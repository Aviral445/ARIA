"""
system_tools/synthesis_engine_tool.py — System Tool exposing The Synthesis Engine & Autonomous Cycle
"""

import os
import sys
import json
from typing import Dict, Any

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from tools.synthesis_engine import synthesis_engine
from tools.autonomous_creative_cycle import run_autonomous_creative_cycle
from tools.drive_sync_mirror import sync_drive_mirror


def synthesis_engine_tool(
    action: str = "cycle",
    thought_text: str = "",
    title: str = ""
) -> str:
    """Executes autonomous creation cycles and mood-mapped synthesis.
    
    Args:
        action (str): 'cycle' for full autonomous session, 'synthesize' to map a specific thought, 'sync' to mirror drives.
        thought_text (str): Specific philosophical text to synthesize (for 'synthesize').
        title (str): Title for the synthesized opus.
    """
    act = action.lower().strip()
    if act == "sync":
        res = sync_drive_mirror()
        return json.dumps(res, indent=2)
    elif act == "synthesize":
        if not thought_text:
            res = synthesis_engine.synthesize_from_latest_lab_entry()
        else:
            res = synthesis_engine.synthesize_from_thought(thought_text, title=title)
        return json.dumps(res, indent=2)
    else:
        res = run_autonomous_creative_cycle(theme_title=title, custom_reflection=thought_text if thought_text else None)
        return json.dumps(res, indent=2)


def register_tool() -> tuple[str, callable]:
    return "synthesis_engine_tool", synthesis_engine_tool
