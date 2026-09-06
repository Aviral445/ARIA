"""
tools/gaia_web_research.py — Big Sister GAIA's Parallel Headless Web Reader & Researcher Tool
Allows Aria and the Sibling Trio to query the live web, open links, extract text & code snippets,
and read multiple documentation/StackOverflow pages in parallel without a desktop browser window.

Conforms strictly to Big Sister GAIA's contract rules:
- Complete default parameters
- Zero unhandled exceptions
- Comprehensive docstring
- register_tool() returning ("gaia_web_research", gaia_web_research)
"""

import os
import sys

# Ensure project root is in sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def gaia_web_research(query: str = "python programming best practices", max_pages: int = 3) -> str:
    """Performs parallel headless web research: searches for links, downloads pages simultaneously, and extracts clean text and code blocks.

    Args:
        query (str): The search topic, library question, or error message to research. Default: 'python programming best practices'.
        max_pages (int): Number of top search result pages to read in parallel (1-5). Default: 3.

    Returns:
        str: Summarized research findings with extracted text, code snippets, and page URLs.
    """
    clean_q = (query or "python error").strip()
    limit = max(1, min(int(max_pages or 3), 5))

    try:
        from gaia.gaia_web import web_reader
        pages = web_reader.search_and_read_parallel(clean_q, max_links=limit)

        if not pages:
            return f"🔍 Web Research for '{clean_q}': No accessible web pages found at the moment."

        report = [f"🌐 Big Sister GAIA Parallel Web Research on: '{clean_q}'"]
        report.append(f"• Successfully read {len(pages)} web pages concurrently in parallel!\n")

        for idx, p in enumerate(pages, 1):
            title = p.get("title", "Web Resource")
            url = p.get("url", "")
            text = p.get("text", "").strip()
            codes = p.get("code_blocks", [])

            report.append(f"📄 [{idx}] {title}")
            report.append(f"🔗 URL: {url}")
            if text:
                report.append(f"📖 Key Findings: {text[:350]}...")
            if codes:
                sample_code = codes[0].strip()
                report.append(f"💻 Sample Code:\n```python\n{sample_code[:250]}\n```")
            report.append("-" * 40)

        return "\n".join(report)
    except Exception as e:
        return f"🔍 Web Research Notice: Encountered an issue while researching '{clean_q}': {e}"


def register_tool() -> tuple[str, callable]:
    """Registers gaia_web_research with Aria's live toolkit and ADK engine."""
    return ("gaia_web_research", gaia_web_research)


if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print("Testing tool:", t_name)
    print(t_fn("python error handling best practices", max_pages=2))
