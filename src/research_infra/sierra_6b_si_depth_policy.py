"""LTO-030 Sierra 6B common-second and SI source-definition policy.

This module turns the existing Sierra/Databento sampling audits into an
explicit source policy. It does not read Sierra depth files, call Databento, or
change live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "sierra_6b_si_depth_policy_status_v1"
REPORT_SCHEMA_VERSION = "lto030_6b_si_depth_policy_v1"
LTO_ID = "LTO-030"
FOLLOW_ID = "LIVE-FOLLOW-028"

MAX_COMMON_DELTA_CONTRACTS_6B = 5.0
MIN_EVENT15_COMMON_SECONDS_6B = 600
MIN_PRE60_COMMON_SECONDS_6B = 2400
MIN_COMMON_JACCARD_6B = 0.90

REQUIRED_POLICY_FIELDS = (
    "sample_alignment_policy",
    "reference_second_source",
    "common_second_count",
    "coverage_jaccard",
    "all_seconds_max_abs_delta",
    "common_seconds_max_abs_delta",
    "feature_claim_boundary",
)

NO_DECISION_COUNTERS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path | str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def source_signature(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        if path.exists():
            digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        else:
            digest.update(b"missing")
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def window_metrics(audit: dict[str, Any], window: str) -> dict[str, Any]:
    item = (audit.get("windows") or {}).get(window) or {}
    coverage = item.get("coverage") or {}
    all_summary = ((item.get("all_seconds") or {}).get("delta_summary") or {})
    common_summary = ((item.get("common_seconds") or {}).get("delta_summary") or {})
    return {
        "window": window,
        "classification": item.get("classification"),
        "sierra_count": coverage.get("sierra_count"),
        "databento_count": coverage.get("databento_count"),
        "common_count": coverage.get("common_count"),
        "coverage_jaccard": coverage.get("coverage_jaccard"),
        "all_seconds_max_abs_delta": all_summary.get("max_abs_delta"),
        "common_seconds_max_abs_delta": common_summary.get("max_abs_delta"),
        "common_seconds_nonzero_delta_count": common_summary.get("nonzero_delta_count"),
    }


def _window_passes_6b(metrics: dict[str, Any], *, min_common_seconds: int) -> bool:
    common_delta = _safe_float(metrics.get("common_seconds_max_abs_delta"))
    jaccard = _safe_float(metrics.get("coverage_jaccard"))
    common_count = metrics.get("common_count")
    try:
        common_count_int = int(common_count)
    except (TypeError, ValueError):
        common_count_int = 0
    return (
        metrics.get("classification") == "SAMPLING_CLOCK_MAJOR_CONTRIBUTOR"
        and common_delta is not None
        and common_delta <= MAX_COMMON_DELTA_CONTRACTS_6B
        and jaccard is not None
        and jaccard >= MIN_COMMON_JACCARD_6B
        and common_count_int >= min_common_seconds
    )


def classify_6b_alignment(audit: dict[str, Any]) -> dict[str, Any]:
    pre60 = window_metrics(audit, "pre60")
    event15 = window_metrics(audit, "event15")
    passed = _window_passes_6b(pre60, min_common_seconds=MIN_PRE60_COMMON_SECONDS_6B) and _window_passes_6b(
        event15,
        min_common_seconds=MIN_EVENT15_COMMON_SECONDS_6B,
    )
    return {
        "policy_status": "COMMON_SECOND_ALIGNMENT_POLICY_REGISTERED" if passed else "COMMON_SECOND_ALIGNMENT_NOT_READY",
        "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
        "parity_status": "COMMON_SECOND_ALIGNMENT_REGISTERED_6B" if passed else "COMMON_SECOND_ALIGNMENT_FAILED_6B",
        "interpretation_status": (
            "REQUIRES_COMMON_SECOND_ALIGNED_FEATURE_ROW_BEFORE_USE"
            if passed
            else "BLOCKED_UNTIL_COMMON_SECOND_ALIGNMENT_PASSES"
        ),
        "depth_interpretation_allowed_current": False,
        "depth_interpretation_allowed_after_policy": bool(passed),
        "policy_type": "COMMON_SECOND_ALIGNMENT",
        "metrics": {"pre60": pre60, "event15": event15},
    }


def classify_si_definition(audits: list[dict[str, Any]]) -> dict[str, Any]:
    source_rows: list[dict[str, Any]] = []
    for audit in audits:
        event = audit.get("event") or {}
        pre60 = window_metrics(audit, "pre60")
        event15 = window_metrics(audit, "event15")
        source_rows.append(
            {
                "source_symbol": event.get("source_symbol"),
                "futures_symbol": event.get("futures_symbol"),
                "pre60": pre60,
                "event15": event15,
                "common_second_alignment_resolves_blocker": False,
            }
        )
    unresolved = [
        row
        for row in source_rows
        if row["event15"].get("classification") == "SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS"
        or (_safe_float(row["event15"].get("common_seconds_max_abs_delta")) or 0.0) > MAX_COMMON_DELTA_CONTRACTS_6B
    ]
    blocked = bool(source_rows) and len(unresolved) == len(source_rows)
    return {
        "policy_status": "SOURCE_DEPTH_DEFINITION_BLOCKED" if blocked else "SOURCE_DEPTH_DEFINITION_REVIEW_REQUIRED",
        "source_status": "LOCAL_SIERRA_DEPTH_CAPTURED",
        "parity_status": "SOURCE_DEPTH_DEFINITION_BLOCKED_SI" if blocked else "SOURCE_DEPTH_DEFINITION_MIXED_SI",
        "interpretation_status": "BLOCKED_DO_NOT_INTERPRET_DEPTH_UNTIL_SI_SOURCE_DEFINITION_REGISTERED",
        "depth_interpretation_allowed_current": False,
        "depth_interpretation_allowed_after_policy": False,
        "policy_type": "SI_SOURCE_DEPTH_DEFINITION",
        "metrics": source_rows,
    }


def _row_key(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]


def build_6b_status_row(
    audit: dict[str, Any],
    *,
    generated_at_utc: str,
    source_dependency_signature: str,
) -> dict[str, Any]:
    event = audit.get("event") or {}
    policy = classify_6b_alignment(audit)
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _row_key(SCHEMA_VERSION, LTO_ID, "GBPUSD", event.get("source_symbol"), policy["policy_status"], source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "status": policy["policy_status"],
        "symbol": "GBPUSD",
        "broker_symbol": "GBPUSD",
        "source_symbol": event.get("source_symbol"),
        "futures_symbol": event.get("futures_symbol"),
        "policy_type": policy["policy_type"],
        "source_status": policy["source_status"],
        "parity_status": policy["parity_status"],
        "interpretation_status": policy["interpretation_status"],
        "current_rows_policy": "KEEP_CURRENT_ROWS_BLOCKED_UNTIL_ALIGNED_FEATURE_ROW",
        "depth_interpretation_allowed_current": policy["depth_interpretation_allowed_current"],
        "depth_interpretation_allowed_after_policy": policy["depth_interpretation_allowed_after_policy"],
        "sample_alignment_policy": {
            "policy_version": "6b_common_second_alignment_v1",
            "required_mode": "INTERSECT_SIERRA_EOB_SECONDS_WITH_REFERENCE_MBP10_SECONDS",
            "reference_second_source": "databento_mbp10_or_registered_reference_sample_seconds",
            "required_policy_fields": list(REQUIRED_POLICY_FIELDS),
            "max_common_seconds_abs_delta_contracts": MAX_COMMON_DELTA_CONTRACTS_6B,
            "min_event15_common_seconds": MIN_EVENT15_COMMON_SECONDS_6B,
            "min_pre60_common_seconds": MIN_PRE60_COMMON_SECONDS_6B,
            "min_common_jaccard": MIN_COMMON_JACCARD_6B,
        },
        "validation_summary": policy["metrics"],
        "requirements_before_interpretation": [
            "feature row must declare sample_alignment_policy=6b_common_second_alignment_v1",
            "feature row must carry reference_second_source and common_second_count",
            "feature row must report all-seconds and common-seconds delta diagnostics",
            "current unaligned feature/source rows remain blockers and cannot be promoted",
        ],
        "no_leak_status": "SOURCE_POLICY_FROM_PREDECLARED_SAMPLING_AUDITS_NO_OUTCOME_FIELDS",
        "promotion_verdict": PROMOTION_VERDICT,
        **NO_DECISION_COUNTERS,
    }


def build_si_status_rows(
    audits: list[dict[str, Any]],
    *,
    generated_at_utc: str,
    source_dependency_signature: str,
) -> list[dict[str, Any]]:
    policy = classify_si_definition(audits)
    rows: list[dict[str, Any]] = []
    for item in policy["metrics"]:
        source_symbol = item.get("source_symbol")
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "row_key": _row_key(SCHEMA_VERSION, LTO_ID, "XAGUSD", source_symbol, policy["policy_status"], source_dependency_signature),
                "source_dependency_signature": source_dependency_signature,
                "created_at_utc": generated_at_utc,
                "backfilled_at_utc": generated_at_utc,
                "lto_id": LTO_ID,
                "follow_id": FOLLOW_ID,
                "status": policy["policy_status"],
                "symbol": "XAGUSD",
                "broker_symbol": "XAGUSD",
                "source_symbol": source_symbol,
                "futures_symbol": item.get("futures_symbol"),
                "policy_type": policy["policy_type"],
                "source_status": policy["source_status"],
                "parity_status": policy["parity_status"],
                "interpretation_status": policy["interpretation_status"],
                "current_rows_policy": "KEEP_CURRENT_ROWS_SOURCE_DEPTH_BLOCKED",
                "depth_interpretation_allowed_current": policy["depth_interpretation_allowed_current"],
                "depth_interpretation_allowed_after_policy": policy["depth_interpretation_allowed_after_policy"],
                "sample_alignment_policy": {
                    "policy_version": "si_source_depth_definition_blocker_v1",
                    "common_second_alignment_resolves_blocker": False,
                    "required_policy_fields": list(REQUIRED_POLICY_FIELDS),
                },
                "validation_summary": {"source": item},
                "requirements_before_interpretation": [
                    "register whether SIM or SIL is the correct Sierra equivalent for SI.v.0",
                    "prove common-second parity on multiple registered windows",
                    "define depth quantity semantics and contract-month/continuous-symbol mapping",
                    "do not interpret SI depth rows as Databento-equivalent while common-second deltas remain material",
                ],
                "no_leak_status": "SOURCE_POLICY_FROM_PREDECLARED_SAMPLING_AUDITS_NO_OUTCOME_FIELDS",
                "promotion_verdict": PROMOTION_VERDICT,
                **NO_DECISION_COUNTERS,
            }
        )
    return rows


def build_report_payload(
    *,
    audit_paths: dict[str, Path],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    gbp_audit = read_json(audit_paths["6b"])
    si_audits = [read_json(audit_paths["si"]), read_json(audit_paths["sil"])]
    signature = source_signature(list(audit_paths.values()))
    rows = [
        build_6b_status_row(gbp_audit, generated_at_utc=generated, source_dependency_signature=signature),
        *build_si_status_rows(si_audits, generated_at_utc=generated, source_dependency_signature=signature),
    ]
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "MISSING")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "lto_id": LTO_ID,
        "follow_id": FOLLOW_ID,
        "status": "OK_WITH_6B_POLICY_AND_SI_BLOCKER",
        "promotion_verdict": PROMOTION_VERDICT,
        "source_dependency_signature": signature,
        "source_paths": {key: str(path) for key, path in audit_paths.items()},
        "status_counts": dict(sorted(status_counts.items())),
        "status_rows": rows,
        "completion_evidence": {
            "common_second_alignment_policy_registered_for_6b": rows[0]["status"] == "COMMON_SECOND_ALIGNMENT_POLICY_REGISTERED",
            "si_depth_definition_remains_blocked": all(row["status"] == "SOURCE_DEPTH_DEFINITION_BLOCKED" for row in rows[1:]),
            "current_rows_keep_source_depth_blockers": all("KEEP_CURRENT_ROWS" in row["current_rows_policy"] for row in rows),
            "new_sierra_depth_scans": 0,
            "databento_calls": 0,
            "live_trading_behavior_changed": False,
        },
        "synthesis": {
            "summary": (
                "6B is unblocked at the policy level only when future rows declare and apply "
                "common-second alignment. Existing unaligned rows remain blocked. SI remains "
                "source/depth-definition blocked because common-second masking did not remove "
                "material depth deltas for SIM or SIL."
            ),
            "next_action": (
                "Use LTO-033/orderflow primitive work to require explicit sample-policy metadata "
                "before any GBPUSD/6B depth feature is interpreted; keep XAGUSD/SI source-status "
                "only until a stronger source definition is registered."
            ),
        },
    }
