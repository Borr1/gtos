#!/usr/bin/env python3
"""F3 (6) — WHAT IS KNOWABLE AT ENTRY.  The centre of the lane.

The owner's standing objection to "widen the stop" is that it protects a thing that
was not strong in the first place.  The same objection applies to every exit-side
repair: it manages a trade that should not have been taken.  So the question that
matters is which reversal causes are visible BEFORE the trade exists.

Every feature here is a pure function of information available at the fill minute.
The headline candidate is the OBSTACLE: a structural level sitting in the path
between the entry and the 2 R target.  If the trade has to climb through the prior
day's high to reach its target, that is knowable when the candidate is generated.

Discipline:
  * TRAIN = feb, apr, may.  TEST = jun, jul.  Nothing is selected on test.
  * LAG TEST: every level is re-run 5 trading days stale.  A real structural effect
    dies when the level is from the wrong day; a construction artifact does not.
  * Bootstrap CIs on the trade level, and a day-block bootstrap because trades on
    one day are not independent.
"""
import gzip, json, math, pickle, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

TMP = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f3")
OUT = Path(__file__).resolve().parent
TRAIN = ["feb", "apr", "may"]
TEST = ["jun", "jul"]
R_USD = 250.0
PRIOR = ["pdh", "pdl", "wkh", "wkl", "psh", "psl"]
FROZEN = ["dh", "dl", "sh", "sl"]
MA = ["sma20", "sma50", "sma200", "swh", "swl"]


def round_step(risk):
    return 10.0 ** (math.floor(math.log10(risk)) if risk > 0 else -4)


def build(month, lag_days=0):
    L = pickle.load(gzip.open(TMP / f"f3_levels_{month}.pkl.gz", "rb"))
    trades = pickle.load(gzip.open(TMP / f"f3_trades_{month}.pkl.gz", "rb"))
    rows = []
    for t in trades:
        S = L.get(t["sym"])
        if S is None:
            continue
        d = 1 if str(t["side"]).upper() == "LONG" else -1
        e, tg, risk = t["entry"], t["target"], t["risk"]
        tt = S["t"]
        j = int(np.searchsorted(tt, t["fill_min"] - lag_days * 1440, side="right")) - 1
        if j < 0:
            continue
        span = (tg - e) * d
        if span <= 0:
            continue
        obs, obs_names, sup = [], [], []
        for nm in PRIOR + FROZEN + MA:
            v = float(S[nm][j])
            if v != v:
                continue
            frac = (v - e) * d / span
            if 0.02 < frac < 0.98:                 # strictly inside the path to target
                obs.append(frac); obs_names.append(nm)
            if -1.0 < frac <= 0.0:                 # behind the entry: support
                sup.append(-frac)
        st = round_step(risk)
        for mult in (1.0, 5.0, 10.0):
            step = st * mult
            k = math.ceil(min(e, tg) / step) * step
            while k < max(e, tg):
                frac = (k - e) * d / span
                if 0.02 < frac < 0.98:
                    obs.append(frac); obs_names.append(f"rnd{int(mult)}")
                k += step
        names = set(obs_names)
        strong = [f for f, nm in zip(obs, obs_names) if nm in PRIOR + FROZEN]
        rows.append(dict(
            k=t["k"], month=month, sym=t["sym"], fam=t["fam"], day=t["day"], ot=t["ot"],
            side=t["side"], net=t["term_gross"] - t["ded"], gross=t["term_gross"],
            mfe=t["mfe"], gb=t["give_back"], term=t["term_kind"], risk=risk,
            n_obstacles=len(obs), n_obstacle_types=len(names),
            n_strong=len([n for n in names if n in PRIOR + FROZEN]),
            nearest_strong=min(strong) if strong else np.nan,
            nearest_obstacle=min(obs) if obs else np.nan,
            obstacle_names=sorted(names),
            n_support=len(sup), nearest_support=min(sup) if sup else np.nan))
    return rows


def boot_mean(x, n=4000, seed=13):
    x = np.asarray(x, float)
    if len(x) < 5:
        return float("nan"), [float("nan")] * 2
    rng = np.random.default_rng(seed)
    mu = x[rng.integers(0, len(x), (n, len(x)))].mean(axis=1)
    return float(x.mean()), [float(np.percentile(mu, 2.5)), float(np.percentile(mu, 97.5))]


