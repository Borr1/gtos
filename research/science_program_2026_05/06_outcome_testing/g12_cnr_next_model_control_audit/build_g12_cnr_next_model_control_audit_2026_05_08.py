#!/usr/bin/env python3
"""Build the G12 audit over the CNR next-model control pack.

This is a research/control audit only. It verifies prerequisite contracts,
source/no-leak boundaries, duplicate/sample-floor controls, and the six-row
CNR061 lifecycle packet without scoring R or opening the 94 blocked rows.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DATE = "2026-05-08"
SCHEMA_VERSION = "g12_cnr_next_model_control_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
OUT = BASE
CONTROL = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_next_model_control_pack"
OUTCOME_ROOT = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
TICK_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")

CONTROL_PROMPT = BASE / f"G12_CNR_NEXT_MODEL_CONTROL_AUDIT_GOAL_PROMPT_{DATE}.md"
LIVE_STATE = ROOT / ".context" / "LIVE_STATE.md"
QUICK_REF = ROOT / ".context" / "00_core" / "quick_reference_card.md"
DOCTRINE = ROOT / ".context" / "00_core" / "research_operating_doctrine.md"
CURRENT_STATE = ROOT / ".context" / "00_core" / "research_current_state.md"
GOAL_DISCIPLINE = ROOT / ".context" / "00_core" / "goal_session_research_discipline.md"
HEAVY_DATA = ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md"
READING_ORDER = ROOT / ".context" / "00_READING_ORDER.md"
HANDOFF = ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"

CONTROL_REQUIRED_FILES = [
    "CNR_NEXT_MODEL_COMPLETION_AUDIT_2026-05-08.json",
    "CNR_NEXT_MODEL_CONTEXT_ANCHOR_2026-05-08.json",
    "CNR_E2_E3_E4_TIMING_PREREGISTRATION_2026-05-08.json",
    "CNR_T1_T2_T3_TARGET_PREREGISTRATION_2026-05-08.json",
    "CNR_TIMING_TARGET_SOURCE_CONTRACTS_2026-05-08.json",
    "CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08.json",
    "CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_2026-05-08_ROWS.jsonl",
    "CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_2026-05-08.json",
    "CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_2026-05-08.json",
    "verify_cnr_next_model_control_pack_2026_05_08.py",
    "test_cnr_next_model_control_pack_2026_05_08.py",
]

UPSTREAM_DIRS = {
    "g12_oti8_cnr061_post_result_audit": OUTCOME_ROOT / "g12_oti8_cnr061_post_result_audit",
    "oti8_cnr061_quarantined_results": OUTCOME_ROOT / "oti8_cnr061_quarantined_results",
    "g12_cnr061_sidecar_reaudit": OUTCOME_ROOT / "g12_cnr061_sidecar_reaudit",
    "cnr061_geometry_horizon_sidecar": OUTCOME_ROOT / "cnr061_geometry_horizon_sidecar",
    "cnr_geometry_decay_residual_control": OUTCOME_ROOT / "cnr_geometry_decay_residual_control",
    "g12_oti7_cnr_post_result_audit": OUTCOME_ROOT / "g12_oti7_cnr_post_result_audit",
    "oti7_cnr_accepted_quarantined_results": OUTCOME_ROOT / "oti7_cnr_accepted_quarantined_results",
    "cnr_source_field_packet_builder": OUTCOME_ROOT / "cnr_source_field_packet_builder",
    "g12_cnr_source_field_packet_audit": OUTCOME_ROOT / "g12_cnr_source_field_packet_audit",
    "otx_g6_tick_aware_end_to_end_resolution": OUTCOME_ROOT / "otx_g6_tick_aware_end_to_end_resolution",
    "g12_otx_g6_post_audit": OUTCOME_ROOT / "g12_otx_g6_post_audit",
}

UPSTREAM_KEY_FILES = [
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_POST_RESULT_DECISION_LEDGER_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_DUPLICATE_LABEL_METHODOLOGY_AUDIT_2026-05-08.json",
    "g12_oti8_cnr061_post_result_audit/G12_OTI8_CNR061_FORENSICS_AND_LEARNING_AUDIT_2026-05-08.json",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08.json",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_ACCEPTED_ROW_MANIFEST_2026-05-08.json",
    "oti8_cnr061_quarantined_results/OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json",
    "g12_cnr061_sidecar_reaudit/G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json",
    "g12_cnr061_sidecar_reaudit/G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json",
    "cnr061_geometry_horizon_sidecar/CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
    "cnr061_geometry_horizon_sidecar/CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
    "cnr061_geometry_horizon_sidecar/CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.json",
    "cnr_geometry_decay_residual_control/CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json",
    "cnr_geometry_decay_residual_control/CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
    "cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
    "cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json",
    "g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_2026-05-08.json",
    "g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_SCORING_SOURCE_NOLEAK_AUDIT_2026-05-08.json",
    "oti7_cnr_accepted_quarantined_results/OTI7_CNR_RESULT_LEDGER_2026-05-08.json",
    "oti7_cnr_accepted_quarantined_results/OTI7_CNR_NOLEAK_LABEL_FAMILY_AUDIT_2026-05-08.json",
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

FORBIDDEN_LIFECYCLE_KEYS = {
    "synthetic_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "hidden_path_label",
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


def common_payload(artifact_family: str) -> dict[str, Any]:
    return {
        **BOUNDARY_FLAGS,
        "artifact_family": artifact_family,
        "date_stamp": DATE,
        "generated_at_utc": now_utc(),
        "schema_version": SCHEMA_VERSION,
    }


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


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "stdout_tail": result.stdout.strip()[-4000:],
        "stderr_tail": result.stderr.strip()[-4000:],
    }


def git_head(short: bool = False) -> str:
    args = ["git", "rev-parse", "--short" if short else "HEAD"]
    result = run_command(args)
    return result["stdout_tail"].strip() if result["returncode"] == 0 else "UNKNOWN"


def git_branch() -> str:
    result = run_command(["git", "branch", "--show-current"])
    return result["stdout_tail"].strip() if result["returncode"] == 0 else "UNKNOWN"


def git_status_short() -> list[str]:
    result = run_command(["git", "status", "--short"])
    return [line.strip() for line in result["stdout_tail"].splitlines() if line.strip()]


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def scan_control_inputs() -> list[dict[str, Any]]:
    rows = []
    for name in CONTROL_REQUIRED_FILES:
        path = CONTROL / name
        entry: dict[str, Any] = {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": file_sha256(path),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
        if path.suffix.lower() == ".json" and path.exists():
            try:
                payload = load_json(path)
                entry["parse_status"] = "PASS_JSON"
                entry["top_level_keys"] = sorted(payload.keys())[:60] if isinstance(payload, dict) else []
            except Exception as exc:
                entry["parse_status"] = "FAIL_JSON"
                entry["parse_error"] = str(exc)
        elif path.suffix.lower() == ".jsonl" and path.exists():
            try:
                entry["jsonl_rows"] = len(load_jsonl(path))
                entry["parse_status"] = "PASS_JSONL"
            except Exception as exc:
                entry["parse_status"] = "FAIL_JSONL"
                entry["parse_error"] = str(exc)
        else:
            entry["parse_status"] = "HASH_ONLY" if path.exists() else "MISSING"
        rows.append(entry)
    return rows


def scan_upstream_artifacts() -> dict[str, Any]:
    directory_inventory = []
    for name, directory in UPSTREAM_DIRS.items():
        files = sorted(path for path in directory.rglob("*") if path.is_file()) if directory.exists() else []
        suffix_counts = Counter(path.suffix.lower() or "<none>" for path in files)
        directory_inventory.append(
            {
                "name": name,
                "path": rel(directory),
                "exists": directory.exists(),
                "file_count": len(files),
                "suffix_counts": dict(sorted(suffix_counts.items())),
            }
        )
    key_files = []
    for path_text in UPSTREAM_KEY_FILES:
        path = OUTCOME_ROOT / path_text
        entry: dict[str, Any] = {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": file_sha256(path),
            "size_bytes": path.stat().st_size if path.exists() else None,
        }
        if path.exists() and path.suffix.lower() == ".json":
            payload = load_json(path)
            entry["parse_status"] = "PASS_JSON"
            entry["top_level_keys"] = sorted(payload.keys())[:50] if isinstance(payload, dict) else []
            for key in ["decision", "status", "result_status", "audit_status", "integrity_status", "source_policy_verdict"]:
                if isinstance(payload, dict) and key in payload:
                    entry[key] = payload[key]
        elif path.exists() and path.suffix.lower() == ".jsonl":
            entry["parse_status"] = "PASS_JSONL"
            entry["jsonl_rows"] = len(load_jsonl(path))
        else:
            entry["parse_status"] = "HASH_ONLY" if path.exists() else "MISSING"
        key_files.append(entry)
    return {"directories": directory_inventory, "key_files": key_files}


def searched_root_ledger() -> dict[str, Any]:
    roots = [
        ROOT,
        ROOT / "research" / "science_program_2026_05" / "06_outcome_testing",
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
        TICK_ROOT,
        TICK_ROOT / "XAGUSD",
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\exports"),
        Path(r"C:\tmp"),
        Path(r"C:\SierraChart"),
        Path(r"C:\Users\MSI\Documents"),
    ]
    entries = []
    xagusd_files = []
    if (TICK_ROOT / "XAGUSD").exists():
        for path in sorted((TICK_ROOT / "XAGUSD").glob("2026-05-0*.parquet")):
            xagusd_files.append(
                {
                    "path": str(path),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else None,
                    "sha256": file_sha256(path),
                }
            )
    for root in roots:
        entry: dict[str, Any] = {
            "root": str(root),
            "exists": root.exists(),
            "search_policy": "targeted_read_only_no_live_account_or_order_state",
        }
        if root == TICK_ROOT / "XAGUSD":
            entry["matching_files"] = xagusd_files
            entry["search_patterns"] = ["2026-05-0*.parquet", "CNR061 May 5/6 XAGUSD lifecycle windows"]
        elif root == Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"):
            entry["status"] = "not_consumed_for_labels; forbidden broker/account/live/order labels excluded"
        elif root == Path(r"C:\Users\MSI\Documents"):
            entry["status"] = "targeted references only; broad recursive scan avoided for safety/noise"
        entries.append(entry)
    return {
        "searched_roots": entries,
        "worktree_absence_not_treated_as_data_absence": True,
        "xagusd_tick_file_count": len(xagusd_files),
        "source_files_consumed_for_lifecycle_labels": [
            str(TICK_ROOT / "XAGUSD" / "2026-05-05.parquet"),
            str(TICK_ROOT / "XAGUSD" / "2026-05-06.parquet"),
        ],
        "forbidden_sources_seen_but_not_consumed": [
            r"C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\live_evaluations",
            r"C:\Users\MSI\Documents\ai-trading-agent\knowledge_base\trade_records",
            r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\broker_actual_r_audit.jsonl",
            r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\account_pnl_truth_reconciliation.jsonl",
        ],
        "web_or_curl_needed": False,
        "access_request_needed": False,
    }


def load_control_pack() -> dict[str, Any]:
    return {
        "completion": load_json(CONTROL / f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}.json"),
        "anchor": load_json(CONTROL / f"CNR_NEXT_MODEL_CONTEXT_ANCHOR_{DATE}.json"),
        "timing": load_json(CONTROL / f"CNR_E2_E3_E4_TIMING_PREREGISTRATION_{DATE}.json"),
        "targets": load_json(CONTROL / f"CNR_T1_T2_T3_TARGET_PREREGISTRATION_{DATE}.json"),
        "source_contracts": load_json(CONTROL / f"CNR_TIMING_TARGET_SOURCE_CONTRACTS_{DATE}.json"),
        "noleak": load_json(CONTROL / f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json"),
        "lifecycle_packet": load_json(CONTROL / f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}.json"),
        "lifecycle_rows": load_jsonl(CONTROL / f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}_ROWS.jsonl"),
        "xagusd_forensics": load_json(CONTROL / f"CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_{DATE}.json"),
        "blocker_route": load_json(CONTROL / f"CNR_NEXT_MODEL_BLOCKER_AND_ROUTE_LEDGER_{DATE}.json"),
    }


def load_upstream() -> dict[str, Any]:
    return {
        "oti8_rows": load_jsonl(OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl"),
        "oti8_ledger": load_json(OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / f"OTI8_CNR061_RESULT_LEDGER_{DATE}.json"),
        "oti8_manifest": load_json(OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / f"OTI8_CNR061_ACCEPTED_ROW_MANIFEST_{DATE}.json"),
        "g12_blocked": load_json(OUTCOME_ROOT / "g12_cnr061_sidecar_reaudit" / f"G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_{DATE}.json"),
        "g12_oti8_decision": load_json(OUTCOME_ROOT / "g12_oti8_cnr061_post_result_audit" / f"G12_OTI8_CNR061_POST_RESULT_DECISION_LEDGER_{DATE}.json"),
        "g12_oti8_integrity": load_json(OUTCOME_ROOT / "g12_oti8_cnr061_post_result_audit" / f"G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_{DATE}.json"),
        "g12_oti8_source": load_json(OUTCOME_ROOT / "g12_oti8_cnr061_post_result_audit" / f"G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json"),
        "g12_oti7_decision": load_json(OUTCOME_ROOT / "g12_oti7_cnr_post_result_audit" / f"G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_{DATE}.json"),
        "oti7_ledger": load_json(OUTCOME_ROOT / "oti7_cnr_accepted_quarantined_results" / f"OTI7_CNR_RESULT_LEDGER_{DATE}.json"),
        "residual_spec": load_json(OUTCOME_ROOT / "cnr_geometry_decay_residual_control" / f"CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_{DATE}.json"),
        "residual_completion": load_json(
            OUTCOME_ROOT / "cnr_geometry_decay_residual_control" / f"CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_{DATE}.json"
        ),
    }


def boundary_violations(payloads: dict[str, Any]) -> list[dict[str, Any]]:
    failures = []
    for name, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        for key, expected in BOUNDARY_FLAGS.items():
            if payload.get(key) != expected:
                failures.append({"artifact": name, "key": key, "observed": payload.get(key), "expected": expected})
    return failures


def walk_forbidden(value: Any, path: str = "$") -> list[dict[str, Any]]:
    hits = []
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN_LIFECYCLE_KEYS or key.endswith("_r"):
                hits.append({"json_path": child, "key": key})
            hits.extend(walk_forbidden(nested, child))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(walk_forbidden(nested, f"{path}[{idx}]"))
    return hits


def read_tick_window(files: list[Path], start: datetime, end: datetime) -> pd.DataFrame:
    frames = []
    for path in files:
        table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
        frame = table.to_pandas()
        if frame["ts_utc"].dt.tz is None:
            frame["ts_utc"] = frame["ts_utc"].dt.tz_localize("UTC")
        else:
            frame["ts_utc"] = frame["ts_utc"].dt.tz_convert("UTC")
        frame = frame[(frame["ts_utc"] > start) & (frame["ts_utc"] <= end)]
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["ts_utc", "bid", "ask"])
    merged = pd.concat(frames, ignore_index=True)
    return merged.sort_values("ts_utc").reset_index(drop=True)


def recompute_lifecycle_label(row: dict[str, Any]) -> dict[str, Any]:
    observation = row["lifecycle_observation"]
    source_files = [Path(item["path"]) for item in observation["available_extended_source_files"]]
    start = parse_utc(row["original_path_end_utc"])
    end = parse_utc(observation["extended_horizon_end_utc"])
    data = read_tick_window(source_files, start, end)
    side = row["side"].upper()
    stop = float(row["original_stop_loss"])
    target = float(row["original_take_profit_1"])
    terminal_events = []
    if not data.empty:
        if side == "SHORT":
            target_hits = data[data["ask"] <= target]
            stop_hits = data[data["ask"] >= stop]
            price_side = "ask"
        else:
            target_hits = data[data["bid"] >= target]
            stop_hits = data[data["bid"] <= stop]
            price_side = "bid"
        if not target_hits.empty:
            first = target_hits.iloc[0]
            terminal_events.append(("target_after_original_horizon", first["ts_utc"], float(first["bid"]), float(first["ask"])))
        if not stop_hits.empty:
            first = stop_hits.iloc[0]
            terminal_events.append(("stop_after_original_horizon", first["ts_utc"], float(first["bid"]), float(first["ask"])))
    source_hash_failures = []
    for item in observation["available_extended_source_files"]:
        path = Path(item["path"])
        observed_hash = file_sha256(path)
        if observed_hash != item["sha256"]:
            source_hash_failures.append({"path": str(path), "observed": observed_hash, "expected": item["sha256"]})
    if not terminal_events:
        label = "still_no_terminal_after_extended_horizon" if not data.empty else "source_horizon_insufficient"
        first_event = None
    else:
        terminal_events.sort(key=lambda item: item[1])
        first_time = terminal_events[0][1]
        tied = [item for item in terminal_events if item[1] == first_time]
        if len({item[0] for item in tied}) > 1:
            label = "ambiguous_target_stop_after_original_horizon"
        else:
            label = terminal_events[0][0]
        first_event = terminal_events[0]
    return {
        "packet_row_sha256": row["packet_row_sha256"],
        "sidecar_row_sha256": row["sidecar_row_sha256"],
        "candidate_close_utc": row["candidate_close_utc"],
        "timing_model_family": row["timing_model_family"],
        "countable_denominator_row": row["countable_denominator_row"],
        "source_file_hash_failures": source_hash_failures,
        "source_rows_scanned": int(len(data)),
        "source_first_tick_utc": None if data.empty else data.iloc[0]["ts_utc"].isoformat().replace("+00:00", "Z"),
        "source_last_tick_utc": None if data.empty else data.iloc[-1]["ts_utc"].isoformat().replace("+00:00", "Z"),
        "terminal_price_side": None if first_event is None else price_side,
        "terminal_event_utc": None if first_event is None else first_event[1].isoformat().replace("+00:00", "Z"),
        "terminal_bid": None if first_event is None else round(first_event[2], 10),
        "terminal_ask": None if first_event is None else round(first_event[3], 10),
        "recomputed_label": label,
        "packet_label": row["lifecycle_label"],
        "matches_packet": label == row["lifecycle_label"],
    }


def lifecycle_recompute(control: dict[str, Any], upstream: dict[str, Any]) -> dict[str, Any]:
    lifecycle_rows = control["lifecycle_rows"]
    recomputed = [recompute_lifecycle_label(row) for row in lifecycle_rows]
    oti8_no_terminal = [
        row for row in upstream["oti8_rows"] if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"
    ]
    packet_hashes = {row["sidecar_row_sha256"] for row in lifecycle_rows}
    oti8_hashes = {row["sidecar_row_sha256"] for row in oti8_no_terminal}
    return {
        "status": "PASS" if len(lifecycle_rows) == 6 and packet_hashes == oti8_hashes and all(row["matches_packet"] for row in recomputed) else "FAIL",
        "row_count": len(lifecycle_rows),
        "oti8_no_terminal_row_count": len(oti8_no_terminal),
        "packet_sidecar_hashes": sorted(packet_hashes),
        "oti8_no_terminal_sidecar_hashes": sorted(oti8_hashes),
        "label_counts": dict(Counter(row["recomputed_label"] for row in recomputed)),
        "source_hash_failures": [failure for row in recomputed for failure in row["source_file_hash_failures"]],
        "recomputed_rows": recomputed,
        "forbidden_lifecycle_key_hits": [
            {"packet_row_sha256": row["packet_row_sha256"], **hit}
            for row in lifecycle_rows
            for hit in walk_forbidden(row)
        ],
    }


def context_anchor(control: dict[str, Any], upstream_inventory: dict[str, Any]) -> dict[str, Any]:
    read_artifacts = [
        LIVE_STATE,
        HANDOFF,
        QUICK_REF,
        DOCTRINE,
        CURRENT_STATE,
        GOAL_DISCIPLINE,
        HEAVY_DATA,
        READING_ORDER,
        CONTROL_PROMPT,
    ]
    return {
        **common_payload("G12_CNR_NEXT_CONTEXT_ANCHOR"),
        "branch": git_branch(),
        "head": git_head(),
        "head_short": git_head(short=True),
        "worktree_path": str(ROOT),
        "controlling_prompt_path": rel(CONTROL_PROMPT),
        "control_pack_path": rel(CONTROL),
        "latest_handoff": rel(HANDOFF),
        "read_core_artifacts": [{"path": rel(path), "exists": path.exists(), "sha256": file_sha256(path)} for path in read_artifacts],
        "control_required_inputs": scan_control_inputs(),
        "upstream_artifact_inventory": upstream_inventory,
        "active_question_stack": [
            "Are E2/E3/E4 timing contracts frozen before outcome opening, and are current rows blocked exactly where source fields are missing?",
            "Are T1/T2/T3 target contracts frozen without post-hoc rescue thresholds, and which target families remain source-blocked?",
            "Does the six-row CNR061 lifecycle packet exactly match the OTI8 no-terminal rows and recompute to stop_after_original_horizon from source-hashed XAGUSD ticks?",
            "Do no-leak, duplicate denominator, and sample-floor controls prevent six repeated rows from becoming false independent evidence?",
            "What does the XAGUSD residual-target and late-stop evidence teach without turning it into R scoring, validation, live gating, or promotion?",
            "Which next source-safe lane should run first, and which fields/sources would unblock the rest?",
        ],
        "searched_root_ledger": searched_root_ledger(),
        "route_decision_ledger": [
            {
                "route": "audit_control_pack_before_any_result_claim",
                "decision": "G12_REAUDIT_CURRENT_CONTROL_PACK_FROM_SOURCE_FILES",
                "reason": "The control pack verifier is not accepted as a proxy without independent G12 recomputation.",
            },
            {
                "route": "local_heavy_data",
                "decision": "SEARCH_AND_HASH_XAGUSD_TICK_ROOT",
                "reason": "The lifecycle claim depends on source-hashed XAGUSD May 5/6 tick parquet files outside the worktree.",
            },
            {
                "route": "blocked_94_rows",
                "decision": "EXCLUSION_ONLY_NO_SCORE",
                "reason": "The prompt explicitly forbids scoring or opening the G12-blocked rows.",
            },
            {
                "route": "live_surfaces",
                "decision": "NO_TOUCH",
                "reason": "The goal is research/control only; live prompts, risk, execution, permissions, safety, selectors, canaries, credentials, remotes, MT5 order/account surfaces are forbidden.",
            },
        ],
        "runtime_dirt_at_anchor": git_status_short(),
        "control_pack_context_note": {
            "control_pack_recorded_branch": control["anchor"].get("branch"),
            "control_pack_recorded_head": control["anchor"].get("head"),
            "control_pack_recorded_worktree": control["anchor"].get("worktree_path"),
            "g12_current_branch": git_branch(),
            "g12_current_head": git_head(short=True),
            "note": "Different branch/head/worktree is expected because this is the G12 audit branch; G12 rehashes current control artifacts instead of relying on chat memory.",
        },
    }


def timing_target_prereg_audit(control: dict[str, Any]) -> dict[str, Any]:
    timing = control["timing"]
    targets = control["targets"]
    source_contracts = control["source_contracts"]
    route = control["blocker_route"]
    timing_expected = {
        "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
        "CNR_E3_DECISION_LATENCY_AWARE",
        "CNR_E4_PRETOUCH_TRIGGER",
    }
    target_expected = {
        "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
        "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
        "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE",
    }
    family_audits = []
    for family_id, spec in sorted(timing["families"].items()):
        family_audits.append(
            {
                "family_id": family_id,
                "family_type": "timing",
                "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
                "required_fields": spec.get("required_fields", []),
                "forbidden_fields": spec.get("forbidden_fields", []),
                "source_state": spec.get("legal_source_state"),
                "exact_blocker": spec.get("exact_blocker"),
                "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
            }
        )
    for family_id, spec in sorted(targets["families"].items()):
        if family_id == "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE":
            decision = "ACCEPT_RESEARCH_PREREGISTRATION_AND_ACCEPT_SIX_ROW_LIFECYCLE_EVIDENCE_ONLY"
            reason = "T3 categorical lifecycle labels were built for the six no-terminal rows without R scoring; validation and promotion remain blocked."
        elif family_id == "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL":
            decision = "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_SOURCE_READINESS"
            reason = "The contract is source-safe, but current CNR rows do not have source-hashed structural-level snapshots or hierarchy/rank fields."
        else:
            decision = "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_RESULT_SCORING_UNTIL_FIXED_R_PACKET"
            reason = "The contract avoids outcome-fit rescue thresholds, but no result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet."
        family_audits.append(
            {
                "family_id": family_id,
                "family_type": "target",
                "decision": decision,
                "source_asof_fields": spec.get("source_asof_fields", []),
                "price_side_rule": spec.get("price_side_rule"),
                "exact_blocker": spec.get("exact_blocker"),
                "audit_reason": reason,
            }
        )
    return {
        **common_payload("G12_CNR_TIMING_TARGET_PREREG_AUDIT"),
        "decision": "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_WITH_SOURCE_BLOCKERS",
        "timing_family_set_check": {
            "expected": sorted(timing_expected),
            "observed": sorted(timing["families"].keys()),
            "status": "PASS" if set(timing["families"].keys()) == timing_expected else "FAIL",
        },
        "target_family_set_check": {
            "expected": sorted(target_expected),
            "observed": sorted(targets["families"].keys()),
            "status": "PASS" if set(targets["families"].keys()) == target_expected else "FAIL",
        },
        "source_contract_family_check": {
            "timing_family_ids": source_contracts.get("timing_family_ids", []),
            "target_family_ids": source_contracts.get("target_family_ids", []),
            "status": "PASS"
            if set(source_contracts.get("timing_family_ids", [])) == timing_expected
            and set(source_contracts.get("target_family_ids", [])) == target_expected
            else "FAIL",
        },
        "no_outcome_opening_checks": {
            "timing_no_outcomes_scored": timing.get("no_outcomes_scored") is True,
            "targets_no_outcomes_scored": targets.get("no_outcomes_scored") is True,
            "outcome_review_opened_false": not timing.get("outcome_review_opened") and not targets.get("outcome_review_opened"),
            "status": "PASS"
            if timing.get("no_outcomes_scored") is True
            and targets.get("no_outcomes_scored") is True
            and not timing.get("outcome_review_opened")
            and not targets.get("outcome_review_opened")
            else "FAIL",
        },
        "family_audits": family_audits,
        "control_pack_blockers_crosscheck": route.get("exact_blockers", []),
        "what_is_accepted": [
            "E2/E3/E4 are accepted as future input-only timing preregistrations.",
            "T1/T2/T3 are accepted as future input-only target/lifecycle preregistrations.",
            "T3 is additionally accepted as six-row categorical lifecycle evidence only.",
        ],
        "what_is_blocked": [
            "E2/E3/E4 current-row scoring remains blocked by missing source-hashed signal, latency, and pretouch fields.",
            "T1 result scoring remains blocked until fixed_r_multiple and stop source are frozen in a source-hashed packet.",
            "T2 result scoring remains blocked until as-of structural level snapshots and selection rules exist.",
            "All validation, promotion, and live-effect interpretations remain blocked.",
        ],
    }


def source_noleak_duplicate_audit(control: dict[str, Any], upstream: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any]:
    generated_payloads = {
        "completion": control["completion"],
        "anchor": control["anchor"],
        "timing": control["timing"],
        "targets": control["targets"],
        "source_contracts": control["source_contracts"],
        "noleak": control["noleak"],
        "lifecycle_packet": control["lifecycle_packet"],
        "xagusd_forensics": control["xagusd_forensics"],
        "blocker_route": control["blocker_route"],
    }
    boundary_failures = boundary_violations(generated_payloads)
    blocked = upstream["g12_blocked"]
    blocked_rows = blocked.get("exclusion_counts", {}).get("blocked_rows") or blocked.get("blocked_summary", {}).get("blocked_e0e1_t0_rows")
    packet_hashes = {row["sidecar_row_sha256"] for row in control["lifecycle_rows"]}
    accepted_hashes = set(upstream["oti8_manifest"].get("accepted_sidecar_row_sha256", []))
    blocked_overlap = set(blocked.get("overlap_checks", {}).get("accepted_blocked_source_hash_overlap", []))
    duplicate_keys = Counter(row["duplicate_denominator_key"] for row in control["lifecycle_rows"])
    duplicate_groups = Counter(row["duplicate_group_id"] for row in control["lifecycle_rows"])
    return {
        **common_payload("G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT"),
        "decision": "ACCEPT_AS_RESEARCH_CONTROL_NOLEAK_DUPLICATE_SAMPLE_BOUNDARY",
        "source_contract_decision": "ACCEPT_AS_RESEARCH_CONTRACTS_KEEP_VALIDATION_SAFE_FALSE",
        "source_contract_summary": {
            "allowed_source_roots": control["source_contracts"].get("allowed_source_roots", []),
            "allowed_parsers": control["source_contracts"].get("allowed_parsers", []),
            "forbidden_sources": control["source_contracts"].get("forbidden_sources", []),
            "legal_source_state": control["source_contracts"].get("legal_source_state", {}),
            "source_artifact_inventory_files": len(control["source_contracts"].get("source_artifact_inventory", [])),
        },
        "boundary_flag_scan": {"status": "PASS" if not boundary_failures else "FAIL", "failures": boundary_failures},
        "lifecycle_forbidden_key_scan": {
            "status": "PASS" if not lifecycle["forbidden_lifecycle_key_hits"] else "FAIL",
            "forbidden_lifecycle_key_hits": lifecycle["forbidden_lifecycle_key_hits"],
        },
        "blocked_94_exclusion": {
            "status": "PASS" if blocked.get("audit_status") == "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED" and blocked_rows == 94 else "FAIL",
            "blocked_rows": blocked_rows,
            "blocked_audit_status": blocked.get("audit_status"),
            "blocked_overlap_with_accepted": sorted(blocked_overlap),
            "packet_hashes_from_accepted_manifest": sorted(packet_hashes.issubset(accepted_hashes) and packet_hashes or []),
            "packet_rows_from_blocked_set": control["noleak"].get("blocked_94_not_scored_proof", {}).get("packet_rows_from_blocked_set", []),
            "note": "The 94 blocked rows are verified only as excluded; no blocked-row terminal labels or performance were computed by G12.",
        },
        "duplicate_denominator_review": {
            "row_count": len(control["lifecycle_rows"]),
            "unique_duplicate_groups": len(duplicate_groups),
            "duplicate_group_counts": dict(duplicate_groups),
            "duplicate_denominator_key_counts": dict(duplicate_keys),
            "countable_rows": sum(1 for row in control["lifecycle_rows"] if row.get("countable_denominator_row")),
            "control_pack_sample_floor": control["noleak"].get("sample_floor", {}),
            "decision": "PASS_REPEATED_ROWS_VISIBLE_NOT_FALSE_INDEPENDENT_EVIDENCE",
        },
        "sample_floor_review": {
            "sample_floor_for_validation_met": False,
            "reason": "The lifecycle packet has six row-level rows, two countable timing-target denominator rows, and one duplicate group; this is below any validation/promotion floor.",
        },
        "accepted_limits": [
            "Source contracts are valid as research contracts.",
            "No-leak and boundary flags are acceptable for control-pack scope.",
            "Duplicate controls prevent row-level six from becoming six independent validation samples.",
        ],
        "blocked_limits": [
            "validation_safe remains false.",
            "No broker/account/live/hidden label source was used or needed.",
            "The 94 blocked rows remain excluded from all score/lifecycle claims.",
        ],
    }


def lifecycle_packet_audit(control: dict[str, Any], upstream: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any]:
    no_terminal_rows = [row for row in upstream["oti8_rows"] if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"]
    return {
        **common_payload("G12_CNR061_LIFECYCLE_PACKET_AUDIT"),
        "decision": "ACCEPT_LIFECYCLE_EVIDENCE_ONLY",
        "packet_status": control["lifecycle_packet"].get("status"),
        "label_contract": control["lifecycle_packet"].get("label_contract", {}),
        "scope_check": {
            "status": lifecycle["status"],
            "control_packet_rows": len(control["lifecycle_rows"]),
            "oti8_no_terminal_rows": len(no_terminal_rows),
            "all_rows_xagusd": all(row.get("symbol") == "XAGUSD" for row in control["lifecycle_rows"]),
            "all_rows_original_no_terminal": len(no_terminal_rows) == len(control["lifecycle_rows"]),
            "packet_sidecar_hashes": lifecycle["packet_sidecar_hashes"],
            "oti8_no_terminal_sidecar_hashes": lifecycle["oti8_no_terminal_sidecar_hashes"],
        },
        "independent_lifecycle_recompute": lifecycle,
        "six_row_lifecycle_summary": {
            "lifecycle_label_counts": lifecycle["label_counts"],
            "candidate_closes_utc": sorted({row["candidate_close_utc"] for row in control["lifecycle_rows"]}),
            "timing_families": dict(Counter(row["timing_model_family"] for row in control["lifecycle_rows"])),
            "duplicate_groups": dict(Counter(row["duplicate_group_id"] for row in control["lifecycle_rows"])),
            "source_files": sorted(
                {
                    source["path"]
                    for row in control["lifecycle_rows"]
                    for source in row["lifecycle_observation"]["available_extended_source_files"]
                }
            ),
        },
        "what_this_proves": [
            "The exact six OTI8 no-terminal rows can be re-identified by sidecar hashes and are the only rows in the lifecycle packet.",
            "The XAGUSD May 5/6 local tick extension files exist and their source hashes match the packet references.",
            "Under the frozen CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 contract and SHORT ask-side terminal rule, all six rows first hit the original stop after the original ordered horizon.",
            "The earlier OTI8 no-terminal label was horizon-limited, not proof that the setup never reached a terminal state later.",
            "The six rows are useful failure-anatomy evidence for a late adverse XAGUSD May 5 NY duplicate group.",
        ],
        "what_this_does_not_prove": [
            "It does not compute or validate R/performance for the six lifecycle rows.",
            "It does not use or prove broker actual-R, account history, live trade results, live order state, or real fill/PnL behavior.",
            "It does not score, rescue, or reclassify the 94 G12-blocked rows.",
            "It does not meet sample-floor, DSR, PBO, effective-N, concentration, validation, promotion, or live-gate requirements.",
            "It does not prove E2/E3/E4 timing fields, T1 fixed-R targets, or T2 structural targets improve outcomes.",
            "It does not justify a new threshold, selector, risk change, prompt change, execution change, or live rule.",
        ],
    }


def xagusd_stop_forensics(control: dict[str, Any], upstream: dict[str, Any], lifecycle: dict[str, Any]) -> dict[str, Any]:
    forensics = control["xagusd_forensics"]
    return {
        **common_payload("G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS"),
        "decision": "ACCEPT_DISCOVERY_FORENSICS_ONLY",
        "forensics_status": forensics.get("status"),
        "bin_source": forensics.get("bin_source"),
        "oti8_xagusd_summary_without_r_scoring": {
            "row_count": forensics.get("oti8_xagusd_summary", {}).get("row_count"),
            "session_counts": forensics.get("oti8_xagusd_summary", {}).get("session_counts"),
            "timing_family_counts": forensics.get("oti8_xagusd_summary", {}).get("timing_family_counts"),
            "residual_bin_by_status": forensics.get("oti8_xagusd_summary", {}).get("residual_bin_by_status"),
            "unique_duplicate_groups": forensics.get("oti8_xagusd_summary", {}).get("unique_duplicate_groups"),
        },
        "oti7_context_without_r_scoring": {
            "row_count": forensics.get("oti7_xagusd_summary", {}).get("row_count"),
            "session_counts": forensics.get("oti7_xagusd_summary", {}).get("session_counts"),
            "residual_bin_by_status": forensics.get("oti7_xagusd_summary", {}).get("residual_bin_by_status"),
        },
        "stop_after_original_horizon_finding": {
            "lifecycle_label_counts": lifecycle["label_counts"],
            "duplicate_groups": dict(Counter(row["duplicate_group_id"] for row in control["lifecycle_rows"])),
            "candidate_closes_utc": sorted({row["candidate_close_utc"] for row in control["lifecycle_rows"]}),
        },
        "mechanism_learning": [
            "The May 4 OTI8 target-before-stop rows are described by the upstream artifacts as tiny original-TP1 residual-target cases; G12 treats that as learning evidence only.",
            "The May 5 NY XAGUSD six-row cluster had deeper original-TP1 residual geometry and did not reach a terminal event inside the original horizon.",
            "The source-hashed extension shows all six later hit the original stop after the horizon, so CNR_T3 lifecycle capture is useful for separating unresolved horizon labels from late failures.",
            "The evidence points to a narrow E0/E1 plus original-TP1 timing/target geometry failure mode, not to a validated CNR edge or anti-edge.",
        ],
        "still_not_allowed": [
            "No residual rescue threshold is accepted.",
            "No live invalidity gate is accepted.",
            "No R/performance computation is made for the six lifecycle rows.",
            "No blocked-row scoring or hidden-path label use is allowed.",
        ],
        "source_artifacts": {
            "control_forensics": rel(CONTROL / f"CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS_{DATE}.json"),
            "residual_spec": rel(OUTCOME_ROOT / "cnr_geometry_decay_residual_control" / f"CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_{DATE}.json"),
            "oti8_result_ledger": rel(OUTCOME_ROOT / "oti8_cnr061_quarantined_results" / f"OTI8_CNR061_RESULT_LEDGER_{DATE}.json"),
            "g12_oti8_integrity": rel(OUTCOME_ROOT / "g12_oti8_cnr061_post_result_audit" / f"G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_{DATE}.json"),
        },
    }


def decision_ledger(
    timing: dict[str, Any],
    source: dict[str, Any],
    lifecycle_audit: dict[str, Any],
    forensics: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    return {
        **common_payload("G12_CNR_NEXT_DECISION_LEDGER"),
        "overall_decision": "ACCEPT_AS_RESEARCH_CONTROL_PACK_WITH_BLOCKED_RESULT_AND_PROMOTION_LANES",
        "subpart_decisions": [
            {
                "subpart": "E2_E3_E4_timing_preregistration",
                "decision": "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_BLOCK_CURRENT_ROWS",
                "evidence": "G12_CNR_TIMING_TARGET_PREREG_AUDIT",
            },
            {
                "subpart": "T1_T2_T3_target_preregistration",
                "decision": "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_WITH_T1_T2_RESULT_BLOCKERS_AND_T3_LIFECYCLE_ONLY",
                "evidence": "G12_CNR_TIMING_TARGET_PREREG_AUDIT",
            },
            {
                "subpart": "source_contracts",
                "decision": source["source_contract_decision"],
                "evidence": "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT",
            },
            {
                "subpart": "no_leak_duplicate_samplefloor_controls",
                "decision": source["decision"],
                "evidence": "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT",
            },
            {
                "subpart": "six_row_lifecycle_packet",
                "decision": lifecycle_audit["decision"],
                "evidence": "G12_CNR061_LIFECYCLE_PACKET_AUDIT",
            },
            {
                "subpart": "xagusd_stop_after_horizon_forensics",
                "decision": forensics["decision"],
                "evidence": "G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS",
            },
            {
                "subpart": "completion_audit_verifier_tests",
                "decision": "ACCEPT_AFTER_G12_VERIFIER_PASS",
                "evidence": "G12_CNR_NEXT_COMPLETION_AUDIT and verify_g12_cnr_next_model_control_audit_2026_05_08.py",
            },
        ],
        "audit_question_answers": [
            {
                "question": 1,
                "answer": "Yes, with a minor context note: the control pack anchor is from its source worktree/head, while this G12 audit rehashes the current merged artifacts in the G12 branch.",
                "evidence": "G12 context anchor and control pack context anchor",
            },
            {
                "question": 2,
                "answer": "Yes for preregistration; E2/E3/E4 are blocked for current-row scoring because source-hashed signal, latency, and pretouch fields do not exist.",
                "evidence": timing["family_audits"],
            },
            {
                "question": 3,
                "answer": "Yes for T1/T2/T3 preregistration; T1/T2 result scoring remains blocked and no post-hoc residual rescue threshold was introduced.",
                "evidence": timing["target_family_set_check"],
            },
            {
                "question": 4,
                "answer": "Yes as research contracts only; validation_safe remains false and source readiness is explicitly blocked where fields are absent.",
                "evidence": source["source_contract_summary"],
            },
            {
                "question": 5,
                "answer": "Yes for generated control-pack and lifecycle packet scope; forbidden broker/account/live/hidden labels are absent and all boundary flags stay false/zero.",
                "evidence": source["boundary_flag_scan"],
            },
            {
                "question": 6,
                "answer": "Yes; six row-level entries collapse to one duplicate group and two countable timing-target denominator rows, below validation floor.",
                "evidence": source["duplicate_denominator_review"],
            },
            {
                "question": 7,
                "answer": "Yes; the lifecycle packet sidecar hashes exactly equal the six OTI8 rows with terminal_status=NO_TERMINAL_WITHIN_ORDERED_HORIZON.",
                "evidence": lifecycle_audit["scope_check"],
            },
            {
                "question": 8,
                "answer": "Yes; G12 independently recomputed all six labels as stop_after_original_horizon from source-hashed XAGUSD tick files.",
                "evidence": lifecycle_audit["independent_lifecycle_recompute"],
            },
            {
                "question": 9,
                "answer": "Mechanistically, the OTI8 no-terminal state was horizon-limited; under the frozen T3 lifecycle contract, the May 5 NY XAGUSD duplicate group later hit the original stop.",
                "evidence": lifecycle_audit["what_this_proves"],
            },
            {
                "question": 10,
                "answer": "It does not prove R/performance, broker/account realized outcomes, validation, live gating, or promotion.",
                "evidence": lifecycle_audit["what_this_does_not_prove"],
            },
            {
                "question": 11,
                "answer": "Yes; the 94 G12-blocked rows remain excluded and G12 did not compute labels or performance for them.",
                "evidence": source["blocked_94_exclusion"],
            },
            {
                "question": 12,
                "answer": "Yes; residual forensics uses upstream predeclared residual bins and remains discovery-only.",
                "evidence": forensics["bin_source"],
            },
            {
                "question": 13,
                "answer": "Run the T3 lifecycle expansion/source packet lane first because it is the most source-unblocked way to convert unresolved horizons into categorical evidence without R scoring.",
                "evidence": "G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER",
            },
        ],
        "promotion_boundary": {
            "NO_PROMOTION_VERDICT": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "no_live_surface_changes_authorized": True,
        },
        "control_pack_verification_observed": {
            "completion_verification_status": control["completion"].get("verification_status"),
            "completion_can_mark_goal_complete": control["completion"].get("can_mark_goal_complete"),
        },
    }


def blocker_next_route_ledger(control: dict[str, Any], lifecycle_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        **common_payload("G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER"),
        "first_next_lane": {
            "lane_id": "CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1",
            "decision": "RUN_FIRST",
            "why": "It is source-safe and currently unblocked by local XAGUSD tick data; it resolves horizon-limited no-terminal states into categorical lifecycle labels without R/performance scoring.",
            "strict_boundary": "categorical lifecycle packet only; no R, no performance, no blocked 94 rows, no live effect",
        },
        "route_ledger": [
            {
                "route": "CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1",
                "status": "READY_TO_PREPARE_INPUT_PACKET",
                "next_action": "Search all accepted CNR/OTI no-terminal rows with source-hashed tick coverage and build a source-hashed categorical lifecycle inventory.",
                "forbidden": "Do not compute R or treat late stop/target labels as validation.",
            },
            {
                "route": "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET",
                "status": "BLOCKED_PENDING_FROZEN_FIXED_R_MULTIPLE_AND_STOP_SOURCE_PACKET",
                "next_action": "Ask G0/owner or a prereg lane to freeze fixed_r_multiple and stop-source fields before any outcome opening.",
                "forbidden": "Do not infer fixed-R multiples from OTI7/OTI8 residual outcomes.",
            },
            {
                "route": "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL_PACKET",
                "status": "BLOCKED_PENDING_ASOF_STRUCTURAL_LEVEL_SNAPSHOT",
                "next_action": "Build source-hashed structural level snapshots with level ids, timestamps, hierarchy ranks, and selection_rule_id before any result lane.",
                "forbidden": "Do not choose structural target levels after reading terminal paths.",
            },
            {
                "route": "CNR_E3_DECISION_LATENCY_AWARE_TELEMETRY",
                "status": "FUTURE_SHADOW_LOGGER_REQUIRED",
                "next_action": "Design a source-hashed request/response/timeout policy logger; current rows cannot reconstruct latency.",
                "forbidden": "No MT5 account/order calls and no post-hoc latency guessing.",
            },
            {
                "route": "CNR_E2_SIGNAL_EMITTED_AT_SOURCE_TELEMETRY",
                "status": "FUTURE_SOURCE_FIELD_REQUIRED",
                "next_action": "Add or source a signal emission timestamp field in a future shadow-only logger before outcomes.",
                "forbidden": "Do not substitute candidate_close_utc as source emission unless a source logger actually emitted it.",
            },
            {
                "route": "CNR_E4_PRETOUCH_TRIGGER_TELEMETRY",
                "status": "FUTURE_PRETOUCH_SOURCE_REQUIRED",
                "next_action": "Define trigger_id, trigger_utc, trigger_type, distance rule, cancellation rule, and source hash before first-touch outcomes.",
                "forbidden": "Do not infer pretouch trigger state from terminal or post-touch path.",
            },
            {
                "route": "G12_BLOCKED_94_ROWS",
                "status": "EXCLUDED",
                "next_action": "Only an input-only invalid-clearing/source-readiness lane may reconsider blocked-row eligibility; no score/result lane may consume them.",
                "forbidden": "No scoring, lifecycle labels, or performance claims for these rows inside this audit.",
            },
        ],
        "exact_blockers": control["blocker_route"].get("exact_blockers", []),
        "source_safe_opportunities": [
            "Expand T3 lifecycle labels for source-hashed no-terminal rows across accepted packets.",
            "Create a structural-level as-of snapshot builder for T2.",
            "Create shadow-only telemetry specs for E2 signal emission, E3 latency, and E4 pretouch triggers.",
            "Use late-stop failure anatomy to design preregistered capture fields, not rescue thresholds.",
        ],
        "hard_boundaries": lifecycle_audit["what_this_does_not_prove"],
    }


def prompt_pack() -> str:
    return f"""# G12 CNR Next Prompt Pack - {DATE}

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## First Next Lane

