from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from typing import List, Dict, Tuple
from app.models import Drone, Order
import math
from .route_integration import generate_path, compute_path_distance

class DroneOptimizer:
    def __init__(self, drones: List[Drone], orders: List[Order], weather_data: dict):
        self.drones = drones
        self.orders = orders
        self.weather = weather_data
        
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km using advanced path generation"""
        route = generate_path(lat1, lon1, lat2, lon2)
        return compute_path_distance(route)
    
    def build_distance_matrix(self) -> np.ndarray:
        """
        Build distance matrix:
        - Rows: drones + orders (depot + delivery points)
        - Cols: same
        Uses straight-line distance (Haversine) as heuristic
        RRT* will compute actual collision-free path later
        """
        n_drones = len(self.drones)
        n_orders = len(self.orders)
        n_total = n_drones + n_orders
        
        matrix = np.zeros((n_total, n_total))
        
        # Drone locations (depots)
        drone_locs = [(d.latitude, d.longitude) for d in self.drones]
        # Order pickup locations
        order_locs = [(o.pickup_latitude, o.pickup_longitude) for o in self.orders]
        
        all_locs = drone_locs + order_locs
        
        for i in range(n_total):
            for j in range(n_total):
                if i != j:
                    matrix[i][j] = self.haversine_distance(
                        all_locs[i][0], all_locs[i][1],
                        all_locs[j][0], all_locs[j][1]
                    )
        
        return matrix
    
    def create_data_model(self):
        """Create data dict for OR-Tools"""
        distance_matrix = self.build_distance_matrix()
        
        # Convert to integer meters (OR-Tools works with integers)
        distance_matrix_int = (distance_matrix * 1000).astype(int)
        
        n_drones = len(self.drones)
        
        data = {
            'distance_matrix': distance_matrix_int.tolist(),
            'num_vehicles': n_drones,  # Number of drones
            'depot': 0,  # All drones start from index 0 (can be adjusted)
            'drone_capacities': [d.max_payload for d in self.drones],
            'order_weights': [o.package_weight for o in self.orders],
            'drone_battery_max': [d.battery_capacity for d in self.drones],
        }
        
        return data
    
    def solve(self) -> Dict:
        """
        Solve multi-drone VRP using OR-Tools
        Returns: dict with assignments {drone_id: [order_ids]}
        """
        data = self.create_data_model()
        
        # Create routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        # Create routing model
        routing = pywrapcp.RoutingModel(manager)
        
        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add capacity constraint (payload weight)
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            n_drones = len(self.drones)
            if from_node < n_drones:
                return 0  # Depots have no demand
            order_idx = from_node - n_drones
            if order_idx < len(data['order_weights']):
                return int(data['order_weights'][order_idx] * 1000)  # Convert to grams
            return 0
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [int(cap * 1000) for cap in data['drone_capacities']],  # vehicle max capacities
            True,  # start cumul to zero
            'Capacity'
        )
        
        # Add distance constraint (battery range approximation)
        # Assume 1km uses 2% battery (adjust based on your battery model)
        BATTERY_PER_KM = 2.0  # percentage
        
        def battery_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            dist_km = data['distance_matrix'][from_node][to_node] / 1000
            battery_used = int(dist_km * BATTERY_PER_KM * 100)  # Scale to integer
            return battery_used
        
        battery_callback_index = routing.RegisterTransitCallback(battery_callback)
        routing.AddDimension(
            battery_callback_index,
            0,  # no slack
            10000,  # max battery capacity (100% = 10000 in scaled units)
            True,
            'Battery'
        )
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 2  # 2 second limit per requirements
        
        # Solve
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            return {"status": "no_solution", "assignments": {}}
        
        # Extract solution
        assignments = {}
        total_distance = 0
        
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            route_orders = []
            route_distance = 0
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                
                # If this is an order (not a depot)
                n_drones = len(self.drones)
                if node >= n_drones:
                    order_idx = node - n_drones
                    if order_idx < len(self.orders):
                        route_orders.append(self.orders[order_idx].id)
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
            
            if route_orders:
                assignments[self.drones[vehicle_id].id] = {
                    'orders': route_orders,
                    'distance_m': route_distance,
                    'drone': self.drones[vehicle_id]
                }
                total_distance += route_distance
        
        return {
            "status": "success",
            "assignments": assignments,
            "total_distance_km": round(total_distance / 1000, 2),
            "solve_time_ms": solution.SolveTime() if hasattr(solution, 'SolveTime') else 0
        }
    
    def generate_collision_free_routes(self, assignments: Dict) -> Dict:
        """
        For each drone assignment, use RRT* to generate collision-free path
        """
        detailed_routes = {}
        
        for drone_id, assignment_data in assignments.items():
            order_ids = assignment_data['orders']
            drone = assignment_data['drone']
            
            # Start from drone's current location
            current_pos = (drone.latitude, drone.longitude)
            full_path = [current_pos]
            
            for order_id in order_ids:
                order = next(o for o in self.orders if o.id == order_id)
                pickup = (order.pickup_latitude, order.pickup_longitude)
                delivery = (order.delivery_latitude, order.delivery_longitude)
                
                # RRT* from current position to pickup
                path_to_pickup = generate_path(current_pos[0], current_pos[1], pickup[0], pickup[1])
                
                if path_to_pickup:
                    full_path.extend(path_to_pickup[1:])  # Skip duplicate start
                    
                    # RRT* from pickup to delivery
                    path_to_delivery = generate_path(pickup[0], pickup[1], delivery[0], delivery[1])
                    
                    if path_to_delivery:
                        full_path.extend(path_to_delivery[1:])
                        current_pos = delivery
            
            detailed_routes[drone_id] = {
                'path': full_path,
                'orders': order_ids,
                'total_waypoints': len(full_path)
            }
        
        return detailed_routes
