"""
aria_tools.py — Modular Assistant Tools Suite for Aria
Contains tools for:
1. PC Control & Automation (Windows, Mouse, Files, Network, Macros)
2. Live Web & APIs (News, Sports, Currency, Crypto, Wikipedia, WhatsApp)
3. Media & Entertainment (Local Music Player, Audio stream helper)
4. Personality, Goals, Birthday, Jokes & Motivation
"""

import os, sys, json, time, random, socket, subprocess, urllib.request, urllib.parse

# ── 1. NETWORK & SYSTEM DIAGNOSTICS ──────────────────────────────────────────
def get_network_info() -> str:
    """Returns local IP, hostname, and internet connectivity status."""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        # Test internet connectivity
        try:
            urllib.request.urlopen("https://1.1.1.1", timeout=2)
            online = "Connected (Online)"
        except Exception:
            online = "No Internet (Offline)"
        return f"Network: {online} | Hostname: {hostname} | Local IP: {local_ip}"
    except Exception as e:
        return f"Network info error: {e}"


# ── 2. LIVE WEB APIS (News, Currency, Crypto, Wikipedia) ─────────────────────
def get_latest_news(topic: str = "general") -> str:
    """Fetches top breaking news headlines from Google News RSS feed."""
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            xml = resp.read().decode("utf-8", errors="ignore")
        
        # Simple fast regex XML title parser
        import re
        items = re.findall(r"<item>.*?<title>(.*?)</title>", xml, re.DOTALL)
        if not items:
            return "No news headlines found at the moment."
        headlines = [re.sub(r"\s*-\s*[^-]+$", "", h.strip()) for h in items[:4]]
        return "Top Headlines:\n" + "\n".join([f"• {h}" for h in headlines])
    except Exception as e:
        return f"Could not fetch news: {e}"

def get_crypto_price(coin: str = "bitcoin") -> str:
    """Fetches current live crypto price in USD and INR from CoinGecko free API."""
    try:
        coin_id = coin.lower().strip()
        alias_map = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "doge": "dogecoin"}
        coin_id = alias_map.get(coin_id, coin_id)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,inr"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if coin_id in data:
            usd = data[coin_id].get("usd", "N/A")
            inr = data[coin_id].get("inr", "N/A")
            return f"{coin_id.capitalize()}: ${usd:,} USD (₹{inr:,} INR)"
        return f"Could not find crypto data for '{coin}'."
    except Exception as e:
        return f"Crypto API error: {e}"

