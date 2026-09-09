r"""
system_tools/adk_management.py — Autonomous ADK Management Tool for Aria & GAIA

Provides a unified, action-routed capability for creating, managing, connecting,
inspecting, and cleanly decommissioning Agent Development Kits (ADKs).
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List, Tuple

# Ensure project root is accessible
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.aria_adk_manager import get_adk_manager


def adk_management(
    action: str = "list",
    adk_name: str = "",
    target_adk: str = "",
    filename: str = "",
    content: str = "",
    query: str = "",
    author: str = "Aria",
    description: str = "",
    options: Optional[Dict[str, Any]] = None
) -> str:
    r"""
    Autonomous ADK Lifecycle Management Tool for Aria and GAIA.
    Enforces the single-project focus, Windows filesystem safety, and clean slate protocol.

    Args:
        action: Operational verb:
            • 'create': Create a new ADK directory (manifest, tools, rules, tests).
            • 'create_batch': Create multiple ADKs simultaneously (pass list in options['adks']).
            • 'list': View all active, installed, and mounted ADKs.
            • 'search': Semantic & keyword search for capabilities before creating duplicates.
            • 'find': Quick targeted lookup for a specific ADK name or tool.
            • 'read': Inspect an ADK file (manifest, tools.py, rules.md, or test_adk.py).
            • 'write': Atomically update code or configuration in an ADK.
            • 'connect': Chain two ADKs into a data pipeline (source adk_name ──> target_adk).
            • 'explain': Generate an architectural overview of what an ADK does.
            • 'define': Extract formal parameter signatures and contracts for ADK tools.
            • 'understand': Perform static AST security and sandbox validation on an ADK.
            • 'delete': Safely unmount and delete an individual ADK.
            • 'decommission_swarm': Purge all temporary project ADKs to free RAM and processing power.
            • 'report_incident': Dispatch an error or impasse to Big Sister GAIA Supervisor.

        adk_name: Target ADK name (e.g. 'Web_Scraper_ADK', 'Data_Parser_ADK').
        target_adk: Destination ADK name when connecting two ADKs together (for action='connect').
        filename: Target file within the ADK (e.g. 'tools.py', 'rules.md', 'test_adk.py').
        content: Code or text payload when action='create' or action='write'.
        query: Search keywords or capability description when action='search' or 'find'.
        author: Creator identity ('Aria' or 'GAIA'). Default: 'Aria'.
        description: Brief purpose of the ADK.
        options: Optional parameters dictionary (e.g. {'adks': ['A_ADK', 'B_ADK']} for batch).

    Returns:
        str: Human and machine-readable execution summary or JSON report.
    """
    act = (action or "list").lower().strip()
    mgr = get_adk_manager()
    opts = options or {}
    if isinstance(opts, str):
        try:
            opts = json.loads(opts)
        except Exception:
            opts = {}

    try:
        # 1. CREATION
        if act in ("create", "new", "scaffold"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to create an ADK."
            res = mgr.create_adk(
                adk_name=adk_name,
                author=author,
                description=description,
                tools_code=content if content and filename in ("tools.py", "") else None,
                rules_text=content if filename == "rules.md" else None
            )
            return json.dumps(res, indent=2)

        elif act in ("create_batch", "batch_create", "swarm_create"):
            adk_list = opts.get("adks", [])
            if not adk_list and query:
                adk_list = [k.strip() for k in query.split(",") if k.strip()]
            if not adk_list:
                return "Error: Please provide a list of ADK names in options['adks'] or as a comma-separated string in query."
            res = mgr.create_batch(adk_names=adk_list, author=author, shared_description=description)
            return json.dumps(res, indent=2)

        # 2. LIST & SEARCH
        elif act in ("list", "ls", "all"):
            adks = mgr.list_adks()
            if not adks:
                return "📂 No ADKs are currently installed in the workspace. Ready to create your first ADK!"
            summary = [f"📦 Active ADKs in Workspace ({len(adks)}):"]
            for a in adks:
                tools_str = ", ".join(a.get("tools", [])) or "None"
                conns = ", ".join([c.get("target", "") for c in a.get("connected_to", [])]) or "None"
                summary.append(
                    f"  • {a.get('adk_name')} [v{a.get('version', '1.0')}] by {a.get('author', 'Aria')} "
                    f"— Status: {a.get('status')} | Tools: [{tools_str}] | Connected: [{conns}]"
                )
            return "\n".join(summary)

        elif act in ("search", "find", "lookup"):
            q = query or adk_name or description
            if not q:
                return "Error: Please provide a search query in 'query' or 'adk_name'."
            matches = mgr.search_adks(query=q)
            if not matches:
                return f"🔍 No existing ADKs match '{q}'. You are clear to create a new ADK without duplicating!"
            summary = [f"🔍 Found {len(matches)} matching ADK(s) for '{q}':"]
            for m in matches:
                tools_str = ", ".join(m.get("tools", [])) or "None"
                summary.append(f"  • {m.get('adk_name')}: {m.get('description', '')} (Tools: {tools_str})")
            return "\n".join(summary)

        # 3. READ & WRITE
        elif act in ("read", "view", "cat", "get"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to read from."
            target_f = filename or "adk_manifest.json"
            res = mgr.read_adk_file(adk_name=adk_name, filename=target_f)
            if not res.get("success"):
                return f"Error: {res.get('error')}"
            if res.get("is_binary"):
                return f"[{adk_name}/{target_f}] Binary file ({res.get('size_bytes')} bytes)."
            return f"=== {adk_name}/{target_f} ===\n" + res.get("content", "")

        elif act in ("write", "update", "save"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to write into."
            target_f = filename or "tools.py"
            if not content:
                return f"Error: Please provide 'content' to write into {adk_name}/{target_f}."
            res = mgr.write_adk_file(adk_name=adk_name, filename=target_f, content=content)
            return json.dumps(res, indent=2)

        # 4. CONNECTION (PIPELINES)
        elif act in ("connect", "link", "chain"):
            if not adk_name or not target_adk:
                return "Error: Connecting ADKs requires both 'adk_name' (source) and 'target_adk' (destination)."
            conn_type = opts.get("type", "pipeline")
            res = mgr.connect_adks(source_adk=adk_name, target_adk=target_adk, connection_type=conn_type)
            return json.dumps(res, indent=2)

        # 5. COGNITIVE REASONING
        elif act in ("explain", "describe"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to explain."
            return mgr.explain_adk(adk_name=adk_name)

        elif act in ("define", "contract", "schema"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to extract contract."
            res = mgr.define_adk_contract(adk_name=adk_name)
            return json.dumps(res, indent=2)

        elif act in ("understand", "audit", "security_check"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to analyze."
            res = mgr.understand_adk(adk_name=adk_name)
            return json.dumps(res, indent=2)

        # 6. DELETION & CLEAN SLATE
        elif act in ("delete", "remove", "unmount"):
            if not adk_name:
                return "Error: Please specify 'adk_name' to delete."
            res = mgr.delete_adk(adk_name=adk_name)
            return json.dumps(res, indent=2)

        elif act in ("decommission_swarm", "clean_slate", "purge_swarm"):
            targets = opts.get("adks", None)
            res = mgr.decommission_swarm(adk_names=targets)
            return json.dumps(res, indent=2)

        # 7. SUPERVISOR INCIDENT ESCALATION
        elif act in ("report_incident", "escalate", "help"):
            if not adk_name:
                return "Error: Please specify 'adk_name' that encountered the impasse."
            task = opts.get("task", query or "Unknown task")
            error_type = opts.get("error_type", "ExecutionImpasse")
            traceback_str = opts.get("traceback", content or "No traceback provided.")
            attempts = int(opts.get("attempts", 1))
            res = mgr.report_incident(adk_name=adk_name, task=task, error_type=error_type, traceback_str=traceback_str, attempts=attempts)
            return json.dumps(res, indent=2)

        else:
            return (
                f"Unknown action '{action}'. Supported actions: 'create', 'create_batch', 'list', "
                f"'search', 'find', 'read', 'write', 'connect', 'explain', 'define', 'understand', "
                f"'delete', 'decommission_swarm', 'report_incident'."
            )

    except Exception as ex:
        return f"ADK Management Execution Error: {ex}"


def register_tool() -> Tuple[str, Any]:
    """Registers adk_management tool into Aria's live toolkit."""
    return "adk_management", adk_management
