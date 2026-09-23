#!/usr/bin/env python3
"""Pre-AI gate Q1 2026 replay (Phase A staleness check).

Mechanically tests the multi-framework pre-AI gate (`h1_poi_availability`)
across every M15 KZ candle for our 5 live instruments in Q1 2026
(Jan 2 - Mar 31). Pure compute, no API calls.

Three gate configurations are evaluated PER candle on the same MSO:

    A. baseline           = ['ob_retest']             (pre-Sunday config)
    B. multi_framework_v2 = ['ob_retest','fvg_fill','breaker_re_entry']
    C. disabled           = []  (gate passive — every candle reaches AI)

For each (instrument, month, kz, config) we record:
    - skip_count (gate said skip → no AI call)
    - per-framework POI counts (how often each framework has POI)
    - skip-only-when-ALL-zero (the actual gate semantics)

Outputs:
    summary.json     -- aggregated counters
    per_candle.csv   -- one row per candle (long format)
    REPORT.md        -- human-readable findings (written separately)

Usage:
    python research/pre_ai_gate_replay_2026-04-25/replay.py \
        --start 2026-01-02 --end 2026-03-31

Note: instruments are processed in parallel via process pools to compress
runtime. Each worker uses its own pipeline_state filename via PID, so the
production knowledge_base/pipeline_state/02_market_state.json side-effect
of compute_market_state is harmless (last writer wins; no decision-impact
since this script never touches the live pipeline).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import multiprocessing as mp
import os
import sys
import time as time_mod
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s [%(processName)s] %(message)s")
logger = logging.getLogger(__name__)

# Live instruments (matches scripts/simulate_t7_live_period.py)
SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]

# Kill zone windows (UTC) -- same as simulate_t7_live_period.KZ_WINDOWS
KZ_WINDOWS = {
    "XAUUSD":    {"london": (time(7, 0), time(10, 30)), "ny": (time(13, 0), time(17, 0))},
    "US30_cash": {"london": (time(8, 0), time(10, 30)), "ny": (time(13, 30), time(16, 0))},
    "USDJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPJPY":    {"london": (time(7, 0), time(9, 30)),  "ny": (time(13, 0), time(15, 30)), "tokyo": (time(0, 0), time(3, 0))},
    "GBPUSD":    {"london": (time(7, 0), time(12, 0)),  "ny": (time(13, 0), time(15, 30))},
}

CONFIGS = {
    "baseline": ["ob_retest"],
    "multi_framework_v2": ["ob_retest", "fvg_fill", "breaker_re_entry"],
    "disabled": [],
}

OUTPUT_DIR = _PROJECT_ROOT / "research" / "pre_ai_gate_replay_2026-04-25"


def _suppress_pipeline_writes() -> None:
    """Disable knowledge_base/pipeline_state/* writes for the duration of replay.

    `compute_market_state` calls `write_pipeline("02_market_state.json", ...)`
    every invocation. In a 5-instrument parallel replay this hammers a single
    file; nothing in this research path consumes the file, so we no-op it.
    """
    import src.utils.file_io as _file_io

    def _noop(*_args, **_kwargs):
        return None

    _file_io.write_pipeline = _noop
    # Also no-op atomic_write so any lurking caller that doesn't go through
    # write_pipeline is similarly silenced. Conservative; reverts on process exit.
    import src.components.market_state as _ms
    _ms.write_pipeline = _noop


def load_config_for_symbol(symbol: str) -> dict:
    """Load `config/agent_config.yaml` and apply per-instrument overrides."""
    import yaml
    from src.utils.config import apply_instrument_overrides

    cfg_path = _PROJECT_ROOT / "config" / "agent_config.yaml"
    with open(cfg_path) as f:
        config = yaml.safe_load(f)
    config = apply_instrument_overrides(config, symbol)
    # Force the canonical symbol so XAUUSD session-ATR + structure shadow
    # logger see the right instrument.
    config.setdefault("market", {})["symbol"] = symbol
    return config


def load_csvs(symbol: str) -> dict:
    """Load TradingView-format CSVs for all 4 timeframes."""
    from scripts.historical_data_loader import parse_tradingview_csv

    historical_dir = _PROJECT_ROOT / "data" / "historical_2026"
    out: dict[str, list[dict]] = {}
    for tf in ("D1", "H4", "H1", "M15"):
        p = historical_dir / f"{symbol}_{tf}.csv"
        if not p.exists():
            logger.warning("Missing CSV: %s", p)
            out[tf] = []
            continue
        out[tf] = parse_tradingview_csv(p)
    return out


def enumerate_kz_candles(
    m15_candles: list[dict],
    symbol: str,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """All M15 candles inside a kill-zone window in [start_date, end_date]."""
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
                })
                break
    return results


def _compute_bias(mso) -> str:
    """Match Orchestrator._compute_deterministic_bias return value."""
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


def _per_framework_poi(mso, bias: str) -> dict:
    """Mirror has_poi_for_framework for the three production frameworks."""
    from src.components.pre_ai_gates import (
        _has_ob_retest_poi,
        _has_fvg_fill_poi,
        _has_breaker_reentry_poi,
    )
    return {
        "ob_retest": bool(_has_ob_retest_poi(mso, bias=bias)),
        "fvg_fill": bool(_has_fvg_fill_poi(mso, bias=bias)),
        "breaker_re_entry": bool(_has_breaker_reentry_poi(mso, bias=bias)),
    }


def _gate_skip(frameworks: list[str], poi_flags: dict) -> bool:
    """Pure-Python re-implementation that matches h1_poi_availability semantics.

    Skip iff frameworks non-empty AND every framework lacks POI.
    """
    if not frameworks:
        return False
    for fw in frameworks:
        if poi_flags.get(fw, True):
            # POI present (or unknown framework -> fail-safe True) -> never skip
            return False
    return True


def _process_symbol(args_tuple) -> dict:
    """Worker entry-point: replay one symbol over [start, end]."""
    symbol, start_iso, end_iso = args_tuple

    _suppress_pipeline_writes()

    # Silence noisy STRUCTURE_DIVERGENCE INFO logs from the v2_shadow detector;
    # we don't consume divergence telemetry in this replay.
    logging.getLogger("src.components.structure_detector_shadow_logger").setLevel(
        logging.WARNING,
    )

    from scripts.historical_data_loader import build_raw_data, compute_session_levels
    from src.components.market_state import compute_market_state

    start_d = date.fromisoformat(start_iso)
    end_d = date.fromisoformat(end_iso)

    config = load_config_for_symbol(symbol)
    all_candles = load_csvs(symbol)
    if not all_candles.get("M15"):
        logger.warning("%s: no M15 data; skipping", symbol)
        return {
            "symbol": symbol, "n_candles": 0, "rows": [],
            "warnings": ["no_m15_data"],
        }

    last_m15 = all_candles["M15"][-1]["time"][:10]
    if last_m15 < end_iso:
        logger.warning(
            "%s: M15 data ends at %s, after end %s. Replay will use only "
            "available history.", symbol, last_m15, end_iso,
        )

    kz_candles = enumerate_kz_candles(all_candles["M15"], symbol, start_d, end_d)
    n_total = len(kz_candles)
    logger.info("%s: %d KZ candles (%s -> %s)", symbol, n_total, start_d, end_d)

    rows: list[dict] = []
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
        except Exception as e:  # noqa: BLE001 -- log and continue
            mso_errors += 1
            if mso_errors <= 3:
                logger.warning("%s MSO build failed @%s: %s", symbol, candle_time, e)
            continue

        bias = _compute_bias(mso)
        poi_flags = _per_framework_poi(mso, bias)

        # Per-config skip determination
        skip_baseline = _gate_skip(CONFIGS["baseline"], poi_flags)
        skip_multi = _gate_skip(CONFIGS["multi_framework_v2"], poi_flags)
        skip_disabled = _gate_skip(CONFIGS["disabled"], poi_flags)

        rows.append({
            "symbol": symbol,
            "candle_time": candle_time,
            "month": kz["month"],
            "date": kz["date"],
            "kill_zone": kz["kill_zone"],
            "bias": bias,
            "poi_ob_retest": int(poi_flags["ob_retest"]),
            "poi_fvg_fill": int(poi_flags["fvg_fill"]),
            "poi_breaker_re_entry": int(poi_flags["breaker_re_entry"]),
            "skip_baseline": int(skip_baseline),
            "skip_multi": int(skip_multi),
            "skip_disabled": int(skip_disabled),
        })

        if (i + 1) % 500 == 0:
            elapsed = time_mod.time() - t0
            logger.info(
                "  %s: %d/%d (%.1f%% done, %.1f cand/s)",
                symbol, i + 1, n_total, 100 * (i + 1) / n_total,
                (i + 1) / max(elapsed, 1e-3),
            )

    elapsed = time_mod.time() - t0
    logger.info("%s: done in %.1fs (%d rows, %d MSO errors)",
                symbol, elapsed, len(rows), mso_errors)
    return {
        "symbol": symbol, "n_candles": n_total, "rows": rows,
        "mso_errors": mso_errors, "elapsed_s": round(elapsed, 1),
        "warnings": [],
    }


def aggregate(rows: list[dict]) -> dict:
    """Build per-instrument and per-(instrument,month) summary tables."""
    by_inst: dict = defaultdict(lambda: defaultdict(int))
    by_inst_month: dict = defaultdict(lambda: defaultdict(int))
    by_inst_month_kz: dict = defaultdict(lambda: defaultdict(int))

    for r in rows:
        sym = r["symbol"]
        ym = r["month"]
        kz = r["kill_zone"]
        by_inst[sym]["n"] += 1
        by_inst[sym]["skip_baseline"] += r["skip_baseline"]
        by_inst[sym]["skip_multi"] += r["skip_multi"]
        by_inst[sym]["skip_disabled"] += r["skip_disabled"]
        by_inst[sym]["poi_ob_retest"] += r["poi_ob_retest"]
        by_inst[sym]["poi_fvg_fill"] += r["poi_fvg_fill"]
        by_inst[sym]["poi_breaker_re_entry"] += r["poi_breaker_re_entry"]
        # bias-direction-aware accounting
        if r["bias"] == "no_bias":
            by_inst[sym]["bias_no_bias"] += 1
        elif r["bias"] == "bullish":
            by_inst[sym]["bias_bullish"] += 1
        elif r["bias"] == "bearish":
            by_inst[sym]["bias_bearish"] += 1

        # Sanity check: invariant skip_multi <= skip_baseline ALWAYS
        # (multi-framework can only DECREASE skip rate by adding alternative
        #  POI sources; can never INCREASE it).
        # We don't break here; we just count violations.
        if r["skip_multi"] > r["skip_baseline"]:
            by_inst[sym]["invariant_violation"] += 1

        # Per-month
        bk = (sym, ym)
        by_inst_month[bk]["n"] += 1
        by_inst_month[bk]["skip_baseline"] += r["skip_baseline"]
        by_inst_month[bk]["skip_multi"] += r["skip_multi"]
        by_inst_month[bk]["poi_ob_retest"] += r["poi_ob_retest"]
        by_inst_month[bk]["poi_fvg_fill"] += r["poi_fvg_fill"]
        by_inst_month[bk]["poi_breaker_re_entry"] += r["poi_breaker_re_entry"]

        # Per-month-kz
        bkk = (sym, ym, kz)
        by_inst_month_kz[bkk]["n"] += 1
        by_inst_month_kz[bkk]["skip_baseline"] += r["skip_baseline"]
        by_inst_month_kz[bkk]["skip_multi"] += r["skip_multi"]

    return {
        "by_instrument": {sym: dict(d) for sym, d in by_inst.items()},
        "by_instrument_month": {
            f"{sym}|{ym}": dict(d) for (sym, ym), d in by_inst_month.items()
        },
        "by_instrument_month_kz": {
            f"{sym}|{ym}|{kz}": dict(d)
            for (sym, ym, kz), d in by_inst_month_kz.items()
        },
    }


def write_csv(rows: list[dict], out_path: Path) -> None:
    """Write all per-candle rows to CSV (long-format, one row per candle)."""
    if not rows:
        out_path.write_text("")
        return
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-AI gate Q1 2026 replay")
    parser.add_argument("--start", default="2026-01-02")
    parser.add_argument("--end", default="2026-03-31")
    parser.add_argument(
        "--symbols", nargs="+", default=SYMBOLS,
        help="Subset of instruments to replay (default: all 5)",
    )
    parser.add_argument(
        "--workers", type=int, default=min(5, mp.cpu_count()),
        help="Process pool size (default: 5)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    work = [(sym, args.start, args.end) for sym in args.symbols]
    logger.info("Launching %d workers for %d symbols (%s -> %s)",
                args.workers, len(work), args.start, args.end)

    t0 = time_mod.time()
    if args.workers > 1 and len(work) > 1:
        # spawn for clean import per worker (Windows requirement)
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=args.workers) as pool:
            results = pool.map(_process_symbol, work)
    else:
        results = [_process_symbol(t) for t in work]
    elapsed = time_mod.time() - t0
    logger.info("All workers done in %.1fs", elapsed)

    all_rows: list[dict] = []
    per_symbol_meta: dict = {}
    for r in results:
        sym = r["symbol"]
        per_symbol_meta[sym] = {
            "n_candles": r["n_candles"],
            "n_rows": len(r["rows"]),
            "mso_errors": r.get("mso_errors", 0),
            "elapsed_s": r.get("elapsed_s", 0.0),
            "warnings": r.get("warnings", []),
        }
        all_rows.extend(r["rows"])

    # Aggregate
    summary = aggregate(all_rows)
    summary["meta"] = {
        "start": args.start,
        "end": args.end,
        "symbols": args.symbols,
        "configs": CONFIGS,
        "total_candles": len(all_rows),
        "total_elapsed_s": round(elapsed, 1),
        "per_symbol": per_symbol_meta,
    }

    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    logger.info("Wrote %s", summary_path)

    csv_path = OUTPUT_DIR / "per_candle.csv"
    write_csv(all_rows, csv_path)
    logger.info("Wrote %s (%d rows)", csv_path, len(all_rows))

    # Console snapshot
    print("\n=== PER-INSTRUMENT SUMMARY ===")
    print(f"{'symbol':<12}{'n':>6}{'baseline%':>12}{'multi_v2%':>12}"
          f"{'delta_pp':>10}{'inv_viol':>10}")
    for sym in args.symbols:
        d = summary["by_instrument"].get(sym, {})
        n = d.get("n", 0)
        if n == 0:
            print(f"{sym:<12}{0:>6}  (no rows)")
            continue
        b = 100.0 * d.get("skip_baseline", 0) / n
        m = 100.0 * d.get("skip_multi", 0) / n
        v = d.get("invariant_violation", 0)
        print(f"{sym:<12}{n:>6}{b:>12.2f}{m:>12.2f}{(b - m):>10.2f}{v:>10}")


if __name__ == "__main__":
    main()
