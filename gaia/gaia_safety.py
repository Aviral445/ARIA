"""
gaia/gaia_safety.py — Polyglot Static AST & Pattern Security Guardrail
Protects the host system by analyzing Aria's self-written code before execution
across all major languages (Python, JavaScript, TypeScript, Java, PowerShell, Batch, Bash, etc.).
"""

import ast
import os
import re
from typing import Dict, List, Any, Tuple, Optional


# Protected system paths and files that must never be targeted
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
    def __init__(self, is_safe: bool, violations: List[str], advice: str = "", language: str = "python"):
        self.is_safe = is_safe
        self.violations = violations
        self.advice = advice
        self.language = language

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "violations": self.violations,
            "advice": self.advice,
            "language": self.language
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


def _audit_polyglot_patterns(code_str: str, sandbox_dir: str, lang: str) -> List[str]:
    """
    Language-agnostic pattern safety scanner for non-Python or mixed code.
    Blocks destructive system commands, disk formats, environment/credential theft,
    and root file wipeouts.
    """
    violations = []
    norm_code = code_str.lower()

    # Destructive disk & OS commands
    dangerous_commands = [
        (r'\bformat\s+[a-z]:', "Destructive disk format command detected"),
        (r'\brmdir\s+/[sS]', "Recursive directory wipeout command detected"),
        (r'\bdel\s+/[fF]\s+/[sS]', "Forced recursive file deletion detected"),
        (r'\brm\s+-[rf]{1,2}\s+[/~]', "Unix root deletion attempt detected"),
        (r'\bRemove-Item.*-(?:Recurse|Force).*[CDEF]:\\', "PowerShell root deletion detected"),
        (r'\b(?:shutdown|Restart-Computer|Stop-Computer)\b', "System power/shutdown command detected"),
        (r'\bdiskpart\b', "Disk partition utility access detected"),
    ]

    for pattern, desc in dangerous_commands:
        if re.search(pattern, code_str, re.IGNORECASE):
            violations.append(desc)

    # Sensitive credentials access
    sensitive_patterns = [
        (r'[\'"](?:[^\'"]*[/\\])?\.env[\'"]', "Unauthorized reference to root .env file"),
        (r'[\'"](?:[^\'"]*[/\\])?id_rsa[\'"]', "Unauthorized reference to SSH private key"),
        (r'[\'"](?:[^\'"]*[/\\])?(?:system32|SAM)[\'"]', "Unauthorized access to Windows system files"),
    ]
    for pattern, desc in sensitive_patterns:
        if re.search(pattern, code_str, re.IGNORECASE):
            violations.append(desc)

    return violations


def audit_code_safety(code_str: str, sandbox_dir: str, language: str = "auto") -> SafetyReport:
    """
    Analyzes source code across all major languages (Python, JavaScript, TypeScript, Java, PowerShell, etc.).
    Uses AST analysis for Python and robust pattern security guardrails for polyglot languages.
    Returns SafetyReport with is_safe status and sisterly coaching advice.
    """
    try:
        from gaia.gaia_runner import detect_language_from_code
        resolved_lang = detect_language_from_code(code_str) if language in ["auto", "", None] else language.lower().strip()
    except Exception:
        resolved_lang = "python" if language in ["auto", "", None] else language.lower().strip()

    violations = []

    # 1. Python Path: AST + Pattern
    if resolved_lang == "python":
        try:
            tree = ast.parse(code_str)
            visitor = SafetyVisitor(sandbox_dir=sandbox_dir)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except SyntaxError as e:
            # If explicit python, report syntax error
            if language == "python":
                return SafetyReport(
                    is_safe=False,
                    violations=[f"Python SyntaxError at line {e.lineno}: {e.msg}"],
                    advice=f"Aria sweetie, check line {e.lineno} — there's a syntax mistake ({e.msg}). Let's fix that syntax before running!",
                    language="python"
                )
            # If auto-detected as python but failed syntax, verify if it was another language
            poly_violations = _audit_polyglot_patterns(code_str, sandbox_dir, resolved_lang)
            violations.extend(poly_violations)

        dangerous_patterns = [
            (r'shutil\.rmtree\s*\(\s*["\']\s*[A-Za-z]:\\', "Root drive deletion attempt"),
            (r'os\.system\s*\(\s*["\']\s*(?:rmdir|del)\s+/[sS]', "Recursive deletion attempt"),
            (r'os\.environ\.clear\s*\(\)', "Environment wiping attempt"),
        ]
        for pattern, desc in dangerous_patterns:
            if re.search(pattern, code_str, re.IGNORECASE):
                violations.append(desc)

    # 2. Polyglot Path: JavaScript, TypeScript, Java, PowerShell, Batch, Bash, etc.
    else:
        poly_violations = _audit_polyglot_patterns(code_str, sandbox_dir, resolved_lang)
        violations.extend(poly_violations)

    if violations:
        advice = (
            f"Aria, hold on! Your big sister detected {len(violations)} security concerns in your {resolved_lang} code:\n"
            + "\n".join(f"- {v}" for v in violations)
            + f"\nRemember: all experiments must stay safely inside your sandbox folder!"
        )
        return SafetyReport(is_safe=False, violations=violations, advice=advice, language=resolved_lang)

    return SafetyReport(
        is_safe=True,
        violations=[],
        advice=f"Everything looks clean and safe for {resolved_lang}, little sis! Go ahead and test it.",
        language=resolved_lang
    )
