"""
agent.py — Backward-compatible root forwarder for Aria CLI Agent.
Proxies directly to core.agent for zero-friction legacy execution.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(_ROOT, "core")
for _p in [_ROOT, _CORE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.agent import *

if __name__ == "__main__":
    from core.agent import main
    main()
