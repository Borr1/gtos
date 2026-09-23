"""m1 — the LIVE SLEEVE arm of the accumulation screen, on the repaired walker.

d3's discriminant is a RATIO of two numbers: the broad family's 0.97x against a live
sleeve's 37.58x.  The broad half is re-derived in `m1_accum.py`; this is the other half,
on the same repaired instrument and with the same deterministic mirror control, so the
comparison is like-for-like.

Population: d3_reverse.load_rows() — every AQ_ESTATE_TRADES_V2 trade of the four live
sleeves plus the standing admission whose entry falls inside the M15 tape window and whose
symbol the tape carries.  d3's own control cohort, unchanged, so any movement here is the
instrument and not the population.

CAVEAT CARRIED FORWARD, because it is the verdict's largest stated soft spot: this cohort
is IN-SAMPLE and n is small.  It is a control, not an admission.
"""
from __future__ import annotations

import gzip
import json
import sys

import numpy as np

sys.path.insert(0, "/tmp/m1")
import m1_accum as A  # noqa: E402

sys.path.insert(0, A.PBG)
sys.path.insert(0, A.REPO)
import pbg_econ as E  # noqa: E402
import pbg_lib as PL  # noqa: E402

from src.research_infra.walkforward.quote_side import (  # noqa: E402
    SpreadUnavailable, spread_for,
)

EST = (A.REPO + "/docs/audits/fable5-vision-audit-20260725/phase11/receipts/"
                "AQ_ESTATE_TRADES_V2.json.gz")
LIVE = ["crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
        "mx_btcusd_d1_donchian_20_breakout"]
NB = 4000
SEED = 20260807


def load_rows(tape_syms):
    o = json.load(gzip.open(EST, "rt"))
    T = o["trades"]
    out = []
    for sl in LIVE:
        for r in T[sl]:
            s = r.get("symbol_canonical") or r.get("symbol")
            eu = r.get("entry_utc")
            if not eu or s not in tape_syms:
                continue
            if not ("2025-06-01" <= eu[:10] <= "2026-05-20"):
                continue
            if not r.get("entry_price") or not r.get("sl_distance_price"):
                continue
            out.append(dict(sleeve=sl, s=s, t=eu.replace("Z", "+00:00"),
                            e=float(r["entry_price"]),
                            dnat=abs(float(r["sl_distance_price"])),
                            long=int(r["direction"]) > 0))
    return out


