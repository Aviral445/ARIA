"""
tests/test_screen_recorder.py — Unit and Integration Tests for Aria Screen Recorder,
Audio Capture, and Meeting Notes Generation.
"""

import unittest
import os
import sys
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "system_tools")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from system_tools.aria_screen_recorder import (
    AriaScreenRecorder,
    AriaMeetingAnalyzer,
    start_screen_recording,
    stop_screen_recording,
    get_recording_status,
    list_recordings,
    analyze_recording,
    generate_meeting_notes
)
import core.aria_adk as adk
import core.agent_core as agent_core


class TestAriaScreenRecorder(unittest.TestCase):
    def setUp(self):
        self.recorder = AriaScreenRecorder()
        # Ensure idle state before each test
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def tearDown(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def test_recorder_idle_by_default(self):
        """Verify the recorder is strictly on-demand and IDLE by default."""
        self.assertFalse(self.recorder.is_recording)
        status = self.recorder.get_status()
        self.assertEqual(status["status"], "IDLE")
        status_text = get_recording_status()
        self.assertIn("IDLE", status_text)

    def test_start_and_stop_recording_lifecycle(self):
        """Test on-demand start and stop recording cycle."""
        # 1. Start recording on demand
        start_res = self.recorder.start_recording(title="UnitTest_Meet", fps=5, record_audio=False)
        self.assertTrue(start_res["success"])
        self.assertTrue(self.recorder.is_recording)

        # 2. Check active status
        status = self.recorder.get_status()
        self.assertEqual(status["status"], "RECORDING")
        self.assertEqual(status["title"], "UnitTest_Meet")

        time.sleep(1.0)

        # 3. Stop recording
        stop_res = self.recorder.stop_recording()
        self.assertTrue(stop_res["success"])
        self.assertFalse(self.recorder.is_recording)
        self.assertIn("UnitTest_Meet", stop_res["session"]["title"])
        self.assertTrue(os.path.exists(stop_res["session"]["video_path"]))

    def test_prevent_double_recording(self):
        """Verify starting an already running recording is safely handled."""
        self.recorder.start_recording(title="Meet_One", fps=5, record_audio=False)
        second_start = self.recorder.start_recording(title="Meet_Two", fps=5, record_audio=False)
        self.assertFalse(second_start["success"])
        self.assertIn("Already recording", second_start["message"])
        self.recorder.stop_recording()

    def test_list_recordings(self):
        """Verify recordings listing returns formatted string."""
        listing = list_recordings()
        self.assertTrue(isinstance(listing, str))
        self.assertTrue(len(listing) > 0)

    def test_adk_tool_registrations(self):
        """Verify all recording tools are exposed to Aria's ADK Swarm."""
        tool_names = [fn.__name__ for fn in adk.ALL_ADK_TOOLS]
        expected_tools = [
            "start_screen_recording",
            "stop_screen_recording",
            "get_recording_status",
            "list_recordings",
            "analyze_recording",
            "generate_meeting_notes"
        ]
        for t in expected_tools:
            self.assertIn(t, tool_names)
            self.assertIn(t, adk.TOOL_NAME_MAP)

        # Check swarm metadata
        self.assertIn("meeting_recorder", adk.SWARM_AGENTS_METADATA)

    def test_agent_core_tool_dispatch(self):
        """Verify natural language dispatch in agent_core tools."""
        self.assertIn("screen_recording", agent_core.TOOLS)
        self.assertIn("meeting_notes", agent_core.TOOLS)

        # Check status dispatch
        handled, msg = agent_core.TOOLS["screen_recording"]("recording status")
        self.assertTrue(handled)
        self.assertIn("IDLE", msg)

        # Check not handled on unrelated text
        handled_unrelated, _ = agent_core.TOOLS["screen_recording"]("what is the weather today")
        self.assertFalse(handled_unrelated)


if __name__ == "__main__":
    unittest.main()
