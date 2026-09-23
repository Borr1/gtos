"""KB5_run.py — measure the NEW condition families against the existing 7.
==========================================================================
Reuses confluence.py's probes + SymCtx + analyzer, but EXTENDS the CONDITIONS
registry with KB5's 6 new families. Produces, per probe x asset-class view:
  - phi-independence of EACH new family vs EACH existing family (and vs each other)
  - marginal forward odds-lift of each new family (base-rate -> rate|cond), TRAIN+FWD+n
  - whether STACKING a new family on the best existing stack MULTIPLIES forward odds
    (incremental ablation: base -> existing-stack -> +new)
  - per-year stability of the headline new-family cells

All leak-free (confluence's simulate labels), n-gated, TRAIN(<=2024)/FWD(2025-26) split.
"""
from __future__ import annotations
import sys, json, math, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

import confluence as C
from geometry_lib import simulate
import wave1_structure_setups_ict as w1
from KB5_condition_families import EXTRA_CONDITIONS, EXTRA_NAMES, LEAD

# Build the combined registry: existing 7 + new 6
BASE_CONDITIONS = list(C.CONDITIONS)
BASE_NAMES = [c[0] for c in BASE_CONDITIONS]
ALL_CONDITIONS = BASE_CONDITIONS + list(EXTRA_CONDITIONS)
ALL_NAMES = [c[0] for c in ALL_CONDITIONS]
N_BASE = len(BASE_NAMES)

WIN = lambda r: r > 0.0


def build(probe="fvg", classes=None, symbols=None):
    """Like confluence.build_dataset but evaluates ALL_CONDITIONS (existing+new).
    SymCtx is extended with .T so the new families can read T[i].hour leak-free."""
    if symbols is None:
        symbols = w1.SYMBOLS
    from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
    if classes is not None:
        symbols = [s for s in symbols if (ASSET_CLASS_BY_SYMBOL.get(s) or "other") in classes]
    ctxs = {}
    for s in symbols:
        try:
            ctx = C.SymCtx(s)
        except Exception:
            continue
        if ctx.n >= 200:
            # attach T (timestamps) so KB5 session/intermarket conditions read it leak-free
            ctx.T = w1.load(s)[0]
            ctxs[s] = ctx
    gen = C.PROBES[probe](ctxs)
    out = []
    for (ctx, i, d, sd, td) in gen:
        r = simulate(ctx.B, i, d, stop_dist=sd, target_dist=td, cost=ctx.cost)
        conds = [fn(ctx, i, d) for _, fn in ALL_CONDITIONS]
        out.append(dict(sym=ctx.sym, cls=ctx.cls, year=ctx.T[i].year,
                        d=d, R=round(r, 5), win=WIN(r), conds=conds))
    return out


def _split(recs):
    return [r for r in recs if r["year"] <= 2024], [r for r in recs if r["year"] >= 2025]

def _odds(recs):
    n = len(recs)
    if n == 0: return dict(n=0, win=0.0, meanR=0.0)
    return dict(n=n, win=round(100*sum(1 for r in recs if r["win"])/n, 1),
                meanR=round(sum(r["R"] for r in recs)/n, 4))

def _phi(a, b):
    n = len(a)
    if n == 0: return 0.0
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    n00 = n - n11 - n10 - n01
    den = math.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
    return (n11*n00 - n10*n01)/den if den > 0 else 0.0

def _perm_p(recs, mask_idx, iters=2000, seed=12345):
    """Label-permutation null on the FORWARD mean-R of the cell where condition mask_idx
    is True: is the observed fwd meanR beyond a shuffled-label null? Returns p (two-sided
    on >= for a positive edge)."""
    import random
    rng = random.Random(seed)
    fw = [r for r in recs if r["year"] >= 2025]
    if not fw: return 1.0
    flags = [r["conds"][mask_idx] for r in fw]
    Rs = [r["R"] for r in fw]
    k = sum(flags)
    if k < 10: return 1.0
    obs = sum(R for R, f in zip(Rs, flags) if f) / k
    ge = 0
    n = len(Rs)
    idxs = list(range(n))
    for _ in range(iters):
        rng.shuffle(idxs)
        s = sum(Rs[idxs[j]] for j in range(k))
        if s/k >= obs: ge += 1
    return (ge+1)/(iters+1)


