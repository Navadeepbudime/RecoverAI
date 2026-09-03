from datetime import datetime, timezone

from ..extensions import db
from ..domain import CaseStatus, RecoveryAction
from ..providers.base import PaymentProvider


class ActionExecutor:
    """Executes recovery actions through the configured payment provider.

    The executor never talks to a payment gateway directly — it delegates
    to the injected PaymentProvider, keeping the core recovery logic
    provider-agnostic.
    """

    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def execute(self, case, action: str) -> dict:
        payment = case.payment
        customer = payment.customer
        result_tag = "ACTION_RECORDED"
        outcome = "PENDING_CUSTOMER_RESPONSE"

        if action == RecoveryAction.RETRY_PAYMENT.value:
            payment.retry_count += 1
            provider_result = self.provider.execute_retry(
                payment_id=payment.external_id,
                amount_paise=payment.amount_paise,
                failure_reason=payment.failure_reason or "",
                recovery_probability=case.recovery_probability or 0,
            )
            if provider_result.success:
                payment.status = "recovered"
                payment.recovered_at = datetime.now(timezone.utc)
                case.status = CaseStatus.RECOVERED.value
                result_tag = "PAYMENT_RECOVERED"
                outcome = "RECOVERED"
            else:
                outcome = "RETRY_SCHEDULED"

        elif action == RecoveryAction.SEND_PAYMENT_LINK.value:
            self.provider.send_payment_link(
                payment_id=payment.external_id,
                amount_paise=payment.amount_paise,
                customer_email=customer.email,
            )
            outcome = "PAYMENT_LINK_SENT"

        elif action == RecoveryAction.SEND_REMINDER.value:
            self.provider.send_reminder(
                payment_id=payment.external_id,
                customer_email=customer.email,
            )
            outcome = "REMINDER_SENT"

        elif action == RecoveryAction.SUGGEST_ALTERNATE_PAYMENT_METHOD.value:
            self.provider.suggest_alternate_method(
                payment_id=payment.external_id,
                customer_email=customer.email,
            )
            outcome = "ALTERNATE_METHOD_SUGGESTED"

        elif action == RecoveryAction.ESCALATE_TO_MERCHANT.value:
            case.status = CaseStatus.ESCALATED.value
            outcome = "MERCHANT_REVIEW_REQUIRED"

        elif action == RecoveryAction.STOP_RECOVERY.value:
            case.status = CaseStatus.STOPPED.value
            outcome = "STOPPED_BY_POLICY"

        case.executed_action = action
        case.outcome = outcome
        db.session.flush()
        return {
            "result": result_tag,
            "outcome": outcome,
            "provider": self.provider.name,
        }
