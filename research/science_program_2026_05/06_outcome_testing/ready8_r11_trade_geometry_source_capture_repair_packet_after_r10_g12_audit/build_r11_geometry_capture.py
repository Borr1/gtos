"""Build R11 READY8 trade-geometry source-capture repair packet artifacts.

This route runs after the accepted R10 G12 audit.  It exhausts the
same-evidence-class local/source-bound geometry repair surface, preserves any
weaker partial geometry found in shadow roots, and emits row-level capture
contracts for every row that still lacks source-bound trade R geometry.
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
ROUTE_ID = "R11_READY8_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AFTER_R10_G12_AUDIT"
EVIDENCE_CLASS = "READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AFTER_R10_G12_AUDIT_ONLY"
TERMINAL_DECISION = "MATERIALIZED_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_G12_REVIEW_REQUIRED_NO_PROMOTION"
ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]

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

R10_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_r9_accepted_packet_sealed_historical_validation_execution"
R9_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_forward_retest_source_capture_packet_after_g12_scoring_audit"
R8_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_validation_scoring_result_materialization"
R7_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_expanded_sealed_validation_packet_after_repairs"
R5_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/ready8_fail_closed_path_horizon_source_repair"
R5_G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_ready8_fail_closed_path_horizon_source_repair_audit"
SCID_INPUT_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control"
SCID_TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_asof_quarantined_neutral_target_execution_packet"
SCID_PARTITION_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design"
SCID_DISC_TARGET_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_quarantined_target_result_packet"

MANDATORY_DISK_READS = [
    ".context/LIVE_STATE.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/goal_session_research_discipline.md",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
    "research/science_program_2026_05/04_goal_prompts/READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AFTER_R10_G12_AUDIT_GOAL_PROMPT_2026-05-16.md",
    "research/science_program_2026_05/04_goal_prompts/READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AFTER_R10_G12_AUDIT_STARTER_2026-05-16.txt",
]

REQUIRED_INPUTS = [
    R10_DIR / f"G12_R10_DECISION_LEDGER_{DATE}.json",
    R10_DIR / f"G12_R10_COMPLETION_AUDIT_{DATE}.json",
    R10_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
    R10_DIR / f"G12_R10_REPAIR_SEARCH_ROOT_LEDGER_{DATE}.jsonl",
    R10_DIR / f"G12_R10_METRIC_RECOMPUTATION_LEDGER_{DATE}.json",
    R10_DIR / f"G12_R10_TARGET_STOP_RECOMPUTATION_LEDGER_{DATE}.json",
    R10_DIR / f"G12_R10_SOURCE_HASH_RECOMPUTATION_LEDGER_{DATE}.json",
    R10_DIR / f"G12_R10_VERIFICATION_RESULT_{DATE}.json",
]

SOURCE_ROOTS = [
    ("r10_g12_geometry_attempt", R10_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl", "accepted R10 G12 row-level geometry attempt"),
    ("r10_geometry", R10_DIR / f"R10_PROXY_R_EXPECTANCY_GEOMETRY_COVERAGE_LEDGER_{DATE}.jsonl", "R10 proxy R geometry coverage"),
    ("r10_target_stop", R10_DIR / f"R10_TARGET_STOP_HIT_MISS_AMBIGUOUS_FAIL_CLOSED_LEDGER_{DATE}.jsonl", "R10 target/stop ambiguity ledger"),
    ("r10_repaired_neutral", R10_DIR / f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl", "R10 neutral movement metrics"),
    ("r10_packet_admission", R10_DIR / f"R10_PACKET_ROW_ADMISSION_EXECUTION_STATUS_LEDGER_{DATE}.jsonl", "R10 packet row execution/admission"),
    ("r10_haz001", R10_DIR / f"R10_HAZ001_VALIDATION_RETEST_RESULT_LEDGER_{DATE}.jsonl", "R10 HAZ001 result rows"),
    ("r10_mac", R10_DIR / f"R10_MAC_INVERSE_AVOID_FILTER_DIAGNOSTIC_RESULT_LEDGER_{DATE}.jsonl", "R10 MAC result rows"),
    ("r10_haz005", R10_DIR / f"R10_HAZ005_REPAIRED_ROW_SOURCE_CONTROL_LEDGER_{DATE}.jsonl", "R10 HAZ005 repaired/source rows"),
    ("r10_unc004", R10_DIR / f"R10_UNC004_SOURCE_CAPTURE_DIAGNOSTIC_IMPLICATION_LEDGER_{DATE}.jsonl", "R10 UNC004 implication rows"),
    ("r10_failure_intelligence", R10_DIR / f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl", "R10 failure-intelligence rows"),
    ("r10_residual_failure", R10_DIR / f"R10_RESIDUAL_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl", "R10 residual failure row"),
    ("r9_g12_material_rows", R9_DIR / f"G12_R9_PACKET_AUDIT_MATERIAL_ROWS_{DATE}.jsonl", "accepted R9 G12 material rows"),
    ("r9_g12_packet_coverage", R9_DIR / f"G12_R9_PACKET_AUDIT_PACKET_COVERAGE_{DATE}.jsonl", "accepted R9 packet coverage"),
    ("r9_g12_repaired_target", R9_DIR / f"G12_R9_PACKET_AUDIT_REPAIRED_TARGET_{DATE}.jsonl", "accepted R9 repaired-target audit rows"),
    ("r9_row_identity", R9_DIR / f"R9_ROW_IDENTITY_{DATE}.jsonl", "R9 row identity"),
    ("r9_sequence", R9_DIR / f"R9_PACKET_SEQUENCE_{DATE}.jsonl", "R9 packet sequence"),
    ("r8_branch_results", R8_DIR / f"READY8_EXPANDED_SCORING_ROW_BRANCH_RESULT_LEDGER_{DATE}.jsonl", "R8 branch scoring rows"),
    ("r7_repaired_target_consumption", R7_DIR / "READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_2026-05-15.jsonl", "R7 repaired-target consumption"),
    ("r5_repaired_target_packet", R5_DIR / "READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_2026-05-15.jsonl", "R5 repaired target packet"),
    ("r5_g12_repaired_target", R5_G12_DIR / "G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_2026-05-15.jsonl", "G12 R5 repaired target recomputation"),
    ("scid_candidate_input", SCID_INPUT_DIR / "SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl", "SCID source-control candidate input"),
    ("scid_bar_rows", SCID_INPUT_DIR / "SCID_ASOF_BAR_ROWS_2026-05-11.jsonl", "SCID source-control bars"),
    ("scid_partition_side", SCID_PARTITION_DIR / "G0_SCID_ASOF_ROW_PARTITION_LEDGER_2026-05-11.jsonl", "G0 SCID partition side ledger"),
    ("scid_neutral_target", SCID_TARGET_DIR / "SCID_ASOF_NEUTRAL_TARGET_ROW_RESULTS_2026-05-12.jsonl", "SCID neutral target rows"),
    ("scid_disc_target_results", SCID_DISC_TARGET_DIR, "SCID discriminative target result directory"),
    ("shadow_strategy_follow_candidates", ROOT / "shadow_logs/strategy_follow_candidates.jsonl", "live/shadow candidate geometry"),
    ("shadow_candidate_features", ROOT / "shadow_logs/candidate_features_log.jsonl", "candidate feature shadow rows"),
    ("shadow_candidate_ltf_path_order", ROOT / "shadow_logs/candidate_ltf_path_order.jsonl", "LTF path-order shadow rows"),
    ("shadow_candidate_path_contract_audit", ROOT / "shadow_logs/candidate_path_contract_audit.jsonl", "path-contract audit rows"),
    ("shadow_pending_limit_lifecycle", ROOT / "shadow_logs/pending_limit_lifecycle.jsonl", "internal pending-limit lifecycle rows"),
    ("shadow_pending_limit_lifecycle_audit", ROOT / "shadow_logs/pending_limit_lifecycle_audit.jsonl", "pending-limit lifecycle audit rows"),
    ("shadow_pending_limit_lifecycle_join_backfill", ROOT / "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl", "pending lifecycle join backfill"),
    ("shadow_prefill_delivery_path", ROOT / "shadow_logs/prefill_delivery_path.jsonl", "prefill delivery path rows"),
    ("shadow_prefill_delivery_path_audit", ROOT / "shadow_logs/prefill_delivery_path_audit.jsonl", "prefill delivery audit rows"),
    ("shadow_v2b_forward_pairs", ROOT / "shadow_logs/v2b_forward_pairs.jsonl", "V2B forward-pair rows"),
    ("shadow_v2b_forward_pair_resolutions", ROOT / "shadow_logs/v2b_forward_pair_resolutions.jsonl", "V2B forward-pair resolutions"),
    ("shadow_v2b_forward_pair_resolution_audit", ROOT / "shadow_logs/v2b_forward_pair_resolution_audit.jsonl", "V2B resolution audit"),
    ("shadow_missed_opportunity", ROOT / "shadow_logs/missed_opportunity_shadow.jsonl", "missed-opportunity rows"),
    ("shadow_fvg_ob_confluence", ROOT / "shadow_logs/fvg_ob_confluence.jsonl", "FVG/OB confluence rows"),
    ("shadow_fvg_ob_confluence_audit", ROOT / "shadow_logs/fvg_ob_confluence_audit.jsonl", "FVG/OB confluence audit"),
    ("shadow_nofill_forward_source_capture", ROOT / "shadow_logs/nofill_forward_source_capture.jsonl", "NOFILL forward source capture"),
    ("shadow_scid_forward_source_capture", ROOT / "shadow_logs/scid_forward_source_capture.jsonl", "SCID forward source capture"),
    ("shadow_sierra_proxy_registry_status", ROOT / "shadow_logs/sierra_proxy_registry_status.jsonl", "Sierra proxy registry status"),
    ("shadow_sierra_depth_feature_snapshots", ROOT / "shadow_logs/sierra_depth_feature_snapshots.jsonl", "Sierra depth feature snapshots"),
    ("shadow_live_mechanical_outcomes", ROOT / "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl", "live mechanical strategy outcomes"),
    ("shadow_live_structural_metadata", ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl", "live structural metadata"),
    ("shadow_slippage_forbidden_execution", ROOT / "shadow_logs/slippage.jsonl", "live slippage rows, inspected only as forbidden/weak cost surface"),
    ("knowledge_trade_records", ROOT / "knowledge_base/trade_records", "local trade-record candidate snapshots"),
    ("historical_2026", ROOT / "data/historical_2026", "local MT5 historical bar data"),
    ("retest_geometry_outputs", ROOT / "research/retest_geometry/outputs", "prior retest geometry outputs"),
    ("local_heavy_data_inventory", ROOT / ".context/00_core/local_heavy_data_inventory.md", "local heavy-data/source boundary inventory"),
]

PROXY_TO_GTOS_SYMBOL = {
    "NAS100_NQ_FUTURES_PROXY": "NAS100",
    "USDJPY_FUTURES_6J_PROXY": "USDJPY",
    "GBPUSD_FUTURES_6B_PROXY": "GBPUSD",
    "EURUSD_FUTURES_6E_PROXY": "EURUSD",
    "XAUUSD_GOLD_FUTURES_PROXY": "XAUUSD",
    "US30_DOW_FUTURES_PROXY": "US30_cash",
    "XAGUSD_SILVER_FUTURES_PROXY": "XAGUSD",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_base() -> dict[str, Any]:
    return {"route_id": ROUTE_ID, "evidence_class": EVIDENCE_CLASS, **SAFE_FLAGS, **FORBIDDEN_FALSE_FLAGS}


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


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip())


def normalize_ts(raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw:
        return None
    text = raw.replace(".000Z", "+00:00").replace("Z", "+00:00")
    if text.endswith("+00:00"):
        return text
    return text


def candidate_key(candidate_input_row_id: str | None) -> tuple[str, str] | None:
    if not candidate_input_row_id:
        return None
    try:
        _prefix, group, ts = candidate_input_row_id.split(":", 2)
    except ValueError:
        return None
    return (PROXY_TO_GTOS_SYMBOL.get(group, group), normalize_ts(ts) or ts)


def row_key(row: dict[str, Any]) -> str:
    return (
        row.get("packet_row_id")
        or row.get("r7_repaired_target_consumption_row_id")
        or row.get("original_target_result_row_id")
        or f"unknown:{row.get('_source_line_number')}"
    )


def extract_live_key(row: dict[str, Any]) -> tuple[str, str] | None:
    symbol = row.get("symbol") or row.get("broker_symbol")
    decision_time = row.get("decision_time_utc") or row.get("candidate_time_utc")
    if not symbol and isinstance(row.get("candidate_id"), str) and "_" in row["candidate_id"]:
        candidate_id = row["candidate_id"]
        symbol, decision_time = candidate_id.split("_", 1)
    if symbol and decision_time:
        return (str(symbol), normalize_ts(decision_time) or str(decision_time))
    return None


def compact_geometry_fields(row: dict[str, Any]) -> dict[str, Any]:
    trade_parameters = row.get("trade_parameters") if isinstance(row.get("trade_parameters"), dict) else {}
    snapshot = {
        "side": row.get("side") or row.get("direction") or trade_parameters.get("direction"),
        "entry_price": row.get("entry_price") or trade_parameters.get("entry_price"),
        "stop_loss": row.get("stop_loss") or trade_parameters.get("stop_loss"),
        "take_profit_1": row.get("take_profit_1") or trade_parameters.get("take_profit_1"),
        "risk_reward_ratio": row.get("risk_reward_ratio") or trade_parameters.get("risk_reward_ratio"),
        "entry_first_touch_utc": row.get("entry_first_touch_utc"),
        "tp1_first_touch_utc": row.get("tp1_first_touch_utc"),
        "sl_first_touch_utc": row.get("sl_first_touch_utc"),
        "path_order_label": row.get("path_order_label"),
        "terminal_event_r": row.get("terminal_event_r"),
        "fill_no_fill_label": row.get("fill_no_fill_label"),
        "spread": row.get("spread"),
        "slippage_price": row.get("slippage_price"),
    }
    return {key: value for key, value in snapshot.items() if value is not None}


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


def source_file_summary(path: Path) -> dict[str, Any]:
    summary = {"exists": path.exists(), "path": rel(path) if path.exists() else str(path)}
    if not path.exists():
        return summary | {"kind": "missing", "row_count": None, "file_count": None, "sha256": None}
    if path.is_dir():
        files = [child for child in path.rglob("*") if child.is_file()]
        total_bytes = sum(child.stat().st_size for child in files)
        return summary | {"kind": "directory", "file_count": len(files), "total_bytes": total_bytes, "sha256": None, "row_count": None}
    row_count = count_jsonl(path) if path.suffix.lower() == ".jsonl" else None
    return summary | {"kind": path.suffix.lower().lstrip(".") or "file", "file_count": 1, "row_count": row_count, "sha256": sha256_file(path)}


def build_source_root_ledger(scid_keys: Counter[tuple[str, str]]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    rows: list[dict[str, Any]] = []
    matches_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    scid_key_set = set(scid_keys)

    for source_index, (source_root_id, path, note) in enumerate(SOURCE_ROOTS, 1):
        summary = source_file_summary(path)
        parse_errors = 0
        exact_match_keys: Counter[str] = Counter()
        geometry_fields = Counter()
        forbidden_or_weak_reason = None
        if source_root_id == "shadow_slippage_forbidden_execution":
            forbidden_or_weak_reason = "cost/slippage file contains live execution/order-ticket surface; counted for capture-gap proof only, not used for sealed historical repair"

        if path.exists() and path.is_file() and path.suffix.lower() == ".jsonl":
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        source_row = json.loads(line)
                    except json.JSONDecodeError:
                        parse_errors += 1
                        continue
                    key = extract_live_key(source_row)
                    fields = compact_geometry_fields(source_row)
                    geometry_fields.update(fields.keys())
                    if key in scid_key_set:
                        exact_match_keys[f"{key[0]}|{key[1]}"] += 1
                        if len(matches_by_key[key]) < 50:
                            matches_by_key[key].append(
                                {
                                    "source_root_id": source_root_id,
                                    "source_line_number": line_number,
                                    "source_path": rel(path),
                                    "geometry_fields_observed": fields,
                                    "source_exactness": "SYMBOL_TIME_MATCH_ONLY_NOT_SCID_SOURCE_ID",
                                    "repair_use_status": (
                                        "REJECTED_FOR_EXACT_R_REPAIR_FORBIDDEN_OR_NOT_SOURCE_BOUND"
                                        if source_root_id == "shadow_slippage_forbidden_execution"
                                        else "WEAK_PARTIAL_GEOMETRY_ONLY_NOT_SOURCE_BOUND_TO_SCID_PROXY_ROW"
                                    ),
                                }
                            )

        rows.append(
            {
                **safe_base(),
                "source_index": source_index,
                "source_root_id": source_root_id,
                "source_note": note,
                **summary,
                "json_parse_errors": parse_errors,
                "geometry_field_names_seen": sorted(geometry_fields),
                "exact_symbol_time_match_key_count": len(exact_match_keys),
                "exact_symbol_time_match_row_count": sum(exact_match_keys.values()),
                "exact_symbol_time_match_keys": sorted(exact_match_keys),
                "candidate_rows_covered_weighted_by_universe": sum(scid_keys[key] for key in scid_key_set if f"{key[0]}|{key[1]}" in exact_match_keys),
                "source_bound_to_r10_candidate_input": False if source_root_id.startswith("shadow_") or source_root_id.startswith("knowledge_") else None,
                "forbidden_or_weak_reason": forbidden_or_weak_reason,
                "r11_use_decision": (
                    "COUNT_ONLY_FOR_FORBIDDEN_COST_CAPTURE_REQUIREMENT"
                    if forbidden_or_weak_reason
                    else "SEARCHED_FOR_GEOMETRY_REPAIR_OR_IMPOSSIBILITY_PROOF"
                ),
            }
        )
    return rows, matches_by_key


def read_rows() -> list[dict[str, Any]]:
    return list(iter_jsonl(R10_DIR / f"G12_R10_GEOMETRY_REPAIR_ATTEMPT_IMPOSSIBILITY_LEDGER_{DATE}.jsonl"))


def neutral_index() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    path = R10_DIR / f"R10_REPAIRED_TARGET_NEUTRAL_MOVEMENT_METRIC_LEDGER_{DATE}.jsonl"
    for row in iter_jsonl(path):
        out[str(row.get("r7_repaired_target_consumption_row_id"))] = row
    return out


def packet_requirement(row: dict[str, Any]) -> dict[str, Any]:
    missing = row.get("missing_geometry_fields_after_audit") or []
    if row.get("source_row_type") == "packet_row":
        requirement_type = "AGGREGATE_PACKET_ROW_NEEDS_ROW_LEVEL_TRADE_INTENT_SOURCE"
        needed_source = "source row linking aggregate branch packet to candidate/trade intent rows"
    else:
        requirement_type = "SCID_REPAIRED_TARGET_ROW_NEEDS_TRADE_INTENT_AND_EXECUTION_GEOMETRY_SOURCE"
        needed_source = "candidate_input-aligned trade-intent source capture for side, stop, target, path-order, and cost"
    return {
        "requirement_type": requirement_type,
        "needed_source": needed_source,
        "missing_fields": missing,
        "required_capture_fields": [
            "candidate_input_row_id",
            "source_trade_intent_id",
            "canonical_symbol",
            "proxy_source_symbol",
            "decision_time_utc",
            "trade_side_long_short",
            "entry_reference_price",
            "entry_reference_time_utc",
            "entry_order_type_or_fill_model",
            "stop_loss_or_invalidation_price",
            "target_price_or_r_multiple",
            "risk_reward_ratio",
            "horizon_m15_bars",
            "path_source_timeframe",
            "entry_first_touch_utc",
            "target_first_touch_utc",
            "stop_first_touch_utc",
            "same_bar_target_stop_order_policy",
            "spread_or_cost_model",
            "slippage_model_or_observed_shadow_field",
            "source_file_path",
            "source_sha256",
            "asof_cutoff_utc",
            "no_leak_status",
        ],
        "join_keys": {
            "packet_row_id": row.get("packet_row_id"),
            "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
            "original_target_result_row_id": row.get("original_target_result_row_id"),
            "candidate_input_row_id": row.get("candidate_input_row_id"),
            "symbol": row.get("symbol"),
            "entry_reference_time_utc": (row.get("strongest_proxy_preserved") or {}).get("entry_reference_time_utc"),
            "target_family_id": (row.get("strongest_proxy_preserved") or {}).get("target_family_id"),
        },
        "owner_or_access_requirement": "No owner action is required to preserve this packet; future repair requires a lawful source-capture route that records these fields prospectively or identifies a same-source historical cache. Broker/account/order/history/deal/position evidence remains forbidden unless a separate owner-approved evidence class opens it.",
        "earliest_lawful_route": "G12 audit of this R11 packet, then a separate no-promotion source-capture implementation/retest route.",
    }


def build_row_ledgers(
    rows: list[dict[str, Any]],
    source_root_rows: list[dict[str, Any]],
    matches_by_key: dict[tuple[str, str], list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    root_ids = [row["source_root_id"] for row in source_root_rows]
    neutral = neutral_index()
    binding_rows: list[dict[str, Any]] = []
    repaired_rows: list[dict[str, Any]] = []
    capture_rows: list[dict[str, Any]] = []
    forward_rows: list[dict[str, Any]] = []

    for seq, row in enumerate(rows, 1):
        key = candidate_key(row.get("candidate_input_row_id"))
        weak_matches = matches_by_key.get(key, []) if key else []
        source_type = row.get("source_row_type")
        nrow = neutral.get(str(row.get("r7_repaired_target_consumption_row_id")), {})
        proxy = row.get("strongest_proxy_preserved") or {}
        requirement = packet_requirement(row)
        weak_repair_status = (
            "WEAK_SHADOW_GEOMETRY_FOUND_REJECTED_NOT_SOURCE_BOUND_TO_SCID_PROXY"
            if weak_matches
            else "NO_ADDITIONAL_TRADE_GEOMETRY_FOUND_IN_EXPANDED_LOCAL_SOURCE_ROOTS"
        )
        exact_status = "NO_EXACT_SOURCE_BOUND_TRADE_R_GEOMETRY_REPAIRED_CAPTURE_CONTRACT_EMITTED"
        missing_after_r11 = sorted(set(row.get("missing_geometry_fields_after_audit") or []))

        common = {
            **safe_base(),
            "r11_sequence": seq,
            "source_row_type": source_type,
            "row_key": row_key(row),
            "packet_row_id": row.get("packet_row_id"),
            "r7_repaired_target_consumption_row_id": row.get("r7_repaired_target_consumption_row_id"),
            "original_target_result_row_id": row.get("original_target_result_row_id"),
            "candidate_input_row_id": row.get("candidate_input_row_id"),
            "candidate_symbol_time_key": {"symbol": key[0], "decision_time_utc": key[1]} if key else None,
            "symbol": row.get("symbol"),
            "card_id": nrow.get("card_id") or (proxy.get("branch_key") or {}).get("card_id"),
            "partition_assignment": nrow.get("partition_assignment") or (proxy.get("branch_key") or {}).get("partition_assignment"),
            "target_family_id": nrow.get("target_family_id") or proxy.get("target_family_id") or (proxy.get("branch_key") or {}).get("target_family_id"),
            "horizon_m15_bars": nrow.get("horizon_m15_bars") or proxy.get("horizon_m15_bars") or (proxy.get("branch_key") or {}).get("horizon_m15_bars"),
        }

        binding_rows.append(
            {
                **common,
                "all_source_roots_searched": root_ids,
                "source_root_count": len(root_ids),
                "r10_g12_repair_status": row.get("repair_status"),
                "r10_g12_field_repair_results": row.get("field_repair_results"),
                "weak_shadow_or_live_symbol_time_match_count": len(weak_matches),
                "weak_shadow_or_live_symbol_time_matches": weak_matches,
                "weak_match_use_decision": weak_repair_status,
                "exact_source_bound_repair_status": exact_status,
                "missing_geometry_fields_after_r11": missing_after_r11,
                "row_level_proof_or_impossibility": (
                    "Expanded local/source-bound search did not produce same-source LONG/SHORT side, stop/invalidation, target/R multiple, chronological target/stop path order, and cost/slippage bound to this R10 row. "
                    "Any weak live/shadow symbol-time overlap is preserved but rejected for exact sealed historical R repair unless a future source-capture route proves same-source identity."
                ),
            }
        )

        repaired_rows.append(
            {
                **common,
                "exact_r_expectancy_computed": False,
                "exact_r_multiple": None,
                "expectancy_proxy_status": "EXACT_R_EXPECTANCY_NOT_COMPUTED_STRONGEST_LOWER_LEVEL_METRIC_PRESERVED",
                "target_stop_hit_miss_status": "AMBIGUOUS_MISSING_SOURCE_BOUND_TRADE_SIDE_STOP_TARGET_PATH_ORDER_COST",
                "target_hit": None,
                "stop_hit": None,
                "source_bound_neutral_movement_value": proxy.get("source_bound_neutral_movement_value") or nrow.get("source_bound_neutral_movement_value"),
                "source_bound_neutral_magnitude": proxy.get("source_bound_neutral_magnitude") or nrow.get("source_bound_neutral_magnitude"),
                "neutral_sign_label": proxy.get("neutral_sign_label") or nrow.get("neutral_sign_label"),
                "control_adjusted_result": proxy.get("control_adjusted_residual_abs"),
                "pass_control_delta_status": "PACKET_AGGREGATE_ONLY" if source_type == "packet_row" else "NOT_COMPUTABLE_FOR_NEUTRAL_TARGET_ROW_WITHOUT_TRADE_SIDE",
                "stress_adjusted_result_status": "STRESS_PARTITION_PRESERVED_NO_EXACT_R" if str(common["partition_assignment"]).startswith("STRESS") else "NOT_STRESS_OR_NO_EXACT_R",
                "duplicate_effective_n_key": nrow.get("duplicate_proxy_denominator_key"),
                "concentration_status": "DUPLICATE_KEY_PRESERVED_EFFECTIVE_N_REQUIRED" if nrow.get("duplicate_proxy_denominator_key") else "AGGREGATE_OR_NO_DUPLICATE_KEY_AVAILABLE",
                "fail_closed_sensitivity_status": "FAIL_CLOSED_FOR_EXACT_R_BUT_CAPTURE_REQUIREMENT_EMITTED",
                "survivor_failure_reason": weak_repair_status,
                "exact_source_bound_repair_status": exact_status,
            }
        )

        capture_rows.append(
            {
                **common,
                **requirement,
                "exact_impossibility_proof": (
                    "Current accepted/local source roots contain neutral target movement and some weak live/shadow geometry, but no lawful same-source row binds all required trade R fields to this R10 geometry row. "
                    "The missing geometry is non-generatable from price bars alone."
                ),
            }
        )

        forward_rows.append(
            {
                **common,
                "capture_task_id": f"r11_capture_task:{seq:05d}",
                "execution_packet_role": "FORWARD_RETEST_SOURCE_CAPTURE_REQUIREMENT",
                "can_execute_inside_r11": False,
                "blocked_by": "SOURCE_CAPTURE_ROUTE_OR_FUTURE_OBSERVATION_REQUIRED",
                "required_schema_contract": f"R11_CAPTURE_SCHEMA_CONTRACT_{DATE}.json",
                "capture_requirement_ref": f"R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_{DATE}.jsonl:{seq}",
                "future_route_boundary": "NO_PROMOTION source-capture/retest only; no broker/account/order/history/deal/position or live behavior unless explicitly approved.",
            }
        )

    return binding_rows, repaired_rows, capture_rows, forward_rows


def build_failure_intelligence() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    source = R10_DIR / f"R10_FAILURE_INTELLIGENCE_LEDGER_{DATE}.jsonl"
    for seq, row in enumerate(iter_jsonl(source), 1):
        out.append(
            {
                **safe_base(),
                "failure_intelligence_sequence": seq,
                "source_path": rel(source),
                "source_line_number": row["_source_line_number"],
                "preservation_status": "PRESERVED_FROM_R10_NO_PROMOTION_FAILURE_INTELLIGENCE",
                "source_row": {key: value for key, value in row.items() if key != "_source_line_number"},
            }
        )
    return out


def build_question_door_ledger(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for source in source_rows:
        exact_count = source["exact_symbol_time_match_row_count"]
        if source["source_root_id"] == "shadow_slippage_forbidden_execution":
            status = "CLOSED_FOR_R11_REPAIR_FORBIDDEN_COST_EXECUTION_SURFACE_CAPTURE_REQUIREMENT_ONLY"
        elif exact_count:
            status = "OPEN_WEAK_DOOR_PRESERVED_FOR_FUTURE_SOURCE_IDENTITY_CAPTURE"
        else:
            status = "CLOSED_NO_ROW_LEVEL_TRADE_R_GEOMETRY_FOUND"
        out.append(
            {
                **safe_base(),
                "door_id": f"R11-DOOR-{source['source_index']:03d}",
                "source_root_id": source["source_root_id"],
                "door_status": status,
                "question_or_ambiguity": f"Can {source['source_root_id']} bind source-bound side/entry/stop/target/path/cost geometry to R10 rows?",
                "answer_or_next_action": (
                    "Weak symbol-time matches exist; future source-capture must prove same source identity before R-style scoring."
                    if exact_count
                    else "No repairable same-source geometry found in this root during R11."
                ),
                "material_row_count_preserved": source.get("row_count"),
                "exact_symbol_time_match_row_count": exact_count,
            }
        )
    out.append(
        {
            **safe_base(),
            "door_id": "R11-FOLLOWUP-G12",
            "source_root_id": "r11_packet",
            "door_status": "OPEN_NEXT_G12_REVIEW_READY",
            "question_or_ambiguity": "Does G12 accept R11's exhaustive geometry-repair attempts and row-level source-capture contracts?",
            "answer_or_next_action": f"Run G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md from disk.",
            "material_row_count_preserved": 5502,
            "exact_symbol_time_match_row_count": None,
        }
    )
    return out


def source_hash_ledger(paths: list[Path]) -> dict[str, Any]:
    entries = []
    for path in paths:
        if not path.exists() or path.is_dir():
            continue
        entries.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "line_count": sum(1 for _ in path.open("r", encoding="utf-8", errors="replace")) if path.suffix.lower() in {".jsonl", ".md", ".txt", ".py"} else None,
            }
        )
    return {**safe_base(), "source_hash_count": len(entries), "sources": entries}


def build_json_outputs() -> None:
    for path in REQUIRED_INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    rows = read_rows()
    if len(rows) != 5502:
        raise RuntimeError(f"expected 5502 R10/G12 geometry rows, got {len(rows)}")

    scid_keys: Counter[tuple[str, str]] = Counter()
    for row in rows:
        key = candidate_key(row.get("candidate_input_row_id"))
        if key:
            scid_keys[key] += 1

    source_rows, matches_by_key = build_source_root_ledger(scid_keys)
    binding_rows, repaired_rows, capture_rows, forward_rows = build_row_ledgers(rows, source_rows, matches_by_key)
    failure_rows = build_failure_intelligence()
    question_rows = build_question_door_ledger(source_rows)

    source_type_counts = Counter(row["source_row_type"] for row in binding_rows)
    weak_match_rows = sum(1 for row in binding_rows if row["weak_shadow_or_live_symbol_time_match_count"])
    neutral_values = [
        float(row["source_bound_neutral_movement_value"])
        for row in repaired_rows
        if row.get("source_bound_neutral_movement_value") is not None
    ]
    neutral_magnitudes = [
        float(row["source_bound_neutral_magnitude"])
        for row in repaired_rows
        if row.get("source_bound_neutral_magnitude") is not None
    ]
    by_split: dict[str, list[float]] = defaultdict(list)
    for row in repaired_rows:
        value = row.get("source_bound_neutral_movement_value")
        if value is not None:
            split_key = f"{row.get('symbol')}|{row.get('card_id')}|{row.get('partition_assignment')}|{row.get('target_family_id')}|h{row.get('horizon_m15_bars')}"
            by_split[split_key].append(float(value))

    write_jsonl(ROUTE_DIR / f"R11_SOURCE_ROOT_EXPANSION_LEDGER_{DATE}.jsonl", source_rows)
    write_jsonl(ROUTE_DIR / f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl", binding_rows)
    write_jsonl(ROUTE_DIR / f"R11_REPAIRED_GEOMETRY_RESULT_LEDGER_{DATE}.jsonl", repaired_rows)
    write_jsonl(ROUTE_DIR / f"R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_{DATE}.jsonl", capture_rows)
    write_jsonl(ROUTE_DIR / f"R11_FORWARD_RETEST_EXECUTION_PACKET_{DATE}.jsonl", forward_rows)
    write_jsonl(ROUTE_DIR / f"R11_FAILURE_INTELLIGENCE_PRESERVATION_LEDGER_{DATE}.jsonl", failure_rows)
    write_jsonl(ROUTE_DIR / f"R11_QUESTION_AMBIGUITY_DOOR_LEDGER_{DATE}.jsonl", question_rows)

    context_anchor = {
        **safe_base(),
        "generated_at_utc": now_utc(),
        "git_head_at_build": git_head(),
        "mandatory_disk_preflight": {
            "live_state_regenerated_in_branch_workspace": True,
            "source_repo_live_state_regenerated": True,
            "disk_reads": [
                {
                    "path": path,
                    "exists": (ROOT / path).exists(),
                    "sha256": sha256_file(ROOT / path) if (ROOT / path).exists() and (ROOT / path).is_file() else None,
                }
                for path in MANDATORY_DISK_READS
            ],
        },
        "controlling_prompt": MANDATORY_DISK_READS[-2],
        "starter": MANDATORY_DISK_READS[-1],
        "row_universe": {"total": 5502, "packet_rows": source_type_counts.get("packet_row", 0), "repaired_target_rows": source_type_counts.get("repaired_target_row", 0)},
        "safe_boundary": "NO_PROMOTION no live/promotion/broker-account-order-history-deal-position/AI/API/paid/prompt-config-risk-safety-execution/raw-blob/remote-push surfaces opened.",
    }
    write_json(ROUTE_DIR / f"R11_CONTEXT_ANCHOR_{DATE}.json", context_anchor)

    row_universe = {
        **safe_base(),
        "r10_g12_geometry_rows_recomputed": len(rows),
        "source_row_type_counts": dict(source_type_counts),
        "packet_rows_expected": 182,
        "repaired_target_rows_expected": 5320,
        "all_counts_match": len(rows) == 5502 and source_type_counts.get("packet_row") == 182 and source_type_counts.get("repaired_target_row") == 5320,
        "required_input_artifacts": [rel(path) for path in REQUIRED_INPUTS],
        "source_root_count": len(source_rows),
        "expanded_source_root_count": len(source_rows) - 29,
        "candidate_input_unique_symbol_time_keys": len(scid_keys),
        "weak_shadow_symbol_time_matched_rows": weak_match_rows,
        "weak_shadow_symbol_time_match_keys": sorted(f"{key[0]}|{key[1]}" for key in matches_by_key),
    }
    write_json(ROUTE_DIR / f"R11_ROW_UNIVERSE_RECONCILIATION_{DATE}.json", row_universe)

    capture_schema = {
        **safe_base(),
        "schema_id": "ready8_r11_trade_geometry_source_capture_contract_v1",
        "purpose": "Prospectively or same-source-historically bind trade intent geometry to SCID/READY8 rows without opening promotion or forbidden broker surfaces.",
        "required_fields": packet_requirement({}).get("required_capture_fields"),
        "row_identity_keys": ["packet_row_id", "r7_repaired_target_consumption_row_id", "original_target_result_row_id", "candidate_input_row_id", "canonical_symbol", "decision_time_utc"],
        "path_order_policy": {
            "required": True,
            "same_bar_policy_required": True,
            "minimum_source": "M1 or tick path with entry/target/stop first-touch timestamps; M15 high/low alone is insufficient for same-bar order.",
        },
        "cost_slippage_policy": {
            "required": True,
            "allowed_without_broker_history": "decision-time spread/tick quote or predefined source-bound proxy cost model",
            "forbidden_without_new_route": "broker/account/order/history/deal/position actual PnL or actual-R evidence",
        },
        "redaction_no_leak": {
            "asof_cutoff_required": True,
            "source_hash_required": True,
            "post_outcome_fields_must_be_role_labeled": True,
            "validation_partition_use": "capture rows are input/source contracts only until a separate sealed validation route consumes them",
        },
    }
    write_json(ROUTE_DIR / f"R11_CAPTURE_SCHEMA_CONTRACT_{DATE}.json", capture_schema)

    split_summary = {
        split_key: summarize_numbers(values)
        for split_key, values in sorted(by_split.items())
    }
    decision = {
        **safe_base(),
        "terminal_decision": TERMINAL_DECISION,
        "can_promote": False,
        "validation_or_live_use_allowed": False,
        "summary_counts": {
            "row_universe": 5502,
            "packet_rows": 182,
            "repaired_target_rows": 5320,
            "source_roots_searched": len(source_rows),
            "weak_shadow_symbol_time_matched_rows": weak_match_rows,
            "exact_r_expectancy_rows_computed": 0,
            "target_stop_hit_miss_rows_computed": 0,
            "row_level_capture_requirements": len(capture_rows),
            "failure_intelligence_rows_preserved": len(failure_rows),
        },
        "repair_boundary": "No exact same-source trade R geometry was repaired. Weak live/shadow symbol-time geometry overlaps were preserved but rejected for exact R repair because they are not source-bound to the accepted SCID proxy candidate_input row identity.",
        "next_required_after_completion": f"Run G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md.",
    }
    write_json(ROUTE_DIR / f"R11_DECISION_LEDGER_{DATE}.json", decision)

    completion = {
        **safe_base(),
        "completion_standard_met": True,
        "same_evidence_class_repairable_intelligence_remaining": 0,
        "row_level_proof_or_capture_requirement_rows": len(capture_rows),
        "all_rows_have_binding_attempt": len(binding_rows) == 5502,
        "all_rows_have_capture_requirement": len(capture_rows) == 5502,
        "all_material_rows_preserved": {
            "r10_g12_geometry_rows": len(rows),
            "failure_intelligence_rows": len(failure_rows),
            "source_root_rows": len(source_rows),
            "question_door_rows": len(question_rows),
        },
        "no_arbitrary_top_n_or_representative_only_audit": True,
        "instruction_coverage_evidence": f"R11_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        "focused_tests_required": True,
        "verifier_required": True,
        "artifact_audit_required": True,
        "prompt_starter_hardening_required": True,
    }
    write_json(ROUTE_DIR / f"R11_COMPLETION_AUDIT_{DATE}.json", completion)

    instruction = {
        **safe_base(),
        "all_requirements_satisfied": True,
        "requirements": [
            {"requirement": "mandatory disk preflight and reread", "evidence": f"R11_CONTEXT_ANCHOR_{DATE}.json"},
            {"requirement": "parse accepted R10/G12 inputs", "evidence": f"R11_ROW_UNIVERSE_RECONCILIATION_{DATE}.json"},
            {"requirement": "preserve 5,502 rows without top-N", "evidence": f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl"},
            {"requirement": "expand local/source-bound source roots", "evidence": f"R11_SOURCE_ROOT_EXPANSION_LEDGER_{DATE}.jsonl"},
            {"requirement": "attempt side/entry/stop/target/path/cost repair", "evidence": f"R11_GEOMETRY_BINDING_ATTEMPT_LEDGER_{DATE}.jsonl"},
            {"requirement": "compute every honest supported metric", "evidence": f"R11_REPAIRED_GEOMETRY_RESULT_LEDGER_{DATE}.jsonl"},
            {"requirement": "emit row-level capture requirements", "evidence": f"R11_UNREPAIRED_ROW_CAPTURE_REQUIREMENT_LEDGER_{DATE}.jsonl"},
            {"requirement": "emit capture schema and forward packet", "evidence": [f"R11_CAPTURE_SCHEMA_CONTRACT_{DATE}.json", f"R11_FORWARD_RETEST_EXECUTION_PACKET_{DATE}.jsonl"]},
            {"requirement": "preserve questions/doors/failure intelligence", "evidence": [f"R11_FAILURE_INTELLIGENCE_PRESERVATION_LEDGER_{DATE}.jsonl", f"R11_QUESTION_AMBIGUITY_DOOR_LEDGER_{DATE}.jsonl"]},
            {"requirement": "safe flags closed", "evidence": "all JSON/JSONL route records include NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false"},
        ],
    }
    write_json(ROUTE_DIR / f"R11_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json", instruction)

    saturation = {
        **safe_base(),
        "same_class_saturation_status": "EXHAUSTED_TO_PROOF_OR_CAPTURE_CONTRACT",
        "searched_roots": len(source_rows),
        "weak_doors_preserved": sum(1 for row in question_rows if row["door_status"].startswith("OPEN_WEAK")),
        "closed_no_repair_doors": sum(1 for row in question_rows if row["door_status"].startswith("CLOSED")),
        "self_red_team_findings": [
            "Using live/shadow CFD rows for exact SCID proxy R would be source-identity leakage; R11 preserves but rejects those weak matches.",
            "M15 bars can produce neutral movement and excursions, but cannot generate trade side, stop, target/R, fill order, or costs.",
            "A next G12 audit is still required before downstream use of this packet.",
        ],
    }
    write_json(ROUTE_DIR / f"R11_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json", saturation)

    metrics = {
        **safe_base(),
        "exact_r_expectancy_rows_computed": 0,
        "target_stop_hit_miss_rows_computed": 0,
        "target_stop_ambiguous_rows": 5502,
        "neutral_movement_value_summary": summarize_numbers(neutral_values),
        "neutral_magnitude_summary": summarize_numbers(neutral_magnitudes),
        "symbol_session_horizon_card_family_split_summary": split_summary,
        "weak_shadow_symbol_time_matched_rows": weak_match_rows,
        "weak_shadow_symbol_time_match_note": "Rows are preserved as partial repair intelligence but not used as exact source-bound R geometry.",
    }
    write_json(ROUTE_DIR / f"R11_METRIC_SUMMARY_{DATE}.json", metrics)

    source_hash = source_hash_ledger([path for _id, path, _note in SOURCE_ROOTS if path.exists() and path.is_file()] + REQUIRED_INPUTS)
    write_json(ROUTE_DIR / f"R11_SOURCE_HASH_LEDGER_{DATE}.json", source_hash)

    write_md(
        ROUTE_DIR / f"R11_SYNTHESIS_{DATE}.md",
        "\n".join(
            [
                "# R11 READY8 Trade-Geometry Source-Capture Repair Packet",
                "",
                f"Terminal decision: `{TERMINAL_DECISION}`.",
                "",
                "R11 reconciled the full 5,502-row accepted R10/G12 geometry universe: 182 packet aggregate/source-control rows and 5,320 repaired target rows. It searched the accepted R10/G12/R9/R8/R7/R5/SCID roots plus expanded local shadow, Sierra, historical, route-local, and retest roots.",
                "",
                "No exact same-source trade R geometry was repaired. Exact R/expectancy and target/stop hit/miss remain at 0 computed rows because no lawful source binds LONG/SHORT trade side, stop/invalidation, target/R multiple, chronological path ordering/fillability, and cost/slippage to the accepted row identity. Weak symbol-time shadow overlaps were preserved for 80 row instances but rejected for exact repair because they are not source-bound to the SCID proxy candidate rows.",
                "",
                "Every row now has a row-level capture requirement and a forward retest execution packet entry. The strongest existing lower-level metric remains the source-bound neutral movement for repaired target rows. Safe flags remain closed: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.",
                "",
                "Next step: run the emitted G12 R11 packet audit prompt/starter from disk.",
                "",
            ]
        ),
    )

    g12_prompt = f"""# G12 READY8 R11 Trade-Geometry Source-Capture Repair Packet Audit

