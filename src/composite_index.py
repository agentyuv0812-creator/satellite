"""
Composite Activity Index Engine - Disabled Policy
Composite index formula disabled until at least two live, validated telemetry inputs exist.
"""

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def calculate_composite_index(traffic_data=None, sat_data=None, trade_data=None):
    """
    Composite Index disabled. Returns null values and status 'disabled'.
    """
    return {
        "status": "disabled",
        "reason": "Composite index calculation disabled until required live telemetry streams are active",
        "composite_index": None,
        "status_label": "Not calculated",
        "status_color": "#6b7280",
        "sub_scores": {
            "traffic_congestion_score": None,
            "satellite_activity_score": None,
            "export_velocity_score": None
        }
    }


if __name__ == "__main__":
    print(calculate_composite_index())
