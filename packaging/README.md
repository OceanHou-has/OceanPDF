# OceanPDF 2.0 桌面端打包说明

本目录包含将 **frontend（Electron）+ backend（FastAPI）** 打包为 Windows 桌面应用的全部打包资产。
**不包含 DPS**（本地版面分析/OCR 模型服务），版面分析可改用已集成的云端解析服务。

## 目录结构

```
packaging/
├── backend_entry.py        # 后端 PyInstaller 打包入口（不改 backend 源码）
├── backend.spec            # PyInstaller 打包配置
├── build_backend.ps1       # 只打包后端
├── build_all.ps1           # 一键打包（后端 + 前端 + 安装包）
├── electron-builder.yml    # electron-builder 配置（独立于 package.json）
├── output/                 # 【产物，已 gitignore】后端 exe 与 PyInstaller 中间文件
└── release/                # 【产物，已 gitignore】最终安装包 OceanPDF Setup x.x.x.exe
```

与原项目的关系（对现有目录的改动已降到最低）：

| 位置 | 说明 |
|---|---|
| `frontend/electron.vite.config.js` | 新增。electron-vite 构建配置（项目原来缺少它，`npm run electron:build` 无法运行） |
| `frontend/src/main/index.js` | 修改。仅在**打包环境**（`app.isPackaged`）下拉起内置后端 exe 并做健康检查，开发模式行为不变；附带渲染层日志捕获（写入 `%APPDATA%\OceanPDF\renderer-debug.log`） |
| `frontend/src/renderer/router/index.js` | 修改。路由改为 `createWebHashHistory`（打包后页面走 `file://` 协议，history 模式会导致白屏） |
| `.gitignore` | 追加。忽略 `packaging/output/`、`packaging/release/`、`frontend/dist-electron/` 等产物 |

## 一键打包

```powershell
# 在项目根目录执行
.\packaging\build_all.ps1
```

产物：`packaging\release\OceanPDF Setup 2.0.0.exe`（NSIS 安装包，约 120~150 MB）

## 自动更新（GitHub Releases）

应用内置了基于 **electron-updater** 的自动更新：启动 15 秒后自动检查 GitHub Releases，
发现新版本时在主界面上方导航栏出现「新版本 vX.X.X」按钮（带红点提示），点击开始下载，
按钮变为下载进度，下载完成后按钮变为绿色「重启安装」，点击后自动退出并完成升级。
开发模式（`npm run electron:dev`）不会触发更新逻辑。

### 发版流程（每次发布新版）

1. 修改 `frontend/package.json` 的 `version`（例如 `2.0.1`），更新日志写在 GitHub Release 描述里
   （会展示在应用内更新弹窗中）。
2. 执行一键打包+发布（默认自动发布到 GitHub Releases）：

```powershell
.\packaging\build_all.ps1
```

electron-builder 会自动创建/更新 `v2.0.1` Release 并上传「exe + latest.yml + blockmap」三件套。
同一个版本重复执行会覆盖更新该 Release 的资产；只想本地打包不发版时加参数：
`.\packaging\build_all.ps1 -SkipPublish`。

### 配置 GitHub Token（一次性）

自动发布需要 electron-builder 以你的身份上传文件，在 PowerShell 里执行一次（把 token 换成你申请的，
权限勾选 `repo`），之后重开终端即永久生效，无需再手动设置：

```powershell
[Environment]::SetEnvironmentVariable("GH_TOKEN", "你的token", "User")
```

注意：token 以明文存在当前 Windows 用户的注册表环境变量里，等效于本机密码，不要提交到 git、
不要发给别人；如果是共用电脑建议改用 Windows 凭据管理器或每次执行时手动设置。

不想用 token 也可以手动发布：本地跑 `.\packaging\build_all.ps1 -SkipPublish`，然后到
GitHub Releases 页面手动新建 `v2.0.1` Release，把以下三个文件一起拖上去
（文件名按 `latest.yml` 里的写法，空格已规范化为连字符）：

- `packaging\release\OceanPDF-Setup-2.0.1.exe`
- `packaging\release\latest.yml`
- `packaging\release\OceanPDF-Setup-2.0.1.exe.blockmap`

> ⚠️ **关键**：electron-updater 靠 Release 里的 `latest.yml` 判断新版本。
> 如果手动往 GitHub Releases 拖 exe，**必须三件套一起传**，否则客户端永远检测不到更新。
> 且手动上传时文件名要按 `latest.yml` 里的 `path`/`url` 命名
> （electron-builder 会把空格规范化为连字符，如 `OceanPDF-Setup-2.0.0.exe`），否则下载 404。

### 自动更新注意事项

- **内置后端占用问题**：主进程在 `update:install` 时会先同步 `taskkill` 结束
  `OceanPDFBackend.exe` 再退出安装，否则新安装包覆盖 `resources/backend` 时文件被锁定。
  若之后发现更新安装失败，优先检查这一步。
- **未代码签名**：更新安装时会再次触发 Windows SmartScreen「未知发布者」提示，点「仍要运行」即可；
  建议后续补代码签名证书。
