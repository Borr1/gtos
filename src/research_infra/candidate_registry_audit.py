"""Candidate-registry contract audit rows.

These helpers create append-only research rows that document whether each live
candidate row has the required decision-time registry fields, confluence source
statuses, L2 terminal state, and structural metadata. They do not call AI,
canary, broker, MT5, or paid data APIs.
"""

from __future__ import annotations

from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "candidate_registry_audit_v1"
COMPLETE = "CANDIDATE_REGISTRY_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "CANDIDATE_REGISTRY_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "CANDIDATE_REGISTRY_ACTION_REQUIRED"

HARD_REQUIRED_FIELDS = (
    "schema_version",
    "candidate_id",
    "created_at_utc",
    "symbol",
    "broker_symbol",
    "decision_time_utc",
    "source_file",
    "framework",
    "analysis_decision",
    "final_outcome_at_log",
    "trade_parameters",
    "external_confluence",
    "strategy_snapshots",
    "verification",
    "no_leak_status",
    "promotion_verdict",
)

STRUCTURAL_FLAG_FIELDS = (
    "h1_setup_present",
    "m15_confirmation_present",
    "frameworks_evaluated_present",
    "mso_summary_present",
    "standalone_fvg_geometry_present",
    "structural_lock_event_present",
    "reentry_state_present",
    "cost_aware_min_r_present",
)


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def trade_geometry_status(candidate: dict[str, Any]) -> str:
    params = candidate.get("trade_parameters")
    if not isinstance(params, dict) or not params:
        return "TRADE_GEOMETRY_MISSING"
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    entry = _num(params.get("entry_price"))
    stop = _num(params.get("stop_loss"))
    tp1 = _num(params.get("take_profit_1"))
    if entry is None or stop is None or tp1 is None:
        return "TRADE_GEOMETRY_NON_NUMERIC"
    if side == "LONG" and stop < entry < tp1:
        return "TRADE_GEOMETRY_VALID"
    if side == "SHORT" and tp1 < entry < stop:
        return "TRADE_GEOMETRY_VALID"
    return "TRADE_GEOMETRY_INVALID"


def _source_hash_status(candidate: dict[str, Any], limitations: list[str], actions: list[str]) -> str:
    if "source_hash" not in candidate:
        actions.append("SOURCE_HASH_FIELD_MISSING")
        return "SOURCE_HASH_FIELD_MISSING"
    if candidate.get("source_hash"):
        return "SOURCE_HASH_PRESENT"
    if candidate.get("source_file"):
        limitations.append("SOURCE_HASH_NULL_SOURCE_FILE_CAPTURED")
        return "SOURCE_HASH_NULL_SOURCE_FILE_CAPTURED"
    actions.append("SOURCE_HASH_NULL_AND_SOURCE_FILE_MISSING")
    return "SOURCE_HASH_NULL_AND_SOURCE_FILE_MISSING"


def _sierra_status(candidate: dict[str, Any], actions: list[str]) -> dict[str, Any]:
    external = candidate.get("external_confluence") if isinstance(candidate.get("external_confluence"), dict) else {}
    sierra = external.get("sierra") if isinstance(external.get("sierra"), dict) else {}
    status = sierra.get("status")
    if not sierra:
        actions.append("MISSING_SIERRA_CONFLUENCE_OBJECT")
    elif not status:
        actions.append("MISSING_SIERRA_STATUS")
    return {
        "object_present": bool(sierra),
        "status": status,
        "source_status": sierra.get("source_status"),
        "parity_status": sierra.get("parity_status"),
        "interpretation_status": sierra.get("interpretation_status"),
        "paid_fetch_attempted": sierra.get("paid_fetch_attempted"),
    }


def _databento_status(
    candidate: dict[str, Any],
    limitations: list[str],
    actions: list[str],
) -> dict[str, Any]:
    external = candidate.get("external_confluence") if isinstance(candidate.get("external_confluence"), dict) else {}
    databento = external.get("databento") if isinstance(external.get("databento"), dict) else {}
    trigger_policy = databento.get("trigger_policy") if isinstance(databento.get("trigger_policy"), dict) else {}
    status = databento.get("status")
    trigger_status = trigger_policy.get("trigger_status")
    paid_fetch = databento.get("paid_fetch_attempted")
    paid_calls = databento.get("paid_data_calls")
    if not databento:
        actions.append("MISSING_DATABENTO_CONFLUENCE_OBJECT")
    elif not status:
        actions.append("MISSING_DATABENTO_STATUS")
    if databento and not trigger_status:
        if paid_fetch is False and status == "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE":
            limitations.append("DATABENTO_TRIGGER_STATUS_SOURCE_NOT_CAPTURED_PRE_TRIGGER_POLICY")
        elif paid_fetch in {False, None} and status == "SOURCE_BLOCKED":
            limitations.append("DATABENTO_TRIGGER_STATUS_IMPLIED_BY_SOURCE_BLOCKED_STATUS")
        else:
            actions.append("MISSING_DATABENTO_TRIGGER_STATUS")
    if paid_fetch is True:
        actions.append("DATABENTO_PAID_FETCH_ATTEMPTED")
    if paid_calls not in {None, 0, 0.0} and paid_fetch is not True:
        actions.append("DATABENTO_PAID_CALLS_NONZERO_WITHOUT_PAID_FETCH_FLAG")
    return {
        "object_present": bool(databento),
        "status": status,
        "trigger_status": trigger_status,
        "paid_fetch_attempted": paid_fetch,
        "paid_data_calls": paid_calls,
        "cost_policy": databento.get("cost_policy"),
    }


