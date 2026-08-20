# ============================================================
# OceanPDF 后端打包脚本（PyInstaller）
# 用法: 在项目根目录执行  .\packaging\build_backend.ps1
# 产物: packaging\output\backend\OceanPDFBackend.exe
# ============================================================
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot          # 项目根目录
$BackendDir  = Join-Path $ProjectRoot "backend"
$PackDir     = Join-Path $ProjectRoot "packaging"
$OutDir      = Join-Path $PackDir "output"
$PyExe       = Join-Path $BackendDir ".venv\Scripts\python.exe"
$Installer   = Join-Path $BackendDir ".venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $PyExe)) {
    Write-Error "未找到后端虚拟环境: $PyExe，请先按 README 安装后端依赖"
    exit 1
}

# 1. 确保 pyinstaller 已安装（装在 backend 的 venv 里，不影响全局环境）
if (-not (Test-Path $Installer)) {
    Write-Host "[1/3] 安装 PyInstaller 到 backend 虚拟环境..." -ForegroundColor Cyan
    & $PyExe -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
} else {
    Write-Host "[1/3] PyInstaller 已存在，跳过安装" -ForegroundColor Cyan
}

# 2. 执行打包（在 backend 目录下运行，保证 app 包可被正确解析）
Write-Host "[2/3] 开始 PyInstaller 打包..." -ForegroundColor Cyan
Push-Location $BackendDir
try {
    & $Installer "..\packaging\backend.spec" --noconfirm `
        --distpath "$OutDir" `
        --workpath "$OutDir\pyinstaller_build"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller 打包失败 (exit=$LASTEXITCODE)" }
}
finally {
    Pop-Location
}

# 3. 简单验证产物
$Exe = Join-Path $OutDir "backend\OceanPDFBackend.exe"
if (Test-Path $Exe) {
    $size = [math]::Round((Get-ChildItem (Join-Path $OutDir "backend") -Recurse |
             Measure-Object Length -Sum).Sum / 1MB, 1)
    Write-Host "[3/3] 打包成功: $Exe （backend 目录共 ${size} MB）" -ForegroundColor Green
} else {
    Write-Error "未找到产物: $Exe"
    exit 1
}