- **自定义安装目录**：`allowToChangeInstallationDirectory: true` 下用户改了安装路径时，
  建议装到自定义目录后实测一次更新。
- **国内网络**：GitHub Releases 下载在国内可能慢/失败；如需改善，可将 `publish` 换成
  `generic`（自建静态服务器）或给下载加代理。

## 分步打包 / 只重打某一部分

### 1. 只重打后端（修改了 backend/ 代码后）

```powershell
.\packaging\build_backend.ps1
```

- 自动把 PyInstaller 装进 `backend\.venv`（不影响全局 Python）
- 产物：`packaging\output\backend\OceanPDFBackend.exe`（onedir 模式，约 80 MB）
- 手工验证：双击运行该 exe，浏览器访问 `http://127.0.0.1:8000/health`

### 2. 只重打前端（修改了 frontend/ 代码后）

```powershell
cd frontend
npm run electron:build          # 产物 -> frontend/dist-electron/
```

### 3. 只重生成安装包（后端/前端产物都已就绪）

```powershell
cd frontend
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"   # 国内网络建议设置
$env:ELECTRON_BUILDER_BINARIES_MIRROR = "https://npmmirror.com/mirrors/electron-builder-binaries/"
npx electron-builder --config ..\packaging\electron-builder.yml
```

### 4. 快速迭代验证（改了前端不想每次重出安装包）

改完前端后不必每次都跑 electron-builder，可直接把新产物覆盖到 `win-unpacked` 里验证：

```powershell
cd frontend
npm run electron:build
$appDir = "..\packaging\release\win-unpacked\resources\app"
Remove-Item "$appDir\dist-electron" -Recurse -Force
Copy-Item -Recurse "dist-electron" "$appDir\dist-electron"
# 双击 ..\packaging\release\win-unpacked\OceanPDF.exe 验证
```

验证通过后再跑第 3 步正式出安装包。

## 运行原理（打包后）

1. Electron 主进程启动 → 检测 `app.isPackaged`
2. 拉起 `resources/backend/OceanPDFBackend.exe`（由 extraResources 注入）
3. 轮询 `http://127.0.0.1:8000/health` 直到就绪（最长 60 秒），再打开窗口
4. 应用退出时用 `taskkill /t /f` 清理后端进程树

后端数据目录（上传文件、解析结果、配置、日志）：

- 默认：`%APPDATA%\OceanPDF`（即 `C:\Users\<用户名>\AppData\Roaming\OceanPDF`）
- 可用环境变量 `OCEANPDF_DATA_DIR` 覆盖
- 卸载应用不会删除该目录的数据

## 打包产物结构约定（⚠️ 改构建配置前必读）

本次白屏问题的根本教训：**主进程加载页面/预加载脚本的路径与构建产物的目录结构是强绑定的**，改任何一边都必须同步另一边。

### 产物目录结构（`frontend/dist-electron/`）

```
dist-electron/
├── main.js                  # 主进程（ESM，对应 package.json 的 "main" 字段，文件名不能改）
├── preload/
│   └── index.cjs            # 预加载脚本（必须是 CJS + .cjs 扩展名）
└── renderer/
    ├── index.html           # 页面入口
    └── assets/              # JS/CSS/图片（index.html 中以相对路径 ./assets/... 引用）
```

### 三层路径契约（都在 `frontend/src/main/index.js`）

| 引用 | 代码 | 说明 |
|---|---|---|
| 页面 | `loadFile(join(__dirname, './renderer/index.html'))` | main.js 与 renderer/ 同级，用 `./` 而不是 `../` |
| preload | `join(__dirname, './preload/index.cjs')` | 同上 |
| 后端 exe | `join(process.resourcesPath, 'backend', 'OceanPDFBackend.exe')` | 对应 electron-builder.yml 的 extraResources `to: backend` |

### 不可变约束（违反任一条都会导致白屏/启动失败）

1. **主进程输出文件名必须是 `main.js`**（`electron.vite.config.js` 里 `entryFileNames: 'main.js'`），与 `package.json` 的 `"main"` 字段一致
2. **preload 必须是 CJS 格式且扩展名 `.cjs`**：package.json 有 `"type": "module"`，.js 会被当 ESM，而 Electron 沙箱模式要求 preload 为 CJS
3. **前端路由必须用 `createWebHashHistory`**：打包后页面走 `file://` 协议，history 模式无法解析路径 → Vue 挂载失败 → 白屏
4. **renderer 资源引用必须保持相对路径**（`./assets/...`）：若 vite base 改成 `/`，file:// 下全部 404 → 白屏
5. **electron-builder.yml 的 `files` 必须包含 `dist-electron/**/*`**，extraResources 的 `to:` 路径必须与主进程 `getBackendExePath()` 一致

## 打包后验证清单

每次出完安装包按顺序检查：

1. **端口先腾空**：确认 8000 没被开发后端占用（见下方"端口冲突判别"），否则验证结果不可信
2. 双击 `packaging\release\win-unpacked\OceanPDF.exe`，确认：
   - 界面正常渲染（左侧深色导航栏 + 上传面板，不是白屏）
   - 任务管理器里能看到 `OceanPDF.exe`（Electron，多个子进程）和 `OceanPDFBackend.exe`（内置后端）
