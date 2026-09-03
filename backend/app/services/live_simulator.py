"""Live Payment Failure Simulator.

Generates live synthetic payment events on demand, streaming them through the full
RecoverAI pipeline:
Ingest → Risk Detect → Memory & Context → Scoring → AI Synthesis → Policy Guardrail → Execution → Audit.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict

from ..extensions import db
from ..models import AuditLog, Customer, MerchantPolicy, Payment, RecoveryCase
from ..agents.recovery_agent import RecoveryAgent, get_configured_ai_provider
from ..policies.engine import PolicyEngine
from ..services.action_executor import ActionExecutor
from ..services.scoring import score_recovery
from ..services.recovery_memory import CustomerRecoveryMemory
from ..services.audit import AuditLogger
from ..providers import get_payment_provider


SCENARIO_TEMPLATES = {
    "BANK_TIMEOUT": {
        "label": "Bank Gateway Timeout",
        "amount_paise": 849900,
        "failure_reason": "bank_timeout",
        "payment_method": "card",
        "checkout_abandoned": False,
        "customer_email": "aarav@example.com",
        "customer_name": "Aarav Mehta",
    },
    "INSUFFICIENT_FUNDS": {
        "label": "Insufficient Account Balance",
        "amount_paise": 2499900,
        "failure_reason": "insufficient_funds",
        "payment_method": "upi",
        "checkout_abandoned": False,
        "customer_email": "diya@example.com",
        "customer_name": "Diya Shah",
    },
    "EXPIRED_CARD": {
        "label": "Card Expired",
        "amount_paise": 499900,
        "failure_reason": "card_expired",
        "payment_method": "card",
        "checkout_abandoned": False,
        "customer_email": "kabir@example.com",
        "customer_name": "Kabir Rao",
    },
    "CHECKOUT_ABANDONED": {
        "label": "Checkout Abandoned",
        "amount_paise": 329900,
        "failure_reason": "checkout_abandonment",
        "payment_method": "upi",
        "checkout_abandoned": True,
        "customer_email": "rohan@example.com",
        "customer_name": "Rohan Kapoor",
    },
    "HIGH_VALUE_TIMEOUT": {
        "label": "High-Value Transaction Timeout (₹75,000)",
        "amount_paise": 7500000,
        "failure_reason": "bank_timeout",
        "payment_method": "netbanking",
        "checkout_abandoned": False,
        "customer_email": "karan@example.com",
        "customer_name": "Karan Thakur",
    },
}


def trigger_live_simulation(scenario_key: str, app_config: Dict[str, Any]) -> Dict[str, Any]:
    scenario = SCENARIO_TEMPLATES.get(scenario_key.upper())
    if not scenario:
        raise ValueError(f"Unknown simulation scenario '{scenario_key}'. Available: {list(SCENARIO_TEMPLATES.keys())}")

    # 1. Fetch or create customer
    customer = Customer.query.filter_by(email=scenario["customer_email"]).first()
    if not customer:
        customer = Customer(
            external_id=f"cust_sim_{int(time.time())}",
            name=scenario["customer_name"],
            email=scenario["customer_email"],
            lifetime_value_paise=500000,
            successful_payments=3,
            failed_payments=1,
            previous_recoveries=1,
        )
        db.session.add(customer)
        db.session.flush()

    # 2. Ingest payment event
    ts = int(time.time() * 1000) % 1000000
    payment_ext_id = f"pay_live_{ts}"
    payment = Payment(
        external_id=payment_ext_id,
        customer=customer,
        amount_paise=scenario["amount_paise"],
        status="checkout_abandoned" if scenario["checkout_abandoned"] else "failed",
        failure_reason=scenario["failure_reason"],
        payment_method=scenario["payment_method"],
        retry_count=0,
        checkout_abandoned=scenario["checkout_abandoned"],
    )
    db.session.add(payment)
    db.session.flush()

    # 3. Create recovery case
    case_ext_id = f"CASE-{payment_ext_id}"
    case = RecoveryCase(
        case_id=case_ext_id,
        payment=payment,
        status="ACTIVE",
    )
    db.session.add(case)
    db.session.flush()

    pipeline_trace = []
    logger = AuditLogger()

    # Stage 1: Ingestion
    logger.log(case, "EVENT_INGESTED", f"Live payment event received: {scenario['label']} of INR {payment.amount_paise / 100:,.2f}")
    pipeline_trace.append({
        "stage": "1. Event Ingestion",
        "status": "COMPLETED",
        "detail": f"Captured failed payment {payment_ext_id} (INR {payment.amount_paise / 100:,.2f})",
    })

    # Stage 2: Memory & Context
    memory = CustomerRecoveryMemory.get_memory(customer, current_payment_id=payment.id)
    score = score_recovery(payment, customer)
    logger.log(case, "CONTEXT_ANALYZED", f"Context and memory analyzed. Score: {score['risk_score']}/100. Memory: {memory.summary_text}")
    pipeline_trace.append({
        "stage": "2. Context & Memory",
        "status": "COMPLETED",
        "detail": f"Risk Score: {score['risk_score']}/100, Recovery Prob: {score['recovery_probability']:.0%}. Memory: {memory.summary_text}",
    })

    # Stage 3: AI Recommendation
    policy = MerchantPolicy.query.filter_by(merchant_id="demo_merchant").first()
    if not policy:
        policy = MerchantPolicy(merchant_id="demo_merchant")
        db.session.add(policy)
        db.session.flush()

    ai_provider = get_configured_ai_provider(app_config)
    agent = RecoveryAgent(provider=ai_provider)
    recommendation = agent.recommend(payment, customer, score, policy, memory)

    case.risk_score = recommendation.risk_score
    case.recovery_probability = recommendation.recovery_probability
    case.recommended_action = recommendation.recommended_action.value
    case.priority = recommendation.priority
    case.ai_explanation = recommendation.reason

    logger.log(case, "AI_DECISION", recommendation.reason, ai_recommendation=recommendation.to_dict())
    pipeline_trace.append({
        "stage": "3. AI Recommendation",
        "status": "COMPLETED",
        "detail": f"Recommended {recommendation.recommended_action.value} ({recommendation.priority} priority). Reason: {recommendation.reason}",
    })

    # Stage 4: Policy Guardrail Verification
    decision = PolicyEngine().validate(payment, customer, recommendation, policy)
    case.policy_decision = "ALLOWED" if decision.allowed else "OVERRIDDEN"
    case.policy_reason = decision.reason
    logger.log(
        case,
        "POLICY_CHECK",
        decision.reason,
        ai_recommendation=recommendation.to_dict(),
        policy_result=decision.to_dict(),
    )
    pipeline_trace.append({
        "stage": "4. Policy Guardrail",
        "status": "ALLOWED" if decision.allowed else "OVERRIDDEN",
        "detail": f"Guardrail verdict: {case.policy_decision}. Action: {decision.final_action}. Rationale: {decision.reason}",
    })

    # Stage 5: Action Execution via Provider
    provider = get_payment_provider(app_config.get("PAYMENT_PROVIDER", "demo"))
    exec_result = ActionExecutor(provider).execute(case, decision.final_action)

    logger.log(
        case,
        "ACTION_EXECUTED",
        decision.reason,
        ai_recommendation=recommendation.to_dict(),
        policy_result=decision.to_dict(),
        executed_action=decision.final_action,
        result=exec_result["outcome"],
    )
    pipeline_trace.append({
        "stage": "5. Action Execution",
        "status": "COMPLETED",
        "detail": f"Executed: {decision.final_action} → Result: {exec_result['outcome']}",
    })

    db.session.commit()

    return {
        "case": case.to_dict(include_detail=True),
        "pipeline_trace": pipeline_trace,
        "scenario": scenario_key,
    }
