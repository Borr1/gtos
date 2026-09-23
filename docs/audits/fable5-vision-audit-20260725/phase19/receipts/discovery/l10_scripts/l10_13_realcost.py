import json
from collections import defaultdict, Counter
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
API='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
deals={}; bypos=defaultdict(list)
for a in ['ftmo','redacted_account']:
    for l in open(f'{API}/{a}_history_deals_get.jsonl'):
        d=json.loads(l); d['_acct']=a
        deals[d['ticket']]=d
        if d['type'] in (0,1) and d['symbol']: bypos[(a,d['position_id'])].append(d)
rows=[json.loads(l) for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl')]
recs=[]
for r in rows:
    if r.get('stage')!='entry_fill_reconciled': continue
    oso=r.get('order_send_observation') or {}; req=oso.get('request') or {}
    dcr=r.get('deal_cost_reconciliation') or {}; pcm=r.get('pretrade_cost_model') or {}
    tc=pcm.get('tick_cost') or {}; sp=(pcm.get('symbol_spec') or {}).get('fields') or {}
    dtk=dcr.get('deal_ticket')
    if dtk not in deals: continue
    d0=deals[dtk]; acct=d0['_acct']; pos=d0['position_id']
    legs=bypos[(acct,pos)]
    ttv=sp.get('trade_tick_value'); tts=sp.get('trade_tick_size'); sld=pcm.get('sl_distance'); vol=req.get('volume')
    if not (ttv and tts and sld and vol): continue
    upu=ttv/tts; cash_risk=sld*upu*vol
    comm_all=sum(x['commission'] for x in legs); swap_all=sum(x['swap'] for x in legs)
    side='LONG' if req.get('type')==0 else 'SHORT'
    sign=1.0 if side=='LONG' else -1.0
    fill=dcr.get('broker_entry_price'); reqp=req.get('price')
    recs.append(dict(acct=acct,sym=req.get('symbol'),side=side,pos=pos,vol=vol,sld=sld,cash_risk=cash_risk,
        n_legs=len(legs), closed=any(x['entry']!=0 for x in legs),
        comm_usd=abs(comm_all), swap_usd=swap_all,
        comm_r=abs(comm_all)/cash_risk, swap_r=(-swap_all)/cash_risk,
        real_spread_r=tc.get('spread_r'), slip_r=((fill-reqp)*sign/sld) if (fill is not None and reqp is not None) else None,
        model_total_cost_r=pcm.get('total_cost_r'), model_spread_r=pcm.get('spread_r')))
def q(v,p):
    v=sorted(v); return v[int(round(p*(len(v)-1)))] if v else None
def S(v,r=6):
    v=[x for x in v if x is not None]
    if not v: return None
    return dict(n=len(v),mean=round(sum(v)/len(v),r),median=round(q(v,.5),r),p10=round(q(v,.1),r),p90=round(q(v,.9),r),min=round(min(v),r),max=round(max(v),r))
closed=[x for x in recs if x['closed']]
tot=[ (x['real_spread_r'] or 0)+x['comm_r']+x['swap_r']+(x['slip_r'] or 0) for x in closed]
out=dict(n_joined=len(recs), n_closed=len(closed),
  spread_r=S([x['real_spread_r'] for x in closed]),
  commission_r=S([x['comm_r'] for x in closed]),
  swap_r=S([x['swap_r'] for x in closed]),
  slippage_r=S([x['slip_r'] for x in closed]),
  TOTAL_REAL_COST_R=S(tot),
  model_total_cost_r=S([x['model_total_cost_r'] for x in closed]),
  frozen_research_model_reference=dict(cost_r=0.663161, spread_r=0.564213, commission_r=0.065220, slippage_r=0.02, swap_r=0.013720,
     source='swarm brief / w0_DATA_DICTIONARY D1, January CJ pool n=27658'),
  n_swap_nonzero=sum(1 for x in closed if abs(x['swap_r'])>1e-9),
  frac_swap_nonzero=round(sum(1 for x in closed if abs(x['swap_r'])>1e-9)/max(1,len(closed)),4),
  by_account={a:dict(n=sum(1 for x in closed if x['acct']==a),
      spread_r=S([x['real_spread_r'] for x in closed if x['acct']==a]),
      commission_r=S([x['comm_r'] for x in closed if x['acct']==a]),
      swap_r=S([x['swap_r'] for x in closed if x['acct']==a]),
      slippage_r=S([x['slip_r'] for x in closed if x['acct']==a]),
      total_r=S([ (x['real_spread_r'] or 0)+x['comm_r']+x['swap_r']+(x['slip_r'] or 0) for x in closed if x['acct']==a]))
      for a in ('ftmo','redacted_account')})
def cls(s):
    if s in ('BTCUSD','ETHUSD','AVAUSD','DASHUSD'): return 'crypto'
    if 'XAU' in s or 'XAG' in s: return 'metals'
    if any(k in s for k in ('GER','JP225','UK100','US30','US100','US500','SPX','NDX','NAS')): return 'index'
    return 'fx'
bc=defaultdict(list)
for x in closed: bc[cls(x['sym'])].append(x)
out['by_class']={c:dict(n=len(g),spread_r=S([x['real_spread_r'] for x in g]),commission_r=S([x['comm_r'] for x in g]),
                        swap_r=S([x['swap_r'] for x in g]),slippage_r=S([x['slip_r'] for x in g]),
                        total_r=S([(x['real_spread_r'] or 0)+x['comm_r']+x['swap_r']+(x['slip_r'] or 0) for x in g]))
                 for c,g in sorted(bc.items())}
json.dump(dict(summary=out,records=recs),open(OUTD+'/L10_REAL_COST_V1.json','w'),indent=0)
print('joined',out['n_joined'],'closed',out['n_closed'])
for k in ('spread_r','commission_r','swap_r','slippage_r','TOTAL_REAL_COST_R','model_total_cost_r'):
    print(' ',k,out[k])
print(' swap nonzero',out['n_swap_nonzero'],out['frac_swap_nonzero'])
for a,v in out['by_account'].items(): print(' ',a,'n',v['n'],'total',v['total_r'])
for c,v in out['by_class'].items(): print(' ',c,'n',v['n'],'spread',v['spread_r']['mean'],'comm',v['commission_r']['mean'],'swap',v['swap_r']['mean'],'slip',(v['slippage_r'] or {}).get('mean'),'TOTAL',v['total_r']['mean'])
