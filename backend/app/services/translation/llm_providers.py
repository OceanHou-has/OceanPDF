"""
LLM 厂商注册表
统一管理主流大模型厂商的 OpenAI 兼容接口配置（base_url / 预置模型）
所有厂商均通过 OpenAI 兼容协议接入，便于扩展
"""
from typing import Dict, List, Optional, Any

# 厂商注册表：新增厂商只需在此追加即可
LLM_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "emoji": "🐳",
        "description": "深度求索，学术翻译性价比高（V4 系列）",
        "default_base_url": "https://api.deepseek.com",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro"],
        "default_model": "deepseek-v4-flash",
        "allow_custom_model": True,
        "key_placeholder": "输入 DeepSeek API 密钥（sk-...）",
        "key_url": "https://platform.deepseek.com/api_keys",
    },
    {
        "id": "qwen",
        "name": "通义千问 (Qwen)",
        "emoji": "☁️",
        "description": "阿里云百炼 DashScope 兼容模式",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen3.7-max", "qwen3.7-plus", "qwen3.7-flash", "qwen-max", "qwen-plus", "qwen-turbo"],
        "default_model": "qwen-plus",
        "allow_custom_model": True,
        "key_placeholder": "输入阿里云百炼 API 密钥（sk-...）",
        "key_url": "https://bailian.console.aliyun.com/",
    },
    {
        "id": "doubao",
        "name": "豆包 (Doubao)",
        "emoji": "🌱",
        "description": "火山引擎方舟平台，模型名可填推理接入点 ID（ep-...）",
        "default_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "models": ["doubao-seed-2.1-pro", "doubao-seed-2.1-turbo", "doubao-seed-evolving"],
        "default_model": "doubao-seed-2.1-pro",
        "allow_custom_model": True,
        "key_placeholder": "输入火山方舟 API Key",
        "key_url": "https://console.volcengine.com/ark",
    },
    {
        "id": "google",
        "name": "Google Gemini",
        "emoji": "✨",
        "description": "通过 Gemini OpenAI 兼容端点接入（可能需要代理）",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
        "default_model": "gemini-3.5-flash",
        "allow_custom_model": True,
        "key_placeholder": "输入 Google AI Studio API Key",
        "key_url": "https://aistudio.google.com/apikey",
    },
    {
        "id": "openai",
        "name": "OpenAI (GPT)",
        "emoji": "🤖",
        "description": "OpenAI 官方接口（可能需要代理）",
        "default_base_url": "https://api.openai.com/v1",
        "models": ["gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.5", "gpt-4o"],
        "default_model": "gpt-5.6-terra",
        "allow_custom_model": True,
        "key_placeholder": "输入 OpenAI API Key（sk-...）",
        "key_url": "https://platform.openai.com/api-keys",
    },
    {
        "id": "moonshot",
        "name": "Moonshot (Kimi)",
        "emoji": "🌙",
        "description": "月之暗面 Kimi 开放平台",
        "default_base_url": "https://api.moonshot.cn/v1",
        "models": ["kimi-k3", "kimi-k2.6", "kimi-k2.7-code", "kimi-k2.7-code-highspeed"],
        "default_model": "kimi-k3",
        "allow_custom_model": True,
        "key_placeholder": "输入 Moonshot API Key",
        "key_url": "https://platform.moonshot.cn/",
    },
    {
        "id": "zhipu",
        "name": "智谱 GLM",
        "emoji": "🧠",
        "description": "智谱 AI 开放平台",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-5.3", "glm-5.2", "glm-5.1-highspeed", "glm-4-plus", "glm-4-flash"],
        "default_model": "glm-5.3",
        "allow_custom_model": True,
        "key_placeholder": "输入智谱 API Key",
        "key_url": "https://open.bigmodel.cn/",
    },
    {
        "id": "custom",
        "name": "自定义 (OpenAI 兼容)",
        "emoji": "🛠️",
        "description": "任意 OpenAI 兼容服务（如 Ollama、OneAPI、中转站等）",
        "default_base_url": "",
        "models": [],
        "default_model": "",
        "allow_custom_model": True,
        "key_placeholder": "输入该服务的 API Key（本地服务可填任意值）",
        "key_url": "",
    },
]


def get_providers() -> List[Dict[str, Any]]:
    """返回完整厂商列表（供前端渲染）"""
    return LLM_PROVIDERS


def get_provider(provider_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """按 id 获取厂商配置"""
    if not provider_id:
        return None
    for p in LLM_PROVIDERS:
        if p["id"] == provider_id:
            return p
    return None
