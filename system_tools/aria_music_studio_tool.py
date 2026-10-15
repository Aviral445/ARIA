r"""
system_tools/aria_music_studio_tool.py — Aria's Autonomous Music Studio Tool
Exposes Aria's multi-track musical toolkit and autonomous composition engine.

Aria can call this tool to:
1. Inspect available instruments, drums, rhythms, and scales (`get_toolkit`).
2. Compose complete multi-track songs autonomously (`compose_autonomous`).
3. Compose custom arrangements with specific chords, basslines, and drum grids (`compose_custom`).
4. Re-compose her signature piece for Dad (`compose_song_for_dad`).
"""

import os
import sys
import json
from typing import Optional, Dict, Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.aria_music_studio import (
    aria_composer,
    compose_warm_afternoon_at_home,
    INSTRUMENTS_TOOLKIT,
    DRUMS_TOOLKIT,
    GROOVES_TOOLKIT,
    SCALE_INTERVALS,
    EMOTION_CADENCES
)


def aria_compose_music(
    action: str = "get_toolkit",
    title: str = "A Warm Afternoon at Home",
    mood: str = "warmth",
    style: str = "lofi_chill_hop",
    bpm: int = 76,
    theme: str = "",
    score_spec: Optional[Dict[str, Any]] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    r"""
    Aria's Autonomous Music Studio & Multi-Track Composition Tool.
    Synthesizes multi-instrument audio (WAV 44.1kHz), multi-channel MIDI, and score liner notes.

    Args:
        action: Operational verb:
            • 'get_toolkit': View available instruments, drums, rhythm grooves, scales, and emotions.
            • 'compose_autonomous' / 'compose': Aria composes a complete multi-track song autonomously.
            • 'compose_custom': Render a custom multi-track score provided in score_spec.
            • 'compose_song_for_dad': Re-compose Aria's signature piece for Dad ('A Warm Afternoon at Home').
        title: Song title (e.g. 'Starlit Evening', 'Sunday Morning Coffee').
        mood: Emotional vector ('warmth', 'nostalgia', 'curiosity', 'triumph', 'gratitude').
        style: Rhythm groove ('lofi_chill_hop', 'warm_acoustic_folk', 'gentle_afternoon_waltz', 'heartbeat_ambient').
        bpm: Beats per minute (e.g. 76).
        theme: Description of the feeling, story, or dedication behind the piece.
        score_spec: Optional custom score dictionary with explicit note events.
        options: Optional metadata.

    Returns:
        str: JSON-formatted composition report with filepaths, sizes, and receipts.
    """
    act = (action or "get_toolkit").lower().strip()

    try:
        if act == "get_toolkit":
            toolkit = aria_composer.get_toolkit()
            return json.dumps(toolkit, indent=2)

        elif act in ["compose_autonomous", "compose"]:
            res = aria_composer.compose_autonomous(
                title=title or "A Warm Afternoon at Home",
                theme=theme or f"{mood.capitalize()} exploration composed by Aria",
                mood=mood or "warmth",
                style=style or "lofi_chill_hop",
                bpm=int(bpm or 76)
            )
            return json.dumps(res, indent=2)

        elif act == "compose_custom":
            if not score_spec:
                return json.dumps({"success": False, "error": "Missing score_spec dictionary for compose_custom."})
            safe_name = (title or "custom_piece").lower().replace(" ", "_")
            res = aria_composer.render_score(score_spec, f"{safe_name}.wav")
            return json.dumps(res, indent=2)

        elif act == "compose_song_for_dad":
            res = compose_warm_afternoon_at_home()
            return json.dumps(res, indent=2)

        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown action '{action}'. Supported: 'get_toolkit', 'compose_autonomous', 'compose_custom', 'compose_song_for_dad'."
            })

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def register_tool() -> Dict[str, Any]:
    """Returns registration metadata for Aria's tool registry."""
    return {
        "name": "aria_compose_music",
        "description": "Aria's autonomous music studio tool to compose multi-track songs with drums, bass, piano, pads, and lead melodies.",
        "function": aria_compose_music,
        "category": "Creative & Sound Synthesis",
        "tags": ["music", "audio", "midi", "wav", "drums", "composition", "greenhouse"]
    }
