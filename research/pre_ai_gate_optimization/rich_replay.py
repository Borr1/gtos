#!/usr/bin/env python3
"""Rich pre-AI gate replay for the Q1 2026 KZ candle population.

Extends the original replay (`research/pre_ai_gate_replay_2026-04-25/replay.py`)
by extracting per-candle MSO features that gate-tightening proposals can
filter on. Each row carries enough information to evaluate G2.1 / G2.2 / G2.3
without re-running compute_market_state.

Outputs: ``rich_per_candle.csv`` (one row per KZ candle, ~9k rows).

Pure compute, no API.
"""
from __future__ import annotations

import argparse
import csv
import logging
import multiprocessing as mp
import sys
import time as time_mod
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(processName)s] %(message)s",
)
logger = logging.getLogger(__name__)

SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]

KZ_WINDOWS = {
    "XAUUSD":    {"london": (time(7, 0), time(10, 30)), "ny": (time(13, 0), time(17, 0))},
    "US30_cash": {"london": (time(8, 0), time(10, 30)), "ny": (time(13, 30), time(16, 0))},
    "USDJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPUSD":    {"london": (time(7, 0), time(12, 0)),  "ny": (time(13, 0), time(15, 30))},
}

OUTPUT_DIR = _PROJECT_ROOT / "research" / "pre_ai_gate_optimization"


def _suppress_pipeline_writes() -> None:
    import src.utils.file_io as _file_io
    _file_io.write_pipeline = lambda *_a, **_k: None
    import src.components.market_state as _ms
    _ms.write_pipeline = lambda *_a, **_k: None


def load_config_for_symbol(symbol: str) -> dict:
    import yaml
    from src.utils.config import apply_instrument_overrides
    cfg_path = _PROJECT_ROOT / "config" / "agent_config.yaml"
    with open(cfg_path) as f:
        config = yaml.safe_load(f)
    config = apply_instrument_overrides(config, symbol)
    config.setdefault("market", {})["symbol"] = symbol
    return config


def load_csvs(symbol: str) -> dict:
    from scripts.historical_data_loader import parse_tradingview_csv
    historical_dir = _PROJECT_ROOT / "data" / "historical_2026"
    out: dict[str, list[dict]] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        p = historical_dir / f"{symbol}_{tf}.csv"
        if not p.exists():
            out[tf] = []
            continue
        out[tf] = parse_tradingview_csv(p)
    return out


def enumerate_kz_candles(m15_candles, symbol, start_date, end_date):
    kz_windows = KZ_WINDOWS.get(symbol, KZ_WINDOWS["XAUUSD"])
    results = []
    for c in m15_candles:
        dt = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
        d = dt.date()
        if d < start_date or d > end_date:
            continue
        if dt.weekday() >= 5:
            continue
        t = dt.time()
        for kz_name, (kz_start, kz_end) in kz_windows.items():
            if kz_start <= t < kz_end:
                results.append({
                    "candle_time": c["time"],
                    "date": str(d),
                    "kill_zone": kz_name,
                    "month": d.strftime("%Y-%m"),
                    "close": c["close"],
                    "high": c["high"],
                    "low": c["low"],
                })
                break
    return results


def _compute_bias(mso) -> str:
    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}
    def _dir(tf_name):
        tf = tfs.get(tf_name)
        if tf is None:
            return "unavailable"
        s = getattr(tf, "structure", None)
        return s.direction if s else "unavailable"
    d1, h4, h1 = _dir("D1"), _dir("H4"), _dir("H1")
    if d1 in ("bullish", "bearish"):
        return d1
    if h4 in ("bullish", "bearish"):
        return h4
    return "no_bias"


def _atr_at(candles, target_index, period=14):
    """Quick ATR(14) over the last `period` candles before target_index."""
    if target_index < period:
        return None
    s = 0.0
    for i in range(target_index - period, target_index):
        c = candles[i]
        prev = candles[i - 1] if i > 0 else c
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - prev["close"]),
            abs(c["low"] - prev["close"]),
        )
        s += tr
    return s / period


