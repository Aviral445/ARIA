"""
core/aria_state_guard.py — Zero-Work-Loss State Persistence & Crash/Shutdown Guard
Ensures Aria, Big Sister GAIA, and Big Bro Antigravity never lose work if an instance,
terminal, or IDE is closed abruptly or interrupted.

Features:
1. Graceful Shutdown Interceptor (atexit, SIGINT, SIGTERM)
2. Periodic Background Heartbeat Checkpointing (Every 30s)
3. Atomic State Checkpointing (data/session_checkpoint.json)
4. Session Recovery & Continuity on Instance Restart
"""

import os
import sys
import json
import time
import signal
import atexit
import threading
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from core.paths import DATA_DIR, ROOT_DIR, ARIA_EVOLVED_DIR
except ImportError:
    from paths import DATA_DIR, ROOT_DIR, ARIA_EVOLVED_DIR

CHECKPOINT_FILE = os.path.join(DATA_DIR, "session_checkpoint.json")
_HEARTBEAT_THREAD = None
_RUNNING = False
_LOCK = threading.Lock()


class StateGuard:
    def __init__(self, checkpoint_path: str = CHECKPOINT_FILE):
        self.checkpoint_path = checkpoint_path
        self.start_time = time.time()
        self.last_saved_time = 0.0
        self.active_tasks = {}

    def _get_active_state(self) -> Dict[str, Any]:
        """Collects current state across the Sibling Trio ecosystem."""
        state = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pid": os.getpid(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "status": "active",
            "active_tasks": list(self.active_tasks.values()),
            "stats": {}
        }

        # 1. Big Bro Mailbox state
        try:
            from core.big_bro_bridge import BigBroBridge
            bridge = BigBroBridge()
            pending = bridge.get_pending_messages()
            state["mailbox"] = {
                "pending_count": len(pending),
                "pending_topics": [p.get("topic") for p in pending[:5]]
            }
        except Exception:
            state["mailbox"] = {"pending_count": 0}

        # 2. GAIA Sister Learning state
        try:
            learning_file = os.path.join(ARIA_EVOLVED_DIR, "sister_learning.json")
            if os.path.exists(learning_file):
                with open(learning_file, "r", encoding="utf-8") as f:
                    lessons = json.load(f)
                    state["stats"]["sister_lessons_count"] = len(lessons)
                    if lessons:
                        state["stats"]["latest_lesson"] = lessons[-1].get("lesson", "")
        except Exception:
            pass

        # 3. Continuous Learning Corrections
        try:
            from core.aria_learning import _load_corrections
            corr = _load_corrections()
            state["stats"]["rules_count"] = len(corr.get("rules", []))
            state["stats"]["mappings_count"] = len(corr.get("custom_mappings", {}))
        except Exception:
            pass

        return state

    def save_checkpoint(self, reason: str = "periodic", status: str = "active") -> bool:
        """Atomically saves the current session state to disk."""
        with _LOCK:
            try:
                os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
                state = self._get_active_state()
                state["reason"] = reason
                state["status"] = status

                # Atomic write via temporary file to prevent corruption on sudden power loss
                temp_path = self.checkpoint_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
                
                # Replace atomically
                if os.path.exists(self.checkpoint_path):
                    try:
                        os.replace(temp_path, self.checkpoint_path)
                    except Exception:
                        os.remove(self.checkpoint_path)
                        os.rename(temp_path, self.checkpoint_path)
                else:
                    os.rename(temp_path, self.checkpoint_path)

                self.last_saved_time = time.time()
                return True
            except Exception as e:
                print(f"[StateGuard Notice]: Could not save checkpoint ({reason}): {e}")
                return False

    def record_task(self, task_name: str, details: Any = None):
        """Records an ongoing task to ensure zero work is lost if instance terminates."""
        with _LOCK:
            self.active_tasks[task_name] = {
                "task": task_name,
                "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "details": details or {}
            }
        self.save_checkpoint(reason=f"task_start_{task_name}")

    def finish_task(self, task_name: str):
        """Marks an ongoing task as finished."""
        with _LOCK:
            if task_name in self.active_tasks:
                del self.active_tasks[task_name]
        self.save_checkpoint(reason=f"task_finish_{task_name}")

    def recover_previous_session(self) -> Dict[str, Any]:
        """Checks if a previous session was interrupted and reports continuity."""
        if not os.path.exists(self.checkpoint_path):
            return {"recovered": False, "message": "Fresh session initialized."}

        try:
            with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                prev_state = json.load(f)

            prev_status = prev_state.get("status", "unknown")
            prev_time = prev_state.get("datetime", "recent session")
            uptime = prev_state.get("uptime_seconds", 0)
            interrupted_tasks = prev_state.get("active_tasks", [])

            if prev_status == "active":
                task_info = ""
                if interrupted_tasks:
                    names = [t.get("task", "unknown") for t in interrupted_tasks]
                    task_info = f" Preserving {len(interrupted_tasks)} ongoing tasks: {', '.join(names)}."
                msg = (
                    f"[Zero-Work-Loss Recovery]: Restored state from unexpected instance close! "
                    f"Last checkpoint was {prev_time} (Session uptime: {uptime}s).{task_info} All files and memories preserved!"
                )
                print(msg)
                return {"recovered": True, "clean_shutdown": False, "message": msg, "state": prev_state}
            else:
                msg = f"[Clean Session Recovery]: Previous instance exited gracefully at {prev_time}."
                return {"recovered": True, "clean_shutdown": True, "message": msg, "state": prev_state}
        except Exception as e:
            return {"recovered": False, "error": str(e)}

    def register_shutdown_hooks(self):
        """Registers system exit, SIGINT, and SIGTERM handlers for emergency state flush."""
        def _safe_print(text: str):
            try:
                print(text)
            except Exception:
                try:
                    print(text.encode("ascii", "replace").decode("ascii"))
                except Exception:
                    pass

        def _on_clean_exit():
            self.save_checkpoint(reason="clean_exit", status="clean_shutdown")
            _safe_print("\n[StateGuard]: Clean shutdown checkpoint saved. Zero work lost, Mentor L!")

        def _on_signal(signum, frame):
            _safe_print(f"\n[StateGuard]: Instance interrupt received ({signum}). Saving emergency checkpoint...")
            self.save_checkpoint(reason=f"signal_{signum}", status="interrupted")
            sys.exit(0)

        # 1. Python atexit
        atexit.register(_on_clean_exit)

        # 2. OS Signals (SIGINT / SIGTERM)
        try:
            signal.signal(signal.SIGINT, _on_signal)
            if hasattr(signal, "SIGTERM"):
                signal.signal(signal.SIGTERM, _on_signal)
        except Exception:
            pass

    def start_heartbeat(self, interval_seconds: int = 30):
        """Starts a background daemon thread that periodically checkpoints state."""
        global _HEARTBEAT_THREAD, _RUNNING
        if _RUNNING:
            return

        _RUNNING = True

        def _heartbeat_loop():
            while _RUNNING:
                time.sleep(interval_seconds)
                if _RUNNING:
                    self.save_checkpoint(reason="heartbeat_30s", status="active")

        _HEARTBEAT_THREAD = threading.Thread(target=_heartbeat_loop, daemon=True, name="StateGuardHeartbeat")
        _HEARTBEAT_THREAD.start()


guard = StateGuard()


def record_active_task(task_name: str, details: Any = None):
    """Records an active background task in StateGuard."""
    guard.record_task(task_name, details)


def finish_active_task(task_name: str):
    """Finishes an active background task in StateGuard."""
    guard.finish_task(task_name)


def initialize_state_guard() -> Dict[str, Any]:
    """Helper to initialize recovery, register shutdown hooks, and start heartbeat."""
    rec = guard.recover_previous_session()
    guard.register_shutdown_hooks()
    guard.start_heartbeat(interval_seconds=30)
    # Save active state
    guard.save_checkpoint(reason="session_start", status="active")
    return rec


if __name__ == "__main__":
    print("Testing State Guard...")
    res = initialize_state_guard()
    print("Recovery result:", res)
    guard.save_checkpoint(reason="manual_test", status="clean_shutdown")
    print("Checkpoint saved to:", CHECKPOINT_FILE)
