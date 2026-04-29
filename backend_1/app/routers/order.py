from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate
from app.utils.jwt_handler import decode_access_token
from app.services.assignment_service import assign_drone

router = APIRouter(prefix="/orders", tags=["Orders"])


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

    new_order = Order(
        user_id=user.id,
        total_amount=0,
        status="pending"
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # ➕ ADD ITEMS
    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        item_total = product.price * item.quantity
        total_amount += item_total

        order_item = OrderItem(
            order_id=new_order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price
        )

        db.add(order_item)

    # ✅ UPDATE TOTAL
    new_order.total_amount = total_amount
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


# 📄 GET USER ORDERS
@router.get("/")
def get_orders(token: str, db: Session = Depends(get_db)):
    user = get_current_user(token, db)

    orders = db.query(Order).filter(Order.user_id == user.id).all()

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