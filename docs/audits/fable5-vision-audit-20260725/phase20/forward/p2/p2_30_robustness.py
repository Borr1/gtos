"""p2-30 — kill the target-deletion result the way the estate's three dead headlines were killed.

Three headlines died in one week from the same shape as this one ("remove the cap and the winners
run"): a trailing stop that booked prices that never printed, a cell selection that was really the
fee schedule, and a forming-bar rule whose loss was booked before its information arrived. So this
lane's own result gets the same three instruments turned on it.

T1  OUT OF SAMPLE. Split the tape in half by calendar. The delta is estimated on the first half
    and re-estimated on the second, which was never looked at while the first was read. A
    contract change that is real is a property of the geometry and must survive; one that is a
    peak in a search does not.

T2  PLACEBO ON SIDE. Re-walk EVERY emission with a coin-flipped direction (seeded), keeping the
    symbol, the instant, the stop distance and the target multiple. The families' directional
    claim is destroyed and nothing else is. Under a correct walker the target-deletion delta on
    a sideless population must be ~0: a cap on a driftless path is worth nothing either way.
    **A non-zero placebo delta is a property of the WALKER, not of the idea** -- which is exactly
    what the pre-repair convention has, and it is the reason this test is the load-bearing one.

T3  PLACEBO ON TIME. Keep the side and the geometry, move the entry instant to a uniformly random
    OTHER bar of the same symbol-day. Destroys the setup, keeps the symbol, the day, the session
    and the volatility regime.

T4  TRUNCATION SHARE, published per arm and per horizon, because a "let it run" gain that is
    really "hold to the 24 h close" is a horizon claim wearing a geometry claim's clothes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from p2_20_walk import HZ, REGEN, boot, spread_series, walk_arm  # noqa: E402

SPLIT = "2025-12-06"  # the calendar midpoint of 2025-06-01..2026-06-10
TARGET_RR = 2.0
RNG = np.random.default_rng(4242)


def qtr(tstr: str) -> str:
    y, m = int(tstr[:4]), int(tstr[5:7])
    return f"{y}Q{(m - 1) // 3 + 1}"


def load_packs():
    packs = []
    for p in sorted(REGEN.glob("P2_EMIT_*.npz")):
        sym = p.name[len("P2_EMIT_"):-len(".npz")]
        z = dict(np.load(p, allow_pickle=False))
        z["_sym"] = sym
        z["_spread"] = spread_series(sym, z["t"])
        packs.append(z)
        print("loaded", sym, file=sys.stderr)
    return packs


def subset(z, mask):
    n = len(z["fam"])
    out = {}
    for k, v in z.items():
        if isinstance(v, np.ndarray) and v.shape and v.shape[0] == n:
            out[k] = v[mask]
        elif not k.startswith("_"):
            out[k] = v
    out["_spread"] = z["_spread"][mask]
    out["_sym"] = z["_sym"]
    return out


def measure(rows, conv, hend, target_rr):
    ship, none, days, ks, kn, qs = [], [], [], [], [], []
    for sub in rows:
        s = sub["_spread"]
        a, ka, _ = walk_arm(sub, s, conv, hend, target_rr)
        b, kb, _ = walk_arm(sub, s, conv, hend, None)
        ship.append(a)
        none.append(b)
        ks.append(ka)
        kn.append(kb)
        days.append(np.array([str(x)[:10] for x in sub["t"]]))
        qs.append(np.array([qtr(str(x)) for x in sub["t"]]))
    ship = np.concatenate(ship)
    none = np.concatenate(none)
    days = np.concatenate(days)
    qs = np.concatenate(qs)
    ks = np.concatenate(ks)
    kn = np.concatenate(kn)
    d = none - ship
    m, lo, hi, p = boot(d, days)
    qpos = 0
    qn = 0
    for q in np.unique(qs):
        qn += 1
        if d[qs == q].mean() > 0:
            qpos += 1
    return {
        "n": int(len(d)),
        "delta_bps": m, "ci95": [lo, hi], "p_le_0": p,
        "quarters_positive": f"{qpos}/{qn}",
        "shipped_bps": float(ship.mean()), "no_target_bps": float(none.mean()),
        "trunc_share_shipped": float((ks == 0).mean()),
        "trunc_share_no_target": float((kn == 0).mean()),
        "target_hit_share_shipped": float((ks == 2).mean()),
    }


def flip_sides(sub, rng):
    """T2: coin-flip the direction, rebuild the stop level at the SAME distance on the new side."""
    out = dict(sub)
    n = len(sub["fam"])
    coin = rng.random(n) < 0.5
    was_long = sub["side"] == "LONG"
    new_long = np.where(coin, ~was_long, was_long)
    risk = np.abs(sub["entry"] - sub["stop"])
    out["side"] = np.where(new_long, "LONG", "SHORT")
    out["stop"] = np.where(new_long, sub["entry"] - risk, sub["entry"] + risk)
    out["tp1"] = np.where(new_long, sub["entry"] + TARGET_RR * risk,
                          sub["entry"] - TARGET_RR * risk)
    return out


def shift_times(sub, rng):
    """T3: move each emission to a uniformly random OTHER row of the same symbol-day.

    Implemented as a within-day permutation of the FORWARD path arrays: the geometry (entry,
    stop, side) stays with its own bar and the future it is judged against comes from another
    bar of the same day. That keeps the stop-to-volatility ratio and the session and destroys
    the setup's claim about what happens next.
    """
    out = dict(sub)
    days = np.array([str(x)[:10] for x in sub["t"]])
    order = np.arange(len(days))
    for d in np.unique(days):
        idx = np.nonzero(days == d)[0]
        if len(idx) < 2:
            continue
        perm = rng.permutation(idx)
        # forbid a fixed point where possible
        for k in range(len(idx)):
            if perm[k] == idx[k] and len(idx) > 1:
                j = (k + 1) % len(idx)
                perm[k], perm[j] = perm[j], perm[k]
        order[idx] = perm
    # the forward path moves; entry/stop/side/close stay
    for hz in HZ:
        for pre in ("fmax", "fmin", "cls"):
            key = f"{pre}{hz}"
            # rebase the borrowed path onto THIS row's entry, so the geometry is comparable:
            # scale the donor's excursion ratio onto the receiver's price level
            donor = sub[key][order]
            out[key] = sub["bar_close"] * (donor / sub["bar_close"][order])
    return out


def main():
    packs = load_packs()
    fams = sorted({f for z in packs for f in set(z["fam"].tolist())})
    res = {"schema": "gtos.p2.robustness.v1", "split_date": SPLIT, "target_rr": TARGET_RR,
           "families": {}}
    for fam in fams:
        fam_rows = [subset(z, z["fam"] == fam) for z in packs
                    if (z["fam"] == fam).any()]
        entry = {}
        for hend, hlab in ((8, "2h"), (96, "24h")):
            per = {}
            for conv in ("UNCORRECTED", "LIVE"):
                tr = [subset(r, np.array([str(x)[:10] for x in r["t"]]) < SPLIT) for r in fam_rows]
                te = [subset(r, np.array([str(x)[:10] for x in r["t"]]) >= SPLIT) for r in fam_rows]
                tr = [r for r in tr if len(r["fam"])]
                te = [r for r in te if len(r["fam"])]
                pl_side = [flip_sides(r, np.random.default_rng(11)) for r in fam_rows]
                pl_time = [shift_times(r, np.random.default_rng(13)) for r in fam_rows]
                per[conv] = {
                    "full": measure(fam_rows, conv, hend, TARGET_RR),
                    "T1_train_first_half": measure(tr, conv, hend, TARGET_RR) if tr else None,
                    "T1_test_second_half": measure(te, conv, hend, TARGET_RR) if te else None,
                    "T2_placebo_random_side": measure(pl_side, conv, hend, TARGET_RR),
                    "T3_placebo_shifted_time": measure(pl_time, conv, hend, TARGET_RR),
                }
            entry[hlab] = per
        res["families"][fam] = entry
        print("done", fam, file=sys.stderr)
    p = HERE / "P2_ROBUSTNESS_V1.json"
    p.write_text(json.dumps(res, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
