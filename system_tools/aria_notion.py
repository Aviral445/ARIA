"""
system_tools/aria_notion.py — Notion Workspace & Task Manager Connector (Feature 39)
Interacts with the official Notion REST API to create tasks, query boards,
and read pages directly from voice or chat without external heavy SDKs.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional

from core.paths import ENV_FILE

NOTION_API_VERSION = "2022-06-28"


def _get_notion_credentials() -> Tuple[str, str]:
    """Retrieves NOTION_API_KEY and NOTION_DATABASE_ID from environment or config."""
    token = os.environ.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN", "")
    db_id = os.environ.get("NOTION_DATABASE_ID", "")
    return token.strip(), db_id.strip()


def _notion_request(endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any]:
    """Dispatches an authenticated HTTP request to Notion API."""
    token, _ = _get_notion_credentials()
    if not token:
        return False, "Notion API key not configured. Please set NOTION_API_KEY in .env."

    url = f"https://api.notion.com/v1/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json"
    }

    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return True, body
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        return False, f"Notion API error ({e.code}): {err_msg}"
    except Exception as e:
        return False, f"Notion connection failed: {e}"


def create_notion_task(title: str, status: str = "To Do", database_id: str = "") -> str:
    """Creates a new task item in a Notion database."""
    token, default_db = _get_notion_credentials()
    target_db = database_id or default_db

    if not token:
        # Mock/Offline preview mode for local verification
        return f"[Notion Demo] Task '{title}' staged (Status: {status}). Please configure NOTION_API_KEY in .env for live sync."

    if not target_db:
        return "Please set NOTION_DATABASE_ID in your .env file or pass database_id."

    payload = {
        "parent": {"database_id": target_db},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Status": {
                "select": {"name": status}
            }
        }
    }

    ok, res = _notion_request("pages", method="POST", payload=payload)
    if ok:
        url = res.get("url", "")
        return f"Successfully created Notion task: '{title}'! URL: {url}"
    return f"Failed to create task: {res}"


def list_notion_tasks(database_id: str = "", limit: int = 10) -> str:
    """Queries recent tasks from a Notion database."""
    token, default_db = _get_notion_credentials()
    target_db = database_id or default_db

    if not token or not target_db:
        return "Notion workspace not connected. Provide NOTION_API_KEY and NOTION_DATABASE_ID in .env."

    payload = {"page_size": limit}
    ok, res = _notion_request(f"databases/{target_db}/query", method="POST", payload=payload)
    if not ok:
        return f"Could not retrieve tasks: {res}"

    results = res.get("results", [])
    if not results:
        return "No tasks found in the configured Notion database."

    items = []
    for page in results:
        props = page.get("properties", {})
        title_prop = props.get("Name", {}).get("title", [])
        title_text = title_prop[0].get("text", {}).get("content", "Untitled") if title_prop else "Untitled"
        status = props.get("Status", {}).get("select", {}).get("name", "Unknown")
        items.append(f"- [{status}] {title_text}")

    return "📋 Notion Tasks:\n" + "\n".join(items)


def notion_tool(action: str = "status", title: str = "", status: str = "To Do", query: str = "") -> str:
    """
    Interacts with your Notion workspace to manage tasks, notes, and boards.
    Args:
        action: 'add_task', 'list_tasks', or 'status'.
        title: Title of the task to create.
        status: Task status ('To Do', 'In Progress', 'Done').
        query: Optional search keyword.
    """
    act = action.lower().strip()
    if act in ["add", "add_task", "create"]:
        if not title:
            return "Please specify a title for the Notion task."
        return create_notion_task(title, status=status)

    if act in ["list", "list_tasks", "read"]:
        return list_notion_tasks()

    token, db = _get_notion_credentials()
    status_str = "CONNECTED" if token else "OFFLINE (Missing NOTION_API_KEY)"
    return f"Notion Integration Status: {status_str}\nTarget Database: {db or 'Not configured'}"


def register_tool() -> Tuple[str, Any]:
    """Registers notion_tool into Aria ADK."""
    return ("notion_tool", notion_tool)
