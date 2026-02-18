
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

if __name__ == "__main__":
    unittest.main()
