from ..models import Payment


RISK_STATUSES = {"failed", "checkout_abandoned"}


def at_risk_payments():
    return Payment.query.filter(Payment.status.in_(RISK_STATUSES)).all()


def is_revenue_at_risk(payment):
    return payment.status in RISK_STATUSES or payment.checkout_abandoned
