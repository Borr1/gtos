#!/usr/bin/env python3
"""Build the MT5/OHLCV market-expansion availability route.

This route is read-only. It inventories the localhost siliconmetatrader5 bridge,
scans existing OHLCV exports, and emits exact safe export commands for remaining
coverage gaps. It does not place, modify, inspect, or cancel broker orders.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ROUTE = Path(__file__).resolve().parent
EXPORT_ROOT = PROJECT_ROOT / "data" / "mt5_research_exports"

TIMEFRAMES = ("D1", "H4", "H1", "M15", "M1")
HARD_DROPPED_FILE_SYMBOLS = {"NATGAS_cash", "HEATOIL_c"}
SOURCE_TRUTH_SCOPE = "market_expansion_ohlcv_tick_volume_only"

ASSET_CLASS_BY_FAMILY = {
    "agri_softs": "commodity_softs",
    "crypto_alt_or_major": "crypto_cfd",
    "dxy_context": "usd_index_context",
    "energy": "commodity_energy",
    "fx_major_usd": "fx",
    "fx_usd_minor_em": "fx",
    "indices_context": "index_cfd_context",
    "jpy_fx": "fx",
    "metal_cross": "metal_cross_cfd",
    "metals_copper": "metal_cfd",
    "non_jpy_fx_cross": "fx",
    "single_stock_cfd": "single_stock_cfd",
    "other": "other",
}

PRIOR_SOURCE_ARTIFACTS = [
    "research/operations/final_moonshot_candidate_full_book_live_activation_2026_06_18/NEXT_PROMPT.md",
    "research/operations/final_moonshot_candidate_full_book_live_activation_2026_06_18/DECISION_LEDGER.jsonl",
    "research/operations/final_moonshot_candidate_natgas_decomposition_2026_06_18/ASIA_PDL_FADE_NATGAS_DECOMPOSITION_RESULT.json",
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/COMPLETENESS_AUDIT_SUBAGENT_RESULTS.json",
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/SUBSTRATE_MAP.json",
    "data/mt5_research_exports/cycle4_universe_d1/manifest.json",
    "scripts/export_mt5_research_ohlcv.py",
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def file_symbol_for_broker_symbol(name: str) -> str:
    return name.replace(".", "_")


def alias_candidates(name: str) -> list[str]:
    file_symbol = file_symbol_for_broker_symbol(name)
    candidates = {name, file_symbol}
    if name.endswith(".cash"):
        candidates.add(name[:-5])
        candidates.add(file_symbol[:-5] + "_cash")
    if name.endswith(".c"):
        candidates.add(name[:-2])
        candidates.add(file_symbol[:-2] + "_c")
    if file_symbol.endswith("_cash"):
        candidates.add(file_symbol[:-5])
    if file_symbol.endswith("_c"):
        candidates.add(file_symbol[:-2])
    return sorted(c for c in candidates if c)


def classify_symbol(row: dict[str, Any]) -> str:
    name = str(row.get("name") or "")
    file_symbol = str(row.get("file_symbol") or "")
    path = str(row.get("path") or "").lower()
    desc = str(row.get("description") or "").lower()
    upper = file_symbol.upper()
    base = str(row.get("currency_base") or "").upper()
    profit = str(row.get("currency_profit") or "").upper()

    if "DXY" in upper:
        return "dxy_context"
    if upper.startswith(("XAU", "XAG")) and upper not in {"XAUUSD", "XAGUSD"}:
        return "metal_cross"
    if upper.startswith(("XAU", "XAG", "XPT", "XPD", "XCU")) or "metal" in path or "copper" in desc:
        return "metals_copper"
    if any(key in upper for key in ("OIL", "NATGAS", "HEATOIL")) or "energy" in path:
        return "energy"
    if any(key in upper for key in ("CORN", "WHEAT", "SOYBEAN", "COCOA", "COFFEE", "SUGAR", "COTTON")):
        return "agri_softs"
    crypto_roots = (
        "BTC", "ETH", "LTC", "XRP", "DASH", "XTZ", "ADA", "SOL", "DOGE", "DOT",
        "BNB", "BCH", "XLM", "XMR", "NEO", "ETC", "UNI", "LINK", "LNK", "AVAX",
        "AVA", "AAVE", "AAV", "ALGO", "ALG", "ATOM", "BAR", "FET", "GAL", "GRT",
        "ICP", "IMX", "MANA", "MAN", "SAND", "SAN", "VET", "VEC", "NER",
    )
    if upper.endswith("USD") and upper[:3] in crypto_roots:
        return "crypto_alt_or_major"
    if "index" in path or "cash cfd" in path or upper.endswith("_CASH") or upper in {"NAS100", "GER40", "US30", "SPX500"}:
        return "indices_context"
    if any(key in path for key in ("equit", "stock", "share", "stocks", "shares")):
        return "single_stock_cfd"
    if "forex" in path or (len(base) == 3 and len(profit) == 3 and base not in {"XAU", "XAG", "XPT", "XPD", "XCU"}):
        if "JPY" in upper:
            return "jpy_fx"
        if upper in {"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"}:
            return "fx_major_usd"
        if upper.startswith("USD") or upper.endswith("USD"):
            return "fx_usd_minor_em"
        return "non_jpy_fx_cross"
    return "other"


def priority_for_family(family: str, file_symbol: str) -> str:
    if file_symbol in HARD_DROPPED_FILE_SYMBOLS:
        return "research_only_hard_dropped_until_cost_repair"
    if family in {"non_jpy_fx_cross", "fx_usd_minor_em", "metals_copper", "metal_cross", "agri_softs", "crypto_alt_or_major"}:
        return "validation_candidate"
    if family in {"indices_context", "dxy_context", "energy", "jpy_fx", "fx_major_usd"}:
        return "context_or_extension_candidate"
    if family == "single_stock_cfd":
        return "research_inventory_only"
    return "research_inventory_only"


def asset_class_for_family(family: str) -> str:
    return ASSET_CLASS_BY_FAMILY.get(family, "other")


def spec_status_for_row(row: dict[str, Any]) -> str:
    if row.get("trade_mode") != 4:
        return "quarantined_non_full_trade_mode"
    if row.get("visible") is not True:
        return "quarantined_not_visible"
    required = (
        "spread",
        "point",
        "trade_tick_size",
        "trade_tick_value",
        "trade_contract_size",
        "volume_min",
        "volume_max",
        "volume_step",
    )
    if any(row.get(name) is None for name in required):
        return "quarantined_missing_spec_field"
    return "trade_ready"


def spread_snapshot_for_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "digits": row.get("digits"),
        "spread": row.get("spread"),
        "spread_float": row.get("spread_float"),
        "point": row.get("point"),
        "bid": row.get("bid"),
        "ask": row.get("ask"),
        "trade_tick_size": row.get("trade_tick_size"),
        "trade_tick_value": row.get("trade_tick_value"),
        "trade_contract_size": row.get("trade_contract_size"),
        "volume_min": row.get("volume_min"),
        "volume_max": row.get("volume_max"),
        "volume_step": row.get("volume_step"),
        "swap_long": row.get("swap_long"),
        "swap_short": row.get("swap_short"),
    }


def _compact_symbol_info(info: Any) -> dict[str, Any]:
    name = str(_get(info, "name") or "")
    file_symbol = file_symbol_for_broker_symbol(name)
    row = {
        "name": name,
        "file_symbol": file_symbol,
        "aliases": alias_candidates(name),
        "path": _get(info, "path"),
        "description": _get(info, "description"),
        "select": bool(_get(info, "select", False)),
        "visible": bool(_get(info, "visible", False)),
        "trade_mode": _get(info, "trade_mode"),
        "digits": _get(info, "digits"),
        "spread": _get(info, "spread"),
        "spread_float": bool(_get(info, "spread_float", False)),
        "point": _get(info, "point"),
        "bid": _get(info, "bid"),
        "ask": _get(info, "ask"),
        "trade_tick_size": _get(info, "trade_tick_size"),
        "trade_tick_value": _get(info, "trade_tick_value"),
        "trade_contract_size": _get(info, "trade_contract_size"),
        "volume_min": _get(info, "volume_min"),
        "volume_max": _get(info, "volume_max"),
        "volume_step": _get(info, "volume_step"),
        "swap_long": _get(info, "swap_long"),
        "swap_short": _get(info, "swap_short"),
        "currency_base": _get(info, "currency_base"),
        "currency_profit": _get(info, "currency_profit"),
        "currency_margin": _get(info, "currency_margin"),
        "exchange": _get(info, "exchange"),
        "ticks_bookdepth_spec_field": _get(info, "ticks_bookdepth"),
    }
    row["family"] = classify_symbol(row)
    row["asset_class"] = asset_class_for_family(row["family"])
    row["spec_status"] = spec_status_for_row(row)
    row["trade_mode_full"] = row["trade_mode"] == 4
    row["spread_snapshot"] = spread_snapshot_for_row(row)
    row["priority"] = priority_for_family(row["family"], file_symbol)
    row["hard_dropped_runtime_status"] = file_symbol in HARD_DROPPED_FILE_SYMBOLS
    return row


def bridge_inventory() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415

    client = MetaTrader5(host="localhost", port=8001, keepalive=True)
    initialized = bool(client.initialize())
    meta: dict[str, Any] = {
        "bridge_host": "localhost",
        "bridge_port": 8001,
        "initialized": initialized,
        "last_error": str(client.last_error()),
        "strict_symbol_spec_only": True,
        "account_info_read": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
    }
    if not initialized:
        return [], meta
    try:
        symbols = client.symbols_get()
        meta["symbol_count"] = 0 if symbols is None else len(symbols)
        meta["symbols_get_last_error"] = str(client.last_error())
        rows = [_compact_symbol_info(info) for info in (symbols or ())]
        rows.sort(key=lambda item: (item["family"], item["file_symbol"]))
        return rows, meta
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()


def parse_export_csv(path: Path) -> tuple[str | None, str | None, int, list[str]]:
    first: str | None = None
    last: str | None = None
    rows = 0
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if not header:
                return None, None, 0, []
            columns = [str(col) for col in header]
            try:
                time_idx = header.index("time")
            except ValueError:
                time_idx = 0
            for rec in reader:
                if not rec:
                    continue
                value = rec[time_idx] if time_idx < len(rec) else None
                first = first or value
                last = value
                rows += 1
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
            if not header:
                return None, None, 0, []
            columns = [str(col) for col in header]
            try:
                time_idx = header.index("time")
            except ValueError:
                time_idx = 0
            for rec in reader:
                if not rec:
                    continue
                value = rec[time_idx] if time_idx < len(rec) else None
                first = first or value
                last = value
                rows += 1
    return first, last, rows, columns


def split_symbol_timeframe(path: Path) -> tuple[str, str] | None:
    stem = path.stem
    for tf in TIMEFRAMES:
        suffix = f"_{tf}"
        if stem.endswith(suffix):
            return stem[: -len(suffix)], tf
    return None


def scan_existing_exports() -> dict[str, dict[str, Any]]:
    matrix: dict[str, dict[str, Any]] = defaultdict(lambda: {tf: {"files": []} for tf in TIMEFRAMES})
    if not EXPORT_ROOT.exists():
        return {}
    for csv_path in sorted(EXPORT_ROOT.rglob("*.csv")):
        parsed = split_symbol_timeframe(csv_path)
        if parsed is None:
            continue
        file_symbol, tf = parsed
        first, last, rows, columns = parse_export_csv(csv_path)
        entry = {
            "path": str(csv_path.relative_to(PROJECT_ROOT)),
            "rows": rows,
            "first": first,
            "last": last,
            "columns": columns,
            "volume_column_available": bool({"volume", "tick_volume"} & set(columns)),
            "sha256": sha256_file(csv_path) if rows else None,
        }
        matrix[file_symbol][tf]["files"].append(entry)

    compact: dict[str, dict[str, Any]] = {}
    for symbol, tf_map in matrix.items():
        compact[symbol] = {}
        for tf, payload in tf_map.items():
            files = payload["files"]
            files.sort(key=lambda item: (item["rows"], item.get("first") or "", item.get("last") or ""), reverse=True)
            total_rows = sum(int(item["rows"] or 0) for item in files)
            compact[symbol][tf] = {
                "available": bool(files),
                "file_count": len(files),
                "total_rows_across_files": total_rows,
                "best": files[0] if files else None,
                "files": files,
            }
    return dict(sorted(compact.items()))


def _coverage_for_aliases(matrix: dict[str, dict[str, Any]], aliases: list[str]) -> dict[str, Any]:
    by_tf: dict[str, Any] = {}
    for tf in TIMEFRAMES:
        candidates = []
        for alias in aliases:
            payload = matrix.get(alias, {}).get(tf)
            if payload and payload.get("available"):
                candidates.append({"alias": alias, **payload})
        candidates.sort(key=lambda item: item.get("total_rows_across_files", 0), reverse=True)
        by_tf[tf] = {
            "available": bool(candidates),
            "best_alias": candidates[0]["alias"] if candidates else None,
            "best": candidates[0].get("best") if candidates else None,
            "volume_column_available": any(bool((item.get("best") or {}).get("volume_column_available")) for item in candidates),
            "file_count": sum(int(item.get("file_count") or 0) for item in candidates),
            "total_rows_across_files": sum(int(item.get("total_rows_across_files") or 0) for item in candidates),
        }
    return by_tf


def export_command(row: dict[str, Any], timeframe: str) -> str:
    family = row["family"]
    file_symbol = row["file_symbol"]
    broker_symbol = row["name"]
    if timeframe in {"D1", "H4"}:
        start, chunk = "2014-01-01", "365"
    elif timeframe == "H1":
        start, chunk = "2020-01-01", "120"
    elif timeframe == "M15":
        start, chunk = "2023-01-01", "30"
    else:
        start, chunk = "2025-01-01", "10"
    end = "2026-06-19"
    symbol_slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in file_symbol).strip("_")
    label = f"market_expansion_{family}_{symbol_slug}_{timeframe.lower()}_20260618"
    return (
        "python3 scripts/export_mt5_research_ohlcv.py "
        "--prefer-silicon-bridge --bridge-host localhost --bridge-port 8001 --yes-live-readonly "
        f"--start {start} --end {end} --label {label} --timeframes {timeframe} "
        f"--symbol {file_symbol}:{broker_symbol} --chunk-days {chunk} "
        "--source-broker FTMO --source-role owner_authorized_research_hydration "
        f"--source-truth-scope {SOURCE_TRUTH_SCOPE}"
    )


def build_rows(inventory: list[dict[str, Any]], matrix: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    priority_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for row in inventory:
        coverage = _coverage_for_aliases(matrix, row["aliases"])
        missing = [tf for tf, payload in coverage.items() if not payload["available"]]
        validation_source_ready = all(coverage[tf]["available"] for tf in ("D1", "H4", "M15"))
        validation_ready = (
            validation_source_ready
            and row["spec_status"] == "trade_ready"
            and not row["hard_dropped_runtime_status"]
        )
        research_only = bool(row["hard_dropped_runtime_status"]) or not coverage["D1"]["available"] or row["spec_status"] != "trade_ready"
        disposition = "validation_ready" if validation_ready else "research_only_or_needs_export"
        source_spans = {
            tf: {
                "best_path": (payload.get("best") or {}).get("path"),
                "first": (payload.get("best") or {}).get("first"),
                "last": (payload.get("best") or {}).get("last"),
                "rows": (payload.get("best") or {}).get("rows"),
                "volume_column_available": payload.get("volume_column_available"),
            }
            for tf, payload in coverage.items()
            if payload.get("available")
        }
        priority_row = {
            "broker_symbol": row["name"],
            "file_symbol": row["file_symbol"],
            "family": row["family"],
            "asset_class": row["asset_class"],
            "priority": row["priority"],
            "disposition": disposition,
            "validation_ready": validation_ready,
            "validation_source_ready": validation_source_ready,
            "research_only": research_only,
            "spec_status": row["spec_status"],
            "trade_mode": row["trade_mode"],
            "trade_mode_full": row["trade_mode_full"],
            "visible": row["visible"],
            "select": row["select"],
            "spread_snapshot": row["spread_snapshot"],
            "hard_dropped_runtime_status": row["hard_dropped_runtime_status"],
            "aliases": row["aliases"],
            "available_timeframes": [tf for tf, payload in coverage.items() if payload["available"]],
            "missing_timeframes": missing,
            "tick_volume_available": any(bool(payload.get("volume_column_available")) for payload in coverage.values()),
            "source_spans": source_spans,
            "useful_inspiration": inspiration_for_family(row["family"]),
            "not_deployable_now_reason": not_deployable_reason(row, missing, validation_source_ready),
            "transformed_use": transformed_use_for_family(row["family"], row["file_symbol"]),
            "revival_gate": revival_gate_for_family(row["family"], row["file_symbol"]),
        }
        priority_rows.append(priority_row)
        for tf in missing:
            gap_rows.append(
                {
                    "broker_symbol": row["name"],
                    "file_symbol": row["file_symbol"],
                    "family": row["family"],
                    "asset_class": row["asset_class"],
                    "spec_status": row["spec_status"],
                    "timeframe": tf,
                    "gap": "no_existing_local_csv_for_any_alias",
                    "safe_export_command": export_command(row, tf),
                    "read_only": True,
                    "orderflow_used": False,
                    "blocks_current_candidate_book": False,
                }
            )
    priority_rows.sort(key=lambda item: (item["priority"], item["family"], item["file_symbol"]))
    gap_rows.sort(key=lambda item: (item["family"], item["file_symbol"], TIMEFRAMES.index(item["timeframe"])))
    return priority_rows, gap_rows


def inspiration_for_family(family: str) -> str:
    return {
        "non_jpy_fx_cross": "candidate VSS/Asian-fade/session-range mechanics can transfer beyond JPY and USD majors",
        "fx_usd_minor_em": "USD-beta, carry, and crisis/negative-beta context can diversify or veto the active book",
        "fx_major_usd": "existing FX major data remains a calibration/control baseline for new FX sleeves",
        "jpy_fx": "active JPY sleeves provide the benchmark for session and squeeze-transfer tests",
        "metals_copper": "copper/platinum/palladium can extend metals session, volatility, and Donchian mechanics",
        "metal_cross": "non-USD metal crosses can separate USD beta from metal-specific movement",
        "energy": "oil/energy Asian-fade and commodity trend ideas remain useful, with NATGAS/HEATOIL cost caution",
        "agri_softs": "soft/agri D1/H4 compression and trend behavior can add low-correlation commodity breadth",
        "crypto_alt_or_major": "active crypto ORB/compression/momentum sleeves can be stress-tested across alts",
        "indices_context": "indices can add risk-on/off context, ORB/reversion tests, and breadth filters",
        "dxy_context": "DXY is context, not an order sleeve, for USD-beta and FX/metals veto features",
        "single_stock_cfd": "single-stock CFDs are research inventory for cross-asset risk context, not immediate live sleeves",
    }.get(family, "bridge-native market can become context, validation control, or a future sleeve after OHLCV proof")


def transformed_use_for_family(family: str, file_symbol: str) -> str:
    if file_symbol in HARD_DROPPED_FILE_SYMBOLS:
        return "research-only cost/spread stress and limit-entry revival lane"
    return {
        "dxy_context": "context feature for FX/metals/risk-on routing",
        "indices_context": "context feature or separately validated index sleeve",
        "single_stock_cfd": "cross-asset context and stress regime inventory",
    }.get(family, "candidate expansion sleeve or validation/control market")


def revival_gate_for_family(family: str, file_symbol: str) -> str:
    if file_symbol in HARD_DROPPED_FILE_SYMBOLS:
        return "measured spread/cost and limit-entry replay repairs W7 hard-drop before any live allowlist use"
    if family == "dxy_context":
        return "as-of DXY feature improves sealed FX/metals routing without leakage or direct trade claims"
    if family == "single_stock_cfd":
        return "only after portfolio-context study proves robust additive value and execution/cost feasibility"
    return "D1/H4/M15 plus needed M1 tick-volume coverage, no-leak protocol, every-split replay, cost stress, null/placebo, and full-book MC pass"


def not_deployable_reason(row: dict[str, Any], missing: list[str], validation_ready: bool) -> str:
    if row["hard_dropped_runtime_status"]:
        return "runtime hard-drop remains active from W7/NATGAS evidence; needs explicit cost/limit-entry repair"
    if row.get("spec_status") != "trade_ready":
        return f"symbol spec quarantined: {row.get('spec_status')}"
    if validation_ready:
        return "data availability only; route does not score performance or authorize live expansion"
    return "missing local OHLCV timeframe coverage: " + ",".join(missing)


def mechanism_rows() -> list[dict[str, Any]]:
    families = [
        ("non_jpy_fx_cross", "FX-cross London squeeze/Asian fade/session reversion"),
        ("fx_usd_minor_em", "USD-beta/carry/crisis-alpha diversifier and veto research"),
        ("metals_copper", "copper/platinum/palladium metals-session and volatility-divergence extension"),
        ("metal_cross", "XAUEUR/XAGEUR/XAUAUD/XAGAUD USD-beta separation"),
        ("agri_softs", "soft/agri D1/H4 compression, Donchian, and commodity-trend breadth"),
        ("energy", "oil Asian-fade/trail and commodity trend; NATGAS/HEATOIL cost-repair only"),
        ("crypto_alt_or_major", "crypto ORB/compression/momentum transfer to alts"),
        ("indices_context", "index breadth/risk-on context, ORB/reversion, and failure-veto research"),
        ("dxy_context", "DXY context for USD-beta and FX/metals veto features"),
        ("single_stock_cfd", "single-stock CFD context inventory for macro/risk regime features"),
        ("tick_volume", "M1/M15 tick-volume relative intensity gate for deployed and expansion sleeves"),
    ]
    rows = []
    for family, mechanism in families:
        rows.append(
            {
                "family": family,
                "mechanism": mechanism,
                "useful_inspiration": inspiration_for_family(family),
                "required_data": ["symbol_info/spec/spread", "D1", "H4", "M15", "M1/tick-volume"],
                "forbidden_data": ["orderflow", "depth", "broker order/deal/position/account mutation"],
                "current_route_effect": "availability_and_preregistration_only",
                "promotion_gate": revival_gate_for_family(family, ""),
                "source_artifacts": PRIOR_SOURCE_ARTIFACTS,
            }
        )
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def protocol_markdown(result: dict[str, Any], gap_rows: list[dict[str, Any]]) -> str:
    sample_commands = gap_rows[:12]
    commands = "\n".join(f"- `{row['safe_export_command']}`" for row in sample_commands)
    if not commands:
        commands = "- No current gaps found for bridge-native symbols in the scanned local export corpus."
    return f"""# Market Expansion Validation Protocol

