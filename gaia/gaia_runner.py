"""
gaia/gaia_runner.py — Polyglot Sandboxed Subprocess Execution Engine
Runs Aria's experimental code in isolated subprocesses across all major programming languages:
Python, JavaScript (Node.js), TypeScript (Node 22 native), Java 25 LTS, PowerShell, Windows Batch, Bash, etc.
Strict timeouts and telemetry are enforced for safety.
"""

import os
import sys
import time
import re
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple


class ExecutionResult:
    def __init__(self, success: bool, stdout: str, stderr: str, returncode: int, duration_sec: float, timeout_occurred: bool = False, language: str = "python"):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.duration_sec = duration_sec
        self.timeout_occurred = timeout_occurred
        self.language = language

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "duration_sec": round(self.duration_sec, 3),
            "timeout_occurred": self.timeout_occurred,
            "language": self.language
        }


LANG_EXTENSIONS: Dict[str, str] = {
    "python": ".py",
    "py": ".py",
    "javascript": ".js",
    "js": ".js",
    "node": ".js",
    "typescript": ".ts",
    "ts": ".ts",
    "java": ".java",
    "powershell": ".ps1",
    "ps1": ".ps1",
    "ps": ".ps1",
    "batch": ".bat",
    "bat": ".bat",
    "cmd": ".bat",
    "bash": ".sh",
    "sh": ".sh",
    "c": ".c",
    "cpp": ".cpp",
    "c++": ".cpp",
    "rust": ".rs",
    "rs": ".rs",
    "go": ".go",
    "golang": ".go",
}

EXT_TO_LANG: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".ps1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    ".sh": "bash",
    ".c": "c",
    ".cpp": "cpp",
    ".rs": "rust",
    ".go": "go",
}


def detect_language_from_code(code_str: str) -> str:
    """
    Intelligently identifies the programming language of a code snippet using shebangs,
    syntax tokens, and standard library markers.
    """
    if not code_str or not code_str.strip():
        return "python"

    first_line = code_str.strip().splitlines()[0] if code_str.strip() else ""
    if first_line.startswith("#!"):
        lower_shebang = first_line.lower()
        if "node" in lower_shebang or "js" in lower_shebang:
            return "javascript"
        if "python" in lower_shebang:
            return "python"
        if "bash" in lower_shebang or "sh" in lower_shebang:
            return "bash"

    # Java detection
    if re.search(r'\bpublic\s+(?:final\s+)?class\s+\w+', code_str) or "System.out.print" in code_str or "public static void main" in code_str:
        return "java"

    # TypeScript specific markers (type annotations, interfaces, type aliases, generic type parameters)
    ts_markers = [
        r':\s*(?:string|number|boolean|any|void|never|unknown)\b',
        r'\binterface\s+\w+\s*\{',
        r'\btype\s+\w+\s*=',
        r'\bas\s+const\b',
        r'\b(enum)\s+\w+\s*\{'
    ]
    if any(re.search(p, code_str) for p in ts_markers):
        return "typescript"

    # JavaScript / Node detection
    js_markers = ["console.log", "const ", "let ", "var ", "require(", "module.exports", "document.", "window."]
    if any(m in code_str for m in js_markers):
        return "javascript"

    # PowerShell detection
    ps_markers = ["Write-Host", "Write-Output", "Get-Process", "Get-ChildItem", "Set-Content", "$PSScriptRoot", "$env:"]
    if any(m in code_str for m in ps_markers):
        return "powershell"

    # Windows Batch detection
    if re.search(r'(?i)^\s*@?echo\s+(?:on|off)\b', code_str, re.MULTILINE) or "%~dp0" in code_str:
        return "batch"

    # Bash / Shell detection
    if re.search(r'\b(if\s+\[.*\];\s*then|elif\s+\[.*\];\s*then|fi\b|done\b|esac\b)', code_str):
        return "bash"

    # C / C++ detection
    if "#include <iostream>" in code_str or "#include <vector>" in code_str or "std::cout" in code_str:
        return "cpp"
    if "#include <stdio.h>" in code_str or "#include <stdlib.h>" in code_str:
        return "c"

    # Rust detection
    if "fn main()" in code_str or "println!" in code_str or "let mut " in code_str:
        return "rust"

    # Go detection
    if re.search(r'\bpackage\s+\w+', code_str) and "func main()" in code_str:
        return "go"

    # Default fallback
    return "python"


