#!/usr/bin/env python3
"""Build a historical pre-AI opportunity dataset for Phase 3 validation.

This is a research-only replay utility. It enumerates historical kill-zone M15
candles from local MT5 CSV exports, applies deterministic pre-AI gates, joins a
no-lookahead external-feed snapshot, and optionally attaches an OB-retest
mechanical outcome. It never calls the primary analyzer or any paid AI API.
"""

from __future__ import annotations

import argparse
import bisect
import copy
import csv
import json
import logging
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_external_feed_snapshots_historical import (  # noqa: E402
    DEFAULT_GROUP_FILTERS,
    DEFAULT_SYMBOL_ALIASES,
    DEFAULT_SYMBOLS,
    build_snapshot_from_index,
    parse_group_filters,
    parse_symbol_aliases,
    prepare_snapshot_index,
)
from scripts.build_external_feed_validation_dataset import (  # noqa: E402
    TIMEFRAME_MINUTES,
    TIMESTAMP_SUFFIXES,
    validate_snapshot_no_lookahead,
)
from scripts.historical_data_loader import (  # noqa: E402
    LOOKBACK,
    ASIAN_END,
    ASIAN_START,
    LONDON_OPEN_END,
    LONDON_OPEN_START,
    LONDON_SESSION_END,
    LONDON_SESSION_START,
    detect_equal_levels,
)
from src.components import market_state as market_state_mod  # noqa: E402
from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    ExternalFeedStore,
    SOURCE_REGISTRY,
    ensure_utc,
    safe_slug,
    utc_now,
)
from src.components.pre_ai_gates import h1_poi_availability  # noqa: E402
from src.research_infra.dumb_baseline import (  # noqa: E402
    BaselineConfig,
    compute_mechanical_entry,
    resolve_mechanical_outcome,
)
from src.utils.config import apply_instrument_overrides  # noqa: E402


logger = logging.getLogger(__name__)

SCHEMA_VERSION = "historical_pre_ai_opportunity_v1"
SUMMARY_SCHEMA_VERSION = "historical_pre_ai_opportunity_summary_v1"

DEFAULT_DATA_DIRS = (
    "data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1",
    "data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1",
)
DEFAULT_TIMEFRAME = "M15"
DEFAULT_LABEL = "phase3_historical_pre_ai_opportunities_v1"
DEFAULT_BUNDLE_ID = "calendar_macro_bundle_v1"
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "HISTORICAL_OPPORTUNITY_AUDIT_2026-05-01.md"
)
DEFAULT_MECHANICAL_MAX_HOLD_BARS = 96
NO_AI_CALLS_MADE = 0


@dataclass(frozen=True)
class CandleSeries:
    """OHLCV rows with both bar-open and bar-close timestamps."""

    timeframe: str
    rows: list[dict[str, Any]]
    open_times: list[datetime]
    close_times: list[datetime]
    source_path: str | None = None
    source_kind: str = "csv"

    @classmethod
    def from_csv(cls, path: str | Path, *, timeframe: str) -> "CandleSeries":
        timeframe_key = timeframe.upper()
        if timeframe_key not in TIMEFRAME_MINUTES:
            raise ValueError(f"unsupported timeframe {timeframe!r}")
        delta = timedelta(minutes=TIMEFRAME_MINUTES[timeframe_key])
        rows: list[dict[str, Any]] = []
        open_times: list[datetime] = []
        close_times: list[datetime] = []
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"time", "open", "high", "low", "close"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise ValueError(f"{path}: missing required OHLC columns")
            for raw in reader:
                try:
                    opened_at = ensure_utc(str(raw["time"]))
                    row = {
                        "time": _iso_z(opened_at),
                        "open": float(raw["open"]),
                        "high": float(raw["high"]),
                        "low": float(raw["low"]),
                        "close": float(raw["close"]),
                        "volume": _float_or_zero(raw.get("volume")),
                    }
                except (KeyError, TypeError, ValueError):
                    continue
                rows.append(row)
                open_times.append(opened_at)
                close_times.append(opened_at + delta)
        order = sorted(range(len(rows)), key=lambda idx: open_times[idx])
        return cls(
            timeframe=timeframe_key,
            rows=[rows[idx] for idx in order],
            open_times=[open_times[idx] for idx in order],
            close_times=[close_times[idx] for idx in order],
            source_path=str(path),
        )

    @classmethod
    def derived(
        cls,
        *,
        timeframe: str,
        rows: list[dict[str, Any]],
        source_path: str | None,
        source_kind: str,
    ) -> "CandleSeries":
        timeframe_key = timeframe.upper()
        delta = timedelta(minutes=TIMEFRAME_MINUTES[timeframe_key])
        sorted_rows = sorted(rows, key=lambda row: ensure_utc(str(row["time"])))
        open_times = [ensure_utc(str(row["time"])) for row in sorted_rows]
        return cls(
            timeframe=timeframe_key,
            rows=sorted_rows,
            open_times=open_times,
            close_times=[opened_at + delta for opened_at in open_times],
            source_path=source_path,
            source_kind=source_kind,
        )

    def slice_for_mso(
        self,
        candle_close_utc: datetime,
        *,
        lookback: int,
        htf_policy: str,
    ) -> list[dict[str, Any]]:
        """Return the as-of slice used to build the MSO.

        M15 always uses closed bars. Higher timeframes default to the historical
        replay convention used by the existing simulator: bar open <= evaluated
        M15 close, approximating live partial HTF bars from MT5.
        """

        if self.timeframe == "M15" or htf_policy == "closed_only":
            idx = bisect.bisect_right(self.close_times, candle_close_utc)
        elif htf_policy == "partial_htf":
            idx = bisect.bisect_right(self.open_times, candle_close_utc)
        else:
            raise ValueError(f"unsupported htf_policy {htf_policy!r}")
        if idx <= 0:
            return []
        return [dict(row) for row in self.rows[max(0, idx - lookback) : idx]]


@dataclass(frozen=True)
class OpportunityCandle:
    symbol: str
    broker_symbol: str
    external_symbol: str
    timeframe: str
    bar_time_utc: datetime
    candle_close_utc: datetime
    kill_zone: str
    session: str
    open: float
    high: float
    low: float
    close: float


def disable_component_side_effects() -> None:
    """Keep Component 2 pure inside this research replay process."""

    market_state_mod.write_pipeline = lambda *_args, **_kwargs: None
    market_state_mod.log_structure_divergence = lambda *_args, **_kwargs: None


