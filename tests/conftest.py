"""
tests/conftest.py — Global Test Fixture & Path Configuration for Aria and GAIA.
Ensures repo root is anchored at sys.path[0] and the tools package is bound.
"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import tools
