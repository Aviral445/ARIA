"""
agent.py — Voice & Terminal CLI Agent launcher for Aria AI
Forwards to core/agent.py
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.agent import main

if __name__ == "__main__":
    main()
