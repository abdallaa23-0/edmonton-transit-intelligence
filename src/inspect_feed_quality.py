
from collections import Counter
from pathlib import Path

from google.transit import gtfs_realtime_pb2


ROOT = Path(__file__).resolve().parent.parent
REALTIME_DIR = ROOT / "data" / "realtime"


def inspect_file(path):
    feed = gtfs_realtime_pb2.FeedMessage()
    with path.open("rb") as file:
        feed.ParseFromString(file.read())

    trip_ids = Counter()
    entity_ids = Counter()
    trip_updates = 0
    missing_trip_id_entities = 0
    stop_updates_total = 0
    repeated_stop_keys = 0
    trips_with_repeats = 0
    stale_predictions = 0
    extreme_delays = 0

    for entity in feed.entity:
        entity_ids[entity.id] += 1

        if not entity.HasField("trip_update"):
            continue

        trip_updates += 1
        update = entity.trip_update
        trip_id = (
            update.trip.trip_id
            if update.trip.HasField("trip_id")
            else ""
        )

        if not trip_id:
            missing_trip_id_entities += 1
        else:
            trip_ids[trip_id] += 1

        seen = set()
        has_repeat = False

        for stop in update.stop_time_update:
            stop_updates_total += 1
            stop_id = stop.stop_id if stop.HasField("stop_id") else ""
            sequence = (
                stop.stop_sequence
                if stop.HasField("stop_sequence")
                else None
            )
            key = (stop_id, sequence)

            if key in seen:
                repeated_stop_keys += 1
                has_repeat = True
            seen.add(key)

            for event_name in ("arrival", "departure"):
                if not stop.HasField(event_name):
                    continue

                event = getattr(stop, event_name)

                if event.HasField("delay") and abs(event.delay) > 3600:
                    extreme_delays += 1

                if event.HasField("time") and feed.header.HasField("timestamp"):
                    # Predictions more than 6 hours behind the feed timestamp
                    # are flagged for investigation, not automatically removed.
                    if event.time < feed.header.timestamp - 6 * 3600:
                        stale_predictions += 1

        if has_repeat:
            trips_with_repeats += 1

    print(f"\n{'=' * 65}\n{path.name}")
    print(f"Entities: {len(feed.entity):,}")
    print(f"Trip updates: {trip_updates:,}")
    print(f"Stop updates: {stop_updates_total:,}")
    print(f"Entities without trip_id: {missing_trip_id_entities:,}")
    print(f"Repeated entity IDs: {sum(n - 1 for n in entity_ids.values() if n > 1):,}")
    print(f"Trip IDs used by multiple entities: {sum(n - 1 for n in trip_ids.values() if n > 1):,}")
    print(f"Repeated stop keys within trip updates: {repeated_stop_keys:,}")
    print(f"Trip updates containing repeated stop keys: {trips_with_repeats:,}")
    print(f"Event delays over 1 hour in magnitude: {extreme_delays:,}")
    print(f"Event timestamps over 6 hours behind feed timestamp: {stale_predictions:,}")


def main():
    files = sorted(REALTIME_DIR.glob("*.pb"))
    if not files:
        print("No protobuf snapshots found.")
        return

    for path in files:
        inspect_file(path)


if __name__ == "__main__":
    main()
