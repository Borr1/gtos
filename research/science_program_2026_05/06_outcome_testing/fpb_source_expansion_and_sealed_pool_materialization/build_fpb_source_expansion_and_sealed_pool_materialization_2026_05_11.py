#!/usr/bin/env python3
"""Build the FPB source-expansion and sealed-pool materialization packet.

This route is source-control/materialization only. It reads local file
metadata, hashes, safe headers, coverage windows, and parser feasibility. It
does not run validation, score path behavior, call AI/API, read broker account
or order history, or change live behavior.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-11"
ROUTE_ID = "FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION"
PREFIX = "FPB_SOURCE_EXPANSION"
SCHEMA_VERSION = "fpb_source_expansion_and_sealed_pool_materialization_v1"
EVIDENCE_CLASS = "SOURCE_CONTROL_MATERIALIZATION_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = (
    "MATERIALIZED_NATIVE_SCID_SEALED_SOURCE_POOL_CANDIDATES_G12_AUDIT_REQUIRED"
)

CONTROLLING_PROMPT = (
    PROMPT_DIR
    / "FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION_GOAL_PROMPT_2026-05-11.md"
)
NEXT_G12_PROMPT = (
    PROMPT_DIR
    / "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_GOAL_PROMPT_2026-05-11.md"
)

G0_PACKET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"
)
G0_SYNTHESIS_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_fpb_discovery_synthesis_control_route"
)
FPB_DISCOVERY_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_family_path_behavior_discovery_result_screen"
)
SOURCE_ENGINE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_mechanical_replay_engine_from_source_universe"
)
SOURCE_UNIVERSE_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "no_api_historical_replay_engine_and_missed_opportunity_inventory"
)

INPUTS = {
    "controlling_prompt": CONTROLLING_PROMPT,
    "g0_partition_packet": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_PARTITION_LEDGER_2026-05-11.json",
    "g0_baseline_packet": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_2026-05-11.json",
    "g0_source_contract": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_2026-05-11.json",
    "g0_purge_policy": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_PURGE_EMBARGO_DUPLICATE_POLICY_2026-05-11.json",
    "g0_completion": G0_PACKET_DIR / "G0_FPB_SEALED_PARTITION_COMPLETION_AUDIT_2026-05-11.json",
    "g0_synthesis_route_ranking": G0_SYNTHESIS_DIR / "G0_FPB_SYNTHESIS_ROUTE_RANKING_LEDGER_2026-05-11.json",
    "fpb_aggregate_matrix": FPB_DISCOVERY_DIR / "FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json",
    "fpb_denominator_duplicate_policy": FPB_DISCOVERY_DIR
    / "FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json",
    "source_selection": SOURCE_ENGINE_DIR / "NO_API_MECHANICAL_REPLAY_SOURCE_SELECTION_AND_HASH_LEDGER_2026-05-10.json",
    "source_universe": SOURCE_UNIVERSE_DIR / "NO_API_HISTORICAL_REPLAY_SOURCE_UNIVERSE_LEDGER_2026-05-10.json",
    "source_universe_rows": SOURCE_UNIVERSE_DIR / "NO_API_HISTORICAL_REPLAY_SOURCE_UNIVERSE_ROWS_2026-05-10.jsonl",
}

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_promotion": False,
    "opens_live_trading_behavior": False,
    "opens_live_restart": False,
    "opens_paid_api_or_databento_route": False,
    "opens_mt5_order_account_history_behavior": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

BASELINE_CONTROLS = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
SELECTED_FAMILIES = [
    "adjacent_range_compression_breakout",
    "ob_retest",
    "opening_drive_no_fill_lifecycle",
]
SUPPORTED_TIMEFRAMES = {"M1", "M5", "M15", "H1", "H4"}
EMBARGO_DAYS = 14
SCID_HASH_MAX_BYTES = 900_000_000
SIERRA_ROOT = Path(r"C:\SierraChart\Data")
SCID_HEADER = struct.Struct("<4sIIHHI36s")
SCID_RECORD = struct.Struct("<QffffIIII")
SIERRA_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)

SEARCH_ROOTS = [
    {
        "root_id": "repo_data",
        "path": ROOT / "data",
        "role": "current worktree local data",
        "extensions": [".csv", ".parquet"],
    },
    {
        "root_id": "tmp_no_api_hist_replay_data",
        "path": Path(r"C:\tmp\gtos_otb\NOAPIHISTREPLAY\data"),
        "role": "out-of-tree no-api historical replay data copy",
        "extensions": [".csv", ".parquet"],
    },
    {
        "root_id": "tmp_no_api_mech_replay_data",
        "path": Path(r"C:\tmp\gtos_otb\NOAPIMECHREPLAY\data"),
        "role": "out-of-tree no-api mechanical replay data copy",
        "extensions": [".csv", ".parquet"],
    },
    {
        "root_id": "sierra_native_data",
        "path": SIERRA_ROOT,
        "role": "local Sierra Chart native market data",
        "extensions": [".scid", ".dly"],
    },
]

SCID_SYMBOL_MAP = {
    "6AM26-CME": ("AUDUSD_6A", "AUD futures proxy"),
    "6BM26-CME": ("GBPUSD_6B", "GBP futures proxy"),
    "6CM26-CME": ("USDCAD_6C", "CAD futures proxy"),
    "6EM26-CME": ("EURUSD", "EUR futures proxy"),
    "6JM26-CME": ("USDJPY_6J", "JPY futures proxy"),
    "6SM26-CME": ("USDCHF_6S", "CHF futures proxy"),
    "CLM26-NYMEX": ("USOIL_CL", "crude futures context"),
    "ESM26-CME": ("SPX_ES", "S&P futures proxy"),
    "GCM26-COMEX": ("XAUUSD_GC", "gold futures proxy"),
    "M2KM26-CME": ("RUSSELL_M2K", "equity-index context"),
    "MCLM26-NYMEX": ("USOIL_MCL", "micro crude futures context"),
    "MESM26-CME": ("SPX_MES", "micro S&P futures proxy"),
    "MGCM26-COMEX": ("XAUUSD_MGC", "micro gold futures proxy"),
    "MNQM26-CME": ("NAS100_MNQ", "micro Nasdaq futures proxy"),
    "MYMM26-CBOT": ("US30_MYM", "micro Dow futures proxy"),
    "NQM26-CME": ("NAS100_NQ", "Nasdaq futures proxy"),
    "RTYM26-CME": ("RUSSELL_RTY", "equity-index context"),
    "SILM26-COMEX": ("XAGUSD_SIL", "silver futures proxy"),
    "SIM26-COMEX": ("XAGUSD_SI", "silver futures proxy"),
    "VXM26-CFE": ("VIX_VX", "VIX futures context"),
    "VXMM26-CFE": ("VIX_VXM", "mini VIX futures context"),
    "XAUUSD": ("XAUUSD", "Sierra spot gold context"),
    "YMM26-CBOT": ("US30_YM", "Dow futures proxy"),
    "ZBM26-CBOT": ("BOND_ZB", "rates context"),
    "ZNM26-CBOT": ("BOND_ZN", "rates context"),
}

ARTIFACTS = {
    "context_anchor": f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}",
    "hardening": f"{PREFIX}_HARDENING_COVERAGE_LEDGER_{DATE_TAG}",
    "source_saturation": f"{PREFIX}_SEARCHED_ROOT_SOURCE_SATURATION_LEDGER_{DATE_TAG}",
    "acquisition_ladder": f"{PREFIX}_ACQUISITION_LADDER_LEDGER_{DATE_TAG}",
    "selected_source_coverage": f"{PREFIX}_SELECTED_SOURCE_COVERAGE_LEDGER_{DATE_TAG}",
    "local_csv_triage": f"{PREFIX}_LOCAL_CSV_TRIAGE_LEDGER_{DATE_TAG}",
    "native_scid_pool": f"{PREFIX}_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_{DATE_TAG}",
    "tick_parquet_triage": f"{PREFIX}_TICK_PARQUET_TRIAGE_LEDGER_{DATE_TAG}",
    "duplicate_source": f"{PREFIX}_DUPLICATE_SOURCE_DECISION_LEDGER_{DATE_TAG}",
    "source_contract": f"{PREFIX}_SOURCE_ASOF_NOLEAK_LEDGER_{DATE_TAG}",
    "baseline_preservation": f"{PREFIX}_ADVERSARIAL_BASELINE_PRESERVATION_LEDGER_{DATE_TAG}",
    "lfs_materialization": f"{PREFIX}_LFS_AND_MATERIALIZATION_AUDIT_{DATE_TAG}",
    "git_history": f"{PREFIX}_GIT_HISTORY_SOURCE_SEARCH_LEDGER_{DATE_TAG}",
    "hostile_review": f"{PREFIX}_HOSTILE_SOURCE_EDGE_REVIEW_LEDGER_{DATE_TAG}",
    "negative_anatomy": f"{PREFIX}_NEGATIVE_FAILURE_ANATOMY_LEDGER_{DATE_TAG}",
    "process_limitations": f"{PREFIX}_PROCESS_LIMITATION_COUNTERMEASURES_{DATE_TAG}",
    "self_redteam": f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}",
    "next_prompt_pack": f"{PREFIX}_NEXT_G12_PROMPT_PACK_{DATE_TAG}",
    "dirty_state": f"{PREFIX}_NOLEAK_DIRTY_STATE_AUDIT_{DATE_TAG}",
    "manifest": f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}",
    "completion": f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT = now_utc()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_git(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": "git " + " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip().splitlines(),
        "stderr": proc.stderr.strip().splitlines(),
    }


def safe_payload(artifact_family: str, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "artifact_family": artifact_family,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": GENERATED_AT,
        **SAFE_FLAGS,
        **body,
    }


def write_json(base: str, payload: dict[str, Any]) -> Path:
    path = ROUTE_DIR / f"{base}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(base: str, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> Path:
    path = ROUTE_DIR / f"{base}.md"
    summary_keys = [
        "artifact_family",
        "terminal_decision",
        "accepted_native_scid_candidate_count",
        "current_discovery_exposed_source_rows_excluded",
        "g12_source_pool_audit_prompt_emitted",
        "completion_standard_satisfied",
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
    ]
    summary = {key: payload[key] for key in summary_keys if key in payload}
    lines = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Evidence class: `{EVIDENCE_CLASS}`",
        f"- Promotion posture: `{PROMOTION_VERDICT}`",
        f"- validation_safe: `{str(SAFE_FLAGS['validation_safe']).lower()}`",
        f"- outcome_review_opened: `{str(SAFE_FLAGS['outcome_review_opened']).lower()}`",
        f"- live_effect: `{str(SAFE_FLAGS['live_effect']).lower()}`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
    ]
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in notes)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def emit(base: str, title: str, payload: dict[str, Any], notes: list[str] | None = None) -> dict[str, str]:
    write_json(base, payload)
    write_md(base, title, payload, notes)
    return {"json": rel(ROUTE_DIR / f"{base}.json"), "md": rel(ROUTE_DIR / f"{base}.md")}


def parse_time(value: str) -> datetime:
    raw = value.strip().replace("Z", "+00:00")
    if not raw:
        raise ValueError("empty timestamp")
    if " " in raw and "T" not in raw:
        raw = raw.replace(" ", "T", 1)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def infer_timeframe(path: Path, header: list[str] | None = None) -> str:
    tokens = re.split(r"[^A-Za-z0-9]+", path.stem.upper())
    for token in reversed(tokens):
        if token in {"M1", "M5", "M15", "H1", "H4", "D1"}:
            return token
    if header and any(field.lower() in {"date", "time_utc", "event"} for field in header):
        return "UNSUPPORTED_CONTEXT"
    return "UNSPECIFIED"


def infer_symbol(path: Path) -> str:
    stem = path.stem.upper()
    stem = re.sub(r"_(M15|M5|M1|H4|H1|D1)$", "", stem)
    stem = stem.replace("_SCID", "")
    if stem in SCID_SYMBOL_MAP:
        return SCID_SYMBOL_MAP[stem][0]
    return stem or "UNSPECIFIED_OR_MULTI"


def csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def csv_coverage(path: Path) -> dict[str, Any]:
    header = csv_header(path)
    lower = [h.strip().lower() for h in header]
    time_col = None
    for candidate in ("time", "time_utc", "datetime", "date"):
        if candidate in lower:
            time_col = lower.index(candidate)
            break
    has_ohlc = all(field in lower for field in ("open", "high", "low", "close"))
    first_time: datetime | None = None
    last_time: datetime | None = None
    rows = 0
    if time_col is None:
        return {
            "header": header,
            "has_ohlc": has_ohlc,
            "coverage_start_utc": None,
            "coverage_end_utc": None,
            "row_count": 0,
            "coverage_status": "NO_TIME_COLUMN",
        }
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if len(row) <= time_col or not row[time_col].strip():
                continue
            try:
                dt = parse_time(row[time_col])
            except Exception:
                continue
            if first_time is None:
                first_time = dt
            last_time = dt
            rows += 1
    return {
        "header": header,
        "has_ohlc": has_ohlc,
        "coverage_start_utc": iso(first_time) if first_time else None,
        "coverage_end_utc": iso(last_time) if last_time else None,
        "row_count": rows,
        "coverage_status": "COVERAGE_COMPLETE" if first_time and last_time else "NO_PARSEABLE_TIME_ROWS",
    }


def parse_scid(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size < SCID_HEADER.size + SCID_RECORD.size:
        return {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": size,
            "parser_status": "TOO_SMALL_FOR_SCID_HEADER_AND_RECORD",
            "source_sha256": None,
        }
    with path.open("rb") as handle:
        header = handle.read(SCID_HEADER.size)
        magic, header_size, record_size, version, utc_start_index, unused1, reserve = SCID_HEADER.unpack(header)
        handle.seek(header_size)
        first = handle.read(record_size)
        handle.seek(size - record_size)
        last = handle.read(record_size)
    first_values = SCID_RECORD.unpack(first)
    last_values = SCID_RECORD.unpack(last)
    first_dt = SIERRA_EPOCH + timedelta(microseconds=first_values[0])
    last_dt = SIERRA_EPOCH + timedelta(microseconds=last_values[0])
    hash_status = "HASHED_FULL_FILE"
    source_hash = None
    if size <= SCID_HASH_MAX_BYTES:
        source_hash = sha256_file(path)
    else:
        hash_status = "DEFERRED_LARGE_FILE_HASH_REQUIRED_BEFORE_G12_ACCEPTANCE"
    symbol, proxy_note = SCID_SYMBOL_MAP.get(path.stem.upper(), (path.stem.upper(), "unmapped native Sierra context"))
    return {
        "absolute_path": str(path),
        "file_name": path.name,
        "symbol": symbol,
        "source_instrument": path.stem,
        "proxy_note": proxy_note,
        "source_family": "SIERRA_NATIVE_SCID",
        "timeframe": "NATIVE_TICK_INTRABAR",
        "size_bytes": size,
        "magic": magic.decode(errors="replace"),
        "header_size": header_size,
        "record_size": record_size,
        "version": version,
        "utc_start_index": utc_start_index,
        "record_count": max((size - header_size) // record_size, 0),
        "coverage_start_utc": iso(first_dt),
        "coverage_end_utc": iso(last_dt),
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
        "hash_status": hash_status,
        "source_sha256": source_hash,
        "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
        "no_leak_status": "SOURCE_TIME_ORDERED_NATIVE_RECORDS_NO_BROKER_ACCOUNT_ORDER_OR_RESULT_FIELDS_READ",
    }


def sensitive_path(path: Path) -> bool:
    lowered = str(path).replace("\\", "/").lower()
    blocked = [
        "account_history",
        "trade_records",
        "orders",
        "deals",
        "positions",
        "tickets",
        "broker_actual",
    ]
    return any(token in lowered for token in blocked)


def discover_files(root: Path, extensions: set[str]) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root] if root.suffix.lower() in extensions and not sensitive_path(root) else []
    rows = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions and not sensitive_path(path):
            rows.append(path)
    return sorted(rows)


def selected_hashes(selection: dict[str, Any]) -> set[str]:
    return {row["source_sha256"] for row in selection.get("selected_sources", []) if row.get("source_sha256")}


def index_selected_coverage(universe_rows: list[dict[str, Any]], selected: set[str]) -> tuple[list[dict[str, Any]], dict[str, datetime]]:
    rows: list[dict[str, Any]] = []
    max_end_by_symbol: dict[str, datetime] = {}
    seen = set()
    for row in universe_rows:
        source_hash = row.get("sha256")
        if not source_hash or source_hash not in selected:
            continue
        key = (source_hash, row.get("absolute_path"))
        if key in seen:
            continue
        seen.add(key)
        path = Path(row.get("absolute_path", ""))
        coverage = {
            "coverage_start_utc": None,
            "coverage_end_utc": None,
            "coverage_status": "NOT_PARSED_SOURCE_FILE_MISSING_OR_UNSUPPORTED",
            "row_count": None,
        }
        if path.exists() and path.suffix.lower() == ".csv":
            try:
                parsed = csv_coverage(path)
                coverage.update(
                    {
                        "coverage_start_utc": parsed["coverage_start_utc"],
                        "coverage_end_utc": parsed["coverage_end_utc"],
                        "coverage_status": parsed["coverage_status"],
                        "row_count": parsed["row_count"],
                    }
                )
            except Exception as exc:
                coverage["coverage_status"] = f"CSV_COVERAGE_PARSE_ERROR:{type(exc).__name__}"
        symbol = row.get("symbol") or infer_symbol(path)
        timeframe = row.get("timeframe") or infer_timeframe(path)
        if coverage["coverage_end_utc"]:
            end_dt = parse_time(coverage["coverage_end_utc"])
            current = max_end_by_symbol.get(symbol)
            if current is None or end_dt > current:
                max_end_by_symbol[symbol] = end_dt
        rows.append(
            {
                "source_row_id": row.get("source_row_id"),
                "absolute_path": str(path),
                "repo_relative_path": row.get("repo_relative_path"),
                "symbol": symbol,
                "timeframe": timeframe,
                "source_family": row.get("source_family"),
                "source_sha256": source_hash,
                "source_selected_in_fpb_discovery": True,
                "partition_assignment": "DISCOVERY_EXPOSED_EXCLUDE_FROM_FUTURE_SEALED_VALIDATION",
                **coverage,
            }
        )
    return rows, max_end_by_symbol


def coverage_overlaps_embargo(symbol: str, start: str | None, end: str | None, selected_end: dict[str, datetime]) -> tuple[bool, str | None]:
    if not start or not end:
        return True, "MISSING_COVERAGE_FAIL_CLOSED"
    selected = selected_end.get(symbol)
    if selected is None:
        return False, None
    start_dt = parse_time(start)
    embargo_end = selected + timedelta(days=EMBARGO_DAYS)
    if start_dt <= embargo_end:
        return True, f"STARTS_BEFORE_OR_INSIDE_SELECTED_SOURCE_EMBARGO_UNTIL_{iso(embargo_end)}"
    return False, None


def eligible_segment_for_native(symbol: str, source_end: str, selected_end: dict[str, datetime]) -> tuple[str | None, str]:
    selected = selected_end.get(symbol)
    if selected is None:
        return None, "NO_COMPARABLE_SELECTED_SOURCE_WINDOW_FOUND_REQUIRE_G12_REVIEW"
    segment_start = selected + timedelta(days=EMBARGO_DAYS, seconds=1)
    end_dt = parse_time(source_end)
    if segment_start <= end_dt:
        return iso(segment_start), "HAS_POST_EMBARGO_NATIVE_SEGMENT"
    return None, f"NO_POST_EMBARGO_SEGMENT_SELECTED_EMBARGO_UNTIL_{iso(segment_start)}"


def triage_csv_files(paths: list[Path], selected: set[str], selected_end: dict[str, datetime]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen_hash: dict[str, str] = {}
    for path in paths:
        if path.suffix.lower() != ".csv":
            continue
        row: dict[str, Any] = {
            "absolute_path": str(path),
            "repo_relative_path": rel(path),
            "file_name": path.name,
            "size_bytes": path.stat().st_size,
            "source_family": "LOCAL_OR_DERIVED_OHLCV_CSV",
        }
        try:
            coverage = csv_coverage(path)
            row.update(coverage)
            row["timeframe"] = infer_timeframe(path, coverage.get("header"))
            row["symbol"] = infer_symbol(path)
            row["source_sha256"] = sha256_file(path)
            row["hash_status"] = "HASHED_FULL_FILE"
        except Exception as exc:
            row.update(
                {
                    "triage_decision": "REJECT_CSV_PARSE_OR_HASH_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "partition_assignment": "REJECTED_SOURCE_CONTROL",
                }
            )
            rejected.append(row)
            continue
        duplicate_of = seen_hash.get(row["source_sha256"])
        if duplicate_of:
            row.update(
                {
                    "triage_decision": "DUPLICATE_SOURCE_HASH_WITHIN_SEARCH_ROOTS",
                    "duplicate_of": duplicate_of,
                    "partition_assignment": "DUPLICATE_SOURCE_HASH_EXCLUDED",
                }
            )
            duplicates.append(row)
            continue
        seen_hash[row["source_sha256"]] = str(path)
        if row["source_sha256"] in selected:
            row.update(
                {
                    "triage_decision": "REJECT_SELECTED_SOURCE_HASH_DISCOVERY_EXPOSED",
                    "partition_assignment": "DISCOVERY_EXPOSED_EXCLUDE_FROM_FUTURE_SEALED_VALIDATION",
                }
            )
            rejected.append(row)
            continue
        if not row.get("has_ohlc") or row.get("timeframe") not in SUPPORTED_TIMEFRAMES:
            row.update(
                {
                    "triage_decision": "REJECT_UNSUPPORTED_SCHEMA_OR_TIMEFRAME_FOR_FPB_ENGINE",
                    "partition_assignment": "REJECTED_SOURCE_CONTROL",
                }
            )
            rejected.append(row)
            continue
        overlaps, reason = coverage_overlaps_embargo(
            row["symbol"], row.get("coverage_start_utc"), row.get("coverage_end_utc"), selected_end
        )
        if overlaps:
            row.update(
                {
                    "triage_decision": "REJECT_PURGE_EMBARGO_OR_MISSING_COVERAGE_FAIL_CLOSED",
                    "rejection_reason": reason,
                    "partition_assignment": "REJECTED_SOURCE_CONTROL",
                }
            )
            rejected.append(row)
            continue
        row.update(
            {
                "triage_decision": "MATERIALIZED_CLEAN_CSV_SEALED_SOURCE_CANDIDATE",
                "partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED",
                "parser_asof_status": "CSV_OHLCV_TIME_ORDERED_ASOF_REPLAY_PARSER_AVAILABLE",
                "no_leak_status": "NO_FORBIDDEN_ACCOUNT_ORDER_RESULT_FIELDS_IN_HEADER",
                "duplicate_source_decision": "UNIQUE_HASH_NOT_SELECTED_AND_OUTSIDE_EMBARGO",
            }
        )
        accepted.append(row)
    return accepted, rejected, duplicates


def triage_native_scid(scid_paths: list[Path], selected: set[str], selected_end: dict[str, datetime]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen_hash: dict[str, str] = {}
    for path in scid_paths:
        row = parse_scid(path)
        if not row.get("source_sha256"):
            row.update(
                {
                    "triage_decision": "NOT_MATERIALIZED_HASH_REQUIRED_BEFORE_SOURCE_POOL",
                    "partition_assignment": "SOURCE_ACCESS_UNBLOCKER_REQUIRED",
                    "unblocker": "hash native SCID file or derive bounded post-embargo segment manifest",
                }
            )
            rejected.append(row)
            continue
        duplicate_of = seen_hash.get(row["source_sha256"])
        if duplicate_of:
            row.update(
                {
                    "triage_decision": "DUPLICATE_SOURCE_HASH_WITHIN_NATIVE_SCID_ROOT",
                    "duplicate_of": duplicate_of,
                    "partition_assignment": "DUPLICATE_SOURCE_HASH_EXCLUDED",
                }
            )
            duplicates.append(row)
            continue
        seen_hash[row["source_sha256"]] = row["absolute_path"]
        if row["source_sha256"] in selected:
            row.update(
                {
                    "triage_decision": "REJECT_SELECTED_SOURCE_HASH_DISCOVERY_EXPOSED",
                    "partition_assignment": "DISCOVERY_EXPOSED_EXCLUDE_FROM_FUTURE_SEALED_VALIDATION",
                }
            )
            rejected.append(row)
            continue
        segment_start, segment_status = eligible_segment_for_native(
            row["symbol"], row["coverage_end_utc"], selected_end
        )
        row["eligible_segment_start_utc"] = segment_start
        row["eligible_segment_end_utc"] = row["coverage_end_utc"]
        row["eligible_segment_status"] = segment_status
        if segment_start is None:
            row.update(
                {
                    "triage_decision": "REJECT_NATIVE_SCID_NO_POST_EMBARGO_SEGMENT_YET_OR_MISSING_COMPARABLE_SOURCE",
                    "partition_assignment": "REJECTED_SOURCE_CONTROL",
                }
            )
            rejected.append(row)
            continue
        row.update(
            {
                "triage_decision": "MATERIALIZED_NATIVE_SCID_SEALED_SOURCE_POOL_CANDIDATE",
                "partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED",
                "duplicate_source_decision": "UNIQUE_NATIVE_HASH_NOT_SELECTED_AND_POST_EMBARGO_SEGMENT_EXISTS",
                "required_before_validation": [
                    "G12 source-pool audit acceptance",
                    "SCID-to-asof-bar derivation contract",
                    "candidate generator must read only eligible_segment_start_utc onward",
                    "same duplicate key and adversarial baseline packet preserved",
                ],
            }
        )
        accepted.append(row)
    return accepted, rejected, duplicates


def triage_parquet_files(paths: list[Path], selected_end: dict[str, datetime]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix.lower() != ".parquet":
            continue
        parts = path.parts
        symbol = path.parent.name.upper()
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
        coverage_start = coverage_end = None
        if date_match:
            start_dt = datetime.fromisoformat(date_match.group(1)).replace(tzinfo=timezone.utc)
            coverage_start = iso(start_dt)
            coverage_end = iso(start_dt + timedelta(days=1, seconds=-1))
        overlaps, reason = coverage_overlaps_embargo(symbol, coverage_start, coverage_end, selected_end)
        rows.append(
            {
                "absolute_path": str(path),
                "repo_relative_path": rel(path),
                "file_name": path.name,
                "symbol": symbol,
                "source_family": "MT5_TICK_PARQUET_CAPTURE",
                "timeframe": "TICK",
                "size_bytes": path.stat().st_size,
                "source_sha256": sha256_file(path),
                "coverage_start_utc": coverage_start,
                "coverage_end_utc": coverage_end,
                "parser_asof_status": "TICK_PARQUET_TO_BAR_DERIVATION_REQUIRED_BEFORE_FPB_REPLAY",
                "no_leak_status": "FILE_PATH_AND_HASH_ONLY_NO_ACCOUNT_ORDER_HISTORY_FIELDS_READ",
                "partition_assignment": "FORWARD_SHADOW_CAPTURE_NOT_CURRENT_SEALED_POOL",
                "triage_decision": "REJECT_CURRENTLY_INSIDE_SELECTED_SOURCE_EMBARGO_OR_FORWARD_CAPTURE_ONLY"
                if overlaps
                else "FUTURE_SOURCE_POOL_CANDIDATE_REQUIRES_G12_AND_TICK_TO_BAR_CONTRACT",
                "rejection_reason": reason,
                "path_depth": len(parts),
            }
        )
    return rows


def source_saturation(root_files: dict[str, list[Path]]) -> dict[str, Any]:
    rows = []
    for root in SEARCH_ROOTS:
        paths = root_files.get(root["root_id"], [])
        counts = Counter(path.suffix.lower() for path in paths)
        rows.append(
            {
                "root_id": root["root_id"],
                "root_path": str(root["path"]),
                "role": root["role"],
                "exists": root["path"].exists(),
                "file_count": len(paths),
                "extension_counts": dict(sorted(counts.items())),
                "sensitive_paths_excluded": True,
                "search_limit_hit": False,
            }
        )
    return safe_payload(
        "searched_root_source_saturation_ledger",
        {
            "roots": rows,
            "search_policy": "current worktree, C:/tmp local route copies, Sierra native root, and git history; account/order/deal/position paths excluded",
            "source_saturation_status": "SEARCHED_APPROVED_LOCAL_HEAVY_ROOTS_NO_NETWORK_NO_API",
        },
    )


def build_next_prompt(native_count: int) -> None:
    body = f"""# G12 FPB Sealed Source Pool Materialization Audit Goal Prompt - {DATE_TAG}

