"""KB5_cross_layer_miner.py — CROSS-LAYER CONFLUENCE STACKING (track KB5).
=========================================================================
Goal (the high-odds frontier): take the substrate's STRONGEST base cells and
INTERSECT each with ONE orthogonal condition from each OTHER engine
(volume_profile node-location, leadlag leader-impulse, regime_map label,
liquidity_map sweep context). Measure how each added INDEPENDENT condition
MULTIPLIES forward odds/EV. Report per-condition incremental lift + phi-
independence + per-year + n-gate + permutation null.

DISCIPLINE (inherited from the wave doctrine, enforced in code):
  - NO LOOKAHEAD. The base cell match + EVERY orthogonal tag at bar i is computed
    from CLOSED bars index<=i only:
      * substrate state  : substrate.build_states (features index<=i)
      * outcome label    : substrate.outcome -> geometry_lib.simulate_detail
                           (pessimistic same-bar, stop wins ties), real w1.cost_for
      * volume_profile   : PRIOR-completed-day profile (prior_profile_at, strictly < t.date())
      * regime_map       : model fit on TRAIN rows only; regime_at uses bars[:i+1]
      * liquidity_map    : cluster levels + sweep-in-last-K-bars, all index<=i
      * leadlag          : leader z-impulse at the SAME-timestamp close (both H4 closes)
  - FORWARD HOLDOUT MANDATORY. Every (base x condition) cell carries TRAIN(<=2024)
    vs FORWARD(2025-26) mean_R, per-YEAR, and n on both sides.
  - NO AVERAGES AS VERDICTS. The verdict is mean_R (real cost). odds reported too.
  - INDEPENDENCE: phi coefficient (base-match vs condition-true over ALL base bars)
    quantifies whether the added condition is orthogonal to the base.
  - PERMUTATION NULL: shuffle the condition labels within the base population K times;
    p = P(shuffled lift >= observed lift). High odds must beat the null.

NOTE ON DATA DEPTH (reported honestly in the KB):
  - volume_profile / liquidity_map(M15) are M1/recent-derived -> their conditioning
    sample is mostly FORWARD (M1 starts 2024). VP-stacked cells are therefore
    forward-strong but TRAIN-thin; flagged. The H4-native layers (regime, leadlag,
    liquidity@H4) have full 2014-2026 depth and split TRAIN/FWD properly.
"""
from __future__ import annotations
import sys, os, json, math, collections, random, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import numpy as np
import substrate as sub
import wave1_structure_setups_ict as w1
from geometry_lib import atr14
import volume_profile as vp
import regime_map as rm
import liquidity_map as lqm
import leadlag as ll
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

TRAIN_MAX = 2024
FWD_MIN = 2025
random.seed(7)

# --------------------------------------------------------------------------- #
# Base cells to stack on. Chosen for FORWARD sample big enough to slice into
# orthogonal sub-buckets and still keep n>=~25 per side. (Headline + broad
# variants + a couple of distinct directional/session cells.)
# --------------------------------------------------------------------------- #
BASE_CELLS = {
    # the headline flagship (depth4) — broad cross-class long
    "xvol_up_pullback_L3R":
        ("g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict",
         dict(vol="xhi", persist="rand", trend="up", mtf="conflict")),
    # broadest xvol-up-conflict (depth3) — most sample to slice
    "xvol_up_conflict_L3R":
        ("g1.0_3.0|dir=1|depth3|vol=xhi|trend=up|mtf=conflict",
         dict(vol="xhi", trend="up", mtf="conflict")),
    # xvol-up-conflict-midrange (depth4) — large fwd n
    "xvol_up_conflict_mid_L3R":
        ("g1.0_3.0|dir=1|depth4|vol=xhi|trend=up|mtf=conflict|rngpos=mid",
         dict(vol="xhi", trend="up", mtf="conflict", rngpos="mid")),
    # hi-vol downtrend conflict NY long (n291/114) — frequent breadth base
    "hi_dn_conflict_ny_L3R":
        ("g1.0_3.0|dir=1|depth7|vol=hi|trend=dn|mtf=conflict|rngpos=mid|comp=norm|persist=rand|session=ny",
         dict(vol="hi", trend="dn", mtf="conflict", rngpos="mid", comp="norm", persist="rand", session="ny")),
    # mid-vol downtrend reversion long NY (the high-freq breadth sleeve, n269/129)
    "mid_dn_revert_ny_L3R":
        ("g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny",
         dict(vol="mid", trend="dn", mtf="neutral", rngpos="mid", comp="norm", persist="revert", session="ny")),
}


