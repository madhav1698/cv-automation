import os
import sys
from datetime import datetime

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from helpers.logger import logger
from core.config import SUPPORTED_CV_TEMPLATES
from core.update_cv import update_cv_bullets, convert_to_pdf
from core.generate_cover_letter import generate_cover_letter

class CVGeneratorService:
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager

    @staticmethod
    def is_supported_template(template_path):
        if not template_path:
            return False
        candidate = os.path.normcase(os.path.abspath(template_path))
        allowed = {
            os.path.normcase(os.path.abspath(path))
            for path in SUPPORTED_CV_TEMPLATES.values()
        }
        return candidate in allowed

    def generate_cv(self, template_path, company, country, summary, bullets, experiences=None, candidate_profile=None):
        try:
            if not self.is_supported_template(template_path):
                msg = "Unsupported template: only Template 1 and Template 2 are allowed"
                logger.error(msg)
                return False, msg

            timestamp = datetime.now().strftime("%d-%m-%y")
            output_dir = os.path.join(self.stats_manager.outputs_dir, timestamp, company.replace(" ", "_"))
            os.makedirs(output_dir, exist_ok=True)
            
            comp_clean = company.replace(" ", "_")
            cnt_clean = country.replace(" ", "_")
            output_docx = os.path.join(output_dir, f"CV_{comp_clean}_{cnt_clean}.docx")
            output_pdf = output_docx.replace(".docx", ".pdf")

            logger.info(f"Using strict supported-template renderer for {company}")
            update_cv_bullets(
                template_path,
                output_docx,
                summary,
                bullets,
                custom_experiences=experiences,
                candidate_profile=candidate_profile,
            )
            
            # 2. Convert to PDF
            convert_to_pdf(output_docx, output_pdf)
            
            # 3. Update Stats
            self.stats_manager.add_application(timestamp, company, country, status="Unknown", manual=False)
            
            logger.info(f"Generated CV for {company} in {country}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate CV: {e}")
            return False, str(e)

    def generate_cl(self, company, cl_data, candidate_profile=None):
        try:
            timestamp = datetime.now().strftime("%d-%m-%y")
            output_dir = os.path.join(self.stats_manager.outputs_dir, timestamp, company.replace(" ", "_"))
            os.makedirs(output_dir, exist_ok=True)
            
            comp_clean = company.replace(" ", "_")
            cnt_clean = cl_data["country"].replace(" ", "_")
            output_docx = os.path.join(output_dir, f"Cover_Letter_{comp_clean}_{cnt_clean}.docx")
            output_pdf = output_docx.replace(".docx", ".pdf")
            candidate_name = ""
            if isinstance(candidate_profile, dict):
                candidate_name = str(candidate_profile.get("name", "")).strip()
            
            generate_cover_letter(
                output_path=output_docx,
                company_name=company,
                city=cl_data["city"],
                country=cl_data["country"],
                date_str=cl_data["date"],
                body_text=cl_data["body"],
                hiring_manager=cl_data["hiring_manager"],
                candidate_name=candidate_name,
            )
            
            # Convert the CL docx to pdf
            convert_to_pdf(output_docx, output_pdf)
            
            logger.info(f"Generated Cover Letter for {company}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate Cover Letter: {e}")
            return False, str(e)

    def generate_both(self, template_path, company, cv_country, summary, bullets, cl_data, experiences=None, candidate_profile=None):
        cv_success, cv_result = self.generate_cv(
            template_path,
            company,
            cv_country,
            summary,
            bullets,
            experiences=experiences,
            candidate_profile=candidate_profile,
        )
        cl_success, cl_result = self.generate_cl(company, cl_data, candidate_profile=candidate_profile)
        
        return cv_success and cl_success, (cv_result, cl_result)
