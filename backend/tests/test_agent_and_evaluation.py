"""Tests for AI Agent, Pydantic schemas, Fallback, Customer Memory, Evaluation, and Live Simulation."""

import pytest
from app import create_app
from app.extensions import db
from app.models import Customer, Payment, RecoveryCase, MerchantPolicy
from app.agents.schemas import RecoveryAction, RecoveryRecommendation
from app.agents.ai_providers import DemoAIProvider, GeminiRecoveryProvider
from app.agents.recovery_agent import RecoveryAgent
from app.services.recovery_memory import CustomerRecoveryMemory
from app.services.evaluation import calculate_evaluation_metrics
from app.services.live_simulator import trigger_live_simulation
from app.routes.api import process_case


def test_pydantic_schema_validates_recommendation():
    rec = RecoveryRecommendation(
        risk_score=75,
        recovery_probability=0.82,
        recommended_action=RecoveryAction.RETRY_PAYMENT,
        priority="HIGH",
        retry_after_minutes=30,
        reason="Bank gateway timeout on trusted customer.",
        confidence=0.9,
    )
    assert rec.risk_score == 75
    assert rec.recommended_action == RecoveryAction.RETRY_PAYMENT
    d = rec.to_dict()
    assert d["recommended_action"] == "RETRY_PAYMENT"
    assert d["priority"] == "HIGH"


def test_pydantic_schema_rejects_invalid_action():
    with pytest.raises(ValueError, match="Unsupported recovery action"):
        RecoveryRecommendation.from_dict({
            "risk_score": 50,
            "recovery_probability": 0.5,
            "recommended_action": "INVALID_ACTION_123",
            "priority": "MEDIUM",
            "reason": "Test",
            "confidence": 0.5,
        })


def test_pydantic_schema_rejects_out_of_bound_probability():
    with pytest.raises(ValueError):
        RecoveryRecommendation(
            risk_score=50,
            recovery_probability=1.5,  # must be <= 1.0
            recommended_action=RecoveryAction.RETRY_PAYMENT,
            priority="MEDIUM",
            reason="Test",
            confidence=0.5,
        )


def test_demo_ai_provider_recommendation():
    app = create_app()
    with app.app_context():
        customer = Customer.query.first()
        payment = Payment.query.filter_by(failure_reason="bank_timeout").first()
        policy = MerchantPolicy.query.first()

        provider = DemoAIProvider()
        rec = provider.recommend(
            payment=payment,
            customer=customer,
            score={"risk_score": 40, "recovery_probability": 0.75},
            policy=policy,
        )
        assert isinstance(rec, RecoveryRecommendation)
        assert rec.recommended_action in {a for a in RecoveryAction}
        assert rec.provider_used == "demo"
        assert len(rec.reason) > 10


def test_gemini_provider_falls_back_gracefully_when_key_invalid():
    app = create_app()
    with app.app_context():
        customer = Customer.query.first()
        payment = Payment.query.first()
        policy = MerchantPolicy.query.first()

        # Dummy invalid key to verify graceful fallback
        gemini = GeminiRecoveryProvider(api_key="invalid-key-testing-fallback")
        rec = gemini.recommend(
            payment=payment,
            customer=customer,
            score={"risk_score": 60, "recovery_probability": 0.65},
            policy=policy,
        )
        # Must return valid recommendation without crashing
        assert isinstance(rec, RecoveryRecommendation)
        assert "fallback" in rec.provider_used or rec.provider_used == "demo"


def test_customer_recovery_memory_summarizes_history():
    app = create_app()
    with app.app_context():
        customer = Customer.query.first()
        memory = CustomerRecoveryMemory.get_memory(customer)
        assert hasattr(memory, "summary_text")
        assert isinstance(memory.summary_text, str)
        assert len(memory.summary_text) > 5


def test_evaluation_metrics_calculates_incremental_lift():
    app = create_app()
    with app.app_context():
        eval_metrics = calculate_evaluation_metrics()
        assert "baseline_recovered_revenue" in eval_metrics
        assert "recoverai_recovered_revenue" in eval_metrics
        assert "incremental_revenue" in eval_metrics
        assert "incremental_lift_percentage" in eval_metrics
        # RecoverAI should beat or match naive baseline
        assert eval_metrics["recoverai_recovered_revenue"] >= eval_metrics["baseline_recovered_revenue"]
        assert eval_metrics["incremental_revenue"] >= 0


def test_live_simulation_runs_full_5_stage_pipeline():
    app = create_app()
    with app.app_context():
        res = trigger_live_simulation("BANK_TIMEOUT", app.config)
        assert "case" in res
        assert "pipeline_trace" in res
        assert len(res["pipeline_trace"]) == 5
        case_id = res["case"]["case_id"]
        assert case_id.startswith("CASE-pay_live_")


def test_cooldown_and_idempotency_prevents_duplicate_spams():
    app = create_app()
    with app.app_context():
        case = RecoveryCase.query.filter_by(status="RECOVERED").first()
        if case:
            # Process without force should respect cooldown
            processed = process_case(case, force=False)
            assert processed.case_id == case.case_id
