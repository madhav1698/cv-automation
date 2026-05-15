# ApplyCraft

**Local-first CV & Cover Letter Automation with Built-in Application Tracking**

ApplyCraft is a desktop application designed to streamline the job application process by automating document tailoring and tracking outcomes locally.

---

## Core Functionality

### 💼 Document Generation
* **Tailored CVs**: Injects specific experience bullets into pre-formatted Word templates.
* **Cover Letters**: Generates professional cover letters with consistent styling.
* **Format Preservation**: Maintains fonts, spacing, and margins from your master templates.
* **PDF Conversion**: Automated conversion from DOCX to PDF using native Windows integration.

### 📊 Application Tracking & Analytics
* **Local Database**: Tracking via SQLite with a JSON mirror for transparency.
* **Audit Dashboard**: Interactive velocity charts and conversion funnel.
* **Action Radar**: Identifies stale applications (>14 days) and stalled applications (>30 days).
* **Automatic Logging**: Every generated document is automatically registered in your history.

---

## Tech Stack
* **Python 3.10+**
* **CustomTkinter**: Modern desktop UI framework.
* **python-docx**: Structural Word document manipulation.
* **SQLite/SQLAlchemy**: Local data persistence.
* **Windows COM (comtypes)**: Native PDF rendering.

---

## Project Structure
```
cv-automation/
├── core/                 # Modular Application Logic
│   ├── cv_generator_gui.py   # Main UI Hub
│   ├── application_audit.py  # Analytics & Tracking logic
│   ├── stats_manager.py      # Database & File Discovery
│   ├── cv_service.py         # Business logic for generation
│   ├── audit_graph.py        # Chart rendering engine
│   └── ...
├── helpers/              # Cross-module utilities (Logger, etc.)
├── templates/            # DOCX Master Templates
├── outputs/              # Organized application results
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/madhav1698/cv-automation.git
cd cv-automation

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch App
```bash
python core/cv_generator_gui.py
```

---

## Usage Guide

1. **Templates**: Place your Word templates in the `templates/` folder. Use `{{SUMMARY}}` and `{{BULLETS}}` placeholders for dynamic injection.
2. **Tailoring**: Input the company details and select relevant experience bullets in the `Builder` tab.
3. **Generation**: Generating a document creates a date-stamped folder in `outputs/` and logs the entry in the `Audit` tab.
4. **Tracking**: Update application statuses (Unknown, In Process, Followed Up, Rejected) directly in the tracking table using hotkeys (`U`, `I`, `F`, `R`).

---

## Data Privacy
ApplyCraft is strictly **local-first**.
* **Zero Cloud**: No external APIs or accounts required.
* **Offline**: works without an internet connection.
* **Privacy**: Your job search data and CV content never leave your machine.

---

## License
MIT
