"""
版面分析结果文件路径解析
根据 parsed.json 中的 layout_provider 字段定位当前生效的版面结果文件：
- layout_provider 为 "dps"（默认）时读取 dps.json
- 外部服务时读取 {provider_id}.json（不存在则回退 dps.json）
"""
import json
from pathlib import Path
from typing import Optional

from app.services.pdf_id_mapper import get_pdf_id_mapper

LOCAL_PROVIDER = "dps"


def get_parsed_dir(pdf_name: str, parsed_base_dir: Optional[str] = None) -> Path:
    """获取PDF的解析结果目录（短ID），可指定自定义base目录"""
    mapper = get_pdf_id_mapper()
    pdf_id = mapper.get_or_create_id(pdf_name)
    base = Path(parsed_base_dir) if parsed_base_dir else Path("storage/parsed")
    return base / pdf_id


def get_layout_provider(pdf_name: str, parsed_base_dir: Optional[str] = None) -> str:
    """读取 parsed.json 中记录的版面分析服务（默认 dps）"""
    parsed_json = get_parsed_dir(pdf_name, parsed_base_dir) / "parsed.json"
    if parsed_json.exists():
        try:
            with open(parsed_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            provider = data.get("layout_provider")
            if provider:
                return str(provider)
        except Exception:
            pass
    return LOCAL_PROVIDER


def get_layout_json_path(
    pdf_name: str,
    provider_id: Optional[str] = None,
    parsed_base_dir: Optional[str] = None,
) -> Path:
    """
    获取当前生效的版面分析结果文件路径

    Args:
        pdf_name: PDF名称
        provider_id: 显式指定服务ID（None=按 parsed.json 中的 layout_provider 解析）
        parsed_base_dir: 自定义解析结果根目录（默认 storage/parsed）
    """
    parsed_dir = get_parsed_dir(pdf_name, parsed_base_dir)

    if provider_id is None:
        provider_id = get_layout_provider(pdf_name, parsed_base_dir)

    if provider_id and provider_id != LOCAL_PROVIDER:
        provider_path = parsed_dir / f"{provider_id}.json"
        if provider_path.exists():
            return provider_path

    return parsed_dir / "dps.json"


def is_external_provider(provider_id: Optional[str]) -> bool:
    """判断是否为外部解析服务"""
    return bool(provider_id) and provider_id != LOCAL_PROVIDER
