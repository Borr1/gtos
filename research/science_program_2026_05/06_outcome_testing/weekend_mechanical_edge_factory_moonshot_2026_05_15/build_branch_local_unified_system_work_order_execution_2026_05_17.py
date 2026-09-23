#!/usr/bin/env python3
"""Consume unified recommendation rows into executable branch-local work orders."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_branch_local_unified_system_work_order_execution import (
    UNIFIED_SYSTEM_WORK_ORDER_SURFACE,
    work_order_from_unified_candidate,
    work_order_rollup,
)


PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE"

UNIFIED_RESULT_PATH = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
UNIFIED_CANDIDATE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / UNIFIED_SYSTEM_WORK_ORDER_SURFACE
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_weekend_moonshot_initial_artifacts_2026_05_15.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RUNTIME_SPEC_PATH = ROUTE_DIR / f"{PREFIX}_RUNTIME_SPEC_2026-05-17.json"
WORK_ORDER_LEDGER = ROUTE_DIR / f"{PREFIX}_WORK_ORDER_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_WORK_ORDER_LEDGER_2026-05-17.jsonl"
SOURCE_CONTROL_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CONTROL_REPAIR_WORK_ORDER_LEDGER_2026-05-17.jsonl"
SCORE_WITH_CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_WITH_CONTROL_WORK_ORDER_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_EXECUTION_WORK_ORDER_LEDGER_2026-05-17.jsonl"
GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_GUARD_WORK_ORDER_LEDGER_2026-05-17.jsonl"
AUDIT_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_AUDIT_PRESERVATION_WORK_ORDER_LEDGER_2026-05-17.jsonl"
RECHECK_LEDGER = ROUTE_DIR / f"{PREFIX}_RECHECK_WORK_ORDER_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
FAMILY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
MARKET_EXPANSION_MATRIX_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
AGENT_CONFIG = REPO / "config/agent_config.yaml"
SHADOW_OBSERVER_REGISTRY = REPO / "config/shadow_observer_registry.yaml"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local unified system work-order execution bundle. It consumes every unified recommendation row into "
    "executable default-off implementation, source/control repair, score-with-control, redesign, guard, audit, "
    "or recheck work orders. It does not change live behavior, place orders, or claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, or promotion."
)

FAMILY_OUTPUTS = {
    "IMPLEMENTATION": IMPLEMENTATION_LEDGER,
    "SOURCE_CONTROL_REPAIR": SOURCE_CONTROL_REPAIR_LEDGER,
    "SCORE_WITH_CONTROL": SCORE_WITH_CONTROL_LEDGER,
    "REDESIGN_EXECUTION": REDESIGN_EXECUTION_LEDGER,
    "GUARD": GUARD_LEDGER,
    "AUDIT_PRESERVATION": AUDIT_PRESERVATION_LEDGER,
    "RECHECK": RECHECK_LEDGER,
}

TIMEFRAME_SUFFIXES = {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"}
SYMBOL_ALIASES = {
    "US30_CASH": "US30_cash",
}

STATIC_MARKET_COVERAGE: dict[str, dict[str, Any]] = {
    "XAUUSD": {
        "broker_proxy_mapping": "MT5 XAUUSD / Sierra XAUUSD SCID / futures proxy GC",
        "tradability_status": "live-candidate-current-configured",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "config max_spread_cents, MT5 OHLC/tick where available, work-order proxy spread rows",
        "source_files": ["config/agent_config.yaml"],
    },
    "US30_cash": {
        "broker_proxy_mapping": "MT5 US30_cash / Sierra YM-to-US30_cash proxy / futures proxy YM/MYM",
        "tradability_status": "live-candidate-current-configured",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "instrument profile/config plus Sierra/proxy source rows where present",
        "source_files": ["config/agent_config.yaml"],
    },
    "US30": {
        "broker_proxy_mapping": "MT5 US30 alias / US30_cash configured tradable alias / futures proxy YM/MYM",
        "tradability_status": "configured-alias-or-historical-replay",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "config/profile alias and historical replay proxy",
        "source_files": ["config/agent_config.yaml"],
    },
    "USDJPY": {
        "broker_proxy_mapping": "MT5 USDJPY / Sierra 6J proxy",
        "tradability_status": "live-candidate-current-configured",
        "session_kz_offkz_coverage": ["tokyo_kz", "london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "config/profile tick source, MT5 historical bars, Sierra 6J proxy rows",
        "source_files": ["config/agent_config.yaml"],
    },
    "GBPJPY": {
        "broker_proxy_mapping": "MT5 GBPJPY",
        "tradability_status": "live-candidate-current-configured",
        "session_kz_offkz_coverage": ["tokyo_kz", "london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "config/profile tick source and work-order proxy spread/cost rows",
        "source_files": ["config/agent_config.yaml"],
    },
    "XAGUSD": {
        "broker_proxy_mapping": "MT5 XAGUSD / Sierra SI proxy / futures proxy SI",
        "tradability_status": "live-candidate-current-configured",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "config/profile tick source, MT5 historical bars, Sierra SI proxy rows",
        "source_files": ["config/agent_config.yaml"],
    },
    "NAS100": {
        "broker_proxy_mapping": "MT5 NAS100 / Sierra NQ proxy / futures proxy NQ/MNQ",
        "tradability_status": "configured-observer-or-live-shadow",
        "session_kz_offkz_coverage": ["ny_kz", "off_kz"],
        "spread_cost_source": "config/profile tick source, MT5 historical bars, Sierra NQ proxy rows",
        "source_files": ["config/agent_config.yaml"],
    },
    "GBPUSD": {
        "broker_proxy_mapping": "MT5 GBPUSD / Sierra 6B proxy",
        "tradability_status": "observer-only-current-configured",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "observer config/profile tick source and Sierra 6B proxy rows",
        "source_files": ["config/agent_config.yaml"],
    },
    "EURUSD": {
        "broker_proxy_mapping": "MT5 EURUSD / 6E proxy",
        "tradability_status": "observer-shadow-active",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "shadow observer registry plus OHLC proxy/no-spread unless tick source attached",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "GER40": {
        "broker_proxy_mapping": "redacted_account GER30 broker symbol for GER40 tier-2 observer",
        "tradability_status": "observer-shadow-active",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "shadow observer registry; exact spread requires source repair",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "UK100": {
        "broker_proxy_mapping": "MT5 UK100 observer",
        "tradability_status": "observer-shadow-active",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "shadow observer registry; exact spread requires source repair",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "SPX500": {
        "broker_proxy_mapping": "MT5 SPX500 / ES/MES proxy",
        "tradability_status": "configured-but-not-live-prereg-required",
        "session_kz_offkz_coverage": ["ny_kz", "off_kz"],
        "spread_cost_source": "shadow observer registry labels only; exact spread/source repair required",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "UKOUSD": {
        "broker_proxy_mapping": "UKOUSD / CL macro-liquidity proxy/control",
        "tradability_status": "context-control-only",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "context-only registry; no direct trade cost source",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "ZN_CONTROL": {
        "broker_proxy_mapping": "ZN rates/control context",
        "tradability_status": "context-control-only",
        "session_kz_offkz_coverage": ["ny_kz", "off_kz"],
        "spread_cost_source": "context-only registry; no direct trade cost source",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "VIX_VXM": {
        "broker_proxy_mapping": "VIX/VXM volatility control context",
        "tradability_status": "context-control-only",
        "session_kz_offkz_coverage": ["ny_kz", "off_kz"],
        "spread_cost_source": "context-only registry; sparse source warning required",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
    "NZDUSD": {
        "broker_proxy_mapping": "MT5 NZDUSD historical lane",
        "tradability_status": "historical-excluded-preserve-audit",
        "session_kz_offkz_coverage": ["london_kz", "ny_kz", "off_kz"],
        "spread_cost_source": "historical OHLC no-spread unless exact source repaired",
        "source_files": ["config/shadow_observer_registry.yaml"],
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        digest = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-WORKORDER-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": digest,
                "status": "HASHED" if digest else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
            "live_effect": False,
        }
    )
    return row


def string_counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter = Counter(str(row.get(key)) for row in rows)
    return {key_: int(counter[key_]) for key_ in sorted(counter)}


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {"path": rel, "artifact": PREFIX, "sha256": sha256_file(path), "safe_flags": SAFE_FLAGS, "not_completion": True}
            )
    manifest["latest_branch_local_unified_system_work_order_execution_bundle"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "branch_local_unified_system_work_order_execution_built",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": "Consumed all unified candidate rows into executable branch-local work orders.",
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def build_rollups(
    work_orders: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_scope: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in work_orders:
        by_scope[(row.get("mechanical_scope_key"), row.get("source_component"))].append(row)
        by_family[(row.get("source_component"), row.get("work_order_family"), row.get("executable_next_action"))].append(row)
    scope_rows = []
    for index, key in enumerate(sorted(by_scope, key=lambda item: tuple(str(part) for part in item)), 1):
        scope_rows.append(with_common(work_order_rollup(key, by_scope[key], index, "scope_component"), generated_at, manifest_hash))
    family_rows = []
    for index, key in enumerate(sorted(by_family, key=lambda item: tuple(str(part) for part in item)), 1):
        family_rows.append(with_common(work_order_rollup(key, by_family[key], index, "component_family_action"), generated_at, manifest_hash))
    return scope_rows, family_rows


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def infer_symbol_from_path(path: Path) -> str | None:
    text = path.as_posix().upper()
    candidates = set(STATIC_MARKET_COVERAGE) | {
        "AUDJPY",
        "AUDUSD",
        "BTCUSD",
        "CHFJPY",
        "DXY",
        "ETHUSD",
        "EURGBP",
        "EURJPY",
        "EURUSD",
        "GBPJPY",
        "GBPUSD",
        "NAS100",
        "NZDUSD",
        "US30",
        "US30_CASH",
        "USDJPY",
        "XAGUSD",
        "XAUUSD",
    }
    for candidate in sorted(candidates, key=len, reverse=True):
        if candidate.upper() in text:
            return normalize_symbol(candidate)
    return None


def normalize_symbol(symbol: str) -> str:
    return SYMBOL_ALIASES.get(symbol.upper(), symbol)


def scan_data_inventory() -> dict[str, dict[str, Any]]:
    inventory: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "available_timeframes": set(),
            "source_files": set(),
            "data_sources": set(),
            "timeframe_file_count": 0,
            "replay_result_file_count": 0,
        }
    )
    data_root = REPO / "data"
    if not data_root.exists():
        return {}
    for path in data_root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".csv", ".json", ".jsonl", ".parquet"}:
            continue
        symbol = None
        timeframe = None
        parts = path.stem.split("_")
        if parts and parts[-1].upper() in TIMEFRAME_SUFFIXES and len(parts) > 1:
            timeframe = parts[-1].upper()
            symbol = normalize_symbol("_".join(parts[:-1]).upper())
        if symbol is None:
            symbol = infer_symbol_from_path(path)
        if symbol is None:
            continue
        row = inventory[symbol]
        row["source_files"].add(relative_path(path))
        source_category = "data/" + path.relative_to(data_root).parts[0] if path.parent != data_root else "data/root"
        row["data_sources"].add(source_category)
        if timeframe:
            row["available_timeframes"].add(timeframe)
            row["timeframe_file_count"] += 1
        if any(token in path.name.lower() for token in ("replay", "events", "path_scaling", "prequential")):
            row["replay_result_file_count"] += 1
    return {
        symbol: {
            "available_timeframes": sorted(values["available_timeframes"]),
            "source_files": sorted(values["source_files"]),
            "data_sources": sorted(values["data_sources"]),
            "timeframe_file_count": int(values["timeframe_file_count"]),
            "replay_result_file_count": int(values["replay_result_file_count"]),
        }
        for symbol, values in inventory.items()
    }


def aggregate_work_order_scope(rows: list[dict[str, Any]]) -> dict[str, Any]:
    family_counts = Counter(str(row.get("work_order_family")) for row in rows)
    action_counts = Counter(str(row.get("executable_next_action")) for row in rows)
    source_counts = Counter(str(row.get("source_component")) for row in rows)
    score_rows = sum(1 for row in rows if row.get("proxy_or_module_score") is not None)
    nofill_rows = sum(1 for row in rows if "nofill" in str(row.get("source_component", "")).lower())
    market_gap_rows = sum(1 for row in rows if "market_gap" in str(row.get("source_component", "")).lower())
    exact_control_rows = sum(1 for row in rows if "EXACT_CONTROL" in str(row.get("executable_next_action", "")))
    return {
        "work_order_rows": len(rows),
        "work_order_family_counts": {key: int(family_counts[key]) for key in sorted(family_counts)},
        "executable_next_action_counts": {key: int(action_counts[key]) for key in sorted(action_counts)},
        "source_component_counts": {key: int(source_counts[key]) for key in sorted(source_counts)},
        "proxy_score_row_count": int(score_rows),
        "nofill_work_order_rows": int(nofill_rows),
        "market_gap_work_order_rows": int(market_gap_rows),
        "exact_control_work_order_rows": int(exact_control_rows),
    }


def expansion_decision(status: str, aggregate: dict[str, Any], has_data: bool) -> str:
    family_counts = aggregate.get("work_order_family_counts", {})
    if family_counts.get("AUDIT_PRESERVATION", 0):
        return "reject-current-claim-with-opportunity-preserved"
    if family_counts.get("SOURCE_CONTROL_REPAIR", 0) or status in {"configured-but-not-live-prereg-required"}:
        return "source-repair"
    if family_counts.get("SCORE_WITH_CONTROL", 0) or family_counts.get("GUARD", 0):
        return "proxy/control feature"
    if family_counts.get("IMPLEMENTATION", 0):
        return "shadow-candidate"
    if family_counts.get("REDESIGN_EXECUTION", 0):
        return "replay-only"
    if "context-control-only" in status:
        return "merge-as-system-input"
    if "historical-excluded" in status:
        return "reject-current-claim-with-opportunity-preserved"
    if has_data:
        return "replay-only"
    return "source-repair"


def exact_r_availability(aggregate: dict[str, Any], has_data: bool) -> str:
    if aggregate.get("work_order_rows", 0):
        return "broker_exact_R_not_available_in_work_order_bundle__proxy_or_control_result_only"
    if has_data:
        return "not_available_from_ohlc_or_proxy_inventory_without_trade_geometry"
    return "not_available_source_missing"


def proxy_r_availability(aggregate: dict[str, Any], has_data: bool) -> str:
    if aggregate.get("proxy_score_row_count", 0):
        return "proxy_score_available_in_work_order_rows"
    if aggregate.get("work_order_rows", 0):
        return "work_order_proxy_or_control_context_available"
    if has_data:
        return "ohlc_replay_proxy_possible_after_branch_materialization"
    return "not_available_until_source_repair"


def fillability_status(aggregate: dict[str, Any], has_data: bool) -> str:
    if aggregate.get("nofill_work_order_rows", 0):
        return "fillability_or_no_fill_rows_present"
    if aggregate.get("market_gap_work_order_rows", 0):
        return "market_gap_entry_or_avoid_fillability_source_rows_present"
    if has_data:
        return "fillability_requires_tick_spread_pending_lifecycle_or_entry_geometry_source"
    return "fillability_not_computable_until_source_available"


def build_market_expansion_matrix(
    work_orders: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    data_inventory = scan_data_inventory()
    rows: list[dict[str, Any]] = []
    seen_data_symbols: set[str] = set()

    def static_for(symbol: str) -> dict[str, Any]:
        return STATIC_MARKET_COVERAGE.get(
            symbol,
            {
                "broker_proxy_mapping": "historical/source-available symbol without current config mapping",
                "tradability_status": "historical-source-available-non-prod",
                "session_kz_offkz_coverage": ["session_unknown_or_all_available_bars", "off_kz"],
                "spread_cost_source": "OHLC inventory only; exact spread/cost requires source repair or MT5/tick extraction",
                "source_files": [],
            },
        )

    by_scope: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for order in work_orders:
        key = (
            normalize_symbol(str(order.get("symbol") or "SYSTEM_LEVEL")),
            str(order.get("route_session") or "ALL_SESSIONS"),
            str(order.get("horizon_id") or "ALL_HORIZONS"),
            str(order.get("source_component") or "unknown_component"),
            str(order.get("primitive_flag") or "ALL_PRIMITIVES"),
        )
        by_scope[key].append(order)

    for key in sorted(by_scope, key=lambda item: tuple(str(part) for part in item)):
        symbol, route_session, horizon_id, source_component, primitive_flag = key
        aggregate = aggregate_work_order_scope(by_scope[key])
        static = static_for(symbol)
        data = data_inventory.get(symbol, {})
        has_data = bool(data)
        seen_data_symbols.add(symbol)
        status = static["tradability_status"]
        missing_evidence = []
        if not has_data and symbol != "SYSTEM_LEVEL":
            missing_evidence.append("no_workspace_data_inventory_files_for_symbol")
        if aggregate.get("source_component_counts", {}).get("nofill_near_miss_source_requirement", 0):
            missing_evidence.append("near_miss_exact_spread_or_first_touch_source_required")
        if aggregate.get("exact_control_work_order_rows", 0):
            missing_evidence.append("exact_same_scope_control_denominator_required_before_runtime_score")
        missing_evidence.append("broker_realized_R_not_present_in_current_work_order_artifact")
        row = {
            "market_timeframe_session_horizon_expansion_row_id": f"OHLC-GTOS-UNIFIED-WORKORDER-MARKET-EXPANSION-{len(rows) + 1:06d}",
            "coverage_source": "work_order_scope_consumed_from_unified_rows",
            "symbol": symbol,
            "broker_proxy_mapping": static["broker_proxy_mapping"],
            "tradability_status": status,
            "data_source": sorted(set(static.get("source_files", [])) | set(data.get("data_sources", []))),
            "available_timeframes": data.get("available_timeframes", []),
            "session_kz_offkz_coverage": sorted(set(static["session_kz_offkz_coverage"]) | {route_session}),
            "route_session": route_session,
            "horizon_id": horizon_id,
            "primitive_flag": primitive_flag,
            "source_component": source_component,
            "spread_cost_source": static["spread_cost_source"],
            "replay_result_row_counts": {
                **aggregate,
                "data_timeframe_file_count": int(data.get("timeframe_file_count", 0)),
                "data_replay_result_file_count": int(data.get("replay_result_file_count", 0)),
            },
            "exact_R_availability": exact_r_availability(aggregate, has_data),
            "proxy_R_availability": proxy_r_availability(aggregate, has_data),
            "fillability_no_fill_status": fillability_status(aggregate, has_data),
            "missing_evidence": sorted(set(missing_evidence)),
            "decision": expansion_decision(status, aggregate, has_data),
            "source_files": sorted(set(static.get("source_files", [])) | set(data.get("source_files", []))),
            "all_material_scope_rows_preserved": True,
            "summary_only_terminal": False,
        }
        rows.append(with_common(row, generated_at, manifest_hash))

    for symbol, data in sorted(data_inventory.items()):
        if symbol in seen_data_symbols:
            continue
        static = static_for(symbol)
        aggregate = {
            "work_order_rows": 0,
            "work_order_family_counts": {},
            "executable_next_action_counts": {},
            "source_component_counts": {},
            "proxy_score_row_count": 0,
            "nofill_work_order_rows": 0,
            "market_gap_work_order_rows": 0,
            "exact_control_work_order_rows": 0,
        }
        row = {
            "market_timeframe_session_horizon_expansion_row_id": f"OHLC-GTOS-UNIFIED-WORKORDER-MARKET-EXPANSION-{len(rows) + 1:06d}",
            "coverage_source": "data_inventory_available_not_yet_consumed_by_current_work_orders",
            "symbol": symbol,
            "broker_proxy_mapping": static["broker_proxy_mapping"],
            "tradability_status": static["tradability_status"],
            "data_source": sorted(set(static.get("source_files", [])) | set(data.get("data_sources", []))),
            "available_timeframes": data.get("available_timeframes", []),
            "session_kz_offkz_coverage": static["session_kz_offkz_coverage"],
            "route_session": "ALL_AVAILABLE_OR_UNMAPPED_SESSIONS",
            "horizon_id": "ALL_AVAILABLE_OR_UNMAPPED_HORIZONS",
            "primitive_flag": "ALL_PRIMITIVES_NOT_YET_ROUTED_IN_CURRENT_WORK_ORDER",
            "source_component": "data_inventory",
            "spread_cost_source": static["spread_cost_source"],
            "replay_result_row_counts": {
                **aggregate,
                "data_timeframe_file_count": int(data.get("timeframe_file_count", 0)),
                "data_replay_result_file_count": int(data.get("replay_result_file_count", 0)),
            },
            "exact_R_availability": exact_r_availability(aggregate, True),
            "proxy_R_availability": proxy_r_availability(aggregate, True),
            "fillability_no_fill_status": fillability_status(aggregate, True),
            "missing_evidence": ["branch-specific_entry_geometry_and_trade_lifecycle_not_in_current_work_order"],
            "decision": expansion_decision(static["tradability_status"], aggregate, True),
            "source_files": sorted(set(static.get("source_files", [])) | set(data.get("source_files", []))),
            "all_material_scope_rows_preserved": True,
            "summary_only_terminal": False,
        }
        rows.append(with_common(row, generated_at, manifest_hash))

    covered_symbols = {row["symbol"] for row in rows}
    for symbol, static in sorted(STATIC_MARKET_COVERAGE.items()):
        if symbol in covered_symbols:
            continue
        aggregate = {
            "work_order_rows": 0,
            "work_order_family_counts": {},
            "executable_next_action_counts": {},
            "source_component_counts": {},
            "proxy_score_row_count": 0,
            "nofill_work_order_rows": 0,
            "market_gap_work_order_rows": 0,
            "exact_control_work_order_rows": 0,
        }
        row = {
            "market_timeframe_session_horizon_expansion_row_id": f"OHLC-GTOS-UNIFIED-WORKORDER-MARKET-EXPANSION-{len(rows) + 1:06d}",
            "coverage_source": "config_or_shadow_registry_not_yet_consumed_by_current_work_orders",
            "symbol": symbol,
            "broker_proxy_mapping": static["broker_proxy_mapping"],
            "tradability_status": static["tradability_status"],
            "data_source": static.get("source_files", []),
            "available_timeframes": [],
            "session_kz_offkz_coverage": static["session_kz_offkz_coverage"],
            "route_session": "REGISTERED_OR_CONFIGURED_SESSIONS_NOT_YET_ROUTED",
            "horizon_id": "NO_CURRENT_WORK_ORDER_HORIZON",
            "primitive_flag": "NO_CURRENT_WORK_ORDER_PRIMITIVE",
            "source_component": "config_or_shadow_registry",
            "spread_cost_source": static["spread_cost_source"],
            "replay_result_row_counts": aggregate,
            "exact_R_availability": exact_r_availability(aggregate, False),
            "proxy_R_availability": proxy_r_availability(aggregate, False),
            "fillability_no_fill_status": fillability_status(aggregate, False),
            "missing_evidence": ["historical_or_replay_rows_not_materialized_in_current_work_order_scope"],
            "decision": expansion_decision(static["tradability_status"], aggregate, False),
            "source_files": static.get("source_files", []),
            "all_material_scope_rows_preserved": True,
            "summary_only_terminal": False,
        }
        rows.append(with_common(row, generated_at, manifest_hash))

    return rows


def main() -> int:
    generated_at = now_utc()
    source_manifest, manifest_hash = source_manifest_rows(
        [
            UNIFIED_RESULT_PATH,
            UNIFIED_CANDIDATE_LEDGER,
            HELPER_MODULE,
            BUILDER_MODULE,
            VERIFIER_MODULE,
            TEST_MODULE,
            AGENT_CONFIG,
            SHADOW_OBSERVER_REGISTRY,
        ],
        generated_at,
    )
    unified_result = read_json(UNIFIED_RESULT_PATH)
    unified_rows = read_jsonl(UNIFIED_CANDIDATE_LEDGER)
    work_orders = [
        with_common(work_order_from_unified_candidate(row, index), generated_at, manifest_hash)
        for index, row in enumerate(unified_rows, 1)
    ]

    by_family = {family: [row for row in work_orders if row.get("work_order_family") == family] for family in FAMILY_OUTPUTS}
    scope_rollups, family_rollups = build_rollups(work_orders, generated_at, manifest_hash)
    market_expansion_rows = build_market_expansion_matrix(work_orders, generated_at, manifest_hash)
    distributions = {
        "work_order_family": string_counter(work_orders, "work_order_family"),
        "executable_next_action": string_counter(work_orders, "executable_next_action"),
        "target_artifact_kind": string_counter(work_orders, "target_artifact_kind"),
        "source_component": string_counter(work_orders, "source_component"),
    }
    component_family_counter = Counter(
        f"{row.get('source_component')}|{row.get('work_order_family')}" for row in work_orders
    )
    distributions["source_component_work_order_family"] = {
        key: int(component_family_counter[key]) for key in sorted(component_family_counter)
    }
    distributions["market_expansion_decision"] = string_counter(market_expansion_rows, "decision")
    distributions["market_expansion_tradability_status"] = string_counter(market_expansion_rows, "tradability_status")
    distributions["market_expansion_symbol"] = string_counter(market_expansion_rows, "symbol")
    distributions["market_expansion_coverage_source"] = string_counter(market_expansion_rows, "coverage_source")

    buckets = []
    for family, counter in distributions.items():
        for value, count in counter.items():
            buckets.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-WORKORDER-BUCKET-{len(buckets) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": value,
                        "row_count": count,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    questions = [
        "Did all 17,916 unified candidate rows become executable branch-local work orders?",
        "Which rows are concrete default-off code/spec implementation work?",
        "Which REDESIGN rows are now no-fill avoid, retest, offset, market-entry, or horizon execution actions?",
        "Which GUARD rows are denominator guards versus no-fill source-confidence guards?",
        "Which SOURCE_OR_CONTROL_REPAIR rows already have satisfied source and should flow into replay instead of staying blocked?",
        "Which SCORE_WITH_CONTROL rows can be computed immediately from existing control context?",
        "Which current-claim rejection rows preserve missed-opportunity paths instead of deleting mechanisms?",
        "Which markets, sessions, timeframes, horizons, and proxy/source roots are covered or still source-repair-only?",
        "What should the next builder execute after this work-order packet?",
    ]
    question_rows = [
        with_common(
            {
                "question_id": f"OHLC-GTOS-UNIFIED-WORKORDER-Q-{index:03d}",
                "question": question,
                "answer_route": "Answered by work-order, family, scope, bucket, and source-manifest ledgers.",
            },
            generated_at,
            manifest_hash,
        )
        for index, question in enumerate(questions, 1)
    ]
    counts = {
        "input_unified_candidate_rows": len(unified_rows),
        "work_order_rows": len(work_orders),
        "implementation_work_order_rows": len(by_family["IMPLEMENTATION"]),
        "source_control_repair_work_order_rows": len(by_family["SOURCE_CONTROL_REPAIR"]),
        "score_with_control_work_order_rows": len(by_family["SCORE_WITH_CONTROL"]),
        "redesign_execution_work_order_rows": len(by_family["REDESIGN_EXECUTION"]),
        "guard_work_order_rows": len(by_family["GUARD"]),
        "audit_preservation_work_order_rows": len(by_family["AUDIT_PRESERVATION"]),
        "recheck_work_order_rows": len(by_family["RECHECK"]),
        "scope_rollup_rows": len(scope_rollups),
        "family_rollup_rows": len(family_rollups),
        "bucket_rows": len(buckets),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "market_timeframe_session_horizon_expansion_rows": len(market_expansion_rows),
        "runtime_spec_rows": 1,
    }
    expected_input_count = unified_result["counts"]["unified_candidate_rows"]
    all_rows_consumed = len(work_orders) == expected_input_count == len(unified_rows)
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "all_unified_rows_consumed": all_rows_consumed,
        "bucket_distributions": distributions,
        "system_decision": {
            "work_order_family_counts": distributions["work_order_family"],
            "source_component_work_order_family_counts": distributions["source_component_work_order_family"],
            "market_expansion_decision_counts": distributions["market_expansion_decision"],
            "system_recommendation": "BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE_RESULT: execute these work orders into concrete code/spec candidates, source/control computations, no-fill variant scoring, guard registrations, current-claim audit routing, and market/timeframe/session/horizon expansion decisions next.",
        },
    }
    runtime = {
        "artifact": f"{PREFIX}_RUNTIME_SPEC",
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "unified_system_work_order_surface": UNIFIED_SYSTEM_WORK_ORDER_SURFACE,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "all_unified_rows_consumed": all_rows_consumed,
        "work_order_family_counts": distributions["work_order_family"],
        "market_timeframe_session_horizon_expansion_rows": len(market_expansion_rows),
    }

    write_jsonl(WORK_ORDER_LEDGER, work_orders)
    for family, path in FAMILY_OUTPUTS.items():
        write_jsonl(path, by_family[family])
    write_jsonl(SCOPE_ROLLUP_LEDGER, scope_rollups)
    write_jsonl(FAMILY_ROLLUP_LEDGER, family_rollups)
    write_jsonl(BUCKET_LEDGER, buckets)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_jsonl(MARKET_EXPANSION_MATRIX_LEDGER, market_expansion_rows)
    write_text(RUNTIME_SPEC_PATH, json.dumps(runtime, indent=2, sort_keys=True) + "\n")
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Branch-Local Unified System Work-Order Execution Bundle",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                f"- Work-order rows: `{counts['work_order_rows']}`.",
                f"- Implementation rows: `{counts['implementation_work_order_rows']}`.",
                f"- Redesign execution rows: `{counts['redesign_execution_work_order_rows']}`.",
                f"- Guard rows: `{counts['guard_work_order_rows']}`.",
                f"- Market/timeframe/session/horizon expansion matrix rows: `{counts['market_timeframe_session_horizon_expansion_rows']}`.",
                "",
                CLAIM_BOUNDARY,
                "",
            ]
        ),
    )
    outputs = [
        RESULT_PATH,
        SUMMARY_PATH,
        RUNTIME_SPEC_PATH,
        WORK_ORDER_LEDGER,
        *FAMILY_OUTPUTS.values(),
        SCOPE_ROLLUP_LEDGER,
        FAMILY_ROLLUP_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        MARKET_EXPANSION_MATRIX_LEDGER,
    ]
    append_manifest(outputs, result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "artifact": PREFIX, "counts": counts}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
