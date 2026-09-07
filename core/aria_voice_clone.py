"""
core/aria_voice_clone.py — Custom Voice Profile & Cloning Manager (Feature 4)
Manages custom synthesized voice profiles, reference audio clips, and tailored
pitch, speed, and timbre maps for Piper and edge-tts engines.
"""

import os
import json
import shutil
import time
from typing import Dict, Any, List, Optional, Tuple

from core.paths import DATA_DIR, get_data_file

PROFILES_DIR = os.path.join(DATA_DIR, "voice_profiles")
ACTIVE_VOICE_CONFIG = os.path.join(DATA_DIR, "active_voice_profile.json")

DEFAULT_PROFILES = {
    "Aria (Default)": {
        "engine": "piper",
        "model": "en_US-lessac-medium",
        "rate": 1.0,
        "pitch": 0,
        "description": "Standard warm, upbeat personal assistant voice."
    },
    "Aria (Calm & Soothing)": {
        "engine": "piper",
        "model": "en_US-amy-medium",
        "rate": 0.9,
        "pitch": -2,
        "description": "Relaxed and calming cadence for late-night or focus sessions."
    },
    "Aria (Expressive Neural)": {
        "engine": "edge-tts",
        "model": "en-US-AnaNeural",
        "rate": 1.05,
        "pitch": 2,
        "description": "High-fidelity neural expressive voice with emotional responsiveness."
    },
    "Custom Cloned Voice": {
        "engine": "custom",
        "model": "cloned_profile_reference",
        "rate": 1.0,
        "pitch": 0,
        "sample_path": "",
        "description": "User custom recorded voice reference profile."
    }
}


def _ensure_profiles_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)
    cfg_file = os.path.join(PROFILES_DIR, "profiles.json")
    if not os.path.exists(cfg_file):
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PROFILES, f, indent=2)


def list_voice_profiles() -> Dict[str, Any]:
    """Returns all registered voice profiles."""
    _ensure_profiles_dir()
    cfg_file = os.path.join(PROFILES_DIR, "profiles.json")
    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_PROFILES


def get_active_voice_profile() -> Dict[str, Any]:
    """Retrieves the currently active voice profile."""
    if os.path.exists(ACTIVE_VOICE_CONFIG):
        try:
            with open(ACTIVE_VOICE_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"name": "Aria (Default)", **DEFAULT_PROFILES["Aria (Default)"]}


def set_active_voice_profile(name: str) -> Tuple[bool, str]:
    """Switches the active voice profile by name."""
    profiles = list_voice_profiles()
    match = None
    for p_name in profiles:
        if name.lower() in p_name.lower():
            match = p_name
            break

    if not match:
        available = ", ".join(profiles.keys())
        return False, f"Profile '{name}' not found. Available profiles: {available}"

    active_data = {"name": match, **profiles[match]}
    with open(ACTIVE_VOICE_CONFIG, "w", encoding="utf-8") as f:
        json.dump(active_data, f, indent=2)

    return True, f"Voice profile successfully switched to '{match}'!"


def create_custom_voice_profile(
    name: str,
    reference_audio_path: str = "",
    rate: float = 1.0,
    pitch: int = 0,
    description: str = ""
) -> Dict[str, Any]:
    """Registers a new custom voice profile with optional reference audio."""
    _ensure_profiles_dir()
    profiles = list_voice_profiles()

    stored_sample = ""
    if reference_audio_path and os.path.exists(reference_audio_path):
        sample_ext = os.path.splitext(reference_audio_path)[1]
        sample_name = f"sample_{int(time.time())}{sample_ext}"
        dest_sample = os.path.join(PROFILES_DIR, sample_name)
        try:
            shutil.copy2(reference_audio_path, dest_sample)
            stored_sample = dest_sample
        except Exception:
            pass

    profiles[name] = {
        "engine": "custom_cloned",
        "model": "cloned_profile",
        "rate": max(0.5, min(2.0, rate)),
        "pitch": max(-10, min(10, pitch)),
        "sample_path": stored_sample,
        "description": description or f"Custom cloned voice profile for {name}.",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    cfg_file = os.path.join(PROFILES_DIR, "profiles.json")
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)

    return {"success": True, "name": name, "profile": profiles[name]}


def aria_voice_profile_tool(action: str = "list", profile_name: str = "") -> str:
    """
    Manages custom voice profiles and voice cloning configurations.
    Args:
        action: 'list' to view available profiles, 'switch' or 'set' to activate one.
        profile_name: Name of the profile to activate (e.g. 'Calm', 'Expressive', 'Default').
    """
    if action in ["switch", "set"]:
        if not profile_name:
            return "Please specify a voice profile name to switch to."
        ok, msg = set_active_voice_profile(profile_name)
        return msg

    profiles = list_voice_profiles()
    active = get_active_voice_profile().get("name", "Unknown")
    lines = [f"Active Voice Profile: {active}\nAvailable Profiles:"]
    for p_name, data in profiles.items():
        curr_marker = " ★ (Active)" if p_name == active else ""
        lines.append(f"- {p_name}{curr_marker}: {data.get('description', '')} (Rate: {data.get('rate')}, Pitch: {data.get('pitch')})")
    return "\n".join(lines)


def register_tool() -> Tuple[str, Any]:
    """Registers aria_voice_profile_tool into Aria ADK."""
    return ("aria_voice_profile_tool", aria_voice_profile_tool)
