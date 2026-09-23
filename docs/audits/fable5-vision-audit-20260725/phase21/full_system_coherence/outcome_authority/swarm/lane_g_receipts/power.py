"""Claim 4: is the selected book distinguishable from zero at these trade counts?"""
import json, math
import numpy as np
from scipy import stats
P={"feb":"/private/tmp/w21-market-top-feb-r2/FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json",
   "aprmay":"/private/tmp/w21-market-top-aprmay-r3/APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json",
   "junjul":"/private/tmp/w21-market-top-junjul-r4/JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json"}
M={"2026-02":"feb","2026-04":"apr","2026-05":"may","2026-06":"jun","2026-07":"jul"}
trades={k:[] for k in ("feb","apr","may","jun","jul")}
for tag,p in P.items():
    d=json.load(open(p))
    for c in d["selected_candidates"]:
        v=c.get("actual_net_r")
        if v is None: continue
        mo=M[c["trading_day"][:7]]
        trades[mo].append(float(v))
print(f"{'month':6s} {'n':>4s} {'sum R':>9s} {'mean':>8s} {'sd':>7s} {'se':>7s} {'t':>6s} {'p':>8s}   95% CI on the TOTAL")
rows={}
allr=[]
for mo in ("feb","apr","may","jun","jul"):
    x=np.array(trades[mo]); allr+=list(x)
    n=len(x); s=x.sum(); mu=x.mean(); sd=x.std(ddof=1); se=sd/math.sqrt(n)
    t=mu/se; p=2*(1-stats.t.cdf(abs(t),n-1))
    crit=stats.t.ppf(0.975,n-1)
    lo,hi=(mu-crit*se)*n,(mu+crit*se)*n
    rows[mo]=dict(n=n,total=s,mean=mu,sd=sd,se=se,t=t,p=p,ci_total=[lo,hi])
    print(f"{mo:6s} {n:4d} {s:+9.3f} {mu:+8.4f} {sd:7.4f} {se:7.4f} {t:+6.2f} {p:8.4f}   [{lo:+8.2f}, {hi:+8.2f}]")
x=np.array(allr); n=len(x); mu=x.mean(); sd=x.std(ddof=1); se=sd/math.sqrt(n)
t=mu/se; p=2*(1-stats.t.cdf(abs(t),n-1)); crit=stats.t.ppf(0.975,n-1)
print(f"{'ALL5':6s} {n:4d} {x.sum():+9.3f} {mu:+8.4f} {sd:7.4f} {se:7.4f} {t:+6.2f} {p:8.4f}   "
      f"[{(mu-crit*se)*n:+8.2f}, {(mu+crit*se)*n:+8.2f}]")
rows["_ALL5"]=dict(n=n,total=float(x.sum()),mean=float(mu),sd=float(sd),se=float(se),t=float(t),p=float(p),
                   ci_total=[float((mu-crit*se)*n),float((mu+crit*se)*n)])

# June+July combined, both the actual and the worst-case convention
jj=np.array(trades["jun"]+trades["jul"]); n=len(jj); mu=jj.mean(); sd=jj.std(ddof=1); se=sd/math.sqrt(n)
crit=stats.t.ppf(0.975,n-1)
print(f"\nJUN+JUL together: n={n} total {jj.sum():+.3f} mean {mu:+.4f} se {se:.4f} "
      f"t {mu/se:+.2f} p {2*(1-stats.t.cdf(abs(mu/se),n-1)):.4f}  95% CI total [{(mu-crit*se)*n:+.2f},{(mu+crit*se)*n:+.2f}]")
rows["_JUNJUL"]=dict(n=n,total=float(jj.sum()),mean=float(mu),se=float(se),t=float(mu/se),
                     ci_total=[float((mu-crit*se)*n),float((mu+crit*se)*n)])

# ---- power: trades needed -------------------------------------------------
sd_pool=float(np.std(x,ddof=1))
print(f"\nPer-trade sd of the selected book (all five months) = {sd_pool:.4f} R")
print("\nTrades needed for 80% power at alpha=0.05 (two-sided), by true edge size:")
za,zb=stats.norm.ppf(0.975),stats.norm.ppf(0.80)
tr_per_month=n/5
print(f"{'edge R/trade':>12s} {'n trades':>9s} {'months @'+f'{tr_per_month:.0f}/mo':>14s} {'R/month':>9s}")
need={}
for edge in (0.30,0.20,0.15,0.10,0.075,0.05,0.03):
    nn=((za+zb)*sd_pool/edge)**2
    need[edge]=nn
    print(f"{edge:12.3f} {nn:9.0f} {nn/tr_per_month:14.1f} {edge*tr_per_month:9.2f}")
# what edge is detectable with what we have?
det=(za+zb)*sd_pool/math.sqrt(n)
print(f"\nWith the {n} trades actually taken, the minimum detectable edge at 80% power is "
      f"{det:+.4f} R/trade  (= {det*n:+.1f} R over the five months).")
print(f"The observed five-month result is {x.mean():+.4f} R/trade ({x.sum():+.2f} R) --- "
      f"{'INSIDE' if abs(x.mean())<det else 'OUTSIDE'} that band.")
json.dump({"per_month":rows,"sd_per_trade":sd_pool,"min_detectable_edge_80pct":det,
           "trades_needed_80pct":{str(k):v for k,v in need.items()}},
          open("/tmp/laneG/power.json","w"),indent=1)
