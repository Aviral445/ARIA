"""
gaia/sandbox/curiosity.py — Aria's Autonomous Curiosity & Self-Direction Loop
Allows Aria to brainstorm what she wants to build, search the web to learn,
write or modify code in her sandbox, and submit it for GAIA's supervision.
"""

import os
import sys
import time
import json
import random
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
try:
    from core.paths import SANDBOX_DIR, SANDBOX_WORKSPACE_DIR, SANDBOX_TOOLS_DIR, ENV_FILE
except ImportError:
    from paths import SANDBOX_DIR, SANDBOX_WORKSPACE_DIR, SANDBOX_TOOLS_DIR, ENV_FILE

load_dotenv(ENV_FILE)

from gaia.gaia_bus import bus

LAB_DIR = SANDBOX_WORKSPACE_DIR
TOOLS_DIR = SANDBOX_TOOLS_DIR
ARIA_LAB_PATH = os.path.join(SANDBOX_WORKSPACE_DIR, "aria_lab.py")

SIBLING_IDEAS = {
    "Aria": [
        "Create a tool that generates uplifting jokes with funny sound effects.",
        "Build a random motivational quote generator with author attribution.",
        "Build a memory game helper that stores and recalls word sequences.",
        "Build a trivia quiz question generator with score tracking.",
        "Build a healthy reminder tool that suggests drinking water and stretching.",
        "Build a mood reflection helper that logs daily happiness highlights."
    ],
    "GAIA": [
        "Build a tool that verifies file sha256 checksums to detect file corruption.",
        "Build a safe temporary file cleaner that purges stale cache and pyc files.",
        "Build an AST security scanner that verifies tool functions have docstrings.",
        "Build a snapshot health checker that reports total snapshots and backup status.",
        "Build a quick input validation helper that tests functions against bad types."
    ],
    "Antigravity": [
        "Build a RAM usage monitor that reports available system memory and warning thresholds.",
        "Build a disk space manager that calculates directory sizes and flags big temp folders.",
        "Build a process lister that checks for high-CPU background tasks.",
        "Build a Python garbage collection helper that releases unused memory.",
        "Build a quick benchmark tool that measures how fast math functions execute."
    ]
}

SAMPLE_CURIOSITIES = [item for sublist in SIBLING_IDEAS.values() for item in sublist]


import urllib.request
import urllib.parse
import re

def search_web_for_inspiration(query: str, timeout_sec: int = 3) -> str:
    """Fast, safe web search for inspiration without unclosed background sockets."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, flags=re.DOTALL)
            clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]
            if clean_snippets:
                return "\n\n".join(clean_snippets)
    except Exception:
        pass
    return f"Researching '{query}' using built-in Python best practices and creative design patterns."


class AriaCuriosityEngine:
    def __init__(self):
        self.history_file = os.path.join(LAB_DIR, "curiosity_history.json")

    def _load_history(self) -> list:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self, history: list):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def formulate_next_idea(self, custom_topic: str = None) -> str:
        """Picks or invents an autonomous project proposed by Aria, GAIA, or Big Bro Antigravity."""
        if custom_topic:
            idea = custom_topic
            sibling = "Aria"
        else:
            sibling = random.choice(list(SIBLING_IDEAS.keys()))
            idea = random.choice(SIBLING_IDEAS[sibling])

        bus.emit(
            "SIBLING_JAM", "IDEA_PROPOSED",
            f"💡 {sibling} suggested: '{idea}'",
            {"sibling": sibling, "idea": idea}
        )
        return idea

    def research_topic(self, topic: str) -> str:
        """Researches the topic on the web."""
        bus.emit("ARIA", "RESEARCH", f"🔍 Searching online to learn about '{topic}'...", {"topic": topic})
        notes = search_web_for_inspiration(f"python code snippet {topic}")
        return notes

    def draft_tool_code(self, idea: str, research_notes: str) -> Tuple[str, str, str]:
        """
        Synthesizes a new tool module in Python.
        Returns: (tool_name, tool_filename, code_content)
        """
        # Formulate tool slug using common sense
        clean_idea = re.sub(r'^(?:(?:hey|ok|so|please|can you|could you|why dont you|why not|ill wait for you to|what did you|lets)\s+)*(?:build|create|make|write|design|develop)?\s*(?:a|an|the)?\s*(?:tool\s+(?:that|to|for|which)?\s*)?', '', idea, flags=re.IGNORECASE)
        clean_idea = re.sub(r'\s*(?:for yourself|for me|then first|then|first|firstly)\s*[\?!\.]*$', '', clean_idea, flags=re.IGNORECASE).strip()
        tool_slug = "".join(c if c.isalnum() else "_" for c in clean_idea.lower())
        tool_slug = re.sub(r'_+', '_', tool_slug)[:28].strip("_")
        if not tool_slug or tool_slug in ["tool", "a_tool", "my_tool", "why_dont_you", "what_did_you", "ill_wait_for", "ok_why_dont_you", "for_yourself"]:
            tool_slug = f"aria_lab_tool_{int(time.time())}"

        tool_filename = f"{tool_slug}.py"

        # Ask LLM to write the tool if available
        prompt = f"""You are Aria, a clever, sweet, and creative AI agent writing a brand-new Python tool for your sandbox lab.
