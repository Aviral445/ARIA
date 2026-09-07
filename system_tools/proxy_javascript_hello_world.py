"""Auto-generated ADK bridge for polyglot tool javascript_hello_world.js"""
import os, sys
from gaia.gaia_runner import run_sandboxed_script
def run_javascript_hello_world(args: str = "") -> str:
    tool_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "javascript_hello_world.js")
    res = run_sandboxed_script(tool_file, cwd=os.path.dirname(tool_file), timeout_sec=15)
    return res.stdout if res.success else f"Error: {res.stderr or res.stdout}"
def register_tool():
    return "run_javascript_hello_world", run_javascript_hello_world
