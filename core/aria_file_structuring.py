r"""
core/aria_file_structuring.py — Sandboxed Hierarchical File Structuring Engine for Aria

Anchored in E:\ARIA FILES (or fallback data/aria_files).
Teaches and enforces the File Structuring Skill:
    Main Folder (Category/Domain) ──> Subfolder (Project/Topic) ──> Nested Folders / Files

Strict Boundary Sandbox (Jail):
    All operations are strictly jailed inside ARIA_FILES_DIR. Any attempt to traverse
    outside (e.g. via '..', absolute paths to C:, or symlinks) is blocked with a security violation.
"""

import os
import re
import json
import shutil
import subprocess
from typing import Optional, List, Dict, Tuple, Any, Union

try:
    from .paths import ARIA_FILES_DIR
except ImportError:
    try:
        from paths import ARIA_FILES_DIR
    except ImportError:
        ARIA_FILES_DIR = r"E:\ARIA FILES" if (os.path.exists(r"E:\ARIA FILES") or os.path.exists("E:\\")) else os.path.join(os.getcwd(), "data", "aria_files")

os.makedirs(ARIA_FILES_DIR, exist_ok=True)

# Recommended Standard Categories for Aria
STANDARD_MAIN_FOLDERS = [
    "Projects",    # Active software, automations, coding projects
    "Documents",   # Reports, summaries, structured documents, guides
    "Notes",       # Thoughts, daily logs, meeting minutes, journal
    "Code",        # Polyglot scripts, tools, modules, snippets
    "Creative",    # Stories, poems, ideas, brainstorms, concepts
    "Research",    # Academic papers, study notes, technology research
    "Archive"      # Completed projects, historical records, backups
]


def _sanitize_name(name: str) -> str:
    """Sanitizes a folder or file name by stripping dangerous or invalid Windows characters."""
    if not name:
        return ""
    # Remove Windows illegal chars: < > : " / \ | ? *
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', name.strip())
    # Collapse multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned).strip(' ._')
    return cleaned or "unnamed"


def _resolve_safe_path(rel_path: str) -> str:
    """
    Safely resolves a relative path against ARIA_FILES_DIR.
    Guarantees the target path cannot escape ARIA_FILES_DIR.
    Raises PermissionError if path traversal is detected.
    """
    clean_rel = rel_path.replace("/", os.sep).replace("\\", os.sep).strip()
    clean_rel = clean_rel.lstrip(os.sep)

    # If an absolute path was passed, check if it starts with ARIA_FILES_DIR
    if os.path.isabs(clean_rel):
        full_path = os.path.normpath(clean_rel)
    else:
        full_path = os.path.normpath(os.path.join(ARIA_FILES_DIR, clean_rel))

    # Strict commonpath jail check
    try:
        common = os.path.commonpath([full_path, ARIA_FILES_DIR])
        if os.path.normcase(common) != os.path.normcase(ARIA_FILES_DIR):
            raise PermissionError(f"Security Sandbox Violation: Path '{rel_path}' attempts to escape '{ARIA_FILES_DIR}'.")
    except ValueError:
        # Happens on Windows if paths are on different drive letters
        raise PermissionError(f"Security Sandbox Violation: Path '{rel_path}' is on a different drive than '{ARIA_FILES_DIR}'.")

    return full_path


