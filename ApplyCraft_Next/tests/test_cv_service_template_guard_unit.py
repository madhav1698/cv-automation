import os
import tempfile
import unittest

from core.cv_service import CVGeneratorService


class _DummyStatsManager:
    def __init__(self, base_dir):
        self.outputs_dir = base_dir

    def add_application(self, *args, **kwargs):
        return "dummy"


class TestCVServiceTemplateGuard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="applycraft_cv_service_")
        self.service = CVGeneratorService(_DummyStatsManager(self.temp_dir))

    def test_unsupported_template_is_rejected(self):
        success, msg = self.service.generate_cv(
            template_path=os.path.join(self.temp_dir, "custom_template.docx"),
            company="Test Co",
            country="UK",
            summary="summary",
            bullets={},
            experiences=[],
        )
        self.assertFalse(success)
        self.assertIn("Unsupported template", msg)


if __name__ == "__main__":
    unittest.main()
