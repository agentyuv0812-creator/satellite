"""
Pipeline Scheduler Daemon
Runs provenanced multi-facility updates over 'methode' and 'aerostar'.
"""

import os
import sys
import time
import logging

sys.path.append(os.path.dirname(__file__))

from backfill import run_backfill_for_facility

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_daily_update():
    """Execute pipeline sync for all facilities."""
    logging.info("Starting operational intelligence pipeline sync...")
    for facility in ["methode", "aerostar"]:
        try:
            run_backfill_for_facility(facility)
        except Exception as e:
            logging.error(f"Error syncing facility '{facility}': {e}")


def daemon_loop(interval_seconds=86400):
    """Continuous update loop."""
    logging.info(f"Scheduler daemon started. Running updates every {interval_seconds}s...")
    while True:
        run_daily_update()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_loop()
    else:
        run_daily_update()
