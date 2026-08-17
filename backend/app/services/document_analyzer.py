"""
PDF文档特征分析服务
分析PDF文档的版面特征，提取布局参数和统计信息
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter
from loguru import logger

from app.services.pdf_id_mapper import get_pdf_id_mapper


class DocumentAnalyzer:
    """PDF文档特征分析器"""
    
    def __init__(self, parsed_base_dir: str = "storage/parsed"):
        """
        初始化文档分析器
        
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
    
    def analyze_document(self, pdf_name: str, force: bool = False) -> Dict:
        """
        分析PDF文档特征并生成元数据
        
        Args:
            pdf_name: PDF文件名
            force: 是否强制重新分析
            
        Returns:
            分析结果
        """
        # 检查是否已存在元数据
        if not force:
            existing_metadata = self.load_metadata(pdf_name)
            if existing_metadata:
                logger.info(f"文档元数据已存在，跳过分析: {pdf_name}")
                return {
                    "success": True,
                    "skipped": True,
                    "data": existing_metadata
                }
        
        # 加载解析数据
        parsed_data = self.load_parsed_data(pdf_name)
        if not parsed_data:
            return {
                "success": False,
                "error": "解析数据不存在"
            }
        
        logger.info(f"开始分析文档特征: {pdf_name}")
        
        # 初始化元数据结构
        metadata = {
            "pdf_name": pdf_name,
            "version": "1.0",
            "analyzers": []  # 记录已运行的分析器
        }
        
        # 运行各个分析器
        try:
            # 1. 分析强段落参数
            paragraph_analysis = self._analyze_paragraph_width(parsed_data)
            metadata["paragraph_width_analysis"] = paragraph_analysis
            metadata["analyzers"].append("paragraph_width")
            
            # 2. 分析页面布局统计
            layout_stats = self._analyze_layout_statistics(parsed_data)
            metadata["layout_statistics"] = layout_stats
            metadata["analyzers"].append("layout_statistics")
            
            # 3. 分析字体使用情况
            font_analysis = self._analyze_font_usage(parsed_data)
            metadata["font_analysis"] = font_analysis
            metadata["analyzers"].append("font_usage")
            
            # 保存元数据
            if not self.save_metadata(pdf_name, metadata):
                return {
                    "success": False,
                    "error": "保存元数据失败"
                }
            
            logger.info(f"✅ 文档特征分析完成: {pdf_name} | 运行分析器: {len(metadata['analyzers'])}个")
            
            return {
                "success": True,
                "data": metadata
            }
            
        except Exception as e:
            logger.error(f"文档特征分析失败: {pdf_name} | 错误: {str(e)}")
            return {
                "success": False,
                "error": f"分析失败: {str(e)}"
            }
    
    def _analyze_paragraph_width(self, parsed_data: Dict) -> Dict:
        """
        分析段落宽度特征，识别"强段落"
        
        强段落定义：宽度大于页面宽度30%的元素框
        统计方法：对宽度进行聚类，找到出现次数最多的宽度簇
        
        Args:
            parsed_data: 解析数据
            
        Returns:
            段落宽度分析结果
        """
        logger.info("开始分析段落宽度特征...")
        
        pages = parsed_data.get("pages", [])
        
        # 收集所有符合条件的元素宽度
        width_samples = []  # 存储 (page_num, element_width, page_width, width_ratio)
        
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
                
                # 只考虑宽度 > 30% 页面宽度的元素
                if width_ratio > 0.3:
                    width_samples.append({
                        "page_num": page_num,
                        "element_width": round(element_width, 2),
                        "page_width": round(page_width, 2),
                        "width_ratio": round(width_ratio, 4)
                    })
        
        if not width_samples:
            return {
                "has_strong_paragraph": False,
                "reason": "未找到宽度大于30%页面宽度的元素",
                "total_samples": 0
            }
        
        # 对宽度进行聚类分析
        # 使用简单的宽度分桶方法（每5%为一个桶）
        width_buckets = Counter()
        
        for sample in width_samples:
            # 将宽度比例分桶（精度5%）
            bucket_key = round(sample["width_ratio"] / 0.05) * 0.05
            width_buckets[bucket_key] += 1
        
        # 找到最常见的宽度桶
        if not width_buckets:
            return {
                "has_strong_paragraph": False,
                "reason": "宽度聚类失败",
                "total_samples": len(width_samples)
            }
        
        most_common_bucket, count = width_buckets.most_common(1)[0]
        
        # 计算该桶的实际宽度平均值
        bucket_samples = [s for s in width_samples if abs(s["width_ratio"] - most_common_bucket) < 0.025]
        avg_width_ratio = sum(s["width_ratio"] for s in bucket_samples) / len(bucket_samples)
        avg_element_width = sum(s["element_width"] for s in bucket_samples) / len(bucket_samples)
        
        # 判断是否为强段落（至少出现10次或占比超过30%）
        is_strong = count >= 10 or (count / len(width_samples)) > 0.3
        
        result = {
            "has_strong_paragraph": is_strong,
            "strong_paragraph_width_ratio": round(avg_width_ratio, 4),
            "strong_paragraph_width_px": round(avg_element_width, 2),
            "occurrence_count": count,
            "total_samples": len(width_samples),
            "confidence": round(count / len(width_samples), 4),
            "width_distribution": {
                f"{k:.2f}": v for k, v in sorted(width_buckets.items(), key=lambda x: -x[1])
            }
        }
        
        logger.info(
            f"段落宽度分析完成: is_strong={is_strong} | "
            f"width_ratio={result['strong_paragraph_width_ratio']} | "
            f"occurrence={count}/{len(width_samples)}"
        )
        
        return result
    
    def _analyze_layout_statistics(self, parsed_data: Dict) -> Dict:
        """
        分析页面布局统计信息
        
        Args:
            parsed_data: 解析数据
            
        Returns:
            布局统计结果
        """
        logger.info("开始分析页面布局统计...")
        
        pages = parsed_data.get("pages", [])
        total_pages = len(pages)
        
        # 统计各类型元素的数量
        type_counts = Counter()
        element_type_counts = Counter()
        
        # 统计页面尺寸分布
        page_sizes = []
        
        for page in pages:
            page_size = page.get("page_size", {})
            if page_size.get("width") and page_size.get("height"):
                page_sizes.append({
                    "width": round(page_size["width"], 2),
                    "height": round(page_size["height"], 2)
                })
            
            elements = page.get("elements", [])
            
            for element in elements:
                # 统计标注类型
                elem_type = element.get("type")
                if elem_type:
                    type_counts[elem_type] += 1
                
                # 统计元素类型（text/image）
                elem_kind = element.get("element_type", "text")
                element_type_counts[elem_kind] += 1
        
        # 计算平均页面尺寸
        avg_page_size = None
        if page_sizes:
            avg_width = sum(p["width"] for p in page_sizes) / len(page_sizes)
            avg_height = sum(p["height"] for p in page_sizes) / len(page_sizes)
            avg_page_size = {
                "width": round(avg_width, 2),
                "height": round(avg_height, 2)
            }
        
        result = {
            "total_pages": total_pages,
            "avg_page_size": avg_page_size,
            "page_size_distribution": page_sizes[:5],  # 只保存前5页的尺寸
            "annotation_type_counts": dict(type_counts),
            "element_type_counts": dict(element_type_counts),
            "total_elements": sum(element_type_counts.values()),
            "annotated_elements": sum(type_counts.values())
        }
        
        logger.info(
            f"布局统计完成: pages={total_pages} | "
            f"total_elements={result['total_elements']} | "
            f"annotated={result['annotated_elements']}"
        )
        
        return result
    
    def _analyze_font_usage(self, parsed_data: Dict) -> Dict:
        """
        分析字体使用情况
        
        Args:
            parsed_data: 解析数据
            
        Returns:
            字体分析结果
        """
        logger.info("开始分析字体使用情况...")
        
        pages = parsed_data.get("pages", [])
        
        # 统计字体和字号
        font_counts = Counter()
        size_counts = Counter()
        font_size_pairs = Counter()
        
        for page in pages:
            elements = page.get("elements", [])
            
            for element in elements:
                # 只统计文本元素
                if element.get("element_type") != "text":
                    continue
                
                font = element.get("font")
                size = element.get("size")
                
                if font:
                    font_counts[font] += 1
                
                if size is not None:
                    # 将字号分桶（精度0.5）
                    size_bucket = round(size * 2) / 2
                    size_counts[size_bucket] += 1
                
                if font and size is not None:
                    size_bucket = round(size * 2) / 2
                    font_size_pairs[(font, size_bucket)] += 1
        
        # 找到最常用的字体和字号
        most_common_font = font_counts.most_common(1)[0] if font_counts else None
        most_common_size = size_counts.most_common(1)[0] if size_counts else None
        most_common_pair = font_size_pairs.most_common(1)[0] if font_size_pairs else None
        
        result = {
            "total_font_usage": sum(font_counts.values()),
            "unique_fonts": len(font_counts),
            "most_common_font": {
                "font": most_common_font[0],
                "count": most_common_font[1],
                "percentage": round(most_common_font[1] / sum(font_counts.values()), 4)
            } if most_common_font else None,
            "most_common_size": {
                "size": most_common_size[0],
                "count": most_common_size[1],
                "percentage": round(most_common_size[1] / sum(size_counts.values()), 4)
            } if most_common_size else None,
            "most_common_font_size": {
                "font": most_common_pair[0][0],
                "size": most_common_pair[0][1],
                "count": most_common_pair[1],
                "percentage": round(most_common_pair[1] / sum(font_size_pairs.values()), 4)
            } if most_common_pair else None,
            "font_distribution": dict(font_counts.most_common(10)),
            "size_distribution": {k: v for k, v in sorted(size_counts.items(), key=lambda x: -x[1])[:10]}
        }
        
        logger.info(
            f"字体分析完成: unique_fonts={result['unique_fonts']} | "
            f"most_common_font={result['most_common_font']['font'] if result['most_common_font'] else 'N/A'}"
        )
        
        return result
    
    def get_strong_paragraph_width(self, pdf_name: str) -> Optional[Dict]:
        """
        获取强段落宽度参数（便捷方法）
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            强段落宽度信息，如果不存在返回None
        """
        metadata = self.load_metadata(pdf_name)
        if not metadata:
            return None
        
        return metadata.get("paragraph_width_analysis")
