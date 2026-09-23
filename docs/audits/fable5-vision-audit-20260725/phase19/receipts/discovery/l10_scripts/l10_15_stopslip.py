import json, datetime as dt
from collections import defaultdict
API='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
REASON={0:'CLIENT',1:'MOBILE',2:'WEB',3:'EXPERT',4:'SL',5:'TP'}
# 1) SL/TP timeline per position from runtime modify requests
tl=defaultdict(list)
for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl'):
    r=json.loads(l)
    if r.get('stage') not in ('sltp_modify_result',): continue
    req=r.get('request') or {}; res=r.get('result') or {}
    if res.get('retcode')!=10009: continue      # only applied modifies
    pos=req.get('position')
    if pos is None: continue
    t=r.get('generated_at_utc')
    tl[pos].append((t, req.get('sl'), req.get('tp')))
for p in tl: tl[p].sort()
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p10=round(q(v,.1),r),p90=round(q(v,.9),r),p99=round(q(v,.99),r),min=round(min(v),r),max=round(max(v),r))
recs=[]; cov={'with_timeline':0,'no_timeline':0}
for a in ['ftmo','redacted_account']:
    orders={}
    for l in open(f'{API}/{a}_history_orders_get.jsonl'):
        o=json.loads(l); orders[o['ticket']]=o
    bypos=defaultdict(list)
    for l in open(f'{API}/{a}_history_deals_get.jsonl'):
        d=json.loads(l)
        if d['type'] in (0,1) and d['symbol']: bypos[d['position_id']].append(d)
    for pos,legs in bypos.items():
        ins=[d for d in legs if d['entry']==0]; outs=[d for d in legs if d['entry']!=0]
        if not ins or not outs: continue
        e=ins[0]; eo=orders.get(e['order'])
        sl0=(eo or {}).get('sl'); tp0=(eo or {}).get('tp')
        side='LONG' if e['type']==0 else 'SHORT'; sign=1.0 if side=='LONG' else -1.0
        risk=abs(e['price']-sl0) if sl0 else None
        hist=tl.get(pos,[])
        cov['with_timeline' if hist else 'no_timeline']+=1
        for x in outs:
            rsn=REASON.get(x['reason'])
            if rsn not in ('SL','TP'): continue
            xt=dt.datetime.fromtimestamp(x['time'],dt.timezone.utc).isoformat()
            cur_sl, cur_tp = sl0, tp0
            for (t,s,tp) in hist:
                if t and t<=xt:
                    if s: cur_sl=s
                    if tp: cur_tp=tp
                else: break
            target = cur_sl if rsn=='SL' else cur_tp
            if not target or not risk: continue
            adv=(target-x['price'])*sign
            recs.append(dict(acct=a,sym=x['symbol'],side=side,reason=rsn,pos=pos,exit=x['price'],
                target=target,risk=risk,slip_price=adv,slip_r=adv/risk,t=xt,
                had_timeline=bool(hist), moved=(abs((cur_sl or 0)-(sl0 or 0))>1e-9)))
sl=[r for r in recs if r['reason']=='SL']; tp=[r for r in recs if r['reason']=='TP']
out=dict(coverage=cov, n_sl=len(sl), n_tp=len(tp),
  sl_slip_r=S([r['slip_r'] for r in sl]), tp_slip_r=S([r['slip_r'] for r in tp]),
  sl_moved=sum(1 for r in sl if r['moved']), sl_not_moved=sum(1 for r in sl if not r['moved']),
  sl_slip_r_moved=S([r['slip_r'] for r in sl if r['moved']]),
  sl_slip_r_static=S([r['slip_r'] for r in sl if not r['moved']]),
  sl_frac_exact=round(sum(1 for r in sl if abs(r['slip_r'])<1e-9)/max(1,len(sl)),4),
  sl_frac_adverse=round(sum(1 for r in sl if r['slip_r']>1e-9)/max(1,len(sl)),4),
  sl_frac_favourable=round(sum(1 for r in sl if r['slip_r']<-1e-9)/max(1,len(sl)),4),
  sl_worst=sorted([(round(r['slip_r'],4),r['sym'],r['t'][:19],r['acct']) for r in sl],reverse=True)[:8],
  by_account={a:dict(n=sum(1 for r in sl if r['acct']==a), slip_r=S([r['slip_r'] for r in sl if r['acct']==a])) for a in ('ftmo','redacted_account')})
json.dump(dict(summary=out,records=recs),open(OUTD+'/L10_STOP_SLIP_V1.json','w'),indent=0)
print('coverage',cov)
print('SL n',out['n_sl'],out['sl_slip_r'])
print('  static-stop n',out['sl_not_moved'],out['sl_slip_r_static'])
print('  moved-stop  n',out['sl_moved'],out['sl_slip_r_moved'])
print('  exact',out['sl_frac_exact'],'adverse',out['sl_frac_adverse'],'fav',out['sl_frac_favourable'])
print('  worst',out['sl_worst'])
print('TP n',out['n_tp'],out['tp_slip_r'])
print('  by acct',{a:(v['n'],(v['slip_r'] or {}).get('mean'),(v['slip_r'] or {}).get('p99')) for a,v in out['by_account'].items()})
