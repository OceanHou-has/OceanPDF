"""
PDF生成器
负责将翻译结果渲染到PDF文件中
使用PyMuPDF (fitz) 进行PDF操作
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

from .font_manager import FontManager, classify_char, FontCategory


class PDFGenerator:
    """
    PDF生成器
    支持在原PDF基础上叠加翻译文本，或生成新的双语PDF
    """
    
    # 元素类型对应的样式配置
    ELEMENT_STYLES = {
        "document_title": {
            "font_size": 13.5,
            "font_weight": "bold",
            "color": (0.7216, 0.5255, 0.0431),
            "align": "center",
            "line_height": 1.15,
        },
        "section_title": {
            "font_size": 10.8,
            "font_weight": "bold",
            "color": (0.1176, 0.2275, 0.5412),
            "align": "left",
            "line_height": 1.12,
        },
        "section_title_2": {
            "font_size": 9.9,
            "font_weight": "bold",
            "color": (0.6, 0.1059, 0.1059),
            "align": "left",
            "line_height": 1.12,
        },
        "section_title_3": {
            "font_size": 9.45,
            "font_weight": "bold",
            "color": (0.4196, 0.1294, 0.6588),
            "align": "left",
            "line_height": 1.12,
        },
        "paragraph": {
            "font_size": 9,
            "font_weight": "normal",
            "color": (0, 0, 0),
            "align": "left",
            "line_height": 1.15,
        },
        "list": {
            "font_size": 9,
            "font_weight": "normal",
            "color": (0, 0, 0),
            "align": "left",
            "line_height": 1.15,
        },
        "figure_caption": {
            "font_size": 9,
            "font_weight": "medium",
            "color": (0.9255, 0.2824, 0.6),
            "align": "center",
            "line_height": 1.12,
        },
        "table_caption": {
            "font_size": 9,
            "font_weight": "medium",
            "color": (0.9255, 0.2824, 0.6),
            "align": "center",
            "line_height": 1.12,
        },
        "formula_caption": {
            "font_size": 10.8,
            "font_weight": "bold",
            "color": (0.0157, 0.4706, 0.3412),
            "align": "center",
            "line_height": 1.15,
        },
    }
    
    # 默认样式
    DEFAULT_STYLE = {
        "font_size": 9,
        "font_weight": "normal",
        "color": (0, 0, 0),
        "align": "left",
        "line_height": 1.15,
    }
    
    def __init__(self, font_manager: FontManager):
        """
        初始化PDF生成器
        
        Args:
            font_manager: 字体管理器实例
        """
        self.font_manager = font_manager
        
        # 注册字体到PyMuPDF
        self._registered_fitz_fonts: Dict[str, str] = {}
        self._fitz_fontname_by_fontfile: Dict[str, str] = {}
        self._insert_textbox_supports_lineheight = False
        try:
            import inspect

            self._insert_textbox_supports_lineheight = (
                "lineheight"
                in inspect.signature(fitz.Page.insert_textbox).parameters
            )
        except Exception:
            self._insert_textbox_supports_lineheight = False
        
        logger.info("PDF生成器初始化完成")

    def _get_fitz_fontname_for_fontfile(self, fontfile: str) -> str:
        cached = self._fitz_fontname_by_fontfile.get(fontfile)
        if cached:
            return cached

        try:
            stem = Path(fontfile).stem
        except Exception:
            stem = "Font"

        safe = re.sub(r"[^0-9A-Za-z_]+", "_", stem).strip("_") or "Font"
        name = f"OceanPDF_{safe}"
        self._fitz_fontname_by_fontfile[fontfile] = name
        return name
    
    def _register_font_to_fitz(self, font_name: str) -> Optional[str]:
        """
        将字体注册到PyMuPDF
        
        Args:
            font_name: 字体管理器中的字体名称
            
        Returns:
            注册后的字体名称（用于fitz），如果失败返回None
        """
        if font_name in self._registered_fitz_fonts:
            return self._registered_fitz_fonts[font_name]
        
        font_path = self.font_manager.get_font_path(font_name)
        if not font_path or not font_path.exists():
            logger.warning(f"字体文件不存在: {font_name}")
            return None

        try:
            self._registered_fitz_fonts[font_name] = str(font_path)
            logger.debug(f"注册字体到PyMuPDF: {font_name} -> {font_path}")
            return str(font_path)
        except Exception as e:
            logger.error(f"注册字体失败: {font_name} | 错误: {str(e)}")
            return None

    def _is_bold_style(self, style: Dict) -> bool:
        weight = str(style.get("font_weight", "normal")).lower().strip()
        return weight not in ("normal", "regular", "400")

    def _clamp_rect_to_page(self, rect: fitz.Rect, page_rect: fitz.Rect) -> fitz.Rect:
        return rect & page_rect

    def _expand_rect(self, rect: fitz.Rect, pad: float) -> fitz.Rect:
        return fitz.Rect(rect.x0 - pad, rect.y0 - pad, rect.x1 + pad, rect.y1 + pad)

    def _erase_regions_on_page(
        self,
        page: fitz.Page,
        rects: List[fitz.Rect],
        fill: Tuple[float, float, float] = (1, 1, 1)
    ) -> bool:
        if not rects:
            return True

        page_rect = page.rect
        valid_rects: List[fitz.Rect] = []
        for rect in rects:
            r = self._clamp_rect_to_page(rect, page_rect)
            if r.is_empty or r.get_area() <= 0:
                continue
            valid_rects.append(r)

        if not valid_rects:
            return True

        try:
            for rect in valid_rects:
                page.add_redact_annot(rect, fill=fill)

            images_flag = getattr(fitz, "PDF_REDACT_IMAGE_NONE", 0)
            page.apply_redactions(images=images_flag)
            logger.info(
                f"🧽 已删除页面内容: page={page.number} rects={len(valid_rects)}"
            )
            return True
        except Exception as e:
            logger.error(
                f"删除页面内容失败，将回退为白底遮盖: page={page.number} rects={len(valid_rects)} err={str(e)}"
            )
            return False

    def _extract_text_union_rect(
        self,
        page: fitz.Page,
        clip_rect: fitz.Rect
    ) -> Optional[fitz.Rect]:
        try:
            data = page.get_text("dict", clip=clip_rect)
        except Exception as e:
            logger.warning(
                f"提取clip文本失败: page={page.number} rect={clip_rect} err={str(e)}"
            )
            return None

        blocks = data.get("blocks") if isinstance(data, dict) else None
        if not isinstance(blocks, list):
            return None

        union: Optional[fitz.Rect] = None
        span_count = 0
        for b in blocks:
            for line in b.get("lines", []) if isinstance(b, dict) else []:
                for span in line.get("spans", []) if isinstance(line, dict) else []:
                    txt = span.get("text") if isinstance(span, dict) else None
                    if not isinstance(txt, str) or not txt.strip():
                        continue
                    bbox = span.get("bbox") if isinstance(span, dict) else None
                    if not (isinstance(bbox, (list, tuple)) and len(bbox) >= 4):
                        continue
                    r = fitz.Rect(bbox)
                    union = r if union is None else (union | r)
                    span_count += 1

        if union is None or union.is_empty or union.get_area() <= 0:
            return None

        logger.debug(
            f"clip文本提取: page={page.number} spans={span_count} union={union}"
        )
        return union

    def _get_redaction_rect_for_task(
        self,
        page: fitz.Page,
        bbox: List[float],
        element_type: str
    ) -> fitz.Rect:
        page_rect = page.rect
        base = fitz.Rect(bbox) & page_rect
        if base.is_empty or base.get_area() <= 0:
            return base

        clip = self._expand_rect(base, 1.0) & page_rect
        if element_type in {
            "document_title",
            "section_title",
            "section_title_2",
            "section_title_3",
            "paragraph",
            "list",
            "figure_caption",
            "table_caption",
            "formula_caption",
        }:
            union = self._extract_text_union_rect(page, clip)
            if union is not None:
                union2 = self._expand_rect(union, 1.0) & page_rect
                if not union2.is_empty and union2.get_area() > 0:
                    ratio = union2.get_area() / max(base.get_area(), 1e-6)
                    if ratio < 0.5:
                        logger.info(
                            f"🧩 redaction收紧: page={page.number} type={element_type} "
                            f"base_area={base.get_area():.2f} union_area={union2.get_area():.2f} ratio={ratio:.3f}"
                        )
                    return union2

        return base
    
    def _get_style_for_element(self, element_type: str) -> Dict:
        """
        获取元素类型对应的样式
        
        Args:
            element_type: 元素类型
            
        Returns:
            样式字典
        """
        return self.ELEMENT_STYLES.get(element_type, self.DEFAULT_STYLE)
    
    def _calculate_text_rect(
        self,
        bbox: List[float],
        page_rect: fitz.Rect,
        padding: float = 2.0
    ) -> fitz.Rect:
        """
        计算文本绘制区域
        
        Args:
            bbox: 原始边界框 [x0, y0, x1, y1]
            page_rect: 页面矩形
            padding: 内边距
            
        Returns:
            文本绘制矩形
        """
        x0, y0, x1, y1 = bbox
        
        # 应用内边距
        rect = fitz.Rect(
            x0 + padding,
            y0 + padding,
            x1 - padding,
            y1 - padding
        )
        
        # 确保矩形在页面范围内
        rect = rect & page_rect
        
        return rect

    def _normalize_text_for_textbox(self, text: str, element_type: str) -> str:
        original = text or ""
        if not original.strip():
            return original

        normalized = re.sub(r"[\r\n\u2028\u2029]+", " ", original)
        normalized = re.sub(r"[ \t]+", " ", normalized)

        nbsp = "\u00A0"
        normalized = re.sub(
            r"\(([^)]+)\)",
            lambda m: "(" + m.group(1).replace(" ", nbsp) + ")",
            normalized
        )
        normalized = re.sub(r" (\d)", nbsp + r"\1", normalized)

        space_count = normalized.count(" ")
        if space_count:
            normalized = normalized.replace(" ", nbsp)

        if element_type in {"paragraph", "list"}:
            normalized = normalized.rstrip()
        else:
            normalized = normalized.strip()

        if space_count:
            logger.debug(
                "文本防断行处理: page_break_hint=NBSP "
                f"type={element_type} spaces={space_count} "
                f"len={len(original)}-> {len(normalized)}"
            )

        return normalized
    
    def _draw_text_block(
        self,
        page: fitz.Page,
        text: str,
        rect: fitz.Rect,
        style: Dict,
        font_path: str,
        background_color: Optional[Tuple[float, float, float]] = None
    ) -> bool:
        """
        在页面上绘制文本块
        
        Args:
            page: PyMuPDF页面对象
            text: 要绘制的文本
            rect: 绘制区域矩形
            style: 样式配置
            font_path: 字体文件路径
            background_color: 背景颜色（RGB，0-1范围）
            
        Returns:
            是否绘制成功
        """
        if not text or not text.strip():
            return True
        
        try:
            if rect.is_empty or rect.get_area() <= 0:
                logger.error(
                    f"绘制文本块失败: empty rect page={page.number} rect={rect} text_len={len(text)}"
                )
                return False

            # 绘制背景（白色遮盖原文）
            if background_color:
                shape = page.new_shape()
                shape.draw_rect(rect)
                shape.finish(color=None, fill=background_color)
                shape.commit()
            
            # 获取样式参数
            font_size = style.get("font_size", 9)
            color = style.get("color", (0, 0, 0))
            align = style.get("align", "left")
            line_height = style.get("line_height", 1.15)
            try:
                line_height = float(line_height)
            except Exception:
                line_height = 1.15
            line_height = max(0.8, min(2.0, line_height))
            if self._is_bold_style(style):
                font_path = (
                    self._register_font_to_fitz("main_bold")
                    or font_path
                )
            
            # 对齐方式转换
            align_map = {
                "left": fitz.TEXT_ALIGN_LEFT,
                "center": fitz.TEXT_ALIGN_CENTER,
                "right": fitz.TEXT_ALIGN_RIGHT,
                "justify": fitz.TEXT_ALIGN_JUSTIFY,
            }
            text_align = align_map.get(align, fitz.TEXT_ALIGN_LEFT)
            
            # 使用 insert_textbox 绘制文本
            # 支持自动换行和对齐
            def try_insert(r: fitz.Rect, size: float) -> float:
                fitz_fontname = self._get_fitz_fontname_for_fontfile(font_path)
                kwargs = {
                    "fontsize": size,
                    "fontfile": font_path,
                    "fontname": fitz_fontname,
                    "color": color,
                    "align": text_align,
                }
                if self._insert_textbox_supports_lineheight:
                    kwargs["lineheight"] = line_height
                return page.insert_textbox(
                    r,
                    text,
                    **kwargs,
                )

            rc = try_insert(rect, font_size)
            
            if rc < 0:
                # 文本溢出，尝试缩小字号
                logger.debug(
                    f"文本溢出，尝试缩小字号: page={page.number} chars={len(text)} rc={rc} "
                    f"rect=({rect.x0:.2f},{rect.y0:.2f},{rect.x1:.2f},{rect.y1:.2f}) size={font_size}"
                )
                
                # 逐步缩小字号直到适合
                min_font_size = 3
                start_size = max(int(font_size), min_font_size + 1)
                for smaller_size in range(start_size, min_font_size - 1, -1):
                    if smaller_size == font_size:
                        continue
                    rc = try_insert(rect, smaller_size)
                    if rc >= 0:
                        break

            if rc < 0:
                page_rect = page.rect
                for expand in (1.0, 2.0, 4.0, 8.0, 12.0, 16.0):
                    expanded = self._expand_rect(rect, expand) & page_rect
                    if expanded.is_empty or expanded.get_area() <= 0:
                        continue

                    for size in (font_size, 9, 8, 7, 6, 5, 4, 3):
                        rc = try_insert(expanded, float(size))
                        if rc >= 0:
                            logger.info(
                                f"🔁 回退渲染成功: page={page.number} expand={expand} size={size} rc={rc}"
                            )
                            return True

                logger.error(
                    f"文本无法放入矩形: page={page.number} rc={rc} "
                    f"rect=({rect.x0:.2f},{rect.y0:.2f},{rect.x1:.2f},{rect.y1:.2f}) "
                    f"font_size={font_size} text_len={len(text)}"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"绘制文本块失败: {str(e)}")
            return False
    
    def _draw_segmented_text(
        self,
        page: fitz.Page,
        text: str,
        rect: fitz.Rect,
        style: Dict,
        background_color: Optional[Tuple[float, float, float]] = None,
        background_rect: Optional[fitz.Rect] = None
    ) -> bool:
        """
        绘制混合字体文本（使用TextWriter实现自动字体回退）
        
        TextWriter会自动处理字体回退：当字符不被当前字体支持时，
        会自动搜索替代字体（包括内置的Droid Sans Fallback和已注册的字体）
        """
        if not text or not text.strip():
            return True
        
        # 绘制背景
        if background_color:
            fill_rect = background_rect if background_rect is not None else rect
            shape = page.new_shape()
            shape.draw_rect(fill_rect)
            shape.finish(color=None, fill=background_color)
            shape.commit()
        
        # 分段文本
        segments = self.font_manager.segment_text(text)
        
        # 如果只有一个段落且使用主字体，直接绘制
        if len(segments) == 1:
            font_name, segment_text = segments[0]
            if self._is_bold_style(style) and font_name in ("main", "main_bold"):
                font_name = "main_bold"
            font_path = self._register_font_to_fitz(font_name)
            if font_path:
                return self._draw_text_block(page, segment_text, rect, style, font_path)
        
        # 多段落情况：使用TextWriter实现自动字体回退
        return self._draw_text_with_textwriter(page, text, rect, style)
    
    def _draw_text_with_textwriter(
        self,
        page: fitz.Page,
        text: str,
        rect: fitz.Rect,
        style: Dict
    ) -> bool:
        """
        使用TextWriter绘制文本，支持自动字体回退
        
        TextWriter会自动处理字体回退：当字符不被当前字体支持时，
        会自动搜索替代字体（包括内置的Droid Sans Fallback和已注册的字体）
        """
        try:
            if rect.is_empty or rect.get_area() <= 0:
                logger.error(
                    f"TextWriter绘制失败: empty rect page={page.number} rect={rect} text_len={len(text)}"
                )
                return False
            
            # 获取样式参数
            font_size = style.get("font_size", 9)
            color = style.get("color", (0, 0, 0))
            align = style.get("align", "left")
            
            # 对齐方式转换
            align_map = {
                "left": fitz.TEXT_ALIGN_LEFT,
                "center": fitz.TEXT_ALIGN_CENTER,
                "right": fitz.TEXT_ALIGN_RIGHT,
                "justify": fitz.TEXT_ALIGN_JUSTIFY,
            }
            text_align = align_map.get(align, fitz.TEXT_ALIGN_LEFT)
            
            # 使用内置CJK字体作为基础字体
            # TextWriter会自动回退到其他已注册字体
            base_font = fitz.Font("cjk")
            
            # 创建TextWriter
            tw = fitz.TextWriter(page.rect, color=color)
            
            # 使用fill_textbox填充文本框
            overflow = tw.fill_textbox(
                rect,
                text,
                font=base_font,
                fontsize=font_size,
                align=text_align,
            )
            
            # 写入页面
            tw.write_text(page)
            
            if overflow:
                logger.debug(
                    f"TextWriter文本溢出: page={page.number} overflow_lines={len(overflow)}"
                )
            
            logger.debug(
                f"TextWriter绘制成功: page={page.number} text_len={len(text)} "
                f"rect=({rect.x0:.2f},{rect.y0:.2f},{rect.x1:.2f},{rect.y1:.2f})"
            )
            return True
            
        except Exception as e:
            logger.error(f"TextWriter绘制失败: page={page.number} err={str(e)}")
            # 回退到原有的绘制方法
            main_font_name = "main_bold" if self._is_bold_style(style) else "main"
            main_font_path = self._register_font_to_fitz(main_font_name)
            if main_font_path:
                return self._draw_text_block(page, text, rect, style, main_font_path)
            return False
    
    def create_translated_pdf(
        self,
        source_pdf_path: str,
        output_path: str,
        translation_data: Dict,
        mode: str = "overlay"
    ) -> Dict:
        """
        创建翻译后的PDF文件
        
        Args:
            source_pdf_path: 源PDF文件路径
            output_path: 输出PDF文件路径
            translation_data: 翻译结果数据
            mode: 生成模式
                - "overlay": 在原PDF上叠加翻译（用白色遮盖原文后写入译文）
                - "bilingual": 生成双语对照PDF（左右或上下排列）
                
        Returns:
            生成结果
        """
        logger.info(f"开始生成翻译PDF: source={source_pdf_path}, mode={mode}")
        
        # 自动注册字体
        font_status = self.font_manager.auto_register_fonts()
        if not any(font_status.values()):
            return {
                "success": False,
                "error": "没有可用的字体文件",
                "font_status": font_status
            }
        
        try:
            # 打开源PDF
            doc = fitz.open(source_pdf_path)
            
            # 获取翻译任务
            translation_tasks = translation_data.get("translation_tasks", [])
            
            # 按页面分组
            tasks_by_page = self._group_tasks_by_page(translation_tasks)
            
            # 统计
            total_tasks = len(translation_tasks)
            rendered_tasks = 0
            failed_tasks = 0
            
            # 逐页处理
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_tasks = tasks_by_page.get(page_num, [])

                erase_ok = True
                if mode == "overlay" and page_tasks:
                    erase_rects: List[fitz.Rect] = []
                    for t in page_tasks:
                        bbox = t.get("bbox")
                        if not bbox or len(bbox) < 4:
                            continue
                        try:
                            element_type = t.get("element_type", "paragraph")
                            rect = self._get_redaction_rect_for_task(page, bbox, element_type)
                            erase_rects.append(rect)
                        except Exception:
                            continue
                    logger.info(
                        f"准备删除原文区域: page={page_num} tasks={len(page_tasks)} rects={len(erase_rects)}"
                    )
                    erase_ok = self._erase_regions_on_page(page, erase_rects, fill=(1, 1, 1))

                for task in page_tasks:
                    success = self._render_task_to_page(
                        page,
                        task,
                        background_color=None if erase_ok else (1, 1, 1)
                    )
                    if success:
                        rendered_tasks += 1
                    else:
                        failed_tasks += 1
            
            # 保存输出文件
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 在关闭文档前保存页数
            total_pages = len(doc)
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            
            logger.info(f"✅ PDF生成完成: {output_path} | 渲染: {rendered_tasks}/{total_tasks}")
            
            return {
                "success": True,
                "output_path": output_path,
                "statistics": {
                    "total_tasks": total_tasks,
                    "rendered_tasks": rendered_tasks,
                    "failed_tasks": failed_tasks,
                    "pages": total_pages
                }
            }
            
        except Exception as e:
            logger.error(f"生成PDF失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _group_tasks_by_page(self, tasks: List[Dict]) -> Dict[int, List[Dict]]:
        """
        将翻译任务按页面分组
        
        Args:
            tasks: 翻译任务列表
            
        Returns:
            按页码分组的任务字典
        """
        groups: Dict[int, List[Dict]] = {}
        total = len(tasks)
        skipped_status = 0
        skipped_no_text = 0
        aggregated_parent = 0
        aggregated_blocks = 0
        
        for task in tasks:
            # 跳过未成功的任务（使用 translation_status 字段）
            if task.get("translation_status") != "success":
                skipped_status += 1
                continue
            
            # 跳过没有翻译结果的任务
            translated_text = task.get("translated_text")
            if not translated_text:
                skipped_no_text += 1
                continue
            
            if task.get("is_aggregated"):
                # 聚合任务：需要处理 aggregated_blocks
                aggregated_parent += 1
                blocks = task.get("aggregated_blocks", [])
                for block in blocks:
                    page_num = block.get("page_num", 0)
                    if page_num not in groups:
                        groups[page_num] = []
                    
                    # 为每个block创建子任务
                    block_task = {
                        "task_id": task["task_id"],
                        "page_num": page_num,
                        "block_id": block.get("block_id"),
                        "bbox": block.get("bbox"),
                        "element_type": task.get("element_type"),
                        # 聚合任务的译文需要分配到各个block
                        # 这里暂时使用完整译文，后续可以优化
                        "translated_text": block.get("translated_text", translated_text),
                        "is_sub_block": True
                    }
                    groups[page_num].append(block_task)
                    aggregated_blocks += 1
            else:
                # 独立任务
                page_num = task.get("page_num", 0)
                if page_num not in groups:
                    groups[page_num] = []
                groups[page_num].append(task)
        
        logger.info(
            "任务分组完成: "
            f"total={total} grouped_pages={len(groups)} "
            f"skipped_status={skipped_status} skipped_no_text={skipped_no_text} "
            f"aggregated_parent={aggregated_parent} aggregated_blocks={aggregated_blocks}"
        )
        return groups
    
    def _render_task_to_page(
        self,
        page: fitz.Page,
        task: Dict,
        background_color: Optional[Tuple[float, float, float]] = (1, 1, 1)
    ) -> bool:
        bbox = task.get("bbox")
        translated_text = task.get("translated_text")
        element_type = task.get("element_type", "paragraph")

        if not bbox or not translated_text:
            return False
        translated_text = self._normalize_text_for_textbox(translated_text, element_type)

        try:
            page_rect = page.rect
            text_rect = self._calculate_text_rect(bbox, page_rect)
            style = self._get_style_for_element(element_type)

            draw_rect = fitz.Rect(
                text_rect.x0,
                text_rect.y0,
                text_rect.x1,
                page_rect.y1 - 2.0
            ) & page_rect
            if draw_rect.is_empty or draw_rect.get_area() <= 0:
                draw_rect = text_rect

            if (draw_rect.y1 - draw_rect.y0) > (text_rect.y1 - text_rect.y0) + 0.5:
                logger.debug(
                    f"解除高度限制绘制: page={page.number} task_id={task.get('task_id')} "
                    f"type={element_type} base_h={(text_rect.y1 - text_rect.y0):.2f} "
                    f"draw_h={(draw_rect.y1 - draw_rect.y0):.2f} "
                    f"x=({draw_rect.x0:.2f},{draw_rect.x1:.2f}) y0={draw_rect.y0:.2f}"
                )

            success = self._draw_segmented_text(
                page,
                translated_text,
                draw_rect,
                style,
                background_color=background_color,
                background_rect=text_rect
            )

            if not success:
                logger.error(
                    f"渲染失败: page={page.number} task_id={task.get('task_id')} "
                    f"type={element_type} bbox={bbox}"
                )

            return success

        except Exception as e:
            logger.error(
                f"渲染任务失败: page={page.number} task_id={task.get('task_id')} "
                f"type={element_type} err={str(e)}"
            )
            return False
    
    def create_bilingual_pdf(
        self,
        source_pdf_path: str,
        output_path: str,
        translation_data: Dict,
        layout: str = "side_by_side"
    ) -> Dict:
        """
        创建双语对照PDF
        
        Args:
            source_pdf_path: 源PDF文件路径
            output_path: 输出PDF文件路径
            translation_data: 翻译结果数据
            layout: 布局方式
                - "side_by_side": 左右对照（原文左，译文右）
                - "interleaved": 交替排列（原文页后跟译文页）
                
        Returns:
            生成结果
        """
        logger.info(f"开始生成双语PDF: layout={layout}")
        
        # 自动注册字体
        font_status = self.font_manager.auto_register_fonts()
        
        try:
            # 打开源PDF
            source_doc = fitz.open(source_pdf_path)
            
            if layout == "side_by_side":
                result = self._create_side_by_side_pdf(
                    source_doc, output_path, translation_data
                )
            elif layout == "interleaved":
                result = self._create_interleaved_pdf(
                    source_doc, output_path, translation_data
                )
            else:
                result = {
                    "success": False,
                    "error": f"不支持的布局方式: {layout}"
                }
            
            source_doc.close()
            return result
            
        except Exception as e:
            logger.error(f"生成双语PDF失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_side_by_side_pdf(
        self,
        source_doc: fitz.Document,
        output_path: str,
        translation_data: Dict
    ) -> Dict:
        """
        创建左右对照的双语PDF
        
        每页宽度翻倍，左侧显示原文，右侧显示译文
        """
        # 创建新文档
        new_doc = fitz.open()
        
        translation_tasks = translation_data.get("translation_tasks", [])
        tasks_by_page = self._group_tasks_by_page(translation_tasks)
        
        for page_num in range(len(source_doc)):
            source_page = source_doc[page_num]
            source_rect = source_page.rect
            
            # 创建宽度翻倍的新页面
            new_width = source_rect.width * 2
            new_height = source_rect.height
            new_page = new_doc.new_page(width=new_width, height=new_height)
            
            # 复制原页面到左侧
            new_page.show_pdf_page(
                fitz.Rect(0, 0, source_rect.width, source_rect.height),
                source_doc,
                page_num
            )
            
            # 在右侧绘制译文
            page_tasks = tasks_by_page.get(page_num, [])
            
            # 先填充右侧为白色背景
            right_rect = fitz.Rect(
                source_rect.width, 0,
                new_width, new_height
            )
            shape = new_page.new_shape()
            shape.draw_rect(right_rect)
            shape.finish(color=None, fill=(1, 1, 1))
            shape.commit()
            
            # 绘制译文到右侧
            for task in page_tasks:
                bbox = task.get("bbox")
                if not bbox:
                    continue
                
                # 将bbox偏移到右侧
                offset_bbox = [
                    bbox[0] + source_rect.width,
                    bbox[1],
                    bbox[2] + source_rect.width,
                    bbox[3]
                ]
                
                task_copy = task.copy()
                task_copy["bbox"] = offset_bbox
                self._render_task_to_page(new_page, task_copy)
        
        # 保存
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        new_doc.save(output_path)
        new_doc.close()
        
        logger.info(f"✅ 双语PDF生成完成（左右对照）: {output_path}")
        
        return {
            "success": True,
            "output_path": output_path,
            "layout": "side_by_side",
            "pages": len(source_doc)
        }
    
    def _create_interleaved_pdf(
        self,
        source_doc: fitz.Document,
        output_path: str,
        translation_data: Dict
    ) -> Dict:
        """
        创建交替排列的双语PDF
        
        原文页后面紧跟译文页
        """
        # 创建新文档
        new_doc = fitz.open()
        
        translation_tasks = translation_data.get("translation_tasks", [])
        tasks_by_page = self._group_tasks_by_page(translation_tasks)
        
        for page_num in range(len(source_doc)):
            source_page = source_doc[page_num]
            source_rect = source_page.rect
            
            # 1. 复制原文页
            new_page = new_doc.new_page(
                width=source_rect.width,
                height=source_rect.height
            )
            new_page.show_pdf_page(source_rect, source_doc, page_num)
            
            # 2. 创建译文页
            trans_page = new_doc.new_page(
                width=source_rect.width,
                height=source_rect.height
            )
            
            # 填充白色背景
            shape = trans_page.new_shape()
            shape.draw_rect(source_rect)
            shape.finish(color=None, fill=(1, 1, 1))
            shape.commit()
            
            # 绘制译文
            page_tasks = tasks_by_page.get(page_num, [])
            for task in page_tasks:
                self._render_task_to_page(trans_page, task)
        
        # 保存
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        new_doc.save(output_path)
        new_doc.close()
        
        logger.info(f"✅ 双语PDF生成完成（交替排列）: {output_path}")
        
        return {
            "success": True,
            "output_path": output_path,
            "layout": "interleaved",
            "pages": len(source_doc) * 2
        }