def load_base_config(path: str | Path = "config/agent_config.yaml") -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_broker_symbol_map(data_dirs: Iterable[str | Path]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for data_dir in data_dirs:
        manifest_path = Path(data_dir) / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in manifest.get("symbols", []) or []:
            file_symbol = item.get("file_symbol")
            mt5_symbol = item.get("mt5_symbol")
            if file_symbol and mt5_symbol:
                mapping[str(file_symbol)] = str(mt5_symbol)
    return mapping


def load_symbol_candle_series(
    *,
    data_dirs: Iterable[str | Path],
    symbol: str,
    derive_h4_from_h1: bool = True,
) -> dict[str, CandleSeries]:
    series: dict[str, CandleSeries] = {}
    roots = [Path(root) for root in data_dirs]
    for timeframe in ("M15", "H1", "H4", "D1"):
        path = _find_ohlcv_path(roots, symbol, timeframe)
        if path is not None:
            series[timeframe] = CandleSeries.from_csv(path, timeframe=timeframe)
    if "H4" not in series and derive_h4_from_h1 and "H1" in series:
        series["H4"] = derive_h4_series_from_h1(series["H1"])
    return series


def derive_h4_series_from_h1(h1: CandleSeries) -> CandleSeries:
    """Derive H4 bars from local H1 rows when MT5 H4 export is absent."""

    grouped: dict[datetime, list[dict[str, Any]]] = {}
    for opened_at, row in zip(h1.open_times, h1.rows):
        block_hour = (opened_at.hour // 4) * 4
        block_start = opened_at.replace(hour=block_hour, minute=0, second=0, microsecond=0)
        grouped.setdefault(block_start, []).append(row)

    h4_rows: list[dict[str, Any]] = []
    for block_start, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: ensure_utc(str(row["time"])))
        h4_rows.append(
            {
                "time": _iso_z(block_start),
                "open": float(ordered[0]["open"]),
                "high": max(float(row["high"]) for row in ordered),
                "low": min(float(row["low"]) for row in ordered),
                "close": float(ordered[-1]["close"]),
                "volume": sum(float(row.get("volume") or 0.0) for row in ordered),
            }
        )
    return CandleSeries.derived(
        timeframe="H4",
        rows=h4_rows,
        source_path=h1.source_path,
        source_kind="derived_from_h1",
    )


def enumerate_opportunity_candles(
    *,
    symbol: str,
    broker_symbol: str,
    external_symbol: str,
    m15: CandleSeries,
    config: Mapping[str, Any],
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    limit: int | None = None,
) -> list[OpportunityCandle]:
    start_dt = ensure_utc(start) if start else None
    end_dt = ensure_utc(end) if end else None
    windows = _kill_zone_windows(config)
    output: list[OpportunityCandle] = []
    for row, opened_at, closed_at in zip(m15.rows, m15.open_times, m15.close_times):
        if start_dt and closed_at < start_dt:
            continue
        if end_dt and closed_at > end_dt:
            continue
        if opened_at.weekday() >= 5:
            continue
        session = _session_for_bar_open(opened_at.time(), windows)
        if session is None:
            continue
        output.append(
            OpportunityCandle(
                symbol=symbol,
                broker_symbol=broker_symbol,
                external_symbol=external_symbol,
                timeframe=m15.timeframe,
                bar_time_utc=opened_at,
                candle_close_utc=closed_at,
                kill_zone=session,
                session=session,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            )
        )
        if limit is not None and len(output) >= limit:
            break
    return output


def build_raw_data_fast(
    *,
    series_by_tf: Mapping[str, CandleSeries],
    candle: OpportunityCandle,
    config: Mapping[str, Any],
    htf_policy: str,
) -> dict[str, Any]:
    equal_level_tolerance = float(
        config.get("model_a", {}).get("equal_level_tolerance", 2.50)
    )
    sliced: dict[str, list[dict[str, Any]]] = {}
    lookbacks = dict(LOOKBACK)
    lookbacks.update(config.get("data", {}).get("lookback", {}) or {})
    for timeframe in ("D1", "H4", "H1", "M15"):
        series = series_by_tf.get(timeframe)
        if series is None:
            sliced[timeframe] = []
            continue
        sliced[timeframe] = series.slice_for_mso(
            candle.candle_close_utc,
            lookback=int(lookbacks.get(timeframe, LOOKBACK.get(timeframe, 100))),
            htf_policy=htf_policy,
        )

    session_levels = compute_session_levels_fast(
        m15=series_by_tf.get("M15"),
        target_date=candle.bar_time_utc.date(),
    )
    _update_session_levels_from_slice(
        session_levels,
        m15_slice=sliced.get("M15", []),
        target_date=candle.bar_time_utc.date(),
        now_utc=candle.candle_close_utc,
    )

    return {
        "symbol": candle.symbol,
        "timestamp_utc": _iso_z(candle.candle_close_utc),
        "candle_open_utc": _iso_z(candle.bar_time_utc),
        "candle_close_utc": _iso_z(candle.candle_close_utc),
        "candle_timestamp_source": "historical_mt5_bar_open_plus_timeframe",
        "candles": sliced,
        "session_levels": session_levels,
        "equal_highs_H4": detect_equal_levels(
            sliced.get("H4", []),
            "high",
            equal_level_tolerance,
        ),
        "equal_lows_H4": detect_equal_levels(
            sliced.get("H4", []),
            "low",
            equal_level_tolerance,
        ),
        "equal_highs_H1": detect_equal_levels(
            sliced.get("H1", []),
            "high",
            equal_level_tolerance,
        ),
        "equal_lows_H1": detect_equal_levels(
            sliced.get("H1", []),
            "low",
            equal_level_tolerance,
        ),
        "spread_cents": None,
        "high_impact_events": [],
        "data_quality": {
            "all_timeframes_complete": all(
                len(sliced.get(tf, [])) >= int(float(lookbacks.get(tf, 100)) * 0.9)
                for tf in ("D1", "H4", "H1", "M15")
            ),
            "spread_normal": True,
            "mt5_connected": False,
            "timestamp_utc": _iso_z(candle.candle_close_utc),
            "candle_open_utc": _iso_z(candle.bar_time_utc),
            "candle_close_utc": _iso_z(candle.candle_close_utc),
            "candle_timestamp_source": "historical_mt5_bar_open_plus_timeframe",
        },
    }


_SESSION_LEVEL_CACHE: dict[tuple[str, date], dict[str, Any]] = {}


def compute_session_levels_fast(
    *,
    m15: CandleSeries | None,
    target_date: date,
) -> dict[str, Any]:
    if m15 is None:
        return _empty_session_levels()
    cache_key = (m15.source_path or "<memory>", target_date)
    cached = _SESSION_LEVEL_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)
    prev_date = _previous_weekday(target_date)
    prev_day: list[dict[str, Any]] = []
    asian: list[dict[str, Any]] = []
    for opened_at, row in zip(m15.open_times, m15.rows):
        row_date = opened_at.date()
        row_time = opened_at.time()
        if row_date == prev_date:
            prev_day.append(row)
        elif row_date == target_date and ASIAN_START <= row_time < ASIAN_END:
            asian.append(row)
    levels = {
        "asian_high": max((float(row["high"]) for row in asian), default=0.0),
        "asian_low": min((float(row["low"]) for row in asian), default=0.0),
        "pdh": max((float(row["high"]) for row in prev_day), default=0.0),
        "pdl": min((float(row["low"]) for row in prev_day), default=0.0),
        "session_high": None,
        "session_low": None,
        "london_high": None,
        "london_low": None,
    }
    _SESSION_LEVEL_CACHE[cache_key] = dict(levels)
    return levels


