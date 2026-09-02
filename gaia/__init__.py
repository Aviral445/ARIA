"""
gaia package — Big Sister & AI Supervisor for Aria.
Hierarchical supervisor-worker architecture with AST security guardrails,
monitored sandboxed runtime, auto-healing, and human escalation.
"""

from gaia.gaia_supervisor import GaiaSupervisor, supervisor
from gaia.gaia_safety import audit_code_safety, SafetyReport
from gaia.gaia_healer import GaiaHealer
from gaia.gaia_voice import gaia_speak
from gaia.gaia_bus import bus
from gaia.gaia_runner import run_sandboxed_script

__all__ = [
    "GaiaSupervisor",
    "supervisor",
    "audit_code_safety",
    "SafetyReport",
    "GaiaHealer",
    "gaia_speak",
    "bus",
    "run_sandboxed_script",
]
