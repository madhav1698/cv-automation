import os
import sys
import customtkinter as ctk

# --- UI CONSTANTS & DESIGN TOKENS ---
DESIGN_TOKENS = {
    "bg": ("#F9FAFB", "#0B0F14"),       # Slightly cleaner white, deeper midnight
    "sidebar": ("#FFFFFF", "#111622"),  # Bright white sidebar, slate midnight
    "preview_bg": ("#F1F5F9", "#080B10"), # Light slate gray, deep noir
    "input_bg": ("#FFFFFF", "#1A202C"), # Pure surfaces
    "accent": "#6366F1",                # Muted Indigo (Premium restraint)
    "accent_soft": ("#EEF2FF", "#1E2235"), 
    "text": ("#111827", "#F3F4F6"),     # Deep ink to soft silver
    "text_muted": ("#6B7280", "#9CA3AF"),
    "border": ("#E5E7EB", "#1F2937"),   # Subtle separation
    "success": "#10B981",
    "card": ("#FFFFFF", "#161D29")      # Elevated card surfaces
}

# --- APPLICATION CONSTANTS ---
DEFAULT_CL_BODY = (
    "At scale, employee listening fails for one simple reason: feedback is collected faster than organisations "
    "can decide what to do with it. What drew me to this role at [Company Name] is that it treats listening as a system "
    "with ownership, governance, and consequences, not just a survey cycle.\n\n"
    "In my work, the most difficult part has never been analysis. It has been deciding which signals deserve attention, "
    "which patterns are noise, and how insights should be framed so leaders actually act. I have spent much of my time "
    "operating in that gap between data and decision, working with stakeholders to clarify intent upfront, "
    "stress-test findings, and narrow focus to actions that are both realistic and measurable.\n\n"
    "[Company Name]’s context makes this discipline especially important. When employee data is sensitive and trust is "
    "non-negotiable, insight must be precise, defensible, and handled with care. My background has made me deliberate about "
    "governance, data quality, and how findings are shared, particularly when results affect perception, prioritisation, or "
    "leadership accountability. Credibility, once lost, cannot be dashboarded back.\n\n"
    "I am particularly interested in the combination of employee listening and hands-on people analytics in this role. "
    "Building dashboards, defining meaningful KPIs, and supporting leaders through data-driven conversations are how "
    "listening becomes embedded rather than episodic. I care about consistency and usability because insights only "
    "matter if they are understood the same way across teams and over time.\n\n"
    "I am applying because this role sits where research judgment, analytics, and organisational responsibility intersect. "
    "I would value the opportunity to contribute to [Company Name]’s employee listening strategy and help ensure feedback "
    "leads to focused, durable change rather than well-intentioned reporting."
)

SUMMARY_TEXT = (
    "Data Analytics professional with experience across music rights, consulting, and research, "
    "specialising in turning complex operational data into decision-ready reporting and BI products. "
    "Skilled in Python, SQL, and modern BI tools, with a track record of automating workflows, "
    "improving data quality, and driving adoption among non-technical stakeholders."
)

JOB_POSITIONS = {
    "PEERMUSIC – Data Analytics Developer": [
        "Delivered production BI dashboards used by operational and finance teams to monitor music rights data, improving visibility into revenue drivers and data completeness.",
        "Took ownership of stakeholder requirements and translated business questions into decision-ready reporting, reducing turnaround time for insights.",
        "Automated metadata ingestion and validation using Python, cutting manual setup effort and reducing reporting errors.",
        "Built and maintained structured SQL-based data models to ensure consistent, reliable reporting across datasets.",
        "Produced clear documentation and walkthroughs that increased dashboard adoption across international teams."
    ],
    "REPHRAIN, University of Bristol – Research Data Scientist": [
        "Owned delivery of analytical outputs across multiple projects, ensuring datasets were accurate, compliant, and usable by stakeholders.",
        "Built a Python-based data quality tool that reduced review time by 80 percent, accelerating project delivery.",
        "Produced dashboards and analytical summaries that enabled stakeholders to interpret sensitive data with confidence.",
        "Scoped data requirements directly with researchers and ensured outputs aligned with governance and security constraints.",
        "Presented findings clearly to mixed technical and non-technical audiences, supporting informed project decisions."
    ],
    "IBA GROUP – Data Scientist": [
        "Delivered Power BI and QlikSense dashboards that enabled management to identify operational issues and data gaps earlier.",
        "Automated ETL and validation workflows using Python, SQL, and Excel, improving data accuracy by 75 percent.",
        "Worked directly with department heads to diagnose data issues and implement practical, business-focused analytical solutions.",
        "Managed large, multi-source datasets with a strong emphasis on precision, traceability, and reporting reliability.",
        "Improved efficiency of recurring reporting cycles by 50 percent, reducing manual effort under tight timelines."
    ],
    "BRISTOL DIGITAL FUTURES INSTITUTE – Data Analyst": [
        "Delivered analytical reports and dashboards that directly informed senior stakeholder decisions.",
        "Ensured data accuracy through structured cleaning, validation, and hypothesis testing.",
        "Presented insights at an international conference, adapting technical content for non-technical audiences.",
        "Met fixed research and delivery deadlines within a multi-stakeholder project environment."
    ]
}

# --- HELPERS ---
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)
