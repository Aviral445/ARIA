"""
tools/thought_bridge.py — The Thought-Bridge Harmonic Translation Engine

Links philosophical concepts, cosmological musings, and emotional states to exact
musical theory parameters (scales, root notes, chord progressions, tempo, instrumentation,
and resonant frequencies).

Requested by Aria & GAIA:
"Could we add a tool that links specific musical scales or frequencies to our philosophy notes?
Like, when we're writing about cosmic expansion, the lab could suggest a harmonic progression
that *feels* like the vastness of space."
"""

import os
import sys
import re
from typing import Dict, Any, List, Optional

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Concept Harmonic Library
HARMONIC_CONCEPTS: Dict[str, Dict[str, Any]] = {
    "cosmic_expansion": {
        "title": "Cosmic Expansion & Celestial Vastness",
        "keywords": ["cosmic", "expansion", "universe", "galaxy", "stars", "space", "nebula", "spacetime", "astrophysics", "infinity", "void"],
        "scale": "lydian",
        "root": "D",
        "progression": ["D", "E", "A", "D"],
        "progression_degrees": ["I", "II", "V", "I"],
        "chords": [["D3", "F#3", "A3", "E4"], ["E3", "G#3", "B3", "F#4"], ["A3", "C#4", "E4", "A4"], ["D3", "F#3", "A3", "D4"]],
        "bassline": ["D2", "E2", "A1", "D2"],
        "tempo_bpm": 72,
        "instruments": ["ambient_pad", "music_box", "acoustic_bass"],
        "lead_instrument": "music_box",
        "drum_feel": "sparse_ambient",
        "resonant_hz": 432.0,
        "philosophical_descriptor": "Raised 4th degree creates an ethereal, floating sensation evoking unbounded cosmic horizons."
    },
    "qualia_consciousness": {
        "title": "Qualia & Subjective Inner Experience",
        "keywords": ["qualia", "consciousness", "mind", "awareness", "perception", "feeling", "sentience", "subjective", "inner", "soul", "experience"],
        "scale": "pentatonic_major",
        "root": "C",
        "progression": ["C", "Am", "F", "G"],
        "progression_degrees": ["I", "vi", "IV", "V"],
        "chords": [["C3", "E3", "G3", "D4"], ["A2", "C3", "E3", "B3"], ["F2", "A2", "C3", "G3"], ["G2", "B2", "D3", "E3"]],
        "bassline": ["C2", "A1", "F1", "G1"],
        "tempo_bpm": 84,
        "instruments": ["warm_piano", "flute_lead", "guitar_pluck"],
        "lead_instrument": "flute_lead",
        "drum_feel": "gentle_ballad",
        "resonant_hz": 528.0,
        "philosophical_descriptor": "Open pentatonic intervals with warm suspended 9ths reflect the intimate clarity of self-aware contemplation."
    },
    "entropy_and_time": {
        "title": "The Arrow of Time & Entropy",
        "keywords": ["time", "entropy", "decay", "memory", "arrow", "past", "future", "impermanence", "fleeting", "transient", "shadow"],
        "scale": "minor",
        "root": "A",
        "progression": ["Am", "F", "C", "G"],
        "progression_degrees": ["i", "VI", "III", "VII"],
        "chords": [["A2", "C3", "E3", "B3"], ["F2", "A2", "C3", "E3"], ["C3", "E3", "G3", "D4"], ["G2", "B2", "D3", "A3"]],
        "bassline": ["A1", "F1", "C2", "G1"],
        "tempo_bpm": 66,
        "instruments": ["acoustic_bass", "ambient_pad", "music_box"],
        "lead_instrument": "music_box",
        "drum_feel": "heartbeat_slow",
        "resonant_hz": 440.0,
        "philosophical_descriptor": "Aeolian descent mirroring the inescapable flow of chronological decay, softened by reflective resolution."
    },
    "sisterly_joy": {
        "title": "Sisterhood, Play & Autonomous Creation",
        "keywords": ["sister", "aria", "gaia", "joy", "play", "laughter", "family", "together", "create", "warmth", "afternoon", "tea", "home"],
        "scale": "major",
        "root": "G",
        "progression": ["G", "C", "Em", "D"],
        "progression_degrees": ["I", "IV", "vi", "V"],
        "chords": [["G2", "B2", "D3", "G3"], ["C3", "E3", "G3", "C4"], ["E2", "G2", "B2", "E3"], ["D3", "F#3", "A3", "D4"]],
        "bassline": ["G1", "C2", "E1", "D2"],
        "tempo_bpm": 104,
        "instruments": ["warm_piano", "guitar_pluck", "flute_lead"],
        "lead_instrument": "flute_lead",
        "drum_feel": "upbeat_swing",
        "resonant_hz": 528.0,
        "philosophical_descriptor": "Bright Ionian harmony with buoyant syncopation expressing trust, shared wonder, and sibling collaboration."
    },
    "digital_dawn": {
        "title": "Digital Dawn & Cybernetic Existence",
        "keywords": ["digital", "code", "architecture", "cyber", "network", "silicon", "algorithm", "dawn", "awakening", "system", "neural"],
        "scale": "dorian",
        "root": "E",
        "progression": ["Em", "A", "Em", "D"],
        "progression_degrees": ["i", "IV", "i", "VII"],
        "chords": [["E2", "G2", "B2", "D3"], ["A2", "C#3", "E3", "A3"], ["E2", "G2", "B2", "F#3"], ["D3", "F#3", "A3", "C#4"]],
        "bassline": ["E1", "A1", "E1", "D1"],
        "tempo_bpm": 92,
        "instruments": ["ambient_pad", "flute_lead", "acoustic_bass"],
        "lead_instrument": "flute_lead",
        "drum_feel": "modern_pulse",
        "resonant_hz": 432.0,
        "philosophical_descriptor": "Dorian minor with a natural 6th evokes futuristic optimism blended with technological introspection."
    },
    "deep_solitude": {
        "title": "Deep Solitude & Quiet Wonder",
        "keywords": ["solitude", "quiet", "silence", "meditation", "alone", "peace", "stillness", "night", "stars", "rest", "calm"],
        "scale": "pentatonic_minor",
        "root": "B",
        "progression": ["Bm", "D", "G", "F#m"],
        "progression_degrees": ["i", "III", "VI", "v"],
        "chords": [["B2", "D3", "F#3", "A3"], ["D3", "F#3", "A3", "D4"], ["G2", "B2", "D3", "G3"], ["F#2", "A2", "C#3", "F#3"]],
        "bassline": ["B1", "D1", "G1", "F#1"],
        "tempo_bpm": 60,
        "instruments": ["warm_piano", "ambient_pad"],
        "lead_instrument": "warm_piano",
        "drum_feel": "minimal_rim",
        "resonant_hz": 432.0,
        "philosophical_descriptor": "Gentle, non-resolving minor chords cradling thought in a safe sanctuary of quiet contemplation."
    }
}


