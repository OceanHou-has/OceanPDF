"""
PP-DocLayoutV2 FastAPI 服务 - 模块化版本
支持版面分析和OCR识别，优化启动速度
"""
import argparse
import os
import platform
import sys
import time

if sys.platform == "win32":
    import ctypes
    venv_site_packages = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", "Lib", "site-packages"))
    cuda_dll_path = os.path.join(venv_site_packages, "nvidia", "cu13", "bin", "x86_64")
    if os.path.exists(cuda_dll_path):
        os.add_dll_directory(cuda_dll_path)
        os.environ["PATH"] = cuda_dll_path + os.pathsep + os.environ.get("PATH", "")
        print(f"[DLL路径] 已添加CUDA DLL目录: {cuda_dll_path}")
        dll_files = [
            "cudart64_13.dll",
            "cublas64_13.dll",
            "cublasLt64_13.dll",
            "cufft64_12.dll",
            "curand64_10.dll",
            "cusparse64_12.dll",
            "cusolver64_12.dll",
        ]
        for dll_name in dll_files:
            dll_full_path = os.path.join(cuda_dll_path, dll_name)
            if os.path.exists(dll_full_path):
                try:
                    ctypes.CDLL(dll_full_path)
                    print(f"[DLL预加载] 成功: {dll_name}")
                except Exception as e:
                    print(f"[DLL预加载] 失败: {dll_name}, 错误: {e}")

from fastapi import FastAPI, File, HTTPException, UploadFile

# 导入模块
from core.logger import log_kv
from core.config import config
from core.model_loader import model_loader
from services.layout_service import LayoutService
from services.ocr_service import OCRService
from utils.import_utils import try_import_paddle, try_import_paddleocr_pkg


app = FastAPI(title="PP-DocLayoutV2 API", version="2.0.0")


@app.on_event("startup")
def startup():
    """服务启动事件"""
    log_kv("服务启动", {"python": sys.version.replace("\n", " "), "exe": sys.executable})
    log_kv("平台", f"{platform.platform()} | {platform.machine()}")
    
    # 显示依赖版本信息
    paddle = try_import_paddle()
    if paddle is not None:
        log_kv("paddle 版本", getattr(paddle, "__version__", None))
        log_kv("是否编译 CUDA", bool(paddle.is_compiled_with_cuda()))
        if bool(paddle.is_compiled_with_cuda()):
            log_kv("CUDA 设备数", paddle.device.cuda.device_count())
    
    paddleocr_pkg = try_import_paddleocr_pkg()
    if paddleocr_pkg is not None:
        log_kv("paddleocr 版本", getattr(paddleocr_pkg, "__version__", None))
    
    # 显示配置信息
    log_kv("配置", {
        "device": config.device,
        "layout_enabled": config.layout_enabled,
        "ocr_enabled": config.ocr_enabled,
        "lazy_load": config.lazy_load,
        "render_zoom": config.render_zoom,
    })
    
    # 加载模型
    if config.lazy_load:
        log_kv("启用懒加载模式", {"说明": "模型将在首次请求时加载"})
    else:
        model_loader.load_models_parallel()


