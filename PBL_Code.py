import math
import random
from dataclasses import dataclass

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
# Data Models
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
# Generate Simulated Incidents
# -----------------------------------
def generate_incidents(n=10, center=(28.61, 77.20), spread=0.3):
    incidents = []
    for i in range(n):
        lat = center[0] + random.uniform(-spread, spread)
        lon = center[1] + random.uniform(-spread, spread)
        severity = round(random.uniform(3.0, 10.0), 1)
        demand = random.randint(1, 5)
        incidents.append(Incident(i+1, lat, lon, severity, demand))
    return incidents

# -----------------------------------
# Generate Simulated Resources
# -----------------------------------
def generate_resources(m=6, center=(28.61, 77.20), spread=0.4):
    types = ["Medical", "Rescue Team", "Truck"]
    resources = []
    for i in range(m):
        lat = center[0] + random.uniform(-spread, spread)
        lon = center[1] + random.uniform(-spread, spread)
        capacity = random.randint(3, 8)
        rtype = random.choice(types)
        resources.append(Resource(i+1, lat, lon, capacity, rtype))
    return resources

# -----------------------------------
# Greedy Allocation Algorithm
# -----------------------------------
def allocate_resources(incidents, resources):
    allocations = []
    incidents_sorted = sorted(incidents, key=lambda x: (-x.severity, -x.demand))

    for inc in incidents_sorted:
        remaining = inc.demand
        candidates = []

        # Score = severity / (distance + 1)
        for res in resources:
            if res.capacity > 0:
                dist = haversine(inc.lat, inc.lon, res.lat, res.lon)
                score = inc.severity / (1.0 + dist)
                candidates.append((score, res, dist))

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
# AUTO RUN
# -----------------------------------
random.seed(42)

incidents = generate_incidents()
resources = generate_resources()
allocations = allocate_resources(incidents, resources)

# -----------------------------------
# DISPLAY RESULTS
# -----------------------------------
print("\n==============================")
print("   DRROS SIMULATION RESULTS")
print("==============================\n")

print("INCIDENTS:")
for inc in incidents:
    print(f"ID {inc.id} | Lat {inc.lat:.4f} | Lon {inc.lon:.4f} | Severity {inc.severity} | Demand {inc.demand}")
print("\n")

print("RESOURCES (Post Allocation):")
for res in resources:
    print(f"ID {res.id} | Lat {res.lat:.4f} | Lon {res.lon:.4f} | Left {res.capacity} | Type {res.type}")
print("\n")

print("ALLOCATIONS MADE:")
if not allocations:
    print("No allocations were made.")
else:
    for a in allocations:
        print(
            f"Incident {a['incident_id']} <-- "
            f"{a['units_assigned']} units -- Resource {a['resource_id']} "
            f"(Distance: {a['distance_km']} km)"
        )

print("\nSimulation Complete.\n")
