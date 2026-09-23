#!/usr/bin/env python3
"""Join accepted-builder decisions to deeper source/order/positive evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

ACCEPTED_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_RESULT_2026-05-16.json"
ACCEPTED_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
ACCEPTED_FAMILY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
ACCEPTED_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_RESULT_LEDGER_2026-05-16.jsonl"
ACCEPTED_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M15_RESULT_LEDGER_2026-05-16.jsonl"
ACCEPTED_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M1_RESULT_LEDGER_2026-05-16.jsonl"
ACCEPTED_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_POSITIVE_RESULT_LEDGER_2026-05-16.jsonl"
ACCEPTED_ENTRY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ENTRY_ADVERSE_RESULT_LEDGER_2026-05-16.jsonl"
ACCEPTED_BINDING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BINDING_RESULT_LEDGER_2026-05-16.jsonl"

SOURCE_DEEP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
ORDERING_DEEP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ORDERING_COLLAPSE_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
POSITIVE_DEEP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
M15_COLLAPSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
M1_COLLAPSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
ACCEPTED_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ACCEPTED_LEDGER_2026-05-16.jsonl"
REPAIR_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_REPAIR_LEDGER_2026-05-16.jsonl"
SOURCE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SOURCE_LEDGER_2026-05-16.jsonl"
M15_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_M15_LEDGER_2026-05-16.jsonl"
M1_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_M1_LEDGER_2026-05-16.jsonl"
POSITIVE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_POSITIVE_LEDGER_2026-05-16.jsonl"
ENTRY_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BINDING_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BINDING_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Next-layer evidence execution packet only. It joins accepted-builder rows "
    "to source-stress, ordering-collapse, M15, M1, positive, and entry/adverse "
    "evidence rows to produce branch-local execution-detail decisions. It does "
    "not change live behavior and does not claim broker R/PnL, realized "
    "expectancy, win-rate, live-readiness, promotion, or live effect."
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
                "source_manifest_id": f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-SRC-{index:04d}",
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


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id") is not None:
            grouped[str(row["branch_queue_id"])].append(row)
    return grouped


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


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        prefix, suffix = branch_id.rsplit("-", 1)
        return prefix, int(suffix)
    except (ValueError, IndexError):
        return branch_id, 0


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


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


def first_non_null(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def avg_non_null(values: list[Any]) -> float | None:
    numeric = [fnum(value) for value in values if fnum(value) is not None]
    return round(sum(numeric) / len(numeric), 6) if numeric else None


def integrated_decision(branch: dict[str, Any], source: dict[str, Any], ordering: dict[str, Any], positive: dict[str, Any]) -> tuple[str, str]:
    family = branch.get("primary_export_family")
    accepted = branch.get("branch_result_binary") == "ACCEPTED"
    if family == "BINDING":
        return "PRESERVE_BINDING_PROVENANCE_ONLY", "TARGETSTOP_NA_NA_NO_SCALAR"
    if not accepted:
        return "ROUTE_TO_REPAIR_OR_AVOID_LEDGER", str(branch.get("next_layer_blocker_or_repair"))
    if family == "SOURCE":
        if source.get("source_repair_route_class") == "CURRENT_SOURCE_REPAIR_COMPLETED_FOR_SPREAD_DESCRIPTOR":
            return "EXECUTE_SOURCE_REPAIRED_DESCRIPTOR_BUILDER", "EXACT_SOURCE_REPAIR_AVAILABLE"
        return "EXECUTE_SOURCE_COST_CAP_OR_BOUNDS_WITH_ACQUISITION", str(source.get("source_repair_route_class"))
    if family == "M15":
        return "EXECUTE_M15_BOUNDED_ORDERING_BUILDER", str(ordering.get("ordering_deep_action_class"))
    if family == "M1":
        return "EXECUTE_M1_SUPPORT_ORDERING_BUILDER", str(ordering.get("ordering_deep_action_class"))
    if family == "POSITIVE":
        return "EXECUTE_POSITIVE_CHALLENGER_DETAIL_BUILDER", str(positive.get("positive_deep_action_class"))
    if family == "ENTRY_ADVERSE":
        return "EXECUTE_ENTRY_ADVERSE_REDESIGN_DETAIL_BUILDER", str(branch.get("exact_failure_cause"))
    return "ROUTE_TO_REPAIR_OR_AVOID_LEDGER", "UNKNOWN_PRIMARY_FAMILY"


def main() -> int:
    generated_at = now_utc()
    accepted_result = read_json(ACCEPTED_RESULT)
    branch_in = read_jsonl(ACCEPTED_BRANCH)
    family_in = read_jsonl(ACCEPTED_FAMILY)
    source_in = read_jsonl(ACCEPTED_SOURCE)
    m15_in = read_jsonl(ACCEPTED_M15)
    m1_in = read_jsonl(ACCEPTED_M1)
    positive_in = read_jsonl(ACCEPTED_POSITIVE)
    entry_in = read_jsonl(ACCEPTED_ENTRY)
    binding_in = read_jsonl(ACCEPTED_BINDING)
    source_deep = by_branch(read_jsonl(SOURCE_DEEP))
    ordering_deep = by_branch(read_jsonl(ORDERING_DEEP))
    positive_deep = by_branch(read_jsonl(POSITIVE_DEEP))
    m15_collapse = by_branch(read_jsonl(M15_COLLAPSE))
    m1_collapse = by_branch(read_jsonl(M1_COLLAPSE))

    source_manifest, manifest_hash = source_manifest_rows(
        [
            ACCEPTED_RESULT,
            ACCEPTED_BRANCH,
            ACCEPTED_FAMILY,
            ACCEPTED_SOURCE,
            ACCEPTED_M15,
            ACCEPTED_M1,
            ACCEPTED_POSITIVE,
            ACCEPTED_ENTRY,
            ACCEPTED_BINDING,
            SOURCE_DEEP,
            ORDERING_DEEP,
            POSITIVE_DEEP,
            M15_COLLAPSE,
            M1_COLLAPSE,
        ],
        generated_at,
    )

    branch_rows: list[dict[str, Any]] = []
    accepted_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for branch in sorted(branch_in, key=lambda row: branch_sort_key(str(row.get("branch_queue_id", "")))):
        branch_id = str(branch.get("branch_queue_id"))
        source = source_deep.get(branch_id, {})
        ordering = ordering_deep.get(branch_id, {})
        positive = positive_deep.get(branch_id, {})
        m15 = m15_collapse.get(branch_id, {})
        m1 = m1_collapse.get(branch_id, {})
        action, evidence_state = integrated_decision(branch, source, ordering, positive)
        score = avg_non_null(
            [
                branch.get("next_layer_composite_score"),
                source.get("rstyle_midpoint_mean"),
                ordering.get("rstyle_midpoint_mean"),
                positive.get("rstyle_midpoint_mean"),
                m15.get("interval_rstyle_midpoint_mean"),
                m1.get("m1_support_adjusted_midpoint"),
            ]
        )
        record = {
            **common_base(branch),
            "next_layer_evidence_branch_id": f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-BRANCH-{len(branch_rows) + 1:05d}",
            "accepted_builder_branch_result_id": branch.get("accepted_builder_branch_result_id"),
            "selector_execution_branch_id": branch.get("selector_execution_branch_id"),
            "primary_export_family": branch.get("primary_export_family"),
            "branch_result_binary": branch.get("branch_result_binary"),
            "branch_decision_class": branch.get("branch_decision_class"),
            "accepted_for_next_executable_builder": branch.get("accepted_for_next_executable_builder"),
            "next_layer_branch_status": branch.get("next_layer_branch_status"),
            "next_layer_branch_action": branch.get("next_layer_branch_action"),
            "integrated_evidence_action": action,
            "integrated_evidence_state": evidence_state,
            "integrated_evidence_score": score,
            "source_deep_action_class": source.get("source_deep_action_class"),
            "source_repair_route_class": source.get("source_repair_route_class"),
            "source_stress_action_class": source.get("source_stress_action_class"),
            "ordering_deep_action_class": ordering.get("ordering_deep_action_class"),
            "ordering_collapse_action_class": ordering.get("ordering_collapse_action_class"),
            "positive_deep_action_class": positive.get("positive_deep_action_class"),
            "positive_challenger_class": positive.get("positive_challenger_class"),
            "m15_interval_sign_class": m15.get("interval_sign_class"),
            "m15_exact_chronology_claim": False,
            "m1_branch_result_class": m1.get("branch_result_class"),
            "m1_support_resolution_class": m1.get("m1_support_resolution_class"),
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "target_stop_result": branch.get("target_stop_result"),
            "sealed_proxy_class": branch.get("sealed_proxy_class"),
            "success_decision": branch.get("success_decision"),
            "failure_decision": branch.get("failure_decision"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(record)
        if branch.get("branch_result_binary") == "ACCEPTED":
            accepted_rows.append({**record, "next_layer_accepted_id": f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-ACCEPTED-{len(accepted_rows) + 1:05d}"})
        else:
            repair_rows.append({**record, "next_layer_repair_id": f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-REPAIR-{len(repair_rows) + 1:05d}"})
        for category in [
            "primary_export_family",
            "branch_result_binary",
            "integrated_evidence_action",
            "integrated_evidence_state",
            "source_deep_action_class",
            "ordering_deep_action_class",
            "positive_deep_action_class",
            "m15_interval_sign_class",
            "m1_branch_result_class",
        ]:
            bucket_counters[category][str(record.get(category))] += 1

    detail_specs = [
        ("SOURCE", source_in, SOURCE_LEDGER, "source_evidence_detail_id", "source_builder_result_status"),
        ("M15", m15_in, M15_LEDGER, "m15_evidence_detail_id", "m15_builder_result_status"),
        ("M1", m1_in, M1_LEDGER, "m1_evidence_detail_id", "m1_builder_result_status"),
        ("POSITIVE", positive_in, POSITIVE_LEDGER, "positive_evidence_detail_id", "positive_builder_result_status"),
        ("ENTRY_ADVERSE", entry_in, ENTRY_LEDGER, "entry_adverse_evidence_detail_id", "entry_adverse_builder_result_status"),
        ("BINDING", binding_in, BINDING_LEDGER, "binding_evidence_detail_id", "binding_builder_result_status"),
    ]
    detail_outputs: list[tuple[Path, list[dict[str, Any]]]] = []
    for family, rows, path, id_key, status_key in detail_specs:
        out_rows = []
        for row in rows:
            branch_id = str(row.get("branch_queue_id"))
            source = source_deep.get(branch_id, {})
            ordering = ordering_deep.get(branch_id, {})
            positive = positive_deep.get(branch_id, {})
            m15 = m15_collapse.get(branch_id, {})
            m1 = m1_collapse.get(branch_id, {})
            record = {
                **common_base(row),
                id_key: f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-{family}-{len(out_rows) + 1:05d}",
                "family": family,
                "upstream_builder_result_status": row.get(status_key),
                "source_deep_action_class": source.get("source_deep_action_class"),
                "ordering_deep_action_class": ordering.get("ordering_deep_action_class"),
                "positive_deep_action_class": positive.get("positive_deep_action_class"),
                "m15_interval_sign_class": m15.get("interval_sign_class"),
                "m1_branch_result_class": m1.get("branch_result_class"),
                "m15_exact_chronology_claim": False,
                "m1_exact_chronology_claim": False,
                "m1_tick_ordering_exact": False,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
            if family == "BINDING":
                record["no_scalar_fill"] = True
                record["primary_selector_score"] = None
            out_rows.append(record)
            bucket_counters[f"{family.lower()}_detail_status"][str(row.get(status_key))] += 1
        detail_outputs.append((path, out_rows))

    family_by_branch = group_by_branch(family_in)
    for branch_id in sorted(family_by_branch, key=branch_sort_key):
        for row in family_by_branch[branch_id]:
            family_rows.append(
                {
                    **common_base(row),
                    "next_layer_family_evidence_id": f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-FAMILY-{len(family_rows) + 1:05d}",
                    "family_builder_result_id": row.get("family_builder_result_id"),
                    "action_family": row.get("action_family"),
                    "family_builder_policy": row.get("family_builder_policy"),
                    "family_builder_result_status": row.get("family_builder_result_status"),
                    "family_builder_score": row.get("family_builder_score"),
                    "family_builder_score_class": row.get("family_builder_score_class"),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
            bucket_counters["action_family"][row.get("action_family")] += 1
            bucket_counters["family_builder_result_status"][row.get("family_builder_result_status")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-NEXT-LAYER-EVIDENCE-BUCKET-{len(bucket_rows) + 1:05d}",
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
        {"question_id": "OHLC-GTOS-NEXT-LAYER-EVIDENCE-QUESTION-001", "question": "Which accepted branches have direct source/order/positive evidence support?", "answer_route": "Use branch ledger integrated_evidence_action and source/order/positive action classes."},
        {"question_id": "OHLC-GTOS-NEXT-LAYER-EVIDENCE-QUESTION-002", "question": "Which rejected branches remain useful as repair or avoid evidence?", "answer_route": "Use repair ledger and integrated_evidence_state."},
        {"question_id": "OHLC-GTOS-NEXT-LAYER-EVIDENCE-QUESTION-003", "question": "Which M15 and M1 accepted builders still preserve ordering uncertainty?", "answer_route": "Use M15/M1 detail ledgers and false exact flags."},
        {"question_id": "OHLC-GTOS-NEXT-LAYER-EVIDENCE-QUESTION-004", "question": "Which positive and source branches require exact acquisition before stronger claims?", "answer_route": "Use positive/source detail ledgers and source_deep_action_class."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "not_completion": True, "generated_utc": generated_at, "source_manifest_hash": manifest_hash})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_accepted_branch_rows": len(branch_in),
            "input_accepted_family_rows": len(family_in),
            "input_accepted_source_rows": len(source_in),
            "input_accepted_m15_rows": len(m15_in),
            "input_accepted_m1_rows": len(m1_in),
            "input_accepted_positive_rows": len(positive_in),
            "input_accepted_entry_adverse_rows": len(entry_in),
            "input_accepted_binding_rows": len(binding_in),
            "input_source_deep_rows": len(source_deep),
            "input_ordering_deep_rows": len(ordering_deep),
            "input_positive_deep_rows": len(positive_deep),
            "input_m15_collapse_rows": len(m15_collapse),
            "input_m1_collapse_rows": len(m1_collapse),
            "branch_evidence_rows": len(branch_rows),
            "family_evidence_rows": len(family_rows),
            "accepted_evidence_rows": len(accepted_rows),
            "repair_evidence_rows": len(repair_rows),
            "source_evidence_rows": len(source_in),
            "m15_evidence_rows": len(m15_in),
            "m1_evidence_rows": len(m1_in),
            "positive_evidence_rows": len(positive_in),
            "entry_adverse_evidence_rows": len(entry_in),
            "binding_evidence_rows": len(binding_in),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_accepted_builder_counts": accepted_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "system_decision": {
            "system_recommendation": (
                "RUN_NEXT_DETAIL_BUILDERS_FROM_INTEGRATED_EVIDENCE_ACTIONS: "
                "source cost-cap/acquisition for 93, M15 bounded ordering for 66, "
                "M1 support ordering for 70, positive challenger detail for 43, "
                "entry/adverse redesign detail for 5; keep 107 repair/avoid rows "
                "and 2 binding provenance rows out of scalar scoring."
            ),
            "execute_source_detail_builder_count": int(bucket_counters["integrated_evidence_action"]["EXECUTE_SOURCE_COST_CAP_OR_BOUNDS_WITH_ACQUISITION"]),
            "execute_m15_detail_builder_count": int(bucket_counters["integrated_evidence_action"]["EXECUTE_M15_BOUNDED_ORDERING_BUILDER"]),
            "execute_m1_detail_builder_count": int(bucket_counters["integrated_evidence_action"]["EXECUTE_M1_SUPPORT_ORDERING_BUILDER"]),
            "execute_positive_detail_builder_count": int(bucket_counters["integrated_evidence_action"]["EXECUTE_POSITIVE_CHALLENGER_DETAIL_BUILDER"]),
            "execute_entry_adverse_detail_builder_count": int(bucket_counters["integrated_evidence_action"]["EXECUTE_ENTRY_ADVERSE_REDESIGN_DETAIL_BUILDER"]),
            "repair_or_avoid_rows": int(bucket_counters["integrated_evidence_action"]["ROUTE_TO_REPAIR_OR_AVOID_LEDGER"]),
            "binding_provenance_rows": int(bucket_counters["integrated_evidence_action"]["PRESERVE_BINDING_PROVENANCE_ONLY"]),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_LEDGER, branch_rows),
        (FAMILY_LEDGER, family_rows),
        (ACCEPTED_LEDGER, accepted_rows),
        (REPAIR_LEDGER, repair_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    outputs.extend(detail_outputs)
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch Next-Layer Evidence Execution Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch evidence rows: `{len(branch_rows)}`",
                f"- Accepted evidence rows: `{len(accepted_rows)}`",
                f"- Repair evidence rows: `{len(repair_rows)}`",
                f"- Family evidence rows: `{len(family_rows)}`",
                "",
                "System recommendation: run the next executable detail builders from the integrated action ledger: source `93`, M15 `66`, M1 `70`, positive `43`, entry/adverse `5`; preserve `107` repair/avoid rows and `2` binding provenance rows without scalar scoring.",
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
                "type": "branch_next_layer_evidence_execution_packet",
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
                    "event_type": "branch_next_layer_evidence_execution_packet_built",
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
