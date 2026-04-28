import math
import random
import numpy as np
from typing import List, Tuple, Dict
from shapely.geometry import Point, LineString, shape
from pyproj import Transformer
from .nfz_loader import OSMNFZLoader

class RRTStarPlanner:
    def __init__(self, step_size=200, max_iter=3000, radius=400):
        self.step_size = step_size
        self.max_iter = max_iter
        self.radius = radius
        self.FOCUS_FACTOR = 0.2
        self.nfz_loader = OSMNFZLoader()
        
        # Setup UTM projection for distance calculation (UTM Zone 44N - India)
        # EPSG:4326 is WGS84 (lat/lon), EPSG:32644 is UTM zone 44N
        self.transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
        self.transformer_to_latlon = Transformer.from_crs("EPSG:32644", "EPSG:4326", always_xy=True)

    def _latlon_to_utm(self, lat: float, lon: float) -> Tuple[float, float]:
        x, y = self.transformer_to_utm.transform(lon, lat)
        return x, y

    def _utm_to_latlon(self, x: float, y: float) -> Tuple[float, float]:
        lon, lat = self.transformer_to_latlon.transform(x, y)
        return lat, lon

    def _distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def _is_collision_free(self, p1: Tuple[float, float], p2: Tuple[float, float], no_fly_zones: List, goal=None) -> bool:
        min_x, max_x = min(p1[0], p2[0]), max(p1[0], p2[0])
        min_y, max_y = min(p1[1], p2[1]), max(p1[1], p2[1])
        
        line = None
        for zone in no_fly_zones:
            # Fast bounding box rejection
            bounds = zone.bounds
            if max_x < bounds[0] or min_x > bounds[2] or max_y < bounds[1] or min_y > bounds[3]:
                continue
                
            if line is None:
                line = LineString([p1, p2])
                
            if line.intersects(zone):
                # If goal is inside NFZ, allow the last step to touch it to complete delivery
                if goal and Point(goal).within(zone) and p2 == goal:
                    continue
                return False
        return True

    def _smooth_path(self, path: List[Tuple[float, float]], no_fly_zones: List) -> List[Tuple[float, float]]:
        """
        Greedy path smoothing: Attempts to connect non-adjacent nodes directly 
        to shortcut the jagged RRT* path.
        """
        if len(path) <= 2:
            return path
            
        smoothed_path = [path[0]]
        current_idx = 0
        
        while current_idx < len(path) - 1:
            furthest_valid_idx = current_idx + 1
            for j in range(len(path) - 1, current_idx + 1, -1):
                if self._is_collision_free(path[current_idx], path[j], no_fly_zones, goal=path[-1]):
                    furthest_valid_idx = j
                    break
                    
            smoothed_path.append(path[furthest_valid_idx])
            current_idx = furthest_valid_idx
            
        return smoothed_path

    def _get_buffered_nfz(self, min_lat, min_lon, max_lat, max_lon) -> List:
        # Fetch raw geojson points from OSM
        features = self.nfz_loader.get_nfz_features(min_lat, min_lon, max_lat, max_lon)
        buffered_polygons = []
        for feat in features:
            buffer_m = feat['properties'].get('buffer_m', 100)
            geom = shape(feat['geometry'])
            
            # Point in lat/lon
            lon, lat = geom.x, geom.y
            x, y = self._latlon_to_utm(lat, lon)
            utm_point = Point(x, y)
            
            # Buffer accurately in meters
            buffered_poly = utm_point.buffer(buffer_m)
            buffered_polygons.append(buffered_poly)
            
        return buffered_polygons

    def plan_path(self, start: Tuple[float, float], goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Plans a collision-free path using RRT* from start to goal.
        Automatically loads and caches OSM No-Fly Zones in the bounding box.
        Returns a list of (lat, lon) waypoints.
        """
        # Calculate Bounding Box with margin
        margin = 0.05
        min_lat = min(start[0], goal[0]) - margin
        max_lat = max(start[0], goal[0]) + margin
        min_lon = min(start[1], goal[1]) - margin
        max_lon = max(start[1], goal[1]) + margin
        
        # Load obstacles and convert to UTM
        no_fly_zones = self._get_buffered_nfz(min_lat, min_lon, max_lat, max_lon)
        
        start_utm = self._latlon_to_utm(start[0], start[1])
        goal_utm = self._latlon_to_utm(goal[0], goal[1])
        
        # Filter out NFZs that contain start or goal, otherwise we can never leave/arrive
        start_pt = Point(start_utm)
        goal_pt = Point(goal_utm)
        valid_nfzs = []
        for zone in no_fly_zones:
            if not (start_pt.within(zone) or goal_pt.within(zone)):
                valid_nfzs.append(zone)
        no_fly_zones = valid_nfzs
        
        # Bounds for sampling
        minx, miny = self._latlon_to_utm(min_lat, min_lon)
        maxx, maxy = self._latlon_to_utm(max_lat, max_lon)

        tree = {start_utm: None}
        costs = {start_utm: 0}

        goal_reached = False
        goal_reached_iter = -1

        for i in range(self.max_iter):
            # If we found the goal, run for a bit more to optimize, then break
            if goal_reached and i > goal_reached_iter + 150:
                break
                
            # Biased sampling towards goal
            if random.random() < self.FOCUS_FACTOR:
                random_point = goal_utm
            else:
                random_point = (random.uniform(minx, maxx), random.uniform(miny, maxy))
                
            # Find nearest node
            nearest_node = min(tree.keys(), key=lambda n: self._distance(n, random_point))
            direction = np.array(random_point) - np.array(nearest_node)
            length = np.linalg.norm(direction)
            
            if length == 0:
                continue
                
            if length < self.step_size:
                new_node = random_point
            else:
                new_node = tuple(np.array(nearest_node) + self.step_size * direction / length)
            
            if not (minx <= new_node[0] <= maxx and miny <= new_node[1] <= maxy):
                continue
                
            if not self._is_collision_free(nearest_node, new_node, no_fly_zones):
                continue
                
            tree[new_node] = nearest_node
            costs[new_node] = costs[nearest_node] + self._distance(nearest_node, new_node)
            
            # Rewire
            for node in list(tree.keys()):
                if node == new_node:
                    continue
                if self._distance(node, new_node) < self.radius and self._is_collision_free(new_node, node, no_fly_zones):
                    new_cost = costs[new_node] + self._distance(new_node, node)
                    if new_cost < costs[node]:
                        # A cycle check should ideally happen here, but triangle inequality mostly prevents it.
                        tree[node] = new_node
                        costs[node] = new_cost
            
            # Check if we reached goal
            if self._distance(new_node, goal_utm) < self.step_size:
                if self._is_collision_free(new_node, goal_utm, no_fly_zones, goal=goal_utm):
                    new_goal_cost = costs[new_node] + self._distance(new_node, goal_utm)
                    if goal_utm not in costs or new_goal_cost < costs[goal_utm]:
                        tree[goal_utm] = new_node
                        costs[goal_utm] = new_goal_cost
                        if not goal_reached:
                            goal_reached = True
                            goal_reached_iter = i

        if goal_reached:
            # Reconstruct path
            path = []
            node = goal_utm
            while node is not None:
                path.append(node)
                node = tree.get(node)
            path.reverse()
            
            # Smooth the path to remove zig-zags
            path = self._smooth_path(path, no_fly_zones)
            
            return [self._utm_to_latlon(x, y) for x, y in path]
                    
        # If no path found, return fallback
        print(f"⚠️ RRT* failed to find path. Returning straight line fallback.")
        return [start, goal]
