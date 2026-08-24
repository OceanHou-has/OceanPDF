import { app, BrowserWindow, shell, dialog, ipcMain } from 'electron'
import { join } from 'path'
import { spawn, spawnSync } from 'child_process'
import { existsSync, appendFileSync } from 'fs'
import http from 'http'
import { autoUpdater } from 'electron-updater'

let mainWindow
let backendProcess = null

const API_PORT = 8000
const API_BASE = `http://127.0.0.1:${API_PORT}`

// 调试日志：同时输出到控制台和 userData/renderer-debug.log（打包环境无控制台，靠文件排查）
function debugLog(...args) {
  const line = `[${new Date().toISOString()}] ${args.join(' ')}\n`
  console.log(line.trimEnd())
  try {
    appendFileSync(join(app.getPath('userData'), 'renderer-debug.log'), line)
  } catch {
    /* 忽略 */
  }
}

// ==================== 后端进程管理（打包环境专用） ====================

function getBackendExePath() {
  // 打包后：resources/backend/OceanPDFBackend.exe（由 electron-builder extraResources 注入）
  return join(process.resourcesPath, 'backend', 'OceanPDFBackend.exe')
}

function startBackend() {
  const exePath = getBackendExePath()
  if (!existsSync(exePath)) {
    dialog.showErrorBox(
      '后端缺失',
      `未找到后端程序：${exePath}\n请重新安装应用。`
    )
    app.quit()
    return false
  }

  try {
    backendProcess = spawn(exePath, [], {
      stdio: 'ignore',       // 后端自带控制台窗口，父进程不接管输出
      detached: false,
      windowsHide: true
    })

    backendProcess.on('error', (err) => {
      console.error('[backend] 启动失败:', err)
    })
    backendProcess.on('exit', (code) => {
      console.log(`[backend] 进程退出 code=${code}`)
      backendProcess = null
    })
    return true
  } catch (err) {
    dialog.showErrorBox('后端启动失败', String(err))
    app.quit()
    return false
  }
}

function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get(`${API_BASE}/health`, { timeout: 1500 }, (res) => {
      resolve(res.statusCode === 200)
      res.resume()
    })
    req.on('error', () => resolve(false))
    req.on('timeout', () => {
      req.destroy()
      resolve(false)
    })
  })
}

async function waitBackendReady(timeoutMs = 60000) {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    if (await checkBackendHealth()) return true
    await new Promise((r) => setTimeout(r, 500))
  }
  return false
}

function stopBackend() {
  if (backendProcess) {
    try {
      // Windows 下用 taskkill 结束整个进程树（PyInstaller onedir 可能派生子进程）
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(backendProcess.pid), '/t', '/f'], {
          stdio: 'ignore',
          windowsHide: true
        })
      } else {
        backendProcess.kill()
      }
    } catch (err) {
      console.error('[backend] 结束进程失败:', err)
    }
    backendProcess = null
  }
}

// 同步结束后端进程：更新安装前必须用（异步 taskkill 可能来不及释放 exe 文件锁）
function stopBackendSync() {
  if (backendProcess) {
    try {
      if (process.platform === 'win32') {
        spawnSync('taskkill', ['/pid', String(backendProcess.pid), '/t', '/f'], {
          stdio: 'ignore',
          windowsHide: true
        })
      } else {
        backendProcess.kill('SIGKILL')
      }
    } catch (err) {
      console.error('[backend] 结束进程失败:', err)
    }
    backendProcess = null
  }
}

// ==================== 自动更新（GitHub Releases + electron-updater） ====================

function getReleaseNotes(info) {
  const notes = info?.releaseNotes
  if (!notes) return ''
  if (typeof notes === 'string') return notes
  if (Array.isArray(notes)) {
    return notes.map((n) => n.note || '').filter(Boolean).join('\n')
  }
  return ''
}

