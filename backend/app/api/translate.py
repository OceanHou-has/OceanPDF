from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict
from loguru import logger
from pathlib import Path
import asyncio
import json
import time
import uuid
from collections import deque

from app.services.translation.pretranslation_service import PretranslationService
from app.services.translation.translation_task_service import TranslationTaskService
from app.services.translation.llm_service import create_translation_service
from app.services.translation.llm_providers import get_providers, get_provider

router = APIRouter()

translation_progress_store = {}
# 翻译任务控制标志存储：task_id -> {"paused": bool, "stopped": bool}
translation_control_flags = {}

MAX_SSE_EVENT_QUEUE_SIZE = 2000


def _mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return api_key[:2] + "***"
    return api_key[:4] + "***" + api_key[-4:]

class TranslateRequest(BaseModel):
    """翻译请求模型"""
    file_id: str
    source_lang: str = "en"
    target_lang: str = "zh"

class PrepareTranslationRequest(BaseModel):
    """准备翻译请求模型"""
    source_lang: str = "en"
    target_lang: str = "zh-CN"
    aggregate_titles: bool = False
    force: bool = False

@router.post("/translation/prepare/{pdf_name}")
async def prepare_translation(
    pdf_name: str,
    source_lang: str = Query("en", description="源语言代码"),
    target_lang: str = Query("zh-CN", description="目标语言代码"),
    aggregate_titles: bool = Query(False, description="是否聚合标题类元素"),
    use_dps: bool = Query(False, description="是否使用DPS/OCR结果（False=Python解析，True=DPS OCR）"),
    force: bool = Query(False, description="是否强制重新生成")
):
    """
    生成预翻译任务清单
    
    Args:
        pdf_name: PDF文件名（不含扩展名）
        source_lang: 源语言代码（默认"en"）
        target_lang: 目标语言代码（默认"zh-CN"）
        aggregate_titles: 是否聚合标题类元素（默认False）
        use_dps: 是否使用DPS/OCR结果（默认False，使用Python解析）
        force: 是否强制重新生成（默认False）
    
    Returns:
        预翻译任务统计信息
    """
    try:
        mode_name = "DPS" if use_dps else "Python"
        logger.info(
            f"准备翻译任务: pdf_name={pdf_name}, mode={mode_name}, source={source_lang}, "
            f"target={target_lang}, aggregate_titles={aggregate_titles}, force={force}"
        )
        
        # 创建预翻译服务
        pretrans_service = PretranslationService()
        
        # 生成预翻译任务
        result = pretrans_service.generate_pretranslation(
            pdf_name=pdf_name,
            source_lang=source_lang,
            target_lang=target_lang,
            aggregate_titles=aggregate_titles,
            use_dps=use_dps,
            force=force
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "生成预翻译任务失败")
            )
        
        return {
            "code": 200,
            "message": f"{mode_name}模式预翻译任务准备完成" if not result.get("skipped") else "预翻译文件已存在",
            "data": result.get("data"),
            "skipped": result.get("skipped", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"准备翻译任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/translation/pretranslation/{pdf_name}")
async def get_pretranslation(
    pdf_name: str,
    use_dps: bool = Query(False, description="是否使用DPS/OCR结果（False=Python解析，True=DPS OCR）"),
):
    """
    获取预翻译任务清单
    
    Args:
        pdf_name: PDF文件名
    
    Returns:
        预翻译任务清单
    """
    try:
        mode_name = "DPS" if use_dps else "Python"
        logger.info(f"获取预翻译任务: pdf_name={pdf_name}, mode={mode_name}")
        pretrans_service = PretranslationService()
        pretrans_path = pretrans_service.get_pretranslation_json_path(pdf_name, use_dps)
        logger.info(f"预翻译文件路径: {pretrans_path} exists={pretrans_path.exists()}")
        
        if not pretrans_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"{mode_name}模式预翻译文件不存在，请先调用prepare接口生成"
            )
        
        import json
        with open(pretrans_path, 'r', encoding='utf-8') as f:
            pretrans_data = json.load(f)
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": pretrans_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预翻译文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/translation/providers")
async def list_translation_providers():
    """
    获取支持的大模型厂商列表（含默认 base_url 与预置模型）
    """
    try:
        return {
            "code": 200,
            "message": "获取成功",
            "data": get_providers()
        }
    except Exception as e:
        logger.error(f"获取厂商列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translation/test")
