"""
PDF标注服务
处理PDF元素类型标注的相关功能
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
from loguru import logger

# 导入排序服务
from ..sorting.reading_order_service import recalculate_page_reading_order
from ..pdf_id_mapper import get_pdf_id_mapper
from .paper_analyzer import PaperAnalyzer


class AnnotationService:
    """PDF标注服务类"""
    
    # 支持的标注类型
    ANNOTATION_TYPES = [
        "document_title",      # 文档标题
        "section_title",       # 章节标题（大标题）
        "section_title_2",     # 二级标题
        "section_title_3",     # 三级标题
        "paragraph",           # 段落
        "list",                # 列表
        "display_formula",     # 公式
        "formula_caption",     # 公式标题
        "figure",              # 图片
        "figure_caption",      # 图片标题
        "table",               # 表格
        "table_caption",       # 表格标题
        "table_footnote",      # 表格注释
        "abandon"              # 废弃/忽略
    ]
    
    # 类型对应的颜色（用于前端显示）
    TYPE_COLORS = {
        "document_title": "#FF6B6B",      # 红色
        "section_title": "#4ECDC4",       # 青色
        "section_title_2": "#2BB3AD",     # 深青
        "section_title_3": "#73E6DA",     # 浅青
        "paragraph": "#45B7D1",           # 蓝色
        "list": "#96CEB4",                # 绿色
        "display_formula": "#FFEAA7",     # 黄色
        "formula_caption": "#DFE6E9",     # 灰色
        "figure": "#FD79A8",              # 粉色
        "figure_caption": "#FDCB6E",      # 橙色
        "table": "#A29BFE",               # 紫色
        "table_caption": "#74B9FF",       # 浅蓝
        "table_footnote": "#81ECEC",      # 浅青
        "abandon": "#B2BEC3"              # 深灰
    }
    
    def __init__(self, parsed_base_dir: str = "storage/parsed"):
        """
        初始化标注服务
        
        Args:
            parsed_base_dir: 解析结果存储的基础目录
        """
        self.parsed_base_dir = Path(parsed_base_dir)
    
    def get_parsed_json_path(self, pdf_name: str) -> Path:
        """
        获取解析结果JSON文件路径
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            JSON文件路径
        """
        # 【优化】使用短ID代替长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "parsed.json"
    
    def load_parsed_data(self, pdf_name: str) -> Optional[Dict]:
        """
        加载解析数据
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            解析数据字典，如果不存在返回None
        """
        json_path = self.get_parsed_json_path(pdf_name)

        if not json_path.exists():
            logger.warning(f"解析数据不存在: {json_path}")
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载解析数据失败: {str(e)}")
            return None
    
    def save_parsed_data(self, pdf_name: str, data: Dict) -> bool:
        """
        保存解析数据
        
        Args:
            pdf_name: PDF文件名
            data: 解析数据
            
        Returns:
            是否保存成功
        """
        json_path = self.get_parsed_json_path(pdf_name)

        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存解析数据成功: {json_path}")
            return True
        except Exception as e:
            logger.error(f"保存解析数据失败: {str(e)}")
            return False
    
    def annotate_element(
        self, 
        pdf_name: str, 
        page_num: int, 
        block_id: int, 
        element_type: str
    ) -> Dict:
        """
        标注PDF元素类型（通过block_id定位）
        
        Args:
            pdf_name: PDF文件名
            page_num: 页码
            block_id: 元素的全局唯一ID
            element_type: 元素类型
            
        Returns:
            标注结果
        """
        # 验证元素类型
        if element_type not in self.ANNOTATION_TYPES:
            return {
                "success": False,
                "error": f"不支持的元素类型: {element_type}"
            }
        
        # 加载解析数据
        parsed_data = self.load_parsed_data(pdf_name)
        if not parsed_data:
            return {
                "success": False,
                "error": "解析数据不存在"
            }
        
        # 验证页码
        if page_num < 0 or page_num >= len(parsed_data.get("pages", [])):
            return {
                "success": False,
                "error": f"页码超出范围: {page_num}"
            }
        
        page = parsed_data["pages"][page_num]
        elements = page.get("elements", [])
        
        # 通过block_id查找元素
        element_found = False
        for element in elements:
            if element.get("block_id") == block_id:
                element["type"] = element_type
                element_found = True
                break
        
        if not element_found:
            return {
                "success": False,
                "error": f"未找到block_id为 {block_id} 的元素"
            }
        
        # 保存数据
        if not self.save_parsed_data(pdf_name, parsed_data):
            return {
                "success": False,
                "error": "保存标注失败"
            }
        
        return {
            "success": True,
            "data": {
                "pdf_name": pdf_name,
                "page_num": page_num,
                "block_id": block_id,
                "type": element_type,
                "color": self.TYPE_COLORS.get(element_type, "#409EFF")
            }
        }
    
    def get_annotation_types(self) -> Dict:
        """
        获取所有支持的标注类型及其颜色
        
        Returns:
            标注类型配置
        """
        return {
            "types": self.ANNOTATION_TYPES,
            "colors": self.TYPE_COLORS
        }
    
    def clear_annotation(
        self, 
        pdf_name: str, 
        page_num: int, 
        block_id: int
    ) -> Dict:
        """
        清除元素标注（通过block_id定位）
        
        Args:
            pdf_name: PDF文件名
            page_num: 页码
            block_id: 元素的全局唯一ID
            
        Returns:
            清除结果
        """
        # 加载解析数据
        parsed_data = self.load_parsed_data(pdf_name)
        if not parsed_data:
            return {
                "success": False,
                "error": "解析数据不存在"
            }
        
        # 验证页码
        if page_num < 0 or page_num >= len(parsed_data.get("pages", [])):
            return {
                "success": False,
                "error": f"页码超出范围: {page_num}"
            }
        
        page = parsed_data["pages"][page_num]
        elements = page.get("elements", [])
        
        # 通过block_id查找元素
        element_found = False
        for element in elements:
            if element.get("block_id") == block_id:
                element["type"] = None
                element_found = True
                break
        
        if not element_found:
            return {
                "success": False,
                "error": f"未找到block_id为 {block_id} 的元素"
            }
        
        # 保存数据
        if not self.save_parsed_data(pdf_name, parsed_data):
            return {
                "success": False,
                "error": "保存清除操作失败"
            }
        
        return {
            "success": True,
            "data": {
                "pdf_name": pdf_name,
                "page_num": page_num,
                "block_id": block_id,
                "cleared": True
            }
        }
    
    def get_page_annotations(self, pdf_name: str, page_num: int) -> Dict:
        """
        获取指定页面的所有标注
        
        Args:
            pdf_name: PDF文件名
            page_num: 页码
            
        Returns:
            页面标注数据
        """
        parsed_data = self.load_parsed_data(pdf_name)
        if not parsed_data:
            return {
                "success": False,
                "error": "解析数据不存在"
            }
        
        if page_num < 0 or page_num >= len(parsed_data.get("pages", [])):
            return {
                "success": False,
                "error": f"页码超出范围: {page_num}"
            }
        
        page = parsed_data["pages"][page_num]
        elements = page.get("elements", [])
        
        # 统计各类型数量
        type_counts = {}
        annotated_elements = []
        
        for element in elements:
            element_type = element.get("type")
            if element_type:
                type_counts[element_type] = type_counts.get(element_type, 0) + 1
                annotated_elements.append({
                    "block_id": element["block_id"],
                    "type": element_type,
                    "text": element["text"]
                })
        
        return {
            "success": True,
            "data": {
                "pdf_name": pdf_name,
                "page_num": page_num,
                "total_elements": len(elements),
                "annotated_count": len(annotated_elements),
                "type_counts": type_counts,
                "annotated_elements": annotated_elements
            }
        }
    
    def batch_annotate(
        self,
        pdf_name: str,
        annotations: List[Dict],
        use_dps: bool = False,
    ) -> Dict:
        """
        批量标注PDF元素（性能优化版本，通过block_id定位，支持合并标注）
        
        Args:
            pdf_name: PDF文件名
            annotations: 标注列表，每项包含 page_num, block_id, element_type
                        或包含 is_merge, source_elements 用于合并标注
            
        Returns:
            批量标注结果
        """
        import random
        import string

        if use_dps:
            return self.batch_annotate_dps(pdf_name=pdf_name, annotations=annotations)
        
        # 加载解析数据（只加载一次）
        parsed_data = self.load_parsed_data(pdf_name)
        if not parsed_data:
            return {
                "success": False,
                "error": "解析数据不存在"
            }
        
        success_count = 0
        error_count = 0
        errors = []
        
        # 批量处理所有标注
        for idx, annotation in enumerate(annotations):
            try:
                # 优先检查是否是拆解操作（无论是否有 is_merge 标记）
                if annotation.get("_unmerge_from"):
                    # 这是拆解操作，需要删除合并元素并还原源元素
                    result = self._handle_unmerge_operation(
                        parsed_data, 
                        annotation, 
                        idx
                    )
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(result["error"])
                    continue
                
                # 检查是否是合并标注
                if annotation.get("is_merge"):
                    # 处理合并标注
                    result = self._handle_merge_annotation(parsed_data, annotation, idx)
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(result["error"])
                else:
                    # 处理普通标注
                    page_num = annotation["page_num"]
                    block_id = annotation["block_id"]
                    element_type = annotation.get("element_type")
                    
                    # 验证元素类型（如果不是清除操作）
                    if element_type is not None and element_type not in self.ANNOTATION_TYPES:
                        errors.append(f"索引{idx}: 不支持的元素类型 {element_type}")
                        error_count += 1
                        continue
                    
                    # 验证页码
                    if page_num < 0 or page_num >= len(parsed_data.get("pages", [])):
                        errors.append(f"索引{idx}: 页码超出范围 {page_num}")
                        error_count += 1
                        continue
                    
                    page = parsed_data["pages"][page_num]
                    elements = page.get("elements", [])
                    
                    # 通过block_id查找元素
                    element_found = False
                    for element in elements:
                        if element.get("block_id") == block_id:
                            element["type"] = element_type
                            
                            # 如果有 dps_label 字段，保存它（用于后续同步reading_order）
                            if "dps_label" in annotation:
                                element["dps_label"] = annotation["dps_label"]
                            
                            # 如果有 reading_order 字段，更新它
                            if "reading_order" in annotation:
                                element["reading_order"] = annotation["reading_order"]
                            
                            element_found = True
                            success_count += 1
                            break
                    
                    if not element_found:
                        errors.append(f"索引{idx}: 未找到block_id为 {block_id} 的元素")
                        error_count += 1
                
            except Exception as e:
                errors.append(f"索引{idx}: {str(e)}")
                error_count += 1
        
        # 只保存一次数据
        if success_count > 0:
            # 收集所有被修改的页面
            modified_pages = set()
            has_manual_reading_order = False  # 是否有手动设置的reading_order
            
            for annotation in annotations:
                page_num = annotation.get('page_num')
                if page_num is not None:
                    modified_pages.add(page_num)
                
                # 检查是否有手动设置的reading_order
                if 'reading_order' in annotation:
                    has_manual_reading_order = True
            
            # 只有在没有手动设置 reading_order 的情况下才自动重新计算
            if not has_manual_reading_order:
                # 为每个修改的页面重新计算阅读顺序
                for page_num in modified_pages:
                    parsed_data = recalculate_page_reading_order(parsed_data, page_num)
                    logger.info(f"已重新计算页面 {page_num} 的阅读顺序")
            else:
                logger.info("检测到手动设置的阅读顺序，跳过自动计算")
            
            # 保存数据
            if not self.save_parsed_data(pdf_name, parsed_data):
                return {
                    "success": False,
                    "error": "保存标注失败"
                }
        
        return {
            "success": True,
            "data": {
                "total": len(annotations),
                "success": success_count,
                "error": error_count,
                "errors": errors if errors else None
            }
        }

    def load_dps_data(self, pdf_name: str) -> Optional[Dict]:
        json_path = self.get_dps_json_path(pdf_name)

        if not json_path.exists():
            logger.warning(f"DPS解析数据不存在: {json_path}")
            return None

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载DPS解析数据失败: {str(e)}")
            return None

    def save_dps_data(self, pdf_name: str, data: Dict) -> bool:
        json_path = self.get_dps_json_path(pdf_name)

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存DPS解析数据成功: {json_path}")
            return True
        except Exception as e:
            logger.error(f"保存DPS解析数据失败: {str(e)}")
            return False

    def batch_annotate_dps(self, pdf_name: str, annotations: List[Dict]) -> Dict:
        dps_data = self.load_dps_data(pdf_name)
        if not dps_data:
            return {"success": False, "error": "DPS解析数据不存在"}

        raw = dps_data.get("raw") or {}
        pages = raw.get("pages") or []
        if not isinstance(pages, list):
            return {"success": False, "error": "DPS解析数据格式错误: raw.pages 不是数组"}

        def find_page(page_num: int) -> Optional[Dict]:
            for p in pages:
                if int(p.get("page_index", -1)) == int(page_num):
                    return p
            if 0 <= page_num < len(pages):
                return pages[page_num]
            return None

        def resolve_box(page_obj: Dict, dps_block_id_or_index: int) -> Optional[Dict]:
            boxes = page_obj.get("boxes") or []
            if not isinstance(boxes, list):
                return None

            for b in boxes:
                if int(b.get("DPS_block_id", -1)) == int(dps_block_id_or_index):
                    return b

            idx0 = int(dps_block_id_or_index) - 1
            if 0 <= idx0 < len(boxes):
                return boxes[idx0]

            return None

        success_count = 0
        error_count = 0
        errors = []

        for idx, annotation in enumerate(annotations):
            try:
                if annotation.get("is_merge") or annotation.get("_unmerge_from"):
                    errors.append(f"索引{idx}: DPS模式不支持合并/拆解操作")
                    error_count += 1
                    continue

                page_num = int(annotation.get("page_num"))
                block_id = annotation.get("block_id")
                if block_id is None:
                    errors.append(f"索引{idx}: 缺少 block_id")
                    error_count += 1
                    continue

                element_type = annotation.get("element_type")
                if element_type is not None and element_type not in self.ANNOTATION_TYPES:
                    errors.append(f"索引{idx}: 不支持的元素类型 {element_type}")
                    error_count += 1
                    continue

                if not isinstance(block_id, str) or not block_id.startswith("dps_"):
                    errors.append(f"索引{idx}: DPS模式 block_id 格式错误: {block_id}")
                    error_count += 1
                    continue

                parts = block_id.split("_", 2)
                if len(parts) < 3:
                    errors.append(f"索引{idx}: DPS模式 block_id 格式错误: {block_id}")
                    error_count += 1
                    continue

                try:
                    dps_id = int(parts[2])
                except Exception:
                    errors.append(f"索引{idx}: DPS模式 block_id 无法解析: {block_id}")
                    error_count += 1
                    continue

                page_obj = find_page(page_num)
                if not page_obj:
                    errors.append(f"索引{idx}: 页码超出范围 {page_num}")
                    error_count += 1
                    continue

                box = resolve_box(page_obj, dps_id)
                if not box:
                    errors.append(f"索引{idx}: 未找到对应的DPS box: block_id={block_id}")
                    error_count += 1
                    continue

                if element_type is None:
                    if "type" in box:
                        box.pop("type", None)
                else:
                    box["type"] = element_type

                if "reading_order" in annotation:
                    box["reading_order"] = annotation.get("reading_order")

                success_count += 1
            except Exception as e:
                errors.append(f"索引{idx}: {str(e)}")
                error_count += 1

        if success_count > 0:
            if not self.save_dps_data(pdf_name, dps_data):
                return {"success": False, "error": "保存DPS标注失败"}

        return {
            "success": True,
            "data": {
                "total": len(annotations),
                "success": success_count,
                "error": error_count,
                "errors": errors if errors else None,
            },
        }
    
    def _handle_merge_annotation(self, parsed_data: Dict, annotation: Dict, idx: int) -> Dict:
        """
        处理合并标注
        
        Args:
            parsed_data: 解析数据
            annotation: 合并标注信息
            idx: 索引（用于错误提示）
            
        Returns:
            处理结果
        """
        import random
        import string
        
        try:
            page_num = annotation["page_num"]
            element_type = annotation["element_type"]
            source_elements = annotation["source_elements"]
            
            # 验证页码
            if page_num < 0 or page_num >= len(parsed_data.get("pages", [])):
                return {
                    "success": False,
                    "error": f"索引{idx}: 页码超出范围 {page_num}"
                }
            
            page = parsed_data["pages"][page_num]
            elements = page.get("elements", [])
            
            # 【关键修复】按照 block_id 排序 source_elements
            # block_id 可能是字符串或数字，提取数字部分进行排序
            def extract_number(block_id):
                """ 从 block_id 中提取数字 """
                import re
                id_str = str(block_id)
                numbers = re.findall(r'\d+', id_str)
                return int(numbers[-1]) if numbers else 0  # 取最后一个数字
            
            sorted_source_elements = sorted(
                source_elements,
                key=lambda elem: extract_number(elem.get("block_id", 0))
            )
            
            logger.info(f"合并元素排序: 原顺序={[e['block_id'] for e in source_elements]}, "
                       f"排序后={[e['block_id'] for e in sorted_source_elements]}")
            
            # 计算最小包围矩形
            bboxes = [elem["bbox"] for elem in sorted_source_elements if elem.get("bbox")]
            if not bboxes:
                return {
                    "success": False,
                    "error": f"索引{idx}: 源元素缺少bbox信息"
                }
            
            min_x = min(bbox[0] for bbox in bboxes)
            min_y = min(bbox[1] for bbox in bboxes)
            max_x = max(bbox[2] for bbox in bboxes)
            max_y = max(bbox[3] for bbox in bboxes)
            merged_bbox = [min_x, min_y, max_x, max_y]
            
            # 【关键修复】按排序后的顺序合并文本和收集block_id
            source_ids = [elem["block_id"] for elem in sorted_source_elements]
            merged_text = " ".join(elem["text"] for elem in sorted_source_elements if elem.get("text"))
            
            logger.info(f"合并后的文本: {merged_text[:100]}...")
            
            # 生成新的block_id
            random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            merged_block_id = f"p{page_num}_merged_{random_suffix}"
            
            # 创建合并元素
            merged_element = {
                "block_id": merged_block_id,
                "bbox": merged_bbox,
                "text": merged_text,
                "type": element_type,
                "is_merged": True,
                "source_ids": source_ids
            }
            
            # 如果有 dps_label 字段，保存它（用于后续同步reading_order）
            if "dps_label" in annotation:
                merged_element["dps_label"] = annotation["dps_label"]
            
            # 如果有 reading_order 字段，保存它（来自DPS的阅读顺序）
            if "reading_order" in annotation:
                merged_element["reading_order"] = annotation["reading_order"]
            
            # 将合并元素添加到页面元素列表末尾
            elements.append(merged_element)
            
            # 更新源元素，添加is_merged和parent_id属性
            for element in elements:
                if element.get("block_id") in source_ids:
                    element["is_merged"] = True
                    element["parent_id"] = merged_block_id
            
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"索引{idx}: 合并标注失败 - {str(e)}"
            }
    
    def _handle_unmerge_operation(self, parsed_data: Dict, annotation: Dict, idx: int) -> Dict:
        """
        处理拆解合并元素的操作
        
        Args:
            parsed_data: 解析数据
            annotation: 拆解标注信息
            idx: 索引（用于错误提示）
            
        Returns:
            处理结果
        """
        try:
            page_num = annotation["page_num"]
            merged_block_id = annotation["_unmerge_from"]
            
            # 验证页码
            if page_num < 0 or page_num >= len(parsed_data.get("pages", [])):
                return {
                    "success": False,
                    "error": f"索引{idx}: 页码超出范围 {page_num}"
                }
            
            page = parsed_data["pages"][page_num]
            elements = page.get("elements", [])
            
            # 查找合并元素（支持字符串和整数类型block_id）
            merged_element = None
            for element in elements:
                elem_id = element.get("block_id")
                # 支持字符串和整数类型的比较
                if str(elem_id) == str(merged_block_id) or elem_id == merged_block_id:
                    merged_element = element
                    break
            
            if not merged_element:
                return {
                    "success": False,
                    "error": f"索引{idx}: 未找到合并元素 {merged_block_id}"
                }
            
            # 还原所有源元素的状态
            if merged_element.get("source_ids"):
                for element in elements:
                    if element.get("block_id") in merged_element["source_ids"]:
                        # 清除 is_merged 和 parent_id
                        if "is_merged" in element:
                            del element["is_merged"]
                        if "parent_id" in element:
                            del element["parent_id"]
            
            # 删除合并元素
            page["elements"] = [el for el in elements if str(el.get("block_id")) != str(merged_block_id) and el.get("block_id") != merged_block_id]
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"拆解操作异常: {str(e)}")
            return {
                "success": False,
                "error": f"索引{idx}: 拆解操作失败 - {str(e)}"
            }

    def get_dps_json_path(self, pdf_name: str) -> Path:
        # 【优化】使用短ID代替长文件名作为目录名
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "dps.json"

    def sync_reading_order_from_dps(self, pdf_name: str) -> Dict:
        """
        将DPS解析结果中的reading_order同步到Python解析结果
        这是首次解析时的初始化操作，直接写入，不调用阅读顺序计算器
        
        Args:
            pdf_name: PDF名称
            
        Returns:
            Dict: 操作结果
        """
        parsed_json_path = self.get_parsed_json_path(pdf_name)
        dps_json_path = self.get_dps_json_path(pdf_name)

        if not parsed_json_path.exists():
            legacy_parsed = self.parsed_base_dir / pdf_name / f"{pdf_name}_parsed.json"
            if legacy_parsed.exists():
                parsed_json_path = legacy_parsed
            else:
                return {"success": False, "error": f"解析JSON不存在: {parsed_json_path}"}
        if not dps_json_path.exists():
            legacy_dps = self.parsed_base_dir / pdf_name / f"{pdf_name}_dps.json"
            if legacy_dps.exists():
                dps_json_path = legacy_dps
            else:
                return {"success": False, "error": f"DPS JSON不存在: {dps_json_path}"}

        try:
            # 读取DPS结果
            with open(dps_json_path, "r", encoding="utf-8") as f:
                dps_payload = json.load(f)
            
            # 读取Python解析结果
            parsed_data = self.load_parsed_data(pdf_name)
            if not parsed_data:
                return {"success": False, "error": "解析数据不存在"}

            dps_raw = dps_payload.get("raw") or {}
            dps_pages = dps_raw.get("pages") or []
            parsed_pages = parsed_data.get("pages") or []
            
            synced_count = 0
            total_elements = 0
            
            logger.info(
                f"开始同步DPS阅读顺序: pdf_name={pdf_name} dps_pages={len(dps_pages)} parsed_pages={len(parsed_pages)}"
            )

            # 遍历每一页
            for dps_page in dps_pages:
                page_num = int(dps_page.get("page_index", 0))
                if page_num < 0 or page_num >= len(parsed_pages):
                    logger.warning(f"DPS page_index越界，跳过: page_index={page_num} parsed_pages={len(parsed_pages)}")
                    continue

                dps_boxes = dps_page.get("boxes") or []
                parsed_page = parsed_pages[page_num]
                parsed_elements = parsed_page.get("elements") or []
                
                total_elements += len(parsed_elements)

                # 为每个DPS box构建坐标索引（用于快速匹配）
                # key: (label, bbox的近似坐标), value: reading_order
                dps_reading_order_map = {}
                for box in dps_boxes:
                    reading_order = box.get("reading_order")
                    if reading_order is None:
                        continue
                    
                    label = box.get("label", "")
                    coord = box.get("coordinate", [])
                    if len(coord) < 4:
                        continue
                    
                    # 使用四舍五入的坐标作为key（允许小范围误差）
                    coord_key = (
                        label,
                        round(coord[0]),
                        round(coord[1]),
                        round(coord[2]),
                        round(coord[3])
                    )
                    dps_reading_order_map[coord_key] = reading_order

                # 匹配Python解析的元素
                for element in parsed_elements:
                    # 只处理已标注的元素（有type字段）
                    if not element.get("type"):
                        continue
                    
                    # 获取元素的DPS标签（如果有预标注信息）
                    dps_label = element.get("dps_label")
                    if not dps_label:
                        continue
                    
                    bbox = element.get("bbox", [])
                    if len(bbox) < 4:
                        continue
                    
                    # 构建相同的坐标key
                    coord_key = (
                        dps_label,
                        round(bbox[0]),
                        round(bbox[1]),
                        round(bbox[2]),
                        round(bbox[3])
                    )
                    
                    # 查找对应的reading_order
                    reading_order = dps_reading_order_map.get(coord_key)
                    if reading_order is not None:
                        element["reading_order"] = reading_order
                        synced_count += 1

            # 保存更新后的数据
            if not self.save_parsed_data(pdf_name, parsed_data):
                return {"success": False, "error": "保存同步结果失败"}

            logger.info(
                f"DPS阅读顺序同步完成: pdf_name={pdf_name} total_elements={total_elements} synced_count={synced_count}"
            )
            
            return {
                "success": True,
                "data": {
                    "total_elements": total_elements,
                    "synced_count": synced_count,
                    "coverage_rate": f"{(synced_count * 100 // total_elements) if total_elements > 0 else 0}%"
                }
            }

        except Exception as e:
            logger.error(f"同步DPS阅读顺序失败: pdf_name={pdf_name} error={str(e)}")
            return {"success": False, "error": f"同步失败: {str(e)}"}

    def preannotate_from_dps(self, pdf_name: str, *, force: bool = False) -> Dict:
        parsed_json_path = self.get_parsed_json_path(pdf_name)
        dps_json_path = self.get_dps_json_path(pdf_name)

        if not parsed_json_path.exists():
            legacy_parsed = self.parsed_base_dir / pdf_name / f"{pdf_name}_parsed.json"
            if legacy_parsed.exists():
                parsed_json_path = legacy_parsed
            else:
                return {"success": False, "error": f"解析JSON不存在: {parsed_json_path}"}
        if not dps_json_path.exists():
            legacy_dps = self.parsed_base_dir / pdf_name / f"{pdf_name}_dps.json"
            if legacy_dps.exists():
                dps_json_path = legacy_dps
            else:
                return {"success": False, "error": f"DPS JSON不存在: {dps_json_path}"}

        try:
            with open(dps_json_path, "r", encoding="utf-8") as f:
                dps_payload = json.load(f)
        except Exception as e:
            return {"success": False, "error": f"读取DPS JSON失败: {str(e)} path={dps_json_path}"}

        dps_raw = dps_payload.get("raw") or {}
        dps_req_id = dps_raw.get("req_id") or (dps_payload.get("meta") or {}).get("req_id")
        dps_generated_at = dps_payload.get("generated_at")

        parsed_data = self.load_parsed_data(pdf_name)
        if not parsed_data:
            return {"success": False, "error": "解析数据不存在"}

        pre_meta = parsed_data.get("dps_preannotation") or {}
        if not force and pre_meta.get("dps_req_id") == dps_req_id and pre_meta.get("dps_generated_at") == dps_generated_at:
            logger.info(
                f"DPS预标注已完成，跳过: pdf_name={pdf_name} dps_req_id={dps_req_id} generated_at={dps_generated_at}"
            )
            return {"success": True, "skipped": True, "data": pre_meta}

        label_to_type = {
            # PP-DocLayoutV2 / PPStructure 标签映射
            "title": "section_title",  # PPStructure 使用 title 而不是 paragraph_title
            "text": "paragraph",
            "figure": "figure",
            "figure_caption": "figure_caption",
            "table": "table",
            "table_caption": "table_caption",
            "header": "abandon",  # 页眉应该被标记为废弃
            "footer": "abandon",
            "reference": "abandon",
            "equation": "display_formula",
            
            # 兼容旧的标签格式（LayoutDetection 3.x）
            "doc_title": "document_title",
            "paragraph_title": "section_title",
            "abstract": "paragraph",
            "display_formula": "display_formula",
            "formula": "display_formula",
            "formula_number": "formula_caption",
            "figure_title": "figure_caption",
            "chart": "figure",
            "image": "figure",
            "footnote": "abandon",
            "reference_content": "abandon",
            "number": "abandon",
        }

        label_priority = {
            # PP-DocLayoutV2 / PPStructure 标签优先级
            "title": 90,
            "text": 10,
            "figure": 65,
            "figure_caption": 60,
            "table": 70,
            "table_caption": 60,
            "equation": 70,
            "header": 0,
            "footer": 0,
            "reference": 0,
            
            # 兼容旧的标签格式
            "doc_title": 100,
            "paragraph_title": 90,
            "abstract": 80,
            "display_formula": 70,
            "formula": 70,
            "chart": 65,
            "image": 65,
            "figure_title": 60,
            "formula_number": 60,
            "reference_content": 0,
            "number": 0,
            "footnote": 0,
        }

        def _normalize_bbox(bbox: List[float]) -> Optional[List[float]]:
            if not bbox or len(bbox) != 4:
                return None
            x0, y0, x1, y1 = bbox
            if x0 > x1:
                x0, x1 = x1, x0
            if y0 > y1:
                y0, y1 = y1, y0
            return [float(x0), float(y0), float(x1), float(y1)]

        def _bbox_center(bbox: List[float]) -> tuple:
            return ((bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0)

        def _point_in_bbox(pt: tuple, bbox: List[float]) -> bool:
            return bbox[0] <= pt[0] <= bbox[2] and bbox[1] <= pt[1] <= bbox[3]

        used_block_ids = set()
        merge_annotations: List[Dict] = []
        total_boxes = 0
        processed_boxes = 0
        skipped_boxes = 0
        selected_elements_total = 0
        merged_ops = 0
        single_ops = 0
        per_label_stats: Dict[str, Dict[str, int]] = {}

        dps_pages = dps_raw.get("pages") or []
        parsed_pages = parsed_data.get("pages") or []
        logger.info(
            f"开始DPS预标注: pdf_name={pdf_name} dps_pages={len(dps_pages)} parsed_pages={len(parsed_pages)} "
            f"dps_req_id={dps_req_id} generated_at={dps_generated_at} force={force}"
        )

        for dps_page in dps_pages:
            page_num = int(dps_page.get("page_index", 0))
            if page_num < 0 or page_num >= len(parsed_pages):
                logger.warning(f"DPS page_index越界，跳过: page_index={page_num} parsed_pages={len(parsed_pages)}")
                continue

            dps_w = dps_page.get("width")
            dps_h = dps_page.get("height")
            parsed_size = (parsed_pages[page_num].get("page_size") or {})
            parsed_w = parsed_size.get("width")
            parsed_h = parsed_size.get("height")

            if dps_w and parsed_w:
                scale_x = float(parsed_w) / float(dps_w)
            else:
                scale_x = 1.0
            if dps_h and parsed_h:
                scale_y = float(parsed_h) / float(dps_h)
            else:
                scale_y = 1.0

            elements = (parsed_pages[page_num].get("elements") or [])

            def _eligible_element(el: Dict) -> bool:
                if el.get("parent_id"):
                    return False
                if el.get("is_merged"):
                    return False
                if el.get("type") is not None:
                    return False
                if not el.get("bbox"):
                    return False
                if el.get("block_id") in used_block_ids:
                    return False
                return True

            eligible_elements = [el for el in elements if _eligible_element(el)]

            boxes = dps_page.get("boxes") or []
            total_boxes += len(boxes)

            candidate_boxes = []
            for box in boxes:
                label = box.get("label")
                mapped_type = label_to_type.get(label)
                if not mapped_type:
                    continue
                coord = _normalize_bbox(box.get("coordinate"))
                if not coord:
                    continue
                pdf_bbox = _normalize_bbox([coord[0] * scale_x, coord[1] * scale_y, coord[2] * scale_x, coord[3] * scale_y])
                if not pdf_bbox:
                    continue
                area = max(0.0, (pdf_bbox[2] - pdf_bbox[0]) * (pdf_bbox[3] - pdf_bbox[1]))
                candidate_boxes.append(
                    {
                        "label": label,
                        "element_type": mapped_type,
                        "bbox": pdf_bbox,
                        "priority": label_priority.get(label, 0),
                        "area": area,
                        "reading_order": box.get("reading_order"),  # 保存DPS的阅读顺序
                    }
                )

            candidate_boxes.sort(key=lambda b: (-b["priority"], b["area"]))

            for box in candidate_boxes:
                label = box["label"]
                element_type = box["element_type"]
                box_bbox = box["bbox"]
                reading_order = box.get("reading_order")  # 获取DPS的阅读顺序

                allow_kinds = {"text"}
                if label in {"table", "chart", "image"}:
                    allow_kinds = {"text", "image"}

                selected = []
                for el in eligible_elements:
                    el_kind = el.get("element_type") or "text"
                    if el_kind not in allow_kinds:
                        continue
                    el_bbox = _normalize_bbox(el.get("bbox"))
                    if not el_bbox:
                        continue
                    if not _point_in_bbox(_bbox_center(el_bbox), box_bbox):
                        continue
                    selected.append(
                        {
                            "block_id": el.get("block_id"),
                            "bbox": el_bbox,
                            "text": el.get("text") or "",
                        }
                    )

                if not selected:
                    skipped_boxes += 1
                    continue

                selected.sort(key=lambda e: (e["bbox"][1], e["bbox"][0], str(e["block_id"])))
                for e in selected:
                    used_block_ids.add(e["block_id"])

                selected_elements_total += len(selected)
                per_label_stats.setdefault(label, {"boxes": 0, "elements": 0, "merge": 0, "single": 0})
                per_label_stats[label]["boxes"] += 1
                per_label_stats[label]["elements"] += len(selected)

                if len(selected) >= 2:
                    merge_annotations.append(
                        {
                            "page_num": page_num,
                            "is_merge": True,
                            "element_type": element_type,
                            "dps_label": label,  # 保存DPS原始标签用于后续匹配reading_order
                            "reading_order": reading_order,  # 直接从DPS获取阅读顺序
                            "source_elements": selected,
                        }
                    )
                    merged_ops += 1
                    per_label_stats[label]["merge"] += 1
                else:
                    merge_annotations.append(
                        {
                            "page_num": page_num,
                            "block_id": selected[0]["block_id"],
                            "element_type": element_type,
                            "dps_label": label,  # 保存DPS原始标签用于后续匹配reading_order
                            "reading_order": reading_order,  # 直接从DPS获取阅读顺序
                        }
                    )
                    single_ops += 1
                    per_label_stats[label]["single"] += 1

                processed_boxes += 1

        logger.info(
            f"DPS预标注构建完成: pdf_name={pdf_name} total_boxes={total_boxes} processed={processed_boxes} "
            f"skipped={skipped_boxes} annos={len(merge_annotations)} merged_ops={merged_ops} single_ops={single_ops} "
            f"selected_elements={selected_elements_total}"
        )
        if per_label_stats:
            logger.info(f"DPS预标注label统计: {per_label_stats}")

        if not merge_annotations:
            parsed_data["dps_preannotation"] = {
                "dps_req_id": dps_req_id,
                "dps_generated_at": dps_generated_at,
                "total_boxes": total_boxes,
                "processed_boxes": processed_boxes,
                "skipped_boxes": skipped_boxes,
                "merged_ops": 0,
                "single_ops": 0,
                "annotations": 0,
                "selected_elements": 0,
                "labels": per_label_stats,
                "note": "无可用匹配元素，未执行写入",
            }
            if not self.save_parsed_data(pdf_name, parsed_data):
                return {"success": False, "error": "保存预标注元数据失败"}
            return {"success": True, "data": parsed_data["dps_preannotation"]}

        batch_result = self.batch_annotate(pdf_name, merge_annotations)
        if not batch_result.get("success"):
            return {"success": False, "error": f"批量写入预标注失败: {batch_result.get('error')}"}

        parsed_data2 = self.load_parsed_data(pdf_name) or {}
        parsed_data2["dps_preannotation"] = {
            "dps_req_id": dps_req_id,
            "dps_generated_at": dps_generated_at,
            "total_boxes": total_boxes,
            "processed_boxes": processed_boxes,
            "skipped_boxes": skipped_boxes,
            "merged_ops": merged_ops,
            "single_ops": single_ops,
            "annotations": len(merge_annotations),
            "selected_elements": selected_elements_total,
            "labels": per_label_stats,
        }
        if not self.save_parsed_data(pdf_name, parsed_data2):
            return {"success": False, "error": "保存预标注元数据失败"}

        logger.info(f"DPS预标注写入完成: pdf_name={pdf_name} merged_ops={merged_ops} single_ops={single_ops}")
        
        # 预标注完成后自动分析论文版面
        logger.info(f"开始分析论文版面: pdf_name={pdf_name}")
        analyzer = PaperAnalyzer(self.parsed_base_dir)
        analysis_result = analyzer.analyze_paper(pdf_name, force=False)
        
        if analysis_result.get("success"):
            logger.info(f"✅ 论文版面分析完成: pdf_name={pdf_name}")
            # 将分析结果摘要添加到返回数据中
            result_data = parsed_data2["dps_preannotation"].copy()
            paper_layout = analysis_result.get("data", {}).get("paper_layout", {})
            result_data["paper_layout"] = {
                "layout_type": paper_layout.get("layout_type"),
                "strong_paragraph_width": paper_layout.get("strong_paragraph_width"),
                "column_count": paper_layout.get("column_count"),
                "column_positions": paper_layout.get("column_positions", [])
            }
            return {"success": True, "data": result_data}
        else:
            logger.warning(f"⚠️ 论文版面分析失败: pdf_name={pdf_name} error={analysis_result.get('error')}")
            # 分析失败不影响预标注结果
            return {"success": True, "data": parsed_data2["dps_preannotation"]}
