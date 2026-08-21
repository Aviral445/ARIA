"""
aria_api.py — FastAPI Mobile & Remote Companion Server for Aria
Serves:
  • Responsive HTML5 Mobile Companion Web App with Web Speech API
  • Master Admin Authentication & Multi-User Profiles (User: "L", Pass: "balluboss")
  • Real-Time Multi-Device Control (Host Laptop vs Mobile Client)
  • Live Background Window & Application Inspection (Antigravity IDE, WhatsApp, etc.)
  • REST API endpoints: /command, /login, /register, /session, /devices, /switch_window, /system_stats, /analytics
"""

import os, sys, time, socket, json, threading, re

# Ensure all sub-packages are discoverable on sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_CURRENT_DIR) if os.path.basename(_CURRENT_DIR) == "server" else _CURRENT_DIR
for _sub in [_ROOT_DIR, os.path.join(_ROOT_DIR, "core"), os.path.join(_ROOT_DIR, "tools"), os.path.join(_ROOT_DIR, "server"), os.path.join(_ROOT_DIR, "mcp"), os.path.join(_ROOT_DIR, "gui")]:
    if _sub not in sys.path:
        sys.path.insert(0, _sub)

from fastapi import FastAPI, Request, Body, Header, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import aria_system_context
import aria_auth

