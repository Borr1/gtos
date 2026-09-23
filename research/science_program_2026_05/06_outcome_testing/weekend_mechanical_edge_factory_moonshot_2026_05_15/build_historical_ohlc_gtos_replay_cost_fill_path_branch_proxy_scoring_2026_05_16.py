#!/usr/bin/env python3
"""Score every Route C cost/fill/path branch with same-resource proxy evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

BRANCH_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_BRANCH_QUEUE_2026-05-16.jsonl"
FAMILY_SYNTHESIS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_FAMILY_LEDGER_2026-05-16.jsonl"
COST_FILL_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_GRID_LEDGER_2026-05-16.jsonl"
PATH_CONTROL_GRID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_GRID_LEDGER_2026-05-16.jsonl"
NEAR_MARKET_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_OFFSET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_AVOID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_RETEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_SOURCE_CONFIDENCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_SOURCE_CONFIDENCE_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_SOURCE_REQUIREMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_SOURCE_REQUIREMENT_LEDGER_2026-05-16.jsonl"
SIERRA_SOURCE_DATE_REQUIREMENT_PATH = ROUTE_DIR / "SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_2026-05-16_REQUIREMENT_ROW_LEDGER.jsonl"
SIERRA_SOURCE_DATE_MANIFEST_PATH = ROUTE_DIR / "SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_2026-05-16.json"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_RESULT_2026-05-16.json"
BRANCH_SCORE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_BRANCH_SCORE_LEDGER_2026-05-16.jsonl"
ACTION_SCORE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_ACTION_SCORE_LEDGER_2026-05-16.jsonl"
CONCENTRATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_CONCENTRATION_LEDGER_2026-05-16.jsonl"
DUPLICATE_EFFECTIVE_N_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_IMPLEMENTATION_IMPLICATION_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
SUBAGENT_LEDGER_PATH = ROUTE_DIR / "SUBAGENT_DELEGATION_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay cost/fill/path branch proxy scoring only. Rows "
    "mechanically score same-resource fillability, spread/path sensitivity, source "
    "confidence, ambiguity, duplicate/effective-N, and implementation implications "
    "for all 386 branch-queue rows; no validation, R/PnL, expectancy, win-rate, "
    "live-readiness, promotion, or live behavior change is claimed."
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        BRANCH_QUEUE_PATH,
        FAMILY_SYNTHESIS_PATH,
        COST_FILL_GRID_PATH,
        PATH_CONTROL_GRID_PATH,
        NEAR_MARKET_ENTRY_PATH,
        NEAR_OFFSET_PATH,
        FAR_AVOID_PATH,
        FAR_RETEST_PATH,
        FAR_SOURCE_CONFIDENCE_PATH,
        NEAR_SOURCE_REQUIREMENT_PATH,
        SIERRA_SOURCE_DATE_REQUIREMENT_PATH,
        SIERRA_SOURCE_DATE_MANIFEST_PATH,
    ]
    rows = []
    for path in paths:
        rows.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
            }
        )
    return rows, hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()


def key_from_parts(route_candidate_id: Any, entry_variant: Any, target_stop_contract_id: Any) -> tuple[str, str, str]:
    return (str(route_candidate_id), str(entry_variant), str(target_stop_contract_id))


def row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    entry = row.get("source_entry_variant") or row.get("entry_variant")
    target_stop = row.get("target_stop_contract_id")
    if target_stop is None:
        target = row.get("target_multiple", row.get("target_multiple_of_rolling_median_range", "NA"))
        stop = row.get("stop_multiple", row.get("stop_multiple_of_rolling_median_range", "NA"))
        target_stop = f"TARGETSTOP_{target}_{stop}"
    return key_from_parts(row.get("route_candidate_id"), entry, target_stop)


def compact_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: int(counter[key]) for key in sorted(counter)}


def merge_counter(counter: Counter[str], value: dict[str, Any] | None) -> None:
    if not isinstance(value, dict):
        return
    for key, count in value.items():
        counter[str(key)] += int(count or 0)


def id_set(value: Any) -> set[str]:
    if not value:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value if item is not None}
    return {str(value)}


def status_class(status: str) -> str:
    text = str(status or "").upper()
    if not text or text == "NONE":
        return "missing_status"
    if any(marker in text for marker in ["SOURCE_FAIL", "UNAVAILABLE", "SOURCE_RECHECK", "TICK_ABSENT", "MISSING", "ABSENT"]):
        return "source_stress"
    if any(marker in text for marker in ["AMBIG", "ORDER_UNRESOLVED", "INTERVAL_OPTIMISTIC", "SIDE_UNRESOLVED"]):
        return "ambiguous"
    if text.startswith("TARGET") or "TARGET_TOUCH_FIRST" in text or "CONSERVATIVE_TARGET" in text:
        return "favorable"
    if text.startswith("STOP") or "STOP_TOUCH" in text:
        return "adverse"
    if any(marker in text for marker in ["NO_TARGET_OR_STOP", "NO_TOUCH", "NOFILL_SCOPE", "UNTOUCHED", "NOFILL"]):
        return "no_resolution"
    if any(marker in text for marker in ["RECOVERED", "MARKET_PROXY_FILLED", "OFFSET_PROXY_FILLED"]):
        return "fillability_opportunity"
    if any(marker in text for marker in ["POST_SIGNAL_UNFILLED", "CONFIRMED_NOFILL", "FAR_MISS", "WITHIN_RANGE_MISS"]):
        return "fillability_failure"
    return "descriptor"


def tally_status(counter: Counter[str]) -> Counter[str]:
    out: Counter[str] = Counter()
    for status, count in counter.items():
        out[status_class(status)] += int(count)
    return out


def branch_extra_template() -> dict[str, Any]:
    return {
        "path_m15_first_touch_status_counts": Counter(),
        "path_m15_cost_model_counts": Counter(),
        "near_market_first_touch_status_counts": Counter(),
        "near_market_path_status_counts": Counter(),
        "near_market_fill_timing_status_counts": Counter(),
        "near_market_variant_counts": Counter(),
        "near_market_entry_delta_bucket_counts": Counter(),
        "near_offset_first_touch_status_counts": Counter(),
        "near_offset_policy_counts": Counter(),
        "near_offset_fill_proxy_status_counts": Counter(),
        "far_avoid_branch_status_counts": Counter(),
        "far_avoid_source_confidence_counts": Counter(),
        "far_retest_branch_status_counts": Counter(),
        "far_retest_miss_class_counts": Counter(),
        "far_retest_source_confidence_counts": Counter(),
        "far_source_confidence_counts": Counter(),
        "source_requirement_counts": Counter(),
        "source_data_availability_counts": Counter(),
        "source_requirement_surface_counts": Counter(),
        "source_requirement_action_counts": Counter(),
        "event_ids": set(),
        "cost_fill_ids": set(),
        "execution_friction_signature_ids": set(),
        "execution_friction_branch_ids": set(),
        "source_requirement_ids": set(),
        "path_control_rows": 0,
        "near_market_rows": 0,
        "near_offset_rows": 0,
        "far_avoid_rows": 0,
        "far_retest_rows": 0,
        "far_source_confidence_rows": 0,
        "source_requirement_rows": 0,
    }


def build_path_context() -> dict[tuple[str, str, str], dict[str, Any]]:
    cost_fill_by_id: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(COST_FILL_GRID_PATH):
        if row.get("_parse_error"):
            continue
        cost_fill_by_id[str(row.get("cost_fill_id"))] = row

    out: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(branch_extra_template)
    for row in read_jsonl(PATH_CONTROL_GRID_PATH):
        if row.get("_parse_error"):
            continue
        cost_fill_id = f"OHLC-GTOS-REPLAY-COSTFILL-{int(row.get('cf')):05d}"
        cost = cost_fill_by_id.get(cost_fill_id)
        if not cost:
            continue
        target_stop = f"OHLC-GTOS-PATH-TARGETSTOP-{int(row.get('tc')):03d}"
        key = key_from_parts(cost.get("route_candidate_id"), cost.get("entry_variant"), target_stop)
        bucket = out[key]
        bucket["path_m15_first_touch_status_counts"][str(row.get("st"))] += 1
        bucket["path_m15_cost_model_counts"][str(cost.get("cost_model"))] += 1
        bucket["event_ids"].update(id_set(cost.get("event_id")))
        bucket["cost_fill_ids"].add(cost_fill_id)
        bucket["path_control_rows"] += 1
    return out


def attach_branch_rows(path: Path, extras: dict[tuple[str, str, str], dict[str, Any]], loader_name: str) -> None:
    for row in read_jsonl(path):
        if row.get("_parse_error"):
            continue
        key = row_key(row)
        bucket = extras[key]
        bucket["event_ids"].update(id_set(row.get("event_id")))
        bucket["execution_friction_signature_ids"].update(id_set(row.get("execution_friction_signature_id")))
        bucket["execution_friction_branch_ids"].update(id_set(row.get("execution_friction_branch_id")))
        if loader_name == "near_market":
            bucket["near_market_rows"] += 1
            bucket["near_market_first_touch_status_counts"][str(row.get("market_first_touch_status"))] += 1
            bucket["near_market_path_status_counts"][str(row.get("market_path_status"))] += 1
            bucket["near_market_fill_timing_status_counts"][str(row.get("market_fill_timing_status"))] += 1
            bucket["near_market_variant_counts"][str(row.get("market_entry_variant"))] += 1
            bucket["near_market_entry_delta_bucket_counts"][str(row.get("market_entry_delta_bucket"))] += 1
            bucket["cost_fill_ids"].update(id_set(row.get("market_cost_fill_id")))
        elif loader_name == "near_offset":
            bucket["near_offset_rows"] += 1
            bucket["near_offset_first_touch_status_counts"][str(row.get("first_touch_status_offset_proxy"))] += 1
            bucket["near_offset_policy_counts"][str(row.get("offset_policy"))] += 1
            bucket["near_offset_fill_proxy_status_counts"][str(row.get("offset_fill_proxy_status"))] += 1
        elif loader_name == "far_avoid":
            bucket["far_avoid_rows"] += 1
            bucket["far_avoid_branch_status_counts"][str(row.get("avoid_filter_branch_status"))] += 1
            bucket["far_avoid_source_confidence_counts"][str(row.get("source_confidence_branch_status"))] += 1
        elif loader_name == "far_retest":
            bucket["far_retest_rows"] += 1
            bucket["far_retest_branch_status_counts"][str(row.get("retest_redesign_branch_status"))] += 1
            bucket["far_retest_miss_class_counts"][str(row.get("confirmed_nofill_miss_class"))] += 1
            bucket["far_retest_source_confidence_counts"][str(row.get("source_confidence_branch_status"))] += 1
        elif loader_name == "far_source_confidence":
            bucket["far_source_confidence_rows"] += 1
            bucket["far_source_confidence_counts"][str(row.get("source_confidence_branch_status"))] += 1
        elif loader_name == "source_requirement":
            bucket["source_requirement_rows"] += 1
            bucket["source_requirement_ids"].update(
                id_set(
                    row.get("source_requirement_id")
                    or row.get("near_miss_entry_control_source_requirement_id")
                    or row.get("source_requirement_row_id")
                    or row.get("unique_source_date_requirement_id")
                )
            )
            bucket["source_requirement_counts"][str(row.get("source_requirement_status"))] += 1
            bucket["source_data_availability_counts"][str(row.get("source_data_availability_status"))] += 1
            bucket["source_requirement_surface_counts"][str(row.get("source_requirement_surface"))] += 1
            bucket["source_requirement_action_counts"][str(row.get("source_requirement_action"))] += 1


def family_context_by_key() -> dict[tuple[str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in read_jsonl(FAMILY_SYNTHESIS_PATH):
        if row.get("_parse_error"):
            continue
        out[row_key(row)] = row
    return out


def compute_buckets(branch: dict[str, Any], family: dict[str, Any], extra: dict[str, Any], outcome_classes: Counter[str]) -> dict[str, str]:
    target_stop = str(branch.get("target_stop_contract_id"))
    if target_stop.startswith("TARGETSTOP_NA"):
        path_scope = "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT"
    elif extra["path_control_rows"] > 0:
        path_scope = "M15_PATH_CONTROL_JOINED"
    else:
        path_scope = "PATH_CONTROL_ABSENT_FOR_BRANCH"

    recovered = int(branch.get("recovered_signature_rows") or 0)
    confirmed = int(branch.get("confirmed_nofill_signature_rows") or 0)
    if extra["near_market_rows"] or extra["near_offset_rows"]:
        fillability = "NEAR_MISS_ENTRY_CHALLENGER_AVAILABLE"
    elif extra["far_avoid_rows"] or extra["far_retest_rows"]:
        fillability = "FAR_OR_WITHIN_RANGE_NOFILL_REDESIGN_AVAILABLE"
    elif recovered > 0 and confirmed == 0:
        fillability = "RECOVERED_FILL_EVIDENCE_DOMINANT"
    elif confirmed > recovered:
        fillability = "CONFIRMED_NOFILL_EVIDENCE_DOMINANT"
    elif outcome_classes["favorable"] > outcome_classes["adverse"]:
        fillability = "PATH_PROXY_FAVORABLE_EVIDENCE_DOMINANT"
    elif path_scope == "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT":
        fillability = "REPAIR_ONLY_FILLABILITY_SCOPE"
    else:
        fillability = "MIXED_OR_DESCRIPTOR_ONLY_FILLABILITY"

    gradient_counts = family.get("gradient_exact_spread_bucket_counts") or {}
    cost_counts = family.get("cost_sensitivity_status_counts") or {}
    if any("UNAVAILABLE" in str(key) for key in gradient_counts):
        cost = "EXACT_SPREAD_SOURCE_STRESS"
    elif any("SUPRA_STATIC" in str(key) for key in gradient_counts):
        cost = "EXACT_SPREAD_SUPRA_STATIC_STRESS"
    elif any("SENSITIVE" in str(key) for key in cost_counts):
        cost = "SPREAD_PROXY_GRADIENT_SENSITIVE"
    elif any("ZERO_TO_SPREAD" in str(key) for key in cost_counts):
        cost = "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT"
    elif any("POST_SIGNAL_UNFILLED" in str(key) for key in cost_counts):
        cost = "POST_SIGNAL_UNFILLED_COST_INVARIANT"
    else:
        cost = "COST_DESCRIPTOR_INVARIANT_OR_ABSENT"

    source_counters = Counter()
    for field in [
        "recovered_fill_source_counts",
        "source_alignment_status_counts",
    ]:
        merge_counter(source_counters, family.get(field))
    for field in [
        "far_avoid_source_confidence_counts",
        "far_retest_source_confidence_counts",
        "far_source_confidence_counts",
        "source_requirement_counts",
        "source_data_availability_counts",
    ]:
        source_counters.update(extra[field])
    if any(any(marker in str(key) for marker in ["UNAVAILABLE", "TICK_ABSENT", "SOURCE_RECHECK", "ABSENT", "MISSING"]) for key in source_counters):
        source = "SOURCE_STRESS_OR_PROXY_DOMINANT"
    elif any("EXACT" in str(key) for key in source_counters):
        source = "EXACT_SOURCE_SUPPORTED"
    elif source_counters:
        source = "PROXY_SOURCE_SUPPORTED"
    else:
        source = "SOURCE_CONTEXT_ABSENT"

    ambiguity_rows = int(branch.get("same_m15_ambiguity_rows_for_family") or 0) + outcome_classes["ambiguous"]
    if ambiguity_rows >= 100:
        ambiguity = "HIGH_SAME_M15_OR_ORDERING_AMBIGUITY"
    elif ambiguity_rows > 0:
        ambiguity = "SOME_SAME_M15_OR_ORDERING_AMBIGUITY"
    else:
        ambiguity = "NO_RECORDED_PATH_ORDERING_AMBIGUITY"

    return {
        "path_scope_bucket": path_scope,
        "fillability_bucket": fillability,
        "cost_robustness_bucket": cost,
        "source_confidence_bucket": source,
        "ambiguity_bucket": ambiguity,
    }


def implication_tags(branch: dict[str, Any], buckets: dict[str, str], extra: dict[str, Any]) -> list[str]:
    tags = set(str(action) for action in branch.get("branch_actions") or [])
    status = str(branch.get("branch_queue_status"))
    if status:
        tags.add(status)
    if buckets["fillability_bucket"] == "NEAR_MISS_ENTRY_CHALLENGER_AVAILABLE":
        tags.add("ENTRY_GEOMETRY_REDESIGN_QUEUE")
        tags.add("MARKET_ENTRY_CHALLENGER_QUEUE")
    if buckets["fillability_bucket"] == "FAR_OR_WITHIN_RANGE_NOFILL_REDESIGN_AVAILABLE":
        tags.add("AVOID_FILTER_DESIGN_QUEUE")
        tags.add("RETEST_REDESIGN_QUEUE")
    if "SOURCE_STRESS" in buckets["source_confidence_bucket"]:
        tags.add("EXACT_SOURCE_ACQUISITION_OR_PROXY_STRESS_QUEUE")
    if buckets["ambiguity_bucket"] != "NO_RECORDED_PATH_ORDERING_AMBIGUITY":
        tags.add("SAME_M15_OR_M1_ORDERING_AMBIGUITY_SPLIT_QUEUE")
    if extra["source_requirement_rows"]:
        tags.add("SIERRA_DEPTH_SOURCE_REQUIREMENT_QUEUE")
    if buckets["path_scope_bucket"] == "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT":
        tags.add("REPAIR_ENTRY_ONLY_NO_PATH_OUTCOME_QUEUE")
    if branch.get("family_sources_present"):
        tags.add("BASELINE_FAMILY_DESCRIPTOR_PRESERVED")
    return sorted(tags)


def collect_outcome_counters(family: dict[str, Any], extra: dict[str, Any]) -> dict[str, Counter[str]]:
    counters = {
        "m15_path_first_touch": extra["path_m15_first_touch_status_counts"],
        "m1_spread_first_touch": Counter(family.get("m1_first_touch_status_counts") or {}),
        "fill_bar_conservative_first_touch": Counter(family.get("fill_bar_conservative_first_touch_status_counts") or {}),
        "fill_bar_interval": Counter(family.get("fill_bar_interval_status_counts") or {}),
        "partial_repair_first_touch": Counter(family.get("partial_repair_first_touch_status_counts") or {}),
        "recovered_path": Counter(family.get("recovered_path_status_counts") or {}),
        "near_market_first_touch": extra["near_market_first_touch_status_counts"],
        "near_offset_first_touch": extra["near_offset_first_touch_status_counts"],
    }
    return counters


def score_branch(branch: dict[str, Any], family: dict[str, Any], extra: dict[str, Any], source_hash: str, seq: int) -> dict[str, Any]:
    outcome_counters = collect_outcome_counters(family, extra)
    outcome_classes: Counter[str] = Counter()
    for counter in outcome_counters.values():
        outcome_classes.update(tally_status(counter))

    descriptor_counters = [
        Counter(family.get("cost_sensitivity_status_counts") or {}),
        Counter(family.get("gradient_exact_spread_bucket_counts") or {}),
        Counter(family.get("confirmed_distance_bucket_counts") or {}),
        extra["far_avoid_branch_status_counts"],
        extra["far_retest_branch_status_counts"],
        extra["far_source_confidence_counts"],
        extra["source_requirement_counts"],
    ]
    descriptor_classes: Counter[str] = Counter()
    for counter in descriptor_counters:
        descriptor_classes.update(tally_status(counter))

    favorable = outcome_classes["favorable"]
    adverse = outcome_classes["adverse"]
    ambiguous = outcome_classes["ambiguous"]
    no_resolution = outcome_classes["no_resolution"]
    source_stress = outcome_classes["source_stress"] + descriptor_classes["source_stress"]
    fillability_failure = (
        int(branch.get("confirmed_nofill_signature_rows") or 0)
        + descriptor_classes["fillability_failure"]
        + extra["far_avoid_rows"]
        + extra["far_retest_rows"]
    )
    fillability_opportunity = (
        outcome_classes["fillability_opportunity"]
        + int(branch.get("recovered_signature_rows") or 0)
        + extra["near_market_rows"]
        + extra["near_offset_rows"]
    )
    evidence_weight = max(
        1,
        favorable
        + adverse
        + ambiguous
        + no_resolution
        + source_stress
        + fillability_failure
        + fillability_opportunity,
    )
    score = (
        favorable
        - adverse
        - (0.25 * fillability_failure)
        - (0.15 * source_stress)
        - (0.10 * ambiguous)
        + (0.15 * fillability_opportunity)
    )
    proxy_mechanical_score = round(100.0 * score / evidence_weight, 6)
    buckets = compute_buckets(branch, family, extra, outcome_classes)
    tags = implication_tags(branch, buckets, extra)
    source_event_ids = set(extra["event_ids"])
    if branch.get("route_candidate_id"):
        source_event_ids.add(str(branch["route_candidate_id"]))

    duplicate_denominator = max(1, len(source_event_ids))
    material_rows = (
        extra["path_control_rows"]
        + extra["near_market_rows"]
        + extra["near_offset_rows"]
        + extra["far_avoid_rows"]
        + extra["far_retest_rows"]
        + extra["far_source_confidence_rows"]
        + extra["source_requirement_rows"]
        + int(branch.get("m1_spread_signature_rows") or 0)
        + int(branch.get("fill_bar_stress_signature_rows") or 0)
        + int(branch.get("partial_repair_signature_scope_rows") or 0)
        + int(branch.get("confirmed_nofill_signature_rows") or 0)
        + int(branch.get("recovered_signature_rows") or 0)
    )

    return {
        "branch_proxy_score_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-SCORE-{seq:05d}",
        "branch_queue_id": branch.get("branch_queue_id"),
        "family_synthesis_id": branch.get("family_synthesis_id"),
        "route_candidate_id": branch.get("route_candidate_id"),
        "symbol": branch.get("symbol"),
        "side": branch.get("side"),
        "route_session": branch.get("route_session"),
        "entry_variant": branch.get("entry_variant"),
        "target_stop_contract_id": branch.get("target_stop_contract_id"),
        "target_multiple": branch.get("target_multiple"),
        "stop_multiple": branch.get("stop_multiple"),
        "branch_queue_status": branch.get("branch_queue_status"),
        "branch_actions": branch.get("branch_actions") or [],
        "proxy_mechanical_score": proxy_mechanical_score,
        "proxy_outcome_counts": {
            "favorable_proxy_rows": int(favorable),
            "adverse_proxy_rows": int(adverse),
            "ambiguous_proxy_rows": int(ambiguous),
            "no_resolution_proxy_rows": int(no_resolution),
            "source_stress_rows": int(source_stress),
            "fillability_failure_rows": int(fillability_failure),
            "fillability_opportunity_rows": int(fillability_opportunity),
            "evidence_weight_rows": int(evidence_weight),
        },
        "proxy_outcome_interval": {
            "lower_favorable_proxy_rows": int(favorable),
            "upper_favorable_if_ambiguity_resolves_favorable": int(favorable + ambiguous),
            "lower_adverse_proxy_rows": int(adverse),
            "upper_adverse_if_ambiguity_resolves_adverse": int(adverse + ambiguous),
        },
        "path_scope_bucket": buckets["path_scope_bucket"],
        "fillability_bucket": buckets["fillability_bucket"],
        "cost_robustness_bucket": buckets["cost_robustness_bucket"],
        "source_confidence_bucket": buckets["source_confidence_bucket"],
        "ambiguity_bucket": buckets["ambiguity_bucket"],
        "system_implication_tags": tags,
        "effective_n_fields": {
            "unique_event_or_route_ids": len(source_event_ids),
            "unique_cost_fill_ids": len(extra["cost_fill_ids"]),
            "unique_execution_friction_signature_ids": len(extra["execution_friction_signature_ids"]),
            "unique_execution_friction_branch_ids": len(extra["execution_friction_branch_ids"]),
            "unique_source_requirement_ids": len(extra["source_requirement_ids"]),
            "material_joined_rows": material_rows,
            "duplicate_inflation_ratio_material_rows_over_event_ids": round(material_rows / duplicate_denominator, 6),
        },
        "status_counters": {
            name: compact_counter(counter)
            for name, counter in {
                **outcome_counters,
                "path_m15_cost_model": extra["path_m15_cost_model_counts"],
                "near_market_path": extra["near_market_path_status_counts"],
                "near_market_fill_timing": extra["near_market_fill_timing_status_counts"],
                "near_market_variant": extra["near_market_variant_counts"],
                "near_market_entry_delta_bucket": extra["near_market_entry_delta_bucket_counts"],
                "near_offset_policy": extra["near_offset_policy_counts"],
                "near_offset_fill_proxy": extra["near_offset_fill_proxy_status_counts"],
                "far_avoid_branch": extra["far_avoid_branch_status_counts"],
                "far_avoid_source_confidence": extra["far_avoid_source_confidence_counts"],
                "far_retest_branch": extra["far_retest_branch_status_counts"],
                "far_retest_miss_class": extra["far_retest_miss_class_counts"],
                "far_retest_source_confidence": extra["far_retest_source_confidence_counts"],
                "far_source_confidence": extra["far_source_confidence_counts"],
                "source_requirement": extra["source_requirement_counts"],
                "source_data_availability": extra["source_data_availability_counts"],
                "source_requirement_surface": extra["source_requirement_surface_counts"],
                "source_requirement_action": extra["source_requirement_action_counts"],
            }.items()
        },
        "source_manifest_hash": source_hash,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_BRANCH_PROXY_SCORING",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def group_key(row: dict[str, Any], group_type: str) -> str:
    parts = group_type.split("|")
    values = []
    for part in parts:
        if part == "primary_tag":
            values.append(str((row.get("system_implication_tags") or ["NO_TAG"])[0]))
        else:
            values.append(str(row.get(part)))
    return "|".join(values)


def build_concentration_rows(branch_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    group_types = [
        "symbol",
        "side",
        "route_session",
        "symbol|side",
        "symbol|route_session",
        "route_candidate_id",
        "entry_variant",
        "target_stop_contract_id",
        "branch_queue_status",
        "fillability_bucket",
        "cost_robustness_bucket",
        "source_confidence_bucket",
        "ambiguity_bucket",
        "primary_tag",
        "route_candidate_id|entry_variant",
        "route_candidate_id|target_stop_contract_id",
    ]
    total = max(1, len(branch_rows))
    rows: list[dict[str, Any]] = []
    seq = 0
    for group_type in group_types:
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in branch_rows:
            buckets[group_key(row, group_type)].append(row)
        for key in sorted(buckets):
            group = buckets[key]
            seq += 1
            rows.append(
                {
                    "concentration_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-CONC-{seq:05d}",
                    "generated_utc": generated_at,
                    "group_type": group_type,
                    "group_key": key,
                    "branch_count": len(group),
                    "branch_share": round(len(group) / total, 9),
                    "unique_route_candidate_count": len({str(row.get("route_candidate_id")) for row in group}),
                    "unique_event_or_route_id_count": sum(row["effective_n_fields"]["unique_event_or_route_ids"] for row in group),
                    "proxy_score_sum": round(sum(float(row["proxy_mechanical_score"]) for row in group), 6),
                    "proxy_score_mean": round(sum(float(row["proxy_mechanical_score"]) for row in group) / len(group), 6),
                    "favorable_proxy_rows": sum(row["proxy_outcome_counts"]["favorable_proxy_rows"] for row in group),
                    "adverse_proxy_rows": sum(row["proxy_outcome_counts"]["adverse_proxy_rows"] for row in group),
                    "ambiguous_proxy_rows": sum(row["proxy_outcome_counts"]["ambiguous_proxy_rows"] for row in group),
                    "source_stress_rows": sum(row["proxy_outcome_counts"]["source_stress_rows"] for row in group),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def build_duplicate_rows(branch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for seq, row in enumerate(branch_rows, 1):
        fields = row["effective_n_fields"]
        rows.append(
            {
                "duplicate_effective_n_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-EFFN-{seq:05d}",
                "branch_proxy_score_id": row["branch_proxy_score_id"],
                "branch_queue_id": row["branch_queue_id"],
                "route_candidate_id": row["route_candidate_id"],
                "entry_variant": row["entry_variant"],
                "target_stop_contract_id": row["target_stop_contract_id"],
                "unique_event_or_route_ids": fields["unique_event_or_route_ids"],
                "unique_cost_fill_ids": fields["unique_cost_fill_ids"],
                "unique_execution_friction_signature_ids": fields["unique_execution_friction_signature_ids"],
                "unique_source_requirement_ids": fields["unique_source_requirement_ids"],
                "material_joined_rows": fields["material_joined_rows"],
                "duplicate_inflation_ratio_material_rows_over_event_ids": fields[
                    "duplicate_inflation_ratio_material_rows_over_event_ids"
                ],
                "duplicate_control_boundary": "Use branch rows as exhaustive design rows; use effective-N fields when interpreting concentration or duplicate inflation.",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_action_rows(branch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    seq = 0
    for row in branch_rows:
        actions = row.get("branch_actions") or ["NO_BRANCH_ACTION_RECORDED"]
        for action in actions:
            seq += 1
            rows.append(
                {
                    "action_score_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-ACTION-{seq:05d}",
                    "branch_proxy_score_id": row["branch_proxy_score_id"],
                    "branch_queue_id": row["branch_queue_id"],
                    "route_candidate_id": row["route_candidate_id"],
                    "entry_variant": row["entry_variant"],
                    "target_stop_contract_id": row["target_stop_contract_id"],
                    "branch_action": action,
                    "proxy_mechanical_score": row["proxy_mechanical_score"],
                    "proxy_outcome_counts": row["proxy_outcome_counts"],
                    "fillability_bucket": row["fillability_bucket"],
                    "cost_robustness_bucket": row["cost_robustness_bucket"],
                    "source_confidence_bucket": row["source_confidence_bucket"],
                    "ambiguity_bucket": row["ambiguity_bucket"],
                    "implementation_tags": row["system_implication_tags"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def build_implementation_rows(branch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    seq = 0
    for row in branch_rows:
        for tag in row.get("system_implication_tags") or ["NO_IMPLEMENTATION_TAG"]:
            seq += 1
            rows.append(
                {
                    "implementation_implication_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-IMPL-{seq:05d}",
                    "branch_proxy_score_id": row["branch_proxy_score_id"],
                    "branch_queue_id": row["branch_queue_id"],
                    "route_candidate_id": row["route_candidate_id"],
                    "symbol": row["symbol"],
                    "side": row["side"],
                    "route_session": row["route_session"],
                    "entry_variant": row["entry_variant"],
                    "target_stop_contract_id": row["target_stop_contract_id"],
                    "implementation_tag": tag,
                    "fillability_bucket": row["fillability_bucket"],
                    "source_confidence_bucket": row["source_confidence_bucket"],
                    "ambiguity_bucket": row["ambiguity_bucket"],
                    "mechanical_next_step": next_step_for_tag(tag),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def next_step_for_tag(tag: str) -> str:
    if "ENTRY_GEOMETRY" in tag:
        return "Compute retest-limit offset and market-entry challenger controls on full affected branch cohort."
    if "MARKET_ENTRY" in tag:
        return "Compare signal-close and next-bar-open market-entry proxy paths against retained retest-limit source rows."
    if "AVOID_FILTER" in tag:
        return "Translate far-miss evidence into avoid-filter predicates and same-context controls before any code change."
    if "RETEST_REDESIGN" in tag:
        return "Expand retest redesign offsets and zone definitions for all affected far/within-range no-fill rows."
    if "SOURCE" in tag or "SIERRA" in tag:
        return "Acquire or materialize exact depth/tick source dates where available; otherwise preserve proxy stress split."
    if "AMBIGUITY" in tag or "ORDERING" in tag:
        return "Run lower-timeframe or exact-tick ordering stress where source exists; otherwise maintain interval bounds."
    if "REPAIR_ENTRY_ONLY" in tag:
        return "Keep as source-repair entry branch until a target/stop contract can be bound."
    return "Preserve branch evidence and feed next same-resource computation queue."


def build_bucket_rows(branch_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    bucket_fields = [
        "path_scope_bucket",
        "fillability_bucket",
        "cost_robustness_bucket",
        "source_confidence_bucket",
        "ambiguity_bucket",
    ]
    rows = []
    seq = 0
    for field in bucket_fields:
        counts = Counter(str(row.get(field)) for row in branch_rows)
        for value in sorted(counts):
            seq += 1
            affected = [row for row in branch_rows if str(row.get(field)) == value]
            rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-BUCKET-{seq:05d}",
                    "generated_utc": generated_at,
                    "bucket_field": field,
                    "bucket_value": value,
                    "branch_count": counts[value],
                    "unique_route_candidate_count": len({str(row.get("route_candidate_id")) for row in affected}),
                    "favorable_proxy_rows": sum(row["proxy_outcome_counts"]["favorable_proxy_rows"] for row in affected),
                    "adverse_proxy_rows": sum(row["proxy_outcome_counts"]["adverse_proxy_rows"] for row in affected),
                    "source_stress_rows": sum(row["proxy_outcome_counts"]["source_stress_rows"] for row in affected),
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )
    return rows


def build_question_rows(branch_rows: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    question_specs = [
        (
            "Which exact-spread source gaps remain after branch scoring?",
            lambda row: "SOURCE_STRESS" in row["source_confidence_bucket"] or "EXACT_SPREAD" in row["cost_robustness_bucket"],
            "source_repair",
        ),
        (
            "Which retest-limit branches are mechanically dominated by no-fill evidence?",
            lambda row: row["fillability_bucket"] in {"CONFIRMED_NOFILL_EVIDENCE_DOMINANT", "FAR_OR_WITHIN_RANGE_NOFILL_REDESIGN_AVAILABLE"},
            "fillability_repair",
        ),
        (
            "Which branches need lower-timeframe or tick ordering to collapse ambiguity intervals?",
            lambda row: row["ambiguity_bucket"] != "NO_RECORDED_PATH_ORDERING_AMBIGUITY",
            "ordering_repair",
        ),
        (
            "Which branches have market-entry or offset challengers already computable?",
            lambda row: row["fillability_bucket"] == "NEAR_MISS_ENTRY_CHALLENGER_AVAILABLE",
            "entry_geometry_challenger",
        ),
        (
            "Which branches are repair-entry-only without target/stop contracts?",
            lambda row: row["path_scope_bucket"] == "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT",
            "target_stop_binding_repair",
        ),
        (
            "Which branches carry high duplicate inflation and need effective-N weighting?",
            lambda row: row["effective_n_fields"]["duplicate_inflation_ratio_material_rows_over_event_ids"] >= 25,
            "duplicate_effective_n_control",
        ),
        (
            "Which branches have favorable proxy path evidence but source stress still blocks exact interpretation?",
            lambda row: row["proxy_outcome_counts"]["favorable_proxy_rows"] > row["proxy_outcome_counts"]["adverse_proxy_rows"]
            and "SOURCE_STRESS" in row["source_confidence_bucket"],
            "favorable_with_source_stress",
        ),
        (
            "Which branches have adverse proxy path evidence that should feed avoid/redesign hypotheses?",
            lambda row: row["proxy_outcome_counts"]["adverse_proxy_rows"] > row["proxy_outcome_counts"]["favorable_proxy_rows"],
            "adverse_path_hypothesis",
        ),
    ]
    rows = []
    for seq, (question, predicate, track) in enumerate(question_specs, 1):
        affected = [row for row in branch_rows if predicate(row)]
        rows.append(
            {
                "question_id": f"OHLC-GTOS-COST-FILL-PATH-BRANCH-PROXY-Q-{seq:03d}",
                "generated_utc": generated_at,
                "question": question,
                "track": track,
                "affected_branch_count": len(affected),
                "affected_unique_route_candidate_count": len({str(row.get("route_candidate_id")) for row in affected}),
                "affected_branch_queue_ids": [row["branch_queue_id"] for row in affected],
                "not_completion": True,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def sierra_source_manifest_counts() -> dict[str, Any]:
    manifest = read_json(SIERRA_SOURCE_DATE_MANIFEST_PATH)
    if not manifest:
        return {"manifest_status": "MISSING_FAIL_CLOSED"}
    counts = dict(manifest.get("counts") or {})
    counts["local_acquisition_classification_counts"] = manifest.get("local_acquisition_classification_counts") or {}
    counts["candidate_relation_counts"] = manifest.get("candidate_relation_counts") or {}
    counts["root_permission_state_counts"] = manifest.get("root_permission_state_counts") or {}
    return counts


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    output_artifact_names = {
        RESULT_PATH.name,
        BRANCH_SCORE_PATH.name,
        ACTION_SCORE_PATH.name,
        CONCENTRATION_PATH.name,
        DUPLICATE_EFFECTIVE_N_PATH.name,
        IMPLEMENTATION_PATH.name,
        BUCKET_PATH.name,
        QUESTION_PATH.name,
        SUMMARY_PATH.name,
    }
    existing_outputs = [row for row in manifest.get("outputs", []) if row.get("artifact") not in output_artifact_names]
    for artifact_path, artifact_type in [
        (RESULT_PATH, "result"),
        (BRANCH_SCORE_PATH, "branch_score_ledger"),
        (ACTION_SCORE_PATH, "action_score_ledger"),
        (CONCENTRATION_PATH, "concentration_ledger"),
        (DUPLICATE_EFFECTIVE_N_PATH, "duplicate_effective_n_ledger"),
        (IMPLEMENTATION_PATH, "implementation_implication_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]:
        existing_outputs.append(
            {
                "artifact": artifact_path.name,
                "category": "historical_ohlc_gtos_replay_cost_fill_path_branch_proxy_scoring",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": outputs["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_artifacts = [
        row for row in manifest.get("artifacts", []) if row.get("path") not in {
            str(path.relative_to(REPO)).replace("\\", "/")
            for path in [
                RESULT_PATH,
                BRANCH_SCORE_PATH,
                ACTION_SCORE_PATH,
                CONCENTRATION_PATH,
                DUPLICATE_EFFECTIVE_N_PATH,
                IMPLEMENTATION_PATH,
                BUCKET_PATH,
                QUESTION_PATH,
                SUMMARY_PATH,
                Path(__file__).resolve(),
            ]
        }
    ]
    for path, artifact_type in [
        (Path(__file__).resolve(), "branch_proxy_scoring_builder"),
        (RESULT_PATH, "branch_proxy_scoring_result"),
        (BRANCH_SCORE_PATH, "branch_proxy_scoring_branch_score_ledger"),
        (ACTION_SCORE_PATH, "branch_proxy_scoring_action_score_ledger"),
        (CONCENTRATION_PATH, "branch_proxy_scoring_concentration_ledger"),
        (DUPLICATE_EFFECTIVE_N_PATH, "branch_proxy_scoring_duplicate_effective_n_ledger"),
        (IMPLEMENTATION_PATH, "branch_proxy_scoring_implementation_implication_ledger"),
        (BUCKET_PATH, "branch_proxy_scoring_bucket_ledger"),
        (QUESTION_PATH, "branch_proxy_scoring_question_ledger"),
        (SUMMARY_PATH, "branch_proxy_scoring_summary"),
    ]:
        existing_artifacts.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "status": "created",
                "type": artifact_type,
            }
        )
    manifest["outputs"] = existing_outputs
    manifest["artifacts"] = existing_artifacts
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_cost_fill_path_branch_proxy_scoring",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def append_subagent_ledger_if_needed(generated_at: str) -> None:
    if not SUBAGENT_LEDGER_PATH.exists():
        return
    existing = SUBAGENT_LEDGER_PATH.read_text(encoding="utf-8", errors="replace")
    if "019e2f48-e38c-7e41-8fbc-b516b22815d1" in existing:
        return
    row = {
        "ts_utc": generated_at,
        "event_type": "return_integrated_from_tool_advice",
        "status": "completed_integrated_advisory",
        "agent_id": "019e2f48-e38c-7e41-8fbc-b516b22815d1",
        "nickname": "Banach",
        "track": "branch_proxy_scoring_design_review",
        "reasoning_effort_required": "xhigh",
        "integration_evidence": "Completed read-only design advice in parent tool return; no file artifact claimed. Incorporated stable join key, no top-N, targetstop-NA repair-only handling, and per-branch proxy outcome interval guidance.",
        "safe_flags": SAFE_FLAGS,
    }
    with SUBAGENT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    counts = result["counts"]
    lines = [
        "# Historical OHLC GTOS Replay Cost/Fill/Path Branch Proxy Scoring",
        "",
        f"Generated UTC: {result['generated_utc']}",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
        f"- Branch score rows: {counts['branch_score_rows']}",
        f"- Action score rows: {counts['action_score_rows']}",
        f"- Concentration rows: {counts['concentration_rows']}",
        f"- Duplicate/effective-N rows: {counts['duplicate_effective_n_rows']}",
        f"- Implementation implication rows: {counts['implementation_implication_rows']}",
        f"- Bucket rows: {counts['bucket_rows']}",
        f"- Question rows: {counts['question_rows']}",
        f"- Repair-entry-only rows: {counts['repair_entry_only_rows']}",
        "",
        "## Bucket Distributions",
        "",
    ]
    for field, distribution in result["bucket_distributions"].items():
        lines.append(f"### {field}")
        for key, value in distribution.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    lines.extend(
        [
            "## Active Next Questions",
            "",
            "The question ledger preserves all generated question rows with affected branch IDs. It is an execution queue, not a completion packet.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, source_hash = source_manifest()
    branch_queue = [row for row in read_jsonl(BRANCH_QUEUE_PATH) if not row.get("_parse_error")]
    families = family_context_by_key()
    extras = build_path_context()
    attach_branch_rows(NEAR_MARKET_ENTRY_PATH, extras, "near_market")
    attach_branch_rows(NEAR_OFFSET_PATH, extras, "near_offset")
    attach_branch_rows(FAR_AVOID_PATH, extras, "far_avoid")
    attach_branch_rows(FAR_RETEST_PATH, extras, "far_retest")
    attach_branch_rows(FAR_SOURCE_CONFIDENCE_PATH, extras, "far_source_confidence")
    attach_branch_rows(NEAR_SOURCE_REQUIREMENT_PATH, extras, "source_requirement")

    branch_score_rows: list[dict[str, Any]] = []
    for seq, branch in enumerate(branch_queue, 1):
        key = row_key(branch)
        family = families.get(key, {})
        extra = extras.get(key, branch_extra_template())
        branch_score_rows.append(score_branch(branch, family, extra, source_hash, seq))

    action_rows = build_action_rows(branch_score_rows)
    concentration_rows = build_concentration_rows(branch_score_rows, generated_at)
    duplicate_rows = build_duplicate_rows(branch_score_rows)
    implementation_rows = build_implementation_rows(branch_score_rows)
    bucket_rows = build_bucket_rows(branch_score_rows, generated_at)
    question_rows = build_question_rows(branch_score_rows, generated_at)

    write_jsonl(BRANCH_SCORE_PATH, branch_score_rows)
    write_jsonl(ACTION_SCORE_PATH, action_rows)
    write_jsonl(CONCENTRATION_PATH, concentration_rows)
    write_jsonl(DUPLICATE_EFFECTIVE_N_PATH, duplicate_rows)
    write_jsonl(IMPLEMENTATION_PATH, implementation_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)

    bucket_fields = [
        "path_scope_bucket",
        "fillability_bucket",
        "cost_robustness_bucket",
        "source_confidence_bucket",
        "ambiguity_bucket",
    ]
    bucket_distributions = {field: compact_counter(Counter(str(row[field]) for row in branch_score_rows)) for field in bucket_fields}
    action_counts = compact_counter(Counter(action for row in branch_score_rows for action in row.get("branch_actions") or []))
    implication_counts = compact_counter(Counter(tag for row in branch_score_rows for tag in row.get("system_implication_tags") or []))
    counts = {
        "input_branch_queue_rows": len(branch_queue),
        "branch_score_rows": len(branch_score_rows),
        "action_score_rows": len(action_rows),
        "concentration_rows": len(concentration_rows),
        "duplicate_effective_n_rows": len(duplicate_rows),
        "implementation_implication_rows": len(implementation_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "repair_entry_only_rows": sum(1 for row in branch_score_rows if row["path_scope_bucket"] == "REPAIR_ENTRY_ONLY_NO_TARGET_STOP_CONTRACT"),
        "joined_path_control_rows": sum(row["effective_n_fields"]["unique_cost_fill_ids"] for row in branch_score_rows),
        "source_manifest_rows": len(manifest_rows),
    }
    result = {
        "generated_utc": generated_at,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "artifact": RESULT_PATH.name,
        "source_manifest": manifest_rows,
        "source_manifest_hash": source_hash,
        "counts": counts,
        "bucket_distributions": bucket_distributions,
        "branch_queue_status_counts": compact_counter(Counter(str(row.get("branch_queue_status")) for row in branch_score_rows)),
        "action_counts": action_counts,
        "implementation_tag_counts": implication_counts,
        "proxy_outcome_count_sums": {
            key: sum(row["proxy_outcome_counts"][key] for row in branch_score_rows)
            for key in [
                "favorable_proxy_rows",
                "adverse_proxy_rows",
                "ambiguous_proxy_rows",
                "no_resolution_proxy_rows",
                "source_stress_rows",
                "fillability_failure_rows",
                "fillability_opportunity_rows",
                "evidence_weight_rows",
            ]
        },
        "score_summary": {
            "min_proxy_mechanical_score": min(float(row["proxy_mechanical_score"]) for row in branch_score_rows),
            "max_proxy_mechanical_score": max(float(row["proxy_mechanical_score"]) for row in branch_score_rows),
            "mean_proxy_mechanical_score": round(
                sum(float(row["proxy_mechanical_score"]) for row in branch_score_rows) / max(1, len(branch_score_rows)),
                6,
            ),
        },
        "external_source_acquisition_counts": {
            "sierra_exact_source_date_manifest": sierra_source_manifest_counts(),
        },
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    append_subagent_ledger_if_needed(generated_at)
    print(json.dumps({"artifact": str(RESULT_PATH), "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
