"""
通用 LLM 翻译服务
通过 OpenAI 兼容协议统一接入各大模型厂商（DeepSeek / 千问 / 豆包 / Google / GPT 等）
"""
import asyncio
from typing import Dict, List, Optional, Any
from openai import OpenAI, AsyncOpenAI
from loguru import logger

from app.core.config import settings


class LLMTranslationService:
    """通用大模型翻译服务类（OpenAI 兼容协议）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        初始化通用翻译服务

        Args:
            api_key: API Key（必填）
            base_url: OpenAI 兼容接口地址（默认 DeepSeek）
            model: 模型名称（默认 DeepSeek 模型）
            provider: 厂商ID（仅用于日志展示）
            temperature: 采样温度
            max_tokens: 单次请求最大 token 数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("API Key is required")

        self.base_url = (base_url or settings.DEEPSEEK_API_BASE).strip()
        self.model = (model or settings.DEEPSEEK_MODEL).strip()
        self.provider = provider or "unknown"
        self.temperature = settings.DEEPSEEK_TEMPERATURE if temperature is None else temperature
        self.max_tokens = max_tokens or settings.DEEPSEEK_MAX_TOKENS
        self.timeout = timeout or settings.DEEPSEEK_TIMEOUT

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
        except TypeError as e:
            # 兼容旧版本 openai SDK 的参数差异
            logger.warning(f"初始化时遇到参数问题，使用基础配置: {str(e)}")
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(
            f"LLM 翻译服务初始化成功: provider={self.provider}, "
            f"model={self.model}, base_url={self.base_url}"
        )

    def _build_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: str = "body",
        element_type: str = "paragraph",
        previous_context: Optional[str] = None
    ) -> str:
        """
        构建翻译提示词

        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言
            context: 上下文类型（title/heading/body/caption/footnote等）
            element_type: 元素类型
            previous_context: 前文上下文（可选，用于保持连贯性）

        Returns:
            提示词字符串
        """
        # 语言代码映射
        lang_map = {
            "en": "英语",
            "zh": "中文",
            "zh-CN": "简体中文",
            "zh-TW": "繁体中文",
            "ja": "日语",
            "ko": "韩语",
            "fr": "法语",
            "de": "德语",
            "es": "西班牙语",
            "ru": "俄语"
        }

        source_lang_name = lang_map.get(source_lang, source_lang)
        target_lang_name = lang_map.get(target_lang, target_lang)

        # 根据上下文类型调整翻译指导
        context_instructions = {
            "title": "这是文档标题，请保持简洁准确，突出核心主题。",
            "heading": "这是章节标题，请保持简洁准确，突出要点。",
            "body": "这是正文段落，请确保翻译流畅自然，保持学术语言风格。",
            "list": "这是列表项，请保持简洁清晰。",
            "caption": "这是图表标题，请简洁准确。",
            "footnote": "这是脚注或注释，请保持简洁。"
        }

        instruction = context_instructions.get(context, context_instructions["body"])

        # 构建提示词
        prompt = f"""你是一位专业的学术论文翻译专家，擅长将{source_lang_name}学术论文翻译成{target_lang_name}。

翻译要求：
1. {instruction}
2. 保持专业术语的准确性
3. 保持原文的段落结构和格式
4. 数字、公式、专有名词（如人名、地名）保持原样
5. 确保翻译的学术性和可读性
6. 直接输出翻译结果，不要添加任何解释或注释

待翻译文本：
{text}

翻译结果："""

        return prompt

    def translate_text(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "zh-CN",
        context: str = "body",
        element_type: str = "paragraph",
        stream: bool = False
    ) -> str:
        """同步翻译文本"""
        try:
            prompt = self._build_translation_prompt(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                element_type=element_type
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional academic paper translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=stream
            )

            if stream:
                translated_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        translated_text += chunk.choices[0].delta.content
                return translated_text
            else:
                return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"翻译失败: {str(e)}")
            raise

    async def translate_text_async(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "zh-CN",
        context: str = "body",
        element_type: str = "paragraph",
        task_id: Optional[str] = None
    ) -> str:
        """异步翻译文本"""
        try:
            prompt = self._build_translation_prompt(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                element_type=element_type
            )

            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional academic paper translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"异步翻译失败: {str(e)}")
            raise

    async def translate_batch_async(
        self,
        texts: List[Dict[str, Any]],
        source_lang: str = "en",
        target_lang: str = "zh-CN",
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """批量异步翻译（带并发控制）"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def translate_with_semaphore(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    translated_text = await self.translate_text_async(
                        text=item["text"],
                        source_lang=source_lang,
                        target_lang=target_lang,
                        context=item.get("context", "body"),
                        element_type=item.get("element_type", "paragraph")
                    )

                    return {
                        "task_id": item.get("task_id"),
                        "source_text": item["text"],
                        "translated_text": translated_text,
                        "status": "success",
                        "error": None
                    }
                except Exception as e:
                    logger.error(f"翻译任务 {item.get('task_id')} 失败: {str(e)}")
                    return {
                        "task_id": item.get("task_id"),
                        "source_text": item["text"],
                        "translated_text": None,
                        "status": "failed",
                        "error": str(e)
                    }

        tasks = [translate_with_semaphore(item) for item in texts]
        results = await asyncio.gather(*tasks)

        return results

    def test_connection(self) -> Dict[str, Any]:
        """
        测试 API 连接
        优先使用轻量级 models.list 接口（0.3-1秒），失败时回退到一次最小对话请求
        """
        # 1. 优先尝试 models.list
        try:
            models = self.client.models.list()
            model_ids = []
            try:
                model_ids = [m.id for m in getattr(models, "data", [])][:5]
            except Exception:
                pass
            return {
                "success": True,
                "message": f"连接正常（{self.provider} / {self.model}）",
                "provider": self.provider,
                "model": self.model,
                "available_models": model_ids
            }
        except Exception as e:
            list_err = str(e)
            logger.warning(f"models.list 测试失败，回退到对话测试: {list_err}")

        # 2. 回退：最小对话请求
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {
                "success": True,
                "message": f"连接正常（{self.provider} / {self.model}）",
                "provider": self.provider,
                "model": self.model,
                "response": response.choices[0].message.content
            }
        except Exception as e:
            logger.error(f"API 连接测试失败: {str(e)}")
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "provider": self.provider,
                "model": self.model
            }


def create_translation_service(
    api_key: str,
    llm_config: Optional[Dict[str, Any]] = None
) -> LLMTranslationService:
    """
    根据 llm_config 创建翻译服务实例

    Args:
        api_key: API Key
        llm_config: {"provider": str, "base_url": str, "model": str}
                    缺省时回退到 DeepSeek 默认配置（向后兼容）
    """
    cfg = llm_config or {}
    base_url = (cfg.get("base_url") or "").strip() or None
    model = (cfg.get("model") or "").strip() or None
    provider = (cfg.get("provider") or "").strip() or "deepseek"
    return LLMTranslationService(
        api_key=api_key,
        base_url=base_url,
        model=model,
        provider=provider
    )
