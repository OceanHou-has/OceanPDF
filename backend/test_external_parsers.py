r"""
外部文档解析服务测试脚本
用样本PDF调用外部解析服务，落盘原始响应 + 归一化结果 + 版面框可视化图，
用于验证各服务API行为与坐标正确性（接入归一化适配层前的探测工具）

用法（在 backend 目录下运行）:
    .\.venv\Scripts\python .\test_external_parsers.py --provider zhipu --pdf xxx.pdf --max-pages 2
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Windows GBK控制台无法输出部分字符，统一切到UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 标签颜色映射（RGB 0-1，用于可视化）
LABEL_COLORS = {
    "text": (0.27, 0.72, 0.82),          # 蓝
    "doc_title": (1.0, 0.42, 0.42),      # 红
    "title": (0.31, 0.80, 0.77),         # 青
    "paragraph_title": (0.31, 0.80, 0.77),
    "abstract": (0.60, 0.80, 0.70),      # 绿
    "figure": (0.99, 0.47, 0.66),        # 粉
    "figure_caption": (0.99, 0.80, 0.43),
    "table": (0.64, 0.61, 1.0),          # 紫
    "table_caption": (0.45, 0.73, 1.0),
    "equation": (0.49, 0.23, 0.93),
    "header": (0.70, 0.75, 0.76),        # 灰
    "footer": (0.70, 0.75, 0.76),
    "footnote": (0.70, 0.75, 0.76),
    "reference": (0.55, 0.55, 0.55),
}
DEFAULT_COLOR = (0.90, 0.60, 0.20)


def visualize(normalized: dict, pdf_path: str, zoom: float, out_dir: Path, provider: str) -> None:
    """在渲染页面上绘制归一化后的版面框"""
    import fitz

    out_dir.mkdir(parents=True, exist_ok=True)
    pages_map = {p["page_index"]: p for p in normalized.get("pages", [])}

    with fitz.open(pdf_path) as doc:
        matrix = fitz.Matrix(zoom, zoom)
        for page_index, page_data in pages_map.items():
            if page_index >= len(doc):
                continue
            pix = doc[page_index].get_pixmap(matrix=matrix)
            img_w, img_h = pix.width, pix.height

            # 归一化坐标基于渲染图像像素，直接映射回PDF点坐标绘制
            page = doc[page_index]
            pw, ph = page.rect.width, page.rect.height
            scale_x = pw / img_w if img_w else 1.0
            scale_y = ph / img_h if img_h else 1.0

            for box in page_data.get("boxes", []):
                coord = box.get("coordinate") or []
                if len(coord) < 4:
                    continue
                label = box.get("label", "")
                color = LABEL_COLORS.get(label, DEFAULT_COLOR)
                rect = fitz.Rect(
                    coord[0] * scale_x, coord[1] * scale_y,
                    coord[2] * scale_x, coord[3] * scale_y,
                )
                page.draw_rect(rect, color=color, width=1.2)
                ro = box.get("reading_order")
                tag = f"{ro}:{label}" if ro else label
                page.insert_text(
                    fitz.Point(rect.x0 + 1, max(rect.y0 - 2, 8)),
                    tag, fontsize=7, color=color,
                )

            out_path = out_dir / f"{provider}_page{page_index + 1}.png"
            pix = doc[page_index].get_pixmap(matrix=matrix)
            pix.save(str(out_path))
            print(f"可视化已保存: {out_path}")


async def main() -> int:
    ap = argparse.ArgumentParser(description="外部文档解析服务测试")
    ap.add_argument("--provider", default="zhipu", help="服务ID（当前支持: zhipu）")
    ap.add_argument("--pdf", required=True, help="样本PDF路径")
    ap.add_argument("--max-pages", type=int, default=2, help="最多解析页数（默认2，控制扣费）")
    ap.add_argument("--zoom", type=float, default=2.0, help="页面渲染缩放比例（默认2.0，与DPS一致）")
    args = ap.parse_args()

    from app.services.document_parser.config_store import get_provider_config
    from app.services.document_parser.parsers import PARSER_REGISTRY

    entry = PARSER_REGISTRY.get(args.provider)
    if not entry:
        print(f"❌ 未实现的解析服务: {args.provider}（可选: {list(PARSER_REGISTRY.keys())}）")
        return 1

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ PDF文件不存在: {pdf_path}")
        return 1

    config = get_provider_config(args.provider)
    if not config:
        print(f"❌ 未找到 {args.provider} 的已保存配置，请先在设置页配置并测试连通性")
        print(f"   配置文件: storage/config/document_parser_config.json")
        return 1

    out_dir = Path("test_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 调用真实解析
    print(f"▶ 开始解析: {pdf_path.name} | provider={args.provider} | max_pages={args.max_pages}")
    try:
        raw = await entry["parse"](str(pdf_path), config, max_pages=args.max_pages, zoom=args.zoom)
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return 1

    raw_path = out_dir / f"{args.provider}_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"✅ 原始响应已落盘: {raw_path}")

    # 2. 归一化
    normalized = entry["normalize"](raw)
    norm_path = out_dir / f"{args.provider}_normalized.json"
    with open(norm_path, "w", encoding="utf-8") as f:
        json.dump({"meta": {"provider": args.provider}, "raw": normalized}, f, ensure_ascii=False, indent=2)
    print(f"✅ 归一化结果已落盘: {norm_path}")

    # 3. 统计概览
    for page in normalized.get("pages", []):
        boxes = page.get("boxes", [])
        labels = {}
        for b in boxes:
            labels[b.get("label")] = labels.get(b.get("label"), 0) + 1
        print(f"   第{page['page_index'] + 1}页: {len(boxes)}框 | 尺寸={page['width']}x{page['height']} | {labels}")

    # 4. 可视化
    try:
        visualize(normalized, str(pdf_path), args.zoom, out_dir, args.provider)
    except Exception as e:
        print(f"⚠️ 可视化生成失败: {e}")

    usage = raw.get("usage") or {}
    print(f"✅ 测试完成 | 耗时: {raw.get('elapsed_sec')}s | tokens: {usage.get('total_tokens', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
