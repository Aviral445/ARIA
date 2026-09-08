/**
 * api.js — Aria Desktop Client API Connector
 * Communicates with Aria's FastAPI Backend (http://127.0.0.1:8000)
 */

class AriaAPI {
  constructor(baseUrl = 'http://127.0.0.1:8000') {
    this.baseUrl = baseUrl;
    this.online = false;
    this.authToken = localStorage.getItem('aria_token') || '';
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
      // Fallback local echo if server is starting or offline
      return {
        handled: true,
        response: `[Offline Simulation] Aria received: "${commandText}". To connect full agent capabilities, please ensure Aria API server is running on ${this.baseUrl}.`
      };
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
        })
      });
      return await res.json();
    } catch (err) {
      return { handled: false, response: `Network Error: ${err.message}` };
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
}

window.ariaApi = new AriaAPI();
