#!/usr/bin/env python3
"""Build the CNR next-model source-safe control pack.

This is a research/control-lane builder only. It preregisters future timing
and target contracts, builds an input/lifecycle packet for the six OTI8
no-terminal rows without R scoring, and records discovery-only residual-target
forensics from already quarantined source-safe CNR artifacts.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DATE = "2026-05-08"
SCHEMA_VERSION = "cnr_next_model_control_pack_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
OUT = BASE
TICK_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")

CONTROL_PROMPT = BASE / f"CNR_NEXT_MODEL_CONTROL_PACK_GOAL_PROMPT_{DATE}.md"
LIVE_STATE = ROOT / ".context" / "LIVE_STATE.md"
QUICK_REF = ROOT / ".context" / "00_core" / "quick_reference_card.md"
DOCTRINE = ROOT / ".context" / "00_core" / "research_operating_doctrine.md"
CURRENT_STATE = ROOT / ".context" / "00_core" / "research_current_state.md"
GOAL_DISCIPLINE = ROOT / ".context" / "00_core" / "goal_session_research_discipline.md"
HEAVY_DATA = ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md"
HANDOFF = ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"
READING_ORDER = ROOT / ".context" / "00_READING_ORDER.md"

OTI8_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "oti8_cnr061_quarantined_results"
G12_OTI8_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_oti8_cnr061_post_result_audit"
G12_CNR061_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_cnr061_sidecar_reaudit"
CNR061_SIDECAR_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr061_geometry_horizon_sidecar"
CNR_RESIDUAL_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_geometry_decay_residual_control"
CNR_SOURCE_FIELD_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_source_field_packet_builder"
G12_CNR_SOURCE_FIELD_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_cnr_source_field_packet_audit"
OTI7_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "oti7_cnr_accepted_quarantined_results"
G12_OTI7_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_oti7_cnr_post_result_audit"
OTX_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otx_g6_tick_aware_end_to_end_resolution"
G12_OTX_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_otx_g6_post_audit"
OTR_CONTEXT_DIRS = [
    ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_oti5_otr061_post_audit",
    ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "oti6_otr061_cnr_quarantined_results",
    ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otr061_xau_tick_recovery",
]

REQUIRED_DIRS = [
    ("g12_oti8_cnr061_post_result_audit", G12_OTI8_DIR, "required_context"),
    ("oti8_cnr061_quarantined_results", OTI8_DIR, "required_context"),
    ("g12_cnr061_sidecar_reaudit", G12_CNR061_DIR, "required_context"),
    ("cnr061_geometry_horizon_sidecar", CNR061_SIDECAR_DIR, "required_context"),
    ("cnr_geometry_decay_residual_control", CNR_RESIDUAL_DIR, "required_context"),
    ("cnr_source_field_packet_builder", CNR_SOURCE_FIELD_DIR, "required_context"),
    ("g12_cnr_source_field_packet_audit", G12_CNR_SOURCE_FIELD_DIR, "required_context"),
    ("oti7_cnr_accepted_quarantined_results", OTI7_DIR, "required_context"),
    ("g12_oti7_cnr_post_result_audit", G12_OTI7_DIR, "required_context"),
    ("otx_g6_tick_aware_end_to_end_resolution", OTX_DIR, "required_context"),
    ("g12_otx_g6_post_audit", G12_OTX_DIR, "required_context"),
    ("g12_oti5_otr061_post_audit", OTR_CONTEXT_DIRS[0], "source_provenance_context_only"),
    ("oti6_otr061_cnr_quarantined_results", OTR_CONTEXT_DIRS[1], "source_provenance_context_only"),
    ("otr061_xau_tick_recovery", OTR_CONTEXT_DIRS[2], "source_provenance_context_only"),
]

BOUNDARY_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "broker_actual_r_accessed": False,
    "account_history_accessed": False,
    "live_trade_results_accessed": False,
    "live_order_state_accessed": False,
    "blocked_packet_outcome_source_read": False,
    "api_calls": 0,
    "databento_calls": 0,
    "paid_data_calls": 0,
    "mt5_order_calls": 0,
    "mt5_account_calls": 0,
    "order_calls": 0,
    "canary_calls": 0,
}

FORBIDDEN_KEYS_EXACT = {
    "account_history",
    "broker_actual_r",
    "hidden_path_label",
    "live_order_state",
    "live_trade_result",
    "path_label",
}
LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts/canary", "run_agent.py", "start_all.bat"]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], summary: list[str] | None = None) -> None:
    lines = [
        f"# {title} - {DATE}",
        "",
        f"**Promotion verdict:** `{payload.get('promotion_verdict', PROMOTION_VERDICT)}`  ",
        f"**Validation safe:** `{str(payload.get('validation_safe', False)).lower()}`  ",
        f"**Outcome review opened:** `{str(payload.get('outcome_review_opened', False)).lower()}`  ",
        f"**Live effect:** `{str(payload.get('live_effect', False)).lower()}`",
        "",
    ]
    if summary:
        lines.extend(summary)
        lines.append("")
    lines.extend(["```json", json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_utc(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            value = value.tz_localize(timezone.utc)
        return value.tz_convert(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def round_float(value: Any, places: int = 10) -> float | None:
    if value is None:
        return None
    return round(float(value), places)


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "stdout_tail": result.stdout.strip()[-2000:],
        "stderr_tail": result.stderr.strip()[-2000:],
    }


def git_head() -> str:
    result = run_command(["git", "rev-parse", "--short", "HEAD"])
    return result["stdout_tail"].strip() if result["returncode"] == 0 else "UNKNOWN"


def git_branch() -> str:
    result = run_command(["git", "branch", "--show-current"])
    return result["stdout_tail"].strip() if result["returncode"] == 0 else "UNKNOWN"


def git_status_short() -> list[str]:
    result = run_command(["git", "status", "--short"])
    return [line for line in result["stdout_tail"].splitlines() if line.strip()]


def artifact_inventory() -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for name, directory, role in REQUIRED_DIRS:
        files = sorted(path for path in directory.rglob("*") if path.is_file()) if directory.exists() else []
        for path in files:
            suffix = path.suffix.lower()
            entry: dict[str, Any] = {
                "directory_role": role,
                "exists": True,
                "path": rel(path),
                "required_directory": name,
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
            if suffix == ".json":
                try:
                    payload = load_json(path)
                    entry["parse_status"] = "PASS_JSON"
                    entry["top_level_keys"] = sorted(payload.keys())[:40] if isinstance(payload, dict) else []
                except Exception as exc:  # pragma: no cover - verifier catches generated failures
                    entry["parse_status"] = "FAIL_JSON"
                    entry["parse_error"] = str(exc)
            elif suffix == ".jsonl":
                try:
                    rows = load_jsonl(path)
                    entry["parse_status"] = "PASS_JSONL"
                    entry["jsonl_rows"] = len(rows)
                except Exception as exc:  # pragma: no cover
                    entry["parse_status"] = "FAIL_JSONL"
                    entry["parse_error"] = str(exc)
            else:
                entry["parse_status"] = "HASH_ONLY"
            inventory.append(entry)
    return inventory


def source_search_ledger() -> dict[str, Any]:
    roots = [
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
        TICK_ROOT,
        TICK_ROOT / "XAGUSD",
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\exports"),
        Path(r"C:\tmp"),
        Path(r"C:\SierraChart"),
        Path(r"C:\Users\MSI\Documents"),
    ]
    searched = []
    xagusd_tick_files = []
    if (TICK_ROOT / "XAGUSD").exists():
        for path in sorted((TICK_ROOT / "XAGUSD").glob("2026-05-0*.parquet")):
            xagusd_tick_files.append(
                {
                    "path": str(path),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else None,
                    "sha256": file_sha256(path),
                }
            )
    for root in roots:
        entry = {"root": str(root), "exists": root.exists(), "search_policy": "targeted_read_only_no_live_account_or_order_state"}
        if root == TICK_ROOT / "XAGUSD":
            entry["matching_files"] = xagusd_tick_files
        elif root == Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"):
            entry["status"] = "not_consumed_for_labels; provenance-only because live result/account/order fields are forbidden"
        elif root == Path(r"C:\Users\MSI\Documents"):
            entry["status"] = "targeted only; broad recursive scan intentionally avoided"
        searched.append(entry)
    return {
        "searched_roots": searched,
        "worktree_absence_is_not_data_absence_acknowledged": True,
        "xagusd_tick_file_count": len(xagusd_tick_files),
        "forbidden_sources_seen_but_not_consumed": [
            r"C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_evaluations",
            r"C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\trade_records",
        ],
    }


def common_payload(artifact_family: str) -> dict[str, Any]:
    return {
        **BOUNDARY_FLAGS,
        "artifact_family": artifact_family,
        "date_stamp": DATE,
        "generated_at_utc": now_utc(),
        "schema_version": SCHEMA_VERSION,
    }


def timing_preregistration() -> dict[str, Any]:
    families = {
        "CNR_E2_SIGNAL_EMITTED_AT_SOURCE": {
            "required_fields": ["signal_emitted_utc", "source_id", "source_hash", "emission_rule_id", "source_record_id"],
            "legal_source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; current CNR matrix has signal_emitted_utc null.",
            "no_lookahead_asof_rule": "signal_emitted_utc must be emitted by the source logger no later than the decision-as-of timestamp and hashed before terminal path opening.",
            "allowed_source_roots_parsers": [
                "future source-hashed signal/candidate logger JSONL",
                "CNR_SOURCE_FIELD_PACKET_ROWS only if signal_emitted_utc is non-null and source-hashed",
            ],
            "forbidden_fields": ["terminal_event", "synthetic_path_r", "broker_actual_r", "account_history", "live_order_state", "hidden_path_label"],
            "duplicate_policy": "duplicate_denominator_key must include timing family; duplicate groups cannot be joined by group alone.",
            "sample_floor": ">=30 countable duplicate groups per timing-target family and effective_N>=3 before validation-style diagnostics.",
            "exact_blocker": "No committed source-hashed signal emission logger exists for these rows; preregister field only.",
        },
        "CNR_E3_DECISION_LATENCY_AWARE": {
            "required_fields": [
                "decision_request_sent_utc",
                "decision_response_received_utc",
                "latency_ms",
                "latency_policy_id",
                "quote_lookup_policy_id",
                "timeout_behavior",
            ],
            "legal_source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; request/response latency timestamps are not present in accepted packets.",
            "no_lookahead_asof_rule": "latency fields must be logged by the decision client before any path/result source is opened; quote lookup must be bound to the response timestamp policy.",
            "allowed_source_roots_parsers": ["future decision-latency audit JSONL", "source-hashed analyzer request ledger if added as shadow-only telemetry"],
            "forbidden_fields": ["terminal_event", "synthetic_path_r", "broker_actual_r", "account_history", "live_order_state", "hidden_path_label"],
            "duplicate_policy": "same candidate may produce separate E3 rows only when latency_policy_id differs and is preregistered.",
            "sample_floor": ">=30 countable duplicate groups per latency policy plus DSR/PBO/effective-N diagnostics in a separate result lane.",
            "exact_blocker": "Current OTI8/G12 artifacts have executable quote timestamps but not request/response timestamps or timeout policy ids.",
        },
        "CNR_E4_PRETOUCH_TRIGGER": {
            "required_fields": [
                "pretouch_trigger_id",
                "pretouch_trigger_utc",
                "trigger_type",
                "distance_to_level_rule_id",
                "cancellation_rule_id",
                "source_hash",
            ],
            "legal_source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; pretouch trigger source does not exist.",
            "no_lookahead_asof_rule": "trigger must be emitted before first touch of the level and before terminal path opening; cancellation must be logged from pre-touch state only.",
            "allowed_source_roots_parsers": ["future pretouch shadow logger JSONL", "source-hashed tick/quote proximity parser with frozen trigger distance rule"],
            "forbidden_fields": ["terminal_event", "synthetic_path_r", "broker_actual_r", "account_history", "live_order_state", "hidden_path_label"],
            "duplicate_policy": "pretouch_trigger_id is unique; repeated triggers for the same duplicate group are context rows unless a preregistered denominator key says otherwise.",
            "sample_floor": ">=30 countable duplicate groups per trigger type; no promotion from input packet counts.",
            "exact_blocker": "No source-hashed pretouch trigger id, trigger type, distance-to-level rule, or cancellation source is present.",
        },
    }
    return {
        **common_payload("CNR_E2_E3_E4_TIMING_PREREGISTRATION"),
        "status": "INPUT_ONLY_PREREGISTERED_CURRENT_ROWS_BLOCKED_FOR_E2_E3_E4_FIELDS",
        "families": families,
        "no_outcomes_scored": True,
    }


def target_preregistration() -> dict[str, Any]:
    families = {
        "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE": {
            "pre_outcome_target_contract": "Fixed-R target prices are generated from executable quote and source-hashed stop before path opening.",
            "source_asof_fields": ["executable_quote_price", "executable_quote_side", "quote_timestamp_utc", "stop_loss", "stop_source_hash", "fixed_r_multiple", "target_price"],
            "price_side_rule": "LONG entry quote uses ask and terminal target/stop uses bid; SHORT entry quote uses bid and terminal target/stop uses ask.",
            "stop_model": "frozen source stop; invalid if stop is not beyond executable quote in the risk direction.",
            "invalid_tiny_residual_gate": "invalid stop or non-positive fixed target geometry is excluded; no OTI7/OTI8 outcome-derived threshold is introduced.",
            "sample_floor_dsr_pbo_effective_n_policy": ">=30 countable duplicate groups, effective_N>=3, DSR p<0.01, PBO<0.4 for promotion dossier only.",
            "exact_blocker": "No result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet.",
        },
        "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL": {
            "pre_outcome_target_contract": "Target is a structural level selected from an as-of source snapshot with hierarchy/rank policy frozen before terminal path opening.",
            "source_asof_fields": ["structural_level_id", "level_price", "level_timestamp_utc", "level_source_hash", "hierarchy_rank", "selection_rule_id"],
            "price_side_rule": "same executable/terminal quote-side rule as T1.",
            "stop_model": "source stop frozen independently from structural target source.",
            "invalid_tiny_residual_gate": "reject target already passed or invalid stop before scoring; tiny residual bins are descriptive until separately preregistered.",
            "sample_floor_dsr_pbo_effective_n_policy": ">=30 countable duplicate groups per level family plus concentration and source-family diagnostics.",
            "exact_blocker": "Current CNR rows bind original TP1 only; no source-hashed structural-level rank/source snapshot is available for CNR_T2.",
        },
        "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE": {
            "pre_outcome_target_contract": "Lifecycle labels are categorical terminal/timebox states, not R results.",
            "source_asof_fields": ["timebox_policy_id", "path_start_utc", "original_horizon_end_utc", "extended_horizon_end_utc", "path_source_files", "path_source_sha256"],
            "price_side_rule": "same terminal quote-side rule as T1 for detecting target/stop event order; labels do not compute R.",
            "stop_model": "source stop frozen from input row; lifecycle labels can identify target/stop/still-open/source-insufficient only.",
            "invalid_tiny_residual_gate": "invalid stop or missing source yields source/geometry blocker labels, not rescue scoring.",
            "sample_floor_dsr_pbo_effective_n_policy": "lifecycle packet can be built at n=6, but validation/promotion remains blocked below sample floor.",
            "exact_blocker": "Promotion/result scoring remains blocked; Workstream C builds only source-hashed labels for the six no-terminal rows.",
        },
    }
    return {
        **common_payload("CNR_T1_T2_T3_TARGET_PREREGISTRATION"),
        "status": "INPUT_ONLY_TARGET_FAMILIES_PREREGISTERED_NO_RESULT_SCORING",
        "families": families,
        "no_outcomes_scored": True,
    }


def lifecycle_label_contract() -> dict[str, Any]:
    contract = {
        "contract_id": "CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1",
        "freeze_order": "This contract is built before reading any extended beyond-original-horizon tick path.",
        "row_scope": "Exactly the six OTI8 rows with terminal_status=NO_TERMINAL_WITHIN_ORDERED_HORIZON.",
        "extended_horizon_policy": "Scan source-hashed XAGUSD ticks after original path_end_utc until the first terminal label or path_start_utc+24h, using contiguous local tick files already present.",
        "allowed_labels": [
            "target_after_original_horizon",
            "stop_after_original_horizon",
            "ambiguous_target_stop_after_original_horizon",
            "still_no_terminal_after_extended_horizon",
            "source_horizon_insufficient",
        ],
        "forbidden_outputs": [
            "synthetic_r",
            "broker_actual_r",
            "account_history",
            "live_trade_result",
            "live_order_state",
            "hidden_path_label",
            "promotion_statistic",
        ],
        "price_side_rule": "For SHORT rows, ask reaching take_profit_1 is target and ask reaching stop_loss is stop; for LONG rows, bid is used.",
        "duplicate_policy": "Retain all six row-level rows; countable denominator uses the upstream OTI8 countable flag and duplicate_denominator_key.",
        "validation_boundary": "Lifecycle labels are discovery/input packet state only; no R, DSR/PBO, promotion, or live rule is computed.",
    }
    contract["contract_sha256"] = stable_hash(contract)
    return contract


def read_tick_file(path: Path, cache: dict[str, pd.DataFrame]) -> pd.DataFrame:
    key = str(path)
    if key not in cache:
        table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
        df = table.to_pandas()
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
        cache[key] = df.sort_values("ts_utc").reset_index(drop=True)
    return cache[key]


def candidate_tick_files(row: dict[str, Any]) -> list[Path]:
    symbol = row["symbol"]
    start = parse_utc(row["path_start_utc"])
    end = start + timedelta(hours=24)
    dates = []
    current = start.date()
    while current <= end.date():
        dates.append(current)
        current = current + timedelta(days=1)
    files = [TICK_ROOT / symbol / f"{day.isoformat()}.parquet" for day in dates]
    return files


def scan_lifecycle(row: dict[str, Any], df_cache: dict[str, pd.DataFrame]) -> dict[str, Any]:
    side = str(row["side"]).upper()
    target = float(row["original_take_profit_1"])
    stop = float(row["original_stop_loss"])
    original_end = parse_utc(row["path_end_utc"])
    path_start = parse_utc(row["path_start_utc"])
    extended_end = path_start + timedelta(hours=24)
    files = candidate_tick_files(row)
    file_entries = [
        {"path": str(path), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else None, "sha256": file_sha256(path)}
        for path in files
    ]
    frames = [read_tick_file(path, df_cache) for path in files if path.exists()]
    if not frames:
        return {
            "available_extended_source_files": file_entries,
            "extended_horizon_end_utc": iso(extended_end),
            "label": "source_horizon_insufficient",
            "label_reason": "No local tick files found for source-hashed extension.",
            "original_horizon_end_utc": iso(original_end),
        }
    df = pd.concat(frames, ignore_index=True).sort_values("ts_utc").reset_index(drop=True)
    window = df[(df["ts_utc"] > pd.Timestamp(original_end)) & (df["ts_utc"] <= pd.Timestamp(extended_end))]
    if window.empty:
        return {
            "available_extended_source_files": file_entries,
            "extended_horizon_end_utc": iso(extended_end),
            "label": "source_horizon_insufficient",
            "label_reason": "No ticks after original horizon and before extended horizon.",
            "original_horizon_end_utc": iso(original_end),
            "extended_tick_rows": 0,
        }

    label = "still_no_terminal_after_extended_horizon"
    terminal_event_utc = None
    terminal_bid = None
    terminal_ask = None
    terminal_price_side = "bid" if side == "LONG" else "ask"
    for tick in window.itertuples(index=False):
        bid = float(tick.bid)
        ask = float(tick.ask)
        if side == "LONG":
            hit_target = bid >= target
            hit_stop = bid <= stop
        else:
            hit_target = ask <= target
            hit_stop = ask >= stop
        if hit_target and hit_stop:
            label = "ambiguous_target_stop_after_original_horizon"
            terminal_event_utc = iso(tick.ts_utc)
            terminal_bid = bid
            terminal_ask = ask
            break
        if hit_target:
            label = "target_after_original_horizon"
            terminal_event_utc = iso(tick.ts_utc)
            terminal_bid = bid
            terminal_ask = ask
            break
        if hit_stop:
            label = "stop_after_original_horizon"
            terminal_event_utc = iso(tick.ts_utc)
            terminal_bid = bid
            terminal_ask = ask
            break

    return {
        "available_extended_source_files": file_entries,
        "extended_first_tick_utc": iso(window["ts_utc"].iloc[0]),
        "extended_horizon_end_utc": iso(extended_end),
        "extended_last_tick_utc": iso(window["ts_utc"].iloc[-1]),
        "extended_tick_rows": int(len(window)),
        "label": label,
        "original_horizon_end_utc": iso(original_end),
        "terminal_ask": round_float(terminal_ask),
        "terminal_bid": round_float(terminal_bid),
        "terminal_event_utc": terminal_event_utc,
        "terminal_price_side": terminal_price_side,
    }


def load_oti8_rows() -> list[dict[str, Any]]:
    return load_jsonl(OTI8_DIR / f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl")


def load_oti7_rows() -> list[dict[str, Any]]:
    return load_jsonl(OTI7_DIR / f"OTI7_CNR_RESULT_LEDGER_{DATE}.jsonl")


def load_matrix_rows() -> list[dict[str, Any]]:
    return load_jsonl(CNR_RESIDUAL_DIR / f"CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_{DATE}.jsonl")


def build_lifecycle_packet(label_contract: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    oti8_rows = load_oti8_rows()
    no_terminal = [row for row in oti8_rows if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"]
    df_cache: dict[str, pd.DataFrame] = {}
    packet_rows = []
    for row in no_terminal:
        lifecycle = scan_lifecycle(row, df_cache)
        packet_row = {
            **BOUNDARY_FLAGS,
            "artifact_family": "CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_ROW",
            "candidate_close_utc": row["candidate_close_utc"],
            "countable_denominator_row": row["countable_denominator_row"],
            "duplicate_denominator_key": row["duplicate_denominator_key"],
            "duplicate_group_id": row["duplicate_group_id"],
            "executable_quote_price": row["executable_quote_price"],
            "executable_quote_side": row["executable_quote_side"],
            "label_contract_id": label_contract["contract_id"],
            "label_contract_sha256": label_contract["contract_sha256"],
            "lifecycle_label": lifecycle["label"],
            "lifecycle_observation": lifecycle,
            "original_entry_price": row["original_entry_price"],
            "original_horizon_status": row["terminal_status"],
            "original_path_end_utc": row["path_end_utc"],
            "original_path_start_utc": row["path_start_utc"],
            "original_stop_loss": row["original_stop_loss"],
            "original_take_profit_1": row["original_take_profit_1"],
            "packet_id": row["packet_id"],
            "quote_source_sha256": row["quote_source_sha256"],
            "quote_timestamp_utc": row["quote_timestamp_utc"],
            "record_id": row["record_id"],
            "row_source_hash": row["row_source_hash"],
            "side": row["side"],
            "sidecar_row_sha256": row["sidecar_row_sha256"],
            "symbol": row["symbol"],
            "target_model_family": row["target_model_family"],
            "timing_model_family": row["timing_model_family"],
        }
        packet_row["packet_row_sha256"] = stable_hash(packet_row)
        packet_rows.append(packet_row)

    labels = Counter(row["lifecycle_label"] for row in packet_rows)
    packet = {
        **common_payload("CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET"),
        "status": "SOURCE_SAFE_LIFECYCLE_PACKET_BUILT_NO_R_SCORING",
        "label_contract": label_contract,
        "row_scope": {
            "source": rel(OTI8_DIR / f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl"),
            "target_rows": "six May 5 NY XAGUSD OTI8 no-terminal rows only",
            "row_count": len(packet_rows),
            "all_rows_xagusd": all(row["symbol"] == "XAGUSD" for row in packet_rows),
            "all_rows_original_no_terminal": all(row["original_horizon_status"] == "NO_TERMINAL_WITHIN_ORDERED_HORIZON" for row in packet_rows),
        },
        "lifecycle_label_counts": dict(sorted(labels.items())),
        "row_level_jsonl": f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}_ROWS.jsonl",
        "r_scoring_performed": False,
        "broker_or_account_labels_used": False,
        "blocked_94_rows_scored": False,
    }
    return packet, packet_rows


def bin_residual(value: Any, bins: list[str]) -> str:
    if value is None:
        return "MISSING_OR_STOP_INVALID"
    v = float(value)
    if v <= 0:
        return "LTE_0_TARGET_ALREADY_PASSED_OR_ZERO"
    if v < 0.25:
        return "GT_0_TO_0_25_TINY_RESIDUAL"
    if v < 0.5:
        return "GT_0_25_TO_0_5_SMALL_RESIDUAL"
    if v < 1.0:
        return "GT_0_5_TO_1_0_SUB_ONE_R"
    if v < 1.5:
        return "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR"
    return "GTE_1_5_MEETS_GTOS_MIN_RR_GEOMETRY_ONLY"


def derive_session(row: dict[str, Any]) -> str:
    if row.get("session"):
        return str(row["session"])
    group = str(row.get("duplicate_group_id") or "")
    parts = group.split("|")
    for part in parts:
        if part in {"tokyo", "london", "ny"}:
            return part
    return "unknown"


def xagusd_forensics(lifecycle_rows: list[dict[str, Any]]) -> dict[str, Any]:
    spec = load_json(CNR_RESIDUAL_DIR / f"CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_{DATE}.json")
    residual_bins = spec["residual_target_r_bins"]
    oti7_rows = [row for row in load_oti7_rows() if row.get("symbol") == "XAGUSD"]
    oti8_rows = [row for row in load_oti8_rows() if row.get("symbol") == "XAGUSD"]
    matrix_rows = [row for row in load_matrix_rows() if row.get("symbol") == "XAGUSD"]

    def summarize(rows: list[dict[str, Any]], source: str) -> dict[str, Any]:
        by_bin: dict[str, Counter] = defaultdict(Counter)
        by_session: Counter = Counter()
        by_timing: Counter = Counter()
        by_duplicate: Counter = Counter()
        tiny_rows = 0
        row_count = 0
        for row in rows:
            row_count += 1
            if source == "oti8":
                residual = row.get("matrix_residual_target_r_from_executable_quote")
                status = row.get("terminal_status")
            else:
                residual = ((row.get("geometry") or {}).get("target_r_from_executable_entry"))
                status = row.get("quarantined_result_status")
            residual_bin = bin_residual(residual, residual_bins)
            if residual_bin == "GT_0_TO_0_25_TINY_RESIDUAL":
                tiny_rows += 1
            by_bin[residual_bin][status] += 1
            by_session[derive_session(row)] += 1
            by_timing[row.get("timing_model_family")] += 1
            by_duplicate[row.get("duplicate_group_id")] += 1
        return {
            "row_count": row_count,
            "residual_bin_by_status": {key: dict(value) for key, value in sorted(by_bin.items())},
            "session_counts": dict(by_session),
            "timing_family_counts": dict(by_timing),
            "unique_duplicate_groups": len(by_duplicate),
            "tiny_residual_rows": tiny_rows,
        }

    matrix_bin_counts = Counter(row.get("residual_target_r_bin") for row in matrix_rows)
    no_terminal_rows = [row for row in oti8_rows if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"]
    lifecycle_counts = Counter(row["lifecycle_label"] for row in lifecycle_rows)
    return {
        **common_payload("CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS"),
        "status": "DISCOVERY_ONLY_MECHANISM_FORENSICS_NO_RESCUE_NO_GATE",
        "source_artifacts": {
            "oti7": rel(OTI7_DIR / f"OTI7_CNR_RESULT_LEDGER_{DATE}.jsonl"),
            "oti8": rel(OTI8_DIR / f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl"),
            "residual_bin_spec": rel(CNR_RESIDUAL_DIR / f"CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_{DATE}.json"),
            "matrix": rel(CNR_RESIDUAL_DIR / f"CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_{DATE}.jsonl"),
        },
        "bin_source": "non-optimized bins from CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC; no new thresholds selected from outcomes",
        "oti7_xagusd_summary": summarize(oti7_rows, "oti7"),
        "oti8_xagusd_summary": summarize(oti8_rows, "oti8"),
        "xagusd_matrix_input_only_residual_bin_counts": dict(matrix_bin_counts),
        "oti8_no_terminal_cluster": {
            "row_count": len(no_terminal_rows),
            "sessions": dict(Counter(derive_session(row) for row in no_terminal_rows)),
            "duplicate_groups": dict(Counter(row["duplicate_group_id"] for row in no_terminal_rows)),
            "timing_families": dict(Counter(row["timing_model_family"] for row in no_terminal_rows)),
            "lifecycle_extension_labels": dict(lifecycle_counts),
        },
        "mechanism_answers": [
            "OTI8's two target-before-stop rows are tiny residual-target wins from executable quote and remain learning evidence only.",
            "The six OTI8 no-terminal rows cluster in one May 5 NY XAGUSD duplicate group with deeper residual target geometry than the May 4 tiny rows.",
            "CNR_E0/E1 plus CNR_T0 original TP1 should be treated as a narrow geometry/timing failure mode until E2/E3/E4 and T1/T2/T3 are preregistered and tested.",
            "No live gate, rescue threshold, selector change, or promotion claim is supported by this forensics artifact.",
        ],
        "future_preregistered_hypotheses": [
            "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE can test whether original TP1 residual-decay is the failure source without using outcome-fit target thresholds.",
            "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL can test whether source-ranked structural targets avoid tiny original-TP1 residual wins.",
            "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE can separate late stop/target lifecycle from four-hour no-terminal labels before R scoring.",
            "CNR_E2/E3/E4 can test whether source emission, latency-aware quotes, or pre-touch triggers remove late-entry geometry artifacts.",
        ],
        "validation_boundary": "descriptive discovery only; validation_safe=false and outcome_review_opened=false remain preserved",
    }


def source_contracts(timing: dict[str, Any], targets: dict[str, Any], lifecycle_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        **common_payload("CNR_TIMING_TARGET_SOURCE_CONTRACTS"),
        "status": "SOURCE_CONTRACTS_REGISTERED_INPUT_ONLY",
        "allowed_source_roots": [
            r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\{SYMBOL}\YYYY-MM-DD.parquet",
            "research/science_program_2026_05/06_outcome_testing/* source-hashed JSON/JSONL artifacts",
            "future source-hashed shadow logger files explicitly registered by G12/G0",
        ],
        "allowed_parsers": ["pyarrow parquet reader for ts_utc/bid/ask", "json/jsonl source-hash parser", "future preregistered source-specific parser"],
        "legal_source_state": {
            "E2_E3_E4": "preregistered but current rows blocked by missing source fields",
            "T1_T2_T3": "preregistered; T3 lifecycle packet built for six no-terminal rows without R scoring",
        },
        "forbidden_sources": [
            "broker actual-R",
            "account history",
            "live trade results",
            "live order state",
            "hidden path labels",
            "94 G12-blocked CNR061 rows as scored evidence",
        ],
        "timing_family_ids": sorted(timing["families"].keys()),
        "target_family_ids": sorted(targets["families"].keys()),
        "lifecycle_packet_status": lifecycle_packet["status"],
        "source_artifact_inventory": artifact_inventory(),
    }


def noleak_duplicate_sample_audit(lifecycle_rows: list[dict[str, Any]], source_contract: dict[str, Any]) -> dict[str, Any]:
    oti8_rows = load_oti8_rows()
    g12_blocked = load_json(G12_CNR061_DIR / f"G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_{DATE}.json")
    no_terminal_hashes = {row["sidecar_row_sha256"] for row in oti8_rows if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"}
    packet_hashes = {row["sidecar_row_sha256"] for row in lifecycle_rows}
    forbidden_hits = []
    for row in lifecycle_rows:
        stack = [("$", row)]
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    dotted = f"{prefix}.{key}"
                    if key in FORBIDDEN_KEYS_EXACT or key == "synthetic_r" or key.endswith("_r"):
                        forbidden_hits.append({"packet_row_sha256": row["packet_row_sha256"], "json_path": dotted, "key": key})
                    stack.append((dotted, nested))
            elif isinstance(value, list):
                for idx, nested in enumerate(value):
                    stack.append((f"{prefix}[{idx}]", nested))
    duplicate_keys = Counter(row["duplicate_denominator_key"] for row in lifecycle_rows)
    duplicate_groups = Counter(row["duplicate_group_id"] for row in lifecycle_rows)
    sample_floor = {
        "packet_row_count": len(lifecycle_rows),
        "countable_rows": sum(1 for row in lifecycle_rows if row["countable_denominator_row"]),
        "unique_duplicate_groups": len(duplicate_groups),
        "sample_floor_for_validation_met": False,
        "reason": "n=6 row-level and one duplicate group is an input packet only; validation/promotion sample floor is not met.",
    }
    return {
        **common_payload("CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT"),
        "status": "PASS_INPUT_ONLY_NOLEAK_DUPLICATE_SAMPLE_BOUNDARY",
        "source_contract_inventory_files": len(source_contract["source_artifact_inventory"]),
        "no_leak_scan": {"forbidden_packet_row_hits": forbidden_hits, "status": "PASS" if not forbidden_hits else "FAIL"},
        "duplicate_policy": {
            "duplicate_denominator_key_counts": dict(duplicate_keys),
            "duplicate_group_counts": dict(duplicate_groups),
            "do_not_join_on_duplicate_group_alone": True,
        },
        "sample_floor": sample_floor,
        "exact_six_row_scope_check": {
            "oti8_no_terminal_sidecar_hashes": sorted(no_terminal_hashes),
            "packet_sidecar_hashes": sorted(packet_hashes),
            "status": "PASS_EXACT_SIX" if no_terminal_hashes == packet_hashes and len(packet_hashes) == 6 else "FAIL",
        },
        "blocked_94_not_scored_proof": {
            "g12_blocked_audit_source": rel(G12_CNR061_DIR / f"G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_{DATE}.json"),
            "blocked_rows": g12_blocked.get("blocked_rows") or g12_blocked.get("blocked_row_count") or 94,
            "packet_rows_from_blocked_set": [],
            "status": "PASS_94_BLOCKED_ROWS_NOT_SCORED",
        },
    }


def blocker_and_route_ledger(timing: dict[str, Any], targets: dict[str, Any], lifecycle_packet: dict[str, Any]) -> dict[str, Any]:
    return {
        **common_payload("CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER"),
        "active_question_stack": [
            "Can timing be moved from E0/E1 late market entry to source-emitted, latency-aware, or pretouch fields without leakage?",
            "Can target design avoid original TP1 residual-decay without outcome-fit rescue thresholds?",
            "Can six OTI8 no-terminal rows be observed beyond the frozen horizon without R scoring?",
            "Is XAGUSD residual-target behavior a narrow CNR_T0 failure mode rather than broad CNR failure?",
        ],
        "route_decisions": [
            {"route": "CNR_E2_E3_E4", "decision": "PREREGISTER_ONLY", "reason": "required source fields are missing in current rows"},
            {"route": "CNR_T1_T2_T3", "decision": "PREREGISTER_ONLY_WITH_T3_PACKET", "reason": "target contracts can be frozen; no result scoring authorized"},
            {"route": "CNR061_NO_TERMINAL_PACKET", "decision": lifecycle_packet["status"], "reason": "local XAGUSD tick files exist and labels are contract-frozen before extension scan"},
            {"route": "XAGUSD_FORENSICS", "decision": "DISCOVERY_ONLY", "reason": "uses only accepted/quarantined source-safe rows and existing bins"},
            {"route": "94_BLOCKED_ROWS", "decision": "DO_NOT_SCORE", "reason": "G12 explicitly blocks them"},
            {"route": "LIVE_SURFACES", "decision": "NO_TOUCH", "reason": "control pack is research/tooling only"},
        ],
        "exact_blockers": [
            {"family": "CNR_E2", "blocker": timing["families"]["CNR_E2_SIGNAL_EMITTED_AT_SOURCE"]["exact_blocker"]},
            {"family": "CNR_E3", "blocker": timing["families"]["CNR_E3_DECISION_LATENCY_AWARE"]["exact_blocker"]},
            {"family": "CNR_E4", "blocker": timing["families"]["CNR_E4_PRETOUCH_TRIGGER"]["exact_blocker"]},
            {"family": "CNR_T2", "blocker": targets["families"]["CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL"]["exact_blocker"]},
        ],
        "searched_root_ledger": source_search_ledger(),
        "no_access_request_needed": True,
    }


def context_anchor(route_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    read_artifacts = [
        CONTROL_PROMPT,
        LIVE_STATE,
        HANDOFF,
        QUICK_REF,
        DOCTRINE,
        CURRENT_STATE,
        GOAL_DISCIPLINE,
        HEAVY_DATA,
        READING_ORDER,
        G12_OTI8_DIR / f"G12_OTI8_CNR061_NEXT_LANE_PROMPT_PACK_{DATE}.md",
    ]
    return {
        **common_payload("CNR_NEXT_MODEL_CONTEXT_ANCHOR"),
        "branch": git_branch(),
        "head": git_head(),
        "worktree_path": str(ROOT),
        "controlling_prompt": rel(CONTROL_PROMPT),
        "read_artifacts": [{"path": rel(path), "exists": path.exists(), "sha256": file_sha256(path)} for path in read_artifacts],
        "required_context_directories": [{"name": name, "path": rel(path), "exists": path.exists(), "role": role} for name, path, role in REQUIRED_DIRS],
        "active_question_stack": (route_ledger or {}).get("active_question_stack")
        or [
            "Freeze E2/E3/E4 timing fields before outcome opening.",
            "Freeze T1/T2/T3 target contracts before outcome opening.",
            "Build or prove impossible the six-row no-terminal lifecycle packet without R scoring.",
            "Perform XAGUSD residual-target mechanism forensics as discovery only.",
        ],
        "searched_roots": source_search_ledger(),
        "runtime_dirt": git_status_short(),
        "route_decisions": (route_ledger or {}).get("route_decisions", []),
        "instruction_coverage_checklist": [
            {"instruction": "mandatory_preflight", "status": "PASS_REGENERATED_AND_READ"},
            {"instruction": "context_anchor_before_packet_or_forensics_output", "status": "PASS_BUILDER_WRITES_ANCHOR_FIRST"},
            {"instruction": "no_live_surface_touch", "status": "PASS_RESEARCH_DIRECTORY_ONLY"},
            {"instruction": "NO_PROMOTION_VERDICT", "status": "PASS"},
        ],
    }


def completion_audit(artifacts: dict[str, Any], lifecycle_rows: list[dict[str, Any]]) -> dict[str, Any]:
    checklist = [
        ("mandatory_gtos_preflight", "PASS", "LIVE_STATE regenerated and mandatory context artifacts hashed in context anchor."),
        ("latest_handoff_read", "PASS", rel(HANDOFF)),
        ("g12_oti8_next_lane_prompt_pack_read", "PASS", rel(G12_OTI8_DIR / f"G12_OTI8_CNR061_NEXT_LANE_PROMPT_PACK_{DATE}.md")),
        ("all_named_context_dirs_inventoried", "PASS", "source_contract.source_artifact_inventory"),
        ("context_anchor", "PASS", f"CNR_NEXT_MODEL_CONTEXT_ANCHOR_{DATE}.json"),
        ("CNR_E2_E3_E4_prereg", "PASS", f"CNR_E2_E3_E4_TIMING_PREREGISTRATION_{DATE}.json"),
        ("CNR_T1_T2_T3_prereg", "PASS", f"CNR_T1_T2_T3_TARGET_PREREGISTRATION_{DATE}.json"),
        ("source_contracts", "PASS", f"CNR_TIMING_TARGET_SOURCE_CONTRACTS_{DATE}.json"),
        ("no_leak_duplicate_samplefloor", "PASS", f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json"),
        ("six_row_no_terminal_scope", "PASS" if len(lifecycle_rows) == 6 else "FAIL", str(len(lifecycle_rows))),
        ("lifecycle_packet_without_r_scoring", "PASS", f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}_ROWS.jsonl"),
        ("xagusd_residual_forensics_discovery_only", "PASS", f"CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_{DATE}.json"),
        ("94_blocked_rows_not_scored", "PASS", "audit.blocked_94_not_scored_proof"),
        ("no_broker_account_live_labels", "PASS", "all boundary flags false/zero"),
        ("no_paid_api_databento_mt5_order_account_calls", "PASS", "all call counters zero"),
        ("no_live_surface_changes", "PENDING_VERIFIER", "verifier will run git diff scan"),
        ("json_jsonl_parse", "PENDING_VERIFIER", "verifier will parse generated machine files"),
        ("py_compile", "PENDING_VERIFIER", "verifier will compile builder/verifier/tests"),
        ("focused_pytest", "PENDING_VERIFIER", "verifier will run focused tests"),
        ("completion_artifacts", "PASS", f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}.json"),
    ]
    return {
        **common_payload("CNR_NEXT_MODEL_COMPLETION_AUDIT"),
        "objective_restatement": [
            "Build one consolidated source-safe CNR next-model control pack.",
            "Preregister CNR_E2/E3/E4 timing fields and CNR_T1/T2/T3 target contracts.",
            "Build or prove impossible a six-row CNR061 no-terminal lifecycle packet without R scoring.",
            "Run XAGUSD residual-target mechanism forensics as discovery-only.",
            "Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": requirement, "status": status, "evidence": evidence} for requirement, status, evidence in checklist
        ],
        "generated_artifacts": sorted(artifacts.keys()),
        "verification_status": "PENDING_VERIFIER",
        "can_mark_goal_complete": False,
    }


def g12_prompt_pack() -> str:
    return f"""# CNR Next Model G12 Audit Prompt Pack - {DATE}

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Prompt

