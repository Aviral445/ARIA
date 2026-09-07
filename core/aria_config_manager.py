"""
core/aria_config_manager.py — Dynamic Engine Configuration & Limits Manager

Decouples token limits, execution timeouts, model parameters, and fallbacks
from the core turn loop. Enables safe runtime adjustments by GAIA's Architect
without editing code.
"""

import os
import json
import threading
from typing import Dict, Any, Optional

try:
    from .paths import CONFIG_DIR
except ImportError:
    from paths import CONFIG_DIR

CONFIG_FILE = os.path.join(CONFIG_DIR, "engine_config.json")
_lock = threading.Lock()
_CACHED_CONFIG: Optional[Dict[str, Any]] = None

DEFAULT_ENGINE_CONFIG: Dict[str, Any] = {
    "limits": {
        "gemini_max_output_tokens": 4096,
        "nvidia_max_tokens": 4096,
        "groq_max_tokens": 4096,
        "ollama_max_tokens": 4096,
        "gaia_architect_max_tokens": 8192,
    },
    "parameters": {
        "temperature": 0.7,
        "max_tool_hops": 4,
        "timeout_sec": 30,
        "history_turn_limit": 6,
    },
    "models": {
        "preferred_gemini": ["gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-2.5-flash", "gemini-3.5-flash"],
        "preferred_nvidia": ["nvidia/llama-3.1-nemotron-70b-instruct"],
        "preferred_groq": ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "qwen/qwen3.6-27b", "groq/compound-mini"],
    }
}


def load_engine_config() -> Dict[str, Any]:
    """Loads and caches the engine configuration from disk."""
    global _CACHED_CONFIG
    with _lock:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with defaults for missing keys
                    merged = dict(DEFAULT_ENGINE_CONFIG)
                    for k in ["limits", "parameters", "models"]:
                        if k in data and isinstance(data[k], dict):
                            merged[k] = {**DEFAULT_ENGINE_CONFIG.get(k, {}), **data[k]}
                    _CACHED_CONFIG = merged
                    return _CACHED_CONFIG
            except Exception as e:
                print(f"[ConfigManager Notice] Error loading engine_config.json: {e}")

        # Fallback to defaults and write to disk
        _CACHED_CONFIG = dict(DEFAULT_ENGINE_CONFIG)
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(_CACHED_CONFIG, f, indent=2)
        except Exception:
            pass
        return _CACHED_CONFIG


def get_engine_config() -> Dict[str, Any]:
    """Returns the cached engine configuration (or loads it if not yet loaded)."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG is None:
        return load_engine_config()
    return _CACHED_CONFIG


def get_token_limit(engine_key: str, default: int = 4096) -> int:
    """Retrieves a specific token limit dynamically (e.g. 'gemini_max_output_tokens')."""
    cfg = get_engine_config()
    limits = cfg.get("limits", {})
    return int(limits.get(engine_key, default))


def get_engine_param(param_key: str, default: Any = None) -> Any:
    """Retrieves an engine parameter dynamically (e.g. 'temperature', 'timeout_sec')."""
    cfg = get_engine_config()
    params = cfg.get("parameters", {})
    return params.get(param_key, default)


def update_token_limit(engine_key: str, new_limit: int) -> bool:
    """Safely updates a token limit on disk with validation (100 <= limit <= 32768)."""
    if not (100 <= new_limit <= 32768):
        return False

    with _lock:
        cfg = get_engine_config()
        if "limits" not in cfg:
            cfg["limits"] = {}
        cfg["limits"][engine_key] = int(new_limit)

        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            return True
        except Exception as e:
            print(f"[ConfigManager Error] Failed to update token limit: {e}")
            return False


def reload_config() -> Dict[str, Any]:
    """Forces an immediate reload from disk."""
    global _CACHED_CONFIG
    _CACHED_CONFIG = None
    return load_engine_config()
