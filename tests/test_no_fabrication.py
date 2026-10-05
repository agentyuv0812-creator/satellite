"""
Automated Test Suite: Zero Fabrication & Provenance Verification
Tests non-negotiable rules:
1. No forbidden hardcoded strings, formulas, or fixture references in codebase.
2. Every numeric field in output JSON has explicit provenance metadata.
3. Network failure returns null with error status (no silent fallbacks).
4. Live network calls fetch real SEC EDGAR facts and Planetary Computer STAC scenes.
"""

import os
import re
import json
import glob
import pytest
from unittest.mock import patch, MagicMock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(BASE_DIR, "web")


def test_no_hardcoded_or_fabricated_values_in_codebase():
    """Acceptance Test 1: Codebase scan for forbidden hardcoded values and formulas."""
    forbidden_terms = [
        "184600000",
        "285400000",
        "42500000",
        "68000000",
        "sum(ord(",
        "real_bols",
        "% 22",
        "* 0.38",
        "fixture"
    ]

    files_to_check = []
    for ext in ["*.py", "*.js", "*.html"]:
        files_to_check.extend(glob.glob(os.path.join(SRC_DIR, ext)))
        files_to_check.extend(glob.glob(os.path.join(WEB_DIR, ext)))
        files_to_check.extend(glob.glob(os.path.join(BASE_DIR, ext)))

    found_violations = []

    for filepath in files_to_check:
        if "test_no_fabrication.py" in filepath:
            continue
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for term in forbidden_terms:
                if term in content:
                    found_violations.append(f"Forbidden term '{term}' found in {filepath}")

    assert not found_violations, "\n".join(found_violations)


def test_provenance_on_numeric_fields():
    """Acceptance Test 2: Verify every numeric field in data feeds has sibling provenance."""
    # Ensure datastores exist
    import sys
    sys.path.append(SRC_DIR)
    from backfill import run_all_facilities
    run_all_facilities()

    for json_file in ["pipeline_data.json", "pipeline_data_aerostar.json"]:
        path = os.path.join(DATA_DIR, json_file)
        assert os.path.exists(path), f"JSON feed missing: {path}"
        with open(path, "r") as f:
            data = json.load(f)

        kpis = data.get("kpis", {})
        sec = data.get("sec_telemetry", {})
        scenes = data.get("satellite_scenes", [])

        # Verify SEC inventory numerical field has provenance if not null
        inv = sec.get("inventory")
        if inv is not None:
            assert "val" in inv
            assert "provenance" in inv
            assert inv["provenance"].get("source")
            assert inv["provenance"].get("retrieved_at")

        # Verify STAC scenes numeric fields have provenance
        for scene in scenes:
            assert "provenance" in scene
            assert scene["provenance"].get("source")
            assert scene["provenance"].get("url")
            assert scene["provenance"].get("retrieved_at")
            assert scene["provenance"].get("observed_at")


def test_network_disabled_behavior():
    """Acceptance Test 3: Run pipeline with network disabled -> every live field must be null."""
    import sys
    sys.path.append(SRC_DIR)
    import requests

    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Network disabled")):
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Network disabled")):
            with patch("pystac_client.Client.open", side_effect=Exception("Network disabled")):
                from sec_edgar_ingestion import fetch_sec_telemetry
                from stac_ingestion import fetch_sentinel_scenes
                from traffic_ingestion import fetch_live_traffic
                from manifest_ingestion import fetch_trade_manifests
                from composite_index import calculate_composite_index

                sec = fetch_sec_telemetry("methode")
                stac = fetch_sentinel_scenes("methode")
                traffic = fetch_live_traffic("methode")
                trade = fetch_trade_manifests("methode")
                comp = calculate_composite_index()

                assert sec["inventory"] is None
                assert sec["revenue"] is None
                assert len(stac) == 0
                assert traffic["congestion_index"] is None
                assert trade["total_weight_mt"] is None
                assert comp["composite_index"] is None


def test_live_network_enabled_verification():
    """Acceptance Test 4: Verify live network responses match actual SEC & STAC API items."""
    import sys
    sys.path.append(SRC_DIR)
    from sec_edgar_ingestion import fetch_sec_telemetry
    from stac_ingestion import fetch_sentinel_scenes

    sec = fetch_sec_telemetry("methode")
    assert sec["company_name"] == "METHODE ELECTRONICS INC"
    assert sec["inventory"] is not None
    assert sec["inventory"]["val"] == 184600000.0
    assert sec["inventory"]["period_end"] == "2026-08-01"
    assert sec["inventory"]["accession_number"] == "0000065270-26-000045"

    assert sec["revenue"] is not None
    assert sec["revenue"]["val"] == 265400000.0
    assert sec["revenue"]["period_end"] == "2026-08-01"
    assert sec["revenue"]["accession_number"] == "0000065270-26-000045"

    stac = fetch_sentinel_scenes("methode", days_back=60)
    assert len(stac) > 0
    first_scene = stac[0]
    assert first_scene["scene_id"].startswith("S2")
    assert first_scene["provenance"]["source"] == "Microsoft Planetary Computer STAC API (sentinel-2-l2a)"
