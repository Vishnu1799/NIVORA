# NIVORA Mobile App

NIVORA is an intelligent grocery delivery application featuring **AUREV AI** — an agentic layer and machine learning system for real-time payment failure recovery.

## 🎨 Design Specification
- **Brand Green**: `#167244` (Nivora Leaf Green)
- **Background**: `#F5F7FA`
- **AUREV Dark Mode**: `#0B1F12` with glowing chip animations
- **Tab Bar**: 5 Tabs (`Home`, `Categories`, `Cart`, `Orders`, `Account`)

---

## 🚀 How to Run

### 1. Start the Bank Simulator (Port 8001)
```bash
cd ..\bank-simulator
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### 2. Start the Backend API (Port 8000)
```bash
cd ..\backend
pip install -r requirements.txt
# Set up your .env file
uvicorn app.main:app --reload --port 8000
```

### 3. Start the Mobile App
```bash
cd ..\mobile
npm install
npx expo start
```
- Press `w` to open in Web browser.
- Or scan the QR code with **Expo Go** on Android / iOS.

> **Testing on a Physical Device:**
> In `lib/api.js`, update `BASE_URL` from `http://localhost:8000` to your computer's local IP address (e.g., `http://192.168.1.X:8000`).

---

## 🤖 Demo Scenarios (AUREV AI)

Open the **Account** tab -> **AUREV AI Dashboard** to switch bank scenarios on the fly:
1. **Normal (UP)**: Instant clean payment success.
2. **Bank Down**: Instant safe decline before charge attempts.
3. **Timeout**: Triggers AUREV AI verification checklist -> safe auto-retry -> recovery.
4. **Unknown**: Triggers AUREV AI verification -> risk escalation -> manual review.
5. **Degraded**: High latency & simulated random intermittent bank failure.
