"""
core/cv_service.py
-------------------
Thin orchestration layer that the GUI calls into when the user clicks
"Generate CV", "Generate Cover Letter", or "Generate Both". This module
deliberately stays short — the heavy lifting lives in :mod:`core.update_cv`
(template-aware docx surgery) and :mod:`core.generate_cover_letter`.

Filenames are derived from ``user_config.filename_slug()`` so the tool is
no longer tied to one person's name.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

# Path bootstrap so this module works whether imported as ``core.cv_service``
# or run from the project root.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from helpers.logger import logger
from helpers import user_config
from core.update_cv import update_cv_bullets, convert_to_pdf
from core.generate_cover_letter import generate_cover_letter


def _safe_segment(value: str) -> str:
    """Make a string filesystem-safe (no spaces, no weird punctuation)."""
    return (value or "").strip().replace(" ", "_")


class CVGeneratorService:
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
    """Coordinates CV + Cover Letter generation and stats logging.

    Construction takes a :class:`StatsManager` so that the moment a CV is
    generated, the application is registered in the tracker.
    """

    def __init__(self, stats_manager):
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
=======
    def __init__(self, stats_manager, user_profile=None):
>>>>>>> theirs
        self.stats_manager = stats_manager
        self.user_profile = user_profile

    # ------------------------------------------------------------------
    # CV
    # ------------------------------------------------------------------
    def generate_cv(
        self,
        template_path,
        company,
        country,
        summary,
        bullets,
        headlines=None,
        current_location=None,
    ):
        try:
            slug = user_config.filename_slug()
            timestamp = datetime.now().strftime("%d-%m-%y")
            output_dir = os.path.join(
                self.stats_manager.outputs_dir,
                timestamp,
                _safe_segment(company),
            )
            os.makedirs(output_dir, exist_ok=True)
<<<<<<< ours

            comp_clean = _safe_segment(company)
            cnt_clean = _safe_segment(country)
            filename = f"{slug}_CV_{comp_clean}_{cnt_clean}.docx"
            output_docx = os.path.join(output_dir, filename)
=======
            
            comp_clean = company.replace(" ", "_")
            cnt_clean = country.replace(" ", "_")
            candidate_slug = (self.user_profile.slug if self.user_profile else "Candidate")
            output_docx = os.path.join(output_dir, f"{candidate_slug}_CV_{comp_clean}_{cnt_clean}.docx")
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
            output_pdf = output_docx.replace(".docx", ".pdf")

            # 1. Update Word Doc
            update_cv_bullets(
                template_path,
                output_docx,
                summary,
                bullets,
                custom_headlines=headlines,
                current_location=current_location,
            )

            # 2. Convert to PDF
            convert_to_pdf(output_docx, output_pdf)

            # 3. Register in stats
            self.stats_manager.add_application(
                timestamp, company, country, status="Unknown", manual=False
            )

            logger.info(f"Generated CV for {company} in {country}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate CV: {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Cover Letter
    # ------------------------------------------------------------------
    def generate_cl(self, company, cl_data):
        try:
            slug = user_config.filename_slug()
            timestamp = datetime.now().strftime("%d-%m-%y")
            output_dir = os.path.join(
                self.stats_manager.outputs_dir,
                timestamp,
                _safe_segment(company),
            )
            os.makedirs(output_dir, exist_ok=True)
<<<<<<< ours

            comp_clean = _safe_segment(company)
            cnt_clean = _safe_segment(cl_data.get("country", ""))
            filename = f"{slug}_Cover_Letter_{comp_clean}_{cnt_clean}.docx"
            output_docx = os.path.join(output_dir, filename)
=======
            
            comp_clean = company.replace(" ", "_")
            cnt_clean = cl_data["country"].replace(" ", "_")
            candidate_slug = (self.user_profile.slug if self.user_profile else "Candidate")
            output_docx = os.path.join(output_dir, f"{candidate_slug}_Cover_Letter_{comp_clean}_{cnt_clean}.docx")
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
            output_pdf = output_docx.replace(".docx", ".pdf")

            generate_cover_letter(
                output_path=output_docx,
                company_name=company,
                city=cl_data["city"],
                country=cl_data["country"],
                date_str=cl_data["date"],
                body_text=cl_data["body"],
                hiring_manager=cl_data["hiring_manager"],
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
=======
                candidate_name=(self.user_profile.full_name if self.user_profile else "Candidate")
>>>>>>> theirs
            )

            convert_to_pdf(output_docx, output_pdf)

            logger.info(f"Generated Cover Letter for {company}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate Cover Letter: {e}")
            return False, str(e)

    # ------------------------------------------------------------------
    # Both
    # ------------------------------------------------------------------
    def generate_both(
        self,
        template_path,
        company,
        cv_country,
        summary,
        bullets,
        cl_data,
        headlines=None,
        current_location=None,
    ):
        cv_success, cv_result = self.generate_cv(
            template_path, company, cv_country, summary, bullets,
            headlines=headlines, current_location=current_location,
        )
        cl_success, cl_result = self.generate_cl(company, cl_data)
        return cv_success and cl_success, (cv_result, cl_result)
