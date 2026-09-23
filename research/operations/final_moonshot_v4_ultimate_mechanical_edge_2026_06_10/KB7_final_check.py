"""KB7 final: (1) corr of each candidate vs the existing book sleeves (double-count radar);
(2) low-conf small-size diversification test: does a SMALL leadlag_top4 add at iso-ruin help at
the conservative end (0.5-0.75% effective) where the program actually deploys first?
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../../..')
import pickle, statistics, collections, math, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
import INTEG_portfolio_build as I
import INTEG_portfolio_build_w2 as W2
import INTEG_portfolio_build_w3 as W3
import KB6_session_stacks as SS
mc_series=W2.mc_series
def wins(r,hi=5.0): return max(-1.3,min(hi,r))
def pear(x,y):
    n=len(x)
    if n<8: return 0.0
    mx=sum(x)/n; my=sum(y)/n; sx=sum((a-mx)**2 for a in x); sy=sum((b-my)**2 for b in y)
    if sx==0 or sy==0: return 0.0
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/math.sqrt(sx*sy)

streams_w3=pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
days_w3,M_w3=W3.W2.build_matrix(streams_w3)
book_sleeves=W3.SLEEVES
daily_sleeve={sl:{day:M_w3[di][si] for di,day in enumerate(days_w3)} for si,sl in enumerate(book_sleeves)}
book_days=set(days_w3)
comb_book={d:sum(M_w3[di]) for di,d in enumerate(days_w3)}
new_streams=pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
idb=pickle.load(open(HERE/'KB7_idb_streams_cache.pkl','rb'))
slg=SS.gen_session_leadlag_genuine()
def cdaily(rows,rawkey=None):
    by=collections.defaultdict(list)
    for r in rows: by[r['date']].append(wins(r[rawkey] if rawkey else r['R']))
    return {d:sum(v)/len(v) for d,v in by.items()}
CANDS={'leadlag_top4':(pickle.load(open(HERE/'KB7_stream_leadlag_top4.pkl','rb')),None),
       'subh4_ll_fx':(new_streams['subh4_ll_fx'],None),
       'idb_crypto':(idb['idb_crypto'],'R_raw'),
       'idb_metals':(idb['idb_metals'],'R_raw')}
print("=== CORR of candidate daily-R vs each book sleeve + combined book (double-count radar) ===")
corrs={}
for nm,(rows,rk) in CANDS.items():
    cd=cdaily(rows,rk); cdays=set(cd)
    per={}
    for sl in book_sleeves:
        u=sorted(cdays|set(daily_sleeve[sl]))
        per[sl]=round(pear([cd.get(d,0.0) for d in u],[daily_sleeve[sl].get(d,0.0) for d in u]),3)
    u=sorted(cdays|book_days)
    vb=round(pear([cd.get(d,0.0) for d in u],[comb_book.get(d,0.0) for d in u]),3)
    top=sorted(per.items(),key=lambda kv:-abs(kv[1]))[:3]
    corrs[nm]=dict(vs_book=vb, top3=top)
    print(f"  {nm:<16} vs_book={vb:+.3f}  top|sleeve|: "+", ".join(f"{s}={v:+.3f}" for s,v in top))

# low-end iso-ruin: very tight budget 0.5% maxDD-fail, conservative deploy regime
base_extra={'sub_xvol_pullback':0.45,'vp_euidx_pocgrav':0.30,'sub_mid_dn_revert':0.20,'session_leadlag_genuine':0.15}
DAILY_BASE={nm:cdaily(new_streams[nm]) for nm in ('sub_xvol_pullback','vp_euidx_pocgrav','sub_mid_dn_revert')}
DAILY_BASE['session_leadlag_genuine']=cdaily(slg)
def build(extra):
    parts={}
    for nm,cf in extra.items():
        if nm in DAILY_BASE: cd=DAILY_BASE[nm]
        else: cd=cdaily(*CANDS[nm])
        parts[nm]={d:v*cf for d,v in cd.items()}
    ad=sorted(book_days|set().union(*[set(p) for p in parts.values()]))
    return [sum(daily_sleeve[sl].get(d,0.0) for sl in book_sleeves)+sum(parts[nm].get(d,0.0) for nm in extra) for d in ad]
def max_size(comb,bud,stress=False):
    s=[(v*1.5 if v<0 else v) for v in comb] if stress else comb
    best=None
    for r in [x/2000 for x in range(6,80)]:  # 0.3%..4% in 0.05% steps
        res=mc_series(s,r,seed_base=(999 if stress else 1))
        if res['p_fail_dd']<=bud: best=(r,res)
        else: break
    return best
print("\n=== ISO-RUIN at TIGHT budget P(maxDD-fail)<=0.5% (conservative deploy regime) ===")
V={'clean4_base':dict(base_extra),
   '+leadlag_top4@0.20':{**base_extra,'leadlag_top4':0.20},
   '+leadlag_top4@0.30':{**base_extra,'leadlag_top4':0.30},
   '+idb_crypto@0.20':{**base_extra,'idb_crypto':0.20}}
print(f"{'variant':<26}{'meanR':>8}{'maxSize':>9}{'P(pass)':>9}{'medDays':>9}")
res={}
for nm,ec in V.items():
    comb=build(ec); m=statistics.fmean(comb); b=max_size(comb,0.005)
    res[nm]=dict(mean=round(m,5), size=b[0] if b else None, p_pass=round(b[1]['p_pass'],4) if b else None, med_days=b[1]['med_days_pass'] if b else None)
    sz=f"{b[0]*100:.2f}%" if b else "n/a"; print(f"{nm:<26}{m:>8.4f}{sz:>9}{(b[1]['p_pass'] if b else 0):>9.3f}{str(b[1]['med_days_pass'] if b else '-'):>9}")
json.dump({'corrs':corrs,'iso_ruin_tight':res}, open(HERE/'KB7_FINAL_CHECK_RESULT.json','w'), indent=1, default=str)
print('\nwrote KB7_FINAL_CHECK_RESULT.json')
