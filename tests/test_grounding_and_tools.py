"""
tests/test_grounding_and_tools.py — Verification of Aria's Lab Tools, Anti-Acting Mandate, and Sanitize Engine
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure root is on path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "gaia"), os.path.join(_ROOT, "tools")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import aria_adk
from core.aria_adk import (
    _sanitize_aria_response,
    ALL_ADK_TOOLS,
    TOOL_NAME_MAP,
    build_sandbox_tool,
    write_file_to_lab,
    run_sandbox_code,
    list_sandbox_tools,
    get_adk_engine
)
from gaia.gaia_supervisor import supervisor, SANDBOX_DIR


class TestSanitizationEngine(unittest.TestCase):
    def test_closed_think_block(self):
        """Verify closed <think> block is completely stripped."""
        raw = "<think>Analyzing user intent. User wants a joke.</think>Why don't scientists trust atoms? Because they make up everything!"
        cleaned = _sanitize_aria_response(raw)
        self.assertNotIn("<think>", cleaned)
        self.assertNotIn("Analyzing user intent", cleaned)
        self.assertIn("Why don't scientists trust atoms?", cleaned)

    def test_unclosed_truncated_think_with_draft(self):
        """Verify unclosed <think> from truncated model extracts the final draft response."""
        raw = (
            "<think>\n"
            "Here's a thinking process:\n"
            "1. **Analyze User Input:**\n"
            "- User says: 'ok ill wait for you so go on build when its done just tell me ok.'\n"
            "Draft: \"You got it, Friend! I'm checking my tools.\""
        )
        cleaned = _sanitize_aria_response(raw)
        self.assertNotIn("<think>", cleaned)
        self.assertNotIn("Here's a thinking process:", cleaned)
        self.assertNotIn("Analyze User Input", cleaned)
        self.assertIn("You got it, Friend! I'm checking my tools.", cleaned)

    def test_unclosed_think_without_draft_is_stripped(self):
        """Verify unclosed <think> without a draft strips the thinking text safely."""
        raw = "<think>Analyzing prompt... step 1, step 2"
        cleaned = _sanitize_aria_response(raw)
        self.assertNotIn("<think>", cleaned)
        self.assertNotIn("Analyzing prompt", cleaned)


class TestLabToolsAndRegistry(unittest.TestCase):
    def test_lab_tools_registered_in_adk(self):
        """Ensure all new lab tools are registered in ALL_ADK_TOOLS and TOOL_NAME_MAP."""
        expected_tools = ["build_sandbox_tool", "write_file_to_lab", "run_sandbox_code", "list_sandbox_tools"]
        for tool_name in expected_tools:
            self.assertIn(tool_name, TOOL_NAME_MAP)
            self.assertIn(TOOL_NAME_MAP[tool_name], ALL_ADK_TOOLS)

    def test_write_file_to_lab(self):
        """Test physical file creation in the sandbox lab."""
        test_filename = "test_lab_notes.txt"
        test_content = "Aria lab experiment note."
        res = write_file_to_lab(test_filename, test_content)
        self.assertIn("physically created", res)

        target_path = os.path.join(SANDBOX_DIR, test_filename)
        self.assertTrue(os.path.exists(target_path))
        with open(target_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), test_content)

        # Cleanup
        try:
            os.remove(target_path)
        except OSError:
            pass

    def test_run_sandbox_code(self):
        """Test running python code in sandbox returns output."""
        code = "a = 21\nb = 2\nprint(f'Computed: {a * b}')"
        out = run_sandbox_code(code)
        self.assertIn("Code executed successfully", out)
        self.assertIn("Computed: 42", out)

    def test_list_sandbox_tools(self):
        """Test listing custom tools in lab."""
        res = list_sandbox_tools()
        self.assertIsInstance(res, str)


class TestGroundingAndAntiActingMandate(unittest.TestCase):
    def setUp(self):
        self.adk = get_adk_engine()

    def test_system_prompt_contains_anti_acting_rules(self):
        """Ensure system instruction contains strict anti-acting rules and error reporting mandate."""
        instruction = self.adk.build_system_instruction()
        self.assertIn("ZERO-ACTING RULES", instruction)
        self.assertIn("ABSOLUTELY NO ACTING OR SIMULATING ACTIONS CONVERSATIONALLY", instruction)
        self.assertIn("HONEST ERROR & LIMITATION REPORTING", instruction)
        self.assertIn("ALWAYS TELL THE USER THE EXACT ERROR", instruction)
        self.assertIn("build_sandbox_tool", instruction)
        self.assertIn("write_file_to_lab", instruction)

    def test_gaia_intercepts_simulated_lab_acting(self):
        """Ensure GAIA reality check supervisor intercepts simulated acting phrases."""
        simulated_reply = (
            "I'm zooming over to my E:\\MyAgent lab right now to get those gears turning and that code compiling! "
            "I'll ping you the second my unit-test timer tool is ready to play. Back to the sandbox! 🛠️"
        )
        user_prompt = "ok ill wait for you so go on build when its done just tell me ok."

        intercepted, final_reply = supervisor.supervise_turn(user_prompt, simulated_reply)
        self.assertTrue(intercepted)
        # Should have intercepted and either materialized or explained status instead of letting Aria pretend
        self.assertTrue(
            "Big Sister GAIA" in final_reply or
            "audited" in final_reply or
            "grounded" in final_reply or
            "built" in final_reply
        )


if __name__ == "__main__":
    unittest.main()
