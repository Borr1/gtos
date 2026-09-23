"""MULTI-SLEEVE BOOK — re-test the REJECTED asset classes through the CHALLENGE-PASS lens,
not the standalone-alpha lens. A weak, uncorrelated, FORWARD-positive sleeve still raises
P(pass 8%) and cuts max-DD blowups via diversification. Reuses the TRUSTED FVG engine
(gold_sleeve_strategy.fvg_signals) on every asset class. No lookahead (engine is leak-checked).
"""
import sys, statistics, collections, random, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC

# group symbols by asset class
byclass = collections.defaultdict(list)
for s in w1.SYMBOLS:
    c = AC.get(s)
    if c: byclass[c].append(s)

# per-class daily correlated-unit R stream (one unit per decision-day within class)
def class_stream(syms):
    trades = []
    for sym in syms:
        try:
            for (t, d, sd, td, i, B, cost) in g.fvg_signals(sym):
                trades.append((t.date(), simulate(B, i, d, stop_dist=sd, target_dist=td, cost=cost)))
        except Exception:
            continue
    byday = collections.defaultdict(list)
    for dt, r in trades: byday[dt].append(r)
    return {dt: sum(rs)/len(rs) for dt, rs in byday.items()}, trades

streams = {}; print(f"{'class':>8} {'n_trd':>6} {'EVfull':>8} {'EVfwd25+':>9} {'corr_gold':>10} {'win%':>6}")
for c in sorted(byclass):
    st, trades = class_stream(byclass[c])
    if not trades: continue
    streams[c] = st
    rs = [r for _, r in trades]
    fwd = [r for dt, r in trades if dt.year >= 2025]
    evf = statistics.fmean(rs); evfwd = statistics.fmean(fwd) if fwd else float('nan')
    win = sum(1 for r in rs if r > 0)/len(rs)
    print(f"{c:>8} {len(trades):>6} {evf:>+8.3f} {evfwd:>+9.3f} {'-':>10} {win:>6.0%}")

# correlation of each class daily stream vs metals (aligned on common dates)
metals = streams.get("metals", {})
print("\ncorrelation of each class's daily-R to GOLD/metals (shared dates):")
def corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 20: return None, len(keys)
    x = [a[k] for k in keys]; y = [b[k] for k in keys]
    mx, my = statistics.fmean(x), statistics.fmean(y)
    num = sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))
    dx = math.sqrt(sum((v-mx)**2 for v in x)); dy = math.sqrt(sum((v-my)**2 for v in y))
    return (num/(dx*dy) if dx*dy>0 else None), len(keys)
for c in sorted(streams):
    if c == "metals": continue
    r, n = corr(streams[c], metals)
    fwd_ev = statistics.fmean([v for dt, v in [(d, streams[c][d]) for d in streams[c]] if dt.year>=2025]) if any(d.year>=2025 for d in streams[c]) else float('nan')
    tag = "  <- DIVERSIFIER" if (r is not None and abs(r) < 0.25 and fwd_ev > 0) else ""
    print(f"  {c:>8}: corr {('%+.2f'%r) if r is not None else 'na':>6} (n={n}) fwd_EV {fwd_ev:+.3f}{tag}")

# ---- challenge-pass MC for a portfolio: bootstrap DATES (preserves cross-sleeve corr + clustering) ----
TARGET=0.08; MAXDD=0.10; DAILY=0.05; BLOCK=5; N=8000
def portfolio_dates(classes):
    alldates = sorted(set().union(*[set(streams[c]) for c in classes]))
    # per date: list of (class, unit_r)
    perdate = {dt: [(c, streams[c][dt]) for c in classes if dt in streams[c]] for dt in alldates}
    return alldates, perdate
def mc(classes, risk_per_sleeve):
    alldates, perdate = portfolio_dates(classes); n=len(alldates)
    outs=collections.Counter(); days_pass=[]
    for s in range(N):
        rng=random.Random(s*131+int(risk_per_sleeve*1e5)+len(classes)); eq=1.0;peak=1.0;res="timeout";dc=0
        for _ in range(1500):
            start=rng.randrange(n)
            for k in range(BLOCK):
                dt=alldates[(start+k)%n]; dc+=1
                day_pct=sum(ur*risk_per_sleeve for _,ur in perdate[dt])
                if day_pct<=-DAILY: res="fail_daily";break
                eq*=(1+day_pct);peak=max(peak,eq)
                if (peak-eq)/peak>=MAXDD: res="fail_maxdd";break
                if eq-1.0>=TARGET: res="pass";break
            if res!="timeout":break
        outs[res]+=1
        if res=="pass":days_pass.append(dc)
    md=int(statistics.median(days_pass)) if days_pass else None
    return outs['pass']/N, outs['fail_maxdd']/N, outs['fail_daily']/N, md

# build book: metals + every uncorrelated forward-positive class
book=["metals"]
for c in sorted(streams):
    if c=="metals": continue
    r,n=corr(streams[c],metals)
    fwd=[v for dt,v in streams[c].items() if dt.year>=2025]
    if r is not None and abs(r)<0.25 and fwd and statistics.fmean(fwd)>0:
        book.append(c)
print(f"\nBOOK (metals + uncorrelated forward-positive sleeves): {book}")
print(f"{'config':>34} {'risk/sleeve':>11} {'P(pass)':>9} {'fail_dd':>8} {'fail_day':>9} {'med_days':>9}")
for risk in (0.005,0.0075,0.01):
    p,fd,fday,md=mc(["metals"],risk)
    print(f"{'GOLD ONLY':>34} {risk*100:>10.2f}% {p:>9.1%} {fd:>8.1%} {fday:>9.1%} {str(md):>9}")
for risk in (0.005,0.0075,0.01):
    p,fd,fday,md=mc(book,risk)
    print(f"{('BOOK '+'+'.join(book)):>34} {risk*100:>10.2f}% {p:>9.1%} {fd:>8.1%} {fday:>9.1%} {str(md):>9}")
