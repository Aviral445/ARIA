"""
system_tools/aria_enterprise.py — Enterprise SaaS Connectors: Slack, Jira & GitHub (Feature 52)
Standardized REST and webhook integrations for Slack channel broadcasting, Jira issue tracking,
and unified enterprise workflow automation alongside the existing GitHub manager.
"""

import os
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional


def send_slack_message(text: str, channel: str = "", webhook_url: str = "") -> str:
    """Dispatches a message to Slack using incoming webhook or Bot Token."""
    resolved_webhook = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()

    # 1. Incoming Webhook path
    if resolved_webhook:
        payload = {"text": text}
        if channel:
            payload["channel"] = channel
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(resolved_webhook, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    return f"Slack message posted successfully: '{text[:50]}...'"
        except Exception as e:
            return f"Slack webhook error: {e}"

    # 2. Slack Web API path
    if bot_token:
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {"channel": channel or "#general", "text": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                if body.get("ok"):
                    return f"Slack message sent to {channel or '#general'}: '{text[:50]}...'"
                return f"Slack API returned error: {body.get('error')}"
        except Exception as e:
            return f"Slack connection error: {e}"

    # Mock / Demo fallback if credentials not yet configured
    return f"[Slack Demo] Staged message for Slack '{channel or '#general'}': '{text}'. (Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN in .env for live sync)"


def create_jira_issue(
    summary: str,
    description: str = "",
    project_key: str = "",
    issue_type: str = "Task"
) -> str:
    """Creates a new issue in Atlassian Jira Cloud."""
    base_url = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
    email = os.environ.get("JIRA_EMAIL", "").strip()
    api_token = os.environ.get("JIRA_API_TOKEN", "").strip()
    default_project = project_key or os.environ.get("JIRA_PROJECT_KEY", "PROJ").strip()

    if not (base_url and email and api_token):
        return f"[Jira Demo] Created {issue_type} in {default_project}: '{summary}' (Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env for live sync)"

    url = f"{base_url}/rest/api/3/issue"
    auth_str = base64.b64encode(f"{email}:{api_token}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "fields": {
            "project": {"key": default_project},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description or summary}]
                    }
                ]
            },
            "issuetype": {"name": issue_type}
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            key = body.get("key", "Unknown")
            return f"Successfully created Jira issue {key}: '{summary}'! URL: {base_url}/browse/{key}"
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        return f"Jira API error ({e.code}): {err}"
    except Exception as e:
        return f"Jira connection error: {e}"


def enterprise_saas_tool(
    platform: str = "slack",
    action: str = "send_message",
    text: str = "",
    channel: str = "",
    summary: str = "",
    description: str = "",
    project: str = ""
) -> str:
    """
    Unified Enterprise connector for Slack, Jira, and GitHub.
    Args:
        platform: 'slack', 'jira', or 'github'.
        action: 'send_message' (Slack), 'create_issue' (Jira/GitHub), 'status'.
        text: Message content for Slack.
        channel: Slack channel (e.g. '#engineering').
        summary: Jira/GitHub issue summary.
        description: Jira/GitHub issue description.
        project: Jira project key or GitHub repository.
    """
    plat = platform.lower().strip()
    act = action.lower().strip()

    if plat == "slack":
        msg = text or summary
        if not msg:
            return "Please provide text content for the Slack message."
        return send_slack_message(msg, channel=channel)

    if plat == "jira":
        summ = summary or text
        if not summ:
            return "Please provide a summary for the Jira issue."
        return create_jira_issue(summary=summ, description=description, project_key=project)

    if plat == "github":
        try:
            from system_tools.aria_github import aria_github
            return aria_github(action=act or "status", issue_title=summary, issue_body=description)
        except Exception as e:
            return f"GitHub tool error: {e}"

    return f"Platform '{platform}' not supported. Choose from 'slack', 'jira', or 'github'."


def register_tool() -> Tuple[str, Any]:
    """Registers enterprise_saas_tool into Aria ADK."""
    return ("enterprise_saas_tool", enterprise_saas_tool)
