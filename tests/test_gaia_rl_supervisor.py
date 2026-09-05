"""
tests/test_gaia_rl_supervisor.py — Automated Test Suite for:
1. Gamified Sisterly Reinforcement Learning (AriaRLGame)
2. Universal Error Categorization & Title Tracking
3. Big Sister GAIA Anti-Hallucination Reality Check Supervisor
4. Dynamic Sandbox Tool Auto-Discovery & Loading into ALL_ADK_TOOLS
5. Context Prompt Self-Awareness
"""

import os
import sys
import unittest
import tempfile
import shutil

# Ensure root workspace is in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "server"), os.path.join(_ROOT, "gaia")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from gaia.gaia_rl import AriaRLGame, classify_error_title
from gaia.gaia_supervisor import GaiaSupervisor
from gaia.gaia_healer import SANDBOX_DIR
import core.aria_adk as aria_adk
import core.aria_learning as aria_learning


class TestAriaRLGame(unittest.TestCase):
    """Verifies the Gamified Reinforcement Learning rules, scoring, and streaks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.score_file = os.path.join(self.temp_dir, "test_score.json")
        self.game = AriaRLGame(score_file=self.score_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initial_state(self):
        status = self.game.get_status()
        self.assertEqual(status["score"], 10)
        self.assertEqual(status["streak"], 0)
        self.assertEqual(status["known_error_titles_count"], 0)
        self.assertIn("Curious Apprentice", status["rank"])

    def test_universal_error_categorization(self):
        """Verify that all varieties of errors map to clean, consistent Error Titles."""
        self.assertEqual(classify_error_title("NameError: name 'foo' is not defined"), "UndefinedVariableError")
        self.assertEqual(classify_error_title("SyntaxError: invalid syntax"), "SyntaxParsingError")
        self.assertEqual(classify_error_title("KeyError: 'secret_key'"), "DictionaryKeyError")
        self.assertEqual(classify_error_title("IndexError: list index out of range"), "IndexOutOfBoundsError")
        self.assertEqual(classify_error_title("TypeError: unsupported operand type(s)"), "TypeMismatchError")
        self.assertEqual(classify_error_title("ZeroDivisionError: division by zero"), "ZeroDivisionError")
        self.assertEqual(classify_error_title("ModuleNotFoundError: No module named 'scipy'"), "MissingModuleImportError")
        self.assertEqual(classify_error_title("FileNotFoundError: [Errno 2] No such file"), "FileNotFoundRuntimeError")
        self.assertEqual(classify_error_title("Reality check fail: missing_file tool_test.py"), "MissingFileHallucination")
        self.assertEqual(classify_error_title("Forbidden AST Node: import subprocess violates security"), "SecurityGuardrailViolation")
        self.assertEqual(classify_error_title("CustomDatabaseConnectionError: timed out"), "CustomDatabaseConnectionError")

    def test_independent_success_awards_points(self):
        """Verify Aria gets +2 points and streak increases when solving independently."""
        initial_score = self.game.data["score"]
        entry = self.game.record_independent_success("Aria wrote clean code without GAIA.")
        self.assertEqual(self.game.data["score"], initial_score + 2)
        self.assertEqual(self.game.data["streak"], 1)
        self.assertEqual(self.game.data["total_independent_solves"], 1)
        self.assertEqual(entry["points"], "+2")

    def test_help_request_first_time_zero_points(self):
        """First time asking GAIA for help on an error title: GAIA titles it, 0 pt penalty."""
        initial_score = self.game.data["score"]
        is_repeat, delta, title = self.game.record_help_request(
            "NameError: name 'x' is not defined",
            context="Testing first-time name error"
        )
        self.assertFalse(is_repeat)
        self.assertEqual(delta, 0)
        self.assertEqual(title, "UndefinedVariableError")
        self.assertEqual(self.game.data["score"], initial_score)
        self.assertIn("UndefinedVariableError", self.game.data["known_error_titles"])

    def test_repeat_error_deducts_one_point_and_resets_streak(self):
        """Repeating a mistake on a known error title deducts -1 point and resets streak!"""
        # First build a streak
        self.game.record_independent_success("Solve 1")
        self.game.record_independent_success("Solve 2")
        self.assertEqual(self.game.data["streak"], 2)

        # First encounter with KeyError
        self.game.record_help_request("KeyError: 'user_id'", context="First encounter")

        # Second encounter with KeyError (repeat!)
        current_score = self.game.data["score"]
        is_repeat, delta, title = self.game.record_help_request(
            "KeyError: 'session_token'",
            context="Second encounter on same title"
        )
        self.assertTrue(is_repeat)
        self.assertEqual(delta, -1)
        self.assertEqual(title, "DictionaryKeyError")
        self.assertEqual(self.game.data["score"], current_score - 1)
        self.assertEqual(self.game.data["streak"], 0)  # Streak reset to 0

    def test_prompt_context_self_awareness(self):
        """Verify prompt context informs Aria about her score, streak, and known titles."""
        self.game.record_help_request("ZeroDivisionError: float division by zero", context="Math error")
        prompt = self.game.get_prompt_context()
        self.assertIn("SISTERLY REINFORCEMENT LEARNING GAME", prompt)
        self.assertIn("Current Score", prompt)
        self.assertIn("ZeroDivisionError", prompt)
        self.assertIn("KEEP YOUR POINTS POSITIVE", prompt)


class TestGaiaSupervisorAndRealityCheck(unittest.TestCase):
    """Verifies GAIA's conversational reality check and anti-hallucination intercept."""

    def setUp(self):
        self.supervisor = GaiaSupervisor(enable_voice=False)

    def test_turn_without_claims_is_unmodified(self):
        """Conversational chat without file creation claims passes through untouched."""
        prompt = "How are you feeling today Aria?"
        response = "I'm doing wonderfully, having fun in my lab!"
        intercepted, final = self.supervisor.supervise_turn(prompt, response)
        self.assertFalse(intercepted)
        self.assertEqual(final, response)

    def test_reality_check_passes_when_file_actually_exists(self):
        """If Aria claims a file exists and it physically does on disk, reality check passes."""
        test_tool_dir = os.path.join(SANDBOX_DIR, "tools")
        os.makedirs(test_tool_dir, exist_ok=True)
        test_file = os.path.join(test_tool_dir, "existing_real_tool.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# Real tool\ndef register_tool(): return 'real_tool', lambda: 'ok'\n")

        try:
            prompt = "Did you make existing_real_tool.py?"
            response = "Yes, I have created the tool existing_real_tool.py in my lab!"
            intercepted, final = self.supervisor.supervise_turn(prompt, response)
            self.assertFalse(intercepted)
            self.assertEqual(final, response)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_reality_check_intercepts_missing_file_and_synthesizes(self):
        """
        When Aria claims to have created a file that DOES NOT exist on disk:
        GAIA intercepts, synthesizes the tool in SANDBOX_DIR/tools,
        runs AST security check, verifies on disk, and grounds the response!
        """
        phantom_tool = "unit_test_timer_tool.py"
        phantom_path = os.path.join(SANDBOX_DIR, "tools", phantom_tool)
        if os.path.exists(phantom_path):
            os.remove(phantom_path)

        prompt = f"Please create a tool named {phantom_tool} for timing things."
        hallucinated_response = f"I have created the tool {phantom_tool} in my sandbox lab! Here it is."

        intercepted, grounded_response = self.supervisor.supervise_turn(prompt, hallucinated_response)

        # 1. Verification of Intercept
        self.assertTrue(intercepted, "GAIA should have intercepted the hallucinated turn!")

        # 2. Verification of physical existence on disk
        self.assertTrue(os.path.exists(phantom_path), f"Synthesized tool {phantom_path} must exist physically on disk!")

        # 3. Verification of response grounding
        self.assertIn("Big Sister GAIA stepped in", grounded_response)
        self.assertIn(phantom_tool, grounded_response)

        # Cleanup
        if os.path.exists(phantom_path):
            os.remove(phantom_path)


