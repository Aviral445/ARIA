const { app, BrowserWindow, Menu, globalShortcut } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let apiProcess = null;

function ensureBackendRunning() {
  const req = http.get('http://127.0.0.1:8000/status', (res) => {
    // Backend is already alive and running on port 8000!
  });
  req.on('error', () => {
    try {
      const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
      const rootDir = path.join(__dirname, '..');
      const apiScript = path.join(rootDir, 'aria_api.py');
      apiProcess = spawn(pythonExe, [apiScript], {
        cwd: rootDir,
        windowsHide: true,
        stdio: 'pipe',
        env: Object.assign({}, process.env, { ARIA_PORT: '8000' })
      });
      if (apiProcess.stdout) {
        apiProcess.stdout.on('data', (d) => console.log(`[AriaBackend] ${d}`));
      }
      if (apiProcess.stderr) {
        apiProcess.stderr.on('data', (d) => console.error(`[AriaBackend] ${d}`));
      }
    } catch (e) {
      console.error('Failed to spawn Aria backend:', e);
    }
  });
}

function createWindow() {
  ensureBackendRunning();

  mainWindow = new BrowserWindow({
    width: 1380,
    height: 880,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: '#07090e',
    title: 'Aria AI — Autonomous Desktop Cyber Workstation',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    },
    show: false
  });

  // Remove default menu bar for sleek workstation cockpit look
  Menu.setApplicationMenu(null);

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Register developer shortcuts (F12 / Ctrl+Shift+I for DevTools, F5 / Ctrl+R to reload)
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.key === 'F12' || (input.control && input.shift && input.key.toLowerCase() === 'i')) {
      mainWindow.webContents.toggleDevTools();
      event.preventDefault();
    }
    if (input.key === 'F5' || (input.control && input.key.toLowerCase() === 'r')) {
      mainWindow.webContents.reload();
      event.preventDefault();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('will-quit', () => {
  if (apiProcess) {
    try {
      apiProcess.kill();
    } catch (e) {}
    apiProcess = null;
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
