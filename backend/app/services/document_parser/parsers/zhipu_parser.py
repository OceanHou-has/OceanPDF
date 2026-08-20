"""
智谱 GLM-OCR 文档解析器
- parse_pdf: 按页渲染图片并调用 layout_parsing 接口，返回原始聚合结果
- normalize: 将原始结果归一化为 dps.json 兼容格式（pages[].boxes[].coordinate/label/ocr_text/reading_order）

智谱接口说明（POST https://open.bigmodel.cn/api/paas/v4/layout_parsing）:
- 请求体: {"model": "glm-ocr", "file": "<url 或 data:image/png;base64,...>"}
- 返回: layout_details（按页的框列表，含 index/label/bbox_2d/content）、md_results、data_info（页面宽高）、usage
- bbox_2d 坐标系存在多种可能（0-1比例 / 0-1000归一化 / 像素坐标），归一化时自适应识别
"""
import base64
import json
import re
import time
from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger

ZHIPU_LAYOUT_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
ZHIPU_MODEL = "glm-ocr"
# 与 DPS render_zoom 默认值保持一致，保证版面框渲染精度
DEFAULT_RENDER_ZOOM = 2.0
# 单页请求超时（秒）
PAGE_REQUEST_TIMEOUT = 120

# 可排序标签（与 DPS layout_service 保持一致，只有这些类型分配 reading_order）
SORTABLE_LABELS = {"doc_title", "paragraph_title", "abstract", "text"}

# 智谱/GLM-OCR 标签 -> DPS 标签词表（preannotate_from_dps 依赖的词表）
LABEL_MAP = {
    # 文本类
    "text": "text",
    "paragraph": "text",
    "list": "text",
    "aside_text": "text",
    "toc": "text",
    "content": "text",
    # 标题类
    "title": "title",
    "doc_title": "doc_title",
    "document_title": "doc_title",
    "paragraph_title": "paragraph_title",
    "section_title": "paragraph_title",
    "heading": "paragraph_title",
    "abstract": "abstract",
    # 图表类
    "figure": "figure",
    "image": "figure",
    "chart": "figure",
    "figure_caption": "figure_caption",
    "figure_title": "figure_caption",
    "table": "table",
    "table_caption": "table_caption",
    "table_note": "table_caption",
    "table_footnote": "table_caption",
    # 公式类
    "formula": "equation",
    "equation": "equation",
    "display_formula": "equation",
    "inline_formula": "equation",
    "formula_number": "text",
    # 页眉页脚/脚注/引用
    "header": "header",
    "footer": "footer",
    "page_number": "footer",
    "footnote": "footnote",
    "reference": "reference",
    "references": "reference",
    "reference_content": "reference",
    # 其他
    "seal": "figure",
    "number": "number",
}


def map_label(zhipu_label: str) -> str:
    """智谱标签映射为 DPS 标签，未知标签归为 text 并记录日志"""
    if not zhipu_label:
        return "text"
    key = str(zhipu_label).strip().lower()
    mapped = LABEL_MAP.get(key)
    if mapped is None:
        logger.warning(f"[智谱解析] 未知标签归为text: {zhipu_label}")
        return "text"
    return mapped


def _extract_label(box: Dict[str, Any]) -> str:
    """
    提取框的真实标签
    实测发现：智谱的 label 字段常为粗分类（如统一为 text），
    细粒度标签（doc_title/abstract/paragraph_title 等）在 native_label 字段
    """
    native = box.get("native_label")
    label = box.get("label")
    # native_label 与 label 不同时优先用 native_label（更细粒度）
    if native and str(native) != str(label):
        return str(native)
    return str(label or native or "")


def _render_pdf_pages(pdf_path: str, zoom: float, max_pages: Optional[int]) -> List[Dict[str, Any]]:
    """
    用 PyMuPDF 按页渲染 PDF 为 PNG

    Returns:
        [{"page_index": i, "png_bytes": ..., "width": px宽, "height": px高}]
    """
    import fitz

    pages = []
    with fitz.open(pdf_path) as doc:
        total = len(doc)
        limit = total if not max_pages else min(total, max_pages)
        if max_pages and total > max_pages:
            logger.info(f"[智谱解析] 页数限制生效: 仅解析前 {max_pages}/{total} 页")
        matrix = fitz.Matrix(zoom, zoom)
        for i in range(limit):
            pix = doc[i].get_pixmap(matrix=matrix)
            pages.append({
                "page_index": i,
                "png_bytes": pix.tobytes("png"),
                "width": pix.width,
                "height": pix.height,
            })
    return pages


