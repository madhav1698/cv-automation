# ApplyCraft Next

ApplyCraft Next is a local desktop product that helps you tailor CVs and cover letters faster, while keeping a full history of your job applications.

It is built for repeat applications: you define your experience once, paste raw notes from any source, auto-sort them into the right roles, generate polished documents, and track outcomes in one workflow.

## Supported CV Templates (Strict)

ApplyCraft Next is intentionally locked to these two CV templates for reliability:

1. `Madhav_Manohar Gopal_CV.docx` (Template 1)
2. `Madhav_Manohar_Gopal_CV_2.docx` (Template 2)

Custom/third-party CV templates are not supported in production mode.

## What The Product Does

1. Lets users define their own work experience profile:
- Company name
- Job title
- Aliases (alternate names)
- Bullet points

2. Auto-sorts pasted experience text into the correct role blocks.
3. Generates CV DOCX + PDF from Template 1 or Template 2 while preserving formatting.
4. Only customizes:
- Professional Summary text
- Bullet points under existing template roles
Everything else in the template stays unchanged.
5. Generates cover letters with reusable structure.
6. Logs every application and shows progress in the audit panel.

## Why It Is Useful

- You are not locked to hardcoded job titles.
- You get stable output because the app only targets two known-good template layouts.
- You stay local-first: no cloud account, no external API dependency.

## Core Algorithm (Layman Version)

### 1) Profile Loading
At startup, ApplyCraft loads your profile from:
`%USERPROFILE%/.applycraft_next/profile.json`

If the file does not exist yet, it creates one from default entries.

### 2) Text Intake
You paste raw experience text into Smart Import.

### 3) Matching Engine
For each profile entry, ApplyCraft builds match tokens from:
- Company
- Role title
- Aliases

It then normalizes text (removes punctuation/spacing differences) so matching is more tolerant.

### 4) Block Detection
As it scans line by line:
- If a line looks like a role/company heading, it switches the active target role.
- If a line looks like a date/metadata line, it skips it.
- Otherwise it treats it as a bullet and appends it to the current role.

### 5) Unmatched Handling
If a line appears before any role match, it is stored as unmatched and shown in the UI for manual review.

### 6) CV Rendering
When you generate:
- Summary is updated.
- Experience headers (company/title/dates/layout) stay exactly as defined in the template.
- Bullets are replaced per role, with add/remove support if counts differ from template.
- Template path is validated against the two supported templates before generation.

### 7) Output + Tracking
The app:
- Saves DOCX and PDF in `outputs/<date>/<company>/`
- Adds/updates application tracking records

## Main Components

- `core/cv_generator_gui.py`: main UI and workflow control
- `core/experience_profile.py`: profile persistence and auto-sort logic
- `core/cv_service.py`: orchestration for CV/CL generation
- `core/update_cv.py`: DOCX mutation logic (summary, headers, bullets, cleanup)
- `core/stats_manager.py`: application stats persistence

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python core/cv_generator_gui.py
```

## Typical User Flow

1. Open CV Builder.
2. Edit/add your experiences (company, title, aliases, bullets).
3. Paste raw text in Smart Import and run Auto-Sort.
4. Review unmatched lines (if any).
5. Generate CV/CL using Template 1 or Template 2.
6. Track status in Audit panel.

## Privacy

ApplyCraft Next is local-first:
- No mandatory cloud service
- Data stays on your machine
- Works offline

## License

MIT