def analyze_new(recs, n_min=40):
    res = {}
    btr, bfw = _split(recs)
    res["base"] = dict(train=_odds(btr), fwd=_odds(bfw), total_n=len(recs))
    K = len(ALL_NAMES)
    cols = [[r["conds"][k] for r in recs] for k in range(K)]
    res["fire_rate_pct"] = {ALL_NAMES[k]: round(100*sum(cols[k])/len(cols[k]),1) if cols[k] else 0.0 for k in range(K)}

    # (1) phi of each NEW family vs every EXISTING family + vs other new families
    indep = {}
    for ni in range(N_BASE, K):
        row = {}
        for bj in range(K):
            if bj == ni: continue
            row[ALL_NAMES[bj]] = round(_phi(cols[ni], cols[bj]), 3)
        mx = max((abs(v) for v in row.values()), default=0.0)
        indep[ALL_NAMES[ni]] = dict(max_abs_phi=round(mx,3), vs=row)
    res["new_independence"] = indep

    # (2) marginal odds-lift of each NEW family
    marg = {}
    for ni in range(N_BASE, K):
        on = [r for r in recs if r["conds"][ni]]
        otr_l, ofw_l = _split(on)
        otr, ofw = _odds(otr_l), _odds(ofw_l)
        marg[ALL_NAMES[ni]] = dict(
            train=otr, fwd=ofw,
            train_winlift=round(otr["win"] - res["base"]["train"]["win"], 1),
            fwd_winlift=round(ofw["win"] - res["base"]["fwd"]["win"], 1),
            train_Rlift=round(otr["meanR"] - res["base"]["train"]["meanR"], 4),
            fwd_Rlift=round(ofw["meanR"] - res["base"]["fwd"]["meanR"], 4),
            perm_p_fwd=round(_perm_p(recs, ni), 4) if ofw["n"] >= n_min else None,
        )
    res["new_marginal"] = marg

    # (3) does ADDING a new family to the best existing pair MULTIPLY forward odds?
    #     find best existing forward-holding pair (n-gated), then add each new family.
    from itertools import combinations
    best_pair = None; best_fwR = -9
    for combo in combinations(range(N_BASE), 2):
        sel = [r for r in recs if all(r["conds"][k] for k in combo)]
        _, sf = _split(sel)
        o = _odds(sf)
        if o["n"] >= n_min and o["meanR"] > best_fwR:
            best_fwR = o["meanR"]; best_pair = combo
    multiply = {}
    if best_pair:
        sel0 = [r for r in recs if all(r["conds"][k] for k in best_pair)]
        _, sf0 = _split(sel0)
        base_stack = _odds(sf0)
        multiply["existing_pair"] = [ALL_NAMES[k] for k in best_pair]
        multiply["existing_pair_fwd"] = base_stack
        adds = {}
        for ni in range(N_BASE, K):
            sel = [r for r in recs if all(r["conds"][k] for k in best_pair) and r["conds"][ni]]
            str_, sf = _split(sel)
            o = _odds(sf); ot = _odds(str_)
            adds[ALL_NAMES[ni]] = dict(train=ot, fwd=o,
                fwd_winlift_vs_pair=round(o["win"] - base_stack["win"], 1) if o["n"] else None,
                fwd_Rlift_vs_pair=round(o["meanR"] - base_stack["meanR"], 4) if o["n"] else None)
        multiply["plus_new"] = adds
    res["multiplication"] = multiply

    # (4) per-year for each new family's cell (stability)
    py = {}
    for ni in range(N_BASE, K):
        on = [r for r in recs if r["conds"][ni]]
        by = collections.defaultdict(list)
        for r in on: by[r["year"]].append(r)
        py[ALL_NAMES[ni]] = {str(y): _odds(by[y]) for y in sorted(by)}
    res["new_per_year"] = py
    return res


