from app.database.connection import Base, engine
from app.models import user, product, order, payment
from app.models.user import User, UserRole
from app.models.product import Product
from app.core.security import hash_password


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_demo_users(db):
    demo_users = [
        User(email="customer@nivora.com", name="Demo Customer", hashed_password=hash_password("demo123"), role=UserRole.CUSTOMER),
        User(email="merchant@nivora.com", name="Demo Merchant", hashed_password=hash_password("demo123"), role=UserRole.MERCHANT),
    ]
    for u in demo_users:
        if not db.query(User).filter(User.email == u.email).first():
            db.add(u)
    db.commit()


def seed_products(db):
    products = [
        Product(id="1", name="Fresh Apples", description="Fresh organic apples", price=120.0, category="Fruits & Vegetables", unit="1 kg"),
        Product(id="2", name="Organic Milk", description="Fresh full cream milk", price=62.0, category="Dairy & Eggs", unit="1 lt"),
        Product(id="3", name="Brown Bread", description="Freshly baked whole wheat bread", price=45.0, category="Snacks & Breakfast", unit="400g"),
        Product(id="4", name="Banana", description="Fresh ripe bananas", price=40.0, category="Fruits & Vegetables", unit="1 dozen"),
        Product(id="5", name="Tomato", description="Farm fresh tomatoes", price=30.0, category="Fruits & Vegetables", unit="500g"),
        Product(id="6", name="Onion", description="Fresh onions", price=40.0, category="Fruits & Vegetables", unit="1 kg"),
        Product(id="7", name="Potato", description="Fresh potatoes", price=35.0, category="Fruits & Vegetables", unit="1 kg"),
        Product(id="8", name="Chicken Breast", description="Boneless chicken breast", price=280.0, category="Meat & Fish", unit="500g"),
        Product(id="9", name="Cheddar Cheese", description="Mature cheddar cheese", price=220.0, category="Dairy & Eggs", unit="200g"),
        Product(id="10", name="Free Range Eggs", description="Farm fresh eggs", price=96.0, category="Dairy & Eggs", unit="6 pack"),
        Product(id="11", name="Olive Oil", description="Cold pressed olive oil", price=450.0, category="Cooking Essentials", unit="500ml"),
        Product(id="12", name="Spinach", description="Fresh baby spinach leaves", price=35.0, category="Fruits & Vegetables", unit="250g"),
    ]
    for p in products:
        existing = db.query(Product).filter((Product.name == p.name) | (Product.id == p.id)).first()
        if not existing:
            db.add(p)
    db.commit()
