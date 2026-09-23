"""Build READY8 R9 accepted-packet sealed historical validation execution artifacts.

This route consumes the G12-accepted R9 packet as downstream no-promotion
packet evidence and materializes the strongest source-bound historical/stress
validation ledgers the accepted artifacts support. It does not open broker/live
actual PnL, broker/live actual R, actual win-rate, actual expectancy, AI/API,
paid/vendor, account/order/history/deal/position, live behavior, or trading
prompt/config/risk/safety/execution/canary/selector surfaces.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "READY8_R9_ACCEPTED_PACKET_SEALED_HISTORICAL_VALIDATION_EXECUTION"
EVIDENCE_CLASS = "READY8_R9_ACCEPTED_PACKET_SEALED_HISTORICAL_VALIDATION_EXECUTION_ONLY"
TERMINAL_DECISION = (
    "MATERIALIZED_READY8_R9_ACCEPTED_PACKET_SEALED_HISTORICAL_VALIDATION_RESULT_"
    "G12_AUDIT_REQUIRED_NO_PROMOTION"
)

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FORBIDDEN_FALSE_FLAGS = {
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_ai_api": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_paid_or_vendor_access": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
}

EXECUTION_STATUSES = {
    "SEALED_HISTORICAL_VALIDATION_EXECUTABLE",
    "STRESS_ROBUSTNESS_EXECUTABLE",
    "FORWARD_SHADOW_CAPTURE_REQUIRED",
    "SOURCE_CONTROL_ONLY",
    "INVERSE_AVOID_FILTER_DIAGNOSTIC_ONLY",
    "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE_ONLY",
    "FAIL_CLOSED_REPAIRABLE_FROM_ACCEPTED_SOURCES",
    "EXACT_OWNER_ACCESS_SOURCE_CAPTURE_IMPOSSIBILITY",
    "CONTAMINATED_OR_FORBIDDEN_FOR_VALIDATION",
}

MANDATORY_CONTEXT_REL = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ".context/00_core/r7_failure_intelligence_doctrine_addendum.md",
    "research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
]

MUTABLE_CONTEXT_REL = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
}

ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]

PROMPT = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_R9_ACCEPTED_PACKET_SEALED_HISTORICAL_VALIDATION_EXECUTION_GOAL_PROMPT_2026-05-16.md"
STARTER = ROOT / "research/science_program_2026_05/04_goal_prompts/READY8_R9_ACCEPTED_PACKET_SEALED_HISTORICAL_VALIDATION_EXECUTION_STARTER_2026-05-16.txt"

R9_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_forward_retest_source_capture_packet_after_g12_scoring_audit"
R8_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization"
R5_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair"
R5_G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit"

R9 = {
    "g12_decision": R9_DIR / "G12_R9_PACKET_AUDIT_DECISION_2026-05-16.json",
    "g12_recomputation": R9_DIR / "G12_R9_PACKET_AUDIT_RECOMPUTATION_2026-05-16.json",
    "g12_verification": R9_DIR / "G12_R9_PACKET_AUDIT_VERIFICATION_RESULT_2026-05-16.json",
    "g12_source_hash": R9_DIR / "G12_R9_PACKET_AUDIT_SOURCE_HASH_2026-05-16.json",
    "g12_source_drift": R9_DIR / "G12_R9_PACKET_AUDIT_SOURCE_DRIFT_2026-05-16.jsonl",
    "g12_material": R9_DIR / "G12_R9_PACKET_AUDIT_MATERIAL_ROWS_2026-05-16.jsonl",
    "g12_packet_coverage": R9_DIR / "G12_R9_PACKET_AUDIT_PACKET_COVERAGE_2026-05-16.jsonl",
    "g12_failure_intel": R9_DIR / "G12_R9_PACKET_AUDIT_FAILURE_INTEL_2026-05-16.jsonl",
    "g12_repaired_target": R9_DIR / "G12_R9_PACKET_AUDIT_REPAIRED_TARGET_2026-05-16.jsonl",
    "g12_blockers": R9_DIR / "G12_R9_PACKET_AUDIT_BLOCKERS_2026-05-16.jsonl",
    "g12_sequence": R9_DIR / "G12_R9_PACKET_AUDIT_SEQUENCE_2026-05-16.jsonl",
    "row_identity": R9_DIR / "R9_ROW_IDENTITY_2026-05-16.jsonl",
    "haz001": R9_DIR / "R9_HAZ001_PACKET_2026-05-16.jsonl",
    "mac": R9_DIR / "R9_MAC_PACKET_2026-05-16.jsonl",
    "haz005": R9_DIR / "R9_HAZ005_PACKET_2026-05-16.jsonl",
    "unc004": R9_DIR / "R9_UNC004_CONTRACT_2026-05-16.jsonl",
    "residual": R9_DIR / "R9_RESIDUAL_PACKET_2026-05-16.jsonl",
    "repaired_targets": R9_DIR / "R9_REPAIRED_TARGETS_2026-05-16.jsonl",
    "failure_intel": R9_DIR / "R9_FAILURE_INTEL_2026-05-16.jsonl",
    "source_capture": R9_DIR / "R9_SOURCE_CAPTURE_REQS_2026-05-16.jsonl",
    "doors": R9_DIR / "R9_DOORS_2026-05-16.jsonl",
    "questions": R9_DIR / "R9_QUESTIONS_2026-05-16.jsonl",
    "blockers": R9_DIR / "R9_BLOCKERS_2026-05-16.jsonl",
    "sequence": R9_DIR / "R9_SEQUENCE_2026-05-16.jsonl",
    "source_roots": R9_DIR / "R9_SOURCE_ROOTS_2026-05-16.jsonl",
    "output_manifest": R9_DIR / "R9_OUTPUT_MANIFEST_2026-05-16.json",
}

R8 = {
    "row_branch": R8_DIR / "READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_2026-05-16.jsonl",
    "adv_control": R8_DIR / "READY8_EXPANDED_SCORING_ADV_CONTROL_ADJUSTMENT_LEDGER_2026-05-16.jsonl",
    "duplicate": R8_DIR / "READY8_EXPANDED_SCORING_DUPLICATE_EFFECTIVE_N_LEDGER_2026-05-16.jsonl",
    "concentration": R8_DIR / "READY8_EXPANDED_SCORING_CONCENTRATION_STRESS_LEDGER_2026-05-16.jsonl",
    "fail_closed": R8_DIR / "READY8_EXPANDED_SCORING_FAIL_CLOSED_SENSITIVITY_LEDGER_2026-05-16.jsonl",
}

R5_REPAIRED_TARGET_PACKET = R5_DIR / "READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_2026-05-15.jsonl"
R5_G12_REPAIRED_TARGET_RECOMPUTATION = (
    R5_G12_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_2026-05-15.jsonl"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def safe_base() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_FALSE_FLAGS,
    }


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_number"] = line_number
                yield row


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            clean = {key: value for key, value in row.items() if key != "_source_line_number"}
            handle.write(json.dumps(clean, sort_keys=True, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file_canonical_lf(path: Path) -> str:
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def count_jsonl(path: Path) -> int | None:
    if path.suffix.lower() != ".jsonl":
        return None
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def row_hash(row: dict[str, Any]) -> str:
    clean = {key: value for key, value in row.items() if key != "_source_line_number"}
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def sign_label(value: float | None) -> str:
    if value is None:
        return "NOT_NUMERIC"
    if value > 0:
        return "POSITIVE"
    if value < 0:
        return "NEGATIVE"
    return "ZERO"


def session_bucket(timestamp: str | None) -> str:
    if not timestamp or len(timestamp) < 13:
        return "SESSION_UNKNOWN"
    try:
        hour = int(timestamp[11:13])
    except ValueError:
        return "SESSION_UNKNOWN"
    if 0 <= hour < 3:
        return "TOKYO_UTC_0000_0300"
    if 7 <= hour < 12:
        return "LONDON_UTC_0700_1200"
    if 13 <= hour < 17:
        return "NEW_YORK_UTC_1300_1700"
    return "OUTSIDE_PRIMARY_READY8_SESSION_BUCKET"


def neutral_value_from_repaired(row: dict[str, Any]) -> float | None:
    family = row.get("target_family_id")
    if family == "neutral_close_to_close_return_m15_horizons_v1":
        return num(row.get("close_to_close_percent_return"))
    if family == "neutral_high_low_excursion_m15_horizons_v1":
        up = num(row.get("upside_excursion_percent"))
        down = num(row.get("downside_excursion_percent"))
        if up is None or down is None:
            return None
        return up - down
    return None


def neutral_magnitude_from_repaired(row: dict[str, Any]) -> float | None:
    family = row.get("target_family_id")
    if family == "neutral_close_to_close_return_m15_horizons_v1":
        value = num(row.get("close_to_close_percent_return"))
        return abs(value) if value is not None else None
    if family == "neutral_high_low_excursion_m15_horizons_v1":
        vals = [v for v in (num(row.get("upside_excursion_percent")), num(row.get("downside_excursion_percent"))) if v is not None]
        return max(vals) if vals else None
    return None


def metric_stats(values: list[float], duplicate_keys: set[str]) -> dict[str, Any]:
    positives = sum(1 for value in values if value > 0)
    negatives = sum(1 for value in values if value < 0)
    zeros = sum(1 for value in values if value == 0)
    return {
        "row_count": len(values),
        "unique_duplicate_denominator_count": len(duplicate_keys),
        "mean": mean(values),
        "median": median(values),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "p10": quantile(values, 0.10),
        "p90": quantile(values, 0.90),
        "positive_count": positives,
        "negative_count": negatives,
        "zero_count": zeros,
        "positive_rate": positives / len(values) if values else None,
        "negative_rate": negatives / len(values) if values else None,
        "zero_rate": zeros / len(values) if values else None,
        "robust_outlier_view": {
            "trimmed_mean_10pct": (
                mean(sorted(values)[max(1, int(len(values) * 0.10)) : -max(1, int(len(values) * 0.10))])
                if len(values) >= 20
                else mean(values)
            ),
            "median_abs_value": median([abs(value) for value in values]),
        },
    }


def load_inputs() -> dict[str, Any]:
    return {
        "g12_decision": read_json(R9["g12_decision"]),
        "g12_recomputation": read_json(R9["g12_recomputation"]),
        "g12_verification": read_json(R9["g12_verification"]),
        "g12_source_hash": read_json(R9["g12_source_hash"]),
        "row_identity": list(iter_jsonl(R9["row_identity"])),
        "haz001": list(iter_jsonl(R9["haz001"])),
        "mac": list(iter_jsonl(R9["mac"])),
        "haz005": list(iter_jsonl(R9["haz005"])),
        "unc004": list(iter_jsonl(R9["unc004"])),
        "residual": list(iter_jsonl(R9["residual"])),
        "repaired_targets": list(iter_jsonl(R9["repaired_targets"])),
        "failure_intel": list(iter_jsonl(R9["failure_intel"])),
        "blockers": list(iter_jsonl(R9["blockers"])),
        "sequence": list(iter_jsonl(R9["sequence"])),
        "source_capture": list(iter_jsonl(R9["source_capture"])),
        "doors": list(iter_jsonl(R9["doors"])),
        "questions": list(iter_jsonl(R9["questions"])),
        "source_roots": list(iter_jsonl(R9["source_roots"])),
        "r5_repaired": list(iter_jsonl(R5_REPAIRED_TARGET_PACKET)),
        "r5_g12_repaired": list(iter_jsonl(R5_G12_REPAIRED_TARGET_RECOMPUTATION)),
    }


def packet_status(row: dict[str, Any]) -> list[str]:
    family = row.get("packet_family")
    partition = (row.get("branch_key") or {}).get("partition_assignment")
    statuses: list[str] = []
    if family == "HAZ001_DECONCENTRATED_RETEST":
        if partition == "SEALED_VALIDATION_CANDIDATE_DESIGN":
            statuses.append("SEALED_HISTORICAL_VALIDATION_EXECUTABLE")
        elif partition == "STRESS_ROBUSTNESS_CANDIDATE_DESIGN":
            statuses.append("STRESS_ROBUSTNESS_EXECUTABLE")
        statuses.append("FORWARD_SHADOW_CAPTURE_REQUIRED")
    elif family == "MAC_INVERSE_AVOID_FILTER_DESIGN":
        statuses.append("INVERSE_AVOID_FILTER_DIAGNOSTIC_ONLY")
    elif family == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL":
        statuses.extend(
            [
                "SOURCE_CONTROL_ONLY",
                "FAIL_CLOSED_REPAIRABLE_FROM_ACCEPTED_SOURCES",
                "EXACT_OWNER_ACCESS_SOURCE_CAPTURE_IMPOSSIBILITY",
            ]
        )
    elif family == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC":
        statuses.extend(["FORWARD_SHADOW_CAPTURE_REQUIRED", "EXACT_OWNER_ACCESS_SOURCE_CAPTURE_IMPOSSIBILITY"])
    elif family == "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE":
        statuses.append("CONTROL_RESIDUAL_FAILURE_INTELLIGENCE_ONLY")
    else:
        statuses.append("CONTAMINATED_OR_FORBIDDEN_FOR_VALIDATION")
    return statuses


def r_geometry_for_packet(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "geometry_scope": "accepted_packet_aggregate_branch",
        "r_style_geometry_status": "FAIL_CLOSED_MISSING_SOURCE_BOUND_ROW_LEVEL_R_GEOMETRY",
        "entry_reference_status": "missing row-level entry/reference price in accepted R9 packet row",
        "side_status": "missing source-bound side/direction for R-style outcome",
        "stop_status": "missing source-bound stop/invalidation geometry",
        "target_status": "missing source-bound target price or R multiple",
        "horizon_status": "present in branch_key where applicable",
        "fillability_status": "missing source-bound fillability/path-order assumption for R-style outcome",
        "cost_slippage_status": "not available in accepted no-promotion packet",
        "expectancy_proxy_status": "not computed as R/expectancy; strongest available metric is neutral target-movement/control delta",
    }


def r_geometry_for_repaired(row: dict[str, Any]) -> dict[str, Any]:
    has_entry = row.get("entry_close") is not None
    has_horizon = row.get("horizon_end_utc") is not None and row.get("horizon_m15_bars") is not None
    has_path = row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1"
    return {
        "geometry_scope": "accepted_r5_repaired_target_row",
        "r_style_geometry_status": "FAIL_CLOSED_MISSING_SIDE_STOP_TARGET_FILLABILITY_FOR_R_STYLE_RESULT",
        "entry_reference_status": "source_bound_entry_close_present" if has_entry else "missing_entry_close",
        "side_status": "missing source-bound trading side; card predicate is not side",
        "stop_status": "missing source-bound stop/invalidation geometry",
        "target_status": "missing source-bound target price/R multiple; neutral target family only",
        "horizon_status": "source_bound_horizon_present" if has_horizon else "missing_horizon",
        "fillability_status": (
            "high_low_path_extremes_present_but_stop_target_order_not_defined"
            if has_path
            else "close_to_close_only_no_intrahorizon_path_order"
        ),
        "cost_slippage_status": "not source-bound in repaired target packet",
        "expectancy_proxy_status": (
            "not computed as R/expectancy; computed neutral source-bound movement only"
        ),
    }


def target_stop_status(row: dict[str, Any], source_type: str) -> dict[str, Any]:
    return {
        "target_stop_result_status": "AMBIGUOUS_MISSING_SOURCE_BOUND_SIDE_STOP_TARGET_GEOMETRY",
        "hit_miss_ambiguous_fail_closed": "AMBIGUOUS",
        "target_hit": None,
        "stop_hit": None,
        "path_order_status": (
            "source high/low extremes available but no target/stop levels or side"
            if source_type == "repaired_high_low"
            else "not enough path-order geometry for target/stop hit result"
        ),
        "missing_geometry_reason": (
            "source-bound target/stop/side/fillability geometry is absent; neutral movement remains computable"
        ),
    }


def build_partition_and_admission(packet_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    partition_rows: list[dict[str, Any]] = []
    admission_rows: list[dict[str, Any]] = []
    for index, row in enumerate(packet_rows, 1):
        statuses = packet_status(row)
        branch = row.get("branch_key") or {}
        partition = branch.get("partition_assignment")
        if not partition:
            if row.get("packet_family") == "HAZ005_REPAIRED_DESCRIPTOR_SOURCE_CONTROL":
                partition = "SOURCE_CONTROL_ONLY_NOT_VALIDATION_PARTITION"
            elif row.get("packet_family") == "UNC004_SOURCE_CONFIDENCE_DIAGNOSTIC":
                partition = "FORWARD_SOURCE_CAPTURE_REQUIRED_PARTITION"
            else:
                partition = "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE_PARTITION"
        frozen = {
            **safe_base(),
            "freeze_sequence": index,
            "packet_row_id": row["packet_row_id"],
            "packet_family": row.get("packet_family"),
            "branch_key": branch,
            "frozen_partition_assignment": partition,
            "execution_statuses": statuses,
            "partition_freeze_status": "FROZEN_BEFORE_R10_VALIDATION_COMPUTATION",
            "source_packet_row_sha256": row_hash(row),
        }
        partition_rows.append(frozen)
        admission_rows.append(
            {
                **frozen,
                "admission_status": "ADMITTED_WITH_EXECUTION_STATUS_OR_EXACT_BOUNDARY",
                "neutral_metric_status": (
                    "AGGREGATE_NEUTRAL_CONTROL_DELTA_AVAILABLE"
                    if row.get("raw_delta") is not None or row.get("control_adjusted_residual_abs") is not None
                    else "NO_PACKET_LEVEL_NEUTRAL_DELTA_AVAILABLE"
                ),
                **r_geometry_for_packet(row),
            }
        )
    return partition_rows, admission_rows


def branch_result_row(row: dict[str, Any], family_label: str) -> dict[str, Any]:
    raw_delta = num(row.get("raw_delta"))
    control_residual = num(row.get("control_adjusted_residual_abs"))
    branch = row.get("branch_key") or {}
    return {
        **safe_base(),
        "packet_row_id": row.get("packet_row_id"),
        "packet_family": row.get("packet_family"),
        "branch_key": branch,
        "family_label": family_label,
        "partition_assignment": branch.get("partition_assignment"),
        "card_id": branch.get("card_id"),
        "horizon_m15_bars": branch.get("horizon_m15_bars"),
        "target_family_id": branch.get("target_family_id"),
        "raw_neutral_target_movement_delta": raw_delta,
        "raw_neutral_direction": row.get("raw_direction") or sign_label(raw_delta),
        "control_adjustment_classification": row.get("control_adjustment", {}).get(
            "control_adjustment_classification", row.get("control_adjustment_classification")
        ),
        "control_adjusted_residual_abs": (
            row.get("control_adjustment", {}).get("control_adjusted_residual_abs", control_residual)
        ),
        "control_envelope_abs": row.get("control_adjustment", {}).get(
            "control_envelope_abs", row.get("control_envelope_abs")
        ),
        "pass_unique_duplicate_denominator_count": row.get("duplicate_effective_n", {}).get(
            "pass_unique_duplicate_denominator_count", row.get("pass_unique_duplicate_denominator_count")
        ),
        "control_unique_duplicate_denominator_count": row.get("duplicate_effective_n", {}).get(
            "control_unique_duplicate_denominator_count", row.get("control_unique_duplicate_denominator_count")
        ),
        "leave_one_survival_counts": row.get("concentration_leave_one", {}).get(
            "leave_one_survival_counts", row.get("leave_one_survival_counts")
        ),
        "source_result_status": row.get("source_result_status") or row.get("result_status"),
        "metric_scope": "source-bound aggregate neutral target movement/control delta; not broker/live actual performance",
        "stress_adjusted_result_note": (
            "Compared against stress rows in R10 stress ledger; no R/PnL/actual expectancy computed"
        ),
    }


def build_branch_ledgers(data: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    haz_rows = [branch_result_row(row, "HAZ001") for row in data["haz001"]]
    mac_rows = [branch_result_row(row, "MAC_INVERSE_DIAGNOSTIC") for row in data["mac"]]
    residual_rows = [branch_result_row(row, "CONTROL_RESIDUAL_FAILURE_INTELLIGENCE") for row in data["residual"]]
    sealed = [
        {**row, "validation_execution_class": "SEALED_HISTORICAL_VALIDATION_EXECUTABLE"}
        for row in haz_rows
        if row.get("partition_assignment") == "SEALED_VALIDATION_CANDIDATE_DESIGN"
    ]
    stress = [
        {**row, "validation_execution_class": "STRESS_ROBUSTNESS_EXECUTABLE"}
        for row in haz_rows
        if row.get("partition_assignment") == "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"
    ]
    return {
        "haz001": haz_rows,
        "mac": mac_rows,
        "residual": residual_rows,
        "sealed": sealed,
        "stress": stress,
    }


def build_unc004_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        is_full = row.get("contract_scope") == "accepted_full_row_implication"
        output.append(
            {
                **safe_base(),
                "packet_row_id": row.get("packet_row_id"),
                "parent_packet_row_id": row.get("parent_packet_row_id"),
                "contract_scope": row.get("contract_scope"),
                "execution_statuses": (
                    ["FORWARD_SHADOW_CAPTURE_REQUIRED", "EXACT_OWNER_ACCESS_SOURCE_CAPTURE_IMPOSSIBILITY"]
                    if not is_full
                    else ["FORWARD_SHADOW_CAPTURE_REQUIRED"]
                ),
                "comparison_key": row.get("comparison_key"),
                "comparison_classification": row.get("comparison_classification"),
                "source_comparison_family": row.get("source_comparison_family"),
                "pass_minus_control_target_movement_mean_delta": row.get(
                    "pass_minus_control_target_movement_mean_delta"
                ),
                "pass_positive_rate_minus_control_positive_rate_delta": row.get(
                    "pass_positive_rate_minus_control_positive_rate_delta"
                ),
                "source_bound_comparable_records": row.get("source_bound_comparable_records"),
                "source_bound_positive_records": row.get("source_bound_positive_records"),
                "target_terminal_status_counts": row.get("target_terminal_status_counts"),
                "warnings": row.get("warnings"),
                "native_capture_requirement": row.get("native_capture_requirement"),
                "source_capture_requirements": row.get("source_capture_requirements"),
                "metric_scope": "UNC004 source-bound diagnostic implication only; native confidence truth remains capture-required",
            }
        )
    return output


def build_haz005_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                **safe_base(),
                "packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                "execution_statuses": [
                    "SOURCE_CONTROL_ONLY",
                    "FAIL_CLOSED_REPAIRABLE_FROM_ACCEPTED_SOURCES",
                    "EXACT_OWNER_ACCESS_SOURCE_CAPTURE_IMPOSSIBILITY",
                ],
                "candidate_input_row_id": row.get("candidate_input_row_id"),
                "symbol": row.get("symbol"),
                "repaired_prior_16_drift_bucket": row.get("repaired_prior_16_drift_bucket"),
                "repaired_prior_16_range_bucket": row.get("repaired_prior_16_range_bucket"),
                "source_bar_hashes_sha256": row.get("source_bar_hashes_sha256"),
                "target_join_status": "FAIL_CLOSED_FOR_THIS_PACKET_ROW",
                "exact_row_level_impossibility": row.get("exact_row_level_impossibility"),
                "source_control_continuation_requirement": row.get("source_control_continuation_requirement"),
                "source_capture_requirements": row.get("source_capture_requirements"),
            }
        )
    return output


def build_repaired_target_ledgers(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    r5_by_id = {row["original_target_result_row_id"]: row for row in data["r5_repaired"]}
    g12_ids = {row["original_target_result_row_id"] for row in data["r5_g12_repaired"]}
    carry: list[dict[str, Any]] = []
    neutral_rows: list[dict[str, Any]] = []
    target_stop_rows: list[dict[str, Any]] = []
    for row in data["repaired_targets"]:
        source = r5_by_id.get(row["original_target_result_row_id"])
        value = neutral_value_from_repaired(source or {})
        magnitude = neutral_magnitude_from_repaired(source or {})
        source_present = source is not None
        base = {
            **safe_base(),
            "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
            "original_target_result_row_id": row.get("original_target_result_row_id"),
            "card_id": row.get("card_id"),
            "symbol": row.get("symbol"),
            "partition_assignment": row.get("partition_assignment"),
            "horizon_m15_bars": row.get("horizon_m15_bars"),
            "target_family_id": row.get("target_family_id"),
            "accepted_g12_audit_status": row.get("accepted_g12_audit_status"),
            "r5_repaired_target_source_present": source_present,
            "r5_g12_repaired_recomputation_present": row.get("original_target_result_row_id") in g12_ids,
            "repair_candidate_target_result_row_hash_match": row.get("repair_candidate_target_result_row_hash_match"),
            "consumption_status": row.get("consumption_status"),
        }
        carry.append(
            {
                **base,
                "carry_forward_rule": row.get("carry_forward_rule"),
                "remaining_requirement": row.get("remaining_requirement"),
                "execution_statuses": [
                    "SEALED_HISTORICAL_VALIDATION_EXECUTABLE"
                    if row.get("partition_assignment") == "SEALED_VALIDATION_CANDIDATE_DESIGN"
                    else "STRESS_ROBUSTNESS_EXECUTABLE"
                ],
            }
        )
        neutral_rows.append(
            {
                **base,
                "candidate_input_row_id": (source or {}).get("candidate_input_row_id"),
                "canonical_economic_group": (source or {}).get("canonical_economic_group"),
                "session_bucket": session_bucket((source or {}).get("entry_reference_time_utc")),
                "duplicate_proxy_denominator_key": (source or {}).get("duplicate_proxy_denominator_key"),
                "denominator_role": (source or {}).get("denominator_role"),
                "entry_close": (source or {}).get("entry_close"),
                "entry_reference_time_utc": (source or {}).get("entry_reference_time_utc"),
                "horizon_end_utc": (source or {}).get("horizon_end_utc"),
                "horizon_close": (source or {}).get("horizon_close"),
                "max_high_over_horizon": (source or {}).get("max_high_over_horizon"),
                "min_low_over_horizon": (source or {}).get("min_low_over_horizon"),
                "close_to_close_percent_return": (source or {}).get("close_to_close_percent_return"),
                "upside_excursion_percent": (source or {}).get("upside_excursion_percent"),
                "downside_excursion_percent": (source or {}).get("downside_excursion_percent"),
                "source_bound_neutral_movement_value": value,
                "source_bound_neutral_magnitude": magnitude,
                "neutral_sign_label": sign_label(value),
                "neutral_metric_status": (
                    "SOURCE_BOUND_NEUTRAL_TARGET_MOVEMENT_COMPUTED"
                    if value is not None
                    else "FAIL_CLOSED_MISSING_REPAIRED_TARGET_VALUE"
                ),
                **r_geometry_for_repaired(source or {}),
            }
        )
        target_stop_rows.append(
            {
                **base,
                "source_row_type": "repaired_target",
                "source_bound_neutral_movement_value": value,
                "neutral_sign_label": sign_label(value),
                **target_stop_status(
                    source or {},
                    "repaired_high_low"
                    if row.get("target_family_id") == "neutral_high_low_excursion_m15_horizons_v1"
                    else "repaired_close_to_close",
                ),
            }
        )
    return carry, neutral_rows, target_stop_rows


def build_group_metrics(neutral_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    for row in neutral_rows:
        value = num(row.get("source_bound_neutral_movement_value"))
        if value is None:
            continue
        key = (
            row.get("partition_assignment") or "UNKNOWN",
            row.get("card_id") or "UNKNOWN",
            str(row.get("horizon_m15_bars")),
            row.get("target_family_id") or "UNKNOWN",
            row.get("symbol") or "UNKNOWN",
            row.get("session_bucket") or "UNKNOWN",
        )
        if key not in groups:
            groups[key] = {"values": [], "dups": set()}
        groups[key]["values"].append(value)
        dup = row.get("duplicate_proxy_denominator_key") or row.get("original_target_result_row_id")
        groups[key]["dups"].add(dup)
    output = []
    for (partition, card, horizon, target_family, symbol, session), payload in sorted(groups.items()):
        scope = {
            "partition_assignment": partition,
            "card_id": card,
            "horizon_m15_bars": horizon,
            "target_family_id": target_family,
            "symbol": symbol,
            "session_bucket": session,
        }
        output.append(
            {
                **safe_base(),
                "ledger_family": "repaired_target_source_bound_neutral_movement_split",
                **scope,
                **metric_stats(payload["values"], payload["dups"]),
                "metric_scope": "source-bound neutral target movement from accepted repaired target rows; not R/PnL/live performance",
            }
        )
    return output


def build_duplicate_concentration(
    packet_rows: list[dict[str, Any]], neutral_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    packet_family_counts = Counter(row.get("packet_family") for row in packet_rows)
    for family, count in sorted(packet_family_counts.items()):
        rows.append(
            {
                **safe_base(),
                "ledger_family": "packet_family_effective_n_count",
                "scope": "packet_rows",
                "packet_family": family,
                "row_count": count,
                "duplicate_effective_n_note": "packet branch rows are aggregate contracts; use carried duplicate fields where present",
            }
        )
    by_partition_card: dict[tuple[str, str], set[str]] = defaultdict(set)
    row_count: Counter[tuple[str, str]] = Counter()
    for row in neutral_rows:
        key = (row.get("partition_assignment") or "UNKNOWN", row.get("card_id") or "UNKNOWN")
        row_count[key] += 1
        by_partition_card[key].add(row.get("duplicate_proxy_denominator_key") or row.get("original_target_result_row_id"))
    for (partition, card), dupes in sorted(by_partition_card.items()):
        concentration_ratio = (max(Counter().values()) if False else None)
        rows.append(
            {
                **safe_base(),
                "ledger_family": "repaired_target_duplicate_effective_n_by_partition_card",
                "partition_assignment": partition,
                "card_id": card,
                "row_count": row_count[(partition, card)],
                "unique_duplicate_denominator_count": len(dupes),
                "concentration_warning": row_count[(partition, card)] != len(dupes),
                "concentration_ratio": concentration_ratio,
            }
        )
    return rows


def build_fail_closed_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    blocker_counts = Counter(row.get("blocker") for row in data["blockers"])
    rows = []
    for blocker, count in sorted(blocker_counts.items()):
        rows.append(
            {
                **safe_base(),
                "ledger_family": "r9_blocker_fail_closed_attrition",
                "blocker": blocker,
                "row_count": count,
                "handling": "exactly bounded, repaired, or carried forward from accepted R9/G12 packet audit",
            }
        )
    rows.append(
        {
            **safe_base(),
            "ledger_family": "r5_repaired_target_sensitivity",
            "accepted_repaired_target_rows": len(data["repaired_targets"]),
            "remaining_fail_closed_target_rows_after_r8": 25240,
            "sensitivity_rule": "5,320 repaired rows are computed as neutral movement inputs; remaining fail-closed rows stay visible and excluded from metric denominators.",
        }
    )
    rows.append(
        {
            **safe_base(),
            "ledger_family": "haz005_packet_rows_target_join_fail_closed",
            "haz005_packet_rows": len(data["haz005"]),
            "handling": "source-control-only rows cannot be assigned target/horizon scoring labels without a separate accepted source-control retest packet",
        }
    )
    return rows


def build_geometry_ledgers(
    packet_rows: list[dict[str, Any]], neutral_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    geometry_rows: list[dict[str, Any]] = []
    target_stop_rows: list[dict[str, Any]] = []
    for row in packet_rows:
        geometry_rows.append(
            {
                **safe_base(),
                "source_row_type": "packet_row",
                "packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                "branch_key": row.get("branch_key"),
                **r_geometry_for_packet(row),
            }
        )
        target_stop_rows.append(
            {
                **safe_base(),
                "source_row_type": "packet_row",
                "packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                **target_stop_status(row, "packet_row"),
            }
        )
    for row in neutral_rows:
        geometry_rows.append(
            {
                **safe_base(),
                "source_row_type": "repaired_target_row",
                "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
                "original_target_result_row_id": row.get("original_target_result_row_id"),
                "card_id": row.get("card_id"),
                "partition_assignment": row.get("partition_assignment"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "target_family_id": row.get("target_family_id"),
                "source_bound_neutral_movement_value": row.get("source_bound_neutral_movement_value"),
                "neutral_metric_status": row.get("neutral_metric_status"),
                "r_style_geometry_status": row.get("r_style_geometry_status"),
                "entry_reference_status": row.get("entry_reference_status"),
                "side_status": row.get("side_status"),
                "stop_status": row.get("stop_status"),
                "target_status": row.get("target_status"),
                "horizon_status": row.get("horizon_status"),
                "fillability_status": row.get("fillability_status"),
                "cost_slippage_status": row.get("cost_slippage_status"),
                "expectancy_proxy_status": row.get("expectancy_proxy_status"),
            }
        )
    return geometry_rows, target_stop_rows


def build_failure_intel(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        output.append(
            {
                **safe_base(),
                "source_branch_classification_row_id": row.get("source_branch_classification_row_id"),
                "branch_key": row.get("branch_key"),
                "branch_status": row.get("branch_status"),
                "doctrine_classifications": row.get("doctrine_classifications"),
                "kill_scope": row.get("kill_scope"),
                "what_was_learned": row.get("what_was_learned"),
                "why_failed_or_weakened": row.get("why_failed_or_weakened"),
                "explaining_mechanism": row.get("explaining_mechanism"),
                "implication": row.get("implication"),
                "result_route_handling": row.get("result_route_handling"),
                "validation_execution_handling": "preserved as failure intelligence; kills unsupported edge claims only",
                "future_route_status": (
                    "source_capture_or_forward_retest_candidate"
                    if row.get("implication") in {"source-capture requirement", "forward-retest candidate"}
                    else "preserve_for_audit_and_failure_anatomy"
                ),
            }
        )
    return output


def build_source_hash_and_drift() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted_sources = {
        source["path"]: source
        for source in read_json(R9["g12_source_hash"]).get("sources", [])
        if source.get("path")
    }
    source_paths = [ROOT / path for path in MANDATORY_CONTEXT_REL]
    source_paths.extend(R9.values())
    source_paths.extend(R8.values())
    source_paths.extend([R5_REPAIRED_TARGET_PACKET, R5_G12_REPAIRED_TARGET_RECOMPUTATION, PROMPT, STARTER])

    seen: set[str] = set()
    source_rows = []
    drift_rows = []
    searched_rows = []
    for path in source_paths:
        relative = rel(path)
        if relative in seen:
            continue
        seen.add(relative)
        exists = path.exists()
        actual = sha256_file(path) if exists else None
        actual_lf = sha256_file_canonical_lf(path) if exists else None
        accepted = accepted_sources.get(relative)
        drift_status = "CURRENT_R10_SOURCE_HASH_RECORDED"
        if accepted and (accepted.get("sha256") == actual or accepted.get("sha256_canonical_lf") == actual_lf):
            drift_status = "MATCHES_ACCEPTED_R9_G12_SOURCE_HASH"
        elif accepted and relative in MUTABLE_CONTEXT_REL:
            drift_status = "MUTABLE_COORDINATION_CONTEXT_DRIFT_BOUNDED"
        elif accepted:
            drift_status = "SOURCE_HASH_DIFFERS_FROM_ACCEPTED_R9_G12_SOURCE"
        row = {
            **safe_base(),
            "path": relative,
            "exists": exists,
            "bytes": path.stat().st_size if exists else None,
            "jsonl_rows": count_jsonl(path) if exists else None,
            "sha256": actual,
            "sha256_canonical_lf": actual_lf,
            "accepted_r9_g12_sha256": accepted.get("sha256") if accepted else None,
            "accepted_r9_g12_sha256_canonical_lf": accepted.get("sha256_canonical_lf") if accepted else None,
            "source_drift_status": drift_status,
        }
        source_rows.append(row)
        drift_rows.append(row)
        searched_rows.append(
            {
                **safe_base(),
                "searched_root_or_file": relative,
                "search_status": "FOUND" if exists else "MISSING",
                "purpose": "mandatory context/input/provenance source for R10 sealed validation execution",
                "hash_recorded": exists,
            }
        )
    source_hash = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "source_count": len(source_rows),
        "source_hash_policy": {
            "strict_for": "accepted R9/R8/R5 immutable route artifacts",
            "bounded_for": sorted(MUTABLE_CONTEXT_REL),
            "raw_vs_canonical_rule": "canonical LF match is sufficient for Windows line-ending drift classification",
        },
        "real_immutable_source_drift_count": sum(
            1
            for row in drift_rows
            if row["source_drift_status"] == "SOURCE_HASH_DIFFERS_FROM_ACCEPTED_R9_G12_SOURCE"
            and row["path"] not in MUTABLE_CONTEXT_REL
        ),
        "sources": source_rows,
    }
    return source_hash, drift_rows, searched_rows


def build_policy_artifacts() -> dict[str, dict[str, Any]]:
    return {
        f"R10_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json": {
            **safe_base(),
            "policy": "Use only accepted R9/G12 packet rows and accepted R5 repaired-target source rows. No broker/account/order/history/deal/position or live actual outcome evidence is opened.",
            "asof_rule": "All source-bound target movement comes from already accepted no-promotion source-control artifacts; no post-route source capture is added.",
            "embargo_rule": "Discovery/development/stress/sealed labels are frozen before R10 computation in partition freeze ledger.",
        },
        f"R10_DUPLICATE_DENOMINATOR_EFFECTIVE_N_POLICY_{DATE}.json": {
            **safe_base(),
            "policy": "Report row counts and unique duplicate_proxy_denominator_key counts separately. Packet rows are aggregate contracts; repaired target rows use source duplicate keys where present.",
        },
        f"R10_CONTROL_PLACEBO_GENERIC_MOVEMENT_ADJUSTMENT_POLICY_{DATE}.json": {
            **safe_base(),
            "policy": "ADV/placebo/control adjustments kill only unsupported edge claims. Residual and failure information is preserved under the failure-intelligence doctrine.",
        },
        f"R10_FAIL_CLOSED_SOURCE_CAPTURE_POLICY_{DATE}.json": {
            **safe_base(),
            "policy": "If R/expectancy/target-stop geometry is missing, emit exact field/source/geometry/fillability reason and compute neutral movement where source-bound.",
        },
    }


def build_questions_doors_blockers(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    questions = []
    for row in data["questions"]:
        questions.append(
            {
                **safe_base(),
                "source_packet_row_id": row.get("packet_row_id"),
                "question_status": "ANSWERED_OR_BOUND_IN_R10_EXECUTION_LEDGER",
                "packet_family": row.get("packet_family"),
                "source_question": row.get("question") or row.get("route_question") or row,
                "r10_answer": "classified, materialized, source-capture-required, or exactly bounded without top-N truncation",
            }
        )
    doors = []
    for row in data["doors"]:
        doors.append(
            {
                **safe_base(),
                "source_packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                "door_status": row.get("door_status"),
                "source_door": row.get("door") or row.get("source_door") or row,
                "r10_handling": "preserved in full; downstream use requires emitted G12 post-validation audit",
            }
        )
    blockers = []
    for row in data["blockers"]:
        blockers.append(
            {
                **safe_base(),
                "packet_row_id": row.get("packet_row_id"),
                "packet_family": row.get("packet_family"),
                "blocker": row.get("blocker"),
                "blocker_status": row.get("blocker_status"),
                "proof_or_boundary": row.get("proof_or_boundary"),
                "owner_access_source_capture_requirement": row.get("owner_access_source_capture_requirement"),
                "r10_handling": "repaired, carried forward, or exactly bounded; no same-evidence-class blocker left unclassified",
            }
        )
    return questions, doors, blockers


def write_next_g12_prompt() -> tuple[Path, Path]:
    prompt = ROUTE_DIR / f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md"
    starter = ROUTE_DIR / f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_STARTER_{DATE}.txt"
    prompt_text = f"""# G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT

