"""
aria_vision_executor.py — Autonomous OS Control & Screen Vision Engine for Aria
Implements:
1. Dynamic PowerShell & Python System Executor (Infinite OS Control)
2. Gemini 2.5 Flash Screen Vision (Look at screen & answer questions)
3. UI Element Grounding (Find button/element by visual description and click it)
"""

import os, sys, time, json, subprocess, tempfile, re
import io
from PIL import Image

try:
    import pyautogui
except ImportError:
    pyautogui = None


# ── 1. DYNAMIC POWERSHELL & SYSTEM EXECUTOR ──────────────────────────────────
def execute_system_powershell(command: str, timeout_sec: int = 15) -> tuple[bool, str]:
    """
    Executes an arbitrary PowerShell command/script with safety guards and timeouts.
    """
    # Safety blacklist for destructive commands
    dangerous_keywords = ["format-volume", "remove-item -recurse c:\\windows", "del c:\\windows", "bcdedit"]
    cmd_lower = command.lower()
    if any(k in cmd_lower for k in dangerous_keywords):
        return False, "Command blocked by security guard (destructive action)."

    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout_sec
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if proc.returncode == 0:
            return True, out if out else "Command executed successfully with no output."
        return False, f"PowerShell error (Code {proc.returncode}): {err if err else out}"
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout_sec} seconds."
    except Exception as e:
        return False, f"Execution failed: {e}"


# ── 2. SCREEN VISION (SEE & ANALYZE USER'S SCREEN) ───────────────────────────
def capture_screen_image() -> Image.Image:
    """Takes a screenshot of the primary display with multi-layered fallbacks."""
    # 1. Try PyAutoGUI / ImageGrab
    try:
        from PIL import ImageGrab
        im = ImageGrab.grab(all_screens=False)
        if im is not None:
            return im
    except Exception:
        pass

    # 2. Try PyAutoGUI
    try:
        if pyautogui is not None:
            im = pyautogui.screenshot()
            if im is not None:
                return im
    except Exception:
        pass

    # 3. Try MSS
    try:
        import mss
        with mss.MSS() as sct:
            mon = sct.monitors[1]
            sct_img = sct.grab(mon)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    except Exception:
        pass

    # 4. Fallback blank canvas with notification
    im = Image.new("RGB", (1280, 720), color=(30, 30, 30))
    return im


def analyze_screen_with_gemini(query: str, api_key: str) -> str:
    """
    Takes a snapshot of the user's screen and sends it to Gemini 2.5 Flash
    to answer questions about what is currently visible.
    """
    if not api_key or api_key == "your_gemini_api_key_here":
        return "Please configure your Gemini API key in Settings to use Screen Vision."

    try:
        shot = capture_screen_image()
        # Resize to max 1280px wide to reduce latency and bandwidth
        w, h = shot.size
        if w > 1280:
            scale = 1280.0 / w
            shot = shot.resize((1280, int(h * scale)), Image.Resampling.LANCZOS)

        img_byte_arr = io.BytesIO()
        shot.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are Aria, viewing the user's live computer screen.\n"
            f"User's Question: {query}\n"
            f"Describe clearly, concisely, and helpfully what is on the screen in 2 to 4 sentences."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                prompt
            ],
            config=types.GenerateContentConfig(max_output_tokens=350, temperature=0.4)
        )
        return response.text.strip()
    except Exception as e:
        return f"Screen vision analysis error: {e}"


# ── 3. VISUAL UI GROUNDING & CLICKING ────────────────────────────────────────
def click_ui_element_with_vision(target_desc: str, api_key: str) -> str:
    """
    Takes a screenshot, asks Gemini 2.5 Flash for the normalized (x, y) coordinates
    of the target visual element, and clicks on it using pyautogui.
    """
    if not api_key:
        return "Gemini API key required for visual UI clicking."
    if pyautogui is None:
        return "pyautogui required for mouse interaction."

    try:
        raw_shot = capture_screen_image()
        screen_w, screen_h = pyautogui.size()

        # Send resized image to Gemini for coordinate estimation
        img_byte_arr = io.BytesIO()
        raw_shot.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            f"You are a computer vision agent controlling a PC mouse.\n"
            f"Target Element: '{target_desc}'\n"
            f"Locate the target element in this screenshot.\n"
            f"Respond ONLY with a JSON object in this exact format, with no markdown fences:\n"
            f'{{"found": true, "x_percent": 0.50, "y_percent": 0.30, "label": "description of button"}}\n'
            f"If the element is not found on screen, respond with:\n"
            f'{{"found": false, "reason": "why not found"}}\n'
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                prompt
            ],
            config=types.GenerateContentConfig(max_output_tokens=150, temperature=0.1)
        )

        raw_text = response.text.strip()
        # Clean JSON fences if any
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text).strip()

        data = json.loads(raw_text)
        if data.get("found"):
            x_pct = float(data.get("x_percent", 0.5))
            y_pct = float(data.get("y_percent", 0.5))
            target_x = int(x_pct * screen_w)
            target_y = int(y_pct * screen_h)

            # Move and click smoothly
            pyautogui.moveTo(target_x, target_y, duration=0.3)
            pyautogui.click()
            label = data.get("label", target_desc)
            return f"Found and clicked '{label}' at ({target_x}, {target_y})!"
        else:
            reason = data.get("reason", "element not visible on screen")
            return f"Could not click '{target_desc}': {reason}."
    except Exception as e:
        return f"Visual click error: {e}"