def run(probe, classes, label, n_min=40):
    recs = build(probe=probe, classes=classes)
    res = analyze_new(recs, n_min=n_min)
    res["label"] = label; res["probe"] = probe; res["classes"] = classes
    return res


def _p(res):
    b = res["base"]
    print(f"\n===== KB5 [{res['label']}] probe={res['probe']} classes={res['classes']} =====")
    print(f" BASE total_n={b['total_n']} TRAIN n={b['train']['n']} win={b['train']['win']}% R={b['train']['meanR']:+.3f} | FWD n={b['fwd']['n']} win={b['fwd']['win']}% R={b['fwd']['meanR']:+.3f}")
    print(" NEW fire-rate%: " + " ".join(f"{k}={v}" for k,v in res['fire_rate_pct'].items() if k in EXTRA_NAMES))
    print(" NEW independence (max|phi| vs ALL existing+new):")
    for k,v in res["new_independence"].items():
        top = sorted(v["vs"].items(), key=lambda x:-abs(x[1]))[:2]
        print(f"   {k:13s} max|phi|={v['max_abs_phi']:+.3f}  top: " + " ".join(f"{a}={p:+.2f}" for a,p in top))
    print(" NEW marginal odds-lift:")
    for k,m in res["new_marginal"].items():
        pp = f" perm_p={m['perm_p_fwd']}" if m['perm_p_fwd'] is not None else ""
        print(f"   {k:13s} TRAIN n={m['train']['n']:5d} win={m['train']['win']:5.1f}%(lift{m['train_winlift']:+.1f}) R={m['train']['meanR']:+.3f}(lift{m['train_Rlift']:+.3f})"
              f" | FWD n={m['fwd']['n']:5d} win={m['fwd']['win']:5.1f}%(lift{m['fwd_winlift']:+.1f}) R={m['fwd']['meanR']:+.3f}(lift{m['fwd_Rlift']:+.3f}){pp}")
    mp = res.get("multiplication", {})
    if mp.get("existing_pair"):
        ep = mp["existing_pair_fwd"]
        print(f" MULTIPLY test — best existing pair {'+'.join(mp['existing_pair'])}: FWD n={ep['n']} win={ep['win']}% R={ep['meanR']:+.3f}")
        for k,a in mp["plus_new"].items():
            if a["fwd"]["n"] >= 20:
                print(f"   +{k:13s} FWD n={a['fwd']['n']:4d} win={a['fwd']['win']:5.1f}% R={a['fwd']['meanR']:+.3f}"
                      f" (vs pair: win{a['fwd_winlift_vs_pair']:+.1f} R{a['fwd_Rlift_vs_pair']:+.3f})")


def main():
    views = [
        ("ALL", None),
        ("fx_jpy", ["fx","jpy_fx"]),
        ("metals", ["metals"]),
        ("index", ["index"]),
        ("energy", ["energy"]),
        ("crypto", ["crypto"]),
    ]
    allres = {}
    for probe in ("fvg","sweep"):
        for label, classes in views:
            try:
                res = run(probe, classes, f"{probe}:{label}")
            except Exception as e:
                import traceback; traceback.print_exc()
                print(f" [skip {probe}:{label}] {e}"); continue
            _p(res)
            allres[f"{probe}:{label}"] = res
    out = HERE/"KB5_CONDITION_FAMILIES_RESULT.json"
    with open(out,"w") as f: json.dump(allres, f, indent=1)
    print(f"\nWROTE {out}")

if __name__ == "__main__":
    main()
