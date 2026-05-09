"""
Admin Router - For system administration and management
Save as: backend/app/routers/admin.py
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
class DroneCreate(BaseModel):
    drone_id: str = Field(..., description="Unique drone identifier")
    model: str
    max_payload: float = Field(..., gt=0, le=10, description="Max payload in kg")
    max_range: float = Field(..., gt=0, description="Max range in km")
    battery_capacity: int = Field(..., gt=0, description="Battery capacity in mAh")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class SystemStats(BaseModel):
    total_drones: int
    active_drones: int
    idle_drones: int
    total_orders: int
    pending_orders: int
    completed_orders: int
    active_assignments: int
    total_telemetry_points: int


@router.get("/nfz")
def get_no_fly_zones(
    min_lat: float = 17.3,
    min_lon: float = 78.3,
    max_lat: float = 17.5,
    max_lon: float = 78.5
):
    """
    Get No-Fly Zones from OSM within bounding box
    """
    try:
        from app.services.nfz_loader import OSMNFZLoader
        loader = OSMNFZLoader()
        features = loader.get_nfz_features(min_lat, min_lon, max_lat, max_lon)
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        # Fallback to empty collection if service fails
        return {"type": "FeatureCollection", "features": []}


# API Endpoints

@router.get("/stats", response_model=SystemStats)
def get_system_stats(db: Session = Depends(get_db)):
    """
    Get comprehensive system statistics
    """
    try:
        stats = SystemStats(
            total_drones=db.query(models.Drone).count(),
            active_drones=db.query(models.Drone).filter(
                models.Drone.status.in_(['assigned', 'in_flight'])
            ).count(),
            idle_drones=db.query(models.Drone).filter(
                models.Drone.status == 'idle'
            ).count(),
            total_orders=db.query(models.Order).count(),
            pending_orders=db.query(models.Order).filter(
                models.Order.status == 'pending'
            ).count(),
            completed_orders=db.query(models.Order).filter(
                models.Order.status == 'delivered'
            ).count(),
            active_assignments=db.query(models.Assignment).filter(
                models.Assignment.status == 'active'
            ).count(),
            total_telemetry_points=db.query(models.Telemetry).count()
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drones", status_code=201)
def create_drone(drone: DroneCreate, db: Session = Depends(get_db)):
    """
    Add a new drone to the fleet
    """
    try:
        # Check if drone_id already exists
        existing = db.query(models.Drone).filter(
            models.Drone.drone_id == drone.drone_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Drone with ID {drone.drone_id} already exists"
            )
        
        # Create drone
        db_drone = models.Drone(
            drone_id=drone.drone_id,
            model=drone.model,
            max_payload=drone.max_payload,
            max_range=drone.max_range,
            battery_capacity=drone.battery_capacity,
            current_battery=100.0,
            status='idle',
            latitude=drone.latitude,
            longitude=drone.longitude
        )
        
        db.add(db_drone)
        db.commit()
        db.refresh(db_drone)
        
        return {
            "message": f"Drone {drone.drone_id} added successfully",
            "drone_id": str(db_drone.id),
            "drone_identifier": db_drone.drone_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/drones/{drone_id}")
def delete_drone(drone_id: str, db: Session = Depends(get_db)):
    """
    Remove a drone from the fleet (only if idle)
    """
    try:
        # Find drone
        try:
            drone = db.query(models.Drone).filter(
                models.Drone.id == uuid.UUID(drone_id)
            ).first()
        except ValueError:
            drone = db.query(models.Drone).filter(
                models.Drone.drone_id == drone_id
            ).first()
        
        if not drone:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
        
        if drone.status != 'idle':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete drone with status '{drone.status}'. Only idle drones can be deleted."
            )
        
        db.delete(drone)
        db.commit()
        
        return {"message": f"Drone {drone_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/drones/{drone_id}")
def update_drone(drone_id: str, update: DroneCreate, db: Session = Depends(get_db)):
    """
    Update an existing drone's details
    """
    try:
        # Find drone
        try:
            db_drone = db.query(models.Drone).filter(
                models.Drone.id == uuid.UUID(drone_id)
            ).first()
        except ValueError:
            db_drone = db.query(models.Drone).filter(
                models.Drone.drone_id == drone_id
            ).first()
        
        if not db_drone:
            raise HTTPException(status_code=404, detail=f"Drone {drone_id} not found")
        
        # Update fields
        db_drone.drone_id = update.drone_id
        db_drone.model = update.model
        db_drone.max_payload = update.max_payload
        db_drone.max_range = update.max_range
        db_drone.battery_capacity = update.battery_capacity
        
        db.commit()
        db.refresh(db_drone)
        
        return {
            "message": f"Drone {db_drone.drone_id} updated successfully",
            "drone_id": str(db_drone.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-system")
def reset_system(db: Session = Depends(get_db)):
    """
    Reset system to clean state (FOR TESTING ONLY)
    Deletes all orders, assignments, and telemetry
    Resets all drones to idle with 100% battery
    """
    try:
        # Delete all telemetry
        db.query(models.Telemetry).delete()
        
        # Delete all assignments
        db.query(models.Assignment).delete()
        
        # Delete all orders
        db.query(models.Order).delete()
        
        # Reset all drones
        drones = db.query(models.Drone).all()
        for drone in drones:
            drone.status = 'idle'
            drone.current_battery = 100.0
            drone.speed = 0
        
        db.commit()
        
        return {
            "message": "System reset successfully",
            "drones_reset": len(drones),
            "warning": "All orders, assignments, and telemetry have been deleted"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health-detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with component status
    """
    try:
        # Test database
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        
        # Check drone fleet
        total_drones = db.query(models.Drone).count()
        low_battery_drones = db.query(models.Drone).filter(
            models.Drone.current_battery < 30
        ).count()
        
        # Check pending orders
        pending_orders = db.query(models.Order).filter(
            models.Order.status == 'pending'
        ).count()
        
        # Check stuck assignments (active for > 1 hour)
        from datetime import timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        stuck_assignments = db.query(models.Assignment).filter(
            models.Assignment.status == 'active',
            models.Assignment.assigned_at < one_hour_ago
        ).count()
        
        health_status = {
            "overall": "healthy",
            "database": db_status,
            "fleet": {
                "total_drones": total_drones,
                "low_battery_count": low_battery_drones,
                "status": "warning" if low_battery_drones > 0 else "healthy"
            },
            "operations": {
                "pending_orders": pending_orders,
                "stuck_assignments": stuck_assignments,
                "status": "warning" if stuck_assignments > 0 else "healthy"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Set overall status
        if low_battery_drones > total_drones // 2 or stuck_assignments > 5:
            health_status["overall"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "overall": "unhealthy",
            "database": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
