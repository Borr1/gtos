#!/usr/bin/env python3
"""F3 (1) — the give-back census.  Defines the population before characterising it."""
import gzip, json, pickle
from pathlib import Path
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = Path(__file__).resolve().parent
R_USD = 250.0          # see report §0: representative 1 R at a $100k account


def load():
    tr = []
    for m in ["feb", "apr", "may", "jun", "jul"]:
        tr += pickle.load(gzip.open(TMP / f"f3_trades_{m}.pkl.gz", "rb"))
    return tr


def ci(x, n=2000, seed=11):
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    b = rng.integers(0, len(x), (n, len(x)))
    mu = x[b].mean(axis=1)
    return [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))]


def main():
    tr = load()
    gross = np.array([t["term_gross"] for t in tr])
    ded = np.array([t["ded"] for t in tr])
    net = gross - ded
    mfe = np.array([t["mfe"] for t in tr])
    gb = np.array([t["give_back"] for t in tr])
    kind = np.array([t["term_kind"] for t in tr])
    out = {"schema": "gtos.f3.giveback_census.v1", "n_trades": len(tr),
           "pool_net_R": float(net.sum()), "pool_net_R_per_trade": float(net.mean()),
           "pool_net_usd": float(net.sum() * R_USD), "R_usd_convention": R_USD,
           "terminal_mix": {k: int((kind == k).sum()) for k in sorted(set(kind))}}

    # --- ladder over "meaningful favourable excursion" -----------------------
    lad = []
    for th in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
        m = mfe >= th
        mneg = m & (net < 0)
        lad.append(dict(
            mfe_threshold_R=th, n=int(m.sum()), share_of_pool=float(m.mean()),
            n_ended_negative=int(mneg.sum()),
            share_of_cohort_ended_negative=float(mneg.sum() / max(m.sum(), 1)),
            mean_mfe_R=float(mfe[m].mean()), mean_net_R=float(net[m].mean()),
            total_net_R=float(net[m].sum()),
            total_give_back_R=float(gb[m].sum()),
            give_back_of_negative_cohort_R=float(gb[mneg].sum()),
            net_R_of_negative_cohort=float(net[mneg].sum()),
            net_usd_of_negative_cohort=float(net[mneg].sum() * R_USD),
            terminal_mix={k: int((kind[m] == k).sum()) for k in sorted(set(kind))}))
    out["ladder"] = lad

    # --- the headline population: reached >= 1R, ended negative --------------
    P = (mfe >= 1.0) & (net < 0)
    out["headline_population"] = dict(
        definition="mfe >= 1.0 R (a full stop-width in our favour) AND terminal net R < 0",
        n=int(P.sum()), share_of_pool=float(P.mean()),
        mean_mfe_R=float(mfe[P].mean()), mean_net_R=float(net[P].mean()),
        total_net_R=float(net[P].sum()), total_net_usd=float(net[P].sum() * R_USD),
        total_give_back_R=float(gb[P].sum()), total_give_back_usd=float(gb[P].sum() * R_USD),
        share_of_pool_total_loss=float(net[P].sum() / net.sum()),
        terminal_mix={k: int((kind[P] == k).sum()) for k in sorted(set(kind))},
        median_bars_fill_to_peak=float(np.median([t["peak_bars"] for t, p in zip(tr, P) if p])),
        median_minutes_peak_to_terminal=float(np.median(
            [t["term_min"] - t["peak_min"] for t, p in zip(tr, P) if p])))

    # --- what if we had simply banked the peak (upper bound on the prize) -----
    for th in [0.5, 1.0]:
        m = mfe >= th
        out[f"upper_bound_bank_at_{th}R"] = dict(
            note="counterfactual ceiling only: exits every trade the instant it first "
                 "touches the threshold; not achievable, prices the size of the prize",
            n=int(m.sum()), realised_net_R=float(net[m].sum()),
            banked_net_R=float((th - ded[m]).sum()),
            delta_R=float((th - ded[m]).sum() - net[m].sum()),
            delta_usd=float(((th - ded[m]).sum() - net[m].sum()) * R_USD))

    # --- give-back concentration --------------------------------------------
    o = np.argsort(-gb)
    for q in [0.01, 0.05, 0.10, 0.25]:
        k = int(len(tr) * q)
        out.setdefault("give_back_concentration", {})[f"top_{int(q*100)}pct_share"] = \
            float(gb[o[:k]].sum() / gb.sum())

    # --- per family / month --------------------------------------------------
    fam = np.array([t["fam"] for t in tr]); mo = np.array([t["month"] for t in tr])
    out["by_family"] = {}
    for f in sorted(set(fam)):
        m = fam == f; P2 = m & (mfe >= 1.0) & (net < 0)
        out["by_family"][f] = dict(n=int(m.sum()), net_R=float(net[m].sum()),
                                   n_reversed=int(P2.sum()),
                                   reversed_net_R=float(net[P2].sum()),
                                   reversed_share_of_family_loss=float(
                                       net[P2].sum() / net[m].sum()) if net[m].sum() else None)
    out["by_month"] = {}
    for f in sorted(set(mo)):
        m = mo == f; P2 = m & (mfe >= 1.0) & (net < 0)
        out["by_month"][f] = dict(n=int(m.sum()), net_R=float(net[m].sum()),
                                  n_reversed=int(P2.sum()), reversed_net_R=float(net[P2].sum()))
    (OUT / "F3_CENSUS.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("n_trades", "pool_net_R", "headline_population")},
                     indent=1))


if __name__ == "__main__":
    main()