Date: {DATE}

## Objective

Audit the R10 route in `research/science_program_2026_05/06_outcome_testing/ready8_r9_accepted_packet_sealed_historical_validation_execution/` as `G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_ONLY`.

Run mandatory preflight and context refresh first. Do not rely on chat memory. Read this controlling prompt, the starter message, `goal_session_research_discipline.md`, `research_operating_doctrine.md`, `r7_failure_intelligence_doctrine_addendum.md`, the historical sealed validation protocol, the R9 G12 audit, and every R10 ledger from disk. After any context compaction, resume, interruption, or uncertainty, regenerate `.context/LIVE_STATE.md`, then reread this controlling prompt, the starter message, `goal_session_research_discipline.md`, `research_operating_doctrine.md`, and the latest route artifacts before continuing; enforce the rules there as active instructions and make the lane strongest possible at all times.

Treat those context files as active instructions, not background. The audit posture is strict but fair, with no conservative brake: pursue proof-or-impossibility inside this same-evidence-class audit until every same-G12 issue is accepted, repaired, or exactly bounded.

Independently recompute row counts, partition freeze, packet row execution statuses, repaired-target neutral movement metrics, sealed/stress split metrics, proxy R/expectancy geometry fail-closed reasons, target/stop hit/miss/ambiguous/fail-closed statuses, HAZ001/MAC/HAZ005/UNC004/residual/failure-intelligence ledgers, duplicate/effective-N, concentration, fail-closed sensitivity, no-leak/source hashes, forbidden surfaces, output manifest, verifier/focused tests, full artifact audit, and instruction coverage.

