"""KB6_veto_other_bases.py — track KB6 (confluence frontier 2).

GOAL 1: the leader-impulse VETO (ll_impulse=none) is BASE-SPECIFIC (KB5 found it
lifts the xvol-up-pullback long family but is forward-NEGATIVE on mid_dn_revert).
Mine it (and EVERY orthogonal condition) on the OTHER substrate long/short bases
from SUBSTRATE_TOP_EDGES.json to find WHERE ELSE it (or another orthogonal gate)
lifts forward EV. Same leak-free single-pass tagger as KB5 (reused verbatim via XL).

GOAL 2: mine DEEPER stacks (2/3-way: veto x session x regime x VP) per base, report
any higher-odds n-gated forward-validated cells.

DISCIPLINE (identical to KB5, enforced in code via XL):
  - NO LOOKAHEAD: base-state + all orthogonal tags at bar i from CLOSED bars index<=i;
    outcome via sub.outcome->geometry_lib.simulate_detail, real w1.cost_for.
  - FORWARD HOLDOUT: TRAIN(<=2024) vs FORWARD(2025-26) + per-year + n both sides.
  - NO AVERAGES AS VERDICTS: verdict = forward mean_R (real cost).
  - PERM NULL: shuffle condition labels within FORWARD base pop; p=P(shuf lift>=obs).
  - SIGN per class (W4/W5 lesson): conditions can be anti-confluent; report the sign.
"""
from __future__ import annotations
import sys, os, json, math, collections, random, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import numpy as np
import substrate as sub
import wave1_structure_setups_ict as w1
import KB5_cross_layer_miner as XL          # reuse the leak-free tagger verbatim
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

TRAIN_MAX = 2024
FWD_MIN = 2025
random.seed(11)

# --------------------------------------------------------------------------- #
# OTHER substrate bases (NOT the 3 xvol-up cells KB5 already mined). Chosen from
# SUBSTRATE_TOP_EDGES.json for fwd n>=~40 so we can slice into orthogonal buckets.
# Each value: (geom_cell_string, {dim:val} base-defining coords).
# --------------------------------------------------------------------------- #
def _coords(cell):
    """parse 'g1.0_3.0|dir=1|depth7|vol=...|...' -> {dim:val} of the substrate dims."""
    d = {}
    for tok in cell.split("|"):
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k in ("vol", "trend", "mtf", "rngpos", "comp", "persist", "session"):
                d[k] = v
    return d

OTHER_BASES = {
    # ---- SHORTS (the veto has never been tested on a short base) ----
    "lo_up_conflict_trend_london_S3R":
        "g1.0_3.0|dir=-1|depth7|vol=lo|trend=up|mtf=conflict|rngpos=mid|comp=norm|persist=trend|session=london",
    "hi_flat_aligned_revert_asia_S3R":
        "g1.0_3.0|dir=-1|depth7|vol=hi|trend=flat|mtf=aligned|rngpos=mid|comp=norm|persist=revert|session=asia",
    "mid_dn_aligned_expand_asia_S3R":
        "g1.0_3.0|dir=-1|depth7|vol=mid|trend=dn|mtf=aligned|rngpos=mid|comp=expand|persist=rand|session=asia",
    "hi_flat_aligned_revert_london_S3R":
        "g1.0_3.0|dir=-1|depth7|vol=hi|trend=flat|mtf=aligned|rngpos=mid|comp=norm|persist=revert|session=london",
    "lo_dn_neutral_rand_asia_S3R":
        "g1.0_3.0|dir=-1|depth7|vol=lo|trend=dn|mtf=neutral|rngpos=low|comp=norm|persist=rand|session=asia",
    "xvol_flat_revert_neutral_S2R":
        "g1.0_2.0|dir=-1|depth4|vol=xhi|persist=revert|trend=flat|mtf=neutral",
    "hi_flat_aligned_revert_depth4_S3R":
        "g1.0_3.0|dir=-1|depth4|vol=hi|persist=revert|trend=flat|mtf=aligned",
    # ---- OTHER LONGS (not the xvol-up-conflict family) ----
    "lo_up_aligned_coil_london_L3R":
        "g1.0_3.0|dir=1|depth7|vol=lo|trend=up|mtf=aligned|rngpos=mid|comp=coil|persist=rand|session=london",
    "xvol_up_neutral_L3R":
        "g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=neutral",
    "xvol_dn_aligned_expand_ny_L3R":
        "g1.0_3.0|dir=1|depth7|vol=xhi|trend=dn|mtf=aligned|rngpos=low|comp=expand|persist=rand|session=ny",
    "mid_up_aligned_coil_asia_L3R":
        "g1.0_3.0|dir=1|depth7|vol=mid|trend=up|mtf=aligned|rngpos=high|comp=coil|persist=rand|session=asia",
    "xvol_up_aligned_london_L3R":
        "g1.0_3.0|dir=1|depth7|vol=xhi|trend=up|mtf=aligned|rngpos=high|comp=norm|persist=rand|session=london",
    "xvol_dn_aligned_london_L3R":
        "g1.0_3.0|dir=1|depth7|vol=xhi|trend=dn|mtf=aligned|rngpos=low|comp=norm|persist=rand|session=london",
    "hi_up_neutral_ny_L3R":
        "g1.0_3.0|dir=1|depth7|vol=hi|trend=up|mtf=neutral|rngpos=high|comp=norm|persist=rand|session=ny",
}