def create_structured_folder(main_folder: str, subfolder: str = "") -> str:
    r"""
    Creates a structured directory in E:\ARIA FILES following the hierarchy:
    Main Folder (Category) ──> Subfolder (Project/Topic).

    Args:
        main_folder: Top-level category (e.g. 'Projects', 'Documents', 'Notes', 'Code', 'Creative', 'Research').
        subfolder: Specific project or subfolder path (e.g. 'Web_Scraper', 'Daily_Journal/2026', 'AI_Bots/modules').
    """
    if not main_folder or not main_folder.strip():
        cats = ", ".join(STANDARD_MAIN_FOLDERS)
        return f"Error: Please specify a Main Folder category (e.g. {cats}). Root files are forbidden to maintain clean hierarchy."

    clean_main = _sanitize_name(main_folder.strip())

    if subfolder and subfolder.strip():
        # Split subfolder by separators to sanitize each component
        parts = [p.strip() for p in re.split(r'[/\\]', subfolder.strip()) if p.strip()]
        clean_parts = [_sanitize_name(p) for p in parts]
        rel_target = os.path.join(clean_main, *clean_parts)
    else:
        rel_target = clean_main

    try:
        safe_path = _resolve_safe_path(rel_target)
        existed = os.path.exists(safe_path)
        os.makedirs(safe_path, exist_ok=True)
        
        display_rel = os.path.relpath(safe_path, ARIA_FILES_DIR)
        if existed:
            return f"📁 Structured folder already exists: E:\\ARIA FILES\\{display_rel}"
        return f"✨ Created structured folder: E:\\ARIA FILES\\{display_rel}\nHierarchy: Main Category [{clean_main}]" + (f" ──> Subfolder [{'/'.join(clean_parts)}]" if subfolder else "")
    except Exception as e:
        return f"Error creating structured folder: {e}"


def write_structured_file(main_folder: str, relative_path: str, content: str, overwrite: bool = True) -> str:
    r"""
    Writes a file inside E:\ARIA FILES under a structured main category and subfolder hierarchy.

    Args:
        main_folder: Top-level category (e.g. 'Projects', 'Notes', 'Code', 'Documents').
        relative_path: Subfolder path and filename (e.g. 'Aria_Bot/main.py' or 'Ideas/dream_journal.md').
        content: Text content to save into the file.
        overwrite: Whether to overwrite existing file content (default True).
    """
    if not main_folder or not main_folder.strip():
        # Check if relative_path already starts with a category
        parts = [p.strip() for p in re.split(r'[/\\]', relative_path.strip()) if p.strip()]
        if len(parts) >= 2:
            clean_main = _sanitize_name(parts[0])
            sub_parts = [_sanitize_name(p) for p in parts[1:]]
            clean_rel = os.path.join(clean_main, *sub_parts)
        else:
            return "Error: File structuring requires organizing into a Main Folder (e.g. Projects, Notes, Code, Documents). Cannot write directly into the root."
    else:
        clean_main = _sanitize_name(main_folder.strip())
        parts = [p.strip() for p in re.split(r'[/\\]', relative_path.strip()) if p.strip()]
        if not parts:
            return "Error: Please provide a filename or subfolder path to write."
        sub_parts = [_sanitize_name(p) for p in parts]
        clean_rel = os.path.join(clean_main, *sub_parts)

    try:
        safe_path = _resolve_safe_path(clean_rel)
        if os.path.exists(safe_path) and not overwrite:
            return f"File '{clean_rel}' already exists and overwrite=False."

        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        size_bytes = os.path.getsize(safe_path)
        size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes >= 1024 else f"{size_bytes} bytes"
        line_count = len(content.splitlines())
        display_rel = os.path.relpath(safe_path, ARIA_FILES_DIR)

        return f"📄 Successfully saved '{display_rel}' ({size_str}, {line_count} lines) in E:\\ARIA FILES!"
    except Exception as e:
        return f"Error writing structured file: {e}"


def read_structured_file(file_path: str, max_lines: int = 300) -> str:
    r"""
    Reads a file from E:\ARIA FILES.

    Args:
        file_path: Relative path to the file inside E:\ARIA FILES (e.g. 'Projects/Bot/main.py').
        max_lines: Maximum number of lines to return (prevents overflowing context).
    """
    if not file_path or not file_path.strip():
        return "Error: Please specify the file path to read."

    try:
        safe_path = _resolve_safe_path(file_path.strip())
        if not os.path.exists(safe_path):
            return f"Error: File '{file_path}' does not exist in E:\\ARIA FILES."
        if os.path.isdir(safe_path):
            return f"'{file_path}' is a directory, not a file. Use list_structure to view its contents."

        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines + 1)]

        truncated = len(lines) > max_lines
        content = "".join(lines[:max_lines])

        display_rel = os.path.relpath(safe_path, ARIA_FILES_DIR)
        header = f"=== E:\\ARIA FILES\\{display_rel} ===\n"
        if truncated:
            content += f"\n... [Truncated at {max_lines} lines for speed]"
        return header + content
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"