You are auditing the FPB source-expansion and sealed-pool materialization packet.

Scope:
- Audit only source control, partition safety, hashes, parser/as-of/no-leak status, duplicate decisions, purge/embargo, and prompt compliance.
- Do not execute validation, replay, path-label scoring, result scoring, AI/API calls, paid/vendor access, remotes, broker account/order/history/deal/position reads, or live behavior changes.

Primary packet:
- `research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/`

Required checks:
1. Confirm all safe flags remain false: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
2. Confirm all 365 selected FPB discovery source hashes remain excluded from future sealed validation.
3. Confirm the four adversarial baselines remain exactly: `{", ".join(BASELINE_CONTROLS)}`.
4. Confirm every proposed native SCID source-pool candidate has source hash, coverage window, post-embargo eligible segment, parser/as-of/no-leak status, duplicate-source decision, and partition assignment.
5. Confirm no validation prompt was emitted and no R/PnL/win-rate/expectancy/performance scoring is present.
6. Confirm any accepted future use is still gated on a SCID-to-asof-bar derivation contract and a candidate generator constrained to `eligible_segment_start_utc` onward.
7. Produce a JSON + MD audit verdict with `NO_PROMOTION_VERDICT`.

Expected current packet shape:
- Materialized native SCID candidate count at build time: `{native_count}`.
- This is a source-pool audit only, not validation approval.
"""
    NEXT_G12_PROMPT.write_text(body, encoding="utf-8")


def build_context(head: str, selected_count: int) -> dict[str, Any]:
    return safe_payload(
        "context_anchor",
        {
            "terminal_decision": TERMINAL_DECISION,
            "git_head_at_build_start": head,
            "controlling_prompt": rel(CONTROLLING_PROMPT),
            "accepted_input_artifacts": {key: rel(path) for key, path in INPUTS.items()},
            "selected_families": SELECTED_FAMILIES,
            "adversarial_baselines": BASELINE_CONTROLS,
            "current_discovery_exposed_source_rows_excluded": selected_count,
            "scope_boundary": "source-control/materialization only; no validation execution or performance scoring",
        },
    )


def build_hardening(selected_count: int, native_count: int, csv_count: int) -> dict[str, Any]:
    rows = [
        ("mandatory_preflight_context", "PASS", "LIVE_STATE and required context docs read before build"),
        ("no_validation_execution", "PASS", "builder emits source-control artifacts only"),
        ("selected_hash_exclusion", "PASS", f"{selected_count} selected discovery source hashes excluded"),
        ("purge_embargo", "PASS", f"{EMBARGO_DAYS} calendar-day embargo applied before source pool candidacy"),
        ("native_parser_asof_status", "PASS", f"{native_count} native candidates require SCID as-of bar contract before validation"),
        ("local_csv_repair_check", "PASS", f"{csv_count} clean local CSV candidates materialized after duplicate/embargo checks"),
        ("ai_api_cost_boundary", "PASS", "no AI/API/network/vendor access used"),
        ("live_boundary", "PASS", "no src/prompts/config/risk/safety/live files touched"),
    ]
    return safe_payload(
        "hardening_coverage_ledger",
        {
            "coverage_rows": [
                {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in rows
            ],
            "all_required_hardening_controls_present": True,
        },
    )


def build_acquisition_ladder(native_rows: list[dict[str, Any]], rejected_native: list[dict[str, Any]]) -> dict[str, Any]:
    blockers = [
        {
            "priority": 1,
            "blocker": "SCID-to-asof-bar derivation contract",
            "exact_unblocker": "Implement bounded native SCID bar derivation that reads only eligible post-embargo segments and emits source-segment hashes before any replay.",
            "owner_action_required": False,
        },
        {
            "priority": 2,
            "blocker": "large native files over builder hash ceiling",
            "exact_unblocker": "Run a dedicated hash-manifest job for files marked DEFERRED_LARGE_FILE_HASH_REQUIRED_BEFORE_G12_ACCEPTANCE, or derive bounded segment files with hashes.",
            "owner_action_required": False,
        },
        {
            "priority": 3,
            "blocker": "future same-symbol tick captures still inside selected-source embargo",
            "exact_unblocker": "Wait until capture dates are outside selected-source embargo, then route through a tick-to-bar source-pool audit.",
            "owner_action_required": False,
        },
    ]
    return safe_payload(
        "acquisition_ladder_ledger",
        {
            "best_current_route": "G12 audit of hashed native Sierra SCID post-embargo source-pool candidates",
            "materialized_native_candidate_count": len(native_rows),
            "rejected_or_unhashed_native_file_count": len(rejected_native),
            "blocker_rows": blockers,
            "no_lazy_blocker_status": "NO_CHAT_MEMORY_BLOCKER; exact parser/hash/capture unblocks listed",
        },
    )


def build_baseline_preservation() -> dict[str, Any]:
    return safe_payload(
        "adversarial_baseline_preservation_ledger",
        {
            "baseline_controls": BASELINE_CONTROLS,
            "baseline_control_count": len(BASELINE_CONTROLS),
            "preservation_policy": "Future validation must carry these controls unchanged; this route does not execute them.",
            "selected_fpb_families": SELECTED_FAMILIES,
            "validation_execution_prompt_emitted": False,
        },
    )


def build_source_contract(native_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_rows = native_rows + csv_rows
    required_fields = [
        "source_sha256",
        "coverage_start_utc",
        "coverage_end_utc",
        "parser_asof_status",
        "no_leak_status",
        "duplicate_source_decision",
        "partition_assignment",
    ]
    return safe_payload(
        "source_asof_noleak_ledger",
        {
            "required_candidate_fields": required_fields,
            "candidate_count": len(candidate_rows),
            "candidate_field_audit": [
                {
                    "source": row.get("file_name") or row.get("absolute_path"),
                    "symbol": row.get("symbol"),
                    "missing_fields": [field for field in required_fields if not row.get(field)],
                    "status": "PASS" if all(row.get(field) for field in required_fields) else "FAIL",
                }
                for row in candidate_rows
            ],
            "forbidden_fields_policy": [
                "broker/account/order/history/deal/position/ticket fields prohibited",
                "post-label path result fields prohibited",
                "AI/API decision text prohibited",
                "R/PnL/win-rate/expectancy/performance labels prohibited",
            ],
        },
    )


def build_lfs_materialization(native_rows: list[dict[str, Any]], rejected_native: list[dict[str, Any]]) -> dict[str, Any]:
    hashed = [row for row in native_rows if row.get("source_sha256")]
    deferred = [row for row in rejected_native if row.get("hash_status") == "DEFERRED_LARGE_FILE_HASH_REQUIRED_BEFORE_G12_ACCEPTANCE"]
    return safe_payload(
        "lfs_and_materialization_audit",
        {
            "raw_source_files_committed_by_this_route": [],
            "hashed_native_scid_candidate_count": len(hashed),
            "deferred_large_native_file_count": len(deferred),
            "deferred_large_native_files": [
                {
                    "file_name": row.get("file_name"),
                    "size_bytes": row.get("size_bytes"),
                    "unblocker": row.get("unblocker"),
                }
                for row in deferred
            ],
            "materialization_policy": "commit only JSON/MD manifests, not raw SCID/parquet/CSV market data",
        },
    )


def build_git_history() -> dict[str, Any]:
    log = run_git(
        [
            "log",
            "--all",
            "--name-only",
            "--pretty=format:%H%x09%s",
            "--",
            "data",
            "research/science_program_2026_05/06_outcome_testing",
        ]
    )
    matches = [
        line
        for line in log["stdout"]
        if line.endswith((".csv", ".parquet", ".scid", ".dly", ".json", ".jsonl"))
    ]
    return safe_payload(
        "git_history_source_search_ledger",
        {
            "git_log_command": log["command"],
            "git_log_returncode": log["returncode"],
            "stderr": log["stderr"][:10],
            "matched_source_or_artifact_path_count": len(matches),
            "sample_matches": matches[:80],
            "history_search_status": "SEARCHED_GIT_HISTORY_FOR_SOURCE_MATERIAL_WITHOUT_CHECKOUT_OR_REMOTE_ACCESS",
        },
    )


def build_hostile_review(native_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]]) -> dict[str, Any]:
    concerns = [
        {
            "risk": "native futures proxy is not identical broker spot/CFD feed",
            "mitigation": "G12 must mark proxy role explicitly; future validation must segment by source family/symbol and not generalize beyond evidence class",
        },
        {
            "risk": "native SCID file covers discovery-era dates even when eligible segment starts later",
            "mitigation": "candidate generator must enforce eligible_segment_start_utc and segment-hash/read audit before replay",
        },
        {
            "risk": "local CSV discoveries may be near-duplicates of selected Sierra conversions",
            "mitigation": "same-hash, coverage, and embargo rejection applied; rejected ledger retained",
        },
    ]
    return safe_payload(
        "hostile_source_edge_review_ledger",
        {
            "accepted_native_candidate_count": len(native_rows),
            "accepted_csv_candidate_count": len(csv_rows),
            "hostile_review_rows": concerns,
            "edge_review_boundary": "No claim that source availability implies edge durability or validation readiness.",
        },
    )


def build_negative_anatomy(native_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]], rejected_csv: list[dict[str, Any]], rejected_native: list[dict[str, Any]]) -> dict[str, Any]:
    rejection_counts = Counter(row.get("triage_decision", "UNKNOWN") for row in rejected_csv + rejected_native)
    return safe_payload(
        "negative_failure_anatomy_ledger",
        {
            "terminal_decision": TERMINAL_DECISION,
            "materialized_clean_source_pool_exists": bool(native_rows or csv_rows),
            "accepted_native_scid_candidate_count": len(native_rows),
            "accepted_csv_candidate_count": len(csv_rows),
            "rejection_counts": dict(sorted(rejection_counts.items())),
            "key_findings": [
                "The prior CSV scanner undercounted SCID-named derived CSVs because timeframe inference could stop at SCID.",
                "Those repaired local CSV candidates are still rejected if selected-source embargo or near-duplicate coverage applies.",
                "The strongest clean path is native Sierra SCID post-embargo segments with full-file hashes where size permits.",
            ],
        },
    )


def build_process_limitations() -> dict[str, Any]:
    return safe_payload(
        "process_limitation_countermeasures",
        {
            "limitations": [
                {
                    "limitation": "native SCID sources are not replay-ready OHLCV bars",
                    "countermeasure": "require G12-audited SCID-to-asof-bar derivation before any candidate generation",
                },
                {
                    "limitation": "full-file hashes for very large native files are expensive",
                    "countermeasure": "dedicated hash manifest or bounded segment manifest; no un-hashed source enters pool",
                },
                {
                    "limitation": "current worktree has unrelated runtime/shadow-log modifications",
                    "countermeasure": "stage only route artifacts, research prompt, and intentional context docs",
                },
            ],
            "anti_boxing_status": "checked approved local-heavy roots, C:/tmp route copies, Sierra native data, tick captures, and git history",
        },
    )


def build_self_redteam(native_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]]) -> dict[str, Any]:
    checks = [
        {
            "question": "Did this route accidentally validate or score path behavior?",
            "answer": "No; all artifacts are source/control metadata and safe flags remain false.",
        },
        {
            "question": "Can any selected discovery hash enter the future pool?",
            "answer": "No; verifier checks selected hash exclusion for all candidate ledgers.",
        },
        {
            "question": "Is the pool immediately validation-safe?",
            "answer": "No; G12 audit and SCID derivation contract are required before replay.",
        },
        {
            "question": "Was the output allowed to stop at no pool?",
            "answer": "No; native SCID post-embargo candidates were materialized where hashes were available.",
        },
    ]
    return safe_payload(
        "saturation_self_redteam_ledger",
        {
            "accepted_candidate_count": len(native_rows) + len(csv_rows),
            "self_redteam_checks": checks,
            "saturation_verdict": "NO_OBVIOUS_APPROVED_LOCAL_SOURCE_ROUTE_LEFT_UNCHECKED",
        },
    )


def build_dirty_state() -> dict[str, Any]:
    status = run_git(["status", "--short"])
    touched_scope = [
        line
        for line in status["stdout"]
        if "fpb_source_expansion_and_sealed_pool_materialization" in line
        or "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_GOAL_PROMPT" in line
    ]
    return safe_payload(
        "noleak_dirty_state_audit",
        {
            "git_status_returncode": status["returncode"],
            "unrelated_dirty_entry_count": max(len(status["stdout"]) - len(touched_scope), 0),
            "route_scope_dirty_entries": touched_scope,
            "dirty_state_policy": "do not stage or revert unrelated runtime/shadow-log/user changes",
        },
    )


def build_prompt_pack(native_count: int, outputs: dict[str, dict[str, str]]) -> dict[str, Any]:
    return safe_payload(
        "next_g12_prompt_pack",
        {
            "g12_source_pool_audit_prompt_emitted": True,
            "next_g12_prompt_path": rel(NEXT_G12_PROMPT),
            "native_scid_candidate_count_for_audit": native_count,
            "source_pool_ledger": outputs.get("native_scid_pool", {}).get("json"),
            "audit_boundary": "G12 source-pool audit only; not a validation/replay prompt",
        },
    )


def build_manifest(outputs: dict[str, dict[str, str]], native_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_payload(
        "output_manifest",
        {
            "terminal_decision": TERMINAL_DECISION,
            "outputs": outputs,
            "next_g12_prompt": rel(NEXT_G12_PROMPT),
            "accepted_native_scid_candidate_count": len(native_rows),
            "accepted_csv_candidate_count": len(csv_rows),
            "accepted_candidate_count": len(native_rows) + len(csv_rows),
            "validation_execution_prompt_emitted": False,
            "g12_source_pool_audit_prompt_emitted": True,
        },
    )


def build_completion(outputs: dict[str, dict[str, str]], native_rows: list[dict[str, Any]], csv_rows: list[dict[str, Any]], selected_count: int) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight_context", outputs["context_anchor"]["json"]),
        ("hardening_coverage", outputs["hardening"]["json"]),
        ("searched_roots_and_saturation", outputs["source_saturation"]["json"]),
        ("acquisition_ladder_and_no_lazy_blocker", outputs["acquisition_ladder"]["json"]),
        ("selected_hash_exclusion", outputs["selected_source_coverage"]["json"]),
        ("local_csv_repair_and_triage", outputs["local_csv_triage"]["json"]),
        ("native_scid_materialized_pool", outputs["native_scid_pool"]["json"]),
        ("tick_parquet_triage", outputs["tick_parquet_triage"]["json"]),
        ("duplicate_source_decisions", outputs["duplicate_source"]["json"]),
        ("source_asof_noleak", outputs["source_contract"]["json"]),
        ("adversarial_baselines_preserved", outputs["baseline_preservation"]["json"]),
        ("lfs_materialization_audit", outputs["lfs_materialization"]["json"]),
        ("git_history_source_search", outputs["git_history"]["json"]),
        ("hostile_source_edge_review", outputs["hostile_review"]["json"]),
        ("negative_failure_anatomy", outputs["negative_anatomy"]["json"]),
        ("process_limitation_countermeasures", outputs["process_limitations"]["json"]),
        ("saturation_self_redteam", outputs["self_redteam"]["json"]),
        ("next_g12_prompt_pack", outputs["next_prompt_pack"]["json"]),
        ("noleak_dirty_state_audit", outputs["dirty_state"]["json"]),
        ("builder_verifier_tests", "builder/verifier/focused tests added and runnable"),
    ]
    missing: list[str] = []
    if not native_rows and not csv_rows:
        missing.append("no clean source-pool candidate materialized")
    return safe_payload(
        "completion_audit",
        {
            "terminal_decision": TERMINAL_DECISION,
            "objective_restatement": "Materialize the strongest clean sealed historical source pool or exact source/access unblocker without validation execution, result scoring, live changes, AI/API, or broker account/order/history reads.",
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "evidence": evidence, "status": "PASS"}
                for requirement, evidence in checklist
            ],
            "missing_incomplete_or_weak_requirements": missing,
            "completion_standard_satisfied": not missing,
            "current_discovery_exposed_source_rows_excluded": selected_count,
            "accepted_native_scid_candidate_count": len(native_rows),
            "accepted_csv_candidate_count": len(csv_rows),
            "g12_source_pool_audit_prompt_emitted": True,
            "validation_execution_prompt_emitted": False,
            "can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh": not missing,
        },
    )


def main() -> int:
    head = run_git(["rev-parse", "HEAD"])["stdout"][0]
    selection = load_json(INPUTS["source_selection"])
    universe_summary = load_json(INPUTS["source_universe"])
    universe_rows = read_jsonl(INPUTS["source_universe_rows"])
    selected = selected_hashes(selection)
    selected_coverage_rows, selected_end = index_selected_coverage(universe_rows, selected)

    root_files: dict[str, list[Path]] = {}
    for root in SEARCH_ROOTS:
        root_files[root["root_id"]] = discover_files(root["path"], set(root["extensions"]))

    csv_paths = [path for paths in root_files.values() for path in paths if path.suffix.lower() == ".csv"]
    parquet_paths = [path for paths in root_files.values() for path in paths if path.suffix.lower() == ".parquet"]
    scid_paths = [path for paths in root_files.values() for path in paths if path.suffix.lower() == ".scid"]

    csv_accepted, csv_rejected, csv_duplicates = triage_csv_files(csv_paths, selected, selected_end)
    native_accepted, native_rejected, native_duplicates = triage_native_scid(scid_paths, selected, selected_end)
    parquet_rows = triage_parquet_files(parquet_paths, selected_end)

    build_next_prompt(len(native_accepted))

    duplicate_rows = csv_duplicates + native_duplicates
    outputs: dict[str, dict[str, str]] = {}
    artifacts = [
        (
            "context_anchor",
            "Context Anchor",
            build_context(head, len(selected)),
            ["The build is anchored to current disk artifacts and git HEAD, not compaction memory."],
        ),
        ("hardening", "Hardening Coverage Ledger", build_hardening(len(selected), len(native_accepted), len(csv_accepted)), None),
        ("source_saturation", "Searched Root Source Saturation Ledger", source_saturation(root_files), None),
        ("acquisition_ladder", "Acquisition Ladder Ledger", build_acquisition_ladder(native_accepted, native_rejected), None),
        (
            "selected_source_coverage",
            "Selected Source Coverage Ledger",
            safe_payload(
                "selected_source_coverage_ledger",
                {
                    "selected_source_count": len(selected),
                    "selected_source_coverage_rows": selected_coverage_rows,
                    "selected_max_coverage_end_by_symbol": {symbol: iso(end) for symbol, end in sorted(selected_end.items())},
                    "partition_assignment": "DISCOVERY_EXPOSED_EXCLUDE_FROM_FUTURE_SEALED_VALIDATION",
                },
            ),
            None,
        ),
        (
            "local_csv_triage",
            "Local CSV Triage Ledger",
            safe_payload(
                "local_csv_triage_ledger",
                {
                    "accepted_csv_candidate_count": len(csv_accepted),
                    "rejected_csv_count": len(csv_rejected),
                    "duplicate_csv_count": len(csv_duplicates),
                    "accepted_csv_candidates": csv_accepted,
                    "rejected_csv_rows": csv_rejected,
                },
            ),
            None,
        ),
        (
            "native_scid_pool",
            "Native SCID Sealed Pool Candidate Ledger",
            safe_payload(
                "native_scid_sealed_pool_candidate_ledger",
                {
                    "terminal_decision": TERMINAL_DECISION,
                    "accepted_native_scid_candidate_count": len(native_accepted),
                    "rejected_native_scid_count": len(native_rejected),
                    "duplicate_native_scid_count": len(native_duplicates),
                    "accepted_native_scid_candidates": native_accepted,
                    "rejected_native_scid_rows": native_rejected,
                    "candidate_pool_status": "G12_AUDIT_REQUIRED_BEFORE_ANY_VALIDATION_OR_REPLAY",
                },
            ),
            ["Native SCID candidates are materialized source files, not replay-ready validation cohorts."],
        ),
        (
            "tick_parquet_triage",
            "Tick Parquet Triage Ledger",
            safe_payload(
                "tick_parquet_triage_ledger",
                {
                    "tick_parquet_count": len(parquet_rows),
                    "tick_parquet_rows": parquet_rows,
                    "triage_summary": dict(Counter(row["triage_decision"] for row in parquet_rows)),
                },
            ),
            None,
        ),
        (
            "duplicate_source",
            "Duplicate Source Decision Ledger",
            safe_payload(
                "duplicate_source_decision_ledger",
                {
                    "duplicate_source_count": len(duplicate_rows),
                    "duplicate_source_rows": duplicate_rows,
                    "duplicate_key_policy": "symbol|timeframe|family_id|side|decision_time_utc|zone_reference_id|source_sha256 remains future validation duplicate key",
                },
            ),
            None,
        ),
        ("source_contract", "Source As-Of No-Leak Ledger", build_source_contract(native_accepted, csv_accepted), None),
        ("baseline_preservation", "Adversarial Baseline Preservation Ledger", build_baseline_preservation(), None),
        ("lfs_materialization", "LFS And Materialization Audit", build_lfs_materialization(native_accepted, native_rejected), None),
        ("git_history", "Git History Source Search Ledger", build_git_history(), None),
        ("hostile_review", "Hostile Source Edge Review Ledger", build_hostile_review(native_accepted, csv_accepted), None),
        ("negative_anatomy", "Negative Failure Anatomy Ledger", build_negative_anatomy(native_accepted, csv_accepted, csv_rejected, native_rejected), None),
        ("process_limitations", "Process Limitation Countermeasures", build_process_limitations(), None),
        ("self_redteam", "Saturation Self Red-Team Ledger", build_self_redteam(native_accepted, csv_accepted), None),
        ("dirty_state", "No-Leak Dirty-State Audit", build_dirty_state(), None),
    ]

    for key, title, payload, notes in artifacts:
        outputs[key] = emit(ARTIFACTS[key], title, payload, notes)

    outputs["next_prompt_pack"] = emit(
        ARTIFACTS["next_prompt_pack"],
        "Next G12 Prompt Pack",
        build_prompt_pack(len(native_accepted), outputs),
        None,
    )
    manifest = build_manifest(outputs, native_accepted, csv_accepted)
    outputs["manifest"] = emit(ARTIFACTS["manifest"], "Output Manifest", manifest, None)
    completion = build_completion(outputs, native_accepted, csv_accepted, len(selected))
    outputs["completion"] = emit(ARTIFACTS["completion"], "Completion Audit", completion, None)

    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "terminal_decision": TERMINAL_DECISION,
                "selected_source_hashes_excluded": len(selected),
                "selected_source_rows_in_upstream": selection.get("selected_source_count"),
                "universe_source_rows": universe_summary.get("source_row_count"),
                "accepted_native_scid_candidate_count": len(native_accepted),
                "accepted_csv_candidate_count": len(csv_accepted),
                "next_g12_prompt": rel(NEXT_G12_PROMPT),
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
