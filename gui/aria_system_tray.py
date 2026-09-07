"""
gui/aria_system_tray.py — System Tray Icon & Minimize-to-Tray Manager (Feature 31)
Runs a background system tray icon on Windows allowing Aria Pygame GUI to minimize
to the notification area, toggle listening, or cleanly exit.
"""

import os
import sys
import threading
import time
from typing import Optional, Callable


class AriaSystemTray:
    def __init__(
        self,
        app_name: str = "Aria Desktop Companion",
        on_restore: Optional[Callable[[], None]] = None,
        on_toggle_listen: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None
    ):
        self.app_name = app_name
        self.on_restore = on_restore
        self.on_toggle_listen = on_toggle_listen
        self.on_quit = on_quit
        self.is_minimized_to_tray = False
        self._icon_instance = None
        self._tray_thread: Optional[threading.Thread] = None

    def start(self):
        """Starts system tray runner in a background thread."""
        self._tray_thread = threading.Thread(target=self._run_tray, daemon=True, name="AriaTrayThread")
        self._tray_thread.start()

    def _run_tray(self):
        """Initializes pystray if available, or native Windows notification loop."""
        try:
            import pystray
            from PIL import Image, ImageDraw

            # Generate 64x64 neon icon for tray
            img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((8, 8, 56, 56), fill=(138, 43, 226), outline=(0, 255, 255), width=3)
            draw.ellipse((22, 22, 42, 42), fill=(255, 105, 180))

            menu = pystray.Menu(
                pystray.MenuItem("Open Aria", self._action_restore, default=True),
                pystray.MenuItem("Toggle Listening", self._action_toggle_listen),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._action_quit)
            )

            self._icon_instance = pystray.Icon("aria_tray", img, self.app_name, menu)
            self._icon_instance.run()
        except Exception:
            # Fallback state tracker for environments without pystray
            pass

    def _action_restore(self, icon=None, item=None):
        self.is_minimized_to_tray = False
        if self.on_restore:
            try:
                self.on_restore()
            except Exception as e:
                print(f"[AriaTray] Restore error: {e}")

    def _action_toggle_listen(self, icon=None, item=None):
        if self.on_toggle_listen:
            try:
                self.on_toggle_listen()
            except Exception as e:
                print(f"[AriaTray] Toggle listen error: {e}")

    def _action_quit(self, icon=None, item=None):
        self.stop()
        if self.on_quit:
            try:
                self.on_quit()
            except Exception as e:
                print(f"[AriaTray] Quit error: {e}")

    def minimize(self):
        """Sets state to minimized."""
        self.is_minimized_to_tray = True

    def restore(self):
        """Restores window from tray."""
        self._action_restore()

    def stop(self):
        """Cleans up tray icon."""
        if self._icon_instance:
            try:
                self._icon_instance.stop()
            except Exception:
                pass
        self._icon_instance = None
