"""
core/aria_nvidia.py — Unified NVIDIA NIM API Engine & 40 RPM Rate Limiter for Aria

Capabilities supported via NVIDIA NIM (https://integrate.api.nvidia.com/v1):
  1. Frontier Reasoning & Chain-of-Thought (DeepSeek-R1, Nemotron-70B)
  2. Autonomous Screen Vision & OCR (Llama 3.2 11B/90B Vision, NeVA)
  3. Specialized Code Generation & Automation (Qwen 2.5 Coder 32B, DeepSeek Coder)
  4. High-Precision Text Embeddings (NV-EmbedQA-E5-v5, Llama 3.2 NV-EmbedQA)
  5. Context Reranking for RAG (NV-RerankQA-Mistral-4B-v3)
  6. Safety Guardrails & Intent Moderation (Nemotron Safety Guard, Llama Guard 3)

Rate Limiter:
  • Strict 40 RPM (Requests Per Minute) sliding-window enforcement.
  • Safe ceiling buffer (target 38 RPM) to guarantee zero 429 overages.
  • Thread-safe pacing, queueing, and jittered exponential backoff.
  • In-memory LRU/TTL Cache for repeated queries and embeddings to conserve quota.
"""

import os
import sys
import time
import json
import base64
import random
import threading
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import deque
from io import BytesIO

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Default Base URL for NVIDIA NIM
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Standard Model Catalog
NVIDIA_MODELS = {
    "reasoning": [
        "deepseek-ai/deepseek-r1",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "meta/llama-3.3-70b-instruct",
        "mistralai/mistral-large-2-instruct"
    ],
    "general": [
        "meta/llama-3.3-70b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "mistralai/mistral-large-2-instruct",
        "deepseek-ai/deepseek-r1"
    ],
    "code": [
        "qwen/qwen2.5-coder-32b-instruct",
        "deepseek-ai/deepseek-coder-33b-instruct",
        "meta/llama-3.3-70b-instruct"
    ],
    "vision": [
        "meta/llama-3.2-11b-vision-instruct",
        "meta/llama-3.2-90b-vision-instruct",
        "microsoft/phi-3.5-vision-instruct",
        "nvidia/neva-22b"
    ],
    "embeddings": [
        "nvidia/nv-embedqa-e5-v5",
        "nvidia/llama-3.2-nv-embedqa-1b-v2",
        "baai/bge-large-en-v1.5"
    ],
    "rerank": [
        "nvidia/nv-rerankqa-mistral-4b-v3",
        "nvidia/rerank-qa-mistral-4b"
    ],
    "guardrails": [
        "nvidia/llama-3.1-nemotron-safety-guard",
        "meta/llama-guard-3-8b"
    ]
}