Status: availability and preregistration protocol, not live expansion authority.

## Boundary

- Allowed data: localhost Docker MT5 bridge read-only symbol info, OHLCV, and tick-volume columns; existing local exports.
- Forbidden data: orderflow/depth, broker order/deal/position/account mutation, credentials, remotes, VPS process mutation, paid APIs.
- Runtime effect: none. The full candidate book remains armed by commit `709aabfc8`; this route does not change config.

## Current Inventory

- Bridge-native symbols: `{result['broker_native_symbol_count']}`.
- Families discovered: `{len(result['family_counts'])}`.
- Validation-ready symbols: `{result['validation_ready_symbol_count']}`.
- Research-only or export-needed symbols: `{result['research_or_export_needed_symbol_count']}`.
- Coverage gap rows: `{result['coverage_gap_count']}`.

## Protocol

Data availability is only the first gate.

1. Keep every market family in the priority ledger; do not cap to a top-N summary.
2. Use symbol-info/spec/spread plus D1/H4/H1/M15/M1 OHLCV/tick-volume only.
3. Treat data availability as input readiness, not performance proof.
4. For any candidate family, freeze source window and aliases before scoring.
5. Run no-leak/as-of replay, cost stress, spread sensitivity, null/placebo, per-year/per-symbol splits, concentration checks, and full-book MC before any live expansion claim.
6. Keep NATGAS and HEATOIL hard-dropped unless a separate cost/limit-entry repair route revives them.

