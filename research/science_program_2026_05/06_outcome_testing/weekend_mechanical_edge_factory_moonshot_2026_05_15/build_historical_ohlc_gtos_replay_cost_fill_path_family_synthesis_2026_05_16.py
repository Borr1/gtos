#!/usr/bin/env python3
"""Join GTOS replay cost/fill/path family evidence into one branch queue."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

COST_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_AGGREGATE_LEDGER_2026-05-16.jsonl"
RECOVERED_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_FAMILY_JOIN_LEDGER_2026-05-16.jsonl"
CONFIRMED_NOFILL_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_FAMILY_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_FAMILY_LEDGER_2026-05-16.jsonl"
M1_SPREAD_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_FAMILY_LEDGER_2026-05-16.jsonl"
M1_SPREAD_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_FAMILY_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
PARTIAL_REPAIR_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_ENTRY_LEDGER_2026-05-16.jsonl"
PARTIAL_REPAIR_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_SIGNATURE_SCOPE_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_RESULT_2026-05-16.json"
FAMILY_SYNTHESIS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_FAMILY_LEDGER_2026-05-16.jsonl"
BRANCH_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_BRANCH_QUEUE_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay cost/fill/path family synthesis only. Rows join "
    "family-level cost sensitivity, exact-spread, recovered-fill, confirmed no-fill, "
    "source-alignment, and M1 spread-adjusted replay descriptors into a complete "
    "same-resource branch queue; no validation, R/PnL, expectancy, win-rate, "
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
        COST_FAMILY_PATH,
        RECOVERED_FAMILY_PATH,
        CONFIRMED_NOFILL_FAMILY_PATH,
        SOURCE_ALIGNMENT_FAMILY_PATH,
        M1_SPREAD_FAMILY_PATH,
        M1_SPREAD_SIGNATURE_PATH,
        M1_FILL_BAR_FAMILY_PATH,
        M1_FILL_BAR_SIGNATURE_PATH,
        PARTIAL_REPAIR_ENTRY_PATH,
        PARTIAL_REPAIR_SIGNATURE_PATH,
        TARGET_STOP_CONTRACT_PATH,
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    return rows, hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()


def merge_counter(target: Counter[str], value: dict[str, Any] | None) -> None:
    if not isinstance(value, dict):
        return
    for key, count in value.items():
        target[str(key)] += int(count or 0)


def stable_float(value: Any) -> str:
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "NA"


def contract_id_by_multiple(rows: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for row in rows:
        target = stable_float(row.get("target_multiple_of_rolling_median_range"))
        stop = stable_float(row.get("stop_multiple_of_rolling_median_range"))
        out[(target, stop)] = str(row.get("target_stop_contract_id"))
    return out


def row_key(row: dict[str, Any], contract_by_multiple: dict[tuple[str, str], str]) -> tuple[str, str, str, str]:
    target = stable_float(row.get("target_multiple", row.get("target_multiple_of_rolling_median_range")))
    stop = stable_float(row.get("stop_multiple", row.get("stop_multiple_of_rolling_median_range")))
    contract = row.get("target_stop_contract_id") or contract_by_multiple.get((target, stop), f"TARGETSTOP_{target}_{stop}")
    return (
        str(row.get("route_candidate_id")),
        str(row.get("entry_variant")),
        str(contract),
        f"{target}|{stop}",
    )


def empty_family(row: dict[str, Any], key: tuple[str, str, str, str]) -> dict[str, Any]:
    target, stop = key[3].split("|", 1)
    return {
        "family_synthesis_id": "",
        "route_candidate_id": key[0],
        "entry_variant": key[1],
        "target_stop_contract_id": key[2],
        "target_multiple": target,
        "stop_multiple": stop,
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "route_session": row.get("route_session"),
        "family_sources_present": [],
        "cost_sensitivity_status_counts": Counter(),
        "changed_model_counts": Counter(),
        "gradient_exact_spread_bucket_counts": Counter(),
        "cross_control_family_status_counts": Counter(),
        "recovered_path_status_counts": Counter(),
        "recovered_fill_source_counts": Counter(),
        "confirmed_distance_bucket_counts": Counter(),
        "source_alignment_status_counts": Counter(),
        "m1_first_touch_status_counts": Counter(),
        "m1_cost_model_counts": Counter(),
        "fill_bar_interval_status_counts": Counter(),
        "fill_bar_conservative_first_touch_status_counts": Counter(),
        "fill_bar_stress_scope_status_counts": Counter(),
        "partial_repair_entry_status_counts": Counter(),
        "partial_repair_signature_scope_status_counts": Counter(),
        "partial_repair_first_touch_status_counts": Counter(),
        "ambiguity_signature_rows": 0,
        "changed_signature_rows": 0,
        "gradient_signature_rows": 0,
        "unfilled_signature_rows": 0,
        "recovered_signature_rows": 0,
        "confirmed_nofill_signature_rows": 0,
        "source_alignment_signature_rows": 0,
        "m1_spread_signature_rows": 0,
        "fill_bar_stress_signature_rows": 0,
        "fill_bar_order_unresolved_rows": 0,
        "partial_repair_entry_rows": 0,
        "partial_repair_signature_scope_rows": 0,
        "exact_descriptor_delta_rows": 0,
        "exact_unavailable_stress_rows": 0,
        "same_m15_ambiguity_rows_for_family": 0,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def add_source(family: dict[str, Any], name: str) -> None:
    sources = set(family["family_sources_present"])
    sources.add(name)
    family["family_sources_present"] = sorted(sources)


def branch_actions(family: dict[str, Any]) -> tuple[str, list[str]]:
    actions: list[str] = []
    m1_status = family["m1_first_touch_status_counts"]
    distance = family["confirmed_distance_bucket_counts"]
    source_alignment = family["source_alignment_status_counts"]
    if any("FILL_BAR" in key and "ORDER_UNRESOLVED" in key for key in m1_status):
        actions.append("M1_FILL_BAR_ORDERING_STRESS")
    interval = family["fill_bar_interval_status_counts"]
    if interval:
        actions.append("M1_FILL_BAR_INTERVAL_STRESS_INTEGRATED")
    if any("SOURCE_FAIL_CLOSED" in key for key in interval):
        actions.append("M1_FILL_BAR_SOURCE_REPAIR_REQUIRED")
    if family["partial_repair_signature_scope_rows"]:
        actions.append("PARTIAL_SOURCE_RECHECK_REPAIR_INTEGRATED")
    if family["m1_spread_signature_rows"]:
        actions.append("M1_SPREAD_ADJUSTED_REPLAY_FAMILY_JOIN")
    if source_alignment:
        actions.append("SOURCE_ALIGNMENT_CONFLICT_SPLIT")
    if distance.get("CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD", 0):
        actions.append("NEAR_MISS_ENTRY_OFFSET_OR_MARKET_ENTRY_CONTROL")
    if distance.get("CONFIRMED_NOFILL_MISS_BEYOND_ROLLING_MEDIAN_RANGE", 0):
        actions.append("FAR_MISS_AVOID_OR_RETEST_REDESIGN_CONTROL")
    if distance.get("CONFIRMED_NOFILL_MISS_WITHIN_ROLLING_MEDIAN_RANGE", 0):
        actions.append("WITHIN_RANGE_FILLABILITY_OR_ENTRY_GEOMETRY_CONTROL")
    if family["recovered_signature_rows"]:
        actions.append("RECOVERED_FILL_SOURCE_AND_ORDERING_SPLIT")
    if family["exact_descriptor_delta_rows"] or family["exact_unavailable_stress_rows"]:
        actions.append("EXACT_SPREAD_INTERVAL_OR_SOURCE_STRESS")
    if family["same_m15_ambiguity_rows_for_family"]:
        actions.append("SAME_M15_AMBIGUITY_SPLIT")
    if not actions:
        actions.append("BASELINE_FAMILY_DESCRIPTOR_PRESERVE")
    if "M1_FILL_BAR_SOURCE_REPAIR_REQUIRED" in actions:
        status = "ACTIVE_M1_FILL_BAR_SOURCE_REPAIR_REQUIRED"
    elif "M1_FILL_BAR_ORDERING_STRESS" in actions and "M1_FILL_BAR_INTERVAL_STRESS_INTEGRATED" not in actions:
        status = "ACTIVE_M1_FILL_BAR_ORDERING_STRESS_REQUIRED"
    elif "PARTIAL_SOURCE_RECHECK_REPAIR_INTEGRATED" in actions:
        status = "ACTIVE_PARTIAL_SOURCE_RECHECK_REPAIR_SYNTHESIS_REQUIRED"
    elif "NEAR_MISS_ENTRY_OFFSET_OR_MARKET_ENTRY_CONTROL" in actions:
        status = "ACTIVE_NEAR_MISS_ENTRY_CONTROL_REQUIRED"
    elif "FAR_MISS_AVOID_OR_RETEST_REDESIGN_CONTROL" in actions:
        status = "ACTIVE_FAR_MISS_AVOID_REDESIGN_REQUIRED"
    elif "M1_SPREAD_ADJUSTED_REPLAY_FAMILY_JOIN" in actions:
        status = "ACTIVE_M1_SPREAD_REPLAY_SYNTHESIS_REQUIRED"
    elif "SOURCE_ALIGNMENT_CONFLICT_SPLIT" in actions:
        status = "ACTIVE_SOURCE_ALIGNMENT_SPLIT_REQUIRED"
    elif "RECOVERED_FILL_SOURCE_AND_ORDERING_SPLIT" in actions:
        status = "ACTIVE_RECOVERED_FILL_SPLIT_REQUIRED"
    elif "EXACT_SPREAD_INTERVAL_OR_SOURCE_STRESS" in actions:
        status = "ACTIVE_EXACT_SPREAD_STRESS_REQUIRED"
    elif "SAME_M15_AMBIGUITY_SPLIT" in actions:
        status = "ACTIVE_SAME_M15_AMBIGUITY_REQUIRED"
    else:
        status = "PRESERVE_BASELINE_FAMILY_DESCRIPTOR"
    return status, actions


def serializable_family(family: dict[str, Any], seq: int, source_hash: str) -> dict[str, Any]:
    status, actions = branch_actions(family)
    row = dict(family)
    for key in [
        "cost_sensitivity_status_counts",
        "changed_model_counts",
        "gradient_exact_spread_bucket_counts",
        "cross_control_family_status_counts",
        "recovered_path_status_counts",
        "recovered_fill_source_counts",
        "confirmed_distance_bucket_counts",
        "source_alignment_status_counts",
        "m1_first_touch_status_counts",
        "m1_cost_model_counts",
        "fill_bar_interval_status_counts",
        "fill_bar_conservative_first_touch_status_counts",
        "fill_bar_stress_scope_status_counts",
        "partial_repair_entry_status_counts",
        "partial_repair_signature_scope_status_counts",
        "partial_repair_first_touch_status_counts",
    ]:
        row[key] = dict(family[key])
    row["family_synthesis_id"] = f"OHLC-GTOS-COST-FILL-PATH-SYNTH-FAMILY-{seq:05d}"
    row["branch_queue_status"] = status
    row["branch_actions"] = actions
    row["source_manifest_hash"] = source_hash
    row["evidence_class"] = "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS"
    return row


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_cost_fill_path_family_synthesis",
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
        "route": "historical_ohlc_gtos_replay_cost_fill_path_family_synthesis",
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
    target_stop_contracts = [row for row in read_jsonl(TARGET_STOP_CONTRACT_PATH) if not row.get("_parse_error")]
    contract_by_multiple = contract_id_by_multiple(target_stop_contracts)
    inputs = {
        "cost_family": [row for row in read_jsonl(COST_FAMILY_PATH) if not row.get("_parse_error")],
        "recovered_family": [row for row in read_jsonl(RECOVERED_FAMILY_PATH) if not row.get("_parse_error")],
        "confirmed_nofill_family": [row for row in read_jsonl(CONFIRMED_NOFILL_FAMILY_PATH) if not row.get("_parse_error")],
        "source_alignment_family": [row for row in read_jsonl(SOURCE_ALIGNMENT_FAMILY_PATH) if not row.get("_parse_error")],
        "m1_spread_family": [row for row in read_jsonl(M1_SPREAD_FAMILY_PATH) if not row.get("_parse_error")],
        "m1_spread_signature": [row for row in read_jsonl(M1_SPREAD_SIGNATURE_PATH) if not row.get("_parse_error")],
        "m1_fill_bar_family": [row for row in read_jsonl(M1_FILL_BAR_FAMILY_PATH) if not row.get("_parse_error")],
        "m1_fill_bar_signature": [row for row in read_jsonl(M1_FILL_BAR_SIGNATURE_PATH) if not row.get("_parse_error")],
        "partial_repair_entry": [row for row in read_jsonl(PARTIAL_REPAIR_ENTRY_PATH) if not row.get("_parse_error")],
        "partial_repair_signature": [row for row in read_jsonl(PARTIAL_REPAIR_SIGNATURE_PATH) if not row.get("_parse_error")],
    }
    families: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    def family_for(row: dict[str, Any]) -> dict[str, Any]:
        key = row_key(row, contract_by_multiple)
        if key not in families:
            families[key] = empty_family(row, key)
        family = families[key]
        for field in ("symbol", "side", "route_session"):
            if family.get(field) in {None, "None"} and row.get(field) is not None:
                family[field] = row.get(field)
        return family

    for row in inputs["cost_family"]:
        family = family_for(row)
        add_source(family, "cost_sensitivity_family")
        merge_counter(family["cost_sensitivity_status_counts"], row.get("cost_sensitivity_status_counts"))
        merge_counter(family["changed_model_counts"], row.get("changed_model_counts"))
        merge_counter(family["gradient_exact_spread_bucket_counts"], row.get("gradient_exact_spread_bucket_counts"))
        family["ambiguity_signature_rows"] += int(row.get("ambiguity_signature_rows") or 0)
        family["changed_signature_rows"] += int(row.get("changed_signature_rows") or 0)
        family["gradient_signature_rows"] += int(row.get("gradient_signature_rows") or 0)
        family["unfilled_signature_rows"] += int(row.get("unfilled_signature_rows") or 0)

    for row in inputs["recovered_family"]:
        family = family_for(row)
        add_source(family, "recovered_unfilled_cross_control_family")
        family["recovered_signature_rows"] += int(row.get("recovered_signature_rows") or 0)
        family["exact_descriptor_delta_rows"] += int(row.get("exact_descriptor_delta_rows") or 0)
        family["exact_unavailable_stress_rows"] += int(row.get("exact_unavailable_stress_rows") or 0)
        family["same_m15_ambiguity_rows_for_family"] = max(
            family["same_m15_ambiguity_rows_for_family"],
            int(row.get("same_m15_ambiguity_rows_for_family") or 0),
        )
        family["cross_control_family_status_counts"][str(row.get("cross_control_family_status"))] += 1
        for status in row.get("recovered_path_statuses") or []:
            family["recovered_path_status_counts"][str(status)] += 1
        for source in row.get("recovered_fill_sources") or []:
            family["recovered_fill_source_counts"][str(source)] += 1

    for row in inputs["confirmed_nofill_family"]:
        family = family_for(row)
        add_source(family, "confirmed_nofill_execution_friction_family")
        family["confirmed_nofill_signature_rows"] += int(row.get("confirmed_nofill_signature_rows") or 0)
        family["same_m15_ambiguity_rows_for_family"] = max(
            family["same_m15_ambiguity_rows_for_family"],
            int(row.get("same_m15_ambiguity_rows_for_family") or 0),
        )
        merge_counter(family["confirmed_distance_bucket_counts"], row.get("distance_bucket_counts"))

    for row in inputs["source_alignment_family"]:
        family = family_for(row)
        add_source(family, "nofill_cost_threshold_source_alignment_family")
        family["source_alignment_signature_rows"] += int(row.get("signature_rows") or 0)
        family["same_m15_ambiguity_rows_for_family"] = max(
            family["same_m15_ambiguity_rows_for_family"],
            int(row.get("same_m15_ambiguity_rows_for_family") or 0),
        )
        merge_counter(family["source_alignment_status_counts"], row.get("entry_alignment_status_counts"))

    for row in inputs["m1_spread_family"]:
        family = family_for(row)
        add_source(family, "m1_spread_adjusted_fill_replay_family")
        family["m1_spread_signature_rows"] += int(row.get("signature_rows") or 0)
        family["same_m15_ambiguity_rows_for_family"] = max(
            family["same_m15_ambiguity_rows_for_family"],
            int(row.get("same_m15_ambiguity_rows_for_family") or 0),
        )
        family["m1_cost_model_counts"][str(row.get("cost_model"))] += int(row.get("signature_rows") or 0)
        merge_counter(family["m1_first_touch_status_counts"], row.get("m1_first_touch_status_counts"))

    for row in inputs["m1_spread_signature"]:
        family = family_for(row)
        add_source(family, "m1_spread_adjusted_fill_replay_signature")

    for row in inputs["m1_fill_bar_family"]:
        family = family_for(row)
        add_source(family, "m1_spread_fill_bar_ordering_stress_family")
        family["fill_bar_stress_signature_rows"] += int(row.get("signature_rows") or 0)
        family["same_m15_ambiguity_rows_for_family"] = max(
            family["same_m15_ambiguity_rows_for_family"],
            int(row.get("same_m15_ambiguity_rows_for_family") or 0),
        )
        merge_counter(family["fill_bar_interval_status_counts"], row.get("interval_status_counts"))
        merge_counter(family["fill_bar_conservative_first_touch_status_counts"], row.get("conservative_first_touch_status_counts"))
        merge_counter(family["fill_bar_stress_scope_status_counts"], row.get("stress_scope_status_counts"))
    for row in inputs["m1_fill_bar_signature"]:
        family = family_for(row)
        add_source(family, "m1_spread_fill_bar_ordering_stress_signature")
        if row.get("stress_scope_status") == "FILL_BAR_ORDER_UNRESOLVED_STRESSED":
            family["fill_bar_order_unresolved_rows"] += 1

    for row in inputs["partial_repair_entry"]:
        family = family_for(row)
        add_source(family, "m1_spread_partial_source_recheck_repair_entry")
        family["partial_repair_entry_rows"] += 1
        family["partial_repair_entry_status_counts"][str(row.get("entry_repair_status"))] += 1
    for row in inputs["partial_repair_signature"]:
        family = family_for(row)
        add_source(family, "m1_spread_partial_source_recheck_repair_signature_scope")
        family["partial_repair_signature_scope_rows"] += 1
        family["same_m15_ambiguity_rows_for_family"] = max(
            family["same_m15_ambiguity_rows_for_family"],
            int(row.get("same_m15_ambiguity_rows_for_family") or 0),
        )
        family["partial_repair_signature_scope_status_counts"][str(row.get("signature_scope_status"))] += 1
        family["partial_repair_first_touch_status_counts"][str(row.get("m1_first_touch_status"))] += 1

    family_rows = [
        serializable_family(family, seq, manifest_hash)
        for seq, family in enumerate(sorted(families.values(), key=lambda row: (row["route_candidate_id"], row["entry_variant"], row["target_stop_contract_id"])), 1)
    ]
    branch_rows = []
    for seq, family in enumerate(family_rows, 1):
        branch_rows.append(
            {
                "branch_queue_id": f"OHLC-GTOS-COST-FILL-PATH-SYNTH-BRANCH-{seq:05d}",
                "family_synthesis_id": family["family_synthesis_id"],
                "route_candidate_id": family["route_candidate_id"],
                "symbol": family["symbol"],
                "side": family["side"],
                "route_session": family["route_session"],
                "entry_variant": family["entry_variant"],
                "target_stop_contract_id": family["target_stop_contract_id"],
                "target_multiple": family["target_multiple"],
                "stop_multiple": family["stop_multiple"],
                "branch_queue_status": family["branch_queue_status"],
                "branch_actions": family["branch_actions"],
                "family_sources_present": family["family_sources_present"],
                "same_m15_ambiguity_rows_for_family": family["same_m15_ambiguity_rows_for_family"],
                "fill_bar_source_fail_closed_rows": sum(
                    count
                    for status, count in family["fill_bar_interval_status_counts"].items()
                    if "SOURCE_FAIL_CLOSED" in status
                ),
                "fill_bar_order_unresolved_rows": family["fill_bar_order_unresolved_rows"],
                "confirmed_nofill_signature_rows": family["confirmed_nofill_signature_rows"],
                "m1_spread_signature_rows": family["m1_spread_signature_rows"],
                "fill_bar_stress_signature_rows": family["fill_bar_stress_signature_rows"],
                "source_alignment_signature_rows": family["source_alignment_signature_rows"],
                "partial_repair_signature_scope_rows": family["partial_repair_signature_scope_rows"],
                "recovered_signature_rows": family["recovered_signature_rows"],
                "source_manifest_hash": manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_BRANCH_QUEUE",
            }
        )

    status_counts = Counter(row["branch_queue_status"] for row in branch_rows)
    action_counts = Counter(action for row in branch_rows for action in row["branch_actions"])
    source_combo_counts = Counter("|".join(row["family_sources_present"]) for row in family_rows)
    bucket_rows = []
    for seq, (status, count) in enumerate(sorted(status_counts.items()), 1):
        bucket_rows.append(
            {
                "bucket_id": f"OHLC-GTOS-COST-FILL-PATH-SYNTH-BUCKET-{seq:03d}",
                "bucket_type": "branch_queue_status",
                "bucket": status,
                "family_rows": count,
                "source_manifest_hash": manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    offset = len(bucket_rows)
    for seq, (action, count) in enumerate(sorted(action_counts.items()), 1):
        bucket_rows.append(
            {
                "bucket_id": f"OHLC-GTOS-COST-FILL-PATH-SYNTH-BUCKET-{offset + seq:03d}",
                "bucket_type": "branch_action",
                "bucket": action,
                "family_rows": count,
                "source_manifest_hash": manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    offset = len(bucket_rows)
    for seq, (combo, count) in enumerate(sorted(source_combo_counts.items()), 1):
        bucket_rows.append(
            {
                "bucket_id": f"OHLC-GTOS-COST-FILL-PATH-SYNTH-BUCKET-{offset + seq:03d}",
                "bucket_type": "source_combo",
                "bucket": combo,
                "family_rows": count,
                "source_manifest_hash": manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    question_specs = [
        ("fill_bar_ordering", "Split M1 fill-bar order-unresolved rows with conservative/optimistic M1 interval bounds.", "M1_FILL_BAR_ORDERING_STRESS"),
        ("near_miss", "Materialize near-miss entry-offset and market-entry controls.", "NEAR_MISS_ENTRY_OFFSET_OR_MARKET_ENTRY_CONTROL"),
        ("far_miss", "Convert far-miss rows into avoid/retest-redesign controls.", "FAR_MISS_AVOID_OR_RETEST_REDESIGN_CONTROL"),
        ("source_alignment", "Repair source-alignment conflict families, including partial/source-recheck rows.", "SOURCE_ALIGNMENT_CONFLICT_SPLIT"),
        ("same_m15", "Join and split same-M15 ambiguity before interpreting target/stop descriptors.", "SAME_M15_AMBIGUITY_SPLIT"),
        ("exact_spread", "Split exact-spread interval/source-stress families.", "EXACT_SPREAD_INTERVAL_OR_SOURCE_STRESS"),
    ]
    question_rows = []
    for seq, (slug, question, action) in enumerate(question_specs, 1):
        affected = action_counts.get(action, 0)
        question_rows.append(
            {
                "question_id": f"OHLC-GTOS-COST-FILL-PATH-SYNTH-QUESTION-{seq:03d}",
                "question_slug": slug,
                "question": question,
                "affected_family_rows": affected,
                "next_action": "ACTIVE_COMPUTATION_ROUTE" if affected else "PRESERVE_FOR_RECHECK_AFTER_NEW_JOIN",
                "source_manifest_hash": manifest_hash,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_QUESTION",
            }
        )

    counts = {
        "cost_family_input_rows": len(inputs["cost_family"]),
        "recovered_family_input_rows": len(inputs["recovered_family"]),
        "confirmed_nofill_family_input_rows": len(inputs["confirmed_nofill_family"]),
        "source_alignment_family_input_rows": len(inputs["source_alignment_family"]),
        "m1_spread_family_input_rows": len(inputs["m1_spread_family"]),
        "m1_spread_signature_input_rows": len(inputs["m1_spread_signature"]),
        "m1_fill_bar_family_input_rows": len(inputs["m1_fill_bar_family"]),
        "m1_fill_bar_signature_input_rows": len(inputs["m1_fill_bar_signature"]),
        "partial_repair_entry_input_rows": len(inputs["partial_repair_entry"]),
        "partial_repair_signature_input_rows": len(inputs["partial_repair_signature"]),
        "target_stop_contract_input_rows": len(target_stop_contracts),
        "family_synthesis_rows": len(family_rows),
        "branch_queue_rows": len(branch_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_cost_fill_path_family_synthesis_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_FILL_PATH_FAMILY_SYNTHESIS_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This cost/fill/path family synthesis does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "branch_queue_status_counts": dict(status_counts),
        "branch_action_counts": dict(action_counts),
        "source_combo_counts": dict(source_combo_counts),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "run M1 fill-bar ordering stress for unresolved fill-bar target/stop rows",
            "run partial/source-recheck repair for source-alignment leftovers",
            "run near-miss entry-offset and market-entry controls",
            "run far-miss avoid/retest-redesign controls",
            "materialize src/execution/orchestrator proposal patches from fillability evidence",
        ],
    }

    write_jsonl(FAMILY_SYNTHESIS_PATH, family_rows)
    write_jsonl(BRANCH_QUEUE_PATH, branch_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "# Historical OHLC GTOS Replay Cost/Fill/Path Family Synthesis\n\n"
        f"Generated UTC: `{generated_at}`\n\n"
        "This packet joins all currently available family-level replay evidence into one branch queue.\n\n"
        "## Counts\n\n"
        + "\n".join(f"- `{key}`: `{value}`" for key, value in counts.items())
        + "\n\n## Branch Queue Status\n\n"
        + "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(status_counts.items()))
        + "\n\n## Immediate Work\n\n"
        + "\n".join(f"- {item}" for item in output["next_same_resource_work"])
        + "\n\nNo validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.\n",
        encoding="utf-8",
    )
    update_manifest(output, generated_at)
    append_sprint_ledger(output, generated_at)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
