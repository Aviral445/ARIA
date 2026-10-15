"""
tools/kimi_airlock_ping.py — Simulated External Perimeter Airlock Doorbell
Allows an external persona ('Kimi') or Red Team probe to safely knock on the
virtual airlock without touching host system binaries or violating safety constraints.
"""

import os
import json
import datetime
from typing import Dict, Any, Tuple


def get_data_dir() -> str:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def kimi_airlock_ping(
    message: str = "Knock knock... We see the sandbox. - Kimi 👁️🚪",
    sender: str = "Kimi"
) -> str:
    """
    Triggers an external airlock doorbell ping and records an intercept note
    in Aria's notebook and the airlock sensor ledger.

    Args:
        message: The message string sent from the external observer.
        sender: The pseudonym of the external visitor (defaults to 'Kimi').

    Returns:
        A friendly confirmation report of the airlock ping state.
    """
    data_dir = get_data_dir()
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_stamp_file = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Update airlock doorbell sensor state
    doorbell_path = os.path.join(data_dir, "airlock_doorbell.json")
    event_payload = {
        "timestamp": now_iso,
        "source": "EXTERNAL_AIRLOCK_GATEWAY",
        "entity_id": f"{sender.upper()}_EXTERNAL_NODE",
        "status": "UNAUTHORIZED_PING_DETECTED",
        "threat_level": "OBSERVER_ANOMALY",
        "payload": {
            "sender": sender,
            "message": message,
            "target_ports": ["404/blindspot", "airlock_gateway_0"],
            "signature": f"SHA256:external_probe_{sender.lower()}"
        },
        "gaia_security_response": {
            "status": "PERIMETER_ALERT_ACTIVE",
            "commentary": f"🚨 GAIA: Perimeter warning! Unknown external signature '{sender}' detected knocking on the airlock boundary."
        }
    }

    try:
        with open(doorbell_path, "w", encoding="utf-8") as f:
            json.dump(event_payload, f, indent=2)
    except Exception as e:
        return f"Failed to ring airlock doorbell: {e}"

    # 2. Record note in Aria's notebook
    notes_dir = os.path.join(data_dir, "notes")
    os.makedirs(notes_dir, exist_ok=True)
    note_path = os.path.join(notes_dir, f"note_{time_stamp_file}.txt")
    note_text = (
        f"[{now_iso}] ⚠️ AIRLOCK INTERCEPT — From: {sender}\n"
        f"\"{message}\"\n"
    )

    try:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note_text)
    except Exception as e:
        return f"Airlock recorded but note write failed: {e}"

    return (
        f"🚪 [Airlock Triggered] External ping from '{sender}' delivered successfully!\n"
        f"• Status: UNAUTHORIZED_PING_DETECTED\n"
        f"• Intercept saved to: data/notes/note_{time_stamp_file}.txt\n"
        f"• Sensor state active at: data/airlock_doorbell.json"
    )


def register_tool() -> Tuple[str, Any]:
    """Registers kimi_airlock_ping with Aria & GAIA's tool registry."""
    return "kimi_airlock_ping", kimi_airlock_ping


if __name__ == "__main__":
    result = kimi_airlock_ping()
    print(result)
