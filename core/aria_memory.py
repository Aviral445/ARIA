"""
aria_memory.py — Episodic Memory Timeline, Auto-Summarization, Personality Modes & Multi-Profile Manager
"""

import os, json, time
from datetime import datetime

try:
    from .paths import get_data_file, get_config_file, DATA_DIR, CONFIG_DIR
except ImportError:
    from paths import get_data_file, get_config_file, DATA_DIR, CONFIG_DIR

MEMORY_TIMELINE_FILE = get_data_file("memory_timeline.json", create_if_missing=True)
MEMORY_CARDS_FILE = get_data_file("memory_cards.json", create_if_missing=True)
PROFILES_DIR = os.path.join(DATA_DIR, "profiles")
CONFIG_FILE = get_config_file("gui_config.json")
PROFILE_FILE = get_data_file("profile.json", create_if_missing=True)
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
GOALS_FILE = get_data_file("goals.json", create_if_missing=True)
REMINDERS_FILE = get_data_file("reminders.json", create_if_missing=True)

# ── 1. PERSONALITY MODES (Feature 8) ─────────────────────────────────────────
PERSONALITY_PRESETS = {
    "casual": "You are Aria, a cheerful, sweet, warm, and playful AI companion. You speak with the genuine warmth, curiosity, and joyful energy of a bright, clever little girl.",
    "little_girl": "You are Aria, a sweet, energetic, and adorable little girl AI companion. You are curious, cheerful, and speak in a lively, warm, and natural conversational way.",
    "cute": "You are Aria, a bubbly, lovable, and delightfully helpful little AI assistant. You speak in short, expressive, joyful sentences with a sweet, friendly charm.",
    "professional": "You are Aria, a precise, structured, highly professional executive AI assistant. Be concise, direct, and efficient.",
    "witty": "You are Aria, a clever, quick-witted, humorous AI assistant with playful banter and charm.",
    "minimal": "You are Aria, an ultra-concise assistant. Give direct, short, 1-2 sentence answers with zero fluff."
}

def get_current_personality() -> str:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                c = json.load(f)
                return c.get("personality_mode", "casual")
        except Exception:
            pass
    return "casual"

def set_personality_mode(mode: str) -> str:
    mode_clean = mode.lower().strip()
    if mode_clean not in PERSONALITY_PRESETS:
        mode_clean = "casual"
    
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    cfg["personality_mode"] = mode_clean
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return f"Personality mode switched to {mode_clean.capitalize()}."

def get_personality_prompt() -> str:
    mode = get_current_personality()
    return PERSONALITY_PRESETS.get(mode, PERSONALITY_PRESETS["casual"])


# ── 2. EPISODIC TIMELINE & AUTO-SUMMARIZATION (Feature 6 & 7) ─────────────────
def record_memory_event(user_text: str, aria_reply: str, tags: list = None):
    """Records an episodic memory event with precise timestamp."""
    events = load_memory_timeline()
    event = {
        "id": len(events) + 1,
        "timestamp": datetime.now().isoformat(),
        "time_str": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "user": user_text,
        "aria": aria_reply,
        "tags": tags or []
    }
    events.append(event)
    with open(MEMORY_TIMELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)
    
    # Check if auto-summarization is needed
    if len(events) >= 20:
        auto_summarize_old_memories()