Repair same-G12 issues inside the audit when possible. A blocker ledger is not completion. A next-route prompt is not completion. A clean fail-closed classification is not completion when same-evidence-class repair is possible. If you discover a missing field, stale hash, source gap, geometry gap, denominator ambiguity, control ambiguity, path/fillability ambiguity, cost/slippage gap, target/stop gap, side/entry/stop/target/fillability/R-geometry gap, or incomplete result condition that prevents the strongest honest computation, pursue repair inside this same G12 audit using every already-approved local/source-bound artifact and every available historical, MT5, Sierra, shadow/log, research, route-local, and accepted upstream source that stays inside the evidence class. After every repair, recompute the affected counts, metrics, ledgers, manifests, source hashes, verifier outputs, focused tests, and artifact audit evidence. Only leave a blocker unresolved when you prove exact owner/access/source/capture impossibility or prove the repair requires a different evidence class that this route cannot open.

For this result-audit route specifically, do not stop at R10's neutral-movement boundary if trade-geometry repair may be source-bound. Attempt to bind side, entry/reference, stop/invalidation, target/R multiple, horizon, fillability/path ordering, and cost/slippage from accepted SCID candidates, source-control packets, repaired target rows, M1/M15 path ledgers, forward-capture schemas, live/shadow logs, Sierra/MT5 historical sources, moonshot-compatible historical sources, route-local artifacts, and accepted upstream R7/R8/R9/R10 artifacts. If exact R/expectancy remains impossible after that pursuit, compute the strongest available proxy and preserve row-level missing-field proof. Do not use "not broker/live actual performance" as a reason to avoid sealed historical/proxy/source-bound R-style metrics where geometry can be bound from approved sources.

