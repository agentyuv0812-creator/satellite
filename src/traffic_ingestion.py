"""
Traffic Ingestion Module - Real API Polling Only
Queries TomTom Traffic Flow API when TOMTOM_API_KEY is supplied in environment.
No fabricated weekday baselines, math formulas, or ordinal hashing.
"""

import os
import json
import logging
import datetime
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOMTOM_FLOW_API_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative/10/json"
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

FACILITY_ROAD_POINTS = {
    "methode": {"lat": 25.780, "lon": -100.130, "name": "Blvd. Agua Fría (Apodaca Plant Gate)"},
    "aerostar": {"lat": 42.208, "lon": -83.393, "name": "Northline Road (Romulus Plant Gate)"}
}


def fetch_live_traffic(facility_key="methode"):
    """
    Poll TomTom Traffic Flow API if key is present.
    If no key or poll fails, returns null with status 'not connected'.
    """
    facility_key_lower = facility_key.lower() if facility_key else "methode"
    point_info = FACILITY_ROAD_POINTS.get(facility_key_lower, FACILITY_ROAD_POINTS["methode"])
    retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not TOMTOM_API_KEY:
        return {
            "status": "not connected",
            "reason": "No TOMTOM_API_KEY set in environment",
            "congestion_index": None,
            "current_speed_kmh": None,
            "free_flow_speed_kmh": None,
            "provenance": {
                "source": "TomTom Traffic Flow API",
                "url": TOMTOM_FLOW_API_URL,
                "retrieved_at": retrieved_at,
                "observed_at": None,
                "note": "API key required for live traffic flow stream"
            }
        }

    try:
        url = f"{TOMTOM_FLOW_API_URL}?point={point_info['lat']},{point_info['lon']}&key={TOMTOM_API_KEY}"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            flow_data = res.json().get("flowSegmentData", {})
            current_speed = flow_data.get("currentSpeed")
            free_flow_speed = flow_data.get("freeFlowSpeed")
            
            congestion_idx = None
            if current_speed is not None and free_flow_speed is not None and free_flow_speed > 0:
                congestion_idx = round(max(0.0, (1.0 - (current_speed / free_flow_speed)) * 100.0), 1)

            return {
                "status": "connected",
                "reason": None,
                "road_segment": point_info["name"],
                "current_speed_kmh": float(current_speed) if current_speed is not None else None,
                "free_flow_speed_kmh": float(free_flow_speed) if free_flow_speed is not None else None,
                "congestion_index": congestion_idx,
                "provenance": {
                    "source": "TomTom Traffic Flow API",
                    "url": url,
                    "retrieved_at": retrieved_at,
                    "observed_at": retrieved_at[:10]
                }
            }
        else:
            return {
                "status": f"Source unavailable (HTTP {res.status_code})",
                "reason": res.text,
                "congestion_index": None,
                "current_speed_kmh": None,
                "free_flow_speed_kmh": None,
                "provenance": {
                    "source": "TomTom Traffic Flow API",
                    "url": url,
                    "retrieved_at": retrieved_at,
                    "observed_at": None
                }
            }
    except Exception as e:
        logging.error(f"Traffic API error: {e}")
        return {
            "status": f"Source unavailable ({e})",
            "reason": str(e),
            "congestion_index": None,
            "current_speed_kmh": None,
            "free_flow_speed_kmh": None,
            "provenance": {
                "source": "TomTom Traffic Flow API",
                "url": TOMTOM_FLOW_API_URL,
                "retrieved_at": retrieved_at,
                "observed_at": None
            }
        }


if __name__ == "__main__":
    print(fetch_live_traffic("methode"))
