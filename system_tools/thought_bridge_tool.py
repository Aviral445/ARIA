"""
system_tools/thought_bridge_tool.py — System Tool exposing The Thought-Bridge
"""

import os
import sys
import json
from typing import Dict, Any

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from tools.thought_bridge import thought_bridge


def thought_bridge_tool(
    action: str = "map",
    text: str = "",
    theme: str = ""
) -> str:
    """Translates philosophical concepts and reflections into musical harmony parameters.
    
    Args:
        action (str): 'map' to analyze text, 'recommend' for a theme name, 'catalog' to view all mappings.
        text (str): Philosophical or reflective text to analyze.
        theme (str): Specific theme name (e.g. 'cosmic_expansion', 'sisterly_joy').
    """
    act = action.lower().strip()
    if act == "recommend":
        res = thought_bridge.recommend_progression_for_theme(theme or text)
        return json.dumps(res, indent=2)
    elif act == "catalog":
        res = thought_bridge.get_harmonic_library()
        return json.dumps(res, indent=2)
    else:
        res = thought_bridge.map_thought_to_harmonic_profile(text or theme or "cosmic expansion")
        return json.dumps(res, indent=2)


def register_tool() -> tuple[str, callable]:
    return "thought_bridge_tool", thought_bridge_tool
