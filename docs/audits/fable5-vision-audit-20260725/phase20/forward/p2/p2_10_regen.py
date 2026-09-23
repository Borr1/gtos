"""p2-10 — regenerate the broad-origin at-market families by CALLING THE PRODUCTION GENERATOR.

Why this and not a re-derivation. g3's `a8_regen.py` re-implemented the arithmetic of three
families by hand. That is fine for a stop decomposition and it is not fine for a repair: the
whole point of p2 is to change `broader_origin_generators.py`, so the measurement has to ride
the same code the repair lands in, or the A/B measures my transcription rather than the estate's
contract.

So this drives `_generate_single_symbol_candidates` — the real function, unmodified — over every
closed M15 bar of the true-UTC tape (24 symbols, 2025-06-01..2026-06-10), with the mined family
enabled so `range_extreme_reversion` is visible, and records the emitted geometry verbatim
(entry, stop, tp1, rr) plus the forward path.

CONTROL: family counts for the three families g3 covered must reproduce
`g3_receipts/G3_REGEN_SUMMARY_V1.json` -> `families`. Two different implementations, same tape,
same answer, or something is wrong with one of them.

Output: P2_EMIT_<SYMBOL>.npz per symbol, then P2_REGEN_V1.npz pooled.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.components.broader_origin_generators import (  # noqa: E402
    Bar,
    BarSeries,
    SESSION_WINDOWS,
    _canonical_symbol,
    _generate_single_symbol_candidates,
)

TAPE = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
    "bridge_ftmo_m15_20250601_20260610"
)
SYMS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY", "EURUSD",
    "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD", "SPX500", "UK100",
    "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash", "XAGUSD", "XAUUSD",
]
HZ = [1, 2, 4, 8, 16, 32, 64, 96]  # M15 bars forward: 15 min .. 24 h
OUT = Path(__file__).resolve().parent / "regen"

#: The three POI families rest PENDING orders at absolute structural levels; the rest are
#: at-market on the decision bar's close. Only the at-market class is measured here, because the
#: quote-side correction for a resting limit needs the fill bar, which this walk does not model.
POI_FAMILIES = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}

TARGET_RR = 2.0  # the sealed pool's value (pbg_run.py:89-90); mainline min_rr is 1.5


def load(sym: str):
    p = TAPE / f"{sym}_M15.csv"
    if not p.is_file():
        return None
    t, o, h, lo, c, v = [], [], [], [], [], []
    with open(p, newline="") as fh:
        for r in csv.DictReader(fh):
            t.append(r["time"])
            o.append(float(r["open"]))
            h.append(float(r["high"]))
            lo.append(float(r["low"]))
            c.append(float(r["close"]))
            v.append(float(r.get("volume") or 0.0))
    return t, np.array(o), np.array(h), np.array(lo), np.array(c), np.array(v)


def main(argv):
    only = argv[1:] if len(argv) > 1 else SYMS
    OUT.mkdir(parents=True, exist_ok=True)
    for sym in only:
        dst = OUT / f"P2_EMIT_{sym}.npz"
        if dst.is_file():
            print("skip", sym, file=sys.stderr)
            continue
        loaded = load(sym)
        if loaded is None:
            print("MISSING", sym, file=sys.stderr)
            continue
        t, o, h, lo, c, v = loaded
        n = len(c)
        times = [datetime.fromisoformat(x).astimezone(timezone.utc) for x in t]
        bars = tuple(
            Bar(time=times[i], open=float(o[i]), high=float(h[i]), low=float(lo[i]),
                close=float(c[i]), volume=float(v[i]))
            for i in range(n)
        )
        series = BarSeries(
            symbol=sym,
            timeframe="M15",
            bars=bars,
            source_path_feature_status="complete",
            session_windows=SESSION_WINDOWS.get(_canonical_symbol(sym), ()),
        )
        # forward running extremes, vectorised once per symbol
        fmax = {}
        fmin = {}
        for hz in HZ:
            mx = np.full(n, np.nan)
            mn = np.full(n, np.nan)
            for i in range(n):
                j = min(i + hz, n - 1)
                if j > i:
                    mx[i] = h[i + 1:j + 1].max()
                    mn[i] = lo[i + 1:j + 1].min()
                else:
                    mx[i] = c[i]
                    mn[i] = c[i]
            fmax[hz] = mx
            fmin[hz] = mn
        cls = {hz: c[np.minimum(np.arange(n) + hz, n - 1)] for hz in HZ}

        rows = []
        t0 = time.time()
        for i in range(51, n):
            cands = _generate_single_symbol_candidates(
                series=series, index=i, target_rr=TARGET_RR, kill_zone="none",
                enable_mined_families=True, enable_microstructure=False,
            )
            for cd in cands:
                if cd.origin_family in POI_FAMILIES:
                    continue
                rows.append((i, cd.origin_family, cd.direction, cd.entry_price,
                             cd.stop_loss, cd.take_profit_1, cd.route_session))
        print(f"{sym}: {n} bars, {len(rows)} at-market emissions, {time.time()-t0:.1f}s",
              file=sys.stderr)
        if not rows:
            continue
        idx = np.array([r[0] for r in rows], dtype=np.int32)
        fam = np.array([r[1] for r in rows])
        side = np.array([r[2] for r in rows])
        ent = np.array([r[3] for r in rows], dtype=np.float64)
        stp = np.array([r[4] for r in rows], dtype=np.float64)
        tp1 = np.array([r[5] for r in rows], dtype=np.float64)
        rses = np.array([r[6] for r in rows])
        payload = dict(
            idx=idx, fam=fam, side=side, entry=ent, stop=stp, tp1=tp1, route_session=rses,
            t=np.array([t[i] for i in idx]),
            bar_close=c[idx], bar_high=h[idx], bar_low=lo[idx],
        )
        for hz in HZ:
            payload[f"fmax{hz}"] = fmax[hz][idx]
            payload[f"fmin{hz}"] = fmin[hz][idx]
            payload[f"cls{hz}"] = cls[hz][idx]
        np.savez_compressed(dst, **payload)
    print("DONE")


if __name__ == "__main__":
    main(sys.argv)
