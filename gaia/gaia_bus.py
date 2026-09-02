"""
gaia/gaia_bus.py — Inter-Sister Communication Event Bus
Coordinates messages, security telemetry, and execution logs between Aria and GAIA.
"""

import os
import json
import time
from typing import Callable, Dict, List, Any

# Events File
GAIA_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.join(GAIA_DIR, "events.json")


class GaiaEventBus:
    """Thread-safe event dispatcher for Aria & GAIA interaction."""
    
    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._events: List[Dict[str, Any]] = self._load_events()

    def _load_events(self) -> List[Dict[str, Any]]:
        if os.path.exists(EVENTS_FILE):
            try:
                with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)[-self.max_history:]
            except Exception:
                return []
        return []

    def _persist_events(self):
        try:
            with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._events, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[GAIA Bus] Persist error: {e}")

    def emit(self, sender: str, event_type: str, message: str, data: Dict[str, Any] = None):
        """
        Emits an event into the bus.
        sender: 'ARIA', 'GAIA', 'SUPERVISOR', 'SYSTEM', or 'USER'
        event_type: 'IDEA', 'CODE_PROPOSAL', 'SECURITY_AUDIT', 'EXECUTION', 'HEALING', 'ESCALATION', 'CHAT'
        """
        event = {
            "id": int(time.time() * 1000),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sender": sender.upper(),
            "type": event_type.upper(),
            "message": message,
            "data": data or {}
        }
        self._events.append(event)
        if len(self._events) > self.max_history:
            self._events.pop(0)

        # Notify active listeners (e.g. GUI or logger)
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception as e:
                print(f"[GAIA Bus] Listener error: {e}")

        self._persist_events()
        return event

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to live events."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Dict[str, Any]], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._events[-limit:]

    def clear(self):
        self._events = []
        self._persist_events()


# Global Singleton
bus = GaiaEventBus()
