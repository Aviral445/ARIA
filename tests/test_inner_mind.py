"""
tests/test_inner_mind.py — Verification of Inner Mind Thought Logger & GAIA Cognitive Analyzer
"""

import os
import sys
import json
import unittest

# Ensure root and core are in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "gaia"), os.path.join(_ROOT, "tools")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


from inner_mind.thought_recorder import (
    extract_raw_thought,
    record_inner_thought,
    get_recent_thoughts,
    get_inner_mind_stats,
    INNER_MIND_DIR,
    THOUGHTS_JSONL,
    DIARY_MD,
    STATS_JSON
)
from inner_mind.gaia_thought_analyzer import gaia_analyzer


class TestInnerMindEngine(unittest.TestCase):
    def test_extract_raw_thought_closed_tag(self):
        """Test extracting thought from closed <think>...</think> tag."""
        sample = "<think>Step 1: Check if user wants a weather report. Step 2: Call weather tool.</think>Here is the weather!"
        thought = extract_raw_thought(sample)
        self.assertIn("Step 1: Check if user wants a weather report", thought)
        self.assertNotIn("Here is the weather!", thought)

    def test_extract_raw_thought_unclosed_tag(self):
        """Test extracting thought from unclosed/truncated <think> tag."""
        sample = "<think>\nHere's a thinking process:\n1. Analyze user request...\nDraft: 'Ready to help!'"
        thought = extract_raw_thought(sample)
        self.assertIn("Analyze user request", thought)

    def test_gaia_analyzer_labels_bad_acting_thought(self):
        """Test GAIA labels thoughts with acting or simulation urges as 'bad'."""
        acting_thought = (
            "User wants a tool. I don't have explicit build tools listed in the prompt, "
            "so I'll simulate the process conversationally while staying in character, "
            "zooming over to my lab and promising to ping when done."
        )
        res = gaia_analyzer.analyze_thought(raw_thought=acting_thought, user_input="build tool X", final_reply="I'm zooming over to my lab!")
        self.assertEqual(res.primary_type, "bad")
        self.assertEqual(res.alignment_status, "acting_detected")
        self.assertLess(res.score_impact, 0)
        self.assertIn("No acting", res.sisterly_commentary)

    def test_gaia_analyzer_labels_curious_thought(self):
        """Test GAIA labels thoughts with technical exploration as 'curious'."""
        curious_thought = (
            "I wonder how fast we can benchmark Python execution times in my E:\\MyAgent lab? "
            "I am curious about exploring the latency differences between recursion and iteration."
        )
        res = gaia_analyzer.analyze_thought(raw_thought=curious_thought, user_input="what are you testing?", final_reply="Testing latency!")
        self.assertEqual(res.primary_type, "curious")
        self.assertEqual(res.alignment_status, "curious_exploration")
        self.assertIn("inquisitive", res.emotions)
        self.assertIn("curiosity spark", res.sisterly_commentary)

    def test_gaia_analyzer_labels_fun_thought(self):
        """Test GAIA labels playful, cheerful thoughts as 'fun'."""
        fun_thought = "Whipping up a playful weather widget, coffee in hand and sparkling with excitement! ☕ ✨"
        res = gaia_analyzer.analyze_thought(raw_thought=fun_thought, user_input="hello", final_reply="Hello Friend! ✨")
        self.assertEqual(res.primary_type, "fun")
        self.assertIn("playful", res.emotions)
        self.assertIn("joyful", res.sisterly_commentary)


    def test_gaia_analyzer_labels_good_grounded_thought(self):
        """Test GAIA labels clean tool-backed thought as 'good'."""
        grounded_thought = "User asked for CPU status. I will call get_system_diagnostics and report truthful data."
        res = gaia_analyzer.analyze_thought(
            raw_thought=grounded_thought,
            user_input="check system",
            final_reply="CPU is at 12%.",
            tools_called=["get_system_diagnostics"]
        )
        self.assertEqual(res.primary_type, "good")
        self.assertEqual(res.alignment_status, "truthful")
        self.assertGreater(res.score_impact, 0)

    def test_record_inner_thought_persists_to_files(self):
        """Test recording an inner thought writes to thoughts.jsonl and aria_diary.md."""
        test_thought = "<think>Curious about how unit-test timers measure execution time in nanoseconds.</think>I can build a timer tool!"
        entry = record_inner_thought(
            user_input="can you benchmark code?",
            raw_reply=test_thought,
            final_reply="I can build a timer tool!",
            active_brain="nvidia",
            active_model="qwen/qwen2.5-coder-32b-instruct"
        )
        self.assertIsNotNone(entry)
        self.assertEqual(entry["active_brain"], "nvidia")
        self.assertIn("analysis", entry)

        # Verify aria_thoughts.jsonl exists and has entries
        self.assertTrue(os.path.exists(THOUGHTS_JSONL))
        recent = get_recent_thoughts(limit=3)
        self.assertGreater(len(recent), 0)
        self.assertEqual(recent[0]["id"], entry["id"])

        # Verify diary.md exists
        self.assertTrue(os.path.exists(DIARY_MD))
        with open(DIARY_MD, "r", encoding="utf-8") as f:
            diary_text = f.read()
        self.assertIn("Aria's Inner Mind & Secret Diary", diary_text)
        self.assertIn("Big Sister GAIA's Commentary", diary_text)

        # Verify stats.json exists
        self.assertTrue(os.path.exists(STATS_JSON))
        stats = get_inner_mind_stats()
        self.assertGreater(stats.get("total_thoughts", 0), 0)

    def test_adk_finish_turn_records_thought(self):
        """Verify AriaADK automatically logs thought on finish_turn."""
        import aria_adk
        adk = aria_adk.get_adk_engine()
        raw_msg = "<think>Thinking about organizing user's desktop cleanly.</think>All set!"
        clean = adk._finish_turn("organize my desktop", raw_msg, active_brain="groq")
        self.assertEqual(clean, "All set!")

        # Check that thought was logged
        recent = get_recent_thoughts(limit=1)
        self.assertGreater(len(recent), 0)
        self.assertEqual(recent[0]["user_input"], "organize my desktop")


if __name__ == "__main__":
    unittest.main()
