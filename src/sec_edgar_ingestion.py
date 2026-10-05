"""
SEC EDGAR Telemetry Ingestion Module
Queries official US Securities and Exchange Commission API (data.sec.gov)
for Methode Electronics Inc. (NYSE: MEI / CIK: 0000065270).

User-Agent: Velocla Research yuvarajpremlal@gmail.com
"""

import os
import json
import logging
import datetime
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

SEC_CIK = "0000065270"  # CIK for METHODE ELECTRONICS INC
SEC_FACTS_URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{SEC_CIK}.json"
HEADERS = {"User-Agent": "Velocla Research yuvarajpremlal@gmail.com"}


def fetch_sec_telemetry(facility_key="methode"):
    """
    Fetch verified XBRL financial facts from US SEC EDGAR API.
    For Aerostar (private company): returns null with explanation.
    """
    retrieved_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if facility_key.lower() == "aerostar":
        return {
            "company_name": "Aerostar Manufacturing",
            "ticker": None,
            "cik": None,
            "status": "Private company – no public SEC filings available",
            "inventory": None,
            "revenue": None,
            "provenance": {
                "source": "US SEC EDGAR API",
                "url": SEC_FACTS_URL,
                "retrieved_at": retrieved_at,
                "observed_at": None,
                "note": "Private entity not subject to SEC public disclosure rules"
            }
        }

    try:
        logging.info(f"Querying SEC EDGAR API for CIK {SEC_CIK} (Methode Electronics Inc.)...")
        res = requests.get(SEC_FACTS_URL, headers=HEADERS, timeout=12)
        if res.status_code != 200:
            logging.error(f"SEC EDGAR API returned HTTP {res.status_code}")
            return {
                "company_name": "METHODE ELECTRONICS INC",
                "ticker": "MEI",
                "cik": SEC_CIK,
                "status": f"Source unavailable (HTTP {res.status_code})",
                "inventory": None,
                "revenue": None,
                "provenance": {
                    "source": "US SEC EDGAR API",
                    "url": SEC_FACTS_URL,
                    "retrieved_at": retrieved_at,
                    "observed_at": None
                }
            }

        facts_data = res.json()
        entity_name = facts_data.get("entityName", "METHODE ELECTRONICS INC")
        gaap_facts = facts_data.get("facts", {}).get("us-gaap", {})

        # 1. Parse Inventory (InventoryNet)
        inventory_metric = None
        if "InventoryNet" in gaap_facts:
            inv_units = gaap_facts["InventoryNet"].get("units", {}).get("USD", [])
            valid_inv = [u for u in inv_units if u.get("form") in ["10-K", "10-Q"] and u.get("end")]
            if valid_inv:
                valid_inv.sort(key=lambda x: x.get("end", ""))
                latest_inv = valid_inv[-1]
                inventory_metric = {
                    "val": float(latest_inv["val"]),
                    "currency": "USD",
                    "form": latest_inv.get("form"),
                    "period_end": latest_inv.get("end"),
                    "accession_number": latest_inv.get("accn"),
                    "filed_date": latest_inv.get("filed"),
                    "provenance": {
                        "source": "US SEC EDGAR API (us-gaap/InventoryNet)",
                        "url": SEC_FACTS_URL,
                        "retrieved_at": retrieved_at,
                        "observed_at": latest_inv.get("end")
                    }
                }

        # 2. Parse Quarterly Revenue
        revenue_metric = None
        rev_tag = "RevenueFromContractWithCustomerExcludingAssessedTax" if "RevenueFromContractWithCustomerExcludingAssessedTax" in gaap_facts else "Revenues"
        if rev_tag in gaap_facts:
            rev_units = gaap_facts[rev_tag].get("units", {}).get("USD", [])
            valid_rev = [u for u in rev_units if u.get("form") in ["10-K", "10-Q"] and u.get("fp") in ["Q1", "Q2", "Q3", "Q4"] and u.get("end")]
            if valid_rev:
                valid_rev.sort(key=lambda x: x.get("end", ""))
                latest_rev = valid_rev[-1]
                revenue_metric = {
                    "val": float(latest_rev["val"]),
                    "currency": "USD",
                    "form": latest_rev.get("form"),
                    "period_fiscal_quarter": latest_rev.get("fp"),
                    "period_start": latest_rev.get("start"),
                    "period_end": latest_rev.get("end"),
                    "accession_number": latest_rev.get("accn"),
                    "filed_date": latest_rev.get("filed"),
                    "provenance": {
                        "source": f"US SEC EDGAR API (us-gaap/{rev_tag})",
                        "url": SEC_FACTS_URL,
                        "retrieved_at": retrieved_at,
                        "observed_at": latest_rev.get("end")
                    }
                }

        return {
            "company_name": entity_name,
            "ticker": "MEI",
            "cik": SEC_CIK,
            "status": "Available",
            "inventory": inventory_metric,
            "revenue": revenue_metric,
            "provenance": {
                "source": "US SEC EDGAR API",
                "url": SEC_FACTS_URL,
                "retrieved_at": retrieved_at,
                "observed_at": latest_inv.get("end") if inventory_metric else None
            }
        }

    except Exception as e:
        logging.error(f"Error querying SEC EDGAR API: {e}")
        return {
            "company_name": "METHODE ELECTRONICS INC",
            "ticker": "MEI",
            "cik": SEC_CIK,
            "status": f"Source unavailable ({e})",
            "inventory": None,
            "revenue": None,
            "provenance": {
                "source": "US SEC EDGAR API",
                "url": SEC_FACTS_URL,
                "retrieved_at": retrieved_at,
                "observed_at": None
            }
        }


if __name__ == "__main__":
    sec_data = fetch_sec_telemetry("methode")
    print(json.dumps(sec_data, indent=2))
