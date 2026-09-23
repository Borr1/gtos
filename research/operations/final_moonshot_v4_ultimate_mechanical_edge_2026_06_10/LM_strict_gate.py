"""
LM_strict_gate.py — apply the HONEST trust gate to liquidity-layer cells.

The pooled sweep+reclaim mechanic is negative (~-0.10R) on every cluster type.
Many cells flip 'forward-positive', but the doctrine warns: a cell that is
TRAIN-NEGATIVE and only forward-positive (often in ONE year, 2026) is a
single-regime artifact, NOT an edge — exactly what data_depth proved for
fx_jpy/idxrev. This script separates GENUINE edges from regime artifacts with a
strict gate, on H4 and M15, and reports the survivors with full per-year detail.

STRICT TRUST GATE (a cell must pass ALL):
  - fwd n >= 40
  - fwd mean_R > +0.05 (beat a real magnitude, not noise)
  - train mean_R > -0.02 (NOT a train-loser that only worked forward)
  - BOTH 2025 and 2026 mean_R > 0 (not a one-year artifact)  [when both years present]
  - train n >= 30 (some train evidence exists)
"""
import sys, os, json, collections, argparse
ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE=ROOT+"/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import liquidity_map as L
import wave1_structure_setups_ict as w1

def htf_dir(B,i,lb=30): return w1.htf_trend(B,i,lb)

def collect(tf, symbols=None):
    if symbols is None:
        symbols = L.M15_SYMBOLS if tf=="M15" else w1.SYMBOLS
    gk=dict(target_mode='fixedR', target_R=2.0, activity_min=0.0)
    recs=[]
    for sym in symbols:
        lm=L.get_map(sym, tf)
        if lm is None: continue
        for sig in L.sweep_signals(lm, **gk):
            i_sweep=sig['i']-1; tr=htf_dir(lm.B,i_sweep)
            d=1 if sig['side']=='long' else -1
            sig['htf']='ALN' if tr==d else 'CTR' if tr==-d else 'NEU'
            recs.append(sig)
    return recs

def strict_pass(rows):
    tr,fw=L.split_tf(rows)
    if fw['n']<40: return False
    if fw['mean_R']<=0.05: return False
    if tr['n']>=30 and tr['mean_R']<=-0.02: return False
    py=L.per_year(rows)
    yrs=[y for y in py if y>=2025]
    pos=[y for y in yrs if py[y]['mean_R']>0]
    # require both forward years positive when both exist; if only one, require it pos & n>=40
    if len(yrs)>=2 and len(pos)<len(yrs): return False
    if len(yrs)==1 and (py[yrs[0]]['mean_R']<=0 or py[yrs[0]]['n']<40): return False
    return True

def grade(rows):
    tr,fw=L.split_tf(rows); py=L.per_year(rows)
    return dict(train=tr, fwd=fw, per_year={str(y):py[y] for y in py}, strict=strict_pass(rows))

def keyed(recs, kf, min_fwd_n=40):
    g=collections.defaultdict(list)
    for r in recs: g[kf(r)].append(r)
    out=[]
    for k,rows in g.items():
        if L.split_tf(rows)[1]['n']<min_fwd_n: continue
        gr=grade(rows); gr['key']=str(k); gr['n']=len(rows)
        out.append(gr)
    out.sort(key=lambda x:-x['fwd']['mean_R'])
    return out

def fmt(c):
    tr,fw,py=c['train'],c['fwd'],c['per_year']
    fy=" ".join(f"{y}:{py[y]['mean_R']:+.2f}(n{py[y]['n']})" for y in sorted(py) if int(y)>=2025)
    return f"{'PASS' if c['strict'] else '    '} {c['key']:40s} TRAIN {tr['mean_R']:+.3f}(n{tr['n']:>5}) | FWD {fw['mean_R']:+.3f}(n{fw['n']:>5}) w{fw['win']:.0f}% [{fy}]"

def run(tf):
    print(f"\n############## {tf} STRICT GATE ##############")
    recs=collect(tf)
    print(f"signals: {len(recs)}")
    views={
        "ct_class_htf": (lambda r:(r['ct'],r['cls'],r['htf'])),
        "ct_class_side_htf": (lambda r:(r['ct'],r['cls'],r['side'],r['htf'])),
        "ct_sym_htf": (lambda r:(r['ct'],r['sym'],r['htf'])),
    }
    res={"tf":tf,"n":len(recs)}
    for vname,kf in views.items():
        cells=keyed(recs, kf)
        passers=[c for c in cells if c['strict']]
        res[vname]={"n_cells":len(cells),"n_pass":len(passers),"passers":passers,"all_top":cells[:30]}
        print(f"\n  view={vname}: {len(passers)}/{len(cells)} cells pass STRICT gate")
        for c in passers[:25]: print("   "+fmt(c))
    return res

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--tf",default="both",choices=["H4","M15","both"])
    a=ap.parse_args()
    out={"_gate":"fwd n>=40 & fwd_R>+0.05 & train_R>-0.02 & BOTH fwd years >0 & train n>=30"}
    if a.tf in ("H4","both"): out["H4"]=run("H4")
    if a.tf in ("M15","both"): out["M15"]=run("M15")
    with open(EDGE+"/LM_STRICT_GATE_RESULT.json","w") as f: json.dump(out,f,indent=1,default=str)
    print("\nWROTE LM_STRICT_GATE_RESULT.json")

if __name__=="__main__":
    main()
