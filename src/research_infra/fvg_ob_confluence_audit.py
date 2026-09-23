"""FVG/OB confluence and disagreement audit helpers.

This module is research/tooling only. It reads append-only FVG/OB confluence
rows plus post-decision path/resolution rows to separate captured
decision-time confluence buckets from exact FVG/OB geometry and sequencing
fields that remain source-not-captured.

It does not call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.components.gtos_vnext_event_fields import enrich_cp281_event_contract_fields
from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "fvg_ob_confluence_audit_v2"
DEFAULT_OUTPUT = Path("shadow_logs/fvg_ob_confluence_audit.jsonl")
COMPLETE = "FVG_OB_CONFLUENCE_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "FVG_OB_CONFLUENCE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
WAITING = "FVG_OB_CONFLUENCE_WAITING_FOR_PATH"
ACTION_REQUIRED = "FVG_OB_CONFLUENCE_ACTION_REQUIRED"
EXACT_SOURCE_CAPTURE_STATUSES = {
    "FVG_OB_EXACT_BOUNDS_CAPTURED",
    "FVG_EXACT_BOUNDS_CAPTURED",
    "OB_EXACT_BOUNDS_CAPTURED",
}

FVG_OB_STRATEGY_ID = "FVG_OB_CONFLUENCE_OB_AFTER_FVG"
FVG_MID_STRATEGY_ID = "V2_STRUCT_FVG_MID_EDGE"
POST_OUTCOME_FIELD_NAMES = {
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "outcome_r",
    "tp_hit",
    "sl_hit",
    "winner",
    "loser",
}
PLACEHOLDER_OUTCOME_LANES = {
    "",
    "UNRESOLVED_REQUIRES_FORWARD_JOIN",
    "no_outcome_at_decision_time",
    "synthetic_path_pending",
}


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line), row) for line, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _latest_clock(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("asof_latest_candle_utc"))
        or parse_utc(row.get("backfilled_at_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("decision_time_utc"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _latest_by_candidate(
    rows: list[tuple[int, dict[str, Any]]],
    *,
    date_prefix: str | None = None,
) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows, date_prefix=date_prefix)


def _latest_mechanical_by_key(rows: list[tuple[int, dict[str, Any]]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    for line_no, row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        strategy_id = str(row.get("strategy_id") or "")
        asof = str(row.get("asof_latest_candle_utc") or "")
        if not candidate_id or not strategy_id or not asof:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        key = (candidate_id, strategy_id, asof)
        current_key = (
            parse_utc(item.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            line_no,
        )
        previous = latest.get(key)
        previous_key = (
            parse_utc((previous or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            int((previous or {}).get("_line_no") or 0),
        )
        if current_key >= previous_key:
            latest[key] = item
    return latest


def _mechanical_for(
    mechanical_by_key: dict[tuple[str, str, str], dict[str, Any]],
    candidate_id: str,
    strategy_id: str,
    asof: str,
) -> dict[str, Any] | None:
    if asof:
        row = mechanical_by_key.get((candidate_id, strategy_id, asof))
        if row:
            return row
    candidates = [
        row
        for (cid, sid, _row_asof), row in mechanical_by_key.items()
        if cid == candidate_id and sid == strategy_id
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            parse_utc(row.get("asof_latest_candle_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            int(row.get("_line_no") or 0),
        ),
    )


def _is_bounds(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return value.get("low") is not None and value.get("high") is not None


def _bounds_overlap(first: Any, second: Any) -> bool | None:
    if not _is_bounds(first) or not _is_bounds(second):
        return None
    try:
        first_low = float(first["low"])
        first_high = float(first["high"])
        second_low = float(second["low"])
        second_high = float(second["high"])
    except (TypeError, ValueError):
        return None
    return max(first_low, second_low) <= min(first_high, second_high)


def _decision_no_leak_status(row: dict[str, Any]) -> str:
    problems: list[str] = []
    if str(row.get("no_leak_status") or "").startswith("POST_OUTCOME_FIELD_PRESENT"):
        problems.append(str(row.get("no_leak_status")))
    lane = str(row.get("candidate_outcome_lane") or "")
    if lane not in PLACEHOLDER_OUTCOME_LANES:
        problems.append(f"CANDIDATE_OUTCOME_LANE_NOT_PLACEHOLDER:{lane}")
    decision_fields = row.get("decision_time_fields") or {}
    if isinstance(decision_fields, dict):
        leaked = sorted(set(decision_fields) & POST_OUTCOME_FIELD_NAMES)
        if leaked:
            problems.append("DECISION_TIME_POST_OUTCOME_FIELDS:" + ",".join(leaked))
    return "NO_POST_OUTCOME_STATE_IN_FVG_OB_DECISION_ROW" if not problems else "FVG_OB_DECISION_ROW_POST_OUTCOME_STATE:" + ",".join(problems)


def _source_capture_statuses(row: dict[str, Any]) -> dict[str, str]:
    decision = row.get("decision_time_fields") or {}
    bucket = str(row.get("bucket") or "")
    h1_poi_type = str((decision or {}).get("h1_poi_type") or "").lower()
    h1_poi_price = (decision or {}).get("h1_poi_price_level")
    fvg_bounds = row.get("fvg_bounds")
    ob_bounds = row.get("ob_bounds")
    sequencing = row.get("sequencing")
    composite = row.get("composite_arbitration")
    disagreement = row.get("disagreement_reason")
    overlap = _bounds_overlap(fvg_bounds, ob_bounds)
    return {
        "bucket": "FVG_OB_BUCKET_CAPTURED" if bucket else "SOURCE_NOT_CAPTURED",
        "fvg_bounds": "FVG_BOUNDS_CAPTURED" if _is_bounds(fvg_bounds) else "SOURCE_NOT_CAPTURED",
        "ob_bounds": "OB_BOUNDS_CAPTURED"
        if _is_bounds(ob_bounds)
        else "PARTIAL_POI_POINT_CAPTURED_NOT_BOUNDS"
        if h1_poi_type == "ob" and h1_poi_price is not None
        else "SOURCE_NOT_CAPTURED",
        "sequencing": "SEQUENCING_CAPTURED"
        if sequencing
        else "SEQUENCE_BUCKET_CAPTURED_WITHOUT_EXACT_TIMES"
        if bucket in {"ob_after_fvg", "fvg_after_ob"}
        else "SOURCE_NOT_CAPTURED",
        "overlap": "OVERLAP_COMPUTED_FROM_EXACT_BOUNDS"
        if overlap is not None
        else "CONFLUENCE_BUCKET_CAPTURED_OVERLAP_EXACT_BOUNDS_MISSING"
        if bucket == "both_fvg_and_ob_fire"
        else "SOURCE_NOT_CAPTURED",
        "composite_arbitration": "COMPOSITE_ARBITRATION_CAPTURED"
        if composite
        else "COMPOSITE_ARBITRATION_SOURCE_NOT_CAPTURED",
        "disagreement_reason": "DISAGREEMENT_REASON_CAPTURED"
        if disagreement
        else "DERIVED_FROM_BUCKET_AND_FRAMEWORK"
        if bucket == "disagreement"
        else "NOT_APPLICABLE_OR_SOURCE_NOT_CAPTURED",
    }


def _overall_source_capture_status(statuses: dict[str, str], bucket: str) -> str:
    if bucket == "fvg_only" and statuses.get("fvg_bounds") == "FVG_BOUNDS_CAPTURED":
        return "FVG_EXACT_BOUNDS_CAPTURED"
    if bucket == "ob_only" and statuses.get("ob_bounds") == "OB_BOUNDS_CAPTURED":
        return "OB_EXACT_BOUNDS_CAPTURED"
    if statuses.get("fvg_bounds") == "FVG_BOUNDS_CAPTURED" and statuses.get("ob_bounds") == "OB_BOUNDS_CAPTURED":
        return "FVG_OB_EXACT_BOUNDS_CAPTURED"
    if statuses.get("bucket") == "FVG_OB_BUCKET_CAPTURED":
        return "FVG_OB_BUCKET_CAPTURED_EXACT_FIELDS_INCOMPLETE"
    return "FVG_OB_CONFLUENCE_SOURCE_NOT_CAPTURED"


def _required_source_fields_for_bucket(bucket: str) -> set[str]:
    if bucket == "fvg_only":
        return {"fvg_bounds"}
    if bucket == "ob_only":
        return {"ob_bounds"}
    if bucket == "both_fvg_and_ob_fire":
        return {"fvg_bounds", "ob_bounds", "overlap"}
    if bucket in {"ob_after_fvg", "fvg_after_ob"}:
        return {"fvg_bounds", "ob_bounds", "sequencing"}
    if bucket == "composite_overlock":
        return {"fvg_bounds", "ob_bounds", "overlap", "composite_arbitration"}
    if bucket == "disagreement":
        return {"disagreement_reason"}
    return set()


def _bucket_state(row: dict[str, Any]) -> dict[str, Any]:
    bucket = str(row.get("bucket") or "no_poi")
    relation = {
        "both_fvg_and_ob_fire": "FVG_AND_OB_AGREE_BUCKET_ONLY",
        "fvg_only": "FVG_ONLY",
        "ob_only": "OB_ONLY",
        "ob_after_fvg": "FVG_FIRST_OB_SECOND_BUCKET_ONLY",
        "fvg_after_ob": "OB_FIRST_FVG_SECOND_BUCKET_ONLY",
        "composite_overlock": "COMPOSITE_BUCKET_ONLY",
        "disagreement": "FVG_OB_DISAGREEMENT_OR_NON_MATCHING_FRAMEWORK",
        "no_poi": "NO_FVG_OR_OB_POI_BUCKET",
        "neither": "NEITHER_FVG_NOR_OB_BUCKET",
    }.get(bucket, "UNKNOWN_BUCKET")
    return {
        "bucket": bucket,
        "relation_state": relation,
        "fvg_fire": bucket in {"both_fvg_and_ob_fire", "fvg_only", "fvg_after_ob", "ob_after_fvg", "composite_overlock"},
        "ob_fire": bucket in {"both_fvg_and_ob_fire", "ob_only", "fvg_after_ob", "ob_after_fvg", "composite_overlock"},
        "agreement_status": "AGREE" if bucket == "both_fvg_and_ob_fire" else "SINGLE_FAMILY" if bucket in {"fvg_only", "ob_only"} else "DISAGREE_OR_OTHER",
    }


def _geometry_state(row: dict[str, Any]) -> dict[str, Any]:
    fvg_bounds = row.get("fvg_bounds")
    ob_bounds = row.get("ob_bounds")
    overlap = _bounds_overlap(fvg_bounds, ob_bounds)
    return {
        "fvg_bounds": fvg_bounds,
        "ob_bounds": ob_bounds,
        "overlap_computed": overlap,
        "sequencing": row.get("sequencing"),
        "composite_arbitration": row.get("composite_arbitration"),
        "disagreement_reason": row.get("disagreement_reason"),
    }


def _path_outcome_status(path: dict[str, Any] | None, resolution: dict[str, Any] | None) -> str | None:
    status = (resolution or {}).get("path_outcome_status") or (path or {}).get("path_outcome_status")
    if status:
        return str(status)
    label = str((resolution or path or {}).get("path_label") or "")
    label_map = {
        "entry_touched_then_reached_tp1": "ENTRY_TOUCHED_THEN_TP1",
        "went_through_entry_and_continued_to_sl": "ENTRY_TOUCHED_THEN_SL",
        "continued_without_entry_touch_to_tp_area": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
    }
    return label_map.get(label)


def _strategy_state(strategy_id: str, resolution: dict[str, Any] | None, mechanical: dict[str, Any] | None) -> dict[str, Any]:
    outcomes = ((resolution or {}).get("strategy_outcomes") or {})
    resolution_state = outcomes.get(strategy_id) if isinstance(outcomes, dict) else {}
    resolution_state = resolution_state if isinstance(resolution_state, dict) else {}
    mechanical = mechanical or {}
    score_status = mechanical.get("score_status") or resolution_state.get("score_status")
    strategy_status = mechanical.get("strategy_status") or resolution_state.get("strategy_status")
    outcome_status = mechanical.get("outcome_status") or resolution_state.get("outcome_status")
    if str(score_status or "").startswith("MISSING_REQUIRED"):
        scoreability = "NOT_SCORABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA"
    elif score_status in {None, "", "NOT_COMPUTABLE"}:
        scoreability = "NOT_SCORABLE_NO_COMPUTED_FVG_OB_OUTCOME"
    else:
        scoreability = "SCORED_OR_CONTEXT_AVAILABLE"
    return {
        "strategy_id": strategy_id,
        "strategy_status": strategy_status,
        "score_status": score_status,
        "outcome_status": outcome_status,
        "status_reason": mechanical.get("status_reason") or resolution_state.get("status_reason"),
        "scoreability_status": scoreability,
        "outcome_source": mechanical.get("outcome_source"),
        "strategy_proxy_r": mechanical.get("strategy_proxy_r"),
    }


def _latest_asof(resolution: dict[str, Any] | None, path: dict[str, Any] | None) -> str | None:
    return (resolution or {}).get("asof_latest_candle_utc") or (path or {}).get("asof_latest_candle_utc")


def _dependency_signature(
    *,
    confluence: dict[str, Any],
    resolution: dict[str, Any] | None,
    path: dict[str, Any] | None,
    ltf: dict[str, Any] | None,
    opportunity: dict[str, Any] | None,
    structural: dict[str, Any] | None,
    mechanical_rows: list[dict[str, Any] | None],
) -> str:
    parts = [
        confluence.get("created_at_utc"),
        confluence.get("_line_no"),
        (resolution or {}).get("row_key"),
        (resolution or {}).get("created_at_utc"),
        (path or {}).get("created_at_utc"),
        (ltf or {}).get("row_key"),
        (ltf or {}).get("created_at_utc"),
        (opportunity or {}).get("row_key"),
        (opportunity or {}).get("created_at_utc"),
        (structural or {}).get("row_key"),
        (structural or {}).get("created_at_utc"),
    ]
    parts.extend((row or {}).get("created_at_utc") for row in mechanical_rows)
    return _stable_hash(*parts)


def build_fvg_ob_confluence_audit_rows(
    confluence_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]],
    resolution_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    *,
    mechanical_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    ltf_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    opportunity_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    structural_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    generated_at_utc: str,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    confluence_by_candidate = _latest_by_candidate(_rows_with_lines(confluence_rows), date_prefix=decision_date_prefix)
    resolutions_by_candidate = _latest_by_candidate(_rows_with_lines(resolution_rows))
    paths_by_candidate = _latest_by_candidate(_rows_with_lines(path_rows))
    ltf_by_candidate = _latest_by_candidate(_rows_with_lines(ltf_rows))
    opportunities_by_candidate = _latest_by_candidate(_rows_with_lines(opportunity_rows))
    structural_by_candidate = _latest_by_candidate(_rows_with_lines(structural_rows))
    mechanical_by_key = _latest_mechanical_by_key(_rows_with_lines(mechanical_rows))

    rows: list[dict[str, Any]] = []
    for candidate_id, confluence in sorted(confluence_by_candidate.items(), key=lambda item: (str(item[1].get("decision_time_utc") or ""), item[0])):
        resolution = resolutions_by_candidate.get(candidate_id)
        path = paths_by_candidate.get(candidate_id)
        ltf = ltf_by_candidate.get(candidate_id)
        opportunity = opportunities_by_candidate.get(candidate_id)
        structural = structural_by_candidate.get(candidate_id)
        asof = str(_latest_asof(resolution, path) or "")
        fvg_ob_mech = _mechanical_for(mechanical_by_key, candidate_id, FVG_OB_STRATEGY_ID, asof)
        fvg_mid_mech = _mechanical_for(mechanical_by_key, candidate_id, FVG_MID_STRATEGY_ID, asof)

        source_statuses = _source_capture_statuses(confluence)
        raw_bucket = str(confluence.get("bucket") or "no_poi")
        source_capture_status = _overall_source_capture_status(source_statuses, raw_bucket)
        decision_no_leak = _decision_no_leak_status(confluence)
        bucket = _bucket_state(confluence)
        geometry = _geometry_state(confluence)
        fvg_ob_strategy = _strategy_state(FVG_OB_STRATEGY_ID, resolution, fvg_ob_mech)
        fvg_mid_strategy = _strategy_state(FVG_MID_STRATEGY_ID, resolution, fvg_mid_mech)

        actions: list[str] = []
        limitations: list[str] = []
        if not candidate_id:
            actions.append("FVG_OB_CANDIDATE_ID_MISSING")
        if decision_no_leak != "NO_POST_OUTCOME_STATE_IN_FVG_OB_DECISION_ROW":
            actions.append(decision_no_leak)
        if source_capture_status not in EXACT_SOURCE_CAPTURE_STATUSES:
            limitations.append(source_capture_status)
        required_source_fields = _required_source_fields_for_bucket(raw_bucket)
        for field, status in source_statuses.items():
            if required_source_fields and field not in required_source_fields:
                continue
            if status in {"SOURCE_NOT_CAPTURED", "PARTIAL_POI_POINT_CAPTURED_NOT_BOUNDS", "COMPOSITE_ARBITRATION_SOURCE_NOT_CAPTURED", "CONFLUENCE_BUCKET_CAPTURED_OVERLAP_EXACT_BOUNDS_MISSING"}:
                limitations.append(f"{field.upper()}_{status}")
        if not confluence.get("source_hash"):
            limitations.append("FVG_OB_SOURCE_HASH_NOT_CAPTURED")
        if not confluence.get("source_symbol"):
            limitations.append("FVG_OB_SOURCE_SYMBOL_NOT_CAPTURED")
        if not confluence.get("trade_id"):
            limitations.append("FVG_OB_TRADE_ID_NOT_CAPTURED")
        if not resolution:
            limitations.append("FVG_OB_RESOLUTION_ROW_NOT_AVAILABLE_YET")
        if not path:
            limitations.append("CANDIDATE_PATH_ROW_NOT_AVAILABLE_FOR_FVG_OB")
        if not opportunity:
            limitations.append("OPPORTUNITY_CLUSTER_ROW_NOT_AVAILABLE_FOR_DUPLICATE_AWARE_COUNTING")
        missing_fields = (structural or {}).get("missing_exact_required_fields") or {}
        if missing_fields.get("standalone_fvg_entry_geometry") == "SOURCE_NOT_CAPTURED" or not structural:
            limitations.append("STANDALONE_FVG_ENTRY_GEOMETRY_SOURCE_NOT_CAPTURED")
        if missing_fields.get("fvg_lock_state") == "SOURCE_NOT_CAPTURED" or not structural:
            limitations.append("FVG_LOCK_STATE_SOURCE_NOT_CAPTURED")
        if fvg_ob_strategy.get("scoreability_status") != "SCORED_OR_CONTEXT_AVAILABLE":
            limitations.append("FVG_OB_CONFLUENCE_STRATEGY_NOT_SCOREABLE")
        if fvg_mid_strategy.get("scoreability_status") != "SCORED_OR_CONTEXT_AVAILABLE":
            limitations.append("FVG_MID_EDGE_STRATEGY_NOT_SCOREABLE")

        resolved_path = bool((resolution or {}).get("resolution_status") == "RESOLVED_FROM_LIVE_PATH_ROW" or path)
        audit_status = ACTION_REQUIRED if actions else WAITING if not resolved_path else COMPLETE_WITH_LIMITATIONS if limitations else COMPLETE
        dependency_signature = _dependency_signature(
            confluence=confluence,
            resolution=resolution,
            path=path,
            ltf=ltf,
            opportunity=opportunity,
            structural=structural,
            mechanical_rows=[fvg_ob_mech, fvg_mid_mech],
        )
        row_key = _stable_hash(SCHEMA_VERSION, candidate_id, asof, dependency_signature)
        row = {
            "schema_version": SCHEMA_VERSION,
            "row_key": row_key,
            "source_dependency_signature": dependency_signature,
            "created_at_utc": generated_at_utc,
            "backfilled_at_utc": generated_at_utc,
            "candidate_id": candidate_id,
            "symbol": confluence.get("symbol"),
            "broker_symbol": confluence.get("broker_symbol"),
            "source_symbol": confluence.get("source_symbol"),
            "session": confluence.get("session") or confluence.get("kill_zone"),
            "kill_zone": confluence.get("kill_zone"),
            "side": confluence.get("side"),
            "framework": (confluence.get("decision_time_fields") or {}).get("framework"),
            "decision_time_utc": confluence.get("decision_time_utc"),
            "trade_id": confluence.get("trade_id"),
            "source_confluence_line_no": confluence.get("_line_no"),
            "source_confluence_created_at_utc": confluence.get("created_at_utc"),
            "bucket_state": bucket,
            "geometry_state": geometry,
            "source_capture_statuses": source_statuses,
            "fvg_ob_source_capture_status": source_capture_status,
            "decision_fvg_ob_no_leak_status": decision_no_leak,
            "candidate_outcome_lane": confluence.get("candidate_outcome_lane"),
            "decision_time_fields": confluence.get("decision_time_fields") or {},
            "latest_resolution_row_key": (resolution or {}).get("row_key"),
            "latest_resolution_status": (resolution or {}).get("resolution_status"),
            "latest_resolution_asof_utc": (resolution or {}).get("asof_latest_candle_utc"),
            "latest_path_asof_utc": (path or {}).get("asof_latest_candle_utc"),
            "path_label": (resolution or path or {}).get("path_label"),
            "path_outcome_status": _path_outcome_status(path, resolution),
            "ltf_path_order_label": (ltf or {}).get("path_order_label"),
            "ltf_terminal_outcome_status": (ltf or {}).get("terminal_outcome_status"),
            "fvg_ob_confluence_outcome": fvg_ob_strategy,
            "fvg_mid_edge_outcome": fvg_mid_strategy,
            "structural_missing_exact_required_fields": missing_fields,
            "opportunity_id": (opportunity or {}).get("opportunity_id"),
            "opportunity_counting_status": (opportunity or {}).get("opportunity_counting_status"),
            "opportunity_duplicate_status": (opportunity or {}).get("opportunity_duplicate_status"),
            "duplicate_aware_counting_status": (
                "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
                if (opportunity or {}).get("opportunity_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
                else (opportunity or {}).get("opportunity_counting_status") or "NO_OPPORTUNITY_CLUSTER_ROW"
            ),
            "fvg_ob_confluence_audit_status": audit_status,
            "documented_limitation_codes": sorted(set(limitations)),
            "action_required_codes": sorted(set(actions)),
            "manual_backfill_status": "BACKFILLED_FROM_FVG_OB_RESOLUTION_PATH_STRUCTURAL_AND_OPPORTUNITY_ROWS",
            "no_leak_status": "POST_DECISION_FVG_OB_AUDIT_NO_DECISION_FEATURE",
            "promotion_verdict": PROMOTION_VERDICT,
            "no_ai_calls": True,
            "no_canary_required": True,
            "no_execution": True,
            "ai_calls": 0,
            "canary_calls": 0,
            "order_calls": 0,
            "paid_data_calls": 0,
            "paid_fetch_attempted": False,
            "scoreability_rule": (
                "FVG/OB confluence rows remain exploratory. Bucket and decision fields can "
                "be source-captured at candidate time; exact FVG bounds, OB bounds, "
                "sequence, overlap, composite arbitration, and FVG lock state must be "
                "captured explicitly before FVG/OB strategies become scoreable."
            ),
        }
        rows.append(enrich_cp281_event_contract_fields(row, source_path=DEFAULT_OUTPUT))
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("fvg_ob_confluence_audit_status") or "UNKNOWN") for row in rows)
    source_counts = Counter(str(row.get("fvg_ob_source_capture_status") or "UNKNOWN") for row in rows)
    bucket_counts = Counter(str((row.get("bucket_state") or {}).get("bucket") or "UNKNOWN") for row in rows)
    relation_counts = Counter(str((row.get("bucket_state") or {}).get("relation_state") or "UNKNOWN") for row in rows)
    path_counts = Counter(str(row.get("path_outcome_status") or row.get("path_label") or "UNKNOWN") for row in rows)
    fvg_score_counts = Counter(str((row.get("fvg_ob_confluence_outcome") or {}).get("scoreability_status") or "UNKNOWN") for row in rows)
    fvg_mid_score_counts = Counter(str((row.get("fvg_mid_edge_outcome") or {}).get("scoreability_status") or "UNKNOWN") for row in rows)
    limitation_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    for row in rows:
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        action_counts.update(row.get("action_required_codes") or [])
    duplicate_countable = sum(
        1
        for row in rows
        if row.get("duplicate_aware_counting_status") == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
    )
    return {
        "schema_version": "fvg_ob_confluence_rolling_status_v1",
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_counts else "OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS",
        "confluence_rows": len(rows),
        "resolved_path_rows": sum(1 for row in rows if row.get("latest_resolution_status") == "RESOLVED_FROM_LIVE_PATH_ROW"),
        "exact_bounds_captured_rows": sum(
            1 for row in rows if row.get("fvg_ob_source_capture_status") in EXACT_SOURCE_CAPTURE_STATUSES
        ),
        "duplicate_aware_countable_path_rows": duplicate_countable,
        "status_counts": dict(status_counts),
        "source_capture_status_counts": dict(source_counts),
        "bucket_counts": dict(bucket_counts),
        "relation_state_counts": dict(relation_counts),
        "path_outcome_status_counts": dict(path_counts),
        "fvg_ob_scoreability_counts": dict(fvg_score_counts),
        "fvg_mid_edge_scoreability_counts": dict(fvg_mid_score_counts),
        "documented_limitation_counts": dict(limitation_counts),
        "action_required_counts": dict(action_counts),
        "no_leak_status": (
            "NO_DECISION_FVG_OB_LEAKS_DETECTED"
            if not any(row.get("decision_fvg_ob_no_leak_status") != "NO_POST_OUTCOME_STATE_IN_FVG_OB_DECISION_ROW" for row in rows)
            else "ACTION_REQUIRED_DECISION_FVG_OB_LEAK_STATUS_PRESENT"
        ),
    }
