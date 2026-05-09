"""
Drones Router - Complete working implementation
Save as: backend/app/routers/drones.py
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.database import get_db
from app import models

router = APIRouter()


# Pydantic Schemas
class DroneResponse(BaseModel):
    id: str
    drone_id: str
    model: str
    max_payload: float
    max_range: float
    battery_capacity: int
    current_battery: float
    status: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    speed: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        }


class DroneUpdate(BaseModel):
    status: Optional[str] = None
    current_battery: Optional[float] = Field(None, ge=0, le=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = None
    speed: Optional[float] = None


# API Endpoints

@router.get("/", response_model=List[DroneResponse])
def get_all_drones(
    status: Optional[str] = None,
    min_battery: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Get all drones with optional filtering
    """
    try:
        query = db.query(models.Drone)
        
        if status:
            query = query.filter(models.Drone.status == status)
        
        if min_battery is not None:
            query = query.filter(models.Drone.current_battery >= min_battery)
        
        drones = query.all()
        
        return [
            DroneResponse(
                id=str(drone.id),
                drone_id=drone.drone_id,
                model=drone.model,
                max_payload=drone.max_payload,
                max_range=drone.max_range,
                battery_capacity=drone.battery_capacity,
                current_battery=drone.current_battery,
                status=drone.status,
                latitude=drone.latitude,
                longitude=drone.longitude,
                altitude=drone.altitude,
                speed=drone.speed,
                created_at=drone.created_at
            )
            for drone in drones
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch drones: {str(e)}")


@router.get("/available", response_model=List[DroneResponse])
def get_available_drones(
    min_battery: float = 30.0,
    max_payload_needed: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Get available drones for assignment
    Filters: status='idle', battery >= min_battery, payload capacity
    """
    try:
        query = db.query(models.Drone).filter(
            models.Drone.status == 'idle',
            models.Drone.current_battery >= min_battery
        )
        
        if max_payload_needed:
            query = query.filter(models.Drone.max_payload >= max_payload_needed)
        
        drones = query.all()
        
        return [
            DroneResponse(
                id=str(drone.id),
                drone_id=drone.drone_id,
                model=drone.model,
                max_payload=drone.max_payload,
                max_range=drone.max_range,
                battery_capacity=drone.battery_capacity,
                current_battery=drone.current_battery,
                status=drone.status,
                latitude=drone.latitude,
                longitude=drone.longitude,
                altitude=drone.altitude,
                speed=drone.speed,
                created_at=drone.created_at
            )
            for drone in drones
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drone_id}", response_model=DroneResponse)
def get_drone(drone_id: str, db: Session = Depends(get_db)):
    """
    Get a specific drone by ID or drone_id
    """
    try:
        # Try UUID first
        try:
            drone = db.query(models.Drone).filter(models.Drone.id == uuid.UUID(drone_id)).first()
        except ValueError:
            # If not UUID, try drone_id string
            drone = db.query(models.Drone).filter(models.Drone.drone_id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
        
        return DroneResponse(
            id=str(drone.id),
            drone_id=drone.drone_id,
            model=drone.model,
            max_payload=drone.max_payload,
            max_range=drone.max_range,
            battery_capacity=drone.battery_capacity,
            current_battery=drone.current_battery,
            status=drone.status,
            latitude=drone.latitude,
            longitude=drone.longitude,
            altitude=drone.altitude,
            speed=drone.speed,
            created_at=drone.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{drone_id}", response_model=DroneResponse)
def update_drone(drone_id: str, drone_update: DroneUpdate, db: Session = Depends(get_db)):
    """
    Update drone status, battery, or location
    """
    try:
        # Find drone
        try:
            drone = db.query(models.Drone).filter(models.Drone.id == uuid.UUID(drone_id)).first()
        except ValueError:
            drone = db.query(models.Drone).filter(models.Drone.drone_id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
        
        # Update fields
        if drone_update.status is not None:
            drone.status = drone_update.status
        
        if drone_update.current_battery is not None:
            drone.current_battery = drone_update.current_battery
        
        if drone_update.latitude is not None:
            drone.latitude = drone_update.latitude
        
        if drone_update.longitude is not None:
            drone.longitude = drone_update.longitude
        
        if drone_update.altitude is not None:
            drone.altitude = drone_update.altitude
        
        if drone_update.speed is not None:
            drone.speed = drone_update.speed
        
        db.commit()
        db.refresh(drone)
        
        return DroneResponse(
            id=str(drone.id),
            drone_id=drone.drone_id,
            model=drone.model,
            max_payload=drone.max_payload,
            max_range=drone.max_range,
            battery_capacity=drone.battery_capacity,
            current_battery=drone.current_battery,
            status=drone.status,
            latitude=drone.latitude,
            longitude=drone.longitude,
            altitude=drone.altitude,
            speed=drone.speed,
            created_at=drone.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{drone_id}/telemetry", response_model=List[dict])
def get_drone_telemetry(
    drone_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get recent telemetry data for a specific drone
    """
    try:
        # Find drone
        try:
            drone = db.query(models.Drone).filter(models.Drone.id == uuid.UUID(drone_id)).first()
        except ValueError:
            drone = db.query(models.Drone).filter(models.Drone.drone_id == drone_id).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
        
        # Get telemetry
        telemetry = db.query(models.Telemetry).filter(
            models.Telemetry.drone_id == drone.id
        ).order_by(
            models.Telemetry.timestamp.desc()
        ).limit(limit).all()
        
        return [
            {
                "id": str(t.id),
                "latitude": t.latitude,
                "longitude": t.longitude,
                "altitude": t.altitude,
                "battery_percentage": t.battery_percentage,
                "speed": t.speed,
                "heading": t.heading,
                "status": t.status,
                "timestamp": t.timestamp.isoformat()
            }
            for t in telemetry
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
