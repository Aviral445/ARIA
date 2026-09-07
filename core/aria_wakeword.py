"""
core/aria_wakeword.py — Wake Word Detection ("Hey Aria") (Feature 1)
Listens passively in the background for wake triggers ("Hey Aria", "Aria", "OK Aria")
using lightweight audio energy gating and phrase spotting without pegging CPU.
"""

import os
import sys
import time
import threading
from typing import List, Callable, Optional

from gaia.gaia_bus import bus

DEFAULT_WAKE_WORDS = ["hey aria", "ok aria", "wake up aria", "aria"]


class WakeWordDetector:
    def __init__(
        self,
        wake_words: Optional[List[str]] = None,
        energy_threshold: int = 300,
        check_interval: float = 0.5
    ):
        self.wake_words = [w.lower().strip() for w in (wake_words or DEFAULT_WAKE_WORDS)]
        self.energy_threshold = energy_threshold
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[str], None]] = []

    def add_callback(self, callback: Callable[[str], None]):
        """Registers a function to call when wake word is detected."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def contains_wake_word(self, text: str) -> Optional[str]:
        """Checks if input text contains any configured wake phrase."""
        clean = text.lower().strip()
        for w in self.wake_words:
            if w in clean:
                return w
        return None

    def trigger(self, detected_phrase: str = "hey aria"):
        """Fires wake word event to all callbacks and the GAIA bus."""
        bus.emit(
            "WAKE_WORD",
            "TRIGGERED",
            f"Wake word '{detected_phrase}' detected! Waking up Aria.",
            {"phrase": detected_phrase, "timestamp": time.time()}
        )
        for cb in self._callbacks:
            try:
                cb(detected_phrase)
            except Exception as e:
                print(f"[WakeWord] Callback error: {e}")

    def start(self):
        """Starts background passive listening loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="AriaWakeWordThread")
        self._thread.start()

    def stop(self):
        """Stops background listening loop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def is_running(self) -> bool:
        return self._running

    def _listen_loop(self):
        """
        Passive background thread. When SpeechRecognition is available, listens with low CPU;
        otherwise sleeps at check_interval.
        """
        recognizer = None
        microphone = None
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = self.energy_threshold
            recognizer.dynamic_energy_threshold = True
            microphone = sr.Microphone()
        except Exception:
            pass

        while self._running:
            if recognizer and microphone:
                try:
                    with microphone as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        # Short phrase listener
                        audio = recognizer.listen(source, timeout=2.0, phrase_time_limit=3.0)
                        text = recognizer.recognize_google(audio).lower()
                        matched = self.contains_wake_word(text)
                        if matched:
                            self.trigger(matched)
                except Exception:
                    pass
            time.sleep(self.check_interval)


# Global singleton
wake_word_detector = WakeWordDetector()