3. 浏览器访问 `http://127.0.0.1:8000/health`，应返回 `{"code":200,..."status":"healthy"}`
4. 关闭应用后确认 `OceanPDFBackend.exe` 也随之退出（taskkill 清理生效）
5. 最后再运行 `OceanPDF Setup 2.0.0.exe` 完整安装一遍（如装过旧版先卸载）

### 端口冲突判别（容易误判为"验证通过"）

打包应用的内置后端若绑不上 8000，健康检查仍可能返回 200——因为请求打到了你本机正在跑的开发后端（`uvicorn app.main:app`）。判别方法：

```powershell
# 看 8000 端口被谁占用
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object { Get-Process -Id $_.OwningProcess }
```

- 进程名是 `OceanPDFBackend` → 内置后端正常接管 ✅
- 进程名是 `python` → 是你的开发后端，打包应用的后端实际没启动 ❌（先停开发后端再验证）

## 改动代码后的重新打包流程

| 改了什么 | 需要执行 |
|---|---|
| `backend/` 下任何 Python 代码 | `.\packaging\build_backend.ps1` → 再跑第 3 步 |
| `frontend/` 下任何 Vue/JS 代码 | 第 2 步 → 再跑第 3 步 |
| 两边都改了 | 直接 `.\packaging\build_all.ps1` |
| 新增 Python 第三方库 | `backend\.venv` 里 pip 安装 + 加入 requirements.txt，再重打后端；若是动态导入的库，可能需要在 `backend.spec` 的 `hiddenimports` 中补充 |
| 新增字体等资源 | 在 `backend.spec` 的 `datas` 中补充映射 |

## 已知限制

1. **端口固定 8000**：前端多处硬编码 `localhost:8000`，若端口被占用内置后端绑不上（窗口仍会打开但功能指向占用端口的服务），运行前先停掉占用 8000 的进程
2. **无 DPS**：本地版面分析/OCR 不可用，上传时请在解析服务下拉中选择云端服务（百度/阿里/腾讯/华为云/智谱/TextIn）；"DPS 预览"开关无数据属正常现象
3. **未代码签名**：首次运行会被 Windows SmartScreen 提示"未知发布者"，点"仍要运行"即可
4. **杀毒误报**：PyInstaller 产物偶发被 Defender 误报，如遇到可将安装目录加入白名单
5. **前端路由必须用 hash 模式**：打包后页面通过 `file://` 加载，若改回 `createWebHistory` 会白屏；同理 vite 构建产物的资源引用必须保持相对路径（`./assets/...`）

## 常见问题与踩坑记录

**Q: electron-builder 下载 Electron 超时（`wsarecv: connection attempt failed`）？**
设置镜像（build_all.ps1 已内置）：
```powershell
$env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_BUILDER_BINARIES_MIRROR="https://npmmirror.com/mirrors/electron-builder-binaries/"
```

**Q: 打包后应用打开是白屏？**
按概率排查：
1. 路由被改回 history 模式 → 改回 `createWebHashHistory`
2. 资源路径变成绝对路径 `/assets/...` → 保持 vite 相对路径输出
3. `loadFile` / preload 路径与产物结构不匹配（`./` vs `../`）→ 对照上面"三层路径契约"
4. 主进程输出文件名不是 `main.js` → 对照 `package.json` 的 `main` 字段

排查工具：`%APPDATA%\OceanPDF\renderer-debug.log`（主进程捕获的渲染层 console 输出与加载失败事件，每次启动都会写入）。

**Q: 报后端启动超时？**
先查端口是否被占用（见"端口冲突判别"）；再查 `%APPDATA%\OceanPDF\logs\app.log`；或手动运行安装目录下 `resources\backend\OceanPDFBackend.exe` 看控制台报错。

**Q: PyInstaller 报某个模块 not found？**
在 `backend.spec` 的 `hiddenimports` 列表中添加该模块名后重新打包。注意包名与导入名可能不同（如 pip 包 `python-multipart` 的导入名是 `multipart`，两个都写上无害）。

**Q: electron-vite 报 `index.html file is not found in /src/renderer directory`？**
本项目的 `index.html` 在 frontend 根目录而非默认的 `src/renderer/`，`frontend/electron.vite.config.js` 已配置 renderer `root: '.'` + 显式 `rollupOptions.input`。不要删这个配置文件。

**Q: PowerShell 里对 npm 命令用管道报错 `StandardOutputEncoding is only supported when standard output is redirected`？**
npm 是 shim 脚本，与 PowerShell 管道+编码设置冲突。不要 `npm run xxx | Select-Object -Last N`，直接执行或先 `Tee-Object` 写日志文件再读取。

**Q: electron-builder 报 spawn EPERM（app-builder.exe 无法启动）？**
瞬时权限/杀软拦截问题，重试一次通常即可；持续出现则把 `%LOCALAPPDATA%\electron-builder` 加入杀软白名单。