async def _parse_page_image(session: aiohttp.ClientSession, api_key: str, png_bytes: bytes, page_index: int) -> Dict[str, Any]:
    """调用 layout_parsing 接口解析单页图片"""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    payload = {
        "model": ZHIPU_MODEL,
        "file": f"data:image/png;base64,{b64}",
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with session.post(
        ZHIPU_LAYOUT_URL,
        json=payload,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=PAGE_REQUEST_TIMEOUT),
    ) as resp:
        text = await resp.text()
        if resp.status == 401 or resp.status == 403:
            raise RuntimeError(f"智谱GLM-OCR认证失败(HTTP {resp.status})，请检查设置页中的API Key是否有效")
        if resp.status == 429:
            raise RuntimeError("智谱GLM-OCR请求频率过高(HTTP 429)，请稍后再试")
        if resp.status != 200:
            raise RuntimeError(f"智谱GLM-OCR解析失败(HTTP {resp.status}): {text[:500]}")
        try:
            data = json.loads(text)
        except Exception as e:
            raise RuntimeError(f"智谱GLM-OCR返回非JSON: {text[:500]}") from e

    if data.get("error"):
        err = data["error"]
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        raise RuntimeError(f"智谱GLM-OCR解析第{page_index + 1}页失败: {msg}")

    return data


async def parse_pdf(
    pdf_path: str,
    config: Dict[str, Any],
    *,
    max_pages: Optional[int] = None,
    zoom: float = DEFAULT_RENDER_ZOOM,
) -> Dict[str, Any]:
    """
    调用智谱GLM-OCR逐页解析PDF

    Args:
        pdf_path: PDF文件路径
        config: 服务配置（需包含 api_key）
        max_pages: 最多解析页数（None=全部）
        zoom: 页面渲染缩放比例

    Returns:
        原始聚合结果:
        {
            "provider": "zhipu",
            "zoom": zoom,
            "elapsed_sec": float,
            "pages": [{"page_index", "image_width", "image_height", "response"}],
            "usage": {"prompt_tokens", "completion_tokens", "total_tokens"}
        }
    """
    api_key = (config or {}).get("api_key", "")
    if not api_key:
        raise RuntimeError("未配置智谱GLM-OCR的API Key，请先在设置页完成配置")

    t0 = time.monotonic()
    logger.info(f"[智谱解析] 开始: {pdf_path} | zoom={zoom} | max_pages={max_pages}")

    rendered_pages = _render_pdf_pages(pdf_path, zoom, max_pages)
    if not rendered_pages:
        raise RuntimeError("PDF渲染失败，未获取到任何页面")

    usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    result_pages = []

    async with aiohttp.ClientSession() as session:
        for page_info in rendered_pages:
            page_index = page_info["page_index"]
            t_page = time.monotonic()
            response = await _parse_page_image(session, api_key, page_info["png_bytes"], page_index)

            usage = response.get("usage") or {}
            for k in usage_total:
                usage_total[k] += int(usage.get(k) or 0)

            result_pages.append({
                "page_index": page_index,
                "image_width": page_info["width"],
                "image_height": page_info["height"],
                "response": response,
            })
            logger.info(f"[智谱解析] 第{page_index + 1}页完成 | 耗时: {time.monotonic() - t_page:.2f}s")

    elapsed = time.monotonic() - t0
    logger.info(
        f"✅ [智谱解析] 完成: {len(result_pages)}页 | 耗时: {elapsed:.2f}s | "
        f"tokens: {usage_total['total_tokens']}"
    )

    return {
        "provider": "zhipu",
        "zoom": zoom,
        "elapsed_sec": round(elapsed, 2),
        "pages": result_pages,
        "usage": usage_total,
    }