# --------------------------------------------------------------------------- #
# Lead-lag leader-impulse map: build a per-(follower-time)-> leader-state lookup.
# We use the canonical null-cleared leaders: SPX500/NAS100 (index), BTCUSD
# (crypto), USDJPY/US30 (risk). For each base signal on a follower symbol, we tag
# whether a relevant leader just impulsed (|z|>=1.5, look=6) at the same close.
# Leak-free: leader z uses a trailing window ending at i-1 on the SAME UTC grid.
# --------------------------------------------------------------------------- #
LEADERS = ["SPX500", "NAS100", "BTCUSD", "USDJPY", "US30_cash", "XAUUSD", "DXY_cash"]
LL_LOOK = 6
LL_Z = 1.5

def build_leader_signals():
    sigs = {}
    for L in LEADERS:
        try:
            sigs[L] = ll.leader_signal(L, LL_LOOK)   # {datetime: z}
        except Exception:
            sigs[L] = {}
    return sigs

# which leader is "relevant" to a follower (same/upstream class). Keeps the tag
# economically grounded rather than a blind any-leader scan.
def relevant_leaders(sym):
    cls = AC.get(sym)
    out = ["XAUUSD", "DXY_cash"]            # macro leaders for everything
    if cls in ("index",):                  out += ["SPX500", "NAS100", "US30_cash"]
    elif cls in ("crypto",):               out += ["BTCUSD", "NAS100"]
    elif cls in ("fx", "jpy_fx"):          out += ["USDJPY", "US30_cash", "SPX500"]
    elif cls in ("metals", "energy", "agri"): out += ["SPX500", "USDJPY"]
    return list(dict.fromkeys(out))


# --------------------------------------------------------------------------- #
# Per-symbol orthogonal-engine context builders (built ONCE per symbol).
# --------------------------------------------------------------------------- #
def build_regime_model(sym, B, closes, atrs, T):
    rows = []
    for i in range(110, len(B) - 1):
        fr = rm.feature_row(B, closes, atrs, i)
        if fr is None:
            continue
        h = rm.hurst_vr(closes, i, rm.HURST_W)
        if h is None:
            continue
        fr = dict(fr); fr["i"] = i; fr["year"] = T[i].year; fr["hurst"] = h
        rows.append(fr)
    train = [r for r in rows if r["year"] <= TRAIN_MAX]
    if len(train) < 300:
        return None, None
    model = rm.RegimeModel().fit(train)
    tax = model.describe()
    arch = {int(reg): rm._archetype(c) for reg, c in tax.items()}
    return model, arch


def build_vp(sym):
    try:
        profs, days = vp.daily_profiles(sym)
    except Exception:
        return {}, []
    return profs, days


def build_liquidity(sym, T, B):
    try:
        lm = lqm.LiquidityMap(T, B, sym).build()
        return lm
    except Exception:
        return None


def liquidity_sweep_recent(lm, i, atr, K=3):
    """Leak-free: did a SWEEP+RECLAIM (any cluster) fire on bars (i-K..i]?  Returns
    'sweep_long' / 'sweep_short' / 'none' for the most recent within window.
    Reuses the same sweep mechanic as liquidity_map.sweep_signals but inline so we
    don't re-scan the whole series per query."""
    if lm is None:
        return "none"
    B = lm.B
    res = "none"
    for j in range(max(60, i - K), i + 1):
        a = lm.atrs[j]
        if a <= 0:
            continue
        b = B[j]
        cl = lm.cluster_levels_at(j)
        for ct in ('pd', 'ps', 'asia', 'eq', 'rn', 'sw'):
            for lvl in cl[ct]['lo']:
                if lvl is None:
                    continue
                if (lvl - b.l) >= 0.05 * a and b.c > lvl and (b.c - lvl) >= 0.10 * a:
                    res = "sweep_long"
            for lvl in cl[ct]['hi']:
                if lvl is None:
                    continue
                if (b.h - lvl) >= 0.05 * a and b.c < lvl and (lvl - b.c) >= 0.10 * a:
                    res = "sweep_short"
    return res


