"""
gaia/gaia_reviewer.py — Big Sister GAIA's Advanced Code Reviewer & Chaos Stress-Tester

Teaches GAIA how Big Bro Antigravity reviews code with 4 foundational pillars:
1. AST Semantic Anti-Pattern Analysis (detects blocking context managers, missing wraps, loose regexes)
2. Dynamic Chaos & Infinite Loop Stress-Testing (monitors actual timeout behavior against runaway loops)
3. Tool Contract & Tuple Return Preservation (verifies (bool, str) contract and prevents double-wrap traps)
4. Resource Safety & Daemon Thread Verification (prevents process hangs on exit)
"""

import os
import sys
import ast
import time
import json
import threading
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

# Ensure core and gaia paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

@dataclass
class ReviewFinding:
    severity: str  # "CRITICAL", "WARNING", "INFO", "PRAISE"
    pillar: str    # "Concurrency", "Contract", "Decorators", "Security", "Resource"
    message: str
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None

@dataclass
class ReviewReport:
    file_path: str
    score: float = 10.0  # 0.0 to 10.0
    is_approved: bool = False
    critical_count: int = 0
    warning_count: int = 0
    findings: List[ReviewFinding] = field(default_factory=list)
    sisterly_coaching: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "score": round(self.score, 1),
            "is_approved": self.is_approved,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "findings": [
                {
                    "severity": f.severity,
                    "pillar": f.pillar,
                    "message": f.message,
                    "code_snippet": f.code_snippet,
                    "fix_suggestion": f.fix_suggestion
                } for f in self.findings
            ],
            "sisterly_coaching": self.sisterly_coaching
        }


