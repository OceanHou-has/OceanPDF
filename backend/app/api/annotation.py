"""
PDF标注相关API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Union
from loguru import logger
from ..services.annotation.annotation_service import AnnotationService
from ..services.annotation.paper_analyzer import PaperAnalyzer

router = APIRouter()
annotation_service = AnnotationService()
paper_analyzer = PaperAnalyzer()


class AnnotationRequest(BaseModel):
    """标注请求模型"""
    pdf_name: str
    page_num: int
    block_id: Union[int, str]  # 支持int和str（合并元素的block_id是字符串）
    element_type: str


class ClearAnnotationRequest(BaseModel):
    """清除标注请求模型"""
    pdf_name: str
    page_num: int
    block_id: Union[int, str]  # 支持int和str


class SourceElement(BaseModel):
    """合并标注的源元素"""
    block_id: Union[int, str]  # 支持int和str
    bbox: List[float]
    text: str


class BatchAnnotationItem(BaseModel):
    """批量标注项"""
    page_num: int
    block_id: Optional[Union[int, str]] = None  # 普通标注时必填，支持int和str
    element_type: Optional[str] = None  # None表示清除标注
    is_merge: Optional[bool] = False  # 是否为合并标注
    source_elements: Optional[List[SourceElement]] = None  # 合并标注的源元素列表
    unmerge_from: Optional[str] = None  # 拆解操作：指向被拆解的合并元素block_id
    reading_order: Optional[int] = None  # 阅读顺序（手动排序时使用）


class BatchAnnotationRequest(BaseModel):
    """批量标注请求模型"""
    pdf_name: str
    annotations: List[BatchAnnotationItem]
    use_dps: Optional[bool] = False  # 是否对 dps.json 执行修改（True=DPS模式）


@router.get("/annotation/types")
async def get_annotation_types():
    """
    获取所有支持的标注类型及颜色配置
    
    Returns:
        标注类型列表和颜色映射
    """
    try:
        result = annotation_service.get_annotation_types()
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"获取标注类型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annotation/annotate")
async def annotate_element(request: AnnotationRequest):
    """
    标注PDF元素
    
    Args:
        request: 标注请求参数
        
    Returns:
        标注结果
    """
    try:
        result = annotation_service.annotate_element(
            pdf_name=request.pdf_name,
            page_num=request.page_num,
            block_id=request.block_id,
            element_type=request.element_type
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "code": 200,
            "message": "标注成功",
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标注元素失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annotation/clear")
async def clear_annotation(request: ClearAnnotationRequest):
    """
    清除元素标注
    
    Args:
        request: 清除标注请求参数
        
    Returns:
        清除结果
    """
    try:
        result = annotation_service.clear_annotation(
            pdf_name=request.pdf_name,
            page_num=request.page_num,
            block_id=request.block_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "code": 200,
            "message": "清除标注成功",
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除标注失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotation/{pdf_name}/page/{page_num}")
async def get_page_annotations(pdf_name: str, page_num: int):
    """
    获取指定页面的所有标注信息
    
    Args:
        pdf_name: PDF文件名
        page_num: 页码
        
    Returns:
        页面标注统计信息
    """
    try:
        result = annotation_service.get_page_annotations(
            pdf_name=pdf_name,
            page_num=page_num
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "code": 200,
            "message": "success",
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取页面标注失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annotation/batch")
async def batch_annotate(request: BatchAnnotationRequest):
    """
    批量标注PDF元素（优化性能）
    
    Args:
        request: 批量标注请求参数
        
    Returns:
        批量标注结果
    """
    try:
        # 转换为Pydantic模型列表
        annotations = []
        for item in request.annotations:
            annotation_dict = {
                "page_num": item.page_num,
            }
            
            # 如果有 unmerge_from 字段，这是拆解操作
            if item.unmerge_from:
                annotation_dict["block_id"] = item.block_id
                annotation_dict["element_type"] = item.element_type
                annotation_dict["_unmerge_from"] = item.unmerge_from  # 后端仍然使用 _unmerge_from
            elif item.is_merge and item.source_elements:
                # 合并标注
                annotation_dict["element_type"] = item.element_type
                annotation_dict["is_merge"] = True
                annotation_dict["source_elements"] = [
                    {
                        "block_id": elem.block_id,
                        "bbox": elem.bbox,
                        "text": elem.text
                    }
                    for elem in item.source_elements
                ]
            else:
                # 普通标注
                annotation_dict["block_id"] = item.block_id
                annotation_dict["element_type"] = item.element_type
            
            # 如果有 reading_order 字段，添加到请求中
            if item.reading_order is not None:
                annotation_dict["reading_order"] = item.reading_order
            
            annotations.append(annotation_dict)
        
        result = annotation_service.batch_annotate(
            pdf_name=request.pdf_name,
            annotations=annotations,
            use_dps=bool(request.use_dps)
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "code": 200,
            "message": f"批量标注成功，共处理 {len(request.annotations)} 项",
            "data": result["data"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量标注失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotation/{pdf_name}/metadata")
async def get_paper_metadata(pdf_name: str, force: bool = False):
    """
    获取PDF论文版面元数据（强段落宽度 + 栏数布局）
    
    Args:
        pdf_name: PDF文件名
        force: 是否强制重新分析
        
    Returns:
        论文版面元数据
    """
    try:
        # 如果强制分析，执行分析
        if force:
            analysis_result = paper_analyzer.analyze_paper(pdf_name, force=True)
            if not analysis_result.get("success"):
                raise HTTPException(status_code=400, detail=analysis_result.get("error"))
        
        # 加载元数据
        metadata = paper_analyzer.load_metadata(pdf_name)
        
        if not metadata:
            # 如果不存在，尝试分析
            analysis_result = paper_analyzer.analyze_paper(pdf_name, force=False)
            if not analysis_result.get("success"):
                raise HTTPException(status_code=404, detail="论文版面元数据不存在且分析失败")
            metadata = analysis_result.get("data")
        
        return {
            "code": 200,
            "message": "success",
            "data": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取论文版面元数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
