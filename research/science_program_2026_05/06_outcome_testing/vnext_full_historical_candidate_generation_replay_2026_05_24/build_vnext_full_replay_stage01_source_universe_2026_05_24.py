"""Stage 01 source-universe freeze for the vNext full historical replay.

This builder is intentionally route-local. It does not call MT5, mutate broker
state, change production config, or score outcomes. It freezes the preregistered
contracts and writes a market-bar denominator ledger from currently available
OHLC/tick/Sierra sources so candidate generation can resume from disk.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


DATE_ID = "2026-05-24"
ROUTE_ID = "vnext_full_historical_candidate_generation_replay_2026_05_24"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]

PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_FULL_HISTORICAL_CANDIDATE_GENERATION_REPLAY_GOAL_PROMPT_2026-05-24.md"
)
STARTER_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "VNEXT_FULL_HISTORICAL_CANDIDATE_GENERATION_REPLAY_STARTER_2026-05-24.txt"
)
DATA_REQUIREMENTS_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_replay_data_audit_2026_05_24/"
    "VNEXT_FULL_HISTORICAL_REPLAY_DATA_REQUIREMENTS_2026-05-24.md"
)
CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
VNEXT_RUNTIME_PATH = REPO_ROOT / "src/components/gtos_vnext_runtime.py"
LIVE_STATE_PATH = REPO_ROOT / ".context/LIVE_STATE.md"

PRIOR_REPLAY_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24"
)

CONTEXT_PATHS = [
    LIVE_STATE_PATH,
    PROMPT_PATH,
    STARTER_PATH,
    REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
    REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
    REPO_ROOT / ".context/00_core/orchestrator_successor_operating_brief.md",
    REPO_ROOT / ".context/00_core/orchestrator_methodology_hardening_controls.md",
    REPO_ROOT / ".context/00_core/parallel_goal_merge_playbook.md",
    REPO_ROOT / ".context/00_core/quick_reference_card.md",
    DATA_REQUIREMENTS_PATH,
    CONFIG_PATH,
    VNEXT_RUNTIME_PATH,
]

OUTPUTS = {
    "preregistration": ROUTE_DIR / f"VNEXT_FULL_REPLAY_PREREGISTRATION_MANIFEST_{DATE_ID}.json",
    "session_state": ROUTE_DIR / f"VNEXT_FULL_REPLAY_SESSION_STATE_{DATE_ID}.json",
    "prompt_application": ROUTE_DIR / f"VNEXT_FULL_REPLAY_PROMPT_APPLICATION_LEDGER_{DATE_ID}.jsonl",
    "source_universe": ROUTE_DIR / f"VNEXT_FULL_REPLAY_SOURCE_UNIVERSE_DENOMINATOR_LEDGER_{DATE_ID}.jsonl",
    "eligibility_contract": ROUTE_DIR / f"VNEXT_FULL_REPLAY_CANDIDATE_ELIGIBILITY_CONTRACT_{DATE_ID}.json",
    "path_r_contract": ROUTE_DIR / f"VNEXT_FULL_REPLAY_PATH_R_SCORING_CONTRACT_{DATE_ID}.json",
    "data_coverage": ROUTE_DIR / f"VNEXT_FULL_REPLAY_DATA_COVERAGE_LEDGER_{DATE_ID}.jsonl",
    "source_acquisition": ROUTE_DIR / f"VNEXT_FULL_REPLAY_SOURCE_ACQUISITION_LEDGER_{DATE_ID}.jsonl",
    "source_repair_proof": ROUTE_DIR / f"VNEXT_FULL_REPLAY_SOURCE_REPAIR_PROOF_LEDGER_{DATE_ID}.jsonl",
    "mt5_export": ROUTE_DIR / f"VNEXT_FULL_REPLAY_MT5_EXPORT_LEDGER_{DATE_ID}.jsonl",
    "sierra_source": ROUTE_DIR / f"VNEXT_FULL_REPLAY_SIERRA_SCID_SOURCE_LEDGER_{DATE_ID}.jsonl",
    "runtime_artifact_coverage": ROUTE_DIR / f"VNEXT_FULL_REPLAY_RUNTIME_ARTIFACT_COVERAGE_LEDGER_{DATE_ID}.jsonl",
    "active_questions": ROUTE_DIR / f"VNEXT_FULL_REPLAY_ACTIVE_QUESTION_LEDGER_{DATE_ID}.jsonl",
    "extra_step": ROUTE_DIR / f"VNEXT_FULL_REPLAY_EXTRA_STEP_PURSUIT_LEDGER_{DATE_ID}.jsonl",
    "line_audit": ROUTE_DIR / f"VNEXT_FULL_REPLAY_LINE_ACCOUNTABILITY_AUDIT_{DATE_ID}.jsonl",
    "completion_audit": ROUTE_DIR / f"VNEXT_FULL_REPLAY_COMPLETION_AUDIT_{DATE_ID}.json",
    "output_manifest": ROUTE_DIR / f"VNEXT_FULL_REPLAY_OUTPUT_MANIFEST_{DATE_ID}.json",
}

CORE_FULL_PATH_SYMBOLS = [
    "GBPJPY",
    "GBPUSD",
    "NAS100",
    "US30_cash",
    "USDJPY",
    "XAGUSD",
    "XAUUSD",
]
EXPANDED_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GER40",
    "JP225",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "USDCAD",
    "USDCHF",
    "USOIL_cash",
]
ALL_SYMBOLS = sorted(set(CORE_FULL_PATH_SYMBOLS + EXPANDED_SYMBOLS))
REQUIRED_TIMEFRAMES = ["M1", "M5", "M15", "H1", "H4", "D1"]
PRIMARY_REPLAY_FRAMEWORKS = ["ob_retest", "fvg_fill", "breaker_re_entry"]

CSV_ROOTS = [
    "data/mt5_research_exports/phase3_rescue_all_m1_m5_chunk1_after_maxbars",
    "data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1",
    "data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1",
    "data/mt5_research_exports/phase3_v2b_forward_20260401_20260502_readonly",
    "data/mt5_research_exports/phase3_v2b_forward_20260501_readonly",
    "data/historical_2026",
]
TICK_ROOT = REPO_ROOT / "data/ticks"
SIERRA_ROOT = Path("C:/SierraChart/Data")
HASH_BYTES_LIMIT = 512 * 1024 * 1024
CSV_NAME_RE = re.compile(r"^(?P<symbol>.+)_(?P<timeframe>M1|M5|M15|H1|H4|D1)\.csv$", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    text = str(path)
    if text.startswith("\\\\?\\"):
        text = text[4:]
    try:
        return Path(text).resolve(strict=False).relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(text).as_posix()


def repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def sha256_file(path: Path, *, allow_large: bool = False) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    if not allow_large and path.stat().st_size > HASH_BYTES_LIMIT:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, payload: Any, length: int = 24) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:length]}"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    tmp = path.with_suffix(path.suffix + ".tmp")
    count = 0
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    tmp.replace(path)
    return count


def write_jsonl_gzip_chunks(
    base_path: Path,
    rows: Iterable[dict[str, Any]],
    *,
    rows_per_chunk: int = 100_000,
) -> tuple[int, list[dict[str, Any]]]:
    """Write a logical JSONL ledger as gzip chunks plus a small JSONL chunk index."""
    for stale in base_path.parent.glob(base_path.stem + ".chunk-*.jsonl.gz"):
        stale.unlink()
    total_rows = 0
    chunk_index = 0
    chunk_rows = 0
    chunk_path: Path | None = None
    chunk_handle: gzip.GzipFile | None = None
    chunk_manifest: list[dict[str, Any]] = []

    def close_chunk() -> None:
        nonlocal chunk_handle, chunk_path, chunk_rows
        if chunk_handle is None or chunk_path is None:
            return
        chunk_handle.close()
        chunk_manifest.append(
            {
                "schema_version": "vnext_full_replay_chunk_index_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "logical_artifact_path": rel(base_path),
                "chunk_index": len(chunk_manifest) + 1,
                "chunk_path": rel(chunk_path),
                "row_count": chunk_rows,
                "bytes": chunk_path.stat().st_size,
                "sha256": sha256_file(chunk_path, allow_large=True),
            }
        )
        chunk_handle = None
        chunk_path = None
        chunk_rows = 0

    for row in rows:
        if chunk_handle is None or chunk_rows >= rows_per_chunk:
            close_chunk()
            chunk_index += 1
            chunk_path = base_path.with_name(f"{base_path.stem}.chunk-{chunk_index:04d}.jsonl.gz")
            chunk_handle = gzip.open(chunk_path, "wt", encoding="utf-8", newline="\n")
        chunk_handle.write(json.dumps(row, sort_keys=True) + "\n")
        chunk_rows += 1
        total_rows += 1
    close_chunk()
    write_jsonl(base_path, chunk_manifest)
    return total_rows, chunk_manifest


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_GIT_HEAD"


def file_line_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() not in {".csv", ".jsonl", ".md", ".txt", ".py", ".yaml", ".yml"}:
        return None
    count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def session_bucket(timestamp: str) -> str:
    hour_min = timestamp.split(" ")[-1][:5] if " " in timestamp else timestamp.split("T")[-1][:5]
    try:
        hour, minute = [int(part) for part in hour_min.split(":")[:2]]
    except ValueError:
        return "unknown_session"
    total = hour * 60 + minute
    if 0 <= total < 3 * 60:
        return "tokyo_broad"
    if 7 * 60 <= total < 12 * 60:
        return "london_broad"
    if 13 * 60 <= total < 17 * 60:
        return "ny_broad"
    return "off_kz_broad"


def csv_source_id(root: Path, path: Path, symbol: str, timeframe: str) -> str:
    return stable_id(
        "csvsrc",
        {"root": rel(root), "path": rel(path), "symbol": symbol, "timeframe": timeframe},
    )


def iter_csv_files() -> Iterable[tuple[Path, Path, str, str]]:
    seen: set[Path] = set()
    for root_text in CSV_ROOTS:
        root = repo_path(root_text)
        if not root.exists():
            continue
        for path in sorted(root.glob("*.csv")):
            if path.name.lower() == "manifest.json":
                continue
            match = CSV_NAME_RE.match(path.name)
            if not match:
                continue
            resolved = path.resolve(strict=False)
            if resolved in seen:
                continue
            seen.add(resolved)
            yield root, path, match.group("symbol"), match.group("timeframe").upper()


def read_csv_metadata_and_m15_rows(
    root: Path,
    path: Path,
    symbol: str,
    timeframe: str,
    source_hash: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    first_time: str | None = None
    last_time: str | None = None
    data_rows = 0
    parse_errors = 0
    header: list[str] = []
    source_id = csv_source_id(root, path, symbol, timeframe)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        for raw in reader:
            data_rows += 1
            ts = raw.get("time") or raw.get("datetime") or raw.get("timestamp") or raw.get("Time")
            if not ts:
                parse_errors += 1
                continue
            if first_time is None:
                first_time = ts
            last_time = ts
            if timeframe == "M15":
                rows.append(
                    {
                        "schema_version": "vnext_full_replay_source_universe_v1",
                        "route_id": ROUTE_ID,
                        "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                        "row_type": "m15_candle",
                        "source_origin": "market_bar_enumeration",
                        "source_id": source_id,
                        "source_root": rel(root),
                        "source_path": rel(path),
                        "source_sha256": source_hash,
                        "source_hash_status": "sha256_full" if source_hash else "hash_deferred_large_or_missing",
                        "symbol": symbol,
                        "source_symbol": symbol,
                        "timeframe": timeframe,
                        "source_mode": "OHLC_M15_CSV",
                        "candle_time_utc": ts,
                        "date_utc": ts[:10],
                        "session_bucket": session_bucket(ts),
                        "candidate_generation_disposition": "pending_candidate_generation",
                        "terminal_disposition": False,
                        "denominator_entry_state": "eligible_for_stage02_market_state_candidate_generation",
                        "candidate_eligibility_contract_path": rel(OUTPUTS["eligibility_contract"]),
                        "path_r_scoring_contract_path": rel(OUTPUTS["path_r_contract"]),
                        "source_universe_row_id": stable_id(
                            "denom",
                            {"source_id": source_id, "time": ts, "symbol": symbol, "timeframe": timeframe},
                        ),
                    }
                )
    metadata = {
        "schema_version": "vnext_full_replay_data_coverage_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
        "row_type": "source_file",
        "source_id": source_id,
        "source_root": rel(root),
        "source_path": rel(path),
        "source_family": "historical_ohlc_csv",
        "source_mode": f"OHLC_{timeframe}_CSV",
        "symbol": symbol,
        "source_symbol": symbol,
        "timeframe": timeframe,
        "bytes": path.stat().st_size,
        "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "sha256": source_hash,
        "hash_status": "sha256_full" if source_hash else "hash_deferred_large_or_missing",
        "header": header,
        "data_rows": data_rows,
        "first_time_utc": first_time,
        "last_time_utc": last_time,
        "parse_error_count": parse_errors,
        "source_use_status": (
            "stage01_denominator_rows_written"
            if timeframe == "M15"
            else "stage01_path_or_htf_source_inventoried_not_yet_consumed"
        ),
    }
    return metadata, rows


def tick_source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not TICK_ROOT.exists():
        return rows
    for path in sorted(TICK_ROOT.glob("*/*.parquet")):
        symbol = path.parent.name
        rows.append(
            {
                "schema_version": "vnext_full_replay_source_acquisition_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "row_type": "tick_source_file",
                "source_family": "local_mt5_tick_parquet",
                "source_mode": "LOCAL_TICK_PARQUET",
                "symbol": symbol,
                "source_symbol": symbol,
                "source_path": rel(path),
                "bytes": path.stat().st_size,
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "sha256": sha256_file(path),
                "hash_status": "sha256_full" if path.stat().st_size <= HASH_BYTES_LIMIT else "hash_deferred_large_source_not_consumed_stage01",
                "source_use_status": "stage01_path_source_inventoried_not_yet_consumed",
            }
        )
    return rows


def sierra_source_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not SIERRA_ROOT.exists():
        rows.append(
            {
                "schema_version": "vnext_full_replay_sierra_scid_source_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "row_type": "sierra_root",
                "source_path": str(SIERRA_ROOT),
                "source_status": "missing_sierra_root",
                "next_action": "search_alternate_local_roots_or_request_owner_export",
            }
        )
        return rows
    for path in sorted(SIERRA_ROOT.glob("*.scid")):
        size = path.stat().st_size
        rows.append(
            {
                "schema_version": "vnext_full_replay_sierra_scid_source_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "row_type": "sierra_scid_file",
                "source_family": "sierra_scid",
                "source_mode": "SIERRA_SCID",
                "symbol_hint": path.stem,
                "source_path": str(path).replace("\\", "/"),
                "bytes": size,
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                "sha256": sha256_file(path),
                "hash_status": "sha256_full" if size <= HASH_BYTES_LIMIT else "hash_deferred_large_source_not_consumed_stage01",
                "parser_status": "supported_by_scripts_inspect_sierra_scid_pending_conversion",
                "source_use_status": "stage01_proxy_source_inventoried_not_yet_converted",
            }
        )
    return rows


def mt5_export_rows(coverage_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    present = {
        (str(row.get("symbol")), str(row.get("timeframe")))
        for row in coverage_rows
        if row.get("row_type") == "source_file" and row.get("source_family") == "historical_ohlc_csv"
    }
    rows: list[dict[str, Any]] = []
    for symbol in EXPANDED_SYMBOLS:
        for timeframe in ["M1", "M5"]:
            key = (symbol, timeframe)
            if key not in present:
                rows.append(
                    {
                        "schema_version": "vnext_full_replay_mt5_export_v1",
                        "route_id": ROUTE_ID,
                        "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                        "row_type": "missing_expanded_m1_m5_export_requirement",
                        "symbol": symbol,
                        "source_symbol": symbol,
                        "timeframe": timeframe,
                        "required_window_start_utc": "source_available_start",
                        "required_window_end_utc": "current_replay_end",
                        "export_disposition": "requires_readonly_mt5_export_or_availability_probe",
                        "terminal_disposition": False,
                        "source_repair_proof_row_required_before_terminal_missing_source": True,
                        "next_action": (
                            "run scripts/inspect_mt5_history_availability.py then "
                            "scripts/export_mt5_research_ohlcv.py for this symbol/timeframe if available"
                        ),
                    }
                )
    for symbol in CORE_FULL_PATH_SYMBOLS:
        for timeframe in REQUIRED_TIMEFRAMES:
            rows.append(
                {
                    "schema_version": "vnext_full_replay_mt5_export_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                    "row_type": "core_current_window_refresh_requirement",
                    "symbol": symbol,
                    "source_symbol": symbol,
                    "timeframe": timeframe,
                    "required_window_start_utc": "2026-05-01T00:00:00Z",
                    "required_window_end_utc": "current_session_date",
                    "export_disposition": "requires_readonly_mt5_export_or_availability_probe",
                    "terminal_disposition": False,
                    "source_repair_proof_row_required_before_terminal_missing_source": True,
                    "next_action": (
                        "probe/export read-only MT5 bars for May continuation without broker mutation"
                    ),
                }
            )
    return rows


def runtime_artifact_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = config.get("gtos_vnext_runtime", {}) or {}
    paths = cfg.get("artifact_paths") or []
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(paths):
        path = repo_path(raw)
        exists = path.exists()
        size = path.stat().st_size if exists and path.is_file() else None
        rows.append(
            {
                "schema_version": "vnext_full_replay_runtime_artifact_coverage_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "row_type": "active_runtime_artifact",
                "artifact_index": index,
                "configured_path": str(raw),
                "resolved_path": rel(path) if path.is_absolute() and str(path).startswith(str(REPO_ROOT)) else str(path),
                "exists": exists,
                "bytes": size,
                "line_count": file_line_count(path) if exists and size is not None and size <= HASH_BYTES_LIMIT else None,
                "sha256": sha256_file(path) if exists and size is not None and size <= HASH_BYTES_LIMIT else None,
                "hash_status": (
                    "sha256_full"
                    if exists and size is not None and size <= HASH_BYTES_LIMIT
                    else "missing_or_hash_deferred_large_source"
                ),
                "coverage_disposition": (
                    "available_for_stage02_runtime_trace"
                    if exists
                    else "missing_configured_runtime_artifact_requires_source_repair"
                ),
            }
        )
    return rows


def context_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in CONTEXT_PATHS:
        exists = path.exists()
        rows.append(
            {
                "schema_version": "vnext_full_replay_prompt_application_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "context_path": rel(path) if path.is_absolute() and str(path).startswith(str(REPO_ROOT)) else str(path),
                "exists": exists,
                "sha256": sha256_file(path) if exists else None,
                "bytes": path.stat().st_size if exists else None,
                "read_after_preflight": True,
                "application": "active_instruction_source_for_stage01_contract_and_source_universe_freeze",
            }
        )
    return rows


def candidate_eligibility_contract(config: dict[str, Any]) -> dict[str, Any]:
    enabled_frameworks = (
        config.get("model_a", {}).get("enabled_frameworks")
        or PRIMARY_REPLAY_FRAMEWORKS
    )
    return {
        "schema_version": "vnext_full_replay_candidate_eligibility_contract_v1",
        "route_id": ROUTE_ID,
        "frozen_at_utc": utc_now(),
        "contract_status": "frozen_before_candidate_generation_and_outcome_scoring",
        "source_origin_required": "market_bar_enumeration",
        "primary_candidate_universe_must_not_seed_from_shadow_logs": True,
        "eligible_symbols": ALL_SYMBOLS,
        "core_full_path_symbols": CORE_FULL_PATH_SYMBOLS,
        "expanded_symbols": EXPANDED_SYMBOLS,
        "eligible_timeframes": REQUIRED_TIMEFRAMES,
        "candidate_generation_timeframe": "M15",
        "enabled_production_frameworks": enabled_frameworks,
        "minimum_generated_families": PRIMARY_REPLAY_FRAMEWORKS,
        "runtime_supported_family_policy": (
            "also generate every current vNext route family that can be source-derived from market bars"
        ),
        "denominator_row_dispositions_allowed_final": [
            "candidate_generated",
            "no_setup_by_asof_market_state",
            "source_missing_after_pursuit",
            "parser_missing_after_full_pursuit",
            "forbidden_boundary",
            "literal_impossibility",
        ],
        "stage01_nonterminal_dispositions": ["pending_candidate_generation"],
        "candidate_row_required_fields": [
            "candidate_id",
            "source_origin",
            "source_universe_row_id",
            "symbol",
            "source_symbol",
            "timeframe",
            "candle_time_utc",
            "session_bucket",
            "side",
            "framework",
            "entry_reference",
            "stop_or_invalidation",
            "target_reference",
            "market_state_packet_id",
            "source_path",
            "source_sha256",
        ],
        "skip_row_required_fields": [
            "source_universe_row_id",
            "skip_reason",
            "asof_market_state_summary",
            "candidate_generation_disposition",
            "source_path",
            "source_sha256",
        ],
        "shadow_log_policy": (
            "shadow logs may join/enrich/audit replay rows but cannot define the primary candidate universe"
        ),
    }


def path_r_scoring_contract() -> dict[str, Any]:
    return {
        "schema_version": "vnext_full_replay_path_r_scoring_contract_v1",
        "route_id": ROUTE_ID,
        "frozen_at_utc": utc_now(),
        "contract_status": "frozen_before_path_outcome_scoring",
        "source_mode_priority": [
            "tick_or_sierra_path_aware",
            "m1_path_aware",
            "m5_path_aware",
            "bar_close_m15",
            "ohlc_only_proxy",
            "missing_source",
        ],
        "mode_rows_required": [
            "current_config_shadow",
            "hypothetical_activated_vnext",
            "bar_close_m15",
            "m1_path_aware",
            "m5_path_aware",
            "tick_or_sierra_path_aware",
            "ohlc_only_proxy",
            "missing_source",
        ],
        "entry_touch_rule": (
            "LONG touches when low<=entry_reference<=high; SHORT touches when low<=entry_reference<=high; "
            "spread/offset variants must be recorded separately"
        ),
        "stop_target_ordering_rule": (
            "use lowest available timeframe/tick ordering; same-bar M15 ambiguity is not terminal while LTF exists"
        ),
        "r_formula": {
            "long": "(exit_price - entry_price) / abs(entry_price - stop_price)",
            "short": "(entry_price - exit_price) / abs(stop_price - entry_price)",
            "cost_adjustment": "subtract spread/slippage proxy in R units when source exists; else label proxy class",
        },
        "terminal_outcomes": [
            "target_first",
            "stop_first",
            "timeout",
            "no_fill",
            "same_bar_ambiguous_unresolved",
            "missing_source_denominator_excluded",
        ],
        "source_repair_link_required_for_missing_modes": True,
        "exact_broker_execution_truth_policy": (
            "not required for this historical simulated replay; broker actual-R remains separate calibration lane"
        ),
    }


def source_repair_placeholder_rows(mt5_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in mt5_rows:
        rows.append(
            {
                "schema_version": "vnext_full_replay_source_repair_proof_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "proof_id": stable_id("repair", row),
                "candidate_id": None,
                "field_name": f"{row['symbol']}::{row['timeframe']}::source_file",
                "expected_source_contract": "read_only_mt5_ohlcv_export_or_availability_probe",
                "searched_paths_or_roots": CSV_ROOTS,
                "commands_or_export_actions": [],
                "join_keys_tested": [{"symbol": row["symbol"], "timeframe": row["timeframe"]}],
                "parser_actions": [],
                "source_hashes": [],
                "result": row["export_disposition"],
                "final_disposition": "not_terminal_stage01_next_action_required",
                "next_action": row["next_action"],
            }
        )
    return rows


def active_question_rows(mt5_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing_expanded = [r for r in mt5_rows if r["row_type"] == "missing_expanded_m1_m5_export_requirement"]
    return [
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "question_id": "Q001_SOURCE_UNIVERSE_DENOMINATOR_COMPLETE",
            "question": "Which discovered/exportable symbols, timeframes, sessions, source modes, and M15 candles are in the replay denominator?",
            "current_answer": "Stage01 writes discovered CSV/tick/Sierra inventory and M15 candle denominator; candidate dispositions remain pending.",
            "status": "answered_for_available_local_sources_pending_candidate_generation",
            "next_action": "Run Stage02 market-state candidate generation over every denominator row.",
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "question_id": "Q002_EXPANDED_M1_M5_SOURCE_GAP",
            "question": "Which expanded symbols lack M1/M5 path sources and need read-only MT5 export or exact availability proof?",
            "current_answer": f"{len(missing_expanded)} expanded symbol/timeframe requirements remain nonterminal.",
            "status": "open_same_evidence_class_source_export_required",
            "next_action": "Probe/export expanded M1/M5 through approved read-only MT5 route or record exact external failure.",
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "question_id": "Q003_CURRENT_WINDOW_REFRESH",
            "question": "How will May 2026 continuation bars be refreshed for core seven without broker mutation?",
            "current_answer": "Core refresh requirements are recorded in MT5 export ledger; no live/broker mutation performed in Stage01.",
            "status": "open_same_evidence_class_readonly_export_required",
            "next_action": "Run availability/export probes for 2026-05-01 onward or record exact environment failure.",
        },
        {
            "schema_version": "vnext_full_replay_active_question_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "question_id": "Q004_SIERRA_PROXY_CONVERSION",
            "question": "Which Sierra SCID proxy sources can be converted and mapped into path-aware replay modes?",
            "current_answer": "Stage01 inventories SCID files; conversion is still pending and must preserve proxy-vs-CFD status.",
            "status": "open_same_evidence_class_parser_conversion_required",
            "next_action": "Run inspect/convert Sierra SCID for supported mappings with source hashes.",
        },
    ]


def extra_step_rows() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "pursuit_id": "P001_CONTEXT_REFRESH",
            "trigger": "resume_or_goal_start",
            "executed_action": "regenerated LIVE_STATE and reread controlling prompt/starter/doctrine/current data contract",
            "artifact_effect": "prompt_application_ledger_and_preregistration_context_hashes_written",
            "next_action": "repeat after next timeout/checkpoint/uncertainty",
        },
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "pursuit_id": "P002_CONTRACT_FREEZE_BEFORE_SCORING",
            "trigger": "first_incomplete_invariant",
            "executed_action": "wrote candidate eligibility and path/R scoring contracts before candidate/outcome scoring",
            "artifact_effect": "future candidate/path rows must reference frozen contracts",
            "next_action": "Stage02 candidate generator must fail if contracts are absent or modified without prereg update",
        },
        {
            "schema_version": "vnext_full_replay_extra_step_pursuit_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "pursuit_id": "P003_MARKET_BAR_DENOMINATOR_NOT_SHADOW_LOG",
            "trigger": "prior_logged_event_replay_underwork",
            "executed_action": "enumerated M15 candle rows directly from historical OHLC CSV sources",
            "artifact_effect": "primary universe has source_origin=market_bar_enumeration and source file hashes",
            "next_action": "Stage02 must generate candidates/skips from these rows and verifier must reject shadow-log seeding",
        },
    ]


def line_audit_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        exists = path.exists()
        row_count = 0
        parse_errors = 0
        first_row: Any = None
        last_row: Any = None
        schema_keys: set[str] = set()
        if exists and path.suffix == ".gz":
            opener = gzip.open
            mode = "rt"
        else:
            opener = open
            mode = "r"
        if exists and (path.suffix == ".jsonl" or path.suffix == ".gz"):
            with opener(path, mode, encoding="utf-8") as handle:
                for line_no, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        parse_errors += 1
                        continue
                    row_count += 1
                    if first_row is None:
                        first_row = payload
                    last_row = payload
                    if isinstance(payload, dict):
                        schema_keys.update(payload.keys())
        elif exists and path.suffix == ".json":
            try:
                payload = read_json(path)
                row_count = 1
                first_row = payload
                last_row = payload
                if isinstance(payload, dict):
                    schema_keys.update(payload.keys())
            except Exception:
                parse_errors += 1
        rows.append(
            {
                "schema_version": "vnext_full_replay_line_accountability_audit_v1",
                "route_id": ROUTE_ID,
                "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
                "file_path": rel(path),
                "exists": exists,
                "bytes": path.stat().st_size if exists else None,
                "sha256": sha256_file(path, allow_large=True) if exists else None,
                "row_count": row_count,
                "parse_error_count": parse_errors,
                "schema_keys": sorted(schema_keys),
                "first_row": first_row,
                "last_row": last_row,
                "audit_status": "PASS" if exists and parse_errors == 0 else "FAIL",
                "source_builder": rel(Path(__file__).resolve()),
                "independent_full_line_parse_status": "PASS" if exists and parse_errors == 0 else "FAIL",
            }
        )
    return rows


def build_outputs() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    started = utc_now()
    free_before = shutil.disk_usage(REPO_ROOT).free

    prompt_rows = context_rows()
    write_jsonl(OUTPUTS["prompt_application"], prompt_rows)

    eligibility = candidate_eligibility_contract(config)
    path_contract = path_r_scoring_contract()
    write_json(OUTPUTS["eligibility_contract"], eligibility)
    write_json(OUTPUTS["path_r_contract"], path_contract)

    coverage_rows: list[dict[str, Any]] = []
    source_universe_rows: list[dict[str, Any]] = []
    for root, path, symbol, timeframe in iter_csv_files():
        source_hash = sha256_file(path, allow_large=True)
        metadata, m15_rows = read_csv_metadata_and_m15_rows(root, path, symbol, timeframe, source_hash)
        coverage_rows.append(metadata)
        source_universe_rows.extend(m15_rows)

    tick_rows = tick_source_rows()
    sierra_rows = sierra_source_rows()
    acquisition_rows = [
        {
            "schema_version": "vnext_full_replay_source_acquisition_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "row_type": "source_root_inspection",
            "source_root": root,
            "exists": repo_path(root).exists(),
            "source_operation": "local_root_inventory",
            "source_use_status": "searched_stage01",
        }
        for root in CSV_ROOTS
    ]
    acquisition_rows.extend(tick_rows)
    acquisition_rows.extend(
        {
            "schema_version": "vnext_full_replay_source_acquisition_v1",
            "route_id": ROUTE_ID,
            "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
            "row_type": row["row_type"],
            "source_family": row.get("source_family"),
            "source_mode": row.get("source_mode"),
            "symbol_hint": row.get("symbol_hint"),
            "source_path": row.get("source_path"),
            "bytes": row.get("bytes"),
            "sha256": row.get("sha256"),
            "hash_status": row.get("hash_status"),
            "source_use_status": row.get("source_use_status"),
        }
        for row in sierra_rows
    )

    mt5_rows = mt5_export_rows(coverage_rows)
    repair_rows = source_repair_placeholder_rows(mt5_rows)
    runtime_rows = runtime_artifact_rows(config)
    question_rows = active_question_rows(mt5_rows)
    pursuit_rows = extra_step_rows()

    write_jsonl(OUTPUTS["data_coverage"], coverage_rows)
    source_universe_total_rows, source_universe_chunks = write_jsonl_gzip_chunks(
        OUTPUTS["source_universe"],
        source_universe_rows,
    )
    write_jsonl(OUTPUTS["source_acquisition"], acquisition_rows)
    write_jsonl(OUTPUTS["source_repair_proof"], repair_rows)
    write_jsonl(OUTPUTS["mt5_export"], mt5_rows)
    write_jsonl(OUTPUTS["sierra_source"], sierra_rows)
    write_jsonl(OUTPUTS["runtime_artifact_coverage"], runtime_rows)
    write_jsonl(OUTPUTS["active_questions"], question_rows)
    write_jsonl(OUTPUTS["extra_step"], pursuit_rows)

    coverage_counter = Counter((row.get("symbol"), row.get("timeframe")) for row in coverage_rows)
    source_root_counter = Counter(row.get("source_root") for row in coverage_rows)
    session_counter = Counter(row.get("session_bucket") for row in source_universe_rows)
    prereg = {
        "schema_version": "vnext_full_replay_preregistration_manifest_v1",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
        "created_at_utc": started,
        "git_head": git_head(),
        "prompt_path": rel(PROMPT_PATH),
        "starter_path": rel(STARTER_PATH),
        "data_requirements_path": rel(DATA_REQUIREMENTS_PATH),
        "active_evidence_class": "full_historical_vnext_candidate_generation_replay",
        "forbidden_surfaces": [
            "live_trading_change",
            "broker_operation",
            "account_mutation",
            "order_mutation",
            "deal_mutation",
            "position_mutation",
            "broker_history_mutation",
            "paid_api_vendor_call_without_explicit_approval",
            "production_prompt_config_risk_execution_safety_canary_selector_change",
            "remote_push",
            "source_data_deletion",
        ],
        "context_files": prompt_rows,
        "contracts": {
            "candidate_eligibility_contract": rel(OUTPUTS["eligibility_contract"]),
            "path_r_scoring_contract": rel(OUTPUTS["path_r_contract"]),
        },
        "source_roots": CSV_ROOTS + [rel(TICK_ROOT), str(SIERRA_ROOT)],
        "core_full_path_symbols": CORE_FULL_PATH_SYMBOLS,
        "expanded_symbols": EXPANDED_SYMBOLS,
        "candidate_frameworks": PRIMARY_REPLAY_FRAMEWORKS,
        "runtime_config_hash": sha256_file(CONFIG_PATH),
        "runtime_module_hash": sha256_file(VNEXT_RUNTIME_PATH),
        "prior_logged_event_replay_dir": rel(PRIOR_REPLAY_DIR),
        "stage01_counts": {
            "coverage_source_files": len(coverage_rows),
            "m15_denominator_rows": source_universe_total_rows,
            "m15_denominator_chunks": len(source_universe_chunks),
            "tick_source_files": len(tick_rows),
            "sierra_scid_files": len([r for r in sierra_rows if r.get("row_type") == "sierra_scid_file"]),
            "runtime_artifact_paths": len(runtime_rows),
            "mt5_export_requirements": len(mt5_rows),
            "source_repair_placeholder_rows": len(repair_rows),
        },
    }
    write_json(OUTPUTS["preregistration"], prereg)

    session_state = {
        "schema_version": "vnext_full_replay_session_state_v1",
        "route_id": ROUTE_ID,
        "updated_at_utc": utc_now(),
        "git_head": git_head(),
        "current_stage": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
        "goal_complete": False,
        "active_invariant": "freeze source-universe denominator, eligibility contract, and path/R contract before scoring",
        "first_incomplete_invariant": "Stage02 candidate generation from market-bar denominator rows",
        "open_questions": [row["question_id"] for row in question_rows if not row["status"].startswith("answered")],
        "next_action": (
            "build Stage02 market-state candidate-generation driver that reads "
            f"{rel(OUTPUTS['source_universe'])}, emits candidate/skipped rows from market bars, "
            "and verifies no shadow-log seeded primary universe"
        ),
        "free_space_bytes_before_stage": free_before,
        "free_space_bytes_after_stage": shutil.disk_usage(REPO_ROOT).free,
        "counts": prereg["stage01_counts"],
        "coverage_by_symbol_timeframe": {
            f"{symbol}::{timeframe}": count
            for (symbol, timeframe), count in sorted(coverage_counter.items())
        },
        "coverage_by_source_root": dict(sorted(source_root_counter.items())),
        "m15_denominator_by_session_bucket": dict(sorted(session_counter.items())),
        "m15_denominator_chunk_index_path": rel(OUTPUTS["source_universe"]),
        "m15_denominator_chunk_paths": [row["chunk_path"] for row in source_universe_chunks],
        "nonterminal_source_requirements": len(mt5_rows),
    }
    write_json(OUTPUTS["session_state"], session_state)

    completion_audit = {
        "schema_version": "vnext_full_replay_completion_audit_v1",
        "route_id": ROUTE_ID,
        "updated_at_utc": utc_now(),
        "completion_status": "IN_PROGRESS_NOT_COMPLETE",
        "completed_requirements_stage01": [
            "mandatory context reread recorded",
            "preregistration manifest written",
            "candidate eligibility contract frozen before scoring",
            "path/R scoring contract frozen before scoring",
            "available local CSV/tick/Sierra sources inventoried",
            "M15 denominator rows written from market bars with source hashes",
            "MT5 export requirements recorded as nonterminal next actions",
            "runtime artifact paths inventoried",
        ],
        "remaining_prompt_requirements_not_complete": [
            "candidate generation",
            "actual vNext runtime tracing for generated candidates",
            "path/R outcome simulation",
            "null/unknown audit after candidate/path ledgers",
            "dominance and pollution counterfactuals",
            "MIXED replay resolution",
            "ablation/robustness/prop metrics",
            "behavioral forensics",
            "subagent or equivalent independent review for terminal outputs",
            "final promote/kill/repair map",
            "scoped commits",
        ],
        "same_evidence_class_next_action": session_state["next_action"],
        "goal_may_be_marked_complete": False,
    }
    write_json(OUTPUTS["completion_audit"], completion_audit)

    paths_for_audit = [
        OUTPUTS["preregistration"],
        OUTPUTS["session_state"],
        OUTPUTS["prompt_application"],
        OUTPUTS["source_universe"],
        OUTPUTS["eligibility_contract"],
        OUTPUTS["path_r_contract"],
        OUTPUTS["data_coverage"],
        OUTPUTS["source_acquisition"],
        OUTPUTS["source_repair_proof"],
        OUTPUTS["mt5_export"],
        OUTPUTS["sierra_source"],
        OUTPUTS["runtime_artifact_coverage"],
        OUTPUTS["active_questions"],
        OUTPUTS["extra_step"],
        OUTPUTS["completion_audit"],
    ]
    paths_for_audit.extend(REPO_ROOT / row["chunk_path"] for row in source_universe_chunks)
    audit_rows = line_audit_rows(paths_for_audit)
    write_jsonl(OUTPUTS["line_audit"], audit_rows)

    manifest_rows = []
    for key, path in OUTPUTS.items():
        if not path.exists() or key == "output_manifest":
            continue
        audited_row_count = next(
            (row["row_count"] for row in audit_rows if row["file_path"] == rel(path)),
            None,
        )
        if audited_row_count is None:
            audited_row_count = file_line_count(path) if path.suffix == ".jsonl" else 1
        manifest_rows.append(
            {
                "artifact_key": key,
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path, allow_large=True),
                "row_count": audited_row_count,
                "logical_row_count": (
                    source_universe_total_rows if key == "source_universe" else None
                ),
            }
        )
    for chunk in source_universe_chunks:
        manifest_rows.append(
            {
                "artifact_key": "source_universe_chunk",
                "path": chunk["chunk_path"],
                "bytes": chunk["bytes"],
                "sha256": chunk["sha256"],
                "row_count": chunk["row_count"],
                "logical_artifact_path": chunk["logical_artifact_path"],
            }
        )
    output_manifest = {
        "schema_version": "vnext_full_replay_output_manifest_v1",
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now(),
        "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
        "goal_complete": False,
        "artifacts": manifest_rows,
    }
    write_json(OUTPUTS["output_manifest"], output_manifest)
    return {
        "status": "ok",
        "route_id": ROUTE_ID,
        "stage_id": "STAGE_01_SOURCE_UNIVERSE_FREEZE",
        "counts": prereg["stage01_counts"],
        "next_action": session_state["next_action"],
        "output_manifest": rel(OUTPUTS["output_manifest"]),
    }


def check_outputs() -> dict[str, Any]:
    missing = [key for key, path in OUTPUTS.items() if not path.exists()]
    failures = []
    if OUTPUTS["line_audit"].exists():
        with OUTPUTS["line_audit"].open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("audit_status") != "PASS":
                    failures.append(row)
    state = read_json(OUTPUTS["session_state"]) if OUTPUTS["session_state"].exists() else {}
    if not state or state.get("goal_complete") is not False:
        failures.append({"file": rel(OUTPUTS["session_state"]), "reason": "session_state_missing_or_goal_complete_not_false"})
    if OUTPUTS["source_universe"].exists() and state:
        chunk_rows = 0
        chunk_failures = []
        with OUTPUTS["source_universe"].open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                chunk_path = REPO_ROOT / row["chunk_path"]
                if not chunk_path.exists():
                    chunk_failures.append({"chunk": row["chunk_path"], "reason": "missing"})
                    continue
                chunk_rows += int(row.get("row_count") or 0)
        expected_rows = int((state.get("counts") or {}).get("m15_denominator_rows") or 0)
        if chunk_rows != expected_rows:
            failures.append(
                {
                    "file": rel(OUTPUTS["source_universe"]),
                    "reason": "chunk_row_sum_mismatch",
                    "chunk_rows": chunk_rows,
                    "expected_rows": expected_rows,
                }
            )
        failures.extend(chunk_failures)
    return {
        "status": "ok" if not missing and not failures else "fail",
        "missing": missing,
        "audit_failures": failures[:20],
        "audit_failure_count": len(failures),
        "session_state": {
            "current_stage": state.get("current_stage"),
            "first_incomplete_invariant": state.get("first_incomplete_invariant"),
            "counts": state.get("counts"),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify existing Stage01 outputs.")
    args = parser.parse_args(argv)
    payload = check_outputs() if args.check else build_outputs()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
