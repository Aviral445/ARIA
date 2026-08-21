import tkinter as tk
import threading, json, os, math, time, subprocess, sys, re, random, webbrowser, socket
from tkinter import messagebox

try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False

# Ensure all sub-packages are discoverable on sys.path
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for _sub in [_ROOT_DIR, os.path.join(_ROOT_DIR, "core"), os.path.join(_ROOT_DIR, "tools"), os.path.join(_ROOT_DIR, "server"), os.path.join(_ROOT_DIR, "mcp"), os.path.join(_ROOT_DIR, "gui")]:
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

# ── FILES ─────────────────────────────────────────────────────────────────────
PROFILE_FILE = get_data_file("profile.json", create_if_missing=True)
AGENT_FILE   = os.path.join(ROOT_DIR, "agent.py")
CONFIG_FILE  = get_config_file("gui_config.json")

def load_profile():
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"name": "Friend", "preferences": [], "notes": [], "system_prompt": ""}

def save_profile(p):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, indent=2)

# ── THEMES ────────────────────────────────────────────────────────────────────
THEMES = {
    "cyber_purple": {
        "name": "Cyber Purple",
        "BG_DEEP": "#050510",
        "BG_MID": "#0a0a20",
        "BG_PANEL": "#0d0d25",
        "CARD": "#12122a",
        "CARD2": "#16163a",
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
    },
    "neon_cyan": {
        "name": "Neon Cyan",
        "BG_DEEP": "#030f14",
        "BG_MID": "#061820",
        "BG_PANEL": "#08212b",
        "CARD": "#0c2b38",
        "CARD2": "#103646",
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
    },
    "emerald_matrix": {
        "name": "Emerald Matrix",
        "BG_DEEP": "#02120a",
        "BG_MID": "#051c11",
        "BG_PANEL": "#082618",
        "CARD": "#0c301f",
        "CARD2": "#103d28",
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
    },
    "sunset_amber": {
        "name": "Sunset Amber",
        "BG_DEEP": "#140a05",
        "BG_MID": "#20120a",
        "BG_PANEL": "#2b180e",
        "CARD": "#382013",
        "CARD2": "#462818",
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
    },
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            c = {}
    else:
        c = {}
    defaults = {
        "theme": "cyber_purple",
        "voice_rate": 2,
        "agent_name": "Aria",
        "model": "gemini-2.5-flash",
        "voice": "Microsoft Zira Desktop",
        "whisper_model": "small",
        "auto_web_search": True,
        # Cloud API Keys
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
        # Context toggles
        "ctx_active_window": True,
        "ctx_clipboard": True,
        "ctx_running_apps": True,
        "ctx_system_stats": True,
        "ctx_screen_ocr": False,
        # Chrome
        "chrome_use_profile": True,
        "chrome_headless": False,
    }
    for k, v in defaults.items():
        c.setdefault(k, v)
    return c

def save_config(c):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(c, f, indent=2)

BT_KW = ["bluetooth", "airpod", "headset", "headphone",
         "wireless", "buds", "earphone", "handsfree"]

def get_input_devices():
    if not HAS_SD:
        return []
    devs = []
    try:
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                devs.append({"index": i, "name": d["name"]})
    except Exception:
        pass
    return devs

def is_bt(name):
    return any(k in name.lower() for k in BT_KW)

def blend(h1, h2, t):
    try:
        t = max(0.0, min(1.0, t))
        r1, g1, b1 = int(h1[1:3], 16), int(h1[3:5], 16), int(h1[5:7], 16)
        r2, g2, b2 = int(h2[1:3], 16), int(h2[3:5], 16), int(h2[5:7], 16)
        return "#{:02x}{:02x}{:02x}".format(
            max(0, min(255, int(r1 + (r2 - r1) * t))),
            max(0, min(255, int(g1 + (g2 - g1) * t))),
            max(0, min(255, int(b1 + (b2 - b1) * t))))
    except Exception:
        return h1

# ── HELPERS ───────────────────────────────────────────────────────────────────
def glow_btn(parent, text, cmd, w=None, h=38, c1=None, c2=None):
    c1 = c1 or parent.winfo_toplevel().pal["GLOW"]
    c2 = c2 or parent.winfo_toplevel().pal["CYAN"]
    b = tk.Button(parent, text=text,
                  font=("Segoe UI", 10, "bold"),
                  bg=c1, fg="#ffffff",
                  activebackground=blend(c1, c2, 0.4),
                  activeforeground="#ffffff",
                  relief="flat", bd=0,
                  padx=20, pady=8,
                  cursor="hand2", command=cmd)
    if w:
        b.config(width=w)
    b.bind("<Enter>", lambda e: b.config(bg=blend(c1, c2, 0.35)))
    b.bind("<Leave>", lambda e: b.config(bg=c1))
    return b

def ghost_btn(parent, text, cmd, col=None):
    pal = parent.winfo_toplevel().pal
    col = col or pal["LAVENDER"]
    b = tk.Button(parent, text=text,
                  font=("Segoe UI", 9),
                  bg=pal["CARD2"], fg=col,
                  activebackground=blend(pal["CARD2"], col, 0.15),
                  activeforeground="#ffffff",
                  relief="flat", bd=0,
                  padx=14, pady=7,
                  cursor="hand2", command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=blend(pal["CARD2"], col, 0.2)))
    b.bind("<Leave>", lambda e: b.config(bg=pal["CARD2"]))
    return b

def danger_btn(parent, text, cmd):
    pal = parent.winfo_toplevel().pal
    b = tk.Button(parent, text=text,
                  font=("Segoe UI", 9),
                  bg=blend(pal["PINK"], pal["BG_PANEL"], 0.8),
                  fg=pal["PINK"],
                  activebackground=blend(pal["PINK"], pal["BG_PANEL"], 0.65),
                  activeforeground="#ffffff",
                  relief="flat", bd=0,
                  padx=14, pady=7,
                  cursor="hand2", command=cmd)
    b.bind("<Enter>", lambda e: b.config(bg=blend(pal["PINK"], pal["BG_PANEL"], 0.65)))
    b.bind("<Leave>", lambda e: b.config(bg=blend(pal["PINK"], pal["BG_PANEL"], 0.8)))
    return b

def section_lbl(parent, text, bg=None):
    pal = parent.winfo_toplevel().pal
    bg = bg or parent.cget("bg")
    f = tk.Frame(parent, bg=bg)
    f.pack(fill="x", pady=(20, 8))
    tk.Frame(f, bg=pal["GLOW2"], width=3, height=18).pack(side="left")
    tk.Frame(f, bg=pal["VIOLET"], width=1, height=18).pack(side="left")
    tk.Label(f, text=f"  {text}",
             font=("Segoe UI", 10, "bold"),
             bg=bg, fg=pal["LAVENDER"]).pack(side="left")

def divider(parent, bg=None):
    pal = parent.winfo_toplevel().pal
    bg = bg or parent.cget("bg")
    tk.Frame(parent, bg=pal["BORDER"], height=1).pack(fill="x", pady=(14, 0))

def scrollable(parent, bg=None):
    pal = parent.winfo_toplevel().pal
    bg = bg or parent.cget("bg")
    c  = tk.Canvas(parent, bg=bg, highlightthickness=0)
    sb = tk.Scrollbar(parent, orient="vertical", command=c.yview,
                      bg=pal["CARD"], troughcolor=pal["BG_PANEL"], width=12)
    c.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    c.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(c, bg=bg)
    win   = c.create_window((0, 0), window=inner, anchor="nw")
    
    parent._scroll_canvas = c
    c._scroll_inner = inner
    
    def _update_bounds(event=None):
        w = max(c.winfo_width(), 100)
        h = max(inner.winfo_reqheight(), c.winfo_height()) + 60
        c.itemconfig(win, width=w)
        c.configure(scrollregion=(0, 0, w, h))
        
    inner.bind("<Configure>", _update_bounds)
    c.bind("<Configure>", _update_bounds)

    def _wheel(event):
        step = -2 if event.delta > 0 else 2
        c.yview_scroll(step, "units")
        return "break"
        
    c.bind("<MouseWheel>", _wheel)
    inner.bind("<MouseWheel>", _wheel)
    
    return c, inner

