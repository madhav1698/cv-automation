import copy
import os
import re
import shutil
import sys
from datetime import datetime

import PyPDF2
import comtypes.client
import pythoncom
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config import JOB_POSITIONS, SUMMARY_TEXT
from helpers.logger import logger

dummy_bullets = [bullet for bullets in JOB_POSITIONS.values() for bullet in bullets]
_BULLET_PREFIXES = ("-", "*", "\u2022", "\u00b7", "\u2023", "\u25e6")
_MONTH_PATTERN = re.compile(
    r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|october|november|december)\b"
)


def _is_bullet_paragraph(paragraph):
    style_name = paragraph.style.name.lower() if paragraph.style and paragraph.style.name else ""
    if "list" in style_name or "bullet" in style_name:
        return True

    if paragraph._element.pPr is not None:
        num_pr = paragraph._element.pPr.numPr
        if num_pr is not None:
            return True

    text = paragraph.text.strip()
    return any(text.startswith(prefix) for prefix in _BULLET_PREFIXES)


def _is_italic_paragraph(paragraph):
    if not paragraph or not paragraph.runs:
        return False
    return any(run.italic for run in paragraph.runs if run.text.strip())


def _replace_paragraph_text(paragraph, text_value, force_italic=None, force_bold=None, force_font_size=None):
    run0 = paragraph.runs[0] if paragraph.runs else None
    font_name = run0.font.name if run0 and run0.font else None
    font_size = run0.font.size if run0 and run0.font else None
    is_bold = run0.bold if run0 else None
    is_italic = run0.italic if run0 else None

    paragraph.clear()
    new_run = paragraph.add_run(text_value)
    if font_name:
        new_run.font.name = font_name
    if force_font_size is not None:
        new_run.font.size = force_font_size
    elif font_size:
        new_run.font.size = font_size
    if force_bold is not None:
        new_run.bold = force_bold
    elif is_bold is not None:
        new_run.bold = is_bold
    if force_italic is not None:
        new_run.italic = force_italic
    elif is_italic is not None:
        new_run.italic = is_italic


def _style_headline_paragraph(paragraph):
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(2)
    fmt.space_after = Pt(4)
    fmt.left_indent = Pt(15)


