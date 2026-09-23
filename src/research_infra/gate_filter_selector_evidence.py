"""Gate/filter/selector evidence joins for default-off research decisions."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "gate_filter_selector_evidence_v1"
LEGACY_CANDIDATE_ID_RE = re.compile(
    r"^(?P<symbol>[A-Za-z0-9_]+)_(?P<date>\d{4}-\d{2}-\d{2})T"
    r"(?P<hour>\d{2})_(?P<minute>\d{2})_(?P<second>\d{2})(?:_\d+)?_00_00$"
)
SYMBOL_ALIASES = {"NDX100": "NAS100", "NAS100": "NAS100", "US30_CASH": "US30", "US30": "US30"}


def stable_hash(payload: Any, *, length: int = 32) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def normalize_candidate_id(candidate_id: Any) -> str:
    text = str(candidate_id or "").strip()
    match = LEGACY_CANDIDATE_ID_RE.match(text)
    if not match:
        return text
    return (
        f"{match.group('symbol')}_{match.group('date')}T"
        f"{match.group('hour')}:{match.group('minute')}:00+00:00"
    )


def canonical_symbol(symbol: Any) -> str:
    text = str(symbol or "").strip()
    return SYMBOL_ALIASES.get(text.upper(), text)


def parse_utc_minute(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(second=0, microsecond=0)


def rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line_no), row) for line_no, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _outcome_by_candidate_id(
    outcome_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
) -> dict[str, tuple[int, dict[str, Any]]]:
    by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for line_no, row in rows_with_lines(outcome_rows):
        normalized_id = normalize_candidate_id(row.get("candidate_id"))
        if normalized_id and normalized_id not in by_id:
            by_id[normalized_id] = (line_no, row)
    return by_id


def _outcome_by_symbol_minute(
    outcome_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
) -> dict[tuple[str, datetime], tuple[int, dict[str, Any]]]:
    by_key: dict[tuple[str, datetime], tuple[int, dict[str, Any]]] = {}
    for line_no, row in rows_with_lines(outcome_rows):
        symbol = canonical_symbol(row.get("symbol") or row.get("broker_symbol"))
        minute = parse_utc_minute(row.get("decision_time_utc"))
        if symbol and minute is not None and (symbol, minute) not in by_key:
            by_key[(symbol, minute)] = (line_no, row)
    return by_key


def _baseline_outcome_by_candidate_id(
    outcome_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
) -> dict[str, tuple[int, dict[str, Any]]]:
    by_id: dict[str, tuple[int, dict[str, Any]]] = {}
    for line_no, row in rows_with_lines(outcome_rows):
        normalized_id = normalize_candidate_id(row.get("candidate_id"))
        if not normalized_id:
            continue
        current = by_id.get(normalized_id)
        current_strategy = str((current[1] if current else {}).get("strategy_id") or "")
        strategy = str(row.get("strategy_id") or "")
        if current is None or (
            current_strategy != "LIVE_AI_J46_J49_BASELINE_COMPARATOR"
            and strategy == "LIVE_AI_J46_J49_BASELINE_COMPARATOR"
        ):
            by_id[normalized_id] = (line_no, row)
    return by_id


def touch_count_join_action(row: dict[str, Any]) -> str:
    if row.get("join_status") != "TOUCH_COUNT_GATE_OUTCOME_JOINED":
        return "TOUCH_COUNT_GATE_OUTCOME_JOIN_MISSING_SOURCE_CAPTURE_REQUIRED"
    decision = str(row.get("gate_decision") or "").upper()
    outcome_status = str(row.get("outcome_status") or "")
    path_label = str(row.get("path_label") or "")
    proxy_r = float_or_none(row.get("strategy_proxy_r"))
    if decision != "REJECT":
        return "TOUCH_COUNT_GATE_PASS_OUTCOME_REFERENCE_ONLY"
    if outcome_status in {"NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH", "NO_ENTRY_TOUCH_BY_ASOF"}:
        return "TOUCH_COUNT_REJECT_JOINED_NO_FILLABLE_MISSED_R_CURRENT_FORWARD"
    if "NO_FILL" in outcome_status or path_label.startswith("no_touch"):
        return "TOUCH_COUNT_REJECT_JOINED_NO_FILLABLE_MISSED_R_CURRENT_FORWARD"
    if proxy_r is not None and proxy_r > 0:
        return "TOUCH_COUNT_REJECT_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
    if proxy_r is not None and proxy_r < 0:
        return "TOUCH_COUNT_REJECT_JOINED_NEGATIVE_OR_ADVERSE_PROXY_SUPPORTS_GATE"
    return "TOUCH_COUNT_REJECT_JOINED_NEUTRAL_OR_UNRESOLVED_REVIEW_REQUIRED"


def build_touch_count_gate_outcome_join_rows(
    *,
    touch_count_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    outcome_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    touch_source_path: str,
    touch_source_sha256: str,
    outcome_source_path: str,
    outcome_source_sha256: str,
) -> list[dict[str, Any]]:
    outcomes = _outcome_by_candidate_id(outcome_rows)
    joined_rows: list[dict[str, Any]] = []
    for index, (line_no, touch_row) in enumerate(rows_with_lines(touch_count_rows), start=1):
        raw_candidate_id = touch_row.get("candidate_id")
        normalized_id = normalize_candidate_id(raw_candidate_id)
        outcome_line_no, outcome_row = outcomes.get(normalized_id, (None, None))  # type: ignore[assignment]
        joined = isinstance(outcome_row, dict)
        path_metrics = outcome_row.get("path_metrics") if joined else {}
        row = {
            "touch_count_gate_outcome_join_row_id": f"MAIN-ORCH48-TOUCH-COUNT-GATE-OUTCOME-JOIN-{index:08d}",
            "schema_version": "main_orch48_touch_count_gate_outcome_join_v1",
            "touch_source_path": touch_source_path,
            "touch_source_line_no": line_no,
            "touch_source_sha256": touch_source_sha256,
            "outcome_source_path": outcome_source_path,
            "outcome_source_line_no": outcome_line_no,
            "outcome_source_sha256": outcome_source_sha256 if joined else None,
            "candidate_id": raw_candidate_id,
            "normalized_candidate_id": normalized_id,
            "symbol": touch_row.get("symbol"),
            "framework": touch_row.get("framework"),
            "gate_decision": touch_row.get("gate_decision"),
            "gate_target_ob_touch": touch_row.get("gate_target_ob_touch"),
            "gate_threshold_at_eval": touch_row.get("gate_threshold_at_eval"),
            "gate_target_ob_id": touch_row.get("gate_target_ob_id"),
            "ob_type": touch_row.get("ob_type"),
            "candle_time": touch_row.get("candle_time"),
            "join_status": (
                "TOUCH_COUNT_GATE_OUTCOME_JOINED"
                if joined
                else "TOUCH_COUNT_GATE_OUTCOME_MISSING_BY_NORMALIZED_CANDIDATE_ID"
            ),
            "outcome_status": outcome_row.get("outcome_status") if joined else None,
            "path_label": outcome_row.get("path_label") if joined else None,
            "candidate_final_outcome_at_log": outcome_row.get("candidate_final_outcome_at_log") if joined else None,
            "strategy_proxy_r": float_or_none(outcome_row.get("strategy_proxy_r")) if joined else None,
            "max_favorable_r_from_entry": float_or_none((path_metrics or {}).get("max_favorable_r_from_entry")),
            "max_adverse_r_from_entry": float_or_none((path_metrics or {}).get("max_adverse_r_from_entry")),
            "current_gate_config_threshold": touch_row.get("gate_threshold_at_eval"),
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "gate_config_change_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "replay_r_reference_counted_as_new_main_result": False,
        }
        row["touch_count_gate_outcome_action"] = touch_count_join_action(row)
        row["row_key"] = stable_hash(
            {
                "schema_version": row["schema_version"],
                "candidate_id": row["normalized_candidate_id"],
                "gate_decision": row["gate_decision"],
                "join_status": row["join_status"],
                "outcome_status": row["outcome_status"],
            }
        )
        joined_rows.append(row)
    return joined_rows


def summarize_touch_count_gate_outcome_join(rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined_reject_rows = [
        row
        for row in rows
        if row.get("join_status") == "TOUCH_COUNT_GATE_OUTCOME_JOINED"
        and str(row.get("gate_decision") or "").upper() == "REJECT"
    ]
    return {
        "rows": len(rows),
        "join_status_counts": dict(sorted(Counter(str(row.get("join_status")) for row in rows).items())),
        "gate_decision_counts": dict(sorted(Counter(str(row.get("gate_decision")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in rows).items())),
        "touch_count_gate_outcome_action_counts": dict(
            sorted(Counter(str(row.get("touch_count_gate_outcome_action")) for row in rows).items())
        ),
        "joined_rows": sum(row.get("join_status") == "TOUCH_COUNT_GATE_OUTCOME_JOINED" for row in rows),
        "missing_outcome_rows": sum(
            row.get("join_status") == "TOUCH_COUNT_GATE_OUTCOME_MISSING_BY_NORMALIZED_CANDIDATE_ID"
            for row in rows
        ),
        "joined_reject_rows": len(joined_reject_rows),
        "joined_reject_no_fillable_missed_r_rows": sum(
            row.get("touch_count_gate_outcome_action")
            == "TOUCH_COUNT_REJECT_JOINED_NO_FILLABLE_MISSED_R_CURRENT_FORWARD"
            for row in joined_reject_rows
        ),
        "joined_reject_positive_fillable_proxy_rows": sum(
            row.get("touch_count_gate_outcome_action")
            == "TOUCH_COUNT_REJECT_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
            for row in joined_reject_rows
        ),
        "runtime_decision_effect_rows": sum(bool(row.get("runtime_decision_effect")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "gate_config_change_now_rows": sum(bool(row.get("gate_config_change_now")) for row in rows),
        "broker_operation_rows": sum(bool(row.get("broker_operation")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def sl_beyond_ob_join_action(row: dict[str, Any]) -> str:
    if row.get("join_status") != "SL_BEYOND_OB_OUTCOME_JOINED":
        if str(row.get("l2_decision") or "").upper() == "REJECT":
            return "SL_BEYOND_OB_REJECT_OUTCOME_JOIN_MISSING_CAPTURE_REQUIRED"
        return "SL_BEYOND_OB_OUTCOME_JOIN_MISSING_SOURCE_CAPTURE_REQUIRED"
    decision = str(row.get("l2_decision") or "").upper()
    if decision == "PASS":
        return "SL_BEYOND_OB_PASS_OUTCOME_REFERENCE_ONLY"
    proxy_r = float_or_none(row.get("strategy_proxy_r"))
    if proxy_r is not None and proxy_r > 0:
        return "SL_BEYOND_OB_REJECT_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
    if proxy_r is not None and proxy_r < 0:
        return "SL_BEYOND_OB_REJECT_JOINED_NEGATIVE_OR_ADVERSE_PROXY_SUPPORTS_GATE"
    return "SL_BEYOND_OB_REJECT_JOINED_NEUTRAL_OR_UNRESOLVED_REVIEW_REQUIRED"


def pre_ai_h1_poi_gate_join_action(row: dict[str, Any]) -> str:
    if row.get("pre_ai_gate_decision") != "SKIP_AI_CALL":
        if row.get("join_status") == "PRE_AI_H1_POI_OUTCOME_JOINED":
            return "PRE_AI_H1_POI_PASS_OUTCOME_REFERENCE_ONLY"
        return "PRE_AI_H1_POI_PASS_NO_OUTCOME_REFERENCE"
    if row.get("join_status") != "PRE_AI_H1_POI_OUTCOME_JOINED":
        return "PRE_AI_H1_POI_SKIP_NO_OUTCOME_JOIN_SOURCE_CAPTURE_REQUIRED"
    outcome_status = str(row.get("outcome_status") or "")
    path_label = str(row.get("path_label") or "")
    proxy_r = float_or_none(row.get("strategy_proxy_r"))
    if outcome_status in {"NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH", "NO_ENTRY_TOUCH_BY_ASOF"}:
        return "PRE_AI_H1_POI_SKIP_JOINED_NO_FILLABLE_MISSED_R_CURRENT_FORWARD"
    if "NO_FILL" in outcome_status or path_label.startswith("no_touch"):
        return "PRE_AI_H1_POI_SKIP_JOINED_NO_FILLABLE_MISSED_R_CURRENT_FORWARD"
    if proxy_r is not None and proxy_r > 0:
        return "PRE_AI_H1_POI_SKIP_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
    if proxy_r is not None and proxy_r < 0:
        return "PRE_AI_H1_POI_SKIP_JOINED_NEGATIVE_OR_ADVERSE_PROXY_SUPPORTS_GATE"
    return "PRE_AI_H1_POI_SKIP_JOINED_NEUTRAL_OR_UNRESOLVED_REVIEW_REQUIRED"


def pre_ai_h1_poi_skip_bias(reason: Any) -> str | None:
    text = str(reason or "")
    if text.startswith("no_bullish_pois_for_"):
        return "bullish"
    if text.startswith("no_bearish_pois_for_"):
        return "bearish"
    return None


def build_pre_ai_h1_poi_outcome_join_rows(
    *,
    candidate_feature_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    outcome_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    candidate_features_source_path: str,
    candidate_features_source_sha256: str,
    outcome_source_path: str,
    outcome_source_sha256: str,
) -> list[dict[str, Any]]:
    outcomes = _baseline_outcome_by_candidate_id(outcome_rows)
    joined_rows: list[dict[str, Any]] = []
    for index, (line_no, feature_row) in enumerate(rows_with_lines(candidate_feature_rows), start=1):
        raw_evaluation_id = feature_row.get("evaluation_id")
        normalized_id = normalize_candidate_id(raw_evaluation_id)
        outcome_line_no, outcome_row = outcomes.get(normalized_id, (None, None))  # type: ignore[assignment]
        joined = isinstance(outcome_row, dict)
        path_metrics = outcome_row.get("path_metrics") if joined else {}
        skipped = bool(feature_row.get("pre_ai_gate_skipped"))
        row = {
            "pre_ai_h1_poi_outcome_join_row_id": f"MAIN-ORCH48-PRE-AI-H1-POI-OUTCOME-JOIN-{index:08d}",
            "schema_version": "main_orch48_pre_ai_h1_poi_outcome_join_v1",
            "candidate_features_source_path": candidate_features_source_path,
            "candidate_features_source_line_no": line_no,
            "candidate_features_source_sha256": candidate_features_source_sha256,
            "outcome_source_path": outcome_source_path,
            "outcome_source_line_no": outcome_line_no,
            "outcome_source_sha256": outcome_source_sha256 if joined else None,
            "evaluation_id": raw_evaluation_id,
            "normalized_evaluation_id": normalized_id,
            "symbol": feature_row.get("symbol"),
            "timestamp_utc": feature_row.get("timestamp_utc"),
            "candle_close_utc": feature_row.get("candle_close_utc"),
            "kill_zone": feature_row.get("kill_zone"),
            "session_tag": feature_row.get("session_tag"),
            "pre_ai_gate_decision": "SKIP_AI_CALL" if skipped else "PASS_TO_AI_OR_DOWNSTREAM",
            "pre_ai_gate_skipped": skipped,
            "pre_ai_gate_reason": feature_row.get("pre_ai_gate_reason"),
            "pre_ai_gate_skip_bias": pre_ai_h1_poi_skip_bias(feature_row.get("pre_ai_gate_reason")),
            "decision": feature_row.get("decision"),
            "framework": feature_row.get("framework"),
            "setup_grade": feature_row.get("setup_grade"),
            "trade_parameters_present": bool(feature_row.get("trade_parameters")),
            "h1_unmitigated_ob_count": feature_row.get("mso_h1_unmitigated_ob_count"),
            "h1_ob_touch_counts": feature_row.get("mso_h1_ob_touch_counts"),
            "h1_fvg_count": feature_row.get("mso_h1_fvg_count"),
            "m15_fvg_count": feature_row.get("mso_m15_fvg_count"),
            "h1_structure_direction": feature_row.get("mso_h1_structure_direction"),
            "m15_structure_direction": feature_row.get("mso_m15_structure_direction"),
            "d1_structure_direction": feature_row.get("mso_d1_structure_direction"),
            "directional_poi_detail_capture_state": (
                "MISSING_FRAMEWORK_DIRECTIONAL_POI_COUNTS_FOR_SKIP_REVIEW"
                if skipped
                else "NOT_NEEDED_FOR_PASS_REFERENCE"
            ),
            "join_status": (
                "PRE_AI_H1_POI_OUTCOME_JOINED"
                if joined
                else "PRE_AI_H1_POI_OUTCOME_MISSING_BY_NORMALIZED_EVALUATION_ID"
            ),
            "outcome_candidate_id": outcome_row.get("candidate_id") if joined else None,
            "outcome_strategy_id": outcome_row.get("strategy_id") if joined else None,
            "outcome_status": outcome_row.get("outcome_status") if joined else None,
            "path_label": outcome_row.get("path_label") if joined else None,
            "candidate_final_outcome_at_log": outcome_row.get("candidate_final_outcome_at_log") if joined else None,
            "strategy_proxy_r": float_or_none(outcome_row.get("strategy_proxy_r")) if joined else None,
            "max_favorable_r_from_entry": float_or_none((path_metrics or {}).get("max_favorable_r_from_entry")),
            "max_adverse_r_from_entry": float_or_none((path_metrics or {}).get("max_adverse_r_from_entry")),
            "saved_ai_call_reference": skipped,
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "gate_config_change_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "replay_r_reference_counted_as_new_main_result": False,
        }
        row["pre_ai_h1_poi_outcome_action"] = pre_ai_h1_poi_gate_join_action(row)
        row["row_key"] = stable_hash(
            {
                "schema_version": row["schema_version"],
                "evaluation_id": row["normalized_evaluation_id"],
                "pre_ai_gate_decision": row["pre_ai_gate_decision"],
                "join_status": row["join_status"],
                "outcome_status": row["outcome_status"],
            }
        )
        joined_rows.append(row)
    return joined_rows


def summarize_pre_ai_h1_poi_outcome_join(rows: list[dict[str, Any]]) -> dict[str, Any]:
    skip_rows = [row for row in rows if row.get("pre_ai_gate_decision") == "SKIP_AI_CALL"]
    joined_skip_rows = [row for row in skip_rows if row.get("join_status") == "PRE_AI_H1_POI_OUTCOME_JOINED"]
    return {
        "rows": len(rows),
        "pre_ai_gate_decision_counts": dict(
            sorted(Counter(str(row.get("pre_ai_gate_decision")) for row in rows).items())
        ),
        "join_status_counts": dict(sorted(Counter(str(row.get("join_status")) for row in rows).items())),
        "pre_ai_gate_reason_counts": dict(
            sorted(Counter(str(row.get("pre_ai_gate_reason") or "") for row in skip_rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in rows).items())),
        "skip_symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in skip_rows).items())),
        "pre_ai_h1_poi_outcome_action_counts": dict(
            sorted(Counter(str(row.get("pre_ai_h1_poi_outcome_action")) for row in rows).items())
        ),
        "skip_rows": len(skip_rows),
        "pass_reference_rows": len(rows) - len(skip_rows),
        "joined_rows": sum(row.get("join_status") == "PRE_AI_H1_POI_OUTCOME_JOINED" for row in rows),
        "missing_outcome_rows": sum(
            row.get("join_status") == "PRE_AI_H1_POI_OUTCOME_MISSING_BY_NORMALIZED_EVALUATION_ID"
            for row in rows
        ),
        "joined_skip_rows": len(joined_skip_rows),
        "missing_skip_rows": sum(
            row.get("join_status") == "PRE_AI_H1_POI_OUTCOME_MISSING_BY_NORMALIZED_EVALUATION_ID"
            for row in skip_rows
        ),
        "saved_ai_call_reference_rows": sum(bool(row.get("saved_ai_call_reference")) for row in rows),
        "skip_rows_missing_directional_poi_detail": sum(
            row.get("directional_poi_detail_capture_state")
            == "MISSING_FRAMEWORK_DIRECTIONAL_POI_COUNTS_FOR_SKIP_REVIEW"
            for row in skip_rows
        ),
        "joined_skip_positive_fillable_proxy_rows": sum(
            row.get("pre_ai_h1_poi_outcome_action")
            == "PRE_AI_H1_POI_SKIP_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
            for row in joined_skip_rows
        ),
        "runtime_decision_effect_rows": sum(bool(row.get("runtime_decision_effect")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "gate_config_change_now_rows": sum(bool(row.get("gate_config_change_now")) for row in rows),
        "broker_operation_rows": sum(bool(row.get("broker_operation")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def build_sl_beyond_ob_outcome_join_rows(
    *,
    sl_beyond_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    outcome_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    sl_beyond_source_path: str,
    sl_beyond_source_sha256: str,
    outcome_source_path: str,
    outcome_source_sha256: str,
) -> list[dict[str, Any]]:
    outcomes = _outcome_by_symbol_minute(outcome_rows)
    joined_rows: list[dict[str, Any]] = []
    for index, (line_no, sl_row) in enumerate(rows_with_lines(sl_beyond_rows), start=1):
        symbol = canonical_symbol(sl_row.get("symbol"))
        candle_minute = parse_utc_minute(sl_row.get("candle_time"))
        outcome_line_no: int | None = None
        outcome_row: dict[str, Any] | None = None
        if symbol and candle_minute is not None:
            outcome_line_no, outcome_row = outcomes.get((symbol, candle_minute), (None, None))  # type: ignore[assignment]
        joined = isinstance(outcome_row, dict)
        path_metrics = outcome_row.get("path_metrics") if joined else {}
        row = {
            "sl_beyond_ob_outcome_join_row_id": f"MAIN-ORCH48-SL-BEYOND-OB-OUTCOME-JOIN-{index:08d}",
            "schema_version": "main_orch48_sl_beyond_ob_outcome_join_v1",
            "sl_beyond_source_path": sl_beyond_source_path,
            "sl_beyond_source_line_no": line_no,
            "sl_beyond_source_sha256": sl_beyond_source_sha256,
            "outcome_source_path": outcome_source_path,
            "outcome_source_line_no": outcome_line_no,
            "outcome_source_sha256": outcome_source_sha256 if joined else None,
            "symbol": sl_row.get("symbol"),
            "canonical_symbol": symbol,
            "framework": sl_row.get("framework"),
            "l2_decision": sl_row.get("l2_decision"),
            "l2_reason": sl_row.get("l2_reason"),
            "direction": sl_row.get("direction"),
            "candle_time": sl_row.get("candle_time"),
            "candle_minute_utc": candle_minute.isoformat() if candle_minute is not None else None,
            "proposed_entry": float_or_none(sl_row.get("proposed_entry")),
            "proposed_sl": float_or_none(sl_row.get("proposed_sl")),
            "proposed_tp1": float_or_none(sl_row.get("proposed_tp1")),
            "ob_low": float_or_none(sl_row.get("ob_low")),
            "ob_high": float_or_none(sl_row.get("ob_high")),
            "zone_label": sl_row.get("zone_label"),
            "join_status": "SL_BEYOND_OB_OUTCOME_JOINED" if joined else "SL_BEYOND_OB_OUTCOME_MISSING_BY_SYMBOL_MINUTE",
            "outcome_candidate_id": outcome_row.get("candidate_id") if joined else None,
            "outcome_status": outcome_row.get("outcome_status") if joined else None,
            "path_label": outcome_row.get("path_label") if joined else None,
            "candidate_final_outcome_at_log": outcome_row.get("candidate_final_outcome_at_log") if joined else None,
            "strategy_proxy_r": float_or_none(outcome_row.get("strategy_proxy_r")) if joined else None,
            "max_favorable_r_from_entry": float_or_none((path_metrics or {}).get("max_favorable_r_from_entry")),
            "max_adverse_r_from_entry": float_or_none((path_metrics or {}).get("max_adverse_r_from_entry")),
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "gate_config_change_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "replay_r_reference_counted_as_new_main_result": False,
        }
        row["sl_beyond_ob_outcome_action"] = sl_beyond_ob_join_action(row)
        row["row_key"] = stable_hash(
            {
                "schema_version": row["schema_version"],
                "symbol": row["canonical_symbol"],
                "candle_minute": row["candle_minute_utc"],
                "l2_decision": row["l2_decision"],
                "join_status": row["join_status"],
                "outcome_status": row["outcome_status"],
            }
        )
        joined_rows.append(row)
    return joined_rows


def summarize_sl_beyond_ob_outcome_join(rows: list[dict[str, Any]]) -> dict[str, Any]:
    joined_reject_rows = [
        row
        for row in rows
        if row.get("join_status") == "SL_BEYOND_OB_OUTCOME_JOINED"
        and str(row.get("l2_decision") or "").upper() == "REJECT"
    ]
    missing_reject_rows = [
        row
        for row in rows
        if row.get("join_status") != "SL_BEYOND_OB_OUTCOME_JOINED"
        and str(row.get("l2_decision") or "").upper() == "REJECT"
    ]
    return {
        "rows": len(rows),
        "join_status_counts": dict(sorted(Counter(str(row.get("join_status")) for row in rows).items())),
        "l2_decision_counts": dict(sorted(Counter(str(row.get("l2_decision")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(str(row.get("canonical_symbol")) for row in rows).items())),
        "sl_beyond_ob_outcome_action_counts": dict(
            sorted(Counter(str(row.get("sl_beyond_ob_outcome_action")) for row in rows).items())
        ),
        "joined_rows": sum(row.get("join_status") == "SL_BEYOND_OB_OUTCOME_JOINED" for row in rows),
        "missing_outcome_rows": sum(
            row.get("join_status") == "SL_BEYOND_OB_OUTCOME_MISSING_BY_SYMBOL_MINUTE" for row in rows
        ),
        "joined_reject_rows": len(joined_reject_rows),
        "missing_reject_rows": len(missing_reject_rows),
        "joined_reject_positive_fillable_proxy_rows": sum(
            row.get("sl_beyond_ob_outcome_action")
            == "SL_BEYOND_OB_REJECT_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
            for row in joined_reject_rows
        ),
        "runtime_decision_effect_rows": sum(bool(row.get("runtime_decision_effect")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "gate_config_change_now_rows": sum(bool(row.get("gate_config_change_now")) for row in rows),
        "broker_operation_rows": sum(bool(row.get("broker_operation")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }
