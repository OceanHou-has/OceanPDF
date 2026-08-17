# PP-DocLayoutV2 服务安装指南

本文档详细说明如何在其他电脑上安装和配置 DPS 服务。

---

## 目录

1. [环境要求](#1-环境要求)
2. [安装步骤概览](#2-安装步骤概览)
3. [GPU 版本安装（推荐）](#3-gpu-版本安装推荐)
4. [CPU 版本安装](#4-cpu-版本安装)
5. [验证安装](#5-验证安装)
6. [启动服务](#6-启动服务)
7. [常见问题](#7-常见问题)

---

## 1. 环境要求

### 1.1 操作系统

- Windows 10/11（64位）
- Linux（Ubuntu 18.04+）
- macOS 10.14+

### 1.2 Python 版本

- **推荐版本**: Python 3.10 - 3.12
- **最低版本**: Python 3.8
- **最高支持**: Python 3.12

> 注意：Python 版本过高可能导致部分依赖不兼容，建议使用 Python 3.10 或 3.11。

### 1.3 GPU 版本额外要求（如需 GPU 加速）

| 组件 | 要求 |
|------|------|
| NVIDIA 显卡 | 计算能力 ≥ 7.0（如 RTX 20系列及以上） |
| NVIDIA 驱动 | 版本 ≥ 450.80+ |
| CUDA | 11.8 或 12.x |

**查看显卡计算能力**: https://developer.nvidia.com/cuda-gpus

**查看当前驱动版本**（Windows）:
```powershell
nvidia-smi
```

---

## 2. 安装步骤概览

```
1. 创建虚拟环境
2. 安装 PaddlePaddle（GPU 或 CPU 版本）
3. 安装其他依赖
4. 验证安装
5. 启动服务
```

---

## 3. GPU 版本安装（推荐）

### 3.1 创建虚拟环境

打开 PowerShell，进入 DPS 文件夹：

```powershell
cd G:\MY_Project\OceanPDF2.0-260101\OceanPDF2.0-260101\DPS
```

创建虚拟环境：

```powershell
python -m venv venv
```

激活虚拟环境：

```powershell
.\venv\Scripts\Activate.ps1
```

> 如果遇到执行策略错误，先运行：
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3.2 升级 pip

```powershell
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.3 安装 PaddlePaddle GPU 版本

根据你的 CUDA 版本选择对应命令：

#### CUDA 12.x（推荐，适用于较新显卡）

```powershell
pip install paddlepaddle-gpu -i https://mirror.baidu.com/pypi/simple
```

#### CUDA 11.8

```powershell
pip install paddlepaddle-gpu==3.0.0 -i https://mirror.baidu.com/pypi/simple
```

#### 指定 CUDA 版本安装

如果需要指定特定的 CUDA 版本，可以使用以下格式：

```powershell
# CUDA 12.3
pip install paddlepaddle-gpu==3.0.0 -i https://mirror.baidu.com/pypi/simple

# CUDA 11.8
pip install paddlepaddle-gaddle==3.0.0.post118 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
```

> **官方安装命令查询**: https://www.paddlepaddle.org.cn/install/quick

### 3.4 安装其他依赖

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.5 验证 GPU 安装

```powershell
python -c "import paddle; print('PaddlePaddle版本:', paddle.__version__); print('CUDA编译:', paddle.device.is_compiled_with_cuda()); print('GPU设备数:', paddle.device.cuda.device_count() if paddle.is_compiled_with_cuda() else 0)"
```

预期输出：
```
PaddlePaddle版本: 3.x.x
CUDA编译: True
GPU设备数: 1
```

---

## 4. CPU 版本安装

如果您的电脑没有 NVIDIA 显卡，或者只想使用 CPU 运行，请按以下步骤操作。

### 4.1 创建虚拟环境

```powershell
cd F:\你的项目路径\DPS
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4.2 升级 pip

```powershell
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4.3 安装 PaddlePaddle CPU 版本

```powershell
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
```

或者指定版本：

```powershell
pip install paddlepaddle==3.0.0 -i https://mirror.baidu.com/pypi/simple
```

### 4.4 安装其他依赖

```powershell
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4.5 验证 CPU 安装

```powershell
python -c "import paddle; print('PaddlePaddle版本:', paddle.__version__); print('CUDA编译:', paddle.device.is_compiled_with_cuda())"
```

预期输出：
```
PaddlePaddle版本: 3.x.x
CUDA编译: False
```

---

## 5. 验证安装

### 5.1 验证所有依赖

```powershell
python -c "
import paddle
import paddleocr
import fitz
import cv2
import fastapi
print('所有依赖导入成功！')
print(f'PaddlePaddle: {paddle.__version__}')
print(f'PaddleOCR: {paddleocr.__version__}')
"
```

### 5.2 验证模型下载

首次运行时，PaddleOCR 会自动下载所需模型。可以提前触发下载：

```powershell
python -c "
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch', use_angle_cls=True)
print('OCR模型下载/加载成功！')
"
```

---

## 6. 启动服务

### 6.1 基本启动

```powershell
.\venv\Scripts\python .\pp_doclayoutv2_api_new.py --host 127.0.0.1 --port 8001
```

### 6.2 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 服务监听地址 | 127.0.0.1 |
| `--port` | 服务监听端口 | 8001 |

### 6.3 外网访问

如需允许其他设备访问，使用：

```powershell
.\venv\Scripts\python .\pp_doclayoutv2_api_new.py --host 0.0.0.0 --port 8001
```

### 6.4 验证服务运行

服务启动后，访问 http://127.0.0.1:8001/health 应返回：

```json
{
  "status": "ok",
  "layout_model_loaded": true,
  "ocr_model_loaded": true,
  ...
}
```

---

## 7. 常见问题

### 7.1 DLL 加载失败（Windows）

**错误信息**:
```
Could not locate cublasLt64_13.dll. Please make sure it is in your library path!
```

**原因**: Windows 无法找到 CUDA 相关的 DLL 文件。

**解决方案**: 代码中已包含自动修复逻辑，会自动将虚拟环境中的 CUDA DLL 路径添加到系统 PATH。如果仍有问题，可以手动安装 CUDA Toolkit：

1. 下载 CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
2. 安装后重启电脑
3. 确保 `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin` 在系统 PATH 中

### 7.2 GPU 内存不足

**错误信息**:
```
OutOfMemoryError: CUDA out of memory
```

**解决方案**:
- 减小处理的 PDF 页数
- 降低图像分辨率（修改 `render_zoom` 参数）
- 使用 CPU 版本

### 7.3 模型下载失败

**错误信息**:
```
Failed to download model...
```

**解决方案**:

1. 检查网络连接
2. 设置代理（如需要）:
   ```powershell
   set HTTP_PROXY=http://127.0.0.1:7890
   set HTTPS_PROXY=http://127.0.0.1:7890
   ```
3. 手动下载模型到 `C:\Users\你的用户名\.paddlex\official_models\`

### 7.4 Python 版本不兼容

**错误信息**:
```
No matching distribution found for paddlepaddle
```

**解决方案**:
- 确保使用 Python 3.8-3.12
- 创建新的虚拟环境并指定 Python 版本:
  ```powershell
  py -3.10 -m venv venv
  ```

### 7.5 pip 安装超时

**解决方案**: 使用国内镜像源：

```powershell
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 7.6 虚拟环境激活失败（PowerShell）

**错误信息**:
```
.\venv\Scripts\Activate.ps1 : 无法加载文件...因为在此系统上禁止运行脚本
```

**解决方案**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新激活虚拟环境。

### 7.7 如何切换 GPU/CPU 模式

服务会自动检测并使用 GPU。如需强制使用 CPU：

修改 `core/config.py` 中的 `device` 配置，或在启动时设置环境变量：

```powershell
$env:CUDA_VISIBLE_DEVICES="-1"
.\venv\Scripts\python .\pp_doclayoutv2_api_new.py --host 127.0.0.1 --port 8001
```

---

## 附录：完整安装命令速查

### GPU 版本（一键安装）

```powershell
cd DPS目录
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddlepaddle-gpu -i https://mirror.baidu.com/pypi/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### CPU 版本（一键安装）

```powershell
cd DPS目录
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 技术支持

- PaddlePaddle 官方文档: https://www.paddlepaddle.org.cn/documentation/docs/zh/guides/index_cn.html
- PaddleOCR 官方仓库: https://github.com/PaddlePaddle/PaddleOCR
- 问题反馈: 请联系项目维护者
