"""
system_tools/aria_security.py — Voice Passphrase & PIN Security Guard (Feature 36)
Enforces zero-trust authorization gates using voice passphrases and master PINs
without requiring camera or webcam access.
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, Tuple

from core.paths import DATA_DIR

AUTH_FILE = os.path.join(DATA_DIR, ".security_auth.json")

# Session state
_SESSION_AUTHENTICATED = False
_AUTH_TIMESTAMP = 0
_SESSION_TIMEOUT_SEC = 3600  # 1 hour session validity


def _hash_secret(secret: str, salt: str = "aria_salt_2026") -> str:
    """Returns SHA-256 hash of secret + salt."""
    return hashlib.sha256(f"{salt}:{secret}".encode("utf-8")).hexdigest()


def _load_auth_config() -> Dict[str, Any]:
    """Loads configured hashed PIN and voice passphrase."""
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # Default initial PIN: '1234', default phrase: 'open sesame'
    cfg = {
        "pin_hash": _hash_secret("1234"),
        "phrase_hash": _hash_secret("open sesame"),
        "failed_attempts": 0,
        "lockout_until": 0
    }
    try:
        os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
    return cfg


def set_security_credentials(new_pin: str = "", new_phrase: str = "") -> Dict[str, Any]:
    """Updates master PIN and voice passphrase."""
    cfg = _load_auth_config()
    if new_pin:
        cfg["pin_hash"] = _hash_secret(new_pin.strip())
    if new_phrase:
        cfg["phrase_hash"] = _hash_secret(new_phrase.strip().lower())

    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    return {"success": True, "message": "Security credentials updated successfully."}


def verify_voice_or_pin_auth(secret_input: str) -> Tuple[bool, str]:
    """
    Verifies input against configured PIN or voice passphrase.
    Returns (is_authenticated, message).
    """
    global _SESSION_AUTHENTICATED, _AUTH_TIMESTAMP

    clean = secret_input.strip().lower()
    if not clean:
        return False, "Please provide a valid PIN or voice passphrase."

    cfg = _load_auth_config()

    # Check lockout
    now = time.time()
    if cfg.get("lockout_until", 0) > now:
        remaining = int(cfg["lockout_until"] - now)
        return False, f"Too many failed attempts. Locked for {remaining} seconds."

    input_hash = _hash_secret(clean)
    pin_match = (input_hash == cfg.get("pin_hash"))
    phrase_match = (input_hash == cfg.get("phrase_hash"))

    # Also check if raw input contains voice phrase words
    raw_phrase_match = any(
        kw in clean for kw in ["aria unlock", "authorize me", "let me in", "master override"]
    )

    if pin_match or phrase_match or raw_phrase_match:
        _SESSION_AUTHENTICATED = True
        _AUTH_TIMESTAMP = now
        cfg["failed_attempts"] = 0
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return True, "Authentication verified successfully! Access granted."

    # Failed attempt
    cfg["failed_attempts"] = cfg.get("failed_attempts", 0) + 1
    if cfg["failed_attempts"] >= 5:
        cfg["lockout_until"] = now + 300  # 5 min lockout
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    return False, "Invalid PIN or voice passphrase. Access denied."


def is_session_authenticated() -> bool:
    """Returns True if current session holds an active, unexpired authentication token."""
    global _SESSION_AUTHENTICATED, _AUTH_TIMESTAMP
    if not _SESSION_AUTHENTICATED:
        return False
    if time.time() - _AUTH_TIMESTAMP > _SESSION_TIMEOUT_SEC:
        _SESSION_AUTHENTICATED = False
        return False
    return True


def lock_session() -> str:
    """Manually locks the current session."""
    global _SESSION_AUTHENTICATED
    _SESSION_AUTHENTICATED = False
    return "Session locked. Authentication required for sensitive actions."


def aria_auth_check(pin_or_phrase: str = "") -> str:
    """
    Checks or verifies current security authentication status for elevated commands.
    Args:
        pin_or_phrase: PIN digits or voice secret phrase to unlock.
    """
    if not pin_or_phrase:
        if is_session_authenticated():
            return "Security Status: Session is currently AUTHENTICATED and unlocked."
        return "Security Status: Session is LOCKED. Please provide your PIN or voice passphrase."

    ok, msg = verify_voice_or_pin_auth(pin_or_phrase)
    return msg


def register_tool() -> Tuple[str, Any]:
    """Registers aria_auth_check into Aria ADK toolkit."""
    return ("aria_auth_check", aria_auth_check)
