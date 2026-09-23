from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - verifier records parser availability
    pq = None


ROUTE_ID = "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

ACTIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

SYMBOL_ALIASES = {
    "GER40.cash": "GER40",
    "GER30": "GER40",
    "JP225.cash": "JP225",
    "NDX100": "NAS100",
    "US100.cash": "NAS100",
    "USTEC": "NAS100",
    "US500.cash": "SPX500",
    "US30": "US30_cash",
    "US30.cash": "US30_cash",
    "UK100.cash": "UK100",
    "UKOIL.cash": "UKOIL_cash",
    "UKOUSD": "UKOIL_cash",
    "USOIL.cash": "USOIL_cash",
    "USOUSD": "USOIL_cash",
}

REQUIRED_TIMEFRAMES = ["TICK", "M1", "M5", "M15", "H1", "H4", "D1"]

BROKER_FIELD_GROUPS = {
    "broker_specs": [
        "contract_size",
        "tick_size",
        "tick_value",
        "point_value",
        "volume_min",
        "volume_step",
        "volume_max",
        "trade_calc_mode",
        "filling_mode",
        "order_mode",
    ],
    "account_deal_order_position_history": [
        "orders",
        "deals",
        "positions",
        "tickets",
        "position_id",
        "close_reason",
        "partial_close_lifecycle",
    ],
    "spread": ["time_varying_spread_samples", "spread_r_at_order_send", "entry_spread_r"],
    "stops_freeze": ["stop_level", "freeze_level", "time_varying_stop_freeze_samples"],
    "swaps": ["swap_long", "swap_short", "swap_mode", "triple_day_rollover"],
    "commissions": ["commission_schedule", "commission", "fee"],
    "symbol_aliases": ["broker_symbol", "canonical_symbol", "alias_map"],
    "session_schedules": ["trading_sessions_by_weekday", "holiday_calendar", "server_timezone_and_dst"],
    "cost_fields": ["commission", "swap", "spread", "slippage", "fee", "net_drag_r"],
}

PARSER_REGISTRY = [
    {
        "parser_id": "csv_ohlc_time_series_v1",
        "formats": ["csv"],
        "source_classes": ["mt5_market_history", "repo_market_history", "m1_forward_capture"],
        "schema_fields_any": ["time", "time_utc", "open", "high", "low", "close"],
        "deterministic_checks": ["header_read", "row_count", "first_last_time_probe"],
    },
    {
        "parser_id": "parquet_tick_bid_ask_v1",
        "formats": ["parquet"],
        "source_classes": ["tick_bid_ask_history"],
        "schema_fields_any": ["time", "time_utc", "bid", "ask", "last"],
        "deterministic_checks": ["parquet_metadata", "row_count", "schema_columns"],
    },
    {
        "parser_id": "jsonl_runtime_route_ledger_v1",
        "formats": ["jsonl", "jsonl_gz"],
        "source_classes": [
            "runtime_shadow_log",
            "route_ledger",
            "selected_denominator_replay",
            "broker_lifecycle_truth",
        ],
        "schema_fields_any": [],
        "deterministic_checks": ["line_count", "first_last_json_parse", "field_presence_probe"],
    },
    {
        "parser_id": "json_summary_contract_v1",
        "formats": ["json"],
        "source_classes": ["route_summary", "manifest", "state_snapshot", "broker_readonly_snapshot"],
        "schema_fields_any": [],
        "deterministic_checks": ["json_parse", "top_level_shape", "summary_count_probe"],
    },
    {
        "parser_id": "yaml_config_contract_v1",
        "formats": ["yaml"],
        "source_classes": ["active_config"],
        "schema_fields_any": [],
        "deterministic_checks": ["text_readable", "yaml_parser_available"],
    },
    {
        "parser_id": "markdown_context_contract_v1",
        "formats": ["markdown"],
        "source_classes": ["context_authority", "route_report"],
        "schema_fields_any": [],
        "deterministic_checks": ["text_readable", "heading_probe"],
    },
    {
        "parser_id": "mt5_native_cache_inventory_v1",
        "formats": ["hcc", "hc", "tkc", "dat"],
        "source_classes": ["local_mt5_cache_native"],
        "schema_fields_any": [],
        "deterministic_checks": ["file_presence", "path_symbol_timeframe_inference", "archive_manifest_presence"],
    },
]

SOURCE_USE_RULES = {
    "broker_real_truth": (
        "May prove broker orders, deals, positions, tickets, account state, and costs for captured windows only. "
        "No price-path or historical intent reconstruction beyond captured rows."
    ),
    "mt5_market_history": (
        "May prove market bars/ticks and source availability for the exported/cache window. "
        "Cannot prove GTOS intent, order lifecycle, or broker fill truth without broker/account rows."
    ),
    "local_mt5_cache": (
        "May prove local terminal cache presence, native history/cache files, and archive preservation. "
        "Server-current symbol specs and full account history still require read-only export."
    ),
    "selected_denominator": (
        "May prove selected replay/proxy denominator rows and source-completeness fields. "
        "Discovery/stress only unless a separate validation lane freezes partitions."
    ),
    "replay_projection": (
        "May prove deterministic replay/projection output under the route's source contract. "
        "Does not prove broker-real execution unless joined to broker truth."
    ),
    "runtime_shadow_log": (
        "May prove current runtime/shadow emissions and forward capture for logged fields. "
        "Missing logger fields remain non-generatable historical truth."
    ),
    "route_summary": (
        "May guide downstream routing when backed by row ledgers/manifests. "
        "Not a substitute for row-bearing artifacts."
    ),
    "stale_historical": (
        "Historical or comparator-only input. Use only when current artifacts cite it or when extracting unique cold evidence."
    ),
    "sensitive_excluded": "Presence/exclusion proof only. Do not parse or expose content.",
    "missing_recoverable": "Recoverable through local cache, read-only export, or future capture as specified by the gap row.",
    "non_generatable_historical_truth": (
        "Cannot be generated from price movement alone. Requires already-logged source truth or prospective capture."
    ),
}


@dataclass(frozen=True)
class RootDef:
    root_id: str
    path: Path
    evidence_class: str
    authority_level: str
    material_scope: str
    source_use_rule_key: str
    tracked_status: str = "repo"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def path_sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info() -> dict[str, Any]:
    def run(args: list[str]) -> str:
        return subprocess.check_output(args, cwd=REPO_ROOT, text=True, encoding="utf-8").strip()

    try:
        return {
            "head": run(["git", "rev-parse", "HEAD"]),
            "head_short": run(["git", "rev-parse", "--short", "HEAD"]),
            "head_subject": run(["git", "log", "-1", "--format=%s"]),
        }
    except Exception as exc:
        return {"error": str(exc)}


