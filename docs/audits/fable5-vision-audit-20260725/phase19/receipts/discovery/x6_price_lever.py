"""PRICE the spread component of the wave's 5-minute-delay lever, per candidate.

MECHANISM measurement, NOT a January score. The tick corpus is 2026-06-18..07-24, outside the
January window, so what is transferred is the SHAPE of within-hour spread (a microstructure
property of the symbol + broker), applied to January's own spread_r. Labelled accordingly.

Per symbol and per boundary minute (:00 hour close vs :15/:30/:45 M15-only close) the saving is
   saving_frac = 1 - spread(boundary + 5 min) / spread(boundary)
measured with the HOUR EFFECT DIVIDED OUT (each broker hour's 60 minute cells normalised by that
hour's own mean), so a rollover/session premium cannot contribute.
Candidate value = spread_r * saving_frac, in R.
"""
import json, statistics, sys, collections
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws

CANON2TICK = {"XAUUSD":"XAUUSD","UK100":"UK100_cash","SPX500":"US500_cash","NAS100":"US100_cash",
 "US30_cash":"US30_cash","GBPUSD":"GBPUSD","GER40":"GER40_cash","JP225":"JP225_cash",
 "USDCAD":"USDCAD","BTCUSD":"BTCUSD","EURJPY":"EURJPY","ETHUSD":"ETHUSD","XAGUSD":"XAGUSD",
 "USDCHF":"USDCHF","USDJPY":"USDJPY","EURGBP":"EURGBP","NZDUSD":"NZDUSD","EURUSD":"EURUSD",
 "UKOIL_cash":"UKOIL_cash","GBPJPY":"GBPJPY","AUDJPY":"AUDJPY","USOIL_cash":"USOIL_cash",
 "AUDUSD":"AUDUSD","CHFJPY":"CHFJPY"}

d=json.load(open('/tmp/x6/X6_SPREAD_2D_ftmo.json'))
cells={s['symbol'].replace('FTMO_',''):s['cell_median'] for s in d['symbols'] if not s.get('error')}

# per (symbol, boundary_minute) -> saving fraction and premium, hour-normalised, median over hours
tab={}
for sym,cm in cells.items():
    per={}
    for bm in (0,15,30,45):
        sav=[];prem=[]
        for h in range(24):
            v=[cm.get(f"{h}|{mo}") for mo in range(60)]
            present=[x for x in v if x is not None]
            if len(present)<50: continue
            m=sum(present)/len(present)
            if m<=0: continue
            b=v[bm]; p5=v[(bm+5)%60]
            interior=[v[mo]/m for mo in range(60) if v[mo] is not None and mo%15>=3]
            if b is None or not interior: continue
            prem.append((b/m)/statistics.mean(interior))
            if p5 is not None and b>0: sav.append(1-p5/b)
        if prem: per[bm]={"premium":statistics.median(prem),
                          "saving_frac":statistics.median(sav) if sav else 0.0,"n_hours":len(prem)}
    tab[sym]=per

rows=w0_ws.load()
tot=0;matched=0;val=[];by_sym=collections.defaultdict(list);by_bm=collections.defaultdict(list)
missing=collections.Counter(); nospread=0
for r in rows:
    tot+=1
    sym=r.get("symbol"); ts=r.get("decision_time_utc") or ""
    tk=CANON2TICK.get(sym)
    if not tk or tk not in tab: missing[sym]+=1; continue
    try: mo=int(ts[14:16])
    except Exception: continue
    bm = mo - (mo%15)          # 0,15,30,45
    e=tab[tk].get(bm)
    if not e: continue
    sr=r.get("spread_r")
    if sr is None: nospread+=1; continue
    try: sr=float(sr)
    except (TypeError,ValueError): nospread+=1; continue
    v=sr*e["saving_frac"]
    matched+=1; val.append(v); by_sym[sym].append(v); by_bm[bm].append(v)

print(f"pool rows {tot}  priced {matched}  unmapped {sum(missing.values())}  no spread_r {nospread}")
print(f"spread_r in pool: mean {statistics.mean(float(r['spread_r']) for r in rows if r.get('spread_r') is not None):.6f}")
print()
print(f"=== SPREAD SAVING FROM A 5-MINUTE DELAY (mechanism-transferred), R per trade ===")
print(f"  mean   {statistics.mean(val):+.6f} R/trade")
print(f"  median {statistics.median(val):+.6f} R/trade")
print(f"  total over the priced pool: {sum(val):+.2f} R")
print()
print("  by boundary minute:")
for bm in (0,15,30,45):
    v=by_bm[bm]
    print(f"    :{bm:02d}  n={len(v):6d}  mean {statistics.mean(v):+.6f} R   ({'HOUR close' if bm==0 else 'M15 close only'})")
print()
print("  top 10 symbols by mean saving:")
for s,v in sorted(by_sym.items(),key=lambda kv:-statistics.mean(kv[1]))[:10]:
    print(f"    {s:12s} n={len(v):5d}  mean {statistics.mean(v):+.6f} R  total {sum(v):+7.2f} R")
print()
print("  symbols with ZERO measured saving:")
print("   ", ", ".join(sorted(s for s,v in by_sym.items() if abs(statistics.mean(v))<1e-9)))
json.dump({"note":"MECHANISM transfer: tick corpus 2026-06-18..07-24, applied to January spread_r. NOT a January score.",
  "per_symbol_boundary_table":tab,"n_priced":matched,"mean_r_per_trade":statistics.mean(val),
  "median_r_per_trade":statistics.median(val),"total_r":sum(val),
  "by_boundary_minute":{str(k):{"n":len(v),"mean_r":statistics.mean(v)} for k,v in by_bm.items()},
  "by_symbol":{k:{"n":len(v),"mean_r":statistics.mean(v),"total_r":sum(v)} for k,v in by_sym.items()}},
  open('/tmp/x6/X6_LEVER_PRICE.json','w'),indent=1)

# --- refinement: restrict to candidates the LIVE gate could actually take -------------
# book_owner._spread_cost_screen refuses spread_r > selected_cell_pretrade_max_spread_r (0.10)
GATE=0.10
ex=[];exn=0
bysym2=collections.defaultdict(list)
for r in rows:
    sym=r.get("symbol"); ts=r.get("decision_time_utc") or ""
    tk=CANON2TICK.get(sym); sr=r.get("spread_r")
    if not tk or tk not in tab or sr is None: continue
    sr=float(sr)
    if sr>GATE: continue
    mo=int(ts[14:16]); bm=mo-(mo%15)
    e=tab[tk].get(bm)
    if not e: continue
    exn+=1; v=sr*e["saving_frac"]; ex.append(v); bysym2[sym].append(v)
print()
print(f"=== restricted to EXECUTABLE candidates (spread_r <= {GATE}, the live pretrade gate) ===")
print(f"  n = {exn} of {len(rows)}  ({100*exn/len(rows):.1f}% of the pool)")
print(f"  mean spread saving from a 5-min delay: {statistics.mean(ex):+.6f} R/trade")
print(f"  total: {sum(ex):+.2f} R")
for s,v in sorted(bysym2.items(),key=lambda kv:-statistics.mean(kv[1]))[:6]:
    print(f"    {s:12s} n={len(v):5d} mean {statistics.mean(v):+.6f} R")
