#!/usr/bin/env python3
"""F4 task 4 — the ceiling, and the control that says whether generation works.

Two things:

1. THE CEILING TABLE. Because MFE is the maximum favourable excursion reached
   BEFORE the trade terminated, "MFE >= k" is exactly "this trade would have hit
   a target at +kR before its stop". So for any k <= the shipped target the
   outcome under a k-target contract is an EXACT re-simulation:
       R(k) = +k                if MFE >= k
            = terminal_gross_r  otherwise
   Reported for a perfect oracle, a rank oracle at a fixed take-fraction, the
   best model, and the shipped rule.

2. THE BLIND-ENTRY CONTROL. The magnitude program established that blind entry
   on this surface is a fair game gross. If the candidate pool's excursion
   distribution matches a matched blind control, then generation is contributing
   nothing and no amount of ranking can help. Matched on symbol, side, month and
   risk; entry minute drawn uniformly from that symbol's own M1 bars (arm U) and
   from the same hour of day (arm H).

Read-only. Writes receipts.
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
from f4_common import MONTHS, dollars, enrich, jdump, load_month  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "receipts"
WALK = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/lane2")
LANE = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
            "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1")
BARS = LANE / "sources/bars"
MONTH_SRC = {"feb": ["202602"], "apr": ["202604"], "may": ["202605"],
             "jun": ["202606"], "jul": ["202607"]}
EPOCH = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
KS = [0.5, 1.0, 1.5, 2.0]
SEED = 20260812


def mins(t):
    return int((t - EPOCH).total_seconds() // 60)


def at(s):
    return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))


# ---------------------------------------------------------------- ceiling ----
def r_at_k(mfe, gross, k):
    return np.where(mfe >= k, k, gross)


def book(net, label):
    net = np.asarray(net)
    return {"n": int(len(net)), "net_mean_r": float(net.mean()),
            "net_sum_r": float(net.sum()),
            "usd_per_trade_at_500_per_R": round(float(net.mean()) * 500.0, 2),
            "frac_positive": float((net > 0).mean())}


def ceiling(rows):
    mfe = np.array([r["mfe"] for r in rows])
    gross = np.array([r["terminal_gross_r"] for r in rows])
    ded = np.array([r["deductible_cost_r"] for r in rows])
    pred = np.array([r.get("pred_month_boundary", np.nan) for r in rows], dtype=float)
    out = {}
    for k in KS:
        g = r_at_k(mfe, gross, k)
        net = g - ded
        hit = (mfe >= k)
        c = float(ded.mean())
        row = {
            "target_multiple_k": k,
            "pool_hit_rate": float(hit.mean()),
            "breakeven_hit_rate": (1.0 + c) / (1.0 + k),
            "mean_cost_r_deductible": c,
            "pool_take_everything": book(net, "all"),
            "oracle_perfect": {
                "definition": "take only trades that will reach +kR before the stop",
                "take_share": float(hit.mean()),
                "hit_rate": 1.0,
                "net_mean_r": float((k - ded[hit]).mean()) if hit.any() else None,
                "usd_per_trade_at_500_per_R": round(float((k - ded[hit]).mean()) * 500.0, 2)
                if hit.any() else None,
            },
        }
        # rank oracle and shipped-score at fixed take fractions
        for f in (0.01, 0.05, 0.10, 0.25):
            m = max(1, int(f * len(net)))
            idx = np.argsort(-net)[:m]
            row[f"rank_oracle_top_{int(f*100)}pct"] = {
                "hit_rate": float(hit[idx].mean()), **book(net[idx], "ro")}
            ok = ~np.isnan(pred)
            if ok.sum() > m:
                pidx = np.argsort(-np.where(ok, pred, -1e9))[:m]
                row[f"shipped_ridge_score_top_{int(f*100)}pct"] = {
                    "hit_rate": float(hit[pidx].mean()), **book(net[pidx], "sh")}
        out[str(k)] = row
    return out


# ------------------------------------------------------------ blind control --
def load_m1(month):
    per = {}
    for tag in MONTH_SRC[month]:
        d = BARS / f"bridge_ftmo_m1_{tag}"
        for p in sorted(d.glob("*_M1.csv")):
            sym = p.name[:-7]
            rows = per.setdefault(sym, [])
            with p.open(newline="") as fh:
                for row in csv.DictReader(fh):
                    rows.append((row["time"], row["open"], row["high"], row["low"]))
    out = {}
    for sym, rows in per.items():
        rows = sorted(set(rows), key=lambda r: r[0])
        t = np.array([mins(at(r[0])) for r in rows], dtype=np.int64)
        keep = np.concatenate([[True], np.diff(t) > 0])
        t = t[keep]
        rows = [r for r, k in zip(rows, keep) if k]
        out[sym] = dict(
            t=t,
            o=np.array([float(r[1]) for r in rows]),
            h=np.array([float(r[2]) for r in rows]),
            l=np.array([float(r[3]) for r in rows]),
            hod=np.array([(int(x) // 60) % 24 for x in t]),
        )
    return out


def blind_month(month, rows, risk_of, rng):
    S = load_m1(month)
    res = []
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["symbol"]].append(r)
    for sym, rs in by_sym.items():
        s = S.get(sym)
        if s is None:
            continue
        n = len(s["t"])
        for r in rs:
            risk = risk_of.get(r["candidate_occurrence_key"])
            if not risk or risk <= 0:
                continue
            span = mins(at(r["label_span_end_utc"])) - mins(at(r["label_span_start_utc"]))
            d = 1.0 if r["side"] == "LONG" else -1.0
            for arm, pool in (("U", None), ("H", s["hod"] == (mins(at(r["label_span_start_utc"])) // 60) % 24)):
                cand = np.arange(n - span) if pool is None else np.nonzero(pool[:n - span])[0]
                if len(cand) < 10:
                    continue
                j = int(cand[rng.integers(len(cand))])
                lo, hi = j, min(n, j + span)
                fp = s["o"][j]
                fav = (s["h"][lo:hi].max() - fp) * d if d > 0 else (fp - s["l"][lo:hi].min()) * d * -1
                fav = ((s["h"][lo:hi].max() - fp) if d > 0 else (fp - s["l"][lo:hi].min()))
                adv = ((fp - s["l"][lo:hi].min()) if d > 0 else (s["h"][lo:hi].max() - fp))
                res.append({"arm": arm, "mfe": fav / risk, "mae": -adv / risk,
                            "symbol": sym, "month": month})
    return res


def main():
    rows = []
    for m in MONTHS:
        rows += enrich(load_month(m))
    with gzip.open(HERE / "f4_excursion_join.pkl.gz", "rb") as f:
        exc = {r["candidate_occurrence_key"]: r for r in pickle.load(f)}
    fil = []
    for r in rows:
        e = exc.get(r["candidate_occurrence_key"])
        if e is None:
            continue
        r["mfe"] = e["mfe"]
        r["mae"] = e["mae"]
        fil.append(r)
    print(f"filled with excursion: {len(fil)}")

    res = {"prereg_sha256": "bfe7c722c2f22d45dd8de072fb4e906352b254696a9eb61896ff53a303d68054",
           "n": len(fil), "ceiling": ceiling(fil)}
    res["ceiling_market_only"] = ceiling([r for r in fil if r["proposed_order_type"] == "MARKET"])

    # ---- blind control -----------------------------------------------------
    rng = np.random.default_rng(SEED)
    blind = []
    for m in MONTHS:
        with gzip.open(WALK / f"walk_{m}.pkl.gz", "rb") as f:
            risk_of = {r["k"]: float(r["risk"]) for r in pickle.load(f) if r.get("risk")}
        sub = [r for r in fil if r["month"] == m]
        blind += blind_month(m, sub, risk_of, rng)
        print(f"blind {m}: {len(blind)}", flush=True)

    def dist(mfes, mae=None):
        a = np.asarray(mfes)
        return {"n": int(len(a)), "mfe_mean": float(a.mean()),
                "mfe_median": float(np.median(a)),
                "frac_ge": {str(k): float((a >= k).mean()) for k in KS}}

    real = dist([r["mfe"] for r in fil])
    armU = dist([b["mfe"] for b in blind if b["arm"] == "U"])
    armH = dist([b["mfe"] for b in blind if b["arm"] == "H"])
    res["blind_control"] = {
        "candidate_pool": real, "blind_uniform": armU, "blind_hour_matched": armH,
        "lift_vs_uniform": {k: real["frac_ge"][k] - armU["frac_ge"][k] for k in real["frac_ge"]},
        "lift_vs_hour_matched": {k: real["frac_ge"][k] - armH["frac_ge"][k] for k in real["frac_ge"]},
        "seed": SEED,
        "note": ("Blind arms use raw M1 high/low from the bar open with no quote "
                 "adjustment; the candidate arm's MFE is measured the same way from "
                 "its quote-adjusted fill. The blind arm is therefore very slightly "
                 "favoured, which makes any positive candidate lift a lower bound."),
    }
    # per-symbol lift, to see whether any instrument's generation works
    persym = {}
    bu = defaultdict(list)
    for b in blind:
        if b["arm"] == "H":
            bu[b["symbol"]].append(b["mfe"])
    rr = defaultdict(list)
    for r in fil:
        rr[r["symbol"]].append(r["mfe"])
    for sym in sorted(rr):
        if len(bu.get(sym, [])) < 200:
            continue
        a, b = np.array(rr[sym]), np.array(bu[sym])
        persym[sym] = {"n_real": len(a), "n_blind": len(b),
                       "p_mfe_ge_2_real": float((a >= 2).mean()),
                       "p_mfe_ge_2_blind": float((b >= 2).mean()),
                       "lift": float((a >= 2).mean() - (b >= 2).mean())}
    res["blind_control"]["per_symbol_lift_at_2R"] = persym

    jdump(res, OUT / "F4_CEILING_V1.json")

    print("\n=== CEILING (all filled) ===")
    for k in KS:
        c = res["ceiling"][str(k)]
        print(f"  k={k}: pool hit {c['pool_hit_rate']:.4f} vs breakeven "
              f"{c['breakeven_hit_rate']:.4f} | take-all netR {c['pool_take_everything']['net_mean_r']:+.4f} "
              f"| oracle {c['oracle_perfect']['net_mean_r']:+.4f} (share {c['oracle_perfect']['take_share']:.4f})"
              f" | rank-oracle top10% netR {c['rank_oracle_top_10pct']['net_mean_r']:+.4f}"
              f" | shipped-score top10% netR {c.get('shipped_ridge_score_top_10pct',{}).get('net_mean_r',float('nan')):+.4f}")
    print("\n=== BLIND CONTROL ===")
    print("  real   ", real["frac_ge"])
    print("  blindU ", armU["frac_ge"])
    print("  blindH ", armH["frac_ge"])
    print("  lift vs hour-matched:", res["blind_control"]["lift_vs_hour_matched"])


if __name__ == "__main__":
    main()
