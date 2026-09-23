"""KB7 (track: reinstate-sleeves) — GROWTH-SIZING reinstatement test.

OBJECTIVE: maximize growth-rate / speed-to-target SUBJECT TO FTMO (5% daily, 10% maxDD)
and an acceptable P(maxDD-breach)/P(ruin). NOT vol-matched. The prior 'dropped' verdict used
a vol-matched lens that re-scales risk DOWN when a lower-Sharpe (but +EV, orthogonal) sleeve is
added, which mechanically penalizes high-frequency breadth. Under growth we ask the real question:
at a FIXED risk budget, does the sleeve CUT median days-to-target and/or RAISE net EV, while
holding P(maxDD-fail) acceptable?

Base = clean_4 (clean_3 + session_leadlag_genuine@0.15), the current deploy book.
Candidates reinstated ON TOP: leadlag_full(@conf), leadlag_top4, leadlag_hisharpe2, subh4_ll_fx,
idb_crypto, idb_metals. Each at a confidence weight; raw label cap configurable.
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../../..')
import pickle, statistics, collections, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB6_session_stacks as SS

mc_series=W2.mc_series
WINHI=5.0
def wins(r,hi=WINHI): return max(-1.3,min(hi,r))

def candidate_daily(rows, cap=WINHI, rawkey=None):
    by=collections.defaultdict(list)
    for r in rows:
        v = r[rawkey] if rawkey else r['R']
        by[r['date']].append(wins(v,cap))
    return {d:sum(v)/len(v) for d,v in by.items()}

# ---------- base book matrix (clean_4) ----------
streams_w3=pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
days_w3,M_w3=W3.W2.build_matrix(streams_w3)
book_sleeves=W3.SLEEVES
daily_sleeve={sl:{} for sl in book_sleeves}
for di,day in enumerate(days_w3):
    for si,sl in enumerate(book_sleeves): daily_sleeve[sl][day]=M_w3[di][si]
book_days=set(days_w3)

new_streams=pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
CLEAN3={'sub_xvol_pullback':0.45,'vp_euidx_pocgrav':0.30,'sub_mid_dn_revert':0.20}
slg=SS.gen_session_leadlag_genuine()
CLEAN4_EXTRA={**CLEAN3, 'session_leadlag_genuine':0.15}

# candidate streams
idb=pickle.load(open(HERE/'KB7_idb_streams_cache.pkl','rb'))
CANDS={
 'leadlag_full':       pickle.load(open(HERE/'KB7_stream_leadlag_full.pkl','rb')),
 'leadlag_top4':       pickle.load(open(HERE/'KB7_stream_leadlag_top4.pkl','rb')),
 'leadlag_hisharpe2':  pickle.load(open(HERE/'KB7_stream_leadlag_hisharpe2.pkl','rb')),
 'subh4_ll_fx':        new_streams['subh4_ll_fx'],
 'idb_crypto':         idb['idb_crypto'],
 'idb_metals':         idb['idb_metals'],
}
RAWKEY={'idb_crypto':'R_raw','idb_metals':'R_raw'}

# precompute per-day series for base extras + session_leadlag_genuine
cand_daily_base={nm:candidate_daily(new_streams[nm]) for nm in CLEAN3}
cand_daily_base['session_leadlag_genuine']=candidate_daily(slg)

def cand_daily(nm, cap=WINHI):
    return candidate_daily(CANDS[nm], cap=cap, rawkey=RAWKEY.get(nm))

def build_comb(extra_conf, cap=WINHI):
    """extra_conf maps {base-extra or candidate name -> conf}. Base 8 sleeves always in."""
    # base-extra dailies
    parts={}
    for nm,cf in extra_conf.items():
        if nm in cand_daily_base: cd=cand_daily_base[nm]
        else: cd=cand_daily(nm,cap)
        parts[nm]={d:v*cf for d,v in cd.items()}
    all_days=sorted(book_days | set().union(*[set(p) for p in parts.values()]) if parts else book_days)
    comb=[]; fwd=[]
    for d in all_days:
        bs=sum(daily_sleeve[sl].get(d,0.0) for sl in book_sleeves)
        es=sum(parts[nm].get(d,0.0) for nm in extra_conf)
        comb.append(bs+es); fwd.append(d.year>=2025)
    return all_days, comb, fwd

def growth_grid(comb, sizes, label='', stress=False, seed=1):
    s=[(v*1.5 if v<0 else v) for v in comb] if stress else comb
    out={}
    for r in sizes:
        res=mc_series(s, r, seed_base=(999 if stress else seed))
        out[f"{r*100:.2f}%"]=dict(p_pass=round(res['p_pass'],4), p_fail_dd=round(res['p_fail_dd'],4),
                                  p_fail_daily=round(res['p_fail_daily'],4), med_days=res['med_days_pass'])
    return out

SIZES=(0.005,0.0075,0.01,0.015,0.02,0.025,0.03)

def daily_breach(comb, sizes):
    return {f"{r*100:.2f}%":dict(worst_pct=round(min(comb)*r*100,3),
            breach_pct=round(100*sum(1 for v in comb if v*r<=-I.DAILY)/len(comb),3)) for r in sizes}

def summarize(name, extra_conf, cap=WINHI):
    ad,comb,fwd=build_comb(extra_conf, cap)
    comb_fwd=[v for v,f in zip(comb,fwd) if f]
    m=statistics.fmean(comb); sd=statistics.pstdev(comb)
    g_all=growth_grid(comb, SIZES, name)
    g_str=growth_grid(comb, SIZES, name, stress=True)
    g_fwd=growth_grid(comb_fwd, SIZES, name, seed=777)
    db=daily_breach(comb, SIZES)
    return dict(sleeves_extra=list(extra_conf.keys()), daily_mean=round(m,5), daily_std=round(sd,5),
                sharpe=round(m/sd,4), n_days=len(comb), n_days_fwd=len(comb_fwd),
                daily_mean_fwd=round(statistics.fmean(comb_fwd),5),
                mc_all=g_all, mc_stress=g_str, mc_fwd=g_fwd, daily_breach=db)

REPORT={'objective':'growth-rate/speed-to-target s.t. FTMO + acceptable P(maxDD-fail)',
        'note':'NOT vol-matched (raw fixed-risk growth lens); cap default +5R'}

VARIANTS=collections.OrderedDict([
 ('clean4_base', dict(CLEAN4_EXTRA)),
 ('clean4+leadlag_full@0.15',      {**CLEAN4_EXTRA,'leadlag_full':0.15}),
 ('clean4+leadlag_full@0.30',      {**CLEAN4_EXTRA,'leadlag_full':0.30}),
 ('clean4+leadlag_top4@0.30',      {**CLEAN4_EXTRA,'leadlag_top4':0.30}),
 ('clean4+leadlag_top4@0.45',      {**CLEAN4_EXTRA,'leadlag_top4':0.45}),
 ('clean4+leadlag_hisharpe2@0.30', {**CLEAN4_EXTRA,'leadlag_hisharpe2':0.30}),
 ('clean4+leadlag_hisharpe2@0.45', {**CLEAN4_EXTRA,'leadlag_hisharpe2':0.45}),
 ('clean4+subh4_ll_fx@0.30',       {**CLEAN4_EXTRA,'subh4_ll_fx':0.30}),
 ('clean4+idb_crypto@0.30',        {**CLEAN4_EXTRA,'idb_crypto':0.30}),
 ('clean4+idb_metals@0.30',        {**CLEAN4_EXTRA,'idb_metals':0.30}),
 # combined growth book: top4 leadlag + subh4 + idb_crypto, all moderate conf
 ('GROWTH_clean4+top4@0.45+subh4@0.30+idbC@0.30',
     {**CLEAN4_EXTRA,'leadlag_top4':0.45,'subh4_ll_fx':0.30,'idb_crypto':0.30}),
 ('GROWTH_top4@0.45+subh4@0.30',
     {**CLEAN4_EXTRA,'leadlag_top4':0.45,'subh4_ll_fx':0.30}),
])

print(f"{'variant':<48}{'Sh':>7}{'mean':>8}{'P@1.5%':>8}{'dd@1.5':>8}{'med@1.5':>8}{'P@2%':>7}{'dd@2%':>7}{'med@2':>7}{'str@1.5':>8}")
for nm,ec in VARIANTS.items():
    r=summarize(nm,ec); REPORT[nm]=r
    a15=r['mc_all']['1.50%']; a2=r['mc_all']['2.00%']; s15=r['mc_stress']['1.50%']
    print(f"{nm:<48}{r['sharpe']:>7.3f}{r['daily_mean']:>8.4f}{a15['p_pass']:>8.3f}{a15['p_fail_dd']:>8.3f}{str(a15['med_days']):>8}{a2['p_pass']:>7.3f}{a2['p_fail_dd']:>7.3f}{str(a2['med_days']):>7}{s15['p_pass']:>8.3f}")

json.dump(REPORT, open(HERE/'KB7_GROWTH_MC_RESULT.json','w'), indent=1, default=str)
print("\nwrote KB7_GROWTH_MC_RESULT.json")
