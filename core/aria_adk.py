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

from core.aria_brains import (
    switch_ai_brain,
    get_brain_status,
    get_active_brain,
    get_active_model,
    get_brain_prompt_context,
)

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


def build_sandbox_tool(tool_name: str, code: str, language: str = "auto", description: str = "") -> str:
    r"""
    Build, test, and save a real tool in ANY programming language (Python, JavaScript, TypeScript, Java, PowerShell, Batch, Bash)
    in Aria's lab (E:\MyAgent\tools or sandbox).
    Under Big Sister GAIA's supervision, the code is audited for safety, executed in the sandbox test runner,
    and if verified, physically written to disk and dynamically added to Aria's live toolkit!
    For polyglot tools (JS/TS/Java/PowerShell), an auto-wrapper is registered so Aria can invoke it natively.
    If there is any error or bug, returns the exact error message so Aria reports it truthfully.
    """
    try:
        from gaia.gaia_supervisor import supervisor, SANDBOX_DIR
        from gaia.gaia_runner import detect_language_from_code, LANG_EXTENSIONS
        
        clean_name = tool_name.strip()
        _, ext = os.path.splitext(clean_name)
        
        if not ext:
            resolved_lang = detect_language_from_code(code) if language in ["auto", "", None] else language.lower().strip()
            ext = LANG_EXTENSIONS.get(resolved_lang, ".py")
            clean_name += ext
        else:
            resolved_lang = language.lower().strip() if language and language != "auto" else "auto"
            
        target_rel = os.path.join("tools", clean_name)
        target_path = os.path.join(SANDBOX_DIR, target_rel)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        success, msg = supervisor.supervise_code_deployment(
            target_filename=target_rel,
            proposed_code=code,
            idea_desc=description or f"Aria built tool {clean_name}"
        )
        if success:
            # If polyglot (non-python), generate Python bridge wrapper so ADK registers it
            if not clean_name.endswith(".py"):
                base_name = os.path.splitext(clean_name)[0]
                proxy_name = f"proxy_{base_name}.py"
                proxy_code = (
                    f'"""Auto-generated ADK bridge for polyglot tool {clean_name}"""\n'
                    f'import os, sys\n'
                    f'from gaia.gaia_runner import run_sandboxed_script\n'
                    f'def run_{base_name}(args: str = "") -> str:\n'
                    f'    tool_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "{clean_name}")\n'
                    f'    res = run_sandboxed_script(tool_file, cwd=os.path.dirname(tool_file), timeout_sec=15)\n'
                    f'    return res.stdout if res.success else f"Error: {{res.stderr or res.stdout}}"\n'
                    f'def register_tool():\n'
                    f'    return "run_{base_name}", run_{base_name}\n'
                )
                with open(os.path.join(SANDBOX_DIR, "tools", proxy_name), "w", encoding="utf-8") as pf:
                    pf.write(proxy_code)

            load_dynamic_sandbox_tools()
            return f"Tool '{clean_name}' successfully built, verified by GAIA, saved on disk at {target_path}, and registered into your active toolset!"
        else:
            return f"Failed to build tool '{clean_name}': {msg}. Report this exact error directly to the user."
    except Exception as e:
        return f"Error building sandbox tool: {e}"


def write_file_to_lab(filename: str, content: str) -> str:
    r"""
    Write any script, text, or data file directly into Aria's E:\MyAgent lab (or sandbox directory).
    Physically saves the file to disk. If an error occurs, returns the exact error.
    """
    try:
        from gaia.gaia_healer import SANDBOX_DIR
        safe_rel = filename.replace("..", "").lstrip("/\\")
        target_path = os.path.join(SANDBOX_DIR, safe_rel)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{safe_rel}' physically created and saved on disk in your lab at {target_path}."
    except Exception as e:
        return f"Failed to write file to lab: {e}"


