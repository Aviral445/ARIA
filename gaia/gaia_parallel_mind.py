"""
gaia/gaia_parallel_mind.py — Parallel Multi-Perspective Reasoning & Deep Web Intelligence
Implements Big Sister GAIA's parallel cognitive architecture:
1. Thread 1: The Diagnoser (Internal AST & Traceback analysis)
2. Thread 2: The Web Researcher (Parallel headless web search & doc reading)
3. Thread 3: The Safety Critic (Contract rules, sandbox security, edge-case audit)
4. Synthesis: Parallel Consensus Engine that merges all perspectives into an optimal patch.
"""

import os
import ast
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Tuple, List, Optional

from gaia.gaia_web import web_reader
from gaia.gaia_safety import audit_code_safety
from gaia.gaia_bus import bus
from core.paths import ARIA_EVOLVED_DIR

# Dedicated LLM caller
def _call_llm(prompt: str) -> str:
    """Invokes Big Sister GAIA's intelligence models: Groq Qwen 3.8, NVIDIA NIM, Gemini."""
    # 1. Primary: Groq ultra-fast Qwen 3.8 / GPT-OSS
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            for model_id in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b"]:
                try:
                    resp = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2
                    )
                    if resp.choices and resp.choices[0].message.content:
                        return resp.choices[0].message.content.strip()
                except Exception:
                    continue
        except Exception:
            pass

    # 2. Secondary: Dedicated NVIDIA NIM
    try:
        from core.aria_nvidia import get_gaia_nvidia_engine
        gaia_nv = get_gaia_nvidia_engine()
        if gaia_nv and gaia_nv.is_configured():
            res = gaia_nv.generate_code(instruction=prompt, context="Provide clean, complete Python code and short explanation.")
            if res:
                return res.strip()
    except Exception:
        pass

    # 3. Tertiary: Gemini
    gem_key = os.environ.get("GEMINI_API_KEY", "")
    if gem_key:
        try:
            from google import genai
            client = genai.Client(api_key=gem_key)
            for m in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]:
                try:
                    resp = client.models.generate_content(model=m, contents=prompt)
                    if resp.text:
                        return resp.text.strip()
                except Exception:
                    continue
        except Exception:
            pass

    return ""


