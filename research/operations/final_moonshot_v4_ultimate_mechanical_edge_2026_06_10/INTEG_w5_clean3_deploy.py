"""INTEG_w5_clean3_deploy.py — finalize the DATA-CHOSEN deploy book (clean_3) full MC.

The W5 deploy-selection table picked clean_3 (book + sub_xvol_pullback 0.45 +
vp_euidx_pocgrav 0.30 + sub_mid_dn_revert 0.20) as the risk-equivalent winner
(Sharpe 0.1522, best additive stress tail). This script computes that book's full
deliverable: per-sleeve contribution, folded corr matrix, vol-matched MC (all/fwd/
stress), daily-breach, and the 2-account allocation — reusing the cached streams.
"""
import sys, json, collections, math, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3

mc_series = W2.mc_series; joint_pass_mc = W2.joint_pass_mc
DAILY = I.DAILY; N = I.N; BLOCK = I.BLOCK

def pearson(x, y):
    n=len(x)
    if n<8: return None
    mx=sum(x)/n; my=sum(y)/n
    sx=sum((a-mx)**2 for a in x); sy=sum((b-my)**2 for b in y)
    if sx==0 or sy==0: return 0.0
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sx*sy)

def candidate_daily(rows):
    by=collections.defaultdict(list)
    for r in rows: by[r['date']].append(r['R'])
    return {d:sum(v)/len(v) for d,v in by.items()}

