import requests
import json
import os
from typing import List, Dict
import redis

# Redis setup
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL)

class OSMNFZLoader:
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    
    # Define tags and their respective safety buffers in meters
    TAG_CONFIGS = {
        "shop": {
            "values": ["mall", "supermarket", "department_store"],
            "buffer_m": 30
        },
        "building": {
            "values": ["retail", "temple"],
            "buffer_m": 30
        },
        "amenity": {
            "values": ["hospital", "clinic", "doctors", "school", "college", "university", "place_of_worship"],
            "buffer_m": 50
        },
        "healthcare": {
            "values": ["hospital", "clinic", "doctor"],
            "buffer_m": 50
        },
        "landuse": {
            "values": ["military"],
            "buffer_m": 300
        },
        "aeroway": {
            "values": ["aerodrome", "helipad"],
            "buffer_m": 1000
        }
    }

    def __init__(self):
        pass

    def get_cache_key(self, min_lat, min_lon, max_lat, max_lon):
        # Round to 1 decimal place (roughly 11km grid) to maximize cache hits for entire city regions
        grid_id = f"{round(min_lat, 1)}_{round(min_lon, 1)}_{round(max_lat, 1)}_{round(max_lon, 1)}"
        return f"nfz_grid_v2:{grid_id}"

    def get_nfz_features(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[Dict]:
        """
        Fetch NFZ data from OSM within bounding box, returning unbuffered points.
        The path planner will convert to UTM and apply the buffer_m accurately.
        """
        cache_key = self.get_cache_key(min_lat, min_lon, max_lat, max_lon)
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                print(f"✅ Loaded NFZs from Redis cache for grid {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            print(f"⚠️ Redis cache error: {e}")

        print(f"🌐 Fetching NFZs from OSM Overpass for grid {cache_key}...")
        
        # Build Overpass Query
        bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"
        query_parts = []
        for key, config in self.TAG_CONFIGS.items():
            for val in config["values"]:
                query_parts.append(f'node["{key}"="{val}"]({bbox});')
                query_parts.append(f'way["{key}"="{val}"]({bbox});')
                query_parts.append(f'relation["{key}"="{val}"]({bbox});')

        overpass_query = f"""
        [out:json][timeout:25];
        (
          {' '.join(query_parts)}
        );
        out center;
        """
        
        try:
            response = requests.post(
                self.OVERPASS_URL,
                data=overpass_query,
                headers={"User-Agent": "DroneDeliverySystem/1.0"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"❌ Overpass API error: {e}")
            return []

        # Process elements
        nfz_features = []
        for el in data.get('elements', []):
            lat = el.get('lat')
            lon = el.get('lon')
            if lat is None and 'center' in el:
                lat = el['center']['lat']
                lon = el['center']['lon']
            
            if lat is None or lon is None:
                continue
                
            tags = el.get('tags', {})
            name = tags.get('name', 'Unknown')
            
            # Determine buffer
            buffer_m = 100 # default
            for key, config in self.TAG_CONFIGS.items():
                if tags.get(key) in config["values"]:
                    buffer_m = config["buffer_m"]
                    break
                    
            nfz_features.append({
                "type": "Feature",
                "properties": {"name": name, "buffer_m": buffer_m},
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat] # GeoJSON format: lon, lat
                }
            })
            
        try:
            # Cache for 24 hours
            redis_client.setex(cache_key, 86400, json.dumps(nfz_features))
            print(f"✅ Loaded and cached {len(nfz_features)} NFZs from OSM")
        except Exception as e:
            print(f"⚠️ Redis cache set error: {e}")
            
        return nfz_features
