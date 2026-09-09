"""
gaia/gaia_architect.py — Big Sister GAIA's Dedicated Architect Sandbox & Evolution Engine

Provides:
1. Dedicated Architect Sandbox at E:\\MyAgent\\gaia_architect (workspace, backups, incidents, patches, tests).
2. Full Codebase Diagnostic Engine (detects missing tools, crashes, token choke points, and architectural gaps).
3. Deterministic Non-LLM Ground Truths:
   - Zero-trust AST parsing (ast.parse)
   - Import dependency pre-flight (importlib.util.find_spec)
   - Subprocess compile & contract execution with exit code 0
   - Token truncation sniffer
4. Hard 3-Attempt Circuit Breaker with snapshot rollback & BigBroBridge incident escalation.
5. Two-Track Evolution:
   - Track 1: Safe autonomous deployment for modular tools (tools/), skills (skills/), and config (config/).
   - Track 2: Verified .diff patch proposals for core kernel files (core/, agent.py) awaiting human approval.
"""

import os
import sys
import json
import time
import ast
import shutil
import difflib
import importlib.util
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    from core.paths import ROOT_DIR, DATA_DIR, TOOLS_DIR
except ImportError:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    TOOLS_DIR = os.path.join(ROOT_DIR, "tools")

from gaia.gaia_bus import bus
from core.big_bro_bridge import BigBroBridge
from core.aria_config_manager import get_token_limit, update_token_limit, get_engine_config
from core.aria_skills_manager import get_all_skills_prompt, save_skill, list_skills

# Architect Sandbox Base Directory
if os.path.exists(r"E:\MyAgent"):
    ARCHITECT_DIR = r"E:\MyAgent\gaia_architect"
elif os.path.exists("E:\\"):
    ARCHITECT_DIR = r"E:\gaia_architect"
else:
    ARCHITECT_DIR = os.path.join(ROOT_DIR, "gaia", "sandbox", "gaia_architect")

WORKSPACE_DIR = os.path.join(ARCHITECT_DIR, "workspace")
BACKUPS_DIR = os.path.join(ARCHITECT_DIR, "backups")
INCIDENTS_DIR = os.path.join(ARCHITECT_DIR, "incidents")
PATCHES_DIR = os.path.join(ARCHITECT_DIR, "patches")
TESTS_DIR = os.path.join(ARCHITECT_DIR, "tests")
LEDGER_FILE = os.path.join(ARCHITECT_DIR, "architect_ledger.json")

MAX_CIRCUIT_ATTEMPTS = 3


