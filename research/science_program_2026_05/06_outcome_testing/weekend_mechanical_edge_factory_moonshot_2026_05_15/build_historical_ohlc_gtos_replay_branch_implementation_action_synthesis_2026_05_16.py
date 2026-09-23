#!/usr/bin/env python3
"""Build the full branch implementation/action synthesis packet.

The output grain is exactly one row per branch_queue_id. Signature, contract,
entry-variant, and lower-timeframe rows are attached as counts, proxy intervals,
source-status distributions, or exploded sequence rows without changing the
386-branch denominator.
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

RSTYLE_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
RSTYLE_CONTROL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CONTROL_DELTA_LEDGER_2026-05-16.jsonl"
RSTYLE_CAUSE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_CAUSE_LEDGER_2026-05-16.jsonl"
MATRIX_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_BRANCH_LEDGER_2026-05-16.jsonl"
MATRIX_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_ACTION_LEDGER_2026-05-16.jsonl"
MATRIX_IMPL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
SOURCE_FEAS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_EXACT_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_REPAIR_FEASIBILITY_EXACT_SPREAD_ROUTE_LEDGER_2026-05-16.jsonl"
AMBIGUITY_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_BRANCH_CLASSIFICATION_LEDGER_2026-05-16.jsonl"
AMBIGUITY_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ORDERING_ROUTE_LEDGER_2026-05-16.jsonl"
AMBIGUITY_INTERVAL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_INTERVAL_PRESERVATION_LEDGER_2026-05-16.jsonl"

EXACT_SPREAD_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
M1_SPREAD_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
RECOVERED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH_LEDGER_2026-05-16.jsonl"
FAR_AVOID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_RETEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_OFFSET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_MARKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl"
SIERRA_SOURCE_MANIFEST_PATH = ROUTE_DIR / "SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_2026-05-16.json"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_RESULT_2026-05-16.json"
BRANCH_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
ENTRY_GEOMETRY_RETEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ENTRY_GEOMETRY_RETEST_LEDGER_2026-05-16.jsonl"
ADVERSE_STOP_FIRST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ADVERSE_STOP_FIRST_AVOID_REDESIGN_LEDGER_2026-05-16.jsonl"
POSITIVE_CHALLENGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_POSITIVE_CHALLENGER_COMPARISON_LEDGER_2026-05-16.jsonl"
SOURCE_STRESS_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_SOURCE_STRESS_ACTION_LEDGER_2026-05-16.jsonl"
ORDERING_COLLAPSE_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ORDERING_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_SEQUENCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_IMPLEMENTATION_SEQUENCE_EXPLODED_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC/MT5/Sierra/source-proxy branch implementation synthesis only. "
    "The packet preserves all 386 branch_queue_id rows and computes mechanically "
    "available proxy outcome, target/stop, pass-control, cost, source, ambiguity, "
    "duplicate/effective-N, concentration, entry-geometry, avoid/redesign, challenger, "
    "and implementation-action fields. It does not claim broker R/PnL, real strategy "
    "expectancy, win-rate, validation, live-readiness, promotion, or live behavior change."
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


def norm(value: Any) -> str:
    if value is None:
        return "None"
    try:
        return f"{float(value):.10g}"
    except (TypeError, ValueError):
        return str(value)


def branch_key(row: dict[str, Any], entry_field: str = "entry_variant") -> tuple[str, ...]:
    return (
        norm(row.get("route_candidate_id")),
        norm(row.get(entry_field)),
        norm(row.get("target_stop_contract_id")),
        norm(row.get("symbol")),
        norm(row.get("side")),
        norm(row.get("target_multiple")),
        norm(row.get("stop_multiple")),
    )


def compact_branch_key(row: dict[str, Any], entry_field: str = "entry_variant") -> tuple[str, ...]:
    return (
        norm(row.get("route_candidate_id")),
        norm(row.get(entry_field)),
        norm(row.get("target_stop_contract_id")),
    )


def group_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def group_by_key(input_rows: list[dict[str, Any]], entry_field: str = "entry_variant") -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[branch_key(row, entry_field)].append(row)
    return grouped


def group_by_compact_key(
    input_rows: list[dict[str, Any]], entry_field: str = "entry_variant"
) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[compact_branch_key(row, entry_field)].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def status_counts(input_rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return compact_counter(Counter(str(row.get(field)) for row in input_rows))


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 9)


def reward_to_risk(row: dict[str, Any]) -> float:
    direct = to_float(row.get("target_stop_reward_to_risk_ratio"))
    if direct is not None:
        return direct
    target = to_float(row.get("target_multiple"))
    stop = to_float(row.get("stop_multiple"))
    if target is None or stop in (None, 0.0):
        return 1.0
    return target / stop


def first_touch_interval(status_counter: dict[str, int], ratio: float) -> dict[str, Any]:
    lower_sum = midpoint_sum = upper_sum = 0.0
    total = 0
    for status, count in status_counter.items():
        total += count
        if "TARGET_AND_STOP" in status or "ORDER_UNRESOLVED" in status:
            lower_sum += -1.0 * count
            midpoint_sum += ((ratio - 1.0) / 2.0) * count
            upper_sum += ratio * count
        elif "TARGET_TOUCH" in status or "TARGET_FIRST" in status:
            lower_sum += ratio * count
            midpoint_sum += ratio * count
            upper_sum += ratio * count
        elif "STOP_TOUCH" in status or "STOP_FIRST" in status:
            lower_sum -= count
            midpoint_sum -= count
            upper_sum -= count
    return {
        "method": "first_touch_status_to_proxy_interval",
        "rows": total,
        "lower_mean": round(lower_sum / total, 9) if total else None,
        "midpoint_mean": round(midpoint_sum / total, 9) if total else None,
        "upper_mean": round(upper_sum / total, 9) if total else None,
        "status_counts": status_counter,
        "reward_to_risk_ratio": ratio,
        "missing_exact_reason": "Proxy interval only; exact broker fill, slippage, ticket lifecycle, and realized account PnL are absent.",
    }


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    paths = [
        RSTYLE_BRANCH_PATH,
        RSTYLE_CONTROL_PATH,
        RSTYLE_CAUSE_PATH,
        MATRIX_BRANCH_PATH,
        MATRIX_ACTION_PATH,
        MATRIX_IMPL_PATH,
        SOURCE_FEAS_PATH,
        SOURCE_EXACT_ROUTE_PATH,
        AMBIGUITY_BRANCH_PATH,
        AMBIGUITY_ORDERING_PATH,
        AMBIGUITY_INTERVAL_PATH,
        EXACT_SPREAD_DELTA_PATH,
        EXACT_SPREAD_UNAVAILABLE_PATH,
        M1_SPREAD_REPLAY_PATH,
        M1_FILL_BAR_STRESS_PATH,
        PATH_AMBIGUITY_PATH,
        RECOVERED_PATH,
        FAR_AVOID_PATH,
        FAR_RETEST_PATH,
        NEAR_OFFSET_PATH,
        NEAR_MARKET_PATH,
        SIERRA_SOURCE_MANIFEST_PATH,
    ]
    output = []
    for idx, path in enumerate(paths, 1):
        output.append(
            {
                "source_manifest_id": f"OHLC-GTOS-BRANCH-IMPL-SYNTH-SOURCE-{idx:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    digest = hashlib.sha256(json.dumps(output, sort_keys=True).encode("utf-8")).hexdigest()
    return output, digest


def source_stress_action_class(source_row: dict[str, Any]) -> str:
    repair_class = str(source_row.get("repair_feasibility_class"))
    if repair_class == "EXACT_SPREAD_RECOMPUTED_FROM_CURRENT_SOURCE":
        return "EXACT_SPREAD_RECOMPUTED_USE_REPAIRED_DESCRIPTOR"
    if repair_class == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        return "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY"
    if repair_class == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_REPLAY_AVAILABLE":
        return "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_USE_M1_REPLAY"
    if repair_class == "CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED":
        return "CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED"
    if repair_class == "PROVENANCE_ONLY_NO_SINGLE_SOURCE_REPAIR":
        return "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY"
    return "SOURCE_STRESS_ACTION_REVIEW_REQUIRED"


def ordering_collapse_action_class(ambiguity_row: dict[str, Any]) -> str:
    cls = str(ambiguity_row.get("ambiguity_collapse_class"))
    if cls == "M1_CHRONOLOGICAL_REPLAY_AVAILABLE_FOR_COLLAPSE":
        return "M1_CHRONOLOGICAL_COLLAPSE_AVAILABLE"
    if cls == "M1_FILL_BAR_STRESS_AVAILABLE_INTERVAL_BOUND_PRESERVED":
        return "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED"
    if cls == "M15_SAME_BAR_NO_EXISTING_M1_INTERVAL_PRESERVED":
        return "M15_INTERVAL_ONLY_NO_M1_SOURCE"
    if cls == "NO_COLLAPSE_REQUIRED_ORDERED_PROXY_PRESERVED":
        return "NO_COLLAPSE_REQUIRED"
    if cls == "RECOVERED_FILL_PATH_PRESENT_WITHOUT_M1_REPLAY_KEY":
        return "RECOVERED_PROXY_ONLY_NO_M1_KEY"
    if cls == "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY":
        return "TARGETSTOP_NA_BINDING_ONLY"
    return "ORDERING_COLLAPSE_ACTION_REVIEW_REQUIRED"


def entry_geometry_retest_class(matrix: dict[str, Any], far_retest_rows: list[dict[str, Any]], near_rows: int) -> str:
    fill_action = str(matrix.get("fillability_action_class"))
    fill_bucket = str(matrix.get("fillability_bucket"))
    miss_classes = {str(row.get("confirmed_nofill_miss_class")) for row in far_retest_rows}
    if fill_action == "NEAR_MISS_MARKET_OR_OFFSET_CHALLENGER_BUILD" or near_rows:
        return "NEAR_MISS_ENTRY_CHALLENGER"
    if "FAR_MISS_BEYOND_ROLLING_MEDIAN_RANGE" in miss_classes:
        return "FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN"
    if "WITHIN_RANGE_MISS_AT_OR_BELOW_ROLLING_MEDIAN_RANGE" in miss_classes:
        return "WITHIN_RANGE_RETEST_REDESIGN"
    if fill_bucket == "MIXED_OR_DESCRIPTOR_ONLY_FILLABILITY" or fill_action == "MIXED_FILLABILITY_SOURCE_SPLIT_REQUIRED":
        return "MIXED_FILLABILITY_SOURCE_SPLIT"
    return "NOT_ENTRY_GEOMETRY_RETEST_SCOPE"


def adverse_stop_first_class(matrix: dict[str, Any], source_cls: str, ordering_cls: str, entry_cls: str) -> str:
    failure = str(matrix.get("exact_failure_cause") or "")
    flagged = matrix.get("target_stop_result") == "STOP_FIRST_PROXY_DOMINANT" or "STOP_FIRST_PATH_ORDERING_DOMINATES" in failure
    if not flagged:
        return "NOT_ADVERSE_STOP_FIRST_SCOPE"
    if matrix.get("branch_result_class") == "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return "STOP_FIRST_MIXED_POSITIVE_PROXY_REVIEW"
    if source_cls == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        return "STOP_FIRST_SOURCE_REPAIR_FIRST"
    if ordering_cls in {
        "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED",
        "M15_INTERVAL_ONLY_NO_M1_SOURCE",
        "RECOVERED_PROXY_ONLY_NO_M1_KEY",
    }:
        return "STOP_FIRST_ORDERING_COLLAPSE_FIRST"
    if entry_cls in {
        "FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN",
        "WITHIN_RANGE_RETEST_REDESIGN",
        "NEAR_MISS_ENTRY_CHALLENGER",
    }:
        return "STOP_FIRST_RETEST_REDESIGN_FIRST"
    return "STOP_FIRST_AVOID_OR_REDESIGN_READY"


def positive_challenger_class(matrix: dict[str, Any], source_cls: str, ordering_cls: str) -> str:
    if matrix.get("branch_result_class") != "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return "NOT_POSITIVE_CHALLENGER_SCOPE"
    if source_cls in {
        "EXACT_SPREAD_RECOMPUTED_USE_REPAIRED_DESCRIPTOR",
        "CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED",
    }:
        return "POSITIVE_AFTER_EXACT_REPAIR"
    if source_cls == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_USE_M1_REPLAY":
        return "POSITIVE_ZERO_TO_SPREAD_REPLAY_COMPARABLE"
    if source_cls == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        return "POSITIVE_STRESS_INTERVAL_ONLY"
    if ordering_cls in {
        "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED",
        "M15_INTERVAL_ONLY_NO_M1_SOURCE",
        "RECOVERED_PROXY_ONLY_NO_M1_KEY",
    }:
        return "POSITIVE_ORDERING_COLLAPSE_REQUIRED"
    if "BELOW" in str(matrix.get("same_route_control_delta_class")) or (to_float(matrix.get("same_route_peer_delta")) or 0.0) < 0:
        return "POSITIVE_CONTROL_DELTA_ADVERSE"
    if str(matrix.get("effective_n_concentration_class")) in {
        "DUPLICATE_INFLATION_HIGH_MATERIAL_ROWS_OVER_EVENTS",
        "CONCENTRATION_HIGH_SYMBOL_OR_ROUTE_SHARE",
        "UNDERPOWERED_EFFECTIVE_N_LT_20",
    }:
        return "POSITIVE_CONCENTRATION_STRESSED"
    return "POSITIVE_CHALLENGER_REVIEW_REQUIRED"


def positive_control_delta_modifier(matrix: dict[str, Any]) -> str:
    if matrix.get("branch_result_class") != "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return "NOT_POSITIVE_CHALLENGER_SCOPE"
    if "BELOW" in str(matrix.get("same_route_control_delta_class")) or (to_float(matrix.get("same_route_peer_delta")) or 0.0) < 0:
        return "CONTROL_DELTA_ADVERSE_OR_BELOW_ROUTE_PEERS"
    return "CONTROL_DELTA_NOT_ADVERSE"


def positive_concentration_modifier(matrix: dict[str, Any]) -> str:
    if matrix.get("branch_result_class") != "POSITIVE_RSTYLE_PROXY_MIDPOINT":
        return "NOT_POSITIVE_CHALLENGER_SCOPE"
    if str(matrix.get("effective_n_concentration_class")) in {
        "DUPLICATE_INFLATION_HIGH_MATERIAL_ROWS_OVER_EVENTS",
        "CONCENTRATION_HIGH_SYMBOL_OR_ROUTE_SHARE",
        "UNDERPOWERED_EFFECTIVE_N_LT_20",
    }:
        return "CONCENTRATION_OR_EFFECTIVE_N_STRESSED"
    return "CONCENTRATION_MODIFIER_NOT_STRESSED"


def implementation_implication(entry_cls: str, adverse_cls: str, positive_cls: str, source_cls: str, ordering_cls: str) -> tuple[str, list[str]]:
    tags = []
    steps = []
    if source_cls == "TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY" or ordering_cls == "TARGETSTOP_NA_BINDING_ONLY":
        tags.append("TARGETSTOP_NA_SIGNATURE_SCOPE_BINDING_ONLY")
        steps.append("Preserve target/stop NA branch as binding/provenance scope; use bound signature-scope rows for target/stop questions.")
    if entry_cls == "NEAR_MISS_ENTRY_CHALLENGER":
        tags.append("NEAR_MISS_ENTRY_GEOMETRY_CHALLENGER")
        steps.append("Replay near-miss offset and market-entry variants with exact source requirements attached.")
    if entry_cls == "FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN":
        tags.append("FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN")
        steps.append("Convert far no-fill miss contexts into avoid-filter and market-entry proxy redesign tests.")
    if entry_cls == "WITHIN_RANGE_RETEST_REDESIGN":
        tags.append("WITHIN_RANGE_RETEST_REDESIGN")
        steps.append("Build retest-zone and entry-offset redesign variants for within-range no-fill branches.")
    if adverse_cls.startswith("STOP_FIRST_") and adverse_cls != "NOT_ADVERSE_STOP_FIRST_SCOPE":
        tags.append(adverse_cls)
        steps.append("Use stop-first failure cause as avoid/redesign intelligence; do not preserve the original branch unchanged.")
    if positive_cls.startswith("POSITIVE_"):
        tags.append(positive_cls)
        steps.append("Compare positive proxy branch after carrying source, ordering, concentration, effective-N, and control-delta flags.")
    if source_cls in {"EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY", "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_USE_M1_REPLAY"}:
        tags.append(source_cls)
        steps.append("Keep exact-spread unavailable or zero-to-spread branches stress/proxy bounded until repaired by current source.")
    if ordering_cls in {"M1_FILL_BAR_STRESS_INTERVAL_PRESERVED", "M15_INTERVAL_ONLY_NO_M1_SOURCE", "RECOVERED_PROXY_ONLY_NO_M1_KEY"}:
        tags.append(ordering_cls)
        steps.append("Preserve interval bounds or use M1/tick collapse where source evidence exists; never coerce interval-straddling rows.")
    if not tags:
        tags.append("PRESERVE_AND_ROUTE_BY_BUCKET")
        steps.append("Preserve branch row and route by full classifier bucket set.")
    return "__".join(tags), steps


def join_diagnostics(
    join_specs: dict[str, tuple[set[tuple[str, ...]], dict[tuple[str, ...], list[dict[str, Any]]], str]]
) -> dict[str, Any]:
    diagnostics = {}
    for name, (base_keys, grouped, key_policy) in join_specs.items():
        input_rows = sum(len(v) for v in grouped.values())
        matched_rows = sum(len(v) for key, v in grouped.items() if key in base_keys)
        diagnostics[name] = {
            "join_key_policy": key_policy,
            "input_rows": input_rows,
            "matched_rows_to_386_branch_keys": matched_rows,
            "unmatched_rows_to_386_branch_keys": input_rows - matched_rows,
            "matched_base_keys": sum(1 for key in base_keys if grouped.get(key)),
            "matched_branch_keys": sum(1 for key in base_keys if grouped.get(key)),
        }
    return diagnostics


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}

    artifacts = [
        (Path(__file__).resolve(), "builder"),
        (RESULT_PATH, "result"),
        (BRANCH_LEDGER_PATH, "branch_ledger"),
        (ENTRY_GEOMETRY_RETEST_PATH, "entry_geometry_retest_ledger"),
        (ADVERSE_STOP_FIRST_PATH, "adverse_stop_first_avoid_redesign_ledger"),
        (POSITIVE_CHALLENGER_PATH, "positive_challenger_comparison_ledger"),
        (SOURCE_STRESS_ACTION_PATH, "source_stress_action_ledger"),
        (ORDERING_COLLAPSE_ACTION_PATH, "ordering_collapse_action_ledger"),
        (IMPLEMENTATION_SEQUENCE_PATH, "implementation_sequence_exploded_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SOURCE_MANIFEST_LEDGER_PATH, "source_manifest_ledger"),
        (SUMMARY_PATH, "summary"),
    ]
    artifact_names = {path.name for path, _ in artifacts}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in artifacts[1:]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_implementation_action_synthesis",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path, _ in artifacts}
    manifest["artifacts"] = [row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths]
    for path, artifact_type in artifacts:
        manifest["artifacts"].append(
            {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": artifact_type}
        )
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "route_artifact_built",
                    "route": "historical_ohlc_gtos_replay_branch_implementation_action_synthesis",
                    "artifact": RESULT_PATH.name,
                    "counts": result["counts"],
                    "not_completion": True,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                },
                sort_keys=True,
            )
            + "\n"
        )


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Branch Implementation/Action Synthesis",
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
    for category in [
        "entry_geometry_retest_class",
        "adverse_stop_first_class",
        "positive_challenger_class",
        "source_stress_action_class",
        "ordering_collapse_action_class",
    ]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"][category].items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()

    matrix_rows = rows(MATRIX_BRANCH_PATH)
    base_keys = {branch_key(row) for row in matrix_rows}
    compact_base_keys = {compact_branch_key(row) for row in matrix_rows}

    rstyle_by_branch = group_by_branch(rows(RSTYLE_BRANCH_PATH))
    control_by_branch = group_by_branch(rows(RSTYLE_CONTROL_PATH))
    cause_by_branch = group_by_branch(rows(RSTYLE_CAUSE_PATH))
    impl_by_branch = group_by_branch(rows(MATRIX_IMPL_PATH))
    source_by_branch = group_by_branch(rows(SOURCE_FEAS_PATH))
    ambiguity_by_branch = group_by_branch(rows(AMBIGUITY_BRANCH_PATH))
    ambiguity_ordering_by_branch = group_by_branch(rows(AMBIGUITY_ORDERING_PATH))
    ambiguity_interval_by_branch = group_by_branch(rows(AMBIGUITY_INTERVAL_PATH))
    source_exact_by_branch = group_by_branch(rows(SOURCE_EXACT_ROUTE_PATH))
    matrix_actions_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows(MATRIX_ACTION_PATH):
        matrix_actions_by_branch[str(row.get("branch_queue_id"))].append(row)

    exact_delta_by_compact_key = group_by_compact_key(rows(EXACT_SPREAD_DELTA_PATH))
    exact_unavailable_by_key = group_by_key(rows(EXACT_SPREAD_UNAVAILABLE_PATH))
    m1_replay_by_key = group_by_key(rows(M1_SPREAD_REPLAY_PATH))
    fill_bar_by_key = group_by_key(rows(M1_FILL_BAR_STRESS_PATH))
    path_ambiguity_by_compact_key = group_by_compact_key(rows(PATH_AMBIGUITY_PATH))
    recovered_by_key = group_by_key(rows(RECOVERED_PATH))
    far_avoid_by_key = group_by_key(rows(FAR_AVOID_PATH))
    far_retest_by_key = group_by_key(rows(FAR_RETEST_PATH))
    near_offset_by_key = group_by_key(rows(NEAR_OFFSET_PATH), "source_entry_variant")
    near_market_by_key = group_by_key(rows(NEAR_MARKET_PATH), "source_entry_variant")

    grouped_for_join = {
        "exact_spread_delta": (compact_base_keys, exact_delta_by_compact_key, "compact_route_entry_targetstop"),
        "exact_spread_unavailable": (base_keys, exact_unavailable_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "m1_spread_replay": (base_keys, m1_replay_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "m1_fill_bar_stress": (base_keys, fill_bar_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "path_ambiguity": (compact_base_keys, path_ambiguity_by_compact_key, "compact_route_entry_targetstop"),
        "recovered_unfilled": (base_keys, recovered_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "far_avoid": (base_keys, far_avoid_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "far_retest": (base_keys, far_retest_by_key, "full_route_entry_targetstop_symbol_side_target_stop"),
        "near_offset": (base_keys, near_offset_by_key, "full_route_source_entry_targetstop_symbol_side_target_stop"),
        "near_market": (base_keys, near_market_by_key, "full_route_source_entry_targetstop_symbol_side_target_stop"),
    }

    branch_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    adverse_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    source_action_rows: list[dict[str, Any]] = []
    ordering_rows: list[dict[str, Any]] = []
    sequence_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    edge_counters: Counter[str] = Counter()

    for index, matrix in enumerate(matrix_rows, 1):
        branch_id = str(matrix.get("branch_queue_id"))
        key = branch_key(matrix)
        compact_key = compact_branch_key(matrix)
        rstyle = rstyle_by_branch.get(branch_id, {})
        control = control_by_branch.get(branch_id, {})
        cause = cause_by_branch.get(branch_id, {})
        source = source_by_branch.get(branch_id, {})
        source_exact = source_exact_by_branch.get(branch_id, {})
        ambiguity = ambiguity_by_branch.get(branch_id, {})
        ambiguity_ordering = ambiguity_ordering_by_branch.get(branch_id, {})
        ambiguity_interval = ambiguity_interval_by_branch.get(branch_id, {})
        impl = impl_by_branch.get(branch_id, {})

        far_retest_rows = far_retest_by_key.get(key, [])
        far_avoid_rows = far_avoid_by_key.get(key, [])
        near_offset_rows = near_offset_by_key.get(key, [])
        near_market_rows = near_market_by_key.get(key, [])
        ratio = reward_to_risk(matrix)

        near_offset_status = status_counts(near_offset_rows, "first_touch_status_offset_proxy")
        near_market_status = status_counts(near_market_rows, "market_first_touch_status")
        far_miss_distances = [
            value
            for value in (to_float(row.get("miss_distance_to_zero_over_rolling_median_range")) for row in far_retest_rows)
            if value is not None
        ]

        entry_cls = entry_geometry_retest_class(matrix, far_retest_rows, len(near_offset_rows) + len(near_market_rows))
        source_cls = source_stress_action_class(source)
        ordering_cls = ordering_collapse_action_class(ambiguity)
        adverse_cls = adverse_stop_first_class(matrix, source_cls, ordering_cls, entry_cls)
        positive_cls = positive_challenger_class(matrix, source_cls, ordering_cls)
        positive_control_delta_mod = positive_control_delta_modifier(matrix)
        positive_concentration_mod = positive_concentration_modifier(matrix)
        implication_cls, steps = implementation_implication(entry_cls, adverse_cls, positive_cls, source_cls, ordering_cls)

        full_classes = {
            "entry_geometry_retest_class": entry_cls,
            "adverse_stop_first_class": adverse_cls,
            "positive_challenger_class": positive_cls,
            "positive_control_delta_modifier_class": positive_control_delta_mod,
            "positive_concentration_modifier_class": positive_concentration_mod,
            "source_stress_action_class": source_cls,
            "ordering_collapse_action_class": ordering_cls,
            "implementation_primary_action_class": matrix.get("primary_action_priority"),
            "implementation_implication_class": implication_cls,
        }
        for field, value in full_classes.items():
            bucket_counters[field][str(value)] += 1
        for field in ["branch_result_class", "target_stop_result", "effective_n_concentration_class"]:
            bucket_counters[field][str(matrix.get(field))] += 1

        if matrix.get("branch_result_class") == "AMBIGUOUS_INTERVAL_STRADDLES_ZERO":
            edge_counters["interval_straddles_preserved"] += 1
        if matrix.get("target_stop_contract_id") == "TARGETSTOP_NA_NA":
            edge_counters["targetstop_na_preserved"] += 1
        if ordering_cls == "RECOVERED_PROXY_ONLY_NO_M1_KEY":
            edge_counters["recovered_without_m1_key"] += 1

        exact_failure = matrix.get("exact_failure_cause") or cause.get("exact_failure_cause")
        exact_success = matrix.get("exact_success_cause") or cause.get("exact_success_cause")
        exact_missing_reason = matrix.get("exact_missing_geometry_reason") or rstyle.get("missing_exact_geometry_reason")
        sequence_base = {
            "branch_queue_id": branch_id,
            "route_candidate_id": matrix.get("route_candidate_id"),
            "symbol": matrix.get("symbol"),
            "route_session": matrix.get("route_session"),
            "side": matrix.get("side"),
            "entry_variant": matrix.get("entry_variant"),
            "target_stop_contract_id": matrix.get("target_stop_contract_id"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
        }

        branch_rows.append(
            {
                "implementation_action_synthesis_branch_id": f"OHLC-GTOS-BRANCH-IMPL-SYNTH-{index:05d}",
                **sequence_base,
                "branch_proxy_score_id": matrix.get("branch_proxy_score_id"),
                "branch_rstyle_proxy_outcome_id": matrix.get("branch_rstyle_proxy_outcome_id"),
                "target_multiple": matrix.get("target_multiple"),
                "stop_multiple": matrix.get("stop_multiple"),
                "target_stop_reward_to_risk_ratio": ratio,
                "sealed_or_proxy_outcome_status": matrix.get("sealed_or_proxy_outcome_status"),
                "branch_result_class": matrix.get("branch_result_class"),
                "target_stop_result": matrix.get("target_stop_result"),
                "rstyle_lower_mean": matrix.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": matrix.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": matrix.get("rstyle_upper_mean"),
                "rstyle_interval_rows": matrix.get("rstyle_interval_rows"),
                "expectancy_style_proxy_method": matrix.get("expectancy_style_proxy_method"),
                "expectancy_style_proxy_exact_missing_reason": (matrix.get("rstyle_proxy_action") or {}).get("exact_missing_reason"),
                "target_first_rows": matrix.get("target_first_rows"),
                "stop_first_rows": matrix.get("stop_first_rows"),
                "ambiguous_ordering_rows": matrix.get("ambiguous_ordering_rows"),
                "no_fill_or_unfilled_rows": matrix.get("no_fill_or_unfilled_rows"),
                "pass_control_delta_status": matrix.get("pass_control_delta_status"),
                "same_route_peer_delta": matrix.get("same_route_peer_delta"),
                "same_route_peer_count": matrix.get("same_route_peer_count"),
                "same_symbol_session_side_targetstop_delta": matrix.get("same_symbol_session_side_targetstop_delta"),
                "neighbor_directional_close_vs_permuted": matrix.get("neighbor_directional_close_vs_permuted"),
                "positive_control_delta_modifier_class": positive_control_delta_mod,
                "positive_concentration_modifier_class": positive_concentration_mod,
                "cost_robustness_bucket": matrix.get("cost_robustness_bucket"),
                "cost_sensitivity": rstyle.get("cost_sensitivity"),
                "source_confidence_status": matrix.get("source_confidence_status"),
                "source_repairability_class": matrix.get("source_repairability_class"),
                "exact_spread_repairability_class": matrix.get("exact_spread_repairability_class"),
                "repair_feasibility_class": source.get("repair_feasibility_class"),
                "source_repair_route_class": source.get("source_repair_route_class"),
                "exact_spread_descriptor_delta_rows": len(exact_delta_by_compact_key.get(compact_key, [])),
                "exact_spread_unavailable_stress_rows": len(exact_unavailable_by_key.get(key, [])),
                "m1_spread_adjusted_replay_rows": len(m1_replay_by_key.get(key, [])),
                "m1_fill_bar_stress_rows": len(fill_bar_by_key.get(key, [])),
                "path_ambiguity_rows": len(path_ambiguity_by_compact_key.get(compact_key, [])),
                "recovered_unfilled_rows": len(recovered_by_key.get(key, [])),
                "ambiguity_status": matrix.get("ambiguity_status"),
                "ambiguity_collapse_class": ambiguity.get("ambiguity_collapse_class"),
                "ordering_collapse_route": matrix.get("ordering_collapse_route"),
                "interval_preservation_class": ambiguity.get("interval_preservation_class"),
                "m15_same_bar_rows_for_branch_key": ambiguity.get("m15_same_bar_rows_for_branch_key"),
                "m1_existing_class": ambiguity.get("m1_existing_class"),
                "targetstop_na_binding_class": ambiguity.get("targetstop_na_binding_class"),
                "unique_event_or_route_ids": matrix.get("unique_event_or_route_ids"),
                "material_joined_rows": matrix.get("material_joined_rows"),
                "duplicate_inflation_ratio_material_rows_over_event_ids": matrix.get(
                    "duplicate_inflation_ratio_material_rows_over_event_ids"
                ),
                "effective_n_concentration_class": matrix.get("effective_n_concentration_class"),
                "concentration_summary": matrix.get("concentration_summary"),
                **full_classes,
                "implementation_candidate_status": impl.get("implementation_candidate_status"),
                "branch_local_code_surface_hint": impl.get("branch_local_code_surface_hint"),
                "exact_failure_cause": exact_failure,
                "exact_success_cause": exact_success,
                "cause_tags": matrix.get("cause_tags") or rstyle.get("cause_tags") or [],
                "exact_missing_geometry_or_source_reason": exact_missing_reason,
                "next_same_resource_actions": steps,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS",
            }
        )

        entry_rows.append(
            {
                "entry_geometry_retest_id": f"OHLC-GTOS-BRANCH-IMPL-ENTRY-GEOMETRY-{index:05d}",
                **sequence_base,
                "entry_geometry_retest_class": entry_cls,
                "fillability_action_class": matrix.get("fillability_action_class"),
                "fillability_bucket": matrix.get("fillability_bucket"),
                "far_avoid_rows": len(far_avoid_rows),
                "far_avoid_status_counts": status_counts(far_avoid_rows, "avoid_filter_branch_status"),
                "far_retest_rows": len(far_retest_rows),
                "far_retest_status_counts": status_counts(far_retest_rows, "retest_redesign_branch_status"),
                "far_retest_miss_class_counts": status_counts(far_retest_rows, "confirmed_nofill_miss_class"),
                "far_mean_miss_distance_to_zero_over_rolling_median_range": mean(far_miss_distances),
                "near_offset_rows": len(near_offset_rows),
                "near_offset_first_touch_proxy": first_touch_interval(near_offset_status, ratio),
                "near_market_rows": len(near_market_rows),
                "near_market_first_touch_proxy": first_touch_interval(near_market_status, ratio),
                "source_requirement_status": "ATTACHED_VIA_NEAR_MISS_PACKET_WHEN_ROWS_PRESENT",
            }
        )
        adverse_rows.append(
            {
                "adverse_stop_first_avoid_redesign_id": f"OHLC-GTOS-BRANCH-IMPL-ADVERSE-{index:05d}",
                **sequence_base,
                "adverse_stop_first_class": adverse_cls,
                "branch_result_class": matrix.get("branch_result_class"),
                "target_stop_result": matrix.get("target_stop_result"),
                "rstyle_midpoint_mean": matrix.get("rstyle_midpoint_mean"),
                "same_route_peer_delta": matrix.get("same_route_peer_delta"),
                "source_stress_action_class": source_cls,
                "ordering_collapse_action_class": ordering_cls,
                "entry_geometry_retest_class": entry_cls,
                "exact_failure_cause": exact_failure,
                "far_avoid_status_counts": status_counts(far_avoid_rows, "avoid_filter_branch_status"),
                "far_retest_status_counts": status_counts(far_retest_rows, "retest_redesign_branch_status"),
            }
        )
        positive_rows.append(
            {
                "positive_challenger_comparison_id": f"OHLC-GTOS-BRANCH-IMPL-POSITIVE-{index:05d}",
                **sequence_base,
                "positive_challenger_class": positive_cls,
                "branch_result_class": matrix.get("branch_result_class"),
                "target_stop_result": matrix.get("target_stop_result"),
                "rstyle_lower_mean": matrix.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": matrix.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": matrix.get("rstyle_upper_mean"),
                "same_route_peer_delta": matrix.get("same_route_peer_delta"),
                "same_route_peer_count": matrix.get("same_route_peer_count"),
                "effective_n_concentration_class": matrix.get("effective_n_concentration_class"),
                "positive_control_delta_modifier_class": positive_control_delta_mod,
                "positive_concentration_modifier_class": positive_concentration_mod,
                "positive_source_modifier_class": source_cls,
                "positive_ordering_modifier_class": ordering_cls,
                "repair_feasibility_class": source.get("repair_feasibility_class"),
                "ambiguity_collapse_class": ambiguity.get("ambiguity_collapse_class"),
                "exact_success_cause": exact_success,
                "exact_failure_cause": exact_failure,
            }
        )
        source_action_rows.append(
            {
                "source_stress_action_id": f"OHLC-GTOS-BRANCH-IMPL-SOURCE-{index:05d}",
                **sequence_base,
                "source_stress_action_class": source_cls,
                "source_confidence_status": matrix.get("source_confidence_status"),
                "source_repairability_class": matrix.get("source_repairability_class"),
                "exact_spread_repairability_class": matrix.get("exact_spread_repairability_class"),
                "repair_feasibility_class": source.get("repair_feasibility_class"),
                "source_repair_route_class": source.get("source_repair_route_class"),
                "exact_descriptor_delta_status_counts": source_exact.get("exact_descriptor_delta_status_counts"),
                "exact_unavailable_source_status_counts": source_exact.get("exact_unavailable_source_status_counts"),
                "exact_spread_descriptor_delta_rows": len(exact_delta_by_compact_key.get(compact_key, [])),
                "exact_spread_unavailable_stress_rows": len(exact_unavailable_by_key.get(key, [])),
                "source_next_actions": source.get("next_same_resource_actions"),
                "sierra_depth_manifest_context": (read_json(SIERRA_SOURCE_MANIFEST_PATH) or {}).get("counts"),
            }
        )
        ordering_rows.append(
            {
                "ordering_collapse_action_id": f"OHLC-GTOS-BRANCH-IMPL-ORDERING-{index:05d}",
                **sequence_base,
                "ordering_collapse_action_class": ordering_cls,
                "ambiguity_collapse_class": ambiguity.get("ambiguity_collapse_class"),
                "ordering_collapse_route": matrix.get("ordering_collapse_route"),
                "interval_preservation_class": ambiguity.get("interval_preservation_class"),
                "m15_same_bar_rows_for_branch_key": ambiguity.get("m15_same_bar_rows_for_branch_key"),
                "m1_spread_adjusted_replay_rows_for_branch_key": ambiguity.get("m1_spread_adjusted_replay_rows_for_branch_key"),
                "m1_fill_bar_stress_rows_for_branch_key": ambiguity.get("m1_fill_bar_stress_rows_for_branch_key"),
                "recovered_signature_path_rows_for_branch_key": ambiguity.get("recovered_signature_path_rows_for_branch_key"),
                "m1_replay_first_touch_status_counts": ambiguity.get("m1_replay_first_touch_status_counts"),
                "m1_fill_bar_interval_status_counts": ambiguity.get("m1_fill_bar_interval_status_counts"),
                "interval_preservation_rstyle_lower_mean": ambiguity_interval.get("rstyle_lower_mean"),
                "interval_preservation_rstyle_midpoint_mean": ambiguity_interval.get("rstyle_midpoint_mean"),
                "interval_preservation_rstyle_upper_mean": ambiguity_interval.get("rstyle_upper_mean"),
                "ordering_route_action": ambiguity_ordering.get("ambiguity_collapse_next_action"),
                "targetstop_na_binding_class": ambiguity.get("targetstop_na_binding_class"),
            }
        )
        seq_items = [
            ("PRIMARY", matrix.get("primary_action_priority")),
            ("ENTRY_GEOMETRY_RETEST", entry_cls),
            ("ADVERSE_STOP_FIRST", adverse_cls),
            ("POSITIVE_CHALLENGER", positive_cls),
            ("SOURCE_STRESS", source_cls),
            ("ORDERING_COLLAPSE", ordering_cls),
            ("IMPLEMENTATION_IMPLICATION", implication_cls),
        ]
        for seq_index, (family, action_class) in enumerate(seq_items, 1):
            sequence_rows.append(
                {
                    "implementation_sequence_id": f"OHLC-GTOS-BRANCH-IMPL-SEQUENCE-{index:05d}-{seq_index:03d}",
                    **sequence_base,
                    "sequence_index": seq_index,
                    "action_family": family,
                    "action_class": action_class,
                    "mechanical_next_steps": steps if family == "IMPLEMENTATION_IMPLICATION" else [],
                }
            )
        for upstream_index, upstream_action in enumerate(matrix_actions_by_branch.get(branch_id, []), len(seq_items) + 1):
            sequence_rows.append(
                {
                    "implementation_sequence_id": f"OHLC-GTOS-BRANCH-IMPL-SEQUENCE-{index:05d}-{upstream_index:03d}",
                    **sequence_base,
                    "sequence_index": upstream_index,
                    "action_family": "UPSTREAM_MATRIX_ACTION",
                    "action_class": upstream_action.get("action_class"),
                    "mechanical_next_steps": [upstream_action.get("mechanical_next_step")],
                }
            )

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-BRANCH-IMPL-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "branch_count": int(count),
                    "branch_share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-BRANCH-IMPL-SYNTH-QUESTION-001",
            "question": "Which entry-geometry/retest branches are now concrete market-entry, offset, retest-zone, or avoid-filter implementations?",
            "answer_route": "Use ENTRY_GEOMETRY_RETEST_LEDGER across all 386 rows and expand each class without top-N truncation.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-IMPL-SYNTH-QUESTION-002",
            "question": "Which stop-first adverse branches are source-blocked, ordering-blocked, retest-redesignable, or immediately avoid/redesign ready?",
            "answer_route": "Use ADVERSE_STOP_FIRST_AVOID_REDESIGN_LEDGER with source_stress_action_class and ordering_collapse_action_class.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-IMPL-SYNTH-QUESTION-003",
            "question": "Which positive proxy midpoint branches survive as challenger comparisons after control, source, ambiguity, and concentration modifiers?",
            "answer_route": "Use POSITIVE_CHALLENGER_COMPARISON_LEDGER; modifiers are attached to every row and not used as top-N filters.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-IMPL-SYNTH-QUESTION-004",
            "question": "Which exact-spread unavailable rows can be repaired from owned/free/current sources versus remaining low/high stress-bounded?",
            "answer_route": "Use SOURCE_STRESS_ACTION_LEDGER and source manifest; no scalar collapse for unavailable rows.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-IMPL-SYNTH-QUESTION-005",
            "question": "Which interval-preserved branches can be collapsed through current M1/tick rows and which remain M15 interval-only?",
            "answer_route": "Use ORDERING_COLLAPSE_ACTION_LEDGER and preserve interval-straddling rows exactly.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "generated_utc": generated_at,
                "not_completion": True,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "bucket_snapshot": {
                    "entry_geometry_retest_class": compact_counter(bucket_counters["entry_geometry_retest_class"]),
                    "adverse_stop_first_class": compact_counter(bucket_counters["adverse_stop_first_class"]),
                    "positive_challenger_class": compact_counter(bucket_counters["positive_challenger_class"]),
                    "source_stress_action_class": compact_counter(bucket_counters["source_stress_action_class"]),
                    "ordering_collapse_action_class": compact_counter(bucket_counters["ordering_collapse_action_class"]),
                },
            }
        )

    join_report = join_diagnostics(grouped_for_join)
    edge_counters["m1_fill_bar_source_fail_closed_rows_carried"] = sum(
        count
        for status, count in Counter(
            str(row.get("conservative_source_status")) for grouped in fill_bar_by_key.values() for row in grouped
        ).items()
        if "FAIL_CLOSED" in status or "MISSING" in status
    )
    edge_counters["exact_unavailable_rows_stress_bounded"] = bucket_counters["source_stress_action_class"][
        "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY"
    ]

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "counts": {
            "matrix_branch_input_rows": len(matrix_rows),
            "rstyle_branch_input_rows": len(rstyle_by_branch),
            "control_delta_input_rows": len(control_by_branch),
            "cause_input_rows": len(cause_by_branch),
            "matrix_action_input_rows": sum(len(v) for v in matrix_actions_by_branch.values()),
            "matrix_implementation_input_rows": len(impl_by_branch),
            "source_feasibility_input_rows": len(source_by_branch),
            "source_exact_route_input_rows": len(source_exact_by_branch),
            "ambiguity_branch_input_rows": len(ambiguity_by_branch),
            "ambiguity_ordering_input_rows": len(ambiguity_ordering_by_branch),
            "ambiguity_interval_input_rows": len(ambiguity_interval_by_branch),
            "branch_synthesis_rows": len(branch_rows),
            "entry_geometry_retest_rows": len(entry_rows),
            "adverse_stop_first_avoid_redesign_rows": len(adverse_rows),
            "positive_challenger_comparison_rows": len(positive_rows),
            "source_stress_action_rows": len(source_action_rows),
            "ordering_collapse_action_rows": len(ordering_rows),
            "implementation_sequence_exploded_rows": len(sequence_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "join_diagnostics": join_report,
        "edge_checks": compact_counter(edge_counters),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }

    write_jsonl(BRANCH_LEDGER_PATH, branch_rows)
    write_jsonl(ENTRY_GEOMETRY_RETEST_PATH, entry_rows)
    write_jsonl(ADVERSE_STOP_FIRST_PATH, adverse_rows)
    write_jsonl(POSITIVE_CHALLENGER_PATH, positive_rows)
    write_jsonl(SOURCE_STRESS_ACTION_PATH, source_action_rows)
    write_jsonl(ORDERING_COLLAPSE_ACTION_PATH, ordering_rows)
    write_jsonl(IMPLEMENTATION_SEQUENCE_PATH, sequence_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER_PATH, source_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)

    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
