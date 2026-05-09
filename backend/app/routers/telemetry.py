"""
Telemetry Router - For real-time drone tracking data
Save as: backend/app/routers/telemetry.py
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from app.database import get_db
from app import models

router = APIRouter()


# Pydantic Schemas
class TelemetryResponse(BaseModel):
    id: str
    drone_id: str
    assignment_id: Optional[str]
    latitude: float
    longitude: float
    altitude: float
    battery_percentage: float
    speed: float
    heading: Optional[float]
    status: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


# API Endpoints

@router.get("/", response_model=List[TelemetryResponse])
def get_telemetry(
    drone_id: Optional[str] = None,
    assignment_id: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get telemetry data with optional filtering
    """
    try:
        query = db.query(models.Telemetry)
        
        # Filter by drone
        if drone_id:
            try:
                query = query.filter(models.Telemetry.drone_id == uuid.UUID(drone_id))
            except ValueError:
                # Try finding drone by drone_id string
                drone = db.query(models.Drone).filter(models.Drone.drone_id == drone_id).first()
                if drone:
                    query = query.filter(models.Telemetry.drone_id == drone.id)
        
        # Filter by assignment
        if assignment_id:
            try:
                query = query.filter(models.Telemetry.assignment_id == uuid.UUID(assignment_id))
            except ValueError:
                pass
        
        # Filter by time
        if since:
            query = query.filter(models.Telemetry.timestamp >= since)
        
        # Get results
        telemetry = query.order_by(models.Telemetry.timestamp.desc()).limit(limit).all()
        
        return [
            TelemetryResponse(
                id=str(t.id),
                drone_id=str(t.drone_id),
                assignment_id=str(t.assignment_id) if t.assignment_id else None,
                latitude=t.latitude,
                longitude=t.longitude,
                altitude=t.altitude,
                battery_percentage=t.battery_percentage,
                speed=t.speed,
                heading=t.heading,
                status=t.status,
                timestamp=t.timestamp
            )
            for t in telemetry
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest", response_model=List[TelemetryResponse])
def get_latest_telemetry(db: Session = Depends(get_db)):
    """
    Get latest telemetry for all active drones
    """
    try:
        # Get all active drones
        active_drones = db.query(models.Drone).filter(
            models.Drone.status.in_(['assigned', 'in_flight'])
        ).all()
        
        latest_telemetry = []
        
        for drone in active_drones:
            # Get most recent telemetry for this drone
            latest = db.query(models.Telemetry).filter(
                models.Telemetry.drone_id == drone.id
            ).order_by(
                models.Telemetry.timestamp.desc()
            ).first()
            
            if latest:
                latest_telemetry.append(
                    TelemetryResponse(
                        id=str(latest.id),
                        drone_id=str(latest.drone_id),
                        assignment_id=str(latest.assignment_id) if latest.assignment_id else None,
                        latitude=latest.latitude,
                        longitude=latest.longitude,
                        altitude=latest.altitude,
                        battery_percentage=latest.battery_percentage,
                        speed=latest.speed,
                        heading=latest.heading,
                        status=latest.status,
                        timestamp=latest.timestamp
                    )
                )
        
        return latest_telemetry
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live", response_model=List[TelemetryResponse])
def get_live_positions(db: Session = Depends(get_db)):
    """
    Get current positions of all drones (within last 10 seconds)
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(seconds=10)
        
        # Subquery to get latest telemetry ID for each drone
        from sqlalchemy import func
        
        latest_subquery = db.query(
            models.Telemetry.drone_id,
            func.max(models.Telemetry.timestamp).label('max_timestamp')
        ).filter(
            models.Telemetry.timestamp >= cutoff_time
        ).group_by(
            models.Telemetry.drone_id
        ).subquery()
        
        # Get the actual telemetry records
        telemetry = db.query(models.Telemetry).join(
            latest_subquery,
            (models.Telemetry.drone_id == latest_subquery.c.drone_id) &
            (models.Telemetry.timestamp == latest_subquery.c.max_timestamp)
        ).all()
        
        return [
            TelemetryResponse(
                id=str(t.id),
                drone_id=str(t.drone_id),
                assignment_id=str(t.assignment_id) if t.assignment_id else None,
                latitude=t.latitude,
                longitude=t.longitude,
                altitude=t.altitude,
                battery_percentage=t.battery_percentage,
                speed=t.speed,
                heading=t.heading,
                status=t.status,
                timestamp=t.timestamp
            )
            for t in telemetry
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
def cleanup_old_telemetry(days_old: int = 7, db: Session = Depends(get_db)):
    """
    Delete telemetry data older than specified days
    Use for maintenance to keep database size manageable
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = db.query(models.Telemetry).filter(
            models.Telemetry.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Deleted {deleted_count} telemetry records older than {days_old} days",
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