def _structural_status(
    candidate: dict[str, Any],
    limitations: list[str],
    actions: list[str],
) -> dict[str, Any]:
    metadata = candidate.get("structural_selector_metadata")
    if isinstance(metadata, dict) and metadata:
        missing_flags = [field for field in STRUCTURAL_FLAG_FIELDS if field not in metadata]
        if missing_flags:
            actions.append("STRUCTURAL_METADATA_FLAG_MISSING")
        return {
            "status": "STRUCTURAL_METADATA_PRESENT",
            "capture_status": metadata.get("capture_status"),
            "missing_flags": missing_flags,
            "presence_flags": {field: metadata.get(field) for field in STRUCTURAL_FLAG_FIELDS},
        }

    source_fields = ("h1_setup", "m15_confirmation", "frameworks_evaluated")
    if all(field not in candidate for field in source_fields):
        limitations.append("STRUCTURAL_SELECTOR_METADATA_SOURCE_NOT_CAPTURED_EARLY_CANDIDATE_ROW")
        return {
            "status": "STRUCTURAL_METADATA_SOURCE_NOT_CAPTURED",
            "capture_status": None,
            "missing_flags": list(STRUCTURAL_FLAG_FIELDS),
            "presence_flags": {},
        }

    actions.append("STRUCTURAL_METADATA_MISSING_WITH_PARTIAL_SOURCE_FIELDS")
    return {
        "status": "STRUCTURAL_METADATA_MISSING_WITH_PARTIAL_SOURCE_FIELDS",
        "capture_status": None,
        "missing_flags": list(STRUCTURAL_FLAG_FIELDS),
        "presence_flags": {},
    }


def build_candidate_registry_audit_row(
    line_no: int,
    candidate: dict[str, Any],
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    limitations: list[str] = []
    actions: list[str] = []
    missing_fields = [field for field in HARD_REQUIRED_FIELDS if _missing(candidate.get(field))]
    actions.extend(f"MISSING_REQUIRED_FIELD:{field}" for field in missing_fields)

    geometry_status = trade_geometry_status(candidate)
    if geometry_status != "TRADE_GEOMETRY_VALID":
        actions.append(geometry_status)

    source_hash_status = _source_hash_status(candidate, limitations, actions)
    sierra = _sierra_status(candidate, actions)
    databento = _databento_status(candidate, limitations, actions)
    structural = _structural_status(candidate, limitations, actions)

    if actions:
        audit_status = ACTION_REQUIRED
    elif limitations:
        audit_status = COMPLETE_WITH_LIMITATIONS
    else:
        audit_status = COMPLETE

    candidate_id = str(candidate.get("candidate_id") or "")
    decision_time = str(candidate.get("decision_time_utc") or "")
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": f"{candidate_id}|{decision_time}|{SCHEMA_VERSION}",
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "candidate_id": candidate_id,
        "candidate_line_no": line_no,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "source_file": candidate.get("source_file"),
        "source_hash": candidate.get("source_hash"),
        "source_hash_status": source_hash_status,
        "framework": candidate.get("framework"),
        "analysis_decision": candidate.get("analysis_decision"),
        "l2_final_state": candidate.get("final_outcome_at_log"),
        "l2_final_state_status": "L2_FINAL_STATE_PRESENT"
        if not _missing(candidate.get("final_outcome_at_log"))
        else "L2_FINAL_STATE_MISSING",
        "trade_geometry_status": geometry_status,
        "sierra_confluence_status": sierra,
        "databento_confluence_status": databento,
        "structural_metadata_status": structural,
        "missing_required_candidate_fields": missing_fields,
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": sorted(set(actions)),
        "registry_audit_status": audit_status,
        "manual_backfill_status": "BACKFILLED_FROM_STRATEGY_FOLLOW_CANDIDATE_ROW",
        "no_leak_status": "DECISION_TIME_CANDIDATE_REGISTRY_AUDIT_NO_POST_OUTCOME_FIELDS",
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


def build_candidate_registry_audit_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, candidate in candidate_rows:
        if decision_date_prefix and not str(candidate.get("decision_time_utc") or "").startswith(decision_date_prefix):
            continue
        rows.append(
            build_candidate_registry_audit_row(
                line_no,
                candidate,
                generated_at_utc=generated_at_utc,
            )
        )
    return rows
