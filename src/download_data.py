import requests
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

datasets = {
    "routes.csv": "https://data.edmonton.ca/resource/d577-xky7.csv",
    "stops.csv": "https://data.edmonton.ca/resource/4vt2-8zrq.csv",
    "stop_times.csv": "https://data.edmonton.ca/resource/greh-g7ac.csv",
}

print("Edmonton Transit Intelligence")
print("=" * 45)

for filename, url in datasets.items():
    print(f"Downloading {filename}...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    file_path = DATA_DIR / filename
    file_path.write_bytes(response.content)

    print(f"✓ Saved: {file_path}")

print("=" * 45)
print("All downloads complete!")