# ✨ ApplyCraft - Premium CV Automation & Strategic Command Center

**ApplyCraft** is an all-in-one job application assistant. It helps you quickly create tailored CVs and Cover Letters for specific roles while keeping track of every application you've sent in a smart, interactive dashboard.

---

## 💎 Premium Features

### 🚀 High-End User Interface
- **Unified Command Center** - A single-window hub with sidebar navigation for seamless transitions between building and auditing.
- **Adaptive Dark Mode** - A sleek, custom-designed interface that intelligently shifts between high-contrast "Slate Blue" and professional "Clean Frost" themes.
- **Scrollable Dashboard** - A modern, full-page scrolling engine (built with `CTkScrollableFrame`) that maximizes screen real estate for data analysis.

### 📊 Application Audit & Tactical Intelligence
- **Interactive Command Center** - A data-rich dashboard with a **Liquid-Motion Activity Graph**:
    - **Dynamic Timeline**: Visualize application volume over time with interactive nodes.
    - **Hover Intelligence**: Instant tooltips showing application density on specific dates.
    - **Deep-Link Filtering**: CLICK a graph node to instantly filter the entire dashboard for that specific date.
- **Action Radar & Intelligence**:
    - ⚡ **Recent / ⌛ Stale / 🛑 Stalled**: Real-time urgency categorization for follow-ups.
    - **Conversion Funnel**: Visual pipeline showing volume drop-off across your career stages.
    - **Autonomous Market Strength**: Sophisticated **City-to-Country Mapping** (e.g. Barcelona → Spain, Amsterdam → Netherlands) that automatically categorizes applications based on filename intelligence.
- **Micro-Animation Layer**: Premium, non-distracting motion including:
    - **Staggered Entrance**: Dashboard cards "slide-up" in sequence for guided eye-tracking.
    - **Number Pulsing**: Status counts count up dynamically during data refreshes.
    - **Liquid Dot Pulse**: Visual feedback during CV tailoring to indicate active background processing.

### 💾 Data Persistence & Portability
- **Hybrid Record Management**:
    - **Auto-Sync**: Background scans the `outputs/` hierarchy to detect new applications.
    - **Manual Injection**: A dedicated entry architect to log external or historic applications directly into the tracker.
    - **Non-Volatile Storage**: Manual records persist in the `application_stats.json` engine even if local output directories are removed.
- **Unified CSV Exporters**:
    - **Filtered Data Portability**: Export specific dashboard views or your entire application history to CSV with a single click.
    - **Reporting Schema**: Standardized headers (Company, Country, Status, Applied Date) ready for ingestion into Excel or CRM tools.

### 💼 Professional Tailoring Engine
- **Live Preview Architect** - Precise rendering of professional documents with **Sub-Pixel Zoom** and automatic **Page Estimation**.
- **Accurate Content Sync**: Instant, clean updates when switching between CV and Cover Letter views.
- **Floating Action Bar**: Contextual, hover-responsive controls for rapid document generation.

### ⌨️ Power-User Productivity
- **Sequential ID Tracking**: Automatically numbered entries for fast communication and referencing.
- **Hotkey Status Management**: `F`, `I`, `R`, `U` for instantaneous status updates on selected rows.
- **Visual Distinction**: Manual entries are automatically *italicized* in the data sheet for instant parity checks between tool-generated and external records.
- **Smart Cleanup**: Automatic empty-defaults for new applications with helpful placeholders.

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
