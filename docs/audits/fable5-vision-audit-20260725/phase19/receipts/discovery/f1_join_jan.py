import json,gzip,glob
from collections import defaultdict
ROOT="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725"
lane=f"{ROOT}/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl"
tr=[json.loads(l) for l in open(lane)]
tr=[r for r in tr if r.get('row_kind')=='trade']
want={(r['candidate_id'],r['decision_time_utc']) for r in tr}
wantc={r['candidate_id'] for r in tr}
hit={}; hitc=defaultdict(list)
for f in sorted(glob.glob('/tmp/pbg_full_jan/*.jsonl.gz')):
    with gzip.open(f,'rt') as fh:
        for line in fh:
            r=json.loads(line)
            if r['k']!=15: continue
            if r['cid'] in wantc:
                hitc[r['cid']].append(r)
                hit[(r['cid'],r['t'])]=r
print('taken trades',len(tr),'unique cid',len(wantc))
print('cid found in roster:',len(hitc))
print('(cid,decision_time) exact match:',sum(1 for k in want if k in hit))
# geometry
rows=[]
for r in tr:
    m=hit.get((r['candidate_id'],r['decision_time_utc']))
    if m is None:
        cands=hitc.get(r['candidate_id'])
        m=cands[0] if cands else None
    if m is None: continue
    d=abs(m['e']-m['sl'])
    rows.append(dict(sym=r['symbol'],entry=m['e'],sl=m['sl'],tp=m['tp'],d=d,
                     d_bps=d/m['e']*1e4,final_r=r['final_r'],cost_r=r['cost_r'],
                     net_r=r['net_r'],fam=m['f'],t=r['decision_time_utc']))
print('joined geometry rows',len(rows))
import statistics as st
print('taken risk distance bps: mean %.2f median %.2f min %.2f max %.2f'%(
    st.mean(x['d_bps'] for x in rows), st.median([x['d_bps'] for x in rows]),
    min(x['d_bps'] for x in rows), max(x['d_bps'] for x in rows)))
from collections import Counter
print('families:',Counter(x['fam'] for x in rows).most_common())
json.dump(rows,open('/tmp/f1/jan_taken_geom.json','w'),indent=1)