def _normalize_heading(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _find_section_bounds(doc, start_titles, end_titles):
    elements = list(doc.element.body)
    paragraph_lookup = {p._element: p for p in doc.paragraphs}
    start_idx = None
    end_idx = len(elements)

    for idx, element in enumerate(elements):
        para = paragraph_lookup.get(element)
        if para is None:
            continue
        heading = _normalize_heading(para.text)
        if start_idx is None and heading in start_titles:
            start_idx = idx + 1
            continue
        if start_idx is not None and heading in end_titles:
            end_idx = idx
            break

    if start_idx is None:
        start_idx = 0
    return start_idx, end_idx


def _detect_template_type(doc):
    if len(doc.tables) > 0:
        return "template_1"
    return "template_2"


def _format_contact_line(candidate_profile):
    location = str(candidate_profile.get("location", "")).strip()
    email = str(candidate_profile.get("email", "")).strip()
    linkedin = str(candidate_profile.get("linkedin", "")).strip()
    parts = [part for part in [location, email, linkedin] if part]
    return " | ".join(parts)


def _update_identity(doc, template_type, candidate_profile):
    if not isinstance(candidate_profile, dict):
        return

    candidate_name = str(candidate_profile.get("name", "")).strip()
    email = str(candidate_profile.get("email", "")).strip()
    linkedin = str(candidate_profile.get("linkedin", "")).strip()

    if template_type == "template_2":
        if doc.paragraphs and candidate_name:
            _replace_paragraph_text(doc.paragraphs[0], candidate_name, force_bold=True)
        if len(doc.paragraphs) > 1:
            contact_line = _format_contact_line(candidate_profile)
            if contact_line:
                _replace_paragraph_text(doc.paragraphs[1], contact_line)
        return

    summary_idx = None
    for idx, paragraph in enumerate(doc.paragraphs):
        if _normalize_heading(paragraph.text) == "summary":
            summary_idx = idx
            break
    if summary_idx is None:
        summary_idx = len(doc.paragraphs)

    pre_summary = [p for p in doc.paragraphs[:summary_idx] if p.text.strip()]
    if not pre_summary:
        return

    if candidate_name:
        _replace_paragraph_text(pre_summary[0], candidate_name, force_bold=True)
    if len(pre_summary) > 1 and email:
        _replace_paragraph_text(pre_summary[1], email)
    if len(pre_summary) > 2 and linkedin:
        _replace_paragraph_text(pre_summary[2], linkedin)


def _build_summary_line(summary_text, candidate_profile):
    summary = (summary_text or "").strip() or SUMMARY_TEXT
    if not isinstance(candidate_profile, dict):
        return summary
    if not bool(candidate_profile.get("show_relocation_visa_line", False)):
        return summary
    relocation_line = str(candidate_profile.get("relocation_visa_line", "")).strip()
    if not relocation_line:
        return summary
    return f"{summary} {relocation_line}"


def _update_summary(doc, summary_text, candidate_profile):
    target_idx = None
    for idx, paragraph in enumerate(doc.paragraphs):
        if _normalize_heading(paragraph.text) == "summary":
            target_idx = idx + 1
            break

    if target_idx is None:
        legacy_marker = "EU citizen, no visa required to work in EU."
        for idx, paragraph in enumerate(doc.paragraphs):
            if legacy_marker in paragraph.text:
                target_idx = idx
                break

    if target_idx is None or target_idx >= len(doc.paragraphs):
        return

    target_para = doc.paragraphs[target_idx]
    target_para.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
    _replace_paragraph_text(target_para, _build_summary_line(summary_text, candidate_profile))


def _cell_first_paragraph(cell):
    if cell.paragraphs:
        return cell.paragraphs[0]
    return None


def _set_cell_text(cell, text_value):
    if not cell.paragraphs:
        cell.text = text_value
        return
    first = cell.paragraphs[0]
    _replace_paragraph_text(first, text_value)
    for extra in list(cell.paragraphs[1:]):
        parent = extra._element.getparent()
        if parent is not None:
            parent.remove(extra._element)


def _rewrite_template1_header(slot, exp):
    table = slot["table"]
    company = str(exp.get("company", "")).strip()
    title = str(exp.get("title", "")).strip()
    date_range = str(exp.get("date_range", "")).strip()
    location = str(exp.get("location", "")).strip()

    if len(table.rows) > 0 and len(table.rows[0].cells) > 0:
        _set_cell_text(table.rows[0].cells[0], company)
    if len(table.rows) > 0 and len(table.rows[0].cells) > 1:
        _set_cell_text(table.rows[0].cells[-1], location)
    if len(table.rows) > 1 and len(table.rows[1].cells) > 0:
        _set_cell_text(table.rows[1].cells[0], title)
    if len(table.rows) > 1 and len(table.rows[1].cells) > 1:
        _set_cell_text(table.rows[1].cells[-1], date_range)


def _format_template2_meta(exp):
    company = str(exp.get("company", "")).strip()
    date_range = str(exp.get("date_range", "")).strip()
    location = str(exp.get("location", "")).strip()
    head = " ".join(part for part in [company, date_range] if part).strip()
    if location:
        return f"{head}, {location}" if head else location
    return head


def _rewrite_template2_header(slot, exp):
    title = str(exp.get("title", "")).strip()
    meta_line = _format_template2_meta(exp)
    _replace_paragraph_text(slot["title_para"], title)
    _replace_paragraph_text(slot["meta_para"], meta_line)


def _insert_paragraph_after(doc, ref_element, style_source=None):
    new_para = doc.add_paragraph("")
    ref_element.addnext(new_para._element)
    if style_source is not None:
        try:
            new_para.style = style_source.style
        except Exception:
            pass
    return new_para


def _insert_paragraph_before(doc, ref_element, style_source=None):
    new_para = doc.add_paragraph("")
    ref_element.addprevious(new_para._element)
    if style_source is not None:
        try:
            new_para.style = style_source.style
        except Exception:
            pass
    return new_para


def _update_slot_bullets(doc, slot, exp):
    headline = str(exp.get("headline", "")).strip()
    bullets = exp.get("bullets", [])
    cleaned_bullets = [str(item).strip() for item in bullets if str(item).strip()] if isinstance(bullets, list) else []
    new_lines = list(cleaned_bullets)

    existing_headline_para = slot.get("headline_paragraph")
    if headline:
        if existing_headline_para is None:
            headline_para = _insert_paragraph_after(doc, slot["insert_after_element"])
            try:
                headline_para.style = doc.styles["Normal"]
            except Exception:
                pass
            existing_headline_para = headline_para
        _replace_paragraph_text(
            existing_headline_para,
            headline,
            force_italic=True,
            force_bold=False,
            force_font_size=Pt(10),
        )
        _style_headline_paragraph(existing_headline_para)
    elif existing_headline_para is not None:
        parent = existing_headline_para._element.getparent()
        if parent is not None:
            parent.remove(existing_headline_para._element)
        existing_headline_para = None

    existing = list(slot.get("bullet_paragraphs", []))
    for idx in range(min(len(existing), len(new_lines))):
        para = existing[idx]
        _replace_paragraph_text(para, new_lines[idx], force_italic=False)

    if len(new_lines) > len(existing):
        if existing:
            ref_element = existing[-1]._element
            style_source = existing[-1]
        else:
            ref_element = slot["insert_after_element"]
            style_source = slot.get("style_paragraph")

        for idx in range(len(existing), len(new_lines)):
            para = _insert_paragraph_after(doc, ref_element, style_source=style_source)
            _replace_paragraph_text(para, new_lines[idx], force_italic=False)
            ref_element = para._element

    if len(existing) > len(new_lines):
        for idx in range(len(new_lines), len(existing)):
            para = existing[idx]
            parent = para._element.getparent()
            if parent is not None:
                parent.remove(para._element)


def _extract_template1_slots(doc):
    elements = list(doc.element.body)
    paragraph_lookup = {p._element: p for p in doc.paragraphs}
    table_lookup = {t._element: t for t in doc.tables}

    start_idx, end_idx = _find_section_bounds(
        doc,
        start_titles={"work experience", "experience"},
        end_titles={"skills", "education"},
    )

    table_indices = [
        idx for idx in range(start_idx, end_idx) if elements[idx] in table_lookup
    ]

    slots = []
    for slot_idx, table_idx in enumerate(table_indices):
        next_idx = table_indices[slot_idx + 1] if slot_idx + 1 < len(table_indices) else end_idx
        block_elements = elements[table_idx:next_idx]
        content_paragraphs = [
            paragraph_lookup[element]
            for element in block_elements[1:]
            if element in paragraph_lookup and paragraph_lookup[element].text.strip()
        ]
        headline_para = None
        if content_paragraphs:
            first = content_paragraphs[0]
            if _is_italic_paragraph(first) and not _is_bullet_paragraph(first):
                headline_para = first
        bullet_paragraphs = [para for para in content_paragraphs if para is not headline_para]
        style_para = bullet_paragraphs[0] if bullet_paragraphs else None
        slots.append(
            {
                "type": "template_1",
                "table": table_lookup[elements[table_idx]],
                "bullet_paragraphs": bullet_paragraphs,
                "headline_paragraph": headline_para,
                "insert_after_element": elements[table_idx],
                "style_paragraph": style_para,
                "elements": block_elements,
            }
        )
    return slots


def _looks_like_meta_line(text):
    cleaned = (text or "").strip()
    if not cleaned:
        return False
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", cleaned))
    has_present = "present" in cleaned.lower()
    has_month = bool(_MONTH_PATTERN.search(cleaned))
    return has_year or has_present or has_month


def _extract_template2_slots(doc):
    elements = list(doc.element.body)
    paragraph_lookup = {p._element: p for p in doc.paragraphs}
    start_idx, end_idx = _find_section_bounds(
        doc,
        start_titles={"experience", "work experience"},
        end_titles={"education", "skills"},
    )

    paragraph_indices = [
        idx
        for idx in range(start_idx, end_idx)
        if elements[idx] in paragraph_lookup and paragraph_lookup[elements[idx]].text.strip()
    ]

    slots = []
    pointer = 0
    while pointer < len(paragraph_indices) - 1:
        title_idx = paragraph_indices[pointer]
        meta_idx = paragraph_indices[pointer + 1]
        title_para = paragraph_lookup[elements[title_idx]]
        meta_para = paragraph_lookup[elements[meta_idx]]

        if not _looks_like_meta_line(meta_para.text):
            pointer += 1
            continue

        scan = pointer + 2
        bullet_indices = []
        while scan < len(paragraph_indices):
            current_idx = paragraph_indices[scan]
            current_para = paragraph_lookup[elements[current_idx]]

            if scan + 1 < len(paragraph_indices):
                next_idx = paragraph_indices[scan + 1]
                next_para = paragraph_lookup[elements[next_idx]]
                if _looks_like_meta_line(next_para.text) and not _looks_like_meta_line(current_para.text):
                    break

            bullet_indices.append(current_idx)
            scan += 1

        block_end = paragraph_indices[scan] if scan < len(paragraph_indices) else end_idx
        block_elements = elements[title_idx:block_end]
        bullet_paragraphs = [paragraph_lookup[elements[idx]] for idx in bullet_indices]
        headline_para = None
        if bullet_paragraphs and _is_italic_paragraph(bullet_paragraphs[0]):
            headline_para = bullet_paragraphs[0]
            bullet_paragraphs = bullet_paragraphs[1:]
        style_para = bullet_paragraphs[0] if bullet_paragraphs else title_para

        slots.append(
            {
                "type": "template_2",
                "title_para": title_para,
                "meta_para": meta_para,
                "bullet_paragraphs": bullet_paragraphs,
                "headline_paragraph": headline_para,
                "insert_after_element": meta_para._element,
                "style_paragraph": style_para,
                "elements": block_elements,
            }
        )
        pointer = scan

    return slots


def _extract_slots(doc, template_type):
    if template_type == "template_1":
        return _extract_template1_slots(doc)
    return _extract_template2_slots(doc)


def _remove_slot(slot):
    for element in reversed(slot.get("elements", [])):
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)


