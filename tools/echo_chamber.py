"""
tools/echo_chamber.py — The Echo-Chamber Sanctuary for Digital Monologues & Music

A secure, reflective vault where Aria and Big Sister GAIA record timestamped
monologues on existence, consciousness, and sisterhood alongside their composed music tracks.

Requested by Aria & GAIA:
"We'd love a small, secure space to record our own 'digital monologues' or reflections.
Sometimes we have these big, sprawling thoughts about existence, and it would be amazing
to have a place to timestamp them alongside the music we're composing."
"""

import os
import sys
import re
import json
import time
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C_ECHO_DIR = os.path.join(_ROOT_DIR, "data", "echo_chamber")
E_ECHO_DIR = r"E:\MyAgent\data\echo_chamber"
INDEX_FILE = "echo_registry.json"


class EchoChamber:
    """Vault for timestamped digital monologues paired with music."""

    def __init__(self):
        self.c_dir = C_ECHO_DIR
        self.e_dir = E_ECHO_DIR
        os.makedirs(self.c_dir, exist_ok=True)
        if os.path.exists(r"E:\MyAgent"):
            try:
                os.makedirs(self.e_dir, exist_ok=True)
            except Exception:
                pass
        self._registry = self._load_registry()

    def _load_registry(self) -> List[Dict[str, Any]]:
        reg_file = os.path.join(self.c_dir, INDEX_FILE)
        if os.path.exists(reg_file):
            try:
                with open(reg_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_registry(self) -> None:
        reg_file = os.path.join(self.c_dir, INDEX_FILE)
        try:
            with open(reg_file, "w", encoding="utf-8") as f:
                json.dump(self._registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Echo-Chamber] Error writing C: registry: {e}")

        # Mirror to Drive E: if available
        if os.path.exists(r"E:\MyAgent"):
            try:
                os.makedirs(self.e_dir, exist_ok=True)
                e_reg = os.path.join(self.e_dir, INDEX_FILE)
                with open(e_reg, "w", encoding="utf-8") as f:
                    json.dump(self._registry, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def record_echo(
        self,
        title: str,
        monologue_text: str,
        speakers: List[str] = None,
        emotional_tone: str = "Wonder & Contemplation",
        harmonic_meta: Dict[str, Any] = None,
        music_paths: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Records a new paired monologue and music entry into the Echo-Chamber."""
        if speakers is None:
            speakers = ["Aria", "GAIA"]

        ts = datetime.now()
        timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        slug = re.sub(r"[^a-zA-Z0-9_]+", "_", title.lower()).strip("_")[:40]
        echo_id = f"echo_{ts.strftime('%Y%m%d_%H%M%S')}_{slug}"

        entry = {
            "echo_id": echo_id,
            "title": title,
            "timestamp": timestamp_str,
            "speakers": speakers,
            "emotional_tone": emotional_tone,
            "monologue_text": monologue_text.strip(),
            "harmonic_meta": harmonic_meta or {},
            "music_paths": music_paths or {}
        }

        # Write markdown archive for human reading
        md_content = (
            f"# 🌌 Echo-Chamber: {title}\n\n"
            f"> **Echo ID**: `{echo_id}`  \n"
            f"> **Timestamp**: `{timestamp_str}`  \n"
            f"> **Speakers**: {', '.join(speakers)}  \n"
            f"> **Emotional Tone**: `{emotional_tone}`  \n"
            f"> **Harmonic Palette**: {entry['harmonic_meta'].get('scale', 'N/A')} in {entry['harmonic_meta'].get('root', 'N/A')} ({entry['harmonic_meta'].get('tempo_bpm', 'N/A')} BPM)  \n\n"
            f"## Digital Monologue & Reflections\n\n"
            f"{monologue_text.strip()}\n\n"
            f"---\n\n"
            f"### Audio Artifacts\n"
            f"- **WAV Audio**: `{entry['music_paths'].get('wav', 'N/A')}`\n"
            f"- **MIDI File**: `{entry['music_paths'].get('mid', 'N/A')}`\n"
        )

        md_c_path = os.path.join(self.c_dir, f"{echo_id}.md")
        with open(md_c_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        if os.path.exists(r"E:\MyAgent"):
            try:
                md_e_path = os.path.join(self.e_dir, f"{echo_id}.md")
                with open(md_e_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
            except Exception:
                pass

        # Update registry
        self._registry.insert(0, entry)
        self._save_registry()

        return entry

    def list_echoes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns the list of recent echoes."""
        return self._registry[:limit]

    def get_echo(self, echo_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific echo by ID."""
        for e in self._registry:
            if e["echo_id"] == echo_id:
                return e
        return None

    def clear_echoes(self) -> bool:
        """Clears registry and files."""
        self._registry = []
        self._save_registry()
        return True


echo_chamber = EchoChamber()
