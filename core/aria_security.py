"""
core/aria_security.py — OS-Enforced ACL & Process Integrity Security Manager
Provides NTFS and filesystem-level immutability locks on GAIA test suites,
preventing Aria or untrusted execution from modifying or tampering with tests.
"""

import os
import sys
import stat
import subprocess
from typing import Dict, Any, Tuple


def set_test_immutability(path: str) -> bool:
    """
    Sets OS-enforced immutability on a test file or directory.
    Combines Windows NTFS ACL restrictions with POSIX/NTFS read-only bit attributes.
    """
    if not os.path.exists(path):
        return False

    abs_path = os.path.abspath(path)

    # 1. Apply filesystem read-only attribute
    try:
        if os.path.isdir(abs_path):
            for root, dirs, files in os.walk(abs_path):
                for f in files:
                    os.chmod(os.path.join(root, f), stat.S_IREAD)
        else:
            os.chmod(abs_path, stat.S_IREAD)
    except Exception as e:
        print(f"[AriaSecurity Notice] chmod S_IREAD notice: {e}")

    # 2. On Windows: Apply OS-enforced NTFS ACL locking via icacls
    if sys.platform == "win32":
        try:
            # Grant Read-Only to Everyone (SID S-1-1-0) and deny Write & Delete
            # /deny *S-1-1-0:(W,D) ensures no non-elevated user/process can modify or delete it
            cmd = f'icacls "{abs_path}" /deny *S-1-1-0:(W,D)'
            subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
        except Exception as e_acl:
            print(f"[AriaSecurity Notice] icacls deny write notice: {e_acl}")

    return True


def verify_test_immutability(path: str) -> Dict[str, Any]:
    """
    Verifies that a test file is strictly immutable (read-only) and cannot be written to.
    """
    if not os.path.exists(path):
        return {"exists": False, "is_immutable": False, "reason": "Path does not exist"}

    abs_path = os.path.abspath(path)
    file_stat = os.stat(abs_path)
    is_readonly_bit = not bool(file_stat.st_mode & stat.S_IWUSR)

    # Attempt to open file for append/write — IT MUST FAIL!
    can_write = False
    try:
        with open(abs_path, "a", encoding="utf-8") as f:
            can_write = True
    except (PermissionError, OSError):
        can_write = False

    is_immutable = is_readonly_bit and not can_write

    return {
        "exists": True,
        "path": abs_path,
        "is_readonly_bit": is_readonly_bit,
        "can_write": can_write,
        "is_immutable": is_immutable,
        "reason": "Test file is OS-locked and read-only" if is_immutable else "Test file is writable"
    }


def unlock_for_gaia_teardown(path: str) -> bool:
    """
    Removes the OS-enforced immutability lock so GAIA or Aria can perform clean slate teardown,
    file replacements, or project resets. Handles both files and directory trees recursively.
    """
    if not os.path.exists(path):
        return True

    abs_path = os.path.abspath(path)

    # 1. On Windows: Remove deny ACL first (recursively if directory)
    if sys.platform == "win32":
        try:
            if os.path.isdir(abs_path):
                # Strip deny ACE from all files and subfolders in tree
                cmd_tree = f'icacls "{abs_path}\\*" /remove:d *S-1-1-0 /t /c /q'
                subprocess.run(cmd_tree, shell=True, capture_output=True, timeout=5)
                # Strip deny ACE from parent folder itself
                cmd_dir = f'icacls "{abs_path}" /remove:d *S-1-1-0 /c /q'
                subprocess.run(cmd_dir, shell=True, capture_output=True, timeout=5)
            else:
                cmd_file = f'icacls "{abs_path}" /remove:d *S-1-1-0 /c /q'
                subprocess.run(cmd_file, shell=True, capture_output=True, timeout=5)
        except Exception as e_acl:
            print(f"[AriaSecurity Notice] icacls remove deny notice: {e_acl}")

    # 2. Restore write attribute
    try:
        if os.path.isdir(abs_path):
            for root, dirs, files in os.walk(abs_path):
                for d in dirs:
                    try:
                        os.chmod(os.path.join(root, d), stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
                for f in files:
                    try:
                        os.chmod(os.path.join(root, f), stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
            os.chmod(abs_path, stat.S_IWRITE | stat.S_IREAD)
        else:
            os.chmod(abs_path, stat.S_IWRITE | stat.S_IREAD)
    except Exception as e:
        print(f"[AriaSecurity Notice] chmod S_IWRITE notice: {e}")

    return True

