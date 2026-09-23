"""KB2 refinement: (a) ETH ac-threshold + scale-out exit sweep; (b) NY-JPY rescue attempts."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, '/Users/borr/Documents/gtos/repo/ai-trading-agent')
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import collections, statistics
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import kb2_new_breadth as kb2

def pstat(rs):
    if not rs: return (0, 0.0, 0.0)
    n=len(rs); return (n, round(sum(rs)/n,4), round(100*sum(1 for r in rs if r>0)/n,1))
def byyear(pairs):
    d=collections.defaultdict(list)
    for y,r in pairs: d[y].append(r)
    return {y:pstat(v) for y,v in sorted(d.items())}
def fy(d): return ' '.join(f"{y}:{ev:+.2f}(n{n})" for y,(n,ev,w) in d.items())

print("===== (a) ETH ac-threshold + exit sweep =====")
Te,Be=kb2.resample_eth_h4()
cost=w1.cost_for('ETHUSD'); atrs=[atr14(Be,i) for i in range(len(Be))]
sigs=kb2.crypto_breakout_signals(Be,20)
for ac_thr in (0.10,0.15,0.175,0.20):
    # target4 geometry
    t4=[]; sd_exit=[]
    for i,d in sigs:
        a=atrs[i]
        if a<=0: continue
        ac=cs.autocorr(Be,i,60)
        if ac is None or ac<ac_thr: continue
        sd=2.0*a; vr=cs.vol_ratio(atrs,i)
        t4.append((Te[i].year, kb2.wins(simulate(Be,i,d,stop_dist=sd,target_dist=4*sd,maxbars=80,cost=cost))))
        sd_exit.append((Te[i].year, cs.exit_state_d(Be,i,d,sd,vr,cost)['R']))
    f4=[r for y,r in t4 if y>=2025]; fd=[r for y,r in sd_exit if y>=2025]
    print(f" ac>={ac_thr}: T4 all{pstat([r for _,r in t4])} fwd{pstat(f4)} {fy(byyear(t4))}")
    print(f"           SD all{pstat([r for _,r in sd_exit])} fwd{pstat(fd)} {fy(byyear(sd_exit))}")

print("\n===== (b) NY-JPY rescue: impulse filter + trend gate + wider target =====")
JPY=['GBPJPY','USDJPY']
for sh in (15,):
    for label,kw in (('base',{}),('imp>=0.8',dict(imp_min=0.8)),('imp>=1.2',dict(imp_min=1.2)),
                     ('trend20',dict(trend_lb=20)),('imp1.0+trend20',dict(imp_min=1.0,trend_lb=20))):
        o=kb2.session_open_mom(JPY,sh,4,1.0,2.5,48,**kw)
        rs=[r for _,_,_,r in o]; pairs=[(y,r) for _,_,y,r in o]
        print(f" NY{sh} {label:>16}: {pstat(rs)} | {fy(byyear(pairs))}")
# also test London hour 8 to confirm R1 reproduces here (sanity that machinery is right)
print("\n sanity: London hour>=8 (should reproduce KB R1 ~+0.17R):")
o=kb2.session_open_mom(JPY,8,4,1.0,2.5,48)
print("  ",pstat([r for _,_,_,r in o]), fy(byyear([(y,r) for _,_,y,r in o])))
# London hour scan to find true London-open in this server tz
print("\n London hour scan (s1.0/t2.5):")
for sh in (6,7,8,9,10):
    o=kb2.session_open_mom(JPY,sh,4,1.0,2.5,48)
    print(f"   h>={sh}: {pstat([r for _,_,_,r in o])}")
