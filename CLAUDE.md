# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

OceanPDF 2.0 是一款桌面端 PDF 论文智能翻译工具：上传 PDF → 版面分析 + OCR 解析 → AI 翻译 → 双语对照排版导出。技术栈为 Electron + Vue 3 + Vite + Element Plus（前端）、FastAPI + PyMuPDF（后端）、PaddleOCR/PP-DocLayoutV2（独立的 DPS 解析微服务）。

三个进程分别监听不同端口：

| 服务 | 端口 | 说明 |
|:---|:---|:---|
| 前端 | 5173 | Vite 开发服务器（打包后用 hash 路由走 file://） |
| 后端 | 8000 | FastAPI 主服务 |
| DPS | 8001 | 版面分析 + OCR（PaddleOCR，可选，未启动则翻译/解析会失败） |

## 常用命令

详细启动步骤见仓库根目录 [命令.md](命令.md) 与 [README.md](README.md)。

**后端**（`backend/`，Python 3.12，虚拟环境 `.venv`）
```bash
cd backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

**前端**（`frontend/`，Node 18+）
```bash
cd frontend
npm install --registry=https://registry.npmmirror.com/
npm run dev        # Vite 开发
npm run build      # 生产构建（校验 SFC 能否编译的快速手段）
npm run electron:build  # electron-vite 打包
```

**DPS 解析服务**（`DPS/`，可选，需 GPU/CPU 的 paddlepaddle）
```powershell
cd DPS
.\venv\Scripts\python .\pp_doclayoutv2_api_new.py --host 127.0.0.1 --port 8001
```

本项目**没有自动化测试套件和 lint 配置**。后端改动可用 `python -m py_compile <file>` 做语法校验；前端改动用 `npm run build` 校验编译。

## 架构

### 后端（`backend/app/`）

分层：`api/` 是 FastAPI 路由（薄层，只做参数校验 + 调 service），`services/` 是业务逻辑，`core/config.py` 用 pydantic-settings 读配置（`.env`，大小写敏感）。所有路由以 `/api/v1` 为前缀，在 `main.py` 统一 `include_router`。

- **上传/解析链路**：`upload.py` → `pdf_parser.py`（PyMuPDF 行级解析）→ DPS 版面分析（`dps_service.py` / `document_parser/`，支持本地 DPS 与外部服务如智谱 GLM-OCR）→ 预标注（`annotation/`）+ 标题层级（`heading_hierarchy_service.py`）。
- **翻译链路**：`translation/` 下多个 service 协作（预翻译 → 分布式执行 → 状态持久化），支持 DeepSeek/OpenAI/Claude 等多厂商（`llm_providers.py`）。
- **导出**：`pdf_export/` 用 PyMuPDF + ReportLab 生成双语对照 PDF。
- **PDF 页面工具**：`pdf_tools.py`（合并/拆分/提取/删除/旋转/重排），API 在 `api/tools.py`，纯 PyMuPDF 实现，不依赖翻译链路。

### 文件存储（`backend/storage/`，相对路径硬编码于代码中）

- `storage/uploads/` 上传的原始 PDF，命名为 `{uuid}_{原名}.pdf`
- `storage/parsed/{短id}/parsed.json` 解析结果，短 id 与真实 PDF 名通过 `pdf_id_mapper.py` 双向映射（`get_or_create_id` / `get_name_by_id`）
- `storage/outputs/` 导出与工具产物（`tools/` 子目录为 PDF 工具输出）
- `storage/temp/` 临时文件

按 `pdf_name`（不含扩展名）定位上传文件时，用 `Path("storage/uploads").glob(f"*{pdf_name}.pdf")`。

### 前端（`frontend/src/renderer/`）

- `main.js` 全局注册了 Element Plus 全部图标，模板里 `<el-icon><Xxx /></el-icon>` 可直接用任意图标名。
- `Home.vue` 是主界面外壳：左侧导航用 `currentView` ref + `v-show` 切换（upload / parsed / tools / setting），**不通过 router**。标注、翻译、AI 问答等是独立 router 页面（`router/index.js`，hash 模式）。
- 视图在 `views/`，可复用组件在 `components/`（含 `dialogs/`），自定义按钮在 `elements/button/`。
- API 封装在 `api/`（`pdf.js`、`tools.js`），统一经 `utils/request.js`（axios 实例，baseURL `http://127.0.0.1:8000/api/v1`）。

### 关键约定

- **响应包装**：所有接口返回 `{code: 200, message, data}`。`request.js` 拦截器在 `code !== 200` 时 reject；前端读 `res.data`。
- **文件下载**：后端用 `FileResponse`，前端用 `document.createElement('a')` + `.click()` 触发下载（见 `PdfExportDialog.vue`、`Tools.vue`）。
- **硬编码地址**：前端 API 与 SSE 地址直接写死 `http://127.0.0.1:8000`，不要改成相对路径（Electron file:// 下无法解析）。
- 上传/翻译等耗时操作超时设得很长（如 30 分钟），新增长耗时接口时留意 timeout 设置。
