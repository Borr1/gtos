#!/usr/bin/env python3
"""Build Phase 3 external-feed validation rows from snapshots + MT5 candles.

The historical snapshot generator freezes what external data was available at
each candle close. This utility adds strictly future-only OHLCV labels and fold
metadata so validation can start without touching live trading code.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    SCHEMA_VERSION,
    ensure_utc,
    safe_slug,
    utc_now,
)


DEFAULT_HORIZONS = (1, 4, 12, 96)
TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}
TIMESTAMP_SUFFIXES = (
    "__published_at_utc",
    "__as_of_utc",
    "__fix_time_utc",
)
DEFAULT_SNAPSHOT_GLOB = "*/*.jsonl"


@dataclass(frozen=True)
class Candle:
    """One MT5 OHLCV bar with an explicit close timestamp."""

    bar_time_utc: datetime
    candle_close_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


def load_mt5_candles(
    csv_path: str | Path,
    *,
    timeframe: str = "M15",
    timestamp_kind: str = "open",
) -> list[Candle]:
    """Load MT5 CSV candles and normalize bar/candle-close timestamps."""

    timeframe_key = timeframe.upper()
    if timeframe_key not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    if timestamp_kind not in {"open", "close"}:
        raise ValueError("timestamp_kind must be 'open' or 'close'")

    delta = timedelta(minutes=TIMEFRAME_MINUTES[timeframe_key])
    candles: list[Candle] = []
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"time", "open", "high", "low", "close"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"{csv_path}: missing required OHLC columns")
        for row in reader:
            bar_time = _parse_mt5_time(str(row["time"]))
            candle_close = bar_time if timestamp_kind == "close" else bar_time + delta
            candles.append(
                Candle(
                    bar_time_utc=bar_time,
                    candle_close_utc=candle_close,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=_float_or_none(row.get("volume")),
                )
            )
    candles.sort(key=lambda candle: candle.candle_close_utc)
    return candles


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_validation_rows(
    *,
    snapshot_rows: Iterable[Mapping[str, Any]],
    candles: Iterable[Candle],
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    bundle_id: str,
    source_snapshot_path: str | Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Join snapshot rows to future-only OHLCV labels."""

    horizon_list = sorted({int(horizon) for horizon in horizons})
    if any(horizon <= 0 for horizon in horizon_list):
        raise ValueError("horizons must be positive bar counts")

    candle_list = sorted(candles, key=lambda candle: candle.candle_close_utc)
    candles_by_close = {
        candle.candle_close_utc.isoformat(): idx
        for idx, candle in enumerate(candle_list)
    }

    rows: list[dict[str, Any]] = []
    skipped_missing_candle = 0
    for raw_snapshot in snapshot_rows:
        snapshot = dict(raw_snapshot)
        candle_close = ensure_utc(str(snapshot["candle_close_utc"]))
        validate_snapshot_no_lookahead(snapshot, candle_close)
        idx = candles_by_close.get(candle_close.isoformat())
        if idx is None:
            skipped_missing_candle += 1
            continue
        candle = candle_list[idx]
        row = dict(snapshot)
        row.update(
            {
                "validation_schema_version": "external_feed_validation_v1",
                "external_snapshot_schema_version": snapshot.get("schema_version", SCHEMA_VERSION),
                "bundle_id": bundle_id,
                "source_snapshot_path": str(source_snapshot_path) if source_snapshot_path else None,
                "label_bar_time_utc": candle.bar_time_utc.isoformat(),
                "label_close_price": candle.close,
                "fold_month": candle_close.strftime("%Y-%m"),
                "fold_quarter": f"{candle_close.year}Q{((candle_close.month - 1) // 3) + 1}",
                "fold_iso_week": f"{candle_close.isocalendar().year}-W{candle_close.isocalendar().week:02d}",
            }
        )
        row.update(_future_labels(candle_list, idx, horizon_list))
        rows.append(row)

    summary = summarize_validation_rows(
        rows,
        horizons=horizon_list,
        skipped_missing_candle=skipped_missing_candle,
    )
    return rows, summary


