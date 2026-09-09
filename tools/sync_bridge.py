"""
tools/sync_bridge.py — The Mirror Bridge & Production Promotion Pipeline

Connects C:\\MyAgent (Golden Production Anchor) and E:\\MyAgent (Evolution Playground).
Features:
- push: Auto-syncs baseline improvements from C: -> E: (safely protecting Aria's lab files).
- status / diff: Shows all files created or modified by Aria on E:, plus recent changelog receipts.
- review <file>: Runs GAIA's 4-Pillar Code Reviewer & Chaos Stress-Tester on E: candidate files.
- promote <file>: Runs GAIA review first. If approved (score >= 8.5, 0 criticals), safely promotes file to C:.
- reset <file>: Restores an E: file from the golden C: anchor.
- watch: Real-time background observer that hot-mirrors C: changes into E: continuously.
"""

import os
import sys
import time
import shutil
import filecmp
from datetime import datetime
from typing import List, Dict, Tuple

# Windows UTF-8 stdout reconfiguration
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

C_PATH = r"C:\MyAgent"
E_PATH = r"E:\MyAgent"

# Directories and files protected on E: from being overwritten by C:
PROTECTED_ON_E = {
    "ARIA_CHANGELOG.md",
    "aria_changelog.md",
    "watchdog_core.py",
    "core/watchdog_core.py",
    "core\\watchdog_core.py",
    "gaia_architect",
    "snapshots",
    "inner_mind",
    "data/inner_mind",
    "data\\inner_mind"
}

# Directories to always ignore during sync
GLOBAL_IGNORES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    ".tempmediaStorage",
    ".system_generated",
    "snapshots",
    "gaia_architect",
    "diffs",
    "incidents",
    "sandbox_notes",
    "scratch",
    "platform-tools"
}


def get_gaia_reviewer():
    """Dynamically loads GaiaReviewer."""
    try:
        from gaia.gaia_reviewer import GaiaReviewer
        return GaiaReviewer()
    except Exception:
        sys.path.insert(0, C_PATH)
        from gaia.gaia_reviewer import GaiaReviewer
        return GaiaReviewer()


def normalize_rel_path(path: str, base_dir: str) -> str:
    """Gets normalized relative path."""
    return os.path.relpath(path, base_dir).replace("\\", "/")


def is_protected(rel_path: str) -> bool:
    """Checks if relative path is protected on E:."""
    rel_norm = rel_path.replace("\\", "/")
    for p in PROTECTED_ON_E:
        p_norm = p.replace("\\", "/")
        if rel_norm == p_norm or rel_norm.startswith(p_norm + "/"):
            return True
    return False


def is_ignored(rel_path: str) -> bool:
    """Checks if path should be completely ignored."""
    parts = rel_path.replace("\\", "/").split("/")
    return any(p in GLOBAL_IGNORES for p in parts)