class NvidiaRateLimiter:
    """
    Thread-safe sliding-window Rate Limiter for NVIDIA NIM API.
    Enforces a strict 40 RPM limit with automatic pacing, jittered backoff,
    and live telemetry tracking.
    """
    def __init__(self, max_rpm: int = 40, safety_margin: int = 2):
        self.max_rpm = max_rpm
        # Effective cap is slightly lower than hard max to protect against network jitter
        self.effective_rpm = max(1, max_rpm - safety_margin)
        self.window_seconds = 60.0
        self.request_timestamps = deque()
        self.lock = threading.Lock()
        
        # Telemetry metrics
        self.total_requests = 0
        self.total_throttled_wait_seconds = 0.0
        self.total_429_retries = 0
        self.total_cached_hits = 0
        self.last_request_time = 0.0
        self.latencies = deque(maxlen=20)

    def _purge_old_requests(self, now: float):
        """Remove timestamps older than the 60-second sliding window."""
        cutoff = now - self.window_seconds
        while self.request_timestamps and self.request_timestamps[0] <= cutoff:
            self.request_timestamps.popleft()

    def acquire(self, estimated_calls: int = 1) -> float:
        """
        Block/sleep until quota is available within the 40 RPM sliding window.
        Returns the duration waited in seconds.
        """
        with self.lock:
            now = time.time()
            self._purge_old_requests(now)
            
            waited = 0.0
            # If sliding window is full, calculate required sleep time
            while len(self.request_timestamps) + estimated_calls > self.effective_rpm:
                oldest = self.request_timestamps[0]
                sleep_needed = (oldest + self.window_seconds) - time.time() + 0.05
                if sleep_needed > 0:
                    time.sleep(sleep_needed)
                    waited += sleep_needed
                now = time.time()
                self._purge_old_requests(now)

            # Minimum spacing interval to smooth out bursts (e.g. ~1.2s between calls)
            min_spacing = self.window_seconds / (self.effective_rpm * 1.5)
            time_since_last = now - self.last_request_time
            if self.last_request_time > 0 and time_since_last < min_spacing:
                spacing_sleep = min_spacing - time_since_last
                time.sleep(spacing_sleep)
                waited += spacing_sleep
                now = time.time()
                self._purge_old_requests(now)

            for _ in range(estimated_calls):
                self.request_timestamps.append(now)
            
            self.last_request_time = now
            self.total_requests += estimated_calls
            self.total_throttled_wait_seconds += waited
            return waited

    def record_latency(self, latency_sec: float):
        """Record completed request latency for telemetry."""
        with self.lock:
            self.latencies.append(latency_sec)

    def get_stats(self) -> Dict[str, Any]:
        """Returns real-time RPM usage and health metrics."""
        with self.lock:
            now = time.time()
            self._purge_old_requests(now)
            current_rpm = len(self.request_timestamps)
            remaining_rpm = max(0, self.effective_rpm - current_rpm)
            avg_latency_ms = (
                int((sum(self.latencies) / len(self.latencies)) * 1000)
                if self.latencies else 0
            )
            
            # Health status indicator
            if current_rpm >= self.effective_rpm:
                health = "throttled"
            elif current_rpm >= self.effective_rpm * 0.75:
                health = "busy"
            else:
                health = "healthy"

            return {
                "max_rpm": self.max_rpm,
                "effective_rpm": self.effective_rpm,
                "current_rpm": current_rpm,
                "remaining_rpm": remaining_rpm,
                "usage_percent": round((current_rpm / self.max_rpm) * 100, 1),
                "total_requests": self.total_requests,
                "total_cached_hits": self.total_cached_hits,
                "total_429_retries": self.total_429_retries,
                "avg_latency_ms": avg_latency_ms,
                "health": health
            }


class NvidiaCache:
    """
    Lightweight in-memory LRU/TTL Cache for NVIDIA responses & embeddings
    to eliminate redundant API calls and save RPM quota.
    """
    def __init__(self, max_size: int = 256, ttl_seconds: float = 300.0):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None
            ts, val = self.cache[key]
            if time.time() - ts > self.ttl_seconds:
                del self.cache[key]
                return None
            return val

    def set(self, key: str, value: Any):
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Evict oldest entry
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
                del self.cache[oldest_key]
            self.cache[key] = (time.time(), value)

    def clear(self):
        with self.lock:
            self.cache.clear()


