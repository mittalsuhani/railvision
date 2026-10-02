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

function App() {
  const [trainNumber, setTrainNumber] = useState("14703");
  const [trainData, setTrainData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const getPrediction = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/predictions/train/${trainNumber}/eta`
      );

      if (!response.ok) {
        throw new Error("Unable to fetch train data");
      }

      const data = await response.json();

      setTrainData(data);
    } catch (error) {
      setError("Unable to fetch train prediction.");
      setTrainData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getPrediction();

    const interval = setInterval(() => {
      getPrediction();
    }, 5000);

    return () => clearInterval(interval);
  }, [trainNumber]);

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 6 }}>

        <Typography variant="h3" gutterBottom>
          RailVision
        </Typography>

        <Typography variant="h6" gutterBottom>
          AI-Powered Train ETA Prediction
        </Typography>

        <Box sx={{ mt: 4 }}>

          <TextField
            label="Train Number"
            value={trainNumber}
            onChange={(e) => setTrainNumber(e.target.value)}
          />

          <Button
            variant="contained"
            sx={{ ml: 2, mt: 1 }}
            onClick={getPrediction}
          >
            Refresh
          </Button>

        </Box>

        {loading && (
          <Typography sx={{ mt: 3 }}>
            Loading train data...
          </Typography>
        )}

        {error && (
          <Typography color="error" sx={{ mt: 3 }}>
            {error}
          </Typography>
        )}

        {trainData && (
          <Card sx={{ mt: 4 }}>
            <CardContent>

              <Typography variant="h5">
                Train {trainData.train_number}
              </Typography>

              <Typography sx={{ mt: 1 }}>
                {trainData.train_name}
              </Typography>

              <Typography sx={{ mt: 2 }}>
                Current Station: {trainData.current_station}
              </Typography>

              <Typography>
                Next Station: {trainData.next_station}
              </Typography>

              <Typography>
                Current Delay: {trainData.current_delay_minutes} minutes
              </Typography>

              <Typography>
                Current Speed: {trainData.current_speed_kmph} km/h
              </Typography>

              <Typography>
                Scheduled Travel Time:{" "}
                {trainData.scheduled_travel_time_minutes} minutes
              </Typography>

              <Typography variant="h6" sx={{ mt: 3 }}>
                AI Predicted Travel Time:{" "}
                {trainData.predicted_travel_time_minutes} minutes
              </Typography>

              <Typography sx={{ mt: 2 }}>
                Location:{" "}
                {trainData.location.latitude.toFixed(4)},{" "}
                {trainData.location.longitude.toFixed(4)}
              </Typography>

              <Typography sx={{ mt: 2 }} color="text.secondary">
                Last updated:{" "}
                {new Date(
                  trainData.location_recorded_at
                ).toLocaleTimeString()}
              </Typography>

            </CardContent>
          </Card>
        )}

      </Box>
    </Container>
  );
}

export default App;