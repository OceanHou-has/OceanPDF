# -*- mode: python ; coding: utf-8 -*-
"""
OceanPDF 后端 PyInstaller 打包配置
用法（构建脚本会自动执行）：
    cd backend
    .\.venv\Scripts\pyinstaller ..\packaging\backend.spec --noconfirm

产物：packaging/output/backend/OceanPDFBackend.exe（onedir 模式）
"""
from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()          # packaging/
PROJECT_ROOT = SPEC_DIR.parent               # 项目根目录
BACKEND_DIR = PROJECT_ROOT / "backend"       # backend/
OUTPUT_DIR = SPEC_DIR / "output"             # packaging/output

a = Analysis(
    [str(SPEC_DIR / "backend_entry.py")],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=[
        # 双语导出所需中文字体（font_manager.py 通过 __file__ 相对路径查找）
        (str(BACKEND_DIR / "app" / "services" / "pdf_export" / "fonts"),
         "app/services/pdf_export/fonts"),
    ],
    hiddenimports=[
        # uvicorn 按需动态导入的模块，必须显式声明
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # FastAPI multipart 表单解析
        "python_multipart",
        "multipart",
        "multipart.multipart",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 明确不打包的重型库（项目未使用或已剥离）
        "sqlalchemy",
        "torch",
        "paddle",
        "paddleocr",
        "paddlex",
        "matplotlib",
        "numpy.testing",
        "tkinter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OceanPDFBackend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # 保留控制台便于排错；Electron 生产环境以 stdio ignore 方式拉起
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="backend",
)

# 输出目录通过构建脚本的 --distpath / --workpath 参数指定（packaging/output）