def load_json(path: Path, default: Any = None) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix.lower() == ".gz" else open
    mode = "rt"
    with opener(path, mode, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            f.write("\n")
            count += 1
    return count


def line_count_binary(path: Path, gzip_mode: bool = False) -> int | None:
    try:
        if gzip_mode:
            count = 0
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        count = 0
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                count += chunk.count(b"\n")
        if path.stat().st_size > 0:
            with path.open("rb") as f:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    count += 1
        return count
    except Exception:
        return None


def first_last_text_lines(path: Path, gzip_mode: bool = False) -> tuple[str | None, str | None]:
    try:
        if gzip_mode:
            first = None
            last = None
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if first is None:
                        first = line
                    last = line
            return first, last

        first = None
        with path.open("rb") as f:
            for raw in f:
                raw = raw.strip()
                if raw:
                    first = raw.decode("utf-8", errors="replace")
                    break
        if path.stat().st_size == 0:
            return first, None
        with path.open("rb") as f:
            seek_size = min(path.stat().st_size, 1024 * 1024)
            f.seek(-seek_size, os.SEEK_END)
            lines = [line.strip() for line in f.read().splitlines() if line.strip()]
            last = lines[-1].decode("utf-8", errors="replace") if lines else None
        return first, last
    except Exception:
        return None, None


def classify_format(path: Path) -> str:
    suffixes = [s.lower() for s in path.suffixes]
    suffix = path.suffix.lower()
    if suffixes[-2:] == [".jsonl", ".gz"]:
        return "jsonl_gz"
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    if suffix == ".parquet":
        return "parquet"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".md":
        return "markdown"
    if suffix == ".xml":
        return "xml"
    if suffix == ".py":
        return "python"
    if suffix == ".hcc":
        return "hcc"
    if suffix == ".hc":
        return "hc"
    if suffix == ".tkc":
        return "tkc"
    if suffix == ".dat":
        return "dat"
    if suffix == ".gz":
        return "gzip"
    if suffix in {".txt", ".log"}:
        return "text"
    return suffix[1:] if suffix else "unknown"


def canonical_symbol_from_text(text: str) -> str | None:
    upper = text.replace("\\", "/").upper()
    alias_items = sorted(SYMBOL_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True)
    for alias, canonical in alias_items:
        if alias.upper() in upper:
            return canonical
    for symbol in sorted(ACTIVE_SYMBOLS, key=len, reverse=True):
        if symbol.upper() in upper:
            return symbol
    return None


def infer_timeframe(path: Path, fmt: str) -> str | None:
    text = str(path).replace("\\", "/")
    upper = text.upper()
    if "/DATA/TICKS/" in upper or fmt == "tkc":
        return "TICK"
    if "/DATA/M1/" in upper:
        return "M1"
    if fmt == "hcc":
        return "M1_PACKED_YEAR"
    stem = path.stem.upper()
    name = path.name.upper()
    for tf in ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]:
        if re.search(rf"(^|[_\-.\\/]){tf}($|[_\-.\\/])", upper) or stem == tf or name == f"{tf}.HC":
            return tf
    if "TICK_MONTH" in upper or "TICK_METADATA" in upper:
        return "TICK"
    return None


def normalize_timeframe(tf: str | None) -> str | None:
    if tf in {"M1_PACKED_YEAR"}:
        return "M1"
    if tf in {"TICK_MONTH", "TICK_METADATA"}:
        return "TICK"
    return tf


def infer_dates_from_name(path: Path) -> tuple[str | None, str | None, str | None]:
    text = str(path).replace("\\", "/")
    day_match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    if day_match:
        d = day_match.group(1)
        return d, d, "filename_date"
    year_match = re.search(r"(20\d{2})\.(hcc|tkc)$", path.name.lower())
    if year_match:
        y = year_match.group(1)
        return f"{y}-01-01", f"{y}-12-31", "filename_year"
    return None, None, None


TIME_KEYS = [
    "time_utc",
    "ts_utc",
    "generated_at_utc",
    "entry_time_utc",
    "candidate_time_utc",
    "source_time_utc",
    "time_msc_utc",
    "captured_at_utc",
    "calendar_start_utc",
    "calendar_end_utc",
    "first_date",
    "last_date",
    "time",
    "timestamp",
    "date",
]


def extract_time_values(obj: Any) -> list[str]:
    values: list[str] = []
    if isinstance(obj, dict):
        for key in TIME_KEYS:
            value = obj.get(key)
            if isinstance(value, str) and value:
                values.append(value)
        for value in obj.values():
            if isinstance(value, dict):
                for key in TIME_KEYS:
                    inner = value.get(key)
                    if isinstance(inner, str) and inner:
                        values.append(inner)
    return values


