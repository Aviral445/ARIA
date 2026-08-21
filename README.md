# 🤖 Aria — Your Personal AI Agent for Windows

A voice-powered AI assistant that talks to you, remembers you, and controls your PC.
Built with Python + Llama 3.2 (via Ollama) — 100% free, runs locally.

---

## ⚡ Quick Setup (do this once)

### Step 1 — Install Ollama
Go to https://ollama.com and download the Windows installer.
Run it. That's it.

### Step 2 — Download Llama 3.2
Open a terminal (CMD or PowerShell) and run:
```
ollama pull llama3.2
```
Wait for it to download (~2GB). You only do this once.

### Step 3 — Install Python dependencies
In your project folder, run:
```bash
pip install -r requirements.txt
```

> ⚠️ If PyAudio fails to install, download the correct .whl from:
> https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
> Then run: pip install PyAudio‑0.2.11‑cpXX‑cpXX‑win_amd64.whl

### Step 4 — Set up Environment Variables
Copy `.env.example` to `.env` and add your API keys (optional for local Ollama, recommended for Gemini / Groq):
```bash
cp .env.example .env
```

### Step 5 — Personalise (optional)
Edit `data/profile.json` and change "name" to your actual name:
```json
{
  "name": "Alex",
  "preferences": [],
  "notes": []
}
```

### Step 6 — Run your agent!
Make sure Ollama is running (it starts automatically after install), then:
```bash
python agent.py
```

---

## 🎤 Voice Commands

| Say this...              | What happens                        |
|--------------------------|-------------------------------------|
| "Open Chrome"            | Launches Google Chrome              |
| "Open Notepad"           | Launches Notepad                    |
| "Open Calculator"        | Launches Calculator                 |
| "Search for cat videos"  | Googles "cat videos"                |
| "YouTube lo-fi music"    | Opens YouTube search                |
| "What time is it?"       | Tells you the current time          |
| "What's today's date?"   | Tells you today's date              |
| "Lock my computer"       | Locks your Windows screen           |
| "Shutdown my computer"   | Shuts down (with 10s cancel window) |
| "Goodbye" / "Exit"       | Saves memory and closes agent       |
| Anything else...         | Talks to you via Llama AI 🧠        |

---

## 🧠 Memory

Aria remembers things you tell her:
- Say "My name is Alex" → she'll call you Alex from now on
- Say "I love jazz music" → saved to your profile
- Say "I prefer dark mode" → saved to preferences

All memory is stored in:
- `profile.json` — facts about you (permanent)
- `memory.json`  — conversation history (rolling last 20 exchanges)

---

## 🛠️ Customisation Tips

**Change the agent's name:**
Edit `AGENT_NAME = "Aria"` at the top of agent.py

**Add more apps to open:**
Add entries to the `APP_MAP` dictionary in agent.py:
```python
APP_MAP = {
    "discord": r"C:\Users\%USERNAME%\AppData\Local\Discord\app-X.X.X\Discord.exe",
    ...
}
```

**Change the AI model:**
```python
MODEL = "mistral"      # faster, lighter
MODEL = "llama3.2"     # best conversation (default)
MODEL = "phi3"         # smallest, great for weak PCs
```

**Make replies longer:**
Change `max_tokens=200` to a higher number in agent.py

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| "PyAudio not found" | Install from .whl file (see Step 3) |
| "Connection refused" | Make sure Ollama is running |
| "Model not found" | Run `ollama pull llama3.2` again |
| Mic not detected | Check Windows mic permissions |
| Voice sounds robotic | Change voice in pyttsx3 settings |

---

---

## 📁 Modular Directory Structure

```
c:\MyAgent\
├── core/                  # Core Brain, ADK, Memory, Scheduler, Learning & Context
├── tools/                 # OS Control, Chrome Browser, Vision OCR, File Organizer
├── gui/                   # Desktop Graphical Dashboard & Chat UI
├── server/                # FastAPI Mobile Companion Server & Auth
├── mcp/                   # Model Context Protocol Server & Client
├── data/                  # Persistent Databases, Memory Timeline, Profiles, Knowledge
├── config/                # App Settings, Auth Stores & Credentials
├── models/                # Local Models & TTS Voices
├── docs/                  # Project Roadmaps, Errors, and Feature Docs
├── tests/                 # Unit & Regression Test Suites
├── .env                   # API Keys (Gemini, Groq)
├── requirements.txt       # Dependencies
├── README.md              # Project Documentation
├── agent.py               # Voice & CLI Launcher (`python agent.py`)
├── aria_gui.py            # Desktop Graphical Launcher (`python aria_gui.py`)
└── aria_api.py            # Mobile & Web Server Launcher (`python aria_api.py`)
```

---

## 🚀 Running Aria

- **Desktop GUI Dashboard:** `python aria_gui.py`
- **Voice / CLI Agent:** `python agent.py`
- **Mobile Companion Server:** `python aria_api.py`
- **Run Test Suite:** `python -m unittest discover -s tests`