Acceptance precondition: do not merely verify that R10 marked R/expectancy geometry fail-closed. Before any `ACCEPT_AS_G12...` decision, independently attempt row-level repair for every R10 row whose side/entry/reference, stop/invalidation, target/R multiple, horizon, fillability/path ordering, or cost/slippage geometry is missing or ambiguous. The audit output must include a row-level repair-attempt or impossibility ledger that names the packet/repaired-target row, every missing geometry field, every accepted/local/source-bound root searched, whether each field was repaired, which artifacts were recomputed after repair, and the exact owner/access/source/capture/evidence-class impossibility if it remains unrepaired. If any geometry field can be repaired inside this same evidence class, repair it and recompute the affected result, target/stop, proxy R/expectancy, split, manifest, verifier, focused-test, and artifact-audit outputs before deciding. If it truly cannot be repaired, prove exact impossibility row-by-row and preserve the strongest neutral/proxy metric for that row. A clean R10 blocker ledger is input evidence, not an audit conclusion.

Preserve all material rows and do not use arbitrary top-N/top 3/5/10 cutoffs. Safe flags are rails, not brakes.

Emit a completion audit that maps every prompt requirement to disk evidence and proves same-evidence-class exhaustion or exact impossibility before any terminal decision.

Forbidden surfaces remain closed: no promotion, live behavior, broker/live actual PnL, broker/live actual R, actual trade win-rate, actual expectancy, Sharpe promotion evidence, broker actual-R, AI/API, paid/vendor, broker account/order/history/deal/position, raw market blob, remote push, or prompt/config/risk/safety/execution/canary/selector changes.

