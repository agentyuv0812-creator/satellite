"""
STAC Ingestion Module - Real Sentinel-2 Satellite Metadata & Assets
Queries Microsoft Planetary Computer STAC API for Sentinel-2 L2A scenes over:
1. Methode Electronics (Apodaca, MX: [-100.138, 25.775, -100.122, 25.785])
2. Aerostar Manufacturing (Romulus, MI: [-83.401, 42.203, -83.385, 42.213])

No fabricated formulas, azimuth calculations, or trailer estimates.
"""

import os
import json
import logging
import datetime
import pystac_client
import planetary_computer as pc

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

FACILITY_BBOXES = {
    "methode": [-100.138, 25.775, -100.122, 25.785],
    "aerostar": [-83.401, 42.203, -83.385, 42.213]
}


def fetch_sentinel_scenes(facility_key="methode", days_back=60):
    """
    Fetch verified Sentinel-2 L2A satellite scenes from Microsoft Planetary Computer STAC API.
    Returns list of items containing ONLY verified STAC metadata and signed asset links.
    """
    facility_key_lower = facility_key.lower() if facility_key else "methode"
    bbox = FACILITY_BBOXES.get(facility_key_lower, FACILITY_BBOXES["methode"])
    retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    end_date = datetime.datetime.now(datetime.timezone.utc).date()
    start_date = end_date - datetime.timedelta(days=days_back)
    datetime_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

    try:
        logging.info(f"Querying Planetary Computer STAC API for '{facility_key_lower}' ({datetime_range})...")
        catalog = pystac_client.Client.open(STAC_API_URL, modifier=pc.sign_inplace)
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=datetime_range,
            query={"eo:cloud_cover": {"lt": 35}},
            limit=25
        )
        items = list(search.items())
        logging.info(f"Retrieved {len(items)} verified Sentinel-2 scenes for '{facility_key_lower}'.")

        parsed_scenes = []
        seen_dates = set()

        for item in items:
            date_str = item.datetime.strftime("%Y-%m-%d")
            if date_str in seen_dates:
                continue
            seen_dates.add(date_str)

            props = item.properties
            cloud_cover = props.get("eo:cloud_cover")
            nodata_pixel_pct = props.get("s2:nodata_pixel_percentage")

            # Extract signed asset links safely
            b04_asset = item.assets.get("B04")
            b08_asset = item.assets.get("B08")
            b04_url = b04_asset.href if b04_asset else None
            b08_url = b08_asset.href if b08_asset else None

            parsed_scenes.append({
                "scene_id": item.id,
                "date": date_str,
                "cloud_cover_pct": float(cloud_cover) if cloud_cover is not None else None,
                "nodata_pixel_pct": float(nodata_pixel_pct) if nodata_pixel_pct is not None else None,
                "b04_url": b04_url,
                "b08_url": b08_url,
                "provenance": {
                    "source": "Microsoft Planetary Computer STAC API (sentinel-2-l2a)",
                    "url": f"{STAC_API_URL}/collections/sentinel-2-l2a/items/{item.id}",
                    "retrieved_at": retrieved_at,
                    "observed_at": date_str
                }
            })

        parsed_scenes.sort(key=lambda x: x["date"])
        return parsed_scenes

    except Exception as e:
        logging.error(f"Error querying STAC API for '{facility_key_lower}': {e}")
        return []


if __name__ == "__main__":
    scenes = fetch_sentinel_scenes("methode")
    print(f"Retrieved {len(scenes)} verified scenes:")
    for s in scenes[:3]:
        print(json.dumps(s, indent=2))
