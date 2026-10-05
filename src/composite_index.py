"""
Composite Activity Index Engine for Methode Electronics (NYSE: MEI)
Calculates the daily 0-100 Logistics Activity Index:
Index = 0.35 * TrafficScore + 0.35 * SatVarianceScore + 0.30 * ExportScore
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def calculate_composite_index(traffic_congestion_pct, sat_yard_variance, sat_utilization_pct, rolling_export_mt_30d):
    """
    Calculate normalized 0-100 Composite Logistics Activity Index.
    
    Parameters:
    - traffic_congestion_pct (float): 0 to 100 (% of free-flow speed reduction during peak/shift hours)
    - sat_yard_variance (float): Pixel variance in holding yard (typically 0.020 to 0.080)
    - sat_utilization_pct (float): Trailer yard occupancy percentage (0 to 100%)
    - rolling_export_mt_30d (float): Trailing 30-day tonnage (typically 150 to 350 MT)
    
    Returns:
    - dict with overall composite index, status rating, and sub-score components.
    """
    # 1. Traffic Congestion Sub-Score (0 to 100)
    # Higher congestion near plant gates correlates with high truck dispatch volume
    traffic_score = min(100.0, max(0.0, traffic_congestion_pct * 1.1))

    # 2. Satellite Variance & Utilization Sub-Score (0 to 100)
    # Variance (0.02 to 0.08) mapped to 0-100 + Yard utilization
    var_score = min(100.0, (sat_yard_variance / 0.075) * 100.0)
    util_score = min(100.0, sat_utilization_pct)
    sat_score = (0.5 * var_score) + (0.5 * util_score)

    # 3. Export Volume Velocity Sub-Score (0 to 100)
    # Baseline benchmark = 250 MT trailing 30 days
    export_score = min(100.0, (rolling_export_mt_30d / 300.0) * 100.0)

    # Composite Index Math
    raw_composite = (0.35 * traffic_score) + (0.35 * sat_score) + (0.30 * export_score)
    composite_index = round(min(100.0, max(0.0, raw_composite)), 1)

    # Status Rating
    if composite_index >= 75:
        status_label = "Surging / Heavy Gate Dispatch"
        status_color = "#10b981" # Green accent
    elif composite_index >= 55:
        status_label = "Optimal Production & Logistics Flow"
        status_color = "#38bdf8" # Blue accent
    elif composite_index >= 35:
        status_label = "Moderate Activity"
        status_color = "#f59e0b" # Amber accent
    else:
        status_label = "Subdued / Idle Capacity"
        status_color = "#ef4444" # Red accent

    return {
        "composite_index": composite_index,
        "status_label": status_label,
        "status_color": status_color,
        "sub_scores": {
            "traffic_congestion_score": round(traffic_score, 1),
            "satellite_activity_score": round(sat_score, 1),
            "export_velocity_score": round(export_score, 1)
        }
    }


if __name__ == "__main__":
    result = calculate_composite_index(
        traffic_congestion_pct=64.2,
        sat_yard_variance=0.058,
        sat_utilization_pct=82.0,
        rolling_export_mt_30d=245.8
    )
    print("Composite Index Result:")
    print(result)