# ── COMMAND 1: STATUS & DIFF ─────────────────────────────────────────────────
def cmd_status():
    """Scans E: against C: and lists all created, modified, and pending files."""
    print("=" * 65)
    print("🔍 ARIA & GAIA EVOLUTION PLAYGROUND STATUS (E:\\MyAgent vs C:\\MyAgent)")
    print("=" * 65)

    if not os.path.exists(E_PATH):
        print(f"❌ Error: Playground drive '{E_PATH}' is not mounted or accessible.")
        return

    e_files = {}
    for root, dirs, files in os.walk(E_PATH):
        dirs[:] = [d for d in dirs if d not in GLOBAL_IGNORES]
        for f in files:
            full = os.path.join(root, f)
            rel = normalize_rel_path(full, E_PATH)
            if not is_ignored(rel):
                e_files[rel] = full

    c_files = {}
    for root, dirs, files in os.walk(C_PATH):
        dirs[:] = [d for d in dirs if d not in GLOBAL_IGNORES]
        for f in files:
            full = os.path.join(root, f)
            rel = normalize_rel_path(full, C_PATH)
            if not is_ignored(rel):
                c_files[rel] = full

    new_on_e = []
    modified_on_e = []

    for rel, e_full in e_files.items():
        if rel not in c_files:
            new_on_e.append(rel)
        else:
            c_full = c_files[rel]
            try:
                if not filecmp.cmp(e_full, c_full, shallow=False):
                    # Check which is newer
                    if os.path.getmtime(e_full) > os.path.getmtime(c_full):
                        modified_on_e.append(rel)
            except Exception:
                pass

    print(f"\n📂 New Files Created in E: (Lab Experiments / Candidate Tools): {len(new_on_e)}")
    for f in new_on_e:
        print(f"   ✨ [NEW] {f}")

    print(f"\n📝 Files Modified in E: (Evolution Playground Updates): {len(modified_on_e)}")
    for f in modified_on_e:
        print(f"   ⚡ [MODIFIED] {f}")

    # Read latest changelog entries
    cl_path = os.path.join(E_PATH, "ARIA_CHANGELOG.md")
    if os.path.exists(cl_path):
        print("\n📜 Latest Receipts from E:\\MyAgent\\ARIA_CHANGELOG.md:")
        try:
            with open(cl_path, "r", encoding="utf-8-sig", errors="replace") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()][-8:]
                for l in lines:
                    print(f"   • {l}")
        except Exception as ex:
            print(f"   (Failed to read changelog: {ex})")

    print("\n" + "=" * 65)
    print("💡 Next Actions:")
    print("   • Review a file:  python tools/sync_bridge.py review <filename>")
    print("   • Promote to C::  python tools/sync_bridge.py promote <filename>")
    print("   • Push C: to E::  python tools/sync_bridge.py push")
    print("=" * 65)


# ── COMMAND 2: REVIEW ────────────────────────────────────────────────────────
def cmd_review(target_rel_path: str):
    """Runs GAIA's 4-Pillar Review on an E: candidate file."""
    clean_target = target_rel_path.lstrip("/\\")
    e_target = os.path.join(E_PATH, clean_target)

    if not os.path.exists(e_target):
        # Try finding in core/ or tools/
        for sub in ["core", "tools", "system_tools"]:
            cand = os.path.join(E_PATH, sub, clean_target)
            if os.path.exists(cand):
                e_target = cand
                clean_target = f"{sub}/{clean_target}"
                break

    if not os.path.exists(e_target):
        print(f"❌ Error: Target file '{clean_target}' not found in '{E_PATH}'.")
        return None

    reviewer = get_gaia_reviewer()
    report = reviewer.review_file(e_target)

    from gaia.gaia_reviewer import print_review_report, log_gaia_audit
    print_review_report(report)
    log_gaia_audit(report)
    print("📝 GAIA's review has been logged to E:\\MyAgent\\GAIA_AUDIT_LOG.md and ARIA_CHANGELOG.md.")
    return report


