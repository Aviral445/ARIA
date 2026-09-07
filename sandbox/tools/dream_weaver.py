import re

def dream_weaver(raw_ideas: str) -> str:
    """Take a jumbled string of ideas and return a clean, numbered list.
    Splits on common separators like commas, semicolons, newlines, and bullet symbols.
    Preserves hyphenated words like 'spider-man' and 'state-of-the-art'.
    Removes empty entries and trims whitespace.
    """
    if not raw_ideas or not raw_ideas.strip():
        return "No ideas provided to weave!"

    # Split on newlines, commas, semicolons, or bullet points (with surrounding whitespace)
    # Notice: a hyphen inside a word like 'spider-man' is preserved because it lacks surrounding whitespace
    parts = re.split(r"(?:\r?\n|[,;]|\s+[\*\-•]\s*|^\s*[\*\-•]\s*)+", raw_ideas.strip())
    cleaned = [p.strip() for p in parts if p.strip()]
    if not cleaned:
        return "No distinct ideas found to weave."

    return "\n".join(f"{i+1}. {item}" for i, item in enumerate(cleaned))

def register_tool() -> tuple[str, callable]:
    """Registers dream_weaver with Aria ADK."""
    return "dream_weaver", dream_weaver
