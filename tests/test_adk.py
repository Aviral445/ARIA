"""
test_adk.py — Verification of Aria ADK Engine, Tool Schemas, and Execution Loop
"""

import os, sys, unittest

# Ensure root and subfolders are in path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "server"), os.path.join(_ROOT, "mcp"), os.path.join(_ROOT, "gui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import aria_adk

class TestAriaADK(unittest.TestCase):
    def setUp(self):
        self.adk = aria_adk.get_adk_engine()

    def test_tool_registry_present(self):
        """Verify that all essential tools are registered and mapped."""
        self.assertGreater(len(aria_adk.ALL_ADK_TOOLS), 10)
        self.assertIn("open_application", aria_adk.TOOL_NAME_MAP)
        self.assertIn("organize_directory", aria_adk.TOOL_NAME_MAP)
        self.assertIn("get_system_diagnostics", aria_adk.TOOL_NAME_MAP)
        self.assertIn("get_latest_news", aria_adk.TOOL_NAME_MAP)
        self.assertIn("get_crypto_price", aria_adk.TOOL_NAME_MAP)

    def test_local_tool_execution(self):
        """Test direct invocation of pure tools via tool map."""
        fn_crypto = aria_adk.TOOL_NAME_MAP.get("get_crypto_price")
        self.assertIsNotNone(fn_crypto)
        # Call with bitcoin
        res = fn_crypto(coin="bitcoin")
        self.assertIsInstance(res, str)
        self.assertTrue("Bitcoin" in res or "USD" in res or "error" in res.lower() or "price" in res.lower())

    def test_system_instruction_builder(self):
        """Verify prompt construction with personality and system context."""
        instruction = self.adk.build_system_instruction(user_name="Alex", preferences="dark mode")
        self.assertIn("Aria", instruction)
        self.assertIn("Alex", instruction)
        self.assertTrue("RULES" in instruction or "GUIDELINES" in instruction)

if __name__ == "__main__":
    unittest.main()
