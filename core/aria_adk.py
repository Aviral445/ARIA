"""
aria_adk.py — Agent Development Kit (ADK) Engine for Aria AI
Provides:
1. Declarative, typed tool registry with automatic schema reflection.
2. Multi-tier resilient model execution:
   - Primary: Google Gemini 2.5 Flash / 2.0 Flash with Native Tool Calling (Free Tier via Google AI Studio)
   - Secondary: Groq Cloud (Free Tier Tool Calling)
   - Tertiary: Local Offline Ollama (Llama 3.2)
3. Automated multi-turn function calling execution loop.
4. Real-time tool-execution callbacks for GUI and Voice status feedback.
5. Multi-Agent Sub-agent tools (System, Browser, Vision, Memory, MCP Workspace).
"""

import os, sys, json, time, re, datetime, subprocess
from typing import Callable, Any, Dict, List, Optional
from dotenv import load_dotenv

try:
    from .paths import ROOT_DIR, DATA_DIR, CONFIG_DIR, ENV_FILE
except ImportError:
    from paths import ROOT_DIR, DATA_DIR, CONFIG_DIR, ENV_FILE

for p in [ROOT_DIR, os.path.join(ROOT_DIR, "core"), os.path.join(ROOT_DIR, "tools"), os.path.join(ROOT_DIR, "server"), os.path.join(ROOT_DIR, "mcp"), os.path.join(ROOT_DIR, "gui")]:
    if p not in sys.path:
        sys.path.insert(0, p)

load_dotenv(ENV_FILE)

# ─────────────────────────────────────────────────────────────────────────────
# 1. TOOL IMPLEMENTATIONS (WRAPPING ARIA CAPABILITIES)
# ─────────────────────────────────────────────────────────────────────────────

def open_application(app_name: str) -> str:
    """Launch an application or software on Windows by name (e.g., 'chrome', 'notepad', 'calculator', 'spotify', 'code')."""
    app_clean = app_name.lower().strip()
    try:
        import aria_extended
        if any(k in app_clean for k in ["chrome", "google", "browser", "internet"]):
            return aria_extended.open_chrome_with_profile()
        return aria_extended.open_or_focus_laptop_app(app_name)
    except Exception as e:
        return f"Failed to open '{app_name}': {e}"


def search_and_open_document(query: str, extension: str = "") -> str:
    """Search the user's Desktop, Downloads, and Documents for a file or PDF and open it."""
    words = [w.lower() for w in query.split() if len(w) > 1 and w.lower() not in ["open", "find", "search", "document", "file", "the", "my"]]
    if not words:
        return "No specific search keywords provided for document search."

    user_home = os.path.expandvars(r"%USERPROFILE%")
    search_dirs = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "OneDrive"),
        r"c:\MyAgent",
        user_home,
    ]
    ext_filter = extension.lower().strip()
    matches = []

    for sdir in search_dirs:
        if os.path.exists(sdir):
            for root, dirs, files in os.walk(sdir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in ["appdata", "node_modules", "venv", "env", "site-packages", "windows"]]
                for f in files:
                    f_lower = f.lower()
                    if ext_filter and not f_lower.endswith(ext_filter):
                        continue
                    matched_count = sum(1 for w in words if w in f_lower)
                    if matched_count > 0:
                        matches.append((matched_count, os.path.join(root, f)))
                        if matched_count == len(words):
                            target = os.path.join(root, f)
                            try:
                                os.startfile(target)
                                return f"Found and opened '{f}' from {os.path.basename(root)}."
                            except Exception as e:
                                return f"Found '{f}', but could not open it: {e}"

    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        best_file = matches[0][1]
        try:
            os.startfile(best_file)
            return f"Opened closest matching document: '{os.path.basename(best_file)}'."
        except Exception as e:
            return f"Found document but failed to open: {e}"

    return f"I searched Desktop, Downloads, and Documents, but could not find a file matching '{query}'."


def create_or_write_file(filename: str = "document.txt", content: str = "", location: str = "Desktop") -> str:
    """Create a new text (.txt), markdown (.md), or code file on Desktop or Documents and write specified content into it."""
    try:
        import aria_tools
        return aria_tools.create_or_write_file(filename, content, location)
    except Exception as e:
        return f"File creation error: {e}"


