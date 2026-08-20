from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger
import os
import uuid
from pathlib import Path
import aiofiles
import json
import time
import asyncio
from typing import Optional

from app.core.config import settings
from app.services.pdf_parser import PDFParser
from app.services.dps_service import DPSService
from app.services.annotation.annotation_service import AnnotationService
from app.services.heading_hierarchy_service import HeadingHierarchyService
from app.services.pdf_id_mapper import get_pdf_id_mapper
from app.services.document_parser.layout_service import analyze_with_provider
from app.services.document_parser.layout_paths import LOCAL_PROVIDER, is_external_provider
from app.services.document_parser.providers import get_provider

router = APIRouter()

# 初始化PDF解析器
pdf_parser = PDFParser()
dps_service = DPSService()
annotation_service = AnnotationService()
heading_service = HeadingHierarchyService()

# 全局进度存储（实际项目中应使用Redis等缓存）
progress_store = {}

async def send_progress(task_id: str, progress: int, stage: str, message: str):
    """发送进度更新"""
    progress_store[task_id] = {
        "progress": progress,
        "stage": stage,
        "message": message,
        "timestamp": time.time()
    }
    logger.info(f"[进度] {task_id[:8]} | {progress}% | {stage} | {message}")

@router.get("/upload/progress/{task_id}")
async def get_upload_progress(task_id: str):
    """SSE进度推送接口"""
    async def event_generator():
        try:
            # 不设置超时限制，等待后端处理完成
            # 如果需要超时保护，可以设置为30分钟或更长
            start_time = time.time()
            max_wait_time = 1800  # 30分钟，给极长的PDF留出充裕的时间
            
            last_progress = -1
            while True:
                # 检查极端超时情况（30分钟）
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    logger.warning(f"[进度推送] 超过30分钟，结束推送: {task_id[:8]}")
                    yield f"data: {json.dumps({'progress': 0, 'stage': 'error', 'message': '处理超时30分钟，请检查后端日志'}, ensure_ascii=False)}\n\n"
                    break
                
                # 获取当前进度
                if task_id in progress_store:
                    current = progress_store[task_id]
                    current_progress = current.get("progress", 0)
                    
                    # 只在进度变化时发送
                    if current_progress != last_progress:
                        yield f"data: {json.dumps(current, ensure_ascii=False)}\n\n"
                        last_progress = current_progress
                        
                        # 如果完成或出错，结束推送
                        if current_progress >= 100 or current.get("stage") == "error":
                            # 清理进度数据
                            if task_id in progress_store:
                                del progress_store[task_id]
                            break
                
                # 每500ms检查一次
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"[进度推送] 异常: {task_id[:8]} | {str(e)}")
            yield f"data: {json.dumps({'progress': 0, 'stage': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )

# 初始化PDF解析器
pdf_parser = PDFParser()
dps_service = DPSService()
annotation_service = AnnotationService()
heading_service = HeadingHierarchyService()


