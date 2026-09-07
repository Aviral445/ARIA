"""Auto-generated ADK bridge for polyglot tool powershell_hello_world.ps1"""
import os, sys
from gaia.gaia_runner import run_sandboxed_script
def run_powershell_hello_world(args: str = "") -> str:
    tool_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "powershell_hello_world.ps1")
    res = run_sandboxed_script(tool_file, cwd=os.path.dirname(tool_file), timeout_sec=15)
    return res.stdout if res.success else f"Error: {res.stderr or res.stdout}"
def register_tool():
    return "run_powershell_hello_world", run_powershell_hello_world
