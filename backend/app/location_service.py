import math


def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
):
    """
    Calculate approximate distance between
    two geographic coordinates in kilometers.
    """

    earth_radius = 6371

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


def find_nearest_station(
    latitude: float,
    longitude: float,
    stations
):
    nearest_station = None
    shortest_distance = float("inf")

    for station in stations:

        if station["latitude"] is None:
            continue

        if station["longitude"] is None:
            continue

        distance = calculate_distance(
            latitude,
            longitude,
            float(station["latitude"]),
            float(station["longitude"])
        )

        if distance < shortest_distance:
            shortest_distance = distance
            nearest_station = station

    return nearest_station, shortest_distance