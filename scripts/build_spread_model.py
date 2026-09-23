#!/usr/bin/env python3
"""Build ``spread_model_v1`` -- spread as a *band*, at any instant, for any symbol.

Why this exists
---------------
Every deep-history number in this estate charges a **37-day spread snapshot**
(2026-06-18..07-24, the tick archive) to as much as 26 years of bars. On a family
where cost runs 33-219% of gross R that is the largest disclosed bias in the
programme (`SESSION_W_WALKFORWARD_GATE_RESULT.md` §4 defect 4). It was stamped as a
disclosure; this module turns it into a **measurement with bands**.

Second, "no measured spread" currently makes a sleeve *unjudgeable* -- which is what
put `crypto`, a sleeve trading real money, at NOT_EVALUABLE. **A band is always
better than a refusal.**

The three inputs
----------------
1. **Ticks** -- ``/Users/borr/GTOSActive/vps-ticks-20260726/`` (263.9M rows, 55 files,
   sha-verified, OUTSIDE the repo). Broker wall clock, not UTC. This is the *anchor*:
   the one place a true quoted spread is observable.
2. **Bars** -- ``/Users/borr/GTOSActive/vps-bars-20260727/`` (43 FTMO + redacted_account
   symbols, D1/H4/M15, back to 2000). MT5 ``MqlRates.spread`` carries a **recorded
   spread per bar**. This is what makes the era term measurable rather than assumed.
   It is NOT clean -- see `_classify_era` -- and it is used for **ratios between
   eras**, never for levels, so any constant multiplicative bias cancels.
3. ``ULTIMATE_TICK_SPREAD_GOLD.json`` -- XAUUSD tick truth over a *second*,
   non-overlapping window (2025-10..2026-04). The out-of-sample calibration point.

Subcommands
-----------
    scan-ticks   ticks  -> TICK_SPREAD_CELLS.json      (hour-of-week x vol-state cells)
    scan-bars    bars   -> BAR_SPREAD_ERAS.json        (per symbol x quarter, all variants)
    fit          both   -> SPREAD_MODEL_V1.json + calibration receipts

Every fitted variant is written to ``SPREAD_MODEL_TRIAL_LEDGER.jsonl`` per
`WAVE_6_WORKING_AGREEMENT.md` §3.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import os
import re
import sys
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.utils.broker_clock import resolve_rule, broker_epoch_to_utc  # noqa: E402

TICKS = Path("/Users/borr/GTOSActive/vps-ticks-20260726")
BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
ROUTE = REPO / "research/operations/spread_model_2026_07_29"

SERVER = {"FTMO": "FTMO-Server3", "redacted_account": "redacted_account-Server 2"}

# Volatility state: quintiles of a trailing, point-in-time-correct D1 vol measure.
# Deliberately D1-based: M15 bars only reach back to 2024 for most symbols, so an
# M15-based state could not be carried into history at all.
VOL_STATES = 5
VOL_FAST = 20    # trailing window for the vol level
VOL_RANK = 500   # trailing window the level is ranked within

# A block pair only carries information if the measured spread actually changed.
# 2% is one point on a 50-point quote -- the smallest change the feed can express.
MOVE_THRESHOLD = 0.02


# --------------------------------------------------------------------- helpers


def read_json_maybe_gz(path: Path) -> dict:
    """Read `path`, or `path.gz` if that is what is on disk.

    The two scan intermediates are committed gzipped (12 MB -> 2.6 MB); §8 of CLAUDE.md
    is explicit that 97% of the tracked tree is already generated evidence.
    """
    if path.is_file():
        return json.loads(path.read_text())
    gz = Path(str(path) + ".gz")
    if gz.is_file():
        with gzip.open(gz, "rt") as fh:
            return json.load(fh)
    raise FileNotFoundError(f"neither {path} nor {gz} exists")


def _q(sorted_vals, p):
    if not sorted_vals:
        return None
    return sorted_vals[min(len(sorted_vals) - 1, int(p * len(sorted_vals)))]


def _hist_quantile(hist: dict, p: float):
    """Quantile of an integer-keyed count histogram, without materialising it."""
    if not hist:
        return None
    keys = sorted(int(k) for k in hist)
    total = sum(hist[k] if k in hist else hist[str(k)] for k in keys)
    target = p * total
    run = 0
    for k in keys:
        run += hist[k] if k in hist else hist[str(k)]
        if run >= target:
            return k
    return keys[-1]


def _hist_total(hist: dict) -> int:
    return sum(hist.values())


def _merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return out


def tick_files(broker: str):
    d = TICKS / broker.lower()
    for p in sorted(d.glob("*.csv.gz")):
        m = re.match(r"(FTMO|redacted_account)_(.+)_ticks_", p.name)
        if m:
            yield m.group(2), p


def bar_path(broker: str, symbol: str, tf: str) -> Path | None:
    p = BARS / f"{broker}_{symbol}_{tf}.csv.gz"
    return p if p.is_file() else None


def bar_symbol_for(broker: str, tick_symbol: str) -> str | None:
    """Tick files use `US100_cash`; bar files are keyed on the canonical GTOS name."""
    cands = [tick_symbol, tick_symbol.replace(".", "_"), tick_symbol.replace("_cash", "")]
    for c in cands:
        if bar_path(broker, c, "D1"):
            return c
    return None


def load_bars(path: Path):
    """-> list of (broker_epoch, open, high, low, close, tick_volume, spread_points)."""
    out = []
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            out.append(
                (
                    int(r["time"]),
                    float(r["open"]),
                    float(r["high"]),
                    float(r["low"]),
                    float(r["close"]),
                    int(r["tick_volume"]),
                    int(r["spread"]),
                )
            )
    out.sort()
    return out


def vol_state_series(d1_bars):
    """Two D1 volatility states per broker-day. Both are needed and they differ.

    ``trailing`` -- mean true-range/close over the last VOL_FAST *completed* days,
    percentile-ranked within the trailing VOL_RANK values. Nothing from day *t*
    enters day *t*'s own state, so a gate can charge it with **no look-ahead**.

    ``contemporaneous`` -- day *t*'s OWN true range, ranked in the same trailing
    reference. This is the one that physically drives spread (a dealer widens while
    the market is moving, not because last month was quiet), but a backtest cannot
    know it at entry. It is measured so the two elasticities can be COMPARED: if
    trailing predicts spread nearly as well, the model can be look-ahead-free at no
    cost, and if it does not, the gap is the honest size of the compromise.

    Returns ``{broker_epoch: (trailing_state, contemporaneous_state)}``.
    """
    tr_pct = []
    prev_close = None
    for (_t, _o, h, low, c, _v, _s) in d1_bars:
        tr = max(h - low,
                 abs(h - prev_close) if prev_close else 0.0,
                 abs(low - prev_close) if prev_close else 0.0)
        tr_pct.append(tr / c if c else 0.0)
        prev_close = c
    states = {}
    slow_hist: list[float] = []
    for i, (t, *_rest) in enumerate(d1_bars):
        if i < VOL_FAST:
            states[t] = (None, None)
            continue
        vol20 = sum(tr_pct[i - VOL_FAST:i]) / VOL_FAST
        slow_ref = sorted(slow_hist[-VOL_RANK:])
        fast_ref = sorted(tr_pct[max(0, i - VOL_RANK):i])
        trail = (min(VOL_STATES - 1, int(bisect_left(slow_ref, vol20) / len(slow_ref) * VOL_STATES))
                 if len(slow_ref) >= 60 else None)
        contemp = (min(VOL_STATES - 1, int(bisect_left(fast_ref, tr_pct[i]) / len(fast_ref) * VOL_STATES))
                   if len(fast_ref) >= 60 else None)
        states[t] = (trail, contemp)
        slow_hist.append(vol20)
    return states


# ----------------------------------------------------------------- scan-ticks


def scan_ticks(stride: int, out: Path, brokers=("ftmo", "redacted_account")):
    """Stream every tick file into hour-of-week x vol-state x week-block histograms.

    Spread is stored as an INTEGER count of `point`, which is exact: quotes are
    already quantised to the point. Histograms keep the full distribution at a few
    hundred KB per symbol -- no sampling of the distribution itself.
    """
    truth = json.loads(
        (REPO / "research/operations/broker_truth_layer_2026_07_27"
                "/BROKER_TRUE_COSTS_V1.json").read_text()
    )
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "stride": stride, "vol_states": VOL_STATES,
              "source": str(TICKS), "accounts": {}}

    for broker in brokers:
        acct = "FTMO" if broker == "ftmo" else "redacted_account"
        rule = resolve_rule(SERVER[acct])
        insts = truth["accounts"][acct]["instruments"]
        acc_out = {}
        for sym, path in tick_files(broker):
            key = sym.replace("_cash", ".cash")
            rec = insts.get(key) or insts.get(sym)
            point = (rec.get("spec") or {}).get("point") if rec else None
            if not point:
                print(f"  [skip] {acct} {sym}: no `point` in broker truth", flush=True)
                continue
            bsym = bar_symbol_for(acct, sym)
            vstates, d1_by_day = {}, {}
            if bsym:
                d1 = load_bars(bar_path(acct, bsym, "D1"))
                vstates = vol_state_series(d1)
                for (t, *_r) in d1:
                    d1_by_day[datetime.fromtimestamp(t, timezone.utc).date()] = t

            cells = defaultdict(Counter)   # (how, vtrail, vcontemp, block) -> Counter[pts]
            allh = Counter()
            first_e = last_e = None
            n = kept = dropped = 0
            with gzip.open(path, "rb") as fh:
                fh.readline()
                for line in fh:
                    n += 1
                    if n % stride:
                        continue
                    f = line.split(b",")
                    try:
                        e = int(f[0]); bid = float(f[1]); ask = float(f[2])
                    except (ValueError, IndexError):
                        continue
                    sp = ask - bid
                    if sp <= 0:
                        dropped += 1
                        continue
                    pts = int(round(sp / point))
                    if pts <= 0:
                        dropped += 1
                        continue
                    if first_e is None:
                        first_e = e
                    last_e = e
                    bw = datetime.fromtimestamp(e, timezone.utc)   # broker WALL, not UTC
                    how = bw.weekday() * 24 + bw.hour
                    day = bw.date()
                    vt, vc = vstates.get(d1_by_day.get(day), (None, None)) if d1_by_day else (None, None)
                    block = min(4, (e - first_e) // (7 * 86400))
                    cells[(how, -1 if vt is None else vt, -1 if vc is None else vc,
                           int(block))][pts] += 1
                    allh[pts] += 1
                    kept += 1
            if not kept:
                continue
            acc_out[key] = {
                "point": point,
                "rows_in_file": n,
                "rows_kept": kept,
                "rows_dropped_nonpositive": dropped,
                "broker_wall_first": datetime.fromtimestamp(first_e, timezone.utc).isoformat(),
                "broker_wall_last": datetime.fromtimestamp(last_e, timezone.utc).isoformat(),
                "utc_first": broker_epoch_to_utc(first_e, rule).isoformat(),
                "utc_last": broker_epoch_to_utc(last_e, rule).isoformat(),
                "bar_symbol": bsym,
                "all": dict(allh),
                "cell_key": "hour_of_week_brokerwall|vol_trailing|vol_contemporaneous|week_block",
                "cells": {f"{h}|{vt}|{vc}|{b}": dict(c)
                          for (h, vt, vc, b), c in cells.items()},
            }
            p50 = _hist_quantile(allh, 0.5)
            print(f"  {acct:11s} {key:12s} kept={kept:>9d} p50={p50 * point:.6g} "
                  f"cells={len(cells)}", flush=True)
        result["accounts"][acct] = acc_out

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return result


# ------------------------------------------------------------------ scan-bars


def _classify_era(vals: list[int]) -> str:
    """What KIND of number is the bar `spread` column here?

    Measured on this archive, the column mixes three populations and conflating
    them is the single easiest way to get the era term wrong:

    * ``RECORDED``   -- dispersed per-bar values. A real measurement.
    * ``SCHEDULE``   -- one constant held across a whole multi-year block
      (EURUSD 2000-2003 is exactly 50 points at p10 AND p99). That is the broker's
      history-server backfill: still the broker's own statement about the era, but
      it is MODELLED, not observed, and it gets a wider band.
    * ``FLOORED``    -- a large mass at 1 point next to a plausible upper tail
      (GBPJPY 2018: p25=1, p75=18, p90=26). 0.1 pip is not a GBPJPY spread; these
      bars carry a degenerate floor, and a p50 taken over them is meaningless.
    """
    if not vals:
        return "ABSENT"
    v = sorted(vals)
    n = len(v)
    distinct = len(set(v))
    if distinct == 1:
        return "SCHEDULE"
    lo, hi = _q(v, 0.25), _q(v, 0.90)
    frac_floor = sum(1 for x in v if x <= 1) / n
    if frac_floor >= 0.15 and hi >= 4 * max(1, lo):
        return "FLOORED"
    if distinct <= 3 and n >= 30:
        return "QUANTIZED"
    return "RECORDED"


# Candidate era estimators. Each is a *variant* and each is logged to the ledger.
ERA_ESTIMATORS = {
    "p50_nonzero":      lambda v: _q(sorted(v), 0.50),
    "p50_above_floor":  lambda v: _q(sorted([x for x in v if x > 1]), 0.50),
    "p75_nonzero":      lambda v: _q(sorted(v), 0.75),
    "p75_above_floor":  lambda v: _q(sorted([x for x in v if x > 1]), 0.75),
    "p90_nonzero":      lambda v: _q(sorted(v), 0.90),
    "mode_above_floor": lambda v: (Counter([x for x in v if x > 1]).most_common(1) or [(None, 0)])[0][0],
    "trimmed_mean_10":  lambda v: (lambda s: sum(s[int(.1 * len(s)):max(int(.1 * len(s)) + 1, int(.9 * len(s)))])
                                   / max(1, len(s[int(.1 * len(s)):max(int(.1 * len(s)) + 1, int(.9 * len(s)))]))
                                   )(sorted([x for x in v if x > 1])) if [x for x in v if x > 1] else None,
}


def scan_bars(out: Path, brokers=("FTMO", "redacted_account")):
    """Per (broker, symbol, timeframe, quarter): every era estimator + a quality class."""
    truth = json.loads(
        (REPO / "research/operations/broker_truth_layer_2026_07_27"
                "/BROKER_TRUE_COSTS_V1.json").read_text()
    )
    res = {"generated_utc": datetime.now(timezone.utc).isoformat(),
           "source": str(BARS), "estimators": sorted(ERA_ESTIMATORS),
           "accounts": {}}
    for acct in brokers:
        insts = truth["accounts"][acct]["instruments"]
        acc = {}
        for p in sorted(BARS.glob(f"{acct}_*_D1.csv.gz")):
            sym = p.name[len(acct) + 1:-len("_D1.csv.gz")]
            side = json.loads(Path(str(p) + ".timebase.json").read_text())
            broker_symbol = side.get("broker_symbol") or sym
            rec = insts.get(broker_symbol) or insts.get(sym) or insts.get(sym.replace("_cash", ".cash"))
            point = (rec.get("spec") or {}).get("point") if rec else None
            entry = {"broker_symbol": broker_symbol, "point": point, "timeframes": {}}
            for tf in ("D1", "H4", "M15"):
                bp = bar_path(acct, sym, tf)
                if not bp:
                    continue
                byq = defaultdict(list)
                tot = Counter()
                for (t, _o, _h, _l, _c, _v, s) in load_bars(bp):
                    d = datetime.fromtimestamp(t, timezone.utc)
                    q = f"{d.year}Q{(d.month - 1) // 3 + 1}"
                    tot[q] += 1
                    if s > 0:
                        byq[q].append(s)
                qs = {}
                for q in sorted(tot):
                    v = byq.get(q, [])
                    row = {"n_bars": tot[q], "n_nonzero": len(v),
                           "nonzero_frac": round(len(v) / tot[q], 4),
                           "class": _classify_era(v)}
                    if v:
                        row["distinct"] = len(set(v))
                        row["frac_floor_le1"] = round(sum(1 for x in v if x <= 1) / len(v), 4)
                        for name, fn in ERA_ESTIMATORS.items():
                            try:
                                row[name] = fn(v)
                            except Exception:
                                row[name] = None
                    qs[q] = row
                entry["timeframes"][tf] = qs
            acc[sym] = entry
            n_rec = sum(1 for q in entry["timeframes"].get("D1", {}).values()
                        if q["class"] == "RECORDED")
            print(f"  {acct:11s} {sym:12s} point={point} "
                  f"D1 quarters={len(entry['timeframes'].get('D1', {}))} RECORDED={n_rec}", flush=True)
        res["accounts"][acct] = acc
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return res


# ------------------------------------------------------------------------ fit
#
# Everything below turns the two scans into `spread_model_v1`. The one idea that
# makes it defensible: the bar column is used for **ratios between eras and never
# for levels**. Any constant multiplicative bias between "recorded bar spread" and
# "tick-median spread" — and there is one, measured at 1.00x-1.73x across 22
# symbols — divides out of a ratio. What has to be true is only that the column
# TRACKS spread changes, and that is what `validate_blocks` tests.


def _bar_vals_between(path: Path, lo_epoch: int, hi_epoch: int) -> list[int]:
    v = []
    with gzip.open(path, "rt") as fh:
        for r in csv.DictReader(fh):
            t = int(r["time"])
            if lo_epoch <= t < hi_epoch and int(r["spread"]) > 0:
                v.append(int(r["spread"]))
    return v


def _trimmed_mean(vals, lo_frac, hi_frac, drop_floor=True):
    v = sorted(x for x in vals if (x > 1 or not drop_floor))
    if not v:
        return None
    a = int(lo_frac * len(v))
    b = max(a + 1, int((1 - hi_frac) * len(v)))
    seg = v[a:b]
    return sum(seg) / len(seg) if seg else None


# The variant family. `mean_above_floor` reproduced the one out-of-sample era ratio
# best, but it is NOT robust to the legacy SCHEDULE constants leaking into a later
# quarter (GBPJPY 2023 carries the 150-point backfill in its upper tail), so the
# trimmed variants exist to beat it. Selection is by `validate_blocks`, not by the
# gold window, because the gold window was already looked at.
ERA_VARIANTS = {
    "mean_above_floor":    lambda v: _trimmed_mean(v, 0.0, 0.0),
    "trimmed_mean_0_05":   lambda v: _trimmed_mean(v, 0.0, 0.05),
    "trimmed_mean_0_10":   lambda v: _trimmed_mean(v, 0.0, 0.10),
    "trimmed_mean_05_05":  lambda v: _trimmed_mean(v, 0.05, 0.05),
    "trimmed_mean_10_10":  lambda v: _trimmed_mean(v, 0.10, 0.10),
    "trimmed_mean_10_25":  lambda v: _trimmed_mean(v, 0.10, 0.25),
    "median_above_floor":  lambda v: _q(sorted([x for x in v if x > 1]), 0.50),
    "p75_above_floor":     lambda v: _q(sorted([x for x in v if x > 1]), 0.75),
    "mean_all_nonzero":    lambda v: (sum(v) / len(v)) if v else None,
}

# Which variants discard the 1-point population. Everything except `mean_all_nonzero`
# does -- including every `trimmed_mean_*`, whose `_trimmed_mean` defaults to
# `drop_floor=True`. Keying the guard below on the NAME instead of on this set was a
# real defect in the first build: it left the trimmed variants in the ensemble for
# EURUSD, where they return the rare 2s against the mean's 1.05, and that factor-1.9
# artifact made all 27 EURUSD eras undecidable.
FLOOR_DROPPING = frozenset(set(ERA_VARIANTS) - {"mean_all_nonzero"})


def validate_blocks(cells_doc, ledger: list, account="FTMO", tf="H4"):
    """Does the bar column TRACK spread changes? The primary selection test.

    The 37-day tick window is cut into 5 weekly blocks. For every symbol and every
    ordered block pair, tick truth gives a real spread ratio and the bar column
    gives a predicted one. That is ~30 symbols x 10 pairs of held-out era ratios —
    a real sample, unlike the single gold-window point.

    Score is the median absolute log error, which is scale-free and robust.
    """
    insts = cells_doc["accounts"][account]
    out = {}
    for vname, fn in ERA_VARIANTS.items():
        errs, base_errs, moved_errs, moved_base, n_pairs, n_sym = [], [], [], [], 0, 0
        for sym, rec in insts.items():
            bsym = rec.get("bar_symbol")
            bp = bar_path(account, bsym, tf) if bsym else None
            if not bp:
                continue
            point = rec["point"]
            # tick side: p50 per weekly block, from the stored histograms
            tick_block = defaultdict(dict)
            for key, hist in rec["cells"].items():
                _h, _vt, _vc, b = key.split("|")
                tick_block[int(b)] = _merge(tick_block[int(b)] or {},
                                            {int(k): v for k, v in hist.items()})
            first = datetime.fromisoformat(rec["broker_wall_first"]).replace(tzinfo=timezone.utc)
            base = int(first.timestamp())
            bar_block = {}
            for b in sorted(tick_block):
                lo = base + b * 7 * 86400
                bar_block[b] = fn(_bar_vals_between(bp, lo, lo + 7 * 86400))
            blocks = [b for b in sorted(tick_block)
                      if bar_block.get(b) and _hist_total(tick_block[b]) >= 2000]
            if len(blocks) < 2:
                continue
            n_sym += 1
            for i in range(len(blocks)):
                for j in range(len(blocks)):
                    if i == j:
                        continue
                    bi, bj = blocks[i], blocks[j]
                    t_i = _hist_quantile(tick_block[bi], 0.5) * point
                    t_j = _hist_quantile(tick_block[bj], 0.5) * point
                    if not t_i or not t_j:
                        continue
                    true_r = t_j / t_i
                    pred_r = bar_block[bj] / bar_block[bi]
                    errs.append(abs(math.log(pred_r / true_r)))
                    # A low error is not automatically skill. Inside a 37-day window
                    # spreads barely move, so "predict no change" is already a strong
                    # baseline. Skill is what the model adds OVER it, and it is the
                    # number that decides whether the bar column tracks anything.
                    base_errs.append(abs(math.log(true_r)))
                    # ...and most pairs do not move AT ALL: quoted spread is quantised
                    # to the point, so the tick median is the SAME integer week to week
                    # for most symbols. Scoring on those pairs measures nothing (both
                    # model and baseline score exactly 0), and selecting on the pooled
                    # median picks the variant that best predicts "no change" rather
                    # than the one that tracks change. Selection therefore runs on the
                    # MOVED subset only.
                    if abs(math.log(true_r)) >= MOVE_THRESHOLD:
                        moved_errs.append(abs(math.log(pred_r / true_r)))
                        moved_base.append(abs(math.log(true_r)))
                    n_pairs += 1
        errs.sort(); base_errs.sort(); moved_errs.sort(); moved_base.sort()
        mmed = _q(moved_errs, 0.5) if moved_errs else None
        mbase = _q(moved_base, 0.5) if moved_base else None
        med = _q(errs, 0.5) if errs else None
        p90 = _q(errs, 0.9) if errs else None
        bmed = _q(base_errs, 0.5) if base_errs else None
        bp90 = _q(base_errs, 0.9) if base_errs else None
        out[vname] = {
            "variant": vname, "timeframe": tf, "n_symbols": n_sym, "n_block_pairs": n_pairs,
            "median_abs_log_err": round(med, 5) if med is not None else None,
            "p90_abs_log_err": round(p90, 5) if p90 is not None else None,
            "median_pct_err": round(100 * (math.exp(med) - 1), 2) if med is not None else None,
            "baseline_median_abs_log_err": round(bmed, 5) if bmed is not None else None,
            "baseline_p90_abs_log_err": round(bp90, 5) if bp90 is not None else None,
            "skill_vs_no_change_median": (round(1 - med / bmed, 4)
                                          if (med is not None and bmed) else None),
            "skill_vs_no_change_p90": (round(1 - p90 / bp90, 4)
                                       if (p90 is not None and bp90) else None),
            "n_moved_pairs": len(moved_errs),
            "moved_median_abs_log_err": round(mmed, 5) if mmed is not None else None,
            "moved_baseline_median_abs_log_err": round(mbase, 5) if mbase is not None else None,
            "moved_skill": (round(1 - mmed / mbase, 4) if (mmed is not None and mbase) else None),
        }
        ledger.append({"stage": "era_estimator_selection", "variant": vname,
                       "timeframe": tf, "criterion": "median_abs_log_err over held-out "
                       "weekly-block era ratios", **out[vname]})
    return out


def calibrate_gold(variant_fn, tf="H4"):
    """The out-of-sample era check named by the prompt: XAUUSD, a second tick window.

    `ULTIMATE_TICK_SPREAD_GOLD.json` measured XAUUSD over 2025-10..2026-04 at a median
    quoted spread of 0.37 price on 1,288,483 ticks. The 37-day archive window measures
    0.46 on 690,463. So tick truth says the spread ROSE 24% while the price FELL ~10% —
    which is the fact that already refuted naive price-proportional scaling (N §8.5),
    and it is reproduced here rather than assumed.
    """
    gold = json.loads((REPO / "research/operations/final_moonshot_v4_ultimate_mechanical"
                              "_edge_2026_06_10/ULTIMATE_TICK_SPREAD_GOLD.json").read_text())
    true_b = gold["spread_price"]["median"]
    truth = json.loads((REPO / "research/operations/broker_truth_layer_2026_07_27"
                               "/BROKER_TRUE_COSTS_V1.json").read_text())
    true_a = truth["accounts"]["FTMO"]["instruments"]["XAUUSD"]["spread_price"]["percentiles"]["p50"]
    bp = bar_path("FTMO", "XAUUSD", tf)
    to_e = lambda s: int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()) + 10800
    a = variant_fn(_bar_vals_between(bp, to_e("2026-06-18"), to_e("2026-07-25")))
    b = variant_fn(_bar_vals_between(bp, to_e("2025-10-01"), to_e("2026-05-01")))
    pred = b / a if (a and b) else None
    true_r = true_b / true_a
    return {
        "symbol": "XAUUSD", "timeframe": tf,
        "window_A": "2026-06-18..2026-07-24 (tick archive)",
        "window_B": "2025-10..2026-04 (ULTIMATE_TICK_SPREAD_GOLD.json)",
        "tick_spread_A_price": true_a, "tick_spread_B_price": true_b,
        "tick_ratio_B_over_A": round(true_r, 4),
        "bar_est_A": round(a, 3) if a else None, "bar_est_B": round(b, 3) if b else None,
        "bar_ratio_B_over_A": round(pred, 4) if pred else None,
        "pct_error": round(100 * (pred - true_r) / true_r, 2) if pred else None,
        "price_A": gold.get("spread_bps"), "note":
            "SECONDARY, not a selection criterion: this window was inspected before the "
            "variant family was written, so it is no longer out-of-sample for the winner.",
    }


def refute_price_proportional(bars_doc, ledger: list, account="FTMO", tf="H4"):
    """Is spread just a fixed number of basis points? Measured, per FOURTH_REVIEW §4.6.

    If spread were price-proportional, log(spread ratio) = 1.0 x log(price ratio) between
    any two eras, and the whole era model would collapse to "rescale by price". The gold
    artifact already showed one counterexample -- XAUUSD's spread rose 24% while its price
    FELL ~10% (N §8.5) -- and this regresses it across every consecutive quarter pair in
    the archive.

    (Computed from the bars here rather than read out of BAR_SPREAD_ERAS.json. The first
    version keyed on an estimator name that scan-bars never writes, so it silently
    collected ZERO pairs and then divided by zero. A statistic assembled from an empty
    set is the failure mode this whole review is about; it is safer to recompute.)
    """
    fn = ERA_VARIANTS["mean_all_nonzero"]
    xs, ys, syms = [], [], 0
    for sym in sorted(bars_doc["accounts"][account]):
        bp = bar_path(account, sym, tf)
        if not bp:
            continue
        sp, px = defaultdict(list), defaultdict(list)
        for (t, _o, _h, _l, c, _v, s) in load_bars(bp):
            d = datetime.fromtimestamp(t, timezone.utc)
            q = f"{d.year}Q{(d.month - 1) // 3 + 1}"
            px[q].append(c)
            if s > 0:
                sp[q].append(s)
        # RECORDED quarters only: a backfilled constant carries no information about
        # what the spread did, so including one would dilute the test toward beta=0.
        qs = [q for q in sorted(sp) if _classify_era(sp[q]) == "RECORDED" and px.get(q)]
        n0 = len(xs)
        for q0, q1 in zip(qs, qs[1:]):
            s0, s1 = fn(sp[q0]), fn(sp[q1])
            p0 = sum(px[q0]) / len(px[q0])
            p1 = sum(px[q1]) / len(px[q1])
            if s0 and s1 and p0 > 0 and p1 > 0:
                xs.append(math.log(p1 / p0))
                ys.append(math.log(s1 / s0))
        syms += 1 if len(xs) > n0 else 0
    n = len(xs)
    if n < 10:
        raise RuntimeError(f"only {n} quarter pairs -- refusing to regress on that")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    beta = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    alpha = my - beta * mx
    ss_res = sum((y - (alpha + beta * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot
    se = math.sqrt(ss_res / (n - 2) / sxx)
    out = {"n_quarter_pairs": n, "n_symbols": syms, "timeframe": tf,
           "beta_log_spread_on_log_price": round(beta, 4),
           "std_error": round(se, 4), "r_squared": round(r2, 4),
           "t_vs_beta_equals_1": round((beta - 1) / se, 2),
           "t_vs_beta_equals_0": round(beta / se, 2),
           "verdict": (
               f"beta = {beta:.3f} +/- {se:.3f}. The SLOPE is NOT rejected against 1.0 "
               f"({abs(beta - 1) / se:.1f} standard errors) -- saying otherwise would be an "
               "overclaim, and an earlier draft of this string made it. What is rejected is "
               f"price as a MODEL: it explains {100 * r2:.1f}% of the variance in era spread "
               "changes across "
               f"{n} quarter pairs on {syms} symbols. Knowing how the price moved between two "
               "eras tells you almost nothing about how the spread moved, so rescaling a "
               "historical spread by the price level is not a substitute for measuring it. "
               "The gold artifact's single counterexample -- XAUUSD spread +24% on a -10% "
               "price -- is not an exception; it is typical."),
           "what_is_refuted": "price-proportional scaling as a usable model (r_squared)",
           "what_is_NOT_refuted": "the slope itself, which is consistent with 1.0"}
    ledger.append({"stage": "price_proportionality_test", "variant": "ols_log_log",
                   "n_variants": 1, **out})
    return out


def _instrument_estimates(vals_by_tf: dict) -> dict:
    """Every (variant, timeframe) estimate of one era's spread level, in points.

    18 numbers for the same quantity. Their spread IS the model uncertainty -- it is
    measured disagreement between instruments looking at the same bars, not an
    assumed error bar, and it widens by itself exactly where the data is bad: a
    SCHEDULE quarter makes trimmed/median/mean variants disagree wildly, so the
    quality penalty falls out of the data instead of being asserted.
    """
    est = {}
    for tf, vals in vals_by_tf.items():
        if not vals:
            continue
        # A variant that throws away most of the data is not measuring the same
        # quantity as one that keeps it. EURUSD quotes ONE point today, so the
        # above-floor variants discard ~all of its reference window and return the
        # rare 2s; pooled with the mean's 1.35 that is a factor-2 "disagreement"
        # which is an artifact of the ensemble, not uncertainty about the spread. It
        # made every EURUSD era undecidable in the first build.
        floor_heavy = sum(1 for x in vals if x <= 1) / len(vals) > 0.5
        for vname, fn in ERA_VARIANTS.items():
            if floor_heavy and vname in FLOOR_DROPPING:
                continue
            try:
                v = fn(vals)
            except Exception:
                v = None
            if v and v > 0:
                est[f"{vname}@{tf}"] = float(v)
    return est


def _split_half_disagreement(vals: list, fn) -> float | None:
    """Sampling noise for THIS era at THIS sample size, measured not modelled.

    Interleaved halves (even/odd bar index) are two independent draws of the same
    era. |log| of their ratio is the era's own noise floor; it shrinks automatically
    as an era gets more bars, which is the behaviour the block-holdout sweep measured
    (skill 0.333 at 7 days -> 0.582 at 21) and the gold window confirmed at 7 months.
    """
    a, b = fn(vals[0::2]), fn(vals[1::2])
    if not a or not b or a <= 0 or b <= 0:
        return None
    return abs(math.log(b / a))


def _reference_vals(bars: list, ref_lo: int, ref_hi: int, min_bars: int = 100,
                    max_back_days: int = 730):
    """Reference-era bar spreads, widening backwards only if the window is empty.

    EURUSD has **zero** non-zero H4 spread readings inside the 37-day tick window --
    100% of its bars there record 0, meaning "not stored", not "no spread". Anchoring
    on an empty window silently dropped the single most-traded symbol in the archive
    from the first build of this model. The reference therefore widens until it has
    something to measure, and says by how much.
    """
    inside = [s for (t, *_r, s) in bars if ref_lo <= t < ref_hi and s > 0]
    if len(inside) >= min_bars // 4:
        return inside, 0
    for back in (90, 180, 365, max_back_days):
        lo = ref_hi - back * 86400
        wid = [s for (t, *_r, s) in bars if lo <= t < ref_hi and s > 0]
        if len(wid) >= min_bars:
            return wid, back
    return inside, -1


def _measure_class_hw_floor(eras_by_symbol: dict) -> dict:
    """Minimum band half-width per era class -- MEASURED, not asserted.

    A SCHEDULE quarter is a constant, so every instrument agrees with every other and
    the split-half noise is exactly zero: the band collapses to a point on the era
    where the data is *least* trustworthy. (DASHUSD 2026Q1 came out of the first build
    as mid=1.000 with a half-width of 0.000.) The honest floor is how much a spread
    ratio actually moves quarter to quarter where it IS recorded -- if the recorded
    quarters drift by a median of x, a backfilled constant cannot be tighter than x.
    """
    moves = defaultdict(list)
    for sym, eras in eras_by_symbol.items():
        qs = sorted(eras)
        for a, b in zip(qs, qs[1:]):
            if eras[a]["class"] == "RECORDED" and eras[b]["class"] == "RECORDED":
                ra, rb = eras[a]["era_ratio_mid"], eras[b]["era_ratio_mid"]
                if ra > 0 and rb > 0:
                    moves["RECORDED"].append(abs(math.log(rb / ra)))
    base = sorted(moves["RECORDED"])
    med = base[len(base) // 2] if base else 0.15
    # Recorded quarters set the scale; the degraded classes are floored at multiples of
    # it, ordered by how much of the per-bar signal each one has actually thrown away.
    return {"RECORDED": 0.0, "QUANTIZED": med, "FLOORED": 2 * med,
            "SCHEDULE": 2 * med, "ABSENT": 4 * med,
            "_recorded_median_quarter_move_log": med, "_n": len(base)}


def fit(reference_a: str, reference_b: str, winner: str, tfs=("H4", "D1"),
        accounts=("FTMO", "redacted_account"), max_decidable_hw: float = 0.5):
    """Build SPREAD_MODEL_V1: era ratios with measured bands, plus the intraweek shape.

    H4 is the era instrument and D1 is only a second opinion, because that is what the
    block holdout measured: **H4 skill 0.334 against D1's 0.007** over the same 188
    held-out pairs, and the same ordering out of sample on the gold window (-0.45% vs
    -6.97%). A D1 bar records one spread reading per day, so an era estimated from it is
    six times thinner. D1 is kept only where H4 is absent, and its disagreement with H4
    widens the band rather than voting in it.
    """
    cells = read_json_maybe_gz(ROUTE / "TICK_SPREAD_CELLS.json")
    truth = json.loads((REPO / "research/operations/broker_truth_layer_2026_07_27"
                               "/BROKER_TRUE_COSTS_V1.json").read_text())
    ledger: list = []
    to_e = lambda s: int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()) + 10800
    ref_lo, ref_hi = to_e(reference_a), to_e(reference_b)
    win_fn = ERA_VARIANTS[winner]

    out = {
        "schema": "spread_model_v1",
        "version": "1.0.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/build_spread_model.py fit",
        "reference_window_broker_wall": [reference_a, reference_b],
        "winning_era_estimator": winner,
        "era_timeframe": "H4 primary, D1 fallback and disagreement term only",
        "band_construction": (
            "mid = median over the H4 instrument ensemble (9 variants) of era/reference; "
            "half-width in log space = sqrt(cross-instrument dispersion^2 + split-half "
            "sampling noise^2 + D1-vs-H4 disagreement^2), floored per era class at the "
            "MEASURED median quarter-to-quarter move of RECORDED eras. All terms measured."
        ),
        "decidability_rule": (
            f"an era whose half-width exceeds {max_decidable_hw} in log space "
            f"(a ~{math.exp(max_decidable_hw):.2f}x span) is published as "
            "capture_required, not as a band. A band too wide to decide anything is a "
            "capture requirement, not a result."
        ),
        "honest_limit": (
            "Bands narrow the look-ahead; they do not eliminate it. Only forward tick "
            "capture does. The instrument is validated at era ratios of 0.78-1.30 (188 "
            "held-out weekly block pairs, skill 0.334 over assume-no-change; skill rises "
            "to 0.582 at 21-day blocks) and at one 7-month out-of-sample point (XAUUSD "
            "2025-10..2026-04, -0.45%). NOTHING validates it at the 5x-25x ratios the "
            "pre-2010 FX eras imply. Those eras are class BROKER SCHEDULE -- a backfilled "
            "constant, the broker's own statement about the era rather than a per-bar "
            "observation -- and they carry the widest bands for exactly that reason."
        ),
        "accounts": {},
    }

    for acct in accounts:
        insts = truth["accounts"][acct]["instruments"]
        tick_acc = cells["accounts"].get(acct, {})
        acc_out = {}
        for p in sorted(BARS.glob(f"{acct}_*_D1.csv.gz")):
            sym = p.name[len(acct) + 1:-len("_D1.csv.gz")]
            side = json.loads(Path(str(p) + ".timebase.json").read_text())
            broker_symbol = side.get("broker_symbol") or sym
            rec = (insts.get(broker_symbol) or insts.get(sym)
                   or insts.get(sym.replace("_cash", ".cash")))
            if not rec:
                continue
            point = (rec.get("spec") or {}).get("point")
            if not point:
                continue
            bars = {tf: load_bars(bar_path(acct, sym, tf)) for tf in tfs
                    if bar_path(acct, sym, tf)}
            ref_vals, ref_widen = {}, {}
            for tf, b in bars.items():
                v, w = _reference_vals(b, ref_lo, ref_hi)
                if v:
                    ref_vals[tf], ref_widen[tf] = v, w
            ref_est = _instrument_estimates(ref_vals)
            if not ref_est:
                continue

            tkey = next((k for k in (broker_symbol, sym, sym.replace("_cash", ".cash"))
                         if k in tick_acc), None)
            trec = tick_acc.get(tkey) if tkey else None
            if trec:
                anchor = _hist_quantile({int(k): v for k, v in trec["all"].items()}, 0.5) * point
                anchor_class = "MEASURED"
                anchor_prov = (f"tick archive, {trec['rows_kept']} sampled ticks, "
                               "p50 of quoted spread over the reference window")
            else:
                h4ref = [ref_est[k] for k in ref_est if k.endswith("@H4")]
                lvl = (sum(h4ref) / len(h4ref)) if h4ref else (
                    sum(ref_est.values()) / len(ref_est))
                anchor = lvl * point          # scaled by the class tick/bar factor below
                anchor_class = "MODELLED"
                anchor_prov = ("no tick file for this symbol: anchor is the H4 bar-recorded "
                               "level over the reference window, to be multiplied by the "
                               "class tick/bar factor (`tick_over_bar_factor`), which is "
                               "measured 1.00x-1.73x across 22 symbols that have both")

            byq = defaultdict(lambda: defaultdict(list))
            for tf, b in bars.items():
                for (t, *_r, s) in b:
                    if s > 0:
                        d = datetime.fromtimestamp(t, timezone.utc)
                        byq[f"{d.year}Q{(d.month - 1) // 3 + 1}"][tf].append(s)

            eras = {}
            for q, vt in sorted(byq.items()):
                est = _instrument_estimates(vt)
                h4 = sorted(est[k] / ref_est[k] for k in est
                            if k.endswith("@H4") and k in ref_est and ref_est[k])
                d1 = sorted(est[k] / ref_est[k] for k in est
                            if k.endswith("@D1") and k in ref_est and ref_est[k])
                use = h4 or d1
                if not use:
                    continue
                mid = use[len(use) // 2]
                logs = [math.log(r) for r in use]
                lm = sum(logs) / len(logs)
                disp = (math.sqrt(sum((x - lm) ** 2 for x in logs) / (len(logs) - 1))
                        if len(logs) > 1 else 0.0)
                noise = [d for d in (_split_half_disagreement(vt.get(tf) or [], win_fn)
                                     for tf in ("H4", "D1") if vt.get(tf)) if d is not None]
                nse = max(noise) if noise else 0.0
                # D1 is only a second opinion, and it is only a valid one when both
                # timeframes were normalised against the SAME reference window. EURUSD
                # widened H4 by 90 days and D1 by 730 (D1 has fewer bars, so it needed
                # more), which made the two ratios answer different questions and
                # manufactured a ln(2) "disagreement" that put all 27 of its eras out of
                # reach. Incomparable references contribute no disagreement term; the
                # fact is recorded instead.
                comparable = ref_widen.get("H4") == ref_widen.get("D1")
                tf_gap = (abs(math.log((d1[len(d1) // 2]) / mid))
                          if (comparable and h4 and d1 and mid > 0 and d1[len(d1) // 2] > 0)
                          else 0.0)
                klass = _classify_era(vt.get("H4") or vt.get("D1") or [])
                eras[q] = {
                    "era_ratio_mid": round(mid, 5),
                    "band_halfwidth_log": round(math.sqrt(disp ** 2 + nse ** 2 + tf_gap ** 2), 5),
                    "cross_instrument_dispersion_log": round(disp, 5),
                    "split_half_noise_log": round(nse, 5),
                    "d1_vs_h4_disagreement_log": round(tf_gap, 5),
                    "timeframe_references_comparable": comparable,
                    "n_instrument_estimates": len(use),
                    "n_bars_nonzero": sum(len(v) for v in vt.values()),
                    "timeframe_used": "H4" if h4 else "D1",
                    "class": klass,
                }
            acc_out[sym] = {
                "broker_symbol": broker_symbol,
                "instrument_class": rec.get("instrument_class"),
                "point": point,
                "anchor_spread_price": anchor,
                "anchor_coverage": anchor_class,
                "anchor_provenance": anchor_prov,
                "reference_widened_days": ref_widen,
                "reference_bar_estimates_points": {k: round(v, 4) for k, v in ref_est.items()},
                "eras": eras,
            }
            ledger.append({"stage": "era_series", "account": acct, "symbol": sym,
                           "n_variants": len(ERA_VARIANTS) * len(bars),
                           "n_eras": len(eras), "anchor_coverage": anchor_class})

        # --- symbols with TICKS but NO BARS -------------------------------------
        # Six tick files landed while this session was running (the export the prompt
        # said was in progress). Three of them -- EU50.cash, SPN35.cash, AUS200.cash --
        # have no bar file at all, so the loop above skips them: it iterates the bar
        # archive. That would have been a real defect in the band path and in the
        # embarrassing direction, because `cost_r` prices them fine from the flat
        # snapshot: passing `spread_band=` would have turned a priceable symbol into a
        # refusal. A band must never be worse than no band.
        #
        # What is knowable for them: today's spread, precisely (tick-measured). What is
        # not: any of its history. So they get a MEASURED anchor, an era ratio of 1.0,
        # and -- for any era other than the reference -- the widest honest band there is,
        # the observed spread of era ratios across that instrument class. Undecidable
        # away from the reference, and it says why.
        cls_ratios: dict[str, list[float]] = defaultdict(list)
        for r in acc_out.values():
            for e in r["eras"].values():
                if e["class"] == "RECORDED" and e["era_ratio_mid"] > 0:
                    cls_ratios[r["instrument_class"] or "unknown"].append(
                        math.log(e["era_ratio_mid"]))
        for sym, trec in tick_acc.items():
            if sym in acc_out or any(r["broker_symbol"] == sym for r in acc_out.values()):
                continue
            rec = insts.get(sym) or insts.get(sym.replace("_cash", ".cash"))
            point = (rec.get("spec") or {}).get("point") if rec else None
            if not point:
                continue
            klass = rec.get("instrument_class") or "unknown"
            obs = sorted(cls_ratios.get(klass) or
                         [x for v in cls_ratios.values() for x in v])
            hw = (max(abs(_q(obs, 0.05) or 0.0), abs(_q(obs, 0.95) or 0.0))
                  if obs else math.log(4.0))
            acc_out[sym] = {
                "broker_symbol": sym,
                "instrument_class": klass,
                "point": point,
                "anchor_spread_price": _hist_quantile(
                    {int(k): v for k, v in trec["all"].items()}, 0.5) * point,
                "anchor_coverage": "MEASURED",
                "anchor_provenance": (
                    f"tick archive, {trec['rows_kept']} sampled ticks, p50 of quoted spread "
                    "over the reference window. NO BAR FILE EXISTS for this symbol, so its "
                    "spread is known precisely today and not at all in the past."),
                "reference_widened_days": {},
                "reference_bar_estimates_points": {},
                "no_bar_history": True,
                "eras": {},
                "era_fallback": {
                    "era_ratio_mid": 1.0,
                    "band_halfwidth_log": round(hw, 5),
                    "basis": (f"p5/p95 of the observed log era ratio across the "
                              f"'{klass}' class ({len(obs)} RECORDED eras)"),
                    "decidable_at_reference_only": True,
                    "capture_requirement": (
                        f"{sym}: tick-measured today, no bar history at all. A broker "
                        "history pull for this symbol is what makes its era measurable; "
                        "until then any instant outside the reference window is priced at "
                        "the class-wide era spread and is not decidable."),
                },
            }
            ledger.append({"stage": "era_series_tick_only", "account": acct, "symbol": sym,
                           "n_variants": 1, "n_eras": 0, "anchor_coverage": "MEASURED"})

        # class half-width floors, measured on this account's own RECORDED eras
        floors = _measure_class_hw_floor({s: r["eras"] for s, r in acc_out.items()})
        for sym, r in acc_out.items():
            for q, e in r["eras"].items():
                hw = max(e["band_halfwidth_log"], floors.get(e["class"], 0.0))
                e["band_halfwidth_log_floored"] = round(hw, 5)
                e["era_ratio_low"] = round(e["era_ratio_mid"] * math.exp(-hw), 5)
                e["era_ratio_high"] = round(e["era_ratio_mid"] * math.exp(hw), 5)
                e["decidable"] = hw <= max_decidable_hw
                if not e["decidable"]:
                    e["capture_requirement"] = (
                        f"{sym} {q}: band spans {math.exp(2 * hw):.1f}x, wider than any "
                        "verdict can survive. Forward tick capture on this symbol, or a "
                        "broker history re-pull for this quarter, is what closes it.")
        out["accounts"][acct] = acc_out
        out.setdefault("class_halfwidth_floors", {})[acct] = floors
        ledger.append({"stage": "class_halfwidth_floor", "account": acct, "n_variants": 1,
                       **{k: v for k, v in floors.items() if not k.startswith("_")}})

    out["intraweek"] = _fit_intraweek(cells, truth, ledger)
    out["tick_over_bar_factor"] = _fit_tick_over_bar(cells, out, ledger)
    return out, ledger



def _fit_intraweek(cells, truth, ledger):
    """Spread multiplier by hour-of-week and by volatility state, pooled per class.

    Per symbol the 37-day window gives ~5 observations per hour-of-week, which is thin;
    pooling within an instrument class (each symbol normalised by its own median first,
    so a wide symbol cannot dominate a tight one) is what makes the shape estimable.
    """
    shape = {}
    for acct, insts in cells["accounts"].items():
        cls_h = defaultdict(lambda: defaultdict(list))
        cls_v = defaultdict(lambda: defaultdict(list))
        per_symbol = {}
        for sym, rec in insts.items():
            base = _hist_quantile({int(k): v for k, v in rec["all"].items()}, 0.5)
            if not base:
                continue
            trec = truth["accounts"][acct]["instruments"].get(sym)
            klass = (trec or {}).get("instrument_class", "unknown")
            h_acc, vt_acc, vc_acc = defaultdict(dict), defaultdict(dict), defaultdict(dict)
            for key, hist in rec["cells"].items():
                h, vt, vc, _b = (int(x) for x in key.split("|"))
                ih = {int(k): v for k, v in hist.items()}
                h_acc[h] = _merge(h_acc[h], ih)
                vt_acc[vt] = _merge(vt_acc[vt], ih)
                vc_acc[vc] = _merge(vc_acc[vc], ih)
            sym_h = {}
            for h, hh in h_acc.items():
                if _hist_total(hh) >= 200:
                    m = _hist_quantile(hh, 0.5) / base
                    cls_h[klass][h].append(m)
                    sym_h[h] = round(m, 4)
            for vt, hh in vt_acc.items():
                if vt >= 0 and _hist_total(hh) >= 500:
                    cls_v[f"{klass}|trailing"][vt].append(_hist_quantile(hh, 0.5) / base)
            for vc, hh in vc_acc.items():
                if vc >= 0 and _hist_total(hh) >= 500:
                    cls_v[f"{klass}|contemporaneous"][vc].append(_hist_quantile(hh, 0.5) / base)
            per_symbol[sym] = sym_h
        shape[acct] = {
            "by_class_hour_of_week": {k: {str(h): round(sorted(v)[len(v) // 2], 4)
                                          for h, v in sorted(d.items())}
                                      for k, d in cls_h.items()},
            "by_class_vol_state": {k: {str(s): round(sorted(v)[len(v) // 2], 4)
                                       for s, v in sorted(d.items())}
                                   for k, d in cls_v.items()},
            "by_symbol_hour_of_week": per_symbol,
        }
        ledger.append({"stage": "intraweek_shape", "account": acct,
                       "n_variants": 3, "n_classes": len(cls_h),
                       "note": "hour-of-week, vol_trailing, vol_contemporaneous"})
    return shape


def _fit_tick_over_bar(cells, model, ledger):
    """tick p50 / bar-recorded level, per symbol and per class.

    Measured 1.00x-1.73x across 22 symbols. It is NOT applied to era ratios (those
    cancel it) -- only to a MODELLED anchor, where a bar level has to stand in for a
    tick measurement that does not exist.
    """
    out = {}
    for acct, syms in model["accounts"].items():
        per, by_class = {}, defaultdict(list)
        for sym, rec in syms.items():
            if rec["anchor_coverage"] != "MEASURED":
                continue
            est = rec["reference_bar_estimates_points"]
            if not est:
                continue
            bar_level = (sum(est.values()) / len(est)) * rec["point"]
            if bar_level > 0:
                f = rec["anchor_spread_price"] / bar_level
                per[sym] = round(f, 4)
                by_class[rec["instrument_class"] or "unknown"].append(f)
        out[acct] = {
            "by_symbol": per,
            "by_class_median": {k: round(sorted(v)[len(v) // 2], 4) for k, v in by_class.items()},
            "global_median": round(sorted(per.values())[len(per) // 2], 4) if per else None,
            "n_symbols": len(per),
        }
        ledger.append({"stage": "tick_over_bar_factor", "account": acct,
                       "n_variants": 1, "n_symbols": len(per)})
    return out


# ------------------------------------------------------- entry timing (§5.5)


def entry_timing(out: Path, account="FTMO"):
    """What the ticks buy that bars cannot: the cost of the hour you enter in.

    FOURTH_REVIEW §5.5 lists entry-timing repair as the second-highest-value use of the
    263.9M-tick archive. Measured here, and it is not a rounding error:

        EURUSD  broker hour 00  p50 spread 25-28 points against a 1-point base   ~26x
        USDJPY  broker hour 00                 58 points against a 3-point base  ~19x
        XAUUSD  broker hour 00  -- no quote at all; the instrument is shut
        US500   broker hour 00  -- shut

    So it is an FX/JPY-family effect, it sits exactly on the broker daily rollover, and
    **that is where a D1 bar closes**. A sleeve that enters on the first tick after its
    D1 decision bar is entering in the single most expensive hour of its week. The
    repair is one hour of patience: by broker 01:00 the multiplier is back to 1.3-2.0x.

    This publishes the per-symbol hourly curve, the cost in R at a stated stop geometry,
    and the cheapest hour within a tolerance of each decision boundary. It does not
    change any sleeve -- entry convention is a sleeve-geometry decision and belongs to
    wave 7's cost-geometry lane (and thresholds are Borhen's).
    """
    cells = read_json_maybe_gz(ROUTE / "TICK_SPREAD_CELLS.json")
    truth = json.loads((REPO / "research/operations/broker_truth_layer_2026_07_27"
                               "/BROKER_TRUE_COSTS_V1.json").read_text())
    insts = truth["accounts"][account]["instruments"]
    res = {"schema": "entry_timing_v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
           "account": account,
           "clock": ("hour-of-week on the BROKER server wall clock (FTMO-Server3 = "
                     "America/New_York + 7h, US DST dates). Hour 0 of a weekday is the "
                     "daily rollover."),
           "reference_window": "2026-06-18..2026-07-24 tick archive",
           "symbols": {}}
    for sym, rec in cells["accounts"][account].items():
        point = rec["point"]
        base = _hist_quantile({int(k): v for k, v in rec["all"].items()}, 0.5)
        if not base:
            continue
        byh: dict[int, dict] = {}
        for k, h in rec["cells"].items():
            how = int(k.split("|")[0])
            byh[how] = _merge(byh.get(how, {}), {int(a): b for a, b in h.items()})
        hours = {}
        for how in sorted(byh):
            hh = byh[how]
            n = _hist_total(hh)
            if n < 100:
                continue
            hours[how] = {
                "n_ticks": n,
                "p50_points": _hist_quantile(hh, 0.5),
                "p90_points": _hist_quantile(hh, 0.9),
                "mult_p50": round(_hist_quantile(hh, 0.5) / base, 4),
                "mult_p90": round(_hist_quantile(hh, 0.9) / base, 4),
            }
        if not hours:
            continue
        rollover = [h for h in hours if h % 24 == 0]
        res["symbols"][sym] = {
            "instrument_class": (insts.get(sym) or {}).get("instrument_class"),
            "point": point,
            "base_p50_price": base * point,
            "quotes_through_rollover": bool(rollover),
            "rollover_mult_p50_median": (round(sorted(hours[h]["mult_p50"] for h in rollover)
                                               [len(rollover) // 2], 3) if rollover else None),
            "worst_hour": max(hours, key=lambda h: hours[h]["mult_p50"]),
            "worst_mult_p50": max(h["mult_p50"] for h in hours.values()),
            "best_hour": min(hours, key=lambda h: hours[h]["mult_p50"]),
            "best_mult_p50": min(h["mult_p50"] for h in hours.values()),
            "hours": {str(k): v for k, v in sorted(hours.items())},
        }
    worst = sorted(((r["rollover_mult_p50_median"] or 0, s) for s, r in res["symbols"].items()),
                   reverse=True)
    res["headline"] = {
        "n_symbols": len(res["symbols"]),
        "worst_rollover_symbols": [{"symbol": s, "rollover_mult_p50": m}
                                   for m, s in worst[:10]],
        "shut_at_rollover": [s for s, r in res["symbols"].items()
                             if not r["quotes_through_rollover"]],
        "prescription": (
            "For any sleeve on a symbol whose rollover multiplier exceeds ~3x, entering on "
            "the first tick after the broker daily boundary pays a spread it does not have "
            "to. Delaying to broker 01:00 recovers most of it. This is a measurement, not a "
            "change: entry convention is sleeve geometry and belongs to the wave-7 "
            "cost-geometry lane."),
    }
    out.write_text(json.dumps(res, indent=1))
    print(f"wrote {out}: {len(res['symbols'])} symbols")
    for m, s in worst[:8]:
        if m:
            r = res["symbols"][s]
            print(f"  {s:12s} rollover x{m:6.2f}  base={r['base_p50_price']:.6g}  "
                  f"best hour {r['best_hour'] % 24:02d} x{r['best_mult_p50']:.2f}")
    print("  shut at rollover:", ", ".join(res["headline"]["shut_at_rollover"]) or "none")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("scan-ticks")
    t.add_argument("--stride", type=int, default=4)
    t.add_argument("-o", default=str(ROUTE / "TICK_SPREAD_CELLS.json"))
    b = sub.add_parser("scan-bars")
    b.add_argument("-o", default=str(ROUTE / "BAR_SPREAD_ERAS.json"))
    v = sub.add_parser("validate")
    v.add_argument("--tf", default="H4")
    f_ = sub.add_parser("fit")
    f_.add_argument("--winner", default="mean_above_floor")
    f_.add_argument("--ref-a", default="2026-06-18")
    f_.add_argument("--ref-b", default="2026-07-25")
    f_.add_argument("-o", default=str(ROUTE / "SPREAD_MODEL_V1.json"))
    et = sub.add_parser("entry-timing")
    et.add_argument("-o", default=str(ROUTE / "ENTRY_TIMING_V1.json"))
    a = ap.parse_args()
    if a.cmd == "scan-ticks":
        scan_ticks(a.stride, Path(a.o))
    elif a.cmd == "scan-bars":
        scan_bars(Path(a.o))
    elif a.cmd == "validate":
        cells = read_json_maybe_gz(ROUTE / "TICK_SPREAD_CELLS.json")
        bars = read_json_maybe_gz(ROUTE / "BAR_SPREAD_ERAS.json")
        ledger = []
        res = validate_blocks(cells, ledger, tf=a.tf)
        f = lambda x, w, d: (f"{x:{w}.{d}f}" if x is not None else "-".rjust(w))
        print(f'{"variant":22s} {"pairs":>6s} {"moved":>6s} | MOVED SUBSET (selection): '
              f'{"err":>8s} {"base":>8s} {"skill":>7s} | ALL: {"p90":>7s} {"base90":>7s} {"skill90":>8s}')
        for k, r in sorted(res.items(), key=lambda kv: -(kv[1]["moved_skill"] or -9)):
            print(f'{k:22s} {r["n_block_pairs"]:6d} {r["n_moved_pairs"]:6d} |'
                  f'{"":26s}{f(r["moved_median_abs_log_err"],8,5)} '
                  f'{f(r["moved_baseline_median_abs_log_err"],8,5)} {f(r["moved_skill"],7,3)} |'
                  f'{"":5s}{f(r["p90_abs_log_err"],7,4)} {f(r["baseline_p90_abs_log_err"],7,4)} '
                  f'{f(r["skill_vs_no_change_p90"],8,3)}')
        best = max(res, key=lambda k: res[k]["moved_skill"] if res[k]["moved_skill"] is not None else -9)
        print(f"\nwinner by block holdout: {best}")
        print("gold-window check:", json.dumps(calibrate_gold(ERA_VARIANTS[best], a.tf), indent=1))
        print("price-proportionality:", json.dumps(refute_price_proportional(bars, ledger), indent=1))
        (ROUTE / "SPREAD_MODEL_VALIDATION_RESULT.json").write_text(json.dumps(
            {"schema": "spread_model_validation_v1",
             "generated_utc": datetime.now(timezone.utc).isoformat(),
             "n_variants": len(ERA_VARIANTS), "n_trials": len(ledger),
             "block_holdout": res, "winner_by_block_holdout": best,
             "gold_window_check": calibrate_gold(ERA_VARIANTS[best], a.tf),
             "gold_window_check_mean_above_floor":
                 calibrate_gold(ERA_VARIANTS["mean_above_floor"], a.tf),
             "price_proportionality": refute_price_proportional(bars, [])}, indent=1))
        with (ROUTE / "SPREAD_MODEL_TRIAL_LEDGER.jsonl").open("a") as fh:
            for row in ledger:
                fh.write(json.dumps(row) + "\n")
    elif a.cmd == "fit":
        model, ledger = fit(a.ref_a, a.ref_b, a.winner)
        Path(a.o).write_text(json.dumps(model, indent=1))
        with (ROUTE / "SPREAD_MODEL_TRIAL_LEDGER.jsonl").open("a") as fh:
            for row in ledger:
                fh.write(json.dumps(row) + "\n")
        n_sym = sum(len(v) for v in model["accounts"].values())
        n_era = sum(len(r["eras"]) for v in model["accounts"].values() for r in v.values())
        n_meas = sum(1 for v in model["accounts"].values() for r in v.values()
                     if r["anchor_coverage"] == "MEASURED")
        print(f"wrote {a.o}: {n_sym} symbols ({n_meas} tick-anchored, "
              f"{n_sym - n_meas} bar-anchored), {n_era} priced eras, "
              f"{len(ledger)} ledger rows")
    elif a.cmd == "entry-timing":
        entry_timing(Path(a.o))


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
