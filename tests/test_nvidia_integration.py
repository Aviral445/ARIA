"""
tests/test_nvidia_integration.py — Unit & Integration Tests for NVIDIA NIM Suite & 40 RPM Rate Limiter
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure root and subfolders are on sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "server"), os.path.join(_ROOT, "gui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.aria_nvidia import NvidiaRateLimiter, NvidiaCache, AriaNvidia, get_nvidia_engine, NVIDIA_MODELS


class TestNvidiaRateLimiter(unittest.TestCase):
    def test_rate_limiter_initialization(self):
        """Test rate limiter bounds and defaults."""
        limiter = NvidiaRateLimiter(max_rpm=40, safety_margin=2)
        self.assertEqual(limiter.max_rpm, 40)
        self.assertEqual(limiter.effective_rpm, 38)
        stats = limiter.get_stats()
        self.assertEqual(stats["max_rpm"], 40)
        self.assertEqual(stats["current_rpm"], 0)
        self.assertEqual(stats["remaining_rpm"], 38)
        self.assertEqual(stats["health"], "healthy")

    def test_rate_limiter_acquire_and_stats(self):
        """Test acquire adds timestamps and updates stats."""
        limiter = NvidiaRateLimiter(max_rpm=40, safety_margin=2)
        waited = limiter.acquire(1)
        self.assertEqual(limiter.total_requests, 1)
        stats = limiter.get_stats()
        self.assertEqual(stats["current_rpm"], 1)
        self.assertEqual(stats["remaining_rpm"], 37)
        self.assertGreater(stats["usage_percent"], 0)

    def test_rate_limiter_sliding_window_purge(self):
        """Test that timestamps older than 60s are purged."""
        limiter = NvidiaRateLimiter(max_rpm=40, safety_margin=2)
        old_time = time.time() - 70.0
        limiter.request_timestamps.append(old_time)
        self.assertEqual(len(limiter.request_timestamps), 1)
        limiter._purge_old_requests(time.time())
        self.assertEqual(len(limiter.request_timestamps), 0)


class TestNvidiaCache(unittest.TestCase):
    def test_cache_set_and_get(self):
        """Test basic caching behavior."""
        cache = NvidiaCache(max_size=10, ttl_seconds=60.0)
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        self.assertIsNone(cache.get("key_nonexistent"))

    def test_cache_ttl_expiry(self):
        """Test TTL expiration."""
        cache = NvidiaCache(max_size=10, ttl_seconds=0.1)
        cache.set("key_temp", "temp_val")
        self.assertEqual(cache.get("key_temp"), "temp_val")
        time.sleep(0.15)
        self.assertIsNone(cache.get("key_temp"))

    def test_cache_lru_eviction(self):
        """Test eviction of oldest items when max_size is reached."""
        cache = NvidiaCache(max_size=3, ttl_seconds=60.0)
        cache.set("a", 1)
        time.sleep(0.01)
        cache.set("b", 2)
        time.sleep(0.01)
        cache.set("c", 3)
        time.sleep(0.01)
        cache.set("d", 4)  # Should evict "a"
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("d"), 4)


class TestAriaNvidiaEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AriaNvidia(api_key="nvapi-mock-key")

    def test_models_catalog(self):
        """Verify model catalog integrity."""
        self.assertIn("reasoning", NVIDIA_MODELS)
        self.assertIn("vision", NVIDIA_MODELS)
        self.assertIn("code", NVIDIA_MODELS)
        self.assertIn("embeddings", NVIDIA_MODELS)
        self.assertIn("deepseek-ai/deepseek-r1", NVIDIA_MODELS["reasoning"])
        self.assertIn("qwen/qwen2.5-coder-32b-instruct", NVIDIA_MODELS["code"])
        self.assertIn("meta/llama-3.2-11b-vision-instruct", NVIDIA_MODELS["vision"])

    def test_engine_stats_telemetry(self):
        """Test stats reporting for GUI and API server."""
        stats = self.engine.get_stats()
        self.assertIn("max_rpm", stats)
        self.assertIn("current_rpm", stats)
        self.assertIn("health", stats)
        self.assertIn("supported_models", stats)
        self.assertEqual(stats["max_rpm"], 40)

    @patch("core.aria_nvidia.OpenAI")
    def test_rate_limited_retry_on_429(self, mock_openai_cls):
        """Test that HTTP 429 triggers exponential backoff retry."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        
        engine = AriaNvidia(api_key="nvapi-test-key")
        engine._client = mock_client

        # Mock function that fails once with 429 then succeeds
        call_count = [0]
        def _mock_call(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Error code: 429 - rate limit exceeded")
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock(message=MagicMock(content="Success after retry"))]
            return mock_resp

        result = engine._execute_with_rate_limit(_mock_call, max_retries=2)
        self.assertEqual(call_count[0], 2)
        self.assertEqual(result.choices[0].message.content, "Success after retry")
        self.assertEqual(engine.limiter.total_429_retries, 1)

    def test_safety_check_heuristics(self):
        """Test rule-based command safety blocking."""
        is_safe, reason = self.engine.check_safety("format-volume C:")
        self.assertFalse(is_safe)
        self.assertIn("Dangerous", reason)


if __name__ == "__main__":
    unittest.main()
