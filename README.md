# Pomodoro

A sleek, lightweight, single-file desktop Pomodoro timer tailored for Apple Silicon (M1) and Intel Macs running macOS. Built entirely on native Python Tcl/Tk widgets, it features zero external dependencies, a modern dark-mode aesthetic, auto-hiding focus mode, and interactive native graphs.

---

## Key Features

### ⏱️ Distraction-Free Focus Mode
* **Auto-Hiding Interface:** When the timer starts, all widgets below the circle (Current Activity, separator, Stats panel, Reset button) automatically fade out (`pack_forget`). The timer circle expands to fill the window.
* **Instant Reappearance:** As soon as you pause, reset, or finish a session, all controls instantly snap back into view.

### 📊 Clean Native Metrics Canvas (Zero Dependencies)
A custom metrics visualization dashboard built entirely on `tkinter.Canvas` coordinate calculations with zero external libraries (no matplotlib, no pandas):
1. **Activity Focus (Minutes):** A vertical bar chart showcasing your top 5 activities and cumulative minutes focused, labeled dynamically with duration counts (e.g. `50m`).
2. **Productivity Heatmap (24h):** A horizontal 24-block hourly timeline. Shading scales from deep navy to bright coral based on productivity density during that hour.
3. **Weekly Velocity (Mon-Sun):** A bar chart tracking cumulative focus minutes across weekdays of the current week.

### 📌 Top-Most Pinning & Layout Centering
* **Topmost Overlay:** Click the **Pin** button in the top left to keep the timer on top of all other windows. The button dynamically updates to **Unpin** and lights up in coral when active.
* **Centered Grid Layout:** The top-bar uses a balanced 3-column grid structure, keeping the **Pomodoro** title perfectly centered at all window scales.

### ⌨️ Editable Timer Core
* **Interactive Digits:** Double-click the digital time in the center of the ring to edit the duration manually (e.g., `25:00` or just `20`). Press `Enter` or click out to save.
* **Start/Pause Trigger:** Click the status text (`START` / `PAUSED`) below the digits to toggle the timer state.
* **Auto-Reset:** On session completion, the timer triggers a flashing alert, automatically resets to your starting duration, and resets the status text to `START`.

---

## Technical Architecture

* **Framework:** Python 3.11+ standard library (`tkinter`, `json`, `time`).
* **Footprint:** Exceptionally low CPU and memory footprint, utilizing native macOS Tcl/Tk rendering pipelines.
* **Data Storage:** Persists metrics locally in `pomodoro_data.json` relative to the script directory.
* **Proportional Scaling:** Resizes dynamically on the window `<Configure>` event, scaling font dimensions and Canvas shapes seamlessly.

---

## Getting Started

### Prerequisites
Make sure you have Python 3 installed. Python comes standard on macOS, but Tcl/Tk support is recommended (included with standard brew python installations).

### Running the App
Navigate to the repository folder and execute:
```bash
python3 pomodoro.py
```

### Controls and Usage
1. **To Start/Pause:** Click the `START` / `PAUSED` word inside the timer ring.
2. **To Reset:** Click the `🗑 Reset` button that appears below the timer when paused.
3. **To Customize Activity:** Select an activity from the dropdown or type a custom task directly into the combobox before starting.
4. **To View Metrics:** Click `📊 Metrics Graphs` at the bottom of the window to expand the stats drawer.
