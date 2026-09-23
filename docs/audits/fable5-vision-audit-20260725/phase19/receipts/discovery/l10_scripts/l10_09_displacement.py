import json
from collections import Counter, defaultdict
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p10=round(q(v,.1),r),p25=round(q(v,.25),r),p75=round(q(v,.75),r),p90=round(q(v,.9),r),min=round(min(v),r),max=round(max(v),r))
out={}
# ---- A) lifecycle capture: pcm.entry_price (intended) vs broker fill
rows=[json.loads(l) for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl')]
A=[]
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}
    dcr=r.get('deal_cost_reconciliation') or {}; pcm=r.get('pretrade_cost_model') or {}
    fill=dcr.get('broker_entry_price'); reqp=req.get('price'); ip=pcm.get('entry_price'); sld=pcm.get('sl_distance')
    if fill is None or ip is None or not sld: continue
    sign=1.0 if req.get('type')==0 else -1.0
    A.append(dict(sym=req.get('symbol'), side='LONG' if req.get('type')==0 else 'SHORT',
        intended=ip, requested=reqp, fill=fill, sld=sld,
        disp_r=(fill-ip)*sign/sld, req_vs_int_r=((reqp-ip)*sign/sld) if reqp is not None else None,
        fill_vs_req_r=((fill-reqp)*sign/sld) if reqp is not None else None))
out['lifecycle_intended_vs_fill']=dict(
  n=len(A),
  displacement_r_fill_minus_intended=S([x['disp_r'] for x in A]),
  requested_minus_intended_r=S([x['req_vs_int_r'] for x in A]),
  fill_minus_requested_r=S([x['fill_vs_req_r'] for x in A]),
  n_requested_equals_intended=sum(1 for x in A if x['requested'] is not None and abs(x['requested']-x['intended'])<1e-9),
  frac_requested_equals_intended=round(sum(1 for x in A if x['requested'] is not None and abs(x['requested']-x['intended'])<1e-9)/max(1,len(A)),4))
byc=defaultdict(list)
def cls(s):
    if s in ('BTCUSD','ETHUSD','AVAUSD','DASHUSD'): return 'crypto'
    if 'XAU' in s or 'XAG' in s: return 'metals'
    if any(k in s for k in ('GER','JP225','UK100','US30','US100','US500','SPX','NDX','NAS')): return 'index'
    return 'fx'
for x in A: byc[cls(x['sym'])].append(x['disp_r'])
out['lifecycle_displacement_by_class']={c:S(v) for c,v in sorted(byc.items())}
# ---- B) legacy slippage.jsonl: entry_price (intended POI) vs fill_price
rows2=[json.loads(l) for l in open(f'{SL}/slippage.jsonl')]
B=[]
for r in rows2:
    ip=r.get('entry_price'); fp=r.get('fill_price'); sld=r.get('sl_distance'); d=r.get('direction')
    rq=r.get('requested_price')
    if not ip or not fp or not sld or not d: continue
    sign=1.0 if d=='LONG' else -1.0
    B.append(dict(sym=r.get('symbol'),side=d,intended=ip,fill=fp,sld=sld,
      disp_r=(fp-ip)*sign/sld, spread_at_request=r.get('spread_at_request'),
      slippage_price=r.get('slippage_price'), close_reason=r.get('close_reason'), ts=r.get('entry_time')))
out['legacy_slippage_intended_vs_fill']=dict(n=len(B),
  displacement_r=S([x['disp_r'] for x in B]),
  frac_adverse=round(sum(1 for x in B if x['disp_r']>1e-9)/max(1,len(B)),4),
  frac_zero=round(sum(1 for x in B if abs(x['disp_r'])<1e-9)/max(1,len(B)),4),
  window=[min(x['ts'] for x in B if x['ts']),max(x['ts'] for x in B if x['ts'])] if B else None,
  reported_slippage_price=S([x['slippage_price'] for x in B]))
json.dump(dict(summary=out, lifecycle_rows=A, legacy_rows=B), open(OUTD+'/L10_DISPLACEMENT_V1.json','w'), indent=0)
print('A n',out['lifecycle_intended_vs_fill']['n'])
print(' disp_r(fill-intended):',out['lifecycle_intended_vs_fill']['displacement_r_fill_minus_intended'])
print(' req-intended:',out['lifecycle_intended_vs_fill']['requested_minus_intended_r'])
print(' fill-req:',out['lifecycle_intended_vs_fill']['fill_minus_requested_r'])
print(' frac req==intended:',out['lifecycle_intended_vs_fill']['frac_requested_equals_intended'])
print(' by class:',{c:(v['n'],v['mean'],v['median']) for c,v in out['lifecycle_displacement_by_class'].items()})
print('B n',out['legacy_slippage_intended_vs_fill']['n'],out['legacy_slippage_intended_vs_fill']['displacement_r'])
print(' frac_adverse',out['legacy_slippage_intended_vs_fill']['frac_adverse'],'zero',out['legacy_slippage_intended_vs_fill']['frac_zero'],'window',out['legacy_slippage_intended_vs_fill']['window'])
