"""模型加载器模块"""
import os
import re
import threading
import time
from typing import Optional, Any

from core.logger import log_kv
from core.config import config
from utils.env_utils import bool_from_env, env_get_str, env_get_int, env_get_float
from utils.import_utils import try_import_paddle


class ModelLoader:
    """模型加载器，支持懒加载和并行加载"""
    
    def __init__(self):
        self._layout_model: Optional[Any] = None
        self._ocr_model: Optional[Any] = None
        self._layout_lock = threading.Lock()
        self._ocr_lock = threading.Lock()
    
    @property
    def layout_model(self):
        """获取版面分析模型（支持懒加载）"""
        if self._layout_model is None and config.lazy_load:
            self._ensure_layout_loaded()
        return self._layout_model
    
    @property
    def ocr_model(self):
        """获取OCR模型（支持懒加载）"""
        if self._ocr_model is None and config.lazy_load:
            self._ensure_ocr_loaded()
        return self._ocr_model
    
    def load_models_parallel(self):
        """并行加载模型"""
        if not config.layout_enabled and not config.ocr_enabled:
            log_kv("所有模型已禁用", {})
            return
        
        t0 = time.time()
        threads = []
        errors = {}
        
        def _load_layout():
            try:
                log_kv("开始加载版面分析模型", {})
                t_start = time.time()
                self._layout_model = self._build_layout_model()
                log_kv("版面分析模型加载完成(秒)", round(time.time() - t_start, 3))
            except Exception as e:
                errors['layout'] = e
                log_kv("版面分析模型加载失败", repr(e))
        
        def _load_ocr():
            try:
                log_kv("开始加载 OCR 模型", {})
                t_start = time.time()
                self._ocr_model = self._build_ocr_model()
                log_kv("OCR 模型加载完成(秒)", round(time.time() - t_start, 3))
            except Exception as e:
                errors['ocr'] = e
                log_kv("OCR 模型加载失败", repr(e))
        
        if config.layout_enabled:
            t = threading.Thread(target=_load_layout, name="LoadLayoutModel")
            t.start()
            threads.append(t)
        else:
            log_kv("跳过版面分析模型加载", {})
        
        if config.ocr_enabled:
            t = threading.Thread(target=_load_ocr, name="LoadOCRModel")
            t.start()
            threads.append(t)
        else:
            log_kv("跳过 OCR 模型加载", {})
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        total_time = round(time.time() - t0, 3)
        log_kv("所有模型加载完成", {
            "总耗时(秒)": total_time,
            "版面分析模型": "已加载" if self._layout_model is not None else "未加载",
            "OCR模型": "已加载" if self._ocr_model is not None else "未加载",
            "失败数": len(errors)
        })
        
        if errors:
            log_kv("模型加载错误详情", errors)
    
    def _ensure_layout_loaded(self):
        """确保版面分析模型已加载（懒加载支持）"""
        if self._layout_model is not None:
            return
        
        with self._layout_lock:
            if self._layout_model is not None:  # 双重检查
                return
            
            if not config.layout_enabled:
                raise RuntimeError("版面分析模型已禁用")
            
            log_kv("懒加载：开始加载版面分析模型", {})
            t0 = time.time()
            self._layout_model = self._build_layout_model()
            log_kv("懒加载：版面分析模型加载完成(秒)", round(time.time() - t0, 3))
    
    def _ensure_ocr_loaded(self):
        """确保 OCR 模型已加载（懒加载支持）"""
        if self._ocr_model is not None:
            return
        
        with self._ocr_lock:
            if self._ocr_model is not None:  # 双重检查
                return
            
            if not config.ocr_enabled:
                raise RuntimeError("OCR 模型已禁用")
            
            log_kv("懒加载：开始加载 OCR 模型", {})
            t0 = time.time()
            self._ocr_model = self._build_ocr_model()
            log_kv("懒加载：OCR 模型加载完成(秒)", round(time.time() - t0, 3))
    
    def _build_layout_model(self):
        """构建版面分析模型"""
        from utils.import_utils import try_import_paddleocr
        
        # 尝试导入 LayoutDetection (PaddleOCR 3.x)
        try:
            from paddleocr import LayoutDetection
        except Exception:
            LayoutDetection = None
        
        # 尝试导入 PPStructure (PaddleOCR 2.8.x)
        PPStructure = None
        if LayoutDetection is None:
            try:
                from paddleocr import PPStructure
            except Exception:
                pass
        
        if LayoutDetection is None and PPStructure is None:
            raise RuntimeError("paddleocr 未安装或不可用（缺少 LayoutDetection / PPStructure）")
        
        paddle = try_import_paddle()
        if paddle is None:
            raise RuntimeError("paddle 未安装或不可用")
        
        use_gpu = config.use_gpu
        if not bool(paddle.is_compiled_with_cuda()) and use_gpu:
            log_kv("GPU 不可用，自动降级到 CPU", {"requested": config.device, "use": "cpu"})
            use_gpu = False
        
        if LayoutDetection is not None:
            init_kwargs = {
                "model_name": config.model_name,
                "device": config.device if use_gpu else "cpu",
                "enable_hpi": bool_from_env("DOC_LAYOUT_ENABLE_HPI", False),
                "use_tensorrt": bool_from_env("DOC_LAYOUT_USE_TENSORRT", False),
            }
            log_kv("开始初始化版面分析模型(LayoutDetection)", {"model_name": config.model_name})
            try:
                return self._safe_init(LayoutDetection, init_kwargs)
            except Exception as e:
                log_kv("LayoutDetection 初始化失败，尝试回退 PPStructure", {"err": repr(e)})
        
        if PPStructure is None:
            raise RuntimeError("版面分析模型不可用：LayoutDetection 初始化失败且 PPStructure 不存在")
        
        init_kwargs = {
            "use_gpu": use_gpu,
            "layout": True,
            "table": False,
            "ocr": False,
            "device": config.device if use_gpu else "cpu",
        }
        log_kv("开始初始化版面分析模型(PPStructure)", {"model_name": config.model_name})
        return self._safe_init(PPStructure, init_kwargs)
    
    def _build_ocr_model(self):
        """构建 OCR 模型"""
        from utils.import_utils import try_import_paddleocr
        
        PaddleOCR = try_import_paddleocr()
        if PaddleOCR is None:
            raise RuntimeError("PaddleOCR 未安装或不可用")
        
        paddle = try_import_paddle()
        use_gpu = config.use_gpu
        
        if paddle is not None and not bool(paddle.is_compiled_with_cuda()) and use_gpu:
            log_kv("OCR GPU 不可用，自动降级到 CPU", {"requested": config.device, "use": "cpu"})
            use_gpu = False
        
        init_kwargs = {
            "lang": config.ocr_lang,
            "use_angle_cls": config.ocr_use_angle_cls,
            "use_gpu": use_gpu,
            "device": config.device if use_gpu else "cpu",
            "show_log": config.ocr_show_log,
            "enable_mkldnn": bool_from_env("OCR_ENABLE_MKLDNN", False),
        }
        
        # 添加可选参数
        ocr_version = env_get_str("OCR_VERSION")
        if ocr_version is not None:
            init_kwargs["ocr_version"] = ocr_version
        
        text_det_name = env_get_str("OCR_TEXT_DETECTION_MODEL_NAME")
        if text_det_name is not None:
            init_kwargs["text_detection_model_name"] = text_det_name
        
        text_rec_name = env_get_str("OCR_TEXT_RECOGNITION_MODEL_NAME")
        if text_rec_name is not None:
            init_kwargs["text_recognition_model_name"] = text_rec_name
        
        # 添加更多可选参数
        self._add_optional_ocr_params(init_kwargs)
        
        log_kv("开始初始化 OCR 模型", init_kwargs)
        return self._safe_init(PaddleOCR, init_kwargs)
    
    def _add_optional_ocr_params(self, init_kwargs: dict):
        """添加可选的 OCR 参数"""
        param_mappings = [
            ("OCR_USE_DOC_ORIENTATION_CLASSIFY", "use_doc_orientation_classify", bool_from_env),
            ("OCR_USE_DOC_UNWARPING", "use_doc_unwarping", bool_from_env),
            ("OCR_ENABLE_HPI", "enable_hpi", bool_from_env),
            ("OCR_USE_TENSORRT", "use_tensorrt", bool_from_env),
            ("OCR_PRECISION", "precision", env_get_str),
            ("OCR_LIMIT_SIDE_LEN", "limit_side_len", env_get_int),
            ("OCR_LIMIT_TYPE", "limit_type", env_get_str),
            ("OCR_DET_THRESH", "thresh", env_get_float),
            ("OCR_DET_BOX_THRESH", "box_thresh", env_get_float),
            ("OCR_DET_UNCLIP_RATIO", "unclip_ratio", env_get_float),
        ]
        
        for env_name, param_name, getter_func in param_mappings:
            if os.getenv(env_name) is not None:
                if getter_func == bool_from_env:
                    init_kwargs[param_name] = getter_func(env_name, False)
                else:
                    value = getter_func(env_name)
                    if value is not None:
                        init_kwargs[param_name] = value
        
        # 特殊处理 use_textline_orientation
        if os.getenv("OCR_USE_TEXTLINE_ORIENTATION") is not None:
            use_textline = bool_from_env("OCR_USE_TEXTLINE_ORIENTATION", False)
            if use_textline:
                if bool(init_kwargs.get("use_angle_cls")):
                    init_kwargs["use_angle_cls"] = False
                    log_kv("检测到互斥参数，已自动关闭 use_angle_cls", {
                        "use_angle_cls": False,
                        "use_textline_orientation": True
                    })
                init_kwargs["use_textline_orientation"] = True
    
    @staticmethod
    def _safe_init(cls, init_kwargs: dict):
        """安全初始化（自动移除不支持的参数）"""
        name = getattr(cls, "__name__", str(cls))
        kwargs = dict(init_kwargs or {})
        removed = []
        last_err = None
        
        for _ in range(len(kwargs) + 1):
            log_kv("模型初始化参数", {"class": name, "kwargs": kwargs, "removed": removed})
            try:
                return cls(**kwargs)
            except Exception as e:
                last_err = e
                msg = str(e) or repr(e)
                m = re.search(r"unexpected keyword argument ['\"]([^'\"]+)['\"]", msg)
                if not m:
                    m = re.search(r"Unknown argument:\s*([A-Za-z_][A-Za-z0-9_]*)", msg)
                bad_key = m.group(1) if m else None
                if bad_key and bad_key in kwargs:
                    kwargs.pop(bad_key, None)
                    removed.append(bad_key)
                    log_kv("移除不支持的初始化参数", {"class": name, "param": bad_key})
                    continue
                break
        
        if last_err is not None:
            raise last_err
        return cls(**kwargs)


# 全局模型加载器实例
model_loader = ModelLoader()
