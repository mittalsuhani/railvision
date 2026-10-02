import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

# Small simulated training dataset
data = {
    "scheduled_minutes": [
        180, 190, 200, 210, 220,
        230, 240, 250, 260, 270,
        280, 290, 300, 310, 320
    ],
    "current_delay": [
        0, 5, 10, 15, 20,
        5, 10, 25, 15, 30,
        20, 35, 25, 40, 30
    ],
    "speed_kmph": [
        80, 78, 75, 72, 70,
        82, 76, 68, 74, 65,
        70, 60, 68, 58, 64
    ],
    "actual_travel_minutes": [
        180, 195, 210, 225, 245,
        235, 255, 275, 280, 305,
        300, 330, 325, 350, 345
    ]
}

df = pd.DataFrame(data)

X = df[
    [
        "scheduled_minutes",
        "current_delay",
        "speed_kmph"
    ]
]

y = df["actual_travel_minutes"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))

print("RailVision ETA Model")
print("--------------------")
print(f"MAE: {mae:.2f} minutes")
print(f"RMSE: {rmse:.2f} minutes")

# Example prediction for train 14703
new_train = pd.DataFrame({
    "scheduled_minutes": [180],
    "current_delay": [15],
    "speed_kmph": [65]
})

predicted_travel_time = model.predict(new_train)[0]

print()
print("Train: 14703")
print(f"Predicted travel time: {predicted_travel_time:.2f} minutes")
import joblib

joblib.dump(model, "D:/railvision/ml/eta_model.joblib")

print("Model saved successfully.")