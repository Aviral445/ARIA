"""
aria_system_context.py — System Context Engine for Aria
Gives Aria deep real-time awareness of what's happening on the user's PC:
  • Active focused window title
  • All open background application windows & software (e.g. Antigravity IDE, WhatsApp, Chrome, VS Code)
  • Clipboard contents
  • Running applications & processes
  • CPU / RAM usage & hardware telemetry
  • Current time & date
"""

import datetime, os, sys

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pygetwindow as gw
    HAS_GW = True
except ImportError:
    HAS_GW = False

try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False

KNOWN_APP_MAP = {
    "antigravity ide.exe": "Antigravity IDE",
    "whatsapp.root.exe": "WhatsApp",
    "whatsapp.exe": "WhatsApp",
    "chrome.exe": "Google Chrome",
    "code.exe": "VS Code",
    "spotify.exe": "Spotify",
    "brave.exe": "Brave Browser",
    "msedge.exe": "Microsoft Edge",
    "notepad.exe": "Notepad",
    "discord.exe": "Discord",
    "telegram.exe": "Telegram",
    "slack.exe": "Slack",
    "cursor.exe": "Cursor IDE",
    "pycharm64.exe": "PyCharm",
    "explorer.exe": "File Explorer",
    "powershell.exe": "PowerShell Terminal",
    "cmd.exe": "Command Prompt",
}

IGNORED_PROCS = {
    "svchost.exe", "conhost.exe", "sihost.exe", "ctfmon.exe", "taskhostw.exe",
    "dllhost.exe", "runtimebroker.exe", "fontdrvhost.exe", "wudfhost.exe",
    "services.exe", "lsass.exe", "wininit.exe", "csrss.exe", "smss.exe",
    "searchindexer.exe", "searchhost.exe", "startmenuexperiencehost.exe",
    "textinputhost.exe", "shellexperiencehost.exe", "systemsettings.exe",
    "securityhealthservice.exe", "msmpeng.exe", "mpdefendercoreService.exe",
    "aggregationhost.exe", "wslservice.exe", "presentmonservice.exe"
}

def get_active_window() -> str:
    """Return the title of the currently focused foreground window."""
    if HAS_GW:
        try:
            win = gw.getActiveWindow()
            if win and win.title and win.title.strip():
                t = win.title.strip()
                if t.lower() not in ["program manager", "windows input experience"]:
                    return t
        except Exception:
            pass
    return "Desktop / no window focused"

def get_open_windows_and_apps() -> list[dict]:
    """
    Scans and returns all open user-facing application windows and background software
    (such as Antigravity IDE, WhatsApp, VS Code, Chrome, etc.) in <15ms.
    """
    apps_found = {}

    # Fast in-memory process scanning via psutil
    if HAS_PSUTIL:
        try:
            for p in psutil.process_iter(["name", "pid"]):
                try:
                    n = p.info.get("name")
                    if n:
                        nl = n.lower()
                        if nl in KNOWN_APP_MAP:
                            friendly_name = KNOWN_APP_MAP[nl]
                            if friendly_name not in apps_found:
                                apps_found[friendly_name] = {
                                    "app": friendly_name,
                                    "title": friendly_name,
                                    "process": n,
                                    "state": "Running in Background"
                                }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass

    # Extract open visible GUI window titles via pygetwindow if available
    if HAS_GW:
        try:
            for w in gw.getAllWindows():
                t = w.title.strip()
                if t and t.lower() not in ["program manager", "windows input experience", "settings", ""]:
                    # Match or add
                    app_label = t.split(" - ")[-1] if " - " in t else t
                    if app_label not in apps_found:
                        apps_found[app_label] = {
                            "app": app_label,
                            "title": t,
                            "process": "gui_app",
                            "state": "Open Window"
                        }
                    else:
                        apps_found[app_label]["title"] = t
        except Exception:
            pass

    return list(apps_found.values())

def get_clipboard() -> str:
    """Return current clipboard text."""
    if not HAS_CLIPBOARD:
        return ""
    try:
        text = pyperclip.paste()
        if not text or not isinstance(text, str):
            return ""
        text = text.strip()
        limit = 400
        return (text[:limit] + "...") if len(text) > limit else text
    except Exception:
        return ""

def get_system_stats() -> dict:
    """Return CPU, RAM, and hardware telemetry."""
    if not HAS_PSUTIL:
        return {}
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_used_gb": round(psutil.virtual_memory().used / 1e9, 1),
            "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 1),
        }
    except Exception:
        return {}

def get_system_context() -> dict:
    """Build and return a full system context snapshot."""
    active_win = get_active_window()
    open_wins = get_open_windows_and_apps()
    stats = get_system_stats()
    cb = get_clipboard()

    return {
        "timestamp": datetime.datetime.now().strftime("%A %B %d %Y, %I:%M %p"),
        "active_window": active_win,
        "open_windows": open_wins,
        "open_window_titles": [w["title"] for w in open_wins],
        "running_software": [w["app"] for w in open_wins],
        "clipboard": cb,
        "cpu_percent": stats.get("cpu_percent", 0),
        "ram_percent": stats.get("ram_percent", 0),
        "ram_used_gb": stats.get("ram_used_gb", 0),
        "ram_total_gb": stats.get("ram_total_gb", 0),
    }

def format_context_for_prompt(ctx: dict) -> str:
    """
    Format the system context dict into a comprehensive, human-readable block
    to inject into Aria's system prompt so she always knows all running apps and open tabs/windows.
    """
    if not ctx:
        return ""

    lines = ["── LIVE SYSTEM CONTEXT ON HOST LAPTOP ──"]
    lines.append(f"Time: {ctx.get('timestamp', '')}")
    lines.append(f"Focused Foreground Window: {ctx.get('active_window', 'Desktop')}")

    open_wins = ctx.get("open_windows", [])
    if open_wins:
        lines.append("Active Background Applications & Open Windows on Laptop:")
        for w in open_wins:
            lines.append(f"  • {w['app']} (Title: '{w['title']}', State: {w.get('state', 'Running')})")
    else:
        lines.append("Active Background Applications: None detected")

    if ctx.get("clipboard"):
        lines.append(f"Current Clipboard: {ctx['clipboard']}")

    lines.append(f"Hardware Load: CPU: {ctx.get('cpu_percent', 0)}% | RAM: {ctx.get('ram_percent', 0)}%")
    lines.append("────────────────────────────────────────")
    return "\n".join(lines)

CONTEXT_CONFIG = {}
def update_config(key, val):
    CONTEXT_CONFIG[key] = val

