#!/usr/bin/env python3
"""Build full-denominator branch source-repair feasibility from the action matrix."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

MATRIX_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_BRANCH_LEDGER_2026-05-16.jsonl"
MATRIX_SOURCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_SOURCE_REPAIR_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
SIERRA_SOURCE_MANIFEST_PATH = ROUTE_DIR / "SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_2026-05-16.json"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_RESULT_2026-05-16.json"
BRANCH_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_BRANCH_LEDGER_2026-05-16.jsonl"
ACTION_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_ACTION_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_EXACT_SPREAD_ROUTE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS branch source-repair feasibility packet only. Rows preserve "
    "all 386 branches and classify current exact-spread/source feasibility, proxy "
    "fallbacks, and same-resource next actions. Exact broker R/PnL, strategy "
    "expectancy, win-rate, validation, live-readiness, promotion, and live behavior "
    "change are not claimed."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
                yield {"_parse_error": True, "_line_no": line_no, "_source_path": str(path)}


def rows(path: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path) or [])


def write_jsonl(path: Path, output_rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        MATRIX_BRANCH_PATH,
        MATRIX_SOURCE_PATH,
        EXACT_SPREAD_DELTA_PATH,
        EXACT_SPREAD_UNAVAILABLE_PATH,
        SIERRA_SOURCE_MANIFEST_PATH,
    ]
    manifest_rows = []
    for path in paths:
        manifest_rows.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
            }
        )
    digest = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, digest


def compact_counter(counter: Counter[str]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter)}


def branch_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("route_candidate_id")),
        str(row.get("entry_variant")),
        str(row.get("target_stop_contract_id")),
    )


def classify_feasibility(row: dict[str, Any], delta_count: int, unavailable_count: int) -> tuple[str, str, list[str]]:
    source_class = row.get("source_repairability_class")
    spread_class = row.get("exact_spread_repairability_class")
    if source_class == "ENTRY_PROVENANCE_ONLY_BOUND":
        return (
            "PROVENANCE_ONLY_NO_SINGLE_SOURCE_REPAIR",
            "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY",
            ["Preserve original branch; route source/path questions through bound signature-scope contract rows."],
        )
    if source_class == "EXACT_SOURCE_CLEAN" and spread_class == "EXACT_SPREAD_RECOMPUTED":
        return (
            "CURRENT_EXACT_SOURCE_AND_SPREAD_RECOMPUTED",
            "NO_SOURCE_REPAIR_REQUIRED_FOR_CURRENT_PROXY",
            ["Use exact-spread descriptor rows already materialized; continue with controls and challenger comparison."],
        )
    if source_class == "EXACT_SOURCE_CLEAN":
        return (
            "CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED",
            "NO_SOURCE_REPAIR_REQUIRED_BUT_KEEP_COST_BUCKET",
            ["Preserve exact-source-clean status and keep cost/descriptor bucket separate."],
        )
    if spread_class == "EXACT_SPREAD_RECOMPUTED" or delta_count:
        return (
            "EXACT_SPREAD_RECOMPUTED_FROM_CURRENT_SOURCE",
            "CURRENT_SOURCE_REPAIR_COMPLETED_FOR_SPREAD_DESCRIPTOR",
            ["Use exact first-touch descriptor and keep low/high proxy delta diagnostics for sensitivity."],
        )
    if spread_class == "EXACT_SPREAD_UNAVAILABLE_STRESS_PAIR" or unavailable_count:
        return (
            "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY",
            "CURRENT_SOURCE_REPAIR_BLOCKED_USE_LOW_HIGH_STRESS_PROXY",
            ["Preserve MT5 no-tick/source-unavailable proof and use low/high spread stress interval."],
        )
    if spread_class == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT":
        return (
            "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_REPLAY_AVAILABLE",
            "SOURCE_ALIGNMENT_AND_M1_SPREAD_REPLAY_PROXY",
            ["Use source-alignment and M1 spread-adjusted replay rows; do not mix zero-cost and spread-adjusted descriptors."],
        )
    if spread_class == "SPREAD_PROXY_GRADIENT_SENSITIVE":
        return (
            "SPREAD_PROXY_GRADIENT_SENSITIVE_NEEDS_EXACT_OR_STRESS",
            "EXACT_SPREAD_OR_PROXY_STRESS_REQUIRED",
            ["Route to exact spread if available; otherwise preserve gradient sensitivity stress interval."],
        )
    if spread_class == "COST_INVARIANT_OR_ABSENT":
        return (
            "COST_INVARIANT_OR_ABSENT_NO_SPREAD_REPAIR",
            "NO_COST_SOURCE_REPAIR_ROUTE",
            ["No current cost descriptor repair route; preserve branch as non-cost-limited or provenance-only."],
        )
    return (
        "SOURCE_REPAIR_CLASS_REVIEW_REQUIRED",
        "FAIL_CLOSED_REVIEW",
        ["Review new source/spread class without inferring a scalar result."],
    )


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifact_paths = [
        RESULT_PATH,
        BRANCH_LEDGER_PATH,
        ACTION_LEDGER_PATH,
        EXACT_SPREAD_ROUTE_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    artifact_names = {path.name for path in artifact_paths}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in [
        (RESULT_PATH, "result"),
        (BRANCH_LEDGER_PATH, "branch_source_repair_feasibility_ledger"),
        (ACTION_LEDGER_PATH, "action_ledger"),
        (EXACT_SPREAD_ROUTE_PATH, "exact_spread_route_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_source_repair_feasibility",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path in artifact_paths}
    manifest["artifacts"] = [row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths]
    for path, artifact_type in [
        (Path(__file__).resolve(), "branch_source_repair_feasibility_builder"),
        (RESULT_PATH, "branch_source_repair_feasibility_result"),
        (BRANCH_LEDGER_PATH, "branch_source_repair_feasibility_branch_ledger"),
        (ACTION_LEDGER_PATH, "branch_source_repair_feasibility_action_ledger"),
        (EXACT_SPREAD_ROUTE_PATH, "branch_source_repair_feasibility_exact_spread_route_ledger"),
        (BUCKET_PATH, "branch_source_repair_feasibility_bucket_ledger"),
        (QUESTION_PATH, "branch_source_repair_feasibility_question_ledger"),
        (SUMMARY_PATH, "branch_source_repair_feasibility_summary"),
    ]:
        manifest["artifacts"].append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "status": "created",
                "type": artifact_type,
            }
        )
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_branch_source_repair_feasibility",
        "artifact": RESULT_PATH.name,
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Branch Source-Repair Feasibility",
        "",
        f"Generated UTC: {result['generated_utc']}",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Feasibility Distribution", ""])
    for bucket, count in result["bucket_distributions"]["repair_feasibility_class"].items():
        lines.append(f"- {bucket}: {count}")
    lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    matrix_rows = rows(MATRIX_BRANCH_PATH)
    matrix_source_by_branch = {row.get("branch_queue_id"): row for row in rows(MATRIX_SOURCE_PATH)}
    exact_delta_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows(EXACT_SPREAD_DELTA_PATH):
        exact_delta_by_key[branch_key(row)].append(row)
    exact_unavailable_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows(EXACT_SPREAD_UNAVAILABLE_PATH):
        exact_unavailable_by_key[branch_key(row)].append(row)
    sierra_manifest = read_json(SIERRA_SOURCE_MANIFEST_PATH)
    sierra_counts = sierra_manifest.get("counts", {})
    sierra_class_counts = sierra_manifest.get("local_acquisition_classification_counts", {})

    branch_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    exact_route_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)

    for index, row in enumerate(matrix_rows, 1):
        key = branch_key(row)
        delta_rows = exact_delta_by_key.get(key, [])
        unavailable_rows = exact_unavailable_by_key.get(key, [])
        feasibility, route_class, steps = classify_feasibility(row, len(delta_rows), len(unavailable_rows))
        source_row = matrix_source_by_branch.get(row.get("branch_queue_id"), {})

        bucket_counters["repair_feasibility_class"][feasibility] += 1
        bucket_counters["source_repair_route_class"][route_class] += 1
        bucket_counters["source_repairability_class"][row.get("source_repairability_class")] += 1
        bucket_counters["exact_spread_repairability_class"][row.get("exact_spread_repairability_class")] += 1
        bucket_counters["source_confidence_status"][row.get("source_confidence_status")] += 1
        bucket_counters["cost_robustness_bucket"][row.get("cost_robustness_bucket")] += 1

        branch_out = {
            "source_repair_feasibility_id": f"OHLC-GTOS-BRANCH-SOURCE-REPAIR-FEAS-{index:05d}",
            "branch_queue_id": row.get("branch_queue_id"),
            "branch_proxy_score_id": row.get("branch_proxy_score_id"),
            "route_candidate_id": row.get("route_candidate_id"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "source_confidence_status": row.get("source_confidence_status"),
            "source_repairability_class": row.get("source_repairability_class"),
            "source_repair_class": row.get("source_repair_class"),
            "source_repair_mechanical_next_step": source_row.get("source_repair_mechanical_next_step"),
            "cost_robustness_bucket": row.get("cost_robustness_bucket"),
            "exact_spread_repairability_class": row.get("exact_spread_repairability_class"),
            "exact_spread_delta_rows_for_branch_key": len(delta_rows),
            "exact_spread_unavailable_stress_rows_for_branch_key": len(unavailable_rows),
            "repair_feasibility_class": feasibility,
            "source_repair_route_class": route_class,
            "next_same_resource_actions": steps,
            "sierra_depth_manifest_context": {
                "classification_rows": sierra_counts.get("classification_rows"),
                "unique_source_date_requirements": sierra_counts.get("unique_source_date_requirements"),
                "local_acquisition_classification_counts": sierra_class_counts,
                "branch_keyed_direct_join_status": "NO_DIRECT_BRANCH_KEYED_SIERRA_DEPTH_JOIN_ATTEMPTED_IN_THIS_PACKET",
            },
            "exact_missing_geometry_reason": row.get("exact_missing_geometry_reason"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY",
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_rows.append(branch_out)

        for action_index, step in enumerate(steps, 1):
            action_rows.append(
                {
                    "source_repair_action_id": f"OHLC-GTOS-BRANCH-SOURCE-REPAIR-ACTION-{index:05d}-{action_index:03d}",
                    "branch_queue_id": row.get("branch_queue_id"),
                    "route_candidate_id": row.get("route_candidate_id"),
                    "repair_feasibility_class": feasibility,
                    "source_repair_route_class": route_class,
                    "mechanical_next_step": step,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

        exact_route_rows.append(
            {
                "exact_spread_route_id": f"OHLC-GTOS-BRANCH-SOURCE-REPAIR-EXACT-SPREAD-{index:05d}",
                "branch_queue_id": row.get("branch_queue_id"),
                "route_candidate_id": row.get("route_candidate_id"),
                "entry_variant": row.get("entry_variant"),
                "target_stop_contract_id": row.get("target_stop_contract_id"),
                "exact_spread_repairability_class": row.get("exact_spread_repairability_class"),
                "exact_spread_delta_rows_for_branch_key": len(delta_rows),
                "exact_spread_unavailable_stress_rows_for_branch_key": len(unavailable_rows),
                "exact_descriptor_delta_status_counts": compact_counter(Counter(d.get("descriptor_delta_status") for d in delta_rows)),
                "exact_unavailable_source_status_counts": compact_counter(Counter(d.get("exact_spread_source_status") for d in unavailable_rows)),
                "repair_feasibility_class": feasibility,
                "source_repair_route_class": route_class,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )

    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items()):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-BRANCH-SOURCE-REPAIR-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": bucket,
                    "branch_count": count,
                    "branch_share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-BRANCH-SOURCE-REPAIR-QUESTION-001",
            "question": "Which exact-spread unavailable branches can be repaired from another owned/current historical source versus only stress-bounded?",
            "answer_route": "Join branch source-repair rows to MT5 tick/M1 availability and local Sierra/source manifests by source date where branch timestamps are available.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-SOURCE-REPAIR-QUESTION-002",
            "question": "Which zero-to-spread descriptor shifts remain attractive after M1 spread-adjusted replay and control deltas?",
            "answer_route": "Build the full-denominator source-alignment challenger comparison from zero-to-spread branches.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-SOURCE-REPAIR-QUESTION-003",
            "question": "Do exact-spread recomputed rows weaken, repair, or confirm branch action priority?",
            "answer_route": "Split exact descriptor-delta statuses against branch result class, target/stop result, and pass-control delta.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-SOURCE-REPAIR-QUESTION-004",
            "question": "Which provenance-only target/stop NA rows need signature-scope source analysis before any implementation route?",
            "answer_route": "Use the target/stop NA binding repair packet and do not explode the base branch rows.",
        },
    ]
    for question in question_rows:
        question.update(
            {
                "generated_utc": generated_at,
                "not_completion": True,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "bucket_snapshot": {
                    "repair_feasibility_class": compact_counter(bucket_counters["repair_feasibility_class"]),
                    "source_repair_route_class": compact_counter(bucket_counters["source_repair_route_class"]),
                },
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "counts": {
            "matrix_branch_input_rows": len(matrix_rows),
            "matrix_source_input_rows": len(matrix_source_by_branch),
            "exact_spread_delta_input_rows": sum(len(v) for v in exact_delta_by_key.values()),
            "exact_spread_unavailable_input_rows": sum(len(v) for v in exact_unavailable_by_key.values()),
            "branch_feasibility_rows": len(branch_rows),
            "action_rows": len(action_rows),
            "exact_spread_route_rows": len(exact_route_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(manifest_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "sierra_depth_manifest_context": {
            "counts": sierra_counts,
            "local_acquisition_classification_counts": sierra_class_counts,
        },
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
    }

    write_jsonl(BRANCH_LEDGER_PATH, branch_rows)
    write_jsonl(ACTION_LEDGER_PATH, action_rows)
    write_jsonl(EXACT_SPREAD_ROUTE_PATH, exact_route_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)

    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
