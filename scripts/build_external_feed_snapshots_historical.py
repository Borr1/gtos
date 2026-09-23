#!/usr/bin/env python3
"""Build shadow external-feed snapshots for historical MT5 candles.

This utility reads local MT5 CSV exports and joins cached external feeds using
publication/as-of timestamps. It writes ignored research artifacts under
``data/external/features`` only when ``--write`` is provided. It does not touch
live trading components.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    SCHEMA_VERSION,
    SOURCE_REGISTRY,
    ExternalFeedStore,
    ensure_utc,
    safe_slug,
    utc_now,
)


DEFAULT_SYMBOLS = (
    "XAUUSD",
    "XAGUSD",
    "NAS100",
    "US30_cash",
    "GBPUSD",
    "USDJPY",
    "GBPJPY",
)
DEFAULT_SYMBOL_ALIASES = {
    "US30_cash": "US30",
}
DEFAULT_GROUP_FILTERS = {
    "wgc": (
        "gold_etf_flows_monthly_total",
        "gold_demand_trends_gold_balance_total_demand_quarterly",
        "gold_demand_trends_gold_balance_total_supply_quarterly",
    ),
}
TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


@dataclass(frozen=True)
class PreparedGroup:
    source: str
    source_prefix: str
    prefix: str
    grouped: bool
    symbol_field: str
    rows_by_symbol: Mapping[str, tuple[list[tuple[datetime, datetime]], list[dict[str, Any]]]]


def parse_symbol_aliases(items: Iterable[str] | None) -> dict[str, str]:
    aliases = dict(DEFAULT_SYMBOL_ALIASES)
    for item in items or []:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"symbol alias must be FILE_SYMBOL:GTOS_SYMBOL, got {item!r}"
            )
        file_symbol, gtos_symbol = item.split(":", 1)
        aliases[file_symbol.strip()] = gtos_symbol.strip().upper()
    return aliases


def parse_group_filters(
    items: Iterable[str] | None,
    *,
    include_defaults: bool = True,
) -> dict[str, set[str]]:
    filters = {
        source: set(groups)
        for source, groups in DEFAULT_GROUP_FILTERS.items()
    } if include_defaults else {}
    for item in items or []:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"group filter must be SOURCE:GROUP_VALUE, got {item!r}"
            )
        source, group = item.split(":", 1)
        filters.setdefault(source.strip(), set()).add(group.strip())
    return filters


def load_candle_closes(
    csv_path: str | Path,
    *,
    timeframe: str = "M15",
    timestamp_kind: str = "open",
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    limit: int | None = None,
) -> list[dict[str, str]]:
    """Read MT5 candle rows and return bar-open + candle-close UTC strings."""

    timeframe_key = timeframe.upper()
    if timeframe_key not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    if timestamp_kind not in {"open", "close"}:
        raise ValueError("timestamp_kind must be 'open' or 'close'")

    start_dt = ensure_utc(start) if start else None
    end_dt = ensure_utc(end) if end else None
    delta = timedelta(minutes=TIMEFRAME_MINUTES[timeframe_key])
    output: list[dict[str, str]] = []
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "time" not in reader.fieldnames:
            raise ValueError(f"{csv_path}: missing required 'time' column")
        for row in reader:
            raw_time = str(row.get("time") or "").strip()
            if not raw_time:
                continue
            bar_time = _parse_mt5_time(raw_time)
            candle_close = bar_time if timestamp_kind == "close" else bar_time + delta
            if start_dt and candle_close < start_dt:
                continue
            if end_dt and candle_close > end_dt:
                continue
            output.append(
                {
                    "bar_time_utc": bar_time.isoformat(),
                    "candle_close_utc": candle_close.isoformat(),
                }
            )
            if limit is not None and len(output) >= limit:
                break
    return output


def build_historical_snapshots(
    *,
    store: ExternalFeedStore,
    data_dir: str | Path,
    symbols: Iterable[str],
    timeframe: str = "M15",
    timestamp_kind: str = "open",
    sources: Iterable[str] | None = None,
    symbol_aliases: Mapping[str, str] | None = None,
    group_filters: Mapping[str, Iterable[str]] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    limit_per_symbol: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build in-memory snapshots keyed by file symbol."""

    selected_sources = list(sources or sorted(SOURCE_REGISTRY))
    aliases = dict(symbol_aliases or DEFAULT_SYMBOL_ALIASES)
    source_rows = {
        source: store.read_latest_normalized_rows(source)
        for source in selected_sources
    }
    snapshot_index = prepare_snapshot_index(
        source_rows,
        group_filters=group_filters if group_filters is not None else DEFAULT_GROUP_FILTERS,
    )
    output: dict[str, list[dict[str, Any]]] = {}
    data_root = Path(data_dir)
    for file_symbol in symbols:
        csv_path = data_root / f"{file_symbol}_{timeframe.upper()}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"missing historical CSV: {csv_path}")
        gtos_symbol = aliases.get(file_symbol, file_symbol).upper()
        candle_rows = load_candle_closes(
            csv_path,
            timeframe=timeframe,
            timestamp_kind=timestamp_kind,
            start=start,
            end=end,
            limit=limit_per_symbol,
        )
        snapshots: list[dict[str, Any]] = []
        for candle_row in candle_rows:
            snapshot = build_snapshot_from_index(
                symbol=gtos_symbol,
                candle_close_utc=candle_row["candle_close_utc"],
                snapshot_index=snapshot_index,
            )
            snapshot["file_symbol"] = file_symbol
            snapshot["bar_time_utc"] = candle_row["bar_time_utc"]
            snapshots.append(snapshot)
        output[file_symbol] = snapshots
    return output


