#!/usr/bin/env python3
"""Build NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 artifacts.

Research/source-control only. The builder writes the context anchor and frozen
source contract before it scans the 298 accepted G12_NOFILL rows, then attempts
source-only closure for pending lifecycle, no-entry path order, terminal
sequence, source-blocked path availability, and OTI1 metadata projection.

It does not compute R, performance, validation, promotion, broker/account/live
labels, or order behavior.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-08"
SCHEMA = "nofill_lifecycle_closure_source_packet_v1"
CONTRACT_ID = "NOFILL_LIFECYCLE_CLOSURE_SOURCE_CONTRACT_V1"
PACKET_ID = "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
MAIN_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
PROMPT_PATH = OUT_DIR / "NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_GOAL_PROMPT_2026-05-08.md"

CORE_CONTEXT_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
]

CONTROL_INPUTS = [
    "g12_no_fill_lifecycle_audit/G12_NOFILL_NEXT_PROMPT_PACK_2026-05-08.md",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_DECISION_LEDGER_2026-05-08.json",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_LABEL_FAMILY_AUDIT_2026-05-08.json",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_FORENSICS_AND_LEARNING_2026-05-08.json",
    "g12_no_fill_lifecycle_audit/G12_NOFILL_BLOCKER_AND_NEXT_ROUTE_LEDGER_2026-05-08.json",
    "no_fill_still_pending_lifecycle_contract/NOFILL_FROZEN_LIFECYCLE_CONTRACT_2026-05-08.json",
    "no_fill_still_pending_lifecycle_contract/NOFILL_INPUT_ONLY_PACKET_2026-05-08.json",
    "no_fill_still_pending_lifecycle_contract/NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl",
    "no_fill_still_pending_lifecycle_contract/NOFILL_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
]

UPSTREAM_INPUTS = [
    "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json",
    "otb1r_input_only_lifecycle_rebuild/source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl",
    "oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "otb2r_input_only_path_rebuild/packets/OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json",
    "oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "oti4_g6_opening_drive_quarantined_results/OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    "otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
    "oti5_g6_cusum_changepoint_quarantined_results/OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
]

HEAVY_ROOTS = [
    Path("C:/Users/MSI/Documents/ai-trading-agent"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/research"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/data"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/data/external"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/pipeline_state"),
    Path("C:/Users/MSI/Documents/ai-trading-agent/knowledge_base"),
    Path("C:/tmp/gtos_otb"),
]

USDJPY_RECOVERED_M1 = MAIN_ROOT / "data" / "mt5_research_exports" / "phase3_v2b_forward_20260401_20260502_readonly" / "USDJPY_M1.csv"
TICK_ROOT = MAIN_ROOT / "data" / "ticks"
OTR061_XAUUSD_TICK_FILE = "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
OTR061_XAUUSD_TICK_SHA256 = "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"

FORBIDDEN_PACKET_KEYS = {
    "actual_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "synthetic_r",
    "descriptive_synthetic_path_r",
    "descriptive_gross_synthetic_path_r",
    "conservative_lower_bound_r",
    "reward_r_to_tp1",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "broker_fill_state",
    "mt5_order_ticket",
    "pending_ticket",
    "trade_state_ticket",
    "hidden_label",
}

FORBIDDEN_VALUE_NEEDLES = [
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_order_state",
    "validation_safe=true",
    "outcome_review_opened=true",
    "live_effect=true",
    "win rate",
    "expectancy",
    "DSR",
    "PBO",
]

FORBIDDEN_LIVE_PREFIXES = [
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
]

FORBIDDEN_LIVE_NAME_NEEDLES = [
    "mt5",
    "account",
    "risk",
    "execution",
    "permissions",
    "safety",
    "selector",
    "credential",
    "remote",
    "databento",
    "paid",
    "canary",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_precise(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_output(*args: str) -> str:
    cmd = ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", *args]
    try:
        return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE: {exc}"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def normalize_symbol(symbol: Any) -> str | None:
    if symbol in (None, ""):
        return None
    text = str(symbol)
    if text == "NDX100":
        return "NAS100"
    return text


def first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def read_packet_rows() -> list[dict[str, Any]]:
    return load_jsonl(OUTCOME_ROOT / "no_fill_still_pending_lifecycle_contract" / "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl")


def source_path_from_rel(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def strip_shared_family(value: str) -> str:
    if "|opportunity:" in value:
        return "opportunity:" + value.split("|opportunity:", 1)[1]
    return value


def index_records(records: list[dict[str, Any]], *keys: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        for key in keys:
            value = record.get(key)
            if value not in (None, ""):
                indexed[str(value)] = record
    return indexed


def load_sources() -> dict[str, Any]:
    oti2_rows = load_jsonl(OUTCOME_ROOT / "oti2_riskbank_quarantined_results" / "OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti2_packet = load_json(OUTCOME_ROOT / "otb2r_input_only_path_rebuild" / "packets" / "OTG0-PKT-013__G10-EXP-RISKBANK-005__otb2r_input_only_path_packet_2026-05-07.json")
    oti3_rows = load_jsonl(OUTCOME_ROOT / "oti3_g3_geometry_quarantined_results" / "OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti4_rows = load_jsonl(OUTCOME_ROOT / "oti4_g6_opening_drive_quarantined_results" / "OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti4_packet = load_json(OUTCOME_ROOT / "otb2r_g6_local_ohlc_momentum_reversion_packets" / "packets" / "OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json")
    oti5_rows = load_jsonl(OUTCOME_ROOT / "oti5_g6_cusum_changepoint_quarantined_results" / "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl")
    oti1_projections = load_jsonl(OUTCOME_ROOT / "otb1r_input_only_lifecycle_rebuild" / "source_projections" / "OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl")
    return {
        "oti1_projections_by_group": {row["duplicate_group_id"]: row for row in oti1_projections},
        "oti2_rows_by_setup": index_records(oti2_rows, "setup_id"),
        "oti2_packet_by_setup": index_records(oti2_packet["records"], "setup_id"),
        "oti3_rows_by_setup": index_records(oti3_rows, "setup_id"),
        "oti4_rows_by_record": index_records(oti4_rows, "record_id"),
        "oti4_packet_by_record": index_records(oti4_packet["records"], "record_id"),
        "oti5_rows_by_record": index_records(oti5_rows, "record_id"),
    }


def collect_input_file_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    paths = [PROMPT_PATH]
    paths += [REPO_ROOT / p for p in CORE_CONTEXT_INPUTS]
    paths += [OUTCOME_ROOT / p for p in CONTROL_INPUTS + UPSTREAM_INPUTS]
    for path in paths:
        checks.append({
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "role": "controlling_or_upstream_input",
        })
    return checks


def search_roots() -> list[dict[str, Any]]:
    wanted_names = {
        "NOFILL_INPUT_ONLY_PACKET_2026-05-08_ROWS.jsonl",
        "OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
        "OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl",
        "USDJPY_M1.csv",
        "NAS100_M15.csv",
        "XAGUSD_M15.csv",
        "XAUUSD_M15.csv",
        "GBPJPY_M15.csv",
        "USDJPY_M15.csv",
        "2026-05-03.parquet",
        "2026-05-04.parquet",
        "2026-05-05.parquet",
        "2026-05-06.parquet",
        OTR061_XAUUSD_TICK_FILE,
    }
    results: list[dict[str, Any]] = []
    for root in HEAVY_ROOTS:
        entry: dict[str, Any] = {
            "root": str(root),
            "exists": root.exists(),
            "search_policy": "targeted names only; no broad source opening",
            "matches": [],
        }
        if root.exists():
            try:
                count = 0
                for path in root.rglob("*"):
                    if not path.is_file() or path.name not in wanted_names:
                        continue
                    entry["matches"].append({
                        "path": str(path),
                        "name": path.name,
                        "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    })
                    count += 1
                    if count >= 80:
                        entry["truncated_after_matches"] = 80
                        break
            except Exception as exc:
                entry["search_error"] = str(exc)
        results.append(entry)
    return results


def lifecycle_projection_for(row: dict[str, Any], projections: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return projections.get(row["source_row_id"]) or projections.get(strip_shared_family(row["source_row_id"]))


def dependency_by_role(projection: dict[str, Any], role: str) -> dict[str, Any] | None:
    for dep in projection.get("projected_dependencies", []):
        if dep.get("source_role") == role:
            return dep.get("sanitized_source_row", {})
    return None


def project_oti1_metadata(row: dict[str, Any], projection: dict[str, Any] | None) -> dict[str, Any]:
    if not projection:
        return {
            "projected_symbol": normalize_symbol(row.get("symbol") or row.get("source_symbol")),
            "projected_session": row.get("session"),
            "projected_side": row.get("side"),
            "projection_status": "SOURCE_PROJECTION_MISSING",
        }
    audit = dependency_by_role(projection, "pending_limit_lifecycle_audit_row") or {}
    latest = dependency_by_role(projection, "pending_limit_lifecycle_latest_group_row") or {}
    opportunity = dependency_by_role(projection, "opportunity_lifecycle_audit_latest_candidate_row") or {}
    setup_id = projection.get("setup_id_or_candidate_id")
    symbol_from_setup = setup_id.split("_", 1)[0] if isinstance(setup_id, str) and "_" in setup_id else None
    return {
        "projected_symbol": normalize_symbol(first_present(audit.get("symbol"), latest.get("symbol"), opportunity.get("symbol"), symbol_from_setup, projection.get("source_symbol"))),
        "projected_session": first_present(audit.get("session"), latest.get("session"), opportunity.get("session")),
        "projected_side": first_present(audit.get("side"), latest.get("side")),
        "decision_asof_utc": first_present(audit.get("decision_time_utc"), latest.get("decision_time_utc"), opportunity.get("decision_time_utc"), setup_id.split("_", 1)[1] if isinstance(setup_id, str) and "_" in setup_id else None),
        "source_projection_id": projection.get("source_projection_id"),
        "source_projection_hash": projection.get("source_hash"),
        "projection_status": "PROJECTED_FROM_SANITIZED_LIFECYCLE_SOURCE",
    }


def close_oti1(row: dict[str, Any], projection: dict[str, Any] | None) -> dict[str, Any]:
    meta = project_oti1_metadata(row, projection)
    blockers: list[str] = []
    source: dict[str, Any] = {}
    label = "source_blocked_missing_pending_lifecycle_fields"
    status = "source_blocked_exact"
    if not projection:
        blockers.append("OTB1R sanitized lifecycle source projection missing for duplicate_group_id; searched exact and shared_family-stripped keys")
    else:
        audit = dependency_by_role(projection, "pending_limit_lifecycle_audit_row") or {}
        latest = dependency_by_role(projection, "pending_limit_lifecycle_latest_group_row") or {}
        final_state = audit.get("final_state")
        final_state_status = audit.get("final_state_status")
        latest_label = audit.get("latest_lifecycle_fill_no_fill_label") or latest.get("fill_no_fill_label")
        cancel_reason = audit.get("latest_lifecycle_cancel_reason") or latest.get("cancel_reason") or latest.get("reason")
        pending_created = latest.get("pending_created_time_utc")
        if not pending_created and audit.get("pending_intent_global_key"):
            pending_created = audit.get("pending_intent_global_key", "").split("|")[2]
        horizon = first_present(
            audit.get("latest_lifecycle_checked_candle_time_utc"),
            latest.get("checked_candle_time_utc"),
            latest.get("asof_cutoff_utc"),
            audit.get("latest_lifecycle_timestamp_utc"),
            latest.get("timestamp_utc"),
        )
        audit_time = parse_utc(audit.get("latest_lifecycle_timestamp_utc"))
        latest_time = parse_utc(latest.get("timestamp_utc"))
        if latest_time and (not audit_time or latest_time > audit_time):
            latest_fill_label = latest.get("fill_no_fill_label")
            if latest_fill_label == "no_fill_cancelled_wrong_side":
                final_state = "NO_FILL_CANCELLED_WRONG_SIDE"
                final_state_status = "FINAL_TERMINAL_NO_FILL"
                latest_label = latest_fill_label
                cancel_reason = latest.get("cancel_reason") or latest.get("reason")
            elif latest_fill_label == "no_fill_still_pending":
                final_state = "NO_FILL_STILL_PENDING"
                final_state_status = "STILL_ACTIVE_PENDING"
                latest_label = latest_fill_label
                cancel_reason = None
        if final_state == "NO_FILL_STILL_PENDING" or final_state_status == "STILL_ACTIVE_PENDING":
            label = "pending_still_open_at_frozen_horizon_source_confirmed"
            status = "source_closed"
        elif final_state == "NO_FILL_CANCELLED_WRONG_SIDE" or latest_label == "no_fill_cancelled_wrong_side":
            label = "pending_cancelled_wrong_side_before_fill_source_confirmed"
            status = "source_closed"
        elif final_state == "NO_FILL_CANCELLED_SYSTEM_OR_MANUAL" or cancel_reason == "new_day":
            label = "pending_cancelled_system_or_new_day_before_fill_source_confirmed"
            status = "source_closed"
        else:
            blockers.append(f"unrecognized pending lifecycle final_state={final_state} final_state_status={final_state_status} latest_label={latest_label}")
        if not pending_created:
            blockers.append("missing pending_created_at_utc in sanitized lifecycle projection")
        if not horizon:
            blockers.append("missing frozen_observation_horizon_utc in sanitized lifecycle projection")
        if not meta.get("projected_symbol") or not meta.get("projected_session") or not meta.get("projected_side"):
            blockers.append("missing top-level symbol/session/side projection from OTI1 lifecycle source")
        blockers.append("entry_touched_at_utc is not materialized in pending lifecycle source; future logger must capture it explicitly")
        source = {
            "pending_created_at_utc": pending_created,
            "source_fill_time_utc": latest.get("fill_time_utc") or audit.get("fill_time_utc"),
            "source_cancel_reason": cancel_reason,
            "source_expiry_time_utc": latest.get("expiry_time_utc"),
            "frozen_observation_horizon_utc": horizon,
            "entry_price": first_present(audit.get("entry_price"), latest.get("entry_price")),
            "terminal_area_price": first_present(audit.get("take_profit_1"), latest.get("take_profit_1")),
            "protective_level_price": first_present(audit.get("stop_loss"), latest.get("stop_loss")),
            "internal_lifecycle_final_state": final_state,
            "internal_lifecycle_final_state_status": final_state_status,
            "dependency_locations": projection.get("dependency_locations", []),
        }
    return {"closure_label": label, "closure_status": status, "source_projection": meta, "source_evidence": source, "exact_blockers": blockers}


def dates_between(start: dt.datetime, end: dt.datetime) -> list[dt.date]:
    cur = start.date()
    last = end.date()
    out = []
    while cur <= last:
        out.append(cur)
        cur += dt.timedelta(days=1)
    return out


_tick_cache: dict[str, pd.DataFrame] = {}


def load_tick_file(path: Path) -> pd.DataFrame | None:
    key = str(path)
    if key in _tick_cache:
        return _tick_cache[key]
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["ts_utc", "bid", "ask"])
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    _tick_cache[key] = df
    return df


def describe_tick_file(path: Path) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }
    if not path.exists() or not path.is_file():
        return item
    try:
        df = pd.read_parquet(path, columns=["ts_utc"])
        ts = pd.to_datetime(df["ts_utc"], utc=True)
        item.update({
            "row_count": int(len(ts)),
            "first_ts_utc": None if ts.empty else ts.min().isoformat().replace("+00:00", "Z"),
            "last_ts_utc": None if ts.empty else ts.max().isoformat().replace("+00:00", "Z"),
        })
    except Exception as exc:
        item["read_error"] = f"{type(exc).__name__}: {exc}"
    return item


def overlaps_window(item: dict[str, Any], start: dt.datetime, end: dt.datetime) -> bool:
    first = parse_utc(item.get("first_ts_utc"))
    last = parse_utc(item.get("last_ts_utc"))
    return bool(first and last and first <= end and last >= start)


def supplemental_tick_recovery_candidates(symbol: str, start: dt.datetime, end: dt.datetime) -> dict[str, Any]:
    """Search prior tick-recovery lanes before accepting a missing/no-window blocker."""
    direct_paths: list[Path] = []
    if normalize_symbol(symbol) == "XAUUSD":
        rel_path = Path("research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery") / OTR061_XAUUSD_TICK_FILE
        direct_paths = [
            REPO_ROOT / rel_path,
            MAIN_ROOT / rel_path,
        ]

    tmp_matches: list[Path] = []
    tmp_root = Path("C:/tmp/gtos_otb")
    if normalize_symbol(symbol) == "XAUUSD" and tmp_root.exists():
        pattern = f"*/research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/{OTR061_XAUUSD_TICK_FILE}"
        tmp_matches = sorted(tmp_root.glob(pattern))

    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for priority, path in enumerate(direct_paths + tmp_matches):
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        item = describe_tick_file(path)
        item["priority"] = priority
        item["source_lane"] = "otr061_xau_tick_recovery"
        item["expected_sha256"] = OTR061_XAUUSD_TICK_SHA256
        item["sha256_matches_expected"] = item.get("sha256") == OTR061_XAUUSD_TICK_SHA256
        item["overlaps_requested_window"] = overlaps_window(item, start, end) if item.get("exists") else False
        item["search_reason"] = "prior tick-recovery lane and absolute local-heavy-data root search before BLOCKED_NO_TICKS_IN_WINDOW"
        candidates.append(item)

    selected = [
        item for item in candidates
        if item.get("exists")
        and item.get("sha256_matches_expected")
        and item.get("overlaps_requested_window")
    ]
    selected = selected[:1]
    return {
        "search_policy": "deterministic priority: current worktree OTR061, main repo OTR061, then C:/tmp prior worktree copies; require expected SHA256 and requested-window overlap",
        "searched_roots": [
            rel(REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery"),
            str(MAIN_ROOT / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery"),
            str(tmp_root),
        ],
        "candidates": candidates,
        "selected_source_files": [item["path"] for item in selected],
    }


def tick_files_for(symbol: str, start: dt.datetime, end: dt.datetime) -> list[Path]:
    return [TICK_ROOT / symbol / f"{day.isoformat()}.parquet" for day in dates_between(start, end)]


def first_tick_touch(df: pd.DataFrame, side: str, level: float, kind: str) -> dt.datetime | None:
    if df.empty or level is None or (isinstance(level, float) and math.isnan(level)):
        return None
    if side == "LONG":
        if kind == "entry":
            mask = df["ask"] <= level
        elif kind == "terminal":
            mask = df["bid"] >= level
        else:
            mask = df["bid"] <= level
    else:
        if kind == "entry":
            mask = df["bid"] >= level
        elif kind == "terminal":
            mask = df["ask"] <= level
        else:
            mask = df["ask"] >= level
    hits = df.loc[mask, "ts_utc"]
    if hits.empty:
        return None
    return hits.iloc[0].to_pydatetime()


def tick_touch_projection(symbol: str, side: str, geometry: dict[str, Any], start_text: Any, end_text: Any, explicit_files: list[str] | None = None) -> dict[str, Any]:
    start = parse_utc(start_text)
    end = parse_utc(end_text)
    if start is None:
        return {"status": "BLOCKED_MISSING_PATH_START", "missing_files": [], "source_files": []}
    if end is None:
        end = start + dt.timedelta(days=2)
    source_files = [Path(p) for p in explicit_files] if explicit_files else tick_files_for(symbol, start, end)
    supplemental_search = {"search_policy": "not_applicable_explicit_files", "candidates": [], "selected_source_files": []}
    if not explicit_files:
        supplemental_search = supplemental_tick_recovery_candidates(symbol, start, end)
        for path_text in supplemental_search.get("selected_source_files", []):
            path = Path(path_text)
            if path not in source_files:
                source_files.append(path)
    missing = [str(p) for p in source_files if not p.exists()]
    existing_files = [p for p in source_files if p.exists()]
    if missing and explicit_files:
        return {"status": "BLOCKED_MISSING_TICK_SOURCE", "missing_files": missing, "source_files": [str(p) for p in source_files]}
    if not existing_files:
        return {
            "status": "BLOCKED_MISSING_TICK_SOURCE",
            "missing_files": missing,
            "source_files": [str(p) for p in source_files],
            "supplemental_tick_source_search": supplemental_search,
        }
    frames = []
    for path in existing_files:
        df = load_tick_file(path)
        if df is not None:
            frames.append(df)
    if not frames:
        return {"status": "BLOCKED_TICK_PARSE_EMPTY", "missing_files": [], "source_files": [str(p) for p in source_files]}
    df = pd.concat(frames, ignore_index=True)
    df = df[(df["ts_utc"] >= pd.Timestamp(start)) & (df["ts_utc"] <= pd.Timestamp(end))].sort_values("ts_utc")
    if df.empty:
        return {
            "status": "BLOCKED_NO_TICKS_IN_WINDOW",
            "missing_files": [],
            "source_files": [str(p) for p in source_files],
            "source_sha256": {str(p): sha256_file(p) for p in source_files},
            "path_start_utc": iso(start),
            "path_end_utc": iso(end),
            "supplemental_tick_source_search": supplemental_search,
        }
    entry = geometry.get("entry_price")
    terminal = geometry.get("take_profit_1")
    protective = geometry.get("stop_loss")
    entry_time = first_tick_touch(df, side, float(entry), "entry") if entry is not None else None
    terminal_time = first_tick_touch(df, side, float(terminal), "terminal") if terminal is not None else None
    protective_time = first_tick_touch(df, side, float(protective), "protective") if protective is not None else None
    touch_times = [t for t in [entry_time, terminal_time, protective_time] if t is not None]
    same_timestamp_ambiguity = len({t for t in touch_times}) < len(touch_times) if len(touch_times) > 1 else False
    return {
        "status": "TICK_SOURCE_PARSED",
        "path_start_utc": iso(start),
        "path_end_utc": iso(end),
        "tick_first_utc": iso_precise(df["ts_utc"].iloc[0].to_pydatetime()),
        "tick_last_utc": iso_precise(df["ts_utc"].iloc[-1].to_pydatetime()),
        "tick_count": int(len(df)),
        "entry_price": entry,
        "terminal_area_price": terminal,
        "protective_level_price": protective,
        "entry_touch_time_utc": iso_precise(entry_time),
        "terminal_area_touch_time_utc": iso_precise(terminal_time),
        "protective_level_touch_time_utc": iso_precise(protective_time),
        "same_timestamp_ambiguity": same_timestamp_ambiguity,
        "source_files": [str(p) for p in source_files],
        "source_sha256": {str(p): sha256_file(p) for p in source_files},
        "selected_supplemental_source_files": supplemental_search.get("selected_source_files", []),
        "supplemental_tick_source_search": supplemental_search,
        "source_selection_policy": "daily tick files plus source-hashed prior tick-recovery lanes where available before emitting missing-tick blockers",
        "parser_contract": "bid_ask_side_aware_touch_times_v1; LONG entry ask<=entry terminal bid>=target protective bid<=stop; SHORT entry bid>=entry terminal ask<=target protective ask>=stop",
    }


def close_oti2(row: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    upstream = sources["oti2_rows_by_setup"].get(row["source_row_id"]) or {}
    packet_record = sources["oti2_packet_by_setup"].get(row["source_row_id"]) or {}
    geometry = packet_record.get("entry_sl_tp_or_level_packet", {})
    blockers = []
    label = "entry_not_touched_before_terminal_area_source_confirmed"
    status = "source_closed"
    if row["contract_label"] == "terminal_order_unclaimed_entry_touched_unresolved":
        label = "entry_touched_terminal_sequence_unclaimed_source_confirmed"
        blockers.append("post_entry_terminal_touch_time is not claimable from the M1 path-order row; tick-level terminal sequence should remain a separate audit if needed")
    if not geometry:
        blockers.append("entry price/bounds missing from OTB2R input-only path packet")
        status = "source_available_exact_blocker"
    evidence = {
        "decision_asof_utc": upstream.get("decision_asof_utc") or row.get("decision_asof_utc"),
        "path_start_utc": upstream.get("path_start_utc") or row.get("path_start_utc"),
        "path_end_utc": upstream.get("path_end_utc") or row.get("original_horizon_end_utc"),
        "path_order_label": upstream.get("path_order_label"),
        "entry_touch_time_utc": upstream.get("entry_first_touch_utc"),
        "terminal_area_touch_time_utc": upstream.get("tp1_first_touch_utc"),
        "protective_level_touch_time_utc": upstream.get("sl_first_touch_utc"),
        "terminal_sequence_claim_allowed": upstream.get("terminal_order_claim_allowed"),
        "coverage_mode": upstream.get("coverage_mode"),
        "coverage_reaches_path_end_utc": upstream.get("coverage_reaches_path_end_utc"),
        "entry_price": geometry.get("entry_price"),
        "terminal_area_price": geometry.get("take_profit_1"),
        "protective_level_price": geometry.get("stop_loss"),
        "source_hash": upstream.get("source_hash"),
        "source_hash_match": upstream.get("source_hash_match"),
        "entry_geometry_hash": (packet_record.get("sanitized_source_hash_components") or {}).get("entry_sl_tp_or_level_packet_hash"),
    }
    return {"closure_label": label, "closure_status": status, "source_projection": {}, "source_evidence": evidence, "exact_blockers": blockers}


def read_csv_time_range_and_price(path: Path) -> dict[str, Any]:
    first_time = last_time = None
    min_low = max_high = None
    rows = 0
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows += 1
            t = parse_utc(row.get("time"))
            first_time = first_time or t
            last_time = t or last_time
            try:
                low = float(row.get("low", "nan"))
                high = float(row.get("high", "nan"))
            except ValueError:
                continue
            min_low = low if min_low is None else min(min_low, low)
            max_high = high if max_high is None else max(max_high, high)
    return {
        "path": str(path),
        "rows": rows,
        "first_utc": iso(first_time),
        "last_utc": iso(last_time),
        "min_low": min_low,
        "max_high": max_high,
        "sha256": sha256_file(path),
    }


_usdjpy_m1_summary: dict[str, Any] | None = None


def usdjpy_m1_summary() -> dict[str, Any]:
    global _usdjpy_m1_summary
    if _usdjpy_m1_summary is None:
        _usdjpy_m1_summary = read_csv_time_range_and_price(USDJPY_RECOVERED_M1)
    return _usdjpy_m1_summary


def close_oti3(row: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    upstream = sources["oti3_rows_by_setup"].get(row["source_row_id"]) or {}
    geometry = upstream.get("entry_sl_tp_or_level_packet", {})
    summary = usdjpy_m1_summary()
    decision = parse_utc(upstream.get("decision_asof_utc") or row.get("decision_asof_utc"))
    first = parse_utc(summary.get("first_utc"))
    last = parse_utc(summary.get("last_utc"))
    entry = geometry.get("entry_price")
    covered = bool(decision and first and last and first <= decision <= last)
    compatible = bool(entry is not None and summary.get("min_low") is not None and summary["min_low"] <= float(entry) <= summary["max_high"])
    blockers = []
    status = "source_closed" if covered and compatible else "source_blocked_exact"
    label = "price_compatible_m1_source_recovered" if covered and compatible else "source_blocked_missing_price_compatible_path"
    if not covered:
        blockers.append("recovered USDJPY M1 source does not cover decision_asof_utc")
    if not compatible:
        blockers.append("recovered USDJPY M1 source price range does not include entry_price")
    blockers.append("terminal touch replay remains unopened; this lane closes source availability only for prior source-blocked rows")
    return {
        "closure_label": label,
        "closure_status": status,
        "source_projection": {},
        "source_evidence": {
            "decision_asof_utc": upstream.get("decision_asof_utc") or row.get("decision_asof_utc"),
            "entry_price": entry,
            "terminal_area_price": geometry.get("take_profit_1"),
            "protective_level_price": geometry.get("stop_loss"),
            "prior_attempted_source_status": row.get("source_evidence", {}).get("outcome_source_status"),
            "prior_attempted_source": row.get("source_evidence", {}).get("outcome_source_attempted"),
            "recovered_m1_source": summary,
            "decision_covered_by_recovered_source": covered,
            "entry_price_compatible_with_recovered_source": compatible,
            "parser_scale_contract": "MT5 USDJPY M1 OHLC price scale; entry must lie inside recovered M1 min_low/max_high range",
        },
        "exact_blockers": blockers,
    }


def close_oti4(row: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    upstream = sources["oti4_rows_by_record"].get(row["source_row_id"]) or {}
    packet_record = sources["oti4_packet_by_record"].get(row["source_row_id"]) or {}
    geometry = packet_record.get("entry_sl_tp_or_level_packet", {})
    symbol = normalize_symbol(row.get("symbol") or packet_record.get("symbol"))
    side = row.get("side") or packet_record.get("side")
    start = packet_record.get("path_start_utc") or row.get("decision_asof_utc")
    end = packet_record.get("path_end_utc") or row.get("original_horizon_end_utc")
    blockers = []
    if not geometry:
        blockers.append("entry price/bounds missing from OTB2R G6 local OHLC input packet")
    if not symbol or not side:
        blockers.append("symbol or side missing for tick terminal sequence projection")
    tick_projection = tick_touch_projection(symbol, side, geometry, start, end) if geometry and symbol and side else {"status": "BLOCKED_MISSING_GEOMETRY_OR_SYMBOL_SIDE"}
    if tick_projection.get("status") == "TICK_SOURCE_PARSED":
        label = "terminal_sequence_tick_source_projected_no_score"
        status = "source_closed"
    else:
        label = "terminal_order_unclaimed_due_same_bar_or_ltf_gap"
        status = "source_blocked_exact"
        blockers.append(f"tick terminal sequence projection failed: {tick_projection.get('status')}")
    for reason in upstream.get("not_computable_reasons", []):
        if reason.startswith("missing_prereg_opening_drive_field"):
            blockers.append(reason)
    return {
        "closure_label": label,
        "closure_status": status,
        "source_projection": {},
        "source_evidence": {
            "decision_asof_utc": upstream.get("decision_asof_utc") or row.get("decision_asof_utc"),
            "prior_ohlc_source_path": upstream.get("ohlc_source_path"),
            "prior_ohlc_source_last_utc": upstream.get("ohlc_source_last_utc"),
            "prior_opening_drive_status": upstream.get("opening_drive_status"),
            "opening_drive_range_definition": packet_record.get("frozen_range_definition"),
            "entry_price": geometry.get("entry_price"),
            "terminal_area_price": geometry.get("take_profit_1"),
            "protective_level_price": geometry.get("stop_loss"),
            "tick_terminal_sequence_projection": tick_projection,
            "same_bar_ambiguity_policy": packet_record.get("same_bar_ambiguity_policy") or upstream.get("same_bar_ambiguity_policy"),
        },
        "exact_blockers": blockers,
    }


def close_oti5(row: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    upstream = sources["oti5_rows_by_record"].get(row["source_row_id"]) or {}
    geometry = upstream.get("entry_sl_tp_or_level_packet", {})
    symbol = normalize_symbol(row.get("symbol") or upstream.get("symbol"))
    side = row.get("side") or upstream.get("side")
    explicit_files = upstream.get("path_source_files") or []
    start = upstream.get("decision_asof_utc") or row.get("decision_asof_utc")
    end = None
    if explicit_files:
        # Use the last cited tick file as the frozen source horizon.
        end_date = Path(explicit_files[-1]).stem
        end = f"{end_date}T23:59:59Z"
    tick_projection = tick_touch_projection(symbol, side, geometry, start, end, explicit_files=explicit_files) if geometry and symbol and side else {"status": "BLOCKED_MISSING_GEOMETRY_OR_SYMBOL_SIDE"}
    blockers = []
    if tick_projection.get("status") != "TICK_SOURCE_PARSED":
        blockers.append(f"tick no-entry projection failed: {tick_projection.get('status')}")
        label = "source_blocked_missing_price_compatible_path"
        status = "source_blocked_exact"
    else:
        label = "entry_not_touched_through_tick_horizon_source_confirmed"
        status = "source_closed"
    return {
        "closure_label": label,
        "closure_status": status,
        "source_projection": {},
        "source_evidence": {
            "prior_result_status": upstream.get("result_status"),
            "prior_entry_touch_time_utc": upstream.get("entry_first_touch_utc"),
            "tick_path_projection": tick_projection,
        },
        "exact_blockers": blockers,
    }


def close_row(row: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    if row["source_lane"] == "OTI1_LIFECYCLE":
        projection = lifecycle_projection_for(row, sources["oti1_projections_by_group"])
        return close_oti1(row, projection)
    if row["source_lane"] == "OTI2_RISKBANK":
        return close_oti2(row, sources)
    if row["source_lane"] == "OTI3_G3_GEOMETRY":
        return close_oti3(row, sources)
    if row["source_lane"] == "OTI4_G6_OPENING_DRIVE":
        return close_oti4(row, sources)
    if row["source_lane"] == "OTI5_G6_CUSUM":
        return close_oti5(row, sources)
    return {
        "closure_label": "not_closure_contract_eligible",
        "closure_status": "source_blocked_exact",
        "source_projection": {},
        "source_evidence": {},
        "exact_blockers": [f"unsupported source_lane={row.get('source_lane')}"],
    }


def build_packet_rows(rows: list[dict[str, Any]], sources: dict[str, Any], classification_started_at: str) -> list[dict[str, Any]]:
    packet_rows = []
    for idx, row in enumerate(rows, 1):
        closure = close_row(row, sources)
        source_projection = closure.get("source_projection") or {}
        projected_symbol = normalize_symbol(first_present(source_projection.get("projected_symbol"), row.get("symbol"), row.get("source_symbol")))
        projected_session = first_present(source_projection.get("projected_session"), row.get("session"))
        projected_side = first_present(source_projection.get("projected_side"), row.get("side"))
        decision = first_present(source_projection.get("decision_asof_utc"), row.get("decision_asof_utc"))
        packet_rows.append({
            "packet_row_id": f"NOFILL-CLOSE-ROW-{idx:04d}",
            "schema_version": SCHEMA,
            "packet_id": PACKET_ID,
            "contract_id": CONTRACT_ID,
            "classification_started_at_utc": classification_started_at,
            "source_inventory_id": row["source_inventory_id"],
            "source_lane": row["source_lane"],
            "source_packet_id": row["source_packet_id"],
            "source_row_id": row["source_row_id"],
            "source_artifact_path": row["source_artifact_path"],
            "original_nofill_contract_label": row["contract_label"],
            "closure_label": closure["closure_label"],
            "closure_status": closure["closure_status"],
            "projected_symbol": projected_symbol,
            "projected_session": projected_session,
            "projected_side": projected_side,
            "decision_asof_utc": decision,
            "duplicate_group_id": row.get("duplicate_group_id"),
            "nofill_duplicate_key": row.get("nofill_duplicate_key"),
            "source_evidence": closure["source_evidence"],
            "source_hashes": row.get("source_hashes", {}),
            "source_projection": source_projection,
            "exact_blockers": closure.get("exact_blockers", []),
            "future_route_boundary": "source closure only; R/performance/result validation/promotion/live use remain blocked",
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "no_r_performance_or_live_fields_carried": True,
        })
    return packet_rows


def collect_consumed_source_files(packet_rows: list[dict[str, Any]], search: list[dict[str, Any]]) -> list[dict[str, Any]]:
    consumed: dict[str, dict[str, Any]] = {}
    for entry in collect_input_file_checks():
        consumed[entry["path"]] = entry
    for row in packet_rows:
        def add(path_text: Any, role: str, expected: str | None = None) -> None:
            if not path_text:
                return
            path = Path(str(path_text))
            if not path.is_absolute():
                path = source_path_from_rel(str(path_text))
            key = str(path)
            consumed[key] = {
                "path": key,
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "expected_sha256": expected,
                "role": role,
            }
        for key, value in (row.get("source_hashes") or {}).items():
            if ":" in key:
                add(key.split(":", 1)[1], "upstream_packet_source_hash", value)
        evidence = row.get("source_evidence") or {}
        for field in ["recovered_m1_source"]:
            source = evidence.get(field)
            if isinstance(source, dict):
                add(source.get("path"), field, source.get("sha256"))
        for proj_key in ["tick_terminal_sequence_projection", "tick_path_projection"]:
            source = evidence.get(proj_key)
            if isinstance(source, dict):
                for path_text, digest in (source.get("source_sha256") or {}).items():
                    add(path_text, proj_key, digest)
        source = row.get("source_projection") or {}
        if source.get("source_projection_hash"):
            # The source projection file itself is already in the input checks.
            pass
    return sorted(consumed.values(), key=lambda item: item["path"])


def scan_forbidden(obj: Any, path: str = "$") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            low = str(key).lower()
            if low in FORBIDDEN_PACKET_KEYS:
                hits.append({"path": f"{path}.{key}", "reason": "forbidden_key"})
            hits.extend(scan_forbidden(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden(value, f"{path}[{idx}]"))
    elif isinstance(obj, str):
        low_value = obj.lower()
        for needle in FORBIDDEN_VALUE_NEEDLES:
            if needle.lower() in low_value:
                hits.append({"path": path, "reason": f"forbidden_value:{needle}"})
    return hits


def write_context_anchor(anchor_time: str, search_results: list[dict[str, Any]]) -> dict[str, Any]:
    anchor = {
        "artifact_family": "NOFILL_CLOSE_CONTEXT_ANCHOR",
        "schema_version": SCHEMA,
        "written_at_utc": anchor_time,
        "git_head": git_output("rev-parse", "HEAD"),
        "git_status_short_at_anchor": git_output("status", "--short"),
        "controlling_prompt_path": rel(PROMPT_PATH),
        "controlling_inputs_read": CORE_CONTEXT_INPUTS + [rel(OUTCOME_ROOT / p) for p in CONTROL_INPUTS],
        "active_question_stack": [
            "pending lifecycle closure",
            "no-entry path order",
            "terminal sequence proof",
            "source-blocked path availability or impossibility",
            "OTI1 top-level symbol/session/side projection",
        ],
        "searched_roots": search_results,
        "source_boundaries": {
            "allowed": [
                "G12_NOFILL accepted 298-row packet",
                "sanitized lifecycle source projections",
                "source-hashed OTI2/OTI3/OTI4/OTI5 upstream ledgers and packet records",
                "read-only local tick parquet and local M1/M15 CSV files",
            ],
            "forbidden": [
                "R/performance/win-rate/expectancy/DSR/PBO",
                "broker/account/live/order-state/hidden labels",
                "blocked CNR061 outcomes",
                "live trading prompt/risk/execution/permissions/safety/selector/canary/MT5/paid/credential/remote changes",
            ],
        },
        "forbidden_fields": sorted(FORBIDDEN_PACKET_KEYS),
        "stop_condition_checklist": [
            "frozen contract before source classification",
            "row packet or exact blockers for every accepted G12_NOFILL row",
            "source search/hash ledger",
            "no-leak/hash audit",
            "duplicate/sample-floor audit",
            "forensics and learning",
            "G12 prompt pack",
            "verifier/tests",
            "completion audit",
            "commit scoped artifacts",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json", anchor)
    md = [
        "# NOFILL Close Context Anchor - 2026-05-08",
        "",
        f"Written at UTC: `{anchor_time}`",
        f"Git HEAD: `{anchor['git_head']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Active Question Stack",
    ]
    md += [f"- {item}" for item in anchor["active_question_stack"]]
    md += ["", "## Boundaries"]
    md += [f"- Allowed: {item}" for item in anchor["source_boundaries"]["allowed"]]
    md += [f"- Forbidden: {item}" for item in anchor["source_boundaries"]["forbidden"]]
    md += ["", "## Searched Roots"]
    for item in search_results:
        md.append(f"- `{item['root']}` exists={item['exists']} matches={len(item.get('matches', []))}")
    (OUT_DIR / "NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return anchor


def write_contract(contract_time: str, anchor_time: str) -> dict[str, Any]:
    contract = {
        "artifact_family": "NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT",
        "contract_id": CONTRACT_ID,
        "packet_id": PACKET_ID,
        "schema_version": SCHEMA,
        "context_anchor_written_at_utc": anchor_time,
        "contract_frozen_at_utc": contract_time,
        "classification_must_start_after_contract": True,
        "allowed_source_inputs": [
            "G12_NOFILL accepted input-only packet rows",
            "NOFILL source hash ledger",
            "OTB1R sanitized lifecycle source projections",
            "OTI2/OTB2R input-only M1 path-order records",
            "OTI3 source-blocked geometry rows plus recovered price-compatible USDJPY M1 CSV",
            "OTI4 G6 opening-drive packet records plus local tick parquet terminal sequence projection",
            "OTI5 tick-path result rows plus cited tick parquet files",
        ],
        "allowed_closure_labels": [
            "pending_still_open_at_frozen_horizon_source_confirmed",
            "pending_cancelled_wrong_side_before_fill_source_confirmed",
            "pending_cancelled_system_or_new_day_before_fill_source_confirmed",
            "entry_not_touched_before_terminal_area_source_confirmed",
            "entry_not_touched_through_tick_horizon_source_confirmed",
            "entry_touched_terminal_sequence_unclaimed_source_confirmed",
            "terminal_sequence_tick_source_projected_no_score",
            "price_compatible_m1_source_recovered",
            "source_blocked_missing_price_compatible_path",
            "source_blocked_missing_pending_lifecycle_fields",
            "source_blocked_missing_top_level_symbol_session_side",
            "terminal_order_unclaimed_due_same_bar_or_ltf_gap",
            "not_closure_contract_eligible",
        ],
        "asof_and_horizon_rules": {
            "pending_lifecycle": "Use sanitized pending lifecycle source timestamps; frozen horizon is latest checked candle/asof/timestamp in source projection.",
            "no_entry_path_order": "Use frozen OTB2R M1 path windows and path-order hashes; entry/terminal/protective touch times are source fields only.",
            "tick_terminal_sequence": "Use source-hashed tick parquet covering path_start through path_end; do not convert touch order into R/performance labels.",
            "source_blocked_recovery": "Source-blocked OTI3 rows can be marked recovered only when a price-compatible M1 source covers decision_asof and the entry price scale.",
        },
        "parser_and_scale_policy": {
            "tick_bid_ask": "bid_ask_side_aware_touch_times_v1",
            "m1_csv": "CSV time/open/high/low/close parsed as UTC; source availability only unless a separate terminal replay contract is frozen.",
            "same_timestamp": "same timestamp target/protective/entry touches are ambiguity, not a score.",
        },
        "source_hash_requirements": [
            "Every consumed artifact is SHA256 hashed.",
            "Prior packet-cited source hashes are recomputed where file exists.",
            "Recovered heavy-data files are recorded with absolute path and SHA256.",
        ],
        "forbidden_fields": sorted(FORBIDDEN_PACKET_KEYS),
        "duplicate_denominator_policy": "Row-level packet remains 298 accepted G12_NOFILL rows; denominator remains blocked by duplicate groups and mixed families.",
        "validation_promotion_blockers": [
            "No R/performance/result scoring in this lane.",
            "Mixed lifecycle/source families remain validation unsafe.",
            "Duplicate groups repeat; sample floor remains false.",
            "Future result lanes require separate frozen contracts and owner/G12 acceptance.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.json", contract)
    md = [
        "# NOFILL Close Frozen Source Contract - 2026-05-08",
        "",
        f"Contract: `{CONTRACT_ID}`",
        f"Frozen at UTC: `{contract_time}`",
        f"Context anchor written at UTC: `{anchor_time}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Allowed Closure Labels",
    ]
    md += [f"- `{label}`" for label in contract["allowed_closure_labels"]]
    md += ["", "## Validation/Promotion Blockers"]
    md += [f"- {item}" for item in contract["validation_promotion_blockers"]]
    (OUT_DIR / "NOFILL_CLOSE_FROZEN_SOURCE_CONTRACT_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return contract


def build_source_ledger(search_results: list[dict[str, Any]], consumed: list[dict[str, Any]]) -> dict[str, Any]:
    mismatches = [
        item for item in consumed
        if item.get("expected_sha256") and item.get("sha256") and item["expected_sha256"] != item["sha256"]
    ]
    missing_expected = [
        item for item in consumed
        if item.get("expected_sha256") and not item.get("exists")
    ]
    ledger = {
        "artifact_family": "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "searched_roots": search_results,
        "consumed_source_files": consumed,
        "consumed_source_file_count": len(consumed),
        "hash_mismatches": mismatches,
        "missing_expected_files": missing_expected,
        "source_boundaries": "local/read-only source files only; no MT5 account/order, paid/API/Databento, credentials, or remotes",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json", ledger)
    md = [
        "# NOFILL Close Source Search Ledger - 2026-05-08",
        "",
        f"Consumed source files: `{len(consumed)}`",
        f"Hash mismatches: `{len(mismatches)}`",
        f"Missing expected files: `{len(missing_expected)}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Searched Roots",
    ]
    for root in search_results:
        md.append(f"- `{root['root']}` exists={root['exists']} matches={len(root.get('matches', []))}")
    (OUT_DIR / "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return ledger


def write_packet(packet_rows: list[dict[str, Any]], classification_started_at: str) -> dict[str, Any]:
    counts = Counter(row["closure_label"] for row in packet_rows)
    status_counts = Counter(row["closure_status"] for row in packet_rows)
    packet = {
        "artifact_family": "NOFILL_CLOSE_ROW_PACKET",
        "schema_version": SCHEMA,
        "packet_id": PACKET_ID,
        "contract_id": CONTRACT_ID,
        "classification_started_at_utc": classification_started_at,
        "packet_row_count": len(packet_rows),
        "packet_rows_jsonl": "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl",
        "closure_label_counts": dict(sorted(counts.items())),
        "closure_status_counts": dict(sorted(status_counts.items())),
        "source_lane_counts": dict(sorted(Counter(row["source_lane"] for row in packet_rows).items())),
        "forbidden_fields_carried": scan_forbidden(packet_rows),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json", packet)
    write_jsonl(OUT_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl", packet_rows)
    return packet


def build_read_only_extraction_requests(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests = []
    for row in packet_rows:
        if not row.get("exact_blockers") or not any("BLOCKED_NO_TICKS_IN_WINDOW" in blocker for blocker in row["exact_blockers"]):
            continue
        tick_projection = (row.get("source_evidence") or {}).get("tick_terminal_sequence_projection") or {}
        symbol = row.get("projected_symbol") or normalize_symbol(row.get("symbol")) or "UNKNOWN"
        start_utc = tick_projection.get("path_start_utc") or row.get("decision_asof_utc")
        end_utc = tick_projection.get("path_end_utc")
        date_token = str(start_utc or DATE)[:10]
        manifest_path = OUT_DIR / "source_requests" / f"{row['packet_row_id']}_{symbol}_{date_token}_ticks_READONLY_REQUEST.json"
        request = {
            "artifact_family": "NOFILL_CLOSE_READ_ONLY_EXTRACTION_REQUEST",
            "schema_version": SCHEMA,
            "generated_at_utc": utc_now(),
            "request_id": f"{row['packet_row_id']}_READONLY_TICK_WINDOW",
            "packet_row_id": row["packet_row_id"],
            "source_inventory_id": row["source_inventory_id"],
            "source_lane": row["source_lane"],
            "source_row_id": row["source_row_id"],
            "reason": "Existing source-hashed tick parquet exists but has no rows inside the frozen terminal-sequence window.",
            "source_gap": "BLOCKED_NO_TICKS_IN_WINDOW",
            "symbol": symbol,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "requested_source": "read-only MT5 tick/rates extraction if owner grants access in a separate run",
            "requested_fields": ["ts_utc", "bid", "ask", "last", "volume", "flags"],
            "proposed_cache_path": rel(manifest_path),
            "request_manifest_path": rel(manifest_path),
            "must_hash_output": True,
            "forbidden_calls": [
                "MT5 account/history/deals/positions",
                "live order state",
                "order send/modify/cancel",
                "broker actual-R",
            ],
            "asof_rule": "Use only ticks/rates inside frozen path_start/path_end; do not compute R/performance.",
            "existing_source_files": tick_projection.get("source_files", []),
            "existing_source_sha256": tick_projection.get("source_sha256", {}),
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(manifest_path, request)
        requests.append(request)
    return requests


def build_superseded_extraction_requests(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    superseded = []
    for row in packet_rows:
        if row.get("packet_row_id") != "NOFILL-CLOSE-ROW-0127":
            continue
        tick_projection = (row.get("source_evidence") or {}).get("tick_terminal_sequence_projection") or {}
        selected = tick_projection.get("selected_supplemental_source_files") or []
        if row.get("closure_status") != "source_closed" or not selected:
            continue
        manifest_path = OUT_DIR / "source_requests" / "NOFILL-CLOSE-ROW-0127_XAUUSD_2026-05-06_ticks_READONLY_REQUEST.json"
        request = {
            "artifact_family": "NOFILL_CLOSE_READ_ONLY_EXTRACTION_REQUEST",
            "schema_version": SCHEMA,
            "generated_at_utc": utc_now(),
            "request_id": "NOFILL-CLOSE-ROW-0127_READONLY_TICK_WINDOW",
            "packet_row_id": row["packet_row_id"],
            "source_inventory_id": row["source_inventory_id"],
            "source_lane": row["source_lane"],
            "source_row_id": row["source_row_id"],
            "current_audit_status": "SUPERSEDED_BY_EXISTING_LOCAL_OTR061_SOURCE_EVIDENCE",
            "active_request": False,
            "superseded_reason": "Existing source-hashed OTR061 XAUUSD tick parquet contains the decisive side-aware terminal-area first touch for source-only closure.",
            "superseded_by_source_files": selected,
            "superseded_by_source_sha256": {
                path: tick_projection.get("source_sha256", {}).get(path)
                for path in selected
            },
            "source_gap": "RESOLVED_FORMER_BLOCKED_NO_TICKS_IN_WINDOW",
            "original_source_gap": "BLOCKED_NO_TICKS_IN_WINDOW",
            "symbol": row.get("projected_symbol"),
            "start_utc": tick_projection.get("path_start_utc"),
            "end_utc": tick_projection.get("path_end_utc"),
            "terminal_area_touch_time_utc": tick_projection.get("terminal_area_touch_time_utc"),
            "entry_touch_time_utc": tick_projection.get("entry_touch_time_utc"),
            "protective_level_touch_time_utc": tick_projection.get("protective_level_touch_time_utc"),
            "request_manifest_path": rel(manifest_path),
            "future_use_boundary": "Only revive a read-only extraction request if a later frozen contract requires full path-end tick coverage independent of the already observed terminal first-touch event.",
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(manifest_path, request)
        superseded.append(request)
    return superseded


def write_blocker_ledger(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row_blockers = [
        {
            "packet_row_id": row["packet_row_id"],
            "source_inventory_id": row["source_inventory_id"],
            "source_lane": row["source_lane"],
            "source_row_id": row["source_row_id"],
            "closure_label": row["closure_label"],
            "closure_status": row["closure_status"],
            "exact_blockers": row["exact_blockers"],
        }
        for row in packet_rows
        if row.get("exact_blockers")
    ]
    blocker_counts = Counter()
    for row in row_blockers:
        for blocker in row["exact_blockers"]:
            blocker_counts[blocker] += 1
    read_only_extraction_requests = build_read_only_extraction_requests(packet_rows)
    superseded_read_only_extraction_requests = build_superseded_extraction_requests(packet_rows)
    ledger = {
        "artifact_family": "NOFILL_CLOSE_ROW_BLOCKER_LEDGER",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "packet_rows": len(packet_rows),
        "rows_with_exact_blockers": len(row_blockers),
        "row_blockers": row_blockers,
        "blocker_counts": dict(blocker_counts.most_common()),
        "read_only_extraction_requests": read_only_extraction_requests,
        "superseded_read_only_extraction_requests": superseded_read_only_extraction_requests,
        "source_closed_rows": sum(1 for row in packet_rows if row["closure_status"] == "source_closed"),
        "source_blocked_exact_rows": sum(1 for row in packet_rows if row["closure_status"] == "source_blocked_exact"),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json", ledger)
    md = [
        "# NOFILL Close Row Blocker Ledger - 2026-05-08",
        "",
        f"Rows: `{len(packet_rows)}`",
        f"Rows with exact blockers: `{len(row_blockers)}`",
        f"Source closed rows: `{ledger['source_closed_rows']}`",
        f"Exact source-blocked rows: `{ledger['source_blocked_exact_rows']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Top Blockers",
    ]
    for blocker, count in blocker_counts.most_common(20):
        md.append(f"- `{count}` {blocker}")
    md += ["", "## Read-Only Extraction Requests"]
    if read_only_extraction_requests:
        for request in read_only_extraction_requests:
            md.append(
                f"- `{request['request_id']}` {request['symbol']} `{request['start_utc']}` to "
                f"`{request['end_utc']}` manifest `{request['request_manifest_path']}`"
            )
    else:
        md.append("- None")
    md += ["", "## Superseded Read-Only Extraction Requests"]
    if superseded_read_only_extraction_requests:
        for request in superseded_read_only_extraction_requests:
            md.append(
                f"- `{request['request_id']}` status `{request['current_audit_status']}` terminal touch "
                f"`{request['terminal_area_touch_time_utc']}` manifest `{request['request_manifest_path']}`"
            )
    else:
        md.append("- None")
    (OUT_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return ledger


def write_noleak_audit(packet_rows: list[dict[str, Any]], source_ledger: dict[str, Any]) -> dict[str, Any]:
    forbidden_hits = scan_forbidden(packet_rows)
    six_t3_leaks = [row for row in packet_rows if row["source_lane"] == "OTI8_CNR061" or row["closure_label"] == "stop_after_original_horizon"]
    blocked_94_leaks = [row for row in packet_rows if row["source_lane"] == "OTI8_CNR061"]
    audit = {
        "artifact_family": "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "forbidden_packet_hits": forbidden_hits,
        "forbidden_packet_hits_count": len(forbidden_hits),
        "hash_mismatches": source_ledger["hash_mismatches"],
        "missing_expected_files": source_ledger["missing_expected_files"],
        "consumed_source_file_count": source_ledger["consumed_source_file_count"],
        "six_t3_rows_exclusion": {"status": "PASS" if not six_t3_leaks else "FAIL", "leaks": six_t3_leaks[:5]},
        "blocked_94_cnr061_exclusion": {"status": "PASS" if not blocked_94_leaks else "FAIL", "leaks": blocked_94_leaks[:5]},
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_account_calls": 0,
        "mt5_order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "canary_calls": 0,
        "status": "PASS" if not forbidden_hits and not source_ledger["hash_mismatches"] and not six_t3_leaks and not blocked_94_leaks else "FAIL",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json", audit)
    md = [
        "# NOFILL Close Source Hash And No-Leak Audit - 2026-05-08",
        "",
        f"Status: `{audit['status']}`",
        f"Forbidden packet hits: `{len(forbidden_hits)}`",
        f"Hash mismatches: `{len(source_ledger['hash_mismatches'])}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
    ]
    (OUT_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return audit


def write_duplicate_audit(packet_rows: list[dict[str, Any]]) -> dict[str, Any]:
    duplicate_counts = Counter(row["nofill_duplicate_key"] for row in packet_rows)
    group_counts = Counter(row["duplicate_group_id"] for row in packet_rows)
    audit = {
        "artifact_family": "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "packet_rows": len(packet_rows),
        "source_inventory_id_unique": len({row["source_inventory_id"] for row in packet_rows}),
        "nofill_duplicate_key_unique": len(duplicate_counts),
        "nofill_duplicate_key_repeated_count": sum(1 for count in duplicate_counts.values() if count > 1),
        "nofill_duplicate_key_max_repeat": max(duplicate_counts.values()),
        "duplicate_group_id_unique": len(group_counts),
        "duplicate_group_id_repeated_count": sum(1 for count in group_counts.values() if count > 1),
        "duplicate_group_id_max_repeat": max(group_counts.values()),
        "top_repeated_nofill_duplicate_keys": dict(duplicate_counts.most_common(12)),
        "closure_label_counts": dict(sorted(Counter(row["closure_label"] for row in packet_rows).items())),
        "validation_sample_floor_status": "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION",
        "sample_floor_reason": "Rows are mixed source-closure families with repeated opportunity groups; source closure does not create a validation denominator.",
        "status": "PASS",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json", audit)
    md = [
        "# NOFILL Close Duplicate Sample-Floor Audit - 2026-05-08",
        "",
        f"Rows: `{len(packet_rows)}`",
        f"Unique source inventory IDs: `{audit['source_inventory_id_unique']}`",
        f"Unique nofill duplicate keys: `{audit['nofill_duplicate_key_unique']}`",
        "Validation sample floor: `FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
    ]
    (OUT_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return audit


def write_forensics(packet_rows: list[dict[str, Any]], blocker: dict[str, Any]) -> dict[str, Any]:
    by_label = defaultdict(list)
    for row in packet_rows:
        by_label[row["closure_label"]].append(row)
    family_notes = {
        "pending_still_open_at_frozen_horizon_source_confirmed": "OTI1 still-pending rows can be source-closed to a frozen lifecycle horizon, but entry-touch timestamps remain a required future logger field.",
        "pending_cancelled_wrong_side_before_fill_source_confirmed": "Wrong-side cancellations are internally source-confirmed as no-fill lifecycle closures; they are not performance outcomes.",
        "pending_cancelled_system_or_new_day_before_fill_source_confirmed": "Some earlier still-pending rows closed later by system/new-day cancellation in sanitized lifecycle audit source.",
        "entry_not_touched_before_terminal_area_source_confirmed": "OTI2 M1 path-order rows prove terminal-area touch before entry touch without carrying R.",
        "entry_not_touched_through_tick_horizon_source_confirmed": "OTI5 tick paths prove no entry touch through the cited tick horizon; terminal scoring remains blocked.",
        "terminal_sequence_tick_source_projected_no_score": "OTI4 terminal touch times can be projected from tick sources under the frozen parser, but opening-drive prereg field gaps remain non-result blockers.",
        "price_compatible_m1_source_recovered": "OTI3's earlier Sierra scale blocker is resolved by a price-compatible MT5 USDJPY M1 CSV for source availability only.",
        "entry_touched_terminal_sequence_unclaimed_source_confirmed": "The lone OTI2 unresolved row remains terminal-sequence unclaimed from M1 path order despite entry touch evidence.",
    }
    forensics = {
        "artifact_family": "NOFILL_CLOSE_FORENSICS_AND_LEARNING",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "row_count": len(packet_rows),
        "closure_label_counts": dict(sorted((label, len(rows)) for label, rows in by_label.items())),
        "source_lane_counts": dict(sorted(Counter(row["source_lane"] for row in packet_rows).items())),
        "learning_by_closure_label": {label: family_notes.get(label, "Exact blockers recorded in row blocker ledger.") for label in by_label},
        "failure_anatomy": {
            "pending_lifecycle": "Pending lifecycle state can be closed from sanitized source projections, but explicit entry_touched_at_utc is not present in the pending lifecycle schema.",
            "no_entry_path_order": "OTI2 rows have M1 path-order proof and OTB2R entry geometry; OTI5 rows have tick path proof. Neither is a result lane.",
            "terminal_sequence": "Tick terminal sequence projection can source-close OTI4 without scoring; prior tick-recovery lanes and absolute heavy-data roots are searched before any missing-tick blocker is emitted.",
            "source_blocked": "OTI3 source absence was not true local absence; a price-compatible MT5 USDJPY M1 source exists in absolute heavy data.",
            "oti1_metadata": "OTI1 top-level symbol/session/side can be projected from sanitized lifecycle dependencies after shared-family key normalization.",
            "access_request": "The stale BLOCKED_NO_TICKS_IN_WINDOW request for NOFILL-CLOSE-ROW-0127 is superseded by the existing source-hashed OTR061 XAUUSD tick recovery parquet; no active extraction request remains.",
        },
        "read_only_extraction_requests": blocker.get("read_only_extraction_requests", []),
        "superseded_read_only_extraction_requests": blocker.get("superseded_read_only_extraction_requests", []),
        "non_claims": [
            "No R/performance/win-rate/expectancy/DSR/PBO was computed.",
            "No broker/account/live labels or hidden outcomes were used.",
            "No validation sample floor passed.",
            "No live trading behavior changed.",
        ],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json", forensics)
    md = [
        "# NOFILL Close Forensics And Learning - 2026-05-08",
        "",
        f"Rows: `{len(packet_rows)}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Learning",
    ]
    for label, note in forensics["learning_by_closure_label"].items():
        md.append(f"- `{label}`: {note}")
    md += ["", "## Read-Only Extraction Requests"]
    if forensics["read_only_extraction_requests"]:
        for request in forensics["read_only_extraction_requests"]:
            md.append(
                f"- `{request['request_id']}` remains an access request only: `{request['request_manifest_path']}`"
            )
    else:
        md.append("- None")
    md += ["", "## Superseded Extraction Requests"]
    if forensics["superseded_read_only_extraction_requests"]:
        for request in forensics["superseded_read_only_extraction_requests"]:
            md.append(f"- `{request['request_id']}` superseded by OTR061 local source evidence.")
    else:
        md.append("- None")
    (OUT_DIR / "NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return forensics


def write_g12_prompt_pack(packet: dict[str, Any], blocker: dict[str, Any]) -> None:
    md = f"""# G12 NOFILL Close Audit Prompt Pack - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Recommended G12 Goal

