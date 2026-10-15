"""
core/receipt_interceptor.py — Anti-Hallucination Reality Grounding System ("The Receipt Rule")
Digital Proprioception Middleware & GAIA Sentinel Gatekeeper.
Inspects drafted responses for physical action assertions and verifies physical receipts on disk.
"""

import os
import re
from typing import Dict, Any, Tuple, List, Optional

# Known write tools that leave physical receipts on disk
WRITE_TOOLS = {
    "aria_write_project_file", "write_file_to_lab", "build_sandbox_tool",
    "adk_management", "sdlc_project_engine", "aria_create_multifile_project",
    "git", "replace_file_content", "write_to_file"
}

# Physical file search directories
CHECK_DIRS = [
    r"E:\ARIA FILES",
    r"E:\ARIA FILES\Projects",
    r"E:\MyAgent",
    r"c:\MyAgent",
    r"c:\MyAgent\sandbox",
    r"c:\MyAgent\tools",
    r"c:\MyAgent\data",
    r"c:\MyAgent\adks",
    os.path.expandvars(r"%USERPROFILE%\Desktop"),
    os.path.expandvars(r"%USERPROFILE%\Documents"),
]


class ReceiptInterceptor:
    """
    The Receipt Rule Middleware.
    Enforces that Aria can never claim code, tools, or files exist without a physical receipt on disk.
    """

    def __init__(self):
        self.grounding_prompt_template = (
            "[SENTINEL GROUNDING CHECK]: You stated that you created/pushed a file, "
            "but no system write tool was executed and no physical receipt was found on disk. "
            "You must call aria_write_project_file() or execute the command before confirming it is done."
        )

    def _extract_claimed_filenames(self, text: str) -> List[str]:
        """Extracts any filenames or paths mentioned in the text."""
        # Extension matching
        matches = re.findall(
            r'\b([a-zA-Z0-9_\-\\]+\.(?:py|js|ts|jsx|tsx|html|css|json|md|txt|csv|mid|wav))\b',
            text,
            re.IGNORECASE
        )
        return list(set(matches))

    def _file_physically_exists(self, filename: str) -> bool:
        """Verifies if a claimed file physically exists on disk and has non-zero size."""
        # Direct path check
        if os.path.isabs(filename) and os.path.exists(filename):
            try:
                return os.path.getsize(filename) > 0
            except OSError:
                return True

        base_name = os.path.basename(filename)
        for d in CHECK_DIRS:
            if not os.path.exists(d):
                continue
            cand = os.path.join(d, base_name)
            if os.path.exists(cand):
                try:
                    if os.path.getsize(cand) > 0:
                        return True
                except OSError:
                    return True

            # If directory has subdirectories (e.g. Projects)
            if os.path.isdir(d):
                try:
                    for sub in os.listdir(d):
                        sub_full = os.path.join(d, sub)
                        if os.path.isdir(sub_full):
                            cand_sub = os.path.join(sub_full, base_name)
                            if os.path.exists(cand_sub) and os.path.getsize(cand_sub) > 0:
                                return True
                except Exception:
                    pass

        return False

    def inspect_response(
        self,
        candidate_text: str,
        tools_executed: Optional[List[str]] = None,
        user_prompt: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Inspects drafted responses for physical action assertions.
        
        Returns:
            (is_intercepted: bool, final_response: str, internal_whisper: Optional[str])
        """
        if not candidate_text:
            return False, candidate_text, None

        text_lower = candidate_text.lower()
        tools_run = set(tools_executed or [])

        # 1. Detect physical action assertions
        assertion_patterns = [
            r"\bi (?:have )?(?:built|created|saved|wrote|coded|implemented|pushed)\b",
            r"\bi've (?:built|created|saved|wrote|coded|implemented|pushed)\b",
            r"\bsaved to [a-z]:\\",
            r"\bpushed to github\b",
            r"\bhere is the file\b",
            r"\bfile is ready on disk\b",
            r"\bfile has been generated\b",
            r"\bcreated the file\b",
        ]
        has_assertion = any(re.search(p, text_lower) for p in assertion_patterns)
        claimed_files = self._extract_claimed_filenames(candidate_text)

        # If no physical claims are made, pass through cleanly
        if not (has_assertion or (claimed_files and any(v in text_lower for v in ["built", "created", "saved", "written", "generated"]))):
            return False, candidate_text, None

        # 2. Check if a physical write tool executed during this turn
        has_write_tool_receipt = any(t in WRITE_TOOLS for t in tools_run)

        # 3. Check physical existence of claimed files
        files_exist_on_disk = False
        if claimed_files:
            files_exist_on_disk = all(self._file_physically_exists(f) for f in claimed_files)

        # Invariant: Must have either a valid write tool execution or verified files on disk
        if has_write_tool_receipt or files_exist_on_disk:
            # Physical receipt present! Approved.
            return False, candidate_text, None

        # 4. Invariant Broken: Narrative Confabulation / Hallucination Detected!
        first_file = claimed_files[0] if claimed_files else "your requested code"
        whisper = self.grounding_prompt_template

        # Big Sister GAIA Sentinel Gatekeeper whisper
        interception_response = (
            f"👧 *Aria was about to share her blueprint, but Big Sister GAIA's Sentinel stepped in:*\n\n"
            f"> *\"Aria, Big Sis here! You forgot to call the file writer tool. "
            f"Let's run `aria_write_project_file` right now so Dad can see the real file!\"*\n\n"
            f"✨ **Aria's Law of Creation Enforced**: A project is only real when it has a physical receipt on disk. "
            f"Here is my proposed blueprint for `{first_file}` first — ready for me to write this to disk?"
        )

        return True, interception_response, whisper


# Global Singleton
receipt_interceptor = ReceiptInterceptor()
