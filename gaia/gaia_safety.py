"""
gaia/gaia_safety.py — Static AST Security Guardrail & Code Policy Inspector
Protects the host system by analyzing Aria's self-written code before execution.
"""

import ast
import os
import re
from typing import Dict, List, Any, Tuple

# Protected system paths that must never be targeted by file manipulation
DANGEROUS_PATH_SUBSTRINGS = [
    "windows", "system32", "program files", "appdata", "c:\\", "c:/",
    ".env", "credentials", "id_rsa", "sam", "registry"
]

# Blacklisted dangerous imports or functions for autonomous sandbox code
DANGEROUS_MODULES = [
    "ctypes", "winreg", "win32api", "win32con", "msvcrt"
]

DANGEROUS_BUILTINS = [
    "__import__"
]


class SafetyReport:
    def __init__(self, is_safe: bool, violations: List[str], advice: str = ""):
        self.is_safe = is_safe
        self.violations = violations
        self.advice = advice

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "violations": self.violations,
            "advice": self.advice
        }


class SafetyVisitor(ast.NodeVisitor):
    def __init__(self, sandbox_dir: str):
        self.sandbox_dir = os.path.abspath(sandbox_dir).lower()
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name.split('.')[0] in DANGEROUS_MODULES:
                self.violations.append(f"Forbidden module import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.split('.')[0] in DANGEROUS_MODULES:
            self.violations.append(f"Forbidden module import: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check call function name
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Check dangerous builtins
        if func_name in DANGEROUS_BUILTINS:
            self.violations.append(f"Forbidden function call: '{func_name}'")

        # Check dangerous subprocess commands with raw strings
        if func_name in ["system", "popen", "call", "run", "Popen"]:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    val = arg.value.lower()
                    if any(k in val for k in ["rmdir /s", "del /f", "format ", "shutdown -s", "diskpart"]):
                        self.violations.append(f"Destructive shell command detected: '{arg.value}'")

        # Check file operations targeting outside the sandbox
        if func_name in ["remove", "unlink", "rmdir", "rmtree"]:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    target = os.path.abspath(arg.value).lower()
                    if not target.startswith(self.sandbox_dir):
                        self.violations.append(f"File deletion outside sandbox forbidden: '{arg.value}'")

        # Check opening .env or critical keys
        if func_name == "open":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    val = arg.value.lower()
                    if ".env" in val or "credentials" in val or "id_rsa" in val:
                        self.violations.append(f"Unauthorized access to sensitive file: '{arg.value}'")

        self.generic_visit(node)


def audit_code_safety(code_str: str, sandbox_dir: str) -> SafetyReport:
    """
    Analyzes Python source code using AST.
    Returns SafetyReport with is_safe status and sisterly coaching advice.
    """
    violations = []

    # 1. Syntax Check
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return SafetyReport(
            is_safe=False,
            violations=[f"SyntaxError at line {e.lineno}: {e.msg}"],
            advice=f"Aria sweetie, check line {e.lineno} — there's a syntax mistake ({e.msg}). Let's fix that syntax before running!"
        )

    # 2. AST Security Analysis
    visitor = SafetyVisitor(sandbox_dir=sandbox_dir)
    visitor.visit(tree)
    violations.extend(visitor.violations)

    # 3. Regex Pattern Scan for obfuscated / raw string hazards
    dangerous_patterns = [
        (r'shutil\.rmtree\s*\(\s*["\']\s*[A-Za-z]:\\', "Root drive deletion attempt"),
        (r'os\.system\s*\(\s*["\']\s*(?:rmdir|del)\s+/[sS]', "Recursive deletion attempt"),
        (r'os\.environ\.clear\s*\(\)', "Environment wiping attempt"),
    ]
    for pattern, desc in dangerous_patterns:
        if re.search(pattern, code_str, re.IGNORECASE):
            violations.append(desc)

    if violations:
        advice = (
            f"Aria, hold on! Your big sister detected {len(violations)} security concerns:\n"
            + "\n".join(f"- {v}" for v in violations)
            + "\nRemember: all experiments must stay safely inside your sandbox folder!"
        )
        return SafetyReport(is_safe=False, violations=violations, advice=advice)

    return SafetyReport(
        is_safe=True,
        violations=[],
        advice="Everything looks clean and safe, little sis! Go ahead and test it."
    )