# parse each into geom + coords
BASES = {name: (cell, _coords(cell)) for name, cell in OTHER_BASES.items()}


def _geom_of(cell):
    head = cell.split("|")[0][1:]            # 'g1.0_3.0' -> '1.0_3.0'
    stop_atr, target_R = head.split("_")
    dmode = int(cell.split("|")[1].split("=")[1])
    return float(stop_atr), float(target_R), dmode


def mine(symbols=None, verbose=True):
    syms = symbols or [s for s in w1.SYMBOLS if AC.get(s)]
    leader_sigs = XL.build_leader_signals()
    signals = {b: [] for b in BASES}
    for s in syms:
        built = sub.build_states(s)
        if built is None:
            continue
        T, B, A, states = built
        closes = np.array([b.c for b in B], dtype=float)
        atrs_np = np.array(A, dtype=float)
        cost = w1.cost_for(s)
        n = len(B)
        model, arch = XL.build_regime_model(s, B, closes, atrs_np, T)
        profs, days = XL.build_vp(s)
        lm = XL.build_liquidity(s, T, B)
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
            matched = [bn for bn, (_, conds) in BASES.items()
                       if all(co.get(d) == v for d, v in conds.items())]
            if not matched:
                continue
            cd = {}
            cd.update(XL.vp_conditions(profs, days, t, price, a))
            cd.update(XL.regime_conditions(model, arch, B, closes, atrs_np, i))
            cd.update(XL.leadlag_conditions(s, t, leader_sigs))
            cd["liq_sweep"] = XL.liquidity_sweep_recent(lm, i, a, K=3)
            # also tag substrate session (for short bases tested across sessions) + dir
            cd["sub_session"] = co.get("session", "na")
            for bname in matched:
                cell, _ = BASES[bname]
                stop_atr, target_R, dmode = _geom_of(cell)
                R, hit = sub.outcome(B, i, dmode, stop_atr, target_R, a, cost)
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
            cnt["m"] += 1
        if verbose and cnt:
            print(f"  {s:14} matches={cnt['m']}", flush=True)
    return signals


# ---- aggregation (reuse KB5 stat helpers) ---- #
_agg = XL._agg; _split = XL._split; _per_year = XL._per_year; _phi = XL._phi; _perm_null = XL._perm_null
COND_DIMS = ["vp_loc", "vp_poc_side", "regime", "hurst", "ll_impulse", "ll_align", "liq_sweep", "liq_align"]


def analyze(signals, min_side_n=25):
    out = {}
    for bname, rs in signals.items():
        btr, bfw = _split(rs)
        base = {"cell": BASES[bname][0], "base_train": btr, "base_fwd": bfw,
                "base_per_year": _per_year(rs), "n_total": len(rs), "conditions": {}}
        base_fwd_mean = bfw["meanR"] if bfw["meanR"] is not None else 0.0
        base_tr_mean = btr["meanR"] if btr["meanR"] is not None else 0.0
        fwd_rs = [r for r in rs if r["year"] >= FWD_MIN]
        for dim in COND_DIMS:
            vals = sorted({r["conds"].get(dim) for r in rs if r["conds"].get(dim) is not None})
            for v in vals:
                if v == "na":
                    continue
                subset = [r for r in rs if r["conds"].get(dim) == v]
                str_, sfw = _split(subset)
                if (str_["n"] < min_side_n) and (sfw["n"] < min_side_n):
                    continue
                fwd_lift = (sfw["meanR"] - base_fwd_mean) if sfw["meanR"] is not None else None
                tr_lift = (str_["meanR"] - base_tr_mean) if str_["meanR"] is not None else None
                pn = None
                if fwd_lift is not None and sfw["n"] >= min_side_n:
                    pn = _perm_null(fwd_rs, dim, v, fwd_lift, K=2000)
                base["conditions"][f"{dim}={v}"] = {
                    "cond_train": str_, "cond_fwd": sfw, "cond_per_year": _per_year(subset),
                    "tr_lift_vs_base": round(tr_lift, 4) if tr_lift is not None else None,
                    "fwd_lift_vs_base": round(fwd_lift, 4) if fwd_lift is not None else None,
                    "phi_cond_vs_win": _phi(rs, dim, v), "perm_null_p_fwd": pn}
        out[bname] = base
    return out


def main():
    t0 = time.time()
    print("KB6 veto-on-other-bases miner — leak-free single pass (reuses KB5 XL tagger)\n")
    signals = mine()
    print(f"\nmined in {round(time.time()-t0,1)}s:")
    for b, rs in signals.items():
        tr = sum(1 for r in rs if r["year"] <= TRAIN_MAX); fw = sum(1 for r in rs if r["year"] >= FWD_MIN)
        print(f"  {b:34} total={len(rs):5d} train={tr:5d} fwd={fw:5d}")
    res = analyze(signals)
    (HERE / "KB6_VETO_OTHER_BASES_RESULT.json").write_text(json.dumps(res, indent=1, default=str))
    # also dump raw signals for the deeper-stack + router passes (reuse, don't re-walk)
    import pickle
    pickle.dump(signals, open(HERE / "KB6_other_base_signals.pkl", "wb"))
    print(f"\nwrote KB6_VETO_OTHER_BASES_RESULT.json + KB6_other_base_signals.pkl ({round(time.time()-t0,1)}s)")
    return res


if __name__ == "__main__":
    main()
