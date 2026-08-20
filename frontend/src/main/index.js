import { app, BrowserWindow, shell, dialog } from 'electron'
import { join } from 'path'
import { spawn } from 'child_process'
import { existsSync, appendFileSync } from 'fs'
import http from 'http'

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
