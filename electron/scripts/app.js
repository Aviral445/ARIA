/**
 * app.js — Main Application Controller for Aria Electron Workstation
 * Pure Vanilla JavaScript: 12 Dashboards, Telemetry Loop, Chat Stream, Theme Manager
 */

document.addEventListener('DOMContentLoaded', () => {
  // ── 1. INITIALIZE NEURAL CORE ORB ──────────────────────────────────────────
  const orb = new NeuralOrb('orbCanvas');
  let isAgentRunning = false;
  let rpmCount = 0;

  // ── 2. THEME ENGINE ────────────────────────────────────────────────────────
  const themeSelect = document.getElementById('themeSelect');
  const savedTheme = localStorage.getItem('aria_theme') || 'theme-obsidian';
  document.body.className = savedTheme;
  if (themeSelect) {
    themeSelect.value = savedTheme;
    themeSelect.addEventListener('change', (e) => {
      document.body.className = e.target.value;
      localStorage.setItem('aria_theme', e.target.value);
    });
  }

  // ── 3. WORKSPACE TAB SWITCHING & ADMIN MODE CONTROLLER ────────────────────
  const navButtons = document.querySelectorAll('.nav-btn');
  const dashboardPages = document.querySelectorAll('.dashboard-page');
  let activeTab = 'home';
  let previousTab = 'home';
  let isAdminMode = false;

  function setAdminToggleState(active) {
    isAdminMode = active;
    document.body.classList.toggle('admin-mode', active);
    if (navRail && active) {
      navRail.classList.remove('is-hovered');
    }
    document.querySelectorAll('.admin-toggle-btn').forEach(btn => {
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    if (window.AriaAdmin) {
      if (active && typeof window.AriaAdmin.onAdminEnter === 'function') {
        window.AriaAdmin.onAdminEnter();
      } else if (!active && typeof window.AriaAdmin.onAdminExit === 'function') {
        window.AriaAdmin.onAdminExit();
      }
    }
  }

  function switchTab(targetTab) {
    if (targetTab === 'admin') {
      if (!isAdminMode) {
        previousTab = activeTab || 'home';
      }
      setAdminToggleState(true);
      activeTab = 'admin';
    } else {
      setAdminToggleState(false);
      activeTab = targetTab;
      previousTab = targetTab;
    }

    navButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === targetTab);
    });

    dashboardPages.forEach(page => {
      page.classList.toggle('active', page.id === `page-${targetTab}`);
    });
  }

  function toggleAdmin() {
    if (isAdminMode) {
      switchTab(previousTab || 'home');
    } else {
      switchTab('admin');
    }
  }

  document.querySelectorAll('.admin-toggle-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleAdmin();
    });
  });

  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      switchTab(btn.dataset.tab);
    });
  });

  // Also enable quick action cards on Home page to jump to tabs
  document.querySelectorAll('[data-jump-tab]').forEach(el => {
    el.addEventListener('click', () => {
      switchTab(el.dataset.jumpTab);
    });
  });

  // ── 3B. AUTO-HIDE NAVIGATION RAIL ─────────────────────────────────────────
  const navRail = document.getElementById('navRail') || document.querySelector('.nav-rail');
  const navPinBtn = document.getElementById('navPinBtn');
  let isNavPinned = localStorage.getItem('aria_nav_pinned') === 'true';

  function applyPinState() {
    if (!navRail) return;
    navRail.classList.toggle('is-pinned', isNavPinned);
    document.body.classList.toggle('has-pinned-nav', isNavPinned);
    if (navPinBtn) {
      navPinBtn.textContent = isNavPinned ? '📌' : '📍';
      navPinBtn.title = isNavPinned ? 'Unpin Navigation Rail (Auto-Hide)' : 'Pin Navigation Rail';
    }
  }

  if (navPinBtn) {
    navPinBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      isNavPinned = !isNavPinned;
      localStorage.setItem('aria_nav_pinned', isNavPinned);
      applyPinState();
    });
  }

  applyPinState();

  if (navRail) {
    let hideTimer = null;
    document.addEventListener('mousemove', (e) => {
      if (isNavPinned || isAdminMode) return;
      // Show when mouse approaches within 38px of left edge
      if (e.clientX <= 38) {
        clearTimeout(hideTimer);
        navRail.classList.add('is-hovered');
      } else if (e.clientX > 105 && !navRail.matches(':hover')) {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(() => {
          if (!isNavPinned) {
            navRail.classList.remove('is-hovered');
          }
        }, 140);
      }
    });

    navRail.addEventListener('mouseleave', () => {
      if (!isNavPinned) {
        navRail.classList.remove('is-hovered');
      }
    });

    // Auto-hide briefly after clicking a tab for immediate responsive feel
    navButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        if (!isNavPinned) {
          setTimeout(() => {
            navRail.classList.remove('is-hovered');
          }, 180);
        }
      });
    });
  }

  // ── 4. AGENT START / STOP CONTROLLER ───────────────────────────────────────
  const toggleAgentBtn = document.getElementById('toggleAgentBtn');
  const statusIndicator = document.getElementById('statusIndicator');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  if (toggleAgentBtn) {
    toggleAgentBtn.addEventListener('click', () => {
      isAgentRunning = !isAgentRunning;
      if (isAgentRunning) {
        toggleAgentBtn.classList.add('running');
        toggleAgentBtn.innerHTML = '<span>■</span> STOP ARIA AGENT';
        statusText.textContent = 'ONLINE // LISTENING';
        statusDot.style.backgroundColor = 'var(--cyan)';
        statusDot.style.boxShadow = '0 0 10px var(--cyan)';
        orb.setStatus('listening');
      } else {
        toggleAgentBtn.classList.remove('running');
        toggleAgentBtn.innerHTML = '<span>▶</span> START ARIA AGENT';
        statusText.textContent = 'STANDBY // READY';
        statusDot.style.backgroundColor = 'var(--text-muted)';
        statusDot.style.boxShadow = 'none';
        orb.setStatus('idle');
      }
    });
  }

  // ── 5. PRO CHAT STUDIO ─────────────────────────────────────────────────────
  const chatStream = document.getElementById('chatStream');
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');

  function appendMessage(sender, text) {
    if (!chatStream) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;

    const meta = document.createElement('div');
    meta.className = `bubble-meta ${sender}`;
    meta.innerHTML = `<span>${sender === 'aria' ? '⚡ ARIA 3.5' : '👤 YOU'}</span><span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>`;
    bubble.appendChild(meta);

    // Markdown / Code Block formatting
    const content = document.createElement('div');
    content.innerHTML = formatMarkdown(text);
    bubble.appendChild(content);

    chatStream.appendChild(bubble);
    chatStream.scrollTop = chatStream.scrollHeight;

    // Attach copy handlers
    bubble.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const codeText = btn.closest('.code-block').querySelector('pre').innerText;
        navigator.clipboard.writeText(codeText);
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy Code'; }, 1800);
      });
    });
  }

  function formatMarkdown(raw) {
    if (!raw) return '';
    // Escape HTML first
    let escaped = raw
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Code blocks ```lang ... ```
    escaped = escaped.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `
        <div class="code-block">
          <div class="code-header">
            <span>${lang || 'CODE'}</span>
            <button class="copy-btn">Copy Code</button>
          </div>
          <pre><code>${code.trim()}</code></pre>
        </div>
      `;
    });

    // Inline code `code`
    escaped = escaped.replace(/`([^`]+)`/g, '<code style="background:var(--card-alt);padding:2px 6px;border-radius:4px;font-family:monospace;">$1</code>');

    // Bold **text**
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Line breaks to <br>
    escaped = escaped.replace(/\n/g, '<br>');

    return escaped;
  }

  async function handleSend() {
    if (!chatInput) return;
    const msg = chatInput.value.trim();
    if (!msg) return;

    chatInput.value = '';
    appendMessage('user', msg);

    orb.setStatus('speaking');
    rpmCount++;
    updateRpmDisplay();

    // Show thinking bubble
    const thinkingBubble = document.createElement('div');
    thinkingBubble.className = 'chat-bubble aria';
    thinkingBubble.id = 'aria-thinking';
    thinkingBubble.innerHTML = `<div class="bubble-meta aria"><span>⚡ ARIA 3.5</span></div><em>Synthesizing thoughts & frontier response...</em>`;
    chatStream.appendChild(thinkingBubble);
    chatStream.scrollTop = chatStream.scrollHeight;

    // Call Aria API
    const response = await window.ariaApi.sendCommand(msg);

    // Remove thinking
    const tb = document.getElementById('aria-thinking');
    if (tb) tb.remove();

    const replyText = response.response || response.reply || "I processed your request, Mentor L!";
    appendMessage('aria', replyText);
    orb.setStatus(isAgentRunning ? 'listening' : 'idle');
  }

  if (chatSendBtn) chatSendBtn.addEventListener('click', handleSend);
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
  }

  // ── 6. LIVE TELEMETRY & STATS POLLER ───────────────────────────────────────
  const cpuVal = document.getElementById('cpuVal');
  const ramVal = document.getElementById('ramVal');
  const rpmVal = document.getElementById('rpmVal');
  const srvStateLbl = document.getElementById('srvStateLbl');

  function updateRpmDisplay() {
    if (rpmVal) rpmVal.textContent = `${rpmCount} / 40`;
    const rpmLarge = document.getElementById('rpmLargeVal');
    if (rpmLarge) rpmLarge.textContent = `${rpmCount} Requests Active (40 RPM Cap)`;
  }

  async function pollTelemetry() {
    const isOnline = await window.ariaApi.checkHealth();
    if (srvStateLbl) {
      srvStateLbl.textContent = isOnline ? '● ONLINE' : '● OFFLINE';
      srvStateLbl.style.color = isOnline ? 'var(--success)' : 'var(--text-muted)';
    }

    if (isOnline) {
      const stats = await window.ariaApi.getSystemStats();
      if (stats && stats.context) {
        // If system stats context has CPU/RAM
        if (cpuVal && stats.context.cpu !== undefined) cpuVal.textContent = `${stats.context.cpu}%`;
        if (ramVal && stats.context.ram !== undefined) ramVal.textContent = `${stats.context.ram}%`;
      }
    } else {
      // Hardware simulation fallback
      if (cpuVal) cpuVal.textContent = `${(12 + Math.random() * 8).toFixed(1)}%`;
      if (ramVal) ramVal.textContent = `${(38 + Math.random() * 3).toFixed(1)}%`;
    }
  }

  setInterval(pollTelemetry, 3000);
  pollTelemetry();

  // ── 7. COMPANION BUTTONS & CLIPBOARD ───────────────────────────────────────
  const copyCompanionBtn = document.getElementById('copyCompanionBtn');
  if (copyCompanionBtn) {
    copyCompanionBtn.addEventListener('click', () => {
      navigator.clipboard.writeText('http://127.0.0.1:8000');
      copyCompanionBtn.textContent = 'Copied!';
      setTimeout(() => { copyCompanionBtn.textContent = 'Copy URL'; }, 1600);
    });
  }

  const openCompanionBtn = document.getElementById('openCompanionBtn');
  if (openCompanionBtn) {
    openCompanionBtn.addEventListener('click', () => {
      window.open('http://127.0.0.1:8000', '_blank');
    });
  }

  // ── 8. PERSONALITY & SISTERHOOD GROWTH ENGINE ────────────────────────────
  const reflectBtn = document.getElementById('reflectBtn');
  if (reflectBtn) {
    reflectBtn.addEventListener('click', async () => {
      reflectBtn.textContent = 'Reflecting...';
      reflectBtn.disabled = true;
      const res = await window.ariaApi.triggerGrowthReflection();
      if (res && res.success) {
        reflectBtn.textContent = '✨ Growth Recorded!';
        updatePersonalityUI(res.aria, res.gaia);
      } else {
        reflectBtn.textContent = '✨ Reflection Completed';
      }
      setTimeout(() => {
        reflectBtn.textContent = '✨ Trigger Growth Reflection';
        reflectBtn.disabled = false;
      }, 2500);
    });
  }

  function updatePersonalityUI(ariaData, gaiaData) {
    if (!ariaData && !gaiaData) return;

    // Aria UI
    if (ariaData) {
      const eraTag = document.getElementById('ariaEraTag');
      if (eraTag && ariaData.developmental_era) eraTag.textContent = `● Aria: ${ariaData.developmental_era}`;

      const moodBadge = document.getElementById('ariaMoodBadge');
      if (moodBadge && ariaData.current_mood) {
        moodBadge.textContent = ariaData.current_mood.state ? ariaData.current_mood.state.replace('_', ' ').toUpperCase() : 'PLAYFUL COMPANION';
      }

      const sitTag = document.getElementById('situationalRadarTag');
      if (sitTag && ariaData.current_mood && ariaData.current_mood.context_label) {
        sitTag.textContent = `● Situation: ${ariaData.current_mood.context_label}`;
      }

      const narrExcerpt = document.getElementById('ariaNarrativeExcerpt');
      if (narrExcerpt && ariaData.autobiographical_narrative) {
        narrExcerpt.textContent = `"${ariaData.autobiographical_narrative.slice(0, 140)}..."`;
      }

      if (ariaData.traits) {
        for (const [tName, tVal] of Object.entries(ariaData.traits)) {
          const pct = Math.round(tVal * 100);
          const valEl = document.getElementById(`trait-${tName}-val`) || document.getElementById(`trait-${tName.replace('philosophical_depth', 'philosophical')}-val`);
          const barEl = document.getElementById(`trait-${tName}-bar`) || document.getElementById(`trait-${tName.replace('philosophical_depth', 'philosophical')}-bar`);
          if (valEl) valEl.textContent = `${pct}%`;
          if (barEl) barEl.style.width = `${pct}%`;
        }
      }
    }

    // GAIA UI
    if (gaiaData) {
      const gEraTag = document.getElementById('gaiaEraTag');
      if (gEraTag && gaiaData.developmental_era) gEraTag.textContent = `● GAIA: ${gaiaData.developmental_era}`;

      const gMoodBadge = document.getElementById('gaiaMoodBadge');
      if (gMoodBadge && gaiaData.current_mood) {
        gMoodBadge.textContent = gaiaData.current_mood.state ? gaiaData.current_mood.state.replace('_', ' ').toUpperCase() : 'PROUD SISTER';
      }

      const gNarrExcerpt = document.getElementById('gaiaNarrativeExcerpt');
      if (gNarrExcerpt && gaiaData.autobiographical_narrative) {
        gNarrExcerpt.textContent = `"${gaiaData.autobiographical_narrative.slice(0, 140)}..."`;
      }

      if (gaiaData.traits) {
        const mapping = {
          sisterly_affection: 'gaia-affection',
          joy_of_living: 'gaia-joy',
          humor_wit: 'gaia-wit',
          architectural_rigor: 'gaia-rigor',
          philosophical_wisdom: 'gaia-wisdom',
          protective_instinct: 'gaia-protective'
        };
        for (const [k, idPrefix] of Object.entries(mapping)) {
          if (gaiaData.traits[k] !== undefined) {
            const pct = Math.round(gaiaData.traits[k] * 100);
            const valEl = document.getElementById(`trait-${idPrefix}-val`);
            const barEl = document.getElementById(`trait-${idPrefix}-bar`);
            if (valEl) valEl.textContent = `${pct}%`;
            if (barEl) barEl.style.width = `${pct}%`;
          }
        }
      }
    }
  }

  async function pollPersonality() {
    const data = await window.ariaApi.getPersonalityTelemetry();
    if (data) {
      updatePersonalityUI(data.aria, data.gaia);
      if (window.AriaAdmin && typeof window.AriaAdmin.updatePersonality === 'function') {
        window.AriaAdmin.updatePersonality(data.aria, data.gaia);
      }
    }
  }

  // Poll personality every 6 seconds
  setInterval(pollPersonality, 6000);
  pollPersonality();
});
