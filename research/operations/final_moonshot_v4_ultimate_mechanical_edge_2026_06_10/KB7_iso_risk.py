"""KB7 — ISO-RISK (iso-P(maxDD-fail)) speed comparison: the HONEST growth test.

For each book, find the LARGEST risk size that keeps P(maxDD-fail) <= a budget (under BOTH
the all-history base MC and the 1.5x stress MC), then report median days-to-target at that size.
The book that reaches target FASTEST at the SAME ruin budget is the growth winner. This removes
the vol-match penalty and the raw-size confound in one move: it's the speed-at-fixed-safety curve.
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
def wins(r,hi=5.0): return max(-1.3,min(hi,r))

streams_w3=pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
days_w3,M_w3=W3.W2.build_matrix(streams_w3)
book_sleeves=W3.SLEEVES
daily_sleeve={sl:{} for sl in book_sleeves}
for di,day in enumerate(days_w3):
    for si,sl in enumerate(book_sleeves): daily_sleeve[sl][day]=M_w3[di][si]
book_days=set(days_w3)
new_streams=pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
idb=pickle.load(open(HERE/'KB7_idb_streams_cache.pkl','rb'))
slg=SS.gen_session_leadlag_genuine()
def cdaily(rows,rawkey=None,cap=5.0):
    by=collections.defaultdict(list)
    for r in rows: by[r['date']].append(wins(r[rawkey] if rawkey else r['R'],cap))
    return {d:sum(v)/len(v) for d,v in by.items()}
base_extra={'sub_xvol_pullback':0.45,'vp_euidx_pocgrav':0.30,'sub_mid_dn_revert':0.20,'session_leadlag_genuine':0.15}
DAILY_BASE={nm:cdaily(new_streams[nm]) for nm in ('sub_xvol_pullback','vp_euidx_pocgrav','sub_mid_dn_revert')}
DAILY_BASE['session_leadlag_genuine']=cdaily(slg)
CANDS={
 'leadlag_full':pickle.load(open(HERE/'KB7_stream_leadlag_full.pkl','rb')),
 'leadlag_top4':pickle.load(open(HERE/'KB7_stream_leadlag_top4.pkl','rb')),
 'leadlag_hisharpe2':pickle.load(open(HERE/'KB7_stream_leadlag_hisharpe2.pkl','rb')),
 'subh4_ll_fx':new_streams['subh4_ll_fx'],
 'idb_crypto':idb['idb_crypto']}
RAWKEY={'idb_crypto':'R_raw'}
def cand_daily(nm): return cdaily(CANDS[nm],RAWKEY.get(nm))
def build_comb(extra):
    parts={}
    for nm,cf in extra.items():
        cd=DAILY_BASE[nm] if nm in DAILY_BASE else cand_daily(nm)
        parts[nm]={d:v*cf for d,v in cd.items()}
    ad=sorted(book_days | set().union(*[set(p) for p in parts.values()]) if parts else book_days)
    comb=[sum(daily_sleeve[sl].get(d,0.0) for sl in book_sleeves)+sum(parts[nm].get(d,0.0) for nm in extra) for d in ad]
    fwd=[v for v,d in zip(comb,ad) if d.year>=2025]
    return comb,fwd

def max_size_for_budget(comb, dd_budget, stress=False, seed=1, lo=0.003, hi=0.05):
    """binary-search the largest risk with P(maxDD-fail) <= budget; return (size, mc-dict)."""
    s=[(v*1.5 if v<0 else v) for v in comb] if stress else comb
    best=None
    # scan a fine grid (binary search is fine but MC noise -> grid is more robust)
    grid=[x/1000 for x in range(3,51)]
    for r in grid:
        res=mc_series(s, r, seed_base=(999 if stress else seed))
        if res['p_fail_dd']<=dd_budget:
            best=(r,res)
        else:
            break
    return best

VARIANTS=collections.OrderedDict([
 ('clean4_base', dict(base_extra)),
 ('+leadlag_full@0.20', {**base_extra,'leadlag_full':0.20}),
 ('+leadlag_top4@0.30', {**base_extra,'leadlag_top4':0.30}),
 ('+leadlag_top4@0.45', {**base_extra,'leadlag_top4':0.45}),
 ('+leadlag_hisharpe2@0.30', {**base_extra,'leadlag_hisharpe2':0.30}),
 ('+subh4_ll_fx@0.30', {**base_extra,'subh4_ll_fx':0.30}),
 ('+idb_crypto@0.30', {**base_extra,'idb_crypto':0.30}),
 ('GROWTH_top4@0.45+subh4@0.30', {**base_extra,'leadlag_top4':0.45,'subh4_ll_fx':0.30}),
 ('GROWTH_top4@0.30+subh4@0.30+idbC@0.30', {**base_extra,'leadlag_top4':0.30,'subh4_ll_fx':0.30,'idb_crypto':0.30}),
])
OUT={}
for BUD,tag in [(0.02,'budget2pct'),(0.05,'budget5pct')]:
    print(f"\n===== ISO-RISK at P(maxDD-fail) <= {BUD:.0%} (base MC) -> speed (median days) =====")
    print(f"{'variant':<42}{'maxSize':>8}{'P(pass)':>9}{'medDays':>8}{'meanR':>8} | {'STRESS:maxSize':>14}{'medDays':>8}{'P(pass)':>9}")
    OUT[tag]={}
    for nm,ec in VARIANTS.items():
        comb,fwd=build_comb(ec); m=statistics.fmean(comb)
        b=max_size_for_budget(comb,BUD,stress=False)
        bs=max_size_for_budget(comb,BUD,stress=True)
        rec=dict(mean_R=round(m,5))
        if b: rec.update(size=b[0],p_pass=round(b[1]['p_pass'],4),med_days=b[1]['med_days_pass'])
        if bs: rec.update(stress_size=bs[0],stress_med_days=bs[1]['med_days_pass'],stress_p_pass=round(bs[1]['p_pass'],4))
        OUT[tag][nm]=rec
        sz=f"{b[0]*100:.1f}%" if b else "n/a"; md=str(b[1]['med_days_pass']) if b else "-"; pp=f"{b[1]['p_pass']:.3f}" if b else "-"
        ssz=f"{bs[0]*100:.1f}%" if bs else "n/a"; smd=str(bs[1]['med_days_pass']) if bs else "-"; spp=f"{bs[1]['p_pass']:.3f}" if bs else "-"
        print(f"{nm:<42}{sz:>8}{pp:>9}{md:>8}{m:>8.4f} | {ssz:>14}{smd:>8}{spp:>9}")
json.dump(OUT, open(HERE/'KB7_ISO_RISK_RESULT.json','w'), indent=1, default=str)
print("\nwrote KB7_ISO_RISK_RESULT.json")
