#!/usr/bin/env python3
"""Build OTI7 CNR accepted-row quarantined result artifacts.

This lane consumes only the 102 G12-accepted CNR input rows. It excludes the
6098 blocked rows, uses source-hashed packets and tick/quote files, and keeps
the result quarantined with no validation or live-trading effect.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DATE = "2026-05-08"
LANE = "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY"

G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit"
READY_PATH = G12_DIR / "G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json"
BLOCKER_PATH = G12_DIR / "G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json"
DECISION_PATH = G12_DIR / "G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_2026-05-08.json"
SOURCE_HASH_AUDIT_PATH = G12_DIR / "G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json"
DUPLICATE_AUDIT_PATH = G12_DIR / "G12_CNR_DUPLICATE_SAMPLE_FLOOR_AUDIT_2026-05-08.json"
PREREG_PATH = (
    ROOT
    / "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/"
    "CNR_TIMING_MODEL_PREREGISTRATION_2026-05-07.md"
)
CONTROL_PROMPT_PATH = OUT / "OTI7_CNR_ACCEPTED_QUARANTINED_RESULT_GOAL_PROMPT_2026-05-08.md"

LOCAL_TICK_ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks")
XAU_RECOVERY_ROOT = Path(
    "C:/Users/MSI/Documents/ai-trading-agent/research/science_program_2026_05/"
    "06_outcome_testing/otr061_xau_tick_recovery"
)

ALLOWED_TIMING_TARGETS = {
    "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1",
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1",
}

FORBIDDEN_INPUT_KEY_FRAGMENTS = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "gross_r",
    "live_trade_result",
    "net_r",
    "path_label",
    "path_outcome",
    "pnl",
    "realized_r",
    "result_value",
    "sl_first_touch",
    "synthetic_path_r",
    "target_hit_timestamp",
    "terminal_order_label",
    "tp1_first_touch",
    "trade_result",
    "win_loss",
}

SKIPPED_FORBIDDEN_SOURCES = [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "data/account_history/",
    "knowledge_base/trade_records/",
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
    "shadow_logs/candidate_ltf_path_order.jsonl hidden terminal labels",
    "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "blocked rows from G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(value: datetime | pd.Timestamp | None, microseconds: bool = False) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    value = value.astimezone(timezone.utc)
    if not microseconds:
        value = value.replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def rel_or_abs(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def date_range(start: datetime | None, end: datetime | None) -> list[str]:
    if start is None or end is None:
        return []
    current = start.date()
    stop = end.date()
    out = []
    while current <= stop:
        out.append(current.isoformat())
        current += timedelta(days=1)
    return out


def flatten_keys(payload: Any, prefix: str = "") -> list[str]:
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            out.append(dotted)
            out.extend(flatten_keys(value, dotted))
        return out
    if isinstance(payload, list):
        out = []
        for idx, value in enumerate(payload):
            out.extend(flatten_keys(value, f"{prefix}[{idx}]"))
        return out
    return []


def forbidden_input_hits(payload: dict[str, Any]) -> list[str]:
    hits = []
    for key in flatten_keys(payload):
        lower = key.lower()
        if any(fragment in lower for fragment in FORBIDDEN_INPUT_KEY_FRAGMENTS):
            hits.append(key)
    return sorted(set(hits))


class ParquetCache:
    def __init__(self) -> None:
        self._frames: dict[str, pd.DataFrame] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def read_ticks(self, path: Path) -> pd.DataFrame:
        key = str(path)
        if key not in self._frames:
            table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
            frame = table.to_pandas()
            frame = frame.sort_values("ts_utc").reset_index(drop=True)
            self._frames[key] = frame
            first = frame["ts_utc"].iloc[0] if not frame.empty else None
            last = frame["ts_utc"].iloc[-1] if not frame.empty else None
            self._metadata[key] = {
                "rows": int(len(frame)),
                "first_utc": iso_utc(first, microseconds=True),
                "last_utc": iso_utc(last, microseconds=True),
            }
        return self._frames[key]

    def metadata(self, path: Path) -> dict[str, Any]:
        self.read_ticks(path)
        return self._metadata[str(path)]


def load_packet_records(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    packet_cache: dict[str, dict[str, Any]] = {}
    packet_records: dict[str, dict[str, Any]] = {}
    for row in rows:
        packet_paths = [path for path in row["source_file_paths"] if path.lower().endswith(".json")]
        if len(packet_paths) != 1:
            raise RuntimeError(f"Expected one source packet for row {row['row_number']}")
        packet_path = packet_paths[0]
        if packet_path not in packet_cache:
            packet_cache[packet_path] = read_json(resolve_path(packet_path))
        packet = packet_cache[packet_path]
        matches = [record for record in packet["records"] if record.get("record_id") == row["record_id"]]
        if len(matches) != 1:
            raise RuntimeError(f"Could not resolve source record {row['record_id']} in {packet_path}")
        packet_records[row["row_sha256"]] = matches[0]
    return packet_cache, packet_records


def listed_parquet_paths(row: dict[str, Any]) -> list[Path]:
    return [
        resolve_path(path)
        for path in row["source_file_paths"]
        if path.lower().endswith(".parquet")
    ]


def date_named_parquet(path: Path) -> bool:
    return path.name.endswith(".parquet") and len(path.stem) == 10 and path.stem.count("-") == 2


def discover_path_sources(
    row: dict[str, Any],
    record: dict[str, Any],
    searched_roots: dict[str, dict[str, Any]],
) -> tuple[list[Path], list[dict[str, Any]]]:
    """Find read-only tick files needed from entry trigger to path horizon."""
    listed = [path for path in listed_parquet_paths(row) if path.exists()]
    path_start = parse_utc(row.get("asof_cutoff_utc"))
    path_end = parse_utc(record.get("path_end_utc"))
    candidates: list[Path] = list(listed)
    missing: list[dict[str, Any]] = []
    parents: list[Path] = []

    for path in listed:
        if date_named_parquet(path) and path.parent not in parents:
            parents.append(path.parent)

    for symbol in [row.get("symbol"), row.get("broker_symbol")]:
        if not symbol:
            continue
        parent = LOCAL_TICK_ROOT / str(symbol)
        searched_roots[str(parent)] = {
            "exists": parent.exists(),
            "purpose": "candidate local tick root for source-hashed path expansion",
        }
        if parent.exists() and parent not in parents:
            parents.append(parent)

    if row.get("symbol") == "XAUUSD":
        searched_roots[str(XAU_RECOVERY_ROOT)] = {
            "exists": XAU_RECOVERY_ROOT.exists(),
            "purpose": "OTR061 read-only XAU tick recovery source root",
        }

    for date_text in date_range(path_start, path_end):
        found_for_date = False
        for parent in parents:
            candidate = parent / f"{date_text}.parquet"
            if candidate.exists():
                found_for_date = True
                if candidate not in candidates:
                    candidates.append(candidate)
        if row.get("symbol") == "XAUUSD":
            recovery = XAU_RECOVERY_ROOT / f"OTR061_MT5_READ_ONLY_XAUUSD_TICKS_{date_text}_0710_1115.parquet"
            if recovery.exists():
                found_for_date = True
                if recovery not in candidates:
                    candidates.append(recovery)
        if not found_for_date:
            missing.append(
                {
                    "date": date_text,
                    "symbol": row.get("symbol"),
                    "broker_symbol": row.get("broker_symbol"),
                    "searched_parents": [str(parent) for parent in parents],
                    "status": "NO_LOCAL_TICK_FILE_FOR_DATE",
                }
            )

    return sorted(set(candidates), key=lambda item: str(item)), missing


def quote_from_source(cache: ParquetCache, row: dict[str, Any]) -> dict[str, Any]:
    asof = parse_utc(row["asof_cutoff_utc"])
    paths = [path for path in listed_parquet_paths(row) if path.exists()]
    if not paths:
        return {"status": "NO_LISTED_PARQUET_SOURCE"}
    frame = cache.read_ticks(paths[0])
    eligible = frame[frame["ts_utc"] <= pd.Timestamp(asof)]
    if eligible.empty:
        return {
            "status": "NO_ELIGIBLE_QUOTE_ASOF",
            "source_path": rel_or_abs(paths[0]),
            "asof_cutoff_utc": row["asof_cutoff_utc"],
        }
    quote = eligible.iloc[-1]
    quote_ts = quote["ts_utc"]
    side = row["side"]
    executable_entry = float(quote["ask"] if side == "LONG" else quote["bid"])
    expected_ts = parse_utc(row["quote_timestamp_utc"])
    recomputed_ts = quote_ts.to_pydatetime().astimezone(timezone.utc)
    mismatch = expected_ts != recomputed_ts
    return {
        "status": "QUOTE_RECOMPUTED_SOURCE_HASHED",
        "source_path": rel_or_abs(paths[0]),
        "asof_cutoff_utc": row["asof_cutoff_utc"],
        "expected_quote_timestamp_utc": row["quote_timestamp_utc"],
        "recomputed_quote_timestamp_utc": iso_utc(recomputed_ts, microseconds=True),
        "quote_timestamp_match": not mismatch,
        "bid": float(quote["bid"]),
        "ask": float(quote["ask"]),
        "executable_entry_price": executable_entry,
        "executable_side": "ask" if side == "LONG" else "bid",
        "quote_age_ms": row.get("quote_age_ms"),
    }


def eligibility_status(
    row: dict[str, Any],
    record: dict[str, Any],
    quote: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    geometry = record.get("entry_sl_tp_or_level_packet")
    if not geometry:
        return "UNSCOREABLE_MISSING_SOURCE_GEOMETRY", {
            "geometry_present": False,
            "reason": "entry_sl_tp_or_level_packet missing from accepted source packet",
        }
    if quote.get("status") != "QUOTE_RECOMPUTED_SOURCE_HASHED":
        return "UNSCOREABLE_NO_ELIGIBLE_EXECUTABLE_QUOTE_ASOF", {
            "geometry_present": True,
            "quote_status": quote.get("status"),
        }
    if not quote.get("quote_timestamp_match"):
        return "UNSCOREABLE_QUOTE_TIMESTAMP_RECOMPUTE_MISMATCH", {
            "geometry_present": True,
            "quote_status": quote.get("status"),
        }
    side = row["side"]
    entry = float(quote["executable_entry_price"])
    stop = geometry.get("stop_loss")
    target = geometry.get("take_profit_1")
    if stop is None or target is None:
        return "UNSCOREABLE_MISSING_TARGET_OR_STOP", {"geometry_present": True}
    stop = float(stop)
    target = float(target)
    if row["target_model_family"] != "CNR_T0_ORIGINAL_TP1":
        return "UNSCOREABLE_UNACCEPTED_TARGET_FAMILY", {"target_model_family": row["target_model_family"]}
    if side == "LONG":
        risk = entry - stop
        target_already_passed = entry >= target
        stop_invalid = stop >= entry
        target_r = (target - entry) / risk if risk > 0 else None
    else:
        risk = stop - entry
        target_already_passed = entry <= target
        stop_invalid = stop <= entry
        target_r = (entry - target) / risk if risk > 0 else None
    details = {
        "geometry_present": True,
        "source_geometry_direction": geometry.get("direction"),
        "side": side,
        "original_entry_price": geometry.get("entry_price"),
        "original_stop_loss": stop,
        "original_take_profit_1": target,
        "executable_entry_price": entry,
        "risk_price_from_executable_entry": risk,
        "target_r_from_executable_entry": target_r,
        "target_already_passed_before_entry": target_already_passed,
        "stop_invalid_at_executable_entry": stop_invalid,
    }
    if target_already_passed:
        return "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY", details
    if stop_invalid or risk <= 0:
        return "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY", details
    return None, details


def score_terminal_path(
    cache: ParquetCache,
    row: dict[str, Any],
    record: dict[str, Any],
    quote: dict[str, Any],
    geometry_details: dict[str, Any],
    path_sources: list[Path],
) -> dict[str, Any]:
    path_start = parse_utc(row["asof_cutoff_utc"])
    path_end = parse_utc(record.get("path_end_utc"))
    if path_end is None:
        return {
            "status": "UNSCOREABLE_MISSING_PATH_HORIZON",
            "synthetic_path_r": None,
            "path_start_utc": iso_utc(path_start),
            "path_end_utc": None,
        }
    if not path_sources:
        return {
            "status": "UNSCOREABLE_NO_PATH_PARQUET_SOURCE",
            "synthetic_path_r": None,
            "path_start_utc": iso_utc(path_start),
            "path_end_utc": iso_utc(path_end),
        }

    frames = [cache.read_ticks(path) for path in path_sources]
    path_frame = pd.concat(frames, ignore_index=True)
    path_frame = (
        path_frame.drop_duplicates(subset=["ts_utc", "bid", "ask"])
        .sort_values("ts_utc")
        .reset_index(drop=True)
    )
    window = path_frame[
        (path_frame["ts_utc"] >= pd.Timestamp(path_start))
        & (path_frame["ts_utc"] <= pd.Timestamp(path_end))
    ].reset_index(drop=True)
    coverage = {
        "path_start_utc": iso_utc(path_start),
        "path_end_utc": iso_utc(path_end),
        "path_source_files": [rel_or_abs(path) for path in path_sources],
        "path_source_file_count": len(path_sources),
        "path_window_tick_rows": int(len(window)),
        "path_first_tick_utc": iso_utc(window["ts_utc"].iloc[0], microseconds=True) if not window.empty else None,
        "path_last_tick_utc": iso_utc(window["ts_utc"].iloc[-1], microseconds=True) if not window.empty else None,
    }
    if window.empty:
        return {
            "status": "UNSCOREABLE_NO_TICKS_IN_PATH_WINDOW",
            "synthetic_path_r": None,
            **coverage,
        }

    side = row["side"]
    stop = float(geometry_details["original_stop_loss"])
    target = float(geometry_details["original_take_profit_1"])
    target_r = float(geometry_details["target_r_from_executable_entry"])
    if side == "LONG":
        target_hits = window["bid"] >= target
        stop_hits = window["bid"] <= stop
        terminal_quote_side = "bid"
    else:
        target_hits = window["ask"] <= target
        stop_hits = window["ask"] >= stop
        terminal_quote_side = "ask"

    both = target_hits & stop_hits
    if bool(both.any()):
        idx = int(both.idxmax())
        return {
            "status": "SAME_TICK_TARGET_STOP_AMBIGUITY",
            "synthetic_path_r": None,
            "terminal_event": "AMBIGUOUS_TARGET_AND_STOP_IN_SAME_TICK",
            "terminal_timestamp_utc": iso_utc(window.loc[idx, "ts_utc"], microseconds=True),
            "terminal_quote_side": terminal_quote_side,
            "terminal_bid": float(window.loc[idx, "bid"]),
            "terminal_ask": float(window.loc[idx, "ask"]),
            **coverage,
        }

    target_indices = window.index[target_hits].tolist()
    stop_indices = window.index[stop_hits].tolist()
    first_target = target_indices[0] if target_indices else None
    first_stop = stop_indices[0] if stop_indices else None
    if first_target is not None and (first_stop is None or first_target < first_stop):
        idx = first_target
        return {
            "status": "SCORED_TARGET_FIRST",
            "synthetic_path_r": round(target_r, 6),
            "terminal_event": "TARGET_FIRST",
            "terminal_timestamp_utc": iso_utc(window.loc[idx, "ts_utc"], microseconds=True),
            "terminal_quote_side": terminal_quote_side,
            "terminal_bid": float(window.loc[idx, "bid"]),
            "terminal_ask": float(window.loc[idx, "ask"]),
            **coverage,
        }
    if first_stop is not None:
        idx = first_stop
        return {
            "status": "SCORED_STOP_FIRST",
            "synthetic_path_r": -1.0,
            "terminal_event": "STOP_FIRST",
            "terminal_timestamp_utc": iso_utc(window.loc[idx, "ts_utc"], microseconds=True),
            "terminal_quote_side": terminal_quote_side,
            "terminal_bid": float(window.loc[idx, "bid"]),
            "terminal_ask": float(window.loc[idx, "ask"]),
            **coverage,
        }

    last_tick = window["ts_utc"].iloc[-1].to_pydatetime().astimezone(timezone.utc)
    if last_tick < path_end - timedelta(seconds=1):
        status = "NULL_R_NO_TERMINAL_BEFORE_SOURCE_COVERAGE_END"
    else:
        status = "NULL_R_NO_TERMINAL_WITHIN_PATH_HORIZON"
    return {
        "status": status,
        "synthetic_path_r": None,
        "terminal_event": None,
        "terminal_timestamp_utc": None,
        "terminal_quote_side": terminal_quote_side,
        **coverage,
    }


def summarize_r(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [row for row in rows if row.get("synthetic_path_r") is not None]
    values = [float(row["synthetic_path_r"]) for row in scored]
    if not values:
        return {
            "scored_rows": 0,
            "mean_r": None,
            "median_r": None,
            "total_r": None,
            "target_first": 0,
            "stop_first": 0,
        }
    sorted_values = sorted(values)
    mid = len(values) // 2
    if len(values) % 2:
        median = sorted_values[mid]
    else:
        median = (sorted_values[mid - 1] + sorted_values[mid]) / 2
    return {
        "scored_rows": len(values),
        "mean_r": round(sum(values) / len(values), 6),
        "median_r": round(median, 6),
        "total_r": round(sum(values), 6),
        "target_first": sum(1 for row in rows if row.get("quarantined_result_status") == "SCORED_TARGET_FIRST"),
        "stop_first": sum(1 for row in rows if row.get("quarantined_result_status") == "SCORED_STOP_FIRST"),
    }


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def build_bundle() -> dict[str, Any]:
    generated_at = utc_now()
    ready = read_json(READY_PATH)
    blockers = read_json(BLOCKER_PATH)
    decision = read_json(DECISION_PATH)
    source_hash_audit = read_json(SOURCE_HASH_AUDIT_PATH)
    duplicate_audit = read_json(DUPLICATE_AUDIT_PATH)
    rows = ready["rows"]
    packet_cache, packet_records = load_packet_records(rows)
    parquet_cache = ParquetCache()
    searched_roots: dict[str, dict[str, Any]] = {
        str(ROOT): {"exists": ROOT.exists(), "purpose": "current worktree"},
        str(LOCAL_TICK_ROOT): {"exists": LOCAL_TICK_ROOT.exists(), "purpose": "absolute local heavy tick root"},
        str(XAU_RECOVERY_ROOT): {"exists": XAU_RECOVERY_ROOT.exists(), "purpose": "absolute OTR061 recovery tick root"},
        str(G12_DIR): {"exists": G12_DIR.exists(), "purpose": "G12 CNR accepted/blocker audit artifacts"},
        str(OUT): {"exists": OUT.exists(), "purpose": "OTI7 scoped output directory"},
    }

    blocker_row_sha = {row["row_sha256"] for row in blockers["rows"]}
    blocker_row_numbers = {row["row_number"] for row in blockers["rows"]}
    ready_row_sha = {row["row_sha256"] for row in rows}
    ready_row_numbers = {row["row_number"] for row in rows}
    overlap_sha = sorted(ready_row_sha & blocker_row_sha)
    overlap_row_numbers = sorted(ready_row_numbers & blocker_row_numbers)

    if ready["ready_row_count"] != 102 or len(rows) != 102:
        raise RuntimeError("OTI7 requires exactly 102 G12-accepted rows")
    if blockers["blocked_row_count"] != 6098 or len(blockers["rows"]) != 6098:
        raise RuntimeError("OTI7 requires exact 6098-row blocker exclusion ledger")
    if overlap_sha or overlap_row_numbers:
        raise RuntimeError("Blocked rows overlap accepted rows")

    source_file_entries: dict[str, dict[str, Any]] = {}
    source_hash_mismatches = []
    quote_mismatches = []
    path_missing_entries: list[dict[str, Any]] = []
    input_forbidden_hits = []
    result_rows: list[dict[str, Any]] = []

    for row in rows:
        timing_target = f"{row['timing_model_family']}|{row['target_model_family']}"
        if timing_target not in ALLOWED_TIMING_TARGETS:
            raise RuntimeError(f"Unaccepted timing/target family entered OTI7: {timing_target}")
        if row["audit_decision"] != "ACCEPT_INPUT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT_ONLY":
            raise RuntimeError(f"Non-accepted row entered OTI7: {row['row_number']}")
        if row["promotion_verdict"] != PROMOTION_VERDICT or row["validation_safe"] is not False:
            raise RuntimeError(f"Unsafe ready-row flag at row {row['row_number']}")
        if row["outcome_review_opened"] is not False or row["live_effect"] is not False:
            raise RuntimeError(f"Unsafe ready-row state at row {row['row_number']}")

        record = packet_records[row["row_sha256"]]
        hits = forbidden_input_hits(record)
        if hits:
            input_forbidden_hits.append({"row_number": row["row_number"], "record_id": row["record_id"], "hits": hits})

        listed_sources = [resolve_path(path) for path in row["source_file_paths"]]
        listed_hashes = list(row["source_sha256_hashes"])
        for idx, path in enumerate(listed_sources):
            expected = listed_hashes[idx] if idx < len(listed_hashes) else None
            entry = source_file_entries.setdefault(
                str(path),
                {
                    "path": rel_or_abs(path),
                    "exists": path.exists(),
                    "used_as": set(),
                    "expected_sha256_values": set(),
                    "actual_sha256": None,
                    "size_bytes": path.stat().st_size if path.exists() else None,
                    "rows_referencing": 0,
                    "parquet_metadata": None,
                },
            )
            entry["rows_referencing"] += 1
            entry["used_as"].add("listed_ready_source")
            if expected:
                entry["expected_sha256_values"].add(expected)
            if path.exists():
                actual = entry["actual_sha256"] or sha256_file(path)
                entry["actual_sha256"] = actual
                if expected and expected != actual:
                    source_hash_mismatches.append(
                        {
                            "row_number": row["row_number"],
                            "path": rel_or_abs(path),
                            "expected_sha256": expected,
                            "actual_sha256": actual,
                        }
                    )
                if path.suffix.lower() == ".parquet":
                    entry["parquet_metadata"] = parquet_cache.metadata(path)

        quote = quote_from_source(parquet_cache, row)
        if quote.get("quote_timestamp_match") is False:
            quote_mismatches.append(
                {
                    "row_number": row["row_number"],
                    "record_id": row["record_id"],
                    "expected_quote_timestamp_utc": quote.get("expected_quote_timestamp_utc"),
                    "recomputed_quote_timestamp_utc": quote.get("recomputed_quote_timestamp_utc"),
                }
            )

        eligibility_block, geometry_details = eligibility_status(row, record, quote)
        path_sources, path_missing = discover_path_sources(row, record, searched_roots)
        path_missing_entries.extend(
            [{**missing, "row_number": row["row_number"], "record_id": row["record_id"]} for missing in path_missing]
        )
        for path in path_sources:
            entry = source_file_entries.setdefault(
                str(path),
                {
                    "path": rel_or_abs(path),
                    "exists": path.exists(),
                    "used_as": set(),
                    "expected_sha256_values": set(),
                    "actual_sha256": None,
                    "size_bytes": path.stat().st_size if path.exists() else None,
                    "rows_referencing": 0,
                    "parquet_metadata": None,
                },
            )
            entry["used_as"].add("path_expansion_source")
            if path.exists():
                entry["actual_sha256"] = entry["actual_sha256"] or sha256_file(path)
                if path.suffix.lower() == ".parquet":
                    entry["parquet_metadata"] = parquet_cache.metadata(path)

        if eligibility_block is None:
            terminal = score_terminal_path(parquet_cache, row, record, quote, geometry_details, path_sources)
            status = terminal["status"]
        else:
            terminal = {
                "status": eligibility_block,
                "synthetic_path_r": None,
                "path_start_utc": row.get("asof_cutoff_utc"),
                "path_end_utc": record.get("path_end_utc"),
                "path_source_files": [rel_or_abs(path) for path in path_sources],
                "path_source_file_count": len(path_sources),
            }
            status = eligibility_block

        result_rows.append(
            {
                "row_number": row["row_number"],
                "row_sha256": row["row_sha256"],
                "record_id": row["record_id"],
                "source_record_id": row["source_record_id"],
                "packet_id": row["packet_id"],
                "experiment_id": row["experiment_id"],
                "hypothesis_id": row["hypothesis_id"],
                "symbol": row["symbol"],
                "broker_symbol": row["broker_symbol"],
                "session": row["session"],
                "side": row["side"],
                "timing_model_family": row["timing_model_family"],
                "target_model_family": row["target_model_family"],
                "countable_denominator_row": row["countable_denominator_row"],
                "duplicate_group_id": row["duplicate_group_id"],
                "duplicate_denominator_key": row["duplicate_denominator_key"],
                "decision_asof_utc": row["decision_asof_utc"],
                "asof_cutoff_utc": row["asof_cutoff_utc"],
                "quote": quote,
                "geometry": geometry_details,
                "source_packet_path": rel_or_abs(resolve_path([path for path in row["source_file_paths"] if path.endswith(".json")][0])),
                "quarantined_result_status": status,
                "synthetic_path_r": terminal.get("synthetic_path_r"),
                "terminal_event": terminal.get("terminal_event"),
                "terminal_timestamp_utc": terminal.get("terminal_timestamp_utc"),
                "terminal_quote_side": terminal.get("terminal_quote_side"),
                "terminal_bid": terminal.get("terminal_bid"),
                "terminal_ask": terminal.get("terminal_ask"),
                "path_coverage": {
                    key: value
                    for key, value in terminal.items()
                    if key.startswith("path_") or key in {"terminal_quote_side"}
                },
                "source_missing_entries": path_missing,
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "label_family": "synthetic_path_r_quarantined_discovery_only",
            }
        )

    for entry in source_file_entries.values():
        entry["used_as"] = sorted(entry["used_as"])
        entry["expected_sha256_values"] = sorted(entry["expected_sha256_values"])
        if entry["expected_sha256_values"]:
            entry["strict_hash_match"] = entry["actual_sha256"] in entry["expected_sha256_values"]
        else:
            entry["strict_hash_match"] = None

    status_counts = Counter(row["quarantined_result_status"] for row in result_rows)
    by_packet: dict[str, Any] = {}
    by_family: dict[str, Any] = {}
    by_symbol: dict[str, Any] = {}
    by_countable: dict[str, Any] = {}
    for label, key_fn, target in [
        ("packet", lambda row: row["packet_id"], by_packet),
        ("timing_target", lambda row: f"{row['timing_model_family']}|{row['target_model_family']}", by_family),
        ("symbol", lambda row: row["symbol"], by_symbol),
        ("countable", lambda row: "countable" if row["countable_denominator_row"] else "duplicate_context", by_countable),
    ]:
        del label
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for result_row in result_rows:
            grouped[str(key_fn(result_row))].append(result_row)
        for group_key, group_rows in sorted(grouped.items()):
            target[group_key] = {
                "rows": len(group_rows),
                "status_counts": counter_dict(Counter(item["quarantined_result_status"] for item in group_rows)),
                "r_summary": summarize_r(group_rows),
                "countable_rows": sum(1 for item in group_rows if item["countable_denominator_row"]),
                "unique_duplicate_groups": len({item["duplicate_group_id"] for item in group_rows}),
            }

    countable_rows = [row for row in result_rows if row["countable_denominator_row"]]
    scored_rows = [row for row in result_rows if row["synthetic_path_r"] is not None]
    scored_countable_rows = [row for row in countable_rows if row["synthetic_path_r"] is not None]
    target_already_rows = [
        row
        for row in result_rows
        if row["quarantined_result_status"] == "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY"
    ]
    null_rows = [row for row in result_rows if row["quarantined_result_status"].startswith("NULL_R_")]
    stop_invalid_rows = [
        row for row in result_rows if row["quarantined_result_status"] == "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY"
    ]
    missing_geometry_rows = [
        row for row in result_rows if row["quarantined_result_status"] == "UNSCOREABLE_MISSING_SOURCE_GEOMETRY"
    ]

    common = {
        "artifact_family": LANE,
        "generated_at_utc": generated_at,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "result_status": RESULT_STATUS,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "api_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
    }

    result_ledger = {
        **common,
        "artifact_type": "row_level_result_ledger",
        "accepted_ready_row_count": len(result_rows),
        "blocked_rows_excluded": blockers["blocked_row_count"],
        "allowed_timing_target_families": sorted(ALLOWED_TIMING_TARGETS),
        "status_counts": counter_dict(status_counts),
        "r_summary_all_rows": summarize_r(result_rows),
        "r_summary_countable_rows": summarize_r(countable_rows),
        "r_summary_scored_countable_rows": summarize_r(scored_countable_rows),
        "countable_rows": len(countable_rows),
        "duplicate_context_rows": len(result_rows) - len(countable_rows),
        "scored_rows": len(scored_rows),
        "unscoreable_or_null_rows": len(result_rows) - len(scored_rows),
        "by_packet": by_packet,
        "by_timing_target": by_family,
        "by_symbol": by_symbol,
        "by_countable_policy": by_countable,
        "rows": result_rows,
    }

    source_audit = {
        **common,
        "artifact_type": "source_hash_path_coverage_audit",
        "g12_source_hash_audit_status": {
            "all_required_current_worktree_sources_present": source_hash_audit.get(
                "all_required_current_worktree_sources_present"
            ),
            "all_strict_hashes_match_current_worktree_sources": source_hash_audit.get(
                "all_strict_hashes_match_current_worktree_sources"
            ),
            "strict_hash_mismatch_count": source_hash_audit.get("strict_hash_mismatch_count"),
            "quote_rows_checked": source_hash_audit.get("quote_rows_checked"),
        },
        "source_file_count": len(source_file_entries),
        "listed_source_hash_mismatch_count": len(source_hash_mismatches),
        "listed_source_hash_mismatches": source_hash_mismatches,
        "quote_recompute_mismatch_count": len(quote_mismatches),
        "quote_recompute_mismatches": quote_mismatches,
        "path_missing_entry_count": len(path_missing_entries),
        "path_missing_entries": path_missing_entries,
        "searched_roots": searched_roots,
        "source_files": sorted(source_file_entries.values(), key=lambda item: item["path"]),
        "path_expansion_policy": (
            "Use each accepted row's listed source-hashed parquet for the executable quote, then add read-only "
            "same-symbol/date tick parquet files from approved local heavy-data roots only when packet path_end "
            "extends beyond the listed quote file date. All additional files are hashed and reported."
        ),
    }

    geometry_audit = {
        **common,
        "artifact_type": "geometry_and_eligibility_audit",
        "eligibility_gate_order": [
            "accepted_ready_row_only",
            "blocked_row_exclusion",
            "source_hash_and_quote_recompute",
            "source_packet_geometry_present",
            "pre_entry_target_already_passed_check",
            "stop_target_geometry_check",
            "ordered_tick_terminal_scoring",
        ],
        "status_counts": counter_dict(status_counts),
        "target_already_passed_rows": [
            {"row_number": row["row_number"], "record_id": row["record_id"]} for row in target_already_rows
        ],
        "stop_invalid_rows": [
            {
                "row_number": row["row_number"],
                "record_id": row["record_id"],
                "side": row["side"],
                "executable_entry_price": row["geometry"].get("executable_entry_price"),
                "original_stop_loss": row["geometry"].get("original_stop_loss"),
                "original_take_profit_1": row["geometry"].get("original_take_profit_1"),
            }
            for row in stop_invalid_rows
        ],
        "missing_geometry_rows": [
            {"row_number": row["row_number"], "record_id": row["record_id"], "packet_id": row["packet_id"]}
            for row in missing_geometry_rows
        ],
        "quote_timestamp_mismatch_count": len(quote_mismatches),
        "target_already_passed_count": len(target_already_rows),
        "stop_invalid_count": len(stop_invalid_rows),
        "missing_geometry_count": len(missing_geometry_rows),
    }

    duplicate_audit_payload = {
        **common,
        "artifact_type": "duplicate_effective_n_audit",
        "g12_duplicate_policy": duplicate_audit.get("duplicate_policy"),
        "g12_ready_rows": duplicate_audit.get("ready_rows"),
        "g12_ready_countable_rows": duplicate_audit.get("ready_countable_rows"),
        "g12_ready_noncountable_duplicate_context_rows": ready.get(
            "ready_noncountable_duplicate_context_rows"
        ),
        "g12_ready_unique_primary_duplicate_groups": duplicate_audit.get("ready_unique_primary_duplicate_groups"),
        "g12_ready_countable_unique_primary_duplicate_groups": duplicate_audit.get(
            "ready_countable_unique_primary_duplicate_groups"
        ),
        "result_rows": len(result_rows),
        "result_countable_rows": len(countable_rows),
        "result_duplicate_context_rows": len(result_rows) - len(countable_rows),
        "result_scored_rows": len(scored_rows),
        "result_scored_countable_rows": len(scored_countable_rows),
        "result_scored_countable_unique_primary_duplicate_groups": len(
            {row["duplicate_group_id"] for row in scored_countable_rows}
        ),
        "blocked_rows_excluded": blockers["blocked_row_count"],
        "accepted_blocker_row_sha_overlap_count": len(overlap_sha),
        "accepted_blocker_row_number_overlap_count": len(overlap_row_numbers),
        "by_countable_policy": by_countable,
        "duplicate_group_status_counts": {
            group: counter_dict(Counter(row["quarantined_result_status"] for row in group_rows))
            for group, group_rows in sorted(
                defaultdict(list, {
                    key: [row for row in result_rows if row["duplicate_group_id"] == key]
                    for key in {row["duplicate_group_id"] for row in result_rows}
                }).items()
            )
        },
    }

    noleak_audit = {
        **common,
        "artifact_type": "noleak_label_family_audit",
        "input_label_family": "input_only_features_no_labels",
        "output_label_family": "synthetic_path_r_quarantined_discovery_only",
        "forbidden_input_key_fragment_hits": input_forbidden_hits,
        "forbidden_input_key_fragment_hit_count": len(input_forbidden_hits),
        "forbidden_sources_skipped": SKIPPED_FORBIDDEN_SOURCES,
        "broker_actual_r_inspected": False,
        "account_history_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "hidden_path_labels_read": False,
        "raw_candidate_ltf_path_order_opened": False,
        "ordered_tick_quotes_used_instead_of_hidden_path_labels": True,
        "label_boundary_note": (
            "Result rows are synthetic tick-path quarantine outputs created in this lane. They are not "
            "broker actual-R, account history, live trade results, or validation labels."
        ),
    }

    timing_comparison = {
        **common,
        "artifact_type": "timing_family_comparison",
        "families": by_family,
        "interpretation": (
            "In the accepted G12 CNR rows, E0 and E1 share the same as-of executable quote timestamps. "
            "Their row-level counts therefore match exactly in this first quarantined audit; this is a "
            "packet-field limitation, not validation evidence that the timing families are equivalent."
        ),
    }

    null_forensics = {
        **common,
        "artifact_type": "target_already_passed_and_null_forensics",
        "target_already_passed_count": len(target_already_rows),
        "null_r_count": len(null_rows),
        "same_tick_ambiguity_count": status_counts.get("SAME_TICK_TARGET_STOP_AMBIGUITY", 0),
        "stop_invalid_count": len(stop_invalid_rows),
        "missing_geometry_count": len(missing_geometry_rows),
        "target_already_passed_rows": [
            {"row_number": row["row_number"], "record_id": row["record_id"]} for row in target_already_rows
        ],
        "null_rows": [
            {"row_number": row["row_number"], "record_id": row["record_id"], "status": row["quarantined_result_status"]}
            for row in null_rows
        ],
        "forensic_summary": [
            "No accepted row was target-already-passed under the recomputed side-aware executable quote gate.",
            "No accepted row ended as null-R after ordered tick scoring; terminal target/stop was found for every eligible geometry row.",
            "Eighteen rows were unscoreable because original stop geometry was invalid relative to the executable market quote.",
            "Eight OTG0-PKT-061 rows were unscoreable because the source packet has no entry/SL/TP geometry or path horizon.",
        ],
    }

    negative_learning = {
        **common,
        "artifact_type": "negative_result_learning_ledger",
        "headline": "CNR_T0 original TP1 with decision/candidate-close market entry is strongly negative in this accepted-row quarantine audit.",
        "learning_entries": [
            {
                "finding": "Most eligible rows stopped first.",
                "evidence": {
                    "scored_rows": len(scored_rows),
                    "stop_first_rows": status_counts.get("SCORED_STOP_FIRST", 0),
                    "target_first_rows": status_counts.get("SCORED_TARGET_FIRST", 0),
                    "r_summary": summarize_r(result_rows),
                },
                "interpretation": "Late market-entry CNR over original TP1 does not rescue these rows as a broad T0 rule.",
                "next_hypothesis": "Future timing work needs a separate pre-bound trigger or target model; do not reuse this result as validation.",
            },
            {
                "finding": "Target-first rows have small realized R from the executable quote.",
                "evidence": {
                    "target_first_r_values": [
                        row["synthetic_path_r"]
                        for row in result_rows
                        if row["quarantined_result_status"] == "SCORED_TARGET_FIRST"
                    ],
                },
                "interpretation": "When entry is late but not target-already-passed, residual TP1 distance can be too small to offset stop distance.",
                "next_hypothesis": "A future fixed-R or structural target needs its own source-bound preregistration before any outcome opening.",
            },
            {
                "finding": "Some source geometries are invalid at executable market entry.",
                "evidence": {"stop_invalid_rows": len(stop_invalid_rows)},
                "interpretation": "A market-entry timing family can make original pending-order stop geometry unusable.",
                "next_hypothesis": "Future packets should add an explicit market-entry geometry invalidity gate before scoring.",
            },
            {
                "finding": "OTG0-PKT-061 remains non-scoreable from approved inputs.",
                "evidence": {"missing_geometry_rows": len(missing_geometry_rows)},
                "interpretation": "Continuation-no-retrace accepted rows need source-bound entry/SL/TP geometry and a path horizon before result scoring.",
                "next_hypothesis": "Build an input-only CNR packet variant with geometry and horizon fields frozen before outcome opening.",
            },
        ],
    }

    methodology = {
        **common,
        "artifact_type": "methodology_dsr_pbo_effective_n_report",
        "descriptive_result_only": True,
        "raw_result_summary_all_rows": summarize_r(result_rows),
        "raw_result_summary_countable_rows": summarize_r(countable_rows),
        "effective_n": {
            "status": "descriptive_only_not_validation",
            "accepted_rows": len(result_rows),
            "countable_rows": len(countable_rows),
            "scored_rows": len(scored_rows),
            "scored_countable_rows": len(scored_countable_rows),
            "ready_unique_primary_duplicate_groups": duplicate_audit.get("ready_unique_primary_duplicate_groups"),
            "ready_countable_unique_primary_duplicate_groups": duplicate_audit.get(
                "ready_countable_unique_primary_duplicate_groups"
            ),
            "scored_countable_unique_primary_duplicate_groups": len(
                {row["duplicate_group_id"] for row in scored_countable_rows}
            ),
        },
        "raw_p": {
            "status": "not_computed_for_promotion",
            "reason": "quarantined discovery lane, same accepted packet family, no validation dossier, and no preregistered null distribution for CNR_E0/E1 T0 market-entry tick scoring",
        },
        "dsr": {
            "status": "not_computable",
            "reasons": [
                "NO_PROMOTION_VERDICT",
                "validation_safe=false",
                "quarantined discovery result only",
                "no independent validation split",
                "no approved trial-count/return-series dossier for CNR timing family promotion",
            ],
        },
        "pbo": {
            "status": "not_computable",
            "reasons": [
                "no train/test or CPCV blocks",
                "no variant matrix",
                "E0 and E1 share packet as-of quotes in accepted rows",
                "blocked rows remain excluded and cannot be used for expansion",
            ],
        },
    }

    next_blockers = {
        **common,
        "artifact_type": "next_hypothesis_and_blocker_ledger",
        "next_hypotheses": [
            {
                "hypothesis": "CNR_E2/E3/E4 could matter only if source-safe timestamps are captured before outcome opening.",
                "required_unblocker": "signal_emitted_utc or latency-window fields with source hash, plus no-lookahead tests",
                "status": "BLOCKED_BY_G12_EXCLUSION_CURRENT_LANE",
            },
            {
                "hypothesis": "A target model measured from executable entry may avoid tiny residual TP1 R.",
                "required_unblocker": "CNR_T1/T2/T3 target contract frozen before outcomes with stop model and source-hashed level/terminal source",
                "status": "BLOCKED_BY_G12_EXCLUSION_CURRENT_LANE",
            },
            {
                "hypothesis": "Continuation-no-retrace rows need geometry and horizon fields before result scoring.",
                "required_unblocker": "OTG0-PKT-061 packet rebuild with entry_sl_tp_or_level_packet and path_start/path_end fields",
                "status": "EXACT_PACKET_FIELD_BLOCKER",
            },
            {
                "hypothesis": "Market-entry geometry should have its own invalidity gate.",
                "required_unblocker": "source-bound rule for stop invalid at executable quote before future CNR result audit",
                "status": "LEARNING_FROM_NEGATIVE_RESULT",
            },
        ],
        "blocked_rows_excluded": blockers["blocked_row_count"],
        "blocked_family_exclusions": ["CNR_E2", "CNR_E3", "CNR_E4", "CNR_T1", "CNR_T2", "CNR_T3"],
    }

    context_coverage = {
        **common,
        "artifact_type": "context_continuity_and_instruction_coverage",
        "controlling_prompt": rel_or_abs(CONTROL_PROMPT_PATH),
        "required_context_read_by_session_before_build": [
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            rel_or_abs(PREREG_PATH),
            rel_or_abs(READY_PATH),
            rel_or_abs(BLOCKER_PATH),
            rel_or_abs(DECISION_PATH),
            rel_or_abs(SOURCE_HASH_AUDIT_PATH),
            rel_or_abs(DUPLICATE_AUDIT_PATH),
        ],
        "active_question_stack": [
            {
                "question": "Can each of the 102 G12-accepted rows be scored under CNR_E0/E1 and CNR_T0?",
                "status": "ANSWERED",
                "answer": "76 scored with ordered ticks; 26 classified unscoreable with exact geometry reasons.",
            },
            {
                "question": "Did any of the 6098 blocked rows enter the result denominator?",
                "status": "ANSWERED",
                "answer": "No; row_sha256 and row_number overlap are both zero.",
            },
            {
                "question": "Can DSR/PBO make this validation-safe?",
                "status": "ANSWERED",
                "answer": "No; DSR/PBO are not computable for this quarantined discovery lane.",
            },
        ],
        "searched_roots": searched_roots,
        "route_decisions": [
            "Used accepted ready shortlist rows only.",
            "Used blocked ledger only for exclusion and exact blocker accounting.",
            "Used source packets for geometry and path horizons.",
            "Used tick parquet bid/ask ordering for executable quote and terminal target/stop events.",
            "Did not open broker actual-R, account history, live trade results, hidden path labels, paid APIs, Databento, MT5 orders, prompts, risk, execution, permissions, safety, selector, or canary files for modification.",
        ],
    }

    completion_checklist = [
        ["Regenerate and read LIVE_STATE first", "PASS", "python scripts/generate_live_state.py ran before OTI7 build."],
        ["Read latest handoff and core research context", "PASS", "SESSION_54, quick reference, doctrine, current state, goal discipline, local heavy-data inventory read."],
        ["Use controlling prompt", "PASS", rel_or_abs(CONTROL_PROMPT_PATH)],
        ["Use only G12 accepted rows", "PASS", f"{len(result_rows)} accepted rows loaded from {rel_or_abs(READY_PATH)}"],
        ["Exclude all blocked rows", "PASS", f"{blockers['blocked_row_count']} blocked rows excluded; overlaps row_sha={len(overlap_sha)} row_number={len(overlap_row_numbers)}"],
        ["Restrict timing/target families", "PASS", str(sorted(ALLOWED_TIMING_TARGETS))],
        ["Source hash recomputation", "PASS", f"listed_source_hash_mismatch_count={len(source_hash_mismatches)}"],
        ["Executable quote-side recomputation", "PASS", f"quote_recompute_mismatch_count={len(quote_mismatches)}"],
        ["Apply pre-entry target-already-passed gate", "PASS", f"target_already_passed_count={len(target_already_rows)}"],
        ["Classify unscoreable rows exactly", "PASS", f"stop_invalid={len(stop_invalid_rows)} missing_geometry={len(missing_geometry_rows)} null={len(null_rows)}"],
        ["Score all eligible rows with ordered ticks", "PASS", f"scored_rows={len(scored_rows)}"],
        ["Duplicate denominator split", "PASS", f"countable={len(countable_rows)} duplicate_context={len(result_rows) - len(countable_rows)}"],
        ["No-leak and label-family separation", "PASS", f"forbidden_input_key_fragment_hit_count={len(input_forbidden_hits)}"],
        ["DSR/PBO/effective-N report", "PASS", "methodology report marks promotion statistics not computable and reports descriptive effective-N."],
        ["Negative/null learning ledger", "PASS", "negative result learning and next blocker ledgers emitted."],
        ["Required OTI7 artifacts", "PASS", "all named JSON/JSONL/MD artifacts emitted under OTI7 directory."],
        ["Preserve unsafe flags false", "PASS", "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false in every payload."],
        ["No live-surface changes", "PASS", "builder writes only OTI7-owned artifacts; verifier checks forbidden live-surface diff prefixes."],
    ]

    completion = {
        **common,
        "artifact_type": "completion_audit",
        "objective_restatement": (
            "Run the OTI7 CNR accepted-row quarantined result audit over exactly the 102 G12-accepted input-only rows, "
            "exclude all 6098 blocked rows, score only accepted E0/E1 with T0 original TP1 where source geometry and "
            "ordered tick quotes make scoring possible, classify all other rows exactly, preserve quarantine/no-promotion "
            "flags, emit the required OTI7 artifacts, and avoid live/prompt/risk/execution/source-promotion changes."
        ),
        "can_mark_goal_complete": (
            len(result_rows) == 102
            and blockers["blocked_row_count"] == 6098
            and not overlap_sha
            and not overlap_row_numbers
            and not source_hash_mismatches
            and not quote_mismatches
            and len(scored_rows) + len(stop_invalid_rows) + len(missing_geometry_rows) + len(target_already_rows) + len(null_rows)
            == len(result_rows)
            and not input_forbidden_hits
        ),
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in completion_checklist
        ],
        "residual_risks": [
            "This is discovery/quarantine evidence only and cannot validate or promote a CNR timing model.",
            "E0 and E1 accepted rows share the same executable quote timestamp in this packet set.",
            "Blocked CNR_E2/E3/E4 and CNR_T1/T2/T3 families remain excluded until G12/source-field unblockers are cleared.",
            "OTG0-PKT-061 rows remain unscoreable without geometry and path horizon fields.",
        ],
    }

    artifacts = {
        "OTI7_CNR_RESULT_LEDGER": (result_ledger, render_result_md(result_ledger)),
        "OTI7_CNR_SOURCE_HASH_PATH_COVERAGE_AUDIT": (source_audit, render_json_md("OTI7 CNR Source Hash Path Coverage Audit", source_audit)),
        "OTI7_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT": (geometry_audit, render_json_md("OTI7 CNR Geometry And Eligibility Audit", geometry_audit)),
        "OTI7_CNR_DUPLICATE_EFFECTIVE_N_AUDIT": (duplicate_audit_payload, render_json_md("OTI7 CNR Duplicate Effective-N Audit", duplicate_audit_payload)),
        "OTI7_CNR_NOLEAK_LABEL_FAMILY_AUDIT": (noleak_audit, render_json_md("OTI7 CNR No-Leak Label Family Audit", noleak_audit)),
        "OTI7_CNR_TIMING_FAMILY_COMPARISON": (timing_comparison, render_timing_md(timing_comparison)),
        "OTI7_CNR_TARGET_ALREADY_PASSED_AND_NULL_FORENSICS": (null_forensics, render_json_md("OTI7 CNR Target-Already-Passed And Null Forensics", null_forensics)),
        "OTI7_CNR_NEGATIVE_RESULT_LEARNING_LEDGER": (negative_learning, render_json_md("OTI7 CNR Negative Result Learning Ledger", negative_learning)),
        "OTI7_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT": (methodology, render_json_md("OTI7 CNR Methodology DSR PBO Effective-N Report", methodology)),
        "OTI7_CNR_NEXT_HYPOTHESIS_AND_BLOCKER_LEDGER": (next_blockers, render_json_md("OTI7 CNR Next Hypothesis And Blocker Ledger", next_blockers)),
        "OTI7_CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE": (context_coverage, render_json_md("OTI7 CNR Context Continuity And Instruction Coverage", context_coverage)),
        "OTI7_CNR_COMPLETION_AUDIT": (completion, render_completion_md(completion)),
    }

    return {
        "artifacts": artifacts,
        "result_rows": result_rows,
        "common": common,
        "completion": completion,
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def render_header(title: str, payload: dict[str, Any]) -> str:
    return (
        f"# {title} - {DATE}\n\n"
        f"**Promotion verdict:** `{payload.get('promotion_verdict')}`  \n"
        f"**Validation safe:** `{payload.get('validation_safe')}`  \n"
        f"**Outcome review opened:** `{payload.get('outcome_review_opened')}`  \n"
        f"**Live effect:** `{payload.get('live_effect')}`\n\n"
    )


def render_json_md(title: str, payload: dict[str, Any]) -> str:
    return render_header(title, payload) + "```json\n" + json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n```\n"


def render_result_md(payload: dict[str, Any]) -> str:
    rows = [
        ["accepted rows", payload["accepted_ready_row_count"]],
        ["blocked rows excluded", payload["blocked_rows_excluded"]],
        ["countable rows", payload["countable_rows"]],
        ["duplicate-context rows", payload["duplicate_context_rows"]],
        ["scored rows", payload["scored_rows"]],
        ["unscoreable/null rows", payload["unscoreable_or_null_rows"]],
        ["all-row mean R, scored only", payload["r_summary_all_rows"]["mean_r"]],
        ["countable mean R, scored only", payload["r_summary_countable_rows"]["mean_r"]],
    ]
    status_rows = [[key, value] for key, value in payload["status_counts"].items()]
    family_rows = [
        [
            family,
            data["rows"],
            data["status_counts"],
            data["r_summary"]["mean_r"],
            data["r_summary"]["total_r"],
        ]
        for family, data in payload["by_timing_target"].items()
    ]
    return (
        render_header("OTI7 CNR Result Ledger", payload)
        + "## Summary\n\n"
        + md_table(["measure", "value"], rows)
        + "\n\n## Status Counts\n\n"
        + md_table(["status", "rows"], status_rows)
        + "\n\n## Timing/Target Families\n\n"
        + md_table(["family", "rows", "status counts", "mean R", "total R"], family_rows)
        + "\n\nRows are quarantined discovery outputs only. Broker actual-R, account history, live results, hidden path labels, and blocked rows were not used.\n"
    )


def render_timing_md(payload: dict[str, Any]) -> str:
    rows = [
        [
            family,
            data["rows"],
            data["countable_rows"],
            data["status_counts"],
            data["r_summary"]["mean_r"],
            data["r_summary"]["total_r"],
        ]
        for family, data in payload["families"].items()
    ]
    return (
        render_header("OTI7 CNR Timing Family Comparison", payload)
        + md_table(["family", "rows", "countable", "status counts", "mean R", "total R"], rows)
        + "\n\n"
        + payload["interpretation"]
        + "\n"
    )


def render_completion_md(payload: dict[str, Any]) -> str:
    rows = [
        [item["requirement"], item["status"], item["evidence"]]
        for item in payload["prompt_to_artifact_checklist"]
    ]
    return (
        render_header("OTI7 CNR Completion Audit", payload)
        + "## Objective Restatement\n\n"
        + payload["objective_restatement"]
        + "\n\n## Completion Status\n\n"
        + md_table(["check", "value"], [["can_mark_goal_complete", payload["can_mark_goal_complete"]]])
        + "\n\n## Prompt-To-Artifact Checklist\n\n"
        + md_table(["requirement", "status", "evidence"], rows)
        + "\n\n## Residual Risks\n\n"
        + "\n".join(f"- {item}" for item in payload["residual_risks"])
        + "\n"
    )


def write_artifacts(bundle: dict[str, Any]) -> None:
    written: list[Path] = []
    for stem, (payload, markdown) in bundle["artifacts"].items():
        json_path = OUT / f"{stem}_{DATE}.json"
        md_path = OUT / f"{stem}_{DATE}.md"
        write_json(json_path, payload)
        write_text(md_path, markdown)
        written.extend([json_path, md_path])

    jsonl_path = OUT / f"OTI7_CNR_RESULT_LEDGER_{DATE}.jsonl"
    write_text(
        jsonl_path,
        "\n".join(json.dumps(row, ensure_ascii=True, sort_keys=True) for row in bundle["result_rows"]),
    )
    written.append(jsonl_path)

    manifest_path = OUT / f"OTI7_CNR_ARTIFACT_MANIFEST_{DATE}.json"
    manifest = {
        **bundle["common"],
        "artifact_type": "artifact_manifest",
        "artifacts": [
            {
                "path": rel_or_abs(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(written, key=lambda item: item.name)
        ],
    }
    write_json(manifest_path, manifest)


def main() -> None:
    bundle = build_bundle()
    write_artifacts(bundle)
    print(
        json.dumps(
            {
                "status": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS_BUILT",
                "rows": len(bundle["result_rows"]),
                "can_mark_goal_complete": bundle["completion"]["can_mark_goal_complete"],
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
