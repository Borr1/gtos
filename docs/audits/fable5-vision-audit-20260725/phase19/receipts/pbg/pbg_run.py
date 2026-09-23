"""pbg_run — run the production broad-origin generator on a day's decision grid,
in close-only mode and (optionally) partial-bar mode.

Usage
    python3 pbg_run.py --days 2026-01-02 --out DIR [--minutes 1,3,5,7,10,14]
    python3 pbg_run.py --month 202601 --workers 6 --out DIR

Design notes (measured, see PARTIAL_BAR_GENERATOR_RESULT.md):

* CLOSE-ONLY at instant T reproduces the shipped contract exactly: raw_data is
  built by `v4_timewarp.raw_data_for_asof`, the MSO by `compute_market_state`,
  and the candidates by the real `generate_live_broader_origin_candidates`.
* PARTIAL at instant T+k (k = 1..14, bar B opens at T) uses:
    - the SAME MSO the engine holds at T (closed bars only — nothing from
      inside B is ever in the market-state object),
    - the M15 series = the 671 closed bars ending at T, plus the forming bar
      B synthesised from B's own M1 bars over [T, T+k),
    - so the bar *times* in the series are identical to the close-only call at
      T+15, and only the last bar differs (partial vs complete).
  No look-ahead of any kind: every input is a print at or before T+k.

The forming bar is selected inside the unmodified generator through the
`candle_open_utc` / `candle_close_utc` contract that `_selected_closed_bar_open`
(`broader_origin_generators.py:2179-2200`) already honours, so NOTHING under
`src/` is edited to take this measurement.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO))
os.chdir(REPO)

import pbg_lib as L  # noqa: E402

from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    raw_data_for_asof,
    replay_symbol_config,
    derive_session,
)
from src.components.market_state import compute_market_state  # noqa: E402
from src.components.broader_origin_generators import (  # noqa: E402
    generate_live_broader_origin_candidates,
)

CLOSE_K = 15
# trading days the sealed January/February/March arms did NOT run (measured from the
# CJ semantic candidate ledger's own `trading_day` set for January).
HOLIDAYS = {"2026-01-01"}
DIAG = bool(int(os.environ.get("PBG_DIAG", "0")))


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def trim_rows(rows, start: datetime, end: datetime):
    out = []
    for r in rows:
        ts = datetime.fromisoformat(r["time_utc"])
        if start <= ts <= end:
            out.append(r)
    return out


def build_day_context(symbols, day: str, min_rr: float, m1_months):
    """Load + trim sources for one UTC day."""
    d0 = datetime.fromisoformat(day + "T00:00:00+00:00")
    lo = d0 - timedelta(days=75)
    hi = d0 + timedelta(days=2)

    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        ResolvedSource,
        SourceSpec,
    )

    cfg = L.load_replay_config()
    if min_rr is not None:
        cfg.setdefault("risk", {})["min_rr"] = float(min_rr)
    # the sealed campaign REQUIRES market-state side effects off
    # (v4_timewarp:59281-59284 raises `d1_market_state_side_effects_must_be_disabled`).
    # Leaving them on writes knowledge_base/ and shadow_logs/ from every worker and
    # is repo dirt; it does not change the MSO, which is log-only either way.
    ms = cfg.setdefault("market_state", {})
    ms["side_effect_writes_enabled"] = False
    ms["structure_shadow_log_enabled"] = False

    sources = {}
    for sym in symbols:
        m15 = trim_rows(L.read_csv_bars(L.M15_DIR / f"{sym}_M15.csv"), lo, hi)
        h1 = L.aggregate_h1(m15)
        h4 = trim_rows(L.read_csv_bars(L.deep_path(sym, "H4")), lo, hi)
        d1 = trim_rows(L.read_csv_bars(L.deep_path(sym, "D1")), lo, hi)
        per_tf = {}
        for tf, rows in (("M15", m15), ("H1", h1), ("H4", h4), ("D1", d1)):
            spec = SourceSpec(
                symbol=sym,
                mapped_symbol=sym,
                timeframe=tf,
                path=Path(f"pbg://{sym}/{tf}"),
                source_family="lane_inputs_true_utc_v1",
                source_broker="ftmo",
                source_role="research",
            )
            per_tf[tf] = ResolvedSource(
                spec=spec,
                rows=tuple(rows),
                rows_by_day={},
                sha256="pbg",
                day_counts={},
                selected_status="pbg",
                min_required_rows_per_day=0,
            )
        sources[sym] = per_tf

    m1 = L.load_m1(symbols, m1_months, day=day) if m1_months else {}
    scfg = {sym: replay_symbol_config(cfg, sym) for sym in symbols}
    return sources, m1, scfg


def emit_rows(cands, *, k, asof, bar_open, sym):
    out = []
    for c in cands:
        try:
            e = float(c["entry_price"])
            s = float(c["stop_loss"])
        except (TypeError, ValueError, KeyError):
            continue
        out.append(
            {
                "k": k,
                "t": _iso(asof),
                "b": _iso(bar_open),
                "s": sym,
                "f": c.get("origin_family"),
                "d": "L" if str(c.get("side", "")).upper() == "LONG" else "S",
                "e": e,
                "sl": s,
                "tp": float(c.get("take_profit_1") or 0.0),
                "cid": c.get("candidate_id"),
            }
        )
        if DIAG:
            sf = c.get("source_fields") or {}
            out[-1].update(
                {
                    "pr": sf.get("proximity_gap_pct"),
                    "fp": c.get("limit_fillability_probability"),
                    "efp": c.get("execution_fill_probability"),
                    "rk": c.get("poi_scheduler_rankable_now"),
                    "ea": c.get("poi_execution_allowed_by_lifecycle"),
                    "dz": c.get("poi_distance_to_zone_atr"),
                    "ag": c.get("poi_age_hours"),
                    "tc": c.get("poi_touch_count"),
                    "mit": c.get("poi_max_mitigation_fraction"),
                    "cp": sf.get("current_price"),
                }
            )
    return out


def run_day(day: str, *, symbols, minutes, out_dir: Path, min_rr: float, m1_months):
    t0 = time.time()
    sources, m1, scfg = build_day_context(symbols, day, min_rr, m1_months)
    d0 = datetime.fromisoformat(day + "T00:00:00+00:00")
    boundaries = [d0 + timedelta(minutes=15 * i) for i in range(0, 96)]  # 00:00..23:45
    # the sealed CJ arm's own grid: 96 windows per trading day, 00:00 through 23:45
    # (verified against CJ_RECLOCKED_S0R0_V7_SEMANTIC_CANDIDATE_LEDGER: 96 distinct minutes)

    path = out_dir / f"pbg_{day}.jsonl.gz"
    n_rows = 0
    stats = {"day": day, "boundaries": len(boundaries), "mso_calls": 0, "gen_calls": 0}
    with gzip.open(path, "wt") as fh:
        for T in boundaries:
            raw_by_sym = {}
            mso_by_sym = {}
            for sym in symbols:
                try:
                    raw, _meta = raw_data_for_asof(
                        symbol=sym, sources=sources[sym], asof=T, config=scfg[sym]
                    )
                except Exception:
                    continue
                try:
                    mso = compute_market_state(raw, scfg[sym])
                except Exception:
                    continue
                raw_by_sym[sym] = raw
                mso_by_sym[sym] = mso
            stats["mso_calls"] += len(mso_by_sym)

            # ---- CLOSE-ONLY decision at T (the bar that just closed) --------
            xdata = {"raw_data_by_symbol": raw_by_sym}
            for sym, raw in raw_by_sym.items():
                kz = derive_session(sym, T)
                cands = generate_live_broader_origin_candidates(
                    raw, mso_by_sym[sym], scfg[sym], sym, kz, xdata, now_utc=T
                )
                stats["gen_calls"] += 1
                for row in emit_rows(
                    cands, k=CLOSE_K, asof=T, bar_open=T - timedelta(minutes=15), sym=sym
                ):
                    fh.write(json.dumps(row, separators=(",", ":")) + "\n")
                    n_rows += 1

            if not minutes:
                continue

            # ---- PARTIAL decisions inside the bar that OPENS at T -----------
            # closed history as of T+k ends with the bar closing at T; take 671
            # of them so appending the forming bar gives the same 672-bar window
            # the close-only call at T+15 would see.
            base_m15 = {}
            for sym, raw in raw_by_sym.items():
                base_m15[sym] = list(raw["candles"]["M15"])[-671:]

            for k in minutes:
                asof = T + timedelta(minutes=k)
                praw_by_sym = {}
                for sym, raw in raw_by_sym.items():
                    pb = L.synth_partial_m15(
                        bar_open=T, m1_index=m1.get(sym, {}), minutes=k
                    )
                    if pb is None:
                        continue
                    praw = dict(raw)
                    praw["candles"] = dict(raw["candles"])
                    praw["candles"]["M15"] = base_m15[sym] + [pb]
                    praw["candle_open_utc"] = _iso(T)
                    praw["candle_close_utc"] = _iso(asof)
                    praw["selected_closed_bar_open_utc"] = _iso(T)
                    praw["timestamp_utc"] = _iso(asof)
                    praw_by_sym[sym] = praw
                pxdata = {"raw_data_by_symbol": praw_by_sym}
                for sym, praw in praw_by_sym.items():
                    kz = derive_session(sym, asof)
                    cands = generate_live_broader_origin_candidates(
                        praw, mso_by_sym[sym], scfg[sym], sym, kz, pxdata, now_utc=asof
                    )
                    stats["gen_calls"] += 1
                    for row in emit_rows(cands, k=k, asof=asof, bar_open=T, sym=sym):
                        fh.write(json.dumps(row, separators=(",", ":")) + "\n")
                        n_rows += 1

    stats["rows"] = n_rows
    stats["seconds"] = round(time.time() - t0, 1)
    (out_dir / f"pbg_{day}.stats.json").write_text(json.dumps(stats, indent=1))
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", default="")
    ap.add_argument("--month", default="")
    ap.add_argument("--symbols", default="")
    ap.add_argument("--minutes", default="")
    ap.add_argument("--min-rr", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    symbols = (
        [s for s in args.symbols.split(",") if s] if args.symbols else list(L.SYMBOLS)
    )
    minutes = [int(x) for x in args.minutes.split(",") if x] if args.minutes else []
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.days:
        days = [d for d in args.days.split(",") if d]
    else:
        y, m = int(args.month[:4]), int(args.month[4:])
        d = datetime(y, m, 1, tzinfo=timezone.utc)
        days = []
        while d.month == m:
            # weekday AND not a market holiday the sealed arm skipped; the holiday
            # list is measured from the arm's own trading_day set, not assumed.
            if d.weekday() < 5 and d.date().isoformat() not in HOLIDAYS:
                days.append(d.date().isoformat())
            d += timedelta(days=1)

    months = sorted({d[:4] + d[5:7] for d in days}) if minutes else []
    # a decision at 00:15 on day 1 needs no earlier M1; partial bars only ever
    # read M1 inside their own day, but keep the neighbouring month for safety.
    if args.workers <= 1:
        for day in days:
            st = run_day(
                day,
                symbols=symbols,
                minutes=minutes,
                out_dir=out_dir,
                min_rr=args.min_rr,
                m1_months=months,
            )
            print(json.dumps(st), flush=True)
        return

    import multiprocessing as mp

    def _job(day):
        return run_day(
            day,
            symbols=symbols,
            minutes=minutes,
            out_dir=out_dir,
            min_rr=args.min_rr,
            m1_months=months,
        )

    with mp.get_context("fork").Pool(args.workers) as pool:
        for st in pool.imap_unordered(
            _RunDay(symbols, minutes, out_dir, args.min_rr, months), days
        ):
            print(json.dumps(st), flush=True)


class _RunDay:
    def __init__(self, symbols, minutes, out_dir, min_rr, months):
        self.a = (symbols, minutes, out_dir, min_rr, months)

    def __call__(self, day):
        symbols, minutes, out_dir, min_rr, months = self.a
        return run_day(
            day,
            symbols=symbols,
            minutes=minutes,
            out_dir=out_dir,
            min_rr=min_rr,
            m1_months=months,
        )


if __name__ == "__main__":
    main()
