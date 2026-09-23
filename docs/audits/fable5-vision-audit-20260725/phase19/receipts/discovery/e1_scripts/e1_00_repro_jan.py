"""e1 step 0: reproduce l10x_06_recost on January EXACTLY, plus an independent
min-spread_r check that needs no tick data at all."""
import json, gzip, statistics as st
from collections import defaultdict
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
ref=json.load(open(f'{D}/L10X_POOL_RECOST_V1.json'))
# --- INDEPENDENT: min / distribution of frozen spread_r per symbol, straight from the working set
per=defaultdict(list); tot=defaultdict(list); grs=defaultdict(list)
n=0; rows=[]
for l in gzip.open(f'{D}/w0_WORKING_SET.jsonl.gz','rt'):
    r=json.loads(l); n+=1
    s=r['symbol']; per[s].append(r['spread_r']); tot[s].append(r['expected_cost_r']); grs[s].append(r['gross_r'])
    rows.append((s,r['spread_r'],r['expected_cost_r'],r['gross_r'],r['entry_price'],r['risk_distance'],
                 r.get('stop_loss'),r.get('origin_family'),r.get('route_session'),r.get('decision_time_utc')))
def q(v,p):
    v=sorted(v); return v[max(0,min(len(v)-1,int(p*(len(v)-1))))]
out={'n_rows':n,'independent_min_spread_r_by_symbol':{}}
for s in sorted(per, key=lambda k:-len(per[k])):
    v=per[s]
    out['independent_min_spread_r_by_symbol'][s]={'n':len(v),'min':round(min(v),6),'p01':round(q(v,0.01),6),
      'median':round(st.median(v),6),'max':round(max(v),6),
      'n_pass_spread_limb':sum(1 for x in v if x<=0.10+1e-12),
      'n_pass_both':sum(1 for a,b in zip(v,tot[s]) if a<=0.10+1e-12 and b<=0.15+1e-12)}
# risk_distance sanity: |entry - stop|
bad=sum(1 for x in rows if x[6] is not None and abs(abs(x[4]-x[6])-x[5])>1e-9*max(1.0,abs(x[4])))
out['risk_distance_equals_abs_entry_minus_stop_violations']=bad
# spread in PRICE units implied by the frozen model
imp=defaultdict(list)
for s,sp,tc,g,ep,rd,sl,fam,ses,dt in rows: imp[s].append(sp*rd)
out['implied_frozen_spread_price_units']={s:{'median':round(st.median(v),8),'min':round(min(v),8),'max':round(max(v),8),
    'cv':round(st.pstdev(v)/st.mean(v),5) if st.mean(v) else None} for s,v in sorted(imp.items(),key=lambda kv:-len(kv[1]))}
# bps of entry price
impb=defaultdict(list)
for s,sp,tc,g,ep,rd,sl,fam,ses,dt in rows: impb[s].append(sp*rd/ep*1e4)
out['implied_frozen_spread_bps_of_entry']={s:{'median':round(st.median(v),5),'min':round(min(v),5),'max':round(max(v),5)}
    for s,v in sorted(impb.items(),key=lambda kv:-len(kv[1]))}
json.dump(out,open(f'{D}/E1_JAN_REPRO_INDEP_V1.json','w'),indent=1)
print('n=',n,'risk_distance violations=',bad)
print(f"{'sym':<12}{'n':>6}{'minSprR':>10}{'medSprR':>10}{'passSpr':>8}{'passBoth':>9}{'refPassF':>9}{'implBps':>9}")
for s,v in out['independent_min_spread_r_by_symbol'].items():
    rp=ref['per_symbol'].get(s,{}).get('n_pass_frozen','-')
    print(f"{s:<12}{v['n']:>6}{v['min']:>10.5f}{v['median']:>10.5f}{v['n_pass_spread_limb']:>8}{v['n_pass_both']:>9}{str(rp):>9}{out['implied_frozen_spread_bps_of_entry'][s]['median']:>9.3f}")
