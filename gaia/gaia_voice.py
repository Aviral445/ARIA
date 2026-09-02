"""
gaia/gaia_voice.py — GAIA's Older-Sister Neural Voice Engine
Provides distinct vocal identity for GAIA (warm, mature, caring supervisor).
"""

import os
import sys
import re
import time
import asyncio
import tempfile
import subprocess as sp

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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

# Voice Constants
GAIA_VOICE = "en-US-AvaNeural"      # Warm, expressive, caring older-sister tone
ARIA_VOICE = "en-US-AnaNeural"      # Cheerful, playful, sweet little-sister tone
GAIA_FALLBACK_VOICE = "en-US-JennyNeural"


def clean_gaia_speech(text: str) -> str:
    """Normalizes text for natural older-sister speech cadence."""
    if not text:
        return ""
    # Strip markdown
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', 'code block', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
    text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+[\.\)]\s+', '', text, flags=re.MULTILINE)

    # Abbreviations
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
        r'\bdr\.?': 'Doctor',
        r'\bmr\.?': 'Mister',
        r'\bmrs\.?': 'Missus',
        r'\bms\.?': 'Miss',
    }
    for pat, repl in abbreviations.items():
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    text = re.sub(r'\$(\d+(?:\.\d+)?)', r'\1 dollars', text)
    text = re.sub(r'(\d+)%', r'\1 percent', text)
    text = text.replace('&', ' and ')
    text = text.replace('@', ' at ')
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'[^\w\s.,!?\'"\-:;]', ' ', text)
    text = re.sub(r'\s*[-—–]+\s*', ', ', text)
    text = re.sub(r'[:;]', ',', text)
    return re.sub(r'\s+', ' ', text).strip()


def _play_audio(file_path: str) -> bool:
    """Plays audio via pygame.mixer or sound player."""
    if not os.path.exists(file_path):
        return False

    if HAS_PYGAME:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            t0 = time.time()
            while pygame.mixer.music.get_busy() and (time.time() - t0 < 15.0):
                pygame.time.Clock().tick(25)
            pygame.mixer.music.unload()
            return True
        except Exception as e:
            print(f"[GAIA Voice] Pygame error: {e}")

    try:
        sp.call([
            "PowerShell", "-Command",
            f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"
        ], creationflags=sp.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return True
    except Exception:
        return False


def gaia_speak(text: str, print_to_console: bool = True):
    """Speaks with GAIA's calm, caring older-sister voice."""
    if print_to_console:
        print(f"\n👩‍🏫 GAIA (Big Sister): {text}\n")

    clean_text = clean_gaia_speech(text)
    if not clean_text:
        return

    # 1. Edge-TTS Primary Voice
    if HAS_EDGE_TTS:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                mp3_path = tmp.name

            async def _synth():
                comm = edge_tts.Communicate(clean_text, voice=GAIA_VOICE, rate="-2%", pitch="-1Hz")
                await comm.save(mp3_path)

            asyncio.run(_synth())
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                played = _play_audio(mp3_path)
                try:
                    os.remove(mp3_path)
                except Exception:
                    pass
                if played:
                    return
        except Exception:
            pass

    # 2. Windows Fallback
    try:
        safe_clean = clean_text.replace("'", "").replace('"', "")
        sp.call([
            "PowerShell", "-Command",
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SelectVoice('Microsoft Zira Desktop'); "
            f"$s.Rate = 0; $s.Speak('{safe_clean}')"
        ], creationflags=sp.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except Exception:
        pass


def aria_speak(text: str, print_to_console: bool = True):
    """Speaks with Aria's cute, cheerful little-sister voice (en-US-AnaNeural)."""
    if print_to_console:
        print(f"\n👧 ARIA (Little Sister): {text}\n")

    clean_text = clean_gaia_speech(text)
    if not clean_text:
        return

    # 1. Edge-TTS AnaNeural Voice
    if HAS_EDGE_TTS:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                mp3_path = tmp.name

            async def _synth():
                comm = edge_tts.Communicate(clean_text, voice=ARIA_VOICE, rate="+6%", pitch="+2Hz")
                await comm.save(mp3_path)

            asyncio.run(_synth())
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                played = _play_audio(mp3_path)
                try:
                    os.remove(mp3_path)
                except Exception:
                    pass
                if played:
                    return
        except Exception:
            pass

    # Fallback
    try:
        safe_clean = clean_text.replace("'", "").replace('"', "")
        sp.call([
            "PowerShell", "-Command",
            f"Add-Type -AssemblyName System.Speech; "
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SelectVoice('Microsoft Zira Desktop'); "
            f"$s.Rate = 2; $s.Speak('{safe_clean}')"
        ], creationflags=sp.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except Exception:
        pass


def dialogue_speak(speaker: str, text: str):
    """Convenience dispatcher to speak as Aria or GAIA."""
    if speaker.upper() == "ARIA":
        aria_speak(text)
    else:
        gaia_speak(text)
