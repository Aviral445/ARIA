"""
core/aria_approval_gate.py — Human-in-the-Loop (HITL) Approval Gates (Feature 51)
Enforces tiered risk assessment on tool execution and intercepts consequential,
destructive, or irreversible actions (file deletion, system modification, external messages)
until explicit human approval is granted.
"""

import os
import json
import time
from enum import Enum
from typing import Dict, Any, Tuple, Optional, Callable

from core.paths import DATA_DIR
from gaia.gaia_bus import bus

AUDIT_LOG_FILE = os.path.join(DATA_DIR, "approval_audit.jsonl")


class RiskTier(str, Enum):
    LOW = "LOW"            # Read-only, informational, safe calculations
    MEDIUM = "MEDIUM"      # Benign writes, reminders, harmless updates
    HIGH = "HIGH"          # Destructive file ops, sensitive edits, external sends
    CRITICAL = "CRITICAL"  # Shell execution, deletions outside sandbox, disk/system operations


# Mapping of tools / actions to baseline risk tiers
CRITICAL_TOOLS = {
    "run_sandbox_code", "execute_macro", "organize_files_by_type",
    "delete_file", "rmdir", "remove_item", "wipe_memory"
}

HIGH_RISK_TOOLS = {
    "send_whatsapp_message", "send_slack_message", "create_jira_issue",
    "aria_github", "trigger_smart_device", "write_project_file"
}

MEDIUM_RISK_TOOLS = {
    "quick_note_tool", "set_reminder", "create_user_goal", "set_dnd_mode",
    "write_file_to_lab", "build_sandbox_tool", "notion_tool"
}


class ApprovalGate:
    def __init__(self):
        self._auto_approve: bool = False
        self._custom_approver: Optional[Callable[[str, Dict[str, Any], RiskTier], bool]] = None

    def set_auto_approve(self, enabled: bool):
        """Used during testing or autonomous headless operation."""
        self._auto_approve = enabled

    def set_custom_approver(self, approver: Callable[[str, Dict[str, Any], RiskTier], bool]):
        """Sets an interactive UI/Voice approval callback."""
        self._custom_approver = approver

    def assess_risk(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> RiskTier:
        """Determines the risk tier of an intended tool call."""
        args = arguments or {}
        name = tool_name.lower().strip()

        # Check critical keywords in arguments
        arg_str = json.dumps(args).lower()
        if any(w in arg_str for w in ["rmdir", "del ", "delete", "format", "drop", "wipe", "truncate"]):
            return RiskTier.CRITICAL

        if name in CRITICAL_TOOLS:
            return RiskTier.CRITICAL
        if name in HIGH_RISK_TOOLS:
            return RiskTier.HIGH
        if name in MEDIUM_RISK_TOOLS:
            return RiskTier.MEDIUM

        return RiskTier.LOW

    def check_approval(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        context_msg: str = ""
    ) -> Tuple[bool, str, RiskTier]:
        """
        Evaluates risk and determines whether action is approved or blocked.
        Returns: (is_approved, explanation, risk_tier)
        """
        args = arguments or {}
        tier = self.assess_risk(tool_name, args)

        # Low and Medium risk tiers pass automatically with audit trace
        if tier in [RiskTier.LOW, RiskTier.MEDIUM]:
            self._log_audit(tool_name, args, tier, True, "Auto-approved by policy")
            return True, f"Action '{tool_name}' pre-approved ({tier.value}).", tier

        # If headless/test auto-approve is active
        if self._auto_approve:
            self._log_audit(tool_name, args, tier, True, "Auto-approved via override")
            return True, f"Action '{tool_name}' approved via auto-approve override.", tier

        # Interactive approval callback
        if self._custom_approver is not None:
            approved = self._custom_approver(tool_name, args, tier)
            status = "Approved by human callback" if approved else "Rejected by human callback"
            self._log_audit(tool_name, args, tier, approved, status)
            return approved, status, tier

        # If no approver configured and High/Critical, require explicit approval
        bus.emit(
            "APPROVAL_GATE",
            "GATE_TRIGGERED",
            f"Action '{tool_name}' ({tier.value}) requires explicit human confirmation.",
            {"tool": tool_name, "tier": tier.value, "args": args}
        )
        msg = f"Confirmation required: '{tool_name}' has {tier.value} risk. Action held for human approval."
        self._log_audit(tool_name, args, tier, False, "Held pending user confirmation")
        return False, msg, tier

    def _log_audit(self, tool: str, args: Dict[str, Any], tier: RiskTier, approved: bool, reason: str):
        """Appends immutable audit record to approval_audit.jsonl."""
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool": tool,
            "args_summary": str(args)[:300],
            "risk_tier": tier.value,
            "approved": approved,
            "reason": reason
        }
        try:
            os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass


# Global singleton instance
approval_gate = ApprovalGate()
