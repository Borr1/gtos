#!/usr/bin/env python3
"""F3 (6c) — the ex-ante levers, priced.

Every lever here is a function of information that exists BEFORE the candidate is
filled.  Each is selected on TRAIN (feb, apr, may) and priced on TEST (jun, jul)
only, with a day-block bootstrap because trades on one day are not independent.

A lever is reported as the change in mean net R of the SURVIVING book and the change
in total R, because a filter that improves the average by throwing away half the
book has to be judged on both.
"""
import gzip, json, pickle, sys
from pathlib import Path
import datetime as dt
import numpy as np

WT = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
sys.path.insert(0, str(WT))
from src.utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
CACHE = "/private/tmp/w21-puzzle-cache/rows_%s.pkl.gz"
OUT = Path(__file__).resolve().parent
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
R_USD = 250.0
TRAIN = ["feb", "apr", "may"]
TEST = ["jun", "jul"]


def boot_day_diff(net, day, keep, n=4000, seed=53):
    """Mean net R of the kept book minus mean net R of the whole book, day-blocked."""
    ud, inv = np.unique(day, return_inverse=True)
    idx = [np.nonzero(inv == i)[0] for i in range(len(ud))]
    rng = np.random.default_rng(seed)
    obs = net[keep].mean() - net.mean()
    mu = []
    for _ in range(n):
        p = rng.integers(0, len(ud), len(ud))
        ii = np.concatenate([idx[i] for i in p])
        k = keep[ii]
        if k.sum() < 30:
            continue
        mu.append(net[ii][k].mean() - net[ii].mean())
    mu = np.array(mu)
    return dict(delta_mean_net_R=float(obs),
                ci95_dayblock=[float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))],
                p_two_sided=float(2 * min((mu <= 0).mean(), (mu >= 0).mean())))


def main():
    trades = []
    for m in TRAIN + TEST:
        trades += pickle.load(gzip.open(TMP / f"f3_trades_{m}.pkl.gz", "rb"))
    feat = {}
    for m in TRAIN + TEST:
        for r in pickle.load(gzip.open(CACHE % m, "rb")):
            feat[r["candidate_occurrence_key"]] = r
    offc = {}

    def off(minute):
        d = int(minute) // 1440
        if d not in offc:
            offc[d] = offset_seconds_at_utc(EPOCH + dt.timedelta(minutes=d * 1440),
                                            NEW_YORK_PLUS_7) // 3600
        return offc[d]

    net = np.array([t["term_gross"] - t["ded"] for t in trades])
    day = np.array([t["day"] for t in trades])
    mon = np.array([t["month"] for t in trades])
    ot = np.array([t["ot"] for t in trades])
    fill = np.array([t["fill_min"] for t in trades])
    H1 = np.array([t["H1"] for t in trades])
    sub = np.array([t["sub"] for t in trades])
    roa = np.array([float(feat[t["k"]].get("risk_over_atr") or np.nan) for t in trades])
    bh = np.array([(int(f) + off(f) * 60) % 1440 // 60 for f in fill])
    # horizon spans broker midnight -- fully determined at submission
    spans = np.array([((int(f) + off(f) * 60) // 1440) !=
                      ((int(s) + int(h) + off(f) * 60) // 1440)
                      for f, s, h in zip(fill, sub, H1)])
    tr = np.isin(mon, TRAIN); te = np.isin(mon, TEST)

    out = {"schema": "gtos.f3.levers.v1", "R_usd": R_USD,
           "train": TRAIN, "test": TEST,
           "note": "every lever selected on TRAIN only; every number below is TEST",
           "test_book": dict(n=int(te.sum()), mean_net_R=float(net[te].mean()),
                             total_net_R=float(net[te].sum()),
                             total_net_usd=float(net[te].sum() * R_USD)),
           "levers": {}}

    def price(name, keep_all, knowable, detail=""):
        k = keep_all[te]
        if k.sum() < 200:
            return
        d = boot_day_diff(net[te], day[te], k)
        d.update(name=name, knowable_at_entry=knowable, detail=detail,
                 n_kept=int(k.sum()), n_dropped=int((~k).sum()),
                 share_dropped=float((~k).mean()),
                 kept_mean_net_R=float(net[te][k].mean()),
                 dropped_mean_net_R=float(net[te][~k].mean()) if (~k).sum() else None,
                 total_R_kept=float(net[te][k].sum()),
                 total_R_recovered=float(-net[te][~k].sum()),
                 total_usd_recovered=float(-net[te][~k].sum() * R_USD))
        out["levers"][name] = d

    price("L1_drop_horizon_spanning_broker_rollover", ~spans, True,
          "the 120-minute horizon is fixed at submission, so whether it crosses "
          "broker midnight is deterministic before the order exists")
    # L2: worst entry broker-hours chosen on TRAIN
    bad = [h for h in range(24)
           if (tr & (bh == h)).sum() > 300 and net[tr & (bh == h)].mean() < net[tr].mean() - 0.10]
    price("L2_drop_worst_entry_broker_hours_trainselected", ~np.isin(bh, bad), True,
          f"train-selected hours {sorted(bad)}")
    # L3: stop-width floor chosen on TRAIN (the real driver behind the obstacle proxy)
    fin = np.isfinite(roa)
    q = np.nanquantile(roa[tr & fin], 0.2)
    price("L3_drop_narrowest_stop_quintile_risk_over_atr", ~(fin & (roa < q)), True,
          f"train 20th percentile of risk_over_atr = {float(q):.4f}")
    price("L4_MARKET_orders_only", ot == "MARKET", True,
          "order type is a property of the candidate at generation")
    # combination of the two that are not the same lever
    price("L1+L3", (~spans) & ~(fin & (roa < q)), True, "rollover filter and stop-width floor")

    # what the NON-knowable causes would be worth if they could be acted on
    mfe = np.array([t["mfe"] for t in trades])
    gross = np.array([t["term_gross"] for t in trades])
    ded = np.array([t["ded"] for t in trades])
    bank = np.where(mfe >= 1.0, 1.0 - ded, gross - ded)
    out["exit_side_reference"] = dict(
        name="X1_close_at_+1R_whenever_touched",
        knowable_at_entry=False,
        note="an EXIT rule, not an entry filter: it cannot be known at entry which "
             "trades will reach +1 R.  Priced on TEST for scale only; the wick receipt "
             "(F3_WICK.json) decides whether it is collectable at all",
        test_delta_total_R=float(bank[te].sum() - net[te].sum()),
        test_delta_total_usd=float((bank[te].sum() - net[te].sum()) * R_USD),
        test_delta_mean_R=float(bank[te].mean() - net[te].mean()))
    (OUT / "F3_LEVERS.json").write_text(json.dumps(out, indent=1))
    for k, v in out["levers"].items():
        print(f"{k:52s} drop={v['share_dropped']:.3f} dmean={v['delta_mean_net_R']:+.4f} "
              f"ci=[{v['ci95_dayblock'][0]:+.4f},{v['ci95_dayblock'][1]:+.4f}] "
              f"p={v['p_two_sided']:.3f} recov=${v['total_usd_recovered']:,.0f}")
    print(json.dumps(out["exit_side_reference"], indent=1))


if __name__ == "__main__":
    main()
