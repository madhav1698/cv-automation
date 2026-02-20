import sys
import os

# Set up paths for internal imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import customtkinter as ctk
from datetime import datetime, timedelta
from stats_manager import StatsManager
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import csv
try:
    from tkcalendar import DateEntry
    CALENDAR_AVAILABLE = True
except ImportError:
    CALENDAR_AVAILABLE = False
    print("tkcalendar not installed. Install with: pip install tkcalendar")

class ApplicationAuditPanel(ctk.CTkFrame):
    def __init__(self, parent, colors=None):
        super().__init__(parent, fg_color="transparent")

        # Design Tokens - Unified for premium feel
        self.colors = colors or {
            "bg": ("#F9FAFB", "#0B0F14"),
            "input_bg": ("#FFFFFF", "#1A202C"),
            "accent": "#6366F1",
            "text": ("#111827", "#F3F4F6"),
            "text_muted": ("#6B7280", "#9CA3AF"),
            "border": ("#E5E7EB", "#1F2937"),
            "success": "#10B981",
            "card": ("#FFFFFF", "#161D29")
        }
        self.stats_manager = StatsManager(os.path.join(current_dir, ".."))
        
        # State
        self.search_query = ctk.StringVar()
        self.sort_order = ctk.StringVar(value="Latest First")
        self.date_filter = ctk.StringVar(value="Last 30 Days")
        self.status_filter = ctk.StringVar(value="All")
        self.country_filter = ctk.StringVar(value="All")
        self.radar_filter = ctk.StringVar(value="All") # New: Radar filtering
        self.available_countries = ["All"]
        self.custom_date_from = None
        self.custom_date_to = None
        self.search_timer = None
        self.filtered_data = []

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Use a Scrollable Frame as the main container for the dashboard
        self.main_scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll_container.grid(row=0, column=0, sticky="nsew")
        self.main_scroll_container.grid_columnconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self.main_scroll_container, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 30)) # More breathable padding
        ctk.CTkLabel(header_frame, text="Application Command Center", 
                      font=ctk.CTkFont(family="Inter", size=34, weight="bold"),
                      text_color=self.colors["text"]).pack(side="left")

        # Summary Card
        self.setup_summary_card(main_frame)
        
        # Graph Card (Collapsible)
        self.setup_graph_panel(main_frame)

        # Intelligence Panel (Funnel & Markets)
        self.setup_intelligence_panel(main_frame)

        # Controls Card
        self.setup_controls_card(main_frame)

        # Treeview Table (MUCH faster than custom widgets)
        self.setup_table(main_frame)

        # Load data
        self.refresh_data()
        self._animate_entrance()
        self.after(500, self.background_scan)

    def _animate_entrance(self):
        """Micro-animation: Staggered reveal of dashboard cards"""
        # Collect all top-level cards in main_frame
        # Animation without alpha (since CTK doesn't support it directly)
        pass

    def background_scan(self):
        def _run():
            self.stats_manager.scan_outputs()
            self.after(0, self.refresh_data)
        import threading
        threading.Thread(target=_run, daemon=True).start()

    def setup_summary_card(self, parent):
        card = self.create_card(parent, "QUICK STATS")
        card.grid(row=1, column=0, sticky="ew", pady=10)
        
        summary_top_frame = ctk.CTkFrame(card, fg_color="transparent")
        summary_top_frame.pack(fill="x", padx=25, pady=(0, 20))
        
        self.summary_container = ctk.CTkFrame(summary_top_frame, fg_color="transparent")
        self.summary_container.pack(side="left", fill="x", expand=True)
        
        # Shortcuts Legend (Tactical Help)
        self.shortcuts_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.shortcuts_frame.pack(fill="x", padx=30, pady=(0, 8))
        shortcut_text = "⌨️  GLOBAL COMMANDS: [F] FOLLOWED UP  •  [I] IN PROCESS  •  [R] REJECTED  •  [U] UNKNOWN"
        ctk.CTkLabel(self.shortcuts_frame, text=shortcut_text, 
                     font=ctk.CTkFont(family="Inter", size=13, weight="bold"), 
                     text_color=self.colors["accent"]).pack(side="left")
        
        # Action Radar Container (Critical Actions)
        self.radar_container = ctk.CTkFrame(card, fg_color="transparent")
        self.radar_container.pack(fill="x", padx=25, pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(summary_top_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(btn_frame, text="🔄 Refresh", width=110, height=32,
                     fg_color=self.colors["accent"], text_color="white",
                     command=lambda: self.refresh_data(scan=True), 
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="top", pady=2)

        ctk.CTkButton(btn_frame, text="📈 Graph", width=110, height=32,
                     fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                     border_width=1, border_color=self.colors["border"],
                     command=self.toggle_graph, font=ctk.CTkFont(size=12)).pack(side="top", pady=2)

        ctk.CTkButton(btn_frame, text="📁 Open Folder", width=110, height=32,
                     fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                     border_width=1, border_color=self.colors["border"],
                     command=self.open_outputs, font=ctk.CTkFont(size=12)).pack(side="top", pady=2)

    def setup_controls_card(self, parent):
        card = self.create_card(parent, "FILTERS & CONTROLS")
        card.grid(row=4, column=0, sticky="ew", pady=10)
        
        controls_frame = ctk.CTkFrame(card, fg_color="transparent")
        controls_frame.pack(fill="x", padx=25, pady=(0, 20))
        
        # Date Range Filter
        date_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        date_container.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(date_container, text="Date Range", font=ctk.CTkFont(size=12), 
                     text_color=self.colors["text_muted"]).pack(anchor="w", pady=(0, 5))
        
        date_options = ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "This Year"]
        if CALENDAR_AVAILABLE:
            date_options.append("Custom Range...")
        
        self.date_menu = ctk.CTkOptionMenu(date_container, 
                         values=date_options,
                         variable=self.date_filter,
                         command=self.on_date_filter_change,
                         width=130, height=38,
                         fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                         button_color=self.colors["accent"])
        self.date_menu.pack()

        # Status Filter
        status_dropdown_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        status_dropdown_container.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(status_dropdown_container, text="Status", font=ctk.CTkFont(size=12), 
                     text_color=self.colors["text_muted"]).pack(anchor="w", pady=(0, 5))
        
        self.status_menu = ctk.CTkOptionMenu(status_dropdown_container,
                         values=["All", "In Process", "Followed Up", "Rejected", "Unknown"],
                         variable=self.status_filter,
                         command=lambda v: self.refresh_data(),
                         width=130, height=38,
                         fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                         button_color=self.colors["accent"])
        self.status_menu.pack()

        # Country Filter
        country_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        country_container.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(country_container, text="Country", font=ctk.CTkFont(size=12), 
                     text_color=self.colors["text_muted"]).pack(anchor="w", pady=(0, 5))
        
        self.country_menu = ctk.CTkOptionMenu(country_container,
                         values=self.available_countries,
                         variable=self.country_filter,
                         command=lambda v: self.refresh_data(),
                         width=130, height=38,
                         fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                         button_color=self.colors["accent"])
        self.country_menu.pack()
        
        # Search Box (Reduced width)
        search_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        search_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(search_container, text="Search Company", font=ctk.CTkFont(size=12), 
                     text_color=self.colors["text_muted"]).pack(anchor="w", pady=(0, 5))
        search_entry = ctk.CTkEntry(search_container, height=38, placeholder_text="Type to search...", 
                                    textvariable=self.search_query,
                                    fg_color=self.colors["input_bg"], border_width=1, 
                                    border_color=self.colors["border"])
        search_entry.pack(fill="x")
        self.search_query.trace_add("write", self.debounced_search)
        
        # Sort Dropdown
        sort_container = ctk.CTkFrame(controls_frame, fg_color="transparent")
        sort_container.pack(side="right")
        ctk.CTkLabel(sort_container, text="Sort By", font=ctk.CTkFont(size=12), 
                     text_color=self.colors["text_muted"]).pack(anchor="w", pady=(0, 5))
        ctk.CTkOptionMenu(sort_container, 
                         values=["Latest First", "Earliest First", "Status", "Company A-Z"],
                         variable=self.sort_order,
                         command=lambda v: self.refresh_data(),
                         width=130, height=38,
                         fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                         button_color=self.colors["accent"]).pack(side="left")

        # Add Record
        ctk.CTkButton(sort_container, text="➕ Add Record", width=110, height=38,
                     fg_color=self.colors["accent"], text_color="white",
                     command=self.open_add_record_dialog,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 0))

        # Export Button
        ctk.CTkButton(sort_container, text="📥 Export CSV", width=110, height=38,
                     fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                     border_width=1, border_color=self.colors["border"],
                     command=self.export_to_csv,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 0))

        # Clear Button
        ctk.CTkButton(sort_container, text="✕ Clear", width=80, height=38,
                     fg_color=self.colors["input_bg"], text_color="#EF4444",
                     hover_color=("#FEE2E2", "#450A0A"),
                     border_width=1, border_color=self.colors["border"],
                     command=self.clear_all_filters,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 0))

    def setup_table(self, parent):
        # Give the table a fixed, large height now that the whole page scrolls
        table_frame = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=12, 
                                   border_width=1, border_color=self.colors["border"],
                                   height=600)  # Large, usable height
        table_frame.grid(row=5, column=0, sticky="nsew", pady=10)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_propagate(False) # Force the height for grid layout

        # Create Treeview with custom styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Higher Contrast Table for better readability
        table_bg = "#252D3D" # Lighter slate blue
        table_fg = "#FFFFFF" # Pure white for max contrast
        header_bg = "#1A202C" # Deep dark for headers
        accent_color = "#6366F1" # Bright Indigo

        style.configure("Custom.Treeview",
                       background=table_bg,
                       foreground=table_fg,
                       fieldbackground=table_bg,
                       borderwidth=0,
                       rowheight=40,  
                       font=('Inter', 13))
        
        style.configure("Custom.Treeview.Heading",
                       background=header_bg,
                       foreground=self.colors["text_muted"],
                       borderwidth=0,
                       relief="flat",
                       font=('Inter', 11, 'bold'))

        # Header hover and separation
        style.map("Custom.Treeview.Heading",
                  background=[('active', "#252D3D")])

        # Selection styling
        style.map('Custom.Treeview', 
                 background=[('selected', accent_color)],
                 foreground=[('selected', '#FFFFFF')])

        # Scrollbar with dark styling
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical",
                                    fg_color="transparent",
                                    button_color=self.colors["border"],
                                    button_hover_color=self.colors["text_muted"])
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)

        # Treeview
        self.tree = ttk.Treeview(table_frame, 
                                columns=("id", "date", "company", "role_title", "country", "status", "age"),
                                show="headings",
                                style="Custom.Treeview",
                                yscrollcommand=scrollbar.set,
                                selectmode="browse")
        
        scrollbar.configure(command=self.tree.yview)
        
        # Define columns with precise alignment
        self.tree.heading("id", text="#", anchor="center")
        self.tree.heading("date", text="Date", anchor="w")
        self.tree.heading("company", text="Company", anchor="w")
        self.tree.heading("role_title", text="Role Title", anchor="w")
        self.tree.heading("country", text="Country", anchor="w")
        self.tree.heading("status", text="Status", anchor="w")
        self.tree.heading("age", text="Age", anchor="w")
        
        self.tree.column("id", width=50, anchor="center", minwidth=40)
        self.tree.column("date", width=110, anchor="w", minwidth=110)
        self.tree.column("company", width=300, anchor="w", minwidth=200)
        self.tree.column("role_title", width=220, anchor="w", minwidth=140)
        self.tree.column("country", width=160, anchor="w", minwidth=120)
        self.tree.column("status", width=160, anchor="w", minwidth=120)
        self.tree.column("age", width=130, anchor="w", minwidth=100)
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Context menu for status update
        self.tree.bind("<Double-Button-1>", self.on_row_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu) # Right click Windows
        
        # Keyboard Shortcuts for Rapid Entry (Bound to Tree for focus)
        self.tree.bind("<r>", lambda e: self.update_status_hotkey("Rejected"))
        self.tree.bind("<R>", lambda e: self.update_status_hotkey("Rejected"))
        self.tree.bind("<f>", lambda e: self.update_status_hotkey("Followed Up"))
        self.tree.bind("<F>", lambda e: self.update_status_hotkey("Followed Up"))
        self.tree.bind("<i>", lambda e: self.update_status_hotkey("In Process"))
        self.tree.bind("<I>", lambda e: self.update_status_hotkey("In Process"))
        self.tree.bind("<u>", lambda e: self.update_status_hotkey("Unknown"))
        self.tree.bind("<U>", lambda e: self.update_status_hotkey("Unknown"))

    def update_styling(self):
        """Update Treeview styling based on current theme"""
        mode = ctk.get_appearance_mode()
        style = ttk.Style()
        
        if mode == "Dark":
            table_bg = "#252D3D"
            table_fg = "#CBD5E0" # Softer "Middle Shade" light gray, less jarring than pure white
            header_bg = "#1A202C"
            odd_row = "#2D3748"
            status_muted = "#94A3B8"
        else:
            table_bg = "#FFFFFF"
            table_fg = "#1E293B"
            header_bg = "#F1F5F9"
            odd_row = "#F8FAFC"
            status_muted = "#64748B"

        accent_color = self.colors["accent"]

        style.configure("Custom.Treeview",
                       background=table_bg,
                       foreground=table_fg,
                       fieldbackground=table_bg,
                       borderwidth=0,
                       rowheight=50,  # Increased
                       font=('Inter', 16)) # Increased

        style.configure("Custom.Treeview.Heading",
                       background=header_bg,
                       foreground=status_muted,
                       borderwidth=0,
                       relief="flat",
                       font=('Inter', 16, 'bold'))

        style.map("Custom.Treeview.Heading",
                  background=[('active', odd_row)])

        style.map('Custom.Treeview', 
                 background=[('selected', accent_color)],
                 foreground=[('selected', '#FFFFFF')])
        
        # Update odd/even row tags
        self.tree.tag_configure("evenrow", background=table_bg)
        self.tree.tag_configure("oddrow", background=odd_row)
        
        # Brighter status colors for better contrast
        if mode == "Dark":
            self.tree.tag_configure("in_process", foreground="#93C5FD")
            self.tree.tag_configure("rejected", foreground="#FCA5A5")
            self.tree.tag_configure("followed_up", foreground="#6EE7B7")
            self.tree.tag_configure("unknown", foreground="#94A3B8")
        else:
            self.tree.tag_configure("in_process", foreground="#3B82F6")
            self.tree.tag_configure("rejected", foreground="#EF4444")
            self.tree.tag_configure("followed_up", foreground="#10B981")
            self.tree.tag_configure("unknown", foreground="#64748B")
        
        # Missing CV tag - subtle underline or color shift
        self.tree.tag_configure("missing_cv", foreground="#F59E0B") # Amber warning
        
        # Manual entry tag - Italics or subtle indicator
        self.tree.tag_configure("manual_entry", font=('Inter', 16, 'italic'))

    def show_context_menu(self, event):
        """Show right-click context menu for status updates"""
        # Select row under cursor
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            
            # Premium large font for the menu
            menu_font = ('Inter', 12)
            
            menu = tk.Menu(self, tearoff=0, bg=self.colors["card"][1] if ctk.get_appearance_mode() == "Dark" else "white", 
                          fg=self.colors["text"][1] if ctk.get_appearance_mode() == "Dark" else "black",
                          activebackground=self.colors["accent"], activeforeground="white", 
                          font=menu_font, borderwidth=0)
            
            menu.add_command(label="🔵 Mark In Process", command=lambda: self.update_status_hotkey("In Process"))
            menu.add_command(label="🟢 Mark Followed Up", command=lambda: self.update_status_hotkey("Followed Up"))
            menu.add_command(label="🔴 Mark Rejected", command=lambda: self.update_status_hotkey("Rejected"))
            menu.add_command(label="⚪ Mark Unknown", command=lambda: self.update_status_hotkey("Unknown"))
            menu.add_separator()
            menu.add_command(label="📝 Edit Details...", command=lambda: self.on_row_double_click(None))
            menu.add_command(label="📁 Open Application Folder", command=lambda: self.open_app_folder(row_id))
            menu.add_separator()
            menu.add_command(label="🗑️ Delete Record", command=lambda: self.delete_record(row_id))
            
            menu.post(event.x_root, event.y_root)

    def delete_record(self, app_id):
        """Delete a record after confirmation"""
        stats = self.stats_manager.get_stats()
        if app_id not in stats:
            return
        
        app = stats[app_id]
        company = app['company']
        date = app['date']
        
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Delete")
        dialog.geometry("420x280")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(main_frame, text="⚠️ Confirm Delete", 
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color="#EF4444").pack(pady=(0, 15))
        
        ctk.CTkLabel(main_frame, text=f"Are you sure you want to delete the application for:\n\n📁 {company}\n📅 {date}\n\nThis action cannot be undone.", 
                    font=ctk.CTkFont(size=13), 
                    text_color=self.colors["text"],
                    wraplength=340,
                    justify="center").pack(pady=10)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        def confirm_delete():
            if self.stats_manager.delete_application(app_id):
                self.refresh_data()
            dialog.destroy()
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                     border_width=1, border_color=self.colors["border"],
                     width=120, height=40).pack(side="left", padx=(0, 10))
                     
        ctk.CTkButton(btn_frame, text="Delete", command=confirm_delete, 
                     fg_color="#EF4444", hover_color="#DC2626",
                     width=120, height=40).pack(side="left")

    def open_app_folder(self, app_id):
        """Open the specific application folder with robust path detection"""
        stats = self.stats_manager.get_stats()
        if app_id in stats:
            app = stats[app_id]
            # Use absolute path and normalized folder names
            outputs_root = os.path.abspath(os.path.join(current_dir, "..", "outputs"))
            date_folder = app['date']
            company_folder = app.get('folder_name', app.get('company', '').replace(' ', '_'))
            
            folder_path = os.path.join(outputs_root, date_folder, company_folder)
            
            if os.path.exists(folder_path):
                self._open_path(folder_path)
            else:
                # Fallback: try searching for the folder if names were modified
                print(f"Path not found: {folder_path}. Trying fallback search...")
                self._open_path(outputs_root) # At least open the root outputs

    def _open_path(self, path):
        if os.name == "nt":
            os.startfile(path)
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
            return
        subprocess.Popen(["xdg-open", path])

    def toggle_radar_filter(self, key):
        """Toggle action radar filtering"""
        if self.radar_filter.get() == key:
            self.radar_filter.set("All")
        else:
            self.radar_filter.set(key)
        self.refresh_data()


    def lighten_color(self, hex_color):
        """Helper to create hover colors"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Lighten by 20%
        new_rgb = tuple(min(255, int(c + (255 - c) * 0.2)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

    def on_date_filter_change(self, value):
        if value == "Custom Range...":
            self.open_custom_date_picker()
        else:
            self.custom_date_from = None
            self.custom_date_to = None
            self.refresh_data()

    def clear_all_filters(self):
        """Reset all filter states to default"""
        self.search_query.set("")
        self.date_filter.set("All Time")
        self.status_filter.set("All")
        self.country_filter.set("All")
        self.radar_filter.set("All")
        self.sort_order.set("Latest First")
        self.custom_date_from = None
        self.custom_date_to = None
        self.refresh_data()

    def open_custom_date_picker(self):
        """Open a dialog with calendar widgets for custom date range"""
        if not CALENDAR_AVAILABLE:
            return
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Select Custom Date Range")
        dialog.geometry("450x280")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (280 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="Select Date Range", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 20))
        
        # Date pickers frame
        dates_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dates_frame.pack(fill="x", pady=10)
        
        # From date
        from_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        from_frame.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(from_frame, text="From Date:", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 5))
        from_cal = DateEntry(from_frame, width=18, background='#4F46E5', 
                            foreground='white', borderwidth=2, font=('Inter', 11),
                            date_pattern='dd/mm/yyyy')
        from_cal.pack()
        
        # To date
        to_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        to_frame.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(to_frame, text="To Date:", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 5))
        to_cal = DateEntry(to_frame, width=18, background='#4F46E5', 
                          foreground='white', borderwidth=2, font=('Inter', 11),
                          date_pattern='dd/mm/yyyy')
        to_cal.pack()
        to_cal.set_date(datetime.now())  # Default to today
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def apply_custom_range():
            self.custom_date_from = from_cal.get_date()
            self.custom_date_to = to_cal.get_date()
            
            # Update the dropdown display
            range_text = f"{self.custom_date_from.strftime('%d/%m/%y')} - {self.custom_date_to.strftime('%d/%m/%y')}"
            self.date_filter.set(range_text)
            
            dialog.destroy()
            self.refresh_data()
        
        def cancel():
            self.date_filter.set("All Time")
            self.custom_date_from = None
            self.custom_date_to = None
            dialog.destroy()
        
        ctk.CTkButton(btn_frame, text="Apply", command=apply_custom_range,
                     fg_color=self.colors["accent"], width=100, height=35).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=cancel,
                     fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                     border_width=1, border_color=self.colors["border"],
                     width=100, height=35).pack(side="left", padx=5)

    def create_card(self, parent, label):
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=16, 
                            border_width=1, border_color=self.colors["border"])
        if label:
            header = ctk.CTkFrame(frame, fg_color="transparent")
            header.pack(fill="x", padx=30, pady=(25, 10))
            ctk.CTkLabel(header, text=label.upper(), 
                         font=ctk.CTkFont(family="Inter", size=13, weight="bold"), 
                         text_color=self.colors["text_muted"]).pack(side="left")
        return frame

    def debounced_search(self, *args):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.refresh_data)

    def refresh_data(self, scan=False):
        if scan:
            self.stats_manager.scan_outputs()
        
        # Sync Style with App Theme
        self.update_styling()

        stats = self.stats_manager.get_stats()
        
        # 0. Update Country List
        unique_countries = sorted(list(set(d.get('country', 'Unknown') for d in stats.values())))
        # Standardize "Unknown" to be at the end
        has_unknown = "Unknown" in unique_countries
        filtered_countries = [c for c in unique_countries if c != "Unknown"]
        self.available_countries = ["All"] + filtered_countries + (["Unknown"] if has_unknown else [])
        
        # Update dropdown values
        self.country_menu.configure(values=self.available_countries)
        if self.country_filter.get() not in self.available_countries:
            self.country_filter.set("All")

        
        # 1. Update Top Summary (Total + Status Pills)
        for widget in self.summary_container.winfo_children(): 
            widget.destroy()
        
        # Apply current filters
        self.filtered_data = self.apply_filters(stats)
        filtered_stats = self.filtered_data
        filtered_count = len(filtered_stats)
        
        ctk.CTkLabel(self.summary_container, text=f"Total: {filtered_count}", 
                    font=ctk.CTkFont(size=26, weight="bold"), 
                    text_color=self.colors["text"]).pack(side="left", padx=(0, 25))
        
        status_counts = {}
        for _, data in filtered_stats:
            s = data['status']
            status_counts[s] = status_counts.get(s, 0) + 1
        
        status_colors = {"In Process": "#3B82F6", "Rejected": "#EF4444", 
                        "Followed Up": "#10B981", "Unknown": "#64748B"}
        
        for status in ["In Process", "Followed Up", "Rejected", "Unknown"]:
            target_count = status_counts.get(status, 0)
            
            pill = ctk.CTkLabel(self.summary_container, 
                               text=f"{status.upper()}: 0", # Initial 0 for animation
                               fg_color=status_colors[status],
                               text_color="white",
                               corner_radius=15, height=32,
                               padx=12,
                               font=ctk.CTkFont(size=14, weight="bold"))
            pill.pack(side="left", padx=5)
            # Animate the count
            self._animate_number(pill, 0, target_count, status.upper())

        # 2. Update Graph
        if self.graph_visible:
            self.render_graph(filtered_stats)

        # 3. Update Action Radar Cards
        filtered_dict = dict(filtered_stats)
        self.render_action_radar(filtered_dict)

        # 3. Update Intelligence (Funnel & Countries)
        self.render_intelligence(filtered_dict)

        # 4. Update table
        self.update_table(filtered_stats)

    def render_action_radar(self, stats):
        for widget in self.radar_container.winfo_children(): widget.destroy()
        
        now = datetime.now()
        stale = [] # > 14 days, no response
        stalled = [] # > 30 days
        recent = [] # last 48h
        
        for aid, data in stats.items():
            try:
                dt = self.parse_date(data['date'])
                diff = (now - dt).days
                if data['status'] == "Unknown" and 14 <= diff < 30: stale.append(aid)
                if data['status'] == "Unknown" and diff >= 30: stalled.append(aid)
                if diff <= 2: recent.append(aid)
            except: pass

        radar_items = [
            ("⚡ RECENT (48H)", len(recent), "#8B5CF6", "Recent"),
            ("⏳ STALE (>14D)", len(stale), "#F59E0B", "Stale"),
            ("🛑 STALLED (>30D)", len(stalled), "#64748B", "Stalled")
        ]

        for label, count, color, filter_key in radar_items:
            is_active = self.radar_filter.get() == filter_key
            card = ctk.CTkButton(self.radar_container, text="", 
                               fg_color=self.colors["card"],
                               hover_color=self.colors["bg"], 
                               corner_radius=16, height=75, width=220,
                               command=lambda k=filter_key: self.toggle_radar_filter(k),
                               border_width=1, 
                               border_color=color if is_active else self.colors["border"])
            card.pack(side="left", padx=(0, 20))
            
            # Hover Lift Effect
            card.bind("<Enter>", lambda e, c=card, col=color, active=is_active: self._on_card_hover(c, col, active), add="+")
            card.bind("<Leave>", lambda e, c=card, col=color, active=is_active: self._on_card_leave(c, col, active), add="+")
            
            ctk.CTkLabel(card, text=label, 
                         font=ctk.CTkFont(family="Inter", size=15, weight="bold"), 
                         text_color=color if is_active else self.colors["text_muted"]).place(x=18, y=14)
            
            ctk.CTkLabel(card, text=str(count), 
                         font=ctk.CTkFont(family="Inter", size=34, weight="bold"), 
                         text_color=self.colors["text"]).place(x=18, y=32)
            
            if is_active: 
                ctk.CTkLabel(card, text="●", text_color=color, 
                            font=ctk.CTkFont(size=12)).place(relx=0.88, y=18)

    def _on_card_hover(self, widget, color, is_active):
        """Card Hover Lift Animation (1-2px upward translation simulation via border/pady)"""
        if not is_active:
            widget.configure(border_color=color, border_width=2)
        # We can't easily translate in pack, so we emphasize via border contrast

    def _on_card_leave(self, widget, color, is_active):
        if not is_active:
            widget.configure(border_color=self.colors["border"], border_width=1)

    def _animate_number(self, widget, current, target, prefix):
        if not widget.winfo_exists(): return
        if current < target:
            step = max(1, (target - current) // 5)
            next_val = min(target, current + step)
            widget.configure(text=f"{prefix}: {next_val}")
            self.after(30, lambda: self._animate_number(widget, next_val, target, prefix))
        else:
            widget.configure(text=f"{prefix}: {target}")

    def setup_graph_panel(self, parent):
        self.graph_visible = False
        self.graph_card = self.create_card(parent, "APPLICATION ACTIVITY OVER TIME")
        self.graph_card.grid(row=2, column=0, sticky="ew", pady=10)
        self.graph_card.grid_remove() # Start hidden
        
        self.graph_body = ctk.CTkFrame(self.graph_card, fg_color="transparent")
        self.graph_body.pack(fill="both", expand=True, padx=25, pady=(0, 10))
        
        # Horizontal Scrollbar for Canvas
        self.graph_hscroll = ctk.CTkScrollbar(self.graph_body, orientation="horizontal",
                                            height=12,
                                            fg_color="transparent",
                                            button_color=self.colors["border"],
                                            button_hover_color=self.colors["accent"])
        self.graph_hscroll.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

        # Canvas for the graph
        self.graph_canvas = tk.Canvas(self.graph_body, height=240, highlightthickness=0,
                                     xscrollcommand=self.graph_hscroll.set)
        self.graph_canvas.pack(fill="x", expand=True, pady=(10, 0))
        
        self.graph_hscroll.configure(command=self.graph_canvas.xview)
        
        # Add resize binding to redraw graph
        self.graph_canvas.bind("<Configure>", lambda e: self.render_graph(self.apply_filters(self.stats_manager.get_stats())))

    def filter_by_graph_date(self, selected_date):
        self.custom_date_from = selected_date
        self.custom_date_to = selected_date
        
        # Update dropdown to show we are filtering
        range_text = f"Date: {selected_date.strftime('%d/%m/%y')}"
        self.date_filter.set(range_text)
        
        # Add a visual "Clear" or "Reset" indicator or just refresh
        self.refresh_data()
        
        # Scroll to table if possible (optional)
        self.tree.focus_set()

    def toggle_graph(self):
        self.graph_visible = not self.graph_visible
        if self.graph_visible:
            self.graph_card.grid()
            self.refresh_data()
        else:
            self.graph_card.grid_remove()

    def show_graph_tooltip(self, x, y, count):
        self.hide_graph_tooltip()
        
        mode = ctk.get_appearance_mode()
        bg = "#1F2937" if mode == "Dark" else "#FFFFFF"
        fg = "#FFFFFF" if mode == "Dark" else "#1F2937"
        border = "#6366F1"
        
        txt = f"{count} Applications"
        
        # Measure text (vague but enough for standard padding)
        tw = len(txt) * 9 
        th = 20
        bw, bh = tw + 20, th + 15
        
        # Position comfortably above
        bx, by = x - bw/2, y - bh - 15
        if bx < 5: bx = 5
        
        # Create tooltip with "fade-in" feel (instant start, but we add a small delay)
        self.graph_canvas.create_rectangle(bx, by, bx+bw, by+bh, fill=bg, outline=border, width=2, tags="tooltip")
        self.graph_canvas.create_text(bx+bw/2, by+bh/2, text=txt, fill=fg, font=('Inter', 12, 'bold'), tags="tooltip")

    def hide_graph_tooltip(self):
        self.graph_canvas.delete("tooltip")

    def render_graph(self, filtered_items):
        if not self.graph_visible:
            return
            
        self.graph_canvas.delete("all")
        
        # Sync color palette
        mode = ctk.get_appearance_mode()
        canvas_bg = "#161D29" if mode == "Dark" else "#FFFFFF"
        grid_color = "#1F2937" if mode == "Dark" else "#F3F4F6"
        line_color = "#6366F1"
        point_color = "#818CF8" if mode == "Dark" else "#4F46E5"
        text_color = "#9CA3AF" if mode == "Dark" else "#6B7280"
            
        self.graph_canvas.configure(bg=canvas_bg)
        
        # Data Processing from Filtered Items
        by_date = {}
        for _, data in filtered_items:
            dt = self.parse_date(data['date'])
            if dt == datetime.min: continue
            date_key = dt.date()
            by_date[date_key] = by_date.get(date_key, 0) + 1
            
        # Determine Date Boundaries from Filter Settings
        today = datetime.now().date()
        date_range = self.date_filter.get()
        
        if self.custom_date_from and self.custom_date_to:
            min_date = self.custom_date_from
            max_date = self.custom_date_to
        elif date_range == "Last 7 Days":
            min_date, max_date = today - timedelta(days=6), today
        elif date_range == "Last 30 Days":
            min_date, max_date = today - timedelta(days=29), today
        elif date_range == "Last 90 Days":
            min_date, max_date = today - timedelta(days=89), today
        elif date_range == "This Year":
            min_date, max_date = datetime(today.year, 1, 1).date(), today
        elif by_date:
            # All Time or Fallback
            min_date, max_date = min(by_date.keys()), max(by_date.keys())
            if (max_date - min_date).days < 7: min_date = max_date - timedelta(days=7)
        else:
            # Complete Empty Fallback
            min_date, max_date = today - timedelta(days=30), today

        plot_data = []
        curr = min_date
        while curr <= max_date:
            plot_data.append((curr, by_date.get(curr, 0)))
            curr += timedelta(days=1)
            
        # Scrolling Logic: Fixed density for long ranges
        px_per_day = 45 # Enough room for labels and hover
        total_days = len(plot_data)
        viewport_w = self.graph_canvas.winfo_width()
        content_w = max(viewport_w, total_days * px_per_day)
        
        # Update Scroll Region
        h = self.graph_canvas.winfo_height()
        self.graph_canvas.configure(scrollregion=(0, 0, content_w, h))
        
        if viewport_w < 10: return 
        
        padding_x = 60
        padding_y = 60
        plot_w = content_w - (padding_x * 2)
        plot_h = h - (padding_y * 2)
        
        max_apps = max(by_date.values()) if by_date else 0
        y_max = max(5, max_apps + 1)
        
        # Draw Background Grid
        self.graph_canvas.create_line(padding_x, h - padding_y, content_w - padding_x, h - padding_y, fill=grid_color)
        for i in range(0, y_max + 1, max(1, y_max // 4)):
            y_pos = (h - padding_y) - (i / y_max * plot_h)
            self.graph_canvas.create_line(padding_x, y_pos, content_w - padding_x, y_pos, fill=grid_color, dash=(2, 2))
            self.graph_canvas.create_text(padding_x - 15, y_pos, text=str(i), fill=text_color, font=('Inter', 12), anchor="e")
            
        # Calculate Points
        x_step = plot_w / (len(plot_data) - 1) if len(plot_data) > 1 else plot_w
        points = []
        
        for i, (date, count) in enumerate(plot_data):
            x = padding_x + (i * x_step)
            y = (h - padding_y) - (count / y_max * plot_h)
            points.append((x, y))
            
            # X-axis Labels (Skip based on density)
            skip = max(1, int(total_days / (content_w / 80)))
            if i % skip == 0 or i == len(plot_data) - 1:
                label = date.strftime("%d %b")
                self.graph_canvas.create_text(x, h - padding_y + 15, text=label, 
                                            fill=text_color, font=('Inter', 11), angle=45, anchor="nw")

        # Draw line and Polygon Shadow
        if len(points) > 1:
            poly_points = [padding_x, h - padding_y]
            for i in range(len(points) - 1):
                self.graph_canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 
                                            fill=line_color, width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND)
                poly_points.extend([points[i][0], points[i][1]])
            
            poly_points.extend([points[-1][0], points[-1][1]])
            poly_points.extend([points[-1][0], h - padding_y])
            
            fill_hex = "#1E2235" if mode == "Dark" else "#EEF2FF"
            poly_id = self.graph_canvas.create_polygon(poly_points, fill=fill_hex, outline="")
            self.graph_canvas.tag_lower(poly_id)

        # Draw nodes
        for i, (date, count) in enumerate(plot_data):
            x, y = points[i]
            r = 6
            node = self.graph_canvas.create_oval(x-r, y-r, x+r, y+r, fill=point_color, outline=canvas_bg, width=2)
            
            # Bindings
            self.graph_canvas.tag_bind(node, "<Enter>", lambda e, nx=x, ny=y, nc=count: [self.show_graph_tooltip(nx, ny, nc), self.graph_canvas.configure(cursor="hand2")])
            self.graph_canvas.tag_bind(node, "<Leave>", lambda e: [self.hide_graph_tooltip(), self.graph_canvas.configure(cursor="")])
            self.graph_canvas.tag_bind(node, "<Button-1>", lambda e, d=date: self.filter_by_graph_date(d))
            
        # Floating Summary (Static on view if we could, but let's just put it at the very end of content)
        total_apps = sum(by_date.values())
        avg_apps = total_apps / len(plot_data) if plot_data else 0
        self.graph_canvas.create_text(content_w - padding_x - 10, padding_y - 25, 
                                    text=f"RANGE AVG: {avg_apps:.1f}/day | SECTION TOTAL: {total_apps}", 
                                    fill=text_color, font=('Inter', 13, 'bold'), anchor="ne")

    def setup_intelligence_panel(self, parent):
        self.intel_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.intel_frame.grid(row=3, column=0, sticky="ew", pady=10)
        self.intel_frame.grid_columnconfigure((0,1), weight=1)

        # Funnel
        self.funnel_card = self.create_card(self.intel_frame, "CONVERSION FUNNEL")
        self.funnel_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.funnel_body = ctk.CTkFrame(self.funnel_card, fg_color="transparent")
        self.funnel_body.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Market
        self.market_card = self.create_card(self.intel_frame, "MARKET STRENGTH (TOP COUNTRIES)")
        self.market_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.market_body = ctk.CTkFrame(self.market_card, fg_color="transparent")
        self.market_body.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def render_intelligence(self, stats):
        # 1. Pipeline Funnel
        for w in self.funnel_body.winfo_children(): w.destroy()
        counts = {"Applied": len(stats), "Interview": 0, "Rejected": 0}
        for d in stats.values():
            if d['status'] == "In Process": counts["Interview"] += 1
            if d['status'] == "Rejected": counts["Rejected"] += 1
        
        steps = [
            ("APPLIED", counts["Applied"], self.colors["accent"]),
            ("INTERVIEW", counts["Interview"], "#3B82F6"),
            ("REJECTED", counts["Rejected"], "#EF4444")
        ]
        
        max_val = max(counts.values()) or 1
        for label, val, color in steps:
            row = ctk.CTkFrame(self.funnel_body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14, weight="bold"), width=90, anchor="w").pack(side="left")
            
            bar_frame = ctk.CTkFrame(row, fg_color=self.colors["input_bg"], height=8, corner_radius=4)
            bar_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            progress = (val / max_val)
            ctk.CTkFrame(bar_frame, fg_color=color, height=8, width=max(1, int(200 * progress)), corner_radius=4).pack(side="left")
            ctk.CTkLabel(row, text=str(val), font=ctk.CTkFont(size=14, weight="bold"), width=30).pack(side="right")

        # 2. Top Countries
        for w in self.market_body.winfo_children(): w.destroy()
        countries = {}
        for d in stats.values():
            c = d.get('country', 'Unknown')
            countries[c] = countries.get(c, 0) + 1
        
        top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:4]
        for name, val in top_countries:
            row = ctk.CTkFrame(self.market_body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=13), width=100, anchor="w").pack(side="left")
            
            bar_bg = ctk.CTkFrame(row, fg_color=self.colors["input_bg"], height=12, corner_radius=6)
            bar_bg.pack(side="left", fill="x", expand=True, padx=10)
            
            share = (val / counts["Applied"]) if counts["Applied"] > 0 else 0
            ctk.CTkFrame(bar_bg, fg_color=self.colors["accent"], height=12, width=max(1, int(150 * share)), corner_radius=6).pack(side="left")
            ctk.CTkLabel(row, text=f"{val}", font=ctk.CTkFont(size=12, weight="bold"), width=30).pack(side="right")

    def apply_filters(self, stats):
        """Apply date range, search, and sort filters"""
        items = list(stats.items())
        
        # 1. Action Radar Filter (NEW)
        radar_key = self.radar_filter.get()
        if radar_key != "All":
            now = datetime.now()
            filtered = []
            for aid, data in items:
                try:
                    dt = self.parse_date(data['date'])
                    diff = (now - dt).days
                    if radar_key == "Stale" and data['status'] == "Unknown" and 14 <= diff < 30: 
                        filtered.append((aid, data))
                    elif radar_key == "Stalled" and data['status'] == "Unknown" and diff >= 30: 
                        filtered.append((aid, data))
                    elif radar_key == "Recent" and diff <= 2: 
                        filtered.append((aid, data))
                except: pass
            items = filtered

        # 2. Date filter
        if self.custom_date_from and self.custom_date_to:
            # Custom date range
            items = [(aid, data) for aid, data in items 
                    if self.custom_date_from <= self.parse_date(data['date']).date() <= self.custom_date_to]
        else:
            # Preset date ranges
            date_range = self.date_filter.get()
            if date_range != "All Time" and not date_range.startswith("Custom"):
                cutoff_date = None
                today = datetime.now()
                
                if date_range == "Last 7 Days":
                    cutoff_date = today - timedelta(days=7)
                elif date_range == "Last 30 Days":
                    cutoff_date = today - timedelta(days=30)
                elif date_range == "Last 90 Days":
                    cutoff_date = today - timedelta(days=90)
                elif date_range == "This Year":
                    cutoff_date = datetime(today.year, 1, 1)
                
                if cutoff_date:
                    items = [(aid, data) for aid, data in items 
                            if self.parse_date(data['date']) >= cutoff_date]
        
        # Search filter
        query = self.search_query.get().lower()
        if query:
            items = [(aid, data) for aid, data in items 
                    if query in data.get('company', '').lower() or query in data.get('country', '').lower() or query in data.get('role_title', '').lower()]
        
        # Status filter (NEW)
        status_filter = self.status_filter.get()
        if status_filter != "All":
            items = [(aid, data) for aid, data in items if data['status'] == status_filter]
        
        # Country filter (NEW)
        country_filter = self.country_filter.get()
        if country_filter != "All":
            items = [(aid, data) for aid, data in items if data.get('country', 'Unknown') == country_filter]
        
        
        # Sort
        sort_by = self.sort_order.get()
        if sort_by == "Latest First":
            # Sort by application date only.
            # Do not use last_updated as a tiebreaker because edits would reorder rows.
            items.sort(key=lambda x: self.parse_date(x[1]['date']), reverse=True)
        elif sort_by == "Earliest First":
            items.sort(key=lambda x: self.parse_date(x[1]['date']))
        elif sort_by == "Status":
            items.sort(key=lambda x: x[1]['status'])
        elif sort_by == "Company A-Z":
            items.sort(key=lambda x: x[1]['company'].lower())
        
        return items

    def parse_timestamp(self, timestamp_str):
        """Parse the last_updated timestamp"""
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            return datetime.min

    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%d-%m-%y")
        except:
            return datetime.min

    def update_table(self, items):
        """Update treeview - MUCH faster than custom widgets"""
        # Preserve scroll position and selection so edits don't jump the user's view.
        try:
            selected = self.tree.selection()
            selected_iid = selected[0] if selected else None
            yview = self.tree.yview()
            yview_top = yview[0] if yview else 0.0
        except:
            selected_iid = None
            yview_top = 0.0

        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        now = datetime.now()
        
        # Insert new data
        for i, (app_id, app) in enumerate(items):
            # Base tag for zebra striping
            tags = ["evenrow" if i % 2 == 0 else "oddrow"]
            
            # Status tag
            status = app['status']
            tags.append(status.lower().replace(" ", "_"))
            
            # Found CV tag
            if not app.get('cv_found', True):
                tags.append("missing_cv")
            
            # Manual record tag
            if app.get('manual'):
                tags.append("manual_entry")
            
            # Calculate Age
            try:
                dt = self.parse_date(app['date'])
                diff = (now - dt).days
                if diff == 0: age_text = "Today"
                elif diff == 1: age_text = "Yesterday"
                else: age_text = f"{diff} days ago"
            except:
                age_text = "-"

            self.tree.insert("", "end", iid=app_id, 
                           values=(i + 1, app.get('date', ''), app.get('company', ''), app.get('role_title', ''), app.get('country', ''), app.get('status', ''), age_text),
                           tags=tuple(tags))

        # Restore selection and scroll position
        try:
            if selected_iid and self.tree.exists(selected_iid):
                self.tree.selection_set(selected_iid)
                self.tree.focus(selected_iid)
            self.tree.yview_moveto(yview_top)
        except:
            pass

    def update_status_hotkey(self, status):
        """Update status using keyboard shortcut"""
        selected = self.tree.selection()
        if not selected:
            return
        
        for app_id in selected:
            if self.stats_manager.update_field(app_id, "status", status):
                # We don't want to refresh the whole data (expensive)
                # Just update the specific row in tree and re-render summary
                self.tree.set(app_id, "status", status)
                # Apply new tag
                tags = list(self.tree.item(app_id, "tags"))
                # Remove old status tag if exists
                for t in ["unknown", "in_process", "rejected", "followed_up"]:
                    if t in tags: tags.remove(t)
                tags.append(status.lower().replace(" ", "_"))
                self.tree.item(app_id, tags=tuple(tags))
        
        # Update summary cards after a short delay
        self.after(500, self.refresh_data)

    def open_add_record_dialog(self):
        """Open a dialog to manually add a new record"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Application Record")
        dialog.geometry("450x580")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (580 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        ctk.CTkLabel(main_frame, text="Manual Entry", 
                    font=ctk.CTkFont(family="Inter", size=24, weight="bold")).pack(pady=(0, 25))
        
        # Company Name
        ctk.CTkLabel(main_frame, text="Company Name:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 5))
        company_entry = ctk.CTkEntry(main_frame, height=45, placeholder_text="e.g. OpenAI",
                                    fg_color=self.colors["input_bg"], border_color=self.colors["border"])
        company_entry.pack(fill="x")
        
        # Country
        ctk.CTkLabel(main_frame, text="Country:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        country_entry = ctk.CTkEntry(main_frame, height=45, placeholder_text="e.g. USA",
                                    fg_color=self.colors["input_bg"], border_color=self.colors["border"])
        country_entry.insert(0, "Denmark") # Default to Denmark or common country
        country_entry.pack(fill="x")

        ctk.CTkLabel(main_frame, text="Role Title (Optional):", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        role_title_entry = ctk.CTkEntry(main_frame, height=45, placeholder_text="e.g. Data Analyst",
                                       fg_color=self.colors["input_bg"], border_color=self.colors["border"])
        role_title_entry.pack(fill="x")
        
        # Date
        ctk.CTkLabel(main_frame, text="Date Applied:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x")
        
        if CALENDAR_AVAILABLE:
            date_cal = DateEntry(date_frame, width=28, background='#6366F1', 
                                foreground='white', borderwidth=2, font=('Inter', 12),
                                date_pattern='dd-mm-yy')
            date_cal.pack(pady=5, side="left")
        else:
            date_entry = ctk.CTkEntry(date_frame, height=45, placeholder_text="dd-mm-yy",
                                    fg_color=self.colors["input_bg"], border_color=self.colors["border"])
            date_entry.insert(0, datetime.now().strftime("%d-%m-%y"))
            date_entry.pack(fill="x")
            
        # Status
        ctk.CTkLabel(main_frame, text="Current Status:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        status_var = ctk.StringVar(value="Unknown")
        status_menu = ctk.CTkOptionMenu(main_frame, values=["In Process", "Followed Up", "Rejected", "Unknown"],
                                       variable=status_var, height=45,
                                       fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                                       button_color=self.colors["accent"])
        status_menu.pack(fill="x")
        
        def save_record():
            company = company_entry.get().strip()
            country = country_entry.get().strip() or "Unknown"
            role_title = role_title_entry.get().strip()
            if not company:
                company_entry.configure(border_color="#EF4444")
                return
            
            if CALENDAR_AVAILABLE:
                date_str = date_cal.get_date().strftime("%d-%m-%y")
            else:
                date_str = date_entry.get().strip()
            
            status = status_var.get()
            
            # Logic to save to stats_manager
            self.stats_manager.add_application(date_str, company, country, status, manual=True, role_title=role_title)
            dialog.destroy()
            self.refresh_data()
            
        ctk.CTkButton(main_frame, text="✨ Save Record", command=save_record,
                     fg_color=self.colors["accent"], hover_color=self.lighten_color(self.colors["accent"]),
                     height=50, corner_radius=12,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(35, 10), fill="x")
        
        ctk.CTkButton(main_frame, text="Cancel", command=dialog.destroy,
                     fg_color="transparent", text_color=self.colors["text_muted"],
                     height=40).pack(fill="x")

    def export_to_csv(self):
        """Export the currently filtered data to a CSV file"""
        if not self.filtered_data:
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Applications",
            initialfile=f"applications_export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["ID", "Date", "Company", "Role Title", "Country", "Status", "Manual Entry"])
                
                # Data
                for i, (app_id, data) in enumerate(self.filtered_data):
                    writer.writerow([
                        i + 1,
                        data.get('date', ''),
                        data.get('company', ''),
                        data.get('role_title', ''),
                        data.get('country', ''),
                        data.get('status', ''),
                        "Yes" if data.get('manual') else "No"
                    ])
            
            # Subtle feedback (could be a toast, but using print/console for now)
            print(f"Exported {len(self.filtered_data)} records to {file_path}")
        except Exception as e:
            print(f"Export Error: {e}")

    def on_row_double_click(self, event):
        """Open a comprehensive editor dialog on double-click"""
        item = self.tree.selection()
        if not item:
            return
        
        app_id = item[0]
        values = self.tree.item(app_id)['values']
        current_date = values[1]
        current_company = values[2]
        current_role_title = values[3]
        current_country = values[4]
        current_status = values[5]
        
        # Create popup dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Application Details")
        dialog.geometry("420x560")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (400 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(main_frame, text="Update Application Details", 
                    font=ctk.CTkFont(family="Inter", size=18, weight="bold")).pack(pady=(0, 20))
        
        # Helper to create labeled inputs
        def create_input(label, current_val):
            ctk.CTkLabel(main_frame, text=label, font=ctk.CTkFont(size=12), 
                        text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 2))
            entry = ctk.CTkEntry(main_frame, width=340, height=35)
            entry.insert(0, str(current_val))
            entry.pack(pady=(0, 5))
            return entry

        company_entry = create_input("Company Name", current_company)

        role_title_entry = create_input("Role Title", current_role_title)
        
        # Date Input
        ctk.CTkLabel(main_frame, text="Date Applied", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 2))
        
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 5))
        
        if CALENDAR_AVAILABLE:
            # Parse current date for DateEntry
            try:
                current_dt = datetime.strptime(current_date, "%d-%m-%y")
                date_cal = DateEntry(date_frame, width=28, background='#6366F1', 
                                    foreground='white', borderwidth=2, font=('Inter', 12),
                                    date_pattern='dd-mm-yy')
                date_cal.set_date(current_dt)
                date_cal.pack(side="left")
            except:
                # Fallback to entry if date parsing fails
                date_entry = ctk.CTkEntry(date_frame, width=200, height=35)
                date_entry.insert(0, current_date)
                date_entry.pack(side="left")
                date_cal = None
        else:
            date_entry = ctk.CTkEntry(date_frame, width=200, height=35)
            date_entry.insert(0, current_date)
            date_entry.pack(side="left")
            date_cal = None
        
        # Country Dropdown
        ctk.CTkLabel(main_frame, text="Country", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 2))
        
        # Filter "All" from available countries and ensure current/Unknown are available
        country_options = [c for c in self.available_countries if c != "All"]
        if current_country not in country_options:
            country_options.append(current_country)
        if "Unknown" not in country_options:
            country_options.append("Unknown")
        country_options = sorted(list(set(country_options)))
            
        country_var = ctk.StringVar(value=current_country)
        ctk.CTkOptionMenu(main_frame, values=country_options,
                         variable=country_var, width=340, height=35,
                         fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                         button_color=self.colors["accent"]).pack(pady=(0, 5))
        
        # Status Dropdown
        ctk.CTkLabel(main_frame, text="Status", font=ctk.CTkFont(size=12), 
                    text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 2))
        status_var = ctk.StringVar(value=current_status)
        ctk.CTkOptionMenu(main_frame, values=["Unknown", "In Process", "Followed Up", "Rejected"],
                         variable=status_var, width=340, height=35,
                         fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                         button_color=self.colors["accent"]).pack(pady=(0, 20))
        
        def save():
            new_company = company_entry.get().strip()
            new_role_title = role_title_entry.get().strip()
            new_country = country_var.get()
            new_status = status_var.get()
            
            # Get new date
            if CALENDAR_AVAILABLE and date_cal:
                new_date = date_cal.get_date().strftime("%d-%m-%y")
            else:
                new_date = date_entry.get().strip()
            
            updated = False
            effective_app_id = app_id

            if new_company != current_company or new_date != current_date:
                ok, effective_app_id = self.stats_manager.rename_application(
                    app_id,
                    new_date,
                    new_company
                )
                if not ok:
                    messagebox.showerror(
                        "Rename Failed",
                        "Could not rename this record. Another application may already use the same date/company combination."
                    )
                    dialog.destroy()
                    return
                updated = True

            if new_role_title != current_role_title:
                self.stats_manager.update_field(effective_app_id, "role_title", new_role_title)
                updated = True
            if new_country != current_country:
                self.stats_manager.update_field(effective_app_id, "country", new_country)
                updated = True
            if new_status != current_status:
                self.stats_manager.update_field(effective_app_id, "status", new_status)
                updated = True
                
            if updated:
                self.refresh_data(scan=False)  # Don't trigger scan after manual edit
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color=self.colors["input_bg"], text_color=self.colors["text"],
                     border_width=1, border_color=self.colors["border"],
                     width=160, height=40).pack(side="left", padx=(0, 10))
                     
        ctk.CTkButton(btn_frame, text="OK", command=save,
                     fg_color=self.colors["accent"],
                     width=160, height=40).pack(side="left")

    def open_outputs(self):
        outputs_dir = os.path.join(current_dir, "..", "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        os.startfile(outputs_dir)

if __name__ == "__main__":
    class StandaloneApp(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("ApplyCraft Audit | Standalone Tracker")
            self.geometry("1200x900")
            self.audit_panel = ApplicationAuditPanel(self)
            self.audit_panel.pack(fill="both", expand=True)
            self.audit_panel.refresh_data()
            
    app = StandaloneApp()
    app.mainloop()
