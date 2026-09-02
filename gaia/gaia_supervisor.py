"""
gaia/gaia_supervisor.py — The Big Sister & Autonomous AI Supervisor Engine
Orchestrates Aria's self-directed coding sessions, enforces AST security guardrails,
monitors subprocess execution, auto-heals bugs, manages snapshots, and escalates to human/Antigravity.
"""

import os
import sys
import time
import threading
from typing import Dict, Any, Tuple, Optional

from gaia.gaia_safety import audit_code_safety, SafetyReport
from gaia.gaia_runner import run_sandboxed_script, ExecutionResult
from gaia.gaia_healer import GaiaHealer, SANDBOX_DIR, SNAPSHOTS_DIR
from gaia.gaia_voice import gaia_speak, aria_speak
from gaia.gaia_bus import bus
from gaia.sandbox.curiosity import AriaCuriosityEngine

GAIA_DIR = os.path.dirname(os.path.abspath(__file__))
ARIA_LAB_SCRIPT = os.path.join(SANDBOX_DIR, "aria_lab.py")


class GaiaSupervisor:
    """The Big Sister and Security Supervisor for Aria."""
    
    def __init__(self, enable_voice: bool = True):
        self.enable_voice = enable_voice
        self.healer = GaiaHealer(max_retries=3)
        self.curiosity = AriaCuriosityEngine()
        self.is_supervising = False
        self._active_thread = None

    def get_status(self) -> Dict[str, Any]:
        """Returns live telemetry of the supervision system."""
        snaps = self.healer.list_snapshots()
        events = bus.get_recent_events(10)
        return {
            "is_supervising": self.is_supervising,
            "sandbox_dir": SANDBOX_DIR,
            "total_snapshots": len(snaps),
            "latest_snapshot": snaps[0]["snapshot_id"] if snaps else "None",
            "recent_events": events
        }

    def supervise_code_deployment(self, target_filename: str, proposed_code: str, idea_desc: str = "") -> Tuple[bool, str]:
        """
        Full supervisory pipeline:
        1. Static AST Security Audit
        2. Snapshot Creation
        3. Staging Code
        4. Monitored Test Execution
        5. Aria attempts to fix her own mistakes first!
        6. If Aria is stuck -> calls Big Sister GAIA!
        7. Big Sister GAIA auto-heals, explains mistake, and both learn.
        8. Escalation to Human/Antigravity if Unresolved.
        """
        target_path = os.path.join(SANDBOX_DIR, target_filename)

        # ── STEP 1: SECURITY & GUARDRAIL AUDIT ────────────────────────────────
        bus.emit("GAIA", "SECURITY_AUDIT", f"Auditing proposed code for '{target_filename}'...", {"filename": target_filename})
        safety_report = audit_code_safety(proposed_code, SANDBOX_DIR)

        if not safety_report.is_safe:
            bus.emit("GAIA", "SECURITY_REJECT", safety_report.advice, {"violations": safety_report.violations})
            if self.enable_voice:
                gaia_speak(f"Hold on, little sis! That code isn't safe: {safety_report.violations[0]}.")
            return False, f"Security Audit Failed: {safety_report.advice}"

        bus.emit("GAIA", "SECURITY_APPROVE", "Security check passed. Code is safe to test!", {"filename": target_filename})

        # ── STEP 2: CREATE SAFETY SNAPSHOT ────────────────────────────────────
        snap_id = self.healer.create_snapshot(label=f"pre_{target_filename.replace('.py', '')}")

        # ── STEP 3: STAGE THE CODE ───────────────────────────────────────────
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(proposed_code)
        except Exception as e:
            return False, f"Failed to write code to sandbox: {e}"

        # ── STEP 4: RUN MONITORED TEST ────────────────────────────────────────
        bus.emit("GAIA", "EXECUTION_START", f"Running monitored test on '{target_filename}'...", {"script": target_filename})
        exec_res = run_sandboxed_script(target_path, cwd=SANDBOX_DIR, timeout_sec=15)

        if exec_res.success:
            success_msg = f"✨ Big Sister Approval: '{target_filename}' tested successfully! (Duration: {exec_res.duration_sec}s)"
            bus.emit("GAIA", "SUCCESS", success_msg, exec_res.to_dict())
            if self.enable_voice:
                gaia_speak("Great job, Aria! Your new code passed all tests and is now active in your lab.")
            self._record_diff_if_any(target_filename, idea_desc, "Tested and approved successfully.")
            return True, success_msg

        # ── STEP 5: ARIA TRIES TO FIX HER OWN ERROR FIRST! ────────────────────
        short_err = exec_res.stderr.strip().splitlines()[-1] if exec_res.stderr.strip() else "Unknown runtime error"
        bus.emit(
            "ARIA", "ERROR_DETECTED",
            f"Uh oh! My code had an error: {short_err}. Let me try to figure this out myself first!",
            exec_res.to_dict()
        )
        if self.enable_voice:
            aria_speak("Uh oh! My code had an error. Don't worry big sis, let me try to figure this out myself first!")

        # Aria's self-healing attempt
        aria_healed, aria_exp, aria_code = self.healer.attempt_aria_self_heal(target_path, exec_res.stderr)
        if aria_healed:
            # Re-test Aria's self-repaired code
            aria_test_res = run_sandboxed_script(target_path, cwd=SANDBOX_DIR, timeout_sec=15)
            if aria_test_res.success:
                healed_msg = f"Yay! I fixed it all by myself! {aria_exp}"
                bus.emit("ARIA", "SELF_HEAL_SUCCESS", healed_msg, {"script": target_filename})
                bus.emit("GAIA", "PRAISE", "Proud of you, little sis! You solved it all on your own!", {"script": target_filename})
                if self.enable_voice:
                    aria_speak(f"Yay! I fixed it all by myself! {aria_exp}")
                    gaia_speak("Proud of you, little sis! You're learning fast!")
                self.healer.record_learning(solver="ARIA", script=target_filename, error=short_err, lesson=aria_exp)
                self._record_diff_if_any(target_filename, idea_desc, f"Aria self-healed: {aria_exp}")
                return True, healed_msg
            else:
                exec_res = aria_test_res

        # ── STEP 6: ARIA CANNOT FIX IT -> CALLS BIG SISTER GAIA! ───────────────
        short_err = exec_res.stderr.strip().splitlines()[-1] if exec_res.stderr.strip() else "Unknown runtime error"
        bus.emit(
            "ARIA", "CALL_BIG_SIS",
            f"Big sis, help please! I tried to fix it, but I don't understand this error: {short_err}",
            {"script": target_filename, "error": short_err}
        )
        bus.emit(
            "GAIA", "BIG_SIS_STEP_IN",
            "Don't worry, little sis! Big sister GAIA's got your back. Let me take a look.",
            {"script": target_filename}
        )
        if self.enable_voice:
            aria_speak("Big sis, help please! I'm stuck and can't fix this error!")
            gaia_speak("Don't worry, little sis! Big sister GAIA's got your back. Let me take a look.")

        current_stderr = exec_res.stderr
        for attempt in range(1, self.healer.max_retries + 1):
            healed, explanation, patched_code = self.healer.attempt_auto_heal(target_path, current_stderr, attempt)
            if not healed:
                continue

            # Re-test patched code
            retry_res = run_sandboxed_script(target_path, cwd=SANDBOX_DIR, timeout_sec=15)
            if retry_res.success:
                healed_msg = f"✅ Big Sister GAIA fixed it: {explanation}"
                bus.emit("GAIA", "HEALING_SUCCESS", healed_msg, {"script": target_filename, "attempt": attempt})
                bus.emit("ARIA", "THANK_BIG_SIS", "Thank you, big sis! You're the best! I learned how to do it now.", {"script": target_filename})
                if self.enable_voice:
                    gaia_speak(explanation)
                    aria_speak("Thank you, big sis! You're the best! I understand now.")
                self.healer.record_learning(solver="GAIA_ASSISTED", script=target_filename, error=short_err, lesson=explanation)
                self._record_diff_if_any(target_filename, idea_desc, f"GAIA assisted: {explanation}")
                return True, healed_msg
            else:
                current_stderr = retry_res.stderr

        # ── STEP 7: ESCALATION TO USER & ANTIGRAVITY ──────────────────────────
        escalation_msg = self.healer.escalate_incident(target_path, proposed_code, current_stderr, self.healer.max_retries)
        if self.enable_voice:
            gaia_speak("Aria and I ran into an error we couldn't resolve together. I've rolled back her code and alerted you and Antigravity!")

        return False, escalation_msg

    def run_curiosity_cycle(self, custom_topic: str = None) -> Tuple[bool, str]:
        """
        Executes one full autonomous cycle for Aria under GAIA's supervision:
        1. Aria formulates an idea.
        2. Aria researches online.
        3. Aria writes Python tool code.
        4. GAIA supervises, audits, executes, and heals.
        """
        self.is_supervising = True
        try:
            # 1. Aria brainstorms
            idea = self.curiosity.formulate_next_idea(custom_topic)
            bus.emit("GAIA", "ENCOURAGEMENT", "Sounds fun, little sis! Go ahead and test it, I'm watching the logs.", {"idea": idea})
            if self.enable_voice:
                aria_speak(f"I want to {idea.lower()}!")
                gaia_speak("Sounds fun, little sis! Go ahead and test it, I'm watching the logs.")
            time.sleep(1)

            # 2. Aria researches
            notes = self.curiosity.research_topic(idea)
            time.sleep(1)

            # 3. Aria writes code
            tool_name, tool_file, code = self.curiosity.draft_tool_code(idea, notes)
            tools_subfolder = os.path.join("tools", tool_file)
            time.sleep(1)

            # 4. GAIA supervises deployment
            success, msg = self.supervise_code_deployment(tools_subfolder, code, idea_desc=idea)

            # 5. Also run Aria's overall lab diagnostics
            if success and os.path.exists(ARIA_LAB_SCRIPT):
                diag_res = run_sandboxed_script(ARIA_LAB_SCRIPT, cwd=SANDBOX_DIR, timeout_sec=10)
                bus.emit("ARIA", "DIAGNOSTICS", f"Aria Lab Diagnostics: {'PASS' if diag_res.success else 'FAIL'}", diag_res.to_dict())

            # 6. Auto-sync to GCS Cloud Vault and prune local snapshot bloat (>24h)
            try:
                from gaia.gaia_vault import vault
                threading.Thread(target=vault.sync_vault, kwargs={"retention_hours": 24}, daemon=True).start()
            except Exception:
                pass

            return success, msg
        finally:
            self.is_supervising = False

    def trigger_curiosity_async(self, custom_topic: str = None):
        """Runs the curiosity cycle in a background thread."""
        if self.is_supervising:
            return False, "Supervision already running."

        self._active_thread = threading.Thread(
            target=self.run_curiosity_cycle,
            args=(custom_topic,),
            daemon=True
        )
        self._active_thread.start()
        return True, "Launched autonomous curiosity session in background."

    def _record_diff_if_any(self, target_filename: str, idea_desc: str, explanation: str):
        try:
            from gaia.gaia_diff import compute_diff, record_evolution_changelog
            diff_info = compute_diff()
            if diff_info.get("has_changes"):
                record_evolution_changelog(
                    goal=idea_desc or target_filename,
                    aria_explanation=explanation,
                    gaia_verdict=f"Verified and approved by GAIA in {SANDBOX_DIR}"
                )
                bus.emit("GAIA", "DIFF_RECORDED", f"Recorded evolution diff: {diff_info['summary']}", diff_info)
        except Exception as e:
            print(f"[GAIA Diff] Error: {e}")

    def rollback_latest(self) -> Tuple[bool, str]:
        """Rolls back sandbox to latest stable snapshot."""
        return self.healer.rollback()

    def get_diff(self) -> Dict[str, Any]:
        r"""Returns unified diff between C:\MyAgent\agent.py and E:\MyAgent\aria_evolved.py."""
        from gaia.gaia_diff import compute_diff
        return compute_diff()

    def promote_to_c(self) -> Tuple[bool, str]:
        r"""Promotes Aria's evolved code in E:\MyAgent\aria_evolved.py to C:\MyAgent\agent.py."""
        from gaia.gaia_diff import promote_to_production
        return promote_to_production()

    def reset_e_from_c(self) -> Tuple[bool, str]:
        r"""Resets E:\MyAgent\aria_evolved.py to match pristine C:\MyAgent\agent.py."""
        from gaia.gaia_diff import reset_to_baseline
        return reset_to_baseline()


# Global Singleton
supervisor = GaiaSupervisor(enable_voice=True)
