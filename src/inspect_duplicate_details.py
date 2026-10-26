
from collections import defaultdict
from pathlib import Path
import hashlib

from google.transit import gtfs_realtime_pb2


ROOT = Path(__file__).resolve().parent.parent
REALTIME_DIR = ROOT / "data" / "realtime"



def message_signature(update):
    """Fingerprint the complete TripUpdate protobuf message."""
    import hashlib

    return hashlib.sha256(
        update.SerializeToString()
    ).hexdigest()


def main():
    for path in sorted(REALTIME_DIR.glob("*.pb")):
        feed = gtfs_realtime_pb2.FeedMessage()

        with path.open("rb") as file:
            feed.ParseFromString(file.read())

        groups = defaultdict(list)

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            update = entity.trip_update
            trip = update.trip

            groups[entity.id].append({
                "trip_id": (
                    trip.trip_id if trip.HasField("trip_id") else ""
                ),
                "route_id": (
                    trip.route_id if trip.HasField("route_id") else ""
                ),
                "start_date": (
                    trip.start_date if trip.HasField("start_date") else ""
                ),
                "stop_count": len(update.stop_time_update),
                "signature": message_signature(update),
            })

        repeated_groups = [
            (entity_id, records)
            for entity_id, records in groups.items()
            if len(records) > 1
        ]

        exact_stop_groups = 0
        mixed_descriptor_groups = 0
        different_stop_groups = 0

        for _, records in repeated_groups:
            signatures = {record["signature"] for record in records}
            if len(signatures) == 1:
                exact_stop_groups += 1
            else:
                different_stop_groups += 1

            has_trip_id = any(record["trip_id"] for record in records)
            lacks_trip_id = any(not record["trip_id"] for record in records)

            if has_trip_id and lacks_trip_id:
                mixed_descriptor_groups += 1

        print(f"\n{'=' * 68}")
        print(path.name)
        print(f"Repeated entity ID groups: {len(repeated_groups):,}")
        print(f"Groups with identical stop-update payloads: {exact_stop_groups:,}")
        print(f"Groups with differing stop-update payloads: {different_stop_groups:,}")
        print(f"Groups mixing present/missing trip IDs: {mixed_descriptor_groups:,}")

        print("\n--- Examples where stop updates differ ---")
        shown = 0

        for entity_id, records in repeated_groups:
            if len({r["signature"] for r in records}) <= 1:
                continue

            print(f"\nEntity ID: {entity_id}")
            for record in records:
                print(
                    f"  trip={record['trip_id'] or '<missing>'}, "
                    f"route={record['route_id'] or '<missing>'}, "
                    f"date={record['start_date'] or '<missing>'}, "
                    f"stops={record['stop_count']}, "
                    f"signature={record['signature'][:12]}"
                )

            shown += 1
            if shown == 5:
                break


if __name__ == "__main__":
    main()
