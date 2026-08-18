"""
DeepSeek 翻译服务（向后兼容层）
现已统一由通用 LLM 翻译服务（llm_service.py）实现，
DeepSeek 仅作为默认厂商配置保留，原有调用方式不变。
"""
from typing import Optional
from loguru import logger

from app.core.config import settings
from app.services.translation.llm_service import LLMTranslationService


class DeepSeekTranslationService(LLMTranslationService):
    """DeepSeek 翻译服务类（通用 LLM 服务的 DeepSeek 默认实现）"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 DeepSeek 翻译服务

        Args:
            api_key: DeepSeek API Key（如果不提供则从配置读取）
        """
        resolved_key = api_key or settings.DEEPSEEK_API_KEY

        if not resolved_key:
            logger.warning("DeepSeek API Key 未配置")
            raise ValueError("DeepSeek API Key is required")

        super().__init__(
            api_key=resolved_key,
            base_url=settings.DEEPSEEK_API_BASE,
            model=settings.DEEPSEEK_MODEL,
            provider="deepseek",
            temperature=settings.DEEPSEEK_TEMPERATURE,
            max_tokens=settings.DEEPSEEK_MAX_TOKENS,
            timeout=settings.DEEPSEEK_TIMEOUT,
        )

        logger.info(f"DeepSeek 翻译服务初始化成功，模型: {settings.DEEPSEEK_MODEL}")