def prepare_snapshot_index(
    source_rows: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    group_filters: Mapping[str, Iterable[str]] | None = None,
) -> list[PreparedGroup]:
    filters = {
        source: {str(group) for group in groups}
        for source, groups in (group_filters or {}).items()
    }
    prepared: list[PreparedGroup] = []
    for source, rows in sorted(source_rows.items()):
        spec = SOURCE_REGISTRY[source]
        materialized_rows = [dict(row) for row in rows]
        if source in filters and spec.group_field:
            allowed = filters[source]
            materialized_rows = [
                row
                for row in materialized_rows
                if str(row.get(spec.group_field) or "") in allowed
            ]

        source_prefix = safe_slug(source)
        if spec.group_field:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for row in materialized_rows:
                group_value = row.get(spec.group_field)
                if group_value in (None, ""):
                    continue
                grouped.setdefault(str(group_value), []).append(row)
            for group_value, group_rows in sorted(grouped.items()):
                prepared.append(
                    PreparedGroup(
                        source=source,
                        source_prefix=source_prefix,
                        prefix=f"{source_prefix}__{safe_slug(group_value)}",
                        grouped=True,
                        symbol_field=spec.symbol_field,
                        rows_by_symbol=_prepare_rows_by_symbol(
                            group_rows,
                            time_field=spec.join_time_field,
                            symbol_field=spec.symbol_field,
                        ),
                    )
                )
            continue

        prepared.append(
            PreparedGroup(
                source=source,
                source_prefix=source_prefix,
                prefix=source_prefix,
                grouped=False,
                symbol_field=spec.symbol_field,
                rows_by_symbol=_prepare_rows_by_symbol(
                    materialized_rows,
                    time_field=spec.join_time_field,
                    symbol_field=spec.symbol_field,
                ),
            )
        )
    return prepared


def build_snapshot_from_index(
    *,
    symbol: str,
    candle_close_utc: str | datetime,
    snapshot_index: Iterable[PreparedGroup],
) -> dict[str, Any]:
    candle_close = ensure_utc(candle_close_utc)
    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "symbol": symbol.upper(),
        "candle_close_utc": candle_close.isoformat(),
    }
    grouped_sources: set[str] = set()
    available_grouped_sources: set[str] = set()
    for group in snapshot_index:
        if group.source == "lbma_calendar":
            _append_lbma_schedule_fields(snapshot, group, symbol.upper(), candle_close)
            continue
        selected = _select_prepared_row(group, symbol.upper(), candle_close)
        if group.grouped:
            grouped_sources.add(group.source_prefix)
        if selected is None:
            snapshot[f"{group.prefix}__available"] = False
            continue
        if group.grouped:
            available_grouped_sources.add(group.source_prefix)
        _append_snapshot_fields(snapshot, group.prefix, selected)
    for source_prefix in grouped_sources:
        snapshot[f"{source_prefix}__available"] = (
            source_prefix in available_grouped_sources
        )
    return snapshot


def _prepare_rows_by_symbol(
    rows: Iterable[Mapping[str, Any]],
    *,
    time_field: str,
    symbol_field: str,
) -> dict[str, tuple[list[tuple[datetime, datetime]], list[dict[str, Any]]]]:
    grouped: dict[str, list[tuple[datetime, datetime, dict[str, Any]]]] = {}
    for raw_row in rows:
        row = dict(raw_row)
        if time_field not in row:
            continue
        try:
            asof = ensure_utc(row[time_field])
        except (TypeError, ValueError):
            continue
        observation_time = _row_observation_time(row, fallback=asof)
        symbol_key = str(row.get(symbol_field) or "__GLOBAL__").upper()
        grouped.setdefault(symbol_key, []).append((asof, observation_time, row))

    prepared: dict[str, tuple[list[tuple[datetime, datetime]], list[dict[str, Any]]]] = {}
    for symbol_key, items in grouped.items():
        items.sort(key=lambda item: (item[0], item[1]))
        prepared[symbol_key] = (
            [(asof, observation) for asof, observation, _row in items],
            [_row for _asof, _observation, _row in items],
        )
    return prepared


