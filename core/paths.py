"""
core/paths.py — Centralized Path Resolution for Aria AI
Ensures consistent resolution of all data, config, models, and docs directories
regardless of the working directory or execution context.
"""

import os

# Root directory of the MyAgent workspace (parent of core/)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Standardized Subdirectories
CORE_DIR   = os.path.join(ROOT_DIR, "core")
TOOLS_DIR  = os.path.join(ROOT_DIR, "tools")
GUI_DIR    = os.path.join(ROOT_DIR, "gui")
SERVER_DIR = os.path.join(ROOT_DIR, "server")
MCP_DIR    = os.path.join(ROOT_DIR, "mcp")
DATA_DIR   = os.path.join(ROOT_DIR, "data")
CONFIG_DIR = os.path.join(ROOT_DIR, "config")
MODELS_DIR = os.path.join(ROOT_DIR, "models")
DOCS_DIR   = os.path.join(ROOT_DIR, "docs")
TESTS_DIR  = os.path.join(ROOT_DIR, "tests")

# Environment
ENV_FILE   = os.path.join(ROOT_DIR, ".env")

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
