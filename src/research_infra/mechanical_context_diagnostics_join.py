"""Mechanical/context diagnostics join helpers for LTO-020.

This joins scattered baseline, proximity, liquidity, displacement, and
structure-divergence rows into one candidate-scoped research substrate. It is
read-only and shadow-only: no orders, no AI calls, no canaries, no paid data
calls, and no live decision impact.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "mechanical_context_diagnostics_join_v1"
CLASSIFIER_VERSION = "mechanical_context_diagnostics_join_classifier_v1"

COMPLETE = "MECHANICAL_CONTEXT_DIAGNOSTICS_JOINED"
PARTIAL = "MECHANICAL_CONTEXT_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED"
ACTION_REQUIRED = "MECHANICAL_CONTEXT_DIAGNOSTICS_ACTION_REQUIRED"

NEAR_TIME_SECONDS = 90
DISPLACEMENT_MAX_AGE_SECONDS = 6 * 60 * 60

SYMBOL_ALIASES = {
    "NDX100": "NAS100",
    "NAS100": "NAS100",
    "US30_CASH": "US30",
    "US30": "US30",
}


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


def _jsonish(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _stable_hash(*parts: Any) -> str:
    return hashlib.sha256("|".join(_jsonish(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def canonical_symbol(value: Any) -> str:
    raw = str(value or "").strip()
    return SYMBOL_ALIASES.get(raw.upper(), raw)


def _normalize_direction(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if text in {"LONG", "BUY", "BULLISH"}:
        return "LONG"
    if text in {"SHORT", "SELL", "BEARISH"}:
        return "SHORT"
    return text or None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("timestamp_logged"))
        or parse_utc(row.get("timestamp_utc"))
        or parse_utc(row.get("timestamp"))
        or parse_utc(row.get("logged_at"))
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("candle_time"))
        or parse_utc(row.get("ts"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]], key: str = "candidate_id") -> dict[str, dict[str, Any]]:
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


def _latest_broker_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        priority = 1 if row.get("actual_r_claim_allowed") is True and row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED" else 0
        item_key = (priority, _clock(item), line_no)
        previous = latest.get(candidate_id)
        prev_priority = 1 if previous and previous.get("actual_r_claim_allowed") is True and previous.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED" else 0
        previous_key = (prev_priority, _clock(previous or {}), int((previous or {}).get("_line_no") or 0))
        if item_key >= previous_key:
            latest[candidate_id] = item
    return latest


def _row_symbol(row: dict[str, Any]) -> str:
    return canonical_symbol(row.get("symbol") or row.get("broker_symbol"))


def _row_time(row: dict[str, Any], fields: tuple[str, ...]) -> datetime | None:
    for field in fields:
        parsed = parse_utc(row.get(field))
        if parsed is not None:
            return parsed
    return None


def _observable_until(candidate: dict[str, Any], decision_dt: datetime) -> datetime:
    created = parse_utc(candidate.get("created_at_utc"))
    same_close = decision_dt + timedelta(seconds=NEAR_TIME_SECONDS)
    if created is None:
        return same_close
    return max(same_close, created + timedelta(seconds=NEAR_TIME_SECONDS))


def _logged_at(row: dict[str, Any]) -> datetime | None:
    return (
        parse_utc(row.get("logged_at"))
        or parse_utc(row.get("timestamp_logged"))
        or parse_utc(row.get("timestamp_utc"))
        or parse_utc(row.get("timestamp"))
    )


def _is_observable(row: dict[str, Any], candidate: dict[str, Any], decision_dt: datetime) -> bool:
    logged = _logged_at(row)
    if logged is None:
        return True
    return logged <= _observable_until(candidate, decision_dt)


def select_nearest_by_symbol_time(
    *,
    candidate: dict[str, Any],
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    time_fields: tuple[str, ...],
    tolerance_seconds: int = NEAR_TIME_SECONDS,
    framework: str | None = None,
) -> dict[str, Any]:
    decision_dt = parse_utc(candidate.get("decision_time_utc"))
    if decision_dt is None:
        return {"join_status": "CONTEXT_JOIN_MISSING_DECISION_TIME_UNPARSEABLE", "row": None, "offset_seconds": None, "source_line": None}
    symbol = canonical_symbol(candidate.get("symbol") or candidate.get("broker_symbol"))
    best: tuple[float, int, dict[str, Any], datetime] | None = None
    for line_no, row in _rows_with_lines(rows):
        if _row_symbol(row) != symbol:
            continue
        if framework and str(row.get("framework") or "") and str(row.get("framework")) != framework:
            continue
        if not _is_observable(row, candidate, decision_dt):
            continue
        ts = _row_time(row, time_fields)
        if ts is None:
            continue
        distance = abs((ts - decision_dt).total_seconds())
        if distance > tolerance_seconds:
            continue
        if best is None or distance < best[0] or (distance == best[0] and line_no > best[1]):
            best = (distance, line_no, row, ts)
    if best is None:
        return {"join_status": "CONTEXT_JOIN_MISSING_WITHIN_TIME_WINDOW", "row": None, "offset_seconds": None, "source_line": None}
    _, line_no, row, ts = best
    return {"join_status": "CONTEXT_NEAR_TIME_JOINED", "row": row, "offset_seconds": int((ts - decision_dt).total_seconds()), "source_line": line_no}


def _geometry_delta(candidate: dict[str, Any], row: dict[str, Any]) -> float:
    params = candidate.get("trade_parameters") if isinstance(candidate.get("trade_parameters"), dict) else {}
    pairs = (
        ("entry_price", "entry_price"),
        ("stop_loss", "stop_loss"),
        ("take_profit_1", "take_profit_1"),
    )
    total = 0.0
    for left, right in pairs:
        a = _float_or_none(params.get(left))
        b = _float_or_none(row.get(right))
        if a is None or b is None:
            total += 1_000_000.0
        else:
            total += abs(a - b)
    return total


def select_liquidity_context(
    *,
    candidate: dict[str, Any],
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    decision_dt = parse_utc(candidate.get("decision_time_utc"))
    if decision_dt is None:
        return {"join_status": "CONTEXT_JOIN_MISSING_DECISION_TIME_UNPARSEABLE", "row": None, "offset_seconds": None, "source_line": None}
    framework = str(candidate.get("framework") or "")
    best: tuple[float, float, int, dict[str, Any], datetime] | None = None
    for line_no, row in _rows_with_lines(rows):
        if framework and str(row.get("framework") or "") and str(row.get("framework")) != framework:
            continue
        if not _is_observable(row, candidate, decision_dt):
            continue
        ts = _row_time(row, ("timestamp",))
        if ts is None:
            continue
        distance = abs((ts - decision_dt).total_seconds())
        if distance > NEAR_TIME_SECONDS:
            continue
        geometry = _geometry_delta(candidate, row)
        if geometry > max(1e-7, abs(_float_or_none(row.get("m15_atr")) or 0.0) * 0.05):
            continue
        item = (distance, geometry, line_no, row, ts)
        if best is None or item[:3] < best[:3]:
            best = item
    if best is None:
        return {"join_status": "CONTEXT_JOIN_MISSING_WITHIN_TIME_WINDOW", "row": None, "offset_seconds": None, "source_line": None}
    _, _, line_no, row, ts = best
    return {"join_status": "CONTEXT_NEAR_TIME_GEOMETRY_JOINED", "row": row, "offset_seconds": int((ts - decision_dt).total_seconds()), "source_line": line_no}


def select_displacement_context(
    *,
    candidate: dict[str, Any],
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    decision_dt = parse_utc(candidate.get("decision_time_utc"))
    if decision_dt is None:
        return {"join_status": "DISPLACEMENT_JOIN_MISSING_DECISION_TIME_UNPARSEABLE", "row": None, "age_seconds": None, "source_line": None}
    symbol = canonical_symbol(candidate.get("symbol") or candidate.get("broker_symbol"))
    best: tuple[float, int, dict[str, Any], datetime] | None = None
    for line_no, row in _rows_with_lines(rows):
        if _row_symbol(row) != symbol:
            continue
        if not _is_observable(row, candidate, decision_dt):
            continue
        ts = parse_utc(row.get("timestamp_utc"))
        if ts is None or ts > decision_dt:
            continue
        age = (decision_dt - ts).total_seconds()
        if age > DISPLACEMENT_MAX_AGE_SECONDS:
            continue
        item = (age, line_no, row, ts)
        if best is None or age < best[0] or (age == best[0] and line_no > best[1]):
            best = item
    if best is None:
        return {"join_status": "DISPLACEMENT_JOIN_MISSING_WITHIN_ASOF_WINDOW", "row": None, "age_seconds": None, "source_line": None}
    age, line_no, row, _ = best
    return {"join_status": "DISPLACEMENT_ASOF_JOINED", "row": row, "age_seconds": int(age), "source_line": line_no}


def select_structure_context(
    *,
    candidate: dict[str, Any],
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    decision_dt = parse_utc(candidate.get("decision_time_utc"))
    if decision_dt is None:
        return {"join_status": "STRUCTURE_DIVERGENCE_JOIN_MISSING_DECISION_TIME_UNPARSEABLE", "timeframes": {}, "source_lines": []}
    symbol = canonical_symbol(candidate.get("symbol") or candidate.get("broker_symbol"))
    best_by_timeframe: dict[str, tuple[float, int, dict[str, Any], datetime]] = {}
    for line_no, row in _rows_with_lines(rows):
        if _row_symbol(row) != symbol:
            continue
        if not _is_observable(row, candidate, decision_dt):
            continue
        ts = parse_utc(row.get("ts"))
        if ts is None:
            continue
        distance = abs((ts - decision_dt).total_seconds())
        if distance > NEAR_TIME_SECONDS:
            continue
        timeframe = str(row.get("timeframe") or "UNKNOWN")
        item = (distance, line_no, row, ts)
        prev = best_by_timeframe.get(timeframe)
        if prev is None or distance < prev[0] or (distance == prev[0] and line_no > prev[1]):
            best_by_timeframe[timeframe] = item
    if not best_by_timeframe:
        return {"join_status": "STRUCTURE_DIVERGENCE_JOIN_MISSING_WITHIN_TIME_WINDOW", "timeframes": {}, "source_lines": []}
    timeframes: dict[str, dict[str, Any]] = {}
    source_lines: list[int] = []
    for timeframe, (_, line_no, row, ts) in sorted(best_by_timeframe.items()):
        source_lines.append(line_no)
        timeframes[timeframe] = {
            "ts": ts.isoformat(),
            "logged_at": row.get("logged_at"),
            "v1_direction": row.get("v1_direction"),
            "v2_direction": row.get("v2_direction"),
            "production_label": row.get("production_label"),
            "v2_score": row.get("v2_score"),
            "v2_dead_zone": row.get("v2_dead_zone"),
            "counts": row.get("counts") if isinstance(row.get("counts"), dict) else None,
        }
    return {
        "join_status": "STRUCTURE_DIVERGENCE_TIMEFRAME_ROWS_JOINED",
        "timeframes": timeframes,
        "source_lines": source_lines,
    }


def _pool_summary(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    pools = row.get("pools_checked") if isinstance(row.get("pools_checked"), list) else []
    type_counts = Counter(str(pool.get("type") or "UNKNOWN") for pool in pools if isinstance(pool, dict))
    violating = [pool for pool in pools if isinstance(pool, dict) and pool.get("violating") is True]
    distances = [_float_or_none(pool.get("distance_to_sl")) for pool in pools if isinstance(pool, dict)]
    distances = [value for value in distances if value is not None]
    violating_distances = [_float_or_none(pool.get("distance_to_sl")) for pool in violating]
    violating_distances = [value for value in violating_distances if value is not None]
    return {
        "pools_checked_count": len(pools),
        "violating_pool_count": len(violating),
        "pool_type_counts": dict(type_counts),
        "nearest_pool_distance_to_sl": min(distances) if distances else None,
        "nearest_violating_distance_to_sl": min(violating_distances) if violating_distances else None,
        "violating_pool_types": sorted({str(pool.get("type") or "UNKNOWN") for pool in violating if isinstance(pool, dict)}),
    }


def _dumb_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {"join_status": join.get("join_status"), "source_line": None, "offset_seconds": join.get("offset_seconds")}
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "hypothesis_id": row.get("hypothesis_id"),
        "timestamp_utc": row.get("timestamp_utc"),
        "candle_time": row.get("candle_time"),
        "symbol": canonical_symbol(row.get("symbol")),
        "kz": row.get("kz"),
        "direction": _normalize_direction(row.get("direction")),
        "bos_direction": row.get("bos_direction"),
        "bos_h1_time": row.get("bos_h1_time"),
        "entry": _float_or_none(row.get("entry")),
        "sl": _float_or_none(row.get("sl")),
        "tp": _float_or_none(row.get("tp")),
        "atr_m15": _float_or_none(row.get("atr_m15")),
        "impulse_range": _float_or_none(row.get("impulse_range")),
        "retrace_pct": _float_or_none(row.get("retrace_pct")),
        "post_decision_comparator_outcome": {
            "outcome": row.get("outcome"),
            "realized_r": _float_or_none(row.get("realized_r")),
            "time_in_trade_bars": _int_or_none(row.get("time_in_trade_bars")),
            "exit_time": row.get("exit_time"),
            "feature_safe": False,
        },
    }


def _proximity_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {"join_status": join.get("join_status"), "source_line": None, "offset_seconds": join.get("offset_seconds")}
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp_logged": row.get("timestamp_logged"),
        "candle_time": row.get("candle_time"),
        "symbol": canonical_symbol(row.get("symbol")),
        "kill_zone": row.get("kill_zone"),
        "trade_direction": _normalize_direction(row.get("trade_direction")),
        "proximity": row.get("proximity"),
        "distance_to_ob": _float_or_none(row.get("distance_to_ob")),
        "distance_atr_ratio": _float_or_none(row.get("distance_atr_ratio")),
        "atr_used": _float_or_none(row.get("atr_used")),
        "atr_source": row.get("atr_source"),
        "h1_ob_count": _int_or_none(row.get("h1_ob_count")),
        "m15_ob_count": _int_or_none(row.get("m15_ob_count")),
        "relevant_ob_count": _int_or_none(row.get("relevant_ob_count")),
    }


def _liquidity_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {"join_status": join.get("join_status"), "source_line": None, "offset_seconds": join.get("offset_seconds")}
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp": row.get("timestamp"),
        "source_identity_status": "PRICE_GEOMETRY_JOIN_NO_SYMBOL_IN_SOURCE",
        "direction": _normalize_direction(row.get("direction")),
        "entry_price": _float_or_none(row.get("entry_price")),
        "stop_loss": _float_or_none(row.get("stop_loss")),
        "take_profit_1": _float_or_none(row.get("take_profit_1")),
        "framework": row.get("framework"),
        "setup_grade": row.get("setup_grade"),
        "m15_atr": _float_or_none(row.get("m15_atr")),
        "margin_required": _float_or_none(row.get("margin_required")),
        "decision": row.get("decision"),
        "pool_summary": _pool_summary(row),
    }


def _displacement_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {"join_status": join.get("join_status"), "source_line": None, "age_seconds": join.get("age_seconds")}
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "age_seconds": join.get("age_seconds"),
        "timestamp_utc": row.get("timestamp_utc"),
        "logged_at": row.get("logged_at"),
        "symbol": canonical_symbol(row.get("symbol")),
        "direction": _normalize_direction(row.get("direction")),
        "classification": row.get("classification"),
        "displacement_ratio": _float_or_none(row.get("displacement_ratio")),
        "body": _float_or_none(row.get("body")),
        "avg_body_20": _float_or_none(row.get("avg_body_20")),
        "body_to_atr": _float_or_none(row.get("body_to_atr")),
        "atr_14": _float_or_none(row.get("atr_14")),
        "kill_zone": row.get("kill_zone"),
        "correlation_count": _int_or_none(row.get("correlation_count")),
        "correlated_with": row.get("correlated_with") if isinstance(row.get("correlated_with"), list) else [],
    }


def _path_context(path_row: dict[str, Any] | None) -> dict[str, Any]:
    if not path_row:
        return {"join_status": "NO_CANDIDATE_PATH_ROW"}
    return {
        "join_status": "PATH_JOINED",
        "path_label": path_row.get("path_label"),
        "touched_entry": path_row.get("touched_entry"),
        "hit_tp1": path_row.get("hit_tp1"),
        "hit_sl": path_row.get("hit_sl"),
        "path_ambiguity_status": path_row.get("path_ambiguity_status"),
        "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
    }


def _broker_actual_allowed(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("actual_r_claim_allowed") is True and row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED")


def _ml_label_eligibility(*, broker_row: dict[str, Any] | None, path_row: dict[str, Any] | None) -> str:
    if _broker_actual_allowed(broker_row):
        return "ACCOUNT_HISTORY_LABEL_WITH_MECHANICAL_CONTEXT"
    if path_row:
        return "SYNTHETIC_PATH_LABEL_WITH_MECHANICAL_CONTEXT_NOT_ACCOUNT_HISTORY"
    return "FEATURE_CONTEXT_ONLY_LABEL_NOT_AVAILABLE"


def build_mechanical_context_row(
    *,
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None = None,
    broker_row: dict[str, Any] | None = None,
    dumb_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    proximity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    liquidity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    displacement_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    structure_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    symbol = canonical_symbol(candidate.get("symbol") or candidate.get("broker_symbol"))
    side = _normalize_direction(candidate.get("side"))
    framework = str(candidate.get("framework") or "")
    dumb_context = _dumb_context(
        select_nearest_by_symbol_time(
            candidate=candidate,
            rows=dumb_rows,
            time_fields=("candle_time", "timestamp_utc"),
            tolerance_seconds=NEAR_TIME_SECONDS,
        )
    )
    proximity_context = _proximity_context(
        select_nearest_by_symbol_time(
            candidate=candidate,
            rows=proximity_rows,
            time_fields=("candle_time", "timestamp_logged"),
            tolerance_seconds=NEAR_TIME_SECONDS,
        )
    )
    liquidity_context = _liquidity_context(select_liquidity_context(candidate=candidate, rows=liquidity_rows))
    displacement_context = _displacement_context(select_displacement_context(candidate=candidate, rows=displacement_rows))
    structure_divergence_context = select_structure_context(candidate=candidate, rows=structure_rows)
    path_context = _path_context(path_row)

    action_required: list[str] = []
    documented_limitations: list[str] = []
    mismatch_codes: list[str] = []
    for source, context in (
        ("DUMB_BASELINE", dumb_context),
        ("PROXIMITY", proximity_context),
        ("LIQUIDITY_DISTANCE", liquidity_context),
        ("DISPLACEMENT", displacement_context),
    ):
        if not str(context.get("join_status") or "").endswith("JOINED"):
            documented_limitations.append(f"{source}_CONTEXT_MISSING_WITHIN_ASOF_WINDOW")
    if structure_divergence_context.get("join_status") != "STRUCTURE_DIVERGENCE_TIMEFRAME_ROWS_JOINED":
        documented_limitations.append("STRUCTURE_DIVERGENCE_CONTEXT_MISSING_WITHIN_ASOF_WINDOW")

    for code, observed in (
        ("DUMB_BASELINE_DIRECTION_MISMATCH_SIDE", dumb_context.get("direction")),
        ("PROXIMITY_DIRECTION_MISMATCH_SIDE", proximity_context.get("trade_direction")),
        ("LIQUIDITY_DISTANCE_DIRECTION_MISMATCH_SIDE", liquidity_context.get("direction")),
    ):
        if side and observed and side != observed:
            mismatch_codes.append(code)
            action_required.append(code)
    displacement_direction = displacement_context.get("direction")
    if side and displacement_direction and side != displacement_direction:
        mismatch_codes.append("DISPLACEMENT_DIRECTION_DIFFERS_FROM_SIDE_CONTEXT")

    join_statuses = {
        "dumb_baseline": dumb_context.get("join_status"),
        "proximity": proximity_context.get("join_status"),
        "liquidity_distance": liquidity_context.get("join_status"),
        "displacement": displacement_context.get("join_status"),
        "structure_divergence": structure_divergence_context.get("join_status"),
    }
    status = ACTION_REQUIRED if action_required else COMPLETE
    if not action_required and any("MISSING" in str(value or "") for value in join_statuses.values()):
        status = PARTIAL

    actual_allowed = _broker_actual_allowed(broker_row)
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        candidate.get("candidate_id"),
        symbol,
        candidate.get("broker_symbol"),
        candidate.get("decision_time_utc"),
        candidate.get("created_at_utc"),
        candidate.get("final_outcome_at_log"),
        side,
        framework,
        path_context,
        (broker_row or {}).get("row_key"),
        dumb_context,
        proximity_context,
        liquidity_context,
        displacement_context,
        structure_divergence_context,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("mechanical_context_diagnostics_join", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-020",
        "follow_id": "LIVE-FOLLOW-017",
        "row_type": "candidate_mechanical_context_diagnostics",
        "mechanical_context_status": status,
        "candidate_id": candidate.get("candidate_id"),
        "symbol": symbol,
        "broker_symbol": candidate.get("broker_symbol") or symbol,
        "side": side,
        "framework": framework or None,
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "candidate_final_outcome_at_log": candidate.get("final_outcome_at_log"),
        "path_context": path_context,
        "account_history_join_status": "ACCOUNT_HISTORY_REALIZED" if actual_allowed else "NO_ACCOUNT_HISTORY_REALIZED_FOR_ROW",
        "actual_r_claim_allowed": actual_allowed,
        "broker_actual_r": (broker_row or {}).get("broker_actual_r") if actual_allowed else None,
        "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
        "mechanical_context_join_statuses": join_statuses,
        "dumb_baseline_context": dumb_context,
        "proximity_context": proximity_context,
        "liquidity_distance_context": liquidity_context,
        "displacement_context": displacement_context,
        "structure_divergence_context": structure_divergence_context,
        "mismatch_codes": sorted(set(mismatch_codes)),
        "documented_limitation_codes": sorted(set(documented_limitations)),
        "action_required_codes": sorted(set(action_required)),
        "claim_boundary": (
            "Decision-time mechanical/context diagnostics are ML features. Dumb-baseline and path outcomes "
            "are post-decision discovery labels/comparators only and must not be used as live features."
        ),
        "ml_feature_role": "ML_MECHANICAL_BASELINE_AND_CONTEXT_DIAGNOSTICS",
        "ml_label_eligibility": _ml_label_eligibility(broker_row=broker_row, path_row=path_row),
        "ml_no_leak_boundary": "ASOF_CONTEXT_FEATURES_ONLY_POST_DECISION_BASELINE_AND_PATH_OUTCOMES_EXCLUDED_FROM_FEATURES",
        "evidence_class": "MECHANICAL_CONTEXT_DIAGNOSTICS",
        "no_leak_status": "MECHANICAL_CONTEXT_AUDIT_NOT_DECISION_CHANGE",
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


def build_mechanical_context_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    broker_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    dumb_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    proximity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    liquidity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    displacement_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    structure_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    candidates = _latest_by_candidate(_rows_with_lines(candidate_rows))
    paths = _latest_by_candidate(_rows_with_lines(path_rows))
    brokers = _latest_broker_by_candidate(_rows_with_lines(broker_rows))
    rows: list[dict[str, Any]] = []
    for candidate_id, candidate in sorted(candidates.items()):
        rows.append(
            build_mechanical_context_row(
                candidate=candidate,
                path_row=paths.get(candidate_id),
                broker_row=brokers.get(candidate_id),
                dumb_rows=dumb_rows,
                proximity_rows=proximity_rows,
                liquidity_rows=liquidity_rows,
                displacement_rows=displacement_rows,
                structure_rows=structure_rows,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("mechanical_context_status") or "UNKNOWN") for row in rows)
    symbol_counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    framework_counts = Counter(str(row.get("framework") or "UNKNOWN") for row in rows)
    final_outcome_counts = Counter(str(row.get("candidate_final_outcome_at_log") or "UNKNOWN") for row in rows)
    label_counts = Counter(str(row.get("ml_label_eligibility") or "UNKNOWN") for row in rows)
    join_counts: dict[str, Counter[str]] = defaultdict(Counter)
    action_counts: Counter[str] = Counter()
    mismatch_counts: Counter[str] = Counter()
    limitation_counts: Counter[str] = Counter()
    proximity_by_path: dict[str, Counter[str]] = defaultdict(Counter)
    baseline_r_by_path: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        statuses = row.get("mechanical_context_join_statuses") if isinstance(row.get("mechanical_context_join_statuses"), dict) else {}
        for source, status in statuses.items():
            join_counts[source][str(status or "UNKNOWN")] += 1
        action_counts.update(row.get("action_required_codes") or [])
        mismatch_counts.update(row.get("mismatch_codes") or [])
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        path_context = row.get("path_context") if isinstance(row.get("path_context"), dict) else {}
        path_label = str(path_context.get("path_label") or "NO_PATH_LABEL")
        prox = row.get("proximity_context") if isinstance(row.get("proximity_context"), dict) else {}
        if prox.get("proximity"):
            proximity_by_path[path_label][str(prox.get("proximity"))] += 1
        dumb = row.get("dumb_baseline_context") if isinstance(row.get("dumb_baseline_context"), dict) else {}
        outcome = dumb.get("post_decision_comparator_outcome") if isinstance(dumb.get("post_decision_comparator_outcome"), dict) else {}
        realized = _float_or_none(outcome.get("realized_r"))
        if realized is not None:
            baseline_r_by_path[path_label].append(realized)
    return {
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "symbol_counts": dict(symbol_counts),
        "framework_counts": dict(framework_counts),
        "final_outcome_counts": dict(final_outcome_counts),
        "ml_label_eligibility_counts": dict(label_counts),
        "mechanical_context_join_counts": {key: dict(value) for key, value in sorted(join_counts.items())},
        "action_required_code_counts": dict(action_counts),
        "mismatch_code_counts": dict(mismatch_counts),
        "documented_limitation_code_counts": dict(limitation_counts),
        "proximity_by_path_label": {key: dict(value) for key, value in sorted(proximity_by_path.items())},
        "dumb_baseline_realized_r_by_path_label": {
            key: {
                "n": len(values),
                "mean_r": round(sum(values) / len(values), 6) if values else None,
                "sum_r": round(sum(values), 6) if values else None,
            }
            for key, values in sorted(baseline_r_by_path.items())
        },
        "actual_r_claim_allowed_rows": sum(1 for row in rows if row.get("actual_r_claim_allowed") is True),
        "path_joined_rows": sum(1 for row in rows if isinstance(row.get("path_context"), dict) and row["path_context"].get("join_status") == "PATH_JOINED"),
    }
