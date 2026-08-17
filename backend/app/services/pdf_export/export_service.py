"""
PDF导出服务
整合字体管理、PDF生成和翻译数据，提供完整的PDF导出功能
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from loguru import logger

from .font_manager import FontManager
from .pdf_generator import PDFGenerator
from ..pdf_id_mapper import get_pdf_id_mapper


class PDFExportService:
    """
    PDF导出服务
    负责将翻译结果导出为各种格式的PDF文件
    """
    
    # 支持的导出模式
    EXPORT_MODES = {
        "overlay": "覆盖模式 - 在原PDF上叠加译文",
        "side_by_side": "左右对照 - 原文和译文并排显示",
        "interleaved": "交替排列 - 原文页后跟译文页",
        "translation_only": "纯译文 - 只包含翻译结果",
    }
    
    def __init__(
        self,
        parsed_base_dir: str = "storage/parsed",
        uploads_dir: str = "storage/uploads",
        output_dir: str = "storage/exports",
        fonts_dir: Optional[str] = None
    ):
        """
        初始化PDF导出服务
        
        Args:
            parsed_base_dir: 解析结果存储目录
            uploads_dir: 上传文件存储目录
            output_dir: 导出文件输出目录
            fonts_dir: 字体文件目录
        """
        self.parsed_base_dir = Path(parsed_base_dir)
        self.uploads_dir = Path(uploads_dir)
        self.output_dir = Path(output_dir)
        
        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化字体管理器
        if fonts_dir:
            self.font_manager = FontManager(fonts_dir)
        else:
            # 默认使用服务目录下的fonts文件夹
            default_fonts_dir = Path(__file__).parent / "fonts"
            self.font_manager = FontManager(str(default_fonts_dir))
        
        # 初始化PDF生成器
        self.pdf_generator = PDFGenerator(self.font_manager)
        
        logger.info(f"PDF导出服务初始化完成: output_dir={self.output_dir}")
    
    def get_pdf_paths(self, pdf_name: str) -> Dict[str, Optional[Path]]:
        """
        获取PDF相关文件路径
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            路径字典
        """
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        parsed_dir = self.parsed_base_dir / pdf_id
        
        # 查找源PDF文件
        source_pdf = None
        for file in self.uploads_dir.glob(f"*_{pdf_name}.pdf"):
            source_pdf = file
            break
        
        # 如果没找到带UUID的，尝试直接匹配
        if not source_pdf:
            direct_pdf = self.uploads_dir / f"{pdf_name}.pdf"
            if direct_pdf.exists():
                source_pdf = direct_pdf
        
        return {
            "source_pdf": source_pdf,
            "parsed_dir": parsed_dir,
            "parsed_json": parsed_dir / "parsed.json",
            "dps_json": parsed_dir / "dps.json",
            "translation_json": parsed_dir / "translation.json",
            "translation_dps_json": parsed_dir / "translation_dps.json",
            "pretranslation_json": parsed_dir / "pretranslation.json",
        }
    
    def load_translation_data(
        self,
        pdf_name: str,
        use_dps: bool = False
    ) -> Optional[Dict]:
        """
        加载翻译结果数据
        
        Args:
            pdf_name: PDF文件名
            use_dps: 是否使用DPS模式的翻译结果
            
        Returns:
            翻译数据字典，如果不存在返回None
        """
        paths = self.get_pdf_paths(pdf_name)
        
        translation_path = (
            paths["translation_dps_json"] if use_dps
            else paths["translation_json"]
        )
        
        if not translation_path or not translation_path.exists():
            logger.warning(f"翻译结果文件不存在: {translation_path}")
            return None
        
        try:
            with open(translation_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载翻译结果失败: {str(e)}")
            return None
    
    def load_parsed_data(self, pdf_name: str) -> Optional[Dict]:
        """
        加载解析结果数据
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            解析数据字典，如果不存在返回None
        """
        paths = self.get_pdf_paths(pdf_name)
        parsed_path = paths["parsed_json"]
        
        if not parsed_path or not parsed_path.exists():
            logger.warning(f"解析结果文件不存在: {parsed_path}")
            return None
        
        try:
            with open(parsed_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载解析结果失败: {str(e)}")
            return None
    
    def get_export_filename(
        self,
        pdf_name: str,
        mode: str,
        target_lang: str = "zh-CN"
    ) -> str:
        """
        生成导出文件名
        
        Args:
            pdf_name: 源PDF文件名
            mode: 导出模式
            target_lang: 目标语言
            
        Returns:
            导出文件名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lang_suffix = target_lang.replace("-", "")
        
        mode_suffix = {
            "overlay": "translated",
            "side_by_side": "bilingual_lr",
            "interleaved": "bilingual_alt",
            "translation_only": "translation"
        }.get(mode, "export")
        
        return f"{pdf_name}_{mode_suffix}_{lang_suffix}_{timestamp}.pdf"
    
    def export_pdf(
        self,
        pdf_name: str,
        mode: str = "overlay",
        use_dps: bool = False,
        output_filename: Optional[str] = None
    ) -> Dict:
        """
        导出翻译后的PDF文件
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            mode: 导出模式
                - "overlay": 覆盖模式（在原PDF上叠加译文）
                - "side_by_side": 左右对照
                - "interleaved": 交替排列
                - "translation_only": 纯译文
            use_dps: 是否使用DPS模式的翻译结果
            output_filename: 自定义输出文件名
            
        Returns:
            导出结果
        """
        logger.info(f"开始导出PDF: pdf_name={pdf_name}, mode={mode}, use_dps={use_dps}")
        
        # 验证导出模式
        if mode not in self.EXPORT_MODES:
            return {
                "success": False,
                "error": f"不支持的导出模式: {mode}",
                "available_modes": list(self.EXPORT_MODES.keys())
            }
        
        # 获取文件路径
        paths = self.get_pdf_paths(pdf_name)
        
        # 检查源PDF文件
        source_pdf = paths["source_pdf"]
        if not source_pdf or not source_pdf.exists():
            return {
                "success": False,
                "error": f"源PDF文件不存在: {pdf_name}"
            }
        
        # 加载翻译数据
        translation_data = self.load_translation_data(pdf_name, use_dps)
        if not translation_data:
            return {
                "success": False,
                "error": "翻译结果不存在，请先完成翻译"
            }
        
        # 检查翻译任务
        tasks = translation_data.get("translation_tasks", [])
        success_tasks = [t for t in tasks if t.get("translation_status") == "success"]
        
        if not success_tasks:
            return {
                "success": False,
                "error": "没有成功的翻译任务"
            }
        
        # 生成输出文件名
        if not output_filename:
            target_lang = translation_data.get("target_lang", "zh-CN")
            output_filename = self.get_export_filename(pdf_name, mode, target_lang)
        
        output_path = self.output_dir / output_filename
        
        # 检查字体状态
        font_status = self.font_manager.check_fonts_available()
        if not any(font_status.values()):
            return {
                "success": False,
                "error": "没有可用的字体文件，请将字体文件放入fonts目录",
                "font_status": font_status,
                "fonts_dir": str(self.font_manager.get_fonts_dir())
            }
        
        # 根据模式执行导出
        try:
            if mode == "overlay":
                result = self.pdf_generator.create_translated_pdf(
                    str(source_pdf),
                    str(output_path),
                    translation_data
                )
            elif mode == "side_by_side":
                result = self.pdf_generator.create_bilingual_pdf(
                    str(source_pdf),
                    str(output_path),
                    translation_data,
                    layout="side_by_side"
                )
            elif mode == "interleaved":
                result = self.pdf_generator.create_bilingual_pdf(
                    str(source_pdf),
                    str(output_path),
                    translation_data,
                    layout="interleaved"
                )
            elif mode == "translation_only":
                result = self._create_translation_only_pdf(
                    str(source_pdf),
                    str(output_path),
                    translation_data
                )
            else:
                result = {
                    "success": False,
                    "error": f"模式 {mode} 尚未实现"
                }
            
            if result.get("success"):
                result["pdf_name"] = pdf_name
                result["filename"] = output_filename
                result["output_path"] = str(output_path)
                result["download_url"] = f"/api/v1/export/download/{output_filename}"
                result["mode"] = mode
                result["use_dps"] = use_dps
                result["translation_stats"] = {
                    "total_tasks": len(tasks),
                    "success_tasks": len(success_tasks),
                    "source_lang": translation_data.get("source_lang"),
                    "target_lang": translation_data.get("target_lang")
                }
            
            return result
            
        except Exception as e:
            logger.error(f"导出PDF失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_translation_only_pdf(
        self,
        source_pdf_path: str,
        output_path: str,
        translation_data: Dict
    ) -> Dict:
        """
        创建纯译文PDF（只包含翻译内容，不包含原文）
        
        Args:
            source_pdf_path: 源PDF路径（用于获取页面尺寸）
            output_path: 输出路径
            translation_data: 翻译数据
            
        Returns:
            生成结果
        """
        import fitz
        
        try:
            # 打开源PDF获取页面尺寸
            source_doc = fitz.open(source_pdf_path)
            new_doc = fitz.open()
            
            translation_tasks = translation_data.get("translation_tasks", [])
            tasks_by_page = self.pdf_generator._group_tasks_by_page(translation_tasks)
            
            # 自动注册字体
            self.font_manager.auto_register_fonts()
            
            for page_num in range(len(source_doc)):
                source_page = source_doc[page_num]
                source_rect = source_page.rect
                
                # 创建新的空白页面
                new_page = new_doc.new_page(
                    width=source_rect.width,
                    height=source_rect.height
                )
                
                # 填充白色背景
                shape = new_page.new_shape()
                shape.draw_rect(source_rect)
                shape.finish(color=None, fill=(1, 1, 1))
                shape.commit()
                
                # 绘制译文
                page_tasks = tasks_by_page.get(page_num, [])
                for task in page_tasks:
                    self.pdf_generator._render_task_to_page(new_page, task)
            
            # 保存
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            new_doc.save(output_path)
            
            source_doc.close()
            new_doc.close()
            
            logger.info(f"✅ 纯译文PDF生成完成: {output_path}")
            
            return {
                "success": True,
                "output_path": output_path,
                "mode": "translation_only",
                "pages": len(source_doc)
            }
            
        except Exception as e:
            logger.error(f"创建纯译文PDF失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_export_status(self, pdf_name: str) -> Dict:
        """
        获取PDF的导出状态
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            状态信息
        """
        paths = self.get_pdf_paths(pdf_name)
        
        # 检查各种文件是否存在
        source_exists = paths["source_pdf"] and paths["source_pdf"].exists()
        translation_exists = (
            paths["translation_json"] and paths["translation_json"].exists()
        )
        translation_dps_exists = (
            paths["translation_dps_json"] and paths["translation_dps_json"].exists()
        )
        
        # 查找已导出的文件
        exported_files = list(self.output_dir.glob(f"{pdf_name}_*.pdf"))
        
        # 检查字体状态
        font_status = self.font_manager.check_fonts_available()
        
        return {
            "pdf_name": pdf_name,
            "source_pdf_exists": source_exists,
            "translation_exists": {
                "python": translation_exists,
                "dps": translation_dps_exists
            },
            "can_export": source_exists and (translation_exists or translation_dps_exists),
            "exported_files": [
                {
                    "filename": f.name,
                    "path": str(f),
                    "size": f.stat().st_size,
                    "created": datetime.fromtimestamp(f.stat().st_ctime).isoformat()
                }
                for f in exported_files
            ],
            "font_status": font_status,
            "fonts_ready": any(font_status.values()),
            "available_modes": list(self.EXPORT_MODES.keys())
        }
    
    def list_exports(self, pdf_name: Optional[str] = None) -> List[Dict]:
        """
        列出已导出的PDF文件
        
        Args:
            pdf_name: PDF文件名（可选，不指定则列出全部）
            
        Returns:
            已导出文件列表
        """
        if pdf_name:
            pattern = f"{pdf_name}_*.pdf"
        else:
            pattern = "*.pdf"
        
        exports = []
        for file in self.output_dir.glob(pattern):
            try:
                stat = file.stat()
                exports.append({
                    "filename": file.name,
                    "path": str(file),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"获取文件信息失败: {file} | {str(e)}")
        
        # 按创建时间降序排序
        exports.sort(key=lambda x: x["created"], reverse=True)
        
        return exports
    
    def delete_export(self, filename: str) -> Dict:
        """
        删除已导出的PDF文件
        
        Args:
            filename: 文件名
            
        Returns:
            删除结果
        """
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"文件不存在: {filename}"
            }
        
        try:
            file_path.unlink()
            logger.info(f"删除导出文件: {filename}")
            return {
                "success": True,
                "deleted_file": filename
            }
        except Exception as e:
            logger.error(f"删除文件失败: {filename} | {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_font_info(self) -> Dict:
        """
        获取字体信息
        
        Returns:
            字体状态信息
        """
        return self.font_manager.get_font_info()


# ==================== 便捷函数 ====================

def export_translated_pdf(
    pdf_name: str,
    mode: str = "overlay",
    use_dps: bool = False
) -> Dict:
    """
    导出翻译后的PDF（便捷函数）
    
    Args:
        pdf_name: PDF文件名
        mode: 导出模式
        use_dps: 是否使用DPS模式
        
    Returns:
        导出结果
    """
    service = PDFExportService()
    return service.export_pdf(pdf_name, mode, use_dps)
