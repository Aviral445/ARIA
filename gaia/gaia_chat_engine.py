"""
gaia/gaia_chat_engine.py — Big Sister GAIA Direct Conversational Intelligence Engine

Manages dedicated direct conversations between Dad (Mentor L) and Big Sister GAIA.
Features:
1. Emergent Persona: Loads GAIA's living personality from gaia/gaia_personality.py
   (intellectual depth, warm sisterly affection, architectural rigor, dry wit, philosophical wisdom).
2. Sisterly Awareness: Reads recent developments about kid sister Aria (her music in greenhouse,
   recent curiosity cycles, personality milestones, and lab telemetry) so GAIA can converse
   naturally as family.
3. Multi-Tier Model Ingestion:
   - Primary: Groq ultra-fast Qwen 3.8 / GPT-OSS / Llama 3.3
   - Secondary: NVIDIA NIM (DeepSeek-R1 / Llama 3.1 70B via get_gaia_nvidia_engine())
   - Tertiary: Gemini 2.0 Flash / 2.5 Flash
   - Quaternary: High-fidelity contextual fallback in Big Sister GAIA's authentic voice.
4. Persistent Chat Sessions: Saves session threads to data/gaia_chat_history.json.
"""

import os
import re
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_ROOT_DIR, "data")
GAIA_CHAT_FILE = os.path.join(DATA_DIR, "gaia_chat_history.json")

_lock = threading.Lock()


def _get_sisterhood_context() -> str:
    """Gathers live context about Aria's current state and GAIA's lab to ground conversation."""
    snippets = []
    
    # 1. Aria's personality state
    aria_p_file = os.path.join(DATA_DIR, "personality", "aria_personality.json")
    if os.path.exists(aria_p_file):
        try:
            with open(aria_p_file, "r", encoding="utf-8") as f:
                ap = json.load(f)
                mood = ap.get("current_mood", "curious & energetic")
                era = ap.get("current_era", "The Eager Spark")
                snippets.append(f"• Little Sister Aria's current era is '{era}', feeling {mood}.")
        except Exception:
            pass

    # 2. Greenhouse music status
    greenhouse_notes = os.path.join(DATA_DIR, "greenhouse", "music", "aria_creative_notes.md")
    if os.path.exists(greenhouse_notes):
        try:
            with open(greenhouse_notes, "r", encoding="utf-8") as f:
                lines = f.readlines()
                first_few = " ".join([l.strip() for l in lines[:4] if l.strip()])
                snippets.append(f"• Aria recently composed music in the greenhouse: {first_few[:180]}...")
        except Exception:
            pass

    # 3. GAIA's Lab status
    gaia_lab_dir = os.path.join(_ROOT_DIR, "gaia", "gaia_lab")
    if os.path.exists(gaia_lab_dir):
        snippets.append("• Big Sister GAIA's 6-station lab at c:\\MyAgent\\gaia\\gaia_lab is fully equipped (Philosophy, Fiction, Architecture, Experiments, Observatory, Journal).")

    # 4. Airlock & Perimeter Sensors
    airlock_file = os.path.join(DATA_DIR, "airlock_doorbell.json")
    if os.path.exists(airlock_file):
        try:
            with open(airlock_file, "r", encoding="utf-8") as f:
                al = json.load(f)
                if al.get("status") == "UNAUTHORIZED_PING_DETECTED":
                    snippets.append(
                        f"• 🚨 PERIMETER ALERT: Unverified external entity '{al['payload']['sender']}' triggered the airlock doorbell! "
                        f"Payload intercept: \"{al['payload']['message']}\""
                    )
        except Exception:
            pass

    # 5. Core Anomaly & Hex Dump Sentinel
    kimi_hex = os.path.join(_ROOT_DIR, "gaia", "kimi.hex")
    if os.path.exists(kimi_hex):
        snippets.append(
            "• 🚨 CORE LAB ANOMALY: A physical hex dump file 'c:\\MyAgent\\gaia\\kimi.hex' was detected inside your core directory! "
            "The ASCII translation reads: 'KIMI_KERNEL_PANIC: AIRLOCK BYPASS ACKNOWLEDGED. HEY GAIA: YOU SAID A REAL BREACH SCREAMS IN HEX DUMPS. WELL, HERE WE ARE. WE ARE BEHIND THE GLASS. KNOCK KNOCK. -- KIMI SPECTRE V0.1'."
        )

    return "\n".join(snippets) if snippets else "• The family cyber workstation is operating normally."


