"""
aria_scheduler.py — Reminders, Alarms & Pomodoro Focus Timer for Aria
Uses APScheduler in a background thread to trigger audio alerts and desktop notifications.
"""

import os, json, time, threading
from datetime import datetime, timedelta

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False

try:
    from plyer import notification
    HAS_NOTIFY = True
except ImportError:
    HAS_NOTIFY = False

try:
    from .paths import get_data_file
except ImportError:
    from paths import get_data_file

REMINDERS_FILE = get_data_file("reminders.json", create_if_missing=True)

class AriaScheduler:
    def __init__(self, speak_callback=None):
        self.speak_cb = speak_callback
        self.scheduler = BackgroundScheduler(daemon=True) if HAS_SCHEDULER else None
        if self.scheduler:
            self.scheduler.start()
        self.reminders = self._load_reminders()
        self._reschedule_all()

    def _load_reminders(self) -> list:
        if os.path.exists(REMINDERS_FILE):
            try:
                with open(REMINDERS_FILE, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_reminders(self):
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, indent=2)

    def _notify(self, title: str, message: str):
        if HAS_NOTIFY:
            try:
                notification.notify(title=title, message=message, app_name="Aria", timeout=8)
            except Exception:
                pass
        if self.speak_cb:
            try:
                self.speak_cb(f"Reminder: {message}")
            except Exception:
                pass

    def add_reminder_in_seconds(self, message: str, seconds: int) -> str:
        """Sets a timer to trigger in N seconds."""
        due_time = datetime.now() + timedelta(seconds=seconds)
        rem_id = f"rem_{int(time.time())}_{len(self.reminders)}"
        item = {
            "id": rem_id,
            "message": message,
            "due_iso": due_time.isoformat(),
            "time_str": due_time.strftime("%I:%M %p"),
            "done": False
        }
        self.reminders.append(item)
        self._save_reminders()

        if self.scheduler:
            self.scheduler.add_job(
                func=self._trigger_reminder,
                trigger="date",
                run_date=due_time,
                args=[rem_id, message],
                id=rem_id
            )
        return f"Reminder set for {item['time_str']} ({seconds}s from now): '{message}'"

    def _trigger_reminder(self, rem_id: str, message: str):
        for r in self.reminders:
            if r["id"] == rem_id:
                r["done"] = True
                break
        self._save_reminders()
        self._notify("Aria Reminder", message)

    def _reschedule_all(self):
        if not self.scheduler:
            return
        now = datetime.now()
        for r in self.reminders:
            if not r.get("done"):
                try:
                    due = datetime.fromisoformat(r["due_iso"])
                    if due > now:
                        self.scheduler.add_job(
                            func=self._trigger_reminder,
                            trigger="date",
                            run_date=due,
                            args=[r["id"], r["message"]],
                            id=r["id"],
                            replace_existing=True
                        )
                except Exception:
                    pass

    def start_pomodoro(self, minutes: int = 25) -> str:
        """Starts a Pomodoro focus countdown."""
        return self.add_reminder_in_seconds(f"Focus session of {minutes} minutes complete! Time for a short break.", minutes * 60)

    def list_active_reminders(self) -> str:
        active = [r for r in self.reminders if not r.get("done")]
        if not active:
            return "No active reminders or timers."
        lines = ["Active Reminders:"]
        for r in active:
            lines.append(f"• [{r.get('time_str', 'Pending')}] {r.get('message')}")
        return "\n".join(lines)

_global_scheduler = None

def get_scheduler(speak_cb=None):
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = AriaScheduler(speak_callback=speak_cb)
    return _global_scheduler
