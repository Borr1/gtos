#!/usr/bin/env python3
"""Build accepted M15 bounded-ordering detail from branch-local interval ledgers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

NEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_RESULT_2026-05-16.json"
NEXT_ACCEPTED = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ACCEPTED_LEDGER_2026-05-16.jsonl"
ACCEPTED_BUILDER_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M15_RESULT_LEDGER_2026-05-16.jsonl"
SELECTOR_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_M15_BOUNDS_SELECTOR_LEDGER_2026-05-16.jsonl"
PARAM_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_M15_LEDGER_2026-05-16.jsonl"
COLLAPSE_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_RESULT_2026-05-16.json"
COLLAPSE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
COLLAPSE_SUPPORT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_AMBIGUITY_SUPPORT_LEDGER_2026-05-16.jsonl"
COLLAPSE_PROXY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
COLLAPSE_REQUIREMENT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_REQUIREMENT_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_BOUNDED_ORDERING_DETAIL"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_LEDGER_2026-05-16.jsonl"
BRANCH_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_DETAIL_LEDGER_2026-05-16.jsonl"
TARGET_FIRST_LEDGER = ROUTE_DIR / f"{PREFIX}_TARGET_FIRST_CHALLENGER_LEDGER_2026-05-16.jsonl"
BOUNDS_SPLIT_LEDGER = ROUTE_DIR / f"{PREFIX}_BOUNDS_SPLIT_LEDGER_2026-05-16.jsonl"
SUPPORT_LEDGER = ROUTE_DIR / f"{PREFIX}_SUPPORT_DETAIL_LEDGER_2026-05-16.jsonl"
PROXY_LEDGER = ROUTE_DIR / f"{PREFIX}_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
REQUIREMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_REQUIREMENT_LEDGER_2026-05-16.jsonl"
SIDECAR_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_CONTEXT_LEDGER_2026-05-16.jsonl"
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
    "M15 bounded-ordering detail packet only. It consumes accepted primary M15 rows and "
    "full M15 sidecar/rejected context, computes target-first versus bounds-split detail "
    "from historical M15 interval proxy ledgers, and preserves exact chronology limits. "
    "It does not change live behavior and does not claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-SRC-{index:04d}",
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


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def avg(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["branch_queue_id"]: row for row in rows if row.get("branch_queue_id")}


def parse_session(route_candidate_id: str | None) -> str | None:
    if not route_candidate_id:
        return None
    parts = route_candidate_id.split("|")
    return parts[1] if len(parts) > 1 else None


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def main() -> int:
    generated_at = now_utc()
    next_result = read_json(NEXT_RESULT)
    collapse_result = read_json(COLLAPSE_RESULT)
    next_accepted_rows = read_jsonl(NEXT_ACCEPTED)
    accepted_m15_rows = [
        row
        for row in next_accepted_rows
        if row.get("primary_export_family") == "M15"
        and row.get("integrated_evidence_action") == "EXECUTE_M15_BOUNDED_ORDERING_BUILDER"
    ]
    accepted_ids = {row["branch_queue_id"] for row in accepted_m15_rows}
    next_by_branch = by_id(accepted_m15_rows)
    m15_result_rows = read_jsonl(ACCEPTED_BUILDER_M15)
    selector_rows = read_jsonl(SELECTOR_M15)
    param_rows = read_jsonl(PARAM_M15)
    collapse_branch_rows = read_jsonl(COLLAPSE_BRANCH)
    support_rows = read_jsonl(COLLAPSE_SUPPORT)
    proxy_rows = read_jsonl(COLLAPSE_PROXY)
    requirement_rows = read_jsonl(COLLAPSE_REQUIREMENT)
    m15_result_by_branch = by_id(m15_result_rows)
    selector_by_branch = by_id(selector_rows)
    param_by_branch = by_id(param_rows)
    collapse_by_branch = by_id(collapse_branch_rows)
    requirement_by_branch = by_id(requirement_rows)
    support_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in support_rows:
        if row.get("branch_queue_id"):
            support_by_branch[row.get("branch_queue_id")].append(row)
    proxies_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in proxy_rows:
        proxies_by_branch[row.get("branch_queue_id")].append(row)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            NEXT_RESULT,
            NEXT_ACCEPTED,
            ACCEPTED_BUILDER_M15,
            SELECTOR_M15,
            PARAM_M15,
            COLLAPSE_RESULT,
            COLLAPSE_BRANCH,
            COLLAPSE_SUPPORT,
            COLLAPSE_PROXY,
            COLLAPSE_REQUIREMENT,
        ],
        generated_at,
    )

    scope_rows: list[dict[str, Any]] = []
    sidecar_rows: list[dict[str, Any]] = []
    for row in m15_result_rows:
        branch_id = row.get("branch_queue_id")
        collapse = collapse_by_branch.get(branch_id, {})
        accepted_primary = branch_id in accepted_ids
        if accepted_primary:
            scope_class = "ACCEPTED_PRIMARY_M15_EXECUTION_SCOPE"
        elif row.get("m15_builder_result_status") == "M15_REJECTED_AVOID_OR_REDESIGN_REQUIRED":
            scope_class = "M15_REJECTED_AVOID_REDESIGN_SCOPE"
        else:
            scope_class = "M15_SIDECAR_CONTEXT_SCOPE"
        out = {
            "m15_bounded_ordering_scope_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-SCOPE-{len(scope_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "scope_class": scope_class,
            "accepted_primary_m15": accepted_primary,
            "route_candidate_id": row.get("route_candidate_id"),
            "route_session": row.get("route_session") or parse_session(row.get("route_candidate_id")),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "m15_builder_result_status": row.get("m15_builder_result_status"),
            "m15_selector_execution_status": row.get("m15_selector_execution_status"),
            "branch_result_class": collapse.get("branch_result_class"),
            "interval_sign_class": collapse.get("interval_sign_class"),
            "target_stop_result": collapse.get("target_stop_result"),
            "support_rows_matched": collapse.get("support_rows_matched"),
            "exact_chronology_claim": False,
        }
        with_common(out, generated_at, manifest_hash)
        scope_rows.append(out)
        if not accepted_primary:
            sidecar = dict(out)
            sidecar["m15_bounded_ordering_sidecar_id"] = f"OHLC-GTOS-M15-BOUNDED-DETAIL-SIDECAR-{len(sidecar_rows) + 1:05d}"
            sidecar.pop("m15_bounded_ordering_scope_id", None)
            sidecar_rows.append(sidecar)

    branch_detail_rows: list[dict[str, Any]] = []
    for accepted in accepted_m15_rows:
        branch_id = accepted["branch_queue_id"]
        m15_result = m15_result_by_branch.get(branch_id, {})
        selector = selector_by_branch.get(branch_id, {})
        param = param_by_branch.get(branch_id, {})
        collapse = collapse_by_branch.get(branch_id, {})
        supports = support_by_branch.get(branch_id, [])
        proxies = proxies_by_branch.get(branch_id, [])
        requirement = requirement_by_branch.get(branch_id, {})
        proxy_by_variant = {row.get("proxy_variant"): as_float(row.get("proxy_rstyle_value")) for row in proxies}
        support_cost_models = Counter(row.get("cost_model") for row in supports)
        support_offsets = Counter(row.get("ambiguous_bar_offset") for row in supports)
        support_match = Counter(row.get("support_match_status") for row in supports)
        status = m15_result.get("m15_builder_result_status")
        if status == "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND":
            detail_status = "M15_TARGET_FIRST_CONSERVATIVE_BOUND_ACCEPTED"
            next_action = "PRESERVE_M15_TARGET_FIRST_CONSERVATIVE_CHALLENGER"
        elif status == "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT":
            detail_status = "M15_BOUNDS_SPLIT_POSITIVE_MIDPOINT_REVIEW"
            next_action = "SPLIT_M15_TARGET_FIRST_STOP_FIRST_BOUNDS_BEFORE_SCALAR_USE"
        else:
            detail_status = "M15_UNEXPECTED_ACCEPTED_STATUS_REVIEW"
            next_action = "REVIEW_M15_ACCEPTED_STATUS"
        lower = as_float(collapse.get("interval_rstyle_lower_mean"))
        midpoint = as_float(collapse.get("interval_rstyle_midpoint_mean"))
        upper = as_float(collapse.get("interval_rstyle_upper_mean"))
        out = {
            "m15_bounded_ordering_branch_detail_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-BRANCH-{len(branch_detail_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "next_layer_evidence_branch_id": accepted.get("next_layer_evidence_branch_id"),
            "accepted_builder_branch_result_id": accepted.get("accepted_builder_branch_result_id"),
            "selector_execution_branch_id": accepted.get("selector_execution_branch_id"),
            "matrix_branch_id": accepted.get("matrix_branch_id") or m15_result.get("matrix_branch_id"),
            "m15_builder_result_id": m15_result.get("m15_builder_result_id"),
            "m15_selector_execution_id": selector.get("m15_selector_execution_id") or m15_result.get("m15_selector_execution_id"),
            "m15_parameter_id": param.get("m15_parameter_id") or m15_result.get("m15_parameter_id"),
            "m15_decision_id": m15_result.get("m15_decision_id") or selector.get("m15_decision_id"),
            "route_candidate_id": accepted.get("route_candidate_id") or m15_result.get("route_candidate_id"),
            "route_session": accepted.get("route_session") or m15_result.get("route_session") or parse_session(m15_result.get("route_candidate_id")),
            "symbol": accepted.get("symbol") or m15_result.get("symbol"),
            "side": accepted.get("side") or m15_result.get("side"),
            "entry_variant": accepted.get("entry_variant") or m15_result.get("entry_variant"),
            "target_stop_contract_id": accepted.get("target_stop_contract_id") or m15_result.get("target_stop_contract_id"),
            "primary_export_family": "M15",
            "branch_result_binary": accepted.get("branch_result_binary"),
            "branch_decision_class": accepted.get("branch_decision_class"),
            "accepted_for_next_executable_builder": accepted.get("accepted_for_next_executable_builder"),
            "integrated_evidence_action": accepted.get("integrated_evidence_action"),
            "integrated_evidence_state": accepted.get("integrated_evidence_state"),
            "integrated_evidence_score": accepted.get("integrated_evidence_score"),
            "m15_builder_result_status": status,
            "m15_builder_next_action": m15_result.get("m15_builder_next_action"),
            "m15_selector_execution_status": selector.get("m15_selector_execution_status") or m15_result.get("m15_selector_execution_status"),
            "m15_selector_policy": selector.get("m15_selector_policy"),
            "m15_selector_action": selector.get("m15_selector_action"),
            "m15_builder_policy": param.get("m15_builder_policy"),
            "m15_detail_status": detail_status,
            "next_same_resource_action": next_action,
            "branch_result_class": collapse.get("branch_result_class"),
            "interval_sign_class": collapse.get("interval_sign_class"),
            "interval_preservation_class": collapse.get("interval_preservation_class"),
            "interval_rstyle_lower_mean": lower,
            "interval_rstyle_midpoint_mean": midpoint,
            "interval_rstyle_upper_mean": upper,
            "interval_width": round(upper - lower, 6) if lower is not None and upper is not None else None,
            "stop_first_bound_proxy": proxy_by_variant.get("STOP_FIRST_BOUND"),
            "target_first_bound_proxy": proxy_by_variant.get("TARGET_FIRST_BOUND"),
            "midpoint_proxy": proxy_by_variant.get("MIDPOINT"),
            "close_direction_proxy": proxy_by_variant.get("CLOSE_DIRECTION_PROXY"),
            "support_rows_matched": len(supports),
            "support_cost_model_counts": compact_counter(support_cost_models),
            "support_ambiguous_bar_offset_counts": compact_counter(support_offsets),
            "support_match_status_counts": compact_counter(support_match),
            "target_stop_result": collapse.get("target_stop_result"),
            "requirement_status": requirement.get("requirement_status"),
            "exact_chronology_claim": False,
            "m15_exact_chronology_claim": False,
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "exact_success_cause": accepted.get("exact_success_cause"),
            "exact_failure_cause": accepted.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": accepted.get("exact_missing_geometry_or_source_reason"),
        }
        with_common(out, generated_at, manifest_hash)
        branch_detail_rows.append(out)

    target_first_rows = [
        row for row in branch_detail_rows if row.get("m15_builder_result_status") == "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND"
    ]
    bounds_split_rows = [
        row for row in branch_detail_rows if row.get("m15_builder_result_status") == "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT"
    ]

    support_detail_rows = []
    for row in [row for row in support_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m15_bounded_ordering_support_detail_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-SUPPORT-{len(support_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        with_common(out, generated_at, manifest_hash)
        support_detail_rows.append(out)
    proxy_detail_rows = []
    for row in [row for row in proxy_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m15_bounded_ordering_proxy_detail_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-PROXY-{len(proxy_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        with_common(out, generated_at, manifest_hash)
        proxy_detail_rows.append(out)
    requirement_detail_rows = []
    for row in [row for row in requirement_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m15_bounded_ordering_requirement_detail_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-REQ-{len(requirement_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        with_common(out, generated_at, manifest_hash)
        requirement_detail_rows.append(out)

    bucket_sources = {
        "scope_class": Counter(row.get("scope_class") for row in scope_rows),
        "accepted_symbol": Counter(row.get("symbol") for row in branch_detail_rows),
        "accepted_route_session": Counter(row.get("route_session") for row in branch_detail_rows),
        "accepted_side": Counter(row.get("side") for row in branch_detail_rows),
        "accepted_entry_variant": Counter(row.get("entry_variant") for row in branch_detail_rows),
        "m15_builder_result_status": Counter(row.get("m15_builder_result_status") for row in branch_detail_rows),
        "m15_selector_execution_status": Counter(row.get("m15_selector_execution_status") for row in branch_detail_rows),
        "interval_sign_class": Counter(row.get("interval_sign_class") for row in branch_detail_rows),
        "branch_result_class": Counter(row.get("branch_result_class") for row in branch_detail_rows),
        "target_stop_result": Counter(row.get("target_stop_result") for row in branch_detail_rows),
        "m15_detail_status": Counter(row.get("m15_detail_status") for row in branch_detail_rows),
        "support_cost_model": Counter(row.get("cost_model") for row in support_detail_rows),
        "support_ambiguous_bar_offset": Counter(row.get("ambiguous_bar_offset") for row in support_detail_rows),
        "support_match_status": Counter(row.get("support_match_status") for row in support_detail_rows),
        "proxy_variant": Counter(row.get("proxy_variant") for row in proxy_detail_rows),
        "requirement_status": Counter(row.get("requirement_status") for row in requirement_detail_rows),
    }
    bucket_rows = []
    for category, counter in sorted(bucket_sources.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-M15-BOUNDED-DETAIL-BUCKET-{len(bucket_rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket": str(bucket),
                        "row_count": int(count),
                        "share": round(count / total, 9) if total else None,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-M15-BOUNDED-DETAIL-QUESTION-001",
            "question": "Which accepted M15 rows are target-first conservative challengers versus bounds-split rows?",
            "answer_route": "Use branch detail m15_builder_result_status and m15_detail_status.",
        },
        {
            "question_id": "OHLC-GTOS-M15-BOUNDED-DETAIL-QUESTION-002",
            "question": "How much same-M15 ambiguity support remains under the accepted M15 branch scope?",
            "answer_route": "Use support detail rows and support_ambiguous_bar_offset buckets.",
        },
        {
            "question_id": "OHLC-GTOS-M15-BOUNDED-DETAIL-QUESTION-003",
            "question": "Which accepted M15 rows still require split treatment instead of scalar target-first use?",
            "answer_route": "Use bounds split ledger and interval_sign_class=INTERVAL_STRADDLES_ZERO.",
        },
        {
            "question_id": "OHLC-GTOS-M15-BOUNDED-DETAIL-QUESTION-004",
            "question": "What is the next executable queue after M15 detail?",
            "answer_route": "Continue SOURCE upgraded/degraded implication, positive challenger detail, and entry/adverse redesign detail builders.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_BOUNDED_ORDERING_DETAIL",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_next_accepted_rows": len(next_accepted_rows),
            "input_next_accepted_m15_rows": len(accepted_m15_rows),
            "input_m15_result_rows": len(m15_result_rows),
            "input_selector_m15_rows": len(selector_rows),
            "input_parameter_m15_rows": len(param_rows),
            "input_collapse_branch_rows": len(collapse_branch_rows),
            "input_collapse_support_rows": len(support_rows),
            "input_collapse_proxy_rows": len(proxy_rows),
            "input_collapse_requirement_rows": len(requirement_rows),
            "scope_rows": len(scope_rows),
            "branch_detail_rows": len(branch_detail_rows),
            "target_first_challenger_rows": len(target_first_rows),
            "bounds_split_rows": len(bounds_split_rows),
            "support_detail_rows": len(support_detail_rows),
            "proxy_variant_rows": len(proxy_detail_rows),
            "requirement_rows": len(requirement_detail_rows),
            "sidecar_context_rows": len(sidecar_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_next_counts": next_result.get("counts", {}),
        "upstream_collapse_counts": collapse_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "system_decision": {
            "system_recommendation": (
                "M15_BOUNDED_ORDERING_DETAIL_RESULT: preserve target-first conservative M15 "
                "challengers, split positive-midpoint bounds rows, keep exact chronology false, "
                "and continue SOURCE/positive/entry-adverse detail builders."
            ),
            "accepted_primary_m15_rows": len(branch_detail_rows),
            "target_first_challenger_rows": len(target_first_rows),
            "bounds_split_rows": len(bounds_split_rows),
            "sidecar_context_rows": len(sidecar_rows),
            "accepted_support_rows": len(support_detail_rows),
            "exact_chronology_true_rows": 0,
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (SCOPE_LEDGER, scope_rows),
        (BRANCH_LEDGER, branch_detail_rows),
        (TARGET_FIRST_LEDGER, target_first_rows),
        (BOUNDS_SPLIT_LEDGER, bounds_split_rows),
        (SUPPORT_LEDGER, support_detail_rows),
        (PROXY_LEDGER, proxy_detail_rows),
        (REQUIREMENT_LEDGER, requirement_detail_rows),
        (SIDECAR_LEDGER, sidecar_rows),
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
                "# Historical OHLC GTOS Replay Branch M15 Bounded Ordering Detail",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Scope rows: `{len(scope_rows)}`",
                f"- Accepted primary M15 rows: `{len(branch_detail_rows)}`",
                f"- Target-first conservative challenger rows: `{len(target_first_rows)}`",
                f"- Bounds-split positive-midpoint rows: `{len(bounds_split_rows)}`",
                f"- Accepted same-M15 ambiguity support rows: `{len(support_detail_rows)}`",
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
                "type": "branch_m15_bounded_ordering_detail",
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
                    "event_type": "branch_m15_bounded_ordering_detail_built",
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
