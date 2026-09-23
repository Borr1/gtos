"""
LM_probe_confluence.py — find forward-validated CONFLUENCE cells in the liquidity layer.
The pooled sweep+reclaim mechanic is negative; high odds (if any) live in stacked
conditions. This probe buckets every signal by (cluster_type x asset_class x side x
activity-bucket x reclaim-strength bucket) and surfaces cells that hold forward.

It also tests an HTF-alignment overlay (only take sweeps in the direction of the H4
trend proxy) which is the most likely source of a real edge for a continuation-style
reclaim. Writes LM_CONFLUENCE_RESULT.json.
"""
import sys, os, json, collections, time
ROOT="/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE=ROOT+"/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import liquidity_map as L
import wave1_structure_setups_ict as w1
from geometry_lib import atr14

MIN_N=L.MIN_TRUST_N

def htf_dir(B,i,lb=30):
    return w1.htf_trend(B,i,lb)

def collect(tf, gen_kwargs, with_htf=True, symbols=None):
    """Return per-signal recs enriched with htf alignment and buckets."""
    if symbols is None:
        symbols = L.M15_SYMBOLS if tf=="M15" else w1.SYMBOLS
    recs=[]
    for sym in symbols:
        try: T,B=L.load(sym,tf)
        except Exception: continue
        if len(B)<300: continue
        lm=L.LiquidityMap(T,B,sym).build()
        for sig in L.sweep_signals(lm, **gen_kwargs):
            i_entry=sig['i']           # entry index = sweep+1
            i_sweep=i_entry-1
            tr=htf_dir(B,i_sweep) if with_htf else 0
            d=1 if sig['side']=='long' else -1
            sig['htf']=tr
            sig['aligned']=(tr==d)            # reclaim in HTF direction (continuation)
            sig['counter']=(tr==-d)           # reclaim against HTF (reversal)
            # buckets
            a=sig['act']
            sig['act_b']=('lo' if a<0.8 else 'mid' if a<1.3 else 'hi' if a<2.0 else 'xhi')
            rc=sig['reclaim']
            sig['rc_b']=('lo' if rc<0.2 else 'mid' if rc<0.4 else 'hi')
            recs.append(sig)
    return recs

def cells(recs, key_fn, min_n=MIN_N):
    g=collections.defaultdict(list)
    for r in recs: g[key_fn(r)].append(r)
    out=[]
    for k,rows in g.items():
        tr,fw=L.split_tf(rows)
        if fw['n']<min_n: continue
        out.append(dict(key=k, train=tr, fwd=fw,
                        fv=L.forward_validated(rows,min_n=min_n),
                        per_year={str(y):L.per_year(rows)[y] for y in L.per_year(rows)}))
    out.sort(key=lambda x:-x['fwd']['mean_R'])
    return out

def fmt(c):
    tr=c['train']; fw=c['fwd']
    py=c['per_year']; fy=" ".join(f"{y}:{py[y]['mean_R']:+.2f}(n{py[y]['n']})" for y in sorted(py) if int(y)>=2025)
    return f"{str(c['key']):42s} TRAIN {tr['mean_R']:+.3f}(n{tr['n']:>5}) | FWD {fw['mean_R']:+.3f}(n{fw['n']:>5}) w{fw['win']:.0f}% fv={c['fv']} [{fy}]"

def run(tf):
    print(f"\n################# {tf} CONFLUENCE PROBE #################")
    # use the activity-gated baseline (relvol available on these series)
    gk=dict(target_mode='fixedR', target_R=2.0, activity_min=0.0)
    recs=collect(tf, gk, with_htf=True)
    print(f"collected {len(recs)} signals")

    res={"tf":tf,"n":len(recs)}

    # 1) HTF alignment is the prime hypothesis: continuation reclaim vs reversal reclaim
    for tag,sub in (("ALIGNED(continuation)",[r for r in recs if r['aligned']]),
                    ("COUNTER(reversal)",[r for r in recs if r['counter']]),
                    ("NEUTRAL_htf",[r for r in recs if r['htf']==0])):
        tr,fw=L.split_tf(sub)
        print(f"  {tag:24s}: TRAIN {tr['mean_R']:+.3f}(n{tr['n']}) FWD {fw['mean_R']:+.3f}(n{fw['n']}) w{fw['win']:.0f}%")
    res["htf_overlay"]={
        "aligned":   dict(zip(("train","fwd"),L.split_tf([r for r in recs if r['aligned']]))),
        "counter":   dict(zip(("train","fwd"),L.split_tf([r for r in recs if r['counter']]))),
        "neutral":   dict(zip(("train","fwd"),L.split_tf([r for r in recs if r['htf']==0]))),
    }

    # 2) top cells: ctype x class x aligned
    def kf_full(r): return (r['ct'], r['cls'], 'ALN' if r['aligned'] else 'CTR' if r['counter'] else 'NEU')
    top=cells(recs, kf_full)
    res["ct_class_htf"]=top
    print("\n  -- TOP cells (ctype x class x htf), fwd-sorted, n_fwd>=40 --")
    for c in top[:25]: print("   "+fmt(c))

    # 3) ctype x class x side x aligned (finer)
    def kf_side(r): return (r['ct'], r['cls'], r['side'], 'ALN' if r['aligned'] else 'CTR' if r['counter'] else 'NEU')
    top2=cells(recs, kf_side)
    res["ct_class_side_htf"]=top2
    print("\n  -- TOP cells (ctype x class x side x htf) --")
    for c in top2[:20]: print("   "+fmt(c))

    # 4) confluence stack: aligned + high activity + strong reclaim, grouped by ctype x class
    stack=[r for r in recs if r['aligned'] and r['act']>=1.2 and r['reclaim']>=0.25]
    def kf_stack(r): return (r['ct'], r['cls'])
    tops=cells(stack, kf_stack, min_n=25)  # confluence cells are rarer; report n>=25, trust at >=40
    res["confluence_stack"]={"definition":"aligned & act>=1.2 & reclaim>=0.25","cells":tops}
    print("\n  -- CONFLUENCE STACK (aligned & act>=1.2 & reclaim>=0.25), ctype x class, n_fwd>=25 --")
    for c in tops[:20]: print("   "+fmt(c))

    # 5) per-instrument best (ctype x sym, aligned only)
    aln=[r for r in recs if r['aligned']]
    top_sym=cells(aln, lambda r:(r['ct'],r['sym']))
    res["ct_sym_aligned"]=top_sym
    print("\n  -- TOP per-instrument (ctype x sym, ALIGNED only) --")
    for c in top_sym[:20]: print("   "+fmt(c))
    return res

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--tf",default="both",choices=["H4","M15","both"])
    a=ap.parse_args()
    out={"_doctrine":"confluence-mined; TRAIN<=2024 vs FWD; n>=40 trust; leak-free; htf overlay tested"}
    if a.tf in ("H4","both"): out["H4"]=run("H4")
    if a.tf in ("M15","both"): out["M15"]=run("M15")
    with open(EDGE+"/LM_CONFLUENCE_RESULT.json","w") as f: json.dump(out,f,indent=1,default=str)
    print("\nWROTE LM_CONFLUENCE_RESULT.json")

if __name__=="__main__":
    main()
