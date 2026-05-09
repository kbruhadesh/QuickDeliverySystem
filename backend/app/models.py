"""
Complete SQLAlchemy models for Drone Delivery System
Replace your existing models.py with this file
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from geoalchemy2 import Geometry
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    phone = Column(String(20))
    role = Column(String(50), default='customer')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")


class Drone(Base):
    __tablename__ = "drones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drone_id = Column(String(50), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=False)
    max_payload = Column(Float, nullable=False)  # kg
    max_range = Column(Float, nullable=False)  # km
    battery_capacity = Column(Integer, nullable=False)  # mAh
    current_battery = Column(Float, default=100.0)  # percentage
    status = Column(String(50), default='idle', index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float, default=0)
    speed = Column(Float, default=0)
    last_maintenance = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="drone")
    telemetry_data = relationship("Telemetry", back_populates="drone", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    
    # Pickup
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    pickup_address = Column(Text)
    
    # Delivery
    delivery_latitude = Column(Float, nullable=False)
    delivery_longitude = Column(Float, nullable=False)
    delivery_address = Column(Text)
    
    # Package
    package_weight = Column(Float, nullable=False)
    package_description = Column(Text)
    items_summary = Column(Text)  # Summary of items (e.g. "2x Burgers, 1x Coke")
    total_amount = Column(Float, default=0.0)
    
    # Path & Simulation Persistence
    route_path = Column(JSONB)  # Store the RRT* path [[lat, lon], ...]
    eta_minutes = Column(Integer)
    start_time = Column(DateTime) # When the flight simulation actually started
    
    # Status
    status = Column(String(50), default='pending', index=True)
    priority = Column(Integer, default=2)
    estimated_delivery_time = Column(DateTime)
    actual_delivery_time = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('package_weight > 0 AND package_weight <= 5.0', name='check_weight'),
        CheckConstraint('priority BETWEEN 1 AND 3', name='check_priority'),
    )
    
    # Relationships
    user = relationship("User", back_populates="orders")
    assignment = relationship("Assignment", back_populates="order", uselist=False)


class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drone_id = Column(UUID(as_uuid=True), ForeignKey('drones.id', ondelete='CASCADE'), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    
    # Route (stored as JSON array of [lat, lon] points)
    route_path = Column(JSONB)  # [[lat1, lon1], [lat2, lon2], ...]
    
    # Metrics
    total_distance = Column(Float)  # km
    estimated_duration = Column(Float)  # minutes
    predicted_battery_consumption = Column(Float)  # percentage
    actual_battery_used = Column(Float)  # percentage
    
    # Weather
    weather_conditions = Column(JSONB)
    
    # Status
    status = Column(String(50), default='active')
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    drone = relationship("Drone", back_populates="assignments")
    order = relationship("Order", back_populates="assignment")
    telemetry_data = relationship("Telemetry", back_populates="assignment", cascade="all, delete-orphan")


class Telemetry(Base):
    __tablename__ = "telemetry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drone_id = Column(UUID(as_uuid=True), ForeignKey('drones.id', ondelete='CASCADE'), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey('assignments.id', ondelete='CASCADE'))
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, default=0)
    
    battery_percentage = Column(Float, nullable=False)
    speed = Column(Float, default=0)
    heading = Column(Float)
    
    status = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('battery_percentage >= 0 AND battery_percentage <= 100', name='check_battery'),
    )
    
    # Relationships
    drone = relationship("Drone", back_populates="telemetry_data")
    assignment = relationship("Assignment", back_populates="telemetry_data")


class NoFlyZone(Base):
    __tablename__ = "no_fly_zones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_name = Column(String(255), nullable=False)
    zone_type = Column(String(100), nullable=False)
    zone_category = Column(String(50), default='permanent')
    
    # Geometry (PostGIS)
    boundary = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    
    buffer_radius_m = Column(Float, default=0)
    max_altitude_m = Column(Float)
    
    # Location
    city = Column(String(100), index=True)
    state = Column(String(100))
    country = Column(String(100), default='India')
    
    # Status
    active = Column(Boolean, default=True, index=True)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    
    # Metadata
    description = Column(Text)
    source = Column(String(100))
    priority = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WeatherCache(Base):
    __tablename__ = "weather_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    temperature = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    humidity = Column(Integer)
    precipitation = Column(Float)
    conditions = Column(String(100))
    
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('humidity >= 0 AND humidity <= 100', name='check_humidity'),
    )
