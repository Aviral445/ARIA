"""
aria_extended.py — Additional Feature Extensions for Aria
Implements:
- Emotion-aware TTS rate & pitch tuning (Feature 3)
- Silence / Do Not Disturb (DND) mode (Feature 5)
- Window & App Switcher (Feature 15)
- Voice Mouse & Cursor commands (Feature 16)
- Response Caching for deterministic inputs (Feature 45)
- Sports Scores Lookup (Feature 22)
- Spotify Voice Controller (Feature 26)
- Birthday & Special Dates Tracker (Feature 50)
- Daily Morning Briefing Generator (Feature 12)
- Toast & System Notification Dispatcher (Feature 30)
- Smart Home / Webhook Trigger (Feature 40)
- YouTube Audio Mode (Feature 28)
"""

import os, sys, json, time, re, subprocess, urllib.request, urllib.parse, threading

# ── 1. SILENCE / DND MODE ────────────────────────────────────────────────────
_DND_MODE = False

def set_dnd_mode(enabled: bool) -> str:
    global _DND_MODE
    _DND_MODE = enabled
    return "Do Not Disturb mode enabled. Aria will now respond in text only." if enabled else "Do Not Disturb mode disabled. Voice responses restored."

def is_dnd_active() -> bool:
    return _DND_MODE


# ── 2. EMOTION-AWARE TTS RATE TUNING ─────────────────────────────────────────
def detect_emotion_rate_modifier(text: str) -> int:
    """
    Returns voice rate adjustment based on text sentiment:
    Excited/Urgent -> +3, Calm/Comforting -> -2, Normal -> 0
    """
    text_lower = text.lower()
    excited_words = ["congratulations", "amazing", "great job", "awesome", "crushed it", "celebrate", "urgent", "hurry", "warning"]
    calm_words = ["relax", "take it easy", "breathe", "sorry", "comfort", "rest", "peaceful", "slow down"]
    
    if any(w in text_lower for w in excited_words):
        return 3
    if any(w in text_lower for w in calm_words):
        return -2
    return 0


# ── 3. WINDOW & APP SWITCHER (pygetwindow & OS Launcher) ────────────────────
def open_or_focus_laptop_app(app_keyword: str) -> str:
    """Opens or brings an application/window to the front on the Host Laptop."""
    target = app_keyword.lower().strip()
    target = re.sub(r"\s+(?:on|in)\s+(?:my\s+)?(?:laptop|pc|computer)|\s+for\s+me|\s+please", "", target, flags=re.IGNORECASE).strip()
    
    # 1. Try to focus if already running
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():
            if target in w.title.lower() and w.title.strip():
                try:
                    w.restore()
                    w.activate()
                    return f"Switched to '{w.title}' on your laptop!"
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Known Windows protocol handlers and executables
    if "whatsapp" in target:
        subprocess.Popen(["powershell", "-c", "Start-Process whatsapp: -ErrorAction SilentlyContinue"])
        return "Opening WhatsApp on your laptop!"
    elif "spotify" in target:
        subprocess.Popen(["powershell", "-c", "Start-Process spotify: -ErrorAction SilentlyContinue"])
        return "Opening Spotify on your laptop!"
    elif "chrome" in target or "browser" in target or "google" in target:
        return open_chrome_with_profile()
    elif "antigravity" in target or "ide" in target or "code editor" in target:
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if "antigravity" in w.title.lower():
                    w.restore()
                    w.activate()
                    return "Focused Antigravity IDE on your laptop!"
        except Exception:
            pass
        subprocess.Popen(["powershell", "-c", "Start-Process 'Antigravity IDE' -ErrorAction SilentlyContinue"])
        return "Focused Antigravity IDE on your laptop!"
    elif "code" in target or "vs code" in target or "vscode" in target:
        subprocess.Popen(["powershell", "-c", "Start-Process code -ErrorAction SilentlyContinue"])
        return "Opening VS Code on your laptop!"
    elif "notepad" in target:
        subprocess.Popen(["powershell", "-c", "Start-Process notepad -ErrorAction SilentlyContinue"])
        return "Opening Notepad on your laptop!"
    elif "calc" in target or "calculator" in target:
        subprocess.Popen(["powershell", "-c", "Start-Process calc -ErrorAction SilentlyContinue"])
        return "Opening Calculator on your laptop!"
    elif "terminal" in target or "powershell" in target or "cmd" in target:
        subprocess.Popen(["powershell", "-c", "Start-Process powershell -ErrorAction SilentlyContinue"])
        return "Opening Terminal on your laptop!"
    else:
        subprocess.Popen(["powershell", "-c", f"Start-Process '{target}' -ErrorAction SilentlyContinue"])
        return f"Opening '{target}' on your laptop!"

