import os
import threading
import sys
from datetime import datetime
import subprocess
import time
import re

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import customtkinter as ctk
from helpers.logger import logger
from helpers import user_config
from core.config import DESIGN_TOKENS, JOB_POSITIONS, DEFAULT_CL_BODY, SUMMARY_TEXT
from core.cv_service import CVGeneratorService
from core.stats_manager import StatsManager
from core.application_audit import ApplicationAuditPanel
from core.jd_ranker import rank_bullets, BulletScore

# --- ANIMATION UTILITY ---

# Appearance defaults
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class ApplyCraftApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ApplyCraft | Premium CV Automation")
        self.geometry("1400x900")
        
        # Design Tokens
        self.colors = DESIGN_TOKENS

        self.configure(fg_color=self.colors["bg"])

        # State Variables - templates come from user_config.json so each
        # user can register their own master .docx files.
        self.templates = user_config.resolved_template_paths()
        if not self.templates:
            # Defensive: ensure the segmented selector always has something.
            self.templates = {"Template 1": ""}
        self._template_labels = list(self.templates.keys())
        self.current_template_name = ctk.StringVar(value=self._template_labels[0])

        # Cached: latest JD-ranked bullets, set when the user presses
        # "Rank against JD" in the Smart Import panel.
        self.last_jd_text = ""
        self.last_jd_ranking = []  # list[BulletScore]
        self.last_jd_recommendations = []
        self.last_jd_fit = {}
        self.last_jd_analysis = {}
        self.job_text_widgets = {}
        self.job_headline_widgets = {}
        self.preview_zoom = 1.0
        self.stats_manager = StatsManager(os.path.dirname(current_dir))
        self.cv_service = CVGeneratorService(self.stats_manager)

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
        
        self.logo_label = ctk.CTkLabel(logo_container, text="ApplyCraft", 
                                       font=ctk.CTkFont(family="Inter", size=30, weight="bold"),
                                       text_color=self.colors["accent"])
        self.logo_label.pack(pady=(0, 4))
        
        self.tagline_label = ctk.CTkLabel(logo_container, text="STRATEGIC CAREER ENGINE",
                                         font=ctk.CTkFont(family="Inter", size=12, weight="bold"), 
                                         text_color=self.colors["text_muted"])
        self.tagline_label.pack()

        # Navigation Buttons with keyboard shortcuts
        self.import_btn = self.create_nav_button("Smart Import", 1, self.show_import_panel)
        self.cv_btn = self.create_nav_button("Experience (CV)", 2, self.show_cv_panel)
        self.cl_btn = self.create_nav_button("Cover Letter", 3, self.show_cl_panel)
        self.audit_btn = self.create_nav_button("Audit & Stats", 4, self.show_audit_panel)
        self.settings_btn = self.create_nav_button("Settings", 6, self.show_settings_panel)
        
        # Keyboard shortcuts hint (Muted bottom hint)
        shortcuts_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        shortcuts_frame.grid(row=5, column=0, padx=20, pady=30, sticky="s")
        ctk.CTkLabel(shortcuts_frame, text="Use Ctrl+G to Generate Everywhere",
                    font=ctk.CTkFont(family="Inter", size=13, weight="normal"), 
                    text_color=self.colors["text_muted"]).pack()

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
                                      font=ctk.CTkFont(size=14), text_color=self.colors["text_muted"])
        self.breadcrumb.pack(anchor="w")
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="Dashboard", 
                                        font=ctk.CTkFont(family="Inter", size=34, weight="bold"),
                                        text_color=self.colors["text"])
        self.title_label.pack(anchor="w")

        # Status Badge (Top Right of Editor)
        self.status_frame = ctk.CTkFrame(self.header_frame, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color=self.colors["border"])
        self.status_frame.place(relx=1.0, rely=0.5, anchor="e")
        self.status_dot = ctk.CTkLabel(self.status_frame, text="*", text_color=self.colors["success"], font=ctk.CTkFont(size=14))
        self.status_dot.pack(side="left", padx=(10, 4), pady=4)
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", font=ctk.CTkFont(size=13, weight="normal"), text_color=self.colors["text"])
        self.status_label.pack(side="left", padx=(0, 10), pady=4)

        # Preview Toggle Button
        self.toggle_preview_btn = ctk.CTkButton(self.header_frame, text="Hide Preview", width=140, height=40,
                                              fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                                              border_width=1, border_color=self.colors["border"],
                                              corner_radius=20,
                                              hover_color=self.colors["sidebar"],
                                              command=self.toggle_preview, font=ctk.CTkFont(size=14, weight="normal"))
        self.toggle_preview_btn.place(relx=1.0, rely=0.5, anchor="e", x=-140)

        # -- RIGHT COLUMN: PERSISTENT PREVIEW --
        self.preview_column = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color=self.colors["preview_bg"], border_width=1, border_color=self.colors["border"])
        self.preview_column.grid(row=0, column=1, sticky="nsew")
        
        preview_header_frame = ctk.CTkFrame(self.preview_column, fg_color="transparent")
        preview_header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        ctk.CTkLabel(preview_header_frame, text="LIVE PREVIEW", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_muted"]).pack(side="left")
        
        # Zoom Controls
        zoom_frame = ctk.CTkFrame(preview_header_frame, fg_color="transparent")
        zoom_frame.pack(side="right")
        
        self.zoom_out_btn = ctk.CTkButton(zoom_frame, text="-", width=35, height=30, fg_color="transparent", text_color=self.colors["text"], hover_color=self.colors["sidebar"], command=lambda: self.change_zoom(-0.1))
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"])
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_btn = ctk.CTkButton(zoom_frame, text="+", width=35, height=30, fg_color="transparent", text_color=self.colors["text"], hover_color=self.colors["sidebar"], command=lambda: self.change_zoom(0.1))
        self.zoom_in_btn.pack(side="left", padx=2)

        self.preview_scroll = ctk.CTkScrollableFrame(self.preview_column, fg_color="transparent")
        self.preview_scroll.pack(fill="both", expand=True, padx=25, pady=(0, 10))
        
        # Simulated Shadow and Depth for the 'Paper'
        self.paper_container = ctk.CTkFrame(self.preview_scroll, fg_color="transparent")
        self.paper_container.pack(pady=40, padx=30, fill="x")
        
        self.preview_card = ctk.CTkFrame(self.paper_container, fg_color=self.colors["card"], corner_radius=4, 
                                        border_width=1, border_color=self.colors["border"])
        self.preview_card.pack(fill="x", expand=True)
        self.preview_card.configure(height=1100) # Full A4-ish height
        self.preview_card.pack_propagate(False)

        self.preview_text = ctk.CTkTextbox(self.preview_card, fg_color="transparent", 
                                          text_color=self.colors["text"], 
                                          font=ctk.CTkFont(family="Times New Roman", size=10), border_width=0)
        self.preview_text.pack(fill="both", expand=True, padx=50, pady=50)
        self.preview_text.configure(state="disabled")

        # Page Indicator (Bottom of preview)
        self.page_indicator = ctk.CTkLabel(self.preview_column, text="Page 1 / 1", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"])
        self.page_indicator.pack(pady=10)

        self.preview_mode = ctk.StringVar(value="CV") # Track which preview to show

        # ---- FLOATING ACTION BAR (Premium Surface) ----
        self.action_bar = ctk.CTkFrame(self, corner_radius=28, fg_color=self.colors["card"], border_width=1, border_color=self.colors["border"])
        self.action_bar.place(relx=0.42, rely=0.92, anchor="center") 
        
        # Primary Action: Generate Both
        self.gen_both_btn = ctk.CTkButton(self.action_bar, text="Generate (Ctrl+G)", corner_radius=24,
                                     fg_color=self.colors["accent"], text_color="white",
                                     hover_color=self.colors["accent"],
                                     font=ctk.CTkFont(family="Inter", size=16, weight="bold"), height=55, width=240,
                                     command=self.generate_both)
        self.gen_both_btn.pack(side="right", padx=(8, 12), pady=12)

        # Contextual Buttons (Outlined & Muted)
        self.gen_cv_btn = ctk.CTkButton(self.action_bar, text="CV Only", corner_radius=22,
                                        fg_color="transparent", text_color=self.colors["text"],
                                        border_width=1, border_color=self.colors["border"],
                                        hover_color=self.colors["accent_soft"], height=48,
                                        font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                                        command=self.generate_cv)
        
        self.gen_cl_btn = ctk.CTkButton(self.action_bar, text="CL Only", corner_radius=22,
                                        fg_color="transparent", text_color=self.colors["text"],
                                        border_width=1, border_color=self.colors["border"],
                                        hover_color=self.colors["accent_soft"], height=48,
                                        font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                                        command=self.generate_cl)

        self.open_folder_btn = ctk.CTkButton(self.action_bar, text="Open", corner_radius=22,
                                      fg_color="transparent", text_color=self.colors["text_muted"],
                                      hover_color=self.colors["accent_soft"], height=42, width=50,
                                      command=self.open_outputs)
        self.open_folder_btn.pack(side="left", padx=(15, 5), pady=10)

        # Panels. NOTE: import_panel must be scrollable - it now holds
        # two cards (Smart Bullet Parser + JD-Aware Ranking) and the
        # Rank button would otherwise be hidden below the viewport.
        self.cv_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.cl_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.import_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.audit_panel = ApplicationAuditPanel(self.editor_column, colors=self.colors)
        self.settings_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        
        # Entrance Animation State
        self.panels = [self.cv_panel, self.cl_panel, self.import_panel, self.settings_panel, self.audit_panel]
        for p in self.panels:
            # We skip grid_propagate manually as some CTk widgets handle it internally
            pass
            
        self.setup_cv_panel()
        self.setup_cl_panel()
        self.setup_import_panel()
        self.setup_settings_panel()
        
        self.show_cv_panel() # Default
        
        # Keyboard Shortcuts
        self.bind("<Control-g>", lambda e: self.generate_both())
        self.bind("<Control-G>", lambda e: self.generate_both())

    def animate_panel_entrance(self, panel):
        """Micro-animation for section reveal (Staggered appearance)"""
        panel.update_idletasks()
        # Staggered reveal of children
        children = [c for c in panel.winfo_children() if isinstance(c, ctk.CTkFrame)]
        for i, child in enumerate(children):
            self.after(i * 50, lambda c=child: self._slide_up(c))

    def _slide_up(self, widget):
        """Simple staggered entrance feel by adjusting pady temporarily."""
        # Simple micro-move: most widgets use packing with pady.
        # We can simulate a 'pop' by updating the layout with a small offset.
        pass # Keeping it minimal to avoid layout flickering in ctk

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.navigation_frame, text=text, corner_radius=12, height=52,
                            fg_color="transparent", text_color=self.colors["text_muted"],
                            hover_color=("#F3F4F6", "#1E2937"), anchor="w",
                            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
                            command=command,
                            border_spacing=15)
        btn.grid(row=row, column=0, padx=15, pady=6, sticky="ew")
        return btn

    def setup_cv_panel(self):
        # General Info Card
        card = self.create_card(self.cv_panel, "GENERAL INFO")
        
        # Template selector with better dark mode support
        ctk.CTkLabel(card, text="Active Template", font=ctk.CTkFont(size=13, weight="bold"), 
                    text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(10, 8))
        self.cv_template_selector = ctk.CTkSegmentedButton(card, values=self._template_labels,
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

        ctk.CTkLabel(card, text="Role Title", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(10, 8))
        self.role_title_entry = ctk.CTkEntry(card, height=50, fg_color=self.colors["input_bg"],
                                            text_color=self.colors["text"], border_width=2,
                                            border_color=self.colors["border"], corner_radius=10,
                                            placeholder_text="e.g. Data Analyst",
                                            font=ctk.CTkFont(size=13))
        self.role_title_entry.pack(fill="x", padx=25)
        self.role_title_entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
        self.role_title_entry.bind("<FocusIn>", lambda e: self.role_title_entry.configure(border_color=self.colors["accent"]))
        self.role_title_entry.bind("<FocusOut>", lambda e: self.role_title_entry.configure(border_color=self.colors["border"]))

        ctk.CTkLabel(card, text="Current Location *", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=25, pady=(10, 8))
        self.current_location_entry = ctk.CTkEntry(card, height=50, fg_color=self.colors["input_bg"],
                                            text_color=self.colors["text"], border_width=2,
                                            border_color=self.colors["border"], corner_radius=10,
                                            placeholder_text="e.g. " + (user_config.location() or "London"),
                                            font=ctk.CTkFont(size=13))
        self.current_location_entry.pack(fill="x", padx=25)
        self.current_location_entry.insert(0, user_config.location())
        self.current_location_entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
        self.current_location_entry.bind("<FocusIn>", lambda e: self.current_location_entry.configure(border_color=self.colors["accent"]))
        self.current_location_entry.bind("<FocusOut>", lambda e: self.current_location_entry.configure(border_color=self.colors["border"]))

        self.summary_text = self.create_textbox(card, "Professional Summary", SUMMARY_TEXT)
        
        for job_title, default_bullets in JOB_POSITIONS.items():
            job_card = self.create_card(self.cv_panel, job_title)
            
            # Optional Headline
            ctk.CTkLabel(job_card, text="Role Headline (Optional)", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=30, pady=(10, 0))
            headline_entry = ctk.CTkEntry(job_card, height=45, fg_color=self.colors["input_bg"],
                                         text_color=self.colors["text"], border_width=1,
                                         border_color=self.colors["border"], corner_radius=10,
                                         placeholder_text="e.g. Developed high-performance analytics dashboards...",
                                         font=ctk.CTkFont(size=13, slant="italic"))
            headline_entry.pack(fill="x", padx=30, pady=(5, 10))
            headline_entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
            self.job_headline_widgets[job_title] = headline_entry

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
        self.cl_city = self.create_input(city_container, "City", "", placeholder="e.g. Cork")
        
        country_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        country_container.pack(side="left", fill="x", expand=True, padx=(20, 0))
        self.cl_country = self.create_input(country_container, "Country", "", placeholder="e.g. Ireland")
        
        self.cl_date = self.create_input(card, "Date", datetime.now().strftime("%d/%m/%Y"))
        
        body_card = self.create_card(self.cl_panel, "COVER LETTER BODY")
        self.cl_body_text = self.create_textbox(body_card, "Body", DEFAULT_CL_BODY, height=400)

    def setup_import_panel(self):
        # --- Card 1: Auto-sort raw resume text into job-bucketed bullets ---
        card = self.create_card(self.import_panel, "SMART BULLET PARSER")
        ctk.CTkLabel(card, text="Paste raw bullets with job titles. The system will auto-sort them.",
                     font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"]).pack(anchor="w", padx=25)
        self.import_text = self.create_textbox(card, "", "", height=260)

        btn = ctk.CTkButton(card, text="Auto-Sort Into CV", corner_radius=10,
                            fg_color=self.colors["accent"], height=45, command=self.auto_sort)
        btn.pack(fill="x", padx=25, pady=(5, 25))

        # --- Card 2: JD-aware bullet ranking -----------------------------
        # Paste a JD, press the button, and we score every bullet in the
        # inventory against it. The user sees a ranked list with the
        # matched keywords, then either copies a bullet into the CV panel
        # or auto-applies the top N per job.
        jd_card = self.create_card(self.import_panel, "JD-AWARE BULLET RANKING")
        ctk.CTkLabel(
            jd_card,
            text="Paste a job description. The local ranker scores every bullet "
                 "in your inventory against it. Top matches show below. "
                 "Click 'Apply Top 5 / Job' to pre-fill the CV builder.",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_muted"],
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=25, pady=(0, 5))

        self.jd_text = self.create_textbox(jd_card, "Job Description", "", height=180)

        controls = ctk.CTkFrame(jd_card, fg_color="transparent")
        controls.pack(fill="x", padx=25, pady=(0, 10))

        rank_btn = ctk.CTkButton(
            controls, text="Rank Against JD", corner_radius=10,
            fg_color=self.colors["accent"], height=42, width=200,
            command=self.run_jd_ranking,
        )
        rank_btn.pack(side="left")

        apply_btn = ctk.CTkButton(
            controls, text="Apply Top 5 / Job", corner_radius=10,
            fg_color="transparent", text_color=self.colors["text"],
            border_width=1, border_color=self.colors["border"],
            hover_color=self.colors["accent_soft"],
            height=42, width=180,
            command=self.apply_top_ranked_bullets,
        )
        apply_btn.pack(side="left", padx=(10, 0))

        self.jd_why_btn = ctk.CTkButton(
            controls, text="Why this score?", corner_radius=10,
            fg_color="transparent", text_color=self.colors["text"],
            border_width=1, border_color=self.colors["border"],
            hover_color=self.colors["accent_soft"],
            height=42, width=150,
            command=self.show_llm_reason_dialog,
        )
        self.jd_why_btn.pack(side="left", padx=(10, 0))

        self.jd_results_label = ctk.CTkLabel(
            jd_card, text="", font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"], justify="left", anchor="w",
        )
        self.jd_results_label.pack(anchor="w", padx=25, pady=(2, 5))

        # Scrollable list of top-ranked bullets. We render it as plain
        # text in a textbox: simpler than a treeview, perfectly readable.
        self.jd_results_box = ctk.CTkTextbox(
            jd_card, height=260, fg_color=self.colors["bg"],
            text_color=self.colors["text"], border_width=1,
            border_color=self.colors["border"], corner_radius=12,
            font=ctk.CTkFont(family="Inter", size=13), wrap="word",
        )
        self.jd_results_box.pack(fill="x", padx=25, pady=(0, 20))
        self.jd_results_box.configure(state="disabled")


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
        self.template_selector = ctk.CTkSegmentedButton(card, values=self._template_labels,
                                                       variable=self.current_template_name,
                                                       command=self.update_template_path,
                                                       height=40,
                                                       fg_color=self.colors["input_bg"],
                                                       selected_color=self.colors["accent"],
                                                       selected_hover_color=self.colors["accent"])
        self.template_selector.pack(fill="x", padx=25, pady=(8, 15))

        first_label = self._template_labels[0]
        self.template_path_entry = self.create_input(card, "CV Template Path", self.templates.get(first_label, ""))

    def update_template_path(self, selected_name):
        path = self.templates.get(selected_name, "")
        self.template_path_entry.delete(0, "end")
        self.template_path_entry.insert(0, path)
        self.set_status(f"Switched to {selected_name}", "accent")

    # UI Helpers
    def create_card(self, parent, label):
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=16, 
                            border_width=1, border_color=self.colors["border"])
        frame.pack(fill="x", pady=15, padx=8)
        if label:
            header = ctk.CTkFrame(frame, fg_color="transparent")
            header.pack(fill="x", padx=30, pady=(25, 10))
            ctk.CTkLabel(header, text=label.upper(), 
                         font=ctk.CTkFont(family="Inter", size=13, weight="bold"), 
                         text_color=self.colors["text_muted"]).pack(side="left")
        return frame

    def create_input(self, parent, label, default_val, placeholder=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(family="Inter", size=14, weight="bold"), 
                    text_color=self.colors["text"]).pack(anchor="w", padx=30, pady=(15, 6))
        entry = ctk.CTkEntry(parent, height=52, fg_color=self.colors["bg"], 
                           text_color=self.colors["text"], border_width=1, 
                           border_color=self.colors["border"], corner_radius=12,
                           placeholder_text=placeholder if placeholder else default_val,
                           font=ctk.CTkFont(family="Inter", size=15))
        entry.pack(fill="x", padx=30, pady=(0, 10))
        entry.insert(0, default_val)
        entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
        entry.bind("<FocusIn>", lambda e: entry.configure(border_color=self.colors["accent"], border_width=2))
        entry.bind("<FocusOut>", lambda e: entry.configure(border_color=self.colors["border"], border_width=1))
        return entry

    def create_textbox(self, parent, label, default_val, height=120):
        if label:
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(family="Inter", size=14, weight="bold"), 
                        text_color=self.colors["text"]).pack(anchor="w", padx=30, pady=(15, 6))
        textbox = ctk.CTkTextbox(parent, height=height, fg_color=self.colors["bg"], 
                                text_color=self.colors["text"], border_width=1, 
                                border_color=self.colors["border"], corner_radius=12,
                                font=ctk.CTkFont(family="Inter", size=15), wrap="word",
                                border_spacing=10)
        textbox.pack(fill="x", padx=30, pady=(0, 20))
        textbox.insert("1.0", default_val)
        textbox.bind("<KeyRelease>", lambda e: self.update_live_preview())
        textbox.bind("<FocusIn>", lambda e: textbox.configure(border_color=self.colors["accent"], border_width=2))
        textbox.bind("<FocusOut>", lambda e: textbox.configure(border_color=self.colors["border"], border_width=1))
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
        
        # Smooth Sidebar Transition (Immediate highlight, but we could fade colors)
        btn_to_active.configure(fg_color=self.colors["accent_soft"], 
                                text_color=self.colors["accent"], 
                                border_width=0)
        
        # Entrance Animation
        self.after(10, lambda: self.animate_panel_entrance(panel_to_show))
        
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
            self.toggle_preview_btn.configure(text="Show Preview")
            self.action_bar.place(relx=0.5, rely=0.92, anchor="center") # Centered for full width
        else:
            self.preview_column.grid(row=0, column=1, sticky="nsew")
            self.main_container.grid_columnconfigure(0, weight=3)
            self.main_container.grid_columnconfigure(1, weight=2)
            self.toggle_preview_btn.configure(text="Hide Preview")
            self.action_bar.place(relx=0.42, rely=0.92, anchor="center") # Offset for partial width

    def change_zoom(self, delta):
        self.preview_zoom = max(0.5, min(2.0, self.preview_zoom + delta))
        self.zoom_label.configure(text=f"{int(self.preview_zoom * 100)}%")
        new_size = int(10 * self.preview_zoom)
        self.preview_text.configure(font=ctk.CTkFont(family="Times New Roman", size=new_size))

    def update_live_preview(self):
        # Microfeedback status change with pulsing dot
        self.set_status("Updating preview", "accent")
        self._animate_status_pulse(0)
        
        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")
        
        company = self.company_entry.get().strip().title() or "[Company Name]"
        city = self.cl_city.get().strip().title()
        country = self.cl_country.get().strip().title()
        
        if self.preview_mode.get() == "CV":
            location = self.current_location_entry.get().strip() or user_config.location() or ""
            relocation_line = user_config.relocation_line(location)
            user_name = user_config.name().upper()
            tail = f" {relocation_line}" if relocation_line else ""
            content = (
                f"{user_name}\n\n"
                f"PROFESSIONAL SUMMARY\n"
                f"{self.summary_text.get('0.0', 'end').strip()}{tail}\n\n"
            )
            for job, widget in self.job_text_widgets.items():
                content += f"{job.upper()}\n"

                headline = self.job_headline_widgets[job].get().strip()
                if headline:
                    content += f"[{headline}]\n"

                bullets = widget.get("0.0", "end").strip().split("\n")
                for b in bullets:
                    if b.strip():
                        content += f"- {b.strip()}\n"
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
                f"{user_config.name()}"
            )
            
        self.preview_text.insert("end", content)
        
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
        
        # Regex for common date patterns (e.g., "Jan 2024 - May 2025", "May 2025 - Present", "2022 - 2023")
        # Matches months + year, or year-year ranges, or just "Month Year"
        date_pattern = re.compile(
            r"(?i)\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\b.*\d{2,4}"
            r"|\b\d{4}\s?-\s?(Present|\d{4}|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b)"
            r"|^Present$|^\d{4}$"
        )

        def normalize_for_match(s):
            # Remove all whitespace and common punctuation for a "fuzzy" match
            return re.sub(r'[\s,.\-\|]', '', s).upper()

        for line in lines:
            line = line.strip()
            if not line: continue
            
            # 1. Check for Job Title match
            matched_job = None
            norm_line = normalize_for_match(line)
            
            for title in JOB_POSITIONS.keys():
                # Extract the company/main identifier (part before the delimiter)
                company_part = re.split(r'[\-\|]', title)[0].strip()
                norm_company = normalize_for_match(company_part)
                
                # Use fuzzy normalized match
                if norm_company and norm_company in norm_line and len(line) < 120:
                    matched_job = title
                    break
            
            if matched_job:
                current_job = matched_job
                job_bullets[current_job] = []
                continue
            
            # 2. If we are within a job block, process bullets
            if current_job:
                # SKIP if it looks like a date range or metadata line
                if date_pattern.search(line) and len(line) < 50:
                    continue
                
                # CLEAN bullet characters from the start of the line
                bullet_chars = ['-', '*']
                clean_line = line
                for char in bullet_chars:
                    if clean_line.startswith(char):
                        # Some people paste " - Bullet", we want to remove the "-" and keep the rest
                        clean_line = clean_line[1:].strip()
                
                # Further check: if line is just a city/country, it might be metadata too
                # Usually these are very short lines right after dates
                if len(clean_line) < 30 and any(x in line for x in [", ", "  "]):
                    # Heuristic: might be "Bristol, UK" or similar
                    # But we'll be careful not to skip actual short bullets
                    pass

                if clean_line:
                    job_bullets[current_job].append(clean_line)
        
        for job, bullets in job_bullets.items():
            if job in self.job_text_widgets:
                self.job_text_widgets[job].delete("0.0", "end")
                self.job_text_widgets[job].insert("0.0", "\n".join(bullets))
        
        self.set_status("Bullets Sorted (Filtered Dates)", "success")
        self.show_cv_panel()

    # ------------------------------------------------------------------
    # JD-aware ranking handlers
    # ------------------------------------------------------------------
    def run_jd_ranking(self):
        """Score every bullet in the inventory against the pasted JD.

        Runs the ranker on a background thread so the UI stays responsive
        if the user has opted into a heavier model (embeddings, Ollama).
        """
        jd = self.jd_text.get("0.0", "end").strip()
        if not jd:
            self.set_status("Paste a JD first", "text_muted")
            return

        # Preflight: fail fast if no local LLM backend is usable.
        try:
            from core.jd_ranker import backend_status
            bstat = backend_status()
            active = (bstat.get("active") or "").lower()
            configured = bstat.get("configured", "local")
            if "local tf-idf" in active:
                self._render_jd_error(
                    "No local LLM backend is active.\n"
                    f"Configured provider: {configured}\n\n"
                    "Set llm.provider to 'ollama' or 'sentence_transformers', "
                    "then ensure the backend is installed/running."
                )
                return
        except Exception:
            # If diagnostics fail, continue and let worker handle runtime errors.
            pass

        self.set_status("Ranking bullets...", "accent")
        self.jd_results_label.configure(text="Scoring JD against your CV bullets...")
        self.jd_results_box.configure(state="normal")
        self.jd_results_box.delete("0.0", "end")
        self.jd_results_box.insert("0.0", "Running local LLM scoring...\nPlease wait.")
        self.jd_results_box.configure(state="disabled")
        inventory = user_config.job_positions()

        def worker():
            try:
                from core.jd_ranker import (
                    rank_bullets,
                    compute_fit_score,
                    generate_match_recommendations,
                )
                ranked = rank_bullets(jd, inventory)
                fit = compute_fit_score(jd, ranked)
                backend = (fit.get("backend") or "").lower()
                if "local tf-idf" in backend:
                    raise RuntimeError(
                        "Local LLM backend not available for matching. "
                        "Start Ollama or install sentence-transformers."
                    )
                rec_payload = generate_match_recommendations(
                    jd, ranked, max_items=5
                )
                self.after(0, lambda: self._render_jd_results(ranked, fit, rec_payload))
            except Exception as e:
                logger.error(f"JD ranking failed: {e}")
                err_msg = str(e)
                self.after(0, lambda m=err_msg: self._render_jd_error(m))

        threading.Thread(target=worker, daemon=True).start()

    def _render_jd_results(self, ranked, fit, rec_payload=None):
        """Paint the ranked list, fit score, and recommendations into the UI."""
        self.last_jd_ranking = ranked
        self.last_jd_text = self.jd_text.get("0.0", "end").strip()

        rec_payload = rec_payload or {}
        recommendations = rec_payload.get("recommendations", [])
        rec_source = rec_payload.get("source", "local-llm")
        self.last_jd_recommendations = recommendations
        self.last_jd_fit = fit
        self.last_jd_analysis = rec_payload

        backend = fit.get("backend", "local TF-IDF")
        score_pct = int(round(fit.get("fit_score", 0.0) * 100))
        n_bullets = fit.get("considered", len(ranked))
        n_strong = fit.get("strong_matches", 0)

        self.jd_results_label.configure(
            text=(
                f"Overall fit: {score_pct}%  |  "
                f"{n_strong} strong matches across {n_bullets} bullets  |  "
                f"backend: {backend}  |  recommendations: {rec_source}"
            )
        )

        lines = []
        lines.append("RECOMMENDED FIXES")
        lines.append(f"source: {rec_source}")
        lines.append("")
        if recommendations:
            for i, rec in enumerate(recommendations, start=1):
                lines.append(f"{i}. {rec}")
        else:
            lines.append("No recommendations generated.")
        lines.append("")
        lines.append("TOP MATCHED BULLETS")
        lines.append("")

        for i, item in enumerate(ranked[:20], start=1):
            keywords = (
                f"  [{', '.join(item.matched_keywords[:6])}]"
                if item.matched_keywords else ""
            )
            item_pct = int(round(item.score * 100))
            lines.append(f"{i:>2}. [{item_pct:>2}%] {item.job_title}")
            lines.append(f"     - {item.bullet}")
            if keywords:
                lines.append(f"     matched:{keywords}")
            lines.append("")

        self.jd_results_box.configure(state="normal")
        self.jd_results_box.delete("0.0", "end")
        self.jd_results_box.insert("0.0", "\n".join(lines) if lines else "No bullets ranked.")
        self.jd_results_box.configure(state="disabled")
        self.set_status("Ranking complete", "success")

    def _render_jd_error(self, message):
        """Show an explicit JD-ranking failure in the results panel."""
        self.jd_results_label.configure(text="Ranking failed")
        self.jd_results_box.configure(state="normal")
        self.jd_results_box.delete("0.0", "end")
        self.jd_results_box.insert(
            "0.0",
            "Local LLM required.\n\n"
            f"Error: {message}\n\n"
            "Fix:\n"
            "1. Start Ollama locally.\n"
            "2. Ensure a generation model is available (e.g., llama3.2:3b).\n"
            "3. Re-run Rank Against JD.",
        )
        self.jd_results_box.configure(state="disabled")
        self.set_status("Ranking failed", "text_muted")


    def show_llm_reason_dialog(self):
        """Show a small dialog explaining what the LLM ranked and why."""
        if not self.last_jd_ranking:
            self.set_status("Run 'Rank Against JD' first", "text_muted")
            return

        fit = self.last_jd_fit or {}
        analysis = self.last_jd_analysis or {}
        source = analysis.get("source", "local-llm")
        recommendations = analysis.get("recommendations", [])
        missing = analysis.get("missing_keywords", [])

        dlg = ctk.CTkToplevel(self)
        dlg.title("LLM Match Explanation")
        dlg.geometry("760x560")
        dlg.transient(self)

        header = ctk.CTkLabel(
            dlg,
            text=(
                f"Fit: {int(round((fit.get('fit_score', 0.0))*100))}%   |   "
                f"Backend: {fit.get('backend', 'unknown')}   |   Source: {source}"
            ),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text"],
            justify="left",
            anchor="w",
        )
        header.pack(fill="x", padx=16, pady=(12, 8))

        box = ctk.CTkTextbox(
            dlg,
            fg_color=self.colors["bg"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
            corner_radius=12,
            font=ctk.CTkFont(family="Inter", size=13),
            wrap="word",
        )
        box.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        lines = []
        lines.append("WHAT THE MODEL RANKED HIGHEST")
        lines.append("")
        for i, item in enumerate(self.last_jd_ranking[:8], start=1):
            item_pct = int(round(item.score * 100))
            lines.append(f"{i}. [{item_pct}%] {item.job_title}")
            lines.append(f"   - {item.bullet}")
            if item.matched_keywords:
                lines.append(f"   matched keywords: {', '.join(item.matched_keywords[:8])}")
            lines.append("")

        lines.append("LLM RECOMMENDATIONS")
        lines.append("")
        if recommendations:
            for i, rec in enumerate(recommendations, start=1):
                lines.append(f"{i}. {rec}")
        else:
            lines.append("No recommendations returned by local LLM.")
        lines.append("")

        lines.append("MISSING JD KEYWORDS")
        lines.append("")
        lines.append(", ".join(missing[:20]) if missing else "None reported.")

        box.insert("0.0", "\n".join(lines))
        box.configure(state="disabled")

    def apply_top_ranked_bullets(self):
        """Replace each job's CV bullets with the top 5 from the last ranking.

        Non-destructive in the sense that the inventory in user_config is
        not modified; only the in-memory CV builder widgets are updated.
        The user can still tweak and revert before generating.
        """
        if not self.last_jd_ranking:
            self.set_status("Run 'Rank Against JD' first", "text_muted")
            return

        from core.jd_ranker import top_bullets_per_job
        buckets = top_bullets_per_job(self.last_jd_ranking, per_job_cap=5)

        applied = 0
        for job_title, items in buckets.items():
            widget = self.job_text_widgets.get(job_title)
            if widget is None:
                continue
            widget.delete("0.0", "end")
            widget.insert("0.0", "\n".join(item.bullet for item in items))
            applied += len(items)

        self.set_status(f"Applied {applied} bullets to the CV builder", "success")
        self.show_cv_panel()

    def _animate_status_pulse(self, step):
        if "Updating" not in self.status_label.cget("text"): return
        dots = "." * (step % 4)
        self.status_label.configure(text=f"Updating preview{dots}")
        self.after(300, lambda: self._animate_status_pulse(step + 1))

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
        current_location = self.current_location_entry.get().strip().title()
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
        headlines = {}
        for job, widget in self.job_text_widgets.items():
            text = widget.get("0.0", "end").strip()
            if text:
                bullets[job] = [b.strip() for b in text.split("\n") if b.strip()]
            
            headline = self.job_headline_widgets[job].get().strip()
            if headline:
                headlines[job] = headline
        
        cl_data = {
            "hiring_manager": self.cl_hiring_manager.get().strip(),
            "city": self.cl_city.get().strip().title(),
            "country": self.cl_country.get().strip().title(),
            "date": self.cl_date.get().strip(),
            "body": self.cl_body_text.get("0.0", "end").strip().replace("[Company Name]", company)
        }
        
        template = self.template_path_entry.get().strip()
        threading.Thread(target=self._run_generation, args=(mode, template, company, cv_country, summary, bullets, cl_data, headlines, current_location), daemon=True).start()

    def _run_generation(self, mode, template, company, cv_country, summary, bullets, cl_data, headlines=None, current_location=None):
        try:
            role_title = self.role_title_entry.get().strip()
            
            if mode == "cv":
                success, result = self.cv_service.generate_cv(template, company, cv_country, summary, bullets, headlines=headlines, current_location=current_location)
            elif mode == "cl":
                success, result = self.cv_service.generate_cl(company, cl_data)
            else:
                success, result = self.cv_service.generate_both(template, company, cv_country, summary, bullets, cl_data, headlines=headlines, current_location=current_location)
            
            # Additional update for role title in stats if it was provided
            if success and role_title:
                timestamp = datetime.now().strftime("%d-%m-%y")
                app_id = f"{timestamp}_{company.replace(' ', '_')}"
                self.stats_manager.update_field(app_id, "role_title", role_title)

            self.after(0, lambda: self._complete(success))
        except Exception as e:
            logger.error(f"Error in generation thread: {e}")
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
