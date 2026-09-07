"""
aria_chrome.py — Chrome Browser Automation Agent for Aria
Gives Aria the ability to operate Google Chrome:
  • Navigate to URLs
  • Search Google
  • Read page content / summarize pages
  • Click elements by text or CSS selector
  • Type into inputs
  • Scroll pages
  • Manage tabs (open, close, switch, list)
  • Take screenshots (for Gemini Vision)

Uses Selenium + webdriver-manager (auto-downloads correct ChromeDriver).
"""

import os
import time
import re
import threading
from typing import Optional

# ── Selenium imports ───────────────────────────────────────────────────────────
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException, TimeoutException,
        WebDriverException, StaleElementReferenceException
    )
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False


# ── Config ─────────────────────────────────────────────────────────────────────
CHROME_CONFIG = {
    # Use your existing Chrome profile so you stay logged in everywhere
    # Set to None to use a fresh throwaway profile
    "use_existing_profile": True,

    # Path to your Chrome user data dir (leave blank to auto-detect)
    "profile_dir": "",

    # Which Chrome profile name to use (usually "Default")
    "profile_name": "Default",

    # Max seconds to wait for elements to appear
    "wait_timeout": 10,

    # Max chars of page text to return (for prompt safety)
    "max_page_chars": 3000,

    # Whether Chrome window is visible (False = headless/hidden)
    "headless": False,
}