def open_chrome_with_profile(url: str = "", profile_name: str = "Profile 7") -> str:
    """Launches Google Chrome directly on the user desktop using the aviirrll@gmail.com profile (Profile 7)."""
    try:
        if url:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            os.system(f'start chrome.exe --profile-directory="{profile_name}" "{url}"')
            return f"Opening {url} in Google Chrome (aviirrll@gmail.com) on your laptop!"
        else:
            os.system(f'start chrome.exe --profile-directory="{profile_name}" "https://www.google.com"')
            return "Opening Google Chrome with profile 'aviirrll@gmail.com' on your laptop!"
    except Exception:
        subprocess.Popen(["powershell", "-c", f"Start-Process chrome -ArgumentList '--profile-directory=\"{profile_name}\"', '{url or 'https://www.google.com'}' -ErrorAction SilentlyContinue"])
        return "Opening Google Chrome with profile 'aviirrll@gmail.com' on your laptop!"


def switch_google_search_section(section_name: str, query: str = "") -> str:
    """
    Switches the active Google search or opens a section:
    Supported sections: 'images', 'maps', 'news', 'videos', 'shopping', 'finance', 'all'
    """
    sec = section_name.lower().strip()
    
    # 1. If query not provided, try to extract from currently focused Chrome window
    if not query:
        try:
            import pygetwindow as gw
            for w in gw.getAllWindows():
                if "chrome" in w.title.lower():
                    title = w.title
                    if " - google search" in title.lower():
                        query = title.lower().split(" - google search")[0].strip()
                        break
                    elif " - google chrome" in title.lower():
                        clean_t = title.lower().split(" - google chrome")[0].strip()
                        if clean_t and clean_t not in ["new tab", "google"]:
                            query = clean_t
                            break
        except Exception:
            pass

    if not query:
        query = "latest"

    import urllib.parse
    encoded_q = urllib.parse.quote_plus(query)

    if any(k in sec for k in ["image", "photo", "pic", "visual"]):
        url = f"https://www.google.com/search?q={encoded_q}&tbm=isch"
        desc = f"Switched to Google Images for '{query}'"
    elif any(k in sec for k in ["map", "location", "route", "direction"]):
        url = f"https://www.google.com/maps/search/{encoded_q}"
        desc = f"Switched to Google Maps for '{query}'"
    elif any(k in sec for k in ["news", "headline", "article"]):
        url = f"https://www.google.com/search?q={encoded_q}&tbm=nws"
        desc = f"Switched to Google News for '{query}'"
    elif any(k in sec for k in ["video", "clip", "youtube"]):
        url = f"https://www.google.com/search?q={encoded_q}&tbm=vid"
        desc = f"Switched to Google Videos for '{query}'"
    elif any(k in sec for k in ["shop", "buy", "product", "price"]):
        url = f"https://www.google.com/search?q={encoded_q}&tbm=shop"
        desc = f"Switched to Google Shopping for '{query}'"
    elif any(k in sec for k in ["finance", "stock", "market"]):
        url = f"https://www.google.com/finance/quote/{encoded_q}"
        desc = f"Switched to Google Finance for '{query}'"
    else:
        url = f"https://www.google.com/search?q={encoded_q}"
        desc = f"Switched to Google All Search for '{query}'"

    open_chrome_with_profile(url)
    return f"{desc} in Google Chrome on your laptop!"


def switch_to_window(app_keyword: str) -> str:
    """Brings an open window to the front by title keyword."""
    return open_or_focus_laptop_app(app_keyword)



