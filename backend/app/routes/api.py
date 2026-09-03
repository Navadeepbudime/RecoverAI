from datetime import datetime, timezone
from flask import Blueprint, current_app, jsonify, request

from ..agents.recovery_agent import RecoveryAgent, get_configured_ai_provider
from ..extensions import db
from ..models import AuditLog, CaseStatus, Customer, MerchantPolicy, Payment, RecoveryCase
from ..policies.engine import PolicyEngine
from ..providers import get_payment_provider
from ..services.action_executor import ActionExecutor
from ..services.analytics import action_breakdown, dashboard_metrics, failure_breakdown
from ..services.audit import AuditLogger
from ..services.evaluation import calculate_evaluation_metrics
from ..services.live_simulator import trigger_live_simulation, SCENARIO_TEMPLATES
from ..services.recovery_memory import CustomerRecoveryMemory
from ..services.scoring import score_recovery
from ..services.simulator import simulate_policy
from ..utils.razorpay import verify_webhook_signature

api_bp = Blueprint("api", __name__)


def _provider():
    """Return the payment provider configured for this app."""
    return get_payment_provider(current_app.config.get("PAYMENT_PROVIDER", "demo"))


def get_policy():
    policy = MerchantPolicy.query.filter_by(merchant_id="demo_merchant").first()
    if not policy:
        policy = MerchantPolicy(merchant_id="demo_merchant")
        db.session.add(policy)
        db.session.commit()
    return policy


def process_case(case, force: bool = False):
    """Processes a recovery case through the complete RecoverAI pipeline."""
    # 1. Idempotency check: If already recovered, no further action is required
    if not force and case.status == CaseStatus.RECOVERED.value:
        return case

    # 2. Cooldown check: If recently executed within 120 seconds, avoid duplicate action
    if not force and case.outcome and case.updated_at:
        now_utc = datetime.now(timezone.utc)
        case_time = case.updated_at
        if case_time.tzinfo is None:
            case_time = case_time.replace(tzinfo=timezone.utc)
        elapsed = (now_utc - case_time).total_seconds()
        if elapsed < 120:
            return case

    provider = _provider()
    policy = get_policy()
    logger = AuditLogger()

    # 1. Customer recovery memory & context analysis
    memory = CustomerRecoveryMemory.get_memory(case.payment.customer, current_payment_id=case.payment.id)
    score = score_recovery(case.payment, case.payment.customer)
    logger.log(case, "CONTEXT_ANALYZED", f"Customer context analyzed. {memory.summary_text}")

    # 2. AI recommendation (uses Gemini if configured, otherwise Demo provider)
    ai_provider = get_configured_ai_provider(current_app.config if current_app else None)
    agent = RecoveryAgent(provider=ai_provider)
    recommendation = agent.recommend(case.payment, case.payment.customer, score, policy, memory)

    case.risk_score = recommendation.risk_score
    case.recovery_probability = recommendation.recovery_probability
    case.recommended_action = recommendation.recommended_action.value
    case.priority = recommendation.priority
    case.ai_explanation = recommendation.reason
    logger.log(case, "AI_DECISION", recommendation.reason, ai_recommendation=recommendation.to_dict())

    # 3. Deterministic policy guardrails
    decision = PolicyEngine().validate(case.payment, case.payment.customer, recommendation, policy)
    case.policy_decision = "ALLOWED" if decision.allowed else "OVERRIDDEN"
    case.policy_reason = decision.reason
    logger.log(
        case,
        "POLICY_CHECK",
        decision.reason,
        ai_recommendation=recommendation.to_dict(),
        policy_result=decision.to_dict(),
    )

    # 4. Action execution
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
# Health & Status
# ---------------------------------------------------------------------------


