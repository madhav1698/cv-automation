import os
import threading
import sys
from datetime import datetime

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from helpers.logger import logger
from core.update_cv import update_cv_bullets, convert_to_pdf
from core.generate_cover_letter import generate_cover_letter

class CVGeneratorService:
    def __init__(self, stats_manager):
        self.stats_manager = stats_manager

    def generate_cv(self, template_path, company, country, summary, bullets):
        try:
            timestamp = datetime.now().strftime("%d-%m-%y")
            output_dir = os.path.join(self.stats_manager.outputs_dir, timestamp, company.replace(" ", "_"))
            os.makedirs(output_dir, exist_ok=True)
            
            output_docx = os.path.join(output_dir, f"Madhav_Manohar_Gopal_CV_{country.replace(' ', '_')}.docx")
            output_pdf = output_docx.replace(".docx", ".pdf")
            
            # 1. Update Word Doc
            update_cv_bullets(template_path, output_docx, bullets, summary)
            
            # 2. Convert to PDF
            convert_to_pdf(output_docx, output_pdf)
            
            # 3. Update Stats
            self.stats_manager.add_application(timestamp, company, country, status="In Process", manual=False)
            
            logger.info(f"Generated CV for {company} in {country}")
            return True, output_pdf
        except Exception as e:
            logger.error(f"Failed to generate CV: {e}")
            return False, str(e)

    def generate_cl(self, company, cl_data):
        try:
            timestamp = datetime.now().strftime("%d-%m-%y")
            output_dir = os.path.join(self.stats_manager.outputs_dir, timestamp, company.replace(" ", "_"))
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, f"Cover_Letter_{company.replace(' ', '_')}.pdf")
            
            generate_cover_letter(
                output_path,
                cl_data["hiring_manager"],
                company,
                cl_data["city"],
                cl_data["country"],
                cl_data["date"],
                cl_data["body"]
            )
            
            logger.info(f"Generated Cover Letter for {company}")
            return True, output_path
        except Exception as e:
            logger.error(f"Failed to generate Cover Letter: {e}")
            return False, str(e)

    def generate_both(self, template_path, company, cv_country, summary, bullets, cl_data):
        cv_success, cv_result = self.generate_cv(template_path, company, cv_country, summary, bullets)
        cl_success, cl_result = self.generate_cl(company, cl_data)
        
        return cv_success and cl_success, (cv_result, cl_result)
