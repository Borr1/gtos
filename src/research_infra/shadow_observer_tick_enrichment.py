"""MT5 tick enrichment backfill for no-AI shadow observer rows."""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.components.tick_capture import classify_aggressor
from src.research_infra.forward_capture import PROMOTION_VERDICT, append_jsonl

SCHEMA_VERSION = "shadow_observer_tick_enrichment_v1"
DEFAULT_SOURCE = Path("shadow_logs/strategy_follow_evaluations.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/shadow_observer_tick_enrichment.jsonl")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def existing_keys(path: Path) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in read_jsonl(path):
        candidate_id = str(row.get("candidate_id") or "")
        decision_time = str(row.get("decision_time_utc") or "")
        if candidate_id and decision_time:
            keys.add((candidate_id, decision_time))
    return keys


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_tick(row: Any) -> dict[str, Any] | None:
    try:
        return {
            "time_msc": int(row["time_msc"]),
            "bid": float(row["bid"]),
            "ask": float(row["ask"]),
            "last": float(row["last"]),
            "volume": float(row["volume"]) if _safe_float(row["volume"]) not in (None, 0.0) else 1.0,
            "flags": int(row["flags"]),
        }
    except Exception:
        return None


def summarize_ticks(ticks: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted((tick for tick in ticks if tick), key=lambda item: int(item.get("time_msc") or 0))
    if not rows:
        return {
            "tick_count": 0,
            "status": "NO_TICKS_IN_WINDOW",
        }
    prev_price = None
    prev_aggressor = None
    buy_count = sell_count = neutral_count = 0
    cumulative_delta = 0.0
    spreads = []
    mids = []
    for row in rows:
        bid = float(row["bid"])
        ask = float(row["ask"])
        last = float(row.get("last") or 0.0)
        flags = int(row.get("flags") or 0)
        aggressor = classify_aggressor(
            bid=bid,
            ask=ask,
            last=last,
            flags=flags,
            prev_price=prev_price,
            prev_aggressor=prev_aggressor,
        )
        volume = float(row.get("volume") or 1.0)
        if aggressor == "buy":
            buy_count += 1
            cumulative_delta += volume
        elif aggressor == "sell":
            sell_count += 1
            cumulative_delta -= volume
        else:
            neutral_count += 1
        prev_price = last if last > 0 else (bid + ask) / 2.0
        prev_aggressor = aggressor
        spreads.append(ask - bid)
        mids.append((bid + ask) / 2.0)
    classifiable = buy_count + sell_count
    return {
        "tick_count": len(rows),
        "status": "FEATURES_EXTRACTED",
        "first_time_msc": rows[0]["time_msc"],
        "last_time_msc": rows[-1]["time_msc"],
        "buy_count": buy_count,
        "sell_count": sell_count,
        "neutral_count": neutral_count,
        "buy_pct": round(buy_count / classifiable, 6) if classifiable else None,
        "cumulative_delta_ticks": cumulative_delta,
        "median_spread": statistics.median(spreads) if spreads else None,
        "max_spread": max(spreads) if spreads else None,
        "mid_change": mids[-1] - mids[0] if len(mids) >= 2 else 0.0,
    }


def pull_mt5_ticks(symbol: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import MetaTrader5 as mt5  # type: ignore

        if not mt5.initialize():
            return [], "mt5_initialize_failed"
        try:
            raw = mt5.copy_ticks_range(symbol, start, end, mt5.COPY_TICKS_ALL)
            if raw is None:
                return [], "mt5_copy_ticks_range_returned_none"
            ticks = []
            for row in raw:
                normalized = normalize_tick(row)
                if normalized is not None:
                    ticks.append(normalized)
            return ticks, None
        finally:
            mt5.shutdown()
    except Exception as exc:  # noqa: BLE001
        return [], f"mt5_read_failed:{exc}"


def build_enrichment_row(
    observer_row: dict[str, Any],
    *,
    pull_ticks=pull_mt5_ticks,
    created_at_utc: str | None = None,
) -> dict[str, Any] | None:
    if observer_row.get("source_file") != "shadow_observer_mso_no_ai":
        return None
    decision_time = parse_utc(observer_row.get("decision_time_utc"))
    if decision_time is None:
        return None
    symbol = str(observer_row.get("broker_symbol") or observer_row.get("symbol") or "")
    start = decision_time - timedelta(minutes=60)
    event_start = decision_time - timedelta(minutes=15)
    ticks, error = pull_ticks(symbol, start, decision_time)
    event_ticks = [
        tick for tick in ticks if int(tick.get("time_msc") or 0) >= int(event_start.timestamp() * 1000)
    ]
    pre60 = summarize_ticks(ticks)
    event15 = summarize_ticks(event_ticks)
    status = "FEATURES_EXTRACTED" if ticks and error is None else "NO_TICKS_OR_READ_ERROR"
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": created_at_utc or utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "evidence_class": "FORWARD_SHADOW",
        "candidate_id": observer_row.get("candidate_id"),
        "decision_time_utc": observer_row.get("decision_time_utc"),
        "symbol": observer_row.get("symbol"),
        "broker_symbol": symbol,
        "source_symbol": observer_row.get("source_symbol"),
        "source_run_id": observer_row.get("source_run_id"),
        "observer_id": (observer_row.get("observer_metadata") or {}).get("observer_id"),
        "window_start_utc": start.isoformat(),
        "event15_start_utc": event_start.isoformat(),
        "window_end_utc": decision_time.isoformat(),
        "status": status,
        "mt5_read_error": error,
        "pre60_tick_summary": pre60,
        "event15_tick_summary": event15,
        "no_leak_status": "POST_DECISION_OBSERVER_ENRICHMENT_NOT_DECISION_FEATURE",
        "manual_backfill_status": "BACKFILLED_FROM_MT5_RECENT_TICKS_OR_EXPLICIT_BLOCKER",
        "no_ai_calls": True,
        "no_canary_required": True,
        "paid_fetch_attempted": False,
    }


def run(
    *,
    source_path: Path = DEFAULT_SOURCE,
    output_path: Path = DEFAULT_OUTPUT,
    symbol_filter: set[str] | None = None,
) -> dict[str, Any]:
    rows = read_jsonl(source_path)
    keys = existing_keys(output_path)
    written = 0
    skipped: dict[str, int] = {}
    for row in rows:
        symbol = str(row.get("symbol") or "")
        if symbol_filter and symbol not in symbol_filter:
            skipped["symbol_filtered"] = skipped.get("symbol_filtered", 0) + 1
            continue
        out = build_enrichment_row(row)
        if out is None:
            skipped["not_shadow_observer_or_missing_time"] = skipped.get(
                "not_shadow_observer_or_missing_time", 0
            ) + 1
            continue
        key = (str(out.get("candidate_id") or ""), str(out.get("decision_time_utc") or ""))
        if key in keys:
            skipped["duplicate_candidate_time"] = skipped.get("duplicate_candidate_time", 0) + 1
            continue
        append_jsonl(output_path, out)
        keys.add(key)
        written += 1
    return {
        "schema_version": "shadow_observer_tick_enrichment_summary_v1",
        "source": str(source_path),
        "output": str(output_path),
        "rows_seen": len(rows),
        "rows_written": written,
        "skipped": dict(sorted(skipped.items())),
    }
