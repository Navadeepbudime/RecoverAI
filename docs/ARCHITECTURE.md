# RecoverAI Architecture

RecoverAI is an Autonomous Revenue Recovery Orchestrator built with a modular Python/Flask backend and a React (Vite + Tailwind) frontend.

---

## 1. Dual Abstraction Architecture

The application is architected around two core abstraction boundaries:

### A. Payment Provider Abstraction
```
PaymentProvider (abstract base)
    ├── DemoPaymentProvider  (default — zero API keys required)
    └── RazorpayProvider     (optional — activated via PAYMENT_PROVIDER=razorpay)
```
- **Demo Mode Default**: The entire payment lifecycle (`payment.failed`, `payment.captured`, `payment.expired`, `payment.retry`) is simulated locally with deterministic repeatability.

### B. AI Reasoning Provider Abstraction
```
RecoveryAgent
    ├── DemoAIProvider          (default — rule-backed, zero API keys required)
    └── GeminiRecoveryProvider  (active when GEMINI_API_KEY is configured)
```
- **Fault Tolerance**: If Gemini encounters network failure or quota exhaustion, it **gracefully falls back** to `DemoAIProvider` in < 2ms, guaranteeing zero presentation downtime.

---

## 2. Core Service Architecture

```
[Payment Event Ingested]
          ↓
[Customer Recovery Memory] (`services/recovery_memory.py`)
          ↓
[Deterministic Scoring Engine] (`services/scoring.py`)
          ↓
[AI Recovery Agent] (`agents/recovery_agent.py`)
          ↓
[Pydantic Schema Validation] (`agents/schemas.py`)
          ↓
[Deterministic Merchant Policy Engine] (`policies/engine.py`)
          ↓
[Action Executor & Provider] (`services/action_executor.py`)
          ↓
[Append-Only Audit Logger] (`services/audit.py`)
          ↓
[Evaluation & ROI Engine] (`services/evaluation.py`)
```

- `services/recovery_memory.py`: Summarizes past customer intervention outcomes into natural language memory.
- `services/scoring.py`: Calculates transparent factor-weighted risk scores and recovery probabilities.
- `policies/engine.py`: Hard merchant guardrails (max retries, repeated failure limits, escalation thresholds) that the AI cannot bypass.
- `services/action_executor.py`: Safe execution of approved actions through the payment provider.
- `services/live_simulator.py`: Ingests on-demand synthetic failure events streaming through the 5-stage pipeline.
- `services/evaluation.py`: Computes comparative **Baseline Naive Retry vs. RecoverAI** revenue and incremental lift.
- `services/simulator.py`: Allows merchants to simulate the financial impact of policy parameter shifts.

---

## 3. Configuration

| Variable | Default | Description |
|---|---|---|
| `PAYMENT_PROVIDER` | `demo` | Payment provider (`demo` or `razorpay`) |
| `DEMO_MODE` | `true` | Display demo mode indicators in UI |
| `DATABASE_URL` | `sqlite:///recoverai_demo.db` | Database connection (SQLite or PostgreSQL) |
| `GEMINI_API_KEY` | (empty) | Optional — enables real Gemini 1.5 Flash AI reasoning |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model identifier |
| `RAZORPAY_KEY_ID` | (empty) | Optional — only needed when `PAYMENT_PROVIDER=razorpay` |
