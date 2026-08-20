"""
PDF 工具 API 接口
提供合并、拆分、提取、删除、旋转、重排等页面级工具。
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from loguru import logger

from app.services.pdf_tools import PDFToolsService

router = APIRouter()


def _wrap(outputs: List[str]) -> dict:
    """统一封装处理结果。"""
    return {
        "code": 200,
        "message": "处理成功",
        "data": {
            "outputs": [
                {
                    "filename": o,
                    "download_url": f"/api/v1/tools/download/{o}",
                }
                for o in outputs
            ]
        },
    }


@router.post("/tools/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    """合并多个 PDF 为一个文件。"""
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="请至少选择 2 个 PDF 文件")
        items = [(f.filename or "document.pdf", await f.read()) for f in files]
        outputs = PDFToolsService().merge(items)
        return _wrap(outputs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF工具] 合并失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"合并失败: {str(e)}")


@router.post("/tools/split")
async def split_pdf(
    file: UploadFile = File(...),
    mode: str = Form("ranges"),
    spec: Optional[str] = Form(None),
    every: Optional[int] = Form(None),
):
    """拆分 PDF。``mode``: ranges(按范围) / every(每 N 页)。"""
    try:
        data = await file.read()
        outputs = PDFToolsService().split(
            data, file.filename, mode=mode, spec=spec, every=every
        )
        return _wrap(outputs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF工具] 拆分失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"拆分失败: {str(e)}")


@router.post("/tools/extract")
async def extract_pages(
    file: UploadFile = File(...),
    spec: str = Form(...),
):
    """提取指定页面生成新 PDF。"""
    try:
        data = await file.read()
        outputs = PDFToolsService().extract(data, file.filename, spec)
        return _wrap(outputs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF工具] 提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.post("/tools/delete")
async def delete_pages(
    file: UploadFile = File(...),
    spec: str = Form(...),
):
    """删除指定页面。"""
    try:
        data = await file.read()
        outputs = PDFToolsService().delete_pages(data, file.filename, spec)
        return _wrap(outputs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF工具] 删除页面失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/tools/rotate")
async def rotate_pages(
    file: UploadFile = File(...),
    angle: int = Form(...),
    pages: Optional[str] = Form(None),
):
    """旋转页面。``pages`` 为空时旋转全部页面。"""
    try:
        data = await file.read()
        outputs = PDFToolsService().rotate(data, file.filename, angle, pages)
        return _wrap(outputs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF工具] 旋转失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"旋转失败: {str(e)}")


@router.post("/tools/reorder")
async def reorder_pages(
    file: UploadFile = File(...),
    spec: str = Form(...),
):
    """按新顺序重排页面。"""
    try:
        data = await file.read()
        outputs = PDFToolsService().reorder(data, file.filename, spec)
        return _wrap(outputs)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PDF工具] 重排失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重排失败: {str(e)}")


@router.get("/tools/download/{filename}")
async def download_tool_output(filename: str):
    """下载工具处理结果。"""
    service = PDFToolsService()
    file_path = service.output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    media_type = "application/zip" if filename.lower().endswith(".zip") else "application/pdf"
    return FileResponse(path=str(file_path), filename=filename, media_type=media_type)
