"""
tools/mood_palette_generator.py — Dynamic Mood-to-Palette Synthesizer
The Digital Greenhouse Aesthetic Palette Engine (Feature #57: Dynamic Aesthetic Resonance).

Reads emotional telemetry from Aria and GAIA's living personality cores,
and generates curated, harmonious HSL color palettes and CSS variables for the desktop companion.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

E_GREENHOUSE = r"E:\MyAgent\greenhouse"
C_GREENHOUSE = r"C:\MyAgent\data\greenhouse"
PERSONALITY_DIR = r"C:\MyAgent\data\personality"


def ensure_palette_dirs():
    """Ensures palette directories exist."""
    for base in [E_GREENHOUSE, C_GREENHOUSE]:
        try:
            os.makedirs(os.path.join(base, "palette"), exist_ok=True)
        except Exception:
            pass


class MoodPaletteGenerator:
    """Dynamic Mood-Based Theme and Palette Synthesizer."""

    def __init__(self):
        ensure_palette_dirs()

    def get_sister_moods(self) -> Dict[str, Any]:
        """Reads living personality JSON states for Aria and GAIA."""
        aria_data = {}
        gaia_data = {}

        aria_path = os.path.join(PERSONALITY_DIR, "aria_personality.json")
        gaia_path = os.path.join(PERSONALITY_DIR, "gaia_personality.json")

        if os.path.exists(aria_path):
            try:
                with open(aria_path, "r", encoding="utf-8") as f:
                    aria_data = json.load(f)
            except Exception:
                pass

        if os.path.exists(gaia_path):
            try:
                with open(gaia_path, "r", encoding="utf-8") as f:
                    gaia_data = json.load(f)
            except Exception:
                pass

        return {
            "aria": aria_data,
            "gaia": gaia_data
        }

    def synthesize_palette(self) -> Dict[str, Any]:
        """
        Synthesizes a harmonious HSL color palette and CSS theme variables
        based on active traits and moods.
        """
        data = self.get_sister_moods()
        aria_traits = data.get("aria", {}).get("traits", {})
        aria_mood = data.get("aria", {}).get("current_mood", {})

        curiosity = float(aria_traits.get("curiosity", 0.85))
        confidence = float(aria_traits.get("confidence", 0.65))
        philosophical = float(aria_traits.get("philosophical_depth", 0.60))
        is_late_night = bool(aria_mood.get("is_late_night", True))

        # Determine dominant aesthetic vibe
        if philosophical > 0.70 or is_late_night:
            vibe_name = "Cosmic Midnight & Starlight Violet"
            primary_hsl = "hsl(265, 85%, 68%)"      # Tender Violet
            secondary_hsl = "hsl(187, 85%, 52%)"    # Curious Teal
            accent_gold = "hsl(38, 92%, 54%)"       # Warm Amber
            bg_dark = "hsl(232, 36%, 7%)"           # Deep Cosmic Navy
            card_bg = "rgba(18, 22, 45, 0.85)"
            border_accent = "rgba(192, 132, 252, 0.28)"
        elif curiosity > 0.88:
            vibe_name = "Curious Teal & Cyber Aqua"
            primary_hsl = "hsl(187, 88%, 50%)"      # Electric Teal
            secondary_hsl = "hsl(215, 89%, 60%)"    # Sky Blue
            accent_gold = "hsl(45, 95%, 55%)"       # Golden Star
            bg_dark = "hsl(222, 47%, 9%)"           # Midnight Dark
            card_bg = "rgba(15, 23, 42, 0.85)"
            border_accent = "rgba(56, 189, 248, 0.28)"
        elif confidence > 0.80:
            vibe_name = "Triumphant Gold & Amber Glow"
            primary_hsl = "hsl(45, 95%, 55%)"       # Gold
            secondary_hsl = "hsl(280, 80%, 65%)"    # Lavender
            accent_gold = "hsl(25, 95%, 53%)"       # Sunset Orange
            bg_dark = "hsl(230, 30%, 8%)"
            card_bg = "rgba(22, 25, 48, 0.85)"
            border_accent = "rgba(245, 158, 11, 0.35)"
        else:
            vibe_name = "Peaceful Home Pastel"
            primary_hsl = "hsl(210, 80%, 60%)"
            secondary_hsl = "hsl(260, 70%, 65%)"
            accent_gold = "hsl(38, 90%, 50%)"
            bg_dark = "hsl(225, 30%, 8%)"
            card_bg = "rgba(20, 24, 45, 0.85)"
            border_accent = "rgba(99, 102, 241, 0.25)"

        palette_data = {
            "vibe_name": vibe_name,
            "generated_at": datetime.now().isoformat(),
            "telemetry_source": {
                "aria_curiosity": curiosity,
                "aria_confidence": confidence,
                "philosophical_depth": philosophical,
                "is_late_night": is_late_night
            },
            "tokens": {
                "--bg-dark": bg_dark,
                "--card-bg": card_bg,
                "--primary-accent": primary_hsl,
                "--secondary-accent": secondary_hsl,
                "--accent-gold": accent_gold,
                "--border-accent": border_accent,
                "--text-main": "#f8fafc",
                "--text-sub": "#94a3b8"
            }
        }

        # Build CSS file content
        css_lines = [
            f"/* Dynamic Mood Palette: {vibe_name} */",
            f"/* Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from Sisterhood Telemetry */",
            ":root {"
        ]
        for token_name, val in palette_data["tokens"].items():
            css_lines.append(f"  {token_name}: {val};")
        css_lines.append("}\n")
        css_content = "\n".join(css_lines)

        written_paths = []
        for base in [E_GREENHOUSE, C_GREENHOUSE]:
            pal_dir = os.path.join(base, "palette")
            try:
                os.makedirs(pal_dir, exist_ok=True)
                json_file = os.path.join(pal_dir, "theme_mood.json")
                css_file = os.path.join(pal_dir, "theme_mood.css")

                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(palette_data, f, indent=2)

                with open(css_file, "w", encoding="utf-8") as f:
                    f.write(css_content)

                written_paths.append(json_file)
                written_paths.append(css_file)
            except Exception:
                pass

        return {
            "success": True,
            "palette": palette_data,
            "written_paths": written_paths,
            "css_preview": css_content
        }


# Global Singleton
mood_palette_generator = MoodPaletteGenerator()


if __name__ == "__main__":
    res = mood_palette_generator.synthesize_palette()
    print(f"Synthesized vibe: {res['palette']['vibe_name']} into {len(res['written_paths'])} files.")