app = FastAPI(title="Aria Assistant Mobile API & Web Companion", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_local_ip() -> str:
    """Find the local Wi-Fi / LAN IP address so smartphones can connect."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ─────────────────────────────────────────────────────────────────────────────
# RESPONSIVE MOBILE WEB APP HTML5 & JAVASCRIPT
# ─────────────────────────────────────────────────────────────────────────────
MOBILE_WEB_APP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover, interactive-widget=resizes-content">
  <meta name="theme-color" content="#0a0a1a">
  <title>Aria — Mobile & Multi-Device Companion</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #070913;
      --card-bg: rgba(18, 22, 40, 0.82);
      --card-border: rgba(99, 102, 241, 0.22);
      --cyan: #38bdf8;
      --purple: #818cf8;
      --pink: #ec4899;
      --gold: #f59e0b;
      --text-main: #f1f5f9;
      --text-sub: #94a3b8;
    }
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }
    html, body {
      height: 100%;
      height: 100dvh;
      overflow: hidden;
      background: var(--bg-dark);
      font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--text-main);
    }
    .app-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      height: 100dvh;
      width: 100%;
      max-width: 600px;
      margin: 0 auto;
      background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15), transparent 70%),
                  radial-gradient(circle at 100% 100%, rgba(236, 72, 153, 0.08), transparent 50%),
                  var(--bg-dark);
      position: relative;
    }
    header {
      padding: 10px 14px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--card-border);
      background: rgba(10, 12, 26, 0.85);
      backdrop-filter: blur(12px);
      z-index: 20;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .orb-canvas {
      width: 30px;
      height: 30px;
      border-radius: 50%;
    }
    .brand-text h1 {
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: 1.5px;
      background: linear-gradient(135deg, #fff, var(--cyan));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .brand-text span {
      font-size: 0.65rem;
      color: var(--text-sub);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      display: block;
    }
    .header-actions {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .admin-badge {
      font-size: 0.68rem;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 20px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.2s;
    }
    .admin-badge.is-admin {
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.4);
      box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
    }
    .admin-badge.is-guest {
      background: rgba(148, 163, 184, 0.15);
      color: var(--text-sub);
      border: 1px solid rgba(148, 163, 184, 0.3);
    }
    .device-pill {
      font-size: 0.65rem;
      padding: 4px 8px;
      border-radius: 12px;
      background: rgba(56, 189, 248, 0.1);
      color: var(--cyan);
      border: 1px solid rgba(56, 189, 248, 0.25);
      cursor: pointer;
    }

    /* System Stats Strip */
    .stats-strip {
      display: flex;
      gap: 8px;
      padding: 6px 12px;
      background: rgba(15, 18, 35, 0.7);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      overflow-x: auto;
      white-space: nowrap;
      font-size: 0.72rem;
      scrollbar-width: none;
    }
    .stats-strip::-webkit-scrollbar { display: none; }
    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--text-sub);
    }
    .stat-item strong {
      color: var(--text-main);
    }

    /* Action Chips Bar */
    .chips-bar {
      display: flex;
      gap: 6px;
      padding: 8px 12px;
      overflow-x: auto;
      scrollbar-width: none;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      background: rgba(10, 13, 28, 0.5);
    }
    .chips-bar::-webkit-scrollbar { display: none; }
    .chip {
      flex: 0 0 auto;
      font-size: 0.75rem;
      font-weight: 500;
      padding: 6px 12px;
      border-radius: 18px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-main);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
    }
    .chip:active {
      transform: scale(0.96);
      border-color: var(--cyan);
    }
    .chip.admin-chip {
      border-color: rgba(245, 158, 11, 0.4);
      color: #fbbf24;
    }

    /* Messages Area */
    .chat-area {
      flex: 1;
      overflow-y: auto;
      padding: 14px 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      scroll-behavior: smooth;
    }
    .msg {
      max-width: 86%;
      padding: 10px 14px;
      border-radius: 16px;
      font-size: 0.9rem;
      line-height: 1.45;
      animation: fadeIn 0.25s ease-out;
      word-break: break-word;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .msg.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #4f46e5, #7c3aed);
      color: #fff;
      border-bottom-right-radius: 4px;
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
    }
    .msg.assistant {
      align-self: flex-start;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-main);
      border-bottom-left-radius: 4px;
      backdrop-filter: blur(10px);
    }
    .msg-header {
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: var(--cyan);
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
    }
    .msg-actions {
      display: flex;
      gap: 8px;
      margin-top: 6px;
      font-size: 0.7rem;
      color: var(--text-sub);
    }
    .msg-action-btn {
      background: none;
      border: none;
      color: var(--text-sub);
      cursor: pointer;
      font-size: 0.72rem;
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .msg-action-btn:active { color: var(--cyan); }

    /* Typing indicator */
    .typing {
      display: none;
      align-self: flex-start;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 10px 14px;
      border-radius: 16px;
      gap: 4px;
      align-items: center;
    }
    .dot {
      width: 6px;
      height: 6px;
      background: var(--cyan);
      border-radius: 50%;
      animation: blink 1.2s infinite ease-in-out;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
      0%, 80%, 100% { opacity: 0.2; transform: scale(0.8); }
      40% { opacity: 1; transform: scale(1.1); }
    }

    /* Pinned Bottom Input Bar */
    .input-bar {
      padding: 8px 12px calc(8px + env(safe-area-inset-bottom, 12px)) 12px;
      background: rgba(10, 12, 26, 0.95);
      border-top: 1px solid var(--card-border);
      backdrop-filter: blur(14px);
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 20;
    }
    .input-wrapper {
      flex: 1;
      display: flex;
      align-items: center;
      background: rgba(18, 22, 45, 0.9);
      border: 1px solid var(--card-border);
      border-radius: 24px;
      padding: 4px 12px;
      transition: border-color 0.2s;
    }
    .input-wrapper:focus-within {
      border-color: var(--cyan);
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }
    .input-box {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 0.92rem;
      font-family: inherit;
      padding: 6px 0;
    }
    .btn-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
      flex-shrink: 0;
    }
    .mic-btn {
      background: #171b38;
      border: 1px solid var(--card-border);
      color: var(--cyan);
    }
    .mic-btn.listening {
      background: var(--pink);
      color: #fff;
      box-shadow: 0 0 16px rgba(236, 72, 153, 0.6);
      animation: pulse-mic 1s infinite;
    }
    @keyframes pulse-mic {
      0% { transform: scale(1); }
      50% { transform: scale(1.08); }
      100% { transform: scale(1); }
    }
    .send-btn {
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
      color: #fff;
      box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
    }
    .send-btn:active { transform: scale(0.92); }

    /* Modal dialogs */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(8px);
      z-index: 50;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .modal-content {
      background: #0f132a;
      border: 1px solid var(--card-border);
      border-radius: 20px;
      width: 100%;
      max-width: 420px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
    }
    .modal-header h3 {
      font-size: 1.1rem;
      color: var(--cyan);
    }
    .modal-close {
      background: none;
      border: none;
      color: var(--text-sub);
      font-size: 1.2rem;
      cursor: pointer;
    }
    .form-group {
      margin-bottom: 12px;
    }
    .form-group label {
      display: block;
      font-size: 0.75rem;
      color: var(--text-sub);
      margin-bottom: 4px;
    }
    .form-input {
      width: 100%;
      background: #181d3d;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 10px 12px;
      color: #fff;
      font-size: 0.9rem;
      outline: none;
    }
    .form-input:focus { border-color: var(--cyan); }
    .btn-block {
      width: 100%;
      padding: 10px;
      border-radius: 10px;
      border: none;
      font-weight: 600;
      cursor: pointer;
      margin-top: 8px;
    }
    .btn-primary {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #fff;
    }
    .app-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      margin-bottom: 8px;
    }
    .app-item-info strong {
      display: block;
      font-size: 0.85rem;
      color: #fff;
    }
    .app-item-info span {
      font-size: 0.7rem;
      color: var(--text-sub);
    }
    .btn-switch {
      padding: 5px 10px;
      border-radius: 8px;
      font-size: 0.72rem;
      background: var(--purple);
      border: none;
      color: #fff;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <div class="app-container">
    <!-- Header -->
    <header>
      <div class="brand">
        <canvas id="orb" class="orb-canvas" width="30" height="30"></canvas>
        <div class="brand-text">
          <h1>ARIA</h1>
          <span id="device-label">💻 Host Laptop</span>
        </div>
      </div>
      <div class="header-actions">
        <div class="device-pill" onclick="openWindowsModal()">🪟 Windows</div>
        <div class="admin-badge is-guest" id="auth-badge" onclick="openLoginModal()">👑 Login</div>
      </div>
    </header>

    <!-- System Stats Strip -->
    <div class="stats-strip">
      <div class="stat-item">💻 CPU: <strong id="cpu-val">--%</strong></div>
      <div class="stat-item">⚡ RAM: <strong id="ram-val">--%</strong></div>
      <div class="stat-item">🪟 Focused: <strong id="win-val">Desktop</strong></div>
    </div>

    <!-- Quick Action Chips -->
    <div class="chips-bar">
      <div class="chip admin-chip" onclick="sendQuick('Which tabs and apps are open on my laptop?')">🪟 Open Tabs & Apps</div>
      <div class="chip" onclick="sendQuick('Morning briefing')">🌤️ Briefing</div>
      <div class="chip" onclick="sendQuick('Tell me what window I am on my laptop')">💻 My Window</div>
      <div class="chip" onclick="sendQuick('Show battery and system stats')">📊 System</div>
      <div class="chip admin-chip" onclick="sendQuick('Minimize all windows')">🗗 Minimize All</div>
    </div>

    <!-- Chat Messages Scroll Area -->
    <div class="chat-area" id="chat-area">
      <div class="msg assistant">
        <div class="msg-header">ARIA ASSISTANT</div>
        Hello! I am your Aria Mobile Companion. Your phone is connected directly to your Main Laptop.
        <div class="msg-actions">
          <button class="msg-action-btn" onclick="speakMsg(this)">🔊 Speak</button>
          <button class="msg-action-btn" onclick="copyMsg(this)">📋 Copy</button>
        </div>
      </div>
    </div>

    <!-- Typing Indicator -->
    <div class="typing" id="typing">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>

    <!-- Input Bar -->
    <div class="input-bar">
      <button class="btn-circle mic-btn" id="mic-btn" onclick="toggleMic()" title="Voice Input">
        🎤
      </button>
      <div class="input-wrapper">
        <input type="text" class="input-box" id="cmd-input" placeholder="Message Aria or type a command..." autocomplete="off">
      </div>
      <button class="btn-circle send-btn" id="send-btn" onclick="submitCmd()" title="Send">
        ➤
      </button>
    </div>
  </div>

  <!-- Login Modal -->
  <div class="modal-overlay" id="login-modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3 id="login-title">👑 Master Admin Login</h3>
        <button class="modal-close" onclick="closeModal('login-modal')">✕</button>
      </div>
      <div class="form-group">
        <label>Username (Admin is 'L')</label>
        <input type="text" id="login-user" class="form-input" value="L">
      </div>
      <div class="form-group">
        <label>Password</label>
        <input type="password" id="login-pass" class="form-input" placeholder="Enter password...">
      </div>
      <button class="btn-block btn-primary" onclick="performLogin()">Unlock Admin Control</button>
      <button class="btn-block" style="background: rgba(255,255,255,0.06); color:#fff;" onclick="performRegister()">Create New Profile</button>
    </div>
  </div>

  <!-- Open Windows Modal -->
  <div class="modal-overlay" id="windows-modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>🪟 Windows on Host Laptop</h3>
        <button class="modal-close" onclick="closeModal('windows-modal')">✕</button>
      </div>
      <div id="windows-list" style="max-height: 280px; overflow-y: auto;">
        <div style="text-align: center; color: var(--text-sub); padding: 12px;">Loading active windows...</div>
      </div>
      <button class="btn-block" style="background: var(--purple); color:#fff; margin-top: 10px;" onclick="refreshWindowsList()">🔄 Refresh List</button>
    </div>
  </div>

  <script>
    // ── Session & Auth State ──────────────────────────────────────────────────
    let sessionToken = localStorage.getItem('aria_session_token') || '';
    let currentRole = localStorage.getItem('aria_session_role') || 'guest';
    let currentUsername = localStorage.getItem('aria_session_user') || 'Guest';

    function updateAuthBadge() {
      const badge = document.getElementById('auth-badge');
      if (currentRole === 'admin') {
        badge.className = 'admin-badge is-admin';
        badge.innerHTML = `👑 ADMIN (${currentUsername})`;
      } else if (currentRole === 'user') {
        badge.className = 'admin-badge is-guest';
        badge.innerHTML = `👤 ${currentUsername}`;
      } else {
        badge.className = 'admin-badge is-guest';
        badge.innerHTML = `🔑 Login`;
      }
    }
    updateAuthBadge();

    function openLoginModal() {
      document.getElementById('login-modal').style.display = 'flex';
      document.getElementById('login-pass').focus();
    }
    function openWindowsModal() {
      document.getElementById('windows-modal').style.display = 'flex';
      refreshWindowsList();
    }
    function closeModal(id) {
      document.getElementById(id).style.display = 'none';
    }

    async function performLogin() {
      const u = document.getElementById('login-user').value.trim();
      const p = document.getElementById('login-pass').value.trim();
      if (!u || !p) return alert('Please enter both username and password.');
      
      try {
        const res = await fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: u, password: p, device_name: 'Mobile Phone' })
        });
        const data = await res.json();
        if (data.success) {
          sessionToken = data.token;
          currentRole = data.role;
          currentUsername = data.username;
          localStorage.setItem('aria_session_token', sessionToken);
          localStorage.setItem('aria_session_role', currentRole);
          localStorage.setItem('aria_session_user', currentUsername);
          updateAuthBadge();
          closeModal('login-modal');
          appendMsg('assistant', data.message);
        } else {
          alert(data.message || 'Login failed.');
        }
      } catch (e) {
        alert('Connection error: ' + e);
      }
    }

    async function performRegister() {
      const u = document.getElementById('login-user').value.trim();
      const p = document.getElementById('login-pass').value.trim();
      if (!u || !p) return alert('Please enter username and password to create a profile.');
      
      try {
        const res = await fetch('/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: u, password: p })
        });
        const data = await res.json();
        alert(data.message);
        if (data.success) performLogin();
      } catch (e) {
        alert('Registration error: ' + e);
      }
    }

    async function refreshWindowsList() {
      const listEl = document.getElementById('windows-list');
      listEl.innerHTML = '<div style="text-align: center; color: var(--text-sub); padding: 12px;">Scanning open apps...</div>';
      try {
        const res = await fetch('/system_stats');
        const data = await res.json();
        const wins = data.context?.open_windows || [];
        if (wins.length === 0) {
          listEl.innerHTML = '<div style="text-align:center; color:var(--text-sub); padding:10px;">No background apps detected.</div>';
          return;
        }
        let html = '';
        wins.forEach(w => {
          html += `
            <div class="app-item">
              <div class="app-item-info">
                <strong>${w.app}</strong>
                <span>${w.title.slice(0, 32)}</span>
              </div>
              <button class="btn-switch" onclick="switchWindow('${w.app.replace(/'/g, "\\\\'")}')">Focus</button>
            </div>
          `;
        });
        listEl.innerHTML = html;
      } catch (e) {
        listEl.innerHTML = '<div style="color: #ef4444; text-align:center;">Failed to load windows.</div>';
      }
    }

    async function switchWindow(appName) {
      try {
        const res = await fetch('/switch_window', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ app_name: appName, token: sessionToken })
        });
        const data = await res.json();
        appendMsg('assistant', data.response);
        closeModal('windows-modal');
      } catch (e) {
        alert('Error: ' + e);
      }
    }

    // ── Canvas Orb Animation ──────────────────────────────────────────────────
    const orbCanvas = document.getElementById('orb');
    const ctx = orbCanvas.getContext('2d');
    let angle = 0;
    function drawOrb() {
      ctx.clearRect(0, 0, 30, 30);
      const gradient = ctx.createRadialGradient(15, 15, 2, 15, 15, 14);
      gradient.addColorStop(0, '#38bdf8');
      gradient.addColorStop(0.5, currentRole === 'admin' ? '#f59e0b' : '#818cf8');
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      const pulse = Math.sin(angle) * 1.5;
      ctx.arc(15, 15, 12 + pulse, 0, Math.PI * 2);
      ctx.fill();
      angle += 0.05;
      requestAnimationFrame(drawOrb);
    }
    drawOrb();

    // ── Chat & Command Logic ──────────────────────────────────────────────────
    const chatArea = document.getElementById('chat-area');
    const cmdInput = document.getElementById('cmd-input');
    const typingIndicator = document.getElementById('typing');

    function appendMsg(role, text) {
      const div = document.createElement('div');
      div.className = `msg ${role}`;
      const headerTitle = role === 'user' ? (currentUsername.toUpperCase()) : 'ARIA ASSISTANT';
      div.innerHTML = `
        <div class="msg-header">${headerTitle}</div>
        <div>${text.replace(/\\n/g, '<br>')}</div>
        ${role === 'assistant' ? `
          <div class="msg-actions">
            <button class="msg-action-btn" onclick="speakMsg(this)">🔊 Speak</button>
            <button class="msg-action-btn" onclick="copyMsg(this)">📋 Copy</button>
          </div>
        ` : ''}
      `;
      chatArea.appendChild(div);
      chatArea.scrollTop = chatArea.scrollHeight;
    }

    async function sendCommand(text) {
      if (!text || !text.trim()) return;
      const cmd = text.trim();
      appendMsg('user', cmd);
      cmdInput.value = '';
      typingIndicator.style.display = 'flex';
      chatArea.scrollTop = chatArea.scrollHeight;

      try {
        const res = await fetch('/command', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cmd: cmd, token: sessionToken })
        });
        const data = await res.json();
        typingIndicator.style.display = 'none';
        appendMsg('assistant', data.response || 'Done.');
      } catch (err) {
        typingIndicator.style.display = 'none';
        appendMsg('assistant', '⚠️ Connection failed: ' + err.message);
      }
    }

    function submitCmd() {
      sendCommand(cmdInput.value);
    }
    function sendQuick(txt) {
      sendCommand(txt);
    }
    cmdInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') submitCmd();
    });

    // ── Web Speech API (Voice Input & TTS) ────────────────────────────────────
    let recognition = null;
    let isListening = false;
    const micBtn = document.getElementById('mic-btn');

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add('listening');
        cmdInput.placeholder = 'Listening...';
      };
      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        cmdInput.value = transcript;
        sendCommand(transcript);
      };
      recognition.onend = () => {
        isListening = false;
        micBtn.classList.remove('listening');
        cmdInput.placeholder = 'Message Aria or type a command...';
      };
      recognition.onerror = () => {
        isListening = false;
        micBtn.classList.remove('listening');
      };
    }

    function toggleMic() {
      if (!recognition) {
        alert('Web Speech recognition is not supported on this browser.');
        return;
      }
      if (isListening) {
        recognition.stop();
      } else {
        recognition.start();
      }
    }

    function speakMsg(btn) {
      const parent = btn.closest('.msg');
      const text = parent.querySelector('div:nth-child(2)').innerText;
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        window.speechSynthesis.speak(utterance);
      }
    }

    function copyMsg(btn) {
      const parent = btn.closest('.msg');
      const text = parent.querySelector('div:nth-child(2)').innerText;
      navigator.clipboard.writeText(text).then(() => {
        btn.innerText = '✅ Copied';
        setTimeout(() => btn.innerText = '📋 Copy', 1500);
      });
    }

    // ── Live Telemetry Poll ───────────────────────────────────────────────────
    async function updateStats() {
      try {
        const res = await fetch('/system_stats');
        const data = await res.json();
        if (data.context) {
          document.getElementById('cpu-val').textContent = data.context.cpu_percent + '%';
          document.getElementById('ram-val').textContent = data.context.ram_percent + '%';
          const title = data.context.active_window || 'Desktop';
          document.getElementById('win-val').textContent = title.length > 18 ? title.slice(0, 18) + '..' : title;
        }
      } catch (e) {}
    }
    setInterval(updateStats, 4000);
    updateStats();
  </script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def get_mobile_ui():
    """Serves the responsive HTML5 Mobile Companion Web App."""
    return HTMLResponse(content=MOBILE_WEB_APP_HTML)

@app.get("/status")
def get_status():
    return {
        "status": "online",
        "agent": "Aria",
        "version": "3.0",
        "local_ip": get_local_ip(),
        "host_device": f"{socket.gethostname()} (Host PC)",
        "models": ["Google Gemini 2.5 Flash", "Groq Cloud"]
    }

@app.post("/login")
def login(data: dict = Body(...)):
    """Authenticate with Master Admin (L / balluboss) or a custom profile."""
    username = data.get("username", "")
    password = data.get("password", "")
    device_name = data.get("device_name", "Remote Device")
    return aria_auth.authenticate_user(username, password, device_name)

@app.post("/register")
def register(data: dict = Body(...)):
    """Register a new personal user profile."""
    username = data.get("username", "")
    password = data.get("password", "")
    return aria_auth.register_new_profile(username, password)

@app.get("/session")
def check_session(token: str = ""):
    """Verify active session token."""
    return aria_auth.verify_session(token)

@app.get("/devices")
def get_devices():
    """Returns connected devices and host laptop status."""
    return aria_auth.get_devices_status()

@app.post("/switch_window")
def switch_window(data: dict = Body(...)):
    """Focuses a running window or application on the host laptop (Admin only)."""
    app_name = data.get("app_name", "").strip()
    token = data.get("token", "")
    sess = aria_auth.verify_session(token)
    
    if not sess.get("is_admin", False):
        return {"success": False, "response": "🔒 Access Restricted: Only the Admin can switch or focus windows on this laptop."}
        
    if not app_name:
        return {"success": False, "response": "No app name provided."}
        
    try:
        import aria_extended
        res = aria_extended.open_or_focus_laptop_app(app_name)
        return {"success": True, "response": res}
    except Exception as e:
        return {"success": False, "response": f"Failed to switch window: {e}"}

@app.post("/command")
def execute_command(data: dict = Body(...)):
    """
    Executes a command or conversational query with live multi-app and window context.
    """
    cmd_clean = data.get("cmd", "").strip()
    token = data.get("token", "")
    
    if not cmd_clean:
        return {"handled": False, "response": "No command provided."}
    
    sess = aria_auth.verify_session(token)
    is_admin = sess.get("is_admin", False)
    user_name = sess.get("username", "L" if is_admin else "Friend")
    cmd_lower = cmd_clean.lower()

    # 1. Smart Laptop Intent Execution (Admin Only)
    import aria_extended, aria_system_context

    m_sec = re.search(r"^(?:switch\s+to|go\s+to|show\s+me|open\s+(?:the\s+)?|show\s+(?:the\s+)?)\s*(?:google\s+)?(images?|photos?|pics?|maps?|news|videos?|shopping|finance)\s*(?:tab|section|results?)?(?:\s+(?:for|of)\s+(.+))?$", cmd_clean, re.IGNORECASE)
    if not m_sec and any(cmd_lower == p or cmd_lower.startswith(p + " ") for p in ["images", "maps", "news", "videos", "shopping", "finance"]):
        m_sec = re.search(r"^(images?|maps?|news|videos?|shopping|finance)\s*(?:tab|section)?(?:\s+(?:for|of)\s+(.+))?$", cmd_clean, re.IGNORECASE)

    if is_admin:
        # Intent: WhatsApp Messaging & Typing
        if "whatsapp" in cmd_lower and any(k in cmd_lower for k in ["send", "type", "message", "tell", "write", "say"]):
            recipient, message = aria_extended.parse_whatsapp_intent(cmd_clean)
            if recipient and message:
                reply = aria_extended.send_whatsapp_message(recipient, message)
                try:
                    import aria_memory
                    aria_memory.record_memory_event(cmd_clean, reply)
                except Exception:
                    pass
                return {"handled": True, "type": "tool", "response": reply}

        # Intent: System Power & Security Commands (Shutdown / Restart / Lock / Sleep)
        handled_power, reply_power = aria_extended.execute_power_command(cmd_clean, is_admin=is_admin)
        if handled_power:
            try:
                import aria_memory
                aria_memory.record_memory_event(cmd_clean, reply_power)
            except Exception:
                pass
            return {"handled": True, "type": "tool", "response": reply_power}

        # Intent: Check open tabs / windows / apps on laptop
        if any(k in cmd_lower for k in ["tab", "window", "apps"]) and any(k in cmd_lower for k in ["how many", "which", "what", "list", "show"]):
            ctx = aria_system_context.get_system_context()
            open_wins = ctx.get("open_windows", [])
            if open_wins:
                titles = [f"• {w['app']}: '{w['title']}'" for w in open_wins]
                reply = f"On your laptop, you currently have {len(open_wins)} active application windows & tabs open:\n" + "\n".join(titles)
            else:
                reply = "On your laptop, no foreground application windows are currently open (showing Desktop)."
            return {"handled": True, "type": "tool", "response": reply}

        # Intent: Minimize all windows on laptop
        if "minimize all" in cmd_lower or "show desktop" in cmd_lower:
            reply = aria_extended.minimize_all_windows()
            return {"handled": True, "type": "tool", "response": reply}

        # Intent: Create / Write File on Desktop, Drives (D:, C:, E:) or Documents
        if any(k in cmd_lower for k in ["make a", "create a", "write a", "new file", "new document", "save a file", "make text file", "make .txt", "create file", "make file", "create .txt"]):
            import aria_tools
            # 1. Extract target location / drive
            m_path = re.search(r'\b(?:in|on|at|inside|to)\s+([a-zA-Z]:\\[^\s"\'<>|]+)', cmd_clean, re.IGNORECASE)
            m_drive = re.search(r'\b(?:in|on|at|inside|to)\s+([a-zA-Z])(?:\s+drive|:\/?|\b)', cmd_clean, re.IGNORECASE)
            m_loc = re.search(r'\b(?:in|on|at|inside|to)\s+(desktop|documents?|downloads?|pictures?|music|videos?)\b', cmd_clean, re.IGNORECASE)

            location = "Desktop"
            if m_path:
                location = m_path.group(1).strip()
            elif m_drive and m_drive.group(1).lower() not in ["a", "the"]:
                location = f"{m_drive.group(1).upper()}:\\"
            elif m_loc:
                location = m_loc.group(1).strip()

            # 2. Extract text content
            content = ""
            m_quote = re.search(r'["\']([^"\']+)["\']', cmd_clean)
            if m_quote:
                content = m_quote.group(1).strip()
            else:
                m_type = re.search(r'(?:type|write|with content|with text)\s+(.+)$', cmd_clean, re.IGNORECASE)
                if m_type:
                    content = m_type.group(1).strip()

            # 3. Extract filename
            filename = "document.txt"
            m_name = re.search(r'(?:named|called)\s+([a-zA-Z0-9_\-\.]+)', cmd_clean, re.IGNORECASE)
            if m_name:
                filename = m_name.group(1).strip()
            else:
                m_file_ext = re.search(r'\b([a-zA-Z0-9_\-]+\.(?:txt|md|py|json|csv|html|log|doc))\b', cmd_clean, re.IGNORECASE)
                if m_file_ext:
                    filename = m_file_ext.group(1).strip()
                elif ".txt" in cmd_lower:
                    filename = "document.txt"
                elif ".md" in cmd_lower:
                    filename = "notes.md"
                elif ".py" in cmd_lower:
                    filename = "script.py"

            reply = aria_tools.create_or_write_file(filename=filename, content=content, location=location)
            try:
                import aria_memory
                aria_memory.record_memory_event(cmd_clean, reply)
            except Exception:
                pass
            return {"handled": True, "type": "tool", "response": reply}

        # Intent: Chrome Browser Automation (Navigate / Search / Read)
        lead_ins_srch = [
            r"^(?:hey\s+|can you\s+|please\s+)?(?:open\s+chrome\s+(?:and\s+)?(?:in\s+it\s+)?)?search\s+(?:on\s+chrome|in\s+chrome|on\s+google|in\s+google|google|chrome)?\s*(?:for\s+)?",
            r"^(?:hey\s+|can you\s+|please\s+)?open\s+google\s+(?:and\s+in\s+it\s+)?search\s+(?:for\s+)?",
            r"^(?:hey\s+|can you\s+|please\s+)?(?:search\s+for|search\s+up|look\s+up|find\s+me|google)\s+",
            r"^(?:hey\s+|can you\s+|please\s+)?search\s+"
        ]
        matched_search = None
        for pat in lead_ins_srch:
            new_q = re.sub(pat, "", cmd_clean, flags=re.IGNORECASE).strip()
            if new_q != cmd_clean and len(new_q) > 1 and new_q.lower() not in ["google", "chrome"]:
                matched_search = new_q
                break

        if matched_search:
            import urllib.parse
            search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(matched_search)}"
            reply = aria_extended.open_chrome_with_profile(search_url)
            try:
                import aria_memory
                aria_memory.record_memory_event(cmd_clean, reply)
            except Exception:
                pass
            return {"handled": True, "type": "tool", "response": reply}

        if any(cmd_lower.startswith(p) for p in ["open url ", "go to ", "navigate to ", "open website ", "open site "]):
            m_url = re.search(r"(?:open url|go to|navigate to|open website|open site)\s+(.+)", cmd_clean, re.IGNORECASE)
            if m_url:
                target_url = m_url.group(1).strip()
                reply = aria_extended.open_chrome_with_profile(target_url)
                try:
                    import aria_memory
                    aria_memory.record_memory_event(cmd_clean, reply)
                except Exception:
                    pass
                return {"handled": True, "type": "tool", "response": reply}

        # Intent: Switch Google Search Section / Sub-Tab (Images, Maps, News, Videos, Shopping, Finance)
        if m_sec:
            section = m_sec.group(1).strip()
            custom_query = m_sec.group(2).strip() if len(m_sec.groups()) > 1 and m_sec.group(2) else ""
            reply = aria_extended.switch_google_search_section(section, custom_query)
            try:
                import aria_memory
                aria_memory.record_memory_event(cmd_clean, reply)
            except Exception:
                pass
            return {"handled": True, "type": "tool", "response": reply}

        # Intent: Open / Switch to New Tab in Chrome
        if any(k in cmd_lower for k in ["new tab in google", "new tab in chrome", "open new tab", "switch to new tab", "create new tab"]):
            reply = aria_extended.open_chrome_with_profile("https://www.google.com")
            try:
                import aria_memory
                aria_memory.record_memory_event(cmd_clean, reply)
            except Exception:
                pass
            return {"handled": True, "type": "tool", "response": reply}

        # Intent: Open / Launch / Focus App on Laptop
        if any(k in cmd_lower for k in ["open ", "launch ", "start ", "focus ", "switch to "]) and not any(cmd_lower.startswith(p) for p in ["how", "what", "which", "who", "why"]):
            m_app = re.search(r"(?:open|launch|start|focus|switch to)\s+([a-zA-Z0-9_\s\.\-]+)", cmd_clean, re.IGNORECASE)
            if m_app:
                raw_target = m_app.group(1).strip()
                if not any(k in raw_target.lower() for k in ["google", "youtube", "search for"]):
                    reply = aria_extended.open_or_focus_laptop_app(raw_target)
                    try:
                        import aria_memory
                        aria_memory.record_memory_event(cmd_clean, reply)
                    except Exception:
                        pass
                    return {"handled": True, "type": "tool", "response": reply}

        # Local tool execution fallback (Admin only)
        try:
            import agent as agent_mod
            handled, reply = agent_mod.run_tools(cmd_clean.lower())
            if handled:
                try:
                    import aria_memory
                    aria_memory.record_memory_event(cmd_clean, reply)
                except Exception:
                    pass
                return {"handled": True, "type": "tool", "response": reply}
        except Exception as e:
            print(f"[Tool routing notice] {e}")

    else:
        # Non-Admin: Check if guest is attempting an explicit OS / laptop command
        lead_ins_cmd = ["open ", "launch ", "start ", "close ", "switch to ", "minimize ", "lock ", "shutdown", "restart", "sleep ", "search on chrome", "search on google", "open chrome", "open website", "open site", "navigate to ", "go to ", "new tab"]
        is_explicit_cmd = (
            any(cmd_lower.startswith(p) for p in lead_ins_cmd) or
            m_sec is not None or
            "whatsapp" in cmd_lower or
            any(k in cmd_lower for k in ["lock pc", "lock laptop", "shutdown laptop", "restart laptop"])
        )
        if is_explicit_cmd and not any(cmd_lower.startswith(q) for q in ["how to", "what is", "why", "who", "can you explain", "tell me"]):
            return {
                "handled": True,
                "type": "auth_restricted",
                "response": "🔒 Access Restricted: Operating this laptop and launching applications requires Admin authorization. Please log in with your Admin credentials (Admin icon at top) to control this PC. In the meantime, feel free to chat or ask me any questions!"
            }

    # 3. AI Brain Direct Call (Available to BOTH Admin and Guests for Talking/Chatting)
    try:
        from dotenv import load_dotenv
        load_dotenv("c:/MyAgent/.env")
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        import aria_memory
        personality = aria_memory.get_personality_prompt()
        sys_ctx = aria_system_context.format_context_for_prompt(aria_system_context.get_system_context())
        
        now_str = time.strftime("%A, %B %d %Y, %I:%M %p")
        admin_status_str = "You are speaking to the Master Admin (L) who has full administrative control." if is_admin else f"You are speaking to a Guest user ('{user_name}'). You are in CONVERSATION-ONLY MODE and cannot command the host laptop."
        
        # Pull recent conversational memory turns
        recent_memories = aria_memory.load_memory_timeline()[-6:]
        history_lines = []
        for ev in recent_memories:
            u_text = ev.get('user', '').strip()
            a_text = ev.get('aria', '').strip()
            if u_text and a_text:
                history_lines.append(f"User: {u_text}")
                history_lines.append(f"Aria: {a_text}")
        history_block = "\n".join(history_lines) if history_lines else "No previous messages in this session."

        # Call Aria ADK Engine (passing is_admin status)
        try:
            import aria_adk
            adk_engine = aria_adk.get_adk_engine(gemini_key=gemini_key)
            formatted_history = []
            for ev in recent_memories:
                u_text = ev.get('user', '').strip()
                a_text = ev.get('aria', '').strip()
                if u_text and a_text:
                    formatted_history.append({"role": "user", "content": u_text})
                    formatted_history.append({"role": "assistant", "content": a_text})

            ai_reply = adk_engine.run_turn(
                user_input=cmd_clean,
                chat_history=formatted_history,
                user_name="Master Admin (L)" if is_admin else user_name,
                preferences="Full administrative laptop control" if is_admin else "",
                is_admin=is_admin
            )
            try:
                aria_memory.record_memory_event(cmd_clean, ai_reply)
            except Exception:
                pass
            return {"handled": True, "type": "ai", "response": ai_reply}
        except Exception as e_adk:
            print(f"[ADK API notice] {e_adk}")

        # Fallback to agent.chat_with_ai
        import agent as agent_mod
        profile = {"name": user_name, "is_admin": is_admin}
        ai_reply = agent_mod.chat_with_ai(cmd_clean, [], profile)
        try:
            aria_memory.record_memory_event(cmd_clean, ai_reply)
        except Exception:
            pass
        return {"handled": True, "type": "ai", "response": ai_reply}

    except Exception as e:
        return {"handled": False, "error": str(e), "response": f"Sorry, I had trouble processing that: {e}"}

@app.get("/system_stats")
def get_system_stats():
    try:
        return {"context": aria_system_context.get_system_context()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/analytics")
def get_analytics():
    try:
        import aria_memory
        return aria_memory.get_analytics_summary()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    local_ip = get_local_ip()
    print("=" * 50)
    print("Aria Mobile Companion & Multi-Device API is Ready!")
    print(f"   • On your PC browser:        http://localhost:8765")
    print(f"   • On your Phone (same WiFi): http://{local_ip}:8765")
    print(f"   • Master Admin Login:        User: 'L' | Pass: 'balluboss'")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")

