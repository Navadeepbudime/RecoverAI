# RecoverAI

RecoverAI is a demo-first Autonomous Revenue Recovery Orchestrator for the Razorpay AI Buildathon. It detects revenue at risk, scores recoverability, asks an AI agent for a structured recommendation, validates that recommendation against deterministic merchant policy, executes only allowed recovery actions, and writes an audit trail for every decision.

## Problem Statement

Merchants lose revenue through failed payments, checkout abandonment, expired cards, authentication issues, insufficient funds, and subscription payment failures. A basic retry system treats these cases the same. RecoverAI decides the safest next recovery action based on payment context, customer history, merchant policy, and explainable scoring.

## Solution

The system follows this flow:

`Payment Event -> Context Collection -> Risk Checks -> AI Recommendation -> Schema Validation -> Policy Validation -> Action Executor -> Outcome -> Audit Log`

The LLM never executes payment actions directly. In demo mode, a deterministic rule-backed agent produces the same structured recommendation shape expected from a real provider.

## Tech Stack

Backend: Python, Flask, SQLAlchemy, PostgreSQL-ready configuration, SQLite demo default.

Frontend: React, Vite, Tailwind CSS, Recharts, lucide-react.

Payments: Provider-agnostic interface with DemoPaymentProvider (default). Razorpay webhook endpoint available when PAYMENT_PROVIDER=razorpay.

AI: Provider abstraction via `RecoveryAgent`; Gemini variables are included but demo mode works without credentials.

## Features

- Dashboard metrics calculated from the database
- Recovery queue and case details
- Transparent recovery scoring
- Structured AI recommendation validation
- Deterministic merchant policy guardrails
- Provider-agnostic payment action executor
- Full audit trail with decision explanations
- Analytics charts (action breakdown, failure distribution)
- Policy editor
- Deterministic recovery simulator
- Razorpay test webhook endpoint (when configured)
- 18 synthetic customers, 35 payments across 10+ scenarios

## Setup

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
python -m pip install -r requirements.txt
python seed.py
python run.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

To start both backend and frontend on Windows:

```powershell
.\start-demo.ps1
```

## Environment Variables

Copy `.env.example` to `.env` and adjust values. By default the backend uses SQLite and demo mode.

### Payment Provider (no API keys needed for demo)

- `PAYMENT_PROVIDER` — `demo` (default) or `razorpay`

### Database

- `DATABASE_URL` — SQLite default: `sqlite:///recoverai_demo.db`. PostgreSQL: `postgresql+psycopg://user:pass@localhost:5432/recoverai`

### AI (optional)

- `GEMINI_API_KEY` — Get a free key at https://aistudio.google.com/apikey
- `GEMINI_MODEL` — Default: `gemini-1.5-flash`

### Razorpay (only when PAYMENT_PROVIDER=razorpay)

- `RAZORPAY_KEY_ID` — Test mode key from Razorpay Dashboard
- `RAZORPAY_KEY_SECRET` — Test mode secret
- `RAZORPAY_WEBHOOK_SECRET` — Webhook signature verification secret

## API Overview

- `GET /api/health`
- `GET /api/metrics`
- `GET /api/analytics`
- `GET /api/cases`
- `GET /api/cases/<case_id>`
- `POST /api/cases/<case_id>/process`
- `GET /api/audit`
- `GET /api/policy`
- `PUT /api/policy`
- `POST /api/simulate`
- `POST /api/webhooks/razorpay`

## Testing

Backend tests:

```bash
cd backend
python -m pytest tests/ -v
```

Frontend build:

```bash
cd frontend
npm run build
```

## Demo Mode

The application works completely without any external API keys. Set `PAYMENT_PROVIDER=demo` (the default) and run `python seed.py` to populate the database with realistic synthetic data covering bank timeouts, insufficient funds, card expiry, network errors, authentication failures, checkout abandonment, and more.

The UI clearly shows **DEMO MODE** in the header.

## Limitations

This is not production-ready. Demo recovery outcomes are deterministic approximations, not a trained ML model. The DemoPaymentProvider simulates payment actions locally. Real payment retries and payment-link creation require merchant-specific Razorpay account configuration and API calls.

## Future Improvements

- Implement a real Gemini client behind `RecoveryAgent`
- Implement `RazorpayProvider` behind the `PaymentProvider` interface
- Add Alembic migrations
- Add merchant authentication and multi-tenant isolation
- Add frontend component tests
- Train a recovery model from actual outcome data