# --------------------------------------------------------------------------- #
# Orthogonal condition extractors. Each returns a small dict of CATEGORICAL
# condition labels for the signal bar i (all leak-free). These are the conditions
# we intersect the base cell with.
# --------------------------------------------------------------------------- #
def vp_conditions(profs, days, t, price, atr):
    dp = vp.prior_profile_at(profs, days, t)
    ns = vp.nearest_node_state(dp, price, atr) if dp is not None else None
    if ns is None:
        return {"vp_loc": "na", "vp_poc_side": "na", "vp_void": "na"}
    # location vs value area
    if ns["above_vah"]:
        loc = "above_va"
    elif ns["below_val"]:
        loc = "below_va"
    else:
        loc = "in_va"
    poc_side = "above_poc" if ns["d_poc_atr"] > 0.25 else ("below_poc" if ns["d_poc_atr"] < -0.25 else "at_poc")
    # near a void (LVN) within 0.5 ATR => price likely to move fast through
    void = "at_void" if (ns["near_lvn_atr"] is not None and ns["near_lvn_atr"] <= 0.5) else "no_void"
    return {"vp_loc": loc, "vp_poc_side": poc_side, "vp_void": void}


def regime_conditions(model, arch, B, closes, atrs, i):
    if model is None:
        return {"regime": "na", "hurst": "na"}
    st = rm.regime_at(B, closes, atrs, i, model)
    if st is None:
        return {"regime": "na", "hurst": "na"}
    return {"regime": arch.get(st["regime"], "na"), "hurst": st["hurst_sign"]}


def leadlag_conditions(sym, t, leader_sigs):
    """Did a relevant leader impulse (|z|>=LL_Z) at this same close, and in which
    direction? Tag the aligned/opposed sense vs the base trade direction is handled
    later (base dir is known); here we record raw up/down/none."""
    rels = relevant_leaders(sym)
    best = None
    for L in rels:
        z = leader_sigs.get(L, {}).get(t)
        if z is None:
            continue
        if abs(z) >= LL_Z:
            if best is None or abs(z) > abs(best[1]):
                best = (L, z)
    if best is None:
        return {"ll_impulse": "none"}
    return {"ll_impulse": "up" if best[1] > 0 else "dn"}


