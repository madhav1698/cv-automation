"""Integration test for job-aware bullet replacement in update_cv."""

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
        "Built and maintained analytics-ready data models across bronze, silver, and gold layers.",
        "Standardized heterogeneous datasets via SQL transformations and entity mappings.",
        "Validated schemas and metadata for more reliable downstream models.",
        "Automated data preparation and validation using Python.",
        "Translated ambiguous requirements into transparent, maintainable data models.",
    ],
    "REPHRAIN, University of Bristol - Research Data Scientist": [
        "Designed unified data models across structured and unstructured sources.",
        "Built Python-based data quality tooling and reduced assessment time.",
        "Explained data transformations and assumptions to non-technical stakeholders.",
        "Delivered reproducible analytics aligned with governance requirements.",
    ],
    "IBA GROUP - Data Scientist": [
        "Automated ETL pipelines using Python and SQL.",
        "Modeled aviation datasets for performance monitoring and anomaly detection.",
        "Translated business needs into decision-ready datasets.",
    ],
    "BRISTOL DIGITAL FUTURES INSTITUTE - Data Analyst": [
        "Analyzed multi-source telecom datasets for senior stakeholders.",
        "Built dashboards on top of reusable analytical datasets.",
    ],
}

TEST_SUMMARY = (
    "Analytics engineer with 5+ years building data models and transformation pipelines "
    "across complex, multi-source environments."
)


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


class TestJobAwareUpdateCV(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template_path = _first_existing_template()
        if not cls.template_path:
            raise unittest.SkipTest("No .docx template found for integration test")

    def test_job_aware_update_cv_generates_docx(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_file = os.path.join(tmp, "test_job_aware_cv.docx")
            update_cv_bullets(
                input_file=self.template_path,
                output_file=output_file,
                custom_summary=TEST_SUMMARY,
                custom_bullets=TEST_BULLETS,
            )
            self.assertTrue(os.path.exists(output_file))


if __name__ == "__main__":
    unittest.main()
