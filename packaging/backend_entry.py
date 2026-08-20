"""
OceanPDF 后端 PyInstaller 打包入口
==================================
此文件仅用于打包，不影响 backend/ 下任何源码。

作用：
1. 将工作目录切换到"数据目录"（backend 中所有 storage/、logs/ 均为相对路径，
   依赖 CWD；打包后的 exe 通常位于只读目录，必须切换到可写目录）
2. 以编程方式启动 uvicorn 运行 FastAPI 应用

数据目录优先级：
    环境变量 OCEANPDF_DATA_DIR > backend/storage 目录（开发调试） > %APPDATA%/OceanPDF
"""
import os
import sys
from pathlib import Path

API_HOST = "127.0.0.1"
API_PORT = 8000


def _is_frozen() -> bool:
    """是否运行在 PyInstaller 打包后的环境"""
    return getattr(sys, "frozen", False)


def _resolve_data_dir() -> Path:
    # 1. 环境变量显式指定
    env_dir = os.environ.get("OCEANPDF_DATA_DIR")
    if env_dir:
        return Path(env_dir)

    # 2. 开发调试模式（python packaging/backend_entry.py 直接运行）：
    #    本文件位于 <项目根>/packaging/，复用 backend/storage 作为数据目录
    if not _is_frozen():
        dev_dir = Path(__file__).resolve().parent.parent / "backend" / "storage"
        if dev_dir.parent.exists():
            return dev_dir

    # 3. 打包后的默认位置：用户目录下 %APPDATA%/OceanPDF
    return Path(os.environ.get("APPDATA", str(Path.home()))) / "OceanPDF"


def main() -> None:
    # PyInstaller 在 Windows 下必须调用 freeze_support
    import multiprocessing
    multiprocessing.freeze_support()

    data_dir = _resolve_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)
    # backend 代码中大量使用 Path("storage/...")、"logs/app.log" 相对路径
    os.chdir(data_dir)

    # 把 backend 目录加入模块搜索路径（打包分析阶段与开发调试阶段都需要）
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    if backend_dir.exists():
        sys.path.insert(0, str(backend_dir))

    print(f"[OceanPDF] data dir: {data_dir}")
    print(f"[OceanPDF] serving on http://{API_HOST}:{API_PORT}")

    import uvicorn
    from app.main import app  # noqa: E402  (必须在 chdir / sys.path 处理之后导入)

    config = uvicorn.Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
        loop="asyncio",
    )
    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()
