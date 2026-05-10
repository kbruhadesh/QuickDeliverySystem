"""
Assignments Router - Complete implementation with RRT* path planning
Save as: backend/app/routers/assignments.py
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timedelta
import uuid
import math

from app.database import get_db
from app import models
from app.services.battery_predictor import BatteryPredictor
from app.services.route_integration import generate_path, compute_path_distance

router = APIRouter()


# Pydantic Schemas
class AssignmentRequest(BaseModel):
    order_id: str


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    drone_id: str
    order_id: str
    status: str
    total_distance: Optional[float]
    estimated_duration: Optional[float]
    predicted_battery_consumption: Optional[float]
    route_path: Optional[List[List[float]]]  # [[lat, lon], ...]
    assigned_at: datetime
    
class OptimizeRequest(BaseModel):
    order_ids: List[str]


# Helper Functions

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate true distance in km between two points using real route planning"""
    route = generate_path(lat1, lon1, lat2, lon2)
    return compute_path_distance(route)


def find_nearest_available_drone(
    order: models.Order,
    db: Session,
    min_battery: float = 30.0
) -> Optional[models.Drone]:
    """Find the nearest available drone that can handle the order"""
    
    # Get available drones
    available_drones = db.query(models.Drone).filter(
        models.Drone.status == 'idle',
        models.Drone.current_battery >= min_battery,
        models.Drone.max_payload >= order.package_weight
    ).all()
    
    if not available_drones:
        return None
    
    # Find nearest drone
    nearest_drone = None
    min_distance = float('inf')
    
    for drone in available_drones:
        if drone.latitude and drone.longitude:
            distance = haversine_distance(
                drone.latitude, drone.longitude,
                order.pickup_latitude, order.pickup_longitude
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_drone = drone
    
    return nearest_drone


# API Endpoints

@router.post("/assign", response_model=AssignmentResponse, status_code=201)
def assign_drone_to_order(
    request: AssignmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Assign a drone to an order using simple nearest-drone strategy
    """
    try:
        # Get order
        order = db.query(models.Order).filter(
            models.Order.id == uuid.UUID(request.order_id)
        ).first()
        
        if not order:
            raise HTTPException(status_code=404, detail=f"Order {request.order_id} not found")
        
        if order.status != 'pending':
            raise HTTPException(
                status_code=400,
                detail=f"Order {request.order_id} is already {order.status}"
            )
        
        # Find available drone
        drone = find_nearest_available_drone(order, db)
        
        if not drone:
            raise HTTPException(
                status_code=404,
                detail="No available drones found. All drones are busy or low on battery."
            )
        
        # Plan path from drone location to pickup
        path_to_pickup = generate_path(
            drone.latitude, drone.longitude,
            order.pickup_latitude, order.pickup_longitude
        )
        
        # Plan path from pickup to delivery
        path_to_delivery = generate_path(
            order.pickup_latitude, order.pickup_longitude,
            order.delivery_latitude, order.delivery_longitude
        )
        
        # Combine paths
        full_route = path_to_pickup + path_to_delivery[1:]  # Avoid duplicate point
        
        # Calculate total distance
        total_distance = compute_path_distance(full_route)
        
        # Predict battery consumption
        predictor = BatteryPredictor()
        predicted_battery = predictor.predict_simple(
            distance_km=total_distance,
            weight_kg=order.package_weight
        )
        
        # Check if drone has enough battery
        if drone.current_battery < predicted_battery + 20:  # 20% safety margin
            raise HTTPException(
                status_code=400,
                detail=f"Drone {drone.drone_id} doesn't have enough battery. " +
                       f"Needs {predicted_battery + 20}%, has {drone.current_battery}%"
            )
        
        # Estimate duration (assume 30 km/h average speed)
        estimated_duration = (total_distance / 30.0) * 60  # minutes
        
        # Create assignment
        assignment = models.Assignment(
            drone_id=drone.id,
            order_id=order.id,
            route_path=full_route,  # Store as JSON
            total_distance=total_distance,
            estimated_duration=estimated_duration,
            predicted_battery_consumption=predicted_battery,
            status='active'
        )
        
        db.add(assignment)
        
        # Update drone status
        drone.status = 'assigned'
        
        # Update order status
        order.status = 'assigned'
        order.estimated_delivery_time = datetime.utcnow() + timedelta(minutes=estimated_duration)
        
        db.commit()
        db.refresh(assignment)
        
        # Start simulation in background (optional)
        # background_tasks.add_task(simulate_delivery, str(assignment.id), db)
        
        return AssignmentResponse(
            id=str(assignment.id),
            drone_id=str(drone.id),
            order_id=str(order.id),
            status=assignment.status,
            total_distance=total_distance,
            estimated_duration=estimated_duration,
            predicted_battery_consumption=predicted_battery,
            route_path=full_route,
            assigned_at=assignment.assigned_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")


@router.get("/", response_model=List[AssignmentResponse])
def get_assignments(
    status: Optional[str] = None,
    drone_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all assignments with optional filtering
    """
    try:
        query = db.query(models.Assignment)
        
        if status:
            query = query.filter(models.Assignment.status == status)
        
        if drone_id:
            try:
                query = query.filter(models.Assignment.drone_id == uuid.UUID(drone_id))
            except ValueError:
                # Try finding drone by drone_id string
                drone = db.query(models.Drone).filter(models.Drone.drone_id == drone_id).first()
                if drone:
                    query = query.filter(models.Assignment.drone_id == drone.id)
        
        assignments = query.order_by(models.Assignment.assigned_at.desc()).all()
        
        return [
            AssignmentResponse(
                id=str(a.id),
                drone_id=str(a.drone_id),
                order_id=str(a.order_id),
                status=a.status,
                total_distance=a.total_distance,
                estimated_duration=a.estimated_duration,
                predicted_battery_consumption=a.predicted_battery_consumption,
                route_path=a.route_path,
                assigned_at=a.assigned_at
            )
            for a in assignments
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """
    Get a specific assignment by ID
    """
    try:
        assignment = db.query(models.Assignment).filter(
            models.Assignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail=f"Assignment {assignment_id} not found")
        
        return AssignmentResponse(
            id=str(assignment.id),
            drone_id=str(assignment.drone_id),
            order_id=str(assignment.order_id),
            status=assignment.status,
            total_distance=assignment.total_distance,
            estimated_duration=assignment.estimated_duration,
            predicted_battery_consumption=assignment.predicted_battery_consumption,
            route_path=assignment.route_path,
            assigned_at=assignment.assigned_at
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assignment_id}/complete")
def complete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """
    Mark an assignment as completed
    """
    try:
        assignment = db.query(models.Assignment).filter(
            models.Assignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail=f"Assignment {assignment_id} not found")
        
        # Update assignment
        assignment.status = 'completed'
        assignment.completed_at = datetime.utcnow()
        
        # Update order
        order = db.query(models.Order).filter(models.Order.id == assignment.order_id).first()
        if order:
            order.status = 'delivered'
            order.actual_delivery_time = datetime.utcnow()
        
        # Update drone
        drone = db.query(models.Drone).filter(models.Drone.id == assignment.drone_id).first()
        if drone:
            drone.status = 'idle'
            # Reduce battery (use actual or predicted)
            if assignment.actual_battery_used:
                drone.current_battery -= assignment.actual_battery_used
            elif assignment.predicted_battery_consumption:
                drone.current_battery -= assignment.predicted_battery_consumption
            
            drone.current_battery = max(0, drone.current_battery)  # Ensure not negative
        
        db.commit()
        
        return {
            "message": f"Assignment {assignment_id} completed successfully",
            "order_id": str(assignment.order_id),
            "drone_id": str(assignment.drone_id)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{assignment_id}/cancel")
def cancel_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """
    Cancel an active assignment
    """
    try:
        assignment = db.query(models.Assignment).filter(
            models.Assignment.id == uuid.UUID(assignment_id)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail=f"Assignment {assignment_id} not found")
        
        if assignment.status == 'completed':
            raise HTTPException(status_code=400, detail="Cannot cancel completed assignment")
        
        # Update assignment
        assignment.status = 'cancelled'
        
        # Update order
        order = db.query(models.Order).filter(models.Order.id == assignment.order_id).first()
        if order:
            order.status = 'pending'  # Return to pending for reassignment
        
        # Update drone
        drone = db.query(models.Drone).filter(models.Drone.id == assignment.drone_id).first()
        if drone:
            drone.status = 'idle'
        
        db.commit()
        
        return {
            "message": f"Assignment {assignment_id} cancelled",
            "order_id": str(assignment.order_id)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
