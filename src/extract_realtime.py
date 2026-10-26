
from pathlib import Path

import pandas as pd
from google.transit import gtfs_realtime_pb2


ROOT = Path(__file__).resolve().parent.parent
REALTIME_DIR = ROOT / "data" / "realtime"
OUTPUT_FILE = ROOT / "data" / "processed" / "realtime_stop_updates.csv"


def get_value(message, field):
    """Return a protobuf field's value when it is present."""
    if message is not None and message.HasField(field):
        return getattr(message, field)
    return None


def timestamp_to_utc(value):
    """Convert a Unix timestamp to a UTC ISO string."""
    if value is None:
        return None
    return pd.to_datetime(value, unit="s", utc=True).isoformat()


def main():
    REALTIME_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for path in sorted(REALTIME_DIR.glob("*.pb")):
        feed = gtfs_realtime_pb2.FeedMessage()

        with path.open("rb") as file:
            feed.ParseFromString(file.read())

        feed_timestamp = get_value(feed.header, "timestamp")
        feed_timestamp_utc = timestamp_to_utc(feed_timestamp)

        file_rows = 0

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            update = entity.trip_update
            trip = update.trip

            is_modified = trip.HasField("modified_trip")
            modified = trip.modified_trip if is_modified else None

            trip_id = get_value(trip, "trip_id")
            route_id = get_value(trip, "route_id")
            start_date = get_value(trip, "start_date")
            start_time = get_value(trip, "start_time")

            affected_trip_id = (
                get_value(modified, "affected_trip_id")
                if modified is not None else None
            )
            modifications_id = (
                get_value(modified, "modifications_id")
                if modified is not None else None
            )

            # Modified-trip descriptors may store start details themselves.
            if modified is not None:
                start_date = start_date or get_value(modified, "start_date")
                start_time = start_time or get_value(modified, "start_time")

            trip_update_timestamp = get_value(update, "timestamp")
            trip_update_delay = get_value(update, "delay")

            for stop in update.stop_time_update:
                arrival = (
                    stop.arrival if stop.HasField("arrival") else None
                )
                departure = (
                    stop.departure if stop.HasField("departure") else None
                )

                rows.append({
                    "snapshot_file": path.name,
                    "feed_timestamp_utc": feed_timestamp_utc,
                    "entity_id": entity.id,
                    "descriptor_type": (
                        "modified" if is_modified else "regular"
                    ),
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "affected_trip_id": affected_trip_id,
                    "modifications_id": modifications_id,
                    "start_date": start_date,
                    "start_time": start_time,
                    "trip_update_timestamp_utc": timestamp_to_utc(
                        trip_update_timestamp
                    ),
                    "trip_update_delay_seconds": trip_update_delay,
                    "stop_id": get_value(stop, "stop_id"),
                    "stop_sequence": get_value(stop, "stop_sequence"),
                    "arrival_prediction_utc": timestamp_to_utc(
                        get_value(arrival, "time") if arrival else None
                    ),
                    "arrival_delay_seconds": (
                        get_value(arrival, "delay") if arrival else None
                    ),
                    "departure_prediction_utc": timestamp_to_utc(
                        get_value(departure, "time") if departure else None
                    ),
                    "departure_delay_seconds": (
                        get_value(departure, "delay") if departure else None
                    ),
                })
                file_rows += 1

        print(f"{path.name}: extracted {file_rows:,} stop updates")

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nTotal rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Output: {OUTPUT_FILE}")

    if not df.empty:
        print("\nDescriptor counts:")
        print(df["descriptor_type"].value_counts(dropna=False).to_string())

        print("\nMissing trip identifiers:")
        print(f"trip_id: {df['trip_id'].isna().sum():,}")
        print(f"affected_trip_id: {df['affected_trip_id'].isna().sum():,}")


if __name__ == "__main__":
    main()
