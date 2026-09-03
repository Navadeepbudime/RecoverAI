from app import create_app
from app.services.simulator import simulate_policy


def test_simulate_policy_handles_empty_inputs():
    app = create_app()
    with app.app_context():
        res = simulate_policy({
            "max_automatic_retries": "",
            "retry_delay_minutes": "",
            "high_value_threshold": "",
            "escalation_threshold": "",
            "repeated_failure_limit": "",
        })
        assert "expected_recovery" in res
        assert "current" in res
        assert "simulated" in res
        assert "delta" in res
        assert res["simulated"]["expected_recovery"] >= 0


def test_simulate_policy_strict_guardrails_shifts_delta():
    app = create_app()
    with app.app_context():
        strict_res = simulate_policy({
            "max_automatic_retries": 1,
            "high_value_threshold": 5000,
            "escalation_threshold": 10000,
            "repeated_failure_limit": 3,
        })
        # Strict policy with low thresholds should trigger stops and escalations
        assert strict_res["simulated"]["stopped_cases"] > 0
        assert strict_res["simulated"]["escalated_cases"] > 0
        assert strict_res["delta"]["recovery_diff"] <= 0


def test_simulate_policy_returns_backward_compatible_keys():
    app = create_app()
    with app.app_context():
        res = simulate_policy({})
        assert isinstance(res["expected_recovery"], (int, float))
        assert isinstance(res["stopped_cases"], int)
        assert isinstance(res["escalated_cases"], int)
        assert isinstance(res["recoverable_cases"], int)
