#!/usr/bin/env python3
"""
Advanced Health Tracker - CLI version
Features:
- BMI calculation + category
- BMR (Mifflin-St Jeor) + TDEE by activity level
- Water intake suggestion
- Save entries to data/health_history.csv
"""

import os
import csv
from datetime import datetime

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "health_history.csv")

ACTIVITY_LEVELS = {
    "1": ("Sedentary (little/no exercise)", 1.2),
    "2": ("Light (1–3 days/wk)", 1.375),
    "3": ("Moderate (3–5 days/wk)", 1.55),
    "4": ("Active (6–7 days/wk)", 1.725),
    "5": ("Very Active (hard exercise)", 1.9),
}

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def cm_to_m(cm):
    return cm / 100.0

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    if height_m <= 0:
        raise ValueError("Height must be > 0")
    return weight_kg / (height_m ** 2)

def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    # Mifflin-St Jeor equation
    if gender.strip().lower().startswith("m"):
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def tdee_from_bmr(bmr: float, activity_multiplier: float) -> float:
    return bmr * activity_multiplier

def water_intake_liters(weight_kg: float) -> float:
    # Approx 35 ml per kg
    return weight_kg * 0.035

def save_entry(row: dict):
    ensure_data_dir()
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"Saved to {CSV_PATH}")

def prompt_float(prompt_text: str, allow_zero=False) -> float:
    while True:
        try:
            val = float(input(prompt_text).strip())
            if not allow_zero and val <= 0:
                print("Please enter a number greater than zero.")
                continue
            return val
        except ValueError:
            print("Invalid number. Try again.")

def prompt_int(prompt_text: str) -> int:
    while True:
        try:
            val = int(input(prompt_text).strip())
            if val <= 0:
                print("Please enter an integer greater than zero.")
                continue
            return val
        except ValueError:
            print("Invalid integer. Try again.")

def main():
    print("🏥 Advanced Health Tracker — CLI")
    name = input("Name (optional): ").strip()
    age = prompt_int("Age (years): ")
    gender = input("Gender (Male/Female) [M/F]: ").strip() or "F"

    # Height input: ask unit
    while True:
        unit = input("Height unit - enter 'cm' or 'm' (default cm): ").strip().lower() or "cm"
        if unit in ("cm", "m"):
            break
        print("Please enter 'cm' or 'm'.")

    height_val = prompt_float(f"Height value ({unit}): ")
    if unit == "cm":
        height_m = cm_to_m(height_val)
        height_cm = height_val
    else:
        height_m = height_val
        height_cm = height_val * 100

    weight = prompt_float("Weight (kg): ")

    print("\nActivity Levels:")
    for key, (label, mul) in ACTIVITY_LEVELS.items():
        print(f" {key}) {label}")
    act = input("Choose activity 1-5 (default 2): ").strip()
    if act not in ACTIVITY_LEVELS:
        act = "2"
    act_label, act_mul = ACTIVITY_LEVELS[act]

    # Calculations
    bmi = calculate_bmi(weight, height_m)
    cat = bmi_category(bmi)
    bmr = calculate_bmr(gender, weight, height_cm, age)
    tdee = tdee_from_bmr(bmr, act_mul)
    water_l = water_intake_liters(weight)

    # Output
    print("\n--- Results ---")
    if name:
        print(f"Name: {name}")
    print(f"Age: {age} years")
    print(f"Gender: {gender}")
    print(f"Height: {height_cm:.1f} cm")
    print(f"Weight: {weight:.1f} kg")
    print(f"BMI: {bmi:.2f} ({cat})")
    print(f"BMR (Mifflin–St Jeor): {bmr:.0f} kcal/day")
    print(f"Estimated Daily Calories (TDEE) [{act_label}]: {tdee:.0f} kcal/day")
    print(f"Recommended Water Intake: {water_l:.2f} L/day")

    save = input("\nSave this entry to history? (y/n): ").strip().lower()
    if save == "y":
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
            "activity": act_label,
        }
        save_entry(row)
    else:
        print("Not saved. Bye!")

if __name__ == "__main__":
    main()
