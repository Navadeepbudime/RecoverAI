from datetime import datetime

from ..extensions import db
from ..domain import CaseStatus


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40))
    lifetime_value_paise = db.Column(db.Integer, default=0)
    successful_payments = db.Column(db.Integer, default=0)
    failed_payments = db.Column(db.Integer, default=0)
    previous_recoveries = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship("Payment", backref="customer", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "external_id": self.external_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "lifetime_value": self.lifetime_value_paise / 100,
            "successful_payments": self.successful_payments,
            "failed_payments": self.failed_payments,
            "previous_recoveries": self.previous_recoveries,
        }


class MerchantPolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.String(64), unique=True, nullable=False, default="demo_merchant")
    max_automatic_retries = db.Column(db.Integer, default=2)
    retry_delay_minutes = db.Column(db.Integer, default=30)
    high_value_threshold_paise = db.Column(db.Integer, default=2_000_000)
    escalation_threshold_paise = db.Column(db.Integer, default=5_000_000)
    repeated_failure_limit = db.Column(db.Integer, default=3)
    auto_retry_enabled = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "merchant_id": self.merchant_id,
            "max_automatic_retries": self.max_automatic_retries,
            "retry_delay_minutes": self.retry_delay_minutes,
            "high_value_threshold": self.high_value_threshold_paise / 100,
            "escalation_threshold": self.escalation_threshold_paise / 100,
            "repeated_failure_limit": self.repeated_failure_limit,
            "auto_retry_enabled": self.auto_retry_enabled,
        }


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(80), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    amount_paise = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(8), default="INR")
    status = db.Column(db.String(40), nullable=False)
    failure_reason = db.Column(db.String(80))
    payment_method = db.Column(db.String(40), default="card")
    retry_count = db.Column(db.Integer, default=0)
    checkout_abandoned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recovered_at = db.Column(db.DateTime)

    case = db.relationship("RecoveryCase", backref="payment", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "external_id": self.external_id,
            "amount": self.amount_paise / 100,
            "currency": self.currency,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "payment_method": self.payment_method,
            "retry_count": self.retry_count,
            "checkout_abandoned": self.checkout_abandoned,
            "created_at": self.created_at.isoformat(),
            "recovered_at": self.recovered_at.isoformat() if self.recovered_at else None,
        }


class RecoveryCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.String(80), unique=True, nullable=False)
    payment_id = db.Column(db.Integer, db.ForeignKey("payment.id"), nullable=False)
    status = db.Column(db.String(40), default=CaseStatus.ACTIVE.value)
    risk_score = db.Column(db.Integer, default=0)
    recovery_probability = db.Column(db.Float, default=0)
    recommended_action = db.Column(db.String(80))
    priority = db.Column(db.String(20), default="MEDIUM")
    ai_explanation = db.Column(db.Text)
    policy_decision = db.Column(db.String(40))
    policy_reason = db.Column(db.Text)
    executed_action = db.Column(db.String(80))
    outcome = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audits = db.relationship("AuditLog", backref="case", lazy=True, cascade="all,delete")

    def to_dict(self, include_detail=False):
        data = {
            "id": self.id,
            "case_id": self.case_id,
            "status": self.status,
            "risk_score": self.risk_score,
            "recovery_probability": self.recovery_probability,
            "recommended_action": self.recommended_action,
            "priority": self.priority,
            "ai_explanation": self.ai_explanation,
            "policy_decision": self.policy_decision,
            "policy_reason": self.policy_reason,
            "executed_action": self.executed_action,
            "outcome": self.outcome,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "payment": self.payment.to_dict(),
            "customer": self.payment.customer.to_dict(),
        }
        if include_detail:
            data["timeline"] = [audit.to_dict() for audit in sorted(self.audits, key=lambda item: item.timestamp)]
        return data


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("recovery_case.id"))
    case_external_id = db.Column(db.String(80), nullable=False)
    event = db.Column(db.String(80), nullable=False)
    customer_external_id = db.Column(db.String(64))
    payment_external_id = db.Column(db.String(80))
    ai_recommendation = db.Column(db.JSON)
    policy_result = db.Column(db.JSON)
    executed_action = db.Column(db.String(80))
    result = db.Column(db.String(80))
    reason = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "case_id": self.case_external_id,
            "event": self.event,
            "customer_id": self.customer_external_id,
            "payment_id": self.payment_external_id,
            "ai_recommendation": self.ai_recommendation,
            "policy_result": self.policy_result,
            "executed_action": self.executed_action,
            "result": self.result,
            "reason": self.reason,
        }
