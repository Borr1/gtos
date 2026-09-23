"""KB2 re-validation: crypto momentum/persistence sleeve + ETHUSD as 3rd carrier.

Reproduces the EXACT locked rule from KB_crypto.md now that ETHUSD H4 is rebuilt via the
deep backfill (3774 bars 2024-09..2026-06, merged into w1.load's D2). The KB flagged ETH H4
as 'broken (134 bars)' and named adding ETH as the high-priority next step.

LOCKED RULE: 20-bar Donchian breakout (closed bars), gate ac60=cs.autocorr(B,i,60)>=0.15,
stop sd=2.0*ATR14, fixed target=4R (4*sd), maxbars default(80), cost=w1.cost_for, winsorize[-1.3,5].
TRAIN=year<=2024, FORWARD=2025 & 2026 separately + per-year + per-symbol.
"""
import sys
ROOT='/Users/borr/Documents/gtos/repo/ai-trading-agent'
sys.path.insert(0,ROOT); sys.path.insert(0,ROOT+'/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10')
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs

def wins(r): return max(-1.3, min(5.0, r))

def breakout_signals(sym, lb=20, ac_min=0.15, stop_a=2.0, tgt_R=4.0, maxbars=80):
    T,B=w1.load(sym)
    if len(B)<150: return []
    atrs=[atr14(B,i) for i in range(len(B))]
    cost=w1.cost_for(sym)
    out=[]
    for i in range(lb+60, len(B)):
        a=atrs[i]
        if a<=0: continue
        ph=max(B[k].h for k in range(i-lb,i)); pl=min(B[k].l for k in range(i-lb,i))
        d=0
        if B[i].c>ph: d=1
        elif B[i].c<pl: d=-1
        if d==0: continue
        ac=cs.autocorr(B,i,60)
        if ac is None or ac<ac_min: continue
        sd=stop_a*a
        r=simulate(B,i,d,stop_dist=sd,target_dist=tgt_R*sd,maxbars=maxbars,cost=cost)
        out.append((T[i].year, sym, d, wins(r)))
    return out

def agg(rs):
    if not rs: return (0,0.0,0.0)
    n=len(rs); m=sum(x[3] for x in rs)/n; w=100*sum(1 for x in rs if x[3]>0)/n
    return (n,round(m,4),round(w,1))

def report(rows,title):
    print(f"\n===== {title} =====")
    for y in sorted(set(r[0] for r in rows)):
        ry=[r for r in rows if r[0]==y]; tag='FWD' if y>=2025 else 'train'
        print(f"  {y}: {agg(ry)} {tag}")
    tr=[r for r in rows if r[0]<=2024]; fwd=[r for r in rows if r[0]>=2025]
    print("  TRAIN<=2024:",agg(tr),"| FWD2025:",agg([r for r in rows if r[0]==2025]),
          "| FWD2026:",agg([r for r in rows if r[0]==2026]),"| FWD25-26:",agg(fwd))

if __name__=='__main__':
    eth=breakout_signals('ETHUSD')
    report(eth, "ETHUSD locked crypto rule (lb20 ac>=0.15 sd2 tgt4)")
    btc=breakout_signals('BTCUSD'); dash=breakout_signals('DASHUSD')
    report(btc, "BTCUSD (reference)")
    report(dash, "DASHUSD (reference)")
    report(btc+dash, "BTC+DASH (KB baseline 2-carrier)")
    report(btc+dash+eth, "BTC+DASH+ETH (3-carrier, ETH added)")
    # ac threshold robustness for ETH
    print("\n----- ETH ac-gate robustness -----")
    for ac in [0.10,0.15,0.175,0.20]:
        e=breakout_signals('ETHUSD',ac_min=ac)
        tr=[r for r in e if r[0]<=2024]; fwd=[r for r in e if r[0]>=2025]
        print(f"  ac>={ac}: TRAIN {agg(tr)} FWD {agg(fwd)}")
