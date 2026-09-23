"""H1 autocorrelation risk sizing.

The edge-mechanism KB identifies H1 return autocorrelation trending toward zero
as the practical early-warning signature for momentum/OB-continuation decay.
This module converts that into a runtime risk reducer: when recent H1 returns
show non-positive autocorrelation, position risk is multiplied down before
correlation, side-aware, and vNext risk sizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AutocorrelationRiskDecision:
    enabled: bool
    apply_to_execution: bool
    applied: bool
    reason: str
    before_risk_pct: float
    after_risk_pct: float
    multiplier: float
    autocorrelation: float | None
    window: int
    returns_count: int
    source_artifact_path: str = ".context/01_knowledge_base/kb_edge_mechanisms_and_risks.md"

    def to_record(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "reason": self.reason,
            "before_risk_pct": self.before_risk_pct,
            "after_risk_pct": self.after_risk_pct,
            "multiplier": self.multiplier,
            "autocorrelation": self.autocorrelation,
            "window": self.window,
            "returns_count": self.returns_count,
            "source_artifact_path": self.source_artifact_path,
        }


def _cfg(config: dict[str, Any] | None) -> dict[str, Any]:
    risk = (config or {}).get("risk", {}) or {}
    return risk.get("autocorrelation_sizing", {}) or {}


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def h1_closes_from_raw_data(raw_data: dict[str, Any] | None) -> list[float]:
    """Extract H1 close prices from the runtime raw_data candle contract."""
    if not isinstance(raw_data, dict):
        return []
    candles_block = raw_data.get("candles") or {}
    h1_candles = candles_block.get("H1") if isinstance(candles_block, dict) else None
    if not isinstance(h1_candles, Iterable):
        return []
    closes: list[float] = []
    for candle in h1_candles:
        if not isinstance(candle, dict):
            continue
        close = _as_float(candle.get("close"))
        if close is not None and close > 0:
            closes.append(close)
    return closes


def rolling_return_autocorrelation(closes: list[float], *, window: int = 20) -> float | None:
    """Compute lag-1 autocorrelation of the most recent H1 percentage returns."""
    if window < 2 or len(closes) < window + 1:
        return None
    returns: list[float] = []
    for previous, current in zip(closes[-(window + 1):], closes[-window:]):
        if previous <= 0:
            return None
        returns.append((current - previous) / previous)
    x = returns[:-1]
    y = returns[1:]
    if len(x) < 2:
        return None
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denom_x = sum((a - mean_x) ** 2 for a in x)
    denom_y = sum((b - mean_y) ** 2 for b in y)
    if denom_x <= 0 or denom_y <= 0:
        return None
    return numerator / ((denom_x * denom_y) ** 0.5)


def evaluate_autocorrelation_risk(
    *,
    current_risk_pct: float,
    raw_data: dict[str, Any] | None,
    config: dict[str, Any] | None,
) -> AutocorrelationRiskDecision:
    cfg = _cfg(config)
    enabled = bool(cfg.get("enabled", False))
    apply_to_execution = bool(cfg.get("apply_to_execution", enabled))
    window = int(cfg.get("window", 20) or 20)
    threshold = float(cfg.get("min_autocorrelation", 0.0) or 0.0)
    multiplier = float(cfg.get("decay_risk_multiplier", 0.5) or 0.5)
    multiplier = max(0.0, min(1.0, multiplier))
    closes = h1_closes_from_raw_data(raw_data)
    autocorr = rolling_return_autocorrelation(closes, window=window)
    base = float(current_risk_pct)

    if not enabled:
        return AutocorrelationRiskDecision(
            enabled=False,
            apply_to_execution=False,
            applied=False,
            reason="autocorrelation_sizing_disabled",
            before_risk_pct=base,
            after_risk_pct=base,
            multiplier=1.0,
            autocorrelation=autocorr,
            window=window,
            returns_count=max(0, min(len(closes) - 1, window)),
        )
    if autocorr is None:
        return AutocorrelationRiskDecision(
            enabled=True,
            apply_to_execution=apply_to_execution,
            applied=False,
            reason="autocorrelation_sizing_insufficient_h1_returns",
            before_risk_pct=base,
            after_risk_pct=base,
            multiplier=1.0,
            autocorrelation=None,
            window=window,
            returns_count=max(0, min(len(closes) - 1, window)),
        )
    if autocorr <= threshold:
        after = base * multiplier if apply_to_execution else base
        return AutocorrelationRiskDecision(
            enabled=True,
            apply_to_execution=apply_to_execution,
            applied=apply_to_execution,
            reason="h1_autocorrelation_decay_risk_reduction",
            before_risk_pct=base,
            after_risk_pct=after,
            multiplier=multiplier if apply_to_execution else 1.0,
            autocorrelation=autocorr,
            window=window,
            returns_count=window,
        )
    return AutocorrelationRiskDecision(
        enabled=True,
        apply_to_execution=apply_to_execution,
        applied=False,
        reason="h1_autocorrelation_positive_no_adjustment",
        before_risk_pct=base,
        after_risk_pct=base,
        multiplier=1.0,
        autocorrelation=autocorr,
        window=window,
        returns_count=window,
    )


def attach_autocorrelation_risk_to_record(
    record: dict[str, Any] | None,
    decision: AutocorrelationRiskDecision,
) -> None:
    if record is None:
        return
    record.setdefault("decision_pipeline", {})["autocorrelation_risk_sizing"] = (
        decision.to_record()
    )
    inst = record.setdefault("instrumentation", {})
    inst["autocorrelation_risk_applied"] = decision.applied
    inst["autocorrelation_risk_reason"] = decision.reason
    inst["autocorrelation_h1"] = decision.autocorrelation
    inst["autocorrelation_risk_multiplier"] = decision.multiplier


__all__ = [
    "AutocorrelationRiskDecision",
    "attach_autocorrelation_risk_to_record",
    "evaluate_autocorrelation_risk",
    "h1_closes_from_raw_data",
    "rolling_return_autocorrelation",
]
