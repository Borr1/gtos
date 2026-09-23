#!/usr/bin/env python3
"""Join GTOS candidate rows to Phase 3 external-feed validation snapshots.

The validation dataset is all-candle. This utility narrows it to the actual
GTOS candidate/opportunity population and adds trade-record outcome metadata
when available. It is research-only and writes ignored artifacts under
``data/external/validation/<bundle>/candidate_join`` when ``--write`` is used.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    ensure_utc,
    safe_slug,
    utc_now,
)
from scripts.build_external_feed_validation_dataset import (  # noqa: E402
    TIMEFRAME_MINUTES,
    validate_snapshot_no_lookahead,
)
from src.research_infra.dumb_baseline import (  # noqa: E402
    DEFAULT_MAX_HOLD_BARS,
    MechanicalSetup,
    resolve_mechanical_outcome,
)


DEFAULT_BUNDLE_ID = "calendar_macro_bundle_v1"
DEFAULT_CANDIDATE_PATH = Path("shadow_logs/candidate_features_log.jsonl")
DEFAULT_TRADE_RECORDS_ROOT = Path("knowledge_base/trade_records")
DEFAULT_DECISIONS = ("CANDIDATE",)
JOIN_SCHEMA_VERSION = "external_feed_candidate_join_v1"


@dataclass(frozen=True)
class TradeRecordOutcome:
    """Outcome metadata extracted from one trade-record JSON."""

    path: str
    trade_id: str | None
    final_outcome: str | None
    realized_r: float | None
    level2_passed: bool | None = None
    level2_blocked_by: Any = None
    gate1_status: Any = None
    gate3_status: Any = None


def normalize_candidate_candle_close(
    value: str | datetime,
    *,
    timeframe: str = "M15",
    require_aligned: bool = True,
) -> datetime | None:
    """Normalize a candidate timestamp to the evaluated candle close.

    GTOS live rows often carry candle-close time plus a few seconds of capture
    latency. We strip seconds/microseconds, then require the minute to be on a
    timeframe boundary by default. Off-boundary timestamps are left unmatched
    because assigning them to a nearby M15 candle would be lower-quality.
    """

    timeframe_key = timeframe.upper()
    if timeframe_key not in TIMEFRAME_MINUTES:
        raise ValueError(f"unsupported timeframe {timeframe!r}")
    parsed = ensure_utc(value).replace(second=0, microsecond=0)
    minutes = TIMEFRAME_MINUTES[timeframe_key]
    minute_of_day = parsed.hour * 60 + parsed.minute
    remainder = minute_of_day % minutes
    if remainder and require_aligned:
        return None
    if remainder:
        parsed = parsed - timedelta(minutes=remainder)
    return parsed


def load_candidate_rows(path: str | Path) -> list[dict[str, Any]]:
    """Load candidate feature JSONL rows and stamp source provenance."""

    rows: list[dict[str, Any]] = []
    candidate_path = Path(path)
    with candidate_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_candidate_path"] = str(candidate_path)
            row["_source_candidate_line"] = line_number
            rows.append(row)
    return rows


def load_trade_record_index(
    root: str | Path = DEFAULT_TRADE_RECORDS_ROOT,
    *,
    timeframe: str = "M15",
) -> dict[tuple[str, str], TradeRecordOutcome]:
    """Index trade records by ``(SYMBOL, normalized_candle_close_iso)``."""

    root_path = Path(root)
    if not root_path.exists():
        return {}
    index: dict[tuple[str, str], TradeRecordOutcome] = {}
    for json_path in sorted(root_path.glob("*/*.json")):
        try:
            record = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        meta = record.get("metadata", {}) if isinstance(record, Mapping) else {}
        if not isinstance(meta, Mapping):
            continue
        symbol = str(meta.get("symbol") or json_path.parent.name).upper()
        candle_time = meta.get("candle_close_utc") or meta.get("candle_time")
        if not candle_time:
            continue
        try:
            candle_close = normalize_candidate_candle_close(
                str(candle_time),
                timeframe=timeframe,
                require_aligned=True,
            )
        except (TypeError, ValueError):
            continue
        if candle_close is None:
            continue
        key = (symbol, candle_close.isoformat())
        current = index.get(key)
        outcome = _trade_record_outcome(record, json_path)
        if current is None or outcome.realized_r is not None:
            index[key] = outcome
    return index


def find_latest_validation_paths(
    root: str | Path = DEFAULT_EXTERNAL_DATA_ROOT,
    *,
    bundle_id: str = DEFAULT_BUNDLE_ID,
    label_contains: str | None = None,
) -> list[Path]:
    """Return latest validation JSONL per file symbol for a bundle."""

    validation_dir = Path(root) / "validation" / safe_slug(bundle_id)
    latest: dict[str, tuple[float, Path]] = {}
    for path in validation_dir.glob("*.jsonl"):
        if not path.is_file():
            continue
        if label_contains and label_contains not in path.name:
            continue
        symbol = _peek_validation_symbol(path)
        if not symbol:
            continue
        mtime = path.stat().st_mtime
        current = latest.get(symbol)
        if current is None or mtime > current[0]:
            latest[symbol] = (mtime, path)
    return [path for _mtime, path in sorted(latest.values(), key=lambda item: item[1].name)]


def load_validation_index(
    paths: Iterable[str | Path],
    *,
    needed_keys: set[tuple[str, str]] | None = None,
) -> dict[tuple[str, str], dict[str, Any]]:
    """Stream validation JSONL files and keep only rows needed for candidates."""

    index: dict[tuple[str, str], dict[str, Any]] = {}
    for raw_path in paths:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                candle_close = ensure_utc(str(row["candle_close_utc"]))
                validate_snapshot_no_lookahead(row, candle_close)
                aliases = _validation_symbol_aliases(row)
                for alias in aliases:
                    key = (alias, candle_close.isoformat())
                    if needed_keys is not None and key not in needed_keys:
                        continue
                    materialized = dict(row)
                    materialized["source_validation_path"] = str(path)
                    index.setdefault(key, materialized)
    return index


def build_candidate_validation_rows(
    *,
    candidate_rows: Iterable[Mapping[str, Any]],
    validation_index: Mapping[tuple[str, str], Mapping[str, Any]],
    trade_record_index: Mapping[tuple[str, str], TradeRecordOutcome] | None = None,
    decisions: Iterable[str] = DEFAULT_DECISIONS,
    timeframe: str = "M15",
    simulate_opportunity: bool = False,
    ohlcv_dir: str | Path = "data/historical_2026",
    ohlcv_dirs: Iterable[str | Path] | None = None,
    max_hold_bars: int = DEFAULT_MAX_HOLD_BARS,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build joined candidate rows plus a coverage summary."""

    allowed_decisions = {decision.upper() for decision in decisions}
    trade_records = trade_record_index or {}
    ohlcv_roots = [Path(path) for path in (ohlcv_dirs or [ohlcv_dir])]
    output: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    final_outcomes: Counter[str] = Counter()
    synthetic_outcomes: Counter[str] = Counter()
    symbols: Counter[str] = Counter()
    missing_reasons: Counter[str] = Counter()
    first_ts: str | None = None
    last_ts: str | None = None

    for candidate in candidate_rows:
        counters["candidate_rows_read"] += 1
        decision = str(candidate.get("decision") or candidate.get("ai_decision") or "").upper()
        if allowed_decisions and decision not in allowed_decisions:
            counters["decision_filtered"] += 1
            continue
        counters["candidate_rows_kept"] += 1
        decision_counts[decision or "UNKNOWN"] += 1

        symbol = str(candidate.get("symbol") or "").upper()
        timestamp = str(candidate.get("timestamp_utc") or "")
        canonical_candle_time = candidate.get("candle_close_utc")
        if timestamp:
            first_ts = min(first_ts, timestamp) if first_ts else timestamp
            last_ts = max(last_ts, timestamp) if last_ts else timestamp

        missing_reason: str | None = None
        key: tuple[str, str] | None = None
        candle_close: datetime | None = None
        try:
            candle_source = canonical_candle_time or timestamp
            candle_close = normalize_candidate_candle_close(
                str(candle_source),
                timeframe=timeframe,
            )
        except (TypeError, ValueError):
            missing_reason = "candidate_timestamp_parse_error"
        if missing_reason is None and candle_close is None:
            missing_reason = "candidate_timestamp_not_m15_aligned"
        if missing_reason is None:
            key = (symbol, candle_close.isoformat())  # type: ignore[union-attr]

        validation_row = validation_index.get(key) if key else None
        if validation_row is None and missing_reason is None:
            missing_reason = "validation_row_not_found"

        trade_outcome = trade_records.get(key) if key else None
        final_outcome = trade_outcome.final_outcome if trade_outcome else None
        if final_outcome:
            final_outcomes[final_outcome] += 1

        if validation_row:
            joined = dict(validation_row)
            counters["validation_matched"] += 1
        else:
            joined = {
                "symbol": symbol,
                "candle_close_utc": candle_close.isoformat() if candle_close else None,
            }
            counters["validation_missing"] += 1
            missing_reasons[missing_reason or "unknown"] += 1

        joined.update(_candidate_projection(candidate))
        if simulate_opportunity:
            synthetic = _simulate_candidate_opportunity(
                candidate,
                candle_close=candle_close,
                ohlcv_dirs=ohlcv_roots,
                timeframe=timeframe,
                max_hold_bars=max_hold_bars,
            )
            joined.update(synthetic)
            synthetic_outcome = synthetic.get("candidate__synthetic_outcome")
            if synthetic_outcome:
                synthetic_outcomes[str(synthetic_outcome)] += 1
            if synthetic.get("candidate__synthetic_realized_r") is not None:
                counters["synthetic_realized_r_available"] += 1
            else:
                counters["synthetic_realized_r_missing"] += 1
        joined.update(
            {
                "candidate_join_schema_version": JOIN_SCHEMA_VERSION,
                "candidate__candle_close_utc": candle_close.isoformat() if candle_close else None,
                "external_validation_matched": validation_row is not None,
                "external_validation_missing_reason": missing_reason if validation_row is None else None,
                "candidate__trade_record_matched": trade_outcome is not None,
                "candidate__trade_record_path": trade_outcome.path if trade_outcome else None,
                "candidate__trade_id": trade_outcome.trade_id if trade_outcome else None,
                "candidate__final_outcome": final_outcome,
                "candidate__level2_passed": trade_outcome.level2_passed if trade_outcome else None,
                "candidate__level2_blocked_by": trade_outcome.level2_blocked_by if trade_outcome else None,
                "candidate__gate1_status": trade_outcome.gate1_status if trade_outcome else None,
                "candidate__gate3_status": trade_outcome.gate3_status if trade_outcome else None,
                "candidate__realized_r": trade_outcome.realized_r if trade_outcome else None,
                "candidate__realized_r_available": (
                    trade_outcome is not None and trade_outcome.realized_r is not None
                ),
                "candidate__realized_r_missing_reason": _realized_r_missing_reason(trade_outcome),
            }
        )
        symbols[symbol] += 1
        if trade_outcome:
            counters["trade_record_matched"] += 1
            if trade_outcome.realized_r is not None:
                counters["realized_r_available"] += 1
            else:
                counters["realized_r_missing"] += 1
        else:
            counters["trade_record_missing"] += 1
            counters["realized_r_missing"] += 1
        output.append(joined)

    summary = {
        "schema_version": "external_feed_candidate_join_summary_v1",
        "join_schema_version": JOIN_SCHEMA_VERSION,
        "timeframe": timeframe.upper(),
        "decisions": sorted(allowed_decisions),
        "candidate_rows_read": counters["candidate_rows_read"],
        "candidate_rows_kept": counters["candidate_rows_kept"],
        "decision_filtered": counters["decision_filtered"],
        "validation_matched": counters["validation_matched"],
        "validation_missing": counters["validation_missing"],
        "trade_record_matched": counters["trade_record_matched"],
        "trade_record_missing": counters["trade_record_missing"],
        "realized_r_available": counters["realized_r_available"],
        "realized_r_missing": counters["realized_r_missing"],
        "synthetic_opportunity_simulated": simulate_opportunity,
        "synthetic_realized_r_available": counters["synthetic_realized_r_available"],
        "synthetic_realized_r_missing": counters["synthetic_realized_r_missing"],
        "first_candidate_timestamp_utc": first_ts,
        "last_candidate_timestamp_utc": last_ts,
        "symbols": dict(sorted(symbols.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "final_outcomes": dict(sorted(final_outcomes.items())),
        "synthetic_outcomes": dict(sorted(synthetic_outcomes.items())),
        "validation_missing_reasons": dict(sorted(missing_reasons.items())),
    }
    return output, summary


def write_candidate_join_artifacts(
    *,
    root: str | Path,
    bundle_id: str,
    label: str,
    rows: Iterable[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Write joined rows and summary under the ignored validation tree."""

    stamp = utc_now()
    output_dir = Path(root) / "validation" / safe_slug(bundle_id) / "candidate_join"
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_label = safe_slug(label)
    rows_path = output_dir / f"{safe_label}_{stamp:%Y%m%dT%H%M%SZ}.jsonl"
    materialized = [dict(row) for row in rows]
    with rows_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in materialized:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    final_summary = dict(summary)
    final_summary.update(
        {
            "created_at_utc": stamp.isoformat(),
            "rows_path": str(rows_path),
            "rows_written": len(materialized),
        }
    )
    summary_path = output_dir / f"{safe_label}_summary_{stamp:%Y%m%dT%H%M%SZ}.json"
    summary_path.write_text(
        json.dumps(final_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    final_summary["summary_path"] = str(summary_path)
    return final_summary


def _candidate_projection(candidate: Mapping[str, Any]) -> dict[str, Any]:
    trade_parameters = candidate.get("trade_parameters")
    if not isinstance(trade_parameters, Mapping):
        trade_parameters = {}
    return {
        "candidate__timestamp_utc": candidate.get("timestamp_utc"),
        "candidate__logged_candle_close_utc": candidate.get("candle_close_utc"),
        "candidate__timestamp_candle_lag_seconds": candidate.get(
            "timestamp_candle_lag_seconds"
        ),
        "candidate__symbol": candidate.get("symbol"),
        "candidate__evaluation_id": candidate.get("evaluation_id"),
        "candidate__source_path": candidate.get("_source_candidate_path"),
        "candidate__source_line": candidate.get("_source_candidate_line"),
        "candidate__kill_zone": candidate.get("kill_zone"),
        "candidate__session_tag": candidate.get("session_tag"),
        "candidate__decision": candidate.get("decision") or candidate.get("ai_decision"),
        "candidate__framework": candidate.get("framework"),
        "candidate__setup_grade": candidate.get("setup_grade"),
        "candidate__ai_no_trade_reason": candidate.get("ai_no_trade_reason"),
        "candidate__direction": trade_parameters.get("direction") or candidate.get("ai_direction_evaluated"),
        "candidate__entry_price": trade_parameters.get("entry_price"),
        "candidate__stop_loss": trade_parameters.get("stop_loss"),
        "candidate__take_profit_1": trade_parameters.get("take_profit_1"),
        "candidate__risk_reward_ratio": trade_parameters.get("risk_reward_ratio"),
        "candidate__c_gate_result": candidate.get("c_gate_result"),
        "candidate__daily_bias_direction": candidate.get("daily_bias_direction"),
        "candidate__daily_bias_confidence": candidate.get("daily_bias_confidence"),
        "candidate__h4_aligned": candidate.get("h4_aligned"),
        "candidate__m15_choch_detected": candidate.get("m15_choch_detected"),
        "candidate__h1_opp_ob_touch": candidate.get("h1_opp_ob_touch"),
        "candidate__h1_opp_ob_touch_long": candidate.get("h1_opp_ob_touch_long"),
        "candidate__h1_opp_ob_touch_short": candidate.get("h1_opp_ob_touch_short"),
        "candidate__h1_fvg_unfilled_count": candidate.get("h1_fvg_unfilled_count"),
        "candidate__m15_fvg_unfilled_count": candidate.get("m15_fvg_unfilled_count"),
        "candidate__mso_h1_structure_direction": candidate.get("mso_h1_structure_direction"),
        "candidate__mso_m15_structure_direction": candidate.get("mso_m15_structure_direction"),
        "candidate__mso_d1_structure_direction": candidate.get("mso_d1_structure_direction"),
        "candidate__mso_h1_unmitigated_ob_count": candidate.get("mso_h1_unmitigated_ob_count"),
        "candidate__mso_h1_nearest_ob_distance_atr": candidate.get("mso_h1_nearest_ob_distance_atr"),
        "candidate__mso_m15_clv_current": candidate.get("mso_m15_clv_current"),
        "candidate__mso_m15_clv_avg_5": candidate.get("mso_m15_clv_avg_5"),
        "candidate__mso_m15_bvc_buy_fraction": candidate.get("mso_m15_bvc_buy_fraction"),
        "candidate__mso_m15_net_flow_5": candidate.get("mso_m15_net_flow_5"),
        "candidate__pre_ai_gate_skipped": candidate.get("pre_ai_gate_skipped"),
        "candidate__pre_ai_gate_reason": candidate.get("pre_ai_gate_reason"),
        "candidate__detector_version_at_eval": candidate.get("detector_version_at_eval"),
        "candidate__slice_tag": candidate.get("slice_tag"),
    }


def _simulate_candidate_opportunity(
    candidate: Mapping[str, Any],
    *,
    candle_close: datetime | None,
    ohlcv_dirs: Iterable[Path],
    timeframe: str,
    max_hold_bars: int,
) -> dict[str, Any]:
    """Resolve candidate trade parameters through future OHLCV."""

    if candle_close is None:
        return _synthetic_missing("candidate_candle_close_unavailable")
    trade_parameters = candidate.get("trade_parameters")
    if not isinstance(trade_parameters, Mapping):
        return _synthetic_missing("candidate_trade_parameters_missing")
    side = str(
        trade_parameters.get("direction") or candidate.get("ai_direction_evaluated") or ""
    ).upper()
    if side not in {"LONG", "SHORT"}:
        return _synthetic_missing("candidate_direction_missing")
    try:
        entry = float(trade_parameters["entry_price"])
        sl = float(trade_parameters["stop_loss"])
        tp = float(trade_parameters["take_profit_1"])
    except (KeyError, TypeError, ValueError):
        return _synthetic_missing("candidate_price_fields_missing")
    sl_dist = abs(entry - sl)
    if sl_dist <= 0:
        return _synthetic_missing("candidate_degenerate_sl")
    symbol = str(candidate.get("symbol") or "").upper()
    setup = MechanicalSetup(
        cand_id=f"{symbol}|{candle_close.isoformat()}",
        symbol=symbol,
        candle_close_time=candle_close,
        side=side,
        framework=str(candidate.get("framework") or ""),
        ob_high=0.0,
        ob_low=0.0,
        entry=entry,
        sl=sl,
        tp=tp,
        rr=abs(tp - entry) / sl_dist,
    )
    roots = list(ohlcv_dirs)
    chosen: dict[str, Any] | None = None
    for root in roots:
        if not _has_near_future_bar(symbol, root, candle_close, timeframe=timeframe):
            chosen = {
                "candidate__synthetic_outcome": "NO_DATA",
                "candidate__synthetic_realized_r": None,
                "candidate__synthetic_bars_in_trade": 0,
                "candidate__synthetic_exit_time": None,
                "candidate__synthetic_skip_reason": "NO_CONTIGUOUS_FUTURE_BARS",
                "candidate__synthetic_max_hold_bars": max_hold_bars,
                "candidate__synthetic_ohlcv_dir": str(root),
                "candidate__synthetic_ohlcv_dirs_tried": [str(path) for path in roots],
            }
            continue
        outcome = resolve_mechanical_outcome(
            setup,
            ohlcv_dir=root,
            max_hold_bars=max_hold_bars,
            ohlcv_rows=_load_ohlcv_rows(symbol, root, timeframe=timeframe),
            require_pending_fill=True,
        )
        rendered = {
            "candidate__synthetic_outcome": outcome.outcome,
            "candidate__synthetic_realized_r": outcome.realized_r,
            "candidate__synthetic_bars_in_trade": outcome.bars_in_trade,
            "candidate__synthetic_exit_time": outcome.exit_time,
            "candidate__synthetic_skip_reason": outcome.skip_reason,
            "candidate__synthetic_max_hold_bars": max_hold_bars,
            "candidate__synthetic_ohlcv_dir": str(root),
            "candidate__synthetic_ohlcv_dirs_tried": [str(path) for path in roots],
        }
        chosen = rendered
        if not (
            outcome.outcome == "NO_DATA"
            and outcome.skip_reason in {"OHLCV_MISSING", "NO_FUTURE_BARS", "ALL_BARS_BAD"}
        ):
            return rendered
    if chosen is not None:
        return chosen
    return {
        "candidate__synthetic_outcome": "NO_DATA",
        "candidate__synthetic_realized_r": None,
        "candidate__synthetic_bars_in_trade": 0,
        "candidate__synthetic_exit_time": None,
        "candidate__synthetic_skip_reason": "OHLCV_ROOTS_EMPTY",
        "candidate__synthetic_max_hold_bars": max_hold_bars,
        "candidate__synthetic_ohlcv_dir": None,
        "candidate__synthetic_ohlcv_dirs_tried": [],
    }


def _has_near_future_bar(
    symbol: str,
    root: Path,
    candle_close: datetime,
    *,
    timeframe: str,
) -> bool:
    """Require the first future OHLCV bar to be near the candidate candle."""

    timeframe_key = timeframe.upper()
    minutes = TIMEFRAME_MINUTES.get(timeframe_key)
    if minutes is None:
        return False
    path = _resolve_ohlcv_path(symbol, root, timeframe_key)
    if path is None:
        return False
    max_gap = timedelta(minutes=minutes * 2)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "time" not in reader.fieldnames:
                return False
            for row in reader:
                raw_time = row.get("time")
                if not raw_time:
                    continue
                try:
                    bar_time = ensure_utc(str(raw_time))
                except (TypeError, ValueError):
                    continue
                if bar_time > candle_close:
                    return bar_time - candle_close <= max_gap
    except OSError:
        return False
    return False


def _resolve_ohlcv_path(symbol: str, root: Path, timeframe: str) -> Path | None:
    for stem in _ohlcv_stems(symbol):
        path = root / f"{stem}_{timeframe}.csv"
        if path.exists():
            return path
    return None


_OHLCV_ROWS_CACHE: dict[tuple[str, str, str], list[dict[str, Any]]] = {}


def _load_ohlcv_rows(symbol: str, root: Path, *, timeframe: str) -> list[dict[str, Any]]:
    """Load timeframe-specific OHLCV rows for the candidate simulator."""

    timeframe_key = timeframe.upper()
    cache_key = (str(root.resolve()), symbol.upper(), timeframe_key)
    if cache_key in _OHLCV_ROWS_CACHE:
        return _OHLCV_ROWS_CACHE[cache_key]
    path = _resolve_ohlcv_path(symbol, root, timeframe_key)
    if path is None:
        _OHLCV_ROWS_CACHE[cache_key] = []
        return []
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"time", "open", "high", "low", "close"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                _OHLCV_ROWS_CACHE[cache_key] = []
                return []
            for row in reader:
                try:
                    rows.append(
                        {
                            "time": ensure_utc(str(row["time"])),
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError:
        rows = []
    rows.sort(key=lambda item: item["time"])
    _OHLCV_ROWS_CACHE[cache_key] = rows
    return rows


def _ohlcv_stems(symbol: str) -> list[str]:
    raw = str(symbol or "").strip()
    upper = raw.upper()
    stems = [raw, upper]
    if upper == "US30":
        stems.extend(["US30_cash", "US30_CASH"])
    if upper == "US30_CASH":
        stems.extend(["US30_cash", "US30"])
    if "_" in raw:
        prefix, suffix = raw.split("_", 1)
        stems.append(f"{prefix.upper()}_{suffix.lower()}")
    deduped: list[str] = []
    for stem in stems:
        if stem and stem not in deduped:
            deduped.append(stem)
    return deduped


def _synthetic_missing(reason: str) -> dict[str, Any]:
    return {
        "candidate__synthetic_outcome": "INVALID",
        "candidate__synthetic_realized_r": None,
        "candidate__synthetic_bars_in_trade": 0,
        "candidate__synthetic_exit_time": None,
        "candidate__synthetic_skip_reason": reason,
        "candidate__synthetic_max_hold_bars": None,
        "candidate__synthetic_ohlcv_dir": None,
        "candidate__synthetic_ohlcv_dirs_tried": [],
    }


def _trade_record_outcome(record: Mapping[str, Any], path: Path) -> TradeRecordOutcome:
    meta = record.get("metadata", {}) if isinstance(record.get("metadata"), Mapping) else {}
    pipeline = (
        record.get("decision_pipeline", {})
        if isinstance(record.get("decision_pipeline"), Mapping)
        else {}
    )
    level2 = (
        pipeline.get("level2_verification", {})
        if isinstance(pipeline.get("level2_verification"), Mapping)
        else {}
    )
    gate1 = pipeline.get("gate1_result")
    gate3 = pipeline.get("gate3_result")
    return TradeRecordOutcome(
        path=str(path),
        trade_id=meta.get("trade_id") if isinstance(meta.get("trade_id"), str) else None,
        final_outcome=(
            pipeline.get("final_outcome")
            if isinstance(pipeline.get("final_outcome"), str)
            else None
        ),
        realized_r=_extract_realized_r(record),
        level2_passed=(
            bool(level2.get("passed")) if "passed" in level2 else None
        ),
        level2_blocked_by=level2.get("blocked_by"),
        gate1_status=_status_or_raw(gate1),
        gate3_status=_status_or_raw(gate3),
    )


def _extract_realized_r(record: Mapping[str, Any]) -> float | None:
    candidates: list[Any] = []
    pipeline = (
        record.get("decision_pipeline", {})
        if isinstance(record.get("decision_pipeline"), Mapping)
        else {}
    )
    outcome = pipeline.get("outcome") if isinstance(pipeline.get("outcome"), Mapping) else {}
    candidates.extend(
        [
            outcome.get("r_multiple") if isinstance(outcome, Mapping) else None,
            outcome.get("realized_r") if isinstance(outcome, Mapping) else None,
            outcome.get("realized_R") if isinstance(outcome, Mapping) else None,
            record.get("r_multiple"),
            record.get("realized_r"),
            record.get("realized_R"),
        ]
    )
    exit_block = record.get("exit") if isinstance(record.get("exit"), Mapping) else {}
    execution = record.get("execution") if isinstance(record.get("execution"), Mapping) else {}
    candidates.extend(
        [
            exit_block.get("r_multiple") if isinstance(exit_block, Mapping) else None,
            exit_block.get("realized_r") if isinstance(exit_block, Mapping) else None,
            exit_block.get("realized_R") if isinstance(exit_block, Mapping) else None,
            execution.get("r_multiple") if isinstance(execution, Mapping) else None,
            execution.get("realized_r") if isinstance(execution, Mapping) else None,
            execution.get("realized_R") if isinstance(execution, Mapping) else None,
        ]
    )
    for value in candidates:
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _status_or_raw(value: Any) -> Any:
    if isinstance(value, Mapping):
        for key in ("status", "result", "decision"):
            if key in value:
                return value[key]
    return value


def _realized_r_missing_reason(outcome: TradeRecordOutcome | None) -> str | None:
    if outcome is None:
        return "trade_record_not_found"
    if outcome.realized_r is not None:
        return None
    if outcome.final_outcome:
        return f"trade_record_no_realized_r:{safe_slug(outcome.final_outcome)}"
    return "trade_record_no_realized_r"


def _validation_symbol_aliases(row: Mapping[str, Any]) -> set[str]:
    aliases = {
        str(value).upper()
        for value in (row.get("file_symbol"), row.get("symbol"))
        if value not in (None, "")
    }
    if "US30_CASH" in aliases:
        aliases.add("US30")
    return aliases


def _peek_validation_symbol(path: Path) -> str | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                symbol = row.get("file_symbol") or row.get("symbol")
                return str(symbol).upper() if symbol else None
    except Exception:
        return None
    return None


def _candidate_needed_keys(
    rows: Iterable[Mapping[str, Any]],
    *,
    decisions: Iterable[str],
    timeframe: str,
) -> set[tuple[str, str]]:
    allowed = {decision.upper() for decision in decisions}
    keys: set[tuple[str, str]] = set()
    for row in rows:
        decision = str(row.get("decision") or row.get("ai_decision") or "").upper()
        if allowed and decision not in allowed:
            continue
        symbol = str(row.get("symbol") or "").upper()
        timestamp = row.get("timestamp_utc")
        candle_source = row.get("candle_close_utc") or timestamp
        if not symbol or not candle_source:
            continue
        try:
            candle_close = normalize_candidate_candle_close(
                str(candle_source),
                timeframe=timeframe,
                require_aligned=True,
            )
        except (TypeError, ValueError):
            continue
        if candle_close is None:
            continue
        keys.add((symbol, candle_close.isoformat()))
    return keys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external).",
    )
    parser.add_argument("--bundle-id", default=DEFAULT_BUNDLE_ID)
    parser.add_argument(
        "--candidate-path",
        default=str(DEFAULT_CANDIDATE_PATH),
        help="Candidate feature JSONL path.",
    )
    parser.add_argument(
        "--trade-records",
        default=str(DEFAULT_TRADE_RECORDS_ROOT),
        help="Trade records directory.",
    )
    parser.add_argument(
        "--validation",
        action="append",
        help="Validation JSONL path; repeatable. Default uses latest per symbol.",
    )
    parser.add_argument(
        "--validation-label-contains",
        action="append",
        default=None,
        help=(
            "Label substring for auto-discovered validation JSONL files; "
            "repeat to join multiple validation windows."
        ),
    )
    parser.add_argument("--timeframe", default="M15", choices=sorted(TIMEFRAME_MINUTES))
    parser.add_argument(
        "--decision",
        action="append",
        default=None,
        help="Candidate decision to keep; repeatable. Default: CANDIDATE.",
    )
    parser.add_argument(
        "--label",
        default="phase3_candidate_calendar_macro_join_v1",
        help="Output label used with --write.",
    )
    parser.add_argument(
        "--simulate-opportunity",
        action="store_true",
        help="Resolve candidate entry/SL/TP against future M15 OHLCV.",
    )
    parser.add_argument(
        "--ohlcv-dir",
        action="append",
        default=None,
        help=(
            "Directory containing SYMBOL_<timeframe>.csv files for opportunity simulation; "
            "repeat to provide fallback roots."
        ),
    )
    parser.add_argument(
        "--max-hold-bars",
        type=int,
        default=DEFAULT_MAX_HOLD_BARS,
        help="Maximum M15 bars for pending fill plus outcome walk.",
    )
    parser.add_argument("--write", action="store_true", help="Write joined JSONL artifacts.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    decisions = tuple(args.decision or DEFAULT_DECISIONS)
    candidates = load_candidate_rows(args.candidate_path)
    needed_keys = _candidate_needed_keys(candidates, decisions=decisions, timeframe=args.timeframe)
    if args.validation:
        validation_paths = [Path(path) for path in args.validation]
    else:
        validation_paths = []
        label_filters = args.validation_label_contains or [
            "phase3_m15_calendar_macro_validation_v3"
        ]
        for label_filter in label_filters:
            validation_paths.extend(
                find_latest_validation_paths(
                    root,
                    bundle_id=args.bundle_id,
                    label_contains=label_filter,
                )
            )
        validation_paths = sorted(set(validation_paths), key=str)
    if not validation_paths:
        raise FileNotFoundError("no validation JSONL files found")
    validation_index = load_validation_index(validation_paths, needed_keys=needed_keys)
    trade_records = load_trade_record_index(args.trade_records, timeframe=args.timeframe)
    rows, summary = build_candidate_validation_rows(
        candidate_rows=candidates,
        validation_index=validation_index,
        trade_record_index=trade_records,
        decisions=decisions,
        timeframe=args.timeframe,
        simulate_opportunity=args.simulate_opportunity,
        ohlcv_dirs=args.ohlcv_dir or ["data/historical_2026"],
        max_hold_bars=args.max_hold_bars,
    )
    summary = dict(summary)
    summary.update(
        {
            "bundle_id": args.bundle_id,
            "candidate_path": str(args.candidate_path),
            "trade_records": str(args.trade_records),
            "validation_paths": [str(path) for path in validation_paths],
            "validation_index_rows": len(validation_index),
            "simulate_opportunity": bool(args.simulate_opportunity),
            "ohlcv_dirs": [str(path) for path in (args.ohlcv_dir or ["data/historical_2026"])],
            "max_hold_bars": int(args.max_hold_bars),
        }
    )
    if args.write:
        summary = write_candidate_join_artifacts(
            root=root,
            bundle_id=args.bundle_id,
            label=args.label,
            rows=rows,
            summary=summary,
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