def _detect_chrome_profile_dir() -> str:
    """Auto-detect the Chrome user data directory on Windows."""
    username = os.environ.get("USERNAME", "User")
    candidates = [
        rf"C:\Users\{username}\AppData\Local\Google\Chrome\User Data",
        rf"C:\Users\{username}\AppData\Local\Chromium\User Data",
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return ""


class ChromeAgent:
    """
    Selenium-based Chrome controller for Aria.
    Maintains a single browser session across calls.
    """

    def __init__(self, config: dict | None = None):
        self.config = dict(CHROME_CONFIG)
        if config:
            self.config.update(config)
        self._driver: Optional[webdriver.Chrome] = None
        self._lock = threading.Lock()

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def _get_driver(self) -> webdriver.Chrome:
        """Return running driver or start a new Chrome session."""
        if self._driver:
            try:
                # Quick check if browser is still alive
                _ = self._driver.current_url
                return self._driver
            except WebDriverException:
                self._driver = None

        if not HAS_SELENIUM:
            raise RuntimeError("selenium is not installed. Run: pip install selenium")
        if not HAS_WDM:
            raise RuntimeError("webdriver-manager not installed. Run: pip install webdriver-manager")

        opts = Options()

        if self.config.get("headless", False):
            opts.add_argument("--headless=new")

        # Use isolated dedicated Aria Chrome profile so it never conflicts with user's open Chrome
        profile_dir = os.path.expandvars(r"%LOCALAPPDATA%\Aria\ChromeProfile")
        os.makedirs(profile_dir, exist_ok=True)
        opts.add_argument(f"--user-data-dir={profile_dir}")

        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        try:
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=opts)
            self._driver.maximize_window()
            return self._driver
        except Exception as e_driver:
            # Fallback to direct Chrome executable
            try:
                self._driver = webdriver.Chrome(options=opts)
                self._driver.maximize_window()
                return self._driver
            except Exception:
                raise e_driver


    def close(self):
        """Close the browser session."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    def is_open(self) -> bool:
        """Check if browser is currently running."""
        if not self._driver:
            return False
        try:
            _ = self._driver.current_url
            return True
        except Exception:
            return False

    # ── Navigation ─────────────────────────────────────────────────────────────

    def open_url(self, url: str) -> str:
        """Navigate to a URL. Auto-adds https:// if missing."""
        with self._lock:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            driver = self._get_driver()
            driver.get(url)
            time.sleep(1.5)
            title = driver.title or url
            return f"Opened: {title} ({driver.current_url})"

    def search_google(self, query: str) -> str:
        """
        Search Google and return a text summary of the top results
        (extracted directly from the search result page).
        """
        with self._lock:
            driver = self._get_driver()
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            driver.get(search_url)
            time.sleep(2)

            # Extract result snippets
            snippets = []
            try:
                # Google result blocks
                result_divs = driver.find_elements(By.CSS_SELECTOR, "div.BNeawe, div.VwiC3b, span.aCOpRe")
                for el in result_divs[:8]:
                    txt = el.text.strip()
                    if txt and len(txt) > 20:
                        snippets.append(txt)
            except Exception:
                pass

            # Fallback: get full page text
            if not snippets:
                body = driver.find_element(By.TAG_NAME, "body")
                raw = body.text[:2000]
                return f"Google search for '{query}':\n{raw}"

            result_text = "\n\n".join(snippets[:6])
            return f"Google search results for '{query}':\n\n{result_text}"

    # ── Page Reading ───────────────────────────────────────────────────────────

    def read_page(self) -> str:
        """
        Extract and return readable text content from the current page.
        Removes nav/footer noise, focuses on main content.
        """
        with self._lock:
            driver = self._get_driver()
            url   = driver.current_url
            title = driver.title

            # Try to grab main content area first
            text = ""
            for selector in ["main", "article", "#content", ".content",
                              "#main-content", ".post-content", "body"]:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, selector)
                    text = el.text.strip()
                    if len(text) > 200:
                        break
                except NoSuchElementException:
                    continue

            if not text:
                text = driver.find_element(By.TAG_NAME, "body").text.strip()

            # Clean up excess whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            limit = self.config.get("max_page_chars", 3000)
            if len(text) > limit:
                text = text[:limit] + f"\n\n... [page truncated at {limit} chars]"

            return f"Page: {title}\nURL: {url}\n\n{text}"

    def get_current_url(self) -> str:
        """Return the current tab's URL."""
        try:
            return self._get_driver().current_url
        except Exception:
            return "no page open"

    def get_page_title(self) -> str:
        """Return the current tab's title."""
        try:
            return self._get_driver().title
        except Exception:
            return "unknown"

    def summarize_page(self) -> str:
        """Read the current page and return its text (for AI to summarize)."""
        return self.read_page()

    # ── Interaction ────────────────────────────────────────────────────────────

    def click_element(self, text_or_selector: str) -> str:
        """
        Click an element by:
        1. Visible link/button text (most natural)
        2. CSS selector
        3. XPath
        """
        with self._lock:
            driver = self._get_driver()
            wait = WebDriverWait(driver, self.config.get("wait_timeout", 10))

            # 1. Try by link text
            try:
                el = wait.until(EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, text_or_selector)))
                el.click()
                time.sleep(1)
                return f"Clicked link: '{text_or_selector}'"
            except (TimeoutException, NoSuchElementException):
                pass

            # 2. Try button/input by value or text
            try:
                els = driver.find_elements(
                    By.XPATH,
                    f"//*[contains(text(), '{text_or_selector}') or "
                    f"@value='{text_or_selector}' or "
                    f"@aria-label='{text_or_selector}']"
                )
                if els:
                    els[0].click()
                    time.sleep(1)
                    return f"Clicked: '{text_or_selector}'"
            except Exception:
                pass

            # 3. Try as CSS selector
            try:
                el = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, text_or_selector)))
                el.click()
                time.sleep(1)
                return f"Clicked element: '{text_or_selector}'"
            except (TimeoutException, NoSuchElementException):
                pass

            return f"Could not find element to click: '{text_or_selector}'"

    def type_text(self, text: str, clear_first: bool = True) -> str:
        """
        Type text into the currently focused element.
        If clear_first=True, clears the field first.
        """
        with self._lock:
            from selenium.webdriver.common.action_chains import ActionChains
            driver = self._get_driver()
            try:
                active = driver.switch_to.active_element
                if clear_first:
                    active.send_keys(Keys.CONTROL + "a")
                    active.send_keys(Keys.DELETE)
                active.send_keys(text)
                return f"Typed: '{text[:50]}{'...' if len(text) > 50 else ''}'"
            except Exception as e:
                return f"Could not type: {e}"

    def press_enter(self) -> str:
        """Press Enter on the focused element."""
        with self._lock:
            driver = self._get_driver()
            try:
                driver.switch_to.active_element.send_keys(Keys.RETURN)
                time.sleep(1.5)
                return "Pressed Enter"
            except Exception as e:
                return f"Could not press Enter: {e}"

    def type_and_submit(self, text: str, selector: str = "") -> str:
        """Type text into an input and press Enter to submit."""
        with self._lock:
            driver = self._get_driver()
            wait = WebDriverWait(driver, self.config.get("wait_timeout", 10))

            target = None
            if selector:
                try:
                    target = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                except Exception:
                    pass

            if target is None:
                # Try finding any visible text input
                try:
                    inputs = driver.find_elements(
                        By.CSS_SELECTOR,
                        "input[type='text'], input[type='search'], textarea, input:not([type])"
                    )
                    for inp in inputs:
                        if inp.is_displayed():
                            target = inp
                            break
                except Exception:
                    pass

            if target:
                target.clear()
                target.send_keys(text)
                target.send_keys(Keys.RETURN)
                time.sleep(2)
                return f"Typed and submitted: '{text}'"
            else:
                return "Could not find an input field to type into"

    def scroll(self, direction: str = "down", amount: int = 500) -> str:
        """Scroll the page up or down by `amount` pixels."""
        with self._lock:
            driver = self._get_driver()
            pixels = amount if direction.lower() == "down" else -amount
            driver.execute_script(f"window.scrollBy(0, {pixels});")
            time.sleep(0.5)
            return f"Scrolled {direction} {amount}px"

    def scroll_to_top(self) -> str:
        """Jump to the top of the page."""
        with self._lock:
            self._get_driver().execute_script("window.scrollTo(0, 0);")
            return "Scrolled to top"

    def scroll_to_bottom(self) -> str:
        """Jump to the bottom of the page."""
        with self._lock:
            self._get_driver().execute_script("window.scrollTo(0, document.body.scrollHeight);")
            return "Scrolled to bottom"

    # ── Tab Management ─────────────────────────────────────────────────────────

    def new_tab(self, url: str = "") -> str:
        """Open a new browser tab, optionally navigating to a URL."""
        with self._lock:
            driver = self._get_driver()
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            if url:
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                driver.get(url)
                time.sleep(1.5)
                return f"Opened new tab: {driver.title}"
            return "Opened new blank tab"

    def get_tabs(self) -> list[dict]:
        """Return a list of open tabs with index, title, and URL."""
        with self._lock:
            driver = self._get_driver()
            tabs = []
            current = driver.current_window_handle
            for i, handle in enumerate(driver.window_handles):
                try:
                    driver.switch_to.window(handle)
                    tabs.append({
                        "index": i,
                        "title": driver.title,
                        "url": driver.current_url,
                        "active": handle == current,
                    })
                except Exception:
                    tabs.append({"index": i, "title": "?", "url": "?", "active": False})
            # Switch back
            driver.switch_to.window(current)
            return tabs

    def switch_tab(self, index: int) -> str:
        """Switch to tab by index (0-based)."""
        with self._lock:
            driver = self._get_driver()
            handles = driver.window_handles
            if 0 <= index < len(handles):
                driver.switch_to.window(handles[index])
                return f"Switched to tab {index}: {driver.title}"
            return f"Tab {index} does not exist (have {len(handles)} tabs)"

    def close_tab(self) -> str:
        """Close the current tab."""
        with self._lock:
            driver = self._get_driver()
            driver.close()
            if driver.window_handles:
                driver.switch_to.window(driver.window_handles[-1])
                return f"Closed tab. Now on: {driver.title}"
            return "Closed last tab. Browser is empty."

    # ── Screenshot ─────────────────────────────────────────────────────────────

    def take_screenshot(self, save_path: str = "") -> str:
        """
        Take a screenshot of the current browser viewport.
        Returns the file path where it was saved.
        """
        with self._lock:
            driver = self._get_driver()
            if not save_path:
                import tempfile
                save_path = os.path.join(tempfile.gettempdir(), "aria_chrome_shot.png")
            driver.save_screenshot(save_path)
            return save_path

    # ── High-level Research Helper ─────────────────────────────────────────────

    def research(self, query: str) -> str:
        """
        Full research flow:
        1. Search Google for the query
        2. Read the top result page content
        3. Return combined text for AI to synthesize
        """
        search_result = self.search_google(query)
        time.sleep(1)

        # Try to click the first organic result
        driver = self._get_driver()
        try:
            links = driver.find_elements(By.CSS_SELECTOR, "div.g a[href^='http']")
            for link in links[:3]:
                href = link.get_attribute("href")
                if href and "google.com" not in href:
                    driver.get(href)
                    time.sleep(2)
                    page_content = self.read_page()
                    return (f"Search results:\n{search_result}\n\n"
                            f"First result page content:\n{page_content}")
        except Exception:
            pass

        return search_result

    # ── Status ─────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return a status summary of the browser session."""
        if not self.is_open():
            return {"open": False}
        try:
            tabs = self.get_tabs()
            return {
                "open": True,
                "tab_count": len(tabs),
                "current_url": self.get_current_url(),
                "current_title": self.get_page_title(),
                "tabs": tabs,
            }
        except Exception:
            return {"open": True, "tab_count": "?"}


# ── Singleton instance (shared across agent.py imports) ───────────────────────
_chrome_agent: Optional[ChromeAgent] = None


def get_chrome_agent() -> ChromeAgent:
    """Return (or create) the shared ChromeAgent singleton."""
    global _chrome_agent
    if _chrome_agent is None:
        _chrome_agent = ChromeAgent()
    return _chrome_agent


def close_chrome():
    """Close the shared Chrome session."""
    global _chrome_agent
    if _chrome_agent:
        _chrome_agent.close()
        _chrome_agent = None


# ── Quick self-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🌐 Starting Chrome automation test...")
    agent = ChromeAgent()
    print(agent.open_url("https://www.google.com"))
    print(agent.search_google("Python tutorials for beginners"))
    print(agent.read_page()[:500])
    print(agent.get_tabs())
    input("Press Enter to close browser...")
    agent.close()
    print("✅ Done")
