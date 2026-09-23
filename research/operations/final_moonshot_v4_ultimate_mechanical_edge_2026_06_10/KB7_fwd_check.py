"""KB7 — FORWARD-window (2025-26) iso-ruin speed test. Leadlag EV is strongest forward, so the
fairest growth test for reinstatement is the forward holdout itself."""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../../..')
import pickle, statistics, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB6_session_stacks as SS
mc_series=W2.mc_series
def wins(r,hi=5.0): return max(-1.3,min(hi,r))
streams_w3=pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
days_w3,M_w3=W3.W2.build_matrix(streams_w3)
book_sleeves=W3.SLEEVES
daily_sleeve={sl:{day:M_w3[di][si] for di,day in enumerate(days_w3)} for si,sl in enumerate(book_sleeves)}
book_days=set(days_w3)
new_streams=pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
idb=pickle.load(open(HERE/'KB7_idb_streams_cache.pkl','rb'))
slg=SS.gen_session_leadlag_genuine()
def cdaily(rows,rk=None):
    by=collections.defaultdict(list)
    for r in rows: by[r['date']].append(wins(r[rk] if rk else r['R']))
    return {d:sum(v)/len(v) for d,v in by.items()}
base_extra={'sub_xvol_pullback':0.45,'vp_euidx_pocgrav':0.30,'sub_mid_dn_revert':0.20,'session_leadlag_genuine':0.15}
DB={nm:cdaily(new_streams[nm]) for nm in ('sub_xvol_pullback','vp_euidx_pocgrav','sub_mid_dn_revert')}
DB['session_leadlag_genuine']=cdaily(slg)
CAND={'leadlag_top4':(pickle.load(open(HERE/'KB7_stream_leadlag_top4.pkl','rb')),None),
      'subh4_ll_fx':(new_streams['subh4_ll_fx'],None),
      'idb_crypto':(idb['idb_crypto'],'R_raw')}
def build_fwd(extra):
    parts={}
    for nm,cf in extra.items():
        cd=DB[nm] if nm in DB else cdaily(*CAND[nm])
        parts[nm]={d:v*cf for d,v in cd.items()}
    ad=sorted([d for d in (book_days|set().union(*[set(p) for p in parts.values()])) if d.year>=2025])
    return [sum(daily_sleeve[sl].get(d,0.0) for sl in book_sleeves)+sum(parts[nm].get(d,0.0) for nm in extra) for d in ad]
def max_size(comb,bud):
    best=None
    for r in [x/1000 for x in range(3,51)]:
        res=mc_series(comb,r,seed_base=777)
        if res['p_fail_dd']<=bud: best=(r,res)
        else: break
    return best
print("=== FORWARD-only (2025-26) iso-ruin @ P(maxDD-fail)<=2% ===")
print(f"{'variant':<30}{'meanR':>8}{'maxSize':>9}{'P(pass)':>9}{'medDays':>9}")
for nm,ec in [('clean4_base',dict(base_extra)),
              ('+leadlag_top4@0.30',{**base_extra,'leadlag_top4':0.30}),
              ('+leadlag_top4@0.45',{**base_extra,'leadlag_top4':0.45}),
              ('+subh4_ll_fx@0.30',{**base_extra,'subh4_ll_fx':0.30}),
              ('+idb_crypto@0.30',{**base_extra,'idb_crypto':0.30}),
              ('GROWTH_top4@0.30+subh4@0.30',{**base_extra,'leadlag_top4':0.30,'subh4_ll_fx':0.30})]:
    comb=build_fwd(ec); m=statistics.fmean(comb); b=max_size(comb,0.02)
    sz=f"{b[0]*100:.2f}%" if b else "n/a"
    print(f"{nm:<30}{m:>8.4f}{sz:>9}{(b[1]['p_pass'] if b else 0):>9.3f}{str(b[1]['med_days_pass'] if b else '-'):>9}")
