r"""
tools/aria_file_structuring.py — Dynamic Lab & ADK Tool for File Structuring

Allows Aria to autonomously organize, create, write, read, and manage files in E:\ARIA FILES
following the strict hierarchy: Main Folder (Category) ──> Subfolder (Project/Topic) ──> Files.
"""

import os
from typing import Tuple, Callable

try:
    from core.aria_file_structuring import (
        create_structured_folder,
        write_structured_file,
        read_structured_file,
        list_structured_tree,
        manage_structured_path,
        search_structured_files,
        open_aria_files_folder,
        open_in_vscode,
        create_multifile_project,
        ARIA_FILES_DIR
    )
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.aria_file_structuring import (
        create_structured_folder,
        write_structured_file,
        read_structured_file,
        list_structured_tree,
        manage_structured_path,
        search_structured_files,
        open_aria_files_folder,
        open_in_vscode,
        create_multifile_project,
        ARIA_FILES_DIR
    )


def file_structuring_tool(
    action: str = "list",
    main_folder: str = "Projects",
    subfolder: str = "",
    filename: str = "",
    content: str = "",
    target: str = ""
) -> str:
    r"""
    Manages structured folders and files in E:\ARIA FILES.
    Follows the hierarchy: Main Folder (Category) ──> Subfolder (Project/Topic) ──> Files.

    Args:
        action: 'create_folder', 'write', 'read', 'list', 'tree', 'manage', 'search', 'open_explorer', 'vscode', or 'scaffold'.
        main_folder: Main category (e.g. 'Projects', 'Documents', 'Notes', 'Code', 'Creative', 'Research', 'Archive').
        subfolder: Specific project or subfolder (e.g. 'Web_Bot' or 'Daily_Notes').
        filename: Filename or relative path inside the folder (e.g. 'main.py' or 'summary.md').
        content: Text content or JSON file map to write if action='write' or 'scaffold'.
        target: Target path for rename/move/copy if action='manage'.
    """
    act = action.lower().strip()

    if act in ("create_folder", "mkdir", "new_folder"):
        return create_structured_folder(main_folder=main_folder, subfolder=subfolder)

    elif act in ("write", "save", "create_file"):
        rel_path = os.path.join(subfolder, filename) if subfolder else filename
        return write_structured_file(main_folder=main_folder, relative_path=rel_path, content=content)

    elif act in ("read", "view", "cat"):
        target_path = filename or (os.path.join(main_folder, subfolder) if subfolder else main_folder)
        return read_structured_file(file_path=target_path)

    elif act in ("list", "tree", "show", "structure"):
        target_dir = os.path.join(main_folder, subfolder) if (main_folder and subfolder) else (main_folder if main_folder != "Projects" else "")
        return list_structured_tree(target_folder=target_dir)

    elif act in ("manage", "move", "rename", "copy", "delete"):
        target_path = filename or (os.path.join(main_folder, subfolder) if subfolder else main_folder)
        return manage_structured_path(action=act if act != "manage" else "rename", path=target_path, target=target)

    elif act in ("search", "find"):
        query = filename or subfolder or main_folder
        return search_structured_files(query=query)

    elif act in ("open", "open_explorer", "explore"):
        return open_aria_files_folder()

    elif act in ("vscode", "open_vscode", "code"):
        target_path = filename or (os.path.join(main_folder, subfolder) if subfolder else (main_folder if main_folder != "Projects" else ""))
        return open_in_vscode(target_path=target_path)

    elif act in ("multifile_project", "scaffold", "new_project"):
        proj_name = subfolder or filename or (main_folder if main_folder != "Projects" else "New_Project")
        return create_multifile_project(project_name=proj_name, files=content, open_editor=True)

    else:
        return f"Unknown action '{action}'. Supported actions: 'create_folder', 'write', 'read', 'list', 'manage', 'search', 'open_explorer', 'vscode', 'scaffold'."


def register_tool() -> Tuple[str, Callable]:
    """Registers file_structuring_tool with Aria's lab and ADK engine."""
    return "file_structuring_tool", file_structuring_tool


if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print("Testing file_structuring_tool:")
    print(t_fn(action="list"))
