from sqlalchemy.orm import Session
from app.db_models.drone import Drone
from app.db_models.assignment import Assignment
from app.db_models.order import Order


def assign_drone(db: Session, order: Order):
    # 1. get available drones  (status must be 'idle', not 'available')
    drones = db.query(Drone).filter(Drone.status == "idle").all()

    if not drones:
        return None

    # 2. simple selection → highest battery  (field is 'current_battery', not 'battery')
    best_drone = max(drones, key=lambda d: d.current_battery)

    # 3. create assignment  (status must be 'active' to match assignments router)
    assignment = Assignment(
        order_id=order.id,
        drone_id=best_drone.id,
        status="active"
    )

    # 4. update drone + order  (drone status 'assigned', not 'busy')
    best_drone.status = "assigned"
    order.status = "assigned"

    db.add(assignment)
    db.commit()

    return assignment