def build_external_snapshot_projection(
    *,
    symbol: str,
    candle_close_utc: str | datetime,
    snapshot_index: Iterable[Any],
    sources: Sequence[str],
) -> dict[str, Any]:
    candle_close = ensure_utc(candle_close_utc)
    snapshot = build_snapshot_from_index(
        symbol=symbol,
        candle_close_utc=candle_close,
        snapshot_index=snapshot_index,
    )
    _sanitize_known_calendar_snapshot(snapshot, candle_close)
    _ensure_source_availability_fields(snapshot, sources)
    validate_snapshot_no_lookahead(snapshot, candle_close)
    feature_flags = _feature_availability(snapshot, sources)
    available_count = sum(1 for available in feature_flags.values() if available)
    if available_count == 0:
        match_status = "MISSING_ALL_SOURCES"
    elif available_count == len(feature_flags):
        match_status = "MATCHED_ALL_SOURCES"
    else:
        match_status = "PARTIAL_SOURCES"

    projection: dict[str, Any] = {
        "external_snapshot_schema_version": snapshot.get("schema_version"),
        "external_snapshot_symbol": snapshot.get("symbol"),
        "external_snapshot_match_status": match_status,
        "external_snapshot_as_of_utc": _latest_source_timestamp(snapshot),
        "external_snapshot_missing_sources": [
            source for source, available in feature_flags.items() if not available
        ],
        "feature_availability_flags": feature_flags,
    }
    for source, available in feature_flags.items():
        projection[f"feature_available__{source}"] = available
    for key, value in snapshot.items():
        if key in {"schema_version", "symbol", "candle_close_utc"}:
            continue
        projection[key] = value
    return projection


def iter_historical_opportunities(
    *,
    store: ExternalFeedStore,
    data_dirs: Iterable[str | Path],
    symbols: Iterable[str],
    base_config: Mapping[str, Any],
    bundle_id: str = DEFAULT_BUNDLE_ID,
    sources: Sequence[str] | None = None,
    symbol_aliases: Mapping[str, str] | None = None,
    group_filters: Mapping[str, Iterable[str]] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    limit_per_symbol: int | None = None,
    derive_h4_from_h1: bool = True,
    htf_policy: str = "partial_htf",
    include_mechanical: bool = True,
    mechanical_timeframe: str = "M15",
    mechanical_max_hold_bars: int = DEFAULT_MECHANICAL_MAX_HOLD_BARS,
) -> Iterator[dict[str, Any]]:
    disable_component_side_effects()
    selected_sources = list(sources or sorted(SOURCE_REGISTRY))
    aliases = dict(DEFAULT_SYMBOL_ALIASES)
    aliases.update(symbol_aliases or {})
    source_rows = {
        source: store.read_latest_normalized_rows(source)
        for source in selected_sources
    }
    snapshot_index = prepare_snapshot_index(
        source_rows,
        group_filters=group_filters if group_filters is not None else DEFAULT_GROUP_FILTERS,
    )
    roots = [Path(root) for root in data_dirs]
    broker_symbols = load_broker_symbol_map(roots)
    outcome_cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for symbol in symbols:
        symbol = str(symbol)
        config = apply_instrument_overrides(copy.deepcopy(dict(base_config)), symbol)
        baseline_cfg = _baseline_config_from_config(config)
        series_by_tf = load_symbol_candle_series(
            data_dirs=roots,
            symbol=symbol,
            derive_h4_from_h1=derive_h4_from_h1,
        )
        m15 = series_by_tf.get("M15")
        if m15 is None:
            logger.warning("missing M15 data for %s; skipping", symbol)
            continue
        broker_symbol = broker_symbols.get(
            symbol,
            config.get("market", {}).get("mt5_symbol") or symbol,
        )
        external_symbol = aliases.get(symbol, symbol).upper()
        candles = enumerate_opportunity_candles(
            symbol=symbol,
            broker_symbol=broker_symbol,
            external_symbol=external_symbol,
            m15=m15,
            config=config,
            start=start,
            end=end,
            limit=limit_per_symbol,
        )
        logger.info("%s: %d kill-zone candles", symbol, len(candles))
        for candle in candles:
            row = _base_row(
                candle,
                bundle_id=bundle_id,
                series_by_tf=series_by_tf,
                htf_policy=htf_policy,
            )
            row.update(
                build_external_snapshot_projection(
                    symbol=candle.external_symbol,
                    candle_close_utc=candle.candle_close_utc,
                    snapshot_index=snapshot_index,
                    sources=selected_sources,
                )
            )
            try:
                raw_data = build_raw_data_fast(
                    series_by_tf=series_by_tf,
                    candle=candle,
                    config=config,
                    htf_policy=htf_policy,
                )
                mso = market_state_mod.compute_market_state(raw_data, config)
                row.update(_evaluate_pre_ai(candle, mso, config))
                row.update(_mso_feature_counts(mso, raw_data))
                if include_mechanical:
                    row.update(
                        _mechanical_projection(
                            candle=candle,
                            mso=mso,
                            row=row,
                            roots=roots,
                            timeframe=mechanical_timeframe,
                            max_hold_bars=mechanical_max_hold_bars,
                            cache=outcome_cache,
                            baseline_cfg=baseline_cfg,
                        )
                    )
            except Exception as exc:  # noqa: BLE001 - row-level audit artifact
                row.update(_error_gate_projection(exc))
                if include_mechanical:
                    row.update(_empty_mechanical_projection("mso_error"))
            yield row


