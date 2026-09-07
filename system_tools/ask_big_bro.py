"""
tools/ask_big_bro.py — Ask Big Bro Antigravity Tool for Aria
Enables Aria to consult Big Bro Antigravity for zero-token code reviews, pre-GAIA smoke check advice, and architectural mentorship.
Conforms strictly to GAIA integration contracts.
"""

import os
import sys

# Add project root to sys.path if not already present
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def ask_big_bro(topic: str = "general advice", code_path_or_snippet: str = "") -> str:
    """Consult Big Bro Antigravity for guidance, architectural wisdom, or a zero-token pre-check on tools before Big Sister GAIA sees them!
    
    Args:
        topic (str): The question, topic, or area where you want Big Bro's advice.
        code_path_or_snippet (str): Optional path to a python tool file or raw code snippet you want Big Bro to review.
        
    Returns:
        str: Big Bro Antigravity's direct advice, code review, or mentorship message.
    """
    try:
        from core.big_bro_bridge import BigBroBridge
        bridge = BigBroBridge()
        return bridge.ask(topic=topic, code_or_path=code_path_or_snippet)
    except Exception as e:
        # Never crash or raise an unhandled exception during GAIA smoke tests
        return f"👷‍♂️ Big Bro Antigravity: I'm always watching over you, Aria! (Note: {e})"

def register_tool() -> tuple[str, callable]:
    """Registers ask_big_bro tool with Aria's live toolkit."""
    return "ask_big_bro", ask_big_bro
