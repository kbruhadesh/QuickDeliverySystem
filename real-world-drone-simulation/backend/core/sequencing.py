"""
Phase 4: Route Sequencing
Deterministic algorithm to order delivery points.
NOT path planning - just decides the order.
"""
import math
import logging

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points in kilometers.
    Uses Haversine formula.
    """
    R = 6371.0  # Earth radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def compute_route_sequence(base_lat: float, base_lon: float, deliveries: list) -> list:
    """
    Compute optimal delivery sequence using nearest-neighbor insertion.
    
    Algorithm:
    1. Start with route = [BASE]
    2. For each unvisited delivery point:
       - Find position in current route that minimizes added distance
       - Insert at that position
    3. Return ordered route: BASE -> D1 -> D2 -> ... -> DN
    
    Args:
        base_lat: Base latitude
        base_lon: Base longitude
        deliveries: List of (lat, lon) tuples
    
    Returns:
        List of (lat, lon) tuples starting with base
    """
    if not deliveries:
        return [(base_lat, base_lon)]
    
    # Start with base
    route = [(base_lat, base_lon)]
    unvisited = deliveries.copy()
    
    # Greedy insertion: for each delivery, find best insertion point
    while unvisited:
        best_insertion = None
        best_position = None
        best_cost_increase = float('inf')
        
        # Try each unvisited delivery point
        for delivery in unvisited:
            # Try inserting at each position in current route
            for pos in range(1, len(route) + 1):
                # Calculate cost increase
                if pos == 1:
                    # Insert at start (after base)
                    cost = haversine_distance(
                        route[0][0], route[0][1],
                        delivery[0], delivery[1]
                    )
                elif pos == len(route):
                    # Insert at end
                    cost = haversine_distance(
                        route[-1][0], route[-1][1],
                        delivery[0], delivery[1]
                    )
                else:
                    # Insert in middle
                    prev_point = route[pos - 1]
                    next_point = route[pos]
                    old_dist = haversine_distance(
                        prev_point[0], prev_point[1],
                        next_point[0], next_point[1]
                    )
                    new_dist = (haversine_distance(
                        prev_point[0], prev_point[1],
                        delivery[0], delivery[1]
                    ) + haversine_distance(
                        delivery[0], delivery[1],
                        next_point[0], next_point[1]
                    ))
                    cost = new_dist - old_dist
                
                if cost < best_cost_increase:
                    best_cost_increase = cost
                    best_insertion = delivery
                    best_position = pos
        
        # Insert best delivery at best position
        if best_insertion:
            route.insert(best_position, best_insertion)
            unvisited.remove(best_insertion)
        else:
            # Fallback: append first unvisited
            route.append(unvisited.pop(0))
    
    # Add return to base at the end
    route.append((base_lat, base_lon))
    
    logger.info(f"Computed route sequence with {len(route)} points (including base and return)")
    return route


def get_route_segments(route: list) -> list:
    """
    Convert route into segments for path planning.
    Returns list of (start, end) tuples.
    """
    if len(route) < 2:
        return []
    
    segments = []
    for i in range(len(route) - 1):
        segments.append((route[i], route[i + 1]))
    
    return segments

