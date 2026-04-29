from sqlalchemy.orm import Session
from app.models.drone import Drone
from app.models.assignment import Assignment
from app.models.order import Order


def assign_drone(db: Session, order: Order):
    # 1. get available drones
    drones = db.query(Drone).filter(Drone.status == "available").all()

    if not drones:
        return None

    # 2. simple selection → highest battery
    best_drone = max(drones, key=lambda d: d.battery)

    # 3. create assignment
    assignment = Assignment(
        order_id=order.id,
        drone_id=best_drone.id,
        status="assigned"
    )

    # 4. update drone + order
    best_drone.status = "busy"
    order.status = "assigned"

    db.add(assignment)
    db.commit()

    return assignment