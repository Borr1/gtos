"""The bar-close spread premium ON THE SYMBOLS THE BOOK ACTUALLY TRADES TODAY.

Normalisation divides out the HOUR entirely (each broker hour's 60 minute-cells are scaled by
that hour's own mean), so a rollover/session premium -- an hour-level effect the estate's cost
model already sees -- cannot produce any of this. What survives is purely WITHIN-hour minute shape.
MT5 aligns H4/D1 to broker 00:00, so H4 closes at broker hours 00,04,08,12,16,20 and D1 at 00."""
import json, statistics
ARMED={'BTCUSD','CORN_c','COTTON_c','DASHUSD','EU50_cash','FRA40_cash','GER40','JP225','SPX500',
       'UK100','UKOIL_cash','US2000_cash','US30_cash','USOIL_cash','XAGAUD','XAGEUR','XAGUSD',
       'XAUAUD','XAUEUR','XAUUSD'}
H4_CLOSE=[0,4,8,12,16,20]
d=json.load(open('/tmp/x6/X6_SPREAD_2D_ftmo.json'))
def norm(name): return name.replace('FTMO_','')
S=[s for s in d['symbols'] if not s.get('error')]
res={}
for s in S:
    nm=norm(s['symbol'])
    cm=s['cell_median']
    per_hour={}
    for h in range(24):
        v=[cm.get(f"{h}|{mo}") for mo in range(60)]
        present=[x for x in v if x is not None]
        if len(present)<50 or v[0] is None: continue     # need the hour substantially covered
        m=sum(present)/len(present)
        if m<=0: continue
        interior=[v[mo]/m for mo in range(3,60) if v[mo] is not None]
        per_hour[h]={"min0":v[0]/m,"min5":(v[5]/m if v[5] is not None else None),
                     "interior":statistics.mean(interior)}
    if per_hour: res[nm]=per_hour

print(f"{'symbol':13s} {'armed':6s} {'all-hr :00 prem':>15s} {'H4-close-hr prem':>17s} {'5min saving':>12s} {'hrs':>4s}")
arm_all=[]; arm_h4=[]; arm_save=[]; oth_all=[]
for nm in sorted(res):
    ph=res[nm]
    pr=[ph[h]["min0"]/ph[h]["interior"] for h in ph]
    h4=[ph[h]["min0"]/ph[h]["interior"] for h in ph if h in H4_CLOSE]
    sv=[1-ph[h]["min5"]/ph[h]["min0"] for h in ph if ph[h]["min5"]]
    a = nm in ARMED
    (arm_all if a else oth_all).append(statistics.median(pr))
    if a:
        if h4: arm_h4.append(statistics.median(h4))
        if sv: arm_save.append(statistics.median(sv))
    print(f"{nm:13s} {'YES' if a else '-':6s} {100*(statistics.median(pr)-1):+14.2f}% "
          f"{(100*(statistics.median(h4)-1) if h4 else float('nan')):+16.2f}% "
          f"{(100*statistics.median(sv) if sv else float('nan')):+11.2f}% {len(ph):4d}")
print()
print(f"ARMED symbols (n={len(arm_all)}):")
print(f"  median :00 premium over the bar interior, hour effect removed : {100*(statistics.median(arm_all)-1):+.2f}%")
print(f"  median premium restricted to H4-CLOSE hours (0,4,8,12,16,20)  : {100*(statistics.median(arm_h4)-1):+.2f}%")
print(f"  median spread SAVED by entering at :05 instead of :00         : {100*statistics.median(arm_save):+.2f}%")
print(f"  armed symbols where :00 is the widest part of the bar         : {sum(1 for x in arm_all if x>1)}/{len(arm_all)}")
print(f"NON-armed symbols (n={len(oth_all)}): median :00 premium {100*(statistics.median(oth_all)-1):+.2f}%")
json.dump({"per_symbol":{k:{str(h):v for h,v in ph.items()} for k,ph in res.items()},
           "armed_median_premium":statistics.median(arm_all),
           "armed_h4_close_median_premium":statistics.median(arm_h4),
           "armed_median_5min_saving":statistics.median(arm_save),
           "armed_symbols":sorted(ARMED)},open('/tmp/x6/X6_ARMED_SPREAD.json','w'),indent=1)