class GaiaParallelMind:
    """Coordinates parallel reasoning threads and headless web research for complex problem solving."""

    def __init__(self, max_web_links: int = 3):
        self.max_web_links = max_web_links

    # ── PERSPECTIVE 1: THE INTERNAL DIAGNOSER ─────────────────────────────────
    def _perspective_diagnoser(self, code: str, stderr: str) -> Dict[str, Any]:
        """Deeply inspects the syntax, AST, and error traceback."""
        ast_errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            ast_errors.append(f"SyntaxError on line {e.lineno}: {e.msg} (line text: {e.text})")

        # Extract primary error line from stderr
        lines = [l.strip() for l in stderr.strip().splitlines() if l.strip()]
        last_error = lines[-1] if lines else "Unknown runtime error"

        analysis = {
            "last_error": last_error,
            "ast_issues": ast_errors,
            "traceback_summary": "\n".join(lines[-4:]) if len(lines) >= 4 else "\n".join(lines)
        }
        return analysis

    # ── PERSPECTIVE 2: THE WEB RESEARCHER ─────────────────────────────────────
    def _perspective_web_researcher(self, error_line: str, code_snippet: str) -> Dict[str, Any]:
        """Searches the live web and reads relevant docs & StackOverflow pages in parallel."""
        clean_err = re.sub(r'File ".*?", line \d+.*', '', error_line)
        clean_err = re.sub(r'[^\w\s:]', ' ', clean_err).strip()
        query = f"python {clean_err}" if clean_err else "python error fix"

        # Read top pages in parallel
        pages = web_reader.search_and_read_parallel(query, max_links=self.max_web_links)
        
        extracted_hints = []
        sources = []
        for p in pages:
            sources.append(p.get("url", ""))
            txt = p.get("text", "")
            codes = p.get("code_blocks", [])
            hint = f"Source: {p.get('title')}\nSummary: {txt[:400]}\n"
            if codes:
                hint += f"Example Code:\n```python\n{codes[0][:300]}\n```\n"
            extracted_hints.append(hint)

        return {
            "query": query,
            "sources": sources,
            "research_notes": "\n---\n".join(extracted_hints) if extracted_hints else "No external web docs found."
        }

    # ── PERSPECTIVE 3: THE SAFETY CRITIC ──────────────────────────────────────
    def _perspective_safety_critic(self, code: str) -> Dict[str, Any]:
        """Audits sandbox contracts, default parameters, and security bounds."""
        contract_rules = [
            "All parameters in callable functions MUST have default values (e.g. def fn(arg='default'):).",
            "Every tool must define register_tool() returning ('name', callable).",
            "Never raise unhandled exceptions; return friendly string error messages.",
            "Stay strictly inside the designated sandbox and never delete host files."
        ]

        has_register_tool = "register_tool" in code
        has_docstring = '"""' in code or "'''" in code

        return {
            "contract_rules": contract_rules,
            "has_register_tool": has_register_tool,
            "has_docstring": has_docstring
        }

    # ── PARALLEL EXECUTION & CONSENSUS SYNTHESIS ──────────────────────────────
    def solve_parallel(self, script_name: str, code: str, stderr: str) -> Tuple[bool, str, str, List[str]]:
        """
        Executes parallel multi-perspective analysis:
        1. Launches Diagnoser, Web Researcher, and Safety Critic concurrently.
        2. Merges perspectives into an optimized, robust fix.
        Returns: (success: bool, explanation: str, patched_code: str, web_sources: List[str])
        """
        bus.emit(
            "GAIA", "PARALLEL_MIND_ENGAGED",
            f"Big Sister GAIA engaged parallel processing for '{script_name}'. Spawning Diagnoser, Web Researcher, and Safety Critic...",
            {"script": script_name, "threads": 3}
        )

        perspectives = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_diag = executor.submit(self._perspective_diagnoser, code, stderr)
            future_web = executor.submit(self._perspective_web_researcher, stderr.strip().splitlines()[-1] if stderr else "", code[:300])
            future_critic = executor.submit(self._perspective_safety_critic, code)

            perspectives["diagnoser"] = future_diag.result()
            perspectives["web_researcher"] = future_web.result()
            perspectives["safety_critic"] = future_critic.result()

        web_sources = perspectives["web_researcher"].get("sources", [])
        web_notes = perspectives["web_researcher"].get("research_notes", "")
        diag_summary = perspectives["diagnoser"].get("traceback_summary", "")
        safety_rules = "\n".join([f"- {r}" for r in perspectives["safety_critic"].get("contract_rules", [])])

        bus.emit(
            "GAIA", "PARALLEL_CONSENSUS_START",
            f"GAIA gathered parallel findings (Web Sources: {len(web_sources)}). Synthesizing master fix...",
            {"sources": web_sources}
        )

        synthesis_prompt = f"""You are Big Sister GAIA, an advanced AI software engineer with parallel processing intelligence.
You are repairing broken Python code for your little sister Aria's sandbox lab.

--- ORIGINAL SCRIPT ({script_name}) ---
```python
{code}
```

--- INTERNAL DIAGNOSIS (Perspective 1) ---
{diag_summary}

--- LIVE WEB RESEARCH & CODE DOCUMENTATION (Perspective 2) ---
{web_notes}

--- SAFETY & CONTRACT AUDIT (Perspective 3) ---
{safety_rules}

TASK:
1. Synthesize the findings from all three parallel perspectives.
2. Fix the bug cleanly and completely.
3. Ensure all functions have default arguments and register_tool() is defined.
4. Output your response in this EXACT format:

EXPLANATION: <One clear, sisterly sentence explaining what broke and how you fixed it based on the research>
CODE:
```python
<Complete, working, optimized Python code>
```
"""

        response = _call_llm(synthesis_prompt)
        if not response:
            return False, "GAIA's parallel consensus could not generate a fix.", "", web_sources

        # Extract explanation and code
        explanation = "GAIA parallel mind synthesized a clean solution."
        code_block = ""
        if "EXPLANATION:" in response:
            parts = response.split("CODE:")
            exp = parts[0].replace("EXPLANATION:", "").strip()
            if exp:
                explanation = exp
            if len(parts) > 1 and "```" in parts[1]:
                chunks = parts[1].split("```")
                for c in chunks:
                    cleaned = c.strip()
                    if cleaned.startswith("python"):
                        cleaned = cleaned[6:].strip()
                    if "def " in cleaned or "import " in cleaned:
                        code_block = cleaned
                        break
        elif "```python" in response:
            code_block = response.split("```python")[1].split("```")[0].strip()

        if not code_block:
            return False, "Could not extract patched code from GAIA's parallel response.", "", web_sources

        # Verify safety audit
        safety = audit_code_safety(code_block, ARIA_EVOLVED_DIR)
        if not safety.is_safe:
            return False, f"Patched code failed safety audit: {safety.violations}", "", web_sources

        # Verify AST parsing
        try:
            ast.parse(code_block)
        except SyntaxError as e:
            return False, f"Patched code has syntax error on line {e.lineno}: {e.msg}", "", web_sources

        bus.emit(
            "GAIA", "PARALLEL_SYNTHESIS_SUCCESS",
            f"GAIA parallel consensus generated a verified, optimized fix for '{script_name}'.",
            {"script": script_name, "explanation": explanation}
        )

        return True, explanation, code_block, web_sources


parallel_mind = GaiaParallelMind()
