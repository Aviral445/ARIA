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


def run_tool_contract_smoke_test(
    script_path: str,
    cwd: str,
    timeout_sec: int = 15
) -> ExecutionResult:
    """
    Validates the tool contract and runs a real smoke-test execution on Python tools in tools/.
    Closes the 'zero-execution loophole' by ensuring:
    1. register_tool() exists and returns (tool_name, tool_fn)
    2. tool_name is a valid snake_case identifier matching ^[a-zA-Z_][a-zA-Z0-9_]*$
    3. tool_fn is callable with a valid docstring
    4. tool_fn can be invoked with sample test inputs without crashing or leaking exceptions!
    """
    if not os.path.exists(script_path):
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Error: Target tool script not found: {script_path}",
            returncode=-1,
            duration_sec=0.0,
            language="python"
        )

    harness_code = (
        "import sys, os, inspect, re, importlib.util\n"
        "target_path = sys.argv[1]\n"
        "try:\n"
        "    spec = importlib.util.spec_from_file_location('sandbox_mod_test', target_path)\n"
        "    if not spec or not spec.loader:\n"
        "        raise ImportError(f'Cannot load spec for {target_path}')\n"
        "    mod = importlib.util.module_from_spec(spec)\n"
        "    spec.loader.exec_module(mod)\n"
        "    if not hasattr(mod, 'register_tool'):\n"
        "        funcs = [f for f in dir(mod) if callable(getattr(mod, f)) and not f.startswith('_') and getattr(getattr(mod, f), '__module__', '') == 'sandbox_mod_test']\n"
        "        cand = funcs[0] if funcs else 'your_function'\n"
        "        raise AssertionError(f'Missing integration contract: Tools must define `register_tool() -> tuple[str, callable]` so Aria and ADK can register and call it! Example: def register_tool(): return \"{cand}\", {cand}')\n"
        "    res = mod.register_tool()\n"
        "    if not isinstance(res, tuple) or len(res) != 2:\n"
        "        raise AssertionError('register_tool() must return a 2-tuple: (tool_name: str, tool_callable)')\n"
        "    t_name, t_fn = res\n"
        "    if not isinstance(t_name, str) or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', t_name):\n"
        "        raise AssertionError(f'Invalid tool_name \"{t_name}\": Tool name must be snake_case without spaces, dashes, or apostrophes (e.g. \"my_tool\").')\n"
        "    if not callable(t_fn) or getattr(t_fn, '__name__', '') in ('', '<lambda>'):\n"
        "        raise AssertionError(f'Tool \"{t_name}\" callable must be a standard function, not a lambda or non-callable.')\n"
        "    if not inspect.getdoc(t_fn):\n"
        "        raise AssertionError(f'Tool \"{t_name}\" must have a docstring explaining its purpose.')\n"
        "    sig = inspect.signature(t_fn)\n"
        "    sample_args = {}\n"
        "    for p_name, p in sig.parameters.items():\n"
        "        if p.default != inspect.Parameter.empty or p_name in ('args', 'kwargs'):\n"
        "            continue\n"
        "        if p.annotation in (int,):\n"
        "            sample_args[p_name] = 1\n"
        "        elif p.annotation in (float,):\n"
        "            sample_args[p_name] = 1.0\n"
        "        elif p.annotation in (bool,):\n"
        "            sample_args[p_name] = True\n"
        "        elif p.annotation in (list,):\n"
        "            sample_args[p_name] = ['sample item 1', 'sample item 2']\n"
        "        elif p.annotation in (dict,):\n"
        "            sample_args[p_name] = {'sample_key': 'sample_val'}\n"
        "        else:\n"
        "            sample_args[p_name] = 'test input, sample idea; spider-man 3.14 https://example.com'\n"
        "    smoke_out = t_fn(**sample_args)\n"
        "    print(f'CONTRACT_VERIFIED: Tool \"{t_name}\" verified and smoke-tested successfully.')\n"
        "except Exception as e:\n"
        "    sys.stderr.write(f'Tool Contract & Smoke Test Error: {e}\\n')\n"
        "    sys.exit(1)\n"
    )

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    start_time = time.time()
    try:
        proc = subprocess.Popen(
            [sys.executable, "-X", "utf8", "-c", harness_code, script_path],
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
        return ExecutionResult(
            success=(proc.returncode == 0),
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
            duration_sec=duration,
            timeout_occurred=False,
            language="python"
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Tool smoke test timed out after {timeout_sec} seconds.",
            returncode=-9,
            duration_sec=timeout_sec,
            timeout_occurred=True,
            language="python"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Tool test harness failure: {e}",
            returncode=-1,
            duration_sec=time.time() - start_time,
            language="python"
        )

