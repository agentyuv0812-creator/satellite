"""
Telemetry Ingestion & Datastore Sync Engine
Populates SQLite datastores and exports JSON feeds with provenanced observations.
No forward filling, daily data interpolation, or fabricated values.
"""

import os
import json
import sqlite3
import datetime
import logging
from stac_ingestion import fetch_sentinel_scenes
from sec_edgar_ingestion import fetch_sec_telemetry
from traffic_ingestion import fetch_live_traffic
from manifest_ingestion import fetch_trade_manifests
from composite_index import calculate_composite_index

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_db_and_json_paths(facility_key):
    if facility_key.lower() == "aerostar":
        db_path = os.path.join(BASE_DIR, "..", "data", "aerostar_intelligence.db")
        json_path = os.path.join(BASE_DIR, "..", "data", "pipeline_data_aerostar.json")
    else:
        db_path = os.path.join(BASE_DIR, "..", "data", "methode_intelligence.db")
        json_path = os.path.join(BASE_DIR, "..", "data", "pipeline_data.json")
    return db_path, json_path


def init_database(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS satellite_metrics")
    cursor.execute("DROP TABLE IF EXISTS traffic_metrics")
    cursor.execute("DROP TABLE IF EXISTS manifest_records")
    cursor.execute("DROP TABLE IF EXISTS daily_composite_index")

    cursor.execute("""
    CREATE TABLE satellite_metrics (
        date TEXT PRIMARY KEY,
        scene_id TEXT,
        cloud_cover_pct REAL,
        nodata_pixel_pct REAL,
        b04_url TEXT,
        b08_url TEXT,
        source TEXT,
        url TEXT,
        retrieved_at TEXT,
        observed_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE traffic_metrics (
        date TEXT PRIMARY KEY,
        status TEXT,
        reason TEXT,
        current_speed_kmh REAL,
        free_flow_speed_kmh REAL,
        congestion_index REAL,
        retrieved_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE manifest_records (
        status TEXT,
        reason TEXT,
        retrieved_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE daily_composite_index (
        status TEXT,
        composite_index REAL,
        status_label TEXT
    )
    """)

    conn.commit()
    conn.close()


def run_backfill_for_facility(facility_key="methode", days_back=60):
    facility_key_lower = facility_key.lower() if facility_key else "methode"
    db_path, json_path = get_db_and_json_paths(facility_key_lower)
    init_database(db_path)

    retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Fetch Verified STAC Satellite Scenes (No daily interpolation!)
    stac_scenes = fetch_sentinel_scenes(facility_key=facility_key_lower, days_back=days_back)

    # 2. Fetch Verified SEC EDGAR Data
    sec_data = fetch_sec_telemetry(facility_key=facility_key_lower)

    # 3. Poll Live Traffic
    traffic_data = fetch_live_traffic(facility_key=facility_key_lower)

    # 4. Fetch Trade Manifest Status
    trade_data = fetch_trade_manifests(facility_key=facility_key_lower)

    # 5. Composite Index (Disabled)
    composite_data = calculate_composite_index(traffic_data, stac_scenes, trade_data)

    # Persist satellite scenes to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for s in stac_scenes:
        prov = s.get("provenance", {})
        cursor.execute("""
        INSERT OR REPLACE INTO satellite_metrics
        (date, scene_id, cloud_cover_pct, nodata_pixel_pct, b04_url, b08_url, source, url, retrieved_at, observed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            s["date"], s["scene_id"], s["cloud_cover_pct"], s["nodata_pixel_pct"],
            s.get("b04_url"), s.get("b08_url"),
            prov.get("source"), prov.get("url"), prov.get("retrieved_at"), prov.get("observed_at")
        ))

    conn.commit()
    conn.close()

    facility_meta = {
        "methode": {
            "facility": "Methode Electronics Planta 2",
            "location": "Apodaca, Monterrey, NL, Mexico",
            "coordinates": {"lat": 25.780, "lon": -100.130},
            "bbox": [-100.138, 25.775, -100.122, 25.785],
            "verification_source": "OpenStreetMap / Public Facility Registry"
        },
        "aerostar": {
            "facility": "Aerostar Manufacturing HQ & Plant",
            "location": "28275 Northline Rd, Romulus, Detroit Metro, MI, USA",
            "coordinates": {"lat": 42.208, "lon": -83.393},
            "bbox": [-83.401, 42.203, -83.385, 42.213],
            "verification_source": "OpenStreetMap / Public Corporate Directory"
        }
    }

    mode_status = {
        "sentinel2_scenes": "live" if len(stac_scenes) > 0 else "source unavailable",
        "sec": "live" if sec_data.get("inventory") or sec_data.get("revenue") else "not connected",
        "traffic": traffic_data.get("status", "not connected"),
        "trade": trade_data.get("status", "not connected")
    }

    export_payload = {
        "metadata": {
            "facility_key": facility_key_lower,
            "facility_info": facility_meta.get(facility_key_lower, facility_meta["methode"]),
            "last_updated": retrieved_at,
            "data_source_mode": mode_status
        },
        "sec_telemetry": sec_data,
        "kpis": {
            "composite_index": composite_data["composite_index"],
            "composite_status_label": composite_data["status_label"],
            "gate_congestion_pct": traffic_data.get("congestion_index"),
            "traffic_status": traffic_data.get("status"),
            "traffic_reason": traffic_data.get("reason"),
            "traffic_provenance": traffic_data.get("provenance"),
            "latest_satellite_revisit_date": stac_scenes[-1]["date"] if stac_scenes else None,
            "latest_satellite_cloud_cover": stac_scenes[-1]["cloud_cover_pct"] if stac_scenes else None,
            "latest_satellite_scene_id": stac_scenes[-1]["scene_id"] if stac_scenes else None,
            "latest_satellite_provenance": stac_scenes[-1]["provenance"] if stac_scenes else None,
            "inventory": sec_data.get("inventory"),
            "revenue": sec_data.get("revenue"),
            "sec_provenance": sec_data.get("provenance")
        },
        "satellite_scenes": stac_scenes,
        "manifests": trade_data
    }

    with open(json_path, "w") as f:
        json.dump(export_payload, f, indent=2)

    logging.info(f"Facility '{facility_key_lower}' sync complete. Saved {len(stac_scenes)} provenanced scenes to {json_path}")
    return export_payload


def run_all_facilities():
    run_backfill_for_facility("methode")
    run_backfill_for_facility("aerostar")


if __name__ == "__main__":
    run_all_facilities()
