from typing import List, Optional, Dict
from pydantic import BaseModel

class StyleSignature(BaseModel):
    style_name: Optional[str] = None
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False
    alignment: str = "left"
    indent_left: float = 0.0

class ParagraphData(BaseModel):
    index: int
    text: str
    style_name: str
    signature: StyleSignature
    is_bullet: bool = False
    location: str = "body" # body, table_cell
    confidence: float = 0.0 # Used for heuristic guesses

class SectionInference(BaseModel):
    section_type: str # Experience, Education, Skills, Header, Other
    start_index: int
    end_index: int
    confidence: float

class ExperienceBlock(BaseModel):
    company_idx: Optional[int] = None
    role_idx: Optional[int] = None
    location_idx: Optional[int] = None
    date_idx: Optional[int] = None
    bullet_start_idx: Optional[int] = None
    bullet_end_idx: Optional[int] = None
    
    # Ground truth labels provided by user
    company_label: Optional[str] = ""
    role_label: Optional[str] = ""
    date_label: Optional[str] = ""

class TemplateAnalysis(BaseModel):
    paragraphs: List[ParagraphData]
    inferred_sections: List[SectionInference]
    inferred_experience_blocks: List[ExperienceBlock]

class TemplateConfig(BaseModel):
    """The final source of truth for a template"""
    template_hash: str
    experience_section: Dict[str, int] # {"start": idx, "end": idx}
    item_pattern: Dict[str, int] # Relative offsets for company, role, dates
    bullet_style: Optional[StyleSignature] = None
    header_mapping: Dict[str, int] # Index for Name, Contact, etc.
    labeled_blocks: List[ExperienceBlock] = [] # New: Stores the learned map
