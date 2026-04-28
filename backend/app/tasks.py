import os
from celery import Celery
from typing import List, Dict

# Read Redis URL from environment or fallback
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "drone_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="tasks.run_optimization")
def run_optimization(drone_data: List[Dict], order_data: List[Dict], weather_data: Dict):
    """
    Background task to run the OR-Tools optimization engine.
    This prevents the main FastAPI thread from blocking during complex assignments.
    """
    from app.models import Drone, Order
    from app.services.drone_optimizer import DroneOptimizer
    
    # Reconstruct data classes
    drones = [Drone(**d) for d in drone_data]
    orders = [Order(**o) for o in order_data]
    
    optimizer = DroneOptimizer(drones=drones, orders=orders, weather_data=weather_data)
    result = optimizer.solve()
    
    if result.get("status") == "success":
        # Generate detailed collision-free routes with RRT*
        detailed_routes = optimizer.generate_collision_free_routes(result["assignments"])
        
        # Merge routes into the result payload
        # Note: Depending on payload size, this might be saved back to Postgres instead
        return {
            "status": "success",
            "total_distance_km": result["total_distance_km"],
            "solve_time_ms": result["solve_time_ms"],
            "assignments": [
                {
                    "drone_id": d_id,
                    "orders": route["orders"],
                    "path": route["path"],
                    "total_waypoints": route["total_waypoints"]
                }
                for d_id, route in detailed_routes.items()
            ]
        }
    
    return {"status": result.get("status", "failed")}

@celery_app.task(name="tasks.simulation_step")
def simulation_step():
    """
    Periodic task representing the Simulation Engine state machine tick.
    Updates the physical location, battery drain, and progress of each active drone.
    Can be hooked into Celery beat for recurring execution.
    """
    # 1. Fetch active drones and their current routes from DB/Cache
    # 2. Advance drone position one step along the path array
    # 3. Calculate battery drain using BatteryPredictor
    # 4. Handle Poisson distributed failures (5% chance)
    # 5. Broadcast `drone:telemetry` event via Websocket/Redis PubSub
    pass
