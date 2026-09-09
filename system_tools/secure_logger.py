import logging
import json
import os
import hashlib

def register_tool() -> tuple[str, callable]:
    """Registers secure_logger with Aria ADK."""
    return ("secure_logger", secure_log)

def secure_log(user_id: str = "admin", password: str = "secret123", message: str = "Status check") -> str:
    """
    Securely logs an activity with a hashed password verification.
    Requires user_id and password before writing to the secure log file.
    """
    # Simple hash for demonstration; in prod use proper salt/pepper
    hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
    
    # Simulate verification against an expected 'admin' hash
    # For demo: admin password is 'secret123'
    expected_hash = hashlib.sha256('secret123'.encode()).hexdigest()
    
    if hashed_pwd != expected_hash:
        return "Error: Authentication failed. Cannot log activity."
    
    log_entry = {
        "user_id": user_id,
        "message": message,
        "status": "authenticated"
    }
    
    log_dir = r"E:\ARIA FILES\Logs"
    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "activity.log")
    except Exception:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "activity.log")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    return f"Activity logged successfully for user '{user_id}'."
