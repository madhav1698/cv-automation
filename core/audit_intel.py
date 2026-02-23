import customtkinter as ctk

class AuditIntel:
    @staticmethod
    def render_intelligence(funnel_body, market_body, stats, colors):
        # 1. Pipeline Funnel
        for w in funnel_body.winfo_children(): w.destroy()
        counts = {"Applied": len(stats), "Interview": 0, "Rejected": 0}
        for d in stats.values():
            if d['status'] == "In Process": counts["Interview"] += 1
            if d['status'] == "Rejected": counts["Rejected"] += 1
        
        steps = [
            ("APPLIED", counts["Applied"], colors["accent"]),
            ("INTERVIEW", counts["Interview"], "#3B82F6"),
            ("REJECTED", counts["Rejected"], "#EF4444")
        ]
        
        max_val = max(counts.values()) or 1
        for label, val, color in steps:
            row = ctk.CTkFrame(funnel_body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14, weight="bold"), width=90, anchor="w").pack(side="left")
            
            bar_frame = ctk.CTkFrame(row, fg_color=colors["input_bg"], height=8, corner_radius=4)
            bar_frame.pack(side="left", fill="x", expand=True, padx=10)
            
            progress = (val / max_val)
            ctk.CTkFrame(bar_frame, fg_color=color, height=8, width=max(1, int(200 * progress)), corner_radius=4).pack(side="left")
            ctk.CTkLabel(row, text=str(val), font=ctk.CTkFont(size=14, weight="bold"), width=30).pack(side="right")

        # 2. Top Countries
        for w in market_body.winfo_children(): w.destroy()
        countries = {}
        for d in stats.values():
            c = d.get('country', 'Unknown')
            countries[c] = countries.get(c, 0) + 1
        
        top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:4]
        for name, val in top_countries:
            row = ctk.CTkFrame(market_body, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=13), width=100, anchor="w").pack(side="left")
            
            bar_bg = ctk.CTkFrame(row, fg_color=colors["input_bg"], height=12, corner_radius=6)
            bar_bg.pack(side="left", fill="x", expand=True, padx=10)
            
            share = (val / counts["Applied"]) if counts["Applied"] > 0 else 0
            ctk.CTkFrame(bar_bg, fg_color=colors["accent"], height=12, width=max(1, int(150 * share)), corner_radius=6).pack(side="left")
            ctk.CTkLabel(row, text=f"{val}", font=ctk.CTkFont(size=12, weight="bold"), width=30).pack(side="right")
