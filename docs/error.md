# 🛠️ Aria — Error & Bug Log (`error.md`)

Use this document to track errors, stack traces, and command parsing bugs to resolve.

---

## 🐛 Active Errors Log

### Bug 3: Limited PC Interaction & App Automation
- **Component / File:** `agent.py` (`APP_MAP`, `_tool_open_app`, `_tool_whatsapp`, `_tool_typing`)
- **Commands tested:**
  1. `"in whatsapp type hi to Alex"`
     - **Observed:** Aria previously only responded *"Opening WhatsApp!"*.
     - **Resolution:** Implemented `_tool_whatsapp` automated hands-free messaging pipeline (opens WhatsApp, focuses chat search with `Ctrl+F`, searches for contact, types and sends the message).
  2. `"open bluestacks"` / `"open lively wallpaper"` / `"open roblox"`
     - **Observed:** Failed to launch unlisted applications.
     - **Resolution:** Built **Universal Windows App Launcher** scanning Start Menu `.lnk` shortcuts, Desktop shortcuts, and AppData directories (`0ms` response) with PowerShell fallback.
  3. `"type <text>"`
     - **Resolution:** Added `_tool_typing` background typing automation via `pyautogui` & `pyperclip`.
### Bug 4: Document & PDF Search Misrouted to App Launcher
- **Component / File:** `agent.py` (`_tool_file_search`), `aria_learning.py`
- **Command tested:** `"open a pdf named hands on machine learning. it is somewhere on my laptop"`
- **What happened:** Aria previously treated the entire phrase as an application name (`"Launching a pdf named hands on machine learning..."`).
- **Resolution:** 
  1. Built **Intelligent File & PDF Search Tool** (`_tool_file_search`) that extracts core keywords and recursively scans `Desktop`, `Downloads`, `Documents`, and `OneDrive` for exact & ranked fuzzy matches and opens the file via `os.startfile()`.
  2. Implemented **Continuous Learning & Self-Correction Engine** ([`aria_learning.py`](file:///c:/MyAgent/aria_learning.py)) with `learned_corrections.json` to learn from mistakes and inject custom aliases (e.g., *"whenever I say work time do open vs code and spotify"*).
- **Verified Output:** `Found and opened 'Hands on Machine Learning with Scikit Learn and TensorFlow.pdf' from Desktop!`
- **Status:** [x] Resolved

---

## ✅ Resolved Errors Log

### Bug 1: Unable to open WhatsApp application
- **Component / File:** `agent.py` (`APP_MAP` / `_tool_open_app`)
- **What happened:** When asked to open WhatsApp, Aria wasn't able to interact with the PC to launch the WhatsApp desktop app or WhatsApp Web.
- **Resolution:** Added desktop protocol launcher (`whatsapp:`) with fallback to WhatsApp Web (`https://web.whatsapp.com`).
- **Status:** [x] Resolved

---

### Bug 2: Search Query Regex Extraction Flaw
- **Component / File:** `agent.py` (`_tool_web_search`)
- **Command given:** `"open google and in it search for ironman"`
- **What happened:** Opened Google, but the search query entered was `"open and in it ironman"` instead of `"ironman"`.
- **Resolution:** Upgraded query cleaner with multi-pattern prefix trimming (e.g. `^open google and in it search for`, `^search google for`, etc.) and `urllib.parse.quote_plus` URL encoding.
- **Status:** [x] Resolved