def _extract_page_boxes(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从单页响应中提取框列表（layout_details 可能是嵌套列表或JSON字符串）"""
    layout_details = response.get("layout_details")
    if layout_details is None:
        return []
    if isinstance(layout_details, str):
        try:
            layout_details = json.loads(layout_details)
        except Exception as e:
            logger.warning(f"[智谱解析] layout_details为字符串但JSON解析失败: {str(e)}")
            return []
    if not isinstance(layout_details, list) or not layout_details:
        return []
    # 单图调用返回 [ [box, ...] ]，取第一页
    first = layout_details[0]
    if isinstance(first, list):
        return [b for b in first if isinstance(b, dict)]
    return [b for b in layout_details if isinstance(b, dict)]


def _convert_bbox(bbox_2d: List[float], img_w: int, img_h: int, box_w: Optional[float], box_h: Optional[float]) -> Optional[List[float]]:
    """
    自适应转换 bbox_2d 为渲染图像像素坐标

    实测：智谱返回的 bbox_2d 是基于框自带 width/height 尺寸空间的像素坐标
    （通常就是上传图片的尺寸，与渲染尺寸一致）。另外兼容两种归一化情形：
    1. 0-1 比例坐标（所有值 <= 1.5）
    2. 0-1000 归一化坐标（框尺寸恰为 1000x1000 且最大值 <= 1005）
    """
    if not bbox_2d or len(bbox_2d) < 4:
        return None
    try:
        x0, y0, x1, y1 = [float(v) for v in bbox_2d[:4]]
    except (TypeError, ValueError):
        return None

    max_val = max(abs(x0), abs(y0), abs(x1), abs(y1))

    if max_val <= 1.5:
        # 0-1 比例坐标
        out = [x0 * img_w, y0 * img_h, x1 * img_w, y1 * img_h]
    elif box_w and box_h and abs(float(box_w) - 1000) <= 5 and abs(float(box_h) - 1000) <= 5 and max_val <= 1005:
        # 0-1000 归一化坐标
        out = [x0 / 1000 * img_w, y0 / 1000 * img_h, x1 / 1000 * img_w, y1 / 1000 * img_h]
    else:
        # 像素坐标：按框自带宽高（或默认同渲染尺寸）缩放到渲染图像
        src_w = float(box_w) if box_w else float(img_w)
        src_h = float(box_h) if box_h else float(img_h)
        scale_x = img_w / src_w if src_w > 0 else 1.0
        scale_y = img_h / src_h if src_h > 0 else 1.0
        out = [x0 * scale_x, y0 * scale_y, x1 * scale_x, y1 * scale_y]

    # 保证 x0<=x1, y0<=y1 并裁剪到页面范围
    rx0 = max(0.0, min(out[0], out[2]))
    rx1 = min(float(img_w), max(out[0], out[2]))
    ry0 = max(0.0, min(out[1], out[3]))
    ry1 = min(float(img_h), max(out[1], out[3]))
    if rx1 - rx0 < 1 or ry1 - ry0 < 1:
        return None
    return [round(rx0, 2), round(ry0, 2), round(rx1, 2), round(ry1, 2)]


def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    将智谱原始聚合结果归一化为 dps.json 兼容的 raw 结构

    Args:
        raw: parse_pdf 的返回值

    Returns:
        {"status", "req_id", "elapsed_sec", "pages": [{"page_index","width","height","boxes"}]}
    """
    pages_out = []

    for page in raw.get("pages", []):
        page_index = page.get("page_index", 0)
        img_w = int(page.get("image_width") or 0)
        img_h = int(page.get("image_height") or 0)
        response = page.get("response") or {}

        boxes_out = []
        reading_order = 1

        for idx, box in enumerate(_extract_page_boxes(response)):
            coordinate = _convert_bbox(
                box.get("bbox_2d"),
                img_w,
                img_h,
                box.get("width"),
                box.get("height"),
            )
            if coordinate is None:
                continue

            zhipu_label = _extract_label(box)
            dps_label = map_label(zhipu_label)

            # 文本内容：多行用空格连接（与DPS保持一致）；
            # content 可能带 Markdown/HTML 修饰符（如 # 标题、<div> 对齐标签），清洗后再写入
            content = str(box.get("content") or "")
            lines = []
            for line in content.splitlines():
                cleaned = re.sub(r"<[^>]+>", "", line).strip()
                # 去除 Markdown 标题前缀（# ## 等），类型信息已由标签表达
                cleaned = cleaned.lstrip("#").strip()
                if cleaned:
                    lines.append(cleaned)
            ocr_text = " ".join(lines)

            normalized_box = {
                "coordinate": coordinate,
                "label": dps_label,
                "zhipu_label": zhipu_label,
                "ocr_text": ocr_text,
                "DPS_block_id": idx,
            }

            # 阅读顺序：仅可排序类型分配（与DPS语义一致）
            if dps_label in SORTABLE_LABELS:
                normalized_box["reading_order"] = reading_order
                reading_order += 1
            else:
                normalized_box["reading_order"] = None

            boxes_out.append(normalized_box)

        pages_out.append({
            "page_index": page_index,
            "width": img_w,
            "height": img_h,
            "boxes": boxes_out,
        })

    return {
        "status": "success",
        "req_id": f"zhipu_{int(time.time() * 1000)}",
        "elapsed_sec": raw.get("elapsed_sec"),
        "pages": pages_out,
    }
