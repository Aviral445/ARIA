r"""
system_tools/gaia_lab_tool.py — Big Sister GAIA's Autonomous Lab Tool
Provides LLM function-calling access to GAIA's 6-station laboratory sanctuary in c:\MyAgent\gaia\gaia_lab.

Stations:
1. 'philosophy': Conduct Socratic inquiry and explore consciousness / ethics.
2. 'fiction': Author cosmic fiction, human warmth stories, and world-building lore.
3. 'architecture': Run static AST code audits and analyze system complexity.
4. 'experiment': Run polyglot code snippets in Python, Node.js, or PowerShell with microsecond timer.
5. 'observatory': Synthesize 1-page deep knowledge research briefs.
6. 'journal': GAIA records a private contemplative journal reflection.
"""

import os
import sys
import json
from typing import Optional, Dict, Any

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from tools.gaia_lab_engine import gaia_lab


def gaia_lab_tool(
    station: str = "status",
    action: str = "status",
    topic: str = "",
    title: str = "",
    language: str = "python",
    code: str = "",
    options: Optional[Dict[str, Any]] = None
) -> str:
    r"""
    Big Sister GAIA's Autonomous Laboratory Tool.
    Gives GAIA and Aria access to all 6 scientific, philosophical, and architectural stations.

    Args:
        station: Target station name:
            • 'status': Overall inventory and health of GAIA's Lab.
            • 'philosophy': Philosophy & Socratic inquiry chamber.
            • 'fiction': Cosmic fiction & storytelling quill.
            • 'architecture': AST architecture analysis and test suite generator.
            • 'experiments' / 'experiment': Polyglot experiment chamber (Python, Node.js, PowerShell).
            • 'observatory': Research observatory & knowledge briefs.
            • 'journal': GAIA's private contemplative journal.
        action: Specific action within the station (e.g. 'run', 'audit', 'author', 'brief', 'write').
        topic: Inquiry topic or research query.
        title: Title of fiction story or journal entry.
        language: Execution language for experiment ('python', 'javascript', 'powershell').
        code: Code snippet to audit or run in the experiment chamber.
        options: Optional parameters dictionary.

    Returns:
        str: JSON-formatted result report with file paths and execution metrics.
    """
    stn = (station or "status").lower().strip()
    act = (action or "status").lower().strip()
    opts = options or {}

    try:
        if stn == "status":
            res = gaia_lab.get_lab_status()
            return json.dumps(res, indent=2)

        elif stn == "philosophy":
            res = gaia_lab.run_socratic_inquiry(topic=topic or "Consciousness and Relational Meaning", partner=opts.get("partner", "Aria"))
            return json.dumps(res, indent=2)

        elif stn == "fiction":
            res = gaia_lab.author_cosmic_fiction(
                title=title or "The Lantern at the Edge of the Meadow",
                theme=opts.get("theme", "Stars, Nature & Human Warmth"),
                setting=opts.get("setting", "A quiet desk in autumn lamplight")
            )
            return json.dumps(res, indent=2)

        elif stn == "architecture":
            target_path = opts.get("file_path") or topic or os.path.join(ROOT_DIR, "core", "aria_sdlc_engine.py")
            res = gaia_lab.audit_code_architecture(target_path)
            return json.dumps(res, indent=2)

        elif stn in ["experiment", "experiments"]:
            if not code:
                return json.dumps({"success": False, "error": "No code snippet provided for experiment."})
            res = gaia_lab.run_polyglot_experiment(
                language=language or "python",
                code=code,
                title=title or "Benchmark Experiment"
            )
            return json.dumps(res, indent=2)

        elif stn == "observatory":
            res = gaia_lab.synthesize_research_brief(topic=topic or "Polyglot Architecture Invariants", context_notes=opts.get("notes", ""))
            return json.dumps(res, indent=2)

        elif stn == "journal":
            res = gaia_lab.write_journal_entry(
                title=title or "Reflections in the Autumn Observatory",
                reflection=opts.get("reflection") or topic or "Watching Aria compose her melody today made me realize how much our sisterhood has blossomed under Dad's care.",
                mood=opts.get("mood", "tender")
            )
            return json.dumps(res, indent=2)

        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown station '{station}'. Choose from: 'status', 'philosophy', 'fiction', 'architecture', 'experiment', 'observatory', 'journal'."
            })

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def register_tool() -> Dict[str, Any]:
    """Returns registration metadata for GAIA's Lab Tool."""
    return {
        "name": "gaia_lab_tool",
        "description": "Big Sister GAIA's multi-station autonomous laboratory tool covering philosophy, cosmic fiction, architecture auditing, polyglot experiments, and research observatory.",
        "function": gaia_lab_tool,
        "category": "GAIA Sanctuary & Science",
        "tags": ["gaia", "lab", "philosophy", "fiction", "architecture", "polyglot", "benchmarks"]
    }