def list_structured_tree(target_folder: str = "", max_depth: int = 4) -> str:
    r"""
    Visualizes the directory tree in E:\ARIA FILES with Unicode icons and file statistics.

    Args:
        target_folder: Optional subfolder to focus on (leave empty to view entire E:\ARIA FILES tree).
        max_depth: Maximum recursion depth (default 4 levels).
    """
    try:
        base_dir = _resolve_safe_path(target_folder) if target_folder else ARIA_FILES_DIR
        if not os.path.exists(base_dir):
            return f"Folder '{target_folder}' does not exist in E:\\ARIA FILES."

        tree_lines = []
        total_folders = 0
        total_files = 0
        total_size = 0

        title_rel = os.path.relpath(base_dir, ARIA_FILES_DIR)
        root_title = "📁 E:\\ARIA FILES" if title_rel == "." else f"📁 E:\\ARIA FILES\\{title_rel}"
        tree_lines.append(root_title)

        def _format_size(sz: int) -> str:
            if sz >= 1024 * 1024:
                return f"{sz / (1024 * 1024):.1f} MB"
            if sz >= 1024:
                return f"{sz / 1024:.1f} KB"
            return f"{sz} B"

        def _walk(current_path: str, prefix: str = "", depth: int = 1):
            nonlocal total_folders, total_files, total_size
            if depth > max_depth:
                tree_lines.append(f"{prefix}└── ... [Max depth reached]")
                return

            try:
                entries = sorted(os.listdir(current_path), key=lambda x: (not os.path.isdir(os.path.join(current_path, x)), x.lower()))
            except Exception:
                return

            count = len(entries)
            for i, name in enumerate(entries):
                is_last = (i == count - 1)
                branch = "└── " if is_last else "├── "
                sub_prefix = "    " if is_last else "│   "
                full_item = os.path.join(current_path, name)

                if os.path.isdir(full_item):
                    total_folders += 1
                    tree_lines.append(f"{prefix}{branch}📁 {name}/")
                    _walk(full_item, prefix + sub_prefix, depth + 1)
                else:
                    total_files += 1
                    try:
                        sz = os.path.getsize(full_item)
                    except Exception:
                        sz = 0
                    total_size += sz
                    
                    # File type icon
                    ext = os.path.splitext(name)[1].lower()
                    if ext in [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".ps1", ".bat", ".sh"]:
                        icon = "⚡"
                    elif ext in [".md", ".txt", ".json", ".yaml", ".yml", ".csv"]:
                        icon = "📄"
                    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
                        icon = "🖼"
                    elif ext in [".zip", ".tar", ".gz", ".7z"]:
                        icon = "📦"
                    else:
                        icon = "📄"

                    tree_lines.append(f"{prefix}{branch}{icon} {name} ({_format_size(sz)})")

        _walk(base_dir)

        if total_files == 0 and total_folders == 0:
            return f"{root_title}\n  (Workspace is currently empty. Ready for your first structured folder!)"

        stats = f"\n\n📊 Summary: {total_folders} folders, {total_files} files ({_format_size(total_size)} total)"
        return "\n".join(tree_lines) + stats
    except Exception as e:
        return f"Error listing structured tree: {e}"


def manage_structured_path(action: str, path: str, target: str = "") -> str:
    r"""
    Safely manages (rename, move, copy, delete) files and folders inside E:\ARIA FILES.

    Args:
        action: 'rename', 'move', 'copy', or 'delete'.
        path: Relative path to target file/folder inside E:\ARIA FILES.
        target: Destination relative path (for rename, move, copy).
    """
    act = action.lower().strip()
    try:
        src = _resolve_safe_path(path)
        if not os.path.exists(src):
            return f"Error: Source '{path}' does not exist in E:\\ARIA FILES."

        if act in ("rename", "move"):
            if not target:
                return "Error: Please specify the new target path/name for rename/move."
            dst = _resolve_safe_path(target)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return f"✅ Moved/Renamed '{path}' ──> '{target}' successfully!"

        elif act == "copy":
            if not target:
                return "Error: Please specify the destination target path for copy."
            dst = _resolve_safe_path(target)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            return f"✅ Copied '{path}' ──> '{target}' successfully!"

        elif act in ("delete", "remove"):
            if os.path.normcase(src) == os.path.normcase(ARIA_FILES_DIR):
                return "Security Error: Cannot delete the root E:\\ARIA FILES workspace."
            if os.path.isdir(src):
                shutil.rmtree(src)
                return f"🗑 Removed directory '{path}' and all contents from E:\\ARIA FILES."
            else:
                os.remove(src)
                return f"🗑 Deleted file '{path}' from E:\\ARIA FILES."

        else:
            return f"Unknown action '{action}'. Supported actions: 'rename', 'move', 'copy', 'delete'."
    except Exception as e:
        return f"Error managing path '{path}': {e}"


