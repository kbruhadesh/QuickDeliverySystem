import os
from celery import Celery
from typing import List, Dict

# Read Redis URL from environment or fallback
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

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
        detailed_routes = optimizer.generate_collision_free_routes(result["assignments"])
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
    Continuous task representing the Simulation Engine state machine.
    Updates the physical location and broadcasts telemetry via Redis PubSub.
    Each drone orbits a center point — runs for 1000 ticks (seconds).
    """
    import redis
    import json
    import time
    import math

    r = redis.Redis.from_url(REDIS_URL)

    for step in range(1000):  # Run for 1000 seconds
        t = time.time()
        drones = []
        # Simulate 3 drones orbiting Hyderabad center
        for i in range(1, 4):
            radius = 0.02 * i
            lat = 17.3850 + radius * math.cos(t / (10 * i))
            lon = 78.4867 + radius * math.sin(t / (10 * i))
            drones.append({
                "id": f"D-0{i}",
                "status": "in-flight",
                "lat": lat,
                "lon": lon
            })

        r.publish("drone_telemetry", json.dumps({"drones": drones}))
        time.sleep(1)

    return {"message": "Simulation ended"}