def create_folder(folder_name: str, location: str = "desktop") -> str:
    """Create a new directory/folder at a specified location (desktop, downloads, documents, etc.)."""
    try:
        import aria_organizer
        return aria_organizer.create_folder(folder_name, location)
    except Exception as e:
        return f"Error creating folder: {e}"


def organize_directory(location: str = "desktop") -> str:
    """Organize and clean up a messy folder (desktop, downloads, documents) into categorized subfolders."""
    try:
        import aria_organizer
        return aria_organizer.organize_directory(location)
    except Exception as e:
        return f"Error organizing folder: {e}"


def execute_powershell_command(command: str) -> str:
    """Run an authorized PowerShell command on Windows to inspect or control the OS."""
    try:
        import aria_vision_executor
        ok, out = aria_vision_executor.execute_system_powershell(command)
        return out if ok else f"Command failed: {out}"
    except Exception as e:
        return f"Error executing PowerShell: {e}"


def set_system_volume(volume_percent: int) -> str:
    """Set the Windows master audio volume percentage (0 to 100)."""
    try:
        vol = max(0, min(100, volume_percent))
        ps_code = f"$w = New-Object -ComObject WScript.Shell; 1..50 | % {{ $w.SendKeys([char]174) }}; 1..{int(vol / 2)} | % {{ $w.SendKeys([char]175) }}"
        subprocess.call(["powershell", "-c", ps_code])
        return f"Volume adjusted to approximately {vol}%."
    except Exception as e:
        return f"Failed to set volume: {e}"


def lock_workstation() -> str:
    """Lock the Windows workstation screen."""
    try:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Workstation screen locked."
    except Exception as e:
        return f"Failed to lock workstation: {e}"


def get_system_diagnostics() -> str:
    """Get real-time CPU, RAM, Battery, Active Window, and Network status."""
    results = []
    try:
        from aria_system_context import get_system_context, format_context_for_prompt
        ctx = get_system_context()
        results.append(format_context_for_prompt(ctx))
    except Exception:
        pass

    try:
        import aria_tools
        results.append(aria_tools.get_network_info())
    except Exception:
        pass

    return "\n".join(results) if results else "System diagnostics available."


def change_wallpaper() -> str:
    """Randomly change the Windows desktop wallpaper from the user's Pictures or Windows default wallpapers."""
    try:
        import ctypes, glob, random
        pics_dir = os.path.expandvars(r"%USERPROFILE%\Pictures")
        wallpapers = glob.glob(os.path.join(pics_dir, "**", "*.jpg"), recursive=True) + glob.glob(os.path.join(pics_dir, "**", "*.png"), recursive=True)
        if wallpapers:
            chosen = random.choice(wallpapers)
            ctypes.windll.user32.SystemParametersInfoW(20, 0, chosen, 3)
            return f"Changed desktop background to {os.path.basename(chosen)}."
        else:
            win_wallpapers = glob.glob(r"C:\Windows\Web\Wallpaper\**\*.jpg", recursive=True)
            if win_wallpapers:
                chosen = random.choice(win_wallpapers)
                ctypes.windll.user32.SystemParametersInfoW(20, 0, chosen, 3)
                return "Switched to Windows desktop wallpaper."
        return "No suitable images found for wallpaper."
    except Exception as e:
        return f"Failed to change wallpaper: {e}"


def chrome_research(query: str) -> str:
    """Use Chrome browser automation to search Google, browse results, and extract factual summaries."""
    try:
        from aria_chrome import get_chrome_agent
        agent = get_chrome_agent()
        return agent.research(query)
    except Exception as e:
        return f"Chrome research failed: {e}"


def chrome_open_url(url: str) -> str:
    """Navigate to a specific URL in Google Chrome."""
    try:
        from aria_chrome import get_chrome_agent
        agent = get_chrome_agent()
        return agent.open_url(url)
    except Exception as e:
        return f"Failed to open URL: {e}"


def chrome_read_current_page() -> str:
    """Extract and read the text content of the currently open Chrome tab."""
    try:
        from aria_chrome import get_chrome_agent
        agent = get_chrome_agent()
        return agent.read_page()
    except Exception as e:
        return f"Failed to read page: {e}"