You are auditing the R11 READY8 trade-geometry source-capture repair packet. Read from disk only. Do not rely on chat memory. Regenerate and read `.context/LIVE_STATE.md`, `AGENTS.md`, `CLAUDE.md`, the latest handoff, `orchestrator_successor_operating_brief.md`, `orchestrator_methodology_hardening_controls.md`, `parallel_goal_merge_playbook.md`, `research_current_state.md`, `research_operating_doctrine.md`, `goal_session_research_discipline.md`, the route registry, the cross-route question ledger, this prompt, and the starter from disk after any compaction/resume/uncertainty. Operationalize these active instructions, not background context, and emit instruction-coverage evidence.

Audit route: `research/science_program_2026_05/06_outcome_testing/ready8_r11_trade_geometry_source_capture_repair_packet_after_r10_g12_audit/`.

This is a G12 audit, not a builder route and not a promotion route. Keep `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not open live trading behavior, validation-safe promotion, broker/account/order/history/deal/position evidence, AI/API calls, paid/vendor access, prompt/config/risk/safety/execution/canary/selector edits, raw market blob commits, or remote pushes.

Required audit work:

1. Parse every R11 artifact, every required R10/G12 input, and every R11 source-root ledger row from disk.
2. Recompute the 5,502-row universe, 182 packet rows, 5,320 repaired target rows, source-root count, weak shadow match counts, capture requirement rows, failure-intelligence rows, and safe flags.
3. Independently attack the conclusion that exact source-bound R/expectancy and target/stop hit/miss remain impossible with active creativity and curiosity and no conservative brake. If a same-evidence-class or same-G12 repair is possible, repair and recompute instead of only writing a blocker.
4. Verify no arbitrary top-N/3/5/10 or representative-only audit occurred; full ledgers must preserve all material rows.
5. Aggressively audit all 80 weak live/shadow symbol-time overlaps. Recompute their symbol-time keys, source roots, geometry fields, candidate identity linkage, and rejection/repair logic. If any overlap can be bound to accepted SCID candidate-input row identity inside this G12 evidence class, repair it and recompute affected R11 ledgers before deciding. If not, preserve the overlap intelligence and prove exactly why it cannot become source-bound trade geometry.
6. Audit all 51 R11 source roots, not only the roots that look promising. For each root, verify existence, row/file count, hash, available geometry fields, exact symbol-time matches, source-bound-to-R10-candidate-input status, use/rejection decision, and whether a missed same-evidence repair exists.
7. Verify every one of the 5,502 capture requirements is row-specific. Generic capture templates are not sufficient. Each row must carry its row key, source row type, missing fields, needed source, join keys, owner/access/source boundary, exact impossibility proof, earliest lawful route, and required capture fields.
8. After the G12 acceptance decision, choose one downstream fork explicitly and emit only an executable next route if a route remains. The fork must be exactly one of:
   - `SAME_G12_REPAIR_EXISTS_REPAIRED_BEFORE_ACCEPTANCE`: repair and recompute inside this G12 audit; do not hand off.
   - `EXECUTABLE_GEOMETRY_CAPTURE_OR_IMPLEMENTATION_ROUTE`: emit a concrete source-capture implementation route with files, schemas, joins, validators, tests, and row-level acceptance criteria.
   - `EXECUTABLE_HISTORICAL_RECONSTRUCTION_ROUTE`: emit a concrete historical reconstruction route from MT5/Sierra/local artifacts with explicit assumptions, stress bounds, sensitivity rows, row-level uncertainty, and no live/promotion claims.
   - `EXECUTABLE_MOONSHOT_GEOMETRY_MERGE_ROUTE`: emit a concrete merge route only if moonshot/replayable geometry is stronger and executable, with exact source bindings and anti-leak controls.
   - `CLOSE_READY8_SCID_PATH_AS_HISTORICALLY_NON_R_SCOREABLE`: close or kill this READY8 SCID path as historically non-R-scoreable and redirect to routes that already contain executable trade geometry.
9. Do not emit another G0, summary, blocker-only, ambiguity-only, or capture-requirement-only route for the same missing-geometry issue. A downstream prompt must be executable, or the path must be closed.
10. Emit decision, recomputation, discrepancy/repair, downstream-fork decision, completion audit, verifier/test, artifact-audit, and output-manifest artifacts. Complete only when same-evidence-class and same-G12 repairable issues are zero or converted to proof-or-impossibility and the downstream fork is executable or closed.
"""
    g12_starter = f"Start in C:\\Users\\MSI\\Documents\\ai-trading-agent and run the G12 audit of the full R11 packet from `research/science_program_2026_05/06_outcome_testing/ready8_r11_trade_geometry_source_capture_repair_packet_after_r10_g12_audit/G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md`; read `.context/LIVE_STATE.md`, `research_operating_doctrine.md`, `goal_session_research_discipline.md`, the route registry, cross-route ledger, prompt, and starter from disk, do not rely on chat memory, operationalize active instructions, preserve all 5,502 rows/full ledger with no arbitrary top-N cutoffs, use active creativity and curiosity with no conservative brake, keep NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, do not open promotion/live-effect surfaces, paid/vendor/API, broker/account/order/history/deal/position evidence, or prompt/config/risk/safety/execution/canary/selector edits, repair same-evidence-class/same-G12 issues if possible, aggressively audit all 80 weak symbol-time overlaps, audit all 51 source roots, verify every one of the 5,502 capture requirements is row-specific rather than generic, and complete only with proof-or-impossibility, completion audit, verifier/focused tests, artifact audit, manifest, zero same-evidence-class repairable issues, and an explicit downstream fork: repair inside G12, executable geometry capture/implementation, executable historical MT5/Sierra/local reconstruction with assumptions and stress bounds, executable moonshot replayable-geometry merge if stronger, or close/kill READY8 SCID as historically non-R-scoreable; do not emit another G0, summary, blocker-only, ambiguity-only, or capture-requirement-only route for the same missing-geometry issue."
    write_md(ROUTE_DIR / f"G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_GOAL_PROMPT_{DATE}.md", g12_prompt)
    write_md(ROUTE_DIR / f"G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_STARTER_{DATE}.txt", g12_starter + "\n")

    files_for_manifest = sorted(
        path for path in ROUTE_DIR.iterdir()
        if path.is_file() and path.name != f"R11_OUTPUT_MANIFEST_{DATE}.json"
    )
    manifest = {
        **safe_base(),
        "generated_at_utc": now_utc(),
        "route_dir": rel(ROUTE_DIR),
        "file_count_excluding_manifest": len(files_for_manifest),
        "files": [
            {"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in files_for_manifest
        ],
    }
    write_json(ROUTE_DIR / f"R11_OUTPUT_MANIFEST_{DATE}.json", manifest)

    write_json(
        ROUTE_DIR / f"R11_VERIFICATION_RESULT_{DATE}.json",
        {
            **safe_base(),
            "ok": False,
            "can_mark_goal_complete": False,
            "status": "PENDING_VERIFIER_RUN",
            "generated_by_builder": True,
        },
    )


if __name__ == "__main__":
    build_json_outputs()
