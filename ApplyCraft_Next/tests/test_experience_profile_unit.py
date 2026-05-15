import os
import shutil
import tempfile
import unittest

from core import experience_profile as ep
from core.config import JOB_POSITIONS


class TestExperienceProfile(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="applycraft_profile_test_")
        self._orig_dir = ep.PROFILE_DIR
        self._orig_path = ep.PROFILE_PATH
        ep.PROFILE_DIR = self.temp_dir
        ep.PROFILE_PATH = os.path.join(self.temp_dir, "profile.json")

    def tearDown(self):
        ep.PROFILE_DIR = self._orig_dir
        ep.PROFILE_PATH = self._orig_path
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_bootstrap_profile_from_legacy_defaults(self):
        profile = ep.load_profile()
        self.assertTrue(os.path.exists(ep.PROFILE_PATH))
        self.assertEqual(profile["profile_version"], ep.PROFILE_VERSION)
        self.assertIn("candidate", profile)
        self.assertEqual(len(profile["experiences"]), len(JOB_POSITIONS))
        self.assertTrue(all("anchor_key" in item for item in profile["experiences"]))
        self.assertTrue(all("include_in_cv" in item for item in profile["experiences"]))

    def test_profile_persistence(self):
        profile = ep.load_profile()
        profile["experiences"][0]["company"] = "Custom Co"
        profile["experiences"][0]["title"] = "Custom Title"
        profile["experiences"][0]["date_range"] = "2024 - Present"
        profile["experiences"][0]["location"] = "Berlin, Germany"
        profile["experiences"][0]["bullets"] = ["Only this bullet should persist"]
        profile["candidate"]["name"] = "Jane Doe"
        profile["candidate"]["show_relocation_visa_line"] = True
        ep.save_profile(profile)
        loaded = ep.load_profile()
        self.assertEqual(loaded["experiences"][0]["company"], "Custom Co")
        self.assertEqual(loaded["experiences"][0]["title"], "Custom Title")
        self.assertEqual(loaded["experiences"][0]["date_range"], "2024 - Present")
        self.assertEqual(loaded["experiences"][0]["location"], "Berlin, Germany")
        self.assertEqual(loaded["experiences"][0]["bullets"], ["Only this bullet should persist"])
        self.assertEqual(loaded["candidate"]["name"], "Jane Doe")
        self.assertTrue(loaded["candidate"]["show_relocation_visa_line"])

    def test_legacy_profile_is_migrated_to_v2(self):
        legacy = {
            "profile_version": 1,
            "summary": "Legacy summary",
            "experiences": [
                {
                    "anchor_key": "exp_legacy",
                    "legacy_key": "Legacy Co - Analyst",
                    "company": "Legacy Co",
                    "title": "Analyst",
                    "aliases": [],
                    "bullets": ["Legacy bullet"],
                }
            ],
        }
        with open(ep.PROFILE_PATH, "w", encoding="utf-8") as handle:
            import json

            json.dump(legacy, handle)

        loaded = ep.load_profile()
        self.assertEqual(loaded["profile_version"], ep.PROFILE_VERSION)
        self.assertIn("candidate", loaded)
        self.assertIn("date_range", loaded["experiences"][0])
        self.assertIn("location", loaded["experiences"][0])
        self.assertIn("include_in_cv", loaded["experiences"][0])
        self.assertTrue(loaded["experiences"][0]["aliases"])

    def test_auto_sort_with_aliases_and_unmatched_capture(self):
        experiences = [
            {
                "anchor_key": "exp_1",
                "company": "Alpha Corp",
                "title": "Data Analyst",
                "aliases": ["Alpha", "AlphaCorp"],
                "bullets": [],
            },
            {
                "anchor_key": "exp_2",
                "company": "Beta Labs",
                "title": "Data Scientist",
                "aliases": ["Beta"],
                "bullets": [],
            },
        ]
        raw = "\n".join(
            [
                "General note before any role",
                "Alpha - Data Analyst",
                "- Built dashboard",
                "2024 - 2025",
                "Beta Labs | Data Scientist",
                "- Automated ETL",
                "Random line not tied to any section",
            ]
        )
        sorted_map, unmatched = ep.auto_sort_experience_lines(raw, experiences)
        self.assertIn("exp_1", sorted_map)
        self.assertIn("exp_2", sorted_map)
        self.assertEqual(sorted_map["exp_1"], ["Built dashboard"])
        self.assertEqual(sorted_map["exp_2"], ["Automated ETL", "Random line not tied to any section"])
        self.assertEqual(unmatched, ["General note before any role"])


if __name__ == "__main__":
    unittest.main()