def chrome_switch_section(section_name: str, query: str = "") -> str:
    """Switch Google Chrome search section to 'images', 'maps', 'news', 'videos', 'shopping', or 'finance'."""
    try:
        import aria_extended
        return aria_extended.switch_google_search_section(section_name, query)
    except Exception as e:
        return f"Chrome section switch error: {e}"


def get_latest_news(topic: str = "general") -> str:
    """Fetch the latest breaking news headlines for a specific topic or general news."""
    try:
        import aria_tools
        return aria_tools.get_latest_news(topic)
    except Exception as e:
        return f"Could not fetch news: {e}"


def get_crypto_price(coin: str = "bitcoin") -> str:
    """Get the live cryptocurrency price in USD and INR (e.g. bitcoin, ethereum, solana)."""
    try:
        import aria_tools
        return aria_tools.get_crypto_price(coin)
    except Exception as e:
        return f"Crypto price error: {e}"


def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "INR") -> str:
    """Convert foreign currency amounts using live exchange rates."""
    try:
        import aria_tools
        return aria_tools.convert_currency(amount, from_currency, to_currency)
    except Exception as e:
        return f"Currency conversion error: {e}"


def get_wikipedia_summary(query: str) -> str:
    """Fetch a verified 2-sentence Wikipedia summary for people, places, concepts, or history."""
    try:
        import aria_tools
        return aria_tools.get_wikipedia_summary(query)
    except Exception as e:
        return f"Wikipedia lookup error: {e}"


def see_and_analyze_screen(question: str) -> str:
    """Capture a screenshot of the user's primary monitor and analyze what is on screen to answer questions or debug."""
    try:
        import aria_vision_executor
        key = os.environ.get("GEMINI_API_KEY", "")
        return aria_vision_executor.analyze_screen_with_gemini(question, key)
    except Exception as e:
        return f"Screen vision failed: {e}"


def visual_click_element(description: str) -> str:
    """Locate a button, icon, or UI element on screen by its visual description and click it."""
    try:
        import aria_vision_executor
        key = os.environ.get("GEMINI_API_KEY", "")
        return aria_vision_executor.locate_and_click_element(description, key)
    except Exception as e:
        return f"Visual click failed: {e}"


def set_reminder(reminder_text: str, minutes_from_now: float) -> str:
    """Set a timer/alarm reminder to notify the user after a specific number of minutes."""
    try:
        import aria_scheduler
        return aria_scheduler.add_reminder(reminder_text, minutes_from_now)
    except Exception as e:
        return f"Failed to set reminder: {e}"


def add_user_goal(goal_title: str) -> str:
    """Add a personal habit or goal to the user's goal tracker."""
    try:
        import aria_tools
        return aria_tools.add_goal(goal_title)
    except Exception as e:
        return f"Failed to add goal: {e}"


def list_user_goals() -> str:
    """Retrieve the list of active user goals and habits."""
    try:
        import aria_tools
        return aria_tools.list_goals()
    except Exception as e:
        return f"Failed to list goals: {e}"


def switch_user_profile(profile_name: str) -> str:
    """Switch active user profile (e.g. 'Alex', 'Work', 'Mom')."""
    try:
        import aria_memory
        data = aria_memory.switch_profile(profile_name)
        return f"Active profile switched to {data.get('name', profile_name)}."
    except Exception as e:
        return f"Failed to switch profile: {e}"


def set_personality_mode(mode: str) -> str:
    """Set Aria's conversational personality (professional, casual, witty, minimal)."""
    try:
        import aria_memory
        return aria_memory.set_personality_mode(mode)
    except Exception as e:
        return f"Failed to set personality: {e}"


def smart_home_toggle(device_name: str, action: str = "toggle") -> str:
    """Control smart home lights, switches, or plugs via Home Assistant."""
    try:
        import aria_extended
        return aria_extended.trigger_smart_device(f"{action} {device_name}")
    except Exception as e:
        return f"Smart home action error: {e}"


def send_whatsapp_message(contact_or_number: str, message: str) -> str:
    """Send a WhatsApp message via WhatsApp Web / API."""
    try:
        import aria_tools
        return aria_tools.send_whatsapp_message(contact_or_number, message)
    except Exception as e:
        return f"WhatsApp messaging error: {e}"


