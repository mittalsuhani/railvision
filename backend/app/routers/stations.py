from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(
    prefix="/api/v1/stations",
    tags=["Stations"]
)


@router.get("/")
def get_stations(db: Session = Depends(get_db)):
    query = text("""
        SELECT
            station_id,
            station_code,
            station_name,
            city,
            state,
            latitude,
            longitude
        FROM stations
        ORDER BY station_id
    """)

    result = db.execute(query)

    stations = []

    for row in result:
        stations.append({
            "station_id": row.station_id,
            "station_code": row.station_code,
            "station_name": row.station_name,
            "city": row.city,
            "state": row.state,
            "latitude": float(row.latitude) if row.latitude else None,
            "longitude": float(row.longitude) if row.longitude else None
        })

    return {
        "count": len(stations),
        "stations": stations
    }