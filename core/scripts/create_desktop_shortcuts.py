"""
core/scripts/create_desktop_shortcuts.py — Creates Desktop Shortcut for Aria Cyber Workstation
"""

import os
import sys
import subprocess

def create_shortcuts():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    electron_exe = os.path.join(root_dir, "electron", "node_modules", "electron", "dist", "electron.exe")

    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell

    # Clean up obsolete Tkinter shortcuts if present
    $old1 = "{desktop_dir}\\Aria Classic Dashboard.lnk"
    $old2 = "{desktop_dir}\\Aria.lnk"
    if (Test-Path $old1) {{ Remove-Item $old1 -Force }}
    if (Test-Path $old2) {{ Remove-Item $old2 -Force }}

    # Create Electron Cyber Workstation Shortcut
    $sc = $WshShell.CreateShortcut("{desktop_dir}\\Aria Cyber Workstation.lnk")
    $sc.TargetPath = "{electron_exe}"
    $sc.Arguments = "."
    $sc.WorkingDirectory = "{root_dir}\\electron"
    $sc.Description = "Aria AI — Autonomous Desktop Cyber Workstation"
    $sc.IconLocation = "C:\\Windows\\System32\\imageres.dll,26"
    $sc.Save()

    Write-Host "Aria Cyber Workstation desktop shortcut configured successfully!"
    """

    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
    print(res.stdout or res.stderr)

if __name__ == "__main__":
    create_shortcuts()
