/**
 * api.js — Aria Desktop Client API Connector
 * Communicates with Aria's FastAPI Backend (http://127.0.0.1:8000)
 */

class AriaAPI {
  constructor(baseUrl = 'http://127.0.0.1:8000') {
    this.baseUrl = baseUrl;
    this.online = false;
    this.authToken = localStorage.getItem('aria_token') || 'admin_master_host_pc';
    if (!localStorage.getItem('aria_token')) {
      try { localStorage.setItem('aria_token', 'admin_master_host_pc'); } catch (_) {}
    }
  }

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/status`, { signal: AbortSignal.timeout(1800) });
      this.online = res.ok;
      return this.online;
    } catch {
      this.online = false;
      return false;
    }
  }

  async sendCommand(commandText, sessionId = 'default-session') {
    if (!this.online) {
      await this.checkHealth();
    }

    try {
      const res = await fetch(`${this.baseUrl}/command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.authToken ? `Bearer ${this.authToken}` : ''
        },
        body: JSON.stringify({
          cmd: commandText,
          token: this.authToken,
          session_id: sessionId
        }),
        signal: AbortSignal.timeout(45000)
      });
      if (res.ok) {
        this.online = true;
        return await res.json();
      }
      return { handled: false, response: `Aria Server Error (${res.status}): Please check backend logs.` };
    } catch (err) {
      this.online = false;
      return {
        handled: false,
        response: `[Aria Workstation Connecting] Aria backend server is initializing or offline at ${this.baseUrl}. If starting up, please try again in a few seconds.`
      };
    }
  }

  async getSystemStats() {
    try {
      const res = await fetch(`${this.baseUrl}/system_stats`, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async getAnalytics() {
    try {
      const res = await fetch(`${this.baseUrl}/analytics`, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async switchWindow(windowName) {
    try {
      const res = await fetch(`${this.baseUrl}/switch_window`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ window: windowName })
      });
      return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
  }

  async getPersonalityTelemetry() {
    try {
      const res = await fetch(`${this.baseUrl}/api/personality`, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async triggerGrowthReflection() {
    try {
      const res = await fetch(`${this.baseUrl}/api/personality/reflect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }

  async getWebOperationsFeed() {
    try {
      const res = await fetch(`${this.baseUrl}/api/web_feed`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async getTokenTelemetry() {
    try {
      const res = await fetch(`${this.baseUrl}/api/tokens_telemetry`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async getAdks() {
    try {
      const res = await fetch(`${this.baseUrl}/api/adks`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async getSdlcStatus() {
    try {
      const res = await fetch(`${this.baseUrl}/api/sdlc/status`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async getGaiaLabStatus() {
    try {
      const res = await fetch(`${this.baseUrl}/api/gaia/lab/status`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async executeGaiaLabAction(payload) {
    try {
      const res = await fetch(`${this.baseUrl}/api/gaia/lab/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }

  async getMusicToolkit() {
    try {
      const res = await fetch(`${this.baseUrl}/api/greenhouse/music/toolkit`, { signal: AbortSignal.timeout(2500) });
      if (res.ok) return await res.json();
    } catch {}
    return null;
  }

  async composeMusic(payload = {}) {
    try {
      const res = await fetch(`${this.baseUrl}/api/greenhouse/music/compose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }

  async sendGaiaChat(message, sessionId = 'default-gaia', userName = 'Dad L') {
    try {
      const res = await fetch(`${this.baseUrl}/api/gaia/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId, user_name: userName }),
        signal: AbortSignal.timeout(45000)
      });
      if (res.ok) return await res.json();
      return { success: false, response: `GAIA Server Error (${res.status})` };
    } catch (err) {
      return { success: false, response: `[GAIA Connecting] GAIA backend is currently offline or initializing: ${err.message}` };
    }
  }

  async getGaiaChatHistory(sessionId = 'default-gaia') {
    try {
      const res = await fetch(`${this.baseUrl}/api/gaia/chat/history?session_id=${encodeURIComponent(sessionId)}`, {
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) return await res.json();
    } catch {}
    return { success: false, history: [] };
  }

  async clearGaiaChatHistory(sessionId = 'default-gaia') {
    try {
      const res = await fetch(`${this.baseUrl}/api/gaia/chat/clear`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }

  async syncDrives() {
    try {
      const res = await fetch(`${this.baseUrl}/api/creative/sync_drives`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }

  async mapThoughtToHarmonics(text) {
    try {
      const res = await fetch(`${this.baseUrl}/api/creative/thought_bridge/map`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }

  async listEchoChamber(limit = 20) {
    try {
      const res = await fetch(`${this.baseUrl}/api/creative/echo_chamber/list?limit=${limit}`);
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false, echoes: [] };
  }

  async runAutonomousCreationCycle(payload = {}) {
    try {
      const res = await fetch(`${this.baseUrl}/api/creative/synthesis/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) return await res.json();
    } catch (err) {
      return { success: false, error: err.message };
    }
    return { success: false };
  }
}

window.ariaApi = new AriaAPI();

