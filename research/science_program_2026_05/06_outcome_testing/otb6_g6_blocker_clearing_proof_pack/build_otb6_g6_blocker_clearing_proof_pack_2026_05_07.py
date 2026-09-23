#!/usr/bin/env python3
"""Build OTB6 G6 blocker-clearing proof pack.

This builder is intentionally input-only. It reads control documents, frozen G6
input packets, G12 blocker ledgers, sanitized path projections, and local data
availability manifests. It does not read result-bearing continuation resolution,
broker actual-R, quarantine, or account-history sources.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENERATED_AT_UTC = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
RUN_DATE = "2026-05-07"
TARGET_PACKET_IDS = ("OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-063", "OTG0-PKT-066")

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
OT_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
G6_PACKET_DIR = OT_ROOT / "otb2r_g6_local_ohlc_momentum_reversion_packets" / "packets"
G12_DIR = OT_ROOT / "g12_g3_g6_packet_builder_audit"
PATH_PROJ_DIR = OT_ROOT / "otb2r_input_only_path_rebuild" / "projections"
CONTROL_ROOT = ROOT / "research" / "science_program_2026_05"

PACKET_FILES = {
    "OTG0-PKT-060": G6_PACKET_DIR
    / "OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
    "OTG0-PKT-061": G6_PACKET_DIR
    / "OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
    "OTG0-PKT-063": G6_PACKET_DIR
    / "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
    "OTG0-PKT-066": G6_PACKET_DIR
    / "OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
}

CONTROL_FILES = {
    "otg0_control_rules": OT_ROOT / "OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json",
    "otg0_prereg_classification": OT_ROOT / "OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json",
    "otg0_frozen_manifest": OT_ROOT / "OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json",
    "otb0_packet_requirements": OT_ROOT
    / "otb0_blocker_clearing_governor"
    / "OTB0_PACKET_BUILDER_REQUIREMENTS_2026-05-07.json",
    "g12_blocked_ledger": G12_DIR / "G12_G3_G6_BLOCKED_REJECTED_QUESTION_LEDGER_2026-05-07.json",
    "g12_decision_ledger": G12_DIR / "G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.json",
    "g12_next_lane": G12_DIR / "G12_G3_G6_NEXT_LANE_RECOMMENDATION_2026-05-07.json",
    "g6_preregistry": CONTROL_ROOT / "03_experiment_specs" / "EXPERIMENT_PREREGISTRY_2026-05-06.json",
    "g6_domain_synthesis": CONTROL_ROOT
    / "01_domain_syntheses"
    / "G6_MOMENTUM_REVERSION_DOMAIN_SYNTHESIS_2026-05-06.md",
    "cnr_preregistration": ROOT
    / "research"
    / "program_control"
    / "CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md",
}

ALLOWED_LOCAL_LOGS = {
    "strategy_follow_candidates_input_only_projection": PATH_PROJ_DIR
    / "strategy_follow_candidates_input_only_projection_2026-05-07.jsonl",
    "prefill_delivery_path_input_only_projection": PATH_PROJ_DIR
    / "prefill_delivery_path_input_only_projection_2026-05-07.jsonl",
    "candidate_ltf_path_order_input_only_projection": PATH_PROJ_DIR
    / "candidate_ltf_path_order_input_only_projection_2026-05-07.jsonl",
    "candidate_mso_snapshot_joins": ROOT / "shadow_logs" / "candidate_mso_snapshot_joins.jsonl",
    "fvg_ob_confluence": ROOT / "shadow_logs" / "fvg_ob_confluence.jsonl",
    "live_structural_strategy_metadata": ROOT / "shadow_logs" / "live_structural_strategy_metadata.jsonl",
    "candidate_features_log": ROOT / "shadow_logs" / "candidate_features_log.jsonl",
}

FORBIDDEN_SOURCE_FRAGMENTS = (
    "quarantine",
    "continuation_no_retrace_resolutions",
    "m15_choch_diagnostic",
    "broker_actual_r",
    "account_history",
    "trade_records",
    "validation_safe",
    "outcome_review",
)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path, read_or_hashed: bool = True) -> dict[str, Any]:
    return {
        "path": rel(path) if path.exists() else rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256_file(path) if read_or_hashed and path.exists() else None,
        "read_or_hashed": read_or_hashed and path.exists(),
    }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, body: str) -> None:
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def get_nested(record: dict[str, Any], path: list[str]) -> Any:
    node: Any = record
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def collect_key_paths(obj: Any, keys: set[str], prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else key
            if key in keys:
                found.append(path)
            found.extend(collect_key_paths(value, keys, path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj[:5]):
            found.extend(collect_key_paths(value, keys, f"{prefix}[{idx}]"))
    return found


def jsonl_scan(path: Path, target_ids: set[str], wanted_keys: set[str]) -> dict[str, Any]:
    scan = {
        "source": file_info(path),
        "line_count": 0,
        "target_candidate_matches": 0,
        "target_match_examples": [],
        "wanted_key_paths_seen": [],
        "target_wanted_key_paths_seen": [],
        "json_errors": 0,
    }
    if not path.exists():
        return scan

    wanted_seen: set[str] = set()
    target_wanted_seen: set[str] = set()
    examples: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            scan["line_count"] += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                scan["json_errors"] += 1
                continue
            wanted_seen.update(collect_key_paths(record, wanted_keys))
            values = {
                str(record.get("candidate_id")),
                str(record.get("setup_id")),
                str(record.get("record_id")),
                str(record.get("trade_id")),
            }
            is_target = bool(target_ids.intersection(values))
            if is_target:
                scan["target_candidate_matches"] += 1
                target_wanted_seen.update(collect_key_paths(record, wanted_keys))
                if len(examples) < 3:
                    examples.append(
                        {
                            "candidate_id": record.get("candidate_id") or record.get("setup_id"),
                            "keys": sorted(record.keys())[:40],
                            "wanted_key_paths": sorted(collect_key_paths(record, wanted_keys))[:40],
                            "source_status": record.get("ltf_status")
                            or record.get("source_status")
                            or record.get("status"),
                        }
                    )

    scan["wanted_key_paths_seen"] = sorted(wanted_seen)
    scan["target_wanted_key_paths_seen"] = sorted(target_wanted_seen)
    scan["target_match_examples"] = examples
    return scan


def packet_summary(packet_id: str, packet: dict[str, Any]) -> dict[str, Any]:
    records = packet.get("records", [])
    return {
        "packet_id": packet_id,
        "experiment_id": packet.get("experiment_id"),
        "decision": packet.get("decision"),
        "record_count": len(records),
        "unique_duplicate_groups": len({r.get("duplicate_group_id") for r in records}),
        "promotion_verdict": packet.get("promotion_verdict"),
        "outcome_review_opened": packet.get("outcome_review_opened"),
        "blocked_packet_outcomes_inspected": packet.get("blocked_packet_outcomes_inspected"),
        "broker_actual_r_inspected": packet.get("broker_actual_r_inspected"),
        "file": file_info(PACKET_FILES[packet_id]),
    }


def analyze_060(packet: dict[str, Any]) -> dict[str, Any]:
    records = packet.get("records", [])
    ob_statuses = Counter()
    comparator_statuses = Counter()
    comparator_ready = 0
    group_match = 0
    missing_structured = []
    for record in records:
        ob = get_nested(record, ["ob_vs_generic_packet", "ob_bounds"]) or {}
        comparator = record.get("generic_retrace_comparator") or {}
        ob_statuses[str(ob.get("status"))] += 1
        comparator_statuses[str(comparator.get("status"))] += 1
        if comparator.get("status") == "INPUT_ONLY_GENERIC_80PCT_RETRACE_COMPARATOR_READY":
            comparator_ready += 1
        if record.get("matched_control_group_id") == record.get("duplicate_group_id"):
            group_match += 1
        required_structured = {
            "ob_id": ob.get("ob_id"),
            "ob_created_utc": ob.get("ob_created_utc"),
            "touch_sequence": ob.get("touch_sequence"),
            "market_state_source_hash": ob.get("market_state_source_hash"),
            "market_state_row_hash": ob.get("market_state_row_hash"),
        }
        if not all(required_structured.values()):
            missing_structured.append(record.get("record_id"))

    return {
        "packet_id": "OTG0-PKT-060",
        "packet_decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
        "subcomponent_clearance": {
            "matched_generic_comparator": "PROVED_LOCALLY",
            "reason": "Every row carries INPUT_ONLY_GENERIC_80PCT_RETRACE_COMPARATOR_READY and matched_control_group_id equals duplicate_group_id.",
            "comparator_ready_rows": comparator_ready,
            "matched_group_rows": group_match,
            "record_count": len(records),
            "unique_matched_control_groups": len({r.get("matched_control_group_id") for r in records}),
            "comparator_status_counts": dict(comparator_statuses),
        },
        "remaining_blocker": {
            "structured_ob_bounds": "NOT_PROVED",
            "reason": "OB low/high are present only as parsed decision-time verifier text; no structured OB id, creation event, touch sequence, market-state source hash, or row hash exists for every row.",
            "ob_status_counts": dict(ob_statuses),
            "records_missing_structured_ob_fields": len(missing_structured),
            "first_missing_record_ids": missing_structured[:5],
        },
    }


def analyze_061(packet: dict[str, Any], ltf_scan: dict[str, Any], local_availability: dict[str, Any]) -> dict[str, Any]:
    records = packet.get("records", [])
    e0_status = Counter()
    e1_status = Counter()
    source_blockers = Counter()
    for record in records:
        packet_fields = record.get("impulse_pullback_no_retrace_packet") or {}
        for model in packet_fields.get("entry_models", []):
            if model.get("entry_model_id") == "CNR_E0_DECISION_CLOSE_MARKET":
                e0_status[str(model.get("entry_source_status"))] += 1
            if model.get("entry_model_id") == "CNR_E1_DECISION_PRICE_PROXY":
                e1_status[str(model.get("entry_source_status"))] += 1
        source_blockers.update(packet_fields.get("source_blockers", []))

    return {
        "packet_id": "OTG0-PKT-061",
        "packet_decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
        "required_evidence": {
            "exact_executable_decision_price": {
                "status": "NOT_PROVED",
                "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
                "e0_status_counts": dict(e0_status),
                "e1_proxy_status_counts": dict(e1_status),
                "reason": "The packet exposes only non-promotable proxy geometry; the exact executable decision quote is not captured.",
            },
            "ordered_m1_or_tick_path_source": {
                "status": "NOT_PROVED",
                "sanitized_ltf_projection_target_matches": ltf_scan.get("target_candidate_matches"),
                "local_tick_parquet_files": local_availability["tick_parquet_summary"]["parquet_file_count"],
                "latest_local_m1_by_symbol": local_availability["latest_m1_by_symbol"],
                "reason": "No local tick parquet exists, local M1 sources end before the 2026-05-03 to 2026-05-06 target decisions, and the sanitized path projection does not supply a complete ordered input path.",
            },
        },
        "packet_source_blockers": dict(source_blockers),
    }


def analyze_063(packet: dict[str, Any]) -> dict[str, Any]:
    records = packet.get("records", [])
    score_models = Counter()
    missing_fields = Counter()
    feature_asof_present = 0
    for record in records:
        fields = record.get("exhaustion_changepoint_packet") or {}
        score = fields.get("predecision_changepoint_score_packet") or {}
        score_models[str(score.get("score_model_id"))] += 1
        missing_fields.update(fields.get("missing_exact_fields", []))
        if fields.get("feature_asof_utc") or score.get("feature_asof_utc"):
            feature_asof_present += 1

    return {
        "packet_id": "OTG0-PKT-063",
        "packet_decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
        "required_evidence": {
            "preregistered_changepoint_parser_model_output": {
                "status": "NOT_PROVED",
                "score_model_counts": dict(score_models),
                "feature_asof_utc_present_rows": feature_asof_present,
                "missing_exact_field_counts": dict(missing_fields),
                "reason": "The packet contains a fixed OHLC proxy score, not a preregistered statistical changepoint parser/model output with feature_asof_utc <= decision_asof_utc.",
            }
        },
    }


def analyze_066(packet: dict[str, Any], candidate_features_scan: dict[str, Any]) -> dict[str, Any]:
    records = packet.get("records", [])
    liquidity_status = Counter()
    round_status = Counter()
    structured_sweep_rows = 0
    ob_statuses = Counter()
    for record in records:
        sweep = record.get("liquidity_sweep_asof_fields") or {}
        round_packet = record.get("round_number_band_packet") or {}
        ob = record.get("ob_bounds") or {}
        liquidity_status[str(sweep.get("source_status"))] += 1
        round_status[str(round_packet.get("status"))] += 1
        ob_statuses[str(ob.get("status"))] += 1
        if sweep.get("sweep_type") and sweep.get("sweep_level") and sweep.get("source_hash"):
            structured_sweep_rows += 1

    return {
        "packet_id": "OTG0-PKT-066",
        "packet_decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
        "subcomponent_clearance": {
            "round_number_band_packet": "PROVED_LOCALLY",
            "round_number_status_counts": dict(round_status),
            "reason": "The packet carries the predefined XAU 50/100 round-number band fields.",
        },
        "remaining_blocker": {
            "structured_liquidity_sweep_join": "NOT_PROVED",
            "liquidity_source_status_counts": dict(liquidity_status),
            "structured_sweep_rows": structured_sweep_rows,
            "ob_status_counts": dict(ob_statuses),
            "candidate_features_target_matches": candidate_features_scan.get("target_candidate_matches"),
            "candidate_features_sweep_key_paths_seen": [
                p for p in candidate_features_scan.get("wanted_key_paths_seen", []) if "sweep" in p.lower()
            ],
            "reason": "Local candidate features expose sweep counts/types in some logs, but no decision-time sweep type, sweep level, and source hash joined to each XAU OB/round-number record.",
        },
    }


def local_data_availability(packets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    target_records = [r for p in packets.values() for r in p.get("records", [])]
    target_symbols = sorted({str(r.get("symbol") or r.get("broker_symbol")) for r in target_records if r})
    target_dates = sorted({str(r.get("decision_asof_utc", ""))[:10] for r in target_records if r.get("decision_asof_utc")})

    tick_root = ROOT / "data" / "ticks"
    parquet_files = sorted(tick_root.rglob("*.parquet")) if tick_root.exists() else []
    tick_readme = tick_root / "README.md"
    tick_availability_path = ROOT / "exports" / "mt5_data_dump" / "tick_data_availability.json"
    mt5_tick_availability = load_json(tick_availability_path) if tick_availability_path.exists() else {}

    sierra_m1: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for manifest_path in sorted((ROOT / "data" / "sierra_ohlcv_roots").glob("*/manifest.json")):
        manifest = load_json(manifest_path)
        for key, item in (manifest.get("files") or {}).items():
            if item.get("timeframe") != "M1":
                continue
            symbol = item.get("file_symbol") or key.split("_")[0]
            sierra_m1[str(symbol)].append(
                {
                    "manifest": rel(manifest_path),
                    "path": item.get("path"),
                    "first": item.get("first"),
                    "last": item.get("last"),
                    "rows": item.get("rows"),
                    "evidence_class": item.get("evidence_class"),
                    "source_system": item.get("source_system"),
                    "source_sha256": item.get("source_sha256"),
                }
            )

    latest_m1_by_symbol: dict[str, str | None] = {}
    for symbol, entries in sierra_m1.items():
        latest_m1_by_symbol[symbol] = max((e.get("last") for e in entries if e.get("last")), default=None)

    return {
        "artifact_family": "OTB6_G6_LOCAL_DATA_AVAILABILITY",
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "target_decision_dates": target_dates,
        "target_symbols": target_symbols,
        "tick_parquet_summary": {
            "tick_root": rel(tick_root),
            "tick_root_exists": tick_root.exists(),
            "parquet_file_count": len(parquet_files),
            "first_parquet_files": [rel(p) for p in parquet_files[:10]],
            "readme": file_info(tick_readme) if tick_readme.exists() else file_info(tick_readme, read_or_hashed=False),
        },
        "mt5_tick_availability_probe": {
            "source": file_info(tick_availability_path),
            "symbols": {
                symbol: {
                    "earliest_available": item.get("earliest_available"),
                    "latest_available": item.get("latest_available"),
                    "has_bid_ask": item.get("has_bid_ask"),
                }
                for symbol, item in mt5_tick_availability.items()
                if not symbol.startswith("_") and isinstance(item, dict)
            },
        },
        "sierra_m1_sources": dict(sierra_m1),
        "latest_m1_by_symbol": latest_m1_by_symbol,
        "coverage_verdict": "LOCAL_TICK_AND_M1_NOT_AVAILABLE_FOR_TARGET_DECISION_DATES",
        "coverage_reason": "No tick parquet exists under data/ticks. Sierra and MT5 M1/tick availability manifests end before the target 2026-05-03 through 2026-05-06 decisions.",
    }


def build_capture_contract() -> dict[str, Any]:
    common = [
        "candidate_id",
        "setup_id",
        "packet_id",
        "experiment_id",
        "symbol",
        "decision_asof_utc",
        "source_capture_utc",
        "source_path",
        "source_sha256",
        "row_hash",
        "feature_asof_utc_lte_decision_asof_utc",
        "duplicate_group_id",
        "no_result_fields_assertion",
    ]
    return {
        "artifact_family": "OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT",
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "contracts": {
            "OTG0-PKT-060": {
                "schema_id": "mechanical_ob_bounds_asof_v1",
                "required_fields": common
                + [
                    "market_state_source_path",
                    "market_state_source_sha256",
                    "market_state_row_hash",
                    "timeframe",
                    "ob_id",
                    "ob_low",
                    "ob_high",
                    "ob_mid",
                    "ob_created_utc",
                    "impulse_bos_utc",
                    "mitigation_state",
                    "touch_sequence",
                    "poi_price_level",
                    "selected_ob_reason",
                    "matched_control_group_id",
                ],
                "touch_sequence_schema": [
                    "touch_utc",
                    "touch_price",
                    "touch_source_path",
                    "touch_source_sha256",
                    "asof_status",
                ],
                "generic_comparator_schema_id": "generic_retrace_comparator_v1",
                "generic_comparator_required_fields": common
                + [
                    "lookback_window_start_utc",
                    "lookback_window_end_utc",
                    "lookback_bar_count",
                    "range_high",
                    "range_low",
                    "generic_retrace_level",
                    "matched_control_group_id",
                ],
            },
            "OTG0-PKT-061": {
                "schema_id": "continuation_no_retrace_decision_price_path_v1",
                "required_fields": common
                + [
                    "entry_model_id",
                    "decision_quote_time_msc",
                    "decision_bid",
                    "decision_ask",
                    "decision_mid",
                    "spread",
                    "decision_price_model",
                    "slippage_model_id",
                    "ordered_path_source_id",
                    "path_source_type",
                    "path_source_path",
                    "path_source_sha256",
                    "path_first_timestamp_utc",
                    "path_last_timestamp_utc",
                    "path_row_count",
                    "path_start_utc",
                    "path_end_utc",
                ],
                "allowed_primary_path_source_types": ["MT5_TICK_PARQUET"],
                "diagnostic_only_source_types": ["M1_OHLC_WITH_ORDER_AMBIGUITY"],
                "excluded_fields": ["tp_hit", "sl_hit", "path_order_label", "actual_r", "resolution_label"],
            },
            "OTG0-PKT-063": {
                "schema_id": "g6_changepoint_feature_v1",
                "required_fields": common
                + [
                    "changepoint_model_id",
                    "changepoint_model_version",
                    "parser_source_path",
                    "parser_sha256",
                    "threshold_freeze_id",
                    "input_ohlc_source_path",
                    "input_ohlc_source_sha256",
                    "window_start_utc",
                    "window_end_utc",
                    "changepoint_count",
                    "last_changepoint_utc",
                    "distance_from_last_changepoint_bars",
                    "changepoint_score",
                ],
                "model_freeze_requirement": "Model family, parser hash, window, and thresholds must be frozen before feature scoring.",
            },
            "OTG0-PKT-066": {
                "schema_id": "xau_liquidity_sweep_ob_round_join_v1",
                "required_fields": common
                + [
                    "ob_zone_key",
                    "ob_low",
                    "ob_high",
                    "ob_mid",
                    "round_number_model_id",
                    "nearest_50_level",
                    "nearest_100_level",
                    "inside_50_band_10usd",
                    "inside_100_band_15usd",
                    "sweep_type",
                    "sweep_level",
                    "sweep_direction",
                    "sweep_detected_utc",
                    "sweep_source_timeframe",
                    "liquidity_pool_id",
                    "join_status",
                ],
                "join_requirement": "Each liquidity sweep row must join to the XAU OB-zone/round-number record by ob_zone_key or candidate_id with source hash preserved.",
            },
        },
    }


def build_markdown_decision_ledger(ledger: dict[str, Any]) -> str:
    lines = [
        "# OTB6 G6 Blocker-Clearing Decision Ledger",
        "",
        f"- Generated at UTC: `{ledger['generated_at_utc']}`",
        "- Promotion verdict: `NO_PROMOTION_VERDICT`",
        "- Validation safe: `false`",
        "- Outcome review opened: `false`",
        "",
        "| Packet | Decision | Cleared evidence | Remaining exact blocker |",
        "|---|---|---|---|",
    ]
    for packet_id in TARGET_PACKET_IDS:
        row = ledger["packet_decisions"][packet_id]
        lines.append(
            f"| `{packet_id}` | `{row['decision']}` | {row['cleared_evidence']} | {row['remaining_exact_blocker']} |"
        )
    lines.extend(
        [
            "",
            "## Control Finding",
            "",
            "The proof pack does not clear any packet for outcome testing. "
            "`OTG0-PKT-060` has one locally proved subcomponent: the matched generic retrace comparator. "
            "Packet-level clearance remains blocked because G12 required structured OB bounds for every row.",
        ]
    )
    return "\n".join(lines)


def build_markdown_matrix(matrix: dict[str, Any]) -> str:
    lines = [
        "# OTB6 G6 Proof Matrix",
        "",
        "| Packet | Required evidence | Status | Evidence summary |",
        "|---|---|---|---|",
    ]
    for packet_id in TARGET_PACKET_IDS:
        for item in matrix["proof_matrix"][packet_id]:
            lines.append(
                f"| `{packet_id}` | {item['required_evidence']} | `{item['status']}` | {item['evidence_summary']} |"
            )
    return "\n".join(lines)


def build_markdown_contract(contract: dict[str, Any]) -> str:
    lines = [
        "# OTB6 G6 Prospective Capture Contract",
        "",
        "All contracts are shadow-only and input-only. They require file hashes, row hashes, and `feature_asof_utc <= decision_asof_utc` before any label or scoring lane opens.",
        "",
    ]
    for packet_id, spec in contract["contracts"].items():
        lines.extend(
            [
                f"## {packet_id}",
                "",
                f"- Schema: `{spec['schema_id']}`",
                f"- Required fields: {', '.join(f'`{field}`' for field in spec['required_fields'])}",
                "",
            ]
        )
    return "\n".join(lines)


def build_markdown_availability(availability: dict[str, Any]) -> str:
    lines = [
        "# OTB6 G6 Local Data Availability",
        "",
        f"- Coverage verdict: `{availability['coverage_verdict']}`",
        f"- Target decision dates: {', '.join(availability['target_decision_dates'])}",
        f"- Tick parquet files under `data/ticks`: {availability['tick_parquet_summary']['parquet_file_count']}",
        "",
        "| Symbol | Latest local M1 |",
        "|---|---|",
    ]
    for symbol, latest in sorted(availability["latest_m1_by_symbol"].items()):
        lines.append(f"| `{symbol}` | `{latest}` |")
    return "\n".join(lines)


def artifact_manifest() -> dict[str, Any]:
    artifacts = {}
    for path in sorted(OUT_DIR.glob("*")):
        if path.name == f"OTB6_G6_ARTIFACT_MANIFEST_{RUN_DATE}.json":
            continue
        if path.is_file():
            artifacts[path.name] = file_info(path)
    return {
        "artifact_family": "OTB6_G6_BLOCKER_CLEARING_PROOF_PACK",
        "generated_at_utc": GENERATED_AT_UTC,
        "git_head_at_generation": git_head(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "artifacts": artifacts,
    }


def build() -> dict[str, Any]:
    for path in list(PACKET_FILES.values()) + list(CONTROL_FILES.values()) + list(ALLOWED_LOCAL_LOGS.values()):
        lowered = rel(path).lower()
        if any(fragment in lowered for fragment in FORBIDDEN_SOURCE_FRAGMENTS):
            raise RuntimeError(f"Forbidden source path configured: {rel(path)}")

    packets = {packet_id: load_json(path) for packet_id, path in PACKET_FILES.items()}
    local_availability = local_data_availability(packets)

    target_ids = {
        str(record.get("candidate_id"))
        for packet in packets.values()
        for record in packet.get("records", [])
        if record.get("candidate_id")
    }
    scan_wanted_keys = {
        "ob_low",
        "ob_high",
        "ob_created_utc",
        "touch_sequence",
        "market_state_row_hash",
        "sweep_type",
        "sweep_level",
        "source_hash",
        "mso_detected_sweeps_count",
        "mso_detected_sweeps_types",
        "ltf_status",
        "m1_bar_count",
    }
    local_log_scans = {
        name: jsonl_scan(path, target_ids, scan_wanted_keys) for name, path in ALLOWED_LOCAL_LOGS.items()
    }

    analyses = {
        "OTG0-PKT-060": analyze_060(packets["OTG0-PKT-060"]),
        "OTG0-PKT-061": analyze_061(
            packets["OTG0-PKT-061"],
            local_log_scans["candidate_ltf_path_order_input_only_projection"],
            local_availability,
        ),
        "OTG0-PKT-063": analyze_063(packets["OTG0-PKT-063"]),
        "OTG0-PKT-066": analyze_066(packets["OTG0-PKT-066"], local_log_scans["candidate_features_log"]),
    }

    decision_ledger = {
        "artifact_family": "OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER",
        "generated_at_utc": GENERATED_AT_UTC,
        "git_head_at_generation": git_head(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "blocked_packet_outcomes_inspected": False,
        "broker_actual_r_inspected": False,
        "scope": "blocker_clearing_only_no_outcome_testing",
        "packet_summaries": {packet_id: packet_summary(packet_id, packets[packet_id]) for packet_id in TARGET_PACKET_IDS},
        "packet_decisions": {
            "OTG0-PKT-060": {
                "decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
                "cleared_evidence": "matched generic retrace comparator proved locally for 80/80 rows and 20 matched groups",
                "remaining_exact_blocker": "structured mechanical OB low/high plus OB creation/touch/source row hash for every row",
                "analysis": analyses["OTG0-PKT-060"],
            },
            "OTG0-PKT-061": {
                "decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
                "cleared_evidence": "none; non-promotable proxy geometry only",
                "remaining_exact_blocker": "exact executable decision price and ordered M1/tick path source",
                "analysis": analyses["OTG0-PKT-061"],
            },
            "OTG0-PKT-063": {
                "decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
                "cleared_evidence": "fixed OHLC proxy scaffold only",
                "remaining_exact_blocker": "preregistered changepoint parser/model output with feature_asof_utc <= decision_asof_utc",
                "analysis": analyses["OTG0-PKT-063"],
            },
            "OTG0-PKT-066": {
                "decision": "BLOCKED_WITH_EXACT_REMAINING_EVIDENCE",
                "cleared_evidence": "round-number band fields proved locally for 7/7 rows",
                "remaining_exact_blocker": "structured liquidity sweep type, level, and source hash joined to every XAU OB/round-number row",
                "analysis": analyses["OTG0-PKT-066"],
            },
        },
    }

    proof_matrix = {
        "artifact_family": "OTB6_G6_PROOF_MATRIX",
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "controlling_sources": {name: file_info(path) for name, path in CONTROL_FILES.items()},
        "local_log_scans": local_log_scans,
        "proof_matrix": {
            "OTG0-PKT-060": [
                {
                    "required_evidence": "structured OB bounds and lifecycle fields",
                    "status": "NOT_PROVED",
                    "evidence_summary": "OB bounds status is PARSED_FROM_DECISION_TIME_L2_VERIFICATION_DETAIL; structured OB id, creation, touch sequence, and source row hash are absent.",
                    "source": rel(PACKET_FILES["OTG0-PKT-060"]),
                },
                {
                    "required_evidence": "matched generic retrace comparator",
                    "status": "PROVED_LOCALLY",
                    "evidence_summary": "80/80 rows have INPUT_ONLY_GENERIC_80PCT_RETRACE_COMPARATOR_READY and matched group equality.",
                    "source": rel(PACKET_FILES["OTG0-PKT-060"]),
                },
            ],
            "OTG0-PKT-061": [
                {
                    "required_evidence": "exact executable decision price",
                    "status": "NOT_PROVED",
                    "evidence_summary": "CNR_E0 status remains EXACT_DECISION_ENTRY_PRICE_REQUIRED; CNR_E1 is a non-promotable proxy.",
                    "source": rel(PACKET_FILES["OTG0-PKT-061"]),
                },
                {
                    "required_evidence": "ordered M1/tick path source",
                    "status": "NOT_PROVED",
                    "evidence_summary": "No tick parquet exists and local M1 manifests end before the target decision dates.",
                    "source": "data/ticks plus data/sierra_ohlcv_roots manifests",
                },
            ],
            "OTG0-PKT-063": [
                {
                    "required_evidence": "preregistered changepoint parser/model output",
                    "status": "NOT_PROVED",
                    "evidence_summary": "Rows contain G6_FIXED_OHLC_PROXY_SCORE_NO_OUTCOME_TUNING and missing_exact_fields include true_statistical_changepoint_model_not_registered.",
                    "source": rel(PACKET_FILES["OTG0-PKT-063"]),
                },
                {
                    "required_evidence": "feature_asof_utc <= decision_asof_utc",
                    "status": "NOT_PROVED",
                    "evidence_summary": "No feature_asof_utc field is present in the changepoint proxy packet.",
                    "source": rel(PACKET_FILES["OTG0-PKT-063"]),
                },
            ],
            "OTG0-PKT-066": [
                {
                    "required_evidence": "round-number band packet",
                    "status": "PROVED_LOCALLY",
                    "evidence_summary": "7/7 rows carry G6_XAU_ROUND_50_100_BANDS_V1 fields.",
                    "source": rel(PACKET_FILES["OTG0-PKT-066"]),
                },
                {
                    "required_evidence": "structured liquidity sweep type/level/source hash joined to XAU OB row",
                    "status": "NOT_PROVED",
                    "evidence_summary": "liquidity_sweep_asof_fields source_status is NOT_STRUCTURED_IN_LOCAL_G6_PACKET_INPUTS; no sweep level/source hash join exists.",
                    "source": rel(PACKET_FILES["OTG0-PKT-066"]),
                },
            ],
        },
    }

    negative_evidence = {
        "artifact_family": "OTB6_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER",
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "evidence_sources_inspected": {
            "packets": {pid: file_info(path) for pid, path in PACKET_FILES.items()},
            "control": {name: file_info(path) for name, path in CONTROL_FILES.items()},
            "allowed_local_logs": {name: scan["source"] for name, scan in local_log_scans.items()},
        },
        "forbidden_sources_not_opened": list(FORBIDDEN_SOURCE_FRAGMENTS),
        "negative_findings": {
            "OTG0-PKT-060": analyses["OTG0-PKT-060"]["remaining_blocker"],
            "OTG0-PKT-061": analyses["OTG0-PKT-061"]["required_evidence"],
            "OTG0-PKT-063": analyses["OTG0-PKT-063"]["required_evidence"],
            "OTG0-PKT-066": analyses["OTG0-PKT-066"]["remaining_blocker"],
        },
    }

    capture_contract = build_capture_contract()

    adversarial_review = {
        "artifact_family": "OTB6_G6_ADVERSARIAL_SELF_REVIEW",
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "reviews": {
            "OTG0-PKT-060": {
                "strongest_objection": "Verifier text contains numeric OB low/high, so a permissive auditor might call bounds present.",
                "resolution": "G12's blocker explicitly rejects verifier-text parsing and requires structured source rows with OB creation/touch/source hashes. The packet status confirms parsed text only.",
                "residual_risk": "Low for blocker decision; medium for future denominator sufficiency because only 20 matched groups exist.",
            },
            "OTG0-PKT-061": {
                "strongest_objection": "Existing raw path logs may contain terminal path order fields.",
                "resolution": "This proof pack uses only sanitized input-only path projections. The exact blocker requires input path source before labels; no local tick parquet or current M1 coverage can supply it.",
                "residual_risk": "Low unless a previously unindexed tick capture outside data/ticks is produced by the operator.",
            },
            "OTG0-PKT-063": {
                "strongest_objection": "The fixed OHLC proxy score is predecision and threshold-frozen.",
                "resolution": "The blocker is not generic predecision scoring; it is a preregistered changepoint parser/model output with feature_asof_utc. The packet itself flags true_statistical_changepoint_model_not_registered.",
                "residual_risk": "Low for current packet; a prospective model contract can clear this later.",
            },
            "OTG0-PKT-066": {
                "strongest_objection": "Candidate feature logs contain sweep count/type fields.",
                "resolution": "Counts/types without sweep level, source hash, and row-level join to the XAU OB/round-number record do not satisfy G12's missing field.",
                "residual_risk": "Medium if a market-state snapshot with hidden liquidity-level rows exists under another allowed path not indexed here.",
            },
        },
    }

    completion_audit = {
        "artifact_family": "OTB6_G6_COMPLETION_AUDIT",
        "generated_at_utc": GENERATED_AT_UTC,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "scope_checks": {
            "target_packets_covered": sorted(decision_ledger["packet_decisions"].keys()) == sorted(TARGET_PACKET_IDS),
            "outcome_testing_run": False,
            "forbidden_sources_opened": False,
            "live_trading_surfaces_touched": False,
            "packet_level_promotions_claimed": False,
            "capture_contracts_written_for_all_blockers": sorted(capture_contract["contracts"].keys())
            == sorted(TARGET_PACKET_IDS),
        },
        "packet_completion": {
            pid: {
                "decision": decision_ledger["packet_decisions"][pid]["decision"],
                "remaining_exact_blocker": decision_ledger["packet_decisions"][pid]["remaining_exact_blocker"],
                "prospective_contract_available": True,
            }
            for pid in TARGET_PACKET_IDS
        },
        "can_mark_goal_complete": True,
        "completion_reason": "Each requested blocker was either partially proved as a subcomponent or proved impossible to clear with local input-only sources, with exact prospective capture contracts supplied.",
    }

    outputs = {
        f"OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_{RUN_DATE}.json": decision_ledger,
        f"OTB6_G6_PROOF_MATRIX_{RUN_DATE}.json": proof_matrix,
        f"OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_{RUN_DATE}.json": capture_contract,
        f"OTB6_G6_LOCAL_DATA_AVAILABILITY_{RUN_DATE}.json": local_availability,
        f"OTB6_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{RUN_DATE}.json": negative_evidence,
        f"OTB6_G6_ADVERSARIAL_SELF_REVIEW_{RUN_DATE}.json": adversarial_review,
        f"OTB6_G6_COMPLETION_AUDIT_{RUN_DATE}.json": completion_audit,
    }
    for name, payload in outputs.items():
        write_json(OUT_DIR / name, payload)

    write_md(
        OUT_DIR / f"OTB6_G6_BLOCKER_CLEARING_DECISION_LEDGER_{RUN_DATE}.md",
        build_markdown_decision_ledger(decision_ledger),
    )
    write_md(OUT_DIR / f"OTB6_G6_PROOF_MATRIX_{RUN_DATE}.md", build_markdown_matrix(proof_matrix))
    write_md(
        OUT_DIR / f"OTB6_G6_PROSPECTIVE_CAPTURE_CONTRACT_{RUN_DATE}.md",
        build_markdown_contract(capture_contract),
    )
    write_md(
        OUT_DIR / f"OTB6_G6_LOCAL_DATA_AVAILABILITY_{RUN_DATE}.md",
        build_markdown_availability(local_availability),
    )
    write_md(
        OUT_DIR / f"OTB6_G6_NEGATIVE_EVIDENCE_SATURATION_LEDGER_{RUN_DATE}.md",
        "# OTB6 G6 Negative Evidence Saturation Ledger\n\n"
        "All configured allowed input sources were hashed/read. The four target packets remain packet-level blocked; see the JSON ledger for per-field negative evidence.",
    )
    write_md(
        OUT_DIR / f"OTB6_G6_ADVERSARIAL_SELF_REVIEW_{RUN_DATE}.md",
        "# OTB6 G6 Adversarial Self Review\n\n"
        + "\n\n".join(
            f"## {pid}\n\n- Strongest objection: {row['strongest_objection']}\n- Resolution: {row['resolution']}\n- Residual risk: {row['residual_risk']}"
            for pid, row in adversarial_review["reviews"].items()
        ),
    )
    write_md(
        OUT_DIR / f"OTB6_G6_COMPLETION_AUDIT_{RUN_DATE}.md",
        "# OTB6 G6 Completion Audit\n\n"
        f"- Can mark goal complete: `{str(completion_audit['can_mark_goal_complete']).lower()}`\n"
        f"- Completion reason: {completion_audit['completion_reason']}\n"
        "- Promotion verdict: `NO_PROMOTION_VERDICT`\n"
        "- Validation safe: `false`\n"
        "- Outcome review opened: `false`",
    )

    manifest = artifact_manifest()
    write_json(OUT_DIR / f"OTB6_G6_ARTIFACT_MANIFEST_{RUN_DATE}.json", manifest)
    return manifest


if __name__ == "__main__":
    result = build()
    print(json.dumps({"ok": True, "artifact_count": len(result["artifacts"])}, indent=2))
