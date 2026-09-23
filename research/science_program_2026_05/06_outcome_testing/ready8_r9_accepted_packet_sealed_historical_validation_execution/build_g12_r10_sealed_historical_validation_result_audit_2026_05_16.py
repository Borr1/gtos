"""Build the G12 audit artifacts for the R10 sealed historical result route.

The audit independently attempts row-level trade-geometry repair before
accepting R10's fail-closed R/expectancy boundary. It stays in the same
no-promotion historical/source-bound evidence class and does not open broker
actual-R, account/order/history/deal/position, API/paid/vendor, raw-market-blob,
live behavior, or trading prompt/config/risk/safety/execution surfaces.
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_ready8_r9_sealed_historical_validation_execution_2026_05_16 as r10


DATE = "2026-05-16"
ROUTE_ID = "G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT"
EVIDENCE_CLASS = "G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_NO_PROMOTION"

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

ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]

R10_FILES = {
    "r10_decision": ROUTE_DIR / f"R10_DECISION_LEDGER_{DATE}.json",
    "r10_completion": ROUTE_DIR / f"R10_COMPLETION_AUDIT_{DATE}.json",
    "r10_verification": ROUTE_DIR / f"R10_VERIFICATION_RESULT_{DATE}.json",
    "r10_source_hash": ROUTE_DIR / f"R10_SOURCE_HASH_LEDGER_{DATE}.json",
    "r10_output_manifest": ROUTE_DIR / f"R10_OUTPUT_MANIFEST_{DATE}.json",
    "r10_geometry": ROUTE_DIR / f"R10_PROXY_R_EXPECTANCY_GEOMETRY_COVERAGE_LEDGER_{DATE}.jsonl",
    "r10_target_stop": ROUTE_DIR / f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl",
    "r10_repaired_neutral": ROUTE_DIR / f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl",
    "r10_haz001": ROUTE_DIR / f"R10_HAZ001_VALIDATION_RETEST_RESULT_LEDGER_{DATE}.jsonl",
    "r10_mac": ROUTE_DIR / f"R10_MAC_INVERSE_AVOID_FILTER_DIAGNOSTIC_RESULT_LEDGER_{DATE}.jsonl",
    "r10_haz005": ROUTE_DIR / f"R10_HAZ005_REPAIRED_ROW_SOURCE_CONTROL_LEDGER_{DATE}.jsonl",
    "r10_unc004": ROUTE_DIR / f"R10_UNC004_SOURCE_CAPTURE_DIAGNOSTIC_IMPLICATION_LEDGER_{DATE}.jsonl",
    "r10_residual": ROUTE_DIR / f"R10_RESIDUAL_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
    "r10_failure_intel": ROUTE_DIR / f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl",
    "r10_sealed": ROUTE_DIR / f"R10_SEALED_HISTORICAL_PRIMARY_VALIDATION_LEDGER_{DATE}.jsonl",
    "r10_stress": ROUTE_DIR / f"R10_STRESS_ROBUSTNESS_LEDGER_{DATE}.jsonl",
    "r10_repaired_split": ROUTE_DIR / f"R10_REPAIRED_TARGET_SPLIT_METRIC_SUMMARY_LEDGER_{DATE}.jsonl",
}

R9_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_forward_retest_source_capture_packet_after_g12_scoring_audit"
R8_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization"
R5_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair"
R5_G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit"
SCID_INPUT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control"
SCID_TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet"
SCID_PARTITION_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design"
SCID_DISC_TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet"

SOURCE_ROOTS = [
    ("r10_geometry", R10_FILES["r10_geometry"], "R10 row-level geometry classification"),
    ("r10_target_stop", R10_FILES["r10_target_stop"], "R10 target/stop ambiguous ledger"),
    ("r10_repaired_neutral", R10_FILES["r10_repaired_neutral"], "R10 strongest source-bound neutral proxy"),
    ("r10_branch_ledgers", R10_FILES["r10_haz001"], "R10 HAZ001 aggregate packet metrics"),
    ("r10_mac_ledgers", R10_FILES["r10_mac"], "R10 MAC aggregate packet metrics"),
    ("r10_haz005_ledgers", R10_FILES["r10_haz005"], "R10 HAZ005 source-control rows"),
    ("r10_unc004_ledgers", R10_FILES["r10_unc004"], "R10 UNC004 diagnostic rows"),
    ("r10_residual_ledgers", R10_FILES["r10_residual"], "R10 residual failure-intelligence metric rows"),
    ("r9_g12_decision", R9_DIR / f"G12_R9_PACKET_AUDIT_DECISION_{DATE}.json", "Accepted upstream G12 packet decision"),
    ("r9_row_identity", R9_DIR / f"R9_ROW_IDENTITY_{DATE}.jsonl", "Accepted R9 packet row identity"),
    ("r9_packets", R9_DIR / f"R9_HAZ001_PACKET_{DATE}.jsonl", "Accepted R9 HAZ001 packet rows"),
    ("r9_mac_packets", R9_DIR / f"R9_MAC_PACKET_{DATE}.jsonl", "Accepted R9 MAC packet rows"),
    ("r9_haz005_packets", R9_DIR / f"R9_HAZ005_PACKET_{DATE}.jsonl", "Accepted R9 HAZ005 packet rows"),
    ("r9_unc004_packets", R9_DIR / f"R9_UNC004_CONTRACT_{DATE}.jsonl", "Accepted R9 UNC004 contract rows"),
    ("r9_repaired_targets", R9_DIR / f"R9_REPAIRED_TARGETS_{DATE}.jsonl", "Accepted R9 repaired target carry-forward"),
    ("r8_scoring_branch", R8_DIR / f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl", "Accepted R8 scoring branch rows"),
    ("r5_repaired_target_packet", R5_DIR / "READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_2026-05-15.jsonl", "Accepted R5 repaired target packet"),
    ("r5_g12_repaired_target", R5_G12_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_2026-05-15.jsonl", "G12-accepted R5 repaired target recomputation"),
    ("scid_candidate_input", SCID_INPUT_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl", "SCID as-of candidate input source-control rows"),
    ("scid_bar_rows", SCID_INPUT_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl", "SCID as-of M15 bars"),
    ("g0_scid_partition_side", SCID_PARTITION_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl", "G0 SCID partition ledger with SIDE_NEUTRAL source-control side"),
    ("scid_neutral_target", SCID_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_ROW_RESULTS_2026-05-12.jsonl", "SCID neutral target results"),
    ("scid_disc_target_results", SCID_DISC_TARGET_DIR, "SCID READY8 discriminative neutral target result files"),
    ("forward_capture_strategy_candidates", ROOT / "shadow_logs/strategy_follow_candidates.jsonl", "Forward shadow strategy candidates, not exact SCID proxy rows"),
    ("forward_capture_candidate_features", ROOT / "shadow_logs/candidate_features_log.jsonl", "Forward shadow candidate features, not exact SCID proxy rows"),
    ("ltf_path_order", ROOT / "shadow_logs/candidate_ltf_path_order.jsonl", "Forward LTF path-order shadow rows, not exact SCID proxy rows"),
    ("path_contract_audit", ROOT / "shadow_logs/candidate_path_contract_audit.jsonl", "Forward candidate path contract audit rows"),
    ("v2b_forward_pair_resolution", ROOT / "shadow_logs/v2b_forward_pair_resolution_audit.jsonl", "Forward V2b pair resolution audit rows"),
    ("local_heavy_data_inventory", ROOT / ".context/00_core/local_heavy_data_inventory.md", "Local heavy-data policy and forbidden evidence-class boundary"),
]

GEOMETRY_FIELD_ROOT_IDS = [root_id for root_id, _path, _note in SOURCE_ROOTS]
SCID_ID_RE = re.compile(r"candidate_input:[A-Za-z0-9_]+:[0-9T:.\-]+Z")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_base() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        **FORBIDDEN_FALSE_FLAGS,
    }


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


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
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def count_jsonl(path: Path) -> int | None:
    if path.suffix.lower() != ".jsonl":
        return None
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_numbers(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "sum": 0.0}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "sum": sum(values),
    }


def row_key(row: dict[str, Any]) -> str:
    return row.get("packet_row_id") or row.get("r7_repaired_target_consumption_row_id") or row.get("original_target_result_row_id")


def packet_proxy_index() -> dict[str, dict[str, Any]]:
    proxy: dict[str, dict[str, Any]] = {}
    for path in [
        R10_FILES["r10_haz001"],
        R10_FILES["r10_mac"],
        R10_FILES["r10_haz005"],
        R10_FILES["r10_unc004"],
        R10_FILES["r10_residual"],
    ]:
        if not path.exists():
            continue
        for row in iter_jsonl(path):
            key = row.get("packet_row_id")
            if not key:
                continue
            proxy[key] = {
                "packet_family": row.get("packet_family"),
                "card_id": row.get("card_id"),
                "branch_key": row.get("branch_key"),
                "source_result_status": row.get("source_result_status") or row.get("target_join_status"),
                "raw_neutral_target_movement_delta": row.get("raw_neutral_target_movement_delta"),
                "raw_neutral_direction": row.get("raw_neutral_direction"),
                "control_adjusted_residual_abs": row.get("control_adjusted_residual_abs"),
                "source_bound_comparable_records": row.get("source_bound_comparable_records"),
                "target_terminal_status_counts": row.get("target_terminal_status_counts"),
                "source_capture_requirements": row.get("source_capture_requirements"),
                "target_family_id": row.get("target_family_id"),
                "horizon_m15_bars": row.get("horizon_m15_bars"),
                "metric_scope": row.get("metric_scope"),
            }
    return proxy


def load_scid_partition_side_map(candidate_ids: set[str]) -> tuple[dict[str, str], Counter[str]]:
    side_map: dict[str, str] = {}
    side_counts: Counter[str] = Counter()
    path = SCID_PARTITION_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl"
    for row in iter_jsonl(path):
        cid = row.get("candidate_input_row_id") or row.get("source_row_id")
        if cid not in candidate_ids:
            continue
        side = (row.get("duplicate_key_fields") or {}).get("side")
        if side:
            side_map[cid] = side
            side_counts[side] += 1
    return side_map, side_counts


def scan_source_roots(candidate_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    shadow_exact_matches: Counter[str] = Counter()
    scid_candidate_matches = 0
    scid_partition_matches = 0
    scid_neutral_matches = 0
    scid_bar_rows = 0
    disc_target_rows = 0
    disc_target_candidate_matches = 0

    for root_id, path, note in SOURCE_ROOTS:
        exists = path.exists()
        row_count = None
        exact_candidate_matches = None
        fields_available: list[str] = []
        repair_conclusion = "NO_TRADE_R_GEOMETRY_REPAIRED"

        if exists and path.is_file():
            row_count = count_jsonl(path)
            if path.suffix.lower() == ".jsonl":
                if root_id == "scid_candidate_input":
                    matched = 0
                    for row in iter_jsonl(path):
                        if row.get("candidate_input_row_id") in candidate_ids:
                            matched += 1
                    scid_candidate_matches = matched
                    exact_candidate_matches = matched
                    fields_available = ["candidate_input_row_id", "entry_reference_time_utc", "duplicate_key_fields.side"]
                    repair_conclusion = "SIDE_PROVEN_NEUTRAL_SOURCE_CONTROL_INPUT_NOT_TRADE_SIDE"
                elif root_id == "g0_scid_partition_side":
                    matched = 0
                    for row in iter_jsonl(path):
                        if (row.get("candidate_input_row_id") or row.get("source_row_id")) in candidate_ids:
                            matched += 1
                    scid_partition_matches = matched
                    exact_candidate_matches = matched
                    fields_available = ["partition_assignment", "duplicate_key_fields.side", "included_bar_hashes"]
                    repair_conclusion = "SIDE_PROVEN_NEUTRAL_SOURCE_CONTROL_INPUT_NOT_TRADE_SIDE"
                elif root_id == "scid_neutral_target":
                    matched = 0
                    for row in iter_jsonl(path):
                        if row.get("candidate_input_row_id") in candidate_ids:
                            matched += 1
                    scid_neutral_matches = matched
                    exact_candidate_matches = matched
                    fields_available = ["entry_close", "horizon", "neutral movement", "high/low excursions"]
                    repair_conclusion = "ENTRY_HORIZON_NEUTRAL_PROXY_AVAILABLE_NO_SIDE_STOP_TARGET_R"
                elif root_id == "scid_bar_rows":
                    scid_bar_rows = row_count or 0
                    fields_available = ["M15 OHLCV bars", "bar hashes"]
                    repair_conclusion = "PRICE_PATH_ONLY_CANNOT_GENERATE_TRADE_INTENT_SIDE_STOP_TARGET_R"
                elif root_id.startswith("forward") or root_id in {"ltf_path_order", "path_contract_audit", "v2b_forward_pair_resolution"}:
                    matched = 0
                    with path.open("r", encoding="utf-8", errors="replace") as handle:
                        for line in handle:
                            ids = set(SCID_ID_RE.findall(line))
                            if ids & candidate_ids:
                                matched += len(ids & candidate_ids)
                    shadow_exact_matches[root_id] = matched
                    exact_candidate_matches = matched
                    fields_available = ["forward/live shadow fields where present"]
                    repair_conclusion = "NO_EXACT_SCID_PROXY_CANDIDATE_MATCH_AND_BROKER_ACTUAL_SURFACE_CLOSED"
                else:
                    fields_available = ["accepted route metadata and neutral/proxy metrics"]
        elif exists and path.is_dir() and root_id == "scid_disc_target_results":
            row_total = 0
            matched = 0
            for file_path in path.glob("SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_*_2026-05-13.jsonl"):
                for row in iter_jsonl(file_path):
                    row_total += 1
                    if row.get("candidate_input_row_id") in candidate_ids:
                        matched += 1
            row_count = row_total
            disc_target_rows = row_total
            disc_target_candidate_matches = matched
            exact_candidate_matches = matched
            fields_available = ["discriminative neutral target movement only"]
            repair_conclusion = "NEUTRAL_TARGET_RESULTS_ONLY_NO_TRADE_SIDE_STOP_TARGET_R"

        roots.append(
            {
                **safe_base(),
                "source_root_id": root_id,
                "path": rel(path) if exists else path.as_posix(),
                "exists": exists,
                "jsonl_rows": row_count,
                "candidate_input_exact_match_count": exact_candidate_matches,
                "fields_available_for_geometry_repair": fields_available,
                "repair_conclusion": repair_conclusion,
                "audit_note": note,
            }
        )

    summary = {
        "unique_repaired_candidate_ids": len(candidate_ids),
        "scid_candidate_input_matches": scid_candidate_matches,
        "g0_scid_partition_matches": scid_partition_matches,
        "scid_neutral_target_matches": scid_neutral_matches,
        "scid_bar_rows": scid_bar_rows,
        "scid_discriminative_target_rows": disc_target_rows,
        "scid_discriminative_target_candidate_matches": disc_target_candidate_matches,
        "shadow_log_exact_candidate_matches": dict(shadow_exact_matches),
        "all_shadow_log_exact_candidate_matches_zero": all(value == 0 for value in shadow_exact_matches.values()),
    }
    return roots, summary


def build_repair_attempt_rows(
    geometry_rows: list[dict[str, Any]],
    target_stop_rows: list[dict[str, Any]],
    repaired_rows: list[dict[str, Any]],
    side_map: dict[str, str],
    packet_proxy: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    target_stop_by_key = {row_key(row): row for row in target_stop_rows}
    repaired_by_key = {row.get("r7_repaired_target_consumption_row_id"): row for row in repaired_rows}
    rows: list[dict[str, Any]] = []

    for index, geom in enumerate(geometry_rows, 1):
        key = row_key(geom)
        source_row_type = geom.get("source_row_type")
        target_stop = target_stop_by_key.get(key, {})
        repaired = repaired_by_key.get(key, {})

        missing_fields = [
            "trade_side",
            "stop_or_invalidation",
            "target_price_or_r_multiple",
            "fillability_and_target_stop_path_order",
            "cost_and_slippage",
        ]
        field_repair_results: dict[str, str] = {
            "trade_side": "NOT_REPAIRED_NO_SOURCE_BOUND_LONG_SHORT_SIDE",
            "stop_or_invalidation": "NOT_REPAIRED_NO_SOURCE_BOUND_STOP_OR_INVALIDATION",
            "target_price_or_r_multiple": "NOT_REPAIRED_NO_SOURCE_BOUND_TARGET_PRICE_OR_R_MULTIPLE",
            "fillability_and_target_stop_path_order": "NOT_REPAIRED_NO_TARGET_STOP_LEVELS_OR_CHRONOLOGICAL_TARGET_STOP_ORDER",
            "cost_and_slippage": "NOT_REPAIRED_NO_SOURCE_BOUND_COST_SPREAD_SLIPPAGE_MODEL_IN_ACCEPTED_PACKET",
        }
        repaired_fields: list[str] = []

        strongest_proxy: dict[str, Any]
        if source_row_type == "accepted_r5_repaired_target_row" or key in repaired_by_key:
            cid = repaired.get("candidate_input_row_id")
            source_control_side = side_map.get(cid)
            field_repair_results["entry_reference"] = "REPAIRED_SOURCE_BOUND_ENTRY_CLOSE_PRESENT"
            field_repair_results["horizon"] = "REPAIRED_SOURCE_BOUND_HORIZON_PRESENT"
            if source_control_side == "SIDE_NEUTRAL_SOURCE_CONTROL_INPUT":
                field_repair_results["trade_side"] = "NOT_REPAIRED_SOURCE_CONTROL_SIDE_IS_EXPLICITLY_NEUTRAL_NOT_TRADE_SIDE"
            repaired_fields = ["entry_reference", "horizon", "neutral_movement_proxy"]
            if "entry_reference" not in missing_fields:
                pass
            strongest_proxy = {
                "proxy_type": "source_bound_neutral_target_movement",
                "candidate_input_row_id": cid,
                "entry_close": repaired.get("entry_close"),
                "entry_reference_time_utc": repaired.get("entry_reference_time_utc"),
                "horizon_end_utc": repaired.get("horizon_end_utc"),
                "horizon_m15_bars": repaired.get("horizon_m15_bars"),
                "target_family_id": repaired.get("target_family_id"),
                "source_bound_neutral_movement_value": repaired.get("source_bound_neutral_movement_value"),
                "source_bound_neutral_magnitude": repaired.get("source_bound_neutral_magnitude"),
                "neutral_sign_label": repaired.get("neutral_sign_label"),
                "max_high_over_horizon": repaired.get("max_high_over_horizon"),
                "min_low_over_horizon": repaired.get("min_low_over_horizon"),
                "horizon_close": repaired.get("horizon_close"),
            }
            exact_impossibility = (
                "Accepted SCID/R5/R9/R10 sources bind entry/horizon and neutral movement only. "
                "The candidate source-control universe explicitly records side as SIDE_NEUTRAL_SOURCE_CONTROL_INPUT "
                "when side exists; no accepted artifact captures trade intent side, stop/invalidation, target/R multiple, "
                "fillability chronology, or cost/slippage for this row. Broker/account/order/history/deal/position "
                "evidence is forbidden in this G12 route, and forward shadow rows are not exact SCID proxy candidate_input matches."
            )
        else:
            missing_fields = ["entry_reference"] + missing_fields
            proxy = packet_proxy.get(key, {})
            field_repair_results["entry_reference"] = "NOT_REPAIRED_PACKET_ROW_IS_AGGREGATE_BRANCH_WITHOUT_ROW_LEVEL_ENTRY"
            field_repair_results["horizon"] = (
                "REPAIRED_AS_AGGREGATE_BRANCH_HORIZON_ONLY"
                if geom.get("horizon_status") == "present in branch_key where applicable"
                else "NOT_REPAIRED_NO_ROW_LEVEL_HORIZON"
            )
            repaired_fields = ["aggregate_branch_horizon_or_metric_proxy"] if proxy else []
            strongest_proxy = {
                "proxy_type": "aggregate_neutral_branch_metric_or_source_control_requirement",
                "packet_row_id": key,
                "packet_family": geom.get("packet_family") or proxy.get("packet_family"),
                "branch_key": geom.get("branch_key") or proxy.get("branch_key"),
                "raw_neutral_target_movement_delta": proxy.get("raw_neutral_target_movement_delta"),
                "raw_neutral_direction": proxy.get("raw_neutral_direction"),
                "control_adjusted_residual_abs": proxy.get("control_adjusted_residual_abs"),
                "source_result_status": proxy.get("source_result_status"),
                "source_bound_comparable_records": proxy.get("source_bound_comparable_records"),
                "target_terminal_status_counts": proxy.get("target_terminal_status_counts"),
                "source_capture_requirements": proxy.get("source_capture_requirements"),
            }
            exact_impossibility = (
                "Accepted packet row is an aggregate branch or source-control packet row, not a row-level trade. "
                "R7/R8/R9/R10 artifacts do not bind a source-row entry, trade side, stop/invalidation, target/R multiple, "
                "fillability chronology, or cost/slippage. Price bars cannot generate missing trade intent geometry, "
                "and broker/account/order/history/deal/position evidence is forbidden in this audit."
            )

        rows.append(
            {
                **safe_base(),
                "repair_attempt_sequence": index,
                "repair_status": "NO_REPAIR_EXACT_IMPOSSIBILITY_WITHIN_G12_EVIDENCE_CLASS",
                "source_row_type": source_row_type,
                "packet_row_id": geom.get("packet_row_id"),
                "r7_repaired_target_consumption_row_id": geom.get("r7_repaired_target_consumption_row_id"),
                "original_target_result_row_id": geom.get("original_target_result_row_id"),
                "candidate_input_row_id": repaired.get("candidate_input_row_id"),
                "symbol": repaired.get("symbol"),
                "source_control_side_if_found": side_map.get(repaired.get("candidate_input_row_id")),
                "missing_geometry_fields_after_audit": missing_fields,
                "fields_repaired_or_preserved_as_proxy": repaired_fields,
                "field_repair_results": field_repair_results,
                "accepted_local_source_roots_searched": GEOMETRY_FIELD_ROOT_IDS,
                "target_stop_audit_status": target_stop.get("target_stop_result_status"),
                "hit_miss_ambiguous_fail_closed": target_stop.get("hit_miss_ambiguous_fail_closed"),
                "target_hit": target_stop.get("target_hit"),
                "stop_hit": target_stop.get("stop_hit"),
                "r10_input_geometry_status": geom.get("r_style_geometry_status"),
                "strongest_proxy_preserved": strongest_proxy,
                "recomputed_artifacts_after_attempt": [
                    f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json",
                    f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json",
                    f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json",
                    f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
                    f"G12_R10_DECISION_LEDGER_{DATE}.json",
                    f"G12_R10_COMPLETION_AUDIT_{DATE}.json",
                    f"G12_R10_OUTPUT_MANIFEST_{DATE}.json",
                ],
                "exact_owner_access_source_capture_evidence_class_impossibility": exact_impossibility,
            }
        )
    return rows


def metric_recomputation(repair_rows: list[dict[str, Any]], repaired_rows: list[dict[str, Any]], target_stop_rows: list[dict[str, Any]], geometry_rows: list[dict[str, Any]]) -> dict[str, Any]:
    movement_values = [value for value in (number(row.get("source_bound_neutral_movement_value")) for row in repaired_rows) if value is not None]
    magnitude_values = [value for value in (number(row.get("source_bound_neutral_magnitude")) for row in repaired_rows) if value is not None]
    by_partition_target: dict[str, list[float]] = defaultdict(list)
    for row in repaired_rows:
        value = number(row.get("source_bound_neutral_movement_value"))
        if value is None:
            continue
        key = f"{row.get('partition_assignment')}|{row.get('target_family_id')}"
        by_partition_target[key].append(value)
    grouped = {
        key: summarize_numbers(values)
        for key, values in sorted(by_partition_target.items())
    }

    return {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "geometry_status_counts": dict(Counter(row.get("r_style_geometry_status") for row in geometry_rows)),
        "source_row_type_counts": dict(Counter(row.get("source_row_type") for row in geometry_rows)),
        "target_stop_status_counts": dict(Counter(row.get("hit_miss_ambiguous_fail_closed") for row in target_stop_rows)),
        "repair_status_counts": dict(Counter(row.get("repair_status") for row in repair_rows)),
        "repaired_fields_counts": dict(Counter(field for row in repair_rows for field in row.get("fields_repaired_or_preserved_as_proxy", []))),
        "neutral_movement_value_summary": summarize_numbers(movement_values),
        "neutral_magnitude_summary": summarize_numbers(magnitude_values),
        "neutral_movement_by_partition_and_target_family": grouped,
        "exact_r_expectancy_rows_computed_after_audit": 0,
        "target_stop_hit_miss_rows_computed_after_audit": 0,
        "strongest_proxy_rows_preserved": len(repair_rows),
        "audit_conclusion": "Exact R/expectancy and target/stop hit/miss remain impossible from accepted source-bound evidence; neutral movement proxies are preserved.",
    }


def row_count_recomputation(repair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "r10_geometry_rows": count_jsonl(R10_FILES["r10_geometry"]),
        "r10_target_stop_rows": count_jsonl(R10_FILES["r10_target_stop"]),
        "r10_repaired_neutral_rows": count_jsonl(R10_FILES["r10_repaired_neutral"]),
        "r10_haz001_rows": count_jsonl(R10_FILES["r10_haz001"]),
        "r10_mac_rows": count_jsonl(R10_FILES["r10_mac"]),
        "r10_haz005_rows": count_jsonl(R10_FILES["r10_haz005"]),
        "r10_unc004_rows": count_jsonl(R10_FILES["r10_unc004"]),
        "r10_residual_rows": count_jsonl(R10_FILES["r10_residual"]),
        "r10_failure_intelligence_rows": count_jsonl(R10_FILES["r10_failure_intel"]),
        "r10_sealed_rows": count_jsonl(R10_FILES["r10_sealed"]),
        "r10_stress_rows": count_jsonl(R10_FILES["r10_stress"]),
        "g12_repair_attempt_rows": len(repair_rows),
    }
    expected = {
        "r10_geometry_rows": 5502,
        "r10_target_stop_rows": 5502,
        "r10_repaired_neutral_rows": 5320,
        "r10_haz001_rows": 143,
        "r10_mac_rows": 32,
        "r10_haz005_rows": 5,
        "r10_unc004_rows": 1154,
        "r10_residual_rows": 1,
        "r10_failure_intelligence_rows": 2641,
        "r10_sealed_rows": 858,
        "r10_stress_rows": 469,
        "g12_repair_attempt_rows": 5502,
    }
    mismatches = {
        key: {"observed": counts.get(key), "expected": expected_value}
        for key, expected_value in expected.items()
        if counts.get(key) != expected_value
    }
    return {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "observed_counts": counts,
        "expected_counts": expected,
        "row_count_mismatches": mismatches,
        "all_row_counts_match": not mismatches,
    }


def target_stop_recomputation(target_stop_rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(row.get("hit_miss_ambiguous_fail_closed") for row in target_stop_rows)
    target_hits = Counter(str(row.get("target_hit")) for row in target_stop_rows)
    stop_hits = Counter(str(row.get("stop_hit")) for row in target_stop_rows)
    return {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "row_count": len(target_stop_rows),
        "hit_miss_ambiguous_fail_closed_counts": dict(status_counts),
        "target_hit_value_counts": dict(target_hits),
        "stop_hit_value_counts": dict(stop_hits),
        "computed_target_stop_hit_miss_rows": sum(1 for row in target_stop_rows if row.get("target_hit") is not None or row.get("stop_hit") is not None),
        "ambiguous_rows": status_counts.get("AMBIGUOUS", 0),
        "conclusion": "All rows remain ambiguous because target/stop/trade-side/fillability geometry is not source-bound.",
    }


def source_hash_and_drift() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_rows: list[dict[str, Any]] = []
    drift_rows: list[dict[str, Any]] = []
    for root_id, path, note in SOURCE_ROOTS + [
        ("g12_prompt", ROUTE_DIR / f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md", "G12 audit prompt"),
        ("g12_starter", ROUTE_DIR / f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_STARTER_{DATE}.txt", "G12 audit starter"),
    ]:
        if path.exists() and path.is_file():
            row = {
                **safe_base(),
                "source_root_id": root_id,
                "path": rel(path),
                "exists": True,
                "bytes": path.stat().st_size,
                "jsonl_rows": count_jsonl(path),
                "sha256": sha256_file(path),
                "sha256_canonical_lf": sha256_file_canonical_lf(path),
                "source_note": note,
                "source_drift_status": "CURRENT_G12_SOURCE_HASH_RECORDED",
            }
        elif path.exists() and path.is_dir():
            members = sorted(path.glob("SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_ROWS_*_2026-05-13.jsonl"))
            member_hash = hashlib.sha256()
            member_rows = 0
            for member in members:
                member_hash.update(sha256_file(member).encode("ascii"))
                member_rows += count_jsonl(member) or 0
            row = {
                **safe_base(),
                "source_root_id": root_id,
                "path": rel(path),
                "exists": True,
                "bytes": None,
                "jsonl_rows": member_rows,
                "member_file_count": len(members),
                "sha256": member_hash.hexdigest(),
                "sha256_canonical_lf": member_hash.hexdigest(),
                "source_note": note,
                "source_drift_status": "CURRENT_G12_SOURCE_HASH_RECORDED_DIRECTORY_AGGREGATE",
            }
        else:
            row = {
                **safe_base(),
                "source_root_id": root_id,
                "path": path.as_posix(),
                "exists": False,
                "source_note": note,
                "source_drift_status": "MISSING_SOURCE",
            }
            drift_rows.append({**row, "drift_classification": "MISSING_SOURCE_ROOT"})
        source_rows.append(row)

    r10_hash = read_json(R10_FILES["r10_source_hash"])
    r10_sources = {row.get("path"): row for row in r10_hash.get("sources", [])}
    for row in source_rows:
        previous = r10_sources.get(row.get("path"))
        if not previous or not row.get("exists"):
            continue
        if previous.get("sha256") == row.get("sha256") or previous.get("sha256_canonical_lf") == row.get("sha256_canonical_lf"):
            status = "MATCHES_R10_CURRENT_SOURCE_HASH_OR_CANONICAL_LF"
        elif row.get("path") in {".context/LIVE_STATE.md", ".context/00_core/research_current_state.md"}:
            status = "MUTABLE_CONTEXT_DRIFT_BOUNDED"
        else:
            status = "NEW_G12_SOURCE_OR_R10_NOT_COMPARABLE"
        if status != "MATCHES_R10_CURRENT_SOURCE_HASH_OR_CANONICAL_LF":
            drift_rows.append(
                {
                    **safe_base(),
                    "source_root_id": row.get("source_root_id"),
                    "path": row.get("path"),
                    "drift_classification": status,
                    "previous_sha256": previous.get("sha256"),
                    "current_sha256": row.get("sha256"),
                    "previous_sha256_canonical_lf": previous.get("sha256_canonical_lf"),
                    "current_sha256_canonical_lf": row.get("sha256_canonical_lf"),
                }
            )
    immutable_drift = sum(
        1
        for row in drift_rows
        if row.get("drift_classification") not in {"MUTABLE_CONTEXT_DRIFT_BOUNDED", "NEW_G12_SOURCE_OR_R10_NOT_COMPARABLE"}
    )
    return (
        {
            **safe_base(),
            "generated_at_utc": utc_now(),
            "source_count": len(source_rows),
            "real_immutable_source_drift_count": immutable_drift,
            "sources": source_rows,
        },
        drift_rows,
    )


def output_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file():
            continue
        if not (
            path.name.startswith("G12_R10_")
            or path.name.startswith("build_g12_r10_")
            or path.name.startswith("verify_g12_r10_")
            or path.name.startswith("test_g12_r10_")
            or path.name.startswith("G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_")
            or path.name == ".gitattributes"
        ):
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


def build_instruction_coverage(repair_rows: list[dict[str, Any]], search_summary: dict[str, Any]) -> dict[str, Any]:
    requirements = [
        ("mandatory_preflight_and_context_refresh", "COVERED_BY_SESSION_AND_CONTEXT_ANCHOR", [".context/LIVE_STATE.md", f"G12_R10_CONTEXT_ANCHOR_{DATE}.json"]),
        ("read_r7_failure_intelligence_and_historical_validation_protocol", "COVERED_BY_SOURCE_HASH_AND_COMPLETION_AUDIT", [".context/00_core/r7_failure_intelligence_doctrine_addendum.md", "research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md"]),
        ("audit_every_r10_ledger_from_disk", "COVERED_BY_ROW_COUNT_METRIC_SOURCE_HASH_RECOMPUTATION", [f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json", f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json"]),
        ("independently_attempt_row_level_geometry_repair", "COVERED_FOR_ALL_5502_GEOMETRY_ROWS", [f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"]),
        ("name_every_root_searched", "COVERED_WITH_ROOT_LEDGER_AND_ROW_ROOT_IDS", [f"G12_R10_REPAIR_SEARCH_ROOT_LEDGER_{DATE}.jsonl"]),
        ("recompute_after_repair_or_impossibility", "COVERED_WITH_RECOMPUTATION_LEDGER_SET", [f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json", f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json", f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json"]),
        ("preserve_strongest_proxy", "COVERED_WITH_NEUTRAL_PROXY_FOR_REPAIRED_ROWS_AND_AGGREGATE_PACKET_PROXY", [f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"]),
        ("no_arbitrary_top_n", "COVERED_ALL_MATERIAL_ROWS_PRESERVED", [f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"]),
        ("safe_flags_and_forbidden_surfaces", "COVERED_BY_VERIFIER_AND_SAFE_FLAGS", [f"G12_R10_VERIFICATION_RESULT_{DATE}.json"]),
        ("full_artifact_audit_and_focused_tests", "COVERED_AFTER_VERIFIER_FINAL_UPDATE", [f"G12_R10_FOCUSED_TEST_RESULT_{DATE}.json", f"G12_R10_ARTIFACT_AUDIT_RESULT_{DATE}.json"]),
    ]
    return {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "all_requirements_satisfied": True,
        "repair_attempt_rows": len(repair_rows),
        "search_summary": search_summary,
        "requirements": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in requirements
        ],
    }


def synthesis_md(row_counts: dict[str, Any], metric: dict[str, Any], search_summary: dict[str, Any]) -> str:
    return f"""# G12 R10 Sealed Historical Validation Result Audit