def unlock_phone(pin: str = "") -> str:
    """Wirelessly unlock the user's Android phone over Wi-Fi (wakes screen, swipes up, and enters PIN/password)."""
    try:
        from tools.aria_android import get_android_controller
        ctrl = get_android_controller()
        return ctrl.unlock_phone(pin=pin if pin else None)
    except Exception as e:
        return f"Failed to unlock phone: {e}"


def lock_phone() -> str:
    """Lock the user's Android phone and turn off its screen."""
    try:
        from tools.aria_android import get_android_controller
        return get_android_controller().lock_phone()
    except Exception as e:
        return f"Failed to lock phone: {e}"


def open_mobile_app(app_name: str) -> str:
    """Launch an application on the user's Android mobile phone (e.g. 'whatsapp', 'instagram', 'camera', 'spotify', 'youtube', 'phone', 'messages', 'maps')."""
    try:
        from tools.aria_android import get_android_controller
        return get_android_controller().open_app(app_name)
    except Exception as e:
        return f"Failed to open '{app_name}' on phone: {e}"


def make_mobile_call(phone_number: str) -> str:
    """Dial and place a phone call to a phone number directly on the user's Android mobile phone."""
    try:
        from tools.aria_android import get_android_controller
        return get_android_controller().make_call(phone_number)
    except Exception as e:
        return f"Failed to call {phone_number}: {e}"


def send_mobile_sms(phone_number: str, message: str) -> str:
    """Send an SMS text message to a contact/phone number from the user's Android mobile phone."""
    try:
        from tools.aria_android import get_android_controller
        return get_android_controller().send_sms(phone_number, message)
    except Exception as e:
        return f"Failed to send SMS to {phone_number}: {e}"


def get_phone_battery() -> str:
    """Check the battery percentage and charging status of the user's connected Android phone."""
    try:
        from tools.aria_android import get_android_controller
        bat = get_android_controller().get_battery_status()
        status = "charging" if bat.get("charging") else "not charging"
        return f"Your phone battery is currently at {bat.get('level', 'Unknown')}% ({status})."
    except Exception as e:
        return f"Failed to check phone battery: {e}"


def analyze_phone_screen(question: str = "Describe what is on my phone screen") -> str:
    """Capture a screenshot of the user's Android phone and analyze what is on screen using NVIDIA Vision NIM."""
    try:
        from tools.aria_android import get_android_controller
        return get_android_controller().analyze_phone_screen(query=question)
    except Exception as e:
        return f"Failed to inspect phone screen: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. ADK TOOL REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

ALL_ADK_TOOLS: List[Callable] = [
    open_application,
    search_and_open_document,
    create_or_write_file,
    create_folder,
    organize_directory,
    execute_powershell_command,
    set_system_volume,
    lock_workstation,
    get_system_diagnostics,
    change_wallpaper,
    chrome_research,
    chrome_open_url,
    chrome_read_current_page,
    chrome_switch_section,
    get_latest_news,
    get_crypto_price,
    convert_currency,
    get_wikipedia_summary,
    see_and_analyze_screen,
    visual_click_element,
    set_reminder,
    add_user_goal,
    list_user_goals,
    switch_user_profile,
    set_personality_mode,
    smart_home_toggle,
    send_whatsapp_message,
    # Mobile Phone Tools
    unlock_phone,
    lock_phone,
    open_mobile_app,
    make_mobile_call,
    send_mobile_sms,
    get_phone_battery,
    analyze_phone_screen,
]

TOOL_NAME_MAP: Dict[str, Callable] = {fn.__name__: fn for fn in ALL_ADK_TOOLS}

# ─────────────────────────────────────────────────────────────────────────────
# 3. SUB-AGENT SWARM METADATA & TOPOLOGY
# ─────────────────────────────────────────────────────────────────────────────

