import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta

class AuditGraph:
    @staticmethod
    def render_graph(canvas, stats_manager, date_filter, custom_date_from, custom_date_to, colors, filter_callback, tooltip_callbacks):
        canvas.delete("all")
        
        mode = ctk.get_appearance_mode()
        canvas_bg = "#161D29" if mode == "Dark" else "#FFFFFF"
        grid_color = "#1F2937" if mode == "Dark" else "#F3F4F6"
        line_color = "#6366F1"
        point_color = "#818CF8" if mode == "Dark" else "#4F46E5"
        text_color = "#9CA3AF" if mode == "Dark" else "#6B7280"
            
        canvas.configure(bg=canvas_bg)
        
        # Data Processing
        stats = stats_manager.get_stats()
        by_date = {}
        for app in stats.values():
            try:
                dt = datetime.strptime(app['date'], "%d-%m-%y").date()
                by_date[dt] = by_date.get(dt, 0) + 1
            except: pass
            
        today = datetime.now().date()
        date_range = date_filter
        
        if custom_date_from and custom_date_to:
            min_date, max_date = custom_date_from, custom_date_to
        elif date_range == "Last 7 Days":
            min_date, max_date = today - timedelta(days=6), today
        elif date_range == "Last 30 Days":
            min_date, max_date = today - timedelta(days=29), today
        elif date_range == "Last 90 Days":
            min_date, max_date = today - timedelta(days=89), today
        elif date_range == "This Year":
            min_date, max_date = datetime(today.year, 1, 1).date(), today
        elif by_date:
            min_date, max_date = min(by_date.keys()), max(by_date.keys())
            if (max_date - min_date).days < 7: min_date = max_date - timedelta(days=7)
        else:
            min_date, max_date = today - timedelta(days=30), today

        plot_data = []
        curr = min_date
        while curr <= max_date:
            plot_data.append((curr, by_date.get(curr, 0)))
            curr += timedelta(days=1)
            
        px_per_day = 45
        total_days = len(plot_data)
        viewport_w = canvas.winfo_width()
        content_w = max(viewport_w, total_days * px_per_day)
        
        h = canvas.winfo_height()
        canvas.configure(scrollregion=(0, 0, content_w, h))
        
        if viewport_w < 10: return 
        
        padding_x, padding_y = 60, 60
        plot_w, plot_h = content_w - (padding_x * 2), h - (padding_y * 2)
        
        max_apps = max(by_date.values()) if by_date else 0
        y_max = max(5, max_apps + 1)
        
        # Grid
        canvas.create_line(padding_x, h - padding_y, content_w - padding_x, h - padding_y, fill=grid_color)
        for i in range(0, y_max + 1, max(1, y_max // 4)):
            y_pos = (h - padding_y) - (i / y_max * plot_h)
            canvas.create_line(padding_x, y_pos, content_w - padding_x, y_pos, fill=grid_color, dash=(2, 2))
            canvas.create_text(padding_x - 15, y_pos, text=str(i), fill=text_color, font=('Inter', 12), anchor="e")
            
        # Points
        x_step = plot_w / (len(plot_data) - 1) if len(plot_data) > 1 else plot_w
        points = []
        for i, (date, count) in enumerate(plot_data):
            x = padding_x + (i * x_step)
            y = (h - padding_y) - (count / y_max * plot_h)
            points.append((x, y))
            
            skip = max(1, int(total_days / (content_w / 80)))
            if i % skip == 0 or i == len(plot_data) - 1:
                label = date.strftime("%d %b")
                canvas.create_text(x, h - padding_y + 15, text=label, 
                                 fill=text_color, font=('Inter', 11), angle=45, anchor="nw")

        if len(points) > 1:
            poly_points = [padding_x, h - padding_y]
            for i in range(len(points) - 1):
                canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], 
                                 fill=line_color, width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND)
                poly_points.extend([points[i][0], points[i][1]])
            
            poly_points.extend([points[-1][0], points[-1][1]])
            poly_points.extend([points[-1][0], h - padding_y])
            
            fill_hex = "#1E2235" if mode == "Dark" else "#EEF2FF"
            poly_id = canvas.create_polygon(poly_points, fill=fill_hex, outline="")
            canvas.tag_lower(poly_id)

        show_tooltip, hide_tooltip = tooltip_callbacks
        for i, (date, count) in enumerate(plot_data):
            x, y = points[i]
            r = 6
            node = canvas.create_oval(x-r, y-r, x+r, y+r, fill=point_color, outline=canvas_bg, width=2)
            canvas.tag_bind(node, "<Enter>", lambda e, nx=x, ny=y, nc=count: [show_tooltip(nx, ny, nc), canvas.configure(cursor="hand2")])
            canvas.tag_bind(node, "<Leave>", lambda e: [hide_tooltip(), canvas.configure(cursor="")])
            canvas.tag_bind(node, "<Button-1>", lambda e, d=date: filter_callback(d))
            
        total_apps = sum(by_date.values())
        avg_apps = total_apps / len(plot_data) if plot_data else 0
        canvas.create_text(content_w - padding_x - 10, padding_y - 25, 
                         text=f"RANGE AVG: {avg_apps:.1f}/day | SECTION TOTAL: {total_apps}", 
                         fill=text_color, font=('Inter', 13, 'bold'), anchor="ne")
