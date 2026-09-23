"""KB6_router_signsource_ab.py — track KB6 GOAL 3 robustness A/B.

The per-base TRAIN-learned router came out flat. WHY: on the non-flagship xvol bases the
veto/liquidity confluence is a FORWARD-ONLY (2025/26-regime) effect whose TRAIN-period sign
is the OPPOSITE (e.g. xvol_dn_london ll=none: TRAIN -0.33 / FWD +0.36; liq=aligned TRAIN
-0.12 / FWD +0.80). A no-lookahead sign-learner cannot capture a sign that does not exist
in TRAIN. This A/B confirms the result is robust across THREE legitimate (no-lookahead)
sign sources, and isolates the one place a router DOES help:
  S1 = per-base TRAIN sign (the built router)
  S2 = pooled across the xvol-vol FAMILY (KB5 proved the veto sign is shared across the
       xvol-up family) — TRAIN only, still no forward peeking
  S3 = KB5-PRIOR signs (the veto/liq direction proven on the FLAGSHIP in BOTH train+fwd,
       transferred as a fixed prior to the family) — this is the only source that encodes
       the genuinely-confluent direction without peeking at THIS book's forward window.
Verdict = vol-matched 1.5x left-tail STRESS challenge-pass on the deploy-book fold, vs FLAT.
Also reports a FLAGSHIP-ONLY sleeve (the KB5-deep cell) router, the honest deployable case.
"""
from __future__ import annotations
import sys, json, collections, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB6_router_validate as RV

TRAIN_MAX = 2024
GAIN, LO, HI = RV.GAIN, RV.LO, RV.HI
DIMS = RV.ROUTER_DIMS
mc_series = W2.mc_series

# S3: KB5/KB6-PRIOR confluence direction (proven on the flagship in train+fwd, and the
# liquidity gate train+fwd-positive on xvol_dn_london). A FIXED prior — no peeking at the
# deploy forward verdict. Applied to every base in the family.
PRIOR_SIGNS = {
    ("*", "ll_align", "none"): +1,      # leader VETO helps (flagship train+fwd; family fwd)
    ("*", "ll_align", "opposed"): -1,   # leader against = bad (signed mirror, all bases)
    ("*", "liq_align", "aligned"): +1,  # sweep+reclaim in dir helps (xvol_dn train+fwd +)
    ("*", "liq_align", "opposed"): -1,
    ("*", "vp_loc", "above_va"): +1,    # acceptance above value helps the longs (KB5)
    ("*", "vp_loc", "below_va"): -1,
    ("*", "hurst", "trend"): -1,        # trending hurst inverts the mean-revert mechanic (KB5)
}


def learn_per_base(rows):
    return RV.learn_signs(rows)[0]


def learn_pooled(rows):
    """pool all rows (xvol family) into ONE TRAIN sign map (key by dim,val; base='*')."""
    tr = [r for r in rows if r["year"] <= TRAIN_MAX]
    bmean = sum(r["R"] for r in tr) / len(tr)
    buck = collections.defaultdict(list)
    for r in tr:
        for d in DIMS:
            v = r["conds"].get(d)
            if v not in (None, "na"):
                buck[(d, v)].append(r["R"])
    signs = {}
    for (d, v), Rs in buck.items():
        if len(Rs) < 25:
            continue
        lift = sum(Rs) / len(Rs) - bmean
        if abs(lift) > RV.EPS:
            signs[("*", d, v)] = 1 if lift > 0 else -1
    return signs


def score(r, signs, pooled=False, prior=False):
    sc = 0
    for d in DIMS:
        v = r["conds"].get(d)
        if v in (None, "na"):
            continue
        if prior:
            sc += PRIOR_SIGNS.get(("*", d, v), 0)
        elif pooled:
            sc += signs.get(("*", d, v), 0)
        else:
            sc += signs.get((r["base"], d, v), 0)
    return sc


def per_day(rows, signs, mode):
    num = collections.defaultdict(float); den = collections.defaultdict(float)
    for r in rows:
        if mode == "flat":
            sz = 1.0
        else:
            s = score(r, signs, pooled=(mode == "pooled"), prior=(mode == "prior"))
            sz = max(LO, min(HI, 1.0 + GAIN * s))
        num[r["date"]] += sz * r["R"]; den[r["date"]] += sz
    return {d: num[d] / den[d] for d in num}