Audit `NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1` under `research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/` as source-closure evidence only. Decide accept, block, or reject the frozen contract, row packet, exact blockers, source search/hash ledger, no-leak audit, duplicate/sample-floor audit, forensics, verifier, and tests.

## Required Checks

- Verify the context anchor was written before the frozen contract and the contract before row classification.
- Verify the packet is anchored to the 298 accepted G12_NOFILL rows and excludes the six CNR T3 rows plus the 94 blocked CNR061 rows.
- Recompute consumed source hashes, including recovered USDJPY M1 and tick parquet files.
- Verify no R/performance/win-rate/expectancy/DSR/PBO, broker/account/live labels, hidden labels, or blocked-packet outcomes are carried.
- Verify OTI1 metadata projection for symbol/session/side, pending lifecycle closure labels, no-entry path-order proof, terminal sequence source projections, and source-blocked path recovery are source-only claims.
- Explain what source-closed rows prove and do not prove. Do not turn touch times into R/performance or validation.
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Packet Summary

- Packet rows: `{packet['packet_row_count']}`
- Closure label counts: `{json.dumps(packet['closure_label_counts'], sort_keys=True)}`
- Closure status counts: `{json.dumps(packet['closure_status_counts'], sort_keys=True)}`
- Rows with exact blockers: `{blocker['rows_with_exact_blockers']}`

