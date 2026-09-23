#!/usr/bin/env python3
"""Build Route C tick/Sierra source contract and primitive schema.

This is the first artifact for the orderflow lane selected by the route
frontier refresh. It inventories local tick parquet files and Sierra Chart
binary files, then freezes primitive families that can be implemented later.

It is deliberately a source/primitive contract only: no edge, R/PnL,
expectancy, validation, live-readiness, or promotion claim.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
STAMP = "2026-05-15"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

TICK_ROOTS = [
    ("worktree_ticks", Path("data/ticks").resolve()),
    ("absolute_ticks", Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks")),
]
SIERRA_ROOTS = [
    ("sierra_data", Path(r"C:\SierraChart\Data")),
    ("sierra_market_depth", Path(r"C:\SierraChart\Data\MarketDepthData")),
]

RESULT_PATH = ROUTE_DIR / f"TICK_SIERRA_SOURCE_CONTRACT_RESULT_{STAMP}.json"
TICK_LEDGER = ROUTE_DIR / f"TICK_PARQUET_SOURCE_CONTRACT_LEDGER_{STAMP}.jsonl"
SIERRA_LEDGER = ROUTE_DIR / f"SIERRA_SOURCE_CONTRACT_LEDGER_{STAMP}.jsonl"
PRIMITIVE_SCHEMA_LEDGER = ROUTE_DIR / f"TICK_SIERRA_PRIMITIVE_SCHEMA_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"TICK_SIERRA_SOURCE_CONTRACT_SUMMARY_{STAMP}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EXPECTED_TICK_COLUMNS = [
    "ts_utc",
    "ts_msc",
    "bid",
    "ask",
    "last",
    "volume",
    "flags",
    "inferred_aggressor",
]


def iso(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def parquet_stats(path: Path) -> dict[str, Any]:
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(path)
    names = pf.schema_arrow.names
    row_count = pf.metadata.num_rows
    row_groups = pf.metadata.num_row_groups
    stats_by_col: dict[str, dict[str, Any]] = {}
    for column_name in ["ts_utc", "bid", "ask", "last", "volume", "flags"]:
        if column_name not in names:
            continue
        column_idx = names.index(column_name)
        mins: list[Any] = []
        maxs: list[Any] = []
        nulls = 0
        stats_available = False
        for rg_idx in range(row_groups):
            col = pf.metadata.row_group(rg_idx).column(column_idx)
            stats = col.statistics
            if stats is None:
                continue
            stats_available = True
            nulls += int(stats.null_count or 0)
            if stats.has_min_max:
                mins.append(stats.min)
                maxs.append(stats.max)
        if stats_available:
            stats_by_col[column_name] = {
                "min": iso(min(mins)) if mins else None,
                "max": iso(max(maxs)) if maxs else None,
                "null_count": nulls,
            }
    return {
        "columns": names,
        "row_count": row_count,
        "row_groups": row_groups,
        "stats": stats_by_col,
    }


def build_tick_rows() -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_paths: set[str] = set()
    for root_label, root in TICK_ROOTS:
        if not root.exists():
            errors.append(f"missing_tick_root:{root_label}:{root}")
            continue
        for path in sorted(root.glob("*/*.parquet")):
            resolved = str(path.resolve()).lower()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            symbol = path.parent.name
            trade_date = path.stem
            try:
                meta = parquet_stats(path)
                missing_columns = [c for c in EXPECTED_TICK_COLUMNS if c not in meta["columns"]]
                schema_status = "SCHEMA_OK" if not missing_columns else "SCHEMA_MISSING_COLUMNS"
                rows.append({
                    "route_id": ROUTE_ID,
                    "root_label": root_label,
                    "path": str(path),
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "bytes": path.stat().st_size,
                    "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat().replace("+00:00", "Z"),
                    "row_count": meta["row_count"],
                    "row_groups": meta["row_groups"],
                    "columns": meta["columns"],
                    "schema_status": schema_status,
                    "missing_columns": missing_columns,
                    "ts_utc_min": meta["stats"].get("ts_utc", {}).get("min"),
                    "ts_utc_max": meta["stats"].get("ts_utc", {}).get("max"),
                    "stats": meta["stats"],
                    "evidence_boundary": "tick parquet source contract only; no strategy or edge result",
                    "safe_flags": SAFE_FLAGS,
                })
            except Exception as exc:  # noqa: BLE001
                errors.append(f"tick_parquet_error:{path}:{type(exc).__name__}:{exc}")
                rows.append({
                    "route_id": ROUTE_ID,
                    "root_label": root_label,
                    "path": str(path),
                    "symbol": symbol,
                    "trade_date": trade_date,
                    "bytes": path.stat().st_size if path.exists() else None,
                    "row_count": None,
                    "schema_status": "PARQUET_READ_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "evidence_boundary": "failed source contract row; do not consume until repaired",
                    "safe_flags": SAFE_FLAGS,
                })
    return rows, errors


def build_sierra_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for root_label, root in SIERRA_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext not in {".scid", ".depth", ".dly"}:
                continue
            resolved = str(path.resolve()).lower()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            rows.append({
                "route_id": ROUTE_ID,
                "root_label": root_label,
                "path": str(path),
                "symbol_hint": path.stem,
                "extension": ext,
                "bytes": path.stat().st_size,
                "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat().replace("+00:00", "Z"),
                "parser_status": "METADATA_ONLY_BINARY_PARSER_PENDING",
                "evidence_boundary": "Sierra source availability only; binary parser and source-time contract required before primitives",
                "safe_flags": SAFE_FLAGS,
            })
    return rows


def build_primitive_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "primitive_id": "TICK_DELTA_M15",
            "family": "signed_flow_proxy",
            "source": "MT5 tick parquet",
            "required_columns": ["ts_utc", "bid", "ask", "volume", "inferred_aggressor"],
            "definition": "M15 cumulative signed tick-volume proxy using inferred_aggressor; spot CFD zero-volume rows substitute one tick.",
            "known_limit": "Broker BUY/SELL flags and last/volume are generally unavailable on current spot CFD feed; this is flow proxy, not true exchange aggressor volume.",
            "control_requirements": ["same-symbol/session baseline", "duplicate-effective-N", "neighbor/shuffled-time placebo", "cost boundary before R language"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "primitive_id": "CVD_DIVERGENCE_M15",
            "family": "absorption_proxy",
            "source": "MT5 tick parquet",
            "required_columns": ["ts_utc", "bid", "ask", "inferred_aggressor"],
            "definition": "Sign disagreement between M15 price change and cumulative tick delta.",
            "known_limit": "Neutral target movement only until tied to entry geometry and sealed controls.",
            "control_requirements": ["same-denominator OHLC movement baseline", "directional placebo", "session/regime concentration"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "primitive_id": "SPREAD_SHOCK_M15",
            "family": "liquidity_withdrawal_proxy",
            "source": "MT5 tick parquet",
            "required_columns": ["ts_utc", "bid", "ask"],
            "definition": "Within-bar spread spike count and max/close spread relative to rolling tick median.",
            "known_limit": "May capture broker feed behavior rather than market microstructure; requires symbol/session normalization.",
            "control_requirements": ["spread baseline by symbol/session", "news/calendar exclusion or label", "cost/fillability stress"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "primitive_id": "TICK_VELOCITY_BURST_M15",
            "family": "activity_regime",
            "source": "MT5 tick parquet",
            "required_columns": ["ts_utc"],
            "definition": "Tick count per second by M15 bar compared with symbol/session baseline.",
            "known_limit": "Activity can correlate with both opportunity and adverse selection; not directional without controls.",
            "control_requirements": ["same-clock baseline", "calendar/news labels", "purged time split"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "primitive_id": "MICRO_REVERSAL_M15",
            "family": "intrabar_path_shape",
            "source": "MT5 tick parquet",
            "required_columns": ["ts_utc", "bid", "ask", "last"],
            "definition": "Greedy zigzag count of reversals exceeding a fraction of the tick-derived M15 range.",
            "known_limit": "Threshold is descriptive until calibrated out of sample.",
            "control_requirements": ["range-normalized baseline", "neighbor-window placebo", "symbol/session concentration"],
            "safe_flags": SAFE_FLAGS,
        },
        {
            "primitive_id": "SIERRA_DEPTH_AVAILABILITY",
            "family": "future_depth_route",
            "source": "Sierra .depth/.scid binary files",
            "required_columns": ["parser_pending"],
            "definition": "Metadata-only route for future queue-depth/order-book features after binary parser and timestamp contract are established.",
            "known_limit": "No Sierra-derived primitive can be scored from this contract alone.",
            "control_requirements": ["binary parser audit", "timestamp/timezone contract", "symbol mapping", "source coverage ledger"],
            "safe_flags": SAFE_FLAGS,
        },
    ]
    return rows


def main() -> int:
    generated_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    tick_rows, tick_errors = build_tick_rows()
    sierra_rows = build_sierra_rows()
    primitive_rows = build_primitive_rows()

    write_jsonl(TICK_LEDGER, tick_rows)
    write_jsonl(SIERRA_LEDGER, sierra_rows)
    write_jsonl(PRIMITIVE_SCHEMA_LEDGER, primitive_rows)

    tick_symbols = sorted({row["symbol"] for row in tick_rows if row.get("schema_status") == "SCHEMA_OK"})
    tick_rows_total = sum(int(row.get("row_count") or 0) for row in tick_rows)
    sierra_ext_counts: dict[str, int] = {}
    for row in sierra_rows:
        sierra_ext_counts[row["extension"]] = sierra_ext_counts.get(row["extension"], 0) + 1

    result = {
        "schema": "tick_sierra_source_contract_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "TICK_SIERRA_SOURCE_CONTRACT_AND_PRIMITIVE_SCHEMA_ONLY",
        "claim_boundary": "Source contract and primitive schema only. No edge, R/PnL, expectancy, validation, live-readiness, or promotion claim.",
        "counts": {
            "tick_parquet_files": len(tick_rows),
            "tick_schema_ok_files": sum(1 for row in tick_rows if row.get("schema_status") == "SCHEMA_OK"),
            "tick_symbols": len(tick_symbols),
            "tick_rows_total": tick_rows_total,
            "tick_error_rows": sum(1 for row in tick_rows if row.get("schema_status") == "PARQUET_READ_ERROR"),
            "sierra_files": len(sierra_rows),
            "sierra_scid_files": sierra_ext_counts.get(".scid", 0),
            "sierra_depth_files": sierra_ext_counts.get(".depth", 0),
            "sierra_dly_files": sierra_ext_counts.get(".dly", 0),
            "primitive_schema_rows": len(primitive_rows),
        },
        "tick_symbols": tick_symbols,
        "tick_errors": tick_errors,
        "open_blockers": [
            "tick primitives need same-symbol/session baseline before descriptor comparison",
            "MT5 tick aggressor is proxy-only on current spot CFD feed",
            "Sierra binary parser and timestamp contract required before depth primitives",
            "no strategy-performance language before entry geometry, costs, and sealed controls",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = [
        "# Tick/Sierra Source Contract",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source contract and primitive schema only. No edge, R/PnL, validation, live-readiness, or promotion verdict.",
        "",
        "## Counts",
        "",
        f"- Tick parquet files: `{len(tick_rows)}`",
        f"- Tick schema-ok files: `{result['counts']['tick_schema_ok_files']}`",
        f"- Tick symbols: `{len(tick_symbols)}` ({', '.join(tick_symbols)})",
        f"- Tick rows total from parquet metadata: `{tick_rows_total}`",
        f"- Sierra files: `{len(sierra_rows)}`",
        f"- Sierra `.scid`: `{sierra_ext_counts.get('.scid', 0)}`",
        f"- Sierra `.depth`: `{sierra_ext_counts.get('.depth', 0)}`",
        f"- Primitive schema rows: `{len(primitive_rows)}`",
        "",
        "## Boundary",
        "",
        "- MT5 tick aggressor is a proxy on this broker because last/volume/buy-sell flags are not authoritative.",
        "- Sierra files are metadata-only until a binary parser and timestamp contract are audited.",
        "- Route C has started, but no primitive has been scored yet.",
        "",
    ]
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")

    print(json.dumps({"ok": True, "result": str(RESULT_PATH), "tick_files": len(tick_rows), "sierra_files": len(sierra_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
