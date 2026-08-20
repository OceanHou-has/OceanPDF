# ============================================================
# OceanPDF 一键打包脚本（后端 exe + Electron 安装包）
# 用法: 在项目根目录执行  .\packaging\build_all.ps1
# 产物: packaging\release\OceanPDF Setup x.x.x.exe
# ============================================================
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PackDir     = Join-Path $ProjectRoot "packaging"

# ---------- 第一步：打包后端 ----------
Write-Host "========== [1/3] 打包后端 (PyInstaller) ==========" -ForegroundColor Yellow
& (Join-Path $PackDir "build_backend.ps1")
if ($LASTEXITCODE -ne 0) { throw "后端打包失败" }

# ---------- 第二步：构建前端（Electron 主进程/预加载/渲染层） ----------
Write-Host "========== [2/3] 构建前端 (electron-vite) ==========" -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    npm run electron:build
    if ($LASTEXITCODE -ne 0) { throw "前端构建失败" }
}
finally {
    Pop-Location
}

# ---------- 第三步：electron-builder 生成安装包 ----------
Write-Host "========== [3/3] 生成安装包 (electron-builder) ==========" -ForegroundColor Yellow
# 国内镜像：避免从 GitHub 下载 Electron 发行包超时
if (-not $env:ELECTRON_MIRROR) {
    $env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
}
if (-not $env:ELECTRON_BUILDER_BINARIES_MIRROR) {
    $env:ELECTRON_BUILDER_BINARIES_MIRROR = "https://npmmirror.com/mirrors/electron-builder-binaries/"
}
Push-Location $FrontendDir
try {
    npx electron-builder --config (Join-Path $PackDir "electron-builder.yml")
    if ($LASTEXITCODE -ne 0) { throw "electron-builder 打包失败" }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "全部完成！安装包位于: $PackDir\release\" -ForegroundColor Green
Get-ChildItem (Join-Path $PackDir "release") -Filter *.exe | ForEach-Object {
    Write-Host ("  - {0}  ({1:N1} MB)" -f $_.Name, ($_.Length / 1MB)) -ForegroundColor Green
}