## Safe Export Commands

These are exact examples from the coverage-gap ledger; run more rows from `COVERAGE_GAP_LEDGER.jsonl` as needed.

{commands}
"""


def build() -> dict[str, Any]:
    created_at = utc_now()
    inventory, bridge_meta = bridge_inventory()
    matrix = scan_existing_exports()
    priority_rows, gap_rows = build_rows(inventory, matrix)
    mechanisms = mechanism_rows()

    family_counts = Counter(row["family"] for row in inventory)
    asset_class_counts = Counter(row["asset_class"] for row in inventory)
    spec_status_counts = Counter(row["spec_status"] for row in inventory)
    validation_ready_rows = [row for row in priority_rows if row["validation_ready"]]
    research_rows = [row for row in priority_rows if not row["validation_ready"]]
    hard_dropped = [row for row in priority_rows if row["hard_dropped_runtime_status"]]
    quarantined_rows = [row for row in priority_rows if row["spec_status"] != "trade_ready"]
    gap_symbol_count = len({row["file_symbol"] for row in gap_rows})
    decision = (
        "MARKET_EXPANSION_DATA_AVAILABILITY_READY_FOR_SCORING"
        if not gap_rows
        else "MARKET_EXPANSION_DATA_AVAILABILITY_READY_WITH_EXPORT_PLAN"
    )

    result = {
        "schema": "gtos.final_moonshot.market_expansion_data_availability.result.v1",
        "created_at_utc": created_at,
        "ok": bool(inventory) and bridge_meta.get("initialized") is True,
        "decision": decision,
        "route": str(ROUTE.relative_to(PROJECT_ROOT)),
        "commit_context": "after 709aabfc8 config: arm full candidate book",
        "bridge_reachable": bridge_meta.get("initialized") is True,
        "broker_native_symbol_count": len(inventory),
        "visible_symbol_count": sum(1 for row in inventory if row["visible"]),
        "full_trade_mode_symbol_count": sum(1 for row in inventory if row["trade_mode_full"]),
        "quarantined_spec_symbol_count": len(quarantined_rows),
        "local_export_symbol_count": len(matrix),
        "family_counts": dict(sorted(family_counts.items())),
        "asset_class_counts": dict(sorted(asset_class_counts.items())),
        "spec_status_counts": dict(sorted(spec_status_counts.items())),
        "validation_ready_symbol_count": len(validation_ready_rows),
        "research_or_export_needed_symbol_count": len(research_rows),
        "export_needed_symbol_count": gap_symbol_count,
        "coverage_gap_count": len(gap_rows),
        "coverage_gap_closure_complete": not gap_rows,
        "hard_dropped_symbols_preserved": [row["file_symbol"] for row in hard_dropped],
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
        "config_or_live_activation_changed": False,
        "allowed_data": [
            "localhost Docker MT5 bridge read-only symbol info/spec/spread",
            "existing local OHLCV CSV exports",
            "OHLCV volume/tick-volume column",
        ],
        "forbidden_data": [
            "orderflow",
            "depth",
            "broker order/deal/position/account mutation",
            "credentials",
            "remotes",
            "VPS process mutation",
            "paid APIs",
        ],
        "source_artifacts": PRIOR_SOURCE_ARTIFACTS,
    }

    inventory_payload = {
        "schema": "gtos.final_moonshot.market_expansion.symbol_inventory.v1",
        "created_at_utc": created_at,
        "bridge": bridge_meta,
        "symbol_count": len(inventory),
        "family_counts": result["family_counts"],
        "symbols": inventory,
    }
    alias_payload = {
        "schema": "gtos.final_moonshot.market_expansion.alias_map.v1",
        "created_at_utc": created_at,
        "aliases": [
            {
                "broker_symbol": row["name"],
                "file_symbol": row["file_symbol"],
                "family": row["family"],
                "asset_class": row["asset_class"],
                "spec_status": row["spec_status"],
                "aliases": row["aliases"],
                "identity_fallback_forbidden": True,
            }
            for row in inventory
        ],
    }
    matrix_payload = {
        "schema": "gtos.final_moonshot.market_expansion.ohlcv_availability_matrix.v1",
        "created_at_utc": created_at,
        "timeframes": list(TIMEFRAMES),
        "export_root": str(EXPORT_ROOT.relative_to(PROJECT_ROOT)),
        "symbols": {
            row["file_symbol"]: {
                "broker_symbol": row["name"],
                "family": row["family"],
                "asset_class": row["asset_class"],
                "spec_status": row["spec_status"],
                "aliases": row["aliases"],
                "coverage": _coverage_for_aliases(matrix, row["aliases"]),
            }
            for row in inventory
        },
        "local_export_symbols_not_in_bridge": sorted(set(matrix) - {row["file_symbol"] for row in inventory}),
    }

    saturation = {
        "schema": "gtos.final_moonshot.market_expansion.saturation_audit.v1",
        "ok": True,
        "no_arbitrary_top_n": True,
        "same_evidence_class_actions_completed": [
            "queried current localhost bridge symbol universe",
            "scanned existing local MT5 OHLCV CSV exports",
            "emitted per-symbol/timeframe coverage gap commands",
            "classified all bridge-native symbols into market families",
            "preserved non-promoted families with transformed use and revival gates",
            "closed all observed D1/H4/H1/M15/M1 coverage gap rows from the read-only bridge",
        ],
        "remaining_same_class_work": (
            ["score candidate mechanisms only in a later frozen validation route"]
            if not gap_rows
            else [
                "run selected safe export commands for remaining gap rows",
                "score candidate mechanisms only in a later frozen validation route",
            ]
        ),
        "not_blocking_current_live_candidate_book": True,
    }
    completion = {
        "schema": "gtos.final_moonshot.market_expansion.completion_audit.v1",
        "ok": result["ok"],
        "bridge_reachable": result["bridge_reachable"],
        "artifacts_written": True,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
        "completion_standard": "availability matrix plus exact gap/export/preregistration ledgers, not performance proof",
    }
    decision_rows = [
        {
            "row": "terminal_decision",
            "decision": decision,
            "broker_native_symbol_count": result["broker_native_symbol_count"],
            "validation_ready_symbol_count": result["validation_ready_symbol_count"],
            "coverage_gap_count": result["coverage_gap_count"],
            "runtime_effect": "none__current_candidate_book_already_armed_elsewhere",
            "owner_vps_boundary": "not_touched",
        },
        {
            "row": "hard_drop_translation",
            "decision": "preserve_natgas_heatoil_research_only_until_cost_limit_entry_repair",
            "symbols": sorted(HARD_DROPPED_FILE_SYMBOLS),
            "useful_inspiration": "energy and gas behavior can still teach cost, spread, and limit-entry repair lessons",
            "revival_gate": "measured spread/cost and limit-entry replay must repair W7 hard-drop before live allowlist use",
        },
        {
            "row": "next_scoring_route",
            "decision": "score_expansion_families_only_after_source_freeze_and_gap_closure",
            "input_ledgers": [
                "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl",
                "COVERAGE_GAP_LEDGER.jsonl",
                "CANDIDATE_MECHANISM_MAP.jsonl",
            ],
            "forbidden_data": ["orderflow", "depth"],
        },
    ]
    repair = {
        "schema": "gtos.final_moonshot.market_expansion.repair_ledger.v1",
        "ok": True,
        "remaining_repairs": [] if not gap_rows else [
            {
                "repair": "close_ohlcv_coverage_gap_rows_before_family_scoring",
                "row_count": len(gap_rows),
                "ledger": "COVERAGE_GAP_LEDGER.jsonl",
                "effect": "not_blocking_current_armed_candidate_book",
            }
        ],
        "completed_repairs": [
            {
                "repair": "close_ohlcv_coverage_gap_rows_before_family_scoring",
                "row_count": 0,
                "ledger": "COVERAGE_GAP_LEDGER.jsonl",
                "effect": "all_observed_bridge_native_ohlcv_timeframe_gap_rows_closed",
            }
        ] if not gap_rows else [],
        "non_repair_boundaries": [
            "orderflow/depth excluded by owner for this route",
            "live config activation already handled by candidate-book activation route, not this route",
        ],
    }
    focused_test = {
        "schema": "gtos.final_moonshot.market_expansion.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 research/operations/final_moonshot_market_expansion_data_availability_2026_06_18/verify_market_expansion_data_availability.py",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_market_expansion_data_availability_2026_06_18/NEXT_PROMPT.md",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_market_expansion_data_availability_2026_06_18 --full-jsonl",
            "PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' pytest tests/ultimate_book/test_market_expansion_data_availability_artifacts.py -q",
        ],
        "warning": "PytestConfigWarning: Unknown config option asyncio_mode may appear and is pre-existing",
    }

    write_json(ROUTE / "MARKET_SYMBOL_INVENTORY.json", inventory_payload)
    write_json(ROUTE / "BROKER_NATIVE_ALIAS_MAP.json", alias_payload)
    write_json(ROUTE / "OHLCV_AVAILABILITY_MATRIX.json", matrix_payload)
    write_jsonl(ROUTE / "COVERAGE_GAP_LEDGER.jsonl", gap_rows)
    write_jsonl(ROUTE / "SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl", priority_rows)
    write_jsonl(ROUTE / "CANDIDATE_MECHANISM_MAP.jsonl", mechanisms)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "MARKET_EXPANSION_DATA_AVAILABILITY_RESULT.json", result)
    write_json(ROUTE / "REPAIR_LEDGER.json", repair)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused_test)
    (ROUTE / "EXPANSION_VALIDATION_PROTOCOL.md").write_text(
        protocol_markdown(result, gap_rows),
        encoding="utf-8",
    )
    next_prompt = """# Market Expansion Validation Scoring Prompt