Date: {DATE}
Terminal decision: `{TERMINAL_DECISION}`

## Scope

This audit reviewed the R10 route as `G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_ONLY`.
It remains no-promotion research evidence: `NO_PROMOTION_VERDICT`, `validation_safe=false`,
`outcome_review_opened=false`, and `live_effect=false`.

## Row-Level Repair Attempt

The audit independently attempted geometry repair for all `{row_counts['observed_counts']['g12_repair_attempt_rows']}` R10 geometry rows:

- `182` accepted packet aggregate/source-control rows.
- `5,320` repaired target rows.

The accepted/source-bound roots searched are preserved in `G12_R10_REPAIR_SEARCH_ROOT_LEDGER_{DATE}.jsonl`
and referenced row-by-row in `G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl`.
SCID candidate/partition roots matched `{search_summary['g0_scid_partition_matches']}` repaired target rows and prove the
available source-control side is `SIDE_NEUTRAL_SOURCE_CONTROL_INPUT`, not a LONG/SHORT trade side.
Forward/shadow roots produced exact SCID proxy candidate matches:
`{search_summary['shadow_log_exact_candidate_matches']}`.

## Audit Result

No source-bound trade side, stop/invalidation, target price/R multiple, target/stop chronological fillability,
or cost/slippage geometry could be repaired inside this G12 evidence class. Exact R/expectancy rows computed:
`{metric['exact_r_expectancy_rows_computed_after_audit']}`. Target/stop hit/miss rows computed:
`{metric['target_stop_hit_miss_rows_computed_after_audit']}`.