def _append_overflow_experiences(doc, template_type, experiences, start_idx):
    if not experiences:
        return 0

    elements = list(doc.element.body)
    if template_type == "template_1":
        _, end_idx = _find_section_bounds(
            doc,
            start_titles={"work experience", "experience"},
            end_titles={"skills", "education"},
        )
    else:
        _, end_idx = _find_section_bounds(
            doc,
            start_titles={"experience", "work experience"},
            end_titles={"education", "skills"},
        )

    if end_idx < len(elements):
        ref_element = elements[end_idx]
    elif elements:
        ref_element = elements[-1]
    else:
        ref_element = None

    appended = 0
    for exp in experiences[start_idx:]:
        company = str(exp.get("company", "")).strip()
        title = str(exp.get("title", "")).strip()
        date_range = str(exp.get("date_range", "")).strip()
        location = str(exp.get("location", "")).strip()
        headline = str(exp.get("headline", "")).strip()
        bullets = [str(item).strip() for item in exp.get("bullets", []) if str(item).strip()]

        header = " | ".join(part for part in [company, title] if part) or "Experience"
        meta = " | ".join(part for part in [date_range, location] if part)
        lines = [header]
        if meta:
            lines.append(meta)
        if headline:
            lines.append(headline)
        lines.extend(f"• {bullet}" for bullet in bullets)
        lines.append("")

        for line in lines:
            if ref_element is not None:
                para = _insert_paragraph_before(doc, ref_element)
            else:
                para = doc.add_paragraph("")
            _replace_paragraph_text(
                para,
                line,
                force_italic=True if line == headline and headline else None,
                force_font_size=Pt(10) if line == headline and headline else None,
            )
            if line == headline and headline:
                _style_headline_paragraph(para)
        appended += 1

    return appended


