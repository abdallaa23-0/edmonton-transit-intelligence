
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "realtime_stop_updates.csv"


def main():
    df = pd.read_csv(DATA_FILE)

    print("=" * 60)
    print("TRANSITCAST REALTIME DATA AUDIT")
    print("=" * 60)

    print(f"\nRows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Snapshots: {df['snapshot_file'].nunique():,}")

    print("\n--- Rows per snapshot ---")
    print(df.groupby("snapshot_file").size().to_string())

    print("\n--- Descriptor types ---")
    print(df["descriptor_type"].value_counts(dropna=False).to_string())

    print("\n--- Missing values (%) ---")
    missing = (df.isna().mean() * 100).sort_values(ascending=False)
    print(missing.round(2).to_string())

    print("\n--- Delay statistics (seconds) ---")
    for column in [
        "arrival_delay_seconds",
        "departure_delay_seconds",
    ]:
        values = pd.to_numeric(df[column], errors="coerce").dropna()

        print(f"\n{column}:")
        if values.empty:
            print("No available values")
            continue

        print(f"  Available values: {len(values):,}")
        print(f"  Median: {values.median():.1f}")
        print(f"  Mean: {values.mean():.1f}")
        print(f"  Minimum: {values.min():.1f}")
        print(f"  Maximum: {values.max():.1f}")
        print(f"  More than 1 hour from zero: {(values.abs() > 3600).sum():,}")

    print("\n--- Delay availability by descriptor ---")
    summary = df.groupby("descriptor_type").agg(
        rows=("stop_id", "size"),
        arrival_delay_available=("arrival_delay_seconds", "count"),
        departure_delay_available=("departure_delay_seconds", "count"),
        unique_entities=("entity_id", "nunique"),
    )
    print(summary.to_string())

    print("\n--- Repeated stop-update keys ---")
    # Include entity and descriptor type so different representations
    # are not automatically treated as duplicates.
    key = [
        "snapshot_file",
        "entity_id",
        "descriptor_type",
        "stop_id",
        "stop_sequence",
    ]

    duplicates = df.duplicated(subset=key, keep=False)
    print(f"Rows participating in repeated keys: {duplicates.sum():,}")

    print("\nAudit complete.")


if __name__ == "__main__":
    main()
