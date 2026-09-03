import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from app.services.analytics import dashboard_metrics
from app.services.evaluation import calculate_evaluation_metrics
from app.services.live_simulator import trigger_live_simulation

app = create_app()
with app.app_context():
    print("=" * 76)
    print("RECOVERAI: END-TO-END DEMO EXECUTION")
    print("Failure Event -> AI Decision -> Guardrail -> Execution -> Revenue Impact")
    print("=" * 76)

    # -------------------------------------------------------------------------
    # DEMO RUN: Bank Gateway Timeout (₹8,499)
    # -------------------------------------------------------------------------
    print("\n[SCENARIO: BANK GATEWAY TIMEOUT (INR 8,499)]")
    m0 = dashboard_metrics()
    ev0 = calculate_evaluation_metrics()
    print(f"  Starting Recovered Revenue: INR {m0['revenue_recovered']:,.2f}")

    res = trigger_live_simulation("BANK_TIMEOUT", app.config)
    case_data = res["case"]
    print(f"\n  [1. Ingestion] Failed Payment: {case_data['payment']['external_id']} (INR {case_data['payment']['amount']:,.2f})")
    print(f"      Customer: {case_data['customer']['name']} ({case_data['customer']['email']})")

    for step in res["pipeline_trace"]:
        print(f"  --> {step['stage']}: {step['status']}")
        print(f"      {step['detail']}")

    m1 = dashboard_metrics()
    ev1 = calculate_evaluation_metrics()
    delta_recovered = m1["revenue_recovered"] - m0["revenue_recovered"]

    print("\n  [Decision & Guardrail Verification]")
    print(f"  - AI Recommendation: {case_data['recommended_action']} (Risk: {case_data['risk_score']}/100, Prob: {case_data['recovery_probability']:.0%})")
    print(f"  - Policy Guardrail:  {case_data['policy_decision']} ({case_data['policy_reason']})")
    print(f"  - Executed Action:   {case_data['executed_action']} -> Outcome: {case_data['outcome']}")

    print("\n  [Revenue Impact]")
    print(f"  - Captured Revenue:      INR {m0['revenue_recovered']:,.2f} -> INR {m1['revenue_recovered']:,.2f} (+INR {delta_recovered:,.2f})")
    print(f"  - Baseline Naive Yield:  INR {ev1['baseline_recovered_revenue']:,.2f}")
    print(f"  - RecoverAI Total Yield: INR {ev1['recoverai_recovered_revenue']:,.2f}")
    print(f"  - Incremental Lift:      +INR {ev1['incremental_revenue']:,.2f} (+{ev1['incremental_lift_percentage']}%)")
    print("=" * 76)
