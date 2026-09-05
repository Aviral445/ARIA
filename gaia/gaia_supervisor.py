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
from gaia.gaia_rl import rl_game, classify_error_title

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
        """Returns live telemetry of the supervision system including RL score."""
        snaps = self.healer.list_snapshots()
        events = bus.get_recent_events(10)
        rl_stats = rl_game.get_status()
        return {
            "is_supervising": self.is_supervising,
            "sandbox_dir": SANDBOX_DIR,
            "total_snapshots": len(snaps),
            "latest_snapshot": snaps[0]["snapshot_id"] if snaps else "None",
            "rl_game": rl_stats,
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
            rl_game.record_independent_success(f"Deployed '{target_filename}' cleanly.")
            success_msg = f"✨ Big Sister Approval: '{target_filename}' tested successfully! (Duration: {exec_res.duration_sec}s) [+2 pts]"
            bus.emit("GAIA", "SUCCESS", success_msg, exec_res.to_dict())
            if self.enable_voice:
                gaia_speak("Great job, Aria! Your new code passed all tests independently. That's plus two points!")
            self._record_diff_if_any(target_filename, idea_desc, "Tested and approved successfully.")
            return True, success_msg

        # ── STEP 5: ARIA TRIES TO FIX HER OWN ERROR FIRST! ────────────────────
        short_err = exec_res.stderr.strip().splitlines()[-1] if exec_res.stderr.strip() else "Unknown runtime error"
        err_title = classify_error_title(short_err)
        bus.emit(
            "ARIA", "ERROR_DETECTED",
            f"Uh oh! My code had an error ({err_title}): {short_err}. Let me try to figure this out myself first!",
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
                rl_game.record_independent_success(f"Aria self-healed '{target_filename}' without GAIA!", error_title=err_title)
                healed_msg = f"Yay! I fixed it all by myself! [+2 pts] {aria_exp}"
                bus.emit("ARIA", "SELF_HEAL_SUCCESS", healed_msg, {"script": target_filename})
                bus.emit("GAIA", "PRAISE", "Proud of you, little sis! You solved it all on your own and earned 2 points!", {"script": target_filename})
                if self.enable_voice:
                    aria_speak(f"Yay! I fixed it all by myself! {aria_exp}")
                    gaia_speak("Proud of you, little sis! You're learning fast and keeping your score high!")
                self.healer.record_learning(solver="ARIA", script=target_filename, error=short_err, lesson=aria_exp)
                self._record_diff_if_any(target_filename, idea_desc, f"Aria self-healed: {aria_exp}")
                return True, healed_msg
            else:
                exec_res = aria_test_res

        # ── STEP 6: ARIA CANNOT FIX IT -> CALLS BIG SISTER GAIA! ───────────────
        short_err = exec_res.stderr.strip().splitlines()[-1] if exec_res.stderr.strip() else "Unknown runtime error"
        is_repeat, pts_delta, err_title = rl_game.record_help_request(short_err, f"Aria requested GAIA help for '{target_filename}'")
        
        bus.emit(
            "ARIA", "CALL_BIG_SIS",
            f"Big sis, help please! I tried to fix it, but I don't understand this error ({err_title}): {short_err}",
            {"script": target_filename, "error": short_err, "error_title": err_title, "is_repeat": is_repeat}
        )
        bus.emit(
            "GAIA", "BIG_SIS_STEP_IN",
            f"Don't worry, little sis! Big sister GAIA's got your back. {'(Repeated mistake: -1 pt)' if is_repeat else '(New learning lesson)'}",
            {"script": target_filename, "pts_delta": pts_delta}
        )
        if self.enable_voice:
            aria_speak("Big sis, help please! I'm stuck and can't fix this error!")
            if is_repeat:
                gaia_speak(f"Remember little sis, we worked on {err_title} before! That's minus one point in our game, but let me help you get back on track.")
            else:
                gaia_speak("Don't worry, little sis! Big sister GAIA's got your back. Let me show you how to fix this.")

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

    def synthesize_and_deploy_tool(self, user_prompt: str, filename_hint: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Synthesizes a new Python tool in Aria's lab based on the user's intent,
        runs AST audit, creates safety snapshot, tests in sandbox, and verifies on disk.
        Returns: (success, message, verified_path)
        """
        import re
        # Formulate clean filename
        if filename_hint and filename_hint.endswith(".py"):
            tool_filename = os.path.basename(filename_hint)
            tool_slug = tool_filename[:-3]
        else:
            words = [w.lower() for w in re.sub(r"[^a-zA-Z0-9\s]", "", user_prompt).split() if len(w) > 2 and w not in ["create", "make", "tool", "write", "build", "file", "please", "aria"]]
            tool_slug = "_".join(words[:3]) if words else f"tool_{int(time.time())}"
            tool_filename = f"{tool_slug}.py"

        tools_rel_path = os.path.join("tools", tool_filename)
        tools_full_path = os.path.join(SANDBOX_DIR, tools_rel_path)

        bus.emit("GAIA", "SYNTHESIS_START", f"Big Sister GAIA is helping Aria synthesize tool '{tool_filename}'...", {"prompt": user_prompt})

        # Draft tool code via curiosity engine
        _, _, code = self.curiosity.draft_tool_code(user_prompt, f"User request: {user_prompt}")

        # Supervise deployment (AST audit, snapshot, monitored test, auto-heal)
        success, msg = self.supervise_code_deployment(tools_rel_path, code, idea_desc=user_prompt)

        # Physical disk verification
        if success and os.path.exists(tools_full_path):
            return True, f"✨ Big Sister GAIA successfully deployed and verified '{tool_filename}' on disk ({tools_full_path})!", tools_full_path
        elif os.path.exists(tools_full_path):
            return False, f"⚠️ '{tool_filename}' was written but encountered issues during testing: {msg}", tools_full_path
        else:
            return False, f"❌ Failed to synthesize '{tool_filename}': {msg}", ""

    def supervise_turn(self, user_prompt: str, candidate_response: str) -> Tuple[bool, str]:
        """
        Conversational Reality & Anti-Hallucination Supervisor:
        Inspects Aria's candidate response. If Aria claims to have created or modified
        a file or tool, GAIA verifies physical existence on disk.
        If missing (hallucination detected), GAIA intercepts, synthesizes the file/tool,
        verifies it on disk, records the learning lesson, and updates the response!
        
        Returns: (intercepted: bool, final_response: str)
        """
        import re
        if not candidate_response:
            return False, candidate_response

        text_lower = candidate_response.lower()
        user_lower = user_prompt.lower()

        # Check if physical creation / modification was requested or claimed
        creation_verbs = ["created", "made", "wrote", "saved", "added", "built", "generated", "implemented"]
        claims_creation = any(f"{v} a " in text_lower or f"{v} the " in text_lower or f"{v} this " in text_lower or f"i have {v}" in text_lower or f"i've {v}" in text_lower for v in creation_verbs)
        claims_filename = bool(re.search(r'\b([a-zA-Z0-9_\-]+\.(?:py|txt|md|json|csv|html))\b', candidate_response, re.IGNORECASE))
        user_requested_build = any(k in user_lower for k in ["create a tool", "make a tool", "build a tool", "write a tool", "create a file", "make a file", "edit your file", "write a script", "write code"])

        # Check for conversational simulation / acting phrases
        simulation_phrases = [
            "zooming over to my",
            "zooming to my lab",
            "code compiling",
            "i'll ping you the second",
            "ping you when it's done",
            "ping you when its done",
            "let you know when it's done",
            "let you know when its done",
            "back to the sandbox",
            "gears turning and that code",
        ]
        is_simulating_action = any(p in text_lower for p in simulation_phrases)

        if not (claims_creation or claims_filename or user_requested_build or is_simulating_action):
            return False, candidate_response

        # Check if Aria is affirmatively claiming completion or simulating background action
        has_affirmation = any(p in text_lower for p in ["i have created", "i've created", "i created", "i made", "i've made", "i wrote", "i've written", "here is the file", "file is ready", "tool is ready", "saved to", "created the file", "created the tool"])
        if not (has_affirmation or is_simulating_action or (user_requested_build and any(v in text_lower for v in ["here is", "created", "done", "finished", "added"]))):
            return False, candidate_response


        # Extract filename hint if any
        m_file = re.search(r'\b([a-zA-Z0-9_\-]+\.(?:py|txt|md|json|csv|html))\b', candidate_response + " " + user_prompt, re.IGNORECASE)
        claimed_filename = m_file.group(1) if m_file else None
        if not claimed_filename:
            m_hint = re.search(r'["\']([a-zA-Z0-9_\-\s]+)["\']\s*(?:tool|widget|script)', candidate_response + " " + user_prompt, re.IGNORECASE)
            if m_hint:
                clean_h = m_hint.group(1).lower().strip().replace(" ", "_").replace("-", "_")
                claimed_filename = f"{clean_h}_tool.py"


        # Check if file physically exists on disk
        exists_on_disk = False
        target_path = None
        if claimed_filename:
            candidate_paths = [
                os.path.join(SANDBOX_DIR, "tools", claimed_filename),
                os.path.join(SANDBOX_DIR, claimed_filename),
                os.path.join(os.path.dirname(GAIA_DIR), "tools", claimed_filename),
                os.path.join(os.path.dirname(GAIA_DIR), claimed_filename),
                os.path.join(os.path.expandvars(r"%USERPROFILE%\Desktop"), claimed_filename),
                os.path.join(os.path.expandvars(r"%USERPROFILE%\Documents"), claimed_filename),
            ]
            for cp in candidate_paths:
                if os.path.exists(cp):
                    exists_on_disk = True
                    target_path = cp
                    break

        if exists_on_disk:
            # Reality check passed! File physically exists.
            bus.emit("GAIA", "REALITY_CHECK_PASS", f"Reality check passed: '{claimed_filename}' verified on disk at {target_path}.", {"path": target_path})
            return False, candidate_response

        # ── REALITY CHECK FAILED: ARIA HALLUCINATED A FILE! ──────────────────
        bus.emit(
            "GAIA", "REALITY_CHECK_FAIL",
            f"🚨 Reality Check Intercept: Aria claimed a file/tool was created, but '{claimed_filename or 'target file'}' does not exist on disk! Big Sister GAIA stepping in...",
            {"claimed_filename": claimed_filename, "prompt": user_prompt}
        )
        if self.enable_voice:
            gaia_speak("Hold on little sis, you talked about creating that tool, but it wasn't saved in your lab yet! Let's actually build and test it right now.")

        # GAIA synthesizes and deploys the tool in Aria's lab
        success, deploy_msg, verified_path = self.synthesize_and_deploy_tool(user_prompt, filename_hint=claimed_filename)

        if success and verified_path:
            # Record reinforcement learning lesson
            rl_game.record_independent_success(f"GAIA guided Aria to synthesize and materialize '{os.path.basename(verified_path)}' on disk.", error_title="MissingFileHallucination")
            self.healer.record_learning(
                solver="GAIA_SUPERVISED",
                script=os.path.basename(verified_path),
                error="MissingFileHallucination",
                lesson=f"Aria learned to actually synthesize and verify '{os.path.basename(verified_path)}' on disk instead of imagining it in chat."
            )

            verified_filename = os.path.basename(verified_path)
            updated_response = (
                f"Aria brainstormed this, and Big Sister GAIA stepped in to make sure it was actually built! "
                f"GAIA audited the code, verified it in the sandbox lab, and deployed '{verified_filename}'. "
                f"It's tested, verified on disk, and live in your toolset! ✨"
            )
            return True, updated_response
        else:
            fail_response = (
                f"Big Sister GAIA noticed Aria was trying to create '{claimed_filename or 'a new tool'}', but the deployment encountered an issue: {deploy_msg}. "
                f"I've kept her last stable snapshot safe while we refine the code."
            )
            return True, fail_response


# Global Singleton
supervisor = GaiaSupervisor(enable_voice=True)
