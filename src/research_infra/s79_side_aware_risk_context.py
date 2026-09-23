"""S79 and side-aware risk-context audit helpers for LTO-017.

This module snapshots shipped risk-policy context for candidates and filled
rows. It is research/tooling only: no risk setting is changed, no orders are
sent, and no live behavior is modified.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Mapping


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "s79_side_aware_risk_context_v1"
CLASSIFIER_VERSION = "s79_side_aware_risk_context_classifier_v1"
COMPLETE = "S79_SIDE_AWARE_CONTEXT_DOCUMENTED"
FILLED_JOINED = "S79_SIDE_AWARE_FILLED_ACCOUNT_HISTORY_JOINED"
SPRT_DISABLED = "S79_SIDE_AWARE_SPRT_DISABLED_CONTEXT"
ACTION_REQUIRED = "S79_SIDE_AWARE_CONTEXT_ACTION_REQUIRED"


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line_no), row) for line_no, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("timestamp_logged"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_key(rows: list[tuple[int, dict[str, Any]]], key: str) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        value = str(row.get(key) or "").strip()
        if not value:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        item_key = (_clock(item), line_no)
        previous = latest.get(value)
        previous_key = (_clock(previous or {}), int((previous or {}).get("_line_no") or 0))
        if item_key >= previous_key:
            latest[value] = item
    return latest


def _latest_broker_by_fill_id(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        fill_id = str(row.get("fill_id") or row.get("trade_id") or "").strip()
        if not fill_id:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        priority = 1 if item.get("actual_r_claim_allowed") is True and item.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED" else 0
        item_key = (priority, _clock(item), line_no)
        previous = latest.get(fill_id)
        previous_priority = (
            1
            if previous
            and previous.get("actual_r_claim_allowed") is True
            and previous.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
            else 0
        )
        previous_key = (previous_priority, _clock(previous or {}), int((previous or {}).get("_line_no") or 0))
        if item_key >= previous_key:
            latest[fill_id] = item
    return latest


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _risk_section(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return _mapping(_mapping(config).get("risk"))


def _instrument_section(config: Mapping[str, Any] | None, symbol: str) -> Mapping[str, Any]:
    instruments = _mapping(_mapping(config).get("instruments"))
    return _mapping(instruments.get(symbol))


def _instrument_risk(config: Mapping[str, Any] | None, symbol: str) -> Mapping[str, Any]:
    return _mapping(_instrument_section(config, symbol).get("risk"))


def _strategy_snapshot_present(candidate: dict[str, Any], strategy_id: str) -> bool:
    snapshots = candidate.get("strategy_snapshots") or []
    if not isinstance(snapshots, list):
        return False
    return any(isinstance(item, dict) and item.get("strategy_id") == strategy_id for item in snapshots)


def _side_multiplier(side: str | None, enabled: bool, disabled: bool, long_multiplier: float, short_multiplier: float) -> float:
    if not enabled or disabled:
        return 1.0
    normalized = str(side or "").upper()
    if normalized == "LONG":
        return long_multiplier
    if normalized == "SHORT":
        return short_multiplier
    return 1.0


def _sprt_summary(sprt_state: Mapping[str, Any] | None) -> dict[str, Any]:
    state = _mapping(sprt_state)
    outcomes = state.get("long_outcomes") if isinstance(state.get("long_outcomes"), list) else []
    wins = sum(1 for item in outcomes if isinstance(item, Mapping) and item.get("win") is True)
    count = len(outcomes)
    return {
        "state_version": state.get("version"),
        "disabled_at": state.get("disabled_at"),
        "disable_reason": state.get("disable_reason"),
        "long_outcome_count": count,
        "long_win_count": wins,
        "long_wr": round(wins / count, 4) if count else None,
    }


def resolve_risk_context(
    *,
    symbol: str,
    side: str | None,
    config: Mapping[str, Any] | None,
    profile: Mapping[str, Any] | None,
    sprt_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    risk_cfg = _risk_section(config)
    profile_risk = _risk_section(profile)
    profile_name = _mapping(profile).get("profile_name") or "base_config"
    base_risk = (
        _float_or_none(profile_risk.get("risk_per_trade_pct"))
        or _float_or_none(risk_cfg.get("risk_per_trade_pct"))
        or 0.0
    )
    instrument_risk = _instrument_risk(profile, symbol) or _instrument_risk(config, symbol)
    symbol_risk = _float_or_none(instrument_risk.get("risk_per_trade_pct"))
    if symbol_risk is None:
        symbol_risk = base_risk
    side_aware_cfg = _mapping(risk_cfg.get("side_aware_sizing"))
    enabled = bool(side_aware_cfg.get("enabled", False))
    long_multiplier = _float_or_none(side_aware_cfg.get("long_multiplier"))
    short_multiplier = _float_or_none(side_aware_cfg.get("short_multiplier"))
    long_multiplier = 0.5 if long_multiplier is None else long_multiplier
    short_multiplier = 1.0 if short_multiplier is None else short_multiplier
    sprt = _sprt_summary(sprt_state)
    disabled = bool(sprt.get("disabled_at"))
    multiplier = _side_multiplier(side, enabled, disabled, long_multiplier, short_multiplier)
    return {
        "profile_name": profile_name,
        "s79_policy_id": "S79_UNIFORM_FN_RISK_POLICY",
        "s79_policy_status": "SHIPPED_POLICY_CONTEXT",
        "base_risk_per_trade_pct": base_risk,
        "symbol_risk_per_trade_pct": symbol_risk,
        "side_aware_enabled": enabled,
        "side_aware_sprt_disabled": disabled,
        "side_aware_long_multiplier": long_multiplier,
        "side_aware_short_multiplier": short_multiplier,
        "side_multiplier_for_row": multiplier,
        "effective_risk_pct_if_side_aware_applied": round(symbol_risk * multiplier, 6),
        "sprt_window_size": side_aware_cfg.get("sprt_window_size"),
        "sprt_wr_threshold": side_aware_cfg.get("sprt_wr_threshold"),
        "sprt_state": sprt,
    }


def _broker_actual_allowed(row: dict[str, Any] | None) -> bool:
    return bool(
        row
        and row.get("actual_r_claim_allowed") is True
        and row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
    )


def _j46_side(row: dict[str, Any] | None) -> str | None:
    return str((row or {}).get("direction") or "") or None


def build_risk_context_row(
    *,
    row_type: str,
    source_row: dict[str, Any],
    config: Mapping[str, Any] | None,
    profile: Mapping[str, Any] | None,
    sprt_state: Mapping[str, Any] | None,
    broker_row: dict[str, Any] | None = None,
    j46_row: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    symbol = str(source_row.get("symbol") or source_row.get("instrument") or (broker_row or {}).get("symbol") or "")
    side = str(source_row.get("side") or _j46_side(j46_row) or "").upper() or None
    risk_context = resolve_risk_context(
        symbol=symbol,
        side=side,
        config=config,
        profile=profile,
        sprt_state=sprt_state,
    )
    actual_allowed = _broker_actual_allowed(broker_row)
    action_required: list[str] = []
    documented_limitations: list[str] = []
    if row_type == "candidate_risk_context" and not _strategy_snapshot_present(source_row, "S79_UNIFORM_FN_RISK_POLICY"):
        action_required.append("S79_STRATEGY_SNAPSHOT_MISSING_ON_CANDIDATE")
    if row_type == "filled_risk_context" and not actual_allowed:
        documented_limitations.append("FILLED_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_RISK_LABEL")
    status = ACTION_REQUIRED if action_required else SPRT_DISABLED if risk_context["side_aware_sprt_disabled"] else FILLED_JOINED if actual_allowed else COMPLETE
    candidate_id = source_row.get("candidate_id") or (broker_row or {}).get("candidate_id")
    fill_id = source_row.get("fill_id") or (broker_row or {}).get("fill_id")
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        row_type,
        candidate_id,
        fill_id,
        source_row.get("created_at_utc"),
        source_row.get("decision_time_utc"),
        source_row.get("timestamp_logged"),
        (broker_row or {}).get("row_key"),
        risk_context,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("s79_side_aware_risk_context", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-017",
        "follow_id": "LIVE-FOLLOW-014",
        "row_type": row_type,
        "s79_side_aware_context_status": status,
        "candidate_id": candidate_id,
        "fill_id": fill_id,
        "trade_id": source_row.get("trade_id") or (broker_row or {}).get("trade_id") or fill_id,
        "symbol": symbol,
        "broker_symbol": source_row.get("broker_symbol") or (broker_row or {}).get("broker_symbol") or symbol,
        "side": side,
        "framework": source_row.get("framework"),
        "session": source_row.get("session") or source_row.get("kill_zone"),
        "decision_time_utc": source_row.get("decision_time_utc") or (broker_row or {}).get("decision_time_utc"),
        "candidate_final_outcome_at_log": source_row.get("final_outcome_at_log"),
        "risk_context": risk_context,
        "s79_strategy_snapshot_present": _strategy_snapshot_present(source_row, "S79_UNIFORM_FN_RISK_POLICY") if row_type == "candidate_risk_context" else None,
        "account_history_join_status": "ACCOUNT_HISTORY_REALIZED" if actual_allowed else "NO_ACCOUNT_HISTORY_REALIZED_FOR_ROW",
        "actual_r_claim_allowed": actual_allowed,
        "broker_actual_r": (broker_row or {}).get("broker_actual_r") if actual_allowed else None,
        "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
        "broker_actual_r_evidence_class": (broker_row or {}).get("accounting_evidence_class"),
        "broker_actual_r_truth_lane": (broker_row or {}).get("truth_lane"),
        "documented_limitation_codes": sorted(set(documented_limitations)),
        "action_required_codes": sorted(set(action_required)),
        "claim_boundary": (
            "This row snapshots shipped S79/side-aware risk context only. It does not change risk, "
            "size positions, or validate a new risk policy."
        ),
        "ml_feature_role": "ML_RISK_POLICY_CONTEXT_AND_SAMPLE_WEIGHT_FEATURE",
        "ml_label_eligibility": "ACCOUNT_HISTORY_LABEL_WITH_RISK_CONTEXT" if actual_allowed else "RISK_CONTEXT_ONLY_NO_ACCOUNT_HISTORY_LABEL",
        "ml_no_leak_boundary": "DECISION_TIME_RISK_POLICY_CONTEXT_PLUS_POST_DECISION_LABEL_STATUS",
        "evidence_class": "SHIPPED_POLICY_CONTEXT",
        "no_leak_status": "RISK_POLICY_CONTEXT_AUDIT_NOT_DECISION_CHANGE",
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_s79_side_aware_context_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    broker_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    j46_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    config: Mapping[str, Any] | None = None,
    profile: Mapping[str, Any] | None = None,
    sprt_state: Mapping[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    candidates = _latest_by_key(_rows_with_lines(candidate_rows), "candidate_id")
    broker_by_candidate = _latest_by_key(_rows_with_lines(broker_rows), "candidate_id")
    broker_by_fill = _latest_broker_by_fill_id(_rows_with_lines(broker_rows))
    j46_by_fill = _latest_by_key(_rows_with_lines(j46_rows), "fill_id")
    rows: list[dict[str, Any]] = []
    for candidate_id, candidate in sorted(candidates.items()):
        rows.append(
            build_risk_context_row(
                row_type="candidate_risk_context",
                source_row=candidate,
                broker_row=broker_by_candidate.get(candidate_id),
                config=config,
                profile=profile,
                sprt_state=sprt_state,
                generated_at_utc=generated_at_utc,
            )
        )
    for fill_id, broker_row in sorted(broker_by_fill.items()):
        if broker_row.get("audit_scope") != "filled_trade_reconciliation":
            continue
        source = {
            "fill_id": fill_id,
            "trade_id": broker_row.get("trade_id"),
            "symbol": broker_row.get("symbol"),
            "broker_symbol": broker_row.get("broker_symbol"),
            "decision_time_utc": broker_row.get("decision_time_utc"),
            "created_at_utc": broker_row.get("created_at_utc"),
        }
        rows.append(
            build_risk_context_row(
                row_type="filled_risk_context",
                source_row=source,
                broker_row=broker_row,
                j46_row=j46_by_fill.get(fill_id),
                config=config,
                profile=profile,
                sprt_state=sprt_state,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("s79_side_aware_context_status") or "UNKNOWN") for row in rows)
    row_type_counts = Counter(str(row.get("row_type") or "UNKNOWN") for row in rows)
    symbol_counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    label_counts = Counter(str(row.get("ml_label_eligibility") or "UNKNOWN") for row in rows)
    action_counts: Counter[str] = Counter()
    limitation_counts: Counter[str] = Counter()
    for row in rows:
        action_counts.update(row.get("action_required_codes") or [])
        limitation_counts.update(row.get("documented_limitation_codes") or [])
    return {
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "row_type_counts": dict(row_type_counts),
        "symbol_counts": dict(symbol_counts),
        "ml_label_eligibility_counts": dict(label_counts),
        "actual_r_claim_allowed_rows": sum(1 for row in rows if row.get("actual_r_claim_allowed") is True),
        "action_required_code_counts": dict(action_counts),
        "documented_limitation_code_counts": dict(limitation_counts),
    }