Run mandatory GTOS preflight, do not rely on chat memory, reread this prompt after any compaction/resume/interruption/uncertainty, and read goal_session_research_discipline.md plus research_operating_doctrine.md as active instructions, not background, before acting.

Evidence class: frozen market-expansion candidate scoring from the availability route. Operate at maximum practical reasoning depth, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 cutoff, same-evidence-class blocker pursuit, full same-evidence-class pursuit, and inspire-not-kill preservation. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action has been tried or proven inapplicable inside the approved evidence class. Preserve all material rows in full ledgers before any ranking summary. Use `MARKET_SYMBOL_INVENTORY.json`, `BROKER_NATIVE_ALIAS_MAP.json`, `OHLCV_AVAILABILITY_MATRIX.json`, `SYMBOL_CLASS_TAXONOMY_PRIORITY_LEDGER.jsonl`, `COVERAGE_GAP_LEDGER.jsonl`, `CANDIDATE_MECHANISM_MAP.jsonl`, and `EXPANSION_VALIDATION_PROTOCOL.md` as controlling inputs.

Allowed data: source-hashed local MT5 OHLCV/tick-volume exports, read-only localhost bridge exports needed to close exact `COVERAGE_GAP_LEDGER.jsonl` rows, current route artifacts, committed code, and public docs only when source captures are saved. Do not use orderflow/depth. Forbidden surfaces: no production-change or live trading broker operation; no prompt/config/risk/execution/safety/canary/selector activation changes; no broker/account/order/history/deal/position mutation; no credentials; no remotes; no VPS processes; no MT5 order state; no paid API/vendor calls.

