import json
import hashlib
from typing import Dict, Any
from .schemas import TemplateAnalysis, TemplateConfig, ExperienceBlock

class TemplateLearner:
    def __init__(self, analysis: TemplateAnalysis, docx_path: str):
        self.analysis = analysis
        self.docx_path = docx_path

    def learn(self, corrections: Dict[str, Any] = None) -> TemplateConfig:
        """
        Synthesizes an Analysis + Optional Corrections into a stable Config.
        """
        # 1. Generate Fingerprint
        with open(self.docx_path, "rb") as f:
            template_hash = hashlib.md5(f.read()).hexdigest()

        # 2. Extract Experience Section Bounds
        # (For now, just take the first experience section found)
        exp_sec = next((s for s in self.analysis.inferred_sections if s.section_type == "Experience"), None)
        
        if not exp_sec:
            raise ValueError("No Experience section detected. Learning failed.")

        # 3. Analyze the 'Pattern' of an experience item
        # We look at the first block and determine relative steps
        # e.g. Company is at Para 0, Role is at Para 1, Bullets start at Para 2
        first_block = self.analysis.inferred_experience_blocks[0] if self.analysis.inferred_experience_blocks else None
        
        item_pattern = {}
        if first_block:
            base = first_block.company_idx or first_block.role_idx
            if first_block.company_idx is not None:
                item_pattern["company_offset"] = first_block.company_idx - base
            if first_block.role_idx is not None:
                item_pattern["role_offset"] = first_block.role_idx - base
            if first_block.date_idx is not None:
                item_pattern["date_offset"] = first_block.date_idx - base
            if first_block.bullet_start_idx is not None:
                item_pattern["bullet_start_offset"] = first_block.bullet_start_idx - base

        # 4. Capture the bullet style signature
        bullet_sig = None
        if first_block and first_block.bullet_start_idx is not None:
            bullet_sig = self.analysis.paragraphs[first_block.bullet_start_idx].signature
            # We already populated style_name in analyzer, but let's be sure
            if not bullet_sig.style_name:
                bullet_sig.style_name = self.analysis.paragraphs[first_block.bullet_start_idx].style_name

        return TemplateConfig(
            template_hash=template_hash,
            experience_section={"start": exp_sec.start_index, "end": exp_sec.end_index},
            item_pattern=item_pattern,
            bullet_style=bullet_sig,
            header_mapping={}, # To be expanded for Name/Contact
            labeled_blocks=self.analysis.inferred_experience_blocks
        )

    def save_config(self, config: TemplateConfig, output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=4))
