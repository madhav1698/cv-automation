"""Integration test for flexible bullet counts in update_cv."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.update_cv import update_cv_bullets
from helpers import user_config


TEST_BULLETS = {
    "PEERMUSIC - Data Analytics Developer": [
        "First bullet for Peermusic",
        "Second bullet for Peermusic",
        "Third bullet for Peermusic",
    ],
    "REPHRAIN, University of Bristol - Research Data Scientist": [
        "First bullet for REPHRAIN",
        "Second bullet for REPHRAIN",
        "Third bullet for REPHRAIN",
        "Fourth bullet for REPHRAIN",
        "Fifth bullet for REPHRAIN",
        "Sixth bullet for REPHRAIN",
        "Seventh bullet for REPHRAIN - THIS IS NEW!",
    ],
    "IBA GROUP - Data Scientist": [
        "First bullet for IBA",
        "Second bullet for IBA",
        "Third bullet for IBA",
        "Fourth bullet for IBA",
        "Fifth bullet for IBA",
    ],
    "BRISTOL DIGITAL FUTURES INSTITUTE - Data Analyst": [
        "First bullet for Bristol",
        "Second bullet for Bristol",
    ],
}

TEST_SUMMARY = "Test summary for flexible bullet counts."


def _first_existing_template() -> str:
    templates = user_config.resolved_template_paths()
    for path in templates.values():
        if path and os.path.exists(path):
            return path

    templates_dir = os.path.join(ROOT, "templates")
    if os.path.isdir(templates_dir):
        for name in os.listdir(templates_dir):
            if name.lower().endswith(".docx"):
                return os.path.join(templates_dir, name)

    return ""


class TestFlexibleUpdateCV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_path = _first_existing_template()
        if not cls.template_path:
            raise unittest.SkipTest("No .docx template found for integration test")

    def test_update_cv_accepts_flexible_bullet_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_file = os.path.join(tmp, "test_flexible_bullets.docx")
            update_cv_bullets(
                input_file=self.template_path,
                output_file=output_file,
                custom_summary=TEST_SUMMARY,
                custom_bullets=TEST_BULLETS,
            )
            self.assertTrue(os.path.exists(output_file))


if __name__ == "__main__":
    unittest.main()