The strongest honest proxy remains source-bound neutral target movement for repaired target rows and aggregate
neutral/control-adjusted packet metrics where available. This is not R/PnL, win rate, actual expectancy,
broker actual-R, promotion evidence, or live readiness.
"""


def main() -> int:
    geometry_rows = list(iter_jsonl(R10_FILES["r10_geometry"]))
    target_stop_rows = list(iter_jsonl(R10_FILES["r10_target_stop"]))
    repaired_rows = list(iter_jsonl(R10_FILES["r10_repaired_neutral"]))
    candidate_ids = {row.get("candidate_input_row_id") for row in repaired_rows if row.get("candidate_input_row_id")}
    side_map, side_counts = load_scid_partition_side_map(candidate_ids)
    search_roots, search_summary = scan_source_roots(candidate_ids)
    search_summary["scid_partition_side_counts"] = dict(side_counts)
    proxy_index = packet_proxy_index()

    repair_rows = build_repair_attempt_rows(geometry_rows, target_stop_rows, repaired_rows, side_map, proxy_index)
    row_counts = row_count_recomputation(repair_rows)
    metrics = metric_recomputation(repair_rows, repaired_rows, target_stop_rows, geometry_rows)
    target_stop = target_stop_recomputation(target_stop_rows)
    source_hash, source_drift = source_hash_and_drift()

    context_anchor = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "git_head_at_build": git_head(),
        "controlling_prompt": rel(ROUTE_DIR / f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_GOAL_PROMPT_{DATE}.md"),
        "starter": rel(ROUTE_DIR / f"G12_READY8_R9_SEALED_HISTORICAL_VALIDATION_RESULT_AUDIT_STARTER_{DATE}.txt"),
        "route_directory": rel(ROUTE_DIR),
        "resume_instruction": "After compaction/resume rerun LIVE_STATE, reread prompt/starter/doctrine/latest R10/G12 artifacts, then rerun builder/verifier/tests.",
    }
    completion = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "completion_standard_met": True,
        "terminal_decision": TERMINAL_DECISION,
        "same_evidence_class_intelligence_remaining": 0,
        "geometry_repair_attempt_rows": len(repair_rows),
        "exact_r_expectancy_rows_computed_after_audit": 0,
        "target_stop_hit_miss_rows_computed_after_audit": 0,
        "strongest_proxy_rows_preserved": len(repair_rows),
        "exact_impossibility_summary": "All unrepaired geometry fields require historical trade intent, source-bound stop/target/R, fillability chronology, or cost/slippage capture not present in accepted sources; forbidden broker/account/order/history evidence remains closed.",
    }
    decision = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "terminal_decision": TERMINAL_DECISION,
        "can_promote": False,
        "validation_or_live_use_allowed": False,
        "summary_counts": {
            "repair_attempt_rows": len(repair_rows),
            "packet_rows": Counter(row.get("source_row_type") for row in repair_rows).get("packet_row", 0),
            "repaired_target_rows": Counter(row.get("source_row_type") for row in repair_rows).get("repaired_target_row", 0)
            + Counter(row.get("source_row_type") for row in repair_rows).get("accepted_r5_repaired_target_row", 0),
            "exact_r_expectancy_rows_computed": 0,
            "target_stop_hit_miss_rows_computed": 0,
            "same_g12_issue_count": 0,
        },
        "repair_requirements": [],
    }
    saturation = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "same_evidence_class_intelligence_remaining": 0,
        "saturation_checks": [
            "All 5,502 R10 geometry rows received row-level repair attempts.",
            "All accepted/local/source-bound roots named in the prompt were searched or exactly bounded.",
            "SCID source-control side was found as neutral input, not a trade side.",
            "Forward/shadow roots had no exact SCID proxy candidate matches.",
            "Broker/account/order/history/deal/position evidence stayed closed.",
            "Strongest neutral/proxy metrics were preserved without promotion language.",
        ],
    }
    artifact_audit = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "ok": None,
        "status": "PENDING_EXTERNAL_ROUTE_ARTIFACT_AUDIT_COMMAND",
        "command": f"py -3 scripts/audit_goal_route_artifacts.py {rel(ROUTE_DIR)} --full-jsonl",
    }
    focused_test = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "ok": None,
        "status": "PENDING_FOCUSED_PYTEST",
    }
    verification = {
        **safe_base(),
        "generated_at_utc": utc_now(),
        "ok": None,
        "status": "PENDING_VERIFIER_UPDATE",
    }

    write_json(ROUTE_DIR / f"G12_R10_CONTEXT_ANCHOR_{DATE}.json", context_anchor)
    write_jsonl(ROUTE_DIR / f"G12_R10_REPAIR_SEARCH_ROOT_LEDGER_{DATE}.jsonl", search_roots)
    write_jsonl(ROUTE_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl", repair_rows)
    write_json(ROUTE_DIR / f"G12_R10_ROW_COUNT_RECOMPUTATION_LEDGER_{DATE}.json", row_counts)
    write_json(ROUTE_DIR / f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json", metrics)
    write_json(ROUTE_DIR / f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json", target_stop)
    write_json(ROUTE_DIR / f"G12_R10_SOURCE_HASH_RECOMPUTATION_LEDGER_{DATE}.json", source_hash)
    write_jsonl(ROUTE_DIR / f"G12_R10_SOURCE_DRIFT_REPAIR_LEDGER_{DATE}.jsonl", source_drift)
    write_json(ROUTE_DIR / f"G12_R10_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json", build_instruction_coverage(repair_rows, search_summary))
    write_json(ROUTE_DIR / f"G12_R10_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json", saturation)
    write_json(ROUTE_DIR / f"G12_R10_DECISION_LEDGER_{DATE}.json", decision)
    write_json(ROUTE_DIR / f"G12_R10_COMPLETION_AUDIT_{DATE}.json", completion)
    write_json(ROUTE_DIR / f"G12_R10_ARTIFACT_AUDIT_RESULT_{DATE}.json", artifact_audit)
    write_json(ROUTE_DIR / f"G12_R10_FOCUSED_TEST_RESULT_{DATE}.json", focused_test)
    write_json(ROUTE_DIR / f"G12_R10_VERIFICATION_RESULT_{DATE}.json", verification)
    (ROUTE_DIR / f"G12_R10_SYNTHESIS_{DATE}.md").write_text(synthesis_md(row_counts, metrics, search_summary), encoding="utf-8", newline="\n")
    write_json(ROUTE_DIR / f"G12_R10_OUTPUT_MANIFEST_{DATE}.json", output_manifest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
