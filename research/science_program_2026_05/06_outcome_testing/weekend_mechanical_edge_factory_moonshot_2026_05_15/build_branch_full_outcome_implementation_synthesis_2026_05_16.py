#!/usr/bin/env python3
"""Build a full-denominator branch outcome and implementation synthesis.

This packet is deliberately one row per branch_queue_id for the main ledger.
Subset packets such as source-stress, M15 interval, and M1 fill-bar interval
are joined as layer status/context, never as denominator shrinkage.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

RSTYLE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
RSTYLE_CONTROL = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONTROL_DELTA_LEDGER_2026-05-16.jsonl"
RSTYLE_CAUSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CAUSE_LEDGER_2026-05-16.jsonl"
RSTYLE_CONCENTRATION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONCENTRATION_LEDGER_2026-05-16.jsonl"
DUP_EFFECTIVE_N = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_2026-05-16.jsonl"
IMPL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
LOCAL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
CODE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_BRANCH_LEDGER_2026-05-16.jsonl"
REPLAY_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_ORDERING = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_ORDERING_LEDGER_2026-05-16.jsonl"
SOURCE_STRESS = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_ACQUISITION_BRANCH_LEDGER_2026-05-16.jsonl"
M15_INTERVAL = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
M1_FILL_INTERVAL = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_INTERVAL_COLLAPSE_BRANCH_LEDGER_2026-05-16.jsonl"
EXACT_REPAIR = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_EXACT_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"
ENTRY_REDESIGN = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ADVERSE_REDESIGN = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
POSITIVE_IMPL = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
POSITIVE_REPLAY_SPEC = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_REPLAY_SPEC_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
LAYER_JOIN_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_LAYER_JOIN_LEDGER_2026-05-16.jsonl"
ACTION_MATRIX_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_ACTION_MATRIX_LEDGER_2026-05-16.jsonl"
CONFLICT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_CONFLICT_LEDGER_2026-05-16.jsonl"
NEXT_COMPUTE_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_NEXT_COMPUTE_LEDGER_2026-05-16.jsonl"
CONCENTRATION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_CONCENTRATION_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Full-denominator branch outcome and implementation synthesis only. "
    "The packet preserves all 386 historical OHLC/MT5/Sierra proxy branches and "
    "joins sealed/proxy R-style outcome, expectancy-style proxy, target/stop, "
    "pass-control, cost, duplicate/effective-N, concentration, source confidence, "
    "ambiguity, source-stress, M15/M1 interval, code/replay, implementation, and "
    "failure/success-cause fields. It does not claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, promotion, or live behavior change."
)

MISSING_EXACT_REASON = (
    "Exact R/PnL cannot be computed from this evidence class because broker-realized "
    "fills, account history, true executed stop distance, slippage, partial exits, "
    "and order lifecycle are not source-bound in these historical proxy rows. "
    "The packet computes the strongest available lower-level target/stop/path proxy "
    "and records the exact source, ordering, and fillability limits per branch."
)

REQUIRED_METRIC_KEYS = [
    "sealed_or_proxy_rstyle_outcome",
    "expectancy_style_proxy",
    "target_stop_result",
    "pass_control_delta",
    "cost_sensitivity",
    "duplicate_effective_n",
    "concentration",
    "source_confidence",
    "ambiguity",
    "implementation_implication",
    "exact_failure_success_cause",
    "missing_exact_geometry_or_source_reason",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"_parse_error": True, "_line_no": line_no, "_source_path": str(path)})
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id") is not None}


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        return (branch_id.rsplit("-", 1)[0], int(branch_id.rsplit("-", 1)[1]))
    except (ValueError, IndexError):
        return (branch_id, 0)


def source_manifest_rows(paths: list[Path]) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rel = path.relative_to(REPO).as_posix()
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-FULL-OUTCOME-SRC-{index:04d}",
                "path": rel,
                "sha256": sha256_file(path) if path.exists() else None,
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def layer_excerpt(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "branch_result_class",
        "target_stop_result",
        "sealed_proxy_class",
        "source_execution_class",
        "ordering_execution_class",
        "source_deep_action_class",
        "ordering_deep_action_class",
        "source_stress_action_class",
        "ordering_collapse_action_class",
        "branch_priority",
        "branch_local_candidate_stage",
        "positive_replay_status",
        "positive_replayable_now",
        "branch_stress_class",
        "interval_sign_class",
        "branch_aggregate_interval_sign_class",
        "m1_support_interval_sign_class",
        "m1_support_resolution_class",
        "repair_feasibility_class",
        "entry_geometry_retest_class",
        "adverse_stop_first_class",
        "positive_challenger_class",
    ]
    return {key: row.get(key) for key in keys if key in row}


def metric_coverage(row: dict[str, Any]) -> tuple[dict[str, bool], str, list[str]]:
    coverage = {
        "sealed_or_proxy_rstyle_outcome": bool(row.get("sealed_or_proxy_outcome_status") or row.get("branch_result_class")),
        "expectancy_style_proxy": bool(row.get("expectancy_style_proxy")),
        "target_stop_result": bool(row.get("target_stop_result")),
        "pass_control_delta": bool(row.get("pass_control_delta")),
        "cost_sensitivity": bool(row.get("cost_sensitivity")),
        "duplicate_effective_n": bool(row.get("duplicate_effective_n")),
        "concentration": bool(row.get("concentration_summary")),
        "source_confidence": bool(row.get("source_confidence_status")),
        "ambiguity": bool(row.get("ambiguity_status")),
        "implementation_implication": bool(row.get("implementation_implication")),
        "exact_failure_success_cause": bool(row.get("exact_failure_cause") and row.get("exact_success_cause")),
        "missing_exact_geometry_or_source_reason": bool(row.get("exact_missing_geometry_or_source_reason")),
    }
    missing = [key for key in REQUIRED_METRIC_KEYS if not coverage[key]]
    status = "ALL_REQUIRED_BRANCH_METRICS_PRESENT" if not missing else "MISSING_REQUIRED_BRANCH_METRICS"
    return coverage, status, missing


def classify_source_stress(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_SOURCE_STRESS_LAYER_SCOPE"
    return str(row.get("branch_stress_class") or "SOURCE_STRESS_LAYER_PRESENT")


def classify_m15(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_M15_INTERVAL_LAYER_SCOPE"
    return str(row.get("interval_sign_class") or row.get("interval_preservation_class") or "M15_INTERVAL_LAYER_PRESENT")


def classify_m1(row: dict[str, Any] | None, branch_result_class: str) -> str:
    if not row:
        return "NO_M1_FILL_BAR_LAYER_SCOPE"
    support_sign = row.get("m1_support_interval_sign_class")
    aggregate = row.get("branch_aggregate_interval_sign_class")
    if support_sign == "INTERVAL_ALL_POSITIVE" and branch_result_class != "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return f"M1_SUPPORT_ALL_POSITIVE_BUT_BRANCH_{branch_result_class}"
    if support_sign == "INTERVAL_ALL_POSITIVE" and aggregate == "INTERVAL_ALL_POSITIVE":
        return "M1_SUPPORT_AND_BRANCH_AGGREGATE_ALL_POSITIVE"
    return f"M1_SUPPORT_{support_sign or 'UNKNOWN'}__BRANCH_{aggregate or 'UNKNOWN'}"


def next_computation_class(
    *,
    source_stress: dict[str, Any] | None,
    m15: dict[str, Any] | None,
    m1: dict[str, Any] | None,
    replay: dict[str, Any],
    local: dict[str, Any],
    code: dict[str, Any],
) -> str:
    if source_stress:
        return "SOURCE_STRESS_RISK_ROUTER_OR_ACQUISITION_NEXT"
    if m15:
        sign = m15.get("interval_sign_class")
        if sign == "INTERVAL_ALL_POSITIVE":
            return "M15_INTERVAL_TARGET_FIRST_CHALLENGER_SCORE_NEXT"
        if sign == "INTERVAL_ALL_NEGATIVE":
            return "M15_INTERVAL_STOP_FIRST_AVOID_REDESIGN_NEXT"
        return "M15_INTERVAL_BOUNDS_ROUTER_NEXT"
    if m1:
        if (
            m1.get("m1_support_interval_sign_class") == "INTERVAL_ALL_POSITIVE"
            and m1.get("branch_aggregate_interval_sign_class") == "INTERVAL_ALL_POSITIVE"
        ):
            return "M1_FILL_BAR_TARGET_STABLE_CHALLENGER_SCORE_NEXT"
        return "M1_FILL_BAR_SUPPORT_BRANCH_CONFLICT_SPLIT_NEXT"
    if code.get("positive_replayable_now") is True or replay.get("positive_replayable_now") is True:
        return "POSITIVE_CHALLENGER_REPLAY_SCORE_NEXT"
    if str(local.get("entry_geometry_retest_class", "")).startswith(("FAR_", "WITHIN_", "NEAR_", "MIXED_")):
        return "ENTRY_GEOMETRY_REDESIGN_SCORE_NEXT"
    if str(local.get("adverse_stop_first_class", "")).startswith("STOP_FIRST"):
        return "ADVERSE_STOP_FIRST_AVOID_REDESIGN_SCORE_NEXT"
    return "PRESERVE_CURRENT_PROXY_AND_ROUTE_BY_BUCKET"


def branch_action_rows(
    *,
    index: int,
    branch_id: str,
    branch: dict[str, Any],
    local: dict[str, Any],
    code: dict[str, Any],
    replay: dict[str, Any],
    source_ordering: dict[str, Any],
    source_stress: dict[str, Any] | None,
    m15: dict[str, Any] | None,
    m1: dict[str, Any] | None,
    entry: dict[str, Any],
    adverse: dict[str, Any],
    positive: dict[str, Any],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    base = {
        "branch_queue_id": branch_id,
        "route_candidate_id": branch.get("route_candidate_id"),
        "symbol": branch.get("symbol"),
        "route_session": branch.get("route_session"),
        "side": branch.get("side"),
        "entry_variant": branch.get("entry_variant"),
        "target_stop_contract_id": branch.get("target_stop_contract_id"),
        "branch_result_class": branch.get("branch_result_class"),
        "target_stop_result": branch.get("target_stop_result"),
    }
    rows = [
        {
            "action_family": "SOURCE",
            "action_class": local.get("source_local_impl_class") or replay.get("source_execution_class"),
            "deep_class": source_ordering.get("source_deep_action_class"),
            "layer_context": classify_source_stress(source_stress),
            "next_computation": (branch.get("branch_local_next_computations") or {}).get("source"),
        },
        {
            "action_family": "ORDERING",
            "action_class": local.get("ordering_local_impl_class") or replay.get("ordering_execution_class"),
            "deep_class": source_ordering.get("ordering_deep_action_class"),
            "layer_context": classify_m1(m1, str(branch.get("branch_result_class"))) if m1 else classify_m15(m15),
            "next_computation": (branch.get("branch_local_next_computations") or {}).get("ordering"),
        },
        {
            "action_family": "ENTRY",
            "action_class": local.get("entry_local_impl_class") or entry.get("entry_geometry_redesign_class"),
            "deep_class": local.get("entry_geometry_retest_class") or entry.get("entry_geometry_retest_class"),
            "layer_context": branch.get("fillability_bucket"),
            "next_computation": (branch.get("branch_local_next_computations") or {}).get("entry"),
        },
        {
            "action_family": "ADVERSE",
            "action_class": local.get("adverse_local_impl_class") or adverse.get("adverse_stop_first_redesign_class"),
            "deep_class": local.get("adverse_stop_first_class") or adverse.get("adverse_stop_first_class"),
            "layer_context": branch.get("target_stop_result"),
            "next_computation": (branch.get("branch_local_next_computations") or {}).get("adverse"),
        },
        {
            "action_family": "POSITIVE",
            "action_class": local.get("positive_local_impl_class") or positive.get("positive_challenger_class"),
            "deep_class": code.get("positive_replay_status") or positive.get("positive_deep_action_class"),
            "layer_context": code.get("positive_replayable_now"),
            "next_computation": (branch.get("branch_local_next_computations") or {}).get("positive"),
        },
    ]
    output = []
    for seq, row in enumerate(rows, 1):
        output.append(
            {
                "full_outcome_action_id": f"OHLC-GTOS-FULL-OUTCOME-ACTION-{index:05d}-{seq}",
                **base,
                **row,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
    return output


def write_summary(result: dict[str, Any]) -> None:
    counts = result["counts"]
    buckets = result["bucket_distributions"]
    lines = [
        "# Historical OHLC GTOS Replay Branch Full Outcome Implementation Synthesis",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Key Distributions", ""])
    for category in [
        "next_computation_class",
        "branch_result_class",
        "target_stop_result",
        "source_execution_class",
        "ordering_execution_class",
        "source_stress_status",
        "m15_interval_status",
        "m1_support_vs_branch_status",
        "metric_coverage_status",
    ]:
        lines.append(f"### {category}")
        for bucket, count in buckets.get(category, {}).items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    lines.extend(
        [
            "## Continuation",
            "",
            "This packet is not completion. It is the all-branch routing layer for the next same-resource computations: source-stress risk routing/acquisition, M15 interval avoid/challenger scoring, M1 fill-bar support-vs-branch conflict splitting, positive challenger replay scoring, and entry/adverse redesign scoring.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    if OUTPUT_MANIFEST.exists():
        manifest = read_json(OUTPUT_MANIFEST)
    else:
        manifest = {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [
        RESULT_PATH,
        BRANCH_LEDGER,
        LAYER_JOIN_LEDGER,
        ACTION_MATRIX_LEDGER,
        CONFLICT_LEDGER,
        NEXT_COMPUTE_LEDGER,
        CONCENTRATION_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    existing = [item for item in manifest.get("artifacts", []) if item.get("path") not in {p.relative_to(REPO).as_posix() for p in output_paths}]
    for path in output_paths:
        existing.append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_full_outcome_implementation_synthesis",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["artifacts"] = existing
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    event = {
        "timestamp_utc": generated_at,
        "event_type": "branch_full_outcome_implementation_synthesis_built",
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        RSTYLE_BRANCH,
        RSTYLE_CONTROL,
        RSTYLE_CAUSE,
        RSTYLE_CONCENTRATION,
        DUP_EFFECTIVE_N,
        IMPL_BRANCH,
        LOCAL_BRANCH,
        CODE_BRANCH,
        REPLAY_BRANCH,
        SOURCE_ORDERING,
        SOURCE_STRESS,
        M15_INTERVAL,
        M1_FILL_INTERVAL,
        EXACT_REPAIR,
        ENTRY_REDESIGN,
        ADVERSE_REDESIGN,
        POSITIVE_IMPL,
        POSITIVE_REPLAY_SPEC,
    ]
    source_rows, manifest_hash = source_manifest_rows(source_paths)

    rstyle_rows = read_jsonl(RSTYLE_BRANCH)
    branch_ids = sorted([str(row["branch_queue_id"]) for row in rstyle_rows], key=branch_sort_key)
    rstyle = by_branch(rstyle_rows)
    control = by_branch(read_jsonl(RSTYLE_CONTROL))
    cause = by_branch(read_jsonl(RSTYLE_CAUSE))
    dup = by_branch(read_jsonl(DUP_EFFECTIVE_N))
    impl = by_branch(read_jsonl(IMPL_BRANCH))
    local = by_branch(read_jsonl(LOCAL_BRANCH))
    code = by_branch(read_jsonl(CODE_BRANCH))
    replay = by_branch(read_jsonl(REPLAY_BRANCH))
    source_ordering = by_branch(read_jsonl(SOURCE_ORDERING))
    source_stress = by_branch(read_jsonl(SOURCE_STRESS))
    m15 = by_branch(read_jsonl(M15_INTERVAL))
    m1 = by_branch(read_jsonl(M1_FILL_INTERVAL))
    exact = by_branch(read_jsonl(EXACT_REPAIR))
    entry = by_branch(read_jsonl(ENTRY_REDESIGN))
    adverse = by_branch(read_jsonl(ADVERSE_REDESIGN))
    positive = by_branch(read_jsonl(POSITIVE_IMPL))
    positive_spec = by_branch(read_jsonl(POSITIVE_REPLAY_SPEC))
    concentration_input_rows = read_jsonl(RSTYLE_CONCENTRATION)

    layer_maps = {
        "RSTYLE_OUTCOME": (rstyle, "FULL_386_BRANCH_DENOMINATOR"),
        "CONTROL_DELTA": (control, "FULL_386_BRANCH_DENOMINATOR"),
        "CAUSE": (cause, "FULL_386_BRANCH_DENOMINATOR"),
        "DUPLICATE_EFFECTIVE_N": (dup, "FULL_386_BRANCH_DENOMINATOR"),
        "IMPLEMENTATION_SYNTHESIS": (impl, "FULL_386_BRANCH_DENOMINATOR"),
        "LOCAL_IMPLEMENTATION": (local, "FULL_386_BRANCH_DENOMINATOR"),
        "CODE_REPLAY": (code, "FULL_386_BRANCH_DENOMINATOR"),
        "REPLAY_EXECUTION": (replay, "FULL_386_BRANCH_DENOMINATOR"),
        "SOURCE_ORDERING": (source_ordering, "FULL_386_BRANCH_DENOMINATOR"),
        "SOURCE_STRESS_ACQUISITION": (source_stress, "SUBSET_LAYER"),
        "M15_INTERVAL_COLLAPSE": (m15, "SUBSET_LAYER"),
        "M1_FILL_BAR_INTERVAL_COLLAPSE": (m1, "SUBSET_LAYER"),
        "EXACT_REPAIR": (exact, "SUBSET_LAYER"),
        "ENTRY_REDESIGN": (entry, "FULL_OR_BRANCH_SCOPE_LAYER"),
        "ADVERSE_REDESIGN": (adverse, "FULL_OR_BRANCH_SCOPE_LAYER"),
        "POSITIVE_IMPLEMENTATION": (positive, "SUBSET_LAYER"),
        "POSITIVE_REPLAY_SPEC": (positive_spec, "SUBSET_LAYER"),
    }

    branch_rows: list[dict[str, Any]] = []
    layer_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    conflict_rows: list[dict[str, Any]] = []
    next_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = {
        "branch_result_class": Counter(),
        "target_stop_result": Counter(),
        "sealed_proxy_outcome_status": Counter(),
        "pass_control_delta_status": Counter(),
        "cost_sensitivity_proxy_status": Counter(),
        "effective_n_concentration_class": Counter(),
        "source_confidence_status": Counter(),
        "ambiguity_status": Counter(),
        "source_execution_class": Counter(),
        "ordering_execution_class": Counter(),
        "source_stress_status": Counter(),
        "m15_interval_status": Counter(),
        "m1_support_vs_branch_status": Counter(),
        "next_computation_class": Counter(),
        "branch_priority": Counter(),
        "branch_local_candidate_stage": Counter(),
        "metric_coverage_status": Counter(),
        "layer_match_status": Counter(),
        "action_family": Counter(),
    }

    for index, branch_id in enumerate(branch_ids, 1):
        branch = rstyle[branch_id]
        control_row = control.get(branch_id, {})
        cause_row = cause.get(branch_id, {})
        dup_row = dup.get(branch_id, {})
        impl_row = impl.get(branch_id, {})
        local_row = local.get(branch_id, {})
        code_row = code.get(branch_id, {})
        replay_row = replay.get(branch_id, {})
        source_ordering_row = source_ordering.get(branch_id, {})
        source_stress_row = source_stress.get(branch_id)
        m15_row = m15.get(branch_id)
        m1_row = m1.get(branch_id)
        exact_row = exact.get(branch_id, {})
        entry_row = entry.get(branch_id, {})
        adverse_row = adverse.get(branch_id, {})
        positive_row = positive.get(branch_id, {})
        positive_spec_row = positive_spec.get(branch_id, {})

        sealed_status = (
            replay_row.get("sealed_proxy_class")
            or (m1_row.get("sealed_or_proxy_outcome_status") if m1_row else None)
            or branch.get("branch_result_class")
        )
        expectancy_proxy = branch.get("expectancy_style_proxy") or {
            "method": branch.get("expectancy_style_proxy_method") or replay_row.get("expectancy_style_proxy_method"),
            "lower_mean": branch.get("rstyle_proxy_all_components", {}).get("rstyle_lower_mean"),
            "midpoint_mean": branch.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean"),
            "upper_mean": branch.get("rstyle_proxy_all_components", {}).get("rstyle_upper_mean"),
            "exact_missing_reason": branch.get("missing_exact_geometry_reason") or MISSING_EXACT_REASON,
        }
        cost_sensitivity = branch.get("cost_sensitivity") or {
            "cost_sensitivity_proxy_status": replay_row.get("cost_sensitivity_proxy_status")
            or code_row.get("cost_sensitivity_proxy_status"),
            "cost_robustness_bucket": branch.get("cost_robustness_bucket"),
            "source_stress_class": source_stress_row.get("branch_stress_class") if source_stress_row else None,
        }
        duplicate_effective_n = branch.get("effective_n_fields") or {
            "material_joined_rows": dup_row.get("material_joined_rows"),
            "unique_event_or_route_ids": dup_row.get("unique_event_or_route_ids"),
            "duplicate_inflation_ratio_material_rows_over_event_ids": dup_row.get(
                "duplicate_inflation_ratio_material_rows_over_event_ids"
            ),
        }
        implementation_implication = {
            "branch_priority": replay_row.get("branch_priority") or code_row.get("branch_priority"),
            "branch_local_candidate_stage": local_row.get("branch_local_candidate_stage"),
            "same_resource_execution_implication": replay_row.get("same_resource_execution_implication"),
            "primary_branch_local_surface": replay_row.get("primary_branch_local_surface"),
            "source_local_impl_class": local_row.get("source_local_impl_class"),
            "ordering_local_impl_class": local_row.get("ordering_local_impl_class"),
            "entry_local_impl_class": local_row.get("entry_local_impl_class"),
            "adverse_local_impl_class": local_row.get("adverse_local_impl_class"),
            "positive_local_impl_class": local_row.get("positive_local_impl_class"),
            "positive_replay_status": code_row.get("positive_replay_status") or positive_spec_row.get("positive_replay_status"),
            "positive_replayable_now": (
                code_row.get("positive_replayable_now")
                if code_row.get("positive_replayable_now") is not None
                else positive_spec_row.get("positive_replayable_now")
            ),
            "branch_local_next_computations": branch.get("branch_local_next_computations")
            or local_row.get("branch_local_next_computations")
            or code_row.get("branch_local_next_computations"),
        }
        source_stress_status = classify_source_stress(source_stress_row)
        m15_status = classify_m15(m15_row)
        m1_status = classify_m1(m1_row, str(branch.get("branch_result_class")))
        next_class = next_computation_class(
            source_stress=source_stress_row,
            m15=m15_row,
            m1=m1_row,
            replay=replay_row,
            local=local_row,
            code=code_row,
        )
        output_row = {
            "full_outcome_branch_id": f"OHLC-GTOS-FULL-OUTCOME-BRANCH-{index:05d}",
            "branch_queue_id": branch_id,
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "target_stop_reward_to_risk_ratio": branch.get("target_stop_reward_to_risk_ratio"),
            "sealed_or_proxy_outcome_status": sealed_status,
            "sealed_proxy_class": sealed_status,
            "branch_result_class": branch.get("branch_result_class"),
            "rstyle_lower_mean": branch.get("rstyle_proxy_all_components", {}).get("rstyle_lower_mean")
            or branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_proxy_all_components", {}).get("rstyle_midpoint_mean")
            or branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_proxy_all_components", {}).get("rstyle_upper_mean")
            or branch.get("rstyle_upper_mean"),
            "expectancy_style_proxy": expectancy_proxy,
            "expectancy_style_proxy_method": expectancy_proxy.get("method"),
            "target_stop_result": branch.get("target_stop_result"),
            "target_stop_result_counts": branch.get("target_stop_result_counts"),
            "pass_control_delta": {
                "status": control_row.get("pass_control_delta_status") or branch.get("pass_control_delta_status"),
                "same_route_peer_delta": control_row.get("same_route_peer_delta") or branch.get("same_route_peer_delta"),
                "same_route_peer_count": control_row.get("same_route_peer_count"),
                "same_symbol_session_side_targetstop_delta": control_row.get(
                    "same_symbol_session_side_targetstop_delta"
                ),
                "neighbor_directional_close_vs_permuted": control_row.get("neighbor_directional_close_vs_permuted"),
            },
            "pass_control_delta_status": control_row.get("pass_control_delta_status") or branch.get("pass_control_delta_status"),
            "cost_sensitivity": cost_sensitivity,
            "cost_sensitivity_proxy_status": replay_row.get("cost_sensitivity_proxy_status")
            or code_row.get("cost_sensitivity_proxy_status")
            or local_row.get("source_stress_action_class")
            or branch.get("cost_robustness_bucket"),
            "duplicate_effective_n": duplicate_effective_n,
            "effective_n_concentration_class": replay_row.get("effective_n_concentration_class")
            or local_row.get("effective_n_concentration_class")
            or branch.get("effective_n_concentration_class"),
            "concentration_summary": branch.get("concentration_summary"),
            "source_confidence_status": branch.get("source_confidence_status") or replay_row.get("source_confidence_status"),
            "source_execution_class": source_ordering_row.get("source_execution_class") or replay_row.get("source_execution_class"),
            "source_deep_action_class": source_ordering_row.get("source_deep_action_class"),
            "source_stress_status": source_stress_status,
            "m15_interval_status": m15_status,
            "m1_support_vs_branch_status": m1_status,
            "m1_support_resolution_class": m1_row.get("m1_support_resolution_class") if m1_row else None,
            "m1_support_interval_sign_class": m1_row.get("m1_support_interval_sign_class") if m1_row else None,
            "ambiguity_status": branch.get("ambiguity_status") or replay_row.get("ambiguity_status"),
            "ordering_execution_class": source_ordering_row.get("ordering_execution_class") or replay_row.get("ordering_execution_class"),
            "ordering_deep_action_class": source_ordering_row.get("ordering_deep_action_class"),
            "implementation_implication": implementation_implication,
            "branch_priority": implementation_implication["branch_priority"],
            "branch_local_candidate_stage": implementation_implication["branch_local_candidate_stage"],
            "branch_execution_class": replay_row.get("branch_execution_class"),
            "same_resource_execution_implication": implementation_implication["same_resource_execution_implication"],
            "primary_branch_local_surface": implementation_implication["primary_branch_local_surface"],
            "branch_local_next_computations": implementation_implication["branch_local_next_computations"],
            "next_computation_class": next_class,
            "exact_success_cause": cause_row.get("exact_success_cause") or branch.get("exact_success_cause"),
            "exact_failure_cause": cause_row.get("exact_failure_cause") or branch.get("exact_failure_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("missing_exact_geometry_reason")
            or branch.get("exact_missing_geometry_or_source_reason")
            or replay_row.get("exact_missing_geometry_or_source_reason")
            or MISSING_EXACT_REASON,
            "source_layer_presence": {
                "source_stress_acquisition": source_stress_row is not None,
                "m15_interval_collapse": m15_row is not None,
                "m1_fill_bar_interval_collapse": m1_row is not None,
                "exact_repair": bool(exact_row),
                "positive_replay_spec": bool(positive_spec_row),
            },
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        coverage, coverage_status, missing_metrics = metric_coverage(output_row)
        output_row["required_metric_coverage"] = coverage
        output_row["metric_coverage_status"] = coverage_status
        output_row["missing_required_metrics"] = missing_metrics
        branch_rows.append(output_row)

        for layer_index, (layer_name, (layer_map, scope)) in enumerate(layer_maps.items(), 1):
            layer_row = layer_map.get(branch_id)
            if layer_row:
                match_status = "MATCHED_FULL_LAYER" if scope.startswith("FULL") else "MATCHED_SUBSET_LAYER"
            elif scope.startswith("FULL"):
                match_status = "MISSING_UNEXPECTED_FULL_LAYER"
            else:
                match_status = "OUT_OF_LAYER_SCOPE"
            layer_rows.append(
                {
                    "layer_join_id": f"OHLC-GTOS-FULL-OUTCOME-LAYER-{index:05d}-{layer_index:02d}",
                    "branch_queue_id": branch_id,
                    "layer_name": layer_name,
                    "layer_scope": scope,
                    "layer_match_status": match_status,
                    "layer_excerpt": layer_excerpt(layer_row or {}),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
            bucket_counters["layer_match_status"][f"{layer_name}:{match_status}"] += 1

        new_actions = branch_action_rows(
            index=index,
            branch_id=branch_id,
            branch=branch,
            local=local_row,
            code=code_row,
            replay=replay_row,
            source_ordering=source_ordering_row,
            source_stress=source_stress_row,
            m15=m15_row,
            m1=m1_row,
            entry=entry_row,
            adverse=adverse_row,
            positive=positive_row,
            generated_at=generated_at,
            manifest_hash=manifest_hash,
        )
        action_rows.extend(new_actions)
        for action in new_actions:
            bucket_counters["action_family"][action["action_family"]] += 1

        conflict_row = {
            "conflict_id": f"OHLC-GTOS-FULL-OUTCOME-CONFLICT-{index:05d}",
            "branch_queue_id": branch_id,
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "source_stress_status": source_stress_status,
            "m15_interval_status": m15_status,
            "m1_support_vs_branch_status": m1_status,
            "pass_control_delta_status": control_row.get("pass_control_delta_status") or branch.get("pass_control_delta_status"),
            "next_computation_class": next_class,
            "conflict_interpretation": "SPLIT_OR_ROUTE_BY_LAYER_STATUS_NOT_SCALAR_SHORTCUT",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        conflict_rows.append(conflict_row)
        next_rows.append(
            {
                "next_compute_id": f"OHLC-GTOS-FULL-OUTCOME-NEXT-{index:05d}",
                "branch_queue_id": branch_id,
                "next_computation_class": next_class,
                "primary_surface": replay_row.get("primary_branch_local_surface"),
                "branch_priority": replay_row.get("branch_priority") or code_row.get("branch_priority"),
                "branch_local_candidate_stage": local_row.get("branch_local_candidate_stage"),
                "same_resource_action": implementation_implication["branch_local_next_computations"],
                "source_layer_presence": output_row["source_layer_presence"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )

        for category, value in [
            ("branch_result_class", output_row["branch_result_class"]),
            ("target_stop_result", output_row["target_stop_result"]),
            ("sealed_proxy_outcome_status", output_row["sealed_or_proxy_outcome_status"]),
            ("pass_control_delta_status", output_row["pass_control_delta_status"]),
            ("cost_sensitivity_proxy_status", output_row["cost_sensitivity_proxy_status"]),
            ("effective_n_concentration_class", output_row["effective_n_concentration_class"]),
            ("source_confidence_status", output_row["source_confidence_status"]),
            ("ambiguity_status", output_row["ambiguity_status"]),
            ("source_execution_class", output_row["source_execution_class"]),
            ("ordering_execution_class", output_row["ordering_execution_class"]),
            ("source_stress_status", source_stress_status),
            ("m15_interval_status", m15_status),
            ("m1_support_vs_branch_status", m1_status),
            ("next_computation_class", next_class),
            ("branch_priority", replay_row.get("branch_priority") or code_row.get("branch_priority")),
            ("branch_local_candidate_stage", local_row.get("branch_local_candidate_stage")),
            ("metric_coverage_status", coverage_status),
        ]:
            bucket_counters[category][str(value)] += 1

    concentration_rows = []
    for index, row in enumerate(concentration_input_rows, 1):
        concentration_rows.append(
            {
                "full_outcome_concentration_id": f"OHLC-GTOS-FULL-OUTCOME-CONC-{index:04d}",
                **row,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-FULL-OUTCOME-BUCKET-{len(bucket_rows) + 1:05d}",
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
        {
            "question_id": "OHLC-GTOS-FULL-OUTCOME-QUESTION-001",
            "question": "Which branches remain positive only after source/ordering interval context is preserved?",
            "answer_route": "Use branch ledger plus source_stress_status, m15_interval_status, and m1_support_vs_branch_status.",
        },
        {
            "question_id": "OHLC-GTOS-FULL-OUTCOME-QUESTION-002",
            "question": "Which all-positive M1 support branches are contradicted by broader branch aggregate evidence?",
            "answer_route": "Use the conflict ledger m1_support_vs_branch_status without top-N truncation.",
        },
        {
            "question_id": "OHLC-GTOS-FULL-OUTCOME-QUESTION-003",
            "question": "Which M15 interval branches become challenger, avoid/redesign, or interval-router candidates?",
            "answer_route": "Use next_compute ledger classes for every M15 interval branch.",
        },
        {
            "question_id": "OHLC-GTOS-FULL-OUTCOME-QUESTION-004",
            "question": "Which source-stress branches need risk-router/source-acquisition before scalar comparison?",
            "answer_route": "Use source_stress_status and next_computation_class across all branches.",
        },
        {
            "question_id": "OHLC-GTOS-FULL-OUTCOME-QUESTION-005",
            "question": "Which branches have every requested per-branch metric present versus a true schema gap?",
            "answer_route": "Use required_metric_coverage and missing_required_metrics in the branch ledger.",
        },
        {
            "question_id": "OHLC-GTOS-FULL-OUTCOME-QUESTION-006",
            "question": "Which action family should be implemented or replayed first for each branch?",
            "answer_route": "Use the action matrix and next_compute ledgers; preserve all five action families per branch.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "not_completion": True,
                "source_manifest_hash": manifest_hash,
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_rstyle_branch_rows": len(rstyle_rows),
            "input_control_delta_rows": len(control),
            "input_cause_rows": len(cause),
            "input_duplicate_effective_n_rows": len(dup),
            "input_implementation_branch_rows": len(impl),
            "input_local_branch_rows": len(local),
            "input_code_branch_rows": len(code),
            "input_replay_branch_rows": len(replay),
            "input_source_ordering_rows": len(source_ordering),
            "input_source_stress_branch_rows": len(source_stress),
            "input_m15_interval_branch_rows": len(m15),
            "input_m1_fill_interval_branch_rows": len(m1),
            "branch_synthesis_rows": len(branch_rows),
            "layer_join_rows": len(layer_rows),
            "action_matrix_rows": len(action_rows),
            "conflict_rows": len(conflict_rows),
            "next_compute_rows": len(next_rows),
            "concentration_rows": len(concentration_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branches_with_all_required_metrics": sum(
                1 for row in branch_rows if row["metric_coverage_status"] == "ALL_REQUIRED_BRANCH_METRICS_PRESENT"
            ),
            "branches_missing_required_metrics": sum(
                1 for row in branch_rows if row["metric_coverage_status"] != "ALL_REQUIRED_BRANCH_METRICS_PRESENT"
            ),
            "layer_count_per_branch": len(layer_maps),
            "action_family_count_per_branch": 5,
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, output_rows in [
        (BRANCH_LEDGER, branch_rows),
        (LAYER_JOIN_LEDGER, layer_rows),
        (ACTION_MATRIX_LEDGER, action_rows),
        (CONFLICT_LEDGER, conflict_rows),
        (NEXT_COMPUTE_LEDGER, next_rows),
        (CONCENTRATION_LEDGER, concentration_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_rows),
    ]:
        write_jsonl(path, output_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
