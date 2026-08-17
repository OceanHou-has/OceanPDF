from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "OceanPDF Backend"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # 服务端口
    API_PORT: int = 8000
    MINERU_SERVICE_URL: str = "http://localhost:8001"
    DPS_SERVICE_URL: str = "http://127.0.0.1:8001"
    DPS_WITH_OCR: bool = True
    DPS_OCR_MIN_CONF: float = 0.0
    DPS_OCR_RETURN_REGIONS: bool = True
    DPS_HTTP_TIMEOUT_SEC: int = 600
    DPS_HEALTH_TIMEOUT_SEC: int = 120
    DPS_HEALTH_POLL_INTERVAL_SEC: float = 1.0
    
    # 文件存储
    UPLOAD_DIR: str = "storage/uploads"
    OUTPUT_DIR: str = "storage/outputs"
    TEMP_DIR: str = "storage/temp"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 数据库
    DATABASE_URL: str = "sqlite:///./oceanpdf.db"
    
    # 大模型API配置 (用户可配置)
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # deepseek-chat 或 deepseek-reasoner
    DEEPSEEK_TEMPERATURE: float = 0.3  # 翻译任务使用较低温度
    DEEPSEEK_MAX_TOKENS: int = 8192  # 单次请求最大token数
    DEEPSEEK_TIMEOUT: int = 180  # 请求超时时间（秒）
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