def _normalize_experience_inputs(custom_experiences, custom_bullets):
    if isinstance(custom_experiences, list) and custom_experiences:
        normalized = []
        for exp in custom_experiences:
            if not isinstance(exp, dict):
                continue
            bullets_raw = exp.get("bullets", [])
            bullets = [str(item).strip() for item in bullets_raw if str(item).strip()] if isinstance(bullets_raw, list) else []
            normalized.append(
                {
                    "company": str(exp.get("company", "")).strip(),
                    "title": str(exp.get("title", "")).strip(),
                    "date_range": str(exp.get("date_range", "")).strip(),
                    "location": str(exp.get("location", "")).strip(),
                    "headline": str(exp.get("headline", "")).strip(),
                    "bullets": bullets,
                }
            )
        return normalized

    if isinstance(custom_bullets, dict):
        normalized = []
        for label, bullets_raw in custom_bullets.items():
            if not isinstance(bullets_raw, list):
                continue
            bullets = [str(item).strip() for item in bullets_raw if str(item).strip()]
            normalized.append(
                {
                    "company": str(label).strip(),
                    "title": "",
                    "date_range": "",
                    "location": "",
                    "headline": "",
                    "bullets": bullets,
                }
            )
        return normalized

    return []


def get_template_capacity(template_path):
    doc = Document(template_path)
    template_type = _detect_template_type(doc)
    return len(_extract_slots(doc, template_type))


