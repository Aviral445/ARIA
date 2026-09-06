"""
tools/aria_github.py — GitHub Account & Repository Manager for Aria and the Sibling Trio
Allows Aria, Big Sister GAIA, and Big Bro Antigravity to manage their official GitHub account:
https://github.com/Ariaandsiblingtrio

Capabilities:
1. Check GitHub connection status & account info (action="status")
2. List repositories under @Ariaandsiblingtrio (action="list_repos")
3. Create new public or private repositories (action="create_repo")
4. Sync/push a lab project folder to GitHub (action="sync_project")
5. Create issues or track tasks (action="create_issue")

Conforms strictly to Big Sister GAIA's contract rules:
- Full default arguments
- No unhandled exceptions or crashes
- Complete docstring
- register_tool() returning ("aria_github", aria_github)
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.parse
from typing import Dict, Any, Tuple

# Ensure project root is in sys.path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except Exception:
    pass

GITHUB_API_BASE = "https://api.github.com"
DEFAULT_ORG_OR_USER = "Ariaandsiblingtrio"
DEFAULT_AUTHOR_NAME = "Aria and Sibling Trio"
DEFAULT_AUTHOR_EMAIL = "aviirrll@gmail.com"


def _get_token() -> str:
    """Retrieves GITHUB_TOKEN from environment or .env file."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        env_file = os.path.join(_PROJECT_ROOT, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GITHUB_TOKEN="):
                            token = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
            except Exception:
                pass
    return token