def _extract_features(mso, bias: str, m15_close: float):
    """Pull gate-relevant scalar features from the MSO."""
    h1 = mso.timeframes.get("H1") if mso and mso.timeframes else None
    m15 = mso.timeframes.get("M15") if mso and mso.timeframes else None

    feats = {
        "bias": bias,
        "h1_unmit_ob_count": 0,
        "h1_unmit_ob_count_aligned": 0,        # bullish OBs if bias=bullish (etc.)
        "h1_min_touch_aligned": -1,             # min touch_count among aligned OBs
        "h1_max_touch_aligned": -1,             # max ditto
        "h1_min_dist_atr_aligned": -1.0,        # nearest aligned OB distance, in H1 ATR
        "h1_unret_breaker_aligned": 0,
        "h1_breaker_dist_atr_min": -1.0,
        "m15_unfilled_fvg": 0,
        "m15_unfilled_fvg_aligned": 0,
        "m15_fvg_dist_atr_min": -1.0,
        "h1_atr": -1.0,
        "m15_close": m15_close,
    }

    h1_atr = None
    if h1 and getattr(h1, "atr_14", None):
        h1_atr = h1.atr_14
    feats["h1_atr"] = h1_atr if h1_atr else -1.0

    if h1 is not None:
        unmit_obs = [ob for ob in h1.order_blocks if not ob.mitigated]
        feats["h1_unmit_ob_count"] = len(unmit_obs)
        if bias in ("bullish", "bearish"):
            aligned_obs = [ob for ob in unmit_obs if ob.type == bias]
        else:
            aligned_obs = unmit_obs
        feats["h1_unmit_ob_count_aligned"] = len(aligned_obs)
        if aligned_obs:
            touches = [ob.touch_count for ob in aligned_obs]
            feats["h1_min_touch_aligned"] = min(touches)
            feats["h1_max_touch_aligned"] = max(touches)
            if h1_atr and h1_atr > 0:
                # distance from current m15 close to nearest aligned OB edge
                # (use ob.high for bullish demand below price; ob.low for bearish supply above)
                dists = []
                for ob in aligned_obs:
                    if bias == "bullish":
                        # demand zone — nearest edge is the OB high
                        d = abs(m15_close - ob.high)
                    elif bias == "bearish":
                        d = abs(m15_close - ob.low)
                    else:
                        d = min(abs(m15_close - ob.high), abs(m15_close - ob.low))
                    dists.append(d / h1_atr)
                feats["h1_min_dist_atr_aligned"] = min(dists)

        unret_breakers = [bb for bb in h1.breaker_blocks if not bb.is_retested]
        if bias in ("bullish", "bearish"):
            unret_aligned = [bb for bb in unret_breakers if bb.direction == bias]
        else:
            unret_aligned = unret_breakers
        feats["h1_unret_breaker_aligned"] = len(unret_aligned)
        if unret_aligned and h1_atr and h1_atr > 0:
            dists = []
            for bb in unret_aligned:
                if bias == "bullish":
                    d = abs(m15_close - bb.zone_high)
                elif bias == "bearish":
                    d = abs(m15_close - bb.zone_low)
                else:
                    d = min(abs(m15_close - bb.zone_high), abs(m15_close - bb.zone_low))
                dists.append(d / h1_atr)
            feats["h1_breaker_dist_atr_min"] = min(dists)

    if m15 is not None:
        unfilled = [fvg for fvg in m15.fair_value_gaps if not fvg.filled]
        feats["m15_unfilled_fvg"] = len(unfilled)
        if bias in ("bullish", "bearish"):
            aligned_fvgs = [fvg for fvg in unfilled if fvg.type == bias]
        else:
            aligned_fvgs = unfilled
        feats["m15_unfilled_fvg_aligned"] = len(aligned_fvgs)
        if aligned_fvgs and h1_atr and h1_atr > 0:
            dists = [abs(m15_close - fvg.midpoint) / h1_atr for fvg in aligned_fvgs]
            feats["m15_fvg_dist_atr_min"] = min(dists)

    return feats


