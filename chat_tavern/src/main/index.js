import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';

// 为 ES 模块获取 __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      webSecurity: false,
      allowRunningInsecureContent: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' 'unsafe-inline' 'unsafe-eval' file: data: http: https:;"
        ]
      }
    });
  });

  if (process.env.NODE_ENV === 'development') {
    win.loadURL('http://localhost:5173')
  } else {
    const filePath = path.join(app.getAppPath(), 'dist/index.html')
    console.log('Loading file from:', filePath)
    console.log('__dirname is:', __dirname)
    
    win.loadFile(filePath)
    
    win.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
      console.error('Failed to load:', errorCode, errorDescription)
      console.error('Attempted path:', filePath)
    })
  }

  win.webContents.openDevTools()
}

app.whenReady().then(() => {
  createWindow()
})

app.on('window-all-closed',()=>{
  if(process.platform !== 'darwin'){
    app.quit();
  }
});

app.on('activate',()=>{
  if(BrowserWindow.getAllWindows().length === 0) createWindow();
});






