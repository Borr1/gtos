"""NAS100/NQ orderflow adverse-selection diagnostic readiness.

This module is research/tooling only. It reads existing cached orderflow
artifacts and local shadow logs, then emits a status row that makes the
Databento/Sierra orderflow lane auditable without fetching new data.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from src.research_infra.databento_live_shadow import (
    GTOS_TO_DATABENTO,
    MAX_COST_PER_TRIGGER_USD,
    DAILY_SPEND_CAP_USD,
    COOLDOWN_SECONDS,
    MAX_RECORDS_PER_TRIGGER,
    MAX_TIMEOUT_SECONDS,
    POLICY_ID as DATABENTO_POLICY_ID,
    PROMOTION_VERDICT,
)


SCHEMA_VERSION = "nas100_orderflow_adverse_selection_status_v1"
REPORT_SCHEMA_VERSION = "lto011_nas100_orderflow_adverse_selection_readiness_v1"
DEFAULT_STATUS_LOG = Path("shadow_logs/nas100_orderflow_adverse_selection_status.jsonl")
DEFAULT_FORENSICS_JSON = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.json"
)
DEFAULT_FORWARD_READINESS_JSON = Path(
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_FORWARD_DIAGNOSTIC_READINESS_2026-05-04.json"
)
DEFAULT_DATABENTO_CONFLUENCE_LOG = Path("shadow_logs/databento_live_confluence.jsonl")
DEFAULT_DATABENTO_BUDGET_LOG = Path("shadow_logs/databento_live_budget_ledger.jsonl")
DEFAULT_BROKER_ACTUAL_R_LOG = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_FORWARD_REQUESTS_LOG = Path(
    "research/databento_orderflow_capture_2026-05-02/databento_forward_requests_2026-05-04.jsonl"
)

FLOOR_BROKER_ACTUAL_R_ROWS = 20
FLOOR_MBP10_CANDIDATE_ROWS = 30
NO_LICENSE_STATUS = "LIVE_SESSION_FAILED_NO_LICENSE"
LIVE_SUCCESS_STATUSES = {"LIVE_RECORD"}
BUDGET_SUCCESS_STATUSES = {"BUDGET_CHARGED", "LIVE_SESSION_CLOSED_ACTUAL_COST_UNKNOWN"}

NO_DECISION_COUNTERS = {
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "paid_data_calls": 0,
    "paid_fetch_attempted": False,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path | str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_source_dependency_signature(paths: Iterable[Path | str]) -> str:
    digest = hashlib.sha256()
    for raw_path in sorted(str(Path(item)) for item in paths):
        path = Path(raw_path)
        digest.update(raw_path.replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.exists()).encode("ascii"))
        digest.update(b"\0")
        file_hash = _file_sha256(path)
        digest.update(str(file_hash).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def stable_row_key(source_dependency_signature: str) -> str:
    payload = f"{SCHEMA_VERSION}|LTO-011|NAS100|NQ|{source_dependency_signature}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def latest_status(rows: list[dict[str, Any]], field: str) -> str | None:
    values = [str(row.get(field) or "") for row in rows if row.get(field)]
    return values[-1] if values else None


def count_databento_live_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    live_rows = [row for row in rows if row.get("status") == "LIVE_RECORD"]
    nas100_live = [
        row
        for row in live_rows
        if row.get("gtos_symbol") == "NAS100" or row.get("symbol") == "NAS100"
    ]
    schema_counts = Counter(str(row.get("schema") or "") for row in nas100_live)
    feature_class_counts = Counter(str(row.get("feature_class") or "") for row in nas100_live)
    return {
        "live_record_rows": len(live_rows),
        "nas100_live_record_rows": len(nas100_live),
        "nas100_live_mbp10_rows": sum(
            1 for row in nas100_live if str(row.get("schema") or "").lower() == "mbp-10"
        ),
        "nas100_live_mbo_rows": sum(
            1 for row in nas100_live if str(row.get("schema") or "").lower() == "mbo"
        ),
        "nas100_live_schema_counts": dict(sorted(schema_counts.items())),
        "nas100_live_feature_class_counts": dict(sorted(feature_class_counts.items())),
        "latest_status": latest_status(rows, "status"),
        "latest_message": latest_status(rows, "message"),
    }


def count_broker_actual_r(rows: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        row
        for row in rows
        if row.get("actual_r_claim_allowed") is True
        and row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED"
        and row.get("broker_actual_r") is not None
    ]
    by_trade: dict[str, dict[str, Any]] = {}
    for row in eligible:
        trade_id = str(row.get("trade_id") or row.get("fill_id") or row.get("ticket") or row.get("row_key") or "")
        if not trade_id:
            continue
        current = by_trade.get(trade_id)
        current_ts = str(current.get("backfilled_at_utc") or current.get("created_at_utc") or "") if current else ""
        row_ts = str(row.get("backfilled_at_utc") or row.get("created_at_utc") or "")
        if current is None or row_ts >= current_ts:
            by_trade[trade_id] = row
    nas100 = [
        row
        for row in by_trade.values()
        if row.get("symbol") == "NAS100" or row.get("broker_symbol") in {"NAS100", "NDX100"}
    ]
    return {
        "broker_actual_r_rows_all_symbols_unique": len(by_trade),
        "broker_actual_r_rows_nas100_unique": len(nas100),
        "broker_actual_r_trade_ids_nas100": sorted(
            str(row.get("trade_id") or row.get("fill_id") or row.get("ticket") or "")
            for row in nas100
        ),
    }


def cached_feed_counts(forensics: dict[str, Any]) -> dict[str, Any]:
    feeds = forensics.get("feeds") or {}
    out: dict[str, Any] = {}
    for feed_name, feed in feeds.items():
        coverage = feed.get("coverage") or {}
        label_coverage = feed.get("label_coverage") or {}
        concentration = feed.get("concentration") or {}
        stability = feed.get("stability") or {}
        total_depth = (stability.get("event15_total_depth") or {}).get("leave_one_date") or {}
        out[feed_name] = {
            "ok_rows": int(coverage.get("ok_rows") or 0),
            "candidate_rows": int(coverage.get("candidate_rows") or 0),
            "context_rows": int(coverage.get("context_rows") or 0),
            "synthetic_label_n": int(label_coverage.get("synthetic_label_n") or 0),
            "actual_r_n": int(label_coverage.get("actual_r_n") or 0),
            "candidate_top_date_share": (concentration.get("candidate_by_date") or {}).get("top_share"),
            "event15_total_depth_full_delta": total_depth.get("full_delta"),
            "event15_total_depth_leave_one_date_sign_flip_count": total_depth.get("sign_flip_count"),
            "event15_total_depth_leave_one_date_max_change": total_depth.get("max_abs_change_vs_full"),
        }
    return out


def feature_family_plan(forensics: dict[str, Any]) -> list[dict[str, Any]]:
    return list(forensics.get("feature_family_forward_plan") or [])


def forward_request_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nas100_rows = [
        row
        for row in rows
        if str(row.get("raw_symbol") or "").startswith("NQ")
        or str(row.get("source_event_id") or "").startswith("NAS100")
    ]
    return {
        "declared_databento_requests_total": len(rows),
        "declared_nas100_nq_requests": len(nas100_rows),
        "declared_nas100_nq_schema_counts": dict(
            sorted(Counter(str(row.get("schema") or "") for row in nas100_rows).items())
        ),
        "declared_nas100_nq_status_counts": dict(
            sorted(Counter(str(row.get("status") or "") for row in nas100_rows).items())
        ),
    }


def trigger_criteria() -> dict[str, Any]:
    mapping = GTOS_TO_DATABENTO["NAS100"]
    return {
        "policy_id": DATABENTO_POLICY_ID,
        "lto_id": "LTO-011",
        "follow_id": "LIVE-FOLLOW-011",
        "gtos_symbol": "NAS100",
        "broker_symbol": "NDX100",
        "databento_dataset": "GLBX.MDP3",
        "databento_raw_symbol": mapping["raw_symbol"],
        "databento_stype_in": mapping["stype_in"],
        "eligible_subjects": [
            "NAS100 live CANDIDATE rows",
            "NAS100 REJECTED_L2 rows with structural candidate context",
            "NAS100 explicit operator-declared parity/context windows",
        ],
        "default_window": {
            "start": "decision_time_utc_minus_60m",
            "asof_cutoff": "decision_time_utc",
            "end": "decision_time_utc_plus_15m_for_forensic_outcome_separation_only",
        },
        "schemas": {
            "trades": {
                "priority": "BASELINE_CONTEXT",
                "feature_class": "TRADES_ONLY",
                "use": "signed-flow, trade intensity, pace, range rejection",
            },
            "mbp-10": {
                "priority": "DEFAULT_DEPTH_DIAGNOSTIC",
                "feature_class": "MBP_DEPTH",
                "use": "top-10 total depth, thinness, imbalance, walls",
            },
            "mbo": {
                "priority": "TARGETED_ESCALATION_ONLY",
                "feature_class": "MBO_ORDER_FLOW",
                "use": "queue add/remove/pull pressure when MBP10 leaves a specific unanswered queue question",
            },
        },
        "join_keys": [
            "candidate_id",
            "source_opportunity_id",
            "decision_time_utc",
            "asof_cutoff_utc",
            "trigger_id",
        ],
        "cost_policy": {
            "max_cost_per_trigger_usd": MAX_COST_PER_TRIGGER_USD,
            "daily_spend_cap_usd": DAILY_SPEND_CAP_USD,
            "cooldown_seconds": COOLDOWN_SECONDS,
            "max_timeout_seconds": MAX_TIMEOUT_SECONDS,
            "max_records_per_trigger": MAX_RECORDS_PER_TRIGGER,
        },
    }


def readiness_status(
    *,
    cached_mbp10_candidate_rows: int,
    nas100_actual_r_rows: int,
    databento_live_license_available: bool,
    live_license_status: str | None,
) -> str:
    if str(live_license_status or "") == NO_LICENSE_STATUS:
        return "WAITING_FOR_DATABENTO_LIVE_LICENSE"
    if not databento_live_license_available:
        return "WAITING_FOR_DATABENTO_LIVE_SUCCESSFUL_SAMPLE"
    if cached_mbp10_candidate_rows < FLOOR_MBP10_CANDIDATE_ROWS:
        return "WAITING_FOR_MBP10_CANDIDATE_ROW_FLOOR"
    if nas100_actual_r_rows < FLOOR_BROKER_ACTUAL_R_ROWS:
        return "WAITING_FOR_BROKER_ACTUAL_R_FLOOR"
    return "READY_FOR_PREREGISTERED_DIAGNOSTIC_DOSSIER_REVIEW"


def databento_live_license_available(live_counts: dict[str, Any], latest_budget_status: str | None) -> bool:
    if live_counts.get("latest_status") == NO_LICENSE_STATUS or latest_budget_status == NO_LICENSE_STATUS:
        return False
    if live_counts.get("nas100_live_record_rows", 0) > 0:
        return True
    return live_counts.get("latest_status") in LIVE_SUCCESS_STATUSES or latest_budget_status in BUDGET_SUCCESS_STATUSES


def build_status_row(
    *,
    generated_at_utc: str,
    source_dependency_signature: str,
    forensics: dict[str, Any],
    forward_readiness: dict[str, Any],
    databento_confluence_rows: list[dict[str, Any]],
    databento_budget_rows: list[dict[str, Any]],
    broker_actual_r_rows: list[dict[str, Any]],
    forward_request_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    cached_counts = cached_feed_counts(forensics)
    mbp10_candidate_rows = int((cached_counts.get("MBP10_TOP10") or {}).get("candidate_rows") or 0)
    live_counts = count_databento_live_rows(databento_confluence_rows)
    broker_counts = count_broker_actual_r(broker_actual_r_rows)
    request_counts = forward_request_counts(forward_request_rows)
    latest_budget_status = latest_status(databento_budget_rows, "budget_status")
    live_license_status = live_counts.get("latest_status")
    license_available = databento_live_license_available(live_counts, latest_budget_status)
    status = readiness_status(
        cached_mbp10_candidate_rows=mbp10_candidate_rows,
        nas100_actual_r_rows=int(broker_counts["broker_actual_r_rows_nas100_unique"]),
        databento_live_license_available=license_available,
        live_license_status=live_license_status,
    )
    floors = {
        "broker_actual_r_rows": FLOOR_BROKER_ACTUAL_R_ROWS,
        "mbp10_candidate_rows": FLOOR_MBP10_CANDIDATE_ROWS,
    }
    current_counts = {
        **broker_counts,
        **request_counts,
        "cached_mbp10_candidate_rows": mbp10_candidate_rows,
        "cached_mbo_candidate_rows": int((cached_counts.get("MBO_TOP20") or {}).get("candidate_rows") or 0),
        "live_mbp10_candidate_rows": live_counts["nas100_live_mbp10_rows"],
        "live_mbo_candidate_rows": live_counts["nas100_live_mbo_rows"],
        "forward_readiness_v2b_forward_pair_rows": (forward_readiness.get("current_counts") or {}).get(
            "v2b_forward_pair_rows"
        ),
    }
    gates = {
        "databento_live_license_available": license_available,
        "broker_actual_r_floor_met": broker_counts["broker_actual_r_rows_nas100_unique"] >= FLOOR_BROKER_ACTUAL_R_ROWS,
        "mbp10_candidate_floor_met": mbp10_candidate_rows >= FLOOR_MBP10_CANDIDATE_ROWS,
        "promotion_claim_allowed": False,
        "adverse_selection_filter_allowed": False,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": stable_row_key(source_dependency_signature),
        "source_dependency_signature": source_dependency_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "lto_id": "LTO-011",
        "follow_id": "LIVE-FOLLOW-011",
        "status": status,
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "databento_raw_symbol": GTOS_TO_DATABENTO["NAS100"]["raw_symbol"],
        "evidence_class": "FUTURES_PROXY_TRANSFER",
        "promotion_verdict": PROMOTION_VERDICT,
        "trigger_criteria": trigger_criteria(),
        "feature_family_forward_plan": feature_family_plan(forensics),
        "cached_feature_status": (forensics.get("synthesis") or {}).get("status"),
        "cached_feed_counts": cached_counts,
        "databento_live_status": {
            **live_counts,
            "latest_budget_status": latest_budget_status,
            "license_blocker": live_license_status == NO_LICENSE_STATUS or latest_budget_status == NO_LICENSE_STATUS,
        },
        "floors": floors,
        "current_counts": current_counts,
        "readiness_gates": gates,
        "boundary": "No live binary orderflow filter, signal, risk modifier, or entry rule is created by this row.",
        "diagnostic_only": True,
        "no_leak_status": "STATUS_ROW_NOT_A_DECISION_FEATURE",
        **NO_DECISION_COUNTERS,
    }


def build_report(
    *,
    root: Path,
    generated_at_utc: str | None = None,
    forensics_path: Path = DEFAULT_FORENSICS_JSON,
    forward_readiness_path: Path = DEFAULT_FORWARD_READINESS_JSON,
    confluence_path: Path = DEFAULT_DATABENTO_CONFLUENCE_LOG,
    budget_path: Path = DEFAULT_DATABENTO_BUDGET_LOG,
    broker_actual_r_path: Path = DEFAULT_BROKER_ACTUAL_R_LOG,
    forward_requests_path: Path = DEFAULT_FORWARD_REQUESTS_LOG,
) -> dict[str, Any]:
    generated = generated_at_utc or utc_now_iso()
    paths = [
        root / forensics_path,
        root / forward_readiness_path,
        root / confluence_path,
        root / budget_path,
        root / broker_actual_r_path,
        root / forward_requests_path,
    ]
    signature = build_source_dependency_signature(paths)
    row = build_status_row(
        generated_at_utc=generated,
        source_dependency_signature=signature,
        forensics=read_json(root / forensics_path),
        forward_readiness=read_json(root / forward_readiness_path),
        databento_confluence_rows=read_jsonl(root / confluence_path),
        databento_budget_rows=read_jsonl(root / budget_path),
        broker_actual_r_rows=read_jsonl(root / broker_actual_r_path),
        forward_request_rows=read_jsonl(root / forward_requests_path),
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": generated,
        "promotion_verdict": PROMOTION_VERDICT,
        "lto_id": "LTO-011",
        "follow_id": "LIVE-FOLLOW-011",
        "status": row["status"],
        "status_row": row,
        "source_paths": [str(path.relative_to(root)) if path.is_relative_to(root) else str(path) for path in paths],
        "source_dependency_signature": signature,
        "completion_evidence": {
            "registered_trigger_criteria": True,
            "cached_artifacts_used_only": True,
            "new_databento_fetches_made_by_audit": 0,
            "paid_data_calls_made_by_audit": 0,
            "live_trading_behavior_changed": False,
            "promotion_claim_allowed": False,
        },
        "synthesis": {
            "summary": (
                "NAS100/NQ orderflow remains diagnostic-only. Cached depth/thinness is useful enough to keep "
                "collecting, but current live Databento is license-blocked and sample floors are not met."
            ),
            "next_action": (
                "After Databento GLBX.MDP3 live licensing is activated, run only registered NAS100/NQ candidate "
                "windows through the LTO-010 collector and keep MBO targeted to explicit unanswered queue questions."
            ),
        },
    }


def append_status_row_if_missing(row: dict[str, Any], path: Path | str = DEFAULT_STATUS_LOG) -> bool:
    target = Path(path)
    existing = read_jsonl(target)
    row_key = row.get("row_key")
    if any(item.get("row_key") == row_key for item in existing):
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return True
