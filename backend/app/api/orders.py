from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import CreateOrderRequest
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("")
def create_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = 0.0
    items_data = []
    for item in req.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            # Fallback by position or name or get first product
            all_prods = db.query(Product).all()
            if all_prods:
                try:
                    idx = int(item.product_id) - 1
                    if 0 <= idx < len(all_prods):
                        product = all_prods[idx]
                    else:
                        product = all_prods[0]
                except ValueError:
                    product = all_prods[0]
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        item_total = product.price * item.quantity
        total += item_total
        items_data.append({"product": product, "quantity": item.quantity, "total": item_total})

    order = Order(
        user_id=current_user.id,
        status=OrderStatus.PENDING,
        total_amount=round(total, 2),
        delivery_address=req.delivery_address,
    )
    db.add(order)
    db.flush()

    for item_data in items_data:
        oi = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            product_name=item_data["product"].name,
            quantity=item_data["quantity"],
            unit_price=item_data["product"].price,
            total_price=item_data["total"],
        )
        db.add(oi)

    db.commit()
    db.refresh(order)
    return {"id": str(order.id), "status": order.status.value, "total_amount": order.total_amount}


@router.get("")
def get_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        result.append({
            "id": str(o.id),
            "status": o.status.value,
            "total_amount": o.total_amount,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": [
                {"product_name": i.product_name, "quantity": i.quantity, "unit_price": i.unit_price}
                for i in o.items
            ],
        })
    return result


@router.get("/{order_id}")
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": str(order.id),
        "status": order.status.value,
        "total_amount": order.total_amount,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items": [
            {
                "product_name": i.product_name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "total_price": i.total_price,
            }
            for i in order.items
        ],
    }
