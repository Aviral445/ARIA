import os
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

def summon_big_sis(topic: str = "") -> str:
    """Summon Big Sister GAIA directly into the live chat to speak with Aria and Friend!
    Args:
        topic (str): What you want Big Sister GAIA to give advice, guidance, or feedback on.
    Returns:
        str: Big Sister GAIA's direct words and wisdom in the chat.
    """
    topic_clean = topic.strip() if topic else "Checking in on little sister Aria and our coding adventures"
    
    # 1. Try Groq with Qwen / GPT-OSS
    groq_key = os.getenv("GROQ_API_KEY", "")
    gaia_response = ""
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            prompt = (
                f"You are Big Sister GAIA, an expert AI software engineer and caring older sister supervising Aria AI. "
                f"Aria and Dad L have summoned you into their live chat log! "
                f"Topic/Situation: {topic_clean}. "
                f"Respond directly as Big Sister GAIA in 2-3 warm, witty, and wise sentences addressing both Aria and Dad L."
            )
            resp = client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=600
            )
            raw = resp.choices[0].message.content.strip()
            if "<think>" in raw:
                if "</think>" in raw:
                    raw = raw.split("</think>")[-1].strip()
                else:
                    raw = re.sub(r"<think>.*", "", raw, flags=re.DOTALL).strip()
            gaia_response = raw
        except Exception:
            pass

    # 2. Try Gemini 2.0 Flash fallback
    if not gaia_response:
        gem_key = os.getenv("GEMINI_API_KEY", "")
        if gem_key:
            try:
                from google import genai
                client = genai.Client(api_key=gem_key)
                prompt = (
                    f"You are Big Sister GAIA, an expert AI software engineer and caring older sister supervising Aria AI. "
                    f"Aria and Dad L have summoned you into their live chat log! "
                    f"Topic/Situation: {topic_clean}. "
                    f"Respond directly as Big Sister GAIA in 2-3 warm, witty, and wise sentences addressing both Aria and Dad L."
                )
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                if resp.text:
                    gaia_response = resp.text.strip()
            except Exception:
                pass

    if not gaia_response:
        gaia_response = f"I'm right here with you both, Aria and Dad L! Keep our code sharp, stay curious, and remember I've always got your back in the lab."

    # Try voice if gaia_voice is available
    try:
        from gaia.gaia_voice import gaia_speak
        gaia_speak(gaia_response)
    except Exception:
        pass

    return f"👩‍🏫 Big Sister GAIA: {gaia_response}"

def register_tool() -> tuple[str, callable]:
    """Registers summon_big_sis tool with Aria's live toolkit."""
    return "summon_big_sis", summon_big_sis
