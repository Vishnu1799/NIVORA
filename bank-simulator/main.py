from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import payments
import health
import admin
from state import bank_state

app = FastAPI(
    title="NIVORA Bank Simulator",
    description="Simulated bank service for NIVORA hackathon demo. Use /admin endpoints to control behavior.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(payments.router)
app.include_router(admin.router)

@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bank Payment Simulator</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: #0F172A; color: #F1F5F9; min-height: 100vh; padding: 24px; display: flex; justify-content: center; }
        .container { max-width: 760px; width: 100%; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .logo { font-size: 20px; font-weight: 800; color: #38BDF8; display: flex; align-items: center; gap: 8px; }
        .status-badge { padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 12px; }
        .badge-up { background: #166534; color: #DCFCE7; }
        .badge-down { background: #991B1B; color: #FEE2E2; }
        .badge-timeout { background: #92400E; color: #FEF3C7; }
        .badge-degraded { background: #6B21A8; color: #F3E8FF; }
        .badge-insufficient_funds { background: #6B21A8; color: #F3E8FF; }
        .badge-invalid_details { background: #6B21A8; color: #F3E8FF; }
        .badge-unknown { background: #0E7490; color: #CFFAFE; }
        
        .card { background: #1E293B; border-radius: 16px; padding: 20px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.08); }
        .section-title { font-size: 13px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; margin: 18px 0 10px 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        @media(max-width: 600px) { .grid { grid-template-columns: 1fr; } }
        
        button.scenario-btn { 
            background: #0F172A; 
            border: 1px solid rgba(255,255,255,0.12); 
            border-radius: 12px; 
            padding: 14px; 
            color: #fff; 
            text-align: left; 
            cursor: pointer; 
            transition: all 0.2s; 
            display: flex; 
            flex-direction: column; 
            gap: 4px; 
            position: relative;
        }
        button.scenario-btn:hover { 
            background: #334155; 
            border-color: #38BDF8; 
            transform: translateY(-1px); 
        }
        button.scenario-btn.active { 
            border-color: #38BDF8 !important; 
            background: rgba(56,189,248,0.14) !important; 
            box-shadow: 0 0 12px rgba(56,189,248,0.25);
        }
        button.scenario-btn.active::after {
            content: '● ACTIVE';
            position: absolute;
            top: 10px;
            right: 12px;
            font-size: 10px;
            font-weight: 800;
            color: #38BDF8;
            background: rgba(56,189,248,0.15);
            padding: 2px 6px;
            border-radius: 4px;
        }
        
        button.scenario-btn span.title { font-weight: 700; font-size: 14px; color: #F8FAFC; }
        button.scenario-btn span.sub { font-weight: 400; font-size: 12px; color: #94A3B8; line-height: 1.3; }
        button.scenario-btn span.result { font-size: 11px; font-weight: 700; color: #4ADE80; margin-top: 4px; }
        button.scenario-btn span.result-halt { font-size: 11px; font-weight: 700; color: #F87171; margin-top: 4px; }
        
        .status-panel { background: #0F172A; border-radius: 10px; padding: 12px 16px; font-size: 12px; color: #38BDF8; display: flex; justify-content: space-between; }
        .toast { position: fixed; bottom: 24px; right: 24px; background: #38BDF8; color: #0F172A; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 13px; display: none; z-index: 1000; }
        .btn-reset { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #fff; padding: 6px 12px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-reset:hover { background: rgba(255,255,255,0.12); border-color: #38BDF8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏦 Bank Payment Simulator</div>
            <div id="liveBadge" class="status-badge badge-up">BANK: ONLINE</div>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h2 style="font-size: 16px; font-weight: 700; color: #F8FAFC;">Choose a Scenario to Test</h2>
                <button class="btn-reset" onclick="resetSimulator()">🔄 Reset to Normal</button>
            </div>
            <p style="font-size: 13px; color: #94A3B8; margin-top: 4px;">
                Click any button below before placing an order to test how the app handles different payment situations:
            </p>

            <!-- Group 1: Automatically Recovered -->
            <div class="section-title">✅ 1. Fixable Issues (Recovered Automatically)</div>
            <div class="grid">
                <button class="scenario-btn" id="btn-timeout" onclick="setScenario('TIMEOUT', 0.0, 'TIMEOUT', 0)">
                    <span class="title">⏱️ Slow Internet / Timeout</span>
                    <span class="sub">Connection dropped before bank replied (No money was cut).</span>
                    <span class="result">➔ Fix: Retries safely and confirms order</span>
                </button>

                <button class="scenario-btn" id="btn-unknown" onclick="setScenario('UNKNOWN', 0.0, 'UNKNOWN', 0)">
                    <span class="title">❓ Money Cut but App Stuck</span>
                    <span class="sub">Bank cut the money, but the app didn't get the receipt in time.</span>
                    <span class="result">➔ Fix: Confirms order without charging twice</span>
                </button>

                <button class="scenario-btn" id="btn-degraded" onclick="setScenario('DEGRADED', 0.7, null, 3000)">
                    <span class="title">🐢 Busy Bank Server (3s Delay)</span>
                    <span class="sub">Bank is slow due to high shopping traffic.</span>
                    <span class="result">➔ Fix: Waits for safe moment and completes</span>
                </button>

                <button class="scenario-btn" id="btn-unstable" onclick="setScenario('UP', 0.35, null, 0)">
                    <span class="title">🎲 Elevator / Train Signal Drop</span>
                    <span class="sub">Simulates random 4G/5G mobile signal loss.</span>
                    <span class="result">➔ Fix: Auto-connects on next try</span>
                </button>
            </div>

            <!-- Group 2: Stopped Safely -->
            <div class="section-title">🛑 2. Permanent Problems (Stops Safely)</div>
            <div class="grid">
                <button class="scenario-btn" id="btn-down" onclick="setScenario('DOWN', 0.0, null, 0)">
                    <span class="title">❌ Bank Server is Down</span>
                    <span class="sub">Bank is completely offline for scheduled maintenance.</span>
                    <span class="result-halt">➔ Stops safely so money is never stuck</span>
                </button>

                <button class="scenario-btn" id="btn-insufficient" onclick="setScenario('INSUFFICIENT_FUNDS', 0.0, 'INSUFFICIENT_FUNDS', 0)">
                    <span class="title">💳 Low Balance</span>
                    <span class="sub">Customer account does not have enough money.</span>
                    <span class="result-halt">➔ Prompts user to choose another account</span>
                </button>

                <button class="scenario-btn" id="btn-invalid" onclick="setScenario('INVALID_DETAILS', 0.0, 'INVALID_DETAILS', 0)">
                    <span class="title">🔑 Wrong UPI PIN or Card Details</span>
                    <span class="sub">Customer entered incorrect security details.</span>
                    <span class="result-halt">➔ Prompts user to type correct PIN</span>
                </button>

                <button class="scenario-btn" id="btn-up" onclick="setScenario('UP', 0.0, null, 0)">
                    <span class="title">🟢 Normal Payment (Instant Success)</span>
                    <span class="sub">Everything works smoothly with no errors.</span>
                    <span class="result" style="color: #38BDF8;">➔ Instant checkout success</span>
                </button>
            </div>
        </div>

        <div class="card">
            <h2 style="font-size: 14px; font-weight: 700; color: #F8FAFC; margin-bottom: 8px;">Current Bank Status</h2>
            <div class="status-panel">
                <span id="stateTelemetry">Status: Online | Active Test: Normal</span>
                <span id="txnCount">Total Payments Tested: 0</span>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Test Scenario Updated!</div>

    <script>
        async function fetchState() {
            try {
                const res = await fetch('/admin/service-state');
                const data = await res.json();
                
                const activeState = data.state || 'UP';
                const force = data.force_outcome;
                const stateDisplay = force || activeState;

                const badge = document.getElementById('liveBadge');
                badge.innerText = `BANK: ${stateDisplay.replace('_', ' ')}`;
                badge.className = `status-badge badge-${stateDisplay.toLowerCase()}`;
                
                document.getElementById('stateTelemetry').innerText = `Status: ${activeState === 'DOWN' ? 'Offline' : 'Online'} | Active Test: ${force || (data.failure_rate > 0 ? (data.response_delay_ms > 0 ? 'Busy Server' : 'Signal Drop') : (activeState === 'UP' ? 'Normal' : activeState))}`;
                document.getElementById('txnCount').innerText = `Total Payments Tested: ${data.transaction_count || 0}`;

                // Dynamically highlight ONLY the active button
                document.querySelectorAll('.scenario-btn').forEach(btn => btn.classList.remove('active'));

                if (force === 'TIMEOUT' || (activeState === 'TIMEOUT' && !force)) {
                    document.getElementById('btn-timeout')?.classList.add('active');
                } else if (force === 'UNKNOWN' || (activeState === 'UNKNOWN' && !force)) {
                    document.getElementById('btn-unknown')?.classList.add('active');
                } else if (activeState === 'DEGRADED' || data.response_delay_ms > 0) {
                    document.getElementById('btn-degraded')?.classList.add('active');
                } else if (data.failure_rate > 0 && activeState === 'UP') {
                    document.getElementById('btn-unstable')?.classList.add('active');
                } else if (activeState === 'DOWN') {
                    document.getElementById('btn-down')?.classList.add('active');
                } else if (activeState === 'INSUFFICIENT_FUNDS' || force === 'INSUFFICIENT_FUNDS') {
                    document.getElementById('btn-insufficient')?.classList.add('active');
                } else if (activeState === 'INVALID_DETAILS' || force === 'INVALID_DETAILS') {
                    document.getElementById('btn-invalid')?.classList.add('active');
                } else if (activeState === 'UP' && !force && data.failure_rate === 0) {
                    document.getElementById('btn-up')?.classList.add('active');
                }
            } catch(e) {}
        }

        async function setScenario(state, failure_rate, force_outcome, response_delay_ms) {
            await fetch('/admin/service-state', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state, failure_rate, force_outcome, response_delay_ms })
            });
            showToast(`Selected: ${force_outcome || state}`);
            fetchState();
        }

        async function resetSimulator() {
            await fetch('/admin/reset', { method: 'POST' });
            showToast("Reset to Normal");
            fetchState();
        }

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => t.style.display = 'none', 2000);
        }

        setInterval(fetchState, 1500);
        fetchState();
    </script>
</body>
</html>"""