def _select_prepared_row(
    group: PreparedGroup,
    symbol: str,
    candle_close: datetime,
) -> dict[str, Any] | None:
    selected: tuple[datetime, datetime, dict[str, Any]] | None = None
    for symbol_key in (symbol.upper(), "__GLOBAL__"):
        keys_and_rows = group.rows_by_symbol.get(symbol_key)
        if keys_and_rows is None:
            continue
        keys, rows = keys_and_rows
        idx = bisect_right(keys, (candle_close, datetime.max.replace(tzinfo=timezone.utc))) - 1
        if idx < 0:
            continue
        asof, observation = keys[idx]
        row = rows[idx]
        if selected is None or (asof, observation) > (selected[0], selected[1]):
            selected = (asof, observation, row)
    return selected[2] if selected else None


def _append_lbma_schedule_fields(
    snapshot: dict[str, Any],
    group: PreparedGroup,
    symbol: str,
    candle_close: datetime,
) -> None:
    """Append deterministic known-calendar LBMA fix proximity features.

    The generic as-of join only selects rows whose ``fix_time_utc`` is in the
    past. That is correct for benchmark prices, but not for the schedule: AM/PM
    fix times are known before the candle. Keep price-style fields tied to the
    previous fix while also exposing next-fix timing as deterministic calendar
    context.
    """

    previous_row, next_row = _select_adjacent_prepared_rows(
        group,
        symbol,
        candle_close,
    )
    prefix = group.prefix
    if previous_row is None and next_row is None:
        snapshot[f"{prefix}__available"] = False
        return

    snapshot[f"{prefix}__available"] = True
    if previous_row is not None:
        _append_snapshot_fields(snapshot, prefix, previous_row)
        previous_fix = ensure_utc(previous_row["fix_time_utc"])
        snapshot[f"{prefix}__previous_fix_time_utc"] = previous_fix.isoformat()
        snapshot[f"{prefix}__previous_fix_name"] = previous_row.get("fix_name")
        snapshot[f"{prefix}__previous_metal"] = previous_row.get("metal")
        snapshot[f"{prefix}__minutes_since_previous_fix"] = (
            candle_close - previous_fix
        ).total_seconds() / 60.0
    if next_row is not None:
        next_fix = ensure_utc(next_row["fix_time_utc"])
        snapshot[f"{prefix}__next_fix_time_utc"] = next_fix.isoformat()
        snapshot[f"{prefix}__next_fix_name"] = next_row.get("fix_name")
        snapshot[f"{prefix}__next_metal"] = next_row.get("metal")
        snapshot[f"{prefix}__minutes_to_next_fix"] = (
            next_fix - candle_close
        ).total_seconds() / 60.0
        snapshot[f"{prefix}__next_uk_us_dst_misalignment"] = next_row.get(
            "uk_us_dst_misalignment"
        )

    minutes_since = snapshot.get(f"{prefix}__minutes_since_previous_fix")
    minutes_to = snapshot.get(f"{prefix}__minutes_to_next_fix")
    snapshot[f"{prefix}__in_fix_window_30m"] = (
        (minutes_since is not None and 0.0 <= float(minutes_since) <= 30.0)
        or (minutes_to is not None and 0.0 <= float(minutes_to) <= 30.0)
    )


