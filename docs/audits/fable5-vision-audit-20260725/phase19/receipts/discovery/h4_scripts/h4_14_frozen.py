"""h4: frozen model vs broker-true vs LIVE, per instrument, in bps."""
import sys, json, statistics as st
D='/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery'
sys.path.insert(0,D)
import w0_ws
DEC=json.load(open(D+'/h4_TOLL_DECOMP_V1.json'))
CT={r['symbol']:r for r in json.load(open(D+'/h4_CORRECTED_TOLL_V1.json'))['per_symbol']}
rows=w0_ws.load()
out={}
for sym in sorted(DEC):
    g=[r for r in rows if r['symbol']==sym]
    rd=[r['risk_distance']/r['entry_price']*1e4 for r in g]
    fz=[ (r['expected_cost_r'] or 0)*b for r,b in zip(g,rd)]
    fs=[ (r['spread_r'] or 0)*b for r,b in zip(g,rd)]
    fc=[ (r['commission_r'] or 0)*b for r,b in zip(g,rd)]
    fw=[ (r['swap_cost_r'] or 0)*b for r,b in zip(g,rd)]
    fsl=[ (r['expected_slippage_r'] or 0)*b for r,b in zip(g,rd)]
    bt=DEC[sym]['toll_bps_recon']; lv=CT[sym]['toll_corrected_bps']
    out[sym]=dict(n=len(g), frozen_total_bps=round(st.mean(fz),4), frozen_spread_bps=round(st.mean(fs),4),
      frozen_comm_bps=round(st.mean(fc),4), frozen_swap_bps=round(st.mean(fw),4), frozen_slip_bps=round(st.mean(fsl),4),
      broker_true_bps=bt, live_grounded_bps=lv,
      frozen_over_live=round(st.mean(fz)/lv,3), brokertrue_over_live=round(bt/lv,3))
print('{:12s} {:>6s} {:>10s} {:>11s} {:>11s} {:>9s} {:>9s}'.format('sym','n','frozen','brokerTrue','liveGround','froz/live','bt/live'))
for s in sorted(out,key=lambda s:-out[s]['frozen_over_live']):
    v=out[s]
    print('{:12s} {:6d} {:10.4f} {:11.4f} {:11.4f} {:9.3f} {:9.3f}'.format(
      s,v['n'],v['frozen_total_bps'],v['broker_true_bps'],v['live_grounded_bps'],v['frozen_over_live'],v['brokertrue_over_live']))
N=sum(v['n'] for v in out.values())
for k in ('frozen_total_bps','broker_true_bps','live_grounded_bps'):
    print('  pool-weighted %-20s %.4f bps'%(k,sum(v[k]*v['n'] for v in out.values())/N))
import numpy as np
fr=[out[s]['frozen_total_bps'] for s in out]; lv=[out[s]['live_grounded_bps'] for s in out]; bt=[out[s]['broker_true_bps'] for s in out]
def spear(a,b):
    ra={v:i for i,v in enumerate(sorted(a))}; rb={v:i for i,v in enumerate(sorted(b))}
    A=[ra[x] for x in a]; B=[rb[x] for x in b]
    ma,mb=st.mean(A),st.mean(B)
    num=sum((x-ma)*(y-mb) for x,y in zip(A,B))
    return num/((sum((x-ma)**2 for x in A)*sum((y-mb)**2 for y in B))**.5)
print('  Spearman(frozen, live-grounded)      = %.4f'%spear(fr,lv))
print('  Spearman(broker-true, live-grounded) = %.4f'%spear(bt,lv))
json.dump(out, open(D+'/h4_FROZEN_VS_LIVE_V1.json','w'), indent=1)
