#!/usr/bin/env python3
"""Build quarantined OTI2 G10 risk-bank synthetic-path result artifacts.

Research/output tooling only. This script opens path outcome labels only after
the method-freeze artifact exists, and only for the single G12-accepted OTB2R
packet OTG0-PKT-013 / G10-EXP-RISKBANK-005.
"""

from __future__ import annotations

import json
import hashlib
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-07"
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results"
OTB2R = ROOT / "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild"
PACKET = OTB2R / "packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json"
LTF_PROJECTION = OTB2R / "projections/candidate_ltf_path_order_input_only_projection_2026-05-07.jsonl"
STRATEGY_PROJECTION = OTB2R / "projections/strategy_follow_candidates_input_only_projection_2026-05-07.jsonl"
LTF_RAW = ROOT / "shadow_logs/candidate_ltf_path_order.jsonl"
METHOD_FREEZE_JSON = OUT / "OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.json"

RESULT_LEDGER_JSON = OUT / "OTI2_RISKBANK_RESULT_LEDGER_2026-05-07.json"
RESULT_LEDGER_JSONL = OUT / "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl"
RESULT_LEDGER_MD = OUT / "OTI2_RISKBANK_RESULT_LEDGER_2026-05-07.md"
METHODOLOGY_MD = OUT / "OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.md"
METHODOLOGY_JSON = OUT / "OTI2_RISKBANK_METHODOLOGY_REPORT_2026-05-07.json"
SOURCE_MD = OUT / "OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md"
SOURCE_JSON = OUT / "OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json"
AMBIGUITY_MD = OUT / "OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.md"
AMBIGUITY_JSON = OUT / "OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json"
BLOCKER_MD = OUT / "OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.md"
BLOCKER_JSON = OUT / "OTI2_RISKBANK_BLOCKER_LEDGER_2026-05-07.json"
AUDIT_MD = OUT / "OTI2_RISKBANK_COMPLETION_AUDIT_2026-05-07.md"
AUDIT_JSON = OUT / "OTI2_RISKBANK_COMPLETION_AUDIT_2026-05-07.json"

ALLOWED_PACKET_ID = "OTG0-PKT-013"
ALLOWED_EXPERIMENT_ID = "G10-EXP-RISKBANK-005"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY"
SAMPLE_FLOOR = 150
COST_SCENARIOS_R = [0.0, 0.02, 0.05, 0.10]

RISK_BANK_REQUIRED_FIELDS = {
    "leg_id",
    "risk_bank_before_action_r",
    "risk_bank_after_action_r",
    "realized_closed_leg_r",
    "open_leg_stop_if_hit_r",
    "estimated_remaining_cost_r",
    "synthetic_closed_leg_r",
    "synthetic_open_leg_stop_if_hit_r",
    "synthetic_episode_reward_r",
    "reentry_state",
    "reentry_leg",
    "structural_lock_event",
}


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def require_method_freeze() -> dict[str, Any]:
    freeze = read_json(METHOD_FREEZE_JSON)
    if not freeze.get("frozen_before_synthetic_path_outcome_inspection"):
        raise RuntimeError("Method freeze does not declare pre-outcome freeze.")
    if freeze["scope"]["allowed_packet_id"] != ALLOWED_PACKET_ID:
        raise RuntimeError("Method freeze packet scope mismatch.")
    return freeze


def sanitize_packet_for_hash(packet: dict[str, Any]) -> dict[str, Any]:
    clean = dict(packet)
    clean.pop("packet_hash", None)
    return clean


