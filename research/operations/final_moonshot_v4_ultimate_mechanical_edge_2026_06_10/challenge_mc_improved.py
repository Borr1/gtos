"""Challenge-pass MC on the IMPROVED core (persistence gate + scale-out exit) vs original.
Ties the compounding build back to the owner's primary goal: P(pass 8% before -5% daily / -10% max)."""
import sys, statistics, collections, random
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parents[2]))
from geometry_lib import simulate, atr14
import gold_sleeve_strategy as g, wave1_structure_setups_ict as w1
import compounding_sleeve as cs

def stream(improved):
    trades=[]
    for s in cs.METALS:
        T,B=w1.load(s)
        if len(B)<200: continue
        atrs=[atr14(B,k) for k in range(len(B))]
        for (t,d,sd,td,i,B2,c2) in g.fvg_signals(s):
            if improved:
                ac=cs.autocorr(B,i,60)
                if ac is None or ac<0.10: continue
                vr=cs.vol_ratio(atrs,i)
                r=cs.exit_state_d(B,i,d,sd,vr,c2)['R']
            else:
                r=cs.wins(simulate(B,i,d,stop_dist=sd,target_dist=2*sd,cost=c2))
            trades.append((t.date(),r))
    byday=collections.defaultdict(list)
    for dt,r in trades: byday[dt].append(r)
    return [sum(rs)/len(rs) for dt,rs in sorted(byday.items())]

TARGET=0.08;MAXDD=0.10;DAILY=0.05;BLOCK=5;N=15000
def mc(daily,risk):
    n=len(daily);outs=collections.Counter();dp=[]
    for s in range(N):
        rng=random.Random(s*101+int(risk*1e5));eq=1.0;peak=1.0;res='timeout';dc=0
        for _ in range(1500):
            st=rng.randrange(n)
            for k in range(BLOCK):
                r=daily[(st+k)%n];d=r*risk;dc+=1
                if d<=-DAILY: res='fail_daily';break
                eq*=1+d;peak=max(peak,eq)
                if (peak-eq)/peak>=MAXDD: res='fail_dd';break
                if eq-1>=TARGET: res='pass';break
            if res!='timeout':break
        outs[res]+=1
        if res=='pass':dp.append(dc)
    return outs['pass']/N,outs['fail_dd']/N,int(statistics.median(dp)) if dp else None

orig=stream(False); imp=stream(True)
print(f"original daily-stream: {len(orig)} days, mean {statistics.fmean(orig):+.3f} unit-R/day")
print(f"improved daily-stream: {len(imp)} days, mean {statistics.fmean(imp):+.3f} unit-R/day")
print(f"\n{'risk/unit':>10} {'ORIG P(pass)':>13} {'IMPROVED P(pass)':>17} {'imp fail_dd':>12} {'imp med_days':>12}")
for risk in (0.005,0.0075,0.01,0.015):
    po,_,_=mc(orig,risk); pi,fdi,mdi=mc(imp,risk)
    print(f"{risk*100:>9.2f}% {po:>13.1%} {pi:>17.1%} {fdi:>12.1%} {str(mdi):>12}")