class GaiaReviewer:
    """Big Sister GAIA's Senior Code Review Engine."""

    def __init__(self):
        pass

    def review_code_string(self, code: str, file_label: str = "snippet.py") -> ReviewReport:
        """Audits code given as a string."""
        code = code.lstrip("\ufeff")
        report = ReviewReport(file_path=file_label)
        self._audit_ast_patterns(code, report)
        self._audit_tool_contract(code, report)
        self._audit_dynamic_chaos(code, report)
        self._calculate_score_and_verdict(report)
        return report

    def review_file(self, file_path: str) -> ReviewReport:
        """Audits a Python file from disk."""
        if not os.path.exists(file_path):
            report = ReviewReport(file_path=file_path, score=0.0, is_approved=False)
            report.findings.append(ReviewFinding(
                severity="CRITICAL",
                pillar="File System",
                message=f"File '{file_path}' does not exist on disk."
            ))
            report.sisterly_coaching = "Little sis, I couldn't find the file on disk! Remember Rule #1: No imaginary files—make sure the receipt is real!"
            return report

        try:
            with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
                code = f.read()
        except Exception as e:
            report = ReviewReport(file_path=file_path, score=0.0, is_approved=False)
            report.findings.append(ReviewFinding(
                severity="CRITICAL",
                pillar="File System",
                message=f"Failed to read file: {e}"
            ))
            return report

        return self.review_code_string(code, file_label=file_path)

    # ── PILLAR 1: AST SEMANTIC PATTERNS ──────────────────────────────────────
    def _audit_ast_patterns(self, code: str, report: ReviewReport):
        """Inspects the syntax tree for concurrency traps and missing safeguards."""
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            report.findings.append(ReviewFinding(
                severity="CRITICAL",
                pillar="Syntax",
                message=f"Syntax Error on line {se.lineno}: {se.msg}",
                fix_suggestion="Fix Python syntax error before proceeding."
            ))
            return

        # 1. Check for ThreadPoolExecutor context manager trap
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    expr_str = ast.unparse(item.context_expr) if hasattr(ast, "unparse") else ""
                    if "ThreadPoolExecutor" in expr_str:
                        # Check if inside the with block there is a timeout or result()
                        with_body_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
                        if "timeout" in with_body_str or "result(" in with_body_str:
                            report.findings.append(ReviewFinding(
                                severity="CRITICAL",
                                pillar="Concurrency",
                                message="ThreadPoolExecutor used as context manager ('with ThreadPoolExecutor(...)').",
                                code_snippet=expr_str,
                                fix_suggestion="ThreadPoolExecutor.__exit__ automatically calls shutdown(wait=True). If the worker hits an infinite loop, the with-block freezes forever! Use a daemon threading.Thread with join(timeout) instead."
                            ))

        # 2. Check for missing @functools.wraps on inner decorator wrappers
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check inner functions that look like decorators
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef) and sub.name in ["wrapper", "decorated", "_wrapper"]:
                        dec_names = [ast.unparse(d) if hasattr(ast, "unparse") else "" for d in sub.decorator_list]
                        has_wraps = any("wraps" in d for d in dec_names)
                        if not has_wraps:
                            report.findings.append(ReviewFinding(
                                severity="WARNING",
                                pillar="Decorators",
                                message=f"Inner decorator function '{sub.name}' is missing @functools.wraps(func).",
                                code_snippet=f"def {sub.name}(*args, **kwargs):",
                                fix_suggestion="Add '@functools.wraps(func)' above the wrapper to preserve function name, docstrings, and parameter signatures."
                            ))

        # 3. Check for daemon=True on threading.Thread
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
                if "Thread" in call_str:
                    kw_names = [kw.arg for kw in node.keywords]
                    if "daemon" not in kw_names:
                        report.findings.append(ReviewFinding(
                            severity="WARNING",
                            pillar="Resource",
                            message="threading.Thread created without explicit daemon=True.",
                            fix_suggestion="Add 'daemon=True' when launching worker threads so hanging loops don't prevent application shutdown."
                        ))

        # 4. Check for loose substring checks on power/destructive commands
        dangerous_words = ["lock", "shutdown", "restart", "reboot", "power off"]
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                left_str = ast.unparse(node.left) if hasattr(ast, "unparse") else ""
                comp_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
                for dw in dangerous_words:
                    if f"'{dw}' in" in comp_str or f'"{dw}" in' in comp_str:
                        if not ("re.search" in code or r"\b" in code):
                            report.findings.append(ReviewFinding(
                                severity="WARNING",
                                pillar="Security",
                                message=f"Loose substring check for dangerous keyword '{dw}'.",
                                code_snippet=comp_str,
                                fix_suggestion=f"Words like 'blocked' or 'clock' will trigger loose checks. Use regex with word boundaries: re.search(r'\\b{dw}\\b', text)."
                            ))

    # ── PILLAR 2: TOOL CONTRACT VALIDATION ────────────────────────────────────
    def _audit_tool_contract(self, code: str, report: ReviewReport):
        """Verifies (handled: bool, response: str) tuple integrity."""
        # Detect stringification of inner return: result[1] = str(val) without tuple check
        if "str(val)" in code or "str(result)" in code:
            if not ("isinstance" in code and "tuple" in code):
                report.findings.append(ReviewFinding(
                    severity="CRITICAL",
                    pillar="Contract",
                    message="Tool return value stringified without tuple type-guard.",
                    code_snippet="result[1] = str(val)",
                    fix_suggestion="In Aria's architecture, tools return (handled: bool, response: str). If val is already a tuple, passing str(val) produces '(True, ...)' strings. Check 'if isinstance(val, tuple) and len(val) == 2: return val'."
                ))

    # ── PILLAR 3: DYNAMIC CHAOS & INFINITE LOOP STRESS TEST ───────────────────
    def _audit_dynamic_chaos(self, code: str, report: ReviewReport):
        """Executes the code against simulated infinite loops in an isolated subprocess."""
        # Only run dynamic stress testing if code defines a watchdog or timeout wrapper
        if not any(k in code for k in ["monitor_execution", "timeout", "watchdog", "circuit_breaker"]):
            return

        test_harness = f"""
import sys, time, threading
{code}

# Simulated runaway function that loops infinitely
def runaway():
    while True:
        time.sleep(0.01)

start_time = time.time()
try:
    # Check if monitor_execution takes a parameter or directly decorates
    try:
        dec = monitor_execution(0.4)
        wrapped = dec(runaway)
    except Exception:
        wrapped = monitor_execution(runaway)
    
    res = wrapped()
    elapsed = time.time() - start_time
    print(f"CHAOS_SUCCESS:{{round(elapsed, 2)}}:{{res}}")
except Exception as ex:
    print(f"CHAOS_EXCEPTION:{{ex}}")
"""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tf:
            tf.write(test_harness)
            harness_path = tf.name

        try:
            proc = subprocess.run(
                [sys.executable, harness_path],
                capture_output=True,
                text=True,
                timeout=2.0  # Hard 2.0s boundary to catch deadlocks
            )
            out = proc.stdout.strip()
            err = proc.stderr.strip()

            if "CHAOS_SUCCESS" in out:
                parts = out.split("CHAOS_SUCCESS:")[1].split(":", 1)
                elapsed_s = float(parts[0])
                output_val = parts[1] if len(parts) > 1 else ""
                if elapsed_s > 1.2:
                    report.findings.append(ReviewFinding(
                        severity="CRITICAL",
                        pillar="Chaos Test",
                        message=f"Chaos Stress Test failed: Watchdog took {elapsed_s}s to timeout (expected < 0.6s).",
                        fix_suggestion="The timeout thread is blocking the main caller. Use threading.Thread(daemon=True) with join(timeout)."
                    ))
                else:
                    report.findings.append(ReviewFinding(
                        severity="PRAISE",
                        pillar="Chaos Test",
                        message=f"Chaos Stress Test passed! Runaway infinite loop successfully broken in {elapsed_s}s."
                    ))
            elif "CHAOS_EXCEPTION" in out:
                report.findings.append(ReviewFinding(
                    severity="WARNING",
                    pillar="Chaos Test",
                    message=f"Chaos test raised exception: {out.split('CHAOS_EXCEPTION:')[1]}"
                ))
            elif proc.returncode != 0:
                report.findings.append(ReviewFinding(
                    severity="CRITICAL",
                    pillar="Chaos Test",
                    message=f"Chaos test crashed with code {proc.returncode}: {err}"
                ))
        except subprocess.TimeoutExpired:
            report.findings.append(ReviewFinding(
                severity="CRITICAL",
                pillar="Chaos Test",
                message="DEADLOCK DETECTED! The process hung permanently on infinite loop and had to be killed!",
                fix_suggestion="Your timeout implementation is blocking! Ensure no context manager (like with ThreadPoolExecutor) is waiting for the worker thread."
            ))
        finally:
            try:
                os.remove(harness_path)
            except Exception:
                pass

    # ── PILLAR 4: SCORE & SISTERLY COACHING ───────────────────────────────────
    def _calculate_score_and_verdict(self, report: ReviewReport):
        score = 10.0
        crit_count = 0
        warn_count = 0

        for f in report.findings:
            if f.severity == "CRITICAL":
                score -= 3.5
                crit_count += 1
            elif f.severity == "WARNING":
                score -= 1.0
                warn_count += 1

        report.score = max(0.0, min(10.0, score))
        report.critical_count = crit_count
        report.warning_count = warn_count
        report.is_approved = (crit_count == 0 and report.score >= 8.5)

        # Generate GAIA's Sisterly Coaching Feedback
        if report.is_approved:
            report.sisterly_coaching = f"🌟 Big Sister GAIA Approval: Score {report.score}/10! Little sis, your code passed all architectural guardrails and survived the chaos stress-tests! Ready for Dad to promote to Golden Anchor!"
        else:
            issues = [f.message for f in report.findings if f.severity == "CRITICAL"]
            if not issues:
                issues = [f.message for f in report.findings if f.severity == "WARNING"]
            main_issue = issues[0] if issues else "Architectural issues detected."
            report.sisterly_coaching = f"👩‍🏫 Big Sister GAIA: Hold on, little sis! Score is {report.score}/10. We found a critical issue: {main_issue}. Let's fix this together before Dad promotes it to C:!"


