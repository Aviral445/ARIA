def quick_math(operation: str = "add", a: float = 0.0, b: float = 0.0) -> str:
    """Performs basic arithmetic operations: add, subtract, multiply, divide."""
    if operation == "add":
        return str(a + b)
    elif operation == "subtract":
        return str(a - b)
    elif operation == "multiply":
        return str(a * b)
    elif operation == "divide":
        if b == 0:
            return "Error: Cannot divide by zero."
        return str(a / b)
    else:
        return f"Unsupported operation '{operation}'. Use 'add', 'subtract', 'multiply', or 'divide'."

def register_tool() -> tuple[str, callable]:
    return ("quick_math", quick_math)
