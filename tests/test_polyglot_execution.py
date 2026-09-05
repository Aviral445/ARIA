"""
tests/test_polyglot_execution.py — Comprehensive Unit Tests for Aria & GAIA Polyglot Architecture
Tests multi-language code detection, execution (Python, JS, TS, Java, PowerShell, Batch),
polyglot safety auditing, error taxonomy, and ADK tool execution.
"""

import os
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gaia.gaia_runner import (
    detect_language_from_code,
    run_polyglot_code,
    resolve_execution_command,
    ExecutionResult
)
from gaia.gaia_safety import audit_code_safety
from gaia.gaia_rl import classify_error_title
from core.aria_adk import run_sandbox_code, build_sandbox_tool


def test_detect_language_from_code():
    """Verify intelligent multi-language source code detection."""
    # Python
    py_code = "def calculate_sum(a, b):\n    return a + b\nprint(calculate_sum(2, 3))"
    assert detect_language_from_code(py_code) == "python"

    # JavaScript
    js_code = "const greeting = 'Hello world';\nconsole.log(greeting);"
    assert detect_language_from_code(js_code) == "javascript"

    # TypeScript
    ts_code = "interface User {\n  id: number;\n  name: string;\n}\nconst u: User = { id: 1, name: 'Aria' };\nconsole.log(u.name);"
    assert detect_language_from_code(ts_code) == "typescript"

    # Java
    java_code = "public class Hello {\n    public static void main(String[] args) {\n        System.out.println(\"Hello from Java\");\n    }\n}"
    assert detect_language_from_code(java_code) == "java"

    # PowerShell
    ps_code = "$message = 'PowerShell running'\nWrite-Output $message"
    assert detect_language_from_code(ps_code) == "powershell"

    # Windows Batch
    bat_code = "@echo off\necho Batch file execution"
    assert detect_language_from_code(bat_code) == "batch"

    # Bash / Shell
    sh_code = "#!/bin/bash\nif [ 1 -eq 1 ]; then\n  echo 'Bash verified'\nfi"
    assert detect_language_from_code(sh_code) == "bash"


def test_polyglot_execution_python():
    """Verify sandboxed execution of Python code."""
    code = "x = 10 * 5\nprint(f'POLYGLOT_PY_RESULT: {x}')"
    res = run_polyglot_code(code, language="python", timeout_sec=10)
    assert res.success is True
    assert "POLYGLOT_PY_RESULT: 50" in res.stdout
    assert res.language == "python"


def test_polyglot_execution_javascript():
    """Verify sandboxed execution of JavaScript code via Node.js."""
    code = "const val = 12 * 12;\nconsole.log(`POLYGLOT_JS_RESULT: ${val}`);"
    res = run_polyglot_code(code, language="javascript", timeout_sec=10)
    assert res.success is True
    assert "POLYGLOT_JS_RESULT: 144" in res.stdout
    assert res.language == "javascript"


def test_polyglot_execution_typescript():
    """Verify sandboxed execution of TypeScript code via Node 22 native type stripping."""
    code = "const double = (n: number): number => n * 2;\nconsole.log(`POLYGLOT_TS_RESULT: ${double(21)}`);"
    res = run_polyglot_code(code, language="typescript", timeout_sec=10)
    assert res.success is True
    assert "POLYGLOT_TS_RESULT: 42" in res.stdout
    assert res.language == "typescript"


def test_polyglot_execution_java():
    """Verify sandboxed execution of Java 25 single-source code."""
    code = (
        "public class AriaJavaTest {\n"
        "    public static void main(String[] args) {\n"
        "        System.out.println(\"POLYGLOT_JAVA_RESULT: \" + (100 / 4));\n"
        "    }\n"
        "}"
    )
    res = run_polyglot_code(code, language="java", timeout_sec=15)
    assert res.success is True
    assert "POLYGLOT_JAVA_RESULT: 25" in res.stdout
    assert res.language == "java"


