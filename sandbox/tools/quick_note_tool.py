"""
Dynamic Sandbox Tool: quick_note_tool
Created autonomously by Aria in the lab with GAIA.
Rigged into Aria's ADK toolset so she can capture quick notes and reminders.
"""
import os
import datetime

def get_notes_folder() -> str:
    """Returns the dedicated folder where Aria saves her quick notes."""
    try:
        from core.paths import DATA_DIR
        primary = os.path.join(DATA_DIR, "notes")
    except Exception:
        primary = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "notes")

    candidates = [
        primary,
        r"E:\MyAgent\notes",
        os.path.join(os.getcwd(), "data", "notes"),
        os.path.join(os.getcwd(), "sandbox_notes")
    ]
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            return d
        except Exception:
            continue
    fallback = os.path.join(os.getcwd(), "sandbox_notes")
    os.makedirs(fallback, exist_ok=True)
    return fallback

def quick_note_tool(note: str = "", action: str = "save") -> str:
    """
    Saves or reads quick thoughts, reminders, or notes for the user or Aria with automatic timestamps.
    Args:
        note: Text of the note to save. If set to 'list' or 'read', lists recent notes.
        action: 'save' to record a new note, or 'read' / 'list' to view recent notes.
    """
    folder = get_notes_folder()

    # Read / list notes
    if action.lower() in ("read", "list", "show") or (note and note.strip().lower() in ("list", "read", "show notes", "list notes", "all")):
        if not os.path.exists(folder):
            return "No notes found yet."
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.startswith("note_") and f.endswith(".txt")]
        if not files:
            return "No notes found yet in your notebook."
        files.sort(key=os.path.getmtime, reverse=True)
        entries = []
        for fp in files[:5]:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    entries.append(f.read().strip())
            except Exception:
                pass
        return "📓 Recent Notes:\n" + "\n---\n".join(entries)

    # Save note
    if not note or not note.strip():
        return "Please provide text for the note to save."

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"note_{timestamp}.txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}] {note.strip()}\n")

    return f"📝 Saved note to {path}: '{note.strip()}'"

def register_tool():
    """Registers quick_note_tool with Aria's lab and ADK engine."""
    return "quick_note_tool", quick_note_tool

if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print(t_fn("Testing Aria's integrated quick note tool!"))
    print(t_fn(action="list"))
