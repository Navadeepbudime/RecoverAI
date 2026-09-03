"""Customer Recovery Memory Service.

Builds explainable, historical recovery memory for customers based entirely on
actual database records (past payments, recovery cases, and executed actions).
Used as contextual memory by the AI Recovery Agent.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CustomerMemorySummary:
    total_interventions: int
    successful_interventions: int
    failed_interventions: int
    history: List[Dict[str, Any]]
    summary_text: str
    recommended_bias: Optional[str] = None


class CustomerRecoveryMemory:
    """Extracts ground-truth recovery history for a customer from the database."""

    @staticmethod
    def get_memory(customer, current_payment_id: Optional[int] = None) -> CustomerMemorySummary:
        if not customer:
            return CustomerMemorySummary(
                total_interventions=0,
                successful_interventions=0,
                failed_interventions=0,
                history=[],
                summary_text="No customer profile available.",
            )

        history: List[Dict[str, Any]] = []
        action_success: Dict[str, int] = {}
        action_failure: Dict[str, int] = {}

        # Look at past payments for this customer (excluding current payment if given)
        for payment in getattr(customer, "payments", []):
            if current_payment_id and payment.id == current_payment_id:
                continue

            case = getattr(payment, "case", None)
            if not case:
                continue

            action = case.executed_action or case.recommended_action
            if not action:
                continue

            is_success = case.status == "RECOVERED" or payment.status == "recovered"
            is_failure = case.status in {"STOPPED", "FAILED"} or (payment.retry_count > 1 and not is_success)

            record = {
                "payment_id": payment.external_id,
                "amount": payment.amount_paise / 100,
                "failure_reason": payment.failure_reason,
                "action": action,
                "outcome": case.outcome or ("RECOVERED" if is_success else "FAILED"),
                "is_success": is_success,
                "timestamp": case.updated_at.isoformat() if case.updated_at else None,
            }
            history.append(record)

            if is_success:
                action_success[action] = action_success.get(action, 0) + 1
            else:
                action_failure[action] = action_failure.get(action, 0) + 1

        total_int = len(history)
        succ_int = sum(action_success.values())
        fail_int = sum(action_failure.values())

        # Construct explainable natural language summary for the AI prompt
        if total_int == 0:
            if customer.successful_payments > 0 and customer.failed_payments == 0:
                summary_text = (
                    f"Customer has {customer.successful_payments} prior successful payments and no prior failures. "
                    "First-time payment recovery incident."
                )
            else:
                summary_text = (
                    f"Customer record shows {customer.successful_payments} successes, "
                    f"{customer.failed_payments} past failures, and {customer.previous_recoveries} prior recoveries."
                )
            recommended_bias = None
        else:
            snippets = []
            for act, count in action_success.items():
                snippets.append(f"{act} succeeded {count} time(s)")
            for act, count in action_failure.items():
                snippets.append(f"{act} failed {count} time(s)")

            details = "; ".join(snippets) if snippets else "actions pending resolution"
            summary_text = (
                f"Historical recovery memory across {total_int} past intervention(s): {details}."
            )

            # Determine algorithmic bias to assist the AI
            if action_failure.get("RETRY_PAYMENT", 0) >= 2 and action_success.get("SEND_PAYMENT_LINK", 0) > 0:
                recommended_bias = "PREFER_PAYMENT_LINK"
            elif action_failure.get("RETRY_PAYMENT", 0) >= 2 and action_success.get("SUGGEST_ALTERNATE_PAYMENT_METHOD", 0) > 0:
                recommended_bias = "PREFER_ALTERNATE_METHOD"
            elif customer.failed_payments >= 4:
                recommended_bias = "HIGH_CHURN_RISK"
            else:
                recommended_bias = None

        return CustomerMemorySummary(
            total_interventions=total_int,
            successful_interventions=succ_int,
            failed_interventions=fail_int,
            history=history,
            summary_text=summary_text,
            recommended_bias=recommended_bias,
        )
