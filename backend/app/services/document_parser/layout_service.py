"""
版面分析统一入口
根据 provider_id 分发到本地DPS服务或外部文档解析服务，
外部服务结果归一化为 dps.json 兼容格式后落盘
"""
import json
import time
from typing import Any, Dict, Optional

from loguru import logger

from app.services.document_parser.config_store import get_provider_config
from app.services.document_parser.layout_paths import (
    LOCAL_PROVIDER,
    get_parsed_dir,
    is_external_provider,
)
from app.services.document_parser.parsers import PARSER_REGISTRY
from app.services.document_parser.providers import get_provider
from app.services.dps_service import DPSService


async def analyze_with_provider(
    pdf_path: str,
    pdf_name: str,
    provider_id: str,
    *,
    with_ocr: Optional[bool] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    使用指定服务执行版面分析

    Args:
        pdf_path: PDF文件路径
        pdf_name: PDF名称
        provider_id: 服务ID（"dps"=本地DPS，其余为外部服务）
        with_ocr: 是否执行OCR（仅本地DPS有效，外部服务自带文本识别）
        force: 是否强制重新解析

    Returns:
        与 DPSService.analyze_pdf 一致的结果结构:
        {"success", "already_exists", "pdf_name", "dps_json_path", "req_id", "elapsed_sec", "pages", ...}
    """
    provider_id = provider_id or LOCAL_PROVIDER

    # 本地DPS：直接转发
    if provider_id == LOCAL_PROVIDER:
        dps_service = DPSService()
        return await dps_service.analyze_pdf(
            pdf_path=pdf_path,
            pdf_name=pdf_name,
            with_ocr=with_ocr,
            force=force,
        )

    # 外部服务
    if not is_external_provider(provider_id):
        raise RuntimeError(f"未知的解析服务: {provider_id}")

    parser_entry = PARSER_REGISTRY.get(provider_id)
    if not parser_entry:
        raise RuntimeError(f"解析服务暂未实现真实解析调用: {provider_id}")

    provider_meta = get_provider(provider_id)
    provider_name = provider_meta["name"] if provider_meta else provider_id

    output_path = get_parsed_dir(pdf_name) / f"{provider_id}.json"

    # 结果已存在则直接复用
    if output_path.exists() and not force:
        logger.info(f"[版面分析] {provider_name} 结果已存在: {pdf_name}")
        return {
            "success": True,
            "already_exists": True,
            "pdf_name": pdf_name,
            "provider": provider_id,
            "provider_name": provider_name,
            "dps_json_path": str(output_path),
            "with_ocr": False,
        }

    # 读取已保存配置并校验必填字段
    config = get_provider_config(provider_id)
    if provider_meta:
        missing = [
            f["label"]
            for f in provider_meta["config_fields"]
            if f.get("required") and not config.get(f["key"])
        ]
        if missing:
            raise RuntimeError(
                f"{provider_name}未配置（缺少: {'、'.join(missing)}），请先在设置页完成配置"
            )

    logger.info(f"[版面分析] 开始调用外部服务: {provider_name} | {pdf_name}")
    t0 = time.monotonic()

    try:
        raw_result = await parser_entry["parse"](pdf_path, config)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"{provider_name}解析失败: {str(e)}") from e

    normalized = parser_entry["normalize"](raw_result)
    pages = normalized.get("pages") or []
    if not any(p.get("boxes") for p in pages):
        logger.warning(f"[版面分析] {provider_name}未返回任何版面框: {pdf_name}")

    elapsed = round(time.monotonic() - t0, 2)
    req_id = normalized.get("req_id")

    payload = {
        "pdf_name": pdf_name,
        "generated_at": int(time.time()),
        "meta": {
            "provider": provider_id,
            "provider_name": provider_name,
            "with_ocr": False,
            "req_id": req_id,
            "elapsed_sec": normalized.get("elapsed_sec") or elapsed,
            "pages": len(pages),
            "usage": raw_result.get("usage"),
        },
        "raw": normalized,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(
        f"✅ [版面分析] {provider_name}完成: {pdf_name} | {len(pages)}页 | 耗时: {elapsed}s"
    )

    return {
        "success": True,
        "already_exists": False,
        "pdf_name": pdf_name,
        "provider": provider_id,
        "provider_name": provider_name,
        "dps_json_path": str(output_path),
        "req_id": req_id,
        "elapsed_sec": elapsed,
        "pages": len(pages),
        "with_ocr": False,
    }
