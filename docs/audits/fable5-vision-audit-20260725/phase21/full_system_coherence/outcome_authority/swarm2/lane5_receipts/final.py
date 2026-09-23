import gzip, pickle, json, math, collections, statistics
rows=[]
for m in ("feb","apr","may","jun","jul"):
    rows+=pickle.load(gzip.open(f"/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz","rb"))
def num(x):
    try:
        v=float(x); return v if v==v else None
    except: return None
# A) LIMIT vs MARKET economics
agg=collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    ot=r.get("proposed_order_type")
    for k in ("cost_r","spread_r","commission_r","expected_slippage_r","swap_cost_r","terminal_net_r","risk_fraction_of_entry","distance_to_limit_atr"):
        v=num(r.get(k))
        if v is not None: agg[ot][k].append(v)
print("A) order-type economics")
print(f"{'field':22s} {'MARKET n':>9s} {'MARKET mean':>12s} {'LIMIT n':>9s} {'LIMIT mean':>12s}")
A={}
for k in ("cost_r","spread_r","commission_r","expected_slippage_r","swap_cost_r","terminal_net_r","risk_fraction_of_entry"):
    mm=agg["MARKET"][k]; ll=agg["LIMIT"][k]
    a=sum(mm)/len(mm) if mm else float('nan'); b=sum(ll)/len(ll) if ll else float('nan')
    A[k]={"MARKET":[len(mm),a],"LIMIT":[len(ll),b]}
    print(f"{k:22s} {len(mm):9d} {a:+12.5f} {len(ll):9d} {b:+12.5f}")
# resolved-only net
for ot in ("MARKET","LIMIT"):
    v=agg[ot]["terminal_net_r"]
    if v:
        n=len(v); m=sum(v)/n; sd=statistics.pstdev(v)
        print(f"   {ot} resolved net_r n={n} mean={m:+.5f} se={sd/math.sqrt(n):.5f} t={m/(sd/math.sqrt(n)):+.2f}")
        A.setdefault("net_t",{})[ot]=[n,m,sd/math.sqrt(n),m/(sd/math.sqrt(n))]
# B) foregone carry in R units for positive-carry sides
SW={  # FTMO swap points, (long, short), point
 "AUDJPY":(2.0,-15.9,0.001),"CADJPY":(0.15,-9.2,0.001),"CHFJPY":(-10.4,0.6,0.001),
 "EURGBP":(-8.39,0.13,1e-5),"EURJPY":(0.89,-11.44,0.001),"EURUSD":(-10.48,0.27,1e-5),
 "GBPJPY":(2.8,-27.88,0.001),"NZDJPY":(0.13,-7.87,0.001),"NZDUSD":(-5.65,0.08,1e-5),
 "UK100":(-233.92,10.8,0.01),"UKOIL_cash":(27.64,-129.84,0.001),"US30_cash":(37.0,-1099.03,0.01),
 "USDCAD":(0.47,-12.75,1e-5),"USDCHF":(1.15,-13.81,1e-5),"USDJPY":(1.93,-20.36,0.001),
 "USOIL_cash":(36.56,-168.09,0.001),"XAGAUD":(-15.15,3.23,0.001),"XAGEUR":(-4.97,0.6,0.001),
 "XAGUSD":(-17.36,0.69,0.001),"CORN_c":(-21.15,3.87,0.01),"COTTON_c":(-4.04,0.75,0.01)}
PX={"AUDJPY":97.0,"CADJPY":110.0,"CHFJPY":175.0,"EURGBP":0.855,"EURJPY":178.0,"EURUSD":1.15,
    "GBPJPY":208.0,"NZDJPY":88.0,"NZDUSD":0.575,"UK100":9600.0,"UKOIL_cash":76.5,"US30_cash":44000.0,
    "USDCAD":1.36,"USDCHF":0.80,"USDJPY":155.0,"USOIL_cash":76.0,"XAGAUD":58.0,"XAGEUR":34.0,
    "XAGUSD":38.0,"CORN_c":430.0,"COTTON_c":68.0}
rfe=collections.defaultdict(list)
for r in rows:
    v=num(r.get("risk_fraction_of_entry"))
    if v and v>0: rfe[r.get("symbol")].append(v)
print("\nB) foregone positive carry, expressed in R/night (credit the estate floors to zero)")
print(f"{'symbol':13s} {'side':6s} {'swap_pts':>9s} {'carry/night':>12s} {'ann%':>7s} {'med risk_frac':>13s} {'CARRY R/night':>14s} {'vs mean cost_r 0.2386':>22s}")
B=[]
for sym,(sl,ss,pt) in sorted(SW.items()):
    px=PX[sym]; rr=rfe.get(sym)
    if not rr: continue
    med=statistics.median(rr)
    for side,pts in (("LONG",sl),("SHORT",ss)):
        if pts<=0: continue
        cn=pts*pt/px
        rn=cn/med
        B.append({"symbol":sym,"side":side,"swap_points":pts,"carry_frac_per_night":cn,
                  "carry_ann_pct":cn*365*100,"median_risk_fraction_of_entry":med,"carry_R_per_night":rn,
                  "pct_of_mean_cost_r":100*rn/0.23855,"n_candidates":len(rr)})
        print(f"{sym:13s} {side:6s} {pts:9.2f} {cn:12.3e} {cn*365*100:6.2f}% {med:13.5f} {rn:+14.5f} {100*rn/0.23855:21.1f}%")
json.dump({"order_type_economics":A,"foregone_carry":B}, open("final_stats.json","w"), indent=1)
