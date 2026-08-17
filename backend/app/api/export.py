"""
PDF导出API接口
提供PDF导出相关的HTTP接口
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from loguru import logger

from app.services.pdf_export import PDFExportService

router = APIRouter()


class ExportRequest(BaseModel):
    """导出请求模型"""
    mode: str = Field(
        default="overlay",
        description="导出模式: overlay(覆盖), side_by_side(左右对照), interleaved(交替), translation_only(纯译文)"
    )
    use_dps: bool = Field(
        default=False,
        description="是否使用DPS模式的翻译结果"
    )
    output_filename: Optional[str] = Field(
        default=None,
        description="自定义输出文件名"
    )


@router.post("/export/{pdf_name}")
async def export_pdf(
    pdf_name: str,
    request: ExportRequest
):
    """
    导出翻译后的PDF文件
    
    Args:
        pdf_name: PDF文件名（不含扩展名）
        request: 导出请求参数
        
    Returns:
        导出结果
    """
    try:
        logger.info(f"PDF导出请求: pdf_name={pdf_name}, mode={request.mode}, use_dps={request.use_dps}")
        
        service = PDFExportService()
        result = service.export_pdf(
            pdf_name=pdf_name,
            mode=request.mode,
            use_dps=request.use_dps,
            output_filename=request.output_filename
        )
        
        if result.get("success"):
            return {
                "code": 200,
                "message": "导出成功",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "导出失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF导出失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"导出失败: {str(e)}"
        )


@router.get("/export/{pdf_name}/status")
async def get_export_status(pdf_name: str):
    """
    获取PDF的导出状态
    
    Args:
        pdf_name: PDF文件名
        
    Returns:
        导出状态信息
    """
    try:
        service = PDFExportService()
        status = service.get_export_status(pdf_name)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"获取导出状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取状态失败: {str(e)}"
        )


@router.get("/export/list")
async def list_exports(
    pdf_name: Optional[str] = Query(None, description="筛选特定PDF的导出文件")
):
    """
    列出已导出的PDF文件
    
    Args:
        pdf_name: 可选，筛选特定PDF的导出文件
        
    Returns:
        已导出文件列表
    """
    try:
        service = PDFExportService()
        exports = service.list_exports(pdf_name)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "total": len(exports),
                "exports": exports
            }
        }
        
    except Exception as e:
        logger.error(f"获取导出列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取列表失败: {str(e)}"
        )


@router.get("/export/download/{filename}")
async def download_export(filename: str):
    """
    下载已导出的PDF文件
    
    Args:
        filename: 文件名
        
    Returns:
        PDF文件流
    """
    try:
        service = PDFExportService()
        file_path = service.output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {filename}"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"下载失败: {str(e)}"
        )


@router.delete("/export/{filename}")
async def delete_export(filename: str):
    """
    删除已导出的PDF文件
    
    Args:
        filename: 文件名
        
    Returns:
        删除结果
    """
    try:
        service = PDFExportService()
        result = service.delete_export(filename)
        
        if result.get("success"):
            return {
                "code": 200,
                "message": "删除成功",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "删除失败")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


@router.get("/export/fonts/status")
async def get_font_status():
    """
    获取字体状态信息
    
    Returns:
        字体状态
    """
    try:
        service = PDFExportService()
        font_info = service.get_font_info()
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": font_info
        }
        
    except Exception as e:
        logger.error(f"获取字体状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取状态失败: {str(e)}"
        )


@router.get("/export/modes")
async def get_export_modes():
    """
    获取支持的导出模式
    
    Returns:
        导出模式列表
    """
    return {
        "code": 200,
        "message": "获取成功",
        "data": {
            "modes": PDFExportService.EXPORT_MODES
        }
    }
