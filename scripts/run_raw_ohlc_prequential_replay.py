#!/usr/bin/env python3
"""Run a no-leak prequential replay directly from raw OHLC candles.

This Phase 3 research adapter walks historical M15 candles in replay-clock
order, reconstructs as-of Component 2/one pre-AI observation from the candle
stream, locks a cohort decision, and only then attaches mechanical outcomes.
It never calls the primary analyzer or any paid AI/API.
"""

from __future__ import annotations

import argparse
import bisect
import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components import market_state as market_state_mod
from src.components.external_feeds import ensure_utc, utc_now
from src.research_infra.dumb_baseline import (
    MechanicalSetup,
    compute_mechanical_entry,
    resolve_mechanical_outcome,
)
from src.utils.config import apply_instrument_overrides

from scripts.build_historical_opportunity_dataset import (  # noqa: E402
    DEFAULT_BUNDLE_ID,
    DEFAULT_DATA_DIRS,
    DEFAULT_MECHANICAL_MAX_HOLD_BARS,
    CandleSeries,
    OpportunityCandle,
    _baseline_config_from_config,
    _evaluate_pre_ai,
    _find_ohlcv_path,
    _float_or_zero,
    _iso_z,
    _load_outcome_rows,
    _mso_feature_counts,
    derive_h4_series_from_h1,
    disable_component_side_effects,
    enumerate_opportunity_candles,
    load_base_config,
    load_broker_symbol_map,
    load_symbol_candle_series,
)
from scripts.build_external_feed_validation_dataset import TIMEFRAME_MINUTES  # noqa: E402
from scripts.historical_data_loader import (  # noqa: E402
    ASIAN_END,
    ASIAN_START,
    LONDON_OPEN_END,
    LONDON_OPEN_START,
    LONDON_SESSION_END,
    LONDON_SESSION_START,
    LOOKBACK,
    detect_equal_levels,
)
from scripts.run_truth_layer_prequential_replay import markdown_table  # noqa: E402


SCHEMA_VERSION = "raw_ohlc_prequential_replay_summary_v1"
DEFAULT_SPEC_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PREQUENTIAL_REPLAY_SPEC_V1.json"
)
DEFAULT_OUTPUT_ROOT = (
    "data/external/validation/calendar_macro_bundle_v1/"
    "historical_opportunities/raw_ohlc_prequential_replay"
)
DEFAULT_REPORT_PATH = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PREQUENTIAL_REPLAY_REPORT_2026-05-01.md"
)
RESOLVED_OUTCOMES = {"TP", "SL", "TIMEOUT"}
FORBIDDEN_OBSERVATION_PREFIXES = ("truth_", "future_", "m1_", "m5_", "lower_tf_")
FORBIDDEN_OBSERVATION_FIELDS = {
    "mechanical_outcome",
    "mechanical_realized_r",
    "mechanical_exit_time",
    "mechanical_bars_in_trade",
    "mechanical_outcome_skip_reason",
}
HTF_TIMEFRAMES = {"H1", "H4", "D1"}
REQUIRED_CSV_COLUMNS = ("time", "open", "high", "low", "close")


@dataclass(frozen=True)
class ReplayEvent:
    symbol: str
    candle: OpportunityCandle
    config: Mapping[str, Any]
    series_by_tf: Mapping[str, CandleSeries]


