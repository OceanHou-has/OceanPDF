"""
文档解析服务注册表
统一管理外部文档解析API服务的配置元数据
"""
from typing import Dict, List, Any

# 文档解析服务注册表
DOCUMENT_PARSER_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "baidu",
        "name": "百度AI文档解析",
        "emoji": "📘",
        "description": "百度智能云文档解析，支持版面分析、表格识别、阅读顺序",
        "default_endpoint": "https://aip.baidubce.com",
        "key_url": "https://console.bce.baidu.com/ai/#/ai/ocr/overview/index",
        "config_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "type": "password",
                "placeholder": "输入百度 AI API Key",
                "required": True
            },
            {
                "key": "secret_key",
                "label": "Secret Key",
                "type": "password",
                "placeholder": "输入百度 AI Secret Key",
                "required": True
            }
        ]
    },
    {
        "id": "aliyun",
        "name": "阿里云文档智能",
        "emoji": "☁️",
        "description": "阿里云DocMind文档智能，支持版面分析、表格解析、公式识别",
        "default_endpoint": "https://docmind-api.cn-hangzhou.aliyuncs.com",
        "key_url": "https://ram.console.aliyun.com/manage/ak",
        "config_fields": [
            {
                "key": "access_key_id",
                "label": "AccessKey ID",
                "type": "password",
                "placeholder": "输入阿里云 AccessKey ID",
                "required": True
            },
            {
                "key": "access_key_secret",
                "label": "AccessKey Secret",
                "type": "password",
                "placeholder": "输入阿里云 AccessKey Secret",
                "required": True
            }
        ]
    },
    {
        "id": "tencent",
        "name": "腾讯云文档解析",
        "emoji": "🌐",
        "description": "腾讯云大模型文档解析，智能结构化文档内容",
        "default_endpoint": "https://es.tencentcloudapi.com",
        "key_url": "https://console.cloud.tencent.com/cam/capi",
        "config_fields": [
            {
                "key": "secret_id",
                "label": "SecretId",
                "type": "password",
                "placeholder": "输入腾讯云 SecretId",
                "required": True
            },
            {
                "key": "secret_key",
                "label": "SecretKey",
                "type": "password",
                "placeholder": "输入腾讯云 SecretKey",
                "required": True
            }
        ]
    },
    {
        "id": "huawei",
        "name": "华为云智能文档",
        "emoji": "🔴",
        "description": "华为云文字识别OCR，支持多版式文档版面分析",
        "default_endpoint": "https://ocr.cn-north-4.myhuaweicloud.com",
        "key_url": "https://console.huaweicloud.com/iam/?region=cn-north-4#/myCredential/accessKey",
        "config_fields": [
            {
                "key": "ak",
                "label": "Access Key (AK)",
                "type": "password",
                "placeholder": "输入华为云 AK",
                "required": True
            },
            {
                "key": "sk",
                "label": "Secret Key (SK)",
                "type": "password",
                "placeholder": "输入华为云 SK",
                "required": True
            },
            {
                "key": "endpoint",
                "label": "Endpoint (可选)",
                "type": "text",
                "placeholder": "https://ocr.cn-north-4.myhuaweicloud.com",
                "required": False
            }
        ]
    },
    {
        "id": "zhipu",
        "name": "智谱GLM-OCR",
        "emoji": "🧠",
        "description": "智谱AI文档解析，基于GLM-OCR模型的版面分析与文本提取",
        "default_endpoint": "https://open.bigmodel.cn/api/paas/v4",
        "key_url": "https://open.bigmodel.cn/usercenter/apikeys",
        "config_fields": [
            {
                "key": "api_key",
                "label": "API Key",
                "type": "password",
                "placeholder": "输入智谱 API Key",
                "required": True
            }
        ]
    },
    {
        "id": "textin",
        "name": "TextIn xParse",
        "emoji": "📄",
        "description": "合合信息TextIn文档解析，16种元素识别，百页PDF快至1.5秒",
        "default_endpoint": "https://api.textin.com",
        "key_url": "https://www.textin.com/console/dashboard/setting",
        "config_fields": [
            {
                "key": "app_id",
                "label": "App ID",
                "type": "text",
                "placeholder": "输入TextIn App ID",
                "required": True
            },
            {
                "key": "secret_code",
                "label": "Secret Code",
                "type": "password",
                "placeholder": "输入TextIn Secret Code",
                "required": True
            }
        ]
    }
]


def get_providers() -> List[Dict[str, Any]]:
    """获取所有文档解析服务注册表"""
    return DOCUMENT_PARSER_PROVIDERS


def get_provider(provider_id: str) -> Dict[str, Any] | None:
    """根据ID获取指定服务"""
    for p in DOCUMENT_PARSER_PROVIDERS:
        if p["id"] == provider_id:
            return p
    return None
