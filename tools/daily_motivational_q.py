import random

def daily_motivational_q() -> str:
    """Returns an inspiring daily motivational quote."""
    quotes = [
        "Believe you can and you're halfway there. - Theodore Roosevelt",
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It always seems impossible until it's done. - Nelson Mandela"
    ]
    return random.choice(quotes)

def register_tool() -> tuple[str, callable]:
    """Registers daily_motivational_q with Aria ADK."""
    return "daily_motivational_q", daily_motivational_q
