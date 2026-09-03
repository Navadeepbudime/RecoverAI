"""AI Providers for RecoverAI.

Supports:
1. DemoAIProvider: Deterministic rule-backed next best action (zero API keys needed).
2. GeminiRecoveryProvider: Real Gemini LLM reasoning with structured JSON output and
   graceful automatic fallback to DemoAIProvider on failure.
"""

import json
import logging
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .schemas import RecoveryAction, RecoveryRecommendation

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Abstract interface for Recovery AI Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""

    @abstractmethod
    def recommend(
        self,
        payment: Any,
        customer: Any,
        score: Dict[str, Any],
        policy: Any,
        memory: Optional[Any] = None,
    ) -> RecoveryRecommendation:
        """Generate a next-best-action recovery recommendation."""


class DemoAIProvider(BaseAIProvider):
    """Deterministic, explainable rule-backed AI provider.

    Incorporates customer recovery memory, failure taxonomy, and policy bounds.
    Requires no external credentials.
    """

    @property
    def name(self) -> str:
        return "demo"

    def recommend(
        self,
        payment: Any,
        customer: Any,
        score: Dict[str, Any],
        policy: Any,
        memory: Optional[Any] = None,
    ) -> RecoveryRecommendation:
        amount_rupees = payment.amount_paise / 100
        mem_bias = getattr(memory, "recommended_bias", None)
        mem_text = getattr(memory, "summary_text", "")

        # 1. Evaluate hard stop / escalation conditions first
        if payment.retry_count >= policy.max_automatic_retries:
            action = RecoveryAction.STOP_RECOVERY
            reason = (
                f"Maximum automatic retries ({policy.max_automatic_retries}) reached. "
                "Stopping automated recovery to prevent customer fatigue and bank fraud flags."
            )
            priority = "MEDIUM"
        elif customer.failed_payments >= policy.repeated_failure_limit:
            action = RecoveryAction.STOP_RECOVERY
            reason = (
                f"Customer has accumulated {customer.failed_payments} failed payments, exceeding merchant threshold "
                f"({policy.repeated_failure_limit}). Stopping recovery to mitigate fraud and non-payment risk."
            )
            priority = "HIGH"
        elif payment.amount_paise >= policy.escalation_threshold_paise:
            action = RecoveryAction.ESCALATE_TO_MERCHANT
            reason = (
                f"Transaction amount of INR {amount_rupees:,.2f} exceeds merchant escalation threshold "
                f"(INR {policy.escalation_threshold_paise / 100:,.2f}). Human merchant review required."
            )
            priority = "CRITICAL"

        # 2. Next-Best-Action selection based on failure type & customer memory
        elif payment.failure_reason in {"bank_timeout", "network_error"}:
            if not policy.auto_retry_enabled:
                action = RecoveryAction.SEND_PAYMENT_LINK
                reason = "Temporary gateway timeout occurred, but automatic retries are disabled by merchant policy. Sending payment link instead."
                priority = "MEDIUM"
            elif mem_bias == "PREFER_PAYMENT_LINK":
                action = RecoveryAction.SEND_PAYMENT_LINK
                reason = (
                    f"Temporary gateway timeout detected. However, customer memory shows past retries failed: {mem_text}. "
                    "Optimizing next best action to SEND_PAYMENT_LINK for direct resolution."
                )
                priority = "HIGH"
            else:
                action = RecoveryAction.RETRY_PAYMENT
                reason = (
                    f"Temporary {payment.failure_reason.replace('_', ' ')} detected on a transaction of INR {amount_rupees:,.2f}. "
                    f"Customer has {customer.successful_payments} prior successful payments with {score['recovery_probability']:.0%} "
                    f"model probability. Safe to schedule automatic retry."
                )
                priority = "HIGH" if score["risk_score"] >= 70 else "MEDIUM"

        elif payment.failure_reason == "card_expired":
            action = RecoveryAction.SUGGEST_ALTERNATE_PAYMENT_METHOD
            reason = (
                "Payment failed due to card expiration. Automatic retry would fail deterministically. "
                "Next best action is directing customer to update card details or select UPI / Netbanking."
            )
            priority = "MEDIUM"

        elif payment.failure_reason == "insufficient_funds":
            action = RecoveryAction.SEND_PAYMENT_LINK
            reason = (
                "Insufficient account balance detected. Blindly retrying would incur bank penalty fees. "
                "Sending an instant payment link with 24-hour validity allows customer to pay from an alternative bank account."
            )
            priority = "HIGH" if amount_rupees > 10000 else "MEDIUM"

        elif payment.checkout_abandoned:
            action = RecoveryAction.SEND_REMINDER
            reason = (
                "Customer abandoned the checkout session prior to payment capture. "
                "Sending a personalized, low-friction payment reminder via WhatsApp / SMS to recover intent."
            )
            priority = "MEDIUM"

        elif payment.failure_reason == "authentication_failure":
            action = RecoveryAction.SEND_REMINDER
            reason = (
                "3D Secure / OTP authentication failed or expired. "
                "Sending customer a quick reminder to re-authenticate with a fresh session."
            )
            priority = "MEDIUM"

        elif score["recovery_probability"] < 0.20:
            action = RecoveryAction.STOP_RECOVERY
            reason = (
                f"Overall recovery probability is critically low ({score['recovery_probability']:.0%}). "
                "Stopping automated interventions to protect brand reputation."
            )
            priority = "LOW"

        else:
            action = RecoveryAction.SEND_REMINDER
            reason = f"Unclassified failure ({payment.failure_reason}). Sending proactive customer assistance reminder."
            priority = "MEDIUM"

        # Incorporate customer memory snippet into reason if present
        if mem_text and "memory" not in reason.lower():
            reason += f" Context: {mem_text}"

        retry_mins = policy.retry_delay_minutes if action == RecoveryAction.RETRY_PAYMENT else None

        return RecoveryRecommendation(
            risk_score=score["risk_score"],
            recovery_probability=score["recovery_probability"],
            recommended_action=action,
            priority=priority,
            retry_after_minutes=retry_mins,
            reason=reason[:1500],
            confidence=0.82,
            provider_used="demo",
        )


