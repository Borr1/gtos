import gzip,json,collections,math
WS='w0_WORKING_SET.jsonl.gz'; AN='w0cap2_DECISION_ANCHOR_V1.jsonl.gz'
anc={}
for L in gzip.open(AN,'rt'):
    r=json.loads(L); anc[(r['candidate_id'],r['decision_time_utc'])]=r['mkt_r_prev_close']
rows=[]
for L in gzip.open(WS,'rt'):
    r=json.loads(L); m=anc.get((r['candidate_id'],r['decision_time_utc']))
    b='UNANCHORED' if m is None else ('past_stop' if m<=-1 else 'marketable' if m<0 else 'at_limit' if m==0 else 'resting')
    rows.append((b,r))
def st(v):
    v=[x for x in v if x is not None]
    if len(v)<2: return dict(n=len(v),mean=round(sum(v)/len(v),6) if v else None,t=None)
    m=sum(v)/len(v); sd=(sum((x-m)**2 for x in v)/(len(v)-1))**.5
    return dict(n=len(v),mean=round(m,6),t=round(m/(sd/math.sqrt(len(v))),3) if sd>0 else None)
out={'population':{'pool':len(rows),'at_limit_live_placeable':sum(1 for b,_ in rows if b=='at_limit')}}
out['at_limit_baseline']=st([r['fill_honest_walk_r'] for b,r in rows if b=='at_limit'])
out['pool_baseline']=st([r['fill_honest_walk_r'] for b,r in rows])
tabs={}
for fld in ['risk_finalizer_reason','selector_reason','final_blocker_class']:
    cnt=collections.Counter(str(r.get(fld)) for b,r in rows); t={}
    for val,n in cnt.most_common(20):
        allv=[r['fill_honest_walk_r'] for b,r in rows if str(r.get(fld))==val]
        lim=[r['fill_honest_walk_r'] for b,r in rows if str(r.get(fld))==val and b=='at_limit']
        t[val]={'ALL':st(allv),'AT_LIMIT':st(lim),'at_limit_share_pct':round(100*len(lim)/max(1,len(allv)),2)}
    tabs[fld]=t
out['tables']=tabs
# cost gate on the live-placeable cohort
kept=[r['fill_honest_walk_r'] for b,r in rows if b=='at_limit' and (r.get('spread_r') or 0)<=0.10 and (r.get('cost_r') or 0)<=0.15]
ref =[r['fill_honest_walk_r'] for b,r in rows if b=='at_limit' and not((r.get('spread_r') or 0)<=0.10 and (r.get('cost_r') or 0)<=0.15)]
out['frozen_cost_gate_on_live_placeable']={'kept':st(kept),'refused':st(ref)}
json.dump(out,open('OWNER_REPORT_GATE_CHECK_V1.json','w'),indent=1)
print('at_limit baseline',out['at_limit_baseline'])
print('gate kept',out['frozen_cost_gate_on_live_placeable']['kept'])
print('gate refused',out['frozen_cost_gate_on_live_placeable']['refused'])
