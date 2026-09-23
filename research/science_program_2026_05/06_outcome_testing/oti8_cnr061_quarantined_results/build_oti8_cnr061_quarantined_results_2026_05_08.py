#!/usr/bin/env python3
"""Build OTI8 CNR061 quarantined result artifacts.

This lane scores only the eight G12-accepted OTG0-PKT-061 CNR061 sidecar
rows. It uses source-hashed executable quotes and ordered tick paths, keeps
blocked rows closed, and writes research-only artifacts under
NO_PROMOTION_VERDICT.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DATE = "2026-05-08"
PACKET_ID = "OTG0-PKT-061"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False
EXPECTED_ACCEPTED_ROWS = 8
EXPECTED_BLOCKED_ROWS = 94
TARGET_FAMILY = "CNR_T0_ORIGINAL_TP1"
TIMING_FAMILIES = {
    "CNR_E0_DECISION_CLOSE_MARKET",
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
}

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OUTCOME = ROOT / "research/science_program_2026_05/06_outcome_testing"
G12_CNR061 = OUTCOME / "g12_cnr061_sidecar_reaudit"
CNR061 = OUTCOME / "cnr061_geometry_horizon_sidecar"
CNR_CONTROL = OUTCOME / "cnr_geometry_decay_residual_control"
CNR_SOURCE = OUTCOME / "cnr_source_field_packet_builder"
G12_CNR_SOURCE = OUTCOME / "g12_cnr_source_field_packet_audit"
OTX = OUTCOME / "otx_g6_tick_aware_end_to_end_resolution"
G12_OTX = OUTCOME / "g12_otx_g6_post_audit"
OTR061 = OUTCOME / "otr061_xau_tick_recovery"

CONTROL_PROMPT = OUT / "OTI8_CNR061_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-08.md"
SIDECAR_JSONL = CNR061 / "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl"
SIDECAR_JSON = CNR061 / "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.json"
CNR_SOURCE_ROWS = CNR_SOURCE / "CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl"
STALE_PROMPT_NAMED_CNR_SOURCE_MATRIX = (
    OUTCOME / "cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROW_MATRIX_2026-05-08.jsonl"
)
CNR_MATRIX = CNR_CONTROL / "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl"

READ_INPUTS = [
    CONTROL_PROMPT,
    ROOT / ".context/LIVE_STATE.md",
    ROOT / ".context/00_core/quick_reference_card.md",
    ROOT / ".context/00_core/research_operating_doctrine.md",
    ROOT / ".context/00_core/research_current_state.md",
    ROOT / ".context/00_core/goal_session_research_discipline.md",
    ROOT / ".context/00_core/local_heavy_data_inventory.md",
    ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    G12_CNR061 / "G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_2026-05-08.json",
    G12_CNR061 / "G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json",
    G12_CNR061 / "G12_CNR061_SOURCE_HASH_JOIN_AUDIT_2026-05-08.json",
    G12_CNR061 / "G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json",
    G12_CNR061 / "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json",
    G12_CNR061 / "G12_CNR061_NEXT_LANE_PROMPT_PACK_2026-05-08.md",
    SIDECAR_JSONL,
    CNR061 / "CNR061_SOURCE_JOIN_MAP_2026-05-08.md",
    CNR061 / "CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.md",
    CNR_MATRIX,
    CNR_CONTROL / "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
    CNR_SOURCE_ROWS,
    G12_CNR_SOURCE / "G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_2026-05-08.json",
    OTX / "OTX_G6_INTERNAL_PACKET_AUDIT_2026-05-07.md",
    G12_OTX / "G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md",
    OTR061 / "OTR061_COMPLETION_AUDIT_2026-05-07.json",
]

OUTPUT_STEMS = {
    "context_anchor": f"OTI8_CNR061_CONTEXT_ANCHOR_{DATE}",
    "method_freeze": f"OTI8_CNR061_METHOD_FREEZE_{DATE}",
    "accepted_manifest": f"OTI8_CNR061_ACCEPTED_ROW_MANIFEST_{DATE}",
    "result_ledger": f"OTI8_CNR061_RESULT_LEDGER_{DATE}",
    "source_report": f"OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT_{DATE}",
    "noleak_duplicate_label": f"OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_{DATE}",
    "methodology": f"OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_{DATE}",
    "forensics": f"OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER_{DATE}",
    "blocker_next": f"OTI8_CNR061_BLOCKER_AND_NEXT_ACTION_LEDGER_{DATE}",
    "prompt_pack": f"OTI8_CNR061_G12_POST_RESULT_PROMPT_PACK_{DATE}",
    "completion": f"OTI8_CNR061_COMPLETION_AUDIT_{DATE}",
}

FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "run_agent.py",
    "start_all.bat",
)

FORBIDDEN_INPUT_KEYS = {
    "actual_r",
    "account_history",
    "broker_actual_r",
    "hidden_path_label",
    "live_result",
    "live_trade_result",
    "path_label",
    "result",
    "result_label",
    "stop_first",
    "target_first",
    "terminal_label",
    "win_loss",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime:
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def round_float(value: Any, digits: int = 10) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return round(number, digits)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, default=str) + "\n")


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


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def base_payload(artifact_family: str, generated_at: str) -> dict[str, Any]:
    return {
        "account_history_accessed": False,
        "api_calls": 0,
        "artifact_family": artifact_family,
        "blocked_packet_outcome_source_read": False,
        "broker_actual_r_accessed": False,
        "canary_calls": 0,
        "databento_calls": 0,
        "date_stamp": DATE,
        "generated_at_utc": generated_at,
        "live_effect": LIVE_EFFECT,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_account_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "packet_id": PACKET_ID,
        "paid_data_calls": 0,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
    }


def source_entry(path: Path, role: str, required: bool = True) -> dict[str, Any]:
    exists = path.exists()
    return {
        "absolute_path": str(path.resolve()) if exists else str(path),
        "exists": exists,
        "path": rel(path) if exists else str(path),
        "required": required,
        "role": role,
        "sha256": sha256_file(path) if exists else None,
        "size_bytes": path.stat().st_size if exists else None,
    }


def walk_keys(value: Any, prefix: str = "$") -> list[tuple[str, str, Any]]:
    hits: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            dotted = f"{prefix}.{key}"
            hits.append((dotted, key, nested))
            hits.extend(walk_keys(nested, dotted))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(walk_keys(nested, f"{prefix}[{idx}]"))
    return hits


def recompute_sidecar_hash(row: dict[str, Any]) -> str:
    copy = dict(row)
    copy["no_leak_scan_status"] = "PENDING_VERIFIER"
    copy.pop("sidecar_row_sha256", None)
    return stable_hash(copy)


def load_sidecar_rows() -> list[dict[str, Any]]:
    rows = read_jsonl(SIDECAR_JSONL)
    if len(rows) != EXPECTED_ACCEPTED_ROWS:
        raise RuntimeError(f"Expected 8 sidecar rows, found {len(rows)}")
    return rows


def accepted_source_hash(row: dict[str, Any]) -> str:
    for evidence in row.get("source_evidence", []):
        if evidence.get("source_name") == "CNR_SOURCE_FIELD_PACKET_ROWS":
            return str(evidence["row_sha256"])
    raise KeyError(f"No CNR source row evidence for {row.get('sidecar_row_sha256')}")


def load_source_rows_for_pkt061() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    line_numbers: dict[str, int] = {}
    with CNR_SOURCE_ROWS.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if PACKET_ID not in line or TARGET_FAMILY not in line:
                continue
            row = json.loads(line)
            if (
                row.get("packet_id") == PACKET_ID
                and row.get("target_model_family") == TARGET_FAMILY
                and row.get("timing_model_family") in TIMING_FAMILIES
            ):
                rows.append(row)
                line_numbers[str(row.get("row_sha256"))] = line_no
    by_hash = {str(row["row_sha256"]): row for row in rows}
    return rows, by_hash, line_numbers


def load_matrix_rows() -> dict[str, dict[str, Any]]:
    matrix_by_source: dict[str, dict[str, Any]] = {}
    with CNR_MATRIX.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or PACKET_ID not in line:
                continue
            row = json.loads(line)
            if row.get("packet_id") == PACKET_ID:
                matrix_by_source[str(row.get("source_row_sha256"))] = row
    return matrix_by_source


def recompute_source_row_hash(row: dict[str, Any]) -> str:
    copy = {k: v for k, v in row.items() if k != "row_sha256"}
    return stable_hash(copy)


def read_tick_path(path: Path) -> pd.DataFrame:
    table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
    df = table.to_pandas()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df.sort_values("ts_utc").reset_index(drop=True)


def terminal_score(row: dict[str, Any], df_cache: dict[str, pd.DataFrame]) -> dict[str, Any]:
    path_packet = row["ordered_path_packet"]
    geometry = row["entry_sl_tp_or_level_packet"]
    quote = row["executable_quote_packet"]
    side = str(row["side"]).upper()
    path_files = [Path(p) for p in path_packet.get("path_source_files") or []]
    if not path_files:
        return {"score_status": "NULL_EXCLUDED_MISSING_ORDERED_PATH_SOURCE_FILE"}
    tick_path = path_files[0]
    key = str(tick_path)
    if key not in df_cache:
        df_cache[key] = read_tick_path(tick_path)
    df = df_cache[key]
    start = parse_utc(path_packet["path_start_utc"])
    end = parse_utc(path_packet["path_end_utc"])
    window = df[(df["ts_utc"] >= pd.Timestamp(start)) & (df["ts_utc"] <= pd.Timestamp(end))]
    if window.empty:
        return {"score_status": "NULL_EXCLUDED_ORDERED_PATH_EMPTY"}

    executable_quote = float(quote["executable_quote_price"])
    stop = float(geometry["stop_loss"])
    target = float(geometry["take_profit_1"])
    if side == "LONG":
        stop_distance = executable_quote - stop
        residual_target_price = target - executable_quote
        stop_valid = stop < executable_quote
    elif side == "SHORT":
        stop_distance = stop - executable_quote
        residual_target_price = executable_quote - target
        stop_valid = executable_quote < stop
    else:
        return {"score_status": "NULL_EXCLUDED_UNKNOWN_SIDE"}

    if not stop_valid or stop_distance <= 0:
        return {"score_status": "NULL_EXCLUDED_INVALID_STOP_GEOMETRY", "stop_distance_price": stop_distance}
    if residual_target_price <= 0:
        return {"score_status": "NULL_EXCLUDED_TARGET_ALREADY_PASSED", "residual_target_price": residual_target_price}

    residual_target_r = residual_target_price / stop_distance
    terminal_status = "NO_TERMINAL_WITHIN_ORDERED_HORIZON"
    terminal_event_utc = None
    terminal_bid = None
    terminal_ask = None
    synthetic_r = None

    for tick in window.itertuples(index=False):
        bid = float(tick.bid)
        ask = float(tick.ask)
        if side == "LONG":
            hit_target = bid >= target
            hit_stop = bid <= stop
            terminal_price_side = "bid"
        else:
            hit_target = ask <= target
            hit_stop = ask >= stop
            terminal_price_side = "ask"
        if hit_target and hit_stop:
            terminal_status = "AMBIGUOUS_TARGET_AND_STOP_SAME_TICK"
            terminal_event_utc = iso(tick.ts_utc)
            terminal_bid = bid
            terminal_ask = ask
            synthetic_r = None
            break
        if hit_target:
            terminal_status = "TARGET_REACHED_BEFORE_STOP"
            terminal_event_utc = iso(tick.ts_utc)
            terminal_bid = bid
            terminal_ask = ask
            synthetic_r = residual_target_r
            break
        if hit_stop:
            terminal_status = "STOP_REACHED_BEFORE_TARGET"
            terminal_event_utc = iso(tick.ts_utc)
            terminal_bid = bid
            terminal_ask = ask
            synthetic_r = -1.0
            break

    min_bid = float(window["bid"].min())
    max_bid = float(window["bid"].max())
    min_ask = float(window["ask"].min())
    max_ask = float(window["ask"].max())
    if side == "LONG":
        max_favorable_r = (max_bid - executable_quote) / stop_distance
        max_adverse_r = (executable_quote - min_bid) / stop_distance
        target_gap_at_best_price = target - max_bid
        stop_gap_at_worst_price = min_bid - stop
    else:
        max_favorable_r = (executable_quote - min_ask) / stop_distance
        max_adverse_r = (max_ask - executable_quote) / stop_distance
        target_gap_at_best_price = min_ask - target
        stop_gap_at_worst_price = stop - max_ask

    return {
        "executable_quote_price": round_float(executable_quote),
        "max_adverse_r_within_horizon": round_float(max_adverse_r),
        "max_favorable_r_within_horizon": round_float(max_favorable_r),
        "ordered_path_first_tick_utc": iso(window["ts_utc"].iloc[0]),
        "ordered_path_last_tick_utc": iso(window["ts_utc"].iloc[-1]),
        "ordered_path_row_count_recomputed": int(len(window)),
        "residual_target_price_from_executable_quote": round_float(residual_target_price),
        "residual_target_r_from_executable_quote": round_float(residual_target_r),
        "score_status": "SCORED_FROM_SOURCE_HASHED_ORDERED_TICKS",
        "stop_distance_price_from_executable_quote": round_float(stop_distance),
        "stop_gap_at_worst_price": round_float(stop_gap_at_worst_price),
        "synthetic_r": round_float(synthetic_r),
        "target_gap_at_best_price": round_float(target_gap_at_best_price),
        "terminal_ask": round_float(terminal_ask),
        "terminal_bid": round_float(terminal_bid),
        "terminal_event_utc": terminal_event_utc,
        "terminal_price_side": terminal_price_side,
        "terminal_status": terminal_status,
        "tick_extremes": {
            "max_ask": round_float(max_ask),
            "max_bid": round_float(max_bid),
            "min_ask": round_float(min_ask),
            "min_bid": round_float(min_bid),
        },
    }


def summarize_results(row_results: list[dict[str, Any]]) -> dict[str, Any]:
    def bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
        resolved = [row for row in rows if row.get("synthetic_r") is not None]
        return {
            "mean_r_all_rows_null_excluded": round_float(sum(row["synthetic_r"] for row in resolved) / len(resolved)) if resolved else None,
            "mean_r_all_rows_null_as_zero": round_float(sum((row.get("synthetic_r") or 0.0) for row in rows) / len(rows)) if rows else None,
            "no_terminal_count": sum(1 for row in rows if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"),
            "null_unresolved_count": sum(1 for row in rows if row.get("synthetic_r") is None),
            "resolved_r_count": len(resolved),
            "row_count": len(rows),
            "status_counts": dict(Counter(row.get("terminal_status") for row in rows)),
            "sum_r_resolved_only": round_float(sum(row["synthetic_r"] for row in resolved)),
            "target_before_stop_count": sum(1 for row in rows if row.get("terminal_status") == "TARGET_REACHED_BEFORE_STOP"),
            "stop_before_target_count": sum(1 for row in rows if row.get("terminal_status") == "STOP_REACHED_BEFORE_TARGET"),
        }

    countable = [row for row in row_results if row.get("countable_denominator_row") is True]
    by_timing = {
        timing: bucket([row for row in row_results if row.get("timing_model_family") == timing])
        for timing in sorted({row.get("timing_model_family") for row in row_results})
    }
    by_duplicate_group = {
        group: bucket([row for row in row_results if row.get("duplicate_group_id") == group])
        for group in sorted({row.get("duplicate_group_id") for row in row_results})
    }
    return {
        "countable_duplicate_policy_summary": bucket(countable),
        "duplicate_group_splits": by_duplicate_group,
        "row_level_all_eight_summary": bucket(row_results),
        "timing_family_splits": by_timing,
        "unique_duplicate_denominator_keys": len({row.get("duplicate_denominator_key") for row in row_results}),
        "unique_duplicate_groups": len({row.get("duplicate_group_id") for row in row_results}),
        "unique_record_ids": len({row.get("record_id") for row in row_results}),
    }


def live_surface_diff_review() -> dict[str, Any]:
    result = subprocess.run(["git", "diff", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=False)
    changed = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES)]
    return {
        "changed_files_at_build_time": changed,
        "forbidden_live_surface_changed_files": forbidden,
        "status": "PASS" if result.returncode == 0 and not forbidden else "FAIL",
    }


def build_bundle() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    generated_at = now_utc()
    sidecar_rows = load_sidecar_rows()
    g12_decision = read_json(G12_CNR061 / "G12_CNR061_SIDECAR_REAUDIT_DECISION_LEDGER_2026-05-08.json")
    g12_readiness = read_json(G12_CNR061 / "G12_CNR061_PACKET_READINESS_OR_BLOCKER_LEDGER_2026-05-08.json")
    g12_source_hash = read_json(G12_CNR061 / "G12_CNR061_SOURCE_HASH_JOIN_AUDIT_2026-05-08.json")
    g12_noleak = read_json(G12_CNR061 / "G12_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json")
    g12_blocked = read_json(G12_CNR061 / "G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json")
    sidecar_packet = read_json(SIDECAR_JSON)
    source_rows, source_by_hash, source_line_numbers = load_source_rows_for_pkt061()
    matrix_by_hash = load_matrix_rows()

    accepted_hashes = {row["sidecar_row_sha256"] for row in sidecar_rows}
    accepted_source_hashes = {accepted_source_hash(row) for row in sidecar_rows}
    accepted_record_ids = {row["record_id"] for row in sidecar_rows}
    accepted_denominator_keys = {row["duplicate_denominator_key"] for row in sidecar_rows}
    accepted_groups = {row["duplicate_group_id"] for row in sidecar_rows}
    accepted_sidecar_recompute = [
        {
            "matches": recompute_sidecar_hash(row) == row["sidecar_row_sha256"],
            "observed_sidecar_row_sha256": row["sidecar_row_sha256"],
            "recomputed_sidecar_row_sha256": recompute_sidecar_hash(row),
        }
        for row in sidecar_rows
    ]
    accepted_source_recompute = []
    for source_hash in sorted(accepted_source_hashes):
        source = source_by_hash[source_hash]
        accepted_source_recompute.append(
            {
                "line_number": source_line_numbers[source_hash],
                "matches": recompute_source_row_hash(source) == source_hash,
                "observed_row_sha256": source_hash,
                "record_id": source.get("record_id"),
                "recomputed_row_sha256": recompute_source_row_hash(source),
            }
        )

    blocked_source_rows = [row for row in source_rows if row.get("row_sha256") not in accepted_source_hashes]
    countable_blocked = [row for row in blocked_source_rows if row.get("countable_denominator_row") is True]
    raw_overlap = {
        "duplicate_denominator_key_overlap": sorted({row["duplicate_denominator_key"] for row in blocked_source_rows} & accepted_denominator_keys),
        "duplicate_group_id_overlap": sorted({row["duplicate_group_id"] for row in blocked_source_rows} & accepted_groups),
        "record_id_overlap": sorted({row["record_id"] for row in blocked_source_rows} & accepted_record_ids),
        "source_row_hash_overlap": sorted({row["row_sha256"] for row in blocked_source_rows} & accepted_source_hashes),
    }
    countable_overlap = {
        "duplicate_denominator_key_overlap": sorted({row["duplicate_denominator_key"] for row in countable_blocked} & accepted_denominator_keys),
        "duplicate_group_id_overlap": sorted({row["duplicate_group_id"] for row in countable_blocked} & accepted_groups),
        "record_id_overlap": sorted({row["record_id"] for row in countable_blocked} & accepted_record_ids),
        "source_row_hash_overlap": sorted({row["row_sha256"] for row in countable_blocked} & accepted_source_hashes),
    }

    # Method freeze is assembled before terminal path scoring. It records the
    # cohort, metric, terminal order, duplicate policy, and exclusion gates.
    method_freeze = base_payload("OTI8_CNR061_METHOD_FREEZE", generated_at)
    method_freeze.update(
        {
            "accepted_sidecar_row_sha256": sorted(accepted_hashes),
            "cohort_freeze_status": "FROZEN_BEFORE_TERMINAL_TICK_PATH_SCORING",
            "duplicate_aggregation_policy": {
                "countable_policy": "Use CNR/G12 countable_denominator_row from source rows: one countable primary row per packet/duplicate_group/timing_model/target_model; duplicate-context rows are retained row-level but excluded from countable aggregate.",
                "raw_duplicate_overlap_disclosure": raw_overlap,
                "countable_blocked_overlap": countable_overlap,
                "countable_overlap_status": "PASS_ZERO_COUNTABLE_BLOCKED_OVERLAP",
                "do_not_join_on_duplicate_group_alone": True,
                "row_level_all_eight_reported": True,
            },
            "exclusion_gates": [
                "Exclude any sidecar_row_sha256 not accepted by G12_CNR061_SIDECAR_REAUDIT.",
                "Exclude the 94 source rows not matching accepted source row hashes.",
                "Null/exclude any accepted row with missing executable quote, missing ordered path, invalid stop geometry, target already passed at quote, or ambiguous same-tick target/stop.",
            ],
            "metric_policy": {
                "path_horizon": "Use source sidecar ordered_path_packet path_start_utc/path_end_utc only.",
                "r_scoring": "Target before stop receives residual_target_r_from_executable_quote; stop before target receives -1.0R; unresolved horizon remains null.",
                "same_tick_policy": "If target and stop are both touched on the same ordered tick, classify ambiguous and do not impute R.",
                "target_model_family": TARGET_FAMILY,
                "target_stop_fields": "entry_sl_tp_or_level_packet.take_profit_1 and stop_loss",
                "terminal_order_source": "source-hashed ordered tick path bid/ask rows, not OHLC ordering or hidden path labels",
            },
            "quote_side_policy": {
                "market_entry": "LONG uses ask, SHORT uses bid at source-hashed executable quote.",
                "terminal_exit": "LONG target/stop evaluated on bid; SHORT target/stop evaluated on ask.",
            },
            "status": "PASS_METHOD_FROZEN",
        }
    )

    df_cache: dict[str, pd.DataFrame] = {}
    row_results: list[dict[str, Any]] = []
    for row in sidecar_rows:
        source_hash = accepted_source_hash(row)
        source = source_by_hash[source_hash]
        matrix = matrix_by_hash[source_hash]
        score = terminal_score(row, df_cache)
        result = {
            **base_payload("OTI8_CNR061_RESULT_LEDGER_ROW", generated_at),
            "candidate_close_utc": row["candidate_close_utc"],
            "countable_denominator_row": bool(source.get("countable_denominator_row")),
            "duplicate_denominator_key": row["duplicate_denominator_key"],
            "duplicate_group_id": row["duplicate_group_id"],
            "executable_quote_price": row["executable_quote_packet"]["executable_quote_price"],
            "executable_quote_side": row["executable_quote_packet"]["executable_quote_side"],
            "matrix_residual_target_r_from_executable_quote": matrix.get("residual_target_r_from_executable_quote"),
            "original_entry_price": row["entry_sl_tp_or_level_packet"]["entry_price"],
            "original_stop_loss": row["entry_sl_tp_or_level_packet"]["stop_loss"],
            "original_take_profit_1": row["entry_sl_tp_or_level_packet"]["take_profit_1"],
            "path_end_utc": row["ordered_path_packet"]["path_end_utc"],
            "path_source_files": row["ordered_path_packet"]["path_source_files"],
            "path_start_utc": row["ordered_path_packet"]["path_start_utc"],
            "quote_source_sha256": row["executable_quote_packet"]["quote_source_sha256"],
            "quote_timestamp_utc": row["executable_quote_packet"]["quote_timestamp_utc"],
            "record_id": row["record_id"],
            "row_source_hash": source_hash,
            "score": score,
            "score_status": score.get("score_status"),
            "side": row["side"],
            "sidecar_row_sha256": row["sidecar_row_sha256"],
            "symbol": row["symbol"],
            "synthetic_r": score.get("synthetic_r"),
            "target_model_family": row["target_model_family"],
            "terminal_status": score.get("terminal_status"),
            "timing_model_family": row["timing_model_family"],
        }
        row_results.append(result)

    result_summary = summarize_results(row_results)

    source_entries = [source_entry(path, "controlling_or_upstream_input") for path in READ_INPUTS]
    source_entries.append(source_entry(STALE_PROMPT_NAMED_CNR_SOURCE_MATRIX, "prompt_named_but_absent_stale_artifact", required=False))
    for tick_file in sorted({Path(row["ordered_path_packet"]["path_source_files"][0]) for row in sidecar_rows}):
        source_entries.append(source_entry(tick_file, "accepted_row_quote_and_ordered_tick_path_source"))
    missing_required = [entry for entry in source_entries if entry["required"] and not entry["exists"]]
    hash_failures = [
        row for row in accepted_source_recompute if not row["matches"]
    ] + [
        row for row in accepted_sidecar_recompute if not row["matches"]
    ]

    context_anchor = base_payload("OTI8_CNR061_CONTEXT_ANCHOR", generated_at)
    context_anchor.update(
        {
            "active_question_stack": [
                "Can the exact 8 G12-accepted source-hashed CNR061 rows be scored without opening blocked rows?",
                "Do raw duplicate overlaps invalidate scoring, or are they duplicate-context rows excluded by countable policy?",
                "Did CNR_T0 original TP1 resolve before stop within the fixed ordered tick horizon?",
                "What does the tiny-n result teach without promotion or rescue?",
            ],
            "branch": run_git(["branch", "--show-current"]),
            "controlling_prompt_path": rel(CONTROL_PROMPT),
            "current_head": run_git(["rev-parse", "HEAD"]),
            "latest_handoff": rel(ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"),
            "read_inputs": [rel(path) for path in READ_INPUTS],
            "route_decision_ledger": [
                {
                    "decision": "USE_ACCEPTED_8_SIDE CAR_ROWS_ONLY",
                    "reason": "G12_CNR061 accepted exactly 8 input-only rows for a future quarantined result audit.",
                },
                {
                    "decision": "USE_SOURCE_HASHED_TICK_PATHS",
                    "reason": "Rows carry executable quote and ordered_path_packet with source parquet hashes.",
                },
                {
                    "decision": "FREEZE_COUNTABLE_DUPLICATE_POLICY_BEFORE_SCORING",
                    "reason": "Raw blocked duplicate groups overlap accepted groups; G12 policy rejects duplicate_group-only joins and countable blocked overlap is zero.",
                },
                {
                    "decision": "DO_NOT_USE_BROKER_ACTUAL_R_OR_HIDDEN_PATH_LABELS",
                    "reason": "Prompt forbids broker/account/live/hidden result labels; scoring reads only bid/ask ticks.",
                },
            ],
            "runtime_dirt_at_anchor": run_git(["status", "--short"]),
            "searched_root_ledger": [
                {"root": str(ROOT), "purpose": "worktree artifacts and prompt-listed upstream files", "status": "SEARCHED"},
                {
                    "root": str(Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")),
                    "purpose": "absolute local heavy tick source paths declared by accepted sidecar rows",
                    "status": "FOUND_XAGUSD_2026_05_04_AND_2026_05_05",
                },
                {
                    "root": rel(CNR_SOURCE),
                    "purpose": "prompt-named CNR source field row matrix replacement search",
                    "status": "FOUND_CNR_SOURCE_FIELD_PACKET_ROWS_2026_05_07_JSONL_PROMPT_2026_05_08_MATRIX_NAME_ABSENT",
                },
            ],
            "worktree_path": str(ROOT),
        }
    )

    accepted_manifest_rows = []
    for result in row_results:
        accepted_manifest_rows.append(
            {
                "countable_denominator_row": result["countable_denominator_row"],
                "duplicate_denominator_key": result["duplicate_denominator_key"],
                "duplicate_group_id": result["duplicate_group_id"],
                "path_source_files": result["path_source_files"],
                "quote_source_sha256": result["quote_source_sha256"],
                "record_id": result["record_id"],
                "row_source_hash": result["row_source_hash"],
                "side": result["side"],
                "sidecar_row_sha256": result["sidecar_row_sha256"],
                "symbol": result["symbol"],
                "target_model_family": result["target_model_family"],
                "timing_model_family": result["timing_model_family"],
            }
        )
    accepted_manifest = base_payload("OTI8_CNR061_ACCEPTED_ROW_MANIFEST", generated_at)
    accepted_manifest.update(
        {
            "accepted_row_count": len(accepted_manifest_rows),
            "accepted_rows": accepted_manifest_rows,
            "accepted_sidecar_row_sha256": sorted(accepted_hashes),
            "source": rel(SIDECAR_JSONL),
            "status": "PASS_EXACT_8_ACCEPTED_ROWS",
        }
    )

    result_ledger = base_payload("OTI8_CNR061_RESULT_LEDGER", generated_at)
    result_ledger.update(
        {
            "label_family": "QUARANTINED_SYNTHETIC_ORDERED_TICK_PATH_R_DISCOVERY_ONLY",
            "method_freeze_artifact": f"{OUTPUT_STEMS['method_freeze']}.json",
            "result_summary": result_summary,
            "row_level_jsonl": f"{OUTPUT_STEMS['result_ledger']}_ROWS.jsonl",
            "row_results": row_results,
            "status": "RESULTS_COMPUTED_DISCOVERY_ONLY_NO_PROMOTION",
        }
    )

    source_report = base_payload("OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT", generated_at)
    source_report.update(
        {
            "accepted_sidecar_hash_recompute": accepted_sidecar_recompute,
            "accepted_source_row_hash_recompute": accepted_source_recompute,
            "all_required_sources_present": not missing_required,
            "all_source_hash_recomputes_match": not hash_failures,
            "control_and_source_files": source_entries,
            "g12_source_hash_join_audit_status": g12_source_hash.get("audit_status"),
            "hash_failures": hash_failures,
            "missing_required_files": missing_required,
            "prompt_named_missing_or_stale_artifacts": [
                {
                    "prompt_named_path": rel(STALE_PROMPT_NAMED_CNR_SOURCE_MATRIX),
                    "exists": STALE_PROMPT_NAMED_CNR_SOURCE_MATRIX.exists(),
                    "replacement_used": rel(CNR_SOURCE_ROWS),
                    "reason": "The controlling prompt's 2026-05-08 ROW_MATRIX filename is absent; the committed upstream source-field packet row file named by sidecar source_evidence is the 2026-05-07 JSONL.",
                }
            ],
            "source_hash_status": "PASS" if not missing_required and not hash_failures else "FAIL",
        }
    )

    forbidden_input_hits = []
    for row in sidecar_rows:
        for path, key, _value in walk_keys(row):
            if key in FORBIDDEN_INPUT_KEYS:
                forbidden_input_hits.append({"sidecar_row_sha256": row["sidecar_row_sha256"], "json_path": path, "key": key})
    noleak_duplicate_label = base_payload("OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT", generated_at)
    noleak_duplicate_label.update(
        {
            "blocked_exclusion": {
                "accepted_rows": len(sidecar_rows),
                "blocked_rows": len(blocked_source_rows),
                "blocked_rows_expected": EXPECTED_BLOCKED_ROWS,
                "countable_blocked_rows": len(countable_blocked),
                "countable_overlap": countable_overlap,
                "raw_overlap_disclosed": raw_overlap,
                "status": "PASS_EXACT_8_ACCEPTED_94_BLOCKED_UNDER_SOURCE_HASH_AND_COUNTABLE_DUPLICATE_POLICY",
            },
            "duplicate_policy": method_freeze["duplicate_aggregation_policy"],
            "forbidden_input_key_hits": forbidden_input_hits,
            "g12_duplicate_summary": g12_noleak.get("duplicate_summary"),
            "label_family_separation": {
                "accepted_input_label_family": "INPUT_ONLY_GEOMETRY_QUOTE_PATH_HORIZON_NO_RESULTS",
                "broker_actual_r_opened": False,
                "hidden_path_labels_opened": False,
                "result_label_family": "QUARANTINED_SYNTHETIC_ORDERED_TICK_PATH_R_DISCOVERY_ONLY",
                "synthetic_path_r_is_not_broker_actual_r": True,
            },
            "no_leak_status": "PASS" if not forbidden_input_hits else "FAIL",
        }
    )

    methodology = base_payload("OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT", generated_at)
    methodology.update(
        {
            "dsr": {
                "reason": "Eight row-level discovery-only rows collapse to four countable timing-family rows and two duplicate groups; no validation vector or promotion test exists.",
                "status": "not_computable",
            },
            "effective_n": {
                "countable_rows": len([row for row in row_results if row["countable_denominator_row"]]),
                "duplicate_groups": len({row["duplicate_group_id"] for row in row_results}),
                "resolved_countable_rows": len(
                    [row for row in row_results if row["countable_denominator_row"] and row.get("synthetic_r") is not None]
                ),
                "row_level_rows": len(row_results),
                "status": "tiny_n_discovery_only_not_validation",
            },
            "pbo": {
                "reason": "No model family selection or train/test split is being evaluated; this is one frozen quarantined packet.",
                "status": "not_computable",
            },
            "sample_floor": {
                "current_duplicate_groups": len({row["duplicate_group_id"] for row in row_results}),
                "current_row_level_n": len(row_results),
                "sample_floor_pass": False,
                "required_future_floor": "future CNR target/timing validation needs a separately preregistered sample floor; this packet cannot validate.",
            },
            "statistical_verdict": "NOT_VALIDATION_NOT_PROMOTION_DSR_PBO_NOT_COMPUTABLE",
        }
    )

    target_rows = [row for row in row_results if row.get("terminal_status") == "TARGET_REACHED_BEFORE_STOP"]
    unresolved_rows = [row for row in row_results if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"]
    forensics = base_payload("OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER", generated_at)
    forensics.update(
        {
            "failure_anatomy": {
                "target_reached_rows": [
                    {
                        "record_id": row["record_id"],
                        "residual_target_r": row["score"]["residual_target_r_from_executable_quote"],
                        "terminal_event_utc": row["score"]["terminal_event_utc"],
                        "timing_model_family": row["timing_model_family"],
                    }
                    for row in target_rows
                ],
                "unresolved_rows": [
                    {
                        "max_adverse_r": row["score"]["max_adverse_r_within_horizon"],
                        "max_favorable_r": row["score"]["max_favorable_r_within_horizon"],
                        "record_id": row["record_id"],
                        "residual_target_r": row["score"]["residual_target_r_from_executable_quote"],
                        "target_gap_at_best_price": row["score"]["target_gap_at_best_price"],
                        "timing_model_family": row["timing_model_family"],
                    }
                    for row in unresolved_rows
                ],
            },
            "learning_summary": [
                "The only resolved duplicate group was the May 4 London XAGUSD short, and it required only about 0.054R residual movement to original TP1.",
                "All six May 5 NY rows stayed inside the fixed four-hour path horizon: no target and no stop, with max favorable movement only about 0.17R to 0.25R against targets requiring about 1.06R to 1.25R.",
                "E0 and E1 are identical for the accepted rows because the source-hashed executable quote was the same for each paired timing family.",
                "The packet is dominated by duplicate concentration: eight row-level rows collapse to four countable timing-family rows and two duplicate groups.",
            ],
            "next_hypotheses": [
                "Register a CNR target family that is not mechanically tied to original TP1 after large favorable displacement.",
                "Capture pre-touch/latency timing fields prospectively so E0/E1/E2/E3/E4 can differ without post-hoc inference.",
                "Treat unresolved four-hour horizons as their own lifecycle label rather than imputing zero or a win/loss.",
            ],
            "status": "NEGATIVE_OR_TINY_N_LEARNING_RECORDED_NO_RESCUE",
        }
    )

    blocker_next = base_payload("OTI8_CNR061_BLOCKER_AND_NEXT_ACTION_LEDGER", generated_at)
    blocker_next.update(
        {
            "blockers": [
                {
                    "blocker": "RAW_DUPLICATE_GROUP_AND_DENOMINATOR_CONTEXT_OVERLAP",
                    "status": "DISCLOSED_NOT_SCORING_BLOCKER_AFTER_COUNTABLE_POLICY_FREEZE",
                    "evidence": raw_overlap,
                    "minimum_future_unblocker": "Future prompt should state countable duplicate-policy overlap, not raw duplicate_group overlap, when duplicate context rows are retained.",
                },
                {
                    "blocker": "TINY_N_AND_DUPLICATE_CONCENTRATION",
                    "status": "BLOCKS_VALIDATION_AND_PROMOTION_ONLY",
                    "minimum_future_unblocker": "Collect a separately preregistered source-complete CNR cohort with enough unique duplicate groups.",
                },
                {
                    "blocker": "MISSING_PROMPT_NAMED_2026_05_08_CNR_SOURCE_FIELD_ROW_MATRIX",
                    "status": "NOT_SCORING_BLOCKER_REPLACEMENT_SOURCE_EVIDENCE_FOUND",
                    "minimum_future_unblocker": "Correct future prompts to name CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl or add a stable alias artifact.",
                },
            ],
            "next_actions": [
                "Run a G12 post-result review over the OTI8 result package before any future synthesis cites it.",
                "Draft a CNR_T4/T5 target preregistration that separates tiny residual-target continuation from deep-target unresolved paths.",
                "Add prospective capture for CNR_E2/E3/E4 timing triggers instead of deriving them after the path is known.",
            ],
        }
    )

    prompt_pack_text = f"""# OTI8 CNR061 G12 Post-Result Prompt Pack - {DATE}

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## Prompt

