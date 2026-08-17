# OceanPDF 2.0 - 桌面端PDF论文翻译软件

<div align="center">

**智能PDF翻译 · 双语对照排版 · 桌面端应用**

</div>

## 项目简介

OceanPDF 2.0 是一款功能强大的桌面端PDF论文翻译软件，支持PDF文档的智能解析、AI翻译和双语对照排版。

### 核心功能

- 📄 **智能PDF解析** - 基于PP-DocLayoutV2的版面分析、OCR识别、表格解析
- 🤖 **AI智能翻译** - 支持多种大模型API（OpenAI、Claude等）
- 📑 **双语对照排版** - 生成专业的双语对照PDF文档
- 💻 **桌面端应用** - 基于Electron的跨平台桌面应用
- 📊 **任务管理** - 实时进度追踪、任务历史记录

## 技术架构

### 前端技术栈
- Vue 3 + Vite
- Element Plus UI组件库
- Pinia状态管理
- Axios HTTP客户端

### 后端架构（微服务）
- **主后端服务** (端口8000) - FastAPI + SQLAlchemy
- **DPS文档解析服务** (端口8001) - PaddlePaddle + PaddleOCR
- **PDF生成服务** - PyMuPDF + ReportLab

## 项目结构

```
OceanPDF2.0/
├── frontend/           # Electron + Vue前端
│   ├── src/
│   │   ├── main/      # Electron主进程
│   │   ├── renderer/  # Vue渲染进程
│   │   └── preload/   # 预加载脚本
│   └── package.json
├── backend/           # 主后端服务
│   ├── app/
│   │   ├── api/      # API路由
│   │   ├── core/     # 核心配置
│   │   ├── models/   # 数据模型
│   │   ├── services/ # 业务逻辑
│   │   └── utils/    # 工具函数
│   └── requirements.txt
└── DPS/               # DPS文档解析服务
    ├── core/         # 核心配置
    ├── services/     # 业务逻辑
    ├── utils/        # 工具函数
    ├── pp_doclayoutv2_api_new.py
    └── requirements.txt
```

## 快速开始

### 环境要求

- **Python**: 3.12（推荐）
- **Node.js**: 18.0+
- **npm**: 9.0+

### 1. DPS文档解析服务 (CPU版)

DPS服务负责PDF文档的智能解析，包括版面分析、OCR识别等功能。

```powershell
# 1. 进入DPS目录
cd DPS

# 2. 创建Python 3.12虚拟环境
py -3.12 -m venv venv

# 3. 激活虚拟环境
.\venv\Scripts\activate

# 4. 升级pip
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 安装PaddlePaddle CPU版本
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 安装其他依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 7. 启动DPS服务（端口8001）
.\venv\Scripts\python .\pp_doclayoutv2_api_new.py --host 127.0.0.1 --port 8001
```

> **注意**：
> - 首次启动时，PaddleOCR会自动下载所需模型（约几百MB），请确保网络畅通
> - 如需GPU加速，请参考 `DPS/INSTALL.md` 安装GPU版本
> - 模型会缓存到 `C:\Users\你的用户名\.paddlex\official_models\` 目录

**验证DPS服务**：
访问 http://127.0.0.1:8001/health 检查服务状态

### 2. 后端服务

```powershell
# 1. 确保系统已安装 Python 3.12
py --list
# 若没有安装Python 3.12，执行以下命令安装
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements

# 2. 创建虚拟环境
cd backend
py -3.12 -m venv .venv

# 3. 激活并安装依赖
.\.venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 启动后端（端口8000）
uvicorn app.main:app --reload --port 8000
```

**验证后端服务**：
访问 http://127.0.0.1:8000/docs 查看API文档

### 3. 前端服务

```bash
# 1. 安装依赖
cd frontend
npm install --registry=https://registry.npmmirror.com/

# 2. 启动开发服务器
npm run dev
```

前端服务将运行在 http://localhost:5173

## 服务端口说明

| 服务 | 端口 | 地址 |
|------|------|------|
| 前端应用 | 5173 | http://localhost:5173 |
| 后端API | 8000 | http://127.0.0.1:8000 |
| DPS文档解析 | 8001 | http://127.0.0.1:8001 |

## 依赖版本

### DPS服务关键依赖
- PaddlePaddle: 3.3.1 (CPU版本)
- PaddleOCR: 3.4.0
- FastAPI: 0.109.0
- PyMuPDF: 1.23.8

### 后端服务关键依赖
- FastAPI: 0.109.0
- Uvicorn: 0.27.0
- SQLAlchemy: 2.0.25
- PyMuPDF: 1.23.8

### 前端应用关键依赖
- Vue: 3.4.0
- Vite: 5.4.21
- Element Plus: 2.5.3

## 常见问题

### DPS服务相关问题

**Q: 模型下载失败怎么办？**
A: 可以设置代理或手动下载模型到 `C:\Users\你的用户名\.paddlex\official_models\` 目录

**Q: 如何切换到GPU版本？**
A: 请参考 `DPS/INSTALL.md` 文档安装GPU版本的PaddlePaddle

**Q: 虚拟环境激活失败（PowerShell）？**
A: 如果提示"无法加载文件"，运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 通用问题

**Q: Python版本不兼容？**
A: 确保使用Python 3.10-3.12版本，推荐3.12

**Q: npm安装速度慢？**
A: 使用国内镜像源：`npm config set registry https://registry.npmmirror.com/`

## 更多文档

- [DPS服务详细安装指南](DPS/INSTALL.md)
- [大模型API配置说明](docs/LLM_CONFIG.md) (待完善)

## 技术支持

- PaddlePaddle官方文档: https://www.paddlepaddle.org.cn/documentation/docs/zh/guides/index_cn.html
- PaddleOCR官方仓库: https://github.com/PaddlePaddle/PaddleOCR
- FastAPI官方文档: https://fastapi.tiangolo.com/zh/

---

**注意事项**：
- 大模型API需要自行申请和配置（OpenAI、Claude等）
- 首次运行建议先测试各服务是否正常启动
- 使用虚拟环境可以隔离项目依赖，避免版本冲突