def run_raw_ohlc_prequential_replay(
    *,
    spec_path: str | Path = DEFAULT_SPEC_PATH,
    data_dirs: Sequence[str | Path] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    max_candles_per_symbol: int | None = None,
    max_events: int | None = None,
    include_blocked_controls: bool = False,
    event_log_path: str | Path | None = None,
) -> dict[str, Any]:
    spec = load_replay_spec(spec_path)
    selected_data_dirs = [Path(path) for path in (data_dirs or spec_data_dirs(spec))]
    active_cohorts = active_cohort_specs(
        spec,
        include_blocked_controls=include_blocked_controls,
    )
    blocked_cohort_keys = {
        str(cohort.get("cohort_key"))
        for cohort in spec.get("cohorts", [])
        if cohort.get("status") == "blocked_control"
    }
    symbols = sorted({split_cohort_key(str(row["cohort_key"]))[0] for row in active_cohorts})
    base_config = load_base_config()
    inventory = inventory_ohlc_sources(
        data_dirs=selected_data_dirs,
        symbols=symbols,
        timeframes=spec_timeframes(spec),
    )
    events, order_diagnostics = build_replay_events(
        data_dirs=selected_data_dirs,
        symbols=symbols,
        base_config=base_config,
        start=start,
        end=end,
        max_candles_per_symbol=max_candles_per_symbol,
    )
    if max_events is not None:
        events = events[:max_events]

    cohort_keys = {str(row["cohort_key"]) for row in active_cohorts}
    score_state = new_score_state()
    decision_counts: Counter[str] = Counter()
    decision_reasons: Counter[str] = Counter()
    pre_ai_gate_counts: Counter[str] = Counter()
    mso_error_counts: Counter[str] = Counter()
    outcome_cache: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    duplicate_event_keys = 0
    event_keys_seen: set[str] = set()
    invalid_clock_rows = 0
    future_candle_exposure_violations = 0
    htf_asof_violations = 0
    forbidden_observation_violations = 0
    blocked_control_matches_seen = 0
    ai_attempted_rows = 0
    ai_call_count_sum = 0
    first_events: list[dict[str, Any]] = []

    event_handle = None
    if event_log_path is not None:
        target = Path(event_log_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        event_handle = target.open("w", encoding="utf-8", newline="\n")

    try:
        disable_component_side_effects()
        for replay_index, event in enumerate(events, start=1):
            row, alignment, setup = build_asof_event_row(
                event=event,
                spec=spec,
                replay_index=replay_index,
            )
            event_key = str(row.get("event_key") or "")
            if event_key:
                if event_key in event_keys_seen:
                    duplicate_event_keys += 1
                event_keys_seen.add(event_key)
            if parse_datetime(row.get("candle_close_utc")) is None:
                invalid_clock_rows += 1
            if row.get("ai_call_attempted"):
                ai_attempted_rows += 1
            ai_call_count_sum += int(row.get("ai_call_count") or 0)
            pre_ai_gate_counts[str(row.get("pre_ai_gate_status") or "UNKNOWN")] += 1
            if row.get("mso_error_type"):
                mso_error_counts[str(row.get("mso_error_type"))] += 1
            future_candle_exposure_violations += int(
                alignment.get("future_candle_exposure_violations") or 0
            )
            htf_asof_violations += int(alignment.get("htf_asof_violations") or 0)

            observation = project_observation(row, spec)
            forbidden_observation_violations += len(
                forbidden_observation_fields(observation, spec)
            )
            decision = decide_from_cohorts(
                observation,
                active_cohort_keys=cohort_keys,
                blocked_cohort_keys=blocked_cohort_keys,
                include_blocked_controls=include_blocked_controls,
            )
            action = decision["action"]
            reason = decision["reason"]
            if (
                str(observation.get("raw_cohort_key") or "") in blocked_cohort_keys
                and not include_blocked_controls
            ):
                blocked_control_matches_seen += 1
            decision_counts[action] += 1
            decision_reasons[reason] += 1
            outcome = empty_outcome_projection()
            if action == "TAKE":
                outcome = score_after_decision(
                    row=row,
                    setup=setup,
                    event=event,
                    data_dirs=selected_data_dirs,
                    max_hold_bars=int(
                        (spec.get("scoring") or {}).get(
                            "mechanical_max_hold_bars",
                            DEFAULT_MECHANICAL_MAX_HOLD_BARS,
                        )
                    ),
                    timeframe=str((spec.get("scoring") or {}).get("mechanical_timeframe") or "M15"),
                    cache=outcome_cache,
                )
                add_taken_action(
                    score_state,
                    row=row,
                    observation=observation,
                    outcome=outcome,
                    replay_index=replay_index,
                    scoring_spec=spec.get("scoring") or {},
                )

            event_record = event_log_record(
                replay_index=replay_index,
                row=row,
                observation=observation,
                decision=decision,
                alignment=alignment,
                outcome=outcome,
            )
            if len(first_events) < 10:
                first_events.append(event_record)
            if event_handle is not None:
                event_handle.write(json.dumps(event_record, sort_keys=True) + "\n")
    finally:
        if event_handle is not None:
            event_handle.close()

    integrity = integrity_summary(
        duplicate_event_keys=duplicate_event_keys,
        invalid_clock_rows=invalid_clock_rows,
        forbidden_observation_violations=forbidden_observation_violations,
        future_candle_exposure_violations=future_candle_exposure_violations,
        htf_asof_violations=htf_asof_violations,
        ai_attempted_rows=ai_attempted_rows,
        ai_call_count_sum=ai_call_count_sum,
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now().isoformat(),
        "spec_path": str(Path(spec_path)),
        "spec_sha256": sha256_file(spec_path),
        "code_commit": git_commit_or_unknown(),
        "promotion_verdict_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "promotion_blocked_reason": (
            "Raw-OHLC historical replay is same-dataset diagnostic research. "
            "It does not compute DSR, PBO, effective_N, or prospective confirmation."
        ),
        "run_mode": spec.get("run_mode"),
        "evidence_class": spec.get("evidence_class"),
        "data_dirs": [str(path) for path in selected_data_dirs],
        "start": str(start) if start else None,
        "end": str(end) if end else None,
        "max_candles_per_symbol": max_candles_per_symbol,
        "max_events": max_events,
        "include_blocked_controls": include_blocked_controls,
        "symbols": symbols,
        "active_cohorts": active_cohorts,
        "blocked_cohort_keys": sorted(blocked_cohort_keys),
        "data_inventory": inventory,
        "replay_clock": {
            "field": "candle_close_utc",
            "timeframe": "M15",
            "sort_before_replay": True,
            "tie_breakers": ["symbol", "session"],
        },
        "higher_timeframe_policy": spec.get("higher_timeframe_policy"),
        "rows_replayed": len(events),
        "unique_event_keys": len(event_keys_seen),
        "duplicate_event_keys": duplicate_event_keys,
        "invalid_clock_rows": invalid_clock_rows,
        "input_order_diagnostics": order_diagnostics,
        "future_candle_exposure_violations": future_candle_exposure_violations,
        "htf_asof_violations": htf_asof_violations,
        "forbidden_observation_violations": forbidden_observation_violations,
        "blocked_control_matches_seen": blocked_control_matches_seen,
        "ai_attempted_rows": ai_attempted_rows,
        "ai_call_count_sum": ai_call_count_sum,
        "pre_ai_gate_counts": dict(sorted(pre_ai_gate_counts.items())),
        "mso_error_counts": dict(sorted(mso_error_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "decision_reasons": dict(sorted(decision_reasons.items())),
        "score": finalize_score(score_state),
        "event_log_path": str(event_log_path) if event_log_path else None,
        "event_log_sha256": sha256_file(event_log_path) if event_log_path else None,
        "first_events": first_events,
        "integrity": integrity,
        "interpretation": [
            "Strategy decisions are made from raw candle-derived as-of fields only.",
            "Mechanical outcomes are attached only after TAKE/SKIP is locked.",
            "Positive or negative historical results remain diagnostic-only.",
            "Promotion language is blocked until a separate prospective or untouched promotion dossier exists.",
        ],
    }
    return summary


def load_replay_spec(path: str | Path = DEFAULT_SPEC_PATH) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "raw_ohlc_prequential_replay_spec_v1":
        raise ValueError(f"unsupported raw replay schema: {payload.get('schema_version')!r}")
    if payload.get("promotion_verdict_allowed") is not False:
        raise ValueError("raw OHLC replay spec must set promotion_verdict_allowed=false")
    if not payload.get("cohorts"):
        raise ValueError("raw OHLC replay spec must define cohorts")
    validate_observation_spec(payload)
    return payload


def validate_observation_spec(spec: Mapping[str, Any]) -> None:
    projection = spec.get("observation_projection") or {}
    allowed = {str(field) for field in projection.get("allowed_direct_fields") or []}
    aliases = {str(field) for field in (projection.get("safe_aliases") or {}).keys()}
    all_fields = allowed | aliases
    forbidden_fields = set(projection.get("forbidden_strategy_fields") or [])
    forbidden_prefixes = tuple(projection.get("forbidden_strategy_prefixes") or [])
    collisions = [
        field
        for field in sorted(all_fields)
        if field in forbidden_fields or any(field.startswith(prefix) for prefix in forbidden_prefixes)
    ]
    if collisions:
        raise ValueError(f"raw OHLC observation allowlist exposes forbidden fields: {collisions}")


def spec_data_dirs(spec: Mapping[str, Any]) -> list[str]:
    sources = spec.get("data_sources") or {}
    data_dirs = sources.get("data_dirs") or list(DEFAULT_DATA_DIRS)
    return [str(path) for path in data_dirs]


def spec_timeframes(spec: Mapping[str, Any]) -> list[str]:
    sources = spec.get("data_sources") or {}
    return [str(tf).upper() for tf in (sources.get("inventory_timeframes") or ["M15", "M5", "M1", "H1", "H4", "D1"])]


def active_cohort_specs(
    spec: Mapping[str, Any],
    *,
    include_blocked_controls: bool,
) -> list[dict[str, Any]]:
    rows = []
    for cohort in spec.get("cohorts") or []:
        item = dict(cohort)
        status = str(item.get("status") or "")
        if status == "blocked_control" and not include_blocked_controls:
            continue
        if item.get("enabled", True):
            rows.append(item)
    return rows


def split_cohort_key(key: str) -> tuple[str, str, str, str]:
    parts = key.split("|")
    if len(parts) != 4:
        raise ValueError(f"raw cohort keys must be symbol|session|bias|source: {key!r}")
    return parts[0], parts[1], parts[2], parts[3]


def inventory_ohlc_sources(
    *,
    data_dirs: Sequence[str | Path],
    symbols: Sequence[str],
    timeframes: Sequence[str],
) -> list[dict[str, Any]]:
    roots = [Path(path) for path in data_dirs]
    manifest_index = load_manifest_index(roots)
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        for timeframe in timeframes:
            tf = timeframe.upper()
            path = _find_ohlcv_path(roots, symbol, tf)
            if path is None and tf == "H4" and _find_ohlcv_path(roots, symbol, "H1"):
                h1_path = _find_ohlcv_path(roots, symbol, "H1")
                meta = manifest_index.get((symbol, "H1", str(h1_path)))
                rows.append(
                    {
                        "symbol": symbol,
                        "timeframe": "H4",
                        "status": "DERIVED_FROM_H1",
                        "path": str(h1_path),
                        "rows": None,
                        "first": meta.get("first") if meta else None,
                        "last": meta.get("last") if meta else None,
                        "gap_count": meta.get("gap_count") if meta else None,
                    }
                )
                continue
            if path is None:
                rows.append(
                    {
                        "symbol": symbol,
                        "timeframe": tf,
                        "status": "MISSING",
                        "path": None,
                        "rows": 0,
                        "first": None,
                        "last": None,
                        "gap_count": None,
                    }
                )
                continue
            meta = manifest_index.get((symbol, tf, str(path)))
            if meta is None:
                meta = inspect_csv_metadata(path, timeframe=tf)
            rows.append(
                {
                    "symbol": symbol,
                    "timeframe": tf,
                    "status": "AVAILABLE",
                    "path": str(path),
                    "rows": meta.get("rows"),
                    "first": meta.get("first"),
                    "last": meta.get("last"),
                    "gap_count": meta.get("gap_count"),
                }
            )
    return rows


def load_manifest_index(roots: Sequence[Path]) -> dict[tuple[str, str, str], dict[str, Any]]:
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for root in roots:
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for key, meta in (manifest.get("files") or {}).items():
            symbol = str(meta.get("file_symbol") or key.rsplit("_", 1)[0])
            timeframe = str(meta.get("timeframe") or key.rsplit("_", 1)[-1]).upper()
            path = str(Path(meta.get("path") or root / f"{symbol}_{timeframe}.csv"))
            index[(symbol, timeframe, path)] = dict(meta)
    return index


def inspect_csv_metadata(path: str | Path, *, timeframe: str) -> dict[str, Any]:
    series = CandleSeries.from_csv(path, timeframe=timeframe)
    return {
        "rows": len(series.rows),
        "first": series.open_times[0].strftime("%Y-%m-%d %H:%M:%S") if series.rows else None,
        "last": series.open_times[-1].strftime("%Y-%m-%d %H:%M:%S") if series.rows else None,
        "gap_count": count_gaps(series),
    }


def count_gaps(series: CandleSeries) -> int:
    if len(series.open_times) < 2:
        return 0
    expected = timedelta(minutes=TIMEFRAME_MINUTES[series.timeframe])
    return sum(
        1
        for prev, current in zip(series.open_times, series.open_times[1:])
        if current - prev > expected
    )


def build_replay_events(
    *,
    data_dirs: Sequence[str | Path],
    symbols: Sequence[str],
    base_config: Mapping[str, Any],
    start: str | datetime | None,
    end: str | datetime | None,
    max_candles_per_symbol: int | None,
) -> tuple[list[ReplayEvent], dict[str, Any]]:
    roots = [Path(path) for path in data_dirs]
    broker_symbols = load_broker_symbol_map(roots)
    unsorted_events: list[ReplayEvent] = []
    per_symbol_counts: dict[str, int] = {}
    for symbol in symbols:
        config = apply_instrument_overrides(copy.deepcopy(dict(base_config)), symbol)
        series_by_tf = load_symbol_candle_series(
            data_dirs=roots,
            symbol=symbol,
            derive_h4_from_h1=True,
        )
        if "H4" not in series_by_tf and "H1" in series_by_tf:
            series_by_tf = dict(series_by_tf)
            series_by_tf["H4"] = derive_h4_series_from_h1(series_by_tf["H1"])
        m15 = series_by_tf.get("M15")
        if m15 is None:
            per_symbol_counts[symbol] = 0
            continue
        candles = enumerate_opportunity_candles(
            symbol=symbol,
            broker_symbol=broker_symbols.get(
                symbol,
                (config.get("market") or {}).get("mt5_symbol") or symbol,
            ),
            external_symbol=symbol,
            m15=m15,
            config=config,
            start=start,
            end=end,
            limit=max_candles_per_symbol,
        )
        per_symbol_counts[symbol] = len(candles)
        for candle in candles:
            unsorted_events.append(
                ReplayEvent(
                    symbol=symbol,
                    candle=candle,
                    config=config,
                    series_by_tf=series_by_tf,
                )
            )
    diagnostics = input_order_diagnostics(unsorted_events)
    return (
        sorted(
            unsorted_events,
            key=lambda event: (
                event.candle.candle_close_utc,
                event.symbol,
                event.candle.session,
            ),
        ),
        {
            **diagnostics,
            "per_symbol_event_counts": per_symbol_counts,
        },
    )


def input_order_diagnostics(events: Sequence[ReplayEvent]) -> dict[str, Any]:
    regressions = 0
    previous: tuple[datetime, str, str] | None = None
    first_clock = None
    last_clock = None
    for event in events:
        current = (event.candle.candle_close_utc, event.symbol, event.candle.session)
        if previous is not None and current < previous:
            regressions += 1
        previous = current
        first_clock = first_clock or event.candle.candle_close_utc.isoformat()
        last_clock = event.candle.candle_close_utc.isoformat()
    return {
        "input_order_clock_regressions": regressions,
        "input_first_clock": first_clock,
        "input_last_clock": last_clock,
        "sort_before_replay": True,
    }


def build_asof_event_row(
    *,
    event: ReplayEvent,
    spec: Mapping[str, Any],
    replay_index: int,
) -> tuple[dict[str, Any], dict[str, Any], MechanicalSetup | None]:
    candle = event.candle
    row = base_event_row(candle, replay_index=replay_index, spec=spec)
    setup: MechanicalSetup | None = None
    alignment: dict[str, Any] = {"future_candle_exposure_violations": 0, "htf_asof_violations": 0}
    try:
        raw_data, alignment = build_raw_data_prequential(
            series_by_tf=event.series_by_tf,
            candle=candle,
            config=event.config,
            htf_policy=str(
                ((spec.get("higher_timeframe_policy") or {}).get("policy"))
                or "partial_from_m15_no_leak"
            ),
        )
        mso = market_state_mod.compute_market_state(raw_data, event.config)
        row.update(_evaluate_pre_ai(candle, mso, event.config))
        row.update(_mso_feature_counts(mso, raw_data))
        setup_projection, setup = mechanical_setup_projection(
            candle=candle,
            mso=mso,
            row=row,
            baseline_cfg=_baseline_config_from_config(event.config),
        )
        row.update(setup_projection)
    except Exception as exc:  # noqa: BLE001 - row-level research audit
        row.update(error_projection(exc))
        row.update(empty_mechanical_setup_projection("mso_error"))
    row["raw_cohort_key"] = raw_cohort_key(row)
    return row, alignment, setup


def base_event_row(
    candle: OpportunityCandle,
    *,
    replay_index: int,
    spec: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "raw_ohlc_prequential_event_v1",
        "event_key": f"{candle.symbol}|{candle.candle_close_utc.isoformat()}",
        "replay_index": replay_index,
        "symbol": candle.symbol,
        "broker_symbol": candle.broker_symbol,
        "timeframe": candle.timeframe,
        "bar_time_utc": candle.bar_time_utc.isoformat(),
        "candle_close_utc": candle.candle_close_utc.isoformat(),
        "kill_zone": candle.kill_zone,
        "session": candle.session,
        "year": str(candle.candle_close_utc.year),
        "month": f"{candle.candle_close_utc.year:04d}-{candle.candle_close_utc.month:02d}",
        "day_of_week": candle.candle_close_utc.strftime("%A"),
        "hour_utc": candle.candle_close_utc.hour,
        "bundle_id": DEFAULT_BUNDLE_ID,
        "replay_policy": spec.get("strategy_id"),
        "paid_ai_replay": False,
        "ai_call_attempted": False,
        "ai_call_count": 0,
        "ohlcv_open": candle.open,
        "ohlcv_high": candle.high,
        "ohlcv_low": candle.low,
        "ohlcv_close": candle.close,
    }


def build_raw_data_prequential(
    *,
    series_by_tf: Mapping[str, CandleSeries],
    candle: OpportunityCandle,
    config: Mapping[str, Any],
    htf_policy: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    lookbacks = dict(LOOKBACK)
    lookbacks.update((config.get("data") or {}).get("lookback", {}) or {})
    slices, alignment = build_asof_slices(
        series_by_tf=series_by_tf,
        candle_close_utc=candle.candle_close_utc,
        lookbacks={tf: int(lookbacks.get(tf, LOOKBACK.get(tf, 100))) for tf in ("D1", "H4", "H1", "M15")},
        htf_policy=htf_policy,
    )
    equal_level_tolerance = float((config.get("model_a") or {}).get("equal_level_tolerance", 2.50))
    session_levels = compute_session_levels_no_leak(
        m15=series_by_tf.get("M15"),
        target_date=candle.bar_time_utc.date(),
        candle_close_utc=candle.candle_close_utc,
    )
    raw_data = {
        "symbol": candle.symbol,
        "timestamp_utc": _iso_z(candle.candle_close_utc),
        "candle_open_utc": _iso_z(candle.bar_time_utc),
        "candle_close_utc": _iso_z(candle.candle_close_utc),
        "candle_timestamp_source": "historical_mt5_bar_open_plus_timeframe",
        "candles": slices,
        "session_levels": session_levels,
        "equal_highs_H4": detect_equal_levels(slices.get("H4", []), "high", equal_level_tolerance),
        "equal_lows_H4": detect_equal_levels(slices.get("H4", []), "low", equal_level_tolerance),
        "equal_highs_H1": detect_equal_levels(slices.get("H1", []), "high", equal_level_tolerance),
        "equal_lows_H1": detect_equal_levels(slices.get("H1", []), "low", equal_level_tolerance),
        "spread_cents": None,
        "high_impact_events": [],
        "data_quality": {
            "all_timeframes_complete": all(
                len(slices.get(tf, [])) >= int(float(lookbacks.get(tf, 100)) * 0.9)
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
    return raw_data, alignment


def build_asof_slices(
    *,
    series_by_tf: Mapping[str, CandleSeries],
    candle_close_utc: datetime,
    lookbacks: Mapping[str, int],
    htf_policy: str = "partial_from_m15_no_leak",
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    slices: dict[str, list[dict[str, Any]]] = {}
    alignment: dict[str, Any] = {
        "htf_policy": htf_policy,
        "future_candle_exposure_violations": 0,
        "htf_asof_violations": 0,
    }
    for timeframe in ("D1", "H4", "H1", "M15"):
        series = series_by_tf.get(timeframe)
        lookback = int(lookbacks.get(timeframe, LOOKBACK.get(timeframe, 100)))
        if series is None:
            slices[timeframe] = []
            alignment[f"lookback_count__{timeframe}"] = 0
            continue
        if timeframe == "M15":
            rows = closed_rows(series, candle_close_utc, lookback=lookback)
            diag = alignment_for_rows(series, rows, candle_close_utc, timeframe=timeframe)
        elif htf_policy == "closed_only":
            rows = closed_rows(series, candle_close_utc, lookback=lookback)
            diag = alignment_for_rows(series, rows, candle_close_utc, timeframe=timeframe)
        elif htf_policy == "partial_from_m15_no_leak":
            rows, diag = htf_rows_with_partial_from_m15(
                native=series,
                m15=series_by_tf.get("M15"),
                timeframe=timeframe,
                candle_close_utc=candle_close_utc,
                lookback=lookback,
            )
        else:
            raise ValueError(f"unsupported HTF policy {htf_policy!r}")
        slices[timeframe] = rows
        alignment.update(diag)
        if any(row_close_after(row, timeframe, candle_close_utc) for row in rows):
            alignment["future_candle_exposure_violations"] += 1
            if timeframe in HTF_TIMEFRAMES:
                alignment["htf_asof_violations"] += 1
    return slices, alignment


def closed_rows(series: CandleSeries, cutoff: datetime, *, lookback: int) -> list[dict[str, Any]]:
    idx = bisect.bisect_right(series.close_times, cutoff)
    if idx <= 0:
        return []
    return [dict(row) for row in series.rows[max(0, idx - lookback) : idx]]


def htf_rows_with_partial_from_m15(
    *,
    native: CandleSeries,
    m15: CandleSeries | None,
    timeframe: str,
    candle_close_utc: datetime,
    lookback: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    period_start = floor_timeframe(candle_close_utc, timeframe)
    rows = closed_rows(native, candle_close_utc, lookback=lookback)
    partial = None
    if period_start < candle_close_utc and m15 is not None:
        partial = aggregate_partial_bar_from_m15(
            m15=m15,
            period_start=period_start,
            candle_close_utc=candle_close_utc,
        )
    if partial is not None:
        rows = rows + [partial]
    rows = sorted(rows, key=lambda row: ensure_utc(str(row["time"])))[-lookback:]
    diag = alignment_for_rows(native, rows, candle_close_utc, timeframe=timeframe)
    diag[f"partial_bar_included__{timeframe}"] = partial is not None
    diag[f"partial_bar_start__{timeframe}"] = _iso_z(period_start) if partial is not None else None
    return rows, diag


def aggregate_partial_bar_from_m15(
    *,
    m15: CandleSeries,
    period_start: datetime,
    candle_close_utc: datetime,
) -> dict[str, Any] | None:
    start_idx = bisect.bisect_left(m15.open_times, period_start)
    end_idx = bisect.bisect_right(m15.close_times, candle_close_utc)
    rows = [
        m15.rows[idx]
        for idx in range(start_idx, end_idx)
        if m15.open_times[idx] >= period_start and m15.close_times[idx] <= candle_close_utc
    ]
    if not rows:
        return None
    return {
        "time": _iso_z(period_start),
        "open": float(rows[0]["open"]),
        "high": max(float(row["high"]) for row in rows),
        "low": min(float(row["low"]) for row in rows),
        "close": float(rows[-1]["close"]),
        "volume": sum(_float_or_zero(row.get("volume")) for row in rows),
        "_asof_partial": True,
    }


def alignment_for_rows(
    series: CandleSeries,
    rows: Sequence[Mapping[str, Any]],
    candle_close_utc: datetime,
    *,
    timeframe: str,
) -> dict[str, Any]:
    if not rows:
        return {
            f"lookback_count__{timeframe}": 0,
            f"asof_last_open__{timeframe}": None,
            f"asof_last_close__{timeframe}": None,
        }
    last_open = ensure_utc(str(rows[-1]["time"]))
    last_close = last_open + timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
    return {
        f"lookback_count__{timeframe}": len(rows),
        f"asof_last_open__{timeframe}": _iso_z(last_open),
        f"asof_last_close__{timeframe}": _iso_z(min(last_close, candle_close_utc)),
        f"source_path__{timeframe}": series.source_path,
        f"source_kind__{timeframe}": series.source_kind,
    }


def row_close_after(row: Mapping[str, Any], timeframe: str, cutoff: datetime) -> bool:
    if row.get("_asof_partial"):
        return False
    opened = ensure_utc(str(row["time"]))
    close = opened + timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
    return close > cutoff


def floor_timeframe(value: datetime, timeframe: str) -> datetime:
    value = value.astimezone(timezone.utc)
    tf = timeframe.upper()
    if tf == "H1":
        return value.replace(minute=0, second=0, microsecond=0)
    if tf == "H4":
        block_hour = (value.hour // 4) * 4
        return value.replace(hour=block_hour, minute=0, second=0, microsecond=0)
    if tf == "D1":
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    if tf == "M15":
        minute = (value.minute // 15) * 15
        return value.replace(minute=minute, second=0, microsecond=0)
    raise ValueError(f"unsupported timeframe for floor: {timeframe!r}")


def compute_session_levels_no_leak(
    *,
    m15: CandleSeries | None,
    target_date: Any,
    candle_close_utc: datetime,
) -> dict[str, Any]:
    if m15 is None:
        return empty_session_levels()
    prev_date = previous_weekday(target_date)
    prev_day = m15_rows_for_date_window(
        m15,
        day=prev_date,
        start_time=time_min(),
        end_time=time_max(),
        cutoff=None,
        inclusive_end=True,
    )
    asian = m15_rows_for_date_window(
        m15,
        day=target_date,
        start_time=ASIAN_START,
        end_time=ASIAN_END,
        cutoff=candle_close_utc,
    )
    session_m15 = m15_rows_for_date_window(
        m15,
        day=target_date,
        start_time=LONDON_OPEN_START,
        end_time=LONDON_OPEN_END,
        cutoff=candle_close_utc,
        inclusive_end=True,
    )
    london_m15 = m15_rows_for_date_window(
        m15,
        day=target_date,
        start_time=LONDON_SESSION_START,
        end_time=LONDON_SESSION_END,
        cutoff=candle_close_utc,
    )
    return {
        "asian_high": max((float(row["high"]) for row in asian), default=0.0),
        "asian_low": min((float(row["low"]) for row in asian), default=0.0),
        "pdh": max((float(row["high"]) for row in prev_day), default=0.0),
        "pdl": min((float(row["low"]) for row in prev_day), default=0.0),
        "session_high": max((float(row["high"]) for row in session_m15), default=None),
        "session_low": min((float(row["low"]) for row in session_m15), default=None),
        "london_high": max((float(row["high"]) for row in london_m15), default=None),
        "london_low": min((float(row["low"]) for row in london_m15), default=None),
    }


def m15_rows_for_date_window(
    series: CandleSeries,
    *,
    day: Any,
    start_time: Any,
    end_time: Any,
    cutoff: datetime | None,
    inclusive_end: bool = False,
) -> list[dict[str, Any]]:
    start_dt = datetime.combine(day, start_time, tzinfo=timezone.utc)
    end_dt = datetime.combine(day, end_time, tzinfo=timezone.utc)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    upper = min(cutoff, end_dt + timedelta(minutes=15)) if cutoff else end_dt + timedelta(minutes=15)
    start_idx = bisect.bisect_left(series.open_times, start_dt)
    end_idx = bisect.bisect_right(series.close_times, upper)
    output: list[dict[str, Any]] = []
    for idx in range(start_idx, end_idx):
        opened_at = series.open_times[idx]
        closed_at = series.close_times[idx]
        if cutoff is not None and closed_at > cutoff:
            continue
        if opened_at < start_dt:
            continue
        if inclusive_end:
            if opened_at.time() > end_time and opened_at.date() == day:
                continue
            if opened_at >= end_dt + timedelta(minutes=15):
                continue
        else:
            if opened_at >= end_dt:
                continue
        output.append(series.rows[idx])
    return output


def time_min() -> Any:
    return datetime.min.time()


def time_max() -> Any:
    return datetime.max.time().replace(microsecond=0)


def previous_weekday(day: Any) -> Any:
    prev = day - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev


def empty_session_levels() -> dict[str, Any]:
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


def mechanical_setup_projection(
    *,
    candle: OpportunityCandle,
    mso: Any,
    row: Mapping[str, Any],
    baseline_cfg: Any,
) -> tuple[dict[str, Any], MechanicalSetup | None]:
    if not row.get("would_send_ai"):
        return empty_mechanical_setup_projection("not_would_send_ai"), None
    bias = str(row.get("deterministic_bias") or "")
    side = {"bullish": "LONG", "bearish": "SHORT"}.get(bias)
    if side is None:
        return empty_mechanical_setup_projection("bias_not_directional"), None
    mso_mapping = mso.model_dump(mode="json") if hasattr(mso, "model_dump") else {}
    setup = compute_mechanical_entry(
        mso_mapping,
        side,
        symbol=candle.symbol,
        candle_close_time=candle.candle_close_utc,
        framework="ob_retest",
        cfg=baseline_cfg,
        cand_id=row.get("event_key"),
    )
    if setup.skip_reason:
        output = empty_mechanical_setup_projection(setup.skip_reason)
        output.update(
            {
                "mechanical_framework": setup.framework,
                "mechanical_side": side,
                "mechanical_setup_status": "SKIPPED",
            }
        )
        return output, None
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
    }, setup


def empty_mechanical_setup_projection(reason: str) -> dict[str, Any]:
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
    }


def error_projection(exc: Exception) -> dict[str, Any]:
    return {
        "deterministic_bias": None,
        "deterministic_bias_source": None,
        "deterministic_bias_d1": None,
        "deterministic_bias_h4": None,
        "deterministic_bias_h1": None,
        "deterministic_bias_m15": None,
        "pre_ai_gate_status": "MSO_ERROR",
        "pre_ai_gate_reason": f"{type(exc).__name__}:{exc}",
        "would_send_ai": False,
        "news_calendar_gate_status": "NOT_EVALUATED_OFFLINE",
        "mso_error_type": type(exc).__name__,
        "all_timeframes_complete": None,
    }


def raw_cohort_key(row: Mapping[str, Any]) -> str | None:
    bias = row.get("deterministic_bias")
    source = row.get("deterministic_bias_source")
    if not bias or not source:
        return None
    if bias == "no_bias" or source == "none":
        return None
    return f"{row.get('symbol')}|{row.get('session')}|{bias}|{source}"


def project_observation(row: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    projection = spec.get("observation_projection") or {}
    observation = {
        str(field): row.get(str(field))
        for field in projection.get("allowed_direct_fields") or []
    }
    aliases = projection.get("safe_aliases") or {}
    for alias in aliases:
        alias = str(alias)
        if alias == "raw_cohort_key":
            observation[alias] = raw_cohort_key(row)
        else:
            raise ValueError(f"unsupported raw replay safe alias: {alias!r}")
    return observation


def forbidden_observation_fields(
    observation: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> list[str]:
    projection = spec.get("observation_projection") or {}
    forbidden_fields = {
        str(field)
        for field in projection.get("forbidden_strategy_fields")
        or sorted(FORBIDDEN_OBSERVATION_FIELDS)
    }
    forbidden_prefixes = [
        str(prefix)
        for prefix in projection.get("forbidden_strategy_prefixes")
        or list(FORBIDDEN_OBSERVATION_PREFIXES)
    ]
    violations: list[str] = []
    for field in observation:
        if field in forbidden_fields or any(str(field).startswith(prefix) for prefix in forbidden_prefixes):
            violations.append(str(field))
    return violations


def decide_from_cohorts(
    observation: Mapping[str, Any],
    *,
    active_cohort_keys: set[str],
    blocked_cohort_keys: set[str],
    include_blocked_controls: bool,
) -> dict[str, str]:
    cohort_key = str(observation.get("raw_cohort_key") or "")
    if cohort_key in blocked_cohort_keys and not include_blocked_controls:
        return {"action": "SKIP", "reason": "blocked_control_not_enabled"}
    if cohort_key in active_cohort_keys:
        return {"action": "TAKE", "reason": "raw_cohort_match"}
    return {"action": "SKIP", "reason": "raw_cohort_non_match"}


def score_after_decision(
    *,
    row: Mapping[str, Any],
    setup: MechanicalSetup | None,
    event: ReplayEvent,
    data_dirs: Sequence[str | Path],
    max_hold_bars: int,
    timeframe: str,
    cache: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    pre_ai_status = str(row.get("pre_ai_gate_status") or "UNKNOWN")
    if pre_ai_status != "WOULD_SEND_AI":
        return {
            **empty_outcome_projection(),
            "mechanical_outcome": pre_ai_status,
            "mechanical_outcome_skip_reason": row.get("pre_ai_gate_reason"),
        }
    if setup is None:
        return {
            **empty_outcome_projection(),
            "mechanical_outcome": "SETUP_NOT_REFINABLE",
            "mechanical_outcome_skip_reason": row.get("mechanical_skip_reason"),
        }
    outcome_rows = _load_outcome_rows(
        roots=[Path(path) for path in data_dirs],
        symbol=event.symbol,
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
        "mechanical_outcome_timeframe": timeframe.upper(),
        "mechanical_max_hold_bars": max_hold_bars,
        "mechanical_outcome": outcome.outcome,
        "mechanical_realized_r": outcome.realized_r,
        "mechanical_bars_in_trade": outcome.bars_in_trade,
        "mechanical_exit_time": outcome.exit_time,
        "mechanical_outcome_skip_reason": outcome.skip_reason,
    }


def empty_outcome_projection() -> dict[str, Any]:
    return {
        "mechanical_outcome_timeframe": None,
        "mechanical_max_hold_bars": None,
        "mechanical_outcome": None,
        "mechanical_realized_r": None,
        "mechanical_bars_in_trade": None,
        "mechanical_exit_time": None,
        "mechanical_outcome_skip_reason": None,
    }


def new_score_state() -> dict[str, Any]:
    return {
        "actions_taken": 0,
        "action_outcomes": Counter(),
        "scoring_population_actions": 0,
        "scoring_exclusions": Counter(),
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "by_cohort": defaultdict(new_cohort_state),
        "by_month": defaultdict(new_period_state),
    }


def new_cohort_state() -> dict[str, Any]:
    return {
        "actions_taken": 0,
        "population_actions": 0,
        "resolved_r_n": 0,
        "sum_r": 0.0,
        "wins": 0,
        "outcomes": Counter(),
    }


def new_period_state() -> dict[str, Any]:
    return {"actions_taken": 0, "resolved_r_n": 0, "sum_r": 0.0}


def add_taken_action(
    state: dict[str, Any],
    *,
    row: Mapping[str, Any],
    observation: Mapping[str, Any],
    outcome: Mapping[str, Any],
    replay_index: int,
    scoring_spec: Mapping[str, Any],
) -> None:
    del replay_index
    state["actions_taken"] += 1
    outcome_name = str(outcome.get("mechanical_outcome") or "UNKNOWN")
    state["action_outcomes"][outcome_name] += 1
    cohort_key = str(observation.get("raw_cohort_key") or "")
    cohort = state["by_cohort"][cohort_key]
    cohort["actions_taken"] += 1
    cohort["outcomes"][outcome_name] += 1
    period = str(row.get("month") or str(row.get("candle_close_utc") or "")[:7])
    state["by_month"][period]["actions_taken"] += 1

    included, reasons = scoring_inclusion(row, outcome, scoring_spec)
    if not included:
        for reason in reasons:
            state["scoring_exclusions"][reason] += 1
        return
    state["scoring_population_actions"] += 1
    cohort["population_actions"] += 1
    if outcome_name not in set(scoring_spec.get("resolved_outcomes") or RESOLVED_OUTCOMES):
        return
    realized = as_float(outcome.get("mechanical_realized_r"))
    if realized is None:
        return
    state["resolved_r_n"] += 1
    state["sum_r"] += realized
    if realized > 0:
        state["wins"] += 1
    cohort["resolved_r_n"] += 1
    cohort["sum_r"] += realized
    if realized > 0:
        cohort["wins"] += 1
    state["by_month"][period]["resolved_r_n"] += 1
    state["by_month"][period]["sum_r"] += realized


def scoring_inclusion(
    row: Mapping[str, Any],
    outcome: Mapping[str, Any],
    scoring_spec: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if scoring_spec.get("setup_only", True) and row.get("mechanical_setup_status") != "OK":
        reasons.append("not_setup_row")
    if scoring_spec.get("require_would_send_ai", True) and not row.get("would_send_ai"):
        reasons.append("not_would_send_ai")
    if outcome.get("mechanical_outcome") in set(scoring_spec.get("exclude_outcomes") or ["SAME_BAR"]):
        reasons.append("mechanical_outcome_excluded")
    return not reasons, reasons


def finalize_score(state: Mapping[str, Any]) -> dict[str, Any]:
    resolved = int(state.get("resolved_r_n") or 0)
    sum_r = float(state.get("sum_r") or 0.0)
    return {
        "actions_taken": int(state.get("actions_taken") or 0),
        "scoring_population_actions": int(state.get("scoring_population_actions") or 0),
        "resolved_r_n": resolved,
        "sum_r": round(sum_r, 6),
        "mean_r": round(sum_r / resolved, 6) if resolved else None,
        "win_rate": round(float(state.get("wins") or 0) / resolved, 6) if resolved else None,
        "action_outcomes": dict(sorted((state.get("action_outcomes") or {}).items())),
        "scoring_exclusions": dict(sorted((state.get("scoring_exclusions") or {}).items())),
        "cohort_scores": cohort_rows(state.get("by_cohort") or {}),
        "period_scores": period_rows(state.get("by_month") or {}),
    }


def cohort_rows(states: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cohort_key, state in sorted(states.items()):
        resolved = int(state.get("resolved_r_n") or 0)
        sum_r = float(state.get("sum_r") or 0.0)
        rows.append(
            {
                "cohort_key": cohort_key,
                "actions_taken": int(state.get("actions_taken") or 0),
                "population_actions": int(state.get("population_actions") or 0),
                "resolved_r_n": resolved,
                "sum_r": round(sum_r, 6),
                "mean_r": round(sum_r / resolved, 6) if resolved else None,
                "win_rate": round(float(state.get("wins") or 0) / resolved, 6) if resolved else None,
                "outcomes": dict(sorted((state.get("outcomes") or {}).items())),
            }
        )
    return rows


def period_rows(states: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for period, state in sorted(states.items()):
        resolved = int(state.get("resolved_r_n") or 0)
        sum_r = float(state.get("sum_r") or 0.0)
        rows.append(
            {
                "period": period,
                "actions_taken": int(state.get("actions_taken") or 0),
                "resolved_r_n": resolved,
                "sum_r": round(sum_r, 6),
                "mean_r": round(sum_r / resolved, 6) if resolved else None,
            }
        )
    return rows


def event_log_record(
    *,
    replay_index: int,
    row: Mapping[str, Any],
    observation: Mapping[str, Any],
    decision: Mapping[str, Any],
    alignment: Mapping[str, Any],
    outcome: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "raw_ohlc_prequential_event_log_v1",
        "replay_index": replay_index,
        "event_key": row.get("event_key"),
        "candle_close_utc": row.get("candle_close_utc"),
        "symbol": row.get("symbol"),
        "session": row.get("session"),
        "raw_cohort_key": observation.get("raw_cohort_key"),
        "pre_ai_gate_status": row.get("pre_ai_gate_status"),
        "would_send_ai": row.get("would_send_ai"),
        "mechanical_setup_status": row.get("mechanical_setup_status"),
        "action": decision.get("action"),
        "decision_reason": decision.get("reason"),
        "decision_locked_before_outcome": True,
        "outcome": outcome.get("mechanical_outcome"),
        "realized_r": outcome.get("mechanical_realized_r"),
        "alignment": compact_alignment(alignment),
    }


def compact_alignment(alignment: Mapping[str, Any]) -> dict[str, Any]:
    keep = [
        "htf_policy",
        "future_candle_exposure_violations",
        "htf_asof_violations",
        "lookback_count__M15",
        "lookback_count__H1",
        "lookback_count__H4",
        "lookback_count__D1",
        "partial_bar_included__H1",
        "partial_bar_included__H4",
        "partial_bar_included__D1",
        "asof_last_close__M15",
        "asof_last_close__H1",
        "asof_last_close__H4",
        "asof_last_close__D1",
    ]
    return {key: alignment.get(key) for key in keep if key in alignment}


def integrity_summary(**counts: int) -> dict[str, Any]:
    blocking_keys = {
        "duplicate_event_keys",
        "invalid_clock_rows",
        "forbidden_observation_violations",
        "future_candle_exposure_violations",
        "htf_asof_violations",
        "ai_attempted_rows",
        "ai_call_count_sum",
    }
    failures = {key: value for key, value in counts.items() if key in blocking_keys and value}
    return {
        "clean_for_controlled_replay": not failures,
        "status": "PASS" if not failures else "BLOCKED",
        "blocking_counts": failures,
    }


def render_report(summary: Mapping[str, Any]) -> str:
    score = summary.get("score") or {}
    lines = [
        "# Phase 3 Raw-OHLC Prequential Replay Report",
        "",
        f"**Created UTC:** {summary.get('created_at_utc')}",
        f"**Spec:** `{summary.get('spec_path')}`",
        f"**Promotion verdict:** `{summary.get('promotion_verdict')}`",
        "",
        "## Boundary",
        "",
        "- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.",
        "- Replay walks raw M15 candles in chronological order and reconstructs as-of observations from candle windows.",
        "- HTF bars use the registered no-leak policy before a decision is locked.",
        "- Mechanical outcomes are attached only after TAKE/SKIP is fixed.",
        "- DSR, PBO, effective_N, and prospective confirmation are not computed here.",
        "",
        "## Reproducibility",
        "",
        markdown_table(
            [
                {
                    "spec_sha256": summary.get("spec_sha256"),
                    "code_commit": summary.get("code_commit"),
                    "run_mode": summary.get("run_mode"),
                    "evidence_class": summary.get("evidence_class"),
                    "event_log_sha256": summary.get("event_log_sha256"),
                }
            ]
        ),
        "",
        "## Run Scope",
        "",
        markdown_table(
            [
                {
                    "source_scope": (
                        "FULL_AVAILABLE_CORPUS"
                        if summary.get("max_candles_per_symbol") is None
                        and summary.get("max_events") is None
                        and summary.get("start") is None
                        and summary.get("end") is None
                        else "BOUNDED_DIAGNOSTIC"
                    ),
                    "start": summary.get("start"),
                    "end": summary.get("end"),
                    "max_candles_per_symbol": summary.get("max_candles_per_symbol"),
                    "max_events": summary.get("max_events"),
                    "include_blocked_controls": summary.get("include_blocked_controls"),
                    "symbols": ",".join(summary.get("symbols") or []),
                    "rows_replayed": summary.get("rows_replayed"),
                }
            ]
        ),
        "",
        "## Data Inventory",
        "",
        markdown_table(summary.get("data_inventory") or []),
        "",
        "## Active Cohorts",
        "",
        markdown_table(summary.get("active_cohorts") or []),
        "",
        "## Guardrails",
        "",
        markdown_table(
            [
                {
                    "rows_replayed": summary.get("rows_replayed"),
                    "duplicate_event_keys": summary.get("duplicate_event_keys"),
                    "invalid_clock_rows": summary.get("invalid_clock_rows"),
                    "future_candle_exposure_violations": summary.get("future_candle_exposure_violations"),
                    "htf_asof_violations": summary.get("htf_asof_violations"),
                    "forbidden_observation_violations": summary.get("forbidden_observation_violations"),
                    "ai_attempted_rows": summary.get("ai_attempted_rows"),
                    "ai_call_count_sum": summary.get("ai_call_count_sum"),
                    "integrity_status": (summary.get("integrity") or {}).get("status"),
                }
            ]
        ),
        "",
        "## Decision Counts",
        "",
        markdown_table([summary.get("decision_counts") or {}]),
        "",
        "## Pre-AI Gate Counts",
        "",
        markdown_table([summary.get("pre_ai_gate_counts") or {}]),
        "",
        "## Score",
        "",
        markdown_table(
            [
                {
                    "actions_taken": score.get("actions_taken"),
                    "scoring_population_actions": score.get("scoring_population_actions"),
                    "resolved_r_n": score.get("resolved_r_n"),
                    "sum_r": score.get("sum_r"),
                    "mean_r": score.get("mean_r"),
                    "win_rate": score.get("win_rate"),
                }
            ]
        ),
        "",
        "## Action Outcomes",
        "",
        markdown_table([score.get("action_outcomes") or {}]),
        "",
        "## Scoring Exclusions",
        "",
        markdown_table([score.get("scoring_exclusions") or {}]),
        "",
        "## Cohort Scores",
        "",
        markdown_table(score.get("cohort_scores") or []),
        "",
        "## Period Scores",
        "",
        markdown_table(score.get("period_scores") or []),
        "",
        "## Interpretation",
        "",
        "- This is a raw-candle replay adapter validation, not a promotion dossier.",
        "- The result can prioritize future research and catch leakage or data-coverage issues.",
        "- Same-dataset historical positives or negatives cannot be called live alpha proof.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(
    summary: Mapping[str, Any],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> tuple[Path, Path]:
    output_dir = Path(output_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = output_dir / f"raw_ohlc_prequential_replay_{stamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    report = Path(report_path)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(summary), encoding="utf-8")
    return summary_path, report


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return ensure_utc(str(value))
    except (TypeError, ValueError):
        return None


def sha256_file(path: str | Path | None) -> str | None:
    if path is None:
        return None
    source = Path(path)
    if not source.exists():
        return None
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit_or_unknown() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    commit = result.stdout.strip() or "unknown"
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return commit
    return f"{commit}+dirty" if status.stdout.strip() else commit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-path", default=DEFAULT_SPEC_PATH)
    parser.add_argument("--data-dir", action="append", help="Raw OHLC data directory. Repeatable.")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--max-candles-per-symbol", type=int)
    parser.add_argument("--max-events", type=int)
    parser.add_argument("--include-blocked-controls", action="store_true")
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    event_log_path = None
    if args.write:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        event_log_path = Path(args.output_root) / f"raw_ohlc_prequential_events_{stamp}.jsonl"
    summary = run_raw_ohlc_prequential_replay(
        spec_path=args.spec_path,
        data_dirs=args.data_dir,
        start=args.start,
        end=args.end,
        max_candles_per_symbol=args.max_candles_per_symbol,
        max_events=args.max_events,
        include_blocked_controls=args.include_blocked_controls,
        event_log_path=event_log_path,
    )
    if args.write:
        summary_path, report_path = write_outputs(
            summary,
            output_root=args.output_root,
            report_path=args.report_path,
        )
        summary = dict(summary)
        summary["output_summary"] = str(summary_path)
        summary["report_path"] = str(report_path)
    if args.quiet:
        print(
            json.dumps(
                {
                    "promotion_verdict": summary.get("promotion_verdict"),
                    "rows_replayed": summary.get("rows_replayed"),
                    "actions_taken": (summary.get("score") or {}).get("actions_taken"),
                    "resolved_r_n": (summary.get("score") or {}).get("resolved_r_n"),
                    "mean_r": (summary.get("score") or {}).get("mean_r"),
                    "integrity_status": (summary.get("integrity") or {}).get("status"),
                    "event_log_path": summary.get("event_log_path"),
                    "output_summary": summary.get("output_summary"),
                    "report_path": summary.get("report_path"),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
