import fitz  # PyMuPDF
import json
import os
import time
from pathlib import Path
from typing import Dict, List
from loguru import logger

from app.services.pdf_id_mapper import get_pdf_id_mapper


class PDFParser:
    """使用PyMuPDF进行PDF行级解析"""
    
    def __init__(self, output_base_dir: str = "storage/parsed"):
        """
        初始化PDF解析器
        
        Args:
            output_base_dir: 解析结果输出的基础目录
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_pdf(self, pdf_path: str, pdf_name: str) -> Dict:
        """
        解析PDF文件，提取行级文本信息
        
        Args:
            pdf_path: PDF文件路径
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            解析结果字典
        """
        t_start = time.time()
        try:
            logger.info(f"[PyMuPDF] 开始解析: {pdf_name}")
            
            # 全局block_id计数器
            block_id_counter = 0
            
            # 打开PDF文件
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # 【优化】使用短ID代替长文件名作为目录名
            mapper = get_pdf_id_mapper()
            pdf_id = mapper.get_or_create_id(pdf_name)
            output_dir = self.output_base_dir / pdf_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"[PyMuPDF] 使用短ID: {pdf_name} -> {pdf_id}")
            
            # 解析结果
            parse_result = {
                "pdf_name": pdf_name,
                "total_pages": total_pages,
                "pages": []
            }
            
            # 逐页解析
            for page_num in range(total_pages):
                page = doc[page_num]
                page_data, block_id_counter = self._parse_page(page, page_num, block_id_counter)
                parse_result["pages"].append(page_data)
            
            # 关闭文档
            doc.close()
            
            json_path = output_dir / "parsed.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(parse_result, f, ensure_ascii=False, indent=2)
            
            t_elapsed = time.time() - t_start
            logger.info(f"✅ [PyMuPDF] 解析成功: {pdf_name} | {total_pages}页 | 耗时: {t_elapsed:.2f}s")
            
            return {
                "success": True,
                "pdf_name": pdf_name,
                "total_pages": total_pages,
                "output_dir": str(output_dir),
                "json_path": str(json_path)
            }
            
        except Exception as e:
            t_elapsed = time.time() - t_start
            logger.error(f"❌ [PyMuPDF] 解析失败: {pdf_name} | 耗时: {t_elapsed:.2f}s | 错误: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_page(self, page: fitz.Page, page_num: int, block_id_counter: int) -> tuple:
        """
        解析单个页面，提取所有文本框（最小单元）
        
        Args:
            page: PyMuPDF页面对象
            page_num: 页码
            block_id_counter: 全局block_id计数器
            
        Returns:
            (页面解析数据, 更新后的计数器)
        """
        # 获取页面尺寸
        rect = page.rect
        
        # 提取文本块
        blocks = page.get_text("dict")["blocks"]
        
        elements_data = []  # 改名为elements，不再是lines

        text_span_count = 0
        image_block_count = 0
        other_block_type_counts = {}

        for block in blocks:
            block_type = block.get("type")
            if block_type == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = (span.get("text") or "").strip()
                        if not span_text:
                            continue

                        block_id_counter += 1
                        text_span_count += 1

                        elements_data.append({
                            "block_id": block_id_counter,
                            "text": span_text,
                            "bbox": span.get("bbox"),
                            "font": span.get("font"),
                            "size": round(span.get("size", 0), 2) if span.get("size") is not None else None,
                            "color": span.get("color"),
                            "type": None,
                            "element_type": "text"
                        })
            elif block_type == 1:
                bbox = block.get("bbox")
                if bbox:
                    block_id_counter += 1
                    image_block_count += 1

                    elements_data.append({
                        "block_id": block_id_counter,
                        "text": "[IMAGE]",
                        "bbox": bbox,
                        "font": None,
                        "size": None,
                        "color": None,
                        "type": None,
                        "element_type": "image",
                        "image_meta": {
                            "xref": block.get("xref"),
                            "width": block.get("width"),
                            "height": block.get("height"),
                            "ext": block.get("ext")
                        }
                    })
            else:
                other_block_type_counts[block_type] = other_block_type_counts.get(block_type, 0) + 1
        
        return {
            "page_num": page_num,
            "page_size": {
                "width": rect.width,
                "height": rect.height
            },
            "total_elements": len(elements_data),
            "elements": elements_data  # 改名为elements
        }, block_id_counter
