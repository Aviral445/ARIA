"""
tests/test_android_controller.py — Test suite for Wireless Android ADB Controller
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure paths
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "gui")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from tools.aria_android import AndroidController, KNOWN_ANDROID_APPS, get_android_controller
from core.aria_adk import ALL_ADK_TOOLS, TOOL_NAME_MAP, SWARM_AGENTS_METADATA


class TestAndroidController(unittest.TestCase):

    def setUp(self):
        self.ctrl = AndroidController()

    def test_known_apps_mapping(self):
        self.assertEqual(KNOWN_ANDROID_APPS.get("whatsapp"), "com.whatsapp")
        self.assertEqual(KNOWN_ANDROID_APPS.get("instagram"), "com.instagram.android")
        self.assertEqual(KNOWN_ANDROID_APPS.get("youtube"), "com.google.android.youtube")
        self.assertEqual(KNOWN_ANDROID_APPS.get("spotify"), "com.spotify.music")
        self.assertEqual(KNOWN_ANDROID_APPS.get("camera"), "com.android.camera")

    def test_settings_persistence(self):
        self.ctrl.save_settings("192.168.1.99", 5555, "4321")
        self.assertEqual(self.ctrl.phone_ip, "192.168.1.99")
        self.assertEqual(self.ctrl.phone_port, 5555)
        self.assertEqual(self.ctrl.phone_pin, "4321")

    @patch.object(AndroidController, "_run_adb")
    def test_unlock_phone_with_pin(self, mock_run):
        mock_run.return_value = (True, "Success")
        res = self.ctrl.unlock_phone(pin="1234")
        
        # Verify wakeup (224), swipe, PIN typing, and submit (66) were invoked
        calls = [c[0][0] for c in mock_run.call_args_list]
        self.assertTrue(any("224" in c for c in calls))
        self.assertTrue(any("swipe" in c for c in calls))
        self.assertTrue(any("1234" in c for c in calls))
        self.assertTrue(any("66" in c for c in calls))
        self.assertIn("Phone unlocked", res)

    @patch.object(AndroidController, "_run_adb")
    def test_lock_phone(self, mock_run):
        mock_run.return_value = (True, "Success")
        res = self.ctrl.lock_phone()
        calls = [c[0][0] for c in mock_run.call_args_list]
        self.assertTrue(any("26" in c for c in calls))
        self.assertIn("Phone locked", res)

    @patch.object(AndroidController, "_run_adb")
    def test_open_app_whatsapp(self, mock_run):
        mock_run.return_value = (True, "Events injected: 1")
        res = self.ctrl.open_app("whatsapp")
        calls = [c[0][0] for c in mock_run.call_args_list]
        self.assertTrue(any("com.whatsapp" in c for c in calls))
        self.assertIn("Opened 'whatsapp'", res)

    def test_adk_phone_tools_registered(self):
        expected_tools = [
            "unlock_phone",
            "lock_phone",
            "open_mobile_app",
            "make_mobile_call",
            "send_mobile_sms",
            "get_phone_battery",
            "analyze_phone_screen",
        ]
        for tool_name in expected_tools:
            self.assertIn(tool_name, TOOL_NAME_MAP, f"Tool {tool_name} must be in ADK TOOL_NAME_MAP")

    def test_mobile_swarm_agent_metadata(self):
        self.assertIn("mobile", SWARM_AGENTS_METADATA)
        agent = SWARM_AGENTS_METADATA["mobile"]
        self.assertEqual(agent["name"], "Mobile & Phone Operative")
        self.assertIn("unlock_phone", agent["tools"])


if __name__ == "__main__":
    unittest.main()