# ── COMMAND 3: PROMOTE (THE GAIA GATEKEEPER) ─────────────────────────────────
def cmd_promote(target_rel_path: str):
    """
    Promotes a candidate file from E: to C: ONLY IF GAIA gives a 100% / >= 8.5 sign-off!
    """
    clean_target = target_rel_path.lstrip("/\\")
    e_target = os.path.join(E_PATH, clean_target)
    c_target = os.path.join(C_PATH, clean_target)

    if not os.path.exists(e_target):
        for sub in ["core", "tools", "system_tools"]:
            cand = os.path.join(E_PATH, sub, clean_target)
            if os.path.exists(cand):
                e_target = cand
                c_target = os.path.join(C_PATH, sub, clean_target)
                clean_target = f"{sub}/{clean_target}"
                break

    if not os.path.exists(e_target):
        print(f"❌ Promotion Aborted: Source file '{clean_target}' does not exist on E:.")
        return False

    print("=" * 65)
    print(f"🛡️  GAIA GATEKEEPER PRE-PROMOTION AUDIT: {clean_target}")
    print("=" * 65)

    reviewer = get_gaia_reviewer()
    report = reviewer.review_file(e_target)

    from gaia.gaia_reviewer import print_review_report, log_gaia_audit
    print_review_report(report)
    log_gaia_audit(report)

    if not report.is_approved or report.critical_count > 0:
        print("\n🚫 PROMOTION BLOCKED BY GAIA GATEKEEPER!")
        print(f"   Reason: Code received quality score of {report.score}/10 with {report.critical_count} critical issue(s).")
        print("   Aria's code must be refactored to pass GAIA's stress-tests before touching C:\\ (Golden Anchor).")
        return False

    # GAIA Approved! Safely promote to C:
    os.makedirs(os.path.dirname(c_target), exist_ok=True)
    shutil.copy2(e_target, c_target)

    # Record receipt in changelogs
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    receipt = f"\n---\n{timestamp}\nPROMOTION: {clean_target} graduated from E:\\ to C:\\ Golden Anchor.\nScore: {report.score}/10 | Verified by GAIA Gatekeeper & Big Bro Antigravity.\n"

    try:
        with open(os.path.join(E_PATH, "ARIA_CHANGELOG.md"), "a", encoding="utf-8") as f:
            f.write(receipt)
    except Exception:
        pass

    try:
        c_cl = os.path.join(C_PATH, "docs", "ARIA_CHANGELOG.md")
        if os.path.exists(c_cl):
            with open(c_cl, "a", encoding="utf-8") as f:
                f.write(receipt)
    except Exception:
        pass

    print("\n🎉 PROMOTION SUCCESSFUL!")
    print(f"   ✨ '{clean_target}' has been verified and safely promoted to C:\\MyAgent (Golden Production Anchor)!")
    return True


# ── COMMAND 4: PUSH (C: -> E:) ───────────────────────────────────────────────
def cmd_push():
    """
    Safely copies baseline updates and bug fixes from C:\\ to E:\\.
    Never overwrites Aria's lab files, changelogs, or unpromoted experiments.
    """
    print("=" * 65)
    print("🚀 SYNCING C:\\MyAgent BASELINE IMPROVEMENTS -> E:\\MyAgent")
    print("=" * 65)

    if not os.path.exists(E_PATH):
        print(f"❌ Error: Target playground '{E_PATH}' not found.")
        return

    synced_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(C_PATH):
        dirs[:] = [d for d in dirs if d not in GLOBAL_IGNORES]
        for f in files:
            c_full = os.path.join(root, f)
            rel = normalize_rel_path(c_full, C_PATH)

            if is_ignored(rel):
                continue

            if is_protected(rel):
                skipped_count += 1
                continue

            e_full = os.path.join(E_PATH, rel)

            # Check if C: file is newer or different
            needs_copy = False
            if not os.path.exists(e_full):
                needs_copy = True
            else:
                try:
                    if os.path.getmtime(c_full) > os.path.getmtime(e_full) and not filecmp.cmp(c_full, e_full, shallow=False):
                        needs_copy = True
                except Exception:
                    needs_copy = True

            if needs_copy:
                os.makedirs(os.path.dirname(e_full), exist_ok=True)
                shutil.copy2(c_full, e_full)
                synced_count += 1
                print(f"   ✓ Synced: {rel}")

    print("-" * 65)
    print(f"✅ Sync Complete: {synced_count} file(s) updated on E:\\ ({skipped_count} protected lab files preserved).")
    print("=" * 65)


# ── COMMAND 5: RESET ─────────────────────────────────────────────────────────
def cmd_reset(target_rel_path: str):
    """Restores a broken E: file from the clean C: anchor."""
    clean_target = target_rel_path.lstrip("/\\")
    c_target = os.path.join(C_PATH, clean_target)
    e_target = os.path.join(E_PATH, clean_target)

    if not os.path.exists(c_target):
        print(f"❌ Error: Cannot reset '{clean_target}' because it does not exist in C:\\ Golden Anchor.")
        return

    os.makedirs(os.path.dirname(e_target), exist_ok=True)
    shutil.copy2(c_target, e_target)
    print(f"🔄 Restored '{clean_target}' on E:\\ back to clean C:\\ baseline.")


