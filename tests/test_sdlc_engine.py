r"""
tests/test_sdlc_engine.py — Comprehensive Unit & Integration Tests for Autonomous SDLC Engine

Verifies:
  1. Concurrency Lock & Single-Project Rule ("One project at a time")
  2. Windows Filesystem Safety (sanitization of reserved device names, invalid characters)
  3. Part 1: Ingestion & Google Deep Research (Brief & State Ledger)
  4. Part 2: Blueprints Scaffolding (Directory topology, Architecture, Checklists)
  5. Part 3: GAIA's Independent QA Suite (Red-Green TDD Gate & Immutability)
  6. Part 4: Autonomous TDD (30s isolated subprocess runner & Clean Slate Teardown)
  7. 5-Tries Escalation Ladder (Big Bro Antigravity & Dad Escalation Card)
  8. GAIA Supervisor Incident Handler Integration
  9. System Tool Function-Calling Wrapper (sdlc_project_engine)
"""

import os
import sys
import stat
import json
import shutil
import tempfile
import pytest

# Ensure root is on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.aria_sdlc_engine import (
    AriaSDLCEngine,
    _sanitize_project_name,
    CONCURRENCY_LOCK_FILE,
    DAD_ESCALATIONS_FILE,
    PROJECT_INSIGHTS_FILE
)
from system_tools.sdlc_project_engine import sdlc_project_engine
from gaia.gaia_supervisor import supervisor


