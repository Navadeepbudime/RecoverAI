# Architecture

RecoverAI is split into a Flask backend and a React frontend.

## Payment Provider Abstraction

The application is designed around a **provider-agnostic payment interface**:

```
PaymentProvider (abstract base)
    ├── DemoPaymentProvider  (default — no API keys)
    └── RazorpayProvider     (future — requires credentials)
```

The default provider is `demo`, configured via `PAYMENT_PROVIDER=demo`.

The DemoPaymentProvider simulates the entire payment lifecycle:
- `payment.failed` (bank timeout, insufficient funds, card expired, etc.)
- `payment.captured` (successful recovery)
- `payment.expired` (payment link expired)
- `payment.cancelled` (customer cancelled)
- `payment.retry` (retry attempt result)

**No external API keys are required to run the application.**

## Backend

- `providers/`: Payment provider abstraction and implementations.
- `models/`: SQLAlchemy entities for customers, payments, recovery cases, merchant policy, and audit logs.
- `services/scoring.py`: Transparent rule-based scoring system.
- `agents/recovery_agent.py`: AI recommendation boundary and structured validation.
- `policies/engine.py`: Deterministic guardrails.
- `services/action_executor.py`: Executes allowed actions through the configured payment provider.
- `routes/api.py`: REST API. Razorpay webhook only processes when `PAYMENT_PROVIDER=razorpay`.

## Data Flow

1. A payment failure or abandonment is stored as a `Payment`.
2. A `RecoveryCase` is created.
3. Scoring evaluates recoverability from customer and transaction context.
4. The AI agent emits structured JSON-compatible data.
5. Policy validation may allow, override, stop, or escalate the recommendation.
6. The executor delegates the action to the configured `PaymentProvider`.
7. Audit entries explain every significant step.

## Demo Persistence

SQLite is the default so the app can run without PostgreSQL. The same SQLAlchemy models work with PostgreSQL by setting `DATABASE_URL`.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `PAYMENT_PROVIDER` | `demo` | Payment provider to use |
| `DEMO_MODE` | `true` | Enable demo mode indicators |
| `DATABASE_URL` | `sqlite:///recoverai_demo.db` | Database connection |
| `GEMINI_API_KEY` | (empty) | Optional — AI agent uses rules without it |
| `RAZORPAY_KEY_ID` | (empty) | Only needed when `PAYMENT_PROVIDER=razorpay` |
