import os
import threading
import sys
from datetime import datetime

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import customtkinter as ctk
from helpers.logger import logger
from core.config import DESIGN_TOKENS, DEFAULT_CL_BODY, SUMMARY_TEXT, SUPPORTED_CV_TEMPLATES
from core.cv_service import CVGeneratorService
from core.stats_manager import StatsManager
from core.application_audit import ApplicationAuditPanel
from core.experience_profile import auto_sort_experience_lines, load_profile, save_profile
from core.update_cv import get_template_capacity

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

        # State Variables
        self.templates = dict(SUPPORTED_CV_TEMPLATES)
        self.current_template_name = ctk.StringVar(value="Template 1")
        self.profile_data = load_profile()
        self.profile_data.setdefault("candidate", {})
        self.job_text_widgets = {}
        self.job_meta = {}
        self.job_editor_widgets = {}
        self.candidate_widgets = {}
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
        
        self.logo_label = ctk.CTkLabel(logo_container, text="✨ ApplyCraft", 
                                       font=ctk.CTkFont(family="Inter", size=30, weight="bold"),
                                       text_color=self.colors["accent"])
        self.logo_label.pack(pady=(0, 4))
        
        self.tagline_label = ctk.CTkLabel(logo_container, text="STRATEGIC CAREER ENGINE",
                                         font=ctk.CTkFont(family="Inter", size=12, weight="bold"), 
                                         text_color=self.colors["text_muted"])
        self.tagline_label.pack()

        # Navigation Buttons with keyboard shortcuts
        self.import_btn = self.create_nav_button("⚡  Smart Import", 1, self.show_import_panel)
        self.cv_btn = self.create_nav_button("💼  Experience (CV)", 2, self.show_cv_panel)
        self.cl_btn = self.create_nav_button("✉️  Cover Letter", 3, self.show_cl_panel)
        self.audit_btn = self.create_nav_button("📊  Audit & Stats", 4, self.show_audit_panel)
        self.settings_btn = self.create_nav_button("⚙️  Settings", 6, self.show_settings_panel)
        
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
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color=self.colors["success"], font=ctk.CTkFont(size=14))
        self.status_dot.pack(side="left", padx=(10, 4), pady=4)
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", font=ctk.CTkFont(size=13, weight="normal"), text_color=self.colors["text"])
        self.status_label.pack(side="left", padx=(0, 10), pady=4)

        # Preview Toggle Button
        self.toggle_preview_btn = ctk.CTkButton(self.header_frame, text="👁️  Hide Preview", width=140, height=40,
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
        
        self.zoom_out_btn = ctk.CTkButton(zoom_frame, text="−", width=35, height=30, fg_color="transparent", text_color=self.colors["text"], hover_color=self.colors["sidebar"], command=lambda: self.change_zoom(-0.1))
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
        self.gen_both_btn = ctk.CTkButton(self.action_bar, text="🪄 Generate (Ctrl+G)", corner_radius=24,
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

        self.open_folder_btn = ctk.CTkButton(self.action_bar, text="📁", corner_radius=22,
                                      fg_color="transparent", text_color=self.colors["text_muted"],
                                      hover_color=self.colors["accent_soft"], height=42, width=50,
                                      command=self.open_outputs)
        self.open_folder_btn.pack(side="left", padx=(15, 5), pady=10)

        # Panels
        self.cv_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.cl_panel = ctk.CTkScrollableFrame(self.editor_column, fg_color="transparent")
        self.import_panel = ctk.CTkFrame(self.editor_column, fg_color="transparent")
        self.audit_panel = ApplicationAuditPanel(self.editor_column, colors=self.colors)
        self.settings_panel = ctk.CTkFrame(self.editor_column, fg_color="transparent")
        
        # Entrance Animation State
        self.panels = [self.cv_panel, self.cl_panel, self.import_panel, self.settings_panel, self.audit_panel]
            
        self.setup_cv_panel()
        self.setup_cl_panel()
        self.setup_import_panel()
        self.setup_settings_panel()
        
        self.show_cv_panel()
        
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
        self.cv_template_selector = ctk.CTkSegmentedButton(card, values=list(self.templates.keys()),
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

        summary_default = self.profile_data.get("summary", SUMMARY_TEXT)
        self.summary_text = self.create_textbox(card, "Professional Summary", summary_default)
        self.summary_text.bind("<KeyRelease>", lambda e: self._on_summary_change())

        profile_card = self.create_card(self.cv_panel, "EXPERIENCE PROFILE")
        ctk.CTkLabel(
            profile_card,
            text="Store unlimited experiences. Use Include in CV + ordering controls to choose what fits the active template.",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
        ).pack(anchor="w", padx=25, pady=(0, 10))
        controls_row = ctk.CTkFrame(profile_card, fg_color="transparent")
        controls_row.pack(fill="x", padx=25, pady=(0, 14))
        add_btn = ctk.CTkButton(
            controls_row,
            text="+ Add Experience",
            width=140,
            height=36,
            fg_color=self.colors["accent"],
            command=self._add_experience,
        )
        add_btn.pack(side="left")
        self.capacity_label = ctk.CTkLabel(
            controls_row,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
        )
        self.capacity_label.pack(side="right")

        self.experience_cards_host = ctk.CTkFrame(self.cv_panel, fg_color="transparent")
        self.experience_cards_host.pack(fill="x", padx=0, pady=0)
        self.render_experience_cards()

    def _on_summary_change(self):
        self.profile_data["summary"] = self.summary_text.get("0.0", "end").strip()
        save_profile(self.profile_data)
        self.update_live_preview()

    def _new_experience_template(self):
        index = len(self.profile_data.get("experiences", [])) + 1
        existing = {exp.get("anchor_key") for exp in self.profile_data.get("experiences", [])}
        anchor = f"exp_custom_{index}"
        while anchor in existing:
            index += 1
            anchor = f"exp_custom_{index}"
        return {
            "anchor_key": anchor,
            "legacy_key": "",
            "company": "",
            "title": "",
            "date_range": "",
            "location": "",
            "headline": "",
            "aliases": [],
            "bullets": [],
            "include_in_cv": True,
        }

    def _collect_experiences_from_ui(self):
        experiences = []
        for exp in self.profile_data.get("experiences", []):
            anchor = exp.get("anchor_key")
            bullets_text = self.job_text_widgets.get(anchor).get("0.0", "end").strip() if anchor in self.job_text_widgets else ""
            bullets = [line.strip() for line in bullets_text.split("\n") if line.strip()]
            
            editor = self.job_editor_widgets.get(anchor, {})
            headline = editor.get("headline").get().strip() if "headline" in editor else ""
            company = editor.get("company").get().strip() if "company" in editor else str(exp.get("company", "")).strip()
            title = editor.get("title").get().strip() if "title" in editor else str(exp.get("title", "")).strip()
            date_range = editor.get("date_range").get().strip() if "date_range" in editor else str(exp.get("date_range", "")).strip()
            location = editor.get("location").get().strip() if "location" in editor else str(exp.get("location", "")).strip()
            aliases_text = editor.get("aliases").get().strip() if "aliases" in editor else ""
            include_in_cv = editor.get("include_var").get() if "include_var" in editor else bool(exp.get("include_in_cv", True))
            aliases = [item.strip() for item in aliases_text.split(",") if item.strip()]

            updated = dict(exp)
            updated["company"] = company
            updated["title"] = title
            updated["date_range"] = date_range
            updated["location"] = location
            updated["bullets"] = bullets
            updated["headline"] = headline
            updated["aliases"] = aliases
            updated["include_in_cv"] = bool(include_in_cv)
            experiences.append(updated)
        return experiences

    def _collect_candidate_from_ui(self):
        current = dict(self.profile_data.get("candidate", {}))
        if not self.candidate_widgets:
            return current
        current["name"] = self.candidate_widgets["name"].get().strip()
        current["email"] = self.candidate_widgets["email"].get().strip()
        current["linkedin"] = self.candidate_widgets["linkedin"].get().strip()
        current["location"] = self.candidate_widgets["location"].get().strip()
        current["relocation_visa_line"] = self.candidate_widgets["relocation_visa_line"].get().strip()
        current["show_relocation_visa_line"] = bool(self.candidate_widgets["show_relocation_var"].get())
        return current

    def _persist_profile_from_ui(self):
        self.profile_data["experiences"] = self._collect_experiences_from_ui()
        self.profile_data["summary"] = self.summary_text.get("0.0", "end").strip()
        self.profile_data["candidate"] = self._collect_candidate_from_ui()
        save_profile(self.profile_data)

    def _on_experience_content_change(self):
        self._persist_profile_from_ui()
        self._update_template_capacity_label()
        self.update_live_preview()

    def _add_experience(self):
        self.profile_data.setdefault("experiences", []).append(self._new_experience_template())
        save_profile(self.profile_data)
        self.render_experience_cards()
        self.update_live_preview()

    def _move_experience(self, anchor_key, direction):
        experiences = self.profile_data.get("experiences", [])
        idx = next((i for i, exp in enumerate(experiences) if exp.get("anchor_key") == anchor_key), None)
        if idx is None:
            return
        swap_idx = idx + direction
        if swap_idx < 0 or swap_idx >= len(experiences):
            return
        experiences[idx], experiences[swap_idx] = experiences[swap_idx], experiences[idx]
        save_profile(self.profile_data)
        self.render_experience_cards()
        self.update_live_preview()

    def _remove_experience(self, anchor_key):
        experiences = self.profile_data.get("experiences", [])
        if len(experiences) <= 1:
            self.set_status("At least one experience is required", "text_muted")
            return
        self.profile_data["experiences"] = [exp for exp in experiences if exp.get("anchor_key") != anchor_key]
        save_profile(self.profile_data)
        self.render_experience_cards()
        self.update_live_preview()

    def _display_heading(self, exp):
        company = exp.get("company", "").strip()
        title = exp.get("title", "").strip()
        date_range = exp.get("date_range", "").strip()
        if company and title:
            heading = f"{company} | {title}"
        else:
            heading = company or title or "New Experience"
        if date_range:
            heading = f"{heading} ({date_range})"
        return heading

    def render_experience_cards(self):
        for child in self.experience_cards_host.winfo_children():
            child.destroy()

        self.job_text_widgets = {}
        self.job_meta = {}
        self.job_editor_widgets = {}

        experiences = self.profile_data.get("experiences", [])
        if not experiences:
            experiences = [self._new_experience_template()]
            self.profile_data["experiences"] = experiences
            save_profile(self.profile_data)

        self._update_template_capacity_label()

        for idx, exp in enumerate(experiences, start=1):
            anchor = exp.get("anchor_key")
            self.job_meta[anchor] = dict(exp)

            card = self.create_card(self.experience_cards_host, f"Experience {idx}: {self._display_heading(exp)}")

            top_controls = ctk.CTkFrame(card, fg_color="transparent")
            top_controls.pack(fill="x", padx=28, pady=(0, 6))
            include_var = ctk.BooleanVar(value=bool(exp.get("include_in_cv", True)))
            include_switch = ctk.CTkSwitch(
                top_controls,
                text="Include in this CV",
                variable=include_var,
                command=self._on_experience_content_change,
                text_color=self.colors["text"],
            )
            include_switch.pack(side="left")
            nav_controls = ctk.CTkFrame(top_controls, fg_color="transparent")
            nav_controls.pack(side="right")
            ctk.CTkButton(
                nav_controls,
                text="Up",
                width=54,
                height=30,
                fg_color=self.colors["input_bg"],
                text_color=self.colors["text"],
                border_width=1,
                border_color=self.colors["border"],
                command=lambda key=anchor: self._move_experience(key, -1),
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                nav_controls,
                text="Down",
                width=64,
                height=30,
                fg_color=self.colors["input_bg"],
                text_color=self.colors["text"],
                border_width=1,
                border_color=self.colors["border"],
                command=lambda key=anchor: self._move_experience(key, 1),
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                nav_controls,
                text="Remove",
                width=74,
                height=30,
                fg_color="transparent",
                text_color=self.colors["text_muted"],
                border_width=1,
                border_color=self.colors["border"],
                command=lambda key=anchor: self._remove_experience(key),
            ).pack(side="left")

            field_row_1 = ctk.CTkFrame(card, fg_color="transparent")
            field_row_1.pack(fill="x", padx=30, pady=(2, 0))
            company_frame = ctk.CTkFrame(field_row_1, fg_color="transparent")
            company_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
            title_frame = ctk.CTkFrame(field_row_1, fg_color="transparent")
            title_frame.pack(side="left", fill="x", expand=True)
            company_entry = self.create_input(company_frame, "Company", exp.get("company", ""), placeholder="e.g. Company name")
            title_entry = self.create_input(title_frame, "Job Title", exp.get("title", ""), placeholder="e.g. Data Analyst")

            field_row_2 = ctk.CTkFrame(card, fg_color="transparent")
            field_row_2.pack(fill="x", padx=30, pady=(0, 0))
            date_frame = ctk.CTkFrame(field_row_2, fg_color="transparent")
            date_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
            location_frame = ctk.CTkFrame(field_row_2, fg_color="transparent")
            location_frame.pack(side="left", fill="x", expand=True)
            date_entry = self.create_input(date_frame, "Date Range", exp.get("date_range", ""), placeholder="e.g. Apr 2025 - Oct 2025")
            location_entry = self.create_input(location_frame, "Location", exp.get("location", ""), placeholder="e.g. London, UK")

            aliases_text = ", ".join(exp.get("aliases", []))
            aliases_entry = self.create_input(card, "Aliases (comma separated)", aliases_text, placeholder="e.g. Company short name, previous name")
            for entry_widget in [company_entry, title_entry, date_entry, location_entry, aliases_entry]:
                entry_widget.bind("<KeyRelease>", lambda e: self._on_experience_content_change())

            ctk.CTkLabel(card, text="Role Headline (Optional)", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=30, pady=(10, 0))
            headline_entry = ctk.CTkEntry(card, height=45, fg_color=self.colors["input_bg"],
                                         text_color=self.colors["text"], border_width=1,
                                         border_color=self.colors["border"], corner_radius=10,
                                         placeholder_text="e.g. Led analytics modernization initiatives...",
                                         font=ctk.CTkFont(size=13, slant="italic"))
            headline_entry.pack(fill="x", padx=30, pady=(5, 10))
            headline_entry.insert(0, exp.get("headline", ""))
            headline_entry.bind("<KeyRelease>", lambda e: self._on_experience_content_change())

            bullets_text = self.create_textbox(card, "Role Highlights", "\n".join(exp.get("bullets", [])), height=150)
            bullets_text.bind("<KeyRelease>", lambda e: self._on_experience_content_change())

            self.job_text_widgets[anchor] = bullets_text
            self.job_editor_widgets[anchor] = {
                "include_var": include_var,
                "company": company_entry,
                "title": title_entry,
                "date_range": date_entry,
                "location": location_entry,
                "aliases": aliases_entry,
                "headline": headline_entry,
            }

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
        card = self.create_card(self.import_panel, "SMART BULLET PARSER")
        ctk.CTkLabel(card, text="Paste raw bullets with job titles. The system will auto-sort them.", 
                     font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"]).pack(anchor="w", padx=25)
        self.import_text = self.create_textbox(card, "", "", height=400)
        
        btn = ctk.CTkButton(card, text="⚡ Auto-Sort Into CV", corner_radius=10, 
                            fg_color=self.colors["accent"], height=45, command=self.auto_sort)
        btn.pack(fill="x", padx=25, pady=25)

        unmatched_card = self.create_card(self.import_panel, "UNMATCHED LINES")
        ctk.CTkLabel(
            unmatched_card,
            text="Lines that did not match any company/title aliases appear here.",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
        ).pack(anchor="w", padx=25, pady=(0, 10))
        self.unmatched_text = ctk.CTkTextbox(
            unmatched_card,
            height=180,
            fg_color=self.colors["bg"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
            corner_radius=12,
            font=ctk.CTkFont(family="Inter", size=14),
            wrap="word",
            border_spacing=10,
        )
        self.unmatched_text.pack(fill="x", padx=30, pady=(0, 20))
        self.unmatched_text.configure(state="disabled")


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
        self.template_selector = ctk.CTkSegmentedButton(card, values=list(self.templates.keys()),
                                                       variable=self.current_template_name,
                                                       command=self.update_template_path,
                                                       height=40,
                                                       fg_color=self.colors["input_bg"],
                                                       selected_color=self.colors["accent"],
                                                       selected_hover_color=self.colors["accent"])
        self.template_selector.pack(fill="x", padx=25, pady=(8, 15))
        self.template_path_value = ctk.CTkLabel(
            card,
            text=self.templates.get(self.current_template_name.get(), ""),
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_muted"],
            anchor="w",
            justify="left",
        )
        self.template_path_value.pack(fill="x", padx=25, pady=(0, 15))

        candidate = dict(self.profile_data.get("candidate", {}))
        candidate_card = self.create_card(self.settings_panel, "CANDIDATE PROFILE")
        self.candidate_widgets["name"] = self.create_input(
            candidate_card,
            "Candidate Name",
            candidate.get("name", ""),
            placeholder="e.g. Jane Doe",
        )
        self.candidate_widgets["email"] = self.create_input(
            candidate_card,
            "Email",
            candidate.get("email", ""),
            placeholder="e.g. jane@email.com",
        )
        self.candidate_widgets["linkedin"] = self.create_input(
            candidate_card,
            "LinkedIn",
            candidate.get("linkedin", ""),
            placeholder="e.g. linkedin.com/in/jane",
        )
        self.candidate_widgets["location"] = self.create_input(
            candidate_card,
            "Location",
            candidate.get("location", ""),
            placeholder="e.g. Berlin, Germany",
        )
        self.candidate_widgets["relocation_visa_line"] = self.create_input(
            candidate_card,
            "Relocation/Visa Line",
            candidate.get("relocation_visa_line", ""),
            placeholder="Optional summary suffix",
        )
        relocation_var = ctk.BooleanVar(value=bool(candidate.get("show_relocation_visa_line", False)))
        relocation_toggle = ctk.CTkSwitch(
            candidate_card,
            text="Show relocation/visa line in summary",
            variable=relocation_var,
            command=lambda: self._on_settings_change(),
            text_color=self.colors["text"],
        )
        relocation_toggle.pack(anchor="w", padx=30, pady=(0, 20))
        self.candidate_widgets["show_relocation_var"] = relocation_var

        for key in ("name", "email", "linkedin", "location", "relocation_visa_line"):
            self.candidate_widgets[key].bind("<KeyRelease>", lambda e: self._on_settings_change())

    def update_template_path(self, selected_name):
        path = self.templates.get(selected_name, "")
        if hasattr(self, "template_path_value"):
            self.template_path_value.configure(text=path)
        self._update_template_capacity_label()
        self.set_status(f"Switched to {selected_name}", "accent")
        self.update_live_preview()

    def _on_settings_change(self):
        self._persist_profile_from_ui()
        self.update_live_preview()

    def _template_capacity(self, template_path):
        if not template_path:
            return 0
        try:
            return get_template_capacity(template_path)
        except Exception as exc:
            logger.warning(f"Could not read template capacity: {exc}")
            return 0

    def _update_template_capacity_label(self):
        if not hasattr(self, "capacity_label"):
            return
        template = self.templates.get(self.current_template_name.get(), "")
        capacity = self._template_capacity(template)
        total = len(self.profile_data.get("experiences", []))
        included = sum(1 for exp in self.profile_data.get("experiences", []) if bool(exp.get("include_in_cv", True)))
        self.capacity_label.configure(text=f"Template slots: {capacity} | Included: {included} / Stored: {total}")

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

    # --- ONBOARDING PANEL (V2 INTELLIGENCE) ---
    def setup_onboarding_panel(self):
        # Onboarding is intentionally disabled in strict 2-template mode.
        return

    def _load_template_onboarding(self):
        return

    def _run_onboarding_analysis(self, path):
        return

    def _render_onboarding_results(self):
        return

    def _create_onboarding_block_card(self, parent, num, block):
        return {}

    def _finalize_onboarding(self):
        return

    # --- PANEL SHIFTING ---
    def show_panel(self, panel_to_show, btn_to_active, title):
        for p in self.panels:
            p.grid_forget()
        for b in [self.cv_btn, self.cl_btn, self.import_btn, self.settings_btn, self.audit_btn]:
            b.configure(fg_color="transparent", text_color=self.colors["text_muted"])
        
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
        
        btn_to_active.configure(fg_color=self.colors["accent_soft"], 
                                text_color=self.colors["accent"])
        
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
        self.set_status("Updating preview", "accent")
        self._animate_status_pulse(0)

        self.preview_text.configure(state="normal")
        self.preview_text.delete("0.0", "end")

        company = self.company_entry.get().strip().title() or "[Company Name]"
        city = self.cl_city.get().strip().title()
        country = self.cl_country.get().strip().title()
        candidate = self._collect_candidate_from_ui()
        candidate_name = candidate.get("name", "").strip() or "Your Name"

        if self.preview_mode.get() == "CV":
            summary_text = self.summary_text.get("0.0", "end").strip()
            if bool(candidate.get("show_relocation_visa_line", False)) and candidate.get("relocation_visa_line", "").strip():
                summary_text = f"{summary_text} {candidate.get('relocation_visa_line').strip()}"
            content = f"{candidate_name.upper()}\n\nPROFESSIONAL SUMMARY\n{summary_text}\n\n"
            for exp in self._collect_experiences_from_ui():
                if not bool(exp.get("include_in_cv", True)):
                    continue
                anchor = exp.get("anchor_key")
                widget = self.job_text_widgets.get(anchor)
                if not widget:
                    continue
                title_line = " | ".join(part for part in [exp.get("company", "").strip(), exp.get("title", "").strip()] if part)
                meta_line = " | ".join(part for part in [exp.get("date_range", "").strip(), exp.get("location", "").strip()] if part)
                heading = title_line or self._display_heading(exp)
                content += f"{heading.upper()}\n"
                if meta_line:
                    content += f"{meta_line}\n"
                
                headline = exp.get("headline", "").strip()
                if headline:
                    content += f"[{headline}]\n" # Simulating italics with brackets in plain text preview

                bullets = widget.get("0.0", "end").strip().split("\n")
                for bullet in bullets:
                    if bullet.strip():
                        content += f"- {bullet.strip()}\n"
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
                f"{candidate_name}"
            )

        self.preview_text.insert("end", content)

        line_count = int(self.preview_text.index("end-1c").split(".")[0])
        pages = max(1, (line_count // 55) + 1)
        self.page_indicator.configure(text=f"Page 1 / {pages}" if line_count < 55 else f"Pages: ~{pages}")
        if line_count > 55:
            self.page_indicator.configure(text_color="orange")
        else:
            self.page_indicator.configure(text_color=self.colors["text_muted"])

        self.preview_text.configure(state="disabled")
        self.after(500, lambda: self.set_status("Ready", "success"))

    def auto_sort(self):
        raw_text = self.import_text.get("0.0", "end").strip()
        if not raw_text:
            return

        experiences = self._collect_experiences_from_ui()
        sorted_bullets, unmatched_lines = auto_sort_experience_lines(raw_text, experiences)

        for anchor, widget in self.job_text_widgets.items():
            widget.delete("0.0", "end")
            if anchor in sorted_bullets:
                widget.insert("0.0", "\n".join(sorted_bullets[anchor]))

        if self.unmatched_text is not None:
            self.unmatched_text.configure(state="normal")
            self.unmatched_text.delete("0.0", "end")
            if unmatched_lines:
                self.unmatched_text.insert("0.0", "\n".join(unmatched_lines))
            self.unmatched_text.configure(state="disabled")

        self._persist_profile_from_ui()
        if unmatched_lines:
            self.set_status(f"Bullets sorted. {len(unmatched_lines)} unmatched line(s).", "success")
        else:
            self.set_status("Bullets Sorted", "success")
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
        self._persist_profile_from_ui()
        all_experiences = self._collect_experiences_from_ui()
        selected_experiences = [exp for exp in all_experiences if bool(exp.get("include_in_cv", True))]
        if not selected_experiences and all_experiences:
            selected_experiences = [all_experiences[0]]
        candidate_profile = self._collect_candidate_from_ui()

        cl_data = {
            "hiring_manager": self.cl_hiring_manager.get().strip(),
            "city": self.cl_city.get().strip().title(),
            "country": self.cl_country.get().strip().title(),
            "date": self.cl_date.get().strip(),
            "body": self.cl_body_text.get("0.0", "end").strip().replace("[Company Name]", company)
        }
        
        selected_template = self.current_template_name.get()
        template = self.templates.get(selected_template, "")
        if not template:
            self.set_status("Invalid template selection", "text_muted")
            for btn in [self.gen_both_btn, self.gen_cv_btn, self.gen_cl_btn]:
                btn.configure(state="normal")
            return
        capacity = self._template_capacity(template)
        if capacity > 0 and len(selected_experiences) > capacity:
            self.set_status(
                f"Template has {capacity} base slots; extra experiences will be appended.",
                "text_muted",
            )

        bullets = {}
        for idx, exp in enumerate(selected_experiences):
            key = exp.get("anchor_key") or f"exp_{idx + 1}"
            exp_bullets = exp.get("bullets", [])
            if exp_bullets:
                bullets[key] = exp_bullets
        threading.Thread(
            target=self._run_generation,
            args=(mode, template, company, cv_country, summary, bullets, cl_data, selected_experiences, candidate_profile),
            daemon=True,
        ).start()

    def _run_generation(self, mode, template, company, cv_country, summary, bullets, cl_data, experiences, candidate_profile):
        try:
            role_title = self.role_title_entry.get().strip()
            
            if mode == "cv":
                success, result = self.cv_service.generate_cv(
                    template,
                    company,
                    cv_country,
                    summary,
                    bullets,
                    experiences=experiences,
                    candidate_profile=candidate_profile,
                )
            elif mode == "cl":
                success, result = self.cv_service.generate_cl(company, cl_data, candidate_profile=candidate_profile)
            else:
                success, result = self.cv_service.generate_both(
                    template,
                    company,
                    cv_country,
                    summary,
                    bullets,
                    cl_data,
                    experiences=experiences,
                    candidate_profile=candidate_profile,
                )
            
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

