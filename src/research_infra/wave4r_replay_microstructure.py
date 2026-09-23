"""Wave4R replay microstructure and day-risk helpers.

These helpers keep three ideas separate:

* decision inputs are bounded at the candidate as-of time;
* outcome path can read forward price action after the candidate;
* read-only historical MT5 hydration is market-data capture, not broker order
  mutation.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
from hashlib import sha256
from typing import Any, Iterable, Mapping, Protocol


class HistoricalMarketDataProvider(Protocol):
    def get_candles_range(self, symbol: str, timeframe: int, date_from: datetime, date_to: datetime) -> list[dict]:
        ...

    def get_ticks_range(self, symbol: str, date_from: datetime, date_to: datetime) -> list[dict]:
        ...


@dataclass(frozen=True)
class DayHydrationResult:
    day: str
    symbols: list[str]
    root: Path
    m1_rows: int
    tick_rows: int
    replaced_previous_day: bool
    decision_input_boundary: str
    outcome_path_boundary: str
    manifest_path: Path | None = None


@dataclass(frozen=True)
class LimitFillInference:
    status: str
    filled: bool
    fill_time_utc: str | None
    fill_price: float | None
    source: str
    source_row_count: int


@dataclass(frozen=True)
class OrderedPathOracleResult:
    status: str
    source: str
    source_row_count: int
    side: str
    asof_utc: str
    entry_price: float
    stop_price: float
    target_price: float
    risk_distance: float | None
    target_r: float | None
    fill_status: str
    fill_time_utc: str | None
    fill_price: float | None
    terminal_outcome: str
    entry_fill_executable: bool | None = None
    entry_fill_authority_status: str | None = None
    entry_fill_authority_reason: str | None = None
    entry_fill_authority_source_boundary: str | None = None
    terminal_r_scoreable: bool = False
    terminal_r_scoreability_status: str = "not_filled_no_terminal_r"
    terminal_r_scoreability_reason: str | None = None
    terminal_r_diagnostic_outcome: str | None = None
    entry_first_touch_utc: str | None = None
    passive_limit_queue_touch_count: int = 0
    passive_limit_queue_max_penetration_price: float | None = None
    passive_limit_queue_max_penetration_r: float | None = None
    passive_limit_queue_penetrated_beyond_limit: bool | None = None
    passive_limit_queue_realism_required: bool = False
    passive_limit_queue_realism_min_penetration_r: float | None = None
    passive_limit_queue_realism_min_touch_count: int | None = None
    passive_limit_queue_realism_passed: bool | None = None
    fill_realism_class: str | None = None
    fill_realism_executable: bool | None = None
    fill_realism_reason: str | None = None
    fill_realism_source_boundary: str | None = None
    fill_realism_queue_model: str | None = None
    fill_realism_diagnostic_fill_status: str | None = None
    fill_realism_diagnostic_fill_time_utc: str | None = None
    fill_realism_diagnostic_fill_price: float | None = None
    fill_realism_diagnostic_terminal_outcome: str | None = None
    diagnostic_fill_only: bool = False
    package_execution_result_scope: str | None = None
    target_first_touch_utc: str | None = None
    stop_first_touch_utc: str | None = None
    same_bar_ambiguity: bool = False
    mfe_r: float | None = None
    mfe_time_utc: str | None = None
    mae_r: float | None = None
    mae_time_utc: str | None = None
    adverse_before_profit_flag: bool | None = None
    adverse_before_profit_status: str = "not_evaluated"
    milestones: dict[str, dict[str, Any]] = field(default_factory=dict)
    source_gaps: tuple[str, ...] = field(default_factory=tuple)
    decision_input_boundary: str = (
        "asof_safe_inputs_must_filter_rows_at_or_before_candidate_asof"
    )
    outcome_path_boundary: str = (
        "post_asof_ordered_price_path_allowed_only_for_replay_labels"
    )
    broker_real_boundary: str = "no_broker_real_cost_or_order_lifecycle_claim"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DayPropDecision:
    candidate_id: str
    asof_utc: str
    requested_risk_r: float
    result_r: float


def parse_utc(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_day_bounds(day: str | date) -> tuple[datetime, datetime]:
    if isinstance(day, date):
        parsed = day
    else:
        parsed = date.fromisoformat(str(day))
    start = datetime.combine(parsed, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def session_bounds(day: str | date, start_hhmm: str | None, end_hhmm: str | None) -> tuple[datetime, datetime]:
    day_start, day_end = utc_day_bounds(day)
    if not start_hhmm or not end_hhmm:
        return day_start, day_end
    start_hour, start_minute = [int(part) for part in start_hhmm.split(":", 1)]
    end_hour, end_minute = [int(part) for part in end_hhmm.split(":", 1)]
    start = datetime.combine(day_start.date(), time(start_hour, start_minute), tzinfo=timezone.utc)
    end = datetime.combine(day_start.date(), time(end_hour, end_minute), tzinfo=timezone.utc)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def _atomic_write_csv(path: Path, rows: list[Mapping[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})
    os.replace(str(tmp), str(path))


def _atomic_write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    count = 0
    with tmp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")
            count += 1
    os.replace(str(tmp), str(path))
    return count


def load_m1_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_tick_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_day_hydration_root(root: Path, day: str) -> bool:
    root.mkdir(parents=True, exist_ok=True)
    replaced = False
    for child in root.iterdir():
        if child.is_dir() and child.name != day:
            shutil.rmtree(child)
            replaced = True
    target = root / day
    if target.exists():
        shutil.rmtree(target)
        replaced = True
    target.mkdir(parents=True, exist_ok=True)
    return replaced


def hydrate_readonly_mt5_day_session(
    *,
    provider: HistoricalMarketDataProvider,
    symbols: Mapping[str, str],
    day: str,
    root: Path,
    timeframe_m1: int,
    session_id: str = "full_day",
    session_start_utc: str | None = None,
    session_end_utc: str | None = None,
    include_ticks: bool = True,
    replace_previous_day: bool = True,
) -> DayHydrationResult:
    """Fetch one UTC replay day/session of M1 and tick data into a scratch root."""

    start, end = session_bounds(day, session_start_utc, session_end_utc)
    replaced = replace_day_hydration_root(root, day) if replace_previous_day else False
    day_root = root / day / session_id
    total_m1_rows = 0
    total_tick_rows = 0
    manifest_files: list[dict[str, Any]] = []
    for canonical_symbol, broker_symbol in symbols.items():
        candles = provider.get_candles_range(broker_symbol, timeframe_m1, start, end)
        candle_rows = [
            {
                "time_utc": (row.get("time") or row.get("time_utc")),
                "symbol": canonical_symbol,
                "broker_symbol": broker_symbol,
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
            }
            for row in candles
        ]
        total_m1_rows += len(candle_rows)
        m1_path = day_root / "m1" / f"{canonical_symbol}.csv"
        _atomic_write_csv(
            m1_path,
            candle_rows,
            ["time_utc", "symbol", "broker_symbol", "open", "high", "low", "close", "volume"],
        )
        manifest_files.append(
            {
                "kind": "m1",
                "symbol": canonical_symbol,
                "path": str(m1_path),
                "rows": len(candle_rows),
                "sha256": _file_sha256(m1_path),
            }
        )
        if include_ticks:
            ticks = provider.get_ticks_range(broker_symbol, start, end)
            tick_rows = [
                {
                    "ts_utc": row.get("ts_utc") or row.get("time"),
                    "symbol": canonical_symbol,
                    "broker_symbol": broker_symbol,
                    "bid": row.get("bid"),
                    "ask": row.get("ask"),
                    "last": row.get("last"),
                    "volume": row.get("volume"),
                    "flags": row.get("flags"),
                    "time_msc": row.get("time_msc"),
                }
                for row in ticks
            ]
            tick_path = day_root / "ticks" / f"{canonical_symbol}.jsonl"
            tick_count = _atomic_write_jsonl(tick_path, tick_rows)
            total_tick_rows += tick_count
            manifest_files.append(
                {
                    "kind": "tick",
                    "symbol": canonical_symbol,
                    "path": str(tick_path),
                    "rows": tick_count,
                    "sha256": _file_sha256(tick_path),
                }
            )
    manifest_path = day_root / "WAVE4R_MT5_DAY_SESSION_HYDRATION_MANIFEST.json"
    manifest = {
        "schema_version": "wave4r_mt5_day_session_hydration_manifest_v1",
        "day": day,
        "session_id": session_id,
        "request_start_utc": start.isoformat(),
        "request_end_utc": end.isoformat(),
        "symbols": dict(symbols),
        "include_ticks": include_ticks,
        "replace_previous_day": replace_previous_day,
        "replaced_previous_day": replaced,
        "m1_rows": total_m1_rows,
        "tick_rows": total_tick_rows,
        "files": manifest_files,
        "decision_input_boundary": "asof_safe_inputs_must_filter_rows_at_or_before_candidate_asof",
        "outcome_path_boundary": "post_asof_price_path_allowed_only_for_result_scoring",
        "broker_order_mutation": False,
        "storage_policy": "scratch_day_session_root_prunes_previous_day_before_next_hydration",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return DayHydrationResult(
        day=day,
        symbols=sorted(symbols),
        root=day_root,
        m1_rows=total_m1_rows,
        tick_rows=total_tick_rows,
        replaced_previous_day=replaced,
        decision_input_boundary="asof_safe_inputs_must_filter_rows_at_or_before_candidate_asof",
        outcome_path_boundary="post_asof_price_path_allowed_only_for_result_scoring",
        manifest_path=manifest_path,
    )


def hydrate_readonly_mt5_day(
    *,
    provider: HistoricalMarketDataProvider,
    symbols: Mapping[str, str],
    day: str,
    root: Path,
    timeframe_m1: int,
    include_ticks: bool = True,
    replace_previous_day: bool = True,
) -> DayHydrationResult:
    return hydrate_readonly_mt5_day_session(
        provider=provider,
        symbols=symbols,
        day=day,
        root=root,
        timeframe_m1=timeframe_m1,
        include_ticks=include_ticks,
        replace_previous_day=replace_previous_day,
    )


def split_decision_and_outcome_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    asof_utc: str,
    time_key: str,
) -> dict[str, list[dict[str, Any]]]:
    asof = parse_utc(asof_utc)
    decision: list[dict[str, Any]] = []
    outcome: list[dict[str, Any]] = []
    if asof is None:
        return {"decision_input_rows": decision, "outcome_path_rows": outcome}
    for row in rows:
        ts = parse_utc(row.get(time_key))
        if ts is None:
            continue
        target = decision if ts <= asof else outcome
        target.append(dict(row))
    return {"decision_input_rows": decision, "outcome_path_rows": outcome}


def infer_limit_fill_from_ticks(
    *,
    ticks: Iterable[Mapping[str, Any]],
    side: str,
    entry_price: float,
    asof_utc: str,
) -> LimitFillInference:
    asof = parse_utc(asof_utc)
    if asof is None:
        return LimitFillInference("missing_asof", False, None, None, "tick", 0)
    side_upper = side.upper()
    count = 0
    for tick in sorted(ticks, key=lambda row: str(row.get("ts_utc") or row.get("time") or "")):
        count += 1
        ts = parse_utc(tick.get("ts_utc") or tick.get("time"))
        if ts is None or ts <= asof:
            continue
        bid = _float(tick.get("bid"))
        ask = _float(tick.get("ask"))
        if side_upper in {"LONG", "BUY"} and ask is not None and ask <= entry_price:
            return LimitFillInference("filled", True, ts.isoformat(), entry_price, "tick_ask", count)
        if side_upper in {"SHORT", "SELL"} and bid is not None and bid >= entry_price:
            return LimitFillInference("filled", True, ts.isoformat(), entry_price, "tick_bid", count)
    return LimitFillInference("not_filled_in_tick_path", False, None, None, "tick", count)


def infer_limit_fill_from_m1(
    *,
    bars: Iterable[Mapping[str, Any]],
    side: str,
    entry_price: float,
    asof_utc: str,
) -> LimitFillInference:
    asof = parse_utc(asof_utc)
    if asof is None:
        return LimitFillInference("missing_asof", False, None, None, "m1", 0)
    side_upper = side.upper()
    count = 0
    for bar in sorted(bars, key=lambda row: str(row.get("time_utc") or row.get("time") or "")):
        count += 1
        ts = parse_utc(bar.get("time_utc") or bar.get("time"))
        if ts is None or ts <= asof:
            continue
        low = _float(bar.get("low"))
        high = _float(bar.get("high"))
        if side_upper in {"LONG", "BUY"} and low is not None and low <= entry_price:
            return LimitFillInference("filled", True, ts.isoformat(), entry_price, "m1_low", count)
        if side_upper in {"SHORT", "SELL"} and high is not None and high >= entry_price:
            return LimitFillInference("filled", True, ts.isoformat(), entry_price, "m1_high", count)
    return LimitFillInference("not_filled_in_m1_path", False, None, None, "m1", count)


def infer_ordered_path_from_m1(
    *,
    bars: Iterable[Mapping[str, Any]],
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    asof_utc: str,
    fill_already_confirmed: bool = False,
    fill_time_utc: str | None = None,
    passive_limit_queue_realism_enabled: bool = False,
    passive_limit_queue_min_penetration_r: float = 0.0,
    passive_limit_queue_min_touch_count: int = 1,
    milestone_rs: Iterable[float] = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0),
) -> OrderedPathOracleResult:
    """Resolve replay fill, target/stop order, MFE/MAE, and milestones from M1 bars.

    M1 bars are ordered across rows, but not inside each row. If target and stop
    are both touched in the same M1 bar after fill, the result stays ambiguous
    and carries an explicit lower-timeframe/tick source requirement.
    """

    return _infer_ordered_path(
        rows=bars,
        side=side,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        asof_utc=asof_utc,
        source="m1",
        time_keys=("time_utc", "time"),
        fill_already_confirmed=fill_already_confirmed,
        fill_time_utc=fill_time_utc,
        passive_limit_queue_realism_enabled=passive_limit_queue_realism_enabled,
        passive_limit_queue_min_penetration_r=passive_limit_queue_min_penetration_r,
        passive_limit_queue_min_touch_count=passive_limit_queue_min_touch_count,
        milestone_rs=tuple(milestone_rs),
    )


def infer_ordered_path_from_ticks(
    *,
    ticks: Iterable[Mapping[str, Any]],
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    asof_utc: str,
    fill_already_confirmed: bool = False,
    fill_time_utc: str | None = None,
    passive_limit_queue_realism_enabled: bool = False,
    passive_limit_queue_min_penetration_r: float = 0.0,
    passive_limit_queue_min_touch_count: int = 1,
    milestone_rs: Iterable[float] = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0),
) -> OrderedPathOracleResult:
    """Resolve replay path from ordered ticks using side-aware bid/ask prices."""

    return _infer_ordered_path(
        rows=ticks,
        side=side,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        asof_utc=asof_utc,
        source="tick",
        time_keys=("ts_utc", "time_utc", "time"),
        fill_already_confirmed=fill_already_confirmed,
        fill_time_utc=fill_time_utc,
        passive_limit_queue_realism_enabled=passive_limit_queue_realism_enabled,
        passive_limit_queue_min_penetration_r=passive_limit_queue_min_penetration_r,
        passive_limit_queue_min_touch_count=passive_limit_queue_min_touch_count,
        milestone_rs=tuple(milestone_rs),
    )


def infer_ordered_path_from_local_files(
    *,
    m1_path: Path | None = None,
    tick_path: Path | None = None,
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    asof_utc: str,
    fill_already_confirmed: bool = False,
    fill_time_utc: str | None = None,
    prefer_ticks: bool = True,
    passive_limit_queue_realism_enabled: bool = False,
    passive_limit_queue_min_penetration_r: float = 0.0,
    passive_limit_queue_min_touch_count: int = 1,
    milestone_rs: Iterable[float] = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0),
) -> OrderedPathOracleResult:
    """Resolve ordered path from lane-owned scratch files.

    Ticks are preferred when present because they can break same-M1 target/stop
    ambiguity. Empty or missing files return an explicit source gap instead of
    pretending the path is resolved.
    """

    tick_rows = load_tick_jsonl_rows(tick_path) if tick_path else []
    m1_rows = load_m1_csv_rows(m1_path) if m1_path else []
    if prefer_ticks and tick_rows:
        return infer_ordered_path_from_ticks(
            ticks=tick_rows,
            side=side,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            asof_utc=asof_utc,
            fill_already_confirmed=fill_already_confirmed,
            fill_time_utc=fill_time_utc,
            passive_limit_queue_realism_enabled=passive_limit_queue_realism_enabled,
            passive_limit_queue_min_penetration_r=passive_limit_queue_min_penetration_r,
            passive_limit_queue_min_touch_count=passive_limit_queue_min_touch_count,
            milestone_rs=milestone_rs,
        )
    if m1_rows:
        return infer_ordered_path_from_m1(
            bars=m1_rows,
            side=side,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            asof_utc=asof_utc,
            fill_already_confirmed=fill_already_confirmed,
            fill_time_utc=fill_time_utc,
            passive_limit_queue_realism_enabled=passive_limit_queue_realism_enabled,
            passive_limit_queue_min_penetration_r=passive_limit_queue_min_penetration_r,
            passive_limit_queue_min_touch_count=passive_limit_queue_min_touch_count,
            milestone_rs=milestone_rs,
        )
    if tick_rows:
        return infer_ordered_path_from_ticks(
            ticks=tick_rows,
            side=side,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            asof_utc=asof_utc,
            fill_already_confirmed=fill_already_confirmed,
            fill_time_utc=fill_time_utc,
            passive_limit_queue_realism_enabled=passive_limit_queue_realism_enabled,
            passive_limit_queue_min_penetration_r=passive_limit_queue_min_penetration_r,
            passive_limit_queue_min_touch_count=passive_limit_queue_min_touch_count,
            milestone_rs=milestone_rs,
        )
    return _empty_path_result(
        status="source_gap",
        source="local_m1_tick_files",
        source_row_count=0,
        side=side.upper(),
        asof_utc=asof_utc,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        source_gaps=(
            "local_m1_or_tick_scratch_file_missing_or_empty_for_ordered_path_oracle",
        ),
    )


def _infer_ordered_path(
    *,
    rows: Iterable[Mapping[str, Any]],
    side: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    asof_utc: str,
    source: str,
    time_keys: tuple[str, ...],
    fill_already_confirmed: bool,
    fill_time_utc: str | None,
    milestone_rs: tuple[float, ...],
    passive_limit_queue_realism_enabled: bool = False,
    passive_limit_queue_min_penetration_r: float = 0.0,
    passive_limit_queue_min_touch_count: int = 1,
) -> OrderedPathOracleResult:
    side_upper = side.upper()
    asof = parse_utc(asof_utc)
    # Replay source rows are immutable.  Rebuilding every mapping for every
    # candidate geometry only adds allocation pressure.
    source_rows = list(rows)
    count = len(source_rows)
    if side_upper not in {"LONG", "BUY", "SHORT", "SELL"}:
        return _empty_path_result(
            status="invalid_side",
            source=source,
            source_row_count=count,
            side=side_upper,
            asof_utc=asof_utc,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            source_gaps=("missing_or_invalid_side",),
        )
    if asof is None:
        return _empty_path_result(
            status="missing_asof",
            source=source,
            source_row_count=count,
            side=side_upper,
            asof_utc=asof_utc,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            source_gaps=("missing_asof_utc",),
        )
    risk_distance = abs(entry_price - stop_price)
    if risk_distance <= 0:
        return _empty_path_result(
            status="invalid_geometry",
            source=source,
            source_row_count=count,
            side=side_upper,
            asof_utc=asof_utc,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            risk_distance=None,
            target_r=None,
            source_gaps=("entry_stop_risk_distance_missing_or_zero",),
        )

    normalized = []
    for row in source_rows:
        row_time = _row_time(row, time_keys)
        if row_time is not None:
            normalized.append((row_time, row))
    normalized.sort(
        key=lambda item: item[0] or datetime.max.replace(tzinfo=timezone.utc)
    )
    target_r = abs(target_price - entry_price) / risk_distance
    milestone_values = sorted({float(value) for value in milestone_rs} | {round(target_r, 9)})
    milestone_hits: dict[str, dict[str, Any]] = {
        _milestone_key(value): {
            "threshold_r": value,
            "reached": False,
            "first_touch_utc": None,
            "seconds_to_first_touch": None,
            "minutes_to_first_touch": None,
            "source_status": "not_reached",
        }
        for value in milestone_values
        if value > 0
    }

    fill_dt = parse_utc(fill_time_utc) if fill_time_utc else None
    fill_status = "filled_before_or_at_asof" if fill_already_confirmed else "not_filled"
    fill_price: float | None = entry_price if fill_already_confirmed else None
    if fill_already_confirmed and fill_dt is None:
        fill_dt = asof
    queue_required = (
        bool(passive_limit_queue_realism_enabled)
        and not fill_already_confirmed
    )
    min_penetration_r = max(0.0, _float(passive_limit_queue_min_penetration_r) or 0.0)
    min_touch_count = max(1, int(_float(passive_limit_queue_min_touch_count) or 1))
    entry_first_touch: datetime | None = None
    queue_touch_count = 0
    queue_max_penetration_price: float | None = None
    queue_max_penetration_r: float | None = None
    queue_realism_passed: bool | None = None
    queue_realism_failed = False

    mfe_r: float | None = None
    mae_r: float | None = None
    mfe_time: datetime | None = None
    mae_time: datetime | None = None
    target_time: datetime | None = None
    stop_time: datetime | None = None
    first_adverse_time: datetime | None = None
    first_profit_time: datetime | None = None
    same_bar_ambiguity = False
    source_gaps: list[str] = []
    terminal_outcome = "not_filled"

    for ts, row in normalized:
        if ts is None or ts <= asof:
            continue
        if fill_dt is None:
            if not _entry_touched(row, side_upper, entry_price, source):
                continue
            if entry_first_touch is None:
                entry_first_touch = ts
            queue_touch_count += 1
            touch_price = _entry_touch_price(row, side_upper, source)
            penetration_r = (
                None
                if touch_price is None
                else (
                    max(0.0, entry_price - touch_price) / risk_distance
                    if side_upper in {"LONG", "BUY"}
                    else max(0.0, touch_price - entry_price) / risk_distance
                )
            )
            if penetration_r is not None and (
                queue_max_penetration_r is None
                or penetration_r > queue_max_penetration_r
            ):
                queue_max_penetration_r = penetration_r
                queue_max_penetration_price = touch_price
            if queue_required:
                penetration_passed = bool(
                    min_penetration_r > 0.0
                    and (queue_max_penetration_r or 0.0) + 1e-12
                    >= min_penetration_r
                )
                queue_realism_passed = (
                    penetration_passed
                    or queue_touch_count >= min_touch_count
                )
                if not queue_realism_passed:
                    terminal_outcome = "first_touch_optimistic_queue_realism_pending"
                    continue
            else:
                queue_realism_passed = True
            fill_dt = ts
            fill_status = f"filled_from_ordered_{source}_path"
            fill_price = entry_price
            terminal_outcome = "filled_no_terminal_event"

        if ts < fill_dt:
            continue

        favorable_price = _favorable_price(row, side_upper, source)
        adverse_price = _adverse_price(row, side_upper, source)
        favorable_r = _r_for_price(side_upper, favorable_price, entry_price, risk_distance)
        adverse_r = _r_for_price(side_upper, adverse_price, entry_price, risk_distance)
        if favorable_r is not None and (mfe_r is None or favorable_r > mfe_r):
            mfe_r = round(favorable_r, 9)
            mfe_time = ts
        if adverse_r is not None and (mae_r is None or adverse_r < mae_r):
            mae_r = round(adverse_r, 9)
            mae_time = ts
        if first_adverse_time is None and adverse_r is not None and adverse_r < 0:
            first_adverse_time = ts
        if first_profit_time is None and favorable_r is not None and favorable_r >= 0.25:
            first_profit_time = ts

        for key, milestone in milestone_hits.items():
            threshold = _float(milestone.get("threshold_r"))
            if threshold is None or milestone_hits[key]["reached"]:
                continue
            if favorable_r is not None and favorable_r >= threshold:
                seconds = max(0.0, (ts - fill_dt).total_seconds())
                milestone_hits[key] = {
                    "threshold_r": threshold,
                    "reached": True,
                    "first_touch_utc": ts.isoformat(),
                    "seconds_to_first_touch": seconds,
                    "minutes_to_first_touch": round(seconds / 60.0, 9),
                    "source_status": (
                        "ordered_tick_touch"
                        if source == "tick"
                        else "m1_bar_range_touch_intrabar_order_unknown"
                    ),
                }

        target_hit = _target_touched(row, side_upper, target_price, source)
        stop_hit = _stop_touched(row, side_upper, stop_price, source)
        if target_hit:
            target_time = ts
        if stop_hit:
            stop_time = ts
        if target_hit and stop_hit:
            same_bar_ambiguity = True
            terminal_outcome = "same_bar_target_stop_ambiguous"
            source_gaps.append("ordered_tick_required_for_same_bar_target_stop_sequence")
            break
        if target_hit:
            terminal_outcome = "target_reached_before_stop"
            break
        if stop_hit:
            terminal_outcome = "stop_reached_before_target"
            break
        terminal_outcome = "filled_no_terminal_event"

    if fill_dt is None and entry_first_touch is not None and queue_required:
        queue_realism_failed = True
        queue_realism_passed = False
    if fill_dt is None and not queue_realism_failed:
        source_gaps.append(f"entry_not_touched_in_post_asof_{source}_path")
    if not normalized:
        source_gaps.append(f"{source}_path_rows_missing_or_unparseable")

    adverse_flag: bool | None = None
    adverse_status = "not_enough_ordered_path"
    if first_adverse_time and first_profit_time:
        if first_adverse_time == first_profit_time and source != "tick":
            source_gaps.append("ordered_tick_required_for_adverse_before_profit_sequence")
            adverse_status = "same_bar_ambiguous"
        else:
            adverse_flag = first_adverse_time < first_profit_time
            adverse_status = "ordered"
    elif first_adverse_time and not first_profit_time:
        adverse_flag = True
        adverse_status = "ordered_no_profit_milestone"
    elif first_profit_time and not first_adverse_time:
        adverse_flag = False
        adverse_status = "ordered_profit_before_adverse"

    status = "source_gap" if source_gaps and fill_dt is None and not queue_realism_failed else "resolved"
    if same_bar_ambiguity:
        status = "ambiguous_requires_tick"
    if fill_dt is None:
        if queue_realism_failed:
            fill_status = "not_filled_passive_limit_queue_realism_not_confirmed"
            terminal_outcome = "first_touch_optimistic_queue_realism_failed"
        else:
            fill_status = f"not_filled_in_post_asof_{source}_path"
            terminal_outcome = "not_filled"

    diagnostic_fill_status: str | None = None
    diagnostic_fill_time_utc: str | None = None
    diagnostic_fill_price: float | None = None
    diagnostic_terminal_outcome: str | None = None
    ordered_tick_sequence_gaps = tuple(
        gap
        for gap in dict.fromkeys(source_gaps)
        if gap
        in {
            "ordered_tick_required_for_adverse_before_profit_sequence",
            "ordered_tick_required_for_same_bar_target_stop_sequence",
        }
    )

    if fill_already_confirmed:
        fill_realism_class = "source_safe_immediate_marketable"
        fill_realism_executable = True
        fill_realism_reason = "fill_confirmed_from_predecision_marketable_price_source"
    elif fill_dt is not None and queue_required:
        fill_realism_class = "passive_queue_confirmed"
        fill_realism_executable = True
        fill_realism_reason = "passive_limit_queue_realism_confirmed_by_penetration_or_repeated_touch"
    elif fill_dt is not None and source == "tick":
        fill_realism_class = "ordered_tick_entry_touch"
        fill_realism_executable = True
        fill_realism_reason = "ordered_tick_path_confirmed_entry_touch"
    elif fill_dt is not None:
        fill_realism_class = "legacy_m1_first_touch_no_queue_realism"
        fill_realism_executable = True
        fill_realism_reason = "raw_comparator_first_touch_fill_without_queue_realism"
    elif queue_realism_failed:
        fill_realism_class = "first_touch_optimistic"
        fill_realism_executable = False
        fill_realism_reason = "passive_limit_first_touch_without_queue_realism_confirmation"
        diagnostic_fill_status = f"filled_from_ordered_{source}_path"
        diagnostic_fill_time_utc = (
            entry_first_touch.isoformat() if entry_first_touch is not None else None
        )
        diagnostic_fill_price = entry_price
        diagnostic_terminal_outcome = "first_touch_optimistic_queue_realism_counterfactual"
    elif source_gaps:
        fill_realism_class = "source_gap"
        fill_realism_executable = False
        fill_realism_reason = "postdecision_ordered_path_source_gap_or_entry_not_touched"
    else:
        fill_realism_class = "not_filled"
        fill_realism_executable = False
        fill_realism_reason = "entry_not_filled_before_expiry"

    entry_fill_executable = bool(fill_dt is not None and fill_realism_executable)
    if entry_fill_executable:
        entry_fill_authority_status = "entry_fill_executable"
        entry_fill_authority_reason = fill_realism_reason
    elif queue_realism_failed:
        entry_fill_authority_status = "entry_fill_diagnostic_queue_unconfirmed"
        entry_fill_authority_reason = fill_realism_reason
    else:
        entry_fill_authority_status = "entry_not_filled_before_expiry"
        entry_fill_authority_reason = fill_realism_reason

    terminal_r_scoreable = bool(
        entry_fill_executable and not ordered_tick_sequence_gaps
    )
    if terminal_r_scoreable:
        terminal_r_scoreability_status = (
            "ordered_tick_terminal_r_scoreable"
            if source == "tick"
            else "ordered_m1_proxy_terminal_r_scoreable"
        )
        terminal_r_scoreability_reason = None
        terminal_r_diagnostic_outcome = None
    elif entry_fill_executable and ordered_tick_sequence_gaps:
        terminal_r_scoreability_status = (
            "entry_fill_executable_terminal_r_ordered_tick_sequence_required"
        )
        terminal_r_scoreability_reason = ",".join(ordered_tick_sequence_gaps)
        terminal_r_diagnostic_outcome = terminal_outcome
        status = "ambiguous_requires_tick"
    else:
        terminal_r_scoreability_status = "not_filled_no_terminal_r"
        terminal_r_scoreability_reason = None
        terminal_r_diagnostic_outcome = None

    return OrderedPathOracleResult(
        status=status,
        source=source,
        source_row_count=count,
        side=side_upper,
        asof_utc=asof.isoformat(),
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        risk_distance=risk_distance,
        target_r=round(target_r, 9),
        fill_status=fill_status,
        fill_time_utc=fill_dt.isoformat() if fill_dt else None,
        fill_price=fill_price,
        entry_fill_executable=entry_fill_executable,
        entry_fill_authority_status=entry_fill_authority_status,
        entry_fill_authority_reason=entry_fill_authority_reason,
        entry_fill_authority_source_boundary=(
            "predecision_marketable_limit_at_decision"
            if fill_already_confirmed and entry_fill_executable
            else "post_asof_ordered_tick_entry_path"
            if source == "tick" and entry_fill_executable
            else "post_asof_ordered_m1_passive_queue_path"
            if entry_fill_executable and queue_required
            else "post_asof_ordered_path_no_executable_entry_fill"
        ),
        terminal_r_scoreable=terminal_r_scoreable,
        terminal_r_scoreability_status=terminal_r_scoreability_status,
        terminal_r_scoreability_reason=terminal_r_scoreability_reason,
        terminal_r_diagnostic_outcome=terminal_r_diagnostic_outcome,
        entry_first_touch_utc=entry_first_touch.isoformat() if entry_first_touch else None,
        passive_limit_queue_touch_count=queue_touch_count,
        passive_limit_queue_max_penetration_price=(
            round(queue_max_penetration_price, 9)
            if queue_max_penetration_price is not None
            else None
        ),
        passive_limit_queue_max_penetration_r=(
            round(queue_max_penetration_r, 9)
            if queue_max_penetration_r is not None
            else None
        ),
        passive_limit_queue_penetrated_beyond_limit=(
            (queue_max_penetration_r or 0.0) > 0.0
            if entry_first_touch is not None
            else None
        ),
        passive_limit_queue_realism_required=queue_required,
        passive_limit_queue_realism_min_penetration_r=min_penetration_r if queue_required else None,
        passive_limit_queue_realism_min_touch_count=min_touch_count if queue_required else None,
        passive_limit_queue_realism_passed=queue_realism_passed,
        fill_realism_class=fill_realism_class,
        fill_realism_executable=fill_realism_executable,
        fill_realism_reason=fill_realism_reason,
        fill_realism_source_boundary=(
            "post_asof_ordered_tick_path"
            if source == "tick"
            else "post_asof_ordered_m1_path_with_queue_realism"
            if queue_required
            else "post_asof_ordered_m1_path_legacy_first_touch"
        ),
        fill_realism_queue_model=(
            "min_penetration_or_repeated_touch"
            if queue_required
            else "ordered_tick_touch"
            if source == "tick"
            else "legacy_first_touch"
        ),
        fill_realism_diagnostic_fill_status=(
            diagnostic_fill_status
            if queue_realism_failed
            else None
        ),
        fill_realism_diagnostic_fill_time_utc=(
            diagnostic_fill_time_utc
            if queue_realism_failed
            else None
        ),
        fill_realism_diagnostic_fill_price=diagnostic_fill_price,
        fill_realism_diagnostic_terminal_outcome=diagnostic_terminal_outcome,
        diagnostic_fill_only=bool(queue_realism_failed),
        package_execution_result_scope=(
            "diagnostic_counterfactual_only"
            if queue_realism_failed
            else "entry_fill_executable_terminal_r_unscoreable"
            if entry_fill_executable and ordered_tick_sequence_gaps
            else None
        ),
        terminal_outcome=terminal_outcome,
        target_first_touch_utc=target_time.isoformat() if target_time else None,
        stop_first_touch_utc=stop_time.isoformat() if stop_time else None,
        same_bar_ambiguity=same_bar_ambiguity,
        mfe_r=mfe_r,
        mfe_time_utc=mfe_time.isoformat() if mfe_time else None,
        mae_r=mae_r,
        mae_time_utc=mae_time.isoformat() if mae_time else None,
        adverse_before_profit_flag=adverse_flag,
        adverse_before_profit_status=adverse_status,
        milestones=milestone_hits,
        source_gaps=tuple(dict.fromkeys(source_gaps)),
    )


def simulate_fresh_day_prop_curve(
    decisions: Iterable[DayPropDecision],
    *,
    daily_drawdown_limit_r: float,
    max_drawdown_limit_r: float | None = None,
) -> list[dict[str, Any]]:
    """Simulate per-day risk blocks using a fresh daily curve and replay R."""

    ordered = sorted(decisions, key=lambda item: item.asof_utc)
    day_realized_r = 0.0
    overall_realized_r = 0.0
    out: list[dict[str, Any]] = []
    for decision in ordered:
        daily_headroom_before = daily_drawdown_limit_r + day_realized_r
        overall_headroom_before = (
            None if max_drawdown_limit_r is None else max_drawdown_limit_r + overall_realized_r
        )
        daily_blocked = decision.requested_risk_r > daily_headroom_before
        overall_blocked = (
            overall_headroom_before is not None and decision.requested_risk_r > overall_headroom_before
        )
        blocked = daily_blocked or overall_blocked
        realized = 0.0 if blocked else decision.result_r
        if not blocked:
            day_realized_r += realized
            overall_realized_r += realized
        out.append(
            {
                "candidate_id": decision.candidate_id,
                "asof_utc": decision.asof_utc,
                "requested_risk_r": decision.requested_risk_r,
                "result_r": decision.result_r,
                "daily_headroom_before_r": round(daily_headroom_before, 9),
                "overall_headroom_before_r": (
                    round(overall_headroom_before, 9) if overall_headroom_before is not None else None
                ),
                "daily_drawdown_blocked": daily_blocked,
                "maximum_drawdown_blocked": overall_blocked,
                "allowed": not blocked,
                "realized_r_applied": round(realized, 9),
                "day_realized_r_after": round(day_realized_r, 9),
                "overall_realized_r_after": round(overall_realized_r, 9),
                "evidence_label": "replay/proxy-R daily prop simulation",
            }
        )
    return out


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _empty_path_result(
    *,
    status: str,
    source: str,
    source_row_count: int,
    side: str,
    asof_utc: str,
    entry_price: float,
    stop_price: float,
    target_price: float,
    risk_distance: float | None = None,
    target_r: float | None = None,
    source_gaps: tuple[str, ...] = (),
) -> OrderedPathOracleResult:
    return OrderedPathOracleResult(
        status=status,
        source=source,
        source_row_count=source_row_count,
        side=side,
        asof_utc=asof_utc,
        entry_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        risk_distance=risk_distance,
        target_r=target_r,
        fill_status="not_evaluated",
        fill_time_utc=None,
        fill_price=None,
        fill_realism_class=(
            "source_gap"
            if "source_gap" in status or "missing" in status
            else "not_evaluated"
        ),
        fill_realism_executable=False,
        fill_realism_reason=status,
        fill_realism_source_boundary="post_asof_ordered_path_unavailable",
        terminal_outcome=status,
        source_gaps=source_gaps,
    )


def _row_time(row: Mapping[str, Any], keys: tuple[str, ...]) -> datetime | None:
    for key in keys:
        parsed = parse_utc(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _milestone_key(value: float) -> str:
    text = f"{value:.9f}".rstrip("0").rstrip(".")
    return f"{text}r"


def _r_for_price(
    side_upper: str,
    price: float | None,
    entry_price: float,
    risk_distance: float,
) -> float | None:
    if price is None or risk_distance <= 0:
        return None
    if side_upper in {"LONG", "BUY"}:
        return (price - entry_price) / risk_distance
    return (entry_price - price) / risk_distance


def _entry_touched(
    row: Mapping[str, Any],
    side_upper: str,
    entry_price: float,
    source: str,
) -> bool:
    if source == "tick":
        if side_upper in {"LONG", "BUY"}:
            ask = _float(row.get("ask"))
            last = _float(row.get("last"))
            return (ask is not None and ask <= entry_price) or (
                ask is None and last is not None and last <= entry_price
            )
        bid = _float(row.get("bid"))
        last = _float(row.get("last"))
        return (bid is not None and bid >= entry_price) or (
            bid is None and last is not None and last >= entry_price
        )
    low = _float(row.get("low"))
    high = _float(row.get("high"))
    if side_upper in {"LONG", "BUY"}:
        return low is not None and low <= entry_price
    return high is not None and high >= entry_price


def _entry_touch_price(
    row: Mapping[str, Any],
    side_upper: str,
    source: str,
) -> float | None:
    if source == "tick":
        if side_upper in {"LONG", "BUY"}:
            touch_price = _float(row.get("ask"))
            if touch_price is None:
                touch_price = _float(row.get("last"))
            return touch_price
        touch_price = _float(row.get("bid"))
        if touch_price is None:
            touch_price = _float(row.get("last"))
        return touch_price
    if side_upper in {"LONG", "BUY"}:
        return _float(row.get("low"))
    return _float(row.get("high"))


def _favorable_price(row: Mapping[str, Any], side_upper: str, source: str) -> float | None:
    if source == "tick":
        if side_upper in {"LONG", "BUY"}:
            return _float(row.get("bid")) or _float(row.get("last"))
        return _float(row.get("ask")) or _float(row.get("last"))
    if side_upper in {"LONG", "BUY"}:
        return _float(row.get("high"))
    return _float(row.get("low"))


def _adverse_price(row: Mapping[str, Any], side_upper: str, source: str) -> float | None:
    if source == "tick":
        if side_upper in {"LONG", "BUY"}:
            return _float(row.get("bid")) or _float(row.get("last"))
        return _float(row.get("ask")) or _float(row.get("last"))
    if side_upper in {"LONG", "BUY"}:
        return _float(row.get("low"))
    return _float(row.get("high"))


def _target_touched(
    row: Mapping[str, Any],
    side_upper: str,
    target_price: float,
    source: str,
) -> bool:
    favorable = _favorable_price(row, side_upper, source)
    if favorable is None:
        return False
    if side_upper in {"LONG", "BUY"}:
        return favorable >= target_price
    return favorable <= target_price


def _stop_touched(
    row: Mapping[str, Any],
    side_upper: str,
    stop_price: float,
    source: str,
) -> bool:
    adverse = _adverse_price(row, side_upper, source)
    if adverse is None:
        return False
    if side_upper in {"LONG", "BUY"}:
        return adverse <= stop_price
    return adverse >= stop_price