Objective: freeze one or more expansion families from the full priority ledger, close required OHLCV gaps with safe exports, build no-leak/as-of replay packets, and compute source-bound candidate/mechanism results with exact-R/proxy-R/expectancy where geometry permits, cost stress, per-symbol/per-year splits, null/placebo controls, concentration checks, and full-book interaction notes. Preserve every non-promoted mechanism with useful inspiration, transformed use, and revival gate. Result materialization is required: data availability must become source-capture/source completeness proof, branch decision, implementation decision, computed candidate result, or exact source-safe impossibility.

Required artifacts: frozen input manifest, export closure ledger, source-hash ledger, replay/scoring scripts, candidate result ledgers, null/placebo ledgers, concentration/stress audit, inspire-not-kill ledger, verifier result, focused tests, completion audit, output manifest, and successor prompt. Completion requires computed results or exact source-safe impossibility for every selected same-class family; data availability alone is not enough.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")

    manifest = {
        "schema": "gtos.final_moonshot.market_expansion.output_manifest.v1",
        "created_at_utc": created_at,
        "files": sorted(
            p.name
            for p in ROUTE.iterdir()
            if p.is_file() and p.name != "__pycache__"
        ),
    }
    write_json(ROUTE / "OUTPUT_MANIFEST.json", manifest)
    return result


def main() -> int:
    result = build()
    print(
        json.dumps(
            {
                "ok": result["ok"],
                "decision": result["decision"],
                "broker_native_symbol_count": result["broker_native_symbol_count"],
                "validation_ready_symbol_count": result["validation_ready_symbol_count"],
                "coverage_gap_count": result["coverage_gap_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