function setupAutoUpdater() {
  // 仅打包环境检查更新；开发模式（npm run electron:dev）不生效
  if (!app.isPackaged) return

  // 后台自动检查的失败要静默处理（比如仓库暂无带 latest.yml 的 Release 时 GitHub 会 404），
  // 只在用户主动操作（手动检查/下载/安装）出错时才弹窗提示
  let quietErrors = false

  autoUpdater.autoDownload = false          // 先弹提示，用户点击后再下载
  autoUpdater.autoInstallOnAppQuit = false  // 安装时机由我们显式控制
  autoUpdater.logger = {
    info: (...args) => debugLog('[updater]', ...args),
    warn: (...args) => debugLog('[updater]', ...args),
    error: (...args) => debugLog('[updater]', ...args)
  }

  const send = (type, data = {}) => {
    mainWindow?.webContents.send('update:event', { type, ...data })
  }

  autoUpdater.on('checking-for-update', () => send('checking'))
  autoUpdater.on('update-available', (info) => {
    send('available', { version: info.version, releaseNotes: getReleaseNotes(info) })
  })
  autoUpdater.on('update-not-available', () => send('not-available'))
  autoUpdater.on('download-progress', (p) => {
    send('progress', { percent: Math.round(p.percent) })
  })
  autoUpdater.on('update-downloaded', (info) => {
    send('downloaded', { version: info.version })
  })
  autoUpdater.on('error', (err) => {
    send('error', { message: String(err?.message || err), silent: quietErrors })
  })

  // 渲染层触发：检查 / 下载 / 安装
  ipcMain.handle('update:check', async () => {
    try {
      await autoUpdater.checkForUpdates()
    } catch (err) {
      send('error', { message: String(err?.message || err), silent: quietErrors })
    }
  })
  ipcMain.on('update:download', () => {
    autoUpdater.downloadUpdate().catch((err) => {
      send('error', { message: String(err?.message || err) })
    })
  })
  ipcMain.on('update:install', () => {
    // 先同步杀掉内置后端，否则新安装包覆盖 resources/backend 时 exe 被占用
    stopBackendSync()
    // 稍等片刻让系统释放文件句柄，再退出并运行安装包
    setTimeout(() => autoUpdater.quitAndInstall(false, true), 800)
  })

  // 当前应用版本（用于界面展示）
  ipcMain.handle('app:version', () => app.getVersion())

  // 启动 15 秒后再检查，不拖慢首屏
  setTimeout(() => {
    quietErrors = true
    // 注意：必须先 catch 消化错误，否则 rejection 会变成 unhandled rejection 把应用终止掉
    autoUpdater.checkForUpdates().catch(() => {}).finally(() => {
      quietErrors = false
    })
  }, 15000)
}

// ==================== 窗口管理 ====================

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: join(__dirname, './preload/index.cjs'),
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  // 外部链接用系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  // 渲染进程日志/加载失败捕获（白屏排查）
  mainWindow.webContents.on('console-message', (_e, level, message) => {
    debugLog(`[renderer L${level}]`, message)
  })
  mainWindow.webContents.on('did-fail-load', (_e, code, desc, url) => {
    debugLog(`[renderer] 页面加载失败 code=${code} desc=${desc} url=${url}`)
  })
  mainWindow.webContents.on('render-process-gone', (_e, details) => {
    debugLog(`[renderer] 渲染进程崩溃 reason=${details.reason} code=${details.exitCode}`)
  })

  // 开发环境
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    // 生产环境（产物结构：dist-electron/main.js 与 renderer/、preload/ 同级）
    const pagePath = join(__dirname, './renderer/index.html')
    debugLog('[main] 加载页面:', pagePath, 'exists=', existsSync(pagePath))
    mainWindow.loadFile(pagePath)
  }
}

app.whenReady().then(async () => {
  // 打包环境：先拉起内置后端并等待就绪；开发环境沿用手动启动后端的方式
  if (app.isPackaged) {
    if (!startBackend()) return
    const ready = await waitBackendReady()
    if (!ready) {
      dialog.showErrorBox(
        '后端启动超时',
        `后端服务未能在预期时间内就绪（${API_BASE}）。\n请检查 8000 端口是否被占用，或查看 %APPDATA%\\OceanPDF\\logs\\app.log`
      )
      stopBackend()
      app.quit()
      return
    }
  }

  createWindow()
  setupAutoUpdater()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('quit', () => {
  stopBackend()
})
