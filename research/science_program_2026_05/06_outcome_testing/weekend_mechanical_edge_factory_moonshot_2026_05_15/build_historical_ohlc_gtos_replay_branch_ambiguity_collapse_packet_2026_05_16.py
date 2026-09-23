#!/usr/bin/env python3
"""Build full-denominator branch ambiguity-collapse packet from current replay sources."""

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
MATRIX_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_AMBIGUITY_COLLAPSE_LEDGER_2026-05-16.jsonl"
MATRIX_SOURCE_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_SOURCE_REPAIR_LEDGER_2026-05-16.jsonl"
SOURCE_REPAIR_FEAS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_BRANCH_LEDGER_2026-05-16.jsonl"
RSTYLE_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
M1_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
RECOVERED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_CANDIDATE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_CANDIDATE_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_TARGETSTOP_NA_BINDING_REPAIR_CONTRACT_SUMMARY_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_BRANCH_CLASSIFICATION_LEDGER_2026-05-16.jsonl"
M15_SAME_BAR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_M15_SAME_BAR_CLASSIFICATION_LEDGER_2026-05-16.jsonl"
M1_STRESS_JOIN_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_M1_STRESS_JOIN_LEDGER_2026-05-16.jsonl"
ORDERING_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ORDERING_ROUTE_LEDGER_2026-05-16.jsonl"
INTERVAL_PRESERVATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_INTERVAL_PRESERVATION_LEDGER_2026-05-16.jsonl"
TARGETSTOP_NA_BINDING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_TARGETSTOP_NA_BINDING_LEDGER_2026-05-16.jsonl"
ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS branch ambiguity-collapse packet only. Rows preserve all "
    "386 branches and classify same-M15 target/stop ambiguity, existing M1 replay "
    "or fill-bar stress evidence, interval preservation, target/stop NA binding, "
    "source confidence, duplicate/effective-N, concentration, and same-resource "
    "next actions. Exact broker R/PnL, strategy expectancy, win-rate, validation, "
    "live-readiness, promotion, and live behavior change are not claimed."
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
        MATRIX_AMBIGUITY_PATH,
        MATRIX_SOURCE_REPAIR_PATH,
        SOURCE_REPAIR_FEAS_PATH,
        RSTYLE_BRANCH_PATH,
        PATH_AMBIGUITY_PATH,
        M1_REPLAY_PATH,
        M1_FILL_BAR_STRESS_PATH,
        RECOVERED_PATH,
        TARGETSTOP_NA_BRANCH_PATH,
        TARGETSTOP_NA_CANDIDATE_PATH,
        TARGETSTOP_NA_CONTRACT_PATH,
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


