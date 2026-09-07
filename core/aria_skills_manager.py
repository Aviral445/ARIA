"""
core/aria_skills_manager.py — Dynamic Skills Manager for Aria

Decouples procedural capabilities, domain knowledge, and operational rules
from monolithic system instruction strings. Scans the skills/ directory,
caches loaded skills with mtime-based hot-reloading, and formats them
for cognitive prompt injection.
"""

import os
import sys
import threading
from typing import Dict, List, Any, Optional

try:
    from .paths import ROOT_DIR, GUIDELINES_DIR
except ImportError:
    from paths import ROOT_DIR, GUIDELINES_DIR

SKILLS_DIR = GUIDELINES_DIR
_lock = threading.Lock()
_CACHED_SKILLS: Dict[str, Dict[str, Any]] = {}


def get_skills_dir() -> str:
    """Returns absolute path to the skills directory (docs/guidelines with fallback to skills/)."""
    if os.path.exists(GUIDELINES_DIR):
        return GUIDELINES_DIR
    legacy_dir = os.path.join(ROOT_DIR, "skills")
    if os.path.exists(legacy_dir):
        return legacy_dir
    os.makedirs(GUIDELINES_DIR, exist_ok=True)
    return GUIDELINES_DIR


def list_skills() -> List[Dict[str, Any]]:
    """Lists all available modular skill files."""
    s_dir = get_skills_dir()
    skills = []
    try:
        for fname in sorted(os.listdir(s_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(s_dir, fname)
                skills.append({
                    "name": os.path.splitext(fname)[0],
                    "filename": fname,
                    "path": fpath,
                    "mtime": os.path.getmtime(fpath) if os.path.exists(fpath) else 0
                })
    except Exception as e:
        print(f"[SkillsManager Notice] Error listing skills: {e}")
    return skills


def load_skill(skill_name: str) -> Optional[str]:
    """Loads a single skill by name (with hot-reload mtime check)."""
    s_dir = get_skills_dir()
    filename = f"{skill_name}.md" if not skill_name.endswith(".md") else skill_name
    fpath = os.path.join(s_dir, filename)
    if not os.path.exists(fpath):
        return None

    try:
        current_mtime = os.path.getmtime(fpath)
        with _lock:
            cached = _CACHED_SKILLS.get(skill_name)
            if cached and cached.get("mtime") == current_mtime:
                return cached.get("content")

            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                _CACHED_SKILLS[skill_name] = {
                    "mtime": current_mtime,
                    "content": content
                }
                return content
    except Exception as e:
        print(f"[SkillsManager Notice] Error reading skill '{skill_name}': {e}")
        return None


def get_all_skills_prompt(priority_skills: Optional[List[str]] = None) -> str:
    """
    Gathers, hot-reloads, and formats all modular skills into a single prompt block.
    Default ordering places safety and grounding first, followed by domain skills.
    """
    s_dir = get_skills_dir()
    if not os.path.exists(s_dir):
        return ""

    preferred_order = priority_skills or [
        "anti_acting_rules",
        "polyglot_coding",
        "file_structuring",
        "web_development"
    ]

    all_files = [os.path.splitext(f)[0] for f in os.listdir(s_dir) if f.endswith(".md")]
    ordered_names = [name for name in preferred_order if name in all_files]
    for name in sorted(all_files):
        if name not in ordered_names:
            ordered_names.append(name)

    sections = []
    for name in ordered_names:
        content = load_skill(name)
        if content:
            sections.append(content)

    if not sections:
        return ""

    return "\n\n" + "\n\n".join(sections) + "\n"


def save_skill(skill_name: str, content: str) -> bool:
    """Safely saves or updates a modular skill file on disk."""
    s_dir = get_skills_dir()
    filename = f"{skill_name}.md" if not skill_name.endswith(".md") else skill_name
    fpath = os.path.join(s_dir, filename)
    try:
        with _lock:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            _CACHED_SKILLS[skill_name] = {
                "mtime": os.path.getmtime(fpath),
                "content": content.strip()
            }
        return True
    except Exception as e:
        print(f"[SkillsManager Notice] Error saving skill '{skill_name}': {e}")
        return False
