
from collections import Counter
from pathlib import Path

from google.transit import gtfs_realtime_pb2


ROOT = Path(__file__).resolve().parent.parent
REALTIME_DIR = ROOT / "data" / "realtime"


def main():
    for path in sorted(REALTIME_DIR.glob("*.pb")):
        feed = gtfs_realtime_pb2.FeedMessage()

        with path.open("rb") as file:
            feed.ParseFromString(file.read())

        descriptor_types = Counter()
        descriptor_pairs = Counter()
        modified_trip_count = 0
        missing_descriptor_count = 0

        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            trip = entity.trip_update.trip
            has_regular_trip_id = (
                trip.HasField("trip_id") and bool(trip.trip_id)
            )
            has_modified_trip = trip.HasField("modified_trip")

            if has_regular_trip_id:
                descriptor_types["regular trip_id"] += 1
            if has_modified_trip:
                descriptor_types["modified_trip"] += 1
                modified_trip_count += 1
            if not has_regular_trip_id and not has_modified_trip:
                descriptor_types["neither"] += 1

            descriptor_pairs[
                (has_regular_trip_id, has_modified_trip)
            ] += 1

        print(f"\n{'=' * 65}")
        print(path.name)
        print("Descriptor types:")
        for label, count in descriptor_types.items():
            print(f"  {label}: {count:,}")

        print("\nDescriptor combinations:")
        for (regular, modified), count in descriptor_pairs.items():
            print(
                f"  regular_trip_id={regular}, "
                f"modified_trip={modified}: {count:,}"
            )


if __name__ == "__main__":
    main()
