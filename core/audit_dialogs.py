import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class AuditDialogs:
    @staticmethod
    def open_add_record_dialog(parent, stats_manager, colors, refresh_callback, calendar_available):
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Add New Application Record")
        dialog.geometry("450x580")
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (580 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)
        
        ctk.CTkLabel(main_frame, text="Manual Entry", 
                    font=ctk.CTkFont(family="Inter", size=24, weight="bold")).pack(pady=(0, 25))
        
        # Company Name
        ctk.CTkLabel(main_frame, text="Company Name:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(10, 5))
        company_entry = ctk.CTkEntry(main_frame, height=45, placeholder_text="e.g. OpenAI",
                                    fg_color=colors["input_bg"], border_color=colors["border"])
        company_entry.pack(fill="x")
        
        # Country
        ctk.CTkLabel(main_frame, text="Country:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        country_entry = ctk.CTkEntry(main_frame, height=45, placeholder_text="e.g. USA",
                                    fg_color=colors["input_bg"], border_color=colors["border"])
        country_entry.insert(0, "Denmark")
        country_entry.pack(fill="x")

        ctk.CTkLabel(main_frame, text="Role Title (Optional):", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        role_title_entry = ctk.CTkEntry(main_frame, height=45, placeholder_text="e.g. Data Analyst",
                                       fg_color=colors["input_bg"], border_color=colors["border"])
        role_title_entry.pack(fill="x")
        
        # Date
        ctk.CTkLabel(main_frame, text="Date Applied:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x")
        
        if calendar_available:
            from tkcalendar import DateEntry
            date_cal = DateEntry(date_frame, width=28, background='#6366F1', 
                                foreground='white', borderwidth=2, font=('Inter', 12),
                                date_pattern='dd-mm-yy')
            date_cal.pack(pady=5, side="left")
        else:
            date_entry = ctk.CTkEntry(date_frame, height=45, placeholder_text="dd-mm-yy",
                                    fg_color=colors["input_bg"], border_color=colors["border"])
            date_entry.insert(0, datetime.now().strftime("%d-%m-%y"))
            date_entry.pack(fill="x")
            
        # Status
        ctk.CTkLabel(main_frame, text="Current Status:", font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(15, 5))
        status_var = ctk.StringVar(value="Unknown")
        status_menu = ctk.CTkOptionMenu(main_frame, values=["In Process", "Followed Up", "Rejected", "Unknown"],
                                       variable=status_var, height=45,
                                       fg_color=colors["input_bg"], text_color=colors["text"],
                                       button_color=colors["accent"])
        status_menu.pack(fill="x")
        
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
            
            stats_manager.add_application(date_str, company, country, status, manual=True, role_title=role_title)
            dialog.destroy()
            refresh_callback()
            
        ctk.CTkButton(main_frame, text="✨ Save Record", command=save_record,
                     fg_color=colors["accent"], height=50, corner_radius=12,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(35, 10), fill="x")
        
        ctk.CTkButton(main_frame, text="Cancel", command=dialog.destroy,
                     fg_color="transparent", text_color=colors["text_muted"],
                     height=40).pack(fill="x")

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
        dialog.geometry("420x560")
        dialog.transient(parent)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        ctk.CTkLabel(main_frame, text="Update Application Details", 
                    font=ctk.CTkFont(family="Inter", size=18, weight="bold")).pack(pady=(0, 20))
        
        def create_input(label, current_val):
            ctk.CTkLabel(main_frame, text=label, font=ctk.CTkFont(size=12), 
                        text_color=colors["text_muted"]).pack(anchor="w", pady=(10, 2))
            entry = ctk.CTkEntry(main_frame, width=340, height=35)
            entry.insert(0, str(current_val))
            entry.pack(pady=(0, 5))
            return entry

        company_entry = create_input("Company Name", current_company)
        role_title_entry = create_input("Role Title", current_role_title)
        
        ctk.CTkLabel(main_frame, text="Date Applied", font=ctk.CTkFont(size=12), 
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(10, 2))
        
        date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 5))
        
        date_cal = None
        if calendar_available:
            from tkcalendar import DateEntry
            try:
                current_dt = datetime.strptime(current_date, "%d-%m-%y")
                date_cal = DateEntry(date_frame, width=28, background='#6366F1', 
                                    foreground='white', borderwidth=2, font=('Inter', 12),
                                    date_pattern='dd-mm-yy')
                date_cal.set_date(current_dt)
                date_cal.pack(side="left")
            except:
                date_entry = ctk.CTkEntry(date_frame, width=200, height=35)
                date_entry.insert(0, current_date)
                date_entry.pack(side="left")
        else:
            date_entry = ctk.CTkEntry(date_frame, width=200, height=35)
            date_entry.insert(0, current_date)
            date_entry.pack(side="left")
        
        country_options = [c for c in available_countries if c != "All"]
        if current_country not in country_options:
            country_options.append(current_country)
        if "Unknown" not in country_options:
            country_options.append("Unknown")
        country_options = sorted(list(set(country_options)))
            
        country_var = ctk.StringVar(value=current_country)
        ctk.CTkOptionMenu(main_frame, values=country_options,
                         variable=country_var, width=340, height=35,
                         fg_color=colors["input_bg"], text_color=colors["text"],
                         button_color=colors["accent"]).pack(pady=(0, 5))
        
        ctk.CTkLabel(main_frame, text="Status", font=ctk.CTkFont(size=12), 
                    text_color=colors["text_muted"]).pack(anchor="w", pady=(10, 2))
        status_var = ctk.StringVar(value=current_status)
        ctk.CTkOptionMenu(main_frame, values=["Unknown", "In Process", "Followed Up", "Rejected"],
                         variable=status_var, width=340, height=35,
                         fg_color=colors["input_bg"], text_color=colors["text"],
                         button_color=colors["accent"]).pack(pady=(0, 20))
        
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
                
            if updated:
                refresh_callback(scan=False)
            dialog.destroy()
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy,
                     fg_color=colors["input_bg"], text_color=colors["text"],
                     border_width=1, border_color=colors["border"],
                     width=160, height=40).pack(side="left", padx=(0, 10))
                     
        ctk.CTkButton(btn_frame, text="OK", command=save,
                     fg_color=colors["accent"],
                     width=160, height=40).pack(side="left")
