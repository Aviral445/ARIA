"""
core/aria_memory_crypto.py — Encrypted Memory & Vault Protection (Feature 37)
Uses PBKDF2HMAC + AES-128/256 Fernet to encrypt sensitive memories, timeline cards,
and profile configurations with user-provided passphrases.
"""

import os
import sys
import json
import base64
from typing import Optional, Tuple, Dict, Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.paths import DATA_DIR, get_data_file

# Dedicated vault encryption metadata path
SALT_FILE = os.path.join(DATA_DIR, ".vault_salt")
VAULT_META_FILE = os.path.join(DATA_DIR, ".vault_meta.json")


def _get_or_create_salt() -> bytes:
    """Retrieves or persists a 16-byte random salt for PBKDF2 key derivation."""
    if os.path.exists(SALT_FILE):
        try:
            with open(SALT_FILE, "rb") as f:
                salt = f.read()
                if len(salt) >= 16:
                    return salt[:16]
        except Exception:
            pass

    salt = os.urandom(16)
    try:
        os.makedirs(os.path.dirname(SALT_FILE), exist_ok=True)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
    except Exception:
        pass
    return salt


def derive_fernet_key(password: str, salt: Optional[bytes] = None) -> bytes:
    """Derives a deterministic URL-safe base64 32-byte key using PBKDF2HMAC SHA-256."""
    if not password:
        raise ValueError("Password cannot be empty for encryption key derivation.")

    resolved_salt = salt if salt is not None else _get_or_create_salt()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=resolved_salt,
        iterations=100_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key


def encrypt_bytes(data: bytes, password: str, salt: Optional[bytes] = None) -> bytes:
    """Encrypts raw bytes using Fernet derived from the given password."""
    key = derive_fernet_key(password, salt=salt)
    cipher = Fernet(key)
    return cipher.encrypt(data)


def decrypt_bytes(token: bytes, password: str, salt: Optional[bytes] = None) -> bytes:
    """Decrypts Fernet ciphertext bytes. Raises InvalidToken on incorrect password."""
    key = derive_fernet_key(password, salt=salt)
    cipher = Fernet(key)
    return cipher.decrypt(token)


def encrypt_file(filepath: str, password: str, out_path: Optional[str] = None) -> str:
    """Encrypts a file on disk in-place or to an out_path."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Target file not found: {filepath}")

    with open(filepath, "rb") as f:
        raw_data = f.read()

    encrypted_data = encrypt_bytes(raw_data, password)
    destination = out_path or (filepath + ".enc")
    with open(destination, "wb") as f:
        f.write(encrypted_data)
    return destination


def decrypt_file(enc_path: str, password: str, out_path: Optional[str] = None) -> str:
    """Decrypts a .enc file on disk. Returns the restored file path."""
    if not os.path.exists(enc_path):
        raise FileNotFoundError(f"Target file not found: {enc_path}")

    with open(enc_path, "rb") as f:
        token = f.read()

    decrypted_data = decrypt_bytes(token, password)
    if out_path:
        dest = out_path
    elif enc_path.endswith(".enc"):
        dest = enc_path[:-4]
    else:
        dest = enc_path + ".dec"

    with open(dest, "wb") as f:
        f.write(decrypted_data)
    return dest


def is_vault_encrypted() -> bool:
    """Checks whether the Aria memory vault is currently marked as encrypted."""
    if os.path.exists(VAULT_META_FILE):
        try:
            with open(VAULT_META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
                return meta.get("encrypted", False)
        except Exception:
            pass
    return False


def encrypt_memory_vault(password: str) -> Dict[str, Any]:
    """
    Encrypts sensitive memory and profile JSON files in data/aria_memory/ and data/
    using password-derived AES Fernet cipher.
    """
    targets = [
        get_data_file("profile.json"),
        get_data_file("goals.json"),
        get_data_file("reminders.json"),
        os.path.join(DATA_DIR, "aria_memory", "memory_timeline.json"),
        os.path.join(DATA_DIR, "aria_memory", "memory_cards.json")
    ]

    encrypted_files = []
    for t in targets:
        if os.path.exists(t):
            try:
                enc_dest = encrypt_file(t, password, out_path=t + ".enc")
                # Remove plaintext version
                os.remove(t)
                encrypted_files.append(t)
            except Exception as e:
                return {"success": False, "error": f"Failed encrypting {t}: {e}"}

    meta = {
        "encrypted": True,
        "files_count": len(encrypted_files),
        "files": encrypted_files
    }
    with open(VAULT_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {"success": True, "encrypted_files": encrypted_files}


def decrypt_memory_vault(password: str) -> Dict[str, Any]:
    """
    Decrypts the Aria memory vault and restores plaintext access for the session.
    """
    if not is_vault_encrypted():
        return {"success": True, "message": "Vault was not encrypted."}

    with open(VAULT_META_FILE, "r", encoding="utf-8") as f:
        meta = json.load(f)

    restored_files = []
    for original_path in meta.get("files", []):
        enc_path = original_path + ".enc"
        if os.path.exists(enc_path):
            try:
                decrypt_file(enc_path, password, out_path=original_path)
                os.remove(enc_path)
                restored_files.append(original_path)
            except InvalidToken:
                return {"success": False, "error": "Invalid decryption password. Access denied."}
            except Exception as e:
                return {"success": False, "error": f"Failed decrypting {enc_path}: {e}"}

    with open(VAULT_META_FILE, "w", encoding="utf-8") as f:
        json.dump({"encrypted": False, "files_count": 0, "files": []}, f, indent=2)

    return {"success": True, "restored_files": restored_files}
