from dataclasses import dataclass
from typing import Optional

from ..domain import RecoveryAction


@dataclass
class RecoveryRecommendation:
    risk_score: int
    recovery_probability: float
    recommended_action: str
    priority: str
    retry_after_minutes: Optional[int]
    reason: str
    confidence: float

    @classmethod
    def from_dict(cls, payload):
        required = {
            "risk_score",
            "recovery_probability",
            "recommended_action",
            "priority",
            "reason",
            "confidence",
        }
        missing = required.difference(payload)
        if missing:
            raise ValueError(f"Missing recommendation fields: {sorted(missing)}")
        action = payload["recommended_action"]
        if action not in {item.value for item in RecoveryAction}:
            raise ValueError(f"Unsupported recovery action: {action}")
        probability = float(payload["recovery_probability"])
        confidence = float(payload["confidence"])
        if not 0 <= probability <= 1:
            raise ValueError("recovery_probability must be between 0 and 1")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        priority = str(payload["priority"]).upper()
        if priority not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            raise ValueError("priority must be LOW, MEDIUM, HIGH, or CRITICAL")
        return cls(
            risk_score=max(0, min(100, int(payload["risk_score"]))),
            recovery_probability=round(probability, 2),
            recommended_action=action,
            priority=priority,
            retry_after_minutes=payload.get("retry_after_minutes"),
            reason=str(payload["reason"])[:1200],
            confidence=round(confidence, 2),
        )

    def to_dict(self):
        return {
            "risk_score": self.risk_score,
            "recovery_probability": self.recovery_probability,
            "recommended_action": self.recommended_action,
            "priority": self.priority,
            "retry_after_minutes": self.retry_after_minutes,
            "reason": self.reason,
            "confidence": self.confidence,
        }


class RecoveryAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def recommend(self, payment, customer, score, policy):
        if self.llm_client:
            raw = self.llm_client.recommend(payment, customer, score, policy)
            return RecoveryRecommendation.from_dict(raw)

        action = self._demo_action(payment, customer, score, policy)
        priority = "HIGH" if score["risk_score"] >= 70 else "MEDIUM"
        if payment.amount_paise >= policy.escalation_threshold_paise:
            priority = "CRITICAL"
        reason = (
            f"Rule-based demo recommendation: {payment.failure_reason} on a "
            f"transaction worth INR {payment.amount_paise / 100:.0f}, "
            f"{customer.successful_payments} prior successes, "
            f"{customer.failed_payments} prior failures, and recovery probability "
            f"{score['recovery_probability']:.0%}."
        )
        return RecoveryRecommendation.from_dict(
            {
                "risk_score": score["risk_score"],
                "recovery_probability": score["recovery_probability"],
                "recommended_action": action,
                "priority": priority,
                "retry_after_minutes": policy.retry_delay_minutes if action == RecoveryAction.RETRY_PAYMENT.value else None,
                "reason": reason,
                "confidence": 0.78,
            }
        )

    def _demo_action(self, payment, customer, score, policy):
        if payment.retry_count >= policy.max_automatic_retries:
            return RecoveryAction.STOP_RECOVERY.value
        if payment.amount_paise >= policy.escalation_threshold_paise:
            return RecoveryAction.ESCALATE_TO_MERCHANT.value
        if payment.failure_reason in {"bank_timeout", "network_error"} and policy.auto_retry_enabled:
            return RecoveryAction.RETRY_PAYMENT.value
        if payment.failure_reason == "card_expired":
            return RecoveryAction.SUGGEST_ALTERNATE_PAYMENT_METHOD.value
        if payment.failure_reason == "insufficient_funds":
            return RecoveryAction.SEND_PAYMENT_LINK.value
        if payment.checkout_abandoned:
            return RecoveryAction.SEND_REMINDER.value
        if score["recovery_probability"] < 0.22 or customer.failed_payments >= policy.repeated_failure_limit:
            return RecoveryAction.STOP_RECOVERY.value
        return RecoveryAction.SEND_REMINDER.value
