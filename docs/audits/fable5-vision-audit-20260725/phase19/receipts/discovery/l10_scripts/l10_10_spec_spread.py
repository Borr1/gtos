import json
from collections import defaultdict, Counter
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
rows=[json.loads(l) for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl')]
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p10=round(q(v,.1),r),p90=round(q(v,.9),r),min=round(min(v),r),max=round(max(v),r))
F=[]; specs={}
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}
    dcr=r.get('deal_cost_reconciliation') or {}; pcm=r.get('pretrade_cost_model') or {}
    fill=dcr.get('broker_entry_price'); reqp=req.get('price'); sld=pcm.get('sl_distance')
    tc=pcm.get('tick_cost') or {}
    sp=(pcm.get('symbol_spec') or {}).get('fields') or {}
    sym=req.get('symbol')
    if sym and sym not in specs and sp: specs[sym]=sp
    if fill is None or reqp is None or not sld: continue
    side='LONG' if req.get('type')==0 else 'SHORT'
    sign=1.0 if side=='LONG' else -1.0
    ttv=sp.get('trade_tick_value'); tts=sp.get('trade_tick_size')
    usd_per_unit_per_lot=(ttv/tts) if (ttv and tts) else None
    cash_risk=(sld*usd_per_unit_per_lot*req.get('volume')) if usd_per_unit_per_lot else None
    comm=dcr.get('commission')
    F.append(dict(sym=sym, side=side, vol=req.get('volume'),
        req=reqp, fill=fill, sld=sld,
        slip_price=(fill-reqp)*sign, slip_r=(fill-reqp)*sign/sld,
        real_bid=tc.get('bid'), real_ask=tc.get('ask'),
        real_spread_price=tc.get('spread_price'), real_spread_r=tc.get('spread_r'),
        quote_status=tc.get('source_status'), quote_time=tc.get('time_utc'),
        request_at_ask=(abs(reqp-(tc.get('ask') or -1))<1e-9), request_at_bid=(abs(reqp-(tc.get('bid') or -1))<1e-9),
        comm_usd=comm, cash_risk_usd=cash_risk,
        comm_r=(abs(comm)/cash_risk if (comm is not None and cash_risk) else None),
        stops_level=sp.get('trade_stops_level'), freeze_level=sp.get('trade_freeze_level'),
        point=sp.get('point'), swap_mode=sp.get('swap_mode'),
        swap_long=sp.get('swap_long'), swap_short=sp.get('swap_short'),
        contract=sp.get('trade_contract_size'), ttv=ttv, tts=tts,
        vol_min=sp.get('volume_min'), vol_step=sp.get('volume_step'),
        m_spread_r=pcm.get('spread_r'), m_total_cost_r=pcm.get('total_cost_r')))
out={}
out['n']=len(F)
out['request_side_convention']=dict(
  long_at_ask=sum(1 for x in F if x['side']=='LONG' and x['request_at_ask']),
  long_n=sum(1 for x in F if x['side']=='LONG'),
  short_at_bid=sum(1 for x in F if x['side']=='SHORT' and x['request_at_bid']),
  short_n=sum(1 for x in F if x['side']=='SHORT'),
  wrong_side=sum(1 for x in F if (x['side']=='LONG' and x['request_at_bid']) or (x['side']=='SHORT' and x['request_at_ask'])))
out['real_spread_r_at_request']=S([x['real_spread_r'] for x in F])
out['pretrade_model_spread_r']=S([x['m_spread_r'] for x in F])
out['spread_r_model_minus_real']=S([ (x['m_spread_r']-x['real_spread_r']) for x in F if x['m_spread_r'] is not None and x['real_spread_r'] is not None])
out['commission_r_real']=S([x['comm_r'] for x in F])
out['quote_status']=dict(Counter(x['quote_status'] for x in F))
def cls(s):
    if s in ('BTCUSD','ETHUSD','AVAUSD','DASHUSD'): return 'crypto'
    if 'XAU' in s or 'XAG' in s: return 'metals'
    if any(k in s for k in ('GER','JP225','UK100','US30','US100','US500','SPX','NDX','NAS')): return 'index'
    return 'fx'
bc=defaultdict(list)
for x in F: bc[cls(x['sym'])].append(x)
out['by_class']={c:dict(n=len(g), real_spread_r=S([x['real_spread_r'] for x in g]),
                        slip_r=S([x['slip_r'] for x in g]),
                        comm_r=S([x['comm_r'] for x in g]),
                        slip_over_spread=S([ (x['slip_price']/x['real_spread_price']) for x in g if x['real_spread_price']]))
                 for c,g in sorted(bc.items())}
out['symbol_specs']={s:{k:v for k,v in sp.items() if k in ('trade_stops_level','trade_freeze_level','point','volume_min','volume_step','volume_max','trade_contract_size','trade_tick_size','trade_tick_value','swap_mode','swap_long','swap_short','swap_rollover3days','filling_mode','spread','trade_mode')} for s,sp in sorted(specs.items())}
json.dump(dict(summary=out, fills=F), open(OUTD+'/L10_SPEC_SPREAD_V1.json','w'), indent=0)
print('n',out['n'])
print('side convention:',out['request_side_convention'])
print('REAL spread_r at request:',out['real_spread_r_at_request'])
print('PRETRADE MODEL spread_r  :',out['pretrade_model_spread_r'])
print('model-real:',out['spread_r_model_minus_real'])
print('REAL commission_r:',out['commission_r_real'])
print('quote status:',out['quote_status'])
for c,v in out['by_class'].items():
    print(' ',c,'n',v['n'],'realSpreadR',v['real_spread_r']['mean'] if v['real_spread_r'] else None,
          'slipR',v['slip_r']['mean'],'commR',(v['comm_r'] or {}).get('mean'),'slip/spread',(v['slip_over_spread'] or {}).get('mean'))
