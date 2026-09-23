#!/usr/bin/env python3
"""Build a full branch cause-to-implementation action matrix from R-style proxies."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

BRANCH_OUTCOME_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
CONTROL_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONTROL_DELTA_LEDGER_2026-05-16.jsonl"
CAUSE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CAUSE_LEDGER_2026-05-16.jsonl"
CONCENTRATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONCENTRATION_LEDGER_2026-05-16.jsonl"
BRANCH_PROXY_IMPLEMENTATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_IMPLEMENTATION_IMPLICATION_LEDGER_2026-05-16.jsonl"
BRANCH_PROXY_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_ACTION_SCORE_LEDGER_2026-05-16.jsonl"
BRANCH_EFFECTIVE_N_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_RESULT_2026-05-16.json"
BRANCH_MATRIX_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_BRANCH_LEDGER_2026-05-16.jsonl"
ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_ACTION_LEDGER_2026-05-16.jsonl"
SOURCE_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_SOURCE_REPAIR_LEDGER_2026-05-16.jsonl"
AMBIGUITY_COLLAPSE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_AMBIGUITY_COLLAPSE_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_CANDIDATE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
UPSTREAM_IMPLEMENTATION_EXPLODED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_UPSTREAM_IMPLEMENTATION_EXPLODED_LEDGER_2026-05-16.jsonl"
UPSTREAM_ACTION_SCORE_EXPLODED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_UPSTREAM_ACTION_SCORE_EXPLODED_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay branch cause-to-implementation action matrix only. "
    "Rows consume the R-style proxy outcome layer and preserve all 386 branches while "
    "mapping mechanically available proxy outcomes, controls, cost/source/ambiguity "
    "causes, duplicate/effective-N, concentration, and implementation implications "
    "to next same-resource actions. Exact broker R/PnL, strategy expectancy, win-rate, "
    "validation, live-readiness, promotion, and live behavior change are not claimed."
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
        BRANCH_OUTCOME_PATH,
        CONTROL_DELTA_PATH,
        CAUSE_PATH,
        CONCENTRATION_PATH,
        BRANCH_PROXY_IMPLEMENTATION_PATH,
        BRANCH_PROXY_ACTION_PATH,
        BRANCH_EFFECTIVE_N_PATH,
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


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sign_bucket(value: Any, pos_label: str, neg_label: str, zero_label: str, missing_label: str) -> str:
    number = to_float(value)
    if number is None:
        return missing_label
    if number > 0:
        return pos_label
    if number < 0:
        return neg_label
    return zero_label


def classify_result(row: dict[str, Any]) -> str:
    result_class = row.get("branch_result_class")
    target_stop = row.get("target_stop_result")
    source_status = row.get("source_confidence_status")
    ambiguity_status = row.get("ambiguity_status")
    if result_class == "NO_RSTYLE_PROXY_INTERVAL_AVAILABLE" or target_stop == "NO_TARGET_STOP_RESULT_ENTRY_PROVENANCE_ONLY":
        return "ENTRY_PROVENANCE_BINDING_OR_SOURCE_SCOPE_ONLY"
    if result_class == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
        return "ORDERING_OR_INTERVAL_COLLAPSE_BEFORE_DIRECTIONAL_USE"
    if result_class == "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        if source_status == "EXACT_SOURCE_SUPPORTED_NO_COMPONENT_SOURCE_STRESS" and ambiguity_status == "NO_ORDERING_AMBIGUITY_RECORDED":
            return "POSITIVE_PROXY_EXACT_SOURCE_LOW_AMBIGUITY_CHALLENGER_CANDIDATE"
        return "POSITIVE_PROXY_WITH_REPAIR_OR_STRESS_BEFORE_CHALLENGER"
    if result_class == "NEGATIVE_RSTYLE_PROXY_MIDPOINT":
        if target_stop == "STOP_FIRST_PROXY_DOMINANT":
            return "NEGATIVE_STOP_FIRST_AVOID_OR_REDESIGN_CANDIDATE"
        return "NEGATIVE_PROXY_FAILURE_DIAGNOSIS_QUEUE"
    return "UNCLASSIFIED_PROXY_RESULT_REVIEW_REQUIRED"


def classify_fillability(row: dict[str, Any]) -> tuple[str, list[str]]:
    bucket = row.get("fillability_bucket")
    if bucket == "NEAR_MISS_ENTRY_CHALLENGER_AVAILABLE":
        return "NEAR_MISS_MARKET_OR_OFFSET_CHALLENGER_BUILD", [
            "Build and compare signal-close, next-open, exact-spread-offset, and closest-approach entry variants."
        ]
    if bucket == "FAR_OR_WITHIN_RANGE_NOFILL_REDESIGN_AVAILABLE":
        return "FAR_WITHIN_NOFILL_AVOID_RETEST_REDESIGN_BUILD", [
            "Split far misses into avoid-filter predicates and within-range misses into retest redesign variants."
        ]
    if bucket == "MIXED_OR_DESCRIPTOR_ONLY_FILLABILITY":
        return "MIXED_FILLABILITY_SOURCE_SPLIT_REQUIRED", [
            "Separate no-fill, recovered-fill, M1 spread-adjusted, and descriptor-only rows before implementation."
        ]
    if bucket == "PATH_PROXY_FAVORABLE_EVIDENCE_DOMINANT":
        return "FILLABILITY_NOT_PRIMARY_BLOCKER_PRESERVE_PATH_SIGNAL", [
            "Preserve path evidence and route remaining actions through source/ambiguity/cost controls."
        ]
    if bucket == "REPAIR_ONLY_FILLABILITY_SCOPE":
        return "REPAIR_ENTRY_SCOPE_ONLY_BINDING_PRESERVED", [
            "Keep row as entry-provenance scope and use bound signature-scope contracts for path questions."
        ]
    return "FILLABILITY_BUCKET_REVIEW_REQUIRED", ["Review missing or new fillability bucket."]


def classify_source(row: dict[str, Any]) -> tuple[str, list[str]]:
    status = row.get("source_confidence_status")
    cost_bucket = row.get("cost_robustness_bucket")
    tags = set(row.get("cause_tags") or [])
    if status == "EXACT_SOURCE_SUPPORTED_NO_COMPONENT_SOURCE_STRESS":
        return "NO_SOURCE_REPAIR_NEEDED_FOR_CURRENT_PROXY", ["Use exact-supported proxy rows; source repair is not primary."]
    if status == "ENTRY_PROVENANCE_ONLY_BOUND_BY_SIGNATURE_SCOPE":
        return "ENTRY_PROVENANCE_BOUND_TO_SIGNATURE_SCOPE", [
            "Do not coerce to one target/stop result; keep the signature-scope target/stop candidates."
        ]
    if "COST_SENSITIVITY_EXACT_SPREAD_SOURCE_STRESS" in tags or cost_bucket == "EXACT_SPREAD_SOURCE_STRESS":
        return "EXACT_SPREAD_SOURCE_REPAIR_OR_LOW_HIGH_STRESS", [
            "Search owned tick/depth/source-date routes; if absent, preserve low/high exact-spread stress interval."
        ]
    if cost_bucket == "EXACT_SPREAD_SUPRA_STATIC_STRESS":
        return "SUPRA_STATIC_SPREAD_MODEL_STRESS", [
            "Treat exact spread above static proxy as an execution-friction stress branch and compare alternatives."
        ]
    if cost_bucket == "SPREAD_PROXY_GRADIENT_SENSITIVE":
        return "SPREAD_PROXY_GRADIENT_SENSITIVITY_RECOMPUTE", [
            "Recompute descriptor/action under zero, median, max, static, and exact/proxy spread variants."
        ]
    if cost_bucket == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT":
        return "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_SPLIT", [
            "Keep zero-cost control separate from spread-adjusted path; do not mix the descriptors."
        ]
    return "PROXY_SOURCE_LIMIT_REPAIR_QUEUE", [
        "Map the branch to source acquisition, exact reconstruction, or fail-closed proxy stress."
    ]


def source_repairability_class(row: dict[str, Any]) -> str:
    if row.get("path_scope_bucket") == "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT" or row.get("target_stop_contract_id") == "TARGETSTOP_NA_NA":
        return "ENTRY_PROVENANCE_ONLY_BOUND"
    if row.get("source_confidence_status") == "EXACT_SOURCE_SUPPORTED_NO_COMPONENT_SOURCE_STRESS":
        return "EXACT_SOURCE_CLEAN"
    if row.get("source_confidence_status") == "SOURCE_STRESS_OR_PROXY_PRESENT":
        return "SOURCE_REPAIR_OR_PROXY_REQUIRED"
    return "MIXED_OR_UNSPECIFIED_SOURCE"


def exact_spread_repairability_class(row: dict[str, Any]) -> str:
    cost_sensitivity = row.get("cost_sensitivity") or {}
    recomputed = cost_sensitivity.get("exact_spread_recomputed_component") or {}
    unavailable = cost_sensitivity.get("exact_spread_unavailable_component") or {}
    if int(recomputed.get("rows") or 0) > 0:
        return "EXACT_SPREAD_RECOMPUTED"
    if int(unavailable.get("rows") or 0) > 0:
        return "EXACT_SPREAD_UNAVAILABLE_STRESS_PAIR"
    bucket = row.get("cost_robustness_bucket")
    if bucket == "EXACT_SPREAD_SUPRA_STATIC_STRESS":
        return "EXACT_SPREAD_SUPRA_STATIC_STRESS"
    if bucket == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT":
        return "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT"
    if bucket == "SPREAD_PROXY_GRADIENT_SENSITIVE":
        return "SPREAD_PROXY_GRADIENT_SENSITIVE"
    if bucket == "COST_DESCRIPTOR_INVARIANT_OR_ABSENT":
        return "COST_INVARIANT_OR_ABSENT"
    if bucket == "EXACT_SPREAD_SOURCE_STRESS":
        return "EXACT_SPREAD_UNAVAILABLE_STRESS_PAIR"
    return "EXACT_SPREAD_REPAIRABILITY_REVIEW_REQUIRED"


def ordering_collapse_route(row: dict[str, Any]) -> str:
    if row.get("ambiguity_status") == "NO_RSTYLE_INTERVAL_ROWS":
        return "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY"
    if row.get("ambiguity_status") == "NO_ORDERING_AMBIGUITY_RECORDED":
        return "NO_ORDERING_COLLAPSE_REQUIRED"
    components = row.get("rstyle_proxy_component_breakdown") or {}
    all_components = row.get("rstyle_proxy_all_components") or {}
    status_text = json.dumps(all_components.get("status_counts", {}), sort_keys=True)
    if "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS" in status_text:
        route = "ATTEMPT_M1_CHRONOLOGICAL_COLLAPSE"
    else:
        route = "ORDERING_INTERVAL_BOUNDS_PRESERVED"
    fill_bar_status = json.dumps(
        {
            key: (components.get(key) or {}).get("status_counts", {})
            for key in ("m1_fill_bar_conservative_stress", "m1_fill_bar_optimistic_stress", "recovered_unfilled_path")
        },
        sort_keys=True,
    )
    if "ORDER_UNRESOLVED" in fill_bar_status or "FILL_BAR" in fill_bar_status:
        return "M1_FILL_BAR_STRESS_OR_TICK_ORDERING_ROUTE"
    if int(all_components.get("ambiguous_ordering_rows") or 0) > 0:
        return route
    return "AMBIGUITY_STATUS_WITH_NO_COMPONENT_AMBIGUITY_REVIEW"


def rstyle_proxy_action(row: dict[str, Any]) -> dict[str, Any]:
    ratio = row.get("target_stop_reward_to_risk_ratio")
    target_stop = row.get("target_stop_result")
    expectancy = row.get("expectancy_style_proxy") or {}
    if target_stop == "TARGET_FIRST_PROXY_DOMINANT":
        interval_class = "TARGET_FIRST_DOMINANT_POINT_PROXY_COMPONENTS_PRESENT"
    elif target_stop == "STOP_FIRST_PROXY_DOMINANT":
        interval_class = "STOP_FIRST_DOMINANT_POINT_PROXY_COMPONENTS_PRESENT"
    elif target_stop in {"ORDERING_AMBIGUITY_DOMINANT"} or row.get("branch_result_class") == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
        interval_class = "ORDERING_INTERVAL_PROXY_BOUNDS_REQUIRED"
    elif target_stop == "NO_FILL_OR_UNFILLED_DOMINANT":
        interval_class = "NO_FILL_NO_TRADE_ZERO_PROXY_COMPONENTS_PRESENT"
    elif target_stop == "NO_TARGET_STOP_RESULT_ENTRY_PROVENANCE_ONLY":
        interval_class = "NO_INTERVAL_ENTRY_PROVENANCE_ONLY"
    elif target_stop == "NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT":
        interval_class = "FILLED_NO_TARGET_STOP_LOWER_LEVEL_CLOSE_UNITS_PROXY"
    else:
        interval_class = "RSTYLE_PROXY_ACTION_REVIEW_REQUIRED"
    return {
        "rstyle_proxy_action_class": interval_class,
        "target_stop_reward_to_risk_ratio": ratio,
        "lower_mean": expectancy.get("lower_mean"),
        "midpoint_mean": expectancy.get("midpoint_mean"),
        "upper_mean": expectancy.get("upper_mean"),
        "interval_rows": expectancy.get("interval_rows"),
        "method": expectancy.get("method"),
        "exact_missing_reason": expectancy.get("exact_missing_reason"),
    }


def classify_ambiguity(row: dict[str, Any]) -> tuple[str, list[str]]:
    status = row.get("ambiguity_status")
    components = row.get("rstyle_proxy_component_breakdown") or {}
    all_components = row.get("rstyle_proxy_all_components") or {}
    ambiguous_rows = int(all_components.get("ambiguous_ordering_rows") or 0)
    m1_rows = 0
    for key in ("m1_spread_adjusted_replay", "m1_fill_bar_conservative_stress", "m1_fill_bar_optimistic_stress"):
        m1_rows += int((components.get(key) or {}).get("rows") or 0)
    if status == "NO_RSTYLE_INTERVAL_ROWS":
        return "NO_INTERVAL_ROWS_BINDING_OR_ENTRY_SCOPE_ONLY", [
            "Use target/stop binding repair and keep original row out of single-result path scoring."
        ]
    if status == "NO_ORDERING_AMBIGUITY_RECORDED":
        return "NO_ORDERING_COLLAPSE_NEEDED", ["Route next action through source, cost, fillability, or control deltas."]
    if status == "HIGH_ORDERING_AMBIGUITY":
        if m1_rows:
            return "M1_STRESS_ALREADY_PARTIAL_COLLAPSE_REMAINING_INTERVALS", [
                "Use existing M1 stress rows, then isolate remaining same-M15/order-unresolved intervals."
            ]
        return "LOWER_TIMEFRAME_OR_TICK_ORDERING_COLLAPSE_REQUIRED", [
            "Attempt tick/M1 ordering reconstruction; preserve interval bounds when current source cannot order."
        ]
    if status == "SOME_ORDERING_AMBIGUITY":
        if ambiguous_rows:
            return "PARTIAL_ORDERING_INTERVAL_STRESS_PRESERVED", [
                "Split ordered rows from interval rows and keep the interval contribution explicit."
            ]
        return "AMBIGUITY_STATUS_WITH_ZERO_AMBIGUOUS_ROWS_REVIEW", ["Review status/counter mismatch."]
    return "AMBIGUITY_BUCKET_REVIEW_REQUIRED", ["Review missing or new ambiguity status."]


def classify_effective_n(row: dict[str, Any]) -> str:
    fields = row.get("effective_n_fields") or {}
    unique_events = int(fields.get("unique_event_or_route_ids") or 0)
    duplicate_ratio = to_float(fields.get("duplicate_inflation_ratio_material_rows_over_event_ids")) or 0.0
    concentration = row.get("concentration_summary") or {}
    symbol_share = to_float((concentration.get("symbol") or {}).get("branch_share")) or 0.0
    route_share = to_float((concentration.get("route_candidate_id") or {}).get("branch_share")) or 0.0
    if unique_events == 0:
        return "NO_EFFECTIVE_N_PROXY_AVAILABLE"
    if unique_events < 20:
        return "UNDERPOWERED_EFFECTIVE_N_LT_20"
    if duplicate_ratio >= 4.0:
        return "DUPLICATE_INFLATION_HIGH_MATERIAL_ROWS_OVER_EVENTS"
    if symbol_share >= 0.8 or route_share >= 0.16:
        return "CONCENTRATION_HIGH_SYMBOL_OR_ROUTE_SHARE"
    return "EFFECTIVE_N_AND_CONCENTRATION_ACCEPTABLE_FOR_NEXT_PROXY_COMPARISON"


def derive_actions(row: dict[str, Any], control: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    result_action = classify_result(row)
    actions.append(
        {
            "action_class": result_action,
            "action_family": "OUTCOME_PROXY",
            "mechanical_next_step": "Use branch result class, target/stop result, and interval bounds to route next branch work.",
        }
    )

    fillability_action, fillability_steps = classify_fillability(row)
    for step in fillability_steps:
        actions.append({"action_class": fillability_action, "action_family": "FILLABILITY", "mechanical_next_step": step})

    source_action, source_steps = classify_source(row)
    for step in source_steps:
        actions.append({"action_class": source_action, "action_family": "SOURCE_COST", "mechanical_next_step": step})

    ambiguity_action, ambiguity_steps = classify_ambiguity(row)
    for step in ambiguity_steps:
        actions.append({"action_class": ambiguity_action, "action_family": "AMBIGUITY", "mechanical_next_step": step})

    effective_n_action = classify_effective_n(row)
    actions.append(
        {
            "action_class": effective_n_action,
            "action_family": "DUPLICATE_EFFECTIVE_N_CONCENTRATION",
            "mechanical_next_step": "Carry effective-N and concentration bucket into any branch comparison or challenger grouping.",
        }
    )

    delta_status = str((control or {}).get("pass_control_delta_status") or "CONTROL_DELTA_MISSING")
    route_delta = sign_bucket(
        (control or {}).get("same_route_peer_delta"),
        "BRANCH_PROXY_ABOVE_SAME_ROUTE_PEER_MEAN",
        "BRANCH_PROXY_BELOW_SAME_ROUTE_PEER_MEAN",
        "BRANCH_PROXY_EQUALS_SAME_ROUTE_PEER_MEAN",
        "SAME_ROUTE_PEER_DELTA_MISSING",
    )
    actions.append(
        {
            "action_class": route_delta,
            "action_family": "PASS_CONTROL_DELTA",
            "mechanical_next_step": f"Preserve control status {delta_status} and compare only within matching route/source scopes.",
        }
    )

    for tag in sorted(set(row.get("system_implication_tags") or [])):
        if tag in {"BASELINE_FAMILY_DESCRIPTOR_PRESERVED", "ACTIVE_M1_SPREAD_REPLAY_SYNTHESIS_REQUIRED"}:
            continue
        actions.append(
            {
                "action_class": str(tag),
                "action_family": "UPSTREAM_IMPLEMENTATION_TAG",
                "mechanical_next_step": "Carry upstream implementation implication into the concrete branch action ledger.",
            }
        )

    deduped = []
    seen = set()
    for action in actions:
        key = (action["action_family"], action["action_class"], action["mechanical_next_step"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(action)
    return deduped


def action_priority(row: dict[str, Any], actions: list[dict[str, str]]) -> str:
    classes = {a["action_class"] for a in actions}
    if "ENTRY_PROVENANCE_BINDING_OR_SOURCE_SCOPE_ONLY" in classes:
        return "BINDING_SCOPE_ONLY_THEN_SIGNATURE_CONTRACT_ANALYSIS"
    if "LOWER_TIMEFRAME_OR_TICK_ORDERING_COLLAPSE_REQUIRED" in classes or "M1_STRESS_ALREADY_PARTIAL_COLLAPSE_REMAINING_INTERVALS" in classes:
        return "AMBIGUITY_COLLAPSE_FIRST"
    if "EXACT_SPREAD_SOURCE_REPAIR_OR_LOW_HIGH_STRESS" in classes:
        return "SOURCE_REPAIR_OR_STRESS_FIRST"
    if "FAR_WITHIN_NOFILL_AVOID_RETEST_REDESIGN_BUILD" in classes or "NEAR_MISS_MARKET_OR_OFFSET_CHALLENGER_BUILD" in classes:
        return "ENTRY_GEOMETRY_CHALLENGER_OR_REDESIGN_FIRST"
    if classify_result(row).startswith("POSITIVE_PROXY"):
        return "CHALLENGER_COMPARISON_AFTER_REPAIR_FLAGS"
    if classify_result(row).startswith("NEGATIVE"):
        return "FAILURE_TO_AVOID_OR_REDESIGN_FIRST"
    return "PRESERVE_AND_ROUTE_BY_BUCKET"


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifact_paths = [
        RESULT_PATH,
        BRANCH_MATRIX_PATH,
        ACTION_PATH,
        SOURCE_REPAIR_PATH,
        AMBIGUITY_COLLAPSE_PATH,
        IMPLEMENTATION_CANDIDATE_PATH,
        UPSTREAM_IMPLEMENTATION_EXPLODED_PATH,
        UPSTREAM_ACTION_SCORE_EXPLODED_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    artifact_names = {path.name for path in artifact_paths}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in [
        (RESULT_PATH, "result"),
        (BRANCH_MATRIX_PATH, "branch_action_matrix_ledger"),
        (ACTION_PATH, "action_ledger"),
        (SOURCE_REPAIR_PATH, "source_repair_ledger"),
        (AMBIGUITY_COLLAPSE_PATH, "ambiguity_collapse_ledger"),
        (IMPLEMENTATION_CANDIDATE_PATH, "implementation_candidate_ledger"),
        (UPSTREAM_IMPLEMENTATION_EXPLODED_PATH, "upstream_implementation_exploded_ledger"),
        (UPSTREAM_ACTION_SCORE_EXPLODED_PATH, "upstream_action_score_exploded_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_cause_implementation_matrix",
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
        (Path(__file__).resolve(), "branch_cause_implementation_matrix_builder"),
        (RESULT_PATH, "branch_cause_implementation_matrix_result"),
        (BRANCH_MATRIX_PATH, "branch_cause_implementation_matrix_branch_ledger"),
        (ACTION_PATH, "branch_cause_implementation_matrix_action_ledger"),
        (SOURCE_REPAIR_PATH, "branch_cause_implementation_matrix_source_repair_ledger"),
        (AMBIGUITY_COLLAPSE_PATH, "branch_cause_implementation_matrix_ambiguity_collapse_ledger"),
        (IMPLEMENTATION_CANDIDATE_PATH, "branch_cause_implementation_matrix_implementation_candidate_ledger"),
        (UPSTREAM_IMPLEMENTATION_EXPLODED_PATH, "branch_cause_implementation_matrix_upstream_implementation_exploded_ledger"),
        (UPSTREAM_ACTION_SCORE_EXPLODED_PATH, "branch_cause_implementation_matrix_upstream_action_score_exploded_ledger"),
        (BUCKET_PATH, "branch_cause_implementation_matrix_bucket_ledger"),
        (QUESTION_PATH, "branch_cause_implementation_matrix_question_ledger"),
        (SUMMARY_PATH, "branch_cause_implementation_matrix_summary"),
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
        "route": "historical_ohlc_gtos_replay_branch_cause_implementation_matrix",
        "artifact": RESULT_PATH.name,
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    counts = result["counts"]
    lines = [
        "# Historical OHLC GTOS Branch Cause-To-Implementation Matrix",
        "",
        f"Generated UTC: {result['generated_utc']}",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
        f"- Branch matrix rows: {counts['branch_matrix_rows']}",
        f"- Action rows: {counts['action_rows']}",
        f"- Source repair rows: {counts['source_repair_rows']}",
        f"- Ambiguity collapse rows: {counts['ambiguity_collapse_rows']}",
        f"- Implementation candidate rows: {counts['implementation_candidate_rows']}",
        f"- Upstream implementation exploded rows: {counts['upstream_implementation_exploded_rows']}",
        f"- Upstream action score exploded rows: {counts['upstream_action_score_exploded_rows']}",
        f"- Bucket rows: {counts['bucket_rows']}",
        f"- Question rows: {counts['question_rows']}",
        "",
        "## Action Priority Distribution",
        "",
    ]
    for bucket, count in sorted(result["bucket_distributions"]["primary_action_priority"].items()):
        lines.append(f"- {bucket}: {count}")
    lines.extend(
        [
            "",
            "## Continuation",
            "",
            "The matrix preserves every branch and routes each to concrete same-resource work. The next layer should materialize the largest action families into branch-local challenger/redesign/source-repair packets without dropping any rows.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()

    branch_rows = rows(BRANCH_OUTCOME_PATH)
    control_by_branch = {row.get("branch_queue_id"): row for row in rows(CONTROL_DELTA_PATH)}
    cause_by_branch = {row.get("branch_queue_id"): row for row in rows(CAUSE_PATH)}
    impl_rows_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    upstream_impl_rows = rows(BRANCH_PROXY_IMPLEMENTATION_PATH)
    for row in upstream_impl_rows:
        impl_rows_by_branch[str(row.get("branch_queue_id"))].append(row)
    upstream_action_score_rows = rows(BRANCH_PROXY_ACTION_PATH)
    action_score_rows_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in upstream_action_score_rows:
        action_score_rows_by_branch[str(row.get("branch_queue_id"))].append(row)

    concentration_rows = rows(CONCENTRATION_PATH)
    concentration_counts = Counter(f"{row.get('group_type')}:{row.get('group_key')}" for row in concentration_rows)

    matrix_rows: list[dict[str, Any]] = []
    action_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    ambiguity_rows: list[dict[str, Any]] = []
    implementation_rows: list[dict[str, Any]] = []
    upstream_impl_exploded_rows: list[dict[str, Any]] = []
    upstream_action_exploded_rows: list[dict[str, Any]] = []

    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)

    for index, branch in enumerate(branch_rows, 1):
        branch_id = str(branch.get("branch_queue_id"))
        control = control_by_branch.get(branch_id, {})
        cause = cause_by_branch.get(branch_id, {})
        actions = derive_actions(branch, control)
        priority = action_priority(branch, actions)
        result_action = classify_result(branch)
        fillability_action, _ = classify_fillability(branch)
        source_action, _ = classify_source(branch)
        ambiguity_action, _ = classify_ambiguity(branch)
        effective_n_action = classify_effective_n(branch)
        source_repairability = source_repairability_class(branch)
        exact_spread_repairability = exact_spread_repairability_class(branch)
        ordering_route = ordering_collapse_route(branch)
        rstyle_action = rstyle_proxy_action(branch)
        route_delta = sign_bucket(
            control.get("same_route_peer_delta"),
            "BRANCH_PROXY_ABOVE_SAME_ROUTE_PEER_MEAN",
            "BRANCH_PROXY_BELOW_SAME_ROUTE_PEER_MEAN",
            "BRANCH_PROXY_EQUALS_SAME_ROUTE_PEER_MEAN",
            "SAME_ROUTE_PEER_DELTA_MISSING",
        )

        action_classes = [action["action_class"] for action in actions]
        bucket_counters["primary_action_priority"][priority] += 1
        bucket_counters["outcome_action_class"][result_action] += 1
        bucket_counters["fillability_action_class"][fillability_action] += 1
        bucket_counters["source_repair_class"][source_action] += 1
        bucket_counters["ambiguity_collapse_class"][ambiguity_action] += 1
        bucket_counters["source_repairability_class"][source_repairability] += 1
        bucket_counters["exact_spread_repairability_class"][exact_spread_repairability] += 1
        bucket_counters["ordering_collapse_route"][ordering_route] += 1
        bucket_counters["rstyle_proxy_action_class"][rstyle_action["rstyle_proxy_action_class"]] += 1
        bucket_counters["effective_n_concentration_class"][effective_n_action] += 1
        bucket_counters["same_route_control_delta_class"][route_delta] += 1
        bucket_counters["target_stop_result"][str(branch.get("target_stop_result"))] += 1
        bucket_counters["branch_result_class"][str(branch.get("branch_result_class"))] += 1

        expectancy = branch.get("expectancy_style_proxy") or {}
        all_components = branch.get("rstyle_proxy_all_components") or {}
        concentration_summary = branch.get("concentration_summary") or {}
        effective_n = branch.get("effective_n_fields") or {}

        matrix = {
            "matrix_id": f"OHLC-GTOS-BRANCH-CAUSE-IMPLEMENTATION-MATRIX-{index:05d}",
            "branch_queue_id": branch_id,
            "branch_proxy_score_id": branch.get("branch_proxy_score_id"),
            "branch_rstyle_proxy_outcome_id": branch.get("branch_rstyle_proxy_outcome_id"),
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "target_stop_reward_to_risk_ratio": branch.get("target_stop_reward_to_risk_ratio"),
            "sealed_or_proxy_outcome_status": "PROXY_RSTYLE_OUTCOME_COMPUTED_OR_ENTRY_SCOPE_BOUND",
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "rstyle_lower_mean": expectancy.get("lower_mean"),
            "rstyle_midpoint_mean": expectancy.get("midpoint_mean"),
            "rstyle_upper_mean": expectancy.get("upper_mean"),
            "rstyle_interval_rows": expectancy.get("interval_rows"),
            "rstyle_component_rows": all_components.get("rows"),
            "target_first_rows": all_components.get("target_first_rows"),
            "stop_first_rows": all_components.get("stop_first_rows"),
            "ambiguous_ordering_rows": all_components.get("ambiguous_ordering_rows"),
            "no_fill_or_unfilled_rows": all_components.get("no_fill_or_unfilled_rows"),
            "expectancy_style_proxy_method": expectancy.get("method"),
            "exact_missing_geometry_reason": branch.get("missing_exact_geometry_reason"),
            "pass_control_delta_status": control.get("pass_control_delta_status"),
            "same_route_peer_delta": control.get("same_route_peer_delta"),
            "same_route_peer_count": control.get("same_route_peer_count"),
            "same_symbol_session_side_targetstop_delta": control.get("same_symbol_session_side_targetstop_delta"),
            "neighbor_directional_close_vs_permuted": control.get("neighbor_directional_close_vs_permuted"),
            "cost_robustness_bucket": branch.get("cost_robustness_bucket"),
            "fillability_bucket": branch.get("fillability_bucket"),
            "source_confidence_status": branch.get("source_confidence_status"),
            "ambiguity_status": branch.get("ambiguity_status"),
            "effective_n_class": effective_n_action,
            "effective_n_concentration_class": effective_n_action,
            "unique_event_or_route_ids": effective_n.get("unique_event_or_route_ids"),
            "material_joined_rows": effective_n.get("material_joined_rows"),
            "duplicate_inflation_ratio_material_rows_over_event_ids": effective_n.get(
                "duplicate_inflation_ratio_material_rows_over_event_ids"
            ),
            "concentration_summary": concentration_summary,
            "exact_failure_cause": cause.get("exact_failure_cause", branch.get("exact_failure_cause")),
            "exact_success_cause": cause.get("exact_success_cause", branch.get("exact_success_cause")),
            "cause_tags": branch.get("cause_tags") or cause.get("cause_tags") or [],
            "primary_action_priority": priority,
            "outcome_action_class": result_action,
            "source_repairability_class": source_repairability,
            "exact_spread_repairability_class": exact_spread_repairability,
            "ordering_collapse_route": ordering_route,
            "rstyle_proxy_action": rstyle_action,
            "rstyle_proxy_action_class": rstyle_action["rstyle_proxy_action_class"],
            "fillability_action_class": fillability_action,
            "source_repair_class": source_action,
            "ambiguity_collapse_class": ambiguity_action,
            "same_route_control_delta_class": route_delta,
            "action_classes": action_classes,
            "upstream_implementation_implication_count": len(impl_rows_by_branch.get(branch_id, [])),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX",
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        matrix_rows.append(matrix)

        source_rows.append(
            {
                "source_repair_id": f"OHLC-GTOS-BRANCH-CAUSE-SOURCE-REPAIR-{index:05d}",
                "branch_queue_id": branch_id,
                "route_candidate_id": branch.get("route_candidate_id"),
                "source_confidence_status": branch.get("source_confidence_status"),
                "cost_robustness_bucket": branch.get("cost_robustness_bucket"),
                "source_repair_class": source_action,
                "source_repairability_class": source_repairability,
                "exact_spread_repairability_class": exact_spread_repairability,
                "source_repair_mechanical_next_step": next(
                    (a["mechanical_next_step"] for a in actions if a["action_family"] == "SOURCE_COST"),
                    "Review source status.",
                ),
                "exact_missing_geometry_reason": branch.get("missing_exact_geometry_reason"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
        ambiguity_rows.append(
            {
                "ambiguity_collapse_id": f"OHLC-GTOS-BRANCH-CAUSE-AMBIGUITY-{index:05d}",
                "branch_queue_id": branch_id,
                "route_candidate_id": branch.get("route_candidate_id"),
                "ambiguity_status": branch.get("ambiguity_status"),
                "ambiguity_collapse_class": ambiguity_action,
                "ordering_collapse_route": ordering_route,
                "ambiguous_ordering_rows": all_components.get("ambiguous_ordering_rows"),
                "rstyle_interval_rows": expectancy.get("interval_rows"),
                "target_stop_result": branch.get("target_stop_result"),
                "mechanical_next_step": next(
                    (a["mechanical_next_step"] for a in actions if a["action_family"] == "AMBIGUITY"),
                    "Review ambiguity status.",
                ),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
        implementation_rows.append(
            {
                "implementation_candidate_id": f"OHLC-GTOS-BRANCH-CAUSE-IMPLEMENTATION-CANDIDATE-{index:05d}",
                "branch_queue_id": branch_id,
                "route_candidate_id": branch.get("route_candidate_id"),
                "primary_action_priority": priority,
                "outcome_action_class": result_action,
                "fillability_action_class": fillability_action,
                "source_repair_class": source_action,
                "source_repairability_class": source_repairability,
                "exact_spread_repairability_class": exact_spread_repairability,
                "ambiguity_collapse_class": ambiguity_action,
                "ordering_collapse_route": ordering_route,
                "exact_failure_cause": matrix["exact_failure_cause"],
                "exact_success_cause": matrix["exact_success_cause"],
                "implementation_candidate_status": (
                    "IMPLEMENTATION_REPAIR_OR_CHALLENGER_ACTION_MAPPED_FULL_DENOMINATOR"
                ),
                "branch_local_code_surface_hint": branch_local_surface_hint(priority, fillability_action, source_action, ambiguity_action),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )

        for action_index, action in enumerate(actions, 1):
            action_rows.append(
                {
                    "action_id": f"OHLC-GTOS-BRANCH-CAUSE-ACTION-{index:05d}-{action_index:03d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": branch.get("route_candidate_id"),
                    "symbol": branch.get("symbol"),
                    "route_session": branch.get("route_session"),
                    "side": branch.get("side"),
                    "entry_variant": branch.get("entry_variant"),
                    "target_stop_contract_id": branch.get("target_stop_contract_id"),
                    "action_family": action["action_family"],
                    "action_class": action["action_class"],
                    "primary_action_priority": priority,
                    "mechanical_next_step": action["mechanical_next_step"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

        for upstream_index, impl in enumerate(impl_rows_by_branch.get(branch_id, []), 1):
            upstream_impl_exploded_rows.append(
                {
                    "upstream_implementation_exploded_id": f"OHLC-GTOS-BRANCH-CAUSE-UPSTREAM-IMPL-{index:05d}-{upstream_index:03d}",
                    "source_implementation_implication_id": impl.get("implementation_implication_id"),
                    "branch_queue_id": branch_id,
                    "branch_proxy_score_id": impl.get("branch_proxy_score_id"),
                    "route_candidate_id": impl.get("route_candidate_id"),
                    "symbol": impl.get("symbol"),
                    "route_session": impl.get("route_session"),
                    "side": impl.get("side"),
                    "entry_variant": impl.get("entry_variant"),
                    "target_stop_contract_id": impl.get("target_stop_contract_id"),
                    "implementation_tag": impl.get("implementation_tag"),
                    "mechanical_next_step": impl.get("mechanical_next_step"),
                    "primary_action_priority": priority,
                    "source_repairability_class": source_repairability,
                    "exact_spread_repairability_class": exact_spread_repairability,
                    "ordering_collapse_route": ordering_route,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

        for upstream_index, action_score in enumerate(action_score_rows_by_branch.get(branch_id, []), 1):
            upstream_action_exploded_rows.append(
                {
                    "upstream_action_score_exploded_id": f"OHLC-GTOS-BRANCH-CAUSE-UPSTREAM-ACTION-{index:05d}-{upstream_index:03d}",
                    "source_action_score_id": action_score.get("action_score_id"),
                    "branch_queue_id": branch_id,
                    "branch_proxy_score_id": action_score.get("branch_proxy_score_id"),
                    "route_candidate_id": action_score.get("route_candidate_id"),
                    "symbol": action_score.get("symbol"),
                    "route_session": action_score.get("route_session"),
                    "side": action_score.get("side"),
                    "entry_variant": action_score.get("entry_variant"),
                    "target_stop_contract_id": action_score.get("target_stop_contract_id"),
                    "branch_action": action_score.get("branch_action"),
                    "proxy_mechanical_score": action_score.get("proxy_mechanical_score"),
                    "proxy_outcome_counts": action_score.get("proxy_outcome_counts"),
                    "primary_action_priority": priority,
                    "source_repairability_class": source_repairability,
                    "exact_spread_repairability_class": exact_spread_repairability,
                    "ordering_collapse_route": ordering_route,
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
                    "bucket_id": f"OHLC-GTOS-BRANCH-CAUSE-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": bucket,
                    "branch_count": count,
                    "branch_share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    question_rows = build_questions(bucket_counters, generated_at)

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "counts": {
            "branch_rstyle_input_rows": len(branch_rows),
            "control_delta_input_rows": len(control_by_branch),
            "cause_input_rows": len(cause_by_branch),
            "concentration_input_rows": len(concentration_rows),
            "concentration_group_counter_rows": len(concentration_counts),
            "branch_matrix_rows": len(matrix_rows),
            "action_rows": len(action_rows),
            "source_repair_rows": len(source_rows),
            "ambiguity_collapse_rows": len(ambiguity_rows),
            "implementation_candidate_rows": len(implementation_rows),
            "upstream_implementation_input_rows": len(upstream_impl_rows),
            "upstream_implementation_exploded_rows": len(upstream_impl_exploded_rows),
            "upstream_action_score_input_rows": len(upstream_action_score_rows),
            "upstream_action_score_exploded_rows": len(upstream_action_exploded_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(manifest_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
    }

    write_jsonl(BRANCH_MATRIX_PATH, matrix_rows)
    write_jsonl(ACTION_PATH, action_rows)
    write_jsonl(SOURCE_REPAIR_PATH, source_rows)
    write_jsonl(AMBIGUITY_COLLAPSE_PATH, ambiguity_rows)
    write_jsonl(IMPLEMENTATION_CANDIDATE_PATH, implementation_rows)
    write_jsonl(UPSTREAM_IMPLEMENTATION_EXPLODED_PATH, upstream_impl_exploded_rows)
    write_jsonl(UPSTREAM_ACTION_SCORE_EXPLODED_PATH, upstream_action_exploded_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)

    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


def branch_local_surface_hint(priority: str, fillability: str, source: str, ambiguity: str) -> str:
    if "ENTRY_GEOMETRY" in priority or "NEAR_MISS" in fillability or "RETEST" in fillability:
        return "research_harness_entry_geometry_and_retest_redesign"
    if "SOURCE" in priority or "SOURCE" in source or "SPREAD" in source:
        return "research_harness_source_locator_spread_replay_and_cost_model"
    if "AMBIGUITY" in priority or "ORDERING" in ambiguity:
        return "research_harness_m1_tick_ordering_interval_collapse"
    if "AVOID" in priority or "NEGATIVE" in priority:
        return "research_harness_avoid_filter_and_failure_router"
    if "CHALLENGER" in priority:
        return "research_harness_challenger_selector_comparison"
    return "research_harness_branch_router_preserve_and_compare"


def build_questions(bucket_counters: dict[str, Counter[str]], generated_at: str) -> list[dict[str, Any]]:
    questions = [
        {
            "question_id": "OHLC-GTOS-BRANCH-CAUSE-QUESTION-001",
            "question": "Which full-denominator action families become concrete branch-local challenger/redesign scripts first?",
            "answer_route": "Expand primary_action_priority buckets into implementation packets without dropping any branch row.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-CAUSE-QUESTION-002",
            "question": "Which ordering ambiguities can be collapsed from already-owned M1/tick/proxy data?",
            "answer_route": "Use ambiguity_collapse_class and rstyle component counters to isolate current-source collapsible rows from interval-only rows.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-CAUSE-QUESTION-003",
            "question": "Which exact-spread/source-stress branches are repairable versus permanently proxy-only from current sources?",
            "answer_route": "Join source_repair_class to source locator/depth/tick inventories and build repair-feasibility rows per branch.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-CAUSE-QUESTION-004",
            "question": "Do adverse stop-first branches imply avoid filters, entry redesign, target/stop redesign, or source ambiguity?",
            "answer_route": "Split negative/stop-first branches by fillability, ambiguity, cost, and same-route control deltas.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-CAUSE-QUESTION-005",
            "question": "Which positive proxy branches remain attractive after source, ambiguity, concentration, and control-delta penalties?",
            "answer_route": "Use action matrix rows to build a non-top-N challenger comparison ledger over all positive, repaired, and stressed branches.",
        },
    ]
    for row in questions:
        row.update(
            {
                "generated_utc": generated_at,
                "not_completion": True,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "supporting_bucket_snapshot": {
                    "primary_action_priority": compact_counter(bucket_counters.get("primary_action_priority", Counter())),
                    "source_repair_class": compact_counter(bucket_counters.get("source_repair_class", Counter())),
                    "ambiguity_collapse_class": compact_counter(bucket_counters.get("ambiguity_collapse_class", Counter())),
                },
            }
        )
    return questions


if __name__ == "__main__":
    raise SystemExit(main())
