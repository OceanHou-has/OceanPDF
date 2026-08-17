"""
PDF ID 映射服务
解决长文件名导致的路径过长问题

设计思路：
1. 为每个PDF生成一个短ID（8位随机字符串）
2. 使用短ID作为存储目录名：storage/parsed/{pdf_id}/
3. 维护一个映射文件：storage/pdf_mappings.json
4. 映射文件记录：pdf_id <-> pdf_name 的双向映射
"""
import json
import random
import string
from pathlib import Path
from typing import Optional, Dict
from loguru import logger


class PDFIDMapper:
    """PDF ID映射管理器"""
    
    def __init__(self, mapping_file: str = "storage/pdf_mappings.json"):
        """
        初始化映射管理器
        
        Args:
            mapping_file: 映射文件路径
        """
        self.mapping_file = Path(mapping_file)
        self.mappings: Dict = self._load_mappings()
    
    def _load_mappings(self) -> Dict:
        """加载映射文件"""
        if not self.mapping_file.exists():
            # 创建空映射文件
            self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
            initial_data = {
                "id_to_name": {},  # pdf_id -> pdf_name
                "name_to_id": {}   # pdf_name -> pdf_id
            }
            self._save_mappings(initial_data)
            return initial_data
        
        try:
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载映射文件失败: {str(e)}")
            return {"id_to_name": {}, "name_to_id": {}}
    
    def _save_mappings(self, data: Optional[Dict] = None) -> bool:
        """保存映射文件"""
        if data is None:
            data = self.mappings
        
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存映射文件失败: {str(e)}")
            return False
    
    def _generate_id(self, length: int = 8) -> str:
        """
        生成随机ID
        
        Args:
            length: ID长度（默认8位）
            
        Returns:
            随机字符串ID
        """
        chars = string.ascii_lowercase + string.digits
        while True:
            pdf_id = ''.join(random.choices(chars, k=length))
            # 确保ID不重复
            if pdf_id not in self.mappings["id_to_name"]:
                return pdf_id
    
    def get_or_create_id(self, pdf_name: str) -> str:
        """
        获取或创建PDF的短ID
        
        Args:
            pdf_name: PDF文件名（不含扩展名）
            
        Returns:
            8位短ID
        """
        # 如果已存在映射，直接返回
        if pdf_name in self.mappings["name_to_id"]:
            pdf_id = self.mappings["name_to_id"][pdf_name]
            logger.debug(f"找到已有映射: {pdf_name} -> {pdf_id}")
            return pdf_id
        
        # 生成新ID
        pdf_id = self._generate_id()
        
        # 添加双向映射
        self.mappings["id_to_name"][pdf_id] = pdf_name
        self.mappings["name_to_id"][pdf_name] = pdf_id
        
        # 保存映射
        self._save_mappings()
        
        logger.info(f"创建新映射: {pdf_name} -> {pdf_id}")
        return pdf_id
    
    def get_name_by_id(self, pdf_id: str) -> Optional[str]:
        """
        通过ID获取PDF名称
        
        Args:
            pdf_id: PDF短ID
            
        Returns:
            PDF文件名，不存在返回None
        """
        return self.mappings["id_to_name"].get(pdf_id)
    
    def get_id_by_name(self, pdf_name: str) -> Optional[str]:
        """
        通过名称获取PDF ID
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            PDF短ID，不存在返回None
        """
        return self.mappings["name_to_id"].get(pdf_name)
    
    def delete_mapping(self, pdf_name: str) -> bool:
        """
        删除PDF映射
        
        Args:
            pdf_name: PDF文件名
            
        Returns:
            是否删除成功
        """
        pdf_id = self.mappings["name_to_id"].get(pdf_name)
        if not pdf_id:
            logger.warning(f"映射不存在，无法删除: {pdf_name}")
            return False
        
        # 删除双向映射
        del self.mappings["name_to_id"][pdf_name]
        del self.mappings["id_to_name"][pdf_id]
        
        # 保存映射
        self._save_mappings()
        
        logger.info(f"删除映射: {pdf_name} <-> {pdf_id}")
        return True
    
    def list_all(self) -> Dict[str, str]:
        """
        列出所有映射
        
        Returns:
            name_to_id映射字典
        """
        return self.mappings["name_to_id"].copy()
    
    def migrate_existing_pdfs(self, parsed_base_dir: str = "storage/parsed") -> Dict:
        """
        迁移现有PDF（从长文件名目录迁移到短ID目录）
        
        Args:
            parsed_base_dir: 解析结果基础目录
            
        Returns:
            迁移统计信息
        """
        import shutil
        
        parsed_dir = Path(parsed_base_dir)
        if not parsed_dir.exists():
            logger.warning(f"解析目录不存在: {parsed_dir}")
            return {"migrated": 0, "skipped": 0, "failed": 0}
        
        stats = {"migrated": 0, "skipped": 0, "failed": 0}
        
        for pdf_folder in parsed_dir.iterdir():
            if not pdf_folder.is_dir():
                continue
            
            pdf_name = pdf_folder.name
            
            # 跳过已经是短ID格式的目录（8位字符）
            if len(pdf_name) == 8 and pdf_name.isalnum():
                logger.debug(f"跳过短ID目录: {pdf_name}")
                stats["skipped"] += 1
                continue
            
            try:
                # 获取或创建PDF ID
                pdf_id = self.get_or_create_id(pdf_name)
                
                # 新目录路径
                new_folder = parsed_dir / pdf_id
                
                # 如果新目录已存在，跳过
                if new_folder.exists():
                    logger.warning(f"目标目录已存在，跳过: {new_folder}")
                    stats["skipped"] += 1
                    continue
                
                # 重命名目录（迁移）
                pdf_folder.rename(new_folder)
                logger.info(f"迁移成功: {pdf_folder} -> {new_folder}")
                stats["migrated"] += 1
                
            except Exception as e:
                logger.error(f"迁移失败: {pdf_name} | {str(e)}")
                stats["failed"] += 1
        
        logger.info(f"迁移完成: 成功={stats['migrated']}, 跳过={stats['skipped']}, 失败={stats['failed']}")
        return stats


# 全局单例
_mapper_instance: Optional[PDFIDMapper] = None

def get_pdf_id_mapper() -> PDFIDMapper:
    """获取全局PDF ID映射器实例"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = PDFIDMapper()
    return _mapper_instance

