"""配置管理模块"""
import os
from utils.env_utils import bool_from_env
from utils.import_utils import try_import_paddle


class AppConfig:
    """应用配置类"""
    
    def __init__(self):
        self.device = self._get_default_device()
        self.layout_enabled = bool_from_env("DOC_LAYOUT_ENABLED", True)
        self.ocr_enabled = bool_from_env("OCR_ENABLED", True)
        self.lazy_load = bool_from_env("MODEL_LAZY_LOAD", False)
        self.render_zoom = float(os.getenv("DOC_LAYOUT_RENDER_ZOOM", "2.0") or "2.0")
        self.layout_nms = bool_from_env("DOC_LAYOUT_NMS", True)
        self.model_name = os.getenv("DOC_LAYOUT_MODEL_NAME", "PP-DocLayoutV2") or "PP-DocLayoutV2"
        
        # OCR配置
        self.ocr_lang = os.getenv("OCR_LANG", "ch")
        self.ocr_use_angle_cls = bool_from_env("OCR_USE_ANGLE_CLS", True)
        self.ocr_show_log = bool_from_env("OCR_SHOW_LOG", False)
    
    def _get_default_device(self) -> str:
        """获取默认设备"""
        env_dev = os.getenv("DOC_LAYOUT_DEVICE")
        if env_dev:
            return env_dev
        paddle = try_import_paddle()
        if paddle is not None and bool(paddle.is_compiled_with_cuda()):
            return "gpu:0"
        return "cpu"
    
    @property
    def use_gpu(self) -> bool:
        """是否使用GPU"""
        return self.device.strip().lower().startswith("gpu")


# 全局配置实例
config = AppConfig()
