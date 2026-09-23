import sys, os, json
import numpy as np
REPO="/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG=REPO+"/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0,PBG); sys.path.insert(0,REPO); os.chdir(REPO)
import pbg_econ as E
cm=E.CostModel()
tk=json.load(open('/tmp/f1/taken_slim.json'))
rows=[]
for w,v in tk.items():
    for r in v:
        if r.get('stop_loss') is None: continue
        d=abs(r['entry_price']-r['stop_loss'])
        px,terms=cm.cost_px(r['symbol'],r['decision_time_utc'],r['entry_price'],r['direction']=='LONG',hold_min=120)
        rows.append(dict(w=w,sym=r['symbol'],arm=r['cost_r'],mine=px/d,
            arm_spread=r.get('spread_r'),arm_comm=r.get('commission_r'),arm_swap=r.get('swap_cost_r'),
            my_spread=terms['spread']/d,my_comm=terms['commission']/d,my_slip=terms['slippage']/d,my_swap=terms['swap']/d))
a=np.array([r['arm'] for r in rows]); m=np.array([r['mine'] for r in rows])
print('n',len(rows))
print('arm cost_r mean %.5f   h1 broker-true mean %.5f   ratio %.3f'%(a.mean(),m.mean(),m.mean()/a.mean()))
print('arm terms: spread %.5f comm %.5f swap %.5f  (sum %.5f)'%(
    np.mean([r['arm_spread'] or 0 for r in rows]),np.mean([r['arm_comm'] or 0 for r in rows]),
    np.mean([r['arm_swap'] or 0 for r in rows]),
    np.mean([(r['arm_spread'] or 0)+(r['arm_comm'] or 0)+(r['arm_swap'] or 0) for r in rows])))
print('h1  terms: spread %.5f comm %.5f slip %.5f swap %.5f'%(
    np.mean([r['my_spread'] for r in rows]),np.mean([r['my_comm'] for r in rows]),
    np.mean([r['my_slip'] for r in rows]),np.mean([r['my_swap'] for r in rows])))
print('median ratio %.3f'%np.median(m/a))
json.dump(rows,open('/tmp/f1/costcheck.json','w'))
