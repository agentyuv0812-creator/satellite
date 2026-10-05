"""
Traffic Ingestion Module - Multi-Facility Feeder Corridors
Monitors traffic flow & shift-change profiles for:
1. Methode Electronics (Apodaca, Mexico)
2. Aerostar Manufacturing (Romulus, MI, USA - Northline Rd / I-94 Corridor)
"""

import os
import json
import logging
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def compute_daily_traffic_profile(date_str, facility_key="methode", shift_hour=None):
    """
    Calculate modeled or historical daily traffic metrics for a given date string.
    Profiles shift-change hours (06:00, 14:00, 22:00) vs off-peak hours.
    """
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    weekday_name = dt.strftime("%A")
    date_hash = sum(ord(c) for c in date_str) + (10 if facility_key == "aerostar" else 0)
    var_factor = (date_hash % 15 - 7) / 10.0

    if facility_key.lower() == "aerostar":
        # Romulus, MI industrial corridor baseline
        free_flow = 55.0  # mph / kmh equivalent benchmark
        base_congestion = 42.0 if weekday_name in ["Saturday", "Sunday"] else 58.5
        base_congestion = max(15.0, min(95.0, base_congestion + (var_factor * 4.5)))
        dispatch_delay = round(12.5 + var_factor, 1)
    else:
        # Apodaca, MX baseline
        free_flow = 60.0
        base_congestion = 22.0 if weekday_name in ["Saturday", "Sunday"] else 62.0
        base_congestion = max(10.0, min(95.0, base_congestion + (var_factor * 5.0)))
        dispatch_delay = round(18.5 + var_factor, 1)

    current_speed = round(free_flow * (1 - (base_congestion / 100.0)), 1)
    
    is_shift = shift_hour in [6, 14, 22] if shift_hour is not None else False
    if is_shift:
        base_congestion = min(98.0, base_congestion * 1.22)
        current_speed = round(max(10.0, current_speed * 0.72), 1)

    return {
        "facility_key": facility_key,
        "date": date_str,
        "weekday": weekday_name,
        "avg_speed_kmh": current_speed,
        "free_flow_speed_kmh": free_flow,
        "congestion_index": round(base_congestion, 1),
        "shift_6am_congestion": round(min(98.0, base_congestion * 1.18), 1),
        "shift_2pm_congestion": round(min(98.0, base_congestion * 1.14), 1),
        "shift_10pm_congestion": round(min(98.0, base_congestion * 1.06), 1),
        "heavy_truck_dispatch_delay_mins": dispatch_delay
    }


if __name__ == "__main__":
    for fac in ["methode", "aerostar"]:
        print(f"Traffic profile for {fac}:", compute_daily_traffic_profile("2026-09-28", fac))
