from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int


class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest]
    delivery_address: Optional[dict] = None


class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    status: str
    total_amount: float
    items: List[OrderItemResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
