
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "realtime_stop_updates.csv"


def main():
    df = pd.read_csv(
        DATA_FILE,
        dtype={
            "stop_id": "string",
            "entity_id": "string",
            "trip_id": "string",
            "route_id": "string",
        },
        low_memory=False,
    )

    for column in ["arrival_delay_seconds", "departure_delay_seconds"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    print("=" * 65)
    print("TRANSITCAST SNAPSHOT COMPARISON")
    print("=" * 65)

    for filename, group in df.groupby("snapshot_file", sort=True):
        print(f"\n--- {filename} ---")
        print(f"Rows: {len(group):,}")
        print(f"Entities: {group['entity_id'].nunique():,}")
        print(f"Routes: {group['route_id'].nunique():,}")

        for column in [
            "arrival_delay_seconds",
            "departure_delay_seconds",
        ]:
            values = group[column].dropna()
            print(f"\n{column}:")
            print(f"  Available: {len(values):,} ({len(values) / len(group) * 100:.2f}%)")

            if not values.empty:
                print(f"  Median: {values.median():.1f} seconds")
                print(f"  Mean: {values.mean():.1f} seconds")
                print(f"  Absolute delay > 1 hour: {(values.abs() > 3600).sum():,}")

        feed_time = pd.to_datetime(
            group["feed_timestamp_utc"], utc=True, errors="coerce"
        )
        prediction_time = pd.to_datetime(
            group["departure_prediction_utc"], utc=True, errors="coerce"
        )

        valid = feed_time.notna() & prediction_time.notna()
        differences = (
            feed_time[valid] - prediction_time[valid]
        ).dt.total_seconds()

        print("\nFeed time minus predicted departure time:")
        if len(differences):
            print(f"  Predictions earlier than feed by > 1 hour: {(differences > 3600).sum():,}")
            print(f"  Predictions later than feed by > 1 hour: {(differences < -3600).sum():,}")
        else:
            print("  No comparable timestamps")

    print("\nComparison complete.")


if __name__ == "__main__":
    main()
