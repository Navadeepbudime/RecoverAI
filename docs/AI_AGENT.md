# AI Agent

The AI layer recommends actions but does not execute them.

## Recommendation Schema

```json
{
  "risk_score": 82,
  "recovery_probability": 0.76,
  "recommended_action": "RETRY_PAYMENT",
  "priority": "HIGH",
  "retry_after_minutes": 30,
  "reason": "Returning customer with temporary bank timeout.",
  "confidence": 0.87
}
```

Allowed actions:

- `RETRY_PAYMENT`
- `SEND_PAYMENT_LINK`
- `SEND_REMINDER`
- `SUGGEST_ALTERNATE_PAYMENT_METHOD`
- `ESCALATE_TO_MERCHANT`
- `STOP_RECOVERY`

## Validation

`RecoveryRecommendation.from_dict` rejects missing fields, invalid probability ranges, unsupported actions, and invalid priorities. This is the equivalent schema boundary for demo mode. A real Gemini client should return data through the same method before policy validation.

## Guardrail Boundary

Even a valid AI recommendation can be overridden by `PolicyEngine`. The LLM has no code path to call the executor directly.