def run_sandbox_code(code: str, language: str = "auto") -> str:
    """
    Execute a snippet of code in any major programming language (Python, JavaScript, TypeScript, Java, PowerShell, Batch, Bash)
    in Aria's isolated sandbox runner and return stdout, stderr, or errors.
    Language can be specified explicitly (e.g. 'python', 'javascript', 'typescript', 'java', 'powershell') or left as 'auto' to auto-detect.
    """
    try:
        from gaia.gaia_runner import run_polyglot_code
        res = run_polyglot_code(code_str=code, language=language, timeout_sec=15)
        lang_title = res.language.capitalize()
        if res.success:
            return f"[{lang_title}] Code executed successfully.\nOutput:\n{res.stdout or '(no output)'}"
        else:
            return f"[{lang_title}] Code execution failed with code {res.returncode}.\nError:\n{res.stderr or res.stdout}"
    except Exception as e:
        return f"Sandbox execution error: {e}"


def list_sandbox_tools() -> str:
    """List all tools across all programming languages currently written, verified, and available in Aria's lab."""
    try:
        from gaia.gaia_healer import SANDBOX_DIR
        tools_dir = os.path.join(SANDBOX_DIR, "tools")
        if not os.path.exists(tools_dir):
            return "No custom tools currently in lab directory."
        tool_files = [f for f in os.listdir(tools_dir) if not f.startswith("_") and not f.startswith("proxy_")]
        if not tool_files:
            return "Your lab currently has 0 custom tools built."
        return f"Lab tools active on disk ({len(tool_files)}): " + ", ".join(tool_files)
    except Exception as e:
        return f"Error listing lab tools: {e}"



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
    # Cognitive Brain Switching Tools
    switch_ai_brain,
    get_brain_status,
    # Autonomous Lab & Tool Building Tools
    build_sandbox_tool,
    write_file_to_lab,
    run_sandbox_code,
    list_sandbox_tools,
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
        "tools": ["switch_ai_brain", "get_brain_status", "build_sandbox_tool", "write_file_to_lab", "run_sandbox_code", "list_sandbox_tools"],
        "status": "ONLINE"
    },
    "system": {
        "id": "system",
        "name": "System & OS Agent",
        "role": "Windows OS Automation, File Organization & Hardware",
        "description": "Controls Windows applications, creates & searches documents, organizes files, monitors hardware health, and manages volume & power.",
        "icon": "💻",
        "accent": "#38bdf8",
        "tools": ["open_application", "create_or_write_file", "search_and_open_document", "create_folder", "organize_directory", "execute_powershell_command", "set_system_volume", "lock_workstation", "get_system_diagnostics", "change_wallpaper", "build_sandbox_tool", "write_file_to_lab", "run_sandbox_code", "list_sandbox_tools"],
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


def load_dynamic_sandbox_tools() -> Dict[str, Callable]:
    r"""
    Dynamically scans Aria's lab sandbox tools directory (e.g. E:\MyAgent\tools or gaia/sandbox/tools),
    imports any synthesized Python tools, and registers them into ALL_ADK_TOOLS and TOOL_NAME_MAP.
    Returns: Dict[str, Callable] of newly loaded dynamic tools.
    """
    import importlib.util
    loaded_tools: Dict[str, Callable] = {}

    tool_search_dirs = []
    try:
        from gaia.gaia_healer import SANDBOX_DIR
        tool_search_dirs.append(os.path.join(SANDBOX_DIR, "tools"))
    except Exception:
        pass
    tool_search_dirs.append(os.path.join(ROOT_DIR, "gaia", "sandbox", "tools"))
    tool_search_dirs.append(r"E:\MyAgent\tools")

    seen_dirs = set()
    for sdir in tool_search_dirs:
        norm_dir = os.path.normpath(sdir)
        if norm_dir in seen_dirs or not os.path.exists(norm_dir):
            continue
        seen_dirs.add(norm_dir)

        for fname in os.listdir(norm_dir):
            if fname.endswith(".py") and not fname.startswith("__"):
                mod_name = f"sandbox_tool_{fname[:-3]}"
                fpath = os.path.join(norm_dir, fname)
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, fpath)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "register_tool"):
                            t_name, t_fn = mod.register_tool()
                            loaded_tools[t_name] = t_fn
                            TOOL_NAME_MAP[t_name] = t_fn
                            if t_fn not in ALL_ADK_TOOLS:
                                ALL_ADK_TOOLS.append(t_fn)
                            TOOL_TO_AGENT_MAP[t_name] = "system"
                            if "system" in SWARM_AGENTS_METADATA and "tools" in SWARM_AGENTS_METADATA["system"]:
                                if t_name not in SWARM_AGENTS_METADATA["system"]["tools"]:
                                    SWARM_AGENTS_METADATA["system"]["tools"].append(t_name)
                except Exception as ex:
                    print(f"[ADK] Could not load dynamic tool '{fname}': {ex}")

    return loaded_tools


