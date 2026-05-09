-- Complete Database Initialization for Drone Delivery System
-- Run this ONCE after creating the database

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean start)
DROP TABLE IF EXISTS telemetry CASCADE;
DROP TABLE IF EXISTS assignments CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS drones CASCADE;
DROP TABLE IF EXISTS no_fly_zones CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS weather_cache CASCADE;

-- Users table (for authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'customer', -- 'customer', 'admin', 'operator'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drones table
CREATE TABLE drones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drone_id VARCHAR(50) UNIQUE NOT NULL,
    model VARCHAR(100) NOT NULL,
    max_payload FLOAT NOT NULL, -- kg
    max_range FLOAT NOT NULL, -- km
    battery_capacity INTEGER NOT NULL, -- mAh
    current_battery FLOAT DEFAULT 100.0, -- percentage
    status VARCHAR(50) DEFAULT 'idle', -- idle, assigned, in_flight, charging, maintenance, failed
    latitude FLOAT,
    longitude FLOAT,
    altitude FLOAT DEFAULT 0,
    speed FLOAT DEFAULT 0, -- km/h
    last_maintenance TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    
    -- Pickup details
    pickup_latitude FLOAT NOT NULL,
    pickup_longitude FLOAT NOT NULL,
    pickup_address TEXT,
    
    -- Delivery details
    delivery_latitude FLOAT NOT NULL,
    delivery_longitude FLOAT NOT NULL,
    delivery_address TEXT,
    
    -- Package details
    package_weight FLOAT NOT NULL, -- kg
    package_description TEXT,
    
    -- Order metadata
    status VARCHAR(50) DEFAULT 'pending', -- pending, assigned, in_transit, delivered, cancelled, failed
    priority INTEGER DEFAULT 2, -- 1=urgent, 2=normal, 3=low
    estimated_delivery_time TIMESTAMP,
    actual_delivery_time TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_weight CHECK (package_weight > 0 AND package_weight <= 5.0),
    CONSTRAINT check_priority CHECK (priority BETWEEN 1 AND 3)
);

-- Assignments table
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drone_id UUID REFERENCES drones(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Route information (stored as JSON array of [lat, lon] points)
    route_path JSONB, -- [[lat1, lon1], [lat2, lon2], ...]
    
    -- Metrics
    total_distance FLOAT, -- km
    estimated_duration FLOAT, -- minutes
    predicted_battery_consumption FLOAT, -- percentage
    actual_battery_used FLOAT, -- percentage
    
    -- Weather at assignment time
    weather_conditions JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, completed, failed, cancelled
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    UNIQUE(drone_id, order_id)
);

-- Telemetry table (real-time drone tracking)
CREATE TABLE telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drone_id UUID REFERENCES drones(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES assignments(id) ON DELETE CASCADE,
    
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    altitude FLOAT DEFAULT 0,
    
    battery_percentage FLOAT NOT NULL,
    speed FLOAT DEFAULT 0, -- km/h
    heading FLOAT, -- degrees
    
    status VARCHAR(50), -- flying, hovering, landing, etc.
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_battery CHECK (battery_percentage >= 0 AND battery_percentage <= 100)
);

-- No Fly Zones table
CREATE TABLE no_fly_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_name VARCHAR(255) NOT NULL,
    zone_type VARCHAR(100) NOT NULL, -- airport, military, government, hospital, etc.
    zone_category VARCHAR(50) DEFAULT 'permanent', -- permanent, temporary
    
    -- Geometry (polygon boundary)
    boundary GEOMETRY(POLYGON, 4326) NOT NULL,
    
    -- Buffer zone
    buffer_radius_m FLOAT DEFAULT 0,
    
    -- Altitude restriction
    max_altitude_m FLOAT, -- NULL means no-fly at any altitude
    
    -- Location metadata
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    
    -- Active status
    active BOOLEAN DEFAULT TRUE,
    
    -- Validity (for temporary zones)
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    
    -- Metadata
    description TEXT,
    source VARCHAR(100), -- 'official', 'osm', 'manual'
    priority INTEGER DEFAULT 1, -- 1=critical, 2=important, 3=advisory
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather cache table
CREATE TABLE weather_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    
    temperature FLOAT, -- Celsius
    wind_speed FLOAT, -- km/h
    wind_direction FLOAT, -- degrees
    humidity INTEGER, -- percentage
    precipitation FLOAT, -- mm/h
    conditions VARCHAR(100), -- sunny, cloudy, rainy, etc.
    
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    CONSTRAINT check_humidity CHECK (humidity >= 0 AND humidity <= 100)
);