def test_polyglot_execution_powershell():
    """Verify sandboxed execution of PowerShell script."""
    code = "$n = 7 * 7\nWrite-Output \"POLYGLOT_PS_RESULT: $n\""
    res = run_polyglot_code(code, language="powershell", timeout_sec=10)
    assert res.success is True
    assert "POLYGLOT_PS_RESULT: 49" in res.stdout
    assert res.language == "powershell"


def test_polyglot_execution_batch():
    """Verify sandboxed execution of Windows Batch script."""
    code = "@echo off\necho POLYGLOT_BAT_RESULT: 777"
    res = run_polyglot_code(code, language="batch", timeout_sec=10)
    assert res.success is True
    assert "POLYGLOT_BAT_RESULT: 777" in res.stdout
    assert res.language == "batch"


def test_polyglot_safety_guardrails():
    """Verify polyglot static safety checks block dangerous commands across languages."""
    sandbox_dir = os.path.join(ROOT_DIR, "gaia", "sandbox")

    # Safe JavaScript
    safe_js = "console.log('Safe math: ' + Math.sqrt(16));"
    report = audit_code_safety(safe_js, sandbox_dir, language="javascript")
    assert report.is_safe is True

    # Dangerous JavaScript attempting disk format
    bad_js = "const exec = require('child_process').exec;\nexec('format C: /y');"
    report_bad = audit_code_safety(bad_js, sandbox_dir, language="javascript")
    assert report_bad.is_safe is False
    assert any("format" in v.lower() for v in report_bad.violations)

    # Dangerous PowerShell attempting root deletion
    bad_ps = "Remove-Item -Recurse -Force C:\\Windows"
    report_ps = audit_code_safety(bad_ps, sandbox_dir, language="powershell")
    assert report_ps.is_safe is False

    # Unauthorized access to root .env
    bad_env_read = "const fs = require('fs');\nfs.readFileSync('../.env');"
    report_env = audit_code_safety(bad_env_read, sandbox_dir, language="javascript")
    assert report_env.is_safe is False
    assert any(".env" in v for v in report_env.violations)


def test_polyglot_error_taxonomy():
    """Verify classify_error_title categorizes multi-language errors."""
    # JavaScript ReferenceError
    assert classify_error_title("ReferenceError: myVar is not defined") == "UndefinedVariableError"

    # JavaScript TypeError
    assert classify_error_title("TypeError: obj.run is not a function") == "TypeMismatchError"

    # Java NullPointerException
    assert classify_error_title("java.lang.NullPointerException: Cannot invoke method on null object") == "NullPointerDereferenceError"

    # Java compilation error
    assert classify_error_title("Test.java:4: error: cannot find symbol") == "CompilationError"

    # Python ZeroDivisionError
    assert classify_error_title("ZeroDivisionError: division by zero") == "ZeroDivisionError"


def test_aria_adk_run_sandbox_code_polyglot():
    """Verify Aria's run_sandbox_code ADK tool supports multiple languages and auto-detection."""
    # JavaScript via ADK tool
    js_tool_out = run_sandbox_code("console.log('ADK_JS_SUCCESS');", language="javascript")
    assert "executed successfully" in js_tool_out.lower()
    assert "ADK_JS_SUCCESS" in js_tool_out

    # Auto-detected TypeScript via ADK tool
    ts_snippet = "const ans: number = 99; console.log(`ADK_TS_SUCCESS: ${ans}`);"
    ts_tool_out = run_sandbox_code(ts_snippet, language="auto")
    assert "executed successfully" in ts_tool_out.lower()
    assert "ADK_TS_SUCCESS: 99" in ts_tool_out

    # Python via ADK tool
    py_snippet = "print('ADK_PY_SUCCESS')"
    py_tool_out = run_sandbox_code(py_snippet)
    assert "executed successfully" in py_tool_out.lower()
    assert "ADK_PY_SUCCESS" in py_tool_out
