from ..models import MerchantPolicy, Payment, RecoveryCase, CaseStatus
from ..services.scoring import score_recovery


def _safe_int(val, default):
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _safe_float(val, default):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _evaluate_policy_rules(payments, max_retries, retry_delay, high_value_paise, escalation_paise, repeated_limit, auto_retry):
    """Deterministic evaluation of recovery outcomes under a given set of policy parameters."""
    expected_recovery_paise = 0
    stopped = 0
    escalated = 0
    recoverable = 0

    for payment in payments:
        customer = payment.customer
        score = score_recovery(payment, customer)
        prob = score["recovery_probability"]

        # Stopping rules
        if payment.retry_count >= max_retries:
            stopped += 1
            continue

        if customer.failed_payments >= repeated_limit:
            stopped += 1
            continue

        # Escalation rules
        if payment.amount_paise >= escalation_paise:
            escalated += 1
            continue

        effective_prob = prob

        # Auto-retry disabled check
        if not auto_retry and payment.failure_reason in {"bank_timeout", "network_error"}:
            effective_prob *= 0.6

        # Retry delay sensitivity: bank/network timeouts resolve best between 15-45 mins
        if payment.failure_reason in {"bank_timeout", "network_error"}:
            if retry_delay < 10:
                effective_prob *= 0.88  # outage still ongoing
            elif retry_delay > 90:
                effective_prob *= 0.90  # delayed retry, customer churn

        # High-value transactions below escalation threshold require merchant review
        if payment.amount_paise > high_value_paise:
            effective_prob *= 0.75

        expected_recovery_paise += payment.amount_paise * effective_prob
        recoverable += 1

    return {
        "expected_recovery": round(expected_recovery_paise / 100, 2),
        "stopped_cases": stopped,
        "escalated_cases": escalated,
        "recoverable_cases": recoverable,
    }


def simulate_policy(policy_payload=None):
    """Run a deterministic what-if policy simulation over all at-risk payments.

    Provides both:
    1. Flat root-level fields for direct compatibility (expected_recovery, stopped_cases, escalated_cases)
    2. Side-by-side 'current' vs 'simulated' comparison and 'delta' calculation.
    """
    if policy_payload is None:
        policy_payload = {}

    # 1. Load active merchant policy from DB for baseline comparison
    current_policy = MerchantPolicy.query.filter_by(merchant_id="demo_merchant").first()
    curr_max_retries = current_policy.max_automatic_retries if current_policy else 2
    curr_retry_delay = current_policy.retry_delay_minutes if current_policy else 30
    curr_high_val = current_policy.high_value_threshold_paise if current_policy else 2_000_000
    curr_escalation = current_policy.escalation_threshold_paise if current_policy else 5_000_000
    curr_repeated_limit = current_policy.repeated_failure_limit if current_policy else 3
    curr_auto_retry = current_policy.auto_retry_enabled if current_policy else True

    # 2. Parse simulated policy parameters with safe fallbacks
    sim_max_retries = max(0, _safe_int(policy_payload.get("max_automatic_retries"), curr_max_retries))
    sim_retry_delay = max(1, _safe_int(policy_payload.get("retry_delay_minutes"), curr_retry_delay))
    sim_high_val = max(0, int(_safe_float(policy_payload.get("high_value_threshold"), curr_high_val / 100) * 100))
    sim_escalation = max(0, int(_safe_float(policy_payload.get("escalation_threshold"), curr_escalation / 100) * 100))
    sim_repeated_limit = max(1, _safe_int(policy_payload.get("repeated_failure_limit"), curr_repeated_limit))
    sim_auto_retry = bool(policy_payload.get("auto_retry_enabled", curr_auto_retry))

    # 3. Load all failed/abandoned payments
    at_risk_payments = Payment.query.filter(
        Payment.status.in_(["failed", "checkout_abandoned"])
    ).all()

    # 4. Evaluate baseline vs simulated
    baseline = _evaluate_policy_rules(
        at_risk_payments,
        max_retries=curr_max_retries,
        retry_delay=curr_retry_delay,
        high_value_paise=curr_high_val,
        escalation_paise=curr_escalation,
        repeated_limit=curr_repeated_limit,
        auto_retry=curr_auto_retry,
    )

    simulated = _evaluate_policy_rules(
        at_risk_payments,
        max_retries=sim_max_retries,
        retry_delay=sim_retry_delay,
        high_value_paise=sim_high_val,
        escalation_paise=sim_escalation,
        repeated_limit=sim_repeated_limit,
        auto_retry=sim_auto_retry,
    )

    # 5. Compute deltas
    diff_recovery = round(simulated["expected_recovery"] - baseline["expected_recovery"], 2)
    pct_change = 0.0
    if baseline["expected_recovery"] > 0:
        pct_change = round((diff_recovery / baseline["expected_recovery"]) * 100, 1)

    diff_stopped = simulated["stopped_cases"] - baseline["stopped_cases"]
    diff_escalated = simulated["escalated_cases"] - baseline["escalated_cases"]

    return {
        # Top-level keys for direct/legacy frontend access
        "expected_recovery": simulated["expected_recovery"],
        "stopped_cases": simulated["stopped_cases"],
        "escalated_cases": simulated["escalated_cases"],
        "recoverable_cases": simulated["recoverable_cases"],
        # Rich comparison structure
        "current": {
            "max_retries": curr_max_retries,
            "retry_delay_minutes": curr_retry_delay,
            "high_value_threshold": curr_high_val / 100,
            "escalation_threshold": curr_escalation / 100,
            "repeated_failure_limit": curr_repeated_limit,
            "auto_retry_enabled": curr_auto_retry,
            "expected_recovery": baseline["expected_recovery"],
            "stopped_cases": baseline["stopped_cases"],
            "escalated_cases": baseline["escalated_cases"],
            "recoverable_cases": baseline["recoverable_cases"],
        },
        "simulated": {
            "max_retries": sim_max_retries,
            "retry_delay_minutes": sim_retry_delay,
            "high_value_threshold": sim_high_val / 100,
            "escalation_threshold": sim_escalation / 100,
            "repeated_failure_limit": sim_repeated_limit,
            "auto_retry_enabled": sim_auto_retry,
            "expected_recovery": simulated["expected_recovery"],
            "stopped_cases": simulated["stopped_cases"],
            "escalated_cases": simulated["escalated_cases"],
            "recoverable_cases": simulated["recoverable_cases"],
        },
        "delta": {
            "recovery_diff": diff_recovery,
            "recovery_pct": pct_change,
            "stopped_diff": diff_stopped,
            "escalated_diff": diff_escalated,
        },
        "total_at_risk_payments": len(at_risk_payments),
    }
