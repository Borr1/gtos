import json, sys, datetime as dt
sys.path.insert(0,'/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801')
from collections import defaultdict, Counter
from src.costs.spread_model import spread_price, SpreadModelError
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
tick_sets={a:set(json.loads(l)['ticket'] for l in open(f'{BASE}/{a}_history_deals_get.jsonl')) for a in ['ftmo','redacted_account']}
rows=[json.loads(l) for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl')]
F=[]
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}
    dcr=r.get('deal_cost_reconciliation') or {}; pcm=r.get('pretrade_cost_model') or {}
    tc=pcm.get('tick_cost') or {}
    if tc.get('spread_price') is None: continue
    dtk=dcr.get('deal_ticket'); acct=None
    for a,s in tick_sets.items():
        if dtk in s: acct=a; break
    F.append(dict(sym=req.get('symbol'), acct=acct, t=(r.get('identity') or {}).get('decision_time_utc'),
                  real_spread_price=tc['spread_price'], real_spread_r=tc.get('spread_r'), sld=pcm.get('sl_distance')))
print('fills with quote:',len(F),'acct',Counter(x['acct'] for x in F))
ACC={'ftmo':'FTMO','redacted_account':'redacted_account'}
res=[];errs=Counter()
for x in F:
    if not x['acct'] or not x['t']: errs['no_acct']+=1; continue
    at=dt.datetime.fromisoformat(x['t'])
    for band in ('low','mid','high'):
        try:
            e=spread_price(x['sym'], ACC[x['acct']], at, band=band)
            v=getattr(e,'price',None) if not isinstance(e,(int,float)) else e
            if v is None: v=getattr(e,'spread_price',None)
            x['model_'+band]=v
            x['model_'+band+'_status']=str(getattr(e,'coverage',None) or getattr(e,'status',None) or getattr(e,'source',None))
        except SpreadModelError as ex:
            x['model_'+band]=None; errs[str(ex)[:60]]+=1
        except Exception as ex:
            x['model_'+band]=None; errs[type(ex).__name__+':'+str(ex)[:50]]+=1
    res.append(x)
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[z for z in v if z is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p10=round(q(v,.1),r),p90=round(q(v,.9),r),min=round(min(v),r),max=round(max(v),r))
out={'n':len(res),'errors':dict(errs.most_common(10))}
for band in ('low','mid','high'):
    ratios=[x['model_'+band]/x['real_spread_price'] for x in res if x.get('model_'+band) and x['real_spread_price']]
    out['ratio_model_over_real_'+band]=S(ratios,4)
    out['model_spread_r_'+band]=S([ (x['model_'+band]/x['sld']) for x in res if x.get('model_'+band) and x['sld']])
out['real_spread_r']=S([x['real_spread_r'] for x in res])
bysym=defaultdict(list)
for x in res:
    if x.get('model_mid') and x['real_spread_price']: bysym[(x['acct'],x['sym'])].append(x['model_mid']/x['real_spread_price'])
out['ratio_by_symbol_mid']={f'{a}:{s}':dict(n=len(v),mean=round(sum(v)/len(v),4),median=round(sorted(v)[len(v)//2],4)) for (a,s),v in sorted(bysym.items())}
json.dump(dict(summary=out,rows=res),open(OUTD+'/L10_SPREADMODEL_VS_REAL_V1.json','w'),indent=0)
print('errors',out['errors'])
print('REAL spread_r',out['real_spread_r'])
for band in ('low','mid','high'):
    print(band,'ratio model/real:',out['ratio_model_over_real_'+band],' model spread_r:',out['model_spread_r_'+band])
print('by symbol (mid):')
for k,v in list(out['ratio_by_symbol_mid'].items())[:18]: print('  ',k,v)
