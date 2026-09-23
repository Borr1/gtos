"""Build vNext moonshot Lane05 Feature Store V1.

Research-only route builder. It streams source-bound upstream ledgers and writes
versioned, no-leak feature vectors plus coverage, source gap, manifest, and
downstream contracts. It does not touch runtime config, MT5, credentials, or
live broker state.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
SCHEMA_VERSION = "lane05_feature_store_v1"
FEATURE_SET_ID = "vnext_moonshot_feature_store_v1_2026_06_01"
RUNTIME_EFFECT_BOUNDARY = "offline_feature_store_artifacts_only_no_live_behavior_change"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]

LANE01_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = REPO_ROOT / "research/operations/vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
SELECTED_CELL_DIR = REPO_ROOT / "research/operations/vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31"
SCHEDULER_DIR = REPO_ROOT / "research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31"

LANE03_CANONICAL_CANDIDATE = LANE03_DIR / "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz"
LANE03_MANIFEST = LANE03_DIR / "LANE03_OUTPUT_MANIFEST.json"
LANE04_TIMELINE = LANE04_DIR / "LANE04_ROW_TIMELINE_LEDGER.jsonl"
LANE04_STRICT_TICK = LANE04_DIR / "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl"
LANE04_MANIFEST = LANE04_DIR / "LANE04_OUTPUT_MANIFEST.json"
LANE01_SOURCE_AUTHORITY = LANE01_DIR / "SOURCE_AUTHORITY_MAP.json"
LANE01_DOWNSTREAM_CONTRACTS = LANE01_DIR / "DOWNSTREAM_SOURCE_CONTRACTS.json"
LANE01_SOURCE_GAPS = LANE01_DIR / "SOURCE_GAP_LEDGER.jsonl"
LANE02_DOWNSTREAM_CONTRACT = LANE02_DIR / "LANE02_DOWNSTREAM_FIELD_CONTRACT.json"
LANE02_VALIDATOR_SPEC = LANE02_DIR / "LANE02_LEAKAGE_VALIDATOR_SPEC.json"
SELECTED_CELL_LEDGER = SELECTED_CELL_DIR / "LANE04_SELECTED_CELL_RISK_BRIDGE_LEDGER.jsonl"
SCHEDULER_LEDGER = SCHEDULER_DIR / "LANE05_SCHEDULER_LEDGER.jsonl"
REGIME_LEDGER = REPO_ROOT / "shadow_logs/regime_decay_outcome_join.jsonl"
CORRELATION_LEDGER = REPO_ROOT / "shadow_logs/cross_instrument_correlation_decisions.jsonl"
EXTERNAL_FEATURE_ROOT = REPO_ROOT / "data/external/features"

OUT_FEATURE_SCHEMA = ROUTE_DIR / "LANE05_FEATURE_SCHEMA.json"
OUT_TIMELINE_FEATURES = ROUTE_DIR / "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz"
OUT_CANONICAL_FEATURES = ROUTE_DIR / "LANE05_CANONICAL_CANDIDATE_FEATURE_VECTOR_LEDGER.jsonl.gz"
OUT_COVERAGE = ROUTE_DIR / "LANE05_FEATURE_COVERAGE_LEDGER.jsonl"
OUT_SOURCE_COMPLETENESS = ROUTE_DIR / "LANE05_SOURCE_COMPLETENESS_LEDGER.jsonl"
OUT_SOURCE_GAPS = ROUTE_DIR / "LANE05_SOURCE_GAP_LEDGER.jsonl"
OUT_NO_LEAK = ROUTE_DIR / "LANE05_NO_LEAK_VALIDATION_LEDGER.jsonl"
OUT_IMPORTANCE = ROUTE_DIR / "LANE05_FEATURE_IMPORTANCE_READINESS.json"
OUT_DOWNSTREAM = ROUTE_DIR / "LANE05_DOWNSTREAM_CONTRACT.json"
OUT_DEPENDENCY = ROUTE_DIR / "LANE05_DEPENDENCY_STATE_LEDGER.jsonl"
OUT_BRANCH = ROUTE_DIR / "LANE05_BRANCH_DECISION_LEDGER.jsonl"
OUT_RESULT_USE = ROUTE_DIR / "LANE05_RESULT_USE_STATUS.json"
OUT_RUNTIME_BOUNDARY = ROUTE_DIR / "LANE05_RUNTIME_EFFECT_BOUNDARY.json"
OUT_CONTEXT_ANCHOR = ROUTE_DIR / "LANE05_CONTEXT_ANCHOR.md"
OUT_COMPLETION_AUDIT = ROUTE_DIR / "LANE05_COMPLETION_AUDIT.json"
OUT_MANIFEST = ROUTE_DIR / "LANE05_OUTPUT_MANIFEST.json"


FORBIDDEN_FEATURE_TOKENS = (
    "actual_r",
    "broker_actual_r",
    "close_time",
    "closed_at",
    "deal_ticket",
    "exact_r",
    "exit_reason",
    "exit_time",
    "final_outcome",
    "final_r",
    "hit_sl",
    "hit_tp",
    "label_h",
    "mae_r",
    "mfe_r",
    "net_r",
    "path_class",
    "profit_factor",
    "proxy_r",
    "time_to_",
    "win_rate",
)

ACTIVE_DOWNSTREAM_LANES = (
    "label_store",
    "digital_twin",
    "ml_dataset",
    "selector",
    "scheduler",
    "execution_policy",
)


def _load_lane02_module() -> Any:
    path = LANE02_DIR / "vnext_lane02_time_contract.py"
    spec = importlib.util.spec_from_file_location("vnext_lane02_time_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Lane02 time contract: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LANE02 = _load_lane02_module()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def as_posix(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def json_dump_line(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def parse_dt(value: Any) -> datetime | None:
    return LANE02.parse_utc_datetime(value)


def iso_dt(value: Any) -> str | None:
    return LANE02.iso_utc(parse_dt(value))


def minute_key(value: Any) -> str | None:
    dt = parse_dt(value)
    if dt is None:
        return None
    return dt.replace(second=0, microsecond=0).isoformat()


def lower_text(value: Any) -> str:
    return str(value or "").strip().lower()


def normalized_symbol(value: Any) -> str:
    return str(value or "").strip().upper().replace("_CASH", "_cash")


def source_family_from_path(path: Any) -> str:
    text = str(path or "").replace("\\", "/").lower()
    if "lane04_historical_microscope" in text:
        return "lane04_microscope_timeline"
    if "lane03_historical_candidate" in text:
        return "lane03_canonical_candidate"
    if "data/external/features" in text:
        return "external_calendar_macro_feature_snapshot"
    if "shadow_logs" in text:
        return "runtime_shadow_log"
    if "data/mt5" in text or text.endswith("_m15.csv"):
        return "repo_market_history"
    if "vnext_lane04_selected_cell" in text:
        return "selected_cell_risk_source_bridge"
    if "vnext_lane05_runtime_portfolio_scheduler" in text:
        return "portfolio_scheduler_replay_projection"
    return "route_or_source_artifact"


def open_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                yield value


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int | None:
    if not path.exists():
        return None
    opener = gzip.open if path.suffix == ".gz" else open
    count = 0
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for _ in handle:
            count += 1
    return count


def upstream_manifest_hash(path: Path, manifest: dict[str, Any]) -> str | None:
    rel = as_posix(path)
    name = path.name
    for key in ("files", "outputs"):
        for row in manifest.get(key, []) or []:
            row_path = str(row.get("path") or "").replace("\\", "/")
            if row_path == rel or row_path.endswith("/" + name):
                return row.get("sha256")
    return None


def feature(
    name: str,
    namespace: str,
    dtype: str,
    availability_class: str,
    source_family: str,
    *,
    nullable: str = "nullable_with_source_gap_or_missingness_feature",
    leakage_class: str = "feature_store_allowed_asof",
    downstream: Iterable[str] = ACTIVE_DOWNSTREAM_LANES,
    source_use_state: str = "source_bound_if_present_else_row_level_gap",
    dependencies: Iterable[str] = (),
    description: str = "",
) -> dict[str, Any]:
    return {
        "asof_dependency_fields": list(dependencies),
        "availability_class": availability_class,
        "description": description,
        "downstream_eligibility": {lane: lane in downstream for lane in ACTIVE_DOWNSTREAM_LANES},
        "dtype": dtype,
        "feature_name": name,
        "feature_namespace": namespace,
        "feature_source_family": source_family,
        "leakage_class": leakage_class,
        "nullable_policy": nullable,
        "post_outcome_field_excluded": False,
        "source_path": "row.source_path_or_join_source_path",
        "source_use_state": source_use_state,
    }


def feature_schema() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = [
        feature("identity_symbol", "symbol_session_time", "category", "pre_candidate", "lane03_lane04_identity", nullable="required_non_null", dependencies=["symbol"]),
        feature("identity_broker_symbol", "symbol_session_time", "category", "pre_candidate", "lane03_lane04_identity", dependencies=["broker_symbol"]),
        feature("time_candidate_hour_utc", "symbol_session_time", "integer", "candidate_time", "lane02_time_contract", dependencies=["feature_time_utc"]),
        feature("time_candidate_minute_of_day_utc", "symbol_session_time", "integer", "candidate_time", "lane02_time_contract", dependencies=["feature_time_utc"]),
        feature("time_candidate_weekday_utc", "symbol_session_time", "integer", "candidate_time", "lane02_time_contract", dependencies=["feature_time_utc"]),
        feature("time_candidate_month", "symbol_session_time", "category", "candidate_time", "lane02_time_contract", dependencies=["feature_time_utc"]),
        feature("time_is_friday", "symbol_session_time", "boolean", "candidate_time", "lane02_time_contract", dependencies=["feature_time_utc"]),
        feature("time_friday_close_risk", "symbol_session_time", "boolean", "candidate_time", "lane02_time_contract", dependencies=["feature_time_utc", "symbol"]),
        feature("session_bucket", "symbol_session_time", "category", "pre_candidate", "lane02_time_contract", dependencies=["feature_time_utc", "symbol"]),
        feature("session_source_state", "symbol_session_time", "category", "source_metadata", "lane02_time_contract", dependencies=["feature_time_utc", "symbol"]),
        feature("origin_family", "origin_framework_side", "category", "pre_candidate", "lane03_lane04_identity", dependencies=["origin_family"]),
        feature("framework", "origin_framework_side", "category", "pre_candidate", "lane03_lane04_identity", dependencies=["framework"]),
        feature("side", "origin_framework_side", "category", "pre_candidate", "lane03_lane04_identity", dependencies=["side"]),
        feature("mechanism_family", "origin_framework_side", "category", "pre_candidate", "lane03_reconstruction", dependencies=["mechanism_family", "origin_family"]),
        feature("chosen_policy", "origin_framework_side", "category", "pre_order", "lane04_microscope_timeline", dependencies=["chosen_policy"]),
        feature("is_ob_retest", "origin_framework_side", "boolean", "pre_candidate", "lane03_lane04_identity", dependencies=["framework"]),
        feature("is_fvg_fill", "origin_framework_side", "boolean", "pre_candidate", "lane03_lane04_identity", dependencies=["framework"]),
        feature("is_breaker_re_entry", "origin_framework_side", "boolean", "pre_candidate", "lane03_lane04_identity", dependencies=["framework"]),
        feature("is_liquidity_sweep_reclaim", "liquidity_sweep", "boolean", "candidate_time", "lane03_lane04_identity", dependencies=["origin_family", "liquidity_sweep_proxy_state"]),
        feature("liquidity_sweep_proxy_state", "liquidity_sweep", "category", "candidate_time", "lane04_microscope_timeline", dependencies=["liquidity_sweep_proxy_state"]),
        feature("is_displacement_continuation", "displacement", "boolean", "candidate_time", "lane03_lane04_identity", dependencies=["mechanism_family", "origin_family"]),
        feature("is_failed_displacement", "failed_displacement", "boolean", "candidate_time", "lane03_lane04_identity", dependencies=["mechanism_family", "origin_family"]),
        feature("m15_trend_state_20", "htf_m15_state", "category", "pre_order", "lane04_microscope_timeline", dependencies=["trend_state_20"]),
        feature("m15_volatility_state_14_vs_50", "volatility", "category", "pre_order", "lane04_microscope_timeline", dependencies=["volatility_state_14_vs_50"]),
        feature("m1_availability_status", "m1_state", "category", "source_metadata", "lane04_microscope_timeline", dependencies=["m1_availability_status"]),
        feature("m1_entry_minute_available", "m1_state", "boolean", "source_metadata", "lane04_microscope_timeline", dependencies=["m1_availability_status"]),
        feature("tick_availability_status", "tick_state", "category", "source_metadata", "lane04_microscope_timeline", dependencies=["tick_availability_status"]),
        feature("strict_tick_available", "tick_state", "boolean", "source_metadata", "lane04_strict_tick_timeline", dependencies=["strict_tick_event_status"]),
        feature("strict_tick_entry_spread_r", "spread_cost", "number", "pre_order", "lane04_strict_tick_timeline", dependencies=["strict_tick_metrics.entry_spread_r"]),
        feature("strict_tick_risk_price_distance", "broker_feasibility", "number", "pre_order", "lane04_strict_tick_timeline", dependencies=["strict_tick_metrics.risk_price_distance"]),
        feature("cost_status", "spread_cost", "category", "source_metadata", "lane04_microscope_timeline", dependencies=["cost_status"]),
        feature("spread_r_bucket", "spread_cost", "category", "source_metadata", "lane04_microscope_timeline", dependencies=["spread_r_bucket"]),
        feature("cost_source_missing", "spread_cost", "boolean", "source_metadata", "lane01_source_gap_contract", dependencies=["cost_status", "source_gaps"]),
        feature("source_window_complete", "source_completeness", "boolean", "source_metadata", "lane04_microscope_timeline", dependencies=["source_window_complete"]),
        feature("source_quality_status", "source_completeness", "category", "source_metadata", "lane04_microscope_timeline", dependencies=["source_quality_status"]),
        feature("source_use_state", "source_completeness", "category", "source_metadata", "lane01_lane03_lane04", dependencies=["source_use_state"]),
        feature("source_family", "source_completeness", "category", "source_metadata", "lane01_source_authority", dependencies=["source_path"]),
        feature("canonical_source_path_state", "source_completeness", "category", "source_metadata", "lane03_reconstruction", dependencies=["first_source_path", "source_path"]),
        feature("candidate_time_known", "source_completeness", "boolean", "source_metadata", "lane03_reconstruction", dependencies=["candidate_time_utc", "source_time_utc"]),
        feature("side_known", "source_completeness", "boolean", "source_metadata", "lane03_reconstruction", dependencies=["side"]),
        feature("symbol_known", "source_completeness", "boolean", "source_metadata", "lane03_reconstruction", dependencies=["symbol"]),
        feature("selected_cell_risk_join_state", "selected_cell_risk_proof", "category", "pre_order", "selected_cell_risk_source_bridge", dependencies=["symbol", "side", "origin_family"]),
        feature("selected_cell_risk_cell_id", "selected_cell_risk_proof", "category", "pre_order", "selected_cell_risk_source_bridge", dependencies=["selected_cell_risk_source_row_identity.risk_cell_id"]),
        feature("selected_cell_effective_risk_pct", "selected_cell_risk_proof", "number", "pre_order", "selected_cell_risk_source_bridge", dependencies=["selected_cell_risk_source_row_identity.effective_risk_per_trade_pct"]),
        feature("portfolio_scheduler_join_state", "portfolio_state", "category", "pre_order", "lane05_scheduler_replay", dependencies=["symbol", "feature_time_utc"]),
        feature("portfolio_open_risk_before", "portfolio_state", "number", "pre_order", "lane05_scheduler_replay", dependencies=["open_risk_before"]),
        feature("portfolio_open_risk_ceiling", "portfolio_state", "number", "pre_order", "lane05_scheduler_replay", dependencies=["portfolio_open_risk_ceiling"]),
        feature("broker_feasibility_state", "broker_feasibility", "category", "source_metadata", "lane01_source_gap_contract", dependencies=["source_gaps", "broker_geometry_pass"]),
        feature("correlation_cluster_join_state", "correlation_cluster", "category", "pre_order", "runtime_shadow_log", dependencies=["symbol", "feature_time_utc"]),
        feature("correlation_cluster_size", "correlation_cluster", "integer", "pre_order", "runtime_shadow_log", dependencies=["cluster_size"]),
        feature("correlation_risk_multiplier", "correlation_cluster", "number", "pre_order", "runtime_shadow_log", dependencies=["risk_multiplier"]),
        feature("regime_join_state", "regime", "category", "pre_order", "runtime_shadow_log", dependencies=["symbol", "feature_time_utc"]),
        feature("regime_h4_state", "regime", "category", "pre_order", "runtime_shadow_log", dependencies=["regime_context.regime"]),
        feature("regime_h4_direction", "regime", "category", "pre_order", "runtime_shadow_log", dependencies=["regime_context.raw_features.h4_direction"]),
        feature("regime_h4_score", "regime", "number", "pre_order", "runtime_shadow_log", dependencies=["regime_context.raw_features.score"]),
        feature("external_calendar_macro_join_state", "news_calendar", "category", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["symbol", "feature_time_utc"]),
        feature("macro_fred_available", "news_calendar", "boolean", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["fred__available"]),
        feature("macro_fred_vixcls_value", "news_calendar", "number", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["fred__VIXCLS__value", "fred__VIXCLS__published_at_utc"]),
        feature("macro_fred_dgs10_value", "news_calendar", "number", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["fred__DGS10__value", "fred__DGS10__published_at_utc"]),
        feature("macro_fred_dgs2_value", "news_calendar", "number", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["fred__DGS2__value", "fred__DGS2__published_at_utc"]),
        feature("macro_fred_dollar_index_value", "news_calendar", "number", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["fred__DTWEXBGS__value", "fred__DTWEXBGS__published_at_utc"]),
        feature("macro_gold_volatility_value", "news_calendar", "number", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["fred__GVZCLS__value", "fred__GVZCLS__published_at_utc"]),
        feature("lbma_fix_window_30m", "news_calendar", "boolean", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["lbma_calendar__in_fix_window_30m"]),
        feature("cftc_cot_available", "news_calendar", "boolean", "pre_order", "external_calendar_macro_feature_snapshot", dependencies=["cftc_cot__available"]),
        feature("stale_label_broker_real_absent_flag", "stale_label_flags", "boolean", "source_metadata", "lane01_lane04_source_gap_contract", dependencies=["cost_status", "source_gaps"], description="Required stale-label flag; indicates broker-real labels are absent and downstream label store must use proxy/source-bound labels only."),
        feature("stale_label_path_proxy_flag", "stale_label_flags", "boolean", "source_metadata", "lane04_microscope_timeline", dependencies=["source_use_state"], description="Required stale-label flag; indicates row uses replay/proxy path source rather than broker-real path truth."),
    ]
    return items


FEATURE_NAMES = tuple(item["feature_name"] for item in feature_schema())
FEATURE_BY_NAME = {item["feature_name"]: item for item in feature_schema()}


def validate_feature_schema_rows(schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    allowed_availability = {"pre_candidate", "candidate_time", "pre_order", "source_metadata"}
    for spec in schema:
        name = spec["feature_name"]
        lower = name.lower()
        token_hits = [token for token in FORBIDDEN_FEATURE_TOKENS if token in lower]
        # These two names are explicit prompt-required source-completeness flags, not labels.
        token_hits = [hit for hit in token_hits if not (hit == "label_h" and name.startswith("stale_label_"))]
        availability = spec["availability_class"]
        rows.append(
            {
                "availability_class": availability,
                "feature_name": name,
                "forbidden_token_hits": token_hits,
                "lane02_classification": LANE02.classify_field(name),
                "no_leak_status": "pass" if not token_hits and availability in allowed_availability else "fail",
                "route_id": ROUTE_ID,
                "schema_version": "lane05_no_leak_validation_v1",
                "validation_scope": "feature_schema",
            }
        )
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json_dump_line(row))
            count += 1
    return count


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=1) as handle:
        for row in rows:
            handle.write(json_dump_line(row))
            count += 1
    return count


def load_strict_tick_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in open_jsonl(LANE04_STRICT_TICK):
        candidate_id = row.get("candidate_id")
        if candidate_id:
            index[str(candidate_id)] = row
    return index


def load_selected_cell_index() -> dict[tuple[str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in open_jsonl(SELECTED_CELL_LEDGER):
        identity = row.get("selected_cell_risk_source_row_identity") or {}
        symbol = normalized_symbol(identity.get("symbol") or row.get("symbol"))
        side = str(identity.get("side") or row.get("side") or "").upper()
        family = str(identity.get("family") or row.get("origin_family") or row.get("framework") or "").lower()
        if symbol and side and family:
            index.setdefault((symbol, side, family), row)
    return index


def load_scheduler_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in open_jsonl(SCHEDULER_LEDGER):
        symbol = normalized_symbol(row.get("symbol"))
        key_time = minute_key(row.get("decision_time_utc") or row.get("timestamp_utc"))
        if symbol and key_time:
            index[(symbol, key_time)] = row
    return index


def load_correlation_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in open_jsonl(CORRELATION_LEDGER):
        symbol = normalized_symbol(row.get("candidate_symbol") or row.get("symbol"))
        key_time = minute_key(row.get("timestamp_utc"))
        if symbol and key_time:
            index.setdefault((symbol, key_time), row)
    return index


def load_regime_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in open_jsonl(REGIME_LEDGER):
        symbol = normalized_symbol(row.get("symbol"))
        key_time = minute_key(row.get("decision_time_utc"))
        if symbol and key_time:
            index[(symbol, key_time)] = row
    return index


def symbol_external_dirs(symbol: str) -> list[str]:
    symbol = normalized_symbol(symbol)
    candidates = [symbol, symbol.replace("_cash", "_CASH"), symbol.replace("_CASH", "_cash")]
    return list(dict.fromkeys(candidates))


def load_external_feature_index() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, int]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for path in EXTERNAL_FEATURE_ROOT.glob("*/phase3_m15_candidate_gap_external_v1_*.jsonl"):
        for row in open_jsonl(path):
            symbol = normalized_symbol(row.get("symbol") or row.get("file_symbol") or path.parent.name)
            bar_time = iso_dt(row.get("bar_time_utc"))
            close_time = iso_dt(row.get("candle_close_utc"))
            if symbol and bar_time:
                row["_lane05_source_path"] = as_posix(path)
                index[(symbol, bar_time)] = row
                counts[symbol] += 1
            if symbol and close_time:
                row["_lane05_source_path"] = as_posix(path)
                index.setdefault((symbol, close_time), row)
    return index, dict(counts)


def load_lane01_gap_index() -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in open_jsonl(LANE01_SOURCE_GAPS):
        symbol = normalized_symbol(row.get("symbol"))
        family = str(row.get("gap_family") or "")
        if symbol and family:
            index[(symbol, family)] = row
    return index


def source_gap(
    code: str,
    family: str,
    reason: str,
    requirement: str,
    *,
    source_path: str | None = None,
    severity: str = "source_gap",
) -> dict[str, Any]:
    return {
        "code": code,
        "field_family": family,
        "reason": reason,
        "repair_requirement": requirement,
        "severity": severity,
        "source_path": source_path,
    }


def base_time_features(value: Any, symbol: str) -> dict[str, Any]:
    dt = parse_dt(value)
    if dt is None:
        return {
            "time_candidate_hour_utc": None,
            "time_candidate_minute_of_day_utc": None,
            "time_candidate_month": None,
            "time_candidate_weekday_utc": None,
            "time_friday_close_risk": False,
            "time_is_friday": False,
        }
    return {
        "time_candidate_hour_utc": dt.hour,
        "time_candidate_minute_of_day_utc": dt.hour * 60 + dt.minute,
        "time_candidate_month": f"{dt.year:04d}-{dt.month:02d}",
        "time_candidate_weekday_utc": dt.weekday(),
        "time_friday_close_risk": bool(LANE02.is_friday_close_risk(dt, symbol)),
        "time_is_friday": dt.weekday() == 4,
    }


def session_bucket_for(row: dict[str, Any], feature_time: Any) -> tuple[str, str]:
    if row.get("session_bucket"):
        return str(row["session_bucket"]), "source_row_session_bucket"
    if row.get("session"):
        return str(row["session"]), "source_row_session"
    return "unknown_session", "session_absent_in_source_row"


def external_values(row: dict[str, Any], feature_time: Any) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    if not row:
        return (
            {
                "cftc_cot_available": False,
                "external_calendar_macro_join_state": "no_exact_external_calendar_macro_snapshot",
                "lbma_fix_window_30m": None,
                "macro_fred_available": False,
                "macro_fred_dgs10_value": None,
                "macro_fred_dgs2_value": None,
                "macro_fred_dollar_index_value": None,
                "macro_fred_vixcls_value": None,
                "macro_gold_volatility_value": None,
            },
            [
                source_gap(
                    "news_calendar_exact_snapshot_absent",
                    "news_calendar",
                    "no exact data/external/features row joined on symbol and candidate/source time",
                    "source-bound external calendar/news/macro snapshot by active symbol and decision timestamp, with publication-as-of timestamp",
                )
            ],
            "no_exact_external_calendar_macro_snapshot",
        )
    feature_dt = parse_dt(feature_time)
    fields = {
        "macro_fred_vixcls_value": ("fred__VIXCLS__value", "fred__VIXCLS__published_at_utc"),
        "macro_fred_dgs10_value": ("fred__DGS10__value", "fred__DGS10__published_at_utc"),
        "macro_fred_dgs2_value": ("fred__DGS2__value", "fred__DGS2__published_at_utc"),
        "macro_fred_dollar_index_value": ("fred__DTWEXBGS__value", "fred__DTWEXBGS__published_at_utc"),
        "macro_gold_volatility_value": ("fred__GVZCLS__value", "fred__GVZCLS__published_at_utc"),
    }
    values: dict[str, Any] = {
        "cftc_cot_available": bool(row.get("cftc_cot__available") or row.get("cftc_cot__disagg_combined__available")),
        "external_calendar_macro_join_state": "exact_external_snapshot_joined",
        "lbma_fix_window_30m": row.get("lbma_calendar__in_fix_window_30m"),
        "macro_fred_available": bool(row.get("fred__available")),
    }
    gaps: list[dict[str, Any]] = []
    for out_name, (value_key, published_key) in fields.items():
        published = parse_dt(row.get(published_key))
        if feature_dt and published and published <= feature_dt:
            values[out_name] = row.get(value_key)
        elif row.get(value_key) is not None:
            values[out_name] = None
            gaps.append(
                source_gap(
                    f"{out_name}_publication_after_candidate",
                    "news_calendar",
                    f"{published_key} is after candidate/source time or unparseable",
                    "only emit macro feature when publication timestamp is at or before decision/source time",
                    source_path=row.get("_lane05_source_path"),
                )
            )
        else:
            values[out_name] = None
    if gaps:
        values["external_calendar_macro_join_state"] = "snapshot_joined_but_some_publication_asof_invalid"
    return values, gaps, values["external_calendar_macro_join_state"]


def selected_cell_values(
    row: dict[str, Any],
    selected_cell_index: dict[tuple[str, str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    symbol = normalized_symbol(row.get("symbol"))
    side = str(row.get("side") or "").upper()
    families = [
        str(row.get("origin_family") or "").lower(),
        str(row.get("framework") or "").lower().replace("origin_", ""),
        str(row.get("mechanism_family") or "").lower(),
    ]
    match = None
    for family in families:
        if family and (symbol, side, family) in selected_cell_index:
            match = selected_cell_index[(symbol, side, family)]
            break
    if not match:
        return (
            {
                "selected_cell_effective_risk_pct": None,
                "selected_cell_risk_cell_id": None,
                "selected_cell_risk_join_state": "no_exact_or_family_selected_cell_risk_bridge_join",
            },
            [
                source_gap(
                    "selected_cell_risk_exact_row_absent",
                    "selected_cell_risk_proof",
                    "no selected-cell risk row joined by symbol, side, and origin/framework family",
                    "candidate packet must preserve selected_cell_risk_cell_id, source row identity, selected policy, risk pct, and failed dimensions",
                    source_path=as_posix(SELECTED_CELL_LEDGER),
                )
            ],
            "no_exact_or_family_selected_cell_risk_bridge_join",
        )
    identity = match.get("selected_cell_risk_source_row_identity") or {}
    state = "family_level_selected_cell_risk_bridge_joined_not_candidate_exact"
    return (
        {
            "selected_cell_effective_risk_pct": identity.get("effective_risk_per_trade_pct"),
            "selected_cell_risk_cell_id": identity.get("risk_cell_id"),
            "selected_cell_risk_join_state": state,
        },
        [],
        state,
    )


def scheduler_values(
    row: dict[str, Any],
    scheduler_index: dict[tuple[str, str], dict[str, Any]],
    feature_time: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    key = (normalized_symbol(row.get("symbol")), minute_key(feature_time) or "")
    matched = scheduler_index.get(key)
    if not matched:
        return (
            {
                "portfolio_open_risk_before": None,
                "portfolio_open_risk_ceiling": None,
                "portfolio_scheduler_join_state": "no_exact_portfolio_scheduler_state_join",
            },
            [
                source_gap(
                    "portfolio_state_exact_row_absent",
                    "portfolio_state",
                    "no scheduler replay row joined by symbol and decision minute",
                    "account/equity/open/pending/new-risk state snapshot at candidate decision time or replay-as-of scheduler ledger",
                    source_path=as_posix(SCHEDULER_LEDGER),
                )
            ],
            "no_exact_portfolio_scheduler_state_join",
        )
    return (
        {
            "portfolio_open_risk_before": matched.get("open_risk_before"),
            "portfolio_open_risk_ceiling": matched.get("portfolio_open_risk_ceiling"),
            "portfolio_scheduler_join_state": "exact_symbol_minute_scheduler_replay_joined",
        },
        [],
        "exact_symbol_minute_scheduler_replay_joined",
    )


def correlation_values(
    row: dict[str, Any],
    correlation_index: dict[tuple[str, str], dict[str, Any]],
    feature_time: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    key = (normalized_symbol(row.get("symbol")), minute_key(feature_time) or "")
    matched = correlation_index.get(key)
    if not matched:
        return (
            {
                "correlation_cluster_join_state": "no_exact_correlation_cluster_runtime_join",
                "correlation_cluster_size": None,
                "correlation_risk_multiplier": None,
            },
            [
                source_gap(
                    "correlation_cluster_exact_row_absent",
                    "correlation_cluster",
                    "no forward runtime correlation row joined by symbol and decision minute",
                    "as-of correlation cluster snapshot or replayable portfolio correlation state for each candidate",
                    source_path=as_posix(CORRELATION_LEDGER),
                )
            ],
            "no_exact_correlation_cluster_runtime_join",
        )
    return (
        {
            "correlation_cluster_join_state": "exact_symbol_minute_runtime_correlation_joined",
            "correlation_cluster_size": matched.get("cluster_size"),
            "correlation_risk_multiplier": matched.get("risk_multiplier"),
        },
        [],
        "exact_symbol_minute_runtime_correlation_joined",
    )


def regime_values(
    row: dict[str, Any],
    regime_index: dict[tuple[str, str], dict[str, Any]],
    feature_time: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    key = (normalized_symbol(row.get("symbol")), minute_key(feature_time) or "")
    matched = regime_index.get(key)
    if not matched:
        return (
            {
                "regime_h4_direction": None,
                "regime_h4_score": None,
                "regime_h4_state": row.get("trend_state_20"),
                "regime_join_state": "m15_trend_proxy_only_no_exact_h4_regime_join",
            },
            [
                source_gap(
                    "h4_regime_exact_row_absent",
                    "regime",
                    "no exact as-of H4 regime row joined by symbol and decision minute",
                    "as-of regime snapshot keyed by symbol and candidate time with regime timestamp <= decision time",
                    source_path=as_posix(REGIME_LEDGER),
                )
            ],
            "m15_trend_proxy_only_no_exact_h4_regime_join",
        )
    decision_dt = parse_dt(feature_time)
    regime_ctx = matched.get("regime_context") or {}
    regime_ts = parse_dt(regime_ctx.get("regime_ts_utc"))
    if decision_dt and regime_ts and regime_ts <= decision_dt:
        raw = regime_ctx.get("raw_features") or {}
        return (
            {
                "regime_h4_direction": raw.get("h4_direction"),
                "regime_h4_score": raw.get("score"),
                "regime_h4_state": regime_ctx.get("regime"),
                "regime_join_state": "exact_asof_h4_regime_joined",
            },
            [],
            "exact_asof_h4_regime_joined",
        )
    return (
        {
            "regime_h4_direction": None,
            "regime_h4_score": None,
            "regime_h4_state": row.get("trend_state_20"),
            "regime_join_state": "regime_row_found_but_timestamp_after_decision_use_m15_proxy",
        },
        [
            source_gap(
                "h4_regime_timestamp_after_decision",
                "regime",
                "matched regime row timestamp is after candidate decision/source time",
                "emit H4 regime feature only when Lane02 as-of rule proves timestamp is decision-available",
                source_path=as_posix(REGIME_LEDGER),
            )
        ],
        "regime_row_found_but_timestamp_after_decision_use_m15_proxy",
    )


def build_timeline_feature_row(
    row: dict[str, Any],
    *,
    line_number: int,
    source_hash: str | None,
    strict_tick_index: dict[str, dict[str, Any]],
    selected_cell_index: dict[tuple[str, str, str], dict[str, Any]],
    scheduler_index: dict[tuple[str, str], dict[str, Any]],
    correlation_index: dict[tuple[str, str], dict[str, Any]],
    regime_index: dict[tuple[str, str], dict[str, Any]],
    external_index: dict[tuple[str, str], dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    symbol = normalized_symbol(row.get("symbol"))
    feature_time = iso_dt(row.get("source_time_utc") or row.get("entry_time_utc"))
    feature_dt = parse_dt(feature_time)
    session, session_state = session_bucket_for(row, feature_time)
    candidate_id = row.get("candidate_id") or row.get("selected_row_id") or row.get("row_id")
    strict = strict_tick_index.get(str(candidate_id)) if candidate_id else None
    strict_metrics = (strict or {}).get("strict_tick_metrics") or {}
    external, external_gaps, external_state = external_values(external_index.get((symbol, feature_time or "")), feature_time)
    selected, selected_gaps, selected_state = selected_cell_values(row, selected_cell_index)
    scheduler, scheduler_gaps, scheduler_state = scheduler_values(row, scheduler_index, feature_time)
    correlation, correlation_gaps, correlation_state = correlation_values(row, correlation_index, feature_time)
    regime, regime_gaps, regime_state = regime_values(row, regime_index, feature_time)

    framework = str(row.get("framework") or "unknown_framework")
    origin = str(row.get("origin_family") or row.get("framework") or "unknown_origin")
    mechanism = origin
    source_use_state = str(row.get("source_use_state") or "unknown_source_use_state")
    cost_status = str(row.get("cost_status") or "cost_status_absent")
    tick_status = str(row.get("tick_availability_status") or "tick_status_absent")
    m1_status = str(row.get("m1_availability_status") or "m1_status_absent")
    source_window_complete = row.get("source_window_complete")
    strict_entry_spread = strict_metrics.get("entry_spread_r")

    features: dict[str, Any] = {
        "broker_feasibility_state": "broker_cost_lifecycle_missing" if "missing" in cost_status else "broker_cost_lifecycle_source_present",
        "candidate_time_known": feature_time is not None,
        "canonical_source_path_state": "source_path_present" if row.get("source_path") else "source_path_absent",
        "chosen_policy": row.get("chosen_policy"),
        "cost_source_missing": "missing" in cost_status or row.get("cost_r") is None,
        "cost_status": cost_status,
        "framework": framework,
        "identity_broker_symbol": row.get("broker_symbol") or symbol,
        "identity_symbol": symbol,
        "is_breaker_re_entry": lower_text(framework) == "breaker_re_entry",
        "is_displacement_continuation": "displacement" in lower_text(origin) and "failed" not in lower_text(origin),
        "is_failed_displacement": "failed_displacement" in lower_text(origin) or "failed displacement" in lower_text(origin),
        "is_fvg_fill": lower_text(framework) == "fvg_fill",
        "is_liquidity_sweep_reclaim": "liquidity_sweep" in lower_text(origin) or "swept" in lower_text(row.get("liquidity_sweep_proxy_state")),
        "is_ob_retest": lower_text(framework) == "ob_retest",
        "liquidity_sweep_proxy_state": row.get("liquidity_sweep_proxy_state"),
        "m15_trend_state_20": row.get("trend_state_20"),
        "m15_volatility_state_14_vs_50": row.get("volatility_state_14_vs_50"),
        "m1_availability_status": m1_status,
        "m1_entry_minute_available": m1_status == "local_m1_bar_available_for_entry_minute",
        "mechanism_family": mechanism,
        "origin_family": origin,
        "session_bucket": session,
        "session_source_state": session_state,
        "side": str(row.get("side") or "unknown_side").upper(),
        "side_known": str(row.get("side") or "").lower() not in {"", "unknown", "unknown_side"},
        "source_family": source_family_from_path(row.get("source_path")),
        "source_quality_status": row.get("source_quality_status"),
        "source_use_state": source_use_state,
        "source_window_complete": source_window_complete,
        "spread_r_bucket": row.get("spread_r_bucket"),
        "stale_label_broker_real_absent_flag": True,
        "stale_label_path_proxy_flag": "proxy" in source_use_state or "m15" in source_use_state or "replay" in source_use_state,
        "strict_tick_available": strict is not None,
        "strict_tick_entry_spread_r": strict_entry_spread,
        "strict_tick_risk_price_distance": strict_metrics.get("risk_price_distance"),
        "symbol_known": symbol not in {"", "UNKNOWN"},
        "tick_availability_status": tick_status,
        **base_time_features(feature_time, symbol),
        **external,
        **selected,
        **scheduler,
        **correlation,
        **regime,
    }

    gaps: list[dict[str, Any]] = []
    if m1_status != "local_m1_bar_available_for_entry_minute":
        gaps.append(
            source_gap(
                "m1_entry_minute_not_exact",
                "m1_state",
                m1_status,
                "deterministic M1 export/parser coverage for candidate symbol and entry/source minute",
            )
        )
    if strict is None:
        gaps.append(
            source_gap(
                "strict_tick_timeline_not_joined",
                "tick_state",
                tick_status,
                "ordered bid/ask tick replay or exact tick snapshot at candidate entry/source time",
                source_path=as_posix(LANE04_STRICT_TICK),
            )
        )
    if features["cost_source_missing"]:
        gaps.append(
            source_gap(
                "broker_cost_lifecycle_missing",
                "spread_cost",
                cost_status,
                "broker deal/order lifecycle capture with commission, swap, spread, slippage, fee, and net drag R",
                source_path=as_posix(LANE01_SOURCE_GAPS),
            )
        )
    if not row.get("source_window_complete", True):
        gaps.append(
            source_gap(
                "source_window_incomplete",
                "source_completeness",
                "source_window_complete_false",
                "source window extension or row exclusion rule for downstream ML/replay partitioning",
            )
        )
    gaps.extend(external_gaps)
    gaps.extend(selected_gaps)
    gaps.extend(scheduler_gaps)
    gaps.extend(correlation_gaps)
    gaps.extend(regime_gaps)

    key = LANE02.canonical_key(
        {
            "broker_symbol": row.get("broker_symbol") or symbol,
            "candidate_time_utc": feature_time,
            "framework": framework,
            "origin_family": origin,
            "side": features["side"],
            "source_row_id": row.get("row_id") or row.get("selected_row_id") or candidate_id,
            "symbol": symbol,
        },
        route_id=ROUTE_ID,
        source_path=as_posix(LANE04_TIMELINE),
    )

    return {
        "asof_dependency_fields": ["source_time_utc", "symbol", "side", "framework", "origin_family"],
        "broker_symbol": key["broker_symbol"],
        "candidate_id": candidate_id,
        "decision_asof_utc": feature_time,
        "duplicate_key": row.get("row_id") or candidate_id,
        "feature_names": list(features.keys()),
        "feature_nulls": {name: value is None for name, value in features.items()},
        "feature_set_id": FEATURE_SET_ID,
        "feature_source_state": "lane04_timeline_features_with_row_level_source_gaps",
        "feature_time_utc": feature_time,
        "features": features,
        "no_leak_status": "passed_lane02_feature_store_contract",
        "post_outcome_field_excluded": True,
        "route_id": ROUTE_ID,
        "row_id": f"lane05_timeline_feature_{line_number:09d}",
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": SCHEMA_VERSION,
        "source_capture_utc": generated_at,
        "source_completeness_state": "complete_with_row_level_gaps" if gaps else "complete_for_emitted_features",
        "source_family": "lane04_microscope_timeline",
        "source_gaps": gaps,
        "source_hash": source_hash,
        "source_line": line_number,
        "source_path": as_posix(LANE04_TIMELINE),
        "source_use_state": source_use_state,
        "symbol": symbol,
        "upstream_row_id": row.get("row_id"),
    }


def build_canonical_candidate_feature_row(
    row: dict[str, Any],
    *,
    line_number: int,
    source_hash: str | None,
    generated_at: str,
) -> dict[str, Any]:
    symbol = normalized_symbol(row.get("symbol"))
    feature_time = iso_dt(row.get("candidate_time_utc"))
    framework = str(row.get("framework") or "unknown_framework")
    origin = str(row.get("origin_family") or "unknown_origin")
    mechanism = str(row.get("mechanism_family") or origin or framework)
    session = str(row.get("session") or "unknown_session")
    source_path = str(row.get("first_source_path") or "")
    source_family = source_family_from_path(source_path)
    side = str(row.get("side") or "unknown_side").upper()
    features: dict[str, Any] = {
        "candidate_time_known": feature_time is not None,
        "canonical_source_path_state": "source_path_present" if source_path else "source_path_absent",
        "cost_source_missing": True,
        "cost_status": "not_materialized_in_lane03_canonical_candidate_row",
        "framework": framework,
        "identity_broker_symbol": symbol,
        "identity_symbol": symbol,
        "is_breaker_re_entry": lower_text(framework) == "breaker_re_entry",
        "is_displacement_continuation": "displacement" in lower_text(mechanism) and "failed" not in lower_text(mechanism),
        "is_failed_displacement": "failed_displacement" in lower_text(mechanism) or "failed displacement" in lower_text(mechanism),
        "is_fvg_fill": lower_text(framework) == "fvg_fill",
        "is_liquidity_sweep_reclaim": "liquidity_sweep" in lower_text(mechanism) or "liquidity_sweep" in lower_text(origin),
        "is_ob_retest": lower_text(framework) == "ob_retest",
        "liquidity_sweep_proxy_state": "not_materialized_in_lane03_canonical_candidate_row",
        "m1_availability_status": "not_materialized_in_lane03_canonical_candidate_row",
        "mechanism_family": mechanism,
        "origin_family": origin,
        "session_bucket": session,
        "session_source_state": "lane03_session_field" if session != "unknown_session" else "session_absent_or_unknown",
        "side": side,
        "side_known": side not in {"", "UNKNOWN", "UNKNOWN_SIDE"},
        "source_family": source_family,
        "source_quality_status": "not_materialized_in_lane03_canonical_candidate_row",
        "source_use_state": "lane03_canonical_candidate_identity_features_only",
        "source_window_complete": None,
        "spread_r_bucket": "not_materialized_in_lane03_canonical_candidate_row",
        "stale_label_broker_real_absent_flag": True,
        "stale_label_path_proxy_flag": True,
        "symbol_known": symbol not in {"", "UNKNOWN"},
        "tick_availability_status": "not_materialized_in_lane03_canonical_candidate_row",
        **base_time_features(feature_time, symbol),
        "portfolio_scheduler_join_state": "not_materialized_in_lane03_canonical_candidate_row",
        "regime_join_state": "not_materialized_in_lane03_canonical_candidate_row",
        "selected_cell_risk_join_state": "not_materialized_in_lane03_canonical_candidate_row",
        "external_calendar_macro_join_state": "not_materialized_in_lane03_canonical_candidate_row",
        "correlation_cluster_join_state": "not_materialized_in_lane03_canonical_candidate_row",
        "broker_feasibility_state": "not_materialized_in_lane03_canonical_candidate_row",
    }

    gaps = [
        {
            "code": "lane03_market_state_features_not_materialized",
            "field_family": "htf_m15_m1_tick_state",
        },
        {
            "code": "lane03_selected_risk_portfolio_broker_news_not_materialized",
            "field_family": "selected_risk_portfolio_broker_news_calendar",
        },
    ]

    key = LANE02.canonical_key(
        {
            "broker_symbol": symbol,
            "candidate_time_utc": feature_time,
            "framework": framework,
            "origin_family": origin,
            "side": side,
            "source_row_id": row.get("canonical_candidate_id"),
            "symbol": symbol,
        },
        route_id=ROUTE_ID,
        source_path=as_posix(LANE03_CANONICAL_CANDIDATE),
    )

    return {
        "asof_dependency_fields": ["candidate_time_utc", "symbol", "side", "framework", "origin_family", "mechanism_family"],
        "broker_symbol": key["broker_symbol"],
        "canonical_candidate_id": row.get("canonical_candidate_id"),
        "canonical_duplicate_key": row.get("canonical_duplicate_key"),
        "decision_asof_utc": feature_time,
        "duplicate_key": row.get("canonical_duplicate_key"),
        "feature_nulls": {name: True for name, value in features.items() if value is None},
        "feature_set_id": FEATURE_SET_ID,
        "feature_source_state": "lane03_canonical_identity_feature_partition_with_row_level_source_gaps",
        "feature_time_utc": feature_time,
        "features": features,
        "no_leak_status": "passed_lane02_feature_store_contract",
        "post_outcome_field_excluded": True,
        "route_id": ROUTE_ID,
        "row_id": f"lane05_canonical_feature_{line_number:09d}",
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": SCHEMA_VERSION,
        "source_capture_utc": generated_at,
        "source_completeness_state": "identity_features_complete_market_state_gaps_recorded",
        "source_family": "lane03_canonical_candidate",
        "source_gaps": gaps,
        "source_hash": source_hash,
        "source_line": line_number,
        "source_path": as_posix(LANE03_CANONICAL_CANDIDATE),
        "source_use_state": "lane03_canonical_candidate_identity_features_only",
        "symbol": symbol,
    }


def feature_row_has_forbidden_fields(feature_row: dict[str, Any]) -> list[str]:
    names = list((feature_row.get("features") or {}).keys())
    hits: list[str] = []
    for name in names:
        lower = name.lower()
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in lower:
                if name.startswith("stale_label_") and token == "label_h":
                    continue
                hits.append(name)
    return sorted(set(hits))


def update_coverage(counter: Counter[tuple[str, str, str, str, str, str]], row: dict[str, Any], partition: str) -> None:
    features = row.get("features") or {}
    counter[
        (
            partition,
            str(features.get("identity_symbol") or row.get("symbol") or "UNKNOWN"),
            str(features.get("session_bucket") or "unknown_session"),
            str(features.get("framework") or "unknown_framework"),
            str(features.get("mechanism_family") or features.get("origin_family") or "unknown_mechanism"),
            str(features.get("source_use_state") or row.get("source_use_state") or "unknown_source_use"),
        )
    ] += 1


def update_gap_counts(counter: Counter[tuple[str, str, str, str]], row: dict[str, Any], partition: str) -> None:
    symbol = str(row.get("symbol") or "UNKNOWN")
    for gap in row.get("source_gaps") or []:
        counter[(partition, symbol, str(gap.get("field_family")), str(gap.get("code")))] += 1


def update_source_completeness(counter: Counter[tuple[str, str, str]], row: dict[str, Any], partition: str) -> None:
    features = row.get("features") or {}
    for family_feature in (
        "m1_availability_status",
        "tick_availability_status",
        "cost_status",
        "selected_cell_risk_join_state",
        "portfolio_scheduler_join_state",
        "correlation_cluster_join_state",
        "regime_join_state",
        "external_calendar_macro_join_state",
    ):
        counter[(partition, family_feature, str(features.get(family_feature)))] += 1


def scan_existing_feature_partition(
    path: Path,
    partition: str,
    *,
    coverage: Counter[tuple[str, str, str, str, str, str]],
    gap_counts: Counter[tuple[str, str, str, str]],
    completeness: Counter[tuple[str, str, str]],
) -> tuple[int, int]:
    row_count = 0
    forbidden_count = 0
    for row in open_jsonl(path):
        row_count += 1
        if feature_row_has_forbidden_fields(row):
            forbidden_count += 1
        update_coverage(coverage, row, partition)
        update_gap_counts(gap_counts, row, partition)
        update_source_completeness(completeness, row, partition)
    return row_count, forbidden_count


def build_outputs(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = utc_now()
    lane03_manifest = read_json(LANE03_MANIFEST)
    lane04_manifest = read_json(LANE04_MANIFEST)
    lane03_hash = upstream_manifest_hash(LANE03_CANONICAL_CANDIDATE, lane03_manifest)
    lane04_hash = upstream_manifest_hash(LANE04_TIMELINE, lane04_manifest)

    strict_tick_index = load_strict_tick_index()
    selected_cell_index = load_selected_cell_index()
    scheduler_index = load_scheduler_index()
    correlation_index = load_correlation_index()
    regime_index = load_regime_index()
    external_index, external_counts = load_external_feature_index()

    coverage: Counter[tuple[str, str, str, str, str, str]] = Counter()
    gap_counts: Counter[tuple[str, str, str, str]] = Counter()
    completeness: Counter[tuple[str, str, str]] = Counter()
    no_leak_rows: list[dict[str, Any]] = validate_feature_schema_rows(feature_schema())
    row_counts = {"canonical_candidate_feature_rows": 0, "timeline_feature_rows": 0}
    leak_violations = {"canonical_candidate_feature_rows": 0, "timeline_feature_rows": 0}

    def timeline_rows() -> Iterable[dict[str, Any]]:
        for line_number, source_row in enumerate(open_jsonl(LANE04_TIMELINE), start=1):
            feature_row = build_timeline_feature_row(
                source_row,
                line_number=line_number,
                source_hash=lane04_hash,
                strict_tick_index=strict_tick_index,
                selected_cell_index=selected_cell_index,
                scheduler_index=scheduler_index,
                correlation_index=correlation_index,
                regime_index=regime_index,
                external_index=external_index,
                generated_at=generated_at,
            )
            row_counts["timeline_feature_rows"] += 1
            if feature_row_has_forbidden_fields(feature_row):
                leak_violations["timeline_feature_rows"] += 1
            update_coverage(coverage, feature_row, "lane04_timeline")
            update_gap_counts(gap_counts, feature_row, "lane04_timeline")
            update_source_completeness(completeness, feature_row, "lane04_timeline")
            yield feature_row

    def canonical_rows() -> Iterable[dict[str, Any]]:
        for line_number, source_row in enumerate(open_jsonl(LANE03_CANONICAL_CANDIDATE), start=1):
            feature_row = build_canonical_candidate_feature_row(
                source_row,
                line_number=line_number,
                source_hash=lane03_hash,
                generated_at=generated_at,
            )
            row_counts["canonical_candidate_feature_rows"] += 1
            if feature_row_has_forbidden_fields(feature_row):
                leak_violations["canonical_candidate_feature_rows"] += 1
            update_coverage(coverage, feature_row, "lane03_canonical_candidate")
            update_gap_counts(gap_counts, feature_row, "lane03_canonical_candidate")
            update_source_completeness(completeness, feature_row, "lane03_canonical_candidate")
            yield feature_row

    if args.skip_timeline:
        if OUT_TIMELINE_FEATURES.exists() and OUT_TIMELINE_FEATURES.stat().st_size:
            count, forbidden_count = scan_existing_feature_partition(
                OUT_TIMELINE_FEATURES,
                "lane04_timeline",
                coverage=coverage,
                gap_counts=gap_counts,
                completeness=completeness,
            )
            row_counts["timeline_feature_rows"] = count
            leak_violations["timeline_feature_rows"] = forbidden_count
        else:
            raise RuntimeError("--skip-timeline requested but existing timeline feature partition is absent or empty")
    else:
        write_jsonl_gz(OUT_TIMELINE_FEATURES, timeline_rows())
    if args.skip_canonical:
        if OUT_CANONICAL_FEATURES.exists() and OUT_CANONICAL_FEATURES.stat().st_size:
            count, forbidden_count = scan_existing_feature_partition(
                OUT_CANONICAL_FEATURES,
                "lane03_canonical_candidate",
                coverage=coverage,
                gap_counts=gap_counts,
                completeness=completeness,
            )
            row_counts["canonical_candidate_feature_rows"] = count
            leak_violations["canonical_candidate_feature_rows"] = forbidden_count
        else:
            raise RuntimeError("--skip-canonical requested but existing canonical feature partition is absent or empty")
    else:
        write_jsonl_gz(OUT_CANONICAL_FEATURES, canonical_rows())

    for partition, count in row_counts.items():
        no_leak_rows.append(
            {
                "forbidden_feature_token_violation_count": leak_violations[partition],
                "no_leak_status": "pass" if leak_violations[partition] == 0 else "fail",
                "partition": partition,
                "route_id": ROUTE_ID,
                "row_count": count,
                "schema_version": "lane05_no_leak_validation_v1",
                "validation_scope": "feature_vector_rows",
            }
        )

    write_json(
        OUT_FEATURE_SCHEMA,
        {
            "feature_count": len(feature_schema()),
            "feature_set_id": FEATURE_SET_ID,
            "features": feature_schema(),
            "forbidden_post_outcome_fields_excluded": list(FORBIDDEN_FEATURE_TOKENS),
            "generated_at_utc": generated_at,
            "lane02_contract": as_posix(LANE02_DOWNSTREAM_CONTRACT),
            "route_id": ROUTE_ID,
            "schema_version": "lane05_feature_schema_v1",
        },
    )

    coverage_rows = [
        {
            "feature_partition": partition,
            "framework": framework,
            "mechanism_family": mechanism,
            "route_id": ROUTE_ID,
            "row_count": count,
            "schema_version": "lane05_feature_coverage_v1",
            "session": session,
            "source_use_state": source_use_state,
            "symbol": symbol,
        }
        for (partition, symbol, session, framework, mechanism, source_use_state), count in sorted(coverage.items())
    ]
    write_jsonl(OUT_COVERAGE, coverage_rows)

    completeness_rows = [
        {
            "feature_family_state": state,
            "feature_partition": partition,
            "route_id": ROUTE_ID,
            "row_count": count,
            "schema_version": "lane05_source_completeness_v1",
            "source_completeness_feature": feature_name,
        }
        for (partition, feature_name, state), count in sorted(completeness.items())
    ]
    write_jsonl(OUT_SOURCE_COMPLETENESS, completeness_rows)

    gap_rows = [
        {
            "feature_partition": partition,
            "field_family": family,
            "gap_code": code,
            "route_id": ROUTE_ID,
            "row_count": count,
            "schema_version": "lane05_source_gap_v1",
            "source_gap_status": "row_level_gap_embedded_in_feature_vector_and_aggregated_here",
            "symbol": symbol,
        }
        for (partition, symbol, family, code), count in sorted(gap_counts.items())
    ]
    write_jsonl(OUT_SOURCE_GAPS, gap_rows)
    write_jsonl(OUT_NO_LEAK, no_leak_rows)

    write_json(
        OUT_IMPORTANCE,
        {
            "feature_set_id": FEATURE_SET_ID,
            "generated_at_utc": generated_at,
            "importance_readiness": [
                {
                    "feature_name": spec["feature_name"],
                    "feature_namespace": spec["feature_namespace"],
                    "ml_ready": spec["downstream_eligibility"]["ml_dataset"] and spec["availability_class"] in {"pre_candidate", "candidate_time", "pre_order", "source_metadata"},
                    "selector_ready": spec["downstream_eligibility"]["selector"],
                    "source_family": spec["feature_source_family"],
                    "source_use_state": spec["source_use_state"],
                }
                for spec in feature_schema()
            ],
            "result_boundary": "feature_importance_metadata_only_no_model_training_no_feature_selection_claim",
            "route_id": ROUTE_ID,
            "schema_version": "lane05_feature_importance_readiness_v1",
        },
    )

    downstream_contract = {
        "feature_set_id": FEATURE_SET_ID,
        "generated_at_utc": generated_at,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane05_downstream_contract_v1",
        "contracts": {
            "Label Store": {
                "join_key": "canonical key from Lane02 plus candidate_id/canonical_candidate_id when present",
                "rule": "labels may join after split/purge; no label/outcome fields are emitted in Lane05 feature columns",
                "required_use": ["stale_label_broker_real_absent_flag", "stale_label_path_proxy_flag", "source_gaps"],
            },
            "Digital Twin": {
                "join_key": "symbol + feature_time_utc + candidate_id/row_id",
                "rule": "decision-state features are separated from future path/tick outcome labels",
                "required_use": ["m1_availability_status", "tick_availability_status", "source_window_complete", "strict_tick_available"],
            },
            "ML": {
                "join_key": "feature_set_id + row_id/candidate_id + split policy from Lane02",
                "rule": "use only feature schema rows with feature_store_allowed availability; honor source gaps as missingness features",
                "required_use": ["LANE05_FEATURE_SCHEMA.json", "LANE05_NO_LEAK_VALIDATION_LEDGER.jsonl"],
            },
            "Selector": {
                "join_key": "candidate identity and as-of feature_time_utc",
                "rule": "source-bound selector features only; selected-cell family joins are not production activation",
                "required_use": ["origin/framework/side", "volatility", "liquidity", "source completeness", "selected_cell_risk_join_state"],
            },
            "Scheduler": {
                "join_key": "symbol + feature_time_utc",
                "rule": "portfolio features are nullable unless exact as-of scheduler row exists; no broker-realized PnL features in Lane05",
                "required_use": ["portfolio_scheduler_join_state", "portfolio_open_risk_before", "portfolio_open_risk_ceiling"],
            },
            "Execution Policy": {
                "join_key": "candidate_id + chosen_policy + feature_time_utc",
                "rule": "strict tick entry spread and source availability are features; future tick path results stay label/replay outputs",
                "required_use": ["chosen_policy", "strict_tick_available", "strict_tick_entry_spread_r", "broker_feasibility_state"],
            },
        },
    }
    write_json(OUT_DOWNSTREAM, downstream_contract)

    dependency_rows = [
        {
            "dependency_id": "lane01_source_authority",
            "path": as_posix(LANE01_SOURCE_AUTHORITY),
            "present": LANE01_SOURCE_AUTHORITY.exists(),
            "route_id": ROUTE_ID,
            "schema_version": "lane05_dependency_state_v1",
            "state": "consumed_source_authority_map",
        },
        {
            "dependency_id": "lane02_no_leak_contract",
            "path": as_posix(LANE02_DOWNSTREAM_CONTRACT),
            "present": LANE02_DOWNSTREAM_CONTRACT.exists(),
            "route_id": ROUTE_ID,
            "schema_version": "lane05_dependency_state_v1",
            "state": "consumed_no_leak_feature_store_contract",
        },
        {
            "dependency_id": "lane03_canonical_candidates",
            "path": as_posix(LANE03_CANONICAL_CANDIDATE),
            "present": LANE03_CANONICAL_CANDIDATE.exists(),
            "route_id": ROUTE_ID,
            "schema_version": "lane05_dependency_state_v1",
            "state": "streamed_full_canonical_candidate_feature_partition" if row_counts["canonical_candidate_feature_rows"] else "not_streamed",
        },
        {
            "dependency_id": "lane04_microscope_timeline",
            "path": as_posix(LANE04_TIMELINE),
            "present": LANE04_TIMELINE.exists(),
            "route_id": ROUTE_ID,
            "schema_version": "lane05_dependency_state_v1",
            "state": "streamed_full_timeline_feature_partition" if row_counts["timeline_feature_rows"] else "not_streamed",
        },
        {
            "dependency_id": "external_calendar_macro_snapshots",
            "path": as_posix(EXTERNAL_FEATURE_ROOT),
            "present": EXTERNAL_FEATURE_ROOT.exists(),
            "route_id": ROUTE_ID,
            "schema_version": "lane05_dependency_state_v1",
            "state": "exact_join_optional_by_symbol_and_time",
            "symbol_row_counts": external_counts,
        },
    ]
    write_jsonl(OUT_DEPENDENCY, dependency_rows)

    branch_rows = [
        {
            "branch_decision": "materialize_full_lane04_timeline_feature_partition",
            "decision_reason": "Lane04 is the row-level path anatomy source for selected denominator, M1/tick/source-completeness, and downstream label/digital-twin joins",
            "row_count": row_counts["timeline_feature_rows"],
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane05_branch_decision_v1",
        },
        {
            "branch_decision": "materialize_full_lane03_canonical_identity_feature_partition",
            "decision_reason": "Lane03 is the canonical reconstructed candidate universe; market-state gaps are embedded per row instead of dropping rows",
            "row_count": row_counts["canonical_candidate_feature_rows"],
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane05_branch_decision_v1",
        },
        {
            "branch_decision": "preserve_news_calendar_as_optional_exact_join_with_gap_rows_elsewhere",
            "decision_reason": "Local external feature snapshots exist only for a subset of symbols/windows; as-of publication checks gate emitted values",
            "row_count": len(external_index),
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane05_branch_decision_v1",
        },
    ]
    write_jsonl(OUT_BRANCH, branch_rows)

    write_json(
        OUT_RESULT_USE,
        {
            "feature_set_id": FEATURE_SET_ID,
            "result_use_status": "research_feature_store_inputs_for_label_store_digital_twin_ml_selector_scheduler_execution_policy_not_live_activation",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane05_result_use_status_v1",
        },
    )
    write_json(
        OUT_RUNTIME_BOUNDARY,
        {
            "credential_or_remote_change": False,
            "live_broker_order_operation": False,
            "paid_api_vendor_call": False,
            "production_config_prompt_risk_execution_selector_change": False,
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
            "schema_version": "lane05_runtime_effect_boundary_v1",
        },
    )
    OUT_CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane05 Feature Store V1 Context Anchor",
                "",
                f"- route_id: `{ROUTE_ID}`",
                f"- generated_at_utc: `{generated_at}`",
                "- controlling_prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_MOONSHOT_LANE05_FEATURE_STORE_V1_GOAL_PROMPT_2026-06-01.md`",
                "- evidence_class: feature-store builder, offline research only",
                "- source posture: Lane01 source authority, Lane02 no-leak/as-of contract, Lane03 canonical candidates, Lane04 microscope timelines",
                "- runtime boundary: no live broker/order/deal/position action, no paid API, no credentials/remotes, no production config/risk/selector/execution activation",
                "- resume rule: regenerate LIVE_STATE and reread prompt/starter/doctrine/current map/current reading order/upstream Lane01-Lane04 artifacts before editing or completing.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    completion = {
        "completion_status": "complete_pending_independent_verifier",
        "feature_set_id": FEATURE_SET_ID,
        "generated_at_utc": generated_at,
        "instruction_coverage": {
            "broker_real_truth_not_required_for_feature_materialization": True,
            "feature_builder_present": True,
            "feature_ledgers_present": True,
            "feature_schema_present": True,
            "full_lane03_canonical_candidate_rows_preserved": row_counts["canonical_candidate_feature_rows"] > 0,
            "full_lane04_timeline_rows_preserved": row_counts["timeline_feature_rows"] > 0,
            "goal_session_research_discipline_read_after_preflight": True,
            "no_arbitrary_top_n": True,
            "no_leak_checks_present": True,
            "research_operating_doctrine_read_after_preflight": True,
            "row_level_source_gaps_embedded": True,
            "runtime_effect_boundary_explicit": True,
            "source_completeness_ledgers_present": True,
        },
        "row_counts": row_counts,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane05_completion_audit_v1",
        "same_evidence_class_pursuit": {
            "calendar_macro": "local external feature snapshots joined where exact symbol/time and as-of publication exists; gaps recorded elsewhere",
            "cost_broker_truth": "not required for feature materialization; broker cost gaps embedded per row and aggregated",
            "m1_tick": "Lane04 M1/tick availability consumed; strict tick subset joined; absent rows carry row-level gap codes",
            "selected_cell_risk": "selected-cell source bridge joined at family level when available; exact candidate absence recorded as source gap",
        },
    }
    write_json(OUT_COMPLETION_AUDIT, completion)

    manifest = write_manifest(generated_at)
    return {
        "generated_at_utc": generated_at,
        "manifest": manifest,
        "row_counts": row_counts,
    }


def write_manifest(generated_at: str) -> dict[str, Any]:
    files = [
        OUT_FEATURE_SCHEMA,
        OUT_TIMELINE_FEATURES,
        OUT_CANONICAL_FEATURES,
        OUT_COVERAGE,
        OUT_SOURCE_COMPLETENESS,
        OUT_SOURCE_GAPS,
        OUT_NO_LEAK,
        OUT_IMPORTANCE,
        OUT_DOWNSTREAM,
        OUT_DEPENDENCY,
        OUT_BRANCH,
        OUT_RESULT_USE,
        OUT_RUNTIME_BOUNDARY,
        OUT_CONTEXT_ANCHOR,
        OUT_COMPLETION_AUDIT,
        Path(__file__),
    ]
    entries = []
    for path in files:
        if not path.exists():
            entries.append({"exists": False, "path": as_posix(path)})
            continue
        entries.append(
            {
                "bytes": path.stat().st_size,
                "exists": True,
                "line_count": count_lines(path) if path.suffix in {".jsonl", ".gz", ".md", ".py"} else None,
                "path": as_posix(path),
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "feature_set_id": FEATURE_SET_ID,
        "generated_at_utc": generated_at,
        "output_count": len(entries),
        "outputs": entries,
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "schema_version": "lane05_output_manifest_v1",
    }
    write_json(OUT_MANIFEST, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-canonical", action="store_true", help="For focused developer tests only; final route must not use this.")
    parser.add_argument("--skip-timeline", action="store_true", help="For focused developer tests only; final route must not use this.")
    return parser.parse_args()


def main() -> None:
    result = build_outputs(parse_args())
    print(json.dumps({"route_id": ROUTE_ID, "row_counts": result["row_counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
