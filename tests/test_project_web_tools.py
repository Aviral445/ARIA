"""
tests/test_project_web_tools.py — Unit Tests for Aria's Multi-File Project & Web Dev Tools
"""

import os
import sys
import unittest
import urllib.request
import time
import shutil

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "gaia"), os.path.join(_ROOT, "tools")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.aria_adk import (
    ALL_ADK_TOOLS,
    TOOL_NAME_MAP,
    aria_write_project_file,
    aria_launch_project_server,
    aria_stop_project_server,
    get_adk_engine,
)
from core.aria_file_structuring import _resolve_safe_path


class TestProjectWebTools(unittest.TestCase):
    def setUp(self):
        self.test_project = "Aria_Test_Web_Unit"
        self.proj_dir = _resolve_safe_path(f"Projects/{self.test_project}")
        if os.path.exists(self.proj_dir):
            shutil.rmtree(self.proj_dir)

    def tearDown(self):
        aria_stop_project_server(self.test_project)
        if os.path.exists(self.proj_dir):
            try:
                shutil.rmtree(self.proj_dir)
            except Exception:
                pass

    def test_tools_registered(self):
        """Verify aria_write_project_file, launch and stop are registered in ADK."""
        for tool_name in ["aria_write_project_file", "aria_launch_project_server", "aria_stop_project_server"]:
            self.assertIn(tool_name, TOOL_NAME_MAP)
            self.assertIn(TOOL_NAME_MAP[tool_name], ALL_ADK_TOOLS)

    def test_write_project_file_and_launch_server(self):
        """Test writing multiple files (HTML, CSS, JS) and serving over localhost."""
        # 1. Write HTML
        html_code = "<!DOCTYPE html><html><body><h1 id='title'>Aria Scientific Web App</h1></body></html>"
        res_html = aria_write_project_file(self.test_project, "index.html", html_code)
        self.assertIn("Successfully saved", res_html)

        # 2. Write CSS
        css_code = "body { background: #0f172a; color: #f8fafc; font-family: sans-serif; }"
        res_css = aria_write_project_file(self.test_project, "style.css", css_code)
        self.assertIn("Successfully saved", res_css)

        # 3. Write JS
        js_code = "console.log('Aria Calculator Loaded');"
        res_js = aria_write_project_file(self.test_project, "app.js", js_code)
        self.assertIn("Successfully saved", res_js)

        # Verify files on disk
        self.assertTrue(os.path.exists(os.path.join(self.proj_dir, "index.html")))
        self.assertTrue(os.path.exists(os.path.join(self.proj_dir, "style.css")))
        self.assertTrue(os.path.exists(os.path.join(self.proj_dir, "app.js")))

        # 4. Launch local server
        test_port = 5088
        launch_msg = aria_launch_project_server(self.test_project, port=test_port, open_in_browser=False)
        self.assertIn("Successfully launched", launch_msg)

        # 5. Query server via HTTP
        time.sleep(0.5)
        url = f"http://localhost:{test_port}/index.html"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = resp.read().decode("utf-8")
            self.assertIn("Aria Scientific Web App", data)

        # 6. Stop server
        stop_msg = aria_stop_project_server(self.test_project)
        self.assertIn("Stopped server", stop_msg)

    def test_system_instruction_teaches_web_and_multifile(self):
        """Ensure system instructions teach HTML, CSS, JS, React and multi-file structuring workflow."""
        adk = get_adk_engine()
        instruction = adk.build_system_instruction()
        self.assertIn("FULLSTACK WEB DEVELOPMENT & MULTI-FILE STRUCTURING METHODOLOGY", instruction)
        self.assertIn("HTML5", instruction)
        self.assertIn("Modern CSS3", instruction)
        self.assertIn("Modern JavaScript", instruction)
        self.assertIn("React", instruction)
        self.assertIn("aria_write_project_file", instruction)
        self.assertIn("aria_launch_project_server", instruction)

    def test_math_calculator_untouched(self):
        """Ensure E:\\ARIA FILES\\Projects\\Math_Calculator is untouched and preserved."""
        calc_dir = _resolve_safe_path("Projects/Math_Calculator")
        if os.path.exists(calc_dir):
            files = os.listdir(calc_dir)
            self.assertEqual(files, ["calculator.py"], "Math_Calculator project was modified!")


if __name__ == "__main__":
    unittest.main()
