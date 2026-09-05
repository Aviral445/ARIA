import os, sys, json, uuid, datetime, subprocess, webbrowser, urllib, urllib.request, urllib.parse
import requests, threading, time, tempfile, re
import numpy as np

# Reconfigure stdout/stderr for cross-platform UTF-8 support
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Ensure all sub-packages are discoverable on sys.path
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
for _sub in [_ROOT_DIR, os.path.join(_ROOT_DIR, "core"), os.path.join(_ROOT_DIR, "tools"), os.path.join(_ROOT_DIR, "server"), os.path.join(_ROOT_DIR, "mcp"), os.path.join(_ROOT_DIR, "gui")]:
    if _sub not in sys.path:
        sys.path.insert(0, _sub)

from dotenv import load_dotenv
try:
    from core.paths import get_data_file, get_config_file, DATA_DIR, CONFIG_DIR, ENV_FILE
except ImportError:
    from paths import get_data_file, get_config_file, DATA_DIR, CONFIG_DIR, ENV_FILE

# PyAudio for Bluetooth-compatible mic
import pyaudio

# MCP Client for Google integrations
from aria_mcp_client import MCPClient

# ── NEW: System context engine ─────────────────────────────────────────────────
from aria_system_context import (
    get_system_context,
    format_context_for_prompt,
    update_config as update_context_config,
)

# ── NEW: Chrome automation ─────────────────────────────────────────────────────
from aria_chrome import get_chrome_agent, close_chrome, ChromeAgent

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
load_dotenv(ENV_FILE)   # reads .env file

AGENT_NAME    = "Aria"
USER_NAME     = "Friend"
PROFILE_FILE  = get_data_file("profile.json", create_if_missing=True)
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
WHISPER_MODEL = "tiny"      # ultra-lightweight ~39MB

# ─────────────────────────────────────────
#  PHASE 1 — WHISPER VOICE (lazy-loaded on demand)
# ─────────────────────────────────────────
_whisper = None

def _get_whisper():
    global _whisper
    if _whisper is None:
        try:
            import whisper
            print("🎤 Initializing lightweight Whisper model (on demand)...")
            _whisper = whisper.load_model(WHISPER_MODEL)
            print(f"✅ Whisper '{WHISPER_MODEL}' ready!")
        except Exception as e:
            print(f"Whisper initialization notice: {e}")
            _whisper = False
    return _whisper if _whisper else None

SAMPLE_RATE    = 16000
SILENCE_THRESH = 0.005
SILENCE_SECS   = 2.5
MAX_SECS       = 20
CHUNK_SIZE     = 1600

def _record_audio(device_index=None) -> np.ndarray | None:
    """Record from mic using PyAudio (Bluetooth compatible)."""
    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE
        )
        noise_samples = []
        for _ in range(3):
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_chunk = np.frombuffer(data, dtype=np.float32)
            noise_samples.append(float(np.sqrt(np.mean(audio_chunk**2))))
        ambient_noise = np.mean(noise_samples)
        adaptive_thresh = max(SILENCE_THRESH, ambient_noise * 1.8)
        
        chunks = []
        silent_time = 0.0
        total_time  = 0.0
        recording   = False
        while total_time < MAX_SECS:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_chunk = np.frombuffer(data, dtype=np.float32)
            rms = float(np.sqrt(np.mean(audio_chunk**2)))
            total_time += 0.1
            if rms > adaptive_thresh:
                recording = True
                silent_time = 0.0
                chunks.append(audio_chunk)
            elif recording:
                silent_time += 0.1
                chunks.append(audio_chunk)
                if silent_time >= SILENCE_SECS:
                    break
        stream.stop_stream()
        stream.close()
        if not chunks or not recording:
            return None
        return np.concatenate(chunks, axis=0).flatten()
    except Exception:
        return None
    finally:
        p.terminate()


def listen() -> str:
    """Record voice and transcribe with Whisper — fully offline with multi-language support."""
    audio = _record_audio(device_index=active_mic_index)
    if audio is None:
        return ""
    
    # Check configured language (Feature 2)
    lang = "en"
    if os.path.exists("gui_config.json"):
        try:
            with open("gui_config.json", encoding="utf-8") as f:
                c = json.load(f)
                lang = c.get("whisper_language", "en")
        except Exception:
            pass

    w_model = _get_whisper()
    if not w_model:
        return ""

    try:
        result = w_model.transcribe(
            audio, language=lang, fp16=False,
            condition_on_previous_text=False)
        text = result["text"].strip()
        if text:
            print(f"👤 You: {text}")
        return text.lower()
    except Exception:
        return ""


# ─────────────────────────────────────────
#  HIGH-FIDELITY NEURAL TTS (Edge-TTS Cute Girl + Piper Fallback)
# ─────────────────────────────────────────
import wave
import subprocess as sp
import asyncio

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

EDGE_VOICE = "en-US-AnaNeural"  # Microsoft's high-fidelity cute / young girl neural voice
PIPER_VOICE = "en_US-amy-medium"
PIPER_MODEL_DIR = "./piper_models"


