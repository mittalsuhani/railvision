import time
import math
import psycopg


DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/railvision"

TRAIN_ID = 1
JOURNEY_ID = 1


# Jaisalmer
START_LAT = 26.9152
START_LON = 70.9269

# Phalodi
END_LAT = 27.1270
END_LON = 72.3680


def interpolate(start, end, progress):
    return start + (end - start) * progress


def main():

    print("RailVision Train Simulator")
    print("---------------------------")
    print("Train: 14703")
    print("Route: Jaisalmer -> Phalodi")
    print()

    connection = psycopg.connect(DATABASE_URL)

    progress = 0.0

    while progress <= 1.0:

        latitude = interpolate(
            START_LAT,
            END_LAT,
            progress
        )

        longitude = interpolate(
            START_LON,
            END_LON,
            progress
        )

        speed = 60

        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO train_locations
                (
                    train_id,
                    journey_id,
                    latitude,
                    longitude,
                    speed_kmph,
                    recorded_at
                )
                VALUES
                (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (
                    TRAIN_ID,
                    JOURNEY_ID,
                    latitude,
                    longitude,
                    speed
                )
            )

            connection.commit()

        print(
            f"Progress: {progress * 100:.0f}% | "
            f"Lat: {latitude:.4f} | "
            f"Lon: {longitude:.4f} | "
            f"Speed: {speed} km/h"
        )

        progress += 0.1

        time.sleep(5)

    connection.close()

    print()
    print("Train reached Phalodi.")


if __name__ == "__main__":
    main()