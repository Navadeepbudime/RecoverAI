"""AI Recovery Agent for RecoverAI.

Orchestrates next-best-action decision making using either DemoAIProvider (default)
or GeminiRecoveryProvider (when GEMINI_API_KEY is configured). All recommendations
are validated using Pydantic schemas before reaching the policy engine.
"""

from typing import Any, Dict, Optional

from .schemas import RecoveryAction, RecoveryRecommendation
from .ai_providers import BaseAIProvider, DemoAIProvider, GeminiRecoveryProvider


def get_configured_ai_provider(config_dict: Optional[Dict[str, Any]] = None) -> BaseAIProvider:
    """Factory creating the appropriate AI provider based on configuration."""
    if config_dict:
        api_key = config_dict.get("GEMINI_API_KEY")
        model = config_dict.get("GEMINI_MODEL", "gemini-1.5-flash")
        if api_key and str(api_key).strip():
            return GeminiRecoveryProvider(api_key=str(api_key).strip(), model_name=model)
    return DemoAIProvider()


class RecoveryAgent:
    """Autonomous AI Agent that determines the Next Best Recovery Action."""

    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self.provider = provider or DemoAIProvider()

    def recommend(
        self,
        payment: Any,
        customer: Any,
        score: Dict[str, Any],
        policy: Any,
        memory: Optional[Any] = None,
    ) -> RecoveryRecommendation:
        """Evaluate context and synthesize the next-best-action recommendation."""
        return self.provider.recommend(
            payment=payment,
            customer=customer,
            score=score,
            policy=policy,
            memory=memory,
        )


__all__ = [
    "RecoveryAction",
    "RecoveryRecommendation",
    "RecoveryAgent",
    "DemoAIProvider",
    "GeminiRecoveryProvider",
    "get_configured_ai_provider",
]
