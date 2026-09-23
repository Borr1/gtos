#!/usr/bin/env python3
"""Recompute SOURCE branch proxy descriptors with materialized local bar spreads."""

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

SOURCE_DETAIL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_RESULT_2026-05-16.json"
SOURCE_DETAIL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_DETAIL_WINDOW = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_COST_CAP_ACQUISITION_DETAIL_WINDOW_LEDGER_2026-05-16.jsonl"
SOURCE_WINDOW_MATERIALIZATION_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION_RESULT_2026-05-16.json"
SOURCE_WINDOW_MATERIALIZATION_WINDOW = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_WINDOW_MATERIALIZATION_WINDOW_LEDGER_2026-05-16.jsonl"
SPREAD_STRESS_BOUND = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPREAD_STRESS_BOUND_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_LEDGER_2026-05-16.jsonl"
WINDOW_LEDGER = ROUTE_DIR / f"{PREFIX}_WINDOW_LEDGER_2026-05-16.jsonl"
ACCEPTED_LEDGER = ROUTE_DIR / f"{PREFIX}_ACCEPTED_LEDGER_2026-05-16.jsonl"
REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_LEDGER_2026-05-16.jsonl"
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
    "SOURCE bar-spread recompute packet only. It uses local bar spread proxy rows "
    "materialized from owned files to select lower-level source descriptors inside the "
    "historical SOURCE queue. It does not change live behavior and does not claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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
                "source_manifest_id": f"OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-SRC-{index:04d}",
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


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def descriptor_to_r(descriptor: str | None, target_multiple: Any, stop_multiple: Any) -> float | None:
    target = as_float(target_multiple)
    stop = as_float(stop_multiple)
    if descriptor is None:
        return None
    if descriptor == "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS":
        return None
    if "TARGET_TOUCH" in descriptor and target is not None:
        return target
    if "STOP_TOUCH" in descriptor and stop is not None:
        return -stop
    if descriptor == "NO_TARGET_OR_STOP_TOUCH_WITHIN_CONTRACT_HORIZON":
        return 0.0
    return None


def choose_spread_scale(raw_spread: float | None, low: float | None, high: float | None) -> tuple[float | None, float | None, str]:
    if raw_spread is None or low is None or high is None:
        return None, None, "BAR_SPREAD_SCALE_UNAVAILABLE"
    candidates = [(1.0, raw_spread), (0.1, raw_spread * 0.1), (0.01, raw_spread * 0.01)]

    def distance(value: float) -> float:
        if low <= value <= high:
            return 0.0
        return min(abs(value - low), abs(value - high))

    scale, normalized = min(candidates, key=lambda item: distance(item[1]))
    if scale == 1.0:
        return scale, normalized, "BAR_SPREAD_RAW_UNITS_MATCH_PROXY"
    if scale == 0.1:
        return scale, normalized, "BAR_SPREAD_POINTS_TO_PROXY_SCALE_0_1"
    return scale, normalized, "BAR_SPREAD_POINTS_TO_PROXY_SCALE_0_01"


def spread_position(normalized: float | None, low: float | None, high: float | None) -> str:
    if normalized is None or low is None or high is None:
        return "BAR_SPREAD_POSITION_UNAVAILABLE"
    tolerance = 1e-9
    if abs(normalized - low) <= tolerance:
        return "BAR_SPREAD_EXACT_LOW_STRESS"
    if abs(normalized - high) <= tolerance:
        return "BAR_SPREAD_EXACT_HIGH_STRESS"
    if normalized < low:
        return "BAR_SPREAD_BELOW_LOW_STRESS"
    if normalized > high:
        return "BAR_SPREAD_ABOVE_HIGH_STRESS"
    return "BAR_SPREAD_INSIDE_TESTED_INTERVAL"


def select_descriptor(position: str, low_descriptor: str | None, high_descriptor: str | None) -> tuple[str | None, str]:
    if position in {"BAR_SPREAD_BELOW_LOW_STRESS", "BAR_SPREAD_EXACT_LOW_STRESS"}:
        return low_descriptor, "BAR_SPREAD_DESCRIPTOR_SELECTED_LOW_BOUND"
    if position in {"BAR_SPREAD_ABOVE_HIGH_STRESS", "BAR_SPREAD_EXACT_HIGH_STRESS"}:
        return high_descriptor, "BAR_SPREAD_DESCRIPTOR_SELECTED_HIGH_BOUND"
    if position == "BAR_SPREAD_INSIDE_TESTED_INTERVAL":
        if low_descriptor == high_descriptor:
            return low_descriptor, "BAR_SPREAD_DESCRIPTOR_STABLE_INSIDE_INTERVAL"
        return "BAR_SPREAD_INTERVAL_INTERIOR_DESCRIPTOR_UNRESOLVED_USE_BOUNDS", "BAR_SPREAD_DESCRIPTOR_INTERIOR_UNRESOLVED"
    return None, "BAR_SPREAD_DESCRIPTOR_UNAVAILABLE"


