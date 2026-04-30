from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from app.database import Base, engine
from app.routers import auth, address, store, order
from app.db_models import user, address as address_model, store as store_model, product as product_model, assignment

app = FastAPI(title="Drone Delivery System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.services.battery_predictor import BatteryPredictor
from app.services.nfz_loader import OSMNFZLoader
from app.tasks import run_optimization, simulation_step, celery_app
from celery.result import AsyncResult

# Create database tables
Base.metadata.create_all(bind=engine)

# Include transactional routers
app.include_router(auth.router)
app.include_router(address.router)
app.include_router(store.router)
app.include_router(order.router)

# Pydantic Schemas for Requests
class WeatherData(BaseModel):
    wind_speed: float = 10.0
    temperature: float = 25.0
    humidity: float = 60.0
    rain: float = 0.0

class BatteryPredictionRequest(BaseModel):
    distance_km: float
    weight_kg: float
    weather: WeatherData

class DroneInput(BaseModel):
    id: str
    max_payload: float
    battery_capacity: float
    latitude: float
    longitude: float

class OrderInput(BaseModel):
    id: str
    package_weight: float
    pickup_latitude: float
    pickup_longitude: float
    delivery_latitude: float
    delivery_longitude: float

class OptimizationRequest(BaseModel):
    drones: List[DroneInput]
    orders: List[OrderInput]
    weather: WeatherData

# Initialize services
predictor = BatteryPredictor()

@app.get("/")
def root():
    return {"message": "Drone Delivery API v1.0"}

@app.post("/api/predict_battery")
def predict_battery(req: BatteryPredictionRequest):
    """
    Predict battery consumption using the Random Forest ML Model
    """
    consumption = predictor.predict(
        distance_km=req.distance_km,
        weight_kg=req.weight_kg,
        weather=req.weather.model_dump()
    )
    return {
        "predicted_consumption_percent": round(consumption, 2),
        "status": "success"
    }

@app.post("/api/optimize_routes")
def optimize_routes(req: OptimizationRequest):
    """
    Trigger the OR-Tools optimization engine via Celery background task
    """
    # Trigger the celery task asynchronously
    task = run_optimization.delay(
        [d.model_dump() for d in req.drones],
        [o.model_dump() for o in req.orders],
        req.weather.model_dump()
    )
    return {
        "message": "Optimization task started in the background",
        "task_id": task.id
    }

@app.post("/api/simulation/step")
def trigger_simulation_step():
    """
    Manually trigger one tick of the simulation state machine
    """
    simulation_step.delay()
    return {"message": "Simulation step triggered"}

@app.get("/api/tasks/{task_id}")
def get_task_status(task_id: str):
    """
    Check the status of a Celery background task
    """
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == 'PENDING':
        return {"status": "pending"}
    elif task_result.state != 'FAILURE':
        return task_result.result
    else:
        return {"status": "failure", "error": str(task_result.info)}

@app.get("/api/nfz")
def get_nfz(min_lat: float, min_lon: float, max_lat: float, max_lon: float):
    """
    Fetch raw OSM No-Fly Zones for frontend visualization
    """
    loader = OSMNFZLoader()
    features = loader.get_nfz_features(min_lat, min_lon, max_lat, max_lon)
    return {"type": "FeatureCollection", "features": features}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
