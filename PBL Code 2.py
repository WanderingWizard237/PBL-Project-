import math
import random
import requests
from dataclasses import dataclass

# -----------------------------------
# CONFIG (ADD YOUR API KEY)
# -----------------------------------
OPENWEATHER_API_KEY = "YOUR_API_KEY_HERE"

# -----------------------------------
# Haversine Distance (km)
# -----------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# -----------------------------------
# DATA MODELS
# -----------------------------------
@dataclass
class Incident:
    id: int
    lat: float
    lon: float
    severity: float
    demand: int

@dataclass
class Resource:
    id: int
    lat: float
    lon: float
    capacity: int
    type: str

# -----------------------------------
# REAL GDACS API (GeoJSON)
# -----------------------------------
def fetch_gdacs_events():
    url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
    params = {
        "eventtype": "EQ,TC,FL"  # Earthquake, Cyclone, Flood
    }

    try:
        res = requests.get(url, params=params).json()
        return res["features"]
    except:
        print("Error fetching GDACS data. Using fallback.")
        return []

# -----------------------------------
# Convert GDACS → Incidents
# -----------------------------------
def create_incidents_from_gdacs():
    events = fetch_gdacs_events()
    incidents = []

    severity_map = {
        "Green": 3,
        "Orange": 6,
        "Red": 9
    }

    for i, event in enumerate(events[:10]):  # limit to 10
        try:
            props = event["properties"]
            coords = event["geometry"]["coordinates"]

            lon, lat = coords[0], coords[1]

            alert_level = props.get("alertlevel", "Green")
            severity = severity_map.get(alert_level, 5)

            demand = max(1, int(severity / 2))

            incidents.append(Incident(
                id=i+1,
                lat=lat,
                lon=lon,
                severity=severity,
                demand=demand
            ))
        except:
            continue

    return incidents

# -----------------------------------
# WEATHER API
# -----------------------------------
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url).json()
        return res["weather"][0]["main"]
    except:
        return "Clear"

# -----------------------------------
# WEATHER FACTOR
# -----------------------------------
def get_weather_factor(condition):
    if condition in ["Thunderstorm", "Storm"]:
        return 2.0
    elif condition in ["Rain"]:
        return 1.5
    elif condition in ["Clouds"]:
        return 1.2
    else:
        return 1.0

# -----------------------------------
# RESOURCE GENERATION
# -----------------------------------
def generate_resources(m=6):
    types = ["Medical", "Rescue Team", "Truck"]
    resources = []

    for i in range(m):
        lat = 28.61 + random.uniform(-0.4, 0.4)
        lon = 77.20 + random.uniform(-0.4, 0.4)
        capacity = random.randint(3, 8)
        rtype = random.choice(types)

        resources.append(Resource(i+1, lat, lon, capacity, rtype))

    return resources

# -----------------------------------
# ALLOCATION ALGORITHM (IMPROVED)
# -----------------------------------
def allocate_resources(incidents, resources):
    allocations = []

    # Sort incidents by priority
    incidents_sorted = sorted(incidents, key=lambda x: (-x.severity, -x.demand))

    for inc in incidents_sorted:
        remaining = inc.demand
        candidates = []

        # Weather impact
        condition = get_weather(inc.lat, inc.lon)
        weather_factor = get_weather_factor(condition)

        for res in resources:
            if res.capacity > 0:
                dist = haversine(inc.lat, inc.lon, res.lat, res.lon)

                # Improved scoring
                score = (inc.severity * weather_factor) / (1.0 + dist)

                candidates.append((score, res, dist))

        # Sort best resources first
        candidates.sort(key=lambda x: -x[0])

        for score, res, dist in candidates:
            if remaining <= 0:
                break

            assigned = min(remaining, res.capacity)

            allocations.append({
                "incident_id": inc.id,
                "resource_id": res.id,
                "units_assigned": assigned,
                "distance_km": round(dist, 2)
            })

            res.capacity -= assigned
            remaining -= assigned

    return allocations

# -----------------------------------
# MAIN EXECUTION
# -----------------------------------
def main():
    random.seed(42)

    print("Fetching real-time GDACS disaster data...")
    incidents = create_incidents_from_gdacs()

    if not incidents:
        print("No incidents found. Exiting.")
        return

    resources = generate_resources()
    allocations = allocate_resources(incidents, resources)

    # -----------------------------------
    # OUTPUT
    # -----------------------------------
    print("\n==============================")
    print("   DRROS REAL-TIME RESULTS")
    print("==============================\n")

    print("INCIDENTS (REAL DATA):")
    for inc in incidents:
        print(f"ID {inc.id} | Lat {inc.lat:.4f} | Lon {inc.lon:.4f} | Severity {inc.severity} | Demand {inc.demand}")

    print("\nRESOURCES (Post Allocation):")
    for res in resources:
        print(f"ID {res.id} | Lat {res.lat:.4f} | Lon {res.lon:.4f} | Left {res.capacity} | Type {res.type}")

    print("\nALLOCATIONS MADE:")
    if not allocations:
        print("No allocations were made.")
    else:
        for a in allocations:
            print(
                f"Incident {a['incident_id']} <-- "
                f"{a['units_assigned']} units -- Resource {a['resource_id']} "
                f"(Distance: {a['distance_km']} km)"
            )

    print("\nSystem Execution Complete.\n")


# -----------------------------------
# RUN PROGRAM
# -----------------------------------
if __name__ == "__main__":
    main()