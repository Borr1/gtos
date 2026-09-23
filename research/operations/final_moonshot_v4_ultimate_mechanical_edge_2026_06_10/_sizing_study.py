"""Growth-optimal sizing study (personal): how fast can the clean_3 book ACTUALLY pass
an 8% FTMO challenge if we stop minimizing size and use the real 5%-daily/10%-maxDD budget?
Reconstructs the deploy series exactly as INTEG_w5_clean3_deploy, then MC across sizing."""
import sys, collections, statistics, pickle, random
from pathlib import Path
HERE=Path("research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10").resolve()
sys.path.insert(0,str(HERE)); sys.path.insert(0,str(HERE.parents[2]))
import INTEG_portfolio_build_w2 as W2, INTEG_portfolio_build_w3 as W3
streams_w3=pickle.load(open(HERE/'INTEG_W3_streams_cache.pkl','rb'))
days_w3,M_w3=W3.W2.build_matrix(streams_w3)
book_sleeves=W3.SLEEVES
daily_sleeve={sl:{} for sl in book_sleeves}
for di,day in enumerate(days_w3):
    for si,sl in enumerate(book_sleeves): daily_sleeve[sl][day]=M_w3[di][si]
new_streams=pickle.load(open(HERE/'INTEG_W5_new_streams_cache.pkl','rb'))
CLEAN3={'sub_xvol_pullback':0.45,'vp_euidx_pocgrav':0.30,'sub_mid_dn_revert':0.20}
def cand_daily(rows):
    by=collections.defaultdict(list)
    for r in rows: by[r['date']].append(r['R'])
    return {d:sum(v)/len(v) for d,v in by.items()}
cand={nm:cand_daily(new_streams[nm]) for nm in CLEAN3}
nd={nm:{d:v*cf for d,v in cand[nm].items()} for nm,cf in CLEAN3.items()}
all_days=sorted(set(days_w3)|set().union(*[set(cand[n]) for n in CLEAN3]))
comb=[]
for day in all_days:
    comb.append(sum(daily_sleeve[sl].get(day,0.0) for sl in book_sleeves)+sum(nd[nm].get(day,0.0) for nm in CLEAN3))
comb_fwd=[v for v,d in zip(comb,all_days) if d.year>=2025]
print(f"series: {len(comb)} days (fwd {len(comb_fwd)}); daily_mean all {statistics.fmean(comb):+.4f} fwd {statistics.fmean(comb_fwd):+.4f} unit-R; worst {min(comb):+.2f}")

TARGET=0.08;DAILY=0.05;MAXDD=0.10;BLOCK=5;N=20000
def mc(series,risk):
    n=len(series);outs=collections.Counter();dp=[]
    for s in range(N):
        rng=random.Random(s*131+int(risk*1e5));eq=1.0;peak=1.0;res='timeout';dc=0
        for _ in range(800):
            st=rng.randrange(n)
            for k in range(BLOCK):
                r=series[(st+k)%n];d=r*risk;dc+=1
                if d<=-DAILY: res='fail_daily';break
                eq*=1+d;peak=max(peak,eq)
                if (peak-eq)/peak>=MAXDD: res='fail_maxdd';break
                if eq-1>=TARGET: res='pass';break
            if res!='timeout':break
        outs[res]+=1
        if res=='pass':dp.append(dc)
    md=int(statistics.median(dp)) if dp else None
    return outs['pass']/N,outs['fail_maxdd']/N,outs['fail_daily']/N,md
def run(series,label):
    dm=statistics.fmean(series)
    print(f"\n=== {label} (daily {dm:+.4f} unit-R) ===")
    print(f"{'risk':>6} {'P(pass)':>8} {'failMaxDD':>10} {'failDaily':>10} {'medDays':>8} {'~mo%':>7}")
    for risk in (0.005,0.0075,0.01,0.0125,0.015,0.02,0.025,0.03):
        p,fdd,fday,md=mc(series,risk)
        mo=dm*risk*21*100  # approx monthly % (21 trading days)
        print(f"{risk*100:>5.2f}% {p:>8.1%} {fdd:>10.1%} {fday:>10.1%} {str(md):>8} {mo:>6.2f}%")
run(comb_fwd,"FORWARD 2025-26 (recent regime)")
run(comb,"ALL-HISTORY 2015-26 (conservative blend)")
