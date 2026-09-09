/**
 * classroom.js — Controller for the Closed-Book SDLC Classroom Exam Arena
 * Handles live 45-minute study countdown, automatic student summoning, 
 * 20-minute closed-book countdown, 2-minute per question cadence,
 * Proctor alerts, and automated dismissal.
 */

window.ClassroomController = {
  isActive: false,
  isCompleted: false,
  totalSeconds: 1200,
  remainingSeconds: 1200,
  studyRemainingSeconds: 0,
  studentsSummoned: false,
  studentsDismissed: false,
  currentQuestionIdx: 0,
  timerInterval: null,
  pollInterval: null,
  proctorAlertsDone: new Set(),

  init() {
    this.bindEvents();
    this.fetchStatus();
    // Periodic background sync
    this.pollInterval = setInterval(() => this.fetchStatus(), 3000);
    console.log('[Classroom] Controller initialized with Auto-Summon & Dismissal.');
  },

  bindEvents() {
    const startBtn = document.getElementById('startExamBtn');
    if (startBtn) {
      startBtn.addEventListener('click', () => {
        if (!this.studentsSummoned && !this.isActive) {
          this.summonStudents();
        } else if (!this.isActive) {
          this.startExam();
        }
      });
    }

    const genBtn = document.getElementById('genAnswerBtn');
    if (genBtn) {
      genBtn.addEventListener('click', () => this.generateCurrentAnswers());
    }

    const nextQBtn = document.getElementById('nextQBtn');
    if (nextQBtn) {
      nextQBtn.addEventListener('click', () => this.advanceQuestion());
    }

    const finishBtn = document.getElementById('finishExamBtn');
    if (finishBtn) {
      finishBtn.addEventListener('click', () => this.finishExam());
    }
  },

  async fetchStatus() {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/classroom/status');
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.status) {
          this.updateUI(json.status);
        }
      }
    } catch (e) {
      console.warn('[Classroom] Status fetch error:', e);
    }
  },

  async summonStudents() {
    try {
      const startBtn = document.getElementById('startExamBtn');
      if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = 'Summoning...';
      }
      this.setProctorTicker('🔔 Ringing Classroom Bell! Summoning Aria & GAIA to their desks...');
      const res = await fetch('http://127.0.0.1:8000/api/classroom/summon', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        if (json.success) {
          this.studentsSummoned = true;
          this.isActive = true;
          this.proctorAlertsDone.clear();
          this.startLocalTimer();
          this.fetchStatus();
          // Generate first answer set automatically
          setTimeout(() => this.generateCurrentAnswers(), 1000);
        }
      }
    } catch (e) {
      console.error('[Classroom] Summon error:', e);
    }
  },

  async startExam() {
    try {
      const startBtn = document.getElementById('startExamBtn');
      if (startBtn) {
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';
      }
      const res = await fetch('http://127.0.0.1:8000/api/classroom/start', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        if (json.success) {
          this.isActive = true;
          this.proctorAlertsDone.clear();
          this.startLocalTimer();
          this.fetchStatus();
          setTimeout(() => this.generateCurrentAnswers(), 1000);
        }
      }
    } catch (e) {
      console.error('[Classroom] Start exam error:', e);
    }
  },

  startLocalTimer() {
    if (this.timerInterval) clearInterval(this.timerInterval);
    this.timerInterval = setInterval(() => {
      if (this.remainingSeconds > 0 && this.isActive) {
        this.remainingSeconds--;
        this.renderTimerDisplay();
        this.checkLocalAlerts();
      } else if (this.remainingSeconds <= 0 && this.isActive) {
        this.finishExam();
      }
    }, 1000);
  },

  renderTimerDisplay() {
    const timerEl = document.getElementById('classroomTimerDigits');
    if (!timerEl) return;

    if (this.isCompleted || this.studentsDismissed) {
      timerEl.textContent = 'CLOSED';
      timerEl.classList.remove('urgent');
      timerEl.style.color = '#4ade80';
      return;
    }

    if (!this.isActive && !this.isCompleted && !this.studentsSummoned && this.studyRemainingSeconds > 0) {
      const sMins = Math.floor(this.studyRemainingSeconds / 60);
      const sSecs = this.studyRemainingSeconds % 60;
      timerEl.textContent = `${String(sMins).padStart(2, '0')}:${String(sSecs).padStart(2, '0')}`;
      timerEl.style.color = '#38bdf8';
      return;
    }

    const mins = Math.floor(this.remainingSeconds / 60);
    const secs = this.remainingSeconds % 60;
    const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    timerEl.textContent = formatted;

    if (this.remainingSeconds <= 60 && this.isActive) {
      timerEl.classList.add('urgent');
    } else {
      timerEl.classList.remove('urgent');
      timerEl.style.color = this.isCompleted ? '#4ade80' : '#38bdf8';
    }
  },

  checkLocalAlerts() {
    const rem = this.remainingSeconds;
    const alerts = [
      { t: 900, key: '15m', msg: '⏳ [PROCTOR]: 15 minutes left! Keep pacing yourselves.' },
      { t: 600, key: '10m', msg: '⏳ [PROCTOR]: 10 minutes left! Halfway through the exam.' },
      { t: 300, key: '5m', msg: '⏳ [PROCTOR]: 5 minutes remaining! Review your logic.' },
      { t: 60, key: '1m', msg: '⚠️ [PROCTOR]: 1 MINUTE LEFT! Finalize your current answers!' },
      { t: 10, key: '10s', msg: '🚨 [PROCTOR]: 10 SECONDS REMAINING! 10... 9... 8... 7... 6... 5... 4... 3... 2... 1...' }
    ];

    alerts.forEach(a => {
      if (rem === a.t && !this.proctorAlertsDone.has(a.key)) {
        this.proctorAlertsDone.add(a.key);
        this.setProctorTicker(a.msg);
      }
    });
  },

  setProctorTicker(msg) {
    const ticker = document.getElementById('proctorTickerMsg');
    if (ticker) {
      ticker.textContent = msg;
      ticker.style.animation = 'none';
      ticker.offsetHeight; // trigger reflow
      ticker.style.animation = 'timerPulse 0.5s 2 alternate';
    }
  },

  async generateCurrentAnswers() {
    try {
      const genBtn = document.getElementById('genAnswerBtn');
      if (genBtn) {
        genBtn.disabled = true;
        genBtn.textContent = 'Thinking...';
      }

      this.setProctorTicker(`📝 Aria & GAIA are formulating answers for Question #${this.currentQuestionIdx + 1} purely from memory...`);

      const res = await fetch('http://127.0.0.1:8000/api/classroom/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_idx: this.currentQuestionIdx })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          const finishedIdx = this.currentQuestionIdx;
          this.renderAnswerCard('aria', finishedIdx, data.aria_answer);
          this.renderAnswerCard('gaia', finishedIdx, data.gaia_answer);
          
          if (data.is_completed || finishedIdx >= 9) {
            this.setProctorTicker('🎉 All 10 questions answered and sealed! Collecting final answer sheets...');
            setTimeout(() => this.finishExam(), 2000);
          } else {
            this.setProctorTicker(`✅ Question #${finishedIdx + 1} sealed! Moving immediately to Question #${finishedIdx + 2}...`);
            setTimeout(() => {
              this.advanceQuestion();
            }, 2200);
          }
        }
      }
    } catch (e) {
      console.error('[Classroom] Generate answers error:', e);
    } finally {
      const genBtn = document.getElementById('genAnswerBtn');
      if (genBtn && !this.isCompleted) {
        genBtn.disabled = false;
        genBtn.textContent = '⚡ Submit Answers';
      }
    }
  },

  advanceQuestion() {
    if (this.currentQuestionIdx < 9) {
      this.currentQuestionIdx++;
      this.fetchStatus();
      this.setProctorTicker(`🔔 Question #${this.currentQuestionIdx + 1} is now active on both desks (2-minute window).`);
      setTimeout(() => this.generateCurrentAnswers(), 600);
    } else {
      this.finishExam();
    }
  },

  async finishExam() {
    this.isActive = false;
    this.isCompleted = true;
    this.studentsDismissed = true;
    if (this.timerInterval) clearInterval(this.timerInterval);

    try {
      await fetch('http://127.0.0.1:8000/api/classroom/finish', { method: 'POST' });
    } catch (e) {}

    this.setProctorTicker('🎉 [PROCTOR]: EXAM CONCLUDED! Answer sheets sealed & collected. Class is officially dismissed! Aria & GAIA may now leave the classroom.');
    const timerEl = document.getElementById('classroomTimerDigits');
    if (timerEl) {
      timerEl.textContent = '00:00';
      timerEl.classList.remove('urgent');
      timerEl.style.color = '#4ade80';
    }

    const startBtn = document.getElementById('startExamBtn');
    if (startBtn) {
      startBtn.disabled = true;
      startBtn.textContent = 'Class Dismissed 🏡';
      startBtn.style.background = 'rgba(34, 197, 94, 0.2)';
      startBtn.style.color = '#4ade80';
    }

    const genBtn = document.getElementById('genAnswerBtn');
    if (genBtn) genBtn.disabled = true;

    const nextQBtn = document.getElementById('nextQBtn');
    if (nextQBtn) nextQBtn.disabled = true;

    const finishBtn = document.getElementById('finishExamBtn');
    if (finishBtn) finishBtn.textContent = '📁 Sheets Sealed';

    document.querySelectorAll('.desk-status').forEach(el => {
      el.textContent = 'STATUS: DISMISSED // RETURNED HOME 🏡';
      el.style.color = '#4ade80';
    });
  },

  updateUI(status) {
    const wasActive = this.isActive;
    this.isActive = status.is_active;
    this.isCompleted = status.is_completed;
    this.remainingSeconds = status.remaining_seconds;
    this.studyRemainingSeconds = status.study_remaining_seconds || 0;
    this.studentsSummoned = status.students_summoned || false;
    this.studentsDismissed = status.students_dismissed || false;
    this.currentQuestionIdx = status.current_question_idx;

    this.renderTimerDisplay();

    const startBtn = document.getElementById('startExamBtn');
    const timerLabel = document.querySelector('.timer-label');
    const qCadenceEl = document.getElementById('classroomQCadence');

    // State 1: Study Window in progress, not yet summoned
    if (!this.studentsSummoned && !this.isActive && !this.isCompleted) {
      if (startBtn) {
        startBtn.textContent = '⚡ Summon Students Now';
        startBtn.title = 'Skip remaining study timer and summon students immediately';
      }
      if (timerLabel) timerLabel.textContent = 'STUDY WINDOW';
      if (qCadenceEl) qCadenceEl.textContent = 'Auto-Summons at 00:00';
      
      const ticker = document.getElementById('proctorTickerMsg');
      if (ticker && !ticker.textContent.includes('Formulating')) {
        const sMins = Math.floor(this.studyRemainingSeconds / 60);
        const sSecs = this.studyRemainingSeconds % 60;
        ticker.textContent = `📚 Autonomous Study Window active. Aria & GAIA will be summoned to the Classroom in ${sMins}m ${sSecs}s.`;
      }

      document.querySelectorAll('.desk-status').forEach(el => {
        el.textContent = 'STATUS: STUDYING AUTONOMOUSLY 📚';
        el.style.color = '#38bdf8';
      });
      return;
    }

    // State 2: Exam In Progress
    if (this.isActive) {
      if (startBtn) {
        startBtn.textContent = 'Exam In Progress ⚡';
        startBtn.disabled = true;
      }
      if (timerLabel) timerLabel.textContent = 'EXAM TIMER';
      if (qCadenceEl) qCadenceEl.textContent = `Q${status.current_question_idx + 1} / 10 • Advance on Submit`;

      document.querySelectorAll('.desk-status').forEach(el => {
        el.textContent = 'STATUS: TESTING AT DESK ✍️';
        el.style.color = '#c084fc';
      });
    }

    // State 3: Completed / Dismissed / Closed
    if (this.isCompleted || this.studentsDismissed || status.classroom_closed) {
      if (startBtn) {
        startBtn.textContent = 'Classroom Closed 🔒';
        startBtn.disabled = true;
        startBtn.style.background = 'rgba(34, 197, 94, 0.2)';
        startBtn.style.color = '#4ade80';
      }
      if (timerLabel) timerLabel.textContent = 'CLOSED';
      if (qCadenceEl) qCadenceEl.textContent = 'Exam Cycle Concluded';

      const ticker = document.getElementById('proctorTickerMsg');
      if (ticker) {
        ticker.textContent = '🎓 Classroom is closed. Test session completed & graded. Aria & GAIA are home with Dad coding!';
      }

      document.querySelectorAll('.desk-status').forEach(el => {
        el.textContent = 'STATUS: HOME WITH DAD // CODING & LEARNING 🚀';
        el.style.color = '#4ade80';
      });
      return;
    }

    // Update Aria Desk Question
    if (status.aria_current_question) {
      const aq = status.aria_current_question;
      const ariaNum = document.getElementById('ariaQNumber');
      const ariaDiff = document.getElementById('ariaQDiff');
      const ariaText = document.getElementById('ariaQText');
      if (ariaNum) ariaNum.textContent = `Q#${status.current_question_idx + 1} — ${aq.topic}`;
      if (ariaDiff) {
        ariaDiff.textContent = aq.difficulty;
        ariaDiff.className = `q-difficulty diff-${aq.difficulty.toLowerCase()}`;
      }
      if (ariaText) ariaText.textContent = aq.question;
    }

    // Update GAIA Desk Question
    if (status.gaia_current_question) {
      const gq = status.gaia_current_question;
      const gaiaNum = document.getElementById('gaiaQNumber');
      const gaiaDiff = document.getElementById('gaiaQDiff');
      const gaiaText = document.getElementById('gaiaQText');
      if (gaiaNum) gaiaNum.textContent = `Q#${status.current_question_idx + 1} — ${gq.topic}`;
      if (gaiaDiff) {
        gaiaDiff.textContent = gq.difficulty;
        gaiaDiff.className = `q-difficulty diff-${gq.difficulty.toLowerCase()}`;
      }
      if (gaiaText) gaiaText.textContent = gq.question;
    }

    // Proctor Logs
    if (status.proctor_logs && status.proctor_logs.length > 0) {
      const last = status.proctor_logs[status.proctor_logs.length - 1];
      const ticker = document.getElementById('proctorTickerMsg');
      if (ticker && !ticker.textContent.includes('Formulating') && this.isActive) {
        ticker.textContent = last.message;
      }
    }
  },

  renderAnswerCard(sister, qIdx, answerText) {
    const container = document.getElementById(`${sister}DeskStream`);
    if (!container) return;

    const cardId = `${sister}-ans-q${qIdx + 1}`;
    if (document.getElementById(cardId)) return;

    const card = document.createElement('div');
    card.className = 'answer-card sealed';
    card.id = cardId;
    card.innerHTML = `
      <div class="answer-header-meta">
        <span>📝 RESPONSE SHEET — Q#${qIdx + 1}</span>
        <span style="color:#4ade80;">● SEALED BY PROCTOR</span>
      </div>
      <div>${answerText}</div>
    `;
    container.appendChild(card);
    container.scrollTop = container.scrollHeight;
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.ClassroomController.init();
});