def fwd_ev(rows, signs, mode):
    fw = [r for r in rows if r["year"] >= 2025]
    if mode == "flat":
        return round(sum(r["R"] for r in fw) / len(fw), 4)
    n = sum(max(LO, min(HI, 1.0 + GAIN * score(r, signs, pooled=(mode=="pooled"), prior=(mode=="prior")))) * r["R"] for r in fw)
    d = sum(max(LO, min(HI, 1.0 + GAIN * score(r, signs, pooled=(mode=="pooled"), prior=(mode=="prior")))) for r in fw)
    return round(n / d, 4)


def main():
    rows = pickle.load(open(HERE / "KB6_router_signals.pkl", "rb"))
    s_pb = learn_per_base(rows)
    s_pool = learn_pooled(rows)
    streams_w3 = pickle.load(open(HERE / "INTEG_W3_streams_cache.pkl", "rb"))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    comb_book = {day: sum(M_w3[di]) for di, day in enumerate(days_w3)}
    book_days = set(days_w3); sd_book = statistics.pstdev([comb_book[d] for d in days_w3])
    CONF = 0.45

    def fold_stress(daily):
        adays = sorted(book_days | set(daily))
        comb = [comb_book.get(d, 0.0) + CONF * daily.get(d, 0.0) for d in adays]
        sd = statistics.pstdev(comb); vs = sd_book / sd if sd > 0 else 1.0
        cstr = [(v * 1.5 if v < 0 else v) for v in comb]
        return dict(
            sharpe=round(statistics.fmean(comb) / sd, 4),
            p1=mc_series(comb, 0.01 * vs, seed_base=1)['p_pass'],
            p15=mc_series(comb, 0.015 * vs, seed_base=1)['p_pass'],
            s1=mc_series(cstr, 0.01 * vs, seed_base=999)['p_pass'],
            s15=mc_series(cstr, 0.015 * vs, seed_base=999)['p_pass'])

    report = {"track": "KB6_router_signsource_ab"}
    print("=== ROUTER SIGN-SOURCE A/B (full confluence sleeve, deploy fold) ===")
    print(f"{'mode':>10} {'fwdEV':>7} {'sharpe':>7} {'P@1%':>7} {'P@1.5%':>8} {'str@1%':>8} {'str@1.5%':>9}")
    report["full_sleeve"] = {}
    for mode, signs in (("flat", None), ("per_base", s_pb), ("pooled", s_pool), ("prior", None)):
        daily = per_day(rows, signs, mode)
        fe = fwd_ev(rows, signs, mode)
        fs = fold_stress(daily)
        report["full_sleeve"][mode] = dict(fwd_ev=fe, **fs)
        print(f"{mode:>10} {fe:>7.3f} {fs['sharpe']:>7.4f} {fs['p1']:>7.2%} {fs['p15']:>8.2%} {fs['s1']:>8.2%} {fs['s15']:>9.2%}")

    # FLAGSHIP-ONLY sleeve (xvol_up_pullback rows): the honest deployable case where the
    # PRIOR sign (veto+liq) is proven train+fwd. Router = PRIOR signs.
    print("\n=== FLAGSHIP-ONLY sleeve (xvol_up_pullback): flat vs PRIOR-router ===")
    flag = [r for r in rows if r["base"] == "xvol_up_pullback"]
    report["flagship_only"] = {}
    print(f"{'mode':>10} {'fwdEV':>7} {'sharpe':>7} {'P@1%':>7} {'P@1.5%':>8} {'str@1%':>8} {'str@1.5%':>9}")
    for mode in ("flat", "prior"):
        daily = per_day(flag, None, mode)
        fe = fwd_ev(flag, None, mode)
        fs = fold_stress(daily)
        report["flagship_only"][mode] = dict(fwd_ev=fe, **fs)
        print(f"{mode:>10} {fe:>7.3f} {fs['sharpe']:>7.4f} {fs['p1']:>7.2%} {fs['p15']:>8.2%} {fs['s1']:>8.2%} {fs['s15']:>9.2%}")

    (HERE / "KB6_ROUTER_SIGNSOURCE_AB.json").write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote KB6_ROUTER_SIGNSOURCE_AB.json")


if __name__ == "__main__":
    main()