# ═════════════════════════════════════════════════════════════════════════════
class AriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ARIA — AI Personal Assistant & Cyber System")
        self.root.state("zoomed")
        
        self.sc = None
        self.nav_dot_c = None
        self.pages = {}
        self.active_page = "home"

        # Universal smooth mousewheel handler
        def _global_mousewheel(event):
            try:
                step = -2 if event.delta > 0 else 2
                # 1. Target canvas under cursor
                w = self.root.winfo_containing(event.x_root, event.y_root)
                while w:
                    if isinstance(w, tk.Canvas) and hasattr(w, "yview_scroll"):
                        if w != getattr(self, "sc", None) and w != getattr(self, "nav_dot_c", None):
                            w.yview_scroll(step, "units")
                            return "break"
                    w = getattr(w, "master", None)
                
                # 2. Fallback to active page canvas
                active_frame = self.pages.get(self.active_page)
                if active_frame and hasattr(active_frame, "_scroll_canvas"):
                    active_frame._scroll_canvas.yview_scroll(step, "units")
                    return "break"
            except Exception:
                pass
        self.root.bind_all("<MouseWheel>", _global_mousewheel)
        
        self.config   = load_config()
        self.profile  = load_profile()
        
        theme_key = self.config.get("theme", "cyber_purple")
        self.pal = THEMES.get(theme_key, THEMES["cyber_purple"])
        self.root.pal = self.pal
        self.root.configure(bg=self.pal["BG_DEEP"])
        self.root.update()

        self.agent_proc   = None
        self.is_running   = False
        self.is_speaking  = False
        self.is_listening = False
        self.active_mic   = None
        self.mic_running  = True
        self.phase        = 0.0
        self.pulses       = []
        self.ribbons      = []
        self.anim_running = True
        self.active_page  = "home"
        self.input_mode   = "voice"
        self.chat_history = []
        
        # Audio level simulation for reactive orb
        self.audio_level  = 0.0

        # Background stars
        self.stars = [
            {"x": random.random(), "y": random.random(),
             "r": random.uniform(0.5, 2.0),
             "bright": random.random(),
             "speed": random.uniform(0.002, 0.008)}
            for _ in range(130)]

        # Energy ribbon particles (lightweight 10 particles)
        self.ribbon_pts = [
            {"angle": random.uniform(0, math.pi * 2),
             "radius": random.uniform(0.6, 1.2),
             "speed": random.uniform(0.02, 0.05),
             "phase": random.uniform(0, math.pi * 2),
             "col_key": random.choice(["GLOW", "GLOW2", "CYAN", "PINK", "VIOLET"])}
            for _ in range(10)]

        self._init_mobile_server()
        self._build()
        self._animate()
        self._start_mic_monitor()
        self._start_system_monitor()
        self.root.after(1000, self._sync_mobile_server_state)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── LAYOUT ────────────────────────────────────────────────────────────────
    def _build(self):
        # Navbar (56px)
        self.navbar = tk.Frame(self.root, bg=self.pal["BG_PANEL"], width=56)
        self.navbar.pack(side="left", fill="y")
        self.navbar.pack_propagate(False)

        # Sidebar (390px)
        self.sidebar = tk.Frame(self.root, bg=self.pal["BG_MID"], width=390)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Separator
        self.sep = tk.Frame(self.root, bg=self.pal["BORDER"], width=1)
        self.sep.pack(side="left", fill="y")

        # Content Area
        self.content = tk.Frame(self.root, bg=self.pal["BG_DEEP"])
        self.content.pack(side="left", fill="both", expand=True)

        self._build_navbar()
        self._build_sidebar()
        self._build_pages()

    # ── NAVBAR ────────────────────────────────────────────────────────────────
    def _build_navbar(self):
        n = self.navbar
        pal = self.pal

        lc = tk.Canvas(n, width=56, height=60, bg=pal["BG_PANEL"], highlightthickness=0)
        lc.pack(pady=(8, 0))
        for i in range(4, 0, -1):
            lc.create_oval(16 - i, 16 - i, 40 + i, 40 + i,
                           fill="", outline=blend(pal["GLOW"], pal["BG_PANEL"], 0.3 + i * 0.15),
                           width=1)
        lc.create_oval(16, 16, 40, 40, fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.6), outline="")
        lc.create_text(28, 28, text="A", font=("Segoe UI", 13, "bold"), fill=pal["WHITE"])

        tk.Frame(n, bg=pal["BORDER"], height=1).pack(fill="x", padx=8, pady=6)

        self._nav_items = [
            ("⌂", "home", "HOME"),
            ("🤖", "agents", "SWARM"),
            ("💬", "chat", "CHAT"),
            ("🖥", "system", "SYS"),
            ("🌐", "browser", "WEB"),
            ("📊", "analytics", "STAT"),
            ("◎", "overview", "CMDS"),
            ("⚙", "settings", "CONF"),
            ("🎤", "mic", "MIC"),
            ("🧠", "memory", "MEM"),
            ("🔍", "search", "SRCH"),
            ("📝", "prompt", "PRMT"),
            ("🔌", "mcp", "MCP"),
        ]
        self.nav_btns = {}
        for icon, pid, label in self._nav_items:
            c = tk.Canvas(n, width=56, height=48, bg=pal["BG_PANEL"],
                          highlightthickness=0, cursor="hand2")
            c.pack()
            self._draw_nav(c, icon, label, pid, pid == "home")
            c.bind("<Button-1>", lambda e, p=pid: self._nav(p))
            c.bind("<Enter>", lambda e, c_=c, i=icon, l=label, p=pid:
                   self._draw_nav(c_, i, l, p, p == self.active_page, True))
            c.bind("<Leave>", lambda e, c_=c, i=icon, l=label, p=pid:
                   self._draw_nav(c_, i, l, p, p == self.active_page))
            self.nav_btns[pid] = (c, icon, label)

        # Status dot at bottom
        tk.Frame(n, bg=pal["BORDER"], height=1).pack(side="bottom", fill="x", padx=8, pady=4)
        self.nav_dot_c = tk.Canvas(n, width=56, height=44, bg=pal["BG_PANEL"], highlightthickness=0)
        self.nav_dot_c.pack(side="bottom")
        self.nav_dot_c.create_oval(22, 6, 34, 18, fill=pal["DGREY"], outline="", tags="dot")
        self.nav_dot_c.create_text(28, 30, text="OFF", font=("Segoe UI", 7, "bold"),
                                   fill=pal["GREY"], tags="lbl")

    def _draw_nav(self, c, icon, label, pid, active=False, hover=False):
        pal = self.pal
        c.delete("all")
        if active:
            for i in range(3, 0, -1):
                c.create_rectangle(0, i, 56, 48 - i,
                                   fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.7 + i * 0.08), outline="")
            c.create_rectangle(0, 0, 56, 48, fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.82), outline="")
            c.create_rectangle(0, 6, 3, 42, fill=pal["GLOW2"], outline="")
        elif hover:
            c.create_rectangle(0, 0, 56, 48, fill=blend(pal["GLOW"], pal["BG_PANEL"], 0.9), outline="")
        else:
            c.create_rectangle(0, 0, 56, 48, fill=pal["BG_PANEL"], outline="")

        col = pal["WHITE"] if active else (pal["LAVENDER"] if hover else pal["GREY"])
        c.create_text(28, 18, text=icon, font=("Segoe UI", 13), fill=col)
        c.create_text(28, 36, text=label, font=("Segoe UI", 6, "bold"), fill=col)

    def _nav(self, page):
        self.active_page = page
        for pid, (c, icon, label) in self.nav_btns.items():
            self._draw_nav(c, icon, label, pid, pid == page)
        for pid, frame in self.pages.items():
            if pid == page:
                frame.lift()
                if hasattr(frame, "_scroll_canvas"):
                    frame._scroll_canvas.yview_moveto(0.0)
                if hasattr(frame, "on_show"):
                    frame.on_show()

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        s = self.sidebar
        pal = self.pal

        # Header
        hdr = tk.Frame(s, bg=pal["BG_MID"])
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(hdr, text="ARIA", font=("Segoe UI", 22, "bold"),
                 bg=pal["BG_MID"], fg=pal["WHITE"]).pack(side="left")
        tk.Label(hdr, text="  v4.5 PRO", font=("Segoe UI", 8, "bold"),
                 bg=pal["BG_MID"], fg=pal["CYAN"]).pack(side="left", pady=(8, 0))

        # Status pill
        self.pill = tk.Frame(hdr, bg=pal["CARD2"], padx=10, pady=4)
        self.pill.pack(side="right", pady=(4, 0))
        self.s_dot = tk.Label(self.pill, text="●", font=("Segoe UI", 8),
                              bg=pal["CARD2"], fg=pal["DGREY"])
        self.s_dot.pack(side="left")
        self.s_lbl = tk.Label(self.pill, text="OFFLINE", font=("Segoe UI", 8, "bold"),
                              bg=pal["CARD2"], fg=pal["GREY"])
        self.s_lbl.pack(side="left", padx=(4, 0))

        # Glowing visual orb
        sz = 260
        self.sphere_sz = sz
        self.sc = tk.Canvas(s, width=sz, height=sz, bg=pal["BG_MID"], highlightthickness=0)
        self.sc.pack(pady=(8, 0))

        # State label
        self.state_lbl = tk.Label(s, text="IDLE", font=("Segoe UI", 10, "bold"),
                                  bg=pal["BG_MID"], fg=pal["GREY"])
        self.state_lbl.pack(pady=(2, 0))

        # Live transcript / state strip
        self.transcript_frame = tk.Frame(s, bg=pal["CARD"], padx=12, pady=8)
        self.transcript_frame.pack(fill="x", padx=16, pady=(8, 0))
        self.transcript_lbl = tk.Label(
            self.transcript_frame,
            text="Ready. Voice or chat active.",
            font=("Segoe UI", 9), bg=pal["CARD"], fg=pal["GREY"],
            wraplength=330, justify="left")
        self.transcript_lbl.pack(anchor="w")

        # Launch Button
        bf = tk.Frame(s, bg=pal["BG_MID"])
        bf.pack(fill="x", padx=16, pady=(12, 0))
        self.start_btn = tk.Button(
            bf, text="▶   LAUNCH ARIA",
            font=("Segoe UI", 11, "bold"),
            bg=pal["GLOW"], fg=pal["WHITE"],
            activebackground=blend(pal["GLOW"], pal["CYAN"], 0.3),
            activeforeground=pal["WHITE"],
            relief="flat", bd=0, pady=11, cursor="hand2",
            command=self._toggle)
        self.start_btn.pack(fill="x")

        # Voice / Chat quick toggle
        mode_row = tk.Frame(s, bg=pal["BG_MID"])
        mode_row.pack(fill="x", padx=16, pady=(8, 0))
        
        self.voice_mode_btn = tk.Button(
            mode_row, text="🎤 VOICE", font=("Segoe UI", 8, "bold"),
            bg=pal["GLOW"], fg=pal["WHITE"],
            activebackground=blend(pal["GLOW"], pal["CYAN"], 0.3),
            activeforeground=pal["WHITE"],
            relief="flat", bd=0, pady=6, cursor="hand2",
            command=lambda: self._set_input_mode("voice"))
        self.voice_mode_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.chat_mode_btn = tk.Button(
            mode_row, text="💬 CHAT", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD2"], fg=pal["GREY"],
            activebackground=blend(pal["GLOW"], pal["CARD2"], 0.3),
            activeforeground=pal["WHITE"],
            relief="flat", bd=0, pady=6, cursor="hand2",
            command=lambda: self._set_input_mode("chat"))
        self.chat_mode_btn.pack(side="left", fill="x", expand=True, padx=(2, 2))

        self.mini_mode_btn = tk.Button(
            mode_row, text="🗗 MINI", font=("Segoe UI", 8, "bold"),
            bg=pal["CARD2"], fg=pal["LAVENDER"],
            activebackground=blend(pal["VIOLET"], pal["CARD2"], 0.3),
            activeforeground=pal["WHITE"],
            relief="flat", bd=0, pady=6, cursor="hand2",
            command=self._toggle_mini_mode)
        self.mini_mode_btn.pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Quick Chat sidebar mini-bar (allows instant typing from anywhere)
        self.chat_input_frame = tk.Frame(s, bg=pal["BG_MID"])
        self.chat_input_frame.pack(fill="x", padx=16, pady=(6, 0))
        
        chat_box = tk.Frame(self.chat_input_frame, bg=pal["CARD2"], padx=6, pady=4)
        chat_box.pack(fill="x")
        self.chat_entry = tk.Entry(chat_box, font=("Segoe UI", 9),
                                   bg=pal["CARD2"], fg=pal["WHITE"],
                                   insertbackground=pal["CYAN"], relief="flat", bd=0)
        self.chat_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.chat_entry.bind("<Return>", lambda e: self._send_quick_chat())
        self.chat_entry.insert(0, "Type a quick command...")
        self.chat_entry.config(fg=pal["GREY"])
        
        def _focus_in(e):
            if self.chat_entry.get() == "Type a quick command...":
                self.chat_entry.delete(0, "end")
                self.chat_entry.config(fg=pal["WHITE"])
        def _focus_out(e):
            if not self.chat_entry.get():
                self.chat_entry.insert(0, "Type a quick command...")
                self.chat_entry.config(fg=pal["GREY"])
        self.chat_entry.bind("<FocusIn>", _focus_in)
        self.chat_entry.bind("<FocusOut>", _focus_out)

        tk.Button(chat_box, text="↵", font=("Segoe UI", 9, "bold"),
                  bg=pal["GLOW"], fg=pal["WHITE"],
                  relief="flat", bd=0, padx=8, cursor="hand2",
                  command=self._send_quick_chat).pack(side="left", padx=(4, 0))

        # Mobile Web Companion Server Control Card
        self.server_frame = tk.Frame(s, bg=pal["CARD2"], padx=10, pady=8)
        self.server_frame.pack(fill="x", padx=16, pady=(10, 0))
        
        srv_hdr = tk.Frame(self.server_frame, bg=pal["CARD2"])
        srv_hdr.pack(fill="x")
        tk.Label(srv_hdr, text="📱 MOBILE SERVER", font=("Segoe UI", 7, "bold"),
                 bg=pal["CARD2"], fg=pal["CYAN"]).pack(side="left")
        self.srv_status_lbl = tk.Label(srv_hdr, text="● ONLINE", font=("Segoe UI", 7, "bold"),
                                       bg=pal["CARD2"], fg=pal["GREEN"])
        self.srv_status_lbl.pack(side="right")
        
        self.srv_url_lbl = tk.Label(self.server_frame, text=getattr(self, "mobile_server_url", "http://0.0.0.0:8765"),
                                    font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=pal["WHITE"], cursor="hand2")
        self.srv_url_lbl.pack(anchor="w", pady=(2, 4))
        self.srv_url_lbl.bind("<Button-1>", lambda e: self._copy_mobile_server_url())

        srv_btn_row = tk.Frame(self.server_frame, bg=pal["CARD2"])
        srv_btn_row.pack(fill="x", pady=(2, 0))
        
        self.toggle_server_btn = tk.Button(
            srv_btn_row, text="🔴 STOP SERVER", font=("Segoe UI", 7, "bold"),
            bg=blend(pal["PINK"], pal["CARD2"], 0.3), fg="#ffffff",
            activebackground=pal["PINK"], activeforeground="#ffffff",
            relief="flat", bd=0, pady=4, cursor="hand2",
            command=self._toggle_mobile_server)
        self.toggle_server_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        tk.Button(
            srv_btn_row, text="📋 COPY", font=("Segoe UI", 7, "bold"),
            bg=pal["BG_MID"], fg=pal["LAVENDER"],
            activebackground=pal["GLOW"], activeforeground="#ffffff",
            relief="flat", bd=0, pady=4, padx=6, cursor="hand2",
            command=self._copy_mobile_server_url).pack(side="left", padx=(2, 0))

        tk.Button(
            srv_btn_row, text="🌐 OPEN", font=("Segoe UI", 7, "bold"),
            bg=pal["BG_MID"], fg=pal["CYAN"],
            activebackground=pal["GLOW"], activeforeground="#ffffff",
            relief="flat", bd=0, pady=4, padx=6, cursor="hand2",
            command=self._open_mobile_server_browser).pack(side="left", padx=(2, 0))

        # Mini Info Row
        row = tk.Frame(s, bg=pal["BG_MID"])
        row.pack(fill="x", padx=16, pady=(10, 0))
        self.model_card = self._mini_card(row, "MODEL", self.config.get("model", "gemini-2.5-flash"), pal["VIOLET"])
        self.model_card.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.user_card = self._mini_card(row, "USER", self.profile.get("name", "Friend"), pal["CYAN"])
        self.user_card.pack(side="left", expand=True, fill="x")

        # Footer
        tk.Label(s, text="Gemini 2.5 Flash · System Context · Chrome Agent",
                 font=("Segoe UI", 7), bg=pal["BG_MID"], fg=pal["DGREY"]).pack(side="bottom", pady=8)

    def _mini_card(self, parent, label, value, accent):
        pal = self.pal
        f = tk.Frame(parent, bg=pal["CARD2"], padx=10, pady=8)
        tk.Label(f, text=label, font=("Segoe UI", 7, "bold"), bg=pal["CARD2"], fg=accent).pack(anchor="w")
        tk.Label(f, text=value, font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=pal["WHITE"]).pack(anchor="w")
        return f


    # ── PAGES ─────────────────────────────────────────────────────────────────
    def _build_pages(self):
        pal = self.pal
        self.pages = {}
        for pid in ["home", "agents", "chat", "system", "browser", "analytics", "overview", "settings",
                    "mic", "memory", "search", "prompt", "mcp"]:
            f = tk.Frame(self.content, bg=pal["BG_DEEP"])
            f.place(x=0, y=0, relwidth=1, relheight=1)
            self.pages[pid] = f

        self._pg_home()
        self._pg_agents()
        self._pg_chat()
        self._pg_system()
        self._pg_browser()
        self._pg_analytics()
        self._pg_overview()
        self._pg_settings()
        self._pg_mic()
        self._pg_memory()
        self._pg_search()
        self._pg_prompt()
        self._pg_mcp()
        
        self.pages["home"].lift()

    def _page_hdr(self, parent, title, sub=""):
        pal = self.pal
        hc = tk.Canvas(parent, height=80, bg=pal["BG_DEEP"], highlightthickness=0)
        hc.pack(fill="x")
        def _draw(e=None):
            w = hc.winfo_width() or 800
            hc.delete("all")
            for i in range(80):
                t = i / 80
                col = blend(blend(pal["GLOW"], pal["BG_DEEP"], 0.85), pal["BG_DEEP"], t)
                hc.create_rectangle(0, i, w, i + 1, fill=col, outline="")
            hc.create_oval(w - 120, -30, w + 30, 110, fill=blend(pal["GLOW2"], pal["BG_DEEP"], 0.88), outline="")
            hc.create_text(32, 32, text=title, font=("Segoe UI", 18, "bold"), fill=pal["WHITE"], anchor="w")
            if sub:
                hc.create_text(32, 56, text=sub, font=("Segoe UI", 9), fill=pal["GREY"], anchor="w")
            for i in range(3, 0, -1):
                hc.create_line(0, 78 + i, w, 78 + i, fill=blend(pal["GLOW"], pal["BG_DEEP"], 0.5 + i * 0.15), width=1)
        hc.bind("<Configure>", _draw)

    # ── HOME PAGE ─────────────────────────────────────────────────────────────
    def _pg_home(self):
        p = self.pages["home"]
        pal = self.pal

        hero = tk.Canvas(p, height=210, bg=pal["BG_DEEP"], highlightthickness=0)
        hero.pack(fill="x")
        hero.bind("<Configure>", lambda e: self._draw_hero(hero))

        bottom = tk.Frame(p, bg=pal["BG_DEEP"])
        bottom.pack(fill="both", expand=True, padx=28, pady=(16, 0))

        cards = [
            ("💬", "Direct AI Chat", "Full conversation panel with intelligent memory.", pal["CYAN"], "chat"),
            ("🖥", "System Awareness", "Real-time context: active window, CPU, clipboard.", pal["VIOLET"], "system"),
            ("🌐", "Chrome Control", "Autonomous browser search, reading & research.", pal["GLOW2"], "browser"),
            ("⚡", "Gemini 2.5 Flash", "Lightning-fast responses with free Google API.", pal["AMBER"], "settings"),
        ]
        for i, (icon, title, desc, col, target_page) in enumerate(cards):
            c = tk.Frame(bottom, bg=pal["CARD2"], padx=16, pady=14, cursor="hand2")
            c.grid(row=0, column=i, sticky="nsew", padx=(0, 8) if i < 3 else (0, 0))
            bottom.columnconfigure(i, weight=1)
            c.bind("<Button-1>", lambda e, tp=target_page: self._nav(tp))

            ic = tk.Canvas(c, width=40, height=40, bg=pal["CARD2"], highlightthickness=0)
            ic.pack(anchor="w")
            ic.create_oval(3, 3, 37, 37, fill=blend(col, pal["CARD2"], 0.8), outline="")
            ic.create_text(20, 20, text=icon, font=("Segoe UI", 15), fill=pal["WHITE"])
            ic.bind("<Button-1>", lambda e, tp=target_page: self._nav(tp))

            lbl_t = tk.Label(c, text=title, font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
            lbl_t.pack(anchor="w", pady=(8, 2))
            lbl_t.bind("<Button-1>", lambda e, tp=target_page: self._nav(tp))

            lbl_d = tk.Label(c, text=desc, font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"],
                             wraplength=180, justify="left")
            lbl_d.pack(anchor="w")
            lbl_d.bind("<Button-1>", lambda e, tp=target_page: self._nav(tp))

            tk.Frame(c, bg=col, height=2).pack(fill="x", side="bottom", pady=(8, 0))

        # Quick Actions Row
        qa_frame = tk.Frame(p, bg=pal["BG_DEEP"], padx=28, pady=12)
        qa_frame.pack(fill="x")
        tk.Label(qa_frame, text="QUICK LAUNCH", font=("Segoe UI", 9, "bold"),
                 bg=pal["BG_DEEP"], fg=pal["LAVENDER"]).pack(anchor="w", pady=(0, 8))
        
        qrow = tk.Frame(qa_frame, bg=pal["BG_DEEP"])
        qrow.pack(fill="x")
        
        ghost_btn(qrow, "💬 Open Full Chat", lambda: self._nav("chat"), col=pal["CYAN"]).pack(side="left", padx=(0, 8))
        ghost_btn(qrow, "🖥 Inspect System", lambda: self._nav("system"), col=pal["VIOLET"]).pack(side="left", padx=(0, 8))
        ghost_btn(qrow, "🌐 Chrome Actions", lambda: self._nav("browser"), col=pal["GLOW2"]).pack(side="left", padx=(0, 8))
        ghost_btn(qrow, "⚙ Check API Key", lambda: self._nav("settings"), col=pal["AMBER"]).pack(side="left")

        # 📱 Mobile Companion Web Server One-Click Card
        srv_box = tk.Frame(p, bg=pal["CARD2"], padx=24, pady=16)
        srv_box.pack(fill="x", padx=28, pady=(8, 16))
        
        sb_top = tk.Frame(srv_box, bg=pal["CARD2"])
        sb_top.pack(fill="x")
        
        tk.Label(sb_top, text="📱 MOBILE & MULTI-DEVICE COMPANION SERVER", font=("Segoe UI", 10, "bold"),
                 bg=pal["CARD2"], fg=pal["CYAN"]).pack(side="left")
        
        self.home_srv_status_lbl = tk.Label(sb_top, text="● SERVER ACTIVE", font=("Segoe UI", 9, "bold"),
                                            bg=pal["CARD2"], fg=pal["GREEN"])
        self.home_srv_status_lbl.pack(side="right")

        tk.Label(srv_box, text="Connect any Smartphone or Tablet on the same local Wi-Fi to chat with voice, switch windows, and execute commands.",
                 font=("Segoe UI", 9), bg=pal["CARD2"], fg=pal["GREY"]).pack(anchor="w", pady=(4, 8))

        sb_mid = tk.Frame(srv_box, bg=pal["CARD2"])
        sb_mid.pack(fill="x", pady=(0, 10))
        
        tk.Label(sb_mid, text="Local LAN URL:", font=("Segoe UI", 8, "bold"),
                 bg=pal["CARD2"], fg=pal["LAVENDER"]).pack(side="left")
                 
        self.home_srv_url_lbl = tk.Label(sb_mid, text=getattr(self, "mobile_server_url", "http://0.0.0.0:8765"),
                                         font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=pal["CYAN"], cursor="hand2")
        self.home_srv_url_lbl.pack(side="left", padx=(8, 0))
        self.home_srv_url_lbl.bind("<Button-1>", lambda e: self._copy_mobile_server_url())

        sb_btn_row = tk.Frame(srv_box, bg=pal["CARD2"])
        sb_btn_row.pack(fill="x")

        self.home_srv_toggle_btn = tk.Button(
            sb_btn_row, text="🔴 TURN OFF SERVER", font=("Segoe UI", 9, "bold"),
            bg=blend(pal["PINK"], pal["CARD2"], 0.3), fg="#ffffff",
            activebackground=pal["PINK"], activeforeground="#ffffff",
            relief="flat", bd=0, pady=8, padx=16, cursor="hand2",
            command=self._toggle_mobile_server)
        self.home_srv_toggle_btn.pack(side="left", padx=(0, 8))

        tk.Button(
            sb_btn_row, text="📋 COPY MOBILE LINK", font=("Segoe UI", 9, "bold"),
            bg=pal["BG_MID"], fg=pal["LAVENDER"],
            activebackground=pal["GLOW"], activeforeground="#ffffff",
            relief="flat", bd=0, pady=8, padx=14, cursor="hand2",
            command=self._copy_mobile_server_url).pack(side="left", padx=(0, 8))

        tk.Button(
            sb_btn_row, text="🌐 OPEN IN BROWSER", font=("Segoe UI", 9, "bold"),
            bg=pal["BG_MID"], fg=pal["CYAN"],
            activebackground=pal["GLOW"], activeforeground="#ffffff",
            relief="flat", bd=0, pady=8, padx=14, cursor="hand2",
            command=self._open_mobile_server_browser).pack(side="left")


    def _draw_hero(self, c):
        pal = self.pal
        w = c.winfo_width() or 900
        c.delete("all")
        for i in range(210):
            t = i / 210
            col = blend(blend(pal["BG_MID"], pal["BG_DEEP"], t * 0.6), pal["BG_DEEP"], t * 0.4)
            c.create_rectangle(0, i, w, i + 1, fill=col, outline="")

        for st in self.stars:
            sx = int(st["x"] * w)
            sy = int(st["y"] * 180)
            col = blend(pal["WHITE"], pal["BG_DEEP"], 0.5 + st["bright"] * 0.45)
            r = st["r"]
            c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=col, outline="")

        name = self.profile.get("name", "Friend")
        c.create_text(36, 44, anchor="w", text="Welcome back,", font=("Segoe UI", 16), fill=pal["GREY"])
        c.create_text(36, 78, anchor="w", text=f"{name}", font=("Segoe UI", 26, "bold"), fill=pal["WHITE"])
        c.create_text(36, 116, anchor="w", text="Aria is armed with Gemini 2.5 Flash, full system awareness, and Chrome automation.",
                      font=("Segoe UI", 10), fill=pal["LAVENDER"])
        
        # Pill indicator
        c.create_oval(36, 140, 140, 168, fill=pal["GLOW"], outline="")
        c.create_text(88, 154, text="System Active", font=("Segoe UI", 8, "bold"), fill=pal["WHITE"])

    # ── FULL-SCREEN CHAT PAGE ─────────────────────────────────────────────────
    def _pg_chat(self):
        p = self.pages["chat"]
        pal = self.pal
        self._page_hdr(p, "INTERACTIVE CHAT", "Conversation stream with Gemini 2.5 Flash & System Memory")

        # Main chat layout
        wrap = tk.Frame(p, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(10, 20))

        # Suggestion Chips
        chips_frame = tk.Frame(wrap, bg=pal["BG_DEEP"])
        chips_frame.pack(fill="x", pady=(0, 8))
        
        suggestions = [
            "What window am I using right now?",
            "Summarize my clipboard text",
            "Research top Python AI frameworks",
            "Open Chrome and go to youtube.com",
            "What's my CPU and RAM usage?",
        ]
        for sug in suggestions:
            btn = tk.Button(chips_frame, text=sug, font=("Segoe UI", 8),
                            bg=pal["CARD2"], fg=pal["LAVENDER"],
                            activebackground=blend(pal["GLOW"], pal["CARD2"], 0.3),
                            activeforeground=pal["WHITE"],
                            relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                            command=lambda s=sug: self._apply_chat_prompt(s))
            btn.pack(side="left", padx=(0, 6))

        # Message Scroll Area
        self.chat_canvas = tk.Canvas(wrap, bg=pal["CARD"], highlightthickness=0)
        self.chat_scroll = tk.Scrollbar(wrap, orient="vertical", command=self.chat_canvas.yview,
                                        bg=pal["CARD"], troughcolor=pal["BG_DEEP"], width=6)
        self.chat_canvas.configure(yscrollcommand=self.chat_scroll.set)
        
        self.chat_scroll.pack(side="right", fill="y")
        self.chat_canvas.pack(side="top", fill="both", expand=True)

        self.chat_inner = tk.Frame(self.chat_canvas, bg=pal["CARD"])
        self.chat_win = self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")
        
        self.chat_inner.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(self.chat_win, width=e.width))

        # Welcome message
        self._add_chat_bubble("assistant", f"Hello {self.profile.get('name', 'Friend')}! I am Aria. How can I help you today?")

        # Input Bar
        input_bar = tk.Frame(wrap, bg=pal["CARD2"], padx=10, pady=8)
        input_bar.pack(fill="x", pady=(10, 0))

        self.full_chat_entry = tk.Entry(input_bar, font=("Segoe UI", 11),
                                        bg=pal["CARD2"], fg=pal["WHITE"],
                                        insertbackground=pal["CYAN"], relief="flat", bd=0)
        self.full_chat_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(4, 8))
        self.full_chat_entry.bind("<Return>", lambda e: self._send_full_chat())
        self.full_chat_entry.focus_set()

        glow_btn(input_bar, "Send Message  ➤", self._send_full_chat, c1=pal["GLOW"], c2=pal["CYAN"]).pack(side="left")
        danger_btn(input_bar, "Clear", self._clear_full_chat).pack(side="left", padx=(6, 0))

    def _apply_chat_prompt(self, prompt_text):
        self.full_chat_entry.delete(0, "end")
        self.full_chat_entry.insert(0, prompt_text)
        self._send_full_chat()

    def _add_chat_bubble(self, role, text):
        pal = self.pal
        is_user = (role == "user")
        
        bubble_row = tk.Frame(self.chat_inner, bg=pal["CARD"], pady=6)
        bubble_row.pack(fill="x", padx=16)

        bubble_bg = blend(pal["GLOW"], pal["CARD2"], 0.4) if is_user else pal["CARD2"]
        bubble_fg = pal["WHITE"]
        align = "e" if is_user else "w"
        
        box = tk.Frame(bubble_row, bg=bubble_bg, padx=14, pady=10)
        box.pack(anchor=align, padx=4)

        sender_tag = "You" if is_user else "Aria"
        sender_col = pal["CYAN"] if is_user else pal["VIOLET"]
        
        tk.Label(box, text=sender_tag, font=("Segoe UI", 8, "bold"), bg=bubble_bg, fg=sender_col).pack(anchor="w")
        tk.Label(box, text=text, font=("Segoe UI", 10), bg=bubble_bg, fg=bubble_fg,
                 wraplength=600, justify="left").pack(anchor="w", pady=(2, 0))

        # Auto scroll to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def _send_full_chat(self):
        text = self.full_chat_entry.get().strip()
        if not text:
            return
        self.full_chat_entry.delete(0, "end")
        self._add_chat_bubble("user", text)
        threading.Thread(target=self._process_chat_input_custom, args=(text,), daemon=True).start()

    def _send_quick_chat(self):
        text = self.chat_entry.get().strip()
        if not text or text == "Type a quick command...":
            return
        self.chat_entry.delete(0, "end")
        if hasattr(self, "_add_chat_bubble"):
            self._add_chat_bubble("user", text)
        threading.Thread(target=self._process_chat_input_custom, args=(text,), daemon=True).start()

    def _clear_full_chat(self):
        for w in self.chat_inner.winfo_children():
            w.destroy()
        self.chat_history = []
        self._add_chat_bubble("assistant", "Chat history cleared. What's on your mind?")

    def _process_chat_input_custom(self, raw_text: str):
        text = raw_text.strip()[:1000]
        # Sanitise
        dangerous = [
            (r"[`$]", ""),
            (r";\s*(rm|del|format|shutdown|kill|exec|eval|import os)", " [blocked] "),
            (r"__import__\s*\(", "[blocked]("),
        ]
        for pattern, replacement in dangerous:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        if not text:
            return

        self.root.after(0, lambda: self.state_lbl.config(text="THINKING...", fg=self.pal["VIOLET"]))

        # Check local instant tools first
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import agent as agent_mod
            handled, response = agent_mod.run_tools(text.lower())
            if handled:
                self.root.after(0, lambda r=response: self._add_chat_bubble("assistant", r))
                self.root.after(0, lambda: self.state_lbl.config(text="IDLE", fg=self.pal["GREY"]))
                return
        except Exception:
            pass

        key = self.config.get("gemini_api_key", os.environ.get("GEMINI_API_KEY", ""))

        try:
            import aria_adk
            adk_engine = aria_adk.get_adk_engine(gemini_key=key)
            user_name = self.profile.get("name", "Friend")
            prefs = ", ".join(self.profile.get("preferences", [])) or "none"

            def on_status_update(status_text: str):
                self.root.after(0, lambda s=status_text: self.state_lbl.config(text=s.upper(), fg=self.pal["CYAN"]))

            reply = adk_engine.run_turn(
                user_input=text,
                chat_history=self.chat_history,
                user_name=user_name,
                preferences=prefs,
                on_status_callback=on_status_update
            )

            self.chat_history.append({"role": "user", "content": text})
            self.chat_history.append({"role": "aria", "content": reply})

            self.root.after(0, lambda r=reply: self._add_chat_bubble("assistant", r))
            self.root.after(0, lambda: self.state_lbl.config(text="IDLE", fg=self.pal["GREY"]))

            # Speak if speech enabled
            try:
                import agent as agent_mod
                threading.Thread(target=agent_mod.speak, args=(reply,), daemon=True).start()
            except Exception:
                pass

            # Immediate RAM reclaim
            import gc
            gc.collect()

        except Exception as e:
            err = str(e)
            self.root.after(0, lambda err=err: self._add_chat_bubble("assistant", f"Error: {err}"))
            self.root.after(0, lambda: self.state_lbl.config(text="IDLE", fg=self.pal["GREY"]))

    # ── SUB-AGENTS SWARM VISUALIZER PAGE ──────────────────────────────────────
    def _pg_agents(self):
        p = self.pages["agents"]
        pal = self.pal
        self._page_hdr(p, "SUB-AGENTS SWARM & ADK TOPOLOGY", "Interactive Neural Swarm Visualizer, Real-Time Routing & Sub-Agent Control")

        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(10, 40))

        # 1. Interactive Swarm Topology Graph
        section_lbl(wrap, "LIVE NEURAL TOPOLOGY GRAPH")
        graph_card = tk.Frame(wrap, bg=pal["CARD2"], padx=10, pady=10)
        graph_card.pack(fill="x", pady=(0, 16))

        self.swarm_canvas = tk.Canvas(graph_card, height=270, bg=pal["CARD"], highlightthickness=0)
        self.swarm_canvas.pack(fill="x")
        self.swarm_canvas.bind("<Configure>", lambda e: self._draw_swarm_graph())

        # 2. Sub-Agent Node Status & Action Cards Grid
        section_lbl(wrap, "SPECIALIZED SUB-AGENT DOMAINS")
        grid = tk.Frame(wrap, bg=pal["BG_DEEP"])
        grid.pack(fill="x", pady=(0, 16))
        for col_i in range(3):
            grid.columnconfigure(col_i, weight=1)

        agents_data = [
            ("💻 System & OS Agent", "system", "Controls Windows apps, manages volume, executes PowerShell, organizes files.", pal["CYAN"], "Test File Search", "Find and open any PDF on desktop"),
            ("🌐 Browser & Web Agent", "browser", "Chrome automation, web search RAG, live crypto prices, news headlines, and Wikipedia.", pal["GREEN"], "Test Crypto Lookup", "What is the live price of Bitcoin?"),
            ("👁️ Screen Vision Agent", "vision", "Multimodal screen inspection, OCR text reading, UI button grounding and clicking.", pal["PINK"], "Test Screen Vision", "What window is currently open on my screen?"),
            ("🧠 Memory & Planner", "memory", "Episodic timeline recall, daily goal tracking, multi-user profiles, alarm reminders.", pal["LAVENDER"], "Test Goal Tracker", "List all my active goals"),
            ("🔌 MCP & IoT Agent", "mcp", "Model Context Protocol bridge for Home Assistant smart lights, WhatsApp messaging.", pal["AMBER"], "Test Network Status", "What is my network status?"),
            ("👑 Core Orchestrator", "orchestrator", "Top-level intent router using Gemini 2.5 Flash & Groq multi-tier AI brain.", pal["GLOW"], "Test Quick Thought", "Tell me a short witty thought"),
        ]

        for idx, (title, aid, desc, accent, btn_txt, test_cmd) in enumerate(agents_data):
            r, c_idx = divmod(idx, 3)
            card = tk.Frame(grid, bg=pal["CARD2"], padx=14, pady=12)
            card.grid(row=r, column=c_idx, sticky="nsew", padx=4, pady=4)

            hdr_row = tk.Frame(card, bg=pal["CARD2"])
            hdr_row.pack(fill="x")
            tk.Label(hdr_row, text=title, font=("Segoe UI", 9, "bold"), bg=pal["CARD2"], fg=accent).pack(side="left")
            tk.Label(hdr_row, text="● READY", font=("Segoe UI", 7, "bold"), bg=pal["CARD2"], fg=pal["GREEN"]).pack(side="right")

            tk.Label(card, text=desc, font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"], wraplength=210, justify="left").pack(anchor="w", pady=(4, 8))

            tk.Button(card, text=f"⚡ {btn_txt}", font=("Segoe UI", 7, "bold"),
                      bg=pal["BG_MID"], fg=accent, activebackground=accent, activeforeground=pal["WHITE"],
                      relief="flat", bd=0, pady=4, cursor="hand2",
                      command=lambda cmd=test_cmd: self._test_subagent_action(cmd)).pack(fill="x")

        # 3. Real-Time Swarm Activity Log Stream
        log_hdr = tk.Frame(wrap, bg=pal["BG_DEEP"])
        log_hdr.pack(fill="x")
        section_lbl(log_hdr, "LIVE SWARM DISPATCH & EXECUTION LOGS")
        
        self.swarm_log_frame = tk.Frame(wrap, bg=pal["CARD2"], padx=14, pady=12)
        self.swarm_log_frame.pack(fill="x")

        self.swarm_log_txt = tk.Text(self.swarm_log_frame, height=9, bg=pal["BG_DEEP"], fg=pal["CYAN"],
                                     font=("JetBrains Mono", 8), relief="flat", bd=0, padx=8, pady=8)
        self.swarm_log_txt.pack(fill="x")
        self.swarm_log_txt.config(state="disabled")

        p.on_show = self._refresh_swarm_page

    def _draw_swarm_graph(self):
        c = getattr(self, "swarm_canvas", None)
        if not c:
            return
        pal = self.pal
        w = c.winfo_width() or 700
        h = 270
        c.delete("all")

        cx, cy = w / 2, h / 2

        # 5 Satellite Sub-Agents
        nodes = [
            {"id": "system", "name": "System & OS", "icon": "💻", "col": pal["CYAN"], "tools": "9 tools", "angle": -math.pi / 2},
            {"id": "browser", "name": "Browser & Web", "icon": "🌐", "col": pal["GREEN"], "tools": "7 tools", "angle": -math.pi / 2 + 2 * math.pi / 5},
            {"id": "vision", "name": "Screen Vision", "icon": "👁️", "col": pal["PINK"], "tools": "2 tools", "angle": -math.pi / 2 + 4 * math.pi / 5},
            {"id": "memory", "name": "Memory & Plan", "icon": "🧠", "col": pal["LAVENDER"], "tools": "5 tools", "angle": -math.pi / 2 + 6 * math.pi / 5},
            {"id": "mcp", "name": "MCP & IoT", "icon": "🔌", "col": pal["AMBER"], "tools": "2 tools", "angle": -math.pi / 2 + 8 * math.pi / 5},
        ]

        radius = min(w / 2.6, 110)

        # Draw connecting energy lines
        for n in nodes:
            nx = cx + radius * math.cos(n["angle"])
            ny = cy + radius * math.sin(n["angle"]) * 0.82

            # Glow line
            c.create_line(cx, cy, nx, ny, fill=blend(n["col"], pal["CARD"], 0.6), width=3)
            c.create_line(cx, cy, nx, ny, fill=n["col"], width=1, dash=(4, 4))

            # Pulse dot halfway
            px = cx + (nx - cx) * 0.52
            py = cy + (ny - cy) * 0.52
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill=n["col"], outline="")

        # Draw Center Orchestrator Node
        c.create_oval(cx - 46, cy - 46, cx + 46, cy + 46, fill=blend(pal["GLOW"], pal["BG_MID"], 0.5), outline=pal["GLOW2"], width=2)
        c.create_oval(cx - 38, cy - 38, cx + 38, cy + 38, fill=pal["BG_MID"], outline="")
        c.create_text(cx, cy - 10, text="👑", font=("Segoe UI", 16))
        c.create_text(cx, cy + 10, text="ORCHESTRATOR", font=("Segoe UI", 7, "bold"), fill=pal["WHITE"])
        c.create_text(cx, cy + 22, text="Gemini 2.5 Flash", font=("Segoe UI", 6), fill=pal["CYAN"])

        # Draw Satellite Nodes
        for n in nodes:
            nx = cx + radius * math.cos(n["angle"])
            ny = cy + radius * math.sin(n["angle"]) * 0.82

            # Node card
            bw, bh = 42, 28
            c.create_oval(nx - 24, ny - 24, nx + 24, ny + 24, fill=blend(n["col"], pal["CARD2"], 0.4), outline=n["col"], width=1.5)
            c.create_oval(nx - 20, ny - 20, nx + 20, ny + 20, fill=pal["CARD2"], outline="")
            c.create_text(nx, ny - 4, text=n["icon"], font=("Segoe UI", 12))
            c.create_text(nx, ny + 10, text="● READY", font=("Segoe UI", 5, "bold"), fill=pal["GREEN"])

            # Outer label
            lbl_y = ny + 32 if ny >= cy else ny - 32
            c.create_text(nx, lbl_y, text=n["name"], font=("Segoe UI", 8, "bold"), fill=pal["WHITE"])
            c.create_text(nx, lbl_y + (10 if ny >= cy else -10), text=n["tools"], font=("Segoe UI", 6), fill=n["col"])

    def _refresh_swarm_page(self):
        self._draw_swarm_graph()
        try:
            import aria_adk
            logs = aria_adk.get_swarm_activity_log()
            if hasattr(self, "swarm_log_txt"):
                self.swarm_log_txt.config(state="normal")
                self.swarm_log_txt.delete("1.0", "end")
                for item in logs[:15]:
                    agent = item.get("agent", "Agent")
                    tool = item.get("tool", "")
                    lat = item.get("latency_ms", 0.0)
                    t_str = item.get("time", "")
                    res = item.get("result", "")
                    line = f"[{t_str}] ➜ [{agent}] Executed '{tool}' in {lat}ms | Result: {res}\n"
                    self.swarm_log_txt.insert("end", line)
                self.swarm_log_txt.config(state="disabled")
        except Exception:
            pass

    def _test_subagent_action(self, cmd: str):
        self._nav("chat")
        if hasattr(self, "full_chat_entry"):
            self.full_chat_entry.delete(0, "end")
            self.full_chat_entry.insert(0, cmd)
            self._send_full_chat()

    # ── SYSTEM CONTEXT MONITOR PAGE ───────────────────────────────────────────
    def _pg_system(self):
        p = self.pages["system"]
        pal = self.pal
        self._page_hdr(p, "SYSTEM CONTEXT MONITOR", "Real-Time Hardware, Active Window & Process Intelligence")

        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(10, 40))

        # Hardware Metrics Row (CPU, RAM, DISK)
        section_lbl(wrap, "LIVE RESOURCE GAUGES")
        gauges_row = tk.Frame(wrap, bg=pal["BG_DEEP"])
        gauges_row.pack(fill="x", pady=(0, 10))
        gauges_row.columnconfigure(0, weight=1)
        gauges_row.columnconfigure(1, weight=1)
        gauges_row.columnconfigure(2, weight=1)

        self.cpu_card, self.cpu_bar, self.cpu_lbl = self._create_gauge_card(gauges_row, "CPU USAGE", pal["CYAN"], 0)
        self.ram_card, self.ram_bar, self.ram_lbl = self._create_gauge_card(gauges_row, "RAM MEMORY", pal["VIOLET"], 1)
        self.disk_card, self.disk_bar, self.disk_lbl = self._create_gauge_card(gauges_row, "DISK SPACE", pal["PINK"], 2)

        # Active Window Card
        section_lbl(wrap, "ACTIVE FOCUSED WINDOW")
        self.win_card = tk.Frame(wrap, bg=pal["CARD2"], padx=18, pady=14)
        self.win_card.pack(fill="x")
        
        self.win_title_lbl = tk.Label(self.win_card, text="Detecting active window...",
                                      font=("Segoe UI", 11, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        self.win_title_lbl.pack(anchor="w")
        self.win_proc_lbl = tk.Label(self.win_card, text="Process: scanning",
                                     font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"])
        self.win_proc_lbl.pack(anchor="w", pady=(2, 0))

        # Clipboard Monitor Card
        section_lbl(wrap, "LIVE CLIPBOARD PREVIEW")
        clip_card = tk.Frame(wrap, bg=pal["CARD2"], padx=18, pady=14)
        clip_card.pack(fill="x")

        self.clip_text_lbl = tk.Label(clip_card, text="Clipboard is empty or inaccessible.",
                                      font=("Segoe UI", 9), bg=pal["CARD2"], fg=pal["LAVENDER"],
                                      wraplength=700, justify="left")
        self.clip_text_lbl.pack(anchor="w", pady=(0, 8))

        clip_btn_row = tk.Frame(clip_card, bg=pal["CARD2"])
        clip_btn_row.pack(anchor="w")
        ghost_btn(clip_btn_row, "📋 Copy To Prompt", self._copy_clip_to_chat, col=pal["CYAN"]).pack(side="left", padx=(0, 6))
        danger_btn(clip_btn_row, "Clear Clipboard", self._clear_clipboard).pack(side="left")

        # Running Applications List
        section_lbl(wrap, "TOP RUNNING PROCESSES")
        self.proc_list_frame = tk.Frame(wrap, bg=pal["BG_DEEP"])
        self.proc_list_frame.pack(fill="x")

        p.on_show = self._refresh_system_data

    def _create_gauge_card(self, parent, title, accent, col_idx):
        pal = self.pal
        card = tk.Frame(parent, bg=pal["CARD2"], padx=16, pady=14)
        card.grid(row=0, column=col_idx, sticky="nsew", padx=(0, 6) if col_idx < 2 else (0, 0))
        
        tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=accent).pack(anchor="w")
        val_lbl = tk.Label(card, text="0%", font=("Segoe UI", 16, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        val_lbl.pack(anchor="w", pady=(4, 6))

        bar_canvas = tk.Canvas(card, height=6, bg=pal["CARD"], highlightthickness=0)
        bar_canvas.pack(fill="x")
        return card, bar_canvas, val_lbl

    def _copy_clip_to_chat(self):
        if HAS_PYPERCLIP:
            t = pyperclip.paste().strip()
            if t:
                self._nav("chat")
                self.full_chat_entry.delete(0, "end")
                self.full_chat_entry.insert(0, f"Summarize this: {t}")

    def _clear_clipboard(self):
        if HAS_PYPERCLIP:
            pyperclip.copy("")
            self.clip_text_lbl.config(text="Clipboard cleared.")

    def _start_system_monitor(self):
        def _loop():
            while True:
                time.sleep(5.0)
                if self.active_page == "system":
                    try:
                        self.root.after(0, self._refresh_system_data)
                    except Exception:
                        break
        threading.Thread(target=_loop, daemon=True).start()

    def _refresh_system_data(self):
        pal = self.pal
        if HAS_PSUTIL:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage("/").percent

                self.cpu_lbl.config(text=f"{cpu:.1f}%")
                self.ram_lbl.config(text=f"{ram:.1f}%")
                self.disk_lbl.config(text=f"{disk:.1f}%")

                def _draw_bar(canvas, pct, col):
                    w = canvas.winfo_width() or 180
                    canvas.delete("all")
                    canvas.create_rectangle(0, 0, w, 6, fill=pal["CARD"], outline="")
                    fill_w = int(w * (pct / 100.0))
                    canvas.create_rectangle(0, 0, fill_w, 6, fill=col, outline="")

                _draw_bar(self.cpu_bar, cpu, pal["CYAN"])
                _draw_bar(self.ram_bar, ram, pal["VIOLET"])
                _draw_bar(self.disk_bar, disk, pal["PINK"])
            except Exception:
                pass

        # Active Window
        try:
            import pygetwindow as gw
            win = gw.getActiveWindow()
            if win and win.title:
                self.win_title_lbl.config(text=win.title[:80])
                self.win_proc_lbl.config(text=f"Window Size: {win.width}x{win.height}")
            else:
                self.win_title_lbl.config(text="No active window detected")
        except Exception:
            pass

        # Clipboard
        if HAS_PYPERCLIP:
            try:
                clip = pyperclip.paste().strip()
                self.clip_text_lbl.config(text=(clip[:250] + "...") if len(clip) > 250 else (clip or "Clipboard is empty"))
            except Exception:
                pass

        # Top processes
        if HAS_PSUTIL:
            for w in self.proc_list_frame.winfo_children():
                w.destroy()
            try:
                procs = []
                for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                    try:
                        procs.append(p.info)
                    except Exception:
                        pass
                procs = sorted(procs, key=lambda x: x.get('cpu_percent') or 0, reverse=True)[:5]
                for pr in procs:
                    row = tk.Frame(self.proc_list_frame, bg=pal["CARD2"], padx=12, pady=6)
                    row.pack(fill="x", pady=2)
                    tk.Label(row, text=pr.get('name', 'Unknown'), font=("Segoe UI", 9, "bold"),
                             bg=pal["CARD2"], fg=pal["WHITE"]).pack(side="left")
                    tk.Label(row, text=f"RAM: {pr.get('memory_percent', 0):.1f}% | CPU: {pr.get('cpu_percent', 0):.1f}%",
                             font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["CYAN"]).pack(side="right")
            except Exception:
                pass

    # ── ENHANCED BROWSER HUB ──────────────────────────────────────────────────
    def _pg_browser(self):
        p = self.pages["browser"]
        pal = self.pal
        self._page_hdr(p, "CHROME AUTOMATION HUB", "Autonomous Web Agent & Interactive Navigation")

        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(10, 40))

        # Status & Control Card
        section_lbl(wrap, "CHROME AGENT STATUS")
        status_card = tk.Frame(wrap, bg=pal["CARD2"], padx=18, pady=16)
        status_card.pack(fill="x")

        status_top = tk.Frame(status_card, bg=pal["CARD2"])
        status_top.pack(fill="x")
        self.browser_dot = tk.Label(status_top, text="●", font=("Segoe UI", 14), bg=pal["CARD2"], fg=pal["DGREY"])
        self.browser_dot.pack(side="left")
        self.browser_status_lbl = tk.Label(status_top, text="  Chrome is not running",
                                           font=("Segoe UI", 10, "bold"), bg=pal["CARD2"], fg=pal["GREY"])
        self.browser_status_lbl.pack(side="left")

        self.browser_url_lbl = tk.Label(status_card, text="", font=("Segoe UI", 8),
                                        bg=pal["CARD2"], fg=pal["CYAN"], wraplength=600, justify="left")
        self.browser_url_lbl.pack(anchor="w", pady=(6, 0))

        btn_row = tk.Frame(status_card, bg=pal["CARD2"])
        btn_row.pack(anchor="w", pady=(12, 0))
        ghost_btn(btn_row, "↻ Refresh Status", self._refresh_browser_status, col=pal["CYAN"]).pack(side="left", padx=(0, 6))
        danger_btn(btn_row, "✕ Stop Chrome", self._stop_chrome).pack(side="left")

        # Quick Actions Bar
        section_lbl(wrap, "ONE-CLICK WEB ACTIONS")
        act_row = tk.Frame(wrap, bg=pal["BG_DEEP"])
        act_row.pack(fill="x")
        
        ghost_btn(act_row, "🔍 Research Query", lambda: self._quick_web_action("research"), col=pal["CYAN"]).pack(side="left", padx=(0, 6))
        ghost_btn(act_row, "📖 Read Current Page", lambda: self._quick_web_action("read"), col=pal["VIOLET"]).pack(side="left", padx=(0, 6))
        ghost_btn(act_row, "📑 List Tabs", lambda: self._quick_web_action("tabs"), col=pal["GLOW2"]).pack(side="left", padx=(0, 6))
        ghost_btn(act_row, "🌐 Google Search", lambda: self._quick_web_action("search"), col=pal["AMBER"]).pack(side="left")

        # Manual URL Bar
        section_lbl(wrap, "URL DIRECT NAVIGATION")
        nav_row = tk.Frame(wrap, bg=pal["CARD2"], padx=10, pady=8)
        nav_row.pack(fill="x")

        self.browser_url_entry = tk.Entry(nav_row, font=("Segoe UI", 10), bg=pal["CARD2"], fg=pal["WHITE"],
                                          insertbackground=pal["CYAN"], relief="flat", bd=0)
        self.browser_url_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.browser_url_entry.insert(0, "https://google.com")

        glow_btn(nav_row, "Navigate  ➤", self._browser_go, c1=pal["GLOW"], c2=pal["CYAN"]).pack(side="left")

        # Active Tabs Frame
        section_lbl(wrap, "OPEN TABS")
        self.tabs_list_frame = tk.Frame(wrap, bg=pal["BG_DEEP"])
        self.tabs_list_frame.pack(fill="x")

        p.on_show = self._refresh_browser_status

    def _quick_web_action(self, action_type):
        def _run():
            try:
                from aria_chrome import get_chrome_agent
                agent = get_chrome_agent()
                if action_type == "read":
                    res = agent.read_page()
                    self._nav("chat")
                    self._add_chat_bubble("assistant", f"Page Summary:\n{res}")
                elif action_type == "tabs":
                    tabs = agent.get_tabs()
                    tab_str = "\n".join([f"• {'[Active] ' if t.get('active') else ''}{t['title']} ({t['url'][:40]}...)" for t in tabs])
                    self._nav("chat")
                    self._add_chat_bubble("assistant", f"Open Tabs:\n{tab_str}")
                elif action_type == "search":
                    agent.search_google("AI technology news")
                    self.root.after(1000, self._refresh_browser_status)
                elif action_type == "research":
                    self._nav("chat")
                    self.full_chat_entry.insert(0, "Research the best AI productivity tools in 2026")
            except Exception as e:
                self.root.after(0, lambda: self.browser_status_lbl.config(text=f"Error: {e}", fg=self.pal["PINK"]))
        threading.Thread(target=_run, daemon=True).start()

    def _refresh_browser_status(self):
        pal = self.pal
        try:
            from aria_chrome import get_chrome_agent
            agent = get_chrome_agent()
            if agent.is_open():
                status = agent.status()
                self.browser_dot.config(fg=pal["CYAN"])
                self.browser_status_lbl.config(text=f"  Chrome Running — {status.get('tab_count', 1)} Open Tab(s)", fg=pal["CYAN"])
                self.browser_url_lbl.config(text=f"Active Page: {status.get('current_title', '')}\nURL: {status.get('current_url', '')}")

                for w in self.tabs_list_frame.winfo_children():
                    w.destroy()
                for tab in status.get("tabs", []):
                    r = tk.Frame(self.tabs_list_frame, bg=pal["CARD2"], padx=12, pady=8)
                    r.pack(fill="x", pady=2)
                    prefix = "▶ [Active] " if tab.get("active") else "• "
                    tk.Label(r, text=f"{prefix}{tab.get('title', '')[:50]}",
                             font=("Segoe UI", 9, "bold" if tab.get("active") else "normal"),
                             bg=pal["CARD2"], fg=pal["WHITE"] if tab.get("active") else pal["GREY"]).pack(side="left")
                    ghost_btn(r, "Switch", lambda idx=tab.get("index", 0): self._switch_tab(idx), col=pal["CYAN"]).pack(side="right")
            else:
                self.browser_dot.config(fg=pal["DGREY"])
                self.browser_status_lbl.config(text="  Chrome is not running", fg=pal["GREY"])
                self.browser_url_lbl.config(text="")
        except Exception as e:
            self.browser_status_lbl.config(text=f"  Status check: {e}", fg=pal["AMBER"])

    def _switch_tab(self, handle):
        def _run():
            try:
                from aria_chrome import get_chrome_agent
                agent = get_chrome_agent()
                agent.switch_tab(handle)
                self.root.after(500, self._refresh_browser_status)
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    def _stop_chrome(self):
        try:
            from aria_chrome import close_chrome
            close_chrome()
            self._refresh_browser_status()
        except Exception as e:
            self.browser_status_lbl.config(text=f"Error: {e}", fg=self.pal["PINK"])

    def _browser_go(self):
        url = self.browser_url_entry.get().strip()
        if not url:
            return
        def _go():
            try:
                from aria_chrome import get_chrome_agent
                agent = get_chrome_agent()
                agent.open_url(url)
                self.root.after(1200, self._refresh_browser_status)
            except Exception as e:
                self.root.after(0, lambda: self.browser_status_lbl.config(text=f"Error: {e}", fg=self.pal["PINK"]))
        threading.Thread(target=_go, daemon=True).start()

    # ── COMMANDS OVERVIEW ─────────────────────────────────────────────────────
    def _pg_overview(self):
        p = self.pages["overview"]
        pal = self.pal
        self._page_hdr(p, "COMMAND DIRECTORY", "Voice & Chat Shortcuts")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 40))

        cmds = [
            (pal["GLOW"],   "🌤️", "WEATHER",     '"What\'s the weather today?"'),
            (pal["GLOW2"],  "🌐", "WEB SEARCH",  '"Search for quantum computing news"'),
            (pal["VIOLET"], "💻", "OPEN APPS",   '"Open Notepad / Chrome / VS Code"'),
            (pal["PINK"],   "🎵", "YOUTUBE",     '"Play synthwave music"'),
            (pal["CYAN"],   "🔍", "RESEARCH",    '"Research the best laptops under 60000"'),
            (pal["AMBER"],  "📖", "READ PAGE",   '"Read this page and summarize it"'),
            (pal["GLOW"],   "🕐", "TIME & DATE", '"What time is it?"'),
            (pal["GLOW2"],  "🔒", "LOCK PC",     '"Lock my computer"'),
            (pal["VIOLET"], "🔊", "VOLUME",      '"Volume up / down / mute"'),
            (pal["PINK"],   "📸", "SCREENSHOT",  '"Take a screenshot"'),
        ]
        grid = tk.Frame(wrap, bg=pal["BG_DEEP"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        for i, (col, icon, title, ex) in enumerate(cmds):
            ci, ri = i % 2, i // 2
            c = tk.Frame(grid, bg=pal["CARD2"], padx=14, pady=12)
            c.grid(row=ri, column=ci, sticky="nsew", padx=(0, 6) if ci == 0 else (6, 0), pady=(0, 6))
            top = tk.Frame(c, bg=pal["CARD2"])
            top.pack(fill="x")
            tk.Frame(top, bg=col, width=3, height=18).pack(side="left")
            tk.Label(top, text=f"  {icon}  {title}", font=("Segoe UI", 9, "bold"),
                     bg=pal["CARD2"], fg=pal["WHITE"]).pack(side="left")
            tk.Label(c, text=ex, font=("Segoe UI", 8), bg=pal["CARD2"], fg=col).pack(anchor="w", pady=(4, 0))

    # ── SETTINGS & THEME SELECTOR ─────────────────────────────────────────────
    def _pg_settings(self):
        p = self.pages["settings"]
        pal = self.pal
        self._page_hdr(p, "SETTINGS & THEMES", "Configure AI Brain, Color Palette & System Preferences")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 60))

        # Color Theme Selector
        section_lbl(wrap, "🎨 COLOR THEME SELECTOR")
        theme_row = tk.Frame(wrap, bg=pal["BG_DEEP"])
        theme_row.pack(fill="x", pady=(0, 10))
        for t_key, t_info in THEMES.items():
            t_col = t_info["GLOW"]
            t_btn = tk.Button(theme_row, text=f"● {t_info['name']}",
                              font=("Segoe UI", 9, "bold"),
                              bg=t_info["CARD2"], fg=t_col,
                              activebackground=t_col, activeforeground="#ffffff",
                              relief="flat", bd=0, padx=14, pady=8, cursor="hand2",
                              command=lambda k=t_key: self._apply_theme(k))
            t_btn.pack(side="left", padx=(0, 8))

        section_lbl(wrap, "IDENTITY")
        self._field(wrap, "Agent Name", "agent_name_var", self.config.get("agent_name", "Aria"))
        self._field(wrap, "Your Name", "user_name_var", self.profile.get("name", "Friend"))

        # Gemini 2.5 Flash API Key Section
        section_lbl(wrap, "🧠 AI ENGINE 1 — GOOGLE GEMINI 2.5 FLASH (DEEP REASONING)")
        gemini_info = tk.Frame(wrap, bg=pal["CARD2"], padx=14, pady=10)
        gemini_info.pack(fill="x", pady=(0, 10))
        tk.Label(gemini_info, text="Best for deep web research, Chrome automation, and large context synthesis.",
                 font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"]).pack(anchor="w")
        ghost_btn(gemini_info, "🔗 Get Free Key at aistudio.google.com",
                  lambda: webbrowser.open("https://aistudio.google.com/app/apikey"),
                  col=pal["CYAN"]).pack(anchor="w", pady=(6, 0))

        key_row = tk.Frame(wrap, bg=pal["BG_DEEP"], pady=6)
        key_row.pack(fill="x")
        tk.Label(key_row, text="Gemini Key", font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["GREY"],
                 width=12, anchor="w").pack(side="left")
        self.gemini_key_var = tk.StringVar(value=self.config.get("gemini_api_key", os.environ.get("GEMINI_API_KEY", "")))
        gemini_entry = tk.Entry(key_row, textvariable=self.gemini_key_var, font=("Segoe UI", 9),
                                bg=pal["CARD2"], fg=pal["CYAN"], insertbackground=pal["CYAN"],
                                relief="flat", bd=0, width=38, show="•")
        gemini_entry.pack(side="left", ipady=6, padx=(0, 6))

        self._gemini_shown = False
        def _toggle_key_vis():
            self._gemini_shown = not self._gemini_shown
            gemini_entry.config(show="" if self._gemini_shown else "•")
        ghost_btn(key_row, "👁", _toggle_key_vis, col=pal["GREY"]).pack(side="left")

        test_row = tk.Frame(wrap, bg=pal["BG_DEEP"], pady=6)
        test_row.pack(fill="x")
        self.test_key_btn = ghost_btn(test_row, "⚡ Test Gemini Key", self._test_gemini_key, col=pal["CYAN"])
        self.test_key_btn.pack(side="left")
        self.test_key_result_lbl = tk.Label(test_row, text="", font=("Segoe UI", 8), bg=pal["BG_DEEP"], fg=pal["GREY"])
        self.test_key_result_lbl.pack(side="left", padx=(10, 0))

        # Groq Cloud API Key Section
        section_lbl(wrap, "⚡ AI ENGINE 2 — GROQ CLOUD (ULTRA-FAST VOICE & CHAT)")
        groq_info = tk.Frame(wrap, bg=pal["CARD2"], padx=14, pady=10)
        groq_info.pack(fill="x", pady=(0, 10))
        tk.Label(groq_info, text="Powers instant voice replies and real-time chat with 500+ tokens/sec inference.",
                 font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"]).pack(anchor="w")
        ghost_btn(groq_info, "🔗 Get Free Key at console.groq.com",
                  lambda: webbrowser.open("https://console.groq.com/keys"),
                  col=pal["AMBER"]).pack(anchor="w", pady=(6, 0))

        groq_key_row = tk.Frame(wrap, bg=pal["BG_DEEP"], pady=6)
        groq_key_row.pack(fill="x")
        tk.Label(groq_key_row, text="Groq Key", font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["GREY"],
                 width=12, anchor="w").pack(side="left")
        self.groq_key_var = tk.StringVar(value=self.config.get("groq_api_key", os.environ.get("GROQ_API_KEY", "")))
        groq_entry = tk.Entry(groq_key_row, textvariable=self.groq_key_var, font=("Segoe UI", 9),
                              bg=pal["CARD2"], fg=pal["AMBER"], insertbackground=pal["AMBER"],
                              relief="flat", bd=0, width=38, show="•")
        groq_entry.pack(side="left", ipady=6, padx=(0, 6))

        self._groq_shown = False
        def _toggle_groq_vis():
            self._groq_shown = not self._groq_shown
            groq_entry.config(show="" if self._groq_shown else "•")
        ghost_btn(groq_key_row, "👁", _toggle_groq_vis, col=pal["GREY"]).pack(side="left")

        groq_test_row = tk.Frame(wrap, bg=pal["BG_DEEP"], pady=6)
        groq_test_row.pack(fill="x")
        self.test_groq_btn = ghost_btn(groq_test_row, "⚡ Test Groq Key", self._test_groq_key, col=pal["AMBER"])
        self.test_groq_btn.pack(side="left")
        self.test_groq_result_lbl = tk.Label(groq_test_row, text="", font=("Segoe UI", 8), bg=pal["BG_DEEP"], fg=pal["GREY"])
        self.test_groq_result_lbl.pack(side="left", padx=(10, 0))

        # Personality Modes Selector (Feature 8)
        section_lbl(wrap, "🎭 PERSONALITY / MOOD MODE")
        p_row = tk.Frame(wrap, bg=pal["BG_DEEP"])
        p_row.pack(fill="x", pady=(0, 6))
        for p_key, p_lbl in [("casual", "Casual"), ("professional", "Professional"), ("witty", "Witty"), ("minimal", "Minimal")]:
            ghost_btn(p_row, f"● {p_lbl}", lambda k=p_key: self._set_personality(k), col=pal["CYAN"]).pack(side="left", padx=(0, 6))

        # Language Selector (Feature 2)
        section_lbl(wrap, "🌐 SPEECH RECOGNITION LANGUAGE")
        lang_row = tk.Frame(wrap, bg=pal["BG_DEEP"])
        lang_row.pack(fill="x", pady=(0, 6))
        for l_code, l_lbl in [("en", "English"), ("es", "Spanish"), ("fr", "French"), ("de", "German"), ("hi", "Hindi")]:
            ghost_btn(lang_row, f"● {l_lbl}", lambda c=l_code: self._set_whisper_lang(c), col=pal["VIOLET"]).pack(side="left", padx=(0, 6))

        # Session Logs Export (Feature 38)
        section_lbl(wrap, "📜 CONVERSATION LOGS EXPORT")
        exp_row = tk.Frame(wrap, bg=pal["CARD2"], padx=14, pady=10)
        exp_row.pack(fill="x", pady=(0, 10))
        tk.Label(exp_row, text="Export your complete conversation timeline & memory cards to a Markdown document.",
                 font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"]).pack(anchor="w")
        ghost_btn(exp_row, "📥 Export Session Logs to Markdown", self._export_logs_gui, col=pal["AMBER"]).pack(anchor="w", pady=(6, 0))

        # Context Toggles
        section_lbl(wrap, "🖥️ SYSTEM CONTEXT SENSORS")
        ctx_toggles = [
            ("ctx_active_window", "Active Focused Window", "Share currently active app title with Aria", pal["CYAN"]),
            ("ctx_clipboard", "Clipboard Contents", "Allow Aria to read copied text on command", pal["VIOLET"]),
            ("ctx_running_apps", "Running Applications", "Let Aria see running desktop processes", pal["GLOW2"]),
            ("ctx_system_stats", "CPU & RAM Load", "Include hardware resource percentages", pal["AMBER"]),
        ]
        self._ctx_vars = {}
        for key, label, desc, col in ctx_toggles:
            row = tk.Frame(wrap, bg=pal["CARD2"], padx=14, pady=8)
            row.pack(fill="x", pady=(0, 4))
            var = tk.BooleanVar(value=self.config.get(key, True))
            self._ctx_vars[key] = var
            cb = tk.Checkbutton(row, text=label, variable=var, font=("Segoe UI", 9, "bold"),
                                bg=pal["CARD2"], fg=col, selectcolor=blend(col, pal["CARD2"], 0.88),
                                relief="flat", cursor="hand2")
            cb.pack(side="left")
            tk.Label(row, text=f" — {desc}", font=("Segoe UI", 8), bg=pal["CARD2"], fg=pal["GREY"]).pack(side="left")

        # Save Button
        divider(wrap)
        self.save_btn_ref = tk.Button(
            wrap, text="SAVE ALL SETTINGS", font=("Segoe UI", 11, "bold"),
            bg=pal["GLOW"], fg=pal["WHITE"],
            activebackground=blend(pal["GLOW"], pal["CYAN"], 0.3),
            relief="flat", bd=0, pady=12, cursor="hand2",
            command=self._save)
        self.save_btn_ref.pack(fill="x", pady=(16, 0))

    def _apply_theme(self, theme_key):
        self.config["theme"] = theme_key
        save_config(self.config)
        self.pal = THEMES.get(theme_key, THEMES["cyber_purple"])
        self.root.pal = self.pal
        # Rebuild UI to apply colors smoothly
        for w in self.root.winfo_children():
            w.destroy()
        self._build()

    def _field(self, parent, label, attr, val):
        pal = self.pal
        f = tk.Frame(parent, bg=pal["BG_DEEP"], pady=4)
        f.pack(fill="x")
        tk.Label(f, text=label, font=("Segoe UI", 9), bg=pal["BG_DEEP"], fg=pal["GREY"], width=12, anchor="w").pack(side="left")
        var = tk.StringVar(value=val)
        e = tk.Entry(f, textvariable=var, font=("Segoe UI", 10), bg=pal["CARD2"], fg=pal["WHITE"],
                     insertbackground=pal["VIOLET"], relief="flat", bd=0, width=28)
        e.pack(side="left", ipady=6, padx=(0, 4))
        setattr(self, attr, var)

    def _test_gemini_key(self):
        key = self.gemini_key_var.get().strip() if hasattr(self, "gemini_key_var") \
              else self.config.get("gemini_api_key", os.environ.get("GEMINI_API_KEY", ""))
        if not key:
            self.test_key_result_lbl.config(text="No key entered", fg=self.pal["AMBER"])
            return

        self.test_key_btn.config(text="Testing...", state="disabled")
        self.test_key_result_lbl.config(text="Connecting to Gemini 2.5 Flash...", fg=self.pal["GREY"])

        def _run():
            t0 = time.time()
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=key)
                r = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents="Reply with: OK",
                    config=types.GenerateContentConfig(max_output_tokens=5)
                )
                lat = int((time.time() - t0) * 1000)
                self.root.after(0, lambda: self._on_key_test_result(True, f"Verified & Working ({lat}ms)"))
            except Exception as e:
                err = str(e)[:40]
                self.root.after(0, lambda: self._on_key_test_result(False, f"Failed: {err}"))

        threading.Thread(target=_run, daemon=True).start()

    def _test_groq_key(self):
        key = self.groq_key_var.get().strip() if hasattr(self, "groq_key_var") \
              else self.config.get("groq_api_key", os.environ.get("GROQ_API_KEY", ""))
        if not key:
            self.test_groq_result_lbl.config(text="No key entered", fg=self.pal["AMBER"])
            return

        self.test_groq_btn.config(text="Testing...", state="disabled")
        self.test_groq_result_lbl.config(text="Connecting to Groq Cloud...", fg=self.pal["GREY"])

        def _run():
            t0 = time.time()
            try:
                from groq import Groq
                client = Groq(api_key=key)
                # Auto-detect available chat model
                try:
                    available = [m.id for m in client.models.list().data]
                except Exception:
                    available = []
                preferred = [
                    "openai/gpt-oss-120b",
                    "llama-3.3-70b-versatile",
                    "groq/compound-mini",
                    "openai/gpt-oss-20b",
                    "qwen/qwen3.6-27b",
                    "llama-3.1-70b-versatile",
                ]
                model_to_use = next((m for m in preferred if m in available), available[0] if available else "openai/gpt-oss-120b")
                
                r = client.chat.completions.create(
                    model=model_to_use,
                    messages=[{"role": "user", "content": "Reply with: OK"}],
                    max_tokens=5
                )
                lat = int((time.time() - t0) * 1000)
                self.root.after(0, lambda: self._on_groq_test_result(True, f"Verified ({lat}ms)"))
            except Exception as e:
                err = str(e)[:40]
                self.root.after(0, lambda: self._on_groq_test_result(False, f"Failed: {err}"))

        threading.Thread(target=_run, daemon=True).start()

    def _on_key_test_result(self, success, msg):
        self.test_key_btn.config(text="⚡ Test Gemini Key", state="normal")
        self.test_key_result_lbl.config(text=msg, fg=self.pal["CYAN"] if success else self.pal["PINK"])

    def _on_groq_test_result(self, success, msg):
        self.test_groq_btn.config(text="⚡ Test Groq Key", state="normal")
        self.test_groq_result_lbl.config(text=msg, fg=self.pal["AMBER"] if success else self.pal["PINK"])

    def _save(self):
        pal = self.pal
        self.config["agent_name"] = self.agent_name_var.get()
        gemini_key = self.gemini_key_var.get().strip()
        groq_key = self.groq_key_var.get().strip()
        self.config["gemini_api_key"] = gemini_key
        self.config["groq_api_key"] = groq_key

        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        try:
            lines = []
            if os.path.exists(env_path):
                with open(env_path, encoding="utf-8") as f:
                    lines = f.readlines()
            # update keys
            new_lines = []
            g_written = False
            gr_written = False
            for l in lines:
                if l.startswith("GEMINI_API_KEY="):
                    new_lines.append(f"GEMINI_API_KEY={gemini_key}\n")
                    g_written = True
                elif l.startswith("GROQ_API_KEY="):
                    new_lines.append(f"GROQ_API_KEY={groq_key}\n")
                    gr_written = True
                else:
                    new_lines.append(l)
            if not g_written:
                new_lines.append(f"GEMINI_API_KEY={gemini_key}\n")
            if not gr_written:
                new_lines.append(f"GROQ_API_KEY={groq_key}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception:
            pass

        if hasattr(self, "_ctx_vars"):
            for k, v in self._ctx_vars.items():
                self.config[k] = v.get()

        save_config(self.config)
        self.profile["name"] = self.user_name_var.get()
        save_profile(self.profile)

        self.save_btn_ref.config(text="✓  SAVED!", bg=blend(pal["GLOW2"], pal["CARD2"], 0.5))
        self.root.after(2000, lambda: self.save_btn_ref.config(text="SAVE ALL SETTINGS", bg=pal["GLOW"]))

    # ── AUDIO & MIC PAGE ──────────────────────────────────────────────────────
    def _pg_mic(self):
        p = self.pages["mic"]
        pal = self.pal
        self._page_hdr(p, "MICROPHONE SETUP", "Input Devices & Signal Level")
        inner = tk.Frame(p, bg=pal["BG_DEEP"])
        inner.pack(fill="both", expand=True, padx=28, pady=(16, 0))

        section_lbl(inner, "ACTIVE MICROPHONE")
        act = tk.Frame(inner, bg=pal["CARD2"], padx=18, pady=16)
        act.pack(fill="x")
        self.mic_name_b = tk.Label(act, text="Detecting...", font=("Segoe UI", 11, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        self.mic_name_b.pack(anchor="w")

        section_lbl(inner, "AVAILABLE AUDIO SOURCES")
        self.mic_list_frame = tk.Frame(inner, bg=pal["BG_DEEP"])
        self.mic_list_frame.pack(fill="x")

    def _start_mic_monitor(self):
        def run():
            while self.mic_running:
                try:
                    self.root.after(0, self._refresh_mics)
                except Exception:
                    break
                time.sleep(4)
        threading.Thread(target=run, daemon=True).start()

    def _refresh_mics(self):
        devices = get_input_devices()
        for w in self.mic_list_frame.winfo_children():
            w.destroy()
        if not devices:
            return
        if self.active_mic is None:
            self.active_mic = devices[0]
        if self.active_mic:
            nm = self.active_mic["name"]
            self.mic_name_b.config(text=f"🎤 {nm}")

    # ── MEMORY & SEARCH & PROMPT PAGES ────────────────────────────────────────
    def _pg_memory(self):
        p = self.pages["memory"]
        self._page_hdr(p, "MEMORY VAULT", "ChromaDB Persistent Store")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=self.pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 0))
        tk.Label(wrap, text="Conversation turns and persistent notes are stored securely.",
                 font=("Segoe UI", 9), bg=self.pal["BG_DEEP"], fg=self.pal["GREY"]).pack(anchor="w")

    def _pg_search(self):
        p = self.pages["search"]
        self._page_hdr(p, "WEB SEARCH & RAG", "Live Web Knowledge Ingestion")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=self.pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 0))
        tk.Label(wrap, text="DuckDuckGo and Gemini 2.5 Flash web searching integrated.",
                 font=("Segoe UI", 9), bg=self.pal["BG_DEEP"], fg=self.pal["GREY"]).pack(anchor="w")

    def _pg_prompt(self):
        p = self.pages["prompt"]
        self._page_hdr(p, "SYSTEM PROMPT", "Custom AI Personality Directive")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=self.pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 0))
        tk.Label(wrap, text="Custom directives appended to Gemini 2.5 Flash.",
                 font=("Segoe UI", 9), bg=self.pal["BG_DEEP"], fg=self.pal["GREY"]).pack(anchor="w")

    def _pg_mcp(self):
        p = self.pages["mcp"]
        self._page_hdr(p, "MCP SERVER HUB", "Model Context Protocol Tool Registry")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=self.pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 0))
        tk.Label(wrap, text="Connected MCP Tools: System Context, Chrome Browser, PC Controls.",
                 font=("Segoe UI", 9), bg=self.pal["BG_DEEP"], fg=self.pal["GREY"]).pack(anchor="w")

    # ── ANALYTICS & STATS PAGE (Feature 34) ───────────────────────────────────
    def _pg_analytics(self):
        p = self.pages["analytics"]
        pal = self.pal
        self._page_hdr(p, "ANALYTICS & SYSTEM METRICS", "Real-Time Agent Intelligence & Knowledge Statistics")
        _, inner = scrollable(p)
        wrap = tk.Frame(inner, bg=pal["BG_DEEP"])
        wrap.pack(fill="both", expand=True, padx=28, pady=(16, 40))

        section_lbl(wrap, "CORE METRICS")
        g1 = tk.Frame(wrap, bg=pal["BG_DEEP"])
        g1.pack(fill="x", pady=(0, 10))
        g1.columnconfigure(0, weight=1)
        g1.columnconfigure(1, weight=1)
        g1.columnconfigure(2, weight=1)

        self.stat_mem_lbl = self._create_stat_box(g1, "EPISODIC MEMORIES", "0", pal["CYAN"], 0)
        self.stat_cards_lbl = self._create_stat_box(g1, "MEMORY CARDS", "0", pal["VIOLET"], 1)
        self.stat_kdocs_lbl = self._create_stat_box(g1, "INDEXED DOCUMENTS", "0", pal["GLOW2"], 2)

        section_lbl(wrap, "GOALS & SCHEDULING")
        g2 = tk.Frame(wrap, bg=pal["BG_DEEP"])
        g2.pack(fill="x", pady=(0, 10))
        g2.columnconfigure(0, weight=1)
        g2.columnconfigure(1, weight=1)
        g2.columnconfigure(2, weight=1)

        self.stat_goals_lbl = self._create_stat_box(g2, "ACTIVE GOALS", "0", pal["AMBER"], 0)
        self.stat_rems_lbl = self._create_stat_box(g2, "PENDING TIMERS", "0", pal["PINK"], 1)
        self.stat_prof_lbl = self._create_stat_box(g2, "USER PROFILES", "1", pal["CYAN"], 2)

        p.on_show = self._refresh_analytics_data

    def _create_stat_box(self, parent, title, val, accent, col_idx):
        pal = self.pal
        c = tk.Frame(parent, bg=pal["CARD2"], padx=18, pady=16)
        c.grid(row=0, column=col_idx, sticky="nsew", padx=(0, 6) if col_idx < 2 else (0, 0))
        tk.Label(c, text=title, font=("Segoe UI", 8, "bold"), bg=pal["CARD2"], fg=accent).pack(anchor="w")
        v_lbl = tk.Label(c, text=val, font=("Segoe UI", 20, "bold"), bg=pal["CARD2"], fg=pal["WHITE"])
        v_lbl.pack(anchor="w", pady=(6, 0))
        return v_lbl

    def _refresh_analytics_data(self):
        try:
            import aria_memory
            stats = aria_memory.get_analytics_summary()
            self.stat_mem_lbl.config(text=str(stats.get("memory_events", 0)))
            self.stat_cards_lbl.config(text=str(stats.get("memory_cards", 0)))
            self.stat_kdocs_lbl.config(text=str(stats.get("knowledge_docs", 0)))
            self.stat_goals_lbl.config(text=f"{stats.get('active_goals', 0)} Active ({stats.get('completed_goals', 0)} Done)")
            self.stat_rems_lbl.config(text=str(stats.get("pending_reminders", 0)))
            self.stat_prof_lbl.config(text=str(stats.get("profiles_count", 1)))
        except Exception:
            pass

    def _set_personality(self, mode):
        try:
            import aria_memory
            msg = aria_memory.set_personality_mode(mode)
            self._add_chat_bubble("assistant", msg)
            self._nav("chat")
        except Exception:
            pass

    def _set_whisper_lang(self, lang_code):
        try:
            self.config["whisper_language"] = lang_code
            save_config(self.config)
            self._add_chat_bubble("assistant", f"Whisper speech recognition language set to '{lang_code}'.")
            self._nav("chat")
        except Exception:
            pass

    def _export_logs_gui(self):
        try:
            import aria_memory
            msg = aria_memory.export_session_logs()
            self._add_chat_bubble("assistant", msg)
            self._nav("chat")
        except Exception:
            pass

    def _toggle_mini_mode(self):
        try:
            if getattr(self, "_is_mini", False):
                self._is_mini = False
                self.navbar.pack(side="left", fill="y")
                self.sep.pack(side="left", fill="y")
                self.content.pack(side="left", fill="both", expand=True)
                self.root.attributes("-topmost", False)
                self.root.state("zoomed")
                self.mini_mode_btn.config(text="🗗 MINI")
            else:
                self._is_mini = True
                self.navbar.pack_forget()
                self.sep.pack_forget()
                self.content.pack_forget()
                self.root.state("normal")
                self.root.geometry("420x620+100+100")
                self.root.attributes("-topmost", True)
                self.mini_mode_btn.config(text="🗖 FULL")
        except Exception:
            pass

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
        self.api_server_running = self._is_server_port_open(8765)

    def _is_server_port_open(self, port=8765):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            res = s.connect_ex(("127.0.0.1", port))
            s.close()
            return res == 0
        except Exception:
            return False

    def _toggle_mobile_server(self):
        running = self._is_server_port_open(8765)
        if running:
            # Turn OFF
            if self.api_server_proc:
                try:
                    self.api_server_proc.terminate()
                except Exception:
                    pass
                self.api_server_proc = None
            try:
                os.system("powershell -Command \"Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like '*aria_api.py*'} | Stop-Process -Force\"")
            except Exception:
                pass
            self._add_chat_bubble("assistant", "🔴 Mobile Companion Server turned OFF. Devices cannot connect until turned back on.")
        else:
            # Turn ON
            try:
                self.api_server_proc = subprocess.Popen(
                    [sys.executable, "c:/MyAgent/aria_api.py"],
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                self._add_chat_bubble("assistant", f"🟢 Mobile Companion Server turned ON!\nConnect from your phone on local Wi-Fi:\n{self.mobile_server_url}")
            except Exception as e:
                messagebox.showerror("Server Error", f"Failed to start mobile server: {e}")
        
        self.root.after(800, self._sync_mobile_server_state)

    def _sync_mobile_server_state(self):
        running = self._is_server_port_open(8765)
        self.api_server_running = running
        if hasattr(self, "toggle_server_btn"):
            if running:
                self.toggle_server_btn.config(
                    text="🔴 STOP SERVER",
                    bg=blend(self.pal["PINK"], self.pal["CARD2"], 0.3),
                    fg="#ffffff"
                )
                self.srv_status_lbl.config(text="● ONLINE", fg=self.pal["GREEN"])
                self.srv_url_lbl.config(text=self.mobile_server_url, fg=self.pal["WHITE"])
            else:
                self.toggle_server_btn.config(
                    text="🟢 START SERVER",
                    bg=self.pal["GLOW"],
                    fg="#ffffff"
                )
                self.srv_status_lbl.config(text="● OFFLINE", fg=self.pal["GREY"])
                self.srv_url_lbl.config(text="Server Stopped", fg=self.pal["GREY"])
        
        if hasattr(self, "home_srv_toggle_btn"):
            if running:
                self.home_srv_toggle_btn.config(
                    text="🔴 TURN OFF SERVER",
                    bg=blend(self.pal["PINK"], self.pal["CARD2"], 0.3),
                    fg="#ffffff"
                )
                self.home_srv_status_lbl.config(text="● SERVER ACTIVE", fg=self.pal["GREEN"])
                self.home_srv_url_lbl.config(text=self.mobile_server_url, fg=self.pal["CYAN"])
            else:
                self.home_srv_toggle_btn.config(
                    text="🟢 TURN ON SERVER",
                    bg=self.pal["GLOW"],
                    fg="#ffffff"
                )
                self.home_srv_status_lbl.config(text="● SERVER STOPPED", fg=self.pal["GREY"])
                self.home_srv_url_lbl.config(text="Click button below to launch", fg=self.pal["GREY"])
        
        # Periodic check every 4 seconds
        self.root.after(4000, self._sync_mobile_server_state)

    def _copy_mobile_server_url(self):
        try:
            import pyperclip
            pyperclip.copy(self.mobile_server_url)
            self.transcript_lbl.config(text=f"Copied {self.mobile_server_url} to clipboard!", fg=self.pal["CYAN"])
        except Exception:
            pass

    def _open_mobile_server_browser(self):
        import webbrowser
        webbrowser.open(self.mobile_server_url)


    # ── ANIMATION LOOP ────────────────────────────────────────────────────────
    def _animate(self):
        if not self.anim_running:
            return
        pal = self.pal
        c = self.sc
        w = c.winfo_width() or 260
        h = c.winfo_height() or 260
        cx, cy = w // 2, h // 2
        r = 58

        self.phase += 0.04
        c.delete("all")

        # Dynamic color based on status
        if self.is_speaking:
            glow, g1, g2 = pal["PINK"], pal["PINK"], pal["VIOLET"]
            st = "SPEAKING"
        elif self.is_listening:
            glow, g1, g2 = pal["CYAN"], pal["CYAN"], pal["GLOW2"]
            st = "LISTENING"
        elif self.is_running:
            glow, g1, g2 = pal["GLOW"], pal["GLOW"], pal["GLOW2"]
            st = "ONLINE"
        else:
            glow, g1, g2 = pal["GLOW"], blend(pal["GLOW"], pal["BG_MID"], 0.6), pal["CARD2"]
            st = "IDLE"

        # Background dust / stars
        for st_ in self.stars[:35]:
            sx = int(st_["x"] * w)
            sy = int(st_["y"] * h)
            c.create_oval(sx - 1, sy - 1, sx + 1, sy + 1, fill=blend(pal["WHITE"], pal["BG_MID"], 0.7), outline="")

        # Outer Atmospheric Glow Rings
        for i in range(5, 0, -1):
            gr = r + i * 10
            c.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                          fill="", outline=blend(glow, pal["BG_MID"], 0.85 + i * 0.02), width=1)

        # Orbiting ribbons
        for pt in self.ribbon_pts:
            pt["angle"] += pt["speed"]
            wobble = math.sin(self.phase * 2 + pt["phase"]) * 0.2
            eff_r = (r + 8) * pt["radius"] * (1 + wobble)
            px = cx + int(eff_r * math.cos(pt["angle"]))
            py = cy + int(eff_r * math.sin(pt["angle"]) * 0.35)
            c_col = pal.get(pt["col_key"], pal["GLOW"])
            c.create_oval(px - 2, py - 2, px + 2, py + 2, fill=c_col, outline="")

        # Core Sphere (lightweight 8-layer gradient)
        for i in range(8, 0, -1):
            t = i / 8.0
            sr = int(r * t)
            col = g2 if t > 0.6 else (blend(g1, g2, 0.5) if t > 0.3 else g1)
            c.create_oval(cx - sr, cy - sr, cx + sr, cy + sr, fill=col, outline="")

        # Specular light
        hlr = int(r * 0.22)
        hx = cx - int(r * 0.25)
        hy = cy - int(r * 0.25)
        c.create_oval(hx - hlr, hy - hlr, hx + hlr, hy + hlr, fill=blend(pal["WHITE"], g1, 0.5), outline="")

        # Latitude dynamic waves
        num_arcs = 4 if (self.is_speaking or self.is_listening) else 2
        for i in range(num_arcs):
            off = math.sin(self.phase * 1.5 + i * 0.8) * (r * 0.7)
            yp = cy + int(off)
            hw = int(math.sqrt(max(0, r**2 - off**2)) * 0.92)
            if hw > 4:
                c.create_arc(cx - hw, yp - 6, cx + hw, yp + 6, start=0, extent=180,
                             outline=blend(glow, pal["BG_MID"], 0.3), width=1, style="arc")

        # Pulse Rings
        if self.is_running or self.is_speaking or self.is_listening:
            if len(self.pulses) < 3 and int(self.phase * 15) % 8 == 0:
                self.pulses.append({"r": float(r + 6), "life": 1.0})
            for pu in self.pulses:
                pu["r"] += 2.2
                pu["life"] -= 0.04
                if pu["life"] > 0:
                    pr = int(pu["r"])
                    c.create_oval(cx - pr, cy - pr, cx + pr, cy + pr,
                                  outline=blend(glow, pal["BG_MID"], 1 - pu["life"] * 0.7), width=1)
            self.pulses = [p for p in self.pulses if p["life"] > 0]

        # Update state pill and nav dot
        self.state_lbl.config(text=st, fg=glow)
        self.s_lbl.config(text=st, fg=glow)
        self.s_dot.config(fg=glow)

        self.root.after(75, self._animate)

    # ── AGENT LIFECYCLE ───────────────────────────────────────────────────────
    def _toggle(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), AGENT_FILE)
            self.agent_proc = subprocess.Popen([sys.executable, path], creationflags=subprocess.CREATE_NO_WINDOW)
            self.is_running = self.is_listening = True
            self.start_btn.config(text="■   STOP ARIA", bg=self.pal["PINK"])
        except Exception as e:
            self.state_lbl.config(text=f"ERR: {e}", fg=self.pal["PINK"])

    def _stop(self):
        if self.agent_proc:
            try:
                self.agent_proc.terminate()
            except Exception:
                pass
            self.agent_proc = None
        self.is_running = self.is_speaking = self.is_listening = False
        self.start_btn.config(text="▶   LAUNCH ARIA", bg=self.pal["GLOW"])

    def _set_input_mode(self, mode):
        self.input_mode = mode
        pal = self.pal
        if mode == "chat":
            self.chat_mode_btn.config(bg=pal["GLOW"], fg=pal["WHITE"])
            self.voice_mode_btn.config(bg=pal["CARD2"], fg=pal["GREY"])
            self._nav("chat")
        else:
            self.voice_mode_btn.config(bg=pal["GLOW"], fg=pal["WHITE"])
            self.chat_mode_btn.config(bg=pal["CARD2"], fg=pal["GREY"])

    def _on_close(self):
        self.anim_running = False
        self.mic_running = False
        self._stop()
        try:
            from aria_chrome import close_chrome
            close_chrome()
        except Exception:
            pass
        self.root.destroy()

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = AriaApp(root)
    root.mainloop()
