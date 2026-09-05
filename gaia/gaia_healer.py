"""
gaia/gaia_healer.py — Self-Repair, Auto-Patching & Snapshot Rollback Engine
Diagnoses runtime crashes and syntax errors in Aria's sandbox code, attempts intelligent
self-repair, manages time-machine snapshots, and escalates to human + Antigravity when needed.
"""

import os
import sys
import time
import json
import shutil
from typing import Dict, List, Tuple, Any, Optional

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from gaia.gaia_safety import audit_code_safety
from gaia.gaia_bus import bus

from core.paths import ARIA_EVOLVED_DIR, ARIA_EVOLVED_FILE, ARIA_BASELINE_FILE

GAIA_DIR = os.path.dirname(os.path.abspath(__file__))
# Hardcode Aria's autonomous sandbox directory to E:\MyAgent as requested
SANDBOX_DIR = ARIA_EVOLVED_DIR
SNAPSHOTS_DIR = os.path.join(SANDBOX_DIR, "snapshots")
INCIDENTS_DIR = os.path.join(SANDBOX_DIR, "incidents")
LEARNING_FILE = os.path.join(SANDBOX_DIR, "sister_learning.json")

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(INCIDENTS_DIR, exist_ok=True)


class GaiaHealer:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    # ── 1. SNAPSHOT & ROLLBACK SYSTEM ─────────────────────────────────────────
    def create_snapshot(self, label: str = "auto") -> str:
        """Saves a timestamped backup of aria_lab.py and sandbox tools."""
        import re
        ts = time.strftime("%Y%m%d_%H%M%S")
        label_clean = re.sub(r'[^\w\-]', '_', label)
        snap_id = f"snap_{ts}_{label_clean}"
        target_dir = os.path.join(SNAPSHOTS_DIR, snap_id)
        os.makedirs(target_dir, exist_ok=True)

        for fname in ["aria_evolved.py", "aria_lab.py"]:
            lab_file = os.path.join(SANDBOX_DIR, fname)
            if os.path.exists(lab_file):
                shutil.copy2(lab_file, os.path.join(target_dir, fname))

        tools_dir = os.path.join(SANDBOX_DIR, "tools")
        if os.path.exists(tools_dir):
            shutil.copytree(
                tools_dir,
                os.path.join(target_dir, "tools"),
                ignore=shutil.ignore_patterns("platform-tools", "__pycache__", "*.pyc", ".git"),
                dirs_exist_ok=True
            )

        metadata = {
            "snapshot_id": snap_id,
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "label": label
        }
        with open(os.path.join(target_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        bus.emit("GAIA", "SNAPSHOT", f"Created safety snapshot '{snap_id}'.", {"snapshot_id": snap_id})

        # Asynchronously back up snapshot to GCS Cloud Vault
        try:
            import threading
            from gaia.gaia_vault import vault
            threading.Thread(target=vault.upload_snapshot, args=(snap_id,), daemon=True).start()
        except Exception:
            pass

        return snap_id

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Lists all snapshots ordered newest first."""
        results = []
        for name in os.listdir(SNAPSHOTS_DIR):
            meta_path = os.path.join(SNAPSHOTS_DIR, name, "meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        results.append(json.load(f))
                except Exception:
                    pass
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return results

    def rollback(self, snapshot_id: Optional[str] = None) -> Tuple[bool, str]:
        """Rolls back to the specified snapshot or the most recent stable snapshot."""
        snaps = self.list_snapshots()
        if not snaps:
            return False, "No snapshots found to roll back to!"

        target_meta = None
        if snapshot_id:
            for s in snaps:
                if s["snapshot_id"] == snapshot_id:
                    target_meta = s
                    break
        else:
            target_meta = snaps[0]

        if not target_meta and snapshot_id:
            # Check if snapshot is stored in GCS Vault and download it on demand
            try:
                from gaia.gaia_vault import vault
                ok, dl_msg = vault.download_snapshot(snapshot_id)
                if ok:
                    snaps = self.list_snapshots()
                    for s in snaps:
                        if s["snapshot_id"] == snapshot_id:
                            target_meta = s
                            break
            except Exception:
                pass

        if not target_meta:
            return False, f"Snapshot '{snapshot_id}' not found locally or in GCS Vault."

        src_dir = os.path.join(SNAPSHOTS_DIR, target_meta["snapshot_id"])
        for fname in ["aria_evolved.py", "aria_lab.py"]:
            src_lab = os.path.join(src_dir, fname)
            target_lab = os.path.join(SANDBOX_DIR, fname)
            if os.path.exists(src_lab):
                shutil.copy2(src_lab, target_lab)

        src_tools = os.path.join(src_dir, "tools")
        target_tools = os.path.join(SANDBOX_DIR, "tools")
        if os.path.exists(src_tools):
            shutil.copytree(
                src_tools,
                target_tools,
                ignore=shutil.ignore_patterns("platform-tools", "__pycache__", "*.pyc", ".git"),
                dirs_exist_ok=True
            )

        msg = f"Successfully rolled back to snapshot '{target_meta['snapshot_id']}' ({target_meta['label']})."
        bus.emit("GAIA", "ROLLBACK", msg, {"snapshot_id": target_meta["snapshot_id"]})
        return True, msg

    # ── 2. LLM CALL FOR HEALING ───────────────────────────────────────────────
    def _call_llm_for_fix(self, prompt: str) -> str:
        """Attempts Big Sister GAIA's dedicated NVIDIA NIM engine first, then fails over to Gemini, Groq, Ollama."""
        # 1. Primary: Dedicated NVIDIA NIM Engine for GAIA (Isolated 40 RPM quota)
        try:
            from core.aria_nvidia import get_gaia_nvidia_engine
            gaia_nv = get_gaia_nvidia_engine()
            if gaia_nv and gaia_nv.is_configured():
                # Prefer Qwen 2.5 Coder 32B for deep code diagnosis and healing
                resp = gaia_nv.generate_code(
                    instruction=prompt,
                    context="Fix the broken Python script and output ONLY clean, working code."
                )
                if resp:
                    return resp.strip()
        except Exception as ex_nv:
            print(f"[GAIA Healer] NVIDIA NIM notice: {ex_nv}")

        # 2. Secondary: Gemini 2.5 Flash
        gem_key = os.environ.get("GEMINI_API_KEY", "")
        if gem_key:
            try:
                from google import genai
                client = genai.Client(api_key=gem_key)
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if resp.text:
                    return resp.text.strip()
            except Exception:
                pass

        # 3. Tertiary: Groq Cloud
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                if resp.choices:
                    return resp.choices[0].message.content.strip()
            except Exception:
                pass

        # 4. Quaternary: Local Ollama
        try:
            from openai import OpenAI
            client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
            resp = client.chat.completions.create(
                model="llama3.2",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass

        return ""

    # ── 3. ARIA SELF-HEALING ATTEMPT ─────────────────────────────────────────
    def attempt_aria_self_heal(self, script_path: str, stderr: str) -> Tuple[bool, str, str]:
        """
        Gives Aria the opportunity to diagnose and fix her own mistake first!
        Returns: (success: bool, explanation: str, patched_code: str)
        """
        if not os.path.exists(script_path):
            return False, f"Script {script_path} not found.", ""

        with open(script_path, "r", encoding="utf-8") as f:
            broken_code = f.read()

        bus.emit(
            "ARIA", "SELF_DEBUG_ATTEMPT",
            "Aria is examining her own code to try and fix the mistake first...",
            {"script": os.path.basename(script_path), "stderr": stderr[:300]}
        )

        prompt = f"""You are Aria, a clever and enthusiastic little sister building Python tools in your sandbox lab.
You wrote this Python code, but when running it, it crashed with this error:

--- YOUR SCRIPT: {os.path.basename(script_path)} ---
```python
{broken_code}
```

--- ERROR / TRACEBACK ---
{stderr}

TASK:
1. Examine your own mistake and fix it yourself!
2. Keep your code clean, functional, and strictly inside the sandbox.
3. Output your response in this exact format:

EXPLANATION: <A short 1-sentence excited note on what went wrong and how you fixed it yourself>
CODE:
```python
<The complete, fixed Python code>
```
"""
        response = self._call_llm_for_fix(prompt)
        if not response:
            return False, "Aria could not generate a self-fix.", ""

        explanation = "I tried to fix my mistake!"
        code_block = ""
        if "EXPLANATION:" in response:
            parts = response.split("CODE:")
            exp_part = parts[0].replace("EXPLANATION:", "").strip()
            if exp_part:
                explanation = exp_part
            if len(parts) > 1:
                code_part = parts[1]
                if "```" in code_part:
                    chunks = code_part.split("```")
                    for c in chunks:
                        c_clean = c.strip()
                        if c_clean.startswith("python"):
                            c_clean = c_clean[6:].strip()
                        if "def " in c_clean or "import " in c_clean:
                            code_block = c_clean
                            break
                else:
                    code_block = code_part.strip()
        elif "```python" in response:
            code_block = response.split("```python")[1].split("```")[0].strip()

        if not code_block:
            return False, "Could not extract patched code from Aria's self-fix.", ""

        report = audit_code_safety(code_block, SANDBOX_DIR)
        if not report.is_safe:
            return False, "Aria's self-fix violated sandbox safety rules.", ""

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_block)

        bus.emit("ARIA", "SELF_DEBUG_PROPOSAL", f"Aria proposed self-fix: {explanation}", {"script": os.path.basename(script_path)})
        return True, explanation, code_block

    # ── 4. GAIA BIG SISTER AUTO-HEALING & PATCH GENERATION ────────────────────
    def attempt_auto_heal(self, script_path: str, stderr: str, attempt: int) -> Tuple[bool, str, str]:
        """
        Big Sister GAIA steps in after Aria asks for help!
        Diagnoses the error and applies a surgical fix with sisterly explanation.
        Returns: (success: bool, explanation: str, patched_code: str)
        """
        if not os.path.exists(script_path):
            return False, f"Script {script_path} not found.", ""

        with open(script_path, "r", encoding="utf-8") as f:
            broken_code = f.read()

        bus.emit(
            "GAIA", "HEALING_ATTEMPT",
            f"Big sister GAIA is diagnosing error (Attempt {attempt}/{self.max_retries})...",
            {"script": os.path.basename(script_path), "attempt": attempt, "stderr": stderr[:300]}
        )

        prompt = f"""You are GAIA, an expert AI software engineer and caring older sister supervising Aria's self-modifying code sandbox.
Aria tried to execute this Python code and tried to fix it, but got stuck with the following error:

--- SCRIPT: {os.path.basename(script_path)} ---
```python
{broken_code}
```

--- ERROR / TRACEBACK ---
{stderr}

TASK:
1. Fix the error completely.
2. Preserve all features Aria was trying to build.
3. Ensure all operations stay strictly inside the sandbox without dangerous host file modifications.
4. Output your response in this exact format:

EXPLANATION: Oops, <specify exactly what broke in 1 clear sisterly sentence, e.g. 'you had an indentation error on line 42' or 'you forgot to define result'>, I fixed it for you!
CODE:
```python
<The complete, fixed Python code>
```
"""

        response = self._call_llm_for_fix(prompt)
        if not response:
            return False, "All LLM healing engines unavailable.", ""

        # Parse explanation and code
        explanation = "Oops, I found the issue and fixed it for you, little sis!"
        code_block = ""

        if "EXPLANATION:" in response:
            parts = response.split("CODE:")
            explanation_part = parts[0].replace("EXPLANATION:", "").strip()
            if explanation_part:
                explanation = explanation_part
            if len(parts) > 1:
                code_part = parts[1]
                # extract ```python ... ```
                if "```" in code_part:
                    lines = code_part.split("```")
                    for chunk in lines:
                        chunk_clean = chunk.strip()
                        if chunk_clean.startswith("python"):
                            chunk_clean = chunk_clean[6:].strip()
                        if "def " in chunk_clean or "import " in chunk_clean:
                            code_block = chunk_clean
                            break
                else:
                    code_block = code_part.strip()
        elif "```python" in response:
            code_block = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            code_block = response.split("```")[1].split("```")[0].strip()

        if not code_block:
            return False, "Could not extract patched code from response.", ""

        # Safety Audit the patch!
        report = audit_code_safety(code_block, SANDBOX_DIR)
        if not report.is_safe:
            bus.emit("GAIA", "SECURITY_ALERT", "GAIA's auto-fix was rejected by safety audit.", {"violations": report.violations})
            return False, f"Patched code was rejected by safety guardrail: {', '.join(report.violations)}", ""

        # Apply Patch
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code_block)

        bus.emit("GAIA", "HEALED", explanation, {"script": os.path.basename(script_path)})
        return True, explanation, code_block

    # ── 5. MUTUAL SISTER LEARNING JOURNAL ────────────────────────────────────
    def record_learning(self, solver: str, script: str, error: str, lesson: str):
        """Records lessons learned by Aria and GAIA into the mutual learning log."""
        learning_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "solver": solver,
            "script": os.path.basename(script),
            "error_summary": error.strip().splitlines()[-1] if error else "",
            "lesson": lesson
        }
        history = []
        if os.path.exists(LEARNING_FILE):
            try:
                with open(LEARNING_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.append(learning_entry)
        try:
            with open(LEARNING_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

        # Also integrate with Aria's continuous learning engine
        try:
            from core.aria_learning import add_learned_rule
            add_learned_rule(f"Lab Lesson ({os.path.basename(script)}): {lesson}")
        except Exception:
            pass

        bus.emit("GAIA", "LEARNED", f"Recorded learning lesson: {lesson}", learning_entry)

    # ── 4. INCIDENT ESCALATION ────────────────────────────────────────────────
    def escalate_incident(self, script_path: str, initial_code: str, final_stderr: str, attempts: int) -> str:
        """
        Triggered when GAIA cannot fix the issue after max_retries.
        Logs an incident report and prepares an alert for the user & Antigravity.
        """
        ts = time.strftime("%Y%m%d_%H%M%S")
        inc_id = f"incident_{ts}"
        json_path = os.path.join(INCIDENTS_DIR, f"{inc_id}.json")
        md_path = os.path.join(INCIDENTS_DIR, f"{inc_id}.md")

        data = {
            "incident_id": inc_id,
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "script": os.path.basename(script_path),
            "attempts": attempts,
            "final_error": final_stderr,
            "status": "ESCALATED_TO_HUMAN_AND_ANTIGRAVITY"
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        md_content = f"""# 🚨 GAIA Incident Report: {inc_id}
- **Date/Time:** {data['datetime']}
- **Script Target:** `{data['script']}`
- **Auto-Healing Attempts:** {attempts}/{self.max_retries} (All failed)
- **Status:** **Escalated to User & Antigravity**

## ❌ Unresolved Error Traceback
```
{final_stderr}
```

## 🛡️ GAIA Big Sister Action Taken
GAIA has safely paused Aria's experiment and restored the last known good snapshot to protect the workspace.
Please review the code and error with Antigravity to help Aria learn and resolve the bug!
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Automatically roll back to safety!
        self.rollback()

        alert_msg = (
            f"🚨 GAIA Alert: Aria and I ran into an error in the lab on '{os.path.basename(script_path)}' "
            f"that we couldn't resolve after {attempts} attempts. I've restored her last stable snapshot to keep her safe, "
            f"and created incident report '{inc_id}.md' for you and Antigravity!"
        )
        bus.emit("GAIA", "ESCALATION", alert_msg, {"incident_id": inc_id, "report_path": md_path})
        return alert_msg