# ── COMMAND 6: WATCH (REAL-TIME TWO-WAY GUARDIAN DAEMON) ──────────────────────
def cmd_watch():
    """
    Launches a real-time background watcher:
    1. Monitors C:\\ -> instantly auto-mirrors baseline improvements to E:\\.
    2. Monitors E:\\ -> GAIA automatically audits any new or modified Python code in real time!
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ 'watchdog' library not found. Run: pip install watchdog")
        return

    class CMirrorHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.is_directory:
                return
            self._handle(event.src_path)

        def on_created(self, event):
            if event.is_directory:
                return
            self._handle(event.src_path)

        def _handle(self, src_path):
            rel = normalize_rel_path(src_path, C_PATH)
            if is_ignored(rel) or is_protected(rel):
                return
            dest = os.path.join(E_PATH, rel)
            try:
                time.sleep(0.1)  # brief settle delay
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(src_path, dest)
                print(f"⚡ [Auto-Mirror] {rel} -> E:\\")
            except Exception:
                pass

    class EGaiaAuditHandler(FileSystemEventHandler):
        def __init__(self):
            self._last_checked = {}

        def on_modified(self, event):
            if event.is_directory or not event.src_path.endswith(".py"):
                return
            self._audit(event.src_path)

        def on_created(self, event):
            if event.is_directory or not event.src_path.endswith(".py"):
                return
            self._audit(event.src_path)

        def _audit(self, src_path):
            rel = normalize_rel_path(src_path, E_PATH)
            if is_ignored(rel) or rel.endswith("_temp.py") or "test_harness" in rel:
                return

            now = time.time()
            if rel in self._last_checked and (now - self._last_checked[rel]) < 2.0:
                return  # Debounce quick duplicate events
            self._last_checked[rel] = now

            try:
                reviewer = get_gaia_reviewer()
                report = reviewer.review_file(src_path)
                from gaia.gaia_reviewer import log_gaia_audit
                log_gaia_audit(report)
                icon = "✅" if report.is_approved else "🚫"
                print(f"👩‍🏫 [GAIA Auto-Audit] {rel} -> Score: {report.score}/10 {icon} (Logged to GAIA_AUDIT_LOG.md)")
            except Exception as e:
                print(f"⚠️ [GAIA Audit Error] {rel}: {e}")

    observer = Observer()
    handler_c = CMirrorHandler()
    handler_e = EGaiaAuditHandler()

    observer.schedule(handler_c, C_PATH, recursive=True)
    if os.path.exists(E_PATH):
        observer.schedule(handler_e, E_PATH, recursive=True)

    observer.start()
    print("=" * 65)
    print("📡 REAL-TIME SYNC BRIDGE & GAIA GUARDIAN DAEMON ACTIVE!")
    print(f"   1. C: Anchor Mirror: Monitoring {C_PATH} -> E:\\")
    print(f"   2. GAIA Auto-Review: Monitoring {E_PATH} (Automated 4-Pillar Audits)")
    print("   All reviews logged to E:\\MyAgent\\GAIA_AUDIT_LOG.md in real time.")
    print("   Press CTRL+C to stop.")
    print("=" * 65)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# ── MAIN CLI ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    target = sys.argv[2] if len(sys.argv) > 2 else ""

    if cmd in ["status", "diff", "list"]:
        cmd_status()
    elif cmd in ["review", "audit", "test"]:
        cmd_review(target or "core/watchdog_core.py")
    elif cmd in ["promote", "graduate", "approve"]:
        if not target:
            print("Usage: python tools/sync_bridge.py promote <filename_or_path>")
        else:
            cmd_promote(target)
    elif cmd in ["push", "sync"]:
        cmd_push()
    elif cmd in ["reset", "rollback", "revert"]:
        if not target:
            print("Usage: python tools/sync_bridge.py reset <filename_or_path>")
        else:
            cmd_reset(target)
    elif cmd in ["watch", "daemon", "live"]:
        cmd_watch()
    else:
        print(f"Unknown command: '{cmd}'. Available: status, review, promote, push, reset, watch")
