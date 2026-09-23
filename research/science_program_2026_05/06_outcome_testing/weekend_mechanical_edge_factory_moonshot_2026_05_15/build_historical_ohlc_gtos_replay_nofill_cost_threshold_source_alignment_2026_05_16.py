#!/usr/bin/env python3
"""Split confirmed no-fill cost-threshold/source-alignment conflicts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

FRICTION_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_CONTROL_RESULT_2026-05-16.json"
FRICTION_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_ENTRY_LEDGER_2026-05-16.jsonl"
FRICTION_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BRANCH_LEDGER_2026-05-16.jsonl"
FRICTION_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_FAMILY_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_RESULT_2026-05-16.json"
ENTRY_ALIGNMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_ENTRY_LEDGER_2026-05-16.jsonl"
SIGNATURE_ALIGNMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_SIGNATURE_LEDGER_2026-05-16.jsonl"
COST_MODEL_ALIGNMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_COST_MODEL_LEDGER_2026-05-16.jsonl"
FAMILY_ALIGNMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_FAMILY_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

CONFLICT_BUCKET = "CONFIRMED_NOFILL_STATUS_CONFLICTS_WITH_EXISTING_COST_THRESHOLD"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS no-fill cost-threshold source-alignment packet only. "
    "Rows split confirmed no-fill signatures whose M1 closest path touches an existing "
    "spread-adjusted effective threshold while the original entry remains untouched; "
    "no validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior change is claimed."
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
                yield {"_parse_error": True, "_line_no": line_no}


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
        FRICTION_RESULT_PATH,
        FRICTION_ENTRY_PATH,
        FRICTION_BRANCH_PATH,
        FRICTION_FAMILY_PATH,
        COST_STATUS_PATH,
        PATH_AMBIGUITY_PATH,
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def family_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("route_candidate_id")),
            str(row.get("entry_variant")),
            str(row.get("target_stop_contract_id")),
        ]
    )


def is_touch(side: str, source_price: float | None, threshold: float | None) -> bool:
    if source_price is None or threshold is None:
        return False
    if side.upper() == "SHORT":
        return source_price >= threshold
    return source_price <= threshold


def miss_distance(side: str, source_price: float | None, threshold: float | None) -> float | None:
    if source_price is None or threshold is None:
        return None
    if side.upper() == "SHORT":
        return round(max(0.0, threshold - source_price), 9)
    return round(max(0.0, source_price - threshold), 9)


def signed_threshold_shift(row: dict[str, Any]) -> float | None:
    if row.get("effective_entry_price") is None or row.get("entry_price_input_only") is None:
        return None
    return round(float(row["effective_entry_price"]) - float(row["entry_price_input_only"]), 9)


def ratio_or_none(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(numerator / denominator, 9)


def median_or_none(values: list[float]) -> float | None:
    return round(float(median(values)), 9) if values else None


def route_session(route_candidate_id: str) -> str:
    parts = str(route_candidate_id).split("|")
    return parts[1] if len(parts) > 1 else "SESSION_UNKNOWN"


def model_alignment_status(touches_model_threshold: bool, cost_path_status: str) -> str:
    path_filled = cost_path_status != "POST_SIGNAL_ENTRY_NOT_FILLED_WITHIN_HORIZON"
    if touches_model_threshold and not path_filled:
        return "M1_TOUCHES_MODEL_THRESHOLD_BUT_M15_COST_PATH_NOT_FILLED"
    if not touches_model_threshold and not path_filled:
        return "M1_AND_M15_BOTH_NO_FILL_FOR_MODEL_THRESHOLD"
    if touches_model_threshold and path_filled:
        return "M1_AND_M15_BOTH_FILL_FOR_MODEL_THRESHOLD"
    return "M1_NO_TOUCH_BUT_M15_COST_PATH_FILLED_SOURCE_DIVERGENCE"


def entry_alignment_status(entry: dict[str, Any], cost_model_rows: list[dict[str, Any]]) -> str:
    touched_models = [row for row in cost_model_rows if row["m1_touches_model_threshold"]]
    touched_nonzero = [row for row in touched_models if row["cost_model"] != "ZERO_COST_CONTROL"]
    zero_rows = [row for row in cost_model_rows if row["cost_model"] == "ZERO_COST_CONTROL"]
    zero_touched = any(row["m1_touches_model_threshold"] for row in zero_rows)
    all_nonzero_touched = len(touched_nonzero) == len([row for row in cost_model_rows if row["cost_model"] != "ZERO_COST_CONTROL"])
    if entry.get("authoritative_distance_source") != "M1_BID_BAR_PROXY_PRICE":
        return "CONFLICT_NOT_M1_PROXY_SOURCE_RECHECK"
    if zero_touched and touched_nonzero:
        return "ZERO_AND_SPREAD_THRESHOLDS_TOUCHED_RECHECK_CLASSIFIER"
    if not zero_touched and all_nonzero_touched:
        return "M1_TOUCHES_ALL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED"
    if not zero_touched and touched_nonzero:
        return "M1_TOUCHES_PARTIAL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED"
    return "CONFLICT_ENTRY_WITHOUT_SPREAD_THRESHOLD_TOUCH_FAIL_CLOSED"


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_nofill_cost_threshold_source_alignment",
            "generated_utc": generated_at,
            "counts": outputs["counts"],
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    manifest["outputs"] = existing
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_nofill_cost_threshold_source_alignment",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    friction_result = read_json(FRICTION_RESULT_PATH)
    friction_entries = [row for row in read_jsonl(FRICTION_ENTRY_PATH) if not row.get("_parse_error")]
    friction_branches = [row for row in read_jsonl(FRICTION_BRANCH_PATH) if not row.get("_parse_error")]
    friction_families = [row for row in read_jsonl(FRICTION_FAMILY_PATH) if not row.get("_parse_error")]
    cost_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    ambiguity_rows = [row for row in read_jsonl(PATH_AMBIGUITY_PATH) if not row.get("_parse_error")]

    conflict_entries = [row for row in friction_entries if row.get("execution_friction_distance_bucket") == CONFLICT_BUCKET]
    conflict_branches = [row for row in friction_branches if row.get("execution_friction_distance_bucket") == CONFLICT_BUCKET]
    costs_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cost_rows:
        costs_by_entry[row["entry_variant_id"]].append(row)
    branches_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in conflict_branches:
        branches_by_entry[row["entry_variant_id"]].append(row)
    ambiguity_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in ambiguity_rows:
        ambiguity_by_family[family_key(row)][str(row.get("ambiguity_status"))] += 1

    cost_model_rows: list[dict[str, Any]] = []
    entry_cost_rows_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in conflict_entries:
        source_price = entry.get("authoritative_closest_fill_side_price")
        for cost in sorted(costs_by_entry.get(entry["entry_variant_id"], []), key=lambda item: str(item.get("cost_model"))):
            threshold = float(cost["effective_entry_price"]) if cost.get("effective_entry_price") is not None else None
            touch = is_touch(str(entry["side"]), float(source_price) if source_price is not None else None, threshold)
            distance = miss_distance(str(entry["side"]), float(source_price) if source_price is not None else None, threshold)
            status = model_alignment_status(touch, str(cost.get("cost_path_status")))
            row = {
                "source_alignment_cost_model_id": f"OHLC-GTOS-NOFILL-SOURCE-ALIGN-COST-{len(cost_model_rows) + 1:05d}",
                "entry_variant_id": entry["entry_variant_id"],
                "event_id": entry["event_id"],
                "route_candidate_id": entry["route_candidate_id"],
                "route_session": route_session(str(entry["route_candidate_id"])),
                "symbol": entry["symbol"],
                "side": entry["side"],
                "entry_variant": entry["entry_variant"],
                "cost_fill_id": cost.get("cost_fill_id"),
                "cost_model": cost.get("cost_model"),
                "cost_path_status": cost.get("cost_path_status"),
                "fill_timing_status": cost.get("fill_timing_status"),
                "entry_price_input_only": cost.get("entry_price_input_only"),
                "effective_entry_price": cost.get("effective_entry_price"),
                "signed_threshold_shift_from_zero": signed_threshold_shift(cost),
                "spread_proxy_value": cost.get("spread_proxy_value"),
                "spread_proxy_price_distance": cost.get("spread_proxy_price_distance"),
                "authoritative_distance_source": entry.get("authoritative_distance_source"),
                "authoritative_closest_fill_side_price": entry.get("authoritative_closest_fill_side_price"),
                "m1_touches_model_threshold": touch,
                "miss_distance_to_model_threshold": distance,
                "miss_distance_to_model_threshold_over_rolling_median_range": ratio_or_none(
                    distance,
                    float(entry["rolling_median_range"]) if entry.get("rolling_median_range") is not None else None,
                ),
                "cost_model_alignment_status": status,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_COST_MODEL",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            cost_model_rows.append(row)
            entry_cost_rows_by_entry[entry["entry_variant_id"]].append(row)

    entry_alignment_rows: list[dict[str, Any]] = []
    entry_status_counter: Counter[str] = Counter()
    for seq, entry in enumerate(conflict_entries, 1):
        model_rows = entry_cost_rows_by_entry.get(entry["entry_variant_id"], [])
        touched_models = [row["cost_model"] for row in model_rows if row["m1_touches_model_threshold"]]
        untouched_models = [row["cost_model"] for row in model_rows if not row["m1_touches_model_threshold"]]
        status = entry_alignment_status(entry, model_rows)
        entry_status_counter[status] += 1
        min_touched_shift = [
            abs(float(row["signed_threshold_shift_from_zero"]))
            for row in model_rows
            if row["m1_touches_model_threshold"] and row.get("signed_threshold_shift_from_zero") is not None
        ]
        row = {
            "source_alignment_entry_id": f"OHLC-GTOS-NOFILL-SOURCE-ALIGN-ENTRY-{seq:05d}",
            "entry_variant_id": entry["entry_variant_id"],
            "event_id": entry["event_id"],
            "route_candidate_id": entry["route_candidate_id"],
            "route_session": route_session(str(entry["route_candidate_id"])),
            "symbol": entry["symbol"],
            "side": entry["side"],
            "entry_variant": entry["entry_variant"],
            "source_time_utc": entry.get("source_time_utc"),
            "probe_window_start_utc": entry.get("probe_window_start_utc"),
            "probe_window_end_utc": entry.get("probe_window_end_utc"),
            "authoritative_distance_source": entry.get("authoritative_distance_source"),
            "authoritative_closest_fill_side_price": entry.get("authoritative_closest_fill_side_price"),
            "entry_price_input_only": entry.get("entry_price_input_only"),
            "miss_distance_to_zero_entry_price": entry.get("miss_distance_to_zero_entry_price"),
            "miss_distance_to_zero_over_max_spread_proxy": entry.get("miss_distance_to_zero_over_max_spread_proxy"),
            "miss_distance_to_zero_over_rolling_median_range": entry.get("miss_distance_to_zero_over_rolling_median_range"),
            "rolling_median_range": entry.get("rolling_median_range"),
            "max_spread_proxy_price_distance": entry.get("max_spread_proxy_price_distance"),
            "cost_model_rows": len(model_rows),
            "m1_touched_cost_models": sorted(touched_models),
            "m1_untouched_cost_models": sorted(untouched_models),
            "min_abs_threshold_shift_touched": min(min_touched_shift) if min_touched_shift else None,
            "median_abs_threshold_shift_touched": median_or_none(min_touched_shift),
            "signature_rows": len(branches_by_entry.get(entry["entry_variant_id"], [])),
            "entry_alignment_status": status,
            "source_manifest_hash": manifest_hash,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_ENTRY",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        entry_alignment_rows.append(row)

    entry_alignment_by_id = {row["entry_variant_id"]: row for row in entry_alignment_rows}
    signature_alignment_rows: list[dict[str, Any]] = []
    for seq, branch in enumerate(conflict_branches, 1):
        entry_alignment = entry_alignment_by_id.get(branch["entry_variant_id"], {})
        ambiguity_counter = ambiguity_by_family.get(branch["family_key"], Counter())
        signature_alignment_rows.append(
            {
                "source_alignment_signature_id": f"OHLC-GTOS-NOFILL-SOURCE-ALIGN-SIG-{seq:05d}",
                "cost_sensitivity_signature_id": branch["cost_sensitivity_signature_id"],
                "entry_variant_id": branch["entry_variant_id"],
                "event_id": branch["event_id"],
                "route_candidate_id": branch["route_candidate_id"],
                "route_session": route_session(str(branch["route_candidate_id"])),
                "symbol": branch["symbol"],
                "side": branch["side"],
                "entry_variant": branch["entry_variant"],
                "target_stop_contract_id": branch["target_stop_contract_id"],
                "target_multiple": branch["target_multiple"],
                "stop_multiple": branch["stop_multiple"],
                "family_key": branch["family_key"],
                "entry_alignment_status": entry_alignment.get("entry_alignment_status"),
                "m1_touched_cost_models": entry_alignment.get("m1_touched_cost_models", []),
                "m1_untouched_cost_models": entry_alignment.get("m1_untouched_cost_models", []),
                "same_m15_ambiguity_rows_for_family": sum(ambiguity_counter.values()),
                "same_m15_ambiguity_statuses_for_family": dict(sorted(ambiguity_counter.items())),
                "cross_control_family_status": branch.get("cross_control_family_status"),
                "family_exact_descriptor_delta_rows": branch.get("family_exact_descriptor_delta_rows"),
                "family_exact_unavailable_stress_rows": branch.get("family_exact_unavailable_stress_rows"),
                "miss_distance_to_zero_entry_price": branch.get("miss_distance_to_zero_entry_price"),
                "miss_distance_to_easiest_existing_cost_threshold": branch.get("miss_distance_to_easiest_existing_cost_threshold"),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_SIGNATURE",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    family_counter: dict[str, Counter[str]] = defaultdict(Counter)
    family_examples: dict[str, dict[str, Any]] = {}
    for row in signature_alignment_rows:
        family_examples.setdefault(row["family_key"], row)
        family_counter[row["family_key"]][str(row.get("entry_alignment_status"))] += 1
    family_rows: list[dict[str, Any]] = []
    for seq, (key, counter) in enumerate(sorted(family_counter.items()), 1):
        example = family_examples[key]
        family_rows.append(
            {
                "source_alignment_family_id": f"OHLC-GTOS-NOFILL-SOURCE-ALIGN-FAMILY-{seq:05d}",
                "family_key": key,
                "route_candidate_id": example["route_candidate_id"],
                "route_session": example["route_session"],
                "symbol": example["symbol"],
                "side": example["side"],
                "entry_variant": example["entry_variant"],
                "target_stop_contract_id": example["target_stop_contract_id"],
                "target_multiple": example["target_multiple"],
                "stop_multiple": example["stop_multiple"],
                "signature_rows": sum(counter.values()),
                "entry_alignment_status_counts": dict(sorted(counter.items())),
                "same_m15_ambiguity_rows_for_family": example.get("same_m15_ambiguity_rows_for_family"),
                "cross_control_family_status": example.get("cross_control_family_status"),
                "family_exact_descriptor_delta_rows": example.get("family_exact_descriptor_delta_rows"),
                "family_exact_unavailable_stress_rows": example.get("family_exact_unavailable_stress_rows"),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_FAMILY",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    bucket_rows: list[dict[str, Any]] = []

    def add_bucket(axis: str, counter: Counter[Any]) -> None:
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("entry_alignment_status", entry_status_counter)
    add_bucket("cost_model_alignment_status", Counter(row["cost_model_alignment_status"] for row in cost_model_rows))
    add_bucket("cost_model__alignment_status", Counter((row["cost_model"], row["cost_model_alignment_status"]) for row in cost_model_rows))
    add_bucket("symbol__entry_alignment_status", Counter((row["symbol"], row["entry_alignment_status"]) for row in entry_alignment_rows))
    add_bucket("session__entry_alignment_status", Counter((row["route_session"], row["entry_alignment_status"]) for row in entry_alignment_rows))
    add_bucket("entry_variant__entry_alignment_status", Counter((row["entry_variant"], row["entry_alignment_status"]) for row in entry_alignment_rows))
    add_bucket("signature_alignment_status", Counter(row["entry_alignment_status"] for row in signature_alignment_rows))
    add_bucket("same_m15_ambiguity__signature_alignment_status", Counter((bool(row["same_m15_ambiguity_rows_for_family"]), row["entry_alignment_status"]) for row in signature_alignment_rows))
    add_bucket("cross_family_status__signature_alignment_status", Counter((row.get("cross_control_family_status"), row["entry_alignment_status"]) for row in signature_alignment_rows))

    all_spread_rows = [
        row for row in entry_alignment_rows
        if row["entry_alignment_status"] == "M1_TOUCHES_ALL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED"
    ]
    partial_spread_rows = [
        row for row in entry_alignment_rows
        if row["entry_alignment_status"] == "M1_TOUCHES_PARTIAL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED"
    ]
    model_conflicts = [
        row for row in cost_model_rows
        if row["cost_model_alignment_status"] == "M1_TOUCHES_MODEL_THRESHOLD_BUT_M15_COST_PATH_NOT_FILLED"
    ]
    ambiguity_overlap = [row for row in signature_alignment_rows if row["same_m15_ambiguity_rows_for_family"]]
    exact_context_overlap = [
        row for row in signature_alignment_rows
        if row.get("family_exact_descriptor_delta_rows", 0) or row.get("family_exact_unavailable_stress_rows", 0)
    ]
    question_rows = [
        {
            "question_id": "OHLC-GTOS-NOFILL-SOURCE-ALIGN-QUESTION-001",
            "question": "How many confirmed no-fill entries are actually M1 touches of spread-adjusted thresholds while zero entry remains untouched?",
            "row_count": len(entry_alignment_rows),
            "next_same_resource_action": "recompute path descriptors from M1 spread-adjusted threshold fills or keep as source-drift branch controls",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-SOURCE-ALIGN-QUESTION-002",
            "question": "How many conflict entries touch every nonzero spread-adjusted threshold?",
            "row_count": len(all_spread_rows),
            "next_same_resource_action": "promote all-spread-threshold-touch rows into the spread-adjusted fill-recovery replay queue",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-SOURCE-ALIGN-QUESTION-003",
            "question": "How many conflict entries only touch partial spread-adjusted thresholds?",
            "row_count": len(partial_spread_rows),
            "next_same_resource_action": "split partial rows by touched cost model and threshold shift before replay",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-SOURCE-ALIGN-QUESTION-004",
            "question": "How many cost-model rows directly contradict M15 cost-path no-fill status?",
            "row_count": len(model_conflicts),
            "next_same_resource_action": "use model-conflict rows as the exact denominator for M1 recompute versus M15 source-drift controls",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-SOURCE-ALIGN-QUESTION-005",
            "question": "How many conflict signatures also carry same-M15 target/stop ambiguity?",
            "row_count": len(ambiguity_overlap),
            "next_same_resource_action": "split spread-adjusted fill recovery by target/stop same-bar ambiguity before descriptor claims",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-NOFILL-SOURCE-ALIGN-QUESTION-006",
            "question": "How many conflict signatures overlap exact-spread or exact-unavailable families?",
            "row_count": len(exact_context_overlap),
            "next_same_resource_action": "join source-alignment rows to exact-spread family context before family synthesis",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "conflict_branch_input_rows": len(conflict_branches),
        "conflict_entry_input_rows": len(conflict_entries),
        "cost_model_alignment_rows": len(cost_model_rows),
        "cost_status_input_rows": len(cost_rows),
        "entry_alignment_rows": len(entry_alignment_rows),
        "family_alignment_rows": len(family_rows),
        "friction_branch_input_rows": len(friction_branches),
        "friction_entry_input_rows": len(friction_entries),
        "friction_family_input_rows": len(friction_families),
        "path_ambiguity_input_rows": len(ambiguity_rows),
        "question_rows": len(question_rows),
        "signature_alignment_rows": len(signature_alignment_rows),
        "source_manifest_rows": len(manifest_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_nofill_cost_threshold_source_alignment_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This no-fill cost-threshold source-alignment packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "entry_alignment_status_counts": dict(sorted(entry_status_counter.items())),
        "cost_model_alignment_status_counts": dict(sorted(Counter(row["cost_model_alignment_status"] for row in cost_model_rows).items())),
        "cost_model_touch_counts": dict(sorted(Counter(row["cost_model"] for row in cost_model_rows if row["m1_touches_model_threshold"]).items())),
        "signature_alignment_status_counts": dict(sorted(Counter(row["entry_alignment_status"] for row in signature_alignment_rows).items())),
        "upstream_friction_counts": friction_result.get("counts", {}),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "recompute M1 spread-adjusted fill path descriptors for all-spread-threshold-touch entries",
            "split partial threshold touches by cost model and threshold shift",
            "join source-alignment signatures to same-M15 ambiguity controls before target/stop descriptor claims",
            "feed source-alignment families into the cost/fill/path synthesis packet preserving all families",
        ],
    }

    write_jsonl(ENTRY_ALIGNMENT_PATH, entry_alignment_rows)
    write_jsonl(SIGNATURE_ALIGNMENT_PATH, signature_alignment_rows)
    write_jsonl(COST_MODEL_ALIGNMENT_PATH, cost_model_rows)
    write_jsonl(FAMILY_ALIGNMENT_PATH, family_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay No-Fill Cost-Threshold Source Alignment",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet splits confirmed no-fill rows where M1 path reaches spread-adjusted effective thresholds while the original retest entry remains untouched.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Entry Alignment",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(entry_status_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Recompute M1 spread-adjusted fill path descriptors for all-spread-threshold-touch entries.",
                "- Split partial threshold touches by cost model and threshold shift.",
                "- Join source-alignment signatures to same-M15 ambiguity controls before target/stop descriptor claims.",
                "- Feed source-alignment families into the cost/fill/path synthesis packet preserving all families.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    update_manifest(output, generated_at)
    append_sprint_ledger(output, generated_at)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