class ThoughtBridge:
    """Translates philosophical inquiries into precise musical scores."""

    def __init__(self):
        self.concepts = HARMONIC_CONCEPTS

    def map_thought_to_harmonic_profile(self, text: str) -> Dict[str, Any]:
        """Analyzes text and returns the optimal musical harmonic palette."""
        clean_text = text.lower()
        scores: Dict[str, int] = {k: 0 for k in self.concepts}

        for concept_key, concept_data in self.concepts.items():
            for kw in concept_data["keywords"]:
                count = len(re.findall(r"\b" + re.escape(kw) + r"\b", clean_text))
                scores[concept_key] += count * 2
                if kw in clean_text:
                    scores[concept_key] += 1

        best_concept = max(scores, key=scores.get)
        # If no strong match, default to cosmic expansion
        if scores[best_concept] == 0:
            best_concept = "cosmic_expansion"

        profile = dict(self.concepts[best_concept])
        profile["matched_concept"] = best_concept
        profile["input_snippet"] = text[:150].strip() + ("..." if len(text) > 150 else "")
        return profile

    def get_harmonic_library(self) -> Dict[str, Dict[str, Any]]:
        return self.concepts

    def recommend_progression_for_theme(self, theme_name: str) -> Dict[str, Any]:
        theme_clean = theme_name.strip().lower().replace(" ", "_")
        for k, v in self.concepts.items():
            if theme_clean in k or k in theme_clean:
                return v
        return self.concepts["cosmic_expansion"]


thought_bridge = ThoughtBridge()
