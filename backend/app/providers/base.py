"""Abstract base class for payment providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentEvent:
    """A payment lifecycle event produced by any payment provider."""

    event_type: str          # payment.failed, payment.captured, payment.expired, etc.
    payment_id: str          # Provider-scoped payment identifier
    amount_paise: int        # Amount in paise (INR smallest unit)
    currency: str            # ISO currency code
    customer_email: str
    customer_name: str
    payment_method: str      # card, upi, netbanking, wallet
    failure_reason: Optional[str] = None
    error_code: Optional[str] = None
    provider: str = "demo"   # Which provider produced this event


@dataclass
class PaymentActionResult:
    """Result of executing a recovery action through the payment provider."""

    success: bool
    action: str              # RETRY_PAYMENT, SEND_PAYMENT_LINK, etc.
    new_status: str          # The payment's status after the action
    message: str
    provider: str = "demo"


class PaymentProvider(ABC):
    """Provider-agnostic interface for payment operations.

    All payment providers (demo, Razorpay, Stripe, etc.) implement this
    interface so the core AI/recovery logic never depends on a specific
    payment gateway.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name shown in the UI."""

    @property
    def is_live(self) -> bool:
        """True when the provider connects to a real payment gateway."""
        return False

    @abstractmethod
    def simulate_event(self, scenario: str, **kwargs) -> PaymentEvent:
        """Generate a payment event for a named scenario.

        Used by the seed script and the demo provider to create
        deterministic test data.
        """

    @abstractmethod
    def execute_retry(self, payment_id: str, amount_paise: int,
                      failure_reason: str, recovery_probability: float) -> PaymentActionResult:
        """Attempt to retry a failed payment."""

    @abstractmethod
    def send_payment_link(self, payment_id: str, amount_paise: int,
                          customer_email: str) -> PaymentActionResult:
        """Send a payment link to the customer."""

    @abstractmethod
    def send_reminder(self, payment_id: str,
                      customer_email: str) -> PaymentActionResult:
        """Send a payment reminder notification."""

    @abstractmethod
    def suggest_alternate_method(self, payment_id: str,
                                 customer_email: str) -> PaymentActionResult:
        """Suggest an alternate payment method to the customer."""
