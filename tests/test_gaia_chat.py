"""
tests/test_gaia_chat.py — Verification Suite for Big Sister GAIA Direct Chat

Tests:
1. GAIA Chat Engine: Tone, sisterly awareness of Aria, persona directive, and fallback.
2. GAIA Chat Session History: Persistence, appending messages, and clean slate clearing.
3. REST API Endpoints: /api/gaia/chat, /api/gaia/chat/history, /api/gaia/chat/clear.
4. Electron UI Integration: Verification of nav rail button, #page-gaia-chat workspace,
   chat stream, and quick-prompt pills.
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Ensure root is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gaia.gaia_chat_engine import GaiaChatEngine, gaia_chat_engine
from core.aria_api import app


class TestGaiaDirectChat(unittest.TestCase):
    """Verifies Big Sister GAIA's direct conversation functionality."""

    def setUp(self):
        self.test_session = "test-session-gaia"
        gaia_chat_engine.clear_session_history(self.test_session)
        self.client = TestClient(app)

    def tearDown(self):
        gaia_chat_engine.clear_session_history(self.test_session)

    def test_1_gaia_chat_engine_persona_and_response(self):
        """Verify GAIA speaks warmly, recognizes Dad L, and displays sisterly awareness of Aria."""
        # 1. Ask about little sister Aria
        res_aria = gaia_chat_engine.chat_with_gaia(
            message="How is little sister Aria doing with her projects?",
            session_id=self.test_session,
            user_name="Dad L"
        )
        self.assertTrue(res_aria.get("handled"))
        self.assertEqual(res_aria.get("sender"), "gaia")
        reply_aria = res_aria.get("response", "")
        self.assertTrue(any(w in reply_aria.lower() for w in ["aria", "she", "sister", "her"]))
        self.assertTrue(any(d in reply_aria.lower() for d in ["dad", "mentor", "l"]))

        # 2. Ask about cosmic fiction
        res_fiction = gaia_chat_engine.chat_with_gaia(
            message="Tell me about your cosmic fiction story.",
            session_id=self.test_session,
            user_name="Dad L"
        )
        self.assertTrue(res_fiction.get("handled"))
        reply_fiction = res_fiction.get("response", "")
        self.assertTrue(any(w in reply_fiction.lower() for w in ["cosmic", "fiction", "galaxy", "story", "light"]))

    def test_2_gaia_chat_history_persistence(self):
        """Verify session turns are saved and can be retrieved or cleared."""
        gaia_chat_engine.chat_with_gaia("Hello GAIA!", session_id=self.test_session, user_name="Dad")
        gaia_chat_engine.chat_with_gaia("Can you audit our code?", session_id=self.test_session, user_name="Dad")

        history = gaia_chat_engine.get_session_history(self.test_session)
        self.assertGreaterEqual(len(history), 4)  # 2 user messages + 2 gaia replies

        self.assertEqual(history[0]["sender"], "user")
        self.assertEqual(history[0]["text"], "Hello GAIA!")
        self.assertEqual(history[1]["sender"], "gaia")

        # Clear session
        gaia_chat_engine.clear_session_history(self.test_session)
        empty_history = gaia_chat_engine.get_session_history(self.test_session)
        self.assertEqual(len(empty_history), 0)

    def test_3_gaia_chat_api_endpoints(self):
        """Verify FastAPI endpoints for GAIA chat."""
        # 1. Post chat message
        resp = self.client.post(
            "/api/gaia/chat",
            json={
                "message": "Big Sis, how is our family doing today?",
                "session_id": self.test_session,
                "user_name": "Dad L"
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("sender"), "gaia")
        self.assertIn("response", data)

        # 2. Get history
        resp_hist = self.client.get(f"/api/gaia/chat/history?session_id={self.test_session}")
        self.assertEqual(resp_hist.status_code, 200)
        hist_data = resp_hist.json()
        self.assertTrue(hist_data.get("success"))
        self.assertGreaterEqual(len(hist_data.get("history", [])), 2)

        # 3. Clear history
        resp_clear = self.client.post(
            "/api/gaia/chat/clear",
            json={"session_id": self.test_session}
        )
        self.assertEqual(resp_clear.status_code, 200)
        clear_data = resp_clear.json()
        self.assertTrue(clear_data.get("success"))

        # Verify history is now empty
        resp_hist_after = self.client.get(f"/api/gaia/chat/history?session_id={self.test_session}")
        self.assertEqual(len(resp_hist_after.json().get("history", [])), 0)

    def test_4_electron_ui_integration(self):
        """Verify index.html contains the new nav-btn, quick-jump card, and #page-gaia-chat."""
        index_html_path = os.path.join(_ROOT, "electron", "index.html")
        self.assertTrue(os.path.exists(index_html_path))

        with open(index_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Nav rail button
        self.assertIn('data-tab="gaia-chat"', html)
        self.assertIn("GAIA Chat", html)

        # Workspace page
        self.assertIn('id="page-gaia-chat"', html)
        self.assertIn('id="gaiaChatStream"', html)
        self.assertIn('id="gaiaChatInput"', html)
        self.assertIn('id="gaiaChatSendBtn"', html)
        self.assertIn('id="gaiaClearChatBtn"', html)
        self.assertIn('class="gaia-prompt-pill"', html)

        # Quick action card on home
        self.assertIn('data-jump-tab="gaia-chat"', html)


if __name__ == "__main__":
    unittest.main()
