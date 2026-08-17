"""
论文版面分析器
分析PDF论文的段落宽度和栏数布局
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter
from loguru import logger

from ..pdf_id_mapper import get_pdf_id_mapper


class PaperAnalyzer:
    """论文版面分析器"""
    
    def __init__(self, parsed_base_dir: str = "storage/parsed"):
        """
        初始化论文分析器
        
        Args:
            parsed_base_dir: 解析结果存储的基础目录
        """
        self.parsed_base_dir = Path(parsed_base_dir)
    
    def get_metadata_path(self, pdf_name: str) -> Path:
        """
        获取文档元数据JSON文件路径
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            元数据文件路径
        """
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "document_metadata.json"
    
    def get_dps_json_path(self, pdf_name: str) -> Path:
        """
        获取DPS结果 JSON文件路径
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            DPS JSON文件路径
        """
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "dps.json"
    
    def get_parsed_json_path(self, pdf_name: str) -> Path:
        """
        获取解析结果JSON文件路径
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            JSON文件路径
        """
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        return self.parsed_base_dir / pdf_id / "parsed.json"
    
    def load_dps_data(self, pdf_name: str) -> Optional[Dict]:
        """
        加载DPS版面分析结果
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            DPS数据字典，如果不存在返回None
        """
        json_path = self.get_dps_json_path(pdf_name)
        
        if not json_path.exists():
            logger.warning(f"DPS结果不存在: {json_path}")
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载DPS数据失败: {str(e)}")
            return None
    
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
    
    def save_metadata(self, pdf_name: str, metadata: Dict) -> bool:
        """
        保存文档元数据
        
        Args:
            pdf_name: PDF文件名
            metadata: 元数据字典
            
        Returns:
            是否保存成功
        """
        metadata_path = self.get_metadata_path(pdf_name)
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"保存文档元数据成功: {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"保存文档元数据失败: {str(e)}")
            return False
    
    def load_metadata(self, pdf_name: str) -> Optional[Dict]:
        """
        加载文档元数据
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            元数据字典，如果不存在返回None
        """
        metadata_path = self.get_metadata_path(pdf_name)
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载文档元数据失败: {str(e)}")
            return None
    
    def analyze_paper(self, pdf_name: str, force: bool = False) -> Dict:
        """
        分析论文版面特征
        
        Args:
            pdf_name: PDF文件名
            force: 是否强制重新分析
            
        Returns:
            分析结果
        """
        # 检查是否已存在元数据
        if not force:
            existing_metadata = self.load_metadata(pdf_name)
            if existing_metadata and existing_metadata.get("paper_layout"):
                logger.info(f"论文版面分析已存在，跳过: {pdf_name}")
                return {
                    "success": True,
                    "skipped": True,
                    "data": existing_metadata
                }
        
        # 加载DPS数据
        dps_data = self.load_dps_data(pdf_name)
        if not dps_data:
            return {
                "success": False,
                "error": "DPS结果不存在"
            }
        
        logger.info(f"开始分析论文版面: {pdf_name}")
        
        try:
            # 分析论文版面（使用DPS结果）
            paper_layout = self._analyze_paper_layout_from_dps(dps_data)
            
            if not paper_layout:
                return {
                    "success": False,
                    "error": "未找到强段落元素"
                }
            
            # 构建元数据
            metadata = {
                "pdf_name": pdf_name,
                "version": "1.0",
                "paper_layout": paper_layout
            }
            
            # 保存元数据
            if not self.save_metadata(pdf_name, metadata):
                return {
                    "success": False,
                    "error": "保存元数据失败"
                }
            
            logger.info(
                f"✅ 论文版面分析完成: {pdf_name} | "
                f"layout={paper_layout['layout_type']} | "
                f"strong_width={paper_layout['strong_paragraph_width']:.2f}px"
            )
            
            return {
                "success": True,
                "data": metadata
            }
            
        except Exception as e:
            logger.error(f"论文版面分析失败: {pdf_name} | 错误: {str(e)}")
            return {
                "success": False,
                "error": f"分析失败: {str(e)}"
            }
    
    def _analyze_paper_layout_from_dps(self, dps_data: Dict) -> Optional[Dict]:
        """
        基于DPS版面分析结果分析论文布局（强段落宽度 + 栏数判断）
        
        Args:
            dps_data: DPS结果数据
            
        Returns:
            论文版面信息，如果未找到强段落返回None
        """
        logger.info("开始分析DPS版面布局...")
        
        # 获取DPS数据结构: data["raw"]["pages"]
        raw_data = dps_data.get("raw", {})
        pages = raw_data.get("pages", [])
        
        if not pages:
            logger.warning("未DPS页面数据")
            return None
        
        # 第一步：收集所有DPS box的宽度信息
        all_boxes = []
        
        # 获取DPS页面宽度（使用第一页的宽度作为参考）
        if not pages or not pages[0].get("width"):
            logger.warning("DPS页面数据中未找到width字段")
            return None
        
        dps_page_width = pages[0].get("width")
        logger.info(f"DPS页面宽度: {dps_page_width}px")
        
        for page in pages:
            page_num = page.get("page_index", 0)
            boxes = page.get("boxes", [])
            
            for box in boxes:
                coordinate = box.get("coordinate")
                if not coordinate or len(coordinate) < 4:
                    continue
                
                # DPS坐标格式: [x0, y0, x1, y1]
                x0, y0, x1, y1 = coordinate
                box_width = x1 - x0
                box_height = y1 - y0
                
                all_boxes.append({
                    "page_num": page_num,
                    "coordinate": coordinate,
                    "box_width": box_width,
                    "box_height": box_height,
                    "x": x0,
                    "y": y0,
                    "label": box.get("label", "unknown")
                })
        
        if not all_boxes:
            logger.warning("未找到DPS box元素")
            return None
        
        # 计算每个box的宽度比例（使用DPS页面宽度）
        for box in all_boxes:
            box["page_width"] = dps_page_width
            box["width_ratio"] = box["box_width"] / dps_page_width
        
        logger.info(f"收集到 {len(all_boxes)} 个DPS box, 页面宽度={dps_page_width}px")
        
        # 第二步：过滤出宽度 > 10% 的box
        wide_boxes = [box for box in all_boxes if box["width_ratio"] > 0.1]
        
        if not wide_boxes:
            logger.warning("未找到宽度>10%的box")
            return None
        
        logger.info(f"过滤后剩余 {len(wide_boxes)} 个宽度>10%的box")
        
        # 第三步：对宽度进行聚类，找到最常见的宽度（强段落）
        width_buckets = Counter()
        
        for box in wide_boxes:
            # 将宽度比例分桶（精度5%）
            bucket_key = round(box["width_ratio"] / 0.05) * 0.05
            width_buckets[bucket_key] += 1
        
        if not width_buckets:
            logger.warning("宽度聚类失败")
            return None
        
        # 找到最常见的宽度桶
        most_common_bucket, count = width_buckets.most_common(1)[0]
        
        # 过滤出属于强段落的box
        strong_boxes = [
            box for box in wide_boxes
            if abs(box["width_ratio"] - most_common_bucket) < 0.025
        ]
        
        if not strong_boxes:
            logger.warning("未找到强段落box")
            return None
        
        # 计算强段落的平均宽度
        avg_strong_width = sum(box["box_width"] for box in strong_boxes) / len(strong_boxes)
        
        logger.info(
            f"强段落识别完成: count={len(strong_boxes)} | "
            f"avg_width={avg_strong_width:.2f}px | "
            f"width_ratio={most_common_bucket:.2%}"
        )
        
        # 第四步：基于强段落box的左上角X坐标判断栏数
        layout_type, column_positions = self._detect_column_layout_from_dps(strong_boxes)
        
        logger.info(f"栏数识别完成: layout_type={layout_type} | columns={len(column_positions)}")
        
        # 第五步：将DPS坐标系的强段落宽度和栏位置转换回PDF坐标系
        # 需要加载parsed.json来获取PDF原始尺寸
        try:
            # 从 dps_data 获取 pdf_name
            pdf_name = dps_data.get("pdf_name")
            if not pdf_name:
                logger.warning("未找到DPS数据中的pdf_name，无法转换坐标")
                # 如果没有pdf_name，直接返回DPS坐标系的宽度（不推荐）
                avg_strong_width_pdf = avg_strong_width
            else:
                parsed_data = self.load_parsed_data(pdf_name)
                if not parsed_data or not parsed_data.get("pages"):
                    logger.warning(f"无法加载parsed数据: {pdf_name}")
                    avg_strong_width_pdf = avg_strong_width
                else:
                    # 获取PDF原始尺寸
                    pdf_page_size = parsed_data["pages"][0].get("page_size", {})
                    pdf_width = pdf_page_size.get("width")
                    
                    if pdf_width and dps_page_width:
                        # 计算缩放比例
                        scale_factor = pdf_width / dps_page_width
                        # 转换强段落宽度
                        avg_strong_width_pdf = avg_strong_width * scale_factor
                        
                        logger.info(
                            f"坐标转换: DPS宽度={avg_strong_width:.2f}px "
                            f"-> PDF宽度={avg_strong_width_pdf:.2f}px "
                            f"(scale={scale_factor:.6f}, dps_page_width={dps_page_width}, pdf_width={pdf_width})"
                        )
                        
                        # 同时转换栏位置X坐标
                        for col_pos in column_positions:
                            original_x = col_pos["x"]
                            col_pos["x"] = round(original_x * scale_factor, 2)
                            logger.debug(f"栏位置X坐标转换: {original_x} -> {col_pos['x']}")
                    else:
                        logger.warning("缺少PDF或DPS页面宽度，无法转换坐标")
                        avg_strong_width_pdf = avg_strong_width
        except Exception as e:
            logger.error(f"坐标转换失败: {str(e)}")
            avg_strong_width_pdf = avg_strong_width
        
        # 构建返回结果（使用转换后的PDF坐标系宽度）
        result = {
            "strong_paragraph_width": round(avg_strong_width_pdf, 2),
            "strong_paragraph_count": len(strong_boxes),
            "layout_type": layout_type,
            "column_count": len(column_positions),
            "column_positions": column_positions
        }
        
        return result
    
    def _analyze_paper_layout(self, parsed_data: Dict) -> Optional[Dict]:
        """
        分析论文版面布局（强段落宽度 + 栏数判断）
        
        Args:
            parsed_data: 解析数据
            
        Returns:
            论文版面信息，如果未找到强段落返回None
        """
        logger.info("开始分析论文版面布局...")
        
        pages = parsed_data.get("pages", [])
        
        # 第一步：收集宽度 > 30% 页面宽度的元素
        width_samples = []  # 存储 (page_num, element, element_width, page_width, width_ratio)
        
        for page in pages:
            page_num = page.get("page_num", 0)
            page_size = page.get("page_size", {})
            page_width = page_size.get("width")
            
            if not page_width or page_width <= 0:
                continue
            
            elements = page.get("elements", [])
            
            for element in elements:
                # 只统计文本类型的元素（排除图片等）
                if element.get("element_type") != "text":
                    continue
                
                # 跳过已合并的子元素
                if element.get("parent_id") or element.get("is_merged"):
                    continue
                
                bbox = element.get("bbox")
                if not bbox or len(bbox) < 4:
                    continue
                
                element_width = bbox[2] - bbox[0]
                width_ratio = element_width / page_width
                
                # 只考虑宽度 > 10% 页面宽度的元素
                if width_ratio > 0.1:
                    width_samples.append({
                        "page_num": page_num,
                        "element": element,
                        "element_width": element_width,
                        "page_width": page_width,
                        "width_ratio": width_ratio,
                        "bbox": bbox
                    })
        
        if not width_samples:
            logger.warning("未找到宽度大于30%页面宽度的元素")
            return None
        
        # 第二步：对宽度进行聚类，找到最常见的宽度（强段落）
        width_buckets = Counter()
        
        for sample in width_samples:
            # 将宽度比例分桶（精度5%）
            bucket_key = round(sample["width_ratio"] / 0.05) * 0.05
            width_buckets[bucket_key] += 1
        
        # 找到最常见的宽度桶
        if not width_buckets:
            logger.warning("宽度聚类失败")
            return None
        
        most_common_bucket, count = width_buckets.most_common(1)[0]
        
        # 过滤出属于强段落的元素
        strong_paragraph_samples = [
            s for s in width_samples 
            if abs(s["width_ratio"] - most_common_bucket) < 0.025
        ]
        
        if not strong_paragraph_samples:
            logger.warning("未找到强段落元素")
            return None
        
        # 计算强段落的平均宽度
        avg_strong_width = sum(s["element_width"] for s in strong_paragraph_samples) / len(strong_paragraph_samples)
        
        logger.info(
            f"强段落识别完成: count={len(strong_paragraph_samples)} | "
            f"avg_width={avg_strong_width:.2f}px | "
            f"width_ratio={most_common_bucket:.2%}"
        )
        
        # 第三步：基于强段落元素的左上角X坐标判断栏数
        layout_type, column_positions = self._detect_column_layout(strong_paragraph_samples)
        
        logger.info(f"栏数识别完成: layout_type={layout_type} | columns={len(column_positions)}")
        
        # 构建返回结果
        result = {
            "strong_paragraph_width": round(avg_strong_width, 2),
            "strong_paragraph_count": len(strong_paragraph_samples),
            "layout_type": layout_type,
            "column_count": len(column_positions),
            "column_positions": column_positions
        }
        
        return result
    
    def _detect_column_layout_from_dps(self, strong_boxes: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        检测栏数布局（通过强段落box左上角X坐标聚类）
        
        Args:
            strong_boxes: 强段落DPS box列表
            
        Returns:
            (布局类型, 栏位置列表)
            布局类型: "single_column" | "double_column" | "triple_column"
            栏位置: [{"x": float, "sample_count": int}, ...]
        """
        # 提取所有左上角X坐标
        x_coords = [box["x"] for box in strong_boxes]
        
        # 对X坐标进行聚类（精度10像素）
        x_buckets = Counter()
        for x in x_coords:
            bucket_key = round(x / 10) * 10
            x_buckets[bucket_key] += 1
        
        # 找到所有显著的X坐标簇（出现次数 >= 总数的10%）
        threshold = len(x_coords) * 0.1
        significant_clusters = [
            (x_pos, count) 
            for x_pos, count in x_buckets.items() 
            if count >= threshold
        ]
        
        # 按X坐标排序
        significant_clusters.sort(key=lambda x: x[0])
        
        # 判断栏数
        cluster_count = len(significant_clusters)
        
        if cluster_count == 1:
            layout_type = "single_column"
        elif cluster_count == 2:
            layout_type = "double_column"
        elif cluster_count >= 3:
            layout_type = "triple_column"
        else:
            # 回退到单栏
            layout_type = "single_column"
            significant_clusters = [(x_buckets.most_common(1)[0][0], x_buckets.most_common(1)[0][1])]
        
        # 为每个栏位置选择一个代表性box
        column_positions = []
        for x_pos, count in significant_clusters:
            column_positions.append({
                "x": round(x_pos, 2),
                "sample_count": count
            })
        
        logger.info(
            f"栏位置聚类: cluster_count={cluster_count} | "
            f"positions={[f'x={p['x']:.2f}' for p in column_positions]}"
        )
        
        return layout_type, column_positions
    
    def _detect_column_layout(self, strong_samples: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        检测栏数布局（通过强段落左上角X坐标聚类）
        
        Args:
            strong_samples: 强段落样本列表
            
        Returns:
            (布局类型, 栏位置列表)
            布局类型: "single_column" | "double_column" | "triple_column"
            栏位置: [{"x": float, "sample_count": int}, ...]
        """
        # 提取所有左上角X坐标
        x_coords = [s["bbox"][0] for s in strong_samples]
        
        # 对X坐标进行聚类（精度10像素）
        x_buckets = Counter()
        for x in x_coords:
            bucket_key = round(x / 10) * 10
            x_buckets[bucket_key] += 1
        
        # 找到所有显著的X坐标簇（出现次数 >= 总数的10%）
        threshold = len(x_coords) * 0.1
        significant_clusters = [
            (x_pos, count) 
            for x_pos, count in x_buckets.items() 
            if count >= threshold
        ]
        
        # 按X坐标排序
        significant_clusters.sort(key=lambda x: x[0])
        
        # 判断栏数
        cluster_count = len(significant_clusters)
        
        if cluster_count == 1:
            layout_type = "single_column"
        elif cluster_count == 2:
            layout_type = "double_column"
        elif cluster_count >= 3:
            layout_type = "triple_column"
        else:
            # 回退到单栏
            layout_type = "single_column"
            significant_clusters = [(x_buckets.most_common(1)[0][0], x_buckets.most_common(1)[0][1])]
        
        # 为每个栏位置选择一个代表性样本
        column_positions = []
        for x_pos, count in significant_clusters:
            column_positions.append({
                "x": round(x_pos, 2),
                "sample_count": count
            })
        
        logger.info(
            f"栏位置聚类: cluster_count={cluster_count} | "
            f"positions={[f'x={p['x']:.2f}' for p in column_positions]}"
        )
        
        return layout_type, column_positions
