"""
core/aria_streaming.py — Streaming LLM Response & Real-Time Sentence TTS (Feature 43)
Streams tokens in real time from LLM providers, dynamically detects sentence boundaries,
and dispatches complete sentences immediately to the audio/TTS queue to minimize latency.
"""

import re
import time
import queue
import threading
from typing import Iterator, Generator, Callable, Optional, List


def clean_sentence_for_speech(text: str) -> str:
    """Removes markdown syntax, URLs, and code blocks for smooth TTS audio playback."""
    # Remove code blocks
    s = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Remove inline code
    s = re.sub(r'`[^`]*`', '', s)
    # Remove URLs
    s = re.sub(r'https?://\S+', '', s)
    # Remove Markdown headers, bold, italics
    s = re.sub(r'[*#_~>]+', '', s)
    # Normalize whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


class SentenceStreamer:
    """
    Buffers token chunks from a streaming LLM response and yields full,
    clean sentences as soon as punctuation boundaries ('.', '!', '?') are encountered.
    """
    def __init__(self, on_sentence_ready: Optional[Callable[[str], None]] = None):
        self.on_sentence_ready = on_sentence_ready
        self.buffer = ""
        self.full_response = ""
        self.sentences: List[str] = []

    def feed_token(self, token: str) -> List[str]:
        """
        Feeds a newly arrived token chunk. Returns list of any completed sentences
        that were emitted in this step.
        """
        self.buffer += token
        self.full_response += token
        completed = []

        # Sentence punctuation pattern (lookahead for space, quote, or end of string)
        # Matches: . ! ? followed by space, quote, or newline
        sentence_end_pattern = re.compile(r'([.!?]+[\'"\)]?)(?:\s+|\n|$)')

        while True:
            match = sentence_end_pattern.search(self.buffer)
            if not match:
                break

            end_pos = match.end()
            sentence = self.buffer[:end_pos].strip()
            self.buffer = self.buffer[end_pos:].lstrip()

            if sentence:
                clean_s = clean_sentence_for_speech(sentence)
                if clean_s:
                    self.sentences.append(clean_s)
                    completed.append(clean_s)
                    if self.on_sentence_ready:
                        try:
                            self.on_sentence_ready(clean_s)
                        except Exception as e:
                            print(f"[SentenceStreamer] Dispatch error: {e}")

        return completed

    def finalize(self) -> List[str]:
        """Flushes any remaining text in the buffer as the final sentence."""
        remaining = self.buffer.strip()
        self.buffer = ""
        completed = []
        if remaining:
            clean_s = clean_sentence_for_speech(remaining)
            if clean_s:
                self.sentences.append(clean_s)
                completed.append(clean_s)
                if self.on_sentence_ready:
                    try:
                        self.on_sentence_ready(clean_s)
                    except Exception as e:
                        print(f"[SentenceStreamer] Finalize dispatch error: {e}")
        return completed


def stream_generator_sentences(token_iterator: Iterator[str]) -> Generator[str, None, str]:
    """
    Generator that accepts an iterator of token strings and yields clean sentences.
    Returns the complete concatenated response string.
    """
    streamer = SentenceStreamer()
    for token in token_iterator:
        new_sentences = streamer.feed_token(token)
        for s in new_sentences:
            yield s

    final_sentences = streamer.finalize()
    for s in final_sentences:
        yield s

    return streamer.full_response
