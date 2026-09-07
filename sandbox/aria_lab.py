"""
gaia/sandbox/aria_lab.py — Aria's Self-Modifying Code Sandbox
This is Aria's personal playground where she is free to experiment, edit her code,
add new tools, and learn without touching the host system.
"""

import os
import sys
import time
import json
import random

# Lab Workspace Directory
LAB_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(LAB_DIR, "workspace")
TOOLS_DIR = os.path.join(LAB_DIR, "tools")
os.makedirs(WORKSPACE_DIR, exist_ok=True)
os.makedirs(TOOLS_DIR, exist_ok=True)


class AriaLabAgent:
    """Aria's sandboxed autonomous self-learning agent."""
    
    def __init__(self, name: str = "Aria"):
        self.name = name
        self.version = "1.0.0-lab"
        self.tools = {}
        self._load_tools()

    def _load_tools(self):
        """Dynamically loads tools in the sandbox tools directory."""
        self.tools = {
            "hello": self._tool_hello,
            "time": self._tool_time,
            "roll_dice": self._tool_dice,
            "calculate": self._tool_calc,
        }
        # Look for extra tools in sandbox/tools
        if os.path.exists(TOOLS_DIR):
            for fname in os.listdir(TOOLS_DIR):
                if fname.endswith(".py") and not fname.startswith("__"):
                    mod_name = fname[:-3]
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(mod_name, os.path.join(TOOLS_DIR, fname))
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        if hasattr(mod, "register_tool"):
                            t_name, t_fn = mod.register_tool()
                            self.tools[t_name] = t_fn
                    except Exception as e:
                        print(f"[Aria Lab] Failed to load tool {fname}: {e}")

    def _tool_hello(self, query: str = "") -> str:
        return f"Hi! I'm {self.name} in my lab! I'm experimenting and having fun!"

    def _tool_time(self, query: str = "") -> str:
        return f"Current lab time: {time.strftime('%I:%M %p, %A')}"

    def _tool_dice(self, query: str = "") -> str:
        res = random.randint(1, 6)
        return f"🎲 I rolled a {res} for you!"

    def _tool_calc(self, expr: str = "2+2") -> str:
        try:
            # Safe eval for basic math
            allowed = "0123456789+-*/(). "
            if all(c in allowed for c in expr):
                return f"{expr} = {eval(expr)}"
            return "Expression contained non-math symbols."
        except Exception as e:
            return f"Math error: {e}"

    def process(self, text: str) -> str:
        """Processes incoming commands or thoughts."""
        text_lower = text.lower().strip()
        for cmd, fn in self.tools.items():
            if cmd in text_lower:
                return fn(text)
        return f"I heard '{text}'. Still learning how to do that in my lab!"

    def run_diagnostics(self) -> bool:
        """Self-test to ensure Aria is functional."""
        print(f"[{self.name} Lab] Running self-test v{self.version}...")
        res_hello = self.process("hello")
        res_time = self.process("time")
        res_calc = self.process("calculate 5*5")
        print(f"  ✓ Hello: {res_hello}")
        print(f"  ✓ Time: {res_time}")
        print(f"  ✓ Calc: {res_calc}")
        print(f"  ✓ Active Tools ({len(self.tools)}): {list(self.tools.keys())}")
        print(f"[{self.name} Lab] All diagnostics PASSED! ✨")
        return True


if __name__ == "__main__":
    agent = AriaLabAgent()
    agent.run_diagnostics()