def summarize_validation_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    horizons: Iterable[int],
    skipped_missing_candle: int = 0,
) -> dict[str, Any]:
    materialized = [dict(row) for row in rows]
    horizon_list = list(horizons)
    symbols = sorted({str(row.get("file_symbol") or row.get("symbol") or "") for row in materialized})
    months = sorted({str(row.get("fold_month")) for row in materialized if row.get("fold_month")})
    weeks = sorted({str(row.get("fold_iso_week")) for row in materialized if row.get("fold_iso_week")})
    source_availability = _source_availability(materialized)
    label_coverage = {
        str(horizon): {
            "available_rows": sum(
                1 for row in materialized if row.get(f"label_h{horizon}__has_full_horizon")
            ),
            "missing_rows": sum(
                1 for row in materialized if not row.get(f"label_h{horizon}__has_full_horizon")
            ),
        }
        for horizon in horizon_list
    }
    return {
        "schema_version": "external_feed_validation_summary_v1",
        "rows": len(materialized),
        "skipped_missing_candle": skipped_missing_candle,
        "symbols": symbols,
        "fold_months": len(months),
        "fold_iso_weeks": len(weeks),
        "first_candle_close_utc": materialized[0]["candle_close_utc"] if materialized else None,
        "last_candle_close_utc": materialized[-1]["candle_close_utc"] if materialized else None,
        "label_coverage": label_coverage,
        "source_availability": source_availability,
        "mean_forward_return_by_horizon": _mean_forward_returns(materialized, horizon_list),
    }


def validate_snapshot_no_lookahead(
    snapshot: Mapping[str, Any],
    candle_close_utc: datetime | str,
) -> None:
    """Fail if timestamped source fields are after the candle close."""

    candle_close = ensure_utc(candle_close_utc)
    violations: list[str] = []
    for key, value in snapshot.items():
        if value in (None, "") or not key.endswith(TIMESTAMP_SUFFIXES):
            continue
        try:
            ts = ensure_utc(str(value))
        except (TypeError, ValueError):
            continue
        if ts > candle_close:
            violations.append(f"{key}={ts.isoformat()}")
    if violations:
        raise ValueError(
            "snapshot contains future source timestamp(s) for "
            f"{candle_close.isoformat()}: {', '.join(violations[:8])}"
        )


def find_latest_snapshot_paths(
    root: str | Path = DEFAULT_EXTERNAL_DATA_ROOT / "features",
    *,
    pattern: str = DEFAULT_SNAPSHOT_GLOB,
    label_contains: str | None = None,
) -> list[Path]:
    """Return the latest snapshot JSONL per feature-symbol directory."""

    root_path = Path(root)
    latest: dict[str, tuple[datetime, Path]] = {}
    for path in root_path.glob(pattern):
        if not path.is_file() or path.suffix != ".jsonl":
            continue
        if label_contains and label_contains not in path.name:
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        key = path.parent.name.upper()
        current = latest.get(key)
        if current is None or mtime > current[0]:
            latest[key] = (mtime, path)
    return [path for _mtime, path in sorted(latest.values(), key=lambda item: str(item[1]))]


