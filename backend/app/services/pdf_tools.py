"""
PDF 页面工具服务
基于 PyMuPDF 提供合并、拆分、提取、删除、旋转、重排等页面级操作。
"""

import base64
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from loguru import logger


class PDFToolsService:
    """PDF 页面级工具服务"""

    OUTPUT_DIR = Path("storage/outputs/tools")
    MAX_PREVIEW_PAGES = 200
    PREVIEW_SCALE = 0.4

    def __init__(self):
        self.output_dir = self.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 通用工具方法 ----------

    @staticmethod
    def _safe_stem(name: str) -> str:
        """从原始文件名提取安全的 ASCII 词干，避免输出文件名异常。"""
        stem = Path(name or "document").stem
        stem = re.sub(r"[^0-9A-Za-z_\-]+", "_", stem).strip("_")
        return stem or "document"

    @staticmethod
    def _parse_pages(spec: str, total_pages: int) -> List[int]:
        """解析 ``1-3,5,7-9`` 为排序去重后的 0-based 页码列表。"""
        pages = set()
        for part in str(spec).split(","):
            part = part.strip()
            if not part:
                continue
            m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                lo, hi = min(a, b), max(a, b)
                pages.update(range(lo, hi + 1))
            elif part.isdigit():
                pages.add(int(part))
            else:
                raise ValueError(f"无效的页码片段: {part}")
        result = sorted(p - 1 for p in pages if 1 <= p <= total_pages)
        if not result:
            raise ValueError("页码范围为空或超出范围")
        return result

    @staticmethod
    def _parse_order(spec: str, total_pages: int) -> List[int]:
        """解析 ``3,1,2`` 或 ``2-4,1`` 为按给定顺序的 0-based 页码列表。"""
        order: List[int] = []
        for part in str(spec).split(","):
            part = part.strip()
            if not part:
                continue
            m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                lo, hi = min(a, b), max(a, b)
                order.extend(range(lo, hi + 1))
            elif part.isdigit():
                order.append(int(part))
            else:
                raise ValueError(f"无效的页码片段: {part}")
        result = [p - 1 for p in order if 1 <= p <= total_pages]
        if not result:
            raise ValueError("页面顺序为空或超出范围")
        return result

    def _save(self, doc: fitz.Document, filename: str) -> str:
        """保存文档到输出目录并返回文件名。"""
        out_path = self.output_dir / filename
        doc.save(str(out_path), garbage=3, deflate=True)
        logger.info(f"[PDFTools] 已生成: {filename} ({out_path.stat().st_size} bytes)")
        return filename

    # ---------- 具体工具 ----------

    def merge(self, files: List[Tuple[str, bytes]]) -> List[str]:
        """按顺序合并多个 PDF。``files`` 为 [(文件名, 字节), ...]。"""
        out = fitz.open()
        try:
            for name, data in files:
                with fitz.open(stream=data, filetype="pdf") as src:
                    out.insert_pdf(src)
            stem = self._safe_stem(files[0][0])
            return [self._save(out, f"{stem}_merged.pdf")]
        finally:
            out.close()

    def split(
        self,
        data: bytes,
        original_name: str,
        mode: str = "ranges",
        spec: Optional[str] = None,
        every: Optional[int] = None,
        group_spec: Optional[str] = None,
    ) -> List[str]:
        """拆分 PDF。

        - ``mode``: ranges(按范围) / every(每 N 页)
        - ``group_spec``: 可视化分组拆分，如 "1-3|5,7"，每组生成一个文件（优先于 mode/spec）
        """
        with fitz.open(stream=data, filetype="pdf") as doc:
            total = doc.page_count
            if group_spec:
                parts = [g for g in str(group_spec).split("|") if g.strip()]
                if not parts:
                    raise ValueError("未指定分组")
                page_groups = [self._parse_pages(g, total) for g in parts]
            elif mode == "every":
                n = int(every or 1)
                if n < 1:
                    raise ValueError("每 N 页的 N 必须 >= 1")
                page_groups = [list(range(i, min(i + n, total))) for i in range(0, total, n)]
            else:
                page_groups = [
                    self._parse_pages(p, total)
                    for p in str(spec).split(",")
                    if p.strip()
                ]
            if not page_groups:
                raise ValueError("未指定拆分范围")

        stem = self._safe_stem(original_name)
        outputs: List[str] = []
        for i, pages in enumerate(page_groups, 1):
            with fitz.open(stream=data, filetype="pdf") as d:
                d.select(pages)
                outputs.append(self._save(d, f"{stem}_split_{i}.pdf"))
        return outputs

    def preview(self, data: bytes) -> dict:
        """渲染 PDF 每页为缩略图（base64 PNG），用于可视化拆分。"""
        with fitz.open(stream=data, filetype="pdf") as doc:
            total = doc.page_count
            if total > self.MAX_PREVIEW_PAGES:
                raise ValueError(
                    f"页数过多（{total} 页），最多支持 {self.MAX_PREVIEW_PAGES} 页预览，请使用手动输入模式"
                )
            pages = []
            matrix = fitz.Matrix(self.PREVIEW_SCALE, self.PREVIEW_SCALE)
            for i, page in enumerate(doc, 1):
                pix = page.get_pixmap(matrix=matrix)
                b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")
                pages.append(
                    {
                        "page": i,
                        "image": f"data:image/png;base64,{b64}",
                        "width": pix.width,
                        "height": pix.height,
                    }
                )
        return {"total_pages": total, "pages": pages}

    def zip_outputs(self, filenames: List[str]) -> str:
        """将多个输出文件打包为 ZIP，返回 zip 文件名。"""
        zip_name = f"tools_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = self.output_dir / zip_name
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for name in filenames:
                safe = Path(name).name
                src = self.output_dir / safe
                if not src.exists():
                    raise ValueError(f"文件不存在: {safe}")
                zf.write(str(src), arcname=safe)
        logger.info(f"[PDFTools] 已打包: {zip_name} ({zip_path.stat().st_size} bytes)")
        return zip_name

    def extract(
        self,
        data: bytes,
        original_name: str,
        spec: str,
        preserve_order: bool = False,
    ) -> List[str]:
        """提取指定页面，合并为单个 PDF。

        ``preserve_order`` 为 True 时按 spec 给定顺序提取（等价于提取 + 重排）。
        """
        with fitz.open(stream=data, filetype="pdf") as doc:
            if preserve_order:
                pages = self._parse_order(spec, doc.page_count)
            else:
                pages = self._parse_pages(spec, doc.page_count)
            doc.select(pages)
            stem = self._safe_stem(original_name)
            return [self._save(doc, f"{stem}_extracted.pdf")]

    def delete_pages(self, data: bytes, original_name: str, spec: str) -> List[str]:
        """删除指定页面。"""
        with fitz.open(stream=data, filetype="pdf") as doc:
            total = doc.page_count
            to_delete = set(self._parse_pages(spec, total))
            keep = [p for p in range(total) if p not in to_delete]
            if not keep:
                raise ValueError("不能删除全部页面")
            doc.select(keep)
            stem = self._safe_stem(original_name)
            return [self._save(doc, f"{stem}_deleted.pdf")]

    def rotate(
        self,
        data: bytes,
        original_name: str,
        angle: int,
        pages_spec: Optional[str] = None,
        rotation_map: Optional[str] = None,
    ) -> List[str]:
        """旋转页面。

        - ``pages_spec`` 为空时旋转全部页面
        - ``rotation_map`` 如 "1:90,3:180" 时按页分别旋转（优先于 angle/pages_spec）
        """
        angle = int(angle) % 360
        if angle not in (90, 180, 270):
            raise ValueError("旋转角度仅支持 90/180/270")
        with fitz.open(stream=data, filetype="pdf") as doc:
            if rotation_map:
                for item in str(rotation_map).split(","):
                    part = item.strip()
                    if not part:
                        continue
                    if ":" not in part:
                        raise ValueError(f"无效的旋转配置: {part}")
                    p_str, a_str = part.split(":", 1)
                    p = int(p_str.strip())
                    a = int(a_str.strip()) % 360
                    if a not in (90, 180, 270):
                        raise ValueError("旋转角度仅支持 90/180/270")
                    if 1 <= p <= doc.page_count:
                        doc[p - 1].set_rotation((doc[p - 1].rotation + a) % 360)
            elif pages_spec:
                pages = self._parse_pages(pages_spec, doc.page_count)
                for p in pages:
                    doc[p].set_rotation((doc[p].rotation + angle) % 360)
            else:
                pages = list(range(doc.page_count))
                for p in pages:
                    doc[p].set_rotation((doc[p].rotation + angle) % 360)
            stem = self._safe_stem(original_name)
            return [self._save(doc, f"{stem}_rotated.pdf")]

    def reorder(self, data: bytes, original_name: str, spec: str) -> List[str]:
        """按新顺序重排页面。"""
        with fitz.open(stream=data, filetype="pdf") as doc:
            order = self._parse_order(spec, doc.page_count)
            doc.select(order)
            stem = self._safe_stem(original_name)
            return [self._save(doc, f"{stem}_reordered.pdf")]