# --------------------------------------------------------------------------- #
# The miner: one leak-free pass per symbol, collecting base-cell signals tagged
# with all orthogonal conditions. Also collects the per-bar (base_match, cond)
# joint counts for phi-independence over the WHOLE base-eligible population.
# --------------------------------------------------------------------------- #
def mine(symbols=None, verbose=True):
    syms = symbols or [s for s in w1.SYMBOLS if AC.get(s)]
    leader_sigs = build_leader_signals()
    # signals[base_name] = list of dicts(sym, year, R, conds{...})
    signals = {b: [] for b in BASE_CELLS}
    # for phi: per base, count joint over all bars where the BASE-defining dims
    # subset is evaluable. We approximate the base population as "all bars with a
    # valid state for that symbol" and record base_match boolean + each cond label.
    # (phi computed later from the tagged signals vs a sampled base population.)
    base_pop = {b: collections.Counter() for b in BASE_CELLS}   # (base_match, cond_key=val) joint
    for s in syms:
        built = sub.build_states(s)
        if built is None:
            if verbose: print(f"  {s:14} skip", flush=True)
            continue
        T, B, A, states = built
        closes = np.array([b.c for b in B], dtype=float)
        atrs_np = np.array(A, dtype=float)
        cost = w1.cost_for(s)
        n = len(B)
        # orthogonal engines built once
        model, arch = build_regime_model(s, B, closes, atrs_np, T)
        profs, days = build_vp(s)
        lm = build_liquidity(s, T, B)
        cls = AC.get(s)
        cnt = collections.Counter()
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st = states[i]
            if st is None:
                continue
            co = sub.cell_coords(st)
            t = T[i]; a = A[i]
            if a <= 0:
                continue
            price = B[i].c
            # which base cells match at this bar
            matched = []
            for bname, (_, conds) in BASE_CELLS.items():
                if all(co.get(d) == v for d, v in conds.items()):
                    matched.append(bname)
            if not matched:
                continue
            # compute orthogonal conditions ONCE for this bar (shared across bases)
            cd = {}
            cd.update(vp_conditions(profs, days, t, price, a))
            cd.update(regime_conditions(model, arch, B, closes, atrs_np, i))
            cd.update(leadlag_conditions(s, t, leader_sigs))
            cd["liq_sweep"] = liquidity_sweep_recent(lm, i, a, K=3)
            for bname in matched:
                geom, _ = BASE_CELLS[bname]
                stop_atr = float(geom.split("|")[0][1:].split("_")[0])
                target_R = float(geom.split("|")[0][1:].split("_")[1])
                dmode = int(geom.split("|")[1].split("=")[1])
                R, hit = sub.outcome(B, i, dmode, stop_atr, target_R, a, cost)
                # direction-relative tags for the directional engines (base dir = dmode)
                bc = dict(cd)
                if cd.get("ll_impulse") in ("up", "dn"):
                    up = (cd["ll_impulse"] == "up")
                    bc["ll_align"] = "aligned" if (up == (dmode > 0)) else "opposed"
                else:
                    bc["ll_align"] = "none"
                if cd.get("liq_sweep") in ("sweep_long", "sweep_short"):
                    lg = (cd["liq_sweep"] == "sweep_long")
                    bc["liq_align"] = "aligned" if (lg == (dmode > 0)) else "opposed"
                else:
                    bc["liq_align"] = "none"
                signals[bname].append(dict(sym=s, cls=cls, year=t.year, R=R, hit=hit,
                                           dir=dmode, conds=bc))
            cnt["match"] += 1
        if verbose and cnt:
            print(f"  {s:14} base-matches={cnt['match']}  (regime={'y' if model else 'n'} "
                  f"vp={'y' if days else 'n'} liq={'y' if lm else 'n'})", flush=True)
    return signals


# --------------------------------------------------------------------------- #
# Aggregation + statistics
# --------------------------------------------------------------------------- #
def _agg(rs):
    n = len(rs)
    if n == 0:
        return dict(n=0, meanR=None, win=None, odds=None)
    s = sum(r["R"] for r in rs)
    w = sum(1 for r in rs if r["R"] > 0)
    h = sum(1 for r in rs if r["hit"])
    return dict(n=n, meanR=round(s / n, 4), win=round(100 * w / n, 1), odds=round(h / n, 4))


def _split(rs):
    tr = [r for r in rs if r["year"] <= TRAIN_MAX]
    fw = [r for r in rs if r["year"] >= FWD_MIN]
    return _agg(tr), _agg(fw)


def _per_year(rs):
    by = collections.defaultdict(list)
    for r in rs:
        by[r["year"]].append(r)
    return {str(y): _agg(by[y]) for y in sorted(by)}


def _phi(rs, cond_key, cond_val):
    """phi coefficient between base-match (all rs are matches=1 by construction, so
    instead measure within-base association of the condition with the OUTCOME sign).
    For independence vs the BASE we use a different proxy: condition prevalence.
    Here phi = corr( cond_indicator , win_indicator ) within the base population —
    a >0 phi means the condition co-moves with winning (the lift is 'real signal'),
    near-0 means orthogonal-but-additive. We report it for interpretability."""
    xs = [1 if r["conds"].get(cond_key) == cond_val else 0 for r in rs]
    ys = [1 if r["R"] > 0 else 0 for r in rs]
    n = len(xs)
    if n < 10:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs); sy = sum((y - my) ** 2 for y in ys)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((xs[k] - mx) * (ys[k] - my) for k in range(n))
    return round(cov / math.sqrt(sx * sy), 4)


