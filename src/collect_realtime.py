
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# Resolve paths relative to the project folder, not the terminal's location.
PROJECT_DIR = Path(__file__).resolve().parent.parent
REALTIME_DIR = PROJECT_DIR / "data" / "realtime"
REALTIME_DIR.mkdir(parents=True, exist_ok=True)

URL = (
    "http://gtfs.edmonton.ca/"
    "TMGTFSRealTimeWebService/TripUpdate/TripUpdates.pb"
)

INTERVAL_SECONDS = 60
TIMEOUT_SECONDS = 30

# Record collection results in a persistent log file.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s UTC | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(REALTIME_DIR / "collection.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

def collect_snapshot(session):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = REALTIME_DIR / f"trip_updates_{timestamp}.pb"
    temp_filename = filename.with_suffix(".tmp")

    response = session.get(URL, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()

    if not response.content:
        raise ValueError("The transit feed returned an empty response.")

    # Write to a temporary file first, then finalize the snapshot.
    temp_filename.write_bytes(response.content)
    temp_filename.replace(filename)

    logging.info(
        "Saved %s (%s bytes)",
        filename.name,
        f"{len(response.content):,}",
    )

def main():
    logging.info("TransitCast collector started.")
    logging.info("Collection interval: %s seconds", INTERVAL_SECONDS)
    logging.info("Saving snapshots to: %s", REALTIME_DIR)
    logging.info("Press Ctrl+C to stop.")

    next_collection = time.monotonic()

    try:
        with requests.Session() as session:
            while True:
                try:
                    collect_snapshot(session)
                except (requests.RequestException, OSError, ValueError) as exc:
                    logging.error("Snapshot failed: %s", exc)

                # Keep a regular schedule without accumulating request-time drift.
                next_collection += INTERVAL_SECONDS
                wait_seconds = next_collection - time.monotonic()

                if wait_seconds <= 0:
                    logging.warning(
                        "Collection took longer than expected; "
                        "starting the next attempt shortly."
                    )
                    next_collection = time.monotonic()
                    wait_seconds = 0

                time.sleep(wait_seconds)

    except KeyboardInterrupt:
        logging.info("Collector stopped by user.")

if __name__ == "__main__":
    main()