def main(out_path):
    syms = sorted(p.name[: -len("_M15.csv")] for p in PL.M15_DIR.glob("*_M15.csv"))
    tape = A.CTape(syms)
    cm = E.CostModel()
    rows = load_rows(set(syms))
    n = len(rows)
    print("live rows", n, flush=True)

    entry = np.array([r["e"] for r in rows])
    dnat = np.array([r["dnat"] for r in rows])
    long = np.array([r["long"] for r in rows])
    dbps = dnat / entry * 1e4
    days = np.array([r["t"][:10] for r in rows])
    sgnR = np.where(long, 1.0, -1.0)
    s_tick = np.zeros(n)
    s_era = np.zeros(n)
    for a, r in enumerate(rows):
        s_tick[a] = cm.spread_bps(r["s"], cm.broker_hour(r["t"])) / 1e4 * r["e"]
        try:
            import datetime as dt
            s_era[a] = spread_for(A.SPREAD_NAME.get(r["s"], r["s"]),
                                  dt.datetime.fromisoformat(r["t"]),
                                  account="FTMO", band="mid")
        except SpreadUnavailable:
            s_era[a] = np.nan

    pos = np.array([tape.pos(r["s"], r["t"]) for r in rows], dtype=np.int64)
    ar = np.arange(A.MAXH + 2)
    Wh = np.full((n, A.MAXH + 2), np.nan)
    Wl = np.full((n, A.MAXH + 2), np.nan)
    Wc = np.full((n, A.MAXH + 2), np.nan)
    for s in set(r["s"] for r in rows):
        aa = np.array([a for a in range(n) if rows[a]["s"] == s])
        h_, l_, c_, m = tape.h[s], tape.l[s], tape.c[s], tape.c[s].size
        cols = pos[aa][:, None] + ar[None, :]
        good = (cols >= 0) & (cols < m)
        cl = np.clip(cols, 0, max(m - 1, 0))
        Wh[aa] = np.where(good, h_[cl], np.nan)
        Wl[aa] = np.where(good, l_[cl], np.nan)
        Wc[aa] = np.where(good, c_[cl], np.nan)

    res = {}
    for arm, sp in (("old", None), ("cor", s_tick), ("era", s_era)):
        for side, sg in (("REAL", sgnR), ("MIRROR", -sgnR)):
            anchor = entry if sp is None else entry + sg * sp
            g = sg[:, None]
            a_ = anchor[:, None]
            dd = dnat[:, None]
            rc = (Wc - a_) / dd * g
            rh = (Wh - a_) / dd * g
            rl = (Wl - a_) / dd * g
            out = A.cell_walk(rc, np.maximum(rh, rl), np.minimum(rh, rl), A.TARGET, A.HOR)
            for h in A.HOR:
                res[f"{arm}_{side}_{h}"] = out[h]

    rng = np.random.default_rng(SEED)
    ud, inv = np.unique(days, return_inverse=True)
    k = ud.size
    ix = rng.integers(0, k, size=(NB, k))
    report = {"what": "the live-sleeve arm of the accumulation screen, repaired walker",
              "population": {"n": n, "sleeves": LIVE, "day_blocks": int(k),
                             "caveat": "in-sample, small; d3's own control cohort"},
              "median_stop_bps": float(np.median(dbps)), "curves": {}}
    for arm in ("old", "cor", "era"):
        rowsout = []
        bs_r = {}
        for h, hh in zip(A.HOR, A.HH):
            a = res[f"{arm}_REAL_{h}"]
            b = res[f"{arm}_MIRROR_{h}"]
            m = np.isfinite(a) & np.isfinite(b)
            dr = ((a - b) * 0.5)[m]
            db = dr * dbps[m]
            s_, c_ = (np.bincount(inv[m], weights=dr, minlength=k),
                      np.bincount(inv[m], minlength=k).astype(float))
            sb, _ = (np.bincount(inv[m], weights=db, minlength=k),
                     np.bincount(inv[m], minlength=k).astype(float))
            cnt = c_[ix].sum(axis=1)
            bs_r[hh] = s_[ix].sum(axis=1) / np.where(cnt > 0, cnt, np.nan)
            bsb = sb[ix].sum(axis=1) / np.where(cnt > 0, cnt, np.nan)
            rowsout.append({
                "hours": hh, "n": int(m.sum()),
                "signal_r": float(dr.mean()), "signal_bps_perrow": float(db.mean()),
                "signal_bps_d3_form": float(dr.mean() * np.median(dbps[m])),
                "ci_lo_bps": float(np.nanpercentile(bsb, 2.5)),
                "ci_hi_bps": float(np.nanpercentile(bsb, 97.5)),
                "p_le0": float(np.nanmean(bsb <= 0)),
                "gross_r_real": float(a[m].mean()), "gross_r_mirror": float(b[m].mean()),
            })
        ratio = bs_r[320] / bs_r[2]
        report["curves"][arm] = {
            "rows": rowsout,
            "growth_ratio_point": rowsout[-1]["signal_r"] / rowsout[0]["signal_r"],
            "growth_ratio_ci95": [float(np.nanpercentile(ratio, 2.5)),
                                  float(np.nanpercentile(ratio, 97.5))],
            "share_ratio_ge_10": float(np.nanmean(ratio >= 10)),
            "share_ratio_ge_3": float(np.nanmean(ratio >= 3)),
        }
    json.dump(report, open(out_path, "w"), indent=1)
    for arm, c in report["curves"].items():
        print(f"\n=== LIVE SLEEVES |{arm}|  n={c['rows'][0]['n']}  "
              f"median_stop={report['median_stop_bps']:.2f} bps")
        print(f"{'h':>5s} {'signal_R':>10s} {'bps(d3)':>10s} {'bps(row)':>10s} "
              f"{'ci_lo':>9s} {'ci_hi':>9s} {'p<=0':>7s} {'real_R':>9s}")
        for r in c["rows"]:
            print(f"{r['hours']:5d} {r['signal_r']:10.5f} {r['signal_bps_d3_form']:10.3f} "
                  f"{r['signal_bps_perrow']:10.3f} {r['ci_lo_bps']:9.3f} "
                  f"{r['ci_hi_bps']:9.3f} {r['p_le0']:7.4f} {r['gross_r_real']:9.4f}")
        print(f"GROWTH {c['growth_ratio_point']:.2f}x  CI95 "
              f"[{c['growth_ratio_ci95'][0]:.2f}, {c['growth_ratio_ci95'][1]:.2f}]  "
              f"P(>=10x)={c['share_ratio_ge_10']:.3f}  P(>=3x)={c['share_ratio_ge_3']:.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
