import unittest, os, sys
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for _p in [_ROOT, os.path.join(_ROOT, "core"), os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "server"), os.path.join(_ROOT, "mcp"), os.path.join(_ROOT, "gui")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import aria_tools, aria_scheduler, aria_memory, aria_extended

class TestAriaModules(unittest.TestCase):
    def test_network_info(self):
        res = aria_tools.get_network_info()
        self.assertIn("Network:", res)
        self.assertIn("Local IP:", res)

    def test_jokes_and_motivation(self):
        joke = aria_tools.get_joke()
        self.assertTrue(len(joke) > 5)
        opener = aria_tools.get_daily_opener()
        self.assertTrue(len(opener) > 5)

    def test_goals(self):
        res = aria_tools.add_goal("Test Unit Goal", "100%")
        self.assertIn("Goal added:", res)
        list_res = aria_tools.list_goals()
        self.assertIn("Test Unit Goal", list_res)

    def test_scheduler_reminders(self):
        sched = aria_scheduler.AriaScheduler()
        res = sched.add_reminder_in_seconds("Test Alert", 9999)
        self.assertIn("Reminder set for", res)
        active = sched.list_active_reminders()
        self.assertIn("Test Alert", active)

    def test_episodic_memory(self):
        aria_memory.record_memory_event("Hello unit test", "I am Aria unit test response")
        recent = aria_memory.get_recent_timeline(limit=3)
        self.assertIn("Hello unit test", recent)

    def test_personality_modes(self):
        res = aria_memory.set_personality_mode("witty")
        self.assertIn("Witty", res)
        self.assertEqual(aria_memory.get_current_personality(), "witty")
        prompt = aria_memory.get_personality_prompt()
        self.assertIn("clever", prompt)

    def test_multi_profiles(self):
        p_data = aria_memory.switch_profile("TestUser")
        self.assertEqual(p_data.get("name"), "Testuser")
        profiles = aria_memory.get_all_profiles()
        self.assertIn("Testuser", profiles)
        aria_memory.switch_profile("Friend")

    def test_analytics_summary(self):
        summary = aria_memory.get_analytics_summary()
        self.assertIn("memory_events", summary)
        self.assertIn("active_goals", summary)
        self.assertIn("personality", summary)

    def test_session_logs_export(self):
        res = aria_memory.export_session_logs("test_export.md")
        self.assertIn("Successfully exported", res)
        self.assertTrue(os.path.exists("test_export.md"))
        os.remove("test_export.md")

    def test_smart_home_trigger(self):
        res = aria_extended.trigger_smart_device("bedroom light")
        self.assertTrue(len(res) > 0)

    def test_extended_features(self):
        # DND
        msg = aria_extended.set_dnd_mode(True)
        self.assertTrue(aria_extended.is_dnd_active())
        aria_extended.set_dnd_mode(False)
        self.assertFalse(aria_extended.is_dnd_active())

        # Emotion rate modifier
        mod_urgent = aria_extended.detect_emotion_rate_modifier("Warning! Urgent issue.")
        self.assertEqual(mod_urgent, 3)
        mod_calm = aria_extended.detect_emotion_rate_modifier("Please relax and breathe.")
        self.assertEqual(mod_calm, -2)

        # Caching
        aria_extended.set_cached_response("what is capital of france", "Paris")
        cached = aria_extended.get_cached_response("what is capital of france")
        self.assertEqual(cached, "Paris")

    def test_organizer_and_folder_creation(self):
        import aria_organizer
        res = aria_organizer.create_folder("Unit_Test_Folder", "desktop")
        self.assertIn("Created folder", res)
        folder_path = os.path.expandvars(r"%USERPROFILE%\Desktop\Unit_Test_Folder")
        self.assertTrue(os.path.exists(folder_path))
        os.rmdir(folder_path)

    def test_master_admin_auth(self):
        import aria_auth
        # Correct Master Admin
        res_admin = aria_auth.authenticate_user("L", "balluboss", "Test Laptop")
        self.assertTrue(res_admin["success"])
        self.assertTrue(res_admin["is_admin"])
        self.assertEqual(res_admin["role"], "admin")
        
        # Verify Session
        sess = aria_auth.verify_session(res_admin["token"])
        self.assertTrue(sess["is_admin"])
        self.assertEqual(sess["username"], "L")

        # Wrong Password
        res_fail = aria_auth.authenticate_user("L", "wrongpassword")
        self.assertFalse(res_fail["success"])

    def test_system_context_apps_detection(self):
        import aria_system_context
        ctx = aria_system_context.get_system_context()
        self.assertIn("running_software", ctx)
        self.assertIn("open_windows", ctx)
        prompt_txt = aria_system_context.format_context_for_prompt(ctx)
        self.assertIn("LIVE SYSTEM CONTEXT", prompt_txt)

if __name__ == "__main__":
    unittest.main()

