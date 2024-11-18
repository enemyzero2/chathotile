'use strict'

import { app, BrowserWindow, ipcMain } from 'electron'
import * as path from 'path'
import { format as formatUrl } from 'url'

const isDevelopment = process.env.NODE_ENV !== 'production'

// 保持window对象的全局引用，避免JavaScript对象被垃圾回收时，窗口被自动关闭
let mainWindow

function createMainWindow() {
  const window = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  })

  if (isDevelopment) {
    // 开发环境下加载本地服务器
    window.loadURL(`http://localhost:8080`)
    window.webContents.openDevTools()
  } else {
    // 生产环境下加载打包后的文件
    window.loadURL(formatUrl({
      pathname: path.join(__dirname, 'index.html'),
      protocol: 'file',
      slashes: true
    }))
  }

  window.on('closed', () => {
    mainWindow = null
  })

  return window
}

// 当Electron完成初始化时被调用
app.on('ready', () => {
  mainWindow = createMainWindow()
})

// 当所有窗口被关闭时退出应用
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // 在macOS上，当dock图标被点击并且没有其他窗口打开时，
  // 通常在应用程序中重新创建一个窗口
  if (mainWindow === null) {
    mainWindow = createMainWindow()
  }
})
