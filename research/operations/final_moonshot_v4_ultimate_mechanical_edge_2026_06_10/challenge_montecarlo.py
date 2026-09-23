"""CHALLENGE-PASS Monte Carlo — the RIGHT objective: P(pass an 8% FTMO challenge
before breaching 5% daily / 10% max DD), no time limit. Uses the real gold-sleeve
daily correlated-unit R stream. This answers 'can this WIN the challenges you have',
which long-run Sharpe/maxDD did NOT answer."""
import sys, random, collections, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate
import gold_sleeve_strategy as g

# build daily correlated-risk-unit R stream (one unit per metals-decision-day)
trades = []
for sym in g.METALS:
    for (t, d, sd, td, i, B, cost) in g.fvg_signals(sym):
        trades.append((t.date(), simulate(B, i, d, stop_dist=sd, target_dist=td, cost=cost)))
byday = collections.defaultdict(list)
for dt, r in trades: byday[dt].append(r)
daily_unit_R = [sum(rs)/len(rs) for dt, rs in sorted(byday.items())]  # 1 unit/day
print(f"trading days with signals: {len(daily_unit_R)} | mean unit-R/day {statistics.fmean(daily_unit_R):+.3f} | win-days {sum(1 for x in daily_unit_R if x>0)/len(daily_unit_R):.0%}")

TARGET=0.08; MAXDD=0.10; DAILY=0.05; N=20000; BLOCK=5
def run_challenge(risk_per_unit, seed):
    rng = random.Random(seed); eq=1.0; peak=1.0; n=len(daily_unit_R)
    for _ in range(2000):  # cap path length (days); no time limit but bound sim
        # block bootstrap to preserve vol clustering
        start = rng.randrange(n)
        for k in range(BLOCK):
            r = daily_unit_R[(start+k) % n]
            day_pct = r * risk_per_unit
            if day_pct <= -DAILY: return "fail_daily"
            eq *= (1+day_pct); peak=max(peak,eq)
            if (peak-eq)/peak >= MAXDD: return "fail_maxdd"
            if eq-1.0 >= TARGET: return "pass"
    return "timeout"

print(f"\nCHALLENGE-PASS MC (8% target, 5% daily, 10% max, no time limit, {N} paths/level):")
print(f"{'risk/unit':>10} {'P(pass)':>9} {'P(fail_dd)':>11} {'P(fail_daily)':>13} {'med_days_pass':>13}")
for risk in (0.005,0.0075,0.01,0.015,0.02,0.03,0.05):
    outs=collections.Counter(); days_pass=[]
    for s in range(N):
        # also track days-to-pass for passers
        rng=random.Random(s*97+int(risk*1e5)); eq=1.0;peak=1.0;dd=0;n=len(daily_unit_R);res="timeout";dcount=0
        for _ in range(2000):
            start=rng.randrange(n)
            for k in range(BLOCK):
                dcount+=1; r=daily_unit_R[(start+k)%n]; dp=r*risk
                if dp<=-DAILY: res="fail_daily";break
                eq*=(1+dp);peak=max(peak,eq)
                if (peak-eq)/peak>=MAXDD: res="fail_maxdd";break
                if eq-1.0>=TARGET: res="pass";break
            if res!="timeout": break
        outs[res]+=1
        if res=="pass": days_pass.append(dcount)
    md = int(statistics.median(days_pass)) if days_pass else None
    print(f"{risk*100:>9.2f}% {outs['pass']/N:>9.1%} {outs['fail_maxdd']/N:>11.1%} {outs['fail_daily']/N:>13.1%} {str(md):>13}")
