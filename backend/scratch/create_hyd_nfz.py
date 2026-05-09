import geopandas as gpd
from shapely.geometry import Point
import os

# Base directory for the simulation data
DATA_DIR = "/Users/tejaramidi/Documents/Teja Documents/6th Sem/1.Projects/QuickDeliverySystem-main/real-world-drone-simulation/backend/data"
NFZ_FILE = os.path.join(DATA_DIR, "nfz.geojson")

def create_hyderabad_nfzs():
    # Define some obstacle points in Hyderabad (Hospitals, Schools, etc.)
    # These are strategically placed between common store/delivery points
    nfz_points = [
        {"name": "Apollo Hospital Jubilee Hills", "lat": 17.425, "lon": 78.411, "radius": 0.003, "type": "hospital"},
        {"name": "KIMS Hospital", "lat": 17.438, "lon": 78.448, "radius": 0.002, "type": "hospital"},
        {"name": "Mindspace Business Park (Restricted)", "lat": 17.442, "lon": 78.385, "radius": 0.004, "type": "military"},
        {"name": "Hitech City School", "lat": 17.450, "lon": 78.375, "radius": 0.0015, "type": "school"},
        {"name": "Banjara Hills Hospital", "lat": 17.415, "lon": 78.435, "radius": 0.0025, "type": "hospital"},
        {"name": "Public Park Zone", "lat": 17.420, "lon": 78.430, "radius": 0.003, "type": "college"},
        {"name": "Secunderabad Station Area", "lat": 17.433, "lon": 78.501, "radius": 0.005, "type": "aerodrome"},
    ]

    features = []
    for p in nfz_points:
        # Create a circular buffer around the point in degrees (approximate)
        point = Point(p["lon"], p["lat"])
        poly = point.buffer(p["radius"])
        features.append({
            "geometry": poly,
            "name": p["name"],
            "nfz_type": p["type"]
        })

    gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
    
    # Save to file
    os.makedirs(DATA_DIR, exist_ok=True)
    gdf.to_file(NFZ_FILE, driver="GeoJSON")
    print(f"Created {len(gdf)} NFZs in Hyderabad at {NFZ_FILE}")

if __name__ == "__main__":
    create_hyderabad_nfzs()
