import joblib
import pandas as pd
from pathlib import Path


MODEL_PATH = Path(__file__).resolve().parents[2] / "ml" / "eta_model.joblib"

model = joblib.load(MODEL_PATH)


def predict_eta(
    scheduled_minutes: float,
    current_delay: float,
    speed_kmph: float
):
    data = pd.DataFrame({
        "scheduled_minutes": [scheduled_minutes],
        "current_delay": [current_delay],
        "speed_kmph": [speed_kmph]
    })

    prediction = model.predict(data)[0]

    return round(float(prediction), 2)