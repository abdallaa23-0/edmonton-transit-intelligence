
from pathlib import Path

from google.transit import gtfs_realtime_pb2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REALTIME_DIR = PROJECT_ROOT / "data" / "realtime"


def inspect_snapshot(file_path: Path) -> None:
    feed = gtfs_realtime_pb2.FeedMessage()

    with file_path.open("rb") as file:
        feed.ParseFromString(file.read())

    print(f"\n{'=' * 65}")
    print(f"File: {file_path.name}")
    print(f"Feed entities: {len(feed.entity)}")

    if feed.HasField("header"):
        print(f"GTFS-Realtime version: {feed.header.gtfs_realtime_version}")

        if feed.header.HasField("timestamp"):
            print(f"Feed timestamp: {feed.header.timestamp}")

    trip_updates = 0
    stop_time_updates = 0
    delays_found = 0
    arrival_predictions = 0
    departure_predictions = 0

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_updates += 1
        trip_update = entity.trip_update

        for stop_update in trip_update.stop_time_update:
            stop_time_updates += 1

            if stop_update.HasField("arrival"):
                if stop_update.arrival.HasField("delay"):
                    delays_found += 1

                if stop_update.arrival.HasField("time"):
                    arrival_predictions += 1

            if stop_update.HasField("departure"):
                if stop_update.departure.HasField("time"):
                    departure_predictions += 1

    print(f"Trip updates: {trip_updates}")
    print(f"Stop-time updates: {stop_time_updates}")
    print(f"Explicit delay values: {delays_found}")
    print(f"Predicted arrival timestamps: {arrival_predictions}")
    print(f"Predicted departure timestamps: {departure_predictions}")

    print("\nSample stop predictions:")

    shown = 0

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update

        for stop_update in trip.stop_time_update:
            if shown >= 5:
                break

            stop_id = (
                stop_update.stop_id
                if stop_update.HasField("stop_id")
                else "unknown"
            )

            print(f"\n  Trip ID: {trip.trip.trip_id}")
            print(f"  Stop ID: {stop_id}")

            if stop_update.HasField("arrival"):
                arrival = stop_update.arrival

                if arrival.HasField("delay"):
                    print(f"  Arrival delay: {arrival.delay} seconds")

                if arrival.HasField("time"):
                    print(f"  Predicted arrival timestamp: {arrival.time}")

            if stop_update.HasField("departure"):
                departure = stop_update.departure

                if departure.HasField("delay"):
                    print(f"  Departure delay: {departure.delay} seconds")

                if departure.HasField("time"):
                    print(f"  Predicted departure timestamp: {departure.time}")

            shown += 1

        if shown >= 5:
            break


def main() -> None:
    files = sorted(REALTIME_DIR.glob("*.pb"))

    if not files:
        print(f"No .pb files found in {REALTIME_DIR}")
        return

    for file_path in files:
        try:
            inspect_snapshot(file_path)
        except Exception as error:
            print(f"Could not inspect {file_path.name}: {error}")


if __name__ == "__main__":
    main()