@app.get("/health")
def health():
    """健康检查"""
    paddle = try_import_paddle()
    paddleocr_pkg = try_import_paddleocr_pkg()
    
    # 判断模型状态
    layout_loaded = model_loader._layout_model is not None
    ocr_loaded = model_loader._ocr_model is not None
    
    return {
        "status": "ok",
        "layout_model_loaded": layout_loaded,
        "ocr_model_loaded": ocr_loaded,
        # 主后端需要的状态字段（对象结构）
        "layout_status": {
            "status": "ready" if layout_loaded else "not_loaded"
        },
        "ocr_status": {
            "status": "ready" if ocr_loaded else "not_loaded"
        },
        "paddle_version": getattr(paddle, "__version__", None) if paddle is not None else None,
        "paddleocr_version": getattr(paddleocr_pkg, "__version__", None) if paddleocr_pkg is not None else None,
        "cuda_compiled": bool(paddle.is_compiled_with_cuda()) if paddle is not None else None,
        "default_device": config.device,
        "layout_model_type": type(model_loader._layout_model).__name__ if model_loader._layout_model is not None else None,
        "ocr_model_type": type(model_loader._ocr_model).__name__ if model_loader._ocr_model is not None else None,
        "lazy_load_enabled": config.lazy_load,
        "config": {
            "layout_enabled": config.layout_enabled,
            "ocr_enabled": config.ocr_enabled,
            "device": config.device,
            "render_zoom": config.render_zoom,
        }
    }


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    with_ocr: bool = False,
    ocr_min_conf: float = 0.0,
    ocr_return_regions: bool = False,
):
    """版面分析接口（可选附带OCR）
    
    参数：
        file: PDF文件
        with_ocr: 是否附带OCR识别（默认False）
        ocr_min_conf: OCR最低置信度阈值（默认0.0）
        ocr_return_regions: 是否返回OCR文本区域详情（默认False）
    """
    # 确保模型已加载
    if model_loader.layout_model is None:
        try:
            model_loader._ensure_layout_loaded()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"模型加载失败: {str(e)}")
    
    if model_loader.layout_model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    # 如果需要OCR，确俜OCR模型已加载
    if with_ocr:
        if model_loader.ocr_model is None:
            try:
                model_loader._ensure_ocr_loaded()
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"OCR 模型加载失败: {str(e)}")
    
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持上传 .pdf 文件")
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    
    req_id = f"{int(time.time() * 1000)}_{os.getpid()}"
    log_kv("收到版面分析请求", {
        "req_id": req_id,
        "filename": file.filename,
        "bytes": len(content),
        "with_ocr": with_ocr,
        "ocr_min_conf": ocr_min_conf,
    })
    
    try:
        result = LayoutService.analyze_pdf(
            content, 
            file.filename, 
            req_id,
            with_ocr=with_ocr,
            ocr_min_conf=ocr_min_conf,
            ocr_return_regions=ocr_return_regions,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        log_kv("版面分析请求失败", {"req_id": req_id, "err": repr(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr")
async def ocr_recognize(file: UploadFile = File(...)):
    """OCR 文字识别接口
    
    支持的文件格式：图片（jpg, jpeg, png, bmp）或 PDF
    """
    # 确保模型已加载
    if model_loader.ocr_model is None:
        try:
            model_loader._ensure_ocr_loaded()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"OCR 模型加载失败: {str(e)}")
    
    if model_loader.ocr_model is None:
        raise HTTPException(status_code=503, detail="OCR 模型未加载")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")
    
    # 检查文件格式
    supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".pdf"]
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 {file_ext}，支持的格式：{', '.join(supported_formats)}",
        )
    
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="空文件")
    
    req_id = f"{int(time.time() * 1000)}_{os.getpid()}"
    log_kv("收到 OCR 请求", {"req_id": req_id, "filename": file.filename, "bytes": len(content)})
    
    try:
        result = OCRService.recognize(content, file.filename, file_ext, req_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        log_kv("OCR 请求失败", {"req_id": req_id, "err": repr(e)})
        raise HTTPException(status_code=500, detail=str(e))


def build_argparser():
    """构建命令行参数解析器"""
    p = argparse.ArgumentParser(prog="pp_doclayoutv2_api_new.py", description="PP-DocLayoutV2 FastAPI 服务（模块化版本）")
    p.add_argument("--host", default="127.0.0.1", help="监听主机地址")
    p.add_argument("--port", type=int, default=8001, help="监听端口")
    p.add_argument("--reload", default="false", help="是否启用热重载")
    return p


def parse_bool(s: str) -> bool:
    """解析布尔值"""
    v = (s or "").strip().lower()
    return v in ("1", "true", "yes", "y", "t")


def main():
    """主函数"""
    args = build_argparser().parse_args()
    
    try:
        import uvicorn
    except ImportError:
        print("错误: 未安装 uvicorn，请运行: pip install uvicorn")
        sys.exit(1)
    
    uvicorn.run(
        "pp_doclayoutv2_api_new:app",
        host=args.host,
        port=args.port,
        reload=parse_bool(args.reload),
        log_level="info",
    )


if __name__ == "__main__":
    main()