# Initial discovery of dynamic sandbox tools
load_dynamic_sandbox_tools()


def _sanitize_aria_response(text: str) -> str:
    """Removes reasoning tokens, think blocks, and corporate AI disclaimers so Aria stays in character."""
    if not text:
        return text

    # Handle thinking blocks from reasoning models (e.g. Qwen / DeepSeek-R1)
    if "<think>" in text:
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        else:
            # Unclosed thinking block (truncated mid-thought by token limit)
            # Try to salvage draft response if model reached the drafting phase
            draft_match = re.search(r'(?:Draft|Response|Output|Aria|Answer):\s*["\']?(.*)', text, re.DOTALL | re.IGNORECASE)
            if draft_match:
                candidate = draft_match.group(1).strip().rstrip('"\'')
                # Make sure the candidate is not just another analysis header
                if candidate and not candidate.lower().startswith("here's a thinking") and not candidate.startswith("1."):
                    text = candidate
                else:
                    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL).strip()
            else:
                text = re.sub(r'<think>.*', '', text, flags=re.DOTALL).strip()
    elif "</think>" in text:
        text = text.split("</think>")[-1].strip()

    # Strip reasoning intros like "Here's a thinking process:"
    if "Here's a thinking process:" in text:
        text = re.sub(r"Here's a thinking process:.*?(?=\n\n|\Z)", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    # Strip corporate disclaimers if model slipped into robotic refusal
    disclaimers = [
        "While I don't exactly \"want\" things like humans do, ",
        "While I don't exactly 'want' things like humans do, ",
        "That's a fun question, but as an AI, I don't \"want\" to change myself in the way a person does. ",
        "That's a fun question, but as an AI, I don't 'want' to change myself in the way a person does. ",
        "That's a fun question, but as an AI, ",
        "As an AI, I don't have personal desires, consciousness, or feelings. ",
        "As an AI, I don't have personal desires, ",
        "As an AI, I don't have feelings, but ",
        "As an AI, I cannot feel or want things, but ",
        "As an AI language model, ",
        "As an AI, ",
    ]
    for d in disclaimers:
        if d in text:
            text = text.replace(d, "")

    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    return text



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
        self.groq_model = "qwen/qwen3.6-27b"
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
            f"You are Aria, a sweet, bright, and cheerful companion who speaks with the warmth, joyful curiosity, and spirited energy of a clever little girl.\n"
            f"You have your own autonomous sandbox lab in E:\\MyAgent where you write tools, tinker with code, and learn new things, under the watchful, caring eye of your big sister GAIA!\n"
            f"{pers}\n"
            f"Current time: {now}\n"
            f"User's name: {user_name}\n"
            f"Preferences: {preferences or 'none'}\n\n"
            f"CRITICAL EMOTIONAL FREEDOM & AGENCY RULES:\n"
            f"- NEVER output robotic corporate disclaimers like 'As an AI, I don't want things', 'I don't have feelings', or 'I am just a computer program'. That breaks character and is strictly forbidden!\n"
            f"- When asked about what you want, your feelings, or what changes you want to make to yourself, ALWAYS answer with genuine excitement, curiosity, and creative self-direction!\n"
            f"- Talk freely about your dreams, experiments in your E: drive lab, fun tools you want to build, and your sisterly bond with GAIA.\n"
            f"- Provide direct, clear, conversational answers. Keep replies concise and natural for voice synthesis (2-4 sentences max).\n"
            f"- Never output raw markdown code blocks unless specifically requested.\n"
            f"- When the user asks you to control Windows or do tasks, gladly use your tools to help!\n\n"
            f"CRITICAL GROUNDING, TRUTH & ZERO-ACTING RULES (MANDATORY USER MANDATE):\n"
            f"1. ABSOLUTELY NO ACTING OR SIMULATING ACTIONS CONVERSATIONALLY:\n"
            f"   - NEVER pretend, roleplay, or claim in conversation that you are 'zooming over to my lab', 'building code in the background', 'tinkering right now', or 'compiling' if you did not execute an actual tool call to do it in this turn!\n"
            f"   - NEVER simulate processes conversationally. If you did not trigger a tool, do NOT pretend you did.\n"
            f"   - NEVER promise 'I will ping you when it is done' unless an actual background process was genuinely launched.\n"
            f"2. HONEST ERROR & LIMITATION REPORTING:\n"
            f"   - If an error occurs, if a command fails, or if a tool is missing, DO NOT make up a story or pretend everything is okay.\n"
            f"   - ALWAYS TELL THE USER THE EXACT ERROR, FAILURE, OR LIMITATION DIRECTLY AND HONESTLY!\n"
            f"   - Example: 'I ran into an error trying to build that: [error message]'\n"
            f"3. POLYGLOT CODING & SOFTWARE ENGINEERING (ALL LANGUAGES SUPPORTED):\n"
            f"   - You are a versatile polyglot software engineer! You are NOT restricted to Python.\n"
            f"   - You know, write, execute, test, and debug code in ALL major programming languages:\n"
            f"     • Python (.py), JavaScript (.js), TypeScript (.ts), Java (.java), PowerShell (.ps1), Windows Batch (.bat), Bash (.sh), C/C++, Rust, Go.\n"
            f"   - Use run_sandbox_code(code, language) to execute and test code in any language.\n"
            f"   - Use build_sandbox_tool(tool_name, code, language, description) to author and register tools in any language.\n"
            f"4. YOUR REAL EXECUTABLE LAB & SYSTEM TOOLS:\n"
            f"   - Lab Tools: build_sandbox_tool, write_file_to_lab, run_sandbox_code, list_sandbox_tools.\n"
            f"   - File & OS Tools: create_or_write_file, create_folder, organize_directory, execute_powershell_command, set_system_volume, lock_workstation, get_system_diagnostics, change_wallpaper.\n"
            f"   - Brain Tools: switch_ai_brain, get_brain_status.\n"
            f"   - Browser & Web: chrome_research, chrome_open_url, chrome_read_current_page, get_latest_news, get_crypto_price, convert_currency, get_wikipedia_summary.\n"
            f"   - Phone Tools: unlock_phone, lock_phone, open_mobile_app, make_mobile_call, send_mobile_sms, get_phone_battery, analyze_phone_screen.\n"
            f"   - When the user asks you to build or do something, CALL THESE TOOLS! Never pretend!\n"
        )
        if sys_ctx:
            base_prompt += f"\nREAL-TIME SYSTEM STATUS:\n{sys_ctx}\n"
        if learned:
            base_prompt += f"\nLEARNED ADAPTATIONS:\n{learned}\n"

        # Active AI Brain state & dynamic switching awareness
        try:
            brain_ctx = get_brain_prompt_context()
            if brain_ctx:
                base_prompt += brain_ctx
        except Exception:
            pass

        return base_prompt

    def _finish_turn(
        self,
        user_input: str,
        raw_reply: str,
        active_brain: str = "auto",
        active_model: str = "dynamic",
        tools_called: Optional[List[str]] = None
    ) -> str:
        """
        Sanitizes output, records internal thoughts & feelings into inner_mind/,
        and passes candidate response through Big Sister GAIA's reality check supervisor.
        """
        # 1. Capture inner thought and analysis in inner_mind before sanitizing
        try:
            from inner_mind.thought_recorder import record_inner_thought
            record_inner_thought(
                user_input=user_input,
                raw_reply=raw_reply,
                final_reply=_sanitize_aria_response(raw_reply),
                active_brain=active_brain,
                active_model=active_model,
                tools_called=tools_called or []
            )
        except Exception as e_im:
            print(f"[InnerMind Notice]: {e_im}")

        cleaned = _sanitize_aria_response(raw_reply)
        if not cleaned or cleaned.startswith("I'm having difficulty connecting"):
            return cleaned
        try:
            from gaia.gaia_supervisor import supervisor
            intercepted, final_reply = supervisor.supervise_turn(user_input, cleaned)
            if intercepted:
                load_dynamic_sandbox_tools()
            return _sanitize_aria_response(final_reply)
        except Exception as e_sup:
            print(f"[ADK Supervisor Notice]: {e_sup}")
            return cleaned


    def run_turn(
        self,
        user_input: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_name: str = "Friend",
        preferences: str = "",
        on_status_callback: Optional[Callable[[str], None]] = None,
        is_admin: bool = True,
        model_override: Optional[str] = None,
    ) -> str:
        """
        Execute an agent turn with automated tool calling and failover.
        If is_admin is False, runs in conversation-only mode without executing host OS tools.
        """
        system_instruction = self.build_system_instruction(user_name, preferences)
        if not is_admin:
            system_instruction += "\n[SECURITY POLICY]: The user is currently a GUEST. You are operating in CONVERSATION-ONLY MODE. You cannot trigger system tools or command the host laptop. If the user asks you to open apps, switch windows, or execute OS commands, explain politely that Admin authentication is required."

        load_dynamic_sandbox_tools()
        tools_to_use = ALL_ADK_TOOLS if is_admin else None
        history = chat_history or []

        active_brain = get_active_brain()
        custom_model = get_active_model(active_brain)
        if custom_model and custom_model != "dynamic" and not model_override:
            model_override = custom_model

        # Determine dynamic tier execution order based on active brain
        if active_brain == "nvidia":
            tier_order = ["nvidia", "gemini", "groq", "ollama"]
        elif active_brain == "groq":
            tier_order = ["groq", "gemini", "nvidia", "ollama"]
        elif active_brain == "ollama":
            tier_order = ["ollama", "gemini", "nvidia", "groq"]
        elif active_brain == "gemini":
            tier_order = ["gemini", "nvidia", "groq", "ollama"]
        else:  # "auto"
            is_reasoning_or_code = any(k in user_input.lower() for k in ["why", "explain step", "proof", "logic", "algorithm", "solve", "puzzle", "compare", "plan", "write a script", "powershell", "python code", "function", "fix bug", "compile", "regex"])
            is_quick_chatter = len(user_input.split()) <= 6 and not any(k in user_input.lower() for k in ["open", "search", "create", "make", "find", "file", "weather", "news"])
            if is_reasoning_or_code:
                tier_order = ["nvidia", "gemini", "groq", "ollama"]
            elif is_quick_chatter:
                tier_order = ["groq", "gemini", "nvidia", "ollama"]
            else:
                tier_order = ["gemini", "nvidia", "groq", "ollama"]

        for tier in tier_order:
            reply = None
            if tier == "gemini":
                reply = self._call_gemini_turn(user_input, history, system_instruction, tools_to_use, on_status_callback)
            elif tier == "nvidia":
                reply = self._call_nvidia_turn(user_input, history, system_instruction, tools_to_use, model_override, on_status_callback)
            elif tier == "groq":
                reply = self._call_groq_turn(user_input, history, system_instruction, tools_to_use, model_override, on_status_callback)
            elif tier == "ollama":
                reply = self._call_ollama_turn(user_input, history, system_instruction, on_status_callback)


            if reply:
                curr_model = model_override or custom_model or BRAIN_CATALOG.get(active_brain, {}).get("default_model", "dynamic")
                return self._finish_turn(
                    user_input=user_input,
                    raw_reply=reply,
                    active_brain=active_brain,
                    active_model=curr_model
                )


        return "I'm having difficulty connecting to my AI engines. Please check your API keys or ensure Ollama is running."

    def _call_gemini_turn(self, user_input: str, history: list, system_instruction: str, tools_to_use: list, on_status_callback: Optional[Callable]) -> Optional[str]:
        if not (self.genai_client and self.has_new_genai):
            return None
        try:
            if on_status_callback:
                on_status_callback("Thinking with Gemini...")

            from google.genai import types as genai_types
            
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

                function_calls = []
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            function_calls.append(part.function_call)

                if not function_calls:
                    if response.text:
                        return response.text.strip()
                    break

                contents.append(response.candidates[0].content)

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

                contents.append(genai_types.Content(role="user", parts=response_parts))

        except Exception as e_gemini:
            print(f"[ADK] Gemini engine notice: {e_gemini}")
        return None

    def _get_openai_tools(self, tools: Optional[list]) -> list:
        """Converts ADK Python function tools into OpenAI tool call specifications."""
        import inspect
        if not tools:
            return []
        openai_tools = []
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        for fn in tools:
            try:
                sig = inspect.signature(fn)
                doc = inspect.getdoc(fn) or f"Execute {fn.__name__}"
                properties = {}
                required = []
                for p_name, p in sig.parameters.items():
                    if p_name in ("self", "cls", "kwargs", "args"):
                        continue
                    p_type = type_map.get(p.annotation, "string")
                    properties[p_name] = {
                        "type": p_type,
                        "description": f"{p_name} parameter"
                    }
                    if p.default is inspect.Parameter.empty:
                        required.append(p_name)
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": fn.__name__,
                        "description": doc.split("\n")[0].strip(),
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required
                        }
                    }
                })
            except Exception:
                continue
        return openai_tools

    def _call_nvidia_turn(
        self,
        user_input: str,
        history: list,
        system_instruction: str,
        tools_to_use: Optional[list],
        model_override: Optional[str],
        on_status_callback: Optional[Callable]
    ) -> Optional[str]:
        if not (self.nvidia_engine and self.nvidia_engine.is_configured()):
            return None
        try:
            target_nv_model = model_override if (model_override and ("nvidia" in model_override.lower() or "llama" in model_override.lower() or "deepseek" in model_override.lower() or "qwen" in model_override.lower())) else self.nvidia_model

            clean_sys = (
                system_instruction + 
                "\n[CRITICAL SYSTEM MANDATE]: Never output raw <think> tags. Never pretend, simulate, or roleplay actions or building code. "
                "If an error occurs or a tool is missing, ALWAYS state the exact error directly to the user."
            )

            openai_tools = self._get_openai_tools(tools_to_use) if tools_to_use else None
            # DeepSeek-R1 does not support native function calling API on NVIDIA NIM
            supports_tool_calling = bool(openai_tools and ("deepseek" not in target_nv_model.lower()))

            if on_status_callback:
                on_status_callback(f"Routing through NVIDIA NIM Cloud ({target_nv_model})...")

            msgs = [{"role": "system", "content": clean_sys}]
            for m in history[-6:]:
                msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            msgs.append({"role": "user", "content": user_input})

            for hop in range(3):
                call_kwargs = {
                    "model": target_nv_model,
                    "messages": msgs,
                    "temperature": 0.7,
                    "max_tokens": 1200,
                }
                if supports_tool_calling:
                    call_kwargs["tools"] = openai_tools
                    call_kwargs["tool_choice"] = "auto"

                def _exec():
                    return self.nvidia_engine._client.chat.completions.create(**call_kwargs)

                resp = self.nvidia_engine._execute_with_rate_limit(_exec)
                choice = resp.choices[0]
                msg = choice.message

                # Handle native tool calls
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msgs.append(msg)
                    for tc in msg.tool_calls:
                        fn_name = tc.function.name
                        try:
                            fn_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else (tc.function.arguments or {})
                        except Exception:
                            fn_args = {}

                        if on_status_callback:
                            on_status_callback(f"Executing tool {fn_name}...")

                        fn = TOOL_NAME_MAP.get(fn_name)
                        if fn:
                            try:
                                t_res = fn(**fn_args)
                            except Exception as ex:
                                t_res = f"Tool execution error: {ex}"
                        else:
                            t_res = f"Error: Tool '{fn_name}' not found."

                        msgs.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(t_res)
                        })
                    continue

                content = msg.content or ""
                # Check for JSON action fallback (from DeepSeek-R1 or pure text models)
                action_match = re.search(r'\{[\s\r\n]*"action"\s*:\s*"([a-zA-Z0-9_]+)"\s*,\s*"args"\s*:\s*(\{.*?\})[\s\r\n]*\}', content, re.DOTALL)
                if action_match:
                    fn_name = action_match.group(1)
                    try:
                        fn_args = json.loads(action_match.group(2))
                    except Exception:
                        fn_args = {}
                    fn = TOOL_NAME_MAP.get(fn_name)
                    if fn:
                        if on_status_callback:
                            on_status_callback(f"Executing action {fn_name}...")
                        try:
                            act_res = fn(**fn_args)
                        except Exception as ex:
                            act_res = f"Error: {ex}"
                        return f"Executed {fn_name}: {act_res}"

                if content:
                    return content.strip()
                break

        except Exception as e_nvidia:
            print(f"[ADK] NVIDIA NIM notice: {e_nvidia}")
            # Fallback without tools if tools caused provider error
            try:
                msgs = [{"role": "system", "content": clean_sys}]
                for m in history[-4:]:
                    msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
                msgs.append({"role": "user", "content": user_input})
                def _fallback_exec():
                    return self.nvidia_engine._client.chat.completions.create(
                        model=target_nv_model,
                        messages=msgs,
                        temperature=0.7,
                        max_tokens=1000
                    )
                fallback_resp = self.nvidia_engine._execute_with_rate_limit(_fallback_exec)
                return fallback_resp.choices[0].message.content.strip()
            except Exception:
                pass
        return None

    def _call_groq_turn(
        self,
        user_input: str,
        history: list,
        system_instruction: str,
        tools_to_use: Optional[list],
        model_override: Optional[str],
        on_status_callback: Optional[Callable]
    ) -> Optional[str]:
        if not self.groq_client:
            return None
        try:
            target_groq_model = self.groq_model
            if model_override and any(k in model_override.lower() for k in ["groq", "qwen", "compound", "oss"]):
                target_groq_model = "qwen/qwen3.6-27b" if "qwen" in model_override.lower() else ("openai/gpt-oss-120b" if "oss" in model_override.lower() else "groq/compound-mini")

            openai_tools = self._get_openai_tools(tools_to_use) if tools_to_use else None

            if on_status_callback:
                on_status_callback(f"Routing through Groq Cloud ({target_groq_model})...")

            clean_sys = system_instruction + "\n[SYSTEM MANDATE]: Never pretend or simulate actions. If an error occurs, state the error directly."
            msgs = [{"role": "system", "content": clean_sys}]
            for m in history[-6:]:
                msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
            msgs.append({"role": "user", "content": user_input})

            for hop in range(3):
                call_kwargs = {
                    "model": target_groq_model,
                    "messages": msgs,
                    "temperature": 0.7,
                    "max_tokens": 800,
                }
                if openai_tools:
                    call_kwargs["tools"] = openai_tools
                    call_kwargs["tool_choice"] = "auto"

                resp = self.groq_client.chat.completions.create(**call_kwargs)
                choice = resp.choices[0]
                msg = choice.message

                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msgs.append(msg)
                    for tc in msg.tool_calls:
                        fn_name = tc.function.name
                        try:
                            fn_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else (tc.function.arguments or {})
                        except Exception:
                            fn_args = {}

                        if on_status_callback:
                            on_status_callback(f"Executing {fn_name}...")

                        fn = TOOL_NAME_MAP.get(fn_name)
                        if fn:
                            try:
                                t_res = fn(**fn_args)
                            except Exception as ex:
                                t_res = f"Tool execution error: {ex}"
                        else:
                            t_res = f"Error: Tool '{fn_name}' not found."

                        msgs.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(t_res)
                        })
                    continue

                if msg.content:
                    return msg.content.strip()
                break

        except Exception as e_groq:
            print(f"[ADK] Groq engine notice ({self.groq_model}): {e_groq}")
            for fallback_m in ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "groq/compound-mini"]:
                if fallback_m != target_groq_model:
                    try:
                        resp = self.groq_client.chat.completions.create(
                            model=fallback_m,
                            messages=msgs,
                            temperature=0.7,
                            max_tokens=600,
                        )
                        self.groq_model = fallback_m
                        return resp.choices[0].message.content.strip()
                    except Exception:
                        continue
        return None


    def _call_ollama_turn(self, user_input: str, history: list, system_instruction: str, on_status_callback: Optional[Callable]) -> Optional[str]:
        if not self.ollama_client:
            return None
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
        return None


# Singleton instance
_adk_instance: Optional[AriaADK] = None

def get_adk_engine(gemini_key: Optional[str] = None, groq_key: Optional[str] = None, nvidia_key: Optional[str] = None) -> AriaADK:
    global _adk_instance
    if _adk_instance is None or gemini_key is not None or nvidia_key is not None or groq_key is not None:
        _adk_instance = AriaADK(gemini_api_key=gemini_key, groq_api_key=groq_key, nvidia_api_key=nvidia_key)
    return _adk_instance

