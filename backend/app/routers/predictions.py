from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import SessionLocal
from app.ml_service import predict_eta
from app.location_service import find_nearest_station


router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predictions"]
)


# ---------------------------------------------------------
# Simple ETA prediction endpoint
# ---------------------------------------------------------

@router.get("/eta")
def calculate_eta(
    scheduled_minutes: float,
    current_delay: float,
    speed_kmph: float
):
    predicted_minutes = predict_eta(
        scheduled_minutes,
        current_delay,
        speed_kmph
    )

    return {
        "predicted_travel_time_minutes": predicted_minutes,
        "scheduled_minutes": scheduled_minutes,
        "current_delay_minutes": current_delay,
        "speed_kmph": speed_kmph
    }


# ---------------------------------------------------------
# Database-backed dynamic ETA endpoint
# ---------------------------------------------------------

@router.get("/train/{train_number}/eta")
def calculate_train_eta(train_number: str):

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # 1. Get train information
        # -------------------------------------------------

        train = db.execute(
            text("""
                SELECT
                    train_id,
                    train_number,
                    train_name
                FROM trains
                WHERE train_number = :train_number
            """),
            {
                "train_number": train_number
            }
        ).mappings().first()

        if not train:
            raise HTTPException(
                status_code=404,
                detail="Train not found"
            )

        # -------------------------------------------------
        # 2. Get latest journey
        # -------------------------------------------------

        journey = db.execute(
            text("""
                SELECT
                    journey_id,
                    train_id,
                    journey_date,
                    status
                FROM journey_records
                WHERE train_id = :train_id
                ORDER BY journey_id DESC
                LIMIT 1
            """),
            {
                "train_id": train["train_id"]
            }
        ).mappings().first()

        if not journey:
            raise HTTPException(
                status_code=404,
                detail="No journey found for this train"
            )

        # -------------------------------------------------
        # 3. Get latest train location
        # -------------------------------------------------

        location = db.execute(
            text("""
                SELECT
                    latitude,
                    longitude,
                    speed_kmph,
                    recorded_at
                FROM train_locations
                WHERE train_id = :train_id
                  AND journey_id = :journey_id
                ORDER BY recorded_at DESC
                LIMIT 1
            """),
            {
                "train_id": train["train_id"],
                "journey_id": journey["journey_id"]
            }
        ).mappings().first()

        if not location:
            raise HTTPException(
                status_code=404,
                detail="No train location found"
            )

        # -------------------------------------------------
        # 4. Get latest delay
        # -------------------------------------------------

        delay = db.execute(
            text("""
                SELECT
                    delay_minutes,
                    reason
                FROM delay_events
                WHERE train_id = :train_id
                  AND journey_id = :journey_id
                ORDER BY detected_at DESC
                LIMIT 1
            """),
            {
                "train_id": train["train_id"],
                "journey_id": journey["journey_id"]
            }
        ).mappings().first()

        if delay:
            current_delay = float(
                delay["delay_minutes"]
            )
            delay_reason = delay["reason"]
        else:
            current_delay = 0.0
            delay_reason = None

        # -------------------------------------------------
        # 5. Get all stations having coordinates
        # -------------------------------------------------

        stations = db.execute(
            text("""
                SELECT
                    station_id,
                    station_code,
                    station_name,
                    latitude,
                    longitude
                FROM stations
                WHERE latitude IS NOT NULL
                  AND longitude IS NOT NULL
            """)
        ).mappings().all()

        if not stations:
            raise HTTPException(
                status_code=404,
                detail="No station coordinates available"
            )

        # -------------------------------------------------
        # 6. Find nearest station to train
        # -------------------------------------------------

        nearest_station, station_distance = (
            find_nearest_station(
                float(location["latitude"]),
                float(location["longitude"]),
                stations
            )
        )

        if not nearest_station:
            raise HTTPException(
                status_code=404,
                detail="Unable to determine current station"
            )

        # -------------------------------------------------
        # 7. Find current station in train schedule
        # -------------------------------------------------

        current_schedule = db.execute(
            text("""
                SELECT
                    schedule_id,
                    station_id,
                    scheduled_arrival,
                    scheduled_departure,
                    stop_sequence
                FROM train_schedules
                WHERE train_id = :train_id
                  AND station_id = :station_id
                LIMIT 1
            """),
            {
                "train_id": train["train_id"],
                "station_id": nearest_station["station_id"]
            }
        ).mappings().first()

        if not current_schedule:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Current nearest station is not "
                    "part of this train route"
                )
            )

        # -------------------------------------------------
        # 8. Find next station
        # -------------------------------------------------

        next_schedule = db.execute(
            text("""
                SELECT
                    ts.station_id,
                    s.station_code,
                    s.station_name,
                    ts.scheduled_arrival,
                    ts.stop_sequence
                FROM train_schedules ts

                JOIN stations s
                    ON s.station_id = ts.station_id

                WHERE ts.train_id = :train_id
                  AND ts.stop_sequence >
                      :current_sequence

                ORDER BY ts.stop_sequence

                LIMIT 1
            """),
            {
                "train_id": train["train_id"],
                "current_sequence":
                    current_schedule["stop_sequence"]
            }
        ).mappings().first()

        if not next_schedule:
            raise HTTPException(
                status_code=404,
                detail="No next station found"
            )

        # -------------------------------------------------
        # 9. Calculate scheduled travel time
        # -------------------------------------------------

        scheduled_minutes = db.execute(
            text("""
                SELECT
                    EXTRACT(
                        EPOCH FROM
                        (
                            next_ts.scheduled_arrival
                            -
                            current_ts.scheduled_departure
                        )
                    ) / 60

                FROM train_schedules current_ts

                JOIN train_schedules next_ts
                    ON next_ts.train_id =
                       current_ts.train_id

                   AND next_ts.stop_sequence =
                       current_ts.stop_sequence + 1

                WHERE current_ts.train_id =
                      :train_id

                  AND current_ts.station_id =
                      :station_id

                LIMIT 1
            """),
            {
                "train_id": train["train_id"],
                "station_id":
                    nearest_station["station_id"]
            }
        ).scalar()

        if scheduled_minutes is None:
            raise HTTPException(
                status_code=404,
                detail="Unable to calculate scheduled travel time"
            )

        scheduled_minutes = float(
            scheduled_minutes
        )

        # -------------------------------------------------
        # 10. Get current speed
        # -------------------------------------------------

        if location["speed_kmph"] is None:
            speed = 0.0
        else:
            speed = float(
                location["speed_kmph"]
            )

        # -------------------------------------------------
        # 11. Run ML model
        # -------------------------------------------------

        predicted_travel_time = predict_eta(
            scheduled_minutes,
            current_delay,
            speed
        )

        # -------------------------------------------------
        # 12. Return complete prediction
        # -------------------------------------------------

        return {

            "train_number":
                train["train_number"],

            "train_name":
                train["train_name"],

            "journey_id":
                journey["journey_id"],

            "journey_status":
                journey["status"],

            "current_station":
                nearest_station["station_name"],

            "current_station_code":
                nearest_station["station_code"],

            "distance_from_current_station_km":
                round(
                    float(station_distance),
                    2
                ),

            "next_station":
                next_schedule["station_name"],

            "next_station_code":
                next_schedule["station_code"],

            "scheduled_travel_time_minutes":
                scheduled_minutes,

            "current_delay_minutes":
                current_delay,

            "delay_reason":
                delay_reason,

            "current_speed_kmph":
                speed,

            "predicted_travel_time_minutes":
                predicted_travel_time,

            "location": {
                "latitude":
                    float(location["latitude"]),

                "longitude":
                    float(location["longitude"])
            },

            "location_recorded_at":
                location["recorded_at"],

            "prediction_status":
                "SUCCESS"
        }

    finally:
        db.close()