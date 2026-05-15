import tkinter as tk
import customtkinter as ctk
import math


class AuditSankey:
    @staticmethod
    def render(canvas, stats, colors):
        canvas.delete("all")

        mode = 1 if ctk.get_appearance_mode() == "Dark" else 0
        def gc(c): return c[mode] if isinstance(c, (list, tuple)) else c

        text_color = gc(colors["text"])
        text_muted = gc(colors["text_muted"])

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 100 or h < 100:
            return

        total = len(stats)
        if total == 0:
            canvas.create_text(w / 2, h / 2, text="No applications logged yet",
                               fill=text_muted, font=("Inter", 13))
            return

        # ── Count statuses ──────────────────────────────────────────────────────
        counts = {
            "In Process": 0, "Followed Up": 0,
            "Rejected (Initial)": 0, "Rejected (Post-Interview)": 0, "Rejected (Post-Task)": 0,
            "Rejected": 0, "Offer": 0, "Accepted": 0, "Unknown": 0
        }
        for app in stats.values():
            s = app.get("status", "Unknown")
            if s in counts:
                counts[s] += 1
            elif "rejected" in s.lower():
                if "interview" in s.lower(): counts["Rejected (Post-Interview)"] += 1
                elif "task" in s.lower(): counts["Rejected (Post-Task)"] += 1
                else: counts["Rejected (Initial)"] += 1
            elif "offer" in s.lower(): counts["Offer"] += 1
            elif "accepted" in s.lower(): counts["Accepted"] += 1
            elif any(v in s for v in ["Interview", "Task", "Applied"]):
                counts["In Process"] += 1
            else:
                counts["Unknown"] += 1

        # ── Cumulative funnel (Success Path) ─────────────────────────────────────
        # Stage 1: Applied (Total)
        s_total = total
        
        # Stage 2: In Process (Proceeded past initial screening)
        # Dropout from Stage 1: Rejected (Initial) + Unknown/No Reply
        s_rej_initial = counts["Rejected (Initial)"] + counts["Rejected"]
        s_unk = counts["Unknown"]
        
        # Stage 3: Success (Offer or Accepted)
        # Dropout from Stage 2: Rejected (Post-Interview/Post-Task)
        s_success = counts["Offer"] + counts["Accepted"]
        s_rej_post = counts["Rejected (Post-Interview)"] + counts["Rejected (Post-Task)"]
        
        s_in_process = s_success + s_rej_post
        
        stages = [
            ("APPLIED",    s_total,      "#6366F1", s_rej_initial + s_unk),
            ("IN PROCESS", s_in_process, "#8B5CF6", s_rej_post),
            ("SUCCESS",    s_success,    "#10B981", 0),
        ]

        # Total rejections and unks for legend
        rej_total = s_rej_initial + s_rej_post
        unk_count = s_unk

        # ── Layout ───────────────────────────────────────────────────────────────
        node_w = 14
        pad_x  = 80 # Wider padding for labels

        n      = len(stages)
        x_step = (w - pad_x * 2) / (n - 1)

        funnel_cy    = int(h * 0.32)          # Center of the success path
        max_half     = int(h * 0.18)          # Half-height of the first bar
        legend_y     = h - 14

        def bar_half(count):
            if s_total == 0 or count <= 0: return 2
            return max(3, int(max_half * math.sqrt(count / s_total)))

        def horiz_flow(x1, y1t, y1b, x2, y2t, y2b, color, steps=26):
            pts = []
            for i in range(steps + 1):
                t = i / steps; st = (1 - math.cos(t * math.pi)) / 2
                pts += [x1 + t * (x2 - x1), y1t + st * (y2t - y1t)]
            for i in range(steps, -1, -1):
                t = i / steps; st = (1 - math.cos(t * math.pi)) / 2
                pts += [x1 + t * (x2 - x1), y1b + st * (y2b - y1b)]
            canvas.create_polygon(pts, fill=color, outline="", stipple="gray50")

        def vert_flow(cx, y0, y_tip, w_top, color, steps=20):
            """Downward tapered flow"""
            pts = []
            for i in range(steps + 1):
                t = i / steps; st = (1 - math.cos(t * math.pi)) / 2
                yi = y0 + st * (y_tip - y0)
                wi = w_top * (1 - st * 0.8) # Taper to 20% width at bottom
                pts.append(cx - wi)
                pts.append(yi)
            for i in range(steps, -1, -1):
                t = i / steps; st = (1 - math.cos(t * math.pi)) / 2
                yi = y0 + st * (y_tip - y0)
                wi = w_top * (1 - st * 0.8)
                pts.append(cx + wi)
                pts.append(yi)
            canvas.create_polygon(pts, fill=color, outline="", stipple="gray25")

        # ── Drawing ──────────────────────────────────────────────────────────────
        nodes = []
        for i, (name, count, color, dropout_count) in enumerate(stages):
            cx = pad_x + i * x_step
            ch = bar_half(count)
            yt, yb = funnel_cy - ch, funnel_cy + ch
            
            # Draw flow from previous
            if i > 0:
                prev_cx, prev_yt, prev_yb, prev_color = nodes[i-1]
                horiz_flow(prev_cx + node_w/2, prev_yt, prev_yb, cx - node_w/2, yt, yb, prev_color)

            # Draw Rejection Branch if any
            if dropout_count > 0:
                drop_h = max(4, int(ch * (dropout_count / count) * 2)) if count > 0 else 4
                drop_h = min(ch * 1.5, drop_h) # Clamp
                vert_flow(cx, yb, yb + 60, drop_h, "#EF4444")
                canvas.create_text(cx, yb + 75, text=f"REJECTED\n{dropout_count}", 
                                   fill="#EF4444", font=("Inter", 9, "bold"), justify="center")

            # Store node info for next flow
            nodes.append((cx, yt, yb, color))

        # ── Nodes & Labels ──────────────────────────────────────────────────────
        for i, (cx, yt, yb, color) in enumerate(nodes):
            name, count, _, _ = stages[i]
            # Main Bar
            canvas.create_rectangle(cx - node_w/2, yt, cx + node_w/2, yb, fill=color, outline="")
            
            # Label Above
            canvas.create_text(cx, yt - 18, text=name, fill=text_color, font=("Inter", 9, "bold"))
            # Count Below
            canvas.create_text(cx, yb + 12, text=str(count), fill=text_color, font=("Inter", 10, "bold"))

        # ── Legend ──────────────────────────────────────────────────────────────
        rej_pct = int(100 * rej_total / s_total) if s_total > 0 else 0
        unk_pct = int(100 * unk_count / s_total) if s_total > 0 else 0
        
        legend_txt = [
            ("●", "#EF4444", f"REJECTED: {rej_total} ({rej_pct}%)"),
            ("○", text_muted, f"NO REPLY: {unk_count} ({unk_pct}%)")
        ]
        
        lx = w/2 - 100
        for icon, color, txt in legend_txt:
            canvas.create_text(lx, legend_y, text=icon, fill=color, font=("Inter", 12))
            canvas.create_text(lx + 12, legend_y, text=txt, fill=text_muted, font=("Inter", 10), anchor="w")
            lx += 180
