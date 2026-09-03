RECOVERABLE_FAILURES = {
    "bank_timeout": 0.18,
    "network_error": 0.16,
    "authentication_failure": 0.08,
    "checkout_abandonment": 0.1,
    "card_expired": 0.02,
    "insufficient_funds": -0.16,
    "repeated_failures": -0.24,
}


def score_recovery(payment, customer):
    total = customer.successful_payments + customer.failed_payments
    success_rate = customer.successful_payments / total if total else 0
    amount_rupees = payment.amount_paise / 100

    probability = 0.32
    probability += success_rate * 0.28
    probability += RECOVERABLE_FAILURES.get(payment.failure_reason or "", -0.04)
    probability += min(customer.previous_recoveries, 3) * 0.04
    probability -= min(customer.failed_payments, 6) * 0.035
    probability -= min(payment.retry_count, 4) * 0.08

    if amount_rupees > 50000:
        probability -= 0.12
    elif amount_rupees > 20000:
        probability -= 0.06

    probability = max(0.05, min(0.94, round(probability, 2)))
    risk_score = round((1 - probability) * 40 + (amount_rupees / 100000) * 35 + payment.retry_count * 8)
    risk_score = max(1, min(100, risk_score))

    return {
        "risk_score": risk_score,
        "recovery_probability": probability,
        "factors": {
            "historical_success_rate": round(success_rate, 2),
            "failure_reason": payment.failure_reason,
            "amount": amount_rupees,
            "retry_count": payment.retry_count,
            "previous_recoveries": customer.previous_recoveries,
        },
    }