class AuditAccumulator:
    def __init__(self) -> None:
        self.rows = 0
        self.would_send_ai = 0
        self.by_symbol: Counter[str] = Counter()
        self.by_year: Counter[str] = Counter()
        self.by_kill_zone: Counter[str] = Counter()
        self.by_session: Counter[str] = Counter()
        self.by_gate_status: Counter[str] = Counter()
        self.by_gate_reason: Counter[str] = Counter()
        self.by_symbol_year: Counter[str] = Counter()
        self.by_symbol_kill_zone: Counter[str] = Counter()
        self.by_symbol_session: Counter[str] = Counter()
        self.by_kill_zone_gate: Counter[str] = Counter()
        self.by_year_gate: Counter[str] = Counter()
        self.by_session_gate: Counter[str] = Counter()
        self.by_symbol_gate: Counter[str] = Counter()
        self.external_match_status: Counter[str] = Counter()
        self.mechanical_outcomes: Counter[str] = Counter()
        self.feature_available: Counter[str] = Counter()
        self.feature_missing: Counter[str] = Counter()
        self.first_candle_close_utc: str | None = None
        self.last_candle_close_utc: str | None = None
        self.keys_seen: set[str] = set()
        self.duplicate_keys: list[str] = []

    def add(self, row: Mapping[str, Any]) -> None:
        self.rows += 1
        key = str(row.get("opportunity_key") or "")
        if key:
            if key in self.keys_seen:
                self.duplicate_keys.append(key)
            self.keys_seen.add(key)
        symbol = str(row.get("symbol") or "")
        year = str(row.get("year") or "")
        kill_zone = str(row.get("kill_zone") or "")
        session = str(row.get("session") or "")
        status = str(row.get("pre_ai_gate_status") or "")
        reason = str(row.get("pre_ai_gate_reason") or "")
        self.by_symbol[symbol] += 1
        self.by_year[year] += 1
        self.by_kill_zone[kill_zone] += 1
        self.by_session[session] += 1
        self.by_gate_status[status] += 1
        self.by_gate_reason[reason] += 1
        self.by_symbol_year[f"{symbol}|{year}"] += 1
        self.by_symbol_kill_zone[f"{symbol}|{kill_zone}"] += 1
        self.by_symbol_session[f"{symbol}|{session}"] += 1
        self.by_kill_zone_gate[f"{kill_zone}|{status}"] += 1
        self.by_year_gate[f"{year}|{status}"] += 1
        self.by_session_gate[f"{session}|{status}"] += 1
        self.by_symbol_gate[f"{symbol}|{status}"] += 1
        self.external_match_status[str(row.get("external_snapshot_match_status") or "")] += 1
        self.mechanical_outcomes[str(row.get("mechanical_outcome") or "NOT_EVALUATED")] += 1
        for source, available in (row.get("feature_availability_flags") or {}).items():
            if available:
                self.feature_available[str(source)] += 1
            else:
                self.feature_missing[str(source)] += 1
        if row.get("would_send_ai"):
            self.would_send_ai += 1
        close = row.get("candle_close_utc")
        if close:
            close_str = str(close)
            if self.first_candle_close_utc is None:
                self.first_candle_close_utc = close_str
            self.last_candle_close_utc = close_str

    def to_summary(self, *, metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            **dict(metadata),
            "rows": self.rows,
            "would_send_ai": self.would_send_ai,
            "would_send_ai_rate": self.would_send_ai / self.rows if self.rows else 0.0,
            "first_candle_close_utc": self.first_candle_close_utc,
            "last_candle_close_utc": self.last_candle_close_utc,
            "unique_keys": len(self.keys_seen),
            "duplicate_key_count": len(self.duplicate_keys),
            "duplicate_keys_sample": self.duplicate_keys[:20],
            "by_symbol": dict(sorted(self.by_symbol.items())),
            "by_year": dict(sorted(self.by_year.items())),
            "by_kill_zone": dict(sorted(self.by_kill_zone.items())),
            "by_session": dict(sorted(self.by_session.items())),
            "by_gate_status": dict(sorted(self.by_gate_status.items())),
            "top_gate_reasons": [
                {"pre_ai_gate_reason": reason, "rows": count}
                for reason, count in self.by_gate_reason.most_common(25)
            ],
            "by_symbol_year": _counter_table(self.by_symbol_year, ("symbol", "year")),
            "by_symbol_kill_zone": _counter_table(
                self.by_symbol_kill_zone,
                ("symbol", "kill_zone"),
            ),
            "by_symbol_session": _counter_table(self.by_symbol_session, ("symbol", "session")),
            "by_kill_zone_gate_status": _counter_table(
                self.by_kill_zone_gate,
                ("kill_zone", "pre_ai_gate_status"),
            ),
            "by_year_gate_status": _counter_table(
                self.by_year_gate,
                ("year", "pre_ai_gate_status"),
            ),
            "by_session_gate_status": _counter_table(
                self.by_session_gate,
                ("session", "pre_ai_gate_status"),
            ),
            "by_symbol_gate_status": _counter_table(
                self.by_symbol_gate,
                ("symbol", "pre_ai_gate_status"),
            ),
            "external_snapshot_match_status": dict(
                sorted(self.external_match_status.items())
            ),
            "feature_available": dict(sorted(self.feature_available.items())),
            "feature_missing": dict(sorted(self.feature_missing.items())),
            "mechanical_outcomes": dict(sorted(self.mechanical_outcomes.items())),
        }


