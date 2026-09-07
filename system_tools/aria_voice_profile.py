"""
system_tools/aria_voice_profile.py — Custom Voice Profile & Cloning Tool Wrapper (Feature 4)
Exposes aria_voice_profile_tool into Aria's live ADK engine.
"""

from typing import Tuple, Any
from core.aria_voice_clone import aria_voice_profile_tool


def register_tool() -> Tuple[str, Any]:
    """Registers aria_voice_profile_tool with Aria ADK."""
    return ("aria_voice_profile_tool", aria_voice_profile_tool)