def group_by_key(input_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[branch_key(row)].append(row)
    return grouped


def classify_interval(row: dict[str, Any]) -> str:
    if row.get("target_stop_contract_id") == "TARGETSTOP_NA_NA" or row.get("branch_result_class") == "NO_RSTYLE_PROXY_INTERVAL_AVAILABLE":
        return "NO_INTERVAL_AVAILABLE"
    if row.get("branch_result_class") == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
        return "INTERVAL_STRADDLES_ZERO"
    if row.get("ordering_collapse_route") == "NO_ORDERING_COLLAPSE_REQUIRED":
        return "POINT_OR_ORDERED_PROXY_INTERVAL_PRESENT"
    return "INTERVAL_BOUNDS_PRESENT_NONSTRADDLE_OR_MIDPOINT"


def classify_collapse(
    row: dict[str, Any],
    m15_count: int,
    m1_replay_count: int,
    fill_stress_count: int,
    recovered_count: int,
) -> tuple[str, str, str]:
    route = str(row.get("ordering_collapse_route"))
    has_m15 = m15_count > 0
    has_m1 = (m1_replay_count + fill_stress_count) > 0
    has_recovered = recovered_count > 0

    if route == "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY":
        return (
            "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY",
            "Use binding repair rows; do not coerce the entry-provenance branch into one target/stop result.",
            "BINDING_SCOPE_ONLY",
        )
    if route == "NO_ORDERING_COLLAPSE_REQUIRED":
        return (
            "NO_COLLAPSE_REQUIRED_ORDERED_PROXY_PRESERVED",
            "Carry branch as already ordered/point-proxy and route remaining work through source/cost/fillability controls.",
            "NO_COLLAPSE_REQUIRED",
        )
    if has_m1 and route == "M1_FILL_BAR_STRESS_OR_TICK_ORDERING_ROUTE":
        return (
            "M1_FILL_BAR_STRESS_AVAILABLE_INTERVAL_BOUND_PRESERVED",
            "Use existing M1 replay plus conservative/optimistic fill-bar stress rows; preserve remaining interval bounds.",
            "M1_STRESS_AVAILABLE",
        )
    if has_m1 and route == "ATTEMPT_M1_CHRONOLOGICAL_COLLAPSE":
        return (
            "M1_CHRONOLOGICAL_REPLAY_AVAILABLE_FOR_COLLAPSE",
            "Use existing M1 replay/stress rows to split ordered components from remaining same-bar intervals.",
            "M1_REPLAY_AVAILABLE",
        )
    if has_m1:
        return (
            "M1_REPLAY_OR_STRESS_PRESENT_ROUTE_REVIEW",
            "Use existing M1 rows, but preserve route mismatch for review before directional collapse.",
            "M1_REPLAY_AVAILABLE_ROUTE_REVIEW",
        )
    if has_m15:
        return (
            "M15_SAME_BAR_NO_EXISTING_M1_INTERVAL_PRESERVED",
            "Preserve M15 interval bounds and route to tick/M1/source acquisition only if current branch needs directional collapse.",
            "M15_INTERVAL_ONLY",
        )
    if has_recovered:
        return (
            "RECOVERED_FILL_PATH_PRESENT_WITHOUT_M1_REPLAY_KEY",
            "Use recovered-fill path evidence as a source-stress proxy and keep original ordering ambiguity explicit.",
            "RECOVERED_PROXY_ONLY",
        )
    if "AMBIGUITY" in route or row.get("ambiguous_ordering_rows"):
        return (
            "ORDERING_AMBIGUITY_WITHOUT_M15_OR_M1_CURRENT_SOURCE",
            "Preserve interval/action route and record source reason; no current lower-timeframe collapse source joins this branch key.",
            "NO_CURRENT_COLLAPSE_SOURCE",
        )
    return (
        "AMBIGUITY_COLLAPSE_REVIEW_REQUIRED",
        "Review new route/source combination before collapsing interval bounds.",
        "REVIEW_REQUIRED",
    )


def summarize_status(rows_for_key: list[dict[str, Any]], field: str) -> dict[str, int]:
    return compact_counter(Counter(str(row.get(field)) for row in rows_for_key))


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}

    artifact_paths = [
        RESULT_PATH,
        BRANCH_LEDGER_PATH,
        M15_SAME_BAR_PATH,
        M1_STRESS_JOIN_PATH,
        ORDERING_ROUTE_PATH,
        INTERVAL_PRESERVATION_PATH,
        TARGETSTOP_NA_BINDING_PATH,
        ACTION_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    artifact_names = {path.name for path in artifact_paths}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in [
        (RESULT_PATH, "result"),
        (BRANCH_LEDGER_PATH, "branch_classification_ledger"),
        (M15_SAME_BAR_PATH, "m15_same_bar_classification_ledger"),
        (M1_STRESS_JOIN_PATH, "m1_stress_join_ledger"),
        (ORDERING_ROUTE_PATH, "ordering_route_ledger"),
        (INTERVAL_PRESERVATION_PATH, "interval_preservation_ledger"),
        (TARGETSTOP_NA_BINDING_PATH, "targetstop_na_binding_ledger"),
        (ACTION_PATH, "action_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_ambiguity_collapse_packet",
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
        (Path(__file__).resolve(), "branch_ambiguity_collapse_builder"),
        (RESULT_PATH, "branch_ambiguity_collapse_result"),
        (BRANCH_LEDGER_PATH, "branch_ambiguity_collapse_branch_classification_ledger"),
        (M15_SAME_BAR_PATH, "branch_ambiguity_collapse_m15_same_bar_ledger"),
        (M1_STRESS_JOIN_PATH, "branch_ambiguity_collapse_m1_stress_join_ledger"),
        (ORDERING_ROUTE_PATH, "branch_ambiguity_collapse_ordering_route_ledger"),
        (INTERVAL_PRESERVATION_PATH, "branch_ambiguity_collapse_interval_preservation_ledger"),
        (TARGETSTOP_NA_BINDING_PATH, "branch_ambiguity_collapse_targetstop_na_binding_ledger"),
        (ACTION_PATH, "branch_ambiguity_collapse_action_ledger"),
        (BUCKET_PATH, "branch_ambiguity_collapse_bucket_ledger"),
        (QUESTION_PATH, "branch_ambiguity_collapse_question_ledger"),
        (SUMMARY_PATH, "branch_ambiguity_collapse_summary"),
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
        "route": "historical_ohlc_gtos_replay_branch_ambiguity_collapse_packet",
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
        "# Historical OHLC GTOS Branch Ambiguity-Collapse Packet",
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
    lines.extend(["", "## Ambiguity Collapse Distribution", ""])
    for bucket, count in result["bucket_distributions"]["ambiguity_collapse_class"].items():
        lines.append(f"- {bucket}: {count}")
    lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()

    matrix_rows = rows(MATRIX_BRANCH_PATH)
    matrix_ambiguity_by_branch = {row.get("branch_queue_id"): row for row in rows(MATRIX_AMBIGUITY_PATH)}
    matrix_source_by_branch = {row.get("branch_queue_id"): row for row in rows(MATRIX_SOURCE_REPAIR_PATH)}
    source_feas_by_branch = {row.get("branch_queue_id"): row for row in rows(SOURCE_REPAIR_FEAS_PATH)}
    rstyle_by_branch = {row.get("branch_queue_id"): row for row in rows(RSTYLE_BRANCH_PATH)}

    m15_rows = rows(PATH_AMBIGUITY_PATH)
    m1_rows = rows(M1_REPLAY_PATH)
    fill_stress_rows = rows(M1_FILL_BAR_STRESS_PATH)
    recovered_rows = rows(RECOVERED_PATH)
    targetstop_na_branch_rows = rows(TARGETSTOP_NA_BRANCH_PATH)
    targetstop_na_candidate_rows = rows(TARGETSTOP_NA_CANDIDATE_PATH)
    targetstop_na_contract_rows = rows(TARGETSTOP_NA_CONTRACT_PATH)

    m15_by_key = group_by_key(m15_rows)
    m1_by_key = group_by_key(m1_rows)
    fill_stress_by_key = group_by_key(fill_stress_rows)
    recovered_by_key = group_by_key(recovered_rows)
    targetstop_na_branch_by_branch = defaultdict(list)
    targetstop_na_candidate_by_branch = defaultdict(list)
    targetstop_na_contract_by_branch = defaultdict(list)
    for row in targetstop_na_branch_rows:
        targetstop_na_branch_by_branch[row.get("branch_queue_id")].append(row)
    for row in targetstop_na_candidate_rows:
        targetstop_na_candidate_by_branch[row.get("branch_queue_id")].append(row)
    for row in targetstop_na_contract_rows:
        targetstop_na_contract_by_branch[row.get("branch_queue_id")].append(row)

    branch_rows: list[dict[str, Any]] = []
    m15_same_bar_rows: list[dict[str, Any]] = []
    m1_stress_join_rows: list[dict[str, Any]] = []
    ordering_route_rows: list[dict[str, Any]] = []
    interval_rows: list[dict[str, Any]] = []
    targetstop_binding_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)

    for index, row in enumerate(matrix_rows, 1):
        key = branch_key(row)
        branch_id = row.get("branch_queue_id")
        m15_for_key = m15_by_key.get(key, [])
        m1_for_key = m1_by_key.get(key, [])
        fill_stress_for_key = fill_stress_by_key.get(key, [])
        recovered_for_key = recovered_by_key.get(key, [])
        source_feas = source_feas_by_branch.get(branch_id, {})
        matrix_amb = matrix_ambiguity_by_branch.get(branch_id, {})
        matrix_source = matrix_source_by_branch.get(branch_id, {})
        rstyle = rstyle_by_branch.get(branch_id, {})

        m15_class = "HAS_M15_PATH_SAME_BAR" if m15_for_key else "NO_M15_PATH_SAME_BAR"
        m1_class = "EXISTING_M1_REPLAY_OR_STRESS" if (m1_for_key or fill_stress_for_key) else "NO_EXISTING_M1_REPLAY_OR_STRESS"
        recovered_class = "RECOVERED_FILL_PATH_ROWS_PRESENT" if recovered_for_key else "NO_RECOVERED_FILL_PATH_ROWS"
        interval_class = classify_interval(row)
        collapse_class, next_action, action_route = classify_collapse(
            row,
            len(m15_for_key),
            len(m1_for_key),
            len(fill_stress_for_key),
            len(recovered_for_key),
        )
        targetstop_binding_class = (
            "TARGETSTOP_NA_BINDING_ROWS_PRESENT"
            if row.get("target_stop_contract_id") == "TARGETSTOP_NA_NA" or targetstop_na_branch_by_branch.get(branch_id)
            else "NOT_TARGETSTOP_NA_BRANCH"
        )

        bucket_counters["m15_same_bar_class"][m15_class] += 1
        bucket_counters["m1_existing_class"][m1_class] += 1
        bucket_counters["recovered_path_class"][recovered_class] += 1
        bucket_counters["ordering_collapse_route"][str(row.get("ordering_collapse_route"))] += 1
        bucket_counters["interval_preservation_class"][interval_class] += 1
        bucket_counters["ambiguity_collapse_class"][collapse_class] += 1
        bucket_counters["targetstop_na_binding_class"][targetstop_binding_class] += 1
        bucket_counters["source_repair_route_class"][str(source_feas.get("source_repair_route_class"))] += 1
        bucket_counters["repair_feasibility_class"][str(source_feas.get("repair_feasibility_class"))] += 1
        bucket_counters["branch_result_class"][str(row.get("branch_result_class"))] += 1
        bucket_counters["target_stop_result"][str(row.get("target_stop_result"))] += 1
        bucket_counters["effective_n_concentration_class"][str(row.get("effective_n_concentration_class"))] += 1

        common = {
            "branch_queue_id": branch_id,
            "branch_proxy_score_id": row.get("branch_proxy_score_id"),
            "branch_rstyle_proxy_outcome_id": row.get("branch_rstyle_proxy_outcome_id"),
            "route_candidate_id": row.get("route_candidate_id"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "side": row.get("side"),
            "entry_variant": row.get("entry_variant"),
            "target_stop_contract_id": row.get("target_stop_contract_id"),
            "target_multiple": row.get("target_multiple"),
            "stop_multiple": row.get("stop_multiple"),
            "branch_result_class": row.get("branch_result_class"),
            "target_stop_result": row.get("target_stop_result"),
            "ordering_collapse_route": row.get("ordering_collapse_route"),
            "source_confidence_status": row.get("source_confidence_status"),
            "source_repairability_class": row.get("source_repairability_class"),
            "exact_spread_repairability_class": row.get("exact_spread_repairability_class"),
            "repair_feasibility_class": source_feas.get("repair_feasibility_class"),
            "source_repair_route_class": source_feas.get("source_repair_route_class"),
            "effective_n_concentration_class": row.get("effective_n_concentration_class"),
            "unique_event_or_route_ids": row.get("unique_event_or_route_ids"),
            "duplicate_inflation_ratio_material_rows_over_event_ids": row.get(
                "duplicate_inflation_ratio_material_rows_over_event_ids"
            ),
            "exact_failure_cause": row.get("exact_failure_cause"),
            "exact_success_cause": row.get("exact_success_cause"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }

        branch_out = {
            "ambiguity_collapse_packet_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-COLLAPSE-{index:05d}",
            **common,
            "m15_same_bar_class": m15_class,
            "m15_same_bar_rows_for_branch_key": len(m15_for_key),
            "m15_same_bar_status_counts": summarize_status(m15_for_key, "ambiguity_status"),
            "m1_existing_class": m1_class,
            "m1_spread_adjusted_replay_rows_for_branch_key": len(m1_for_key),
            "m1_fill_bar_stress_rows_for_branch_key": len(fill_stress_for_key),
            "m1_replay_first_touch_status_counts": summarize_status(m1_for_key, "m1_first_touch_status"),
            "m1_fill_bar_interval_status_counts": summarize_status(fill_stress_for_key, "interval_status"),
            "m1_fill_bar_stress_scope_counts": summarize_status(fill_stress_for_key, "stress_scope_status"),
            "recovered_path_class": recovered_class,
            "recovered_signature_path_rows_for_branch_key": len(recovered_for_key),
            "recovered_first_touch_status_counts": summarize_status(recovered_for_key, "recovered_first_touch_status"),
            "interval_preservation_class": interval_class,
            "ambiguity_collapse_class": collapse_class,
            "ambiguity_collapse_next_action": next_action,
            "ambiguity_action_route": action_route,
            "matrix_ambiguity_collapse_class": matrix_amb.get("ambiguity_collapse_class"),
            "matrix_ambiguity_next_step": matrix_amb.get("mechanical_next_step"),
            "matrix_source_repair_class": matrix_source.get("source_repair_class"),
            "rstyle_lower_mean": row.get("rstyle_lower_mean", rstyle.get("expectancy_style_proxy", {}).get("lower_mean")),
            "rstyle_midpoint_mean": row.get("rstyle_midpoint_mean", rstyle.get("expectancy_style_proxy", {}).get("midpoint_mean")),
            "rstyle_upper_mean": row.get("rstyle_upper_mean", rstyle.get("expectancy_style_proxy", {}).get("upper_mean")),
            "rstyle_interval_rows": row.get("rstyle_interval_rows"),
            "ambiguous_ordering_rows": row.get("ambiguous_ordering_rows"),
            "targetstop_na_binding_class": targetstop_binding_class,
            "targetstop_na_branch_binding_rows": len(targetstop_na_branch_by_branch.get(branch_id, [])),
            "targetstop_na_candidate_binding_rows": len(targetstop_na_candidate_by_branch.get(branch_id, [])),
            "targetstop_na_contract_summary_rows": len(targetstop_na_contract_by_branch.get(branch_id, [])),
            "exact_missing_geometry_reason": row.get("exact_missing_geometry_reason"),
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_PACKET",
        }
        branch_rows.append(branch_out)

        m15_same_bar_rows.append(
            {
                "m15_same_bar_classification_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-M15-SAMEBAR-{index:05d}",
                **common,
                "m15_same_bar_class": m15_class,
                "m15_same_bar_rows_for_branch_key": len(m15_for_key),
                "m15_ambiguity_status_counts": summarize_status(m15_for_key, "ambiguity_status"),
                "m15_cost_model_counts": summarize_status(m15_for_key, "cost_model"),
                "m15_event_ids": sorted({str(item.get("event_id")) for item in m15_for_key}),
                "m15_event_id_count": len({str(item.get("event_id")) for item in m15_for_key}),
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_M15_SAME_BAR",
            }
        )
        m1_stress_join_rows.append(
            {
                "m1_stress_join_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-M1-STRESS-JOIN-{index:05d}",
                **common,
                "m1_existing_class": m1_class,
                "m1_spread_adjusted_replay_rows_for_branch_key": len(m1_for_key),
                "m1_fill_bar_stress_rows_for_branch_key": len(fill_stress_for_key),
                "recovered_path_class": recovered_class,
                "recovered_signature_path_rows_for_branch_key": len(recovered_for_key),
                "m1_replay_first_touch_status_counts": summarize_status(m1_for_key, "m1_first_touch_status"),
                "fill_bar_interval_status_counts": summarize_status(fill_stress_for_key, "interval_status"),
                "fill_bar_conservative_status_counts": summarize_status(fill_stress_for_key, "conservative_first_touch_status"),
                "fill_bar_optimistic_status_counts": summarize_status(fill_stress_for_key, "optimistic_first_touch_status"),
                "recovered_path_status_counts": summarize_status(recovered_for_key, "recovered_path_status"),
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_M1_STRESS_JOIN",
            }
        )
        ordering_route_rows.append(
            {
                "ordering_route_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-ORDERING-ROUTE-{index:05d}",
                **common,
                "m15_same_bar_class": m15_class,
                "m1_existing_class": m1_class,
                "recovered_path_class": recovered_class,
                "ambiguity_collapse_class": collapse_class,
                "ambiguity_collapse_next_action": next_action,
                "action_route": action_route,
                "matrix_ambiguity_collapse_class": matrix_amb.get("ambiguity_collapse_class"),
                "matrix_ambiguity_next_step": matrix_amb.get("mechanical_next_step"),
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ORDERING_ROUTE",
            }
        )
        interval_rows.append(
            {
                "interval_preservation_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-INTERVAL-{index:05d}",
                **common,
                "interval_preservation_class": interval_class,
                "rstyle_lower_mean": branch_out["rstyle_lower_mean"],
                "rstyle_midpoint_mean": branch_out["rstyle_midpoint_mean"],
                "rstyle_upper_mean": branch_out["rstyle_upper_mean"],
                "rstyle_interval_rows": branch_out["rstyle_interval_rows"],
                "ambiguous_ordering_rows": row.get("ambiguous_ordering_rows"),
                "ambiguity_collapse_class": collapse_class,
                "exact_missing_geometry_reason": row.get("exact_missing_geometry_reason"),
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_INTERVAL_PRESERVATION",
            }
        )
        action_rows.append(
            {
                "ambiguity_collapse_action_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-ACTION-{index:05d}",
                **common,
                "m15_same_bar_class": m15_class,
                "m1_existing_class": m1_class,
                "interval_preservation_class": interval_class,
                "ambiguity_collapse_class": collapse_class,
                "mechanical_next_step": next_action,
                "action_route": action_route,
                "not_completion": True,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ACTION",
            }
        )

    binding_index = 0
    for row_type, source_rows in [
        ("TARGETSTOP_NA_BRANCH", targetstop_na_branch_rows),
        ("TARGETSTOP_NA_CANDIDATE_BOUND", targetstop_na_candidate_rows),
        ("TARGETSTOP_NA_CONTRACT_SUMMARY_BOUND", targetstop_na_contract_rows),
    ]:
        for source_row in source_rows:
            binding_index += 1
            targetstop_binding_rows.append(
                {
                    "targetstop_na_binding_packet_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-TARGETSTOP-NA-{binding_index:05d}",
                    "row_type": row_type,
                    "source_binding_id": source_row.get("targetstop_na_repair_id")
                    or source_row.get("targetstop_na_binding_candidate_id")
                    or source_row.get("targetstop_na_contract_summary_id"),
                    "branch_queue_id": source_row.get("branch_queue_id"),
                    "route_candidate_id": source_row.get("route_candidate_id"),
                    "symbol": source_row.get("symbol"),
                    "route_session": source_row.get("route_session"),
                    "side": source_row.get("side"),
                    "entry_variant": source_row.get("entry_variant"),
                    "target_stop_contract_id": source_row.get("target_stop_contract_id", source_row.get("original_target_stop_contract_id")),
                    "binding_repair_status": source_row.get("binding_repair_status", "SIGNATURE_SCOPE_BOUND_ROW"),
                    "signature_scope_status_counts": source_row.get("signature_scope_status_counts"),
                    "m1_first_touch_status_counts": source_row.get("m1_first_touch_status_counts"),
                    "touch_class_counts": source_row.get("touch_class_counts"),
                    "candidate_rows": source_row.get("candidate_rows"),
                    "cost_model": source_row.get("cost_model"),
                    "m1_first_touch_status": source_row.get("m1_first_touch_status"),
                    "touch_class": source_row.get("touch_class"),
                    "interpretation": "TARGETSTOP_NA entry-provenance branch remains separate; target/stop evidence is bound through signature-scope rows.",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_TARGETSTOP_NA_BINDING",
                }
            )

    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items()):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-BRANCH-AMBIGUITY-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": bucket,
                    "branch_count": count,
                    "branch_share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    ordering_without_m15 = sum(
        1
        for row in branch_rows
        if row["m15_same_bar_class"] == "NO_M15_PATH_SAME_BAR"
        and row["ordering_collapse_route"] not in {"NO_ORDERING_COLLAPSE_REQUIRED", "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY"}
    )
    fill_bar_source_fail_closed_rows = sum(
        count
        for status, count in Counter(
            str(item.get("conservative_source_status")) for item in fill_stress_rows
        ).items()
        if "FAIL_CLOSED" in status or "MISSING" in status
    )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-BRANCH-AMBIGUITY-QUESTION-001",
            "question": "Which M15 same-bar branches can be collapsed by existing M1 replay/stress rows versus interval-preserved?",
            "answer_route": "Use m15_same_bar_class, m1_existing_class, ordering_collapse_route, and ambiguity_collapse_class over all 386 branches.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-AMBIGUITY-QUESTION-002",
            "question": "Which ordering-ambiguity branches have no M15 same-bar rows and therefore indicate source/status mismatch or lower-level route dependency?",
            "answer_route": f"Preserve {ordering_without_m15} no-M15 ordering-route branches as explicit review/source-action rows.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-AMBIGUITY-QUESTION-003",
            "question": "Which interval-straddles-zero branches remain non-directional after current M1/stress evidence?",
            "answer_route": "Use interval_preservation_class plus ambiguity_collapse_class; do not coerce interval rows into a sign.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-AMBIGUITY-QUESTION-004",
            "question": "How should TARGETSTOP_NA rows be used without losing target/stop contract intelligence?",
            "answer_route": "Use the 162-row targetstop NA binding ledger: 2 entry-provenance rows, 128 signature-scope candidate rows, and 32 contract summaries.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-AMBIGUITY-QUESTION-005",
            "question": "Which fill-bar stress rows remain fail-closed because next-M1/source ordering is absent?",
            "answer_route": f"Carry conservative source-status counts including {fill_bar_source_fail_closed_rows} fail-closed or missing-source stress rows into the next ordering repair packet.",
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
                    "m15_same_bar_class": compact_counter(bucket_counters["m15_same_bar_class"]),
                    "m1_existing_class": compact_counter(bucket_counters["m1_existing_class"]),
                    "interval_preservation_class": compact_counter(bucket_counters["interval_preservation_class"]),
                    "ambiguity_collapse_class": compact_counter(bucket_counters["ambiguity_collapse_class"]),
                },
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_PACKET",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "counts": {
            "matrix_branch_input_rows": len(matrix_rows),
            "matrix_ambiguity_input_rows": len(matrix_ambiguity_by_branch),
            "matrix_source_repair_input_rows": len(matrix_source_by_branch),
            "source_repair_feasibility_input_rows": len(source_feas_by_branch),
            "rstyle_branch_input_rows": len(rstyle_by_branch),
            "m15_path_ambiguity_input_rows": len(m15_rows),
            "m1_replay_input_rows": len(m1_rows),
            "m1_fill_bar_stress_input_rows": len(fill_stress_rows),
            "recovered_signature_path_input_rows": len(recovered_rows),
            "targetstop_na_branch_input_rows": len(targetstop_na_branch_rows),
            "targetstop_na_candidate_input_rows": len(targetstop_na_candidate_rows),
            "targetstop_na_contract_input_rows": len(targetstop_na_contract_rows),
            "branch_classification_rows": len(branch_rows),
            "m15_same_bar_classification_rows": len(m15_same_bar_rows),
            "m1_stress_join_rows": len(m1_stress_join_rows),
            "ordering_route_rows": len(ordering_route_rows),
            "interval_preservation_rows": len(interval_rows),
            "targetstop_na_binding_rows": len(targetstop_binding_rows),
            "action_rows": len(action_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(manifest_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "m1_fill_bar_conservative_source_status_counts": compact_counter(
            Counter(str(item.get("conservative_source_status")) for item in fill_stress_rows)
        ),
        "m1_fill_bar_interval_status_counts": compact_counter(Counter(str(item.get("interval_status")) for item in fill_stress_rows)),
        "targetstop_na_binding_row_type_counts": compact_counter(Counter(row["row_type"] for row in targetstop_binding_rows)),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
    }

    write_jsonl(BRANCH_LEDGER_PATH, branch_rows)
    write_jsonl(M15_SAME_BAR_PATH, m15_same_bar_rows)
    write_jsonl(M1_STRESS_JOIN_PATH, m1_stress_join_rows)
    write_jsonl(ORDERING_ROUTE_PATH, ordering_route_rows)
    write_jsonl(INTERVAL_PRESERVATION_PATH, interval_rows)
    write_jsonl(TARGETSTOP_NA_BINDING_PATH, targetstop_binding_rows)
    write_jsonl(ACTION_PATH, action_rows)
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
