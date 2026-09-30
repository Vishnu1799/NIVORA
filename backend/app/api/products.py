from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.product import Product
from typing import Optional

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_products(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Product).filter(Product.is_available == True)
    if category:
        q = q.filter(Product.category == category)
    products = q.all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "category": p.category,
            "unit": p.unit,
            "image_url": p.image_url,
            "stock": p.stock,
        }
        for p in products
    ]


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(Product.category).distinct().all()
    return [c[0] for c in cats]


@router.get("/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "category": p.category,
        "unit": p.unit,
        "image_url": p.image_url,
        "stock": p.stock,
    }
