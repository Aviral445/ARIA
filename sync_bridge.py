"""
sync_bridge.py — Root launcher for the Mirror Bridge & GAIA Gatekeeper Pipeline
Usage:
    python sync_bridge.py status
    python sync_bridge.py push
    python sync_bridge.py review core/watchdog_core.py
    python sync_bridge.py promote core/watchdog_core.py
    python sync_bridge.py watch
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools import sync_bridge

if __name__ == "__main__":
    # Forward all CLI arguments to tools.sync_bridge
    sys.argv[0] = os.path.join(_ROOT, "tools", "sync_bridge.py")
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    target = sys.argv[2] if len(sys.argv) > 2 else ""

    if cmd in ["status", "diff", "list"]:
        sync_bridge.cmd_status()
    elif cmd in ["review", "audit", "test"]:
        sync_bridge.cmd_review(target or "core/watchdog_core.py")
    elif cmd in ["promote", "graduate", "approve"]:
        if not target:
            print("Usage: python sync_bridge.py promote <filename_or_path>")
        else:
            sync_bridge.cmd_promote(target)
    elif cmd in ["push", "sync"]:
        sync_bridge.cmd_push()
    elif cmd in ["reset", "rollback", "revert"]:
        if not target:
            print("Usage: python sync_bridge.py reset <filename_or_path>")
        else:
            sync_bridge.cmd_reset(target)
    elif cmd in ["watch", "daemon", "live"]:
        sync_bridge.cmd_watch()
    else:
        print(f"Unknown command: '{cmd}'. Available: status, review, promote, push, reset, watch")
