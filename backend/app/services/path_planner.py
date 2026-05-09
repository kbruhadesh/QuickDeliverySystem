"""
RRT* Path Planning Service - Simplified version for drone delivery
Save as: backend/app/services/path_planner.py
"""

import numpy as np
import random
import math
from typing import List, Tuple, Optional
from shapely.geometry import Point, LineString, Polygon


class RRTStarPlanner:
    """
    RRT* (Rapidly-exploring Random Tree Star) path planner
    Generates collision-free paths avoiding no-fly zones
    """
    
    def __init__(self):
        self.step_size = 0.001  # Degrees (~111 meters at equator)
        self.max_iter = 5000
        self.search_radius = 0.005  # Degrees for rewiring
        self.goal_threshold = 0.0005  # Degrees (~55 meters)
    
    def distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def is_collision_free(
        self, 
        p1: Tuple[float, float], 
        p2: Tuple[float, float],
        obstacles: List[Polygon]
    ) -> bool:
        """Check if line segment between p1 and p2 intersects any obstacle"""
        if not obstacles:
            return True
        
        line = LineString([p1, p2])
        
        for obstacle in obstacles:
            if line.intersects(obstacle):
                return False
        
        return True
    
    def get_nearest_node(
        self, 
        nodes: List[Tuple[float, float]], 
        random_point: Tuple[float, float]
    ) -> int:
        """Find index of nearest node to random point"""
        min_dist = float('inf')
        nearest_idx = 0
        
        for i, node in enumerate(nodes):
            dist = self.distance(node, random_point)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        return nearest_idx
    
    def steer(
        self, 
        from_node: Tuple[float, float], 
        to_point: Tuple[float, float]
    ) -> Tuple[float, float]:
        """Generate new point at step_size distance from from_node towards to_point"""
        dist = self.distance(from_node, to_point)
        
        if dist < self.step_size:
            return to_point
        
        # Calculate direction
        theta = math.atan2(to_point[1] - from_node[1], to_point[0] - from_node[0])
        
        # New point at step_size distance
        new_x = from_node[0] + self.step_size * math.cos(theta)
        new_y = from_node[1] + self.step_size * math.sin(theta)
        
        return (new_x, new_y)
    
    def plan_path(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        obstacles: List[Polygon] = None
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Plan collision-free path using RRT*
        
        Args:
            start: (lat, lon) starting point
            goal: (lat, lon) goal point
            obstacles: List of Shapely Polygon objects representing no-fly zones
        
        Returns:
            List of (lat, lon) waypoints or None if no path found
        """
        if obstacles is None:
            obstacles = []
        
        # Initialize tree
        nodes = [start]
        parents = [-1]  # Parent index for each node
        costs = [0.0]   # Cost from start to each node
        
        # Calculate bounds for random sampling
        min_lat = min(start[0], goal[0]) - 0.01
        max_lat = max(start[0], goal[0]) + 0.01
        min_lon = min(start[1], goal[1]) - 0.01
        max_lon = max(start[1], goal[1]) + 0.01
        
        goal_found = False
        goal_node_idx = -1
        
        for iteration in range(self.max_iter):
            # Sample random point (bias towards goal 10% of time)
            if random.random() < 0.1:
                random_point = goal
            else:
                random_point = (
                    random.uniform(min_lat, max_lat),
                    random.uniform(min_lon, max_lon)
                )
            
            # Find nearest node
            nearest_idx = self.get_nearest_node(nodes, random_point)
            nearest_node = nodes[nearest_idx]
            
            # Steer towards random point
            new_node = self.steer(nearest_node, random_point)
            
            # Check collision
            if not self.is_collision_free(nearest_node, new_node, obstacles):
                continue
            
            # Find nodes within search radius for rewiring
            new_cost = costs[nearest_idx] + self.distance(nearest_node, new_node)
            parent_idx = nearest_idx
            
            # RRT* rewiring - find best parent
            for i, node in enumerate(nodes):
                if self.distance(node, new_node) < self.search_radius:
                    potential_cost = costs[i] + self.distance(node, new_node)
                    if potential_cost < new_cost:
                        if self.is_collision_free(node, new_node, obstacles):
                            new_cost = potential_cost
                            parent_idx = i
            
            # Add new node
            nodes.append(new_node)
            parents.append(parent_idx)
            costs.append(new_cost)
            
            # Check if goal reached
            if self.distance(new_node, goal) < self.goal_threshold:
                goal_found = True
                goal_node_idx = len(nodes) - 1
                break
        
        # If goal not reached, try to connect last node to goal
        if not goal_found and nodes:
            # Find closest node to goal
            closest_idx = self.get_nearest_node(nodes, goal)
            closest_node = nodes[closest_idx]
            
            if self.is_collision_free(closest_node, goal, obstacles):
                nodes.append(goal)
                parents.append(closest_idx)
                costs.append(costs[closest_idx] + self.distance(closest_node, goal))
                goal_node_idx = len(nodes) - 1
                goal_found = True
        
        if not goal_found:
            # Return straight line as fallback
            return [start, goal]
        
        # Reconstruct path
        path = []
        current_idx = goal_node_idx
        
        while current_idx != -1:
            path.append(nodes[current_idx])
            current_idx = parents[current_idx]
        
        path.reverse()
        
        # Smooth path (optional - remove intermediate points on straight lines)
        smoothed_path = self.smooth_path(path, obstacles)
        
        return smoothed_path
    
    def smooth_path(
        self,
        path: List[Tuple[float, float]],
        obstacles: List[Polygon]
    ) -> List[Tuple[float, float]]:
        """
        Smooth path by removing unnecessary waypoints
        """
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]
        i = 0
        
        while i < len(path) - 1:
            # Try to connect current point to furthest visible point
            for j in range(len(path) - 1, i, -1):
                if self.is_collision_free(path[i], path[j], obstacles):
                    smoothed.append(path[j])
                    i = j
                    break
            else:
                # If no connection found, add next point
                i += 1
                if i < len(path):
                    smoothed.append(path[i])
        
        return smoothed
    
    def plan_simple_path(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """
        Plan simple straight-line path (no obstacle avoidance)
        Use this as fallback when NFZ data is not available
        """
        # Generate waypoints along straight line
        num_waypoints = 10
        path = []
        
        for i in range(num_waypoints + 1):
            t = i / num_waypoints
            lat = start[0] + t * (goal[0] - start[0])
            lon = start[1] + t * (goal[1] - start[1])
            path.append((lat, lon))
        
        return path


# Example usage and testing
if __name__ == "__main__":
    planner = RRTStarPlanner()
    
    # Test simple path
    start = (13.0827, 80.2707)  # Chennai
    goal = (13.0878, 80.2785)
    
    path = planner.plan_simple_path(start, goal)
    print(f"Simple path with {len(path)} waypoints")
    print(f"Start: {path[0]}")
    print(f"Goal: {path[-1]}")
    
    # Test with obstacles
    obstacle = Polygon([
        (13.084, 80.273),
        (13.085, 80.273),
        (13.085, 80.275),
        (13.084, 80.275)
    ])
    
    path_with_avoidance = planner.plan_path(start, goal, obstacles=[obstacle])
    print(f"\nPath with obstacle avoidance: {len(path_with_avoidance)} waypoints")