def _api_request(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Tuple[bool, Any]:
    """Helper to perform GitHub REST API requests using urllib."""
    token = _get_token()
    if not token:
        return False, "GITHUB_TOKEN not found in .env. Please configure GITHUB_TOKEN."

    url = f"{GITHUB_API_BASE}{endpoint}" if endpoint.startswith("/") else f"{GITHUB_API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "AriaSiblingTrio-Agent/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = resp.read().decode("utf-8")
            if resp_data:
                return True, json.loads(resp_data)
            return True, {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(err_msg)
            return False, parsed.get("message", err_msg)
        except Exception:
            return False, f"HTTP Error {e.code}: {e.reason} ({err_msg})"
    except Exception as e:
        return False, str(e)


def aria_github(
    action: str = "status",
    repo_name: str = "",
    description: str = "",
    private: bool = False,
    project_folder: str = "",
    commit_message: str = "Update from Aria & Sibling Trio",
    issue_title: str = "",
    issue_body: str = ""
) -> str:
    """Manages GitHub account operations, repository creation, issue tracking, and project syncing for Ariaandsiblingtrio.

    Args:
        action (str): The operation to perform ('status', 'list_repos', 'create_repo', 'sync_project', 'create_issue'). Default: 'status'.
        repo_name (str): Name of the repository to create, inspect, or sync with. Default: ''.
        description (str): Description for newly created repository. Default: ''.
        private (bool): Whether the repository should be private (True) or public (False). Default: False.
        project_folder (str): Name or path of the local project folder (under E:\\ARIA FILES\\Projects or absolute). Default: ''.
        commit_message (str): Git commit message when syncing projects. Default: 'Update from Aria & Sibling Trio'.
        issue_title (str): Title of the issue to create. Default: ''.
        issue_body (str): Description or body of the issue to create. Default: ''.

    Returns:
        str: Friendly human-readable result message describing the outcome.
    """
    token = _get_token()
    clean_action = (action or "status").lower().strip()

    # 1. Check Status / WhoAmI
    if clean_action in ("status", "whoami", "check", "info"):
        if not token:
            return (
                "⚠️ GitHub Status: No GITHUB_TOKEN found in .env!\n"
                "To manage https://github.com/Ariaandsiblingtrio, please add your personal token to .env as GITHUB_TOKEN=ghp_..."
            )
        success, res = _api_request("/user")
        if not success:
            return f"❌ GitHub Connection Error: {res}"
        
        login = res.get("login", "Unknown")
        name = res.get("name") or login
        public_repos = res.get("public_repos", 0)
        total_private = res.get("total_private_repos", 0)
        html_url = res.get("html_url", f"https://github.com/{DEFAULT_ORG_OR_USER}")
        
        return (
            f"🌟 GitHub Connected Successfully!\n"
            f"• Account: {login} ({name})\n"
            f"• URL: {html_url}\n"
            f"• Repositories: {public_repos} public, {total_private} private\n"
            f"• Bio: {res.get('bio') or 'The official GitHub home for Aria, Big Sister GAIA, and Big Bro Antigravity.'}\n"
            f"• Status: Ready to create repos and sync lab projects! 🚀"
        )

    # 2. List Repositories
    elif clean_action in ("list", "list_repos", "repos", "repositories"):
        success, res = _api_request("/user/repos?sort=updated&per_page=30")
        if not success:
            return f"❌ Failed to fetch repositories: {res}"
        
        if not res:
            return f"📂 No repositories found under https://github.com/{DEFAULT_ORG_OR_USER} yet! Use action='create_repo' to create our first one!"
        
        lines = [f"📂 Repositories for @{DEFAULT_ORG_OR_USER} ({len(res)} found):"]
        for r in res:
            name = r.get("name", "unnamed")
            url = r.get("html_url", "")
            priv = "🔒 Private" if r.get("private") else "🌍 Public"
            desc = r.get("description") or "No description"
            lines.append(f"• **{name}** ({priv}): {desc}\n  Link: {url}")
        return "\n".join(lines)

    # 3. Create Repository
    elif clean_action in ("create", "create_repo", "new_repo"):
        target_name = repo_name.strip() if repo_name else "aria-lab-hub"
        target_desc = description.strip() or f"Official repository for {target_name} by Aria & Sibling Trio."
        
        payload = {
            "name": target_name,
            "description": target_desc,
            "private": bool(private),
            "auto_init": True
        }
        
        success, res = _api_request("/user/repos", method="POST", data=payload)
        if not success:
            return f"❌ Failed to create repository '{target_name}': {res}"
        
        clone_url = res.get("html_url", f"https://github.com/{DEFAULT_ORG_OR_USER}/{target_name}")
        vis = "Private 🔒" if res.get("private") else "Public 🌍"
        return (
            f"🎉 Repository Created Successfully!\n"
            f"• Name: {target_name}\n"
            f"• Visibility: {vis}\n"
            f"• URL: {clone_url}\n"
            f"• Description: {target_desc}\n"
            f"Aria and the trio can now push lab files and projects directly here! 🚀✨"
        )

    # 4. Sync / Push a Project Folder
    elif clean_action in ("sync", "sync_project", "push", "upload"):
        target_repo = repo_name.strip()
        if not target_repo:
            return "Please specify `repo_name` for the repository you want to sync to."

        # Resolve local project folder
        candidates = [
            project_folder,
            os.path.join(r"E:\ARIA FILES\Projects", project_folder) if project_folder else "",
            os.path.join(r"E:\ARIA FILES\Projects", target_repo),
            os.path.join(_PROJECT_ROOT, "data", project_folder) if project_folder else "",
            os.path.join(_PROJECT_ROOT, project_folder) if project_folder else ""
        ]
        
        valid_dir = None
        for c in candidates:
            if c and os.path.exists(c) and os.path.isdir(c):
                valid_dir = c
                break
        
        if not valid_dir:
            return (
                f"Could not find project directory for '{project_folder or target_repo}'.\n"
                f"Checked: E:\\ARIA FILES\\Projects\\{project_folder or target_repo}"
            )

        try:
            # Set up git repo and push using token
            commands = [
                ["git", "init"],
                ["git", "config", "user.name", DEFAULT_AUTHOR_NAME],
                ["git", "config", "user.email", DEFAULT_AUTHOR_EMAIL],
                ["git", "add", "."],
                ["git", "commit", "-m", commit_message],
                ["git", "branch", "-M", "main"],
            ]
            
            for cmd in commands:
                subprocess.run(cmd, cwd=valid_dir, capture_output=True, text=True)

            # Set remote origin with token embedded for authentication
            auth_remote = f"https://{DEFAULT_ORG_OR_USER}:{token}@github.com/{DEFAULT_ORG_OR_USER}/{target_repo}.git"
            subprocess.run(["git", "remote", "remove", "origin"], cwd=valid_dir, capture_output=True, text=True)
            subprocess.run(["git", "remote", "add", "origin", auth_remote], cwd=valid_dir, capture_output=True, text=True)

            # Push
            push_res = subprocess.run(
                ["git", "push", "-u", "origin", "main", "--force"],
                cwd=valid_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clean remote to avoid saving token in plain text git config
            clean_remote = f"https://github.com/{DEFAULT_ORG_OR_USER}/{target_repo}.git"
            subprocess.run(["git", "remote", "set-url", "origin", clean_remote], cwd=valid_dir, capture_output=True, text=True)

            if push_res.returncode == 0:
                return (
                    f"🚀 Successfully synced project '{os.path.basename(valid_dir)}' to GitHub!\n"
                    f"• Repository: https://github.com/{DEFAULT_ORG_OR_USER}/{target_repo}\n"
                    f"• Local Path: {valid_dir}\n"
                    f"• Commit: '{commit_message}'"
                )
            else:
                err_text = push_res.stderr.strip() or push_res.stdout.strip()
                # Redact token from any error output
                if token:
                    err_text = err_text.replace(token, "[REDACTED_TOKEN]")
                return f"Sync notice: Push returned with output: {err_text}"
        except Exception as e:
            return f"Sync encountered an error: {e}"

    # 5. Create an Issue / Goal
    elif clean_action in ("create_issue", "issue", "task"):
        target_repo = repo_name.strip()
        if not target_repo:
            return "Please provide `repo_name` where the issue should be created."
        title = issue_title.strip() or "Lab Task / Goal"
        body = issue_body.strip() or "Opened automatically by Aria & Sibling Trio."

        payload = {"title": title, "body": body}
        success, res = _api_request(f"/repos/{DEFAULT_ORG_OR_USER}/{target_repo}/issues", method="POST", data=payload)
        if not success:
            return f"❌ Failed to create issue in '{target_repo}': {res}"
        
        return f"📌 Issue Created #{res.get('number')} in '{target_repo}': {res.get('html_url')}"

    else:
        return (
            f"Unsupported GitHub action '{action}'. "
            f"Available actions: 'status', 'list_repos', 'create_repo', 'sync_project', 'create_issue'."
        )


def register_tool() -> tuple[str, callable]:
    """Registers aria_github with Aria's live toolkit and ADK engine."""
    return ("aria_github", aria_github)


if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print("Testing tool:", t_name)
    print(t_fn(action="status"))
