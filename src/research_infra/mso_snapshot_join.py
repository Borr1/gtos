"""Decision-time MSO snapshot joins for live shadow candidates.

The helpers in this module are pure data transforms. They do not call AI,
broker APIs, canary checks, MT5, or paid data sources.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SNAPSHOT_SCHEMA_VERSION = "mso_decision_snapshot_v1"
JOIN_SCHEMA_VERSION = "candidate_mso_snapshot_join_v1"

JOINED_EXACT = "JOINED_EXACT_MSO_SNAPSHOT"
JOIN_MISSING = "MSO_JOIN_MISSING"

TIMEFRAMES = ("D1", "H4", "H1", "M15")
TIMEFRAME_COUNT_FIELDS = (
    "order_block_count",
    "unmitigated_order_block_count",
    "fvg_count",
    "breaker_block_count",
)
TIMEFRAME_STATE_FIELDS = (
    "structure_direction",
    "bos_detected",
    "choch_detected",
    *TIMEFRAME_COUNT_FIELDS,
)


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _same_dt(left: Any, right: Any) -> bool:
    left_dt = parse_dt(left)
    right_dt = parse_dt(right)
    return left_dt is not None and right_dt is not None and left_dt == right_dt


def _timeframe_state(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary = row.get("mso_summary") if isinstance(row, dict) else {}
    timeframes = summary.get("timeframes") if isinstance(summary, dict) else {}
    if not isinstance(timeframes, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for tf in TIMEFRAMES:
        state = timeframes.get(tf) or {}
        if isinstance(state, dict):
            out[tf] = {field: state.get(field) for field in TIMEFRAME_STATE_FIELDS}
    return out


def _timeframe_bias(state: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {tf: values.get("structure_direction") for tf, values in state.items()}


def _timeframe_counts(state: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        tf: {field: values.get(field) for field in TIMEFRAME_COUNT_FIELDS}
        for tf, values in state.items()
    }


def _candidate_poi(candidate_row: dict[str, Any] | None) -> dict[str, Any]:
    if not candidate_row:
        return {
            "capture_status": "NOT_PRESENT_ON_PRE_AI_MSO_ROW",
            "source": "pre_ai_mso_row",
        }
    h1_setup = candidate_row.get("h1_setup")
    if not isinstance(h1_setup, dict) or not h1_setup:
        return {
            "capture_status": "CANDIDATE_H1_SETUP_MISSING",
            "source": "strategy_follow_candidate",
        }
    return {
        "capture_status": "CANDIDATE_H1_SETUP_PRESENT",
        "source": "strategy_follow_candidate",
        "poi_identified": h1_setup.get("poi_identified"),
        "poi_type": h1_setup.get("poi_type"),
        "poi_price_level": h1_setup.get("poi_price_level"),
        "zone": h1_setup.get("zone"),
        "causing_event_type": h1_setup.get("causing_event_type"),
    }


def _parse_qualification(value: Any) -> bool | None:
    if isinstance(value, dict) and "qualified" in value:
        qualified = value.get("qualified")
        if isinstance(qualified, bool):
            return qualified
    text = str(value)
    if "qualified=True" in text:
        return True
    if "qualified=False" in text:
        return False
    return None


def _framework_qualification(candidate_row: dict[str, Any] | None) -> dict[str, Any]:
    if not candidate_row:
        return {
            "capture_status": "NOT_PRESENT_ON_PRE_AI_MSO_ROW",
            "source": "pre_ai_mso_row",
            "frameworks": {},
        }
    frameworks = candidate_row.get("frameworks_evaluated")
    if not isinstance(frameworks, dict):
        return {
            "capture_status": "CANDIDATE_FRAMEWORKS_EVALUATED_MISSING",
            "source": "strategy_follow_candidate",
            "frameworks": {},
        }
    return {
        "capture_status": "CANDIDATE_FRAMEWORKS_EVALUATED_PRESENT",
        "source": "strategy_follow_candidate",
        "selected_framework": candidate_row.get("framework"),
        "frameworks": {
            str(name): {
                "qualified": _parse_qualification(value),
                "raw": value,
            }
            for name, value in sorted(frameworks.items())
        },
    }


def _strategy_ids(row: dict[str, Any]) -> list[str]:
    snapshots = row.get("strategy_snapshots")
    if not isinstance(snapshots, list):
        return []
    ids = [str(item.get("strategy_id")) for item in snapshots if isinstance(item, dict) and item.get("strategy_id")]
    return sorted(ids)


def canonical_mso_snapshot(
    evaluation_row: dict[str, Any],
    candidate_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the reusable decision-time market-state snapshot schema."""
    state = _timeframe_state(evaluation_row)
    summary = evaluation_row.get("mso_summary") or {}
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "symbol": evaluation_row.get("symbol"),
        "broker_symbol": evaluation_row.get("broker_symbol"),
        "decision_time_utc": evaluation_row.get("decision_time_utc"),
        "session": evaluation_row.get("session"),
        "kill_zone": evaluation_row.get("kill_zone"),
        "side": (candidate_row or evaluation_row).get("side"),
        "mso_timestamp_utc": summary.get("timestamp_utc") if isinstance(summary, dict) else None,
        "timeframe_bias": _timeframe_bias(state),
        "timeframe_counts": _timeframe_counts(state),
        "structural_state": state,
        "framework_qualification": _framework_qualification(candidate_row),
        "candidate_poi": _candidate_poi(candidate_row),
        "source_provenance": {
            "evaluation_candidate_id": evaluation_row.get("candidate_id"),
            "candidate_id": (candidate_row or {}).get("candidate_id"),
            "evaluation_stage": evaluation_row.get("evaluation_stage"),
            "source_file": evaluation_row.get("source_file"),
            "source_hash": evaluation_row.get("source_hash"),
            "source_run_id": evaluation_row.get("source_run_id"),
            "ai_dependency": evaluation_row.get("ai_dependency"),
            "ai_status": evaluation_row.get("ai_status"),
        },
        "strategy_snapshot_ids": _strategy_ids(evaluation_row),
    }


