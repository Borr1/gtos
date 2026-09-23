#!/usr/bin/env python3
"""Build accepted M1 support-conflict detail from branch-local collapse ledgers."""

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
ACCEPTED_BUILDER_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M1_RESULT_LEDGER_2026-05-16.jsonl"
SELECTOR_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_M1_SUPPORT_CONFLICT_SELECTOR_LEDGER_2026-05-16.jsonl"
PARAM_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_BUILDER_PARAMETER_PACKET_M1_LEDGER_2026-05-16.jsonl"
COLLAPSE_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_RESULT_2026-05-16.json"
COLLAPSE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
COLLAPSE_SIGNATURE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_SIGNATURE_SUPPORT_LEDGER_2026-05-16.jsonl"
COLLAPSE_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_FAMILY_SUPPORT_LEDGER_2026-05-16.jsonl"
COLLAPSE_PROXY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_PROXY_VARIANT_LEDGER_2026-05-16.jsonl"
COLLAPSE_REQUIREMENT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_REQUIREMENT_LEDGER_2026-05-16.jsonl"
SOURCE_MATERIALIZATION_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION_RESULT_2026-05-16.json"
SOURCE_BAR_RECOMPUTE_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE_RESULT_2026-05-16.json"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_SUPPORT_CONFLICT_DETAIL"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_LEDGER_2026-05-16.jsonl"
BRANCH_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_DETAIL_LEDGER_2026-05-16.jsonl"
STABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_STABLE_CHALLENGER_LEDGER_2026-05-16.jsonl"
CONFLICT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONFLICT_SPLIT_LEDGER_2026-05-16.jsonl"
SIGNATURE_LEDGER = ROUTE_DIR / f"{PREFIX}_SIGNATURE_SUPPORT_DETAIL_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_SUPPORT_DETAIL_LEDGER_2026-05-16.jsonl"
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
    "M1 support-conflict detail packet only. It consumes accepted primary M1 rows and "
    "full M1 sidecar context, computes support/conflict detail from historical M1 proxy "
    "ledgers, and preserves exact tick-order limits. It does not change live behavior "
    "and does not claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-SRC-{index:04d}",
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


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def avg(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["branch_queue_id"]: row for row in rows if row.get("branch_queue_id")}


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
    source_materialization_result = read_json(SOURCE_MATERIALIZATION_RESULT)
    source_bar_result = read_json(SOURCE_BAR_RECOMPUTE_RESULT)
    next_accepted_rows = read_jsonl(NEXT_ACCEPTED)
    accepted_m1_rows = [
        row
        for row in next_accepted_rows
        if row.get("primary_export_family") == "M1"
        and row.get("integrated_evidence_action") == "EXECUTE_M1_SUPPORT_ORDERING_BUILDER"
    ]
    accepted_ids = {row["branch_queue_id"] for row in accepted_m1_rows}
    next_by_branch = by_id(accepted_m1_rows)
    m1_result_rows = read_jsonl(ACCEPTED_BUILDER_M1)
    selector_rows = read_jsonl(SELECTOR_M1)
    param_rows = read_jsonl(PARAM_M1)
    collapse_branch_rows = read_jsonl(COLLAPSE_BRANCH)
    signature_rows = read_jsonl(COLLAPSE_SIGNATURE)
    family_rows = read_jsonl(COLLAPSE_FAMILY)
    proxy_rows = read_jsonl(COLLAPSE_PROXY)
    requirement_rows = read_jsonl(COLLAPSE_REQUIREMENT)
    m1_result_by_branch = by_id(m1_result_rows)
    selector_by_branch = by_id(selector_rows)
    param_by_branch = by_id(param_rows)
    collapse_by_branch = by_id(collapse_branch_rows)
    requirement_by_branch = by_id(requirement_rows)
    signatures_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in signature_rows:
        signatures_by_branch[row.get("branch_queue_id")].append(row)
    families_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in family_rows:
        families_by_branch[row.get("branch_queue_id")].append(row)
    proxies_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in proxy_rows:
        proxies_by_branch[row.get("branch_queue_id")].append(row)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            NEXT_RESULT,
            NEXT_ACCEPTED,
            ACCEPTED_BUILDER_M1,
            SELECTOR_M1,
            PARAM_M1,
            COLLAPSE_RESULT,
            COLLAPSE_BRANCH,
            COLLAPSE_SIGNATURE,
            COLLAPSE_FAMILY,
            COLLAPSE_PROXY,
            COLLAPSE_REQUIREMENT,
            SOURCE_MATERIALIZATION_RESULT,
            SOURCE_BAR_RECOMPUTE_RESULT,
        ],
        generated_at,
    )

    scope_rows: list[dict[str, Any]] = []
    sidecar_rows: list[dict[str, Any]] = []
    for row in m1_result_rows:
        branch_id = row.get("branch_queue_id")
        collapse = collapse_by_branch.get(branch_id, {})
        scope_class = "ACCEPTED_PRIMARY_M1_EXECUTION_SCOPE" if branch_id in accepted_ids else "M1_SIDECAR_CONTEXT_SCOPE"
        out = {
            "m1_support_conflict_scope_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-SCOPE-{len(scope_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "scope_class": scope_class,
            "accepted_primary_m1": branch_id in accepted_ids,
            "route_candidate_id": row.get("route_candidate_id"),
            "route_session": row.get("route_session"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "m1_builder_result_status": row.get("m1_builder_result_status"),
            "m1_selector_execution_status": row.get("m1_selector_execution_status"),
            "branch_result_class": collapse.get("branch_result_class"),
            "branch_aggregate_interval_sign_class": collapse.get("branch_aggregate_interval_sign_class"),
            "m1_support_interval_sign_class": collapse.get("m1_support_interval_sign_class"),
            "m1_support_resolution_class": collapse.get("m1_support_resolution_class"),
            "target_stop_result": collapse.get("target_stop_result"),
            "exact_chronology_claim": False,
            "tick_ordering_exact": False,
        }
        with_common(out, generated_at, manifest_hash)
        scope_rows.append(out)
        if branch_id not in accepted_ids:
            sidecar_rows.append(
                with_common(
                    {
                        "m1_support_conflict_sidecar_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-SIDECAR-{len(sidecar_rows) + 1:05d}",
                        **{key: out.get(key) for key in out if key not in {"m1_support_conflict_scope_id"}},
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    branch_detail_rows: list[dict[str, Any]] = []
    for index, accepted in enumerate(sorted(accepted_m1_rows, key=lambda row: row["branch_queue_id"]), 1):
        branch_id = accepted["branch_queue_id"]
        m1_result = m1_result_by_branch.get(branch_id, {})
        selector = selector_by_branch.get(branch_id, {})
        param = param_by_branch.get(branch_id, {})
        collapse = collapse_by_branch.get(branch_id, {})
        requirement = requirement_by_branch.get(branch_id, {})
        sigs = signatures_by_branch.get(branch_id, [])
        fams = families_by_branch.get(branch_id, [])
        prox = proxies_by_branch.get(branch_id, [])
        lower_values = [value for value in (as_float(row.get("support_rstyle_lower")) for row in sigs) if value is not None]
        midpoint_values = [value for value in (as_float(row.get("support_rstyle_midpoint")) for row in sigs) if value is not None]
        upper_values = [value for value in (as_float(row.get("support_rstyle_upper")) for row in sigs) if value is not None]
        conservative_values = [value for value in (as_float(row.get("support_conservative_scalar")) for row in sigs) if value is not None]
        optimistic_values = [value for value in (as_float(row.get("support_optimistic_scalar")) for row in sigs) if value is not None]
        conservative_source_fail_rows = sum(1 for row in sigs if row.get("conservative_source_status") == "MT5_M1_NO_NEXT_BAR_IN_ORIGINAL_REPLAY_WINDOW_FAIL_CLOSED")
        fill_bar_unresolved_rows = sum(1 for row in sigs if row.get("stress_scope_status") == "FILL_BAR_ORDER_UNRESOLVED_STRESSED")
        support_conservative_target_rows = sum(
            1
            for row in sigs
            if row.get("conservative_first_touch_status")
            in {
                "CONSERVATIVE_CARRIED_TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY",
                "CONSERVATIVE_TARGET_TOUCH_FIRST_OR_ONLY_AFTER_FILL_BAR",
            }
        )
        support_conservative_stop_or_no_touch_rows = len(sigs) - support_conservative_target_rows - conservative_source_fail_rows
        support_status = "M1_SUPPORT_STABLE" if m1_result.get("m1_builder_result_status") == "M1_SUPPORT_STABLE_ACCEPTED" else "M1_SUPPORT_BRANCH_CONFLICT"
        if collapse.get("branch_result_class") != "POSITIVE_RSTYLE_PROXY_MIDPOINT":
            support_status = f"{support_status}_BRANCH_AGGREGATE_NOT_CLEAN_POSITIVE"
        out = {
            "m1_support_conflict_branch_detail_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-BRANCH-{index:05d}",
            "branch_queue_id": branch_id,
            "matrix_branch_id": accepted.get("matrix_branch_id") or m1_result.get("matrix_branch_id"),
            "route_candidate_id": accepted.get("route_candidate_id"),
            "route_session": accepted.get("route_session"),
            "symbol": accepted.get("symbol"),
            "side": accepted.get("side"),
            "entry_variant": accepted.get("entry_variant"),
            "target_stop_contract_id": accepted.get("target_stop_contract_id"),
            "target_multiple": collapse.get("target_multiple"),
            "stop_multiple": collapse.get("stop_multiple"),
            "m1_parameter_id": m1_result.get("m1_parameter_id") or param.get("m1_parameter_id"),
            "m1_decision_id": m1_result.get("m1_decision_id") or param.get("m1_decision_id"),
            "m1_selector_execution_id": m1_result.get("m1_selector_execution_id") or selector.get("m1_selector_execution_id"),
            "m1_builder_policy": param.get("m1_builder_policy"),
            "m1_selector_policy": selector.get("m1_selector_policy"),
            "m1_builder_result_status": m1_result.get("m1_builder_result_status"),
            "m1_selector_execution_status": m1_result.get("m1_selector_execution_status") or selector.get("m1_selector_execution_status"),
            "m1_builder_next_action": m1_result.get("m1_builder_next_action"),
            "m1_selector_action": selector.get("m1_selector_action"),
            "branch_decision_class": accepted.get("branch_decision_class"),
            "branch_result_class": collapse.get("branch_result_class"),
            "branch_aggregate_interval_sign_class": collapse.get("branch_aggregate_interval_sign_class"),
            "m1_support_interval_sign_class": collapse.get("m1_support_interval_sign_class"),
            "m1_support_resolution_class": collapse.get("m1_support_resolution_class"),
            "m1_fill_bar_requirement_status": collapse.get("m1_fill_bar_requirement_status") or requirement.get("requirement_status"),
            "m1_fill_bar_next_action": collapse.get("m1_fill_bar_next_action") or requirement.get("next_repair_or_proxy_action"),
            "target_stop_result": collapse.get("target_stop_result"),
            "interval_rstyle_lower_mean": collapse.get("interval_rstyle_lower_mean"),
            "interval_rstyle_midpoint_mean": collapse.get("interval_rstyle_midpoint_mean"),
            "interval_rstyle_upper_mean": collapse.get("interval_rstyle_upper_mean"),
            "support_component_lower_mean": avg(lower_values),
            "support_component_midpoint_mean": avg(midpoint_values),
            "support_component_upper_mean": avg(upper_values),
            "support_component_conservative_scalar_mean": avg(conservative_values),
            "support_component_optimistic_scalar_mean": avg(optimistic_values),
            "m1_replay_rows": collapse.get("m1_replay_rows"),
            "m1_fill_bar_stress_rows": collapse.get("m1_fill_bar_stress_rows"),
            "support_rows_matched": len(sigs),
            "family_support_rows_matched": len(fams),
            "proxy_variant_rows_matched": len(prox),
            "fill_bar_order_unresolved_rows": fill_bar_unresolved_rows,
            "support_conservative_source_fail_rows": conservative_source_fail_rows,
            "support_conservative_target_rows": support_conservative_target_rows,
            "support_conservative_stop_or_no_touch_rows": support_conservative_stop_or_no_touch_rows,
            "support_first_touch_status_counts": compact_counter(Counter(row.get("conservative_first_touch_status") for row in sigs)),
            "support_stress_scope_status_counts": compact_counter(Counter(row.get("stress_scope_status") for row in sigs)),
            "support_cost_model_counts": compact_counter(Counter(row.get("cost_model") for row in sigs)),
            "support_detail_status": support_status,
            "exact_chronology_claim": False,
            "tick_ordering_exact": False,
            "exact_tick_ordering_blocker": "SUB_M1_TICK_ORDER_UNAVAILABLE_USE_M1_SUPPORT_BOUNDS",
            "next_same_resource_action": (
                "PRESERVE_STABLE_M1_SUPPORT_CHALLENGER"
                if m1_result.get("m1_builder_result_status") == "M1_SUPPORT_STABLE_ACCEPTED"
                else "SPLIT_M1_SUPPORT_POSITIVE_FROM_BRANCH_AGGREGATE_CONFLICT"
            ),
        }
        with_common(out, generated_at, manifest_hash)
        branch_detail_rows.append(out)

    stable_rows = [row for row in branch_detail_rows if row.get("m1_builder_result_status") == "M1_SUPPORT_STABLE_ACCEPTED"]
    conflict_rows = [row for row in branch_detail_rows if row.get("m1_builder_result_status") == "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED"]

    signature_detail_rows = []
    for row in [row for row in signature_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m1_support_conflict_signature_detail_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-SIG-{len(signature_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        out["tick_ordering_exact"] = False
        with_common(out, generated_at, manifest_hash)
        signature_detail_rows.append(out)
    family_detail_rows = []
    for row in [row for row in family_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m1_support_conflict_family_detail_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-FAMILY-{len(family_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        out["tick_ordering_exact"] = False
        with_common(out, generated_at, manifest_hash)
        family_detail_rows.append(out)
    proxy_detail_rows = []
    for row in [row for row in proxy_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m1_support_conflict_proxy_detail_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-PROXY-{len(proxy_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        out["tick_ordering_exact"] = False
        with_common(out, generated_at, manifest_hash)
        proxy_detail_rows.append(out)
    requirement_detail_rows = []
    for row in [row for row in requirement_rows if row.get("branch_queue_id") in accepted_ids]:
        out = {"m1_support_conflict_requirement_detail_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-REQ-{len(requirement_detail_rows) + 1:05d}", **row}
        out["claim_boundary"] = CLAIM_BOUNDARY
        out["exact_chronology_claim"] = False
        out["tick_ordering_exact"] = False
        with_common(out, generated_at, manifest_hash)
        requirement_detail_rows.append(out)

    bucket_sources = {
        "scope_class": Counter(row.get("scope_class") for row in scope_rows),
        "accepted_symbol": Counter(row.get("symbol") for row in branch_detail_rows),
        "accepted_route_session": Counter(row.get("route_session") for row in branch_detail_rows),
        "accepted_side": Counter(row.get("side") for row in branch_detail_rows),
        "accepted_entry_variant": Counter(row.get("entry_variant") for row in branch_detail_rows),
        "m1_builder_result_status": Counter(row.get("m1_builder_result_status") for row in branch_detail_rows),
        "branch_result_class": Counter(row.get("branch_result_class") for row in branch_detail_rows),
        "m1_support_interval_sign_class": Counter(row.get("m1_support_interval_sign_class") for row in branch_detail_rows),
        "m1_support_resolution_class": Counter(row.get("m1_support_resolution_class") for row in branch_detail_rows),
        "target_stop_result": Counter(row.get("target_stop_result") for row in branch_detail_rows),
        "support_detail_status": Counter(row.get("support_detail_status") for row in branch_detail_rows),
        "signature_stress_scope_status": Counter(row.get("stress_scope_status") for row in signature_detail_rows),
        "signature_conservative_first_touch_status": Counter(row.get("conservative_first_touch_status") for row in signature_detail_rows),
        "signature_support_scalar_status": Counter(row.get("support_scalar_status") for row in signature_detail_rows),
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
                        "bucket_id": f"OHLC-GTOS-M1-SUPPORT-DETAIL-BUCKET-{len(bucket_rows) + 1:05d}",
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
            "question_id": "OHLC-GTOS-M1-SUPPORT-DETAIL-QUESTION-001",
            "question": "Which accepted M1 rows are stable challenger rows versus support/branch conflict splits?",
            "answer_route": "Use branch detail ledger m1_builder_result_status and support_detail_status.",
        },
        {
            "question_id": "OHLC-GTOS-M1-SUPPORT-DETAIL-QUESTION-002",
            "question": "How many accepted M1 support rows still have sub-M1 ordering unresolved?",
            "answer_route": "Use signature support detail stress_scope_status=FILL_BAR_ORDER_UNRESOLVED_STRESSED.",
        },
        {
            "question_id": "OHLC-GTOS-M1-SUPPORT-DETAIL-QUESTION-003",
            "question": "Which rows rely on source-fail conservative support proxy?",
            "answer_route": "Use branch detail support_conservative_source_fail_rows and requirement detail status.",
        },
        {
            "question_id": "OHLC-GTOS-M1-SUPPORT-DETAIL-QUESTION-004",
            "question": "What is the next executable queue after M1 detail?",
            "answer_route": "Continue M15 bounded ordering, positive replay/repair, and entry/adverse redesign detail builders.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_SUPPORT_CONFLICT_DETAIL",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_next_accepted_rows": len(next_accepted_rows),
            "input_next_accepted_m1_rows": len(accepted_m1_rows),
            "input_m1_result_rows": len(m1_result_rows),
            "input_selector_m1_rows": len(selector_rows),
            "input_parameter_m1_rows": len(param_rows),
            "input_collapse_branch_rows": len(collapse_branch_rows),
            "input_collapse_signature_rows": len(signature_rows),
            "input_collapse_family_rows": len(family_rows),
            "input_collapse_proxy_rows": len(proxy_rows),
            "input_collapse_requirement_rows": len(requirement_rows),
            "scope_rows": len(scope_rows),
            "branch_detail_rows": len(branch_detail_rows),
            "stable_challenger_rows": len(stable_rows),
            "conflict_split_rows": len(conflict_rows),
            "signature_support_detail_rows": len(signature_detail_rows),
            "family_support_detail_rows": len(family_detail_rows),
            "proxy_variant_rows": len(proxy_detail_rows),
            "requirement_rows": len(requirement_detail_rows),
            "sidecar_context_rows": len(sidecar_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_next_counts": next_result.get("counts", {}),
        "upstream_collapse_counts": collapse_result.get("counts", {}),
        "upstream_source_materialization_counts": source_materialization_result.get("counts", {}),
        "upstream_source_bar_recompute_counts": source_bar_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "system_decision": {
            "system_recommendation": (
                "M1_SUPPORT_CONFLICT_DETAIL_RESULT: preserve stable M1 support challengers, "
                "split support-positive branch-aggregate conflicts, keep exact tick-order flags "
                "false, and continue M15/positive/entry-adverse detail builders."
            ),
            "accepted_primary_m1_rows": len(branch_detail_rows),
            "stable_challenger_rows": len(stable_rows),
            "conflict_split_rows": len(conflict_rows),
            "sidecar_context_rows": len(sidecar_rows),
            "fill_bar_order_unresolved_signature_rows": int(bucket_sources["signature_stress_scope_status"]["FILL_BAR_ORDER_UNRESOLVED_STRESSED"]),
            "source_fail_conservative_signature_rows": int(
                Counter(row.get("conservative_source_status") for row in signature_detail_rows)[
                    "MT5_M1_NO_NEXT_BAR_IN_ORIGINAL_REPLAY_WINDOW_FAIL_CLOSED"
                ]
            ),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (SCOPE_LEDGER, scope_rows),
        (BRANCH_LEDGER, branch_detail_rows),
        (STABLE_LEDGER, stable_rows),
        (CONFLICT_LEDGER, conflict_rows),
        (SIGNATURE_LEDGER, signature_detail_rows),
        (FAMILY_LEDGER, family_detail_rows),
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
                "# Historical OHLC GTOS Replay Branch M1 Support Conflict Detail",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Scope rows: `{len(scope_rows)}`",
                f"- Accepted primary M1 rows: `{len(branch_detail_rows)}`",
                f"- Stable challenger rows: `{len(stable_rows)}`",
                f"- Conflict split rows: `{len(conflict_rows)}`",
                f"- Accepted signature support rows: `{len(signature_detail_rows)}`",
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
                "type": "branch_m1_support_conflict_detail",
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
                    "event_type": "branch_m1_support_conflict_detail_built",
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
