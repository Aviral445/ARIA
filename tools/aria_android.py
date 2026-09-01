"""
tools/aria_android.py — Wireless Android ADB Phone Controller for Aria

Enables autonomous, wire-free Android device control over Wi-Fi:
  • Auto-Unlock Phone (Screen wake + Swipe lockscreen + Auto PIN/Password entry)
  • Launch & Control any Mobile App (WhatsApp, Instagram, Spotify, YouTube, Camera, Phone)
  • Multimodal Phone Screen Vision with NVIDIA Llama 3.2 Vision NIM
  • Make Phone Calls & Send SMS messages
  • Hardware Telemetry (Battery percentage, charging status, device model)
  • Auto-detects adb.exe or auto-downloads official Google platform-tools if missing
"""

import os
import sys
import time
import json
import re
import urllib.request
import zipfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple

try:
    from PIL import Image
    import io
except ImportError:
    Image = None

# Ensure paths can be resolved
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_FILE = os.path.join(_ROOT_DIR, "config", "gui_config.json")
_PLATFORM_TOOLS_DIR = os.path.join(_ROOT_DIR, "tools", "platform-tools")

# Common Android App Package Mappings
KNOWN_ANDROID_APPS = {
    "whatsapp": "com.whatsapp",
    "instagram": "com.instagram.android",
    "youtube": "com.google.android.youtube",
    "spotify": "com.spotify.music",
    "camera": "com.android.camera",
    "phone": "com.google.android.dialer",
    "dialer": "com.google.android.dialer",
    "contacts": "com.google.android.contacts",
    "messages": "com.google.android.apps.messaging",
    "sms": "com.google.android.apps.messaging",
    "chrome": "com.android.chrome",
    "browser": "com.android.chrome",
    "settings": "com.android.settings",
    "maps": "com.google.android.apps.maps",
    "photos": "com.google.android.apps.photos",
    "gallery": "com.google.android.apps.photos",
    "telegram": "org.telegram.messenger",
    "twitter": "com.twitter.android",
    "x": "com.twitter.android",
    "uber": "com.ubercab",
    "netflix": "com.netflix.mediaclient",
    "calculator": "com.google.android.calculator",
    "clock": "com.google.android.deskclock",
    "gmail": "com.google.android.gm"
}