def _evaluation_preference(item: tuple[int, dict[str, Any]]) -> tuple[int, int]:
    line_no, row = item
    source = str(row.get("source_file") or "")
    if source == "live_orchestrator_mso_pre_ai":
        source_rank = 0
    elif source == "shadow_observer_mso_no_ai":
        source_rank = 2
    else:
        source_rank = 1
    return (source_rank, -line_no)


def select_mso_row(
    candidate_row: dict[str, Any],
    evaluation_rows: list[tuple[int, dict[str, Any]]],
) -> tuple[int | None, dict[str, Any] | None, dict[str, Any]]:
    """Select the exact symbol/time MSO row and report nearest-row diagnostics."""
    symbol = candidate_row.get("symbol")
    decision_time = candidate_row.get("decision_time_utc")
    exact = [
        (line_no, row)
        for line_no, row in evaluation_rows
        if row.get("symbol") == symbol and _same_dt(row.get("decision_time_utc"), decision_time)
    ]
    if exact:
        line_no, row = sorted(exact, key=_evaluation_preference)[0]
        return line_no, row, {
            "join_status": JOINED_EXACT,
            "join_method": "exact_symbol_decision_time",
            "nearest_mso_delta_seconds": 0.0,
        }

    candidate_dt = parse_dt(decision_time)
    nearest_delta: float | None = None
    nearest_candidate_id: str | None = None
    if candidate_dt is not None:
        for _, row in evaluation_rows:
            if row.get("symbol") != symbol:
                continue
            row_dt = parse_dt(row.get("decision_time_utc"))
            if row_dt is None:
                continue
            delta = abs((row_dt - candidate_dt).total_seconds())
            if nearest_delta is None or delta < nearest_delta:
                nearest_delta = delta
                nearest_candidate_id = str(row.get("candidate_id") or "")

    return None, None, {
        "join_status": JOIN_MISSING,
        "join_method": "none_exact_symbol_decision_time",
        "nearest_mso_delta_seconds": nearest_delta,
        "nearest_mso_candidate_id": nearest_candidate_id,
    }


