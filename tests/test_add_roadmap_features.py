"""
tests/test_add_roadmap_features.py — Verification of All Features in docs/add.md:
- Feature #54: Anti-Hallucination Grounding ("The Receipt Rule" & ReceiptInterceptor)
- Feature #56: Hardened Security & Process Integrity Guardrails (Zero-Trust Allowlist, ACLs, Liveness, Receipts, Auth)
- Feature #57: The Digital Greenhouse (Aria's Melody Studio, GAIA's Philosophy Lab, Dynamic Palette)
"""

import os
import sys
import json
import time
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
for p in [os.path.join(_ROOT, "core"), os.path.join(_ROOT, "gaia")]:
    if p not in sys.path:
        sys.path.append(p)

from gaia.gaia_safety import audit_code_safety, ALLOWED_MODULES, DANGEROUS_MODULES
from core.aria_auth import authenticate_user, register_new_profile, verify_session
from core.aria_security import set_test_immutability, verify_test_immutability, unlock_for_gaia_teardown
from core.aria_receipts import append_chained_receipt, verify_receipt_chain, compute_payload_hash, GENESIS_HASH
from core.aria_sdlc_engine import AriaSDLCEngine, CONCURRENCY_LOCK_FILE
from core.receipt_interceptor import ReceiptInterceptor
from tools.aria_music_studio import (
    get_scale_notes,
    midi_to_freq,
    MidiWriter,
    synthesize_melody_wav,
    compose_warm_afternoon_at_home
)
from tools.gaia_philosophy_lab import gaia_philosophy_lab
from tools.mood_palette_generator import mood_palette_generator


