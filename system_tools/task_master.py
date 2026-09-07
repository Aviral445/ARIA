import os

def register_tool() -> tuple[str, callable]:
    return ("task_master", task_master)

def task_master(action: str = "list", task: str = "") -> str:
    """Manages a simple task list. Actions: 'add', 'list', 'clear'."""
    try:
        from core.paths import DATA_DIR
        notes_dir = os.path.join(DATA_DIR, "notes")
    except Exception:
        notes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "notes")
    
    os.makedirs(notes_dir, exist_ok=True)
    file_path = os.path.join(notes_dir, "tasks.txt")
    
    clean_action = (action or "list").lower().strip()
    if clean_action == "add":
        if not task:
            return "Please provide a task description to add."
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(task.strip() + "\n")
        return f"Added task: {task.strip()}"
    elif clean_action in ("list", "show"):
        if not os.path.exists(file_path):
            return "No tasks yet! Your list is all clear."
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return f"📋 Current Tasks:\n{content}" if content else "No tasks yet! Your list is all clear."
    elif clean_action in ("clear", "delete"):
        if os.path.exists(file_path):
            os.remove(file_path)
        return "Task list cleared!"
    return f"Unknown action '{action}'. Use 'add', 'list', or 'clear'."