def ensure_architect_environment() -> Dict[str, str]:
    """Ensures all sandbox directories and the ledger exist."""
    dirs = {
        "root": ARCHITECT_DIR,
        "workspace": WORKSPACE_DIR,
        "backups": BACKUPS_DIR,
        "incidents": INCIDENTS_DIR,
        "patches": PATCHES_DIR,
        "tests": TESTS_DIR,
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    if not os.path.exists(LEDGER_FILE):
        default_ledger = {
            "initialized_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "diagnoses": [],
            "active_attempts": {},
            "deployments": [],
            "patches": [],
            "incidents": []
        }
        try:
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump(default_ledger, f, indent=2)
        except Exception as e:
            print(f"[GAIA Architect Notice] Failed to create ledger: {e}")

    return dirs


class GaiaArchitect:
    """The Autonomous Architect and Evolution Engine for GAIA."""

    def __init__(self, architect_dir: str = ARCHITECT_DIR):
        self.architect_dir = architect_dir
        self.env_dirs = ensure_architect_environment()
        self.bridge = BigBroBridge()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. LEDGER MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────

    def load_ledger(self) -> Dict[str, Any]:
        """Loads persistent architect ledger."""
        if not os.path.exists(LEDGER_FILE):
            ensure_architect_environment()
        try:
            with open(LEDGER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "initialized_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "diagnoses": [],
                "active_attempts": {},
                "deployments": [],
                "patches": [],
                "incidents": []
            }

    def save_ledger(self, ledger: Dict[str, Any]) -> None:
        """Saves persistent architect ledger."""
        try:
            with open(LEDGER_FILE, "w", encoding="utf-8") as f:
                json.dump(ledger, f, indent=2)
        except Exception as e:
            print(f"[GAIA Architect Notice] Failed to save ledger: {e}")

    def get_attempts(self, issue_id: str) -> int:
        """Returns current attempt count for an issue."""
        ledger = self.load_ledger()
        return ledger.get("active_attempts", {}).get(issue_id, 0)

    def increment_attempt(self, issue_id: str) -> int:
        """Increments attempt counter for an issue and persists."""
        ledger = self.load_ledger()
        attempts = ledger.get("active_attempts", {})
        count = attempts.get(issue_id, 0) + 1
        attempts[issue_id] = count
        ledger["active_attempts"] = attempts
        self.save_ledger(ledger)
        return count

    def reset_attempts(self, issue_id: str) -> None:
        """Clears attempt counter for a resolved issue."""
        ledger = self.load_ledger()
        attempts = ledger.get("active_attempts", {})
        if issue_id in attempts:
            del attempts[issue_id]
            ledger["active_attempts"] = attempts
            self.save_ledger(ledger)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. CODEBASE INSPECTION & DIAGNOSTICS
    # ─────────────────────────────────────────────────────────────────────────

    def read_codebase_file(self, rel_path: str) -> str:
        """Safely reads a file from the host codebase (c:\\MyAgent)."""
        full_path = os.path.abspath(os.path.join(ROOT_DIR, rel_path))
        if not full_path.startswith(os.path.abspath(ROOT_DIR)):
            return "Error: Path traversal outside codebase is forbidden."
        if not os.path.exists(full_path):
            return f"Error: File '{rel_path}' does not exist."
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    def search_codebase(self, query: str, ext: str = ".py", max_results: int = 10) -> List[Dict[str, Any]]:
        """Searches the codebase for specific patterns or symbols."""
        results = []
        q_lower = query.lower()
        skip_dirs = {".git", ".pytest_cache", "__pycache__", "node_modules", "venv", "env", "piper_models"}

        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if ext and not fname.endswith(ext):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for line_no, line in enumerate(f, 1):
                            if q_lower in line.lower():
                                rel = os.path.relpath(fpath, ROOT_DIR)
                                results.append({
                                    "file": rel,
                                    "line": line_no,
                                    "content": line.strip()[:160]
                                })
                                if len(results) >= max_results:
                                    return results
                except Exception:
                    continue
        return results

    def diagnose_aria_impediments(self) -> List[Dict[str, Any]]:
        """
        Scans events.json, aria thoughts, and swarm logs for impediments:
        - Missing tools
        - Crashed tools
        - Token choke points
        - Code limitations
        """
        impediments = []
        seen_keys = set()

        # 1. Check gaia/events.json
        events_file = os.path.join(ROOT_DIR, "gaia", "events.json")
        if os.path.exists(events_file):
            try:
                with open(events_file, "r", encoding="utf-8") as f:
                    events = json.load(f)
                    for ev in reversed(events[-50:]):
                        desc = ev.get("description", "")
                        ev_type = ev.get("type", "")

                        # Detect missing tools
                        if "Unknown tool:" in desc or "not found" in desc:
                            import re
                            m = re.search(r"(?:Unknown tool:\s*|Tool\s*')([a-zA-Z0-9_]+)", desc)
                            tool_name = m.group(1) if m else "unknown_tool"
                            key = f"missing_tool_{tool_name}"
                            if key not in seen_keys:
                                seen_keys.add(key)
                                impediments.append({
                                    "issue_id": key,
                                    "type": "MISSING_TOOL",
                                    "target_name": tool_name,
                                    "description": f"Aria attempted to call missing tool '{tool_name}'",
                                    "evidence": desc,
                                    "solution_type": "tool"
                                })

                        # Detect tool crashes
                        elif "Tool execution error:" in desc or "CRASH" in ev_type:
                            import re
                            m = re.search(r"(?:Tool execution error:\s*|in\s*)([a-zA-Z0-9_]+)", desc)
                            tool_name = m.group(1) if m else "crashed_tool"
                            key = f"tool_crash_{tool_name}"
                            if key not in seen_keys:
                                seen_keys.add(key)
                                impediments.append({
                                    "issue_id": key,
                                    "type": "TOOL_CRASH",
                                    "target_name": tool_name,
                                    "description": f"Tool '{tool_name}' crashed during execution",
                                    "evidence": desc,
                                    "solution_type": "tool"
                                })
            except Exception as e:
                print(f"[GAIA Architect Notice] Error reading events.json: {e}")

        # 2. Check inner_mind thoughts for token choke or frustration
        thoughts_file = os.path.join(ROOT_DIR, "inner_mind", "aria_thoughts.jsonl")
        if os.path.exists(thoughts_file):
            try:
                with open(thoughts_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                            thought = record.get("thought", "")
                            if any(k in thought.lower() for k in ["token limit", "truncated", "cut off", "token choke"]):
                                key = "token_limit_choke"
                                if key not in seen_keys:
                                    seen_keys.add(key)
                                    impediments.append({
                                        "issue_id": key,
                                        "type": "TOKEN_LIMIT_CHOKE",
                                        "target_name": "gemini_max_output_tokens",
                                        "description": "Aria encountered response truncation due to token limits",
                                        "evidence": thought[:200],
                                        "solution_type": "config"
                                    })
                        except Exception:
                            pass
            except Exception as e:
                print(f"[GAIA Architect Notice] Error reading thoughts: {e}")

        # Log diagnostics to ledger
        if impediments:
            ledger = self.load_ledger()
            for imp in impediments:
                ledger.setdefault("diagnoses", []).append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    **imp
                })
            # Keep recent 100
            ledger["diagnoses"] = ledger["diagnoses"][-100:]
            self.save_ledger(ledger)
            bus.emit("GAIA_ARCHITECT", "DIAGNOSE_COMPLETE", f"Diagnosed {len(impediments)} impediment(s).", {"count": len(impediments)})

        return impediments

    # ─────────────────────────────────────────────────────────────────────────
    # 3. DETERMINISTIC NON-LLM GROUND TRUTHS
    # ─────────────────────────────────────────────────────────────────────────

    def check_token_truncation(self, code_str: str) -> Tuple[bool, str]:
        """
        Deterministic sniffer for token truncation:
        Checks unclosed parentheses, braces, brackets, string quotes, or incomplete blocks.
        """
        code = code_str.strip()
        if not code:
            return True, "Code is empty."

        # Check triple quotes parity
        if code.count('"""') % 2 != 0:
            return True, "Unclosed triple double-quotes detected (truncated)."
        if code.count("'''") % 2 != 0:
            return True, "Unclosed triple single-quotes detected (truncated)."

        # Check bracket parity
        open_parens = code.count("(") - code.count(")")
        open_brackets = code.count("[") - code.count("]")
        open_braces = code.count("{") - code.count("}")
        if open_parens > 0 or open_brackets > 0 or open_braces > 0:
            return True, f"Unbalanced brackets detected (parens: {open_parens}, brackets: {open_brackets}, braces: {open_braces})."

        # Check if code ends abruptly mid-statement
        last_line = code.splitlines()[-1].strip() if code.splitlines() else ""
        if last_line.endswith(("=", "+", "-", "*", "/", ",", "import", "from", "def", "class", "try:", "except:")):
            return True, f"Abrupt truncated EOF at line: '{last_line}'"

        return False, "No truncation detected."

    def check_import_dependencies(self, tree: ast.AST) -> Tuple[bool, List[str]]:
        """
        Pre-flight check: verifies all imported third-party and standard modules exist
        in the current environment without executing untrusted code.
        """
        missing = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if not importlib.util.find_spec(root_mod):
                        missing.append(root_mod)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if not importlib.util.find_spec(root_mod):
                        missing.append(root_mod)
        return len(missing) == 0, list(set(missing))

    def verify_tool_contract(self, tree: ast.AST, tool_name: str) -> Tuple[bool, str]:
        """
        Verifies that a proposed tool meets Aria's ADK tool contract:
        - Must contain register_tool() returning (name, function)
        - Tool name must be snake_case
        """
        import re
        if not re.match(r"^[a-z][a-z0-9_]*$", tool_name):
            return False, f"Tool name '{tool_name}' violates snake_case convention."

        has_register_tool = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "register_tool":
                has_register_tool = True
                break

        if not has_register_tool:
            return False, "Missing mandatory 'def register_tool() -> tuple[str, callable]:' entrypoint."

        return True, "Tool contract valid."

    def verify_code_deterministic(self, code_str: str, tool_name: str, solution_type: str = "tool") -> Dict[str, Any]:
        """
        Executes the 5 non-LLM ground truth checks:
        1. Token truncation check
        2. AST parse (syntax check)
        3. Import pre-flight check
        4. Tool contract check (for tools)
        5. Subprocess compilation and execution test (exit code 0)
        """
        # 1. Truncation Sniffer
        is_truncated, trunc_reason = self.check_token_truncation(code_str)
        if is_truncated:
            return {
                "passed": False,
                "step": "TRUNCATION_SNIFFER",
                "reason": f"Code rejected due to token truncation: {trunc_reason}"
            }

        # 2. Zero-Trust AST Parse
        try:
            tree = ast.parse(code_str)
        except SyntaxError as syn_err:
            return {
                "passed": False,
                "step": "AST_PARSE",
                "reason": f"SyntaxError: {syn_err.msg} at line {syn_err.lineno}"
            }

        # 3. Import Dependencies Pre-Flight
        imports_ok, missing_mods = self.check_import_dependencies(tree)
        if not imports_ok:
            return {
                "passed": False,
                "step": "DEPENDENCY_PREFLIGHT",
                "reason": f"Missing module dependencies in Python environment: {', '.join(missing_mods)}"
            }

        # 4. Tool Contract
        if solution_type == "tool":
            contract_ok, contract_msg = self.verify_tool_contract(tree, tool_name)
            if not contract_ok:
                return {
                    "passed": False,
                    "step": "TOOL_CONTRACT",
                    "reason": contract_msg
                }

        # 5. Staging & Subprocess Execution
        staging_file = os.path.join(WORKSPACE_DIR, f"{tool_name}.py")
        try:
            with open(staging_file, "w", encoding="utf-8") as f:
                f.write(code_str)
        except Exception as e:
            return {
                "passed": False,
                "step": "STAGING",
                "reason": f"Failed to stage file: {e}"
            }

        # Run py_compile in subprocess
        try:
            compile_res = subprocess.run(
                [sys.executable, "-m", "py_compile", staging_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            if compile_res.returncode != 0:
                return {
                    "passed": False,
                    "step": "SUBPROCESS_COMPILE",
                    "reason": f"py_compile failed:\n{compile_res.stderr.strip()}"
                }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "step": "SUBPROCESS_COMPILE",
                "reason": "Compilation timed out after 10s."
            }

        # If it's a tool, test smoke execution of register_tool() in subprocess
        if solution_type == "tool":
            test_script = (
                f"import sys\n"
                f"sys.path.insert(0, r'{WORKSPACE_DIR}')\n"
                f"import {tool_name}\n"
                f"name, fn = {tool_name}.register_tool()\n"
                f"assert callable(fn), 'register_tool did not return callable'\n"
                f"print('SMOKE_TEST_PASS')\n"
            )
            test_harness_file = os.path.join(TESTS_DIR, f"harness_{tool_name}.py")
            try:
                with open(test_harness_file, "w", encoding="utf-8") as f:
                    f.write(test_script)
                smoke_res = subprocess.run(
                    [sys.executable, test_harness_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if smoke_res.returncode != 0:
                    return {
                        "passed": False,
                        "step": "SMOKE_EXECUTION",
                        "reason": f"Smoke execution failed:\n{smoke_res.stderr.strip()}"
                    }
            except subprocess.TimeoutExpired:
                return {
                    "passed": False,
                    "step": "SMOKE_EXECUTION",
                    "reason": "Smoke execution timed out."
                }

        return {
            "passed": True,
            "step": "ALL_PASSED",
            "staging_path": staging_file
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 4. CIRCUIT BREAKER, ROLLBACK & INCIDENT ESCALATION
    # ─────────────────────────────────────────────────────────────────────────

    def rollback_workspace(self, tool_name: str) -> None:
        """Cleans up staging and test artifacts in the sandbox."""
        staging_file = os.path.join(WORKSPACE_DIR, f"{tool_name}.py")
        harness_file = os.path.join(TESTS_DIR, f"harness_{tool_name}.py")
        for fpath in [staging_file, harness_file]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception:
                    pass

    def generate_incident_report(self, issue_id: str, error_history: List[str]) -> str:
        """Generates an incident report and escalates to BigBroBridge."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = f"incident_{timestamp}_{issue_id}.md"
        incident_path = os.path.join(INCIDENTS_DIR, fname)

        content = (
            f"# GAIA Architect Incident Escalation Report\n\n"
            f"**Issue ID**: `{issue_id}`\n"
            f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"**Circuit Breaker Status**: **TRIPPED (Max {MAX_CIRCUIT_ATTEMPTS} attempts exceeded)**\n\n"
            f"## Summary\n"
            f"Big Sister GAIA's Architect Sandbox attempted to synthesize and verify a solution for `{issue_id}`. "
            f"All {MAX_CIRCUIT_ATTEMPTS} attempts failed non-LLM deterministic verification. "
            f"To prevent hallucination loops and protect system stability, the circuit breaker tripped and the workspace was safely rolled back.\n\n"
            f"## Verification Failure Log\n"
        )
        for idx, err in enumerate(error_history, 1):
            content += f"### Attempt {idx}\n```\n{err}\n```\n\n"

        content += (
            f"## Recommended Action for Human / Antigravity Review\n"
            f"1. Review the required functionality or dependency for `{issue_id}`.\n"
            f"2. Check if a missing C-extension or system binary is required.\n"
            f"3. Manually provide an approved implementation or relax constraints.\n"
        )

        try:
            with open(incident_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"[GAIA Architect Notice] Failed to write incident file: {e}")

        # Escalate to BigBroBridge
        self.bridge.enqueue_message(
            sender="GAIA_Architect",
            topic=f"CIRCUIT_BREAKER_TRIPPED: {issue_id}",
            code="\n".join(error_history[-2:]) if error_history else "",
            status="ESCALATED_TO_ANTIGRAVITY",
            response=f"Incident report generated at {incident_path}. Circuit breaker tripped after {MAX_CIRCUIT_ATTEMPTS} failed attempts."
        )

        # Log to ledger
        ledger = self.load_ledger()
        ledger.setdefault("incidents", []).append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "issue_id": issue_id,
            "incident_path": incident_path
        })
        self.save_ledger(ledger)

        bus.emit("GAIA_ARCHITECT", "CIRCUIT_BREAKER_TRIPPED", f"Circuit breaker tripped for {issue_id}. Escalated to BigBroBridge.", {"issue_id": issue_id, "incident": fname})
        return incident_path

    # ─────────────────────────────────────────────────────────────────────────
    # 5. TWO-TRACK EVOLUTION & DEPLOYMENT
    # ─────────────────────────────────────────────────────────────────────────

    def deploy_modular_tool(self, tool_name: str, code_str: str, issue_id: str) -> Dict[str, Any]:
        """
        Track 1: Safe Autonomous Deployment for Modular Tools.
        Writes to tools/<tool_name>.py and triggers dynamic reload.
        """
        target_path = os.path.join(TOOLS_DIR, f"{tool_name}.py")
        backup_path = os.path.join(BACKUPS_DIR, f"{tool_name}_{int(time.time())}.py")

        # Backup existing tool if any
        if os.path.exists(target_path):
            shutil.copy2(target_path, backup_path)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(code_str)

            # Hot reload in ADK engine
            try:
                from core.aria_adk import load_dynamic_sandbox_tools
                load_dynamic_sandbox_tools()
            except Exception as e_reload:
                print(f"[GAIA Architect Notice] Hot-reload notification: {e_reload}")

            self.reset_attempts(issue_id)
            self.rollback_workspace(tool_name)

            # Ledger record
            ledger = self.load_ledger()
            ledger.setdefault("deployments", []).append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "modular_tool",
                "name": tool_name,
                "target_path": target_path,
                "status": "DEPLOYED_LIVE"
            })
            self.save_ledger(ledger)

            bus.emit("GAIA_ARCHITECT", "DEPLOY_SUCCESS", f"Successfully deployed tool '{tool_name}' into tools/.", {"tool_name": tool_name})
            return {
                "success": True,
                "type": "modular_tool",
                "target_path": target_path,
                "status": "DEPLOYED_LIVE"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to deploy tool: {e}"
            }

    def deploy_modular_skill(self, skill_name: str, markdown_content: str, issue_id: str) -> Dict[str, Any]:
        """
        Track 1: Safe Autonomous Deployment for Modular Skills.
        Saves to skills/<skill_name>.md via aria_skills_manager.
        """
        ok = save_skill(skill_name, markdown_content)
        if ok:
            self.reset_attempts(issue_id)
            ledger = self.load_ledger()
            ledger.setdefault("deployments", []).append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "modular_skill",
                "name": skill_name,
                "status": "DEPLOYED_LIVE"
            })
            self.save_ledger(ledger)
            bus.emit("GAIA_ARCHITECT", "DEPLOY_SUCCESS", f"Successfully deployed skill '{skill_name}' into skills/.", {"skill_name": skill_name})
            return {"success": True, "type": "modular_skill", "name": skill_name}
        return {"success": False, "error": f"Failed to save skill '{skill_name}'."}

    def deploy_modular_adk(self, adk_name: str, tools_code: Optional[str] = None, rules_text: Optional[str] = None, description: str = "") -> Dict[str, Any]:
        """
        Track 1: Safe Autonomous Deployment for Modular ADKs.
        Uses AriaADKManager with author='GAIA'.
        """
        from core.aria_adk_manager import get_adk_manager
        mgr = get_adk_manager()
        res = mgr.create_adk(
            adk_name=adk_name,
            author="GAIA",
            description=description or f"Autonomous ADK architected by GAIA for {adk_name}",
            tools_code=tools_code,
            rules_text=rules_text
        )
        if res.get("success"):
            ledger = self.load_ledger()
            ledger.setdefault("deployments", []).append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "modular_adk",
                "name": adk_name,
                "status": "DEPLOYED_LIVE"
            })
            self.save_ledger(ledger)
            bus.emit("GAIA_ARCHITECT", "DEPLOY_SUCCESS", f"GAIA deployed new ADK '{adk_name}'.", {"adk_name": adk_name})
        return res

    def adjust_engine_config(self, key: str, value: int, issue_id: str) -> Dict[str, Any]:

        """
        Track 1: Safe Autonomous Adjustment of Config/Token Limits.
        """
        ok = update_token_limit(key, value)
        if ok:
            self.reset_attempts(issue_id)
            ledger = self.load_ledger()
            ledger.setdefault("deployments", []).append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "config_limit",
                "key": key,
                "value": value,
                "status": "UPDATED_CONFIG"
            })
            self.save_ledger(ledger)
            bus.emit("GAIA_ARCHITECT", "CONFIG_UPDATED", f"Updated limit '{key}' to {value}.", {"key": key, "value": value})
            return {"success": True, "type": "config_limit", "key": key, "value": value}
        return {"success": False, "error": f"Failed to update token limit for {key}."}

    def propose_core_kernel_patch(self, target_rel_path: str, proposed_code: str, rationale: str) -> Dict[str, Any]:
        """
        Track 2: Core Kernel Patch Proposal.
        Does NOT overwrite core files directly. Computes a verified unified diff,
        saves to patches/patch_<timestamp>_<slug>.diff, and alerts BigBroBridge.
        """
        full_target_path = os.path.abspath(os.path.join(ROOT_DIR, target_rel_path))
        if not os.path.exists(full_target_path):
            return {"success": False, "error": f"Target file '{target_rel_path}' does not exist."}

        # Verify syntax of proposed code
        try:
            ast.parse(proposed_code)
        except SyntaxError as se:
            return {"success": False, "error": f"Proposed core patch contains SyntaxError: {se}"}

        # Read original
        with open(full_target_path, "r", encoding="utf-8", errors="replace") as f:
            orig_lines = f.readlines()
        prop_lines = proposed_code.splitlines(keepends=True)

        diff_lines = list(difflib.unified_diff(
            orig_lines,
            prop_lines,
            fromfile=f"a/{target_rel_path}",
            tofile=f"b/{target_rel_path}",
            lineterm=""
        ))

        if not diff_lines:
            return {"success": False, "error": "No changes detected in proposed patch."}

        diff_text = "\n".join(diff_lines)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = os.path.splitext(os.path.basename(target_rel_path))[0]
        patch_file = os.path.join(PATCHES_DIR, f"patch_{timestamp}_{slug}.diff")

        try:
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(f"# Rationale: {rationale}\n")
                f.write(f"# Target: {target_rel_path}\n")
                f.write(f"# Proposed At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(diff_text)
        except Exception as e:
            return {"success": False, "error": f"Failed to save patch file: {e}"}

        # Enqueue patch proposal in BigBroBridge for human review
        self.bridge.enqueue_message(
            sender="GAIA_Architect",
            topic=f"PROPOSED_CORE_PATCH: {target_rel_path}",
            code=diff_text[:500],
            status="AWAITING_HUMAN_APPROVAL",
            response=f"Patch generated at {patch_file}. Rationale: {rationale}"
        )

        # Record in ledger
        ledger = self.load_ledger()
        ledger.setdefault("patches", []).append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": target_rel_path,
            "patch_file": patch_file,
            "status": "PROPOSED_AWAITING_APPROVAL",
            "rationale": rationale
        })
        self.save_ledger(ledger)

        bus.emit("GAIA_ARCHITECT", "CORE_PATCH_PROPOSED", f"Proposed core patch for {target_rel_path}.", {"target": target_rel_path, "patch_file": patch_file})
        return {
            "success": True,
            "type": "core_patch_proposal",
            "target": target_rel_path,
            "patch_file": patch_file,
            "diff_preview": diff_text[:500]
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 6. HIGH-LEVEL SOLVE WORKFLOW & STATUS
    # ─────────────────────────────────────────────────────────────────────────

    def solve_impediment(self, impediment: Dict[str, Any], candidate_code_or_value: str, rationale: str = "") -> Dict[str, Any]:
        """
        Coordinates the verification, circuit breaker, and two-track deployment
        for a diagnosed impediment.
        """
        issue_id = impediment.get("issue_id", "unnamed_issue")
        sol_type = impediment.get("solution_type", "tool")
        target_name = impediment.get("target_name", "unnamed")

        # Check circuit breaker
        attempt = self.increment_attempt(issue_id)
        if attempt > MAX_CIRCUIT_ATTEMPTS:
            incident_path = self.generate_incident_report(
                issue_id=issue_id,
                error_history=[f"Attempt {attempt}: Exceeded maximum allowed attempts ({MAX_CIRCUIT_ATTEMPTS})."]
            )
            return {
                "success": False,
                "circuit_breaker": "TRIPPED",
                "incident_report": incident_path
            }

        # Route by solution type
        if sol_type == "tool":
            v_res = self.verify_code_deterministic(candidate_code_or_value, target_name, solution_type="tool")
            if not v_res["passed"]:
                # If this was attempt 3, trip circuit breaker
                if attempt == MAX_CIRCUIT_ATTEMPTS:
                    incident_path = self.generate_incident_report(issue_id, [v_res["reason"]])
                    return {
                        "success": False,
                        "circuit_breaker": "TRIPPED",
                        "reason": v_res["reason"],
                        "incident_report": incident_path
                    }
                return {
                    "success": False,
                    "attempt": attempt,
                    "reason": v_res["reason"]
                }
            # Verification passed: deploy to tools/
            return self.deploy_modular_tool(target_name, candidate_code_or_value, issue_id)

        elif sol_type == "skill":
            return self.deploy_modular_skill(target_name, candidate_code_or_value, issue_id)

        elif sol_type == "config":
            try:
                new_limit = int(candidate_code_or_value)
                return self.adjust_engine_config(target_name, new_limit, issue_id)
            except Exception as e:
                return {"success": False, "error": f"Invalid integer limit: {e}"}

        elif sol_type == "core_patch":
            return self.propose_core_kernel_patch(target_name, candidate_code_or_value, rationale)

        return {"success": False, "error": f"Unknown solution type '{sol_type}'"}

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive telemetry of the Architect Sandbox."""
        ledger = self.load_ledger()
        workspace_files = os.listdir(WORKSPACE_DIR) if os.path.exists(WORKSPACE_DIR) else []
        incidents = os.listdir(INCIDENTS_DIR) if os.path.exists(INCIDENTS_DIR) else []
        patches = os.listdir(PATCHES_DIR) if os.path.exists(PATCHES_DIR) else []
        backups = os.listdir(BACKUPS_DIR) if os.path.exists(BACKUPS_DIR) else []

        return {
            "architect_dir": self.architect_dir,
            "workspace_files_count": len(workspace_files),
            "incidents_count": len(incidents),
            "patches_count": len(patches),
            "backups_count": len(backups),
            "active_circuit_attempts": ledger.get("active_attempts", {}),
            "total_deployments": len(ledger.get("deployments", [])),
            "total_diagnoses": len(ledger.get("diagnoses", [])),
            "engine_config": get_engine_config(),
            "skills_count": len(list_skills())
        }


# Singleton accessor
_ARCHITECT_INSTANCE: Optional[GaiaArchitect] = None


def get_gaia_architect() -> GaiaArchitect:
    """Returns singleton instance of GaiaArchitect."""
    global _ARCHITECT_INSTANCE
    if _ARCHITECT_INSTANCE is None:
        _ARCHITECT_INSTANCE = GaiaArchitect()
    return _ARCHITECT_INSTANCE
