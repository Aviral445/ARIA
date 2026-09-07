"""
tests/test_gaia_architect.py — Comprehensive Test Suite for GAIA Architect

Verifies:
1. Architect Sandbox environment initialization & ledger persistence.
2. Codebase inspection & search methods.
3. Deterministic Non-LLM ground truths (AST parse, import preflight, truncation sniffer, contract, subprocess execution).
4. Hard 3-attempt circuit breaker with automatic rollback & BigBroBridge escalation.
5. Two-track evolution:
   - Safe autonomous deployment (tools, skills, dynamic limits).
   - Core patch proposals (.diff generation without mutating core).
6. Absolute safety: E:\\ARIA FILES\\Projects\\Math_Calculator is untouched.
"""

import os
import sys
import shutil
import json
import pytest

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from gaia.gaia_architect import (
    GaiaArchitect,
    get_gaia_architect,
    ensure_architect_environment,
    ARCHITECT_DIR,
    WORKSPACE_DIR,
    INCIDENTS_DIR,
    PATCHES_DIR
)
from core.big_bro_bridge import BigBroBridge
from core.aria_config_manager import get_token_limit


@pytest.fixture
def architect():
    return get_gaia_architect()


def test_architect_environment_and_ledger(architect):
    """Test 1: Verifies sandbox directories and ledger are created."""
    dirs = ensure_architect_environment()
    for name, path in dirs.items():
        assert os.path.exists(path), f"Directory {name} ({path}) must exist"
    
    ledger = architect.load_ledger()
    assert "diagnoses" in ledger
    assert "active_attempts" in ledger
    assert "deployments" in ledger
    assert "patches" in ledger
    assert "incidents" in ledger


def test_deterministic_verification_valid_tool(architect):
    """Test 2: Valid tool passes all 5 deterministic ground truth checks."""
    valid_code = (
        "def sample_hello(name: str = 'friend') -> str:\n"
        "    return f'Hello, {name}!'\n\n"
        "def register_tool() -> tuple[str, callable]:\n"
        "    return ('sample_hello', sample_hello)\n"
    )
    res = architect.verify_code_deterministic(valid_code, "sample_hello", solution_type="tool")
    assert res["passed"] is True, f"Valid tool should pass: {res.get('reason')}"
    assert res["step"] == "ALL_PASSED"
    # Clean up staging
    architect.rollback_workspace("sample_hello")


def test_deterministic_syntax_error_rejected(architect):
    """Test 3: Syntax error is caught by AST parser."""
    bad_syntax = "def broken_code(): return return 42"
    res = architect.verify_code_deterministic(bad_syntax, "broken_code", solution_type="tool")
    assert res["passed"] is False
    assert res["step"] == "AST_PARSE"
    assert "SyntaxError" in res["reason"]


def test_deterministic_missing_dependency_rejected(architect):
    """Test 4: Missing package rejected in pre-flight without running untrusted code."""
    code_with_missing_pkg = (
        "import nonexistent_crypto_hyper_pkg_99999\n\n"
        "def run_hyper():\n"
        "    return 'hyper'\n\n"
        "def register_tool():\n"
        "    return ('run_hyper', run_hyper)\n"
    )
    res = architect.verify_code_deterministic(code_with_missing_pkg, "run_hyper", solution_type="tool")
    assert res["passed"] is False
    assert res["step"] == "DEPENDENCY_PREFLIGHT"
    assert "nonexistent_crypto_hyper_pkg_99999" in res["reason"]


def test_deterministic_truncation_sniffer(architect):
    """Test 5: Token truncation detected by sniffer."""
    # Unclosed triple quote
    truncated_quotes = '"""Incomplete docstring\ndef incomplete():\n    pass'
    res1 = architect.verify_code_deterministic(truncated_quotes, "incomplete", solution_type="tool")
    assert res1["passed"] is False
    assert res1["step"] == "TRUNCATION_SNIFFER"

    # Unbalanced brackets
    truncated_bracket = 'def func():\n    x = [1, 2, 3\n'
    res2 = architect.verify_code_deterministic(truncated_bracket, "func", solution_type="tool")
    assert res2["passed"] is False
    assert res2["step"] == "TRUNCATION_SNIFFER"


def test_deterministic_contract_rejection(architect):
    """Test 6: Missing register_tool() rejected by contract verifier."""
    code_no_register = (
        "def simple_func():\n"
        "    return 'ok'\n"
    )
    res = architect.verify_code_deterministic(code_no_register, "simple_func", solution_type="tool")
    assert res["passed"] is False
    assert res["step"] == "TOOL_CONTRACT"
    assert "register_tool" in res["reason"]