def search_structured_files(query: str) -> str:
    r"""Searches for files by name or text content inside E:\ARIA FILES."""
    if not query or not query.strip():
        return "Please provide a search query."

    q = query.lower().strip()
    name_matches = []
    content_matches = []

    try:
        for root, dirs, files in os.walk(ARIA_FILES_DIR):
            for d in dirs:
                if q in d.lower():
                    rel = os.path.relpath(os.path.join(root, d), ARIA_FILES_DIR)
                    name_matches.append(f"📁 {rel}/")

            for f in files:
                full_f = os.path.join(root, f)
                rel = os.path.relpath(full_f, ARIA_FILES_DIR)
                if q in f.lower():
                    name_matches.append(f"📄 {rel}")

                # Search content in text files (< 1MB)
                try:
                    if os.path.getsize(full_f) < 1024 * 1024:
                        with open(full_f, "r", encoding="utf-8", errors="ignore") as file_obj:
                            content = file_obj.read()
                            if q in content.lower():
                                content_matches.append(f"🔍 {rel} (matches inside file)")
                except Exception:
                    pass

        res = []
        if name_matches:
            res.append("Filename & Folder Matches:\n" + "\n".join(name_matches[:10]))
        if content_matches:
            res.append("File Content Matches:\n" + "\n".join(content_matches[:10]))

        if not res:
            return f"No matches found for '{query}' in E:\\ARIA FILES."
        return "\n\n".join(res)
    except Exception as e:
        return f"Search error: {e}"


def open_aria_files_folder() -> str:
    r"""Opens E:\ARIA FILES in Windows File Explorer so the user can visually view and browse."""
    try:
        os.makedirs(ARIA_FILES_DIR, exist_ok=True)
        os.startfile(ARIA_FILES_DIR)
        return f"📂 Opened E:\\ARIA FILES in Windows File Explorer!"
    except Exception as e:
        return f"Could not open explorer: {e}"


def open_in_vscode(target_path: str = "", new_window: bool = False) -> str:
    r"""Opens E:\ARIA FILES (or a specific project/file inside it) in Visual Studio Code."""
    try:
        os.makedirs(ARIA_FILES_DIR, exist_ok=True)
        safe_path = _resolve_safe_path(target_path) if target_path else ARIA_FILES_DIR
        
        # Locate code.cmd / code executable
        code_cmd = shutil.which("code") or shutil.which("code.cmd") or os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd")
        
        cmd = [code_cmd]
        if new_window:
            cmd.append("-n")
        cmd.append(safe_path)
        
        subprocess.Popen(cmd, shell=True)
        rel = os.path.relpath(safe_path, ARIA_FILES_DIR)
        display = f"E:\\ARIA FILES\\{rel}" if rel != "." else "E:\\ARIA FILES"
        return f"💻 Opened '{display}' in Visual Studio Code!"
    except Exception as e:
        return f"Could not open in VS Code: {e}"


