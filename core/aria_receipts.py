"""
core/aria_receipts.py — Tamper-Evident SHA-256 Hash-Chained Audit Ledger
Enforces the Repudiation invariant in the STRIDE security matrix by hash-chaining
every receipt entry Git-commit style. Walking the chain verifies integrity from genesis to tip.
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

GENESIS_HASH = "0" * 64


def _normalize_for_hashing(payload: str) -> str:
    """Normalizes string payload for consistent SHA-256 computation."""
    return payload.strip().encode("utf-8")


def compute_payload_hash(payload: str) -> str:
    """Computes SHA-256 hex digest for a receipt line payload."""
    return hashlib.sha256(_normalize_for_hashing(payload)).hexdigest()


def append_chained_receipt(
    receipt_file_path: str,
    action: str,
    author: str,
    details: str = ""
) -> Dict[str, Any]:
    """
    Appends a new cryptographically chained receipt entry to receipt_file_path.
    Each entry includes [HASH: <entry_hash>] and [PREV: <prev_line_hash>].
    """
    os.makedirs(os.path.dirname(os.path.abspath(receipt_file_path)), exist_ok=True)

    prev_hash = GENESIS_HASH
    existing_lines = []

    if os.path.exists(receipt_file_path):
        try:
            with open(receipt_file_path, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
            if existing_lines:
                last_line = existing_lines[-1]
                # Extract the hash of the last line directly
                prev_hash = compute_payload_hash(last_line)
        except Exception as e:
            print(f"[Receipts Ledger] Read notice: {e}")

    now_iso = datetime.now().isoformat()
    # Construct base payload without the HASH header
    payload = f"[PREV: {prev_hash}] [{now_iso}] [AUTHOR: {author}] [{action}] {details}".strip()
    entry_hash = compute_payload_hash(payload)
    full_entry = f"[HASH: {entry_hash}] {payload}\n"

    with open(receipt_file_path, "a", encoding="utf-8") as f:
        f.write(full_entry)

    return {
        "success": True,
        "entry_hash": entry_hash,
        "prev_hash": prev_hash,
        "entry": full_entry.strip(),
        "timestamp": now_iso
    }


def verify_receipt_chain(receipt_file_path: str) -> Dict[str, Any]:
    """
    Walks a receipts.log from genesis to tip, verifying every cryptographic link.
    Detects any modified, inserted, or omitted lines immediately.
    """
    if not os.path.exists(receipt_file_path):
        return {"valid": True, "entries_count": 0, "errors": [], "message": "Empty/no ledger"}

    try:
        with open(receipt_file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        return {"valid": False, "entries_count": 0, "errors": [f"Cannot read receipt file: {e}"]}

    if not lines:
        return {"valid": True, "entries_count": 0, "errors": [], "message": "Empty ledger"}

    errors = []
    prev_expected_hash = GENESIS_HASH

    for idx, line in enumerate(lines):
        # Extract [HASH: <hash>] [PREV: <prev_hash>] ...
        m_hash = re.match(r'^\[HASH:\s*([a-f0-9]{64})\]\s*(.*)$', line)
        if not m_hash:
            errors.append(f"Line {idx + 1}: Malformed receipt format (missing or invalid [HASH: ...]).")
            continue

        entry_hash = m_hash.group(1)
        payload = m_hash.group(2)

        # 1. Verify internal payload hash integrity
        calculated_hash = compute_payload_hash(payload)
        if entry_hash != calculated_hash:
            errors.append(f"Line {idx + 1}: Tamper detected! Recorded HASH '{entry_hash}' != Computed '{calculated_hash}'.")

        # 2. Extract recorded PREV hash
        m_prev = re.search(r'\[PREV:\s*([a-f0-9]{64})\]', payload)
        if not m_prev:
            errors.append(f"Line {idx + 1}: Missing [PREV: ...] hash header.")
        else:
            recorded_prev = m_prev.group(1)
            if idx == 0:
                # Genesis line must point to GENESIS_HASH
                if recorded_prev != GENESIS_HASH:
                    errors.append(f"Line 1 (Genesis): Invalid prev hash '{recorded_prev}' (expected GENESIS).")
            else:
                # Subsequent lines must point to the SHA-256 of the prior full line
                if recorded_prev != prev_expected_hash:
                    errors.append(f"Line {idx + 1}: Chain broken! PREV '{recorded_prev}' != Expected '{prev_expected_hash}'.")

        # Update expected hash for next line
        prev_expected_hash = compute_payload_hash(line)

    return {
        "valid": (len(errors) == 0),
        "entries_count": len(lines),
        "errors": errors,
        "message": "Ledger intact and cryptographically verified" if not errors else f"Ledger compromised: {len(errors)} error(s)"
    }
