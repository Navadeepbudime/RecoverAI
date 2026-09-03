from dataclasses import dataclass

from ..domain import RecoveryAction


@dataclass
class PolicyDecision:
    allowed: bool
    final_action: str
    reason: str

    def to_dict(self):
        return {"allowed": self.allowed, "final_action": self.final_action, "reason": self.reason}


class PolicyEngine:
    def validate(self, payment, customer, recommendation, policy):
        action = recommendation.recommended_action

        if payment.retry_count >= policy.max_automatic_retries:
            return PolicyDecision(False, RecoveryAction.STOP_RECOVERY.value, "Maximum automatic retry count reached.")

        if customer.failed_payments >= policy.repeated_failure_limit:
            return PolicyDecision(False, RecoveryAction.STOP_RECOVERY.value, "Customer has repeated historical failures.")

        if payment.amount_paise >= policy.escalation_threshold_paise:
            return PolicyDecision(False, RecoveryAction.ESCALATE_TO_MERCHANT.value, "Transaction exceeds escalation threshold.")

        if action == RecoveryAction.RETRY_PAYMENT.value:
            if not policy.auto_retry_enabled:
                return PolicyDecision(False, RecoveryAction.SEND_PAYMENT_LINK.value, "Automatic retries are disabled.")
            if payment.amount_paise > policy.high_value_threshold_paise:
                return PolicyDecision(False, RecoveryAction.ESCALATE_TO_MERCHANT.value, "High-value transaction requires merchant review.")

        return PolicyDecision(True, action, "Recommendation complies with configured merchant policy.")
