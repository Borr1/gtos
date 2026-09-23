#!/usr/bin/env python3
"""Extract registered NAS100/NQ MBO diagnostics from UTC-midnight pulls.

Research/tooling only. This script intentionally computes only as-of pre60 and
event15 features. It does not use post-event MBO data for decision features and
does not emit promotion language.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts import analyze_orderflow_depth_mbp1_features as mbp1  # noqa: E402
from src.research_infra.orderflow_features import generated_at_utc, median_or_none, parse_utc, tick_size  # noqa: E402


DEFAULT_MANIFEST = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FULL_DAY_MANIFEST_2026-05-02.json"
)
DEFAULT_FETCH_PLAN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FULL_DAY_FETCH_EXECUTED_2026-05-02.json"
)
DEFAULT_OUTCOME_JOIN = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_AGGRESSIVE_SURGICAL_TRADES_OUTCOME_JOIN_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.md"
)

SUMMARY_FEATURES = (
    "event15_median_depth20_imbalance",
    "event15_median_total_depth20",
    "event15_thin_depth20_rate",
    "event15_median_wall_concentration20",
    "event15_near10_pull_pressure",
    "event15_near10_net_liquidity",
    "pre60_median_total_depth20",
    "pre60_near10_pull_pressure",
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def _side(value: Any) -> str | None:
    text = str(value or "").upper()
    if text.startswith("B"):
        return "B"
    if text.startswith("A") or text.startswith("S"):
        return "A"
    return None


def _action(value: Any) -> str:
    text = str(value or "").upper()
    return text[:1]


def _median(values: list[Any]) -> float | None:
    return median_or_none(values)


class WindowTracker:
    def __init__(self, windows: list[dict[str, Any]]) -> None:
        self.starts = sorted((window["start"], idx) for idx, window in enumerate(windows))
        self.ends = sorted((window["end"], idx) for idx, window in enumerate(windows))
        self.start_idx = 0
        self.end_idx = 0
        self.active: set[int] = set()

    def advance(self, ts: pd.Timestamp) -> set[int]:
        while self.start_idx < len(self.starts) and self.starts[self.start_idx][0] <= ts:
            self.active.add(self.starts[self.start_idx][1])
            self.start_idx += 1
        while self.end_idx < len(self.ends) and self.ends[self.end_idx][0] <= ts:
            self.active.discard(self.ends[self.end_idx][1])
            self.end_idx += 1
        return self.active


class WindowAccumulator:
    def __init__(self) -> None:
        self.samples: dict[str, list[float]] = defaultdict(list)
        self.action_sizes: dict[str, float] = defaultdict(float)
        self.sample_count = 0
        self.action_count = 0

    def add_sample(self, snapshot: dict[str, float | None]) -> None:
        self.sample_count += 1
        for key, value in snapshot.items():
            if value is not None:
                self.samples[key].append(float(value))

    def add_action(self, side: str | None, bucket: str, size: float, near10: bool) -> None:
        self.action_count += 1
        self.action_sizes[f"{bucket}_size"] += size
        if near10 and side in {"B", "A"}:
            side_name = "bid" if side == "B" else "ask"
            self.action_sizes[f"{bucket}_near10_{side_name}_size"] += size
            self.action_sizes[f"near10_{side_name}_size"] += size


class OrderBook:
    def __init__(self, futures_symbol: str) -> None:
        self.futures_symbol = futures_symbol
        self.tick_size = tick_size(futures_symbol)
        self.orders: dict[int, tuple[str, float, float]] = {}
        self.book: dict[str, dict[float, float]] = {"B": defaultdict(float), "A": defaultdict(float)}
        self.clear_count = 0
        self._best_bid: float | None = None
        self._best_ask: float | None = None

    def clear(self) -> None:
        self.orders.clear()
        self.book = {"B": defaultdict(float), "A": defaultdict(float)}
        self.clear_count += 1
        self._best_bid = None
        self._best_ask = None

    def best_bid(self) -> float | None:
        return self._best_bid

    def best_ask(self) -> float | None:
        return self._best_ask

    def _recompute_best(self, side: str) -> None:
        prices = [price for price, size in self.book[side].items() if size > 0]
        if side == "B":
            self._best_bid = max(prices) if prices else None
        else:
            self._best_ask = min(prices) if prices else None

    def _add_book(self, side: str, price: float, size: float) -> None:
        if size <= 0:
            return
        self.book[side][price] += size
        if side == "B" and (self._best_bid is None or price > self._best_bid):
            self._best_bid = price
        elif side == "A" and (self._best_ask is None or price < self._best_ask):
            self._best_ask = price

    def _remove_book(self, side: str, price: float, size: float) -> float:
        if size <= 0:
            return 0.0
        old = self.book[side].get(price, 0.0)
        removed = min(old, size)
        new = old - removed
        if new <= 0:
            self.book[side].pop(price, None)
            if (side == "B" and price == self._best_bid) or (side == "A" and price == self._best_ask):
                self._recompute_best(side)
        else:
            self.book[side][price] = new
        return removed

    def _near10(self, side: str | None, price: float | None, best_bid: float | None, best_ask: float | None) -> bool:
        if side == "B" and price is not None and best_bid is not None:
            return price >= best_bid - 10 * self.tick_size
        if side == "A" and price is not None and best_ask is not None:
            return price <= best_ask + 10 * self.tick_size
        return False

    def apply_row(self, row: Any, *, capture_effects: bool) -> list[dict[str, Any]]:
        action = _action(getattr(row, "action", None))
        if action == "R":
            self.clear()
            return []

        order_id = getattr(row, "order_id", None)
        try:
            order_key = int(order_id)
        except (TypeError, ValueError):
            order_key = None
        price = _safe_float(getattr(row, "price", None))
        size = _safe_float(getattr(row, "size", None)) or 0.0
        side = _side(getattr(row, "side", None))
        old = self.orders.get(order_key) if order_key is not None else None
        if old is not None:
            old_side, old_price, old_size = old
            side = side or old_side
            if price is None:
                price = old_price
        best_bid = self.best_bid() if capture_effects else None
        best_ask = self.best_ask() if capture_effects else None
        effects: list[dict[str, Any]] = []

        if action == "A":
            if order_key is not None and old is not None:
                self._remove_book(old[0], old[1], old[2])
            if order_key is not None and side in {"B", "A"} and price is not None and size > 0:
                self.orders[order_key] = (side, price, size)
                self._add_book(side, price, size)
                if capture_effects:
                    effects.append(
                        {
                            "side": side,
                            "price": price,
                            "bucket": "add",
                            "size": size,
                            "near10": self._near10(side, price, best_bid, best_ask),
                        }
                    )
            return effects

        if action == "C":
            if old is not None and order_key is not None:
                old_side, old_price, old_size = old
                cancel_size = old_size if size <= 0 else min(size, old_size)
                removed = self._remove_book(old_side, old_price, cancel_size)
                remaining = old_size - removed
                if remaining <= 0:
                    self.orders.pop(order_key, None)
                else:
                    self.orders[order_key] = (old_side, old_price, remaining)
                if capture_effects:
                    effects.append(
                        {
                            "side": old_side,
                            "price": old_price,
                            "bucket": "remove",
                            "size": removed,
                            "near10": self._near10(old_side, old_price, best_bid, best_ask),
                        }
                    )
            return effects

        if action == "M":
            if old is not None and order_key is not None and side in {"B", "A"} and price is not None:
                old_side, old_price, old_size = old
                self._remove_book(old_side, old_price, old_size)
                if size > 0:
                    self.orders[order_key] = (side, price, size)
                    self._add_book(side, price, size)
                else:
                    self.orders.pop(order_key, None)
                delta = size - old_size
                bucket = "add" if delta >= 0 else "remove"
                if capture_effects:
                    effects.append(
                        {
                            "side": side if delta >= 0 else old_side,
                            "price": price if delta >= 0 else old_price,
                            "bucket": bucket,
                            "size": abs(delta),
                            "near10": self._near10(side if delta >= 0 else old_side, price if delta >= 0 else old_price, best_bid, best_ask),
                        }
                    )
            elif order_key is not None and side in {"B", "A"} and price is not None and size > 0:
                self.orders[order_key] = (side, price, size)
                self._add_book(side, price, size)
                if capture_effects:
                    effects.append(
                        {
                            "side": side,
                            "price": price,
                            "bucket": "add",
                            "size": size,
                            "near10": self._near10(side, price, best_bid, best_ask),
                        }
                    )
            return effects

        if action in {"F", "T"}:
            bucket = "fill" if action == "F" else "trade"
            if old is not None and order_key is not None:
                old_side, old_price, old_size = old
                fill_size = old_size if size <= 0 else min(size, old_size)
                removed = self._remove_book(old_side, old_price, fill_size)
                remaining = old_size - removed
                if remaining <= 0:
                    self.orders.pop(order_key, None)
                else:
                    self.orders[order_key] = (old_side, old_price, remaining)
                if capture_effects:
                    effects.append(
                        {
                            "side": old_side,
                            "price": old_price,
                            "bucket": bucket,
                            "size": removed,
                            "near10": self._near10(old_side, old_price, best_bid, best_ask),
                        }
                    )
            elif side in {"B", "A"} and price is not None and size > 0:
                if capture_effects:
                    effects.append(
                        {
                            "side": side,
                            "price": price,
                            "bucket": bucket,
                            "size": size,
                            "near10": self._near10(side, price, best_bid, best_ask),
                        }
                    )
            return effects

        return effects

    def snapshot(self) -> dict[str, float | None]:
        def side_stats(side: str, levels: int) -> tuple[float, float]:
            reverse = side == "B"
            prices = sorted((price for price, size in self.book[side].items() if size > 0), reverse=reverse)[:levels]
            sizes = [self.book[side][price] for price in prices]
            return float(sum(sizes)), float(max(sizes)) if sizes else 0.0

        bid10, max_bid10 = side_stats("B", 10)
        ask10, max_ask10 = side_stats("A", 10)
        bid20, max_bid20 = side_stats("B", 20)
        ask20, max_ask20 = side_stats("A", 20)
        bid5, _ = side_stats("B", 5)
        ask5, _ = side_stats("A", 5)
        total10 = bid10 + ask10
        total20 = bid20 + ask20
        near5 = bid5 + ask5
        far6_20 = max(total20 - near5, 0.0)
        best_bid = self.best_bid()
        best_ask = self.best_ask()
        mid_px = (best_bid + best_ask) / 2.0 if best_bid is not None and best_ask is not None else None
        return {
            "mid_px": mid_px,
            "bid_depth10": bid10,
            "ask_depth10": ask10,
            "total_depth10": total10,
            "depth10_imbalance": (bid10 - ask10) / total10 if total10 > 0 else None,
            "bid_depth20": bid20,
            "ask_depth20": ask20,
            "total_depth20": total20,
            "depth20_imbalance": (bid20 - ask20) / total20 if total20 > 0 else None,
            "near_far_ratio20": near5 / far6_20 if far6_20 > 0 else None,
            "max_bid_wall20": max_bid20,
            "max_ask_wall20": max_ask20,
            "wall_concentration20": max(max_bid20, max_ask20) / total20 if total20 > 0 else None,
        }


def build_windows(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], WindowAccumulator]]:
    windows: list[dict[str, Any]] = []
    accs: dict[tuple[str, str], WindowAccumulator] = {}
    for event in events:
        event_id = event["event_id"]
        canonical = parse_utc(event["canonical_m15_close_utc"])
        pre_start = parse_utc(event["window_start_utc"])
        for prefix, start in (("pre60", pre_start), ("event15", canonical - pd.Timedelta(minutes=15))):
            key = (event_id, prefix)
            accs[key] = WindowAccumulator()
            windows.append({"event_id": event_id, "prefix": prefix, "start": start, "end": canonical})
    return windows, accs


def append_snapshot(accs: dict[tuple[str, str], WindowAccumulator], active: set[int], windows: list[dict[str, Any]], snapshot: dict[str, Any]) -> None:
    for idx in active:
        window = windows[idx]
        accs[(window["event_id"], window["prefix"])].add_sample(snapshot)


def append_effects(
    accs: dict[tuple[str, str], WindowAccumulator],
    active: set[int],
    windows: list[dict[str, Any]],
    effects: list[dict[str, Any]],
) -> None:
    if not effects or not active:
        return
    for idx in active:
        window = windows[idx]
        acc = accs[(window["event_id"], window["prefix"])]
        for effect in effects:
            acc.add_action(effect.get("side"), str(effect.get("bucket")), float(effect.get("size") or 0.0), bool(effect.get("near10")))


def finalize_window(prefix: str, acc: WindowAccumulator, *, tick: float, thin_threshold: float | None) -> dict[str, Any]:
    samples = acc.samples
    total20 = samples.get("total_depth20", [])
    thin_rate = None
    if thin_threshold is not None and total20:
        thin_rate = _safe_float(np.mean(np.array(total20, dtype=float) <= thin_threshold))
    mid_change = None
    mids = samples.get("mid_px", [])
    if len(mids) >= 2:
        mid_change = _safe_float((mids[-1] - mids[0]) / tick)
    add_bid = acc.action_sizes.get("add_near10_bid_size", 0.0)
    add_ask = acc.action_sizes.get("add_near10_ask_size", 0.0)
    remove_bid = acc.action_sizes.get("remove_near10_bid_size", 0.0)
    remove_ask = acc.action_sizes.get("remove_near10_ask_size", 0.0)
    near_add = add_bid + add_ask
    near_remove = remove_bid + remove_ask
    near_total = near_add + near_remove
    return {
        f"{prefix}_sample_count": int(acc.sample_count),
        f"{prefix}_action_count": int(acc.action_count),
        f"{prefix}_median_total_depth10": _median(samples.get("total_depth10", [])),
        f"{prefix}_median_depth10_imbalance": _median(samples.get("depth10_imbalance", [])),
        f"{prefix}_median_total_depth20": _median(total20),
        f"{prefix}_median_depth20_imbalance": _median(samples.get("depth20_imbalance", [])),
        f"{prefix}_median_near_far_ratio20": _median(samples.get("near_far_ratio20", [])),
        f"{prefix}_median_max_bid_wall20": _median(samples.get("max_bid_wall20", [])),
        f"{prefix}_median_max_ask_wall20": _median(samples.get("max_ask_wall20", [])),
        f"{prefix}_median_wall_concentration20": _median(samples.get("wall_concentration20", [])),
        f"{prefix}_thin_depth20_rate": thin_rate,
        f"{prefix}_mid_change_ticks": mid_change,
        f"{prefix}_near10_add_bid_size": _safe_float(add_bid),
        f"{prefix}_near10_add_ask_size": _safe_float(add_ask),
        f"{prefix}_near10_remove_bid_size": _safe_float(remove_bid),
        f"{prefix}_near10_remove_ask_size": _safe_float(remove_ask),
        f"{prefix}_near10_add_size": _safe_float(near_add),
        f"{prefix}_near10_remove_size": _safe_float(near_remove),
        f"{prefix}_near10_net_liquidity": _safe_float(near_add - near_remove),
        f"{prefix}_near10_pull_pressure": _safe_float(near_remove / near_total) if near_total > 0 else None,
        f"{prefix}_near10_bid_pull_pressure": _safe_float(remove_bid / (add_bid + remove_bid)) if (add_bid + remove_bid) > 0 else None,
        f"{prefix}_near10_ask_pull_pressure": _safe_float(remove_ask / (add_ask + remove_ask)) if (add_ask + remove_ask) > 0 else None,
    }


def load_mbo_features_for_group(
    path: Path,
    *,
    events: list[dict[str, Any]],
    futures_symbol: str,
    chunk_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import databento as db  # Local import keeps unit tests dependency-light.

    windows, accs = build_windows(events)
    action_tracker = WindowTracker(windows)
    sample_tracker = WindowTracker(windows)
    book = OrderBook(futures_symbol)
    store = db.DBNStore.from_file(str(path))
    last_sample_ts: pd.Timestamp | None = None
    rows_processed = 0
    unique_symbols: set[str] = set()
    action_counts: Counter[str] = Counter()

    for chunk in store.to_df(count=chunk_size):
        if chunk.empty:
            continue
        chunk = chunk.loc[:, ~chunk.columns.duplicated()].copy()
        required = {"ts_event", "action", "side", "price", "size", "order_id"}
        missing = required - set(chunk.columns)
        if missing:
            raise ValueError(f"MBO DBN missing columns {sorted(missing)}: {path}")
        if "symbol" in chunk.columns:
            unique_symbols.update(str(value) for value in chunk["symbol"].dropna().unique())
        chunk["ts_event"] = pd.to_datetime(chunk["ts_event"], utc=True)
        if isinstance(chunk.index, pd.DatetimeIndex):
            chunk["ts_process"] = pd.to_datetime(chunk.index, utc=True)
        else:
            chunk["ts_process"] = chunk["ts_event"]
        for row in chunk.itertuples(index=False):
            ts = getattr(row, "ts_process")
            sample_ts = ts.floor("s")
            if last_sample_ts is None:
                last_sample_ts = sample_ts
            elif sample_ts != last_sample_ts:
                append_snapshot(accs, sample_tracker.advance(last_sample_ts), windows, book.snapshot())
                last_sample_ts = sample_ts

            active = action_tracker.advance(ts)
            action_counts[_action(getattr(row, "action", None))] += 1
            effects = book.apply_row(row, capture_effects=bool(active))
            append_effects(accs, active, windows, effects)
            rows_processed += 1

    if last_sample_ts is not None:
        append_snapshot(accs, sample_tracker.advance(last_sample_ts), windows, book.snapshot())

    feature_rows: list[dict[str, Any]] = []
    for event in events:
        pre_acc = accs[(event["event_id"], "pre60")]
        pre_total20 = pre_acc.samples.get("total_depth20", [])
        thin_threshold = _safe_float(np.quantile(pre_total20, 0.2)) if pre_total20 else None
        row: dict[str, Any] = {
            "event_id": event["event_id"],
            "symbol": event["symbol"],
            "futures_symbol": futures_symbol,
            "is_primary_proxy": True,
            "event_class": event["event_class"],
            "decision": event.get("decision"),
            "framework": event.get("framework"),
            "direction": event.get("direction"),
            "canonical_m15_close_utc": event["canonical_m15_close_utc"],
            "window_start_utc": event["window_start_utc"],
            "data_status": "ok" if rows_processed else "no_data",
            "mbo_rows_processed_in_group": rows_processed,
            "mbo_book_clear_count": book.clear_count,
            "pre60_thin_depth20_threshold": thin_threshold,
        }
        row.update(finalize_window("pre60", pre_acc, tick=book.tick_size, thin_threshold=thin_threshold))
        row.update(finalize_window("event15", accs[(event["event_id"], "event15")], tick=book.tick_size, thin_threshold=thin_threshold))
        feature_rows.append(row)

    diagnostics = {
        "rows_processed": rows_processed,
        "unique_symbols": sorted(unique_symbols),
        "action_counts": dict(sorted(action_counts.items())),
        "book_clear_count": book.clear_count,
    }
    return feature_rows, diagnostics


def build_feature_rows(manifest: dict[str, Any], fetch_plan: dict[str, Any], *, chunk_size: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    events = {event["event_id"]: event for event in manifest.get("events") or []}
    manifest_groups = {group["group_id"]: group for group in manifest.get("fetch_groups") or []}
    rows: list[dict[str, Any]] = []
    group_diagnostics: dict[str, Any] = {}
    for fetch_group in fetch_plan.get("groups") or []:
        group_id = fetch_group["group_id"]
        manifest_group = manifest_groups.get(group_id, {})
        event_ids = fetch_group.get("event_ids") or manifest_group.get("event_ids") or []
        group_events = [events[event_id] for event_id in event_ids if event_id in events]
        output_path = Path(fetch_group["output_path"])
        request_symbols = fetch_group.get("request", {}).get("symbols") or ["NQ.v.0"]
        futures_symbol = request_symbols[0]
        if not output_path.exists():
            group_diagnostics[group_id] = {"status": "missing_raw", "output_path": str(output_path)}
            for event in group_events:
                rows.append(
                    {
                        "event_id": event["event_id"],
                        "symbol": event["symbol"],
                        "futures_symbol": futures_symbol,
                        "is_primary_proxy": True,
                        "event_class": event["event_class"],
                        "canonical_m15_close_utc": event["canonical_m15_close_utc"],
                        "data_status": "missing_raw",
                        "group_id": group_id,
                    }
                )
            continue
        group_rows, diagnostics = load_mbo_features_for_group(
            output_path,
            events=group_events,
            futures_symbol=futures_symbol,
            chunk_size=chunk_size,
        )
        for row in group_rows:
            row["group_id"] = group_id
        rows.extend(group_rows)
        group_diagnostics[group_id] = {"status": "ok", "output_path": str(output_path), **diagnostics}
    return rows, group_diagnostics


def summarize_bucket(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"n": len(rows)}
    for feature in SUMMARY_FEATURES:
        out[f"median_{feature}"] = median_or_none([row.get(feature) for row in rows])
    return out


def candidate_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in rows if row.get("data_status") == "ok"]
    candidate = summarize_bucket([row for row in ok if row.get("event_class") == "candidate"])
    context = summarize_bucket([row for row in ok if row.get("event_class") != "candidate"])
    deltas = {}
    for feature in SUMMARY_FEATURES:
        c = candidate.get(f"median_{feature}")
        x = context.get(f"median_{feature}")
        deltas[feature] = None if c is None or x is None else float(c) - float(x)
    return {"candidate": candidate, "context": context, "candidate_minus_context": deltas}


def outcome(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_rows = [
        row
        for row in rows
        if row.get("event_class") == "candidate"
        and row.get("data_status") == "ok"
        and row.get("candidate__synthetic_realized_r") is not None
    ]
    winners = [row for row in target_rows if float(row["candidate__synthetic_realized_r"]) > 0]
    losers = [row for row in target_rows if float(row["candidate__synthetic_realized_r"]) <= 0]
    winner = summarize_bucket(winners)
    loser = summarize_bucket(losers)
    deltas = {}
    for feature in SUMMARY_FEATURES:
        w = winner.get(f"median_{feature}")
        l = loser.get(f"median_{feature}")
        deltas[feature] = None if w is None or l is None else float(w) - float(l)
    return {"winner": winner, "loser": loser, "winner_minus_loser": deltas}


def build_readout(cc: dict[str, Any], out: dict[str, Any]) -> list[str]:
    delta = cc["candidate_minus_context"]
    odelta = out["winner_minus_loser"]
    return [
        (
            f"NAS100 MBO candidate/context n={cc['candidate']['n']}/{cc['context']['n']}; "
            f"event15 total-depth20 delta={_fmt(delta.get('event15_median_total_depth20'))}, "
            f"pull-pressure delta={_fmt(delta.get('event15_near10_pull_pressure'))}, "
            f"net-liquidity delta={_fmt(delta.get('event15_near10_net_liquidity'))}."
        ),
        (
            f"NAS100 MBO outcome n winner/loser={out['winner']['n']}/{out['loser']['n']}; "
            f"winner-minus-loser pull-pressure={_fmt(odelta.get('event15_near10_pull_pressure'))}, "
            f"winner-minus-loser total-depth20={_fmt(odelta.get('event15_median_total_depth20'))}."
        ),
        "This is a registered diagnostic pass, not a promotion result; actual broker-R coverage remains sparse.",
    ]


def build_payload(manifest: dict[str, Any], fetch_plan: dict[str, Any], outcome_payload: dict[str, Any], *, chunk_size: int) -> dict[str, Any]:
    rows, group_diagnostics = build_feature_rows(manifest, fetch_plan, chunk_size=chunk_size)
    mbp1.attach_outcomes(rows, mbp1.index_outcome_rows(outcome_payload))
    cc = candidate_context(rows)
    out = outcome(rows)
    status_counts = Counter(row.get("data_status") for row in rows)
    return {
        "schema_version": "orderflow_nas100_mbo_feature_diagnostic_v1",
        "generated_at_utc": generated_at_utc(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "registered_hypothesis_id": "OF-NAS100-DEPTH-ADVERSE-SELECTION-V1",
        "inputs": {
            "manifest_schema_version": manifest.get("schema_version"),
            "fetch_plan_schema_version": fetch_plan.get("schema_version"),
            "outcome_join_schema_version": outcome_payload.get("schema_version"),
            "feature_fields": list(SUMMARY_FEATURES),
            "chunk_size": chunk_size,
            "decision_windows": ["pre60", "event15"],
            "forbidden_windows": ["post15", "post60"],
        },
        "feature_rows": rows,
        "group_diagnostics": group_diagnostics,
        "synthesis": {
            "summary": (
                "Registered NAS100/NQ MBO diagnostics were extracted from UTC-midnight MBO pulls. "
                "Only pre60 and event15 as-of windows are scored."
            ),
            "feature_row_count": len(rows),
            "data_status_counts": dict(sorted(status_counts.items())),
            "candidate_context": cc,
            "outcome": out,
            "readout": build_readout(cc, out),
            "ambiguities": [
                "MBO action semantics are normalized defensively; action-level add/remove/fill buckets should be cross-checked before any future promotion dossier.",
                "The current outcome contrast is dominated by synthetic/path labels, not broker actual R.",
                "Candidate dates were chosen because candidates already existed; this is registered diagnostic validation, not broad population inference.",
                "No threshold was fitted or selected from the MBO outcome readout.",
            ],
            "open_questions": [
                "Does MBO add a clearer NAS100 failure signature than MBP-10?",
                "Are near-touch pull/add pressure features stable enough to justify SierraChart full-depth capture?",
                "Can future NAS100 candidates add enough winner-side coverage to test outcome contrast honestly?",
            ],
            "next_steps": [
                "Compare this MBO readout against the MBP-10 result before deciding whether more Databento MBO spend is justified.",
                "Continue forward surgical trades + MBP-10 collection for new NAS100 candidates.",
                "Use SierraChart/full-depth only if the feature family remains coherent after this MBO pass.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.4f}"


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    cc = synth["candidate_context"]
    outc = synth["outcome"]
    lines = [
        "# NAS100 MBO Feature Diagnostic",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Registered hypothesis: `{payload['registered_hypothesis_id']}`",
        "",
        "## Summary",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Feature rows: {synth['feature_row_count']}",
        f"- Data status counts: {synth['data_status_counts']}",
        f"- Decision windows: {payload['inputs']['decision_windows']}",
        f"- Forbidden windows: {payload['inputs']['forbidden_windows']}",
        "",
        "## Readout",
        "",
        *[f"- {item}" for item in synth["readout"]],
        "",
        "## Candidate vs Context",
        "",
        "| Bucket | n | event15 depth20 imbalance | event15 total depth20 | event15 thin rate | event15 wall concentration | event15 pull pressure | event15 net liquidity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ("candidate", "context"):
        row = cc[label]
        lines.append(
            "| "
            f"{label} | {row['n']} | "
            f"{_fmt(row.get('median_event15_median_depth20_imbalance'))} | "
            f"{_fmt(row.get('median_event15_median_total_depth20'))} | "
            f"{_fmt(row.get('median_event15_thin_depth20_rate'))} | "
            f"{_fmt(row.get('median_event15_median_wall_concentration20'))} | "
            f"{_fmt(row.get('median_event15_near10_pull_pressure'))} | "
            f"{_fmt(row.get('median_event15_near10_net_liquidity'))} |"
        )
    delta = cc["candidate_minus_context"]
    lines.append(
        "| candidate-context |  | "
        f"{_fmt(delta.get('event15_median_depth20_imbalance'))} | "
        f"{_fmt(delta.get('event15_median_total_depth20'))} | "
        f"{_fmt(delta.get('event15_thin_depth20_rate'))} | "
        f"{_fmt(delta.get('event15_median_wall_concentration20'))} | "
        f"{_fmt(delta.get('event15_near10_pull_pressure'))} | "
        f"{_fmt(delta.get('event15_near10_net_liquidity'))} |"
    )
    lines.extend(
        [
            "",
            "## Outcome Contrast",
            "",
            "| Bucket | n | event15 depth20 imbalance | event15 total depth20 | event15 thin rate | event15 wall concentration | event15 pull pressure | event15 net liquidity |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label in ("winner", "loser"):
        row = outc[label]
        lines.append(
            "| "
            f"{label} | {row['n']} | "
            f"{_fmt(row.get('median_event15_median_depth20_imbalance'))} | "
            f"{_fmt(row.get('median_event15_median_total_depth20'))} | "
            f"{_fmt(row.get('median_event15_thin_depth20_rate'))} | "
            f"{_fmt(row.get('median_event15_median_wall_concentration20'))} | "
            f"{_fmt(row.get('median_event15_near10_pull_pressure'))} | "
            f"{_fmt(row.get('median_event15_near10_net_liquidity'))} |"
        )
    odelta = outc["winner_minus_loser"]
    lines.append(
        "| winner-loser |  | "
        f"{_fmt(odelta.get('event15_median_depth20_imbalance'))} | "
        f"{_fmt(odelta.get('event15_median_total_depth20'))} | "
        f"{_fmt(odelta.get('event15_thin_depth20_rate'))} | "
        f"{_fmt(odelta.get('event15_median_wall_concentration20'))} | "
        f"{_fmt(odelta.get('event15_near10_pull_pressure'))} | "
        f"{_fmt(odelta.get('event15_near10_net_liquidity'))} |"
    )
    lines.extend(
        [
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--fetch-plan", default=DEFAULT_FETCH_PLAN)
    parser.add_argument("--outcome-join", default=DEFAULT_OUTCOME_JOIN)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--chunk-size", type=int, default=1_000_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(
        load_json(args.manifest),
        load_json(args.fetch_plan),
        load_json(args.outcome_join),
        chunk_size=args.chunk_size,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(f"feature_rows={payload['synthesis']['feature_row_count']} status={payload['synthesis']['data_status_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