def _remove_readonly(func, path, excinfo):
    """Clear the read-only bit on Windows and re-attempt removal."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


@pytest.fixture
def temp_engine():
    """Provides an isolated AriaSDLCEngine instance with a temporary workspace."""
    temp_dir = tempfile.mkdtemp(prefix="aria_sdlc_test_")
    engine = AriaSDLCEngine(projects_root=temp_dir)
    # Ensure lock is clear initially
    engine.release_lock(reason="TEST_CLEANUP")
    yield engine
    # Cleanup
    engine.release_lock(reason="TEST_CLEANUP")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, onerror=_remove_readonly)


class TestWindowsSafetyAndSanitization:
    """Test Windows filesystem safety rules and reserved device names."""

    def test_sanitize_windows_reserved_names(self):
        assert _sanitize_project_name("CON") == "Proj_CON"
        assert _sanitize_project_name("prn") == "Proj_prn"
        assert _sanitize_project_name("aux.txt") == "Proj_aux.txt"
        assert _sanitize_project_name("NUL") == "Proj_NUL"
        assert _sanitize_project_name("COM1") == "Proj_COM1"

    def test_sanitize_invalid_characters(self):
        assert _sanitize_project_name("Audio:Player/Visualizer?") == "Audio_Player_Visualizer"
        assert _sanitize_project_name("   Project...   ") == "Project"
        assert _sanitize_project_name("") == "Unnamed_Project"


class TestConcurrencyLock:
    """Test the single-project concurrency lock mechanism."""

    def test_acquire_and_release_lock(self, temp_engine):
        # Initial status
        status = temp_engine.get_lock_status()
        assert not status.get("is_locked")

        # Acquire lock for Project A
        ok, msg = temp_engine.acquire_lock("Project_Alpha", "Alpha Topic")
        assert ok
        assert "Lock successfully acquired" in msg

        status = temp_engine.get_lock_status()
        assert status.get("is_locked")
        assert status.get("active_project") == "Project_Alpha"

        # Try to acquire lock for Project B while Project A is active — MUST BE REJECTED!
        ok2, msg2 = temp_engine.acquire_lock("Project_Beta", "Beta Topic")
        assert not ok2
        assert "Concurrency Lock Active" in msg2

        # Re-acquiring for Project A should be permitted (same project)
        ok_same, _ = temp_engine.acquire_lock("Project_Alpha")
        assert ok_same

        # Release lock
        released = temp_engine.release_lock(reason="COMPLETED")
        assert released
        status_after = temp_engine.get_lock_status()
        assert not status_after.get("is_locked")


class TestSDLCPhase1To3:
    """Test Ingestion, Scaffolding, and GAIA's Independent QA Suite."""

    def test_part_1_ingestion_and_deep_research(self, temp_engine):
        res = temp_engine.run_deep_research(
            topic="Fast Fourier Transform Audio Analyzer",
            project_name="Audio_Analyzer"
        )
        assert res.get("success")
        assert os.path.exists(res["brief_path"])
        assert os.path.exists(res["spec_path"])
        assert os.path.exists(res["ledger_path"])

        # Physical Grounding ("Receipt Rule") verification
        assert os.path.getsize(res["brief_path"]) > 50
        with open(res["ledger_path"], "r", encoding="utf-8") as f:
            ledger = json.load(f)
            assert ledger["project_name"] == "Audio_Analyzer"
            assert ledger["status"] == "INGESTED"

    def test_part_2_blueprints_scaffolding(self, temp_engine):
        res = temp_engine.scaffold_blueprints("Audio_Analyzer", "Audio DSP Tooling")
        assert res.get("success")
        proj_dir = res["project_dir"]

        # Check required topology
        for sub in ["docs", "src", "tests", "adks", "database"]:
            assert os.path.isdir(os.path.join(proj_dir, sub))

        # Check key scaffolded files
        assert os.path.exists(os.path.join(proj_dir, "docs", "ARCHITECTURE.md"))
        assert os.path.exists(os.path.join(proj_dir, "docs", "TASK_LIST.md"))
        assert os.path.exists(os.path.join(proj_dir, "docs", "CHECKLIST.md"))
        assert os.path.exists(os.path.join(proj_dir, "src", "__init__.py"))

    def test_part_3_gaia_qa_red_green_gate(self, temp_engine):
        # Scaffold blueprints first
        temp_engine.scaffold_blueprints("Audio_Analyzer")

        # Big Sister GAIA authors QA suite
        # It MUST fail initially because src/ has not been implemented yet!
        res = temp_engine.gaia_create_independent_qa("Audio_Analyzer")
        assert res.get("success"), f"Red-Green Gate setup failed: {res}"
        assert res.get("red_verified") is True
        assert os.path.exists(res["test_path"])

        # Test Immutability: Verify test file is marked read-only
        test_path = res["test_path"]
        mode = os.stat(test_path).st_mode
        # On Windows, read-only means write permissions are disabled
        assert not (mode & stat.S_IWUSR)

        # Clear read-only so subsequent teardown works
        os.chmod(test_path, stat.S_IWRITE)

    def test_part_3_rejects_tautological_test(self, temp_engine):
        temp_engine.scaffold_blueprints("Tautology_Proj")
        # Provide a tautological test that passes without checking anything
        tautology_code = "def test_tautology():\n    assert True\n"
        res = temp_engine.gaia_create_independent_qa("Tautology_Proj", test_code=tautology_code)
        # MUST BE REJECTED!
        assert not res.get("success")
        assert "Red-Green Gate Violation" in res.get("error", "")