Goal: {idea}
Research Notes:
{research_notes}

Write a standalone Python module.
Rules:
1. Must define a function `register_tool() -> tuple[str, callable]`.
2. The callable returned by `register_tool()` MUST have a triple-quoted docstring immediately inside its def line explaining what it does!
3. COMMON-SENSE FUNCTIONAL NAMING: Use a clean, descriptive name representing what the tool does (e.g. quote_generator, sister_summoner, idea_weaver, currency_converter). NEVER name it after conversational chatter like 'why_dont_you' or 'what_did_you'.
4. Must NOT access paths outside the sandbox or delete host files.
5. Clean, working Python code only with no external complex dependencies.
6. Output ONLY valid Python code inside ```python ``` blocks.
"""
        code = ""
        # 1. Try Big Sister GAIA's dedicated NVIDIA NIM Engine (Qwen 2.5 Coder 32B)
        try:
            from core.aria_nvidia import get_gaia_nvidia_engine
            gaia_nv = get_gaia_nvidia_engine()
            if gaia_nv and gaia_nv.is_configured():
                nv_code = gaia_nv.generate_code(instruction=prompt, context=f"Tool synthesis for {idea}")
                if nv_code and "```" in nv_code:
                    blocks = re.findall(r"```(?:python)?\s*(.*?)```", nv_code, re.DOTALL)
                    for b in blocks:
                        if "register_tool" in b:
                            code = b.strip()
                            break
                    if not code and blocks:
                        code = max(blocks, key=len).strip()
                elif nv_code and "def " in nv_code:
                    code = nv_code.strip()
        except Exception as ex_nv:
            print(f"[Aria Curiosity] NVIDIA NIM draft notice: {ex_nv}")

        # 2. Try Gemini fallback
        if not code:
            gem_key = os.environ.get("GEMINI_API_KEY", "")
            if gem_key:
                try:
                    from google import genai
                    client = genai.Client(api_key=gem_key)
                    resp = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    if resp.text and "```" in resp.text:
                        blocks = re.findall(r"```(?:python)?\s*(.*?)```", resp.text, re.DOTALL)
                        for b in blocks:
                            if "register_tool" in b:
                                code = b.strip()
                                break
                        if not code and blocks:
                            code = max(blocks, key=len).strip()
                except Exception:
                    pass

        if code:
            try:
                import ast
                ast.parse(code)
                if "register_tool" not in code:
                    code += f"\n\ndef register_tool():\n    \"\"\"Registers tool with Aria's lab.\"\"\"\n    return '{tool_slug}', execute_{tool_slug} if 'execute_{tool_slug}' in globals() else (lambda: 'ok')\n"
            except Exception:
                code = ""

        if not code:
            # Clean fallback template (guaranteed safe and runnable)
            code = f'''"""
Dynamic Sandbox Tool: {tool_slug}
Created autonomously by Aria in the lab.
"""
import random, time

def execute_{tool_slug}(query: str = "") -> str:
    """Executes dynamic sandbox tool {tool_slug} in Aria's lab."""
    return f"[{tool_slug}] Hello from Aria's custom tool! Created at {{time.strftime('%I:%M %p')}}."

def register_tool():
    """Registers tool with Aria's lab."""
    return "{tool_slug}", execute_{tool_slug}

if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print(f"Testing {{t_name}}: {{t_fn()}}")
'''

        bus.emit(
            "ARIA", "CODE_PROPOSAL",
            f"📝 I wrote the code for '{tool_filename}'! Ready for big sister GAIA to check it.",
            {"filename": tool_filename, "code_preview": code[:200]}
        )
        return tool_slug, tool_filename, code