def parse_whatsapp_intent(text: str) -> tuple[str, str]:
    """Extracts (recipient, message) from natural language instructions."""
    t = text.strip()
    
    # 1. Double quotes or smart quotes around message
    m = re.search(r'[\"“]([^\"]+?)[\"”]', t)
    if m:
        msg = m.group(1).strip()
        prefix = t[:m.start()] + t[m.end():]
        m_rec = re.search(r'(?:send\s+(?:a\s+message\s+)?to|message|text|type\s+to)\s+([a-zA-Z0-9_\s]+?)(?:\s+on\s+whatsapp|\s+in\s+whatsapp|\s+saying|\s+with|\s+that|$)', prefix, re.IGNORECASE)
        if m_rec:
            return m_rec.group(1).strip(), msg
        clean_p = re.sub(r'(?:on|in)?\s*whatsapp|send|a message to|message|text|type to|saying|to', '', prefix, flags=re.IGNORECASE).strip()
        return clean_p or "Contact", msg

    # 2. Format: type <message> to <recipient> [on whatsapp]
    m = re.search(r'(?:in|on)?\s*whatsapp\s+(?:type|send|write|text)\s+(.+?)\s+to\s+(.+)$', t, re.IGNORECASE)
    if m:
        val1, val2 = m.group(1).strip(), m.group(2).strip()
        if "a message to" in val1.lower():
            val1 = re.sub(r'a message to\s*', '', val1, flags=re.IGNORECASE).strip()
            return val1, val2
        return val2.replace("on whatsapp","").replace("in whatsapp","").strip(), val1

    # 3. Format: tell <recipient> that <message>
    m = re.search(r'(?:in|on)?\s*whatsapp\s+(?:tell|message)\s+(.+?)\s+(?:that|to)\s+(.+)$', t, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()
        
    return "", ""


def send_whatsapp_message(recipient: str, message: str) -> str:
    """Automates opening WhatsApp, focusing contact search, typing, and sending the message."""
    def _run():
        try:
            import time, pyautogui, pyperclip
            pyautogui.FAILSAFE = False
            open_or_focus_laptop_app("whatsapp")
            time.sleep(2.0)
            
            # Focus search in WhatsApp
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.8)
            
            # Paste contact name and open chat
            pyperclip.copy(recipient)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1.2)
            pyautogui.press('enter')
            time.sleep(1.0)
            
            # Paste message and send
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.6)
            pyautogui.press('enter')
        except Exception as e:
            print(f"[WhatsApp Automation Error] {e}")
            
    threading.Thread(target=_run, daemon=True).start()
    return f"Sending '{message}' to {recipient} on WhatsApp!"




def execute_power_command(command: str, is_admin: bool = True) -> tuple[bool, str]:
    """Handles remote or voice power commands: shutdown, restart, sleep, lock, cancel shutdown."""
    cmd_l = command.lower().strip()
    
    # Cancel shutdown
    if any(k in cmd_l for k in ["cancel shutdown", "abort shutdown", "stop shutdown"]):
        os.system("shutdown /a")
        return True, "Shutdown cancelled on your laptop."

    # Power off / Shutdown
    if any(k in cmd_l for k in ["shutdown", "shut down", "turn off laptop", "turn off pc", "turn off my laptop", "power off"]):
        if not is_admin:
            return True, "Access Denied: Only Master Admin (L) can remotely power down the host laptop."
        os.system('shutdown /s /t 20 /c "Aria Remote Shutdown Request"')
        return True, "Initiating shutdown on your laptop in 20 seconds. You can type 'cancel shutdown' from your phone to abort."

    # Restart
    if any(k in cmd_l for k in ["restart laptop", "restart pc", "reboot laptop", "reboot pc", "restart computer", "restart"]):
        if not is_admin:
            return True, "Access Denied: Only Master Admin (L) can remotely reboot the host laptop."
        os.system("shutdown /r /t 15")
        return True, "Restarting your laptop in 15 seconds. You can type 'cancel shutdown' to abort."

    # Lock
    if any(k in cmd_l for k in ["lock laptop", "lock pc", "lock computer", "lock screen", "lock my laptop", "lock"]):
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True, "Locked your laptop screen."

    # Sleep
    if any(k in cmd_l for k in ["sleep laptop", "sleep pc", "put laptop to sleep", "sleep computer"]):
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return True, "Putting your laptop to sleep."

    return False, ""

def minimize_all_windows() -> str:
    """Minimizes all windows to show desktop."""
    try:
        subprocess.call(["powershell", "-c", "$o=New-Object -ComObject Shell.Application;$o.MinimizeAll()"])
        return "Minimized all windows."
    except Exception as e:
        return f"Minimize error: {e}"



