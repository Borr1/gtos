"""KB5_validate_stack.py — final validation of the top cross-layer STACKS:
 - permutation null on the full 2-way stack vs base (forward population)
 - per-class breakdown (not one symbol's luck)
 - the leader-impulse VETO as a standalone gate (deepest-sample, all xvol-up bases)
 - confirm ll_impulse=none is NOT merely a low-vol artifact (compare vol_pct of
   none vs impulse bars within the base)
Reuses the cached mine (re-mines once)."""
import sys, json, collections, random, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import KB5_cross_layer_miner as M
random.seed(11)

def ag(rs):
    if not rs: return (0, None, None)
    n=len(rs); s=sum(r['R'] for r in rs); w=sum(1 for r in rs if r['R']>0)
    return (n, round(s/n,3), round(100*w/n,1))

def split(rs):
    return ag([r for r in rs if r['year']<=2024]), ag([r for r in rs if r['year']>=2025])

def perm_null_stack(rs_fwd, predicate, obs_lift, K=3000):
    base=sum(r['R'] for r in rs_fwd)/len(rs_fwd)
    Rs=[r['R'] for r in rs_fwd]
    nsub=sum(1 for r in rs_fwd if predicate(r))
    if nsub==0 or nsub==len(rs_fwd): return None, nsub
    idx=list(range(len(rs_fwd))); ge=0
    for _ in range(K):
        random.shuffle(idx)
        m=sum(Rs[idx[k]] for k in range(nsub))/nsub
        if (m-base)>=obs_lift-1e-12: ge+=1
    return round(ge/K,4), nsub

def main():
    sig=M.mine(verbose=False)
    print("VALIDATION OF TOP CROSS-LAYER STACKS\n"+"="*80)
    for bname in ['xvol_up_pullback_L3R','xvol_up_conflict_L3R','xvol_up_conflict_mid_L3R','mid_dn_revert_ny_L3R']:
        rs=sig[bname]; btr,bfw=split(rs)
        fwd=[r for r in rs if r['year']>=2025]; base_fwd_mean=bfw[1] or 0
        print(f"\n### {bname}  base fwd n{bfw[0]} R{bfw[1]} win{bfw[2]}")
        # standalone leader-impulse VETO (ll_impulse==none)
        veto=lambda r: r['conds'].get('ll_impulse')=='none'
        sub_=[r for r in rs if veto(r)]; vtr,vfw=split(sub_)
        lift=(vfw[1]-base_fwd_mean) if vfw[1] is not None else None
        p,nsub=perm_null_stack(fwd, veto, lift) if lift is not None else (None,0)
        print(f"  VETO ll=none      : trn n{vtr[0]} R{vtr[1]} | fwd n{vfw[0]} R{vfw[1]} win{vfw[2]} lift{lift:+.3f} perm-p{p}")
        # per-class of the veto cell (forward)
        byc=collections.defaultdict(list)
        for r in sub_:
            if r['year']>=2025: byc[r['cls']].append(r['R'])
        pc=", ".join(f"{c}:R{round(sum(v)/len(v),2)}(n{len(v)})" for c,v in sorted(byc.items(), key=lambda x:-sum(x[1])/len(x[1])))
        print(f"     fwd per-class: {pc}")
        # 2-way stack ll=none & above_va
        stk=lambda r: r['conds'].get('ll_impulse')=='none' and r['conds'].get('vp_loc')=='above_va'
        sub2=[r for r in rs if stk(r)]; s2tr,s2fw=split(sub2)
        if s2fw[0]>=10:
            lift2=(s2fw[1]-base_fwd_mean)
            p2,n2=perm_null_stack(fwd, stk, lift2)
            byy=collections.defaultdict(list)
            for r in sub2:
                if r['year']>=2025: byy[r['year']].append(r['R'])
            yrs=", ".join(f"{y}:R{round(sum(v)/len(v),2)}(n{len(v)})" for y,v in sorted(byy.items()))
            print(f"  STACK ll=none&above_va: fwd n{s2fw[0]} R{s2fw[1]} win{s2fw[2]} lift{lift2:+.3f} perm-p{p2} | {yrs}")
        # artifact check: is ll=none just lower vol? compare vol_pct proxy via 'regime'
        none_reg=collections.Counter(r['conds'].get('regime') for r in rs if veto(r) and r['year']>=2025)
        imp_reg=collections.Counter(r['conds'].get('regime') for r in rs if not veto(r) and r['year']>=2025)
        print(f"     regime mix | ll=none: {dict(none_reg)}  ll=impulse: {dict(imp_reg)}")

if __name__=="__main__":
    main()
