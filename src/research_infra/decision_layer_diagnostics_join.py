"""Decision-layer diagnostics join helpers for LTO-019.

This module joins candidate rows to already-written observation logs from the
AI/candidate feature path, D1-bias lag monitor, direction-emission audit,
SL-beyond-OB audit, touch-count gate audit, and cross-instrument correlation
gate audit. It is research/tooling only: no orders, no AI calls, no canaries,
no paid data calls, and no live decision impact.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "decision_layer_diagnostics_join_v1"
CLASSIFIER_VERSION = "decision_layer_diagnostics_join_classifier_v2"

COMPLETE = "DECISION_DIAGNOSTICS_JOINED"
PARTIAL = "DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED"
ACTION_REQUIRED = "DECISION_DIAGNOSTICS_ACTION_REQUIRED"

NEAR_TIME_SECONDS = 90
D1_BIAS_TIME_SECONDS = 15 * 60

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
    payload = "|".join(_jsonish(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("timestamp_utc"))
        or parse_utc(row.get("logged_at_utc"))
        or parse_utc(row.get("timestamp"))
        or parse_utc(row.get("decision_time_utc"))
        or parse_utc(row.get("candle_close_utc"))
        or parse_utc(row.get("candle_time_utc"))
        or parse_utc(row.get("candle_time"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        item_key = (_clock(item), line_no)
        previous = latest.get(candidate_id)
        previous_key = (_clock(previous or {}), int((previous or {}).get("_line_no") or 0))
        if item_key >= previous_key:
            latest[candidate_id] = item
    return latest


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


def _row_symbol(row: dict[str, Any]) -> str:
    return canonical_symbol(
        row.get("symbol")
        or row.get("instrument")
        or row.get("broker_symbol")
        or row.get("candidate_symbol")
    )


def _row_time(row: dict[str, Any], fields: tuple[str, ...]) -> datetime | None:
    for field in fields:
        parsed = parse_utc(row.get(field))
        if parsed is not None:
            return parsed
    return None


def select_nearest_diagnostic(
    *,
    symbol: str,
    decision_time_utc: Any,
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    time_fields: tuple[str, ...],
    tolerance_seconds: int = NEAR_TIME_SECONDS,
    framework: str | None = None,
) -> dict[str, Any]:
    decision_dt = parse_utc(decision_time_utc)
    if decision_dt is None:
        return {
            "join_status": "DIAGNOSTIC_JOIN_MISSING_DECISION_TIME_UNPARSEABLE",
            "row": None,
            "offset_seconds": None,
            "source_line": None,
        }
    normalized_symbol = canonical_symbol(symbol)
    best: tuple[float, int, dict[str, Any], datetime] | None = None
    for line_no, row in _rows_with_lines(rows):
        if _row_symbol(row) != normalized_symbol:
            continue
        if framework and str(row.get("framework") or "") and str(row.get("framework")) != framework:
            continue
        ts = _row_time(row, time_fields)
        if ts is None:
            continue
        distance = abs((ts - decision_dt).total_seconds())
        if distance > tolerance_seconds:
            continue
        item = (distance, line_no, row, ts)
        if best is None or distance < best[0] or (distance == best[0] and line_no > best[1]):
            best = item
    if best is None:
        return {
            "join_status": "DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW",
            "row": None,
            "offset_seconds": None,
            "source_line": None,
        }
    _, line_no, row, ts = best
    return {
        "join_status": "DIAGNOSTIC_NEAR_TIME_JOINED",
        "row": row,
        "offset_seconds": int((ts - decision_dt).total_seconds()),
        "source_line": line_no,
    }


def _candidate_features_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": join.get("join_status"),
            "source_line": None,
            "offset_seconds": join.get("offset_seconds"),
        }
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp_utc": row.get("timestamp_utc"),
        "candle_close_utc": row.get("candle_close_utc"),
        "evaluation_id": row.get("evaluation_id"),
        "decision": row.get("decision"),
        "framework": row.get("framework"),
        "setup_grade": row.get("setup_grade"),
        "ai_decision": row.get("ai_decision"),
        "ai_direction_evaluated": _normalize_direction(row.get("ai_direction_evaluated")),
        "ai_no_trade_reason": row.get("ai_no_trade_reason"),
        "daily_bias_direction": row.get("daily_bias_direction"),
        "daily_bias_confidence": row.get("daily_bias_confidence"),
        "h4_aligned": row.get("h4_aligned"),
        "m15_choch_detected": row.get("m15_choch_detected"),
        "c_gate_result": row.get("c_gate_result") if isinstance(row.get("c_gate_result"), dict) else None,
        "pre_ai_gate_skipped": row.get("pre_ai_gate_skipped"),
        "pre_ai_gate_reason": row.get("pre_ai_gate_reason"),
        "mso": {
            "h1_structure_direction": row.get("mso_h1_structure_direction"),
            "m15_structure_direction": row.get("mso_m15_structure_direction"),
            "d1_structure_direction": row.get("mso_d1_structure_direction"),
            "h1_unmitigated_ob_count": row.get("mso_h1_unmitigated_ob_count"),
            "h1_ob_touch_counts": row.get("mso_h1_ob_touch_counts"),
            "h1_nearest_ob_distance_atr": row.get("mso_h1_nearest_ob_distance_atr"),
            "h1_fvg_count": row.get("mso_h1_fvg_count"),
            "m15_fvg_count": row.get("mso_m15_fvg_count"),
            "h1_atr_14": row.get("mso_h1_atr_14"),
            "m15_atr_14": row.get("mso_m15_atr_14"),
            "d1_atr_14": row.get("mso_d1_atr_14"),
            "pd_equilibrium_50": row.get("mso_pd_equilibrium_50"),
            "pd_current_zone": row.get("mso_pd_current_zone"),
            "m15_clv_current": row.get("mso_m15_clv_current"),
            "m15_clv_avg_5": row.get("mso_m15_clv_avg_5"),
            "m15_bvc_buy_fraction": row.get("mso_m15_bvc_buy_fraction"),
            "m15_net_flow_5": row.get("mso_m15_net_flow_5"),
            "m15_session_vol_ratio": row.get("mso_m15_session_vol_ratio"),
            "detected_sweeps_count": row.get("mso_detected_sweeps_count"),
        },
    }


def _d1_bias_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": join.get("join_status"),
            "source_line": None,
            "offset_seconds": join.get("offset_seconds"),
        }
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp": row.get("timestamp"),
        "d1_bias": row.get("d1_bias"),
        "h4_bias": row.get("h4_bias"),
        "h1_direction": row.get("h1_direction"),
        "kill_zone": row.get("kill_zone"),
        "h4_missing": row.get("h4_missing"),
        "rolling_N_consecutive": row.get("rolling_N_consecutive"),
    }


def _direction_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": join.get("join_status"),
            "source_line": None,
            "offset_seconds": join.get("offset_seconds"),
        }
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "logged_at_utc": row.get("logged_at_utc"),
        "candle_time_utc": row.get("candle_time_utc"),
        "proposed_direction": _normalize_direction(row.get("proposed_direction")),
        "xau_d1_direction": row.get("xau_d1_direction"),
        "correlation_to_xau": _float_or_none(row.get("correlation_to_xau")),
        "direction_aligned_with_xau": row.get("direction_aligned_with_xau"),
        "kill_zone": row.get("kill_zone"),
        "confidence_score": row.get("confidence_score"),
        "framework": row.get("framework"),
    }


def _sl_beyond_ob_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": join.get("join_status"),
            "source_line": None,
            "offset_seconds": join.get("offset_seconds"),
        }
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp_utc": row.get("timestamp_utc"),
        "candle_time": row.get("candle_time"),
        "framework": row.get("framework"),
        "l2_decision": row.get("l2_decision"),
        "l2_reason": row.get("l2_reason"),
        "direction": _normalize_direction(row.get("direction")),
        "proposed_entry": _float_or_none(row.get("proposed_entry")),
        "proposed_sl": _float_or_none(row.get("proposed_sl")),
        "proposed_tp1": _float_or_none(row.get("proposed_tp1")),
        "ob_low": _float_or_none(row.get("ob_low")),
        "ob_high": _float_or_none(row.get("ob_high")),
        "zone_label": row.get("zone_label"),
        "h1_atr": _float_or_none(row.get("h1_atr")),
        "confidence_score": row.get("confidence_score"),
    }


def _touch_count_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": join.get("join_status"),
            "source_line": None,
            "offset_seconds": join.get("offset_seconds"),
        }
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp_utc": row.get("timestamp_utc"),
        "candle_time": row.get("candle_time"),
        "symbol": canonical_symbol(row.get("symbol")),
        "raw_symbol": row.get("symbol"),
        "framework": row.get("framework"),
        "gate_target_ob_touch": _int_or_none(row.get("gate_target_ob_touch")),
        "gate_threshold_at_eval": _int_or_none(row.get("gate_threshold_at_eval")),
        "gate_decision": row.get("gate_decision"),
        "gate_target_ob_id": row.get("gate_target_ob_id"),
        "candidate_id": row.get("candidate_id"),
        "ob_low": _float_or_none(row.get("ob_low")),
        "ob_high": _float_or_none(row.get("ob_high")),
        "ob_type": row.get("ob_type"),
    }


def _cross_instrument_correlation_context(join: dict[str, Any]) -> dict[str, Any]:
    row = join.get("row")
    if not isinstance(row, dict):
        return {
            "join_status": join.get("join_status"),
            "source_line": None,
            "offset_seconds": join.get("offset_seconds"),
        }
    return {
        "join_status": join.get("join_status"),
        "source_line": join.get("source_line"),
        "offset_seconds": join.get("offset_seconds"),
        "timestamp_utc": row.get("timestamp_utc"),
        "candidate_symbol": canonical_symbol(row.get("candidate_symbol")),
        "raw_candidate_symbol": row.get("candidate_symbol"),
        "candidate_direction": _normalize_direction(row.get("candidate_direction")),
        "evaluation_context": row.get("evaluation_context"),
        "gate_action": row.get("gate_action"),
        "risk_multiplier": _float_or_none(row.get("risk_multiplier")),
        "cluster_size": _int_or_none(row.get("cluster_size")),
        "correlated_positions": row.get("correlated_positions")
        if isinstance(row.get("correlated_positions"), list)
        else [],
        "threshold": _float_or_none(row.get("threshold")),
        "min_positions": _int_or_none(row.get("min_positions")),
        "reason": row.get("reason"),
    }


def _select_nearest_cross_instrument_correlation(
    *,
    symbol: str,
    side: str | None,
    decision_time_utc: Any,
    rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    decision_dt = parse_utc(decision_time_utc)
    if decision_dt is None:
        return {
            "join_status": "DIAGNOSTIC_JOIN_MISSING_DECISION_TIME_UNPARSEABLE",
            "row": None,
            "offset_seconds": None,
            "source_line": None,
        }
    normalized_symbol = canonical_symbol(symbol)
    normalized_side = _normalize_direction(side)
    best: tuple[float, int, dict[str, Any], datetime] | None = None
    for line_no, row in _rows_with_lines(rows):
        if canonical_symbol(row.get("candidate_symbol")) != normalized_symbol:
            continue
        row_direction = _normalize_direction(row.get("candidate_direction"))
        if normalized_side and row_direction and row_direction != normalized_side:
            continue
        ts = _row_time(row, ("timestamp_utc",))
        if ts is None:
            continue
        distance = abs((ts - decision_dt).total_seconds())
        if distance > NEAR_TIME_SECONDS:
            continue
        item = (distance, line_no, row, ts)
        if best is None or distance < best[0] or (distance == best[0] and line_no > best[1]):
            best = item
    if best is None:
        return {
            "join_status": "DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW",
            "row": None,
            "offset_seconds": None,
            "source_line": None,
        }
    _, line_no, row, ts = best
    return {
        "join_status": "DIAGNOSTIC_NEAR_TIME_JOINED",
        "row": row,
        "offset_seconds": int((ts - decision_dt).total_seconds()),
        "source_line": line_no,
    }


def _verification_context(candidate: dict[str, Any]) -> dict[str, Any]:
    verification = candidate.get("verification") if isinstance(candidate.get("verification"), dict) else {}
    raw_checks = verification.get("checks") if isinstance(verification.get("checks"), list) else []
    checks: list[dict[str, Any]] = []
    for check in raw_checks:
        if not isinstance(check, dict):
            continue
        checks.append(
            {
                "name": check.get("name"),
                "status": check.get("status"),
                "detail": check.get("detail"),
            }
        )
    fail_checks = [str(check.get("name")) for check in checks if str(check.get("status") or "").upper() == "FAIL"]
    pass_checks = [str(check.get("name")) for check in checks if str(check.get("status") or "").upper() == "PASS"]
    skip_checks = [str(check.get("name")) for check in checks if str(check.get("status") or "").upper() == "SKIP"]
    return {
        "passed": verification.get("passed"),
        "blocked_by": verification.get("blocked_by"),
        "checks": checks,
        "pass_checks": pass_checks,
        "fail_checks": fail_checks,
        "skip_checks": skip_checks,
        "l2_check_summary": {str(check.get("name")): check.get("status") for check in checks if check.get("name")},
    }


def _add_direction_mismatch(
    *,
    mismatch_codes: list[str],
    action_required: list[str],
    code: str,
    expected: Any,
    observed: Any,
) -> None:
    expected_direction = _normalize_direction(expected)
    observed_direction = _normalize_direction(observed)
    if expected_direction and observed_direction and expected_direction != observed_direction:
        mismatch_codes.append(code)
        action_required.append(code)


def _expected_touch_count(candidate: dict[str, Any]) -> bool:
    framework = str(candidate.get("framework") or "")
    if framework != "ob_retest":
        return False
    h1_setup = candidate.get("h1_setup") if isinstance(candidate.get("h1_setup"), dict) else {}
    poi_type = str(h1_setup.get("poi_type") or "").upper()
    return poi_type in {"", "OB"}


def build_decision_layer_diagnostics_row(
    *,
    candidate: dict[str, Any],
    candidate_feature_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    d1_bias_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    direction_emission_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    sl_beyond_ob_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    touch_count_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    cross_instrument_correlation_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    symbol = canonical_symbol(candidate.get("symbol") or candidate.get("broker_symbol"))
    decision_time = candidate.get("decision_time_utc")
    framework = str(candidate.get("framework") or "")
    side = _normalize_direction(candidate.get("side"))
    trade_params = candidate.get("trade_parameters") if isinstance(candidate.get("trade_parameters"), dict) else {}
    trade_parameter_direction = _normalize_direction(trade_params.get("direction"))

    feature_join = select_nearest_diagnostic(
        symbol=symbol,
        decision_time_utc=decision_time,
        rows=candidate_feature_rows,
        time_fields=("candle_close_utc", "timestamp_utc"),
        tolerance_seconds=NEAR_TIME_SECONDS,
        framework=framework,
    )
    d1_join = select_nearest_diagnostic(
        symbol=symbol,
        decision_time_utc=decision_time,
        rows=d1_bias_rows,
        time_fields=("timestamp",),
        tolerance_seconds=D1_BIAS_TIME_SECONDS,
    )
    direction_join = select_nearest_diagnostic(
        symbol=symbol,
        decision_time_utc=decision_time,
        rows=direction_emission_rows,
        time_fields=("candle_time_utc", "logged_at_utc"),
        tolerance_seconds=NEAR_TIME_SECONDS,
        framework=framework,
    )
    sl_join = select_nearest_diagnostic(
        symbol=symbol,
        decision_time_utc=decision_time,
        rows=sl_beyond_ob_rows,
        time_fields=("candle_time", "timestamp_utc"),
        tolerance_seconds=NEAR_TIME_SECONDS,
        framework=framework,
    )
    touch_join = select_nearest_diagnostic(
        symbol=symbol,
        decision_time_utc=decision_time,
        rows=touch_count_rows,
        time_fields=("candle_time", "timestamp_utc"),
        tolerance_seconds=NEAR_TIME_SECONDS,
        framework=framework,
    )
    cross_corr_join = _select_nearest_cross_instrument_correlation(
        symbol=symbol,
        side=side,
        decision_time_utc=decision_time,
        rows=cross_instrument_correlation_rows,
    )

    candidate_features_context = _candidate_features_context(feature_join)
    d1_bias_lag_context = _d1_bias_context(d1_join)
    direction_emission_context = _direction_context(direction_join)
    sl_beyond_ob_context = _sl_beyond_ob_context(sl_join)
    touch_count_context = _touch_count_context(touch_join)
    cross_instrument_correlation_context = _cross_instrument_correlation_context(cross_corr_join)
    verification_context = _verification_context(candidate)

    action_required: list[str] = []
    documented_limitations: list[str] = []
    mismatch_codes: list[str] = []

    if candidate_features_context.get("join_status") != "DIAGNOSTIC_NEAR_TIME_JOINED":
        action_required.append("CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE")
    elif candidate_features_context.get("decision") != "CANDIDATE" or candidate_features_context.get("ai_decision") != "CANDIDATE":
        action_required.append("CANDIDATE_FEATURES_DECISION_NOT_CANDIDATE")

    for source_name, context in (
        ("D1_BIAS_LAG", d1_bias_lag_context),
        ("DIRECTION_EMISSION", direction_emission_context),
        ("SL_BEYOND_OB", sl_beyond_ob_context),
    ):
        if context.get("join_status") != "DIAGNOSTIC_NEAR_TIME_JOINED":
            documented_limitations.append(f"{source_name}_DIAGNOSTIC_MISSING_WITHIN_TIME_WINDOW")

    if _expected_touch_count(candidate) and touch_count_context.get("join_status") != "DIAGNOSTIC_NEAR_TIME_JOINED":
        documented_limitations.append("TOUCH_COUNT_GATE_DIAGNOSTIC_MISSING_FOR_OB_RETEST")
    if cross_instrument_correlation_context.get("join_status") != "DIAGNOSTIC_NEAR_TIME_JOINED":
        documented_limitations.append(
            "CROSS_INSTRUMENT_CORRELATION_DIAGNOSTIC_OPTIONAL_MISSING_WITHIN_TIME_WINDOW"
        )

    _add_direction_mismatch(
        mismatch_codes=mismatch_codes,
        action_required=action_required,
        code="TRADE_PARAMETER_DIRECTION_MISMATCH_SIDE",
        expected=side,
        observed=trade_parameter_direction,
    )
    _add_direction_mismatch(
        mismatch_codes=mismatch_codes,
        action_required=action_required,
        code="AI_DIRECTION_MISMATCH_SIDE",
        expected=side,
        observed=candidate_features_context.get("ai_direction_evaluated"),
    )
    _add_direction_mismatch(
        mismatch_codes=mismatch_codes,
        action_required=action_required,
        code="DIRECTION_EMISSION_MISMATCH_SIDE",
        expected=side,
        observed=direction_emission_context.get("proposed_direction"),
    )
    _add_direction_mismatch(
        mismatch_codes=mismatch_codes,
        action_required=action_required,
        code="SL_BEYOND_OB_DIRECTION_MISMATCH_SIDE",
        expected=side,
        observed=sl_beyond_ob_context.get("direction"),
    )

    verification_passed = verification_context.get("passed")
    fail_checks = verification_context.get("fail_checks") or []
    blocked_by = verification_context.get("blocked_by")
    if verification_passed is True and fail_checks:
        action_required.append("VERIFICATION_PASSED_WITH_FAIL_CHECKS")
    if verification_passed is True and blocked_by:
        action_required.append("VERIFICATION_PASSED_WITH_BLOCKED_BY")
    if verification_passed is False and not fail_checks:
        action_required.append("VERIFICATION_FAILED_WITHOUT_FAIL_CHECK")
    if verification_passed is False and not blocked_by:
        action_required.append("VERIFICATION_FAILED_WITHOUT_BLOCKED_BY")
    if blocked_by and fail_checks and str(blocked_by) not in set(fail_checks):
        action_required.append("VERIFICATION_BLOCKED_BY_NOT_A_FAIL_CHECK")

    l2_summary = verification_context.get("l2_check_summary") if isinstance(verification_context.get("l2_check_summary"), dict) else {}
    sl_status = l2_summary.get("sl_beyond_ob")
    sl_decision = sl_beyond_ob_context.get("l2_decision")
    if sl_status in {"PASS", "FAIL"} and sl_decision in {"PASS", "FAIL"} and sl_status != sl_decision:
        action_required.append("SL_BEYOND_OB_L2_DECISION_MISMATCH_VERIFICATION_CHECK")

    if touch_count_context.get("gate_decision") == "REJECT" and "REJECTED_GATE1" not in str(candidate.get("final_outcome_at_log") or ""):
        action_required.append("TOUCH_COUNT_REJECT_WITHOUT_GATE1_FINAL_OUTCOME")

    joined_sources = {
        "candidate_features": candidate_features_context.get("join_status"),
        "d1_bias_lag": d1_bias_lag_context.get("join_status"),
        "direction_emission": direction_emission_context.get("join_status"),
        "sl_beyond_ob": sl_beyond_ob_context.get("join_status"),
        "touch_count": touch_count_context.get("join_status"),
        "cross_instrument_correlation": cross_instrument_correlation_context.get("join_status"),
    }
    optional_missing_sources = {"cross_instrument_correlation"}
    status = ACTION_REQUIRED if action_required else COMPLETE
    if not action_required and any(
        str(value).startswith("DIAGNOSTIC_JOIN_MISSING")
        for source, value in joined_sources.items()
        if source not in optional_missing_sources
    ):
        status = PARTIAL

    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        CLASSIFIER_VERSION,
        candidate.get("candidate_id"),
        symbol,
        candidate.get("broker_symbol"),
        decision_time,
        candidate.get("created_at_utc"),
        candidate.get("final_outcome_at_log"),
        side,
        trade_parameter_direction,
        verification_context,
        candidate_features_context,
        d1_bias_lag_context,
        direction_emission_context,
        sl_beyond_ob_context,
        touch_count_context,
        cross_instrument_correlation_context,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("decision_layer_diagnostics_join", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "classifier_version": CLASSIFIER_VERSION,
        "lto_id": "LTO-019",
        "follow_id": "LIVE-FOLLOW-016",
        "row_type": "candidate_decision_diagnostics",
        "decision_diagnostics_status": status,
        "candidate_id": candidate.get("candidate_id"),
        "symbol": symbol,
        "broker_symbol": candidate.get("broker_symbol") or symbol,
        "side": side,
        "framework": framework or None,
        "session": candidate.get("session") or candidate.get("kill_zone"),
        "decision_time_utc": decision_time,
        "candidate_final_outcome_at_log": candidate.get("final_outcome_at_log"),
        "ai_decision": candidate_features_context.get("ai_decision"),
        "ai_direction": candidate_features_context.get("ai_direction_evaluated"),
        "trade_parameter_direction": trade_parameter_direction,
        "verification_passed": verification_passed,
        "verification_blocked_by": blocked_by,
        "verification_context": verification_context,
        "candidate_features_join_status": joined_sources["candidate_features"],
        "d1_bias_lag_join_status": joined_sources["d1_bias_lag"],
        "direction_emission_join_status": joined_sources["direction_emission"],
        "sl_beyond_ob_join_status": joined_sources["sl_beyond_ob"],
        "touch_count_join_status": joined_sources["touch_count"],
        "cross_instrument_correlation_join_status": joined_sources["cross_instrument_correlation"],
        "diagnostic_join_statuses": joined_sources,
        "candidate_features_context": candidate_features_context,
        "d1_bias_lag_context": d1_bias_lag_context,
        "direction_emission_context": direction_emission_context,
        "sl_beyond_ob_context": sl_beyond_ob_context,
        "touch_count_context": touch_count_context,
        "cross_instrument_correlation_context": cross_instrument_correlation_context,
        "mismatch_codes": sorted(set(mismatch_codes)),
        "documented_limitation_codes": sorted(set(documented_limitations)),
        "action_required_codes": sorted(set(action_required)),
        "claim_boundary": (
            "Decision-layer diagnostic rows join only same-candle/as-of observation logs. "
            "They are ML feature/context substrate and do not validate or change live decisions."
        ),
        "ml_feature_role": "ML_DECISION_LAYER_DIAGNOSTICS_AND_GATE_CONTEXT",
        "ml_label_eligibility": "DECISION_DIAGNOSTIC_FEATURE_CONTEXT_ONLY",
        "ml_no_leak_boundary": "SAME_CANDLE_DECISION_DIAGNOSTICS_ONLY_NO_POST_OUTCOME_FEATURES",
        "evidence_class": "DECISION_LAYER_DIAGNOSTICS_CONTEXT",
        "no_leak_status": "DECISION_LAYER_DIAGNOSTICS_AUDIT_NOT_DECISION_CHANGE",
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


def build_decision_layer_diagnostics_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    *,
    candidate_feature_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    d1_bias_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    direction_emission_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    sl_beyond_ob_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    touch_count_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    cross_instrument_correlation_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    candidates = _latest_by_candidate(_rows_with_lines(candidate_rows))
    rows: list[dict[str, Any]] = []
    for _, candidate in sorted(candidates.items()):
        rows.append(
            build_decision_layer_diagnostics_row(
                candidate=candidate,
                candidate_feature_rows=candidate_feature_rows,
                d1_bias_rows=d1_bias_rows,
                direction_emission_rows=direction_emission_rows,
                sl_beyond_ob_rows=sl_beyond_ob_rows,
                touch_count_rows=touch_count_rows,
                cross_instrument_correlation_rows=cross_instrument_correlation_rows,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("decision_diagnostics_status") or "UNKNOWN") for row in rows)
    symbol_counts = Counter(str(row.get("symbol") or "UNKNOWN") for row in rows)
    framework_counts = Counter(str(row.get("framework") or "UNKNOWN") for row in rows)
    final_outcome_counts = Counter(str(row.get("candidate_final_outcome_at_log") or "UNKNOWN") for row in rows)
    join_counts: dict[str, Counter[str]] = defaultdict(Counter)
    action_counts: Counter[str] = Counter()
    mismatch_counts: Counter[str] = Counter()
    limitation_counts: Counter[str] = Counter()
    daily_status_mix: dict[str, Counter[str]] = defaultdict(Counter)
    weekly_status_mix: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        statuses = row.get("diagnostic_join_statuses") if isinstance(row.get("diagnostic_join_statuses"), dict) else {}
        for source, status in statuses.items():
            join_counts[source][str(status or "UNKNOWN")] += 1
        action_counts.update(row.get("action_required_codes") or [])
        mismatch_counts.update(row.get("mismatch_codes") or [])
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        decision_dt = parse_utc(row.get("decision_time_utc"))
        if decision_dt is not None:
            daily_status_mix[decision_dt.date().isoformat()][str(row.get("decision_diagnostics_status") or "UNKNOWN")] += 1
            iso_year, iso_week, _ = decision_dt.isocalendar()
            weekly_status_mix[f"{iso_year:04d}-W{iso_week:02d}"][str(row.get("decision_diagnostics_status") or "UNKNOWN")] += 1
    return {
        "rows": len(rows),
        "status_counts": dict(status_counts),
        "symbol_counts": dict(symbol_counts),
        "framework_counts": dict(framework_counts),
        "final_outcome_counts": dict(final_outcome_counts),
        "diagnostic_join_counts": {key: dict(value) for key, value in sorted(join_counts.items())},
        "action_required_code_counts": dict(action_counts),
        "mismatch_code_counts": dict(mismatch_counts),
        "documented_limitation_code_counts": dict(limitation_counts),
        "candidate_features_joined_rows": sum(1 for row in rows if row.get("candidate_features_join_status") == "DIAGNOSTIC_NEAR_TIME_JOINED"),
        "direction_emission_joined_rows": sum(1 for row in rows if row.get("direction_emission_join_status") == "DIAGNOSTIC_NEAR_TIME_JOINED"),
        "sl_beyond_ob_joined_rows": sum(1 for row in rows if row.get("sl_beyond_ob_join_status") == "DIAGNOSTIC_NEAR_TIME_JOINED"),
        "touch_count_joined_rows": sum(1 for row in rows if row.get("touch_count_join_status") == "DIAGNOSTIC_NEAR_TIME_JOINED"),
        "cross_instrument_correlation_joined_rows": sum(
            1
            for row in rows
            if row.get("cross_instrument_correlation_join_status") == "DIAGNOSTIC_NEAR_TIME_JOINED"
        ),
        "d1_bias_lag_joined_rows": sum(1 for row in rows if row.get("d1_bias_lag_join_status") == "DIAGNOSTIC_NEAR_TIME_JOINED"),
        "daily_status_mix": {key: dict(value) for key, value in sorted(daily_status_mix.items())},
        "weekly_status_mix": {key: dict(value) for key, value in sorted(weekly_status_mix.items())},
    }
