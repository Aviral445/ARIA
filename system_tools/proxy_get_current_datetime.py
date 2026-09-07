"""Auto-generated ADK bridge for polyglot tool get_current_datetime.ps1"""
import os, sys
from gaia.gaia_runner import run_sandboxed_script
def run_get_current_datetime(args: str = "") -> str:
    tool_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "get_current_datetime.ps1")
    res = run_sandboxed_script(tool_file, cwd=os.path.dirname(tool_file), timeout_sec=15)
    return res.stdout if res.success else f"Error: {res.stderr or res.stdout}"
def register_tool():
    return "run_get_current_datetime", run_get_current_datetime
