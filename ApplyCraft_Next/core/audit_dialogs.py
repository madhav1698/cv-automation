import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class AuditDialogs:
    @staticmethod
    def open_add_record_dialog(parent, stats_manager, colors, refresh_callback, calendar_available):
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Add New Application Record")
        dialog.geometry("480x780")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (480 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (780 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=35, pady=25)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="✨ Add Manual Record", 
                    font=ctk.CTkFont(family="Inter", size=22, weight="bold")).pack(side="left")
        
        # Form Container for better grouping
        form_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_container.pack(fill="both", expand=True)
        
        def create_field(parent, label, placeholder=None, height=40, initial_val=None):
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
            entry = ctk.CTkEntry(parent, height=height, placeholder_text=placeholder,
                                fg_color=colors["input_bg"], border_color=colors["border"])
            entry.pack(fill="x", pady=(0, 8))
            if initial_val:
                entry.insert(0, initial_val)
            return entry

        company_entry = create_field(form_container, "Company Name", "e.g. OpenAI")
        role_title_entry = create_field(form_container, "Role Title (Optional)", "e.g. Software Engineer")
        
        # Multi-column for Country and Date
        row_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=(5, 5))
        
        country_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        country_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
        country_entry = create_field(country_col, "Country", initial_val="Denmark")
        
        date_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(date_col, text="Date Applied", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        
        if calendar_available:
            from tkcalendar import DateEntry
            # Enhanced DateEntry styling for better visibility and month flipping
            date_cal = DateEntry(date_col, width=15, 
                                background=colors["accent"], 
                                foreground='white', 
                                borderwidth=2, 
                                font=('Inter', 11),
                                date_pattern='dd-mm-yy',
                                selectbackground=colors["accent"],
                                normalbackground=colors["input_bg"][0],
                                headersbackground=colors["accent"],
                                headersforeground='white')
            date_cal.pack(fill="both", pady=(0, 8), ipady=8)
        else:
            date_entry = ctk.CTkEntry(date_col, height=40, placeholder_text="dd-mm-yy",
                                    fg_color=colors["input_bg"], border_color=colors["border"])
            date_entry.insert(0, datetime.now().strftime("%d-%m-%y"))
            date_entry.pack(fill="x", pady=(0, 8))
            
        # Status
        ctk.CTkLabel(form_container, text="Current Status", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        status_var = ctk.StringVar(value="In Process")
        status_menu = ctk.CTkOptionMenu(form_container, values=["In Process", "Followed Up", "Rejected", "Unknown"],
                                       variable=status_var, height=40,
                                       fg_color=colors["input_bg"], text_color=colors["text"],
                                       button_color=colors["accent"])
        status_menu.pack(fill="x", pady=(0, 15))

        # Notes
        ctk.CTkLabel(form_container, text="Notes", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        notes_text = ctk.CTkTextbox(form_container, height=80, fg_color=colors["input_bg"], border_color=colors["border"], border_width=1)
        notes_text.pack(fill="x", pady=(0, 15))
        
        def save_record():
            company = company_entry.get().strip()
            country = country_entry.get().strip() or "Unknown"
            role_title = role_title_entry.get().strip()
            
            if not company:
                company_entry.configure(border_color="#EF4444")
                return
            
            if calendar_available:
                date_str = date_cal.get_date().strftime("%d-%m-%y")
            else:
                date_str = date_entry.get().strip()
            
            status = status_var.get()
            notes = notes_text.get("1.0", "end-1c").strip()
            
            stats_manager.add_application(date_str, company, country, status, manual=True, role_title=role_title)
            # Save notes
            app_id = stats_manager._build_app_id(date_str, company)
            if notes:
                stats_manager.update_field(app_id, "notes", notes)
            dialog.destroy()
            refresh_callback()
            
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color="transparent", text_color=colors["text_muted"],
                     height=45, border_width=1, border_color=colors["border"]).pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(btn_frame, text="Add Record", command=save_record,
                     fg_color=colors["accent"], height=45, corner_radius=10,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", fill="x", expand=True)

    @staticmethod
    def open_edit_dialog(parent, app_id, stats_manager, colors, refresh_callback, calendar_available, available_countries, tree):
        values = tree.item(app_id)['values']
        current_date = values[1]
        current_company = values[2]
        current_role_title = values[3]
        current_country = values[4]
        current_status = values[5]
        
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Edit Application Details")
        dialog.geometry("480x750")
        dialog.transient(parent)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (480 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (750 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=35, pady=25)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="📝 Edit Application Details", 
                    font=ctk.CTkFont(family="Inter", size=20, weight="bold")).pack(side="left")
        
        form_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_container.pack(fill="both", expand=True)

        def create_field(parent, label, height=40, initial_val=None):
            ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                        text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
            entry = ctk.CTkEntry(parent, height=height,
                                fg_color=colors["input_bg"], border_color=colors["border"])
            entry.pack(fill="x", pady=(0, 8))
            if initial_val:
                entry.insert(0, str(initial_val))
            return entry

        company_entry = create_field(form_container, "Company Name", initial_val=current_company)
        role_title_entry = create_field(form_container, "Role Title", initial_val=current_role_title)
        
        # Row for Date and Country
        row_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=(5, 5))
        
        date_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(date_col, text="Date Applied", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        
        date_cal = None
        if calendar_available:
            from tkcalendar import DateEntry
            try:
                current_dt = datetime.strptime(current_date, "%d-%m-%y")
                date_cal = DateEntry(date_col, width=15, background=colors["accent"], 
                                    foreground='white', borderwidth=2, font=('Inter', 11),
                                    date_pattern='dd-mm-yy',
                                    selectbackground=colors["accent"],
                                    headersbackground=colors["accent"])
                date_cal.set_date(current_dt)
                date_cal.pack(fill="both", pady=(0, 8), ipady=8)
            except:
                date_entry = ctk.CTkEntry(date_col, height=40)
                date_entry.insert(0, current_date)
                date_entry.pack(fill="x", pady=(0, 8))
        else:
            date_entry = ctk.CTkEntry(date_col, height=40)
            date_entry.insert(0, current_date)
            date_entry.pack(fill="x", pady=(0, 8))
        
        country_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        country_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(country_col, text="Country", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        
        country_options = [c for c in available_countries if c != "All"]
        if current_country not in country_options:
            country_options.append(current_country)
        if "Unknown" not in country_options:
            country_options.append("Unknown")
        country_options = sorted(list(set(country_options)))
            
        country_var = ctk.StringVar(value=current_country)
        country_menu = ctk.CTkOptionMenu(country_col, values=country_options,
                         variable=country_var, height=40,
                         fg_color=colors["input_bg"], text_color=colors["text"],
                         button_color=colors["accent"])
        country_menu.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form_container, text="Status", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        status_var = ctk.StringVar(value=current_status)
        status_menu = ctk.CTkOptionMenu(form_container, values=["In Process", "Followed Up", "Rejected", "Unknown"],
                         variable=status_var, height=40,
                         fg_color=colors["input_bg"], text_color=colors["text"],
                         button_color=colors["accent"])
        status_menu.pack(fill="x", pady=(0, 15))

        # Notes
        full_data = stats_manager.get_stats().get(app_id, {})
        current_notes = full_data.get("notes", "")
        ctk.CTkLabel(form_container, text="Notes", font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(8, 2))
        notes_text = ctk.CTkTextbox(form_container, height=80, fg_color=colors["input_bg"], border_color=colors["border"], border_width=1)
        notes_text.pack(fill="x", pady=(0, 15))
        notes_text.insert("1.0", current_notes)
        
        def save():
            new_company = company_entry.get().strip()
            new_role_title = role_title_entry.get().strip()
            new_country = country_var.get()
            new_status = status_var.get()
            
            if calendar_available and date_cal:
                new_date = date_cal.get_date().strftime("%d-%m-%y")
            else:
                new_date = date_entry.get().strip()
            
            updated = False
            effective_app_id = app_id

            if new_company != current_company or new_date != current_date:
                ok, effective_app_id = stats_manager.rename_application(app_id, new_date, new_company)
                if not ok:
                    messagebox.showerror("Rename Failed", "Could not rename record.")
                    dialog.destroy()
                    return
                updated = True

            if new_role_title != current_role_title:
                stats_manager.update_field(effective_app_id, "role_title", new_role_title)
                updated = True
            if new_country != current_country:
                stats_manager.update_field(effective_app_id, "country", new_country)
                updated = True
            if new_status != current_status:
                stats_manager.update_field(effective_app_id, "status", new_status)
                updated = True

            new_notes = notes_text.get("1.0", "end-1c").strip()
            if new_notes != current_notes:
                stats_manager.update_field(effective_app_id, "notes", new_notes)
                updated = True
                
            if updated:
                refresh_callback(scan=False)
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color="transparent", text_color=colors["text_muted"],
                     height=45, border_width=1, border_color=colors["border"]).pack(side="left", fill="x", expand=True, padx=(0, 10))
                     
        ctk.CTkButton(btn_frame, text="Update Record", command=save,
                     fg_color=colors["accent"], height=45, corner_radius=10,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", fill="x", expand=True)