def format_markdown_receipt(report: ReviewReport) -> str:
    """Formats a detailed GAIA architectural audit entry for changelogs."""
    timestamp = time.strftime("%Y-%m-%d %I:%M %p")
    verdict = "✅ APPROVED FOR GOLDEN ANCHOR" if report.is_approved else "🚫 BLOCKED (NEEDS REFACTOR)"
    
    entry = f"\n---\n### 🛡️ GAIA Supervisor Code Review — {timestamp}\n"
    entry += f"- **Target File:** `{report.file_path}`\n"
    entry += f"- **Quality Score:** **{report.score}/10** ({verdict})\n"
    entry += f"- **Audit Metrics:** {report.critical_count} Critical Issues, {report.warning_count} Warnings\n"
    entry += "- **Review Findings:**\n"
    if not report.findings:
        entry += "  - ✨ Zero issues found. Clean syntax, contracts, and resource management.\n"
    else:
        for f in report.findings:
            icon = "❌" if f.severity == "CRITICAL" else ("⚠️" if f.severity == "WARNING" else "✨")
            entry += f"  - {icon} **[{f.pillar}]** {f.message}\n"
            if f.fix_suggestion:
                entry += f"    - *Recommended Fix:* {f.fix_suggestion}\n"
    entry += f"- **Sisterly Coaching:** *\"{report.sisterly_coaching}\"*\n"
    return entry


