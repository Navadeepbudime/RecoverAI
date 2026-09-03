# RecoverAI – Autonomous Revenue Recovery Orchestrator
**Razorpay AI Buildathon Submission — AI Revenue Recovery Track**

RecoverAI is an autonomous, policy-governed revenue recovery orchestrator. It replaces naive, repetitive payment retries with an intelligent **Next Best Recovery Action** pipeline powered by customer recovery memory, multi-dimensional risk scoring, Pydantic-validated AI synthesis, deterministic merchant guardrails, and automated ROI evaluation.

---

## The Core Concept: Next Best Action vs. Dumb Retries

Traditional dunning systems follow a basic loop:
> *"Payment failed → Retry payment → Fail again → Annoy customer → Churn."*

RecoverAI orchestrates the **Next Best Action** tailored to why the revenue is at risk:

```
Payment Failure Event
         ↓
Customer Context & Recovery Memory (`CustomerRecoveryMemory`)
         ↓
Deterministic Risk Pre-Scoring (`score_recovery`)
         ↓
AI Reasoning Agent (`RecoveryAgent` → Gemini / Demo with Fallback)
         ↓
Pydantic Schema Validation (`RecoveryRecommendation`)
         ↓
Deterministic Merchant Policy Guardrails (`PolicyEngine`)
         ↓
Safe Action Execution via Payment Provider (`ActionExecutor`)
         ↓
Immutable Decision Audit Trail (`AuditLog`)
         ↓
Comparative ROI & Incremental Lift Evaluation (`evaluation.py`)
```

---

## Key Features

1. **Dual AI Provider Architecture**:
   - `DemoAIProvider`: Smart, deterministic, memory-aware rule engine (zero API keys needed).
   - `GeminiRecoveryProvider`: Real Google Gemini 1.5 Flash client with structured JSON prompting and **automatic < 2ms fallback** to Demo provider on any network or quota fault.
2. **Customer Recovery Memory**:
   - Grounds AI decisions in historical intervention data (e.g. *"Customer previously failed card retries twice; UPI payment link succeeded on 2026-08-15"*).
3. **Comparative Evaluation & Incremental Lift**:
   - Computes empirical ROI over the identical dataset:
   - **Naive Retry Baseline**: ₹20,554 (11.9% recovery rate).
   - **RecoverAI Orchestrator**: ₹2,20,442 (58.5% recovery rate).
   - **Net Incremental Lift**: **+₹1,99,888 (+972.5%)**.
4. **Live Failure Simulation Bar ("⚡ Simulate Event")**:
   - Interactive UI trigger on the Dashboard allowing judges to trigger live scenarios (`Bank Timeout`, `Insufficient Funds`, `Expired Card`, `Checkout Abandoned`, `High-Value Escalation`) and watch the live 5-stage pipeline progress in real time.
5. **Non-Bypassable Policy Guardrails**:
   - Deterministic checks for max retries, high-value thresholds, repeated failures, and cooldown idempotency. The AI recommends; the policy engine decides.
6. **Recovery Queue with Status Tabs & Search**:
   - Filter by `All`, `Active`, `Recovered`, `Escalated`, `Stopped` with instant customer/case search.
7. **What-If Policy Simulator**:
   - Allows merchants to simulate parameter shifts (e.g. increasing max retries from 2 to 3) against live synthetic data with side-by-side before-and-after comparison.
8. **Provider-Agnostic Payment Abstraction**:
   - Runs 100% locally with `DemoPaymentProvider`. Razorpay webhook endpoint ready for live credentials.

---

## Tech Stack

- **Backend**: Python 3.12+, Flask 3.1, Flask-SQLAlchemy, Pydantic v2, SQLite (PostgreSQL ready).
- **Frontend**: React 18, Vite 7, Tailwind CSS, Recharts, Lucide Icons.
- **Testing**: Pytest (27 automated unit and integration tests).

---

## Quick Start (Demo Mode — Zero API Keys Required)

### 1. Backend Setup
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
python -m pip install -r requirements.txt
python seed.py
python run.py
```

### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

*(On Windows, you can also run `.\start-demo.ps1` from the project root).*

---

## Environment Variables

Copy `.env.example` to `.env`:

```ini
DEMO_MODE=true
SECRET_KEY=recoverai-dev-key
DATABASE_URL=sqlite:///recoverai_demo.db
CORS_ORIGINS=*

# Payment provider (demo by default, zero API keys required)
PAYMENT_PROVIDER=demo

# Optional: Enable real Gemini 1.5 Flash AI reasoning
# Free key available at https://aistudio.google.com/apikey
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# Optional: Razorpay test credentials (only when PAYMENT_PROVIDER=razorpay)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
```

---

## API Reference

| Endpoint | Method | Description |
|---|:---:|---|
| `/api/health` | GET | Health, demo mode, and active AI/payment provider status |
| `/api/metrics` | GET | Aggregated revenue at risk, recovered, and recovery rate |
| `/api/evaluation` | GET | Naive baseline vs. RecoverAI comparative ROI & lift |
| `/api/analytics` | GET | Category breakdowns, action distribution, and failure stats |
| `/api/cases` | GET | List recovery incidents (supports `?status=` and `?search=`) |
| `/api/cases/<case_id>` | GET | Case detail with customer context, AI rationale, and audit trail |
| `/api/cases/<case_id>/process` | POST | Trigger manual agent processing on a case |
| `/api/simulate-live` | POST | Ingest live failure scenario and stream 5-stage pipeline |
| `/api/simulate-live/scenarios`| GET | List available live simulation scenario templates |
| `/api/policy` | GET / PUT | Inspect or update merchant guardrails |
| `/api/simulate` | POST | Run what-if policy simulator against the dataset |
| `/api/audit` | GET | Full decision audit trail with filter support |
| `/api/webhooks/razorpay` | POST | Razorpay webhook receiver with HMAC signature verification |

---

## Automated Test Suite

Run the full pytest suite (27 passing tests):

```powershell
cd backend
.venv\Scripts\activate
pytest tests/ -v
```

Tests cover:
- Pydantic schema validation & invalid action rejection
- Real Gemini provider with automatic fallback
- Customer recovery memory summarization
- Baseline vs. RecoverAI incremental lift calculations
- Live simulation 5-stage pipeline trace
- Policy guardrails, cooldown, and idempotency protection
- Deterministic simulator edge-case handling

---

## Documentation Links

- [Architecture Design](docs/ARCHITECTURE.md)
- [AI Agent & Pydantic Boundary](docs/AI_AGENT.md)
- [Empirical Benchmarks & ROI](docs/BENCHMARKS.md)
- [5-Minute Live Pitch Walkthrough](docs/DEMO.md)
- [Real Development Problems & Solutions Log](PROBLEMS_AND_SOLUTIONS.md)
