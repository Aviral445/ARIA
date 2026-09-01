"""
aria_gui.py — Root Entrypoint & Launcher for Aria Desktop GUI
Proxies directly to gui.aria_gui
"""

import os, sys

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for _sub in [_ROOT_DIR, os.path.join(_ROOT_DIR, "core"), os.path.join(_ROOT_DIR, "tools"), os.path.join(_ROOT_DIR, "server"), os.path.join(_ROOT_DIR, "mcp"), os.path.join(_ROOT_DIR, "gui"), os.path.join(_ROOT_DIR, "backend")]:
    if _sub not in sys.path:
        sys.path.insert(0, _sub)

from gui.aria_gui import AriaGUI, main

if __name__ == "__main__":
    main()
