# Demo

Demo mode lets RecoverAI run **without any external API keys** — no Razorpay, no Gemini credentials needed.

## How It Works

The application uses a **provider-agnostic payment interface**:

```
PAYMENT_PROVIDER=demo  (default)
```

The `DemoPaymentProvider` simulates the entire payment lifecycle:

| Event | Description |
|---|---|
| `payment.failed` | Bank timeout, insufficient funds, card expired, etc. |
| `payment.captured` | Payment successfully recovered |
| `payment.expired` | Payment link timed out |
| `payment.cancelled` | Customer cancelled the payment |
| `payment.retry` | Retry attempt with deterministic outcome |

## Seed Data

Run:

```bash
cd backend
python seed.py
```

The seed creates **18 customers** and **35 payments** covering:

- Bank timeout (temporary, recoverable)
- Network error (temporary, recoverable)
- Insufficient funds
- Card expired
- Authentication failure
- Checkout abandonment
- Repeated failures (chronic issue)
- Payment expired
- Customer cancelled
- Successful recovery (already recovered)
- High-value transactions (triggers escalation)
- Low-value easy recovery

## Demo Behavior

The demo agent is **deterministic**. It uses the same structured recommendation schema and policy guardrails that a real LLM-backed agent or Razorpay-integrated system would use.

All demo actions are clearly labelled with `[DEMO]` prefixes in their results.

The UI shows **DEMO MODE** in the header when using the demo provider.

## Suggested Walkthrough

1. Open **Dashboard** and review at-risk revenue (₹2.84L at risk, ₹54K recovered).
2. Open **Recovery Queue** and scan the 31 cases across all scenarios.
3. Click a case to see the full timeline: `CONTEXT_ANALYZED → AI_DECISION → POLICY_CHECK → ACTION_EXECUTED`.
4. Open **Recovery Policy** and edit guardrails (e.g., change max retries to 3).
5. Open **Simulator** and compare expected recovery under different policies.
6. Open **Audit Trail** to verify the chain of decisions and explanations.
7. Open **Analytics** to see action and failure type distributions.

## Transitioning to Live Mode

To switch from demo to Razorpay:

1. Set `PAYMENT_PROVIDER=razorpay` in `.env`.
2. Provide `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and optionally `RAZORPAY_WEBHOOK_SECRET`.
3. The core AI/recovery logic remains unchanged — only the payment execution layer changes.
