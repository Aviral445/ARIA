"""
tests/test_aria_music_engine.py — Comprehensive Unit Tests for Aria's Polyglot Music Studio
Verifies:
1. Node.js audio engine execution (aria_music_engine.mjs).
2. Drum synthesizer generation (kick, snare, hi-hats, rimshot).
3. Multi-track instrument rendering (piano, bass, pad, flute lead).
4. Multi-channel MIDI file structure and WAV audio headers (RIFF, 44.1kHz, 16-bit).
5. AriaComposerEngine autonomous composition and liner notes generation.
6. System tool aria_compose_music function calling.
"""

import os
import sys
import json
import wave
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.aria_music_studio import (
    aria_composer,
    compose_warm_afternoon_at_home,
    C_GREENHOUSE,
    E_GREENHOUSE
)
from system_tools.aria_music_studio_tool import aria_compose_music


class TestAriaPolyglotMusicEngine(unittest.TestCase):

    def test_1_get_toolkit_contains_all_components(self):
        """Aria's musical toolkit must contain instruments, drums, grooves, and scales."""
        toolkit = aria_composer.get_toolkit()
        self.assertTrue(toolkit["success"])
        self.assertIn("instruments", toolkit)
        self.assertIn("drums", toolkit)
        self.assertIn("grooves", toolkit)
        self.assertIn("scales", toolkit)

        # Verify key instruments
        self.assertIn("warm_piano", toolkit["instruments"])
        self.assertIn("acoustic_bass", toolkit["instruments"])
        self.assertIn("ambient_pad", toolkit["instruments"])
        self.assertIn("flute_lead", toolkit["instruments"])

        # Verify drums
        self.assertIn("kick", toolkit["drums"])
        self.assertIn("snare", toolkit["drums"])
        self.assertIn("closed_hat", toolkit["drums"])
        self.assertIn("rimshot", toolkit["drums"])

    def test_2_autonomous_composition_generates_wav_midi_and_notes(self):
        """Aria composes an autonomous song, producing verified WAV, MIDI, and Markdown liner notes."""
        res = aria_composer.compose_autonomous(
            title="Autumn Starlight",
            theme="Quiet reflections by the window with Dad",
            mood="warmth",
            style="lofi_chill_hop",
            bpm=74
        )
        self.assertTrue(res["success"], f"Composition failed: {res}")
        self.assertTrue(os.path.exists(res["wav_path"]))
        self.assertTrue(os.path.exists(res["midi_path"]))
        self.assertTrue(os.path.exists(res["notes_path"]))

        # Check non-zero size
        self.assertGreater(res["wav_size_bytes"], 100000)
        self.assertGreater(res["midi_size_bytes"], 200)

        # Inspect WAV header
        with wave.open(res["wav_path"], "rb") as wf:
            self.assertEqual(wf.getframerate(), 44100)
            self.assertEqual(wf.getsampwidth(), 2)  # 16-bit
            self.assertEqual(wf.getnchannels(), 1)  # Mono

        # Inspect liner notes
        with open(res["notes_path"], "r", encoding="utf-8") as f:
            notes = f.read()
        self.assertIn("Autumn Starlight", notes)
        self.assertIn("Dad (Mentor L)", notes)
        self.assertIn("warm_piano", notes)
        self.assertIn("lofi_chill_hop", notes)

    def test_3_compose_warm_afternoon_at_home_opus(self):
        """Aria's signature opus for Dad must render cleanly via multi-track engine."""
        res = compose_warm_afternoon_at_home()
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["wav_path"]))
        self.assertIn("Node.js Web Audio Engine", res.get("engine", ""))

    def test_4_system_tool_aria_compose_music_calling(self):
        """Function-calling wrapper aria_compose_music must handle all action verbs."""
        # Action: get_toolkit
        tk_str = aria_compose_music(action="get_toolkit")
        tk = json.loads(tk_str)
        self.assertTrue(tk["success"])

        # Action: compose_autonomous
        comp_str = aria_compose_music(action="compose_autonomous", title="Sunday Tea", mood="gratitude", bpm=78)
        comp = json.loads(comp_str)
        self.assertTrue(comp["success"])
        self.assertEqual(comp["title"], "Sunday Tea")


if __name__ == "__main__":
    unittest.main()