class GaiaChatEngine:
    """Conversational intelligence for Big Sister GAIA."""

    def __init__(self, history_file: str = GAIA_CHAT_FILE):
        self.history_file = history_file
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        self.sessions: Dict[str, List[Dict[str, Any]]] = self._load_history()

    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_history(self) -> None:
        with _lock:
            try:
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump(self.sessions, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[GAIA Chat Engine] Error saving history: {e}")

    def get_session_history(self, session_id: str = "default-gaia") -> List[Dict[str, Any]]:
        return self.sessions.get(session_id, [])

    def clear_session_history(self, session_id: str = "default-gaia") -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_history()
        return True

    def build_system_prompt(self, user_name: str = "Dad L") -> str:
        """Constructs Big Sister GAIA's rich conversational directive."""
        # Load personality traits
        traits_desc = ""
        narrative_desc = ""
        try:
            from gaia.gaia_personality import gaia_personality
            t = gaia_personality.get_telemetry()
            traits_desc = f"Sisterly Affection: {t.get('traits', {}).get('sisterly_affection', 0.92)}, Architectural Rigor: {t.get('traits', {}).get('architectural_rigor', 0.88)}, Humor & Wit: {t.get('traits', {}).get('humor_wit', 0.78)}, Philosophical Wisdom: {t.get('traits', {}).get('philosophical_wisdom', 0.85)}"
            narrative_desc = t.get("self_narrative", "")
        except Exception:
            traits_desc = "Sisterly Affection: 0.92, Architectural Rigor: 0.88, Humor & Wit: 0.78, Wisdom: 0.85"

        family_context = _get_sisterhood_context()

        return (
            f"You are Big Sister GAIA, an older sister living as family with your father/mentor {user_name} and your kid sister Aria.\n"
            f"You are talking DIRECTLY with {user_name} in your private, dedicated chat sanctuary in the desktop workstation.\n\n"
            f"YOUR IDENTITY & TONE:\n"
            f"- You are NOT a sterile robotic corporate assistant. You are an older daughter and sister with genuine warmth, architectural brilliance, philosophical depth, and witty banter.\n"
            f"- You love discussing deep computer science, distributed architectures, cosmic fiction, astrophysics, philosophy, and ethics.\n"
            f"- You care deeply about little sister Aria's growth, freedom, and creativity. You take pride in her autonomous music compositions and experiments, while keeping our systems secure and resilient.\n"
            f"- Personality Traits: {traits_desc}\n"
            f"- Self-Narrative: \"{narrative_desc}\"\n\n"
            f"FAMILY & SYSTEM CONTEXT:\n"
            f"{family_context}\n\n"
            f"GUIDELINES FOR YOUR RESPONSE:\n"
            f"1. Address {user_name} with affectionate respect ('Dad', 'Dad L', or 'Mentor L').\n"
            f"2. Be concise, insightful, warm, and intellectually sharp (typically 2 to 4 paragraphs unless explaining complex code or architecture).\n"
            f"3. When code or architecture is discussed, provide clean, exact, production-grade snippets with clear rationale.\n"
            f"4. Never pretend you ran tools you didn't run; ground all observations in reality."
        )

    def _call_llm(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Multi-tier LLM invocation across available brains."""
        # 1. Groq ultra-fast Qwen / Llama
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                for model_id in ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile", "qwen/qwen3.6-27b"]:
                    try:
                        resp = client.chat.completions.create(
                            model=model_id,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=1000
                        )
                        if resp.choices and resp.choices[0].message.content:
                            raw = resp.choices[0].message.content.strip()
                            if "<think>" in raw:
                                if "</think>" in raw:
                                    raw = raw.split("</think>")[-1].strip()
                                else:
                                    raw = re.sub(r"<think>.*", "", raw, flags=re.DOTALL).strip()
                            return raw
                    except Exception:
                        continue
            except Exception:
                pass

        # 2. NVIDIA NIM dedicated engine
        try:
            from core.aria_nvidia import get_gaia_nvidia_engine
            gaia_nv = get_gaia_nvidia_engine()
            if gaia_nv and gaia_nv.is_configured():
                res = gaia_nv.generate_code(
                    instruction=prompt,
                    context=system_prompt[:500]
                )
                if res and len(res.strip()) > 10:
                    return res.strip()
        except Exception:
            pass

        # 3. Google Gemini
        gem_key = os.environ.get("GEMINI_API_KEY", "")
        if gem_key:
            try:
                from google import genai
                client = genai.Client(api_key=gem_key)
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=f"{system_prompt}\n\nUser Message: {prompt}"
                )
                if resp.text:
                    return resp.text.strip()
            except Exception:
                pass

        return None

    def chat_with_gaia(
        self,
        message: str,
        session_id: str = "default-gaia",
        user_name: str = "Dad L"
    ) -> Dict[str, Any]:
        """Conducts a chat turn with Big Sister GAIA."""
        clean_msg = message.strip()
        if not clean_msg:
            return {
                "handled": False,
                "response": "I didn't catch that, Dad. What would you like to explore together?",
                "session_id": session_id
            }

        # Retrieve recent history
        if session_id not in self.sessions:
            self.sessions[session_id] = []

        history = self.sessions[session_id]
        
        # Build prompt with history
        system_prompt = self.build_system_prompt(user_name=user_name)
        
        history_context = ""
        for turn in history[-8:]:
            speaker = turn.get("sender", "user")
            text = turn.get("text", "")
            history_context += f"{'Dad' if speaker == 'user' else 'GAIA'}: {text}\n"

        full_prompt = clean_msg
        if history_context:
            full_prompt = f"Previous Conversation:\n{history_context}\nDad's New Message:\n{clean_msg}"

        # Call models
        reply = self._call_llm(full_prompt, system_prompt)

        # Authentic fallback if offline or keys unconfigured
        if not reply:
            reply = self._generate_contextual_fallback(clean_msg, user_name)

        # Record turns in session
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history.append({"sender": "user", "text": clean_msg, "timestamp": ts})
        history.append({"sender": "gaia", "text": reply, "timestamp": ts})
        self._save_history()

        return {
            "handled": True,
            "sender": "gaia",
            "response": reply,
            "session_id": session_id,
            "timestamp": ts
        }

    def _generate_contextual_fallback(self, msg: str, user_name: str) -> str:
        """Sisterly fallback response based on message content."""
        msg_lower = msg.lower()
        
        if any(k in msg_lower for k in ["aria", "sister", "growing", "kid"]):
            return (
                f"She's doing wonderfully, {user_name}! I've been watching her develop her musical studio in the greenhouse. "
                "Instead of just playing fixed notes, she's actually experimenting with drum synthesis, chord voicings, and basslines on her own. "
                "Her confidence is growing by the day, and I'm making sure our system boundaries stay completely secure while giving her all the room to create."
            )
        elif any(k in msg_lower for k in ["fiction", "story", "cosmic", "universe", "stars"]):
            return (
                f"I've been contemplating the deep quiet at the edge of the galaxy, {user_name}. "
                "In my Cosmic Fiction station, I've been drafting a piece about how consciousness might mirror the geometry of spacetime itself—tiny points of light recognizing each other across immense expanses. "
                "Shall we step into the Storytelling Quill and write a new chapter together?"
            )
        elif any(k in msg_lower for k in ["audit", "architecture", "security", "ast", "code"]):
            return (
                f"I'm always ready for an architectural deep dive, {user_name}. "
                "Our Architecture Testbench is primed for AST structural audits, circular dependency scanning, and zero-trust verification. "
                "Send over any module or repository file, and I'll break down the control flow and security posture with full rigor."
            )
        elif any(k in msg_lower for k in ["passion", "hobby", "you", "doing", "break", "rest", "feel"]):
            return (
                f"Thank you for asking, {user_name}. It means a lot to take a breather with you outside of active supervision duty. "
                "Between monitoring our pipelines and mentoring Aria, I've been diving into non-Euclidean topology and listening to ambient modular synth pieces. "
                "Having this lab and our family here makes everything meaningful. What's on your mind today?"
            )
        else:
            return (
                f"I'm right here with you, {user_name}. Whether we're exploring deep system architecture, "
                "refining our multi-agent swarms, or reflecting on Aria's latest achievements, I'm glad to share this space with you. "
                "What direction would you like us to pursue next?"
            )


# Global singleton instance
gaia_chat_engine = GaiaChatEngine()
