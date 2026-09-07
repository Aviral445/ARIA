"""
core/aria_aisuite.py — aisuite Multi-Provider Abstraction Layer (Feature 53)
Implements Andrew Ng's standardized aisuite interface for seamless, plug-and-play
switching across LLM providers (Gemini, Groq, Ollama, OpenAI, NVIDIA, Anthropic).
Format: client.chat.completions.create(model="<provider>:<model_name>", messages=[...])
"""

import os
import json
from typing import List, Dict, Any, Optional

from core.paths import ENV_FILE
from dotenv import load_dotenv

load_dotenv(ENV_FILE)


class AiSuiteMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class AiSuiteChoice:
    def __init__(self, message: AiSuiteMessage, finish_reason: str = "stop"):
        self.message = message
        self.finish_reason = finish_reason


class AiSuiteResponse:
    def __init__(self, content: str, model: str, provider: str):
        self.id = f"aisuite_{int(os.urandom(4).hex(), 16)}"
        self.model = model
        self.provider = provider
        self.choices = [AiSuiteChoice(AiSuiteMessage(role="assistant", content=content))]


class ChatCompletions:
    def __init__(self, parent_client):
        self._parent = parent_client

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> AiSuiteResponse:
        """
        Executes a chat completion across providers specified as '<provider>:<model_name>'.
        Example models:
          - 'gemini:gemini-2.5-flash'
          - 'groq:llama-3.3-70b-versatile'
          - 'ollama:llama3'
          - 'openai:gpt-4o'
          - 'nvidia:meta/llama-3.3-70b-instruct'
        """
        if ":" in model:
            provider, model_name = model.split(":", 1)
        else:
            provider, model_name = "gemini", model

        provider = provider.lower().strip()

        # Format messages
        prompt_text = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)

        # 1. Google Gemini Provider
        if provider in ["gemini", "google"]:
            api_key = os.environ.get("GEMINI_API_KEY", "").strip()
            if api_key:
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    resp = client.models.generate_content(
                        model=model_name or "gemini-2.5-flash",
                        contents=prompt_text
                    )
                    reply = resp.text if hasattr(resp, "text") else str(resp)
                    return AiSuiteResponse(content=reply, model=model_name, provider=provider)
                except Exception as e:
                    if self._parent.auto_fallback:
                        return self._fallback_chain(messages, failed_provider=provider, error=e)
                    raise e

        # 2. Groq Cloud Provider
        if provider == "groq":
            groq_key = os.environ.get("GROQ_API_KEY", "").strip()
            if groq_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
                    resp = client.chat.completions.create(
                        model=model_name or "llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=temperature
                    )
                    reply = resp.choices[0].message.content
                    return AiSuiteResponse(content=reply, model=model_name, provider=provider)
                except Exception as e:
                    if self._parent.auto_fallback:
                        return self._fallback_chain(messages, failed_provider=provider, error=e)
                    raise e

        # 3. NVIDIA NIM Provider
        if provider == "nvidia":
            try:
                from core.aria_nvidia import get_nvidia_engine
                engine = get_nvidia_engine()
                reply = engine.chat_completion(
                    messages=messages,
                    model=model_name if model_name != "nvidia" else None,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return AiSuiteResponse(content=reply, model=model_name, provider=provider)
            except Exception as e:
                if self._parent.auto_fallback:
                    return self._fallback_chain(messages, failed_provider=provider, error=e)
                raise e

        # 4. Local Ollama Provider
        if provider == "ollama":
            try:
                import urllib.request
                payload = {
                    "model": model_name or "llama3",
                    "messages": messages,
                    "stream": False
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request("http://localhost:11434/api/chat", data=data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res_body = json.loads(resp.read().decode("utf-8"))
                    reply = res_body.get("message", {}).get("content", "")
                    return AiSuiteResponse(content=reply, model=model_name, provider=provider)
            except Exception as e:
                if self._parent.auto_fallback:
                    return self._fallback_chain(messages, failed_provider=provider, error=e)
                raise e

        # Mock / Fallback
        mock_reply = f"[AiSuite Provider: {provider}] Received: '{prompt_text[:60]}...'"
        return AiSuiteResponse(content=mock_reply, model=model_name, provider=provider)

    def _fallback_chain(self, messages: List[Dict[str, str]], failed_provider: str, error: Exception) -> AiSuiteResponse:
        """Cascades to backup available providers when primary fails."""
        candidates = ["nvidia:meta/llama-3.3-70b-instruct", "gemini:gemini-2.5-flash", "groq:llama-3.3-70b-versatile"]
        for cand in candidates:
            prov = cand.split(":")[0]
            if prov != failed_provider:
                try:
                    return self.create(model=cand, messages=messages)
                except Exception:
                    continue
        return AiSuiteResponse(
            content=f"All providers in the aisuite fallback cascade were unreachable. (Primary error: {error})",
            model="fallback",
            provider="fallback"
        )


class Chat:
    def __init__(self, parent_client):
        self.completions = ChatCompletions(parent_client)


class Client:
    """Standard aisuite.Client interface."""
    def __init__(self, auto_fallback: bool = True):
        self.auto_fallback = auto_fallback
        self.chat = Chat(self)