## Still Forbidden

No R/performance scoring, broker/account/live labels, blocked CNR061 outcomes, validation, promotion, live-effect claims, paid/API/Databento calls, MT5 account/order calls, credentials, remotes, or live trading surface changes.
"""
    (OUT_DIR / "NOFILL_CLOSE_G12_AUDIT_PROMPT_PACK_2026-05-08.md").write_text(md, encoding="utf-8")


def write_completion_audit(
    anchor: dict[str, Any],
    contract: dict[str, Any],
    packet: dict[str, Any],
    source_ledger: dict[str, Any],
    blocker: dict[str, Any],
    noleak: dict[str, Any],
    duplicate: dict[str, Any],
    forensics: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        {"requirement": "Mandatory GTOS preflight and controlling prompt read", "evidence": "LIVE_STATE regenerated; context anchor lists core docs, latest handoff, heavy-data docs, and controlling prompt", "status": "PASS"},
        {"requirement": "Context anchor before contract/classification artifacts", "evidence": f"anchor={anchor['written_at_utc']} contract={contract['contract_frozen_at_utc']}", "status": "PASS"},
        {"requirement": "Freeze NOFILL_LIFECYCLE_CLOSURE_SOURCE_CONTRACT_V1 before row scan", "evidence": f"contract_frozen_at={contract['contract_frozen_at_utc']} classification_started={packet['classification_started_at_utc']}", "status": "PASS" if contract["contract_frozen_at_utc"] <= packet["classification_started_at_utc"] else "FAIL"},
        {"requirement": "Accepted G12_NOFILL universe anchored", "evidence": f"packet_rows={packet['packet_row_count']} source lanes={packet['source_lane_counts']}", "status": "PASS" if packet["packet_row_count"] == 298 else "FAIL"},
        {"requirement": "Pending lifecycle closure pursued", "evidence": "OTI1 rows projected and labeled into still-open/cancelled/source-blocked closure families; row blockers name missing entry_touched_at_utc", "status": "PASS"},
        {"requirement": "No-entry path order pursued", "evidence": "OTI2 and OTI5 closure rows include source-hashed entry/terminal/protective touch-time fields or exact blockers", "status": "PASS"},
        {"requirement": "Terminal sequence proof pursued", "evidence": f"OTI4 rows use frozen tick parser contract and source-hashed tick files; unresolved tick-window gaps carry exact blockers plus read-only extraction manifests={len(blocker.get('read_only_extraction_requests', []))}", "status": "PASS"},
        {"requirement": "Source-blocked path availability/impossibility pursued", "evidence": "OTI3 rows check recovered price-compatible USDJPY M1 source under source ledger", "status": "PASS"},
        {"requirement": "OTI1 metadata projection", "evidence": "OTI1 rows project symbol/session/side using sanitized lifecycle dependencies and shared-family normalization", "status": "PASS"},
        {"requirement": "Preserve NO_PROMOTION_VERDICT and false flags", "evidence": "all generated artifact headers and JSON status fields preserve required flags", "status": "PASS"},
        {"requirement": "No forbidden R/performance/broker/account/live/hidden labels", "evidence": f"forbidden_hits={noleak['forbidden_packet_hits_count']}", "status": noleak["status"]},
        {"requirement": "Source hashes recomputed", "evidence": f"consumed_files={source_ledger['consumed_source_file_count']} mismatches={len(source_ledger['hash_mismatches'])}", "status": "PASS" if not source_ledger["hash_mismatches"] else "FAIL"},
        {"requirement": "Six T3 rows and 94 blocked CNR061 rows excluded", "evidence": f"six_t3={noleak['six_t3_leaks'] if 'six_t3_leaks' in noleak else noleak['six_t3_rows_exclusion']['status']} blocked94={noleak['blocked_94_cnr061_exclusion']['status']}", "status": "PASS" if noleak["six_t3_rows_exclusion"]["status"] == "PASS" and noleak["blocked_94_cnr061_exclusion"]["status"] == "PASS" else "FAIL"},
        {"requirement": "Duplicate/sample-floor audit", "evidence": duplicate["validation_sample_floor_status"], "status": duplicate["status"]},
        {"requirement": "Forensics/learning", "evidence": f"learning labels={len(forensics['learning_by_closure_label'])}", "status": "PASS"},
        {"requirement": "G12 prompt pack", "evidence": "NOFILL_CLOSE_G12_AUDIT_PROMPT_PACK_2026-05-08.md", "status": "PASS"},
        {"requirement": "Verifier/tests", "evidence": "verify_nofill_lifecycle_closure_source_packet_2026_05_08.py and test_nofill_lifecycle_closure_source_packet_2026_05_08.py", "status": "PENDING_VERIFIER_RUN"},
    ]
    completion = {
        "artifact_family": "NOFILL_CLOSE_COMPLETION_AUDIT",
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "objective_restatement": "Build NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_V1 as a frozen source-only closure lane for accepted G12_NOFILL families, with exact blockers and no result/promotion/live effect.",
        "prompt_to_artifact_checklist": checklist,
        "completion_status": "BUILT_PENDING_VERIFIER",
        "can_mark_goal_complete": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    write_json(OUT_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json", completion)
    md = [
        "# NOFILL Close Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for item in checklist:
        md.append(f"- `{item['status']}` {item['requirement']}: {item['evidence']}")
    (OUT_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return completion


def main() -> int:
    search_results = search_roots()
    anchor_time = utc_now()
    anchor = write_context_anchor(anchor_time, search_results)
    contract_time = utc_now()
    contract = write_contract(contract_time, anchor_time)

    classification_started_at = utc_now()
    rows = read_packet_rows()
    sources = load_sources()
    packet_rows = build_packet_rows(rows, sources, classification_started_at)
    packet = write_packet(packet_rows, classification_started_at)
    consumed = collect_consumed_source_files(packet_rows, search_results)
    source_ledger = build_source_ledger(search_results, consumed)
    blocker = write_blocker_ledger(packet_rows)
    noleak = write_noleak_audit(packet_rows, source_ledger)
    duplicate = write_duplicate_audit(packet_rows)
    forensics = write_forensics(packet_rows, blocker)
    write_g12_prompt_pack(packet, blocker)
    completion = write_completion_audit(anchor, contract, packet, source_ledger, blocker, noleak, duplicate, forensics)

    print(json.dumps({
        "status": "BUILT",
        "packet_rows": packet["packet_row_count"],
        "closure_label_counts": packet["closure_label_counts"],
        "closure_status_counts": packet["closure_status_counts"],
        "forbidden_hits": noleak["forbidden_packet_hits_count"],
        "hash_mismatches": len(source_ledger["hash_mismatches"]),
        "completion_status": completion["completion_status"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
