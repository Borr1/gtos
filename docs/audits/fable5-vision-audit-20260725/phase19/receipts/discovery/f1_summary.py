import json,glob,os
import numpy as np
W=sorted(glob.glob('/tmp/f1/out/W_*.json'))
D={os.path.basename(f)[2:-5]:json.load(open(f)) for f in W}
def row(w,e,label):
    if not e: return None
    return (w,label,e['n'],e['gross_mean'],e['cost_mean'],e['net_mean'],e['gross_win_rate'],
            e['gross_payoff'],e['gross_breakeven_wr'],e['gross_gap'],e.get('fill_rate'),
            e.get('d_bps_median'),e.get('born_past_stop_share'),e.get('days_net_positive'),e.get('days'))
def show(keys,title):
    print('\n'+'='*140); print(title); print('='*140)
    h=f"{'win':8s} {'pop':26s} {'n':>7s} {'gross':>9s} {'cost':>8s} {'net':>9s} {'wr':>7s} {'payoff':>7s} {'be_wr':>7s} {'gap':>8s} {'fill':>6s} {'dbps':>7s} {'past':>6s} {'days+':>7s}"
    print(h); print('-'*len(h))
    for w in sorted(D):
        for k,lab in keys:
            e=D[w].get(k)
            if not e: continue
            f=lambda x,fmt: (fmt%x) if x is not None else '   -  '
            print(f"{w:8s} {lab:26s} {e['n']:7d} {e['gross_mean']:+9.5f} {e['cost_mean']:8.5f} {e['net_mean']:+9.5f} {e['gross_win_rate']:7.4f} {f(e['gross_payoff'],'%7.4f')} {f(e['gross_breakeven_wr'],'%7.4f')} {f(e['gross_gap'],'%+8.4f')} {f(e.get('fill_rate'),'%6.3f')} {f(e.get('d_bps_median'),'%7.2f')} {f(e.get('born_past_stop_share'),'%6.3f')} {e.get('days_net_positive')}/{e.get('days')}")
show([('roster_honest_t2.0','ROSTER honest t2.0'),('pool_honest_t2.0','POOL honest t2.0'),
      ('taken_honest_t2.0','TAKEN honest t2.0'),('taken_realised','TAKEN realised(arm)')],
     'CONTRACT C1 (honest resting-limit fill, 120 M1 bars, target 2.0R = policy target)')
show([('roster_market_t2.0','ROSTER market t2.0'),('pool_market_t2.0','POOL market t2.0'),
      ('taken_market_t2.0','TAKEN market t2.0')],
     'CONTRACT C0 (market fill at decision instant, target 2.0R) -- reproduces sealed plain_walk_r')
show([('roster_honest_t1.5','ROSTER honest t1.5'),('pool_honest_t1.5','POOL honest t1.5'),
      ('taken_honest_t1.5','TAKEN honest t1.5')],
     'CONTRACT C1 at min_rr = 1.5 (the generator target)')