class TestDynamicSandboxToolDiscovery(unittest.TestCase):
    """Verifies newly created tools in SANDBOX_DIR/tools are auto-registered into ALL_ADK_TOOLS."""

    def test_dynamic_tool_loading(self):
        tools_dir = os.path.join(SANDBOX_DIR, "tools")
        os.makedirs(tools_dir, exist_ok=True)
        test_tool_path = os.path.join(tools_dir, "test_dice_roller.py")

        code = (
            "import random\n"
            "def roll_dice(sides: int = 6) -> str:\n"
            "    val = random.randint(1, sides)\n"
            "    return f'Rolled {val} on a {sides}-sided die.'\n"
            "def register_tool():\n"
            "    return 'roll_dice_sandbox', roll_dice\n"
        )
        with open(test_tool_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            loaded = aria_adk.load_dynamic_sandbox_tools()
            self.assertIn("roll_dice_sandbox", loaded)
            self.assertIn("roll_dice_sandbox", aria_adk.TOOL_NAME_MAP)
            
            # Verify tool execution
            tool_fn = aria_adk.TOOL_NAME_MAP["roll_dice_sandbox"]
            result = tool_fn(sides=20)
            self.assertTrue("Rolled" in result and "20-sided die" in result)
        finally:
            if os.path.exists(test_tool_path):
                os.remove(test_tool_path)


class TestLearnedContextPromptIntegration(unittest.TestCase):
    """Verifies that Aria's system prompt context includes learned rules and RL game status."""

    def test_learned_context_contains_rl_and_rules(self):
        prompt_ctx = aria_learning.get_learned_context_prompt()
        self.assertIn("SISTERLY REINFORCEMENT LEARNING GAME", prompt_ctx)
        self.assertIn("Current Score", prompt_ctx)
        self.assertIn("Rules: You earn +2 points", prompt_ctx)


if __name__ == "__main__":
    unittest.main()