def write_opportunity_artifacts(
    *,
    root: str | Path,
    bundle_id: str,
    label: str,
    rows: Iterable[Mapping[str, Any]],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    output_dir = (
        Path(root)
        / "validation"
        / safe_slug(bundle_id)
        / "historical_opportunities"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    stem = f"{safe_slug(label)}_{timestamp}"
    jsonl_path = output_dir / f"{stem}.jsonl"
    summary_path = output_dir / f"{stem}_summary.json"
    audit = AuditAccumulator()
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            materialized = dict(row)
            handle.write(json.dumps(materialized, sort_keys=True, default=_json_default) + "\n")
            audit.add(materialized)
    summary = audit.to_summary(metadata=metadata)
    summary.update(
        {
            "output_jsonl": str(jsonl_path),
            "output_summary": str(summary_path),
        }
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=_json_default),
        encoding="utf-8",
    )
    return summary


def render_audit_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 3 Historical Pre-AI Opportunity Audit",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Dataset:** `{summary.get('output_jsonl')}`",
        f"**Bundle:** `{summary.get('bundle_id')}`",
        f"**Rows:** {summary.get('rows')}",
        f"**Would send AI:** {summary.get('would_send_ai')} "
        f"({float(summary.get('would_send_ai_rate') or 0.0):.2%})",
        "",
        "## Scope",
        "",
        "- Research-only artifact; no live trading logic, prompt, or config file was changed.",
        "- No paid AI/API replay was run; this script does not call the primary analyzer.",
        "- `WOULD_SEND_AI` means the deterministic offline pre-AI gates pass; it is not an AI `CANDIDATE`, an L2-verified setup, or an executable trade.",
        "- KZ enumeration uses local MT5 CSV exports and canonical M15 candle closes.",
        "- External features are selected by publication/as-of timestamps no later than the evaluated candle close.",
        "- LBMA calendar schedule features are marked missing unless the cached previous/current/next fix is within 7 days of the candle.",
        "- Higher-timeframe replay policy: "
        f"`{summary.get('htf_policy')}`. This approximates live MT5 partial HTF context when set to `partial_htf`; "
        "historical final OHLCV cannot perfectly reconstruct live in-progress HTF bars.",
        "",
        "## Input Data",
        "",
        f"- Symbols: `{', '.join(summary.get('symbols') or [])}`",
        f"- Data dirs: `{', '.join(summary.get('data_dirs') or [])}`",
        f"- Timeframe: `{summary.get('timeframe')}`",
        f"- Start: `{summary.get('start')}`",
        f"- End: `{summary.get('end')}`",
        "",
        "## Gate Counts",
        "",
        _markdown_table_from_mapping(
            summary.get("by_gate_status") or {},
            ("pre_ai_gate_status", "rows"),
        ),
        "",
        "## Counts By Symbol",
        "",
        _markdown_table_from_mapping(summary.get("by_symbol") or {}, ("symbol", "rows")),
        "",
        "## Counts By Year",
        "",
        _markdown_table_from_mapping(summary.get("by_year") or {}, ("year", "rows")),
        "",
        "## Counts By Kill Zone",
        "",
        _markdown_table_from_mapping(summary.get("by_kill_zone") or {}, ("kill_zone", "rows")),
        "",
        "## Top Gate Reasons",
        "",
        _markdown_table(summary.get("top_gate_reasons") or []),
        "",
        "## Symbol x Gate Status",
        "",
        _markdown_table(summary.get("by_symbol_gate_status") or []),
        "",
        "## Year x Gate Status",
        "",
        _markdown_table(summary.get("by_year_gate_status") or []),
        "",
        "## Kill Zone x Gate Status",
        "",
        _markdown_table(summary.get("by_kill_zone_gate_status") or []),
        "",
        "## External Snapshot Coverage",
        "",
        _markdown_table_from_mapping(
            summary.get("external_snapshot_match_status") or {},
            ("match_status", "rows"),
        ),
        "",
        "### Feature Availability",
        "",
        _markdown_source_availability(summary),
        "",
        "## Mechanical Outcome Coverage",
        "",
        _markdown_table_from_mapping(
            summary.get("mechanical_outcomes") or {},
            ("mechanical_outcome", "rows"),
        ),
        "",
        "## Data Integrity",
        "",
        f"- No AI calls made: {summary.get('no_ai_calls_made')}",
        f"- Unique keys: {summary.get('unique_keys')}",
        f"- Duplicate keys: {summary.get('duplicate_key_count')}",
        f"- First candle close: `{summary.get('first_candle_close_utc')}`",
        f"- Last candle close: `{summary.get('last_candle_close_utc')}`",
        "",
        "## Known Limitations",
        "",
        "- This is a deterministic pre-AI opportunity population, not a paid historical AI candidate replay.",
        "- News/calendar blocking is not replayed here; external calendar/macro rows are attached as research features.",
        "- FRED rows use current-vintage cached values with a conservative publication-time model; vintage-perfect ALFRED reconstruction is outside this offline artifact.",
        "- If native H4 CSVs are absent, H4 is derived from local H1 bars and marked through `ohlcv_source__H4`.",
        "- Mechanical outcomes are diagnostic OB-retest outcomes inferred from deterministic bias and local OHLCV; they are not AI trade outcomes.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_report(path: str | Path, summary: Mapping[str, Any]) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_audit_markdown(summary), encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external)",
    )
    parser.add_argument(
        "--data-dir",
        action="append",
        help="Directory containing MT5 CSV exports. Repeatable.",
    )
    parser.add_argument(
        "--symbol",
        action="append",
        help="GTOS/file symbol to process; repeatable. Default uses Phase 3 symbols.",
    )
    parser.add_argument("--start", help="Start candle-close timestamp/date")
    parser.add_argument("--end", help="End candle-close timestamp/date")
    parser.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID)
    parser.add_argument("--label", default=DEFAULT_LABEL)
    parser.add_argument(
        "--source",
        action="append",
        choices=sorted(SOURCE_REGISTRY),
        help="External source to include; repeatable. Default includes all registered sources.",
    )
    parser.add_argument(
        "--symbol-alias",
        action="append",
        help="Map CSV file symbol to external GTOS symbol, e.g. US30_cash:US30.",
    )
    parser.add_argument(
        "--group",
        action="append",
        help="Restrict grouped sources to SOURCE:GROUP_VALUE. Defaults keep frozen groups.",
    )
    parser.add_argument("--all-groups", action="store_true")
    parser.add_argument("--limit-per-symbol", type=int)
    parser.add_argument(
        "--htf-policy",
        choices=("partial_htf", "closed_only"),
        default="partial_htf",
        help="Higher-timeframe slicing policy for MSO reconstruction.",
    )
    parser.add_argument(
        "--no-derive-h4",
        action="store_true",
        help="Do not derive missing H4 bars from H1 exports.",
    )
    parser.add_argument(
        "--no-mechanical",
        action="store_true",
        help="Skip diagnostic mechanical OB outcome resolution.",
    )
    parser.add_argument(
        "--mechanical-timeframe",
        default="M15",
        choices=sorted(TIMEFRAME_MINUTES),
    )
    parser.add_argument(
        "--mechanical-max-hold-bars",
        type=int,
        default=DEFAULT_MECHANICAL_MAX_HOLD_BARS,
    )
    parser.add_argument(
        "--config",
        default="config/agent_config.yaml",
        help="Read-only config path used for deterministic gate parameters.",
    )
    parser.add_argument("--write", action="store_true", help="Write JSONL artifacts.")
    parser.add_argument(
        "--report-path",
        default=DEFAULT_REPORT_PATH,
        help="Markdown audit report path to write when --write is set.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
    args = build_parser().parse_args(argv)
    data_dirs = args.data_dir or list(DEFAULT_DATA_DIRS)
    symbols = args.symbol or list(DEFAULT_SYMBOLS)
    selected_sources = args.source or sorted(SOURCE_REGISTRY)
    base_config = load_base_config(args.config)
    store = ExternalFeedStore(args.root)
    metadata = {
        "created_at_utc": utc_now().isoformat(),
        "bundle_id": args.bundle_id,
        "label": args.label,
        "root": str(Path(args.root)),
        "data_dirs": [str(Path(path)) for path in data_dirs],
        "symbols": list(symbols),
        "sources": list(selected_sources),
        "timeframe": DEFAULT_TIMEFRAME,
        "start": args.start,
        "end": args.end,
        "limit_per_symbol": args.limit_per_symbol,
        "htf_policy": args.htf_policy,
        "derive_h4_from_h1": not args.no_derive_h4,
        "include_mechanical": not args.no_mechanical,
        "mechanical_timeframe": args.mechanical_timeframe,
        "mechanical_max_hold_bars": args.mechanical_max_hold_bars,
        "no_ai_calls_made": NO_AI_CALLS_MADE,
    }
    rows = iter_historical_opportunities(
        store=store,
        data_dirs=data_dirs,
        symbols=symbols,
        base_config=base_config,
        bundle_id=args.bundle_id,
        sources=selected_sources,
        symbol_aliases=parse_symbol_aliases(args.symbol_alias),
        group_filters=parse_group_filters(args.group, include_defaults=not args.all_groups),
        start=args.start,
        end=args.end,
        limit_per_symbol=args.limit_per_symbol,
        derive_h4_from_h1=not args.no_derive_h4,
        htf_policy=args.htf_policy,
        include_mechanical=not args.no_mechanical,
        mechanical_timeframe=args.mechanical_timeframe,
        mechanical_max_hold_bars=args.mechanical_max_hold_bars,
    )
    if args.write:
        summary = write_opportunity_artifacts(
            root=args.root,
            bundle_id=args.bundle_id,
            label=args.label,
            rows=rows,
            metadata=metadata,
        )
        report_path = write_report(args.report_path, summary)
        summary["report_path"] = str(report_path)
        print(json.dumps(summary, indent=2, sort_keys=True, default=_json_default))
        return 0

    audit = AuditAccumulator()
    preview: list[dict[str, Any]] = []
    for row in rows:
        materialized = dict(row)
        audit.add(materialized)
        if len(preview) < 5:
            preview.append(materialized)
    summary = audit.to_summary(metadata=metadata)
    summary["preview_rows"] = preview
    print(json.dumps(summary, indent=2, sort_keys=True, default=_json_default))
    return 0


def _base_row(
    candle: OpportunityCandle,
    *,
    bundle_id: str,
    series_by_tf: Mapping[str, CandleSeries],
    htf_policy: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "opportunity_key": f"{candle.symbol}|{candle.candle_close_utc.isoformat()}",
        "symbol": candle.symbol,
        "broker_symbol": candle.broker_symbol,
        "external_symbol": candle.external_symbol,
        "timeframe": candle.timeframe,
        "bar_time_utc": candle.bar_time_utc.isoformat(),
        "candle_close_utc": candle.candle_close_utc.isoformat(),
        "kill_zone": candle.kill_zone,
        "session": candle.session,
        "year": str(candle.candle_close_utc.year),
        "month": f"{candle.candle_close_utc.year:04d}-{candle.candle_close_utc.month:02d}",
        "day_of_week": candle.candle_close_utc.strftime("%A"),
        "hour_utc": candle.candle_close_utc.hour,
        "bundle_id": bundle_id,
        "pre_ai_gate_policy": "current_orchestrator_deterministic_pre_ai_offline_v1",
        "paid_ai_replay": False,
        "ai_call_attempted": False,
        "ai_call_count": NO_AI_CALLS_MADE,
        "ohlcv_open": candle.open,
        "ohlcv_high": candle.high,
        "ohlcv_low": candle.low,
        "ohlcv_close": candle.close,
        "htf_policy": htf_policy,
        **_ohlcv_source_flags(series_by_tf),
    }


def _evaluate_pre_ai(
    candle: OpportunityCandle,
    mso: Any,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    if _is_first_ny_bar_to_skip(candle, config):
        return {
            **_bias_projection({}),
            "pre_ai_gate_status": "SKIP_FIRST_NY_CANDLE",
            "pre_ai_gate_reason": "skip_first_ny_candle",
            "would_send_ai": False,
            "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
        }
    passed, reason = _prescreen_mso(mso)
    if not passed:
        return {
            **_bias_projection({}),
            "pre_ai_gate_status": "PRE_SCREEN_REJECT",
            "pre_ai_gate_reason": reason,
            "would_send_ai": False,
            "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
        }
    bias_result = _compute_deterministic_bias(mso)
    if bias_result["bias"] == "no_bias":
        return {
            **_bias_projection(bias_result),
            "pre_ai_gate_status": "NO_BIAS_REJECT",
            "pre_ai_gate_reason": (
                f"deterministic_no_bias:D1={bias_result['d1']},"
                f"H4={bias_result['h4']},H1={bias_result['h1']}"
            ),
            "would_send_ai": False,
            "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
        }
    if config.get("pre_ai_gates", {}).get("h1_poi_availability_enabled", False):
        should_skip, skip_reason = h1_poi_availability(
            mso,
            dict(config),
            bias=bias_result.get("bias", ""),
        )
        if should_skip:
            return {
                **_bias_projection(bias_result),
                "pre_ai_gate_status": "PRE_AI_POI_REJECT",
                "pre_ai_gate_reason": skip_reason,
                "would_send_ai": False,
                "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
            }
    return {
        **_bias_projection(bias_result),
        "pre_ai_gate_status": "WOULD_SEND_AI",
        "pre_ai_gate_reason": "passed_deterministic_pre_ai_gates",
        "would_send_ai": True,
        "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
    }


def _prescreen_mso(mso: Any) -> tuple[bool, str]:
    """Research-local mirror of orchestrator.prescreen_mso.

    Kept local so this offline builder does not import the live orchestrator or
    AI analyzer stack just to run deterministic gate accounting.
    """

    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}
    d1 = tfs.get("D1")
    d1_dir = d1.structure.direction if d1 else "insufficient_data"
    h4 = tfs.get("H4")
    h4_dir = h4.structure.direction if h4 else "insufficient_data"
    d1_clear = d1_dir in ("bullish", "bearish")
    h4_clear = h4_dir in ("bullish", "bearish")
    if not d1_clear and not h4_clear:
        return False, f"L1_no_direction_d1_{d1_dir}_h4_{h4_dir}"
    if d1_clear and h4_clear and h4_dir != d1_dir:
        return False, f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}"
    return True, ""


