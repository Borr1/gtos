import pandas as pd, numpy as np
RES=pd.read_pickle('res.pkl')
RES['gross']=RES['R_barrier']  # terminal_net_r + deductible_cost_r
print("check: deductible == cost_r - spread_r ?  max|diff| =",
      float((RES.deductible_cost_r-(RES.cost_r-RES.spread_r)).abs().max()))
print("     : deductible == slip+swap+comm ?     max|diff| =",
      float((RES.deductible_cost_r-(RES.expected_slippage_r+RES.swap_cost_r+RES.commission_r)).abs().max()))
print()
print("=== TEST: is one spread embedded in gross?  target leg should book 2.0 (LIMIT) vs 2.0-spread (MARKET) ===")
for ot in ['LIMIT','MARKET']:
    for leg,barrier in [('TARGET',2.0),('STOP',-1.0),('TIME_STOP',None)]:
        d=RES[(RES.proposed_order_type==ot)&(RES.leg==leg)]
        if not len(d): continue
        dev=d.gross-barrier if barrier is not None else d.gross
        print(f"  {ot:6s} {leg:10s} n={len(d):6d} gross_mean={d.gross.mean():+.5f} "
              f"median={d.gross.median():+.5f} mean_spread_r={d.spread_r.mean():.5f} "
              + (f"mean(gross-barrier)={dev.mean():+.5f}  frac_exactly_at_barrier={float((dev.abs()<1e-9).mean()):.4f}" if barrier else ""))
print()
print("=== FAIR VALUE NULL:  E[terminal_net_r] = -E[cost_r] under a driftless martingale ===")
for lab,sub in [('ALL',RES),('MARKET',RES[RES.proposed_order_type=='MARKET']),('LIMIT',RES[RES.proposed_order_type=='LIMIT'])]:
    net=sub.R_engine.mean(); null=-sub.cost_r.mean(); gross=sub.gross.mean(); gnull=-sub.spread_r.mean()
    print(f"  {lab:7s} n={len(sub):7d}  realized_net={net:+.5f}  fair_null=-E[cost]={null:+.5f}  EDGE={net-null:+.5f}")
    print(f"          {'':7s}  realized_gross={gross:+.5f}  gross_null=-E[spread]={gnull:+.5f}  EDGE={gross-gnull:+.5f}")
