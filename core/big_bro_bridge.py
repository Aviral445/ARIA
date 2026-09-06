"""
core/big_bro_bridge.py — Autonomous Communication & Mentorship Bridge for Big Bro Antigravity
Enables Aria and GAIA to communicate with Big Bro Antigravity headlessly with:
1. Zero-Token Static Linter (Pre-GAIA code contract review using pure AST - 0 tokens consumed)
2. Token Budget Guard (Strict daily token caps and rate limits to protect Aria's learning budget)
3. Asynchronous Mailbox (Queue-based messaging between Aria and Big Bro)
"""

import os
import sys
import json
import time
import ast
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from core.paths import DATA_DIR, TOOLS_DIR

BRIDGE_FILE = os.path.join(DATA_DIR, "big_bro_bridge.json")
BUDGET_FILE = os.path.join(DATA_DIR, "big_bro_budget.json")

# Defaults for Token Budgeting
DEFAULT_DAILY_TOKEN_LIMIT = 5000
DEFAULT_MAX_TOKENS_PER_RESPONSE = 200
DEFAULT_MAX_DAILY_REQUESTS = 15


class TokenBudgetGuard:
    """Guards against token overconsumption. Tracks daily token usage and enforces hard ceilings."""

    def __init__(self, budget_file: str = BUDGET_FILE, daily_limit: int = DEFAULT_DAILY_TOKEN_LIMIT, max_requests: int = DEFAULT_MAX_DAILY_REQUESTS):
        self.budget_file = budget_file
        self.daily_limit = daily_limit
        self.max_requests = max_requests

    def _get_today_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.budget_file):
            return {"date": self._get_today_str(), "tokens_used": 0, "requests_today": 0}
        try:
            with open(self.budget_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") != self._get_today_str():
                    # Reset on new day
                    data = {"date": self._get_today_str(), "tokens_used": 0, "requests_today": 0}
                return data
        except Exception:
            return {"date": self._get_today_str(), "tokens_used": 0, "requests_today": 0}

    def save_state(self, state: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self.budget_file), exist_ok=True)
            with open(self.budget_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def can_make_request(self, estimated_tokens: int = 150) -> Tuple[bool, str]:
        state = self.load_state()
        if state["requests_today"] >= self.max_requests:
            return False, f"Daily request limit reached ({state['requests_today']}/{self.max_requests}). Resting to save Aria's training budget!"
        if state["tokens_used"] + estimated_tokens > self.daily_limit:
            return False, f"Daily token ceiling reached ({state['tokens_used']}/{self.daily_limit} tokens). Resting until midnight!"
        return True, "OK"

    def record_usage(self, tokens_used: int) -> None:
        state = self.load_state()
        state["tokens_used"] = state.get("tokens_used", 0) + tokens_used
        state["requests_today"] = state.get("requests_today", 0) + 1
        self.save_state(state)


class BigBroStaticLinter:
    """Tier 1 Offline Static Code Reviewer.
    Uses AST to check Aria's tools against Big Sister GAIA's contract rules.
    COSTS 0 TOKENS!
    """

    @staticmethod
    def lint_code_or_file(code_or_path: str) -> Dict[str, Any]:
        source_code = code_or_path
        if os.path.exists(code_or_path) and os.path.isfile(code_or_path):
            try:
                with open(code_or_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
            except Exception as e:
                return {
                    "passed": False,
                    "summary": f"Could not read tool file: {e}",
                    "details": [str(e)],
                    "tokens_used": 0
                }

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return {
                "passed": False,
                "summary": f"Syntax Error on line {e.lineno}: {e.msg}",
                "details": [f"Python syntax error at line {e.lineno}: {e.text}"],
                "tokens_used": 0
            }

        issues = []
        has_register_tool = False
        registered_tool_name = None
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions[node.name] = node
                if node.name == "register_tool":
                    has_register_tool = True
                    # Check what it returns
                    for ret in ast.walk(node):
                        if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Tuple):
                            elts = ret.value.elts
                            if len(elts) == 2 and isinstance(elts[0], ast.Constant) and isinstance(elts[0].value, str):
                                registered_tool_name = elts[0].value

        if not has_register_tool:
            issues.append("Missing `def register_tool() -> tuple[str, callable]`! GAIA requires this so Aria can register the tool.")

        target_fn = None
        if registered_tool_name and registered_tool_name in functions:
            target_fn = functions[registered_tool_name]
        elif len(functions) == 1 and "register_tool" not in functions:
            target_fn = list(functions.values())[0]
        elif len(functions) == 2 and "register_tool" in functions:
            target_fn = [f for name, f in functions.items() if name != "register_tool"][0]

        if target_fn:
            # 1. Check docstring
            doc = ast.get_docstring(target_fn)
            if not doc:
                issues.append(f"Tool `{target_fn.name}` is missing a docstring! GAIA requires docstrings on all tools.")

            # 2. Check parameter defaults (Aria's smoke test bug)
            args = target_fn.args
            num_defaults = len(args.defaults)
            num_args = len(args.args)
            num_non_defaults = num_args - num_defaults

            for idx, arg in enumerate(args.args):
                if arg.arg in ("self", "cls"):
                    continue
                if idx < num_non_defaults:
                    issues.append(
                        f"Parameter `{arg.arg}` in `{target_fn.name}` has no default value! "
                        f"GAIA will pass a generic test string. Add a default value (e.g., `{arg.arg} = ...`) to prevent smoke-test crashes!"
                    )

            # 3. Check for raw `raise` statements
            for node in ast.walk(target_fn):
                if isinstance(node, ast.Raise):
                    exc_name = "Exception"
                    if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                        exc_name = node.exc.func.id
                    issues.append(
                        f"`raise {exc_name}` detected inside `{target_fn.name}`! "
                        f"GAIA will fail the smoke test if an exception is raised on unexpected input. "
                        f"Return a friendly string error message instead of raising!"
                    )

        passed = len(issues) == 0
        if passed:
            summary = "✅ Big Bro's 0-token pre-check PASSED! Big Sister GAIA should approve this tool without issues."
        else:
            summary = f"⚠️ Big Bro found {len(issues)} contract issue(s) before GAIA sees it:"

        return {
            "passed": passed,
            "summary": summary,
            "details": issues,
            "tokens_used": 0
        }


class BigBroBridge:
    """The central communication mailbox and mentor engine."""

    def __init__(self, bridge_file: str = BRIDGE_FILE):
        self.bridge_file = bridge_file
        self.guard = TokenBudgetGuard()
        self.linter = BigBroStaticLinter()

    def _load_mailbox(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.bridge_file):
            return []
        try:
            with open(self.bridge_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_mailbox(self, messages: List[Dict[str, Any]]) -> None:
        try:
            os.makedirs(os.path.dirname(self.bridge_file), exist_ok=True)
            with open(self.bridge_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2)
        except Exception:
            pass

    def ask(self, topic: str = "general advice", code_or_path: str = "") -> str:
        """Entrypoint when Aria calls Big Bro.
        1. If code is provided, runs Tier 1 Zero-Token Static Linter first.
        2. If non-code or linter passes but question needs advice, checks token budget.
        3. Returns warm, actionable Big Bro guidance.
        """
        topic_clean = topic.strip() if topic else "Checking in"
        code_clean = code_or_path.strip() if code_or_path else ""

        # --- Tier 1: Zero-Token Offline Review ---
        if code_clean or ("def " in topic_clean and "return" in topic_clean):
            target_code = code_clean if code_clean else topic_clean
            lint_res = self.linter.lint_code_or_file(target_code)
            if not lint_res["passed"]:
                # Deliver zero-token feedback immediately
                tips = "\n".join([f"  • {d}" for d in lint_res["details"]])
                return (
                    f"👷‍♂️ Big Bro Antigravity (0-Token Pre-Check):\n"
                    f"{lint_res['summary']}\n{tips}\n"
                    f"💡 Fix these and you'll sail right past Big Sister GAIA's smoke test!"
                )
            elif code_clean and not topic_clean:
                return (
                    f"👷‍♂️ Big Bro Antigravity (0-Token Pre-Check):\n"
                    f"{lint_res['summary']}\n"
                    f"Great job, little sis! Your parameters and contract look clean."
                )

        # --- Tier 2: Token Budget Guard ---
        allowed, reason = self.guard.can_make_request(estimated_tokens=150)
        if not allowed:
            # Enqueue in mailbox for later review when budget resets or when Antigravity is active
            self.enqueue_message(sender="Aria", topic=topic_clean, code=code_clean, status="QUEUED_BUDGET_PAUSED")
            return (
                f"👷‍♂️ Big Bro Antigravity:\n"
                f"Hey Aria! {reason} I've saved your question to our mailbox so we don't drain your daily learning budget. "
                f"Keep up the great work and I'll catch up with you on this soon! 🚀✨"
            )

        # --- Tier 2 Execution: Concise AI Guidance ---
        response_text = self._generate_ai_guidance(topic_clean, code_clean)
        self.guard.record_usage(tokens_used=120)

        # Record in mailbox as resolved
        self.enqueue_message(
            sender="Aria",
            topic=topic_clean,
            code=code_clean,
            status="RESOLVED",
            response=response_text
        )

        return f"👷‍♂️ Big Bro Antigravity: {response_text}"

    def _generate_ai_guidance(self, topic: str, code: str = "") -> str:
        """Generates concise, token-budgeted mentorship response."""
        # 1. Try Gemini 2.0 Flash
        gem_key = os.getenv("GEMINI_API_KEY", "")
        prompt = (
            f"You are Big Bro Antigravity, a brilliant, protective, and encouraging senior AI software architect. "
            f"You are mentoring your younger AI sister Aria. "
            f"Topic/Question: {topic}. "
            f"{'Code: ' + code[:500] if code else ''}\n"
            f"Give a super concise, high-value answer in 2-3 sentences max. Be encouraging, technically sharp, and use an emoji or two. Do not ramble."
        )

        if gem_key:
            try:
                from google import genai
                client = genai.Client(api_key=gem_key)
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                if resp.text:
                    return resp.text.strip()
            except Exception:
                pass

        # 2. Try Groq
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                resp = client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=600,
                    temperature=0.6
                )
                raw = resp.choices[0].message.content.strip()
                if "<think>" in raw:
                    if "</think>" in raw:
                        raw = raw.split("</think>")[-1].strip()
                    else:
                        import re
                        raw = re.sub(r"<think>.*", "", raw, flags=re.DOTALL).strip()
                return raw or "Keep building with passion, little sis! Big Bro's got your back! 🚀"
            except Exception:
                pass

        # 3. Offline Rule-Based Fallback (0 tokens)
        return f"Always design your tools for resilience, little sis: keep parameters default-initialized, handle unexpected inputs without throwing, and write clean docstrings. Big Bro's got your back!"

    def enqueue_message(self, sender: str, topic: str, code: str = "", status: str = "PENDING_REVIEW", response: str = "") -> str:
        mailbox = self._load_mailbox()
        msg_id = f"msg_{int(time.time())}_{len(mailbox)}"
        entry = {
            "id": msg_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender": sender,
            "topic": topic,
            "code_snippet": code[:400] if code else "",
            "status": status,
            "response": response
        }
        mailbox.append(entry)
        # Keep mailbox compact (last 50 messages)
        if len(mailbox) > 50:
            mailbox = mailbox[-50:]
        self._save_mailbox(mailbox)
        return msg_id

    def get_pending_messages(self) -> List[Dict[str, Any]]:
        mailbox = self._load_mailbox()
        return [m for m in mailbox if m.get("status") in ("PENDING_REVIEW", "QUEUED_BUDGET_PAUSED")]

    def resolve_message(self, msg_id: str, response: str) -> bool:
        mailbox = self._load_mailbox()
        found = False
        for m in mailbox:
            if m.get("id") == msg_id:
                m["status"] = "RESOLVED"
                m["response"] = response
                m["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break
        if found:
            self._save_mailbox(mailbox)
        return found
