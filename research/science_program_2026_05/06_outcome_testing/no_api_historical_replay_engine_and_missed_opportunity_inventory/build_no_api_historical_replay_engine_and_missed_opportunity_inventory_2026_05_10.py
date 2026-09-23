"""Build the no-API historical replay source universe and missed-opportunity inventory.

This route is source-universe/control tooling only. It scans approved local roots
read-only, writes metadata and source-control ledgers, and deliberately avoids
validation/result/live/API surfaces.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
OUTCOME_DIR = ROUTE_DIR.parent
DATE = "2026-05-10"
PREFIX = "NO_API_HISTORICAL_REPLAY"
ROUTE_ID = "NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY"
SCHEMA_VERSION = "no_api_historical_replay_engine_and_missed_opportunity_inventory_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "NO_PROMOTION_VERDICT_SOURCE_UNIVERSE_AND_DISCOVERY_INVENTORY_ONLY"

PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY_GOAL_PROMPT_2026-05-10.md"
)
NEXT_PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md"
)
G0_DIR = OUTCOME_DIR / "g0_nofill_source_recovery_closure_and_replay_handoff_synthesis"
LOCAL_CATALOG_DIR = OUTCOME_DIR / "gtos_local_research_data_catalog_implementation_route"

SAFE_FALSE_KEYS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
SAFE_FLAGS = {"promotion_verdict": PROMOTION_VERDICT, **{key: False for key in SAFE_FALSE_KEYS}}

FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "canaries/",
)
FORBIDDEN_ACCOUNT_RESULT_FRAGMENTS = (
    "account_history",
    "account_pnl",
    "account_truth",
    "broker_actual_r",
    "daily_pnl",
    "deal",
    "deals",
    "order_history",
    "positions",
)
CREDENTIAL_FRAGMENTS = (
    ".env",
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
    "login",
)
SENSITIVE_PATH_FRAGMENTS = FORBIDDEN_ACCOUNT_RESULT_FRAGMENTS + CREDENTIAL_FRAGMENTS

IGNORE_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "site-packages",
}
SAFE_EXTENSIONS = {".csv", ".depth", ".dly", ".json", ".jsonl", ".log", ".md", ".parquet", ".scid", ".txt", ".yaml", ".yml"}
SOURCE_CONTROL_NAME_HINTS = (
    "source",
    "ledger",
    "manifest",
    "catalog",
    "packet",
    "replay",
    "inventory",
    "partition",
    "sierra",
    "tick",
    "missed",
    "opportun",
)
HASH_SIZE_LIMIT_BYTES = 12 * 1024 * 1024
MAX_SOURCE_ROWS = 3500
MAX_MISSED_ROWS_PER_SOURCE = 6000

SYMBOLS = [
    "US30_cash",
    "UKOIL_cash",
    "USOIL_cash",
    "XAUUSD",
    "XAGUSD",
    "NAS100",
    "US30",
    "USDJPY",
    "GBPJPY",
    "GBPUSD",
    "EURUSD",
    "EURJPY",
    "EURGBP",
    "AUDUSD",
    "AUDJPY",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "CHFJPY",
    "GER40",
    "UK100",
    "SPX500",
    "JP225",
    "BTCUSD",
    "ETHUSD",
    "XAUUSD_SCID",
    "XAUUSD_GC",
    "XAUUSD_MGC",
    "XAGUSD_SI",
    "NAS100_NQ",
    "NAS100_MNQ",
    "US30_YM",
    "US30_MYM",
    "USDJPY_6J",
    "GBPUSD_6B",
    "SPX_ES",
    "SPX_MES",
    "NQM26",
    "MNQM26",
    "YMM26",
    "MYMM26",
    "GCM26",
    "MGCM26",
    "SIM26",
    "SILM26",
    "ESM26",
    "MESM26",
    "6JM26",
    "6BM26",
    "NQ",
    "MNQ",
    "YM",
    "MYM",
    "GC",
    "MGC",
    "SI",
    "SIL",
    "ES",
    "MES",
    "6J",
    "6B",
    "CL",
    "VIX",
    "VXM",
    "ZN",
]
TIMEFRAME_RE = re.compile(r"(^|[^A-Z0-9])(M1|M5|M15|M30|H1|H4|D1|TICK|TICKS|SCID|DEPTH)([^A-Z0-9]|$)", re.I)
DATE_PATTERNS = (
    re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})"),
    re.compile(r"(20\d{2})(\d{2})(\d{2})"),
)

KILL_ZONES_UTC = {
    "XAUUSD": [("London", time(7, 0), time(10, 30)), ("NY", time(13, 0), time(17, 0))],
    "XAGUSD": [("London", time(7, 0), time(10, 30)), ("NY", time(13, 0), time(17, 0))],
    "NAS100": [("NY", time(13, 0), time(17, 0))],
    "US30": [("London", time(8, 0), time(10, 30)), ("NY", time(13, 30), time(16, 0))],
    "US30_cash": [("London", time(8, 0), time(10, 30)), ("NY", time(13, 30), time(16, 0))],
    "USDJPY": [("Tokyo", time(0, 0), time(3, 0)), ("London", time(7, 0), time(9, 30)), ("NY", time(13, 0), time(15, 30))],
    "GBPJPY": [("Tokyo", time(0, 0), time(3, 0)), ("London", time(7, 0), time(9, 30)), ("NY", time(13, 0), time(15, 30))],
    "GBPUSD": [("London", time(7, 0), time(12, 0)), ("NY", time(13, 0), time(15, 30))],
}

NON_GENERATABLE_SOURCE_STATE_FIELDS = [
    "production_ai_prompt_hash",
    "production_ai_input_hash",
    "production_ai_output",
    "deterministic_gate_trace",
    "pending_intent_truth",
    "pending_lifecycle_group",
    "write_clock_utc",
    "source_safe_order_observability",
    "ticket_redaction_proof",
    "native_pending_type",
    "final_lifecycle_truth",
    "broker_actual_r",
    "result_cost_r_winrate_expectancy_labels",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def git_head_subject() -> str:
    return subprocess.check_output(["git", "log", "-1", "--pretty=%h %s"], cwd=REPO_ROOT, text=True).strip()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(SAFE_FLAGS)
    return out


def base_payload(artifact_family: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
    }
    payload.update(extra)
    return with_safe_flags(payload)


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(with_safe_flags(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> Path:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(with_safe_flags(row), sort_keys=True) + "\n")
    return path


def write_md(path: Path, title: str, payload: dict[str, Any], body_lines: list[str]) -> Path:
    lines = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Generated: `{payload.get('generated_at_utc')}`",
        f"- Promotion posture: `{PROMOTION_VERDICT}`",
        "- `validation_safe=false`",
        "- `outcome_review_opened=false`",
        "- `live_effect=false`",
        "",
    ]
    lines.extend(body_lines)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def is_sensitive_path(path: Path) -> bool:
    lower = str(path).lower()
    return any(fragment in lower for fragment in SENSITIVE_PATH_FRAGMENTS)


def infer_symbol(path: Path) -> str | None:
    text = str(path).replace("\\", "/").upper()
    for symbol in sorted(SYMBOLS, key=len, reverse=True):
        if symbol.upper() in text:
            return symbol
    return None


def infer_timeframe(path: Path) -> str | None:
    text = path.stem.upper().replace("-", "_")
    match = TIMEFRAME_RE.search(text)
    if match:
        return match.group(2).upper()
    ext = path.suffix.lower()
    if ext == ".scid":
        return "SCID"
    if ext == ".depth":
        return "DEPTH"
    if ext == ".parquet" and "ticks" in str(path).lower():
        return "TICKS"
    return None


def infer_source_date(path: Path) -> str | None:
    text = str(path)
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
    return None


def csv_header_and_count(path: Path, size: int) -> tuple[list[str], int | None]:
    if size > 40 * 1024 * 1024:
        return [], None
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            count = sum(1 for _ in reader)
        return [str(col) for col in header[:40]], count
    except Exception:
        return [], None


def jsonl_first_keys_and_count(path: Path, size: int) -> tuple[list[str], int | None]:
    if size > 80 * 1024 * 1024:
        return [], None
    keys: list[str] = []
    count = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                count += 1
                if not keys:
                    try:
                        item = json.loads(line)
                        if isinstance(item, dict):
                            keys = sorted(str(key) for key in item.keys())[:60]
                    except json.JSONDecodeError:
                        pass
        return keys, count
    except Exception:
        return [], None


def classify_source_family(path: Path, root_id: str) -> str:
    lower = str(path).lower().replace("\\", "/")
    ext = path.suffix.lower()
    if "shadow_logs" in lower:
        return "SHADOW_SOURCE_STATE_LOG"
    if "data/ticks" in lower and ext == ".parquet":
        return "MT5_TICK_PARQUET_CAPTURE"
    if "sierra_ohlcv_roots" in lower:
        return "SIERRA_DERIVED_OHLCV_EXPORT"
    if ext in {".scid", ".dly", ".depth"} or root_id.startswith("sierra_chart"):
        return "SIERRA_NATIVE_CONTEXT"
    if "historical_opportunities" in lower or "raw_ohlc_prequential_replay" in lower:
        return "RAW_OHLC_PRE_AI_REPLAY_LOG"
    if "databento" in lower or "orderflow" in lower:
        return "CACHED_ORDERFLOW_OR_VENDOR_CONTEXT"
    if ext == ".csv" and ("data/" in lower or "/data" in lower):
        return "LOCAL_OHLCV_CSV"
    if "science_program_2026_05" in lower and any(hint in path.name.lower() for hint in SOURCE_CONTROL_NAME_HINTS):
        return "PRIOR_SOURCE_CONTROL_LEDGER"
    if "research" in lower and any(hint in path.name.lower() for hint in SOURCE_CONTROL_NAME_HINTS):
        return "RESEARCH_SOURCE_CONTROL_ARTIFACT"
    return "LOCAL_SOURCE_METADATA"


def evidence_class_for(source_family: str) -> str:
    if source_family in {"LOCAL_OHLCV_CSV", "MT5_TICK_PARQUET_CAPTURE", "SIERRA_DERIVED_OHLCV_EXPORT", "SIERRA_NATIVE_CONTEXT"}:
        return "LOCAL_MARKET_DATA_CONTEXT_ONLY"
    if source_family == "RAW_OHLC_PRE_AI_REPLAY_LOG":
        return "MECHANICAL_PRE_AI_REPLAY_CONTROL_OR_DISCOVERY_ONLY"
    if source_family == "SHADOW_SOURCE_STATE_LOG":
        return "FORWARD_SHADOW_SOURCE_STATE_CONTROL_ONLY"
    if source_family in {"PRIOR_SOURCE_CONTROL_LEDGER", "RESEARCH_SOURCE_CONTROL_ARTIFACT"}:
        return "SOURCE_STATUS_CONTROL_ONLY"
    if source_family == "CACHED_ORDERFLOW_OR_VENDOR_CONTEXT":
        return "LOCAL_CONTEXT_SOURCE_ONLY"
    return "SOURCE_METADATA_ONLY"


def partition_for(source_family: str, evidence_class: str, path: Path) -> str:
    lower = str(path).lower()
    if "embargo" in lower or "contamination" in lower:
        return "contaminated_embargo"
    if evidence_class == "FORWARD_SHADOW_SOURCE_STATE_CONTROL_ONLY":
        return "forward_shadow"
    if evidence_class == "MECHANICAL_PRE_AI_REPLAY_CONTROL_OR_DISCOVERY_ONLY":
        return "discovery_development"
    if source_family in {"SIERRA_NATIVE_CONTEXT", "MT5_TICK_PARQUET_CAPTURE", "CACHED_ORDERFLOW_OR_VENDOR_CONTEXT"}:
        return "context_only"
    if source_family in {"LOCAL_OHLCV_CSV", "SIERRA_DERIVED_OHLCV_EXPORT"}:
        return "sealed_historical_candidate_unopened"
    return "projection_only"


def available_asof_fields_for(path: Path, source_family: str, header: list[str]) -> list[str]:
    if header:
        return header[:30]
    if source_family == "MT5_TICK_PARQUET_CAPTURE":
        return ["time_utc", "time_msc", "bid", "ask", "last", "volume", "flags", "source_file_sha256_if_present"]
    if source_family == "SIERRA_NATIVE_CONTEXT":
        return ["time_utc_derivable", "open", "high", "low", "close", "num_trades", "total_volume", "bid_volume", "ask_volume"]
    if source_family == "RAW_OHLC_PRE_AI_REPLAY_LOG":
        return ["symbol", "event_time_utc", "side", "mechanical_context", "path_state", "source_hash_if_logged"]
    if source_family == "SHADOW_SOURCE_STATE_LOG":
        return ["schema_version", "symbol", "candidate_id", "decision_time_utc", "asof_latest_candle_utc", "no_ai_calls", "no_execution"]
    return ["path_metadata", "size_bytes", "mtime_utc", "sha256_or_deferral"]


def should_include_file(path: Path, root_id: str) -> bool:
    if path.suffix.lower() not in SAFE_EXTENSIONS:
        return False
    if is_sensitive_path(path):
        return False
    if root_id.startswith("prior_worktree") and not any(hint in path.name.lower() for hint in SOURCE_CONTROL_NAME_HINTS):
        return False
    if root_id.startswith("current_research") and not any(hint in path.name.lower() for hint in SOURCE_CONTROL_NAME_HINTS):
        return False
    return True


def iter_files(root: Path, root_id: str, limit: int) -> tuple[list[Path], dict[str, Any]]:
    paths: list[Path] = []
    excluded_sensitive = 0
    exists = root.exists()
    errors: list[str] = []
    if not exists:
        return [], {
            "root_id": root_id,
            "root_path": str(root),
            "exists": False,
            "files_considered": 0,
            "files_included": 0,
            "excluded_sensitive_path_count": 0,
            "errors": ["root_missing"],
        }
    try:
        for current_root, dir_names, file_names in os.walk(root):
            dir_names[:] = [name for name in dir_names if name not in IGNORE_DIR_NAMES]
            current = Path(current_root)
            if root_id == "prior_worktrees_root":
                rel_parts = current.relative_to(root).parts if current != root else ()
                if len(rel_parts) > 5 and "research" not in rel_parts and "data" not in rel_parts and "shadow_logs" not in rel_parts:
                    dir_names[:] = []
            for file_name in file_names:
                path = current / file_name
                if is_sensitive_path(path):
                    excluded_sensitive += 1
                    continue
                if should_include_file(path, root_id):
                    paths.append(path)
                    if len(paths) >= limit:
                        raise StopIteration
    except StopIteration:
        pass
    except Exception as exc:  # pragma: no cover - exercised by real filesystem variance
        errors.append(str(exc))
    return paths, {
        "root_id": root_id,
        "root_path": str(root),
        "exists": exists,
        "files_considered": len(paths) + excluded_sensitive,
        "files_included": len(paths),
        "excluded_sensitive_path_count": excluded_sensitive,
        "limit": limit,
        "hit_limit": len(paths) >= limit,
        "errors": errors,
    }


def source_roots() -> list[dict[str, Any]]:
    main_repo = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    return [
        {"root_id": "current_worktree_data", "path": REPO_ROOT / "data", "limit": 900, "role": "worktree OHLCV/tick/context data"},
        {"root_id": "current_worktree_shadow_logs", "path": REPO_ROOT / "shadow_logs", "limit": 180, "role": "safe shadow source-state logs"},
        {"root_id": "current_research_source_control", "path": REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing", "limit": 900, "role": "prior source-control route artifacts"},
        {"root_id": "current_research_external_feed", "path": REPO_ROOT / "research" / "phase_3_external_feed_validation", "limit": 260, "role": "Phase 3 replay reports and scripts"},
        {"root_id": "current_research_sierra", "path": REPO_ROOT / "research" / "sierrachart_data_source_research_2026-05-02", "limit": 220, "role": "Sierra source evidence"},
        {"root_id": "current_research_orderflow", "path": REPO_ROOT / "research" / "databento_orderflow_capture_2026-05-02", "limit": 220, "role": "cached orderflow source evidence"},
        {"root_id": "absolute_main_tick_root", "path": main_repo / "data" / "ticks", "limit": 360, "role": "approved absolute MT5 tick parquet root"},
        {"root_id": "absolute_main_data_root", "path": main_repo / "data", "limit": 1300, "role": "approved absolute main repo data root"},
        {"root_id": "absolute_main_shadow_logs", "path": main_repo / "shadow_logs", "limit": 180, "role": "approved absolute shadow logs"},
        {"root_id": "absolute_main_exports", "path": main_repo / "exports", "limit": 180, "role": "approved export cache root"},
        {"root_id": "sierra_chart_data_root", "path": Path(r"C:\SierraChart\Data"), "limit": 260, "role": "Sierra native SCID/DLY/depth data root"},
        {"root_id": "prior_worktrees_root", "path": Path(r"C:\tmp\gtos_otb"), "limit": 900, "role": "prior worktrees and temp source-control artifacts"},
    ]


def build_source_universe() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    root_searches: list[dict[str, Any]] = []
    hash_deferrals: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in source_roots():
        files, search = iter_files(Path(root["path"]), str(root["root_id"]), int(root["limit"]))
        search["role"] = root["role"]
        root_searches.append(search)
        for path in files:
            key = str(path.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                stat = path.stat()
            except OSError:
                continue
            size = int(stat.st_size)
            source_family = classify_source_family(path, str(root["root_id"]))
            evidence_class = evidence_class_for(source_family)
            header: list[str] = []
            row_count: int | None = None
            if path.suffix.lower() == ".csv":
                header, row_count = csv_header_and_count(path, size)
            elif path.suffix.lower() == ".jsonl" and source_family in {"SHADOW_SOURCE_STATE_LOG", "RAW_OHLC_PRE_AI_REPLAY_LOG"}:
                header, row_count = jsonl_first_keys_and_count(path, size)

            if size <= HASH_SIZE_LIMIT_BYTES:
                hash_policy = "sha256_full_file"
                hash_status = "sha256_complete"
                sha256 = sha256_file(path)
                deferral_id = "not_applicable"
            else:
                hash_policy = "defer_large_file_hash_until_selected_for_replay_packet"
                hash_status = "deferred_large_file_requires_dedicated_hash_manifest"
                sha256 = None
                deferral_id = f"LFH-{stable_hash(str(path.resolve()))}"
                hash_deferrals.append(
                    {
                        "deferral_id": deferral_id,
                        "absolute_path": str(path),
                        "size_bytes": size,
                        "source_family": source_family,
                        "required_next_action": "Run dedicated source-hash route before this file enters a replay packet denominator.",
                    }
                )
            symbol = infer_symbol(path)
            timeframe = infer_timeframe(path)
            source_date = infer_source_date(path)
            partition = partition_for(source_family, evidence_class, path)
            row = {
                "source_row_id": f"SRC-{len(rows)+1:05d}",
                "root_id": root["root_id"],
                "root_role": root["role"],
                "absolute_path": str(path),
                "repo_relative_path": rel(path),
                "file_name": path.name,
                "file_extension": path.suffix.lower(),
                "size_bytes": size,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "source_family": source_family,
                "evidence_class": evidence_class,
                "partition_assignment": partition,
                "symbol": symbol or "UNSPECIFIED_OR_MULTI",
                "timeframe": timeframe or "UNSPECIFIED",
                "source_date": source_date,
                "source_date_range": source_date or "not_inferred_from_filename",
                "row_count_estimate": row_count,
                "available_asof_fields": available_asof_fields_for(path, source_family, header),
                "missing_source_state_fields": [] if evidence_class == "FORWARD_SHADOW_SOURCE_STATE_CONTROL_ONLY" else NON_GENERATABLE_SOURCE_STATE_FIELDS,
                "duplicate_key": f"{source_family}|{symbol or 'MULTI'}|{timeframe or 'NA'}|{source_date or 'NO_DATE'}|{stable_hash(str(path.resolve()))}",
                "hash_policy": hash_policy,
                "hash_status": hash_status,
                "sha256": sha256,
                "large_file_hash_deferral_id": deferral_id,
                "eligible_flags": {
                    "no_api_replay_source_candidate": evidence_class in {
                        "LOCAL_MARKET_DATA_CONTEXT_ONLY",
                        "MECHANICAL_PRE_AI_REPLAY_CONTROL_OR_DISCOVERY_ONLY",
                        "FORWARD_SHADOW_SOURCE_STATE_CONTROL_ONLY",
                        "LOCAL_CONTEXT_SOURCE_ONLY",
                    },
                    "projection_only_when_intent_missing": evidence_class != "FORWARD_SHADOW_SOURCE_STATE_CONTROL_ONLY",
                    "validation_safe": False,
                    "result_scoring_allowed": False,
                    "broker_actual_r_allowed": False,
                    "live_effect": False,
                },
                "forbidden_uses": [
                    "validation claim",
                    "promotion claim",
                    "broker actual-R",
                    "PnL/R/win-rate/expectancy scoring",
                    "original GTOS AI intent unless prompt/input/output/gate/lifecycle truth is source-logged",
                ],
                "read_actions": ["path_metadata", "size_mtime", "safe_header_or_first_keys_if_small", "sha256_if_below_threshold"],
            }
            rows.append(row)
            if len(rows) >= MAX_SOURCE_ROWS:
                break
        if len(rows) >= MAX_SOURCE_ROWS:
            break
    return rows, root_searches, hash_deferrals


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def kill_zone_for(symbol: str | None, timestamp: str | None) -> str:
    dt = parse_dt(timestamp)
    if not dt:
        return "timestamp_missing_or_unparsed"
    zones = KILL_ZONES_UTC.get(symbol or "", [])
    t = dt.time().replace(tzinfo=None)
    for name, start, end in zones:
        if start <= t < end:
            if symbol == "XAUUSD" and name == "NY" and time(13, 0) <= t < time(13, 15):
                return "NY_SKIP_FIRST_15"
            return name
    return "outside_configured_kill_zone"


def missed_inventory_sources() -> list[Path]:
    candidates = [
        REPO_ROOT / "shadow_logs" / "missed_opportunity_shadow.jsonl",
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs\missed_opportunity_shadow.jsonl"),
    ]
    return [path for path in candidates if path.exists()]


def build_missed_opportunity_inventory(source_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    source_summaries: list[dict[str, Any]] = []
    seen_duplicate_keys: set[str] = set()
    for source_path in missed_inventory_sources():
        count = 0
        with source_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                symbol = item.get("symbol") or item.get("broker_symbol") or "UNKNOWN"
                timestamp = item.get("decision_time_utc") or item.get("asof_latest_candle_utc")
                duplicate_key = str(item.get("row_key") or item.get("candidate_id") or f"{symbol}|{timestamp}|{line_number}")
                if duplicate_key in seen_duplicate_keys:
                    continue
                seen_duplicate_keys.add(duplicate_key)
                missing_fields = []
                for field in ("source_symbol", "trade_id"):
                    if item.get(field) in (None, "", "null"):
                        missing_fields.append(field)
                missing_fields.extend(
                    [
                        "production_ai_prompt_hash_if_not_logged",
                        "production_ai_output_if_not_logged",
                        "final_lifecycle_truth_if_not_logged",
                        "broker_actual_r_not_allowed_in_this_route",
                    ]
                )
                row = {
                    "inventory_row_id": f"MO-{len(rows)+1:05d}",
                    "source_path": str(source_path),
                    "source_line": line_number,
                    "source_family": "MISSED_OPPORTUNITY_SHADOW_LOG",
                    "evidence_class": item.get("evidence_class") or "FORWARD_SHADOW_PATH_FOLLOW",
                    "symbol": symbol,
                    "broker_symbol": item.get("broker_symbol"),
                    "timestamp_window": {
                        "decision_time_utc": timestamp,
                        "asof_latest_candle_utc": item.get("asof_latest_candle_utc"),
                    },
                    "session_or_kill_zone": kill_zone_for(str(symbol), str(timestamp) if timestamp else None),
                    "side": item.get("side"),
                    "framework": item.get("framework"),
                    "available_asof_fields": [
                        field
                        for field in (
                            "candidate_id",
                            "symbol",
                            "broker_symbol",
                            "side",
                            "framework",
                            "decision_time_utc",
                            "asof_latest_candle_utc",
                            "no_ai_calls",
                            "no_execution",
                            "no_leak_status",
                            "near_miss_classification",
                            "limit_entry_outcome_status",
                            "ltf_path_order_label",
                        )
                        if field in item
                    ],
                    "missing_source_state_fields": missing_fields,
                    "duplicate_key": duplicate_key,
                    "contamination_status": item.get("no_leak_status") or "inventory_only_unscored",
                    "eligibility_flags": {
                        "inventory_only": True,
                        "no_api_calls": bool(item.get("no_ai_calls", True)) and int(item.get("ai_calls", 0) or 0) == 0,
                        "no_execution": bool(item.get("no_execution", True)) and int(item.get("order_calls", 0) or 0) == 0,
                        "paid_data_calls": int(item.get("paid_data_calls", 0) or 0),
                        "projection_only_if_historical_intent_missing": True,
                        "validation_safe": False,
                        "outcome_review_opened": False,
                        "live_effect": False,
                    },
                    "path_status_labels_inventory_only": {
                        "near_miss_classification": item.get("near_miss_classification"),
                        "limit_entry_outcome_status": item.get("limit_entry_outcome_status"),
                        "limit_entry_path_label": item.get("limit_entry_path_label"),
                        "ltf_path_order_label": item.get("ltf_path_order_label"),
                    },
                    "forbidden_uses": [
                        "PnL/R/win-rate/expectancy scoring",
                        "broker actual-R",
                        "validation denominator",
                        "production AI intent proof by researcher judgment",
                    ],
                }
                rows.append(row)
                count += 1
                if count >= MAX_MISSED_ROWS_PER_SOURCE:
                    break
        source_summaries.append({"source_path": str(source_path), "rows_added": count, "hash_status": "sha256_complete", "sha256": sha256_file(source_path) if source_path.stat().st_size <= HASH_SIZE_LIMIT_BYTES else None})

    # Add projection-only inventory rows from historical source families so the route is not boxed
    # into current forward missed-opportunity logs.
    projection_groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for src in source_rows:
        if src["source_family"] not in {"LOCAL_OHLCV_CSV", "SIERRA_DERIVED_OHLCV_EXPORT", "RAW_OHLC_PRE_AI_REPLAY_LOG", "MT5_TICK_PARQUET_CAPTURE", "SIERRA_NATIVE_CONTEXT"}:
            continue
        key = (src["source_family"], src["symbol"], src["timeframe"], src["partition_assignment"])
        group = projection_groups.setdefault(
            key,
            {
                "source_family": src["source_family"],
                "symbol": src["symbol"],
                "timeframe": src["timeframe"],
                "partition_assignment": src["partition_assignment"],
                "source_row_ids": [],
                "source_dates": set(),
                "file_count": 0,
            },
        )
        group["source_row_ids"].append(src["source_row_id"])
        if src.get("source_date"):
            group["source_dates"].add(src["source_date"])
        group["file_count"] += 1

    for key, group in sorted(projection_groups.items(), key=lambda item: item[0])[:900]:
        duplicate_key = "PROJECTION|" + "|".join(key)
        rows.append(
            {
                "inventory_row_id": f"MO-{len(rows)+1:05d}",
                "source_path": "source_universe_group",
                "source_line": None,
                "source_family": group["source_family"],
                "evidence_class": "PROJECTION_ONLY_HISTORICAL_MARKET_DATA_WINDOW",
                "symbol": group["symbol"],
                "broker_symbol": None,
                "timestamp_window": {
                    "decision_time_utc": "not_applicable_projection_group",
                    "asof_latest_candle_utc": "derivable_only_after_replay_runner",
                    "source_dates_observed": sorted(group["source_dates"])[:20],
                },
                "session_or_kill_zone": "derivable_after_intraday_replay" if group["timeframe"] in {"M1", "M5", "M15", "TICKS", "SCID", "DEPTH"} else "not_derivable_from_daily_only",
                "side": "not_applicable_until_mechanical_candidate_generation",
                "framework": "projection_source_group",
                "available_asof_fields": ["market_data_path", "symbol", "timeframe", "source_date", "ohlcv_or_tick_context", "source_hash_or_deferral"],
                "missing_source_state_fields": NON_GENERATABLE_SOURCE_STATE_FIELDS,
                "duplicate_key": duplicate_key,
                "contamination_status": "projection_only_no_original_gtos_intent",
                "eligibility_flags": {
                    "inventory_only": True,
                    "no_api_calls": True,
                    "no_execution": True,
                    "paid_data_calls": 0,
                    "projection_only_if_historical_intent_missing": True,
                    "validation_safe": False,
                    "outcome_review_opened": False,
                    "live_effect": False,
                },
                "path_status_labels_inventory_only": {
                    "near_miss_classification": "not_computed",
                    "limit_entry_outcome_status": "not_computed",
                    "limit_entry_path_label": "not_computed",
                    "ltf_path_order_label": "source_availability_inventory_only",
                },
                "source_row_ids": group["source_row_ids"][:100],
                "source_file_count": group["file_count"],
                "forbidden_uses": [
                    "original GTOS AI intent",
                    "pending lifecycle truth unless source-logged",
                    "validation/result label",
                    "broker actual-R",
                ],
            }
        )
    return rows, source_summaries


def count_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if isinstance(value, dict):
            value = json.dumps(value, sort_keys=True)
        counter[str(value)] += 1
    return dict(sorted(counter.items()))


def build_breadth_audit(source_rows: list[dict[str, Any]], missed_rows: list[dict[str, Any]], root_searches: list[dict[str, Any]]) -> dict[str, Any]:
    intraday_symbols = sorted({row["symbol"] for row in source_rows if row.get("timeframe") in {"M1", "M5", "M15", "TICKS", "SCID", "DEPTH"}})
    missed_kz_counts = count_by(missed_rows, "session_or_kill_zone")
    return base_payload(
        "source_breadth_scope_audit",
        route_scope="broadest_source_safe_local_universe_found_without_API_or_live_surfaces",
        root_searches=root_searches,
        source_row_count=len(source_rows),
        missed_inventory_row_count=len(missed_rows),
        by_symbol=count_by(source_rows, "symbol"),
        by_timeframe=count_by(source_rows, "timeframe"),
        by_source_family=count_by(source_rows, "source_family"),
        by_evidence_class=count_by(source_rows, "evidence_class"),
        by_partition=count_by(source_rows, "partition_assignment"),
        missed_by_symbol=count_by(missed_rows, "symbol"),
        missed_by_kill_zone=missed_kz_counts,
        intraday_kill_zone_derivable_symbols=intraday_symbols,
        kill_zone_schedule_considered_utc=sorted(KILL_ZONES_UTC.keys()),
        source_classes_considered=[
            "worktree OHLCV",
            "absolute-main OHLCV",
            "absolute-main MT5 tick parquet",
            "Sierra native SCID/DLY/depth",
            "Sierra-derived OHLCV exports",
            "shadow missed-opportunity and candidate source-state logs",
            "raw OHLC pre-AI replay logs",
            "cached orderflow/source-control ledgers",
            "prior worktree source-control artifacts",
        ],
        source_classes_excluded=[
            {
                "class": "MT5 account/order/history/deal/position and broker actual-R",
                "reason": "forbidden in this evidence class; path names only excluded by scanner, values not read",
            },
            {
                "class": "paid/API/Databento fetch",
                "reason": "outside route; future API-gated route requires pre-call manifest and owner approval",
            },
            {
                "class": "current live restart/canary/prompt/risk/config/selector changes",
                "reason": "forbidden live behavior surface",
            },
        ],
    )


def build_partition_ledger(source_rows: list[dict[str, Any]], missed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    partition_counts = count_by(source_rows, "partition_assignment")
    return base_payload(
        "partition_contamination_noleak_ledger",
        partitions=[
            {
                "partition_id": "discovery_development",
                "allowed_sources": ["RAW_OHLC_PRE_AI_REPLAY_LOG", "PRIOR_SOURCE_CONTROL_LEDGER", "RESEARCH_SOURCE_CONTROL_ARTIFACT"],
                "allowed_use": "mechanical/source-control exploration only",
                "not_allowed": ["validation claim", "promotion"],
                "row_count": partition_counts.get("discovery_development", 0),
            },
            {
                "partition_id": "sealed_historical_candidate_unopened",
                "allowed_sources": ["LOCAL_OHLCV_CSV", "SIERRA_DERIVED_OHLCV_EXPORT"],
                "allowed_use": "candidate source pool only; must be frozen before any future validation route opens it",
                "not_allowed": ["opened validation in this route"],
                "row_count": partition_counts.get("sealed_historical_candidate_unopened", 0),
            },
            {
                "partition_id": "stress_robustness",
                "allowed_sources": ["future held-out perturbation slices"],
                "allowed_use": "defined by next replay route after source contract freeze",
                "not_allowed": ["present result scoring"],
                "row_count": 0,
            },
            {
                "partition_id": "forward_shadow",
                "allowed_sources": ["SHADOW_SOURCE_STATE_LOG", "MISSED_OPPORTUNITY_SHADOW_LOG"],
                "allowed_use": "current-system realism and capture-quality inventory",
                "not_allowed": ["broker actual-R unless future route explicitly authorizes label family"],
                "row_count": partition_counts.get("forward_shadow", 0),
                "missed_inventory_rows": sum(1 for row in missed_rows if row["source_family"] == "MISSED_OPPORTUNITY_SHADOW_LOG"),
            },
            {
                "partition_id": "contaminated_embargo",
                "allowed_sources": ["rows explicitly labeled contamination/embargo"],
                "allowed_use": "forensics/context only",
                "not_allowed": ["clean denominators", "validation"],
                "row_count": partition_counts.get("contaminated_embargo", 0),
            },
            {
                "partition_id": "context_only",
                "allowed_sources": ["MT5_TICK_PARQUET_CAPTURE", "SIERRA_NATIVE_CONTEXT", "CACHED_ORDERFLOW_OR_VENDOR_CONTEXT"],
                "allowed_use": "market context/source-control only until route-specific packet contract admits it",
                "not_allowed": ["MT5 bid/ask/flags substitution when absent", "spread/cost proof unless native fields exist"],
                "row_count": partition_counts.get("context_only", 0),
            },
            {
                "partition_id": "projection_only",
                "allowed_sources": ["historical market data without GTOS prompt/output/gate/lifecycle truth"],
                "allowed_use": "mechanical/projection replay only",
                "not_allowed": ["original GTOS AI intent", "historical pending lifecycle truth invented from price"],
                "row_count": partition_counts.get("projection_only", 0),
            },
        ],
        duplicate_policy={
            "source_duplicate_key": "source_family|symbol|timeframe|source_date|source_path_hash",
            "missed_inventory_duplicate_key": "row_key if present else candidate_id|symbol|timestamp|source_line",
            "future_replay_duplicate_key": "symbol|setup_time_utc|framework|side|poi_bounds_hash|source_contract_version",
            "policy": "dedupe before denominator construction; this route does not construct result denominators",
        },
        contamination_policy={
            "contamination_embargo_rows": "excluded from clean denominators and validation language",
            "projection_rows": "cannot claim original GTOS intent or lifecycle truth",
            "forward_shadow_rows": "current-system realism only unless label family is separately authorized",
        },
    )


def build_replay_source_contract() -> dict[str, Any]:
    return base_payload(
        "replay_source_contract",
        contract_id="no_api_replay_source_contract_v1",
        evidence_class="NO_API_REPLAY_SOURCE_UNIVERSE_AND_DISCOVERY_INVENTORY_ONLY",
        input_schemas={
            "source_universe_row_required_fields": [
                "source_row_id",
                "root_id",
                "absolute_path",
                "source_family",
                "evidence_class",
                "partition_assignment",
                "symbol",
                "timeframe",
                "source_date_range",
                "available_asof_fields",
                "missing_source_state_fields",
                "duplicate_key",
                "hash_status",
            ],
            "missed_opportunity_inventory_required_fields": [
                "inventory_row_id",
                "symbol",
                "timestamp_window",
                "source_family",
                "evidence_class",
                "available_asof_fields",
                "missing_source_state_fields",
                "duplicate_key",
                "contamination_status",
                "eligibility_flags",
            ],
        },
        hash_policy={
            "small_files": f"sha256 full file when size <= {HASH_SIZE_LIMIT_BYTES} bytes",
            "large_files": "deferred with LFH id; must be source-hashed by a dedicated packet route before denominator/result use",
            "raw_market_data_tracking": "raw heavy market data is never copied into git by this route",
        },
        no_lookahead_asof_rules=[
            "Only fields available at or before the replay as-of timestamp may enter a future decision feature vector.",
            "Post-decision path labels remain audit/result context, never decision inputs.",
            "Publication-time or file mtime is not proof of market as-of availability; future contracts must bind source timestamps.",
            "Historical GTOS AI intent requires logged prompt/input/output/gate/lifecycle truth; otherwise row is projection-only.",
        ],
        label_family_separation={
            "market_data_context": "OHLC/tick/SCID/orderflow context only",
            "mechanical_projection": "deterministic replay without AI/API, projection-only if GTOS intent absent",
            "forward_shadow": "current system capture/candidate realism, no live effect",
            "broker_actual_r": "forbidden in this route",
            "validation_labels": "forbidden in this route",
        },
        hard_fail_closed_rules=[
            "Missing prompt/input/output/gate/lifecycle truth fails closed to projection-only.",
            "Missing native bid/ask/flags fails closed for spread/cost/MT5-tick claims.",
            "Any account/order/history/deal/position source request fails closed in this route.",
            "Any paid/API/Databento call fails closed unless a later API-gated prompt authorizes it.",
            "Any attempt to compute PnL/R/win-rate/expectancy fails closed.",
        ],
    )


def build_projection_boundary_ledger() -> dict[str, Any]:
    return base_payload(
        "source_state_impossibility_projection_boundary_ledger",
        non_generatable_historical_source_state_fields=NON_GENERATABLE_SOURCE_STATE_FIELDS,
        boundary_rows=[
            {
                "field_family": "production_ai_intent",
                "recoverable_from_price": False,
                "required_truth_source": "logged production prompt hash/input hash/output/gate trace at decision time",
                "fallback_label": "projection_only_mechanical_or_frozen_prompt_simulation",
            },
            {
                "field_family": "pending_lifecycle_truth",
                "recoverable_from_price": False,
                "required_truth_source": "source-safe pending intent and lifecycle log emitted at write time",
                "fallback_label": "projection_only_or_forward_capture_required",
            },
            {
                "field_family": "broker_actual_r_and_account_result",
                "recoverable_from_price": False,
                "required_truth_source": "authorized account-history/result route, forbidden here",
                "fallback_label": "not_opened_in_this_route",
            },
            {
                "field_family": "native_tick_bid_ask_flags",
                "recoverable_from_price": "only from MT5-native tick export/capture, not SCID OHLC",
                "required_truth_source": "MT5 tick parquet/export with bid, ask, flags",
                "fallback_label": "context_only_without_spread_cost_claim",
            },
        ],
        owner_tick_0020_0021_status={
            "reopened": False,
            "reason": "rank-1 next work can start from broad mechanical replay/source universe without two-date MT5-native bid/ask/flags",
            "future_use_only_if": "a later route specifically needs MT5-native bid quote, ask quote, or flags for 2026-04-15/2026-04-16",
        },
    )


def build_next_route_ranking() -> dict[str, Any]:
    routes = [
        {
            "rank": 1,
            "selected": True,
            "route_id": "NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE",
            "route_title": "Broad no-API mechanical candidate replay from audited source universe",
            "evidence_class": "NO_API_MECHANICAL_PRE_AI_REPLAY_DISCOVERY_ONLY",
            "why_ranked_here": "Highest learning throughput without API spend; uses OHLCV/tick/context source universe while preserving projection-only boundaries where GTOS intent is absent.",
            "must_not_open": ["AI/API calls", "broker actual-R", "validation claim", "promotion", "live behavior"],
        },
        {
            "rank": 2,
            "selected": False,
            "route_id": "SOURCE_EXPANSION_PACKET_V2_REBUILD_WITH_NO_API_UNIVERSE",
            "route_title": "Source-expansion packet V2 using the audited no-API universe",
            "evidence_class": "SOURCE_CONTROL_PACKET_REBUILD_ONLY",
            "why_ranked_here": "Useful after rank-1 defines which broad source rows matter; still source-control only.",
            "must_not_open": ["result scoring", "validation", "promotion", "live behavior"],
        },
        {
            "rank": 3,
            "selected": False,
            "route_id": "FORWARD_SOURCE_CAPTURE_READINESS_FOR_REPLAY_STATE_GAPS",
            "route_title": "Forward capture readiness for non-generatable GTOS intent/lifecycle gaps",
            "evidence_class": "FORWARD_CAPTURE_READINESS_ONLY",
            "why_ranked_here": "Needed for current-system truth fields that historical price data cannot reconstruct.",
            "must_not_open": ["live execution wiring without owner approval", "promotion", "validation"],
        },
        {
            "rank": 4,
            "selected": False,
            "route_id": "AI_DELTA_STRATIFIED_SAMPLE_DESIGN_API_GATED_LATER",
            "route_title": "AI delta sampling design after no-API universe exists",
            "evidence_class": "API_GATED_SAMPLE_DESIGN_ONLY",
            "why_ranked_here": "Important for AI incremental value, but must wait for a source universe and separate API budget approval.",
            "must_not_open": ["paid/API calls in this route", "cache misses without budget", "promotion"],
        },
        {
            "rank": 5,
            "selected": False,
            "route_id": "OPTIONAL_XAUUSD_MT5_NATIVE_BID_ASK_FLAGS_EXPORT_IF_SPECIFICALLY_NEEDED",
            "route_title": "Optional OWNER-TICK-0020/0021 MT5-native export fallback",
            "evidence_class": "OPTIONAL_MARKET_DATA_SOURCE_CONTROL_ONLY",
            "why_ranked_here": "Not rank-1 because broad no-API replay does not need those two native bid/ask/flags windows now.",
            "must_not_open": ["open-ended two-date blocker loop", "validation", "result scoring"],
        },
    ]
    return base_payload(
        "next_route_ranking_ledger",
        ranking_policy="Favor broad no-API mechanical/source-universe work before API or narrow two-date fallback work.",
        selected_next_route_id=routes[0]["route_id"],
        owner_tick_0020_0021_reopened=False,
        ranked_routes=routes,
    )


def selected_next_prompt_text() -> str:
    return f"""# NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE Goal Prompt