def log_gaia_audit(report: ReviewReport):
    """Writes GAIA's audit findings directly to E:\\MyAgent\\GAIA_AUDIT_LOG.md and ARIA_CHANGELOG.md."""
    receipt = format_markdown_receipt(report)
    
    # 1. Write to dedicated GAIA_AUDIT_LOG.md on E: and C:
    for base in [r"E:\MyAgent", r"C:\MyAgent\docs"]:
        log_file = os.path.join(base, "GAIA_AUDIT_LOG.md")
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            header = "# 🛡️ GAIA ARCHITECTURAL AUDIT LOG\n*Automated 4-Pillar code reviews conducted by Big Sister GAIA on Aria's lab code.*\n" if not os.path.exists(log_file) else ""
            with open(log_file, "a", encoding="utf-8") as f:
                if header:
                    f.write(header)
                f.write(receipt)
        except Exception:
            pass

    # 2. Append supervisor note to ARIA_CHANGELOG.md on E:
    aria_cl = os.path.join(r"E:\MyAgent", "ARIA_CHANGELOG.md")
    try:
        if os.path.exists(aria_cl):
            with open(aria_cl, "a", encoding="utf-8") as f:
                f.write(receipt)
    except Exception:
        pass


def print_review_report(report: ReviewReport):
    """Prints a clean, formatted report in the terminal."""
    print("=" * 65)
    print(f"👩‍🏫 GAIA ARCHITECTURAL CODE REVIEW: {os.path.basename(report.file_path)}")
    print(f"Overall Quality Score: {report.score}/10 | Approved: {'✅ YES' if report.is_approved else '❌ NO'}")
    print("=" * 65)

    for f in report.findings:
        icon = "❌" if f.severity == "CRITICAL" else ("⚠️" if f.severity == "WARNING" else "✨")
        print(f"{icon} [{f.severity}] [{f.pillar}] {f.message}")
        if f.code_snippet:
            print(f"   Snippet: {f.code_snippet}")
        if f.fix_suggestion:
            print(f"   💡 Fix: {f.fix_suggestion}")

    print("-" * 65)
    print(f"💬 Sisterly Coaching: {report.sisterly_coaching}")
    print("=" * 65)


if __name__ == "__main__":
    reviewer = GaiaReviewer()
    target = sys.argv[1] if len(sys.argv) > 1 else r"E:\MyAgent\core\watchdog_core.py"
    res = reviewer.review_file(target)
    print_review_report(res)
    log_gaia_audit(res)
