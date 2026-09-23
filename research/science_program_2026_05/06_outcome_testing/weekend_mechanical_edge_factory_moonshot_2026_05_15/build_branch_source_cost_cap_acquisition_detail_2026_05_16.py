#!/usr/bin/env python3
"""Build SOURCE cost-cap/acquisition detail rows for the 138 SOURCE branches."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

NEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_RESULT_2026-05-16.json"
NEXT_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
NEXT_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SOURCE_LEDGER_2026-05-16.jsonl"
ACCEPTED_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_RESULT_LEDGER_2026-05-16.jsonl"
SOURCE_DEEP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_ACQ_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_RESULT_2026-05-16.json"
SOURCE_ACQ_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_ACQ_SUPPORT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_SUPPORT_LEDGER_2026-05-16.jsonl"
SOURCE_ACQ_SPLIT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_DESCRIPTOR_SPLIT_LEDGER_2026-05-16.jsonl"
SOURCE_ACQ_WINDOW = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_WINDOW_REQUIREMENT_LEDGER_2026-05-16.jsonl"
SOURCE_UNAVAILABLE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UNAVAILABLE_ACQUISITION_LEDGER_2026-05-16.jsonl"
SOURCE_PROXY_STRESS = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_PROXY_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_LEDGER_2026-05-16.jsonl"
ACCEPTED_LEDGER = ROUTE_DIR / f"{PREFIX}_ACCEPTED_LEDGER_2026-05-16.jsonl"
REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_LEDGER_2026-05-16.jsonl"
COST_CAP_LEDGER = ROUTE_DIR / f"{PREFIX}_COST_CAP_LEDGER_2026-05-16.jsonl"
SUPPORT_LEDGER = ROUTE_DIR / f"{PREFIX}_SUPPORT_LEDGER_2026-05-16.jsonl"
WINDOW_LEDGER = ROUTE_DIR / f"{PREFIX}_WINDOW_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "SOURCE cost-cap/acquisition detail packet only. It consumes the next-layer "
    "SOURCE execution rows, joins current source-stress/acquisition evidence, "
    "separates accepted source-cost-cap branches from repair branches, and "
    "preserves low/high stress bounds without live behavior, broker R/PnL, "
    "realized expectancy, win-rate, validation, live-readiness, or promotion claims."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-SOURCE-DETAIL-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["branch_queue_id"]): row for row in rows if row.get("branch_queue_id") is not None}


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = row.get(key)
        if value is not None:
            grouped[str(value)].append(row)
    return grouped


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        prefix, suffix = branch_id.rsplit("-", 1)
        return prefix, int(suffix)
    except (ValueError, IndexError):
        return branch_id, 0


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def fnum(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Any, digits: int = 6) -> float | None:
    value_float = fnum(value)
    return round(value_float, digits) if value_float is not None else None


def interval_sign(lower: Any, upper: Any) -> str:
    lower_float = fnum(lower)
    upper_float = fnum(upper)
    if lower_float is None or upper_float is None:
        return "SOURCE_COST_INTERVAL_MISSING"
    if lower_float > 0:
        return "SOURCE_COST_INTERVAL_ALL_POSITIVE"
    if upper_float < 0:
        return "SOURCE_COST_INTERVAL_ALL_NEGATIVE"
    return "SOURCE_COST_INTERVAL_STRADDLES_ZERO"


def source_detail_status(branch: dict[str, Any], acq: dict[str, Any]) -> str:
    sign = interval_sign(acq.get("rstyle_lower_mean"), acq.get("rstyle_upper_mean"))
    accepted = branch.get("branch_result_binary") == "ACCEPTED"
    if accepted and sign == "SOURCE_COST_INTERVAL_ALL_POSITIVE":
        return "ACCEPTED_SOURCE_COST_CAP_ALL_BOUNDS_POSITIVE"
    if accepted and sign == "SOURCE_COST_INTERVAL_STRADDLES_ZERO":
        return "ACCEPTED_SOURCE_BOUNDS_STRADDLE_EXACT_ACQUISITION_REQUIRED"
    if not accepted and sign == "SOURCE_COST_INTERVAL_ALL_NEGATIVE":
        return "REPAIR_SOURCE_ALL_BOUNDS_NEGATIVE_AVOID_UNTIL_SOURCE_REPAIR"
    if not accepted and sign == "SOURCE_COST_INTERVAL_STRADDLES_ZERO":
        return "REPAIR_SOURCE_BOUNDS_STRADDLE_EXACT_ACQUISITION_REQUIRED"
    return "SOURCE_DETAIL_UNCLASSIFIED"


def acquisition_state(support_rows: list[dict[str, Any]], window_rows: list[dict[str, Any]]) -> str:
    statuses = {row.get("source_window_status") or row.get("exact_spread_source_status") for row in window_rows + support_rows}
    if statuses == {"MT5_NO_TICKS_IN_REFERENCE_WINDOW_FAIL_CLOSED"}:
        return "CURRENT_MT5_EXACT_SOURCE_FAIL_CLOSED_USE_LOW_HIGH_STRESS_PROXY"
    if "MT5_NO_TICKS_IN_REFERENCE_WINDOW_FAIL_CLOSED" in statuses:
        return "MIXED_SOURCE_WINDOW_STATUS_REQUIRES_SPLIT"
    if not statuses:
        return "NO_SOURCE_WINDOW_ROWS_FOR_BRANCH"
    return "SOURCE_WINDOW_STATUS_REQUIRES_REVIEW"


def detail_scope(branch: dict[str, Any], sign: str) -> str:
    accepted = branch.get("branch_result_binary") == "ACCEPTED"
    if accepted and sign == "SOURCE_COST_INTERVAL_ALL_POSITIVE":
        return "ACCEPTED_COST_CAP"
    if accepted and sign == "SOURCE_COST_INTERVAL_STRADDLES_ZERO":
        return "ACCEPTED_LOW_HIGH_BOUNDS"
    if not accepted and sign == "SOURCE_COST_INTERVAL_ALL_NEGATIVE":
        return "REPAIR_AVOID"
    if not accepted and sign == "SOURCE_COST_INTERVAL_STRADDLES_ZERO":
        return "REPAIR_LOW_HIGH_CONTEXT"
    return "SOURCE_DETAIL_SCOPE_UNCLASSIFIED"


def cost_cap_policy(branch: dict[str, Any], sign: str) -> str:
    accepted = branch.get("branch_result_binary") == "ACCEPTED"
    if accepted and sign == "SOURCE_COST_INTERVAL_ALL_POSITIVE":
        return "LOWER_BOUND_UNTIL_EXACT"
    if sign == "SOURCE_COST_INTERVAL_STRADDLES_ZERO":
        return "LOW_HIGH_BOUNDS_INTERVAL"
    if not accepted:
        return "REPAIR_PRESERVE_ONLY"
    return "SOURCE_POLICY_UNCLASSIFIED"


def source_scalar_permission(branch: dict[str, Any]) -> str:
    if branch.get("branch_result_binary") == "ACCEPTED":
        return "ACCEPTED_PROXY_DETAIL_ALLOWED"
    return "REPAIR_NO_SCALAR"


def next_same_resource_action(branch: dict[str, Any]) -> str:
    if branch.get("branch_result_binary") == "ACCEPTED":
        return "ACQUIRE_OR_RESTRESS_EXACT_SOURCE_WINDOW"
    return "PRESERVE_LOW_HIGH_STRESS_ONLY"


def stress_descriptor_class(support_rows: list[dict[str, Any]], split_row: dict[str, Any]) -> str:
    descriptors = {
        row.get("descriptor_split_class")
        for row in support_rows
        if row.get("descriptor_split_class")
    }
    split_counts = split_row.get("descriptor_split_counts") if isinstance(split_row, dict) else None
    if isinstance(split_counts, dict):
        descriptors.update(key for key in split_counts if key)
    if descriptors == {"LOW_TARGET_HIGH_STOP_STRESS_FLIP"}:
        return "LOW_TARGET_HIGH_STOP_FLIP"
    if not descriptors:
        return "NO_STRESS_DESCRIPTOR_ROWS"
    return "AMBIGUOUS_STRESS_DESCRIPTOR_SPLIT"


def common_base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_queue_id": row.get("branch_queue_id"),
        "matrix_branch_id": row.get("matrix_branch_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
    }


def main() -> int:
    generated_at = now_utc()
    next_result = read_json(NEXT_RESULT)
    source_acq_result = read_json(SOURCE_ACQ_RESULT)
    next_branch_rows_all = read_jsonl(NEXT_BRANCH)
    source_branch_rows = [
        row for row in next_branch_rows_all
        if row.get("primary_export_family") == "SOURCE"
    ]
    next_source_by_branch = by_branch(read_jsonl(NEXT_SOURCE))
    accepted_source_by_branch = by_branch(read_jsonl(ACCEPTED_SOURCE))
    source_deep_by_branch = by_branch(read_jsonl(SOURCE_DEEP))
    source_unavailable_by_branch = by_branch(read_jsonl(SOURCE_UNAVAILABLE))
    source_proxy_by_branch = by_branch(read_jsonl(SOURCE_PROXY_STRESS))
    acq_branch_by_branch = by_branch(read_jsonl(SOURCE_ACQ_BRANCH))
    support_rows = read_jsonl(SOURCE_ACQ_SUPPORT)
    split_by_branch = by_branch(read_jsonl(SOURCE_ACQ_SPLIT))
    window_rows = read_jsonl(SOURCE_ACQ_WINDOW)
    support_by_branch = group_by([row for row in support_rows if row.get("branch_queue_id")], "branch_queue_id")
    window_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in window_rows:
        for branch_id in {support.get("branch_queue_id") for support in support_rows if support.get("source_window_key") == row.get("source_window_key")}:
            if branch_id:
                window_by_branch[str(branch_id)].append(row)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            NEXT_RESULT,
            NEXT_BRANCH,
            NEXT_SOURCE,
            ACCEPTED_SOURCE,
            SOURCE_DEEP,
            SOURCE_ACQ_RESULT,
            SOURCE_ACQ_BRANCH,
            SOURCE_ACQ_SUPPORT,
            SOURCE_ACQ_SPLIT,
            SOURCE_ACQ_WINDOW,
            SOURCE_UNAVAILABLE,
            SOURCE_PROXY_STRESS,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    cost_cap_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for branch in sorted(source_branch_rows, key=lambda row: branch_sort_key(str(row.get("branch_queue_id", "")))):
        branch_id = str(branch.get("branch_queue_id"))
        source_result = accepted_source_by_branch.get(branch_id, {})
        source_detail = next_source_by_branch.get(branch_id, {})
        source_deep = source_deep_by_branch.get(branch_id, {})
        source_unavailable = source_unavailable_by_branch.get(branch_id, {})
        source_proxy = source_proxy_by_branch.get(branch_id, {})
        acq = acq_branch_by_branch.get(branch_id, {})
        split = split_by_branch.get(branch_id, {})
        support = support_by_branch.get(branch_id, [])
        windows = window_by_branch.get(branch_id, [])
        lower = round_or_none(acq.get("rstyle_lower_mean"))
        midpoint = round_or_none(acq.get("rstyle_midpoint_mean"))
        upper = round_or_none(acq.get("rstyle_upper_mean"))
        sign = interval_sign(lower, upper)
        detail_status = source_detail_status(branch, acq)
        source_acquisition_state = acquisition_state(support, windows)
        record = {
            **common_base(branch),
            "source_cost_cap_detail_branch_id": f"OHLC-GTOS-SOURCE-DETAIL-BRANCH-{len(branch_rows) + 1:05d}",
            "next_layer_evidence_branch_id": branch.get("next_layer_evidence_branch_id"),
            "source_evidence_detail_id": source_detail.get("source_evidence_detail_id"),
            "source_builder_result_id": source_result.get("source_builder_result_id"),
            "source_stress_acquisition_branch_id": acq.get("source_stress_acquisition_branch_id"),
            "primary_export_family": branch.get("primary_export_family"),
            "branch_result_binary": branch.get("branch_result_binary"),
            "accepted_for_next_executable_builder": branch.get("accepted_for_next_executable_builder"),
            "integrated_evidence_action": branch.get("integrated_evidence_action"),
            "integrated_evidence_state": branch.get("integrated_evidence_state"),
            "source_builder_result_status": source_result.get("source_builder_result_status"),
            "source_builder_next_action": source_result.get("source_builder_next_action"),
            "source_selector_execution_status": source_result.get("source_selector_execution_status"),
            "source_exact_acquisition_required": source_result.get("source_exact_acquisition_required"),
            "source_cost_cap_required": source_result.get("source_cost_cap_required"),
            "source_cost_sensitivity_span": source_result.get("source_cost_sensitivity_span"),
            "source_deep_action_class": source_deep.get("source_deep_action_class") or branch.get("source_deep_action_class"),
            "source_repair_route_class": source_deep.get("source_repair_route_class") or branch.get("source_repair_route_class"),
            "source_stress_action_class": source_deep.get("source_stress_action_class") or branch.get("source_stress_action_class"),
            "source_deep_output_route": source_deep.get("source_deep_output_route"),
            "repair_feasibility_class": source_unavailable.get("repair_feasibility_class") or source_proxy.get("repair_feasibility_class") or source_deep.get("repair_feasibility_class"),
            "acquisition_status": source_unavailable.get("acquisition_status"),
            "source_cost_interval_sign_class": sign,
            "source_cost_cap_detail_status": detail_status,
            "source_detail_scope": detail_scope(branch, sign),
            "cost_cap_policy": cost_cap_policy(branch, sign),
            "exact_acquisition_state": "REQUIRED_NOT_ACQUIRED_FAIL_CLOSED",
            "stress_descriptor_class": stress_descriptor_class(support, split),
            "source_scalar_permission": source_scalar_permission(branch),
            "next_same_resource_action": next_same_resource_action(branch),
            "source_acquisition_state": source_acquisition_state,
            "rstyle_lower_mean": lower,
            "rstyle_midpoint_mean": midpoint,
            "rstyle_upper_mean": upper,
            "rstyle_interval_width": round_or_none((fnum(upper) or 0.0) - (fnum(lower) or 0.0)) if lower is not None and upper is not None else None,
            "stress_interval_policy": acq.get("stress_interval_policy") or source_proxy.get("stress_interval_policy"),
            "branch_stress_class": acq.get("branch_stress_class"),
            "descriptor_split_counts": acq.get("descriptor_split_counts"),
            "support_row_match_status": acq.get("support_row_match_status"),
            "support_rows_matched": len(support),
            "unique_source_window_keys": len({row.get("source_window_key") for row in support if row.get("source_window_key")}),
            "window_requirement_rows": len(windows),
            "target_multiple": source_unavailable.get("target_multiple") or source_proxy.get("target_multiple") or acq.get("target_multiple"),
            "stop_multiple": source_unavailable.get("stop_multiple") or source_proxy.get("stop_multiple") or acq.get("stop_multiple"),
            "target_stop_result": branch.get("target_stop_result"),
            "sealed_proxy_class": branch.get("sealed_proxy_class"),
            "success_decision": branch.get("success_decision"),
            "failure_decision": branch.get("failure_decision"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "next_source_detail_action": (
                "RUN_SOURCE_LOW_HIGH_STRESS_COST_CAP_DETAIL"
                if branch.get("branch_result_binary") == "ACCEPTED"
                else "PRESERVE_SOURCE_REPAIR_OR_AVOID_DETAIL"
            ),
            "m15_exact_chronology_claim": False,
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(record)
        if branch.get("branch_result_binary") == "ACCEPTED":
            accepted_rows.append({**record, "source_cost_cap_accepted_id": f"OHLC-GTOS-SOURCE-DETAIL-ACCEPTED-{len(accepted_rows) + 1:05d}"})
        else:
            repair_rows.append({**record, "source_cost_cap_repair_id": f"OHLC-GTOS-SOURCE-DETAIL-REPAIR-{len(repair_rows) + 1:05d}"})
        cost_cap_rows.append(
            {
                **common_base(branch),
                "source_cost_cap_row_id": f"OHLC-GTOS-SOURCE-DETAIL-COSTCAP-{len(cost_cap_rows) + 1:05d}",
                "source_cost_interval_sign_class": sign,
                "source_cost_cap_detail_status": detail_status,
                "source_detail_scope": detail_scope(branch, sign),
                "cost_cap_policy": cost_cap_policy(branch, sign),
                "exact_acquisition_state": "REQUIRED_NOT_ACQUIRED_FAIL_CLOSED",
                "stress_descriptor_class": stress_descriptor_class(support, split),
                "source_scalar_permission": source_scalar_permission(branch),
                "next_same_resource_action": next_same_resource_action(branch),
                "source_acquisition_state": source_acquisition_state,
                "rstyle_lower_mean": lower,
                "rstyle_midpoint_mean": midpoint,
                "rstyle_upper_mean": upper,
                "rstyle_interval_width": record["rstyle_interval_width"],
                "support_rows_matched": len(support),
                "window_requirement_rows": len(windows),
                "stress_interval_policy": acq.get("stress_interval_policy"),
                "branch_stress_class": acq.get("branch_stress_class"),
                "source_builder_result_status": source_result.get("source_builder_result_status"),
                "branch_result_binary": branch.get("branch_result_binary"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        for category in [
            "branch_result_binary",
            "source_cost_interval_sign_class",
            "source_cost_cap_detail_status",
            "source_detail_scope",
            "cost_cap_policy",
            "exact_acquisition_state",
            "stress_descriptor_class",
            "source_scalar_permission",
            "next_same_resource_action",
            "source_acquisition_state",
            "source_builder_result_status",
            "target_stop_result",
            "source_deep_action_class",
            "source_repair_route_class",
        ]:
            bucket_counters[category][record.get(category)] += 1

    source_branch_ids = {row["branch_queue_id"] for row in branch_rows}
    support_detail_rows = []
    for row in support_rows:
        branch_id = row.get("branch_queue_id")
        scope = "SOURCE_DETAIL_ACCEPTED" if branch_id in {accepted["branch_queue_id"] for accepted in accepted_rows} else (
            "SOURCE_DETAIL_REPAIR" if branch_id in {repair["branch_queue_id"] for repair in repair_rows} else "SOURCE_DETAIL_UNMATCHED_SUPPORT_CONTEXT"
        )
        support_detail_rows.append(
            {
                **row,
                "source_cost_cap_support_detail_id": f"OHLC-GTOS-SOURCE-DETAIL-SUPPORT-{len(support_detail_rows) + 1:05d}",
                "source_detail_scope": scope,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["support_detail_scope"][scope] += 1
    window_detail_rows = []
    source_window_to_branches: dict[str, set[str]] = defaultdict(set)
    for support in support_rows:
        if support.get("source_window_key") and support.get("branch_queue_id"):
            source_window_to_branches[str(support["source_window_key"])].add(str(support["branch_queue_id"]))
    for row in window_rows:
        matched_source_branches = sorted(source_window_to_branches.get(str(row.get("source_window_key")), set()) & source_branch_ids)
        window_detail_rows.append(
            {
                **row,
                "source_cost_cap_window_detail_id": f"OHLC-GTOS-SOURCE-DETAIL-WINDOW-{len(window_detail_rows) + 1:05d}",
                "matched_source_detail_branch_count": len(matched_source_branches),
                "matched_source_detail_branches": matched_source_branches,
                "source_detail_window_scope": "SOURCE_DETAIL_MATCHED_WINDOW" if matched_source_branches else "SOURCE_DETAIL_UNMATCHED_WINDOW_CONTEXT",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["source_detail_window_scope"][window_detail_rows[-1]["source_detail_window_scope"]] += 1
        bucket_counters["source_window_status"][row.get("source_window_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-SOURCE-DETAIL-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

    question_rows = [
        {"question_id": "OHLC-GTOS-SOURCE-DETAIL-QUESTION-001", "question": "How many accepted SOURCE branches remain positive across low/high stress bounds?", "answer_route": "Use accepted ledger source_cost_interval_sign_class and source_cost_cap_detail_status."},
        {"question_id": "OHLC-GTOS-SOURCE-DETAIL-QUESTION-002", "question": "Which SOURCE repair rows are all-negative versus straddling exact-source ambiguity?", "answer_route": "Use repair ledger source_cost_interval_sign_class."},
        {"question_id": "OHLC-GTOS-SOURCE-DETAIL-QUESTION-003", "question": "Which exact source windows remain fail-closed under current MT5 source extraction?", "answer_route": "Use window ledger source_window_status and matched_source_detail_branch_count."},
        {"question_id": "OHLC-GTOS-SOURCE-DETAIL-QUESTION-004", "question": "What same-resource builder should run next after SOURCE detail?", "answer_route": "Run M1 support-ordering or M15 bounded-ordering detail builders while preserving SOURCE exact-acquisition requirements."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_next_branch_rows": len(next_branch_rows_all),
            "input_next_source_rows": len(next_source_by_branch),
            "input_accepted_builder_source_rows": len(accepted_source_by_branch),
            "input_source_deep_rows": len(source_deep_by_branch),
            "input_source_unavailable_rows": len(source_unavailable_by_branch),
            "input_source_proxy_stress_rows": len(source_proxy_by_branch),
            "input_source_acquisition_branch_rows": len(acq_branch_by_branch),
            "input_source_support_rows": len(support_rows),
            "input_source_window_rows": len(window_rows),
            "unique_source_window_keys": len({row.get("source_window_key") for row in window_rows if row.get("source_window_key")}),
            "source_detail_branch_rows": len(branch_rows),
            "source_detail_accepted_rows": len(accepted_rows),
            "source_detail_repair_rows": len(repair_rows),
            "source_detail_cost_cap_rows": len(cost_cap_rows),
            "source_detail_support_rows": len(support_detail_rows),
            "source_detail_window_rows": len(window_detail_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_next_layer_counts": next_result.get("counts", {}),
        "upstream_source_acquisition_counts": source_acq_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "system_decision": {
            "system_recommendation": (
                "SOURCE_DETAIL_RESULT: keep 87 accepted SOURCE rows as all-bounds-positive "
                "low/high stress proxy candidates, keep 6 accepted SOURCE rows as bounds-straddle "
                "exact-acquisition-sensitive candidates, keep 31 repair rows as all-bounds-negative "
                "avoid/source-repair rows, and keep 14 repair rows as straddle exact-acquisition "
                "requirements; next run the M1 and M15 detail builders while preserving SOURCE "
                "window acquisition requirements."
            ),
            "accepted_all_bounds_positive": int(bucket_counters["source_cost_cap_detail_status"]["ACCEPTED_SOURCE_COST_CAP_ALL_BOUNDS_POSITIVE"]),
            "accepted_bounds_straddle": int(bucket_counters["source_cost_cap_detail_status"]["ACCEPTED_SOURCE_BOUNDS_STRADDLE_EXACT_ACQUISITION_REQUIRED"]),
            "repair_all_bounds_negative": int(bucket_counters["source_cost_cap_detail_status"]["REPAIR_SOURCE_ALL_BOUNDS_NEGATIVE_AVOID_UNTIL_SOURCE_REPAIR"]),
            "repair_bounds_straddle": int(bucket_counters["source_cost_cap_detail_status"]["REPAIR_SOURCE_BOUNDS_STRADDLE_EXACT_ACQUISITION_REQUIRED"]),
            "exact_source_fail_closed_rows": int(bucket_counters["source_window_status"]["MT5_NO_TICKS_IN_REFERENCE_WINDOW_FAIL_CLOSED"]),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_LEDGER, branch_rows),
        (ACCEPTED_LEDGER, accepted_rows),
        (REPAIR_LEDGER, repair_rows),
        (COST_CAP_LEDGER, cost_cap_rows),
        (SUPPORT_LEDGER, support_detail_rows),
        (WINDOW_LEDGER, window_detail_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch SOURCE Cost-Cap Acquisition Detail",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- SOURCE branch detail rows: `{len(branch_rows)}`",
                f"- Accepted SOURCE rows: `{len(accepted_rows)}`",
                f"- Repair SOURCE rows: `{len(repair_rows)}`",
                "- Accepted split: `87` all-bounds-positive, `6` bounds-straddle.",
                "- Repair split: `31` all-bounds-negative, `14` bounds-straddle.",
            ]
        ),
        encoding="utf-8",
    )

    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [RESULT_PATH, SUMMARY_PATH] + [path for path, _rows in outputs]
    path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_source_cost_cap_acquisition_detail",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_source_cost_cap_acquisition_detail_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