-- Create spatial indexes for performance
CREATE INDEX idx_drones_location ON drones(latitude, longitude);
CREATE INDEX idx_drones_status ON drones(status);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_assignments_drone ON assignments(drone_id);
CREATE INDEX idx_assignments_order ON assignments(order_id);
CREATE INDEX idx_telemetry_drone ON telemetry(drone_id);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp DESC);
CREATE INDEX idx_nfz_boundary ON no_fly_zones USING GIST(boundary);
CREATE INDEX idx_nfz_active ON no_fly_zones(active);
CREATE INDEX idx_weather_location ON weather_cache(latitude, longitude);
CREATE INDEX idx_weather_expires ON weather_cache(expires_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drones_updated_at BEFORE UPDATE ON drones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nfz_updated_at BEFORE UPDATE ON no_fly_zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample drones
INSERT INTO drones (drone_id, model, max_payload, max_range, battery_capacity, current_battery, status, latitude, longitude)
VALUES 
    ('DRONE-001', 'DJI Matrice 300 RTK', 2.7, 15.0, 5935, 100.0, 'idle', 13.0827, 80.2707),
    ('DRONE-002', 'DJI Matrice 300 RTK', 2.7, 15.0, 5935, 100.0, 'idle', 13.0850, 80.2750),
    ('DRONE-003', 'Autel EVO II Pro', 2.0, 12.0, 7100, 100.0, 'idle', 13.0800, 80.2680),
    ('DRONE-004', 'DJI Matrice 300 RTK', 2.7, 15.0, 5935, 95.0, 'idle', 13.0870, 80.2720),
    ('DRONE-005', 'Autel EVO II Pro', 2.0, 12.0, 7100, 88.0, 'idle', 13.0820, 80.2690);

-- Insert sample admin user (password: admin123)
-- Password hash generated with bcrypt
INSERT INTO users (email, password_hash, full_name, role)
VALUES 
    ('admin@dronedeliver.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxKzQCiOy', 'Admin User', 'admin'),
    ('customer@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxKzQCiOy', 'Test Customer', 'customer');

-- Insert sample no-fly zones (Chennai area examples)
INSERT INTO no_fly_zones (zone_name, zone_type, zone_category, boundary, buffer_radius_m, max_altitude_m, city, state, active, source, priority)
VALUES 
    (
        'Chennai International Airport',
        'airport',
        'permanent',
        ST_GeomFromText('POLYGON((80.1500 12.9800, 80.1800 12.9800, 80.1800 13.0100, 80.1500 13.0100, 80.1500 12.9800))', 4326),
        5000,
        NULL,
        'Chennai',
        'Tamil Nadu',
        TRUE,
        'official',
        1
    ),
    (
        'Fort St. George',
        'government',
        'permanent',
        ST_GeomFromText('POLYGON((80.2850 13.0790, 80.2890 13.0790, 80.2890 13.0820, 80.2850 13.0820, 80.2850 13.0790))', 4326),
        500,
        100,
        'Chennai',
        'Tamil Nadu',
        TRUE,
        'manual',
        2
    );

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;

-- Verify installation
SELECT 'Database initialized successfully!' AS status;
SELECT 'PostGIS version: ' || PostGIS_Version() AS postgis_info;
SELECT COUNT(*) AS drone_count FROM drones;
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS nfz_count FROM no_fly_zones;