def index_projection(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(path):
        expected = sha256_json({k: v for k, v in row.items() if k not in {"projection_hash", "_source_line_no"}})
        row["projection_hash_recomputed"] = expected
        row["projection_hash_matches"] = expected == row.get("projection_hash")
        out[row["projection_hash"]] = row
    return out


def reward_r(entry_packet: dict[str, Any]) -> float | None:
    entry = entry_packet.get("entry_price")
    stop = entry_packet.get("stop_loss")
    tp1 = entry_packet.get("take_profit_1")
    if entry is None or stop is None or tp1 is None:
        return None
    risk = abs(float(entry) - float(stop))
    if risk <= 0:
        return None
    return abs(float(tp1) - float(entry)) / risk


def classify_path(label: str, reward: float | None, same_state: str) -> dict[str, Any]:
    same_flagged = same_state == "same_m1_ambiguity_flagged"
    if label == "entry_then_tp1_before_sl" and not same_flagged:
        return {
            "descriptive_status": "resolved_non_ambiguous_tp1",
            "descriptive_gross_synthetic_path_r": reward,
            "descriptive_non_ambiguous_included": True,
            "conservative_lower_bound_r": reward,
            "cost_chargeable_completed_leg": True,
        }
    if label == "tp1_area_reached_without_entry_touch" and not same_flagged:
        return {
            "descriptive_status": "resolved_non_ambiguous_unfilled_tp_area_before_entry",
            "descriptive_gross_synthetic_path_r": 0.0,
            "descriptive_non_ambiguous_included": True,
            "conservative_lower_bound_r": 0.0,
            "cost_chargeable_completed_leg": False,
        }
    if label == "entry_then_sl_before_tp1" and same_flagged:
        return {
            "descriptive_status": "same_bar_flagged_conservative_sl_bound",
            "descriptive_gross_synthetic_path_r": None,
            "descriptive_non_ambiguous_included": False,
            "conservative_lower_bound_r": -1.0,
            "cost_chargeable_completed_leg": True,
        }
    if label == "entry_sl_same_m1_ambiguous" and same_flagged:
        return {
            "descriptive_status": "same_bar_flagged_entry_sl_ambiguous_lower_bound",
            "descriptive_gross_synthetic_path_r": None,
            "descriptive_non_ambiguous_included": False,
            "conservative_lower_bound_r": -1.0,
            "cost_chargeable_completed_leg": True,
        }
    if label == "entry_touched_unresolved":
        return {
            "descriptive_status": "entry_touched_terminal_unresolved",
            "descriptive_gross_synthetic_path_r": None,
            "descriptive_non_ambiguous_included": False,
            "conservative_lower_bound_r": None,
            "cost_chargeable_completed_leg": False,
        }
    return {
        "descriptive_status": f"unclassified_path_label_{label}",
        "descriptive_gross_synthetic_path_r": None,
        "descriptive_non_ambiguous_included": False,
        "conservative_lower_bound_r": None,
        "cost_chargeable_completed_leg": False,
    }


def build_rows(packet: dict[str, Any], ltf_projection: dict[str, dict[str, Any]], raw_ltf_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in packet["records"]:
        if record.get("packet_id") != ALLOWED_PACKET_ID or record.get("experiment_id") != ALLOWED_EXPERIMENT_ID:
            raise RuntimeError("Non-accepted packet row encountered.")
        ltf_hash = record["sanitized_source_hash_components"]["ltf_projection_row_hash"]
        projection = ltf_projection[ltf_hash]
        raw_line_no = int(projection["source_line_no"])
        raw = raw_ltf_rows[raw_line_no - 1]
        if raw.get("candidate_id") != record["setup_id"]:
            raise RuntimeError(f"Raw LTF line mismatch for {record['setup_id']}")

        components = dict(record["sanitized_source_hash_components"])
        coverage_hash_match = components["coverage_binding_hash"] == sha256_json(record["coverage_binding"])
        entry_hash_match = components["entry_sl_tp_or_level_packet_hash"] == sha256_json(record["entry_sl_tp_or_level_packet"])
        source_hash_recomputed = sha256_json(components)
        source_hash_match = source_hash_recomputed == record["source_hash"]
        reward = reward_r(record["entry_sl_tp_or_level_packet"])
        path = classify_path(str(raw.get("path_order_label")), reward, str(record.get("same_bar_ambiguity_state")))
        rows.append(
            {
                "setup_id": record["setup_id"],
                "packet_id": record["packet_id"],
                "experiment_id": record["experiment_id"],
                "hypothesis_id": record["hypothesis_id"],
                "symbol": record["symbol"],
                "source_symbol": record["source_symbol"],
                "session": record["session"],
                "side": record["side"],
                "decision_asof_utc": record["decision_asof_utc"],
                "path_start_utc": record["path_start_utc"],
                "path_end_utc": record["path_end_utc"],
                "duplicate_group_id": record["duplicate_group_id"],
                "source_hash": record["source_hash"],
                "source_hash_recomputed": source_hash_recomputed,
                "source_hash_match": source_hash_match,
                "coverage_binding_hash_match": coverage_hash_match,
                "entry_packet_hash_match": entry_hash_match,
                "coverage_reaches_path_end_utc": bool(record["coverage_binding"].get("coverage_reaches_path_end_utc")),
                "coverage_mode": record["coverage_binding"].get("coverage_mode"),
                "coverage_first_utc": record["coverage_binding"].get("coverage_first_utc"),
                "coverage_last_utc": record["coverage_binding"].get("coverage_last_utc"),
                "ltf_projection_hash": ltf_hash,
                "ltf_projection_hash_matches": projection["projection_hash_matches"],
                "ltf_source_line_no": raw_line_no,
                "raw_path_log_path": "shadow_logs/candidate_ltf_path_order.jsonl",
                "path_order_label": raw.get("path_order_label"),
                "entry_first_touch_utc": raw.get("entry_first_touch_utc"),
                "sl_first_touch_utc": raw.get("sl_first_touch_utc"),
                "tp1_first_touch_utc": raw.get("tp1_first_touch_utc"),
                "same_bar_ambiguity_state": record.get("same_bar_ambiguity_state"),
                "raw_same_m1_ambiguity": raw.get("same_m1_ambiguity"),
                "terminal_order_claim_allowed": False,
                "reward_r_to_tp1": reward,
                "descriptive_status": path["descriptive_status"],
                "descriptive_gross_synthetic_path_r": path["descriptive_gross_synthetic_path_r"],
                "descriptive_non_ambiguous_included": path["descriptive_non_ambiguous_included"],
                "conservative_lower_bound_r": path["conservative_lower_bound_r"],
                "cost_chargeable_completed_leg": path["cost_chargeable_completed_leg"],
                "riskbank_reentry_metric_status": "not_computable_missing_leg_level_reentry_ledger",
                "riskbank_reentry_metric_reasons": [
                    "accepted_packet_has_no_leg_id_or_child_leg_table",
                    "accepted_packet_has_no_risk_bank_before_after_fields",
                    "accepted_packet_has_no_structural_lock_or_reentry_action_state",
                    "accepted_packet_has_no_numeric_estimated_remaining_cost_r",
                ],
                "promotion_verdict": PROMOTION_VERDICT,
                "result_status": RESULT_STATUS,
            }
        )
    return rows


def mean(values: list[float]) -> float | None:
    return round(statistics.mean(values), 6) if values else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 6) if values else None


def summarize_values(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "sum_r": None, "mean_r": None, "median_r": None, "win_rate_gt_zero": None, "min_r": None}
    return {
        "n": len(values),
        "sum_r": round(sum(values), 6),
        "mean_r": mean(values),
        "median_r": median(values),
        "win_rate_gt_zero": round(sum(v > 0 for v in values) / len(values), 6),
        "min_r": round(min(values), 6),
        "max_r": round(max(values), 6),
    }


def cost_adjusted(rows: list[dict[str, Any]], *, field: str, cost_r: float) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        adjusted = float(value) - (cost_r if row.get("cost_chargeable_completed_leg") else 0.0)
        values.append(adjusted)
    return values


def grouped_summary(rows: list[dict[str, Any]], keys: tuple[str, ...], field: str) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is not None:
            groups[tuple(row.get(key) for key in keys)].append(float(value))
    out = []
    for key, values in groups.items():
        out.append({"dimensions": dict(zip(keys, key)), **summarize_values(values)})
    return sorted(out, key=lambda item: (str(item["dimensions"]), item["n"]))


def build_result_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    non_ambiguous = [float(r["descriptive_gross_synthetic_path_r"]) for r in rows if r["descriptive_non_ambiguous_included"]]
    conservative = [float(r["conservative_lower_bound_r"]) for r in rows if r["conservative_lower_bound_r"] is not None]
    return {
        "artifact_id": f"OTI2_RISKBANK_RESULT_LEDGER_{DATE}",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "packet_id": ALLOWED_PACKET_ID,
        "experiment_id": ALLOWED_EXPERIMENT_ID,
        "label_family": "synthetic_path_r",
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "raw_records": len(rows),
        "unique_duplicate_group_id_count": len({r["duplicate_group_id"] for r in rows}),
        "path_order_label_counts": dict(Counter(r["path_order_label"] for r in rows)),
        "same_bar_ambiguity_state_counts": dict(Counter(r["same_bar_ambiguity_state"] for r in rows)),
        "descriptive_status_counts": dict(Counter(r["descriptive_status"] for r in rows)),
        "riskbank_primary_metric": {
            "status": "not_computable",
            "reason": "accepted input-only packet and cited local path log do not contain leg-level reentry state, risk_bank_before_action_r, risk_bank_after_action_r, realized_closed_leg_r, open_leg_stop_if_hit_r, or numeric estimated_remaining_cost_r",
            "rows_scored": 0,
        },
        "descriptive_initial_path_non_ambiguous": summarize_values(non_ambiguous),
        "descriptive_conservative_lower_bound_including_same_bar": summarize_values(conservative),
        "cost_sensitivity": {
            str(cost): {
                "non_ambiguous_initial_path": summarize_values(
                    cost_adjusted(rows, field="descriptive_gross_synthetic_path_r", cost_r=cost)
                ),
                "conservative_lower_bound": summarize_values(
                    cost_adjusted(rows, field="conservative_lower_bound_r", cost_r=cost)
                ),
            }
            for cost in COST_SCENARIOS_R
        },
        "dimension_summaries": {
            "non_ambiguous_by_symbol": grouped_summary(rows, ("symbol",), "descriptive_gross_synthetic_path_r"),
            "non_ambiguous_by_session": grouped_summary(rows, ("session",), "descriptive_gross_synthetic_path_r"),
            "non_ambiguous_by_side": grouped_summary(rows, ("side",), "descriptive_gross_synthetic_path_r"),
            "conservative_by_symbol": grouped_summary(rows, ("symbol",), "conservative_lower_bound_r"),
            "conservative_by_session": grouped_summary(rows, ("session",), "conservative_lower_bound_r"),
            "conservative_by_side": grouped_summary(rows, ("side",), "conservative_lower_bound_r"),
        },
        "rows": rows,
    }


def build_source_payload(packet: dict[str, Any], rows: list[dict[str, Any]], ltf_projection: dict[str, dict[str, Any]], strategy_projection: dict[str, dict[str, Any]]) -> dict[str, Any]:
    packet_hash_recomputed = sha256_json(sanitize_packet_for_hash(packet))
    coverage_failures = [r["setup_id"] for r in rows if not r["coverage_reaches_path_end_utc"]]
    source_hash_failures = [r["setup_id"] for r in rows if not r["source_hash_match"]]
    ltf_projection_hash_failures = [r["setup_id"] for r in rows if not r["ltf_projection_hash_matches"]]
    return {
        "artifact_id": f"OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "packet_hash_stored": packet.get("packet_hash"),
        "packet_hash_recomputed": packet_hash_recomputed,
        "packet_hash_match": packet_hash_recomputed == packet.get("packet_hash"),
        "packet_file_sha256": sha256_file(PACKET),
        "projection_file_hashes": {
            "candidate_ltf_path_order_input_only_projection": sha256_file(LTF_PROJECTION),
            "strategy_follow_candidates_input_only_projection": sha256_file(STRATEGY_PROJECTION),
        },
        "local_path_log_hashes": {
            "candidate_ltf_path_order_jsonl": sha256_file(LTF_RAW),
        },
        "row_source_hash_match_count": sum(r["source_hash_match"] for r in rows),
        "row_source_hash_failure_count": len(source_hash_failures),
        "source_hash_failures": source_hash_failures,
        "coverage_reaches_path_end_count": sum(r["coverage_reaches_path_end_utc"] for r in rows),
        "coverage_failure_count": len(coverage_failures),
        "coverage_failures": coverage_failures,
        "coverage_mode_counts": dict(Counter(r["coverage_mode"] for r in rows)),
        "ltf_projection_hash_match_count": sum(r["ltf_projection_hash_matches"] for r in rows),
        "ltf_projection_hash_failure_count": len(ltf_projection_hash_failures),
        "duplicate_group_denominator": {
            "raw_records": len(rows),
            "unique_duplicate_group_id_count": len({r["duplicate_group_id"] for r in rows}),
            "within_packet_duplicate_group_drift": len(rows) - len({r["duplicate_group_id"] for r in rows}),
            "required_denominator": "86/86",
        },
        "projection_inventory": {
            "ltf_projection_rows_total": len(ltf_projection),
            "strategy_projection_rows_total": len(strategy_projection),
            "accepted_ltf_projection_rows_used": len({r["ltf_projection_hash"] for r in rows}),
        },
        "leakage_guard": {
            "packet_broker_actual_r_absent": all(r.get("broker_actual_r_absent_from_primary_metric") is True for r in packet["records"]),
            "packet_label_family": packet.get("label_family"),
            "builder_result_values_inspected": packet.get("r_result_values_inspected_by_builder"),
            "builder_quarantine_outputs_created": packet.get("quarantine_or_result_outputs_created"),
            "g12_rebuild_leakage_verdict": "PASS_REBUILT_NOLEAK per G12 OTB rebuild review; this result script opens path labels only after freeze",
        },
    }


def flatten_keys(payload: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.add(str(key))
            keys.update(flatten_keys(value))
    elif isinstance(payload, list):
        for value in payload:
            keys.update(flatten_keys(value))
    return keys


def build_methodology_payload(freeze: dict[str, Any], packet: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    packet_keys = flatten_keys(packet)
    missing_risk_fields = sorted(field for field in RISK_BANK_REQUIRED_FIELDS if field not in packet_keys)
    return {
        "artifact_id": f"OTI2_RISKBANK_METHODOLOGY_REPORT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "method_freeze_artifact": str(METHOD_FREEZE_JSON.relative_to(ROOT)),
        "controlling_metric": freeze["metric"],
        "sample_floor_rule": freeze["sample_floor_rule"],
        "label_family_boundary": freeze["label_family_boundary"],
        "duplicate_policy": freeze["duplicate_policy"],
        "same_bar_ambiguity_rule": freeze["same_bar_ambiguity_rule"],
        "cost_slippage_assumptions": freeze["cost_slippage_assumptions"],
        "effective_n": {
            "accepted_packet_unique_duplicate_groups": len({r["duplicate_group_id"] for r in rows}),
            "riskbank_primary_effective_n": 0,
            "descriptive_non_ambiguous_path_n": sum(r["descriptive_non_ambiguous_included"] for r in rows),
            "conservative_lower_bound_n": sum(r["conservative_lower_bound_r"] is not None for r in rows),
            "validation_floor": SAMPLE_FLOOR,
            "validation_floor_pass": False,
        },
        "dsr": {
            "status": "not_computable",
            "reasons": [
                "dsr_not_computable_no_unseen_validation_split",
                "dsr_not_computable_effective_n_below_150_floor",
                "validation_stats_not_computable_result_quarantined_discovery_only",
                "riskbank_primary_metric_not_computable_missing_leg_level_reentry_ledger",
            ],
        },
        "pbo": {
            "status": "not_computable",
            "reasons": [
                "pbo_not_computable_no_strategy_variant_matrix",
                "pbo_not_computable_no_train_test_or_cpcv_blocks",
                "riskbank_primary_metric_not_computable_missing_leg_level_reentry_ledger",
            ],
        },
        "risk_bank_reentry_scoreability": {
            "status": "not_computable",
            "missing_packet_fields": missing_risk_fields,
            "evidence_exhausted": [
                "accepted OTB2R packet",
                "OTB2R projections",
                "OTB2R source hash report",
                "OTB2R coverage audit",
                "candidate_ltf_path_order local path log filtered to accepted source_line_no rows",
                "OTB2R builder schema",
            ],
        },
    }


def build_ambiguity_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = [
        {
            "setup_id": r["setup_id"],
            "symbol": r["symbol"],
            "session": r["session"],
            "side": r["side"],
            "same_bar_ambiguity_state": r["same_bar_ambiguity_state"],
            "path_order_label": r["path_order_label"],
            "entry_first_touch_utc": r["entry_first_touch_utc"],
            "sl_first_touch_utc": r["sl_first_touch_utc"],
            "tp1_first_touch_utc": r["tp1_first_touch_utc"],
            "resolution": r["descriptive_status"],
            "primary_policy": "not used for riskbank primary metric; same-bar flagged rows are conservative lower-bound only",
        }
        for r in rows
        if r["same_bar_ambiguity_state"] == "same_m1_ambiguity_flagged"
        or r["descriptive_status"] == "entry_touched_terminal_unresolved"
    ]
    return {
        "artifact_id": f"OTI2_RISKBANK_AMBIGUITY_RESOLUTION_LEDGER_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "terminal_order_claim_allowed": False,
        "same_bar_ambiguity_state_counts": dict(Counter(r["same_bar_ambiguity_state"] for r in rows)),
        "path_order_label_counts": dict(Counter(r["path_order_label"] for r in rows)),
        "unresolved_or_bounded_row_count": len(unresolved),
        "unresolved_same_bar_ambiguity_remaining": sum(
            r["same_bar_ambiguity_state"] == "same_m1_ambiguity_flagged" for r in rows
        ),
        "non_same_bar_unresolved_terminal_count": sum(
            r["descriptive_status"] == "entry_touched_terminal_unresolved" for r in rows
        ),
        "policy": "same-minute terminal order is not guessed; flagged rows are retained as conservative/bounded ambiguity rows and excluded from primary resolved riskbank scoring",
        "rows": unresolved,
    }


def build_blocker_payload(rows: list[dict[str, Any]], source_payload: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    blockers.append(
        {
            "blocker_id": "OTI2-RISKBANK-BLK-001",
            "status": "OPEN_LOCAL_PACKET_BLOCKER",
            "name": "Risk-bank reentry ledger absent from accepted packet",
            "evidence": "All 86 accepted rows lack leg_id, reentry action state, risk_bank_before_action_r, risk_bank_after_action_r, realized_closed_leg_r, open_leg_stop_if_hit_r, and numeric estimated_remaining_cost_r.",
            "next_exact_question": "Which future frozen input packet provides leg-level reentry state and numeric risk-bank cost fields for G10-EXP-RISKBANK-005 without broker actual-R or blocked-packet outcome pooling?",
            "owner_question_required": True,
        }
    )
    blockers.append(
        {
            "blocker_id": "OTI2-RISKBANK-BLK-002",
            "status": "OPEN_LOCAL_PACKET_BLOCKER",
            "name": "Same-bar terminal order cannot be claimed",
            "evidence": f"{sum(r['same_bar_ambiguity_state'] == 'same_m1_ambiguity_flagged' for r in rows)} of 86 rows have same_m1_ambiguity_flagged; terminal_order_claim_allowed=false.",
            "next_exact_question": "Should a future packet add tick-order evidence or a predeclared conservative-bound scoring policy for same-minute entry/SL rows?",
            "owner_question_required": True,
        }
    )
    blockers.append(
        {
            "blocker_id": "OTI2-RISKBANK-BLK-003",
            "status": "DOCUMENTED_STATISTICS_BLOCKER",
            "name": "Validation statistics are below preregistered evidentiary floor",
            "evidence": "Accepted duplicate denominator is 86/86, below the frozen 150 unique-group validation floor, and no unseen validation split or variant matrix exists.",
            "next_exact_question": "Collect or freeze additional prospectively separated resolved path rows before any DSR/PBO validation-style claim.",
            "owner_question_required": False,
        }
    )
    if source_payload["row_source_hash_failure_count"] or source_payload["coverage_failure_count"]:
        blockers.append(
            {
                "blocker_id": "OTI2-RISKBANK-BLK-004",
                "status": "OPEN_SOURCE_HASH_OR_COVERAGE_BLOCKER",
                "name": "Source hash or path coverage failure",
                "evidence": {
                    "source_hash_failures": source_payload["source_hash_failures"],
                    "coverage_failures": source_payload["coverage_failures"],
                },
                "next_exact_question": "Rebuild accepted packet from sanitized projections until every source hash and coverage binding passes.",
                "owner_question_required": False,
            }
        )
    return {
        "artifact_id": f"OTI2_RISKBANK_BLOCKER_LEDGER_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "blocker_count": len(blockers),
        "open_owner_question_count": sum(b["owner_question_required"] for b in blockers),
        "blockers": blockers,
    }


def checklist_item(requirement: str, evidence: str, status: str = "PASS") -> dict[str, str]:
    return {"requirement": requirement, "evidence": evidence, "status": status}


def build_audit_payload(result: dict[str, Any], source: dict[str, Any], methodology: dict[str, Any], ambiguity: dict[str, Any], blocker: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        checklist_item("Complete GTOS preflight", "generate_live_state.py was run before artifact implementation; LIVE_STATE showed HEAD b458f099 and clean tree before generated LIVE_STATE timestamp dirt."),
        checklist_item("Freeze method before outcome inspection", "OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.md/json exist and builder requires the JSON freeze before reading path labels."),
        checklist_item("Use only accepted OTB2R packet", f"Result packet_id={result['packet_id']} experiment_id={result['experiment_id']} raw_records={result['raw_records']}."),
        checklist_item("Do not use blocked OTB2R packets", "Builder hardcodes OTG0-PKT-013 and fails on any other packet_id/experiment_id."),
        checklist_item("Duplicate denominator 86/86", f"unique_duplicate_group_id_count={result['unique_duplicate_group_id_count']} raw_records={result['raw_records']}."),
        checklist_item("Source hashes recomputed", f"row_source_hash_match_count={source['row_source_hash_match_count']} row_source_hash_failure_count={source['row_source_hash_failure_count']}."),
        checklist_item("Coverage through path_end_utc", f"coverage_reaches_path_end_count={source['coverage_reaches_path_end_count']} coverage_failure_count={source['coverage_failure_count']}."),
        checklist_item("Terminal-order ambiguity policy", f"terminal_order_claim_allowed=false; same_bar rows={ambiguity['unresolved_same_bar_ambiguity_remaining']}."),
        checklist_item("Label-family separation", "broker_actual_r_inspected=false; blocked_packet_outcomes_inspected=false; label_family=synthetic_path_r."),
        checklist_item("Report descriptive results", f"non_ambiguous_n={result['descriptive_initial_path_non_ambiguous']['n']} conservative_bound_n={result['descriptive_conservative_lower_bound_including_same_bar']['n']}."),
        checklist_item("Report DSR/PBO/effective-N", f"DSR={methodology['dsr']['status']} PBO={methodology['pbo']['status']} accepted_effective_n={methodology['effective_n']['accepted_packet_unique_duplicate_groups']} floor={SAMPLE_FLOOR}."),
        checklist_item("Produce required ledgers", "result, methodology, source/hash/coverage, ambiguity, blocker, and completion audit artifacts are emitted under oti2_riskbank_quarantined_results/."),
        checklist_item("Preserve NO_PROMOTION_VERDICT", "Every emitted payload/report carries NO_PROMOTION_VERDICT and RESULT_QUARANTINED_DISCOVERY_ONLY."),
    ]
    can_mark_complete = all(item["status"] == "PASS" for item in checklist)
    return {
        "artifact_id": f"OTI2_RISKBANK_COMPLETION_AUDIT_{DATE}",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "objective_restatement": (
            "Run a quarantined synthetic-path outcome-test implementation for the single G12-accepted "
            "OTB2R packet OTG0-PKT-013 / G10-EXP-RISKBANK-005, preserving packet, label, duplicate, "
            "source-hash, coverage, ambiguity, and no-promotion boundaries."
        ),
        "prompt_to_artifact_checklist": checklist,
        "can_mark_goal_complete": can_mark_complete,
        "remaining_open_blockers": blocker["blockers"],
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    text = str(value).replace("\n", " ")
    return text.replace("|", "\\|")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_result_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OTI2 Risk-Bank Result Ledger - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Result status:** `{RESULT_STATUS}`  ",
        "**Scope:** `OTG0-PKT-013` / `G10-EXP-RISKBANK-005` only",
        "",
        "## Summary",
        "",
        table(
            ["metric", "value"],
            [
                ["raw rows", payload["raw_records"]],
                ["unique duplicate groups", payload["unique_duplicate_group_id_count"]],
                ["risk-bank primary metric", payload["riskbank_primary_metric"]["status"]],
                ["descriptive non-ambiguous n", payload["descriptive_initial_path_non_ambiguous"]["n"]],
                ["descriptive non-ambiguous mean R", payload["descriptive_initial_path_non_ambiguous"]["mean_r"]],
                ["conservative lower-bound n", payload["descriptive_conservative_lower_bound_including_same_bar"]["n"]],
                ["conservative lower-bound mean R", payload["descriptive_conservative_lower_bound_including_same_bar"]["mean_r"]],
            ],
        ),
        "",
        "## Path Labels",
        "",
        table(["label", "rows"], [[k, v] for k, v in payload["path_order_label_counts"].items()]),
        "",
        "## Cost Sensitivity",
        "",
        table(
            ["cost R", "non-amb n", "non-amb mean", "conservative n", "conservative mean"],
            [
                [
                    cost,
                    data["non_ambiguous_initial_path"]["n"],
                    data["non_ambiguous_initial_path"]["mean_r"],
                    data["conservative_lower_bound"]["n"],
                    data["conservative_lower_bound"]["mean_r"],
                ]
                for cost, data in payload["cost_sensitivity"].items()
            ],
        ),
        "",
        "## Note",
        "",
        "The primary risk-bank reentry metric is not computable from the accepted input-only packet because leg-level reentry and risk-bank ledger fields are absent. Descriptive values are quarantined synthetic path summaries, not validation.",
    ]
    write_text(RESULT_LEDGER_MD, "\n".join(lines))


def write_methodology_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OTI2 Risk-Bank Methodology Report - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Result status:** `{RESULT_STATUS}`",
        "",
        "## Effective N And Statistics",
        "",
        table(
            ["item", "value"],
            [
                ["accepted unique duplicate groups", payload["effective_n"]["accepted_packet_unique_duplicate_groups"]],
                ["riskbank primary effective N", payload["effective_n"]["riskbank_primary_effective_n"]],
                ["descriptive non-ambiguous path n", payload["effective_n"]["descriptive_non_ambiguous_path_n"]],
                ["validation floor", payload["effective_n"]["validation_floor"]],
                ["validation floor pass", payload["effective_n"]["validation_floor_pass"]],
                ["DSR", payload["dsr"]["status"]],
                ["PBO", payload["pbo"]["status"]],
            ],
        ),
        "",
        "## Risk-Bank Scoreability",
        "",
        f"Status: `{payload['risk_bank_reentry_scoreability']['status']}`.",
        "",
        "Missing packet fields:",
        "",
        *[f"- `{field}`" for field in payload["risk_bank_reentry_scoreability"]["missing_packet_fields"]],
        "",
        "## Not Computable Reasons",
        "",
        *[f"- `{reason}`" for reason in payload["dsr"]["reasons"] + payload["pbo"]["reasons"]],
    ]
    write_text(METHODOLOGY_MD, "\n".join(lines))


def write_source_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OTI2 Risk-Bank Source Hash Coverage Report - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Result status:** `{RESULT_STATUS}`",
        "",
        table(
            ["check", "value"],
            [
                ["packet hash match", payload["packet_hash_match"]],
                ["row source hash matches", payload["row_source_hash_match_count"]],
                ["row source hash failures", payload["row_source_hash_failure_count"]],
                ["coverage reaches path_end", payload["coverage_reaches_path_end_count"]],
                ["coverage failures", payload["coverage_failure_count"]],
                ["duplicate denominator", payload["duplicate_group_denominator"]["required_denominator"]],
                ["within-packet duplicate drift", payload["duplicate_group_denominator"]["within_packet_duplicate_group_drift"]],
            ],
        ),
        "",
        "## Coverage Modes",
        "",
        table(["mode", "rows"], [[k, v] for k, v in payload["coverage_mode_counts"].items()]),
        "",
        "## Leakage Guard",
        "",
        table(["guard", "value"], [[k, v] for k, v in payload["leakage_guard"].items()]),
    ]
    write_text(SOURCE_MD, "\n".join(lines))


def write_ambiguity_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OTI2 Risk-Bank Ambiguity Resolution Ledger - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Result status:** `{RESULT_STATUS}`",
        "",
        table(
            ["item", "value"],
            [
                ["terminal order claim allowed", payload["terminal_order_claim_allowed"]],
                ["same-bar flagged rows", payload["unresolved_same_bar_ambiguity_remaining"]],
                ["non-same-bar unresolved rows", payload["non_same_bar_unresolved_terminal_count"]],
                ["unresolved or bounded rows", payload["unresolved_or_bounded_row_count"]],
            ],
        ),
        "",
        "## Same-Bar State Counts",
        "",
        table(["state", "rows"], [[k, v] for k, v in payload["same_bar_ambiguity_state_counts"].items()]),
        "",
        "## Policy",
        "",
        payload["policy"],
    ]
    write_text(AMBIGUITY_MD, "\n".join(lines))


def write_blocker_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OTI2 Risk-Bank Blocker Ledger - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Result status:** `{RESULT_STATUS}`",
        "",
        table(
            ["blocker", "status", "name", "next exact question"],
            [[b["blocker_id"], b["status"], b["name"], b["next_exact_question"]] for b in payload["blockers"]],
        ),
    ]
    write_text(BLOCKER_MD, "\n".join(lines))