# ── 4. VOICE MOUSE CONTROL (pyautogui) ────────────────────────────────────────
def control_mouse(command: str) -> str:
    """Controls mouse cursor: move left/right/up/down, click, scroll."""
    try:
        import pyautogui
        cmd = command.lower()
        if "click" in cmd:
            pyautogui.click()
            return "Clicked mouse."
        if "double click" in cmd:
            pyautogui.doubleClick()
            return "Double clicked."
        if "right click" in cmd:
            pyautogui.rightClick()
            return "Right clicked."
        if "scroll down" in cmd:
            pyautogui.scroll(-400)
            return "Scrolled down."
        if "scroll up" in cmd:
            pyautogui.scroll(400)
            return "Scrolled up."
        if "move right" in cmd:
            pyautogui.moveRel(200, 0, duration=0.2)
            return "Moved mouse right."
        if "move left" in cmd:
            pyautogui.moveRel(-200, 0, duration=0.2)
            return "Moved mouse left."
        if "move up" in cmd:
            pyautogui.moveRel(0, -200, duration=0.2)
            return "Moved mouse up."
        if "move down" in cmd:
            pyautogui.moveRel(0, 200, duration=0.2)
            return "Moved mouse down."
        return "Mouse command not recognized."
    except Exception as e:
        return f"Mouse control error: {e}"


# ── 5. RESPONSE CACHING ───────────────────────────────────────────────────────
_RESPONSE_CACHE = {}

def get_cached_response(prompt: str, ttl_seconds: int = 60) -> str:
    key = prompt.lower().strip()
    if key in _RESPONSE_CACHE:
        val, timestamp = _RESPONSE_CACHE[key]
        if time.time() - timestamp < ttl_seconds:
            return val
    return ""

def set_cached_response(prompt: str, response: str):
    key = prompt.lower().strip()
    _RESPONSE_CACHE[key] = (response, time.time())


# ── 6. SPORTS & CRICKET SCORES ───────────────────────────────────────────────
def get_sports_score(query: str = "cricket") -> str:
    """Pulls live sports / match updates."""
    try:
        import aria_tools
        return aria_tools.get_latest_news(f"{query} match score")
    except Exception as e:
        return f"Sports lookup error: {e}"


# ── 7. SPOTIFY CONTROLLER ─────────────────────────────────────────────────────
def control_spotify(action: str = "play") -> str:
    """Opens or controls Spotify desktop app."""
    try:
        act = action.lower()
        if "play" in act or "open" in act:
            os.system("start spotify:")
            return "Launching Spotify."
        # Use media key commands
        if "pause" in act or "stop" in act or "resume" in act:
            subprocess.call(["powershell", "-c", "$o=New-Object -ComObject WScript.Shell;$o.SendKeys([char]179)"])
            return "Toggled Spotify playback."
        if "next" in act or "skip" in act:
            subprocess.call(["powershell", "-c", "$o=New-Object -ComObject WScript.Shell;$o.SendKeys([char]176)"])
            return "Skipped track."
        if "previous" in act or "back" in act:
            subprocess.call(["powershell", "-c", "$o=New-Object -ComObject WScript.Shell;$o.SendKeys([char]177)"])
            return "Previous track."
        return "Spotify command sent."
    except Exception as e:
        return f"Spotify error: {e}"


# ── 8. BIRTHDAY & SPECIAL DATES TRACKER ───────────────────────────────────────
def check_special_dates(profile: dict) -> str:
    today_str = time.strftime("%B %d").lower()
    dates = profile.get("special_dates", {})
    greetings = []
    for event_name, date_str in dates.items():
        if date_str.lower() in today_str:
            greetings.append(f"🎉 Today is {event_name}! Wishing you an incredible celebration!")
    return " ".join(greetings)


# ── 9. DAILY MORNING BRIEFING ────────────────────────────────────────────────
def get_morning_briefing(profile: dict) -> str:
    """Generates a complete personalized daily briefing."""
    user_name = profile.get("name", "Friend")
    now_str = time.strftime("%A, %B %d, %Y")
    
    import aria_tools, aria_scheduler
    quote = aria_tools.get_daily_opener()
    reminders = aria_scheduler.get_scheduler().list_active_reminders()
    special = check_special_dates(profile)
    
    briefing = [
        f"Good morning, {user_name}! Today is {now_str}.",
        special if special else "",
        f"Daily Thought: {quote}",
        f"{reminders}",
        "Have a productive and wonderful day ahead!"
    ]
    return "\n\n".join([b for b in briefing if b])


