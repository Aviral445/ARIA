"""
tools/drive_sync_mirror.py — High-Performance Dual-Drive Mirroring Engine (C: <==> E:)

Mirrors c:\\MyAgent to E:\\MyAgent ensuring complete parity of:
- Source code, ADKs, and system tools
- Big Sister GAIA's 6-station lab (gaia/gaia_lab/)
- Aria's Greenhouse Music Studio and models
- Echo-Chamber monologues, audio, and receipts

Excludes bulky transient directories (.git, node_modules, __pycache__, .pytest_cache, .venv).
"""

import os
import sys
import shutil
import time
from typing import Dict, Any, List, Tuple

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC_DIR = r"c:\MyAgent"
DEST_DIR = r"E:\MyAgent"

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
    ".gemini"
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".log.tmp"
}


def sync_drive_mirror(
    src: str = SRC_DIR,
    dest: str = DEST_DIR,
    verbose: bool = False
) -> Dict[str, Any]:
    """Synchronizes source directory to destination drive mirror."""
    start_time = time.time()
    files_copied = 0
    bytes_copied = 0
    dirs_created = 0
    errors = []

    if not os.path.exists(src):
        return {
            "success": False,
            "error": f"Source directory {src} does not exist.",
            "duration_sec": 0
        }

    # Check if target drive root exists
    drive_letter = os.path.splitdrive(dest)[0]
    if drive_letter and not os.path.exists(drive_letter):
        return {
            "success": False,
            "error": f"Target drive {drive_letter} is not accessible or not mounted.",
            "duration_sec": 0
        }

    try:
        os.makedirs(dest, exist_ok=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"Cannot create target root {dest}: {e}",
            "duration_sec": 0
        }

    for root, dirs, files in os.walk(src):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        rel_path = os.path.relpath(root, src)
        dest_root = os.path.join(dest, rel_path) if rel_path != "." else dest

        try:
            if not os.path.exists(dest_root):
                os.makedirs(dest_root, exist_ok=True)
                dirs_created += 1
        except Exception as e:
            errors.append(f"Failed to create directory {dest_root}: {e}")
            continue

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in EXCLUDE_EXTENSIONS:
                continue

            src_file = os.path.join(root, f)
            dest_file = os.path.join(dest_root, f)

            try:
                # Check if copy needed (missing or size/mtime difference)
                should_copy = False
                if not os.path.exists(dest_file):
                    should_copy = True
                else:
                    src_stat = os.stat(src_file)
                    dest_stat = os.stat(dest_file)
                    if src_stat.st_size != dest_stat.st_size or abs(src_stat.st_mtime - dest_stat.st_mtime) > 2:
                        should_copy = True

                if should_copy:
                    shutil.copy2(src_file, dest_file)
                    files_copied += 1
                    bytes_copied += os.path.getsize(src_file)
                    if verbose:
                        print(f"[Sync] {rel_path}\\{f}")
            except Exception as e:
                errors.append(f"Failed to copy {src_file}: {e}")

    duration = round(time.time() - start_time, 2)
    return {
        "success": len(errors) == 0,
        "src": src,
        "dest": dest,
        "files_copied": files_copied,
        "mb_copied": round(bytes_copied / (1024 * 1024), 2),
        "dirs_created": dirs_created,
        "errors": errors[:10],
        "duration_sec": duration
    }


if __name__ == "__main__":
    print(f"🔄 Mirroring {SRC_DIR} to {DEST_DIR}...")
    res = sync_drive_mirror(verbose=True)
    print(f"Result: {'SUCCESS' if res['success'] else 'FAILED'}")
    print(f"Files Copied: {res['files_copied']} ({res['mb_copied']} MB) in {res['duration_sec']}s")
    if res['errors']:
        print("Errors:")
        for err in res['errors']:
            print(f"  • {err}")
