from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.database import SessionLocal
from app.ml_service import predict_eta

router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predictions"]
)


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


@router.get("/train/{train_number}/eta")
def calculate_train_eta(train_number: str):

    db = SessionLocal()

    try:
        # 1. Get train
        train = db.execute(
            text("""
                SELECT
                    train_id,
                    train_number,
                    train_name
                FROM trains
                WHERE train_number = :train_number
            """),
            {"train_number": train_number}
        ).mappings().first()

        if not train:
            raise HTTPException(
                status_code=404,
                detail="Train not found"
            )

        # 2. Get latest journey
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
            {"train_id": train["train_id"]}
        ).mappings().first()

        if not journey:
            raise HTTPException(
                status_code=404,
                detail="No journey found for this train"
            )

        # 3. Get latest train location
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

        # 4. Get latest delay
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

        current_delay = delay["delay_minutes"] if delay else 0
        delay_reason = delay["reason"] if delay else None

        # 5. Get first two scheduled stops
        schedule = db.execute(
            text("""
                SELECT
                    ts1.station_id AS current_station_id,
                    s1.station_name AS current_station,
                    ts1.scheduled_departure,

                    ts2.station_id AS next_station_id,
                    s2.station_name AS next_station,
                    ts2.scheduled_arrival,

                    EXTRACT(
                        EPOCH FROM
                        (ts2.scheduled_arrival - ts1.scheduled_departure)
                    ) / 60 AS scheduled_minutes

                FROM train_schedules ts1

                JOIN train_schedules ts2
                    ON ts2.train_id = ts1.train_id
                    AND ts2.stop_sequence = ts1.stop_sequence + 1

                JOIN stations s1
                    ON s1.station_id = ts1.station_id

                JOIN stations s2
                    ON s2.station_id = ts2.station_id

                WHERE ts1.train_id = :train_id

                ORDER BY ts1.stop_sequence

                LIMIT 1
            """),
            {"train_id": train["train_id"]}
        ).mappings().first()

        if not schedule:
            raise HTTPException(
                status_code=404,
                detail="Train schedule not found"
            )

        scheduled_minutes = float(schedule["scheduled_minutes"])
        speed = float(location["speed_kmph"])

        # 6. Run ML model
        predicted_travel_time = predict_eta(
            scheduled_minutes,
            current_delay,
            speed
        )

        return {
            "train_number": train["train_number"],
            "train_name": train["train_name"],

            "journey_id": journey["journey_id"],
            "journey_status": journey["status"],

            "current_station": schedule["current_station"],
            "next_station": schedule["next_station"],

            "scheduled_travel_time_minutes": scheduled_minutes,
            "current_delay_minutes": current_delay,
            "delay_reason": delay_reason,

            "current_speed_kmph": speed,

            "predicted_travel_time_minutes":
                predicted_travel_time,

            "location": {
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"])
            },

            "prediction_status": "SUCCESS"
        }

    finally:
        db.close()