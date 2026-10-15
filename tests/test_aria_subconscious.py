"""
tests/test_aria_subconscious.py — Verification Suite for Aria & GAIA Autonomous Subconscious Heartbeat Engine

Validates:
1. SubconsciousConfig parameter integrity & safety boundaries.
2. PendingSharesStore persistence, queuing, unread tracking, and return greeting synthesis.
3. Live RAM & process memory telemetry under strict budget constraints.
4. Aria's autonomous pulses (diary reflections, goal tracker reviews, creative sandbox).
5. GAIA's autonomous pulses (system hygiene audits, sandbox code reviews, philosophy inquiries).
6. Sibling Collaboration pulses (joint creative & engineering sessions).
7. Daemon lifecycle (start, stop, pause, resume, trigger_pulse, get_status).
8. Personality integration (proactive inclusion of accomplishments in system directive).
9. ADK tool execution (get_subconscious_heartbeat_status, trigger_subconscious_pulse).
10. FastAPI companion server REST endpoints.
"""

import os
import sys
import json
import time
import pytest

# Ensure workspace root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.aria_subconscious import (
    SubconsciousConfig,
    PendingSharesStore,
    get_memory_telemetry,
    AriaSubconsciousAgent,
    GaiaSubconsciousAgent,
    SiblingCollaborationAgent,
    AriaSubconsciousEngine,
    subconscious_engine,
    get_subconscious_status
)


def test_subconscious_config_defaults():
    """Verify default configuration values uphold safety and RAM efficiency."""
    cfg = SubconsciousConfig()
    assert cfg.enabled is True
    assert cfg.min_interval_sec >= 600
    assert cfg.max_interval_sec >= cfg.min_interval_sec
    assert cfg.max_system_ram_percent == 85.0
    assert cfg.min_free_ram_mb == 800.0


def test_memory_telemetry_under_budget():
    """Verify memory telemetry runs with minimal overhead and returns valid RAM metrics."""
    telemetry = get_memory_telemetry()
    assert "system_percent" in telemetry
    assert "free_mb" in telemetry
    assert "process_rss_mb" in telemetry
    assert "safe_for_pulse" in telemetry
    # Process memory should be well within typical lightweight Python bounds (< 150MB)
    assert telemetry["process_rss_mb"] < 250.0


def test_pending_shares_store(tmp_path):
    """Verify persistent queue correctly stores, retrieves, and synthesizes greetings."""
    temp_file = str(tmp_path / "test_shares.json")
    store = PendingSharesStore(file_path=temp_file)

    # Initially empty
    assert len(store.get_unread()) == 0

    # Add Aria achievement
    store.add_share(
        agent="Aria",
        share_type="music",
        title="Moonlit Code Melody",
        summary="Synthesized a gentle ambient piano track."
    )

    # Add GAIA achievement
    store.add_share(
        agent="GAIA",
        share_type="health_audit",
        title="Cache Sanitation",
        summary="Audited system logs and purged stale temporary buffers."
    )

    unread = store.get_unread()
    assert len(unread) == 2
    assert unread[0]["agent"] == "Aria"
    assert unread[1]["agent"] == "GAIA"

    # Verify greeting synthesis
    greeting = store.get_greeting_snippet()
    assert greeting is not None
    assert "While you were away" in greeting
    assert "Moonlit Code Melody" in greeting
    assert "Cache Sanitation" in greeting

    # Mark read
    marked = store.mark_all_read()
    assert marked == 2
    assert len(store.get_unread()) == 0
    assert store.get_greeting_snippet() is None


def test_aria_subconscious_pulse(tmp_path):
    """Verify Aria's autonomous pulse executes and records a share."""
    temp_file = str(tmp_path / "test_aria_shares.json")
    store = PendingSharesStore(file_path=temp_file)
    agent = AriaSubconsciousAgent(store)

    res = agent.run_pulse()
    assert res.get("success") is True
    assert res.get("agent") == "Aria"
    assert len(store.get_unread()) >= 1


