"""One-shot expired-POI watch evaluator.

Connects to MT5, reads active expired-POI watches for a symbol, evaluates the
latest closed M15 candle plus current tick, and writes shadow revalidation rows.
This script never places orders.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.data_ingestion import TF_MAP
from src.components.expired_poi_watch import (
    archive_expired_pending_intent,
    build_expired_poi_watch,
    evaluate_and_log_active_watches,
    evaluate_expired_poi_watch,
    load_active_watches,
)
from src.mt5 import create_mt5
from src.utils.config import apply_instrument_overrides, apply_profile_overrides, resolve_profile


def _load_config(path: str, symbol: str | None, profile: str | None) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    resolved = apply_profile_overrides(raw, resolve_profile(profile))
    return apply_instrument_overrides(resolved, symbol)


def _latest_candle(candles: list[dict[str, Any]]) -> dict[str, Any] | None:
    return candles[-1] if candles else None


def _load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _intent_like_from_record(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("metadata") or {}
    limit_info = record.get("limit_intent") or {}
    trade_params = record.get("trade_parameters") or {}
    pipeline = record.get("decision_pipeline") or {}
    decision_time = meta.get("candle_close_utc") or meta.get("candle_time")
    symbol = meta.get("symbol")
    candidate_id = (
        record.get("candidate_id")
        or meta.get("candidate_id")
        or (record.get("ai_response") or {}).get("candidate_id")
    )
    if not candidate_id and symbol and decision_time:
        candidate_id = f"{symbol}_{decision_time}"
    return {
        "direction": (
            limit_info.get("direction")
            or trade_params.get("direction")
            or pipeline.get("ai_direction")
        ),
        "limit_price": limit_info.get("limit_price") or trade_params.get("entry_price"),
        "stop_loss": limit_info.get("stop_loss") or trade_params.get("stop_loss"),
        "take_profit_1": (
            limit_info.get("take_profit_1") or trade_params.get("take_profit_1")
        ),
        "trade_id": limit_info.get("trade_id") or meta.get("trade_id"),
        "placed_time": (
            limit_info.get("placed_time")
            or meta.get("wall_clock_timestamp_utc")
            or meta.get("candle_time")
        ),
        "candidate_id": candidate_id,
        "decision_time_utc": decision_time,
        "source_symbol": symbol,
        "session": meta.get("kill_zone"),
        "kill_zone": meta.get("kill_zone"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--config", default="config/agent_config.yaml")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--mode", default="live", choices=["mock", "demo", "live"])
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--no-write", action="store_true", help="print evaluations without appending shadow rows")
    parser.add_argument("--seed-record", default=None, help="archive one LIMIT_PLACED trade record as an expired-POI watch")
    parser.add_argument("--cancel-reason", default="new_day", help="cancel reason for --seed-record")
    args = parser.parse_args()

    config = _load_config(args.config, args.symbol, args.profile)
    seeded_watch = None
    if args.seed_record:
        record = _load_json(args.seed_record)
        intent_like = _intent_like_from_record(record)
        if args.no_write:
            seeded_watch = build_expired_poi_watch(
                record=record,
                intent=intent_like,
                cancel_reason=args.cancel_reason,
                config=config,
                record_path=args.seed_record,
            )
        else:
            seeded_watch = archive_expired_pending_intent(
                record=record,
                intent=intent_like,
                cancel_reason=args.cancel_reason,
                config=config,
                record_path=args.seed_record,
            )

    mt5_symbol = config.get("market", {}).get("mt5_symbol", args.symbol)
    mt5 = create_mt5(mode=args.mode)
    if not mt5.connect():
        raise SystemExit("MT5 connection failed")

    try:
        tick = mt5.get_tick(mt5_symbol)
        candles = mt5.get_candles(mt5_symbol, TF_MAP["M15"], args.count)
        candle = _latest_candle(candles)

        if args.no_write:
            rows = [
                evaluate_expired_poi_watch(
                    watch,
                    candle=candle,
                    bid=getattr(tick, "bid", None) if tick else None,
                    ask=getattr(tick, "ask", None) if tick else None,
                    config=config,
                    kill_zone="manual_probe",
                )
                for watch in load_active_watches(args.symbol)
            ]
        else:
            rows = evaluate_and_log_active_watches(
                symbol=args.symbol,
                candle=candle,
                bid=getattr(tick, "bid", None) if tick else None,
                ask=getattr(tick, "ask", None) if tick else None,
                config=config,
                kill_zone="manual_probe",
            )

        print(json.dumps(
            {"symbol": args.symbol, "seeded_watch": seeded_watch, "rows": rows},
            indent=2,
            sort_keys=True,
        ))
        return 0
    finally:
        mt5.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
