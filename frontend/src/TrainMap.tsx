
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap
} from "react-leaflet";
import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type TrainMapProps = {
  latitude: number;
  longitude: number;
};

const stations = [
  {
    name: "Jaisalmer",
    code: "JSM",
    position: [26.9152, 70.9269] as [number, number]
  },
  {
    name: "Phalodi Junction",
    code: "PLC",
    position: [27.1270, 72.3680] as [number, number]
  },
  {
    name: "Lalgarh Junction",
    code: "LGH",
    // Approximate position; verify against your database.
    position: [28.0167, 73.3167] as [number, number]
  }
];

const trainIcon = L.divIcon({
  className: "train-marker",
  html: '<div style="font-size:28px">🚆</div>',
  iconSize: [34, 34],
  iconAnchor: [17, 17]
});

function FollowTrain({ latitude, longitude }: TrainMapProps) {
  const map = useMap();

  useEffect(() => {
    map.panTo([latitude, longitude], { animate: true });
  }, [latitude, longitude, map]);

  return null;
}

export default function TrainMap({
  latitude,
  longitude
}: TrainMapProps) {
  const route = stations.map((station) => station.position);

  return (
    <MapContainer
      center={[latitude, longitude]}
      zoom={8}
      scrollWheelZoom
      style={{
        height: "450px",
        width: "100%",
        borderRadius: "12px"
      }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <Polyline
        positions={route}
        pathOptions={{
          color: "#1976d2",
          weight: 5
        }}
      />

      {stations.map((station) => (
        <Marker
          key={station.code}
          position={station.position}
        >
          <Popup>
            <strong>{station.name}</strong>
            <br />
            Station code: {station.code}
          </Popup>
        </Marker>
      ))}

      <Marker
        position={[latitude, longitude]}
        icon={trainIcon}
      >
        <Popup>
          <strong>Train 14703</strong>
          <br />
          Jaisalmer - Lalgarh Express
          <br />
          Current simulated position
        </Popup>
      </Marker>

      <FollowTrain
        latitude={latitude}
        longitude={longitude}
      />
    </MapContainer>
  );
}
