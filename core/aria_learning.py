"""
aria_learning.py — Continuous Learning & Self-Correction Engine for Aria
Allows Aria to learn from user feedback, correct mistakes, and persist rules.
"""

import os, json, time, re

try:
    from .paths import get_data_file
except ImportError:
    from paths import get_data_file

CORRECTIONS_FILE = get_data_file("learned_corrections.json", create_if_missing=True)

def _load_corrections() -> dict:
    if os.path.exists(CORRECTIONS_FILE):
        try:
            with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "rules": [
            "When user asks for a document, PDF, or file, use file search instead of open_app.",
            "User profile name is a proper name, never treat it as a dark mode command.",
            "When user specifies recipient and message in WhatsApp, automate typing and sending.",
        ],
        "custom_mappings": {},
        "history": []
    }

def _save_corrections(data: dict):
    try:
        with open(CORRECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Learning] Save error: {e}")

def add_learned_rule(rule_text: str) -> str:
    """Adds a new persistent rule or correction."""
    data = _load_corrections()
    if rule_text not in data["rules"]:
        data["rules"].append(rule_text)
        _save_corrections(data)
    return f"Learned new rule: '{rule_text}'. I will apply this in all future interactions!"

def add_custom_alias(trigger: str, target_action: str) -> str:
    """Maps a user shortcut/alias to a target action (e.g. 'work mode' -> 'open vs code and slack')."""
    data = _load_corrections()
    data["custom_mappings"][trigger.lower().strip()] = target_action.strip()
    _save_corrections(data)
    return f"Got it! Whenever you say '{trigger}', I will execute '{target_action}'."

def get_learned_context_prompt() -> str:
    """Formats all learned rules and corrections for prompt injection."""
    data = _load_corrections()
    rules = data.get("rules", [])
    mappings = data.get("custom_mappings", {})
    
    if not rules and not mappings:
        return ""
        
    lines = ["\n[CONTINUOUS LEARNING & CORRECTIONS RULES]"]
    for r in rules:
        lines.append(f"- {r}")
    for k, v in mappings.items():
        lines.append(f"- Shortcut: When user says '{k}', do '{v}'.")
    lines.append("[END CORRECTIONS RULES]\n")
    return "\n".join(lines)

def detect_and_learn_feedback(user_text: str, last_response: str) -> tuple[bool, str]:
    """Detects user correction intent like 'no that is wrong, do X' and records it."""
    text = user_text.lower()
    
    # Pattern: "when I say X, do Y" / "whenever I say X, do Y"
    m_alias = re.search(r"when(?:ever)?\s+i\s+say\s+['\"]?(.+?)['\"]?\s*,?\s*(?:do|open|run|mean)\s+['\"]?(.+?)['\"]?$", user_text, re.IGNORECASE)
    if m_alias:
        trigger = m_alias.group(1).strip()
        action = m_alias.group(2).strip()
        msg = add_custom_alias(trigger, action)
        return True, msg

    # Pattern: "remember that X" / "learn that X"
    m_rule = re.search(r"^(?:remember|learn|note)\s+that\s+(.+)$", user_text, re.IGNORECASE)
    if m_rule:
        rule = m_rule.group(1).strip()
        msg = add_learned_rule(rule)
        return True, msg

    # Pattern: "that's wrong / incorrect"
    if any(k in text for k in ["that's wrong", "that was wrong", "you made a mistake", "not what i asked", "incorrect"]):
        # Log negative feedback to history
        data = _load_corrections()
        data["history"].append({
            "timestamp": time.time(),
            "user_complaint": user_text,
            "last_response": last_response
        })
        _save_corrections(data)
        return True, "I apologize for the mistake! Could you tell me what you'd like me to do differently so I can learn and remember it?"

    return False, ""
