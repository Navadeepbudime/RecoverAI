"""Tests for the payment provider abstraction and DemoPaymentProvider."""

import pytest

from app.providers import DemoPaymentProvider, get_payment_provider
from app.providers.base import PaymentEvent, PaymentActionResult


def test_get_payment_provider_returns_demo_by_default():
    provider = get_payment_provider("demo")
    assert isinstance(provider, DemoPaymentProvider)
    assert provider.name == "Demo Provider"
    assert provider.is_live is False


def test_get_payment_provider_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown payment provider"):
        get_payment_provider("stripe")


def test_demo_simulate_bank_timeout():
    provider = DemoPaymentProvider()
    event = provider.simulate_event("BANK_TIMEOUT", payment_id="pay_test_1", amount_paise=500000)
    assert isinstance(event, PaymentEvent)
    assert event.event_type == "payment.failed"
    assert event.failure_reason == "bank_timeout"
    assert event.provider == "demo"
    assert event.payment_id == "pay_test_1"
    assert event.amount_paise == 500000


def test_demo_simulate_all_scenarios():
    provider = DemoPaymentProvider()
    scenarios = [
        "BANK_TIMEOUT", "NETWORK_ERROR", "INSUFFICIENT_FUNDS", "CARD_EXPIRED",
        "AUTHENTICATION_FAILURE", "CHECKOUT_ABANDONMENT", "REPEATED_FAILURES",
        "PAYMENT_CAPTURED", "PAYMENT_EXPIRED", "PAYMENT_CANCELLED",
    ]
    for scenario in scenarios:
        event = provider.simulate_event(scenario)
        assert isinstance(event, PaymentEvent)
        assert event.provider == "demo"


def test_demo_simulate_unknown_scenario_raises():
    provider = DemoPaymentProvider()
    with pytest.raises(ValueError, match="Unknown demo scenario"):
        provider.simulate_event("ALIEN_ABDUCTION")


def test_demo_retry_succeeds_for_bank_timeout():
    provider = DemoPaymentProvider()
    result = provider.execute_retry("pay_001", 100000, "bank_timeout", 0.75)
    assert isinstance(result, PaymentActionResult)
    assert result.success is True
    assert result.new_status == "captured"
    assert result.provider == "demo"


def test_demo_retry_fails_for_insufficient_funds():
    provider = DemoPaymentProvider()
    result = provider.execute_retry("pay_002", 100000, "insufficient_funds", 0.30)
    assert result.success is False
    assert result.new_status == "failed"


def test_demo_retry_fails_for_low_probability():
    provider = DemoPaymentProvider()
    result = provider.execute_retry("pay_003", 100000, "bank_timeout", 0.30)
    assert result.success is False


def test_demo_send_payment_link():
    provider = DemoPaymentProvider()
    result = provider.send_payment_link("pay_001", 100000, "test@example.com")
    assert result.success is True
    assert result.action == "SEND_PAYMENT_LINK"
    assert "test@example.com" in result.message


def test_demo_send_reminder():
    provider = DemoPaymentProvider()
    result = provider.send_reminder("pay_001", "test@example.com")
    assert result.success is True
    assert result.action == "SEND_REMINDER"


def test_demo_suggest_alternate():
    provider = DemoPaymentProvider()
    result = provider.suggest_alternate_method("pay_001", "test@example.com")
    assert result.success is True
    assert result.action == "SUGGEST_ALTERNATE_PAYMENT_METHOD"