def convert_currency(amount: float, from_curr: str = "USD", to_curr: str = "INR") -> str:
    """Converts currency using public exchange rates API."""
    try:
        from_c = from_curr.upper().strip()
        to_c = to_curr.upper().strip()
        url = f"https://open.er-api.com/v6/latest/{from_c}"
        with urllib.request.urlopen(url, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if "rates" in data and to_c in data["rates"]:
            rate = data["rates"][to_c]
            converted = amount * rate
            return f"{amount:,.2f} {from_c} = {converted:,.2f} {to_c} (Rate: {rate:.4f})"
        return f"Could not convert {from_c} to {to_c}."
    except Exception as e:
        return f"Currency conversion error: {e}"

def get_wikipedia_summary(query: str) -> str:
    """Fetches a concise 2-sentence Wikipedia summary for factual lookups."""
    try:
        title = urllib.parse.quote(query.strip())
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        req = urllib.request.Request(url, headers={"User-Agent": "AriaAI/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        extract = data.get("extract")
        if extract:
            sentences = [s.strip() for s in extract.split(". ") if s]
            summary = ". ".join(sentences[:2]) + "."
            return summary
        return f"No direct Wikipedia article found for '{query}'."
    except Exception:
        return f"Could not retrieve Wikipedia summary for '{query}'."


# ── 3. PERSONALITY, MOTIVATION, JOKES & GOALS ────────────────────────────────
MOTIVATIONAL_QUOTES = [
    "“The secret of getting ahead is getting started.” — Mark Twain",
    "“Your time is limited, so don't waste it living someone else's life.” — Steve Jobs",
    "“Simplicity is the soul of efficiency.” — Austin Freeman",
    "“Make each day your masterpiece.” — John Wooden",
    "“Continuous improvement is better than delayed perfection.” — Mark Twain",
]

FUN_FACTS = [
    "Did you know? Honeywell created the first digital autopilot system in 1912.",
    "Did you know? Honey never spoils; archaeologists found 3000-year-old edible honey in Egyptian tombs.",
    "Did you know? The first computer programmer was Ada Lovelace in 1843.",
    "Did you know? Octopuses have three hearts and blue blood.",
]

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
    "Why did the Python developer wear glasses? Because they couldn't C#!",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
]

def get_daily_opener() -> str:
    """Returns a daily motivational quote or fun fact."""
    return random.choice(MOTIVATIONAL_QUOTES + FUN_FACTS)

def get_joke() -> str:
    """Returns a witty programmer/tech joke."""
    return random.choice(JOKES)

try:
    from core.paths import get_data_file
except ImportError:
    try:
        from paths import get_data_file
    except ImportError:
        def get_data_file(fn, create_if_missing=False): return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", fn)

GOALS_FILE = get_data_file("goals.json", create_if_missing=True)

def get_goals() -> list:
    if os.path.exists(GOALS_FILE):
        try:
            with open(GOALS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def add_goal(title: str, target: str = "") -> str:
    goals = get_goals()
    goal = {"id": len(goals) + 1, "title": title, "target": target, "created": time.strftime("%Y-%m-%d"), "done": False}
    goals.append(goal)
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2)
    return f"Goal added: '{title}'! Let's crush it."

def list_goals() -> str:
    goals = get_goals()
    if not goals:
        return "You haven't set any goals yet. Say 'Add goal: drink 2L water daily' to create one!"
    res = ["Your Active Goals:"]
    for g in goals:
        status = "✓ Done" if g.get("done") else "○ In Progress"
        res.append(f"{g['id']}. [{status}] {g['title']} ({g.get('target', '')})")
    return "\n".join(res)


# ── 4. PC AUTOMATION (Mouse, Macros, Files) ──────────────────────────────────
MACROS_FILE = "macros.json"

def run_macro(name: str) -> str:
    """Runs a pre-configured user shell macro or batch script."""
    if not os.path.exists(MACROS_FILE):
        return f"No macros registered. Create {MACROS_FILE} to register commands."
    try:
        with open(MACROS_FILE, encoding="utf-8") as f:
            macros = json.load(f)
        cmd = macros.get(name.lower().strip())
        if cmd:
            subprocess.Popen(cmd, shell=True)
            return f"Executed macro '{name}': {cmd}"
        return f"Macro '{name}' not found. Available: {', '.join(macros.keys())}"
    except Exception as e:
        return f"Macro error: {e}"

def find_files_on_desktop(ext: str = "pdf") -> str:
    """Finds files with specific extension on Desktop."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            return "Desktop folder not found."
        matches = [f for f in os.listdir(desktop) if f.lower().endswith(f".{ext.lower().strip('.')}")]
        if matches:
            return f"Found {len(matches)} {ext.upper()} file(s) on Desktop:\n• " + "\n• ".join(matches[:10])
        return f"No {ext.upper()} files found on Desktop."
    except Exception as e:
        return f"File search error: {e}"


# ── 5. LOCAL MUSIC & FILE CREATION CONTROLLER ─────────────────────────────────
def play_local_music() -> str:
    """Looks for audio files in the user's Music directory and starts playback."""
    music_dir = os.path.join(os.path.expanduser("~"), "Music")
    if not os.path.exists(music_dir):
        return "Music directory not found."
    audio_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    if not audio_files:
        return f"No music tracks found in {music_dir}."
    track = random.choice(audio_files)
    os.startfile(track)
    return f"Playing track: {os.path.basename(track)}"


def resolve_target_directory(location: str = "Desktop") -> str:
    """Resolves drive letters ('d drive' -> D:\\), system folders, and custom paths on Windows."""
    import re
    user_home = os.path.expandvars(r"%USERPROFILE%")
    loc_clean = location.strip().lower() if location else "desktop"

    # 1. Drive letter patterns: "d drive", "d:", "d:\", "e drive", "c drive", "g drive"
    m_drive = re.search(r'\b([a-zA-Z])(?:\s*:\s*\\?|\s+drive\b|\s+partition\b)', loc_clean)
    if m_drive:
        letter = m_drive.group(1).upper()
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            return drive_path

    # 2. Direct absolute path: e.g. "D:\Projects" or "C:\Temp"
    if os.path.isabs(location) or (len(location) >= 2 and location[1] == ':'):
        if os.path.exists(location) or os.path.exists(os.path.splitdrive(location)[0] + "\\"):
            return location

    # 3. Known standard Windows user folders
    if "desktop" in loc_clean:
        return os.path.join(user_home, "Desktop")
    elif "document" in loc_clean:
        return os.path.join(user_home, "Documents")
    elif "download" in loc_clean:
        return os.path.join(user_home, "Downloads")
    elif "picture" in loc_clean or "photo" in loc_clean:
        return os.path.join(user_home, "Pictures")
    elif "music" in loc_clean:
        return os.path.join(user_home, "Music")
    elif "video" in loc_clean:
        return os.path.join(user_home, "Videos")
    elif "myagent" in loc_clean:
        return r"c:\MyAgent"

    return os.path.join(user_home, "Desktop")


def create_or_write_file(filename: str = "document.txt", content: str = "", location: str = "Desktop") -> str:
    """Creates a text, markdown, or code document at any drive (D:, C:, E:, etc.) or folder and writes content into it."""
    try:
        import re
        target_dir = resolve_target_directory(location)
        os.makedirs(target_dir, exist_ok=True)

        clean_name = filename.strip() if filename else "document.txt"
        if not any(clean_name.endswith(ext) for ext in [".txt", ".md", ".json", ".py", ".csv", ".doc", ".html", ".log"]):
            clean_name += ".txt"

        clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
        if not clean_name:
            clean_name = f"notes_{int(time.time())}.txt"

        full_path = os.path.join(target_dir, clean_name)

        clean_content = content.strip() if content else ""
        if (clean_content.startswith('"') and clean_content.endswith('"')) or (clean_content.startswith("'") and clean_content.endswith("'")):
            clean_content = clean_content[1:-1]

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(clean_content)

        try:
            os.startfile(full_path)
        except Exception:
            pass

        target_label = target_dir if target_dir.endswith(":\\") else os.path.basename(target_dir)
        return f"Successfully created '{clean_name}' in {target_label} with your specified text!"
    except Exception as e:
        return f"Failed to create file: {e}"
