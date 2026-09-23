"""Context/control ledger audit helpers.

This module is research/tooling only. It preserves CL/ZN/VIX/VXM context
questions as controls and blocks any accidental direct strategy-validation
claim from entering the context/control lane.

It does not call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "context_control_audit_v1"
COMPLETE = "CONTEXT_CONTROL_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "CONTEXT_CONTROL_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "CONTEXT_CONTROL_ACTION_REQUIRED"

CONTROL_FAMILIES = ("CL", "ZN", "VIX", "VXM")
CONTROL_ROLE = "CONTROL_ONLY"
DIRECT_VALIDATION_STATUS = "NOT_DIRECT_STRATEGY_VALIDATION"
STRATEGY_VALIDATION_STATUS = "CONTROL_CONTEXT_ONLY_NOT_STRATEGY_VALIDATION"
VALIDATION_SCOPE = "EXPLORATORY_CONTEXT_ONLY"

REGISTERED_CONTROL_QUESTIONS = (
    {
        "id": "VIX_VXM_VOL_REGIME_CONTEXT_V1",
        "family": "VIX/VXM",
        "question": "Does volatility-regime context explain candidate quality without becoming a direct trade validator?",
    },
    {
        "id": "ZN_RATES_STRESS_CONTEXT_V1",
        "family": "ZN",
        "question": "Does rates stress context identify index/metals regimes at decision time?",
    },
    {
        "id": "CL_LIQUIDITY_MACRO_CONTEXT_V1",
        "family": "CL",
        "question": "Does oil/liquidity macro stress context explain risk-on/off candidate behavior?",
    },
)

ALLOWED_CONTEXT_EVIDENCE_CLASSES = {"CONTROL_ONLY", "CROSS_INSTRUMENT_CONTEXT"}
ALLOWED_DIRECT_VALIDATION_STATUSES = {"", DIRECT_VALIDATION_STATUS, None}
ALLOWED_STRATEGY_VALIDATION_STATUSES = {"", STRATEGY_VALIDATION_STATUS, "NOT_STRATEGY_VALIDATION_CONTROL_ONLY", None}
ALLOWED_VALIDATION_SCOPES = {"", VALIDATION_SCOPE, None}

FORBIDDEN_DIRECT_VALIDATION_KEYS = {
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "outcome_r",
    "strategy_edge_validated",
    "strategy_score",
    "strategy_validation_claim",
    "validated_edge_claim",
    "validated_strategy_id",
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


def _latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for line_no, row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        item = dict(row)
        item["_line_no"] = line_no
        current_key = (
            _latest_clock(item),
            parse_utc(item.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            line_no,
        )
        previous = latest.get(candidate_id)
        previous_key = (
            _latest_clock(previous or {}),
            parse_utc((previous or {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            int((previous or {}).get("_line_no") or 0),
        )
        if current_key >= previous_key:
            latest[candidate_id] = item
    return latest


def _context_values(row: dict[str, Any]) -> dict[str, Any]:
    values = row.get("context_values")
    return values if isinstance(values, dict) else {}


def _context_source_statuses(row: dict[str, Any]) -> dict[str, str]:
    values = _context_values(row)
    statuses: dict[str, str] = {}
    key_variants = {
        "CL": ("cl", "CL", "cl_context", "oil_context"),
        "ZN": ("zn", "ZN", "zn_context", "rates_context"),
        "VIX": ("vix", "VIX", "vix_context", "vix_vxm", "vol_context"),
        "VXM": ("vxm", "VXM", "vxm_context", "vix_vxm", "vol_context"),
    }
    for family in CONTROL_FAMILIES:
        captured_key = next((key for key in key_variants[family] if key in values and values.get(key) is not None), None)
        statuses[family] = "CAPTURED_AS_OF_DECISION_TIME" if captured_key else "SOURCE_NOT_CAPTURED_AT_DECISION_TIME"
    return statuses


def _iter_nested_items(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, key, nested
            yield from _iter_nested_items(nested, path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            path = f"{prefix}[{index}]"
            yield from _iter_nested_items(nested, path)


def direct_validation_problems(row: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    top_direct = row.get("direct_strategy_validation_status")
    if top_direct not in ALLOWED_DIRECT_VALIDATION_STATUSES:
        problems.append(f"direct_strategy_validation_status={top_direct!r}")
    top_strategy = row.get("strategy_validation_status")
    if top_strategy not in ALLOWED_STRATEGY_VALIDATION_STATUSES:
        problems.append(f"strategy_validation_status={top_strategy!r}")
    top_scope = row.get("validation_scope")
    if top_scope not in ALLOWED_VALIDATION_SCOPES:
        problems.append(f"validation_scope={top_scope!r}")

    for path, key, value in _iter_nested_items(_context_values(row)):
        if key in FORBIDDEN_DIRECT_VALIDATION_KEYS and value is not None:
            problems.append(f"{path}={value!r}")
        if key == "direct_strategy_validation_status" and value not in ALLOWED_DIRECT_VALIDATION_STATUSES:
            problems.append(f"{path}={value!r}")
        if key == "strategy_validation_status" and value not in ALLOWED_STRATEGY_VALIDATION_STATUSES:
            problems.append(f"{path}={value!r}")
        if key == "validation_scope" and value not in ALLOWED_VALIDATION_SCOPES:
            problems.append(f"{path}={value!r}")
    return problems


def _event_window_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    values = _context_values(row)
    return {
        "window_anchor_utc": row.get("decision_time_utc"),
        "asof_cutoff_utc": row.get("asof_cutoff_utc") or row.get("decision_time_utc"),
        "pre_window_minutes": 60,
        "event_window_minutes": 15,
        "post_window_minutes": 0,
        "timestamp_convention": row.get("asof_timestamp_convention")
        or "latest_observation_at_or_before_decision_time",
        "context_family_source_statuses": _context_source_statuses(row),
        "captured_context_value_keys": sorted(values),
        "snapshot_status": "SAME_TIME_CONTEXT_WINDOW_REGISTERED_CONTROL_ONLY",
    }


def _exploratory_outcome_context(row: dict[str, Any], path_row: dict[str, Any] | None) -> dict[str, Any]:
    values = _context_values(row)
    return {
        "comparison_role": VALIDATION_SCOPE,
        "strategy_validation_status": STRATEGY_VALIDATION_STATUS,
        "direct_strategy_validation_status": DIRECT_VALIDATION_STATUS,
        "candidate_path_label": (path_row or {}).get("path_label"),
        "candidate_path_asof_utc": (path_row or {}).get("asof_latest_candle_utc"),
        "candidate_path_status": "PATH_JOINED_FOR_EXPLORATORY_CONTEXT_ONLY" if path_row else "PATH_NOT_JOINED",
        "final_outcome_at_log": values.get("final_outcome_at_log"),
        "note": "Context/control behavior may be compared to candidate outcomes only as exploratory context, not strategy validation.",
    }


def build_context_control_audit_row(
    source_row: dict[str, Any],
    *,
    path_row: dict[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    candidate_id = str(source_row.get("candidate_id") or "")
    family_statuses = _context_source_statuses(source_row)
    action_codes: list[str] = []
    limitation_codes: list[str] = []

    if source_row.get("control_only") is not True:
        action_codes.append("CONTEXT_ROW_NOT_CONTROL_ONLY")
    if source_row.get("promotion_verdict") != PROMOTION_VERDICT:
        action_codes.append("CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION")
    evidence_class = str(source_row.get("evidence_class") or "")
    if evidence_class not in ALLOWED_CONTEXT_EVIDENCE_CLASSES:
        action_codes.append("CONTEXT_ROW_INVALID_EVIDENCE_CLASS")
    elif evidence_class != CONTROL_ROLE:
        limitation_codes.append("LEGACY_EVIDENCE_CLASS_CROSS_INSTRUMENT_CONTEXT")

    direct_problems = direct_validation_problems(source_row)
    if direct_problems:
        action_codes.append("DIRECT_STRATEGY_VALIDATION_FORBIDDEN_IN_CONTEXT_CONTROL")

    for family, status in family_statuses.items():
        if status != "CAPTURED_AS_OF_DECISION_TIME":
            limitation_codes.append(f"{family}_SOURCE_NOT_CAPTURED_AT_DECISION_TIME")
    if not path_row:
        limitation_codes.append("CANDIDATE_PATH_NOT_JOINED_FOR_EXPLORATORY_CONTEXT")

    audit_status = ACTION_REQUIRED if action_codes else COMPLETE_WITH_LIMITATIONS if limitation_codes else COMPLETE
    source_dependency_signature = _stable_hash(
        SCHEMA_VERSION,
        candidate_id,
        source_row.get("decision_time_utc"),
        source_row.get("created_at_utc"),
        (path_row or {}).get("asof_latest_candle_utc"),
        (path_row or {}).get("path_label"),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("context_control_audit", source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated,
        "backfilled_at_utc": generated,
        "candidate_id": candidate_id,
        "symbol": source_row.get("symbol"),
        "broker_symbol": source_row.get("broker_symbol"),
        "decision_time_utc": source_row.get("decision_time_utc"),
        "context_question_id": source_row.get("context_question_id"),
        "context_family": source_row.get("context_family"),
        "registered_control_questions": list(REGISTERED_CONTROL_QUESTIONS),
        "control_role": CONTROL_ROLE,
        "control_only": True,
        "source_control_only": source_row.get("control_only"),
        "evidence_class_at_source": evidence_class,
        "normalized_evidence_class": CONTROL_ROLE,
        "direct_strategy_validation_status": DIRECT_VALIDATION_STATUS
        if not direct_problems
        else "DIRECT_STRATEGY_VALIDATION_FORBIDDEN",
        "strategy_validation_status": STRATEGY_VALIDATION_STATUS,
        "validation_scope": VALIDATION_SCOPE,
        "direct_validation_problem_paths": direct_problems,
        "context_family_source_statuses": family_statuses,
        "context_event_window_snapshot": _event_window_snapshot(source_row),
        "exploratory_outcome_context": _exploratory_outcome_context(source_row, path_row),
        "context_control_audit_status": audit_status,
        "action_required_codes": action_codes,
        "documented_limitation_codes": sorted(set(limitation_codes)),
        "manual_backfill_status": "BACKFILLED_OR_REFRESHED_FROM_CONTEXT_CONTROL_ROWS",
        "no_leak_status": "CONTEXT_CONTROL_ONLY_NO_DIRECT_STRATEGY_VALIDATION"
        if not action_codes
        else "CONTEXT_CONTROL_VALIDATION_BOUNDARY_BROKEN",
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


def build_context_control_audit_rows(
    context_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    path_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    *,
    generated_at_utc: str | None = None,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    context_with_lines = _rows_with_lines(context_rows)
    path_by_candidate = _latest_by_candidate(_rows_with_lines(path_rows))
    rows: list[dict[str, Any]] = []
    for _line_no, row in context_with_lines:
        if decision_date_prefix and not str(row.get("decision_time_utc") or "").startswith(decision_date_prefix):
            continue
        candidate_id = str(row.get("candidate_id") or "")
        rows.append(
            build_context_control_audit_row(
                row,
                path_row=path_by_candidate.get(candidate_id),
                generated_at_utc=generated_at_utc,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("context_control_audit_status") or "UNKNOWN") for row in rows)
    evidence_counts = Counter(str(row.get("evidence_class_at_source") or "UNKNOWN") for row in rows)
    direct_counts = Counter(str(row.get("direct_strategy_validation_status") or "UNKNOWN") for row in rows)
    source_counts: Counter[str] = Counter()
    outcome_counts = Counter(
        str((row.get("exploratory_outcome_context") or {}).get("candidate_path_label") or "PATH_NOT_JOINED")
        for row in rows
    )
    for row in rows:
        for family, status in (row.get("context_family_source_statuses") or {}).items():
            source_counts[f"{family}:{status}"] += 1
    return {
        "context_rows": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "source_evidence_class_counts": dict(sorted(evidence_counts.items())),
        "direct_strategy_validation_status_counts": dict(sorted(direct_counts.items())),
        "context_family_source_status_counts": dict(sorted(source_counts.items())),
        "exploratory_outcome_label_counts": dict(sorted(outcome_counts.items())),
        "action_required_rows": status_counts.get(ACTION_REQUIRED, 0),
        "control_only_rows": sum(1 for row in rows if row.get("control_role") == CONTROL_ROLE and row.get("control_only") is True),
        "no_promotion_rows": sum(1 for row in rows if row.get("promotion_verdict") == PROMOTION_VERDICT),
    }