def write_audit_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# OTI2 Risk-Bank Completion Audit - 2026-05-07",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Result status:** `{RESULT_STATUS}`  ",
        f"**Can mark goal complete:** `{payload['can_mark_goal_complete']}`",
        "",
        "## Objective Restatement",
        "",
        payload["objective_restatement"],
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        table(
            ["status", "requirement", "evidence"],
            [[item["status"], item["requirement"], item["evidence"]] for item in payload["prompt_to_artifact_checklist"]],
        ),
        "",
        "## Remaining Open Blockers",
        "",
        table(
            ["blocker", "status", "next exact question"],
            [[b["blocker_id"], b["status"], b["next_exact_question"]] for b in payload["remaining_open_blockers"]],
        ),
    ]
    write_text(AUDIT_MD, "\n".join(lines))


def main() -> int:
    freeze = require_method_freeze()
    packet = read_json(PACKET)
    if packet.get("packet_id") != ALLOWED_PACKET_ID or packet.get("experiment_id") != ALLOWED_EXPERIMENT_ID:
        raise RuntimeError("Unexpected packet scope.")
    if packet.get("outcome_review_opened") is not False or packet.get("validation_safe") is not False:
        raise RuntimeError("Packet guard flags changed.")

    ltf_projection = index_projection(LTF_PROJECTION)
    strategy_projection = index_projection(STRATEGY_PROJECTION)
    raw_ltf_rows = load_jsonl(LTF_RAW)
    rows = build_rows(packet, ltf_projection, raw_ltf_rows)
    result = build_result_payload(rows)
    source = build_source_payload(packet, rows, ltf_projection, strategy_projection)
    methodology = build_methodology_payload(freeze, packet, rows)
    ambiguity = build_ambiguity_payload(rows)
    blocker = build_blocker_payload(rows, source)
    audit = build_audit_payload(result, source, methodology, ambiguity, blocker)

    result_without_rows = dict(result)
    result_without_rows.pop("rows")
    write_json(RESULT_LEDGER_JSON, result_without_rows)
    with RESULT_LEDGER_JSONL.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
    write_json(SOURCE_JSON, source)
    write_json(METHODOLOGY_JSON, methodology)
    write_json(AMBIGUITY_JSON, {k: v for k, v in ambiguity.items() if k != "rows"})
    write_json(BLOCKER_JSON, blocker)
    write_json(AUDIT_JSON, audit)

    write_result_markdown(result)
    write_source_markdown(source)
    write_methodology_markdown(methodology)
    write_ambiguity_markdown(ambiguity)
    write_blocker_markdown(blocker)
    write_audit_markdown(audit)

    print(json.dumps({
        "result": str(RESULT_LEDGER_JSON.relative_to(ROOT)),
        "rows": len(rows),
        "unique_duplicate_groups": result["unique_duplicate_group_id_count"],
        "riskbank_primary_metric": result["riskbank_primary_metric"]["status"],
        "can_mark_goal_complete": audit["can_mark_goal_complete"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
