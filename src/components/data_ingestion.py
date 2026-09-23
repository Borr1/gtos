"""Component 1 — Live Data Ingestion from MT5.

Pulls OHLCV candles across all timeframes, computes session levels,
and packages data for Component 2 (Market State Analyzer).

The output dict must match the format produced by
scripts/historical_data_loader.build_raw_data() so that
compute_market_state() receives identical input in live and backtest modes.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from src.mt5.mt5_interface import MT5Interface
from src.research_infra.wave21_full_flow_truth import (
    wave21_full_flow_truth_mode_enabled,
)
from src.research_infra.completed_bar_witness import (
    CompletedBarWitnessError,
    ROW_WITNESS_FIELD,
    validate_completed_bar_witness,
)

# Tick-feature merge (additive, fail-open).
try:
    from src.components.tick_features import (
        TICKS_ROOT as _TICKS_ROOT,
        _read_ticks_for_bar as _tick_read_ticks_for_bar,
        compute_for_bar as _tick_compute_for_bar,
    )
except ImportError:  # pyarrow / pandas missing or module not deployed yet
    _tick_compute_for_bar = None
    _tick_read_ticks_for_bar = None
    _TICKS_ROOT = None

# MT5 timeframe constants — H1+ use special encoded values, NOT minute counts
try:
    import MetaTrader5 as _mt5
    TF_M1 = _mt5.TIMEFRAME_M1     # 1
    TF_M5 = _mt5.TIMEFRAME_M5     # 5
    TF_M15 = _mt5.TIMEFRAME_M15   # 15
    TF_H1 = _mt5.TIMEFRAME_H1     # 16385
    TF_H4 = _mt5.TIMEFRAME_H4     # 16388
    TF_D1 = _mt5.TIMEFRAME_D1     # 16408
except (ImportError, AttributeError):
    # Fallback for macOS/testing where MetaTrader5 isn't available -- or where
    # a partial stub is installed in sys.modules. AttributeError was NOT caught
    # before, so any test harness that stubbed MetaTrader5 without the
    # timeframe constants made this module unimportable for the rest of the
    # session, and the failure surfaced in whichever suite ran next.
    TF_M1 = 1
    TF_M5 = 5
    TF_M15 = 15
    TF_H1 = 16385
    TF_H4 = 16388
    TF_D1 = 16408

TIMEFRAMES = ("D1", "H4", "H1", "M15")
TF_MAP = {"D1": TF_D1, "H4": TF_H4, "H1": TF_H1, "M15": TF_M15}
TF_MINUTES = {"D1": 1440, "H4": 240, "H1": 60, "M15": 15, "M5": 5, "M1": 1}

DEFAULT_LOOKBACKS = {"D1": 30, "H4": 80, "H1": 168, "M15": 672}
DEFAULT_MAX_INTERBAR_PRICE_JUMP_RATIO = 0.35

# Session boundaries (UTC)
ASIAN_START = time(0, 0)
ASIAN_END = time(7, 0)
LONDON_SESSION_START = time(7, 0)
LONDON_SESSION_END = time(13, 0)
_CHALLENGE_NS = "operator"


class DataIncompleteError(Exception):
    pass


class SourceTimebaseError(DataIncompleteError):
    """A truth-mode decision or source timestamp is not explicit aware UTC."""

    terminal_status = "NOT_EVALUABLE_SOURCE_TIMEBASE"


class SourceChronologyError(DataIncompleteError):
    """A truth-mode source row violates the causal completion boundary."""

    terminal_status = "NOT_EVALUABLE_SOURCE_CHRONOLOGY"


def _namespace_of(config: dict | None, namespace: str | None = None) -> str:
    if namespace:
        return str(namespace)
    if not isinstance(config, dict):
        return ""
    runtime = config.get("runtime")
    if isinstance(runtime, dict) and runtime.get("broker_account_namespace"):
        return str(runtime["broker_account_namespace"])
    for key in ("namespace", "book_namespace"):
        if config.get(key):
            return str(config[key])
    return ""


def _is_challenge(namespace: str | None) -> bool:
    return str(namespace or "") == _CHALLENGE_NS


def _ask(question: str, spot_id: str, facts: dict) -> str | None:
    try:
        from src.judgment.pipeline_choices import spot

        return spot(question, spot=spot_id, facts=facts)
    except Exception:
        return None


def _series_continues(
    question: str,
    short_side: str,
    *,
    namespace: str | None,
    spot_id: str,
    facts: dict,
    short: bool,
) -> bool:
    """The short side refuses the pull only when it is the unique highest.

    A pull that is not short continues. An empty answer does not refuse.
    """

    if not short:
        return True
    if not _is_challenge(namespace):
        return False
    return _ask(question, spot_id, facts) != short_side


def ingest_live_data(
    mt5: MT5Interface,
    config: dict,
    *,
    now_utc: datetime | None = None,
    namespace: str | None = None,
) -> dict:
    """Pull current market data from MT5 and package for compute_market_state().

    Returns dict in the same format as historical_data_loader.build_raw_data().
    """
    data_cfg = config.get("data", {})
    lookbacks = data_cfg.get("lookback", DEFAULT_LOOKBACKS)
    equal_level_tolerance = config.get("model_a", {}).get("equal_level_tolerance", 2.50)

    # Use mt5_symbol for broker API calls (e.g., US30.cash vs US30_cash).
    # canonical_symbol is the GTOS instrument identifier (e.g., US30_cash) —
    # stored in raw_data["symbol"] for downstream consumers that need a
    # normalized, broker-agnostic label (shadow divergence logger, XAUUSD
    # session-ATR gate in market_state.compute_market_state, etc.).
    canonical_symbol = config.get("market", {}).get("symbol", "XAUUSD")
    mt5_symbol = config.get("market", {}).get("mt5_symbol", canonical_symbol)

    truth_mode = wave21_full_flow_truth_mode_enabled(config)
    ns = _namespace_of(config, namespace)
    now_utc = now_utc or datetime.now(timezone.utc)
    if truth_mode and (now_utc.tzinfo is None or now_utc.utcoffset() is None):
        raise SourceTimebaseError("decision_time_utc_naive")
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    # Pull candles for each timeframe. MT5 commonly includes the current
    # forming bar; production market state and broader-origin candidates must
    # be built from closed bars only.
    candles: dict[str, list[dict]] = {}
    closed_bar_filter: dict[str, dict[str, object]] = {}
    for tf_name, tf_const in TF_MAP.items():
        count = lookbacks.get(tf_name, 100)
        raw = mt5.get_candles(mt5_symbol, tf_const, count)
        if not raw:
            raise DataIncompleteError(
                f"Insufficient {tf_name} candles: got 0, need {count}"
            )
        raw_short = len(raw) < int(count * 0.9)
        if not truth_mode and not _series_continues(
            "raw_series",
            "series_short",
            namespace=ns,
            spot_id=f"{canonical_symbol}|{tf_name}|{len(raw)}|{count}",
            facts={
                "symbol": canonical_symbol,
                "timeframe": tf_name,
                "got": len(raw),
                "need": count,
                "namespace": ns,
            },
            short=raw_short,
        ):
            raise DataIncompleteError(
                f"Insufficient {tf_name} candles: got {len(raw)}, need {count}"
            )
        if truth_mode and raw_short:
            raise DataIncompleteError(
                f"Insufficient {tf_name} candles: got {len(raw)}, need {count}"
            )
        closed = filter_closed_candles(
            raw,
            tf_name,
            now_utc=now_utc,
            require_aware_utc=truth_mode,
            future_tolerance_seconds=0.0 if truth_mode else 2.0,
            reject_future_rows=truth_mode,
            require_completion_witness=truth_mode,
            namespace=None if truth_mode else ns,
        )
        closed_short = len(closed) < int(count * 0.9)
        if not truth_mode and not _series_continues(
            "closed_series",
            "closed_series_short",
            namespace=ns,
            spot_id=f"{canonical_symbol}|{tf_name}|closed|{len(closed)}|{count}",
            facts={
                "symbol": canonical_symbol,
                "timeframe": tf_name,
                "got": len(closed),
                "need": count,
                "namespace": ns,
            },
            short=closed_short,
        ):
            raise DataIncompleteError(
                f"Insufficient closed {tf_name} candles: got {len(closed)}, need {count}"
            )
        if truth_mode and closed_short:
            raise DataIncompleteError(
                f"Insufficient closed {tf_name} candles: got {len(closed)}, need {count}"
            )
        run_quote_lane = tf_name == "M15"
        if not truth_mode and _is_challenge(ns):
            # The timeframe name is a fact. The tick lane opens only when
            # that side is the unique highest.
            run_quote_lane = _ask(
                "repair_lane",
                f"{canonical_symbol}|{tf_name}",
                {"symbol": canonical_symbol, "timeframe": tf_name, "namespace": ns},
            ) == "quote_repair_lane"
        if run_quote_lane:
            closed, repair_report = repair_malformed_ohlc_from_ticks(
                closed,
                canonical_symbol,
                tf_name,
                config,
                namespace=ns,
            )
        else:
            repair_report = {"enabled": False, "reason": "candle_lane"}
        candles[tf_name] = closed
        closed_bar_filter[tf_name] = {
            "input_count": len(raw),
            "closed_count": len(closed),
            "removed_unclosed_count": len(raw) - len(closed),
            "latest_input_time": _candle_time_text(raw[-1]) if raw else None,
            "latest_closed_time": _candle_time_text(closed[-1]) if closed else None,
            "ohlc_repair": repair_report,
            **(
                {
                    "truth_mode_aware_utc_required": True,
                    "future_tolerance_seconds": 0.0,
                }
                if truth_mode
                else {}
            ),
        }

    target = now_utc.date()
    candle_timestamp = infer_latest_closed_m15_timestamp(
        candles["M15"], now_utc=now_utc, namespace=None if truth_mode else ns,
    )

    # Compute session levels from M15 candles
    session_levels = compute_session_levels(
        candles["M15"], target, namespace=None if truth_mode else ns,
    )

    # Update session H/L and London H/L from current session M15 candles
    _update_session_highs_lows(
        candles["M15"], target, now_utc, session_levels,
        namespace=None if truth_mode else ns,
    )

    # Get current spread
    tick = mt5.get_tick(mt5_symbol)
    spread_cents = tick.spread_cents if tick else None

    # Equal levels (matches historical_data_loader.build_raw_data)
    h4_candles = candles.get("H4", [])
    h1_candles = candles.get("H1", [])

    raw_data = {
        "symbol": canonical_symbol,
        "timestamp_utc": now_utc.isoformat(),
        **candle_timestamp,
        "candles": candles,
        "session_levels": session_levels,
        "equal_highs_H4": detect_equal_levels(h4_candles, "high", equal_level_tolerance),
        "equal_lows_H4": detect_equal_levels(h4_candles, "low", equal_level_tolerance),
        "equal_highs_H1": detect_equal_levels(h1_candles, "high", equal_level_tolerance),
        "equal_lows_H1": detect_equal_levels(h1_candles, "low", equal_level_tolerance),
        "spread_cents": spread_cents,
        "high_impact_events": [],
        "data_quality": {
            "all_timeframes_complete": all(
                len(candles.get(tf, [])) >= int(lookbacks.get(tf, 100) * 0.9)
                for tf in TIMEFRAMES
            ),
            "closed_bar_filter": closed_bar_filter,
            "spread_normal": spread_cents is not None and spread_cents <= config.get("risk", {}).get("max_spread_cents", 100),
            "mt5_connected": True,
            "timestamp_utc": now_utc.isoformat(),
            **candle_timestamp,
        },
    }

    # Tick-feature merge (additive — `tick_features` defaults to None and
    # never breaks the pipeline). Reads the latest M15 bar's tick parquet,
    # computes microstructure features, writes a sidecar JSON, attaches the
    # in-memory dict to raw_data. If anything fails (pyarrow missing, daemon
    # not running, parquet corrupt), we log a warning and proceed with None.
    raw_data["tick_features"] = _maybe_attach_tick_features(
        canonical_symbol, candles.get("M15", []), config
    )

    return raw_data


def filter_closed_candles(
    candles: list[dict],
    timeframe: str,
    *,
    now_utc: datetime | None = None,
    require_aware_utc: bool = False,
    future_tolerance_seconds: float = 2.0,
    reject_future_rows: bool = False,
    require_completion_witness: bool = False,
    namespace: str | None = None,
) -> list[dict]:
    """Return only bars whose timeframe close is not in the future.

    The live MT5 rate buffer can expose the in-progress bar immediately after
    a close. That bar is not valid production market-state evidence.
    """

    if not candles:
        return []
    minutes = TF_MINUTES.get(str(timeframe).upper())
    if not minutes:
        return list(candles)
    now = now_utc or datetime.now(timezone.utc)
    if require_aware_utc and (now.tzinfo is None or now.utcoffset() is None):
        raise SourceTimebaseError("decision_time_utc_naive")
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    closed: list[dict] = []
    tail: list[dict] = []
    close_delta = timedelta(minutes=minutes)
    tolerance = timedelta(seconds=max(0.0, float(future_tolerance_seconds)))
    for ordinal, candle in enumerate(candles):
        bar_open = _parse_candle_time_utc(
            candle.get("time"),
            require_aware_utc=require_aware_utc,
            field=f"{timeframe}_row_{ordinal}_time",
        )
        if bar_open is None:
            if require_aware_utc:
                raise SourceTimebaseError(
                    f"{timeframe}_row_{ordinal}_time_missing_or_invalid"
                )
            continue
        if require_completion_witness:
            _validate_completed_bar_witness(
                candle,
                timeframe=timeframe,
                bar_open=bar_open,
                decision_time=now,
                ordinal=ordinal,
            )
            closed.append(candle)
            continue
        close_time = bar_open + close_delta
        if close_time <= now + tolerance:
            closed.append(candle)
        elif reject_future_rows:
            raise SourceChronologyError(
                f"{timeframe}_row_{ordinal}_close_after_decision:"
                f"{close_time.isoformat()}>{now.isoformat()}"
            )
        else:
            tail.append(candle)
    if tail and _is_challenge(namespace) and not require_completion_witness and not reject_future_rows:
        # The close-versus-clock comparison is a fact. The tail stays out
        # only when that side is the unique highest.
        winner = _ask(
            "unclosed_tail",
            f"{timeframe}|{now.isoformat()}|{len(candles)}|{len(tail)}",
            {
                "timeframe": timeframe,
                "input_count": len(candles),
                "closed_count": len(closed),
                "unclosed_count": len(tail),
                "namespace": namespace,
            },
        )
        if winner != "unclosed_stays_out":
            return closed + tail
    return closed


def _validate_completed_bar_witness(
    candle: dict,
    *,
    timeframe: str,
    bar_open: datetime,
    decision_time: datetime,
    ordinal: int,
) -> None:
    witness = candle.get(ROW_WITNESS_FIELD)
    try:
        validate_completed_bar_witness(
            witness,
            timeframe=timeframe,
            row_open=bar_open,
            asof=decision_time,
        )
    except CompletedBarWitnessError as exc:
        detail = str(exc)
        timebase = any(
            token in detail
            for token in (
                "_naive",
                "_open_invalid",
                "_open_missing_or_unsupported",
                "asof_invalid",
                "asof_missing_or_unsupported",
            )
        )
        if witness is None:
            detail = "completion_witness_missing"
        elif detail == "completion_witness_contract_invalid":
            detail = "completion_witness_adjacency_invalid"
        error = SourceTimebaseError if timebase else SourceChronologyError
        raise error(f"{timeframe}_row_{ordinal}_{detail}") from exc


def _parse_candle_time_utc(
    value: object,
    *,
    require_aware_utc: bool = False,
    field: str = "candle_time",
) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif value is None:
        return None
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if require_aware_utc and (dt.tzinfo is None or dt.utcoffset() is None):
        raise SourceTimebaseError(f"{field}_naive")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _candle_time_text(candle: dict) -> object:
    value = candle.get("time") if isinstance(candle, dict) else None
    return value.isoformat() if isinstance(value, datetime) else value


def repair_malformed_m15_ohlc_from_ticks(
    candles: list[dict],
    symbol: str,
    config: dict | None = None,
) -> tuple[list[dict], dict[str, object]]:
    return repair_malformed_ohlc_from_ticks(candles, symbol, "M15", config)


def repair_malformed_ohlc_from_ticks(
    candles: list[dict],
    symbol: str,
    timeframe: str,
    config: dict | None = None,
    *,
    anchor_price: float | None = None,
    namespace: str | None = None,
) -> tuple[list[dict], dict[str, object]]:
    """Repair malformed closed OHLC candles from local tick parquet evidence.

    This is intentionally narrow: only bars that fail OHLC ordering, a recent
    interbar price-scale sanity check, or an optional current-tick anchor check
    are candidates for repair.
    """

    tf_name = str(timeframe or "").upper()
    report: dict[str, object] = {
        "enabled": True,
        "source": "local_tick_parquet",
        "timeframe": tf_name,
        "repaired_count": 0,
        "failed_count": 0,
        "events": [],
    }
    if not candles:
        return [], report
    if _tick_read_ticks_for_bar is None or _TICKS_ROOT is None:
        report["enabled"] = False
        report["reason"] = "tick_parquet_reader_unavailable"
        return list(candles), report

    max_jump_ratio = _max_interbar_price_jump_ratio(config)
    anchor = _float_or_none(anchor_price)
    repaired: list[dict] = []
    previous_close: float | None = None
    for candle in candles:
        current = dict(candle)
        reason = _ohlc_malformed_reason(
            current,
            previous_close=previous_close,
            max_jump_ratio=max_jump_ratio,
            anchor_price=anchor,
            timeframe=tf_name,
        )
        if reason is not None:
            tick_repair = _reconstruct_ohlc_candle_from_ticks(symbol, current, tf_name)
            use_quote = tick_repair is not None
            if use_quote and _is_challenge(namespace):
                # A reconstructed quote is a fact. It replaces the print only
                # when that side is the unique highest.
                use_quote = _ask(
                    "tick_quote",
                    f"{symbol}|{tf_name}|{current.get('time')}|{reason}",
                    {
                        "symbol": symbol,
                        "timeframe": tf_name,
                        "time": str(current.get("time")),
                        "reason": reason,
                        "tick_rows": tick_repair["tick_rows"],
                        "namespace": namespace,
                    },
                ) == "tick_quote_reaches"
            if use_quote and tick_repair is not None:
                original = {
                    "open": _json_safe_scalar(current.get("open")),
                    "high": _json_safe_scalar(current.get("high")),
                    "low": _json_safe_scalar(current.get("low")),
                    "close": _json_safe_scalar(current.get("close")),
                    "volume": _json_safe_scalar(current.get("volume")),
                }
                current.update(tick_repair["candle"])
                current["ohlc_source_repair"] = {
                    "status": "repaired_from_local_tick_parquet",
                    "reason": reason,
                    "original": original,
                    "tick_rows": tick_repair["tick_rows"],
                    "source": tick_repair["source"],
                }
                report["repaired_count"] = int(report["repaired_count"]) + 1
                report["events"].append(
                    {
                        "time": current.get("time"),
                        "status": "repaired",
                        "reason": reason,
                        "tick_rows": tick_repair["tick_rows"],
                        "original": original,
                        "repaired": tick_repair["candle"],
                    }
                )
            elif tick_repair is None:
                current["ohlc_source_repair"] = {
                    "status": "repair_failed_local_tick_parquet_unavailable_or_empty",
                    "reason": reason,
                    "source": "local_tick_parquet_unavailable_or_empty",
                }
                report["failed_count"] = int(report["failed_count"]) + 1
                report["events"].append(
                    {
                        "time": current.get("time"),
                        "status": "repair_failed",
                        "reason": reason,
                        "source": "local_tick_parquet_unavailable_or_empty",
                    }
                )
        repair_status = (
            (current.get("ohlc_source_repair") or {}).get("status")
            if isinstance(current.get("ohlc_source_repair"), dict)
            else None
        )
        close = _float_or_none(current.get("close"))
        if close is not None and not str(repair_status or "").startswith("repair_failed"):
            previous_close = close
        repaired.append(current)
    return repaired, report


def _reconstruct_m15_candle_from_ticks(symbol: str, candle: dict) -> dict[str, object] | None:
    return _reconstruct_ohlc_candle_from_ticks(symbol, candle, "M15")


def _reconstruct_ohlc_candle_from_ticks(
    symbol: str,
    candle: dict,
    timeframe: str,
) -> dict[str, object] | None:
    bar_open = _parse_candle_time_utc(candle.get("time"))
    if bar_open is None:
        return None
    minutes = TF_MINUTES.get(str(timeframe or "").upper())
    if not minutes:
        return None
    bar_close = bar_open + timedelta(minutes=minutes)
    try:
        ticks = _tick_read_ticks_for_bar(symbol, bar_open, bar_close, ticks_root=_TICKS_ROOT)
    except Exception as exc:  # noqa: BLE001
        logger.warning("tick OHLC repair failed reading %s @ %s: %s", symbol, bar_open.isoformat(), exc)
        return None
    if ticks is None or getattr(ticks, "empty", True):
        return None
    if "bid" not in ticks.columns:
        return None
    bid = ticks["bid"].dropna()
    bid = bid[bid > 0]
    if bid.empty:
        return None
    return {
        "source": f"{_TICKS_ROOT}/{symbol}/{bar_open.date().isoformat()}.parquet",
        "tick_rows": int(len(bid)),
        "candle": {
            "open": float(bid.iloc[0]),
            "high": float(bid.max()),
            "low": float(bid.min()),
            "close": float(bid.iloc[-1]),
            "volume": int(len(bid)),
        },
    }


def _json_safe_scalar(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _json_safe_scalar(item())
        except Exception:  # noqa: BLE001
            pass
    return str(value)


def _m15_ohlc_malformed_reason(
    candle: dict,
    *,
    previous_close: float | None,
    max_jump_ratio: float,
) -> str | None:
    return _ohlc_malformed_reason(
        candle,
        previous_close=previous_close,
        max_jump_ratio=max_jump_ratio,
        timeframe="M15",
    )


def _ohlc_malformed_reason(
    candle: dict,
    *,
    previous_close: float | None,
    max_jump_ratio: float,
    anchor_price: float | None = None,
    timeframe: str = "M15",
) -> str | None:
    prefix = str(timeframe or "M15").lower()
    open_ = _float_or_none(candle.get("open"))
    high = _float_or_none(candle.get("high"))
    low = _float_or_none(candle.get("low"))
    close = _float_or_none(candle.get("close"))
    if None in (open_, high, low, close):
        return f"{prefix}_ohlc_missing_or_non_numeric"
    values = (open_, high, low, close)
    if any(value <= 0 for value in values):
        return f"{prefix}_ohlc_non_positive_price"
    if high < low:
        return f"{prefix}_high_below_low"
    if low > min(open_, close):
        return f"{prefix}_low_above_open_or_close"
    if high < max(open_, close):
        return f"{prefix}_high_below_open_or_close"
    if previous_close and previous_close > 0:
        jump_ratio = max(abs(value - previous_close) / abs(previous_close) for value in values)
        if jump_ratio > max_jump_ratio:
            return f"{prefix}_interbar_price_jump_exceeds_threshold"
    if anchor_price and anchor_price > 0:
        anchor_jump_ratio = max(abs(value - anchor_price) / abs(anchor_price) for value in values)
        if anchor_jump_ratio > max_jump_ratio:
            return f"{prefix}_anchor_price_jump_exceeds_threshold"
    return None


def _max_interbar_price_jump_ratio(config: dict | None) -> float:
    runtime = config.get("gtos_vnext_runtime") if isinstance(config, dict) else {}
    if not isinstance(runtime, dict):
        return DEFAULT_MAX_INTERBAR_PRICE_JUMP_RATIO
    value = _float_or_none(runtime.get("moonshot_broader_origin_max_interbar_price_jump_ratio"))
    if value is None or value <= 0:
        return DEFAULT_MAX_INTERBAR_PRICE_JUMP_RATIO
    return value


def _float_or_none(value: object) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def infer_latest_closed_m15_timestamp(
    m15_candles: list[dict],
    *,
    now_utc: datetime | None = None,
    namespace: str | None = None,
) -> dict[str, object]:
    """Return canonical latest-closed M15 candle timestamps.

    MT5 commonly includes the new in-progress bar at position ``[-1]`` shortly
    after a candle close. The live wall-clock timestamp can also drift if
    Windows wakes late. For shadow validation, use the most recent M15 bar whose
    close is not in the future relative to ``now_utc`` instead of the wall clock.
    """

    if not m15_candles:
        return {
            "candle_open_utc": None,
            "candle_close_utc": None,
            "candle_timestamp_source": "m15_unavailable",
            "candle_close_lag_seconds": None,
        }
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    selected: tuple[datetime, datetime] | None = None
    for candle in reversed(m15_candles):
        raw_time = candle.get("time")
        if not raw_time:
            continue
        try:
            bar_open = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
        except ValueError:
            continue
        if bar_open.tzinfo is None:
            bar_open = bar_open.replace(tzinfo=timezone.utc)
        else:
            bar_open = bar_open.astimezone(timezone.utc)
        bar_close = bar_open + timedelta(minutes=15)
        if bar_close <= now + timedelta(seconds=2):
            selected = (bar_open, bar_close)
            break

    if selected is None:
        return {
            "candle_open_utc": None,
            "candle_close_utc": None,
            "candle_timestamp_source": "no_closed_m15_bar",
            "candle_close_lag_seconds": None,
        }

    bar_open, bar_close = selected
    if _is_challenge(namespace):
        # The measured close is a fact. It becomes the decision timestamp
        # only when that side is the unique highest.
        winner = _ask(
            "decision_m15",
            f"{bar_open.isoformat()}|{bar_close.isoformat()}",
            {
                "bar_open": bar_open.isoformat(),
                "bar_close": bar_close.isoformat(),
                "lag_seconds": (now - bar_close).total_seconds(),
                "namespace": namespace,
            },
        )
        if winner != "this_m15_is_the_close":
            return {
                "candle_open_utc": None,
                "candle_close_utc": None,
                "candle_timestamp_source": "no_closed_m15_bar",
                "candle_close_lag_seconds": None,
            }
    return {
        "candle_open_utc": bar_open.isoformat(),
        "candle_close_utc": bar_close.isoformat(),
        "candle_timestamp_source": "latest_closed_m15_bar",
        "candle_close_lag_seconds": (now - bar_close).total_seconds(),
    }


def _maybe_attach_tick_features(
    symbol: str,
    m15_candles: list[dict],
    config: dict,
) -> Optional[dict]:
    """Compute and attach tick-microstructure features for the just-closed M15 bar.

    Fail-open by design: returns ``None`` when:
      - The tick-features extractor module isn't importable (pyarrow missing).
      - The feature is disabled via ``config.tick_features.enabled = false``.
      - No tick parquet data exists for the bar (daemon not running yet).
      - Any unexpected exception surfaces inside the extractor.

    A warning log is emitted on failure paths so operators can spot a missing
    daemon, but the orchestrator pipeline continues unmodified.
    """
    # Honor explicit opt-out via config (default ENABLED).
    cfg = (config.get("tick_features") or {}) if isinstance(config, dict) else {}
    if not cfg.get("enabled", True):
        return None

    if _tick_compute_for_bar is None:
        # Module unimportable (e.g., pyarrow not installed). One-shot warn.
        logger.warning("tick_features module unavailable — tick_features=None")
        return None

    if not m15_candles:
        return None

    try:
        # ingest_live_data filters out the MT5 forming bar before this helper
        # is called, so [-1] is the just-closed M15 bar.
        latest = m15_candles[-1]
        candle_time_str = latest.get("time")
        if not candle_time_str:
            return None
        # The candle "time" field is the bar OPEN; the close is open + 15 min.
        # We hand the close time to compute_for_bar (its convention).
        bar_open_dt = datetime.fromisoformat(str(candle_time_str).replace("Z", "+00:00"))
        if bar_open_dt.tzinfo is None:
            bar_open_dt = bar_open_dt.replace(tzinfo=timezone.utc)
        bar_close_dt = bar_open_dt + timedelta(minutes=15)
        record = _tick_compute_for_bar(symbol, bar_close_dt, write_to_sidecar=True)
        if record is None:
            logger.warning("tick_features: no parquet data for %s @ %s",
                            symbol, bar_close_dt.isoformat())
            return None
        # Return dict-form so consumers don't need the dataclass type.
        return {
            "schema_version": record.schema_version,
            "candle_time_utc": record.candle_time_utc,
            "bar_open_utc": record.bar_open_utc,
            "bar_close_utc": record.bar_close_utc,
            "n_ticks": record.n_ticks,
            "features": record.features,
        }
    except Exception as e:  # noqa: BLE001 — fail-open is the contract
        logger.warning("tick_features extraction failed for %s: %s", symbol, e)
        return None


# ---------------------------------------------------------------------------
# Session level computation — mirrors historical_data_loader.py exactly
# ---------------------------------------------------------------------------

def _level_reaches(
    question: str,
    reach_side: str,
    *,
    namespace: str | None,
    spot_id: str,
    facts: dict,
    bars: list,
) -> bool:
    """Publish this measured window only when its reach side is unique highest.

    An empty window stays unset. An empty answer does not publish it.
    """

    if not bars:
        return False
    if not _is_challenge(namespace):
        return True
    return _ask(question, spot_id, facts) == reach_side


def compute_session_levels(
    m15_candles: list[dict],
    target_date: date,
    *,
    namespace: str | None = None,
) -> dict:
    """Compute Asian session H/L and PDH/PDL for *target_date*.

    Asian session: 00:00-07:00 UTC on *target_date* (from M15 candles).
    PDH/PDL: high/low of the previous trading day.
    """
    prev_day_candles: list[dict] = []
    asian_candles: list[dict] = []

    prev_date = _previous_weekday(target_date)

    for c in m15_candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        c_date = dt.date()
        c_time = dt.time()

        if c_date == prev_date:
            prev_day_candles.append(c)
        elif c_date == target_date and ASIAN_START <= c_time < ASIAN_END:
            asian_candles.append(c)

    day_key = target_date.isoformat()
    if _level_reaches(
        "asian_bars",
        "asian_bars_reach",
        namespace=namespace,
        spot_id=f"{day_key}|asian|{len(asian_candles)}",
        facts={"day": day_key, "bars": len(asian_candles), "namespace": namespace},
        bars=asian_candles,
    ):
        asian_high = max(c["high"] for c in asian_candles)
        asian_low = min(c["low"] for c in asian_candles)
    else:
        asian_high = 0.0
        asian_low = 0.0

    if _level_reaches(
        "prev_day_bars",
        "prev_day_bars_reach",
        namespace=namespace,
        spot_id=f"{day_key}|prev|{len(prev_day_candles)}",
        facts={"day": day_key, "bars": len(prev_day_candles), "namespace": namespace},
        bars=prev_day_candles,
    ):
        pdh = max(c["high"] for c in prev_day_candles)
        pdl = min(c["low"] for c in prev_day_candles)
    else:
        pdh = 0.0
        pdl = 0.0

    return {
        "asian_high": asian_high,
        "asian_low": asian_low,
        "pdh": pdh,
        "pdl": pdl,
        "session_high": None,
        "session_low": None,
        "london_high": None,
        "london_low": None,
    }


def _update_session_highs_lows(
    m15_candles: list[dict],
    target_date: date,
    now_utc: datetime,
    session_levels: dict,
    *,
    namespace: str | None = None,
) -> None:
    """Update session H/L and London H/L in-place from M15 candles."""
    session_m15 = []
    london_m15 = []

    for c in m15_candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt.date() != target_date:
            continue
        c_time = dt.time()

        # Session window candles (07:00-09:30 or 13:00-15:30 depending on KZ)
        if LONDON_SESSION_START <= c_time:
            session_m15.append(c)
        # London session H/L: 07:00-13:00 UTC
        if LONDON_SESSION_START <= c_time < LONDON_SESSION_END and dt <= now_utc:
            london_m15.append(c)

    day_key = target_date.isoformat()
    if _level_reaches(
        "session_bars",
        "session_bars_reach",
        namespace=namespace,
        spot_id=f"{day_key}|session|{len(session_m15)}",
        facts={"day": day_key, "bars": len(session_m15), "namespace": namespace},
        bars=session_m15,
    ):
        session_levels["session_high"] = max(c["high"] for c in session_m15)
        session_levels["session_low"] = min(c["low"] for c in session_m15)
    if _level_reaches(
        "london_bars",
        "london_bars_reach",
        namespace=namespace,
        spot_id=f"{day_key}|london|{len(london_m15)}",
        facts={"day": day_key, "bars": len(london_m15), "namespace": namespace},
        bars=london_m15,
    ):
        session_levels["london_high"] = max(c["high"] for c in london_m15)
        session_levels["london_low"] = min(c["low"] for c in london_m15)


def _previous_weekday(d: date) -> date:
    """Return the previous weekday (Mon-Fri) before *d*."""
    prev = d - timedelta(days=1)
    while prev.weekday() >= 5:
        prev -= timedelta(days=1)
    return prev


# ---------------------------------------------------------------------------
# Equal levels detection — mirrors historical_data_loader.py exactly
# ---------------------------------------------------------------------------

def detect_equal_levels(
    candles: list[dict],
    side: str,
    tolerance: float = 2.50,
) -> list[dict]:
    """Find equal highs or equal lows within *tolerance* dollars."""
    key = "high" if side == "high" else "low"
    levels: list[dict] = []
    used: set[int] = set()
    if len(candles) < 2:
        return levels

    bucket_width = tolerance if tolerance > 0 else 1.0
    price_buckets: dict[int, list[int]] = defaultdict(list)
    prices: list[float] = []
    for idx, candle in enumerate(candles):
        price = float(candle[key])
        prices.append(price)
        price_buckets[math.floor(price / bucket_width)].append(idx)

    for i in range(len(candles)):
        if i in used:
            continue
        price_i = prices[i]
        center_bucket = math.floor(price_i / bucket_width)
        group = [i]
        candidate_indices: list[int] = []
        if tolerance > 0:
            candidate_bins = range(center_bucket - 1, center_bucket + 2)
        else:
            candidate_bins = (center_bucket,)
        for bucket in candidate_bins:
            candidate_indices.extend(price_buckets.get(bucket, ()))
        for j in sorted(candidate_indices):
            if j <= i:
                continue
            if j in used:
                continue
            if abs(prices[j] - price_i) <= tolerance:
                group.append(j)
        if len(group) >= 2:
            avg_price = sum(prices[k] for k in group) / len(group)
            levels.append({
                "price": round(avg_price, 2),
                "count": len(group),
                "candle_indices": group,
            })
            used.update(group)

    return levels


# ---------------------------------------------------------------------------
# M5 Data Pull (for M5 Entry Refinement)
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


def pull_m5_candles(mt5: MT5Interface, lookback: int = 36,
                    symbol: str = "XAUUSD", *,
                    namespace: str | None = None) -> list[dict] | None:
    """Pull the last *lookback* M5 candles from MT5.

    Called only when a CANDIDATE trade needs M5 refinement — NOT on
    every M15 candle close (minimizes MT5 data overhead).

    Returns a list of dicts with keys: time, open, high, low, close, volume.
    Returns None if data is unavailable or insufficient (<12 candles).
    """
    try:
        candles = mt5.get_candles(symbol, TF_M5, lookback)
    except Exception as e:
        logger.warning("M5 pull from MT5 failed: %s", e)
        return None

    if candles is None:
        logger.warning("M5 pull returned 0 candles (need ≥12).")
        return None
    if len(candles) < 12 and not _series_continues(
        "m5_series",
        "m5_short",
        namespace=namespace,
        spot_id=f"{symbol}|{len(candles)}|{lookback}",
        facts={"symbol": symbol, "got": len(candles), "need": 12, "namespace": namespace},
        short=True,
    ):
        logger.warning("M5 pull returned %d candles (need ≥12).", len(candles))
        return None

    result = []
    for c in candles:
        result.append({
            "time": str(c["time"]) if not isinstance(c["time"], str) else c["time"],
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
            "volume": int(c.get("tick_volume", c.get("volume", 0))),
        })
    return result
