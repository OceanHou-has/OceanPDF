import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from loguru import logger

from app.services.annotation.annotation_service import AnnotationService
from app.services.sorting.reading_order_service import recalculate_page_reading_order


class HeadingHierarchyService:
    def __init__(self, parsed_base_dir: str = "storage/parsed"):
        self.parsed_base_dir = Path(parsed_base_dir)
        self.annotation_service = AnnotationService(parsed_base_dir=parsed_base_dir)

    @staticmethod
    def _detect_level(text: str) -> Tuple[int, Optional[str]]:
        s = (text or "").strip()
        s = re.sub(r"\s+", " ", s)
        if not s:
            return 1, None

        s_norm = s.replace("．", ".").replace("。", ".")
        m = re.match(r"^(\d+(?:\.\d+){0,8})\s*[\.\)\]\:：\-–—]?\s*(.*)$", s_norm)
        if not m:
            if re.match(r"^\d", s_norm) and ("." in s_norm or "．" in s or "。" in s):
                logger.warning(f"标题序号识别失败，按一级处理: text={s[:200]}")
            return 1, None

        num = (m.group(1) or "").strip(".")
        if not num:
            return 1, None

        num = num.replace("．", ".").replace("。", ".")
        parts = [p for p in num.split(".") if p]
        level = max(1, len(parts))
        return min(3, level), num

    @staticmethod
    def _level_to_type(level: int) -> str:
        if level <= 1:
            return "section_title"
        if level == 2:
            return "section_title_2"
        return "section_title_3"

    def analyze_and_apply(self, pdf_name: str, *, force: bool = False) -> Dict[str, Any]:
        parsed_data = self.annotation_service.load_parsed_data(pdf_name)
        if not parsed_data:
            return {"success": False, "error": "解析数据不存在"}

        pre = parsed_data.get("dps_preannotation") or {}
        based_on_req_id = pre.get("dps_req_id")
        based_on_generated_at = pre.get("dps_generated_at")

        meta = parsed_data.get("heading_hierarchy") or {}
        if not force and meta.get("based_on_dps_req_id") == based_on_req_id and meta.get("based_on_dps_generated_at") == based_on_generated_at:
            logger.info(
                f"标题层级分析已完成，跳过: pdf_name={pdf_name} dps_req_id={based_on_req_id} generated_at={based_on_generated_at}"
            )
            return {"success": True, "skipped": True, "data": meta}

        pages = parsed_data.get("pages") or []
        changed_elements = 0
        changed_pages = set()
        level_stats = {"1": 0, "2": 0, "3": 0}
        with_number = 0
        without_number = 0

        for page in pages:
            page_num = page.get("page_num")
            elements = page.get("elements") or []
            for el in elements:
                t = el.get("type")
                if t not in {"section_title", "section_title_2", "section_title_3"}:
                    continue

                level, num = self._detect_level(el.get("text") or "")
                new_type = self._level_to_type(level)
                if num:
                    with_number += 1
                else:
                    without_number += 1

                level_stats[str(level)] += 1

                if t != new_type:
                    el["type"] = new_type
                    changed_elements += 1
                    if page_num is not None:
                        changed_pages.add(int(page_num))

        logger.info(
            f"标题层级分析: pdf_name={pdf_name} pages={len(pages)} changed_elements={changed_elements} "
            f"with_number={with_number} without_number={without_number} level_stats={level_stats}"
        )

        # 标题层级分析完成后，不再计算阅读顺序
        # 阅读顺序在首次解析时由DPS同步功能直接写入
        # 后续只有用户修改后才重新计算

        parsed_data["heading_hierarchy"] = {
            "based_on_dps_req_id": based_on_req_id,
            "based_on_dps_generated_at": based_on_generated_at,
            "changed_elements": changed_elements,
            "with_number": with_number,
            "without_number": without_number,
            "level_stats": level_stats,
        }

        if not self.annotation_service.save_parsed_data(pdf_name, parsed_data):
            return {"success": False, "error": "保存标题层级分析结果失败"}

        return {"success": True, "data": parsed_data["heading_hierarchy"]}
