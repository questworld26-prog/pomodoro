#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import json
import os
import time
from datetime import date, datetime, timedelta

# Theme Color Palette
BG_COLOR = "#1e213a"
RING_BG = "#161932"
ACCENT_COLOR = "#f87070"
TEXT_COLOR = "#ffffff"
MUTED_TEXT = "#d7e0ff"
INPUT_BG = "#272b4c"
INPUT_BORDER = "#2d3154"
PANEL_BG = "#161932"
GRAPH_PALETTE = ["#f87070", "#d7e0ff", "#707597", "#383e68", "#272b4c"]

def interpolate_color(c1, c2, factor):
    c1 = c1.lstrip('#')
    c2 = c2.lstrip('#')
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

class PomodoroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Pomodoro")
        self.geometry("250x450")
        self.configure(bg=BG_COLOR)
        self.minsize(200, 300)
        
        self.data = self.load_data()
        
        self.default_duration_mins = 25.0
        self.total_seconds = int(self.default_duration_mins * 60)
        self.remaining_seconds = self.total_seconds
        self.is_running = False
        self.timer_id = None
        self.is_always_on_top = False
        self.is_flashing = False
        self.flash_state = False
        
        self.init_fonts()
        
        # Style Combobox popup menu font and colors globally
        self.option_add("*TCombobox*Listbox.font", self.combo_font)
        self.option_add("*TCombobox*Listbox.background", INPUT_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT_COLOR)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT_COLOR)
        self.option_add("*TCombobox*Listbox.selectForeground", TEXT_COLOR)
        
        self.build_ui()
        
        self.bind("<Configure>", self.on_window_configure)
        self.main_container.bind("<Button-1>", self.stop_flashing)
        self.canvas.bind("<Button-1>", self.stop_flashing)
        
        self.attributes('-topmost', self.is_always_on_top)
        self.update_timer_layout()

    def init_fonts(self):
        self.title_font = tkfont.Font(family="Helvetica Neue", size=24, weight="bold")
        self.timer_font = tkfont.Font(family="Helvetica Neue", size=58, weight="bold")
        self.status_font = tkfont.Font(family="Helvetica Neue", size=13, weight="bold")
        self.body_font = tkfont.Font(family="Helvetica Neue", size=11, weight="normal")
        self.bold_body_font = tkfont.Font(family="Helvetica Neue", size=11, weight="bold")
        self.combo_font = tkfont.Font(family="Helvetica Neue", size=16, weight="bold")
        self.graph_font = tkfont.Font(family="Helvetica Neue", size=9, weight="bold")

    def build_ui(self):
        self.main_container = tk.Frame(self, bg=BG_COLOR)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Top Bar using Grid for perfect centering
        self.top_bar = tk.Frame(self.main_container, bg=BG_COLOR)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        self.top_bar.columnconfigure(0, weight=1)
        self.top_bar.columnconfigure(1, weight=2)
        self.top_bar.columnconfigure(2, weight=1)
        
        self.pin_btn = tk.Label(self.top_bar, text="Pin", font=self.bold_body_font, fg=MUTED_TEXT, bg=INPUT_BG, padx=12, pady=6, cursor="hand2")
        self.pin_btn.grid(row=0, column=0, sticky="w")
        self.pin_btn.bind("<Button-1>", lambda e: self.toggle_always_on_top())
        self.pin_btn.bind("<Enter>", self.on_pin_enter)
        self.pin_btn.bind("<Leave>", self.on_pin_leave)
        
        self.title_label = tk.Label(self.top_bar, text="Pomodoro", fg=TEXT_COLOR, bg=BG_COLOR, font=self.title_font)
        self.title_label.grid(row=0, column=1)
        
        # Spacer for right balance
        self.right_spacer = tk.Frame(self.top_bar, bg=BG_COLOR)
        self.right_spacer.grid(row=0, column=2, sticky="e")
        
        # Timer Canvas
        self.canvas_frame = tk.Frame(self.main_container, bg=BG_COLOR)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=BG_COLOR, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create persistent canvas graphics items once
        self.ring_bg_id = self.canvas.create_oval(0, 0, 0, 0, outline=RING_BG, width=6, tags="background_ring")
        self.progress_arc_id = self.canvas.create_arc(0, 0, 0, 0, start=90, extent=0, outline=ACCENT_COLOR, style=tk.ARC, width=6, tags="progress_arc")
        
        # Editable Time Entry (Embedded into Canvas)
        self.time_var = tk.StringVar(value="25:00")
        self.time_entry = tk.Entry(
            self.canvas,
            textvariable=self.time_var,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            font=self.timer_font,
            relief="flat",
            highlightthickness=0,
            justify="center",
            width=5
        )
        self.time_entry.bind("<Return>", lambda e: self.apply_canvas_time())
        self.time_entry.bind("<FocusOut>", lambda e: self.apply_canvas_time())
        
        self.digits_entry_id = self.canvas.create_window(0, 0, window=self.time_entry, tags="digits_entry")
        
        self.status_text_id = self.canvas.create_text(0, 0, text="START", fill=MUTED_TEXT, font=self.status_font, tags="status_text")
        
        # Bindings for status text
        self.canvas.tag_bind(self.status_text_id, "<Button-1>", lambda e: self.toggle_timer_canvas_click())
        self.canvas.tag_bind(self.status_text_id, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind(self.status_text_id, "<Leave>", lambda e: self.canvas.config(cursor=""))
        
        self.canvas.bind("<Configure>", lambda e: self.update_timer_layout())
        
        # Bottom Controls Container
        self.bottom_controls_frame = tk.Frame(self.main_container, bg=BG_COLOR)
        self.bottom_controls_frame.pack(side=tk.TOP, fill=tk.X)

        # Bin Frame
        self.bin_frame = tk.Frame(self.bottom_controls_frame, bg=BG_COLOR, height=40)
        self.bin_frame.pack(side=tk.TOP, fill=tk.X)
        self.bin_frame.pack_propagate(False) 
        
        self.bin_btn = tk.Label(self.bin_frame, text="🗑 Reset", fg=ACCENT_COLOR, bg=INPUT_BG, font=self.bold_body_font, padx=12, pady=6, cursor="hand2")
        self.bin_btn.bind("<Button-1>", lambda e: self.reset_timer())
        self.bin_btn.bind("<Enter>", lambda e: self.bin_btn.configure(bg="#383e68"))
        self.bin_btn.bind("<Leave>", lambda e: self.bin_btn.configure(bg=INPUT_BG))
        
        # Current Activity Box (Spacious, larger font)
        self.activity_frame = tk.Frame(self.bottom_controls_frame, bg=BG_COLOR)
        self.activity_frame.pack(fill=tk.X, pady=(10, 15))
        
        act_lbl = tk.Label(self.activity_frame, text="Current Activity", font=self.bold_body_font, fg=MUTED_TEXT, bg=BG_COLOR, anchor="w")
        act_lbl.pack(fill=tk.X, pady=(0, 5))
        
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("Dark.TCombobox", fieldbackground=INPUT_BG, background=PANEL_BG, foreground=TEXT_COLOR, borderwidth=0, arrowcolor=MUTED_TEXT, padding=12)
        self.style.map("Dark.TCombobox", fieldbackground=[('readonly', INPUT_BG)], foreground=[('readonly', TEXT_COLOR)])
        
        self.activity_var = tk.StringVar(value="General Focus")
        self.activity_combo = ttk.Combobox(self.activity_frame, textvariable=self.activity_var, style="Dark.TCombobox", font=self.combo_font)
        self.activity_combo.pack(fill=tk.X)
        self.update_activity_dropdown_items()
        
        # Stats Toggles
        self.sep = tk.Frame(self.bottom_controls_frame, bg=INPUT_BORDER, height=1)
        self.sep.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))
        
        self.toggles_frame = tk.Frame(self.bottom_controls_frame, bg=BG_COLOR)
        self.toggles_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.stats_toggle_btn = self.create_button(self.toggles_frame, "📊 Metrics Graphs", self.toggle_stats_panel, bg=INPUT_BG, fg=MUTED_TEXT)
        self.stats_toggle_btn.pack(side=tk.TOP, expand=True, fill=tk.X, padx=4)
        
        # Stats Panel
        self.stats_panel = tk.Frame(self.bottom_controls_frame, bg=PANEL_BG, bd=1, relief="flat", highlightbackground=INPUT_BORDER, highlightthickness=1)
        self.show_stats_var = tk.BooleanVar(value=False)
        self.build_stats_panel()

    def build_stats_panel(self):
        inner_frame = tk.Frame(self.stats_panel, bg=PANEL_BG, padx=10, pady=10)
        inner_frame.pack(fill=tk.BOTH, expand=True)
        
        self.summary_lbl = tk.Label(inner_frame, text="", font=self.bold_body_font, fg=TEXT_COLOR, bg=PANEL_BG)
        self.summary_lbl.pack(fill=tk.X, pady=(0, 5))
        
        self.metrics_canvas = tk.Canvas(inner_frame, bg=PANEL_BG, highlightthickness=0, bd=0)
        self.metrics_canvas.pack(fill=tk.BOTH, expand=True)
        self.metrics_canvas.bind("<Configure>", lambda e: self.draw_metrics_graphs())

    def create_button(self, parent, text, command, bg, fg):
        btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=self.bold_body_font, padx=12, pady=7, cursor="hand2")
        btn.bind("<Enter>", lambda e: btn.configure(bg="#383e68"))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        btn.bind("<Button-1>", lambda e: command())
        return btn

    def update_bottom_controls_visibility(self):
        if self.is_running:
            self.bottom_controls_frame.pack_forget()
        else:
            if self.show_stats_var.get():
                self.bottom_controls_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            else:
                self.bottom_controls_frame.pack(side=tk.TOP, fill=tk.X)

    def toggle_stats_panel(self):
        if self.show_stats_var.get():
            self.stats_panel.pack_forget()
            self.show_stats_var.set(False)
            self.stats_toggle_btn.configure(bg=INPUT_BG, fg=MUTED_TEXT)
            self.update_bottom_controls_visibility()
        else:
            self.stats_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(5, 10))
            self.show_stats_var.set(True)
            self.stats_toggle_btn.configure(bg=ACCENT_COLOR, fg=TEXT_COLOR)
            self.refresh_stats_display()
            self.update_bottom_controls_visibility()
            
    def on_pin_enter(self, event):
        if self.is_always_on_top:
            self.pin_btn.configure(bg="#ff8a8a")
        else:
            self.pin_btn.configure(bg="#383e68")

    def on_pin_leave(self, event):
        if self.is_always_on_top:
            self.pin_btn.configure(bg=ACCENT_COLOR)
        else:
            self.pin_btn.configure(bg=INPUT_BG)

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        self.attributes('-topmost', 1 if self.is_always_on_top else 0)
        self.update()
        if self.is_always_on_top:
            self.lift()
        
        # Update text & colors
        if self.is_always_on_top:
            self.pin_btn.configure(text="Unpin", bg=ACCENT_COLOR, fg=TEXT_COLOR)
        else:
            self.pin_btn.configure(text="Pin", bg=INPUT_BG, fg=MUTED_TEXT)

    # --- Data Persistence ---
    def load_data(self):
        self.data_file = "pomodoro_data.json"
        default = {
            "total_minutes": 0.0,
            "daily_minutes": {},
            "hourly_minutes": {},
            "activities": {}
        }
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    for k, v in default.items():
                        if k not in data: data[k] = v
                    return data
            except:
                return default
        return default

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.data, f, indent=4)
        except:
            pass

    def log_completed_session(self):
        mins = self.default_duration_mins
        self.data["total_minutes"] += mins
        
        today_str = date.today().isoformat()
        self.data["daily_minutes"][today_str] = self.data["daily_minutes"].get(today_str, 0.0) + mins
        
        hour_str = str(datetime.now().hour)
        self.data["hourly_minutes"][hour_str] = self.data["hourly_minutes"].get(hour_str, 0.0) + mins
        
        act = self.activity_var.get().strip() or "General Focus"
        self.data["activities"][act] = self.data["activities"].get(act, 0.0) + mins
        
        self.save_data()
        self.update_activity_dropdown_items()
        if self.show_stats_var.get():
            self.refresh_stats_display()

    def update_activity_dropdown_items(self):
        acts = list(self.data.get("activities", {}).keys())
        acts.sort()
        self.activity_combo['values'] = acts

    # --- Dynamic Canvas Graphics ---
    def refresh_stats_display(self):
        self.summary_lbl.configure(text=f"Total Lifetime Focus: {self.data['total_minutes']:.1f} mins")
        self.draw_metrics_graphs()

    def draw_metrics_graphs(self):
        if not self.show_stats_var.get(): return
        self.metrics_canvas.delete("all")
        w, h = self.metrics_canvas.winfo_width(), self.metrics_canvas.winfo_height()
        if w < 50 or h < 50: return
        
        sec_h = h / 3.0
        self.draw_activity_bars(0, 0, w, sec_h)
        self.draw_hourly_heatmap(0, sec_h, w, sec_h)
        self.draw_weekly_bars(0, sec_h * 2, w, sec_h)

    def draw_activity_bars(self, x_off, y_off, width, height):
        if width < 50 or height < 50: return
        self.metrics_canvas.create_text(x_off + 5, y_off + 10, text="Activity Focus (Minutes)", font=self.graph_font, fill=MUTED_TEXT, anchor="nw")
        
        acts = self.data.get("activities", {})
        if not acts:
            self.metrics_canvas.create_text(x_off + width/2, y_off + height/2, text="No Activity Data", fill=MUTED_TEXT, font=self.graph_font)
            return
            
        # Get top 5 activities sorted by total minutes
        sorted_acts = sorted(acts.items(), key=lambda x: x[1], reverse=True)[:5]
        labels = [item[0] for item in sorted_acts]
        vals = [item[1] for item in sorted_acts]
        
        max_val = max(vals) if max(vals) > 0 else 1.0
        
        w_avail = max(10.0, width - 40)
        h_avail = max(10.0, height - 60)
        num_bars = len(vals)
        spacing = w_avail / max(1, num_bars)
        bar_w = spacing * 0.6
        
        for i, val in enumerate(vals):
            cx = x_off + 20 + (i * spacing) + (spacing / 2)
            bar_h = (val / max_val) * h_avail
            bx0, by0 = cx - (bar_w / 2), y_off + 25 + h_avail - bar_h
            bx1, by1 = cx + (bar_w / 2), y_off + 25 + h_avail
            self.metrics_canvas.create_rectangle(bx0, by0, bx1, by1, fill=ACCENT_COLOR, outline="")
            
            # Draw duration text above the bar
            self.metrics_canvas.create_text(cx, by0 - 5, text=f"{val:.0f}m", font=self.graph_font, fill=TEXT_COLOR, anchor="s")
            
            # Truncate labels if too long
            label_text = labels[i]
            if len(label_text) > 10:
                label_text = label_text[:8] + ".."
            self.metrics_canvas.create_text(cx, by1 + 10, text=label_text, font=self.graph_font, fill=MUTED_TEXT, anchor="n")

    def draw_weekly_bars(self, x_off, y_off, width, height):
        if width < 50 or height < 50: return
        self.metrics_canvas.create_text(x_off + 5, y_off + 10, text="Weekly Velocity (Mon-Sun)", font=self.graph_font, fill=MUTED_TEXT, anchor="nw")
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        days = [monday + timedelta(days=i) for i in range(7)]
        labels = ["M", "T", "W", "T", "F", "S", "S"]
        
        vals = [self.data["daily_minutes"].get(d.isoformat(), 0.0) for d in days]
        max_val = max(vals) if max(vals) > 0.0 else 1.0
        
        w_avail = max(10.0, width - 40)
        h_avail = max(10.0, height - 50)
        bar_w, spacing = w_avail / 7.0 * 0.6, w_avail / 7.0
        
        for i, val in enumerate(vals):
            cx = x_off + 20 + (i * spacing) + (spacing / 2)
            bar_h = (val / max_val) * h_avail
            bx0, by0 = cx - (bar_w / 2), y_off + 25 + h_avail - bar_h
            bx1, by1 = cx + (bar_w / 2), y_off + 25 + h_avail
            self.metrics_canvas.create_rectangle(bx0, by0, bx1, by1, fill=ACCENT_COLOR, outline="")
            
            lbl_color = TEXT_COLOR if days[i] == today else MUTED_TEXT
            self.metrics_canvas.create_text(cx, by1 + 10, text=labels[i], font=self.graph_font, fill=lbl_color, anchor="n")

    def draw_hourly_heatmap(self, x_off, y_off, width, height):
        if width < 50 or height < 40: return
        self.metrics_canvas.create_text(x_off + 5, y_off + 10, text="Productivity Heatmap (24h)", font=self.graph_font, fill=MUTED_TEXT, anchor="nw")
        vals = [self.data["hourly_minutes"].get(str(i), 0) for i in range(24)]
        max_val = max(vals) if max(vals) > 0 else 1.0
        block_w = max(1.0, (width - 40) / 24.0)
        strip_y = y_off + height/2
        
        for i, val in enumerate(vals):
            bx0 = x_off + 20 + (i * block_w)
            bx1 = bx0 + block_w - 1
            if val == 0: color = RING_BG
            else: color = interpolate_color(RING_BG, ACCENT_COLOR, 0.2 + 0.8 * (val / max_val))
            self.metrics_canvas.create_rectangle(bx0, strip_y - 15, bx1, strip_y + 15, fill=color, outline=BG_COLOR)
            if i % 6 == 0: self.metrics_canvas.create_text(bx0, strip_y + 20, text=f"{i}h", font=self.graph_font, fill=MUTED_TEXT, anchor="n")

    # --- Timer & Scaling ---
    def on_window_configure(self, event):
        if event.widget == self:
            w, h = self.winfo_width(), self.winfo_height()
            scale = max(0.6, min(min(w / 450.0, h / 700.0), 2.5))
            
            self.title_font.configure(size=int(24 * scale))
            self.timer_font.configure(size=int(58 * scale))
            self.status_font.configure(size=int(14 * scale))
            self.body_font.configure(size=int(11 * scale))
            self.bold_body_font.configure(size=int(11 * scale))
            self.combo_font.configure(size=int(16 * scale))
            self.graph_font.configure(size=int(9 * scale))
            self.time_entry.configure(font=self.timer_font)

    def update_timer_layout(self, event=None):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 10 or h < 10:
            w, h = 300, 300
            
        margin = 15
        circle_size = max(50, min(w, h) - (margin * 2))
        x0, y0 = (w - circle_size) / 2, (h - circle_size) / 2
        x1, y1 = x0 + circle_size, y0 + circle_size
        thickness = max(6, int(circle_size * 0.04))
        
        self.canvas.coords(self.ring_bg_id, x0, y0, x1, y1)
        self.canvas.itemconfig(self.ring_bg_id, width=thickness)
        
        self.canvas.coords(self.progress_arc_id, x0, y0, x1, y1)
        self.canvas.itemconfig(self.progress_arc_id, width=thickness)
        
        cx, cy = w / 2, h / 2
        self.canvas.coords(self.digits_entry_id, cx, cy - (circle_size * 0.05))
        self.canvas.coords(self.status_text_id, cx, cy + (circle_size * 0.20))
        
        self.update_timer_display()

    def update_timer_display(self):
        extent = -359.99 * (self.remaining_seconds / self.total_seconds) if self.total_seconds > 0 else 0
        self.canvas.itemconfig(self.progress_arc_id, extent=extent)
        
        # Determine background color to use for the entry dynamically
        current_bg = self.canvas.cget("bg")
        
        if self.is_running:
            self.time_entry.configure(state="readonly", readonlybackground=current_bg, fg=TEXT_COLOR)
        else:
            self.time_entry.configure(state="normal", bg=current_bg)
            focus_widget = None
            try:
                focus_widget = self.focus_get()
            except Exception:
                pass
            if focus_widget != self.time_entry:
                mins, secs = int(self.remaining_seconds) // 60, int(self.remaining_seconds) % 60
                self.time_var.set(f"{mins:02d}:{secs:02d}")
                
        if self.is_running:
            status_str = "FOCUSED"
        elif self.remaining_seconds == self.total_seconds:
            status_str = "START"
        else:
            status_str = "PAUSED"
            
        if not self.is_flashing:
            self.canvas.itemconfig(self.status_text_id, text=status_str, fill=MUTED_TEXT)
        else:
            self.canvas.itemconfig(self.status_text_id, text=status_str)
            
        self.update_bin_visibility()

    def update_bin_visibility(self):
        if not self.is_running and self.remaining_seconds < self.total_seconds:
            if not self.bin_btn.winfo_ismapped():
                self.bin_btn.pack(pady=4)
        else:
            if self.bin_btn.winfo_ismapped():
                self.bin_btn.pack_forget()

    def toggle_timer_canvas_click(self):
        # We know they clicked the exact word because of tag_bind
        if self.is_running: self.pause_timer()
        else: self.start_timer()

    def apply_canvas_time(self):
        val_str = self.time_var.get().strip()
        try:
            if ':' in val_str:
                m, s = val_str.split(':')
                total = int(m)*60 + int(s)
            else:
                total = int(float(val_str) * 60)
            
            if total > 0:
                self.default_duration_mins = total / 60.0
                if not self.is_running:
                    self.total_seconds = total
                    self.remaining_seconds = total
                    self.update_timer_display()
        except:
            pass
        
        # Reset visual
        self.update_timer_display()
        # Remove focus from entry
        self.focus()

    def start_timer(self):
        if self.is_running: return
        if self.is_flashing: self.stop_flashing()
        
        self.apply_canvas_time()
        if self.remaining_seconds <= 0: self.remaining_seconds = self.total_seconds
            
        self.is_running = True
        self.tick()
        self.update_timer_display()
        self.update_bottom_controls_visibility()

    def pause_timer(self):
        self.is_running = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.update_timer_display()
        self.update_bottom_controls_visibility()

    def reset_timer(self):
        self.pause_timer()
        self.apply_canvas_time()
        self.total_seconds = int(self.default_duration_mins * 60)
        self.remaining_seconds = self.total_seconds
        if self.is_flashing: self.stop_flashing()
        self.update_timer_display()
        self.update_bottom_controls_visibility()

    def tick(self):
        if not self.is_running: return
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            mins, secs = int(self.remaining_seconds) // 60, int(self.remaining_seconds) % 60
            self.time_var.set(f"{mins:02d}:{secs:02d}")
            self.update_timer_display()
            self.timer_id = self.after(1000, self.tick)
        else:
            self.is_running = False
            self.timer_id = None
            self.log_completed_session()
            # Reset to the last used duration
            self.remaining_seconds = self.total_seconds
            mins, secs = int(self.remaining_seconds) // 60, int(self.remaining_seconds) % 60
            self.time_var.set(f"{mins:02d}:{secs:02d}")
            self.update_timer_display()
            self.update_bottom_controls_visibility()
            self.start_flashing_alert()

    # --- Flashing Alert ---
    def start_flashing_alert(self):
        self.is_flashing = True
        self.flash_state = False
        self.flash_tick()

    def flash_tick(self):
        if not self.is_flashing: return
        self.flash_state = not self.flash_state
        flash_bg = ACCENT_COLOR if self.flash_state else BG_COLOR
        flash_fg = BG_COLOR if self.flash_state else TEXT_COLOR
        
        self.configure(bg=flash_bg)
        self.main_container.configure(bg=flash_bg)
        self.top_bar.configure(bg=flash_bg)
        self.title_label.configure(bg=flash_bg, fg=flash_fg)
        
        # Style the Pin button background during flash
        if self.is_always_on_top:
            self.pin_btn.configure(bg=ACCENT_COLOR, fg=TEXT_COLOR)
        else:
            self.pin_btn.configure(bg=flash_bg, fg=flash_fg)
            
        self.right_spacer.configure(bg=flash_bg)
        self.canvas_frame.configure(bg=flash_bg)
        self.canvas.configure(bg=flash_bg)
        self.bin_frame.configure(bg=flash_bg)
        self.activity_frame.configure(bg=flash_bg)
        self.toggles_frame.configure(bg=flash_bg)
        
        self.time_entry.configure(bg=flash_bg, fg=flash_fg, readonlybackground=flash_bg)
        self.canvas.itemconfig(self.status_text_id, fill=flash_fg)
        
        # Style the combobox field and mapping to match the flash color
        self.style.configure("Dark.TCombobox", fieldbackground=flash_bg, background=flash_bg, foreground=flash_fg, arrowcolor=flash_fg)
        self.style.map("Dark.TCombobox", fieldbackground=[('readonly', flash_bg)], foreground=[('readonly', flash_fg)])
        
        self.timer_id = self.after(500, self.flash_tick)

    def stop_flashing(self, event=None):
        if not self.is_flashing: return
        self.is_flashing = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
            
        self.configure(bg=BG_COLOR)
        self.main_container.configure(bg=BG_COLOR)
        self.top_bar.configure(bg=BG_COLOR)
        self.title_label.configure(bg=BG_COLOR, fg=TEXT_COLOR)
        
        # Restore Pin button bg/fg based on top-most status
        if self.is_always_on_top:
            self.pin_btn.configure(text="Unpin", bg=ACCENT_COLOR, fg=TEXT_COLOR)
        else:
            self.pin_btn.configure(text="Pin", bg=INPUT_BG, fg=MUTED_TEXT)
            
        self.right_spacer.configure(bg=BG_COLOR)
        self.canvas_frame.configure(bg=BG_COLOR)
        self.canvas.configure(bg=BG_COLOR)
        self.bin_frame.configure(bg=BG_COLOR)
        self.activity_frame.configure(bg=BG_COLOR)
        self.toggles_frame.configure(bg=BG_COLOR)
        
        self.time_entry.configure(bg=BG_COLOR, fg=TEXT_COLOR, readonlybackground=BG_COLOR)
        
        # Restore combobox theme styles
        self.style.configure("Dark.TCombobox", fieldbackground=INPUT_BG, background=PANEL_BG, foreground=TEXT_COLOR, arrowcolor=MUTED_TEXT)
        self.style.map("Dark.TCombobox", fieldbackground=[('readonly', INPUT_BG)], foreground=[('readonly', TEXT_COLOR)])
        
        self.update_timer_display()

if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