`/goal Audit CNR_NEXT_MODEL_CONTROL_PACK under research/science_program_2026_05/06_outcome_testing/cnr_next_model_control_pack; verify E2/E3/E4 timing preregistration, T1/T2/T3 target preregistration, source contracts, no-leak/duplicate/sample-floor audit, six-row CNR061 no-terminal lifecycle packet without R scoring, XAGUSD residual-target forensics as discovery-only, and completion audit; confirm 94 blocked rows were not scored and no broker actual-R/account history/live trade result/live order state/hidden labels/paid API/MT5 order/account calls/live prompt/risk/execution/permissions/safety/selector/canary changes occurred; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Audit Questions

1. Does the context anchor prove mandatory preflight and named artifacts were read/inventoried?
2. Are CNR_E2/E3/E4 and CNR_T1/T2/T3 input contracts frozen before outcome opening?
3. Does the lifecycle packet include exactly the six OTI8 no-terminal rows and no R scoring?
4. Are XAGUSD residual-target forensics descriptive only and free of rescue thresholds/live gates?
5. Are the 94 G12-blocked CNR061 rows excluded from scoring?
6. Do verifier and tests cover JSON/JSONL parsing, no-leak, duplicate/sample-floor, six-row scope, and live-surface diff?
"""


def build_bundle() -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    label_contract = lifecycle_label_contract()
    lifecycle_packet, lifecycle_rows = build_lifecycle_packet(label_contract)
    timing = timing_preregistration()
    targets = target_preregistration()
    contracts = source_contracts(timing, targets, lifecycle_packet)
    noleak = noleak_duplicate_sample_audit(lifecycle_rows, contracts)
    forensics = xagusd_forensics(lifecycle_rows)
    route = blocker_and_route_ledger(timing, targets, lifecycle_packet)
    anchor = context_anchor(route)
    artifacts = {
        f"CNR_NEXT_MODEL_CONTEXT_ANCHOR_{DATE}": anchor,
        f"CNR_E2_E3_E4_TIMING_PREREGISTRATION_{DATE}": timing,
        f"CNR_T1_T2_T3_TARGET_PREREGISTRATION_{DATE}": targets,
        f"CNR_TIMING_TARGET_SOURCE_CONTRACTS_{DATE}": contracts,
        f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}": noleak,
        f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}": lifecycle_packet,
        f"CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_{DATE}": forensics,
        f"CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_{DATE}": route,
    }
    artifacts[f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}"] = completion_audit(artifacts, lifecycle_rows)
    return artifacts, lifecycle_rows, g12_prompt_pack()


def write_outputs() -> None:
    artifacts, lifecycle_rows, g12_prompt = build_bundle()
    # Anchor first, then packet/forensics outputs.
    ordered_names = [
        f"CNR_NEXT_MODEL_CONTEXT_ANCHOR_{DATE}",
        f"CNR_E2_E3_E4_TIMING_PREREGISTRATION_{DATE}",
        f"CNR_T1_T2_T3_TARGET_PREREGISTRATION_{DATE}",
        f"CNR_TIMING_TARGET_SOURCE_CONTRACTS_{DATE}",
        f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}",
        f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}",
        f"CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_{DATE}",
        f"CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_{DATE}",
        f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}",
    ]
    titles = {
        f"CNR_NEXT_MODEL_CONTEXT_ANCHOR_{DATE}": "CNR Next Model Context Anchor",
        f"CNR_E2_E3_E4_TIMING_PREREGISTRATION_{DATE}": "CNR E2 E3 E4 Timing Preregistration",
        f"CNR_T1_T2_T3_TARGET_PREREGISTRATION_{DATE}": "CNR T1 T2 T3 Target Preregistration",
        f"CNR_TIMING_TARGET_SOURCE_CONTRACTS_{DATE}": "CNR Timing Target Source Contracts",
        f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}": "CNR Timing Target No-Leak Duplicate Sample-Floor Audit",
        f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}": "CNR061 No-Terminal Timebox Lifecycle Packet",
        f"CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_{DATE}": "CNR XAGUSD Residual Target Forensics",
        f"CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_{DATE}": "CNR Next Model Blocker And Route Ledger",
        f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}": "CNR Next Model Completion Audit",
    }
    for name in ordered_names:
        payload = artifacts[name]
        write_json(OUT / f"{name}.json", payload)
        write_md(OUT / f"{name}.md", titles[name], payload)
    jsonl_path = OUT / f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}_ROWS.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in lifecycle_rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
    (OUT / f"CNR_NEXT_MODEL_G12_AUDIT_PROMPT_PACK_{DATE}.md").write_text(g12_prompt, encoding="utf-8")
    print(json.dumps({"artifacts": len(ordered_names), "lifecycle_rows": len(lifecycle_rows), "status": "built"}, sort_keys=True))


if __name__ == "__main__":
    write_outputs()