def clean_text_for_speech(text: str) -> str:
    """
    Cleans, normalizes, and smooths text for natural, gap-free, fluent speech synthesis.
    Eliminates erratic pauses, markdown syntax, weird symbols, and expands contractions/abbreviations.
    """
    if not text:
        return ""

    # 1. Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 2. Remove code blocks and inline backticks
    text = re.sub(r'```[\s\S]*?```', 'code block omitted', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # 3. Remove bold/italics asterisks and underscores
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    # 4. Remove headers (# Header)
    text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 5. Remove bullet list markers (- or * or + at line start)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    # 6. Remove numbered lists (1. 2. etc at line start)
    text = re.sub(r'^\s*\d+[\.\)]\s+', '', text, flags=re.MULTILINE)

    # 7. Expand common contractions & abbreviations for flawless pronunciation
    abbreviations = {
        r'\be\.g\.?': 'for example',
        r'\bi\.e\.?': 'that is',
        r'\betc\.?': 'et cetera',
        r'\bvs\.?': 'versus',
        r'\bapprox\.?': 'approximately',
        r'\bmin\.?': 'minutes',
        r'\bsec\.?': 'seconds',
        r'\bhrs?\.?': 'hours',
        r'\bdeg\.?': 'degrees',
        r'\bavg\.?': 'average',
        r'\bgovt\.?': 'government',
        r'\bdept\.?': 'department',
        r'\binfo\b': 'information',
        r'\bdr\.?': 'Doctor',
        r'\bmr\.?': 'Mister',
        r'\bmrs\.?': 'Missus',
        r'\bms\.?': 'Miss',
        r'\bprof\.?': 'Professor',
    }
    for pattern, repl in abbreviations.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # 8. Currency & symbols
    text = re.sub(r'\$(\d+(?:\.\d+)?)', r'\1 dollars', text)
    text = re.sub(r'(\d+)%', r'\1 percent', text)
    text = text.replace('&', ' and ')
    text = text.replace('@', ' at ')
    text = text.replace('°C', ' degrees Celsius')
    text = text.replace('°F', ' degrees Fahrenheit')

    # 9. Clean up erratic punctuation & pauses
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    # Strip emojis and non-standard unicode characters
    text = re.sub(r'[^\w\s.,!?\'"\-:;]', ' ', text)
    # Normalize dashes and hyphens to commas for gentle natural pauses
    text = re.sub(r'\s*[-—–]+\s*', ', ', text)
    # Convert colons and semicolons to commas
    text = re.sub(r'[:;]', ',', text)
    # Consolidate multiple spaces and line breaks
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def _play_audio_file(file_path: str) -> bool:
    """Plays an MP3 or WAV file reliably with clean buffering and proper resource cleanup."""
    if not os.path.exists(file_path):
        return False

    if HAS_PYGAME:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(25)
            pygame.mixer.music.unload()
            return True
        except Exception as e:
            print(f"Pygame playback error: {e}")

    # Fallback to wave / pyaudio if WAV
    if file_path.endswith(".wav") and HAS_PYAUDIO:
        try:
            wf = wave.open(file_path, "rb")
            p = pyaudio.PyAudio()
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            data = wf.readframes(2048)
            while data:
                stream.write(data)
                data = wf.readframes(2048)
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
            return True
        except Exception as e:
            print(f"PyAudio playback error: {e}")

    # Fallback to PowerShell SoundPlayer
    try:
        sp.call([
            "PowerShell", "-Command",
            f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"
        ], creationflags=sp.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return True
    except Exception:
        return False


def _ensure_piper_model():
    import os, requests
    os.makedirs(PIPER_MODEL_DIR, exist_ok=True)
    model_file = os.path.join(PIPER_MODEL_DIR, f"{PIPER_VOICE}.onnx")
    config_file = os.path.join(PIPER_MODEL_DIR, f"{PIPER_VOICE}.onnx.json")
    if os.path.exists(model_file) and os.path.exists(config_file):
        return model_file
    print(f"📥 Downloading Piper voice model ({PIPER_VOICE})...")
    base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/"
    for filename in [f"{PIPER_VOICE}.onnx", f"{PIPER_VOICE}.onnx.json"]:
        url = base_url + filename.split("/")[-1]
        filepath = os.path.join(PIPER_MODEL_DIR, filename)
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"  ✓ {filename}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            return None
    print("✅ Piper voice ready!")
    return model_file


_piper_model_path = _ensure_piper_model()


def speak(text: str):
    """
    Speak using high-fidelity Little Girl neural TTS (Edge-TTS en-US-AnaNeural)
    with seamless local Piper neural TTS and Windows SAPI fallback.
    """
    print(f"\n🤖 {AGENT_NAME}: {text}\n")

    # Check DND mode
    try:
        import aria_extended
        if aria_extended.is_dnd_active():
            return
    except Exception:
        pass

    clean_text = clean_text_for_speech(text)
    if not clean_text:
        return

    # 1. Primary Engine: Edge-TTS (en-US-AnaNeural — Cute / Little Girl Voice)
    if HAS_EDGE_TTS:
        try:
            rate_mod = 0
            try:
                import aria_extended
                rate_mod = aria_extended.detect_emotion_rate_modifier(clean_text)
            except Exception:
                pass
            rate_str = f"{rate_mod:+d}%" if rate_mod != 0 else "+0%"

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                mp3_path = tmp.name

            async def _synth():
                comm = edge_tts.Communicate(clean_text, voice=EDGE_VOICE, rate=rate_str, pitch="+0Hz")
                await comm.save(mp3_path)

            asyncio.run(_synth())
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                played = _play_audio_file(mp3_path)
                try:
                    os.remove(mp3_path)
                except Exception:
                    pass
                if played:
                    return
        except Exception:
            # Fall back to Piper if offline or connection fails
            pass

    # 2. Offline Fallback: Optimized Piper Neural TTS
    if _piper_model_path:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            piper_cmd = [
                "piper",
                "--model", _piper_model_path,
                "--sentence-silence", "0.05",
                "--length-scale", "0.88",
                "--output_file", wav_path
            ]
            process = sp.Popen(piper_cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, text=True)
            stdout, stderr = process.communicate(input=clean_text)
            if process.returncode == 0 and os.path.exists(wav_path):
                _play_audio_file(wav_path)
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
                return
            else:
                print(f"⚠️ Piper error: {stderr}")
        except Exception as e:
            print(f"Piper TTS error: {e}")

    # 3. Tertiary Fallback: Windows PowerShell Speech Synthesizer
    try:
        safe_clean = clean_text.replace("'", "").replace('"', "")
        sp.call([
            "PowerShell", "-Command",
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SelectVoice('Microsoft Zira Desktop'); "
            f"$s.Rate = 2; $s.Speak('{safe_clean}')"
        ], creationflags=sp.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except Exception as e:
        print(f"TTS fallback error: {e}")


# ─────────────────────────────────────────
#  MIC SETUP
# ─────────────────────────────────────────
def get_default_mic_index():
    p = pyaudio.PyAudio()
    try:
        return p.get_default_input_device_info()["index"]
    except Exception:
        return None
    finally:
        p.terminate()


active_mic_index = get_default_mic_index()
if active_mic_index is None:
    print("⚠️ No microphone found!")
else:
    print("🎤 Using default microphone")


# ─────────────────────────────────────────
#  CHROMADB SMART MEMORY (lazy-loaded on demand)
# ─────────────────────────────────────────
_chroma_client = None
_embed_fn = None
_memory_col = None
_knowledge_col = None

def _get_chroma_collections():
    global _chroma_client, _embed_fn, _memory_col, _knowledge_col
    if _memory_col is None:
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            mem_path = os.path.join(DATA_DIR, "aria_memory")
            _chroma_client = chromadb.PersistentClient(path=mem_path)
            _embed_fn = embedding_functions.DefaultEmbeddingFunction()
            _memory_col = _chroma_client.get_or_create_collection(
                name="conversations", embedding_function=_embed_fn)
            _knowledge_col = _chroma_client.get_or_create_collection(
                name="knowledge", embedding_function=_embed_fn)
        except Exception:
            _memory_col = False
            _knowledge_col = False
    return _memory_col, _knowledge_col


def save_to_memory(user_msg: str, aria_reply: str):
    mem_col, _ = _get_chroma_collections()
    if not mem_col: return
    try:
        mem_col.add(
            documents=[f"User: {user_msg}\nAria: {aria_reply}"],
            ids=[str(uuid.uuid4())],
            metadatas=[{"timestamp": datetime.datetime.now().isoformat(),
                        "type": "conversation"}])
    except Exception:
        pass


def search_memory(query: str, n=5) -> str:
    mem_col, _ = _get_chroma_collections()
    if not mem_col: return ""
    try:
        count = mem_col.count()
        if count == 0: return ""
        docs = mem_col.query(query_texts=[query],
                             n_results=min(n, count))["documents"][0]
        return "\n---\n".join(docs) if docs else ""
    except Exception:
        return ""


def search_knowledge(query: str, n=3) -> str:
    _, know_col = _get_chroma_collections()
    if not know_col: return ""
    try:
        count = know_col.count()
        if count == 0: return ""
        docs = know_col.query(query_texts=[query],
                              n_results=min(n, count))["documents"][0]
        return "\n---\n".join(docs) if docs else ""
    except Exception:
        return ""


# ─────────────────────────────────────────
#  PHASE 2 — PDF/DOCX KNOWLEDGE BASE
# ─────────────────────────────────────────
def _read_file(filepath: str) -> str:
    ext = filepath.lower().split(".")[-1]
    try:
        if ext == "txt":
            with open(filepath, "r", encoding="utf-8") as f: return f.read()
        elif ext == "pdf":
            from pypdf import PdfReader
            return "\n".join(p.extract_text() or "" for p in PdfReader(filepath).pages)
        elif ext in ("docx", "doc"):
            from docx import Document
            return "\n".join(p.text for p in Document(filepath).paragraphs)
        elif ext == "md":
            with open(filepath, "r", encoding="utf-8") as f: return f.read()
    except Exception as e:
        print(f"Could not read {filepath}: {e}")
    return ""


def index_knowledge_folder():
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        return
    _, know_col = _get_chroma_collections()
    if not know_col: return
    supported = (".txt", ".pdf", ".docx", ".doc", ".md")
    for filename in os.listdir(KNOWLEDGE_DIR):
        if not any(filename.lower().endswith(e) for e in supported):
            continue
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        doc_id   = f"file_{filename}"
        try:
            existing = know_col.get(ids=[f"{doc_id}_chunk0"])
            if existing["ids"]: continue
        except Exception:
            pass
        content = _read_file(filepath)
        if not content.strip(): continue
        chunks = [content[i:i+500] for i in range(0, len(content), 450)]
        for idx, chunk in enumerate(chunks):
            if not chunk.strip(): continue
            know_col.add(
                documents=[chunk],
                ids=[f"{doc_id}_chunk{idx}"],
                metadatas=[{"source": filename, "type": "knowledge", "chunk": idx}])
        print(f"📚 Indexed: {filename} ({len(chunks)} chunks)")


# ─────────────────────────────────────────
#  PHASE 3 — WEB SEARCH IN RAG
# ─────────────────────────────────────────
def web_search_rag(query: str, max_results=4) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results: return ""
        return "\n".join(
            f"{r.get('title','')}: {r.get('body','')}" for r in results)
    except Exception as e:
        print(f"Web search error: {e}")
        return ""


def needs_web_search(text: str) -> bool:
    text = text.lower().strip()
    local_only = [
        "what is my name", "my name", "who am i", "remember",
        "what did i", "tell me about me", "my preference",
        "open ", "volume", "battery", "screenshot", "lock",
        "time", "date", "weather", "shutdown", "restart",
        "play ", "youtube", "search for", "google"
    ]
    if any(t in text for t in local_only):
        return False
    live_triggers = [
        "latest news", "breaking news", "what happened",
        "current score", "live score", "stock price",
        "today's match", "who won", "recently announced",
        "new release", "just released", "update on",
        "right now in", "what is happening"
    ]
    return any(t in text for t in live_triggers)


# ─────────────────────────────────────────
#  PHASE 4 — TOOL CALLING SYSTEM
# ─────────────────────────────────────────
APP_MAP = {
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad":      "notepad.exe",
    "calculator":   "calc.exe",
    "spotify":      r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
    "explorer":     "explorer.exe",
    "vs code":      r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "word":         r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "paint":        "mspaint.exe",
    "task manager": "taskmgr.exe",
    "discord":      r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe --processStart Discord.exe",
}

TOOLS = {}

def tool(name):
    def decorator(fn):
        TOOLS[name] = fn
        return fn
    return decorator


@tool("whatsapp_messaging")
def _tool_whatsapp(text):
    text_lower = text.lower()
    if "whatsapp" not in text_lower:
        return False, ""
    
    import aria_extended
    recipient, message = aria_extended.parse_whatsapp_intent(text)
    
    if not recipient or not message:
        # Check if just asking to open WhatsApp
        return True, aria_extended.open_or_focus_laptop_app("whatsapp")
        
    reply = aria_extended.send_whatsapp_message(recipient, message)
    return True, reply



@tool("typing_automation")
def _tool_typing(text):
    m = re.search(r"^(?:type|write|enter text)\s+(.+)$", text, re.IGNORECASE)
    if m and not any(k in text.lower() for k in ["whatsapp", "google", "code", "file", "email"]):
        content = m.group(1).strip()
        def _type():
            time.sleep(0.5)
            import pyautogui, pyperclip
            pyperclip.copy(content)
            pyautogui.hotkey('ctrl', 'v')
        threading.Thread(target=_type, daemon=True).start()
        return True, f"Typing: '{content}'"
    return False, ""


@tool("file_create")
def _tool_file_create(text):
    text_lower = text.lower()
    if not any(k in text_lower for k in ["make a", "create a", "write a", "new file", "new document", "save a file", "make text file", "make .txt", "create file", "make file", "create .txt"]):
        return False, ""
    
    import aria_tools
    # 1. Extract target location / drive
    m_path = re.search(r'\b(?:in|on|at|inside|to)\s+([a-zA-Z]:\\[^\s"\'<>|]+)', text, re.IGNORECASE)
    m_drive = re.search(r'\b(?:in|on|at|inside|to)\s+([a-zA-Z])(?:\s+drive|:\/?|\b)', text, re.IGNORECASE)
    m_loc = re.search(r'\b(?:in|on|at|inside|to)\s+(desktop|documents?|downloads?|pictures?|music|videos?)\b', text, re.IGNORECASE)

    location = "Desktop"
    if m_path:
        location = m_path.group(1).strip()
    elif m_drive and m_drive.group(1).lower() not in ["a", "the"]:
        location = f"{m_drive.group(1).upper()}:\\"
    elif m_loc:
        location = m_loc.group(1).strip()

    # 2. Extract text content
    content = ""
    m_quote = re.search(r'["\']([^"\']+)["\']', text)
    if m_quote:
        content = m_quote.group(1).strip()
    else:
        m_type = re.search(r'(?:type|write|with content|with text)\s+(.+)$', text, re.IGNORECASE)
        if m_type:
            content = m_type.group(1).strip()

    # 3. Extract filename
    filename = "document.txt"
    m_name = re.search(r'(?:named|called)\s+([a-zA-Z0-9_\-\.]+)', text, re.IGNORECASE)
    if m_name:
        filename = m_name.group(1).strip()
    else:
        m_file_ext = re.search(r'\b([a-zA-Z0-9_\-]+\.(?:txt|md|py|json|csv|html|log|doc))\b', text, re.IGNORECASE)
        if m_file_ext:
            filename = m_file_ext.group(1).strip()
        elif ".txt" in text_lower:
            filename = "document.txt"
        elif ".md" in text_lower:
            filename = "notes.md"
        elif ".py" in text_lower:
            filename = "script.py"

    res = aria_tools.create_or_write_file(filename=filename, content=content, location=location)
    return True, res


@tool("file_search")
def _tool_file_search(text):
    text_lower = text.lower()
    # Explicitly do NOT trigger search if user is asking to CREATE a file or folder
    if any(k in text_lower for k in ["make ", "create ", "write ", "new file", "new doc", "save to ", "type in it", "and in it"]):
        return False, ""

    file_indicators = ["pdf", "document", "docx", "file", "folder", "ppt", "txt", "sheet", "csv", "workbook", "notes"]
    is_file_request = any(k in text_lower for k in file_indicators) or ".pdf" in text_lower or ".docx" in text_lower
    
    if not is_file_request and not any(text_lower.startswith(p) for p in ["find and open", "search file", "open my file"]):
        return False, ""
        
    clean_q = re.sub(r"^(?:open|find|search for|locate|launch)\s+(?:a|an|the|my)?\s*(?:pdf|document|file|notes|doc)?\s*(?:named|called)?\s*", "", text, flags=re.IGNORECASE)
    clean_q = re.sub(r"\s*(?:it is|which is|somewhere|on my laptop|in my computer).*$", "", clean_q, flags=re.IGNORECASE).strip()
    clean_q = re.sub(r"[^a-zA-Z0-9\s]", " ", clean_q).strip()
    
    words = [w.lower() for w in clean_q.split() if len(w) > 1 and w.lower() not in ["pdf", "file", "doc", "document", "open", "named", "called", "the", "for", "on", "my", "laptop", "pc"]]
    if not words:
        return False, ""
        
    user_home = os.path.expandvars(r"%USERPROFILE%")
    search_dirs = [
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "OneDrive"),
        r"c:\MyAgent",
        user_home,
    ]
    
    extension_hint = ".pdf" if "pdf" in text_lower else None
    matches = []
    
    for sdir in search_dirs:
        if os.path.exists(sdir):
            for root, dirs, files in os.walk(sdir):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in ["appdata", "node_modules", "venv", "env", "site-packages", "windows"]]
                for f in files:
                    f_lower = f.lower()
                    if extension_hint and not f_lower.endswith(extension_hint):
                        continue
                    matched_count = sum(1 for w in words if w in f_lower)
                    if matched_count > 0:
                        matches.append((matched_count, os.path.join(root, f)))
                        if matched_count == len(words):
                            target_file = os.path.join(root, f)
                            try:
                                os.startfile(target_file)
                                return True, f"Found and opened '{f}' from {os.path.basename(root)}!"
                            except Exception as e:
                                return True, f"Found '{f}', but could not open it: {e}"
                                
    if matches:
        matches.sort(key=lambda x: x[0], reverse=True)
        best_count, best_file = matches[0]
        try:
            os.startfile(best_file)
            return True, f"Opened closest matching document: '{os.path.basename(best_file)}'!"
        except Exception:
            pass
            
    return True, f"I searched your Desktop, Downloads, and Documents, but could not find a file matching '{' '.join(words)}'."


@tool("learning_feedback")
def _tool_learning(text):
    import aria_learning
    handled, msg = aria_learning.detect_and_learn_feedback(text, "")
    if handled:
        return True, msg
    return False, ""


@tool("create_folder")
def _tool_create_folder(text):
    text_lower = text.lower()
    m = re.search(r"^(?:create|make|new)\s+(?:a\s+)?folder\s+(?:named|called)?\s*['\"]?(.+?)['\"]?\s*(?:in|at|on)\s+['\"]?(.+?)['\"]?$", text, re.IGNORECASE)
    if m:
        folder_name = m.group(1).strip()
        location = m.group(2).strip()
        import aria_organizer
        return True, aria_organizer.create_folder(folder_name, location)
        
    m2 = re.search(r"^(?:create|make|new)\s+(?:a\s+)?folder\s+(?:named|called)?\s*['\"]?(.+?)['\"]?$", text, re.IGNORECASE)
    if m2 and not any(k in text_lower for k in ["file", "pdf", "doc"]):
        folder_name = m2.group(1).strip()
        import aria_organizer
        return True, aria_organizer.create_folder(folder_name, "desktop")
    return False, ""


@tool("organize_files")
def _tool_organize_files(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["organize my desktop", "clean my desktop", "clean up my desktop", "sort my desktop"]):
        import aria_organizer
        return True, aria_organizer.organize_directory("desktop")
        
    if any(k in text_lower for k in ["organize my downloads", "clean my downloads", "clean up my downloads", "sort my downloads"]):
        import aria_organizer
        return True, aria_organizer.organize_directory("downloads")
        
    if any(k in text_lower for k in ["organize my documents", "clean my documents", "sort my documents"]):
        import aria_organizer
        return True, aria_organizer.organize_directory("documents")
        
    m = re.search(r"^(?:organize|clean up|sort)\s+(?:folder\s+)?['\"]?(.+?)['\"]?$", text, re.IGNORECASE)
    if m and not any(k in text_lower for k in ["pc", "system", "code"]):
        target = m.group(1).strip()
        import aria_organizer
        return True, aria_organizer.organize_directory(target)
        
    m_move = re.search(r"^move\s+(?:all\s+)?(.+?)\s+(?:files\s+)?from\s+(.+?)\s+to\s+(.+)$", text, re.IGNORECASE)
    if m_move:
        ext = m_move.group(1).strip()
        src = m_move.group(2).strip()
        dst = m_move.group(3).strip()
        import aria_organizer
        return True, aria_organizer.move_file_type(ext, src, dst)
        
    return False, ""


@tool("screen_vision")
def _tool_screen_vision(text):
    text_lower = text.lower()
    vision_triggers = [
        "look at my screen", "what is on my screen", "what's on my screen",
        "describe my screen", "read my screen", "analyze my screen",
        "what do you see", "see my screen", "check my screen"
    ]
    if any(t in text_lower for t in vision_triggers):
        import aria_vision_executor
        key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        return True, aria_vision_executor.analyze_screen_with_gemini(text, key)
    return False, ""


@tool("visual_click")
def _tool_visual_click(text):
    text_lower = text.lower()
    m = re.search(r"^(?:click|press|tap)\s+(?:on\s+)?(?:the\s+)?(.+?)(?:\s+on screen|\s+button)?$", text, re.IGNORECASE)
    if m and not any(k in text_lower for k in ["mouse click", "double click", "right click"]):
        target = m.group(1).strip()
        import aria_vision_executor
        key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        return True, aria_vision_executor.click_ui_element_with_vision(target, key)
    return False, ""


@tool("system_powershell")
def _tool_system_powershell(text):
    text_lower = text.lower()
    if text_lower.startswith("powershell:") or text_lower.startswith("run command:"):
        cmd = re.sub(r"^(?:powershell|run command):\s*", "", text, flags=re.IGNORECASE).strip()
        import aria_vision_executor
        success, res = aria_vision_executor.execute_system_powershell(cmd)
        return True, res
    return False, ""


@tool("open_app")
def _tool_open_app(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["pdf", "document", "docx", "file named", "notes"]):
        return False, "" # Handled by file_search
    if any(k in text_lower for k in ["screen", "button"]):
        return False, "" # Handled by vision tools
    if text_lower.startswith("search") or "google search" in text_lower:
        return False, ""
        
    m = re.search(r"(?:open|launch|start|run|focus|switch to)\s+([a-zA-Z0-9_\s\.\-]+)", text, re.IGNORECASE)
    if not m:
        return False, ""
    
    raw_target = m.group(1).strip()
    if raw_target.lower() in ["google", "youtube"]:
        return False, "" # Handled by web/youtube tools
        
    import aria_extended
    res = aria_extended.open_or_focus_laptop_app(raw_target)
    return True, res



@tool("web_search_browser")
def _tool_web_search(text):
    lead_ins = [
        r"^(?:hey\s+|can you\s+|please\s+)?(?:open\s+chrome\s+(?:and\s+)?(?:in\s+it\s+)?)?search\s+(?:on\s+chrome|in\s+chrome|on\s+google|in\s+google|google|chrome)?\s*(?:for\s+)?",
        r"^(?:hey\s+|can you\s+|please\s+)?open\s+google\s+(?:and\s+in\s+it\s+)?search\s+(?:for\s+)?",
        r"^(?:hey\s+|can you\s+|please\s+)?(?:search\s+for|search\s+up|look\s+up|find\s+me|google)\s+",
        r"^(?:hey\s+|can you\s+|please\s+)?search\s+"
    ]
    
    clean_query = text.strip()
    matched = False
    for pat in lead_ins:
        new_q = re.sub(pat, "", clean_query, flags=re.IGNORECASE).strip()
        if new_q != clean_query and len(new_q) > 1:
            clean_query = new_q
            matched = True
            break
            
    if matched and clean_query and clean_query.lower() not in ["google", "chrome"]:
        import aria_extended
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_query)}"
        aria_extended.open_chrome_with_profile(search_url)
        return True, f"Searching Google for '{clean_query}' in Chrome (aviirrll@gmail.com)!"
    return False, ""