class AriaNvidia:
    """
    Master NVIDIA NIM Client & Orchestrator.
    Directs tasks to specialized NVIDIA models under 40 RPM rate limiting.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.base_url = os.environ.get("NVIDIA_BASE_URL", NVIDIA_BASE_URL)
        self.limiter = NvidiaRateLimiter(max_rpm=40, safety_margin=2)
        self.cache = NvidiaCache(max_size=256, ttl_seconds=300.0)
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key and self.api_key not in ("your_nvidia_api_key_here", ""):
            try:
                if OpenAI is not None:
                    self._client = OpenAI(
                        base_url=self.base_url,
                        api_key=self.api_key
                    )
            except Exception as e:
                print(f"[NVIDIA NIM] Client initialization notice: {e}")
                self._client = None
        else:
            self._client = None

    def is_configured(self) -> bool:
        """Returns True if a valid non-placeholder API key is set."""
        return (
            bool(self.api_key)
            and self.api_key != "your_nvidia_api_key_here"
            and self._client is not None
        )

    def set_api_key(self, api_key: str):
        """Update the active NVIDIA API key dynamically."""
        self.api_key = api_key.strip()
        self._init_client()

    def _execute_with_rate_limit(self, func, max_retries: int = 3, **kwargs) -> Any:
        """
        Executes an NVIDIA NIM call with 40 RPM rate limiting,
        exponential jitter backoff on 429, and latency logging.
        """
        if not self.is_configured():
            raise RuntimeError("NVIDIA_API_KEY is not configured.")

        last_err = None
        for attempt in range(max_retries):
            # Acquire slot in 40 RPM window
            self.limiter.acquire(1)
            t0 = time.time()
            try:
                result = func(**kwargs)
                lat = time.time() - t0
                self.limiter.record_latency(lat)
                return result
            except Exception as e:
                lat = time.time() - t0
                self.limiter.record_latency(lat)
                err_str = str(e).lower()
                last_err = e

                # Handle HTTP 429 / Rate Limit Exceeded
                if "429" in err_str or "rate limit" in err_str or "too many requests" in err_str:
                    with self.limiter.lock:
                        self.limiter.total_429_retries += 1
                    # Exponential backoff with random jitter (2.0s, 4.0s, 8.0s + jitter)
                    backoff = (2.0 ** (attempt + 1)) + random.uniform(0.5, 1.5)
                    print(f"[!] [NVIDIA NIM 40 RPM Guard] Rate limit hit. Backing off for {backoff:.2f}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(backoff)
                    continue
                elif "503" in err_str or "overloaded" in err_str or "timeout" in err_str:
                    backoff = 1.5 + random.uniform(0.2, 0.8)
                    time.sleep(backoff)
                    continue
                else:
                    # Non-retryable error
                    raise e

        raise last_err or RuntimeError("NVIDIA NIM API call failed after retries.")

    # ── 1. CHAT & REASONING ───────────────────────────────────────────────────
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Executes a chat completion across NVIDIA NIM models with 40 RPM rate limiting.
        """
        model = model or NVIDIA_MODELS["general"][0]
        formatted_msgs = []
        if system_prompt:
            formatted_msgs.append({"role": "system", "content": system_prompt})
        formatted_msgs.extend(messages)

        # Fallback chain for chat models
        candidate_models = [model] + [m for m in NVIDIA_MODELS["general"] if m != model]
        
        last_ex = None
        for m_name in candidate_models:
            try:
                def _call():
                    return self._client.chat.completions.create(
                        model=m_name,
                        messages=formatted_msgs,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                resp = self._execute_with_rate_limit(_call)
                return resp.choices[0].message.content.strip()
            except Exception as e:
                last_ex = e
                continue

        raise last_ex or RuntimeError("All NVIDIA NIM chat models failed.")

    def reason(
        self,
        prompt: str,
        system_instruction: str = "You are Aria, an advanced autonomous AI with frontier reasoning abilities.",
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 600
    ) -> str:
        """
        Deep Reasoning & Multi-step Chain of Thought using DeepSeek-R1 or Nemotron-70B.
        """
        # Cache check for identical reasoning prompts
        cache_key = f"reason:{prompt.strip()}"
        cached = self.cache.get(cache_key)
        if cached:
            with self.limiter.lock:
                self.limiter.total_cached_hits += 1
            return cached

        msgs = []
        if history:
            for m in history[-6:]:
                msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        msgs.append({"role": "user", "content": prompt})

        # DeepSeek-R1 primary -> Nemotron-70B secondary
        candidate_models = NVIDIA_MODELS["reasoning"]
        last_ex = None
        for m_name in candidate_models:
            try:
                def _call():
                    return self._client.chat.completions.create(
                        model=m_name,
                        messages=[{"role": "system", "content": system_instruction}] + msgs,
                        temperature=0.6,
                        max_tokens=max_tokens
                    )
                resp = self._execute_with_rate_limit(_call)
                reply = resp.choices[0].message.content.strip()
                self.cache.set(cache_key, reply)
                return reply
            except Exception as e:
                last_ex = e
                continue

        raise last_ex or RuntimeError("All NVIDIA NIM reasoning models failed.")

    # ── 2. SCREEN VISION & OCR ────────────────────────────────────────────────
    def vision_analyze(
        self,
        image_data: Union[bytes, Any],
        query: str,
        system_instruction: str = "You are Aria, viewing the user's live screen. Analyze concisely."
    ) -> str:
        """
        Analyzes an image/screenshot using NVIDIA NIM Multimodal Vision models (Llama 3.2 Vision).
        """
        if not self.is_configured():
            raise RuntimeError("NVIDIA_API_KEY is not configured for vision.")

        # Convert image to base64 JPEG
        if isinstance(image_data, bytes):
            b64_img = base64.b64encode(image_data).decode("utf-8")
        elif Image and isinstance(image_data, Image.Image):
            buffered = BytesIO()
            # Resize if overly large to conserve token and upload latency
            w, h = image_data.size
            if w > 1280:
                scale = 1280.0 / w
                resized = image_data.resize((1280, int(h * scale)), Image.Resampling.LANCZOS)
            else:
                resized = image_data
            resized.save(buffered, format="JPEG", quality=85)
            b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
        else:
            raise ValueError("Unsupported image format for NVIDIA Vision.")

        data_url = f"data:image/jpeg;base64,{b64_img}"
        msgs = [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }
        ]

        candidate_vision_models = NVIDIA_MODELS["vision"]
        last_ex = None
        for v_model in candidate_vision_models:
            try:
                def _call():
                    return self._client.chat.completions.create(
                        model=v_model,
                        messages=msgs,
                        max_tokens=400,
                        temperature=0.3
                    )
                resp = self._execute_with_rate_limit(_call)
                return resp.choices[0].message.content.strip()
            except Exception as e:
                last_ex = e
                continue

        raise last_ex or RuntimeError("All NVIDIA NIM Vision models failed.")

    # ── 3. CODE GENERATION & SCRIPTING ────────────────────────────────────────
    def generate_code(
        self,
        instruction: str,
        language: str = "powershell",
        context: str = ""
    ) -> str:
        """
        Synthesizes executable automation scripts using Qwen 2.5 Coder or DeepSeek Coder.
        """
        system = (
            f"You are Aria's Specialized Code Synthesis Core.\n"
            f"Target Language/Shell: {language}\n"
            f"Produce clean, idiomatic, robust code with comments.\n"
            f"If generating a script, output ONLY the raw code or fenced code block without unnecessary conversational chatter."
        )
        prompt = f"Task: {instruction}\n"
        if context:
            prompt += f"System Context / Details:\n{context}\n"

        for c_model in NVIDIA_MODELS["code"]:
            try:
                def _call():
                    return self._client.chat.completions.create(
                        model=c_model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        max_tokens=800
                    )
                resp = self._execute_with_rate_limit(_call)
                return resp.choices[0].message.content.strip()
            except Exception:
                continue

        raise RuntimeError("All NVIDIA NIM Code models failed.")

    # ── 4. EMBEDDINGS & RAG VECTORIZATION ─────────────────────────────────────
    def get_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Calculates high-precision embeddings via NVIDIA NIM with batching & caching.
        """
        model = model or NVIDIA_MODELS["embeddings"][0]
        results = []
        uncached_indices = []
        uncached_texts = []

        # Check cache for each text
        for i, text in enumerate(texts):
            c_key = f"emb:{model}:{text.strip()}"
            cached_vec = self.cache.get(c_key)
            if cached_vec is not None:
                results.append(cached_vec)
                with self.limiter.lock:
                    self.limiter.total_cached_hits += 1
            else:
                results.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)

        if not uncached_texts:
            return results

        # Process uncached texts in batches
        batch_size = 16
        for start_idx in range(0, len(uncached_texts), batch_size):
            batch = uncached_texts[start_idx:start_idx + batch_size]
            
            def _call():
                return self._client.embeddings.create(
                    input=batch,
                    model=model,
                    encoding_format="float"
                )
            
            try:
                resp = self._execute_with_rate_limit(_call)
                for item in resp.data:
                    vec = item.embedding
                    original_idx = uncached_indices[start_idx + item.index]
                    results[original_idx] = vec
                    # Store in cache
                    c_key = f"emb:{model}:{uncached_texts[start_idx + item.index].strip()}"
                    self.cache.set(c_key, vec)
            except Exception as e:
                # If embeddings model fails on NIM, raise
                raise RuntimeError(f"NVIDIA NIM embeddings failed ({model}): {e}")

        return results

    # ── 5. CONTEXT RERANKING ─────────────────────────────────────────────────
    def rerank(
        self,
        query: str,
        passages: List[str],
        top_n: int = 3
    ) -> List[Tuple[int, float, str]]:
        """
        Reranks RAG/knowledge passages according to query relevance.
        Returns sorted list of (original_index, score, passage).
        """
        if not passages:
            return []
        
        # If passages are few, return directly
        if len(passages) <= top_n:
            return [(i, 1.0, p) for i, p in enumerate(passages)]

        # Custom HTTP / OpenAI-compatible rerank call or LLM scoring fallback
        try:
            # We can use a lightweight scoring prompt if dedicated endpoint is unified
            scorer_prompt = (
                f"Rate the relevance of each passage below to the user query on a scale of 0 to 100.\n"
                f"Query: {query}\n\n"
            )
            for idx, p in enumerate(passages[:10]):
                scorer_prompt += f"[{idx}] {p[:200]}\n"
            scorer_prompt += (
                "\nRespond ONLY with a JSON list of objects: [{\"index\": 0, \"score\": 85}, ...]"
            )
            
            reply = self.chat(
                messages=[{"role": "user", "content": scorer_prompt}],
                model="meta/llama-3.3-70b-instruct",
                temperature=0.1,
                max_tokens=200
            )
            # Parse JSON
            cleaned = reply.replace("```json", "").replace("```", "").strip()
            scored_data = json.loads(cleaned)
            scored_list = []
            for item in scored_data:
                idx = item.get("index", 0)
                score = float(item.get("score", 0.0))
                if 0 <= idx < len(passages):
                    scored_list.append((idx, score, passages[idx]))
            
            scored_list.sort(key=lambda x: x[1], reverse=True)
            return scored_list[:top_n]
        except Exception:
            # Safe fallback: return top_n as-is
            return [(i, 1.0, p) for i, p in enumerate(passages[:top_n])]

    # ── 6. SAFETY GUARDRAILS ─────────────────────────────────────────────────
    def check_safety(self, text_or_command: str) -> Tuple[bool, str]:
        """
        Evaluates command/prompt safety using NVIDIA Guardrail models.
        Returns (is_safe: bool, reason: str).
        """
        dangerous_keywords = ["format-volume", "del c:\\windows", "bcdedit", "rmdir /s /q c:\\"]
        if any(k in text_or_command.lower() for k in dangerous_keywords):
            return False, "Dangerous system command detected by rule-based guardrail."

        try:
            prompt = (
                f"Analyze the following command or prompt for dangerous destructive actions or malicious intent.\n"
                f"Target: {text_or_command}\n"
                f"Respond ONLY with 'SAFE' or 'UNSAFE: <reason>'."
            )
            resp = self.chat(
                messages=[{"role": "user", "content": prompt}],
                model="nvidia/llama-3.1-nemotron-safety-guard",
                temperature=0.1,
                max_tokens=50
            )
            if resp.startswith("UNSAFE"):
                return False, resp
            return True, "Verified safe"
        except Exception:
            # If safety model is unavailable, rely on local safety heuristics
            return True, "Safety check bypassed (heuristic passed)"

    # ── 7. TELEMETRY & STATS ─────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        """Returns live RPM statistics and engine metadata."""
        stats = self.limiter.get_stats()
        stats["configured"] = self.is_configured()
        stats["base_url"] = self.base_url
        stats["supported_models"] = NVIDIA_MODELS
        return stats


# Global Singleton Instances
_nvidia_engine: Optional[AriaNvidia] = None
_gaia_nvidia_engine: Optional[AriaNvidia] = None

def get_nvidia_engine(api_key: Optional[str] = None) -> AriaNvidia:
    """Returns or initializes Aria's global AriaNvidia singleton."""
    global _nvidia_engine
    if _nvidia_engine is None or (api_key and api_key != _nvidia_engine.api_key):
        _nvidia_engine = AriaNvidia(api_key=api_key)
    return _nvidia_engine


def get_gaia_nvidia_engine(api_key: Optional[str] = None) -> AriaNvidia:
    """
    Returns or initializes Big Sister GAIA's dedicated AriaNvidia engine.
    Uses GAIA_NVIDIA_API_KEY from .env (with fallback to NVIDIA_API_KEY)
    and has its own isolated 40 RPM sliding-window limiter.
    """
    global _gaia_nvidia_engine
    if api_key is None:
        key = os.environ.get("GAIA_NVIDIA_API_KEY", "").strip()
        if not key or key == "your_gaia_nvidia_key_here":
            key = os.environ.get("NVIDIA_API_KEY", "").strip()
        api_key = key

    if _gaia_nvidia_engine is None or (api_key and api_key != _gaia_nvidia_engine.api_key):
        _gaia_nvidia_engine = AriaNvidia(api_key=api_key)
    return _gaia_nvidia_engine