@api_bp.get("/health")
def health():
    provider = _provider()
    gemini_key = current_app.config.get("GEMINI_API_KEY")
    ai_status = "gemini-active" if (gemini_key and str(gemini_key).strip()) else "demo-rule-agent"
    return jsonify(
        {
            "status": "ok",
            "demo_mode": not provider.is_live,
            "payment_provider": provider.name,
            "ai_provider": ai_status,
            "gemini_configured": bool(gemini_key and str(gemini_key).strip()),
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
    return jsonify({
        "actions": action_breakdown(),
        "failures": failure_breakdown(),
        "evaluation": calculate_evaluation_metrics(),
    })


@api_bp.get("/evaluation")
def evaluation():
    """Returns the comparative Baseline Naive Retry vs. RecoverAI evaluation."""
    return jsonify(calculate_evaluation_metrics())


# ---------------------------------------------------------------------------
# Recovery Cases (with Filtering & Search)
# ---------------------------------------------------------------------------


@api_bp.get("/cases")
def cases():
    status = request.args.get("status")
    search = request.args.get("search", "").strip().lower()

    query = RecoveryCase.query.join(Payment).join(Customer)
    if status and status.upper() not in {"ALL", ""}:
        query = query.filter(RecoveryCase.status == status.upper())

    if search:
        query = query.filter(
            db.or_(
                RecoveryCase.case_id.ilike(f"%{search}%"),
                Payment.external_id.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
                Payment.failure_reason.ilike(f"%{search}%"),
            )
        )

    return jsonify([case.to_dict() for case in query.order_by(RecoveryCase.updated_at.desc()).all()])


@api_bp.get("/cases/<case_id>")
def case_detail(case_id):
    case = RecoveryCase.query.filter_by(case_id=case_id).first_or_404()
    return jsonify(case.to_dict(include_detail=True))


@api_bp.post("/cases/<case_id>/process")
def process_case_endpoint(case_id):
    case = RecoveryCase.query.filter_by(case_id=case_id).first_or_404()
    force = request.args.get("force", "false").lower() == "true"
    if request.is_json and request.get_json(silent=True):
        force = force or bool(request.get_json().get("force", False))
    return jsonify(process_case(case, force=force).to_dict(include_detail=True))


# ---------------------------------------------------------------------------
# Live Simulation Trigger
# ---------------------------------------------------------------------------


@api_bp.post("/simulate-live")
def simulate_live():
    """Trigger on-demand live failure event and trace execution through agent."""
    payload = request.get_json(force=True) or {}
    scenario = payload.get("scenario", "BANK_TIMEOUT")
    result = trigger_live_simulation(scenario, current_app.config)
    return jsonify(result)


@api_bp.get("/simulate-live/scenarios")
def list_scenarios():
    """List available templates for live simulation."""
    return jsonify([
        {"key": k, "label": v["label"], "amount": v["amount_paise"] / 100, "reason": v["failure_reason"]}
        for k, v in SCENARIO_TEMPLATES.items()
    ])


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


@api_bp.get("/audit")
def audit():
    event_filter = request.args.get("event")
    query = AuditLog.query
    if event_filter and event_filter.upper() != "ALL":
        query = query.filter(AuditLog.event == event_filter.upper())
    entries = query.order_by(AuditLog.timestamp.desc()).limit(200).all()
    return jsonify([entry.to_dict() for entry in entries])


# ---------------------------------------------------------------------------
# Policy & Policy Simulator
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


@api_bp.post("/simulate")
def simulate():
    return jsonify(simulate_policy(request.get_json(force=True)))


# ---------------------------------------------------------------------------
# Razorpay Webhook
# ---------------------------------------------------------------------------


@api_bp.post("/webhooks/razorpay")
def razorpay_webhook():
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

    if payment.status == "failed" and not RecoveryCase.query.filter_by(payment_id=payment.id).first():
        case = RecoveryCase(case_id=f"CASE-{payment.external_id}", payment=payment)
        db.session.add(case)
        db.session.flush()
        process_case(case)
    else:
        db.session.commit()
    return jsonify({"received": True, "event": event})
