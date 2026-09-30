from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order
from app.models.user import User

router = APIRouter(prefix="/api/merchant", tags=["merchant"])


@router.get("/metrics")
def merchant_metrics(db: Session = Depends(get_db)):
    """Return JSON metrics for merchant dashboard."""
    total_orders = db.query(Order).count()
    successful = db.query(Payment).filter(Payment.status == PaymentStatus.SUCCESS).count()
    recovered = db.query(Payment).filter(
        Payment.status == PaymentStatus.SUCCESS,
        Payment.recovery_attempt_count > 0,
    ).count()
    escalated = db.query(Payment).filter(Payment.status == PaymentStatus.ESCALATED).count()
    declined = db.query(Payment).filter(Payment.status == PaymentStatus.DECLINED).count()
    return {
        "total_orders": total_orders,
        "successful_payments": successful,
        "recovered_by_aurev": recovered,
        "escalated": escalated,
        "declined": declined,
    }


@router.get("/orders")
def merchant_orders(db: Session = Depends(get_db)):
    """List all customer orders with complete product details, quantities, and customer info."""
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    result = []
    for o in orders:
        user_name = o.user.name if o.user else "Customer"
        user_email = o.user.email if o.user else "customer@nivora.com"
        
        # Get latest payment for this order
        latest_payment = None
        if o.payments:
            p = sorted(o.payments, key=lambda x: x.created_at or 0, reverse=True)[0]
            latest_payment = {
                "transaction_id": p.transaction_id,
                "status": p.status.value,
                "amount": p.amount,
                "payment_method": p.payment_method.value if hasattr(p.payment_method, "value") else str(p.payment_method),
                "aurev_action": p.aurev_action,
                "recovered": p.recovery_attempt_count > 0,
            }

        result.append({
            "order_id": str(o.id),
            "status": o.status.value,
            "total_amount": o.total_amount,
            "customer_name": user_name,
            "customer_email": user_email,
            "delivery_address": o.delivery_address,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": [
                {
                    "product_name": i.product_name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total_price": i.total_price,
                }
                for i in o.items
            ],
            "item_count": sum(i.quantity for i in o.items),
            "payment": latest_payment,
        })
    return result


