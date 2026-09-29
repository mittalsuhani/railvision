from fastapi import FastAPI
from sqlalchemy import text
from app.routers.stations import router as stations_router
from app.database import engine
from app.routers.trains import router as trains_router
app = FastAPI(
    title="RailVision API",
    description="AI-powered train ETA and delay prediction system",
    version="1.0.0",
)
app.include_router(trains_router)
app.include_router(stations_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to RailVision!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "service": "RailVision Backend",
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }