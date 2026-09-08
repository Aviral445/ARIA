/**
 * orb.js — Relativistic Accretion Disk / Neural Core Canvas Animation
 * Faithful 1:1 elevation of Aria's Black Hole & Neural Core simulation in 60 FPS Canvas
 */

class NeuralOrb {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.phase = 0;
    this.status = 'idle'; // 'idle', 'running', 'listening', 'speaking'
    this.audioLevel = 0;

    this.stars = [];
    for (let i = 0; i < 40; i++) {
      this.stars.push({
        x: Math.random(),
        y: Math.random(),
        size: Math.random() * 1.5 + 0.5,
        alpha: Math.random() * 0.7 + 0.3
      });
    }

    this.ribbonPts = [];
    const colKeys = ['#00f2fe', '#8b5cf6', '#4facfe', '#f43f5e', '#a78bfa', '#22d3ee'];
    for (let i = 0; i < 50; i++) {
      this.ribbonPts.push({
        angle: (i / 50) * Math.PI * 2,
        speed: 0.02 + Math.random() * 0.025,
        radius: 0.7 + Math.random() * 0.7,
        phase: Math.random() * Math.PI * 2,
        color: colKeys[i % colKeys.length],
        size: Math.random() * 2 + 1
      });
    }

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    this.width = this.canvas.width = rect.width * (window.devicePixelRatio || 1);
    this.height = this.canvas.height = rect.height * (window.devicePixelRatio || 1);
  }

  setStatus(st) {
    this.status = st;
  }

  setAudioLevel(lvl) {
    this.audioLevel = Math.min(1, Math.max(0, lvl));
  }

  animate() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) * 0.28 * (1 + this.audioLevel * 0.35);

    this.phase += 0.04;
    ctx.clearRect(0, 0, w, h);

    // Dynamic glow color
    let glow = '#00f2fe';
    if (this.status === 'speaking') glow = '#f43f5e';
    else if (this.status === 'listening') glow = '#00f2fe';
    else if (this.status === 'running') glow = '#8b5cf6';
    else glow = '#334155';

    // 1. Background Stars
    this.stars.forEach(st => {
      ctx.fillStyle = `rgba(240, 240, 255, ${st.alpha * (0.6 + Math.sin(this.phase + st.x * 10) * 0.4)})`;
      ctx.beginPath();
      ctx.arc(st.x * w, st.y * h, st.size, 0, Math.PI * 2);
      ctx.fill();
    });

    // 2. Diffuse Ambient Glow Behind Singularity
    const ambGrad = ctx.createRadialGradient(cx, cy, r * 0.2, cx, cy, r * 1.6);
    ambGrad.addColorStop(0, glow + '44');
    ambGrad.addColorStop(0.7, glow + '11');
    ambGrad.addColorStop(1, 'transparent');
    ctx.fillStyle = ambGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, r * 1.6, 0, Math.PI * 2);
    ctx.fill();

    // 3. Relativistic Accretion Jets & Ribbons
    this.ribbonPts.forEach(pt => {
      pt.angle += pt.speed * 1.2;
      const wobble = Math.sin(this.phase * 2.5 + pt.phase) * 0.25;
      const effR = (r + 14) * pt.radius * (1 + wobble + this.audioLevel * 0.2);
      const px = cx + effR * Math.cos(pt.angle);
      const py = cy + effR * Math.sin(pt.angle) * 0.38;

      ctx.fillStyle = pt.color;
      ctx.shadowColor = pt.color;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(px, py, pt.size * (window.devicePixelRatio || 1), 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    // 4. Photon Ring
    const photonR = r * 0.9 + Math.sin(this.phase * 3) * 3;
    ctx.strokeStyle = glow;
    ctx.lineWidth = 2.5 * (window.devicePixelRatio || 1);
    ctx.shadowColor = glow;
    ctx.shadowBlur = 14;
    ctx.beginPath();
    ctx.arc(cx, cy, photonR, 0, Math.PI * 2);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // 5. Singularity Core (Deep Relativistic Void with Lensing Gradient)
    const coreR = r * 0.74;
    const coreGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
    coreGrad.addColorStop(0, 'rgba(3, 4, 8, 0.88)');
    coreGrad.addColorStop(0.75, 'rgba(4, 7, 15, 0.80)');
    coreGrad.addColorStop(1, 'rgba(6, 12, 24, 0.62)');
    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
    ctx.fill();

    // 6. Laser Horizon Beam Across Singularity
    const beamW = r * 1.4;
    ctx.strokeStyle = glow;
    ctx.lineWidth = 2 * (window.devicePixelRatio || 1);
    ctx.shadowColor = glow;
    ctx.shadowBlur = 10;
    ctx.beginPath();
    ctx.moveTo(cx - beamW, cy);
    ctx.lineTo(cx + beamW, cy);
    ctx.stroke();
    ctx.shadowBlur = 0;

    requestAnimationFrame(() => this.animate());
  }
}

window.NeuralOrb = NeuralOrb;
