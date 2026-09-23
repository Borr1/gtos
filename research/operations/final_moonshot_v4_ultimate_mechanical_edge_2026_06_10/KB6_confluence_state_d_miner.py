"""KB6_confluence_state_d_miner.py — RE-MINE cross-layer confluence under the DEPLOYED STATE_D exit.
=================================================================================================
TRACK (KB6): The KB5 cross-layer confluence winners (leader-impulse VETO `ll_align=none` /
`ll_impulse=none`, session/regime-stack, VP-acceptance `vp_loc`) were scored at FIXED 3R
(sub.outcome -> geometry_lib.simulate_detail, target=3R, stop=1R). But the DEPLOYED book exits
via the STATE_D vol-tiered scale-out (compounding_sleeve.exit_state_d: 50% leg @ scaleR + BE
runner + deep fixed target, no trail). A cell's odds at fixed-3R need NOT survive the real exit:
scale-out caps the right tail and converts many full-runners into half-size partials, while the
BE-runner kills the -1R left tail of the scaled trades. So we must re-label every base-cell
signal with BOTH labels and re-test whether the confluence overlays REMAIN high-odds under the
exit the book actually trades.

DISCIPLINE (inherited, enforced in code):
  - NO LOOKAHEAD. Base-cell match + every orthogonal tag at bar i is from CLOSED bars index<=i
    (substrate.build_states features, prior-day VP, train-fit regime, same-close leader z).
  - The STATE_D label is leak-free: cs.exit_state_d only reads bars j>i forward as price action,
    using sd=atr[i] (the substrate stop R-unit) and vr=cs.vol_ratio(atrs,i) (100-bar trailing).
  - FORWARD HOLDOUT MANDATORY: TRAIN(<=2024) vs FWD(2025-26) + per-YEAR + n on BOTH labels.
  - NO AVERAGES AS VERDICTS: per-condition fwd lift vs base, per-year, n-gate, phi, perm-null.
  - SIZE BY CONFIDENCE, DELETE NOTHING: a condition that decays under STATE_D is mapped (where/
    when it survives), not discarded.

R-UNIT CONSISTENCY (why the two labels are comparable):
  substrate stop_atr=1.0 -> sd = 1.0*atr.  exit_state_d uses the SAME sd=atr as the 1R unit and
  raw w1.cost_for (substrate scales cost by 1/stop_atr = 1/1.0 = raw). So both labels are in the
  same R-unit (1R = 1 ATR move) and the same cost basis. The ONLY difference is the exit rule.
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
import compounding_sleeve as cs

# reuse the exact leak-free orthogonal-engine extractors + base cells from KB5
import KB5_cross_layer_miner as KB5

TRAIN_MAX = 2024
FWD_MIN = 2025
random.seed(7)


# --------------------------------------------------------------------------- #
# The miner: one leak-free pass per symbol. Each base-cell signal is labelled
# with BOTH the fixed-3R outcome (sub.outcome) AND the STATE_D scale-out exit
# (cs.exit_state_d). All orthogonal tags identical to KB5 (leak-free).
# --------------------------------------------------------------------------- #
def mine(symbols=None, verbose=True):
    syms = symbols or [s for s in w1.SYMBOLS if KB5.AC.get(s)]
    leader_sigs = KB5.build_leader_signals()
    signals = {b: [] for b in KB5.BASE_CELLS}
    for s in syms:
        built = sub.build_states(s)
        if built is None:
            if verbose: print(f"  {s:14} skip", flush=True)
            continue
        T, B, A, states = built
        closes = np.array([b.c for b in B], dtype=float)
        atrs_np = np.array(A, dtype=float)
        atrs_list = list(A)                       # cs.vol_ratio wants a plain sequence
        cost = w1.cost_for(s)
        n = len(B)
        model, arch = KB5.build_regime_model(s, B, closes, atrs_np, T)
        profs, days = KB5.build_vp(s)
        lm = KB5.build_liquidity(s, T, B)
        cls = KB5.AC.get(s)
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
            matched = []
            for bname, (_, conds) in KB5.BASE_CELLS.items():
                if all(co.get(d) == v for d, v in conds.items()):
                    matched.append(bname)
            if not matched:
                continue
            # orthogonal conditions ONCE per bar (shared across matched bases)
            cd = {}
            cd.update(KB5.vp_conditions(profs, days, t, price, a))
            cd.update(KB5.regime_conditions(model, arch, B, closes, atrs_np, i))
            cd.update(KB5.leadlag_conditions(s, t, leader_sigs))
            cd["liq_sweep"] = KB5.liquidity_sweep_recent(lm, i, a, K=3)
            vr = cs.vol_ratio(atrs_list, i)
            for bname in matched:
                geom, _ = KB5.BASE_CELLS[bname]
                stop_atr = float(geom.split("|")[0][1:].split("_")[0])
                target_R = float(geom.split("|")[0][1:].split("_")[1])
                dmode = int(geom.split("|")[1].split("=")[1])
                # fixed-3R label (the KB5 scoring basis)
                R3, hit3 = sub.outcome(B, i, dmode, stop_atr, target_R, a, cost)
                # STATE_D scale-out label (the DEPLOYED exit). sd = stop_atr*atr = atr.
                sd = stop_atr * a
                ex = cs.exit_state_d(B, i, dmode, sd, vr, cost, maxbars=sub.MAXBARS)
                Rd = ex["R"]; reason = ex["reason"]
                hitd = reason in ("win_runner", "win_partial")
                # direction-relative tags
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
                signals[bname].append(dict(
                    sym=s, cls=cls, year=t.year, date=str(t)[:10], dir=dmode,
                    R3=R3, hit3=hit3, Rd=Rd, hitd=hitd, reason=reason, vr=round(vr, 3),
                    conds=bc))
            cnt["match"] += 1
        if verbose and cnt:
            print(f"  {s:14} base-matches={cnt['match']}  (regime={'y' if model else 'n'} "
                  f"vp={'y' if days else 'n'} liq={'y' if lm else 'n'})", flush=True)
    return signals


# --------------------------------------------------------------------------- #
# Aggregation over BOTH labels (R3 = fixed 3R, Rd = STATE_D).
# --------------------------------------------------------------------------- #
def _agg(rs, key):
    n = len(rs)
    if n == 0:
        return dict(n=0, meanR=None, win=None, odds=None)
    s = sum(r[key] for r in rs)
    w = sum(1 for r in rs if r[key] > 0)
    hk = "hit3" if key == "R3" else "hitd"
    h = sum(1 for r in rs if r[hk])
    return dict(n=n, meanR=round(s / n, 4), win=round(100 * w / n, 1), odds=round(h / n, 4))


def _split(rs, key):
    tr = [r for r in rs if r["year"] <= TRAIN_MAX]
    fw = [r for r in rs if r["year"] >= FWD_MIN]
    return _agg(tr, key), _agg(fw, key)


def _per_year(rs, key):
    by = collections.defaultdict(list)
    for r in rs:
        by[r["year"]].append(r)
    return {str(y): _agg(by[y], key) for y in sorted(by)}


def _phi(rs, cond_key, cond_val, outcome_key):
    """phi between condition-indicator and win-indicator within the base population
    (interpretability: >0 co-moves with winning under THIS label)."""
    xs = [1 if r["conds"].get(cond_key) == cond_val else 0 for r in rs]
    ys = [1 if r[outcome_key] > 0 else 0 for r in rs]
    n = len(xs)
    if n < 10:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs); sy = sum((y - my) ** 2 for y in ys)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((xs[k] - mx) * (ys[k] - my) for k in range(n))
    return round(cov / math.sqrt(sx * sy), 4)


def _perm_null(rs, cond_key, cond_val, observed_lift, outcome_key, K=2000):
    base_mean = sum(r[outcome_key] for r in rs) / len(rs)
    Rs = [r[outcome_key] for r in rs]
    labels = [1 if r["conds"].get(cond_key) == cond_val else 0 for r in rs]
    nsub = sum(labels)
    if nsub == 0 or nsub == len(rs):
        return None
    ge = 0
    idx = list(range(len(rs)))
    for _ in range(K):
        random.shuffle(idx)
        sub_mean = sum(Rs[idx[k]] for k in range(nsub)) / nsub
        if (sub_mean - base_mean) >= observed_lift - 1e-12:
            ge += 1
    return round(ge / K, 4)


# The cross-layer WINNER overlays we are re-testing (from KB5_FRONTIER.json),
# expressed as (base_cell_name, cond_dim, cond_val). These are the leader-veto,
# session/regime-stack and VP-acceptance winners.
WINNER_OVERLAYS = [
    ("xvol_up_pullback_L3R",     "ll_align",    "none"),
    ("xvol_up_pullback_L3R",     "ll_impulse",  "none"),
    ("xvol_up_conflict_L3R",     "ll_align",    "none"),
    ("xvol_up_conflict_L3R",     "ll_impulse",  "none"),
    ("xvol_up_conflict_mid_L3R", "ll_align",    "none"),
    ("xvol_up_conflict_mid_L3R", "ll_impulse",  "none"),
    ("mid_dn_revert_ny_L3R",     "vp_loc",      "above_va"),
    ("xvol_up_conflict_L3R",     "vp_loc",      "above_va"),
    ("xvol_up_conflict_L3R",     "vp_poc_side", "above_poc"),
    # regime/session-stack probes (these were the anti-confluent / mixed cells —
    # we re-check whether STATE_D rescues or kills them):
    ("xvol_up_conflict_L3R",     "regime",      "calm_chop"),
    ("xvol_up_pullback_L3R",     "regime",      "calm_chop"),
]

COND_DIMS = ["vp_loc", "vp_poc_side", "vp_void", "regime", "hurst",
             "ll_impulse", "ll_align", "liq_sweep", "liq_align"]


def analyze(signals, min_side_n=25):
    """For each base cell, report base stats under BOTH labels, plus every
    orthogonal condition's lift under BOTH labels (so we can see the exit-shift)."""
    out = {}
    for bname, rs in signals.items():
        rec = {"cell": KB5.BASE_CELLS[bname][0], "n_total": len(rs), "conditions": {}}
        for key, tag in (("R3", "fixed3R"), ("Rd", "state_d")):
            btr, bfw = _split(rs, key)
            rec[f"base_{tag}_train"] = btr
            rec[f"base_{tag}_fwd"] = bfw
            rec[f"base_{tag}_per_year"] = _per_year(rs, key)
        # STATE_D exit-reason mix on the base (diagnostic of why odds shift)
        rmix = collections.Counter(r["reason"] for r in rs)
        rec["state_d_reason_mix"] = dict(rmix)
        for dim in COND_DIMS:
            vals = sorted({r["conds"].get(dim) for r in rs if r["conds"].get(dim) is not None})
            for v in vals:
                if v == "na":
                    continue
                subset = [r for r in rs if r["conds"].get(dim) == v]
                # n-gate on either side
                ntr = sum(1 for r in subset if r["year"] <= TRAIN_MAX)
                nfw = sum(1 for r in subset if r["year"] >= FWD_MIN)
                if ntr < min_side_n and nfw < min_side_n:
                    continue
                cell = {"reason_mix": dict(collections.Counter(r["reason"] for r in subset))}
                for key, tag in (("R3", "fixed3R"), ("Rd", "state_d")):
                    base_fwd_mean = (rec[f"base_{tag}_fwd"]["meanR"] or 0.0)
                    base_tr_mean = (rec[f"base_{tag}_train"]["meanR"] or 0.0)
                    str_, sfw = _split(subset, key)
                    fwd_lift = (sfw["meanR"] - base_fwd_mean) if sfw["meanR"] is not None else None
                    tr_lift = (str_["meanR"] - base_tr_mean) if str_["meanR"] is not None else None
                    phi = _phi(rs, dim, v, "R3" if key == "R3" else "Rd")
                    pn = None
                    if fwd_lift is not None and sfw["n"] >= min_side_n:
                        fwd_rs = [r for r in rs if r["year"] >= FWD_MIN]
                        pn = _perm_null(fwd_rs, dim, v, fwd_lift, key, K=2000)
                    cell[tag] = {
                        "cond_train": str_, "cond_fwd": sfw,
                        "cond_per_year": _per_year(subset, key),
                        "tr_lift_vs_base": round(tr_lift, 4) if tr_lift is not None else None,
                        "fwd_lift_vs_base": round(fwd_lift, 4) if fwd_lift is not None else None,
                        "phi_cond_vs_win": phi, "perm_null_p_fwd": pn,
                    }
                rec["conditions"][f"{dim}={v}"] = cell
        out[bname] = rec
    return out


