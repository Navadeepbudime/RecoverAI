"""Demo payment provider – deterministic simulation, no external API keys.

Every scenario produces the same results on every run, making the demo
reproducible.  The provider simulates the complete payment lifecycle:

    payment.failed  →  recovery action  →  payment.captured / payment.expired

All results are clearly labelled as simulated demo data.
"""

from .base import PaymentActionResult, PaymentEvent, PaymentProvider


# ---------------------------------------------------------------------------
# Deterministic scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "BANK_TIMEOUT": {
        "event_type": "payment.failed",
        "failure_reason": "bank_timeout",
        "error_code": "BANK_TIMEOUT",
        "retry_succeeds": True,
        "recovery_probability_hint": 0.78,
    },
    "NETWORK_ERROR": {
        "event_type": "payment.failed",
        "failure_reason": "network_error",
        "error_code": "GATEWAY_NETWORK_ERROR",
        "retry_succeeds": True,
        "recovery_probability_hint": 0.72,
    },
    "INSUFFICIENT_FUNDS": {
        "event_type": "payment.failed",
        "failure_reason": "insufficient_funds",
        "error_code": "INSUFFICIENT_FUNDS",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.28,
    },
    "CARD_EXPIRED": {
        "event_type": "payment.failed",
        "failure_reason": "card_expired",
        "error_code": "CARD_EXPIRED",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.18,
    },
    "AUTHENTICATION_FAILURE": {
        "event_type": "payment.failed",
        "failure_reason": "authentication_failure",
        "error_code": "AUTHENTICATION_FAILED",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.35,
    },
    "CHECKOUT_ABANDONMENT": {
        "event_type": "payment.failed",
        "failure_reason": "checkout_abandonment",
        "error_code": "CHECKOUT_ABANDONED",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.40,
    },
    "REPEATED_FAILURES": {
        "event_type": "payment.failed",
        "failure_reason": "repeated_failures",
        "error_code": "MULTIPLE_FAILURES",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.10,
    },
    "PAYMENT_CAPTURED": {
        "event_type": "payment.captured",
        "failure_reason": None,
        "error_code": None,
        "retry_succeeds": True,
        "recovery_probability_hint": 1.0,
    },
    "PAYMENT_EXPIRED": {
        "event_type": "payment.expired",
        "failure_reason": "payment_expired",
        "error_code": "PAYMENT_LINK_EXPIRED",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.12,
    },
    "PAYMENT_CANCELLED": {
        "event_type": "payment.cancelled",
        "failure_reason": "customer_cancelled",
        "error_code": "CANCELLED_BY_USER",
        "retry_succeeds": False,
        "recovery_probability_hint": 0.15,
    },
}


class DemoPaymentProvider(PaymentProvider):
    """Fully self-contained demo provider — no API keys required."""

    @property
    def name(self) -> str:
        return "Demo Provider"

    @property
    def is_live(self) -> bool:
        return False

    # ----- event simulation --------------------------------------------------

    def simulate_event(self, scenario: str, **kwargs) -> PaymentEvent:
        scenario_upper = scenario.upper().replace(" ", "_")
        defn = SCENARIOS.get(scenario_upper)
        if defn is None:
            raise ValueError(
                f"Unknown demo scenario '{scenario}'. "
                f"Available: {sorted(SCENARIOS)}"
            )
        return PaymentEvent(
            event_type=defn["event_type"],
            payment_id=kwargs.get("payment_id", f"demo_pay_{scenario_upper.lower()}"),
            amount_paise=kwargs.get("amount_paise", 100000),
            currency=kwargs.get("currency", "INR"),
            customer_email=kwargs.get("customer_email", "demo@example.com"),
            customer_name=kwargs.get("customer_name", "Demo Customer"),
            payment_method=kwargs.get("payment_method", "card"),
            failure_reason=defn["failure_reason"],
            error_code=defn["error_code"],
            provider="demo",
        )

    # ----- recovery actions --------------------------------------------------

    def execute_retry(self, payment_id: str, amount_paise: int,
                      failure_reason: str, recovery_probability: float) -> PaymentActionResult:
        # Deterministic: temporary failures with decent probability succeed
        recoverable = failure_reason in {"bank_timeout", "network_error"}
        if recoverable and recovery_probability >= 0.50:
            return PaymentActionResult(
                success=True,
                action="RETRY_PAYMENT",
                new_status="captured",
                message="[DEMO] Retry succeeded — payment captured.",
                provider="demo",
            )
        return PaymentActionResult(
            success=False,
            action="RETRY_PAYMENT",
            new_status="failed",
            message="[DEMO] Retry attempted — payment still failed.",
            provider="demo",
        )

    def send_payment_link(self, payment_id: str, amount_paise: int,
                          customer_email: str) -> PaymentActionResult:
        return PaymentActionResult(
            success=True,
            action="SEND_PAYMENT_LINK",
            new_status="payment_link_sent",
            message=f"[DEMO] Payment link sent to {customer_email}.",
            provider="demo",
        )

    def send_reminder(self, payment_id: str,
                      customer_email: str) -> PaymentActionResult:
        return PaymentActionResult(
            success=True,
            action="SEND_REMINDER",
            new_status="reminder_sent",
            message=f"[DEMO] Payment reminder sent to {customer_email}.",
            provider="demo",
        )

    def suggest_alternate_method(self, payment_id: str,
                                  customer_email: str) -> PaymentActionResult:
        return PaymentActionResult(
            success=True,
            action="SUGGEST_ALTERNATE_PAYMENT_METHOD",
            new_status="alternate_method_suggested",
            message=f"[DEMO] Alternate payment method suggestion sent to {customer_email}.",
            provider="demo",
        )