def sign_class(values: list[float]) -> str:
    if not values:
        return "BAR_PROXY_NO_SCALAR"
    if all(value > 0 for value in values):
        return "BAR_PROXY_ALL_POSITIVE"
    if all(value < 0 for value in values):
        return "BAR_PROXY_ALL_NEGATIVE"
    if any(value > 0 for value in values) and any(value < 0 for value in values):
        return "BAR_PROXY_STRADDLES_ZERO"
    return "BAR_PROXY_TOUCHES_ZERO_OR_MIXED"


def branch_decision(original_binary: str | None, mean_r: float | None, unresolved_rows: int) -> str:
    if mean_r is None:
        return "BAR_PROXY_NO_SCALAR_DECISION"
    if unresolved_rows:
        if original_binary == "ACCEPTED" and mean_r > 0:
            return "BAR_PROXY_PARTIAL_SCALAR_ACCEPTED_SUPPORTS_WITH_M15_AMBIGUITY"
        if original_binary == "ACCEPTED" and mean_r <= 0:
            return "BAR_PROXY_PARTIAL_SCALAR_ACCEPTED_DEGRADED_REVIEW_WITH_M15_AMBIGUITY"
        if original_binary == "REJECTED" and mean_r > 0:
            return "BAR_PROXY_PARTIAL_SCALAR_REPAIR_UPGRADED_REVIEW_WITH_M15_AMBIGUITY"
        if original_binary == "REJECTED" and mean_r <= 0:
            return "BAR_PROXY_PARTIAL_SCALAR_REPAIR_SUPPORTS_WITH_M15_AMBIGUITY"
    if original_binary == "ACCEPTED" and mean_r > 0:
        return "BAR_PROXY_ACCEPTED_CONFIRMED"
    if original_binary == "ACCEPTED" and mean_r <= 0:
        return "BAR_PROXY_ACCEPTED_DEGRADED_TO_REPAIR"
    if original_binary == "REJECTED" and mean_r > 0:
        return "BAR_PROXY_REPAIR_UPGRADED_TO_CHALLENGER_REVIEW"
    if original_binary == "REJECTED" and mean_r <= 0:
        return "BAR_PROXY_REPAIR_CONFIRMED"
    return "BAR_PROXY_DECISION_UNCLASSIFIED"


