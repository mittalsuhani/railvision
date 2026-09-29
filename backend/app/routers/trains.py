from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(
    prefix="/api/v1/trains",
    tags=["Trains"]
)


@router.get("/")
def get_trains(db: Session = Depends(get_db)):

    query = text("""
        SELECT
            t.train_id,
            t.train_number,
            t.train_name,
            t.train_type,
            s1.station_code AS source_code,
            s1.station_name AS source_name,
            s2.station_code AS destination_code,
            s2.station_name AS destination_name,
            t.is_active
        FROM trains t
        JOIN stations s1
            ON t.source_station_id = s1.station_id
        JOIN stations s2
            ON t.destination_station_id = s2.station_id
        ORDER BY t.train_id
    """)

    result = db.execute(query)

    trains = []

    for row in result:
        trains.append({
            "train_id": row.train_id,
            "train_number": row.train_number,
            "train_name": row.train_name,
            "train_type": row.train_type,
            "source": {
                "code": row.source_code,
                "name": row.source_name
            },
            "destination": {
                "code": row.destination_code,
                "name": row.destination_name
            },
            "is_active": row.is_active
        })

    return {
        "count": len(trains),
        "trains": trains
    }