"""
文档解析服务 API 路由
提供配置管理、连通性测试等接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from loguru import logger

from app.services.document_parser.providers import get_providers, get_provider
from app.services.document_parser.connectivity import test_connectivity
from app.services.document_parser.config_store import (
    read_config as _read_config,
    write_config as _write_config,
)

router = APIRouter()


def _mask_key(value: str) -> str:
    """脱敏密钥"""
    if not value:
        return ""
    if len(value) <= 6:
        return value[:2] + "***"
    return value[:3] + "***" + value[-3:]


def _mask_config(provider_id: str, config: Dict[str, str]) -> Dict[str, str]:
    """对配置中的敏感字段进行脱敏"""
    masked = {}
    sensitive_keys = {"api_key", "secret_key", "access_key_secret", "sk", "secret_code"}
    for key, value in config.items():
        if key in sensitive_keys:
            masked[key] = _mask_key(value)
        else:
            masked[key] = value
    return masked


class SaveConfigRequest(BaseModel):
    """保存配置请求"""
    provider_id: str = Field(..., description="服务ID")
    config: Dict[str, str] = Field(..., description="配置内容")


class TestConnectionRequest(BaseModel):
    """测试连通性请求"""
    provider_id: str = Field(..., description="服务ID")
    config: Dict[str, str] = Field(..., description="配置内容（可选，不传则使用已保存配置）")


@router.get("/document-parser/providers")
async def list_providers():
    """
    获取所有文档解析服务列表（含配置字段、描述）
    """
    try:
        providers = get_providers()
        return {
            "code": 200,
            "message": "获取成功",
            "data": providers
        }
    except Exception as e:
        logger.error(f"获取文档解析服务列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document-parser/config")
async def get_config():
    """
    获取已保存的文档解析服务配置（密钥脱敏）
    """
    try:
        config = _read_config()
        masked_config = {}
        for provider_id, provider_config in config.items():
            masked_config[provider_id] = _mask_config(provider_id, provider_config)

        return {
            "code": 200,
            "message": "获取成功",
            "data": masked_config
        }
    except Exception as e:
        logger.error(f"获取文档解析配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document-parser/config")
async def save_config(request: SaveConfigRequest):
    """
    保存文档解析服务配置
    """
    try:
        provider = get_provider(request.provider_id)
        if not provider:
            raise HTTPException(status_code=400, detail=f"未知的服务ID: {request.provider_id}")

        # 验证必填字段
        for field in provider["config_fields"]:
            if field["required"] and not request.config.get(field["key"]):
                raise HTTPException(status_code=400, detail=f"缺少必填字段: {field['label']}")

        # 读取现有配置
        config = _read_config()

        # 更新指定服务的配置（保留已有字段，覆盖新值；脱敏占位值不覆盖真实密钥）
        existing = config.get(request.provider_id, {})
        for key, value in request.config.items():
            if value and "***" not in value:  # 只更新非空且非脱敏的值
                existing[key] = value
        config[request.provider_id] = existing

        _write_config(config)

        masked = _mask_config(request.provider_id, existing)
        logger.info(f"文档解析配置已保存: {request.provider_id}")

        return {
            "code": 200,
            "message": "配置保存成功",
            "data": {
                "provider_id": request.provider_id,
                "config": masked
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存文档解析配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document-parser/test")
async def test_connection(request: TestConnectionRequest):
    """
    测试文档解析服务连通性
    """
    try:
        provider = get_provider(request.provider_id)
        if not provider:
            raise HTTPException(status_code=400, detail=f"未知的服务ID: {request.provider_id}")

        # 使用传入的配置，或回退到已保存的配置
        config = request.config
        if not config or all(not v for v in config.values()):
            saved_config = _read_config()
            config = saved_config.get(request.provider_id, {})
            if not config:
                raise HTTPException(status_code=400, detail=f"未配置 {provider['name']}，请先填写配置")

        # 执行连通性测试
        result = await test_connectivity(request.provider_id, config)

        return {
            "code": 200 if result["success"] else 500,
            "message": result["message"],
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试文档解析连通性失败: {str(e)}")
        return {
            "code": 500,
            "message": f"测试异常: {str(e)}",
            "data": {"success": False, "message": str(e), "latency_ms": 0}
        }


@router.get("/document-parser/status")
async def get_status():
    """
    获取各文档解析服务配置状态（已配置/未配置）
    """
    try:
        config = _read_config()
        providers = get_providers()

        status_list = []
        for provider in providers:
            pid = provider["id"]
            provider_config = config.get(pid, {})

            # 检查必填字段是否都已配置
            required_fields = [f["key"] for f in provider["config_fields"] if f["required"]]
            is_configured = all(provider_config.get(f) for f in required_fields)

            status_list.append({
                "id": pid,
                "name": provider["name"],
                "emoji": provider["emoji"],
                "configured": is_configured
            })

        return {
            "code": 200,
            "message": "获取成功",
            "data": status_list
        }
    except Exception as e:
        logger.error(f"获取文档解析状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/document-parser/config/{provider_id}")
async def delete_config(provider_id: str):
    """
    删除指定服务的配置
    """
    try:
        provider = get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=400, detail=f"未知的服务ID: {provider_id}")

        config = _read_config()
        if provider_id in config:
            del config[provider_id]
            _write_config(config)
            logger.info(f"文档解析配置已删除: {provider_id}")

        return {
            "code": 200,
            "message": "配置已删除",
            "data": {"provider_id": provider_id}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档解析配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

