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
}

window.ariaApi = new AriaAPI();

