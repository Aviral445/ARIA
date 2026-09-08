"""
aria_api.py — Multi-Device Companion Server launcher for Aria AI
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.aria_api:app", host="0.0.0.0", port=8000, reload=False)