# ── 10. TOAST NOTIFICATION DISPATCHER (Feature 30) ───────────────────────────
def show_toast_notification(title: str, message: str):
    """Dispatches a native Windows toast notification popup."""
    def _dispatch():
        try:
            clean_title = title.replace("'", "").replace('"', "")
            clean_msg = message.replace("'", "").replace('"', "")
            ps_script = (
                f"[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null; "
                f"$notify = New-Object System.Windows.Forms.NotifyIcon; "
                f"$notify.Icon = [System.Drawing.SystemIcons]::Information; "
                f"$notify.Visible = $true; "
                f"$notify.ShowBalloonTip(5000, '{clean_title}', '{clean_msg}', [System.Windows.Forms.ToolTipIcon]::Info);"
            )
            subprocess.call(["powershell", "-c", ps_script])
        except Exception:
            pass
    threading.Thread(target=_dispatch, daemon=True).start()
    return f"Notification shown: {title}"


# ── 11. SMART HOME / WEBHOOK TRIGGER (Feature 40) ─────────────────────────────
SMART_HOME_CONFIG = "smart_home.json"

def trigger_smart_device(device_or_action: str) -> str:
    """Triggers configured Home Assistant or Webhook endpoints for smart switches/lights."""
    if not os.path.exists(SMART_HOME_CONFIG):
        default_cfg = {
            "bedroom light": "http://192.168.1.100/api/switch/bedroom_light/toggle",
            "study lamp": "http://192.168.1.100/api/switch/study_lamp/toggle"
        }
        with open(SMART_HOME_CONFIG, "w", encoding="utf-8") as f:
            json.dump(default_cfg, f, indent=2)
            
    try:
        with open(SMART_HOME_CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
            
        dev_clean = device_or_action.lower().strip()
        for dev_name, url in cfg.items():
            if dev_name in dev_clean:
                req = urllib.request.Request(url, method="POST" if not url.startswith("http") else "GET")
                try:
                    urllib.request.urlopen(req, timeout=3)
                    return f"Sent command to smart device '{dev_name}' successfully."
                except Exception as e:
                    return f"Triggered '{dev_name}', but received network response: {e}"
                    
        return f"Device '{device_or_action}' not configured in smart_home.json."
    except Exception as e:
        return f"Smart home error: {e}"


# ── 12. YOUTUBE AUDIO STREAM HELPER (Feature 28) ──────────────────────────────
def play_youtube_audio(query: str) -> str:
    """Searches YouTube and opens lightweight audio playback."""
    clean_q = query.replace("youtube", "").replace("play", "").replace("audio", "").strip()
    if clean_q:
        url = f"https://music.youtube.com/search?q={urllib.parse.quote_plus(clean_q)}"
        import webbrowser
        webbrowser.open(url)
        return f"Playing YouTube Music stream for '{clean_q}'!"
    return "Please specify a song or artist to play."


# ── 13. NVIDIA NIM CODER AUTOMATION (Qwen 2.5 Coder & DeepSeek Coder) ────────
def synthesize_and_execute_script(task_description: str, language: str = "powershell", execute: bool = False) -> str:
    """
    Synthesizes a system automation script using NVIDIA NIM Coder models
    (Qwen 2.5 Coder 32B) under the 40 RPM rate limit, with optional safe execution.
    """
    try:
        from core.aria_nvidia import get_nvidia_engine
        nv = get_nvidia_engine()
        if not nv.is_configured():
            return "NVIDIA_API_KEY is required for specialized code synthesis."
        
        script = nv.generate_code(instruction=task_description, language=language)
        
        if not execute:
            return f"Generated {language.upper()} script using NVIDIA Coder:\n\n```\n{script}\n```"
        
        # Verify safety guardrail before execution
        safe, reason = nv.check_safety(script)
        if not safe:
            return f"Script execution blocked by NVIDIA Safety Guard: {reason}\n\n```\n{script}\n```"
            
        if language.lower() == "powershell":
            from tools.aria_vision_executor import execute_system_powershell
            success, out = execute_system_powershell(script, timeout_sec=20)
            status = "Executed successfully" if success else "Execution failed"
            return f"{status} (NVIDIA NIM Qwen 2.5 Coder):\n{out}"
        else:
            return f"Generated script (execution not supported for {language}):\n\n```\n{script}\n```"
    except Exception as e:
        return f"Code synthesis error: {e}"