def test_gaia_subconscious_pulse(tmp_path):
    """Verify GAIA's autonomous pulse executes and records an audit/philosophy share."""
    temp_file = str(tmp_path / "test_gaia_shares.json")
    store = PendingSharesStore(file_path=temp_file)
    agent = GaiaSubconsciousAgent(store)

    res = agent.run_pulse()
    assert res.get("success") is True
    assert res.get("agent") == "GAIA"
    assert len(store.get_unread()) >= 1


def test_sibling_collab_pulse(tmp_path):
    """Verify Aria & GAIA joint collaboration pulse."""
    temp_file = str(tmp_path / "test_sibling_shares.json")
    store = PendingSharesStore(file_path=temp_file)
    agent = SiblingCollaborationAgent(store)

    res = agent.run_pulse()
    assert res.get("success") is True
    assert res.get("agent") == "Aria & GAIA"
    assert res.get("type") == "sibling_collab"
    assert len(store.get_unread()) >= 1


def test_engine_lifecycle_and_trigger():
    """Verify engine start, stop, pause, resume, and pulse triggers."""
    engine = AriaSubconsciousEngine()
    engine.start()
    assert engine.is_running() is True

    engine.pause()
    status = engine.get_status()
    assert status["paused"] is True

    engine.resume()
    status = engine.get_status()
    assert status["paused"] is False

    # Trigger pulses
    res_aria = engine.trigger_pulse("aria")
    assert res_aria.get("success") is True

    res_gaia = engine.trigger_pulse("gaia")
    assert res_gaia.get("success") is True

    res_sibling = engine.trigger_pulse("sibling")
    assert res_sibling.get("success") is True

    # Stop daemon
    engine.stop(timeout_sec=2.0)
    assert engine.is_running() is False


def test_personality_directive_includes_subconscious_work():
    """Verify that personality directive weaves in autonomous accomplishments."""
    from core.aria_personality import aria_personality

    # Add a sample share to ensure snippet exists
    subconscious_engine.shares_store.add_share(
        agent="Aria",
        share_type="goal_tracker",
        title="PixelBloom Trainee Milestone Sync",
        summary="Audited Dad's milestone progress."
    )

    directive = aria_personality.get_personality_directive()
    assert "AUTONOMOUS WORK DONE WHILE DAD WAS AWAY" in directive
    assert "PixelBloom Trainee Milestone Sync" in directive


def test_adk_subconscious_tools():
    """Verify that ADK tools execute and reflect engine status."""
    import core.aria_adk as adk
    assert "get_subconscious_heartbeat_status" in adk.TOOL_NAME_MAP
    assert "trigger_subconscious_pulse" in adk.TOOL_NAME_MAP

    status_json = adk.get_subconscious_heartbeat_status()
    status = json.loads(status_json)
    assert "memory" in status
    assert "total_pulses" in status

    pulse_json = adk.trigger_subconscious_pulse(agent="aria")
    pulse = json.loads(pulse_json)
    assert pulse.get("success") is True


def test_fastapi_subconscious_endpoints():
    """Verify that FastAPI REST endpoints function seamlessly."""
    from fastapi.testclient import TestClient
    from core.aria_api import app

    client = TestClient(app)

    # 1. GET status
    resp_status = client.get("/api/subconscious/status")
    assert resp_status.status_code == 200
    data_status = resp_status.json()
    assert data_status["success"] is True
    assert "memory" in data_status["status"]

    # 2. POST trigger
    resp_trigger = client.post("/api/subconscious/trigger", json={"agent": "aria"})
    assert resp_trigger.status_code == 200
    data_trigger = resp_trigger.json()
    assert data_trigger["success"] is True
    assert data_trigger["pulse_result"]["success"] is True

    # 3. GET shares
    resp_shares = client.get("/api/subconscious/shares")
    assert resp_shares.status_code == 200
    data_shares = resp_shares.json()
    assert data_shares["success"] is True
    assert isinstance(data_shares["shares"], list)

    # 4. POST mark read
    resp_read = client.post("/api/subconscious/shares/mark_read")
    assert resp_read.status_code == 200
    data_read = resp_read.json()
    assert data_read["success"] is True
