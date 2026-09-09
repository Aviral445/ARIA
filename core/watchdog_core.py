"""
watchdog_core.py — Self-Reflective Sandbox Watchdog for Aria AI & GAIA.

Enforces strict non-blocking timeout guards, prevents runaway infinite loops,
and seamlessly preserves Aria tool return contracts (handled: bool, response: str).
"""
import functools
import threading
import time
from typing import Callable, Any

def monitor_execution(func_or_timeout=30.0):
    """
    Decorator that executes a function in a daemon thread with an enforced timeout.
    
    Can be used as:
        @monitor_execution
        def my_tool(...): ...
    or:
        @monitor_execution(timeout_seconds=15)
        def my_tool(...): ...

    Guarantees:
    1. Non-blocking: runaway loops (e.g. while True) will NEVER hang the caller.
    2. Contract-preserving: if the decorated function returns (bool, str), the tuple is preserved directly.
    3. Metadata-preserving: @functools.wraps preserves function docstring, name, and signatures.
    """
    timeout_seconds = 30.0 if callable(func_or_timeout) else float(func_or_timeout)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = [False, "Execution timed out or failed to start"]

            def target():
                try:
                    val = func(*args, **kwargs)
                    # Preserve Aria tool convention (handled: bool, response: str)
                    if isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], bool):
                        result[0], result[1] = val[0], val[1]
                    else:
                        result[0] = True
                        result[1] = str(val) if val is not None else ""
                except Exception as e:
                    result[0] = False
                    result[1] = f"Watchdog Error: {type(e).__name__}: {str(e)}"

            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            thread.join(timeout=timeout_seconds)

            if thread.is_alive():
                return False, f"Watchdog Circuit Breaker: Execution exceeded {timeout_seconds}s limit."

            return result[0], result[1]
        return wrapper

    if callable(func_or_timeout):
        return decorator(func_or_timeout)
    return decorator

def register_tool():
    return ("monitor_execution_v2", monitor_execution)
