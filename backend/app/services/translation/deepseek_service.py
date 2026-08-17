"""
DeepSeek 翻译服务
使用 DeepSeek API 进行论文翻译
"""
import asyncio
from typing import Dict, List, Optional, Any
from openai import OpenAI, AsyncOpenAI
from loguru import logger

from app.core.config import settings


class DeepSeekTranslationService:
    """DeepSeek 翻译服务类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 DeepSeek 翻译服务
        
        Args:
            api_key: DeepSeek API Key（如果不提供则从配置读取）
        """
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置")
            raise ValueError("DeepSeek API Key is required")
        
        # 初始化同步和异步客户端
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=settings.DEEPSEEK_API_BASE,
                timeout=settings.DEEPSEEK_TIMEOUT
            )
            
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=settings.DEEPSEEK_API_BASE,
                timeout=settings.DEEPSEEK_TIMEOUT
            )
        except TypeError as e:
            # 如果timeout参数也不支持，则使用最基础的初始化
            logger.warning(f"初始化时遇到参数问题，使用基础配置: {str(e)}")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=settings.DEEPSEEK_API_BASE
            )
            
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=settings.DEEPSEEK_API_BASE
            )
        
        logger.info(f"DeepSeek 翻译服务初始化成功，模型: {settings.DEEPSEEK_MODEL}")
    
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
        """
        同步翻译文本
        
        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言
            context: 上下文类型
            element_type: 元素类型
            stream: 是否使用流式输出
            
        Returns:
            翻译结果
        """
        try:
            prompt = self._build_translation_prompt(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                element_type=element_type
            )
            
            response = self.client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional academic paper translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.DEEPSEEK_TEMPERATURE,
                max_tokens=settings.DEEPSEEK_MAX_TOKENS,
                stream=stream
            )
            
            if stream:
                # 流式输出
                translated_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        translated_text += chunk.choices[0].delta.content
                return translated_text
            else:
                # 非流式输出
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
        """
        异步翻译文本
        
        Args:
            text: 待翻译文本
            source_lang: 源语言
            target_lang: 目标语言
            context: 上下文类型
            task_id: 任务ID（用于日志）
            element_type: 元素类型
            
        Returns:
            翻译结果
        """
        try:
            prompt = self._build_translation_prompt(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                context=context,
                element_type=element_type
            )
            
            response = await self.async_client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional academic paper translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.DEEPSEEK_TEMPERATURE,
                max_tokens=settings.DEEPSEEK_MAX_TOKENS,
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
        """
        批量异步翻译（带并发控制）
        
        Args:
            texts: 待翻译文本列表，每项包含 {text, context, element_type, task_id}
            source_lang: 源语言
            target_lang: 目标语言
            max_concurrent: 最大并发数
            
        Returns:
            翻译结果列表
        """
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
        
        # 并发执行所有翻译任务
        tasks = [translate_with_semaphore(item) for item in texts]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试 DeepSeek API 连接
        
        Returns:
            测试结果
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=10
            )
            
            return {
                "success": True,
                "message": "DeepSeek API 连接正常",
                "model": settings.DEEPSEEK_MODEL,
                "response": response.choices[0].message.content
            }
        except Exception as e:
            logger.error(f"DeepSeek API 连接测试失败: {str(e)}")
            return {
                "success": False,
                "message": f"连接失败: {str(e)}"
            }
