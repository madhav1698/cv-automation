# ✨ ApplyCraft - Premium CV & Cover Letter Automation

**ApplyCraft** is a sophisticated, high-performance automation suite designed to streamline the process of tailoring job applications. It transforms the tedious task of manual CV editing into a seamless, high-end experience with real-time previews and intelligent data parsing.

---

## 💎 Premium Features

### 🚀 High-End User Interface
- **Modern Aesthetics** - A sleek, custom-designed interface built with `customtkinter`.
- **Dual-Pane Logic** - Edit on the left, preview in real-time on the right.
- **Dark Mode Support** - Fully integrated theme switching for comfortable late-night application sessions.
- **Floating Action Bar** - Context-aware controls for lightning-fast document generation.

### 👁️ Live Preview Engine
- **Instant Updates** - See exactly how your CV or Cover Letter looks as you type.
- **Intelligent Formatting** - Automatically applies bullet points and professional spacing in the preview.
- **Document Simulation** - Realistic A4-style preview with page indicators and zoom controls (50% - 200%).

### 💼 Professional Tailoring
- **Multi-Template Support** - Choose between different CV layouts (Template 1 vs. Template 2) directly from the dashboard.
- **Smart Experience Manager** - Dedicated tabs for each past role with individual bullet control.
- **Automated Typography** - Standardizes all tailored sections to **Times New Roman, 10pt** for a consistent, professional look.
- **Country-Specific Customization** - Tailor your CV for specific markets (e.g., "UK", "Germany") with dedicated file naming.
- **Cover Letter Architect** - Dynamic generation with smart placeholders for [Company Name], Hiring Manager, and Location.
- **Intelligence Engine** - One-click "Smart Import" to auto-sort raw bullets into their respective job sections.
- **Date-Ready** - Automatically defaults to the current date while remaining fully editable.

### 📂 Advanced Output Management
- **Hierarchical Organization** - Outputs are saved in `outputs/[Date]/[Company]/` for perfect traceability.
- **Dual-Format Delivery** - Generates both professional `.docx` and print-ready `.pdf` automatically.
- **Smart Naming Convention**:
  - CV: `Madhav_Manohar_Gopal_CV_{Country_or_Company}.pdf`
  - Cover Letter: `Madhav_Manohar_Gopal_Cover_Letter_{Company}.pdf`

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Windows OS (for native PDF conversion via Microsoft Word)
- `pip install -r requirements.txt` (Run from root folder)

### Quick Launch
Simply double-click `launch_cv_generator.bat` or run from the root directory:
```bash
python core/cv_generator_gui.py
```

---

## 📖 The ApplyCraft Workflow

### 1. Template Selection
In the **CV Builder** panel, select your preferred layout (Template 1 or 2). ApplyCraft's engine is structure-aware and will adapt its injection logic to match the template's design (table-based vs. paragraph-based).

### 2. Intelligence Engine (Smart Import)
Paste all your raw experience bullets into the **⚡ Smart Import** panel. ApplyCraft will use its fuzzy-matching algorithm to distribute them into the correct job categories automatically.

### 3. Experience Refinement
Navigate to the **💼 Experience (CV)** tab to fine-tune your bullets for a specific role. The **Live Preview** on the right will update instantly at **10pt Times New Roman** to show your progress.

### 4. Cover Letter Composition
Switch to the **✉️ Cover Letter** tab. Fill in the hiring manager's name and location. ApplyCraft injects the company name and your custom body text into a professionally formatted layout.

### 5. One-Click Magic
Use the **🪄 Generate Both** button in the floating action bar to produce your tailored CV and Cover Letter simultaneously.

---


## 📂 Project Architecture

The project has been reorganized for clarity and maintainability:

```
Cv Automation/
├── core/                       # The Heart of the Application
│   ├── cv_generator_gui.py     # Main Application Entry Point
│   ├── update_cv.py            # CV Processing Logic
│   └── generate_cover_letter.py # Cover Letter Logic
├── templates/                  # Your Master Documents
│   ├── Madhav_Manohar Gopal_CV.docx   # Table-based Template
│   └── Madhav_Manohar_Gopal_CV_2.docx # Paragraph-based Template
├── tests/                      # Unit and integration tests
├── archive/                    # Legacy scripts and tools
├── outputs/                    # Generated CVs and Cover Letters
├── launch_cv_generator.bat     # One-click Launcher
├── requirements.txt            # Project Dependencies
└── README.md                   # This file
```

---

## 🔧 Technical Deep Dive

### Smart Bullet Parser
The parsing logic uses a multi-delimiter strategy to identify job titles. Whether you use `–`, `|`, `:`, or `/`, ApplyCraft recognizes the company name and maps your content to the correct section of your `DOCX` template.

### Document Injection Logic
Unlike simple search-and-replace, ApplyCraft performs **structural injection**:
- **Hybrid Detection**: Identifies job sections using both **Table Headers** (Template 1) and **Paragraph Patterns** (Template 2).
- **Paragraph Management**: Intelligently adds or removes bullet points to match your input, preserving the original formatting.
- **Typography Standardization**: Enforces **Times New Roman at size 10** for all tailored text blocks, ensuring professional uniformity regardless of the base template.
- **Style Preservation**: Ensures that new bullets inherit the exact indentation and list style of the template.

---

## 🛡️ License & Credits

Built with precision for streamlined professional success. 

**Happy Hunting! 🚀**