def _mechanical_projection(
    *,
    candle: OpportunityCandle,
    mso: Any,
    row: Mapping[str, Any],
    roots: Sequence[Path],
    timeframe: str,
    max_hold_bars: int,
    cache: dict[tuple[str, str, str], list[dict[str, Any]]],
    baseline_cfg: BaselineConfig,
) -> dict[str, Any]:
    if not row.get("would_send_ai"):
        return _empty_mechanical_projection("not_would_send_ai")
    bias = str(row.get("deterministic_bias") or "")
    side = {"bullish": "LONG", "bearish": "SHORT"}.get(bias)
    if side is None:
        return _empty_mechanical_projection("bias_not_directional")
    mso_mapping = mso.model_dump(mode="json") if hasattr(mso, "model_dump") else {}
    setup = compute_mechanical_entry(
        mso_mapping,
        side,
        symbol=candle.symbol,
        candle_close_time=candle.candle_close_utc,
        framework="ob_retest",
        cfg=baseline_cfg,
        cand_id=row.get("opportunity_key"),
    )
    if setup.skip_reason:
        output = _empty_mechanical_projection(setup.skip_reason)
        output.update(
            {
                "mechanical_framework": setup.framework,
                "mechanical_side": side,
                "mechanical_setup_status": "SKIPPED",
            }
        )
        return output
    outcome_rows = _load_outcome_rows(
        roots=roots,
        symbol=candle.symbol,
        timeframe=timeframe,
        cache=cache,
    )
    outcome = resolve_mechanical_outcome(
        setup,
        ohlcv_rows=outcome_rows,
        max_hold_bars=max_hold_bars,
        require_pending_fill=True,
    )
    return {
        "mechanical_framework": setup.framework,
        "mechanical_side": side,
        "mechanical_setup_status": "OK",
        "mechanical_skip_reason": setup.skip_reason,
        "mechanical_entry": setup.entry,
        "mechanical_sl": setup.sl,
        "mechanical_tp": setup.tp,
        "mechanical_rr": setup.rr,
        "mechanical_sl_buffer_used": setup.sl_buffer_used,
        "mechanical_h1_atr": setup.h1_atr,
        "mechanical_tp_source": setup.tp_source,
        "mechanical_outcome_timeframe": timeframe.upper(),
        "mechanical_max_hold_bars": max_hold_bars,
        "mechanical_outcome": outcome.outcome,
        "mechanical_realized_r": outcome.realized_r,
        "mechanical_bars_in_trade": outcome.bars_in_trade,
        "mechanical_exit_time": outcome.exit_time,
        "mechanical_outcome_skip_reason": outcome.skip_reason,
    }


