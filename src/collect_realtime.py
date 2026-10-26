import requests
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
REALTIME_DIR = DATA_DIR / "realtime"

REALTIME_DIR.mkdir(parents=True, exist_ok=True)

URL = "http://gtfs.edmonton.ca/TMGTFSRealTimeWebService/TripUpdate/TripUpdates.pb"

print("Edmonton Transit Service Intelligence")
print("=" * 50)
print("Collecting ETS real-time trip updates...")

timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

response = requests.get(URL, timeout=30)
response.raise_for_status()

filename = REALTIME_DIR / f"trip_updates_{timestamp}.pb"
filename.write_bytes(response.content)

print(f"✓ Saved: {filename}")
print(f"✓ Size: {len(response.content):,} bytes")
print("Collection complete!")