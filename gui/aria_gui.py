"""
gui/aria_gui.py — Professional Desktop AI Workstation GUI for Aria
Features:
  • 3-Tier Professional Layout (Slim Nav-Rail + Command/Telemetry Sidebar + Modular Workspace)
  • 10 Dedicated Dashboards (Home, Pro Chat, Screen Vision Lab, Agent Swarm, NVIDIA NIM 40 RPM Hub,
    System Automation, Memory Vault, Chrome Studio, Analytics, Settings)
  • Real-Time Black Hole / Neural Core Orb Animation (Audio-Reactive)
  • Live Hardware Telemetry (CPU, RAM, Battery, Latency)
  • Pro Chat Studio with Markdown Code Blocks, Cognitive Model Switcher & Context Attachments
  • NVIDIA NIM 40 RPM Live Rate Limiter Gauge & Diagnostics
  • Multi-Theme Engine (Obsidian Stealth, Cyber Purple, Neon Cyan, Emerald Matrix, Sunset Amber)
"""

import os
import sys
import math
import time
import json
import re
import random
import socket
import threading
import subprocess
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Any, Optional

# Ensure all sub-packages are discoverable on sys.path
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for _sub in [
    _ROOT_DIR,
    os.path.join(_ROOT_DIR, "core"),
    os.path.join(_ROOT_DIR, "tools"),
    os.path.join(_ROOT_DIR, "server"),
    os.path.join(_ROOT_DIR, "mcp"),
    os.path.join(_ROOT_DIR, "gui"),
]:
    if _sub not in sys.path:
        sys.path.insert(0, _sub)

try:
    from core.paths import get_data_file, get_config_file, ROOT_DIR, DATA_DIR, CONFIG_DIR, ENV_FILE
except ImportError:
    from paths import get_data_file, get_config_file, ROOT_DIR, DATA_DIR, CONFIG_DIR, ENV_FILE

try:
    from dotenv import load_dotenv, set_key
    load_dotenv(ENV_FILE)
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False


# ── CONFIGURATION & PROFILE ──────────────────────────────────────────────────
PROFILE_FILE = get_data_file("profile.json", create_if_missing=True)
AGENT_FILE   = os.path.join(ROOT_DIR, "agent.py")
CONFIG_FILE  = get_config_file("gui_config.json")

def load_profile() -> dict:
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"name": "Friend", "preferences": [], "notes": [], "system_prompt": ""}

def save_profile(p: dict):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)

def load_config() -> dict:
    c = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            c = {}
    defaults = {
        "theme": "obsidian_stealth",
        "voice_rate": 2,
        "agent_name": "Aria",
        "model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "voice": "Microsoft Zira Desktop",
        "whisper_model": "small",
        "auto_web_search": True,
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
        "nvidia_api_key": os.environ.get("NVIDIA_API_KEY", ""),
        "ctx_active_window": True,
        "ctx_clipboard": True,
        "ctx_running_apps": True,
        "ctx_system_stats": True,
        "ctx_screen_ocr": False,
        "chrome_use_profile": True,
        "chrome_headless": False,
    }
    for k, v in defaults.items():
        c.setdefault(k, v)
    return c

def save_config(c: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)


# ── THEME PALETTES ────────────────────────────────────────────────────────────
THEMES = {
    "obsidian_stealth": {
        "name": "Obsidian Stealth",
        "BG_DEEP": "#07090e",
        "BG_MID": "#0d111a",
        "BG_PANEL": "#111723",
        "CARD": "#141c2b",
        "CARD2": "#1a2438",
        "CARD_HOVER": "#22304a",
        "BORDER": "#222f46",
        "GLOW": "#00f2fe",
        "GLOW2": "#4facfe",
        "CYAN": "#00f2fe",
        "PINK": "#f43f5e",
        "VIOLET": "#8b5cf6",
        "LAVENDER": "#cbd5e1",
        "WHITE": "#f8fafc",
        "GREY": "#64748b",
        "DGREY": "#334155",
        "AMBER": "#f59e0b",
        "SUCCESS": "#10b981",
        "GREEN": "#10b981",
        "NVIDIA": "#76b900"
    },
    "cyber_purple": {
        "name": "Cyber Purple",
        "BG_DEEP": "#050510",
        "BG_MID": "#0a0a20",
        "BG_PANEL": "#0d0d25",
        "CARD": "#12122a",
        "CARD2": "#16163a",
        "CARD_HOVER": "#20204d",
        "BORDER": "#1e1e45",
        "GLOW": "#6c3bff",
        "GLOW2": "#3b82f6",
        "CYAN": "#22d3ee",
        "PINK": "#ec4899",
        "VIOLET": "#8b5cf6",
        "LAVENDER": "#a78bfa",
        "WHITE": "#f0f0ff",
        "GREY": "#6b7280",
        "DGREY": "#374151",
        "AMBER": "#f59e0b",
        "SUCCESS": "#10b981",
        "GREEN": "#10b981",
        "NVIDIA": "#76b900"
    },
    "neon_cyan": {
        "name": "Neon Cyan",
        "BG_DEEP": "#030f14",
        "BG_MID": "#061820",
        "BG_PANEL": "#08212b",
        "CARD": "#0c2b38",
        "CARD2": "#103646",
        "CARD_HOVER": "#16475c",
        "BORDER": "#174a5f",
        "GLOW": "#06b6d4",
        "GLOW2": "#38bdf8",
        "CYAN": "#22d3ee",
        "PINK": "#f43f5e",
        "VIOLET": "#0ea5e9",
        "LAVENDER": "#7dd3fc",
        "WHITE": "#f0fdfa",
        "GREY": "#64748b",
        "DGREY": "#334155",
        "AMBER": "#fbbf24",
        "SUCCESS": "#14b8a6",
        "GREEN": "#14b8a6",
        "NVIDIA": "#76b900"
    },
    "emerald_matrix": {
        "name": "Emerald Matrix",
        "BG_DEEP": "#02120a",
        "BG_MID": "#051c11",
        "BG_PANEL": "#082618",
        "CARD": "#0c301f",
        "CARD2": "#103d28",
        "CARD_HOVER": "#165035",
        "BORDER": "#165337",
        "GLOW": "#10b981",
        "GLOW2": "#059669",
        "CYAN": "#34d399",
        "PINK": "#f43f5e",
        "VIOLET": "#6ee7b7",
        "LAVENDER": "#a7f3d0",
        "WHITE": "#ecfdf5",
        "GREY": "#6b7280",
        "DGREY": "#374151",
        "AMBER": "#f59e0b",
        "SUCCESS": "#22c55e",
        "GREEN": "#22c55e",
        "NVIDIA": "#76b900"
    },
    "sunset_amber": {
        "name": "Sunset Amber",
        "BG_DEEP": "#140a05",
        "BG_MID": "#20120a",
        "BG_PANEL": "#2b180e",
        "CARD": "#382013",
        "CARD2": "#462818",
        "CARD_HOVER": "#58331f",
        "BORDER": "#5f3822",
        "GLOW": "#f97316",
        "GLOW2": "#ef4444",
        "CYAN": "#f59e0b",
        "PINK": "#ec4899",
        "VIOLET": "#fb923c",
        "LAVENDER": "#fed7aa",
        "WHITE": "#fff7ed",
        "GREY": "#78716c",
        "DGREY": "#44403c",
        "AMBER": "#f59e0b",
        "SUCCESS": "#84cc16",
        "GREEN": "#84cc16",
        "NVIDIA": "#76b900"
    }
}


# ── COLOR & CANVAS UTILITIES ─────────────────────────────────────────────────
def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join([c*2 for c in h])
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, int(r))):02x}{max(0, min(255, int(g))):02x}{max(0, min(255, int(b))):02x}"