def parse_json_line(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else {"_list_len": len(obj)} if isinstance(obj, list) else {"_value": obj}


def source_class_for(root: RootDef, path: Path, fmt: str) -> tuple[str, str, str]:
    rel = rel_path(path)
    rel_lower = rel.lower()
    if root.root_id == "repo_data":
        if "/account_history/" in rel_lower:
            return "broker_lifecycle_truth", "broker_real_truth", "broker_real_truth"
        if "/ticks/" in rel_lower:
            return "tick_bid_ask_history", "mt5_market_history", "mt5_market_history"
        if "/m1/" in rel_lower:
            return "m1_forward_capture", "mt5_market_history", "mt5_market_history"
        if "/mt5_research_exports/" in rel_lower:
            return "mt5_readonly_market_export", "mt5_market_history", "mt5_market_history"
        if fmt == "csv":
            return "repo_market_history", "mt5_market_history", "mt5_market_history"
    if root.root_id == "shadow_logs":
        return "runtime_shadow_log", "runtime_shadow_log", "runtime_shadow_log"
    if root.root_id == "pipeline_state":
        return "hot_runtime_state", "runtime_shadow_log", "runtime_shadow_log"
    if root.root_id == "knowledge_base":
        return "trade_record_or_monitoring_state", "runtime_shadow_log", "runtime_shadow_log"
    if root.root_id == "config":
        return "active_config", "route_summary", "route_summary"
    if root.root_id == "src":
        return "runtime_source_code", "route_summary", "route_summary"
    if root.root_id == "tests":
        return "test_contract", "route_summary", "route_summary"
    if root.root_id == "mt5_local_cache_preservation_route":
        if "sensitive_exclusion" in rel_lower:
            return "sensitive_exclusion_ledger", "sensitive_excluded", "sensitive_excluded"
        if "mt5_local_cache_inventory" in rel_lower or "mt5_archive" in rel_lower:
            return "local_mt5_cache_manifest", "local_mt5_cache", "local_mt5_cache"
        return "mt5_cache_route_output", "route_summary", "route_summary"
    if root.root_id == "vps_data_preservation_route":
        if "missing_source_export_requirements" in rel_lower or "broker_portability_gap" in rel_lower:
            return "missing_source_requirement", "missing_recoverable", "missing_recoverable"
        return "vps_data_preservation_output", "route_summary", "route_summary"
    if root.root_id == "friday_microscope_route":
        if fmt == "jsonl":
            return "friday_microscope_ledger", "replay_projection", "replay_projection"
        return "friday_microscope_summary", "route_summary", "route_summary"
    if root.root_id == "live_companion_route":
        if fmt == "jsonl":
            return "live_companion_ledger", "runtime_shadow_log", "runtime_shadow_log"
        return "live_companion_state_summary", "runtime_shadow_log", "runtime_shadow_log"
    if root.root_id == "absolute_master_route":
        return "absolute_master_orchestration_output", "route_summary", "route_summary"
    if root.root_id == "lane02_broad_selected":
        if "broad_selected_portfolio_replay_ledger" in rel_lower:
            return "selected_denominator_replay", "selected_denominator", "selected_denominator"
        return "lane02_selected_stress_output", "selected_denominator", "selected_denominator"
    if root.root_id == "lane04_selected_cell_risk":
        return "selected_cell_risk_source_bridge", "selected_denominator", "selected_denominator"
    if root.root_id == "lane06_broker_truth":
        return "broker_readonly_snapshot", "broker_real_truth", "broker_real_truth"
    if root.root_id == "lane08_execution_policy":
        return "execution_policy_replay_projection", "replay_projection", "replay_projection"
    if root.root_id.startswith("lane"):
        return "next_level_lane_output", "route_summary", "route_summary"
    if root.root_id.startswith("activation"):
        if "final_dynamic_router_replay" in rel_lower:
            return "selected_denominator_replay", "selected_denominator", "selected_denominator"
        return "activation_repair_route_output", "replay_projection", "replay_projection"
    if root.root_id == "external_mt5_archive":
        return "external_mt5_archive_file", "local_mt5_cache", "local_mt5_cache"
    if root.root_id == "prior_science_worktree":
        return "prior_worktree_research_reference", "stale_historical", "stale_historical"
    return root.evidence_class, root.authority_level, root.source_use_rule_key


def parser_id_for(fmt: str, source_class: str) -> str | None:
    for parser in PARSER_REGISTRY:
        if fmt in parser["formats"] and source_class in parser["source_classes"]:
            return parser["parser_id"]
    for parser in PARSER_REGISTRY:
        if fmt in parser["formats"]:
            return parser["parser_id"]
    return None


def inspect_file(path: Path, root: RootDef) -> tuple[dict[str, Any], dict[str, Any]]:
    fmt = classify_format(path)
    source_class, authority, rule_key = source_class_for(root, path, fmt)
    parser_id = parser_id_for(fmt, source_class)
    first_date, last_date, date_source = infer_dates_from_name(path)
    row_count: int | None = None
    schema_fields: list[str] = []
    parser_status = "not_row_or_schema_parsed"
    parser_issue = None

    try:
        if fmt == "csv":
            row_count = max((line_count_binary(path) or 0) - 1, 0)
            with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                schema_fields = [h.strip() for h in header]
                first_data = next(reader, None)
            _, last_line = first_last_text_lines(path)
            time_idx = next((i for i, h in enumerate(schema_fields) if h in TIME_KEYS), None)
            if time_idx is not None:
                if first_data and len(first_data) > time_idx:
                    first_date = first_date or first_data[time_idx]
                if last_line:
                    last_parts = next(csv.reader([last_line]))
                    if len(last_parts) > time_idx:
                        last_date = last_date or last_parts[time_idx]
                date_source = date_source or "csv_time_column"
            parser_status = "ok"
        elif fmt in {"jsonl", "jsonl_gz"}:
            row_count = line_count_binary(path, gzip_mode=(fmt == "jsonl_gz"))
            first_line, last_line = first_last_text_lines(path, gzip_mode=(fmt == "jsonl_gz"))
            first_obj = parse_json_line(first_line)
            last_obj = parse_json_line(last_line)
            schema_fields = sorted(first_obj.keys()) if isinstance(first_obj, dict) else []
            times = extract_time_values(first_obj) + extract_time_values(last_obj)
            if times:
                first_date = first_date or times[0]
                last_date = last_date or times[-1]
                date_source = date_source or "jsonl_first_last_time_probe"
            parser_status = "ok" if first_obj is not None or row_count == 0 else "parse_probe_failed"
        elif fmt == "json":
            obj = load_json(path, default=None)
            if isinstance(obj, list):
                row_count = len(obj)
                schema_fields = sorted(obj[0].keys()) if obj and isinstance(obj[0], dict) else []
            elif isinstance(obj, dict):
                schema_fields = sorted(obj.keys())
                for count_key in [
                    "rows",
                    "total_rows",
                    "selected_surface_rows",
                    "input_rows",
                    "history_deals",
                    "history_orders",
                    "positions",
                    "file_rows",
                    "inventory_rows",
                ]:
                    value = obj.get(count_key)
                    if isinstance(value, int):
                        row_count = value
                        break
                times = extract_time_values(obj)
                if times:
                    first_date = first_date or times[0]
                    last_date = last_date or times[-1]
                    date_source = date_source or "json_time_probe"
            parser_status = "ok" if obj is not None else "json_parse_failed"
        elif fmt == "parquet":
            if pq is None:
                parser_status = "pyarrow_unavailable"
                parser_issue = "pyarrow import unavailable"
            else:
                pf = pq.ParquetFile(path)
                row_count = pf.metadata.num_rows
                schema_fields = list(pf.schema_arrow.names)
                parser_status = "ok"
        elif fmt in {"markdown", "text", "yaml", "python", "xml"}:
            with path.open("r", encoding="utf-8", errors="replace") as f:
                sample = f.read(4096)
            row_count = line_count_binary(path)
            if fmt == "markdown":
                schema_fields = [line.strip() for line in sample.splitlines() if line.startswith("#")][:20]
            parser_status = "ok"
        elif fmt in {"hcc", "hc", "tkc", "dat", "gzip", "unknown"}:
            parser_status = "presence_only_native_or_binary"
        else:
            parser_status = "presence_only"
    except Exception as exc:
        parser_status = "error"
        parser_issue = f"{type(exc).__name__}: {exc}"

    canonical_symbol = canonical_symbol_from_text(str(path))
    timeframe = infer_timeframe(path, fmt)
    normalized_timeframe = normalize_timeframe(timeframe)
    stat = path.stat()
    inventory_row = {
        "schema_version": "lane01_data_source_inventory_v1",
        "route_id": ROUTE_ID,
        "root_id": root.root_id,
        "path": rel_path(path),
        "path_sha256": path_sha256_text(str(path.resolve())),
        "tracked_status": root.tracked_status,
        "format": fmt,
        "extension": path.suffix.lower() or None,
        "bytes": stat.st_size,
        "modified_time_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "row_count": row_count,
        "file_count": 1,
        "evidence_class": root.evidence_class,
        "source_class": source_class,
        "authority_level": authority,
        "source_use_rule": SOURCE_USE_RULES.get(rule_key, SOURCE_USE_RULES["route_summary"]),
        "canonical_symbol": canonical_symbol,
        "timeframe": normalized_timeframe,
        "raw_timeframe": timeframe,
        "time_coverage_start": first_date,
        "time_coverage_end": last_date,
        "time_coverage_source": date_source,
        "parser_id": parser_id,
        "parser_available": parser_id is not None,
        "parser_status": parser_status,
        "schema_fields": schema_fields,
        "freshness": "current_or_hot" if root.root_id in {"shadow_logs", "pipeline_state", "live_companion_route"} else "route_or_historical",
        "material_scope": root.material_scope,
    }
    parser_row = {
        "schema_version": "lane01_parser_check_result_v1",
        "route_id": ROUTE_ID,
        "path": inventory_row["path"],
        "root_id": root.root_id,
        "format": fmt,
        "source_class": source_class,
        "parser_id": parser_id,
        "parser_available": parser_id is not None,
        "parser_status": parser_status,
        "parser_issue": parser_issue,
        "row_count": row_count,
        "schema_field_count": len(schema_fields),
        "schema_fields": schema_fields,
        "deterministic_check_scope": "all_material_inventory_files_no_top_n_sampling",
    }
    return inventory_row, parser_row


def route_roots() -> list[RootDef]:
    return [
        RootDef("repo_data", REPO_ROOT / "data", "repo_market_and_broker_data", "mt5_market_history", "repo data/ including account_history, ticks, m1, historical OHLC, and MT5 research exports", "mt5_market_history"),
        RootDef("repo_exports", REPO_ROOT / "exports", "legacy_exports", "stale_historical", "legacy exports; comparator/cold evidence unless current route consumes them", "stale_historical"),
        RootDef("shadow_logs", REPO_ROOT / "shadow_logs", "shadow_live_runtime_logs", "runtime_shadow_log", "runtime/shadow logs and forward capture rows", "runtime_shadow_log"),
        RootDef("pipeline_state", REPO_ROOT / "pipeline_state", "hot_runtime_state", "runtime_shadow_log", "runtime state, heartbeats, monitor state, capture state", "runtime_shadow_log"),
        RootDef("knowledge_base", REPO_ROOT / "knowledge_base", "trade_records_and_monitoring", "runtime_shadow_log", "trade records and monitoring state", "runtime_shadow_log"),
        RootDef("config", REPO_ROOT / "config", "active_config", "route_summary", "active config inspected only; no live behavior change", "route_summary"),
        RootDef("src", REPO_ROOT / "src", "runtime_source_code", "route_summary", "runtime/source parser availability and downstream code contracts", "route_summary"),
        RootDef("tests", REPO_ROOT / "tests", "test_contracts", "route_summary", "existing tests as deterministic enforcement evidence", "route_summary"),
        RootDef("context_core", REPO_ROOT / ".context" / "00_core", "current_context_authority", "route_summary", "current context authority and doctrine", "route_summary"),
        RootDef("goal_prompts", REPO_ROOT / "research" / "science_program_2026_05" / "04_goal_prompts", "goal_prompt_pack", "route_summary", "absolute moonshot prompt pack", "route_summary"),
        RootDef("mt5_local_cache_preservation_route", REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01", "mt5_local_cache_preservation", "local_mt5_cache", "MT5 local cache inventory/archive route", "local_mt5_cache"),
        RootDef("vps_data_preservation_route", REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01", "vps_data_preservation", "route_summary", "compliant VPS/data preservation and broker portability route", "route_summary"),
        RootDef("friday_microscope_route", REPO_ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31", "friday_microscope", "replay_projection", "Friday microscope route", "replay_projection"),
        RootDef("live_companion_route", REPO_ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28", "live_companion", "runtime_shadow_log", "hot live companion route", "runtime_shadow_log"),
        RootDef("next_level_master_route", REPO_ROOT / "research" / "operations" / "vnext_next_level_master_orchestration_2026_05_31", "next_level_master", "route_summary", "current next-level master route", "route_summary"),
        RootDef("absolute_master_route", REPO_ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01", "absolute_master_orchestration", "route_summary", "absolute moonshot master orchestration route", "route_summary"),
        RootDef("lane01_fixed_friday", REPO_ROOT / "research" / "operations" / "vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31", "next_level_lane_output", "replay_projection", "next-level lane01 fixed Friday portfolio replay", "replay_projection"),
        RootDef("lane02_broad_selected", REPO_ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31", "next_level_lane_output", "selected_denominator", "next-level lane02 broad selected denominator", "selected_denominator"),
        RootDef("lane03_meta_selector", REPO_ROOT / "research" / "operations" / "vnext_lane03_meta_selector_discovery_implementation_2026_05_31", "next_level_lane_output", "replay_projection", "next-level lane03 meta selector", "replay_projection"),
        RootDef("lane04_selected_cell_risk", REPO_ROOT / "research" / "operations" / "vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31", "next_level_lane_output", "selected_denominator", "next-level lane04 selected-cell risk bridge", "selected_denominator"),
        RootDef("lane05_scheduler", REPO_ROOT / "research" / "operations" / "vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31", "next_level_lane_output", "replay_projection", "next-level lane05 scheduler", "replay_projection"),
        RootDef("lane06_broker_truth", REPO_ROOT / "research" / "operations" / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31", "next_level_lane_output", "broker_real_truth", "next-level lane06 broker lifecycle net-R/cost truth", "broker_real_truth"),
        RootDef("lane07_market_coverage", REPO_ROOT / "research" / "operations" / "vnext_lane07_market_coverage_source_starvation_repair_2026_05_31", "next_level_lane_output", "runtime_shadow_log", "next-level lane07 market coverage", "runtime_shadow_log"),
        RootDef("lane08_execution_policy", REPO_ROOT / "research" / "operations" / "vnext_lane08_execution_policy_microstructure_stress_2026_05_31", "next_level_lane_output", "replay_projection", "next-level lane08 execution policy microstructure stress", "replay_projection"),
        RootDef("lane09_merge_package", REPO_ROOT / "research" / "operations" / "vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31", "next_level_lane_output", "route_summary", "next-level lane09 merge/dossier package", "route_summary"),
        RootDef("activation_repair_hardening_route", REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27", "activation_repair_route", "replay_projection", "activation repair-hardening route and selected denominator shards", "replay_projection"),
        RootDef("activation_route", REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "vnext_moonshot_production_replacement_activation_2026_05_26", "activation_route", "replay_projection", "activation market source and broker geometry route", "replay_projection"),
        RootDef("external_mt5_archive", Path(r"C:\Users\MSI\Documents\GTOS_MT5_LOCAL_PRESERVATION_2026_06_01"), "external_mt5_archive", "local_mt5_cache", "outside-git MT5 local cache preservation archive", "local_mt5_cache", tracked_status="outside_git"),
        RootDef("prior_science_worktree", Path(r"C:\Users\MSI\Documents\gtos-science-goals"), "prior_science_worktree", "stale_historical", "referenced prior science worktree; cold evidence only", "stale_historical", tracked_status="outside_git"),
    ]


def should_skip(path: Path) -> bool:
    skip_parts = {"__pycache__", ".git", ".pytest_cache"}
    return any(part in skip_parts or part.startswith(".pytest-tmp") for part in path.parts)


def scan_inventory() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    inventory: list[dict[str, Any]] = []
    parser_results: list[dict[str, Any]] = []
    acquisition_rows: list[dict[str, Any]] = []
    for root in route_roots():
        if not root.path.exists():
            acquisition_rows.append(
                {
                    "schema_version": "lane01_source_acquisition_attempt_v1",
                    "route_id": ROUTE_ID,
                    "root_id": root.root_id,
                    "path": str(root.path),
                    "action": "filesystem_scan",
                    "status": "missing_root_recorded_as_gap_or_dependency",
                    "source_use_state": "not_available_from_current_filesystem",
                }
            )
            continue
        files = [root.path] if root.path.is_file() else [p for p in root.path.rglob("*") if p.is_file() and not should_skip(p)]
        acquisition_rows.append(
            {
                "schema_version": "lane01_source_acquisition_attempt_v1",
                "route_id": ROUTE_ID,
                "root_id": root.root_id,
                "path": str(root.path),
                "action": "filesystem_scan",
                "status": "completed",
                "file_count": len(files),
                "source_use_state": root.source_use_rule_key,
            }
        )
        for file_path in sorted(files, key=lambda p: str(p).lower()):
            row, parser_row = inspect_file(file_path, root)
            inventory.append(row)
            parser_results.append(parser_row)
    acquisition_rows.append(
        {
            "schema_version": "lane01_source_acquisition_attempt_v1",
            "route_id": ROUTE_ID,
            "root_id": "direct_broker_server_mt5_readonly_export",
            "action": "mt5_server_readonly_export",
            "status": "not_executed_in_this_lane_due_compliant_vps_dependency_recorded",
            "source_use_state": "recoverable_missing_source_requirement",
            "evidence": [
                "research/operations/vnext_compliant_vps_data_preservation_broker_portability_2026_06_01/MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
                "research/operations/vnext_mt5_local_cache_preservation_2026_06_01/MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl",
            ],
            "reason": "current approved source artifacts require full account/symbol server export from compliant non-restricted non-US MT5/VPS origin; Lane01 records exact export requirements rather than opening a broker server session from this local route",
        }
    )
    acquisition_rows.append(
        {
            "schema_version": "lane01_source_acquisition_attempt_v1",
            "route_id": ROUTE_ID,
            "root_id": "paid_vendor_or_orderflow_depth_sources",
            "action": "external_api_or_paid_source",
            "status": "proven_inapplicable_by_prompt_forbidden_surface",
            "source_use_state": "excluded",
            "reason": "Lane01 prompt forbids Sierra, Databento, orderflow/depth API work and paid/vendor calls.",
        }
    )
    return inventory, parser_results, acquisition_rows


def summarize_inventory(inventory: list[dict[str, Any]]) -> dict[str, Any]:
    root_summary: dict[str, dict[str, Any]] = {}
    authority_counts = Counter(row["authority_level"] for row in inventory)
    source_class_counts = Counter(row["source_class"] for row in inventory)
    format_counts = Counter(row["format"] for row in inventory)
    parser_status_counts = Counter(row["parser_status"] for row in inventory)
    for row in inventory:
        root_id = row["root_id"]
        summary = root_summary.setdefault(
            root_id,
            {
                "file_count": 0,
                "bytes": 0,
                "row_count_known_sum": 0,
                "row_count_known_file_count": 0,
                "formats": Counter(),
                "source_classes": Counter(),
                "authority_levels": Counter(),
                "symbols": set(),
                "timeframes": set(),
                "first_time": None,
                "last_time": None,
            },
        )
        summary["file_count"] += 1
        summary["bytes"] += row.get("bytes") or 0
        if isinstance(row.get("row_count"), int):
            summary["row_count_known_sum"] += row["row_count"]
            summary["row_count_known_file_count"] += 1
        summary["formats"][row["format"]] += 1
        summary["source_classes"][row["source_class"]] += 1
        summary["authority_levels"][row["authority_level"]] += 1
        if row.get("canonical_symbol"):
            summary["symbols"].add(row["canonical_symbol"])
        if row.get("timeframe"):
            summary["timeframes"].add(row["timeframe"])
        for key, target in [("time_coverage_start", "first_time"), ("time_coverage_end", "last_time")]:
            value = row.get(key)
            if value:
                if summary[target] is None:
                    summary[target] = value
                elif target == "first_time" and value < summary[target]:
                    summary[target] = value
                elif target == "last_time" and value > summary[target]:
                    summary[target] = value

    normalized = {}
    for root_id, summary in root_summary.items():
        normalized[root_id] = {
            **{k: v for k, v in summary.items() if k not in {"formats", "source_classes", "authority_levels", "symbols", "timeframes"}},
            "formats": dict(summary["formats"]),
            "source_classes": dict(summary["source_classes"]),
            "authority_levels": dict(summary["authority_levels"]),
            "symbols": sorted(summary["symbols"]),
            "timeframes": sorted(summary["timeframes"]),
        }
    return {
        "schema_version": "lane01_source_authority_map_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "git": git_info(),
        "active_symbols": ACTIVE_SYMBOLS,
        "root_summary": normalized,
        "global_counts": {
            "file_count": len(inventory),
            "bytes": sum(row.get("bytes") or 0 for row in inventory),
            "known_row_count_sum": sum(row.get("row_count") or 0 for row in inventory if isinstance(row.get("row_count"), int)),
            "authority_counts": dict(authority_counts),
            "source_class_counts": dict(source_class_counts),
            "format_counts": dict(format_counts),
            "parser_status_counts": dict(parser_status_counts),
        },
        "source_use_rules": SOURCE_USE_RULES,
        "parser_registry": PARSER_REGISTRY,
    }


def load_route_inputs() -> dict[str, Any]:
    return {
        "vps_coverage": load_json(REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01" / "LOCAL_EVIDENCE_COVERAGE_SUMMARY.json", {}),
        "vps_requirement_map": load_json(REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01" / "ABSOLUTE_MOONSHOT_DATA_REQUIREMENT_MAP.json", {}),
        "mt5_cache_summary": load_json(REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01" / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json", {}),
        "mt5_repo_comparison": load_json(REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01" / "MT5_REPO_COVERAGE_COMPARISON.json", {}),
        "mt5_archive_manifest": load_json(REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01" / "MT5_ARCHIVE_MANIFEST.json", {}),
        "lane02_summary": load_json(REPO_ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31" / "LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json", {}),
        "lane04_state": load_json(REPO_ROOT / "research" / "operations" / "vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31" / "LANE04_ROUTE_STATE.json", {}),
        "lane06_summary": load_json(REPO_ROOT / "research" / "operations" / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31" / "LANE06_SUMMARY.json", {}),
        "lane06_snapshot": load_json(REPO_ROOT / "research" / "operations" / "vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31" / "LANE06_MT5_READONLY_SNAPSHOT.json", {}),
        "lane08_summary": load_json(REPO_ROOT / "research" / "operations" / "vnext_lane08_execution_policy_microstructure_stress_2026_05_31" / "LANE08_EXPECTANCY_SUMMARY.json", {}),
        "live_companion_state": load_json(REPO_ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28" / "ACTIVE_REPAIR_STATE.json", {}),
    }


def normalize_mt5_coverage(raw: dict[str, list[str]]) -> dict[str, set[str]]:
    normalized: dict[str, set[str]] = defaultdict(set)
    for symbol, tfs in raw.items():
        canonical = SYMBOL_ALIASES.get(symbol, symbol)
        if canonical not in ACTIVE_SYMBOLS:
            continue
        for tf in tfs:
            ntf = normalize_timeframe(tf)
            if ntf:
                normalized[canonical].add(ntf)
    return normalized


def build_gap_ledgers(inputs: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    gaps: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    repo_coverage = inputs.get("vps_coverage", {}).get("timeframe_coverage_by_symbol", {})
    mt5_coverage = normalize_mt5_coverage(inputs.get("mt5_cache_summary", {}).get("timeframe_coverage_by_symbol", {}))
    lane02_source_path = REPO_ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31" / "LANE02_SOURCE_COMPLETENESS_LEDGER.jsonl"

    for symbol in ACTIVE_SYMBOLS:
        for tf in REQUIRED_TIMEFRAMES:
            repo_present = tf in set(repo_coverage.get(symbol, []))
            mt5_present = tf in mt5_coverage.get(symbol, set())
            if repo_present and mt5_present:
                status = "available_repo_and_preserved_mt5_cache"
                decision = "use_repo_primary_with_mt5_cache_cross_check"
            elif repo_present:
                status = "available_repo_only"
                decision = "use_repo_with_mt5_cache_gap_note"
            elif mt5_present:
                status = "recoverable_from_preserved_mt5_cache"
                decision = "recover_or_export_from_preserved_mt5_cache_before_downstream_use"
            else:
                status = "missing_after_repo_and_mt5_cache_inventory"
                decision = "read_only_mt5_export_or_future_capture_required"
            gaps.append(
                {
                    "schema_version": "lane01_source_gap_v1",
                    "route_id": ROUTE_ID,
                    "gap_family": "market_history_timeframe_coverage",
                    "symbol": symbol,
                    "timeframe": tf,
                    "repo_status": "present" if repo_present else "missing",
                    "mt5_cache_status": "present" if mt5_present else "missing",
                    "source_gap_status": status,
                    "source_completeness_decision": decision,
                    "source_use_state": "market_history_source_authority",
                }
            )

    for row in iter_jsonl(lane02_source_path):
        field = row.get("field")
        value = row.get("value")
        if field in {
            "m1_availability_status",
            "tick_availability_status",
            "source_quality_status",
            "ordered_path_status",
            "missing_field_note",
            "spread_r_bucket",
            "cost_status",
            "stop_freeze_feasibility_status",
        }:
            accepted = row.get("accepted_rows")
            rejected = row.get("rejected_rows")
            gaps.append(
                {
                    "schema_version": "lane01_source_gap_v1",
                    "route_id": ROUTE_ID,
                    "gap_family": f"selected_denominator_{field}",
                    "symbol": None,
                    "timeframe": None,
                    "source_gap_status": value,
                    "accepted_rows": accepted,
                    "rejected_rows": rejected,
                    "affected_rows": (accepted or 0) + (rejected or 0) if isinstance(accepted, int) or isinstance(rejected, int) else None,
                    "source_completeness_decision": "preserve_row_level_status_for_downstream_microscope_feature_label_and_execution_lanes",
                    "source_use_state": "selected_denominator_source_completeness",
                    "source_path": rel_path(lane02_source_path),
                }
            )

    for path in [
        REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01" / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl",
        REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01" / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl",
    ]:
        for row in iter_jsonl(path):
            gaps.append(
                {
                    "schema_version": "lane01_source_gap_v1",
                    "route_id": ROUTE_ID,
                    "gap_family": row.get("source_family") or "missing_export_requirement",
                    "symbol": row.get("symbol"),
                    "timeframe": None,
                    "missing_fields_or_windows": row.get("missing_fields_or_windows") or row.get("fields"),
                    "requirement_id": row.get("requirement_id"),
                    "source_gap_status": row.get("state") or "read_only_or_owner_capture_requirement",
                    "required_action": row.get("required_action"),
                    "proof_required": row.get("proof_required"),
                    "source_completeness_decision": "exact_read_only_export_or_owner_capture_required_before_downstream_authoritative_use",
                    "source_use_state": "missing_recoverable_or_non_generatable_by_field",
                    "source_path": rel_path(path),
                }
            )

    lane06_snapshot = inputs.get("lane06_snapshot", {})
    broker_symbols = sorted((lane06_snapshot.get("symbol_info") or {}).keys())
    gaps.append(
        {
            "schema_version": "lane01_source_gap_v1",
            "route_id": ROUTE_ID,
            "gap_family": "broker_server_readonly_snapshot_coverage",
            "symbol": None,
            "timeframe": None,
            "source_gap_status": "sparse_lane06_snapshot_present_full_24_symbol_export_missing",
            "covered_broker_symbols": broker_symbols,
            "history_deals": lane06_snapshot.get("history_deals"),
            "history_orders": lane06_snapshot.get("history_orders"),
            "positions": lane06_snapshot.get("positions"),
            "source_completeness_decision": "use_lane06_for_sparse_friday_broker_truth_only_full_export_required_for_authoritative_all_symbol_cost_specs",
            "source_use_state": "broker_real_truth_sparse_window",
            "source_path": "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31/LANE06_MT5_READONLY_SNAPSHOT.json",
        }
    )

    mt5_compare = inputs.get("mt5_repo_comparison", {})
    for symbol in mt5_compare.get("symbols_in_repo_not_in_external_mt5_cache", []):
        gaps.append(
            {
                "schema_version": "lane01_source_gap_v1",
                "route_id": ROUTE_ID,
                "gap_family": "symbol_alias_map",
                "symbol": symbol,
                "source_gap_status": "repo_symbol_not_exact_in_external_mt5_cache_alias_mapping_required",
                "source_completeness_decision": "use_alias_map_before_downstream_symbol_join",
                "source_use_state": "alias_reconciliation_required",
                "known_alias_candidates": [alias for alias, canonical in SYMBOL_ALIASES.items() if canonical == symbol],
            }
        )

    for family, fields in BROKER_FIELD_GROUPS.items():
        for symbol in ACTIVE_SYMBOLS:
            covered = symbol in broker_symbols or any(SYMBOL_ALIASES.get(raw) == symbol for raw in broker_symbols)
            gaps.append(
                {
                    "schema_version": "lane01_source_gap_v1",
                    "route_id": ROUTE_ID,
                    "gap_family": family,
                    "symbol": symbol,
                    "timeframe": None,
                    "missing_fields_or_windows": [] if covered and family == "symbol_aliases" else fields,
                    "source_gap_status": "partially_covered_by_sparse_lane06_snapshot" if covered else "full_read_only_broker_export_required",
                    "source_completeness_decision": "authoritative_downstream_use_requires_full_24_symbol_read_only_export_or_prospective_capture",
                    "source_use_state": "broker_truth_or_cost_gap",
                }
            )

    grouped = Counter(gap["gap_family"] for gap in gaps)
    for family, count in sorted(grouped.items()):
        decisions.append(
            {
                "schema_version": "lane01_source_completeness_decision_v1",
                "route_id": ROUTE_ID,
                "gap_family": family,
                "row_count": count,
                "decision": "preserve_full_gap_rows_and_route_to_downstream_contracts",
                "runtime_effect_boundary": "data_source_authority_only_no_live_runtime_or_config_change",
            }
        )
    return gaps, decisions


def build_dependency_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    dependencies = [
        ("absolute_master_route", REPO_ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01", "master route when present"),
        ("moonshot_lane02_asof_route", REPO_ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01", "downstream absolute moonshot lane02"),
        ("moonshot_lane03_candidate_reconstruction_route", REPO_ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01", "downstream absolute moonshot lane03"),
        ("mt5_local_cache_preservation_route", REPO_ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01", "local MT5 cache preservation input"),
        ("vps_data_preservation_route", REPO_ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01", "compliant VPS/data portability input"),
        ("friday_microscope_route", REPO_ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31", "Friday microscope input"),
        ("live_companion_route", REPO_ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28", "hot live companion input"),
        ("lane02_broad_selected_route", REPO_ROOT / "research" / "operations" / "vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31", "selected denominator input"),
    ]
    for dep_id, path, purpose in dependencies:
        rows.append(
            {
                "schema_version": "lane01_dependency_state_v1",
                "route_id": ROUTE_ID,
                "dependency_id": dep_id,
                "path": rel_path(path) if is_under(path, REPO_ROOT) else str(path),
                "purpose": purpose,
                "exists": path.exists(),
                "dependency_state": "present_consumed" if path.exists() else "absent_recorded_not_stop_condition",
                "action": "consume_latest_artifacts" if path.exists() else "record_exact_dependency_state_and_continue_independent_source_authority_work",
            }
        )
    lane02 = inputs.get("lane02_summary", {})
    rows.append(
        {
            "schema_version": "lane01_dependency_state_v1",
            "route_id": ROUTE_ID,
            "dependency_id": "lane02_selected_denominator_counts",
            "path": "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/LANE02_PORTFOLIO_REPLAY_STRESS_SUMMARY.json",
            "exists": bool(lane02),
            "dependency_state": "present_consumed" if lane02 else "missing",
            "selected_surface_rows": lane02.get("selected_surface_rows"),
            "accepted_rows": ((lane02.get("stats") or {}).get("accepted_rows")),
            "proxy_expectancy_r": ((lane02.get("stats") or {}).get("accepted_expectancy_r")),
        }
    )
    return rows


def build_comparison(inputs: dict[str, Any]) -> dict[str, Any]:
    repo_cov = inputs.get("vps_coverage", {}).get("timeframe_coverage_by_symbol", {})
    mt5_cov = {symbol: sorted(tfs) for symbol, tfs in normalize_mt5_coverage(inputs.get("mt5_cache_summary", {}).get("timeframe_coverage_by_symbol", {})).items()}
    lane02 = inputs.get("lane02_summary", {})
    lane08 = inputs.get("lane08_summary", {})
    lane06 = inputs.get("lane06_summary", {})
    return {
        "schema_version": "lane01_repo_vs_mt5_cache_comparison_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "active_symbols": ACTIVE_SYMBOLS,
        "repo_timeframe_coverage_by_symbol": {symbol: repo_cov.get(symbol, []) for symbol in ACTIVE_SYMBOLS},
        "mt5_cache_timeframe_coverage_by_symbol": {symbol: mt5_cov.get(symbol, []) for symbol in ACTIVE_SYMBOLS},
        "mt5_repo_comparison_input": inputs.get("mt5_repo_comparison", {}),
        "mt5_archive_manifest": inputs.get("mt5_archive_manifest", {}),
        "broker_readonly_export_evidence": {
            "lane06_summary": lane06,
            "snapshot_symbols": sorted((inputs.get("lane06_snapshot", {}).get("symbol_info") or {}).keys()),
            "source_use_decision": "sparse_friday_broker_truth_only_full_24_symbol_export_still_required",
        },
        "selected_denominator_reference": {
            "lane02_selected_surface_rows": lane02.get("selected_surface_rows"),
            "lane02_accepted_rows": ((lane02.get("stats") or {}).get("accepted_rows")),
            "lane02_proxy_expectancy_r": ((lane02.get("stats") or {}).get("accepted_expectancy_r")),
            "lane08_input_rows": lane08.get("input_rows"),
            "lane08_portfolio_ready_rows": lane08.get("portfolio_ready_rows"),
            "lane08_best_policy_by_denominator": lane08.get("best_policy_by_denominator"),
        },
    }


def build_downstream_contracts(gap_rows: list[dict[str, Any]], inputs: dict[str, Any]) -> dict[str, Any]:
    gap_counts = Counter(row["gap_family"] for row in gap_rows)
    common = {
        "source_inventory": f"research/operations/{ROUTE_ID}/DATA_SOURCE_INVENTORY.jsonl",
        "source_authority_map": f"research/operations/{ROUTE_ID}/SOURCE_AUTHORITY_MAP.json",
        "source_gap_ledger": f"research/operations/{ROUTE_ID}/SOURCE_GAP_LEDGER.jsonl",
        "parser_check_results": f"research/operations/{ROUTE_ID}/PARSER_CHECK_RESULTS.jsonl",
        "runtime_effect_boundary": "data/source-authority artifacts only; no live runtime, broker operation, config, risk, selector, safety, or execution activation change",
    }
    lane_contracts = {
        "historical_microscope": {
            **common,
            "must_use_source_classes": ["repo_market_history", "m1_forward_capture", "tick_bid_ask_history", "selected_denominator_replay", "friday_microscope_ledger"],
            "allowed_result_scope": "source-bound replay/microscope rows only",
            "blocked_until_repaired": ["non-generatable broker intent/order lifecycle truth unless already captured"],
            "source_gap_families_to_consume": ["market_history_timeframe_coverage", "selected_denominator_m1_availability_status", "selected_denominator_tick_availability_status"],
        },
        "feature_store_v1": {
            **common,
            "must_use_source_classes": ["selected_denominator_replay", "runtime_shadow_log", "selected_cell_risk_source_bridge", "repo_market_history"],
            "required_keys": ["canonical_symbol", "timeframe", "time_coverage_start", "source_class", "authority_level", "parser_id"],
            "source_gap_families_to_consume": ["broker_specs", "spread", "stops_freeze", "symbol_aliases", "session_schedules"],
        },
        "label_store_v1": {
            **common,
            "must_use_source_classes": ["broker_readonly_snapshot", "selected_denominator_replay", "execution_policy_replay_projection"],
            "label_authority_order": ["broker_real_truth", "strict_tick_projection", "m15_proxy_replay"],
            "source_gap_families_to_consume": ["account_deal_order_position_history", "cost_fields", "commissions", "swaps"],
        },
        "broker_truth_cost_calibration": {
            **common,
            "must_use_source_classes": ["broker_readonly_snapshot", "broker_lifecycle_truth", "local_mt5_cache_manifest"],
            "authoritative_use_requires": "full read-only orders/deals/positions/symbol_info/session/cost export for all active symbols",
            "source_gap_families_to_consume": ["broker_specs", "account_deal_order_position_history", "spread", "stops_freeze", "swaps", "commissions", "session_schedules"],
        },
        "digital_twin_replay_engine": {
            **common,
            "must_use_source_classes": ["selected_denominator_replay", "tick_bid_ask_history", "m1_forward_capture", "broker_readonly_snapshot", "runtime_shadow_log"],
            "source_gap_families_to_consume": ["selected_denominator_ordered_path_status", "selected_denominator_tick_availability_status", "broker_specs", "account_deal_order_position_history"],
        },
        "meta_selector_v2": {
            **common,
            "must_use_source_classes": ["selected_denominator_replay", "selected_cell_risk_source_bridge", "execution_policy_replay_projection"],
            "result_boundary": "discovery/stress until no-leak partitions and validation lanes accept",
            "source_gap_families_to_consume": ["selected_denominator_source_quality_status", "selected_denominator_cost_status", "selected_denominator_missing_field_note"],
        },
        "portfolio_scheduler_v2": {
            **common,
            "must_use_source_classes": ["broker_readonly_snapshot", "selected_denominator_replay", "runtime_shadow_log"],
            "authoritative_use_requires": "account/equity/deal/order/position lifecycle export and source-bound risk release timing",
            "source_gap_families_to_consume": ["account_deal_order_position_history", "selected_denominator_partial_release_source_status"],
        },
        "execution_policy_engine_v2": {
            **common,
            "must_use_source_classes": ["execution_policy_replay_projection", "tick_bid_ask_history", "broker_readonly_snapshot"],
            "source_gap_families_to_consume": ["selected_denominator_tick_availability_status", "stops_freeze", "spread", "cost_fields"],
        },
        "ml_dataset_baseline_lab": {
            **common,
            "must_use_source_classes": ["repo_market_history", "selected_denominator_replay", "execution_policy_replay_projection", "runtime_shadow_log"],
            "no_leak_dependency_state": "absolute lane02 route absent in this run; consume dependency-state ledger before training",
            "source_gap_families_to_consume": sorted(gap_counts),
        },
        "daily_learning_repair_companion": {
            **common,
            "must_use_source_classes": ["runtime_shadow_log", "hot_runtime_state", "broker_readonly_snapshot", "local_mt5_cache_manifest"],
            "source_gap_families_to_consume": ["broker_specs", "account_deal_order_position_history", "symbol_aliases"],
        },
        "command_center_production_dossier": {
            **common,
            "must_use_source_classes": ["runtime_shadow_log", "broker_readonly_snapshot", "route_summary", "selected_denominator_replay"],
            "production_boundary": "dossier only; no hidden activation",
            "source_gap_families_to_consume": sorted(gap_counts),
        },
    }
    return {
        "schema_version": "lane01_downstream_source_contracts_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "contracts": lane_contracts,
        "gap_family_counts": dict(gap_counts),
        "source_use_state": "contracts_bind_downstream_lanes_to_inventory_authority_and_gap_ledgers",
    }


def build_result_use_status(inputs: dict[str, Any]) -> dict[str, Any]:
    lane02_stats = (inputs.get("lane02_summary", {}).get("stats") or {})
    lane08_best = inputs.get("lane08_summary", {}).get("best_policy_by_denominator", {})
    return {
        "schema_version": "lane01_result_use_status_v1",
        "route_id": ROUTE_ID,
        "lane01_owns_r_scoring": False,
        "result_scope": "source_authority_inventory_and_contracts",
        "exact_r_status": "not_owned_by_lane01",
        "proxy_r_status": "consumed_as_source_metadata_from_lane02_lane08_not_recomputed_as_lane01_result",
        "expectancy_fields_consumed": {
            "lane02_selected_surface_rows": inputs.get("lane02_summary", {}).get("selected_surface_rows"),
            "lane02_accepted_rows": lane02_stats.get("accepted_rows"),
            "lane02_accepted_expectancy_r": lane02_stats.get("accepted_expectancy_r"),
            "lane02_accepted_gross_r_sum": lane02_stats.get("accepted_gross_r_sum"),
            "lane08_best_policy_by_denominator": lane08_best,
        },
        "source_use_state": "result_numbers_are_downstream_source_inventory_metadata_not_production_change_claims",
        "runtime_effect_boundary": "no live behavior change",
    }


def build_branch_decisions() -> list[dict[str, Any]]:
    decisions = [
        {
            "decision_id": "implement_lane01_source_authority_builder_verifier",
            "decision": "implemented",
            "reason": "downstream moonshot lanes need deterministic source inventory, authority map, gap ledgers, contracts, and parser checks from disk",
            "runtime_effect_boundary": "route-local research artifacts only",
        },
        {
            "decision_id": "direct_local_broker_server_export",
            "decision": "defer_to_exact_compliant_vps_readonly_export_requirement",
            "reason": "existing VPS/cache preservation route records full broker/server export as compliant VPS requirement; Lane01 consumes local/cache/sparse broker evidence and preserves exact export gaps",
            "runtime_effect_boundary": "no MT5 server session opened by this route",
        },
        {
            "decision_id": "paid_vendor_orderflow_depth_sources",
            "decision": "excluded_by_prompt",
            "reason": "Lane01 forbids Sierra, Databento, orderflow/depth API work and paid/vendor calls",
            "runtime_effect_boundary": "no paid or external source call",
        },
        {
            "decision_id": "downstream_use",
            "decision": "allow_downstream_lanes_to_consume_lane01_artifacts_as_source_authority_input",
            "reason": "inventory/gap/contracts/parser checks are material data products with verifier coverage",
            "runtime_effect_boundary": "source authority only; no production activation",
        },
    ]
    return [
        {
            "schema_version": "lane01_branch_decision_v1",
            "route_id": ROUTE_ID,
            **row,
        }
        for row in decisions
    ]


def build_context_anchor(inputs: dict[str, Any]) -> dict[str, Any]:
    master_path = REPO_ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
    master_state = "present_consumed" if master_path.exists() else "absent_recorded_in_DEPENDENCY_STATE_LEDGER"
    return {
        "schema_version": "lane01_context_anchor_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "git": git_info(),
        "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE01_DATA_UNIVERSE_SOURCE_AUTHORITY_GOAL_PROMPT_2026-06-01.md",
        "starter": "research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE01_DATA_UNIVERSE_SOURCE_AUTHORITY_STARTER_2026-06-01.txt",
        "context_files_read_after_preflight": [
            ".context/LIVE_STATE.md",
            ".context/00_core/current_vnext_system_map.md",
            ".context/00_core/current_repo_reading_order.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/vnext_absolute_moonshot_vision_and_limitations.md",
            "research/science_program_2026_05/04_goal_prompts/VNEXT_ABSOLUTE_MOONSHOT_MASTER_ORCHESTRATION_GOAL_PROMPT_2026-06-01.md",
            "research/science_program_2026_05/04_goal_prompts/VNEXT_ABSOLUTE_MOONSHOT_PROGRAM_LAUNCH_ORDER_2026-06-01.md",
        ],
        "lane_posture": "constructive data/source-authority builder with curiosity, active creativity, no arbitrary top-N, and proof-or-impossibility inside source-authority evidence class",
        "master_route_state": master_state,
        "source_boundary": "repo/local/MT5-cache/route/read-only broker evidence only; no live operation, paid vendor, credential, remote, config/risk/execution/safety/selector activation",
        "latest_inputs_consumed": {
            "lane02_selected_surface_rows": inputs.get("lane02_summary", {}).get("selected_surface_rows"),
            "lane06_source_completeness_status": inputs.get("lane06_summary", {}).get("source_completeness_status"),
            "mt5_archive_sha256": inputs.get("mt5_archive_manifest", {}).get("archive_sha256"),
        },
        "resume_instruction": "Regenerate LIVE_STATE, reread prompt/starter/doctrine/this anchor, then rerun builder and verifier before claiming completion.",
    }


def build_completion_audit(
    inventory: list[dict[str, Any]],
    parser_results: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    dependency_by_id = {row.get("dependency_id"): row for row in dependencies}
    master_row = dependency_by_id.get("absolute_master_route") or {}
    master_coverage = (
        "absolute master route present and consumed"
        if master_row.get("exists") is True
        else "absolute master route absent; dependency row recorded"
    )
    return {
        "schema_version": "lane01_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "can_mark_goal_complete": False,
        "verification_ok": False,
        "scoped_commit_status": "pending",
        "instruction_coverage": {
            "mandatory_preflight_completed": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "moonshot_vision_read": True,
            "starter_and_controlling_prompt_read": True,
            "master_route_when_present_or_dependency_state_when_absent": master_coverage,
            "builder_posture_applied": "constructive_source_authority_builder",
            "anti_boxing_actions": [
                "repo data, exports, shadow logs, pipeline state, knowledge base, context, code/test contracts scanned",
                "next-level lanes, Friday microscope, live companion, activation routes, MT5 cache preservation, VPS preservation, external archive, and prior science worktree scanned",
                "local repo coverage compared against preserved MT5 cache and sparse broker read-only snapshot",
            ],
            "outside_current_edge_sources_considered": [
                "local MT5 native cache/archive",
                "prior science worktree",
                "selected denominator replay",
                "strict tick execution policy subset",
                "broker lifecycle truth snapshot",
                "forward live companion/runtime logs",
            ],
            "proof_or_impossibility_stop_condition": "all executable filesystem reads and parser checks in source-authority class completed; broker/server full export reduced to exact compliant VPS read-only export requirement; paid/vendor/orderflow sources excluded by prompt",
        },
        "artifact_counts": {
            "inventory_rows": len(inventory),
            "parser_check_rows": len(parser_results),
            "gap_rows": len(gaps),
            "dependency_rows": len(dependencies),
            "inventory_bytes": sum(row.get("bytes") or 0 for row in inventory),
        },
        "required_outputs": {
            "inventory_ledgers": "DATA_SOURCE_INVENTORY.jsonl",
            "source_authority_map": "SOURCE_AUTHORITY_MAP.json",
            "gap_ledgers": "SOURCE_GAP_LEDGER.jsonl",
            "downstream_contracts": "DOWNSTREAM_SOURCE_CONTRACTS.json",
            "manifest": "OUTPUT_MANIFEST.json",
            "verifier": "verify_vnext_moonshot_lane01_data_universe_source_authority.py",
            "focused_tests": "test_vnext_moonshot_lane01_data_universe_source_authority.py",
            "source_capture_decisions": "SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
            "branch_decisions": "BRANCH_DECISION_LEDGER.jsonl",
            "result_use_status": "RESULT_USE_STATUS.json",
        },
        "source_use_state": "complete_source_authority_artifacts_pending_verifier_and_scoped_commit",
        "result_use_status": "Lane01 does not own exact/proxy R scoring; consumed Lane02/Lane08 expectancy metadata as source inventory fields.",
        "runtime_effect_boundary": "no live broker operation, no order/deal/position mutation, no paid API/vendor call, no credential/remote action, no production activation, no prompt/config/risk/execution/safety/canary/selector change",
        "lane02_reference": {
            "selected_surface_rows": inputs.get("lane02_summary", {}).get("selected_surface_rows"),
            "accepted_expectancy_r": (inputs.get("lane02_summary", {}).get("stats") or {}).get("accepted_expectancy_r"),
        },
    }


def refresh_manifest() -> dict[str, Any]:
    files = []
    for path in sorted(ROUTE_DIR.rglob("*"), key=lambda p: str(p).lower()):
        if not path.is_file() or should_skip(path):
            continue
        entry = {
            "path": rel_path(path),
            "bytes": path.stat().st_size,
            "hash_status": "sha256",
            "sha256": None,
        }
        if path.name == "OUTPUT_MANIFEST.json":
            entry["hash_status"] = "self_manifest_no_hash"
        else:
            entry["sha256"] = file_sha256(path)
        files.append(entry)
    manifest = {
        "schema_version": "lane01_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "route_dir": rel_path(ROUTE_DIR),
        "files": files,
    }
    write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", manifest)
    return manifest


def main() -> None:
    inputs = load_route_inputs()
    inventory, parser_results, acquisition_rows = scan_inventory()
    source_authority = summarize_inventory(inventory)
    gaps, source_decisions = build_gap_ledgers(inputs)
    dependencies = build_dependency_rows(inputs)
    comparison = build_comparison(inputs)
    contracts = build_downstream_contracts(gaps, inputs)
    result_use_status = build_result_use_status(inputs)
    branch_decisions = build_branch_decisions()
    context_anchor = build_context_anchor(inputs)
    completion_audit = build_completion_audit(inventory, parser_results, gaps, dependencies, inputs)

    write_jsonl(ROUTE_DIR / "DATA_SOURCE_INVENTORY.jsonl", inventory)
    write_jsonl(ROUTE_DIR / "PARSER_CHECK_RESULTS.jsonl", parser_results)
    write_jsonl(ROUTE_DIR / "SOURCE_ACQUISITION_ATTEMPT_LEDGER.jsonl", acquisition_rows)
    write_json(ROUTE_DIR / "SOURCE_AUTHORITY_MAP.json", source_authority)
    write_jsonl(ROUTE_DIR / "SOURCE_GAP_LEDGER.jsonl", gaps)
    write_jsonl(ROUTE_DIR / "SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl", source_decisions)
    write_jsonl(ROUTE_DIR / "DEPENDENCY_STATE_LEDGER.jsonl", dependencies)
    write_json(ROUTE_DIR / "LOCAL_REPO_VS_MT5_CACHE_COMPARISON.json", comparison)
    write_json(ROUTE_DIR / "DOWNSTREAM_SOURCE_CONTRACTS.json", contracts)
    write_json(ROUTE_DIR / "PARSER_CHECKER_REGISTRY.json", {"schema_version": "lane01_parser_checker_registry_v1", "route_id": ROUTE_ID, "parsers": PARSER_REGISTRY})
    write_json(ROUTE_DIR / "RESULT_USE_STATUS.json", result_use_status)
    write_jsonl(ROUTE_DIR / "BRANCH_DECISION_LEDGER.jsonl", branch_decisions)
    write_json(ROUTE_DIR / "ROUTE_CONTEXT_ANCHOR.json", context_anchor)
    write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", completion_audit)
    manifest = refresh_manifest()
    print(json.dumps({"route_id": ROUTE_ID, "inventory_rows": len(inventory), "gap_rows": len(gaps), "manifest_files": len(manifest["files"])}, sort_keys=True))


if __name__ == "__main__":
    main()