def day_block_diff(rows, mask, n=4000, seed=17):
    """Difference in mean net R between mask and ~mask, bootstrapped over DAYS."""
    net = np.array([r["net"] for r in rows])
    days = np.array([r["day"] for r in rows])
    ud = np.unique(days)
    didx = {d: np.nonzero(days == d)[0] for d in ud}
    if mask.sum() < 5 or (~mask).sum() < 5:
        return dict(diff=None, ci95_dayblock=None, p_two_sided=None,
                    n_days=int(len(ud)), degenerate=True,
                    n_in=int(mask.sum()), n_out=int((~mask).sum()))
    rng = np.random.default_rng(seed)
    obs = net[mask].mean() - net[~mask].mean()
    out = []
    for _ in range(n):
        pick = rng.integers(0, len(ud), len(ud))
        idx = np.concatenate([didx[ud[p]] for p in pick])
        m = mask[idx]
        if m.sum() < 5 or (~m).sum() < 5:
            continue
        out.append(net[idx][m].mean() - net[idx][~m].mean())
    if len(out) < 100:
        return dict(diff=float(obs), ci95_dayblock=None, p_two_sided=None,
                    n_days=int(len(ud)), unstable=True)
    out = np.array(out)
    return dict(diff=float(obs),
                ci95_dayblock=[float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))],
                p_two_sided=float(2 * min((out <= 0).mean(), (out >= 0).mean())),
                n_days=int(len(ud)))


def describe(rows, label):
    net = np.array([r["net"] for r in rows])
    gb = np.array([r["gb"] for r in rows])
    no = np.array([r["n_obstacles"] for r in rows])
    nt = np.array([r["n_obstacle_types"] for r in rows])
    nr = np.array([r["nearest_obstacle"] for r in rows])
    out = {"label": label, "n": len(rows), "mean_net_R": float(net.mean()),
           "total_net_R": float(net.sum()), "mean_give_back_R": float(gb.mean())}
    out["by_n_obstacle_types"] = {}
    for v in range(0, 7):
        m = nt == v if v < 6 else nt >= 6
        if m.sum() < 30:
            continue
        mu, c = boot_mean(net[m])
        out["by_n_obstacle_types"][str(v) if v < 6 else "6+"] = dict(
            n=int(m.sum()), mean_net_R=mu, ci95=c, mean_give_back_R=float(gb[m].mean()),
            reversal_rate=float(((np.array([r["mfe"] for r in rows]) >= 1.0) & (net < 0))[m].mean()))
    out["by_nearest_obstacle_decile"] = {}
    fin = nr == nr
    if fin.sum() > 100:
        qs = np.quantile(nr[fin], np.linspace(0, 1, 6))
        for a in range(5):
            m = fin & (nr >= qs[a]) & (nr <= qs[a + 1] if a == 4 else nr < qs[a + 1])
            if m.sum() < 30:
                continue
            mu, c = boot_mean(net[m])
            out["by_nearest_obstacle_decile"][f"{qs[a]:.2f}-{qs[a+1]:.2f}"] = dict(
                n=int(m.sum()), mean_net_R=mu, ci95=c)
    mu0, c0 = boot_mean(net[nt == 0]); mu1, c1 = boot_mean(net[nt > 0])
    out["clean_path_vs_obstructed"] = dict(
        clean_n=int((nt == 0).sum()), clean_mean_net_R=mu0, clean_ci95=c0,
        obstructed_n=int((nt > 0).sum()), obstructed_mean_net_R=mu1, obstructed_ci95=c1)
    out["clean_path_vs_obstructed"].update(day_block_diff(rows, nt == 0))
    # STRONG obstacles only (prior-period + fill-frozen extremes; no MAs, no round numbers)
    ns = np.array([r["n_strong"] for r in rows])
    out["strong_obstacle_count"] = {}
    for v in range(0, 6):
        m = ns == v if v < 5 else ns >= 5
        if m.sum() < 30:
            continue
        mu, c = boot_mean(net[m])
        out["strong_obstacle_count"][str(v) if v < 5 else "5+"] = dict(
            n=int(m.sum()), share=float(m.mean()), mean_net_R=mu, ci95=c,
            mean_give_back_R=float(gb[m].mean()),
            reversal_rate=float(((np.array([r["mfe"] for r in rows]) >= 1.0) & (net < 0))[m].mean()))
    mu0, c0 = boot_mean(net[ns == 0]); mu1, c1 = boot_mean(net[ns >= 2])
    out["strong_none_vs_two_plus"] = dict(
        none_n=int((ns == 0).sum()), none_mean_net_R=mu0, none_ci95=c0,
        two_plus_n=int((ns >= 2).sum()), two_plus_mean_net_R=mu1, two_plus_ci95=c1)
    if (ns == 0).sum() >= 5 and (ns >= 2).sum() >= 5:
        sub = [r for r in rows if r["n_strong"] == 0 or r["n_strong"] >= 2]
        m = np.array([r["n_strong"] == 0 for r in sub])
        out["strong_none_vs_two_plus"].update(day_block_diff(sub, m))
    # nearest STRONG obstacle position
    nsr = np.array([r["nearest_strong"] for r in rows])
    fin2 = nsr == nsr
    out["by_nearest_strong_quintile"] = {}
    if fin2.sum() > 500:
        qs = np.quantile(nsr[fin2], np.linspace(0, 1, 6))
        for a in range(5):
            hi = nsr <= qs[a + 1] if a == 4 else nsr < qs[a + 1]
            m = fin2 & (nsr >= qs[a]) & hi
            if m.sum() < 30:
                continue
            mu, c = boot_mean(net[m])
            out["by_nearest_strong_quintile"][f"{qs[a]:.3f}-{qs[a+1]:.3f}"] = dict(
                n=int(m.sum()), mean_net_R=mu, ci95=c,
                mean_give_back_R=float(gb[m].mean()))
    return out


