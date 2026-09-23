#!/usr/bin/env python3
"""F4 — the blind-entry control, done adversarially.

Question: does the generator's CHOICE OF MOMENT put the trade in a better place
than a coin flip would? If not, no ranking layer can rescue the pool, because
there is nothing in it to rank.

Two corrections over the naive comparison, both of which cut AGAINST the
finding and are applied anyway:

  1. SPREAD. The real trade's MFE is measured from a quote-adjusted fill; the
     blind arm's from a raw bar open. The blind arm is therefore handed a free
     half-spread. Corrected by charging the blind arm the candidate's OWN
     spread_r.
  2. FILL CONDITIONING. A filled LIMIT is a trade the market came back to,
     which is a selection the blind arm does not undergo. The headline is
     therefore MARKET-ONLY, where fill is unconditional (0 NO_FILL rows).

Matched on symbol, side, month, hour-of-day, horizon length and risk.
3 independent draws per trade, seed 20260812. Paired cluster bootstrap by day.

Read-only.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from f4_common import MONTHS, enrich, jdump, load_month  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "receipts"
WALK = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
BARS = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
MONTH_SRC = {"feb": "202602", "apr": "202604", "may": "202605",
             "jun": "202606", "jul": "202607"}
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
KS = [0.5, 1.0, 1.5, 2.0]
SEED = 20260812
NDRAW = 3


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def load_m1(month):
    out = {}
    d = BARS / f"bridge_ftmo_m1_{MONTH_SRC[month]}"
    for p in sorted(d.glob("*_M1.csv")):
        sym = p.name[:-7]
        rows = []
        with p.open(newline="") as fh:
            for row in csv.DictReader(fh):
                rows.append((row["time"], row["open"], row["high"], row["low"]))
        rows = sorted(set(rows), key=lambda r: r[0])
        t = np.array([mins(at(r[0])) for r in rows], dtype=np.int64)
        keep = np.concatenate([[True], np.diff(t) > 0])
        t = t[keep]
        rows = [r for r, k in zip(rows, keep) if k]
        o = np.array([float(r[1]) for r in rows])
        h = np.array([float(r[2]) for r in rows])
        lo = np.array([float(r[3]) for r in rows])
        out[sym] = dict(t=t, o=o, h=h, l=lo, hod=((t // 60) % 24).astype(np.int64),
                        cmaxh=None, cminl=None)
    return out


def main():
    rows = []
    for m in MONTHS:
        rows += enrich(load_month(m))
    with gzip.open(HERE / "f4_excursion_join.pkl.gz", "rb") as f:
        exc = {r["candidate_occurrence_key"]: r["mfe"] for r in pickle.load(f)}
    fil = []
    for r in rows:
        if r["candidate_occurrence_key"] in exc:
            r["mfe"] = exc[r["candidate_occurrence_key"]]
            fil.append(r)

    rng = np.random.default_rng(SEED)
    recs = []
    for m in MONTHS:
        S = load_m1(m)
        risk_of = {}
        with gzip.open(WALK / f"walk_{m}.pkl.gz", "rb") as f:
            for r in pickle.load(f):
                if r.get("risk"):
                    risk_of[r["k"]] = float(r["risk"])
        sub = [r for r in fil if r["month"] == m]
        by_sym = defaultdict(list)
        for r in sub:
            by_sym[r["symbol"]].append(r)
        for sym, rs in by_sym.items():
            s = S.get(sym)
            if s is None:
                continue
            n = len(s["t"])
            hod_idx = {h: np.nonzero(s["hod"] == h)[0] for h in range(24)}
            for r in rs:
                risk = risk_of.get(r["candidate_occurrence_key"])
                if not risk or risk <= 0:
                    continue
                t0 = mins(at(r["label_span_start_utc"]))
                span = mins(at(r["label_span_end_utc"])) - t0
                if span <= 0:
                    continue
                d = 1.0 if r["side"] == "LONG" else -1.0
                pool = hod_idx[(t0 // 60) % 24]
                pool = pool[pool < n - span]
                if len(pool) < 10:
                    continue
                spr = float(r.get("spread_r") or 0.0)
                draws = []
                for j in rng.choice(pool, size=min(NDRAW, len(pool)), replace=False):
                    j = int(j)
                    hi = min(n, j + span)
                    fp = s["o"][j]
                    fav = (s["h"][j:hi].max() - fp) if d > 0 else (fp - s["l"][j:hi].min())
                    draws.append(fav / risk - spr)      # charge the blind arm the spread
                recs.append({"key": r["candidate_occurrence_key"], "day": r["trading_day"],
                             "symbol": sym, "family": r["origin_family"],
                             "ot": r["proposed_order_type"], "month": m,
                             "real": r["mfe"], "blind": float(np.mean(draws)),
                             "blind_draws": draws})
        print(f"blind {m}: cum {len(recs)}", flush=True)

    def summarise(rs, label):
        if not rs:
            return {}
        real = np.array([x["real"] for x in rs])
        bl = np.concatenate([np.array(x["blind_draws"]) for x in rs])
        out = {"label": label, "n_real": int(len(real)), "n_blind_draws": int(len(bl)),
               "real_mfe_mean": float(real.mean()), "blind_mfe_mean": float(bl.mean()),
               "real_frac_ge": {str(k): float((real >= k).mean()) for k in KS},
               "blind_frac_ge": {str(k): float((bl >= k).mean()) for k in KS}}
        out["lift"] = {k: out["real_frac_ge"][k] - out["blind_frac_ge"][k] for k in out["real_frac_ge"]}
        # paired cluster bootstrap by trading day on P(MFE>=2R)
        days = defaultdict(list)
        for x in rs:
            days[x["day"]].append(x)
        dk = list(days)
        bs = []
        rg = np.random.default_rng(SEED)
        for _ in range(2000):
            pick = rg.choice(len(dk), size=len(dk), replace=True)
            rr, bb = [], []
            for i in pick:
                for x in days[dk[i]]:
                    rr.append(x["real"] >= 2.0)
                    bb += [v >= 2.0 for v in x["blind_draws"]]
            bs.append(np.mean(rr) - np.mean(bb))
        bs = np.array(bs)
        out["lift_at_2R_bootstrap"] = {
            "point": out["lift"]["2.0"], "ci95_lo": float(np.quantile(bs, 0.025)),
            "ci95_hi": float(np.quantile(bs, 0.975)),
            "p_lift_gt_0": float((bs > 0).mean()), "n_days": len(dk), "draws": 2000}
        return out

    res = {"prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
           "seed": SEED, "n_draws_per_trade": NDRAW,
           "matching": "symbol + side + month + hour-of-day + horizon length + risk",
           "spread_correction": "blind arm charged the candidate's own spread_r",
           "HEADLINE_market_only": summarise([x for x in recs if x["ot"] == "MARKET"], "MARKET"),
           "all_filled": summarise(recs, "ALL_FILLED"),
           "limit_only_fill_conditioned": summarise([x for x in recs if x["ot"] == "LIMIT"], "LIMIT")}
    perfam, permon = {}, {}
    for fam in sorted({x["family"] for x in recs}):
        sub = [x for x in recs if x["family"] == fam and x["ot"] == "MARKET"]
        if len(sub) >= 500:
            s = summarise(sub, fam)
            perfam[fam] = {"n": s["n_real"], "real_2R": s["real_frac_ge"]["2.0"],
                           "blind_2R": s["blind_frac_ge"]["2.0"], "lift": s["lift"]["2.0"]}
    for m in MONTHS:
        sub = [x for x in recs if x["month"] == m and x["ot"] == "MARKET"]
        if sub:
            s = summarise(sub, m)
            permon[m] = {"n": s["n_real"], "lift_2R": s["lift"]["2.0"]}
    res["per_family_market_only"] = perfam
    res["per_month_market_only"] = permon
    jdump(res, OUT / "F4_BLIND_CONTROL_V1.json")

    h = res["HEADLINE_market_only"]
    print("\n=== BLIND CONTROL, MARKET ONLY, SPREAD-MATCHED ===")
    print("  real  P(MFE>=k):", h["real_frac_ge"])
    print("  blind P(MFE>=k):", h["blind_frac_ge"])
    print("  lift            :", h["lift"])
    print("  lift@2R bootstrap:", h["lift_at_2R_bootstrap"])
    print("\n  per family (MARKET):")
    for k, v in sorted(perfam.items(), key=lambda kv: -kv[1]["lift"]):
        print(f"    {k:34s} n={v['n']:6d} real={v['real_2R']:.4f} blind={v['blind_2R']:.4f} lift={v['lift']:+.4f}")
    print("  per month:", permon)


if __name__ == "__main__":
    main()
