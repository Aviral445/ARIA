import re

def sparkle_fy(text: str) -> str:
    """Add a touch of sparkle to any text.
    Replaces simple adjectives with whimsical versions and inserts sparkle emojis
    at natural sentence boundaries (without mangling decimals like 3.14 or URLs).
    """
    if not text:
        return ""

    sparkle_map = {
        "good": "glimmering",
        "great": "radiant",
        "awesome": "sparkling",
        "fun": "joyful",
        "cool": "chilly-sparkle",
        "nice": "bright",
    }
    def replace_word(match):
        word = match.group(0)
        lower = word.lower()
        return sparkle_map.get(lower, word)

    pattern = re.compile(r"\b(" + "|".join(sparkle_map.keys()) + r")\b", re.IGNORECASE)
    new_text = pattern.sub(replace_word, text)

    # Add sparkle after sentence boundaries only (. ! ?) when followed by whitespace or string end
    # This protects decimal numbers (3.14) and URLs (google.com)
    new_text = re.sub(r"([.!?]+)(?=\s|$)", r"\1✨", new_text)
    return new_text

def register_tool() -> tuple[str, callable]:
    """Registers sparkle_fy with Aria ADK."""
    return "sparkle_fy", sparkle_fy