def _select_adjacent_prepared_rows(
    group: PreparedGroup,
    symbol: str,
    candle_close: datetime,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    previous: tuple[datetime, datetime, dict[str, Any]] | None = None
    next_item: tuple[datetime, datetime, dict[str, Any]] | None = None
    for symbol_key in (symbol.upper(), "__GLOBAL__"):
        keys_and_rows = group.rows_by_symbol.get(symbol_key)
        if keys_and_rows is None:
            continue
        keys, rows = keys_and_rows
        idx = bisect_right(
            keys,
            (candle_close, datetime.max.replace(tzinfo=timezone.utc)),
        ) - 1
        if idx >= 0:
            asof, observation = keys[idx]
            candidate = (asof, observation, rows[idx])
            if previous is None or (asof, observation) > (previous[0], previous[1]):
                previous = candidate
        next_idx = idx + 1
        if 0 <= next_idx < len(rows):
            asof, observation = keys[next_idx]
            candidate = (asof, observation, rows[next_idx])
            if next_item is None or (asof, observation) < (next_item[0], next_item[1]):
                next_item = candidate
    return (
        previous[2] if previous else None,
        next_item[2] if next_item else None,
    )


def _append_snapshot_fields(
    snapshot: dict[str, Any],
    prefix: str,
    selected: Mapping[str, Any],
) -> None:
    snapshot[f"{prefix}__available"] = True
    for key, value in selected.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            snapshot[f"{prefix}__{key}"] = value
        elif isinstance(value, datetime):
            snapshot[f"{prefix}__{key}"] = value.isoformat()


def _row_observation_time(
    row: Mapping[str, Any],
    *,
    fallback: datetime,
) -> datetime:
    for field in (
        "observation_date",
        "report_date",
        "fix_time_utc",
        "as_of_utc",
        "trading_date_london",
    ):
        value = row.get(field)
        if value in (None, ""):
            continue
        try:
            return ensure_utc(value)
        except (TypeError, ValueError):
            continue
    return fallback


def write_historical_snapshots(
    *,
    store: ExternalFeedStore,
    snapshots_by_symbol: Mapping[str, Iterable[Mapping[str, Any]]],
    timeframe: str,
    label: str | None = None,
) -> dict[str, Path]:
    """Write snapshots as one JSONL file per file symbol."""

    stamp = utc_now()
    rendered_label = safe_slug(label or f"historical_{timeframe.upper()}")
    paths: dict[str, Path] = {}
    for file_symbol, snapshots in snapshots_by_symbol.items():
        symbol_dir = store.feature_dir(file_symbol)
        symbol_dir.mkdir(parents=True, exist_ok=True)
        target = symbol_dir / f"{rendered_label}_{stamp:%Y%m%dT%H%M%SZ}.jsonl"
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for snapshot in snapshots:
                handle.write(json.dumps(dict(snapshot), sort_keys=True) + "\n")
        paths[file_symbol] = target
    return paths


def _parse_mt5_time(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external)",
    )
    parser.add_argument(
        "--data-dir",
        default="data/historical_2026",
        help="Directory containing MT5 CSV exports.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        help="File symbol to process; repeatable. Default uses Phase 3 target set.",
    )
    parser.add_argument("--timeframe", default="M15", choices=sorted(TIMEFRAME_MINUTES))
    parser.add_argument(
        "--timestamp-kind",
        choices=("open", "close"),
        default="open",
        help="Whether CSV time is bar open or candle close. MT5 exports use open.",
    )
    parser.add_argument("--start", help="Start candle-close timestamp/date")
    parser.add_argument("--end", help="End candle-close timestamp/date")
    parser.add_argument(
        "--source",
        action="append",
        choices=sorted(SOURCE_REGISTRY),
        help="Source to include; repeatable. Default includes all registered sources.",
    )
    parser.add_argument(
        "--symbol-alias",
        action="append",
        help="Map CSV file symbol to GTOS symbol, e.g. US30_cash:US30.",
    )
    parser.add_argument(
        "--group",
        action="append",
        help=(
            "Restrict a grouped source to SOURCE:GROUP_VALUE. Defaults keep only "
            "the frozen WGC context groups; repeat to add more."
        ),
    )
    parser.add_argument(
        "--all-groups",
        action="store_true",
        help="Disable default grouped-source filters. Can create huge artifacts.",
    )
    parser.add_argument(
        "--limit-per-symbol",
        type=int,
        help="Limit candles per symbol for smoke runs.",
    )
    parser.add_argument("--write", action="store_true", help="Write JSONL artifacts.")
    parser.add_argument("--label", help="Output label used with --write.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = ExternalFeedStore(args.root)
    symbols = args.symbol or list(DEFAULT_SYMBOLS)
    snapshots_by_symbol = build_historical_snapshots(
        store=store,
        data_dir=args.data_dir,
        symbols=symbols,
        timeframe=args.timeframe,
        timestamp_kind=args.timestamp_kind,
        sources=args.source,
        symbol_aliases=parse_symbol_aliases(args.symbol_alias),
        group_filters=parse_group_filters(
            args.group,
            include_defaults=not args.all_groups,
        ),
        start=args.start,
        end=args.end,
        limit_per_symbol=args.limit_per_symbol,
    )
    summary = {
        "root": str(Path(args.root)),
        "data_dir": str(Path(args.data_dir)),
        "timeframe": args.timeframe,
        "timestamp_kind": args.timestamp_kind,
        "symbols": {
            symbol: {
                "snapshots": len(snapshots),
                "first": snapshots[0]["candle_close_utc"] if snapshots else None,
                "last": snapshots[-1]["candle_close_utc"] if snapshots else None,
            }
            for symbol, snapshots in snapshots_by_symbol.items()
        },
    }
    if args.write:
        paths = write_historical_snapshots(
            store=store,
            snapshots_by_symbol=snapshots_by_symbol,
            timeframe=args.timeframe,
            label=args.label,
        )
        summary["written"] = {symbol: str(path) for symbol, path in paths.items()}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
