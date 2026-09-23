import json
from collections import Counter, defaultdict
BASE='/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api'
SL='/Users/borr/GTOSActive/vps-export-20260725/extracted/05_shadow_logs'
OUTD='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
REASON={0:'CLIENT',1:'MOBILE',2:'WEB',3:'EXPERT',4:'SL',5:'TP',6:'SO',7:'ROLLOVER',8:'VMARGIN',9:'SPLIT'}
out={}
for a in ['ftmo','redacted_account']:
    deals=[json.loads(l) for l in open(f'{BASE}/{a}_history_deals_get.jsonl')]
    tr=[d for d in deals if d['type'] in (0,1) and d['symbol']]
    o=dict(
      entry_reason=dict(Counter(REASON.get(d['reason']) for d in tr if d['entry']==0)),
      exit_reason=dict(Counter(REASON.get(d['reason']) for d in tr if d['entry']!=0)),
      n_entry=sum(1 for d in tr if d['entry']==0), n_exit=sum(1 for d in tr if d['entry']!=0))
    ex=[d for d in tr if d['entry']!=0]
    o['exit_share_broker_sl']=round(sum(1 for d in ex if d['reason']==4)/max(1,len(ex)),4)
    o['exit_share_broker_tp']=round(sum(1 for d in ex if d['reason']==5)/max(1,len(ex)),4)
    o['exit_share_book_expert']=round(sum(1 for d in ex if d['reason']==3)/max(1,len(ex)),4)
    o['exit_share_manual']=round(sum(1 for d in ex if d['reason'] in (0,1,2))/max(1,len(ex)),4)
    # partial closes: exit volume < entry volume for a position
    pos=defaultdict(lambda: dict(inv=0.0,outv=0.0,nout=0))
    for d in tr:
        p=pos[d['position_id']]
        if d['entry']==0: p['inv']+=d['volume']
        else: p['outv']+=d['volume']; p['nout']+=1
    closed=[p for p in pos.values() if p['nout']>0]
    o['n_positions']=len(pos)
    o['n_positions_multi_exit_deal']=sum(1 for p in closed if p['nout']>1)
    o['frac_multi_exit']=round(sum(1 for p in closed if p['nout']>1)/max(1,len(closed)),4)
    o['n_positions_partial_only']=sum(1 for p in closed if p['outv']<p['inv']-1e-9)
    out[a]=o
# result.price==0 check on ALL order_send results in lifecycle capture
rows=[json.loads(l) for l in open(f'{SL}/broker_order_lifecycle_capture_v4.jsonl')]
pr=[]
for r in rows:
    oso=r.get('order_send_observation') or {}
    res=oso.get('result') or {}
    if res.get('present'): pr.append(res.get('price'))
    rr=r.get('result')
    if isinstance(rr,dict) and 'price' in rr: pr.append(rr.get('price'))
out['order_send_result_price']=dict(n=len(pr), n_zero=sum(1 for x in pr if not x), n_nonzero=sum(1 for x in pr if x),
                                    frac_zero=round(sum(1 for x in pr if not x)/max(1,len(pr)),4))
rc=[]
for r in rows:
    oso=r.get('order_send_observation') or {}; res=oso.get('result') or {}
    if res.get('present'): rc.append(res.get('retcode'))
    rr=r.get('result')
    if isinstance(rr,dict) and 'retcode' in rr: rc.append(rr.get('retcode'))
out['all_retcodes']=dict(Counter(rc))
json.dump(out,open(OUTD+'/L10_EXIT_MECH_V1.json','w'),indent=1)
for a in ['ftmo','redacted_account']:
    o=out[a]; print('==',a,'entries',o['n_entry'],'exits',o['n_exit'],'positions',o['n_positions'])
    print('  entry_reason',o['entry_reason']); print('  exit_reason',o['exit_reason'])
    print('  broker_SL',o['exit_share_broker_sl'],'broker_TP',o['exit_share_broker_tp'],'book',o['exit_share_book_expert'],'manual',o['exit_share_manual'])
    print('  multi-exit positions',o['n_positions_multi_exit_deal'],'frac',o['frac_multi_exit'],'partial-only',o['n_positions_partial_only'])
print('RESULT.PRICE:',out['order_send_result_price'])
print('RETCODES:',out['all_retcodes'])
