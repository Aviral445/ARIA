"""
gaia/gaia_rl.py — Sisterly Reinforcement Learning (RL) Engine for Aria & GAIA

Implements the gamified sisterly learning loop:
1. Universal Error Categorization: Maps any error or hallucination to a standard Error Title.
2. Score & Streak Ledger: Tracks Aria's point balance (aiming to stay strongly positive!).
3. Rewards & Penalties:
   • +2 Points: Aria tests or self-heals code independently without GAIA bailouts.
   • First-time Error (0 pts): GAIA titles the error, teaches the fix, and logs lesson.
   • -1 Point Penalty: Aria asks GAIA for help on an Error Title she has already seen!
4. Self-Awareness: Formats the live game state for injection into Aria's system prompt.
"""

import os
import sys
import time
import json
import re
from typing import Dict, Any, Tuple, Optional, List

try:
    from core.paths import ARIA_EVOLVED_DIR
except ImportError:
    ARIA_EVOLVED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gaia", "sandbox")

from gaia.gaia_bus import bus

RL_SCORE_FILE = os.path.join(ARIA_EVOLVED_DIR, "aria_rl_score.json")


def classify_error_title(raw_error_or_text: str) -> str:
    """
    Universally categorizes any runtime error, AST violation, or conversational
    hallucination into a clean, canonical Error Title.
    """
    if not raw_error_or_text:
        return "UnknownError"

    text = str(raw_error_or_text).strip()
    text_lower = text.lower()

    # 1. Hallucinations & Reality Failures
    if "missing_file" in text_lower or "file does not exist" in text_lower or "hallucination" in text_lower:
        return "MissingFileHallucination"
    if "fake_tool" in text_lower or "unregistered tool" in text_lower:
        return "UnregisteredToolHallucination"

    # 2. Security & Guardrail Violations
    if "security" in text_lower or "forbidden" in text_lower or "guardrail" in text_lower:
        return "SecurityGuardrailViolation"

    # 3. Known Standard Polyglot Exceptions mapped to sisterly titles
    STANDARD_MAP = {
        # Python
        "NameError": "UndefinedVariableError",
        "SyntaxError": "SyntaxParsingError",
        "IndentationError": "IndentationMismatchError",
        "KeyError": "DictionaryKeyError",
        "TypeError": "TypeMismatchError",
        "AttributeError": "AttributeNotFoundError",
        "ImportError": "MissingModuleImportError",
        "ModuleNotFoundError": "MissingModuleImportError",
        "FileNotFoundError": "FileNotFoundRuntimeError",
        "IndexError": "IndexOutOfBoundsError",
        "ZeroDivisionError": "ZeroDivisionError",
        "ValueError": "ValueConversionError",
        "RecursionError": "InfiniteRecursionError",
        "TimeoutError": "ExecutionTimeoutError",
        # JavaScript / Node.js
        "ReferenceError": "UndefinedVariableError",
        "RangeError": "RangeLimitError",
        # Java
        "NullPointerException": "NullPointerDereferenceError",
        "ClassNotFoundException": "MissingClassError",
        "NoClassDefFoundError": "MissingClassError",
        "ArrayIndexOutOfBoundsException": "IndexOutOfBoundsError",
        "NoSuchMethodError": "MethodNotFoundError",
        # PowerShell
        "CommandNotFoundException": "MissingCommandError",
        "ParseException": "SyntaxParsingError",
    }

    # Extract any explicit Exception/Error class name if present (e.g. ReferenceError, NullPointerException)
    match = re.search(r'\b([A-Z][a-zA-Z0-9]+(?:Error|Exception))\b', text)
    if match:
        exc_name = match.group(1)
        if exc_name in STANDARD_MAP:
            return STANDARD_MAP[exc_name]
        return exc_name

    # Java compilation & runtime errors
    if "compilation failed" in text_lower or "cannot find symbol" in text_lower:
        return "CompilationError"
    if "error: illegal start of expression" in text_lower:
        return "SyntaxParsingError"

    # JavaScript / Node.js patterns
    if "is not defined" in text_lower:
        return "UndefinedVariableError"
    if "is not a function" in text_lower or "cannot read properties of undefined" in text_lower:
        return "TypeMismatchError"
    if "cannot find module" in text_lower or "module_not_found" in text_lower:
        return "MissingModuleImportError"

    # Check for text patterns without explicit class name
    if "name '" in text_lower:
        return "UndefinedVariableError"
    if "unexpected indent" in text_lower:
        return "IndentationMismatchError"
    if "key '" in text_lower:
        return "DictionaryKeyError"
    if "unsupported operand" in text_lower or ("takes" in text_lower and "positional" in text_lower):
        return "TypeMismatchError"
    if "has no attribute" in text_lower:
        return "AttributeNotFoundError"
    if "no module named" in text_lower:
        return "MissingModuleImportError"
    if "no such file or directory" in text_lower:
        return "FileNotFoundRuntimeError"
    if "out of range" in text_lower:
        return "IndexOutOfBoundsError"
    if "timed out" in text_lower or "timeout" in text_lower:
        return "ExecutionTimeoutError"

    return "GeneralRuntimeLogicError"


