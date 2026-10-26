
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "realtime_stop_updates.csv"


def main():
    df = pd.read_csv(
        DATA_FILE,
        dtype={
            "trip_id": "string",
            "route_id": "string",
            "stop_id": "string",
            "stop_sequence": "string",
        },
    )

    print("=" * 65)
    print("TRANSITCAST DATA QUALITY CHECK")
    print("=" * 65)

    print(f"\nTotal rows: {len(df):,}")

    # Missing trip identifiers
    missing_trip = df["trip_id"].isna() | (
        df["trip_id"].str.strip() == ""
    )
    print(f"\nRows missing trip ID: {missing_trip.sum():,}")
    print(f"Rows with trip ID: {(~missing_trip).sum():,}")

    print("\n--- Duplicate key investigation ---")
    keys = ["snapshot_file", "trip_id", "stop_id", "stop_sequence"]

    identifiable = df.loc[~missing_trip]
    duplicate_mask = identifiable.duplicated(subset=keys, keep=False)

    print(
        "Rows participating in duplicate keys "
        f"(only rows with trip IDs): {duplicate_mask.sum():,}"
    )

    if duplicate_mask.any():
        print("\nExample duplicate keys:")
        print(
            identifiable.loc[duplicate_mask, keys]
            .sort_values(keys)
            .head(12)
            .to_string(index=False)
        )

    print("\n--- Delay label coverage ---")
    for column in [
        "departure_delay_seconds",
        "arrival_delay_seconds",
    ]:
        delays = pd.to_numeric(df[column], errors="coerce").dropna()
        print(f"{column}: {len(delays):,} labels")

        if len(delays):
            print(
                f"  Median: {delays.median():.1f}s | "
                f"Mean: {delays.mean():.1f}s | "
                f"Min: {delays.min():.1f}s | "
                f"Max: {delays.max():.1f}s"
            )

    # Inspect extreme departure-delay values; don't remove them yet.
    departure_delay = pd.to_numeric(
        df["departure_delay_seconds"], errors="coerce"
    )

    extreme = df.loc[
        departure_delay.abs() > 3600,
        [
            "snapshot_file",
            "feed_timestamp_utc",
            "trip_id",
            "route_id",
            "stop_id",
            "stop_sequence",
            "departure_prediction_utc",
            "departure_delay_seconds",
        ],
    ].copy()

    print("\n--- Departure delays beyond +/- 1 hour ---")
    print(f"Count: {len(extreme):,}")

    if not extreme.empty:
        print(extreme.head(15).to_string(index=False))

    # Check the schedule files before attempting to join them.
    print("\n--- Scheduled data files ---")

    for filename in [
        "routes.csv",
        "stops.csv",
        "stop_times.csv",
    ]:
        path = ROOT / "data" / filename

        if path.exists():
            schedule_df = pd.read_csv(path, dtype=str)
            print(
                f"{filename}: {len(schedule_df):,} rows, "
                f"{len(schedule_df.columns)} columns"
            )

    print("\nAudit complete.")


if __name__ == "__main__":
    main()
