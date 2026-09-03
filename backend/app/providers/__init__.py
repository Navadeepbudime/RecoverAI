from .base import PaymentProvider
from .demo import DemoPaymentProvider


def get_payment_provider(provider_name: str = "demo") -> PaymentProvider:
    """Return the payment provider for the configured provider name."""
    providers = {
        "demo": DemoPaymentProvider,
    }
    cls = providers.get(provider_name.lower())
    if cls is None:
        raise ValueError(
            f"Unknown payment provider '{provider_name}'. "
            f"Available: {sorted(providers)}"
        )
    return cls()


__all__ = ["PaymentProvider", "DemoPaymentProvider", "get_payment_provider"]
