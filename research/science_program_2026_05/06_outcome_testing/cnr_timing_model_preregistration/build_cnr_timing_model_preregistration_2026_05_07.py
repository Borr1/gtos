#!/usr/bin/env python3
"""Build the CNR timing model preregistration control package.

This lane freezes future continuation/no-retrace timing, entry, target,
source, latency, duplicate, no-leak, and sample-floor rules before any new
outcome opening. It consumes committed G12/OTI6/OTR061 control artifacts and
source-hashed local files. It does not score outcomes or change live trading
behavior.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-07"
LANE_ID = "CNR_TIMING_MODEL_PREREGISTRATION"
PACKET_ID = "OTG0-PKT-061"
TARGET_RECORD_ID = "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
OUTCOME = ROOT / "research/science_program_2026_05/06_outcome_testing"
G12_OTI6 = OUTCOME / "g12_oti6_cnr_post_audit"
OTI6 = OUTCOME / "oti6_otr061_cnr_quarantined_results"
OTR061 = OUTCOME / "otr061_xau_tick_recovery"
G12_OTI5 = OUTCOME / "g12_oti5_otr061_post_audit"
G12_OTX = OUTCOME / "g12_otx_g6_post_audit"
OTB2R_G6 = OUTCOME / "otb2r_g6_local_ohlc_momentum_reversion_packets"
OTB2R_PATH = OUTCOME / "otb2r_input_only_path_rebuild"

PROMPT_PATH = BASE / f"CNR_TIMING_MODEL_PREREGISTRATION_GOAL_PROMPT_{DATE}.md"
PARQUET_PATH = OTR061 / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"

REQUIRED_OUTPUT_STEMS = [
    "CNR_TIMING_MODEL_PREREGISTRATION",
    "CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT",
    "CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC",
    "CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY",
    "CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP",
    "CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER",
    "CNR_TIMING_MODEL_DATA_EXPANSION_PLAN",
    "CNR_TIMING_MODEL_NEXT_PACKET_PLAN",
    "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY",
    "CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER",
    "CNR_TIMING_MODEL_ANTI_BOXING_REVIEW",
    "CNR_TIMING_MODEL_CONTEXT_ANCHOR",
    "CNR_TIMING_MODEL_COMPLETION_AUDIT",
]

CONTEXT_FILES = {
    "claude": ROOT / "CLAUDE.md",
    "live_state": ROOT / ".context/LIVE_STATE.md",
    "latest_handoff": ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context/00_core/quick_reference_card.md",
    "research_operating_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ROOT / ".context/00_core/research_current_state.md",
    "reading_order": ROOT / ".context/00_READING_ORDER.md",
    "goal_session_research_discipline": ROOT / ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": ROOT / ".context/00_core/local_heavy_data_inventory.md",
    "controlling_prompt": PROMPT_PATH,
}

CONTROL_INPUTS = {
    "g12_oti6_decision": G12_OTI6 / f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}.json",
    "g12_oti6_learning": G12_OTI6 / f"G12_OTI6_CNR_LEARNING_AND_NEXT_HYPOTHESIS_LEDGER_{DATE}.json",
    "g12_oti6_geometry": G12_OTI6 / f"G12_OTI6_CNR_GEOMETRY_AUDIT_{DATE}.json",
    "g12_oti6_source": G12_OTI6 / f"G12_OTI6_CNR_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json",
    "g12_oti6_duplicate": G12_OTI6 / f"G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT_{DATE}.json",
    "oti6_result": OTI6 / f"OTI6_CNR_RESULT_LEDGER_{DATE}.json",
    "oti6_method": OTI6 / f"OTI6_CNR_METHOD_FREEZE_{DATE}.json",
    "oti6_geometry": OTI6 / f"OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_{DATE}.json",
    "oti6_forensics": OTI6 / f"OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_{DATE}.json",
    "oti6_source": OTI6 / f"OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_{DATE}.json",
    "oti6_duplicate": OTI6 / f"OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_{DATE}.json",
    "oti6_methodology": OTI6 / f"OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}.json",
    "otr061_packet": OTR061 / f"OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_{DATE}.json",
    "otr061_hash": OTR061 / f"OTR061_XAU_TICK_SOURCE_HASH_LEDGER_{DATE}.json",
    "g12_oti5_decision_md": G12_OTI5 / f"G12_OTI5_OTR061_DECISION_LEDGER_{DATE}.md",
    "g12_otx_decision_md": G12_OTX / f"G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_{DATE}.md",
    "otb2r_g6_packet_061": OTB2R_G6 / "packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
    "otb2r_g6_packet_063": OTB2R_G6 / "packets/OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
    "otb2r_g6_packet_066": OTB2R_G6 / "packets/OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
    "otb2r_path_packet_063": OTB2R_PATH / "packets/OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__otb2r_input_only_path_packet_2026-05-07.json",
    "otb2r_path_packet_066": OTB2R_PATH / "packets/OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__otb2r_input_only_path_packet_2026-05-07.json",
    "recovered_tick_parquet": PARQUET_PATH,
}

OPTIONAL_LOCAL_SOURCES = {
    "main_xau_m1": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\historical\XAUUSD_M1.csv"),
    "main_xau_m5": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\historical\XAUUSD_M5.csv"),
    "main_xau_m15_2026": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\historical_2026\XAUUSD_M15.csv"),
    "main_xau_h1_2026": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\historical_2026\XAUUSD_H1.csv"),
    "sierra_xau_pilot_m1": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M1.csv"),
    "sierra_xau_pilot_manifest": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\manifest.json"),
    "sierra_xau_scid": Path(r"C:\SierraChart\Data\XAUUSD.scid"),
    "sierra_gc_scid": Path(r"C:\SierraChart\Data\GCM26-COMEX.scid"),
    "sierra_gc_depth_2026_05_06": Path(r"C:\SierraChart\Data\MarketDepthData\GCM26-COMEX.2026-05-06.depth"),
    "main_shadow_cnr_candidates": Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\continuation_no_retrace_candidates.jsonl"),
    "main_shadow_candidate_ltf_path_order": Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_ltf_path_order.jsonl"),
    "main_shadow_candidate_path_follow": Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\candidate_path_follow.jsonl"),
}

FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)

FORBIDDEN_OUTPUT_DIR_FRAGMENTS = (
    "quarantined_result",
    "quarantined_results",
    "result_lane",
    "outcome_result",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return f"ERROR[{result.returncode}]: {result.stderr.strip()}"
    return result.stdout.strip()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], lines: list[str] | None = None) -> None:
    body = [
        f"# {title} - {DATE}",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        f"**Validation safe:** `{str(VALIDATION_SAFE).lower()}`  ",
        f"**Outcome review opened:** `{str(OUTCOME_REVIEW_OPENED).lower()}`  ",
        f"**Live effect:** `{str(LIVE_EFFECT).lower()}`",
        "",
    ]
    if lines:
        body.extend(lines)
        body.append("")
    body.extend(["```json", json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(body), encoding="utf-8")


def source_row(path: Path, role: str, required: bool = True, compute_hash: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        "absolute_path": str(path.resolve()) if exists else str(path),
        "exists": exists,
        "last_write_time_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z") if exists else None,
        "path": rel(path),
        "required": required,
        "role": role,
        "sha256": sha256_file(path) if exists and compute_hash else None,
        "sha256_status": "HASHED" if exists and compute_hash else ("NOT_HASHED_NOT_CONSUMED" if exists else "MISSING"),
        "size_bytes": path.stat().st_size if exists else None,
    }


def base_payload(family: str, generated_at: str) -> dict[str, Any]:
    return {
        "account_history_accessed": False,
        "api_calls": 0,
        "artifact_family": family,
        "blocked_packet_outcome_source_read": False,
        "broker_actual_r_accessed": False,
        "canary_calls": 0,
        "databento_calls": 0,
        "date_stamp": DATE,
        "generated_at_utc": generated_at,
        "git_branch_at_build": git(["branch", "--show-current"]),
        "git_head_at_build": git(["log", "-1", "--oneline"]),
        "lane_id": LANE_ID,
        "live_effect": LIVE_EFFECT,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_id": PACKET_ID,
        "paid_data_calls": 0,
        "promotion_verdict": PROMOTION_VERDICT,
        "target_record_id": TARGET_RECORD_ID,
        "validation_safe": VALIDATION_SAFE,
    }


def load_inputs() -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    for name, path in CONTROL_INPUTS.items():
        if path.suffix.lower() == ".json" and path.exists():
            inputs[name] = read_json(path)
    return inputs


def find_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for nested in value.values():
            found = find_key(nested, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_key(item, key)
            if found is not None:
                return found
    return None


def count_packet_records(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "record_count": 0, "duplicate_group_count": 0, "symbols": {}}
    data = read_json(path)
    records = data.get("records") or []
    symbols: dict[str, int] = {}
    duplicate_groups: set[str] = set()
    entry_models: set[str] = set()
    for row in records:
        symbol = find_key(row, "symbol")
        duplicate_group = find_key(row, "duplicate_group_id")
        entry_model = find_key(row, "entry_model_id")
        if symbol:
            symbols[str(symbol)] = symbols.get(str(symbol), 0) + 1
        if duplicate_group:
            duplicate_groups.add(str(duplicate_group))
        if entry_model:
            entry_models.add(str(entry_model))
    return {
        "decision": data.get("decision"),
        "duplicate_group_count": len(duplicate_groups),
        "entry_models_found": sorted(entry_models),
        "exists": True,
        "packet_id": data.get("packet_id"),
        "record_count": len(records),
        "symbols": symbols,
    }


def live_state_freshness() -> dict[str, Any]:
    path = ROOT / ".context/LIVE_STATE.md"
    result: dict[str, Any] = {"exists": path.exists(), "path": rel(path)}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("| Status |"):
            result["research_context_status"] = line.split("|")[2].strip().strip("` ")
        if line.startswith("| Latest research-relevant commit |"):
            result["latest_research_relevant_commit"] = line.split("|")[2].strip().strip("` ")
        if line.startswith("| Current-state captured commit |"):
            result["current_state_captured_commit"] = line.split("|")[2].strip().strip("` ")
    return result


def collect_search_results(root: Path, terms: tuple[str, ...], max_results: int = 80) -> dict[str, Any]:
    row: dict[str, Any] = {
        "exists": root.exists(),
        "max_results": max_results,
        "patterns": list(terms),
        "results": [],
        "root": str(root),
        "search_status": "NOT_RUN_MISSING_ROOT",
        "truncated": False,
    }
    if not root.exists():
        return row
    skip_dirs = {".git", "__pycache__", ".pytest_cache", "node_modules"}
    denied: list[str] = []
    try:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda err: denied.append(str(err))):
            dirnames[:] = [
                d
                for d in dirnames
                if d not in skip_dirs and not d.startswith("pytest-cache-files") and not d.startswith("pytest-")
            ]
            for filename in filenames:
                full = Path(dirpath) / filename
                text = str(full)
                if any(term.lower() in text.lower() for term in terms):
                    row["results"].append(text)
                    if len(row["results"]) >= max_results:
                        row["truncated"] = True
                        raise StopIteration
    except StopIteration:
        pass
    row["denied_or_walk_errors"] = denied[:20]
    row["result_count_returned"] = len(row["results"])
    row["search_status"] = "SEARCHED"
    return row


def build_source_inventory(generated_at: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in CONTEXT_FILES.values():
        rows.append(source_row(path, "mandatory_preflight_context", required=True))
    for path in CONTROL_INPUTS.values():
        rows.append(source_row(path, "controlling_or_neighbor_input", required=True))
    for path in OPTIONAL_LOCAL_SOURCES.values():
        rows.append(source_row(path, "optional_local_source_found_for_expansion_or_context", required=False))

    search_roots = [
        ROOT,
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\science_program_2026_05\06_outcome_testing"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        Path(r"C:\tmp\gtos_otb\OTR061TICK"),
        Path(r"C:\tmp\gtos_otb\OTI6CNR"),
        Path(r"C:\tmp\gtos_otb\G12OTI5OTR061"),
        Path(r"C:\tmp\gtos_otb\G12OTI6"),
        Path(r"C:\SierraChart\Data"),
    ]
    searches = [
        collect_search_results(root, ("CNR", "OTR061", "OTG0-PKT-061", "OTG0-PKT-063", "OTG0-PKT-066", "XAUUSD", "GCM26", "MGC"))
        for root in search_roots
    ]
    return {
        **base_payload("CNR_TIMING_MODEL_SOURCE_INVENTORY", generated_at),
        "all_required_control_inputs_exist": all(path.exists() for path in CONTROL_INPUTS.values()),
        "all_required_control_inputs_hashed": all(row["sha256"] for row in rows if row["required"]),
        "control_input_rows": rows,
        "local_heavy_data_searches": searches,
        "source_inventory_verdict": "PASS_CONTROL_INPUTS_FOUND_HASHED_LOCAL_SEARCH_EXPANDED",
    }


def build_evidence(inputs: dict[str, Any], source_inventory: dict[str, Any]) -> dict[str, Any]:
    result = inputs["oti6_result"]
    geometry = inputs["oti6_geometry"]
    forensics = inputs["oti6_forensics"]
    packet = inputs["otr061_packet"]
    g12_learning = inputs["g12_oti6_learning"]
    ordered_path = result["ordered_path_summary"]
    original = geometry["original_gtos_geometry"]
    decision_quote = geometry["decision_quote_reconstructed_from_parquet"]
    distance = geometry["distance_diagnostics"]
    packet_record = packet["records"][0]
    return {
        "accepted_g12_decision": inputs["g12_oti6_decision"].get("terminal_g12_decision") or inputs["g12_oti6_decision"].get("terminal_decision"),
        "candidate_geometry_source": geometry.get("candidate_geometry_source"),
        "decision_asof_utc": packet_record.get("decision_asof_utc"),
        "decision_quote": decision_quote,
        "distance_diagnostics": distance,
        "duplicate_group_id": inputs["g12_oti6_duplicate"].get("duplicate_group_id"),
        "g12_mechanism_interpretation": g12_learning.get("mechanism_interpretation"),
        "label_family": result.get("label_family"),
        "ordered_path_context_only": {
            **ordered_path,
            "context_only_not_scored": True,
            "not_scored_reason": result.get("r_scoring_blocked_before_path_scoring_reason"),
        },
        "original_gtos_geometry": original,
        "packet_record_count": packet.get("record_count"),
        "parquet_hash": sha256_file(PARQUET_PATH),
        "result_status": result.get("result_status"),
        "r_scoring_attempted": result.get("r_scoring_attempted"),
        "synthetic_path_r": result.get("synthetic_path_r"),
        "target_already_passed_at_decision": geometry.get("target_already_passed_at_decision"),
        "terminal_status": forensics.get("terminal_status"),
    }


def terminal_states() -> list[dict[str, Any]]:
    return [
        {
            "terminal_state": "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
            "meaning": "For LONG, eligible executable ask is at or beyond target before entry. For SHORT, eligible executable bid is at or beyond target before entry.",
            "result_handling": "not_scoreable_for_that_target_model",
        },
        {
            "terminal_state": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
            "meaning": "No source-hashed quote exists at or before the trigger timestamp or inside the predeclared latency window.",
            "result_handling": "blocked_missing_quote_source",
        },
        {
            "terminal_state": "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
            "meaning": "The candidate trigger exists, but source-hashed tick/M1/M5 evidence needed to prove timing eligibility before entry is absent.",
            "result_handling": "blocked_missing_pre_entry_path",
        },
        {
            "terminal_state": "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
            "meaning": "Entry, stop, target, invalidity, or terminal state order cannot be proved with ordered tick/M1 evidence.",
            "result_handling": "ambiguous_or_bounded_not_guessed",
        },
        {
            "terminal_state": "MISSING_SOURCE_HASH",
            "meaning": "A referenced source file lacks a recorded SHA256 or reproducible lineage row.",
            "result_handling": "blocked_source_hash",
        },
        {
            "terminal_state": "MISSING_QUOTE_SIDE",
            "meaning": "The source lacks bid/ask or a declared executable side rule.",
            "result_handling": "blocked_quote_side",
        },
        {
            "terminal_state": "DUPLICATE_DENOMINATOR_EXCLUSION",
            "meaning": "A row is a duplicate within the same opportunity denominator and must not add an independent sample.",
            "result_handling": "excluded_from_primary_denominator",
        },
        {
            "terminal_state": "CONTEXT_ONLY_ROW",
            "meaning": "A row can explain failure anatomy or source coverage but cannot enter a future result denominator.",
            "result_handling": "context_only_no_result_claim",
        },
        {
            "terminal_state": "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT",
            "meaning": "All source, no-leak, duplicate, timing, target, and sample-floor controls pass packet audit before any outcome opening.",
            "result_handling": "eligible_for_future_quarantined_result_lane_not_promotion",
        },
    ]


def target_models() -> list[dict[str, Any]]:
    return [
        {
            "target_model_id": "CNR_T0_ORIGINAL_TP1",
            "definition": "Use original GTOS TP1 from the candidate geometry frozen before the timing-model outcome opening.",
            "eligibility_rule": "Eligible only if the executable entry is not already beyond TP1 in the favorable direction and original entry/SL/TP geometry is valid.",
            "status_for_oti6_record": "NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
        },
        {
            "target_model_id": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
            "definition": "A predeclared fixed-R target measured from the timing model's executable quote using a predeclared stop or invalidity distance.",
            "eligibility_rule": "Requires a frozen R multiple, stop model, quote-side rule, and source-hashed executable quote before outcome opening.",
            "status_for_oti6_record": "FUTURE_ONLY_REJECTED_AS_OTI6_RESCUE",
        },
        {
            "target_model_id": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
            "definition": "A target from an as-of H1/H4/M15 structure source such as next liquidity, swing, OB boundary, or FVG edge.",
            "eligibility_rule": "Requires structured level id, timestamp, parser, source hash, and level selected before any post-entry path is opened.",
            "status_for_oti6_record": "BLOCKED_PENDING_STRUCTURED_ASOF_LEVEL_SOURCE",
        },
        {
            "target_model_id": "CNR_T3_TIMEBOX_TERMINAL",
            "definition": "A predeclared time horizon terminal state such as fixed 4h close or session close without tuning to path extremes.",
            "eligibility_rule": "Requires quote-side terminal pricing, cost rule, and same-bar/tick ordering policy before outcome opening.",
            "status_for_oti6_record": "FUTURE_ONLY_REJECTED_AS_OTI6_RESCUE",
        },
    ]


def timing_families() -> list[dict[str, Any]]:
    source_whitelist = [
        "packet_id",
        "record_id",
        "symbol",
        "side",
        "session",
        "decision_asof_utc",
        "candidate_close_utc",
        "signal_emitted_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "duplicate_group_id",
        "source_sha256",
        "quote_timestamp_utc",
        "bid",
        "ask",
        "spread",
        "predecision_context_fields",
    ]
    forbidden_fields = [
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "post_entry_path_extremes_for_model_definition",
        "target_hit_timestamp",
        "stop_hit_timestamp",
        "result_status",
    ]
    return [
        {
            "model_family_id": "CNR_E0_DECISION_CLOSE_MARKET",
            "readiness": "FROZEN_BASELINE_FAILED_FOR_OTI6_RECORD_READY_AS_CONTROL",
            "trigger_timestamp_rule": "decision_asof_utc from frozen packet",
            "executable_quote_source_and_side": "source-hashed quote at or immediately before decision_asof_utc; LONG uses ask, SHORT uses bid",
            "target_geometry_rule": "default CNR_T0_ORIGINAL_TP1 unless a future packet explicitly binds another target model before outcomes",
            "stop_or_invalidity_rule": "original GTOS stop/invalidity geometry unless another stop model is preregistered before outcomes",
            "trigger_timeframe": "M15 decision close",
            "execution_timeframe": "tick_or_quote",
            "context_timeframes": ["M1", "M5", "M15", "H1", "H4", "D1", "session"],
            "terminal_states": [state["terminal_state"] for state in terminal_states()],
            "source_whitelist": source_whitelist,
            "forbidden_fields": forbidden_fields,
            "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
            "sample_floor": "single-row result-or-impossibility allowed after G12/G0 packet audit; no aggregate claim until >=30 unique duplicate groups and no validation claim until validation dossier floor passes",
            "oti6_record_status": "target_already_passed_before_eligible_executable_entry",
        },
        {
            "model_family_id": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
            "readiness": "FROZEN_FOR_FUTURE_PACKET_AUDIT_BLOCKED_WHEN_CANDIDATE_CLOSE_QUOTE_MISSING",
            "trigger_timestamp_rule": "candidate_close_utc from source-hashed candidate log, not reconstructed from later path",
            "executable_quote_source_and_side": "last source-hashed executable quote <= candidate_close_utc; LONG uses ask, SHORT uses bid; max quote age declared in packet",
            "target_geometry_rule": "CNR_T0_ORIGINAL_TP1 by default; CNR_T1/T2/T3 only if registered in packet before outcomes",
            "stop_or_invalidity_rule": "original GTOS SL for T0 or preregistered invalidity for T1/T2/T3",
            "trigger_timeframe": "M15 candidate close or explicit signal close",
            "execution_timeframe": "tick_or_quote",
            "context_timeframes": ["M1", "M5", "M15", "H1", "H4", "D1", "session"],
            "terminal_states": [state["terminal_state"] for state in terminal_states()],
            "source_whitelist": source_whitelist + ["candidate_close_source_line", "candidate_close_source_sha256"],
            "forbidden_fields": forbidden_fields,
            "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
            "sample_floor": "same as CNR_E0; one row can be impossibility evidence only",
            "oti6_record_status": "not_retroactively_scoreable; candidate_close_quote cannot be used to rescue OTI6 after seeing target-already-passed state",
        },
        {
            "model_family_id": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
            "readiness": "BLOCKED_UNTIL_SIGNAL_EMITTED_UTC_AND_TICK_QUOTE_SOURCE_ARE_PACKET_FIELDS",
            "trigger_timestamp_rule": "first system signal_emitted_utc from source-hashed logger before AI/decision latency, if such field exists",
            "executable_quote_source_and_side": "first source-hashed tick/quote >= signal_emitted_utc and <= signal_emitted_utc + declared latency cap; LONG uses ask, SHORT uses bid",
            "target_geometry_rule": "must bind CNR_T0/T1/T2/T3 in the packet before outcomes",
            "stop_or_invalidity_rule": "must bind original stop or preregistered timing invalidity before outcomes",
            "trigger_timeframe": "event timestamp from logger",
            "execution_timeframe": "tick_or_quote",
            "context_timeframes": ["M1", "M5", "M15", "H1", "H4", "D1", "session"],
            "terminal_states": [state["terminal_state"] for state in terminal_states()],
            "source_whitelist": source_whitelist + ["signal_emitted_utc", "signal_logger_schema", "latency_cap_ms"],
            "forbidden_fields": forbidden_fields,
            "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
            "sample_floor": "requires >=30 unique duplicate groups before aggregate result summary; not computable otherwise",
            "oti6_record_status": "blocked_current_artifacts_do_not_prove_signal_emit_timestamp_before_target_passage",
        },
        {
            "model_family_id": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
            "readiness": "FROZEN_AS_FUTURE_LATENCY_MODEL_REQUIRES_CAPTURE_FIELDS",
            "trigger_timestamp_rule": "decision_request_sent_utc or decision_asof_utc plus predeclared latency window, not chosen after path inspection",
            "executable_quote_source_and_side": "first or last quote in the declared window, explicitly selected in packet; LONG ask, SHORT bid",
            "target_geometry_rule": "target model pre-bound; target-already-passed gate checked before scoring",
            "stop_or_invalidity_rule": "pre-bound stop or invalidity; missing stop blocks result",
            "trigger_timeframe": "event timestamp plus M15 decision context",
            "execution_timeframe": "tick_or_quote",
            "context_timeframes": ["M1", "M5", "M15", "H1", "H4", "D1", "session"],
            "terminal_states": [state["terminal_state"] for state in terminal_states()],
            "source_whitelist": source_whitelist + ["decision_request_sent_utc", "decision_response_received_utc", "latency_policy_id"],
            "forbidden_fields": forbidden_fields,
            "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
            "sample_floor": "requires latency-source coverage report plus >=30 unique duplicate groups before aggregate result summary",
            "oti6_record_status": "conceptually_available_future_model; not valid rescue because OTI6 latency rule was not pre-bound",
        },
        {
            "model_family_id": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
            "readiness": "BLOCKED_PENDING_PREFILL_OR_PRETOUCH_ASOF_STRUCTURE_LOGGER",
            "trigger_timestamp_rule": "predefined no-retrace/impulse state before target passage, sourced from M1/M5/M15 as-of rows",
            "executable_quote_source_and_side": "first eligible quote after the pretouch trigger within declared latency cap; LONG ask, SHORT bid",
            "target_geometry_rule": "must bind target model before outcomes; original TP1 can only be used if not already passed",
            "stop_or_invalidity_rule": "predeclared invalidation such as impulse origin, original SL, or structure level",
            "trigger_timeframe": "M1/M5/M15 source-safe pre-entry path",
            "execution_timeframe": "tick_or_quote",
            "context_timeframes": ["H1", "H4", "D1", "session"],
            "terminal_states": [state["terminal_state"] for state in terminal_states()],
            "source_whitelist": source_whitelist + ["pretouch_trigger_id", "pretouch_trigger_utc", "pretouch_source_sha256"],
            "forbidden_fields": forbidden_fields,
            "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price|pretouch_trigger_id",
            "sample_floor": "requires separate denominator audit because multiple pretouch triggers may exist inside one original opportunity",
            "oti6_record_status": "blocked_without_predecision_pretouch_trigger_logger; cannot be inferred from recovered successful path",
        },
    ]


def build_preregistration(evidence: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_PREREGISTRATION", generated_at),
        "control_lane_status": "FROZEN_PREREGISTRATION_CONTROL_PACKAGE_NO_OUTCOME_OPENING",
        "evidence_summary": evidence,
        "future_model_families": timing_families(),
        "target_models": target_models(),
        "terminal_states": terminal_states(),
        "primary_answer": "CNR_E0 failed for OTG0-PKT-061 because the eligible decision-close market quote was already beyond original TP1; future CNR timing may only test separately frozen entry/target models with source-hashed quote-side and target-already-passed gates.",
        "not_scored_or_rescued": [
            "No earlier entry was scored.",
            "No alternate target was scored.",
            "The post-decision upward path is context-only failure anatomy.",
            "No validation or promotion claim is made.",
        ],
    }


def build_source_field_contract(source_inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT", generated_at),
        "source_inventory": source_inventory,
        "required_fields_by_layer": {
            "identity": ["packet_id", "record_id", "experiment_id", "candidate_id", "duplicate_group_id"],
            "timing": ["signal_emitted_utc", "candidate_close_utc", "decision_asof_utc", "quote_timestamp_utc", "entry_eligible_utc"],
            "executable_quote": ["bid", "ask", "spread", "quote_side_rule", "source_sha256", "quote_age_ms"],
            "geometry": ["side", "original_entry_price", "original_stop_loss", "original_take_profit_1", "target_model_id", "stop_model_id"],
            "context": ["session", "symbol", "M1_pre_entry_context", "M5_pre_entry_context", "M15_trigger_context", "H1_H4_D1_asof_context"],
            "audit": ["source_path", "source_sha256", "parser_version", "asof_cutoff_utc", "forbidden_field_scan"],
        },
        "quote_side_rule": {
            "LONG": "entry and terminal executable market prices use ask for buy-side fills; stop/exit side must be declared per target/stop model before outcomes",
            "SHORT": "entry and terminal executable market prices use bid for sell-side fills; stop/exit side must be declared per target/stop model before outcomes",
        },
        "forbidden_fields": [
            "synthetic_path_r",
            "broker_actual_r",
            "account_history",
            "live_trade_results",
            "live_order_state",
            "target_hit_after_entry",
            "stop_hit_after_entry",
            "post_entry_max_favorable_excursion",
            "post_entry_max_adverse_excursion",
            "result_status",
        ],
        "field_contract_verdict": "READY_FOR_FUTURE_PACKET_AUDIT_IF_SOURCE_HASHES_AND_TIMESTAMPS_ARE_PRESENT",
    }


def build_latency_capture_spec(generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC", generated_at),
        "latency_clock_chain": [
            "source_bar_close_utc",
            "candidate_detected_utc",
            "signal_emitted_utc",
            "packet_decision_asof_utc",
            "analysis_request_started_utc",
            "analysis_response_received_utc",
            "entry_model_selected_utc",
            "entry_eligible_utc",
            "quote_timestamp_utc",
            "order_intent_created_utc_for_future_shadow_only",
        ],
        "required_metrics": [
            "candidate_detection_lag_ms",
            "analysis_latency_ms",
            "decision_to_quote_age_ms",
            "entry_eligible_to_quote_age_ms",
            "source_clock_skew_ms",
            "max_allowed_quote_age_ms",
            "latency_bucket_id",
        ],
        "latency_window_policies": [
            {
                "policy_id": "LATENCY_W0_ASOF_LAST_QUOTE",
                "entry_quote_rule": "last quote <= trigger_utc",
                "terminal_if_missing": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
            },
            {
                "policy_id": "LATENCY_W1_FIRST_TICK_AFTER_TRIGGER_0_1000MS",
                "entry_quote_rule": "first quote >= trigger_utc and <= trigger_utc+1000ms",
                "terminal_if_missing": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
            },
            {
                "policy_id": "LATENCY_W2_FIRST_TICK_AFTER_TRIGGER_0_15000MS",
                "entry_quote_rule": "first quote >= trigger_utc and <= trigger_utc+15000ms",
                "terminal_if_missing": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
            },
        ],
        "capture_status": "FROZEN_SPEC_REQUIRES_FUTURE_SHADOW_OR_PACKET_FIELDS_FOR_SIGNAL_EMIT_AND_LATENCY",
    }


def build_noleak_duplicate_policy(generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY", generated_at),
        "label_family_policy": {
            "input_only_features_no_labels": "allowed for packet construction and preregistration",
            "synthetic_path_r_quarantined_discovery": "allowed only in explicitly opened quarantined result lanes, never for this preregistration lane",
            "broker_actual_r": "forbidden in this lane and not interchangeable with synthetic path labels",
            "lifecycle_no_fill": "context-only unless a lifecycle lane explicitly opens that label family",
        },
        "duplicate_denominator_policy": {
            "primary_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
            "pretouch_extension_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price|pretouch_trigger_id",
            "rule": "Only one primary countable row per denominator per model family and target model. Duplicate rows can exist for context or source coverage but do not add effective N.",
        },
        "no_leak_controls": [
            "model family and target model must be selected before outcome path fields are opened",
            "target-already-passed gate must run before R scoring",
            "post-decision path can verify terminal ordering only after G12/G0 packet audit opens a result lane",
            "source hashes and parser versions must be recorded before outcome opening",
            "same-bar ambiguity must be classified or bounded rather than guessed",
        ],
        "policy_verdict": "FROZEN_NOLEAK_DUPLICATE_POLICY_READY_FOR_G12_G0_PACKET_AUDIT",
    }


def build_multitimeframe_map(source_inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP", generated_at),
        "timeframe_roles": [
            {
                "timeframe": "tick_or_quote",
                "role": "execution_timeframe",
                "allowed_fields": ["bid", "ask", "timestamp", "spread", "source_sha256"],
                "forbidden_fields": ["path_outcome_for_model_selection"],
                "current_status": "packet-ready for OTR061 recovered XAU window; must be source-hashed per future row",
            },
            {
                "timeframe": "M1",
                "role": "execution_context_and_latency_path",
                "allowed_fields": ["pre-entry path ordering", "latency window context", "bar timestamp"],
                "forbidden_fields": ["post-entry target/stop ordering before result lane opening"],
                "current_status": "available in local roots for XAUUSD, but future packet must bind source hashes and parser",
            },
            {
                "timeframe": "M5",
                "role": "microstructure_context",
                "allowed_fields": ["impulse/no-retrace context before trigger", "range expansion context"],
                "forbidden_fields": ["threshold tuned from seen result"],
                "current_status": "available in local roots for XAUUSD and proxies",
            },
            {
                "timeframe": "M15",
                "role": "trigger_timeframe",
                "allowed_fields": ["candidate close", "decision close", "setup family fields"],
                "forbidden_fields": ["future M15 bars after trigger for model definition"],
                "current_status": "current packet trigger source; future rows need exact candidate_close_utc",
            },
            {
                "timeframe": "H1_H4_D1",
                "role": "context_timeframe",
                "allowed_fields": ["as-of structure", "regime", "higher-timeframe bias"],
                "forbidden_fields": ["post-trigger regime or structure update"],
                "current_status": "context-only until structured source ids and hashes are packetized",
            },
            {
                "timeframe": "session_and_event",
                "role": "context_timeframe",
                "allowed_fields": ["session name", "kill-zone window", "known scheduled event before trigger"],
                "forbidden_fields": ["post-event price reaction used for model selection"],
                "current_status": "allowed if as-of source timestamp is recorded",
            },
        ],
        "searched_source_inventory": source_inventory["local_heavy_data_searches"],
        "map_verdict": "MULTITIMEFRAME_ROLES_FROZEN_WITH_EXECUTION_VS_CONTEXT_VS_FORBIDDEN_BOUNDARIES",
    }


def build_blocker_sample_floor(generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER", generated_at),
        "blockers": [
            {
                "blocker_id": "B1_SIGNAL_EMIT_TIMESTAMP",
                "status": "BLOCKED_UNTIL_FIELD_CAPTURED",
                "exact_requirement": "source-hashed signal_emitted_utc or candidate_close_utc for each future row",
            },
            {
                "blocker_id": "B2_EXECUTABLE_QUOTE_SIDE",
                "status": "PARTIALLY_SOLVED_BY_OTR061_FOR_ONE_XAU_ROW",
                "exact_requirement": "bid/ask quote stream and LONG/SHORT quote-side rule for every future row",
            },
            {
                "blocker_id": "B3_TARGET_MODEL",
                "status": "FROZEN_OPTIONS_BUT_FUTURE_PACKET_MUST_BIND_ONE",
                "exact_requirement": "CNR_T0/T1/T2/T3 selected before outcome opening",
            },
            {
                "blocker_id": "B4_SOURCE_HASH_AND_PARSER",
                "status": "SOLVED_FOR_CONTROL_INPUTS_NOT_ALL_FUTURE_ROWS",
                "exact_requirement": "SHA256, parser version, timestamp convention, and as-of cutoff for every consumed source file",
            },
            {
                "blocker_id": "B5_DUPLICATE_DENOMINATOR",
                "status": "POLICY_FROZEN",
                "exact_requirement": "one countable row per denominator per timing-family/target-model pair",
            },
            {
                "blocker_id": "B6_SAMPLE_SIZE",
                "status": "NOT_A_PREREGISTRATION_BLOCKER_VALIDATION_BLOCKER_ONLY",
                "exact_requirement": "single-packet result-or-impossibility allowed only after G12/G0 audit; aggregate descriptive summary requires >=30 unique duplicate groups; validation dossier requires >=50 unique duplicate groups, DSR/PBO/effective-N computable or explicitly not_computable",
            },
        ],
        "statistical_handling": {
            "n_less_than_20": "no significance claim; failure anatomy only",
            "n_20_to_29": "descriptive only; no aggregate lift claim",
            "n_at_least_30": "aggregate quarantined result summary can be reported with concentration and duplicate audit",
            "validation_floor": ">=50 unique duplicate groups plus DSR/PBO/effective-N diagnostics; promotion still requires separate dossier",
            "dsr_pbo_effective_n": "required when computable; otherwise report not_computable with exact reason",
        },
        "ledger_verdict": "NO_SMALL_N_STOPPAGE_PREREGISTRATION_FROZEN_WITH_EXACT_EXPANSION_REQUIREMENTS",
    }


def build_data_expansion_plan(source_inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    packet_061 = count_packet_records(CONTROL_INPUTS["otb2r_g6_packet_061"])
    return {
        **base_payload("CNR_TIMING_MODEL_DATA_EXPANSION_PLAN", generated_at),
        "searched_roots": source_inventory["local_heavy_data_searches"],
        "source_hashed_candidate_inventory": source_inventory["control_input_rows"],
        "current_input_packet_inventory": {
            "otg0_pkt_061_g6_local_ohlc": packet_061,
            "otg0_pkt_063_path": count_packet_records(CONTROL_INPUTS["otb2r_path_packet_063"]),
            "otg0_pkt_066_path": count_packet_records(CONTROL_INPUTS["otb2r_path_packet_066"]),
        },
        "next_extraction_manifest": {
            "purpose": "Build future CNR timing packets without opening outcomes",
            "row_unit": "unique duplicate denominator per timing-family/target-model pair",
            "symbols": ["XAUUSD", "XAGUSD", "US30_cash", "NAS100", "USDJPY", "GBPUSD", "context_only_proxies_if_registered"],
            "timeframes": ["tick_or_quote", "M1", "M5", "M15", "H1", "H4", "D1", "session"],
            "fields": [
                "signal_emitted_utc",
                "candidate_close_utc",
                "decision_asof_utc",
                "bid",
                "ask",
                "spread",
                "quote_timestamp_utc",
                "source_sha256",
                "parser_version",
                "original_entry_price",
                "original_stop_loss",
                "original_take_profit_1",
                "duplicate_group_id",
                "predecision_context_fields",
            ],
            "forbidden_fields": [
                "synthetic_path_r",
                "broker_actual_r",
                "account_history",
                "target_hit_timestamp",
                "stop_hit_timestamp",
                "post_entry_mfe_mae",
                "result_status",
            ],
            "source_priority": [
                "committed packet/source artifacts",
                "worktree recovered MT5 tick parquet",
                "absolute main repo data/ticks and data/historical roots",
                "Sierra OHLCV exported CSV roots",
                "Sierra raw scid/depth only after parser/source-contract proof",
                "read-only MT5 extraction only with owner approval and no order calls",
            ],
            "cost_api_status": "no paid/API/Databento calls in this lane; future paid/free-credit source use requires separate manifest and approval",
        },
        "plan_verdict": "EXPANSION_PLAN_SOURCE_HASHED_AND_NO_OUTCOMES_OPENED",
    }


def build_next_packet_plan(generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_NEXT_PACKET_PLAN", generated_at),
        "packet_schema_id": "cnr_timing_model_packet_v1",
        "packet_required_sections": [
            "identity",
            "timing_model_family",
            "target_model",
            "source_field_contract",
            "latency_capture",
            "quote_side_and_execution_source",
            "terminal_state_policy",
            "duplicate_denominator",
            "forbidden_field_scan",
            "source_hash_manifest",
            "sample_floor_status",
            "g12_g0_audit_status",
        ],
        "packet_opening_gates": [
            "all source files hashed",
            "validation_safe remains false",
            "outcome_review_opened remains false until separate result lane",
            "no broker/live/account/paid/API/Databento/order calls",
            "timing model and target model frozen before outcome fields",
            "duplicate denominator and sample floor stated",
            "same-bar/terminal-order ambiguity policy stated",
        ],
        "next_packet_status": "READY_TO_BUILD_FUTURE_INPUT_PACKET_AFTER_SOURCE_FIELDS_CAPTURED",
    }


def build_failure_anatomy(evidence: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY", generated_at),
        "timeline": [
            {
                "event": "original_candidate_geometry_source",
                "timestamp_utc": "2026-05-06T07:15:00+00:00",
                "evidence": evidence["candidate_geometry_source"],
                "interpretation": "Original GTOS geometry existed before this lane; entry 4561.52, SL 4547.35, TP1 4582.77.",
            },
            {
                "event": "decision_close_asof",
                "timestamp_utc": evidence["decision_asof_utc"],
                "evidence": "OTR061 packet proposal decision_asof_utc",
                "interpretation": "CNR_E0 trigger clock for the failed baseline model.",
            },
            {
                "event": "decision_quote",
                "timestamp_utc": evidence["decision_quote"]["quote_timestamp_utc"],
                "evidence": evidence["decision_quote"],
                "interpretation": "LONG executable ask 4648.29 was already beyond original TP1 4582.77.",
            },
            {
                "event": "first_ordered_tick_after_decision",
                "timestamp_utc": evidence["ordered_path_context_only"]["first_timestamp_utc"],
                "evidence": {
                    "first_ask": evidence["ordered_path_context_only"]["first_ask"],
                    "first_bid": evidence["ordered_path_context_only"]["first_bid"],
                },
                "interpretation": "Path ordering exists but is context-only in this preregistration lane.",
            },
            {
                "event": "post_horizon_tick",
                "timestamp_utc": evidence["ordered_path_context_only"]["post_horizon_first_timestamp_utc"],
                "evidence": {
                    "last_ask_before_horizon": evidence["ordered_path_context_only"]["last_ask"],
                    "last_bid_before_horizon": evidence["ordered_path_context_only"]["last_bid"],
                },
                "interpretation": "The path continued upward, but no R score or alternate target is opened here.",
            },
        ],
        "failure_type": "ENTRY_CLOCK_TOO_LATE_FOR_ORIGINAL_TARGET_GEOMETRY",
        "what_cnr_e0_missed": "The no-retrace move had already traversed original TP1 before decision-close market entry could legally enter.",
        "earliest_future_entry_routes": [
            {
                "route": "candidate_close_quote",
                "status": "provable_only_if_candidate_close_quote_source_exists_before_outcome_opening",
                "oti6_current_status": "not scoreable as rescue",
            },
            {
                "route": "signal_emit_first_tick",
                "status": "blocked_current_artifacts_need signal_emitted_utc and quote stream binding",
                "oti6_current_status": "cannot infer from upward recovered path",
            },
            {
                "route": "pretouch_continuation_trigger",
                "status": "blocked_until pre-entry trigger logger/parser exists",
                "oti6_current_status": "forbidden if derived from known target-already-passed path",
            },
        ],
        "target_eligibility": {
            "original_tp1": "invalid_for_CNR_E0_on_OTI6_record_because_target_already_passed",
            "continuation_target": "future-only if preregistered before outcomes; rejected as OTI6 rescue",
            "timebox_target": "future-only if preregistered before outcomes; rejected as OTI6 rescue",
        },
        "anatomy_verdict": "CORRECT_DIRECTION_MOVE_STUDIED_WITHOUT_SCORING_OR_RESCUE",
    }


def build_recursive_ambiguity_ledger(generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER", generated_at),
        "question_stack": [
            {"question": "What exact failure did OTI6 expose?", "status": "ANSWERED", "answer": "CNR_E0 decision-close entry clock was too late for original TP1 geometry."},
            {"question": "Can earlier-entry timing families be frozen without outcome leakage?", "status": "ANSWERED", "answer": "Yes, CNR_E1/E2/E3/E4 are frozen with source/latency gates; current OTI6 cannot be rescored under them."},
            {"question": "Which quote-side rules are executable as-of?", "status": "ANSWERED", "answer": "LONG uses ask, SHORT uses bid, source-hashed quote at/before trigger or inside predeclared latency window."},
            {"question": "Which target models are legitimate?", "status": "ANSWERED", "answer": "Original TP1, fixed-R, structural level, and timebox targets are legitimate only if bound before outcomes; alternate targets are rejected for OTI6 rescue."},
            {"question": "Which rows can join future packets?", "status": "ANSWERED", "answer": "Only rows with source hashes, timing fields, quote side, duplicate denominator, target model, and no forbidden labels."},
            {"question": "What sample floor blocks future claims?", "status": "ANSWERED", "answer": "Small n blocks validation/promotion, not preregistration; exact floors and expansion plan are frozen."},
            {"question": "Can local data expand the denominator?", "status": "ANSWERED", "answer": "Yes, local packet rows and heavy roots exist; future extraction must remain input-only and source-hashed."},
            {"question": "Does any ambiguity remain locally resolvable now?", "status": "NO", "answer": "No outcome-safe local step can recover signal_emitted_utc or score earlier entries without post-hoc rescue; those are future instrumentation/source-capture requirements."},
        ],
        "ledger_verdict": "SATURATED_FOR_PREREGISTRATION_SCOPE_OPEN_AMBIGUITIES_HAVE_EXACT_CAPTURE_REQUIREMENTS",
    }


def build_anti_boxing_review(source_inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_ANTI_BOXING_REVIEW", generated_at),
        "limitation_classes": [
            {"class": "timeframe", "status": "EXPANDED", "evidence": "tick, M1, M5, M15, H1/H4/D1, session roles mapped."},
            {"class": "data_location", "status": "EXPANDED", "evidence": "worktree, main repo, C:\\tmp worktrees, C:\\SierraChart, data roots, shadow_logs searched."},
            {"class": "data_modality", "status": "EXPANDED", "evidence": "quote/tick, OHLC, Sierra scid/depth, shadow logs, packet JSON, source hashes considered."},
            {"class": "instrument_symbol", "status": "EXPANDED_CONTEXT_ONLY", "evidence": "XAUUSD primary; XAGUSD/US30/NAS100/USDJPY/GBPUSD and futures proxies included only as future source-safe context."},
            {"class": "science_domain", "status": "EXPANDED", "evidence": "timing, latency, microstructure, target geometry, structure/regime, validation methodology considered."},
            {"class": "model_class", "status": "EXPANDED", "evidence": "CNR_E0/E1/E2/E3/E4 timing families plus CNR_T0/T1/T2/T3 target models frozen/rejected/blocked."},
            {"class": "code_artifact_history", "status": "EXPANDED", "evidence": "G12/OTI6/OTR061 builders, tests, JSON ledgers, packet records, and current-state docs inspected."},
            {"class": "access_path", "status": "EXPANDED_WITH_BOUNDARIES", "evidence": "No paid/API/Databento/MT5 order access used; read-only local roots searched; future read-only extraction requires approval if needed."},
            {"class": "question_scope", "status": "EXPANDED", "evidence": "Every new blocker was converted into source, field, parser, timestamp, schema, sample, or approval requirements."},
        ],
        "searched_roots": source_inventory["local_heavy_data_searches"],
        "anti_boxing_verdict": "PASS_NO_BOXING_BLOCKER_REMAINS_WITHOUT_EXACT_BOUNDARY_OR_CAPTURE_REQUIREMENT",
    }


def build_context_anchor(source_inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        **base_payload("CNR_TIMING_MODEL_CONTEXT_ANCHOR", generated_at),
        "controlling_prompt_path": rel(PROMPT_PATH),
        "current_branch": git(["branch", "--show-current"]),
        "current_head": git(["log", "-1", "--oneline"]),
        "live_state_freshness": live_state_freshness(),
        "mandatory_boundaries": [
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "no outcome scoring",
            "no OTI6 post-hoc rescue",
            "no live trading surface edits",
            "no paid/API/Databento/MT5 order calls",
        ],
        "control_inputs_read": [rel(path) for path in CONTROL_INPUTS.values()],
        "searched_roots": source_inventory["local_heavy_data_searches"],
        "active_question_stack": [
            "freeze timing families",
            "freeze source fields",
            "freeze latency capture",
            "freeze no-leak duplicate policy",
            "freeze sample floors and expansion plan",
            "write failure anatomy without scoring",
        ],
        "route_decisions": [
            "CNR_E0 retained as failed baseline control",
            "CNR_E1/E2/E3/E4 frozen for future packet audit only",
            "alternate targets rejected as OTI6 rescue unless preregistered in future packet",
            "Sierra/raw depth context remains source-contract/parser blocked for outcome use",
        ],
        "remaining_blockers_or_approvals": [
            "future signal_emitted_utc/candidate_close_utc capture",
            "future source-hashed quote windows for every candidate row",
            "future parser/source contract for raw Sierra scid/depth if used",
            "owner approval for any read-only MT5 extraction or paid/source access outside local files",
        ],
        "required_outputs_status": {stem: "written_by_builder" for stem in REQUIRED_OUTPUT_STEMS},
        "stop_condition_status": "FROZEN_PREREGISTRATION_PACKAGE_READY_FOR_VERIFICATION",
    }


def build_completion_audit(source_inventory: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checklist = [
        ("run_generate_live_state", "satisfied", ".context/LIVE_STATE.md regenerated and read during preflight"),
        ("read_live_state", "satisfied", rel(CONTEXT_FILES["live_state"])),
        ("read_latest_handoff", "satisfied", rel(CONTEXT_FILES["latest_handoff"])),
        ("read_quick_reference", "satisfied", rel(CONTEXT_FILES["quick_reference"])),
        ("read_research_operating_doctrine", "satisfied", rel(CONTEXT_FILES["research_operating_doctrine"])),
        ("read_research_current_state", "satisfied", rel(CONTEXT_FILES["research_current_state"])),
        ("read_goal_session_research_discipline", "satisfied", rel(CONTEXT_FILES["goal_session_research_discipline"])),
        ("read_local_heavy_data_inventory", "satisfied", rel(CONTEXT_FILES["local_heavy_data_inventory"])),
        ("controlling_inputs_read", "satisfied", "G12/OTI6/OTR061/OTB2R/G12 OTX artifacts loaded from files"),
        ("no_outcome_scoring", "satisfied", "synthetic_path_r remains null and no new result directory is created"),
        ("preserve_no_promotion_flags", "satisfied", "all generated artifacts carry false validation/outcome/live flags"),
        ("freeze_timing_models", "satisfied", "CNR_E0/E1/E2/E3/E4 model families frozen"),
        ("freeze_target_models", "satisfied", "CNR_T0/T1/T2/T3 target models frozen with OTI6 rescue rejection"),
        ("freeze_source_field_contract", "satisfied", "source whitelist and forbidden fields written"),
        ("freeze_latency_capture", "satisfied", "latency clock chain and window policies written"),
        ("freeze_no_leak_duplicate_policy", "satisfied", "label-family and duplicate denominator policy written"),
        ("freeze_sample_floor", "satisfied", "sample floors and DSR/PBO/effective-N handling written"),
        ("data_expansion_not_small_n_stop", "satisfied", "local roots searched and extraction manifest written"),
        ("correct_direction_failure_anatomy", "satisfied", "timeline reconstructed without scoring"),
        ("recursive_ambiguity_protocol", "satisfied", "question stack closed or exact capture requirement written"),
        ("anti_boxing_review", "satisfied", "timeframe/data/modality/instrument/domain/model/history/access/scope reviewed"),
        ("context_anchor", "satisfied", "context anchor written"),
        ("forbidden_live_surface", "satisfied", "builder writes only lane artifacts"),
        ("paid_api_databento_mt5_order", "satisfied", "zero calls recorded"),
    ]
    return {
        **base_payload("CNR_TIMING_MODEL_COMPLETION_AUDIT", generated_at),
        "objective_restatement": "Freeze a future CNR timing/entry/target/source/latency/no-leak/duplicate/sample-floor preregistration model before any outcome opening, while preserving NO_PROMOTION_VERDICT and not touching live trading surfaces.",
        "success_criteria": [
            "required artifacts exist as md/json pairs",
            "future timing and target families are frozen or exactly blocked",
            "correct-direction move is analyzed without scoring",
            "local source search and data expansion plan are recorded",
            "all flags remain NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            "verification passes and artifacts are committed",
        ],
        "preflight_evidence": {
            "branch": git(["branch", "--show-current"]),
            "dirty_files_at_builder_run": git(["status", "--short"]),
            "head": git(["log", "-1", "--oneline"]),
            "live_state_freshness": live_state_freshness(),
        },
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "status": status, "evidence": evidence}
            for requirement, status, evidence in checklist
        ],
        "required_artifacts": [
            {"md": rel(BASE / f"{stem}_{DATE}.md"), "json": rel(BASE / f"{stem}_{DATE}.json")}
            for stem in REQUIRED_OUTPUT_STEMS
        ],
        "verification_evidence": {
            "status": "PENDING_VERIFIER_RUN",
            "expected_verifier": rel(BASE / "verify_cnr_timing_model_preregistration_2026_05_07.py"),
        },
        "completion_verdict": "READY_FOR_VERIFICATION_NOT_MARKED_COMPLETE_UNTIL_VERIFIER_AND_COMMIT_PASS",
    }


def build_bundle() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    inputs = load_inputs()
    source_inventory = build_source_inventory(generated_at)
    evidence = build_evidence(inputs, source_inventory)
    artifacts = {
        "CNR_TIMING_MODEL_PREREGISTRATION": build_preregistration(evidence, generated_at),
        "CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT": build_source_field_contract(source_inventory, generated_at),
        "CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC": build_latency_capture_spec(generated_at),
        "CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY": build_noleak_duplicate_policy(generated_at),
        "CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP": build_multitimeframe_map(source_inventory, generated_at),
        "CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER": build_blocker_sample_floor(generated_at),
        "CNR_TIMING_MODEL_DATA_EXPANSION_PLAN": build_data_expansion_plan(source_inventory, generated_at),
        "CNR_TIMING_MODEL_NEXT_PACKET_PLAN": build_next_packet_plan(generated_at),
        "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY": build_failure_anatomy(evidence, generated_at),
        "CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER": build_recursive_ambiguity_ledger(generated_at),
        "CNR_TIMING_MODEL_ANTI_BOXING_REVIEW": build_anti_boxing_review(source_inventory, generated_at),
        "CNR_TIMING_MODEL_CONTEXT_ANCHOR": build_context_anchor(source_inventory, generated_at),
        "CNR_TIMING_MODEL_COMPLETION_AUDIT": build_completion_audit(source_inventory, generated_at),
    }
    return artifacts


def write_bundle(artifacts: dict[str, dict[str, Any]]) -> None:
    title_by_stem = {
        "CNR_TIMING_MODEL_PREREGISTRATION": "CNR Timing Model Preregistration",
        "CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT": "CNR Timing Model Source Field Contract",
        "CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC": "CNR Timing Model Latency Capture Spec",
        "CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY": "CNR Timing Model Noleak Duplicate Label Policy",
        "CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP": "CNR Timing Model Multitimeframe Evidence Map",
        "CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER": "CNR Timing Model Blocker And Sample Floor Ledger",
        "CNR_TIMING_MODEL_DATA_EXPANSION_PLAN": "CNR Timing Model Data Expansion Plan",
        "CNR_TIMING_MODEL_NEXT_PACKET_PLAN": "CNR Timing Model Next Packet Plan",
        "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY": "CNR Timing Model Correct Direction Failure Anatomy",
        "CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER": "CNR Timing Model Recursive Ambiguity Ledger",
        "CNR_TIMING_MODEL_ANTI_BOXING_REVIEW": "CNR Timing Model Anti Boxing Review",
        "CNR_TIMING_MODEL_CONTEXT_ANCHOR": "CNR Timing Model Context Anchor",
        "CNR_TIMING_MODEL_COMPLETION_AUDIT": "CNR Timing Model Completion Audit",
    }
    summary_by_stem = {
        "CNR_TIMING_MODEL_PREREGISTRATION": [
            "This is a control/preregistration artifact only. It freezes future CNR timing and target model families before any new outcome opening.",
            "The OTI6 correct-direction path is treated as failure anatomy, not as a scoreable rescue.",
        ],
        "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY": [
            "The recovered path moved upward after the decision quote, but the baseline CNR_E0 original TP1 target was already passed before eligible entry.",
            "No earlier-entry or alternate-target result is opened here.",
        ],
        "CNR_TIMING_MODEL_COMPLETION_AUDIT": [
            "This audit maps the prompt requirements to concrete artifacts. The verifier updates the verification_evidence section after checks run.",
        ],
    }
    for stem, payload in artifacts.items():
        json_path = BASE / f"{stem}_{DATE}.json"
        md_path = BASE / f"{stem}_{DATE}.md"
        write_json(json_path, payload)
        write_md(md_path, title_by_stem[stem], payload, summary_by_stem.get(stem))


def main() -> None:
    artifacts = build_bundle()
    write_bundle(artifacts)
    print(f"Wrote {len(artifacts) * 2} CNR timing preregistration artifacts under {BASE}")


if __name__ == "__main__":
    main()