def main():
    streams_w3 = pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
    days_w3, M_w3 = W3.W2.build_matrix(streams_w3)
    book_sleeves = W3.SLEEVES
    daily_sleeve = {sl:{} for sl in book_sleeves}
    for di,day in enumerate(days_w3):
        for si,sl in enumerate(book_sleeves):
            daily_sleeve[sl][day]=M_w3[di][si]
    comb_book = {day:sum(M_w3[di]) for di,day in enumerate(days_w3)}
    book_days = set(days_w3)
    sd_book = statistics.pstdev([comb_book[d] for d in days_w3])

    new_streams = pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
    CLEAN3 = {'sub_xvol_pullback':0.45, 'vp_euidx_pocgrav':0.30, 'sub_mid_dn_revert':0.20}
    cand = {nm:candidate_daily(new_streams[nm]) for nm in CLEAN3}
    nd = {nm:{d:v*cf for d,v in cand[nm].items()} for nm,cf in CLEAN3.items()}

    sleeves = list(book_sleeves)+list(CLEAN3.keys())
    conf = dict(W3.SLEEVE_CONF); conf.update(CLEAN3)
    all_days = sorted(book_days | set().union(*[set(cand[n]) for n in CLEAN3]))
    fwd_mask = [d.year>=2025 for d in all_days]
    M = []
    for day in all_days:
        M.append([daily_sleeve[sl].get(day,0.0) for sl in book_sleeves]+[nd[nm].get(day,0.0) for nm in CLEAN3])
    comb = [sum(r) for r in M]
    comb_fwd = [v for v,f in zip(comb,fwd_mask) if f]
    M_fwd = [r for r,f in zip(M,fwd_mask) if f]
    sd = statistics.pstdev(comb); vs = sd_book/sd if sd>0 else 1.0
    rep = dict(book='clean_3', sleeves=sleeves, conf=conf, vol_scale=round(vs,4),
               daily_mean=round(statistics.fmean(comb),5), daily_std=round(sd,5),
               daily_mean_fwd=round(statistics.fmean(comb_fwd),5),
               sharpe=round(statistics.fmean(comb)/sd,4),
               n_days=len(comb), n_days_fwd=len(comb_fwd),
               win_days_pct=round(100*sum(1 for x in comb if x>0)/len(comb),1))

    # corr matrix
    cols=list(zip(*M)); k=len(sleeves)
    C=[[round(pearson(list(cols[i]),list(cols[j])),3) for j in range(k)] for i in range(k)]
    offs=[C[i][j] for i in range(k) for j in range(k) if i<j]
    rep['corr_matrix']=C; rep['sleeve_order']=sleeves
    rep['avg_off_diag_corr']=round(sum(offs)/len(offs),4); rep['corr_minmax']=[round(min(offs),3),round(max(offs),3)]

    # contribution
    contrib={s:sum(M[d][i] for d in range(len(M))) for i,s in enumerate(sleeves)}
    tot=sum(contrib.values()); rep['sleeve_contribution']={}
    for s in sorted(sleeves,key=lambda x:-contrib[x]):
        rep['sleeve_contribution'][s]=dict(sum=round(contrib[s],3),share_pct=round(100*contrib[s]/tot,1),
                                           conf=conf[s], is_new=s in CLEAN3)

    # MC grids (vol-matched + raw + fwd) and book baseline on same grid
    book_series=[comb_book.get(d,0.0) for d in all_days]
    def grid(series, stress=False, scale=1.0):
        s=[(v*1.5 if v<0 else v) for v in series] if stress else series
        return {f"{r*100:.2f}%":mc_series(s, r*scale, seed_base=(999 if stress else 1)) for r in (0.005,0.0075,0.01,0.015,0.02)}
    rep['mc_volmatched_all']=grid(comb, scale=vs)
    rep['mc_volmatched_stress']=grid(comb, stress=True, scale=vs)
    rep['mc_raw_all']=grid(comb)
    rep['mc_raw_stress']=grid(comb, stress=True)
    rep['mc_fwd']={f"{r*100:.2f}%":mc_series(comb_fwd, r, seed_base=777) for r in (0.005,0.0075,0.01,0.015,0.02)}
    rep['mc_book_all']=grid(book_series)
    rep['mc_book_stress']=grid(book_series, stress=True)

    # daily breach
    rep['daily_breach']={}
    for r in (0.005,0.0075,0.01,0.015,0.02):
        rep['daily_breach'][f"{r*100:.2f}%"]=dict(worst_day_pct=round(min(comb)*r*100,3),
            breach_pct=round(100*sum(1 for v in comb if v*r<=-DAILY)/len(comb),3))

    # 2-account (vol-matched eff sizes)
    idx={s:i for i,s in enumerate(sleeves)}; full={idx[s]:1.0 for s in sleeves}
    M_stress=[[(v*1.5 if v<0 else v) for v in row] for row in M]
    rep['two_account']={}
    for (sA,sB,label) in [(0.0075,0.0075,'balanced_A0.75_B0.75'),(0.01,0.005,'staggered_A1.00_B0.50'),
                          (0.01,0.0075,'staggered_A1.00_B0.75'),(0.005,0.005,'conservative_A0.50_B0.50')]:
        sAe=sA*vs; sBe=sB*vs
        base=joint_pass_mc(M,(full,sAe),(full,sBe),seed_base=7)
        fwd=joint_pass_mc(M_fwd,(full,sAe),(full,sBe),seed_base=33)
        strs=joint_pass_mc(M_stress,(full,sAe),(full,sBe),seed_base=44)
        rep['two_account'][label]=dict(sizeA_nominal=sA,sizeB_nominal=sB,sizeA_eff=round(sAe,5),sizeB_eff=round(sBe,5),
            base_p_both=base['p_pass_both'],fwd_p_both=fwd['p_pass_both'],stress15_p_both=strs['p_pass_both'],
            daily_breach_max=max(base['p_A_fail_daily'],base['p_B_fail_daily']))

    (HERE/'INTEG_W5_CLEAN3_DEPLOY.json').write_text(json.dumps(rep,indent=1,default=str))
    # console
    print(f"CLEAN3 deploy: {len(sleeves)} sleeves, sharpe={rep['sharpe']}, vol_scale={vs:.4f}, win-days={rep['win_days_pct']}%")
    print(f"avg off-diag corr {rep['avg_off_diag_corr']} (min {rep['corr_minmax'][0]} max {rep['corr_minmax'][1]})")
    print("\nrisk    DEP@vm  DEPstr@vm  BOOK  BOOKstr  DEPfwd")
    for r in (0.005,0.0075,0.01,0.015,0.02):
        kk=f"{r*100:.2f}%"
        print(f"{r*100:>5.2f}% {rep['mc_volmatched_all'][kk]['p_pass']:>7.2%} {rep['mc_volmatched_stress'][kk]['p_pass']:>9.2%} "
              f"{rep['mc_book_all'][kk]['p_pass']:>6.2%} {rep['mc_book_stress'][kk]['p_pass']:>7.2%} {rep['mc_fwd'][kk]['p_pass']:>7.2%}")
    print("\n2-account:")
    for k,v in rep['two_account'].items():
        print(f"  {k} (effA={v['sizeA_eff']*100:.2f}% effB={v['sizeB_eff']*100:.2f}%): P(both)={v['base_p_both']:.2%} FWD={v['fwd_p_both']:.2%} STRESS={v['stress15_p_both']:.2%} breach={v['daily_breach_max']:.2%}")
    print("\nwrote INTEG_W5_CLEAN3_DEPLOY.json")

if __name__=='__main__':
    main()
