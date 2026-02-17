# ✨ ApplyCraft - Premium CV Automation & Strategic Command Center

**ApplyCraft** is a sophisticated, high-performance automation suite designed to transform the job application process into a high-end, data-driven experience. It combines a professional document generation engine with a powerful analytical dashboard to help you craft, track, and optimize your career trajectory.

---

## 💎 Premium Features

### 🚀 High-End User Interface
- **Unified Command Center** - A single-window hub with sidebar navigation for seamless transitions between building and auditing.
- **Adaptive Dark Mode** - A sleek, custom-designed interface that intelligently shifts between high-contrast "Slate Blue" and professional "Clean Frost" themes.
- **Scrollable Dashboard** - A modern, full-page scrolling engine (built with `CTkScrollableFrame`) that maximizes screen real estate for data analysis.

### 📊 Application Audit & Tactical Intelligence (NEW)
- **Action Radar** - A real-time urgency categorization system:
    - ⚡ **Recent**: Highlights applications from the last 48 hours.
    - ⌛ **Stale**: Identifies applications older than 14 days needing follow-up.
    - ⚠️ **Stalled**: Surfaces inactive applications older than 30 days.
- **Strategy Visualizations**:
    - **Conversion Funnel**: A visual pipeline showing the volume drop-off from initial application to interview and outcome.
    - **Market Strength**: Analytics identifying regional clusters where your applications are most concentrated.
- **Pro Data Table**: A high-performance, theme-aware "spreadsheet" view with zebra striping and 14pt high-readability typography.

### 💼 Professional Tailoring Engine
- **Live Preview Architect** - Real-time rendering of CVs and Cover Letters in **10pt Times New Roman** professional standard.
- **Smart Experience Manager** - Multi-job management with dedicated bullet controls and "Smart Import" fuzzy-matching logic.
- **Multi-Template Logic** - Structure-aware injection into both table-based and paragraph-based `.docx` layouts.
- **Floating Action Bar** - Contextual controls for lightning-fast document generation (CV, CL, or Both).

### ⌨️ Power-User Productivity
- **Keyboard Shortcuts**:
    - `Ctrl + G`: Instant document generation.
    - `F`, `I`, `R`, `U`: Rapidly update application status (Followed Up, In Process, Rejected, Unknown).
- **Pro Right-Click Menu**: Instant access to status updates and deep-links to specific local application folders in Windows Explorer.

---

## 📂 Project Architecture

The project is engineered for clarity, speed, and reliability:

```
Cv Automation/
├── core/                       # The Heart of the Application
│   ├── cv_generator_gui.py     # Unified Application Hub
│   ├── application_audit.py    # Analytics & Tracker Panel
│   ├── stats_manager.py        # Central Data Engine & Metadata Manager
│   ├── update_cv.py            # CV Structural Injection Logic
│   └── generate_cover_letter.py # Cover Letter Architect
├── templates/                  # Master Professional Layouts
├── outputs/                    # Hierarchical Organized Results (outputs/[Date]/[Company]/)
├── launch_cv_generator.bat     # One-click Suite Launcher
├── requirements.txt            # Project System Dependencies
└── README.md                   # This Strategic Guide
```

---

## 🛠️ Installation & Quick Launch

### Prerequisites
- Python 3.8+
- Windows OS (for native `comtypes` PDF conversion)
- `pip install -r requirements.txt`

### Launch commands
Simply double-click `launch_cv_generator.bat` or run:
```bash
python core/cv_generator_gui.py
```

---

## 📖 The ApplyCraft Workflow

### 1. Intelligence Engine (Smart Import)
Paste raw experience bullets into the **⚡ Smart Import** panel. ApplyCraft uses its fuzzy-matching algorithm to map your history to the correct job categories automatically.

### 2. Tailoring & Execution
Refine your bullets and Cover Letter body in the **Builder Panels**. Use the **Live Preview** to ensure your 10pt Times New Roman formatting is perfect, then hit **🪄 Generate Both**.

### 3. Tactical Command (Audit)
Navigate to the **📊 Audit & Stats** tab to view your application log. Use the **Action Radar** cards to identify which companies require a follow-up today.

### 4. Rapid Management
Select a row and use the **Hotkey Entry** (`F`, `R`, etc.) or **Right-Click** to update your progress. Use the right-click menu to jump directly into the application's local folder to retrieve your documents for submission.

---

## 🛡️ License & Credits

Built with precision to turn job hunting into a mathematical victory.

**Happy Hunting! 🚀**
