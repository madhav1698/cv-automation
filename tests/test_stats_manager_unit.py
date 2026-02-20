
import unittest
import os
import json
import shutil
from core.stats_manager import StatsManager

class TestStatsManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), "test_temp_dir")
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        self.stats_file = os.path.join(self.test_dir, "application_stats.json")
        self.manager = StatsManager(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_application(self):
        app_id = self.manager.add_application("2026-02-17", "Test Company", "Denmark", "Applied")
        self.assertIn(app_id, self.manager.get_stats())
        self.assertEqual(self.manager.get_stats()[app_id]["company"], "Test Company")
        self.assertEqual(self.manager.get_stats()[app_id]["country"], "Denmark")
        self.assertEqual(self.manager.get_stats()[app_id]["status"], "Applied")

    def test_update_status(self):
        app_id = self.manager.add_application("2026-02-17", "Test Company", "Denmark", "Unknown")
        self.manager.update_status(app_id, "Interview")
        self.assertEqual(self.manager.get_stats()[app_id]["status"], "Interview")

    def test_get_summary(self):
        self.manager.add_application("2026-02-17", "Company A", "Denmark", "Applied")
        self.manager.add_application("2026-02-17", "Company B", "Sweden", "Rejected")
        self.manager.add_application("2026-02-17", "Company C", "UK", "Applied")
        
        summary = self.manager.get_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_status"]["Applied"], 2)
        self.assertEqual(summary["by_status"]["Rejected"], 1)

    def test_rename_application_rekeys_id(self):
        app_id = self.manager.add_application("2026-02-17", "Test Company", "Denmark", "Unknown")

        ok, new_app_id = self.manager.rename_application(app_id, "2026-02-18", "Renamed Company")
        self.assertTrue(ok)
        self.assertNotEqual(app_id, new_app_id)

        stats = self.manager.get_stats()
        self.assertNotIn(app_id, stats)
        self.assertIn(new_app_id, stats)
        self.assertEqual(stats[new_app_id]["date"], "2026-02-18")
        self.assertEqual(stats[new_app_id]["company"], "Renamed Company")

    def test_rename_application_updates_folder_name_when_id_unchanged(self):
        app_id = self.manager.add_application("2026-02-17", "A/B Co", "Denmark", "Unknown")

        ok, same_app_id = self.manager.rename_application(app_id, "2026-02-17", "AB Co")
        self.assertTrue(ok)
        self.assertEqual(app_id, same_app_id)

        stats = self.manager.get_stats()
        self.assertEqual(stats[same_app_id]["company"], "AB Co")
        self.assertEqual(stats[same_app_id]["folder_name"], "AB_Co")

if __name__ == "__main__":
    unittest.main()
