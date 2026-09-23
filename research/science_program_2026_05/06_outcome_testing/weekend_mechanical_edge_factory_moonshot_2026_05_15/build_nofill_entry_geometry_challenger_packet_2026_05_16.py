#!/usr/bin/env python3
"""Build the no-fill entry geometry challenger packet.

The packet preserves all latest candidate path rows and materializes frozen
entry-geometry branch inputs for no-fill-to-TP-area cases. It only emits
source/readiness/design evidence; it does not score R, PnL, expectancy,
win-rate, live-readiness, or promotion.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

PATH_FOLLOW_PATH = REPO / "shadow_logs" / "candidate_path_follow.jsonl"
PENDING_LIFECYCLE_PATH = REPO / "shadow_logs" / "pending_limit_lifecycle.jsonl"
PENDING_AUDIT_PATH = REPO / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl"
LTF_PATH_ORDER_PATH = REPO / "shadow_logs" / "candidate_ltf_path_order.jsonl"
PATH_CONTRACT_AUDIT_PATH = REPO / "shadow_logs" / "candidate_path_contract_audit.jsonl"
NOFILL_FORWARD_CAPTURE_PATH = REPO / "shadow_logs" / "nofill_forward_source_capture.jsonl"
NOFILL_DESIGN_RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_DESIGN_RESULT_2026-05-15.json"
TICK_RECOVERY_AUDIT_PATH = (
    REPO
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_nofill_readonly_tick_recovery_export_source_control_audit"
    / "G12_NOFILL_READONLY_TICK_RECOVERY_AUDIT_REPORT_2026-05-10.json"
)
TICK_RECOVERY_RECONCILIATION_PATH = (
    REPO
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "nofill_readonly_tick_recovery_export_source_control_route"
    / "NOFILL_READONLY_TICK_RECOVERY_GROUPED_REQUEST_RECONCILIATION_LEDGER_2026-05-10.json"
)

RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_RESULT_2026-05-16.json"
INPUT_JOIN_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_INPUT_JOIN_2026-05-16.jsonl"
BRANCH_PACKET_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_BRANCH_PACKET_2026-05-16.jsonl"
READINESS_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_READINESS_LEDGER_2026-05-16.jsonl"
DENOMINATOR_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_DENOMINATOR_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "No-fill entry-geometry challenger packet only. Rows are source joins, "
    "frozen branch inputs, and readiness labels; no validation, R/PnL, "
    "expectancy, live-readiness, or live behavior change is claimed."
)

EVIDENCE_CLASS = "NOFILL_ENTRY_GEOMETRY_CHALLENGER_INPUT_ONLY"
NOFILL_LABEL = "continued_without_entry_touch_to_tp_area"
BRANCHES = [
    ("OFFSET_25", 0.25),
    ("OFFSET_50", 0.50),
    ("OFFSET_75", 0.75),
    ("OFFSET_100", 1.00),
    ("MARKET_OR_TOUCH_ROUTER", None),
]


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        PATH_FOLLOW_PATH,
        PENDING_LIFECYCLE_PATH,
        PENDING_AUDIT_PATH,
        LTF_PATH_ORDER_PATH,
        PATH_CONTRACT_AUDIT_PATH,
        NOFILL_FORWARD_CAPTURE_PATH,
        NOFILL_DESIGN_RESULT_PATH,
        TICK_RECOVERY_AUDIT_PATH,
        TICK_RECOVERY_RECONCILIATION_PATH,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "status": "HASHED",
                }
            )
        else:
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                    "status": "MISSING_FAIL_CLOSED",
                }
            )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("asof_latest_candle_utc") or row.get("checked_candle_time_utc") or ""),
        str(row.get("created_at_utc") or row.get("timestamp_utc") or row.get("backfilled_at_utc") or ""),
        str(row.get("row_key") or ""),
    )


def latest_by_candidate(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        if row.get("_parse_error"):
            continue
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        current = latest.get(candidate_id)
        if current is None or sort_key(row) >= sort_key(current):
            latest[candidate_id] = row
    return latest


def latest_lifecycle_rows() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_candidate: dict[str, dict[str, Any]] = {}
    by_trade: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(PENDING_LIFECYCLE_PATH):
        if row.get("_parse_error"):
            continue
        candidate_id = row.get("candidate_id")
        trade_id = row.get("trade_id")
        if candidate_id:
            current = by_candidate.get(candidate_id)
            if current is None or sort_key(row) >= sort_key(current):
                by_candidate[candidate_id] = row
        if trade_id:
            current = by_trade.get(trade_id)
            if current is None or sort_key(row) >= sort_key(current):
                by_trade[trade_id] = row
    return by_candidate, by_trade


def tick_recovery_by_candidate() -> dict[str, dict[str, Any]]:
    payload = read_json(TICK_RECOVERY_RECONCILIATION_PATH)
    by_candidate: dict[str, dict[str, Any]] = {}
    for group in payload.get("grouped_rows", []):
        for candidate_id in group.get("candidate_ids", []):
            by_candidate[candidate_id] = {
                "tick_recovery_terminal_status": group.get("terminal_status"),
                "tick_recovery_owner_request_id": group.get("owner_request_id"),
                "tick_recovery_coverage_status": group.get("coverage_status"),
                "tick_recovery_source_path": group.get("source_path"),
                "tick_recovery_source_sha256": group.get("source_sha256")
                or "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            }
    return by_candidate


def numeric(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_nested(row: dict[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = row
    for part in path:
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def rounded(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def proposed_entry(entry: float | None, last_close: float | None, fraction: float | None) -> float | None:
    if entry is None or last_close is None:
        return None
    if fraction is None:
        return rounded(last_close)
    return rounded(entry + (last_close - entry) * fraction)


def compact_source_status(
    ltf: dict[str, Any] | None,
    path_contract: dict[str, Any] | None,
    lifecycle: dict[str, Any] | None,
    lifecycle_audit: dict[str, Any] | None,
    forward_capture: dict[str, Any] | None,
    tick_recovery: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ltf_status": (ltf or {}).get("ltf_status", "MISSING"),
        "path_order_label": (ltf or {}).get("path_order_label"),
        "path_contract_status": (path_contract or {}).get("path_contract_status", "MISSING"),
        "path_ambiguity_status": (path_contract or {}).get("path_ambiguity_status", "MISSING"),
        "tick_order_claim_status": (path_contract or {}).get("tick_order_claim_status", "MISSING"),
        "lifecycle_fill_no_fill_label": (lifecycle or {}).get("fill_no_fill_label", "MISSING"),
        "lifecycle_intent_after_check": (lifecycle or {}).get("intent_after_check"),
        "lifecycle_audit_status": (lifecycle_audit or {}).get("pending_limit_lifecycle_audit_status", "MISSING"),
        "lifecycle_final_state_status": (lifecycle_audit or {}).get("final_state_status"),
        "forward_capture_status": "PRESENT" if forward_capture else "MISSING",
        "decision_spread_status": (forward_capture or {}).get("decision_spread_status", "MISSING"),
        "native_pending_order_type_status": (forward_capture or {}).get("native_pending_order_type_status", "MISSING"),
        "tick_recovery_terminal_status": (tick_recovery or {}).get("tick_recovery_terminal_status", "NO_MATCHING_RECOVERY_ROW"),
    }


def build_input_rows(
    latest_path: dict[str, dict[str, Any]],
    ltf_by_candidate: dict[str, dict[str, Any]],
    path_contract_by_candidate: dict[str, dict[str, Any]],
    lifecycle_by_candidate: dict[str, dict[str, Any]],
    lifecycle_by_trade: dict[str, dict[str, Any]],
    lifecycle_audit_by_candidate: dict[str, dict[str, Any]],
    forward_capture_by_candidate: dict[str, dict[str, Any]],
    tick_recovery: dict[str, dict[str, Any]],
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    input_rows: list[dict[str, Any]] = []
    denominator_rows: list[dict[str, Any]] = []
    for idx, (candidate_id, path_row) in enumerate(sorted(latest_path.items()), 1):
        trade_id = path_row.get("trade_id")
        lifecycle = lifecycle_by_candidate.get(candidate_id) or lifecycle_by_trade.get(str(trade_id))
        ltf = ltf_by_candidate.get(candidate_id)
        path_contract = path_contract_by_candidate.get(candidate_id)
        lifecycle_audit = lifecycle_audit_by_candidate.get(candidate_id)
        forward_capture = forward_capture_by_candidate.get(candidate_id)
        tick_recovery_row = tick_recovery.get(candidate_id)
        trade_params = path_row.get("trade_parameters") or {}
        sierra_features = get_nested(path_row, ["external_confluence", "sierra", "features"], {}) or {}
        source_status = compact_source_status(
            ltf,
            path_contract,
            lifecycle,
            lifecycle_audit,
            forward_capture,
            tick_recovery_row,
        )
        is_nofill_tp_area = path_row.get("path_label") == NOFILL_LABEL
        row = {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": EVIDENCE_CLASS,
            "input_join_id": f"NOFILL-GEOM-INPUT-{idx:05d}",
            "candidate_id": candidate_id,
            "symbol": path_row.get("symbol"),
            "broker_symbol": path_row.get("broker_symbol"),
            "side": path_row.get("side"),
            "framework": path_row.get("framework"),
            "decision_time_utc": path_row.get("decision_time_utc"),
            "asof_latest_candle_utc": path_row.get("asof_latest_candle_utc"),
            "trade_id": trade_id,
            "path_label": path_row.get("path_label"),
            "is_nofill_tp_area": is_nofill_tp_area,
            "entry_price": trade_params.get("entry_price"),
            "stop_loss": trade_params.get("stop_loss"),
            "take_profit_1": trade_params.get("take_profit_1"),
            "last_close": path_row.get("last_close"),
            "nearest_distance_to_entry": path_row.get("nearest_distance_to_entry"),
            "abs_nearest_distance_to_entry": (
                abs(numeric(path_row.get("nearest_distance_to_entry")))
                if numeric(path_row.get("nearest_distance_to_entry")) is not None
                else None
            ),
            "source_status": source_status,
            "sierra_status": get_nested(path_row, ["external_confluence", "sierra", "status"], "MISSING"),
            "sierra_event15_thin_depth10_rate": sierra_features.get("event15_thin_depth10_rate"),
            "sierra_event15_median_total_depth10": sierra_features.get("event15_median_total_depth10"),
            "sierra_event15_mid_change_ticks": sierra_features.get("event15_mid_change_ticks"),
            "databento_status": get_nested(path_row, ["external_confluence", "databento", "status"], "MISSING"),
            "source_manifest_hash": manifest_hash,
            "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            "safe_flags": SAFE_FLAGS,
        }
        input_rows.append(row)
        denominator_rows.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_CHALLENGER_DENOMINATOR",
                "candidate_id": candidate_id,
                "path_label": path_row.get("path_label"),
                "is_nofill_tp_area": is_nofill_tp_area,
                "symbol": path_row.get("symbol"),
                "side": path_row.get("side"),
                "framework": path_row.get("framework"),
                "decision_time_utc": path_row.get("decision_time_utc"),
                "has_ltf_path_order": ltf is not None,
                "has_path_contract_audit": path_contract is not None,
                "has_lifecycle_row": lifecycle is not None,
                "has_lifecycle_audit": lifecycle_audit is not None,
                "has_nofill_forward_capture": forward_capture is not None,
                "tick_recovery_terminal_status": source_status["tick_recovery_terminal_status"],
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                "safe_flags": SAFE_FLAGS,
            }
        )
    return input_rows, denominator_rows


def readiness_for(input_row: dict[str, Any]) -> tuple[str, list[str]]:
    status = input_row["source_status"]
    blockers: list[str] = []
    if status["ltf_status"] in ("MISSING", "SOURCE_BLOCKED"):
        blockers.append("BLOCKED_LTF_SOURCE")
    if status["lifecycle_audit_status"] == "MISSING":
        blockers.append("BLOCKED_LIFECYCLE_AUDIT_MISSING")
    if status["lifecycle_audit_status"] and "ACTION_REQUIRED" in str(status["lifecycle_audit_status"]):
        blockers.append("BLOCKED_LIFECYCLE_ACTION_REQUIRED")
    if status["decision_spread_status"] != "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE":
        blockers.append("BLOCKED_DECISION_SPREAD_MISSING")
    if status["tick_order_claim_status"] not in (
        "LOWER_TF_M1_ORDER_OBSERVED",
        "M15_OHLC_PATH_LABEL_ONLY",
    ):
        blockers.append("BLOCKED_TICK_ORDER_AMBIGUOUS")
    if status["tick_recovery_terminal_status"] == "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION":
        blockers.append("FAIL_CLOSED_RECOVERY_GAP")
    if not blockers:
        return "READY_INPUT_ONLY", []

    priority = [
        "FAIL_CLOSED_RECOVERY_GAP",
        "BLOCKED_LIFECYCLE_ACTION_REQUIRED",
        "BLOCKED_LTF_SOURCE",
        "BLOCKED_DECISION_SPREAD_MISSING",
        "BLOCKED_TICK_ORDER_AMBIGUOUS",
        "BLOCKED_LIFECYCLE_AUDIT_MISSING",
    ]
    for code in priority:
        if code in blockers:
            return code, blockers
    return blockers[0], blockers


def build_branch_and_readiness(input_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    branch_rows: list[dict[str, Any]] = []
    readiness_rows: list[dict[str, Any]] = []
    nofill_rows = [row for row in input_rows if row["is_nofill_tp_area"]]
    for idx, input_row in enumerate(nofill_rows, 1):
        entry = numeric(input_row.get("entry_price"))
        last_close = numeric(input_row.get("last_close"))
        for branch_name, fraction in BRANCHES:
            branch_id = f"NOFILL-GEOM-BRANCH-{idx:05d}-{branch_name}"
            proposed = proposed_entry(entry, last_close, fraction)
            branch = {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_CHALLENGER_BRANCH_INPUT",
                "branch_id": branch_id,
                "candidate_id": input_row["candidate_id"],
                "symbol": input_row["symbol"],
                "side": input_row["side"],
                "framework": input_row["framework"],
                "decision_time_utc": input_row["decision_time_utc"],
                "branch_type": branch_name,
                "offset_fraction_of_miss_distance": fraction,
                "original_entry_price": input_row.get("entry_price"),
                "input_last_close": input_row.get("last_close"),
                "proposed_entry_price_input_only": proposed,
                "entry_construction_rule": (
                    "interpolate original entry toward decision/path last_close by offset fraction; "
                    "MARKET_OR_TOUCH uses last_close as source-safe placeholder input"
                ),
                "stop_loss": input_row.get("stop_loss"),
                "take_profit_1": input_row.get("take_profit_1"),
                "abs_nearest_distance_to_entry": input_row.get("abs_nearest_distance_to_entry"),
                "source_manifest_hash": input_row["source_manifest_hash"],
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                "not_scored": True,
                "safe_flags": SAFE_FLAGS,
            }
            branch_rows.append(branch)
            readiness_status, blocker_codes = readiness_for(input_row)
            readiness_rows.append(
                {
                    "claim_boundary": CLAIM_BOUNDARY,
                    "evidence_class": "NOFILL_ENTRY_GEOMETRY_CHALLENGER_READINESS",
                    "branch_id": branch_id,
                    "candidate_id": input_row["candidate_id"],
                    "branch_type": branch_name,
                    "readiness_status": readiness_status,
                    "blocker_codes": blocker_codes,
                    "ltf_status": input_row["source_status"]["ltf_status"],
                    "path_contract_status": input_row["source_status"]["path_contract_status"],
                    "tick_order_claim_status": input_row["source_status"]["tick_order_claim_status"],
                    "lifecycle_audit_status": input_row["source_status"]["lifecycle_audit_status"],
                    "decision_spread_status": input_row["source_status"]["decision_spread_status"],
                    "tick_recovery_terminal_status": input_row["source_status"]["tick_recovery_terminal_status"],
                    "next_same_resource_action": (
                        "source-safe projection may proceed only after readiness blockers are cleared or stress-labeled"
                        if readiness_status != "READY_INPUT_ONLY"
                        else "build same-denominator no-score projection packet"
                    ),
                    "not_completion": "Readiness labels are current-work routing, not validation.",
                    "source_manifest_hash": input_row["source_manifest_hash"],
                    "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return branch_rows, readiness_rows


def build_bucket_rows(
    input_rows: list[dict[str, Any]],
    denominator_rows: list[dict[str, Any]],
    branch_rows: list[dict[str, Any]],
    readiness_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counters = {
        "path_label_counts": Counter(row["path_label"] for row in input_rows),
        "symbol_counts": Counter(row["symbol"] for row in input_rows),
        "nofill_symbol_counts": Counter(row["symbol"] for row in input_rows if row["is_nofill_tp_area"]),
        "nofill_side_counts": Counter(row["side"] for row in input_rows if row["is_nofill_tp_area"]),
        "nofill_framework_counts": Counter(row["framework"] for row in input_rows if row["is_nofill_tp_area"]),
        "ltf_status_counts": Counter(row["source_status"]["ltf_status"] for row in input_rows),
        "path_contract_status_counts": Counter(row["source_status"]["path_contract_status"] for row in input_rows),
        "decision_spread_status_counts": Counter(row["source_status"]["decision_spread_status"] for row in input_rows),
        "readiness_status_counts": Counter(row["readiness_status"] for row in readiness_rows),
        "branch_type_counts": Counter(row["branch_type"] for row in branch_rows),
        "denominator_has_ltf_counts": Counter(str(row["has_ltf_path_order"]) for row in denominator_rows),
        "denominator_has_forward_capture_counts": Counter(str(row["has_nofill_forward_capture"]) for row in denominator_rows),
    }
    rows: list[dict[str, Any]] = []
    for axis, counter in counters.items():
        for bucket, count in sorted(counter.items()):
            rows.append(
                {
                    "claim_boundary": CLAIM_BOUNDARY,
                    "evidence_class": "NOFILL_ENTRY_GEOMETRY_CHALLENGER_BUCKET",
                    "bucket_axis": axis,
                    "bucket": str(bucket),
                    "count": count,
                    "safe_flags": SAFE_FLAGS,
                }
            )
    return rows


def build_question_rows(input_rows: list[dict[str, Any]], readiness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    readiness_counts = Counter(row["readiness_status"] for row in readiness_rows)
    rows: list[dict[str, Any]] = []
    for idx, (status, count) in enumerate(sorted(readiness_counts.items()), 1):
        rows.append(
            {
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_CHALLENGER_QUESTION",
                "question_id": f"NOFILL-GEOM-QUESTION-{idx:03d}",
                "readiness_status": status,
                "branch_count": count,
                "question": "What source-safe repair, proxy, or projection packet is implied by this readiness class?",
                "next_same_resource_action": {
                    "READY_INPUT_ONLY": "build same-denominator no-score projection packet",
                    "BLOCKED_LTF_SOURCE": "use recovered tick/source artifacts or M15-conservative path proxy",
                    "BLOCKED_DECISION_SPREAD_MISSING": "join nofill forward capture spread rows or build source-safe spread proxy",
                    "BLOCKED_TICK_ORDER_AMBIGUOUS": "route to tick/path-order recovery or conservative stop-first ambiguity stress",
                    "BLOCKED_LIFECYCLE_ACTION_REQUIRED": "repair pending lifecycle/audit action-required row before projection",
                    "FAIL_CLOSED_RECOVERY_GAP": "use exact tick recovery owner/export route or Sierra alternate-source control",
                }.get(status, "preserve blocker and route to source repair"),
                "safe_flags": SAFE_FLAGS,
            }
        )
    rows.append(
        {
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "NOFILL_ENTRY_GEOMETRY_CHALLENGER_QUESTION",
            "question_id": f"NOFILL-GEOM-QUESTION-{len(rows) + 1:03d}",
            "readiness_status": "FULL_DENOMINATOR",
            "branch_count": len(input_rows),
            "question": "Which non-nofill path labels should become controls for no-fill entry geometry?",
            "next_same_resource_action": "use all 207 denominator rows as same-source context before any branch scoring",
            "safe_flags": SAFE_FLAGS,
        }
    )
    return rows


def update_manifest(generated_utc: str) -> None:
    if not OUTPUT_MANIFEST_PATH.exists():
        return
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    additions = [
        ("build_nofill_entry_geometry_challenger_packet_2026_05_16.py", "nofill_entry_geometry_challenger_builder"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_RESULT_2026-05-16.json", "nofill_entry_geometry_challenger_result"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_INPUT_JOIN_2026-05-16.jsonl", "nofill_entry_geometry_challenger_input_join"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_BRANCH_PACKET_2026-05-16.jsonl", "nofill_entry_geometry_challenger_branch_packet"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_READINESS_LEDGER_2026-05-16.jsonl", "nofill_entry_geometry_challenger_readiness_ledger"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_DENOMINATOR_LEDGER_2026-05-16.jsonl", "nofill_entry_geometry_challenger_denominator_ledger"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_BUCKET_LEDGER_2026-05-16.jsonl", "nofill_entry_geometry_challenger_bucket_ledger"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_QUESTION_LEDGER_2026-05-16.jsonl", "nofill_entry_geometry_challenger_question_ledger"),
        ("NOFILL_ENTRY_GEOMETRY_CHALLENGER_SUMMARY_2026-05-16.md", "nofill_entry_geometry_challenger_summary"),
    ]
    existing = {entry.get("path") for entry in manifest.get("artifacts", [])}
    for filename, artifact_type in additions:
        path = (
            "research/science_program_2026_05/06_outcome_testing/"
            "weekend_mechanical_edge_factory_moonshot_2026_05_15/"
            f"{filename}"
        )
        if path not in existing:
            manifest.setdefault("artifacts", []).append(
                {"path": path, "type": artifact_type, "status": "created"}
            )
    manifest["last_updated_utc"] = generated_utc
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, result: dict[str, Any]) -> None:
    row = {
        "ts_utc": generated_utc,
        "event_type": "nofill_entry_geometry_challenger_packet",
        "status": "done",
        "route": "nofill_entry_geometry_challenger",
        "details": "Joined all latest no-fill/path/lifecycle/source rows and emitted five frozen entry-geometry branch inputs for each no-fill-to-TP-area candidate.",
        "counts": result["counts"],
        "readiness_status_counts": result["readiness_status_counts"],
        "artifacts": [
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/build_nofill_entry_geometry_challenger_packet_2026_05_16.py",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/NOFILL_ENTRY_GEOMETRY_CHALLENGER_RESULT_2026-05-16.json",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/NOFILL_ENTRY_GEOMETRY_CHALLENGER_INPUT_JOIN_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/NOFILL_ENTRY_GEOMETRY_CHALLENGER_BRANCH_PACKET_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/NOFILL_ENTRY_GEOMETRY_CHALLENGER_READINESS_LEDGER_2026-05-16.jsonl",
            "research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/NOFILL_ENTRY_GEOMETRY_CHALLENGER_DENOMINATOR_LEDGER_2026-05-16.jsonl",
        ],
        "commands": [
            "py -3 research/science_program_2026_05/06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15/build_nofill_entry_geometry_challenger_packet_2026_05_16.py"
        ],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# No-Fill Entry Geometry Challenger Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, "
        "`outcome_review_opened=false`, `live_effect=false`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Readiness", ""])
    for key, value in sorted(result["readiness_status_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Next Work",
            "",
            "- Clear or proxy spread/LTF/tick-order blockers before any projection.",
            "- Build same-denominator no-score projection only for readiness-cleared rows.",
            "- Use all 207 denominator rows as same-source controls.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    latest_path = latest_by_candidate(PATH_FOLLOW_PATH)
    ltf_by_candidate = latest_by_candidate(LTF_PATH_ORDER_PATH)
    path_contract_by_candidate = latest_by_candidate(PATH_CONTRACT_AUDIT_PATH)
    lifecycle_by_candidate, lifecycle_by_trade = latest_lifecycle_rows()
    lifecycle_audit_by_candidate = latest_by_candidate(PENDING_AUDIT_PATH)
    forward_capture_by_candidate = latest_by_candidate(NOFILL_FORWARD_CAPTURE_PATH)
    tick_recovery = tick_recovery_by_candidate()
    design_counts = read_json(NOFILL_DESIGN_RESULT_PATH).get("counts", {})
    tick_audit = read_json(TICK_RECOVERY_AUDIT_PATH)

    input_rows, denominator_rows = build_input_rows(
        latest_path,
        ltf_by_candidate,
        path_contract_by_candidate,
        lifecycle_by_candidate,
        lifecycle_by_trade,
        lifecycle_audit_by_candidate,
        forward_capture_by_candidate,
        tick_recovery,
        manifest_hash,
    )
    branch_rows, readiness_rows = build_branch_and_readiness(input_rows)
    bucket_rows = build_bucket_rows(input_rows, denominator_rows, branch_rows, readiness_rows)
    question_rows = build_question_rows(input_rows, readiness_rows)

    write_jsonl(INPUT_JOIN_PATH, input_rows)
    write_jsonl(BRANCH_PACKET_PATH, branch_rows)
    write_jsonl(READINESS_LEDGER_PATH, readiness_rows)
    write_jsonl(DENOMINATOR_LEDGER_PATH, denominator_rows)
    write_jsonl(BUCKET_LEDGER_PATH, bucket_rows)
    write_jsonl(QUESTION_LEDGER_PATH, question_rows)

    readiness_status_counts = Counter(row["readiness_status"] for row in readiness_rows)
    result = {
        "schema": "nofill_entry_geometry_challenger_packet_v1",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": EVIDENCE_CLASS,
        "claim_boundary": CLAIM_BOUNDARY,
        "counts": {
            "latest_candidate_denominator_rows": len(input_rows),
            "denominator_rows": len(denominator_rows),
            "nofill_tp_area_rows": sum(1 for row in input_rows if row["is_nofill_tp_area"]),
            "branch_rows": len(branch_rows),
            "readiness_rows": len(readiness_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(manifest_rows),
            "ltf_path_order_input_rows": len(ltf_by_candidate),
            "path_contract_audit_input_rows": len(path_contract_by_candidate),
            "pending_lifecycle_audit_input_rows": len(lifecycle_audit_by_candidate),
            "nofill_forward_capture_input_rows": len(forward_capture_by_candidate),
            "tick_recovery_candidate_rows": len(tick_recovery),
        },
        "design_result_counts": design_counts,
        "readiness_status_counts": dict(sorted(readiness_status_counts.items())),
        "path_label_counts": dict(sorted(Counter(row["path_label"] for row in input_rows).items())),
        "nofill_group_counts": dict(
            sorted(
                Counter(
                    f"{row['symbol']}|{row['side']}|{row['framework']}"
                    for row in input_rows
                    if row["is_nofill_tp_area"]
                ).items()
            )
        ),
        "tick_recovery_audit_counts": tick_audit.get("count_summary", {}),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "clear or proxy readiness blockers",
            "build same-denominator no-score projection for readiness-cleared rows",
            "join all 207 denominator rows as controls",
            "route XAUUSD tick recovery gaps to Sierra alternate-source control where applicable",
        ],
        "not_completion": "This no-fill challenger packet does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, result)

    print(json.dumps({"ok": True, "counts": result["counts"], "readiness": result["readiness_status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
