"""
gaia/gaia_web.py — Headless Multi-Threaded Web Search & Reader for Big Sister GAIA
Allows GAIA to independently search the web, open links, extract text & code snippets,
and read multiple documentation/StackOverflow pages in parallel without a desktop browser.
"""

import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class TextAndCodeExtractor(HTMLParser):
    """Cleanly extracts readable text, headers, and code blocks from HTML, ignoring scripts/styles."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.text_parts = []
        self.code_blocks = []
        self._in_title = False
        self._in_script_or_style = False
        self._in_code = False
        self._current_code = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._in_script_or_style = True
        elif tag_lower == "title":
            self._in_title = True
        elif tag_lower in ("pre", "code"):
            self._in_code = True

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._in_script_or_style = False
        elif tag_lower == "title":
            self._in_title = False
        elif tag_lower in ("pre", "code"):
            self._in_code = False
            joined = "".join(self._current_code).strip()
            if len(joined) > 20 and joined not in self.code_blocks:
                self.code_blocks.append(joined)
            self._current_code = []
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr"):
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self._in_script_or_style:
            return
        if self._in_title:
            self.title += data.strip() + " "
        elif self._in_code:
            self._current_code.append(data)
        else:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned + " ")

    def get_extracted_content(self, max_chars: int = 4000) -> Dict[str, Any]:
        full_text = " ".join("".join(self.text_parts).split())
        return {
            "title": self.title.strip(),
            "text": full_text[:max_chars],
            "code_blocks": self.code_blocks[:5]
        }


class GaiaWebReader:
    """Headless web crawler and search engine designed for Big Sister GAIA's research mind."""

    def __init__(self, timeout: int = 6):
        self.timeout = timeout

    def search_web(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Performs a headless web search using DuckDuckGo HTML and returns external links."""
        url = "https://html.duckduckgo.com/html/"
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        results = []
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            
            # Extract links from DuckDuckGo result anchors
            items = re.findall(
                r'<h2[^>]*>.*?<a[^>]+class="[^"]*result__snippet[^"]*"[^>]+href="([^"]+)".*?>(.*?)</a>',
                content, re.DOTALL | re.IGNORECASE
            )
            if not items:
                items = re.findall(
                    r'<a[^>]+class="[^"]*result__url[^"]*"[^>]+href="([^"]+)".*?>(.*?)</a>',
                    content, re.DOTALL | re.IGNORECASE
                )
            if not items:
                items = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL)

            seen = set()
            for href, raw_text in items:
                # Filter out search engine self-links, ads, video sites
                if any(x in href for x in ["duckduckgo.com", "adclick", "youtube.com", "yandex", "bing.com"]):
                    continue
                if href not in seen and href.startswith("http"):
                    seen.add(href)
                    clean_title = re.sub(r"<[^>]+>", "", raw_text).strip()
                    # Unescape HTML entities
                    clean_title = (
                        clean_title.replace("&quot;", '"')
                        .replace("&amp;", "&")
                        .replace("&#x27;", "'")
                        .replace("&lt;", "<")
                        .replace("&gt;", ">")
                    )
                    results.append({
                        "title": clean_title or "Documentation / Solution",
                        "url": href
                    })
                if len(results) >= max_results:
                    break
        except Exception as e:
            # Fallback direct Python search if rate-limited
            clean_q = re.sub(r"[^\w\s]", "", query).strip()
            results.append({
                "title": f"Documentation lookup for {clean_q}",
                "url": f"https://docs.python.org/3/search.html?q={urllib.parse.quote(clean_q)}"
            })

        return results[:max_results]

    def fetch_and_parse_page(self, url: str) -> Dict[str, Any]:
        """Downloads a web page and extracts clean readable text and code blocks."""
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                # Read at most 500KB to prevent memory bloat
                raw_html = resp.read(500000).decode("utf-8", errors="ignore")
            
            parser = TextAndCodeExtractor()
            parser.feed(raw_html)
            extracted = parser.get_extracted_content()
            extracted["url"] = url
            extracted["success"] = True
            return extracted
        except Exception as e:
            return {
                "url": url,
                "title": "Failed to read",
                "text": f"Could not extract page text: {e}",
                "code_blocks": [],
                "success": False
            }

    def search_and_read_parallel(self, query: str, max_links: int = 4) -> List[Dict[str, Any]]:
        """
        Executes parallel headless search and link reading:
        1. Searches for top relevant links
        2. Spawns concurrent worker threads to read all links simultaneously
        3. Returns combined structured documentation & code snippets in ~1-2s!
        """
        search_results = self.search_web(query, max_results=max_links)
        if not search_results:
            return []

        pages = []
        with ThreadPoolExecutor(max_workers=max_links) as executor:
            future_to_url = {
                executor.submit(self.fetch_and_parse_page, r["url"]): r
                for r in search_results
            }
            for future in as_completed(future_to_url):
                try:
                    data = future.result()
                    orig_info = future_to_url[future]
                    if not data.get("title") or data.get("title") == "Failed to read":
                        data["title"] = orig_info.get("title", "")
                    if data.get("success") and (data.get("text") or data.get("code_blocks")):
                        pages.append(data)
                except Exception:
                    pass

        return pages


web_reader = GaiaWebReader()