def _find_uploaded_pdf_path(pdf_name: str) -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    pdf_files = list(upload_dir.glob(f"*{pdf_name}.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"未找到已上传PDF文件: {pdf_name} dir={upload_dir}")
    return pdf_files[0]


def _attach_dps_meta_to_parsed_json(parsed_json_path: Path, dps_result: dict, provider: str = LOCAL_PROVIDER) -> None:
    if not parsed_json_path.exists():
        raise FileNotFoundError(f"解析JSON不存在，无法写入版面分析元数据: {parsed_json_path}")

    with open(parsed_json_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    # 记录当前生效的版面分析服务（下游读取版面结果时据此定位文件）
    parsed_data["layout_provider"] = provider

    parsed_data["dps"] = {
        "success": bool(dps_result.get("success")),
        "already_exists": bool(dps_result.get("already_exists")),
        "dps_json_path": dps_result.get("dps_json_path"),
        "req_id": dps_result.get("req_id"),
        "elapsed_sec": dps_result.get("elapsed_sec"),
        "pages": dps_result.get("pages"),
        "with_ocr": dps_result.get("with_ocr"),
        "ocr_min_conf": dps_result.get("ocr_min_conf"),
        "ocr_return_regions": dps_result.get("ocr_return_regions"),
        "base_url": settings.DPS_SERVICE_URL,
        "provider": provider,
        "provider_name": dps_result.get("provider_name"),
    }

    with open(parsed_json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    with_ocr: bool = False,
    parser: str = Query(LOCAL_PROVIDER, description="版面分析服务ID（dps=本地DPS，其余为外部服务）"),
    task_id: Optional[str] = Query(None),
):
    """
    上传PDF文件并进行行级解析
    如果文件已经解析过，则返回已存在的解析结果
    支持进度推送：task_id参数用于SSE进度推送
    parser参数：选择版面分析服务（默认本地DPS）
    """
    t_total_start = time.time()
    pdf_name = ""  # 初始化变量
    
    # 如果没有提供task_id，生成一个
    if not task_id:
        task_id = str(uuid.uuid4())
    
    # 解析服务名称（用于进度文案）
    parser = parser or LOCAL_PROVIDER
    use_external = is_external_provider(parser)
    provider_meta = get_provider(parser) if use_external else None
    parser_display_name = provider_meta["name"] if provider_meta else "本地DPS"
    
    try:
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        # 获取不带扩展名的文件名
        pdf_name = Path(file.filename).stem
        logger.info(f"[上传] 开始处理: {pdf_name} | OCR={with_ocr} | 解析服务={parser_display_name} | TaskID={task_id[:8]}")
        
        await send_progress(task_id, 5, "checking", "检查文件是否已存在")
        
        # 【优化】使用短ID获取parsed目录
        mapper = get_pdf_id_mapper()
        pdf_id = mapper.get_or_create_id(pdf_name)
        parsed_dir = Path("storage/parsed") / pdf_id
        json_path = parsed_dir / "parsed.json"
        # 所选服务的版面结果文件（本地DPS=dps.json，外部服务={provider}.json）
        layout_json_path = parsed_dir / "dps.json" if not use_external else parsed_dir / f"{parser}.json"
        
        if json_path.exists():
            # 已存在解析结果，读取并返回
            t_exists_start = time.time()
            logger.info(f"[上传] PDF已存在: {pdf_name}")
            await send_progress(task_id, 10, "exists", "PDF已存在，读取缓存")
            
            with open(json_path, "r", encoding="utf-8") as f:
                parsed_data = json.load(f)

            # 版面结果缺失时补齐（外部服务自带文本识别，with_ocr不影响；本地DPS开OCR时也需补齐校验）
            if (not layout_json_path.exists()) or (with_ocr and not use_external):
                t_dps_start = time.time()
                await send_progress(task_id, 30, "dps", f"补齐{parser_display_name}版面分析")
                existing_pdf_path = _find_uploaded_pdf_path(pdf_name)
                dps_result = await analyze_with_provider(
                    pdf_path=str(existing_pdf_path),
                    pdf_name=pdf_name,
                    provider_id=parser,
                    with_ocr=with_ocr,
                    force=False,
                )
                _attach_dps_meta_to_parsed_json(json_path, dps_result, provider=parser)
                logger.info(f"[上传] 版面分析补齐完成: {time.time() - t_dps_start:.2f}s")
                await send_progress(task_id, 70, "dps", f"{parser_display_name}解析完成")
            elif parsed_data.get("layout_provider") != parser:
                # 版面结果已存在但来源服务不同：切换当前生效的版面分析服务
                parsed_data["layout_provider"] = parser
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)
                logger.info(f"[上传] 切换版面分析服务: {pdf_name} -> {parser_display_name}")

            try:
                t_anno_start = time.time()
                await send_progress(task_id, 80, "annotation", "预标注处理中")
                pre = annotation_service.preannotate_from_dps(pdf_name)
                hs = heading_service.analyze_and_apply(pdf_name)
                
                # 阅读顺序已在预标注时直接从DPS写入，无需额外同步
                logger.info(f"[上传] 预标注+层级分析完成: {time.time() - t_anno_start:.2f}s")
                await send_progress(task_id, 95, "annotation", "预标注完成")
            except Exception as e:
                logger.error(f"[上传] 预标注异常: {pdf_name} | {str(e)}")
            
            t_total = time.time() - t_total_start
            logger.info(f"✅ [上传] 成功(已存在): {pdf_name} | 总耗时: {t_total:.2f}s")
            await send_progress(task_id, 100, "completed", "处理完成")
                    
            # 给SSE一点时间推送最后的进度
            await asyncio.sleep(0.1)
            
            return {
                "code": 200,
                "message": "PDF已存在，无需重复解析",
                "data": {
                    "task_id": task_id,
                    "file_id": "",  # 已存在的文件没有新的file_id
                    "filename": file.filename,
                    "pdf_name": pdf_name,
                    "total_pages": parsed_data.get("total_pages", 0),
                    "output_dir": str(parsed_dir),
                    "json_path": str(json_path),
                    "dps_json_path": str(layout_json_path) if layout_json_path.exists() else None,
                    "layout_provider": parser,
                    "with_ocr": with_ocr,
                    "already_exists": True  # 标记为已存在
                }
            }
        
        # 生成唯一文件ID
        file_id = str(uuid.uuid4())
        
        # 创建上传目录
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        file_path = upload_dir / f"{file_id}_{file.filename}"
        
        t_save_start = time.time()
        await send_progress(task_id, 15, "uploading", "正在保存文件")
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        logger.info(f"[上传] 文件保存完成: {time.time() - t_save_start:.2f}s")
        await send_progress(task_id, 20, "uploaded", "文件上传完成")
        
        # 进行PDF行级解析
        t_parse_start = time.time()
        await send_progress(task_id, 25, "parsing", "PyMuPDF解析中")
        parse_result = pdf_parser.parse_pdf(
            pdf_path=str(file_path),
            pdf_name=pdf_name
        )
        logger.info(f"[上传] PyMuPDF解析完成: {time.time() - t_parse_start:.2f}s | 页数: {parse_result.get('total_pages', 0)}")
        await send_progress(task_id, 45, "parsing", f"PDF解析完成 ({parse_result.get('total_pages', 0)}页)")
        
        if not parse_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"PDF解析失败: {parse_result.get('error')}"
            )

        t_dps_start = time.time()
        await send_progress(task_id, 50, "dps", f"{parser_display_name}版面分析中")
        dps_result = await analyze_with_provider(
            pdf_path=str(file_path),
            pdf_name=pdf_name,
            provider_id=parser,
            with_ocr=with_ocr,
            force=False,
        )
        logger.info(f"[上传] 版面分析完成({parser_display_name}): {time.time() - t_dps_start:.2f}s")
        await send_progress(task_id, 75, "dps", f"{parser_display_name}分析完成")
        
        _attach_dps_meta_to_parsed_json(Path(parse_result["json_path"]), dps_result, provider=parser)
        
        try:
            t_anno_start = time.time()
            await send_progress(task_id, 80, "annotation", "预标注处理中")
            pre = annotation_service.preannotate_from_dps(pdf_name)
            hs = heading_service.analyze_and_apply(pdf_name)
            
            # 阅读顺序已在预标注时直接从DPS写入，无需额外同步
            logger.info(f"[上传] 预标注+层级分析完成: {time.time() - t_anno_start:.2f}s")
            await send_progress(task_id, 95, "annotation", "预标注完成")
        except Exception as e:
            logger.error(f"[上传] 预标注异常: {pdf_name} | {str(e)}")
        
        t_total = time.time() - t_total_start
        logger.info(f"✅ [上传] 成功(新解析): {pdf_name} | 总耗时: {t_total:.2f}s")
        await send_progress(task_id, 100, "completed", "处理完成")
        
        # 给SSE一点时间推送最后的进度
        await asyncio.sleep(0.1)
        
        return {
            "code": 200,
            "message": "上传并解析成功",
            "data": {
                "task_id": task_id,
                "file_id": file_id,
                "filename": file.filename,
                "pdf_name": pdf_name,
                "total_pages": parse_result["total_pages"],
                "output_dir": parse_result["output_dir"],
                "json_path": parse_result["json_path"],
                "dps_json_path": dps_result.get("dps_json_path"),
                "dps_req_id": dps_result.get("req_id"),
                "dps_elapsed_sec": dps_result.get("elapsed_sec"),
                "layout_provider": parser,
                "with_ocr": with_ocr,
                "already_exists": False  # 标记为新解析
            }
        }
        
    except HTTPException:
        await send_progress(task_id, 0, "error", "处理失败")
        raise
    except Exception as e:
        t_total = time.time() - t_total_start
        logger.error(f"❌ [上传] 失败: {pdf_name if 'pdf_name' in locals() else file.filename} | 耗时: {t_total:.2f}s | 错误: {str(e)}")
        await send_progress(task_id, 0, "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))
