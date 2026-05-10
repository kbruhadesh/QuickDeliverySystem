import os
import sys
import math
from functools import lru_cache

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


def _normalize_path(path):
    normalized = []
    for point in path or []:
        if len(point) < 2:
            continue
        normalized.append([float(point[0]), float(point[1])])
    return normalized


def _sample_direct_path(start_lat, start_lon, end_lat, end_lon, spacing_km=1.0):
    distance_km = haversine((start_lat, start_lon), (end_lat, end_lon))
    segments = max(2, int(math.ceil(distance_km / spacing_km)))
    return [
        [
            start_lat + (end_lat - start_lat) * (i / segments),
            start_lon + (end_lon - start_lon) * (i / segments)
        ]
        for i in range(segments + 1)
    ]


@lru_cache(maxsize=1)
def _get_environment_index():
    from core.environment_index import EnvironmentIndex
    return EnvironmentIndex()


def generate_path(start_lat, start_lon, end_lat, end_lon):
    """
    Calls the real-world-drone-simulation RRTStarPlanner.
    Returns a list of [lat, lon] waypoints.
    """
    try:
        from core.planner import RRTPlanner

        direct_distance_km = haversine((start_lat, start_lon), (end_lat, end_lon))
        distance_m = direct_distance_km * 1000
        step_size = min(500.0, max(20.0, distance_m / 300.0))
        max_iterations = max(10000, int((distance_m / step_size) * 120))

        env_index = _get_environment_index()
        planner = RRTPlanner(
            env_index,
            max_iterations=max_iterations,
            step_size=step_size,
            goal_bias=0.25
        )
        route_points = [(start_lat, start_lon), (end_lat, end_lon)]
        path = _normalize_path(planner.plan_route(route_points))
        if len(path) >= 2:
            return path
    except Exception as e:
        print(f"Integration error generating path: {e}")

    # Last-resort fallback: keep enough waypoints for animation/distance instead
    # of collapsing to a two-point line if the external RRT cannot solve a segment.
    return _sample_direct_path(start_lat, start_lon, end_lat, end_lon)

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