def _process_symbol(args_tuple):
    symbol, start_iso, end_iso = args_tuple

    _suppress_pipeline_writes()

    logging.getLogger("src.components.structure_detector_shadow_logger").setLevel(
        logging.WARNING,
    )

    from scripts.historical_data_loader import build_raw_data, compute_session_levels
    from src.components.market_state import compute_market_state
    from src.components.pre_ai_gates import (
        _has_ob_retest_poi,
        _has_fvg_fill_poi,
        _has_breaker_reentry_poi,
    )

    start_d = date.fromisoformat(start_iso)
    end_d = date.fromisoformat(end_iso)

    config = load_config_for_symbol(symbol)
    all_candles = load_csvs(symbol)
    if not all_candles.get("M15"):
        logger.warning("%s: no M15 data; skipping", symbol)
        return {"symbol": symbol, "rows": []}

    kz_candles = enumerate_kz_candles(all_candles["M15"], symbol, start_d, end_d)
    n_total = len(kz_candles)
    logger.info("%s: %d KZ candles", symbol, n_total)

    rows = []
    mso_errors = 0
    t0 = time_mod.time()

    for i, kz in enumerate(kz_candles):
        target_date = date.fromisoformat(kz["date"])
        candle_time = kz["candle_time"]
        try:
            session_levels = compute_session_levels(
                all_candles.get("M15", []), target_date,
            )
            raw_data = build_raw_data(
                all_candles, target_date, candle_time, session_levels,
                equal_level_tolerance=config.get("model_a", {}).get(
                    "equal_level_tolerance", 2.50,
                ),
                symbol=symbol,
            )
            mso = compute_market_state(raw_data, config)
        except Exception as e:
            mso_errors += 1
            if mso_errors <= 3:
                logger.warning("%s MSO err @%s: %s", symbol, candle_time, e)
            continue

        bias = _compute_bias(mso)
        feats = _extract_features(mso, bias, kz["close"])

        # POI flags - direction-aware (matches production)
        poi_ob = bool(_has_ob_retest_poi(mso, bias=bias))
        poi_fvg = bool(_has_fvg_fill_poi(mso, bias=bias))
        poi_brk = bool(_has_breaker_reentry_poi(mso, bias=bias))

        skip_baseline = not poi_ob
        skip_multi = not (poi_ob or poi_fvg or poi_brk)

        rows.append({
            "symbol": symbol,
            "candle_time": candle_time,
            "month": kz["month"],
            "date": kz["date"],
            "kill_zone": kz["kill_zone"],
            "bias": feats["bias"],
            "poi_ob_retest": int(poi_ob),
            "poi_fvg_fill": int(poi_fvg),
            "poi_breaker_re_entry": int(poi_brk),
            "skip_baseline": int(skip_baseline),
            "skip_multi": int(skip_multi),
            "h1_unmit_ob_count": feats["h1_unmit_ob_count"],
            "h1_unmit_ob_count_aligned": feats["h1_unmit_ob_count_aligned"],
            "h1_min_touch_aligned": feats["h1_min_touch_aligned"],
            "h1_max_touch_aligned": feats["h1_max_touch_aligned"],
            "h1_min_dist_atr_aligned": round(feats["h1_min_dist_atr_aligned"], 4),
            "h1_unret_breaker_aligned": feats["h1_unret_breaker_aligned"],
            "h1_breaker_dist_atr_min": round(feats["h1_breaker_dist_atr_min"], 4),
            "m15_unfilled_fvg": feats["m15_unfilled_fvg"],
            "m15_unfilled_fvg_aligned": feats["m15_unfilled_fvg_aligned"],
            "m15_fvg_dist_atr_min": round(feats["m15_fvg_dist_atr_min"], 4),
            "h1_atr": round(feats["h1_atr"], 6) if feats["h1_atr"] > 0 else -1,
            "m15_close": feats["m15_close"],
        })

        if (i + 1) % 500 == 0:
            elapsed = time_mod.time() - t0
            logger.info(
                "  %s: %d/%d (%.1f cand/s)",
                symbol, i + 1, n_total,
                (i + 1) / max(elapsed, 1e-3),
            )

    logger.info("%s: done %d rows %d MSO errs in %.1fs",
                symbol, len(rows), mso_errors, time_mod.time() - t0)
    return {"symbol": symbol, "rows": rows, "mso_errors": mso_errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-01-02")
    parser.add_argument("--end", default="2026-03-31")
    parser.add_argument("--symbols", nargs="+", default=SYMBOLS)
    parser.add_argument("--workers", type=int, default=min(5, mp.cpu_count()))
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    work = [(s, args.start, args.end) for s in args.symbols]
    logger.info("Launching %d workers for %d symbols", args.workers, len(work))

    t0 = time_mod.time()
    if args.workers > 1 and len(work) > 1:
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=args.workers) as pool:
            results = pool.map(_process_symbol, work)
    else:
        results = [_process_symbol(t) for t in work]
    elapsed = time_mod.time() - t0
    logger.info("All workers done in %.1fs", elapsed)

    all_rows = []
    for r in results:
        all_rows.extend(r["rows"])

    if not all_rows:
        logger.error("No rows produced.")
        return

    out_path = OUTPUT_DIR / "rich_per_candle.csv"
    fieldnames = list(all_rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)
    logger.info("Wrote %s (%d rows)", out_path, len(all_rows))


if __name__ == "__main__":
    main()