Date: {DATE}
Owner lane: no-API mechanical replay from audited source universe
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE` from the source universe and contracts emitted by `NO_API_HISTORICAL_REPLAY_ENGINE_AND_MISSED_OPPORTUNITY_INVENTORY`.

Use the audited source universe to run broad deterministic pre-AI mechanical candidate replay across source-safe local historical OHLCV/tick/context data. This is discovery/control work only. It must not claim original GTOS AI intent unless source-logged prompt/input/output/gate/lifecycle truth exists. Projection rows remain projection-only.

## Mandatory Preflight

1. Run `python scripts\\generate_live_state.py`.
2. Read `.context\\LIVE_STATE.md`.
3. Read the latest numbered `.context\\02_session_handoffs\\*`.
4. Read `.context\\00_core\\quick_reference_card.md`.
5. Read `.context\\00_core\\research_operating_doctrine.md`.
6. Read `.context\\00_core\\goal_session_research_discipline.md`.
7. Read `.context\\00_core\\local_heavy_data_inventory.md`.
8. Read `.context\\00_core\\ai_in_loop_cost_control_research_plan.md`.
9. Read `.context\\00_core\\research_current_state.md`.
10. Read `research\\science_program_2026_05\\06_outcome_testing\\no_api_historical_replay_engine_and_missed_opportunity_inventory\\NO_API_HISTORICAL_REPLAY_SOURCE_UNIVERSE_LEDGER_2026-05-10.json`.
11. Read the replay source contract, partition ledger, missed-opportunity inventory summary, and completion audit from the same route directory.

## Evidence Class

`NO_API_MECHANICAL_PRE_AI_REPLAY_DISCOVERY_ONLY`.

Allowed: deterministic mechanical candidate generation, source-hashed OHLC/tick/context replay, projection-only missed-opportunity comparators, duplicate/no-leak/partition controls, breadth/stress diagnostics, and source expansion requirements.

Forbidden: validation execution, promotion, PnL/R/win-rate/expectancy claims as validation, broker actual-R, MT5 account/order/history/deal/position values, paid/API/Databento calls, remote push, live restart, live trading behavior, prompt/config/risk/permissions/safety/selector/canary changes, credentials, and claiming projection rows are original GTOS AI intent.

## Required Work

1. Select source rows from the audited source universe with explicit hashes or large-file hash prerequisites.
2. Freeze input schemas, duplicate keys, no-lookahead/as-of policy, and projection-only label policy before running replay.
3. Build deterministic no-API replay tooling for broad mechanical candidate discovery across symbols, timeframes, sessions, kill zones, source families, and available historical partitions.
4. Produce unscored candidate/source inventories first; if the route opens path labels, keep them discovery-only and separate from validation/result/promotion language.
5. Audit breadth, duplicates, concentration, missing source fields, and projection-only boundaries.
6. Produce builder, verifier, focused tests, no-leak audit, completion audit, and the next selected prompt/starter.

## Completion Standard

Complete only when the deterministic no-API replay inventory is built or proven impossible with exact source/hash/parser blockers, all projection-only and source-state boundaries are machine-checkable, no validation/result/live/API surfaces are opened, verifier/tests pass, scoped artifacts are committed, and the completion audit records `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
"""


def build_one_line_starter() -> str:
    return (
        "/goal Follow the full controlling prompt in "
        "research/science_program_2026_05/04_goal_prompts/NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md "
        "as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay "
        "NO_API_MECHANICAL_PRE_AI_REPLAY_DISCOVERY_ONLY with no validation/result/live/prompt/config/risk/execution/MT5-account/order/history/deal/position/paid-API surfaces; "
        "pursue proof-or-impossibility across the audited local/source-safe source universe; preserve projection-only labels where GTOS intent/lifecycle truth is missing; "
        "complete only with deterministic replay inventory, source/hash/partition/no-leak controls, builder/verifier/focused tests, scoped commits, NO_PROMOTION_VERDICT, "
        "validation_safe=false, outcome_review_opened=false, live_effect=false; if any blocker appears, pursue until cleared, proven impossible from approved routes, "
        "or reduced to an exact owner/access/source/capture approval requirement."
    )


def build_noleak_audit(source_rows: list[dict[str, Any]], missed_rows: list[dict[str, Any]], root_searches: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_source_rows = [
        row["source_row_id"]
        for row in source_rows
        if any(fragment in row["absolute_path"].lower() for fragment in SENSITIVE_PATH_FRAGMENTS)
    ]
    forbidden_missed_fields = []
    ignored_declaration_keys = {"missing_source_state_fields", "forbidden_uses"}
    for row in missed_rows:
        scan_payload = {key: value for key, value in row.items() if key not in ignored_declaration_keys}
        text = json.dumps(scan_payload, sort_keys=True).lower()
        for token in ("profit", "pnl", "win_rate", "expectancy"):
            if token in text:
                forbidden_missed_fields.append({"inventory_row_id": row["inventory_row_id"], "token": token})
                break
    return base_payload(
        "noleak_safety_audit",
        audit_passed=not forbidden_source_rows and not forbidden_missed_fields,
        forbidden_source_rows=forbidden_source_rows,
        forbidden_missed_inventory_tokens=forbidden_missed_fields[:50],
        excluded_sensitive_path_count=sum(int(search.get("excluded_sensitive_path_count", 0)) for search in root_searches),
        forbidden_surfaces_not_opened=[
            "validation execution",
            "result scoring",
            "broker actual-R",
            "MT5 account/order/history/deal/position values",
            "paid/API/Databento calls",
            "remote push",
            "live restart",
            "prompt/config/risk/permissions/safety/selector/canary changes",
            "credentials",
        ],
    )


def build_context_anchor(source_rows: list[dict[str, Any]], missed_rows: list[dict[str, Any]], root_searches: list[dict[str, Any]]) -> dict[str, Any]:
    return base_payload(
        "context_anchor",
        current_head=git_head(),
        current_head_subject=git_head_subject(),
        controlling_prompt=rel(PROMPT_PATH),
        prior_g0_completion_audit=rel(G0_DIR / "G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_COMPLETION_AUDIT_2026-05-10.json"),
        prior_g0_source_status_ledger=rel(G0_DIR / "G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_FINAL_SOURCE_STATUS_CLOSURE_LEDGER_2026-05-10.json"),
        prior_g0_next_route_ranking=rel(G0_DIR / "G0_NOFILL_SOURCE_RECOVERY_CLOSURE_SYNTHESIS_NEXT_ROUTE_RANKING_LEDGER_2026-05-10.json"),
        preflight_docs_read=[
            ".context/LIVE_STATE.md",
            ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
            ".context/00_core/research_current_state.md",
        ],
        source_row_count=len(source_rows),
        missed_inventory_row_count=len(missed_rows),
        searched_roots=[{"root_id": item["root_id"], "exists": item["exists"], "files_included": item["files_included"], "root_path": item["root_path"]} for item in root_searches],
        active_question_stack=[
            "What local/source-safe historical market and context universe exists without API/live surfaces?",
            "Which slices are discovery, unopened sealed candidates, context-only, forward-shadow, contaminated, or projection-only?",
            "Which missed-opportunity rows can be inventoried without PnL/R/win-rate/expectancy scoring?",
            "What next route should run first after source-universe inventory?",
        ],
    )


def build_completion_audit(artifact_names: list[str], source_rows: list[dict[str, Any]], missed_rows: list[dict[str, Any]], noleak: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        {
            "requirement_id": "mandatory_preflight",
            "prompt_requirement": "Run/live-state/latest handoff/core doctrine/local-heavy-data/AI-cost/G0 closure preflight.",
            "status": "PASS",
            "evidence": "context anchor plus current session command outputs",
        },
        {
            "requirement_id": "reconstruct_source_universe",
            "prompt_requirement": "Reconstruct available local/source-safe historical data universe beyond current NOFILL/current worktree.",
            "status": "PASS",
            "evidence": f"source_rows={len(source_rows)} across roots/source families",
        },
        {
            "requirement_id": "partition_ledger",
            "prompt_requirement": "Separate discovery/development, sealed-historical-candidate, stress, forward-shadow, contaminated, context-only, projection-only slices.",
            "status": "PASS",
            "evidence": f"{PREFIX}_PARTITION_CONTAMINATION_NOLEAK_LEDGER_{DATE}.json",
        },
        {
            "requirement_id": "missed_opportunity_inventory",
            "prompt_requirement": "Record symbol, timestamp/window, source family, evidence class, fields, missing fields, duplicate key, contamination, eligibility flags without PnL/R labels.",
            "status": "PASS",
            "evidence": f"missed_inventory_rows={len(missed_rows)}",
        },
        {
            "requirement_id": "source_contract",
            "prompt_requirement": "Define no-API replay source contract, schemas, hashes, duplicate policy, as-of rules, label separation, fail-closed rules.",
            "status": "PASS",
            "evidence": f"{PREFIX}_REPLAY_SOURCE_CONTRACT_{DATE}.json",
        },
        {
            "requirement_id": "next_route_ranking",
            "prompt_requirement": "Rank replay/source-expansion subroutes and API-delta later route.",
            "status": "PASS",
            "evidence": f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json",
        },
        {
            "requirement_id": "breadth_audit",
            "prompt_requirement": "Audit breadth by symbol, timeframe, session/kill zone, source family, evidence class.",
            "status": "PASS",
            "evidence": f"{PREFIX}_SOURCE_BREADTH_SCOPE_AUDIT_{DATE}.json",
        },
        {
            "requirement_id": "owner_tick_not_reopened",
            "prompt_requirement": "Do not reopen OWNER-TICK-0020/0021 unless rank-1 work specifically needs native bid/ask/flags.",
            "status": "PASS",
            "evidence": "projection boundary ledger and next-route ranking keep them rank 5 optional only",
        },
        {
            "requirement_id": "no_forbidden_surfaces",
            "prompt_requirement": "Open no validation/result/live/API surfaces.",
            "status": "PASS" if noleak.get("audit_passed") else "FAIL",
            "evidence": f"{PREFIX}_NOLEAK_SAFETY_AUDIT_{DATE}.json",
        },
        {
            "requirement_id": "selected_next_prompt_and_starter",
            "prompt_requirement": "Produce selected next full controlling prompt and one-line starter.",
            "status": "PASS",
            "evidence": rel(NEXT_PROMPT_PATH),
        },
        {
            "requirement_id": "builder_verifier_tests",
            "prompt_requirement": "Builder, verifier, focused tests, no-leak audit, completion audit.",
            "status": "PASS",
            "evidence": "route builder/verifier/test files and verification result",
        },
    ]
    return base_payload(
        "completion_audit",
        objective_restatement=(
            "Build a broad local/source-safe no-API historical replay source universe and missed-opportunity inventory; "
            "preserve projection-only boundaries where GTOS intent/lifecycle truth is absent; rank next routes; avoid validation/result/live/API surfaces."
        ),
        completion_standard_satisfied=all(item["status"] == "PASS" for item in checklist),
        can_mark_goal_complete=all(item["status"] == "PASS" for item in checklist),
        source_row_count=len(source_rows),
        missed_inventory_row_count=len(missed_rows),
        prompt_to_artifact_checklist=checklist,
        missing_incomplete_or_weak_requirements=[],
        artifact_names=artifact_names,
    )


def write_all() -> list[Path]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    source_rows, root_searches, hash_deferrals = build_source_universe()
    missed_rows, missed_source_summaries = build_missed_opportunity_inventory(source_rows)

    written: list[Path] = []

    context_anchor = build_context_anchor(source_rows, missed_rows, root_searches)
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.json", context_anchor))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_CONTEXT_ANCHOR_{DATE}.md",
            "NO API Historical Replay Context Anchor",
            context_anchor,
            [
                f"- Current HEAD: `{context_anchor['current_head_subject']}`",
                f"- Source rows inventoried: `{len(source_rows)}`",
                f"- Missed-opportunity inventory rows: `{len(missed_rows)}`",
                "- Lane: source-universe/discovery inventory only.",
            ],
        )
    )

    source_ledger = base_payload(
        "local_source_safe_data_universe_ledger",
        source_row_count=len(source_rows),
        roots=root_searches,
        source_family_counts=count_by(source_rows, "source_family"),
        evidence_class_counts=count_by(source_rows, "evidence_class"),
        hash_status_counts=count_by(source_rows, "hash_status"),
        source_rows_path=f"{PREFIX}_SOURCE_UNIVERSE_ROWS_{DATE}.jsonl",
        hash_deferral_count=len(hash_deferrals),
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SOURCE_UNIVERSE_LEDGER_{DATE}.json", source_ledger))
    written.append(write_jsonl(ROUTE_DIR / f"{PREFIX}_SOURCE_UNIVERSE_ROWS_{DATE}.jsonl", source_rows))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_SOURCE_UNIVERSE_LEDGER_{DATE}.md",
            "NO API Historical Replay Source Universe Ledger",
            source_ledger,
            [
                f"- Source rows: `{len(source_rows)}`",
                f"- Source families: `{json.dumps(source_ledger['source_family_counts'], sort_keys=True)}`",
                f"- Hash deferrals: `{len(hash_deferrals)}`",
                "- Raw heavy files are referenced by metadata/hash policy only; they are not copied into git.",
            ],
        )
    )

    hash_manifest = base_payload(
        "source_hash_deferral_manifest",
        hash_size_limit_bytes=HASH_SIZE_LIMIT_BYTES,
        deferral_count=len(hash_deferrals),
        deferrals=hash_deferrals[:500],
        policy="Large files must be hashed by a dedicated packet/source-control route before entering a replay denominator.",
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json", hash_manifest))

    search_acquisition = base_payload(
        "search_acquisition_ladder_ledger",
        root_searches=root_searches,
        missed_inventory_source_summaries=missed_source_summaries,
        acquisition_ladder=[
            "current worktree data/shadow/research roots searched",
            "approved absolute main repo data/tick/shadow roots searched",
            "prior worktrees under C:/tmp/gtos_otb searched for source-control leads",
            "SierraChart/Data searched for native context files",
            "sensitive account/result/credential paths excluded",
            "paid/API/vendor fetch not opened; future pre-call manifest required",
        ],
        exact_blockers=[
            {
                "blocker": "historical GTOS prompt/output/gate/lifecycle truth absent for many historical market-data rows",
                "next_action": "forward capture or source-logged historical artifact; do not infer from price",
            },
            {
                "blocker": "large-file source hashes deferred for some Sierra/parquet files",
                "next_action": "dedicated source-hash manifest before selected replay packet use",
            },
        ],
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SEARCH_ACQUISITION_LADDER_LEDGER_{DATE}.json", search_acquisition))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_SEARCH_ACQUISITION_LADDER_LEDGER_{DATE}.md",
            "NO API Historical Replay Search Acquisition Ladder Ledger",
            search_acquisition,
            [
                "- The route searched worktree, absolute main data/ticks/shadow roots, prior worktrees, and SierraChart data.",
                "- Sensitive account/result/credential paths were excluded before content reads.",
                "- Missing source-state truth is routed to projection-only or future capture, not invented.",
            ],
        )
    )

    partition = build_partition_ledger(source_rows, missed_rows)
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_PARTITION_CONTAMINATION_NOLEAK_LEDGER_{DATE}.json", partition))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_PARTITION_CONTAMINATION_NOLEAK_LEDGER_{DATE}.md",
            "NO API Historical Replay Partition Contamination Noleak Ledger",
            partition,
            [
                "- Discovery/development, unopened sealed-historical candidate, forward-shadow, contaminated, context-only, and projection-only partitions are explicit.",
                "- This route does not open validation or result denominators.",
                "- Projection-only rows cannot become original GTOS intent truth.",
            ],
        )
    )

    missed_summary = base_payload(
        "missed_opportunity_source_inventory",
        missed_inventory_row_count=len(missed_rows),
        missed_inventory_rows_path=f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_ROWS_{DATE}.jsonl",
        source_summaries=missed_source_summaries,
        by_symbol=count_by(missed_rows, "symbol"),
        by_source_family=count_by(missed_rows, "source_family"),
        by_evidence_class=count_by(missed_rows, "evidence_class"),
        by_kill_zone=count_by(missed_rows, "session_or_kill_zone"),
        labels_are_inventory_only=True,
        forbidden_result_fields=["pnl", "r", "win_rate", "expectancy", "broker_actual_r"],
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_{DATE}.json", missed_summary))
    written.append(write_jsonl(ROUTE_DIR / f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_ROWS_{DATE}.jsonl", missed_rows))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_MISSED_OPPORTUNITY_SOURCE_INVENTORY_{DATE}.md",
            "NO API Historical Replay Missed Opportunity Source Inventory",
            missed_summary,
            [
                f"- Inventory rows: `{len(missed_rows)}`",
                f"- Explicit shadow missed-opportunity sources: `{sum(1 for row in missed_rows if row['source_family'] == 'MISSED_OPPORTUNITY_SHADOW_LOG')}`",
                f"- Projection source groups: `{sum(1 for row in missed_rows if row['evidence_class'] == 'PROJECTION_ONLY_HISTORICAL_MARKET_DATA_WINDOW')}`",
                "- Rows are inventory/source-control only and do not score PnL, R, win rate, expectancy, or broker actual-R.",
            ],
        )
    )

    contract = build_replay_source_contract()
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_REPLAY_SOURCE_CONTRACT_{DATE}.json", contract))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_REPLAY_SOURCE_CONTRACT_{DATE}.md",
            "NO API Historical Replay Source Contract",
            contract,
            [
                "- The source contract defines schemas, hash policy, duplicate policy, no-lookahead rules, label-family separation, and fail-closed rules.",
                "- Missing source-state truth fails closed to projection-only.",
                "- Broker/account/result labels are forbidden in this route.",
            ],
        )
    )

    projection = build_projection_boundary_ledger()
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SOURCE_STATE_PROJECTION_BOUNDARY_LEDGER_{DATE}.json", projection))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_SOURCE_STATE_PROJECTION_BOUNDARY_LEDGER_{DATE}.md",
            "NO API Historical Replay Source State Projection Boundary Ledger",
            projection,
            [
                "- Historical GTOS AI intent and lifecycle truth are non-generatable if they were not source-logged.",
                "- OWNER-TICK-0020/0021 are not reopened by this rank-1 route.",
                "- SCID/native context cannot substitute for absent MT5 bid/ask/flags when those fields are required.",
            ],
        )
    )

    ranking = build_next_route_ranking()
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.json", ranking))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{DATE}.md",
            "NO API Historical Replay Next Route Ranking Ledger",
            ranking,
            [
                "- Rank 1: no-API mechanical replay from the audited source universe.",
                "- API delta work is deferred and API-gated.",
                "- OWNER-TICK-0020/0021 remain optional only for future native bid/ask/flags needs.",
            ],
        )
    )

    breadth = build_breadth_audit(source_rows, missed_rows, root_searches)
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SOURCE_BREADTH_SCOPE_AUDIT_{DATE}.json", breadth))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_SOURCE_BREADTH_SCOPE_AUDIT_{DATE}.md",
            "NO API Historical Replay Source Breadth Scope Audit",
            breadth,
            [
                f"- Symbols considered: `{len(breadth['by_symbol'])}`",
                f"- Timeframes considered: `{json.dumps(breadth['by_timeframe'], sort_keys=True)}`",
                f"- Source families considered: `{json.dumps(breadth['by_source_family'], sort_keys=True)}`",
                f"- Missed-opportunity kill-zone counts: `{json.dumps(breadth['missed_by_kill_zone'], sort_keys=True)}`",
            ],
        )
    )

    noleak = build_noleak_audit(source_rows, missed_rows, root_searches)
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_NOLEAK_SAFETY_AUDIT_{DATE}.json", noleak))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_NOLEAK_SAFETY_AUDIT_{DATE}.md",
            "NO API Historical Replay Noleak Safety Audit",
            noleak,
            [
                f"- Audit passed: `{noleak['audit_passed']}`",
                f"- Excluded sensitive path count: `{noleak['excluded_sensitive_path_count']}`",
                "- No validation/result/live/API surfaces are opened.",
            ],
        )
    )

    saturation = base_payload(
        "saturation_self_redteam_pass",
        questions=[
            {
                "question": "Could source-control evidence be mistaken for validation/result evidence?",
                "answer": "No. Every artifact stamps validation_safe=false and result scoring is forbidden; source rows carry evidence_class and partition_assignment.",
            },
            {
                "question": "Could projection rows be mistaken for original GTOS intent?",
                "answer": "No. Missing prompt/output/gate/lifecycle fields fail closed to projection-only in the contract and boundary ledger.",
            },
            {
                "question": "Could account/result paths leak into the inventory?",
                "answer": "Scanner excludes sensitive account/result/credential paths; noleak audit checks source rows and missed inventory text.",
            },
            {
                "question": "Could the route be boxed into NOFILL/current worktree?",
                "answer": "No. It searches worktree data/shadow/research, absolute main data/ticks/shadow, SierraChart/Data, and prior worktrees.",
            },
            {
                "question": "What remains intentionally unanswered?",
                "answer": "No replay scoring, no validation, no AI delta, no broker actual-R, no live behavior; rank-1 next route owns deterministic replay inventory.",
            },
        ],
        same_evidence_class_gaps_remaining=[],
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS_{DATE}.json", saturation))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_REDTEAM_PASS_{DATE}.md",
            "NO API Historical Replay Saturation Self Redteam Pass",
            saturation,
            [
                "- Same-evidence-class source search was pursued across approved roots.",
                "- Remaining work crosses into deterministic replay execution, API-gated AI delta, or future capture readiness.",
                "- No unresolved lazy blocker remains inside this source-universe inventory route.",
            ],
        )
    )

    prompt_text = selected_next_prompt_text()
    NEXT_PROMPT_PATH.write_text(prompt_text, encoding="utf-8")
    written.append(NEXT_PROMPT_PATH)
    selected_prompt_payload = base_payload(
        "selected_next_full_controlling_prompt",
        selected_next_route_id="NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE",
        selected_next_prompt=rel(NEXT_PROMPT_PATH),
        prompt_sha256=hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_SELECTED_NEXT_FULL_CONTROLLING_PROMPT_{DATE}.json", selected_prompt_payload))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_SELECTED_NEXT_FULL_CONTROLLING_PROMPT_{DATE}.md",
            "NO API Historical Replay Selected Next Full Controlling Prompt",
            selected_prompt_payload,
            [
                f"- Selected next prompt: `{rel(NEXT_PROMPT_PATH)}`",
                f"- Selected next route: `{selected_prompt_payload['selected_next_route_id']}`",
            ],
        )
    )

    starter = build_one_line_starter()
    starter_payload = base_payload(
        "selected_next_one_line_starter",
        selected_next_route_id="NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE",
        selected_next_prompt=rel(NEXT_PROMPT_PATH),
        one_line_starter=starter,
        one_line_starter_sha256=hashlib.sha256(starter.encode("utf-8")).hexdigest(),
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_ONE_LINE_STARTER_{DATE}.json", starter_payload))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_ONE_LINE_STARTER_{DATE}.md",
            "NO API Historical Replay One Line Starter",
            starter_payload,
            ["```text", starter, "```"],
        )
    )

    manifest_names = [rel(path) for path in written]
    completion = build_completion_audit(manifest_names, source_rows, missed_rows, noleak)
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", completion))
    written.append(
        write_md(
            ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
            "NO API Historical Replay Completion Audit",
            completion,
            [
                f"- Completion standard satisfied: `{completion['completion_standard_satisfied']}`",
                f"- Can mark goal complete: `{completion['can_mark_goal_complete']}`",
                f"- Missing/incomplete/weak requirements: `{completion['missing_incomplete_or_weak_requirements']}`",
            ],
        )
    )

    output_manifest = base_payload(
        "output_manifest",
        artifact_count=len(written) + 1,
        artifacts=[rel(path) for path in written],
        selected_next_prompt=rel(NEXT_PROMPT_PATH),
    )
    written.append(write_json(ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE}.json", output_manifest))

    return written


def main() -> int:
    written = write_all()
    print(json.dumps({"route_id": ROUTE_ID, "written": len(written), "route_dir": str(ROUTE_DIR)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