@router.get("/payments")
def merchant_payments(db: Session = Depends(get_db)):
    """List all transactions enriched with ordered product details."""
    payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(50).all()
    result = []
    for p in payments:
        order = p.order
        items = []
        customer_name = "Customer"
        if order:
            customer_name = order.user.name if order.user else "Customer"
            items = [
                {
                    "product_name": i.product_name,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total_price": i.total_price,
                }
                for i in order.items
            ]

        result.append({
            "transaction_id": p.transaction_id,
            "order_id": str(p.order_id) if p.order_id else None,
            "amount": p.amount,
            "payment_method": p.payment_method.value if hasattr(p.payment_method, "value") else str(p.payment_method),
            "status": p.status.value,
            "failure_code": p.failure_code,
            "aurev_action": p.aurev_action,
            "ml_classification": p.ml_classification,
            "customer_name": customer_name,
            "products_ordered": items,
            "item_summary": ", ".join(f"{i['quantity']}x {i['product_name']}" for i in items) if items else "Groceries",
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return result


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/portal", response_class=HTMLResponse)
def merchant_portal(request: Request, db: Session = Depends(get_db)):
    """Visual Merchant Order & Product Dispatch Portal with live customer items manifest."""
    # If explicit json header requested without html
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(merchant_metrics(db))

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIVORA Merchant Order & Product Dispatch Portal</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0B1120;
            --bg-card: #1E293B;
            --bg-card-sub: #0F172A;
            --border-subtle: rgba(255, 255, 255, 0.08);
            --primary: #167244;
            --primary-light: #22C55E;
            --cyan: #38BDF8;
            --amber: #F59E0B;
            --rose: #F43F5E;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; }
        body { background: var(--bg-base); color: #F1F5F9; padding: 24px; min-height: 100vh; display: flex; justify-content: center; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        
        .container { max-width: 1080px; width: 100%; display: flex; flex-direction: column; gap: 20px; }
        
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: var(--bg-card); 
            border-radius: 20px; 
            padding: 18px 24px; 
            border: 1px solid var(--border-subtle);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }
        .brand { display: flex; align-items: center; gap: 14px; }
        .brand-icon { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #167244, #22C55E); display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: 0 0 20px rgba(34, 197, 94, 0.3); }
        
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
        @media(max-width: 780px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
        
        .stat-card { 
            background: var(--bg-card); 
            border-radius: 16px; 
            padding: 16px 20px; 
            border: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .stat-label { font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; }
        .stat-val { font-size: 24px; font-weight: 800; color: #fff; margin-top: 2px; }
        .stat-sub { font-size: 11px; color: #64748B; }
        
        .orders-panel { 
            background: var(--bg-card); 
            border-radius: 20px; 
            padding: 24px; 
            border: 1px solid var(--border-subtle);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }
        .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
        
        .order-card { 
            background: var(--bg-card-sub); 
            border-radius: 16px; 
            padding: 18px 20px; 
            margin-bottom: 14px; 
            border: 1px solid var(--border-subtle); 
            display: flex; 
            flex-direction: column; 
            gap: 12px;
            transition: all 0.2s;
        }
        .order-card:hover {
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }
        
        .order-top { display: flex; justify-content: space-between; align-items: center; }
        .order-id { font-weight: 800; font-size: 15px; color: var(--cyan); }
        
        .status-badge { font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 8px; letter-spacing: 0.04em; }
        .badge-confirmed { background: rgba(34, 197, 94, 0.15); color: #4ADE80; border: 1px solid rgba(34, 197, 94, 0.3); }
        .badge-pending { background: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-escalated { background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); }
        
        .items-box { 
            background: rgba(255,255,255,0.03); 
            border-radius: 12px; 
            padding: 12px 16px; 
            display: flex; 
            flex-direction: column; 
            gap: 8px; 
            border: 1px solid rgba(255, 255, 255, 0.04);
        }
        .item-row { display: flex; justify-content: space-between; font-size: 13.5px; color: #E2E8F0; align-items: center; }
        .item-name { font-weight: 700; display: flex; align-items: center; gap: 8px; }
        .item-qty { background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 6px; color: #94A3B8; font-size: 11px; font-weight: 700; }
        
        .customer-row { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            font-size: 11.5px; 
            color: #94A3B8; 
            border-top: 1px solid rgba(255,255,255,0.06); 
            padding-top: 10px; 
        }

        .recovered-pill {
            background: rgba(56, 189, 248, 0.15);
            color: #38BDF8;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 10px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="brand">
                <div class="brand-icon">🏪</div>
                <div>
                    <h1 style="font-size: 17px; font-weight: 800;">NIVORA Merchant Dispatch & Order Manifest</h1>
                    <p style="font-size: 12px; color: #94A3B8;">Real-Time Incoming Grocery Items & Fulfillments</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="mono" style="font-size: 12px; color: #4ADE80; font-weight: 700;">● STORE ONLINE</div>
            </div>
        </div>

        <!-- Metric Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Customer Orders</div>
                <div class="stat-val mono" id="totalOrders">0</div>
                <div class="stat-sub">Lifetime orders placed</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Confirmed Revenue</div>
                <div class="stat-val mono" id="totalRevenue" style="color: #4ADE80;">₹0</div>
                <div class="stat-sub">Settled to merchant</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">AUREV Auto-Recovered</div>
                <div class="stat-val mono" id="autoRecovered" style="color: #38BDF8;">0</div>
                <div class="stat-sub">Saved from drop-off</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fulfillment SLA</div>
                <div class="stat-val mono" style="color: #FBBF24;">10 Min</div>
                <div class="stat-sub">Express grocery delivery</div>
            </div>
        </div>

        <!-- Orders & Product Manifests -->
        <div class="orders-panel">
            <div class="panel-header">
                <h2 style="font-size: 15px; font-weight: 800; color: #F8FAFC;">📦 Real-Time Incoming Orders & Product Manifests</h2>
                <span class="mono" style="font-size: 11px; color: #94A3B8;" id="livePulse">Live Auto-Sync (1.5s)</span>
            </div>
            <div id="ordersList">
                <div style="text-align: center; color: #64748B; padding: 40px;">Loading customer orders...</div>
            </div>
        </div>
    </div>

    <script>
        async function fetchOrders() {
            try {
                const res = await fetch('/api/merchant/orders');
                const orders = await res.json();
                
                const dRes = await fetch('/api/merchant/metrics');
                const stats = await dRes.json();
                
                document.getElementById('totalOrders').innerText = stats.total_orders || orders.length;
                document.getElementById('autoRecovered').innerText = stats.recovered_by_aurev || 0;

                let revenue = 0;
                orders.forEach(o => {
                    if (o.status === 'CONFIRMED' || o.payment?.status === 'SUCCESS') {
                        revenue += o.total_amount;
                    }
                });
                document.getElementById('totalRevenue').innerText = `₹${Math.round(revenue)}`;

                const container = document.getElementById('ordersList');
                if (!orders || orders.length === 0) {
                    container.innerHTML = '<div style="text-align:center; color:#64748B; padding:30px;">No orders placed yet. Place an order in NIVORA app.</div>';
                    return;
                }

                container.innerHTML = orders.map(o => {
                    const itemsHtml = o.items.map(i => `
                        <div class="item-row">
                            <span class="item-name">
                                🥬 ${i.product_name} 
                                <span class="item-qty mono">${i.quantity} unit${i.quantity > 1 ? 's' : ''}</span>
                            </span>
                            <span class="mono" style="font-weight:700; color:#fff;">₹${i.total_price}</span>
                        </div>
                    `).join('');

                    const isConfirmed = o.status === 'CONFIRMED' || o.payment?.status === 'SUCCESS';
                    const badgeClass = isConfirmed ? 'badge-confirmed' : (o.status === 'ESCALATED' ? 'badge-escalated' : 'badge-pending');
                    const statusText = isConfirmed ? 'CONFIRMED & DISPATCHED' : (o.payment?.status || o.status);

                    const recoveryBadge = o.payment?.recovered ? '<span class="recovered-pill">🛡️ AUREV RECOVERED</span>' : '';

                    return `
                        <div class="order-card">
                            <div class="order-top">
                                <div>
                                    <span class="order-id mono">#ORD-${o.order_id.substring(0, 8).toUpperCase()}</span>
                                    <span style="font-size: 12px; color: #94A3B8; margin-left: 8px; font-weight:600;">👤 ${o.customer_name}</span>
                                    ${recoveryBadge}
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span class="mono" style="font-weight: 800; font-size: 16px; color: #fff;">₹${o.total_amount}</span>
                                    <span class="status-badge ${badgeClass}">${statusText}</span>
                                </div>
                            </div>
                            
                            <div class="items-box">
                                <div style="font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 2px;">
                                    Product Manifest (${o.item_count || o.items.length} items):
                                </div>
                                ${itemsHtml || '<div style="font-size:12px; color:#94A3B8;">General Grocery Items</div>'}
                            </div>

                            <div class="customer-row">
                                <span>📍 Delivery: ${o.delivery_address ? (o.delivery_address.city || 'Bangalore') : 'Saved Customer Address (10 Min Delivery)'}</span>
                                <span class="mono">${o.payment ? (o.payment.payment_method || 'UPI') : 'UPI'}</span>
                            </div>
                        </div>
                    `;
                }).join('');
            } catch (e) {}
        }

        setInterval(fetchOrders, 1500);
        fetchOrders();
    </script>
</body>
</html>"""