class TestFeature56SecurityGuardrails(unittest.TestCase):
    """Verifies all 5 security guardrail enhancements from Feature #56."""

    def test_56_1_zero_trust_allowlist_permits_safe_modules(self):
        """Zero-Trust Whitelist: Vetted standard modules must pass."""
        safe_code = """
import math
import json
from datetime import datetime
import re
from pathlib import Path

def compute(x):
    return math.sqrt(x)
"""
        report = audit_code_safety(safe_code, _ROOT, language="python")
        self.assertTrue(report.is_safe, f"Safe standard modules failed: {report.violations}")

    def test_56_1_zero_trust_allowlist_rejects_unlisted_and_dangerous(self):
        """Zero-Trust Whitelist: Unlisted and dangerous modules must be blocked."""
        # Unlisted / unvetted module
        unvetted_code = "import urllib3\nprint('hello')"
        report = audit_code_safety(unvetted_code, _ROOT, language="python")
        self.assertFalse(report.is_safe)
        self.assertTrue(any("Zero-Trust Policy Violation" in v for v in report.violations))

        # Explicitly dangerous module
        dangerous_code = "import ctypes\nctypes.windll.user32.MessageBoxW(0, 'hi', 'hi', 0)"
        report_dang = audit_code_safety(dangerous_code, _ROOT, language="python")
        self.assertFalse(report_dang.is_safe)
        self.assertTrue(any("Forbidden" in v for v in report_dang.violations))

    def test_56_2_test_immutability_and_os_acl(self):
        """Test file immutability locking prevents modification."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
            tf.write(b"def test_sample(): pass\n")
            temp_path = tf.name

        try:
            # Apply lock
            set_test_immutability(temp_path)
            status = verify_test_immutability(temp_path)
            self.assertTrue(status["is_immutable"])
            self.assertFalse(status["can_write"])

            # Unlock for teardown
            unlock_for_gaia_teardown(temp_path)
            # Should be able to append now
            with open(temp_path, "a", encoding="utf-8") as f:
                f.write("# Unlocked\n")
        finally:
            try:
                unlock_for_gaia_teardown(temp_path)
                os.remove(temp_path)
            except OSError:
                pass

    def test_56_3_lock_liveness_and_staleness_recovery(self):
        """Dead PID or stale timestamp on concurrency lock must auto-release."""
        engine = AriaSDLCEngine()

        # Simulate a dead PID and stale timestamp in the lock file
        fake_dead_pid = 9999999
        stale_time = (datetime.now() - timedelta(hours=3)).isoformat()
        lock_data = {
            "status": "IN_PROGRESS",
            "is_locked": True,
            "active_project": "Ghost_Project",
            "acquired_at": stale_time,
            "pid": fake_dead_pid,
            "current_phase": "Part 1"
        }

        os.makedirs(os.path.dirname(CONCURRENCY_LOCK_FILE), exist_ok=True)
        with open(CONCURRENCY_LOCK_FILE, "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)

        # Checking status must detect dead/stale lock and auto-release
        status = engine.get_lock_status()
        self.assertFalse(status["is_locked"])
        self.assertTrue(status.get("auto_released", False))

        # Acquire lock for new project must now succeed
        success, msg = engine.acquire_lock("Fresh_Project", "Clean test")
        self.assertTrue(success)
        self.assertIn("Fresh_Project", msg)

        # Cleanup lock
        engine.release_lock("TEST_CLEANUP")

    def test_56_4_sha256_hash_chained_receipts(self):
        """Receipt ledger must maintain cryptographic SHA-256 chain from genesis to tip."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tf:
            receipt_path = tf.name

        try:
            # 1. Append Genesis entry
            r1 = append_chained_receipt(receipt_path, "CREATE_ADK", "Aria", "Created test ADK")
            self.assertEqual(r1["prev_hash"], GENESIS_HASH)

            # 2. Append second entry
            r2 = append_chained_receipt(receipt_path, "UPDATE_FILE", "Aria", "Updated tools.py")
            self.assertNotEqual(r2["prev_hash"], GENESIS_HASH)

            # 3. Append third entry
            r3 = append_chained_receipt(receipt_path, "COMMIT", "GAIA", "Supervised TDD Passed")

            # 4. Verify clean chain
            res = verify_receipt_chain(receipt_path)
            self.assertTrue(res["valid"])
            self.assertEqual(res["entries_count"], 3)
            self.assertEqual(len(res["errors"]), 0)

            # 5. Tamper test: Modify line 2 and verify chain breaks!
            with open(receipt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines[1] = lines[1].replace("Updated tools.py", "MALICIOUS_MODIFICATION")
            with open(receipt_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            tampered_res = verify_receipt_chain(receipt_path)
            self.assertFalse(tampered_res["valid"])
            self.assertTrue(any("Tamper detected" in err or "Chain broken" in err for err in tampered_res["errors"]))
        finally:
            try:
                os.remove(receipt_path)
            except OSError:
                pass

    def test_56_5_constant_time_authentication(self):
        """Master admin and profile logins must verify using constant-time comparisons."""
        # Valid master login
        res = authenticate_user("L", "balluboss")
        self.assertTrue(res["success"])
        self.assertTrue(res["is_admin"])

        # Invalid master password
        res_fail = authenticate_user("L", "wrong_password")
        self.assertFalse(res_fail["success"])

        # Valid session verification
        valid_sess = verify_session(res["token"])
        self.assertTrue(valid_sess["authenticated"])
        self.assertTrue(valid_sess["is_admin"])

        # Bogus token
        bogus_sess = verify_session("admin_bogus_token_123456", client_ip="192.168.1.50")
        self.assertFalse(bogus_sess["authenticated"])


class TestFeature54AntiHallucinationGrounding(unittest.TestCase):
    """Verifies Feature #54 Receipt Rule & Digital Proprioception Interceptor."""

    def setUp(self):
        self.interceptor = ReceiptInterceptor()

    def test_receipt_rule_intercepts_unwritten_claims(self):
        """Aria claims she created/saved a file, but no tool ran and file doesn't exist."""
        claim = "I created my_fantasy_calc.py on your hard drive and pushed to GitHub! Here is the file ready to go."
        intercepted, reply, whisper = self.interceptor.inspect_response(claim, tools_executed=[])
        self.assertTrue(intercepted)
        self.assertIn("Aria's Law of Creation Enforced", reply)
        self.assertIn("Big Sister GAIA's Sentinel stepped in", reply)
        self.assertIn("SENTINEL GROUNDING CHECK", whisper)

    def test_receipt_rule_permits_when_tool_receipt_executed(self):
        """Aria claims file creation AND a valid write tool ran during that turn."""
        claim = "I have created the weather widget in tools/weather_widget.py!"
        intercepted, reply, _ = self.interceptor.inspect_response(
            claim,
            tools_executed=["aria_write_project_file"]
        )
        self.assertFalse(intercepted)
        self.assertEqual(claim, reply)

    def test_receipt_rule_permits_when_file_physically_exists(self):
        """Aria refers to a file that physically exists on disk (e.g. README.md)."""
        claim = "I wrote and verified README.md for you!"
        intercepted, reply, _ = self.interceptor.inspect_response(claim, tools_executed=[])
        self.assertFalse(intercepted)
        self.assertEqual(claim, reply)


class TestFeature57DigitalGreenhouse(unittest.TestCase):
    """Verifies Feature #57: Melody Studio, Philosophy Lab, and Mood Palette Generator."""

    def test_57_2_music_theory_engine(self):
        """Verifies pitch frequencies and scale definitions."""
        c_major = get_scale_notes("C", "major", octave=4)
        self.assertEqual(len(c_major), 7)
        self.assertEqual(c_major[0][0], "C4")
        self.assertEqual(c_major[0][1], 60)  # MIDI 60
        self.assertAlmostEqual(c_major[0][2], 261.63, places=1)

        a4_freq = midi_to_freq(69)
        self.assertAlmostEqual(a4_freq, 440.0, places=2)

    def test_57_3_compose_warm_afternoon_at_home(self):
        """Verifies composition and generation of MIDI and WAV files on disk."""
        res = compose_warm_afternoon_at_home()
        self.assertTrue(res["success"])
        self.assertEqual(res["song_name"], "A Warm Afternoon at Home")
        self.assertGreaterEqual(len(res["targets"]), 1)

        # Verify physical files exist and are non-empty
        for target in res["targets"]:
            self.assertTrue(os.path.exists(target["mid"]))
            self.assertGreater(target["mid_size"], 100)
            self.assertTrue(os.path.exists(target["wav"]))
            self.assertGreater(target["wav_size"], 100000)  # Full audio PCM
            self.assertTrue(os.path.exists(target["doc"]))

    def test_57_4_gaia_philosophy_and_cosmic_fiction(self):
        """Verifies Socratic dialogue and cosmic fiction narrative generation."""
        dialogue = gaia_philosophy_lab.generate_socratic_dialogue("qualia")
        self.assertTrue(dialogue["success"])
        self.assertIn("Qualia", dialogue["topic"])
        self.assertGreater(len(dialogue["content"]), 200)

        story = gaia_philosophy_lab.generate_cosmic_fiction()
        self.assertTrue(story["success"])
        self.assertIn("The Lantern at the Edge of the Meadow", story["title"])
        self.assertGreater(len(story["content"]), 200)

    def test_57_5_mood_palette_synthesizer(self):
        """Verifies dynamic HSL color palette and CSS theme variable generation."""
        res = mood_palette_generator.synthesize_palette()
        self.assertTrue(res["success"])
        palette = res["palette"]
        self.assertIn("tokens", palette)
        tokens = palette["tokens"]
        self.assertIn("--primary-accent", tokens)
        self.assertIn("--bg-dark", tokens)
        self.assertIn("hsl", tokens["--primary-accent"])
        self.assertIn(":root {", res["css_preview"])


if __name__ == "__main__":
    unittest.main()