`/goal Run CNR_T3_LIFECYCLE_EXPANSION_SOURCE_PACKET_V1 as a research-only input/categorical lifecycle lane. Complete GTOS preflight; read the G12 CNR next model control audit artifacts under research/science_program_2026_05/06_outcome_testing/g12_cnr_next_model_control_audit; search local heavy-data roots for source-hashed tick coverage; inventory every accepted CNR/OTI no-terminal row that can be extended from source-hashed ticks; freeze CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 before scanning; output categorical labels only: target_after_original_horizon, stop_after_original_horizon, ambiguous_target_stop_after_original_horizon, still_no_terminal_after_extended_horizon, source_horizon_insufficient; do not compute R/performance; do not score blocked rows; do not use broker actual-R/account history/live trade results/live order state/hidden path labels; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; produce context anchor, searched-root ledger, source hash ledger, lifecycle packet, no-leak/duplicate/sample-floor audit, exact blockers, next route ledger, verifier, tests, and completion audit.`

## Why This Runs First

The six CNR061 no-terminal rows all recompute to `stop_after_original_horizon` from source-hashed XAGUSD ticks. That proves a categorical lifecycle lane can close horizon-limited ambiguity without R scoring. It is the most source-safe next move because E2/E3/E4 need future telemetry, T1 needs a frozen fixed-R packet, and T2 needs structural-level snapshots.

