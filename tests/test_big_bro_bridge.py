"""
tests/test_big_bro_bridge.py — Test Suite for Big Bro Antigravity Autonomous Bridge
Verifies:
1. TokenBudgetGuard (Zero token leaks, daily hard caps)
2. BigBroStaticLinter (0-token static AST inspection catching GAIA contract violations)
3. GAIA Smoke Test Compliance for tools/ask_big_bro.py
4. BigBroBridge mailbox operations
"""

import os
import sys
import inspect
import pytest
import tempfile
import json

from core.big_bro_bridge import TokenBudgetGuard, BigBroStaticLinter, BigBroBridge
from tools.ask_big_bro import ask_big_bro, register_tool


def test_gaia_smoke_contract_compliance():
    """Verify ask_big_bro conforms 100% to GAIA's contract rules."""
    res = register_tool()
    assert isinstance(res, tuple) and len(res) == 2
    tool_name, tool_fn = res

    assert tool_name == "ask_big_bro"
    assert callable(tool_fn)
    assert inspect.getdoc(tool_fn) is not None

    sig = inspect.signature(tool_fn)
    for p_name, p in sig.parameters.items():
        # Every parameter MUST have a default value so GAIA smoke tests don't fail!
        assert p.default != inspect.Parameter.empty, f"Parameter {p_name} is missing a default value!"

    # Smoke test execution with dummy string (simulating GAIA harness)
    out = tool_fn("test input, sample idea; spider-man 3.14 https://example.com")
    assert isinstance(out, str)
    assert "Big Bro Antigravity" in out


def test_token_budget_guard():
    """Verify TokenBudgetGuard strictly enforces token limits and resets."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_budget = tf.name

    try:
        guard = TokenBudgetGuard(budget_file=temp_budget, daily_limit=500, max_requests=3)
        
        # 1. Initial check should be allowed
        allowed, reason = guard.can_make_request(estimated_tokens=100)
        assert allowed is True
        assert reason == "OK"

        # 2. Record 200 tokens
        guard.record_usage(200)
        state = guard.load_state()
        assert state["tokens_used"] == 200
        assert state["requests_today"] == 1

        # 3. Requesting 400 tokens should exceed 500 limit
        allowed, reason = guard.can_make_request(estimated_tokens=400)
        assert allowed is False
        assert "token ceiling" in reason.lower()

        # 4. Max requests check
        guard.record_usage(100) # req 2
        guard.record_usage(100) # req 3
        allowed, reason = guard.can_make_request(estimated_tokens=10)
        assert allowed is False
        assert "daily request limit" in reason.lower()
    finally:
        if os.path.exists(temp_budget):
            os.remove(temp_budget)


def test_zero_token_static_linter_catches_bugs():
    """Verify the 0-token static AST linter detects missing defaults, missing docstrings, and unhandled raises."""
    linter = BigBroStaticLinter()

    # Broken tool 1: Missing defaults on parameters and raises ValueError (Aria's exact bug)
    broken_code = '''
def my_bad_math(operation: str, a: float, b: float):
    """Perform math."""
    if operation not in ['add']:
        raise ValueError("Unsupported operation")
    return a + b

def register_tool():
    return "my_bad_math", my_bad_math
'''
    res = linter.lint_code_or_file(broken_code)
    assert res["passed"] is False
    assert res["tokens_used"] == 0
    issues_text = " ".join(res["details"])
    assert "has no default value" in issues_text
    assert "raise ValueError" in issues_text

    # Broken tool 2: Missing register_tool and missing docstring
    broken_code_2 = '''
def add_numbers(x=0, y=0):
    return x + y
'''
    res2 = linter.lint_code_or_file(broken_code_2)
    assert res2["passed"] is False
    issues_text2 = " ".join(res2["details"])
    assert "Missing `def register_tool()" in issues_text2
    assert "missing a docstring" in issues_text2

    # Clean tool: Should pass with flying colors
    clean_code = '''
def clean_calculator(operation: str = "add", a: float = 0.0, b: float = 0.0) -> str:
    """Safe calculator tool for Aria."""
    if operation != "add":
        return "Only add supported"
    return str(a + b)

def register_tool():
    return "clean_calculator", clean_calculator
'''
    res3 = linter.lint_code_or_file(clean_code)
    assert res3["passed"] is True
    assert "PASSED" in res3["summary"]


def test_big_bro_bridge_mailbox():
    """Verify mailbox enqueue and resolve cycle."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_bridge = tf.name

    try:
        bridge = BigBroBridge(bridge_file=temp_bridge)
        msg_id = bridge.enqueue_message(sender="Aria", topic="How to structure a multi-file tool?", status="PENDING_REVIEW")
        
        pending = bridge.get_pending_messages()
        assert len(pending) == 1
        assert pending[0]["id"] == msg_id
        assert pending[0]["topic"] == "How to structure a multi-file tool?"

        # Resolve
        success = bridge.resolve_message(msg_id, "Use modular packages and clean __init__.py files!")
        assert success is True

        pending_after = bridge.get_pending_messages()
        assert len(pending_after) == 0
    finally:
        if os.path.exists(temp_bridge):
            os.remove(temp_bridge)
