import os
import geopandas as gpd
import pandas as pd
import sys

# Add the simulation module to path
simulation_path = "/Users/tejaramidi/Documents/Teja Documents/6th Sem/1.Projects/QuickDeliverySystem-main/real-world-drone-simulation/backend"
if simulation_path not in sys.path:
    sys.path.insert(0, simulation_path)

from services.nfz_builder import build_nfz

DATA_DIR = "/Users/tejaramidi/Documents/Teja Documents/6th Sem/1.Projects/QuickDeliverySystem-main/real-world-drone-simulation/backend/data"
NFZ_FILE = os.path.join(DATA_DIR, "nfz.geojson")

def add_hanamkonda_to_nfz():
    # 1. Build Hanamkonda NFZs to a temp file
    temp_nfz = os.path.join(DATA_DIR, "temp_hanamkonda.geojson")
    print("Building Hanamkonda NFZs from OSM...")
    build_nfz("Hanamkonda, Warangal, Telangana, India", temp_nfz)
    
    # 2. Load existing Hyderabad NFZs (if any)
    existing_nfzs = []
    if os.path.exists(NFZ_FILE):
        try:
            existing_nfzs.append(gpd.read_file(NFZ_FILE))
            print(f"Loaded existing NFZs from {NFZ_FILE}")
        except:
            pass
            
    # 3. Load Hanamkonda NFZs
    if os.path.exists(temp_nfz):
        existing_nfzs.append(gpd.read_file(temp_nfz))
        print(f"Loaded Hanamkonda NFZs")
        os.remove(temp_nfz)
        
    # 4. Merge and save
    if existing_nfzs:
        combined = gpd.GeoDataFrame(
            pd.concat(existing_nfzs, ignore_index=True),
            crs="EPSG:4326"
        )
        # Ensure consistent columns
        if 'severity' not in combined.columns:
            combined['severity'] = 'hard'
        
        combined.to_file(NFZ_FILE, driver="GeoJSON")
        print(f"Successfully merged NFZs. Total: {len(combined)}")
    else:
        print("No NFZs found to merge.")

if __name__ == "__main__":
    add_hanamkonda_to_nfz()
