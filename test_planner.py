import requests
import json

payload = {
  "drones": [
    {
      "id": "drone_1",
      "max_payload": 5.0,
      "battery_capacity": 100.0,
      "latitude": 17.3850,
      "longitude": 78.4867
    }
  ],
  "orders": [
    {
      "id": "order_1",
      "package_weight": 2.0,
      "pickup_latitude": 17.3850,
      "pickup_longitude": 78.4867,
      "delivery_latitude": 17.4000,
      "delivery_longitude": 78.5000
    }
  ],
  "weather": {
    "wind_speed": 10.0,
    "temperature": 25.0,
    "humidity": 60.0,
    "rain": 0.0
  }
}

print("Triggering optimization task...")
r = requests.post("http://localhost:8000/api/optimize_routes", json=payload)
print(r.status_code, r.text)