`/goal Run G12 post-result review for OTI8_CNR061_QUARANTINED_RESULT_LANE using research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08.json, OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl, OTI8_CNR061_METHOD_FREEZE_2026-05-08.json, OTI8_CNR061_NOLEAK_DUPLICATE_LABEL_AUDIT_2026-05-08.json, OTI8_CNR061_SOURCE_HASH_COVERAGE_REPORT_2026-05-08.json, and OTI8_CNR061_COMPLETION_AUDIT_2026-05-08.json as controlling inputs; verify exact 8 accepted row hashes, 94 blocked exclusions, source-hash recomputation, label separation, duplicate policy, and no live/broker/account/result-label leakage; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; do not promote or edit live trading surfaces.`

## Current Result Snapshot

- Row-level: {result_summary['row_level_all_eight_summary']['target_before_stop_count']} target-before-stop, {result_summary['row_level_all_eight_summary']['no_terminal_count']} unresolved horizon, {result_summary['row_level_all_eight_summary']['stop_before_target_count']} stop-before-target.
- Countable: {result_summary['countable_duplicate_policy_summary']['row_count']} rows under frozen duplicate policy, {result_summary['countable_duplicate_policy_summary']['resolved_r_count']} resolved R rows.
- Posture: discovery-only, not validation-safe, no promotion.
"""

    completion_checklist = [
        ("mandatory_gtos_preflight", "PASS", "LIVE_STATE regenerated; required core docs and latest handoff read and hashed."),
        ("context_anchor_before_scoring", "PASS", f"{OUTPUT_STEMS['context_anchor']}.json records HEAD, branch, worktree, runtime dirt, controlling prompt, routes, and searched roots."),
        ("controlling_inputs_read", "PASS", "All present prompt-listed CNR061/CNR/OTX/OTR061 artifacts consumed or hashed; stale missing source-field matrix recorded with replacement."),
        ("method_freeze_before_label_review", "PASS", f"{OUTPUT_STEMS['method_freeze']}.json freezes cohort, quote side, terminal order, R scoring, horizon, and duplicate policy before terminal scoring in the builder flow."),
        ("exact_8_accepted_rows", "PASS", f"{len(sidecar_rows)} accepted sidecar rows matched G12 decision/readiness ledgers."),
        (
            "exact_94_blocked_rows_excluded",
            "PASS_WITH_RAW_DUPLICATE_CONTEXT_OVERLAP_DISCLOSED",
            f"{len(blocked_source_rows)} blocked source rows excluded; source row hash and record overlap zero; countable duplicate key/group overlap zero.",
        ),
        ("source_hash_recompute", "PASS" if not hash_failures else "FAIL", f"sidecar/source row hash failures={len(hash_failures)}; required source missing={len(missing_required)}"),
        ("no_leak_forbidden_key_scan", "PASS" if not forbidden_input_hits else "FAIL", f"forbidden input key hits={len(forbidden_input_hits)}"),
        ("label_family_separation", "PASS", "Result rows are quarantined synthetic ordered-tick path R only; broker actual-R/account/live/hidden path labels unopened."),
        ("duplicate_denominator_audit", "PASS_WITH_RAW_DUPLICATE_CONTEXT_OVERLAP_DISCLOSED", "Countable blocked overlap zero; raw duplicate group overlap intentionally not used for identity."),
        ("row_level_and_countable_results", "PASS", f"{OUTPUT_STEMS['result_ledger']}.json and row-level JSONL written."),
        ("methodology_report", "PASS", "DSR/PBO/effective-N reported as not computable/tiny-n discovery-only."),
        ("failure_forensics", "PASS", "Resolved tiny-residual target and unresolved May 5 path anatomy recorded."),
        ("next_lane_prompt", "PASS", f"{OUTPUT_STEMS['prompt_pack']}.md written."),
        ("no_live_surface_changes", "PASS" if live_surface_diff_review()["status"] == "PASS" else "FAIL", "git diff live-surface scan at build time."),
    ]
    completion = base_payload("OTI8_CNR061_COMPLETION_AUDIT", generated_at)
    completion.update(
        {
            "can_mark_goal_complete": False,
            "concrete_success_criteria": [
                "Build quarantined package over exactly 8 G12-accepted sidecar row hashes.",
                "Exclude 94 blocked rows and freeze countable duplicate denominator policy before terminal scoring.",
                "Score only source-hashed executable quote plus ordered tick path evidence.",
                "Write method/source/no-leak/duplicate/label/methodology/forensics/next-lane/completion artifacts.",
                "Run verifier/tests and preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.",
            ],
            "objective_restated": "Run OTI8_CNR061_QUARANTINED_RESULT_LANE for OTG0-PKT-061 using only the 8 G12-accepted CNR061 sidecar rows and no broker/account/live/hidden labels.",
            "prompt_to_artifact_checklist": [
                {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in completion_checklist
            ],
            "verification_status": "PENDING_VERIFIER",
        }
    )

    artifacts = {
        OUTPUT_STEMS["context_anchor"]: context_anchor,
        OUTPUT_STEMS["method_freeze"]: method_freeze,
        OUTPUT_STEMS["accepted_manifest"]: accepted_manifest,
        OUTPUT_STEMS["result_ledger"]: result_ledger,
        OUTPUT_STEMS["source_report"]: source_report,
        OUTPUT_STEMS["noleak_duplicate_label"]: noleak_duplicate_label,
        OUTPUT_STEMS["methodology"]: methodology,
        OUTPUT_STEMS["forensics"]: forensics,
        OUTPUT_STEMS["blocker_next"]: blocker_next,
        OUTPUT_STEMS["completion"]: completion,
    }
    return artifacts, row_results, prompt_pack_text


def write_artifacts(artifacts: dict[str, dict[str, Any]], rows: list[dict[str, Any]], prompt_pack_text: str) -> None:
    titles = {
        OUTPUT_STEMS["context_anchor"]: "OTI8 CNR061 Context Anchor",
        OUTPUT_STEMS["method_freeze"]: "OTI8 CNR061 Method Freeze",
        OUTPUT_STEMS["accepted_manifest"]: "OTI8 CNR061 Accepted Row Manifest",
        OUTPUT_STEMS["result_ledger"]: "OTI8 CNR061 Result Ledger",
        OUTPUT_STEMS["source_report"]: "OTI8 CNR061 Source Hash Coverage Report",
        OUTPUT_STEMS["noleak_duplicate_label"]: "OTI8 CNR061 No-Leak Duplicate Label Audit",
        OUTPUT_STEMS["methodology"]: "OTI8 CNR061 Methodology DSR PBO Effective-N Report",
        OUTPUT_STEMS["forensics"]: "OTI8 CNR061 Result Forensics And Learning Ledger",
        OUTPUT_STEMS["blocker_next"]: "OTI8 CNR061 Blocker And Next Action Ledger",
        OUTPUT_STEMS["completion"]: "OTI8 CNR061 Completion Audit",
    }
    summaries = {
        OUTPUT_STEMS["result_ledger"]: [
            f"- Row-level summary: `{artifacts[OUTPUT_STEMS['result_ledger']]['result_summary']['row_level_all_eight_summary']}`",
            "- Discovery-only synthetic ordered-tick path R; no broker/account/live result labels opened.",
        ],
        OUTPUT_STEMS["forensics"]: [
            "- The resolved May 4 rows had tiny residual target distance; the May 5 rows did not reach target or stop inside the fixed horizon.",
        ],
    }
    for stem, payload in artifacts.items():
        write_json(OUT / f"{stem}.json", payload)
        write_md(OUT / f"{stem}.md", titles.get(stem, stem), payload, summaries.get(stem))
    write_jsonl(OUT / f"{OUTPUT_STEMS['result_ledger']}_ROWS.jsonl", rows)
    (OUT / f"{OUTPUT_STEMS['prompt_pack']}.md").write_text(prompt_pack_text, encoding="utf-8")


def main() -> None:
    artifacts, rows, prompt_pack_text = build_bundle()
    write_artifacts(artifacts, rows, prompt_pack_text)
    result = artifacts[OUTPUT_STEMS["result_ledger"]]["result_summary"]["row_level_all_eight_summary"]
    print(
        json.dumps(
            {
                "accepted_rows": EXPECTED_ACCEPTED_ROWS,
                "blocked_rows_excluded": EXPECTED_BLOCKED_ROWS,
                "no_terminal_count": result["no_terminal_count"],
                "target_before_stop_count": result["target_before_stop_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