class TestSDLCPhase4TDDAndCleanSlate:
    """Test Autonomous TDD, Subprocess Isolation, Escalation, and Clean Slate Teardown."""

    def test_part_4_successful_green_tdd_and_clean_slate(self, temp_engine):
        proj_name = "Success_Project"
        temp_engine.acquire_lock(proj_name)
        temp_engine.run_deep_research("Modular Parser", proj_name)
        temp_engine.scaffold_blueprints(proj_name)
        temp_engine.gaia_create_independent_qa(proj_name)

        # Aria builds implementation satisfying the GAIA test contract
        impl_code = (
            'def execute_task(task_type="health_check") -> dict:\n'
            '    return {"status": "SUCCESS", "receipt": "PHYSICAL_DISK_VERIFIED", "task": task_type}\n'
        )
        tdd_res = temp_engine.aria_autonomous_tdd_cycle(proj_name, implementation_code=impl_code)
        assert tdd_res.get("success")
        assert tdd_res.get("verdict") == "PASSED_GREEN"
        assert tdd_res.get("attempts") == 1

        # Verify clean slate: production src/ is preserved
        proj_dir = os.path.join(temp_engine.projects_root, proj_name)
        assert os.path.exists(os.path.join(proj_dir, "src", "main_module.py"))

        # Verify concurrency lock was released
        assert not temp_engine.get_lock_status().get("is_locked")

        # Verify insights saved
        assert os.path.exists(PROJECT_INSIGHTS_FILE)

    def test_part_4_escalation_ladder_after_5_failures(self, temp_engine):
        proj_name = "Impasse_Project"
        temp_engine.acquire_lock(proj_name)
        temp_engine.scaffold_blueprints(proj_name)
        temp_engine.gaia_create_independent_qa(proj_name)

        # Provide intentionally broken code that will never pass
        broken_code = "def execute_task(task_type):\n    raise RuntimeError('Persistent failure!')\n"
        tdd_res = temp_engine.aria_autonomous_tdd_cycle(proj_name, implementation_code=broken_code, max_tries=5)

        # After 5 tries, should escalate to Dad Escalation Card
        assert not tdd_res.get("success")
        assert tdd_res.get("verdict") == "ESCALATED_TO_DAD"
        assert "dad_escalation_card" in tdd_res

        card = tdd_res["dad_escalation_card"]
        assert card.get("project_name") == proj_name
        assert card.get("total_attempts") == 5

        # Check dad_escalations.json
        assert os.path.exists(DAD_ESCALATIONS_FILE)


class TestGAIASupervisorIncidentHandler:
    """Test Big Sister GAIA's supervise_adk_incident handler."""

    def test_gaia_auto_heal_on_early_attempts(self):
        incident = {
            "adk_id": "Data_Parser_ADK",
            "incident_type": "SYNTAX_ERROR",
            "description": "SyntaxError: invalid syntax on line 12",
            "severity": "MEDIUM",
            "context": {"attempts": 1}
        }
        res = supervisor.supervise_adk_incident(incident)
        assert not res.get("resolved")
        assert res.get("action") == "AUTO_HEAL"
        assert res.get("stage") == "GAIA_SUPERVISED"
        assert "Auto-Heal Directive" in res.get("prescription", "")

    def test_gaia_big_bro_escalation_on_attempt_3(self):
        incident = {
            "adk_id": "Data_Parser_ADK",
            "incident_type": "CONTRACT_VIOLATION",
            "description": "Smoke test failed: missing return value",
            "severity": "HIGH",
            "context": {"attempts": 3, "code_snippet": "def run(): pass"}
        }
        res = supervisor.supervise_adk_incident(incident)
        assert res.get("action") == "ESCALATED_BIG_BRO"
        assert res.get("stage") == "BIG_BRO_ANTIGRAVITY"
        assert "Big Bro Antigravity" in res.get("prescription", "")

    def test_gaia_dad_escalation_on_attempt_5(self):
        incident = {
            "adk_id": "Data_Parser_ADK",
            "incident_type": "UNRESOLVED_IMPASSE",
            "description": "Exhausted 5 attempts without convergence",
            "severity": "HIGH",
            "context": {"attempts": 5}
        }
        res = supervisor.supervise_adk_incident(incident)
        assert res.get("action") == "ESCALATED_DAD"
        assert res.get("stage") == "DAD_MENTOR"
        assert "card" in res
        assert res["card"]["adk_id"] == "Data_Parser_ADK"


class TestSystemToolWrapper:
    """Test system_tools/sdlc_project_engine.py callable interface."""

    def test_tool_status_and_lock_release(self):
        status_raw = sdlc_project_engine(action="status")
        status = json.loads(status_raw)
        assert "is_locked" in status

        cancel_raw = sdlc_project_engine(action="cancel")
        cancel_res = json.loads(cancel_raw)
        assert cancel_res.get("success") is not None
