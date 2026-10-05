"""
Daily Pipeline Scheduler & Automated Sync Daemon
Appends daily metrics, queries live or fixture sources, updates SQLite,
and refreshes JSON datastore for the Methode Electronics Operational Dashboard.
"""

import os
import sys
import time
import datetime
import logging

# Add src to python path if executing directly
sys.path.append(os.path.dirname(__file__))

from backfill import run_backfill

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_daily_update():
    """Execute daily update cycle."""
    logging.info("Starting daily operational intelligence pipeline update...")
    try:
        data = run_backfill(days_back=42)
        kpis = data.get("kpis", {})
        logging.info("Update complete. Latest KPIs:")
        logging.info(f"  Activity Index: {kpis.get('current_composite_index')} ({kpis.get('status_label')})")
        logging.info(f"  Gate Congestion: {kpis.get('gate_congestion_pct')}%")
        logging.info(f"  30d Export Tonnage: {kpis.get('trailing_30d_export_mt')} MT")
        return True
    except Exception as e:
        logging.error(f"Error during pipeline execution: {e}")
        return False


def daemon_loop(interval_seconds=86400):
    """Run pipeline on a continuous daily schedule."""
    logging.info(f"Scheduler daemon started. Will run updates every {interval_seconds} seconds.")
    while True:
        run_daily_update()
        logging.info(f"Sleeping for {interval_seconds} seconds until next scheduled run...")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_loop()
    else:
        run_daily_update()
