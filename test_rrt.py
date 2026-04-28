import sys
import time
sys.path.append('.')
from backend.app.services.path_planner import RRTStarPlanner
from backend.app.services.nfz_loader import OSMNFZLoader
from shapely.geometry import Point

loader = OSMNFZLoader()
min_lat, max_lat = 17.35, 17.50
min_lon, max_lon = 78.35, 78.50
nfz_data = loader.get_nfz_features(min_lat, min_lon, max_lat, max_lon)
print(f"Loaded {len(nfz_data)} NFZs")

from shapely.geometry import shape
from pyproj import Proj
utm_proj = Proj(proj='utm', zone=44, ellps='WGS84')
nfzs = []
for f in nfz_data:
    geom = shape(f["geometry"])
    lon, lat = geom.x, geom.y
    x, y = utm_proj(lon, lat)
    buf = f["properties"]["buffer_m"]
    nfzs.append(Point(x, y).buffer(buf))

planner = RRTStarPlanner(step_size=200, max_iter=3000, radius=400)
start = (17.40, 78.45)
goal = (17.385, 78.486)
print(f"Planning from {start} to {goal}")
t0 = time.time()
path = planner.plan_path(start, goal, nfzs)
print(f"Path length: {len(path)}, Time: {time.time()-t0:.2f}s")
