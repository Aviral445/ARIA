"""
run.py — Unified Master Launcher for Aria AI & GAIA System

Commands:
  python run.py [agent]        Launch interactive voice/text CLI agent (default)
  python run.py gui            Launch desktop Pygame Graphical User Interface
  python run.py api            Launch FastAPI remote mobile & web companion server
  python run.py gaia [options] Run GAIA Big Sister supervisor & architect CLI
  python run.py test           Execute automated verification test suite
"""

import os
import sys
import subprocess

# Set encoding-safe stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure repository root and core are discoverable
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.paths import CORE_DIR, SYSTEM_TOOLS_DIR, SERVER_DIR, GUI_DIR, DATA_DIR


def launch_agent(extra_args):
    """Launches the Aria CLI agent."""
    from core.agent import main
    sys.argv = ["agent.py"] + extra_args
    main()


def launch_gui(extra_args):
    """Launches the Pygame Desktop GUI."""
    from gui.aria_gui import main
    sys.argv = ["aria_gui.py"] + extra_args
    main()


def launch_api(extra_args):
    """Launches the FastAPI companion server."""
    port = 8000
    host = "0.0.0.0"
    for arg in extra_args:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg.startswith("--host="):
            host = arg.split("=")[1]
    print(f"🚀 Starting Aria FastAPI Server on http://{host}:{port}...")
    import uvicorn
    uvicorn.run("server.aria_api:app", host=host, port=port, reload=False)


def launch_gaia(extra_args):
    """Launches GAIA CLI (Supervisor & Architect)."""
    from gaia.gaia_cli import main
    sys.argv = ["gaia_cli.py"] + extra_args
    main()


def launch_test(extra_args):
    """Runs automated pytest verification suite."""
    print("[TEST] Running Aria & GAIA Test Suite...")
    cmd = [sys.executable, "-m", "pytest"] + (extra_args if extra_args else ["tests", "-v"])
    res = subprocess.run(cmd)
    sys.exit(res.returncode)


def print_help():
    print("""
============================================================
ARIA AI & GAIA SUPERVISOR -- UNIFIED LAUNCHER
============================================================
Usage: python run.py <command> [options]

Commands:
  agent            Launch Aria interactive voice/text CLI (default)
  gui              Launch Aria Pygame Desktop Companion
  api              Launch FastAPI mobile & web companion server
  gaia             Launch GAIA Supervisor & Architect CLI
                   Examples:
                     python run.py gaia --status
                     python run.py gaia --architect
                     python run.py gaia --architect-status
  test             Run the automated pytest test suite
============================================================
""")


def main():
    if len(sys.argv) < 2:
        launch_agent([])
        return

    cmd = sys.argv[1].lower()
    extra_args = sys.argv[2:]

    if cmd in ("-h", "--help", "help"):
        print_help()
    elif cmd in ("agent", "cli", "run"):
        launch_agent(extra_args)
    elif cmd in ("gui", "app", "desktop"):
        launch_gui(extra_args)
    elif cmd in ("api", "server", "web"):
        launch_api(extra_args)
    elif cmd == "gaia":
        launch_gaia(extra_args)
    elif cmd in ("test", "tests", "pytest"):
        launch_test(extra_args)
    else:
        # If command matches an argument for agent, pass it to agent
        launch_agent(sys.argv[1:])


if __name__ == "__main__":
    main()