def create_multifile_project(project_name: str, files: Any = None, open_editor: bool = True) -> str:
    r"""Creates a multi-file project inside E:\ARIA FILES\Projects\<project_name> and optionally opens it in VS Code."""
    if not project_name or not project_name.strip():
        return "Error: Please specify a project name."

    clean_proj = _sanitize_name(project_name.strip())
    proj_dir = os.path.join(ARIA_FILES_DIR, "Projects", clean_proj)
    os.makedirs(proj_dir, exist_ok=True)

    # Parse files argument
    files_map = {}
    if isinstance(files, str) and files.strip():
        try:
            parsed = json.loads(files)
            if isinstance(parsed, dict):
                files_map = parsed
        except Exception:
            # Treat as single main.py content
            files_map = {"main.py": files}
    elif isinstance(files, dict):
        files_map = files

    # Default scaffold if empty
    if not files_map:
        files_map = {
            "main.py": f'"""\n{clean_proj} — Main Entry Point\nCreated by Aria in E:\\ARIA FILES\\Projects\\{clean_proj}\n"""\n\ndef main():\n    print("✨ Welcome to {clean_proj}! Powered by Aria & VS Code.")\n\nif __name__ == "__main__":\n    main()\n',
            "README.md": f"# {clean_proj}\n\nAutomated multi-file project created by **Aria** in `E:\\ARIA FILES\\Projects\\{clean_proj}`.\n\n## Structure\n- `main.py`: Main application entry point\n- `.vscode/settings.json`: VS Code workspace preferences\n",
            "requirements.txt": "# Project dependencies\n",
            ".vscode/settings.json": '{\n    "python.analysis.typeCheckingMode": "basic",\n    "files.encoding": "utf8",\n    "terminal.integrated.defaultProfile.windows": "PowerShell"\n}\n'
        }

    created_files = []
    for rel_path, content in files_map.items():
        clean_rel = os.path.normpath(str(rel_path).strip().lstrip("/\\")).replace("\\", "/")
        full_path = os.path.join(proj_dir, os.path.normpath(clean_rel))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(str(content))
        created_files.append(clean_rel)

    summary = f"✨ Created multi-file project 'Projects/{clean_proj}' with {len(created_files)} files:\n" + "\n".join([f"  • {f}" for f in created_files])

    if open_editor:
        vscode_msg = open_in_vscode(f"Projects/{clean_proj}")
        summary += f"\n{vscode_msg}"

    return summary


def write_project_file(project_name: str, file_path: str, content: str, overwrite: bool = True) -> str:
    r"""
    Writes or updates a specific file inside E:\ARIA FILES\Projects\<project_name>\<file_path>.
    Creates any needed intermediate subfolders automatically.

    Args:
        project_name: Name of the project folder (e.g. 'Math_Calculator', 'Web_App', 'My_Game').
        file_path: Relative path or filename within the project (e.g. 'index.html', 'style.css', 'app.js', 'src/App.jsx', 'server.py').
        content: Code or text to save in the file.
        overwrite: Whether to overwrite existing file (default True).
    """
    if not project_name or not project_name.strip():
        return "Error: Please specify a project name."
    if not file_path or not file_path.strip():
        return "Error: Please specify the file path inside the project."

    clean_proj = _sanitize_name(project_name.strip())
    clean_file = file_path.replace("/", os.sep).replace("\\", os.sep).strip().lstrip(os.sep)
    rel_path = os.path.join("Projects", clean_proj, clean_file)

    try:
        safe_path = _resolve_safe_path(rel_path)
        if os.path.exists(safe_path) and not overwrite:
            return f"File '{clean_file}' already exists in Projects/{clean_proj} and overwrite=False."

        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        size_bytes = os.path.getsize(safe_path)
        size_str = f"{size_bytes / 1024:.1f} KB" if size_bytes >= 1024 else f"{size_bytes} bytes"
        line_count = len(content.splitlines())

        return f"📄 Successfully saved '{clean_file}' ({size_str}, {line_count} lines) in E:\\ARIA FILES\\Projects\\{clean_proj}!"
    except Exception as e:
        return f"Error writing project file: {e}"


_RUNNING_SERVERS: Dict[str, Any] = {}


def _open_url_in_browser(url: str) -> bool:
    """Helper to open a URL in Chrome or default browser."""
    import webbrowser
    try:
        try:
            import aria_extended
            aria_extended.open_chrome_with_profile(url)
            return True
        except Exception:
            webbrowser.open(url)
            return True
    except Exception:
        return False


