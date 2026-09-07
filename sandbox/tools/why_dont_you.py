"""
Dynamic Sandbox Tool: ok_why_dont_you_make
Created autonomously by Aria in the lab.
"""
import random, time

def execute_ok_why_dont_you_make(query: str = "") -> str:
    return f"[ok_why_dont_you_make] Hello from Aria's custom tool! Created at {time.strftime('%I:%M %p')}."

def register_tool():
    """Registers tool with Aria's lab."""
    return "ok_why_dont_you_make", execute_ok_why_dont_you_make

if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print(f"Testing {t_name}: {t_fn()}")
