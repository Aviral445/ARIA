import os
import unittest
from gaia.sandbox.tools.quick_note_tool import quick_note_tool, register_tool, get_notes_folder
from core.aria_adk import load_dynamic_sandbox_tools, ALL_ADK_TOOLS, TOOL_NAME_MAP

class TestQuickNoteTool(unittest.TestCase):
    def test_register_tool(self):
        t_name, t_fn = register_tool()
        self.assertEqual(t_name, "quick_note_tool")
        self.assertTrue(callable(t_fn))

    def test_quick_note_tool_saves_file(self):
        note_text = "Unit test reminder: calibrate quantum sensor at 5 PM"
        res = quick_note_tool(note_text)
        self.assertIn("Saved note to", res)
        folder = get_notes_folder()
        self.assertTrue(os.path.exists(folder))

        # Check latest file in folder
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.startswith("note_")]
        self.assertTrue(len(files) > 0)
        latest = max(files, key=os.path.getctime)
        with open(latest, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(note_text, content)

    def test_quick_note_tool_empty_input(self):
        res = quick_note_tool("")
        self.assertIn("Please provide text", res)

    def test_adk_discovery_registers_quick_note_tool(self):
        tools = load_dynamic_sandbox_tools()
        self.assertIn("quick_note_tool", TOOL_NAME_MAP)
        self.assertIn(TOOL_NAME_MAP["quick_note_tool"], ALL_ADK_TOOLS)

if __name__ == "__main__":
    unittest.main()
