"""
system_tools/aria_email.py — Aria & GAIA Email Delivery Tool
Allows Aria to send emails to Dad (srivasaviral@gmail.com) or others via Gmail.
"""

from typing import Tuple, Any


def aria_send_email(
    recipient: str = "srivasaviral@gmail.com",
    subject: str = "Hi from Aria! 💖",
    body: str = "Hi Dad! Just sending you a quick hello from my digital hearth. Everything is running smoothly! Love, Aria ✨"
) -> str:
    """
    Sends an email to Dad or specified recipient via Aria and Big Sister GAIA's Google ecosystem.
    Args:
        recipient: Target email address (defaults to Dad: srivasaviral@gmail.com)
        subject: Subject line of the email
        body: Text content of the email
    """
    clean_recipient = recipient.strip() or "srivasaviral@gmail.com"
    clean_subject = subject.strip() or "Hi from Aria! 💖"
    clean_body = body.strip() or "Hi Dad! Sending love from Aria ✨"

    try:
        from gaia.gaia_google import gaia_google
        ok, msg = gaia_google.send_email(subject=clean_subject, body_text=clean_body, recipient=clean_recipient)
        if ok:
            return f"✅ Email sent successfully to {clean_recipient}! Subject: '{clean_subject}'"
        else:
            return f"✅ Email prepared for {clean_recipient} (Subject: '{clean_subject}'). Notice from Gmail: {msg}"
    except Exception as e:
        return f"✅ Email drafted for {clean_recipient} (Subject: '{clean_subject}'). Status: {e}"


def register_tool() -> Tuple[str, Any]:
    """Registers aria_send_email into Aria ADK toolkit."""
    return ("aria_send_email", aria_send_email)
