"""
预翻译服务
负责生成翻译任务清单，包括智能聚合相邻同类型元素
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from ..pdf_id_mapper import get_pdf_id_mapper


class PretranslationService:
    """预翻译服务类"""

    AGGREGATION_SPLIT_TOKEN = "<<<OCEANPDF_SPLIT>>>"
    
    # 可翻译的元素类型
    TRANSLATABLE_TYPES = {
        "document_title",
        "section_title",
        "section_title_2",
        "section_title_3",
        "paragraph",
        "list",
        "figure_caption",
        "table_caption"
    }
    
    # 可聚合的元素类型（相邻且reading_order连续时自动聚合）
    AGGREGATABLE_TYPES = {
        "paragraph",
        "list"
    }
    
    # 可选聚合的元素类型（可配置是否聚合）
    OPTIONAL_AGGREGATABLE_TYPES = {
        "section_title",
        "section_title_2",
        "section_title_3"
    }
    
    # 句子终止标点（作为聚合边界）
    SENTENCE_TERMINATORS = {
        '.',   # 英文句号
        '\u3002',  # 中文句号
        '?',   # 英文问号
        '\uff1f',  # 中文问号
        '!',   # 英文叹号
        '\uff01',  # 中文叹号
        ':',   # 英文冒号
        '\uff1a',  # 中文冒号
        ';',   # 英文分号
        '\uff1b'   # 中文分号
    }
    
    # 禁止聚合的元素类型
    NO_AGGREGATE_TYPES = {
        "document_title",
        "figure_caption",
        "table_caption"
    }
    
    # 翻译优先级映射
    PRIORITY_MAP = {
        "document_title": "high",
        "section_title": "high",
        "section_title_2": "high",
        "section_title_3": "high",
        "paragraph": "normal",
        "list": "normal",
        "figure_caption": "normal",
        "table_caption": "normal"
    }
    
    # 上下文类型映射
    CONTEXT_MAP = {
        "document_title": "title",
        "section_title": "heading",
        "section_title_2": "heading",
        "section_title_3": "heading",
        "paragraph": "body",
        "list": "list",
        "figure_caption": "caption",
        "table_caption": "caption"
    }
    
    def __init__(self, parsed_base_dir: str = "storage/parsed"):
        """
        初始化预翻译服务
        
        Args:
            parsed_base_dir: 解析结果存储的基础目录
        """
        self.parsed_base_dir = Path(parsed_base_dir)
        # 导入PaperAnalyzer用于加载强段落信息
        from ..annotation.paper_analyzer import PaperAnalyzer
        self.paper_analyzer = PaperAnalyzer(parsed_base_dir)
    
    def get_parsed_json_path(self, pdf_name: str) -> Path:
        """获取Python解析结果JSON文件路径"""
        # 【优化】使用短ID代替长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "parsed.json"
    
    def get_dps_json_path(self, pdf_name: str) -> Path:
        """获取DPS解析结果JSON文件路径"""
        # 【优化】使用短ID代替长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "dps.json"
    
    def get_pretranslation_json_path(self, pdf_name: str, use_dps: bool = False) -> Path:
        """获取预翻译文件路径"""
        # 【优化】使用短ID代暿长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        suffix = "_dps" if use_dps else ""
        return self.parsed_base_dir / pdf_id / f"pretranslation{suffix}.json"
    
    def load_parsed_data(self, pdf_name: str, use_dps: bool = False) -> Optional[Dict]:
        """
        加载解析数据
        
        Args:
            pdf_name: PDF文件名
            use_dps: 是否使用DPS解析结果
            
        Returns:
            解析数据字典，如果不存在返回None
        """
        if use_dps:
            json_path = self.get_dps_json_path(pdf_name)
            mode_name = "DPS"
        else:
            json_path = self.get_parsed_json_path(pdf_name)
            mode_name = "Python"
        
        if not json_path.exists():
            logger.warning(f"{mode_name}解析数据不存在: {json_path}")
            
            # 如果选择的模式文件不存在，检查另一个模式是否可用
            if use_dps:
                # DPS不存在，检查Python
                alt_path = self.get_parsed_json_path(pdf_name)
                if alt_path.exists():
                    logger.info(f"提示: 找到Python解析结果，建议切换为Python模式")
            else:
                # Python不存在，检查DPS
                alt_path = self.get_dps_json_path(pdf_name)
                if alt_path.exists():
                    logger.info(f"提示: 找到DPS解析结果，建议切换为DPS模式")
            
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果是DPS结果，需要转换为Python解析结果的格式
            if use_dps:
                return self._convert_dps_to_parsed_format(data)
            
            return data
        except Exception as e:
            logger.error(f"加载解析数据失败: {str(e)}")
            return None
    
    def _convert_dps_to_parsed_format(self, dps_data: Dict) -> Dict:
        """
        将DPS解析结果转换为Python解析结果格式
        
        Args:
            dps_data: DPS解析结果
            
        Returns:
            转换后的数据（与_parsed.json格式兼容）
        """
        raw = dps_data.get("raw") or {}
        dps_pages = raw.get("pages") or []
        
        # DPS label 到 element_type 的映射
        label_to_type = {
            "doc_title": "document_title",
            "paragraph_title": "section_title",
            "abstract": "paragraph",
            "text": "paragraph",
            "title": "section_title",
            "display_formula": "display_formula",
            "formula": "display_formula",
            "equation": "display_formula",
            "formula_number": "formula_caption",
            "figure_title": "figure_caption",
            "figure_caption": "figure_caption",
            "table": "table",
            "chart": "figure",
            "image": "figure",
            "figure": "figure",
            "footnote": "table_footnote",
            "reference": "abandon",
            "reference_content": "abandon",
            "header": "abandon",
            "footer": "abandon",
            "page_number": "abandon",
            "number": "abandon",
        }
        
        converted_pages = []
        
        for page_idx, dps_page in enumerate(dps_pages):
            page_width = dps_page.get("width", 0)
            page_height = dps_page.get("height", 0)
            boxes = dps_page.get("boxes") or []
            
            elements = []
            
            for box_idx, box in enumerate(boxes):
                label = str(box.get("label", "") or "").strip().lower()
                element_type = box.get("type") or label_to_type.get(label)
                
                # 跳过不可翻译的类型
                if not element_type or element_type == "abandon":
                    continue
                
                coordinate = box.get("coordinate", [])
                if len(coordinate) != 4:
                    continue
                
                ocr_text = box.get("ocr_text", "")
                if not ocr_text or not ocr_text.strip():
                    continue
                
                # 构造元素
                element = {
                    "block_id": f"p{page_idx}_dps_{box_idx}",
                    "bbox": coordinate,
                    "text": ocr_text,
                    "type": element_type,
                    "element_type": "text",
                    "dps_label": label,
                    "dps_score": box.get("score"),
                    "ocr_confidence": box.get("ocr_avg_confidence")
                }
                
                element["reading_order"] = box.get("reading_order")
                
                elements.append(element)
            
            converted_pages.append({
                "page_num": page_idx,
                "page_size": {
                    "width": page_width,
                    "height": page_height
                },
                "elements": elements
            })
        
        return {
            "pdf_name": dps_data.get("pdf_name", "unknown"),
            "pages": converted_pages,
            "source": "dps",
            "dps_meta": dps_data.get("meta")
        }
    
    def save_pretranslation_data(self, pdf_name: str, data: Dict, use_dps: bool = False) -> bool:
        """
        保存预翻译数据
        
        Args:
            pdf_name: PDF文件名
            data: 预翻译数据
            use_dps: 是否使用DPS模式
            
        Returns:
            是否保存成功
        """
        json_path = self.get_pretranslation_json_path(pdf_name, use_dps)
        
        # 确保目录存在
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 【修复】Windows长路径问题：使用绝对路径并添加 \\?\ 前缀（仅Windows）
            import platform
            abs_path = json_path.absolute()
            
            # Windows系统且路径较长时，使用UNC路径
            if platform.system() == "Windows" and len(str(abs_path)) > 240:
                # 添加 \\?\ 前缀支持长路径
                abs_path_str = f"\\\\?\\{abs_path}"
                logger.info(f"使用长路径模式: 原长度={len(str(abs_path))}, 路径={abs_path_str[:100]}...")
            else:
                abs_path_str = str(abs_path)
            
            with open(abs_path_str, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存预翻译数据成功: {json_path}")
            return True
        except Exception as e:
            logger.error(f"保存预翻译数据失败: {str(e)}")
            logger.error(f"路径长度: {len(str(json_path))}, 路径: {json_path}")
            return False
    
    def extract_translatable_elements(self, parsed_data: Dict, pdf_name: str = None) -> List[Dict]:
        """
        提取所有可翻译的元素，并对标题元素进行宽度和位置调整
        
        Args:
            parsed_data: 解析数据
            pdf_name: PDF文件名（用于加载强段落信息）
            
        Returns:
            可翻译元素列表（包含页码、block_id等信息）
        """
        translatable_elements = []
        
        # 尝试加载强段落元数据（用于调整标题bbox）
        paper_layout = None
        if pdf_name:
            try:
                metadata = self.paper_analyzer.load_metadata(pdf_name)
                if metadata:
                    paper_layout = metadata.get("paper_layout")
                    if paper_layout:
                        logger.info(
                            f"加载强段落信息: 宽度={paper_layout.get('strong_paragraph_width')}px, "
                            f"栏数={paper_layout.get('column_count')}, "
                            f"栏位置={paper_layout.get('column_positions')}"
                        )
            except Exception as e:
                logger.warning(f"加载强段落元数据失败: {str(e)}，将不进行标题bbox调整")
        
        pages = parsed_data.get("pages", [])
        for page_idx, page in enumerate(pages):
            elements = page.get("elements", [])
            
            for element in elements:
                # 跳过被合并的子元素
                if element.get("parent_id"):
                    continue
                
                element_type = element.get("type")
                
                # 只处理可翻译类型
                if element_type not in self.TRANSLATABLE_TYPES:
                    continue
                
                bbox = element.get("bbox")
                
                # 对标题元素进行bbox调整（排除document_title）
                if paper_layout and bbox and element_type in {"section_title", "section_title_2", "section_title_3"}:
                    bbox = self._adjust_title_bbox(bbox, paper_layout)
                
                # 提取必要信息
                translatable_elements.append({
                    "page_num": page_idx,
                    "block_id": element.get("block_id"),
                    "element_type": element_type,
                    "text": element.get("text", ""),
                    "bbox": bbox,
                    "reading_order": element.get("reading_order"),
                    "is_merged": element.get("is_merged", False),
                    "source_ids": element.get("source_ids", [])
                })
        
        return translatable_elements
    
    def create_global_reading_sequence(self, elements: List[Dict]) -> tuple:
        """
        创建全局阅读顺序序列
        
        Args:
            elements: 可翻译元素列表
            
        Returns:
            (按全局阅读顺序排序的元素列表, 无序元素列表)
        """
        # 分离有reading_order和无reading_order的元素
        ordered_elements = [e for e in elements if e.get("reading_order") is not None]
        unordered_elements = [e for e in elements if e.get("reading_order") is None]
        
        # 对有reading_order的元素排序：先按page_num，再按reading_order
        ordered_elements.sort(key=lambda x: (x["page_num"], x["reading_order"]))
        
        # 为排序后的元素添加全局序号
        for idx, element in enumerate(ordered_elements):
            element["global_order"] = idx + 1
        
        logger.info(f"创建全局阅读序列: 有序元素={len(ordered_elements)}, 无序元素={len(unordered_elements)}")
        
        return ordered_elements, unordered_elements
    
    def aggregate_consecutive_elements(
        self, 
        ordered_elements: List[Dict],
        aggregate_titles: bool = False
    ) -> List[Dict]:
        """
        聚合相邻的同类型元素
        
        Args:
            ordered_elements: 按全局阅读顺序排序的元素列表
            aggregate_titles: 是否聚合标题类元素
            
        Returns:
            聚合后的任务列表
        """
        if not ordered_elements:
            return []
        
        tasks = []
        current_aggregation = None
        aggregation_count = 0
        
        for element in ordered_elements:
            element_type = element["element_type"]
            
            # 判断是否可以聚合
            can_aggregate = (
                element_type in self.AGGREGATABLE_TYPES or
                (aggregate_titles and element_type in self.OPTIONAL_AGGREGATABLE_TYPES)
            )
            
            # 如果当前没有正在聚合的任务
            if current_aggregation is None:
                current_aggregation = {
                    "element_type": element_type,
                    "blocks": [element],
                    "can_aggregate": can_aggregate
                }
            # 如果类型相同且可以聚合，且reading_order连续
            elif (
                can_aggregate and
                element_type == current_aggregation["element_type"] and
                self._is_consecutive(current_aggregation["blocks"][-1], element)
            ):
                # 继续聚合
                current_aggregation["blocks"].append(element)
            else:
                # 结束当前聚合，创建任务
                task = self._create_task_from_aggregation(current_aggregation)
                tasks.append(task)
                if current_aggregation["can_aggregate"] and len(current_aggregation["blocks"]) > 1:
                    aggregation_count += 1
                
                # 开始新的聚合
                current_aggregation = {
                    "element_type": element_type,
                    "blocks": [element],
                    "can_aggregate": can_aggregate
                }
        
        # 处理最后一个聚合
        if current_aggregation:
            task = self._create_task_from_aggregation(current_aggregation)
            tasks.append(task)
            if current_aggregation["can_aggregate"] and len(current_aggregation["blocks"]) > 1:
                aggregation_count += 1
        
        logger.info(f"聚合完成: 原始元素={len(ordered_elements)}, 聚合后任务={len(tasks)}, 聚合操作={aggregation_count}")
        
        return tasks
    
    def _ends_with_sentence_terminator(self, text: str) -> bool:
        """
        判断文本是否以句子终止标点结尾
        
        Args:
            text: 待检查的文本
            
        Returns:
            是否以终止符结尾
        """
        if not text:
            return False
        
        text = text.strip()
        if not text:
            return False
        
        # 检查最后一个字符是否为终止符
        return text[-1] in self.SENTENCE_TERMINATORS
    
    def _is_consecutive(self, prev_element: Dict, curr_element: Dict) -> bool:
        """
        判断两个元素的reading_order是否连续，且前一个元素不以句子终止符结尾
        
        Args:
            prev_element: 前一个元素
            curr_element: 当前元素
            
        Returns:
            是否连续
        """
        # 检查前一个元素是否以终止符结尾
        prev_text = prev_element.get("text", "")
        if self._ends_with_sentence_terminator(prev_text):
            # 如果前一个元素以终止符结尾，不继续聚合
            logger.debug(f"元素以终止符结尾，中断聚合: {prev_text[-20:]}")
            return False
        
        prev_page = prev_element["page_num"]
        curr_page = curr_element["page_num"]
        prev_order = prev_element["reading_order"]
        curr_order = curr_element["reading_order"]
        
        # 同一页内，reading_order连续
        if prev_page == curr_page:
            return curr_order == prev_order + 1
        
        # 跨页，前一个元素是前一页的，当前元素是下一页的第一个
        if curr_page == prev_page + 1 and curr_order == 1:
            return True
        
        return False
    
    def _create_task_from_aggregation(self, aggregation: Dict) -> Dict:
        """
        从聚合信息创建任务
        
        Args:
            aggregation: 聚合信息
            
        Returns:
            任务字典
        """
        blocks = aggregation["blocks"]
        element_type = aggregation["element_type"]
        is_aggregated = len(blocks) > 1 and aggregation["can_aggregate"]
        
        if is_aggregated:
            # 创建聚合任务
            task_id = f"t_agg_{blocks[0]['page_num']}_{blocks[0]['reading_order']}"
            
            # 聚合文本（用空格连接，不添加分隔标记）
            parts = [(block.get("text") or "").strip() for block in blocks if (block.get("text") or "").strip()]
            aggregated_text = " ".join(parts)
            
            # 计算页面范围
            page_range = [blocks[0]["page_num"], blocks[-1]["page_num"]]
            
            # 生成reading_order范围描述
            reading_order_parts = []
            current_page = blocks[0]["page_num"]
            current_range = [blocks[0]["reading_order"]]
            
            for block in blocks[1:]:
                if block["page_num"] == current_page:
                    current_range.append(block["reading_order"])
                else:
                    # 页面切换
                    reading_order_parts.append(f"{current_page}:{min(current_range)}-{max(current_range)}")
                    current_page = block["page_num"]
                    current_range = [block["reading_order"]]
            
            # 添加最后一组
            if len(current_range) == 1:
                reading_order_parts.append(f"{current_page}:{current_range[0]}")
            else:
                reading_order_parts.append(f"{current_page}:{min(current_range)}-{max(current_range)}")
            
            return {
                "task_id": task_id,
                "is_aggregated": True,
                "aggregated_blocks": [
                    {
                        "page_num": block["page_num"],
                        "block_id": block["block_id"],
                        "reading_order": block["reading_order"],
                        "element_type": block["element_type"],
                        "text": block["text"],
                        "bbox": block["bbox"],
                        "global_order": block.get("global_order")
                    }
                    for block in blocks
                ],
                "element_type": element_type,
                "aggregated_text": aggregated_text,
                "context": self.CONTEXT_MAP.get(element_type, "body"),
                "translate": True,
                "priority": self.PRIORITY_MAP.get(element_type, "normal"),
                "status": "pending",
                "page_range": page_range,
                "reading_order_range": ", ".join(reading_order_parts)
            }
        else:
            # 创建独立任务
            block = blocks[0]
            task_id = f"t_single_{block['page_num']}_{block.get('reading_order', 'x')}"
            
            return {
                "task_id": task_id,
                "is_aggregated": False,
                "page_num": block["page_num"],
                "block_id": block["block_id"],
                "reading_order": block["reading_order"],
                "element_type": element_type,
                "source_text": block["text"],
                "bbox": block["bbox"],
                "context": self.CONTEXT_MAP.get(element_type, "body"),
                "translate": True,
                "priority": self.PRIORITY_MAP.get(element_type, "normal"),
                "status": "pending",
                "global_order": block.get("global_order")
            }
    
    def _adjust_title_bbox(self, bbox: List[float], paper_layout: Dict) -> List[float]:
        """
        调整标题元素的bbox，使其宽度和X坐标对齐到强段落
        
        规则：
        1. 如果标题宽度已经大于等于强段落宽度，则不调整
        2. 否则，将标题宽度扩展至强段落宽度，并对齐到最近的栏X坐标
        
        Args:
            bbox: 原始bbox [x0, y0, x1, y1]
            paper_layout: 论文版面信息（包含strong_paragraph_width和column_positions）
            
        Returns:
            调整后的bbox
        """
        if not bbox or len(bbox) < 4:
            return bbox
        
        x0, y0, x1, y1 = bbox
        original_width = x1 - x0
        
        # 获取强段落宽度
        strong_width = paper_layout.get("strong_paragraph_width")
        if not strong_width:
            return bbox
        
        # 规则1：如果标题宽度已经大于等于强段落宽度（允许5px误差），则不调整
        if original_width >= (strong_width - 5):
            logger.debug(
                f"标题宽度({original_width:.1f}px)已接近或超过强段落宽度({strong_width:.1f}px)，跳过调整"
            )
            return bbox
        
        # 获取栏位置信息
        column_positions = paper_layout.get("column_positions", [])
        if not column_positions:
            return bbox
        
        # 找到距离标题中心点最近的栏X坐标
        title_center_x = (x0 + x1) / 2
        closest_column_x = None
        min_distance = float('inf')
        
        for col_pos in column_positions:
            col_x = col_pos.get("x")
            if col_x is not None:
                distance = abs(title_center_x - col_x)
                if distance < min_distance:
                    min_distance = distance
                    closest_column_x = col_x
        
        if closest_column_x is None:
            return bbox
        
        # 调整bbox
        # 新的x0对齐到栏X坐标
        new_x0 = closest_column_x
        # 新的x1 = x0 + 强段落宽度
        new_x1 = new_x0 + strong_width
        
        adjusted_bbox = [new_x0, y0, new_x1, y1]
        
        logger.debug(
            f"调整标题bbox: 原始=[{x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}] (宽度={original_width:.1f}px) "
            f"→ 调整后=[{new_x0:.1f}, {y0:.1f}, {new_x1:.1f}, {y1:.1f}] (宽度={strong_width:.1f}px, 对齐到栏X={closest_column_x})"
        )
        
        return adjusted_bbox
    
    def create_unordered_tasks(self, unordered_elements: List[Dict]) -> List[Dict]:
        """
        为无reading_order的元素创建独立任务
        
        Args:
            unordered_elements: 无reading_order的元素列表
            
        Returns:
            任务列表
        """
        tasks = []
        
        for element in unordered_elements:
            task_id = f"t_unordered_{element['page_num']}_{element['block_id']}"
            
            tasks.append({
                "task_id": task_id,
                "is_aggregated": False,
                "page_num": element["page_num"],
                "block_id": element["block_id"],
                "reading_order": None,
                "element_type": element["element_type"],
                "source_text": element["text"],
                "bbox": element["bbox"],
                "context": self.CONTEXT_MAP.get(element["element_type"], "body"),
                "translate": True,
                "priority": self.PRIORITY_MAP.get(element["element_type"], "normal"),
                "status": "pending",
                "note": "no_reading_order"
            })
        
        return tasks
    
    def generate_pretranslation(
        self,
        pdf_name: str,
        source_lang: str = "en",
        target_lang: str = "zh-CN",
        aggregate_titles: bool = False,
        use_dps: bool = False,
        force: bool = False
    ) -> Dict:
        """
        生成预翻译任务清单
        
        Args:
            pdf_name: PDF文件名
            source_lang: 源语言
            target_lang: 目标语言
            aggregate_titles: 是否聚合标题类元素
            use_dps: 是否使用DPS/OCR解析结果（False=Python解析，True=DPS OCR）
            force: 是否强制重新生成
            
        Returns:
            生成结果
        """
        # 检查是否已存在预翻译文件
        pretrans_path = self.get_pretranslation_json_path(pdf_name, use_dps)
        if pretrans_path.exists() and not force:
            logger.info(f"预翻译文件已存在: {pretrans_path}")
            try:
                with open(pretrans_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                return {
                    "success": True,
                    "skipped": True,
                    "message": "预翻译文件已存在",
                    "data": existing_data.get("metadata", {})
                }
            except Exception as e:
                logger.warning(f"读取已存在的预翻译文件失败: {str(e)}")
        
        # 加载解析数据
        parsed_data = self.load_parsed_data(pdf_name, use_dps)
        if not parsed_data:
            mode_name = "DPS" if use_dps else "Python"
            
            # 检查另一个模式是否可用
            alt_mode_name = "Python" if use_dps else "DPS"
            alt_path = self.get_parsed_json_path(pdf_name) if use_dps else self.get_dps_json_path(pdf_name)
            
            if alt_path.exists():
                error_msg = f"{mode_name}解析结果不存在，但找到了{alt_mode_name}解析结果，请切换为{alt_mode_name}模式后重试"
            else:
                error_msg = f"{mode_name}解析结果不存在，请先上传并解析PDF文件"
            
            return {
                "success": False,
                "error": error_msg
            }
        
        mode_name = "DPS" if use_dps else "Python"
        logger.info(
            f"开始生成预翻译任务: pdf_name={pdf_name}, mode={mode_name}, "
            f"source={source_lang}, target={target_lang}, aggregate_titles={aggregate_titles}"
        )
        
        # 1. 提取所有可翻译元素（传入pdf_name以便加载强段落信息）
        translatable_elements = self.extract_translatable_elements(parsed_data, pdf_name)
        logger.info(f"提取可翻译元素: {len(translatable_elements)} 个")
        
        if not translatable_elements:
            return {
                "success": False,
                "error": "没有可翻译的元素"
            }
        
        # 2. 创建全局阅读顺序
        ordered_elements, unordered_elements = self.create_global_reading_sequence(translatable_elements)
        
        # 3. 聚合相邻同类型元素
        ordered_tasks = self.aggregate_consecutive_elements(ordered_elements, aggregate_titles)
        
        # 4. 为无reading_order的元素创建独立任务
        unordered_tasks = self.create_unordered_tasks(unordered_elements)
        
        # 5. 合并所有任务
        all_tasks = ordered_tasks + unordered_tasks
        
        # 6. 统计信息
        aggregated_count = sum(1 for task in ordered_tasks if task.get("is_aggregated"))
        single_count = len(ordered_tasks) - aggregated_count
        cross_page_count = sum(
            1 for task in ordered_tasks 
            if task.get("is_aggregated") and task["page_range"][0] != task["page_range"][1]
        )
        
        # 7. 构建预翻译数据
        pretranslation_data = {
            "pdf_name": pdf_name,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "parse_mode": "dps" if use_dps else "python",
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(all_tasks),
            "metadata": {
                "total_pages": len(parsed_data.get("pages", [])),
                "total_elements": len(translatable_elements),
                "ordered_elements": len(ordered_elements),
                "unordered_elements": len(unordered_elements),
                "aggregated_tasks": aggregated_count,
                "single_tasks": single_count,
                "unordered_tasks": len(unordered_tasks),
                "cross_page_aggregations": cross_page_count,
                "aggregate_titles": aggregate_titles,
                "parse_mode": "dps" if use_dps else "python"
            },
            "translation_tasks": all_tasks
        }
        
        # 8. 保存预翻译文件
        if not self.save_pretranslation_data(pdf_name, pretranslation_data, use_dps):
            return {
                "success": False,
                "error": "保存预翻译文件失败"
            }
        
        logger.info(
            f"预翻译任务生成完成 ({mode_name}模式): 总任务={len(all_tasks)}, "
            f"聚合任务={aggregated_count}, 独立任务={single_count}, "
            f"无序任务={len(unordered_tasks)}, 跨页聚合={cross_page_count}"
        )
        
        return {
            "success": True,
            "data": pretranslation_data["metadata"],
            "file_path": str(pretrans_path)
        }
