import json, os, datetime as dt
from collections import Counter, defaultdict
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
OUT='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/L10_MT5_CENSUS_V1.json'
OTYPE={0:'BUY',1:'SELL',2:'BUY_LIMIT',3:'SELL_LIMIT',4:'BUY_STOP',5:'SELL_STOP',6:'BUY_STOP_LIMIT',7:'SELL_STOP_LIMIT',8:'CLOSE_BY'}
OSTATE={0:'STARTED',1:'PLACED',2:'CANCELED',3:'PARTIAL',4:'FILLED',5:'REJECTED',6:'EXPIRED',7:'REQ_ADD',8:'REQ_MOD',9:'REQ_CANCEL'}
DTYPE={0:'BUY',1:'SELL',2:'BALANCE',3:'CREDIT',4:'CHARGE',5:'CORRECTION',6:'BONUS',7:'COMMISSION',8:'COMM_DAILY',9:'COMM_MONTHLY',10:'COMM_AGENT_DAILY',11:'COMM_AGENT_MONTHLY',12:'INTEREST',13:'DEAL_DIVIDEND',15:'DEAL_DIVIDEND_FRANKED',16:'DEAL_TAX'}
DENTRY={0:'IN',1:'OUT',2:'INOUT',3:'OUT_BY'}
FILLING={0:'FOK',1:'IOC',2:'RETURN',3:'BOC'}
TTIME={0:'GTC',1:'DAY',2:'SPECIFIED',3:'SPECIFIED_DAY'}
REASON={0:'CLIENT',1:'MOBILE',2:'WEB',3:'EXPERT',4:'SL',5:'TP',6:'SO',7:'ROLLOVER',8:'VMARGIN',9:'SPLIT'}
def iso(ts):
    if not ts: return None
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat()
res={}
for acct in ['ftmo','redacted_account']:
    orders=[json.loads(l) for l in open(f'{BASE}/{acct}_history_orders_get.jsonl')]
    deals=[json.loads(l) for l in open(f'{BASE}/{acct}_history_deals_get.jsonl')]
    a={}
    a['n_orders']=len(orders); a['n_deals']=len(deals)
    ts=[o['time_setup'] for o in orders if o.get('time_setup')]
    a['orders_window_utc']=[iso(min(ts)),iso(max(ts))] if ts else None
    td=[d['time'] for d in deals if d.get('time')]
    a['deals_window_utc']=[iso(min(td)),iso(max(td))] if td else None
    a['order_type_x_state']={f'{OTYPE.get(o["type"],o["type"])}|{OSTATE.get(o["state"],o["state"])}':c for o,c in Counter((o['type'],o['state']) for o in orders).items()} if False else dict(Counter(f'{OTYPE.get(o["type"],o["type"])}|{OSTATE.get(o["state"],o["state"])}' for o in orders))
    a['order_type_counts']=dict(Counter(OTYPE.get(o['type'],o['type']) for o in orders))
    a['order_state_counts']=dict(Counter(OSTATE.get(o['state'],o['state']) for o in orders))
    a['type_filling_counts']=dict(Counter(FILLING.get(o['type_filling'],o['type_filling']) for o in orders))
    a['type_time_counts']=dict(Counter(TTIME.get(o['type_time'],o['type_time']) for o in orders))
    a['order_reason_counts']=dict(Counter(REASON.get(o['reason'],o['reason']) for o in orders))
    a['order_magic_counts']=dict(Counter(o['magic'] for o in orders))
    a['deal_type_counts']=dict(Counter(DTYPE.get(d['type'],d['type']) for d in deals))
    a['deal_entry_counts']=dict(Counter(DENTRY.get(d['entry'],d['entry']) for d in deals))
    a['deal_reason_counts']=dict(Counter(REASON.get(d['reason'],d['reason']) for d in deals))
    a['deal_symbols']=dict(Counter(d['symbol'] for d in deals if d['symbol']).most_common())
    # PENDING orders (limit/stop) resolution
    pend=[o for o in orders if o['type']>=2 and o['type']<=7]
    a['n_pending_orders']=len(pend)
    a['pending_state_counts']=dict(Counter(OSTATE.get(o['state'],o['state']) for o in pend))
    a['pending_type_counts']=dict(Counter(OTYPE.get(o['type'],o['type']) for o in pend))
    sits=[]
    for o in pend:
        if o.get('time_setup') and o.get('time_done'):
            sits.append({'ticket':o['ticket'],'symbol':o['symbol'],'type':OTYPE.get(o['type']),'state':OSTATE.get(o['state']),
                         'sit_s':o['time_done']-o['time_setup'],'expiration':o.get('time_expiration'),
                         'setup_utc':iso(o['time_setup']),'done_utc':iso(o['time_done'])})
    a['pending_resolutions']=sits
    # MARKET order latency: time_setup_msc -> time_done_msc
    mkt=[o for o in orders if o['type'] in (0,1)]
    lat=[(o['time_done_msc']-o['time_setup_msc']) for o in mkt if o.get('time_done_msc') and o.get('time_setup_msc')]
    lat.sort()
    def q(v,p):
        if not v: return None
        i=int(round(p*(len(v)-1))); return v[i]
    a['market_order_latency_ms']={'n':len(lat),'min':q(lat,0),'p25':q(lat,.25),'median':q(lat,.5),'p75':q(lat,.75),'p90':q(lat,.9),'p99':q(lat,.99),'max':q(lat,1),'mean':(sum(lat)/len(lat) if lat else None)}
    a['market_order_state_counts']=dict(Counter(OSTATE.get(o['state'],o['state']) for o in mkt))
    # partial fills: volume_current != 0 on filled
    a['n_orders_partial_state']=sum(1 for o in orders if o['state']==3)
    a['n_filled_with_residual_volume']=sum(1 for o in orders if o['state']==4 and o.get('volume_current',0)>0)
    res[acct]=a
json.dump(res,open(OUT,'w'),indent=1)
# compact print
for acct,a in res.items():
    print('==',acct,'orders',a['n_orders'],'deals',a['n_deals'])
    print('  orders window',a['orders_window_utc'])
    print('  deals window',a['deals_window_utc'])
    print('  types',a['order_type_counts'])
    print('  states',a['order_state_counts'])
    print('  filling',a['type_filling_counts'],'time',a['type_time_counts'])
    print('  pending',a['n_pending_orders'],a['pending_state_counts'],a['pending_type_counts'])
    print('  lat_ms',{k:v for k,v in a['market_order_latency_ms'].items()})
    print('  deal_entry',a['deal_entry_counts'],'deal_reason',a['deal_reason_counts'])
    print('  partials',a['n_orders_partial_state'],a['n_filled_with_residual_volume'])
