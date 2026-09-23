"""Devil's Advocate shadow evaluator — logs risk assessment without affecting trades."""

from __future__ import annotations

import json
import logging

from anthropic import Anthropic

logger = logging.getLogger(__name__)

DA_SYSTEM_PROMPT = """You are a risk analyst. The following trade has been approved by the primary analyst. Your job is NOT to argue against it — it is to identify the 3 most specific threats to this trade succeeding. Be precise about price levels and probabilities.

For each risk, provide:
1. A specific description citing exact price levels from the data
2. The price level that would confirm this risk is materializing
3. Your probability estimate (0-100%) that this risk invalidates the trade

Output ONLY valid JSON:
{
  "risks": [
    {
      "description": "string — specific risk with price levels",
      "confirming_level": 0.0,
      "probability_pct": 0,
      "category": "STRUCTURAL_RESISTANCE | MOMENTUM_EXHAUSTION | DISPLACEMENT_DOUBT | TIMING_CONFLICT | CONTEXT_MISMATCH"
    }
  ],
  "max_risk_pct": 0,
  "overall_risk_assessment": "string — 2 sentences max"
}"""


class DevilsAdvocate:
    """Shadow risk evaluator that runs alongside the primary pipeline.

    Produces a risk assessment for every CANDIDATE but never gates execution.
    Output is stored in the trade record for post-hoc analysis during WF-1.
    """

    def __init__(self, config: dict):
        ai_cfg = config.get("ai", {})
        da_cfg = config.get("devils_advocate", {})
        self.enabled = da_cfg.get("shadow_enabled", True)
        self._model = da_cfg.get("model", ai_cfg.get("primary_model", "claude-sonnet-4-6"))
        self._effort = da_cfg.get("effort", ai_cfg.get("primary_effort"))
        self._timeout = da_cfg.get("timeout_seconds",
                                   ai_cfg.get("api_timeout_seconds", 60 if self._effort == "max" else 30))
        self._client: Anthropic | None = None

    def _get_client(self) -> Anthropic:
        if self._client is None:
            self._client = Anthropic()
        return self._client

    def evaluate(self, mso_text: str, pa_reasoning: str, trade_params: dict) -> dict:
        """Run shadow DA evaluation. Returns risk assessment dict.

        Always non-blocking: returns ``{"error": ...}`` on any failure.
        """
        if not self.enabled:
            return {}

        try:
            user_message = (
                f"The primary analyst has approved this trade:\n"
                f"Direction: {trade_params.get('direction', 'unknown')}\n"
                f"Entry: {trade_params.get('entry_price', 0)}\n"
                f"Stop Loss: {trade_params.get('stop_loss', 0)}\n"
                f"TP1: {trade_params.get('take_profit_1', 0)}\n\n"
                f"Primary Analyst Reasoning:\n{pa_reasoning}\n\n"
                f"Market State Data:\n{mso_text[:8000]}"
            )

            create_kwargs = dict(
                model=self._model,
                max_tokens=1000,
                temperature=0,
                system=DA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                timeout=self._timeout,
            )
            if self._effort:
                create_kwargs["output_config"] = {"effort": self._effort}
            response = self._get_client().messages.create(**create_kwargs)

            text = response.content[0].text.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
            result = json.loads(text)

            if "risks" in result and result["risks"]:
                result["max_risk_pct"] = max(
                    r.get("probability_pct", 0) for r in result["risks"]
                )

            return result

        except Exception as e:
            logger.warning("Shadow DA evaluation failed (non-blocking): %s", e)
            return {"error": str(e)}
