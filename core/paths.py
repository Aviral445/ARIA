"""
core/paths.py — Centralized Path Resolution for Aria AI
Ensures consistent resolution of all data, config, models, system tools,
sandbox, and docs directories regardless of working directory or execution context.
"""

import os
import sys

# Root directory of the MyAgent workspace (parent of core/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Standardized Subdirectories
CORE_DIR         = os.path.join(ROOT_DIR, "core")
SYSTEM_TOOLS_DIR = os.path.join(ROOT_DIR, "system_tools")
TOOLS_DIR        = SYSTEM_TOOLS_DIR  # Alias for backward compatibility
GUI_DIR          = os.path.join(ROOT_DIR, "gui")
SERVER_DIR       = os.path.join(ROOT_DIR, "server")
MCP_DIR          = os.path.join(ROOT_DIR, "mcp")
DATA_DIR         = os.path.join(ROOT_DIR, "data")
CONFIG_DIR       = os.path.join(ROOT_DIR, "config")
MODELS_DIR       = os.path.join(ROOT_DIR, "models")
DOCS_DIR         = os.path.join(ROOT_DIR, "docs")
GUIDELINES_DIR   = os.path.join(DOCS_DIR, "guidelines")
TESTS_DIR        = os.path.join(ROOT_DIR, "tests")
GAIA_DIR         = os.path.join(ROOT_DIR, "gaia")

# Isolated Sandbox (The Agent's Playground at Root)
SANDBOX_DIR           = os.path.join(ROOT_DIR, "sandbox")
SANDBOX_WORKSPACE_DIR = os.path.join(SANDBOX_DIR, "workspace")
SANDBOX_TOOLS_DIR     = os.path.join(SANDBOX_DIR, "tools")
SANDBOX_SNAPSHOTS_DIR = os.path.join(SANDBOX_DIR, "snapshots")
SANDBOX_INCIDENTS_DIR = os.path.join(SANDBOX_DIR, "incidents")

# Cognitive Telemetry & Inner Mind (Nested under data/)
INNER_MIND_DIR = os.path.join(DATA_DIR, "inner_mind")

# Evolution & Baseline Paths
ARIA_EVOLVED_DIR = r"E:\MyAgent" if os.path.exists(r"E:\MyAgent") else SANDBOX_DIR
ARIA_BASELINE_FILE = os.path.join(CORE_DIR, "agent.py")
ARIA_EVOLVED_FILE = os.path.join(ARIA_EVOLVED_DIR, "aria_evolved.py")

# Dedicated Personal Files Workspace for Aria (E:\ARIA FILES)
ARIA_FILES_DIR = r"E:\ARIA FILES" if (os.path.exists(r"E:\ARIA FILES") or os.path.exists("E:\\")) else os.path.join(ROOT_DIR, "data", "aria_files")
try:
    os.makedirs(ARIA_FILES_DIR, exist_ok=True)
except Exception:
    pass

# Environment
ENV_FILE = os.path.join(ROOT_DIR, ".env")

# Ensure sub-packages are discoverable across the entire runtime
for _p in [ROOT_DIR, CORE_DIR, SYSTEM_TOOLS_DIR, SERVER_DIR, MCP_DIR, GUI_DIR, DATA_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# Helper function to find a file checking data/config/root
def get_data_file(filename: str, create_if_missing: bool = False) -> str:
    """Returns absolute path to a data file, checking data/ and fallback to root."""
    data_path = os.path.join(DATA_DIR, filename)
    root_path = os.path.join(ROOT_DIR, filename)
    if os.path.exists(data_path):
        return data_path
    if os.path.exists(root_path):
        return root_path
    if create_if_missing:
        os.makedirs(DATA_DIR, exist_ok=True)
        return data_path
    return data_path


def get_config_file(filename: str) -> str:
    """Returns absolute path to a configuration file, checking config/ and fallback to root."""
    cfg_path = os.path.join(CONFIG_DIR, filename)
    root_path = os.path.join(ROOT_DIR, filename)
    if os.path.exists(cfg_path):
        return cfg_path
    if os.path.exists(root_path):
        return root_path
    return cfg_path
