from fastapi import APIRouter, HTTPException
from pathlib import Path
import fitz  # PyMuPDF
from loguru import logger
import base64
from typing import List
import os
from datetime import datetime
import shutil

from app.services.pdf_id_mapper import get_pdf_id_mapper

router = APIRouter()

@router.get("/pdf/{pdf_name}/page/{page_num}")
async def get_pdf_page_image(pdf_name: str, page_num: int, render_scale: float = 3.0):
    """
    获取PDF指定页面的图片
    
    Args:
        pdf_name: PDF文件名（不含扩展名）
        page_num: 页码（从0开始）
        render_scale: 渲染缩放倍率（越大越清晰，越慢/越占内存）
    
    Returns:
        Base64编码的图片数据
    """
    try:
        try:
            scale = float(render_scale)
        except Exception:
            scale = 3.0
        scale = max(1.0, min(6.0, scale))

        # 查找PDF文件
        upload_dir = Path("storage/uploads")
        pdf_files = list(upload_dir.glob(f"*{pdf_name}.pdf"))
        
        if not pdf_files:
            raise HTTPException(status_code=404, detail=f"未找到PDF文件: {pdf_name}")
        
        pdf_path = pdf_files[0]
        
        # 打开PDF
        doc = fitz.open(pdf_path)
        
        if page_num < 0 or page_num >= len(doc):
            raise HTTPException(
                status_code=400, 
                detail=f"页码超出范围，总页数: {len(doc)}"
            )
        
        # 获取页面
        page = doc[page_num]
        
        mat = fitz.Matrix(scale, scale)
        
        # 渲染为图片
        pix = page.get_pixmap(matrix=mat)
        
        # 转换为PNG格式的字节数据
        img_bytes = pix.tobytes("png")
        
        # Base64编码
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        doc.close()
        logger.info(
            f"[get_pdf_page_image] pdf={pdf_name} page={page_num} render_scale={scale} pix={pix.width}x{pix.height}"
        )
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "page_num": page_num,
                "image": f"data:image/png;base64,{img_base64}",
                "width": pix.width,
                "height": pix.height
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PDF页面图片失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/{pdf_name}/parsed")
async def get_parsed_data(pdf_name: str):
    """
    获取PDF的解析数据
    
    Args:
        pdf_name: PDF文件名（不含扩展名）
    
    Returns:
        解析结果JSON数据
    """
    try:
        # 【优化】使用短ID获取parsed目录
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        parsed_dir = Path("storage/parsed") / pdf_id
        json_path = parsed_dir / "parsed.json"

        if not json_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"未找到解析结果: {pdf_name}"
            )

        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
        
        return {
            "code": 200,
            "message": "success",
            "data": parsed_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取解析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf/{pdf_name}/dps")
async def get_dps_data(pdf_name: str):
    """
    获取PDF的DPS版面分析+OCR结果
    """
    try:
        # 按 layout_provider 定位当前生效的版面结果文件（外部服务={provider_id}.json）
        from app.services.document_parser.layout_paths import get_layout_json_path
        json_path = get_layout_json_path(pdf_name)

        import json
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "code": 200,
            "message": "success",
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取DPS解析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parsed-list")
async def get_parsed_list():
    """
    获取所有已解析的PDF列表
    
    Returns:
        已解析PDF的列表，包含名称、页数、解析时间、OCR状态、翻译状态等
    """
    try:
        parsed_dir = Path("storage/parsed")

        if not parsed_dir.exists():
            return {
                "code": 200,
                "message": "success",
                "data": []
            }
        
        pdf_list = []

        for pdf_folder in parsed_dir.iterdir():
            if not pdf_folder.is_dir():
                continue
            
            pdf_name = pdf_folder.name
            
            # 【优化】跳过短ID目录，通过映射获取真实PDF名
            mapper = get_pdf_id_mapper()
            real_pdf_name = mapper.get_name_by_id(pdf_name)
            if not real_pdf_name:
                # 如果不在映射中，跳过（可能是旧数据）
                logger.debug(f"跳过未映射的目录: {pdf_name}")
                continue
            
            json_path = pdf_folder / "parsed.json"

            if not json_path.exists():
                continue

            import json
            with open(json_path, 'r', encoding='utf-8') as f:
                parsed_data = json.load(f)
            
            # 获取文件修改时间
            mtime = os.path.getmtime(json_path)
            parsed_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # 检查是否有OCR（判断当前生效的版面结果文件是否存在且包含OCR文本）
            layout_provider = parsed_data.get("layout_provider") or "dps"
            if layout_provider != "dps":
                dps_json_path = pdf_folder / f"{layout_provider}.json"
                if not dps_json_path.exists():
                    dps_json_path = pdf_folder / "dps.json"
            else:
                dps_json_path = pdf_folder / "dps.json"
            has_ocr = False
            if dps_json_path.exists():
                try:
                    with open(dps_json_path, 'r', encoding='utf-8') as f:
                        dps_data = json.load(f)
                    # 检查是否有OCR文本（查看raw.pages[0].boxes是否有ocr_text字段）
                    dps_raw = dps_data.get("raw", {})
                    dps_pages = dps_raw.get("pages", [])
                    if dps_pages:
                        first_page_boxes = dps_pages[0].get("boxes", [])
                        # 只要有任意一个box包含ocr_text就认为做过OCR
                        has_ocr = any(box.get("ocr_text") for box in first_page_boxes)
                except Exception as e:
                    logger.warning(f"读取DPS文件失败 {real_pdf_name}: {str(e)}")
                    has_ocr = False
            
            # 检查是否有翻译结果（判断是否存在 translation.json 或 translation_dps.json）
            translation_json_path = pdf_folder / "translation.json"
            translation_dps_json_path = pdf_folder / "translation_dps.json"
            has_translation = translation_json_path.exists() or translation_dps_json_path.exists()
            
            # 如果有翻译结果，检查翻译完成情况
            translation_progress = None
            if has_translation:
                # 优先检查 translation.json，其次检查 translation_dps.json
                active_translation_path = translation_json_path if translation_json_path.exists() else translation_dps_json_path
                try:
                    with open(active_translation_path, 'r', encoding='utf-8') as f:
                        translation_data = json.load(f)
                    
                    # 【修复】使用 translation_tasks 统计，而不是 pages.elements
                    translation_tasks = translation_data.get("translation_tasks", [])
                    total_tasks = len(translation_tasks)
                    completed_tasks = 0
                    
                    for task in translation_tasks:
                        status = task.get("translation_status")
                        # 只要有 translated_text 就认为完成（包括 success 和 failed）
                        if status in ("success", "failed") or task.get("translated_text"):
                            completed_tasks += 1
                    
                    if total_tasks > 0:
                        translation_progress = {
                            "completed": completed_tasks,
                            "total": total_tasks,
                            "percentage": round(completed_tasks / total_tasks * 100, 1)
                        }
                except Exception as e:
                    logger.warning(f"读取翻译进度失败 {real_pdf_name}: {str(e)}")
            
            pdf_list.append({
                "pdf_name": real_pdf_name,
                "total_pages": parsed_data.get("total_pages", 0),
                "parsed_time": parsed_time,
                "file_path": str(json_path),
                "has_ocr": has_ocr,
                "has_translation": has_translation,
                "translation_progress": translation_progress,
                # 版面分析服务来源（dps=本地，其余为外部服务ID）
                "layout_provider": layout_provider,
                # 【新增】明确的状态标识
                "translation_status": "completed" if (translation_progress and translation_progress["percentage"] >= 100) else ("in_progress" if has_translation else "none")
            })
        
        # 按解析时间降序排列
        pdf_list.sort(key=lambda x: x["parsed_time"], reverse=True)
        
        return {
            "code": 200,
            "message": "success",
            "data": pdf_list
        }
        
    except Exception as e:
        logger.error(f"获取已解析PDF列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/pdf/{pdf_name}")
async def delete_parsed_pdf(pdf_name: str):
    """
    删除已解析的PDF及其所有相关数据
    
    Args:
        pdf_name: PDF文件名（不含扩展名）
    
    Returns:
        删除结果
    """
    try:
        # 【优化】使用短ID删除parsed目录
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        parsed_dir = Path("storage/parsed") / pdf_id
        if parsed_dir.exists():
            shutil.rmtree(parsed_dir)
            logger.info(f"已删除解析结果: {parsed_dir}")
        
        # 删除原始PDF文件
        upload_dir = Path("storage/uploads")
        pdf_files = list(upload_dir.glob(f"*{pdf_name}.pdf"))
        for pdf_file in pdf_files:
            pdf_file.unlink()
            logger.info(f"已删除PDF文件: {pdf_file}")
        
        return {
            "code": 200,
            "message": "删除成功",
            "data": {
                "pdf_name": pdf_name,
                "deleted": True
            }
        }
        
    except Exception as e:
        logger.error(f"删除PDF失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
