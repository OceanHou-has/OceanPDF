import { contextBridge, ipcRenderer } from 'electron'

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 文件选择
  selectFile: () => ipcRenderer.invoke('dialog:selectFile'),
  
  // 系统信息
  platform: process.platform,
  
  // 其他需要的API可以在这里添加
})
