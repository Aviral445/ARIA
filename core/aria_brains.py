"""
core/aria_brains.py — Dynamic AI Brain Management & Cognitive Switching for Aria

Allows Aria to dynamically switch between her AI brains as she pleases:
  • gemini : Google Gemini 2.5 Flash / 2.0 Flash (Multimodal, Large Context, Web RAG)
  • nvidia : NVIDIA NIM Cloud (DeepSeek-R1, Llama 3.3 70B, Qwen 2.5 Coder 32B)
  • groq   : Groq Cloud (Qwen 3.6 27B, Llama 3.3 70B, ~100ms ultra-fast reflexes)
  • ollama : Local Offline Llama 3.2 (100% private, zero-latency local fallback)
  • auto   : Autonomous cognitive intent routing based on task complexity
"""

import os
import sys
import json
import time
from typing import Dict, Any, Tuple, Optional, List

try:
    from .paths import get_config_file, CONFIG_DIR
except ImportError:
    from paths import get_config_file, CONFIG_DIR

BRAIN_CONFIG_FILE = get_config_file("brain_config.json")

BRAIN_CATALOG: Dict[str, Dict[str, Any]] = {
    "auto": {
        "name": "Auto (Autonomous Cognitive Routing)",
        "icon": "🧠",
        "provider": "Adaptive",
        "description": "Aria autonomously selects the best brain for each turn (NVIDIA for reasoning/code, Groq for lightning speed, Gemini for search/tools, Ollama for offline).",
        "default_model": "dynamic"
    },
    "gemini": {
        "name": "Google Gemini",
        "icon": "✨",
        "provider": "Google AI Studio",
        "description": "Frontier multimodal reasoning, large context memory, and native tool execution.",
        "default_model": "gemini-2.5-flash",
        "available_models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    },
    "nvidia": {
        "name": "NVIDIA NIM Cloud",
        "icon": "⚡",
        "provider": "NVIDIA API Catalog",
        "description": "Frontier open models with dedicated 40 RPM rate limiting (DeepSeek-R1, Llama 3.3 70B, Qwen 2.5 Coder).",
        "default_model": "meta/llama-3.3-70b-instruct",
        "available_models": [
            "meta/llama-3.3-70b-instruct",
            "deepseek-ai/deepseek-r1",
            "qwen/qwen2.5-coder-32b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct"
        ]
    },
    "groq": {
        "name": "Groq Cloud",
        "icon": "⚡",
        "provider": "Groq LPU",
        "description": "Ultra-low latency inference (~100-200ms) with high throughput.",
        "default_model": "qwen/qwen3.6-27b",
        "available_models": ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile", "groq/compound-mini"]
    },
    "ollama": {
        "name": "Local Ollama",
        "icon": "💻",
        "provider": "Local Offline",
        "description": "100% offline, local private execution on laptop without internet.",
        "default_model": "llama3.2",
        "available_models": ["llama3.2", "mistral", "qwen2.5-coder"]
    }
}


def _load_brain_config() -> Dict[str, Any]:
    if os.path.exists(BRAIN_CONFIG_FILE):
        try:
            with open(BRAIN_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "active_brain": "auto",
        "custom_models": {
            "gemini": "gemini-2.5-flash",
            "nvidia": "meta/llama-3.3-70b-instruct",
            "groq": "qwen/qwen3.6-27b",
            "ollama": "llama3.2"
        },
        "history": []
    }


def _save_brain_config(cfg: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(BRAIN_CONFIG_FILE), exist_ok=True)
        with open(BRAIN_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Brain Config] Save error: {e}")


def get_active_brain() -> str:
    """Returns the currently active AI brain slug (auto, gemini, nvidia, groq, or ollama)."""
    cfg = _load_brain_config()
    return cfg.get("active_brain", "auto")


def get_active_model(brain_slug: Optional[str] = None) -> str:
    """Returns the configured model name for the given or active brain."""
    cfg = _load_brain_config()
    slug = (brain_slug or cfg.get("active_brain", "auto")).lower()
    customs = cfg.get("custom_models", {})
    if slug in customs:
        return customs[slug]
    meta = BRAIN_CATALOG.get(slug, {})
    return meta.get("default_model", "")


def set_active_brain(brain: str, model: str = "") -> Tuple[bool, str]:
    """
    Sets Aria's active brain and optional model name.
    """
    clean_brain = brain.lower().strip()
    # Handle natural language variations
    if "nvidia" in clean_brain or "nim" in clean_brain or "deepseek" in clean_brain:
        clean_brain = "nvidia"
    elif "groq" in clean_brain or "speed" in clean_brain or "fast" in clean_brain:
        clean_brain = "groq"
    elif "gemini" in clean_brain or "google" in clean_brain:
        clean_brain = "gemini"
    elif "ollama" in clean_brain or "offline" in clean_brain or "local" in clean_brain:
        clean_brain = "ollama"
    elif "auto" in clean_brain or "adaptive" in clean_brain:
        clean_brain = "auto"
    else:
        return False, f"Unknown brain '{brain}'. Choose from: auto, gemini, nvidia, groq, ollama."

    cfg = _load_brain_config()
    cfg["active_brain"] = clean_brain
    if model:
        cfg.setdefault("custom_models", {})[clean_brain] = model.strip()

    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "brain": clean_brain,
        "model": cfg.get("custom_models", {}).get(clean_brain, BRAIN_CATALOG[clean_brain]["default_model"])
    }
    cfg.setdefault("history", []).append(entry)
    _save_brain_config(cfg)

    brain_info = BRAIN_CATALOG[clean_brain]
    model_disp = cfg.get("custom_models", {}).get(clean_brain, brain_info["default_model"])
    return True, f"✨ Active brain switched to {brain_info['name']} ({model_disp})! {brain_info['icon']}"