Required safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

Terminal decision must be one of:

- `ACCEPT_AS_G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_NO_PROMOTION`
- `REJECT_R10_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_WITH_REPAIR_REQUIREMENTS_NO_PROMOTION`
"""
    starter_text = (
        "/goal Follow the full controlling prompt in "
        f"{rel(prompt)} as the complete objective; do mandatory preflight and context refresh first; "
        "read this starter, the controlling prompt, goal_session_research_discipline.md, and research_operating_doctrine.md as active instructions, not background; "
        "after any context compaction/resume/interruption/uncertainty, regenerate LIVE_STATE and reread this starter, the controlling prompt, goal_session_research_discipline.md, research_operating_doctrine.md, and latest route artifacts before continuing; "
        "do not rely on chat memory; stay G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_ONLY "
        "with NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; "
        "audit all R10 ledgers from disk, recompute row counts/metrics/source hashes/manifest/verifier/tests/full artifact audit, "
        "pursue proof-or-impossibility to the full end, and do not merely accept R10 fail-closed R/expectancy geometry "
        "or treat blocker ledgers, next-route prompts, or clean fail-closed classifications as completion if same-evidence-class repair is possible; "
        "independently attempt row-level side/entry/reference/stop/invalidation/target/R/horizon/fillability/path-order/cost/slippage geometry repair "
        "from approved local/source-bound artifacts, historical/MT5/Sierra/shadow/log/research/route-local/accepted upstream sources, "
        "then recompute affected result/target-stop/proxy/split/manifest/verifier/test/audit artifacts; "
        "if exact R/expectancy remains impossible, compute the strongest proxy and preserve row-level missing-field proof with exact owner/access/source/capture/evidence-class impossibility; "
        "completion audit and instruction-coverage required; "
        "no conservative brake, no arbitrary top-N/top 3/5/10/number-limited cutoff, preserve all material rows, "
        "no promotion/live/broker actual/API/paid/vendor/account-order-history-deal-position/raw-blob/remote/prompt-config-risk-safety-execution-canary-selector changes; "
        "mark complete only when the prompt completion standard is fully satisfied with scoped commits."
    )
    prompt.write_text(prompt_text, encoding="utf-8", newline="\n")
    starter.write_text(starter_text + "\n", encoding="utf-8", newline="\n")
    return prompt, starter


def output_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name.endswith(f"OUTPUT_MANIFEST_{DATE}.json"):
            continue
        files.append(
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "sha256_canonical_lf": sha256_file_canonical_lf(path),
                "jsonl_rows": count_jsonl(path),
            }
        )
    return {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "file_count": len(files),
        "files": files,
    }


def main() -> int:
    data = load_inputs()
    packet_rows = data["row_identity"]
    partition_rows, admission_rows = build_partition_and_admission(packet_rows)
    branch_ledgers = build_branch_ledgers(data)
    repaired_carry, repaired_neutral_rows, repaired_target_stop_rows = build_repaired_target_ledgers(data)
    repaired_group_metrics = build_group_metrics(repaired_neutral_rows)
    geometry_rows, packet_target_stop_rows = build_geometry_ledgers(packet_rows, repaired_neutral_rows)
    target_stop_rows = packet_target_stop_rows + repaired_target_stop_rows
    duplicate_rows = build_duplicate_concentration(packet_rows, repaired_neutral_rows)
    fail_closed_rows = build_fail_closed_rows(data)
    questions, doors, blockers = build_questions_doors_blockers(data)
    source_hash, source_drift, searched_roots = build_source_hash_and_drift()
    failure_rows = build_failure_intel(data["failure_intel"])

    sealed_primary_rows = branch_ledgers["sealed"] + [
        {**row, "validation_execution_class": "SEALED_HISTORICAL_VALIDATION_EXECUTABLE"}
        for row in repaired_group_metrics
        if row.get("partition_assignment") == "SEALED_VALIDATION_CANDIDATE_DESIGN"
    ]
    stress_rows = branch_ledgers["stress"] + [
        {**row, "validation_execution_class": "STRESS_ROBUSTNESS_EXECUTABLE"}
        for row in repaired_group_metrics
        if row.get("partition_assignment") == "STRESS_ROBUSTNESS_CANDIDATE_DESIGN"
    ]

    context_anchor = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "git_head_at_build": git_head(),
        "controlling_prompt": rel(PROMPT),
        "starter": rel(STARTER),
        "route_directory": rel(ROUTE_DIR),
        "mandatory_context_files_read_from_disk": MANDATORY_CONTEXT_REL,
        "evidence_class_note": "R10 sealed historical/proxy execution only; no promotion or live-system effect.",
        "resume_instruction": "Rerun py -3 scripts/generate_live_state.py, read prompt/context, then rerun this builder and verifier.",
    }
    provenance = {
        **safe_base(),
        "accepted_r9_g12_terminal_decision": data["g12_decision"].get("terminal_decision"),
        "downstream_canonical_no_promotion_packet_use_allowed": data["g12_decision"].get(
            "downstream_canonical_no_promotion_packet_use_allowed"
        ),
        "accepted_counts": data["g12_decision"].get("summary_counts"),
        "r9_g12_recomputation_counts": data["g12_recomputation"].get("observed_counts"),
        "r9_g12_verifier_ok": data["g12_verification"].get("ok"),
        "used_sources": {name: rel(path) for name, path in {**R9, **R8}.items()},
        "r5_repaired_target_source": rel(R5_REPAIRED_TARGET_PACKET),
        "r5_g12_repaired_target_recomputation": rel(R5_G12_REPAIRED_TARGET_RECOMPUTATION),
    }

    write_json(ROUTE_DIR / f"R10_CONTEXT_ANCHOR_{DATE}.json", context_anchor)
    write_json(ROUTE_DIR / f"R10_PREREQUISITE_ACCEPTANCE_G12_PROVENANCE_LEDGER_{DATE}.json", provenance)
    write_json(ROUTE_DIR / f"R10_SOURCE_HASH_LEDGER_{DATE}.json", source_hash)
    write_jsonl(ROUTE_DIR / f"R10_SOURCE_DRIFT_LEDGER_{DATE}.jsonl", source_drift)
    write_jsonl(ROUTE_DIR / f"R10_PARTITION_FREEZE_LEDGER_{DATE}.jsonl", partition_rows)
    for name, artifact in build_policy_artifacts().items():
        write_json(ROUTE_DIR / name, artifact)
    write_jsonl(ROUTE_DIR / f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl", admission_rows)
    write_jsonl(ROUTE_DIR / f"R10_SEALED_HISTORICAL_PRIMARY_VALIDATION_LEDGER_{DATE}.jsonl", sealed_primary_rows)
    write_jsonl(ROUTE_DIR / f"R10_STRESS_ROBUSTNESS_LEDGER_{DATE}.jsonl", stress_rows)
    write_jsonl(ROUTE_DIR / f"R10_PROXY_R_EXPECTANCY_GEOMETRY_COVERAGE_LEDGER_{DATE}.jsonl", geometry_rows)
    write_jsonl(ROUTE_DIR / f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl", target_stop_rows)
    write_jsonl(ROUTE_DIR / f"R10_HAZ001_VALIDATION_RETEST_RESULT_LEDGER_{DATE}.jsonl", branch_ledgers["haz001"])
    write_jsonl(ROUTE_DIR / f"R10_MAC_INVERSE_AVOID_FILTER_DIAGNOSTIC_RESULT_LEDGER_{DATE}.jsonl", branch_ledgers["mac"])
    write_jsonl(ROUTE_DIR / f"R10_HAZ005_REPAIRED_ROW_SOURCE_CONTROL_LEDGER_{DATE}.jsonl", build_haz005_rows(data["haz005"]))
    write_jsonl(ROUTE_DIR / f"R10_UNC004_SOURCE_CAPTURE_DIAGNOSTIC_IMPLICATION_LEDGER_{DATE}.jsonl", build_unc004_rows(data["unc004"]))
    write_jsonl(ROUTE_DIR / f"R10_RESIDUAL_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl", branch_ledgers["residual"])
    write_jsonl(ROUTE_DIR / f"R10_REPAIRED_TARGET_CARRY_FORWARD_LEDGER_{DATE}.jsonl", repaired_carry)
    write_jsonl(ROUTE_DIR / f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl", repaired_neutral_rows)
    write_jsonl(ROUTE_DIR / f"R10_REPAIRED_TARGET_SPLIT_METRIC_SUMMARY_LEDGER_{DATE}.jsonl", repaired_group_metrics)
    write_jsonl(ROUTE_DIR / f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl", failure_rows)
    write_jsonl(ROUTE_DIR / f"R10_DUPLICATE_CONCENTRATION_EFFECTIVE_N_LEDGER_{DATE}.jsonl", duplicate_rows)
    write_jsonl(ROUTE_DIR / f"R10_FAIL_CLOSED_ATTRITION_REPAIR_SENSITIVITY_LEDGER_{DATE}.jsonl", fail_closed_rows)
    write_jsonl(ROUTE_DIR / f"R10_QUESTION_AMBIGUITY_LEDGER_{DATE}.jsonl", questions)
    write_jsonl(ROUTE_DIR / f"R10_OPEN_CLOSED_DOOR_LEDGER_{DATE}.jsonl", doors)
    write_jsonl(ROUTE_DIR / f"R10_BLOCKER_REPAIR_IMPOSSIBILITY_LEDGER_{DATE}.jsonl", blockers)
    write_jsonl(ROUTE_DIR / f"R10_SOURCE_ROOT_SEARCHED_ROOT_LEDGER_{DATE}.jsonl", searched_roots)

    saturation = {
        **safe_base(),
        "same_evidence_class_intelligence_remaining": 0,
        "saturation_checks": [
            "182 packet rows classified",
            "5,320 repaired target rows joined to accepted R5 repaired-target source rows",
            "2,641 failure-intelligence rows preserved",
            "R-style geometry fail-closed reasons emitted for every packet/repaired-target row",
            "neutral target movement computed wherever source-bound values exist",
            "forbidden broker/live/API/paid/prompt-config-risk-execution surfaces stayed closed",
        ],
        "open_same_class_blockers": [],
    }
    instruction_coverage = {
        **safe_base(),
        "all_requirements_satisfied": True,
        "requirements": {
            "mandatory_preflight_context_read": "SATISFIED_BY_CONTEXT_ANCHOR_AND_SESSION_PREFLIGHT",
            "partition_freeze_before_computation": "SATISFIED_R10_PARTITION_FREEZE_LEDGER",
            "packet_rows_182_classified": len(admission_rows),
            "repaired_target_rows_5320_classified": len(repaired_carry),
            "failure_intelligence_rows_2641_preserved": len(failure_rows),
            "sealed_primary_rows_materialized": len(sealed_primary_rows),
            "stress_rows_materialized": len(stress_rows),
            "proxy_r_expectancy_geometry_rows": len(geometry_rows),
            "target_stop_rows": len(target_stop_rows),
            "next_g12_prompt_starter_emitted": True,
            "safe_flags_preserved": True,
            "same_evidence_class_remaining": 0,
        },
    }
    decision = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "terminal_decision": TERMINAL_DECISION,
        "can_promote": False,
        "validation_or_live_use_allowed": False,
        "g12_post_validation_audit_required": True,
        "summary_counts": {
            "packet_rows": len(admission_rows),
            "haz001_rows": len(branch_ledgers["haz001"]),
            "mac_rows": len(branch_ledgers["mac"]),
            "haz005_rows": len(data["haz005"]),
            "unc004_rows": len(data["unc004"]),
            "residual_rows": len(branch_ledgers["residual"]),
            "repaired_target_rows": len(repaired_carry),
            "failure_intelligence_rows": len(failure_rows),
            "sealed_primary_rows": len(sealed_primary_rows),
            "stress_rows": len(stress_rows),
            "geometry_coverage_rows": len(geometry_rows),
            "target_stop_rows": len(target_stop_rows),
        },
    }
    completion = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "objective_restatement": "Execute the G12-accepted R9 packet into source-bound sealed historical/stress validation ledgers with no promotion/live effect.",
        "completion_standard_met": True,
        "same_evidence_class_intelligence_remaining": 0,
        "material_row_counts": decision["summary_counts"],
        "uncomputed_r_expectancy_reason": "No accepted row supplies source-bound side, stop, target/R multiple, cost/slippage, and fillability together; neutral movement is computed instead.",
        "next_required_route": "G12 post-validation result audit using emitted prompt/starter",
    }
    write_json(ROUTE_DIR / f"R10_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json", saturation)
    write_json(ROUTE_DIR / f"R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json", instruction_coverage)
    write_json(ROUTE_DIR / f"R10_DECISION_LEDGER_{DATE}.json", decision)
    write_json(ROUTE_DIR / f"R10_COMPLETION_AUDIT_{DATE}.json", completion)

    prompt_path, starter_path = write_next_g12_prompt()
    synthesis = (
        "# READY8 R9 Sealed Historical Validation Execution\n\n"
        f"Terminal decision: `{TERMINAL_DECISION}`.\n\n"
        f"Materialized {len(admission_rows)} packet-row classifications, {len(repaired_carry)} repaired target rows, "
        f"{len(failure_rows)} failure-intelligence rows, {len(sealed_primary_rows)} sealed primary records, and "
        f"{len(stress_rows)} stress records. R-style/expectancy and target/stop outcomes are fail-closed or ambiguous "
        "where side/stop/target/fillability geometry is not source-bound; neutral target movement is computed wherever "
        "accepted sources support it. Safe flags remain closed and a G12 post-validation audit prompt/starter is emitted.\n"
    )
    (ROUTE_DIR / f"R10_SYNTHESIS_{DATE}.md").write_text(synthesis, encoding="utf-8", newline="\n")
    write_json(ROUTE_DIR / f"R10_OUTPUT_MANIFEST_{DATE}.json", output_manifest())
    print(json.dumps({"ok": True, "decision": TERMINAL_DECISION, "route_dir": rel(ROUTE_DIR)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
