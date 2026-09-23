import json, statistics as st, datetime as dt
from collections import Counter, defaultdict
SRC='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs/broker_order_lifecycle_capture_v4.jsonl'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
rows=[json.loads(l) for l in open(SRC)]
R=[]
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}
    dcr=r.get('deal_cost_reconciliation') or {}; pcm=r.get('pretrade_cost_model') or {}
    ident=r.get('identity') or {}
    fill=dcr.get('broker_entry_price'); reqp=req.get('price'); sl=req.get('sl')
    if fill is None or reqp is None: continue
    side = 'LONG' if req.get('type')==0 else 'SHORT'
    sign = 1.0 if side=='LONG' else -1.0
    slip_price = (fill-reqp)*sign          # >0 = adverse (paid worse)
    sld = pcm.get('sl_distance')
    if not sld and sl: sld=abs(reqp-sl)
    slip_r = (slip_price/sld) if sld else None
    R.append(dict(cid=ident.get('candidate_id'), sym=ident.get('broker_symbol') or req.get('symbol'),
      t=ident.get('decision_time_utc'), side=side, vol=req.get('volume'), dev=req.get('deviation'),
      req=reqp, fill=fill, sl=sl, sl_distance=sld,
      slip_price=slip_price, slip_r=slip_r,
      comm=dcr.get('commission'), swap=dcr.get('swap'),
      m_spread_price=pcm.get('spread_price'), m_spread_r=pcm.get('spread_r'),
      m_slip_r=pcm.get('expected_slippage_r'), m_total_cost_r=pcm.get('total_cost_r'),
      m_swap=pcm.get('swap'), m_tick_cost=pcm.get('tick_cost'), m_risk_pct=pcm.get('risk_pct'),
      m_comm_status=pcm.get('commission_model_status'), m_slip_src=pcm.get('expected_slippage_source'),
      send=oso.get('order_send_time_utc'), res=oso.get('order_result_time_utc'),
      spec=pcm.get('symbol_spec')))
print('n with fill+req:',len(R))
def q(v,p):
    v=sorted(v);
    if not v: return None
    return v[int(round(p*(len(v)-1)))]
def stats(v):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),6),median=round(q(v,.5),6),p10=round(q(v,.1),6),p25=round(q(v,.25),6),
                p75=round(q(v,.75),6),p90=round(q(v,.9),6),min=round(min(v),6),max=round(max(v),6))
slipr=[x['slip_r'] for x in R if x['slip_r'] is not None]
print('SLIP_R (adverse>0):', stats(slipr))
print('abs SLIP_R:', stats([abs(x) for x in slipr]))
print('zero slip rows:', sum(1 for x in slipr if abs(x)<1e-12), 'of', len(slipr))
print('adverse:', sum(1 for x in slipr if x>1e-12), 'favourable:', sum(1 for x in slipr if x<-1e-12))
print('MODELLED slip_r:', stats([x['m_slip_r'] for x in R]))
print('MODELLED spread_r:', stats([x['m_spread_r'] for x in R]))
print('MODELLED total_cost_r:', stats([x['m_total_cost_r'] for x in R]))
print('slip_src', Counter(x['m_slip_src'] for x in R))
print('comm_status', Counter(x['m_comm_status'] for x in R))
print('symbols', Counter(x['sym'] for x in R).most_common(12))
json.dump(R, open(OUTD+'/L10_SLIP_RECORDS_V1.json','w'), indent=0)