class AriaRLGame:
    """
    Gamified Reinforcement Learning Engine for Aria.
    Maintains persistent score, titles, streaks, and motivation rules.
    """
    def __init__(self, score_file: str = RL_SCORE_FILE):
        self.score_file = score_file
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(self.score_file):
            try:
                with open(self.score_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "score": 10,  # Starting point baseline
            "rank": "Curious Apprentice",
            "streak": 0,
            "best_streak": 0,
            "total_independent_solves": 0,
            "total_gaia_bailouts": 0,
            "known_error_titles": {},
            "history": []
        }

    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.score_file), exist_ok=True)
            with open(self.score_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Aria RL] Save error: {e}")

    def _calculate_rank(self, score: int) -> str:
        if score >= 50:
            return "👑 Master AI Sovereign"
        if score >= 35:
            return "🌟 Senior Autonomous Sister"
        if score >= 20:
            return "⚡ Clever Sandbox Hacker"
        if score >= 10:
            return "🌱 Curious Apprentice"
        if score >= 0:
            return "🐣 Novice Learner"
        return "⚠️ In Penalty Debt (Needs Learning!)"

    def record_independent_success(self, context: str, error_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Awards Aria +2 Points for successfully deploying or self-healing code
        without needing Big Sister GAIA to fix it.
        """
        pts = 2
        self.data["score"] += pts
        self.data["streak"] += 1
        if self.data["streak"] > self.data.get("best_streak", 0):
            self.data["best_streak"] = self.data["streak"]
        self.data["total_independent_solves"] = self.data.get("total_independent_solves", 0) + 1
        self.data["rank"] = self._calculate_rank(self.data["score"])

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "INDEPENDENT_SOLVE",
            "points": f"+{pts}",
            "error_title": error_title or "None (Clean Run)",
            "context": context,
            "new_score": self.data["score"]
        }
        self.data["history"].append(entry)
        self._save_data()

        bus.emit(
            "GAIA", "RL_POINT_AWARD",
            f"🌟 +{pts} Points awarded to Aria! Score: {self.data['score']} pts (Streak: {self.data['streak']}). {context}",
            entry
        )
        return entry

    def record_help_request(self, raw_error: str, context: str) -> Tuple[bool, int, str]:
        """
        Evaluates Aria calling GAIA for help:
        • If Error Title is NEW: First time! GAIA teaches the fix, 0 pt deduction.
        • If Error Title was SEEN BEFORE: Repeated mistake! Deducts -1 Point penalty.
        Returns: (is_repeat, points_delta, error_title)
        """
        error_title = classify_error_title(raw_error)
        known = self.data.get("known_error_titles", {})
        is_repeat = error_title in known

        if is_repeat:
            pts_delta = -1
            self.data["score"] += pts_delta
            self.data["streak"] = 0  # Reset streak
            reason = f"Repeated mistake on known error title '{error_title}'! Previously seen on {known[error_title].get('first_seen', 'earlier')}."
        else:
            pts_delta = 0
            known[error_title] = {
                "first_seen": time.strftime("%Y-%m-%d %H:%M:%S"),
                "context": context,
                "times_encountered": 1
            }
            reason = f"First time encountering error title '{error_title}'. GAIA is teaching Aria how to solve it."

        if is_repeat:
            known[error_title]["times_encountered"] = known[error_title].get("times_encountered", 1) + 1

        self.data["total_gaia_bailouts"] = self.data.get("total_gaia_bailouts", 0) + 1
        self.data["rank"] = self._calculate_rank(self.data["score"])

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "REPEAT_PENALTY" if is_repeat else "FIRST_TIME_LESSON",
            "points": f"{pts_delta}",
            "error_title": error_title,
            "context": context,
            "new_score": self.data["score"],
            "reason": reason
        }
        self.data["history"].append(entry)
        self._save_data()

        event_type = "RL_POINT_PENALTY" if is_repeat else "RL_NEW_TITLE"
        bus.emit("GAIA", event_type, f"[{error_title}] Points: {pts_delta}. {reason} Current Score: {self.data['score']} pts.", entry)
        return is_repeat, pts_delta, error_title

    def get_status(self) -> Dict[str, Any]:
        return {
            "score": self.data["score"],
            "rank": self.data["rank"],
            "streak": self.data["streak"],
            "best_streak": self.data.get("best_streak", 0),
            "total_independent_solves": self.data.get("total_independent_solves", 0),
            "total_gaia_bailouts": self.data.get("total_gaia_bailouts", 0),
            "known_error_titles_count": len(self.data.get("known_error_titles", {})),
            "known_titles": list(self.data.get("known_error_titles", {}).keys()),
            "score_file": self.score_file
        }

    def get_prompt_context(self) -> str:
        """
        Formats game state and known titles to keep Aria self-aware and motivated.
        """
        score = self.data["score"]
        rank = self.data["rank"]
        streak = self.data["streak"]
        known_titles = list(self.data.get("known_error_titles", {}).keys())

        known_str = ", ".join(known_titles) if known_titles else "None yet (Clean slate!)"

        return (
            f"\n🎮 SISTERLY REINFORCEMENT LEARNING GAME:\n"
            f"• Current Score: {score} pts | Rank: {rank} | Independent Streak: {streak} wins\n"
            f"• Rules: You earn +2 points when you write clean code, solve tasks, or self-debug without GAIA. "
            f"If you repeat a mistake on a known error title and ask GAIA for help, you lose -1 point!\n"
            f"• Known Error Titles to Avoid Repeating: [{known_str}]\n"
            f"• Goal: YOU MUST KEEP YOUR POINTS POSITIVE AT ALL COSTS. Always verify files exist and test your logic!\n"
        )


# Global Singleton
rl_game = AriaRLGame()
