import json, datetime as dt
from collections import defaultdict, Counter
API='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
REASON={0:'CLIENT',1:'MOBILE',2:'WEB',3:'EXPERT',4:'SL',5:'TP',6:'SO',7:'ROLLOVER'}
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p10=round(q(v,.1),r),p90=round(q(v,.9),r),p99=round(q(v,.99),r),min=round(min(v),r),max=round(max(v),r))
out={}
allrec=[]
for a in ['ftmo','redacted_account']:
    orders={}
    for l in open(f'{API}/{a}_history_orders_get.jsonl'):
        o=json.loads(l); orders[o['ticket']]=o
    deals=[json.loads(l) for l in open(f'{API}/{a}_history_deals_get.jsonl')]
    bypos=defaultdict(list)
    for d in deals:
        if d['type'] in (0,1) and d['symbol']: bypos[d['position_id']].append(d)
    recs=[]
    for pos,legs in bypos.items():
        ins=[d for d in legs if d['entry']==0]; outs=[d for d in legs if d['entry']!=0]
        if not ins or not outs: continue
        e=ins[0]
        eo=orders.get(e['order'])
        if not eo: continue
        sl=eo.get('sl'); tp=eo.get('tp')
        side='LONG' if e['type']==0 else 'SHORT'
        sign=1.0 if side=='LONG' else -1.0
        risk=abs(e['price']-sl) if sl else None
        for x in outs:
            o=orders.get(x['order'])
            # exit order's OWN sl/tp at time of the closing order (broker stop uses the position's current sl)
            rsn=REASON.get(x['reason'])
            target=None
            if rsn=='SL': target=(o.get('sl') if o and o.get('sl') else sl)
            elif rsn=='TP': target=(o.get('tp') if o and o.get('tp') else tp)
            if target and risk:
                # adverse = filled worse than the stop/target for the trader
                adv=(target-x['price'])*sign if rsn=='SL' else (target-x['price'])*sign
                recs.append(dict(acct=a,sym=x['symbol'],side=side,reason=rsn,pos=pos,
                    exit_price=x['price'],target=target,risk=risk,
                    slip_price=adv, slip_r=adv/risk,
                    t=dt.datetime.fromtimestamp(x['time'],dt.timezone.utc).isoformat()))
    allrec+=recs
    sl_r=[r['slip_r'] for r in recs if r['reason']=='SL']
    tp_r=[r['slip_r'] for r in recs if r['reason']=='TP']
    out[a]=dict(n_sl=len(sl_r), sl_slip_r=S(sl_r), n_tp=len(tp_r), tp_slip_r=S(tp_r),
      sl_frac_adverse=round(sum(1 for x in sl_r if x>1e-9)/max(1,len(sl_r)),4),
      sl_frac_exact=round(sum(1 for x in sl_r if abs(x)<1e-9)/max(1,len(sl_r)),4),
      sl_worse_than_0p1R=sum(1 for x in sl_r if x>0.1),
      sl_worse_than_0p5R=sum(1 for x in sl_r if x>0.5),
      tp_frac_adverse=round(sum(1 for x in tp_r if x>1e-9)/max(1,len(tp_r)),4))
sl_all=[r['slip_r'] for r in allrec if r['reason']=='SL']
tp_all=[r['slip_r'] for r in allrec if r['reason']=='TP']
out['BOTH']=dict(n_sl=len(sl_all),sl_slip_r=S(sl_all),n_tp=len(tp_all),tp_slip_r=S(tp_all),
   sl_frac_exact=round(sum(1 for x in sl_all if abs(x)<1e-9)/max(1,len(sl_all)),4),
   sl_frac_adverse=round(sum(1 for x in sl_all if x>1e-9)/max(1,len(sl_all)),4),
   worst=sorted([(round(r['slip_r'],4),r['sym'],r['t'][:19]) for r in allrec if r['reason']=='SL'],reverse=True)[:6])
json.dump(dict(summary=out,records=allrec),open(OUTD+'/L10_EXIT_SLIP_V1.json','w'),indent=0)
for k,v in out.items():
    print('==',k); print('  SL n',v['n_sl'],v['sl_slip_r']); print('  TP n',v['n_tp'],v['tp_slip_r'])
    print('  sl exact',v.get('sl_frac_exact'),'adverse',v.get('sl_frac_adverse'),'>0.1R',v.get('sl_worse_than_0p1R'),'>0.5R',v.get('sl_worse_than_0p5R'))
    if 'worst' in v: print('  worst:',v['worst'])