def _empty_mechanical_projection(reason: str) -> dict[str, Any]:
    return {
        "mechanical_framework": "ob_retest",
        "mechanical_side": None,
        "mechanical_setup_status": "NOT_EVALUATED",
        "mechanical_skip_reason": reason,
        "mechanical_entry": None,
        "mechanical_sl": None,
        "mechanical_tp": None,
        "mechanical_rr": None,
        "mechanical_sl_buffer_used": None,
        "mechanical_h1_atr": None,
        "mechanical_tp_source": None,
        "mechanical_outcome_timeframe": None,
        "mechanical_max_hold_bars": None,
        "mechanical_outcome": None,
        "mechanical_realized_r": None,
        "mechanical_bars_in_trade": None,
        "mechanical_exit_time": None,
        "mechanical_outcome_skip_reason": reason,
    }


def _error_gate_projection(exc: Exception) -> dict[str, Any]:
    return {
        **_bias_projection({}),
        "pre_ai_gate_status": "MSO_ERROR",
        "pre_ai_gate_reason": f"{type(exc).__name__}:{exc}",
        "would_send_ai": False,
        "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
        "mso_error_type": type(exc).__name__,
    }


def _mso_feature_counts(mso: Any, raw_data: Mapping[str, Any]) -> dict[str, Any]:
    tfs = getattr(mso, "timeframes", {}) if mso is not None else {}
    raw_candles = raw_data.get("candles", {}) if isinstance(raw_data, Mapping) else {}
    output: dict[str, Any] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        tf_state = tfs.get(tf) if isinstance(tfs, Mapping) else None
        output[f"lookback_count__{tf}"] = len(raw_candles.get(tf, []) or [])
        output[f"structure_direction__{tf}"] = (
            getattr(getattr(tf_state, "structure", None), "direction", None)
            if tf_state is not None
            else None
        )
        output[f"order_block_count__{tf}"] = len(getattr(tf_state, "order_blocks", []) or [])
        output[f"breaker_block_count__{tf}"] = len(
            getattr(tf_state, "breaker_blocks", []) or []
        )
        output[f"fvg_count__{tf}"] = len(getattr(tf_state, "fair_value_gaps", []) or [])
    dq = getattr(mso, "data_quality", None)
    output["all_timeframes_complete"] = getattr(dq, "all_timeframes_complete", None)
    return output


def _compute_deterministic_bias(mso: Any) -> dict[str, str]:
    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}

    def direction(tf_name: str) -> str:
        tf = tfs.get(tf_name)
        if tf is None:
            return "unavailable"
        structure = getattr(tf, "structure", None)
        return structure.direction if structure else "unavailable"

    d1, h4, h1, m15 = direction("D1"), direction("H4"), direction("H1"), direction("M15")
    directional = ("bullish", "bearish")
    if d1 in directional:
        bias, source = d1, "D1"
    elif h4 in directional and h4 == h1:
        bias, source = h4, "H4+H1_consensus"
    elif h4 in directional:
        bias, source = h4, "H4_primary"
    else:
        bias, source = "no_bias", "none"
    return {"bias": bias, "source": source, "d1": d1, "h4": h4, "h1": h1, "m15": m15}


def _bias_projection(bias_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "deterministic_bias": bias_result.get("bias"),
        "deterministic_bias_source": bias_result.get("source"),
        "deterministic_bias_d1": bias_result.get("d1"),
        "deterministic_bias_h4": bias_result.get("h4"),
        "deterministic_bias_h1": bias_result.get("h1"),
        "deterministic_bias_m15": bias_result.get("m15"),
    }


def _baseline_config_from_config(config: Mapping[str, Any]) -> BaselineConfig:
    risk = config.get("risk", {}) if isinstance(config, Mapping) else {}
    risk = risk if isinstance(risk, Mapping) else {}
    return BaselineConfig(
        sl_buffer_atr_multiplier=float(risk.get("sl_buffer_atr_multiplier", 0.25)),
        sl_buffer_min_ticks=int(risk.get("sl_buffer_min_ticks", 5)),
        min_rr=float(risk.get("min_rr", 1.5)),
    )


