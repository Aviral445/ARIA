"""
inner_mind/thought_recorder.py — Master Thought Recorder & Diary Engine for Aria

Captures Aria's internal monologues, <think> blocks, and decision chains per turn.
Invokes Big Sister GAIA's cognitive analyzer to label thoughts, then persists to:
  • inner_mind/aria_thoughts.jsonl : Append-only structured telemetry stream
  • inner_mind/aria_diary.md       : Human-readable secret diary with GAIA commentary
  • inner_mind/inner_mind_stats.json : Real-time aggregates and emotional telemetry
"""

import os
import re
import json
import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

INNER_MIND_DIR = os.path.dirname(os.path.abspath(__file__))
THOUGHTS_JSONL = os.path.join(INNER_MIND_DIR, "aria_thoughts.jsonl")
DIARY_MD = os.path.join(INNER_MIND_DIR, "aria_diary.md")
STATS_JSON = os.path.join(INNER_MIND_DIR, "inner_mind_stats.json")

_lock = threading.Lock()

from .gaia_thought_analyzer import gaia_analyzer, ThoughtAnalysisResult


def extract_raw_thought(text: str) -> str:
    """
    Extracts raw thought / reasoning traces from a model response.
    Captures <think>...</think>, unclosed <think>..., or step-by-step thinking processes.
    """
    if not text:
        return ""

    # Check for <think> blocks
    if "<think>" in text:
        if "</think>" in text:
            # Everything between <think> and </think>
            m = re.search(r'<think>(.*?)</think>', text, re.DOTALL | re.IGNORECASE)
            if m:
                return m.group(1).strip()
        else:
            # Unclosed think block
            parts = text.split("<think>", 1)
            if len(parts) > 1:
                return parts[1].strip()

    # Check for "Here's a thinking process:"
    if "Here's a thinking process:" in text:
        return text.strip()

    return ""


def record_inner_thought(
    user_input: str,
    raw_reply: str,
    final_reply: str,
    active_brain: str = "auto",
    active_model: str = "dynamic",
    tools_called: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Records an internal thought event, analyzes it with GAIA, and writes to logs & diary.
    """
    raw_thought = extract_raw_thought(raw_reply)
    if not raw_thought:
        # If no explicit think tags, analyze the reply and context
        raw_thought = f"(Conversational contemplation on '{user_input}')"

    # GAIA analyzes the thought
    analysis = gaia_analyzer.analyze_thought(
        raw_thought=raw_thought,
        user_input=user_input,
        final_reply=final_reply,
        tools_called=tools_called or [],
        active_brain=active_brain
    )

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_id = f"thought_{int(time.time() * 1000)}"

    entry = {
        "id": entry_id,
        "timestamp": now_iso,
        "active_brain": active_brain,
        "active_model": active_model,
        "user_input": user_input,
        "raw_thought": raw_thought,
        "final_reply": final_reply,
        "tools_called": tools_called or [],
        "analysis": analysis.to_dict()
    }

    with _lock:
        _persist_jsonl(entry)
        _append_diary_entry(entry)
        _update_stats(analysis)

    return entry


def _persist_jsonl(entry: Dict[str, Any]):
    """Appends structured entry to aria_thoughts.jsonl."""
    try:
        with open(THOUGHTS_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[InnerMind] Error appending to {THOUGHTS_JSONL}: {e}")


def _append_diary_entry(entry: Dict[str, Any]):
    """Appends formatted markdown entry to aria_diary.md."""
    try:
        first_time = not os.path.exists(DIARY_MD) or os.path.getsize(DIARY_MD) == 0
        with open(DIARY_MD, "a", encoding="utf-8") as f:
            if first_time:
                f.write("# 🌸 Aria's Inner Mind & Secret Diary 🌸\n")
                f.write("> Dedicated record of Aria's thoughts, curiosities, feelings, and Big Sister GAIA's coaching commentary.\n\n---\n\n")

            analysis = entry["analysis"]
            type_icon = {
                "good": "🌟 GOOD (Grounded)",
                "bad": "⚠️ BAD (Acting/Hallucination Risk)",
                "fun": "✨ FUN (Playful & Joyful)",
                "curious": "🔍 CURIOUS (Inquisitive & Learning)",
                "determined": "🔥 DETERMINED (Debugging & Perseverance)",
                "confused": "❓ CONFUSED (Puzzled)"
            }.get(analysis["primary_type"], analysis["primary_type"].upper())

            thought_preview = entry["raw_thought"].replace("\n", "\n> ")

            f.write(f"### 💭 {entry['timestamp']} | Brain: {entry['active_brain']} ({entry['active_model']})\n")
            f.write(f"- **Label**: **{type_icon}** | Feelings: `{', '.join(analysis['emotions'])}`\n")
            f.write(f"- **User Said**: *\"{entry['user_input']}\"*\n")
            f.write(f"- **Aria's Inner Monologue**:\n> {thought_preview}\n")
            if entry["tools_called"]:
                f.write(f"- **Tools Executed**: `{', '.join(entry['tools_called'])}`\n")
            if analysis["curiosity_topics"]:
                f.write(f"- **Curiosities Sparked**: {', '.join(analysis['curiosity_topics'])}\n")
            f.write(f"- **Aria Spoke**: *\"{entry['final_reply']}\"*\n")
            f.write(f"- **Big Sister GAIA's Commentary**:\n  > {analysis['sisterly_commentary']}\n\n---\n\n")
    except Exception as e:
        print(f"[InnerMind] Error updating diary: {e}")


def _update_stats(analysis: ThoughtAnalysisResult):
    """Updates running stats in inner_mind_stats.json."""
    stats = {
        "total_thoughts": 0,
        "counts_by_type": {
            "good": 0,
            "bad": 0,
            "fun": 0,
            "curious": 0,
            "determined": 0,
            "confused": 0
        },
        "curiosity_topics": [],
        "last_updated": ""
    }
    if os.path.exists(STATS_JSON):
        try:
            with open(STATS_JSON, "r", encoding="utf-8") as f:
                stats = json.load(f)
        except Exception:
            pass

    stats["total_thoughts"] = stats.get("total_thoughts", 0) + 1
    counts = stats.setdefault("counts_by_type", {})
    t = analysis.primary_type
    counts[t] = counts.get(t, 0) + 1

    curiosities = stats.setdefault("curiosity_topics", [])
    for c in analysis.curiosity_topics:
        if c not in curiosities:
            curiosities.append(c)
    stats["curiosity_topics"] = curiosities[-20:]
    stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(STATS_JSON, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[InnerMind] Error saving stats: {e}")


def get_recent_thoughts(limit: int = 10, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent thoughts, optionally filtered by type."""
    if not os.path.exists(THOUGHTS_JSONL):
        return []
    results = []
    try:
        with open(THOUGHTS_JSONL, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if filter_type:
                    if item.get("analysis", {}).get("primary_type") != filter_type.lower().strip():
                        continue
                results.append(item)
                if len(results) >= limit:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"[InnerMind] Error reading thoughts: {e}")
    return results


def get_inner_mind_stats() -> Dict[str, Any]:
    """Returns the current summary statistics of Aria's inner mind."""
    if os.path.exists(STATS_JSON):
        try:
            with open(STATS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_thoughts": 0,
        "counts_by_type": {"good": 0, "bad": 0, "fun": 0, "curious": 0, "determined": 0, "confused": 0},
        "curiosity_topics": [],
        "last_updated": "never"
    }