def resolve_execution_command(script_path: str, language: str = "auto") -> Tuple[List[str], str]:
    """
    Returns the subprocess command invocation and normalized language identifier
    for the given script file and requested language.
    """
    ext = os.path.splitext(script_path)[1].lower()
    lang = language.lower().strip() if language and language != "auto" else EXT_TO_LANG.get(ext, "python")

    # Normalize aliases
    if lang in ["py", "python3"]:
        lang = "python"
    elif lang in ["js", "node"]:
        lang = "javascript"
    elif lang in ["ts"]:
        lang = "typescript"
    elif lang in ["ps", "ps1"]:
        lang = "powershell"
    elif lang in ["bat", "cmd"]:
        lang = "batch"
    elif lang in ["sh"]:
        lang = "bash"

    # 1. Python
    if lang == "python":
        return [sys.executable, script_path], "python"

    # 2. JavaScript (Node.js)
    if lang == "javascript":
        node_bin = shutil.which("node") or "node"
        return [node_bin, script_path], "javascript"

    # 3. TypeScript (Node 22 native type stripping)
    if lang == "typescript":
        node_bin = shutil.which("node") or "node"
        return [node_bin, "--experimental-strip-types", script_path], "typescript"

    # 4. Java (Java 11+ single-source file execution)
    if lang == "java":
        java_bin = shutil.which("java") or "java"
        return [java_bin, script_path], "java"

    # 5. PowerShell
    if lang == "powershell":
        pwsh_bin = shutil.which("pwsh") or shutil.which("powershell") or "powershell"
        return [pwsh_bin, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path], "powershell"

    # 6. Windows Batch
    if lang == "batch":
        cmd_bin = shutil.which("cmd") or "cmd"
        return [cmd_bin, "/c", script_path], "batch"

    # 7. Bash
    if lang == "bash":
        bash_bin = shutil.which("bash") or "bash"
        return [bash_bin, script_path], "bash"

    # Fallback to python
    return [sys.executable, script_path], "python"


def run_sandboxed_script(
    script_path: str,
    cwd: str,
    timeout_sec: int = 20,
    language: str = "auto",
    env_overrides: Optional[Dict[str, str]] = None
) -> ExecutionResult:
    """
    Executes a script inside the sandbox with strict timeout and polyglot runtime dispatch.
    Supports Python, JavaScript, TypeScript, Java, PowerShell, Batch, Bash, etc.
    """
    if not os.path.exists(script_path):
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Error: Target script not found: {script_path}",
            returncode=-1,
            duration_sec=0.0,
            language=language
        )

    cmd, resolved_lang = resolve_execution_command(script_path, language)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NODE_OPTIONS"] = "--no-warnings"
    if env_overrides:
        env.update(env_overrides)

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        stdout, stderr = proc.communicate(timeout=timeout_sec)
        duration = time.time() - start_time
        success = (proc.returncode == 0)

        return ExecutionResult(
            success=success,
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
            duration_sec=duration,
            timeout_occurred=False,
            language=resolved_lang
        )

    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        duration = time.time() - start_time
        return ExecutionResult(
            success=False,
            stdout=stdout,
            stderr=f"Execution timed out! The {resolved_lang} script exceeded the safety limit of {timeout_sec} seconds.",
            returncode=-9,
            duration_sec=duration,
            timeout_occurred=True,
            language=resolved_lang
        )

    except Exception as e:
        duration = time.time() - start_time
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Execution process error for {resolved_lang}: {e}",
            returncode=-1,
            duration_sec=duration,
            language=resolved_lang
        )


def run_polyglot_code(
    code_str: str,
    language: str = "auto",
    cwd: Optional[str] = None,
    timeout_sec: int = 15
) -> ExecutionResult:
    """
    Executes a raw string of code in any supported programming language in an isolated sandbox runner.
    Automatically determines the language, writes a temporary script file, runs it, and cleans up.
    """
    resolved_lang = detect_language_from_code(code_str) if language in ["auto", "", None] else language.lower().strip()
    ext = LANG_EXTENSIONS.get(resolved_lang, ".py")

    # Determine execution working directory
    target_cwd = cwd
    if not target_cwd:
        try:
            from gaia.gaia_healer import SANDBOX_DIR
            target_cwd = SANDBOX_DIR
        except Exception:
            target_cwd = os.getcwd()

    os.makedirs(target_cwd, exist_ok=True)

    # For Java, single-source files require matching public class name if specified
    if resolved_lang == "java":
        m = re.search(r'\bpublic\s+(?:final\s+)?class\s+(\w+)', code_str)
        class_name = m.group(1) if m else "AriaJavaRunner"
        filename = f"{class_name}.java"
        # If no public class was declared, wrap in AriaJavaRunner if needed
        if not m and "public static void main" in code_str:
            code_str = f"public class AriaJavaRunner {{\n{code_str}\n}}"
    else:
        filename = f"_aria_polyglot_temp_{int(time.time() * 1000)}{ext}"

    script_path = os.path.join(target_cwd, filename)
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_str)

        return run_sandboxed_script(script_path, cwd=target_cwd, timeout_sec=timeout_sec, language=resolved_lang)
    finally:
        try:
            if os.path.exists(script_path):
                os.remove(script_path)
        except Exception:
            pass