def main():
    lag = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    tr, te = [], []
    for m in TRAIN:
        tr += build(m, lag)
        print(json.dumps({"stage": "train", "month": m, "n": len(tr)}), flush=True)
    for m in TEST:
        te += build(m, lag)
        print(json.dumps({"stage": "test", "month": m, "n": len(te)}), flush=True)
    out = {"schema": "gtos.f3.exante.v1", "lag_days": lag, "R_usd": R_USD,
           "train_months": TRAIN, "test_months": TEST,
           "obstacle_definition": "a structural level strictly inside (2%,98%) of the "
                                  "price path from entry to the 2R target, evaluated at "
                                  "the fill minute from closed bars only",
           "train": describe(tr, "TRAIN feb+apr+may"),
           "test": describe(te, "TEST jun+jul")}
    # per-family on test, for the honest breadth check
    out["test_by_family"] = {}
    fam = defaultdict(list)
    for r in te:
        fam[r["fam"]].append(r)
    for f, rs in sorted(fam.items()):
        if len(rs) < 200:
            continue
        net = np.array([r["net"] for r in rs]); nt = np.array([r["n_obstacle_types"] for r in rs])
        if (nt == 0).sum() < 30 or (nt > 0).sum() < 30:
            continue
        mu0, c0 = boot_mean(net[nt == 0]); mu1, c1 = boot_mean(net[nt > 0])
        out["test_by_family"][f] = dict(n=len(rs), clean_n=int((nt == 0).sum()),
                                        clean_mean_net_R=mu0, clean_ci95=c0,
                                        obstructed_mean_net_R=mu1, obstructed_ci95=c1)
    # which obstacle types carry the damage (test)
    out["test_by_obstacle_type"] = {}
    for nm in PRIOR + FROZEN + MA + ["rnd1", "rnd5", "rnd10"]:
        m = np.array([nm in r["obstacle_names"] for r in te])
        if m.sum() < 100 or (~m).sum() < 100:
            continue
        net = np.array([r["net"] for r in te])
        mu, c = boot_mean(net[m])
        out["test_by_obstacle_type"][nm] = dict(n=int(m.sum()), mean_net_R=mu, ci95=c,
                                                mean_net_R_without=float(net[~m].mean()))
    tag = f"_lag{lag}" if lag else ""
    (OUT / f"F3_EXANTE{tag}.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"train": out["train"]["clean_path_vs_obstructed"],
                      "test": out["test"]["clean_path_vs_obstructed"]}, indent=1))
    with gzip.open(TMP / f"f3_exante_rows{tag}.pkl.gz", "wb") as fh:
        pickle.dump({"train": tr, "test": te}, fh, protocol=5)


if __name__ == "__main__":
    main()
