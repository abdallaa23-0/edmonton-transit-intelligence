import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
files = ["routes.csv", "stops.csv","stop_times.csv"]
print("Edmonton Transit Service Intelligence")
print("="*50)
for filename in files:
    path = DATA_DIR / filename

    print(f"\n📄 {filename}")

    if not path.exists():
        print("❌ File not found")
        continue

    df = pd.read_csv(path)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))

    print("-" * 50)