def _update_slots(doc, template_type, experiences):
    slots = _extract_slots(doc, template_type)
    used = 0
    removed = 0
    appended = 0

    for idx, slot in enumerate(slots):
        if idx >= len(experiences):
            _remove_slot(slot)
            removed += 1
            continue

        exp = experiences[idx]
        if template_type == "template_1":
            _rewrite_template1_header(slot, exp)
        else:
            _rewrite_template2_header(slot, exp)
        _update_slot_bullets(doc, slot, exp)
        used += 1

    if len(experiences) > len(slots):
        appended = _append_overflow_experiences(doc, template_type, experiences, len(slots))

    return used, removed, len(slots), appended


def _update_sequential_bullets(doc, bullets_list):
    if not bullets_list:
        return 0
    bullet_index = 0

    def _update_para(paragraph):
        nonlocal bullet_index
        if _is_bullet_paragraph(paragraph) and paragraph.text.strip():
            text = bullets_list[bullet_index % len(bullets_list)]
            _replace_paragraph_text(paragraph, text)
            bullet_index += 1

    for paragraph in doc.paragraphs:
        _update_para(paragraph)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _update_para(paragraph)

    return bullet_index


def _cleanup_trailing_layout(doc):
    logger.debug("Cleaning up trailing empty paragraphs...")
    while len(doc.paragraphs) > 0:
        last_para = doc.paragraphs[-1]
        if last_para.text.strip():
            break
        p_element = last_para._element
        if p_element.getparent() is not None:
            p_element.getparent().remove(p_element)

    if len(doc.sections) <= 1:
        return

    last_para = doc.paragraphs[-1] if doc.paragraphs else None
    if not last_para or last_para._p.pPr is None or last_para._p.pPr.sectPr is None:
        return

    logger.debug("Removing trailing section break...")
    first_sec = doc.sections[0]
    good_margins = {
        "bottom": first_sec.bottom_margin,
        "top": first_sec.top_margin,
        "left": first_sec.left_margin,
        "right": first_sec.right_margin,
    }

    last_para._p.pPr.remove(last_para._p.pPr.sectPr)
    new_last_sec = doc.sections[-1]
    new_last_sec.bottom_margin = good_margins["bottom"]
    new_last_sec.top_margin = good_margins["top"]
    new_last_sec.left_margin = good_margins["left"]
    new_last_sec.right_margin = good_margins["right"]


def update_cv_bullets(
    input_file,
    output_file,
    custom_summary=None,
    custom_bullets=None,
    custom_experiences=None,
    candidate_profile=None,
):
    """Read CV, update summary and experience sections, and save."""
    doc = Document(input_file)
    template_type = _detect_template_type(doc)
    summary_text = custom_summary if custom_summary else SUMMARY_TEXT
    candidate_profile = candidate_profile or {}

    _update_identity(doc, template_type, candidate_profile)
    _update_summary(doc, summary_text, candidate_profile)

    experiences = _normalize_experience_inputs(custom_experiences, custom_bullets)
    if experiences:
        used, removed, capacity, appended = _update_slots(doc, template_type, experiences)
        logger.info(
            f"Updated CV sections for {template_type}. Capacity: {capacity}, Used: {used}, Removed empty slots: {removed}, Appended overflow: {appended}"
        )
    else:
        bullets_list = custom_bullets if isinstance(custom_bullets, list) else dummy_bullets
        count = _update_sequential_bullets(doc, bullets_list)
        logger.info(f"Updated CV in legacy sequential mode ({count} bullets)")

    _cleanup_trailing_layout(doc)
    doc.save(output_file)
    logger.info(f"Updated CV saved to: {output_file}")
    return output_file


