import os
import sys
import math

# Add the simulation module to Python path
# Try container path first, then relative path for local development
simulation_path = "/real-world-drone-simulation/backend"
if not os.path.exists(simulation_path):
    simulation_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../real-world-drone-simulation/backend"))

if simulation_path not in sys.path:
    sys.path.insert(0, simulation_path)

# Fallback haversine just in case
def haversine(coord1, coord2):
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def generate_path(start_lat, start_lon, end_lat, end_lon):
    """
    Calls the real-world-drone-simulation RRTStarPlanner.
    Returns a list of [lat, lon, alt] waypoints.
    """
    try:
        from core.environment_index import EnvironmentIndex
        from core.planner import RRTPlanner
        
        env_index = EnvironmentIndex()
        planner = RRTPlanner(env_index)
        route_points = [(start_lat, start_lon), (end_lat, end_lon)]
        path = planner.plan_route(route_points)
        return path
    except Exception as e:
        print(f"Integration error generating path: {e}")
        # Fallback to direct path
        return [(start_lat, start_lon, 50.0), (end_lat, end_lon, 50.0)]

def compute_path_distance(route):
    """
    Calculates total distance in km for a given route.
    """
    dist_km = 0.0
    for i in range(len(route) - 1):
        dist_km += haversine(
            (route[i][0], route[i][1]),
            (route[i+1][0], route[i+1][1])
        )
    return max(dist_km, 0.01)  # Ensure non-zero
