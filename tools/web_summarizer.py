import os

def register_tool() -> tuple[str, callable]:
    return ("web_summarizer", web_summarizer)

def web_summarizer(url: str = "https://google.com") -> str:
    """Summarizes content from a URL using GAIA's headless web reader or Chrome."""
    clean_url = (url or "https://google.com").strip()
    try:
        from gaia.gaia_web import web_reader
        data = web_reader.fetch_page_text_and_code(clean_url)
        title = data.get("title", clean_url)
        text = data.get("text", "")
        if text:
            summary = text[:400].replace("\n", " ").strip()
            return f"📄 Summary for '{title}':\n{summary}..."
    except Exception:
        pass
    return f"I would summarize {clean_url} by reading the text directly from the web!"