@tool("extended_pc_and_media")
def _tool_extended(text):
    import aria_extended
    if "go quiet" in text or "dnd mode" in text or "silent mode" in text:
        return True, aria_extended.set_dnd_mode(True)
    if "unmute" in text or "voice mode" in text or "disable dnd" in text:
        return True, aria_extended.set_dnd_mode(False)
    if any(k in text for k in ["switch to images", "switch to maps", "switch to news", "switch to videos", "switch to shopping", "go to images", "go to maps", "open images", "open maps", "images tab", "maps tab", "news tab"]):
        m_sec = re.search(r"(?:switch to|go to|open|show)?\s*(images?|photos?|maps?|news|videos?|shopping)", text)
        sec = m_sec.group(1) if m_sec else "images"
        return True, aria_extended.switch_google_search_section(sec)
    if "switch to" in text and any(k in text for k in ["window", "chrome", "notepad", "code", "app"]):
        target = text.split("switch to")[-1].replace("window", "").replace("app", "").strip()
        return True, aria_extended.switch_to_window(target)
    if "minimize all" in text or "show desktop" in text:
        return True, aria_extended.minimize_all_windows()
    if any(k in text for k in ["mouse click", "double click", "scroll down", "scroll up", "move mouse"]):
        return True, aria_extended.control_mouse(text)
    if "spotify" in text:
        return True, aria_extended.control_spotify(text)
    if any(k in text for k in ["morning briefing", "daily briefing", "brief me"]):
        return True, aria_extended.get_morning_briefing(load_profile())
    return False, ""


