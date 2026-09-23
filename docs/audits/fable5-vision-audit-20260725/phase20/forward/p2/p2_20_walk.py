"""p2-20 — walk every at-market broad-origin emission on the REPAIRED quote-side convention.

THE THREE CONVENTIONS, and why all three are published
------------------------------------------------------
`UNCORRECTED`  spread = 0. Entry at the tape close, both exit legs resolved against the tape
               with unshifted levels. This is what every walker in this estate did before
               `029b2fc1c`, and it is what g3 measured. Kept as the control arm so the
               reproduction of g3 is exact and the correction's size is visible.

`LIVE`         what `orchestrator.py:5075-5124` + `execution.py:3247`/`:6953` actually do to a
               broader-origin candidate, on a BID tape:
                 LONG   fills at the ASK (c + s); the generator's ABSOLUTE stop level is
                        unchanged and resolves against the BID unshifted; risk is measured
                        from the FILL (`:5107` `sl_distance = abs(entry - stop)` after the
                        entry was replaced by the live price at `:5049`); the target is
                        recomputed as `entry + final_target_r * sl_distance` (`:5111-5113`)
                        and resolves against the BID.
                 SHORT  fills at the BID (c, exact); both exit legs transact on the ASK, so
                        each triggers when the BID is one spread lower than the level.
               This is the asymmetry a bid archive imposes and it is not a modelling choice.

`FILL_SYM`     r1's canonical fill anchor, `anchor = c + direction * s`, stop at -1R and target
               at +rr*R from the anchor (`quote_side.replay_anchor`). Published as a
               sensitivity: it is the convention the armed W7 book runs and it is symmetric
               between the sides, so if the p2 verdict were an artifact of the LIVE model's
               long/short asymmetry it would show up here.

THE QUESTION
------------
For each convention, walk two contracts on the IDENTICAL rows:
    shipped   stop + `target_rr` take-profit
    no-target stop only
and report `no-target - shipped`, trade-weighted, with a day-block bootstrap CI95, plus the
per-arm truncation share (the fraction that exits on time rather than at a level), because a
"let the winners run" result that is really a maxbars artifact is the failure mode this whole
family of claims dies of.

Estimator is `a15_final.py`'s, deliberately: trade-weighted mean, 2000-rep day-block bootstrap.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from src.research_infra.walkforward.quote_side import spread_for  # noqa: E402

HERE = Path(__file__).resolve().parent
REGEN = HERE / "regen"
HZ = [1, 2, 4, 8, 16, 32, 64, 96]
TOLL_BPS = 3.02  # the round-trip toll g3 priced against (spread+commission+slippage)
RNG = np.random.default_rng(20260807)


def spread_series(sym: str, times: np.ndarray) -> np.ndarray:
    """One spread per emission. The model is era-aware and intraweek-aware, so it is queried
    per MONTH (its own resolution for the era ratio) and per weekday-hour bucket, not once."""
    key = {}
    out = np.empty(len(times), dtype=np.float64)
    for k, tstr in enumerate(times):
        t = dt.datetime.fromisoformat(str(tstr))
        bucket = (t.year, t.month, t.weekday(), t.hour)
        if bucket not in key:
            key[bucket] = spread_for(sym, t.astimezone(dt.timezone.utc))
        out[k] = key[bucket]
    return out


def walk_arm(z, s, conv: str, hend: int, target_rr: float | None):
    """Return (pnl_bps, exit_kind) for every row. `target_rr=None` deletes the take-profit."""
    c = z["bar_close"]
    ent_gen = z["entry"]          # the generator's emitted entry == the decision bar close
    stop_lvl = z["stop"]          # absolute structural level
    is_long = z["side"] == "LONG"
    sgn = np.where(is_long, 1.0, -1.0)

    if conv == "UNCORRECTED":
        fill = ent_gen.copy()
        stop_trig = stop_lvl.copy()
        risk = np.abs(fill - stop_lvl)
        exit_at_stop = stop_lvl.copy()
        time_exit_shift = np.zeros_like(c)
    elif conv == "LIVE":
        fill = np.where(is_long, c + s, c)
        # tape trigger for the stop: LONG on the bid (unshifted), SHORT on the ask (bid one
        # spread lower)
        stop_trig = np.where(is_long, stop_lvl, stop_lvl - s)
        risk = np.abs(fill - stop_lvl)
        exit_at_stop = stop_lvl.copy()
        time_exit_shift = s.copy()
    elif conv == "FILL_SYM":
        anchor = c + sgn * s
        fill = anchor.copy()
        risk = np.abs(ent_gen - stop_lvl)          # the declared R unit
        stop_trig = anchor - sgn * risk
        exit_at_stop = stop_trig.copy()
        time_exit_shift = np.zeros_like(c)
    else:
        raise ValueError(conv)

    if target_rr is None:
        tp_lvl = None
        tp_trig = None
    else:
        if conv == "UNCORRECTED":
            tp_lvl = ent_gen + sgn * target_rr * risk
            tp_trig = tp_lvl.copy()
        elif conv == "LIVE":
            tp_lvl = fill + sgn * target_rr * risk
            tp_trig = np.where(is_long, tp_lvl, tp_lvl - s)
        else:
            tp_lvl = fill + sgn * target_rr * risk
            tp_trig = tp_lvl.copy()

    n = len(c)
    done = np.zeros(n, dtype=bool)
    pnl = np.zeros(n, dtype=np.float64)
    kind = np.zeros(n, dtype=np.int8)  # 0 time, 1 stop, 2 target

    for hz in HZ:
        if hz > hend:
            break
        fmax = z[f"fmax{hz}"]
        fmin = z[f"fmin{hz}"]
        hit_stop = np.where(is_long, fmin <= stop_trig, fmax >= stop_trig) & ~done
        pnl[hit_stop] = (sgn * (exit_at_stop - fill))[hit_stop]
        kind[hit_stop] = 1
        done |= hit_stop
        if tp_trig is not None:
            hit_tp = np.where(is_long, fmax >= tp_trig, fmin <= tp_trig) & ~done
            pnl[hit_tp] = (sgn * (tp_lvl - fill))[hit_tp]
            kind[hit_tp] = 2
            done |= hit_tp

    cls = z[f"cls{hend}"]
    pnl[~done] = (sgn * (cls - fill) - time_exit_shift)[~done]
    return pnl / c * 1e4, kind, risk / c * 1e4


def boot(vals, days, B=2000):
    v = np.asarray(vals, dtype=np.float64)
    dl = np.asarray(days)
    uk, inv = np.unique(dl, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    inv_s = inv[order]
    v_s = v[order]
    starts = np.searchsorted(inv_s, np.arange(len(uk)))
    ends = np.searchsorted(inv_s, np.arange(len(uk)), side="right")
    buckets = [v_s[a:b] for a, b in zip(starts, ends)]
    nb = len(uk)
    out = np.empty(B)
    sums = np.array([b.sum() for b in buckets])
    cnts = np.array([len(b) for b in buckets], dtype=np.float64)
    for i in range(B):
        pick = RNG.integers(0, nb, nb)
        out[i] = sums[pick].sum() / cnts[pick].sum()
    return (float(v.mean()), float(np.percentile(out, 2.5)),
            float(np.percentile(out, 97.5)), float((out <= 0).mean()))


def main():
    target_rr = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    packs = []
    for p in sorted(REGEN.glob("P2_EMIT_*.npz")):
        sym = p.name[len("P2_EMIT_"):-len(".npz")]
        z = dict(np.load(p, allow_pickle=False))
        z["_sym"] = sym
        z["_spread"] = spread_series(sym, z["t"])
        packs.append(z)
        print("loaded", sym, len(z["fam"]), file=sys.stderr)

    fams = sorted({f for z in packs for f in set(z["fam"].tolist())})
    result = {
        "schema": "gtos.p2.target_deletion.v1",
        "target_rr": target_rr,
        "toll_bps": TOLL_BPS,
        "conventions": ["UNCORRECTED", "LIVE", "FILL_SYM"],
        "families": {},
    }

    for fam in fams:
        rows = {}
        for z in packs:
            m = z["fam"] == fam
            if not m.any():
                continue
            sub = {k: (v[m] if isinstance(v, np.ndarray) and v.shape and v.shape[0] == len(z["fam"]) else v)
                   for k, v in z.items() if not k.startswith("_")}
            sub["_spread"] = z["_spread"][m]
            rows[z["_sym"]] = sub
        if not rows:
            continue
        fam_out = {}
        for hend, hlab in ((8, "2h"), (96, "24h")):
            per_h = {}
            for conv in ("UNCORRECTED", "LIVE", "FILL_SYM"):
                ship_all, none_all, days_all = [], [], []
                k_ship, k_none = [], []
                risk_all = []
                for sym, sub in rows.items():
                    s = sub["_spread"]
                    a, ka, rk = walk_arm(sub, s, conv, hend, target_rr)
                    b, kb, _ = walk_arm(sub, s, conv, hend, None)
                    ship_all.append(a)
                    none_all.append(b)
                    k_ship.append(ka)
                    k_none.append(kb)
                    risk_all.append(rk)
                    days_all.append(np.array([str(x)[:10] for x in sub["t"]]))
                ship = np.concatenate(ship_all)
                none = np.concatenate(none_all)
                days = np.concatenate(days_all)
                ks = np.concatenate(k_ship)
                kn = np.concatenate(k_none)
                risk = np.concatenate(risk_all)
                delta = none - ship
                ms, los, his, ps = boot(ship, days)
                mn, lon, hin, pn = boot(none, days)
                md, lod, hid, pd = boot(delta, days)
                per_h[conv] = {
                    "n": int(len(ship)),
                    "median_risk_bps": float(np.median(risk)),
                    "shipped": {"mean_bps": ms, "ci95": [los, his], "p_le_0": ps,
                                "exit_mix": {"time": float((ks == 0).mean()),
                                             "stop": float((ks == 1).mean()),
                                             "target": float((ks == 2).mean())}},
                    "no_target": {"mean_bps": mn, "ci95": [lon, hin], "p_le_0": pn,
                                  "exit_mix": {"time": float((kn == 0).mean()),
                                               "stop": float((kn == 1).mean())}},
                    "delta_no_target_minus_shipped": {
                        "mean_bps": md, "ci95": [lod, hid], "p_le_0": pd},
                    "vs_toll_no_target": mn - TOLL_BPS,
                }
            fam_out[hlab] = per_h
        result["families"][fam] = fam_out
        print("done", fam, file=sys.stderr)

    out = HERE / "P2_TARGET_DELETION_V1.json"
    out.write_text(json.dumps(result, indent=1))
    print("WROTE", out)


if __name__ == "__main__":
    main()
