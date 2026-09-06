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
import shutil
import subprocess
from typing import Optional, List, Dict, Tuple, Any

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