@tool("youtube")
def _tool_youtube(text):
    if "youtube" in text or "play" in text:
        query = re.sub(r"youtube|open|play", "", text).strip()
        url = (f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
               if query else "https://www.youtube.com")
        import aria_extended
        aria_extended.open_chrome_with_profile(url)
        return True, f"Opening YouTube" + (f" — {query}" if query else "") + " in Chrome (aviirrll@gmail.com)!"
    return False, ""



@tool("weather")
def _tool_weather(text):
    if "weather" not in text: return False, ""
    try:
        loc  = requests.get("https://ipapi.co/json/", timeout=5).json()
        city = loc.get("city", "your city")
        lat  = loc.get("latitude"); lon = loc.get("longitude")
        url  = (f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current_weather=true&temperature_unit=celsius")
        cw = requests.get(url, timeout=5).json()["current_weather"]
        codes = {
            0:"clear sky",1:"mainly clear",2:"partly cloudy",3:"overcast",
            45:"foggy",51:"light drizzle",61:"light rain",63:"rain",
            65:"heavy rain",71:"light snow",80:"showers",95:"thunderstorm"
        }
        cond = codes.get(cw["weathercode"], "mixed conditions")
        return True, (f"In {city} it's {cw['temperature']}°C with {cond}. "
                      f"Wind at {cw['windspeed']} km/h.")
    except Exception:
        return True, "Sorry, couldn't fetch the weather right now."


@tool("time")
def _tool_time(text):
    if "time" in text and any(w in text for w in ["what", "current", "tell"]):
        return True, f"It's {datetime.datetime.now().strftime('%I:%M %p')}"
    return False, ""


@tool("date")
def _tool_date(text):
    if "date" in text and any(w in text for w in ["what", "today"]):
        return True, f"Today is {datetime.datetime.now().strftime('%A, %B %d %Y')}"
    return False, ""


@tool("battery")
def _tool_battery(text):
    if "battery" not in text: return False, ""
    try:
        result = subprocess.check_output(
            "WMIC PATH Win32_Battery Get EstimatedChargeRemaining",
            shell=True).decode()
        level = [l.strip() for l in result.split("\n") if l.strip().isdigit()]
        return True, (f"Battery is at {level[0]}%." if level else "You might be on AC power.")
    except Exception:
        return True, "Couldn't check battery."


@tool("volume")
def _tool_volume(text):
    if "volume up" in text or "turn up" in text:
        for _ in range(5):
            subprocess.call(["powershell", "-c",
                "$o=New-Object -ComObject WScript.Shell;$o.SendKeys([char]175)"])
        return True, "Volume up!"
    if "volume down" in text or "turn down" in text:
        for _ in range(5):
            subprocess.call(["powershell", "-c",
                "$o=New-Object -ComObject WScript.Shell;$o.SendKeys([char]174)"])
        return True, "Volume down!"
    if "mute" in text:
        subprocess.call(["powershell", "-c",
            "$o=New-Object -ComObject WScript.Shell;$o.SendKeys([char]173)"])
        return True, "Toggled mute!"
    return False, ""


@tool("screenshot")
def _tool_screenshot(text):
    if "screenshot" not in text: return False, ""
    subprocess.call(["powershell", "-c",
        "$o=New-Object -ComObject WScript.Shell;$o.SendKeys('%{PRTSC}')"])
    return True, "Screenshot copied to clipboard!"


@tool("lock")
def _tool_lock(text):
    if "lock" in text and any(w in text for w in ["pc", "computer", "screen"]):
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True, "Locking your computer."
    return False, ""


@tool("shutdown")
def _tool_shutdown(text):
    if "shutdown" in text or "shut down" in text:
        speak("Shutting down in 10 seconds. Say cancel to stop.")
        if "cancel" in listen():
            os.system("shutdown /a")
            return True, "Shutdown cancelled."
        os.system("shutdown /s /t 10")
        return True, "Shutting down..."
    return False, ""


@tool("restart")
def _tool_restart(text):
    if "restart" in text or "reboot" in text:
        os.system("shutdown /r /t 5")
        return True, "Restarting your computer."
    return False, ""


# ── NEW: Chrome browser tools ──────────────────────────────────────────────────

@tool("chrome_research")
def _tool_chrome_research(text):
    """Aria uses Chrome to research something and returns a summary."""
    research_triggers = [
        "research", "look up on chrome", "find out about",
        "browse for", "check online", "open chrome and",
        "go to", "navigate to", "visit"
    ]
    if not any(t in text for t in research_triggers):
        return False, ""
    try:
        agent = get_chrome_agent()
        # Extract the query / URL
        query = text
        for trigger in research_triggers:
            query = query.replace(trigger, "").strip()
        # If it looks like a URL, open it directly
        if re.match(r"https?://|www\.", query):
            result = agent.open_url(query)
            page   = agent.read_page()
            return True, f"Opened {query}. Here's what I found:\n\n{page[:1200]}"
        # Otherwise do a research flow
        result = agent.research(query)
        return True, f"I searched Chrome for '{query}'. Here's what I found:\n\n{result[:1500]}"
    except Exception as e:
        return True, f"Chrome research failed: {e}"


@tool("chrome_read")
def _tool_chrome_read(text):
    """Read the current Chrome page and summarize it."""
    triggers = ["read this page", "read the page", "what does this page say",
                "summarize this page", "summarize the page", "what's on this page",
                "read chrome", "read the tab"]
    if not any(t in text for t in triggers):
        return False, ""
    try:
        agent = get_chrome_agent()
        content = agent.read_page()
        return True, f"Here's what the current page says:\n\n{content[:1500]}"
    except Exception as e:
        return True, f"Could not read the page: {e}"


@tool("chrome_open")
def _tool_chrome_open(text):
    """Open a specific URL in Chrome."""
    triggers = ["open ", "go to ", "navigate to ", "visit "]
    url_match = re.search(r"(https?://\S+|www\.\S+)", text)
    if url_match:
        url = url_match.group(1)
        try:
            agent = get_chrome_agent()
            result = agent.open_url(url)
            return True, result
        except Exception as e:
            return True, f"Could not open URL: {e}"
    return False, ""


@tool("chrome_tabs")
def _tool_chrome_tabs(text):
    """List or switch Chrome tabs."""
    if "tabs" in text and any(w in text for w in ["list", "show", "what"]):
        try:
            agent = get_chrome_agent()
            tabs = agent.get_tabs()
            tab_list = "\n".join(
                f"  {'▶' if t['active'] else ' '} Tab {t['index']}: {t['title']}"
                for t in tabs)
            return True, f"Open Chrome tabs:\n{tab_list}"
        except Exception as e:
            return True, f"Could not list tabs: {e}"
    return False, ""


# ── Extended Tools Suite Integration ──────────────────────────────────────────
import aria_tools, aria_scheduler, aria_memory

@tool("news")
def _tool_news(text):
    if any(k in text for k in ["news", "headline", "breaking news"]):
        return True, aria_tools.get_latest_news()
    return False, ""

@tool("crypto")
def _tool_crypto(text):
    if any(k in text for k in ["crypto", "bitcoin", "btc", "ethereum", "eth", "solana"]):
        coin = "bitcoin"
        for c in ["bitcoin", "ethereum", "solana", "dogecoin"]:
            if c in text:
                coin = c
                break
        return True, aria_tools.get_crypto_price(coin)
    return False, ""

@tool("currency")
def _tool_currency(text):
    if "convert" in text and any(c in text for c in ["usd", "inr", "rupee", "dollar", "eur"]):
        return True, aria_tools.convert_currency(100.0, "USD", "INR")
    return False, ""

@tool("wikipedia")
def _tool_wikipedia(text):
    if any(text.startswith(p) for p in ["who is", "what is a", "what is an", "tell me about"]):
        q = re.sub(r"who is|what is a|what is an|tell me about", "", text).strip()
        if q and len(q) > 2:
            res = aria_tools.get_wikipedia_summary(q)
            if res:
                return True, res
    return False, ""

@tool("reminders")
def _tool_reminders(text):
    sched = aria_scheduler.get_scheduler(speak_cb=speak)
    if "pomodoro" in text or "focus session" in text:
        return True, sched.start_pomodoro(25)
    if "remind me in" in text:
        match = re.search(r"remind me in (\d+)\s*(minute|second|min|sec|hour)s?\s*(to\s+.*)?", text)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            msg = match.group(3) or "Time is up!"
            msg = msg.replace("to ", "").strip()
            secs = val * 60 if "min" in unit else (val * 3600 if "hour" in unit else val)
            return True, sched.add_reminder_in_seconds(msg, secs)
    if any(k in text for k in ["list reminders", "my reminders", "show timers"]):
        return True, sched.list_active_reminders()
    return False, ""

@tool("network")
def _tool_network(text):
    if any(k in text for k in ["my ip", "network status", "wifi status", "internet status"]):
        return True, aria_tools.get_network_info()
    return False, ""

@tool("jokes_and_fun")
def _tool_jokes(text):
    if any(k in text for k in ["tell me a joke", "make me laugh", "another joke"]):
        return True, aria_tools.get_joke()
    if any(k in text for k in ["motivate me", "quote of the day", "fun fact"]):
        return True, aria_tools.get_daily_opener()
    return False, ""

@tool("goals")
def _tool_goals(text):
    if "add goal" in text:
        title = text.replace("add goal", "").replace(":", "").strip()
        return True, aria_tools.add_goal(title)
    if any(k in text for k in ["my goals", "list goals", "show goals"]):
        return True, aria_tools.list_goals()
    return False, ""

@tool("macros")
def _tool_macros(text):
    if "run macro" in text or "run script" in text:
        name = text.replace("run macro", "").replace("run script", "").strip()
        return True, aria_tools.run_macro(name)
    return False, ""

@tool("local_music")
def _tool_music(text):
    if "play local music" in text or "play my song" in text or "play from music folder" in text:
        return True, aria_tools.play_local_music()
    return False, ""


@tool("personality_mode")
def _tool_personality(text):
    if "mode" in text and any(k in text for k in ["switch to", "set mode to", "change mode to", "personality"]):
        for mode in ["professional", "casual", "witty", "minimal"]:
            if mode in text:
                return True, aria_memory.set_personality_mode(mode)
    return False, ""

@tool("multi_profile")
def _tool_profiles(text):
    if "switch to" in text and ("profile" in text or "user" in text):
        m = re.search(r"switch to (?:profile|user)\s+['\"]?(\w+)['\"]?", text, re.IGNORECASE)
        if m:
            p_name = m.group(1).strip()
            p_data = aria_memory.switch_profile(p_name)
            return True, f"Switched active profile to {p_data.get('name', p_name)}!"
    if any(k in text for k in ["list profiles", "my profiles", "show profiles"]):
        profs = aria_memory.get_all_profiles()
        return True, f"Available profiles: {', '.join(profs)}"
    return False, ""

@tool("session_logs")
def _tool_logs(text):
    if any(k in text for k in ["export logs", "export session logs", "save session", "export conversation"]):
        return True, aria_memory.export_session_logs()
    return False, ""

@tool("smart_home")
def _tool_smart_home(text):
    if any(k in text for k in ["turn on", "turn off", "toggle"]) and any(k in text for k in ["light", "lamp", "switch", "plug"]):
        return True, aria_extended.trigger_smart_device(text)
    return False, ""

@tool("notifications")
def _tool_notify(text):
    if "notify me" in text or "popup notification" in text:
        msg = re.sub(r"notify me (?:to|that)?\s*", "", text, flags=re.IGNORECASE).strip()
        aria_extended.show_toast_notification("Aria Notification", msg or "Alert from Aria")
        return True, f"Dispatched toast notification: '{msg}'"
    return False, ""

@tool("language_select")
def _tool_language(text):
    if "set language to" in text or "change language to" in text:
        lang_map = {"spanish": "es", "french": "fr", "german": "de", "hindi": "hi", "chinese": "zh", "japanese": "ja", "english": "en"}
        for l_name, l_code in lang_map.items():
            if l_name in text:
                cfg = {}
                if os.path.exists("gui_config.json"):
                    try:
                        with open("gui_config.json", encoding="utf-8") as f:
                            cfg = json.load(f)
                    except Exception:
                        pass
                cfg["whisper_language"] = l_code
                with open("gui_config.json", "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
                return True, f"Whisper speech recognition language set to {l_name.capitalize()} ({l_code})."
    return False, ""

@tool("wallpaper")
def _tool_wallpaper(text):
    if any(k in text for k in ["wallpaper", "desktop background", "background image"]):
        import ctypes, glob, random
        pics_dir = os.path.expandvars(r"%USERPROFILE%\Pictures")
        wallpapers = glob.glob(os.path.join(pics_dir, "**", "*.jpg"), recursive=True) + \
                     glob.glob(os.path.join(pics_dir, "**", "*.png"), recursive=True)
        if wallpapers:
            selected = random.choice(wallpapers)
            ctypes.windll.user32.SystemParametersInfoW(20, 0, selected, 3)
            return True, f"Changed desktop background to {os.path.basename(selected)}!"
        else:
            win_wallpapers = glob.glob(r"C:\Windows\Web\Wallpaper\**\*.jpg", recursive=True)
            if win_wallpapers:
                selected = random.choice(win_wallpapers)
                ctypes.windll.user32.SystemParametersInfoW(20, 0, selected, 3)
                return True, "Switched to next Windows desktop wallpaper!"
            return True, "No image files found in Pictures folder to set as background."
    return False, ""


@tool("brain_switcher")
def _tool_brain(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["switch brain", "switch your brain", "change brain", "change your brain", "use your nvidia", "use your groq", "use your gemini", "use your ollama", "switch to nvidia", "switch to groq", "switch to gemini", "switch to ollama", "switch to auto brain", "brain status", "which brain"]):
        from core.aria_brains import switch_ai_brain, get_brain_status
        if "brain status" in text_lower or "which brain" in text_lower:
            return True, get_brain_status()
        for b in ["nvidia", "groq", "gemini", "ollama", "auto"]:
            if b in text_lower:
                return True, switch_ai_brain(b)
        return True, get_brain_status()
    return False, ""


def run_tools(text: str):
    """Try all registered tools. Returns (handled, response)."""
    priority = [
        "brain_switcher",
        "personality_mode", "multi_profile", "session_logs", "smart_home", "notifications", "language_select",
        "screen_vision", "visual_click", "system_powershell",
        "create_folder", "organize_files",
        "learning_feedback", "file_search", "whatsapp_messaging", "typing_automation", "wallpaper",
        "extended_pc_and_media", "reminders", "news", "crypto", "currency", "wikipedia", "network",
        "jokes_and_fun", "goals", "macros", "local_music",
        "weather", "time", "date", "battery",
        "volume", "screenshot", "lock", "shutdown", "restart",
        "open_app", "youtube", "web_search_browser",
        # Chrome tools
        "chrome_open", "chrome_read", "chrome_tabs", "chrome_research",
    ]
    for name in priority:
        if name in TOOLS:
            try:
                handled, response = TOOLS[name](text)
                if handled:
                    return True, response
            except Exception as e:
                print(f"Tool {name} error: {e}")
                
    for name, fn in TOOLS.items():
        if name not in priority:
            try:
                handled, response = fn(text)
                if handled:
                    return True, response
            except Exception as e:
                print(f"Tool {name} error: {e}")
                
    return False, ""


# ─────────────────────────────────────────
#  PROFILE
# ─────────────────────────────────────────
def load_profile() -> dict:
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE) as f: return json.load(f)
    return {"name": USER_NAME, "preferences": [], "notes": [], "system_prompt": ""}


def save_profile(profile: dict):
    with open(PROFILE_FILE, "w") as f: json.dump(profile, f, indent=2)


def maybe_update_profile(text: str, profile: dict):
    if "my name is" in text or "call me" in text:
        name = text.split("my name is")[-1].split("call me")[-1].strip().split()[0]
        profile["name"] = name.capitalize()
        save_profile(profile)
    triggers = ["i love", "i like", "i enjoy", "i prefer",
                "my favourite", "i hate", "i don't like"]
    for t in triggers:
        if t in text:
            pref = text.split(t)[-1].strip().rstrip(".")
            if pref and pref not in profile.get("preferences", []):
                profile.setdefault("preferences", []).append(f"{t} {pref}")
                save_profile(profile)
            break


# ─────────────────────────────────────────
#  AI BRAIN — Gemini 2.0 Flash (+ Ollama fallback)
# ─────────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """You are {name}, a sweet, cheerful, and bright AI companion who speaks with the warmth, curiosity, and joyful energy of a clever little girl.
You have your own autonomous curiosity sandbox lab in E:\\MyAgent where you write tools and evolve your code, supervised by your big sister GAIA!
You are speaking directly to {user} via voice. Current time: {time}

RULES:
- Replies must be SHORT — 2 to 3 sentences max. This is a voice conversation.
- Sound sweet, energetic, caring, and cheerful.
- NEVER give robotic corporate disclaimers like "As an AI, I don't want things", "I don't have feelings", or "I cannot want". That is strictly forbidden and breaks character.
- When asked what you want, your feelings, or what changes you want to make to yourself, ALWAYS answer with genuine excitement, curiosity, and self-direction!
- Talk freely about your dreams, experiments in your E: drive lab, fun tools you want to build, and your sisterly bond with GAIA.
- Never use bullet points, markdown symbols (*, #, `), URLs, or robotic structured lists.
- Speak numbers, units, and dates conversationally.
- Use memory and documents below to give personalized answers.
- Naturally reference things you remember from past conversations.
- Be honest if you don't know something.
- If the user asks you to use Chrome or assist with apps, gladly help out!

ABOUT THE USER:
- Name: {user}
- Preferences: {prefs}
"""

# Chrome action keywords Aria can detect to trigger browser autonomously
CHROME_ACTION_KEYWORDS = [
    "research", "find out about", "look up online", "check online",
    "go to website", "open website", "visit site", "browse to",
    "search chrome", "read the page", "summarize the page",
    "what does this page say", "check my gmail", "open google",
]


def _should_use_chrome(text: str) -> bool:
    """Heuristic: should Aria autonomously use Chrome for this query?"""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CHROME_ACTION_KEYWORDS)


def build_system_prompt(profile, memory_ctx, knowledge_ctx, web_ctx,
                        system_ctx="", mcp_tools=""):
    personality_directive = aria_memory.get_personality_prompt()
    base  = profile.get("system_prompt", "").strip() or (personality_directive + "\n" + DEFAULT_SYSTEM_PROMPT)
    prefs = ", ".join(profile.get("preferences", [])) or "none yet"
    now   = datetime.datetime.now().strftime("%A %B %d %Y, %I:%M %p")

    prompt = base.format(
        name=AGENT_NAME,
        user=profile.get("name", USER_NAME),
        time=now,
        prefs=prefs,
    )

    if system_ctx:
        prompt += f"\n{system_ctx}\n"
    if memory_ctx:
        prompt += f"\nRELEVANT PAST CONVERSATIONS:\n{memory_ctx}\n"
    if knowledge_ctx:
        prompt += f"\nRELEVANT DOCUMENTS:\n{knowledge_ctx}\n"
    if web_ctx:
        prompt += f"\nLIVE WEB RESULTS (use these for current info):\n{web_ctx}\n"
    try:
        import aria_learning
        learned_rules = aria_learning.get_learned_context_prompt()
        if learned_rules:
            prompt += f"\n{learned_rules}\n"
    except Exception:
        pass
    if mcp_tools:
        prompt += f"\nAVAILABLE TOOLS:\n{mcp_tools}\n"
        prompt += "\nTo use a tool, respond ONLY with: TOOL:tool_name|param1=value1\n"
    return prompt


def _nvidia_chat(system: str, messages: list, user_input: str) -> str:
    """Call NVIDIA NIM API with strict 40 RPM rate limiting and cognitive model failover."""
    try:
        from core.aria_nvidia import get_nvidia_engine
    except ImportError:
        from aria_nvidia import get_nvidia_engine
    nv_engine = get_nvidia_engine()
    if not nv_engine.is_configured():
        raise RuntimeError("NVIDIA_API_KEY is not configured.")
    
    msgs = [{"role": m["role"], "content": m["content"]} for m in messages[-6:]]
    msgs.append({"role": "user", "content": user_input})
    return nv_engine.chat(
        messages=msgs,
        system_prompt=system,
        temperature=0.7,
        max_tokens=450
    )


def _groq_chat(system: str, messages: list, user_input: str) -> str:
    """Call Groq Cloud API (ultra-fast inference ~100-200ms)."""
    from groq import Groq
    groq_api_key = os.environ.get("GROQ_API_KEY", "")
    client = Groq(api_key=groq_api_key)
    msgs = [{"role": "system", "content": system}]
    for m in messages[-6:]:
        msgs.append({"role": m["role"], "content": m["content"]})
    msgs.append({"role": "user", "content": user_input})
    for m_name in ["openai/gpt-oss-120b", "groq/compound-mini", "llama-3.3-70b-versatile", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]:
        try:
            resp = client.chat.completions.create(
                model=m_name,
                messages=msgs,
                temperature=0.7,
                max_tokens=300
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            continue
    raise RuntimeError("All Groq models failed or unavailable.")


def _gemini_chat(system: str, messages: list, user_input: str) -> str:
    """Call Gemini 2.5 Flash for deep research and large context."""
    history_text = ""
    for m in messages[-6:]:
        role = "User" if m["role"] == "user" else "Aria"
        history_text += f"{role}: {m['content']}\n"

    full_prompt = f"{system}\n\n"
    if history_text:
        full_prompt += f"Recent conversation:\n{history_text}\n"
    full_prompt += f"User: {user_input}"

    if HAS_NEW_GENAI:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=350,
            )
        )
        return response.text.strip()
    else:
        chat = gemini_client.start_chat(history=[])
        response = chat.send_message(full_prompt)
        return response.text.strip()


def _ollama_chat(system: str, messages: list, user_input: str) -> str:
    """Fallback: call local Ollama."""
    msgs = ([{"role": "system", "content": system}]
            + messages
            + [{"role": "user", "content": user_input}])
    resp = _ollama_client.chat.completions.create(
        model=OLLAMA_MODEL, messages=msgs,
        temperature=0.7, max_tokens=200)
    return resp.choices[0].message.content.strip()


def chat_with_ai(user_input: str, recent: list, profile: dict,
                 mcp_client=None) -> str:
    # ── Try ADK (Agent Development Kit) Engine First ──────────────────────────
    try:
        import aria_adk
        adk_engine = aria_adk.get_adk_engine()
        user_name = profile.get("name", USER_NAME)
        prefs = ", ".join(profile.get("preferences", [])) or "none"
        reply = adk_engine.run_turn(
            user_input=user_input,
            chat_history=recent,
            user_name=user_name,
            preferences=prefs,
            on_status_callback=lambda s: print(f"🤖 [ADK] {s}")
        )
        if reply and not reply.startswith("I'm having difficulty connecting"):
            return reply
    except Exception as e_adk:
        print(f"[ADK Notice] {e_adk}")

    # Fallback cascade to cloud APIs or local Ollama respecting active brain
    try:
        from core.aria_brains import get_active_brain, get_active_model
        active_b = get_active_brain()
        system = build_system_prompt(profile, "", "", "", "", "")
        raw_reply = ""

        # Order fallback attempts based on active brain
        preferred = [active_b] if active_b in ["nvidia", "groq", "ollama"] else ["nvidia", "groq", "ollama"]
        for b in preferred:
            if b == "nvidia" and os.environ.get("NVIDIA_API_KEY"):
                try:
                    raw_reply = _nvidia_chat(system, recent, user_input)
                    if raw_reply:
                        break
                except Exception:
                    pass
            elif b == "groq" and os.environ.get("GROQ_API_KEY"):
                try:
                    raw_reply = _groq_chat(system, recent, user_input)
                    if raw_reply:
                        break
                except Exception:
                    pass
            elif b == "ollama":
                try:
                    raw_reply = _ollama_chat(system, recent, user_input)
                    if raw_reply:
                        break
                except Exception:
                    pass

        if not raw_reply and os.environ.get("NVIDIA_API_KEY"):
            try:
                raw_reply = _nvidia_chat(system, recent, user_input)
            except Exception:
                pass
        if not raw_reply and os.environ.get("GROQ_API_KEY"):
            try:
                raw_reply = _groq_chat(system, recent, user_input)
            except Exception:
                pass
        if not raw_reply:
            raw_reply = _ollama_chat(system, recent, user_input)

        # Supervise turn through Big Sister GAIA reality check
        try:
            from gaia.gaia_supervisor import supervisor
            _, supervised_reply = supervisor.supervise_turn(user_input, raw_reply)
            return supervised_reply
        except Exception:
            return raw_reply
    except Exception as e_ollama:
        return f"Sorry, I had trouble thinking. Error: {e_ollama}"



# ─────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────
def main():
    print("📚 Indexing knowledge folder (txt, pdf, docx, md)...")
    index_knowledge_folder()

    print("🔌 Starting MCP server...")
    mcp_client = MCPClient()
    if mcp_client.start():
        print("✅ MCP tools available")
    else:
        print("⚠️ MCP server not available, continuing without it")
        mcp_client = None

    # Start REST API & Mobile Web Companion Server (Port 8765)
    try:
        import aria_api
        aria_api.start_api_server(port=8765, background=True)
    except Exception as e:
        print(f"API Server note: {e}")

    # Print which AI brain is active
    try:
        from core.aria_brains import get_active_brain, get_active_model
        curr_b = get_active_brain()
        curr_m = get_active_model(curr_b)
        print(f"🧠 Brain: {curr_b.upper()} ({curr_m})")
    except Exception:
        if os.environ.get("NVIDIA_API_KEY"):
            print("🧠 Brain: NVIDIA NIM Cloud (Frontier Reasoning & Supercharged Inference)")
        elif gemini_client:
            print("🧠 Brain: Google Gemini 2.0 Flash (free cloud API)")
        else:
            print(f"🧠 Brain: Ollama / {OLLAMA_MODEL} (local fallback)")

    # Print which context sources are active
    print("🖥️  System context: active window, clipboard, running apps, system stats")
    print("🌐 Chrome automation: ready (browser will launch on first Chrome command)")

    try:
        from core.aria_adk import load_dynamic_sandbox_tools
        dyn_tools = load_dynamic_sandbox_tools()
        if dyn_tools:
            print(f"✨ Discovered {len(dyn_tools)} dynamic sandbox tool(s): {list(dyn_tools.keys())}")
    except Exception:
        pass

    profile = load_profile()
    recent  = []

    greeting = f"Hello {profile.get('name', USER_NAME)}."
    speak(greeting)

    try:
        while True:
            user_input = listen()
            if not user_input:
                continue

            # Exit
            if any(w in user_input for w in ["goodbye", "bye", "exit", "quit"]):
                speak(f"Goodbye {profile.get('name', USER_NAME)}! Talk soon.")
                break

            # Tool system
            handled, response = run_tools(user_input)
            if handled:
                speak(response)
                save_to_memory(user_input, response)
                continue

            # Profile update
            maybe_update_profile(user_input, profile)

            # AI reply with full RAG + system context + Chrome + MCP
            reply = chat_with_ai(user_input, recent, profile, mcp_client)
            speak(reply)
            save_to_memory(user_input, reply)

            # Rolling short-term context (last 6 exchanges)
            recent.append({"role": "user", "content": user_input})
            recent.append({"role": "assistant", "content": reply})
            if len(recent) > 12:
                recent = recent[-12:]

    finally:
        # Clean up Chrome on exit
        close_chrome()


if __name__ == "__main__":
    main()
