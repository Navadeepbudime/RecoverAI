from sqlalchemy import func

from ..models import CaseStatus, Payment, RecoveryCase


def dashboard_metrics():
    active_cases = RecoveryCase.query.filter_by(status=CaseStatus.ACTIVE.value).count()
    recovered_cases = RecoveryCase.query.filter_by(status=CaseStatus.RECOVERED.value).count()
    stopped_cases = RecoveryCase.query.filter(RecoveryCase.status.in_([CaseStatus.STOPPED.value, CaseStatus.ESCALATED.value])).count()
    failed_payments = Payment.query.filter(Payment.status.in_(["failed", "checkout_abandoned"])).count()
    revenue_at_risk = (
        Payment.query.filter(Payment.status.in_(["failed", "checkout_abandoned"]))
        .with_entities(func.coalesce(func.sum(Payment.amount_paise), 0))
        .scalar()
        or 0
    )
    recovered_revenue = (
        Payment.query.filter_by(status="recovered")
        .with_entities(func.coalesce(func.sum(Payment.amount_paise), 0))
        .scalar()
        or 0
    )
    probability_weighted = sum(case.payment.amount_paise * case.recovery_probability for case in RecoveryCase.query.all())
    total_cases = RecoveryCase.query.count()
    return {
        "revenue_at_risk": revenue_at_risk / 100,
        "potentially_recoverable_revenue": round(probability_weighted / 100, 2),
        "revenue_recovered": recovered_revenue / 100,
        "recovery_rate": round((recovered_cases / total_cases) * 100, 1) if total_cases else 0,
        "failed_payments": failed_payments,
        "active_recovery_cases": active_cases,
        "successful_recoveries": recovered_cases,
        "stopped_escalated_cases": stopped_cases,
    }


def action_breakdown():
    rows = (
        RecoveryCase.query.with_entities(RecoveryCase.executed_action, func.count(RecoveryCase.id))
        .group_by(RecoveryCase.executed_action)
        .all()
    )
    return [{"name": action or "PENDING", "value": count} for action, count in rows]


def failure_breakdown():
    rows = Payment.query.with_entities(Payment.failure_reason, func.count(Payment.id)).group_by(Payment.failure_reason).all()
    return [{"name": reason or "unknown", "value": count} for reason, count in rows]
