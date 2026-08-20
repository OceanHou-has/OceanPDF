"""
通用 LLM 翻译服务
通过 OpenAI 兼容协议统一接入各大模型厂商（DeepSeek / 千问 / 豆包 / Google / GPT 等）
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
from openai import OpenAI, AsyncOpenAI
import openai
import aiohttp
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
        测试 API 连接（同步包装，兼容旧调用方）
        """
        try:
            return asyncio.run(self.test_connection_async())
        except RuntimeError:
            # 已处于事件循环内（如 FastAPI 异步上下文直接调用）时用独立线程执行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, self.test_connection_async()).result()

    async def test_connection_async(self) -> Dict[str, Any]:
        """
        测试 API 连接（异步、快速失败版）

        优化策略：
        - 使用轻量级 models.list 接口（通常 0.3-1秒）
        - 测试专用短超时（8秒），避免网络异常时长时间等待
        - 认证类错误（401/403）立即返回失败，不再回退发对话请求
        - 仅当接口不支持 models.list（404/405）时才回退到最小对话请求
        """
        t0 = time.monotonic()
        # 测试专用短超时，避免复用翻译任务的长超时（180s）
        test_timeout = 8.0

        # 1. 优先尝试 models.list
        try:
            models = await self.async_client.models.list(timeout=test_timeout)
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
        except openai.AuthenticationError as e:
            # Key 无效，无需再试
            logger.warning(f"API 认证失败: {str(e)}")
            return self._fail_result(f"认证失败: API Key 无效或已过期")
        except openai.PermissionDeniedError as e:
            logger.warning(f"API 无权限访问: {str(e)}")
            return self._fail_result(f"认证失败: API Key 没有权限访问该服务")
        except openai.APITimeoutError:
            logger.warning("models.list 超时")
            return self._fail_result(f"连接超时（>{int(test_timeout)}秒），请检查网络连接或接口地址")
        except openai.NotFoundError as e:
            # 部分厂商不支持 models.list，回退到最小对话请求
            logger.info(f"models.list 不支持，回退对话测试: {str(e)}")
        except openai.APIStatusError as e:
            if e.status_code == 405:
                logger.info("models.list 不支持(405)，回退对话测试")
            else:
                # 其他 HTTP 错误（如 429 限流）：服务可达，按连通成功提示
                logger.warning(f"models.list 返回 HTTP {e.status_code}")
                if e.status_code == 429:
                    return {
                        "success": True,
                        "message": f"连接正常，但请求频率过高（{self.provider}）",
                        "provider": self.provider,
                        "model": self.model
                    }
                return self._fail_result(f"请求失败 (HTTP {e.status_code}): {str(e)[:200]}")
        except openai.APIConnectionError as e:
            logger.warning(f"无法连接到 API 服务: {str(e)}")
            return self._fail_result(f"无法连接到服务，请检查接口地址和网络: {str(e)[:200]}")
        except Exception as e:
            logger.warning(f"models.list 测试失败，回退到对话测试: {str(e)}")

        # 2. 回退：最小对话请求（仅用于不支持 models.list 的厂商）
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
                timeout=test_timeout * 2
            )
            return {
                "success": True,
                "message": f"连接正常（{self.provider} / {self.model}）",
                "provider": self.provider,
                "model": self.model,
                "response": response.choices[0].message.content
            }
        except openai.AuthenticationError:
            return self._fail_result("认证失败: API Key 无效或已过期")
        except openai.PermissionDeniedError:
            return self._fail_result("认证失败: API Key 没有权限访问该服务")
        except openai.APITimeoutError:
            return self._fail_result(f"连接超时，请检查网络连接或接口地址")
        except Exception as e:
            logger.error(f"API 连接测试失败: {str(e)}")
            return self._fail_result(f"连接失败: {str(e)[:300]}")

    def _fail_result(self, message: str) -> Dict[str, Any]:
        return {
            "success": False,
            "message": message,
            "provider": self.provider,
            "model": self.model
        }


async def test_llm_connection_lightweight(
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    轻量级连通性测试（直接 HTTP 调用，不构建 SDK 客户端）

    背景：OpenAI SDK 客户端构造本身约需 1秒/个，而测试接口只需一次
    models.list 请求（~0.2s），故改用 aiohttp 直接请求，总耗时可降至 0.5s 以内。
    判定策略与 test_connection_async 一致：认证错误立即失败，429 视为连通。
    """
    url = (base_url or settings.DEEPSEEK_API_BASE).strip().rstrip("/") + "/models"
    model_name = (model or settings.DEEPSEEK_MODEL).strip()
    provider_name = (provider or "").strip() or "deepseek"
    headers = {"Authorization": f"Bearer {api_key}"}

    def _ok(message: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = {"success": True, "message": message, "provider": provider_name, "model": model_name}
        if extra:
            result.update(extra)
        return result

    def _fail(message: str) -> Dict[str, Any]:
        return {"success": False, "message": message, "provider": provider_name, "model": model_name}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = {}

                if resp.status == 200:
                    model_ids = []
                    try:
                        model_ids = [m.get("id", "") for m in (data.get("data") or [])][:5]
                    except Exception:
                        pass
                    return _ok(f"连接正常（{provider_name} / {model_name}）", {"available_models": model_ids})
                if resp.status in (401, 403):
                    return _fail("认证失败: API Key 无效或已过期")
                if resp.status == 429:
                    return _ok(f"连接正常，但请求频率过高（{provider_name}）")
                if resp.status in (404, 405):
                    # 厂商不支持 models.list：能收到响应说明服务可达，视为连通
                    return _ok(f"连接成功（{provider_name} 不支持模型列表查询，已验证服务可达）")
                msg = ""
                if isinstance(data, dict):
                    err = data.get("error") or {}
                    msg = err.get("message", "") if isinstance(err, dict) else str(err)
                return _fail(f"请求失败 (HTTP {resp.status}): {msg or '未知错误'}")
    except asyncio.TimeoutError:
        return _fail("连接超时（>8秒），请检查网络连接或接口地址")
    except aiohttp.ClientError as e:
        return _fail(f"无法连接到服务，请检查接口地址和网络: {str(e)[:200]}")
    except Exception as e:
        logger.error(f"轻量级连接测试异常: {str(e)}")
        return _fail(f"测试异常: {str(e)[:200]}")


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
