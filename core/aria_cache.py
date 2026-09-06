"""
core/aria_cache.py — Centralized LRU & TTL Cache Management Engine for Aria & GAIA
Provides:
  • Generic, thread-safe LRUTTLCache with max capacity and time-to-live eviction
  • Telemetry metrics: hits, misses, evictions, and real-time hit ratio
  • Pre-configured namespaces:
      - response_cache: LLM & conversational query responses
      - telemetry_cache: Hardware & OS window context (eliminates high CPU polling)
      - web_cache: DuckDuckGo / web snippets
  • Central CacheManager with inspection, clearing, and pruning endpoints
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict


class LRUTTLCache:
    """
    Thread-safe Least-Recently-Used (LRU) and Time-To-Live (TTL) Cache.
    Bounded capacity prevents memory leaks and RAM bloat.
    """
    def __init__(self, name: str, max_size: int = 256, ttl_seconds: float = 300.0):
        self.name = name
        self.max_size = max(1, max_size)
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            created_at, val = self._cache[key]
            if time.time() - created_at > self.ttl_seconds:
                # Expired
                del self._cache[key]
                self.evictions += 1
                self.misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self.hits += 1
            return val

    def set(self, key: str, value: Any, custom_ttl: Optional[float] = None):
        with self._lock:
            now = time.time()
            if key in self._cache:
                self._cache.move_to_end(key)
                effective_ttl = custom_ttl if custom_ttl is not None else self.ttl_seconds
                self._cache[key] = (now - (self.ttl_seconds - effective_ttl), value)
                return

            if len(self._cache) >= self.max_size:
                # Evict least recently used (first item in OrderedDict)
                self._cache.popitem(last=False)
                self.evictions += 1

            effective_ttl = custom_ttl if custom_ttl is not None else self.ttl_seconds
            self._cache[key] = (now - (self.ttl_seconds - effective_ttl), value)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        with self._lock:
            self._cache.clear()

    def prune_expired(self) -> int:
        """Removes all expired entries and returns the count pruned."""
        with self._lock:
            now = time.time()
            expired_keys = [k for k, (ts, _) in self._cache.items() if now - ts > self.ttl_seconds]
            for k in expired_keys:
                del self._cache[k]
                self.evictions += 1
            return len(expired_keys)

    def stats(self) -> dict:
        with self._lock:
            total_requests = self.hits + self.misses
            hit_ratio = round((self.hits / total_requests) * 100, 1) if total_requests > 0 else 0.0
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "hit_ratio_percent": hit_ratio,
            }


class CacheManager:
    """
    Central Coordinator for all subsystem caches in Aria.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.channels: Dict[str, LRUTTLCache] = {
            "response": LRUTTLCache(name="response", max_size=512, ttl_seconds=300.0),
            "telemetry": LRUTTLCache(name="telemetry", max_size=16, ttl_seconds=2.0),
            "web": LRUTTLCache(name="web", max_size=128, ttl_seconds=600.0),
        }

    def get_channel(self, name: str) -> LRUTTLCache:
        with self._lock:
            if name not in self.channels:
                self.channels[name] = LRUTTLCache(name=name, max_size=256, ttl_seconds=300.0)
            return self.channels[name]

    @property
    def response_cache(self) -> LRUTTLCache:
        return self.get_channel("response")

    @property
    def telemetry_cache(self) -> LRUTTLCache:
        return self.get_channel("telemetry")

    @property
    def web_cache(self) -> LRUTTLCache:
        return self.get_channel("web")

    def clear_all(self):
        with self._lock:
            for ch in self.channels.values():
                ch.clear()

    def get_all_stats(self) -> dict:
        with self._lock:
            channel_stats = {name: ch.stats() for name, ch in self.channels.items()}
            total_hits = sum(ch.hits for ch in self.channels.values())
            total_misses = sum(ch.misses for ch in self.channels.values())
            total_items = sum(len(ch._cache) for ch in self.channels.values())
            total_evictions = sum(ch.evictions for ch in self.channels.values())
            total_reqs = total_hits + total_misses
            overall_hit_ratio = round((total_hits / total_reqs) * 100, 1) if total_reqs > 0 else 0.0
            return {
                "total_items": total_items,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_evictions": total_evictions,
                "overall_hit_ratio_percent": overall_hit_ratio,
                "channels": channel_stats,
            }


# Global Singleton Instance
cache_manager = CacheManager()
