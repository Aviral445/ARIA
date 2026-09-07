"""
tests/test_roadmap_features.py — Comprehensive Test Suite for All 10 Roadmap Features
Verifies:
1. Feature 1: Wake Word Detection ("Hey Aria")
2. Feature 4: Voice Cloning / Custom Voice Profile
3. Feature 31: System Tray Icon Manager
4. Feature 36: Voice Passphrase & PIN Security Guard (No Camera)
5. Feature 37: Encrypted Memory Vault (PBKDF2 + AES Fernet)
6. Feature 39: Notion Workspace & Task Integration
7. Feature 43: Streaming LLM Responses & Sentence-by-Sentence TTS
8. Feature 51: Human-in-the-Loop (HITL) Risk-Tiered Approval Gates
9. Feature 52: Enterprise SaaS Connectors (Slack, Jira & GitHub)
10. Feature 53: aisuite Multi-Provider Abstraction Layer
"""

import os
import sys
import json
import pytest

# Ensure repository root and core are on sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "system_tools"), os.path.join(_ROOT, "server"), os.path.join(_ROOT, "gui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
import core.paths

# ── 1. ENCRYPTED MEMORY VAULT TESTS ───────────────────────────────────────────
from core.aria_memory_crypto import (
    encrypt_bytes, decrypt_bytes, encrypt_file, decrypt_file,
    derive_fernet_key, encrypt_memory_vault, decrypt_memory_vault, is_vault_encrypted
)
from cryptography.fernet import InvalidToken