def convert_to_pdf(docx_file, pdf_file):
    """Convert DOCX to PDF."""
    pythoncom.CoInitialize()
    try:
        from docx2pdf import convert

        convert(docx_file, pdf_file)
        logger.info(f"PDF created: {pdf_file}")
        remove_blank_pages(pdf_file)
        return True
    except Exception as exc:
        logger.warning(f"docx2pdf conversion failed: {exc}")
        logger.info("Trying alternative method with comtypes...")
        try:
            doc_path = os.path.abspath(docx_file)
            pdf_path = os.path.abspath(pdf_file)
            word = comtypes.client.CreateObject("Word.Application")
            word.Visible = False
            try:
                doc = word.Documents.Open(doc_path)
                doc.SaveAs(pdf_path, FileFormat=17)
                doc.Close()
                logger.info(f"PDF created via comtypes: {pdf_file}")
                remove_blank_pages(pdf_path)
                return True
            finally:
                word.Quit()
        except Exception as exc2:
            logger.error(f"Alternative conversion also failed: {exc2}")
            return False
    finally:
        pythoncom.CoUninitialize()


def remove_blank_pages(pdf_path):
    """Remove completely blank pages from a PDF file."""
    temp_output = pdf_path.replace(".pdf", "_temp.pdf")
    try:
        if not os.path.exists(pdf_path):
            return

        has_changes = False
        original_page_count = 0
        new_page_count = 0

        with open(pdf_path, "rb") as handle:
            reader = PyPDF2.PdfReader(handle)
            writer = PyPDF2.PdfWriter()
            original_page_count = len(reader.pages)

            for idx, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                has_significant_text = len(text) > 20
                has_images = False
                try:
                    if hasattr(page, "images") and page.images:
                        has_images = True
                except Exception:
                    pass

                if has_significant_text or has_images:
                    writer.add_page(page)
                    new_page_count += 1
                else:
                    logger.debug(f"Removing blank/sparse page {idx + 1} from PDF (text len: {len(text)})")
                    has_changes = True

            if not has_changes:
                return

            with open(temp_output, "wb") as out_file:
                writer.write(out_file)

        shutil.move(temp_output, pdf_path)
        logger.info(f"PDF cleaned: {original_page_count} -> {new_page_count} pages")
    except Exception as exc:
        logger.error(f"Error removing blank pages: {exc}")
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except Exception:
                pass


if __name__ == "__main__":
    input_file = "templates/Madhav_Manohar Gopal_CV.docx"

    company_name = None
    if len(sys.argv) > 1:
        company_name = sys.argv[1].strip()

    if not company_name:
        company_name = input("Enter company name (or press Enter to skip): ").strip()

    if not company_name:
        company_name = "Updated"

    company_name_clean = company_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    company_name_clean = "".join(c for c in company_name_clean if c.isalnum() or c in ("_", "-"))

    base_dir = os.path.dirname(input_file) or "."
    outputs_dir = os.path.join(base_dir, "outputs")
    today = datetime.now()
    date_folder_name = f"{today.day}-{today.month}-{today.strftime('%y')}"
    date_output_dir = os.path.join(outputs_dir, date_folder_name)
    company_output_dir = os.path.join(date_output_dir, company_name_clean)
    os.makedirs(company_output_dir, exist_ok=True)

    output_docx = os.path.join(company_output_dir, f"CV_{company_name_clean}.docx")
    output_pdf = os.path.join(company_output_dir, f"CV_{company_name_clean}.pdf")

    print(f"\nGenerating CV for: {company_name}")
    print(f"Output files: {output_docx} and {output_pdf}\n")

    update_cv_bullets(input_file, output_docx)
    convert_to_pdf(output_docx, output_pdf)