def compare_candidate_to_snapshot(
    candidate_row: dict[str, Any],
    snapshot: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    mismatches: list[dict[str, Any]] = []
    missing_candidate_context: list[str] = []

    for field in ("symbol", "broker_symbol", "decision_time_utc", "session", "kill_zone", "side"):
        left = candidate_row.get(field)
        right = snapshot.get(field)
        if left is None or right is None:
            if left is None:
                missing_candidate_context.append(field)
            continue
        if field == "decision_time_utc":
            if not _same_dt(left, right):
                mismatches.append({"field": field, "candidate": left, "mso": right})
            continue
        if str(left) != str(right):
            mismatches.append({"field": field, "candidate": left, "mso": right})

    candidate_state = _timeframe_state(candidate_row)
    snapshot_state = snapshot.get("structural_state") or {}
    if not candidate_state:
        missing_candidate_context.append("mso_summary.timeframes")
    for tf in TIMEFRAMES:
        candidate_tf = candidate_state.get(tf) or {}
        snapshot_tf = snapshot_state.get(tf) or {}
        if not candidate_tf:
            missing_candidate_context.append(f"mso_summary.timeframes.{tf}")
            continue
        for field in TIMEFRAME_STATE_FIELDS:
            left = candidate_tf.get(field)
            right = snapshot_tf.get(field)
            if left is None or right is None:
                continue
            if left != right:
                mismatches.append(
                    {
                        "field": f"mso_summary.timeframes.{tf}.{field}",
                        "candidate": left,
                        "mso": right,
                    }
                )

    return mismatches, sorted(set(missing_candidate_context))


def build_candidate_mso_join_row(
    candidate_line_no: int,
    candidate_row: dict[str, Any],
    evaluation_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    evaluation_line_no, evaluation_row, join_meta = select_mso_row(candidate_row, evaluation_rows)
    snapshot = canonical_mso_snapshot(evaluation_row, candidate_row) if evaluation_row else None
    mismatches: list[dict[str, Any]] = []
    missing_candidate_context: list[str] = []
    if snapshot:
        mismatches, missing_candidate_context = compare_candidate_to_snapshot(candidate_row, snapshot)

    if join_meta["join_status"] == JOIN_MISSING:
        comparison_status = JOIN_MISSING
    elif mismatches:
        comparison_status = "MSO_CONTEXT_MISMATCH"
    elif missing_candidate_context:
        comparison_status = "JOINED_CANDIDATE_CONTEXT_SPARSE"
    else:
        comparison_status = "JOINED_CONTEXT_MATCHED"

    candidate_id = str(candidate_row.get("candidate_id") or "")
    decision_time = str(candidate_row.get("decision_time_utc") or "")
    return {
        "schema_version": JOIN_SCHEMA_VERSION,
        "row_key": f"{candidate_id}|{decision_time}|{SNAPSHOT_SCHEMA_VERSION}",
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate_id,
        "symbol": candidate_row.get("symbol"),
        "broker_symbol": candidate_row.get("broker_symbol"),
        "decision_time_utc": candidate_row.get("decision_time_utc"),
        "candidate_line_no": candidate_line_no,
        "evaluation_line_no": evaluation_line_no,
        "join_status": join_meta["join_status"],
        "join_method": join_meta["join_method"],
        "nearest_mso_delta_seconds": join_meta.get("nearest_mso_delta_seconds"),
        "nearest_mso_candidate_id": join_meta.get("nearest_mso_candidate_id"),
        "context_comparison_status": comparison_status,
        "context_mismatches": mismatches,
        "missing_candidate_context_fields": missing_candidate_context,
        "mso_snapshot": snapshot,
        "manual_backfill_status": "BACKFILLED_FROM_EXACT_STRATEGY_FOLLOW_EVALUATION_ROW"
        if snapshot
        else "DOCUMENTED_SOURCE_NOT_CAPTURED_MSO_JOIN_MISSING",
        "no_leak_status": "DECISION_TIME_MSO_CONTEXT_ONLY_NO_POST_OUTCOME_FIELDS",
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


def build_candidate_mso_join_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    evaluation_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, candidate in candidate_rows:
        if decision_date_prefix and not str(candidate.get("decision_time_utc") or "").startswith(decision_date_prefix):
            continue
        rows.append(
            build_candidate_mso_join_row(
                line_no,
                candidate,
                evaluation_rows,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows
