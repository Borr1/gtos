import json, datetime as dt
from collections import defaultdict, Counter
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def sess(h):
    if 0<=h<7: return 'tokyo'
    if 7<=h<12: return 'london'
    if 12<=h<21: return 'ny'
    return 'late'
out={}
for a in ['ftmo','redacted_account']:
    orders=[json.loads(l) for l in open(f'{BASE}/{a}_history_orders_get.jsonl')]
    strat=[o for o in orders if o['magic']==20260401]
    mkt=[o for o in orders if o['type'] in (0,1)]
    # open vs close: an OPEN order has position_id == ticket
    op=[o for o in mkt if o['position_id']==o['ticket']]
    cl=[o for o in mkt if o['position_id']!=o['ticket']]
    def lat(g): 
        v=sorted(o['time_done_msc']-o['time_setup_msc'] for o in g if o.get('time_done_msc'))
        return dict(n=len(v),median=v[len(v)//2] if v else None,p90=v[int(.9*(len(v)-1))] if v else None,max=v[-1] if v else None,
                    frac_lt50=round(sum(1 for x in v if x<50)/len(v),4) if v else None)
    persym={}; persess=defaultdict(lambda:[0,0])
    bys=defaultdict(list)
    for o in mkt: bys[o['symbol']].append(o)
    for s,g in bys.items():
        persym[s]=dict(n=len(g), filled=sum(1 for o in g if o['state']==4),
                       rate=round(sum(1 for o in g if o['state']==4)/len(g),5))
    for o in mkt:
        k=sess(dt.datetime.fromtimestamp(o['time_setup'],dt.timezone.utc).hour)
        persess[k][0]+=1; persess[k][1]+= (1 if o['state']==4 else 0)
    out[a]=dict(
      n_orders_total=len(orders), n_market=len(mkt), n_pending=sum(1 for o in orders if 2<=o['type']<=7),
      n_strategy_magic=len(strat),
      n_market_filled=sum(1 for o in mkt if o['state']==4),
      market_fill_rate=round(sum(1 for o in mkt if o['state']==4)/len(mkt),5),
      n_strategy_market=sum(1 for o in strat if o['type'] in (0,1)),
      strategy_fill_rate=round(sum(1 for o in strat if o['type'] in (0,1) and o['state']==4)/max(1,sum(1 for o in strat if o['type'] in (0,1))),5),
      n_rejected=sum(1 for o in orders if o['state']==5),
      rejected_detail=[dict(ticket=o['ticket'],symbol=o['symbol'],comment=o['comment'],
                            utc=dt.datetime.fromtimestamp(o['time_setup'],dt.timezone.utc).isoformat(),
                            vol=o['volume_initial'],magic=o['magic']) for o in orders if o['state']==5],
      latency_open_ms=lat(op), latency_close_ms=lat(cl),
      n_open=len(op), n_close=len(cl),
      fill_rate_per_symbol=dict(sorted(persym.items(), key=lambda kv:-kv[1]['n'])),
      fill_rate_per_session_utc={k:dict(n=v[0],filled=v[1],rate=round(v[1]/v[0],5)) for k,v in sorted(persess.items())})
json.dump(out,open(OUTD+'/L10_FILLRATE_V1.json','w'),indent=1)
for a,o in out.items():
    print('==',a,'orders',o['n_orders_total'],'market',o['n_market'],'pending',o['n_pending'],
          'fill_rate',o['market_fill_rate'],'strategy_fill_rate',o['strategy_fill_rate'],'rejected',o['n_rejected'])
    print('   open',o['n_open'],o['latency_open_ms'])
    print('   close',o['n_close'],o['latency_close_ms'])
    print('   session',o['fill_rate_per_session_utc'])