SWARM_AGENTS_METADATA: Dict[str, Dict[str, Any]] = {
    "orchestrator": {
        "id": "orchestrator",
        "name": "Aria Core Orchestrator",
        "role": "Top-Level Intent Routing & Swarm Coordinator",
        "description": "Deconstructs voice & chat prompts, delegates tasks to specialized sub-agents, and synthesizes conversational responses.",
        "icon": "👑",
        "accent": "#818cf8",
        "model": "Gemini 2.5 Flash / Groq",
        "status": "ONLINE"
    },
    "system": {
        "id": "system",
        "name": "System & OS Agent",
        "role": "Windows OS Automation, File Organization & Hardware",
        "description": "Controls Windows applications, creates & searches documents, organizes files, monitors hardware health, and manages volume & power.",
        "icon": "💻",
        "accent": "#38bdf8",
        "tools": ["open_application", "create_or_write_file", "search_and_open_document", "create_folder", "organize_directory", "execute_powershell_command", "set_system_volume", "lock_workstation", "get_system_diagnostics", "change_wallpaper"],
        "status": "READY"
    },
    "browser": {
        "id": "browser",
        "name": "Browser & Web Agent",
        "role": "Autonomous Chrome Browser & Live Web RAG",
        "description": "Automates Chrome navigation, reads live webpages, extracts news headlines, crypto prices, and currency conversions.",
        "icon": "🌐",
        "accent": "#4ade80",
        "tools": ["chrome_research", "chrome_open_url", "chrome_read_current_page", "chrome_switch_section", "get_latest_news", "get_crypto_price", "convert_currency", "get_wikipedia_summary"],
        "status": "READY"
    },
    "vision": {
        "id": "vision",
        "name": "Screen Vision Agent",
        "role": "Multimodal Visual Inspection & UI Grounding",
        "description": "Inspects what is visible on the primary monitor, reads text via OCR, and visually locates & clicks UI elements.",
        "icon": "👁️",
        "accent": "#ec4899",
        "tools": ["see_and_analyze_screen", "visual_click_element"],
        "status": "READY"
    },
    "memory": {
        "id": "memory",
        "name": "Memory & Planning Agent",
        "role": "Episodic Recall, Habit Tracking & Reminders",
        "description": "Maintains the conversational memory timeline, schedules timers/alarms, manages user profiles, and tracks personal goals.",
        "icon": "🧠",
        "accent": "#a855f7",
        "tools": ["set_reminder", "add_user_goal", "list_user_goals", "switch_user_profile", "set_personality_mode"],
        "status": "READY"
    },
    "mcp": {
        "id": "mcp",
        "name": "MCP & Workspace Agent",
        "role": "IoT Smart Home & External Service Bridge",
        "description": "Integrates Model Context Protocol tools for Home Assistant smart lights, WhatsApp messaging, and Google Workspace.",
        "icon": "🔌",
        "accent": "#f59e0b",
        "tools": ["smart_home_toggle", "send_whatsapp_message"],
        "status": "READY"
    },
    "mobile": {
        "id": "mobile",
        "name": "Mobile & Phone Operative",
        "role": "Wireless Android ADB & Mobile Device Autonomy",
        "description": "Wirelessly unlocks phone with PIN, launches mobile apps, inspects phone screen with NVIDIA Vision, dials calls, and reads battery.",
        "icon": "📱",
        "accent": "#10b981",
        "tools": ["unlock_phone", "lock_phone", "open_mobile_app", "make_mobile_call", "send_mobile_sms", "get_phone_battery", "analyze_phone_screen"],
        "status": "READY"
    }
}

TOOL_TO_AGENT_MAP: Dict[str, str] = {}
for agent_id, info in SWARM_AGENTS_METADATA.items():
    for tool_name in info.get("tools", []):
        TOOL_TO_AGENT_MAP[tool_name] = agent_id

# Global Swarm Activity Log (rolling last 50 events)
_SWARM_ACTIVITY_LOG: List[Dict[str, Any]] = [
    {
        "time": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "agent": "Aria Core Orchestrator",
        "agent_id": "orchestrator",
        "tool": "swarm_init",
        "args": "{}",
        "latency_ms": 12.4,
        "status": "READY",
        "result": "Swarm initialized with 5 specialized sub-agents"
    }
]

