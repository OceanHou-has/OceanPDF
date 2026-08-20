"""
文档解析服务配置存储
统一读写 storage/config/document_parser_config.json
"""
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path("storage/config/document_parser_config.json")

# 配置文件中的保留字段：默认解析服务ID（dps=本地DPS）
DEFAULT_PARSER_KEY = "default_parser"
LOCAL_PARSER_ID = "dps"


def read_config() -> Dict[str, Any]:
    """读取文档解析服务配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def write_config(config: Dict[str, Any]) -> None:
    """写入文档解析服务配置文件"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_provider_config(provider_id: str) -> Dict[str, Any]:
    """获取指定服务的已保存配置"""
    return read_config().get(provider_id, {})


def get_default_parser() -> str:
    """获取默认解析服务ID（未设置时返回本地DPS）"""
    value = read_config().get(DEFAULT_PARSER_KEY)
    return value if isinstance(value, str) and value else LOCAL_PARSER_ID


def set_default_parser(provider_id: str) -> None:
    """设置默认解析服务ID"""
    config = read_config()
    config[DEFAULT_PARSER_KEY] = provider_id or LOCAL_PARSER_ID
    write_config(config)
