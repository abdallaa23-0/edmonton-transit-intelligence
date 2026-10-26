import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"

PROCESSED_DIR.mkdir(exist_ok=True)

def clean_routes():
    print("Cleaning routes...")

    df = pd.read_csv(DATA_DIR / "routes.csv")

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate routes
    df = df.drop_duplicates()

    output = PROCESSED_DIR / "routes_clean.csv"
    df.to_csv(output, index=False)

    print(f"✓ Routes: {len(df):,} rows")
    print(f"✓ Saved: {output}")


def clean_stops():
    print("Cleaning stops...")

    df = pd.read_csv(DATA_DIR / "stops.csv")

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate stops
    df = df.drop_duplicates()

    output = PROCESSED_DIR / "stops_clean.csv"
    df.to_csv(output, index=False)

    print(f"✓ Stops: {len(df):,} rows")
    print(f"✓ Saved: {output}")


def clean_stop_times():
    print("Cleaning stop times...")

    df = pd.read_csv(DATA_DIR / "stop_times.csv")

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Remove duplicate records
    df = df.drop_duplicates()

    output = PROCESSED_DIR / "stop_times_clean.csv"
    df.to_csv(output, index=False)

    print(f"✓ Stop times: {len(df):,} rows")
    print(f"✓ Saved: {output}")


if __name__ == "__main__":
    print("Edmonton Transit Intelligence")
    print("=" * 50)

    clean_routes()
    clean_stops()
    clean_stop_times()

    print("=" * 50)
    print("Cleaning complete!") 