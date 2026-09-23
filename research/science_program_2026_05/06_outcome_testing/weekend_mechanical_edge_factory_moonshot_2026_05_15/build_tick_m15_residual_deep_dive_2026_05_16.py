#!/usr/bin/env python3
"""Deep-dive every Route C residual descriptor after full controls.

This is not a completion packet. It turns the first full-control pass into
more work: date/month deconcentration stress, all flagged-date contributions,
all flagged-index clusters, sign anatomy, failure intelligence, and question
avalanche rows for every residual descriptor.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

TARGET_EVENT_LEDGER = ROUTE_DIR / f"TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_{SOURCE_STAMP}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"TICK_M15_FULL_PERMUTATION_CONCENTRATION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"TICK_M15_RESIDUAL_DEEP_DIVE_RESULT_{STAMP}.json"
DATE_CONTRIBUTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_DATE_CONTRIBUTION_LEDGER_{STAMP}.jsonl"
MONTH_CONTRIBUTION_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_MONTH_CONTRIBUTION_LEDGER_{STAMP}.jsonl"
DECONCENTRATION_STRESS_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_DECONCENTRATION_STRESS_LEDGER_{STAMP}.jsonl"
INDEX_CLUSTER_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_INDEX_CLUSTER_LEDGER_{STAMP}.jsonl"
SIGN_ANATOMY_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_SIGN_ANATOMY_LEDGER_{STAMP}.jsonl"
FAILURE_INTELLIGENCE_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_FAILURE_INTELLIGENCE_LEDGER_{STAMP}.jsonl"
QUESTION_AVALANCHE_LEDGER = ROUTE_DIR / f"TICK_M15_RESIDUAL_QUESTION_AVALANCHE_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_M15_RESIDUAL_DEEP_DIVE_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C residual deep-dive diagnostics only; not validation, trade outcome, "
    "R/PnL, expectancy, live-readiness, or promotion"
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    return value


def mean(values: list[float]) -> float | None:
    return safe_float(sum(values) / len(values)) if values else None


def rate(values: list[bool]) -> float | None:
    return safe_float(sum(1 for value in values if value) / len(values)) if values else None


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    changes = [
        safe_float(row.get("future_change"))
        for row in rows
        if safe_float(row.get("future_change")) is not None
    ]
    abs_changes = [
        safe_float(row.get("future_abs_change"))
        for row in rows
        if safe_float(row.get("future_abs_change")) is not None
    ]
    align = [
        bool(row["delta_aligned_with_future"])
        for row in rows
        if row.get("delta_sign", 0) != 0 and row.get("future_sign", 0) != 0
    ]
    return {
        "n": len(rows),
        "mean_future_change": mean(changes),
        "mean_abs_future_change": mean(abs_changes),
        "delta_alignment_n": len(align),
        "delta_alignment_rate": rate(align),
    }


def deterministic_hash_score(seed: int, row: dict[str, Any]) -> str:
    text = f"{seed}|{row['symbol']}|{row['session_bucket']}|{row['horizon_id']}|{row['bar_open_utc']}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_orders(denom_rows: list[dict[str, Any]]) -> list[list[int]]:
    denom_n = len(denom_rows)
    orders: list[list[int]] = []
    for seed in range(1, denom_n):
        orders.append(sorted(range(denom_n), key=lambda idx, s=seed: deterministic_hash_score(s, denom_rows[idx])))
    return orders


def tail_fraction_ge(observed: float | None, values: list[float]) -> float | None:
    numeric = [value for value in values if safe_float(value) is not None]
    if observed is None or not numeric:
        return None
    return safe_float(sum(1 for value in numeric if value >= observed) / len(numeric))


def control_tail_for_indices(
    denom_rows: list[dict[str, Any]],
    selected_indices: list[int],
    precomputed_hash_orders: list[list[int]],
) -> dict[str, Any]:
    selected_rows = [denom_rows[idx] for idx in selected_indices]
    observed = stats(selected_rows)
    denom_n = len(denom_rows)
    selected_n = len(selected_indices)
    if denom_n <= 1 or selected_n < 1:
        return {
            "remaining_n": selected_n,
            "observed_mean_abs_future_change": observed["mean_abs_future_change"],
            "observed_delta_alignment_rate": observed["delta_alignment_rate"],
            "circular_tail_fraction_ge_observed_abs": None,
            "hash_tail_fraction_ge_observed_abs": None,
        }

    circular_abs: list[float] = []
    hash_abs: list[float] = []
    for shift in range(1, denom_n):
        circular_rows = [denom_rows[(idx + shift) % denom_n] for idx in selected_indices]
        circular_value = safe_float(stats(circular_rows)["mean_abs_future_change"])
        if circular_value is not None:
            circular_abs.append(circular_value)
    for order in precomputed_hash_orders:
        hash_rows = [denom_rows[idx] for idx in order[:selected_n]]
        hash_value = safe_float(stats(hash_rows)["mean_abs_future_change"])
        if hash_value is not None:
            hash_abs.append(hash_value)

    return {
        "remaining_n": selected_n,
        "observed_mean_abs_future_change": observed["mean_abs_future_change"],
        "observed_delta_alignment_rate": observed["delta_alignment_rate"],
        "circular_tail_fraction_ge_observed_abs": tail_fraction_ge(observed["mean_abs_future_change"], circular_abs),
        "hash_tail_fraction_ge_observed_abs": tail_fraction_ge(observed["mean_abs_future_change"], hash_abs),
    }


def index_runs(indices: list[int]) -> list[tuple[int, int]]:
    if not indices:
        return []
    ordered = sorted(indices)
    runs: list[tuple[int, int]] = []
    start = ordered[0]
    previous = ordered[0]
    for value in ordered[1:]:
        if value == previous + 1:
            previous = value
            continue
        runs.append((start, previous))
        start = value
        previous = value
    runs.append((start, previous))
    return runs


def log10_combination(n: int, k: int) -> float | None:
    if k < 0 or k > n:
        return None
    return safe_float((math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(10))


def stress_bucket(stress: dict[str, Any]) -> str:
    circ = stress.get("circular_tail_fraction_ge_observed_abs")
    hsh = stress.get("hash_tail_fraction_ge_observed_abs")
    n = stress.get("remaining_n", 0)
    if n < 20 or circ is None or hsh is None:
        return "STRESS_UNDERPOWERED"
    if circ <= 0.05 and hsh <= 0.05:
        return "STRESS_RESIDUAL_REMAINS_LOW_TAIL"
    if circ <= 0.05 or hsh <= 0.05:
        return "STRESS_MIXED"
    return "STRESS_WEAKENED"


def interpretation_for(row: dict[str, Any], stress_rows: list[dict[str, Any]]) -> dict[str, Any]:
    base_bucket = row["control_bucket"]
    stress_counts = Counter(stress["stress_bucket"] for stress in stress_rows)
    if base_bucket == "WEAKENED_BY_CIRCULAR_AND_HASH_CONTROL":
        intelligence_class = "control_explained_or_generic_movement_candidate"
        next_action = "mine_as_failure_intelligence_and_check_inverse_or_avoid_use_before_discarding"
    elif base_bucket == "MIXED_AFTER_CIRCULAR_OR_HASH_CONTROL":
        intelligence_class = "mixed_mechanism_requires_split"
        next_action = "split_by_date_month_horizon_direction_and_source_proxy_before_candidate_language"
    elif base_bucket == "DESCRIPTIVE_RESIDUAL_WITH_CONCENTRATION_CAUTION":
        if stress_counts.get("STRESS_RESIDUAL_REMAINS_LOW_TAIL", 0):
            intelligence_class = "residual_candidate_but_concentration_repair_required"
            next_action = "deconcentrate_with sealed_or_forward_rows_and_entry_cost_packet"
        else:
            intelligence_class = "concentration_dependent_residual_candidate"
            next_action = "treat_as_concentration_mechanism_or event-window artifact until deconcentrated"
    else:
        intelligence_class = "diagnostic_followup_required"
        next_action = "preserve_all_rows_and_generate_next_same_resource_test"
    return {
        "intelligence_class": intelligence_class,
        "next_action": next_action,
        "stress_bucket_counts": dict(stress_counts),
    }


def residual_questions(row: dict[str, Any], interpretation: dict[str, Any]) -> list[dict[str, Any]]:
    queue_id = row["queue_id"]
    stem = {
        "queue_id": queue_id,
        "route_id": ROUTE_ID,
        "symbol": row["symbol"],
        "session_bucket": row["session_bucket"],
        "horizon_id": row["horizon_id"],
        "primitive_flag": row["primitive_flag"],
        "source_control_bucket": row["control_bucket"],
        "safe_flags": SAFE_FLAGS,
    }
    templates = [
        (
            "date_deconcentration",
            "Does the descriptor survive every leave-one-date stress row, or is it a few event dates wearing a signal costume?",
            "TICK_M15_RESIDUAL_DECONCENTRATION_STRESS_LEDGER_2026-05-16.jsonl",
        ),
        (
            "month_deconcentration",
            "Does the descriptor survive leave-one-month stress, or is the month acting as a hidden regime/source artifact?",
            "TICK_M15_RESIDUAL_DECONCENTRATION_STRESS_LEDGER_2026-05-16.jsonl",
        ),
        (
            "direction_vs_magnitude",
            "Is the usable information directional alignment, absolute movement expansion, or only generic volatility?",
            "TICK_M15_RESIDUAL_SIGN_ANATOMY_LEDGER_2026-05-16.jsonl",
        ),
        (
            "horizon_split",
            "Does this primitive strengthen, weaken, or invert across h4/h16/h32 on the same symbol/session denominator?",
            "future_same_resource_cross_horizon_join",
        ),
        (
            "session_transfer",
            "Does the primitive transfer between off-core and kill-zone/core sessions, or is session context the real mechanism?",
            "future_same_resource_cross_session_join",
        ),
        (
            "entry_geometry",
            "What mechanically defined entry/stop/target geometry could make this movement tradable instead of merely descriptive?",
            "entry_geometry_and_cost_packet_required",
        ),
        (
            "execution_friction",
            "Would spread, slippage, commission, and fill timing erase, invert, or select this movement descriptor?",
            "spread_slippage_commission_packet_required",
        ),
        (
            "source_proxy",
            "Would Sierra depth/SCID or futures proxy data confirm the MT5 aggressor proxy, contradict it, or split it by venue?",
            "sierra_binary_parser_timestamp_contract_required",
        ),
        (
            "avoid_or_router_use",
            "If not an entry signal, can this descriptor become an avoid filter, horizon selector, volatility router, or risk throttle?",
            interpretation["next_action"],
        ),
    ]
    out: list[dict[str, Any]] = []
    for idx, (question_type, question, owner) in enumerate(templates, 1):
        row_out = dict(stem)
        row_out.update({
            "question_id": f"{queue_id}-Q{idx:02d}",
            "question_type": question_type,
            "question": question,
            "current_owner_or_artifact": owner,
            "status": "answered_here_if_matching_deep_dive_artifact_else_open_same_resource_or_next_packet",
            "evidence_boundary": EVIDENCE_BOUNDARY,
        })
        out.append(row_out)
    return out


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "tick_m15_residual_deep_dive_builder", "created"),
        (RESULT_PATH, "tick_m15_residual_deep_dive_result", "created"),
        (DATE_CONTRIBUTION_LEDGER, "tick_m15_residual_date_contribution_ledger", "created"),
        (MONTH_CONTRIBUTION_LEDGER, "tick_m15_residual_month_contribution_ledger", "created"),
        (DECONCENTRATION_STRESS_LEDGER, "tick_m15_residual_deconcentration_stress_ledger", "created"),
        (INDEX_CLUSTER_LEDGER, "tick_m15_residual_index_cluster_ledger", "created"),
        (SIGN_ANATOMY_LEDGER, "tick_m15_residual_sign_anatomy_ledger", "created"),
        (FAILURE_INTELLIGENCE_LEDGER, "tick_m15_residual_failure_intelligence_ledger", "created"),
        (QUESTION_AVALANCHE_LEDGER, "tick_m15_residual_question_avalanche", "created"),
        (SUMMARY_PATH, "tick_m15_residual_deep_dive_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], failure_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "tick_m15_residual_deep_dive",
        "status": "done",
        "route": "tick_sierra_orderflow_route_c",
        "details": (
            "Deep-dived every Route C residual descriptor with date/month contributions, leave-date/month-out "
            "deconcentration stress, index clusters, sign anatomy, failure intelligence, and question avalanche rows."
        ),
        "counts": counts,
        "failure_intelligence_counts": failure_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(DATE_CONTRIBUTION_LEDGER),
            relative(DECONCENTRATION_STRESS_LEDGER),
            relative(FAILURE_INTELLIGENCE_LEDGER),
            relative(QUESTION_AVALANCHE_LEDGER),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    target_rows = read_jsonl(TARGET_EVENT_LEDGER)
    control_rows = read_jsonl(CONTROL_LEDGER)

    denominator_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in target_rows:
        key = (row["symbol"], row["session_bucket"], row["horizon_id"])
        denominator_by_key.setdefault(key, []).append(row)
    for rows in denominator_by_key.values():
        rows.sort(key=lambda value: value["bar_open_utc"])

    date_rows: list[dict[str, Any]] = []
    month_rows: list[dict[str, Any]] = []
    stress_rows: list[dict[str, Any]] = []
    cluster_rows: list[dict[str, Any]] = []
    sign_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []

    for control in control_rows:
        key = (control["symbol"], control["session_bucket"], control["horizon_id"])
        denom_rows = denominator_by_key[key]
        primitive_flag = control["primitive_flag"]
        flagged_indices = [
            idx for idx, row in enumerate(denom_rows)
            if primitive_flag in row.get("primitive_flags", [])
        ]
        flagged_rows = [denom_rows[idx] for idx in flagged_indices]
        precomputed_hash_orders = hash_orders(denom_rows)
        queue_id = control["queue_id"]

        date_to_indices: dict[str, list[int]] = {}
        month_to_indices: dict[str, list[int]] = {}
        for idx in flagged_indices:
            date = denom_rows[idx]["bar_open_utc"][:10]
            month = denom_rows[idx]["bar_open_utc"][:7]
            date_to_indices.setdefault(date, []).append(idx)
            month_to_indices.setdefault(month, []).append(idx)

        denom_date_counts = Counter(row["bar_open_utc"][:10] for row in denom_rows)
        denom_month_counts = Counter(row["bar_open_utc"][:7] for row in denom_rows)

        for date, indices in sorted(date_to_indices.items()):
            subset = [denom_rows[idx] for idx in indices]
            subset_stats = stats(subset)
            date_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "event_date": date,
                "event_month": date[:7],
                "flagged_date_n": len(indices),
                "denominator_date_n": denom_date_counts[date],
                "flagged_share_of_residual": safe_float(len(indices) / len(flagged_indices)) if flagged_indices else None,
                "flagged_share_of_date_denominator": safe_float(len(indices) / denom_date_counts[date]) if denom_date_counts[date] else None,
                "date_stats": subset_stats,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

            remaining = [idx for idx in flagged_indices if idx not in set(indices)]
            stress = control_tail_for_indices(denom_rows, remaining, precomputed_hash_orders)
            stress.update({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "stress_type": "leave_one_event_date_out",
                "removed_key": date,
                "removed_n": len(indices),
                "original_flagged_n": len(flagged_indices),
                "stress_bucket": stress_bucket(stress),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })
            stress_rows.append(stress)

        for month, indices in sorted(month_to_indices.items()):
            subset = [denom_rows[idx] for idx in indices]
            subset_stats = stats(subset)
            month_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "event_month": month,
                "flagged_month_n": len(indices),
                "denominator_month_n": denom_month_counts[month],
                "flagged_share_of_residual": safe_float(len(indices) / len(flagged_indices)) if flagged_indices else None,
                "flagged_share_of_month_denominator": safe_float(len(indices) / denom_month_counts[month]) if denom_month_counts[month] else None,
                "month_stats": subset_stats,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

            remaining = [idx for idx in flagged_indices if idx not in set(indices)]
            stress = control_tail_for_indices(denom_rows, remaining, precomputed_hash_orders)
            stress.update({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "stress_type": "leave_one_event_month_out",
                "removed_key": month,
                "removed_n": len(indices),
                "original_flagged_n": len(flagged_indices),
                "stress_bucket": stress_bucket(stress),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })
            stress_rows.append(stress)

        for cluster_idx, (start, end) in enumerate(index_runs(flagged_indices), 1):
            indices = list(range(start, end + 1))
            subset = [denom_rows[idx] for idx in indices if idx in set(flagged_indices)]
            if not subset:
                continue
            cluster_rows.append({
                "cluster_id": f"{queue_id}-CLUSTER-{cluster_idx:04d}",
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "start_denominator_index": start,
                "end_denominator_index": end,
                "cluster_n": len(subset),
                "start_bar_open_utc": subset[0]["bar_open_utc"],
                "end_bar_open_utc": subset[-1]["bar_open_utc"],
                "event_dates": sorted({row["bar_open_utc"][:10] for row in subset}),
                "event_months": sorted({row["bar_open_utc"][:7] for row in subset}),
                "cluster_stats": stats(subset),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

        grouped_by_sign: dict[tuple[int, int], list[dict[str, Any]]] = {}
        for row in flagged_rows:
            grouped_by_sign.setdefault((int(row.get("delta_sign", 0)), int(row.get("future_sign", 0))), []).append(row)
        for (delta_sign, future_sign), subset in sorted(grouped_by_sign.items()):
            sign_rows.append({
                "queue_id": queue_id,
                "route_id": ROUTE_ID,
                "symbol": control["symbol"],
                "session_bucket": control["session_bucket"],
                "horizon_id": control["horizon_id"],
                "primitive_flag": primitive_flag,
                "delta_sign": delta_sign,
                "future_sign": future_sign,
                "sign_group_n": len(subset),
                "sign_group_share": safe_float(len(subset) / len(flagged_rows)) if flagged_rows else None,
                "sign_group_stats": stats(subset),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            })

        own_stress_rows = [row for row in stress_rows if row["queue_id"] == queue_id]
        interpretation = interpretation_for(control, own_stress_rows)
        failure_rows.append({
            "queue_id": queue_id,
            "route_id": ROUTE_ID,
            "symbol": control["symbol"],
            "session_bucket": control["session_bucket"],
            "horizon_id": control["horizon_id"],
            "primitive_flag": primitive_flag,
            "source_control_bucket": control["control_bucket"],
            "flagged_n": control["flagged_n"],
            "denominator_n": control["denominator_n"],
            "log10_combinatorial_row_subsets_same_n": log10_combination(control["denominator_n"], control["flagged_n"]),
            "control_proxy_count": (
                control["circular_shift_abs_change"]["control_count"]
                + control["hash_shuffle_abs_change"]["control_count"]
            ),
            "concentration_warnings": control["concentration"]["concentration_warnings"],
            "failure_or_residual_intelligence_class": interpretation["intelligence_class"],
            "stress_bucket_counts": interpretation["stress_bucket_counts"],
            "next_action": interpretation["next_action"],
            "not_a_completion": True,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        })
        question_rows.extend(residual_questions(control, interpretation))

    write_jsonl(DATE_CONTRIBUTION_LEDGER, date_rows)
    write_jsonl(MONTH_CONTRIBUTION_LEDGER, month_rows)
    write_jsonl(DECONCENTRATION_STRESS_LEDGER, stress_rows)
    write_jsonl(INDEX_CLUSTER_LEDGER, cluster_rows)
    write_jsonl(SIGN_ANATOMY_LEDGER, sign_rows)
    write_jsonl(FAILURE_INTELLIGENCE_LEDGER, failure_rows)
    write_jsonl(QUESTION_AVALANCHE_LEDGER, question_rows)

    failure_counts = Counter(row["failure_or_residual_intelligence_class"] for row in failure_rows)
    stress_counts = Counter(row["stress_bucket"] for row in stress_rows)
    counts = {
        "residual_rows": len(control_rows),
        "date_contribution_rows": len(date_rows),
        "month_contribution_rows": len(month_rows),
        "deconcentration_stress_rows": len(stress_rows),
        "index_cluster_rows": len(cluster_rows),
        "sign_anatomy_rows": len(sign_rows),
        "failure_intelligence_rows": len(failure_rows),
        "question_avalanche_rows": len(question_rows),
    }
    result = {
        "schema": "tick_m15_residual_deep_dive_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_RESIDUAL_DEEP_DIVE_DIAGNOSTIC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "failure_intelligence_counts": dict(failure_counts),
        "stress_bucket_counts": dict(stress_counts),
        "next_same_resource_work": [
            "cross_horizon_join_for_each_symbol_session_primitive",
            "cross_session_transfer_join_for_each_symbol_primitive_horizon",
            "entry_geometry_and_cost_packet_for_remaining_residual_information",
            "sierra_depth_scid_parser_timestamp_contract_for_proxy_repair",
            "future_or_sealed_rows_to_deconcentrate_month_and_date_cautions",
        ],
        "not_completion": "This deep dive opens more same-resource work and does not complete the 60-hour objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick M15 Residual Deep Dive",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: residual diagnostics only. This is not validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        summary.append(f"- `{key}`: `{value}`")
    summary.extend(["", "## Failure / Residual Intelligence", ""])
    for key, value in sorted(failure_counts.items()):
        summary.append(f"- `{key}`: `{value}`")
    summary.extend(["", "## Stress Buckets", ""])
    for key, value in sorted(stress_counts.items()):
        summary.append(f"- `{key}`: `{value}`")
    summary.extend([
        "",
        "## Next Same-Resource Work",
        "",
        "- Cross-horizon and cross-session joins should be built from the same target ledger before treating any residual as a candidate.",
        "- Entry geometry, costs, and Sierra proxy repair remain active work, not vague future notes.",
        "",
    ])
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, dict(failure_counts))
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