def test_encrypted_memory_vault_roundtrip(tmp_path):
    pwd = "SuperSecretPassword123!"
    secret_text = b"Aria's deepest personal reflections and memory tokens."

    # Encrypt bytes
    token = encrypt_bytes(secret_text, pwd)
    assert token != secret_text

    # Decrypt bytes
    decrypted = decrypt_bytes(token, pwd)
    assert decrypted == secret_text

    # Wrong password raises InvalidToken
    with pytest.raises(InvalidToken):
        decrypt_bytes(token, "WrongPassword!")

    # Test file encryption / decryption
    plain_file = tmp_path / "test_notes.json"
    plain_file.write_text('{"note": "doctor appointment Tuesday"}', encoding="utf-8")

    enc_file = encrypt_file(str(plain_file), pwd)
    assert os.path.exists(enc_file)

    dec_file = decrypt_file(enc_file, pwd, out_path=str(tmp_path / "restored.json"))
    with open(dec_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["note"] == "doctor appointment Tuesday"


# ── 2. VOICE PASSPHRASE & PIN SECURITY TESTS ──────────────────────────────────
from system_tools.aria_security import (
    verify_voice_or_pin_auth, is_session_authenticated,
    lock_session, aria_auth_check, set_security_credentials
)


def test_voice_and_pin_auth():
    # Set known test credentials
    set_security_credentials(new_pin="9876", new_phrase="aria open the vault")
    lock_session()
    assert not is_session_authenticated()

    # Wrong PIN fails
    ok, msg = verify_voice_or_pin_auth("0000")
    assert not ok
    assert not is_session_authenticated()

    # Correct PIN succeeds
    ok, msg = verify_voice_or_pin_auth("9876")
    assert ok
    assert is_session_authenticated()

    # Tool check shows authenticated
    status_msg = aria_auth_check()
    assert "AUTHENTICATED" in status_msg

    # Lock session
    lock_session()
    assert not is_session_authenticated()

    # Voice phrase succeeds
    ok, msg = verify_voice_or_pin_auth("aria open the vault")
    assert ok
    assert is_session_authenticated()


# ── 3. HUMAN-IN-THE-LOOP APPROVAL GATES TESTS ─────────────────────────────────
from core.aria_approval_gate import approval_gate, RiskTier


def test_approval_gate_risk_tiers():
    approval_gate.set_auto_approve(False)

    # Safe tool is low risk
    tier_safe = approval_gate.assess_risk("quick_math", {"expr": "2+2"})
    assert tier_safe == RiskTier.LOW
    ok, _, _ = approval_gate.check_approval("quick_math", {"expr": "2+2"})
    assert ok is True

    # Destructive argument elevates to critical risk
    tier_crit_arg = approval_gate.assess_risk("custom_file_op", {"action": "delete and format disk"})
    assert tier_crit_arg == RiskTier.CRITICAL
    ok, _, tier = approval_gate.check_approval("custom_file_op", {"action": "delete and format disk"})
    assert ok is False
    assert tier == RiskTier.CRITICAL

    # Test auto-approve override for headless/automated runs
    approval_gate.set_auto_approve(True)
    ok, msg, _ = approval_gate.check_approval("run_sandbox_code", {"code": "print('hello')"})
    assert ok is True
    assert "approved via auto-approve override" in msg
    approval_gate.set_auto_approve(False)


# ── 4. WAKE WORD DETECTOR TESTS ───────────────────────────────────────────────
from core.aria_wakeword import WakeWordDetector


def test_wake_word_detection():
    detector = WakeWordDetector(wake_words=["hey aria", "aria", "ok aria"])

    assert detector.contains_wake_word("Hey Aria, what time is it?") == "hey aria"
    assert detector.contains_wake_word("Aria tell me a joke") == "aria"
    assert detector.contains_wake_word("Good morning everyone!") is None

    # Test trigger event callback
    detected_phrases = []
    detector.add_callback(lambda phrase: detected_phrases.append(phrase))
    detector.trigger("hey aria")

    assert len(detected_phrases) == 1
    assert detected_phrases[0] == "hey aria"


# ── 5. VOICE CLONING / CUSTOM PROFILE TESTS ───────────────────────────────────
from core.aria_voice_clone import (
    list_voice_profiles, set_active_voice_profile, get_active_voice_profile,
    create_custom_voice_profile, aria_voice_profile_tool
)


def test_voice_cloning_profile_manager():
    profiles = list_voice_profiles()
    assert "Aria (Default)" in profiles
    assert "Aria (Expressive Neural)" in profiles

    # Switch active profile
    ok, msg = set_active_voice_profile("Expressive")
    assert ok is True
    active = get_active_voice_profile()
    assert "Expressive" in active["name"]

    # Create new custom profile
    res = create_custom_voice_profile("TestUserClonedVoice", rate=1.1, pitch=2)
    assert res["success"] is True
    assert res["name"] == "TestUserClonedVoice"

    # Tool execution
    tool_output = aria_voice_profile_tool(action="list")
    assert "Active Voice Profile:" in tool_output


try:
    from gui.aria_system_tray import AriaSystemTray
except (ImportError, ModuleNotFoundError):
    from aria_system_tray import AriaSystemTray


def test_system_tray_manager():
    restore_called = []
    quit_called = []

    tray = AriaSystemTray(
        app_name="Aria Test Tray",
        on_restore=lambda: restore_called.append(True),
        on_quit=lambda: quit_called.append(True)
    )

    tray.minimize()
    assert tray.is_minimized_to_tray is True

    tray.restore()
    assert tray.is_minimized_to_tray is False
    assert len(restore_called) == 1

    tray.stop()


# ── 7. NOTION INTEGRATION TESTS ───────────────────────────────────────────────
from system_tools.aria_notion import create_notion_task, list_notion_tasks, notion_tool


def test_notion_connector():
    # Test creation in demo/offline preview mode
    res = create_notion_task("Buy matcha green tea", status="To Do")
    assert "Buy matcha green tea" in res

    # Tool status check
    status_str = notion_tool(action="status")
    assert "Notion Integration Status:" in status_str


# ── 8. ENTERPRISE SAAS CONNECTORS TESTS ───────────────────────────────────────
from system_tools.aria_enterprise import send_slack_message, create_jira_issue, enterprise_saas_tool


def test_enterprise_saas_connectors():
    # Slack demo test
    slack_res = send_slack_message("Release v2.0 deployed successfully", channel="#general")
    assert "Release v2.0 deployed" in slack_res

    # Jira demo test
    jira_res = create_jira_issue("Fix audio buffer underflow", description="Edge-TTS sentence latency", project_key="ARIA")
    assert "Fix audio buffer underflow" in jira_res

    # Unified tool routing
    tool_slack = enterprise_saas_tool(platform="slack", text="Team standup at 10 AM")
    assert "Team standup at 10 AM" in tool_slack

    tool_jira = enterprise_saas_tool(platform="jira", summary="Add OAuth2 token refresh")
    assert "Add OAuth2 token refresh" in tool_jira


# ── 9. STREAMING & SENTENCE-BY-SENTENCE TTS TESTS ─────────────────────────────
from core.aria_streaming import SentenceStreamer, clean_sentence_for_speech, stream_generator_sentences


def test_streaming_sentence_streamer():
    clean = clean_sentence_for_speech("### Hello **World**! Visit https://google.com for `code`.")
    assert clean == "Hello World! Visit for ."

    emitted_sentences = []
    streamer = SentenceStreamer(on_sentence_ready=lambda s: emitted_sentences.append(s))

    tokens = ["Hello, ", "friend! ", "How ", "are you doing ", "today? ", "I am so excited to see you."]
    for tok in tokens:
        streamer.feed_token(tok)

    # Finalize should capture any remaining unpunctuated sentence
    streamer.finalize()

    assert len(emitted_sentences) >= 2
    assert any("friend" in s for s in emitted_sentences)
    assert any("today" in s for s in emitted_sentences)


# ── 10. AISUITE MULTI-PROVIDER ABSTRACTION TESTS ──────────────────────────────
from core.aria_aisuite import Client as AiSuiteClient


def test_aisuite_multi_provider_abstraction():
    client = AiSuiteClient(auto_fallback=True)

    # Test client instantiation and standard model routing syntax
    resp = client.chat.completions.create(
        model="mock:test-model",
        messages=[{"role": "user", "content": "Ping"}]
    )

    assert resp.choices[0].message.role == "assistant"
    assert "Ping" in resp.choices[0].message.content
    assert resp.provider == "mock"