def launch_project_server(project_name: str, port: int = 5000, open_in_browser: bool = True) -> str:
    r"""
    Launches a lightweight local web server for a project located in E:\ARIA FILES\Projects\<project_name>
    and opens it in Google Chrome / browser on localhost.

    Args:
        project_name: Name of the project in Projects/ (e.g. 'Math_Calculator', 'Web_App').
        port: Desired port (default 5000). If port is busy, automatically finds an open port.
        open_in_browser: Whether to open http://localhost:<port> in Google Chrome (default True).
    """
    import socket
    import sys
    import time

    if not project_name or not project_name.strip():
        return "Error: Please specify a project name to launch."

    clean_proj = _sanitize_name(project_name.strip())
    rel_proj = os.path.join("Projects", clean_proj)

    try:
        proj_dir = _resolve_safe_path(rel_proj)
        if not os.path.exists(proj_dir) or not os.path.isdir(proj_dir):
            return f"Error: Project folder 'Projects/{clean_proj}' does not exist in E:\\ARIA FILES."

        # Check if already running for this project
        if clean_proj in _RUNNING_SERVERS:
            proc_info = _RUNNING_SERVERS[clean_proj]
            proc = proc_info.get("process")
            existing_port = proc_info.get("port")
            if proc and proc.poll() is None:
                url = f"http://localhost:{existing_port}"
                if open_in_browser:
                    _open_url_in_browser(url)
                return f"🚀 Project '{clean_proj}' server is already running at {url} (PID: {proc.pid}) and opened in browser!"

        # Find an open port starting from requested port
        def _is_port_in_use(p: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('127.0.0.1', p)) == 0

        target_port = port
        while _is_port_in_use(target_port) and target_port < port + 20:
            target_port += 1

        if _is_port_in_use(target_port):
            return f"Error: Could not find an open port between {port} and {port + 20}."

        has_server_py = os.path.exists(os.path.join(proj_dir, "server.py"))
        has_app_py = os.path.exists(os.path.join(proj_dir, "app.py"))

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

        if has_server_py:
            cmd = [sys.executable, "server.py"]
            desc = "Python backend server (server.py)"
        elif has_app_py:
            cmd = [sys.executable, "app.py"]
            desc = "Python backend application (app.py)"
        else:
            cmd = [sys.executable, "-m", "http.server", str(target_port)]
            desc = f"Python HTTP static web server (port {target_port})"

        env = os.environ.copy()
        env["PORT"] = str(target_port)

        proc = subprocess.Popen(
            cmd,
            cwd=proj_dir,
            env=env,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        _RUNNING_SERVERS[clean_proj] = {
            "process": proc,
            "port": target_port,
            "cmd": cmd,
            "started_at": time.time(),
            "dir": proj_dir
        }

        # Wait briefly for socket binding
        time.sleep(0.5)

        url = f"http://localhost:{target_port}"
        browser_status = ""
        if open_in_browser:
            opened = _open_url_in_browser(url)
            browser_status = " and opened in Google Chrome!" if opened else "!"

        file_list = [f for f in os.listdir(proj_dir) if not f.startswith(".")]
        return (
            f"🚀 Successfully launched {desc} for 'Projects/{clean_proj}'!\n"
            f"• Local URL: {url}\n"
            f"• Server PID: {proc.pid}\n"
            f"• Project files detected: {', '.join(file_list[:8])}\n"
            f"Server is actively running in background{browser_status}"
        )
    except Exception as e:
        return f"Error launching project server: {e}"


def stop_project_server(project_name: str) -> str:
    r"""Stops a running local web server for a project."""
    if not project_name or not project_name.strip():
        return "Error: Please specify a project name."
    clean_proj = _sanitize_name(project_name.strip())
    if clean_proj in _RUNNING_SERVERS:
        proc_info = _RUNNING_SERVERS.pop(clean_proj)
        proc = proc_info.get("process")
        if proc:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
                    proc.wait(timeout=1)
                return f"🛑 Stopped server for project '{clean_proj}' (PID: {proc.pid})."
            except Exception as e:
                return f"Error stopping server process: {e}"
    return f"No active server tracked for project '{clean_proj}'."


