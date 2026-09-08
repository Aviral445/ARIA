"""
run.py — Unified Master Launcher for Aria AI & GAIA System
Forwards to core/run.py
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.run import main

if __name__ == "__main__":
    main()
