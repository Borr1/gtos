"""Trades-level orderflow feature extraction for research windows.

The features here are descriptive diagnostics for Databento trades windows.
They do not alter live trading behavior and do not define a strategy.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd


TICK_SIZE_BY_SYMBOL = {
    "GC.v.0": 0.1,
    "SI.v.0": 0.005,
    "NQ.v.0": 0.25,
    "ES.v.0": 0.25,
    "YM.v.0": 1.0,
    "6B.v.0": 0.0001,
    "6J.v.0": 0.0000005,
}


def parse_utc(value: str) -> pd.Timestamp:
    return pd.Timestamp(value).tz_convert("UTC") if pd.Timestamp(value).tzinfo else pd.Timestamp(value, tz="UTC")


def tick_size(symbol: str) -> float:
    return TICK_SIZE_BY_SYMBOL.get(symbol, 0.01)


def prepare_trades(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["ts_event", "symbol", "price", "size", "side", "signed_size"])
    required = {"ts_event", "symbol", "price", "size"}
    missing = required - set(trades.columns)
    if missing:
        raise ValueError(f"trades missing columns: {sorted(missing)}")
    df = trades.copy()
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True)
    df["symbol"] = df["symbol"].astype(str)
    df["price"] = df["price"].astype(float)
    df["size"] = df["size"].astype(float)
    if "side" not in df.columns:
        df["side"] = ""
    side = df["side"].astype(str).str.upper()
    df["signed_size"] = 0.0
    df.loc[side == "B", "signed_size"] = df.loc[side == "B", "size"]
    df.loc[side == "A", "signed_size"] = -df.loc[side == "A", "size"]
    return df.sort_values("ts_event")


def slice_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    if df.empty or end <= start:
        return df.iloc[0:0].copy()
    return df[(df["ts_event"] >= start) & (df["ts_event"] < end)].copy()


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _price_change_ticks(df: pd.DataFrame, symbol: str) -> float | None:
    if df.empty:
        return None
    return _safe_float((df["price"].iloc[-1] - df["price"].iloc[0]) / tick_size(symbol))


def _range_ticks(df: pd.DataFrame, symbol: str) -> float | None:
    if df.empty:
        return None
    return _safe_float((df["price"].max() - df["price"].min()) / tick_size(symbol))


def flow_stats(df: pd.DataFrame, symbol: str, prefix: str) -> dict[str, Any]:
    if df.empty:
        return {
            f"{prefix}_trade_count": 0,
            f"{prefix}_volume": 0.0,
            f"{prefix}_buy_volume": 0.0,
            f"{prefix}_sell_volume": 0.0,
            f"{prefix}_signed_volume": 0.0,
            f"{prefix}_buy_fraction": None,
            f"{prefix}_avg_trade_size": None,
            f"{prefix}_price_change_ticks": None,
            f"{prefix}_range_ticks": None,
            f"{prefix}_absorption_volume_per_tick": None,
            f"{prefix}_delta_price_divergence": None,
        }
    buy_volume = float(df.loc[df["signed_size"] > 0, "size"].sum())
    sell_volume = float(df.loc[df["signed_size"] < 0, "size"].sum())
    volume = float(df["size"].sum())
    range_ticks = _range_ticks(df, symbol)
    price_change_ticks = _price_change_ticks(df, symbol)
    signed_volume = float(df["signed_size"].sum())
    divergence = None
    if price_change_ticks is not None:
        divergence = (signed_volume > 0 and price_change_ticks <= 0) or (
            signed_volume < 0 and price_change_ticks >= 0
        )
    return {
        f"{prefix}_trade_count": int(len(df)),
        f"{prefix}_volume": volume,
        f"{prefix}_buy_volume": buy_volume,
        f"{prefix}_sell_volume": sell_volume,
        f"{prefix}_signed_volume": signed_volume,
        f"{prefix}_buy_fraction": _safe_float(buy_volume / volume) if volume > 0 else None,
        f"{prefix}_avg_trade_size": _safe_float(volume / len(df)) if len(df) else None,
        f"{prefix}_price_change_ticks": price_change_ticks,
        f"{prefix}_range_ticks": range_ticks,
        f"{prefix}_absorption_volume_per_tick": _safe_float(volume / max(range_ticks or 0.0, 1.0)),
        f"{prefix}_delta_price_divergence": divergence,
    }


def volume_profile_stats(df: pd.DataFrame, symbol: str, event_price: float | None) -> dict[str, Any]:
    if df.empty or event_price is None:
        return {
            "profile_levels": 0,
            "profile_poc_price": None,
            "profile_poc_volume": None,
            "profile_event_price_bin": None,
            "profile_event_price_volume": None,
            "profile_event_price_volume_percentile": None,
            "profile_nearest_lvn_distance_ticks": None,
            "profile_nearest_hvn_distance_ticks": None,
        }
    ts = tick_size(symbol)
    bins = ((df["price"] / ts).round() * ts).round(10)
    profile = df.assign(price_bin=bins).groupby("price_bin")["size"].sum().sort_index()
    if profile.empty:
        return volume_profile_stats(df.iloc[0:0], symbol, None)
    poc_price = float(profile.idxmax())
    poc_volume = float(profile.max())
    event_bin = float(round(round(event_price / ts) * ts, 10))
    if event_bin in profile.index:
        event_volume = float(profile.loc[event_bin])
        percentile = float((profile <= event_volume).mean())
    else:
        event_volume = 0.0
        percentile = 0.0
    low_threshold = float(profile.quantile(0.2))
    high_threshold = float(profile.quantile(0.8))
    low_levels = profile[profile <= low_threshold].index.astype(float)
    high_levels = profile[profile >= high_threshold].index.astype(float)
    nearest_lvn = None
    nearest_hvn = None
    if len(low_levels):
        nearest_lvn = float(np.min(np.abs(low_levels - event_bin)) / ts)
    if len(high_levels):
        nearest_hvn = float(np.min(np.abs(high_levels - event_bin)) / ts)
    return {
        "profile_levels": int(len(profile)),
        "profile_poc_price": poc_price,
        "profile_poc_volume": poc_volume,
        "profile_event_price_bin": event_bin,
        "profile_event_price_volume": event_volume,
        "profile_event_price_volume_percentile": percentile,
        "profile_nearest_lvn_distance_ticks": nearest_lvn,
        "profile_nearest_hvn_distance_ticks": nearest_hvn,
    }


def range_rejection_stats(pre: pd.DataFrame, event15: pd.DataFrame) -> dict[str, Any]:
    if pre.empty or event15.empty:
        return {
            "event15_breaks_pre_high": None,
            "event15_breaks_pre_low": None,
            "event15_rejects_above_pre_high": None,
            "event15_rejects_below_pre_low": None,
        }
    pre_high = float(pre["price"].max())
    pre_low = float(pre["price"].min())
    event_high = float(event15["price"].max())
    event_low = float(event15["price"].min())
    event_close = float(event15["price"].iloc[-1])
    return {
        "event15_breaks_pre_high": event_high > pre_high,
        "event15_breaks_pre_low": event_low < pre_low,
        "event15_rejects_above_pre_high": event_high > pre_high and event_close < pre_high,
        "event15_rejects_below_pre_low": event_low < pre_low and event_close > pre_low,
    }


def event_price_at(trades: pd.DataFrame, canonical: pd.Timestamp) -> float | None:
    before = trades[trades["ts_event"] <= canonical]
    if before.empty:
        return _safe_float(trades["price"].iloc[0]) if not trades.empty else None
    return _safe_float(before["price"].iloc[-1])


def compute_event_features(event: dict[str, Any], trades: pd.DataFrame, futures_symbol: str) -> dict[str, Any]:
    prepared = prepare_trades(trades)
    symbol_trades = prepared[prepared["symbol"] == futures_symbol].copy()
    canonical = parse_utc(event["canonical_m15_close_utc"])
    window_start = parse_utc(event["window_start_utc"])
    window_end = parse_utc(event["window_end_utc"])
    pre60 = slice_window(symbol_trades, window_start, canonical)
    event15 = slice_window(symbol_trades, canonical - pd.Timedelta(minutes=15), canonical)
    post15 = slice_window(symbol_trades, canonical, min(canonical + pd.Timedelta(minutes=15), window_end))
    post60 = slice_window(symbol_trades, canonical, window_end)
    event_price = event_price_at(symbol_trades, canonical)
    row: dict[str, Any] = {
        "event_id": event["event_id"],
        "symbol": event["symbol"],
        "futures_symbol": futures_symbol,
        "is_primary_proxy": (
            (event["symbol"] == "XAUUSD" and futures_symbol == "GC.v.0")
            or (event["symbol"] == "XAGUSD" and futures_symbol == "SI.v.0")
            or (event["symbol"] == "NAS100" and futures_symbol == "NQ.v.0")
            or (event["symbol"] in {"US30", "US30_cash"} and futures_symbol == "YM.v.0")
            or (event["symbol"] == "GBPUSD" and futures_symbol == "6B.v.0")
        ),
        "event_class": event["event_class"],
        "decision": event.get("decision"),
        "framework": event.get("framework"),
        "setup_grade": event.get("setup_grade"),
        "direction": event.get("direction"),
        "canonical_m15_close_utc": event["canonical_m15_close_utc"],
        "window_start_utc": event["window_start_utc"],
        "window_end_utc": event["window_end_utc"],
        "window_truncated_at_available_end": event.get("window_truncated_at_available_end"),
        "data_status": "ok" if not symbol_trades.empty else "no_data",
        "event_price": event_price,
        "total_trades_in_group_symbol": int(len(symbol_trades)),
    }
    row.update(flow_stats(pre60, futures_symbol, "pre60"))
    row.update(flow_stats(event15, futures_symbol, "event15"))
    row.update(flow_stats(post15, futures_symbol, "post15"))
    row.update(flow_stats(post60, futures_symbol, "post60"))
    row.update(volume_profile_stats(pre60, futures_symbol, event_price))
    row.update(range_rejection_stats(pre60, event15))
    return row


def median_or_none(values: list[Any]) -> float | None:
    numeric = [float(value) for value in values if value is not None and not isinstance(value, bool)]
    if not numeric:
        return None
    return _safe_float(float(np.median(numeric)))


def generated_at_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