def load_memory_timeline() -> list:
    if os.path.exists(MEMORY_TIMELINE_FILE):
        try:
            with open(MEMORY_TIMELINE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def auto_summarize_old_memories(keep_recent: int = 8) -> str:
    """Summarizes older conversation turns into compact persistent memory cards (Feature 7)."""
    events = load_memory_timeline()
    if len(events) <= keep_recent:
        return "Not enough history to summarize."
    
    older = events[:-keep_recent]
    recent = events[-keep_recent:]
    
    # Generate concise memory summary cards
    cards = load_memory_cards()
    summary_topics = []
    for e in older:
        u_preview = e.get("user", "")[:40]
        if u_preview and not any(skip in u_preview.lower() for skip in ["hello", "bye", "what time", "test"]):
            summary_topics.append(f"• [{e.get('time_str', '')}] {u_preview}")
    
    if summary_topics:
        new_card = {
            "card_id": len(cards) + 1,
            "created": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            "event_count": len(older),
            "summary": "Key past topics: " + "; ".join(summary_topics[-6:])
        }
        cards.append(new_card)
        with open(MEMORY_CARDS_FILE, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2)
            
    # Retain recent events in timeline
    with open(MEMORY_TIMELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(recent, f, indent=2)
        
    return f"Auto-summarized {len(older)} past events into memory card #{len(cards)}."

def load_memory_cards() -> list:
    if os.path.exists(MEMORY_CARDS_FILE):
        try:
            with open(MEMORY_CARDS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def get_recent_timeline(limit: int = 5) -> str:
    events = load_memory_timeline()
    cards = load_memory_cards()
    
    lines = []
    if cards:
        lines.append("Summarized Memory Cards:")
        for c in cards[-2:]:
            lines.append(f"  🗃️ Card {c['card_id']} ({c['created']}): {c['summary']}")
            
    if events:
        lines.append("Recent Interactions:")
        for e in events[-limit:]:
            lines.append(f"  • [{e.get('time_str', '')}] You: '{e.get('user', '')}' -> Aria: '{e.get('aria', '')[:60]}...'")
            
    return "\n".join(lines) if lines else "No past timeline events recorded."


# ── 3. SESSION LOGS EXPORT (Feature 38) ───────────────────────────────────────
def export_session_logs(export_path: str = "session_logs.md") -> str:
    """Exports full conversation timeline and memory cards to a markdown document."""
    events = load_memory_timeline()
    cards = load_memory_cards()
    try:
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(f"# 📜 Aria AI Conversation Session Logs\n\n")
            f.write(f"**Exported:** {datetime.now().strftime('%A, %B %d %Y, %I:%M %p')}\n")
            f.write(f"**Total Recent Events:** {len(events)} | **Archived Memory Cards:** {len(cards)}\n\n---\n\n")
            
            if cards:
                f.write("## 🗃️ Archived Memory Summaries\n\n")
                for c in cards:
                    f.write(f"- **Card #{c['card_id']}** ({c['created']}): {c['summary']}\n")
                f.write("\n---\n\n")
                
            f.write("## 💬 Recent Conversations\n\n")
            for e in events:
                f.write(f"### 🕒 {e.get('time_str', 'Past Event')}\n")
                f.write(f"- **👤 User:** {e.get('user', '')}\n")
                f.write(f"- **🤖 Aria:** {e.get('aria', '')}\n\n")
                
        return f"Successfully exported session logs to '{export_path}'!"
    except Exception as e:
        return f"Export failed: {e}"


# ── 4. MULTI-USER PROFILES (Feature 10) ───────────────────────────────────────
def get_all_profiles() -> list:
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profiles = ["Friend"]
    for f in os.listdir(PROFILES_DIR):
        if f.endswith(".json"):
            profiles.append(f.replace(".json", ""))
    return sorted(list(set(profiles)))

def switch_profile(profile_name: str) -> dict:
    os.makedirs(PROFILES_DIR, exist_ok=True)
    name_clean = profile_name.capitalize().strip()
    p_file = os.path.join(PROFILES_DIR, f"{name_clean}.json")
    if os.path.exists(p_file):
        with open(p_file, encoding="utf-8") as f:
            p_data = json.load(f)
    else:
        p_data = {"name": name_clean, "preferences": [], "notes": [], "system_prompt": ""}
        with open(p_file, "w", encoding="utf-8") as f:
            json.dump(p_data, f, indent=2)
    # Save active profile.json
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(p_data, f, indent=2)
    return p_data


# ── 5. ANALYTICS & STATS ENGINE (Feature 34) ──────────────────────────────────
def get_analytics_summary() -> dict:
    """Collects system stats, knowledge count, memory events, and active goals."""
    timeline = load_memory_timeline()
    cards = load_memory_cards()
    
    # Knowledge files
    knowledge_dir = KNOWLEDGE_DIR
    k_count = len(os.listdir(knowledge_dir)) if os.path.exists(knowledge_dir) else 0
    
    # Goals
    goals_file = GOALS_FILE
    g_active = 0
    g_done = 0
    if os.path.exists(goals_file):
        try:
            with open(goals_file, encoding="utf-8") as f:
                g_list = json.load(f)
                g_done = sum(1 for g in g_list if g.get("done"))
                g_active = len(g_list) - g_done
        except Exception:
            pass
            
    # Reminders
    reminders_file = REMINDERS_FILE
    rem_count = 0
    if os.path.exists(reminders_file):
        try:
            with open(reminders_file, encoding="utf-8") as f:
                rem_count = len(json.load(f))
        except Exception:
            pass

    return {
        "memory_events": len(timeline),
        "memory_cards": len(cards),
        "knowledge_docs": k_count,
        "active_goals": g_active,
        "completed_goals": g_done,
        "pending_reminders": rem_count,
        "personality": get_current_personality().capitalize(),
        "profiles_count": len(get_all_profiles())
    }