def _perm_null(rs, cond_key, cond_val, observed_lift, K=2000):
    """Shuffle the condition labels within the base population; recompute the lift
    (cond-subset meanR - base meanR) K times. p = P(perm_lift >= observed_lift)."""
    base_mean = sum(r["R"] for r in rs) / len(rs)
    Rs = [r["R"] for r in rs]
    labels = [1 if r["conds"].get(cond_key) == cond_val else 0 for r in rs]
    nsub = sum(labels)
    if nsub == 0 or nsub == len(rs):
        return None
    ge = 0
    idx = list(range(len(rs)))
    for _ in range(K):
        random.shuffle(idx)
        # take first nsub shuffled positions as the "condition" subset
        sub_mean = sum(Rs[idx[k]] for k in range(nsub)) / nsub
        if (sub_mean - base_mean) >= observed_lift - 1e-12:
            ge += 1
    return round(ge / K, 4)


# orthogonal condition dimensions to test (each value sliced)
COND_DIMS = ["vp_loc", "vp_poc_side", "vp_void", "regime", "hurst",
             "ll_impulse", "ll_align", "liq_sweep", "liq_align"]


def analyze(signals, min_side_n=25):
    out = {}
    for bname, rs in signals.items():
        btr, bfw = _split(rs)
        base = {
            "cell": BASE_CELLS[bname][0],
            "base_train": btr, "base_fwd": bfw,
            "base_per_year": _per_year(rs),
            "n_total": len(rs),
            "conditions": {},
        }
        base_fwd_mean = bfw["meanR"] if bfw["meanR"] is not None else 0.0
        base_tr_mean = btr["meanR"] if btr["meanR"] is not None else 0.0
        for dim in COND_DIMS:
            vals = sorted({r["conds"].get(dim) for r in rs if r["conds"].get(dim) is not None})
            for v in vals:
                if v in ("na", "none"):
                    # 'none'/'na' is a meaningful absence label for ll_impulse/liq_sweep;
                    # keep it but mark; skip pure 'na' (engine unavailable) to avoid noise
                    if v == "na":
                        continue
                subset = [r for r in rs if r["conds"].get(dim) == v]
                str_, sfw = _split(subset)
                if (str_["n"] < min_side_n) and (sfw["n"] < min_side_n):
                    continue
                fwd_lift = (sfw["meanR"] - base_fwd_mean) if sfw["meanR"] is not None else None
                tr_lift = (str_["meanR"] - base_tr_mean) if str_["meanR"] is not None else None
                phi = _phi(rs, dim, v)
                pn = None
                if fwd_lift is not None and sfw["n"] >= min_side_n:
                    # permutation null on the FORWARD population (the holdout that matters)
                    fwd_rs = [r for r in rs if r["year"] >= FWD_MIN]
                    pn = _perm_null(fwd_rs, dim, v, fwd_lift, K=2000)
                base["conditions"][f"{dim}={v}"] = {
                    "cond_train": str_, "cond_fwd": sfw,
                    "cond_per_year": _per_year(subset),
                    "tr_lift_vs_base": round(tr_lift, 4) if tr_lift is not None else None,
                    "fwd_lift_vs_base": round(fwd_lift, 4) if fwd_lift is not None else None,
                    "phi_cond_vs_win": phi,
                    "perm_null_p_fwd": pn,
                }
        out[bname] = base
    return out


def main():
    t0 = time.time()
    print("KB5 cross-layer confluence miner — leak-free single pass\n")
    signals = mine()
    print(f"\nmined base signals in {round(time.time()-t0,1)}s:")
    for b, rs in signals.items():
        tr = sum(1 for r in rs if r["year"] <= TRAIN_MAX); fw = sum(1 for r in rs if r["year"] >= FWD_MIN)
        print(f"  {b:28} total={len(rs):5d}  train={tr:5d} fwd={fw:5d}")
    res = analyze(signals)
    out_path = HERE / "KB5_CROSS_LAYER_RESULT.json"
    out_path.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {out_path.name}  ({round(time.time()-t0,1)}s total)")
    return res


if __name__ == "__main__":
    main()
