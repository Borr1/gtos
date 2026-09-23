"""
LM_mine.py — mine the liquidity-map / stop-hunt layer for forward-validated cells.
Track key prefix: LM. Writes LM_LIQUIDITY_STOPHUNT_RESULT.json.

Reports STATES not systems: per-cluster-type, per-instrument, per-YEAR, TRAIN<=2024
vs FORWARD 2025-26, with sample size n. Trust only forward-validated cells (n>=40).
Confluence sweeps: cluster type x reclaim strength x activity (relvol) x optional HTF.
"""
import sys, os, json, time, collections, argparse
ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE=ROOT+"/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import liquidity_map as L
import wave1_structure_setups_ict as w1

CTYPES=('pd','ps','asia','eq','rn','sw')

def cell_report(recs, key_fn, label, min_n=L.MIN_TRUST_N):
    """Group recs by key_fn, report train/fwd/per-year, flag forward-validated."""
    groups=collections.defaultdict(list)
    for r in recs: groups[key_fn(r)].append(r)
    rows=[]
    for k in sorted(groups, key=lambda x:str(x)):
        g=groups[k]
        tr,fw=L.split_tf(g)
        py=L.per_year(g)
        fv=L.forward_validated(g, min_n=min_n)
        rows.append(dict(key=k, train=tr, fwd=fw,
                         per_year={str(y):py[y] for y in py},
                         forward_validated=fv))
    return {"label":label, "cells":rows}

def top_edges(recs, *, by='ct_sym', min_n=L.MIN_TRUST_N):
    if by=='ct_sym':
        kf=lambda r:(r['ct'],r['sym'])
    elif by=='ct_sym_side':
        kf=lambda r:(r['ct'],r['sym'],r['side'])
    else:
        kf=lambda r:r['ct']
    groups=collections.defaultdict(list)
    for r in recs: groups[kf(r)].append(r)
    out=[]
    for k,g in groups.items():
        tr,fw=L.split_tf(g)
        if fw['n']<min_n: continue
        fv=L.forward_validated(g, min_n=min_n)
        out.append(dict(key=k, train=tr, fwd=fw, forward_validated=fv,
                        per_year={str(y):L.per_year(g)[y] for y in L.per_year(g)}))
    out.sort(key=lambda x:-x['fwd']['mean_R'])
    return out

def run_tf(tf, configs):
    """configs: list of (name, gen_kwargs). Returns dict per config of raw recs + cells."""
    res={}
    for name,gk in configs:
        t0=time.time()
        recs=L.run_cells(tf=tf, gen_kwargs=gk, ctypes=CTYPES)
        dt=time.time()-t0
        tr,fw=L.split_tf(recs)
        res[name]=dict(
            n_total=len(recs),
            overall_train=tr, overall_fwd=fw,
            by_ctype=cell_report(recs, lambda r:r['ct'], "per cluster-type (pooled syms)"),
            by_ctype_class=cell_report(recs, lambda r:f"{r['ct']}|{r['cls']}", "per cluster-type x asset-class"),
            top_ct_sym=top_edges(recs, by='ct_sym'),
            top_ct_sym_side=top_edges(recs, by='ct_sym_side'),
        )
        print(f"[{tf}/{name}] n={len(recs)} train R={tr['mean_R']:+.3f}(n{tr['n']}) fwd R={fw['mean_R']:+.3f}(n{fw['n']}) {dt:.0f}s")
        # quick per-ctype forward print
        for row in res[name]['by_ctype']['cells']:
            ct=row['key']; fw2=row['fwd']; trn=row['train']
            print(f"     {ct:>5}: train {trn['mean_R']:+.3f}(n{trn['n']:>5}) fwd {fw2['mean_R']:+.3f}(n{fw2['n']:>5}) w{fw2['win']:.0f}% fv={row['forward_validated']}")
    return res

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tf", default="both", choices=["H4","M15","both"])
    ap.add_argument("--quick", action="store_true", help="single baseline config only")
    args=ap.parse_args()

    if args.quick:
        configs=[("base_2R_act0", dict(target_mode='fixedR', target_R=2.0, activity_min=0.0))]
    else:
        configs=[
            ("base_2R_act0",      dict(target_mode='fixedR', target_R=2.0, activity_min=0.0)),
            ("base_2R_act1.2",    dict(target_mode='fixedR', target_R=2.0, activity_min=1.2)),
            ("base_3R_act1.2",    dict(target_mode='fixedR', target_R=3.0, activity_min=1.2)),
            ("strong_2R_act1.2",  dict(target_mode='fixedR', target_R=2.0, activity_min=1.2,
                                       sweep_min=0.15, reclaim_min=0.25)),
            ("opp_act1.2",        dict(target_mode='opposing', target_R=2.0, activity_min=1.2)),
        ]

    out={"_doctrine":"per-cell/per-year/per-regime; TRAIN<=2024 vs FWD2025-26; n>=40 to trust; "
                     "leak-free (clusters from index<=i, enter i+1); real w1.cost_for; geometry_lib.simulate.",
         "min_trust_n":L.MIN_TRUST_N}
    if args.tf in ("H4","both"):
        print("\n========== H4 ==========")
        out["H4"]=run_tf("H4", configs)
    if args.tf in ("M15","both"):
        print("\n========== M15 ==========")
        out["M15"]=run_tf("M15", configs)

    with open(EDGE+"/LM_LIQUIDITY_STOPHUNT_RESULT.json","w") as f:
        json.dump(out,f,indent=1)
    print("\nWROTE LM_LIQUIDITY_STOPHUNT_RESULT.json")

if __name__=="__main__":
    main()
