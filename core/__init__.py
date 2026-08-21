# core package initialization
import sys, os
from .paths import ROOT_DIR, DATA_DIR, CONFIG_DIR

# Ensure ROOT_DIR, core, tools, server, mcp, gui are on sys.path
for p in [ROOT_DIR, os.path.join(ROOT_DIR, "core"), os.path.join(ROOT_DIR, "tools"), os.path.join(ROOT_DIR, "server"), os.path.join(ROOT_DIR, "mcp"), os.path.join(ROOT_DIR, "gui")]:
    if p not in sys.path:
        sys.path.insert(0, p)
