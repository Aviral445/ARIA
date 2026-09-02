"""
gaia/gaia_diff.py — Automated Diff & Evolution Tracking Engine
Tracks all self-modifications made by Aria on E:\\MyAgent\\aria_evolved.py compared
to the clean baseline in C:\\MyAgent\\agent.py.
"""

import os
import sys
import time
import shutil
import difflib
from typing import Dict, Any, Tuple

# Paths
from core.paths import ROOT_DIR, ARIA_BASELINE_FILE, ARIA_EVOLVED_DIR, ARIA_EVOLVED_FILE

DIFFS_DIR = os.path.join(ARIA_EVOLVED_DIR, "diffs")
CHANGELOG_E_PATH = os.path.join(ARIA_EVOLVED_DIR, "ARIA_CHANGELOG.md")
CHANGELOG_C_PATH = os.path.join(ROOT_DIR, "gaia", "ARIA_CHANGELOG.md")

os.makedirs(DIFFS_DIR, exist_ok=True)


def ensure_evolved_file_exists() -> str:
    """Ensures E:\\MyAgent\\aria_evolved.py exists as a clone of C:\\MyAgent\\agent.py."""
    if not os.path.exists(ARIA_EVOLVED_FILE):
        if os.path.exists(ARIA_BASELINE_FILE):
            os.makedirs(ARIA_EVOLVED_DIR, exist_ok=True)
            shutil.copy2(ARIA_BASELINE_FILE, ARIA_EVOLVED_FILE)
    return ARIA_EVOLVED_FILE


def compute_diff(baseline_path: str = ARIA_BASELINE_FILE, evolved_path: str = ARIA_EVOLVED_FILE) -> Dict[str, Any]:
    """
    Computes a clean line-by-line diff between baseline (C:) and Aria's evolved copy (E:).
    Returns stats and unified diff string.
    """
    ensure_evolved_file_exists()

    if not os.path.exists(baseline_path) or not os.path.exists(evolved_path):
        return {
            "has_changes": False,
            "additions": 0,
            "deletions": 0,
            "diff_text": "Error: One of the comparison files does not exist.",
            "summary": "Missing comparison files."
        }

    with open(baseline_path, "r", encoding="utf-8", errors="replace") as f:
        base_lines = f.readlines()
    with open(evolved_path, "r", encoding="utf-8", errors="replace") as f:
        evolved_lines = f.readlines()

    diff_generator = difflib.unified_diff(
        base_lines,
        evolved_lines,
        fromfile="C:\\MyAgent\\agent.py (Baseline)",
        tofile="E:\\MyAgent\\aria_evolved.py (Aria)",
        lineterm=""
    )

    diff_lines = list(diff_generator)
    if not diff_lines:
        return {
            "has_changes": False,
            "additions": 0,
            "deletions": 0,
            "diff_text": "No differences found. E:\\MyAgent\\aria_evolved.py is in sync with C:\\MyAgent\\agent.py.",
            "summary": "E: drive is currently identical to C: drive baseline."
        }

    additions = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    diff_text = "\n".join(diff_lines)
    summary = f"+{additions} lines added, -{deletions} lines removed by Aria on E: drive."

    return {
        "has_changes": True,
        "additions": additions,
        "deletions": deletions,
        "diff_text": diff_text,
        "summary": summary
    }


def record_evolution_changelog(goal: str, aria_explanation: str, gaia_verdict: str) -> Dict[str, Any]:
    """
    Records a permanent changelog entry in ARIA_CHANGELOG.md and saves a .diff file.
    """
    diff_info = compute_diff()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    file_ts = time.strftime("%Y%m%d_%H%M%S")

    # 1. Save timestamped .diff file in E:\MyAgent\diffs
    diff_file_path = os.path.join(DIFFS_DIR, f"diff_{file_ts}.diff")
    try:
        with open(diff_file_path, "w", encoding="utf-8") as f:
            f.write(diff_info["diff_text"])
    except Exception:
        pass

    # 2. Build Markdown Changelog Entry
    entry = f"""
## 🌿 Aria Evolution Entry — {ts}
- **Aria's Goal:** {goal}
- **Aria's Commentary:** {aria_explanation}
- **GAIA Supervision Verdict:** {gaia_verdict}
- **Diff Stats:** `{diff_info['summary']}`
- **Snapshot Diff File:** `{os.path.basename(diff_file_path)}`

```diff
{diff_info['diff_text'][:2500]}
{"... (truncated diff for readability)" if len(diff_info['diff_text']) > 2500 else ""}
```

---
"""

    # Append to E:\MyAgent\ARIA_CHANGELOG.md
    for target_path in [CHANGELOG_E_PATH, CHANGELOG_C_PATH]:
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            existing = ""
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8") as f:
                    existing = f.read()
            else:
                existing = "# 🧬 ARIA SELF-EVOLUTION CHANGELOG\n*Tracking all autonomous edits made by Aria in E:\\MyAgent compared to C:\\MyAgent baseline.*\n\n---\n"
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(existing + entry)
        except Exception:
            pass

    return {
        "timestamp": ts,
        "summary": diff_info["summary"],
        "diff_file": diff_file_path
    }


def promote_to_production() -> Tuple[bool, str]:
    r"""
    Promotes Aria's evolved code in E:\MyAgent\aria_evolved.py to C:\MyAgent\agent.py.
    Creates a backup of C:\MyAgent\agent.py first.
    """
    if not os.path.exists(ARIA_EVOLVED_FILE):
        return False, f"Evolved file {ARIA_EVOLVED_FILE} does not exist."

    # Backup C:\MyAgent\agent.py
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(ROOT_DIR, f"agent.py.bak_{ts}")
    try:
        shutil.copy2(ARIA_BASELINE_FILE, backup_path)
        shutil.copy2(ARIA_EVOLVED_FILE, ARIA_BASELINE_FILE)
        return True, f"Successfully merged Aria's code into C:\\MyAgent\\agent.py! (Backup saved to agent.py.bak_{ts})"
    except Exception as e:
        return False, f"Failed to promote evolved code: {e}"


def reset_to_baseline() -> Tuple[bool, str]:
    r"""
    Resets E:\MyAgent\aria_evolved.py to match C:\MyAgent\agent.py baseline.
    """
    if not os.path.exists(ARIA_BASELINE_FILE):
        return False, f"Baseline file {ARIA_BASELINE_FILE} does not exist."

    try:
        shutil.copy2(ARIA_BASELINE_FILE, ARIA_EVOLVED_FILE)
        return True, "Reset E:\\MyAgent\\aria_evolved.py to match pristine C:\\MyAgent\\agent.py baseline."
    except Exception as e:
        return False, f"Failed to reset evolved file: {e}"
