"""p2-40 — THE RESOLUTION LADDER. Is the take-profit finding an idea or an estimator?

WHY THIS EXISTS
---------------
`p2_30`'s side placebo came back at 89-180 % of the real effect: coin-flip the direction of every
emission, keep everything else, and deleting the take-profit is worth AS MUCH OR MORE than it is
on the family's own signal. A directional claim whose placebo reproduces it is not a directional
claim. Something in the measurement is generating it.

The suspect is the estimator's own time grid. `a15_final.py` -- and `p2_20` reproducing it --
steps the walk through hz in {1,2,4,8,16,32,64,96} M15 bars and, at each step, books the STOP if
the running low ever reached it, else the TARGET if the running high ever reached it. Between
hz=32 and hz=64 that is a **thirty-two bar** window inside which a path that touched the target
and then the stop is booked as a stop. Every such path is a loss for the take-profit arm and is
free for the no-target arm, which never had a target to miss. That is a bias in exactly the
measured direction and it is INDEPENDENT of the trade's side -- which is why the placebo has it.

So: hold the contract, the rows, the geometry, the spread and the estimator fixed, and vary ONLY
the resolution at which stop-versus-target order is resolved.

  COARSE   the geometric ladder {1,2,4,8,16,32,64,96} M15 bars  -- g3's grid, and p2_20's
  M15      every M15 bar, 1..96                                  -- 8x finer
  M1       every M1 minute, 1..1440                              -- 15x finer again, 120x COARSE

If the effect is economic it is a property of the contract and survives all three. If it is the
grid, it decays toward zero as the grid refines, and the side placebo decays with it.

The M1 tape is the same true-UTC hold the M15 tape comes from (`bridge_ftmo_m1_YYYYMM`), 24
symbols, 11 of the 12 months -- 2025-07 is absent from the M1 packs, so July emissions are
excluded FROM ALL THREE ARMS, not just from M1, or the comparison would be between populations.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from p2_20_walk import REGEN, boot, spread_series  # noqa: E402

M1ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
    "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars"
)
MONTHS = ["202506", "202508", "202509", "202510", "202511", "202512",
          "202601", "202602", "202603", "202604", "202605"]
COARSE = [1, 2, 4, 8, 16, 32, 64, 96]
TARGET_RR = 2.0
RNG = np.random.default_rng(909)


def load_m1(sym: str):
    ts, hi, lo, cl = [], [], [], []
    for m in MONTHS:
        p = M1ROOT / f"bridge_ftmo_m1_{m}" / f"{sym}_M1.csv"
        if not p.is_file():
            continue
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh):
                ts.append(r["time"])
                hi.append(float(r["high"]))
                lo.append(float(r["low"]))
                cl.append(float(r["close"]))
    if not ts:
        return None
    order = np.argsort(np.array(ts), kind="stable")
    ts = np.array(ts)[order]
    return ts, np.array(hi)[order], np.array(lo)[order], np.array(cl)[order]


def walk_steps(is_long, fill, stop_trig, exit_at_stop, tp_trig, tp_lvl, s_time_shift,
               hi, lo, cl, start, steps, use_target):
    """One walk over an explicit step list. `steps` are integer row offsets from `start`."""
    n = len(fill)
    done = np.zeros(n, dtype=bool)
    pnl = np.zeros(n, dtype=np.float64)
    kind = np.zeros(n, dtype=np.int8)
    sgn = np.where(is_long, 1.0, -1.0)
    cur_hi = np.full(n, -np.inf)
    cur_lo = np.full(n, np.inf)
    prev = 0
    last = start.copy()
    for k in steps:
        j = np.minimum(start + k, len(hi) - 1)
        # extend the running extremes over (prev, k]
        for q in range(prev + 1, k + 1):
            jq = np.minimum(start + q, len(hi) - 1)
            cur_hi = np.maximum(cur_hi, hi[jq])
            cur_lo = np.minimum(cur_lo, lo[jq])
        prev = k
        last = j
        hit_stop = np.where(is_long, cur_lo <= stop_trig, cur_hi >= stop_trig) & ~done
        pnl[hit_stop] = (sgn * (exit_at_stop - fill))[hit_stop]
        kind[hit_stop] = 1
        done |= hit_stop
        if use_target:
            hit_tp = np.where(is_long, cur_hi >= tp_trig, cur_lo <= tp_trig) & ~done
            pnl[hit_tp] = (sgn * (tp_lvl - fill))[hit_tp]
            kind[hit_tp] = 2
            done |= hit_tp
        if done.all():
            break
    pnl[~done] = (sgn * (cl[last] - fill) - s_time_shift)[~done]
    return pnl, kind


def geometry(sub, s, conv, flip_side=False):
    c = sub["bar_close"]
    ent = sub["entry"]
    stop_lvl = sub["stop"].copy()
    is_long = sub["side"] == "LONG"
    if flip_side:
        coin = RNG.random(len(c)) < 0.5
        is_long = np.where(coin, ~is_long, is_long)
        risk0 = np.abs(ent - sub["stop"])
        stop_lvl = np.where(is_long, ent - risk0, ent + risk0)
    sgn = np.where(is_long, 1.0, -1.0)
    if conv == "UNCORRECTED":
        fill = ent.copy()
        stop_trig = stop_lvl.copy()
        risk = np.abs(fill - stop_lvl)
        exit_at_stop = stop_lvl.copy()
        shift = np.zeros_like(c)
        tp_lvl = ent + sgn * TARGET_RR * risk
        tp_trig = tp_lvl.copy()
    else:  # LIVE
        fill = np.where(is_long, c + s, c)
        stop_trig = np.where(is_long, stop_lvl, stop_lvl - s)
        risk = np.abs(fill - stop_lvl)
        exit_at_stop = stop_lvl.copy()
        shift = s.copy()
        tp_lvl = fill + sgn * TARGET_RR * risk
        tp_trig = np.where(is_long, tp_lvl, tp_lvl - s)
    return is_long, fill, stop_trig, exit_at_stop, tp_trig, tp_lvl, shift, c


def main():
    out = {"schema": "gtos.p2.resolution_ladder.v1", "target_rr": TARGET_RR,
           "months_with_m1": MONTHS, "excluded": "2025-07 (absent from the M1 packs)",
           "families": {}}
    acc = {}
    for p in sorted(REGEN.glob("P2_EMIT_*.npz")):
        sym = p.name[len("P2_EMIT_"):-len(".npz")]
        z = dict(np.load(p, allow_pickle=False))
        m1 = load_m1(sym)
        if m1 is None:
            print("no M1", sym, file=sys.stderr)
            continue
        mt, mhi, mlo, mcl = m1
        # decision instant = M15 bar OPEN + 15 min  ==  the close of the decision bar
        want = np.array([
            (dt.datetime.fromisoformat(str(x)) + dt.timedelta(minutes=15)).isoformat()
            for x in z["t"]])
        pos = np.searchsorted(mt, want, side="left")
        ok = (pos < len(mt) - 1441) & (pos > 0) & (np.array(mt[np.minimum(pos, len(mt) - 1)]) == want)
        if not ok.any():
            print("no join", sym, file=sys.stderr)
            continue
        n0 = len(z["fam"])
        sub = {k: (v[ok] if isinstance(v, np.ndarray) and v.shape and v.shape[0] == n0 else v)
               for k, v in z.items()}
        start_m1 = pos[ok] - 1  # so offset q=1 is the first minute AFTER the decision close
        s = spread_series(sym, sub["t"])
        # M15 forward index for the M15/COARSE arms
        m15_start = sub["idx"]
        acc[sym] = dict(sub=sub, s=s, m1=(mhi, mlo, mcl), start_m1=start_m1,
                        m15_start=m15_start)
        print(f"{sym}: {ok.sum()}/{n0} emissions joined to M1", file=sys.stderr)

    # M15 arrays per symbol, reloaded once (needed for the M15/COARSE arms at full resolution)
    from p2_10_regen import TAPE
    m15 = {}
    for sym in acc:
        hi, lo, cl = [], [], []
        with open(TAPE / f"{sym}_M15.csv", newline="") as fh:
            for r in csv.DictReader(fh):
                hi.append(float(r["high"]))
                lo.append(float(r["low"]))
                cl.append(float(r["close"]))
        m15[sym] = (np.array(hi), np.array(lo), np.array(cl))

    fams = sorted({f for a in acc.values() for f in set(a["sub"]["fam"].tolist())})
    LADDER = [
        ("COARSE_M15", "m15", COARSE, 8, 96),
        ("EVERY_M15", "m15", None, 8, 96),
        ("EVERY_M1", "m1", None, 120, 1440),
    ]
    for fam in fams:
        fam_out = {}
        for name, tape, steps_spec, h2, h24 in LADDER:
            for hend, hlab in ((h2, "2h"), (h24, "24h")):
                for conv in ("UNCORRECTED", "LIVE"):
                    for placebo in (False, True):
                        ship_a, none_a, days_a, kn_a = [], [], [], []
                        for sym, a in acc.items():
                            m = a["sub"]["fam"] == fam
                            if not m.any():
                                continue
                            ssub = {k: (v[m] if isinstance(v, np.ndarray) and v.shape
                                        and v.shape[0] == len(a["sub"]["fam"]) else v)
                                    for k, v in a["sub"].items()}
                            sp = a["s"][m]
                            g = geometry(ssub, sp, conv, flip_side=placebo)
                            is_long, fill, st, eas, tpt, tpl, shift, c = g
                            if tape == "m1":
                                hi, lo, cl = a["m1"]
                                start = a["start_m1"][m]
                            else:
                                hi, lo, cl = m15[sym]
                                start = a["m15_start"][m]
                            steps = (steps_spec if steps_spec is not None
                                     else list(range(1, hend + 1)))
                            steps = [k for k in steps if k <= hend]
                            pa, ka = walk_steps(is_long, fill, st, eas, tpt, tpl, shift,
                                                hi, lo, cl, start, steps, True)
                            pb, kb = walk_steps(is_long, fill, st, eas, tpt, tpl, shift,
                                                hi, lo, cl, start, steps, False)
                            ship_a.append(pa / c * 1e4)
                            none_a.append(pb / c * 1e4)
                            kn_a.append(kb)
                            days_a.append(np.array([str(x)[:10] for x in ssub["t"]]))
                        if not ship_a:
                            continue
                        ship = np.concatenate(ship_a)
                        none = np.concatenate(none_a)
                        days = np.concatenate(days_a)
                        kn = np.concatenate(kn_a)
                        d = none - ship
                        m_, lo_, hi_, p_ = boot(d, days)
                        key = f"{name}|{hlab}|{conv}|{'PLACEBO' if placebo else 'REAL'}"
                        fam_out[key] = {
                            "n": int(len(d)), "delta_bps": m_, "ci95": [lo_, hi_],
                            "p_le_0": p_,
                            "shipped_bps": float(ship.mean()),
                            "no_target_bps": float(none.mean()),
                            "trunc_share_no_target": float((kn == 0).mean()),
                        }
                        print(f"  {fam:30s} {key:38s} {m_:+8.4f}", file=sys.stderr)
        out["families"][fam] = fam_out
    p = HERE / "P2_RESOLUTION_V1.json"
    p.write_text(json.dumps(out, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
