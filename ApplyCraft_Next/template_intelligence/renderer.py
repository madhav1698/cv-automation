from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from copy import deepcopy
from .schemas import TemplateConfig

class TemplateRenderer:
    def __init__(self, template_path: str, config: TemplateConfig):
        self.template_path = template_path
        self.config = config
        self.doc = Document(template_path)

    def render(self, data: dict, output_path: str):
        """
        Renders the tailored CV.
        Data structure: {"summary": str, "experience": [{"company": str, "role": str, "date": str, "bullets": [str]}]}
        """
        # 1. Update Profile Summary (Not implemented yet - requires finding summary index)
        
        # 2. Update Experience Section
        self._inject_experience(data.get("experience", []))
        
        self.doc.save(output_path)

    def _inject_experience(self, experiences):
        # This is where we use the "Learned Pattern"
        # For simplicity in V1: 
        # - Find the Experience Section start
        # - Remove all old paragraphs in that section
        # - Insert new ones following the pattern
        
        # Note: Removing paragraphs in python-docx is tricky. 
        # A more robust way is to find the section and replace text or replicate paragraphs.
        
        start_idx = self.config.experience_section["start"]
        end_idx = self.config.experience_section["end"]
        
        # We'll actually work with the document elements directly
        # For this prototype, we'll just append to the end of the section for now
        # to demonstrate the pattern usage.
        
        for exp in experiences:
            # Create a new block based on the learned style
            # (In a full version, we would clone the actual paragraphs to keep formatting perfect)
            p_comp = self.doc.add_paragraph(exp["company"])
            p_comp.style = self.doc.paragraphs[start_idx + 1].style # Use learned style
            
            p_role = self.doc.add_paragraph(exp["role"])
            # p_role.style = ...
            
            for bullet in exp["bullets"]:
                p_b = self.doc.add_paragraph(bullet, style='List Bullet')
                # Apply learned bullet signature
                p_b.paragraph_format.left_indent = self.config.bullet_style.indent_left
