import os
import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), 'mood_log.txt')

def track_mood(mood: str) -> str:
    """Append the given mood with timestamp to the log and return a song suggestion.
    Simple keyword matching: if 'sad' -> upbeat song, if 'happy' -> chill song, else generic.
    """
    timestamp = datetime.datetime.now().isoformat(timespec='seconds')
    entry = f"{timestamp}: {mood}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception as e:
        return f"Error writing mood log: {e}"

    mood_lower = mood.lower()
    if 'sad' in mood_lower:
        suggestion = 'Try listening to "Happy" by Pharrell Williams!'
    elif 'happy' in mood_lower:
        suggestion = 'How about some chill vibes? Check out "Sunflower" by Post Malone.'
    elif 'angry' in mood_lower:
        suggestion = 'Maybe a calming track like "Weightless" by Marconi Union helps.'
    else:
        suggestion = 'A great tune for any mood: "Shape of You" by Ed Sheeran.'
    return suggestion

def register_tool() -> tuple[str, callable]:
    """Registers mood_tracker_tool with Aria ADK."""
    return "mood_tracker_tool", track_mood