def main():
    t0 = time.time()
    print("KB6 cross-layer confluence RE-MINE under STATE_D exit — leak-free single pass\n")
    signals = mine()
    print(f"\nmined base signals in {round(time.time()-t0,1)}s:")
    for b, rs in signals.items():
        tr = sum(1 for r in rs if r["year"] <= TRAIN_MAX); fw = sum(1 for r in rs if r["year"] >= FWD_MIN)
        m3 = sum(r["R3"] for r in rs) / len(rs) if rs else 0
        md = sum(r["Rd"] for r in rs) / len(rs) if rs else 0
        print(f"  {b:28} total={len(rs):5d}  train={tr:5d} fwd={fw:5d}  meanR3={m3:+.3f} meanRd={md:+.3f}")
    res = analyze(signals)
    # also dump the raw labelled signals (for the materialize+corr step)
    raw = {b: [dict(sym=r["sym"], date=r["date"], year=r["year"], dir=r["dir"],
                    R3=r["R3"], Rd=r["Rd"], reason=r["reason"], conds=r["conds"]) for r in rs]
           for b, rs in signals.items()}
    (HERE / "KB6_CONFLUENCE_STATE_D_RAW.json").write_text(json.dumps(raw, default=str))
    out_path = HERE / "KB6_CONFLUENCE_STATE_D_RESULT.json"
    out_path.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {out_path.name} + KB6_CONFLUENCE_STATE_D_RAW.json  ({round(time.time()-t0,1)}s total)")
    return res, signals


if __name__ == "__main__":
    main()
