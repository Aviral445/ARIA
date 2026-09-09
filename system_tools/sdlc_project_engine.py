r"""
system_tools/sdlc_project_engine.py — Autonomous Big-Project SDLC Tool for Aria & GAIA

Exposes the 4-Part Autonomous Engineering Architecture in E:\ARIA FILES:
  • Part 1: Ingestion & Google Deep Research ──> Project Database / State Ledger
  • Part 2: Blueprints & Architecture Scaffolding in E:\ARIA FILES\Projects\<Project_Name>
  • Part 3: GAIA's Independent QA Suite (Red-Green TDD Verification Gate & Test Immutability)
  • Part 4: Autonomous TDD & 5-Tries Escalation Ladder (Subprocess isolation, Diagnostic Delta retries,
            Big Bro Antigravity escalation, and Dad Escalation Card)
  • Post-Completion: Distills insights to ChromaDB memory and executes Clean Slate Teardown.
"""

import os
import sys
import json
from typing import Optional, Dict, Any

# Ensure project root is accessible
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.aria_sdlc_engine import get_sdlc_engine


def sdlc_project_engine(
    action: str = "status",
    project_name: str = "",
    topic: str = "",
    code: str = "",
    options: Optional[Dict[str, Any]] = None
) -> str:
    r"""
    Autonomous Big-Project SDLC Lifecycle Tool for Aria and GAIA.
    Enforces the single-project concurrency rule, physical disk grounding ("receipts"),
    and Windows filesystem safety laws in E:\ARIA FILES\Projects\.

    Args:
        action: Operational verb:
            • 'status': Check the active concurrency lock and project progress.
            • 'start' / 'run': Execute full autonomous pipeline (Parts 1 to 4 + Clean Slate).
            • 'ingest' / 'research': Run Part 1 (Deep technical research and project ledger).
            • 'scaffold' / 'blueprints': Run Part 2 (Directory structure, architecture, checklists).
            • 'qa_suite' / 'test_gate': Run Part 3 (GAIA independent test suite & Red-Green gate).
            • 'tdd_cycle' / 'build': Run Part 4 (Aria 5-tries TDD loop with 30s isolated subprocess).
            • 'clean_slate' / 'teardown': Decommission ephemeral ADKs and scratch docs.
            • 'cancel' / 'release_lock': Safely release active lock if needed.

        project_name: Target project name (e.g. 'Audio_Visualizer', 'Market_Analyzer').
        topic: Detailed technical topic or requirements prompt.
        code: Custom Python implementation or test code string (optional).
        options: Optional dictionary or JSON string for additional parameters.

    Returns:
        str: JSON-formatted execution report or error message.
    """
    act = (action or "status").lower().strip()
    engine = get_sdlc_engine()

    opts = options or {}
    if isinstance(opts, str):
        try:
            opts = json.loads(opts)
        except Exception:
            opts = {}

    try:
        # 1. STATUS & CONCURRENCY LOCK CHECK
        if act in ("status", "lock_status", "check"):
            status = engine.get_lock_status()
            return json.dumps(status, indent=2)

        elif act in ("cancel", "release_lock", "unlock"):
            reason = opts.get("reason", "MANUAL_OVERRIDE")
            success = engine.release_lock(reason=reason)
            return json.dumps({
                "success": success,
                "action": "release_lock",
                "message": "🔒 Concurrency Lock released." if success else "No active lock found."
            }, indent=2)

        # 2. FULL AUTONOMOUS PIPELINE
        elif act in ("start", "run", "execute_full"):
            if not project_name:
                return "Error: Please specify 'project_name' to run the SDLC pipeline."
            if not topic:
                topic = f"Enterprise Autonomous Implementation of {project_name}"

            # Acquire single-project concurrency lock
            locked, lock_msg = engine.acquire_lock(project_name=project_name, topic=topic)
            if not locked:
                return json.dumps({"success": False, "error": lock_msg}, indent=2)

            reports = {}

            # Part 1: Ingestion & Deep Research
            p1_res = engine.run_deep_research(topic=topic, project_name=project_name)
            reports["part_1_ingestion"] = p1_res
            if not p1_res.get("success"):
                engine.release_lock(reason="FAILED_PART_1")
                return json.dumps({"success": False, "error": "Part 1 failed", "details": p1_res}, indent=2)

            # Part 2: Blueprints & Architecture Scaffolding
            p2_res = engine.scaffold_blueprints(project_name=project_name, topic=topic)
            reports["part_2_blueprints"] = p2_res
            if not p2_res.get("success"):
                engine.release_lock(reason="FAILED_PART_2")
                return json.dumps({"success": False, "error": "Part 2 failed", "details": p2_res}, indent=2)

            # Part 3: GAIA Independent QA Suite (Red-Green TDD Gate)
            test_code = opts.get("test_code") or (code if "def test_" in code else None)
            p3_res = engine.gaia_create_independent_qa(project_name=project_name, test_code=test_code)
            reports["part_3_qa_suite"] = p3_res
            if not p3_res.get("success"):
                engine.release_lock(reason="FAILED_PART_3_RED_GATE")
                return json.dumps({"success": False, "error": "Part 3 Red-Green Gate failed", "details": p3_res}, indent=2)

            # Part 4: Autonomous TDD & 5-Tries Escalation
            impl_code = opts.get("implementation_code") or (code if "def test_" not in code and code else None)
            p4_res = engine.aria_autonomous_tdd_cycle(project_name=project_name, implementation_code=impl_code)
            reports["part_4_tdd_cycle"] = p4_res

            return json.dumps({
                "success": p4_res.get("success", False),
                "project_name": project_name,
                "reports": reports
            }, indent=2)

        # 3. INDIVIDUAL STAGES
        elif act in ("ingest", "research", "part_1"):
            if not project_name:
                return "Error: Please specify 'project_name'."
            res = engine.run_deep_research(topic=topic or project_name, project_name=project_name)
            return json.dumps(res, indent=2)

        elif act in ("scaffold", "blueprints", "part_2"):
            if not project_name:
                return "Error: Please specify 'project_name'."
            res = engine.scaffold_blueprints(project_name=project_name, topic=topic)
            return json.dumps(res, indent=2)

        elif act in ("qa_suite", "test_gate", "part_3"):
            if not project_name:
                return "Error: Please specify 'project_name'."
            res = engine.gaia_create_independent_qa(project_name=project_name, test_code=code or None)
            return json.dumps(res, indent=2)

        elif act in ("tdd_cycle", "build", "part_4"):
            if not project_name:
                return "Error: Please specify 'project_name'."
            res = engine.aria_autonomous_tdd_cycle(project_name=project_name, implementation_code=code or None)
            return json.dumps(res, indent=2)

        elif act in ("clean_slate", "teardown"):
            if not project_name:
                return "Error: Please specify 'project_name'."
            res = engine.clean_slate_teardown(project_name=project_name)
            return json.dumps(res, indent=2)

        else:
            return f"Error: Unknown action '{action}'. Valid actions: status, start, ingest, scaffold, qa_suite, tdd_cycle, clean_slate, cancel."

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)