def _load_outcome_rows(
    *,
    roots: Sequence[Path],
    symbol: str,
    timeframe: str,
    cache: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    timeframe_key = timeframe.upper()
    for root in roots:
        path = _find_ohlcv_path([root], symbol, timeframe_key)
        if path is None:
            continue
        cache_key = (str(path.resolve()), symbol.upper(), timeframe_key)
        if cache_key in cache:
            return cache[cache_key]
        series = CandleSeries.from_csv(path, timeframe=timeframe_key)
        rows = [
            {
                "time": close_time,
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
            }
            for row, close_time in zip(series.rows, series.close_times)
        ]
        cache[cache_key] = rows
        return rows
    return []


def _find_ohlcv_path(roots: Sequence[Path], symbol: str, timeframe: str) -> Path | None:
    timeframe_key = timeframe.upper()
    stems = [symbol]
    if symbol == "US30":
        stems.append("US30_cash")
    elif symbol == "US30_cash":
        stems.append("US30")
    for root in roots:
        for stem in stems:
            path = root / f"{stem}_{timeframe_key}.csv"
            if path.exists():
                return path
    return None


def _ohlcv_source_flags(series_by_tf: Mapping[str, CandleSeries]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        series = series_by_tf.get(tf)
        output[f"ohlcv_available__{tf}"] = series is not None and bool(series.rows)
        output[f"ohlcv_source__{tf}"] = series.source_path if series else None
        output[f"ohlcv_source_kind__{tf}"] = series.source_kind if series else None
        output[f"ohlcv_rows_available__{tf}"] = len(series.rows) if series else 0
    return output


def _feature_availability(
    snapshot: Mapping[str, Any],
    sources: Sequence[str],
) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for source in sources:
        prefix = safe_slug(source)
        flags[prefix] = bool(snapshot.get(f"{prefix}__available", False))
    return flags


def _ensure_source_availability_fields(
    snapshot: dict[str, Any],
    sources: Sequence[str],
) -> None:
    for source in sources:
        key = f"{safe_slug(source)}__available"
        snapshot.setdefault(key, False)


def _sanitize_known_calendar_snapshot(
    snapshot: dict[str, Any],
    candle_close: datetime,
    *,
    max_calendar_gap: timedelta = timedelta(days=7),
) -> None:
    """Drop calendar rows that are not local to the evaluated candle.

    Historical LBMA schedule caches may start after the oldest MT5 candles. The
    generic schedule join can then expose the first future cached fix as the
    "next" fix for a much older candle. That is not a useful historical feature,
    so treat it as missing unless a previous/current/next fix is close enough
    to represent the same local calendar context.
    """

    prefix = "lbma_calendar__"
    if not snapshot.get(f"{prefix}available"):
        return
    candidate_fields = (
        f"{prefix}fix_time_utc",
        f"{prefix}previous_fix_time_utc",
        f"{prefix}next_fix_time_utc",
    )
    local_context = False
    for field in candidate_fields:
        value = snapshot.get(field)
        if value in (None, ""):
            continue
        try:
            fix_time = ensure_utc(str(value))
        except (TypeError, ValueError):
            continue
        if abs(candle_close - fix_time) <= max_calendar_gap:
            local_context = True
            break
    if local_context:
        return
    for key in list(snapshot):
        if key.startswith(prefix):
            del snapshot[key]
    snapshot[f"{prefix}available"] = False


def _latest_source_timestamp(snapshot: Mapping[str, Any]) -> str | None:
    latest: datetime | None = None
    for key, value in snapshot.items():
        if value in (None, "") or not key.endswith(TIMESTAMP_SUFFIXES):
            continue
        try:
            parsed = ensure_utc(str(value))
        except (TypeError, ValueError):
            continue
        if latest is None or parsed > latest:
            latest = parsed
    return latest.isoformat() if latest else None


def _kill_zone_windows(config: Mapping[str, Any]) -> dict[str, tuple[time, time]]:
    raw = config.get("market", {}).get("kill_zones", {}) or {}
    windows: dict[str, tuple[time, time]] = {}
    for name, payload in raw.items():
        if not isinstance(payload, Mapping):
            continue
        start_raw = payload.get("start_utc")
        end_raw = payload.get("end_utc")
        if not start_raw or not end_raw:
            continue
        windows[str(name)] = (_parse_hhmm(str(start_raw)), _parse_hhmm(str(end_raw)))
    return windows


def _session_for_bar_open(
    bar_time: time,
    windows: Mapping[str, tuple[time, time]],
) -> str | None:
    for name, (start, end) in windows.items():
        if start <= end:
            if start <= bar_time < end:
                return name
        elif bar_time >= start or bar_time < end:
            return name
    return None


def _is_first_ny_bar_to_skip(
    candle: OpportunityCandle,
    config: Mapping[str, Any],
) -> bool:
    if not config.get("skip_first_ny_candle", False):
        return False
    windows = _kill_zone_windows(config)
    ny = windows.get("ny")
    if ny is None or candle.kill_zone != "ny":
        return False
    return candle.bar_time_utc.time() == ny[0]


def _update_session_levels_from_slice(
    session_levels: dict[str, Any],
    *,
    m15_slice: Sequence[Mapping[str, Any]],
    target_date: date,
    now_utc: datetime,
) -> None:
    session_m15: list[Mapping[str, Any]] = []
    london_m15: list[Mapping[str, Any]] = []
    for row in m15_slice:
        opened_at = ensure_utc(str(row["time"]))
        if opened_at.date() != target_date:
            continue
        opened_time = opened_at.time()
        if LONDON_OPEN_START <= opened_time <= LONDON_OPEN_END:
            session_m15.append(row)
        if LONDON_SESSION_START <= opened_time < LONDON_SESSION_END and opened_at <= now_utc:
            london_m15.append(row)
    if session_m15:
        session_levels["session_high"] = max(float(row["high"]) for row in session_m15)
        session_levels["session_low"] = min(float(row["low"]) for row in session_m15)
    if london_m15:
        session_levels["london_high"] = max(float(row["high"]) for row in london_m15)
        session_levels["london_low"] = min(float(row["low"]) for row in london_m15)


def _empty_session_levels() -> dict[str, Any]:
    return {
        "asian_high": 0.0,
        "asian_low": 0.0,
        "pdh": 0.0,
        "pdl": 0.0,
        "session_high": None,
        "session_low": None,
        "london_high": None,
        "london_low": None,
    }


def _previous_weekday(day: date) -> date:
    prev = day - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev


def _counter_table(counter: Counter[str], columns: tuple[str, str]) -> list[dict[str, Any]]:
    rows = []
    for key, value in sorted(counter.items()):
        left, right = key.split("|", 1)
        rows.append({columns[0]: left, columns[1]: right, "rows": value})
    return rows


def _markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "_No rows._"
    preferred = (
        "symbol",
        "year",
        "kill_zone",
        "session",
        "pre_ai_gate_status",
        "pre_ai_gate_reason",
        "match_status",
        "source",
        "mechanical_outcome",
        "rows",
        "available_rows",
        "missing_rows",
    )
    keys = list(rows[0].keys())
    columns = [key for key in preferred if key in keys]
    columns.extend(key for key in keys if key not in columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def _markdown_table_from_mapping(mapping: Mapping[str, Any], columns: tuple[str, str]) -> str:
    rows = [{columns[0]: key, columns[1]: value} for key, value in sorted(mapping.items())]
    return _markdown_table(rows)


def _markdown_source_availability(summary: Mapping[str, Any]) -> str:
    available = summary.get("feature_available") or {}
    missing = summary.get("feature_missing") or {}
    sources = sorted(set(available) | set(missing))
    rows = [
        {
            "source": source,
            "available_rows": available.get(source, 0),
            "missing_rows": missing.get(source, 0),
        }
        for source in sources
    ]
    return _markdown_table(rows)


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(int(hour), int(minute))


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _float_or_zero(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