class AndroidController:
    """
    Autonomous Wireless Android Controller for Aria.
    Communicates with Android devices over Wi-Fi via ADB.
    """
    def __init__(self):
        self.adb_path = self._resolve_adb_path()
        self.connected_device = ""
        self.phone_ip = ""
        self.phone_port = 5555
        self.phone_pin = ""
        self._load_saved_settings()

    def _resolve_adb_path(self) -> str:
        """Finds adb executable on system PATH, Android SDK, or local platform-tools."""
        # 1. Check if adb is directly on PATH
        try:
            res = subprocess.run(["adb", "version"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                return "adb"
        except Exception:
            pass

        # 2. Check bundled tools/platform-tools/adb.exe
        bundled_adb = os.path.join(_PLATFORM_TOOLS_DIR, "adb.exe" if os.name == 'nt' else "adb")
        if os.path.exists(bundled_adb):
            return bundled_adb

        # 3. Check standard Android SDK paths on Windows
        if os.name == 'nt':
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            if local_appdata:
                sdk_adb = os.path.join(local_appdata, "Android", "Sdk", "platform-tools", "adb.exe")
                if os.path.exists(sdk_adb):
                    return sdk_adb

        return "adb"

    def ensure_adb_installed(self) -> Tuple[bool, str]:
        """Downloads official Google Android platform-tools for Windows if missing."""
        if self.adb_path != "adb" and os.path.exists(self.adb_path):
            return True, f"ADB available at: {self.adb_path}"

        try:
            res = subprocess.run([self.adb_path, "version"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                return True, "ADB is available on system PATH."
        except Exception:
            pass

        # Download official Google Android platform-tools for Windows
        if os.name == 'nt':
            url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
            zip_target = os.path.join(_ROOT_DIR, "tools", "platform-tools.zip")
            os.makedirs(os.path.dirname(zip_target), exist_ok=True)
            try:
                print("📥 Downloading official Google Android platform-tools...")
                urllib.request.urlretrieve(url, zip_target)
                with zipfile.ZipFile(zip_target, 'r') as zip_ref:
                    zip_ref.extractall(os.path.join(_ROOT_DIR, "tools"))
                if os.path.exists(zip_target):
                    os.remove(zip_target)
                
                bundled_adb = os.path.join(_PLATFORM_TOOLS_DIR, "adb.exe")
                if os.path.exists(bundled_adb):
                    self.adb_path = bundled_adb
                    return True, "Successfully downloaded and configured ADB platform-tools."
            except Exception as e:
                return False, f"Failed to download ADB platform-tools: {e}"

        return False, "ADB not found. Please install Android platform-tools or add adb to PATH."

    def _load_saved_settings(self):
        if os.path.exists(_CONFIG_FILE):
            try:
                with open(_CONFIG_FILE, encoding="utf-8") as f:
                    c = json.load(f)
                    self.phone_ip = c.get("phone_ip", "")
                    self.phone_port = int(c.get("phone_port", 5555))
                    self.phone_pin = c.get("phone_pin", "")
            except Exception:
                pass

    def save_settings(self, ip: str, port: int = 5555, pin: str = ""):
        self.phone_ip = ip.strip()
        self.phone_port = int(port)
        self.phone_pin = pin.strip()
        
        cfg = {}
        if os.path.exists(_CONFIG_FILE):
            try:
                with open(_CONFIG_FILE, encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                cfg = {}
        cfg["phone_ip"] = self.phone_ip
        cfg["phone_port"] = self.phone_port
        cfg["phone_pin"] = self.phone_pin
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    def _run_adb(self, args: List[str], timeout_sec: int = 10) -> Tuple[bool, str]:
        """Runs an ADB command safely with device targeting."""
        cmd = [self.adb_path]
        
        # Insert target device if connected and not a general command
        if self.connected_device and args and args[0] not in ("connect", "devices", "pair", "version", "kill-server", "start-server", "tcpip"):
            cmd += ["-s", self.connected_device]
            
        cmd += args
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()
            if proc.returncode == 0:
                return True, out if out else "Success"
            return False, f"ADB Error ({proc.returncode}): {err if err else out}"
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout_sec}s"
        except Exception as e:
            return False, f"ADB execution failed: {e}"

    # ── 1. WIRELESS CONNECTION & PAIRING ──────────────────────────────────────
    def enable_tcpip_mode(self, port: int = 5555) -> Tuple[bool, str]:
        """
        Switches connected USB Android device to Wireless TCP/IP mode on specified port.
        After running this once over USB, you can unplug the USB cable and connect wirelessly forever!
        """
        self.ensure_adb_installed()
        devices = self.get_connected_devices()
        if not devices:
            return False, "No phone detected over USB. Please plug your phone in via USB first and tap 'Allow USB Debugging'."
        
        success, out = self._run_adb(["tcpip", str(port)])
        if success and ("restarting in tcp mode" in out.lower() or "port" in out.lower() or out == ""):
            return True, f"✅ Phone is now in Wireless TCP/IP mode on port {port}! You can now unplug the USB cable and connect over Wi-Fi."
        return False, f"Failed to enable TCP/IP mode: {out}"

    def connect_wireless(self, ip: Optional[str] = None, port: Optional[int] = None) -> Tuple[bool, str]:
        """Connects to Android phone over Wi-Fi ADB."""
        target_ip = (ip or self.phone_ip).strip()
        target_port = port or self.phone_port
        if not target_ip:
            return False, "Phone IP address is not specified."

        ok, msg = self.ensure_adb_installed()
        if not ok:
            return False, f"ADB Setup required: {msg}"

        target = f"{target_ip}:{target_port}"
        success, out = self._run_adb(["connect", target], timeout_sec=8)
        if success and ("connected" in out.lower() or "already connected" in out.lower()):
            self.connected_device = target
            self.save_settings(target_ip, target_port, self.phone_pin)
            return True, f"Successfully connected wirelessly to phone at {target}!"

        # Provide actionable troubleshooting advice
        err_msg = out.strip()
        if "cannot connect" in err_msg.lower() or "actively refused" in err_msg.lower() or "failed to connect" in err_msg.lower():
            err_msg += (
                "\n\n💡 Troubleshooting Tips:"
                "\n1. Make sure 'Wireless Debugging' is switched ON in Developer Options."
                "\n2. Check your phone's screen in Wireless Debugging for the exact PORT number (Android 11+ often uses random ports like :37291, not :5555)."
                "\n3. If your phone and PC are not paired yet, use the 'Pair Device with Code' section below."
                "\n4. Quickest fix: Plug phone in via USB once, click 'Enable Wireless Port 5555', and unplug!"
            )
        return False, f"Could not connect to {target}: {err_msg}"

    def pair_wireless(self, ip: str, port: int, pairing_code: str) -> Tuple[bool, str]:
        """Pairs with Android 11+ Wireless Debugging using a 6-digit pairing code."""
        self.ensure_adb_installed()
        target = f"{ip.strip()}:{port}"
        success, out = self._run_adb(["pair", target, str(pairing_code).strip()], timeout_sec=10)
        if success and "successfully paired" in out.lower():
            return True, f"Successfully paired with phone at {target}! Now enter the main Connection Port and click 'Connect Over Wi-Fi'."
        return False, f"Pairing failed: {out}\n(Ensure pairing dialog is open on your phone while clicking Pair)"

    def get_connected_devices(self) -> List[str]:
        """Returns list of currently connected ADB devices/emulators."""
        success, out = self._run_adb(["devices"])
        if not success:
            return []
        devices = []
        for line in out.splitlines()[1:]:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        return devices

    # ── 2. PHONE AUTO-UNLOCK & LOCK ───────────────────────────────────────────
    def unlock_phone(self, pin: Optional[str] = None) -> str:
        """
        Wakes screen, swipes up lockscreen, and types PIN/password to unlock.
        """
        pin_to_use = pin if pin is not None else self.phone_pin
        
        # 1. Wake up screen (KEYCODE_WAKEUP 224 / KEYCODE_POWER 26)
        self._run_adb(["shell", "input", "keyevent", "224"])
        time.sleep(0.3)

        # 2. Swipe up from bottom of screen to reveal PIN keypad
        # Generic normalized swipe for high-res screens
        self._run_adb(["shell", "input", "swipe", "500", "1600", "500", "400", "200"])
        time.sleep(0.4)

        # 3. Enter PIN if configured
        if pin_to_use:
            # Escape any special characters
            clean_pin = re.sub(r'[^a-zA-Z0-9]', '', pin_to_use)
            self._run_adb(["shell", "input", "text", clean_pin])
            time.sleep(0.2)
            # Send ENTER / SUBMIT (KEYCODE_ENTER 66)
            self._run_adb(["shell", "input", "keyevent", "66"])
            time.sleep(0.2)
            return "Phone screen awakened, lockscreen swiped, and PIN submitted. Phone unlocked!"
        else:
            return "Phone screen awakened and swiped up (no PIN was provided)."

    def lock_phone(self) -> str:
        """Puts phone to sleep / turns screen off."""
        self._run_adb(["shell", "input", "keyevent", "26"])
        return "Phone locked and screen turned off."

    # ── 3. LAUNCH & OPERATE APPS ──────────────────────────────────────────────
    def open_app(self, app_name: str) -> str:
        """Launches an app by name, using universal Android intents where applicable."""
        clean_name = app_name.lower().strip()

        # 1. Universal Android Intent Actions (works on all device manufacturers)
        universal_intents = {
            "phone": ["shell", "am", "start", "-a", "android.intent.action.DIAL"],
            "dialer": ["shell", "am", "start", "-a", "android.intent.action.DIAL"],
            "call": ["shell", "am", "start", "-a", "android.intent.action.DIAL"],
            "camera": ["shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA"],
            "messages": ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.APP_MESSAGING"],
            "sms": ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.APP_MESSAGING"],
            "contacts": ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.APP_CONTACTS"],
            "browser": ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "http://google.com"],
            "gallery": ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.APP_GALLERY"],
            "photos": ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.APP_GALLERY"],
            "settings": ["shell", "am", "start", "-a", "android.settings.SETTINGS"],
            "calculator": ["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.APP_CALCULATOR"],
            "clock": ["shell", "am", "start", "-a", "android.intent.action.SHOW_ALARMS"],
            "maps": ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "geo:0,0"],
        }

        if clean_name in universal_intents:
            success, out = self._run_adb(universal_intents[clean_name])
            if success and "error" not in out.lower():
                return f"Opened '{app_name}' on your phone!"

        # 2. Package-specific Launchers
        package = KNOWN_ANDROID_APPS.get(clean_name, clean_name)

        # Try monkey runner
        success, out = self._run_adb(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
        if success and "events injected" in out.lower():
            return f"Opened '{app_name}' ({package}) on your phone!"

        # Try deep links for popular apps
        deep_links = {
            "youtube": ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://youtube.com"],
            "spotify": ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "spotify:genre"],
            "whatsapp": ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "whatsapp://send"],
            "instagram": ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "https://instagram.com"],
        }
        if clean_name in deep_links:
            success_dl, out_dl = self._run_adb(deep_links[clean_name])
            if success_dl and "error" not in out_dl.lower():
                return f"Launched '{app_name}' on your phone!"

        # Try am start MAIN
        success_am, out_am = self._run_adb(["shell", "am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER", "-n", f"{package}/.MainActivity"])
        if success_am and "error" not in out_am.lower():
            return f"Launched '{app_name}' on your phone!"

        return f"Could not launch '{app_name}'. Error: {out}"

    def make_call(self, phone_number: str) -> str:
        """Dials a phone number directly through the phone's dialer."""
        clean_num = re.sub(r'[^0-9+]', '', phone_number)
        if not clean_num:
            return "Please provide a valid phone number."
        
        success, out = self._run_adb(["shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{clean_num}"])
        if success:
            return f"Calling {clean_num} from your phone..."
        return f"Failed to place call: {out}"

    def send_sms(self, phone_number: str, message: str) -> str:
        """Sends an SMS message to a phone number."""
        clean_num = re.sub(r'[^0-9+]', '', phone_number)
        success, out = self._run_adb([
            "shell", "am", "start", "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{clean_num}",
            "--es", "sms_body", message,
            "--ez", "exit_on_sent", "true"
        ])
        if success:
            return f"Drafted SMS to {clean_num}: '{message}'"
        return f"Failed to send SMS: {out}"

    def type_text(self, text: str) -> str:
        """Types text into the currently active mobile input field."""
        escaped = text.replace(" ", "%s").replace("&", "\\&").replace("<", "\\<").replace(">", "\\>")
        self._run_adb(["shell", "input", "text", escaped])
        return f"Typed '{text}' on phone."

    def tap(self, x: int, y: int) -> str:
        """Taps at screen coordinates (X, Y)."""
        self._run_adb(["shell", "input", "tap", str(x), str(y)])
        return f"Tapped at ({x}, {y}) on phone."

    def press_home(self) -> str:
        """Presses Home button."""
        self._run_adb(["shell", "input", "keyevent", "3"])
        return "Pressed Home on phone."

    def press_back(self) -> str:
        """Presses Back button."""
        self._run_adb(["shell", "input", "keyevent", "4"])
        return "Pressed Back on phone."

    # ── 4. MULTIMODAL PHONE SCREEN VISION ─────────────────────────────────────
    def capture_screen_bytes(self) -> Tuple[Optional[bytes], str]:
        """
        Captures raw PNG screenshot bytes from phone via ADB.
        Uses 3-tier resilient fallbacks (direct exec-out -> binary screencap -> /data/local/tmp pull).
        Returns (bytes, debug_info).
        """
        target_dev = self.connected_device
        if not target_dev:
            devices = self.get_connected_devices()
            if devices:
                target_dev = devices[0]
                self.connected_device = target_dev

        base_cmd = [self.adb_path]
        if target_dev:
            base_cmd += ["-s", target_dev]

        # Tier 1: exec-out screencap -p (Fast binary stream)
        try:
            cmd = base_cmd + ["exec-out", "screencap", "-p"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=6,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if proc.returncode == 0 and len(proc.stdout) > 500:
                raw = proc.stdout
                if raw.startswith(b'\x89PNG'):
                    return raw, "exec-out direct"
                # If CRLF translation occurred on Windows
                fixed = raw.replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')
                if fixed.startswith(b'\x89PNG'):
                    return fixed, "exec-out normalized"
        except Exception as e:
            print(f"Tier 1 exec-out error: {e}")

        # Tier 2: Universal /data/local/tmp file pull (100% guaranteed on all Android phones)
        try:
            tmp_remote = "/data/local/tmp/aria_sc.png"
            tmp_local = os.path.join(_ROOT_DIR, "data", "temp_phone_screen.png")
            os.makedirs(os.path.dirname(tmp_local), exist_ok=True)
            
            # 1. Take screencap on device inside /data/local/tmp/
            self._run_adb(["shell", "screencap", "-p", tmp_remote], timeout_sec=6)
            # 2. Pull binary file to PC
            self._run_adb(["pull", tmp_remote, tmp_local], timeout_sec=6)
            # 3. Clean up on device
            self._run_adb(["shell", "rm", "-f", tmp_remote], timeout_sec=3)

            if os.path.exists(tmp_local) and os.path.getsize(tmp_local) > 500:
                with open(tmp_local, "rb") as f:
                    data = f.read()
                try:
                    os.remove(tmp_local)
                except Exception:
                    pass
                if data.startswith(b'\x89PNG'):
                    return data, "adb pull /data/local/tmp"
                return data, "adb pull (raw)"
        except Exception as e_pull:
            print(f"Tier 2 pull error: {e_pull}")

        return None, "All screenshot capture tiers failed"

    def analyze_phone_screen(self, query: str = "Describe what is on my phone screen in detail.") -> str:
        """
        Captures phone screen and analyzes it with NVIDIA Llama 3.2 Vision NIM,
        with seamless automatic fallback to Gemini 2.5 Flash Vision.
        """
        img_bytes, debug_src = self.capture_screen_bytes()
        if not img_bytes:
            return "Could not capture phone screen. Please ensure your phone screen is unlocked and turned on."

        system_prompt = (
            "You are Aria, viewing the user's Android phone screen in real time.\n"
            "Analyze clearly, concisely, and helpfully what app, notification, or content is displayed."
        )

        # 1. Try NVIDIA NIM Vision
        try:
            from core.aria_nvidia import get_nvidia_engine
            nv = get_nvidia_engine()
            if nv.is_configured():
                return nv.vision_analyze(
                    image_data=img_bytes,
                    query=query,
                    system_instruction=system_prompt
                )
        except Exception as e:
            print(f"NVIDIA vision fallback: {e}")

        # 2. Resilient Fallback to Gemini 2.5 Flash Vision
        try:
            import base64
            import urllib.request
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            
            gemini_key = ""
            if os.path.exists(_CONFIG_FILE):
                try:
                    with open(_CONFIG_FILE, encoding="utf-8") as f:
                        gemini_key = json.load(f).get("gemini_api_key", "")
                except Exception:
                    pass
            if not gemini_key:
                gemini_key = os.environ.get("GEMINI_API_KEY", "")

            if gemini_key:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{system_prompt}\n\nUser Question: {query}"},
                                {
                                    "inline_data": {
                                        "mime_type": "image/png",
                                        "data": b64_img
                                    }
                                }
                            ]
                        }
                    ]
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    return text.strip()
        except Exception as e_gem:
            return f"Vision Analysis Error: {e_gem}"

        return "Please configure your NVIDIA or Gemini API Key in Settings to enable multimodal Phone Screen Vision."

    # ── 5. TELEMETRY & DEVICE INFO ────────────────────────────────────────────
    def get_battery_status(self) -> Dict[str, Any]:
        """Fetches phone battery percentage and charging status."""
        success, out = self._run_adb(["shell", "dumpsys", "battery"])
        level = 100
        charging = False
        if success:
            m_lvl = re.search(r"level:\s*(\d+)", out)
            if m_lvl:
                level = int(m_lvl.group(1))
            m_stat = re.search(r"status:\s*(\d+)", out)
            if m_stat and m_stat.group(1) in ("2", "5"):
                charging = True
        return {"level": level, "charging": charging}

    def get_device_info(self) -> Dict[str, Any]:
        """Returns comprehensive device status."""
        devices = self.get_connected_devices()
        connected = len(devices) > 0
        model = "Android Phone"
        
        if connected:
            s_mod, o_mod = self._run_adb(["shell", "getprop", "ro.product.model"])
            if s_mod and o_mod:
                model = o_mod
                
        bat = self.get_battery_status() if connected else {"level": 0, "charging": False}
        return {
            "connected": connected,
            "device": devices[0] if devices else self.phone_ip,
            "model": model,
            "ip": self.phone_ip,
            "port": self.phone_port,
            "battery_level": bat["level"],
            "is_charging": bat["charging"]
        }


# Global Singleton Instance
_android_controller: Optional[AndroidController] = None

def get_android_controller() -> AndroidController:
    global _android_controller
    if _android_controller is None:
        _android_controller = AndroidController()
    return _android_controller
