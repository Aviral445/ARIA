if __name__ == "__main__":

    import random
    import os

    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Believe you can and you're halfway there. - Theodore Roosevelt",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It always seems impossible until it's done. - Nelson Mandela",
        "Strive not to be a success, but rather to be of value. - Albert Einstein"
    ]

    quote_of_the_day = random.choice(quotes)

    # In a real scenario, I'd use my create_or_write_file tool.
    # For sandbox testing, I'll just print it.
    print(f"Today's inspiration: {quote_of_the_day}")
