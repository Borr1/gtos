"""Side-aware position sizing pure helpers (no I/O).

Validated by H38 + side_aware_a sweep (commit 124de56). 4/5 ship gates passed:
  - Legacy fixed rule: LONG=0.5x risk multiplier, SHORT=1.0x.
  - Composite (P(pass) x P(NOT-blow)): sa_a 0.536 vs baseline 0.005 (100x)
  - H2-2026 OOS: sa_a $17,328 vs baseline $13,870 (24% better)
  - DD 14.9% vs baseline 21.8% (Pareto-dominant on risk-adjusted)
  - Bootstrap CI95 lower -$3,662 (within FN's 8% buffer; ONE failed gate)

Runtime now supports contextual mode. In that mode both LONG and SHORT default
to full base risk when evidence is neutral. Risk is reduced only when
symbol/session/framework/regime, Asian range, H1 follow-through, vNext
R/proxy/stress/effective-N, no-fill/fillability, and target/stop path evidence
are weak or adverse. The fixed multipliers remain only as an explicit
``mode: legacy`` fallback.

The flag is read each call so that orchestrator code never imports a stale
module-level value. Optional READY8 rule artifacts are loaded by path and
cached; sizing decisions themselves keep no mutable state.

Usage:

    from src.components import side_aware_sizing

    if side_aware_sizing.is_enabled(config):
        decision = side_aware_sizing.evaluate_contextual_side_multiplier(
            base_risk_pct=effective_risk_pct,
            direction=trade_direction,  # 'LONG' or 'SHORT'
            config=config,
            context=runtime_context,
        )
        effective_risk_pct = decision.after_risk_pct

The SPRT auto-revert watcher (``side_aware_sprt_watcher.SideAwareSprtWatcher``)
sits at a higher layer in the orchestrator: callers must check
``watcher.is_disabled()`` before applying side-risk sizing.

Config schema (under ``risk.side_aware_sizing``):

    risk:
      side_aware_sizing:
        enabled: true
        mode: contextual
        contextual_default_multiplier: 1.0
        contextual_weak_multiplier: 0.5
        contextual_adverse_multiplier: 0.25
        contextual_full_risk_multiplier: 1.0
        long_multiplier: 0.5        # legacy fallback only
        short_multiplier: 1.0       # legacy fallback only
        sprt_window_size: 20        # rolling window of LONG outcomes
        sprt_wr_threshold: 0.50     # auto-disable if WR < this in window
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping


# Default constants (sourced from H38 + side_aware_a validation).
DEFAULT_ENABLED: bool = False
DEFAULT_LONG_MULTIPLIER: float = 0.5
DEFAULT_SHORT_MULTIPLIER: float = 1.0


@dataclass(frozen=True)
class ContextualSideRiskDecision:
    """Evidence-backed side risk sizing decision for the current candidate."""

    enabled: bool
    apply_to_execution: bool
    applied: bool
    mode: str
    direction: str
    before_risk_pct: float
    after_risk_pct: float
    multiplier: float
    would_multiplier: float
    score: float
    reason: str
    context: dict[str, Any] = field(default_factory=dict)
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    factors: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_record(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "mode": self.mode,
            "direction": self.direction,
            "before_risk_pct": self.before_risk_pct,
            "after_risk_pct": self.after_risk_pct,
            "multiplier": self.multiplier,
            "would_multiplier": self.would_multiplier,
            "score": self.score,
            "reason": self.reason,
            "context": dict(self.context),
            "evidence_summary": dict(self.evidence_summary),
            "factors": [dict(item) for item in self.factors],
        }


def _section(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    """Return the ``risk.side_aware_sizing`` block (empty mapping if missing)."""
    if not isinstance(config, Mapping):
        return {}
    risk = config.get("risk", {})
    if not isinstance(risk, Mapping):
        return {}
    block = risk.get("side_aware_sizing", {})
    if not isinstance(block, Mapping):
        return {}
    return block


def is_enabled(config: Mapping[str, Any] | None) -> bool:
    """Return True iff ``risk.side_aware_sizing.enabled`` is truthy.

    Default is False so that any malformed/missing config preserves baseline
    sizing behavior (fail-safe).
    """
    return bool(_section(config).get("enabled", DEFAULT_ENABLED))


def get_long_multiplier(config: Mapping[str, Any] | None) -> float:
    """Return ``risk.side_aware_sizing.long_multiplier`` (default 0.5)."""
    val = _section(config).get("long_multiplier", DEFAULT_LONG_MULTIPLIER)
    try:
        return float(val)
    except (TypeError, ValueError):
        return DEFAULT_LONG_MULTIPLIER


def get_short_multiplier(config: Mapping[str, Any] | None) -> float:
    """Return ``risk.side_aware_sizing.short_multiplier`` (default 1.0)."""
    val = _section(config).get("short_multiplier", DEFAULT_SHORT_MULTIPLIER)
    try:
        return float(val)
    except (TypeError, ValueError):
        return DEFAULT_SHORT_MULTIPLIER


def apply_side_multiplier(
    base_risk_pct: float,
    direction: str,
    config: Mapping[str, Any] | None,
) -> float:
    """Apply the side-specific multiplier to ``base_risk_pct``.

    If side-aware sizing is disabled, returns ``base_risk_pct`` unchanged.

    Args:
        base_risk_pct: pre-multiplier risk percentage. Pass through unchanged
            when the flag is OFF.
        direction: ``'LONG'`` or ``'SHORT'`` (case-insensitive). Anything else
            is treated as a no-op (returns base unchanged) — fail-safe for
            malformed inputs.
        config: full agent config dict (the function reads
            ``config['risk']['side_aware_sizing']`` keys).

    Returns:
        The multiplier-adjusted risk percentage. Pure function — no I/O.
    """
    if not is_enabled(config):
        return base_risk_pct
    side = (direction or "").upper()
    if side == "LONG":
        return base_risk_pct * get_long_multiplier(config)
    if side == "SHORT":
        return base_risk_pct * get_short_multiplier(config)
    # Unknown/empty direction — fail-safe pass-through.
    return base_risk_pct


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def _context_value(context: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = context.get(key)
        if value not in (None, ""):
            return value
    return None


def _decision_object_context(context: Mapping[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    decision_obj = context.get("vnext_decision")
    if hasattr(decision_obj, "decision"):
        label = str(getattr(decision_obj, "decision", "") or "")
        evidence = getattr(decision_obj, "evidence", {}) or {}
        event = getattr(decision_obj, "event", {}) or {}
        return (
            label,
            dict(evidence) if isinstance(evidence, Mapping) else {},
            dict(event) if isinstance(event, Mapping) else {},
        )
    label = str(context.get("vnext_decision") or context.get("vnext_label") or "")
    evidence = _mapping(context.get("vnext_evidence"))
    event = _mapping(context.get("vnext_event"))
    return label, dict(evidence), dict(event)


def _configured_scores(
    block: Mapping[str, Any],
    key: str,
    defaults: Mapping[str, float],
) -> dict[str, float]:
    configured = _mapping(block.get(key))
    result = {_normalized(name): float(value) for name, value in defaults.items()}
    for name, value in configured.items():
        result[_normalized(name)] = _float_value(value, result.get(_normalized(name), 0.0))
    return result


def _metric_sum(evidence: Mapping[str, Any], metric: str) -> float | None:
    metrics = _mapping(evidence.get("metrics"))
    block = _mapping(metrics.get(metric))
    if "sum" in block:
        try:
            return float(block.get("sum"))
        except (TypeError, ValueError):
            return None
    if metric in evidence:
        try:
            return float(evidence.get(metric))
        except (TypeError, ValueError):
            return None
    return None


def _dict_counts_total(counts: Mapping[str, Any], tokens: tuple[str, ...]) -> int:
    total = 0
    for name, raw_count in counts.items():
        label = _normalized(name)
        if not any(token in label for token in tokens):
            continue
        try:
            total += int(raw_count)
        except (TypeError, ValueError):
            continue
    return total


def _decision_counts_for_tokens(
    dimension_counts: Mapping[str, Any],
    tokens: tuple[str, ...],
) -> tuple[int, int]:
    follow = 0
    avoid = 0
    for name, raw_counts in dimension_counts.items():
        label = _normalized(name)
        if not any(token in label for token in tokens):
            continue
        counts = _mapping(raw_counts)
        try:
            follow += int(counts.get("FOLLOW", 0) or 0)
            avoid += int(counts.get("AVOID", 0) or 0)
        except (TypeError, ValueError):
            continue
    return follow, avoid


def _add_factor(
    factors: list[dict[str, Any]],
    score: float,
    name: str,
    value: Any,
    detail: str = "",
) -> None:
    factors.append({
        "factor": name,
        "score": round(float(score), 6),
        "value": value,
        "detail": detail,
    })


def _score_context_maps(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> float:
    total = 0.0
    config_maps = {
        "side": "contextual_side_scores",
        "symbol": "contextual_symbol_scores",
        "symbol_family": "contextual_symbol_family_scores",
        "session": "contextual_session_scores",
        "framework": "contextual_framework_scores",
        "route_family": "contextual_route_family_scores",
        "regime": "contextual_regime_scores",
        "market_timeframe": "contextual_market_timeframe_scores",
    }
    for context_key, config_key in config_maps.items():
        value = _context_value(context, context_key)
        if not value:
            continue
        scores = _configured_scores(block, config_key, {})
        score = scores.get(_normalized(value))
        if score is None:
            continue
        total += score
        _add_factor(factors, score, config_key, value, "configured_context_score")
    return total


def _ready8_rule_matches(rule: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    field_map = {
        "card_id": "ready8_card_id",
        "horizon_m15_bars": "ready8_horizon_m15_bars",
        "target_family_id": "ready8_target_family_id",
        "partition_assignment": "ready8_partition_assignment",
        "descriptor_name": "ready8_descriptor_name",
        "descriptor_value": "ready8_descriptor_value",
        "wait_gap_bucket": "ready8_wait_gap_bucket",
        "prior_24h_count_bucket": "ready8_prior_24h_count_bucket",
        "source_window": "ready8_source_window",
        "source_segment_sha256": "ready8_source_segment_sha256",
        "canonical_economic_group": "ready8_canonical_economic_group",
        "symbol": "symbol",
        "symbol_family": "symbol_family",
        "side": "side",
        "session": "session",
        "framework": "framework",
        "route_family": "route_family",
    }
    for rule_key, context_key in field_map.items():
        expected = rule.get(rule_key)
        if expected in (None, ""):
            continue
        actual = _context_value(context, context_key)
        if actual in (None, ""):
            return False
        if _normalized(expected) != _normalized(actual):
            return False
    return True


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _repo_relative_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return Path.cwd() / path


@lru_cache(maxsize=32)
def _load_ready8_rule_artifact(path_text: str) -> tuple[dict[str, Any], ...]:
    path = _repo_relative_path(path_text)
    if not path.exists():
        return ()
    try:
        if path.suffix.lower() == ".jsonl":
            rows = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                rows = payload.get("rules") or payload.get("rows") or []
            elif isinstance(payload, list):
                rows = payload
            else:
                rows = []
    except (OSError, json.JSONDecodeError):
        return ()
    return tuple(dict(row) for row in rows if isinstance(row, Mapping))


def _configured_ready8_rules(block: Mapping[str, Any]) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    raw_rules = block.get("contextual_ready8_rules")
    if isinstance(raw_rules, list):
        rules.extend(dict(rule) for rule in raw_rules if isinstance(rule, Mapping))
    for path_text in _as_list(block.get("contextual_ready8_rule_artifact_paths")):
        if not path_text:
            continue
        rules.extend(_load_ready8_rule_artifact(str(path_text)))
    return rules


def _configured_ready8_adjustment_rules(block: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not bool(block.get("contextual_ready8_adjustment_enabled", True)):
        return []
    rules: list[dict[str, Any]] = []
    raw_rules = block.get("contextual_ready8_adjustment_rules")
    if isinstance(raw_rules, list):
        rules.extend(dict(rule) for rule in raw_rules if isinstance(rule, Mapping))
    for path_text in _as_list(block.get("contextual_ready8_adjustment_rule_artifact_paths")):
        if not path_text:
            continue
        rules.extend(_load_ready8_rule_artifact(str(path_text)))
    return rules


def _apply_ready8_adjustments(
    *,
    score: float,
    adjustment_rules: list[dict[str, Any]],
    context: Mapping[str, Any],
) -> tuple[float, list[dict[str, Any]]]:
    adjusted = float(score)
    matched: list[dict[str, Any]] = []
    for raw_rule in adjustment_rules:
        rule = _mapping(raw_rule)
        if not rule or not _ready8_rule_matches(rule, context):
            continue
        if score > 0:
            multiplier = _float_value(
                rule.get("positive_score_multiplier"),
                _float_value(rule.get("score_multiplier"), 1.0),
            )
        elif score < 0:
            multiplier = _float_value(
                rule.get("negative_score_multiplier"),
                _float_value(rule.get("score_multiplier"), 1.0),
            )
        else:
            multiplier = _float_value(rule.get("score_multiplier"), 1.0)
        before = adjusted
        adjusted *= multiplier
        payload = {
            "ready8_adjustment_rule_id": rule.get("ready8_adjustment_rule_id"),
            "card_id": rule.get("card_id"),
            "horizon_m15_bars": rule.get("horizon_m15_bars"),
            "target_family_id": rule.get("target_family_id"),
            "partition_assignment": rule.get("partition_assignment"),
            "descriptor_name": rule.get("descriptor_name"),
            "descriptor_value": rule.get("descriptor_value"),
            "score_multiplier": multiplier,
            "score_before": round(before, 6),
            "score_after": round(adjusted, 6),
            "source_row_count": rule.get("source_row_count"),
            "adjustment_action_counts": rule.get("adjustment_action_counts"),
            "reason_counts": rule.get("reason_counts"),
            "source_paths": rule.get("source_paths"),
        }
        matched.append({key: value for key, value in payload.items() if value not in (None, "", [], {})})
    return adjusted, matched


def _score_ready8_rules(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, list[dict[str, Any]], list[dict[str, Any]]]:
    if not bool(block.get("contextual_ready8_enabled", True)):
        return 0.0, [], []
    raw_rules = _configured_ready8_rules(block)
    if not raw_rules:
        return 0.0, [], []
    adjustment_rules = _configured_ready8_adjustment_rules(block)
    total = 0.0
    matched: list[dict[str, Any]] = []
    matched_adjustments: list[dict[str, Any]] = []
    for raw_rule in raw_rules:
        rule = _mapping(raw_rule)
        if not rule or not _ready8_rule_matches(rule, context):
            continue
        raw_score = _float_value(rule.get("score"), 0.0)
        score, adjustments = _apply_ready8_adjustments(
            score=raw_score,
            adjustment_rules=adjustment_rules,
            context=context,
        )
        total += score
        payload = {
            "card_id": rule.get("card_id"),
            "horizon_m15_bars": rule.get("horizon_m15_bars"),
            "target_family_id": rule.get("target_family_id"),
            "partition_assignment": rule.get("partition_assignment"),
            "symbol_family": rule.get("symbol_family"),
            "symbol": rule.get("symbol"),
            "session": rule.get("session"),
            "source_row_id": rule.get("source_row_id"),
            "branch_role": rule.get("branch_role"),
            "score": round(score, 6),
            "raw_score": round(raw_score, 6) if score != raw_score else None,
            "evidence_delta": rule.get("evidence_delta"),
            "source_path": rule.get("source_path"),
            "source_line_no": rule.get("source_line_no"),
            "reason": rule.get("reason"),
            "ready8_adjustments": adjustments,
        }
        matched.append({key: value for key, value in payload.items() if value not in (None, "")})
        matched_adjustments.extend(adjustments)
        detail = _normalized(rule.get("reason") or "ready8_context_rule")
        _add_factor(
            factors,
            score,
            "ready8_context",
            {
                "card_id": rule.get("card_id"),
                "horizon_m15_bars": rule.get("horizon_m15_bars"),
                "target_family_id": rule.get("target_family_id"),
                "symbol_family": rule.get("symbol_family"),
                "symbol": rule.get("symbol"),
                "session": rule.get("session"),
                "source_row_id": rule.get("source_row_id"),
            },
            detail,
        )
        if score != raw_score:
            _add_factor(
                factors,
                score - raw_score,
                "ready8_context_adjustment",
                {
                    "card_id": rule.get("card_id"),
                    "horizon_m15_bars": rule.get("horizon_m15_bars"),
                    "target_family_id": rule.get("target_family_id"),
                    "partition_assignment": rule.get("partition_assignment"),
                },
                "ready8_failure_context_adjustment",
            )
    return total, matched, matched_adjustments


def _score_validation_leash_rules(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, list[dict[str, Any]]]:
    if not bool(block.get("contextual_validation_leash_enabled", True)):
        return 0.0, []
    raw_rules = block.get("contextual_validation_leash_rules")
    if not isinstance(raw_rules, list):
        return 0.0, []
    symbol = _normalized(_context_value(context, "symbol"))
    source_symbol = _normalized(_context_value(context, "source_symbol"))
    symbol_family = _normalized(_context_value(context, "symbol_family"))
    scoped_fields = {
        "side": _normalized(_context_value(context, "side", "direction")),
        "session": _normalized(_context_value(context, "session", "kill_zone", "route_session")),
        "framework": _normalized(_context_value(context, "framework")),
        "route_family": _normalized(_context_value(context, "route_family")),
        "regime": _normalized(_context_value(context, "regime")),
        "market_timeframe": _normalized(
            _context_value(context, "market_timeframe", "timeframe", "entry_timeframe")
        ),
    }
    total = 0.0
    matched: list[dict[str, Any]] = []
    for raw_rule in raw_rules:
        rule = _mapping(raw_rule)
        rule_symbol = _normalized(rule.get("symbol"))
        rule_source_symbol = _normalized(rule.get("source_symbol"))
        rule_family = _normalized(rule.get("symbol_family"))
        if rule_symbol and rule_symbol not in {symbol, source_symbol}:
            continue
        if rule_source_symbol and rule_source_symbol != source_symbol:
            continue
        if rule_family and rule_family != symbol_family:
            continue
        if any(
            _normalized(rule.get(field)) and _normalized(rule.get(field)) != actual
            for field, actual in scoped_fields.items()
        ):
            continue
        score = _float_value(rule.get("score"), 0.0)
        if score == 0.0:
            continue
        payload = {
            "symbol": rule.get("symbol"),
            "source_symbol": rule.get("source_symbol"),
            "symbol_family": rule.get("symbol_family"),
            "side": rule.get("side"),
            "session": rule.get("session"),
            "framework": rule.get("framework"),
            "route_family": rule.get("route_family"),
            "regime": rule.get("regime"),
            "market_timeframe": rule.get("market_timeframe"),
            "score": round(score, 6),
            "source_path": rule.get("source_path"),
            "source_line_no": rule.get("source_line_no"),
            "reason": rule.get("reason"),
        }
        payload = {key: value for key, value in payload.items() if value not in (None, "")}
        matched.append(payload)
        total += score
        _add_factor(
            factors,
            score,
            "validation_leash",
            payload,
            str(rule.get("reason") or "validation_framework_instrument_leash"),
        )
    return total, matched


def _rule_value_matches_context(rule_value: Any, actual: str) -> bool:
    if rule_value in (None, ""):
        return True
    if isinstance(rule_value, (list, tuple, set)):
        return any(_normalized(value) == actual for value in rule_value)
    return _normalized(rule_value) == actual


def _score_monthly_decay_rules(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, list[dict[str, Any]]]:
    """Score S1 monthly-decay alerts as contextual risk reducers."""
    if not bool(block.get("contextual_monthly_decay_enabled", True)):
        return 0.0, []
    raw_rules = block.get("contextual_monthly_decay_rules")
    if not isinstance(raw_rules, list):
        return 0.0, []

    symbol = _normalized(_context_value(context, "symbol"))
    source_symbol = _normalized(_context_value(context, "source_symbol"))
    symbol_family = _normalized(_context_value(context, "symbol_family"))
    scoped_fields = {
        "side": _normalized(_context_value(context, "side", "direction")),
        "session": _normalized(_context_value(context, "session", "kill_zone", "route_session")),
        "framework": _normalized(_context_value(context, "framework")),
        "route_family": _normalized(_context_value(context, "route_family")),
        "regime": _normalized(_context_value(context, "regime")),
        "market_timeframe": _normalized(
            _context_value(context, "market_timeframe", "timeframe", "entry_timeframe")
        ),
        "detector_version": _normalized(
            _context_value(context, "detector_version", "detector_version_at_eval")
        ),
    }
    total = 0.0
    matched: list[dict[str, Any]] = []
    for raw_rule in raw_rules:
        rule = _mapping(raw_rule)
        rule_symbol = _normalized(rule.get("symbol"))
        rule_source_symbol = _normalized(rule.get("source_symbol"))
        rule_family = _normalized(rule.get("symbol_family"))
        if rule_symbol and rule_symbol not in {symbol, source_symbol}:
            continue
        if rule_source_symbol and rule_source_symbol != source_symbol:
            continue
        if rule_family and rule_family != symbol_family:
            continue
        scoped_mismatch = False
        for field, actual in scoped_fields.items():
            rule_value = rule.get(
                field if field != "detector_version" else "detector_versions",
                rule.get(field),
            )
            if rule_value in (None, ""):
                continue
            if not actual or not _rule_value_matches_context(rule_value, actual):
                scoped_mismatch = True
                break
        if scoped_mismatch:
            continue
        score = _float_value(rule.get("score"), 0.0)
        if score == 0.0:
            continue
        payload = {
            "symbol": rule.get("symbol"),
            "source_symbol": rule.get("source_symbol"),
            "symbol_family": rule.get("symbol_family"),
            "side": rule.get("side"),
            "session": rule.get("session"),
            "framework": rule.get("framework"),
            "route_family": rule.get("route_family"),
            "regime": rule.get("regime"),
            "market_timeframe": rule.get("market_timeframe"),
            "detector_versions": rule.get("detector_versions"),
            "alert_kinds": rule.get("alert_kinds"),
            "current_wr_pct": rule.get("current_wr_pct"),
            "baseline_wr_pct": rule.get("baseline_wr_pct"),
            "wr_drop_pp": rule.get("wr_drop_pp"),
            "current_exp_r": rule.get("current_exp_r"),
            "baseline_exp_r": rule.get("baseline_exp_r"),
            "exp_drop_r": rule.get("exp_drop_r"),
            "score": round(score, 6),
            "source_path": rule.get("source_path"),
            "source_line_no": rule.get("source_line_no"),
            "reason": rule.get("reason"),
        }
        payload = {key: value for key, value in payload.items() if value not in (None, "")}
        matched.append(payload)
        total += score
        _add_factor(
            factors,
            score,
            "monthly_decay_alert",
            payload,
            str(rule.get("reason") or "monthly_decay_runtime_risk_reducer"),
        )
    return total, matched


def _normalized_config_set(raw_values: Any, defaults: tuple[str, ...]) -> set[str]:
    if isinstance(raw_values, (list, tuple, set)):
        values = raw_values
    elif raw_values in (None, ""):
        values = defaults
    else:
        values = (raw_values,)
    result = {_normalized(value).upper() for value in values if value not in (None, "")}
    return result or {_normalized(value).upper() for value in defaults}


def _context_symbol_in_families(context: Mapping[str, Any], families: set[str]) -> bool:
    if not families:
        return True
    symbol_family = _normalized(_context_value(context, "symbol_family")).upper()
    symbol = _normalized(_context_value(context, "symbol", "source_symbol")).upper()
    if symbol_family and symbol_family in families:
        return True
    if symbol.startswith(("XAU", "GC")) and "XAUUSD_GC_FAMILY" in families:
        return True
    if symbol.startswith(("XAG", "SI")) and "XAGUSD_SILVER_FAMILY" in families:
        return True
    return False


def _score_news_event_risk(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_news_event_enabled", True)):
        return 0.0, {}
    minutes_raw = _context_value(
        context,
        "news_minutes_to_event",
        "high_impact_news_minutes_to_event",
    )
    try:
        minutes = None if minutes_raw is None else float(minutes_raw)
    except (TypeError, ValueError):
        minutes = None
    if minutes is None:
        return 0.0, {}

    impact = _normalized(_context_value(context, "news_impact", "high_impact_news_impact")).upper()
    currency = _normalized(_context_value(context, "news_currency", "high_impact_news_currency")).upper()
    allowed_impacts = _normalized_config_set(
        block.get("contextual_news_impact_levels"),
        ("HIGH",),
    )
    allowed_currencies = _normalized_config_set(
        block.get("contextual_news_currencies"),
        ("USD", "GBP"),
    )
    if not impact or impact not in allowed_impacts:
        return 0.0, {}
    if not currency or currency not in allowed_currencies:
        return 0.0, {}

    hard_pre = _float_value(block.get("contextual_news_hard_pre_minutes"), 15.0)
    hard_post = _float_value(block.get("contextual_news_hard_post_minutes"), 2.0)
    reduce_pre = _float_value(block.get("contextual_news_reduce_pre_minutes"), 60.0)
    reduce_post = _float_value(block.get("contextual_news_reduce_post_minutes"), 10.0)
    if -hard_post <= minutes <= hard_pre:
        factor_score = _float_value(block.get("contextual_news_hard_window_score"), -3.0)
        detail = "inside_high_impact_news_hard_window"
    elif -reduce_post <= minutes <= reduce_pre:
        factor_score = _float_value(block.get("contextual_news_reduce_window_score"), -1.0)
        detail = "near_high_impact_news_reduce_window"
    else:
        return 0.0, {}

    event_summary = {
        "minutes_to_event": minutes,
        "event": _context_value(context, "news_event_name", "high_impact_news_event"),
        "currency": currency or None,
        "impact": impact or None,
        "source": _context_value(context, "news_source"),
        "time_utc": _context_value(context, "news_event_time_utc", "high_impact_news_time_utc"),
    }
    event_summary = {key: value for key, value in event_summary.items() if value not in (None, "")}
    _add_factor(factors, factor_score, "news_event_risk", event_summary, detail)
    return factor_score, event_summary


def _score_volatility_regime(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_volatility_regime_enabled", True)):
        return 0.0, {}
    families = _normalized_config_set(
        block.get("contextual_gvz_symbol_families"),
        ("XAUUSD_GC_FAMILY", "XAGUSD_SILVER_FAMILY"),
    )
    if not _context_symbol_in_families(context, families):
        return 0.0, {}
    gvz_raw = _context_value(
        context,
        "volatility_gvz",
        "gvz",
        "gvz_close",
        "fred__GVZCLS__value",
        "GVZCLS",
    )
    try:
        gvz = None if gvz_raw is None else float(gvz_raw)
    except (TypeError, ValueError):
        gvz = None
    if gvz is None:
        return 0.0, {}

    high_threshold = _float_value(block.get("contextual_gvz_high_threshold"), 40.0)
    elevated_threshold = _float_value(block.get("contextual_gvz_elevated_threshold"), 30.0)
    if gvz >= high_threshold:
        factor_score = _float_value(block.get("contextual_gvz_high_score"), -1.0)
        detail = "gvz_high_headline_regime"
    elif gvz >= elevated_threshold:
        factor_score = _float_value(block.get("contextual_gvz_elevated_score"), -0.5)
        detail = "gvz_elevated_regime"
    else:
        return 0.0, {"gvz": gvz}

    summary = {
        "gvz": gvz,
        "threshold": high_threshold if gvz >= high_threshold else elevated_threshold,
        "regime": detail,
        "source": _context_value(context, "volatility_source", "gvz_source"),
        "symbol_family": _context_value(context, "symbol_family"),
    }
    summary = {key: value for key, value in summary.items() if value not in (None, "")}
    _add_factor(factors, factor_score, "volatility_regime", summary, detail)
    return factor_score, summary


def _parse_hhmm_minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        hour_text, minute_text = text.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text[:2])
    except (TypeError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def _parse_utc_clock_minutes(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    parsed_time = _parse_hhmm_minutes(text)
    if parsed_time is not None:
        return parsed_time
    try:
        iso_text = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_text)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    return dt.hour * 60 + dt.minute


def _score_session_phase(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_session_phase_enabled", True)):
        return 0.0, {}
    candle_minutes = _parse_utc_clock_minutes(
        _context_value(
            context,
            "candle_time_utc",
            "timestamp_utc",
            "time_utc",
        )
    )
    start_minutes = _parse_hhmm_minutes(
        _context_value(context, "session_start_utc", "kill_zone_start_utc")
    )
    if candle_minutes is None or start_minutes is None:
        return 0.0, {}
    elapsed = candle_minutes - start_minutes
    if elapsed < 0:
        elapsed += 24 * 60
    first_window = _float_value(block.get("contextual_session_first_window_minutes"), 90.0)
    late_after = _float_value(block.get("contextual_session_late_after_minutes"), 90.0)
    summary = {
        "session": _context_value(context, "session", "kill_zone"),
        "candle_time_utc": _context_value(context, "candle_time_utc", "timestamp_utc", "time_utc"),
        "session_start_utc": _context_value(context, "session_start_utc", "kill_zone_start_utc"),
        "minutes_since_session_start": elapsed,
        "first_window_minutes": first_window,
        "late_after_minutes": late_after,
    }
    if elapsed <= first_window:
        factor_score = _float_value(block.get("contextual_session_first_window_score"), 0.25)
        summary["phase"] = "first_window"
        _add_factor(
            factors,
            factor_score,
            "session_phase",
            summary,
            "first_90_minutes_quality_window",
        )
        return factor_score, summary
    if elapsed > late_after:
        factor_score = _float_value(block.get("contextual_session_late_score"), -0.5)
        summary["phase"] = "late_session"
        _add_factor(
            factors,
            factor_score,
            "session_phase",
            summary,
            "post_90_minute_decision_fatigue_and_vol_decay",
        )
        return factor_score, summary
    summary["phase"] = "middle_window"
    return 0.0, summary


def _score_align_context(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_align_score_enabled", True)):
        return 0.0, {}
    raw_align = _context_value(
        context,
        "align_score",
        "alignment_score",
        "tf_alignment_score",
        "timeframe_alignment_score",
    )
    try:
        align_score = None if raw_align is None else float(raw_align)
    except (TypeError, ValueError):
        return 0.0, {}
    if align_score is None:
        return 0.0, {}

    min_align = _float_value(block.get("contextual_align_score_min"), 2.0)
    summary = {
        "align_score": align_score,
        "min_support_score": min_align,
        "policy": "positive_modifier_not_gate",
    }
    if align_score >= min_align:
        factor_score = _float_value(block.get("contextual_align_support_score"), 0.5)
        _add_factor(
            factors,
            factor_score,
            "align_context",
            summary,
            "align_score_positive_modifier_not_gate",
        )
        return factor_score, summary
    return 0.0, summary


def _truthy_context_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "present", "positive"}
    return False


def _score_fvg_in_impulse_context(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_fvg_in_impulse_enabled", True)):
        return 0.0, {}
    raw_signal = _context_value(
        context,
        "fvg_in_impulse",
        "creates_fvg",
        "impulse_creates_fvg",
        "has_fvg_in_impulse",
        "fvg_impulse_present",
    )
    if raw_signal is None:
        return 0.0, {}

    symbol = _normalized(_context_value(context, "symbol", "source_symbol"))
    deltas = _mapping(block.get("contextual_fvg_in_impulse_delta_pp"))
    delta_pp = None
    for key, value in deltas.items():
        if _normalized(key) == symbol:
            delta_pp = _float_value(value, 0.0)
            break

    summary = {
        "raw_signal": raw_signal,
        "present": _truthy_context_value(raw_signal),
        "symbol": _context_value(context, "symbol", "source_symbol"),
        "delta_pp": delta_pp,
        "policy": "positive_modifier_not_gate",
        "source_path": ".context/02_session_handoffs/03_apr6_multiinstrument.md",
        "source_line_no": 134,
    }
    if not summary["present"]:
        return 0.0, summary

    factor_score = _float_value(block.get("contextual_fvg_in_impulse_support_score"), 0.5)
    _add_factor(
        factors,
        factor_score,
        "fvg_in_impulse_context",
        summary,
        "fvg_in_impulse_positive_modifier_not_gate",
    )
    return factor_score, summary


def _score_sweep_before_ob_context(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_sweep_before_ob_enabled", True)):
        return 0.0, {}
    raw_signal = _context_value(
        context,
        "sweep_before_ob",
        "liquidity_sweep_before_ob",
        "pre_ob_sweep_detected",
        "ob_preceded_by_sweep",
        "setup_has_sweep_before_ob",
        "sweep_before_poi",
        "liquidity_sweep_before_poi",
    )
    if raw_signal is None:
        return 0.0, {}

    summary = {
        "raw_signal": raw_signal,
        "present": _truthy_context_value(raw_signal),
        "policy": "explicit_sweep_before_ob_modifier_not_generic_sweep_gate",
        "with_sweep_continuation_wr_pct": _float_value(
            block.get("contextual_sweep_before_ob_with_continuation_wr_pct"),
            63.4,
        ),
        "without_sweep_continuation_wr_pct": _float_value(
            block.get("contextual_sweep_before_ob_without_continuation_wr_pct"),
            71.6,
        ),
        "source_path": ".context/02_session_handoffs/06_apr7_complete_v2.md",
        "source_line_no": 173,
    }
    if not summary["present"]:
        return 0.0, summary

    factor_score = _float_value(block.get("contextual_sweep_before_ob_score"), -0.5)
    _add_factor(
        factors,
        factor_score,
        "sweep_before_ob_context",
        summary,
        "sweep_before_ob_adverse_modifier_not_gate",
    )
    return factor_score, summary


def _score_internal_session_volatility_context(
    *,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_internal_session_volatility_enabled", True)):
        return 0.0, {}
    raw_ratio = _context_value(
        context,
        "m15_session_vol_ratio",
        "session_vol_ratio",
        "mso_m15_session_vol_ratio",
        "internal_session_vol_ratio",
    )
    try:
        ratio = None if raw_ratio is None else float(raw_ratio)
    except (TypeError, ValueError):
        return 0.0, {}
    if ratio is None:
        return 0.0, {}

    support_min = _float_value(block.get("contextual_session_vol_ratio_support_min"), 1.2)
    summary = {
        "m15_session_vol_ratio": ratio,
        "support_min": support_min,
        "policy": "high_internal_vol_positive_modifier_not_entry_filter",
        "removed_high_vol_entries_delta_r": _float_value(
            block.get("contextual_garch_evt_removed_high_vol_delta_r"),
            -18.8,
        ),
        "source_path": ".context/02_session_handoffs/09_apr11_research_pipeline.md",
        "source_line_no": 46,
    }
    if ratio >= support_min:
        factor_score = _float_value(block.get("contextual_session_vol_ratio_support_score"), 0.5)
        _add_factor(
            factors,
            factor_score,
            "internal_session_volatility",
            summary,
            "high_internal_vol_positive_modifier_not_filter",
        )
        return factor_score, summary
    return 0.0, summary


def _score_derived_order_flow_context(
    *,
    direction: str,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
    factors: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    if not bool(block.get("contextual_derived_order_flow_enabled", True)):
        return 0.0, {}

    raw_clv = _context_value(context, "m15_clv_avg_5", "clv_avg_5", "mso_m15_clv_avg_5")
    raw_bvc = _context_value(
        context,
        "m15_bvc_buy_fraction",
        "bvc_buy_fraction",
        "mso_m15_bvc_buy_fraction",
    )
    raw_net_flow = _context_value(context, "m15_net_flow_5", "net_flow_5", "mso_m15_net_flow_5")
    if raw_clv is None and raw_bvc is None and raw_net_flow is None:
        return 0.0, {}

    try:
        clv = None if raw_clv is None else float(raw_clv)
        bvc = None if raw_bvc is None else float(raw_bvc)
        net_flow = None if raw_net_flow is None else float(raw_net_flow)
    except (TypeError, ValueError):
        return 0.0, {}

    clv_threshold = _float_value(block.get("contextual_order_flow_clv_threshold"), 0.2)
    bvc_threshold = _float_value(block.get("contextual_order_flow_bvc_threshold"), 0.6)
    net_flow_threshold = _float_value(block.get("contextual_order_flow_net_flow_threshold"), 0.0)

    side = (direction or "").upper()
    if side not in {"LONG", "SHORT"}:
        return 0.0, {}
    side_sign = 1 if side == "LONG" else -1
    aligned_signals = 0
    opposed_signals = 0
    total_signals = 0
    if clv is not None and abs(clv) >= clv_threshold:
        total_signals += 1
        if clv * side_sign > 0:
            aligned_signals += 1
        else:
            opposed_signals += 1
    if bvc is not None and (bvc >= bvc_threshold or bvc <= 1.0 - bvc_threshold):
        total_signals += 1
        bullish_bvc = bvc >= bvc_threshold
        if (bullish_bvc and side_sign > 0) or (not bullish_bvc and side_sign < 0):
            aligned_signals += 1
        else:
            opposed_signals += 1
    if net_flow is not None and abs(net_flow) > net_flow_threshold:
        total_signals += 1
        if net_flow * side_sign > 0:
            aligned_signals += 1
        else:
            opposed_signals += 1

    min_signals = int(_float_value(block.get("contextual_order_flow_min_signals"), 2.0))
    summary = {
        "m15_clv_avg_5": clv,
        "m15_bvc_buy_fraction": bvc,
        "m15_net_flow_5": net_flow,
        "aligned_signals": aligned_signals,
        "opposed_signals": opposed_signals,
        "total_signals": total_signals,
        "min_signals": min_signals,
        "policy": "derived_order_flow_modifier_not_raw_volume_gate",
        "source_path": ".context/02_session_handoffs/10_apr11_strategic_advisor_handoff.md",
        "source_line_no": 91,
    }

    if aligned_signals >= min_signals and aligned_signals > opposed_signals:
        factor_score = _float_value(block.get("contextual_order_flow_aligned_score"), 0.5)
        _add_factor(
            factors,
            factor_score,
            "derived_order_flow",
            summary,
            "clv_bvc_net_flow_aligned_positive_modifier",
        )
        return factor_score, summary
    if opposed_signals >= min_signals and opposed_signals >= aligned_signals:
        factor_score = _float_value(block.get("contextual_order_flow_opposed_score"), -0.5)
        _add_factor(
            factors,
            factor_score,
            "derived_order_flow",
            summary,
            "clv_bvc_net_flow_opposed_risk_reducer",
        )
        return factor_score, summary
    return 0.0, summary


def _contextual_score(
    *,
    direction: str,
    block: Mapping[str, Any],
    context: Mapping[str, Any],
) -> tuple[float, dict[str, Any], tuple[dict[str, Any], ...]]:
    factors: list[dict[str, Any]] = []
    vnext_label, vnext_evidence, vnext_event = _decision_object_context(context)
    label = _normalized(vnext_label or "LEGACY").upper() or "LEGACY"
    decision_scores = _configured_scores(
        block,
        "contextual_decision_scores",
        {"FOLLOW": 2.0, "MIXED": -1.0, "AVOID": -3.0, "LEGACY": 0.0},
    )
    score = decision_scores.get(_normalized(label), 0.0)
    _add_factor(factors, score, "vnext_decision", label, "matched_runtime_decision")

    metric_settings = {
        "cost_adjusted_simulated_r": (
            "contextual_cost_adjusted_r_positive_score",
            "contextual_cost_adjusted_r_negative_score",
            1.0,
            -1.0,
        ),
        "proxy_score": (
            "contextual_proxy_positive_score",
            "contextual_proxy_negative_score",
            0.5,
            -0.5,
        ),
        "stress_simulated_r": (
            "contextual_stress_positive_score",
            "contextual_stress_negative_score",
            0.5,
            -0.5,
        ),
    }
    metric_sums: dict[str, float | None] = {}
    for metric, (pos_key, neg_key, pos_default, neg_default) in metric_settings.items():
        value = _metric_sum(vnext_evidence, metric)
        metric_sums[metric] = value
        if value is None or value == 0:
            continue
        factor_score = _float_value(
            block.get(pos_key if value > 0 else neg_key),
            pos_default if value > 0 else neg_default,
        )
        score += factor_score
        _add_factor(factors, factor_score, metric, value, "vnext_metric_sum")

    min_effective_n = _float_value(block.get("contextual_min_effective_n"), 3.0)
    effective_n = _metric_sum(vnext_evidence, "effective_n")
    metric_sums["effective_n"] = effective_n
    matched_rows = _float_value(vnext_evidence.get("matched_rows"), 0.0)
    if effective_n is not None and effective_n >= min_effective_n:
        factor_score = _float_value(block.get("contextual_effective_n_support_score"), 0.5)
        score += factor_score
        _add_factor(factors, factor_score, "effective_n", effective_n, "vnext_sample_support")
    elif matched_rows > 0 and (effective_n is None or effective_n < min_effective_n):
        factor_score = _float_value(block.get("contextual_low_effective_n_score"), -0.5)
        score += factor_score
        _add_factor(factors, factor_score, "effective_n", effective_n, "vnext_low_sample_support")

    h1_autocorr = context.get("h1_autocorrelation")
    try:
        h1_autocorr_float = None if h1_autocorr is None else float(h1_autocorr)
    except (TypeError, ValueError):
        h1_autocorr_float = None
    h1_threshold = _float_value(block.get("h1_autocorrelation_follow_threshold"), 0.0)
    h1_decay_applied = bool(context.get("h1_decay_risk_applied"))
    if h1_autocorr_float is not None:
        if h1_autocorr_float > h1_threshold:
            factor_score = _float_value(block.get("contextual_h1_follow_through_score"), 1.0)
            score += factor_score
            _add_factor(factors, factor_score, "h1_follow_through", h1_autocorr_float, "positive_autocorrelation")
        elif h1_decay_applied:
            _add_factor(factors, 0.0, "h1_decay", h1_autocorr_float, "already_sized_by_autocorrelation_risk")
        else:
            factor_score = _float_value(block.get("contextual_h1_decay_score"), -1.5)
            score += factor_score
            _add_factor(factors, factor_score, "h1_decay", h1_autocorr_float, "non_positive_autocorrelation")

    asian_info = _mapping(context.get("asian_range_info"))
    asian_pct_raw = _context_value(context, "asian_range_pct_of_adr") or asian_info.get("pct_of_adr")
    try:
        asian_pct = None if asian_pct_raw is None else float(asian_pct_raw)
    except (TypeError, ValueError):
        asian_pct = None
    if asian_pct is not None and bool(block.get("contextual_asian_range_enabled", True)):
        too_narrow = _float_value(block.get("contextual_asian_too_narrow_threshold_pct"), 28.0)
        support_max = _float_value(block.get("contextual_asian_narrow_support_max_pct"), 50.0)
        wide = _float_value(block.get("contextual_asian_wide_threshold_pct"), 80.0)
        if asian_pct < too_narrow:
            factor_score = _float_value(block.get("contextual_asian_too_narrow_score"), -1.0)
            score += factor_score
            _add_factor(factors, factor_score, "asian_range", asian_pct, "too_narrow_low_liquidity")
        elif asian_pct <= support_max:
            factor_score = _float_value(block.get("contextual_asian_narrow_support_score"), 0.5)
            score += factor_score
            _add_factor(factors, factor_score, "asian_range", asian_pct, "compressed_range_support")
        elif asian_pct >= wide:
            factor_score = _float_value(block.get("contextual_asian_wide_score"), -1.0)
            score += factor_score
            _add_factor(factors, factor_score, "asian_range", asian_pct, "wide_range_consolidation_risk")

    session_phase_score, session_phase_summary = _score_session_phase(
        block=block,
        context=context,
        factors=factors,
    )
    score += session_phase_score

    news_score, news_summary = _score_news_event_risk(
        block=block,
        context=context,
        factors=factors,
    )
    score += news_score

    volatility_score, volatility_summary = _score_volatility_regime(
        block=block,
        context=context,
        factors=factors,
    )
    score += volatility_score

    ready8_score, ready8_matches, ready8_adjustments = _score_ready8_rules(
        block=block,
        context={**context, "side": direction},
        factors=factors,
    )
    score += ready8_score

    align_score, align_summary = _score_align_context(
        block=block,
        context=context,
        factors=factors,
    )
    score += align_score

    fvg_impulse_score, fvg_impulse_summary = _score_fvg_in_impulse_context(
        block=block,
        context=context,
        factors=factors,
    )
    score += fvg_impulse_score

    sweep_before_ob_score, sweep_before_ob_summary = _score_sweep_before_ob_context(
        block=block,
        context=context,
        factors=factors,
    )
    score += sweep_before_ob_score

    internal_vol_score, internal_vol_summary = _score_internal_session_volatility_context(
        block=block,
        context=context,
        factors=factors,
    )
    score += internal_vol_score

    order_flow_score, order_flow_summary = _score_derived_order_flow_context(
        direction=direction,
        block=block,
        context=context,
        factors=factors,
    )
    score += order_flow_score

    validation_leash_score, validation_leash_matches = _score_validation_leash_rules(
        block=block,
        context={**context, "side": direction},
        factors=factors,
    )
    score += validation_leash_score

    monthly_decay_score, monthly_decay_matches = _score_monthly_decay_rules(
        block=block,
        context={**context, "side": direction},
        factors=factors,
    )
    score += monthly_decay_score

    source_component_decisions = _mapping(vnext_evidence.get("source_component_decision_counts"))
    nofill_follow, nofill_avoid = _decision_counts_for_tokens(
        source_component_decisions,
        ("nofill", "no_fill", "fillability", "pending"),
    )
    if nofill_avoid > nofill_follow:
        factor_score = _float_value(block.get("contextual_nofill_avoid_score"), -2.0)
        score += factor_score
        _add_factor(factors, factor_score, "nofill_path_quality", f"{nofill_follow}/{nofill_avoid}", "avoid_dominant")
    elif nofill_follow > nofill_avoid:
        factor_score = _float_value(block.get("contextual_nofill_follow_score"), 1.0)
        score += factor_score
        _add_factor(factors, factor_score, "nofill_path_quality", f"{nofill_follow}/{nofill_avoid}", "follow_dominant")

    proxy_counts = _mapping(vnext_evidence.get("proxy_r_class_counts"))
    positive_proxy = _dict_counts_total(proxy_counts, ("positive",))
    negative_proxy = _dict_counts_total(proxy_counts, ("negative",))
    proxy_min_rows = int(_float_value(block.get("contextual_proxy_class_min_rows"), 1.0))
    if positive_proxy >= proxy_min_rows and positive_proxy > negative_proxy:
        factor_score = _float_value(block.get("contextual_strong_positive_proxy_score"), 1.0)
        score += factor_score
        _add_factor(factors, factor_score, "proxy_r_class", positive_proxy, "positive_proxy_dominant")
    elif negative_proxy >= proxy_min_rows and negative_proxy >= positive_proxy:
        factor_score = _float_value(block.get("contextual_strong_negative_proxy_score"), -1.5)
        score += factor_score
        _add_factor(factors, factor_score, "proxy_r_class", negative_proxy, "negative_proxy_dominant")

    target_stop_counts = _mapping(vnext_evidence.get("target_stop_order_class_counts"))
    stop_first = _dict_counts_total(target_stop_counts, ("stop_first",))
    not_source_bound = _dict_counts_total(target_stop_counts, ("not_source_bound",))
    target_first = _dict_counts_total(target_stop_counts, ("target_first",))
    if stop_first or not_source_bound:
        factor_score = _float_value(block.get("contextual_stop_or_geometry_adverse_score"), -2.0)
        score += factor_score
        _add_factor(
            factors,
            factor_score,
            "target_stop_path_quality",
            {"stop_first": stop_first, "not_source_bound": not_source_bound},
            "adverse_path_or_geometry",
        )
    elif target_first:
        factor_score = _float_value(block.get("contextual_target_first_score"), 0.5)
        score += factor_score
        _add_factor(factors, factor_score, "target_stop_path_quality", target_first, "target_first_proxy")

    score += _score_context_maps(block=block, context=context, factors=factors)

    evidence_summary = {
        "vnext_decision": label,
        "vnext_matched_rows": vnext_evidence.get("matched_rows"),
        "vnext_metric_sums": metric_sums,
        "vnext_decision_counts": vnext_evidence.get("decision_counts", {}),
        "vnext_symbol_family_counts": vnext_evidence.get("symbol_family_counts", {}),
        "vnext_side_counts": vnext_evidence.get("side_counts", {}),
        "vnext_session_counts": vnext_evidence.get("route_session_counts", {}),
        "vnext_framework_counts": vnext_evidence.get("framework_counts", {}),
        "vnext_route_family_counts": vnext_evidence.get("route_family_counts", {}),
        "vnext_market_timeframe_counts": vnext_evidence.get("market_timeframe_counts", {}),
        "vnext_source_component_decision_counts": source_component_decisions,
        "vnext_proxy_r_class_counts": proxy_counts,
        "vnext_target_stop_order_class_counts": target_stop_counts,
        "vnext_event": vnext_event,
        "h1_autocorrelation": h1_autocorr_float,
        "h1_decay_risk_applied": h1_decay_applied,
        "asian_range_pct_of_adr": asian_pct,
        "asian_range_category": context.get("asian_range_category") or asian_info.get("category"),
        "session_phase": session_phase_summary,
        "news_event_risk": news_summary,
        "volatility_regime": volatility_summary,
        "ready8_card_id": _context_value(context, "ready8_card_id"),
        "ready8_horizon_m15_bars": _context_value(context, "ready8_horizon_m15_bars"),
        "ready8_target_family_id": _context_value(context, "ready8_target_family_id"),
        "ready8_partition_assignment": _context_value(context, "ready8_partition_assignment"),
        "ready8_descriptor_name": _context_value(context, "ready8_descriptor_name"),
        "ready8_descriptor_value": _context_value(context, "ready8_descriptor_value"),
        "ready8_wait_gap_bucket": _context_value(context, "ready8_wait_gap_bucket"),
        "ready8_prior_24h_count_bucket": _context_value(
            context, "ready8_prior_24h_count_bucket"
        ),
        "ready8_source_window": _context_value(context, "ready8_source_window"),
        "ready8_source_segment_sha256": _context_value(
            context, "ready8_source_segment_sha256"
        ),
        "ready8_canonical_economic_group": _context_value(
            context, "ready8_canonical_economic_group"
        ),
        "ready8_matched_rules": ready8_matches,
        "ready8_matched_adjustments": ready8_adjustments,
        "align_context": align_summary,
        "fvg_in_impulse_context": fvg_impulse_summary,
        "sweep_before_ob_context": sweep_before_ob_summary,
        "internal_session_volatility": internal_vol_summary,
        "derived_order_flow": order_flow_summary,
        "validation_leash_matched_rules": validation_leash_matches,
        "monthly_decay_matched_rules": monthly_decay_matches,
        "direction": direction,
    }
    return round(score, 6), evidence_summary, tuple(factors)


def evaluate_contextual_side_multiplier(
    base_risk_pct: float,
    direction: str,
    config: Mapping[str, Any] | None,
    context: Mapping[str, Any] | None = None,
) -> ContextualSideRiskDecision:
    """Evaluate the runtime side-risk multiplier from context and evidence."""
    block = _section(config)
    side = (direction or "").upper()
    before = float(base_risk_pct)
    apply_to_execution = bool(block.get("apply_to_execution", True))
    if not is_enabled(config):
        return ContextualSideRiskDecision(
            enabled=False,
            apply_to_execution=False,
            applied=False,
            mode="disabled",
            direction=side,
            before_risk_pct=before,
            after_risk_pct=before,
            multiplier=1.0,
            would_multiplier=1.0,
            score=0.0,
            reason="side_aware_disabled",
        )
    if side not in {"LONG", "SHORT"}:
        return ContextualSideRiskDecision(
            enabled=True,
            apply_to_execution=apply_to_execution,
            applied=False,
            mode="unknown_side",
            direction=side,
            before_risk_pct=before,
            after_risk_pct=before,
            multiplier=1.0,
            would_multiplier=1.0,
            score=0.0,
            reason="side_aware_unknown_side",
        )

    mode = _normalized(block.get("mode") or "legacy")
    if mode != "contextual":
        would_multiplier = get_long_multiplier(config) if side == "LONG" else get_short_multiplier(config)
        multiplier = would_multiplier if apply_to_execution else 1.0
        after = round(before * multiplier, 12)
        return ContextualSideRiskDecision(
            enabled=True,
            apply_to_execution=apply_to_execution,
            applied=apply_to_execution and multiplier != 1.0,
            mode="legacy",
            direction=side,
            before_risk_pct=before,
            after_risk_pct=after,
            multiplier=multiplier,
            would_multiplier=would_multiplier,
            score=0.0,
            reason="side_aware_legacy_multiplier",
            context=dict(context or {}),
        )

    ctx = dict(context or {})
    ctx.setdefault("side", side)
    score, evidence_summary, factors = _contextual_score(
        direction=side,
        block=block,
        context=ctx,
    )
    full_score = _float_value(block.get("contextual_full_risk_min_score"), 2.0)
    adverse_score = _float_value(block.get("contextual_adverse_score_threshold"), -1.0)
    weak_score = _float_value(block.get("contextual_weak_score_threshold"), -0.25)
    full_multiplier = _float_value(block.get("contextual_full_risk_multiplier"), 1.0)
    default_multiplier = _float_value(block.get("contextual_default_multiplier"), 1.0)
    weak_multiplier = _float_value(block.get("contextual_weak_multiplier"), 0.5)
    adverse_multiplier = _float_value(block.get("contextual_adverse_multiplier"), 0.25)
    if score >= full_score:
        would_multiplier = full_multiplier
        reason = "contextual_side_risk_full_supported"
    elif score <= adverse_score:
        would_multiplier = adverse_multiplier
        reason = "contextual_side_risk_adverse_reduced"
    elif score <= weak_score:
        would_multiplier = weak_multiplier
        reason = "contextual_side_risk_weak_reduced"
    else:
        would_multiplier = default_multiplier
        reason = "contextual_side_risk_neutral_base"
    min_multiplier = _float_value(block.get("contextual_min_multiplier"), 0.0)
    max_multiplier = _float_value(block.get("contextual_max_multiplier"), 1.0)
    would_multiplier = max(min_multiplier, min(max_multiplier, would_multiplier))
    multiplier = would_multiplier if apply_to_execution else 1.0
    after = round(before * multiplier, 12)
    return ContextualSideRiskDecision(
        enabled=True,
        apply_to_execution=apply_to_execution,
        applied=apply_to_execution and multiplier != 1.0,
        mode="contextual",
        direction=side,
        before_risk_pct=before,
        after_risk_pct=after,
        multiplier=multiplier,
        would_multiplier=would_multiplier,
        score=score,
        reason=reason if apply_to_execution else f"shadow_{reason}",
        context=ctx,
        evidence_summary=evidence_summary,
        factors=factors,
    )


def attach_contextual_side_risk_to_record(
    record: dict[str, Any] | None,
    decision: ContextualSideRiskDecision,
) -> dict[str, Any] | None:
    """Attach contextual side-risk evidence to a trade record in-place."""
    if record is None:
        return None
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["contextual_side_risk"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["contextual_side_risk_applied"] = decision.applied
    inst["contextual_side_risk_multiplier"] = decision.multiplier
    inst["contextual_side_risk_would_multiplier"] = decision.would_multiplier
    inst["contextual_side_risk_score"] = decision.score
    inst["contextual_side_risk_reason"] = decision.reason
    return record
