"""
system_tools/adk_bridge_tool.py — Unified Invocation Bridge for Installed ADKs
Author: Aria & GAIA
Supervised by: Big Bro Antigravity
"""

import os
import sys
import importlib.util
from typing import Dict, Any, Tuple

# Restricted ADKs that are test fixtures or intentionally unstable
RESTRICTED_ADKS = {"faulty_adk", "disposable_adk"}

def aria_invoke_adk(adk_name: str, query: str = "") -> str:
    r"""
    Executes a capability from an installed Agent Development Kit (ADK) in c:\MyAgent\adks.
    Available ADKs include: Data_Analyzer_ADK, Source_ADK, Sink_ADK, Logic_ADK,
    Image_Processing_ADK, Audio_Synthesis_ADK, and Editor_ADK.

    Args:
        adk_name: Name of the target ADK (e.g. 'Data_Analyzer_ADK' or 'Source_ADK').
        query: Operational query or payload string to pass to the ADK.
    """
    clean_name = adk_name.strip()
    if clean_name.lower() in RESTRICTED_ADKS:
        return f"[ADK Security Block]: '{clean_name}' is a test fixture and restricted from direct production invocation."

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    adk_dir = os.path.join(root_dir, "adks", clean_name)

    if not os.path.exists(adk_dir):
        # Case-insensitive lookup fallback
        adk_base = os.path.join(root_dir, "adks")
        found = None
        if os.path.exists(adk_base):
            for d in os.listdir(adk_base):
                if d.lower() == clean_name.lower():
                    adk_dir = os.path.join(adk_base, d)
                    clean_name = d
                    found = True
                    break
        if not found:
            return f"[ADK Error]: ADK '{clean_name}' not found in installed catalog."

    tools_py = os.path.join(adk_dir, "tools.py")
    if not os.path.exists(tools_py):
        return f"[ADK Error]: 'tools.py' missing from '{clean_name}' package."

    try:
        spec = importlib.util.spec_from_file_location(f"adk_mod_{clean_name}", tools_py)
        if not spec or not spec.loader:
            return f"[ADK Error]: Failed to create module spec for '{clean_name}'."
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Look for sample_tool or any exported callable
        if hasattr(mod, "sample_tool"):
            res = mod.sample_tool(query=query)
            return f"[ADK {clean_name}]: {res}"
        elif hasattr(mod, "register_tools"):
            tools = mod.register_tools()
            if tools and callable(tools[0]):
                res = tools[0](query=query)
                return f"[ADK {clean_name}]: {res}"
        
        return f"[ADK {clean_name}]: Module loaded successfully (no primary entry point found)."
    except Exception as e:
        return f"[ADK Execution Error in {clean_name}]: {e}"

def register_tool() -> Tuple[str, Any]:
    return ("aria_invoke_adk", aria_invoke_adk)
