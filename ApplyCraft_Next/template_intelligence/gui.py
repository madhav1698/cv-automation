import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from .analyzer import TemplateAnalyzer
from .learner import TemplateLearner
from .schemas import TemplateAnalysis, TemplateConfig

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TemplateIntelligenceUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ApplyCraft | Template Intelligence Dashboard")
        self.geometry("1100x700")

        self.current_analysis = None
        self.current_path = None

        self._setup_ui()

    def _setup_ui(self):
        # Grid layout 1x2
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Template Intelligence", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.load_btn = ctk.CTkButton(self.sidebar, text="Import New Template", command=self._load_template)
        self.load_btn.grid(row=1, column=0, padx=20, pady=10)

        self.label_info = ctk.CTkLabel(self.sidebar, text="Template Patterns", text_color="gray")
        self.label_info.grid(row=2, column=0, padx=20, pady=(20, 0))

        # Stats section
        self.stats_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Main Content Area
        self.main_content = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)

        # Welcome Placeholder
        self.welcome_label = ctk.CTkLabel(self.main_content, text="Please import a .docx CV template to begin analysis", font=ctk.CTkFont(size=14))
        self.welcome_label.pack(expand=True, pady=200)

    def _load_template(self):
        path = filedialog.askopenfilename(filetypes=[("Word Documents", "*.docx")])
        if not path: return

        self.current_path = path
        self._run_analysis(path)

    def _run_analysis(self, path):
        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        self.welcome_label = ctk.CTkLabel(self.main_content, text=f"Analyzing {os.path.basename(path)}...", font=ctk.CTkFont(size=16))
        self.welcome_label.pack(pady=20)
        self.main_content.update()

        try:
            analyzer = TemplateAnalyzer(path)
            self.current_analysis = analyzer.analyze()
            self._render_results()
        except Exception as e:
            self.welcome_label.configure(text=f"Analysis Failed: {str(e)}", text_color="red")

    def _render_results(self):
        # Clear again
        for widget in self.main_content.winfo_children():
            widget.destroy()

        header_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(40, 20))

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x")

        title = ctk.CTkLabel(title_frame, text="Step 2: Label Detected Entries", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")

        # Experience Blocks
        self.block_entries = []
        blocks = self.current_analysis.inferred_experience_blocks
        for i, block in enumerate(blocks):
            entry_widgets = self._create_block_card(i + 1, block)
            self.block_entries.append((block, entry_widgets))

        # Learned Config Preview
        learn_btn = ctk.CTkButton(self.main_content, text="Confirm & Save Template Design", 
                                  command=self._finalize_template,
                                  fg_color="#2ecc71", hover_color="#27ae60", height=45, font=ctk.CTkFont(weight="bold"))
        learn_btn.pack(pady=40, padx=40, fill="x")

    def _create_block_card(self, num, block):
        card = ctk.CTkFrame(self.main_content, corner_radius=15, border_width=1, border_color="#333333")
        card.pack(fill="x", padx=40, pady=10)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x")
        
        ctk.CTkLabel(title_row, text=f"DETECTOR FOUND: ENTRY #{num}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#3498db").pack(side="left")

        # Show snippet of what we found
        snippet_text = self._get_snippet(block)
        snippet_label = ctk.CTkLabel(inner, text=f"Raw text found: \"{snippet_text}...\"", font=ctk.CTkFont(size=11, slant="italic"), text_color="gray")
        snippet_label.pack(anchor="w", pady=(5, 15))

        fields_row = ctk.CTkFrame(inner, fg_color="transparent")
        fields_row.pack(fill="x")

        # Form Entries
        entry_widgets = {}
        
        form_data = [
            ("company", "Company Name", block.company_idx),
            ("role", "Job Title / Role", block.role_idx),
            ("dates", "Date Range", block.date_idx)
        ]

        for i, (key, label, idx) in enumerate(form_data):
            f = ctk.CTkFrame(fields_row, fg_color="transparent")
            f.grid(row=0, column=i, sticky="ew", padx=5)
            fields_row.grid_columnconfigure(i, weight=1)

            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(anchor="w", padx=2)
            
            # Initial value hint
            hint = self.current_analysis.paragraphs[idx].text if idx is not None else ""
            
            entry = ctk.CTkEntry(f, placeholder_text=f"Enter {label.lower()}...")
            entry.insert(0, hint)
            entry.pack(fill="x", pady=5)
            entry_widgets[key] = entry

        # Bullet info
        if block.bullet_start_idx is not None:
            count = block.bullet_end_idx - block.bullet_start_idx + 1
            bullet_box = ctk.CTkFrame(inner, fg_color="#1a2a3a", corner_radius=8)
            bullet_box.pack(fill="x", pady=(15, 0))
            ctk.CTkLabel(bullet_box, text=f"✓ Dynamic Bullet Zone Detected ({count} original bullets found)", font=ctk.CTkFont(size=11)).pack(padx=10, pady=5)
        
        return entry_widgets

    def _get_snippet(self, block):
        indices = [idx for idx in [block.company_idx, block.role_idx, block.location_idx] if idx is not None]
        if not indices: return "No text found"
        return self.current_analysis.paragraphs[min(indices)].text[:60]

    def _finalize_template(self):
        # Update blocks with user labels
        for block, widgets in self.block_entries:
            block.company_label = widgets["company"].get()
            block.role_label = widgets["role"].get()
            block.date_label = widgets["dates"].get()

        # Learn and save
        try:
            learner = TemplateLearner(self.current_analysis, self.current_path)
            config = learner.learn()
            
            config_path = os.path.join(os.path.dirname(self.current_path), "template_config.json")
            learner.save_config(config, "template_config.json") # Save local for testing
            
            tk.messagebox.showinfo("Success", f"Template design saved!\nFuture generations will use this mapping.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to save design: {e}")

if __name__ == "__main__":
    app = TemplateIntelligenceUI()
    app.mainloop()
