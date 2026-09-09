"""
system_tools/aria_data_collector_tool.py — Runner Bridge for E:\ARIA FILES Data_Collector
Author: Aria & GAIA
Supervised by: Big Bro Antigravity
"""

import os
import sys
import json
from typing import Dict, Any, Tuple

def aria_run_data_collector(task: str = "health_check", source: str = "all") -> str:
    r"""
    Executes the Data_Collector project located at E:\ARIA FILES\Projects\Data_Collector.
    
    Args:
        task: The task type to execute ('health_check', 'collect_system', 'collect_files', 'collect_adk', 'full_pipeline').
        source: Target data source ('all', 'system', 'file', 'web', 'adk').
    """
    project_root = r"E:\ARIA FILES\Projects\Data_Collector"
    src_dir = os.path.join(project_root, "src")

    if not os.path.exists(project_root) or not os.path.exists(src_dir):
        return f"[Data_Collector Error]: Project not found at {project_root}."

    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    try:
        from main_module import execute_task
        task_name = "full_pipeline" if source == "all" and task == "health_check" else task
        result = execute_task(task_name)
        receipt = result.get("receipt", "NO_RECEIPT")
        status = result.get("status", "UNKNOWN")
        sources = result.get("sources_collected", [])
        return f"[Data_Collector]: Executed '{task_name}' successfully with Status: {status}, Receipt: {receipt}, Sources: {sources}."
    except Exception as e:
        return f"[Data_Collector Error]: Execution failed: {e}"

def register_tool() -> Tuple[str, Any]:
    return ("aria_run_data_collector", aria_run_data_collector)
