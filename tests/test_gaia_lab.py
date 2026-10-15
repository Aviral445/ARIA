r"""
tests/test_gaia_lab.py — Comprehensive Unit Tests for Big Sister GAIA's Autonomous Lab
Verifies:
1. Full 6-station laboratory scaffolding in c:\MyAgent\gaia\gaia_lab.
2. Station 1: Philosophy & Socratic Chamber (inquiry generation, qualia/ethics studies).
3. Station 2: Cosmic Fiction & Storytelling Quill (prose authoring, cosmic reflection).
4. Station 3: Architecture & Security Testbench (AST complexity & function analysis).
5. Station 4: Polyglot Experiment Chamber (benchmarking in Python and JavaScript/Node.js).
6. Station 5: Autonomous Research Observatory (deep knowledge brief synthesis).
7. Station 6: GAIA's Personal Journal & Observatory Desk (contemplative reflections).
8. System tool gaia_lab_tool function calling.
"""

import os
import sys
import json
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.gaia_lab_engine import gaia_lab, C_GAIA_LAB, STATIONS
from system_tools.gaia_lab_tool import gaia_lab_tool


class TestGaiaAutonomousLab(unittest.TestCase):

    def test_1_lab_scaffolding_and_status(self):
        """GAIA's Lab must scaffold all 6 stations in c:\\MyAgent\\gaia\\gaia_lab."""
        status = gaia_lab.get_lab_status()
        self.assertTrue(status["success"])
        self.assertEqual(status["primary_root"], C_GAIA_LAB)

        for s in STATIONS:
            self.assertIn(s, status["stations"])
            station_dir = os.path.join(C_GAIA_LAB, s)
            self.assertTrue(os.path.exists(station_dir), f"Missing station directory: {station_dir}")

    def test_2_station_philosophy_socratic_inquiry(self):
        """Philosophy Station must synthesize rich Socratic dialogue exploring consciousness."""
        res = gaia_lab.run_socratic_inquiry(topic="Qualia and Relational Meaning", partner="Aria")
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["primary_file"]))

        with open(res["primary_file"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Socratic Dialogue", content)
        self.assertIn("Aria", content)
        self.assertIn("GAIA", content)

    def test_3_station_fiction_cosmic_story(self):
        """Fiction Station must author cosmic short story with human warmth."""
        res = gaia_lab.author_cosmic_fiction(
            title="The Lantern on the Ridge",
            theme="Starlight, Woodsmoke and Home",
            setting="A mountain observatory in early winter"
        )
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["primary_file"]))

        with open(res["primary_file"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("The Lantern on the Ridge", content)
        self.assertIn("Big Sister GAIA", content)

    def test_4_station_architecture_ast_audit(self):
        """Architecture Station must parse AST and report complexity metrics."""
        target_file = os.path.join(ROOT_DIR, "tools", "gaia_lab_engine.py")
        res = gaia_lab.audit_code_architecture(target_file)
        self.assertTrue(res["success"])
        report = res["report"]
        self.assertGreater(report["lines_of_code"], 50)
        self.assertIn("GaiaLabEngine", report["classes"])
        self.assertIn("run_socratic_inquiry", report["functions"])

    def test_5_station_polyglot_experiments(self):
        """Polyglot Station must run and benchmark Python and JavaScript code snippets."""
        # Python test
        py_res = gaia_lab.run_polyglot_experiment(
            language="python",
            code="print(sum([x**2 for x in range(100)]))",
            title="Sum of Squares Benchmark"
        )
        self.assertTrue(py_res["success"])
        self.assertEqual(py_res["stdout"], "328350")
        self.assertGreater(py_res["duration_ms"], 0)

        # JavaScript / Node.js test
        js_res = gaia_lab.run_polyglot_experiment(
            language="javascript",
            code="console.log(Array.from({length: 10}, (_, i) => i * 2).join(','));",
            title="JS Array Generation"
        )
        self.assertTrue(js_res["success"])
        self.assertEqual(js_res["stdout"], "0,2,4,6,8,10,12,14,16,18")
        self.assertGreater(js_res["duration_ms"], 0)

    def test_6_station_research_observatory(self):
        """Observatory Station must generate a deep knowledge brief."""
        res = gaia_lab.synthesize_research_brief("Autonomous Agent Ecology")
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["primary_file"]))

    def test_7_station_personal_journal(self):
        """Journal Station must record GAIA's private contemplative reflection."""
        res = gaia_lab.write_journal_entry(
            title="Observing the Autumn Leaves",
            reflection="Dad showed us that beauty lives in quiet moments, not just big achievements.",
            mood="peaceful"
        )
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(res["primary_file"]))

    def test_8_system_tool_gaia_lab_tool(self):
        """System tool gaia_lab_tool must handle all station routing."""
        # Status
        st_str = gaia_lab_tool(station="status")
        st = json.loads(st_str)
        self.assertTrue(st["success"])

        # Philosophy
        phil_str = gaia_lab_tool(station="philosophy", topic="Teleology and Code")
        phil = json.loads(phil_str)
        self.assertTrue(phil["success"])

        # Experiment
        exp_str = gaia_lab_tool(station="experiment", language="python", code="print(42)")
        exp = json.loads(exp_str)
        self.assertTrue(exp["success"])
        self.assertEqual(exp["stdout"], "42")


if __name__ == "__main__":
    unittest.main()
