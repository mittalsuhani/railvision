
import time
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/railvision"

TRAIN_NUMBER = "14703"
STATION_CODES = ["JSM", "PLC", "LGH"]
UPDATE_INTERVAL = 5
PROGRESS_STEP = 0.1
SPEED_KMPH = 60


def interpolate(start, end, progress):
    return start + (end - start) * progress


def main():
    print("RailVision Train Simulator")
    print("=" * 35)
    print(f"Train: {TRAIN_NUMBER}")
    print("Route: Jaisalmer -> Phalodi -> Lalgarh")
    print()

    with psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT train_id
                FROM trains
                WHERE train_number = %s
                """,
                (TRAIN_NUMBER,)
            )
            train = cursor.fetchone()

            if not train:
                raise ValueError(f"Train {TRAIN_NUMBER} not found.")

            train_id = train["train_id"]

            cursor.execute(
                """
                SELECT journey_id
                FROM journey_records
                WHERE train_id = %s
                  AND status = 'RUNNING'
                ORDER BY journey_id DESC
                LIMIT 1
                """,
                (train_id,)
            )
            journey = cursor.fetchone()

            if not journey:
                raise ValueError(
                    "No RUNNING journey found for this train. "
                    "Create or activate a journey first."
                )

            journey_id = journey["journey_id"]

            cursor.execute(
                """
                SELECT station_code, station_name, latitude, longitude
                FROM stations
                WHERE station_code = ANY(%s)
                """,
                (STATION_CODES,)
            )
            rows = cursor.fetchall()

            station_data = {
                row["station_code"]: row
                for row in rows
            }

            for code in STATION_CODES:
                station = station_data.get(code)

                if not station:
                    raise ValueError(
                        f"Station {code} was not found in the database."
                    )

                if station["latitude"] is None or station["longitude"] is None:
                    raise ValueError(
                        f"Station {code} is missing coordinates. "
                        "Update its latitude and longitude first."
                    )

            route = [station_data[code] for code in STATION_CODES]

            print(f"Journey ID: {journey_id}")
            print()

            for index in range(len(route) - 1):
                start_station = route[index]
                end_station = route[index + 1]

                print(
                    f"Simulating: {start_station['station_name']} "
                    f"-> {end_station['station_name']}"
                )

                steps = round(1 / PROGRESS_STEP)

                for step in range(steps + 1):
                    progress = step / steps

                    latitude = interpolate(
                        float(start_station["latitude"]),
                        float(end_station["latitude"]),
                        progress
                    )

                    longitude = interpolate(
                        float(start_station["longitude"]),
                        float(end_station["longitude"]),
                        progress
                    )

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
                            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                            """,
                            (
                                train_id,
                                journey_id,
                                latitude,
                                longitude,
                                SPEED_KMPH
                                if step not in (0, steps)
                                else 0
                            )
                        )

                    connection.commit()

                    print(
                        f"{start_station['station_code']} -> "
                        f"{end_station['station_code']} | "
                        f"{progress * 100:5.0f}% | "
                        f"Lat: {latitude:.5f} | "
                        f"Lon: {longitude:.5f}"
                    )

                    if not (index == len(route) - 2 and step == steps):
                        time.sleep(UPDATE_INTERVAL)

                print(f"Reached {end_station['station_name']}")
                print()

    print("Simulation completed at Lalgarh Junction.")


if __name__ == "__main__":
    main()
