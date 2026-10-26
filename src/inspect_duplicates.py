
from collections import defaultdict
from pathlib import Path

from google.transit import gtfs_realtime_pb2


ROOT = Path(__file__).resolve().parent.parent
REALTIME_DIR = ROOT / "data" / "realtime"


def main():
    for path in sorted(REALTIME_DIR.glob("*.pb")):
        feed = gtfs_realtime_pb2.FeedMessage()

        with path.open("rb") as file:
            feed.ParseFromString(file.read())

        by_entity_id = defaultdict(list)
        missing_trip_id = []

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            update = entity.trip_update
            trip = update.trip

            trip_id = (
                trip.trip_id if trip.HasField("trip_id") else ""
            )
            route_id = (
                trip.route_id if trip.HasField("route_id") else ""
            )
            start_date = (
                trip.start_date if trip.HasField("start_date") else ""
            )

            info = {
                "entity_id": entity.id,
                "trip_id": trip_id,
                "route_id": route_id,
                "start_date": start_date,
                "stop_count": len(update.stop_time_update),
                "first_stop": (
                    update.stop_time_update[0].stop_id
                    if update.stop_time_update
                    and update.stop_time_update[0].HasField("stop_id")
                    else ""
                ),
            }

            by_entity_id[entity.id].append(info)

            if not trip_id:
                missing_trip_id.append(info)

        repeated = [
            entries
            for entries in by_entity_id.values()
            if len(entries) > 1
        ]

        print(f"\n{'=' * 70}")
        print(path.name)
        print(f"Repeated entity ID groups: {len(repeated):,}")
        print(f"Entities without trip IDs: {len(missing_trip_id):,}")

        print("\n--- First 5 repeated entity ID groups ---")
        for group in repeated[:5]:
            print(f"\nEntity ID: {group[0]['entity_id']}")
            for item in group:
                print(
                    f"  trip={item['trip_id'] or '<missing>'}, "
                    f"route={item['route_id'] or '<missing>'}, "
                    f"date={item['start_date'] or '<missing>'}, "
                    f"stops={item['stop_count']}, "
                    f"first_stop={item['first_stop']}"
                )

        print("\n--- First 10 entities missing trip IDs ---")
        for item in missing_trip_id[:10]:
            print(
                f"entity={item['entity_id']}, "
                f"route={item['route_id'] or '<missing>'}, "
                f"date={item['start_date'] or '<missing>'}, "
                f"stops={item['stop_count']}, "
                f"first_stop={item['first_stop']}"
            )


if __name__ == "__main__":
    main()
