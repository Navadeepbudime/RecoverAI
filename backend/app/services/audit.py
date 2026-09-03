from ..extensions import db
from ..models import AuditLog


class AuditLogger:
    def log(self, case, event, reason, ai_recommendation=None, policy_result=None, executed_action=None, result=None):
        entry = AuditLog(
            case=case,
            case_external_id=case.case_id,
            event=event,
            customer_external_id=case.payment.customer.external_id,
            payment_external_id=case.payment.external_id,
            ai_recommendation=ai_recommendation,
            policy_result=policy_result,
            executed_action=executed_action,
            result=result,
            reason=reason,
        )
        db.session.add(entry)
        return entry
