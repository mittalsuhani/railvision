
import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  TextField,
  Typography
} from "@mui/material";
import TrainMap from "./TrainMap";

type TrainData = {
  train_number: string;
  train_name: string;
  current_station: string;
  next_station: string;
  current_delay_minutes: number;
  current_speed_kmph: number;
  scheduled_travel_time_minutes: number;
  predicted_travel_time_minutes: number;
  location: {
    latitude: number;
    longitude: number;
  };
  location_recorded_at: string;
};

function App() {
  const [trainNumber, setTrainNumber] = useState("14703");
  const [trainData, setTrainData] = useState<TrainData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    let requestInProgress = false;

    const fetchPrediction = async () => {
      if (requestInProgress) return;
      requestInProgress = true;

      try {
        setLoading(true);

        const response = await fetch(
          `http://127.0.0.1:8000/api/v1/predictions/train/${encodeURIComponent(trainNumber)}/eta`
        );

        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`);
        }

        const data: TrainData = await response.json();

        if (active) {
          setTrainData(data);
          setError("");
        }
      } catch {
        if (active) {
          setError("Unable to fetch train data. Check that the backend is running.");
        }
      } finally {
        requestInProgress = false;

        if (active) {
          setLoading(false);
        }
      }
    };

    fetchPrediction();

    const interval = window.setInterval(fetchPrediction, 5000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [trainNumber]);

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 5 }}>
        <Typography variant="h3" gutterBottom>
          RailVision
        </Typography>

        <Typography variant="h6" gutterBottom>
          AI-Powered Train ETA Prediction
        </Typography>

        <Box sx={{ display: "flex", gap: 2, mt: 3, mb: 3 }}>
          <TextField
            label="Train Number"
            value={trainNumber}
            onChange={(event) => setTrainNumber(event.target.value)}
          />

          <Button
            variant="contained"
            onClick={() => setTrainNumber(trainNumber.trim())}
          >
            Refresh
          </Button>
        </Box>

        {loading && !trainData && (
          <Typography>Loading train data...</Typography>
        )}

        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
        )}

        {trainData && (
          <>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h5">
                  Train {trainData.train_number} — {trainData.train_name}
                </Typography>

                <Typography sx={{ mt: 2 }}>
                  Current station: {trainData.current_station}
                </Typography>

                <Typography>
                  Next station: {trainData.next_station}
                </Typography>

                <Typography>
                  Delay: {trainData.current_delay_minutes} minutes
                </Typography>

                <Typography>
                  Speed: {trainData.current_speed_kmph} km/h
                </Typography>

                <Typography>
                  Predicted travel time:{" "}
                  {trainData.predicted_travel_time_minutes} minutes
                </Typography>

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  Last location update:{" "}
                  {new Date(trainData.location_recorded_at).toLocaleTimeString()}
                </Typography>
              </CardContent>
            </Card>

            <Typography variant="h5" sx={{ mb: 2 }}>
              Live Train Map
            </Typography>

            <TrainMap
              latitude={trainData.location.latitude}
              longitude={trainData.location.longitude}
            />

            <Typography color="text.secondary" sx={{ mt: 2 }}>
              Coordinates: {trainData.location.latitude.toFixed(5)},{" "}
              {trainData.location.longitude.toFixed(5)}
            </Typography>
          </>
        )}
      </Box>
    </Container>
  );
}

export default App;