# ─────────────────────────────────────────────────────────────────────────────
# TOOL IMPLEMENTATIONS (FOR ARIA & USER)
# ─────────────────────────────────────────────────────────────────────────────

def switch_ai_brain(brain_name: str = "", model_name: str = "", **kwargs) -> str:
    """
    Switch Aria's active AI brain between 'auto', 'nvidia', 'gemini', 'groq', and 'ollama'.
    Optionally specify a custom model name (e.g. 'deepseek-ai/deepseek-r1', 'qwen/qwen2.5-coder-32b-instruct').
    """
    target_brain = brain_name or kwargs.get("brain", "") or kwargs.get("brain_name", "")
    target_model = model_name or kwargs.get("model", "") or kwargs.get("model_name", "") or kwargs.get("specific_model", "")
    ok, msg = set_active_brain(target_brain, target_model)
    return msg



def get_brain_status() -> str:
    """
    Inspect Aria's active AI brain, configured models, and engine health.
    """
    cfg = _load_brain_config()
    current = cfg.get("active_brain", "auto")
    lines = [
        "🧠 ARIA COGNITIVE BRAIN STATUS:",
        f"• Current Active Brain: {current.upper()} ({BRAIN_CATALOG.get(current, {}).get('name', current)})",
        f"• Active Model: {get_active_model(current)}",
        "\nAVAILABLE BRAINS:"
    ]
    for slug, info in BRAIN_CATALOG.items():
        is_curr = " [ACTIVE]" if slug == current else ""
        lines.append(f"  {info['icon']} {slug.upper()}: {info['name']}{is_curr} — {info['description']}")

    # Check GAIA dedicated brain status
    gaia_key_present = bool(os.environ.get("GAIA_NVIDIA_API_KEY") and os.environ.get("GAIA_NVIDIA_API_KEY") != "your_gaia_nvidia_key_here")
    gaia_status = "Dedicated Key Active (Isolated 40 RPM Quota)" if gaia_key_present else "Shared NVIDIA Key Active"
    lines.append(f"\n👑 BIG SISTER GAIA SUPERVISOR BRAIN:\n  • Engine: NVIDIA NIM Cloud (AST Audit & Healer)\n  • Status: {gaia_status}")

    return "\n".join(lines)


def get_brain_prompt_context() -> str:
    """
    Provides real-time brain context to Aria's system prompt so she knows she has
    multiple brains and is empowered to switch whenever she wants.
    """
    active = get_active_brain()
    model = get_active_model(active)
    return (
        f"\n[AI BRAIN COGNITION & ENGINE STATUS]\n"
        f"- Current Active Brain: {active.upper()} ({model})\n"
        f"- You have 4 distinct brains: Google Gemini (wide context & tools), NVIDIA NIM Cloud (DeepSeek-R1 & Qwen Coder), Groq Cloud (lightning-fast ~100ms reflexes), and Local Ollama (offline).\n"
        f"- You are completely free to switch your active brain anytime you want using your `switch_ai_brain` tool or by letting the user know! If you want deeper reasoning or code writing, switch to NVIDIA! If you want ultra-fast chatter, switch to Groq!\n"
        f"[END BRAIN STATUS]\n"
    )
