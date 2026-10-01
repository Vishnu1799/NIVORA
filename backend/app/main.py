from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.database.init_db import create_tables
    create_tables()
    # Seed products
    from app.database.connection import SessionLocal
    from app.database.init_db import seed_products, seed_demo_users
    db = SessionLocal()
    try:
        seed_products(db)
        seed_demo_users(db)
    finally:
        db.close()
    logging.getLogger(__name__).info("NIVORA Backend started")
    yield
    logging.getLogger(__name__).info("NIVORA Backend shutting down")


app = FastAPI(
    title="NIVORA Payment API",
    description="NIVORA Grocery Platform with AUREV AI Payment Recovery",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, products, orders, payments, merchant, aurev_dashboard, bank_health, ws_payments

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(merchant.router)
app.include_router(aurev_dashboard.router)
app.include_router(bank_health.router)
app.include_router(ws_payments.router)


@app.get("/")
def root():
    return {"app": "NIVORA", "version": "1.0.0", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

flutter_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../flutter_app/build/web"))
if os.path.exists(flutter_web_dir):
    app.mount("/app", StaticFiles(directory=flutter_web_dir, html=True), name="flutter_app")

@app.get("/merchant", response_class=HTMLResponse)
def merchant_direct(request: Request, db = Depends(__import__('app.database.connection', fromlist=['get_db']).get_db)):
    from app.api.merchant import merchant_portal
    return merchant_portal(request, db)


