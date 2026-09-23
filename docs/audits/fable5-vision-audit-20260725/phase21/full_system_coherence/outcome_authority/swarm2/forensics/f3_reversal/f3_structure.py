#!/usr/bin/env python3
"""F3 (2) — WHERE IN PRICE.  Did the reversal happen at a structural level?

The null hypothesis this lane is built to defeat: levels are everywhere, so a turn
lands near one by chance.  Three controls, run on identical machinery:

  PAIRED (primary)   Within the SAME trade, compare the terminal peak against that
                     trade's own earlier stalls — advances that retraced by the same
                     >= DELTA R and then RESUMED.  Same symbol, same day, same hour,
                     same volatility, same trade geometry.  The only difference is
                     whether the move came back.  A structural claim that does not
                     survive this is an artifact.
  PLACEBO-LEVEL      The identical test against levels lifted from 5 trading days
                     earlier (same construction, same roundness, wrong day).
  PLACEBO-TIME       The identical test at a random minute inside the trade's life.

Distances are in R (the trade's own stop distance), which is the scale the
economics are denominated in.
"""
import gzip, json, math, pickle, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = Path(__file__).resolve().parent
MONTHS = ["feb", "apr", "may", "jun", "jul"]
TAUS = [0.05, 0.10, 0.25]
PRIOR = ["pdh", "pdl", "wkh", "wkl", "psh", "psl"]      # fixed before the day/session
FROZEN = ["dh", "dl", "sh", "sl"]                        # frozen at the fill minute
LIVE = ["sma20", "sma50", "sma200", "swh", "swl"]        # evolve, causal at stall minute
ROUND = ["rnd1", "rnd5", "rnd10"]
ALL = PRIOR + FROZEN + LIVE + ROUND + ["target", "entry"]


def round_step(risk):
    """Round-number granularity anchored to the trade's own risk scale."""
    p = math.floor(math.log10(risk)) if risk > 0 else -4
    return 10.0 ** p


def lvl_at(L, minute, name):
    t = L["t"]
    j = int(np.searchsorted(t, minute, side="right")) - 1
    if j < 0:
        return np.nan
    return float(L[name][j])


def collect(month, rng):
    L = pickle.load(gzip.open(TMP / f"f3_levels_{month}.pkl.gz", "rb"))
    trades = {t["k"]: t for t in pickle.load(gzip.open(TMP / f"f3_trades_{month}.pkl.gz", "rb"))}
    stalls = pickle.load(gzip.open(TMP / f"f3_stalls_{month}.pkl.gz", "rb"))
    idx = {}
    for sym, S in L.items():
        idx[sym] = S["t"]
    rows = []
    for s in stalls:
        sym = s["sym"]; S = L.get(sym)
        if S is None:
            continue
        tr = trades[s["k"]]
        d = 1 if str(s["side"]).upper() == "LONG" else -1
        risk = s["risk"]; px = s["px"]
        t = S["t"]
        j = int(np.searchsorted(t, s["minute"], side="right")) - 1
        jf = int(np.searchsorted(t, tr["fill_min"], side="right")) - 1
        jp = int(np.searchsorted(t, s["minute"] - 5 * 1440, side="right")) - 1
        if j < 0 or jf < 0:
            continue
        # random placebo minute inside the trade's life
        span = max(tr["term_min"] - tr["fill_min"], 1)
        jr = int(np.searchsorted(t, tr["fill_min"] + int(rng.integers(0, span)), side="right")) - 1
        jr = max(jr, 0)
        r = dict(k=s["k"], kind=s["kind"], sym=sym, fam=s["fam"], month=month,
                 minute=s["minute"], fav=s["fav"], retr=s["retr"], risk=risk,
                 term_kind=s["term_kind"], mfe=s["mfe"], bars=s["bars"])
        vals = {}
        for nm in PRIOR + LIVE:
            vals[nm] = float(S[nm][j])
        for nm in FROZEN:
            vals[nm] = float(S[nm][jf])                  # frozen at fill: ex-ante
        vals["target"] = s["target"]; vals["entry"] = s["entry"]
        st = round_step(risk)
        for nm, mult in zip(ROUND, [1.0, 5.0, 10.0]):
            step = st * mult
            vals[nm] = round(px / step) * step
        for nm in ALL:
            v = vals[nm]
            r["d_" + nm] = abs(px - v) / risk if v == v else np.nan
            r["s_" + nm] = (v - px) * d / risk if v == v else np.nan
        # placebo levels: same construction, five trading days earlier
        for nm in PRIOR:
            v = float(S[nm][jp]) if jp >= 0 else np.nan
            r["p_" + nm] = abs(px - v) / risk if v == v else np.nan
        # placebo time: same levels, a random minute in the trade
        pxr = float(S["c"][jr])
        for nm in PRIOR:
            v = float(S[nm][jr])
            r["q_" + nm] = abs(pxr - v) / risk if v == v else np.nan
        for nm, mult in zip(ROUND, [1.0, 5.0, 10.0]):
            step = st * mult
            r["q_" + nm] = abs(pxr - round(pxr / step) * step) / risk
        rows.append(r)
    return rows


