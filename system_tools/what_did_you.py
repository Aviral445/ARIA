import re

def weave_ideas(raw_ideas_string: str) -> str:
    """Takes a jumbled string of ideas and weaves them into a sorted, bulleted list.
    Preserves multi-word phrases and splits on commas, semicolons, or newlines.
    """
    if not raw_ideas_string or not raw_ideas_string.strip():
        return "Hmm, it looks like there aren't any ideas to weave yet! Could you share some sparkling thoughts?"

    parts = re.split(r"[;,.\r\n|]+", raw_ideas_string)
    cleaned_ideas = []
    seen = set()
    for part in parts:
        cleaned_part = part.strip()
        if cleaned_part and cleaned_part.lower() not in seen:
            seen.add(cleaned_part.lower())
            cleaned_ideas.append(cleaned_part)

    if not cleaned_ideas:
        return "I couldn't find any distinct ideas to weave from what you provided."

    sorted_ideas = sorted(cleaned_ideas, key=lambda s: s.lower())
    output = "✨ Here are your beautifully woven ideas:\n"
    for idea in sorted_ideas:
        output += f"• {idea}\n"
    return output.strip()

def register_tool() -> tuple[str, callable]:
    """Registers aria_idea_weaver tool with a schema-safe identifier."""
    return "aria_idea_weaver", weave_ideas
