
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

    key = [
        "snapshot_file",
        "entity_id",
        "descriptor_type",
        "stop_id",
        "stop_sequence",
    ]

    repeated = df[df.duplicated(subset=key, keep=False)].copy()

    print("=" * 60)
    print("REPEATED STOP-UPDATE INSPECTION")
    print("=" * 60)
    print(f"Rows in repeated keys: {len(repeated):,}")
    print(f"Distinct repeated keys: {repeated[key].drop_duplicates().shape[0]:,}")

    if not repeated.empty:
        compare_columns = [
            "arrival_prediction_utc",
            "arrival_delay_seconds",
            "departure_prediction_utc",
            "departure_delay_seconds",
        ]

        groups = repeated.groupby(key, dropna=False)
        identical = 0
        different = 0

        for _, group in groups:
            if len(group[compare_columns].drop_duplicates()) == 1:
                identical += 1
            else:
                different += 1

        print(f"Keys with identical prediction fields: {identical:,}")
        print(f"Keys with differing prediction fields: {different:,}")

        print("\nSample repeated records:")
        print(
            repeated[
                key + compare_columns
            ].head(12).to_string(index=False)
        )

    print("\n" + "=" * 60)
    print("EXTREME DELAY RECORDS")
    print("=" * 60)

    for column in [
        "arrival_delay_seconds",
        "departure_delay_seconds",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        extreme = df[df[column].abs() > 3600]

        print(f"\n{column}: {len(extreme):,} records over 1 hour in magnitude")

        if not extreme.empty:
            columns = [
                "snapshot_file",
                "feed_timestamp_utc",
                "entity_id",
                "descriptor_type",
                "trip_id",
                "route_id",
                "stop_id",
                "stop_sequence",
                "departure_prediction_utc",
                column,
            ]
            columns = [c for c in columns if c in extreme.columns]
            print(extreme[columns].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