async def test_llm_connection(
    api_key: str = Query(..., description="大模型 API Key"),
    provider: Optional[str] = Query(None, description="厂商ID（deepseek/qwen/doubao/google/openai/moonshot/zhipu/custom）"),
    base_url: Optional[str] = Query(None, description="OpenAI 兼容接口地址（缺省回退 DeepSeek）"),
    model: Optional[str] = Query(None, description="模型名称（缺省回退 DeepSeek 默认模型）")
):
    """
    测试大模型 API 连接（支持多厂商，优先使用轻量级 models.list 接口）

    Args:
        api_key: API Key
        provider: 厂商ID
        base_url: 接口地址
        model: 模型名称

    Returns:
        测试结果
    """
    try:
        service = create_translation_service(
            api_key=api_key,
            llm_config={"provider": provider, "base_url": base_url, "model": model}
        )
        result = service.test_connection()

        return {
            "code": 200 if result["success"] else 500,
            "message": result["message"],
            "data": result
        }
    except Exception as e:
        logger.error(f"测试连接失败: {str(e)}")
        return {
            "code": 500,
            "message": f"测试失败: {str(e)}",
            "data": {"success": False}
        }


@router.post("/translation/config/api-key")
async def save_api_key(api_key: str = Query(..., description="DeepSeek API Key")):
    """
    保存 API Key 到本地配置文件
    
    Args:
        api_key: DeepSeek API Key
        
    Returns:
        保存结果
    """
    try:
        config_dir = Path("storage/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "translation_config.json"
        
        # 读取现有配置或创建新配置
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # 更新 API Key（若传入的是脱敏占位值则保留已有密钥，避免覆盖丢失）
        if "***" not in api_key:
            config["deepseek_api_key"] = api_key
        elif not config.get("deepseek_api_key"):
            raise HTTPException(status_code=400, detail="请重新填写完整的 API Key")
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        masked_key = _mask_api_key(api_key)
        logger.info(f"API Key 已保存: {masked_key}")
        
        return {
            "code": 200,
            "message": "API Key 保存成功",
            "data": {
                "masked_key": masked_key
            }
        }
    except Exception as e:
        logger.error(f"保存 API Key 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translation/config/api-key")
async def get_api_key():
    """
    获取已保存的 API Key
    
    Returns:
        API Key（如果存在）
    """
    try:
        config_file = Path("storage/config/translation_config.json")
        
        if not config_file.exists():
            return {
                "code": 404,
                "message": "未找到保存的 API Key",
                "data": {
                    "api_key": "",
                    "masked_key": ""
                }
            }
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 优先读取新版模型配置中的 api_key，兼容旧版 deepseek_api_key
        model_config = config.get("model_config") or {}
        api_key = model_config.get("api_key") or config.get("deepseek_api_key", "")
        
        return {
            "code": 200,
            "message": "成功",
            "data": {
                "api_key": api_key,
                "masked_key": _mask_api_key(api_key)
            }
        }
    except Exception as e:
        logger.error(f"获取 API Key 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class TranslationModelConfig(BaseModel):
    """翻译模型配置（厂商 + 接口地址 + 模型 + API Key）"""
    provider: str = Field("deepseek", description="厂商ID")
    base_url: Optional[str] = Field("", description="OpenAI 兼容接口地址")
    model: Optional[str] = Field("", description="模型名称")
    api_key: Optional[str] = Field("", description="API Key")


def _read_translation_config_file() -> Dict:
    """读取本地翻译配置文件"""
    config_file = Path("storage/config/translation_config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _write_translation_config_file(config: Dict) -> None:
    """写入本地翻译配置文件"""
    config_dir = Path("storage/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "translation_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


@router.post("/translation/config/model-config")
async def save_model_config(model_config: TranslationModelConfig):
    """
    保存翻译模型配置（厂商 / base_url / 模型 / API Key）到本地
    """
    try:
        config = _read_translation_config_file()

        provider = model_config.provider or "deepseek"
        api_key = (model_config.api_key or "").strip()

        # 若传入的是脱敏占位值（含***），保留已保存的真实密钥（仅限同一厂商）
        if "***" in api_key:
            existing = config.get("model_config") or {}
            if existing.get("provider") == provider and existing.get("api_key") and "***" not in existing["api_key"]:
                api_key = existing["api_key"]
            else:
                api_key = ""

        saved = {
            "provider": provider,
            "base_url": (model_config.base_url or "").strip(),
            "model": (model_config.model or "").strip(),
            "api_key": api_key,
        }
        config["model_config"] = saved

        # 向后兼容：DeepSeek 厂商同步写入旧字段
        if saved["provider"] == "deepseek" and saved["api_key"]:
            config["deepseek_api_key"] = saved["api_key"]

        _write_translation_config_file(config)

        masked_key = _mask_api_key(saved["api_key"])
        logger.info(f"翻译模型配置已保存: provider={saved['provider']}, model={saved['model']}, key={masked_key}")

        return {
            "code": 200,
            "message": "翻译模型配置保存成功",
            "data": {
                "provider": saved["provider"],
                "base_url": saved["base_url"],
                "model": saved["model"],
                "masked_key": masked_key
            }
        }
    except Exception as e:
        logger.error(f"保存翻译模型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translation/config/model-config")
async def get_model_config():
    """
    获取已保存的翻译模型配置（不存在时回退旧版 DeepSeek 配置）
    """
    try:
        config = _read_translation_config_file()

        model_config = config.get("model_config")
        if not model_config:
            # 兼容旧版本：仅有 deepseek_api_key 的情况
            legacy_key = config.get("deepseek_api_key", "")
            provider_info = get_provider("deepseek") or {}
            model_config = {
                "provider": "deepseek",
                "base_url": provider_info.get("default_base_url", ""),
                "model": provider_info.get("default_model", ""),
                "api_key": legacy_key
            }

        # 修复历史脏数据：若密钥被脱敏占位值污染，清空并落盘，提示用户重新填写
        dirty = False
        if "***" in (model_config.get("api_key") or ""):
            model_config["api_key"] = ""
            config["model_config"] = model_config
            dirty = True
        if "***" in (config.get("deepseek_api_key") or ""):
            config["deepseek_api_key"] = ""
            dirty = True
        if dirty:
            _write_translation_config_file(config)
            logger.warning("检测到脱敏占位值污染翻译配置，已清空，请重新填写 API Key")

        return {
            "code": 200,
            "message": "成功",
            "data": {
                "provider": model_config.get("provider", "deepseek"),
                "base_url": model_config.get("base_url", ""),
                "model": model_config.get("model", ""),
                "api_key": model_config.get("api_key", ""),
                "masked_key": _mask_api_key(model_config.get("api_key", ""))
            }
        }
    except Exception as e:
        logger.error(f"获取翻译模型配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translation/config/max-concurrent")
async def save_max_concurrent(max_concurrent: int = Query(..., ge=1, le=20, description="最大并发数")):
    """
    保存最大并发数到本地配置文件
    """
    try:
        config_dir = Path("storage/config")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "translation_config.json"
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config["max_concurrent"] = max_concurrent
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"最大并发数已保存: {max_concurrent}")
        
        return {
            "code": 200,
            "message": "保存成功",
            "data": {"max_concurrent": max_concurrent}
        }
    except Exception as e:
        logger.error(f"保存最大并发数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translation/config/max-concurrent")
async def get_max_concurrent():
    """
    获取已保存的最大并发数
    """
    try:
        config_file = Path("storage/config/translation_config.json")
        
        if not config_file.exists():
            return {
                "code": 404,
                "message": "未找到保存的配置",
                "data": {"max_concurrent": 5}
            }
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        max_concurrent = config.get("max_concurrent", 5)
        
        return {
            "code": 200,
            "message": "成功",
            "data": {"max_concurrent": max_concurrent}
        }
    except Exception as e:
        logger.error(f"获取最大并发数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class TranslationRequest(BaseModel):
    """翻译请求模型"""
    pdf_name: str = Field(..., description="PDF文件名")
    api_key: str = Field(..., description="大模型 API Key")
    use_dps: bool = Field(False, description="是否使用DPS解析结果")
    max_concurrent: int = Field(5, ge=1, le=20, description="最大并发数（1-20）")
    enable_distribution: bool = Field(True, description="是否启用译文分配（针对组合块）")
    provider: Optional[str] = Field(None, description="大模型厂商ID（缺省 deepseek）")
    base_url: Optional[str] = Field(None, description="OpenAI 兼容接口地址（缺省回退 DeepSeek）")
    model: Optional[str] = Field(None, description="模型名称（缺省回退 DeepSeek 默认模型）")


def _build_llm_config(request: TranslationRequest) -> Dict:
    """从翻译请求构建大模型厂商配置"""
    return {
        "provider": request.provider,
        "base_url": request.base_url,
        "model": request.model
    }


@router.post("/translation/translate")
async def translate_pdf(
    request: TranslationRequest,
    background_tasks: BackgroundTasks
):
    """
    执行PDF翻译
    
    Args:
        request: 翻译请求
        background_tasks: 后台任务
        
    Returns:
        翻译结果
    """
    try:
        logger.info(
            f"开始翻译: pdf_name={request.pdf_name}, "
            f"use_dps={request.use_dps}, max_concurrent={request.max_concurrent}, "
            f"enable_distribution={request.enable_distribution}"
        )
        
        # 创建翻译任务服务
        task_service = TranslationTaskService()
        
        # 检查预翻译文件是否存在
        pretrans_data = task_service.load_pretranslation_data(
            request.pdf_name, 
            request.use_dps
        )
        
        if not pretrans_data:
            mode_name = "DPS" if request.use_dps else "Python"
            raise HTTPException(
                status_code=404,
                detail=f"{mode_name}模式的预翻译文件不存在，请先调用 /translation/prepare 接口生成"
            )
        
        # 执行翻译（同步方式，适合小文档）
        result = task_service.translate_pdf_sync(
            pdf_name=request.pdf_name,
            api_key=request.api_key,
            use_dps=request.use_dps,
            max_concurrent=request.max_concurrent,
            enable_distribution=request.enable_distribution,
            llm_config=_build_llm_config(request)
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "翻译失败")
            )
        
        return {
            "code": 200,
            "message": "翻译完成",
            "data": result.get("data")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"翻译失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translation/translate/async")
async def translate_pdf_async(request: TranslationRequest):
    try:
        task_id = str(uuid.uuid4())

        # 初始化进度存储
        translation_progress_store[task_id] = {
            "seq": 0,
            "task_id": task_id,
            "pdf_name": request.pdf_name,
            "use_dps": request.use_dps,
            "progress": 0,
            "stage": "starting",
            "message": "开始翻译",
            "current": 0,
            "total": 0,
            "phase": None,
            "result": None,
            "file_path": None,
            "started_at": time.time(),
            "finished_at": None,
            "pending_events": deque(),
        }
        
        # 【关键新增】初始化控制标志
        translation_control_flags[task_id] = {
            "paused": False,
            "stopped": False
        }

        logger.info(
            f"[翻译异步] 创建任务: task_id={task_id[:8]} | pdf={request.pdf_name} | "
            f"use_dps={request.use_dps} | max_concurrent={request.max_concurrent} | "
            f"enable_distribution={request.enable_distribution} | provider={request.provider or 'deepseek'} | "
            f"model={request.model or '-'} | api_key={_mask_api_key(request.api_key)}"
        )

        async def run_translation():
            try:
                task_service = TranslationTaskService()

                def on_progress(progress, current, total, result=None, phase: str = None):
                    try:
                        record = translation_progress_store.get(task_id)
                        if not record:
                            return

                        record["seq"] += 1
                        record["progress"] = round(float(progress), 2)
                        record["stage"] = "running"
                        record["message"] = "翻译中" if phase != "distribution" else "译文分配中"
                        record["current"] = int(current) if current is not None else 0
                        record["total"] = int(total) if total is not None else 0
                        record["phase"] = phase
                        record["result"] = result
                        
                        # 从翻译结果文件读取统计信息
                        try:
                            translation_result = task_service.get_translation_result(request.pdf_name, request.use_dps)
                            if translation_result and "statistics" in translation_result:
                                stats = translation_result["statistics"]
                                record["translation_success"] = stats.get("translation_success", 0)
                                record["translation_failed"] = stats.get("translation_failed", 0)
                                record["distribution_success"] = stats.get("distribution_success", 0)
                                record["distribution_failed"] = stats.get("distribution_failed", 0)
                        except Exception as e:
                            logger.warning(f"[翻译推送] 无法读取统计信息: {str(e)}")

                        pending = record.get("pending_events")
                        if pending is None:
                            pending = deque()
                            record["pending_events"] = pending
                        if len(pending) >= MAX_SSE_EVENT_QUEUE_SIZE:
                            dropped = len(pending) - MAX_SSE_EVENT_QUEUE_SIZE + 1
                            for _ in range(dropped):
                                try:
                                    pending.popleft()
                                except Exception:
                                    break
                            logger.warning(
                                f"[翻译SSE] 事件队列溢出，已丢弃旧事件: task_id={task_id[:8]} dropped~={dropped}"
                            )

                        pending.append({
                            "seq": record.get("seq", 0),
                            "task_id": record.get("task_id"),
                            "pdf_name": record.get("pdf_name"),
                            "use_dps": record.get("use_dps"),
                            "progress": record.get("progress"),
                            "stage": record.get("stage"),
                            "message": record.get("message"),
                            "current": record.get("current"),
                            "total": record.get("total"),
                            "phase": record.get("phase"),
                            "result": record.get("result"),
                            "file_path": record.get("file_path"),
                            "started_at": record.get("started_at"),
                            "finished_at": record.get("finished_at"),
                            "translation_success": record.get("translation_success", 0),
                            "translation_failed": record.get("translation_failed", 0),
                            "distribution_success": record.get("distribution_success", 0),
                            "distribution_failed": record.get("distribution_failed", 0),
                        })

                        if result and isinstance(result, dict):
                            rid = result.get("task_id")
                            status = result.get("status")
                            logger.info(
                                f"[翻译推送] task_id={task_id[:8]} | phase={phase} | "
                                f"{record['current']}/{record['total']} | "
                                f"result_task_id={rid} | status={status} | progress={record['progress']}%"
                            )
                    except Exception as e:
                        logger.error(f"[翻译推送] 回调异常: task_id={task_id[:8]} | {str(e)}")

                result = await task_service.translate_pdf_async(
                    pdf_name=request.pdf_name,
                    api_key=request.api_key,
                    use_dps=request.use_dps,
                    max_concurrent=request.max_concurrent,
                    enable_distribution=request.enable_distribution,
                    progress_callback=on_progress,
                    control_flags=translation_control_flags.get(task_id),  # 【新增】传递控制标志
                    llm_config=_build_llm_config(request)  # 【新增】传递大模型厂商配置
                )

                record = translation_progress_store.get(task_id)
                if not record:
                    return

                record["seq"] += 1
                if result.get("success"):
                    record["progress"] = 100
                    record["stage"] = "completed"
                    record["message"] = "翻译完成"
                    record["file_path"] = result.get("file_path")
                    record["finished_at"] = time.time()
                    logger.info(f"[翻译异步] 完成: task_id={task_id[:8]} | file={record['file_path']}")
                else:
                    record["progress"] = 0
                    record["stage"] = "error"
                    record["message"] = result.get("error", "翻译失败")
                    record["finished_at"] = time.time()
                    logger.error(f"[翻译异步] 失败: task_id={task_id[:8]} | {record['message']}")

                pending = record.get("pending_events")
                if pending is None:
                    pending = deque()
                    record["pending_events"] = pending
                pending.append({
                    "seq": record.get("seq", 0),
                    "task_id": record.get("task_id"),
                    "pdf_name": record.get("pdf_name"),
                    "use_dps": record.get("use_dps"),
                    "progress": record.get("progress"),
                    "stage": record.get("stage"),
                    "message": record.get("message"),
                    "current": record.get("current"),
                    "total": record.get("total"),
                    "phase": record.get("phase"),
                    "result": record.get("result"),
                    "file_path": record.get("file_path"),
                    "started_at": record.get("started_at"),
                    "finished_at": record.get("finished_at"),
                    "translation_success": record.get("translation_success", 0),
                    "translation_failed": record.get("translation_failed", 0),
                    "distribution_success": record.get("distribution_success", 0),
                    "distribution_failed": record.get("distribution_failed", 0),
                })

                async def cleanup():
                    await asyncio.sleep(300)
                    if task_id in translation_progress_store:
                        del translation_progress_store[task_id]
                        logger.info(f"[翻译异步] 清理任务: task_id={task_id[:8]}")
                    # 【新增】清理控制标志
                    if task_id in translation_control_flags:
                        del translation_control_flags[task_id]

                asyncio.create_task(cleanup())

            except Exception as e:
                record = translation_progress_store.get(task_id)
                if record:
                    record["seq"] += 1
                    record["progress"] = 0
                    record["stage"] = "error"
                    record["message"] = str(e)
                    record["finished_at"] = time.time()
                    pending = record.get("pending_events")
                    if pending is None:
                        pending = deque()
                        record["pending_events"] = pending
                    pending.append({
                        "seq": record.get("seq", 0),
                        "task_id": record.get("task_id"),
                        "pdf_name": record.get("pdf_name"),
                        "use_dps": record.get("use_dps"),
                        "progress": record.get("progress"),
                        "stage": record.get("stage"),
                        "message": record.get("message"),
                        "current": record.get("current", 0),
                        "total": record.get("total", 0),
                        "phase": record.get("phase"),
                        "result": record.get("result"),
                        "file_path": record.get("file_path"),
                        "started_at": record.get("started_at"),
                        "finished_at": record.get("finished_at"),
                        "translation_success": record.get("translation_success", 0),
                        "translation_failed": record.get("translation_failed", 0),
                        "distribution_success": record.get("distribution_success", 0),
                        "distribution_failed": record.get("distribution_failed", 0),
                    })
                logger.error(f"[翻译异步] 异常: task_id={task_id[:8]} | {str(e)}")

        asyncio.create_task(run_translation())

        return {
            "code": 200,
            "message": "翻译任务已创建",
            "data": {"task_id": task_id}
        }

    except Exception as e:
        logger.error(f"创建异步翻译任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translation/progress/{task_id}")
async def get_translation_progress(task_id: str):
    async def event_generator():
        try:
            start_time = time.time()
            max_wait_time = 3600

            last_seq = -1
            while True:
                elapsed = time.time() - start_time
                if elapsed > max_wait_time:
                    logger.warning(f"[翻译SSE] 超时结束: task_id={task_id[:8]}")
                    yield f"data: {json.dumps({'progress': 0, 'stage': 'error', 'message': '翻译推送超时(60分钟)'}, ensure_ascii=False)}\n\n"
                    break

                record = translation_progress_store.get(task_id)
                if record:
                    pending = record.get("pending_events")
                    if pending:
                        while pending:
                            event = pending.popleft()
                            event_seq = event.get("seq", 0)
                            if event_seq <= last_seq:
                                continue
                            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                            last_seq = event_seq
                            if event.get("stage") in ("completed", "error"):
                                await asyncio.sleep(0.1)
                                return
                        await asyncio.sleep(0.05)
                        continue

                    current_seq = record.get("seq", 0)
                    if current_seq != last_seq:
                        safe_record = dict(record)
                        safe_record.pop("pending_events", None)
                        yield f"data: {json.dumps(safe_record, ensure_ascii=False)}\n\n"
                        last_seq = current_seq

                        if record.get("stage") in ("completed", "error"):
                            await asyncio.sleep(0.1)
                            break

                await asyncio.sleep(0.3)

        except Exception as e:
            logger.error(f"[翻译SSE] 异常: task_id={task_id[:8]} | {str(e)}")
            yield f"data: {json.dumps({'progress': 0, 'stage': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/translation/result/{pdf_name}")
async def get_translation_result(
    pdf_name: str,
    use_dps: bool = Query(False, description="是否使用DPS模式")
):
    """
    获取翻译结果
    
    Args:
        pdf_name: PDF文件名
        use_dps: 是否使用DPS模式
        
    Returns:
        翻译结果
    """
    try:
        task_service = TranslationTaskService()
        result = task_service.get_translation_result(pdf_name, use_dps)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="翻译结果不存在"
            )
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取翻译结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 【新增】翻译控制接口

@router.post("/translation/control/{task_id}/pause")
async def pause_translation(task_id: str):
    """
    暂停翻译任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        if task_id not in translation_control_flags:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        translation_control_flags[task_id]["paused"] = True
        logger.info(f"[翻译控制] 暂停: task_id={task_id[:8]}")
        
        return {
            "code": 200,
            "message": "已暂停翻译任务",
            "data": {"task_id": task_id, "paused": True}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停翻译失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translation/control/{task_id}/resume")
async def resume_translation(task_id: str):
    """
    继续翻译任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        if task_id not in translation_control_flags:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        translation_control_flags[task_id]["paused"] = False
        logger.info(f"[翻译控制] 继续: task_id={task_id[:8]}")
        
        return {
            "code": 200,
            "message": "已继续翻译任务",
            "data": {"task_id": task_id, "paused": False}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"继续翻译失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translation/control/{task_id}/stop")
async def stop_translation(task_id: str):
    """
    停止翻译任务（【新增】删除翻译结果文件）
    
    Args:
        task_id: 任务ID
        
    Returns:
        操作结果
    """
    try:
        if task_id not in translation_control_flags:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 设置停止标志
        translation_control_flags[task_id]["stopped"] = True
        logger.info(f"[翻译控制] 停止: task_id={task_id[:8]}")
        
        # 【关键新增】删除翻译结果文件
        record = translation_progress_store.get(task_id)
        if record:
            pdf_name = record.get("pdf_name")
            use_dps = record.get("use_dps", False)
            
            if pdf_name:
                from pathlib import Path
                task_service = TranslationTaskService()
                translation_file = task_service.get_translation_result_path(pdf_name, use_dps)
                
                if translation_file.exists():
                    try:
                        translation_file.unlink()
                        logger.info(f"[翻译控制] 删除翻译文件: {translation_file}")
                    except Exception as e:
                        logger.error(f"[翻译控制] 删除翻译文件失败: {str(e)}")
        
        return {
            "code": 200,
            "message": "已停止翻译任务并删除翻译结果",
            "data": {"task_id": task_id, "stopped": True}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止翻译失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translation/control/{task_id}/status")
async def get_translation_control_status(task_id: str):
    """
    获取翻译任务控制状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        控制状态
    """
    try:
        if task_id not in translation_control_flags:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        flags = translation_control_flags[task_id]
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "task_id": task_id,
                "paused": flags.get("paused", False),
                "stopped": flags.get("stopped", False)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取控制状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translation/active-tasks")
async def get_active_translation_tasks():
    """
    获取所有活跃的翻译任务状态
    用于在已解析PDF列表中实时显示翻译进度
    
    Returns:
        活跃任务列表 {pdf_name: {task_id, progress, stage, ...}}
    """
    try:
        active_tasks = {}
        
        for task_id, record in translation_progress_store.items():
            pdf_name = record.get("pdf_name")
            if not pdf_name:
                continue
            
            stage = record.get("stage", "unknown")
            # 只返回正在运行的任务（排除已完成/失败/错误的）
            if stage in ("starting", "running"):
                active_tasks[pdf_name] = {
                    "task_id": task_id,
                    "pdf_name": pdf_name,
                    "use_dps": record.get("use_dps", False),
                    "progress": record.get("progress", 0),
                    "stage": stage,
                    "message": record.get("message", ""),
                    "current": record.get("current", 0),
                    "total": record.get("total", 0),
                    "translation_success": record.get("translation_success", 0),
                    "translation_failed": record.get("translation_failed", 0),
                    "started_at": record.get("started_at"),
                }
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": active_tasks
        }
        
    except Exception as e:
        logger.error(f"获取活跃翻译任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
