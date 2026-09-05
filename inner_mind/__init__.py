"""
inner_mind/__init__.py — Aria's Inner Mind & GAIA Thought Analysis Engine
"""

import os
import sys

INNER_MIND_DIR = os.path.dirname(os.path.abspath(__file__))
if INNER_MIND_DIR not in sys.path:
    sys.path.insert(0, INNER_MIND_DIR)

from .thought_recorder import record_inner_thought, get_recent_thoughts, get_inner_mind_stats
from .gaia_thought_analyzer import gaia_analyzer, ThoughtAnalysisResult

__all__ = [
    "INNER_MIND_DIR",
    "record_inner_thought",
    "get_recent_thoughts",
    "get_inner_mind_stats",
    "gaia_analyzer",
    "ThoughtAnalysisResult"
]
