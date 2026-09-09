import os
import subprocess

def create_github_repo_safe(repo_name: str, description: str = "") -> str:
    """
    Creates a new GitHub repository using the gh CLI.
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "create", f"Ariaandsiblingtrio/{repo_name}", "--public", f"--description={description}"],
            capture_output=True, text=True, check=True
        )
        return f"Successfully created: {result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error creating repo: {e.stderr}"

def register_tool() -> tuple[str, callable]:
    return ("create_github_repo_safe", create_github_repo_safe)
