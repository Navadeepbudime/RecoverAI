# RecoverAI AI Agent Architecture

RecoverAI implements an **autonomous, policy-governed reasoning agent** designed to select the safest and most effective **Next Best Recovery Action** for each failed payment incident.

```
Incoming Payment Event
         ↓
Customer Context & Recovery Memory (`CustomerRecoveryMemory`)
         ↓
Deterministic Risk Pre-Scoring (`score_recovery`)
         ↓
AI Reasoning Agent (`RecoveryAgent`)
    ├── GeminiRecoveryProvider (when GEMINI_API_KEY is configured)
    └── DemoAIProvider (default, zero keys required)
         ↓
Pydantic Schema Validation (`RecoveryRecommendation`)
         ↓
Deterministic Merchant Policy Guardrails (`PolicyEngine`)
         ↓
Action Executor via Payment Provider (`ActionExecutor`)
         ↓
Append-Only Decision Audit Trail (`AuditLog`)
```

---

## 1. Multi-Signal Decision Context

The agent does not perform a simple error-code lookup. It synthesizes a multi-dimensional context vector:

1. **Payment Incident**: Amount (INR), failure taxonomy, payment method (card, UPI, netbanking), retry attempts.
2. **Customer Behavioral Profile**: Lifetime value, historical payment success rate, past failure frequency.
3. **Customer Recovery Memory**: Ground-truth historical record of which interventions previously succeeded or failed for this customer (e.g. *"Customer has 2 failed card retries; previous UPI payment link succeeded on 2026-08-15"*).
4. **Deterministic Pre-Score**: Factor-weighted recovery probability and risk score.
5. **Merchant Guardrail Limits**: Max retries, escalation threshold, auto-retry toggles.

---

## 2. Pydantic Schema Boundary

The AI agent's output is strictly validated against a Pydantic v2 model:

```python
class RecoveryRecommendation(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    recovery_probability: float = Field(ge=0.0, le=1.0)
    recommended_action: RecoveryAction # One of 6 allowed actions
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    retry_after_minutes: Optional[int]
    reason: str = Field(max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)
    provider_used: str # "gemini", "demo", "gemini-fallback-demo"
```

Any invalid action, missing field, or out-of-bounds probability is rejected before reaching the policy engine.

---

## 3. Allowed Next Best Recovery Actions

- `RETRY_PAYMENT`: Scheduled retry for temporary bank/network timeouts on low-risk transactions.
- `SEND_PAYMENT_LINK`: Send instant link for insufficient funds, expired links, or where retries failed.
- `SEND_REMINDER`: Low-friction WhatsApp/SMS notification for checkout dropouts or auth timeouts.
- `SUGGEST_ALTERNATE_PAYMENT_METHOD`: Direct customer to update card or switch to UPI for expired/blocked cards.
- `ESCALATE_TO_MERCHANT`: Route high-ticket transactions (e.g. > ₹50,000) for human merchant review.
- `STOP_RECOVERY`: Deterministic safety halt on chronic non-payers or max-retry limits.

---

## 4. Dual AI Provider Architecture & Automatic Fallback

- **Default Provider**: `DemoAIProvider`. Requires no API keys, runs locally, and uses memory-aware rule logic.
- **Gemini Provider**: `GeminiRecoveryProvider`. Enabled automatically when `GEMINI_API_KEY` is present in `.env`.
- **Fault Tolerance**: If the Gemini API experiences network timeouts, quota limits, or invalid responses, it **gracefully falls back to DemoAIProvider in < 2ms**, flagging `provider_used="gemini-fallback-demo"`. The application never crashes or stalls.

---

## 5. Non-Bypassable Policy Guardrails

The LLM is strictly advisory. It cannot execute payments. All recommendations must pass through `PolicyEngine.validate()`:

- If `payment.retry_count >= max_automatic_retries` → forced `STOP_RECOVERY`.
- If `customer.failed_payments >= repeated_failure_limit` → forced `STOP_RECOVERY`.
- If `payment.amount_paise >= escalation_threshold_paise` → forced `ESCALATE_TO_MERCHANT`.
- If `amount_paise > high_value_threshold_paise` and action is `RETRY_PAYMENT` → forced `ESCALATE_TO_MERCHANT`.
