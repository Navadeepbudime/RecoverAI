from types import SimpleNamespace

import pytest

from app.agents.recovery_agent import RecoveryRecommendation
from app.policies.engine import PolicyEngine
from app.services.scoring import score_recovery


def payment(**kwargs):
    defaults = {
        "amount_paise": 849900,
        "failure_reason": "bank_timeout",
        "retry_count": 0,
        "checkout_abandoned": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def customer(**kwargs):
    defaults = {"successful_payments": 7, "failed_payments": 1, "previous_recoveries": 1}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def policy(**kwargs):
    defaults = {
        "max_automatic_retries": 2,
        "retry_delay_minutes": 30,
        "high_value_threshold_paise": 2_000_000,
        "escalation_threshold_paise": 5_000_000,
        "repeated_failure_limit": 3,
        "auto_retry_enabled": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_scoring_rewards_temporary_failure_and_good_history():
    result = score_recovery(payment(), customer())
    assert result["recovery_probability"] >= 0.65
    assert result["factors"]["failure_reason"] == "bank_timeout"


def test_policy_blocks_high_value_retry():
    recommendation = RecoveryRecommendation.from_dict(
        {
            "risk_score": 80,
            "recovery_probability": 0.7,
            "recommended_action": "RETRY_PAYMENT",
            "priority": "HIGH",
            "retry_after_minutes": 30,
            "reason": "Temporary failure.",
            "confidence": 0.8,
        }
    )
    decision = PolicyEngine().validate(payment(amount_paise=2_999_900), customer(), recommendation, policy())
    assert decision.allowed is False
    assert decision.final_action == "ESCALATE_TO_MERCHANT"


def test_policy_stops_after_max_retries():
    recommendation = RecoveryRecommendation.from_dict(
        {
            "risk_score": 60,
            "recovery_probability": 0.5,
            "recommended_action": "SEND_REMINDER",
            "priority": "MEDIUM",
            "reason": "Reminder may recover abandoned checkout.",
            "confidence": 0.7,
        }
    )
    decision = PolicyEngine().validate(payment(retry_count=2), customer(), recommendation, policy())
    assert decision.allowed is False
    assert decision.final_action == "STOP_RECOVERY"


def test_invalid_ai_action_is_rejected():
    with pytest.raises(ValueError):
        RecoveryRecommendation.from_dict(
            {
                "risk_score": 50,
                "recovery_probability": 0.5,
                "recommended_action": "WIRE_CUSTOMER_MONEY",
                "priority": "HIGH",
                "reason": "Bad action.",
                "confidence": 0.9,
            }
        )
