from flask import Blueprint, current_app, jsonify, request

from ..agents.recovery_agent import RecoveryAgent
from ..extensions import db
from ..models import AuditLog, Customer, MerchantPolicy, Payment, RecoveryCase
from ..policies.engine import PolicyEngine
from ..providers import get_payment_provider
from ..services.action_executor import ActionExecutor
from ..services.analytics import action_breakdown, dashboard_metrics, failure_breakdown
from ..services.audit import AuditLogger
from ..services.scoring import score_recovery
from ..services.simulator import simulate_policy
from ..utils.razorpay import verify_webhook_signature

api_bp = Blueprint("api", __name__)


def _provider():
    """Return the payment provider configured for this app."""
    return get_payment_provider(current_app.config["PAYMENT_PROVIDER"])


def get_policy():
    policy = MerchantPolicy.query.filter_by(merchant_id="demo_merchant").first()
    if not policy:
        policy = MerchantPolicy(merchant_id="demo_merchant")
        db.session.add(policy)
        db.session.commit()
    return policy


def process_case(case):
    provider = _provider()
    policy = get_policy()
    logger = AuditLogger()

    # 1. Context analysis
    score = score_recovery(case.payment, case.payment.customer)
    logger.log(case, "CONTEXT_ANALYZED", "Customer and payment context analyzed for revenue risk.")

    # 2. AI recommendation
    recommendation = RecoveryAgent().recommend(case.payment, case.payment.customer, score, policy)
    case.risk_score = recommendation.risk_score
    case.recovery_probability = recommendation.recovery_probability
    case.recommended_action = recommendation.recommended_action
    case.priority = recommendation.priority
    case.ai_explanation = recommendation.reason
    logger.log(case, "AI_DECISION", recommendation.reason, ai_recommendation=recommendation.to_dict())

    # 3. Policy validation
    decision = PolicyEngine().validate(case.payment, case.payment.customer, recommendation, policy)
    case.policy_decision = "ALLOWED" if decision.allowed else "OVERRIDDEN"
    case.policy_reason = decision.reason
    logger.log(case, "POLICY_CHECK", decision.reason, ai_recommendation=recommendation.to_dict(), policy_result=decision.to_dict())

    # 4. Action execution via payment provider
    result = ActionExecutor(provider).execute(case, decision.final_action)
    logger.log(
        case,
        "ACTION_EXECUTED",
        decision.reason,
        ai_recommendation=recommendation.to_dict(),
        policy_result=decision.to_dict(),
        executed_action=decision.final_action,
        result=result["outcome"],
    )
    db.session.commit()
    return case


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@api_bp.get("/health")
def health():
    provider = _provider()
    return jsonify(
        {
            "status": "ok",
            "demo_mode": not provider.is_live,
            "payment_provider": provider.name,
            "ai_provider": "demo-rule-agent" if not current_app.config.get("GEMINI_API_KEY") else "gemini-configured",
            "razorpay": "configured" if current_app.config.get("RAZORPAY_KEY_ID") else "not-configured",
        }
    )


# ---------------------------------------------------------------------------
# Metrics & Analytics
# ---------------------------------------------------------------------------


@api_bp.get("/metrics")
def metrics():
    return jsonify(dashboard_metrics())


@api_bp.get("/analytics")
def analytics():
    return jsonify({"actions": action_breakdown(), "failures": failure_breakdown()})


# ---------------------------------------------------------------------------
# Recovery Cases
# ---------------------------------------------------------------------------


@api_bp.get("/cases")
def cases():
    status = request.args.get("status")
    query = RecoveryCase.query
    if status:
        query = query.filter_by(status=status.upper())
    return jsonify([case.to_dict() for case in query.order_by(RecoveryCase.updated_at.desc()).all()])


@api_bp.get("/cases/<case_id>")
def case_detail(case_id):
    case = RecoveryCase.query.filter_by(case_id=case_id).first_or_404()
    return jsonify(case.to_dict(include_detail=True))


