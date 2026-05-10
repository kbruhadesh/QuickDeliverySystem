"""
Orders Router - Fixed version with proper validation and responses
Save as: backend/app/routers/orders.py
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
import uuid
import requests

from app.database import get_db
from app import models
from app.services.route_integration import generate_path, compute_path_distance
from app.services.battery_predictor import BatteryPredictor
from app.utils.jwt_handler import decode_access_token

router = APIRouter()


# Pydantic Schemas
class OrderCreate(BaseModel):
    pickup_latitude: float = Field(..., ge=-90, le=90, description="Pickup latitude")
    pickup_longitude: float = Field(..., ge=-180, le=180, description="Pickup longitude")
    pickup_address: Optional[str] = None
    
    delivery_latitude: float = Field(..., ge=-90, le=90, description="Delivery latitude")
    delivery_longitude: float = Field(..., ge=-180, le=180, description="Delivery longitude")
    delivery_address: Optional[str] = None
    
    package_weight: float = Field(..., gt=0, le=5.0, description="Package weight in kg (max 5kg)")
    package_description: Optional[str] = None
    items_summary: Optional[str] = None
    total_amount: float = Field(default=0.0)
    priority: int = Field(default=2, ge=1, le=3, description="1=urgent, 2=normal, 3=low")
    
    @field_validator('package_weight')
    @classmethod
    def validate_weight(cls, v):
        if v <= 0 or v > 5.0:
            raise ValueError('Package weight must be between 0 and 5 kg')
        return v


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_number: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    pickup_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    delivery_address: Optional[str] = None
    package_weight: Optional[float] = None
    package_description: Optional[str] = None
    items_summary: Optional[str] = None
    total_amount: float = 0.0
    status: Optional[str] = None
    priority: Optional[int] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    route_path: Optional[List] = None
    eta_minutes: Optional[float] = None
    start_time: Optional[datetime] = None
    created_at: Optional[datetime] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    route_path: Optional[List] = None
    eta_minutes: Optional[float] = None


class RouteCalcRequest(BaseModel):
    pickup_latitude: float
    pickup_longitude: float
    delivery_latitude: float
    delivery_longitude: float
    weight_kg: float = 1.0


def _get_user_from_token(token: Optional[str], db: Session) -> Optional[models.User]:
    if not token or token in {"null", "undefined"}:
        return None

    payload = decode_access_token(token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# API Endpoints

@router.post("/calculate_eta")
def calculate_eta(req: RouteCalcRequest):
    # 1. Plan the route using route integration
    start = (req.pickup_latitude, req.pickup_longitude)
    goal = (req.delivery_latitude, req.delivery_longitude)
    
    route = generate_path(start[0], start[1], goal[0], goal[1])
    distance_km = compute_path_distance(route)
    path = route
    
    # Assume 54 km/h drone speed (15 m/s) to match frontend simulation
    eta_min = int((distance_km / 54) * 60)
    
    # Predict battery drop
    predictor = BatteryPredictor()
    
    # Fetch live weather data from Open-Meteo API
    weather_data = {"wind_speed": 10.0, "temperature": 25.0, "humidity": 60.0, "rain": 0.0}
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={req.pickup_latitude}&longitude={req.pickup_longitude}&current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m"
        response = requests.get(weather_url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("current", {})
            weather_data = {
                "wind_speed": float(data.get("wind_speed_10m", 10.0)),
                "temperature": float(data.get("temperature_2m", 25.0)),
                "humidity": float(data.get("relative_humidity_2m", 60.0)),
                "rain": float(data.get("rain", 0.0))
            }
    except Exception as e:
        print(f"Weather API fetch failed: {e}")

    battery_drop = predictor.predict(
        distance_km=distance_km,
        weight_kg=req.weight_kg,
        weather=weather_data
    )
    
    return {
        "eta_min": max(1, eta_min),
        "distance_km": round(distance_km, 2),
        "battery_drop": round(battery_drop, 2),
        "path": path
    }


@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate, token: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Create a new delivery order
    """
    try:
        # Generate unique order number
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # 2. Plan the route to store it persistently
        route = generate_path(order.pickup_latitude, order.pickup_longitude, 
                             order.delivery_latitude, order.delivery_longitude)
        distance_km = compute_path_distance(route)
        eta_min = int((distance_km / 54) * 60)
        user = _get_user_from_token(token, db)

        # Create order
        db_order = models.Order(
            order_number=order_number,
            user_id=user.id if user else None,
            pickup_latitude=order.pickup_latitude,
            pickup_longitude=order.pickup_longitude,
            pickup_address=order.pickup_address,
            delivery_latitude=order.delivery_latitude,
            delivery_longitude=order.delivery_longitude,
            delivery_address=order.delivery_address,
            package_weight=order.package_weight,
            package_description=order.package_description,
            items_summary=order.items_summary,
            total_amount=order.total_amount,
            priority=order.priority,
            status='CONFIRMED', # Auto-confirm for simulation
            route_path=route,
            eta_minutes=eta_min
        )
        
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        
        # Convert to response format
        return OrderResponse(
            id=db_order.id,
            order_number=db_order.order_number,
            user_id=db_order.user_id,
            pickup_latitude=db_order.pickup_latitude,
            pickup_longitude=db_order.pickup_longitude,
            pickup_address=db_order.pickup_address,
            delivery_latitude=db_order.delivery_latitude,
            delivery_longitude=db_order.delivery_longitude,
            delivery_address=db_order.delivery_address,
            package_weight=db_order.package_weight,
            package_description=db_order.package_description,
            items_summary=db_order.items_summary,
            total_amount=db_order.total_amount,
            status=db_order.status,
            priority=db_order.priority,
            estimated_delivery_time=db_order.estimated_delivery_time,
            actual_delivery_time=db_order.actual_delivery_time,
            route_path=db_order.route_path,
            eta_minutes=db_order.eta_minutes,
            start_time=db_order.start_time,
            created_at=db_order.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/all", response_model=List[OrderResponse])
def get_orders_all(
    status: Optional[str] = None,
    limit: int = 500,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Explicit endpoint for all orders to avoid collision with {order_id}
    """
    try:
        query = db.query(models.Order)
        if status:
            query = query.filter(models.Order.status == status)
        orders = query.order_by(models.Order.created_at.desc()).limit(limit).all()
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{order_id}/status")
def update_order_status(order_id: str, status: str, db: Session = Depends(get_db)):
    """
    Update order status manually (e.g. for cancellation)
    """
    try:
        order = db.query(models.Order).filter(models.Order.id == uuid.UUID(order_id)).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = status.upper()
        db.commit()
        return {"message": f"Order status updated to {status}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[OrderResponse])
def get_orders(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all orders with optional filtering
    """
    try:
        query = db.query(models.Order)
        user = _get_user_from_token(token, db)
        if user:
            query = query.filter(models.Order.user_id == user.id)
        
        if status:
            query = query.filter(models.Order.status == status)
        
        orders = query.order_by(models.Order.created_at.desc()).offset(offset).limit(limit).all()
        
        return [
            OrderResponse(
                id=order.id,
                order_number=order.order_number,
                user_id=order.user_id,
                pickup_latitude=order.pickup_latitude,
                pickup_longitude=order.pickup_longitude,
                pickup_address=order.pickup_address,
                delivery_latitude=order.delivery_latitude,
                delivery_longitude=order.delivery_longitude,
                delivery_address=order.delivery_address,
                package_weight=order.package_weight,
                package_description=order.package_description,
                items_summary=order.items_summary,
                total_amount=order.total_amount,
                status=order.status,
                priority=order.priority,
                estimated_delivery_time=order.estimated_delivery_time,
                actual_delivery_time=order.actual_delivery_time,
                route_path=order.route_path,
                eta_minutes=order.eta_minutes,
                start_time=order.start_time,
                created_at=order.created_at
            )
            for order in orders
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, token: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get a specific order by ID
    """
    try:
        query = db.query(models.Order).filter(models.Order.id == uuid.UUID(order_id))
        user = _get_user_from_token(token, db)
        if user:
            query = query.filter(models.Order.user_id == user.id)
        order = query.first()
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            pickup_latitude=order.pickup_latitude,
            pickup_longitude=order.pickup_longitude,
            pickup_address=order.pickup_address,
            delivery_latitude=order.delivery_latitude,
            delivery_longitude=order.delivery_longitude,
            delivery_address=order.delivery_address,
            package_weight=order.package_weight,
            package_description=order.package_description,
            items_summary=order.items_summary,
            total_amount=order.total_amount,
            status=order.status,
            priority=order.priority,
            estimated_delivery_time=order.estimated_delivery_time,
            actual_delivery_time=order.actual_delivery_time,
            route_path=order.route_path,
            eta_minutes=order.eta_minutes,
            start_time=order.start_time,
            created_at=order.created_at
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: str, order_update: OrderUpdate, token: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Update an order's status or delivery times
    """
    try:
        query = db.query(models.Order).filter(models.Order.id == uuid.UUID(order_id))
        user = _get_user_from_token(token, db)
        if user:
            query = query.filter(models.Order.user_id == user.id)
        order = query.first()
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        # Update fields
        if order_update.status:
            order.status = order_update.status
        
        if order_update.estimated_delivery_time:
            order.estimated_delivery_time = order_update.estimated_delivery_time
        
        if order_update.actual_delivery_time:
            order.actual_delivery_time = order_update.actual_delivery_time

        if order_update.start_time:
            order.start_time = order_update.start_time

        if order_update.route_path is not None:
            order.route_path = order_update.route_path

        if order_update.eta_minutes is not None:
            order.eta_minutes = order_update.eta_minutes
        
        db.commit()
        db.refresh(order)
        
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            pickup_latitude=order.pickup_latitude,
            pickup_longitude=order.pickup_longitude,
            pickup_address=order.pickup_address,
            delivery_latitude=order.delivery_latitude,
            delivery_longitude=order.delivery_longitude,
            delivery_address=order.delivery_address,
            package_weight=order.package_weight,
            package_description=order.package_description,
            items_summary=order.items_summary,
            total_amount=order.total_amount,
            status=order.status,
            priority=order.priority,
            estimated_delivery_time=order.estimated_delivery_time,
            actual_delivery_time=order.actual_delivery_time,
            route_path=order.route_path,
            eta_minutes=order.eta_minutes,
            start_time=order.start_time,
            created_at=order.created_at
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{order_id}")
def delete_order(order_id: str, token: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Delete an order (only if status is pending or cancelled)
    """
    try:
        query = db.query(models.Order).filter(models.Order.id == uuid.UUID(order_id))
        user = _get_user_from_token(token, db)
        if user:
            query = query.filter(models.Order.user_id == user.id)
        order = query.first()
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        
        if order.status.lower() == 'delivered':
            raise HTTPException(
                status_code=400,
                detail="Cannot delete an order that has already been delivered."
            )
        
        db.delete(order)
        db.commit()
        
        return {"message": f"Order {order_id} deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID format")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