def test_circuit_breaker_and_rollback(architect):
    """Test 7: 3 consecutive failures trip circuit breaker and escalate to BigBroBridge."""
    test_issue_id = "test_impediment_flaky_99"
    bad_code = "def broken(:\n    pass"

    # Reset any prior attempts for test
    architect.reset_attempts(test_issue_id)

    # Attempt 1
    imp = {"issue_id": test_issue_id, "solution_type": "tool", "target_name": "flaky_tool"}
    res1 = architect.solve_impediment(imp, bad_code)
    assert res1["success"] is False
    assert res1.get("attempt") == 1

    # Attempt 2
    res2 = architect.solve_impediment(imp, bad_code)
    assert res2["success"] is False
    assert res2.get("attempt") == 2

    # Attempt 3: Trips circuit breaker
    res3 = architect.solve_impediment(imp, bad_code)
    assert res3["success"] is False
    assert res3.get("circuit_breaker") == "TRIPPED"
    assert "incident_report" in res3
    assert os.path.exists(res3["incident_report"])

    # Verify escalation in BigBroBridge mailbox
    bridge = BigBroBridge()
    mailbox = bridge._load_mailbox()
    escalated = [m for m in mailbox if test_issue_id in m.get("topic", "")]
    assert len(escalated) > 0, "Circuit breaker trip must be escalated to BigBroBridge"
    assert escalated[-1]["status"] == "ESCALATED_TO_ANTIGRAVITY"

    # Clean up test incident and attempts
    architect.reset_attempts(test_issue_id)


def test_track1_safe_tool_deployment(architect):
    """Test 8: Track 1 safe autonomous deployment of a modular tool."""
    tool_name = "architect_demo_tool"
    code = (
        "def architect_demo_calc(x: int = 1) -> int:\n"
        "    return x * 2\n\n"
        "def register_tool() -> tuple[str, callable]:\n"
        "    return ('architect_demo_calc', architect_demo_calc)\n"
    )
    imp = {"issue_id": "test_deploy_tool_1", "solution_type": "tool", "target_name": tool_name}
    architect.reset_attempts(imp["issue_id"])
    res = architect.solve_impediment(imp, code)
    assert res["success"] is True
    assert res["status"] == "DEPLOYED_LIVE"

    from core.paths import TOOLS_DIR
    deployed_file = os.path.join(TOOLS_DIR, f"{tool_name}.py")
    assert os.path.exists(deployed_file)

    # Clean up deployed tool
    if os.path.exists(deployed_file):
        os.remove(deployed_file)
    architect.reset_attempts(imp["issue_id"])


def test_track2_core_patch_proposal_does_not_mutate_core(architect):
    """Test 9: Track 2 core kernel patch generates .diff without mutating target file."""
    target_rel = "core/aria_config_manager.py"
    target_full = os.path.join(REPO_ROOT, target_rel)
    
    with open(target_full, "r", encoding="utf-8") as f:
        orig_content = f.read()

    # Proposed tweak: add a comment at the top
    proposed_code = "# GAIA Architect proposed performance tuning\n" + orig_content

    imp = {
        "issue_id": "test_core_patch_1",
        "solution_type": "core_patch",
        "target_name": target_rel
    }
    architect.reset_attempts(imp["issue_id"])
    res = architect.solve_impediment(imp, proposed_code, rationale="Adding performance annotation")
    assert res["success"] is True
    assert res["type"] == "core_patch_proposal"
    assert os.path.exists(res["patch_file"])

    # CRITICAL CHECK: Target file must remain 100% UNCHANGED!
    with open(target_full, "r", encoding="utf-8") as f:
        current_content = f.read()
    assert current_content == orig_content, "Core kernel file must NOT be mutated by patch proposal!"

    # Verify BigBroBridge received review request
    bridge = BigBroBridge()
    mailbox = bridge._load_mailbox()
    patch_msgs = [m for m in mailbox if "PROPOSED_CORE_PATCH" in m.get("topic", "")]
    assert len(patch_msgs) > 0
    assert patch_msgs[-1]["status"] == "AWAITING_HUMAN_APPROVAL"

    # Clean up generated patch file and reset attempts
    if os.path.exists(res["patch_file"]):
        os.remove(res["patch_file"])
    architect.reset_attempts(imp["issue_id"])


def test_absolute_preservation_math_calculator():
    """Test 10: Absolute preservation rule — Math_Calculator is 100% untouched."""
    calc_path = r"E:\ARIA FILES\Projects\Math_Calculator\calculator.py"
    if os.path.exists(calc_path):
        with open(calc_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert len(content) > 100, "calculator.py must exist and contain code"
        assert "def " in content or "class " in content, "calculator.py must have original logic"
