"""
tests/test_brain_switching.py — Unit Tests for Aria's Brain Switching & GAIA's Dedicated NVIDIA NIM Key
"""

import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# Ensure root is in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "gaia"), os.path.join(_ROOT, "tools")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.aria_brains import (
    BRAIN_CATALOG,
    get_active_brain,
    set_active_brain,
    get_active_model,
    switch_ai_brain,
    get_brain_status,
    get_brain_prompt_context
)
from core.aria_nvidia import get_nvidia_engine, get_gaia_nvidia_engine, AriaNvidia


class TestBrainManagement(unittest.TestCase):
    def setUp(self):
        # Save original brain config if needed
        self.original_brain, self.original_model = get_active_brain(), get_active_model()

    def tearDown(self):
        # Restore original state
        set_active_brain(self.original_brain, self.original_model)

    def test_catalog_structure(self):
        """Ensure all required brains exist in catalog."""
        expected_brains = ["auto", "gemini", "nvidia", "groq", "ollama"]
        for b in expected_brains:
            self.assertIn(b, BRAIN_CATALOG)
            self.assertIn("name", BRAIN_CATALOG[b])
            self.assertIn("description", BRAIN_CATALOG[b])

    def test_set_and_get_active_brain(self):
        """Test switching active brain persists to config."""
        success, msg = set_active_brain("nvidia", "deepseek-ai/deepseek-r1")
        self.assertTrue(success)
        self.assertEqual(get_active_brain(), "nvidia")
        self.assertEqual(get_active_model("nvidia"), "deepseek-ai/deepseek-r1")

        # Test switching to groq
        success, msg = set_active_brain("groq")
        self.assertTrue(success)
        self.assertEqual(get_active_brain(), "groq")
        self.assertEqual(get_active_model("groq"), BRAIN_CATALOG["groq"]["default_model"])

        # Test switching back to auto
        success, msg = set_active_brain("auto")
        self.assertTrue(success)
        self.assertEqual(get_active_brain(), "auto")

    def test_invalid_brain_switch(self):
        """Test switching to non-existent brain is rejected gracefully."""
        success, msg = set_active_brain("quantum_supercomputer")
        self.assertFalse(success)
        self.assertIn("Unknown brain", msg)

    def test_switch_ai_brain_tool_function(self):
        """Test the user-facing/agent-facing switch_ai_brain function."""
        res = switch_ai_brain("nvidia", model="meta/llama-3.3-70b-instruct")
        self.assertIn("Active brain switched to", res)
        self.assertEqual(get_active_brain(), "nvidia")

    def test_get_brain_status(self):
        """Test brain status report formatting."""
        status = get_brain_status()
        self.assertIsInstance(status, str)
        self.assertIn("ARIA COGNITIVE BRAIN STATUS", status)
        self.assertIn("Current Active Brain:", status)
        self.assertIn("NVIDIA NIM Cloud", status)
        self.assertIn("Google Gemini", status)
        self.assertIn("Groq Cloud", status)
        self.assertIn("BIG SISTER GAIA", status)

    def test_brain_prompt_context(self):
        """Test prompt context injected into Aria's system instruction."""
        set_active_brain("nvidia")
        ctx = get_brain_prompt_context()
        self.assertIn("AI BRAIN COGNITION & ENGINE STATUS", ctx)
        self.assertIn("NVIDIA", ctx)


class TestGaiaDedicatedNvidiaKey(unittest.TestCase):
    def test_gaia_nvidia_engine_isolation(self):
        """Verify GAIA has her own dedicated AriaNvidia instance and rate limiter."""
        aria_engine = get_nvidia_engine()
        gaia_engine = get_gaia_nvidia_engine()

        # Both should be AriaNvidia instances
        self.assertIsInstance(aria_engine, AriaNvidia)
        self.assertIsInstance(gaia_engine, AriaNvidia)

        # They must have separate rate limiter instances so GAIA doesn't deplete Aria's quota
        self.assertIsNot(aria_engine.limiter, gaia_engine.limiter)

        # Check GAIA rate limiter starts healthy
        stats = gaia_engine.limiter.get_stats()
        self.assertEqual(stats["max_rpm"], 40)
        self.assertEqual(stats["health"], "healthy")

    def test_gaia_engine_uses_dedicated_key_or_fallback(self):
        """Verify get_gaia_nvidia_engine respects GAIA_NVIDIA_API_KEY environment variable."""
        with patch.dict(os.environ, {"GAIA_NVIDIA_API_KEY": "test_dedicated_key_gaia_123"}):
            test_engine = get_gaia_nvidia_engine(api_key=None)
            self.assertEqual(test_engine.api_key, "test_dedicated_key_gaia_123")

        # Fallback to NVIDIA_API_KEY when GAIA_NVIDIA_API_KEY is placeholder or empty
        with patch.dict(os.environ, {"GAIA_NVIDIA_API_KEY": "your_gaia_nvidia_key_here", "NVIDIA_API_KEY": "nvapi_fallback_key_456"}):
            fallback_engine = get_gaia_nvidia_engine(api_key=None)
            self.assertEqual(fallback_engine.api_key, "nvapi_fallback_key_456")


class TestAdkTierPriority(unittest.TestCase):
    def test_tier_prioritization_nvidia(self):
        """Ensure AriaADK tier ordering prioritizes active brain."""
        import aria_adk
        adk = aria_adk.get_adk_engine()
        self.assertIsNotNone(adk)

        # Set brain to nvidia
        set_active_brain("nvidia")
        active = get_active_brain()
        self.assertEqual(active, "nvidia")

        # Test prompt context
        ctx = get_brain_prompt_context()
        self.assertIn("NVIDIA", ctx)

    def test_tier_prioritization_groq(self):
        """Ensure AriaADK tier ordering prioritizes groq when active."""
        set_active_brain("groq")
        self.assertEqual(get_active_brain(), "groq")



if __name__ == "__main__":
    unittest.main()
