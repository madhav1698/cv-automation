"""
core/cv_service.py
-------------------
Thin orchestration layer for CV and cover letter generation.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from helpers import user_config
from helpers.logger import logger
from core.generate_cover_letter import generate_cover_letter
from core.update_cv import convert_to_pdf, update_cv_bullets


def _safe_segment(value: str) -> str:
    """Make a string safe for filesystem paths."""
    return (value or "").strip().replace(" ", "_")


class CVGeneratorService:
    """Coordinate CV + cover-letter generation and stats writes."""

    def __init__(self, stats_manager):
        self.stats_manager = stats_manager

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

            comp_clean = _safe_segment(company)
            cnt_clean = _safe_segment(country)
            filename = f"{slug}_CV_{comp_clean}_{cnt_clean}.docx"
            output_docx = os.path.join(output_dir, filename)
            output_pdf = output_docx.replace(".docx", ".pdf")

            update_cv_bullets(
                template_path,
                output_docx,
                summary,
                bullets,
                custom_headlines=headlines,
                current_location=current_location,
            )
            convert_to_pdf(output_docx, output_pdf)

            self.stats_manager.add_application(
                timestamp, company, country, status="Unknown", manual=False
            )

            logger.info(f"Generated CV for {company} in {country}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate CV: {e}")
            return False, str(e)

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

            comp_clean = _safe_segment(company)
            cnt_clean = _safe_segment(cl_data.get("country", ""))
            filename = f"{slug}_Cover_Letter_{comp_clean}_{cnt_clean}.docx"
            output_docx = os.path.join(output_dir, filename)
            output_pdf = output_docx.replace(".docx", ".pdf")

            generate_cover_letter(
                output_path=output_docx,
                company_name=company,
                city=cl_data["city"],
                country=cl_data["country"],
                date_str=cl_data["date"],
                body_text=cl_data["body"],
                hiring_manager=cl_data["hiring_manager"],
            )
            convert_to_pdf(output_docx, output_pdf)

            logger.info(f"Generated Cover Letter for {company}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate Cover Letter: {e}")
            return False, str(e)

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
            template_path,
            company,
            cv_country,
            summary,
            bullets,
            headlines=headlines,
            current_location=current_location,
        )
        cl_success, cl_result = self.generate_cl(company, cl_data)
        return cv_success and cl_success, (cv_result, cl_result)
