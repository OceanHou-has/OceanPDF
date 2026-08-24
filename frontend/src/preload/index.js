import { contextBridge, ipcRenderer } from 'electron'

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 文件选择
  selectFile: () => ipcRenderer.invoke('dialog:selectFile'),

  // 系统信息
  platform: process.platform,

  // ==================== 自动更新 ====================
  // 检查更新（手动触发时用，主进程也会在启动后自动检查一次）
  checkForUpdates: () => ipcRenderer.invoke('update:check'),
  // 开始下载新版本
  downloadUpdate: () => ipcRenderer.send('update:download'),
  // 下载完成后退出并安装
  installUpdate: () => ipcRenderer.send('update:install'),
  // 当前应用版本号
  getAppVersion: () => ipcRenderer.invoke('app:version'),
  // 订阅更新事件：{ type: 'available'|'progress'|'downloaded'|'error'|'checking'|'not-available', ... }
  onUpdateEvent: (callback) => {
    const handler = (_e, payload) => callback(payload)
    ipcRenderer.on('update:event', handler)
    return () => ipcRenderer.removeListener('update:event', handler)
  }
})
