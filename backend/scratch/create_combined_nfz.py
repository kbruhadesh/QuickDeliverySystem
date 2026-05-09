import geopandas as gpd
from shapely.geometry import Point
import os
import pandas as pd

DATA_DIR = "/Users/tejaramidi/Documents/Teja Documents/6th Sem/1.Projects/QuickDeliverySystem-main/real-world-drone-simulation/backend/data"
NFZ_FILE = os.path.join(DATA_DIR, "nfz.geojson")

def create_combined_nfzs():
    # Hyderabad obstacles
    hyd_nfz = [
        {"name": "Apollo Hospital Jubilee Hills", "lat": 17.425, "lon": 78.411, "radius": 0.003, "type": "hospital"},
        {"name": "KIMS Hospital", "lat": 17.438, "lon": 78.448, "radius": 0.002, "type": "hospital"},
        {"name": "Mindspace Business Park", "lat": 17.442, "lon": 78.385, "radius": 0.004, "type": "military"},
        {"name": "Banjara Hills Hospital", "lat": 17.415, "lon": 78.435, "radius": 0.0025, "type": "hospital"},
    ]

    # Hanamkonda obstacles (near the new store at 18.0125, 79.5539)
    # Pincode 506001 area
    hnk_nfz = [
        {"name": "Rohini Hospital Hanamkonda", "lat": 17.9955, "lon": 79.5465, "radius": 0.002, "type": "hospital"},
        {"name": "Warangal Public Garden", "lat": 18.005, "lon": 79.560, "radius": 0.003, "type": "college"},
        {"name": "KITS Warangal (Restricted)", "lat": 18.030, "lon": 79.540, "radius": 0.004, "type": "college"},
        {"name": "MGM Hospital", "lat": 17.985, "lon": 79.580, "radius": 0.003, "type": "hospital"},
        {"name": "Regional Science Center", "lat": 18.020, "lon": 79.550, "radius": 0.002, "type": "school"},
    ]

    features = []
    for p in (hyd_nfz + hnk_nfz):
        point = Point(p["lon"], p["lat"])
        poly = point.buffer(p["radius"])
        features.append({
            "geometry": poly,
            "name": p["name"],
            "nfz_type": p["type"],
            "severity": "hard"
        })

    gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
    gdf.to_file(NFZ_FILE, driver="GeoJSON")
    print(f"Created {len(gdf)} combined NFZs (Hyderabad + Hanamkonda) at {NFZ_FILE}")

if __name__ == "__main__":
    create_combined_nfzs()
