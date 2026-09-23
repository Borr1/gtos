"""Market Whiteboard V2 runtime admission model.

This module owns source-bound market-state memory for candidate admission. It
does not read broker history, mutate broker state, call paid APIs, or infer
historical intent. Callers provide decision-time source status and any
precomputed damage memory; the evaluator returns an auditable admission action.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


SourceLabel = Literal[
    "decision-available",
    "broker-real",
    "proxy",
    "replay-only",
    "label-only",
    "missing",
    "non-generatable",
]
AdmissionAction = Literal[
    "ALLOW",
    "RISK_REDUCE",
    "NO_TRADE",
    "QUARANTINE",
    "SOURCE_REQUIRED",
]
MarketSystemDisposition = Literal[
    "acceptable_market_state",
    "bad_market",
    "bad_system",
    "market_system_mismatch",
    "source_incomplete",
]


DEFAULT_CRITICAL_SOURCES = (
    "m1",
    "tick",
    "spread",
    "session",
    "volatility",
    "correlation",
)
DEFAULT_PROXY_ALLOWED_SOURCES = ("volatility", "correlation")
VALID_SOURCE_LABELS = {
    "decision-available",
    "broker-real",
    "proxy",
    "replay-only",
    "label-only",
    "missing",
    "non-generatable",
}
HARD_ACTIONS = {"NO_TRADE", "QUARANTINE", "SOURCE_REQUIRED"}


@dataclass(frozen=True)
class SourceCompleteness:
    """Decision-time source state for the fields the whiteboard uses."""

    state: str
    missing_sources: list[str] = field(default_factory=list)
    forbidden_sources: list[str] = field(default_factory=list)
    proxy_sources: list[str] = field(default_factory=list)
    field_source_state: dict[str, str] = field(default_factory=dict)
    stale_or_null_reason: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DamageClassification:
    """Symbol/session damage-memory result."""

    action: AdmissionAction
    reason: str
    symbol_state: str
    cell_state: str
    symbol_health: dict[str, Any] = field(default_factory=dict)
    symbol_session_side_health: dict[str, Any] = field(default_factory=dict)
    evidence_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketWhiteboardDecision:
    """Final Market Whiteboard V2 admission result."""

    action: AdmissionAction
    reason: str
    disposition: MarketSystemDisposition
    candidate_symbol: str
    candidate_side: str | None
    decision_asof_utc: str
    source_completeness: SourceCompleteness
    damage: DamageClassification
    zero_trade_state: dict[str, Any] = field(default_factory=dict)
    semantic_handoffs: dict[str, Any] = field(default_factory=dict)
    evidence_class: str = "production-code integration plus source-bound market-state memory"
    broker_runtime_change_status: bool = False
    validation_result_status: bool = False
    outcome_result_rows_status: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_enabled(config: dict | None) -> bool:
    cfg = (config or {}).get("market_whiteboard_v2")
    return isinstance(cfg, dict) and bool(cfg.get("enabled", False))


def _whiteboard_cfg(config: dict | None) -> dict[str, Any]:
    cfg = (config or {}).get("market_whiteboard_v2", {})
    return cfg if isinstance(cfg, dict) else {}


def _source_cfg(config: dict | None) -> dict[str, Any]:
    cfg = _whiteboard_cfg(config).get("source_requirements", {})
    return cfg if isinstance(cfg, dict) else {}


def _damage_cfg(config: dict | None) -> dict[str, Any]:
    cfg = _whiteboard_cfg(config).get("damage_rules", {})
    return cfg if isinstance(cfg, dict) else {}


def normalize_source_label(value: object) -> str:
    text = str(value or "missing").strip().lower().replace("_", "-")
    return text if text in VALID_SOURCE_LABELS else "missing"


def _normalize_source_status(raw: object) -> tuple[str, dict[str, Any]]:
    if isinstance(raw, dict):
        label = normalize_source_label(
            raw.get("source_state")
            or raw.get("status")
            or raw.get("label")
            or raw.get("state")
        )
        return label, dict(raw)
    label = normalize_source_label(raw)
    return label, {"source_state": label}


def _as_mapping(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump(mode="json")
        return dict(dumped) if isinstance(dumped, dict) else {}
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _get_nested_context(container: object, attr: str) -> dict[str, Any]:
    if container is None:
        return {}
    value = getattr(container, attr, None)
    if value is None and isinstance(container, dict):
        value = container.get(attr)
    return _as_mapping(value)


def candidate_context_from_runtime(
    trade_params: object,
    session_state: dict | None,
    symbol: str,
) -> dict[str, Any]:
    """Extract the caller-supplied whiteboard context without side effects."""

    merged: dict[str, Any] = {}
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None and isinstance(trade_params, dict):
        tp = trade_params.get("trade_parameters")

    for context in (
        _get_nested_context(trade_params, "gtos_vnext_market_whiteboard_context"),
        _get_nested_context(tp, "gtos_vnext_market_whiteboard_context"),
    ):
        merged.update(context)

    state_context = (session_state or {}).get("market_whiteboard_v2_context")
    if isinstance(state_context, dict):
        symbol_key = normalize_symbol(symbol)
        candidate = (
            state_context.get(symbol)
            or state_context.get(symbol_key)
            or state_context.get("default")
        )
        if isinstance(candidate, dict):
            merged.update(candidate)
        elif any(key in state_context for key in ("source_status", "damage_memory")):
            merged.update(state_context)

    if "source_status" not in merged:
        source_status: dict[str, dict[str, Any]] = {}

        def value(name: str) -> Any:
            if isinstance(tp, dict) and name in tp:
                return tp.get(name)
            if tp is not None and hasattr(tp, name):
                return getattr(tp, name)
            if isinstance(trade_params, dict):
                return trade_params.get(name)
            return getattr(trade_params, name, None)

        has_source_identity = any(
            value(name) not in (None, "", [], {})
            for name in (
                "source_file",
                "source_path",
                "gtos_vnext_source_file",
                "gtos_vnext_source_path",
                "gtos_vnext_source_event_hash",
                "gtos_vnext_source_event_details",
                "gtos_vnext_selector_row_id",
            )
        )
        source_window_complete = value("source_window_complete")
        if has_source_identity or source_window_complete is True:
            source_status["m1"] = {
                "source_state": "decision-available",
                "reason": "derived_from_vnext_source_identity",
            }
        session_value = (
            value("session")
            or value("kill_zone")
            or value("route_session")
            or value("gtos_vnext_route_session")
        )
        if session_value not in (None, ""):
            source_status["session"] = {
                "source_state": "decision-available",
                "value": session_value,
                "reason": "derived_from_runtime_session_context",
            }
        source_status.setdefault(
            "volatility",
            {
                "source_state": "proxy",
                "reason": "market_whiteboard_accepts_proxy_volatility_until_feature_store_v2_materializes",
            },
        )
        source_status.setdefault(
            "correlation",
            {
                "source_state": "proxy",
                "reason": "market_whiteboard_accepts_proxy_correlation_until_feature_store_v2_materializes",
            },
        )
        if source_status:
            merged["source_status"] = source_status

    return merged


def normalize_symbol(symbol: object) -> str:
    text = str(symbol or "").strip()
    return text.upper().replace(".", "_")


def session_bucket_from_utc(timestamp_utc: str | None) -> str | None:
    if not timestamp_utc:
        return None
    text = str(timestamp_utc)
    try:
        hour = int(text[11:13])
    except (TypeError, ValueError, IndexError):
        return None
    if 0 <= hour <= 6:
        return "asia_tokyo_broad_utc_00_06"
    if 7 <= hour <= 11:
        return "london_broad_utc_07_11"
    if 12 <= hour <= 16:
        return "ny_overlap_broad_utc_12_16"
    if 17 <= hour <= 21:
        return "late_ny_broad_utc_17_21"
    return "rollover_utc_22_23"


def evaluate_source_completeness(
    source_status: dict[str, Any] | None,
    config: dict | None = None,
) -> SourceCompleteness:
    """Check critical source families with no hidden nulls."""

    cfg = _source_cfg(config)
    critical_sources = tuple(cfg.get("critical_sources") or DEFAULT_CRITICAL_SOURCES)
    proxy_allowed = set(cfg.get("proxy_allowed") or DEFAULT_PROXY_ALLOWED_SOURCES)
    statuses = source_status if isinstance(source_status, dict) else {}

    missing: list[str] = []
    forbidden: list[str] = []
    proxy: list[str] = []
    field_state: dict[str, str] = {}
    reasons: list[dict[str, Any]] = []

    for source in critical_sources:
        label, details = _normalize_source_status(statuses.get(source))
        field_state[source] = label
        if label == "proxy":
            proxy.append(source)
            if source not in proxy_allowed:
                forbidden.append(source)
                reasons.append({
                    "field": source,
                    "source_state": label,
                    "reason": "proxy_not_allowed_for_live_admission",
                    "capture_or_repair_requirement": details.get(
                        "capture_or_repair_requirement",
                        f"provide decision-available {source} source",
                    ),
                })
        elif label in {"missing", "non-generatable"}:
            missing.append(source)
            reasons.append({
                "field": source,
                "source_state": label,
                "reason": details.get("reason") or "critical_source_missing",
                "capture_or_repair_requirement": details.get(
                    "capture_or_repair_requirement",
                    f"capture decision-time {source} state before admission",
                ),
            })
        elif label in {"replay-only", "label-only"}:
            forbidden.append(source)
            reasons.append({
                "field": source,
                "source_state": label,
                "reason": "not_allowed_as_live_decision_feature",
                "capture_or_repair_requirement": details.get(
                    "capture_or_repair_requirement",
                    f"replace {source} with decision-available source state",
                ),
            })

    if missing or forbidden:
        state = "incomplete"
    elif proxy:
        state = "proxy_complete"
    else:
        state = "complete_decision_available"

    return SourceCompleteness(
        state=state,
        missing_sources=missing,
        forbidden_sources=forbidden,
        proxy_sources=proxy,
        field_source_state=field_state,
        stale_or_null_reason=reasons,
    )


def _float_metric(metrics: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(metrics.get(key, default))
    except (TypeError, ValueError):
        return default


def _int_metric(metrics: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(metrics.get(key, default))
    except (TypeError, ValueError):
        return default


def _classify_symbol_health(metrics: dict[str, Any], cfg: dict[str, Any]) -> str:
    trades = _int_metric(metrics, "trades")
    losses = _int_metric(metrics, "losses")
    net = _float_metric(metrics, "net")
    win_rate = _float_metric(metrics, "win_rate", 1.0)

    min_trades = int(cfg.get("symbol_hard_min_trades", 6))
    max_win_rate = float(cfg.get("symbol_hard_max_win_rate", 0.35))
    max_net = float(cfg.get("symbol_hard_max_net_cash", -500.0))
    min_losses = int(cfg.get("symbol_hard_min_losses", 4))
    reduce_net = float(cfg.get("symbol_reduce_max_net_cash", -100.0))
    reduce_win_rate = float(cfg.get("symbol_reduce_max_win_rate", 0.45))

    if trades >= min_trades and (
        net <= max_net or win_rate <= max_win_rate or losses >= min_losses
    ):
        return "hard_quarantine"
    if trades > 0 and (net <= reduce_net or win_rate <= reduce_win_rate):
        return "risk_reduce"
    return "healthy_or_unproven"


def _classify_cell_health(metrics: dict[str, Any], cfg: dict[str, Any]) -> str:
    trades = _int_metric(metrics, "trades")
    losses = _int_metric(metrics, "losses")
    net = _float_metric(metrics, "net")
    win_rate = _float_metric(metrics, "win_rate", 1.0)

    min_trades = int(cfg.get("cell_hard_min_trades", 2))
    max_win_rate = float(cfg.get("cell_hard_max_win_rate", 0.0))
    max_net = float(cfg.get("cell_hard_max_net_cash", -250.0))
    reduce_net = float(cfg.get("cell_reduce_max_net_cash", -100.0))
    reduce_win_rate = float(cfg.get("cell_reduce_max_win_rate", 0.35))

    hard_loss_cluster = losses >= min_trades and win_rate <= max_win_rate
    if trades >= min_trades and (net <= max_net or hard_loss_cluster):
        return "hard_quarantine"
    if trades > 0 and (net <= reduce_net or win_rate <= reduce_win_rate):
        return "risk_reduce"
    return "healthy_or_unproven"


def classify_damage_memory(
    damage_memory: dict[str, Any] | None,
    config: dict | None = None,
) -> DamageClassification:
    """Classify symbol/session-side memory without copying broker facts to another broker."""

    cfg = _damage_cfg(config)
    memory = damage_memory if isinstance(damage_memory, dict) else {}
    symbol_health = _as_mapping(memory.get("symbol_health"))
    cell_health = _as_mapping(
        memory.get("symbol_session_side_health")
        or memory.get("symbol_side_bucket_health")
        or memory.get("cell_health")
    )
    tags = [
        str(tag)
        for tag in memory.get("supporting_evidence_tags", [])
        if str(tag).strip()
    ]

    symbol_state = _classify_symbol_health(symbol_health, cfg) if symbol_health else "not_supplied"
    cell_state = _classify_cell_health(cell_health, cfg) if cell_health else "not_supplied"

    if symbol_state == "hard_quarantine" or cell_state == "hard_quarantine":
        return DamageClassification(
            action="QUARANTINE",
            reason="recent_damage_symbol_session_quarantine",
            symbol_state=symbol_state,
            cell_state=cell_state,
            symbol_health=symbol_health,
            symbol_session_side_health=cell_health,
            evidence_tags=tags,
        )
    if symbol_state == "risk_reduce" or cell_state == "risk_reduce":
        return DamageClassification(
            action="RISK_REDUCE",
            reason="recent_damage_symbol_session_risk_reduce",
            symbol_state=symbol_state,
            cell_state=cell_state,
            symbol_health=symbol_health,
            symbol_session_side_health=cell_health,
            evidence_tags=tags,
        )
    return DamageClassification(
        action="ALLOW",
        reason="no_material_recent_damage_memory_supplied_or_triggered",
        symbol_state=symbol_state,
        cell_state=cell_state,
        symbol_health=symbol_health,
        symbol_session_side_health=cell_health,
        evidence_tags=tags,
    )


def _zero_trade_state(context: dict[str, Any], config: dict | None) -> dict[str, Any]:
    cfg = _whiteboard_cfg(config).get("zero_trade_quality", {})
    if not isinstance(cfg, dict):
        cfg = {}
    no_trade_classes = set(cfg.get("no_trade_classifications") or [
        "no_trade_by_evidence",
        "source_capture_required",
    ])
    classification = (
        context.get("candidate_quality_classification")
        or context.get("zero_trade_quality")
        or context.get("quality_classification")
    )
    final_outcome = context.get("final_outcome")
    is_zero_trade = str(classification or "") in no_trade_classes
    return {
        "candidate_quality_classification": classification,
        "final_outcome": final_outcome,
        "zero_trade_is_positive_decision": bool(is_zero_trade),
        "source_gap": context.get("source_gap"),
    }


def _semantic_handoffs() -> dict[str, Any]:
    return {
        "same_symbol_lifecycle_owner": "same_symbol_same_instrument_lifecycle_v4",
        "probability_debate_owner": "probability_debate_team_engine_v4",
        "numeric_confluence_owner": "follow_avoid_mixed_numeric_confluence_v4",
        "ml_feature_label_owner": "Feature Store V2 and Label Store V2",
        "whiteboard_boundary": (
            "market state admission memory only; no ticket lifecycle mutation, "
            "no probability final selection, no ML label promotion"
        ),
    }


def evaluate_market_whiteboard_v2(
    *,
    candidate_symbol: str,
    candidate_side: str | None = None,
    context: dict[str, Any] | None = None,
    config: dict | None = None,
) -> MarketWhiteboardDecision:
    """Return the source-complete V2 market-state admission decision."""

    ctx = context if isinstance(context, dict) else {}
    source = evaluate_source_completeness(ctx.get("source_status"), config)
    damage = classify_damage_memory(ctx.get("damage_memory"), config)
    zero_trade = _zero_trade_state(ctx, config)
    asof = str(ctx.get("decision_asof_utc") or ctx.get("timestamp_utc") or _utc_now_iso())

    if source.state == "incomplete":
        action: AdmissionAction = "SOURCE_REQUIRED"
        reason = "critical_market_whiteboard_source_missing_or_forbidden"
        disposition: MarketSystemDisposition = "source_incomplete"
    elif damage.action == "QUARANTINE":
        action = "QUARANTINE"
        reason = damage.reason
        disposition = "market_system_mismatch"
    elif zero_trade["zero_trade_is_positive_decision"]:
        action = "NO_TRADE"
        reason = "zero_trade_by_market_state_quality_evidence"
        disposition = "market_system_mismatch"
    elif damage.action == "RISK_REDUCE":
        action = "RISK_REDUCE"
        reason = damage.reason
        disposition = "market_system_mismatch"
    else:
        action = "ALLOW"
        reason = "market_whiteboard_sources_complete_no_damage_or_zero_trade_trigger"
        disposition = "acceptable_market_state"

    return MarketWhiteboardDecision(
        action=action,
        reason=reason,
        disposition=disposition,
        candidate_symbol=normalize_symbol(candidate_symbol),
        candidate_side=candidate_side,
        decision_asof_utc=asof,
        source_completeness=source,
        damage=damage,
        zero_trade_state=zero_trade,
        semantic_handoffs=_semantic_handoffs(),
    )


def evaluate_for_permissions(
    *,
    trade_params: object,
    session_state: dict | None,
    config: dict | None,
    symbol: str,
) -> MarketWhiteboardDecision | None:
    """Evaluate the gate path only when config explicitly enables V2."""

    if not is_enabled(config):
        return None
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None and isinstance(trade_params, dict):
        tp = trade_params.get("trade_parameters")
    side = getattr(tp, "direction", None)
    if side is None and isinstance(tp, dict):
        side = tp.get("direction")
    context = candidate_context_from_runtime(trade_params, session_state, symbol)
    return evaluate_market_whiteboard_v2(
        candidate_symbol=symbol,
        candidate_side=side,
        context=context,
        config=config,
    )
