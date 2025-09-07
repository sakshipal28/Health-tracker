#!/usr/bin/env python3
"""
Advanced Health Tracker - GUI version (Tkinter)
Features:
- Inputs: Name, Age, Gender, Height (cm/m), Weight, Activity Level
- Calculates: BMI, Category, BMR, TDEE, Water intake
- Save entry to data/health_history.csv
- View history in a table
- Optional: Show BMI trend chart if matplotlib installed
"""

import os
import csv
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Try optional matplotlib for charting
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "health_history.csv")

ACTIVITY_LEVELS = {
    "Sedentary (little/no exercise)": 1.2,
    "Light (1–3 days/wk)": 1.375,
    "Moderate (3–5 days/wk)": 1.55,
    "Active (6–7 days/wk)": 1.725,
    "Very Active (hard exercise)": 1.9,
}

CATEGORIES = [
    ("Underweight", 0, 18.5),
    ("Normal weight", 18.5, 25),
    ("Overweight", 25, 30),
    ("Obese", 30, float("inf")),
]

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def cm_to_m(cm):
    return cm / 100.0

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    if height_m <= 0:
        raise ValueError("Height must be > 0")
    return weight_kg / (height_m ** 2)

def bmi_category(bmi: float) -> str:
    for label, lo, hi in CATEGORIES:
        if lo <= bmi < hi:
            return label
    return "Unknown"

def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    # Mifflin-St Jeor
    if gender.strip().lower().startswith("m"):
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def tdee_from_bmr(bmr: float, activity_multiplier: float) -> float:
    return bmr * activity_multiplier

def water_intake_liters(weight_kg: float) -> float:
    return weight_kg * 0.035

class HealthTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🏥 Health Tracker")
        self.geometry("760x560")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        pad = 10
        header = ttk.Label(self, text="Health Tracker", font=("Segoe UI", 18, "bold"))
        header.pack(pady=(8,6))

        main = ttk.Frame(self, padding=pad)
        main.pack(fill="both", expand=True)

        form = ttk.LabelFrame(main, text="Enter Details", padding=pad)
        results = ttk.LabelFrame(main, text="Results", padding=pad)
        form.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=8)
        results.grid(row=0, column=1, sticky="nsew", pady=8)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # Form variables
        self.name_var = tk.StringVar()
        self.age_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="Female")
        self.height_var = tk.StringVar()
        self.height_unit_var = tk.StringVar(value="cm")
        self.weight_var = tk.StringVar()
        self.activity_var = tk.StringVar(value=list(ACTIVITY_LEVELS.keys())[1])

        # Form layout
        r = 0
        ttk.Label(form, text="Name").grid(row=r, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.name_var, width=30).grid(row=r, column=1, sticky="ew")
        r += 1

        ttk.Label(form, text="Age (years)").grid(row=r, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.age_var, width=10).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(form, text="Gender").grid(row=r, column=0, sticky="w")
        ttk.Combobox(form, textvariable=self.gender_var, values=["Female", "Male"], state="readonly", width=12).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(form, text="Height").grid(row=r, column=0, sticky="w")
        hf = ttk.Frame(form)
        hf.grid(row=r, column=1, sticky="w")
        ttk.Entry(hf, textvariable=self.height_var, width=10).pack(side="left")
        ttk.Combobox(hf, textvariable=self.height_unit_var, values=["cm", "m"], state="readonly", width=5).pack(side="left", padx=(6,0))
        r += 1

        ttk.Label(form, text="Weight (kg)").grid(row=r, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.weight_var, width=10).grid(row=r, column=1, sticky="w")
        r += 1

        ttk.Label(form, text="Activity Level").grid(row=r, column=0, sticky="w")
        ttk.Combobox(form, textvariable=self.activity_var, values=list(ACTIVITY_LEVELS.keys()), state="readonly", width=28).grid(row=r, column=1, sticky="w")
        r += 1

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=r, column=0, columnspan=2, pady=(10,0), sticky="w")
        ttk.Button(btn_frame, text="Calculate", command=self.on_calculate).pack(side="left", padx=(0,6))
        ttk.Button(btn_frame, text="Save Entry", command=self.on_save).pack(side="left", padx=(0,6))
        ttk.Button(btn_frame, text="View History", command=self.on_view_history).pack(side="left", padx=(0,6))
        self.chart_btn = ttk.Button(btn_frame, text="Show BMI Chart", command=self.on_show_chart)
        if not MATPLOTLIB_OK:
            self.chart_btn.state(["disabled"])
        self.chart_btn.pack(side="left", padx=(0,6))
        ttk.Button(btn_frame, text="Clear", command=self.on_clear).pack(side="left")

        # Results text
        self.result_text = tk.Text(results, height=20, wrap="word", font=("Segoe UI", 10))
        self.result_text.pack(fill="both", expand=True)

        self.status = ttk.Label(self, text="Fill the form and click Calculate.", anchor="w")
        self.status.pack(fill="x", padx=pad, pady=(0,8))

    def _parse_inputs(self):
        try:
            age = int(self.age_var.get())
        except Exception:
            raise ValueError("Enter valid integer for Age.")

        try:
            height_val = float(self.height_var.get())
        except Exception:
            raise ValueError("Enter valid number for Height.")

        unit = self.height_unit_var.get()
        if unit == "cm":
            height_m = cm_to_m(height_val)
            height_cm = height_val
        else:
            height_m = height_val
            height_cm = height_val * 100

        try:
            weight = float(self.weight_var.get())
        except Exception:
            raise ValueError("Enter valid number for Weight.")

        gender = self.gender_var.get()
        activity_multiplier = ACTIVITY_LEVELS[self.activity_var.get()]
        name = self.name_var.get().strip()

        if age <= 0 or height_m <= 0 or weight <= 0:
            raise ValueError("Age, Height and Weight must be > 0")

        return name, age, gender, height_m, height_cm, weight, activity_multiplier

    def on_calculate(self):
        try:
            name, age, gender, height_m, height_cm, weight, activity = self._parse_inputs()
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        bmi = calculate_bmi(weight, height_m)
        cat = bmi_category(bmi)
        bmr = calculate_bmr(gender, weight, height_cm, age)
        tdee = tdee_from_bmr(bmr, activity)
        water_l = water_intake_liters(weight)

        self._show_results(name, age, gender, height_cm, weight, bmi, cat, bmr, tdee, water_l)
        self.status.config(text="Calculated. Click Save Entry to save.")

    def _show_results(self, name, age, gender, height_cm, weight, bmi, cat, bmr, tdee, water_l):
        self.result_text.delete("1.0", "end")
        lines = []
        if name:
            lines.append(f"Name: {name}")
        lines.extend([
            f"Age: {age} years",
            f"Gender: {gender}",
            f"Height: {height_cm:.1f} cm",
            f"Weight: {weight:.1f} kg",
            "",
            f"BMI: {bmi:.2f} ({cat})",
            f"BMR (Mifflin–St Jeor): {bmr:.0f} kcal/day",
            f"Estimated Daily Calories (TDEE): {tdee:.0f} kcal/day",
            f"Recommended Water Intake: {water_l:.2f} L/day",
        ])
        self.result_text.insert("1.0", "\n".join(lines))

    def on_clear(self):
        self.name_var.set("")
        self.age_var.set("")
        self.gender_var.set("Female")
        self.height_var.set("")
        self.height_unit_var.set("cm")
        self.weight_var.set("")
        self.activity_var.set(list(ACTIVITY_LEVELS.keys())[1])
        self.result_text.delete("1.0", "end")
        self.status.config(text="Cleared.")

    def on_save(self):
        ensure_data_dir()
        try:
            name, age, gender, height_m, height_cm, weight, activity = self._parse_inputs()
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        bmi = calculate_bmi(weight, height_m)
        cat = bmi_category(bmi)
        bmr = calculate_bmr(gender, weight, height_cm, age)
        tdee = tdee_from_bmr(bmr, activity)
        water_l = water_intake_liters(weight)

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": name,
            "age": age,
            "gender": gender,
            "height_cm": round(height_cm, 1),
            "weight_kg": round(weight, 1),
            "bmi": round(bmi, 2),
            "category": cat,
            "bmr": round(bmr, 0),
            "tdee": round(tdee, 0),
            "water_l": round(water_l, 2),
        }

        file_exists = os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        messagebox.showinfo("Saved", f"Entry saved to {CSV_PATH}")
        self.status.config(text=f"Saved to {CSV_PATH}")

    def on_view_history(self):
        if not os.path.exists(CSV_PATH):
            messagebox.showinfo("No Data", "No history yet. Save an entry first.")
            return

        win = tk.Toplevel(self)
        win.title("History")
        win.geometry("900x360")

        cols = ["timestamp", "name", "age", "gender", "height_cm", "weight_kg", "bmi", "category", "bmr", "tdee", "water_l"]
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=100, anchor="center")
        tree.pack(fill="both", expand=True)

        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                tree.insert("", "end", values=[r.get(c, "") for c in cols])

    def on_show_chart(self):
        if not MATPLOTLIB_OK:
            messagebox.showerror("Matplotlib Missing", "Matplotlib not installed. Install via 'pip install matplotlib'.")
            return
        if not os.path.exists(CSV_PATH):
            messagebox.showinfo("No Data", "No history yet. Save an entry first.")
            return

        timestamps = []
        bmis = []
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    timestamps.append(datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S"))
                    bmis.append(float(r["bmi"]))
                except Exception:
                    pass

        if not timestamps:
            messagebox.showinfo("No Data", "No valid entries to plot.")
            return

        plt.figure()
        plt.plot(timestamps, bmis, marker="o")
        plt.title("BMI Trend Over Time")
        plt.xlabel("Date")
        plt.ylabel("BMI")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    ensure_data_dir()
    app = HealthTrackerApp()
    app.mainloop()