def paired(rows, field, tau):
    """Within-trade paired rate difference: peak vs its own pauses."""
    byk = defaultdict(lambda: ([], []))
    for r in rows:
        v = r.get(field)
        if v is None or v != v:
            continue
        hit = 1.0 if v <= tau else 0.0
        byk[r["k"]][0 if r["kind"] == "peak" else 1].append(hit)
    dif, pk, pa = [], [], []
    for k, (P, Q) in byk.items():
        if not P or not Q:
            continue
        dif.append(np.mean(P) - np.mean(Q)); pk.append(np.mean(P)); pa.append(np.mean(Q))
    if len(dif) < 30:
        return None
    dif = np.array(dif)
    rng = np.random.default_rng(7)
    b = rng.integers(0, len(dif), (2000, len(dif)))
    mu = dif[b].mean(axis=1)
    return dict(n_trades=len(dif), peak_rate=float(np.mean(pk)), pause_rate=float(np.mean(pa)),
                diff=float(dif.mean()),
                ci95=[float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))],
                p_two_sided=float(2 * min((mu <= 0).mean(), (mu >= 0).mean())))


def unpaired(rows, field, tau):
    P = [r[field] for r in rows if r["kind"] == "peak" and r.get(field) == r.get(field)]
    Q = [r[field] for r in rows if r["kind"] == "pause" and r.get(field) == r.get(field)]
    if len(P) < 30 or len(Q) < 30:
        return None
    return dict(n_peak=len(P), n_pause=len(Q),
                peak_rate=float(np.mean(np.array(P) <= tau)),
                pause_rate=float(np.mean(np.array(Q) <= tau)))


def main():
    rng = np.random.default_rng(3)
    rows = []
    for m in MONTHS:
        rows += collect(m, rng)
        print(json.dumps({"stage": "collected", "month": m, "rows": len(rows)}), flush=True)
    out = {"schema": "gtos.f3.structure.v1", "n_stalls": len(rows),
           "n_peak": sum(1 for r in rows if r["kind"] == "peak"),
           "n_pause": sum(1 for r in rows if r["kind"] == "pause"),
           "delta_R_defining_a_stall": 0.25,
           "design": {"primary": "within-trade paired peak vs pause",
                      "placebo_level": "same level construction, 5 trading days earlier (p_*)",
                      "placebo_time": "same levels, random minute inside the trade (q_*)"}}
    res = {}
    for tau in TAUS:
        r1 = {}
        for nm in ALL:
            v = paired(rows, "d_" + nm, tau)
            if v:
                r1[nm] = v
        for nm in PRIOR:
            v = paired(rows, "p_" + nm, tau)
            if v:
                r1["PLACEBO_LEVEL_" + nm] = v
            v = paired(rows, "q_" + nm, tau)
            if v:
                r1["PLACEBO_TIME_" + nm] = v
        for nm in ROUND:
            v = paired(rows, "q_" + nm, tau)
            if v:
                r1["PLACEBO_TIME_" + nm] = v
        res[f"tau_{tau}"] = r1
    out["paired"] = res
    out["unpaired_tau_0.10"] = {nm: unpaired(rows, "d_" + nm, 0.10) for nm in ALL}
    # "any structural level" composite
    for tau in TAUS:
        for r in rows:
            r[f"any_{tau}"] = 0.0 if any(
                (r.get("d_" + nm) == r.get("d_" + nm)) and r.get("d_" + nm, 9) <= tau
                for nm in PRIOR + FROZEN + LIVE) else 1.0
        # store as distance-like (0 = hit) so the same helper works
        out.setdefault("composite_any_level", {})[f"tau_{tau}"] = paired(rows, f"any_{tau}", 0.5)
    (OUT / "F3_STRUCTURE.json").write_text(json.dumps(out, indent=1))
    with gzip.open(TMP / "f3_struct_rows.pkl.gz", "wb") as fh:
        pickle.dump(rows, fh, protocol=5)
    print(json.dumps(out["paired"]["tau_0.1"], indent=1)[:3000])


if __name__ == "__main__":
    main()