def main() -> int:
    generated_at = now_utc()
    source_detail_result = read_json(SOURCE_DETAIL_RESULT)
    source_window_materialization_result = read_json(SOURCE_WINDOW_MATERIALIZATION_RESULT)
    branch_rows = read_jsonl(SOURCE_DETAIL_BRANCH)
    source_window_rows = read_jsonl(SOURCE_DETAIL_WINDOW)
    materialized_window_rows = read_jsonl(SOURCE_WINDOW_MATERIALIZATION_WINDOW)
    stress_rows = read_jsonl(SPREAD_STRESS_BOUND)
    stress_by_signature = {row.get("cost_sensitivity_signature_id"): row for row in stress_rows}
    materialized_by_key = {row.get("source_window_key"): row for row in materialized_window_rows}
    branch_by_id = {row.get("branch_queue_id"): row for row in branch_rows}
    source_manifest, manifest_hash = source_manifest_rows(
        [
            SOURCE_DETAIL_RESULT,
            SOURCE_DETAIL_BRANCH,
            SOURCE_DETAIL_WINDOW,
            SOURCE_WINDOW_MATERIALIZATION_RESULT,
            SOURCE_WINDOW_MATERIALIZATION_WINDOW,
            SPREAD_STRESS_BOUND,
        ],
        generated_at,
    )

    recompute_window_rows: list[dict[str, Any]] = []
    windows_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_window_rows:
        signature_id = row.get("cost_sensitivity_signature_id")
        stress = stress_by_signature.get(signature_id, {})
        materialized = materialized_by_key.get(row.get("source_window_key"), {})
        raw_spread = as_float(materialized.get("best_candidate_spread_min"))
        low_spread = as_float(stress.get("tested_low_spread_proxy_value"))
        high_spread = as_float(stress.get("tested_high_spread_proxy_value"))
        scale, normalized_spread, scale_class = choose_spread_scale(raw_spread, low_spread, high_spread)
        position = spread_position(normalized_spread, low_spread, high_spread)
        descriptor, descriptor_selection = select_descriptor(
            position,
            stress.get("low_spread_descriptor_status"),
            stress.get("high_spread_descriptor_status"),
        )
        r_proxy = descriptor_to_r(descriptor, stress.get("target_multiple"), stress.get("stop_multiple"))
        recompute_status = "BAR_SPREAD_PROXY_DESCRIPTOR_SELECTED"
        if descriptor_selection == "BAR_SPREAD_DESCRIPTOR_INTERIOR_UNRESOLVED":
            recompute_status = "BAR_SPREAD_PROXY_DESCRIPTOR_UNRESOLVED_PRESERVE_BOUNDS"
        elif descriptor == "TARGET_AND_STOP_TOUCH_SAME_M15_BAR_AMBIGUOUS":
            recompute_status = "BAR_SPREAD_PROXY_DESCRIPTOR_SELECTED_M15_ORDER_UNRESOLVED"
        matched_branch_ids = [branch_id for branch_id in row.get("matched_source_detail_branches", []) if branch_id in branch_by_id]
        out = {
            "source_bar_spread_window_recompute_id": f"OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-WINDOW-{len(recompute_window_rows) + 1:05d}",
            "source_cost_cap_window_detail_id": row.get("source_cost_cap_window_detail_id"),
            "source_window_key": row.get("source_window_key"),
            "cost_sensitivity_signature_id": signature_id,
            "symbol": row.get("symbol"),
            "route_candidate_id": stress.get("route_candidate_id"),
            "entry_variant": stress.get("entry_variant"),
            "target_stop_contract_id": stress.get("target_stop_contract_id"),
            "target_multiple": stress.get("target_multiple"),
            "stop_multiple": stress.get("stop_multiple"),
            "source_detail_window_scope": row.get("source_detail_window_scope"),
            "materialization_status": materialized.get("materialization_status"),
            "source_descriptor_recompute_state": materialized.get("source_descriptor_recompute_state"),
            "best_candidate_path": materialized.get("best_candidate_path"),
            "best_candidate_timeframe": materialized.get("best_candidate_timeframe"),
            "observed_bar_spread_raw": raw_spread,
            "tested_low_spread_proxy_value": low_spread,
            "tested_high_spread_proxy_value": high_spread,
            "bar_spread_scale": scale,
            "bar_spread_normalized_proxy_value": normalized_spread,
            "bar_spread_scale_class": scale_class,
            "bar_spread_position_vs_stress": position,
            "low_spread_descriptor_status": stress.get("low_spread_descriptor_status"),
            "high_spread_descriptor_status": stress.get("high_spread_descriptor_status"),
            "bar_spread_descriptor_status": descriptor,
            "bar_spread_descriptor_selection": descriptor_selection,
            "bar_spread_rstyle_proxy": r_proxy,
            "bar_spread_recompute_status": recompute_status,
            "matched_source_detail_branch_count": len(matched_branch_ids),
            "matched_source_detail_branches": matched_branch_ids,
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        recompute_window_rows.append(out)
        for branch_id in matched_branch_ids:
            windows_by_branch[branch_id].append(out)

    recompute_branch_rows: list[dict[str, Any]] = []
    for branch in branch_rows:
        branch_id = branch.get("branch_queue_id")
        matched_windows = windows_by_branch.get(branch_id, [])
        r_values = [row["bar_spread_rstyle_proxy"] for row in matched_windows if row.get("bar_spread_rstyle_proxy") is not None]
        unresolved = sum(1 for row in matched_windows if row.get("bar_spread_recompute_status") != "BAR_SPREAD_PROXY_DESCRIPTOR_SELECTED")
        mean_r = round(mean(r_values), 6) if r_values else None
        min_r = round(min(r_values), 6) if r_values else None
        max_r = round(max(r_values), 6) if r_values else None
        sign = sign_class(r_values)
        decision = branch_decision(branch.get("branch_result_binary"), mean_r, unresolved)
        branch_out = {
            "source_bar_spread_branch_recompute_id": f"OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-BRANCH-{len(recompute_branch_rows) + 1:05d}",
            "branch_queue_id": branch_id,
            "source_cost_cap_detail_branch_id": branch.get("source_cost_cap_detail_branch_id"),
            "branch_result_binary": branch.get("branch_result_binary"),
            "primary_export_family": branch.get("primary_export_family"),
            "route_candidate_id": branch.get("route_candidate_id"),
            "route_session": branch.get("route_session"),
            "symbol": branch.get("symbol"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "source_cost_cap_detail_status": branch.get("source_cost_cap_detail_status"),
            "source_cost_interval_sign_class": branch.get("source_cost_interval_sign_class"),
            "source_detail_scope": branch.get("source_detail_scope"),
            "source_scalar_permission": branch.get("source_scalar_permission"),
            "source_builder_result_status": branch.get("source_builder_result_status"),
            "source_acquisition_state_before_bar_proxy": branch.get("source_acquisition_state"),
            "bar_spread_materialized_window_rows": len(matched_windows),
            "bar_spread_scalar_rows": len(r_values),
            "bar_spread_unresolved_rows": unresolved,
            "bar_spread_descriptor_counts": compact_counter(Counter(row.get("bar_spread_descriptor_status") for row in matched_windows)),
            "bar_spread_position_counts": compact_counter(Counter(row.get("bar_spread_position_vs_stress") for row in matched_windows)),
            "bar_spread_scale_class_counts": compact_counter(Counter(row.get("bar_spread_scale_class") for row in matched_windows)),
            "bar_spread_rstyle_mean": mean_r,
            "bar_spread_rstyle_min": min_r,
            "bar_spread_rstyle_max": max_r,
            "bar_spread_sign_class": sign,
            "bar_spread_recompute_decision": decision,
            "bar_spread_delta_vs_source_midpoint": round(mean_r - as_float(branch.get("rstyle_midpoint_mean")), 6)
            if mean_r is not None and as_float(branch.get("rstyle_midpoint_mean")) is not None
            else None,
            "bar_spread_delta_vs_source_lower": round(mean_r - as_float(branch.get("rstyle_lower_mean")), 6)
            if mean_r is not None and as_float(branch.get("rstyle_lower_mean")) is not None
            else None,
            "bar_spread_delta_vs_source_upper": round(mean_r - as_float(branch.get("rstyle_upper_mean")), 6)
            if mean_r is not None and as_float(branch.get("rstyle_upper_mean")) is not None
            else None,
            "next_same_resource_action": (
                "ROUTE_BAR_PROXY_UPGRADED_REPAIR_TO_CHALLENGER_REVIEW"
                if "UPGRADED" in decision
                else "USE_BAR_PROXY_SOURCE_DESCRIPTOR_IN_NEXT_SOURCE_BRANCH_SPLIT"
            ),
            "m15_exact_chronology_claim": False,
            "m1_exact_chronology_claim": False,
            "m1_tick_ordering_exact": False,
            "exact_tick_recompute_state": "EXACT_TICK_STILL_UNAVAILABLE_BAR_SPREAD_PROXY_USED",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        recompute_branch_rows.append(branch_out)

    accepted_rows = [row for row in recompute_branch_rows if row.get("branch_result_binary") == "ACCEPTED"]
    repair_rows = [row for row in recompute_branch_rows if row.get("branch_result_binary") == "REJECTED"]
    bucket_sources = {
        "branch_result_binary": Counter(row.get("branch_result_binary") for row in recompute_branch_rows),
        "bar_spread_sign_class": Counter(row.get("bar_spread_sign_class") for row in recompute_branch_rows),
        "bar_spread_recompute_decision": Counter(row.get("bar_spread_recompute_decision") for row in recompute_branch_rows),
        "source_cost_cap_detail_status": Counter(row.get("source_cost_cap_detail_status") for row in recompute_branch_rows),
        "bar_spread_position_vs_stress": Counter(row.get("bar_spread_position_vs_stress") for row in recompute_window_rows),
        "bar_spread_scale_class": Counter(row.get("bar_spread_scale_class") for row in recompute_window_rows),
        "bar_spread_descriptor_status": Counter(row.get("bar_spread_descriptor_status") for row in recompute_window_rows),
        "bar_spread_recompute_status": Counter(row.get("bar_spread_recompute_status") for row in recompute_window_rows),
        "materialization_status": Counter(row.get("materialization_status") for row in recompute_window_rows),
    }
    bucket_rows = []
    for category, counter in sorted(bucket_sources.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-BUCKET-{len(bucket_rows) + 1:05d}",
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
            "question_id": "OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-QUESTION-001",
            "question": "Which SOURCE repair branches become positive under materialized bar-spread proxy?",
            "answer_route": "Filter branch ledger where bar_spread_recompute_decision is BAR_PROXY_REPAIR_UPGRADED_TO_CHALLENGER_REVIEW.",
        },
        {
            "question_id": "OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-QUESTION-002",
            "question": "Which accepted SOURCE branches degrade under local bar-spread proxy?",
            "answer_route": "Filter branch ledger where bar_spread_recompute_decision is BAR_PROXY_ACCEPTED_DEGRADED_TO_REPAIR.",
        },
        {
            "question_id": "OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-QUESTION-003",
            "question": "Which source windows still lack exact tick truth?",
            "answer_route": "All rows retain exact_tick_recompute_state or source_descriptor_recompute_state; bar proxy is lower-level source evidence, not exact tick proof.",
        },
        {
            "question_id": "OHLC-GTOS-SRC-BAR-SPREAD-RECOMP-QUESTION-004",
            "question": "What executable queue follows this packet?",
            "answer_route": "Use branch recompute decisions to split SOURCE challenger/avoid rows, then continue M1/M15/positive/entry-adverse detail builders.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "not_completion": True,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_BAR_SPREAD_RECOMPUTE",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_source_detail_branch_rows": len(branch_rows),
            "input_source_detail_window_rows": len(source_window_rows),
            "input_materialized_window_rows": len(materialized_window_rows),
            "input_spread_stress_rows": len(stress_rows),
            "source_bar_recompute_branch_rows": len(recompute_branch_rows),
            "source_bar_recompute_window_rows": len(recompute_window_rows),
            "source_bar_recompute_accepted_rows": len(accepted_rows),
            "source_bar_recompute_repair_rows": len(repair_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_source_detail_counts": source_detail_result.get("counts", {}),
        "upstream_materialization_counts": source_window_materialization_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "system_decision": {
            "system_recommendation": (
                "SOURCE_BAR_SPREAD_RECOMPUTE_RESULT: use materialized local bar-spread "
                "proxy to split SOURCE accepted/repair rows, preserve exact tick gap, and "
                "continue M1/M15/positive/entry-adverse executable queues."
            ),
            "branch_rows": len(recompute_branch_rows),
            "window_rows": len(recompute_window_rows),
            "repair_upgraded_to_challenger_review": int(bucket_sources["bar_spread_recompute_decision"]["BAR_PROXY_REPAIR_UPGRADED_TO_CHALLENGER_REVIEW"]),
            "accepted_degraded_to_repair": int(bucket_sources["bar_spread_recompute_decision"]["BAR_PROXY_ACCEPTED_DEGRADED_TO_REPAIR"]),
            "partial_scalar_repair_upgraded_review_with_m15_ambiguity": int(
                bucket_sources["bar_spread_recompute_decision"]["BAR_PROXY_PARTIAL_SCALAR_REPAIR_UPGRADED_REVIEW_WITH_M15_AMBIGUITY"]
            ),
            "partial_scalar_accepted_degraded_review_with_m15_ambiguity": int(
                bucket_sources["bar_spread_recompute_decision"]["BAR_PROXY_PARTIAL_SCALAR_ACCEPTED_DEGRADED_REVIEW_WITH_M15_AMBIGUITY"]
            ),
            "exact_tick_still_unavailable_rows": len(recompute_branch_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_LEDGER, recompute_branch_rows),
        (WINDOW_LEDGER, recompute_window_rows),
        (ACCEPTED_LEDGER, accepted_rows),
        (REPAIR_LEDGER, repair_rows),
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
                "# Historical OHLC GTOS Replay Branch SOURCE Bar Spread Recompute",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch recompute rows: `{len(recompute_branch_rows)}`",
                f"- Window recompute rows: `{len(recompute_window_rows)}`",
                f"- Repair upgraded to challenger review: `{result['system_decision']['repair_upgraded_to_challenger_review']}`",
                f"- Accepted degraded to repair: `{result['system_decision']['accepted_degraded_to_repair']}`",
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
                "type": "branch_source_bar_spread_recompute",
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
                    "event_type": "branch_source_bar_spread_recompute_built",
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
