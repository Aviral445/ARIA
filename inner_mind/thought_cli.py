"""
inner_mind/thought_cli.py — Command-Line Inspector for Aria's Inner Mind & GAIA Analysis

Usage:
  python inner_mind/thought_cli.py --last 5
  python inner_mind/thought_cli.py --filter curious
  python inner_mind/thought_cli.py --filter bad
  python inner_mind/thought_cli.py --stats
  python inner_mind/thought_cli.py --diary
"""

import os
import sys
import argparse
import json

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Ensure project root is in sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


from inner_mind.thought_recorder import (
    get_recent_thoughts,
    get_inner_mind_stats,
    THOUGHTS_JSONL,
    DIARY_MD
)


def format_thought_card(t: dict) -> str:
    analysis = t.get("analysis", {})
    ptype = analysis.get("primary_type", "unknown").upper()
    emotions = ", ".join(analysis.get("emotions", []))
    color_map = {
        "GOOD": "\033[92m",       # Green
        "BAD": "\033[91m",        # Red
        "FUN": "\033[95m",        # Magenta
        "CURIOUS": "\033[96m",    # Cyan
        "DETERMINED": "\033[93m", # Yellow
        "CONFUSED": "\033[94m",   # Blue
    }
    reset = "\033[0m"
    color = color_map.get(ptype, "")

    lines = [
        f"{color}─────────────────────────────────────────────────────────────────────────────{reset}",
        f"💭 [{t.get('timestamp')}] Brain: {t.get('active_brain')} ({t.get('active_model')})",
        f"🏷️  Category: {color}**{ptype}**{reset} | Feelings: [{emotions}]",
        f"👤 User: \"{t.get('user_input')}\"",
        f"🧠 Raw Inner Monologue:",
    ]
    for tl in t.get("raw_thought", "").splitlines()[:6]:
        lines.append(f"   > {tl}")
    if len(t.get("raw_thought", "").splitlines()) > 6:
        lines.append("   > [...]")
    
    if t.get("tools_called"):
        lines.append(f"🛠️  Tools Called: {', '.join(t.get('tools_called'))}")
    if analysis.get("curiosity_topics"):
        lines.append(f"🔍 Curiosities: {', '.join(analysis.get('curiosity_topics'))}")

    lines.append(f"🗣️  Aria Spoke: \"{t.get('final_reply')}\"")
    lines.append(f"👩‍🏫 GAIA Commentary: {analysis.get('sisterly_commentary')}")
    lines.append(f"{color}─────────────────────────────────────────────────────────────────────────────{reset}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Aria's Inner Mind & GAIA Cognitive Inspector")
    parser.add_argument("--last", type=int, default=5, help="Number of recent thoughts to view (default: 5)")
    parser.add_argument("--filter", type=str, choices=["good", "bad", "fun", "curious", "determined", "confused"], help="Filter thoughts by GAIA's label")
    parser.add_argument("--stats", action="store_true", help="Display aggregate cognitive stats")
    parser.add_argument("--diary", action="store_true", help="Show path to diary or view recent markdown")

    args = parser.parse_args()

    if args.stats:
        stats = get_inner_mind_stats()
        print("\n🧠 ARIA INNER MIND TELEMETRY & STATS:")
        print(f"• Total Thoughts Logged : {stats.get('total_thoughts', 0)}")
        print(f"• Last Thought Recorded : {stats.get('last_updated', 'None')}")
        print("\n📊 Breakdown by Emotional / Thought Type:")
        for t, count in stats.get("counts_by_type", {}).items():
            print(f"  - {t.capitalize():<12}: {count}")
        print("\n🔍 Recent Curiosities Sparked:")
        for c in stats.get("curiosity_topics", [])[-8:]:
            print(f"  • {c}")
        print()
        return

    if args.diary:
        print(f"\n📖 Aria's Secret Diary is located at:\n   {DIARY_MD}\n")
        if os.path.exists(DIARY_MD):
            with open(DIARY_MD, "r", encoding="utf-8") as f:
                content = f.read()
            print("--- Recent Diary Excerpt ---")
            lines = content.splitlines()
            print("\n".join(lines[-40:]))
        return

    thoughts = get_recent_thoughts(limit=args.last, filter_type=args.filter)
    if not thoughts:
        filter_msg = f" of type '{args.filter}'" if args.filter else ""
        print(f"\nNo inner thoughts found{filter_msg}. Start a conversation with Aria to record thoughts!\n")
        return

    print(f"\n🧠 ARIA'S RECENT INNER THOUGHTS (Showing {len(thoughts)} entries):\n")
    for t in thoughts:
        print(format_thought_card(t))
        print()


if __name__ == "__main__":
    main()