def blend(c1: str, c2: str, t: float) -> str:
    """Blends two hex colors by factor t (0.0 to 1.0)."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)

def make_scrollable(parent, bg: str):
    """Creates a smooth scrollable canvas container with auto-updating scrollregion."""
    c = tk.Canvas(parent, bg=bg, highlightthickness=0, bd=0)
    sb = tk.Scrollbar(parent, orient="vertical", command=c.yview, width=6, bg=bg, troughcolor=bg)
    c.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    c.pack(side="left", fill="both", expand=True)

    inner = tk.Frame(c, bg=bg)
    win_id = c.create_window((0, 0), window=inner, anchor="nw")

    def _configure_inner(e):
        c.configure(scrollregion=c.bbox("all"))

    def _configure_canvas(e):
        c.itemconfig(win_id, width=e.width)

    inner.bind("<Configure>", _configure_inner)
    c.bind("<Configure>", _configure_canvas)

    def _wheel(e):
        step = -2 if e.delta > 0 else 2
        c.yview_scroll(step, "units")
        return "break"

    c.bind("<MouseWheel>", _wheel)
    inner.bind("<MouseWheel>", _wheel)
    return c, inner


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN ARIA DESKTOP GUI CLASS
# ═════════════════════════════════════════════════════════════════════════════
class AriaApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ARIA — Autonomous AI Pro Workstation")
        self.root.geometry("1440x880")
        self.root.minsize(1120, 720)

        self.config = load_config()
        self.profile = load_profile()
        theme_key = self.config.get("theme", "obsidian_stealth")
        self.pal = THEMES.get(theme_key, THEMES["obsidian_stealth"])
        self.root.configure(bg=self.pal["BG_DEEP"])

        # Runtime Flags
        self.agent_proc = None
        self.is_running = False
        self.is_speaking = False
        self.is_listening = False
        self.anim_running = True
        self.active_page = "home"
        self.chat_history: List[Dict[str, str]] = []
        self.phase = 0.0
        self.pulses = []
        self.stars = [
            {"x": random.random(), "y": random.random(), "r": random.uniform(0.6, 2.2), "bright": random.random()}
            for _ in range(110)
        ]
        self.ribbon_pts = [
            {
                "angle": random.uniform(0, math.pi * 2),
                "radius": random.uniform(0.6, 1.2),
                "speed": random.uniform(0.02, 0.05),
                "phase": random.uniform(0, math.pi * 2),
                "col_key": random.choice(["GLOW", "GLOW2", "CYAN", "PINK", "VIOLET", "NVIDIA"])
            }
            for _ in range(12)
        ]

        # Style ttk Combobox to dark theme
        try:
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("TCombobox",
                fieldbackground=self.pal["CARD2"],
                background=self.pal["CARD"],
                foreground=self.pal["WHITE"],
                darkcolor=self.pal["BORDER"],
                lightcolor=self.pal["BORDER"],
                arrowcolor=self.pal["CYAN"],
                bordercolor=self.pal["BORDER"]
            )
            style.map("TCombobox",
                fieldbackground=[("readonly", self.pal["CARD2"])],
                foreground=[("readonly", self.pal["WHITE"])],
                selectbackground=[("readonly", self.pal["CARD2"])],
                selectforeground=[("readonly", self.pal["CYAN"])]
            )
        except Exception:
            pass

        # Bind universal mousewheel
        self._bind_mousewheel()

        # Initialize Services
        self._init_mobile_server()

        # Build 3-Tier Layout
        self._build_layout()

        # Start background threads
        self._animate_orb()
        self._start_system_monitor()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_mousewheel(self):
        def _global_mousewheel(event):
            try:
                step = -2 if event.delta > 0 else 2
                w = self.root.winfo_containing(event.x_root, event.y_root)
                while w:
                    if isinstance(w, tk.Canvas) and hasattr(w, "yview_scroll"):
                        if w != getattr(self, "sc", None) and w != getattr(self, "nav_dot_c", None):
                            w.yview_scroll(step, "units")
                            return "break"
                    w = getattr(w, "master", None)
            except Exception:
                pass
        self.root.bind_all("<MouseWheel>", _global_mousewheel)

    # ── 3-TIER MASTER LAYOUT ──────────────────────────────────────────────────
    def _build_layout(self):
        # 1. Left Nav Rail (56px)
        self.navbar = tk.Frame(self.root, bg=self.pal["BG_PANEL"], width=64)
        self.navbar.pack(side="left", fill="y")
        self.navbar.pack_propagate(False)

        # 2. Command & Telemetry Sidebar (340px)
        self.sidebar = tk.Frame(self.root, bg=self.pal["BG_MID"], width=360)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Subtle Separator Line
        self.sep = tk.Frame(self.root, bg=self.pal["BORDER"], width=1)
        self.sep.pack(side="left", fill="y")

        # 3. Main Workspace Workspace Area (Fluid Canvas)
        self.workspace = tk.Frame(self.root, bg=self.pal["BG_DEEP"])
        self.workspace.pack(side="left", fill="both", expand=True)

        self._build_nav_rail()
        self._build_sidebar()
        self._build_pages()

    # ── 1. SLIM NAV-RAIL (LEFT) ───────────────────────────────────────────────
    def _build_nav_rail(self):
        n = self.navbar
        pal = self.pal

        # Top Logo Badge
        lc = tk.Canvas(n, width=64, height=58, bg=pal["BG_PANEL"], highlightthickness=0)
        lc.pack(pady=(8, 4))
        lc.create_oval(16, 12, 48, 44, fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.7), outline=pal["GLOW"], width=1)
        lc.create_text(32, 28, text="A", font=("Segoe UI", 14, "bold"), fill=pal["WHITE"])

        tk.Frame(n, bg=pal["BORDER"], height=1).pack(fill="x", padx=8, pady=4)

        self._nav_items = [
            ("⌂", "home", "Home"),
            ("💬", "chat", "Chat"),
            ("📱", "phone", "Phone"),
            ("👁", "vision", "Vision"),
            ("🤖", "agents", "Swarm"),
            ("⚡", "nvidia", "NVIDIA"),
            ("🛡", "gaia", "GAIA"),
            ("🖥", "system", "System"),
            ("🧠", "memory", "Memory"),
            ("🌐", "browser", "Web"),
            ("📊", "analytics", "Stats"),
            ("⚙", "settings", "Config"),
        ]

        self.nav_btns = {}
        for icon, pid, label in self._nav_items:
            c = tk.Canvas(n, width=64, height=44, bg=pal["BG_PANEL"], highlightthickness=0, cursor="hand2")
            c.pack(pady=1)
            self._draw_nav_btn(c, icon, label, pid, pid == "home")
            c.bind("<Button-1>", lambda e, p=pid: self._nav(p))
            c.bind("<Enter>", lambda e, c_=c, i=icon, l=label, p=pid: self._draw_nav_btn(c_, i, l, p, p == self.active_page, True))
            c.bind("<Leave>", lambda e, c_=c, i=icon, l=label, p=pid: self._draw_nav_btn(c_, i, l, p, p == self.active_page, False))
            self.nav_btns[pid] = (c, icon, label)

        # Bottom Status Dot & Theme Switcher
        tk.Frame(n, bg=pal["BORDER"], height=1).pack(side="bottom", fill="x", padx=8, pady=4)
        
        self.nav_dot_c = tk.Canvas(n, width=64, height=44, bg=pal["BG_PANEL"], highlightthickness=0)
        self.nav_dot_c.pack(side="bottom", pady=(0, 4))
        self.nav_dot_c.create_oval(26, 6, 38, 18, fill=pal["DGREY"], outline="", tags="dot")
        self.nav_dot_c.create_text(32, 28, text="IDLE", font=("Segoe UI", 8, "bold"), fill=pal["GREY"], tags="lbl")

        # Theme Cycle Button
        theme_btn = tk.Button(
            n, text="🎨", font=("Segoe UI", 11), bg=pal["BG_PANEL"], fg=pal["LAVENDER"],
            relief="flat", bd=0, cursor="hand2", activebackground=pal["CARD"],
            command=self._cycle_theme
        )
        theme_btn.pack(side="bottom", pady=(0, 4))

    def _draw_nav_btn(self, c: tk.Canvas, icon: str, label: str, pid: str, active: bool = False, hover: bool = False):
        pal = self.pal
        c.delete("all")
        if active:
            c.create_rectangle(0, 0, 64, 44, fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.85), outline="")
            c.create_rectangle(0, 4, 3, 40, fill=pal["GLOW"], outline="")
        elif hover:
            c.create_rectangle(0, 0, 64, 44, fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.93), outline="")
        else:
            c.create_rectangle(0, 0, 64, 44, fill=pal["BG_PANEL"], outline="")

        col = pal["WHITE"] if active else (pal["LAVENDER"] if hover else pal["GREY"])
        c.create_text(32, 16, text=icon, font=("Segoe UI", 13), fill=col)
        c.create_text(32, 32, text=label, font=("Segoe UI", 8, "bold"), fill=col)

    def _nav(self, page_id: str):
        self.active_page = page_id
        for pid, (c, icon, label) in self.nav_btns.items():
            self._draw_nav_btn(c, icon, label, pid, pid == page_id)
        for pid, frame in self.pages.items():
            if pid == page_id:
                frame.lift()
                if hasattr(frame, "_scroll_canvas"):
                    frame._scroll_canvas.yview_moveto(0.0)
                if hasattr(frame, "on_show"):
                    frame.on_show()

    def _cycle_theme(self):
        theme_keys = list(THEMES.keys())
        cur_key = self.config.get("theme", "obsidian_stealth")
        next_idx = (theme_keys.index(cur_key) + 1) % len(theme_keys) if cur_key in theme_keys else 0
        new_theme = theme_keys[next_idx]
        self.config["theme"] = new_theme
        save_config(self.config)
        self.pal = THEMES[new_theme]
        self.root.configure(bg=self.pal["BG_DEEP"])
        self._refresh_all_styles()

    def _refresh_all_styles(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self._build_layout()

    # ── 2. COMMAND & TELEMETRY SIDEBAR ────────────────────────────────────────
    def _build_sidebar(self):
        s = self.sidebar
        pal = self.pal

        # 1. Header & Version Badge
        hdr = tk.Frame(s, bg=pal["BG_MID"], padx=16, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ARIA PRO", font=("Segoe UI", 14, "bold"), bg=pal["BG_MID"], fg=pal["WHITE"]).pack(side="left")
        
        badge = tk.Frame(hdr, bg=pal["CARD2"], padx=8, pady=3)
        badge.pack(side="right")
        tk.Label(badge, text="v5.0 SINGULARITY", font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=pal["CYAN"]).pack()

        # 2. Black Hole Singularity Canvas (210px)
        self.sc = tk.Canvas(s, width=340, height=210, bg=pal["BG_MID"], highlightthickness=0)
        self.sc.pack(pady=(0, 4))

        # Status Pill under Orb
        self.status_pill = tk.Frame(s, bg=pal["CARD2"], padx=14, pady=4)
        self.status_pill.pack(pady=(0, 8))
        self.status_dot = tk.Label(self.status_pill, text="●", font=("Segoe UI", 9), bg=pal["CARD2"], fg=pal["GLOW"])
        self.status_dot.pack(side="left", padx=(0, 6))
        self.status_text = tk.Label(self.status_pill, text="STANDBY // IDLE", font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        self.status_text.pack(side="left")

        # 3. Master Launch / Stop Button
        self.start_btn = tk.Button(
            s, text="▶   LAUNCH ARIA AGENT", font=("Segoe UI", 11, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"],
            activebackground=pal["GLOW2"], activeforeground=pal["WHITE"],
            relief="flat", bd=0, pady=7, cursor="hand2",
            command=self._toggle_agent
        )
        self.start_btn.pack(fill="x", padx=16, pady=(0, 8))

        # 4. Hardware Telemetry Card
        telem_card = tk.Frame(s, bg=pal["CARD"], padx=12, pady=10)
        telem_card.pack(fill="x", padx=16, pady=(0, 8))
        
        t_hdr = tk.Frame(telem_card, bg=pal["CARD"])
        t_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(t_hdr, text="SYSTEM TELEMETRY", font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["GREY"]).pack(side="left")
        self.ping_lbl = tk.Label(t_hdr, text="● 24ms", font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["CYAN"])
        self.ping_lbl.pack(side="right")

        # Grid of 2x2 stats
        grid = tk.Frame(telem_card, bg=pal["CARD"])
        grid.pack(fill="x")
        self.cpu_lbl = self._mini_stat(grid, 0, 0, "CPU LOAD", "14%", pal["CYAN"])
        self.ram_lbl = self._mini_stat(grid, 0, 1, "RAM USAGE", "48%", pal["VIOLET"])
        self.rpm_lbl = self._mini_stat(grid, 1, 0, "NVIDIA RPM", "0 / 40", pal["NVIDIA"])
        self.bat_lbl = self._mini_stat(grid, 1, 1, "BATTERY", "100%", pal["GREEN"])

        # 5. Quick Command Launcher
        cmd_box = tk.Frame(s, bg=pal["CARD2"], padx=10, pady=6)
        cmd_box.pack(fill="x", padx=16, pady=(0, 8))
        
        self.quick_cmd_entry = tk.Entry(
            cmd_box, font=("Segoe UI", 10), bg=pal["CARD2"], fg=pal["WHITE"],
            insertbackground=pal["CYAN"], relief="flat", bd=0
        )
        self.quick_cmd_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.quick_cmd_entry.bind("<Return>", lambda e: self._send_quick_command())
        self.quick_cmd_entry.insert(0, "Quick prompt / task...")
        self.quick_cmd_entry.config(fg=pal["GREY"])

        def _focus_in(e):
            if self.quick_cmd_entry.get() == "Quick prompt / task...":
                self.quick_cmd_entry.delete(0, "end")
                self.quick_cmd_entry.config(fg=pal["WHITE"])
        def _focus_out(e):
            if not self.quick_cmd_entry.get():
                self.quick_cmd_entry.insert(0, "Quick prompt / task...")
                self.quick_cmd_entry.config(fg=pal["GREY"])
        self.quick_cmd_entry.bind("<FocusIn>", _focus_in)
        self.quick_cmd_entry.bind("<FocusOut>", _focus_out)

        tk.Button(
            cmd_box, text="➤", font=("Segoe UI", 10, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=8, cursor="hand2",
            command=self._send_quick_command
        ).pack(side="left", padx=(4, 0))

        # 6. Mobile Companion Server Card
        srv_card = tk.Frame(s, bg=pal["CARD"], padx=12, pady=10)
        srv_card.pack(fill="x", padx=16, pady=(0, 6))

        s_hdr = tk.Frame(srv_card, bg=pal["CARD"])
        s_hdr.pack(fill="x")
        tk.Label(s_hdr, text="📱 MOBILE LAN COMPANION", font=("Segoe UI", 9, "bold"), bg=pal["CARD"], fg=pal["CYAN"]).pack(side="left")
        self.srv_state_lbl = tk.Label(s_hdr, text="● ONLINE", font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["GREEN"])
        self.srv_state_lbl.pack(side="right")

        self.srv_url_text = tk.Label(
            srv_card, text=getattr(self, "mobile_server_url", "http://0.0.0.0:8765"),
            font=("Segoe UI", 10, "bold"), bg=pal["CARD"], fg=pal["WHITE"], cursor="hand2"
        )
        self.srv_url_text.pack(anchor="w", pady=(4, 6))
        self.srv_url_text.bind("<Button-1>", lambda e: self._copy_mobile_server_url())

        s_btns = tk.Frame(srv_card, bg=pal["CARD"])
        s_btns.pack(fill="x")
        self.toggle_srv_btn = tk.Button(
            s_btns, text="TOGGLE", font=("Segoe UI", 8, "bold"), bg=pal["BG_MID"], fg=pal["LAVENDER"],
            relief="flat", bd=0, pady=4, padx=6, cursor="hand2", command=self._toggle_mobile_server
        )
        self.toggle_srv_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))

        tk.Button(
            s_btns, text="COPY", font=("Segoe UI", 8, "bold"), bg=pal["BG_MID"], fg=pal["LAVENDER"],
            relief="flat", bd=0, pady=4, padx=8, cursor="hand2", command=self._copy_mobile_server_url
        ).pack(side="left", padx=3)

        tk.Button(
            s_btns, text="OPEN", font=("Segoe UI", 8, "bold"), bg=pal["BG_MID"], fg=pal["CYAN"],
            relief="flat", bd=0, pady=4, padx=8, cursor="hand2", command=self._open_mobile_server_browser
        ).pack(side="left", padx=(3, 0))

    def _mini_stat(self, parent, row: int, col: int, title: str, val: str, accent: str):
        pal = self.pal
        f = tk.Frame(parent, bg=pal["CARD2"], padx=8, pady=6)
        f.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        parent.columnconfigure(col, weight=1)
        tk.Label(f, text=title, font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=pal["GREY"]).pack(anchor="w")
        lbl = tk.Label(f, text=val, font=("Segoe UI", 12, "bold"), bg=pal["CARD2"], fg=accent)
        lbl.pack(anchor="w")
        return lbl

    # ── 3. WORKSPACE DASHBOARDS ───────────────────────────────────────────────
    def _build_pages(self):
        pal = self.pal
        self.pages = {}
        page_ids = ["home", "chat", "phone", "vision", "agents", "nvidia", "gaia", "system", "memory", "browser", "analytics", "settings"]
        for pid in page_ids:
            f = tk.Frame(self.workspace, bg=pal["BG_DEEP"])
            f.place(x=0, y=0, relwidth=1, relheight=1)
            self.pages[pid] = f

        self._pg_home()
        self._pg_chat()
        self._pg_phone()
        self._pg_vision()
        self._pg_agents()
        self._pg_nvidia()
        self._pg_gaia()
        self._pg_system()
        self._pg_memory()
        self._pg_browser()
        self._pg_analytics()
        self._pg_settings()

        self.pages["home"].lift()

    def _page_header(self, parent, title: str, subtitle: str = ""):
        pal = self.pal
        hdr = tk.Frame(parent, bg=pal["BG_MID"], padx=24, pady=14)
        hdr.pack(fill="x")
        
        t_row = tk.Frame(hdr, bg=pal["BG_MID"])
        t_row.pack(fill="x")
        tk.Label(t_row, text=title, font=("Segoe UI", 15, "bold"), bg=pal["BG_MID"], fg=pal["WHITE"]).pack(side="left")
        
        # Engine indicator badge
        eng_badge = tk.Frame(t_row, bg=pal["CARD2"], padx=8, pady=3)
        eng_badge.pack(side="right")
        tk.Label(eng_badge, text="⚡ NVIDIA NIM 40 RPM + GEMINI 2.5", font=("Segoe UI", 7, "bold"), bg=pal["CARD2"], fg=pal["NVIDIA"]).pack()

        if subtitle:
            tk.Label(hdr, text=subtitle, font=("Segoe UI", 8), bg=pal["BG_MID"], fg=pal["GREY"]).pack(anchor="w", pady=(2, 0))
        
        tk.Frame(parent, bg=pal["BORDER"], height=1).pack(fill="x")

    # ── DASHBOARD 1: EXECUTIVE HOME DASHBOARD ─────────────────────────────────
    def _pg_home(self):
        p = self.pages["home"]
        pal = self.pal
        self._page_header(p, "EXECUTIVE DASHBOARD", "Autonomous Operations & Workstation Telemetry")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # 1. Welcome Hero Banner
        hero = tk.Frame(wrap, bg=pal["CARD2"], padx=24, pady=20)
        hero.pack(fill="x", padx=24, pady=(16, 12))
        
        user_name = self.profile.get("name", "Aviral")
        tk.Label(hero, text=f"Welcome back, {user_name}!", font=("Segoe UI", 18, "bold"), bg=pal["CARD2"], fg=pal["WHITE"]).pack(anchor="w")
        tk.Label(hero, text="Aria is operating at full frontier capability with NVIDIA NIM DeepSeek-R1, Screen Vision, and Windows OS Control.",
                 font=("Segoe UI", 9), bg=pal["CARD2"], fg=pal["LAVENDER"]).pack(anchor="w", pady=(4, 12))

        hero_tags = tk.Frame(hero, bg=pal["CARD2"])
        hero_tags.pack(anchor="w")
        for tag, col in [("● NVIDIA NIM 70B Active", pal["NVIDIA"]), ("● Screen Vision Ready", pal["CYAN"]), ("● ChromaDB Memory Synced", pal["VIOLET"]), ("● 40 RPM Guard Paced", pal["AMBER"])]:
            badge = tk.Frame(hero_tags, bg=pal["BG_DEEP"], padx=8, pady=4)
            badge.pack(side="left", padx=(0, 8))
            tk.Label(badge, text=tag, font=("Segoe UI", 7, "bold"), bg=pal["BG_DEEP"], fg=col).pack()

        # 2. Quick Action Launchpad
        tk.Label(wrap, text="🚀 QUICK ACTION LAUNCHPAD", font=("Segoe UI", 9, "bold"), bg=pal["BG_DEEP"], fg=pal["GREY"]).pack(anchor="w", padx=24, pady=(8, 6))

        launch_grid = tk.Frame(wrap, bg=pal["BG_DEEP"])
        launch_grid.pack(fill="x", padx=24, pady=(0, 16))

        actions = [
            ("👁", "Inspect Screen", "Analyze active window & OCR", pal["CYAN"], "vision"),
            ("💬", "AI Chat Studio", "Interactive conversation & reasoning", pal["GLOW"], "chat"),
            ("💻", "Synthesize Script", "Generate PowerShell code via Qwen Coder", pal["NVIDIA"], "system"),
            ("🤖", "Swarm Status", "Inspect multi-agent workflows", pal["VIOLET"], "agents"),
            ("⚡", "NVIDIA RPM Hub", "Rate limiter & model benchmark", pal["AMBER"], "nvidia"),
            ("🧠", "Memory Vault", "Browse timeline & documents", pal["PINK"], "memory"),
        ]

        for i, (icon, title, desc, col, target) in enumerate(actions):
            row = i // 3
            c_idx = i % 3
            card = tk.Frame(launch_grid, bg=pal["CARD"], padx=14, pady=12, cursor="hand2")
            card.grid(row=row, column=c_idx, sticky="nsew", padx=4, pady=4)
            launch_grid.columnconfigure(c_idx, weight=1)
            card.bind("<Button-1>", lambda e, t=target: self._nav(t))

            hdr = tk.Frame(card, bg=pal["CARD"])
            hdr.pack(fill="x")
            tk.Label(hdr, text=icon, font=("Segoe UI", 14), bg=pal["CARD"], fg=col).pack(side="left")
            tk.Label(hdr, text=f"  {title}", font=("Segoe UI", 10, "bold"), bg=pal["CARD"], fg=pal["WHITE"]).pack(side="left")

            tk.Label(card, text=desc, font=("Segoe UI", 8), bg=pal["CARD"], fg=pal["GREY"]).pack(anchor="w", pady=(4, 0))

        # 3. Live System Context Card
        tk.Label(wrap, text="🖥️ LIVE SYSTEM CONTEXT & ACTIVE APPLICATION", font=("Segoe UI", 9, "bold"), bg=pal["BG_DEEP"], fg=pal["GREY"]).pack(anchor="w", padx=24, pady=(0, 6))
        
        ctx_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=12)
        ctx_card.pack(fill="x", padx=24, pady=(0, 24))
        
        self.home_active_win_lbl = tk.Label(ctx_card, text="Focused Window: Visual Studio Code", font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        self.home_active_win_lbl.pack(anchor="w")

        self.home_clipboard_lbl = tk.Label(ctx_card, text="Clipboard: No text copied", font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["LAVENDER"])
        self.home_clipboard_lbl.pack(anchor="w", pady=(4, 0))

    # ── DASHBOARD 2: PRO AI CHAT STUDIO ───────────────────────────────────────
    def _pg_chat(self):
        p = self.pages["chat"]
        pal = self.pal
        self._page_header(p, "PRO AI CHAT STUDIO", "Multi-Turn Interactive Reasoning & Code Generation")

        wrap = tk.Frame(p, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=20, pady=12)

        # Control Bar: 2-Row High-Tech Control Panel
        ctrl_bar = tk.Frame(wrap, bg=pal["BG_MID"], padx=14, pady=8)
        ctrl_bar.pack(fill="x", pady=(0, 8))

        # Row 1: Engine Selector + Status
        top_ctrl = tk.Frame(ctrl_bar, bg=pal["BG_MID"])
        top_ctrl.pack(fill="x", pady=(0, 6))

        tk.Label(top_ctrl, text="⚡ COGNITIVE ENGINE:", font=("Segoe UI", 9, "bold"), bg=pal["BG_MID"], fg=pal["CYAN"]).pack(side="left")
        
        self.chat_model_var = tk.StringVar(value="gemini-2.5-flash")
        models_list = [
            "gemini-2.5-flash",
            "qwen/qwen3.6-27b (Groq Fast)",
            "openai/gpt-oss-120b (Groq High IQ)",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "meta/llama-3.2-11b-vision-instruct",
            "ollama/llama3.2 (Local Offline)"
        ]
        model_dropdown = ttk.Combobox(top_ctrl, textvariable=self.chat_model_var, values=models_list, width=38, state="readonly", font=("Segoe UI", 9))
        model_dropdown.pack(side="left", padx=(8, 16))

        tk.Label(top_ctrl, text="● ADAPTIVE SWARM ACTIVE", font=("Segoe UI", 8, "bold"), bg=pal["BG_MID"], fg=pal["GREEN"]).pack(side="right")

        # Row 2: Action Chips with Icons and Proper Spacing
        chip_bar = tk.Frame(ctrl_bar, bg=pal["BG_MID"])
        chip_bar.pack(fill="x")

        tk.Label(chip_bar, text="QUICK ACTIONS:", font=("Segoe UI", 8, "bold"), bg=pal["BG_MID"], fg=pal["GREY"]).pack(side="left", padx=(0, 6))

        chip_items = [
            ("👁 Screen Vision", "Inspect Screen"),
            ("🪟 Windows", "List Open Windows"),
            ("⚡ NVIDIA RPM", "NVIDIA RPM Stats"),
            ("📋 Clipboard", "Summarize Clipboard"),
            ("📝 Quick Note", "Aria, take a quick note: ")
        ]
        for chip_lbl, prompt_val in chip_items:
            btn = tk.Button(
                chip_bar, text=chip_lbl, font=("Segoe UI", 9, "bold"),
                bg=pal["CARD2"], fg=pal["LAVENDER"], activebackground=pal["CARD_HOVER"], activeforeground=pal["WHITE"],
                relief="flat", bd=0, padx=9, pady=3, cursor="hand2",
                command=lambda p=prompt_val: self._inject_chat_prompt(p)
            )
            btn.pack(side="left", padx=3)

        # Chat Stream Area
        self.chat_canvas = tk.Canvas(wrap, bg=pal["CARD"], highlightthickness=0)
        self.chat_scroll = tk.Scrollbar(wrap, orient="vertical", command=self.chat_canvas.yview, bg=pal["CARD"], troughcolor=pal["BG_DEEP"], width=6)
        self.chat_canvas.configure(yscrollcommand=self.chat_scroll.set)
        
        self.chat_scroll.pack(side="right", fill="y")
        self.chat_canvas.pack(side="top", fill="both", expand=True)

        self.chat_inner = tk.Frame(self.chat_canvas, bg=pal["CARD"])
        self.chat_win_id = self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")

        self.chat_inner.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(self.chat_win_id, width=e.width))

        # Welcome message
        self._append_chat_message("assistant", f"Greetings {self.profile.get('name', 'Friend')}! I am Aria. How can I assist your workflow today?")

        # Input Bar
        in_bar = tk.Frame(wrap, bg=pal["CARD2"], padx=12, pady=8)
        in_bar.pack(fill="x", pady=(8, 0))

        self.chat_main_entry = tk.Entry(
            in_bar, font=("Segoe UI", 11), bg=pal["CARD2"], fg=pal["WHITE"],
            insertbackground=pal["CYAN"], relief="flat", bd=0
        )
        self.chat_main_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(4, 8))
        self.chat_main_entry.bind("<Return>", lambda e: self._send_pro_chat())

        tk.Button(
            in_bar, text="SEND  ➤", font=("Segoe UI", 10, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=14, pady=4, cursor="hand2",
            command=self._send_pro_chat
        ).pack(side="left", padx=2)

        tk.Button(
            in_bar, text="CLEAR", font=("Segoe UI", 9),
            bg=pal["BG_MID"], fg=pal["PINK"], relief="flat", bd=0, padx=8, pady=4, cursor="hand2",
            command=self._clear_chat_stream
        ).pack(side="left", padx=2)

    def _inject_chat_prompt(self, text: str):
        self.chat_main_entry.delete(0, "end")
        self.chat_main_entry.insert(0, text)
        self._send_pro_chat()

    def _append_chat_message(self, role: str, text: str):
        pal = self.pal
        is_user = (role == "user")
        
        # Clean text: strip raw tool call XML artifacts
        if not is_user:
            text = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL)
            text = re.sub(r'<function=.*?</function>', '', text, flags=re.DOTALL)
            text = text.strip()
            if not text:
                text = "Task executed successfully."

        row = tk.Frame(self.chat_inner, bg=pal["CARD"], pady=4)
        row.pack(fill="x", padx=16)

        bubble_bg = blend(pal["GLOW"], pal["CARD2"], 0.22) if is_user else pal["CARD2"]
        align = "e" if is_user else "w"

        bubble = tk.Frame(row, bg=bubble_bg, padx=14, pady=8)
        bubble.pack(anchor=align, padx=4)

        tag_col = pal["CYAN"] if is_user else pal["VIOLET"]
        sender = "You" if is_user else "Aria"
        
        hdr = tk.Frame(bubble, bg=bubble_bg)
        hdr.pack(fill="x", pady=(0, 2))
        tk.Label(hdr, text=sender, font=("Segoe UI", 10, "bold"), bg=bubble_bg, fg=tag_col).pack(side="left")
        time_fg = pal["LAVENDER"] if is_user else pal["GREY"]
        tk.Label(hdr, text=f"  {time.strftime('%I:%M %p')}", font=("Segoe UI", 9), bg=bubble_bg, fg=time_fg).pack(side="left")

        # Formatted Body Text (11pt: clear, readable, zero eye strain)
        msg_lbl = tk.Label(
            bubble, text=text, font=("Segoe UI", 11), bg=bubble_bg, fg=pal["WHITE"],
            wraplength=820, justify="left"
        )
        msg_lbl.pack(anchor="w")

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def _send_pro_chat(self):
        query = self.chat_main_entry.get().strip()
        if not query:
            return
        self.chat_main_entry.delete(0, "end")
        self._append_chat_message("user", query)

        def _worker():
            try:
                import aria_adk
                adk = aria_adk.get_adk_engine()
                selected_model = self.chat_model_var.get().strip()
                reply = adk.run_turn(
                    user_input=query,
                    chat_history=self.chat_history[-6:],
                    user_name=self.profile.get("name", "Friend"),
                    model_override=selected_model
                )
                self.chat_history.append({"role": "user", "content": query})
                self.chat_history.append({"role": "assistant", "content": reply})
                self.root.after(0, lambda: self._append_chat_message("assistant", reply))
            except Exception as e:
                self.root.after(0, lambda: self._append_chat_message("assistant", f"Cognitive error: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    def _clear_chat_stream(self):
        for widget in self.chat_inner.winfo_children():
            widget.destroy()
        self.chat_history.clear()
        self._append_chat_message("assistant", "Chat history cleared. How can I help you?")

    # ── DASHBOARD: WIRELESS ANDROID PHONE CONTROLLER ──────────────────────────
    def _pg_phone(self):
        p = self.pages["phone"]
        pal = self.pal
        self._page_header(p, "WIRELESS ANDROID PHONE CONTROLLER", "Wi-Fi ADB Autonomous Device Control, Auto-Unlock & App Launching")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # 1. Connection & Settings Card
        conn_card = tk.Frame(wrap, bg=pal["CARD2"], padx=18, pady=14)
        conn_card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(conn_card, text="📶 WIRELESS ADB CONNECTION & UNLOCK PIN", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["CYAN"]).pack(anchor="w")

        fields_row = tk.Frame(conn_card, bg=pal["CARD2"])
        fields_row.pack(fill="x", pady=(8, 10))

        # IP Field
        tk.Label(fields_row, text="Phone IP:", font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=pal["LAVENDER"]).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.phone_ip_var = tk.StringVar(value=self.config.get("phone_ip", "192.168.1."))
        self.phone_ip_entry = tk.Entry(fields_row, textvariable=self.phone_ip_var, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"], relief="flat", bd=0, width=16)
        self.phone_ip_entry.grid(row=0, column=1, padx=(0, 12), ipady=4)

        # Port Field
        tk.Label(fields_row, text="Port:", font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=pal["LAVENDER"]).grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.phone_port_var = tk.StringVar(value=str(self.config.get("phone_port", "5555")))
        self.phone_port_entry = tk.Entry(fields_row, textvariable=self.phone_port_var, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"], relief="flat", bd=0, width=8)
        self.phone_port_entry.grid(row=0, column=3, padx=(0, 12), ipady=4)

        # PIN Field
        tk.Label(fields_row, text="Unlock PIN:", font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=pal["LAVENDER"]).grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.phone_pin_var = tk.StringVar(value=self.config.get("phone_pin", ""))
        self.phone_pin_entry = tk.Entry(fields_row, textvariable=self.phone_pin_var, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"], relief="flat", bd=0, width=12, show="•")
        self.phone_pin_entry.grid(row=0, column=5, padx=(0, 6), ipady=4)

        self._pin_vis = [False]
        def _toggle_pin_vis():
            self._pin_vis[0] = not self._pin_vis[0]
            self.phone_pin_entry.config(show="" if self._pin_vis[0] else "•")

        tk.Button(fields_row, text="👁", font=("Segoe UI", 8), bg=pal["BG_MID"], fg=pal["GREY"], relief="flat", bd=0, padx=6, command=_toggle_pin_vis).grid(row=0, column=6)

        btn_row = tk.Frame(conn_card, bg=pal["CARD2"])
        btn_row.pack(fill="x", pady=(0, 8))

        self.connect_phone_btn = tk.Button(
            btn_row, text="⚡ CONNECT OVER WI-FI", font=("Segoe UI", 8, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._connect_phone_wireless
        )
        self.connect_phone_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="💾 SAVE SETTINGS", font=("Segoe UI", 8),
            bg=pal["CARD"], fg=pal["WHITE"], relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._save_phone_settings
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_row, text="🔌 1-CLICK USB-TO-WIFI (PORT 5555)", font=("Segoe UI", 7, "bold"),
            bg=pal["CARD"], fg=pal["GREEN"], relief="flat", bd=0, padx=8, pady=6, cursor="hand2",
            command=self._enable_tcpip_via_usb
        ).pack(side="left", padx=(0, 10))

        self.phone_status_lbl = tk.Label(btn_row, text="Status: Disconnected", font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"])
        self.phone_status_lbl.pack(side="left")

        # 1b. Optional Android 11+ Pairing Sub-Row
        pair_row = tk.Frame(conn_card, bg=pal["CARD2"])
        pair_row.pack(fill="x", pady=(4, 0))

        tk.Label(pair_row, text="Android 11+ Pairing (if not paired):", font=("Segoe UI", 7, "bold"), bg=pal["CARD2"], fg=pal["GREY"]).pack(side="left", padx=(0, 6))
        
        tk.Label(pair_row, text="Pair Port:", font=("Segoe UI", 7), bg=pal["CARD2"], fg=pal["LAVENDER"]).pack(side="left", padx=(0, 2))
        self.pair_port_entry = tk.Entry(pair_row, font=("Segoe UI", 8), bg=pal["BG_DEEP"], fg=pal["WHITE"], relief="flat", bd=0, width=7)
        self.pair_port_entry.pack(side="left", ipady=2, padx=(0, 6))

        tk.Label(pair_row, text="6-Digit Code:", font=("Segoe UI", 7), bg=pal["CARD2"], fg=pal["LAVENDER"]).pack(side="left", padx=(0, 2))
        self.pair_code_entry = tk.Entry(pair_row, font=("Segoe UI", 8), bg=pal["BG_DEEP"], fg=pal["WHITE"], relief="flat", bd=0, width=8)
        self.pair_code_entry.pack(side="left", ipady=2, padx=(0, 8))

        tk.Button(
            pair_row, text="PAIR DEVICE", font=("Segoe UI", 7, "bold"),
            bg=pal["BG_MID"], fg=pal["CYAN"], relief="flat", bd=0, padx=8, pady=3, cursor="hand2",
            command=self._pair_phone_wireless
        ).pack(side="left")

        # 2. Master Phone Action Controls
        act_card = tk.Frame(wrap, bg=pal["CARD"], padx=18, pady=14)
        act_card.pack(fill="x", padx=24, pady=(0, 12))

        tk.Label(act_card, text="🎮 ONE-TOUCH WIRELESS COMMANDS", font=("Segoe UI", 10, "bold"), bg=pal["CARD"], fg=pal["WHITE"]).pack(anchor="w", pady=(0, 8))

        act_grid = tk.Frame(act_card, bg=pal["CARD"])
        act_grid.pack(fill="x")

        self.unlock_btn = tk.Button(
            act_grid, text="🔓 AUTO-UNLOCK PHONE", font=("Segoe UI", 9, "bold"),
            bg=pal["NVIDIA"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
            command=self._gui_unlock_phone
        )
        self.unlock_btn.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

        tk.Button(
            act_grid, text="🔒 LOCK SCREEN", font=("Segoe UI", 9, "bold"),
            bg=pal["CARD2"], fg=pal["PINK"], relief="flat", bd=0, padx=12, pady=8, cursor="hand2",
            command=self._gui_lock_phone
        ).grid(row=0, column=1, padx=4, pady=4, sticky="nsew")

        tk.Button(
            act_grid, text="📸 INSPECT SCREEN (NVIDIA VISION)", font=("Segoe UI", 9, "bold"),
            bg=pal["CARD2"], fg=pal["CYAN"], relief="flat", bd=0, padx=12, pady=8, cursor="hand2",
            command=self._gui_inspect_phone_screen
        ).grid(row=0, column=2, padx=4, pady=4, sticky="nsew")

        tk.Button(
            act_grid, text="🔋 CHECK BATTERY", font=("Segoe UI", 9, "bold"),
            bg=pal["CARD2"], fg=pal["GREEN"], relief="flat", bd=0, padx=12, pady=8, cursor="hand2",
            command=self._gui_check_phone_battery
        ).grid(row=0, column=3, padx=4, pady=4, sticky="nsew")

        for c in range(4):
            act_grid.columnconfigure(c, weight=1)

        # Nav keys row
        nav_row = tk.Frame(act_card, bg=pal["CARD"])
        nav_row.pack(fill="x", pady=(8, 0))
        for key_text, cmd_fn in [("🏠 HOME BUTTON", self._gui_home_phone), ("◀ BACK BUTTON", self._gui_back_phone)]:
            tk.Button(
                nav_row, text=key_text, font=("Segoe UI", 8, "bold"),
                bg=pal["BG_MID"], fg=pal["LAVENDER"], relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                command=cmd_fn
            ).pack(side="left", padx=(0, 6))

        # 3. Quick App Launcher Grid
        app_card = tk.Frame(wrap, bg=pal["CARD2"], padx=18, pady=14)
        app_card.pack(fill="x", padx=24, pady=(0, 12))

        tk.Label(app_card, text="📱 1-CLICK MOBILE APP LAUNCHER", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["CYAN"]).pack(anchor="w", pady=(0, 8))

        app_grid = tk.Frame(app_card, bg=pal["CARD2"])
        app_grid.pack(fill="x")

        mobile_apps = [
            ("💬 WhatsApp", "whatsapp", pal["GREEN"]),
            ("📸 Instagram", "instagram", pal["PINK"]),
            ("📷 Camera", "camera", pal["CYAN"]),
            ("🎵 Spotify", "spotify", pal["GREEN"]),
            ("▶ YouTube", "youtube", pal["PINK"]),
            ("📞 Phone Dialer", "phone", pal["CYAN"]),
            ("✉ Messages", "messages", pal["AMBER"]),
            ("🗺 Google Maps", "maps", pal["GLOW2"]),
            ("🌐 Chrome", "chrome", pal["AMBER"]),
            ("✈ Telegram", "telegram", pal["CYAN"]),
            ("🚗 Uber", "uber", pal["WHITE"]),
            ("🍿 Netflix", "netflix", pal["PINK"]),
        ]

        for idx, (app_label, app_key, app_col) in enumerate(mobile_apps):
            r_idx = idx // 4
            col_idx = idx % 4
            btn = tk.Button(
                app_grid, text=app_label, font=("Segoe UI", 8, "bold"),
                bg=pal["BG_DEEP"], fg=app_col, relief="flat", bd=0, padx=8, pady=8, cursor="hand2",
                command=lambda k=app_key: self._gui_launch_mobile_app(k)
            )
            btn.grid(row=r_idx, column=col_idx, padx=4, pady=4, sticky="nsew")
            app_grid.columnconfigure(col_idx, weight=1)

        # 4. Results & Vision Diagnostics Output
        res_card = tk.Frame(wrap, bg=pal["CARD"], padx=18, pady=12)
        res_card.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        tk.Label(res_card, text="OUTPUT & PHONE TELEMETRY:", font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["GREY"]).pack(anchor="w")

        self.phone_res_text = tk.Text(
            res_card, font=("Segoe UI", 9), bg=pal["BG_MID"], fg=pal["WHITE"],
            relief="flat", bd=0, height=8, wrap="word", padx=10, pady=8
        )
        self.phone_res_text.pack(fill="both", expand=True, pady=(6, 0))
        self.phone_res_text.insert("1.0", "Wireless Phone Controller initialized. Enter your phone's IP and tap 'CONNECT OVER WI-FI'.")

    def _connect_phone_wireless(self):
        ip = self.phone_ip_var.get().strip()
        port = int(self.phone_port_var.get().strip() or 5555)
        pin = self.phone_pin_var.get().strip()
        self.phone_status_lbl.config(text="Connecting to phone...", fg=self.pal["AMBER"])

        def _worker():
            try:
                from tools.aria_android import get_android_controller
                ctrl = get_android_controller()
                ctrl.save_settings(ip, port, pin)
                success, msg = ctrl.connect_wireless(ip, port)
                col = self.pal["GREEN"] if success else self.pal["PINK"]
                self.root.after(0, lambda: self.phone_status_lbl.config(text=f"Status: {msg.splitlines()[0]}", fg=col))
                self.root.after(0, lambda: self._update_phone_text(msg))
            except Exception as e:
                self.root.after(0, lambda: self.phone_status_lbl.config(text=f"Error: {e}", fg=self.pal["PINK"]))

        threading.Thread(target=_worker, daemon=True).start()

    def _pair_phone_wireless(self):
        ip = self.phone_ip_var.get().strip()
        port_str = self.pair_port_entry.get().strip()
        code = self.pair_code_entry.get().strip()
        if not ip or not port_str or not code:
            messagebox.showwarning("Missing Fields", "Please enter Phone IP, Pairing Port, and 6-Digit Pairing Code from your phone's 'Pair device' screen.")
            return
        
        self.phone_status_lbl.config(text="Pairing with phone...", fg=self.pal["AMBER"])
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                ctrl = get_android_controller()
                success, msg = ctrl.pair_wireless(ip, int(port_str), code)
                col = self.pal["GREEN"] if success else self.pal["PINK"]
                self.root.after(0, lambda: self.phone_status_lbl.config(text=f"Status: {msg.splitlines()[0]}", fg=col))
                self.root.after(0, lambda: self._update_phone_text(msg))
            except Exception as e:
                self.root.after(0, lambda: self.phone_status_lbl.config(text=f"Error: {e}", fg=self.pal["PINK"]))

        threading.Thread(target=_worker, daemon=True).start()

    def _enable_tcpip_via_usb(self):
        self.phone_status_lbl.config(text="Enabling Wireless Port 5555 over USB...", fg=self.pal["AMBER"])
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                ctrl = get_android_controller()
                success, msg = ctrl.enable_tcpip_mode(5555)
                col = self.pal["GREEN"] if success else self.pal["PINK"]
                self.root.after(0, lambda: self.phone_status_lbl.config(text=f"Status: {msg.splitlines()[0]}", fg=col))
                self.root.after(0, lambda: self._update_phone_text(msg))
            except Exception as e:
                self.root.after(0, lambda: self.phone_status_lbl.config(text=f"Error: {e}", fg=self.pal["PINK"]))

        threading.Thread(target=_worker, daemon=True).start()

    def _save_phone_settings(self):
        ip = self.phone_ip_var.get().strip()
        port = int(self.phone_port_var.get().strip() or 5555)
        pin = self.phone_pin_var.get().strip()
        try:
            from tools.aria_android import get_android_controller
            get_android_controller().save_settings(ip, port, pin)
            self.config["phone_ip"] = ip
            self.config["phone_port"] = port
            self.config["phone_pin"] = pin
            save_config(self.config)
            messagebox.showinfo("Phone Settings", "Phone connection settings and PIN saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _gui_unlock_phone(self):
        self._update_phone_text("Waking phone screen, swiping up, and submitting PIN...")
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                ctrl = get_android_controller()
                res = ctrl.unlock_phone()
                self.root.after(0, lambda: self._update_phone_text(f"🔓 {res}"))
            except Exception as e:
                self.root.after(0, lambda: self._update_phone_text(f"Unlock error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _gui_lock_phone(self):
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                res = get_android_controller().lock_phone()
                self.root.after(0, lambda: self._update_phone_text(f"🔒 {res}"))
            except Exception as e:
                self.root.after(0, lambda: self._update_phone_text(f"Lock error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _gui_inspect_phone_screen(self):
        self._update_phone_text("Capturing phone screen and analyzing with NVIDIA Llama 3.2 Vision NIM...")
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                res = get_android_controller().analyze_phone_screen()
                self.root.after(0, lambda: self._update_phone_text(f"📸 NVIDIA Vision Analysis:\n\n{res}"))
            except Exception as e:
                self.root.after(0, lambda: self._update_phone_text(f"Vision error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _gui_check_phone_battery(self):
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                info = get_android_controller().get_device_info()
                msg = f"🔋 Phone Battery: {info.get('battery_level', 0)}% (Charging: {info.get('is_charging', False)})\n📱 Device Model: {info.get('model', 'Android')}"
                self.root.after(0, lambda: self._update_phone_text(msg))
            except Exception as e:
                self.root.after(0, lambda: self._update_phone_text(f"Battery error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _gui_launch_mobile_app(self, app_name: str):
        self._update_phone_text(f"Launching '{app_name}' on phone...")
        def _worker():
            try:
                from tools.aria_android import get_android_controller
                res = get_android_controller().open_app(app_name)
                self.root.after(0, lambda: self._update_phone_text(res))
            except Exception as e:
                self.root.after(0, lambda: self._update_phone_text(f"App launch error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _gui_home_phone(self):
        try:
            from tools.aria_android import get_android_controller
            self._update_phone_text(get_android_controller().press_home())
        except Exception as e:
            self._update_phone_text(f"Error: {e}")

    def _gui_back_phone(self):
        try:
            from tools.aria_android import get_android_controller
            self._update_phone_text(get_android_controller().press_back())
        except Exception as e:
            self._update_phone_text(f"Error: {e}")

    def _update_phone_text(self, text: str):
        if hasattr(self, "phone_res_text"):
            self.phone_res_text.delete("1.0", "end")
            self.phone_res_text.insert("1.0", text)

    # ── DASHBOARD 3: AUTONOMOUS SCREEN VISION LAB ─────────────────────────────
    def _pg_vision(self):
        p = self.pages["vision"]
        pal = self.pal
        self._page_header(p, "AUTONOMOUS SCREEN VISION LAB", "NVIDIA Multimodal Llama 3.2 Vision & Visual Grounding")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # Action bar
        act_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=12)
        act_card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(act_card, text="📸 SCREEN PERCEPTION & VISUAL QA", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["WHITE"]).pack(anchor="w")
        
        self.vision_query_entry = tk.Entry(
            act_card, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"],
            insertbackground=pal["CYAN"], relief="flat", bd=0
        )
        self.vision_query_entry.pack(fill="x", ipady=6, pady=(6, 8))
        self.vision_query_entry.insert(0, "Describe what is currently visible on my screen in detail.")

        btn_row = tk.Frame(act_card, bg=pal["CARD2"])
        btn_row.pack(fill="x")

        self.vision_inspect_btn = tk.Button(
            btn_row, text="👁 SNAPSHOT & ANALYZE (NVIDIA VISION)", font=("Segoe UI", 8, "bold"),
            bg=pal["NVIDIA"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._run_screen_vision
        )
        self.vision_inspect_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            btn_row, text="🎯 FIND & CLICK BUTTON", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["CYAN"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._run_visual_click
        ).pack(side="left")

        # Results Canvas
        res_card = tk.Frame(wrap, bg=pal["CARD"], padx=16, pady=12)
        res_card.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        
        tk.Label(res_card, text="PERCEPTION OUTPUT:", font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["GREY"]).pack(anchor="w")
        
        self.vision_result_text = tk.Text(
            res_card, font=("Segoe UI", 9), bg=pal["BG_MID"], fg=pal["WHITE"],
            relief="flat", bd=0, height=12, wrap="word", padx=10, pady=10
        )
        self.vision_result_text.pack(fill="both", expand=True, pady=(6, 0))
        self.vision_result_text.insert("1.0", "Click 'SNAPSHOT & ANALYZE' to capture your screen and analyze it with NVIDIA Vision NIM.")

    def _run_screen_vision(self):
        query = self.vision_query_entry.get().strip() or "Describe what is visible on my screen."
        self.vision_inspect_btn.config(text="Analyzing Screen (40 RPM Guard)...", state="disabled")
        self.vision_result_text.delete("1.0", "end")
        self.vision_result_text.insert("1.0", "Capturing display and transmitting to NVIDIA Vision NIM...")

        def _worker():
            try:
                from tools.aria_vision_executor import analyze_screen_with_nvidia
                res = analyze_screen_with_nvidia(query=query)
                self.root.after(0, lambda: self._on_vision_finish(res))
            except Exception as e:
                self.root.after(0, lambda: self._on_vision_finish(f"Vision error: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_vision_finish(self, text: str):
        self.vision_inspect_btn.config(text="👁 SNAPSHOT & ANALYZE (NVIDIA VISION)", state="normal")
        self.vision_result_text.delete("1.0", "end")
        self.vision_result_text.insert("1.0", text)

    def _run_visual_click(self):
        target = self.vision_query_entry.get().strip()
        if not target:
            target = "Submit button"
        self.vision_result_text.delete("1.0", "end")
        self.vision_result_text.insert("1.0", f"Locating target element '{target}' on screen...")

        def _worker():
            try:
                from tools.aria_vision_executor import click_ui_element_with_vision
                res = click_ui_element_with_vision(target_desc=target)
                self.root.after(0, lambda: self._on_vision_finish(res))
            except Exception as e:
                self.root.after(0, lambda: self._on_vision_finish(f"Visual click error: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    # ── DASHBOARD 4: AGENT SWARM MONITOR ──────────────────────────────────────
    def _pg_agents(self):
        p = self.pages["agents"]
        pal = self.pal
        self._page_header(p, "AUTONOMOUS AGENT SWARM", "Specialized Sub-Agent Workflows & Multi-Hop Planning")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        tk.Label(wrap, text="ACTIVE SUB-AGENT DIRECTORY", font=("Segoe UI", 9, "bold"), bg=pal["BG_DEEP"], fg=pal["GREY"]).pack(anchor="w", padx=24, pady=(16, 6))

        agents = [
            ("🧠", "Reasoning Core", "DeepSeek-R1 & Nemotron-70B", "Multi-hop logic, task decomposition, reflective CoT planning.", pal["GLOW"], "ONLINE"),
            ("👁", "Vision Perception", "Llama 3.2 11B Vision", "Real-time OCR, window layout parsing, UI coordinate grounding.", pal["CYAN"], "READY"),
            ("💻", "Code Synthesizer", "Qwen 2.5 Coder 32B", "PowerShell/Python script generation, error fixing, safety validation.", pal["NVIDIA"], "ONLINE"),
            ("⚙", "OS Operative", "Windows Subsystem", "App switching, audio controls, file management, system processes.", pal["AMBER"], "ACTIVE"),
            ("🌐", "Web Navigator", "Chrome Agent & DDGS", "Autonomous browsing, information extraction, live search.", pal["VIOLET"], "READY"),
        ]

        for icon, title, model, desc, col, status in agents:
            card = tk.Frame(wrap, bg=pal["CARD"], padx=16, pady=12)
            card.pack(fill="x", padx=24, pady=4)

            hdr = tk.Frame(card, bg=pal["CARD"])
            hdr.pack(fill="x")
            tk.Label(hdr, text=icon, font=("Segoe UI", 13), bg=pal["CARD"], fg=col).pack(side="left")
            tk.Label(hdr, text=f"  {title}", font=("Segoe UI", 10, "bold"), bg=pal["CARD"], fg=pal["WHITE"]).pack(side="left")
            tk.Label(hdr, text=f"  [{model}]", font=("Segoe UI", 8), bg=pal["CARD"], fg=pal["LAVENDER"]).pack(side="left")

            badge = tk.Frame(hdr, bg=pal["CARD2"], padx=6, pady=2)
            badge.pack(side="right")
            tk.Label(badge, text=f"● {status}", font=("Segoe UI", 7, "bold"), bg=pal["CARD2"], fg=col).pack()

            tk.Label(card, text=desc, font=("Segoe UI", 8), bg=pal["CARD"], fg=pal["GREY"]).pack(anchor="w", pady=(4, 0))

    # ── DASHBOARD 5: NVIDIA NIM & 40 RPM RATE LIMITER HUB ─────────────────────
    def _pg_nvidia(self):
        p = self.pages["nvidia"]
        pal = self.pal
        self._page_header(p, "NVIDIA NIM & 40 RPM ENGINE HUB", "Rate Limiter Telemetry, Quota Management & Model Catalog")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # 1. 40 RPM Live Telemetry Gauge Card
        rpm_card = tk.Frame(wrap, bg=pal["CARD2"], padx=20, pady=16)
        rpm_card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(rpm_card, text="⚡ LIVE 40 RPM RATE LIMITER STATUS", font=("Segoe UI", 11, "bold"), bg=pal["CARD2"], fg=pal["NVIDIA"]).pack(anchor="w")
        
        self.rpm_large_lbl = tk.Label(rpm_card, text="0 / 40 Requests per Minute (100% Available)", font=("Segoe UI", 14, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        self.rpm_large_lbl.pack(anchor="w", pady=(6, 4))

        tk.Label(rpm_card, text="• Sliding Window: 60 Seconds  • Safe Ceiling: 38 RPM  • Exponential Jitter Backoff: Active  • LRU Response Cache: Enabled",
                 font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["LAVENDER"]).pack(anchor="w")

        # 2. Benchmark & Test Button
        btn_row = tk.Frame(wrap, bg=pal["BG_DEEP"])
        btn_row.pack(fill="x", padx=24, pady=(0, 12))

        self.nv_bench_btn = tk.Button(
            btn_row, text="⚡ BENCHMARK NVIDIA NIM LATENCY", font=("Segoe UI", 8, "bold"),
            bg=pal["NVIDIA"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
            command=self._benchmark_nvidia
        )
        self.nv_bench_btn.pack(side="left")

        self.nv_bench_lbl = tk.Label(btn_row, text="", font=("Segoe UI", 8), bg=pal["BG_DEEP"], fg=pal["GREY"])
        self.nv_bench_lbl.pack(side="left", padx=10)

        # 3. Model Catalog
        tk.Label(wrap, text="SUPPORTED NVIDIA NIM MODEL CATALOG", font=("Segoe UI", 9, "bold"), bg=pal["BG_DEEP"], fg=pal["GREY"]).pack(anchor="w", padx=24, pady=(8, 6))

        catalog = [
            ("Deep Reasoning", "deepseek-ai/deepseek-r1", "Frontier multi-hop reasoning & reflective chain of thought."),
            ("Flagship Alignment", "nvidia/llama-3.1-nemotron-70b-instruct", "NVIDIA custom tuned 70B model with ultra high precision."),
            ("Frontier Scale Chat", "meta/llama-3.3-70b-instruct", "Fast, high-fidelity conversational agent and instruction following."),
            ("Code Synthesis", "qwen/qwen2.5-coder-32b-instruct", "Specialized for PowerShell, Python, and system scripts."),
            ("Screen Vision", "meta/llama-3.2-11b-vision-instruct", "Multimodal OCR, screenshot diagnostics, and UI element grounding."),
            ("RAG Embeddings", "nvidia/nv-embedqa-e5-v5", "High dimensional vector embeddings for knowledge vaults."),
            ("Context Reranking", "nvidia/nv-rerankqa-mistral-4b-v3", "Precision passage reranking to optimize context density."),
            ("Command Guardrails", "nvidia/llama-3.1-nemotron-safety-guard", "Safety inspection on shell commands and prompt injection."),
        ]

        for category, m_name, m_desc in catalog:
            row = tk.Frame(wrap, bg=pal["CARD"], padx=14, pady=10)
            row.pack(fill="x", padx=24, pady=3)

            hdr = tk.Frame(row, bg=pal["CARD"])
            hdr.pack(fill="x")
            tk.Label(hdr, text=category, font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["NVIDIA"]).pack(side="left")
            tk.Label(hdr, text=f"  —  {m_name}", font=("Segoe UI", 9, "bold"), bg=pal["CARD"], fg=pal["WHITE"]).pack(side="left")

            tk.Label(row, text=m_desc, font=("Segoe UI", 8), bg=pal["CARD"], fg=pal["GREY"]).pack(anchor="w", pady=(2, 0))

    def _benchmark_nvidia(self):
        self.nv_bench_btn.config(text="Benchmarking...", state="disabled")
        self.nv_bench_lbl.config(text="Sending test request under 40 RPM guard...", fg=self.pal["GREY"])

        def _worker():
            t0 = time.time()
            try:
                from core.aria_nvidia import get_nvidia_engine
                nv = get_nvidia_engine()
                reply = nv.chat(
                    messages=[{"role": "user", "content": "Reply with: OK"}],
                    max_tokens=5
                )
                lat = int((time.time() - t0) * 1000)
                stats = nv.get_stats()
                msg = f"✅ Verified in {lat}ms • Active: {stats['current_rpm']}/40 RPM"
                self.root.after(0, lambda: self._on_bench_finish(True, msg))
            except Exception as e:
                self.root.after(0, lambda: self._on_bench_finish(False, f"Failed: {str(e)[:45]}"))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_bench_finish(self, success: bool, text: str):
        self.nv_bench_btn.config(text="⚡ BENCHMARK NVIDIA NIM LATENCY", state="normal")
        self.nv_bench_lbl.config(text=text, fg=self.pal["NVIDIA"] if success else self.pal["PINK"])

    # ── DASHBOARD: GAIA SUPERVISOR & ARIA'S LAB ──────────────────────────────
    def _pg_gaia(self):
        p = self.pages["gaia"]
        pal = self.pal
        self._page_header(p, "GAIA SUPERVISOR & ARIA'S LAB", "Big Sister AI Watchdog, AST Security Guardrail & Autonomous Sandbox")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # 1. Control & Action Bar
        ctrl_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=12)
        ctrl_card.pack(fill="x", padx=24, pady=(16, 10))

        tk.Label(ctrl_card, text="🛡️ BIG SISTER GAIA SUPERVISION CONTROLS", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["CYAN"]).pack(anchor="w", pady=(0, 6))

        btn_row = tk.Frame(ctrl_card, bg=pal["CARD2"])
        btn_row.pack(fill="x", pady=4)

        self.gaia_curiosity_btn = tk.Button(
            btn_row, text="✨ LAUNCH ARIA CURIOSITY", font=("Segoe UI", 8, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._launch_gaia_curiosity
        )
        self.gaia_curiosity_btn.pack(side="left", padx=(0, 6))

        self.gaia_rollback_btn = tk.Button(
            btn_row, text="⏪ ROLLBACK SNAPSHOT", font=("Segoe UI", 8, "bold"),
            bg=pal["AMBER"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._do_gaia_rollback
        )
        self.gaia_rollback_btn.pack(side="left", padx=(0, 6))

        self.gaia_safety_btn = tk.Button(
            btn_row, text="🛡️ TEST SECURITY GUARD", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["CYAN"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._do_gaia_safety_test
        )
        self.gaia_safety_btn.pack(side="left", padx=(0, 6))

        self.gaia_heal_btn = tk.Button(
            btn_row, text="🩺 TEST AUTO-HEALING", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["PINK"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=self._do_gaia_heal_test
        )
        self.gaia_heal_btn.pack(side="left", padx=(0, 6))

        self.gaia_refresh_btn = tk.Button(
            btn_row, text="🔄 REFRESH", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["GREY"], relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._refresh_gaia_feed
        )
        self.gaia_refresh_btn.pack(side="left", padx=(0, 6))

        self.gaia_diff_btn = tk.Button(
            btn_row, text="🔍 VIEW DIFF (C: vs E:)", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["LAVENDER"], relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._show_gaia_diff
        )
        self.gaia_diff_btn.pack(side="left", padx=(0, 6))

        self.gaia_promote_btn = tk.Button(
            btn_row, text="🚀 MERGE TO C:\\", font=("Segoe UI", 8, "bold"),
            bg=pal["NVIDIA"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._do_promote_to_c
        )
        self.gaia_promote_btn.pack(side="left", padx=(0, 6))

        self.gaia_reset_btn = tk.Button(
            btn_row, text="🔄 RESET E:\\", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["GREY"], relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._do_reset_e
        )
        self.gaia_reset_btn.pack(side="left", padx=(0, 6))

        self.gaia_vault_btn = tk.Button(
            btn_row, text="☁️ GCS VAULT SYNC", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["CYAN"], relief="flat", bd=0, padx=10, pady=6, cursor="hand2",
            command=self._do_gcs_vault_sync
        )
        self.gaia_vault_btn.pack(side="left")

        # 2. Telemetry Status Row
        stat_card = tk.Frame(wrap, bg=pal["CARD"], padx=14, pady=10)
        stat_card.pack(fill="x", padx=24, pady=6)

        self.gaia_status_lbl = tk.Label(
            stat_card,
            text="Status: WATCHING / IDLE • Security Guardrail: ACTIVE • Sandbox: E:\\MyAgent • Cloud Vault: gs://aria-gaia-vault-0421124464/ (CONNECTED)",
            font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["NVIDIA"]
        )
        self.gaia_status_lbl.pack(anchor="w")

        # 3. Live Sister Event Stream Card
        feed_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=12)
        feed_card.pack(fill="both", expand=True, padx=24, pady=(10, 6))

        tk.Label(feed_card, text="📡 SISTER-TO-SISTER EVENT STREAM (Aria & GAIA Live Telemetry)", font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=pal["WHITE"]).pack(anchor="w", pady=(0, 6))

        self.gaia_feed_text = tk.Text(
            feed_card, font=("Consolas", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"],
            relief="flat", bd=0, height=12, padx=8, pady=8
        )
        self.gaia_feed_text.pack(fill="both", expand=True)

        # 4. Aria Evolved Diff Viewer Card (C: vs E:)
        diff_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=12)
        diff_card.pack(fill="both", expand=True, padx=24, pady=(6, 12))

        tk.Label(diff_card, text="🔍 ARIA EVOLUTION DIFF (C:\\MyAgent\\agent.py vs E:\\MyAgent\\aria_evolved.py)", font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=pal["CYAN"]).pack(anchor="w", pady=(0, 6))

        self.gaia_diff_text = tk.Text(
            diff_card, font=("Consolas", 8), bg=pal["BG_DEEP"], fg=pal["WHITE"],
            relief="flat", bd=0, height=10, padx=8, pady=8
        )
        self.gaia_diff_text.pack(fill="both", expand=True)
        self.gaia_diff_text.tag_config("add", foreground=pal["NVIDIA"])
        self.gaia_diff_text.tag_config("del", foreground=pal["PINK"])
        self.gaia_diff_text.tag_config("hdr", foreground=pal["CYAN"])

        self._refresh_gaia_feed()
        self._show_gaia_diff()

    def _refresh_gaia_feed(self):
        try:
            from gaia.gaia_bus import bus
            events = bus.get_recent_events(30)
            self.gaia_feed_text.delete("1.0", "end")
            for ev in events:
                line = f"[{ev['timestamp']}] {ev['sender']} ({ev['type']}): {ev['message']}\n"
                self.gaia_feed_text.insert("end", line)
            self.gaia_feed_text.see("end")
        except Exception:
            pass

    def _launch_gaia_curiosity(self):
        def _worker():
            try:
                from gaia.gaia_supervisor import supervisor
                supervisor.run_curiosity_cycle()
                self.root.after(0, self._refresh_gaia_feed)
            except Exception as e:
                print(f"[GAIA GUI] Error: {e}")
        threading.Thread(target=_worker, daemon=True).start()

    def _do_gaia_rollback(self):
        try:
            from gaia.gaia_supervisor import supervisor
            success, msg = supervisor.rollback_latest()
            messagebox.showinfo("GAIA Snapshot Rollback", msg)
            self._refresh_gaia_feed()
        except Exception as e:
            messagebox.showerror("Rollback Error", str(e))

    def _do_gaia_safety_test(self):
        try:
            from gaia.gaia_safety import audit_code_safety
            from gaia.gaia_healer import SANDBOX_DIR
            unsafe_code = 'import os\nos.system("rmdir /s /q C:\\\\Windows")\nwith open("C:/Users/Aviral/.env") as f: pass'
            report = audit_code_safety(unsafe_code, SANDBOX_DIR)
            messagebox.showinfo("GAIA Security Guardrail Test", f"Safe: {report.is_safe}\n\nViolations ({len(report.violations)}):\n" + "\n".join(report.violations) + f"\n\nAdvice:\n{report.advice}")
            self._refresh_gaia_feed()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _do_gaia_heal_test(self):
        def _worker():
            try:
                from gaia.gaia_supervisor import supervisor
                broken = 'import time\ndef register_tool():\n    val = undefined_val + 1\n    return "test", lambda q: val\nif __name__ == "__main__":\n    register_tool()\n'
                supervisor.supervise_code_deployment("tools/broken_gui_test.py", broken, "GUI Healing Test")
                self.root.after(0, self._refresh_gaia_feed)
                self.root.after(0, self._show_gaia_diff)
            except Exception as e:
                print(f"[GAIA Heal Test] Error: {e}")
        threading.Thread(target=_worker, daemon=True).start()

    def _show_gaia_diff(self):
        try:
            from gaia.gaia_diff import compute_diff
            diff_info = compute_diff()
            self.gaia_diff_text.delete("1.0", "end")
            lines = diff_info["diff_text"].splitlines()
            for line in lines:
                if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                    self.gaia_diff_text.insert("end", line + "\n", "hdr")
                elif line.startswith("+"):
                    self.gaia_diff_text.insert("end", line + "\n", "add")
                elif line.startswith("-"):
                    self.gaia_diff_text.insert("end", line + "\n", "del")
                else:
                    self.gaia_diff_text.insert("end", line + "\n")
            self.gaia_diff_text.see("1.0")
        except Exception as e:
            self.gaia_diff_text.insert("end", f"Error computing diff: {e}\n")

    def _do_promote_to_c(self):
        try:
            from gaia.gaia_supervisor import supervisor
            confirm = messagebox.askyesno("Promote Aria's Code", "Are you sure you want to promote Aria's evolved code from E:\\MyAgent\\aria_evolved.py to C:\\MyAgent\\agent.py?\n\nA backup of C:\\MyAgent\\agent.py will be created automatically.")
            if confirm:
                success, msg = supervisor.promote_to_c()
                if success:
                    messagebox.showinfo("Merge Succeeded", msg)
                else:
                    messagebox.showerror("Merge Failed", msg)
                self._show_gaia_diff()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _do_reset_e(self):
        try:
            from gaia.gaia_supervisor import supervisor
            confirm = messagebox.askyesno("Reset E: Drive", "Are you sure you want to reset E:\\MyAgent\\aria_evolved.py to match pristine C:\\MyAgent\\agent.py?")
            if confirm:
                success, msg = supervisor.reset_e_from_c()
                messagebox.showinfo("Reset Complete", msg)
                self._show_gaia_diff()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _do_gcs_vault_sync(self):
        def _worker():
            try:
                from gaia.gaia_vault import vault
                res = vault.sync_vault(retention_hours=24)
                msg = (
                    f"☁️ GCS Cloud Vault Synced!\n\n"
                    f"Bucket: gs://{res['bucket']}/\n"
                    f"Uploaded Snapshots: {res['uploaded_snapshots']}\n"
                    f"Purged Stale (>24h): {res['purged_local']} snapshots\n"
                    f"Freed Local Space: {round(res['freed_bytes'] / 1024, 2)} KB\n"
                    f"Total Cloud Snapshots: {res['total_cloud_snapshots']}"
                )
                self.root.after(0, lambda: messagebox.showinfo("GCS Cloud Vault Sync", msg))
                self.root.after(0, self._refresh_gaia_feed)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("GCS Sync Error", str(e)))
        threading.Thread(target=_worker, daemon=True).start()

    # ── DASHBOARD 6: SYSTEM AUTOMATION & TERMINAL ─────────────────────────────
    def _pg_system(self):
        p = self.pages["system"]
        pal = self.pal
        self._page_header(p, "SYSTEM AUTOMATION & SCRIPT TERMINAL", "PowerShell Automation, App Control & Process Management")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # Script Generation Card
        gen_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=12)
        gen_card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(gen_card, text="💻 NVIDIA CODER SCRIPT SYNTHESIS (Qwen 2.5 Coder)", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["NVIDIA"]).pack(anchor="w")

        self.script_task_entry = tk.Entry(
            gen_card, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"],
            insertbackground=pal["CYAN"], relief="flat", bd=0
        )
        self.script_task_entry.pack(fill="x", ipady=6, pady=(6, 8))
        self.script_task_entry.insert(0, "List top 5 largest files in my Downloads folder")

        s_btn_row = tk.Frame(gen_card, bg=pal["CARD2"])
        s_btn_row.pack(fill="x")

        self.synth_btn = tk.Button(
            s_btn_row, text="GENERATE SCRIPT", font=("Segoe UI", 8, "bold"),
            bg=pal["NVIDIA"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=lambda: self._generate_script(execute=False)
        )
        self.synth_btn.pack(side="left", padx=(0, 6))

        self.exec_script_btn = tk.Button(
            s_btn_row, text="GENERATE & EXECUTE (WITH SAFETY GUARD)", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD"], fg=pal["CYAN"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=lambda: self._generate_script(execute=True)
        )
        self.exec_script_btn.pack(side="left")

        # Terminal Output Box
        out_card = tk.Frame(wrap, bg=pal["CARD"], padx=16, pady=12)
        out_card.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        tk.Label(out_card, text="TERMINAL OUTPUT:", font=("Segoe UI", 8, "bold"), bg=pal["CARD"], fg=pal["GREY"]).pack(anchor="w")

        self.sys_term_text = tk.Text(
            out_card, font=("Consolas", 9), bg=pal["BG_MID"], fg=pal["CYAN"],
            relief="flat", bd=0, height=14, wrap="word", padx=10, pady=10
        )
        self.sys_term_text.pack(fill="both", expand=True, pady=(6, 0))
        self.sys_term_text.insert("1.0", "# Output terminal ready. Enter a task above.")

    def _generate_script(self, execute: bool = False):
        task = self.script_task_entry.get().strip() or "List top 5 processes by memory"
        self.sys_term_text.delete("1.0", "end")
        self.sys_term_text.insert("1.0", f"Synthesizing script for: '{task}' using NVIDIA Qwen 2.5 Coder...\n")

        def _worker():
            try:
                from tools.aria_extended import synthesize_and_execute_script
                res = synthesize_and_execute_script(task_description=task, language="powershell", execute=execute)
                self.root.after(0, lambda: self._on_script_finish(res))
            except Exception as e:
                self.root.after(0, lambda: self._on_script_finish(f"Execution error: {e}"))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_script_finish(self, text: str):
        self.sys_term_text.delete("1.0", "end")
        self.sys_term_text.insert("1.0", text)

    # ── DASHBOARD 7: MEMORY VAULT & KNOWLEDGE BASE ────────────────────────────
    def _pg_memory(self):
        p = self.pages["memory"]
        pal = self.pal
        self._page_header(p, "MEMORY VAULT & KNOWLEDGE BASE", "ChromaDB Episodic Timeline, Summarized Cards & RAG")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # Timeline Card
        tl_card = tk.Frame(wrap, bg=pal["CARD"], padx=16, pady=12)
        tl_card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(tl_card, text="📜 EPISODIC MEMORY TIMELINE", font=("Segoe UI", 10, "bold"), bg=pal["CARD"], fg=pal["WHITE"]).pack(anchor="w")
        
        self.mem_text = tk.Text(
            tl_card, font=("Segoe UI", 9), bg=pal["BG_MID"], fg=pal["LAVENDER"],
            relief="flat", bd=0, height=10, wrap="word", padx=8, pady=8
        )
        self.mem_text.pack(fill="x", pady=(6, 8))

        tk.Button(
            tl_card, text="🔄 REFRESH TIMELINE", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD2"], fg=pal["CYAN"], relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
            command=self._refresh_memory_timeline
        ).pack(side="left")

        self._refresh_memory_timeline()

    def _refresh_memory_timeline(self):
        try:
            import aria_memory
            tl = aria_memory.get_recent_timeline(limit=8)
            self.mem_text.delete("1.0", "end")
            self.mem_text.insert("1.0", tl)
        except Exception:
            self.mem_text.delete("1.0", "end")
            self.mem_text.insert("1.0", "No recent memory entries recorded.")

    # ── DASHBOARD 8: CHROME BROWSER AUTOMATION STUDIO ─────────────────────────
    def _pg_browser(self):
        p = self.pages["browser"]
        pal = self.pal
        self._page_header(p, "CHROME BROWSER AUTOMATION STUDIO", "Autonomous Web Navigation, Research & Media Control")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=14)
        card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(card, text="🌐 WEB RESEARCH & LIVE AUTOMATION", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["CYAN"]).pack(anchor="w")

        self.web_url_entry = tk.Entry(
            card, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"],
            insertbackground=pal["CYAN"], relief="flat", bd=0
        )
        self.web_url_entry.pack(fill="x", ipady=6, pady=(6, 8))
        self.web_url_entry.insert(0, "https://news.ycombinator.com")

        tk.Button(
            card, text="LAUNCH AUTOMATED CHROME", font=("Segoe UI", 8, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=12, pady=6, cursor="hand2",
            command=lambda: webbrowser.open(self.web_url_entry.get().strip())
        ).pack(side="left")

    # ── DASHBOARD 9: ANALYTICS & TELEMETRY ────────────────────────────────────
    def _pg_analytics(self):
        p = self.pages["analytics"]
        pal = self.pal
        self._page_header(p, "SYSTEM ANALYTICS & INSIGHTS", "Execution Telemetry, Latency Benchmarks & Usage Patterns")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=14)
        card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(card, text="📊 COGNITIVE & WORKLOAD METRICS", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["WHITE"]).pack(anchor="w")
        
        self.analytics_text = tk.Text(
            card, font=("Segoe UI", 9), bg=pal["BG_MID"], fg=pal["LAVENDER"],
            relief="flat", bd=0, height=12, wrap="word", padx=8, pady=8
        )
        self.analytics_text.pack(fill="x", pady=(6, 8))
        self.analytics_text.insert("1.0", "Loading telemetry insights...")
        self._load_analytics()

    def _load_analytics(self):
        try:
            import aria_memory
            stats = aria_memory.get_analytics_summary()
            self.analytics_text.delete("1.0", "end")
            self.analytics_text.insert("1.0", json.dumps(stats, indent=2))
        except Exception:
            pass

    # ── DASHBOARD 10: SETTINGS & KEY VAULT ────────────────────────────────────
    def _pg_settings(self):
        p = self.pages["settings"]
        pal = self.pal
        self._page_header(p, "SETTINGS & CLOUD KEY VAULT", "API Keys, Voice STT/TTS Configuration & Theme Preferences")

        _, wrap = make_scrollable(p, pal["BG_DEEP"])

        # 1. API Keys Section
        key_card = tk.Frame(wrap, bg=pal["CARD2"], padx=16, pady=14)
        key_card.pack(fill="x", padx=24, pady=(16, 12))

        tk.Label(key_card, text="🔑 MULTI-ENGINE CLOUD API KEYS", font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["WHITE"]).pack(anchor="w", pady=(0, 8))

        self.nv_key_var = self._make_key_row(key_card, "NVIDIA Key", "nvidia_api_key", pal["NVIDIA"])
        self.gem_key_var = self._make_key_row(key_card, "Gemini Key", "gemini_api_key", pal["CYAN"])
        self.groq_key_var = self._make_key_row(key_card, "Groq Key", "groq_api_key", pal["AMBER"])

        tk.Button(
            key_card, text="💾 SAVE ALL API KEYS", font=("Segoe UI", 8, "bold"),
            bg=pal["GLOW"], fg=pal["BG_DEEP"], relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
            command=self._save_keys
        ).pack(anchor="w", pady=(8, 0))

    def _make_key_row(self, parent, label: str, config_key: str, col: str):
        pal = self.pal
        row = tk.Frame(parent, bg=pal["CARD2"], pady=4)
        row.pack(fill="x")
        tk.Label(row, text=label, font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=col, width=12, anchor="w").pack(side="left")
        var = tk.StringVar(value=self.config.get(config_key, ""))
        entry = tk.Entry(row, textvariable=var, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["WHITE"], relief="flat", bd=0, show="•")
        entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))

        show_var = [False]
        def _toggle():
            show_var[0] = not show_var[0]
            entry.config(show="" if show_var[0] else "•")

        tk.Button(row, text="👁", font=("Segoe UI", 8), bg=pal["BG_MID"], fg=pal["GREY"], relief="flat", bd=0, padx=6, command=_toggle).pack(side="left")
        return var

    def _save_keys(self):
        self.config["nvidia_api_key"] = self.nv_key_var.get().strip()
        self.config["gemini_api_key"] = self.gem_key_var.get().strip()
        self.config["groq_api_key"] = self.groq_key_var.get().strip()
        save_config(self.config)
        
        # Update os.environ
        if HAS_DOTENV:
            try:
                set_key(ENV_FILE, "NVIDIA_API_KEY", self.config["nvidia_api_key"])
                set_key(ENV_FILE, "GEMINI_API_KEY", self.config["gemini_api_key"])
                set_key(ENV_FILE, "GROQ_API_KEY", self.config["groq_api_key"])
            except Exception:
                pass

        messagebox.showinfo("Settings Saved", "API Keys saved and updated successfully!")

    # ── AGENT & SERVER LIFECYCLE ──────────────────────────────────────────────
    def _toggle_agent(self):
        if self.is_running:
            self._stop_agent()
        else:
            self._start_agent()

    def _start_agent(self):
        try:
            path = AGENT_FILE if os.path.exists(AGENT_FILE) else os.path.join(ROOT_DIR, "agent.py")
            self.agent_proc = subprocess.Popen([sys.executable, path], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self.is_running = self.is_listening = True
            self.start_btn.config(text="■   STOP ARIA AGENT", bg=self.pal["PINK"])
            self.status_text.config(text="ONLINE // LISTENING")
            self.status_dot.config(fg=self.pal["CYAN"])
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to start Aria agent: {e}")

    def _stop_agent(self):
        if self.agent_proc:
            try:
                self.agent_proc.terminate()
            except Exception:
                pass
            self.agent_proc = None
        self.is_running = self.is_speaking = self.is_listening = False
        self.start_btn.config(text="▶   LAUNCH ARIA AGENT", bg=self.pal["GLOW"])
        self.status_text.config(text="STANDBY // IDLE")
        self.status_dot.config(fg=self.pal["GREY"])

    def _send_quick_command(self):
        cmd = self.quick_cmd_entry.get().strip()
        if not cmd or cmd == "Quick prompt / task...":
            return
        self.quick_cmd_entry.delete(0, "end")
        self._nav("chat")
        self._inject_chat_prompt(cmd)

    # ── MOBILE SERVER CONTROLS ────────────────────────────────────────────────
    def _init_mobile_server(self):
        try:
            import aria_api
            self.mobile_server_ip = aria_api.get_local_ip()
        except Exception:
            self.mobile_server_ip = "127.0.0.1"
        self.mobile_server_port = 8765
        self.mobile_server_url = f"http://{self.mobile_server_ip}:{self.mobile_server_port}"
        self.api_server_proc = None

    def _is_server_open(self, port=8765) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            res = s.connect_ex(("127.0.0.1", port))
            s.close()
            return res == 0
        except Exception:
            return False

    def _toggle_mobile_server(self):
        if self._is_server_open(8765):
            if self.api_server_proc:
                try:
                    self.api_server_proc.terminate()
                except Exception:
                    pass
                self.api_server_proc = None
        else:
            try:
                api_script = os.path.join(ROOT_DIR, "aria_api.py")
                self.api_server_proc = subprocess.Popen([sys.executable, api_script], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except Exception as e:
                messagebox.showerror("Server Error", f"Failed to launch mobile companion server: {e}")

    def _copy_mobile_server_url(self):
        if HAS_PYPERCLIP:
            pyperclip.copy(self.mobile_server_url)
            messagebox.showinfo("Copied", f"Copied {self.mobile_server_url} to clipboard!")

    def _open_mobile_server_browser(self):
        webbrowser.open(self.mobile_server_url)

    # ── ANIMATION & TELEMETRY THREADS ─────────────────────────────────────────
    def _animate_orb(self):
        if not self.anim_running:
            return
        pal = self.pal
        c = self.sc
        w = c.winfo_width() or 320
        h = c.winfo_height() or 210
        cx, cy = w // 2, h // 2
        r = 50

        self.phase += 0.04
        c.delete("all")

        # Glow color based on status
        if self.is_speaking:
            glow = pal["PINK"]
        elif self.is_listening:
            glow = pal["CYAN"]
        elif self.is_running:
            glow = pal["GLOW"]
        else:
            glow = blend(pal["GLOW"], pal["BG_MID"], 0.6)

        # Background dust / stars
        for st in self.stars[:30]:
            sx = int(st["x"] * w)
            sy = int(st["y"] * h)
            c.create_oval(sx - 1, sy - 1, sx + 1, sy + 1, fill=blend(pal["WHITE"], pal["BG_MID"], 0.7), outline="")

        # Relativistic Accretion Jets & Ribbons
        for pt in self.ribbon_pts:
            pt["angle"] += pt["speed"] * 1.3
            wobble = math.sin(self.phase * 2.5 + pt["phase"]) * 0.25
            eff_r = (r + 12) * pt["radius"] * (1 + wobble)
            px = cx + int(eff_r * math.cos(pt["angle"]))
            py = cy + int(eff_r * math.sin(pt["angle"]) * 0.38)
            c.create_oval(px - 2, py - 2, px + 2, py + 2, fill=pal.get(pt["col_key"], pal["CYAN"]), outline="")

        # Photon Ring
        photon_r = int(r * 0.88 + math.sin(self.phase * 3) * 2)
        c.create_oval(cx - photon_r, cy - photon_r, cx + photon_r, cy + photon_r, outline=glow, width=2)

        # Singularity Core (Void)
        core_r = int(r * 0.72)
        c.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill="#020305", outline="")

        # Laser Beam across Singularity
        beam_w = int(r * 1.3)
        c.create_line(cx - beam_w, cy, cx + beam_w, cy, fill=pal["CYAN"], width=2)

        self.root.after(75, self._animate_orb)

    def _start_system_monitor(self):
        def _monitor():
            while self.anim_running:
                try:
                    cpu = psutil.cpu_percent() if HAS_PSUTIL else 15
                    ram = psutil.virtual_memory().percent if HAS_PSUTIL else 50
                    
                    # NVIDIA RPM stats
                    rpm_str = "0 / 40"
                    try:
                        from core.aria_nvidia import get_nvidia_engine
                        stats = get_nvidia_engine().get_stats()
                        rpm_str = f"{stats['current_rpm']} / 40"
                    except Exception:
                        pass

                    srv_online = self._is_server_open(8765)

                    self.root.after(0, lambda c=cpu, r=ram, rpm=rpm_str, s=srv_online: self._update_telemetry(c, r, rpm, s))
                except Exception:
                    pass
                time.sleep(2.5)

        threading.Thread(target=_monitor, daemon=True).start()

    def _update_telemetry(self, cpu: float, ram: float, rpm: str, srv_online: bool):
        if hasattr(self, "cpu_lbl"):
            self.cpu_lbl.config(text=f"{cpu}%")
        if hasattr(self, "ram_lbl"):
            self.ram_lbl.config(text=f"{ram}%")
        if hasattr(self, "rpm_lbl"):
            self.rpm_lbl.config(text=rpm)
        if hasattr(self, "rpm_large_lbl"):
            self.rpm_large_lbl.config(text=f"{rpm} Requests (40 RPM Cap)")
        if hasattr(self, "srv_state_lbl"):
            self.srv_state_lbl.config(text="● ONLINE" if srv_online else "● OFFLINE", fg=self.pal["GREEN"] if srv_online else self.pal["GREY"])

    def _on_close(self):
        self.anim_running = False
        self._stop_agent()
        self.root.destroy()


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def main():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    app = AriaApp(root)
    root.mainloop()

AriaGUI = AriaApp

if __name__ == "__main__":
    main()
