"""
gaia/gaia_runner.py — Sandboxed Subprocess Execution Engine
Runs Aria's experimental code in an isolated subprocess with strict timeouts and telemetry.
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any


class ExecutionResult:
    def __init__(self, success: bool, stdout: str, stderr: str, returncode: int, duration_sec: float, timeout_occurred: bool = False):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.duration_sec = duration_sec
        self.timeout_occurred = timeout_occurred

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "duration_sec": round(self.duration_sec, 3),
            "timeout_occurred": self.timeout_occurred
        }


def run_sandboxed_script(script_path: str, cwd: str, timeout_sec: int = 20, env_overrides: Dict[str, str] = None) -> ExecutionResult:
    """
    Executes a python script inside the sandbox with timeout protection.
    """
    if not os.path.exists(script_path):
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Error: Target script not found: {script_path}",
            returncode=-1,
            duration_sec=0.0
        )

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if env_overrides:
        env.update(env_overrides)

    start_time = time.time()
    try:
        proc = subprocess.Popen(
            [sys.executable, script_path],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
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
            timeout_occurred=False
        )

    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        duration = time.time() - start_time
        return ExecutionResult(
            success=False,
            stdout=stdout,
            stderr="Execution timed out! The script exceeded the maximum safety time limit.",
            returncode=-9,
            duration_sec=duration,
            timeout_occurred=True
        )

    except Exception as e:
        duration = time.time() - start_time
        return ExecutionResult(
            success=False,
            stdout="",
            stderr=f"Execution process error: {e}",
            returncode=-1,
            duration_sec=duration
        )
