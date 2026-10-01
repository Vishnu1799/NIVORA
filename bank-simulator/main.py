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
    <title>AUREV AI — Bank Signal Simulator</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
        body { background: #0B1120; color: #F1F5F9; min-height: 100vh; padding: 20px; display: flex; justify-content: center; }
        .container { max-width: 820px; width: 100%; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .logo { font-size: 20px; font-weight: 800; color: #38BDF8; display: flex; align-items: center; gap: 8px; }
        .status-badge { padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 12px; }
        .badge-up { background: #166534; color: #DCFCE7; }
        .badge-down { background: #991B1B; color: #FEE2E2; }
        .badge-timeout { background: #92400E; color: #FEF3C7; }
        .badge-error_signal { background: #DC2626; color: #FEF2F2; }
        .badge-no_response { background: #B45309; color: #FEF3C7; }
        .badge-degraded { background: #6B21A8; color: #F3E8FF; }
        .badge-insufficient_funds { background: #6B21A8; color: #F3E8FF; }
        .badge-invalid_details { background: #6B21A8; color: #F3E8FF; }
        
        .card { background: #1E293B; border-radius: 16px; padding: 20px; margin-bottom: 14px; border: 1px solid rgba(255,255,255,0.08); }
        .section-title { font-size: 12px; font-weight: 800; color: #38BDF8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
        
        /* AUREV Signal Control Buttons */
        .signal-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 8px; }
        @media(max-width: 680px) { .signal-grid { grid-template-columns: 1fr; } }
        
        .signal-btn {
            background: #0F172A;
            border: 2px solid rgba(255,255,255,0.12);
            border-radius: 12px;
            padding: 16px 12px;
            color: #fff;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }
        .signal-btn:hover { transform: translateY(-2px); }
        
        .btn-error { border-color: #EF4444; background: rgba(239,68,68,0.1); }
        .btn-error:hover { background: rgba(239,68,68,0.25); box-shadow: 0 0 14px rgba(239,68,68,0.4); }
        
        .btn-timeout { border-color: #F59E0B; background: rgba(245,158,11,0.1); }
        .btn-timeout:hover { background: rgba(245,158,11,0.25); box-shadow: 0 0 14px rgba(245,158,11,0.4); }
        
        .btn-success { border-color: #10B981; background: rgba(16,185,129,0.15); }
        .btn-success:hover { background: rgba(16,185,129,0.3); box-shadow: 0 0 16px rgba(16,185,129,0.5); }
        
        .signal-btn.active {
            box-shadow: 0 0 16px #38BDF8 !important;
            border-color: #38BDF8 !important;
            background: rgba(56,189,248,0.2) !important;
        }
        
        .signal-title { font-weight: 800; font-size: 13px; letter-spacing: -0.2px; }
        .signal-desc { font-size: 11px; color: #94A3B8; line-height: 1.3; }
        
        /* Secondary Scenarios */
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        @media(max-width: 600px) { .grid { grid-template-columns: 1fr; } }
        
        button.scenario-btn { 
            background: #0F172A; 
            border: 1px solid rgba(255,255,255,0.12); 
            border-radius: 12px; 
            padding: 12px; 
            color: #fff; 
            text-align: left; 
            cursor: pointer; 
            transition: all 0.2s; 
            display: flex; 
            flex-direction: column; 
            gap: 3px; 
        }
        button.scenario-btn:hover { background: #334155; border-color: #38BDF8; }
        button.scenario-btn.active { border-color: #38BDF8 !important; background: rgba(56,189,248,0.14) !important; }
        button.scenario-btn span.title { font-weight: 700; font-size: 13px; color: #F8FAFC; }
        button.scenario-btn span.sub { font-weight: 400; font-size: 11px; color: #94A3B8; }
        
        .guide-box { background: rgba(56,189,248,0.06); border: 1px dashed rgba(56,189,248,0.3); border-radius: 10px; padding: 12px; margin-top: 10px; font-size: 12px; line-height: 1.5; color: #BAE6FD; }
        .status-panel { background: #0F172A; border-radius: 10px; padding: 10px 14px; font-size: 12px; color: #38BDF8; display: flex; justify-content: space-between; }
        .toast { position: fixed; bottom: 20px; right: 20px; background: #38BDF8; color: #0F172A; padding: 10px 16px; border-radius: 8px; font-weight: 800; font-size: 13px; display: none; z-index: 1000; }
        .btn-reset { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #fff; padding: 6px 12px; font-size: 12px; font-weight: 600; cursor: pointer; }
        .btn-reset:hover { background: rgba(255,255,255,0.12); border-color: #38BDF8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">⚡ AUREV AI — Payment Signal Simulator</div>
            <div id="liveBadge" class="status-badge badge-up">SIGNAL: NORMAL</div>
        </div>

        <!-- 1. PRIMARY AUREV AI MIDDLE-STUCK DEMO SIGNALS -->
        <div class="card" style="border: 1px solid rgba(56,189,248,0.3); background: #131E32;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="section-title">🎯 AUREV AI Demo Signal Controls</div>
                <button class="btn-reset" onclick="resetSimulator()">🔄 Reset to Normal</button>
            </div>
            <p style="font-size: 12px; color: #94A3B8; margin-top: 2px;">
                Use these controls to simulate external payment network conditions for live judging:
            </p>

            <div class="signal-grid">
                <button class="signal-btn btn-error" id="sig-error" onclick="sendSignal('ERROR_SIGNAL')">
                    <span class="signal-title" style="color: #F87171;">⚡ TRIGGER ERROR SIGNAL</span>
                    <span class="signal-desc">Simulates connection loss mid-capture. Triggers <b>UNDER_VERIFICATION</b>.</span>
                </button>

                <button class="signal-btn btn-timeout" id="sig-timeout" onclick="sendSignal('TIMEOUT')">
                    <span class="signal-title" style="color: #FBBF24;">⏱️ TRIGGER NO RESPONSE / TIMEOUT</span>
                    <span class="signal-desc">Simulates dropped gateway reply. Triggers <b>UNDER_VERIFICATION</b>.</span>
                </button>

                <button class="signal-btn btn-success" id="sig-success" onclick="sendSignal('INSTANT_SUCCESS')">
                    <span class="signal-title" style="color: #34D399;">🟢 TRIGGER INSTANT SUCCESS</span>
                    <span class="signal-desc">Delivers late success signal to active <b>UNDER_VERIFICATION</b> payment.</span>
                </button>
            </div>

            <div class="guide-box">
                <b>💡 How to Demo Both Paths to Judges:</b><br/>
                • <b>Path A (Recovered):</b> Click <i>[TRIGGER ERROR SIGNAL]</i> ➔ Customer clicks Pay Now (enters <b>Under Verification</b>, Retry disabled) ➔ Click <i>[TRIGGER INSTANT SUCCESS]</i> ➔ AUREV verifies & confirms order!<br/>
                • <b>Path B (Safe Return):</b> Click <i>[TRIGGER ERROR SIGNAL]</i> ➔ Customer clicks Pay Now ➔ Wait 7s without sending success ➔ AUREV audits bank ledger & safely closes with ₹0 debited!
            </div>
        </div>

        <!-- 2. OTHER PERMANENT CONDITIONS -->
        <div class="card">
            <div class="section-title" style="color: #94A3B8;">🛑 Other Bank Conditions</div>
            <div class="grid">
                <button class="scenario-btn" id="btn-down" onclick="setScenario('DOWN', 0.0, null, 0)">
                    <span class="title">❌ Bank Server Down (503)</span>
                    <span class="sub">Immediate decline before money touches customer account.</span>
                </button>

                <button class="scenario-btn" id="btn-insufficient" onclick="setScenario('INSUFFICIENT_FUNDS', 0.0, 'INSUFFICIENT_FUNDS', 0)">
                    <span class="title">💳 Low Balance (Decline 51)</span>
                    <span class="sub">Customer account has insufficient funds. ₹0 debited.</span>
                </button>

                <button class="scenario-btn" id="btn-invalid" onclick="setScenario('INVALID_DETAILS', 0.0, 'INVALID_DETAILS', 0)">
                    <span class="title">🔑 Wrong PIN / Card Details (Decline 55)</span>
                    <span class="sub">Incorrect credentials entered. ₹0 debited.</span>
                </button>

                <button class="scenario-btn" id="btn-up" onclick="setScenario('UP', 0.0, null, 0)">
                    <span class="title">🟢 Normal Operation (Instant Success)</span>
                    <span class="sub">100% smooth normal checkout without errors.</span>
                </button>
            </div>
        </div>

        <div class="card">
            <div class="status-panel">
                <span id="stateTelemetry">Status: Online | Active Signal: None</span>
                <span id="txnCount">Total Payments Processed: 0</span>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Signal Dispatched!</div>

    <script>
        async function fetchState() {
            try {
                const res = await fetch('/admin/service-state');
                const data = await res.json();
                const activeState = data.state || 'UP';
                const force = data.force_outcome;
                const stateDisplay = force || activeState;

                const badge = document.getElementById('liveBadge');
                badge.innerText = `SIGNAL: ${stateDisplay.replace('_', ' ')}`;
                badge.className = `status-badge badge-${stateDisplay.toLowerCase()}`;
                
                document.getElementById('stateTelemetry').innerText = `Status: ${activeState === 'DOWN' ? 'Offline' : 'Online'} | Active Test: ${stateDisplay}`;
                document.getElementById('txnCount').innerText = `Total Payments Processed: ${data.transaction_count || 0}`;

                document.querySelectorAll('.signal-btn, .scenario-btn').forEach(btn => btn.classList.remove('active'));

                if (force === 'ERROR_SIGNAL' || activeState === 'ERROR_SIGNAL') {
                    document.getElementById('sig-error')?.classList.add('active');
                } else if (force === 'TIMEOUT' || activeState === 'TIMEOUT' || activeState === 'NO_RESPONSE') {
                    document.getElementById('sig-timeout')?.classList.add('active');
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

        async function sendSignal(signal) {
            await fetch('/admin/signal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ signal: signal })
            });
            showToast(`Triggered: ${signal}`);
            fetchState();
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
            setTimeout(() => t.style.display = 'none', 2500);
        }

        setInterval(fetchState, 1500);
        fetchState();
    </script>
</body>
</html>"""