@api_bp.post("/cases/<case_id>/process")
def process_case_endpoint(case_id):
    case = RecoveryCase.query.filter_by(case_id=case_id).first_or_404()
    return jsonify(process_case(case).to_dict(include_detail=True))


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


@api_bp.get("/audit")
def audit():
    entries = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return jsonify([entry.to_dict() for entry in entries])


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


@api_bp.get("/policy")
def policy():
    return jsonify(get_policy().to_dict())


@api_bp.put("/policy")
def update_policy():
    payload = request.get_json(force=True)
    pol = get_policy()
    if "max_automatic_retries" in payload:
        pol.max_automatic_retries = max(0, int(payload["max_automatic_retries"]))
    if "retry_delay_minutes" in payload:
        pol.retry_delay_minutes = max(1, int(payload["retry_delay_minutes"]))
    if "high_value_threshold" in payload:
        pol.high_value_threshold_paise = max(0, int(float(payload["high_value_threshold"]) * 100))
    if "escalation_threshold" in payload:
        pol.escalation_threshold_paise = max(0, int(float(payload["escalation_threshold"]) * 100))
    if "repeated_failure_limit" in payload:
        pol.repeated_failure_limit = max(1, int(payload["repeated_failure_limit"]))
    if "auto_retry_enabled" in payload:
        pol.auto_retry_enabled = bool(payload["auto_retry_enabled"])
    db.session.commit()
    return jsonify(pol.to_dict())


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------


@api_bp.post("/simulate")
def simulate():
    return jsonify(simulate_policy(request.get_json(force=True)))


# ---------------------------------------------------------------------------
# Razorpay Webhook (only functional when PAYMENT_PROVIDER=razorpay)
# ---------------------------------------------------------------------------


@api_bp.post("/webhooks/razorpay")
def razorpay_webhook():
    """Accept Razorpay webhook events.

    This endpoint is always registered so the URL doesn't 404, but it
    only processes events when the payment provider is set to 'razorpay'
    and credentials are configured.
    """
    provider_name = current_app.config.get("PAYMENT_PROVIDER", "demo")
    if provider_name != "razorpay":
        return jsonify({"received": True, "note": "Razorpay provider not active — event acknowledged but not processed."}), 200

    signature = request.headers.get("X-Razorpay-Signature")
    secret = current_app.config.get("RAZORPAY_WEBHOOK_SECRET")
    if secret and not verify_webhook_signature(request.get_data(), signature, secret):
        return jsonify({"error": "invalid webhook signature"}), 400

    payload = request.get_json(force=True)
    event = payload.get("event", "unknown")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    external_id = payment_entity.get("id")
    amount = payment_entity.get("amount", 0)
    email = payment_entity.get("email") or "razorpay@example.com"

    customer = Customer.query.filter_by(email=email).first()
    if not customer:
        customer = Customer(external_id=f"rzp_{email}", name="Razorpay Customer", email=email)
        db.session.add(customer)
        db.session.flush()

    payment = Payment.query.filter_by(external_id=external_id).first() if external_id else None
    if not payment:
        payment = Payment(
            external_id=external_id or f"rzp_event_{AuditLog.query.count() + 1}",
            customer=customer,
            amount_paise=amount,
            status="failed" if "failed" in event else "created",
            failure_reason=payment_entity.get("error_reason") or "network_error",
            payment_method=payment_entity.get("method") or "unknown",
        )
        db.session.add(payment)
        db.session.flush()

    # Prevent duplicate cases for the same payment
    if payment.status == "failed" and not RecoveryCase.query.filter_by(payment_id=payment.id).first():
        case = RecoveryCase(case_id=f"CASE-{payment.external_id}", payment=payment)
        db.session.add(case)
        db.session.flush()
        process_case(case)
    else:
        db.session.commit()
    return jsonify({"received": True, "event": event})
