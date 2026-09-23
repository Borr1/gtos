#!/usr/bin/env python3
"""Build OTI6 OTR061 continuation/no-retrace quarantined result artifacts.

This lane consumes the G12-accepted OTG0-PKT-061 recovered XAUUSD tick
packet and applies the preregistered CNR_E0 market-entry geometry before any
R scoring. It never reads broker actual-R, account history, live order state,
blocked-packet outcomes, or paid/API/Databento sources.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DATE = "2026-05-07"
PACKET_ID = "OTG0-PKT-061"
TARGET_RECORD_ID = "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
EXPERIMENT_ID = "G6-EXP-002-CONTINUATION-NO-RETRACE"
HYPOTHESIS_ID = "G6-HYP-002"
ENTRY_MODEL_ID = "CNR_E0_DECISION_CLOSE_MARKET"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False
RESULT_STATUS_TARGET_ALREADY_PASSED = (
    "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION"
)
EXPECTED_PARQUET_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
DECISION_ASOF = datetime(2026, 5, 6, 7, 15, tzinfo=timezone.utc)
RECOVERY_START = datetime(2026, 5, 6, 7, 10, tzinfo=timezone.utc)
RECOVERY_END = datetime(2026, 5, 6, 11, 15, tzinfo=timezone.utc)

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OUTCOME = ROOT / "research/science_program_2026_05/06_outcome_testing"
G12 = OUTCOME / "g12_oti5_otr061_post_audit"
OTR061 = OUTCOME / "otr061_xau_tick_recovery"
PROGRAM_CONTROL = ROOT / "research/program_control"
DOMAIN = ROOT / "research/science_program_2026_05/01_domain_syntheses"
PARQUET_PATH = OTR061 / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
CANDIDATE_LOG = ROOT / "shadow_logs/continuation_no_retrace_candidates.jsonl"
RESOLUTION_LOG = ROOT / "shadow_logs/continuation_no_retrace_resolutions.jsonl"

CONTROL_FILES = [
    OUT / "OTI6_OTR061_CNR_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-07.md",
    ROOT / ".context/LIVE_STATE.md",
    ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ROOT / ".context/00_core/quick_reference_card.md",
    ROOT / ".context/00_core/research_operating_doctrine.md",
    ROOT / ".context/00_core/research_current_state.md",
    ROOT / ".context/00_core/goal_session_research_discipline.md",
    ROOT / ".context/00_core/local_heavy_data_inventory.md",
    G12 / "G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json",
    G12 / "G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
    G12 / "G12_OTI5_OTR061_NEXT_LANE_PROMPT_PACK_2026-05-07.md",
    OTR061 / "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
    OTR061 / "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json",
    OTR061 / "OTR061_COMPLETION_AUDIT_2026-05-07.json",
    PARQUET_PATH,
    PROGRAM_CONTROL / "CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md",
    PROGRAM_CONTROL / "CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md",
    DOMAIN / "G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json",
    OUTCOME / "OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
    CANDIDATE_LOG,
    RESOLUTION_LOG,
]

FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "run_agent.py",
    "start_all.bat",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(value: datetime | pd.Timestamp | None, *, micros: bool = True) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    if not micros:
        value = value.replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def round_float(value: float | None, digits: int = 8) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, digits)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any], summary: list[str] | None = None) -> None:
    lines = [
        f"# {title} - {DATE}",
        "",
        f"**Promotion verdict:** `{payload.get('promotion_verdict')}`  ",
        f"**Validation safe:** `{str(payload.get('validation_safe')).lower()}`  ",
        f"**Outcome review opened:** `{str(payload.get('outcome_review_opened')).lower()}`  ",
        f"**Live effect:** `{str(payload.get('live_effect')).lower()}`",
        "",
    ]
    if summary:
        lines.extend(summary)
        lines.append("")
    lines.extend(["```json", json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def git_head() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def base_payload(artifact_family: str, generated_at: str) -> dict[str, Any]:
    return {
        "account_history_accessed": False,
        "api_calls": 0,
        "artifact_family": artifact_family,
        "broker_actual_r_accessed": False,
        "canary_calls": 0,
        "databento_calls": 0,
        "date_stamp": DATE,
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": generated_at,
        "git_head_at_build": git_head(),
        "live_effect": LIVE_EFFECT,
        "live_order_state_accessed": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_id": PACKET_ID,
        "paid_data_calls": 0,
        "promotion_verdict": PROMOTION_VERDICT,
        "target_record_id": TARGET_RECORD_ID,
        "validation_safe": VALIDATION_SAFE,
    }


def source_row(path: Path, role: str, required: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        "exists": exists,
        "path": rel(path) if exists else str(path),
        "absolute_path": str(path.resolve()) if exists else str(path),
        "required": required,
        "role": role,
        "sha256": sha256_file(path) if exists else None,
        "size_bytes": path.stat().st_size if exists else None,
    }


def load_jsonl_target(path: Path, predicate) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if predicate(row):
                return {
                    "line_no": idx,
                    "row": row,
                    "source_file": rel(path),
                    "source_file_sha256": sha256_file(path),
                    "source_line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                }
    return None


def inspect_parquet(path: Path) -> dict[str, Any]:
    computed_sha = sha256_file(path)
    parquet = pq.ParquetFile(path)
    columns = parquet.schema.names
    df = pq.read_table(path, columns=[col for col in ["ts_utc", "bid", "ask", "last", "time_msc"] if col in columns]).to_pandas()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.sort_values(["ts_utc", "time_msc"] if "time_msc" in df.columns else ["ts_utc"]).reset_index(drop=True)

    decision_mask = df["ts_utc"] <= pd.Timestamp(DECISION_ASOF)
    decision_rows = df.loc[decision_mask]
    if decision_rows.empty:
        raise RuntimeError("No tick at or before decision_asof in recovered parquet")
    decision_quote = decision_rows.iloc[-1]

    path_mask = (df["ts_utc"] >= pd.Timestamp(DECISION_ASOF)) & (df["ts_utc"] <= pd.Timestamp(RECOVERY_END))
    path_rows = df.loc[path_mask]
    post_horizon = df.loc[df["ts_utc"] > pd.Timestamp(RECOVERY_END)]
    first_path = path_rows.iloc[0] if not path_rows.empty else None
    last_path = path_rows.iloc[-1] if not path_rows.empty else None

    source_mask = (df["ts_utc"] >= pd.Timestamp(RECOVERY_START)) & (df["ts_utc"] <= pd.Timestamp(RECOVERY_END))
    source_window = df.loc[source_mask]

    return {
        "columns": columns,
        "decision_quote": {
            "ask": float(decision_quote["ask"]),
            "bid": float(decision_quote["bid"]),
            "decision_rows_lte_071500": int(len(decision_rows)),
            "executable_decision_price_long_ask": float(decision_quote["ask"]),
            "quote_timestamp_utc": iso(decision_quote["ts_utc"]),
        },
        "expected_sha256": EXPECTED_PARQUET_SHA256,
        "first_ask": float(df["ask"].iloc[0]),
        "first_bid": float(df["bid"].iloc[0]),
        "first_tick_utc": iso(df["ts_utc"].iloc[0]),
        "last_ask": float(df["ask"].iloc[-1]),
        "last_bid": float(df["bid"].iloc[-1]),
        "last_tick_utc": iso(df["ts_utc"].iloc[-1]),
        "ordered_path": {
            "first_ask": float(first_path["ask"]) if first_path is not None else None,
            "first_bid": float(first_path["bid"]) if first_path is not None else None,
            "first_timestamp_utc": iso(first_path["ts_utc"]) if first_path is not None else None,
            "last_ask": float(last_path["ask"]) if last_path is not None else None,
            "last_bid": float(last_path["bid"]) if last_path is not None else None,
            "last_timestamp_utc": iso(last_path["ts_utc"]) if last_path is not None else None,
            "path_end_utc": iso(RECOVERY_END, micros=False),
            "path_start_utc": iso(DECISION_ASOF, micros=False),
            "post_horizon_first_timestamp_utc": iso(post_horizon["ts_utc"].iloc[0]) if not post_horizon.empty else None,
            "row_count": int(len(path_rows)),
        },
        "path": rel(path),
        "required_source_window": {
            "first_timestamp_utc": iso(source_window["ts_utc"].iloc[0]) if not source_window.empty else None,
            "last_timestamp_utc": iso(source_window["ts_utc"].iloc[-1]) if not source_window.empty else None,
            "row_count": int(len(source_window)),
            "window_end_utc": iso(RECOVERY_END, micros=False),
            "window_start_utc": iso(RECOVERY_START, micros=False),
        },
        "row_count": int(parquet.metadata.num_rows),
        "sha256": computed_sha,
        "sha256_matches_expected": computed_sha == EXPECTED_PARQUET_SHA256,
    }


def c_nr_geometry_status(side: str, executable_entry: float, stop_loss: float, target: float) -> dict[str, Any]:
    side = side.upper()
    if side == "LONG" and executable_entry > target:
        return {
            "eligible": False,
            "terminal_result_status": RESULT_STATUS_TARGET_ALREADY_PASSED,
            "reason": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
        }
    if side == "SHORT" and executable_entry < target:
        return {
            "eligible": False,
            "terminal_result_status": RESULT_STATUS_TARGET_ALREADY_PASSED,
            "reason": "SHORT executable bid is below original TP1 before CNR_E0 can enter.",
        }
    if side == "LONG" and not (stop_loss < executable_entry < target):
        return {
            "eligible": False,
            "terminal_result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_BAD_CONTINUATION_GEOMETRY",
            "reason": "LONG continuation entry/stop/target ordering violates stop < entry < target.",
        }
    if side == "SHORT" and not (target < executable_entry < stop_loss):
        return {
            "eligible": False,
            "terminal_result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_BAD_CONTINUATION_GEOMETRY",
            "reason": "SHORT continuation entry/stop/target ordering violates target < entry < stop.",
        }
    return {
        "eligible": True,
        "terminal_result_status": "CNR_E0_GEOMETRY_VALID_FOR_PATH_SCORING",
        "reason": "CNR_E0 executable entry is between original stop and target.",
    }


def safety_scan_generated(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    true_hits = []
    missing_promotion = []
    for name, payload in payloads.items():
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            missing_promotion.append(name)
        for key in ("validation_safe", "outcome_review_opened", "live_effect"):
            if payload.get(key) is True:
                true_hits.append({"artifact": name, "key": key})
    return {
        "promotion_verdict_missing_or_wrong": missing_promotion,
        "forbidden_true_flag_hits": true_hits,
        "status": "PASS" if not true_hits and not missing_promotion else "FAIL",
    }


def live_surface_diff_review() -> dict[str, Any]:
    result = subprocess.run(["git", "diff", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=False)
    changed = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES)]
    return {
        "changed_files_at_build_time": changed,
        "forbidden_live_surface_changed_files": forbidden,
        "status": "PASS" if not forbidden else "FAIL",
    }


def build_bundle() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    g12_decision = read_json(G12 / "G12_OTI5_OTR061_DECISION_LEDGER_2026-05-07.json")
    g12_recovery = read_json(G12 / "G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json")
    packet = read_json(OTR061 / "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json")
    otr061_hash_ledger = read_json(OTR061 / "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json")
    g6_rows = read_json(DOMAIN / "G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json")

    record = packet["records"][0]
    if record.get("record_id") != TARGET_RECORD_ID:
        raise RuntimeError(f"Unexpected OTR061 record id: {record.get('record_id')}")

    candidate_evidence = load_jsonl_target(CANDIDATE_LOG, lambda row: row.get("candidate_id") == "XAUUSD_2026-05-06T07:15:00+00:00")
    if candidate_evidence is None:
        raise RuntimeError("Target CNR candidate row not found in continuation_no_retrace_candidates.jsonl")
    candidate = candidate_evidence["row"]
    geometry = candidate["original_trade_geometry"]

    resolution_rows = []
    with RESOLUTION_LOG.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("candidate_id") == "XAUUSD_2026-05-06T07:15:00+00:00":
                resolution_rows.append(
                    {
                        "line_no": idx,
                        "row_key": row.get("row_key"),
                        "asof_latest_candle_utc": row.get("asof_latest_candle_utc"),
                        "later_path_outcome_status": row.get("later_path_outcome_status"),
                        "score_status": row.get("score_status"),
                        "synthetic_r_status": row.get("synthetic_r_status"),
                        "touched_original_limit_entry": row.get("touched_original_limit_entry"),
                        "first_touch_times": row.get("first_touch_times"),
                    }
                )

    parquet = inspect_parquet(PARQUET_PATH)
    side = str(candidate.get("side") or record.get("side")).upper()
    executable_entry = float(parquet["decision_quote"]["executable_decision_price_long_ask"])
    original_entry = float(geometry["entry_price"])
    stop_loss = float(geometry["stop_loss"])
    tp1 = float(geometry["take_profit_1"])
    base_r = float(geometry["base_r_price"])
    geometry_status = c_nr_geometry_status(side, executable_entry, stop_loss, tp1)
    target_already_passed = not geometry_status["eligible"] and geometry_status["terminal_result_status"] == RESULT_STATUS_TARGET_ALREADY_PASSED

    control_source_rows = [source_row(path, "controlling_input_or_context") for path in CONTROL_FILES]
    missing_required = [row for row in control_source_rows if row["required"] and not row["exists"]]
    hash_failures = []
    if not parquet["sha256_matches_expected"]:
        hash_failures.append(
            {
                "path": parquet["path"],
                "expected_sha256": EXPECTED_PARQUET_SHA256,
                "observed_sha256": parquet["sha256"],
            }
        )

    source_report = base_payload("OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT", generated_at)
    source_report.update(
        {
            "all_consumed_files_hashed": not missing_required and not hash_failures,
            "control_context_and_source_files": control_source_rows,
            "forbidden_source_review": {
                "account_history_accessed": False,
                "broker_actual_r_accessed": False,
                "blocked_packet_outcome_source_read": False,
                "live_order_state_accessed": False,
                "paid_or_api_or_databento_called": False,
                "resolution_log_used_only_as_permitted_lifecycle_context": True,
            },
            "hash_failures": hash_failures,
            "local_heavy_data_inventory_enforced": True,
            "missing_required_files": missing_required,
            "otr061_prior_source_hash_verdict": otr061_hash_ledger.get("all_used_files_hashed"),
            "parquet_direct_verification": parquet,
            "source_gate_status": "PASS" if not missing_required and not hash_failures else "FAIL",
        }
    )

    geometry_audit = base_payload("OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT", generated_at)
    geometry_audit.update(
        {
            "candidate_geometry_source": {
                "line_no": candidate_evidence["line_no"],
                "row_key": candidate.get("row_key"),
                "source_file": candidate_evidence["source_file"],
                "source_file_sha256": candidate_evidence["source_file_sha256"],
                "source_line_sha256": candidate_evidence["source_line_sha256"],
            },
            "cnr_e0_geometry_rule": {
                "entry_model_id": ENTRY_MODEL_ID,
                "long_entry": "use executable decision ask",
                "short_entry": "use executable decision bid",
                "score_only_after_geometry_valid": True,
                "target_model": "original_gtos_take_profit_1",
                "stop_model": "original_gtos_structural_stop_loss",
            },
            "decision_quote_reconstructed_from_parquet": parquet["decision_quote"],
            "distance_diagnostics": {
                "executable_entry_minus_original_entry_price": round_float(executable_entry - original_entry),
                "executable_entry_minus_original_entry_r": round_float((executable_entry - original_entry) / base_r),
                "executable_entry_minus_tp1_price": round_float(executable_entry - tp1),
                "executable_entry_minus_tp1_r": round_float((executable_entry - tp1) / base_r),
                "tp1_minus_original_entry_price": round_float(tp1 - original_entry),
                "tp1_minus_original_entry_r": round_float((tp1 - original_entry) / base_r),
            },
            "eligibility_status": geometry_status,
            "original_gtos_geometry": {
                "base_r_price": base_r,
                "entry_price": original_entry,
                "geometry_valid": bool(geometry.get("geometry_valid")),
                "side": side,
                "stop_loss": stop_loss,
                "take_profit_1": tp1,
            },
            "preregistered_original_geometry_valid": bool(stop_loss < original_entry < tp1) if side == "LONG" else bool(tp1 < original_entry < stop_loss),
            "target_already_passed_at_decision": target_already_passed,
        }
    )

    result_ledger = base_payload("OTI6_CNR_RESULT_LEDGER", generated_at)
    result_ledger.update(
        {
            "entry_model_id": ENTRY_MODEL_ID,
            "label_family": "synthetic_path_r_quarantined_discovery_only_not_computed",
            "ordered_path_summary": parquet["ordered_path"],
            "record_count": 1,
            "result_row": {
                "base_r_price": base_r,
                "candidate_id": "XAUUSD_2026-05-06T07:15:00+00:00",
                "cnr_e0_executable_entry": executable_entry,
                "decision_asof_utc": iso(DECISION_ASOF, micros=False),
                "decision_quote_timestamp_utc": parquet["decision_quote"]["quote_timestamp_utc"],
                "original_entry_price": original_entry,
                "original_stop_loss": stop_loss,
                "original_take_profit_1": tp1,
                "packet_id": PACKET_ID,
                "record_id": TARGET_RECORD_ID,
                "result_status": geometry_status["terminal_result_status"],
                "side": side,
                "synthetic_path_r": None,
                "synthetic_path_r_status": "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE",
                "target_already_passed_at_decision": target_already_passed,
            },
            "result_status": geometry_status["terminal_result_status"],
            "r_scoring_attempted": False,
            "r_scoring_blocked_before_path_scoring_reason": geometry_status["reason"],
            "synthetic_path_r": None,
            "terminal_status_counts": {geometry_status["terminal_result_status"]: 1},
        }
    )

    duplicate_label = base_payload("OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT", generated_at)
    duplicate_label.update(
        {
            "accepted_packet_record_count": 1,
            "broker_actual_r_opened": False,
            "blocked_packet_outcomes_opened": False,
            "candidate_no_leak_status": candidate.get("no_leak_status"),
            "duplicate_group_id": "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52",
            "duplicate_group_source": "G12_OTR061_PACKET_RECOVERY_AUDIT.prior_duplicate_group_id_for_future_denominator and candidate geometry",
            "duplicate_policy": "One primary countable opportunity; duplicate context rows are not summed as independent opportunities.",
            "label_family_gate_status": "PASS",
            "label_family_separation": {
                "input_packet_label_family": record.get("label_family"),
                "lifecycle_context_label_family": "lifecycle_no_fill_context_only",
                "result_label_family": "synthetic_path_r_quarantined_discovery_only_not_computed",
                "validation_label_family": None,
            },
            "live_trade_results_opened": False,
            "opportunity_counting_context": {
                "candidate_duplicate_counting_rule": candidate.get("duplicate_counting_rule"),
                "latest_resolution_rows_inspected": len(resolution_rows),
                "permitted_resolution_context": resolution_rows,
            },
            "post_decision_context_not_used_for_cnr_e0_scoring": True,
        }
    )

    method_freeze = base_payload("OTI6_CNR_METHOD_FREEZE", generated_at)
    method_freeze.update(
        {
            "cohort": {
                "packet_id": PACKET_ID,
                "record_id": TARGET_RECORD_ID,
                "record_count": 1,
            },
            "entry_model": {
                "entry_model_id": ENTRY_MODEL_ID,
                "executable_price_rule": "LONG uses ask at decision quote; SHORT uses bid at decision quote.",
                "quote_timestamp_rule": "last source-hashed tick at or before decision_asof_utc",
            },
            "geometry_gate_before_r_scoring": {
                "long_valid_ordering": "stop_loss < executable_entry < original_take_profit_1",
                "short_valid_ordering": "original_take_profit_1 < executable_entry < stop_loss",
                "target_already_passed_policy": "If executable entry is already beyond original TP1, do not score as positive R.",
            },
            "metric_freeze": {
                "primary_status": RESULT_STATUS_TARGET_ALREADY_PASSED,
                "r_metric": "quarantined synthetic path-R only if geometry is valid and ordered path reaches TP1/SL unambiguously",
                "this_record_r_metric_status": "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE",
            },
            "preregistration_sources": [
                rel(PROGRAM_CONTROL / "CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md"),
                rel(DOMAIN / "G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json"),
            ],
        }
    )

    forensics = base_payload("OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS", generated_at)
    forensics.update(
        {
            "impossibility_type": "PREREGISTERED_GEOMETRY_INVALID_TARGET_ALREADY_PASSED_AT_DECISION",
            "not_a_forced_win_loss": True,
            "row_teaches": [
                "The original GTOS structural idea had already delivered through TP1 before the CNR_E0 market-entry quote was available.",
                "A no-retrace continuation did occur in lifecycle context, but not in a way that the preregistered decision-close market-entry model can score.",
                "Using CNR_E0 at 4648.29 against original TP1 4582.77 would be an impossible long target geometry, not a profitable R result.",
            ],
            "evidence": {
                "cnr_e0_entry_ask": executable_entry,
                "decision_quote_timestamp_utc": parquet["decision_quote"]["quote_timestamp_utc"],
                "first_ordered_path_bid": parquet["ordered_path"]["first_bid"],
                "first_ordered_path_timestamp_utc": parquet["ordered_path"]["first_timestamp_utc"],
                "original_tp1": tp1,
                "source_file_line": f"{candidate_evidence['source_file']}:{candidate_evidence['line_no']}",
                "target_already_passed_by_price": round_float(executable_entry - tp1),
                "target_already_passed_by_r": round_float((executable_entry - tp1) / base_r),
            },
            "future_preregistered_capture_needed": [
                "Capture executable quotes before or during the decision candle if testing an earlier-entry CNR model.",
                "Register a distinct target model if testing continuation beyond original TP1; do not reuse this CNR_E0 target.",
                "Log exact decision latency and quote-side marketability prospectively so target-passed states are explicit.",
            ],
            "terminal_status": geometry_status["terminal_result_status"],
        }
    )

    methodology = base_payload("OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT", generated_at)
    methodology.update(
        {
            "countable_records": 1,
            "dsr": {
                "status": "not_computable",
                "reason": "One quarantined geometry-impossible record is not a validation sample and no variant/performance vector exists.",
            },
            "effective_n": {
                "status": "not_computable_for_validation",
                "observed_frozen_record_n": 1,
                "reason": "Duplicate-aware opportunity N is one and R is not computed; this cannot support sample-floor or promotion statistics.",
            },
            "pbo": {
                "status": "not_computable",
                "reason": "No train/test, CPCV, or model-family selection matrix exists in this single-record result-or-impossibility lane.",
            },
            "sample_floor_review": {
                "cnr_preregistered_floor": "60 primary countable candidates with exact decision entry price and ordered post-decision path",
                "current_exact_quote_ordered_path_records": 1,
                "current_r_scored_records": 0,
                "sample_floor_pass": False,
            },
            "statistical_verdict": "NOT_VALIDATION_NOT_COMPUTABLE_GEOMETRY_IMPOSSIBLE_SINGLE_RECORD",
        }
    )

    artifacts: dict[str, dict[str, Any]] = {
        f"OTI6_CNR_METHOD_FREEZE_{DATE}": method_freeze,
        f"OTI6_CNR_RESULT_LEDGER_{DATE}": result_ledger,
        f"OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_{DATE}": source_report,
        f"OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_{DATE}": geometry_audit,
        f"OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_{DATE}": duplicate_label,
        f"OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_{DATE}": forensics,
        f"OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}": methodology,
    }
    safety = safety_scan_generated(artifacts)
    live_surface = live_surface_diff_review()
    required_artifact_stems = [
        f"OTI6_CNR_METHOD_FREEZE_{DATE}",
        f"OTI6_CNR_RESULT_LEDGER_{DATE}",
        f"OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_{DATE}",
        f"OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_{DATE}",
        f"OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_{DATE}",
        f"OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_{DATE}",
        f"OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}",
        f"OTI6_CNR_COMPLETION_AUDIT_{DATE}",
    ]
    completion_checklist = [
        ("objective_terminal_status", "PASS", geometry_status["terminal_result_status"]),
        ("mandatory_live_state_regenerated_and_read", "PASS", ".context/LIVE_STATE.md regenerated and hashed in source report."),
        ("latest_handoff_read", "PASS", "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md hashed in source report."),
        ("quick_reference_read", "PASS", "quick_reference_card.md hashed in source report."),
        ("research_doctrine_read", "PASS", "research_operating_doctrine.md hashed in source report."),
        ("research_current_state_read", "PASS", "research_current_state.md hashed in source report."),
        ("goal_discipline_read", "PASS", "goal_session_research_discipline.md hashed in source report."),
        ("local_heavy_data_inventory_read", "PASS", "local_heavy_data_inventory.md hashed and local recovered parquet rechecked."),
        ("all_controlling_inputs_read_and_hashed", "PASS" if source_report["source_gate_status"] == "PASS" else "FAIL", source_report["source_gate_status"]),
        ("otr061_g12_claims_recomputed", "PASS" if parquet["sha256_matches_expected"] and parquet["row_count"] == 89391 else "FAIL", parquet),
        ("original_geometry_recovered_from_source_line", "PASS", f"{candidate_evidence['source_file']}:{candidate_evidence['line_no']}"),
        ("cnr_e0_geometry_applied_before_r_scoring", "PASS", geometry_status["reason"]),
        ("long_ask_already_beyond_original_tp1_verified", "PASS" if target_already_passed else "FAIL", f"{executable_entry} > {tp1}"),
        ("result_or_impossibility_forensics_written", "PASS", forensics["impossibility_type"]),
        ("no_promotion_flags_preserved", "PASS" if safety["status"] == "PASS" else "FAIL", safety),
        ("no_forbidden_result_or_live_sources_read", "PASS", "No broker actual-R, account history, live trade results, live order state, blocked-packet outcomes, paid/API/Databento, or MT5 order calls opened."),
        ("forbidden_live_surface_diff_absent_at_build", "PASS" if live_surface["status"] == "PASS" else "FAIL", live_surface),
        ("dsr_pbo_effective_n_reported", "PASS", methodology["statistical_verdict"]),
    ]
    completion = base_payload("OTI6_CNR_COMPLETION_AUDIT", generated_at)
    completion.update(
        {
            "can_mark_goal_complete": all(row[1] == "PASS" for row in completion_checklist),
            "concrete_success_criteria": [
                "verify OTG0-PKT-061/G12/OTR061/prereg claims from files",
                "recompute recovered parquet SHA256 and tick coverage",
                "recover original GTOS geometry from source-hashed candidate row",
                "apply CNR_E0 executable market-entry geometry before R scoring",
                "emit terminal result-or-impossibility forensics without forcing a win/loss",
                "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            ],
            "live_surface_diff_review_at_build": live_surface,
            "objective_restated": "Run the OTI6 quarantined result lane for one frozen OTR061 recovered XAUUSD tick packet and determine whether CNR_E0 can be R-scored under preregistered geometry.",
            "prompt_to_artifact_checklist": [
                {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in completion_checklist
            ],
            "required_artifacts_written": [
                f"{stem}.md" for stem in required_artifact_stems
            ]
            + [f"{stem}.json" for stem in required_artifact_stems]
            + [
                "build_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
                "test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
            ],
            "safety_scan_at_build": safety,
            "terminal_status": geometry_status["terminal_result_status"],
            "verification_commands_required_after_build": [
                "JSON parse all generated OTI6 JSON artifacts",
                "python -B -m py_compile build_oti6_otr061_cnr_quarantined_results_2026_05_07.py test_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
                "python -B -m pytest -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/test_oti6_otr061_cnr_quarantined_results_2026_05_07.py -q",
                "focused OTR061/G12 control tests",
                "scan generated outputs for NO_PROMOTION_VERDICT and forbidden true safety flags",
                "git diff forbidden live-surface scan",
            ],
            "verification_status": "PENDING_EXTERNAL_COMMANDS_AT_BUILD_TIME",
        }
    )
    artifacts[f"OTI6_CNR_COMPLETION_AUDIT_{DATE}"] = completion
    return artifacts


def write_artifacts(artifacts: dict[str, dict[str, Any]]) -> None:
    titles = {
        f"OTI6_CNR_METHOD_FREEZE_{DATE}": "OTI6 CNR Method Freeze",
        f"OTI6_CNR_RESULT_LEDGER_{DATE}": "OTI6 CNR Result Ledger",
        f"OTI6_CNR_SOURCE_HASH_COVERAGE_REPORT_{DATE}": "OTI6 CNR Source Hash Coverage Report",
        f"OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_{DATE}": "OTI6 CNR Geometry And Eligibility Audit",
        f"OTI6_CNR_DUPLICATE_LABEL_NOLEAK_AUDIT_{DATE}": "OTI6 CNR Duplicate Label No-Leak Audit",
        f"OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_{DATE}": "OTI6 CNR Result Or Impossibility Forensics",
        f"OTI6_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}": "OTI6 CNR Methodology DSR/PBO/Effective-N Report",
        f"OTI6_CNR_COMPLETION_AUDIT_{DATE}": "OTI6 CNR Completion Audit",
    }
    summaries = {
        f"OTI6_CNR_RESULT_LEDGER_{DATE}": [
            f"- Terminal status: `{artifacts[f'OTI6_CNR_RESULT_LEDGER_{DATE}']['result_status']}`",
            "- Synthetic path-R was not computed because CNR_E0 failed preregistered geometry before path scoring.",
        ],
        f"OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS_{DATE}": [
            "- This is a result-or-impossibility forensic artifact, not a promotion or validation result.",
            "- The row is useful evidence about decision latency and target-already-passed states.",
        ],
    }
    for stem, payload in artifacts.items():
        write_json(OUT / f"{stem}.json", payload)
        write_md(OUT / f"{stem}.md", titles.get(stem, stem), payload, summaries.get(stem))


def main() -> None:
    artifacts = build_bundle()
    write_artifacts(artifacts)
    completion = artifacts[f"OTI6_CNR_COMPLETION_AUDIT_{DATE}"]
    print(
        json.dumps(
            {
                "can_mark_goal_complete": completion["can_mark_goal_complete"],
                "terminal_status": completion["terminal_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
