import sys
import os

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import customtkinter as ctk
import threading
from datetime import datetime
import subprocess

# Backend Imports
from update_cv import update_cv_bullets, convert_to_pdf, SUMMARY_TEXT
from generate_cover_letter import generate_cover_letter
from stats_manager import StatsManager
from application_audit import ApplicationAuditPanel

# --- CONFIGURATION & CONSTANTS ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

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

class ApplyCraftApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ApplyCraft | Premium CV Automation")
        self.geometry("1400x900")
        
        # Design Tokens (Light, Dark) - Enhanced for better dark mode contrast
        self.colors = {
            "bg": ("#FBFCFE", "#0F1419"),
            "sidebar": ("#F8FAFC", "#1A1F2E"),
            "preview_bg": ("#E2E8F0", "#0B0F19"),
            "input_bg": ("#F1F5F9", "#1E2433"),  # Lighter in dark mode
            "accent": "#4F46E5",
            "accent_soft": ("#EEF2FF", "#3730A3"),  # Darker in dark mode for better contrast
            "text": ("#1E293B", "#E2E8F0"),  # Lighter text in dark mode
            "text_muted": ("#64748B", "#94A3B8"),
            "border": ("#E2E8F0", "#374151"),  # More visible borders in dark mode
            "success": "#10B981",
            "card": ("white", "#1E2433")  # Lighter cards in dark mode
        }

        self.configure(fg_color=self.colors["bg"])

        # State Variables
        self.templates = {
            "Template 1": os.path.join(current_dir, "..", "templates", "Madhav_Manohar Gopal_CV .docx"),
            "Template 2": os.path.join(current_dir, "..", "templates", "Madhav_Manohar_Gopal_CV_2.docx")
        }
        self.current_template_name = ctk.StringVar(value="Template 1")
        self.job_text_widgets = {}
        self.preview_zoom = 1.0
        self.stats_manager = StatsManager(os.path.join(current_dir, ".."))
        self.preview_zoom = 1.0
        self.stats_manager = StatsManager(os.path.join(current_dir, ".."))

        # Layout Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- SIDEBAR ----
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.colors["sidebar"], border_width=1, border_color=self.colors["border"])
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        # ---- SIDEBAR LOGO AREA ----
        logo_container = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        logo_container.grid(row=0, column=0, padx=20, pady=(40, 30), sticky="ew")
        
        self.logo_label = ctk.CTkLabel(logo_container, text="✨ ApplyCraft", 
                                       font=ctk.CTkFont(family="Inter", size=26, weight="bold"),
                                       text_color=self.colors["accent"])
        self.logo_label.pack(pady=(0, 2))
        
        self.tagline_label = ctk.CTkLabel(logo_container, text="Professional CV Automation",
                                         font=ctk.CTkFont(size=11, weight="bold"), 
                                         text_color=self.colors["text_muted"])
        self.tagline_label.pack()

        # Navigation Buttons with keyboard shortcuts
        self.import_btn = self.create_nav_button("⚡  Smart Import", 1, self.show_import_panel)
        self.cv_btn = self.create_nav_button("💼  Experience (CV)", 2, self.show_cv_panel)
        self.cl_btn = self.create_nav_button("✉️  Cover Letter", 3, self.show_cl_panel)
        self.audit_btn = self.create_nav_button("📊  Audit & Stats", 4, self.show_audit_panel)
        self.settings_btn = self.create_nav_button("⚙️  Settings", 6, self.show_settings_panel)
        
        # Keyboard shortcuts hint
        shortcuts_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        shortcuts_frame.grid(row=5, column=0, padx=20, pady=20, sticky="s")
        ctk.CTkLabel(shortcuts_frame, text="💡 Tip: Use Ctrl+G to generate",
                    font=ctk.CTkFont(size=10), text_color=self.colors["text_muted"]).pack()

        # Theme Toggle at the bottom of sidebar
        self.theme_switch = ctk.CTkSwitch(self.navigation_frame, text="Dark Mode", 
                                          command=self.toggle_theme,
                                          font=ctk.CTkFont(size=12),
                                          text_color=self.colors["text_muted"])
        self.theme_switch.grid(row=7, column=0, padx=20, pady=20, sticky="s")
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()

        # ---- MAIN CONTENT ----
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=3) # Editor side
        self.main_container.grid_columnconfigure(1, weight=2) # Preview side
        self.main_container.grid_rowconfigure(0, weight=1)

        # -- LEFT COLUMN: EDITOR --
        self.editor_column = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        self.editor_column.grid(row=0, column=0, sticky="nsew", padx=(30, 15), pady=20)
        self.editor_column.grid_columnconfigure(0, weight=1)
        self.editor_column.grid_rowconfigure(1, weight=1)

        # Header (In Editor Column)
        self.header_frame = ctk.CTkFrame(self.editor_column, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.breadcrumb = ctk.CTkLabel(self.header_frame, text="My Projects / Job Applications", 
                                      font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"])
        self.breadcrumb.pack(anchor="w")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Dashboard", 
                                        font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
                                        text_color=self.colors["text"])
        self.title_label.pack(anchor="w")

        # Status Badge (Top Right of Editor)
        self.status_frame = ctk.CTkFrame(self.header_frame, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color=self.colors["border"])
        self.status_frame.place(relx=1.0, rely=0.5, anchor="e")
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color=self.colors["success"], font=ctk.CTkFont(size=12))
        self.status_dot.pack(side="left", padx=(10, 4), pady=4)
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", font=ctk.CTkFont(size=11, weight="normal"), text_color=self.colors["text"])
        self.status_label.pack(side="left", padx=(0, 10), pady=4)

        # Preview Toggle Button
        self.toggle_preview_btn = ctk.CTkButton(self.header_frame, text="👁️  Hide Preview", width=130, height=35,
                                              fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                                              border_width=1, border_color=self.colors["border"],
                                              corner_radius=20,
                                              hover_color=self.colors["sidebar"],
                                              command=self.toggle_preview, font=ctk.CTkFont(size=12, weight="normal"))
        self.toggle_preview_btn.place(relx=1.0, rely=0.5, anchor="e", x=-140)

        # -- RIGHT COLUMN: PERSISTENT PREVIEW --
        self.preview_column = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color=self.colors["preview_bg"], border_width=1, border_color=self.colors["border"])
        self.preview_column.grid(row=0, column=1, sticky="nsew")
        
        preview_header_frame = ctk.CTkFrame(self.preview_column, fg_color="transparent")
        preview_header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        ctk.CTkLabel(preview_header_frame, text="LIVE PREVIEW", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_muted"]).pack(side="left")
        
        # Zoom Controls
        zoom_frame = ctk.CTkFrame(preview_header_frame, fg_color="transparent")
        zoom_frame.pack(side="right")
        
        self.zoom_out_btn = ctk.CTkButton(zoom_frame, text="−", width=30, height=25, fg_color="transparent", text_color=self.colors["text"], hover_color=self.colors["sidebar"], command=lambda: self.change_zoom(-0.1))
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"])
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_btn = ctk.CTkButton(zoom_frame, text="+", width=30, height=25, fg_color="transparent", text_color=self.colors["text"], hover_color=self.colors["sidebar"], command=lambda: self.change_zoom(0.1))
        self.zoom_in_btn.pack(side="left", padx=2)

        self.preview_scroll = ctk.CTkScrollableFrame(self.preview_column, fg_color="transparent")
        self.preview_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.preview_card = ctk.CTkFrame(self.preview_scroll, fg_color="white", corner_radius=0, border_width=1, border_color="#D1D5DB")
        self.preview_card.pack(pady=20, padx=20, fill="x")
        self.preview_card.configure(height=1100) # Full A4-ish height
        self.preview_card.pack_propagate(False)

        self.preview_text = ctk.CTkTextbox(self.preview_card, fg_color="transparent", text_color="#1E293B", font=ctk.CTkFont(family="Times New Roman", size=10), border_width=0)
        self.preview_text.pack(fill="both", expand=True, padx=40, pady=40)
        self.preview_text.configure(state="disabled")

        # Page Indicator (Bottom of preview)
        self.page_indicator = ctk.CTkLabel(self.preview_column, text="Page 1 / 1", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"])
        self.page_indicator.pack(pady=10)

        self.preview_mode = ctk.StringVar(value="CV") # Track which preview to show

        # ---- FLOATING ACTION BAR ----
        self.action_bar = ctk.CTkFrame(self, corner_radius=25, fg_color=self.colors["accent"], border_width=0)
        self.action_bar.place(relx=0.42, rely=0.92, anchor="center") # Centered over the editor side
        
        # Primary Action: Both (Solid) with shadow effect
        self.gen_both_btn = ctk.CTkButton(self.action_bar, text="🪄 Generate Both (Ctrl+G)", corner_radius=22,
                                     fg_color="white", text_color=self.colors["accent"],
                                     hover_color="#F8FAFC",
                                     font=ctk.CTkFont(size=14, weight="bold"), height=45, width=220,
                                     command=self.generate_both)
        self.gen_both_btn.pack(side="right", padx=(8, 18), pady=12)

        # Contextual Action: Generate CV (Secondary - Outlined)
        self.gen_cv_btn = ctk.CTkButton(self.action_bar, text="💼 Generate CV Only", corner_radius=20,
                                        fg_color="transparent", text_color="white",
                                        border_width=1, border_color="#9590EF",
                                        hover_color="#6158E8", height=40,
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        command=self.generate_cv)
        
        # Contextual Action: Generate CL (Secondary - Outlined)
        self.gen_cl_btn = ctk.CTkButton(self.action_bar, text="✉️ Generate CL Only", corner_radius=20,
                                        fg_color="transparent", text_color="white",
                                        border_width=1, border_color="#9590EF",
                                        hover_color="#6158E8", height=40,
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        command=self.generate_cl)

        # Tertiary Action: Open Folder (Ghost)
        self.open_folder_btn = ctk.CTkButton(self.action_bar, text="📁 Open Outputs", corner_radius=20,
                                      fg_color="transparent", text_color="#E2E8F0",
                                      hover_color="#6158E8", height=40,
                                      command=self.open_outputs)
        self.open_folder_btn.pack(side="left", padx=(15, 5), pady=10)

        # Panels
        self.cv_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.cl_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.import_panel = ctk.CTkFrame(self.editor_column, fg_color="transparent")
        self.audit_panel = ApplicationAuditPanel(self.editor_column, colors=self.colors)
        self.settings_panel = ctk.CTkFrame(self.editor_column, fg_color="transparent")
        
        self.setup_cv_panel()
        self.setup_cl_panel()
        self.setup_import_panel()
        # Removed self.setup_stats_panel()
        self.setup_settings_panel()
        
        self.show_cv_panel() # Default
        
        # Keyboard Shortcuts
        self.bind("<Control-g>", lambda e: self.generate_both())
        self.bind("<Control-G>", lambda e: self.generate_both())

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.navigation_frame, text=text, corner_radius=8, height=45,
                            fg_color="transparent", text_color=self.colors["text_muted"],
                            hover_color=("#E5E7EB", "#2D3748"), anchor="w",
                            font=ctk.CTkFont(size=14, weight="normal"),
                            command=command)
        btn.grid(row=row, column=0, padx=20, pady=8, sticky="ew")
        return btn

    def setup_cv_panel(self):
        # General Info Card
        card = self.create_card(self.cv_panel, "GENERAL INFO")
        
        # Template selector with better dark mode support
        ctk.CTkLabel(card, text="Active Template", font=ctk.CTkFont(size=13, weight="bold"), 
                    text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(10, 8))
        self.cv_template_selector = ctk.CTkSegmentedButton(card, values=["Template 1", "Template 2"],
                                                       variable=self.current_template_name,
                                                       command=self.update_template_path,
                                                       height=45,
                                                       fg_color=self.colors["input_bg"],
                                                       selected_color=self.colors["accent"],
                                                       selected_hover_color=self.colors["accent"],
                                                       unselected_color=self.colors["input_bg"],
                                                       text_color=self.colors["text"],
                                                       font=ctk.CTkFont(size=13, weight="bold"))
        self.cv_template_selector.pack(fill="x", padx=25, pady=(0, 20))


        # Row for Company and Country
        row_frame = ctk.CTkFrame(card, fg_color="transparent")
        row_frame.pack(fill="x", padx=25, pady=(5, 10))
        
        # Company Container
        company_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        company_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(company_container, text="Target Company *", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(0, 8))
        self.company_entry = ctk.CTkEntry(company_container, height=50, fg_color=self.colors["input_bg"], 
                                         text_color=self.colors["text"], border_width=2, 
                                         border_color=self.colors["border"], corner_radius=10, 
                                         placeholder_text="e.g. Google",
                                         font=ctk.CTkFont(size=13))
        self.company_entry.pack(fill="x")
        self.company_entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
        self.company_entry.bind("<FocusIn>", lambda e: self.company_entry.configure(border_color=self.colors["accent"]))
        self.company_entry.bind("<FocusOut>", lambda e: self.company_entry.configure(border_color=self.colors["border"]))

        # Country Container
        country_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        country_container.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(country_container, text="Country *", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(0, 8))
        self.cv_country_entry = ctk.CTkEntry(country_container, height=50, fg_color=self.colors["input_bg"], 
                                            text_color=self.colors["text"], border_width=2, 
                                            border_color=self.colors["border"], corner_radius=10, 
                                            placeholder_text="e.g. UK",
                                            font=ctk.CTkFont(size=13))
        self.cv_country_entry.pack(fill="x")
        self.cv_country_entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
        self.cv_country_entry.bind("<FocusIn>", lambda e: self.cv_country_entry.configure(border_color=self.colors["accent"]))
        self.cv_country_entry.bind("<FocusOut>", lambda e: self.cv_country_entry.configure(border_color=self.colors["border"]))

        self.summary_text = self.create_textbox(card, "Professional Summary", SUMMARY_TEXT)
        
        for job_title, default_bullets in JOB_POSITIONS.items():
            job_card = self.create_card(self.cv_panel, job_title)
            text_widget = self.create_textbox(job_card, "Role Highlights", "\n".join(default_bullets), height=150)
            self.job_text_widgets[job_title] = text_widget

    def setup_cl_panel(self):
        card = self.create_card(self.cl_panel, "RECIPIENT & CONTEXT")
        self.cl_hiring_manager = self.create_input(card, "Hiring Manager", "Hiring Manager")
        
        # Sub-frames for side-by-side fields
        row_frame = ctk.CTkFrame(card, fg_color="transparent")
        row_frame.pack(fill="x", padx=25, pady=5)
        
        city_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        city_container.pack(side="left", fill="x", expand=True)
        self.cl_city = self.create_input(city_container, "City", "Cork")
        
        country_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        country_container.pack(side="left", fill="x", expand=True, padx=(20, 0))
        self.cl_country = self.create_input(country_container, "Country", "Ireland")
        
        self.cl_date = self.create_input(card, "Date", datetime.now().strftime("%d/%m/%Y"))
        
        body_card = self.create_card(self.cl_panel, "COVER LETTER BODY")
        self.cl_body_text = self.create_textbox(body_card, "Body", DEFAULT_CL_BODY, height=400)

    def setup_import_panel(self):
        card = self.create_card(self.import_panel, "SMART BULLET PARSER")
        ctk.CTkLabel(card, text="Paste raw bullets with job titles. The system will auto-sort them.", 
                     font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"]).pack(anchor="w", padx=25)
        self.import_text = self.create_textbox(card, "", "", height=400)
        
        btn = ctk.CTkButton(card, text="⚡ Auto-Sort Into CV", corner_radius=10, 
                            fg_color=self.colors["accent"], height=45, command=self.auto_sort)
        btn.pack(fill="x", padx=25, pady=25)


    def setup_preview_panel(self):
        # Preview Selector
        selector_frame = ctk.CTkFrame(self.preview_panel, fg_color="transparent")
        selector_frame.pack(fill="x", pady=(0, 10))
        
        self.preview_mode = ctk.StringVar(value="CV")
        cv_toggle = ctk.CTkRadioButton(selector_frame, text="CV Preview", variable=self.preview_mode, value="CV", command=self.update_live_preview, font=ctk.CTkFont(size=13, weight="bold"))
        cv_toggle.pack(side="left", padx=20)
        
        cl_toggle = ctk.CTkRadioButton(selector_frame, text="Cover Letter Preview", variable=self.preview_mode, value="CL", command=self.update_live_preview, font=ctk.CTkFont(size=13, weight="bold"))
        cl_toggle.pack(side="left", padx=20)

        # Document Simulator
        self.preview_scroll = ctk.CTkScrollableFrame(self.preview_panel, fg_color=self.colors["sidebar"], corner_radius=15, border_width=1, border_color=self.colors["border"])
        self.preview_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.preview_card = ctk.CTkFrame(self.preview_scroll, fg_color="white", width=700, corner_radius=0, border_width=1, border_color="#D1D5DB")
        self.preview_card.pack(pady=40, padx=40, fill="y")
        self.preview_card.pack_propagate(False) # Keep fixed width feeling
        self.preview_card.configure(height=1000)

        self.preview_text = ctk.CTkTextbox(self.preview_card, fg_color="transparent", text_color="#1E293B", font=ctk.CTkFont(family="Times New Roman", size=14), border_width=0)
        self.preview_text.pack(fill="both", expand=True, padx=50, pady=50)
        self.preview_text.configure(state="disabled")

    def setup_settings_panel(self):
        card = self.create_card(self.settings_panel, "FILE CONFIGURATION")
        
        ctk.CTkLabel(card, text="Select Active Template", font=ctk.CTkFont(size=13, weight="normal"), text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(10, 0))
        self.template_selector = ctk.CTkSegmentedButton(card, values=["Template 1", "Template 2"],
                                                       variable=self.current_template_name,
                                                       command=self.update_template_path,
                                                       height=40,
                                                       fg_color=self.colors["input_bg"],
                                                       selected_color=self.colors["accent"],
                                                       selected_hover_color=self.colors["accent"])
        self.template_selector.pack(fill="x", padx=25, pady=(8, 15))
        
        self.template_path_entry = self.create_input(card, "CV Template Path", self.templates["Template 1"])

    def update_template_path(self, selected_name):
        path = self.templates.get(selected_name, "")
        self.template_path_entry.delete(0, "end")
        self.template_path_entry.insert(0, path)
        self.set_status(f"Switched to {selected_name}", "accent")

    # UI Helpers
    def create_card(self, parent, label):
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=12, 
                            border_width=1, border_color=self.colors["border"])
        frame.pack(fill="x", pady=12, padx=5)
        if label:
            # Card header with better spacing
            header = ctk.CTkFrame(frame, fg_color="transparent")
            header.pack(fill="x", padx=25, pady=(20, 5))
            ctk.CTkLabel(header, text=label, font=ctk.CTkFont(size=12, weight="bold"), 
                        text_color=self.colors["text_muted"]).pack(side="left")
        return frame

    def create_input(self, parent, label, default_val, placeholder=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13, weight="bold"), 
                    text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(15, 8))
        entry = ctk.CTkEntry(parent, height=50, fg_color=self.colors["input_bg"], 
                           text_color=self.colors["text"], border_width=2, 
                           border_color=self.colors["border"], corner_radius=10,
                           placeholder_text=placeholder if placeholder else default_val,
                           font=ctk.CTkFont(size=13))
        entry.pack(fill="x", padx=25, pady=(0, 10))
        entry.insert(0, default_val)
        entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
        entry.bind("<FocusIn>", lambda e: entry.configure(border_color=self.colors["accent"]))
        entry.bind("<FocusOut>", lambda e: entry.configure(border_color=self.colors["border"]))
        return entry

    def create_textbox(self, parent, label, default_val, height=120):
        if label:
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=13, weight="bold"), 
                        text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(15, 8))
        textbox = ctk.CTkTextbox(parent, height=height, fg_color=self.colors["input_bg"], 
                                text_color=self.colors["text"], border_width=2, 
                                border_color=self.colors["border"], corner_radius=10,
                                font=ctk.CTkFont(size=13), wrap="word")
        textbox.pack(fill="x", padx=25, pady=(0, 20))
        textbox.insert("1.0", default_val)
        textbox.bind("<KeyRelease>", lambda e: self.update_live_preview())
        textbox.bind("<FocusIn>", lambda e: textbox.configure(border_color=self.colors["accent"]))
        textbox.bind("<FocusOut>", lambda e: textbox.configure(border_color=self.colors["border"]))
        return textbox

    # Navigation Logic
    def show_panel(self, panel_to_show, btn_to_active, title):
        for p in [self.cv_panel, self.cl_panel, self.import_panel, self.settings_panel, self.audit_panel]:
            p.grid_forget()
        for b in [self.cv_btn, self.cl_btn, self.import_btn, self.settings_btn, self.audit_btn]:
            b.configure(fg_color="transparent", text_color=self.colors["text_muted"], border_width=0)
        
        # Default behavior: Show preview and action bar
        self.preview_column.grid(row=0, column=1, sticky="nsew")
        self.action_bar.place(relx=0.42, rely=0.92, anchor="center")
        self.main_container.grid_columnconfigure(1, weight=2)
        self.toggle_preview_btn.configure(state="normal")

        # Contextual Behavior for Audit: Maximize width, Hide preview/bar
        if panel_to_show == self.audit_panel:
            self.preview_column.grid_forget()
            self.action_bar.place_forget()
            self.main_container.grid_columnconfigure(1, weight=0)
            self.toggle_preview_btn.configure(state="disabled")
        
        # Hide contextual gen buttons first
        self.gen_cv_btn.pack_forget()
        self.gen_cl_btn.pack_forget()

        panel_to_show.grid(row=1, column=0, sticky="nsew")
        btn_to_active.configure(fg_color=self.colors["accent_soft"], text_color=self.colors["accent"], border_width=1, border_color=self.colors["accent"])
        self.title_label.configure(text=title)

        # Set preview mode based on panel
        if panel_to_show == self.cv_panel:
            self.preview_mode.set("CV")
        elif panel_to_show == self.cl_panel:
            self.preview_mode.set("CL")
        
        self.update_live_preview()

        # Show contextual gen button in the floating bar if relevant
        if panel_to_show == self.cv_panel:
            self.gen_cv_btn.pack(side="right", padx=10, pady=10, before=self.gen_both_btn)
        elif panel_to_show == self.cl_panel:
            self.gen_cl_btn.pack(side="right", padx=10, pady=10, before=self.gen_both_btn)

    def show_cv_panel(self): self.show_panel(self.cv_panel, self.cv_btn, "CV Builder")
    def show_cl_panel(self): self.show_panel(self.cl_panel, self.cl_btn, "Cover Letter Composition")
    def show_audit_panel(self): 
        self.show_panel(self.audit_panel, self.audit_btn, "Application Command Center")
        self.audit_panel.refresh_data()
    def show_import_panel(self): self.show_panel(self.import_panel, self.import_btn, "Intelligence Engine")
    def show_settings_panel(self): self.show_panel(self.settings_panel, self.settings_btn, "App Configuration")

    def toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def toggle_preview(self):
        if self.preview_column.grid_info():
            self.preview_column.grid_forget()
            self.main_container.grid_columnconfigure(0, weight=1)
            self.main_container.grid_columnconfigure(1, weight=0)
            self.toggle_preview_btn.configure(text="👁️  Show Preview")
            self.action_bar.place(relx=0.5, rely=0.92, anchor="center") # Centered for full width
        else:
            self.preview_column.grid(row=0, column=1, sticky="nsew")
            self.main_container.grid_columnconfigure(0, weight=3)
            self.main_container.grid_columnconfigure(1, weight=2)
            self.toggle_preview_btn.configure(text="👁️  Hide Preview")
            self.action_bar.place(relx=0.42, rely=0.92, anchor="center") # Offset for partial width

    def change_zoom(self, delta):
        self.preview_zoom = max(0.5, min(2.0, self.preview_zoom + delta))
        self.zoom_label.configure(text=f"{int(self.preview_zoom * 100)}%")
        new_size = int(10 * self.preview_zoom)
        self.preview_text.configure(font=ctk.CTkFont(family="Times New Roman", size=new_size))

    def update_live_preview(self):
        # Microfeedback status change
        self.set_status("Updating preview...", "accent")
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        
        company = self.company_entry.get().strip().title() or "[Company Name]"
        city = self.cl_city.get().strip().title()
        country = self.cl_country.get().strip().title()
        
        if self.preview_mode.get() == "CV":
            content = f"MADHAV MANOHAR GOPAL\n\nPROFESSIONAL SUMMARY\n{self.summary_text.get('0.0', 'end').strip()}\n\n"
            for job, widget in self.job_text_widgets.items():
                content += f"{job.upper()}\n"
                bullets = widget.get("0.0", "end").strip().split("\n")
                for b in bullets:
                    if b.strip(): content += f"• {b.strip()}\n"
                content += "\n"
        else:
            body = self.cl_body_text.get("0.0", "end").strip().replace("[Company Name]", company)
            content = (
                f"{self.cl_date.get()}\n\n"
                f"To: {self.cl_hiring_manager.get()}\n"
                f"{company}\n"
                f"{city}, {country}\n\n"
                f"Dear {self.cl_hiring_manager.get()},\n\n"
                f"{body}\n\n"
                "Sincerely,\n"
                "Madhav Manohar Gopal"
            )
            
        self.preview_text.insert("0.0", content)
        
        # Simple Page calculation (approximate by character count/lines)
        line_count = int(self.preview_text.index('end-1c').split('.')[0])
        pages = max(1, (line_count // 55) + 1)
        self.page_indicator.configure(text=f"Page 1 / {pages}" if line_count < 55 else f"Pages: ~{pages}")
        if line_count > 55:
            self.page_indicator.configure(text_color="orange") # Warning!
        else:
            self.page_indicator.configure(text_color=self.colors["text_muted"])

        self.preview_text.configure(state="disabled")
        self.after(500, lambda: self.set_status("Ready", "success")) # Revert status after short delay

    def auto_sort(self):
        raw_text = self.import_text.get("0.0", "end").strip()
        if not raw_text: return
        
        lines = raw_text.split("\n")
        current_job = None
        job_bullets = {}
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            matched_job = None
            for title in JOB_POSITIONS.keys():
                if title.split("–")[0].strip().upper() in line.upper():
                    matched_job = title
                    break
            
            if matched_job:
                current_job = matched_job
                job_bullets[current_job] = []
            elif current_job:
                job_bullets[current_job].append(line)
        
        for job, bullets in job_bullets.items():
            if job in self.job_text_widgets:
                self.job_text_widgets[job].delete("0.0", "end")
                self.job_text_widgets[job].insert("0.0", "\n".join(bullets))
        
        self.set_status("Bullets Sorted", "success")
        self.show_cv_panel()

    def set_status(self, text, type="success"):
        self.status_label.configure(text=text)
        self.status_dot.configure(text_color=self.colors[type])

    def open_outputs(self):
        outputs_dir = os.path.join(current_dir, "..", "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        os.startfile(outputs_dir)

    def generate_cv(self): self._start_gen("cv")
    def generate_cl(self): self._start_gen("cl")
    def generate_both(self): self._start_gen("both")

    def _start_gen(self, mode):
        company = self.company_entry.get().strip().title()
        cv_country = self.cv_country_entry.get().strip().title()
        if not company:
            # Prompt via dialog
            dialog = ctk.CTkInputDialog(text="Enter Target Company Name:", title="Company Required")
            response = dialog.get_input()
            if response:
                company = response.strip().title()
                self.company_entry.delete(0, "end")
                self.company_entry.insert(0, company)
            else:
                self.set_status("Company Name Required!", "text_muted")
                return
            
        # Disable all relevant buttons
        for btn in [self.gen_both_btn, self.gen_cv_btn, self.gen_cl_btn]:
            btn.configure(state="disabled")
            
        self.set_status("Generating...", "accent")
        
        # Gather Data
        summary = self.summary_text.get("0.0", "end").strip()
        bullets = {}
        for job, widget in self.job_text_widgets.items():
            text = widget.get("0.0", "end").strip()
            if text:
                bullets[job] = [b.strip() for b in text.split("\n") if b.strip()]
        
        cl_data = {
            "hiring_manager": self.cl_hiring_manager.get().strip(),
            "city": self.cl_city.get().strip().title(),
            "country": self.cl_country.get().strip().title(),
            "date": self.cl_date.get().strip(),
            "body": self.cl_body_text.get("0.0", "end").strip().replace("[Company Name]", company)
        }
        
        template = self.template_path_entry.get().strip()
        threading.Thread(target=self._run_generation, args=(mode, template, company, cv_country, summary, bullets, cl_data), daemon=True).start()

    def _run_generation(self, mode, template, company, cv_country, summary, bullets, cl_data):
        try:
            # Setup paths
            company_clean = "".join(c for c in company.replace(" ", "_") if c.isalnum() or c in ("_", "-"))
            today = datetime.now()
            date_folder = f"{today.day}-{today.month}-{today.strftime('%y')}"
            out_dir = os.path.join(current_dir, "..", "outputs", date_folder, company_clean)
            os.makedirs(out_dir, exist_ok=True)
            
            # Execute based on mode
            country_clean = "".join(c for c in cv_country.replace(" ", "_") if c.isalnum() or c in ("_", "-"))
            
            # Construct filename suffix: Company_Country or just Company or just Country
            file_suffix = company_clean
            if country_clean and country_clean.lower() != company_clean.lower():
                file_suffix = f"{company_clean}_{country_clean}"
            
            if mode in ["cv", "both"]:
                cv_docx = os.path.join(out_dir, f"Madhav_Manohar_Gopal_CV_{file_suffix}.docx")
                cv_pdf = os.path.join(out_dir, f"Madhav_Manohar_Gopal_CV_{file_suffix}.pdf")
                update_cv_bullets(template, cv_docx, custom_summary=summary, custom_bullets=bullets)
                convert_to_pdf(cv_docx, cv_pdf)
            
            if mode in ["cl", "both"]:
                cl_docx = os.path.join(out_dir, f"Madhav_Manohar_Gopal_Cover_Letter_{company_clean}.docx")
                cl_pdf = os.path.join(out_dir, f"Madhav_Manohar_Gopal_Cover_Letter_{company_clean}.pdf")
                generate_cover_letter(cl_docx, company, cl_data['city'], cl_data['country'], cl_data['date'], cl_data['body'], cl_data['hiring_manager'])
                convert_to_pdf(cl_docx, cl_pdf)
            
            # Add to stats immediately to bypass scan
            date_str = f"{today.day}-{today.month}-{today.strftime('%y')}"
            self.stats_manager.add_application(date_str, company, cv_country or cl_data['country'])
            
            self.after(0, lambda: self._complete(True))
        except Exception as e:
            print(f"Error: {e}")
            self.after(0, lambda: self._complete(False))

    def _complete(self, success):
        # Re-enable all relevant buttons
        for btn in [self.gen_both_btn, self.gen_cv_btn, self.gen_cl_btn]:
            btn.configure(state="normal")
            
        if success:
            self.status_label.configure(text="Documents Ready!")
            self.status_dot.configure(text_color=self.colors["success"])
        else:
            self.status_label.configure(text="Error Occurred")
            self.status_dot.configure(text_color=self.colors["text_muted"])

if __name__ == "__main__":
    app = ApplyCraftApp()
    app.mainloop()
