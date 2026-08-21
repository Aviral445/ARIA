"""
aria_organizer.py — Autonomous Folder Creator & Smart File Organizer for Aria
Handles:
1. Creating folders at any named or specified location
2. Organizing messy folders (Desktop, Downloads, Documents) by file categories
3. Moving specific file types (e.g. "move all pdfs from desktop to documents")
"""

import os, sys, shutil, re

FILE_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".epub", ".md", ".rtf"],
    "Images": [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".bmp", ".tiff"],
    "Videos": [".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".iso", ".tgz"],
    "Installers": [".exe", ".msi", ".apk", ".dmg"],
    "Code_and_Scripts": [".py", ".js", ".ts", ".html", ".css", ".json", ".sql", ".java", ".cpp", ".c", ".sh", ".bat", ".ps1"]
}

def resolve_location_path(location_str: str) -> str:
    """Resolves keywords like 'desktop', 'downloads', 'documents' to real paths."""
    user_home = os.path.expandvars(r"%USERPROFILE%")
    loc_lower = location_str.lower().strip()
    
    if "desktop" in loc_lower:
        return os.path.join(user_home, "Desktop")
    if "download" in loc_lower:
        return os.path.join(user_home, "Downloads")
    if "document" in loc_lower:
        return os.path.join(user_home, "Documents")
    if "picture" in loc_lower or "photo" in loc_lower:
        return os.path.join(user_home, "Pictures")
    if "music" in loc_lower:
        return os.path.join(user_home, "Music")
    if "video" in loc_lower or "movie" in loc_lower:
        return os.path.join(user_home, "Videos")
    if os.path.exists(location_str.strip('"').strip("'")):
        return location_str.strip('"').strip("'")
    return os.path.join(user_home, "Desktop") # default


# ── 1. CREATE FOLDER ──────────────────────────────────────────────────────────
def create_folder(folder_name: str, location_str: str = "desktop") -> str:
    """Creates a new folder at the target directory."""
    target_base = resolve_location_path(location_str)
    # Clean folder name
    clean_name = re.sub(r'[\\/*?:"<>|]', '', folder_name).strip()
    if not clean_name:
        clean_name = "New_Folder"
        
    full_path = os.path.join(target_base, clean_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Created folder '{clean_name}' at {full_path}!"
    except Exception as e:
        return f"Could not create folder: {e}"


# ── 2. AUTONOMOUS FOLDER ORGANIZER ───────────────────────────────────────────
def organize_directory(location_str: str = "desktop") -> str:
    """
    Cleans up a messy folder (e.g. Desktop or Downloads), grouping loose files
    into categorized subfolders: Documents, Images, Videos, Archives, etc.
    """
    target_dir = resolve_location_path(location_str)
    if not os.path.exists(target_dir):
        return f"Directory does not exist: {target_dir}"

    dir_name = os.path.basename(target_dir)
    stats = {}
    total_moved = 0

    try:
        items = os.listdir(target_dir)
    except Exception as e:
        return f"Could not access {dir_name}: {e}"

    # Set of category folders to avoid moving them into themselves
    protected_folders = set(FILE_CATEGORIES.keys()) | {"Desktop", "Downloads", "Documents", "Screenshots"}

    for item in items:
        item_path = os.path.join(target_dir, item)
        # Skip subdirectories, shortcuts, and hidden/system files
        if os.path.isdir(item_path) or item.lower().endswith((".lnk", ".url", ".ini")) or item.startswith("."):
            continue

        ext = os.path.splitext(item)[1].lower()
        if not ext:
            continue

        # Find matching category
        target_category = None
        for cat_name, extensions in FILE_CATEGORIES.items():
            if ext in extensions:
                target_category = cat_name
                break

        if not target_category:
            target_category = "Other_Files"

        cat_folder = os.path.join(target_dir, target_category)
        os.makedirs(cat_folder, exist_ok=True)

        dest_path = os.path.join(cat_folder, item)
        # Resolve filename collision if dest already exists
        if os.path.exists(dest_path):
            base, extension = os.path.splitext(item)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(cat_folder, f"{base}_{counter}{extension}")
                counter += 1

        try:
            shutil.move(item_path, dest_path)
            stats[target_category] = stats.get(target_category, 0) + 1
            total_moved += 1
        except Exception:
            pass

    if total_moved == 0:
        return f"Your {dir_name} is already neatly organized! No loose files needed moving."

    summary_parts = [f"{count} {cat.lower()}" for cat, count in stats.items()]
    return f"Organized {dir_name}! Moved {total_moved} files ({', '.join(summary_parts)}) into neat category folders."


# ── 3. MOVE SPECIFIC FILE TYPES ──────────────────────────────────────────────
def move_file_type(extension_hint: str, from_loc: str, to_loc: str) -> str:
    """Moves all files matching an extension (e.g. '.pdf') from one folder to another."""
    src = resolve_location_path(from_loc)
    dst = resolve_location_path(to_loc)
    
    if not os.path.exists(src) or not os.path.exists(dst):
        return "Source or destination directory does not exist."

    ext = extension_hint.lower()
    if not ext.startswith("."):
        ext = f".{ext}"

    count = 0
    for item in os.listdir(src):
        item_path = os.path.join(src, item)
        if os.path.isfile(item_path) and item.lower().endswith(ext):
            dest_path = os.path.join(dst, item)
            if os.path.exists(dest_path):
                base, ext_ = os.path.splitext(item)
                dest_path = os.path.join(dst, f"{base}_{int(os.path.getmtime(item_path))}{ext_}")
            try:
                shutil.move(item_path, dest_path)
                count += 1
            except Exception:
                pass

    return f"Moved {count} {ext.upper()} files from {os.path.basename(src)} to {os.path.basename(dst)}!"
