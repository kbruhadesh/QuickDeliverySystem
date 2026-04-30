from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import json
from app.database import get_db
from app.db_models.user import User
from app.db_models.order import Order
from app.db_models.order_item import OrderItem
from app.db_models.product import Product
from app.schemas.order import OrderCreate
from app.utils.jwt_handler import decode_access_token
from app.services.assignment_service import assign_drone
from app.services.path_planner import RRTStarPlanner
from app.services.battery_predictor import BatteryPredictor
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["Orders"])

class RouteCalcRequest(BaseModel):
    pickup_latitude: float
    pickup_longitude: float
    delivery_latitude: float
    delivery_longitude: float
    weight_kg: float = 1.0


# 🔐 HELPER FUNCTION
def get_current_user(token: str, db: Session):
    payload = decode_access_token(token)
    email = payload.get("sub")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ➕ CREATE ORDER
@router.post("/")
def create_order(order_data: OrderCreate, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)

    total_amount = 0
    order_items = []

    # 1. VALIDATE PRODUCTS FIRST BEFORE DB COMMIT
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        item_total = product.price * item.quantity
        total_amount += item_total
        
        # We temporarily hold these to insert after creating the order
        order_items.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price
        })

    # 2. CREATE ORDER NOW THAT VALIDATION PASSED
    new_order = Order(
        user_id=user.id,
        total_amount=total_amount,
        status="pending",
        pickup_latitude=order_data.pickup_latitude,
        pickup_longitude=order_data.pickup_longitude,
        delivery_latitude=order_data.delivery_latitude,
        delivery_longitude=order_data.delivery_longitude
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 3. ADD ITEMS
    for oi in order_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=oi["product_id"],
            quantity=oi["quantity"],
            price=oi["price"]
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)

    # 🚀 ASSIGN DRONE
    assignment = assign_drone(db, new_order)

    if assignment:
        message = "Order created and drone assigned"
    else:
        message = "Order created but no drone available"

    return {
        "message": message,
        "order_id": new_order.id,
        "total_amount": total_amount
    }

@router.post("/calculate_eta")
def calculate_eta(req: RouteCalcRequest):
    # 1. Plan the route using RRT*
    planner = RRTStarPlanner(step_size=200, max_iter=8000, radius=400)
    start = (req.pickup_latitude, req.pickup_longitude)
    goal = (req.delivery_latitude, req.delivery_longitude)
    
    path = planner.plan_path(start, goal)
    
    # Calculate distance based on path
    import math
    def haversine(p1, p2):
        lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
        lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c
        
    distance_km = 0
    if len(path) > 1:
        for i in range(len(path)-1):
            distance_km += haversine(path[i], path[i+1])
    else:
        distance_km = haversine(start, goal)
        
    # Assume 40 km/h drone speed
    eta_min = int((distance_km / 40) * 60)
    
    # Predict battery drop
    predictor = BatteryPredictor()
    
    # Fetch live weather data from Open-Meteo API
    weather_data = {"wind_speed": 10.0, "temperature": 25.0, "humidity": 60.0, "rain": 0.0}
    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={req.pickup_latitude}&longitude={req.pickup_longitude}&current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m"
        response = requests.get(weather_url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("current", {})
            weather_data = {
                "wind_speed": float(data.get("wind_speed_10m", 10.0)),
                "temperature": float(data.get("temperature_2m", 25.0)),
                "humidity": float(data.get("relative_humidity_2m", 60.0)),
                "rain": float(data.get("rain", 0.0))
            }
    except Exception as e:
        print(f"Weather API fetch failed: {e}")

    battery_drop = predictor.predict(
        distance_km=distance_km,
        weight_kg=req.weight_kg,
        weather=weather_data
    )
    
    return {
        "eta_min": max(1, eta_min),
        "distance_km": round(distance_km, 2),
        "battery_drop": round(battery_drop, 2),
        "path": path
    }


# 📄 GET USER ORDERS
@router.get("/")
def get_orders(token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    orders = db.query(Order).filter(Order.user_id == user.id).all()
    return orders

# 👮 GET ALL ORDERS (ADMIN)
@router.get("/all")
def get_all_orders(token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)
    # In a real app we'd check user.role == 'ADMIN'
    orders = db.query(Order).all()
    return orders


# ❌ CANCEL ORDER
@router.delete("/{order_id}")
def cancel_order(order_id: int, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = "cancelled"
    db.commit()

    return {"message": "Order cancelled"}
