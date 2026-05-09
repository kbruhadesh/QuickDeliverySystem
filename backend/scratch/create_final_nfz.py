import geopandas as gpd
from shapely.geometry import Point
import os

DATA_DIR = "/Users/tejaramidi/Documents/Teja Documents/6th Sem/1.Projects/QuickDeliverySystem-main/real-world-drone-simulation/backend/data"
NFZ_FILE = os.path.join(DATA_DIR, "nfz.geojson")

def create_robust_combined_nfzs():
    # Hyderabad obstacles
    hyd_nfz = [
        {"name": "Apollo Hospital Jubilee Hills", "lat": 17.4258, "lon": 78.4115, "radius": 0.003, "type": "hospital"},
        {"name": "KIMS Hospital Secunderabad", "lat": 17.4380, "lon": 78.4880, "radius": 0.002, "type": "hospital"},
        {"name": "Care Hospital Banjara Hills", "lat": 17.4120, "lon": 78.4480, "radius": 0.002, "type": "hospital"},
        {"name": "Rainbow Childrens Hospital", "lat": 17.4290, "lon": 78.4410, "radius": 0.0015, "type": "hospital"},
        {"name": "Mindspace Business Park", "lat": 17.4420, "lon": 78.3850, "radius": 0.004, "type": "military"},
        {"name": "Hyderabad Public School", "lat": 17.4360, "lon": 78.4600, "radius": 0.002, "type": "school"},
        {"name": "JNTU Hyderabad (Restricted)", "lat": 17.4930, "lon": 78.3910, "radius": 0.003, "type": "college"},
    ]

    # Hanamkonda obstacles
    hnk_nfz = [
        {"name": "Rohini Hospital Hanamkonda", "lat": 17.9955, "lon": 79.5465, "radius": 0.002, "type": "hospital"},
        {"name": "Warangal Public Garden", "lat": 18.0050, "lon": 79.5600, "radius": 0.003, "type": "college"},
        {"name": "KITS Warangal (Restricted)", "lat": 18.0300, "lon": 79.5400, "radius": 0.004, "type": "college"},
        {"name": "MGM Hospital Warangal", "lat": 17.9850, "lon": 79.5800, "radius": 0.003, "type": "hospital"},
        {"name": "Regional Science Center", "lat": 18.0200, "lon": 79.5500, "radius": 0.002, "type": "school"},
        {"name": "NIT Warangal Campus", "lat": 17.9830, "lon": 79.5310, "radius": 0.005, "type": "college"},
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
    create_robust_combined_nfzs()