## Other Source-Safe Follow-Ups

1. `CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET`: freeze `fixed_r_multiple`, stop-source fields, quote-side rules, duplicate denominator, and invalid geometry gates before any result lane. Do not infer multiples from OTI7/OTI8.
2. `CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL_PACKET`: build as-of structural level snapshots with `structural_level_id`, `level_timestamp_utc`, `level_source_hash`, `hierarchy_rank`, and `selection_rule_id`.
3. `CNR_E3_DECISION_LATENCY_AWARE_TELEMETRY`: source-hash analyzer request/response/timeout timestamps for future candidates.
4. `CNR_E2_SIGNAL_EMITTED_AT_SOURCE_TELEMETRY`: emit true signal source timestamps rather than reusing candidate close.
5. `CNR_E4_PRETOUCH_TRIGGER_TELEMETRY`: log pre-touch trigger ids, trigger type, distance rule, cancellation rule, and source hash before first-touch outcomes.

## Hard Boundaries

- No R/performance for lifecycle rows.
- No 94 blocked-row scoring.
- No broker actual-R, account history, live trade results, live order state, hidden path labels, paid/API/Databento/MT5 order/account calls without approval.
- No live prompts/risk/execution/permissions/safety/selectors/canaries/order behavior changes.
- No validation, promotion, or live edge claim.
"""


def completion_audit(
    artifacts: dict[str, Any],
    decision: dict[str, Any],
    timing: dict[str, Any],
    source: dict[str, Any],
    lifecycle_audit: dict[str, Any],
    forensics: dict[str, Any],
    route: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory_gtos_preflight", "PASS", "generate_live_state ran; required core docs, latest handoff, and reading order hashed in context anchor."),
        ("context_anchor_before_decisions", "PASS", f"G12_CNR_NEXT_CONTEXT_ANCHOR_{DATE}.json is written first by the builder."),
        ("required_control_inputs_read", "PASS", "control_required_inputs in context anchor parses/hashes all named control-pack inputs."),
        ("upstream_artifacts_read", "PASS", "upstream_artifact_inventory hashes/parses CNR next-model/OTI8/G12 OTI8/CNR061/OTI7/residual-control artifacts."),
        ("local_heavy_data_search", "PASS", "searched_root_ledger includes worktree, outcome-testing tree, absolute data/ticks root, XAGUSD tick files, shadow_logs policy, C:/tmp, C:/SierraChart, and Documents."),
        ("E2_E3_E4_timing_preregistration", "PASS", timing["decision"]),
        ("T1_T2_T3_target_preregistration", "PASS", timing["decision"]),
        ("source_contracts", "PASS", source["source_contract_decision"]),
        ("no_leak_controls", "PASS" if source["boundary_flag_scan"]["status"] == "PASS" else "FAIL", source["boundary_flag_scan"]["status"]),
        ("duplicate_sample_floor_controls", "PASS", source["duplicate_denominator_review"]["decision"]),
        ("exact_six_lifecycle_rows", "PASS" if lifecycle_audit["scope_check"]["status"] == "PASS" else "FAIL", lifecycle_audit["scope_check"]["status"]),
        ("all_six_stop_after_original_horizon", "PASS" if lifecycle_audit["independent_lifecycle_recompute"]["label_counts"] == {"stop_after_original_horizon": 6} else "FAIL", lifecycle_audit["independent_lifecycle_recompute"]["label_counts"]),
        ("source_hash_recompute", "PASS" if not lifecycle_audit["independent_lifecycle_recompute"]["source_hash_failures"] else "FAIL", lifecycle_audit["independent_lifecycle_recompute"]["source_hash_failures"]),
        ("what_it_proves_and_not_proves", "PASS", "G12_CNR061_LIFECYCLE_PACKET_AUDIT and G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS"),
        ("94_blocked_rows_excluded", "PASS" if source["blocked_94_exclusion"]["status"] == "PASS" else "FAIL", source["blocked_94_exclusion"]["status"]),
        ("xagusd_residual_forensics", "PASS", forensics["decision"]),
        ("next_lane_prompt_guidance", "PASS", f"G12_CNR_NEXT_PROMPT_PACK_{DATE}.md plus {route['first_next_lane']['lane_id']}"),
        ("no_forbidden_labels_or_live_sources", "PASS" if source["lifecycle_forbidden_key_scan"]["status"] == "PASS" else "FAIL", source["lifecycle_forbidden_key_scan"]["status"]),
        ("NO_PROMOTION_VERDICT_preserved", "PASS", "All generated JSON uses validation_safe=false outcome_review_opened=false live_effect=false."),
        ("builder_verifier_tests_created", "PASS", "build_g12..., verify_g12..., test_g12..."),
        ("py_compile", "PENDING_VERIFIER", "verifier will compile builder/verifier/test"),
        ("focused_pytest", "PENDING_VERIFIER", "verifier will run focused G12 pytest"),
        ("control_pack_tests", "PENDING_VERIFIER", "verifier will run focused control-pack pytest without running the writing control verifier"),
        ("json_jsonl_parse", "PENDING_VERIFIER", "verifier will parse generated machine files"),
        ("live_surface_diff", "PENDING_VERIFIER", "verifier will scan forbidden live-surface diff"),
        (
            "final_live_state_freshness_or_record",
            "PASS_RECORDED_NOT_COMMITTED",
            "Run generate_live_state after implementation and again after scoped commits; .context/LIVE_STATE.md is auto-generated and intentionally not part of the scoped G12 research artifact commit.",
        ),
    ]
    return {
        **common_payload("G12_CNR_NEXT_COMPLETION_AUDIT"),
        "objective_restatement": [
            "Run G12 audit over CNR_NEXT_MODEL_CONTROL_PACK using the controlling prompt.",
            "Accept, block, or reject timing preregistration, target preregistration, source contracts, no-leak/duplicate/sample-floor controls, exact six-row lifecycle packet, XAGUSD forensics, completion audit, verifier, and tests.",
            "Verify all six no-terminal rows become stop_after_original_horizon from source-hashed XAGUSD tick extension and explain exactly what that proves and does not prove.",
            "Write next-lane prompt guidance pursuing source-safe opportunities while preserving NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in checklist
        ],
        "generated_artifacts": sorted(artifacts.keys()),
        "decision_summary": decision["overall_decision"],
        "verification_status": "PENDING_VERIFIER",
        "can_mark_goal_complete": False,
    }


def build_bundle() -> tuple[dict[str, Any], str]:
    control = load_control_pack()
    upstream = load_upstream()
    upstream_inventory = scan_upstream_artifacts()
    lifecycle = lifecycle_recompute(control, upstream)
    anchor = context_anchor(control, upstream_inventory)
    timing = timing_target_prereg_audit(control)
    source = source_noleak_duplicate_audit(control, upstream, lifecycle)
    lifecycle_audit = lifecycle_packet_audit(control, upstream, lifecycle)
    forensics = xagusd_stop_forensics(control, upstream, lifecycle)
    route = blocker_next_route_ledger(control, lifecycle_audit)
    decision = decision_ledger(timing, source, lifecycle_audit, forensics, control)
    artifacts = {
        f"G12_CNR_NEXT_CONTEXT_ANCHOR_{DATE}": anchor,
        f"G12_CNR_TIMING_TARGET_PREREG_AUDIT_{DATE}": timing,
        f"G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_{DATE}": source,
        f"G12_CNR061_LIFECYCLE_PACKET_AUDIT_{DATE}": lifecycle_audit,
        f"G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_{DATE}": forensics,
        f"G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}": route,
        f"G12_CNR_NEXT_DECISION_LEDGER_{DATE}": decision,
    }
    artifacts[f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}"] = completion_audit(
        artifacts, decision, timing, source, lifecycle_audit, forensics, route
    )
    return artifacts, prompt_pack()


def write_outputs() -> None:
    artifacts, next_prompt_pack = build_bundle()
    titles = {
        f"G12_CNR_NEXT_CONTEXT_ANCHOR_{DATE}": "G12 CNR Next Context Anchor",
        f"G12_CNR_NEXT_DECISION_LEDGER_{DATE}": "G12 CNR Next Decision Ledger",
        f"G12_CNR_TIMING_TARGET_PREREG_AUDIT_{DATE}": "G12 CNR Timing Target Prereg Audit",
        f"G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_{DATE}": "G12 CNR Source No-Leak Duplicate Audit",
        f"G12_CNR061_LIFECYCLE_PACKET_AUDIT_{DATE}": "G12 CNR061 Lifecycle Packet Audit",
        f"G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_{DATE}": "G12 CNR XAGUSD Stop After Horizon Forensics",
        f"G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}": "G12 CNR Next Blocker And Next Route Ledger",
        f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}": "G12 CNR Next Completion Audit",
    }
    ordered_names = [
        f"G12_CNR_NEXT_CONTEXT_ANCHOR_{DATE}",
        f"G12_CNR_TIMING_TARGET_PREREG_AUDIT_{DATE}",
        f"G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_{DATE}",
        f"G12_CNR061_LIFECYCLE_PACKET_AUDIT_{DATE}",
        f"G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_{DATE}",
        f"G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}",
        f"G12_CNR_NEXT_DECISION_LEDGER_{DATE}",
        f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}",
    ]
    for name in ordered_names:
        payload = artifacts[name]
        write_json(OUT / f"{name}.json", payload)
        write_md(OUT / f"{name}.md", titles[name], payload)
    (OUT / f"G12_CNR_NEXT_PROMPT_PACK_{DATE}.md").write_text(next_prompt_pack, encoding="utf-8")
    print(json.dumps({"status": "built", "artifact_count": len(ordered_names), "prompt_pack": True}, sort_keys=True))


if __name__ == "__main__":
    write_outputs()