class GeminiRecoveryProvider(BaseAIProvider):
    """Google Gemini AI Provider with structured JSON output and automatic Demo fallback."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", timeout_seconds: int = 8):
        self.api_key = api_key
        self.model_name = model_name or "gemini-1.5-flash"
        self.timeout_seconds = timeout_seconds
        self.fallback = DemoAIProvider()

    @property
    def name(self) -> str:
        return "gemini"

    def recommend(
        self,
        payment: Any,
        customer: Any,
        score: Dict[str, Any],
        policy: Any,
        memory: Optional[Any] = None,
    ) -> RecoveryRecommendation:
        if not self.api_key or not self.api_key.strip():
            logger.info("Gemini API key not configured; using DemoAIProvider.")
            return self.fallback.recommend(payment, customer, score, policy, memory)

        try:
            prompt = self._build_prompt(payment, customer, score, policy, memory)
            raw_response = self._call_gemini_api(prompt)
            data = json.loads(raw_response)

            # Enforce validation via Pydantic schema
            recommendation = RecoveryRecommendation.from_dict({**data, "provider_used": "gemini"})
            return recommendation

        except Exception as exc:
            logger.warning("Gemini AI recommendation failed (%s). Gracefully falling back to DemoAIProvider.", exc)
            fallback_rec = self.fallback.recommend(payment, customer, score, policy, memory)
            # Annotate that fallback took place
            fallback_rec.provider_used = "gemini-fallback-demo"
            fallback_rec.reason = f"[AI Fallback: {str(exc)[:60]}] " + fallback_rec.reason
            return fallback_rec

    def _build_prompt(
        self,
        payment: Any,
        customer: Any,
        score: Dict[str, Any],
        policy: Any,
        memory: Optional[Any] = None,
    ) -> str:
        amount_rupees = payment.amount_paise / 100
        mem_text = getattr(memory, "summary_text", "No prior intervention history.")

        return f"""You are RecoverAI, an autonomous fintech revenue recovery orchestrator for merchants on Razorpay.
Your goal is to choose the safest, most effective NEXT BEST RECOVERY ACTION for a failed payment.

PAYMENT DETAILS:
- Payment ID: {payment.external_id}
- Amount: INR {amount_rupees:,.2f}
- Payment Method: {payment.payment_method}
- Failure Reason: {payment.failure_reason}
- Retry Count to date: {payment.retry_count}
- Checkout Abandoned: {payment.checkout_abandoned}

CUSTOMER CONTEXT:
- Customer Name: {customer.name}
- Email: {customer.email}
- Lifetime Value: INR {customer.lifetime_value_paise / 100:,.2f}
- Past Successful Payments: {customer.successful_payments}
- Past Failed Payments: {customer.failed_payments}
- Prior Successful Recoveries: {customer.previous_recoveries}

CUSTOMER RECOVERY MEMORY:
{mem_text}

DETERMINISTIC PRE-SCORE:
- Calculated Risk Score: {score['risk_score']} / 100
- Estimated Recovery Probability: {score['recovery_probability']:.2f}

MERCHANT POLICY GUARDRAILS:
- Max Automatic Retries Allowed: {policy.max_automatic_retries}
- Configured Retry Delay: {policy.retry_delay_minutes} minutes
- High Value Threshold: INR {policy.high_value_threshold_paise / 100:,.2f}
- Escalation Threshold: INR {policy.escalation_threshold_paise / 100:,.2f}
- Repeated Failure Limit: {policy.repeated_failure_limit}
- Auto-Retry Enabled: {policy.auto_retry_enabled}

ALLOWED ACTIONS (Choose exactly ONE):
- RETRY_PAYMENT: For temporary bank/network timeouts on good customers where auto-retry is allowed.
- SEND_PAYMENT_LINK: For insufficient funds, expired links, or where retries previously failed.
- SEND_REMINDER: For checkout abandonment, OTP/auth expirations, or voluntary drops.
- SUGGEST_ALTERNATE_PAYMENT_METHOD: For expired cards, blocked cards, or chronic method-specific failure.
- ESCALATE_TO_MERCHANT: For transactions over escalation threshold or high risk requiring human approval.
- STOP_RECOVERY: When max retries exceeded, customer churned, or recovery is unviable.

Respond ONLY with a valid JSON object with these EXACT keys:
{{
  "risk_score": <integer 0-100>,
  "recovery_probability": <float 0.0-1.0>,
  "recommended_action": "<ONE OF THE 6 ALLOWED ACTIONS>",
  "priority": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "retry_after_minutes": <integer or null>,
  "reason": "<Detailed 2-3 sentence fintech explanation referencing customer history and memory>",
  "confidence": <float 0.0-1.0>
}}"""

    def _call_gemini_api(self, prompt: str) -> str:
        """Invokes the Google Gemini REST endpoint directly with standard library to avoid heavy dependencies."""
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": 500,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidate generated by Gemini API")
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise ValueError("Empty content returned by Gemini API")
            return parts[0].get("text", "").strip()
