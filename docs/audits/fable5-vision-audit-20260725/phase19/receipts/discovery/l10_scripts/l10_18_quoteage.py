import json, datetime as dt
from collections import Counter
SLD='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
rows=[json.loads(l) for l in open(f'{SLD}/broker_order_lifecycle_capture_v4.jsonl')]
ages=[]; devs=[]; unres=[]
for r in rows:
    if r.get('stage') not in ('entry_fill_reconciled','pre_send'): continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}
    pcm=r.get('pretrade_cost_model') or {}; tc=pcm.get('tick_cost') or {}
    dcr=r.get('deal_cost_reconciliation') or {}
    qt=tc.get('time_utc'); stt=oso.get('order_send_time_utc'); rst=oso.get('order_result_time_utc')
    if qt and stt:
        try:
            a=(dt.datetime.fromisoformat(stt)-dt.datetime.fromisoformat(qt)).total_seconds()
            ages.append((a, req.get('symbol'), r.get('stage')))
        except Exception: pass
    if r.get('stage')=='entry_fill_reconciled':
        fill=dcr.get('broker_entry_price'); reqp=req.get('price'); dev=req.get('deviation')
        pt=((pcm.get('symbol_spec') or {}).get('fields') or {}).get('point')
        if fill is not None and reqp is not None and dev and pt:
            sign=1.0 if req.get('type')==0 else -1.0
            slip_pts=abs((fill-reqp)*sign)/pt
            devs.append(dict(sym=req.get('symbol'),dev=dev,slip_pts=round(slip_pts,3),
                             used=round(slip_pts/dev,4) if dev else None,
                             spread_pts=round((tc.get('spread_price') or 0)/pt,2)))
        if dcr.get('account_history_lookup_status')=='UNRESOLVED_AFTER_HISTORY_ATTEMPT':
            unres.append(dict(sym=req.get('symbol'), t=(r.get('identity') or {}).get('decision_time_utc'),
                              attempts=dcr.get('account_history_lookup_attempt_count'),
                              err=str(dcr.get('account_history_lookup_error'))[:80]))
a=sorted(x[0] for x in ages)
def q(v,p): return v[int(round(p*(len(v)-1)))] if v else None
out=dict(quote_age_at_send_s=dict(n=len(a),mean=round(sum(a)/len(a),4),median=round(q(a,.5),4),p90=round(q(a,.9),4),p99=round(q(a,.99),4),min=round(min(a),4),max=round(max(a),4)),
  deviation_headroom=dict(n=len(devs),
     mean_used_frac=round(sum(d['used'] for d in devs if d['used'] is not None)/max(1,len(devs)),5),
     max_used_frac=round(max((d['used'] for d in devs if d['used'] is not None),default=0),5),
     n_over_50pct=sum(1 for d in devs if (d['used'] or 0)>0.5),
     n_over_90pct=sum(1 for d in devs if (d['used'] or 0)>0.9),
     deviation_values=dict(Counter(d['dev'] for d in devs).most_common(12)),
     largest_usage=sorted(devs,key=lambda d:-(d['used'] or 0))[:6]),
  unresolved_fills=dict(n=len(unres), rows=unres))
json.dump(out,open(D+'/L10_QUOTEAGE_DEV_V1.json','w'),indent=1)
print('quote age s:',out['quote_age_at_send_s'])
print('deviation:',{k:v for k,v in out['deviation_headroom'].items() if k!='largest_usage'})
print('largest usage:',out['deviation_headroom']['largest_usage'])
print('unresolved:',out['unresolved_fills']['n'], out['unresolved_fills']['rows'][:4])