def write_validation_artifacts(
    *,
    root: str | Path,
    bundle_id: str,
    label: str,
    rows_by_symbol: Mapping[str, Iterable[Mapping[str, Any]]],
    summaries_by_symbol: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    stamp = utc_now()
    output_dir = Path(root) / "validation" / safe_slug(bundle_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = safe_slug(label)
    written: dict[str, str] = {}
    summary = {
        "schema_version": "external_feed_validation_run_v1",
        "bundle_id": bundle_id,
        "label": safe_label,
        "created_at_utc": stamp.isoformat(),
        "symbols": {},
    }
    for symbol, rows in sorted(rows_by_symbol.items()):
        materialized = [dict(row) for row in rows]
        target = output_dir / f"{safe_label}_{safe_slug(symbol)}_{stamp:%Y%m%dT%H%M%SZ}.jsonl"
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for row in materialized:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        written[symbol] = str(target)
        summary["symbols"][symbol] = dict(summaries_by_symbol[symbol])
    summary["written"] = written
    summary_path = output_dir / f"{safe_label}_summary_{stamp:%Y%m%dT%H%M%SZ}.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary["summary_path"] = str(summary_path)
    return summary


def _future_labels(candles: list[Candle], idx: int, horizons: Iterable[int]) -> dict[str, Any]:
    current = candles[idx]
    labels: dict[str, Any] = {}
    for horizon in horizons:
        prefix = f"label_h{horizon}"
        end_idx = idx + horizon
        if end_idx >= len(candles):
            labels[f"{prefix}__has_full_horizon"] = False
            labels[f"{prefix}__future_close_utc"] = None
            labels[f"{prefix}__forward_return"] = None
            labels[f"{prefix}__forward_points"] = None
            labels[f"{prefix}__max_up_return"] = None
            labels[f"{prefix}__max_down_return"] = None
            labels[f"{prefix}__realized_range_return"] = None
            continue
        future_window = candles[idx + 1 : end_idx + 1]
        future_close = candles[end_idx]
        max_high = max(candle.high for candle in future_window)
        min_low = min(candle.low for candle in future_window)
        labels[f"{prefix}__has_full_horizon"] = True
        labels[f"{prefix}__future_close_utc"] = future_close.candle_close_utc.isoformat()
        labels[f"{prefix}__forward_return"] = (future_close.close - current.close) / current.close
        labels[f"{prefix}__forward_points"] = future_close.close - current.close
        labels[f"{prefix}__max_up_return"] = (max_high - current.close) / current.close
        labels[f"{prefix}__max_down_return"] = (min_low - current.close) / current.close
        labels[f"{prefix}__realized_range_return"] = (max_high - min_low) / current.close
    return labels


def _source_availability(rows: list[dict[str, Any]]) -> dict[str, int]:
    keys = sorted(
        key
        for row in rows
        for key, value in row.items()
        if key.endswith("__available") and isinstance(value, bool)
    )
    return {
        key: sum(1 for row in rows if row.get(key) is True)
        for key in sorted(set(keys))
    }


def _mean_forward_returns(rows: list[dict[str, Any]], horizons: Iterable[int]) -> dict[str, float | None]:
    output: dict[str, float | None] = {}
    for horizon in horizons:
        key = f"label_h{horizon}__forward_return"
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        output[str(horizon)] = mean(values) if values else None
    return output


def _infer_file_symbol(snapshot_path: Path, first_snapshot: Mapping[str, Any]) -> str:
    if first_snapshot.get("file_symbol"):
        return str(first_snapshot["file_symbol"])
    symbol = str(first_snapshot.get("symbol") or snapshot_path.parent.name)
    if symbol.upper() == "US30_CASH":
        return "US30_cash"
    return symbol


def _parse_mt5_time(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


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
    parser.add_argument("--timeframe", default="M15", choices=sorted(TIMEFRAME_MINUTES))
    parser.add_argument(
        "--timestamp-kind",
        choices=("open", "close"),
        default="open",
        help="Whether CSV time is bar open or candle close. MT5 exports use open.",
    )
    parser.add_argument(
        "--snapshot",
        action="append",
        help="Snapshot JSONL to label; repeatable. Default uses latest per feature symbol.",
    )
    parser.add_argument(
        "--snapshot-label-contains",
        default="phase3_m15_2025_2026_external_v3",
        help="When --snapshot is omitted, restrict auto-discovery to filenames containing this string.",
    )
    parser.add_argument(
        "--horizon-bars",
        action="append",
        type=int,
        help="Forward label horizon in bars; repeatable. Default: 1, 4, 12, 96.",
    )
    parser.add_argument(
        "--bundle-id",
        default="calendar_macro_bundle_v1",
        help="Registered bundle id to stamp into rows.",
    )
    parser.add_argument(
        "--label",
        default="phase3_m15_validation_v1",
        help="Output label used with --write.",
    )
    parser.add_argument("--write", action="store_true", help="Write validation JSONL artifacts.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    snapshot_paths = [
        Path(path) for path in args.snapshot
    ] if args.snapshot else find_latest_snapshot_paths(
        root / "features",
        label_contains=args.snapshot_label_contains,
    )
    if not snapshot_paths:
        raise FileNotFoundError("no snapshot JSONL files found")
    horizons = args.horizon_bars or list(DEFAULT_HORIZONS)

    rows_by_symbol: dict[str, list[dict[str, Any]]] = {}
    summaries_by_symbol: dict[str, dict[str, Any]] = {}
    for snapshot_path in snapshot_paths:
        snapshots = load_jsonl(snapshot_path)
        if not snapshots:
            continue
        file_symbol = _infer_file_symbol(snapshot_path, snapshots[0])
        candle_path = Path(args.data_dir) / f"{file_symbol}_{args.timeframe.upper()}.csv"
        candles = load_mt5_candles(
            candle_path,
            timeframe=args.timeframe,
            timestamp_kind=args.timestamp_kind,
        )
        rows, summary = build_validation_rows(
            snapshot_rows=snapshots,
            candles=candles,
            horizons=horizons,
            bundle_id=args.bundle_id,
            source_snapshot_path=snapshot_path,
        )
        rows_by_symbol[file_symbol] = rows
        summaries_by_symbol[file_symbol] = summary

    run_summary = {
        "schema_version": "external_feed_validation_run_v1",
        "bundle_id": args.bundle_id,
        "snapshot_paths": [str(path) for path in snapshot_paths],
        "symbols": summaries_by_symbol,
    }
    if args.write:
        run_summary = write_validation_artifacts(
            root=root,
            bundle_id=args.bundle_id,
            label=args.label,
            rows_by_symbol=rows_by_symbol,
            summaries_by_symbol=summaries_by_symbol,
        )
    print(json.dumps(run_summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
