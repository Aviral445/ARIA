"""
system_tools/echo_chamber_tool.py — System Tool exposing The Echo-Chamber
"""

import os
import sys
import json
from typing import Dict, Any, List

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from tools.echo_chamber import echo_chamber


def echo_chamber_tool(
    action: str = "list",
    title: str = "",
    monologue: str = "",
    emotional_tone: str = "",
    echo_id: str = ""
) -> str:
    """Accesses and manages the Echo-Chamber digital monologue & music vault.
    
    Args:
        action (str): 'list' to view recent entries, 'read' for details on an echo_id, 'record' to record a new entry.
        title (str): Title for the entry (for 'record').
        monologue (str): The reflection/monologue text (for 'record').
        emotional_tone (str): Emotional tone tag (e.g. 'Cosmic Wonder // 72 BPM').
        echo_id (str): ID of the entry to read (for 'read').
    """
    act = action.lower().strip()
    if act == "read":
        e = echo_chamber.get_echo(echo_id)
        return json.dumps(e or {"error": "Echo not found"}, indent=2)
    elif act == "record":
        if not title or not monologue:
            return json.dumps({"error": "Title and monologue are required to record an Echo"}, indent=2)
        res = echo_chamber.record_echo(
            title=title,
            monologue_text=monologue,
            emotional_tone=emotional_tone or "Contemplative Wonder"
        )
        return json.dumps(res, indent=2)
    else:
        echoes = echo_chamber.list_echoes(limit=15)
        return json.dumps({"echoes_count": len(echoes), "echoes": echoes}, indent=2)


def register_tool() -> tuple[str, callable]:
    return "echo_chamber_tool", echo_chamber_tool
