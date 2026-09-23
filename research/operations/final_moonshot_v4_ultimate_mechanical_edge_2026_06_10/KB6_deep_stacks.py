"""KB6_deep_stacks.py — track KB6 GOAL 2: DEEPER (2/3/4-way) confluence stacks.

Take the per-base tagged signals (cached by KB5 miner re-run + KB6 miner) and mine
the deepest n-gated forward-validated INTERSECTIONS of orthogonal conditions:
  veto (ll_align=none) x VP (vp_loc) x regime (hurst) x session.
For EACH base, enumerate all 2-way and 3-way condition combos, keep those with
fwd n>=N_GATE, fwd meanR>0, both fwd years +, and a permutation null clearing.
Verdict = forward meanR (real cost). Reports the best deep cells per base.

Leak-free by construction: every tag was computed at bar i from closed bars only
(KB5_cross_layer_miner). This pass is pure aggregation over those tags — no new
feature computation, so no new leakage surface.
"""
from __future__ import annotations
import sys, json, math, collections, random, pickle, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

TRAIN_MAX = 2024
FWD_MIN = 2025
random.seed(13)
N_GATE = 22          # forward n floor for a deep cell (pocket-honest; <30 flagged)

# condition dims usable for stacking (categorical, leak-free); drop raw ll_impulse
# (use direction-relative ll_align instead). vp_poc_side correlated w/ vp_loc (note).
STACK_DIMS = ["ll_align", "vp_loc", "hurst", "regime", "liq_align", "sub_session"]


def _agg(rs):
    n = len(rs)
    if n == 0:
        return dict(n=0, meanR=None, win=None)
    s = sum(r["R"] for r in rs)
    w = sum(1 for r in rs if r["R"] > 0)
    return dict(n=n, meanR=round(s / n, 4), win=round(100 * w / n, 1))


def _split(rs):
    return (_agg([r for r in rs if r["year"] <= TRAIN_MAX]),
            _agg([r for r in rs if r["year"] >= FWD_MIN]))


def _pos_fwd_yrs(rs):
    by = collections.defaultdict(list)
    for r in rs:
        if r["year"] >= FWD_MIN:
            by[r["year"]].append(r["R"])
    yrs = sorted(by)
    pos = sum(1 for y in yrs if sum(by[y]) / len(by[y]) > 0)
    return pos, len(yrs), {str(y): round(sum(by[y]) / len(by[y]), 3) for y in yrs}


def _perm_null_combo(fwd_rs, mask_fn, observed_lift, base_mean, K=2000):
    """shuffle which rows satisfy the combo (size-preserving) within FWD pop."""
    Rs = [r["R"] for r in fwd_rs]
    labels = [1 if mask_fn(r) else 0 for r in fwd_rs]
    nsub = sum(labels)
    if nsub == 0 or nsub == len(fwd_rs):
        return None
    idx = list(range(len(fwd_rs))); ge = 0
    for _ in range(K):
        random.shuffle(idx)
        sm = sum(Rs[idx[k]] for k in range(nsub)) / nsub
        if (sm - base_mean) >= observed_lift - 1e-12:
            ge += 1
    return round(ge / K, 4)


def mine_base(rs, name, cell):
    btr, bfw = _split(rs)
    base_fwd_mean = bfw["meanR"] if bfw["meanR"] is not None else 0.0
    fwd_rs = [r for r in rs if r["year"] >= FWD_MIN]
    # collect candidate (dim,val) atoms with enough fwd sample to be worth stacking
    atoms = []
    for dim in STACK_DIMS:
        vals = collections.Counter(r["conds"].get(dim) for r in fwd_rs if r["conds"].get(dim) not in (None, "na"))
        for v, c in vals.items():
            if c >= N_GATE:               # atom must itself have fwd sample
                atoms.append((dim, v))
    results = []
    # 1-, 2-, 3-way combos (no two atoms from the same dim)
    for depth in (1, 2, 3):
        for combo in itertools.combinations(atoms, depth):
            dims = [a[0] for a in combo]
            if len(set(dims)) != depth:
                continue
            def mask(r, combo=combo):
                return all(r["conds"].get(d) == v for d, v in combo)
            sub = [r for r in rs if mask(r)]
            str_, sfw = _split(sub)
            if sfw["n"] < N_GATE:
                continue
            if sfw["meanR"] is None or sfw["meanR"] <= base_fwd_mean:
                continue
            pos, tot, peryr = _pos_fwd_yrs(sub)
            if tot >= 2 and pos < tot:    # require all fwd years + (strict for deep cells)
                continue
            lift = sfw["meanR"] - base_fwd_mean
            pn = _perm_null_combo(fwd_rs, mask, lift, base_fwd_mean, K=2000)
            results.append(dict(
                combo=[f"{d}={v}" for d, v in combo], depth=depth,
                base_fwd_R=base_fwd_mean, cell_fwd_R=sfw["meanR"], lift=round(lift, 4),
                n_fwd=sfw["n"], n_tr=str_["n"], tr_R=str_["meanR"],
                fwd_win=sfw["win"], fwd_pos_yrs=f"{pos}/{tot}", fwd_per_yr=peryr,
                perm_p=pn))
    results.sort(key=lambda x: x["cell_fwd_R"], reverse=True)
    return dict(cell=cell, base_train=btr, base_fwd=bfw, deep_cells=results[:25])


def main():
    out = {}
    # load BOTH the KB5 bases (xvol family) and the KB6 other bases
    allsig = {}
    # KB5 re-run produces no pickle; re-run its miner to get tagged signals for the
    # xvol family too (so deep stacks cover the proven family at depth-3). Reuse XL.
    import KB5_cross_layer_miner as XL
    print("re-mining KB5 xvol-family base signals for deep stacking...", flush=True)
    kb5_sig = XL.mine(verbose=False)
    for b, rs in kb5_sig.items():
        allsig[b] = (rs, XL.BASE_CELLS[b][0])
    # KB6 other-base signals from cache
    kb6_sig = pickle.load(open(HERE / "KB6_other_base_signals.pkl", "rb"))
    import KB6_veto_other_bases as K6
    for b, rs in kb6_sig.items():
        allsig[b] = (rs, K6.BASES[b][0])
    print(f"deep-stacking {len(allsig)} bases...", flush=True)
    for b, (rs, cell) in allsig.items():
        out[b] = mine_base(rs, b, cell)
        nd = len(out[b]["deep_cells"])
        bfw = out[b]["base_fwd"]["meanR"]
        top = out[b]["deep_cells"][0] if nd else None
        ts = f"top {top['cell_fwd_R']:+.2f}R n{top['n_fwd']} d{top['depth']} p{top['perm_p']}" if top else "(none)"
        print(f"  {b:34} base_fwd={bfw} deep_cells={nd}  {ts}", flush=True)
    (HERE / "KB6_DEEP_STACKS_RESULT.json").write_text(json.dumps(out, indent=1, default=str))
    print("\nwrote KB6_DEEP_STACKS_RESULT.json")
    return out


if __name__ == "__main__":
    main()