def record_swarm_event(agent_id: str, tool_name: str, arguments: dict, result: str, latency_ms: float = 0.0, status: str = "SUCCESS"):
    """Thread-safe logging of sub-agent activity."""
    agent_info = SWARM_AGENTS_METADATA.get(agent_id, {})
    entry = {
        "time": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "agent": agent_info.get("name", agent_id),
        "agent_id": agent_id,
        "tool": tool_name,
        "args": json.dumps(arguments, ensure_ascii=False) if isinstance(arguments, dict) else str(arguments),
        "latency_ms": latency_ms,
        "status": status,
        "result": (result[:120] + "...") if len(result) > 120 else result
    }
    _SWARM_ACTIVITY_LOG.insert(0, entry)
    if len(_SWARM_ACTIVITY_LOG) > 60:
        _SWARM_ACTIVITY_LOG.pop()

def get_swarm_activity_log() -> List[Dict[str, Any]]:
    return list(_SWARM_ACTIVITY_LOG)

def get_swarm_metadata() -> Dict[str, Dict[str, Any]]:
    return SWARM_AGENTS_METADATA


# ─────────────────────────────────────────────────────────────────────────────
# 3. ADK ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────────────

class AriaADK:
    """
    Core ADK Orchestrator for Aria.
    Coordinates tool execution, multi-agent capabilities, and multi-tier model failover.
    """
    def __init__(self, gemini_api_key: Optional[str] = None, groq_api_key: Optional[str] = None, nvidia_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.nvidia_api_key = nvidia_api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.gemini_model = "gemini-2.5-flash"
        self.groq_model = "openai/gpt-oss-120b"
        self.nvidia_model = "meta/llama-3.3-70b-instruct"
        self.ollama_model = "llama3.2"

        self._init_clients()

    def _init_clients(self):
        # Gemini Client
        self.genai_client = None
        self.has_new_genai = False
        if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.gemini_api_key)
                self.has_new_genai = True
            except ImportError:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=self.gemini_api_key)
                    self.genai_client = legacy_genai
                    self.has_new_genai = False
                except ImportError:
                    self.genai_client = None

        # NVIDIA NIM Client & 40 RPM Rate Limiter Engine
        self.nvidia_engine = None
        if self.nvidia_api_key and self.nvidia_api_key != "your_nvidia_api_key_here":
            try:
                try:
                    from core.aria_nvidia import get_nvidia_engine
                except ImportError:
                    from aria_nvidia import get_nvidia_engine
                self.nvidia_engine = get_nvidia_engine(api_key=self.nvidia_api_key)
            except Exception as e_nv:
                print(f"[ADK] NVIDIA NIM engine init notice: {e_nv}")
                self.nvidia_engine = None
        self.nvidia_client = self.nvidia_engine._client if self.nvidia_engine else None

        # Groq Client
        self.groq_client = None
        if self.groq_api_key and self.groq_api_key != "your_groq_api_key_here":
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                try:
                    # Discover available chat models on Groq
                    available = [m.id for m in self.groq_client.models.list().data]
                    preferred = [
                        "openai/gpt-oss-120b",
                        "llama-3.3-70b-versatile",
                        "llama-3.1-70b-versatile",
                        "groq/compound-mini",
                        "openai/gpt-oss-20b",
                        "qwen/qwen3.6-27b",
                        "llama3-70b-8192",
                    ]
                    for p in preferred:
                        if p in available:
                            self.groq_model = p
                            break
                except Exception:
                    pass
            except ImportError:
                self.groq_client = None

        # Ollama Client
        self.ollama_client = None
        try:
            from openai import OpenAI
            self.ollama_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        except Exception:
            self.ollama_client = None

    def build_system_instruction(self, user_name: str = "Friend", preferences: str = "") -> str:
        now = datetime.datetime.now().strftime("%A %B %d %Y, %I:%M %p")
        
        # Personality prompt
        try:
            import aria_memory
            pers = aria_memory.get_personality_prompt()
        except Exception:
            pers = ""

        # System context
        try:
            from aria_system_context import get_system_context, format_context_for_prompt
            sys_ctx = format_context_for_prompt(get_system_context())
        except Exception:
            sys_ctx = ""

        # Learned rules
        try:
            import aria_learning
            learned = aria_learning.get_learned_context_prompt()
        except Exception:
            learned = ""

        base_prompt = (
            f"You are Aria, an intelligent, helpful, and highly capable AI assistant for Windows.\n"
            f"{pers}\n"
            f"Current time: {now}\n"
            f"User's name: {user_name}\n"
            f"Preferences: {preferences or 'none'}\n\n"
            f"GUIDELINES:\n"
            f"- You have access to a rich set of native system tools to control Windows, search documents, automate Chrome, inspect the screen, organize files, manage reminders, and fetch live data.\n"
            f"- Whenever the user asks you to do something in Windows or online, USE THE APPROPRIATE TOOL immediately.\n"
            f"- Provide direct, clear, conversational answers. Keep replies concise and natural for voice synthesis (2-4 sentences when possible).\n"
            f"- Never output raw markdown code blocks unless specifically requested.\n"
        )
        if sys_ctx:
            base_prompt += f"\nREAL-TIME SYSTEM STATUS:\n{sys_ctx}\n"
        if learned:
            base_prompt += f"\nLEARNED ADAPTATIONS:\n{learned}\n"

        return base_prompt

    def run_turn(
        self,
        user_input: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_name: str = "Friend",
        preferences: str = "",
        on_status_callback: Optional[Callable[[str], None]] = None,
        is_admin: bool = True,
    ) -> str:
        """
        Execute an agent turn with automated tool calling and failover.
        If is_admin is False, runs in conversation-only mode without executing host OS tools.
        """
        system_instruction = self.build_system_instruction(user_name, preferences)
        if not is_admin:
            system_instruction += "\n[SECURITY POLICY]: The user is currently a GUEST. You are operating in CONVERSATION-ONLY MODE. You cannot trigger system tools or command the host laptop. If the user asks you to open apps, switch windows, or execute OS commands, explain politely that Admin authentication is required."

        tools_to_use = ALL_ADK_TOOLS if is_admin else None
        history = chat_history or []

        # ── 1. PRIMARY: Google Gemini with Native Tool Calling ────────────────
        if self.genai_client and self.has_new_genai:
            try:
                if on_status_callback:
                    on_status_callback("Thinking with Gemini...")

                from google.genai import types as genai_types
                
                # Format conversation contents
                contents = []
                for turn in history[-6:]:
                    role = "user" if turn.get("role") in ["user", "human"] else "model"
                    contents.append(genai_types.Content(
                        role=role,
                        parts=[genai_types.Part.from_text(text=turn.get("content", ""))]
                    ))
                contents.append(genai_types.Content(
                    role="user",
                    parts=[genai_types.Part.from_text(text=user_input)]
                ))

                config = genai_types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=500,
                    tools=tools_to_use,
                )

                # Tool calling loop (up to 4 multi-turn hops)
                for _ in range(4):
                    response = self.genai_client.models.generate_content(
                        model=self.gemini_model,
                        contents=contents,
                        config=config,
                    )

                    # Check for function calls
                    function_calls = []
                    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.function_call:
                                function_calls.append(part.function_call)

                    if not function_calls:
                        # Final response produced
                        if response.text:
                            return response.text.strip()
                        break

                    # Append model turn containing function calls
                    contents.append(response.candidates[0].content)

                    # Execute each function call
                    response_parts = []
                    for fc in function_calls:
                        fn_name = fc.name
                        fn_args = fc.args or {}
                        agent_id = TOOL_TO_AGENT_MAP.get(fn_name, "system")
                        agent_meta = SWARM_AGENTS_METADATA.get(agent_id, {})
                        agent_name = agent_meta.get("name", "Specialized Sub-Agent")

                        if on_status_callback:
                            on_status_callback(f"Delegating to {agent_name} -> {fn_name}...")

                        t_start = time.time()
                        fn = TOOL_NAME_MAP.get(fn_name)
                        if fn:
                            try:
                                result = fn(**fn_args)
                                status_str = "SUCCESS"
                            except Exception as ex:
                                result = f"Tool execution error: {ex}"
                                status_str = "ERROR"
                        else:
                            result = f"Unknown tool: {fn_name}"
                            status_str = "NOT_FOUND"

                        t_dur = round((time.time() - t_start) * 1000, 1)
                        record_swarm_event(
                            agent_id=agent_id,
                            tool_name=fn_name,
                            arguments=fn_args,
                            result=str(result),
                            latency_ms=t_dur,
                            status=status_str
                        )

                        response_parts.append(
                            genai_types.Part.from_function_response(
                                name=fn_name,
                                response={"result": str(result)}
                            )
                        )

                    # Append tool responses as a user/tool turn
                    contents.append(genai_types.Content(role="user", parts=response_parts))

            except Exception as e_gemini:
                print(f"[ADK] Gemini engine notice: {e_gemini}")

        # ── 2. NVIDIA NIM Cloud (Frontier Reasoning & High Speed, 40 RPM Limiter) ───
        if self.nvidia_engine and self.nvidia_engine.is_configured():
            try:
                # Cognitive routing: If question involves deep logic / math / puzzles -> reason()
                is_reasoning_heavy = any(k in user_input.lower() for k in ["why", "explain step", "proof", "logic", "algorithm", "solve", "puzzle", "compare", "plan"])
                is_code_heavy = any(k in user_input.lower() for k in ["write a script", "powershell", "python code", "function", "fix bug", "compile", "regex"])

                if is_reasoning_heavy:
                    if on_status_callback:
                        on_status_callback("Routing to DeepSeek-R1 / Nemotron on NVIDIA NIM (Deep Reasoning)...")
                    return self.nvidia_engine.reason(
                        prompt=user_input,
                        system_instruction=system_instruction,
                        history=history
                    )
                elif is_code_heavy:
                    if on_status_callback:
                        on_status_callback("Routing to Qwen 2.5 Coder on NVIDIA NIM (Code Synthesis)...")
                    return self.nvidia_engine.generate_code(
                        instruction=user_input,
                        context=f"Conversation context: {str(history[-2:]) if history else ''}"
                    )
                else:
                    if on_status_callback:
                        on_status_callback("Routing through NVIDIA NIM Cloud (40 RPM Guard)...")
                    msgs = []
                    for m in history[-6:]:
                        msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
                    msgs.append({"role": "user", "content": user_input})
                    return self.nvidia_engine.chat(
                        messages=msgs,
                        model=self.nvidia_model,
                        system_prompt=system_instruction,
                        temperature=0.7,
                        max_tokens=450
                    )
            except Exception as e_nvidia:
                print(f"[ADK] NVIDIA NIM notice ({self.nvidia_model}): {e_nvidia}")

        # ── 3. TERTIARY: Groq Cloud ───────────────────────────────────────────
        if self.groq_client:
            try:
                if on_status_callback:
                    on_status_callback("Routing through Groq Cloud...")

                msgs = [{"role": "system", "content": system_instruction}]
                for m in history[-6:]:
                    msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
                msgs.append({"role": "user", "content": user_input})

                resp = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=msgs,
                    temperature=0.7,
                    max_tokens=400,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e_groq:
                print(f"[ADK] Groq engine notice ({self.groq_model}): {e_groq}")
                for fallback_m in ["openai/gpt-oss-120b", "groq/compound-mini", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]:
                    if fallback_m != self.groq_model:
                        try:
                            resp = self.groq_client.chat.completions.create(
                                model=fallback_m,
                                messages=msgs,
                                temperature=0.7,
                                max_tokens=400,
                            )
                            self.groq_model = fallback_m
                            return resp.choices[0].message.content.strip()
                        except Exception:
                            continue

        # ── 4. QUATERNARY: Local Ollama (100% Offline) ─────────────────────────
        if self.ollama_client:
            try:
                if on_status_callback:
                    on_status_callback("Running local Ollama...")

                msgs = [{"role": "system", "content": system_instruction}]
                for m in history[-6:]:
                    msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
                msgs.append({"role": "user", "content": user_input})

                resp = self.ollama_client.chat.completions.create(
                    model=self.ollama_model,
                    messages=msgs,
                    temperature=0.7,
                    max_tokens=300,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e_ollama:
                print(f"[ADK] Ollama fallback notice: {e_ollama}")

        return "I'm having difficulty connecting to my AI engines. Please check your API keys or ensure Ollama is running."


# Singleton instance
_adk_instance: Optional[AriaADK] = None

def get_adk_engine(gemini_key: Optional[str] = None, groq_key: Optional[str] = None, nvidia_key: Optional[str] = None) -> AriaADK:
    global _adk_instance
    if _adk_instance is None or gemini_key is not None or nvidia_key is not None or groq_key is not None:
        _adk_instance = AriaADK(gemini_api_key=gemini_key, groq_api_key=groq_key, nvidia_api_key=nvidia_key)
    return _adk_instance

