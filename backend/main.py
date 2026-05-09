"""
Fixed FastAPI main application with proper CORS configuration
Replace your backend/main.py with this file
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from app.database import get_db, engine, Base
from app import models
from app.routers import orders, drones, assignments, telemetry, admin, auth, address, store

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Drone Delivery System API",
    description="Backend API for Hyperlocal Drone Delivery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CRITICAL FIX: Proper CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8080",
        "*"  # Allow all origins for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(drones.router, prefix="/api/drones", tags=["Drones"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(telemetry.router, prefix="/api/telemetry", tags=["Telemetry"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(address.router, prefix="/api", tags=["Address"])
app.include_router(store.router, prefix="/api", tags=["Store"])


@app.get("/")
def root():
    """Root endpoint - health check"""
    return {
        "message": "Drone Delivery System API v1.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity test"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        drone_count = db.query(models.Drone).count()
        order_count = db.query(models.Order).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "drones_count": drone_count,
            "orders_count": order_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.get("/api/stats")
def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        total_drones = db.query(models.Drone).count()
        # Active = Assigned + In Flight
        active_drones = db.query(models.Drone).filter(
            models.Drone.status.in_(['assigned', 'in_flight'])
        ).count()
        idle_drones = db.query(models.Drone).filter(models.Drone.status == 'idle').count()
        
        total_orders = db.query(models.Order).count()
        pending_orders = db.query(models.Order).filter(models.Order.status == 'PENDING').count()
        completed_orders = db.query(models.Order).filter(models.Order.status == 'DELIVERED').count()
        
        active_assignments = db.query(models.Assignment).filter(
            models.Assignment.status == 'active'
        ).count()
        
        return {
            "drones": {
                "total": total_drones,
                "active": active_drones,
                "idle": idle_drones
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders,
                "completed": completed_orders
            },
            "assignments": {
                "active": active_assignments
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
