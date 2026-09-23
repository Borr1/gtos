import gzip,json,collections,statistics,datetime as dt
T='/Users/borr/.claude/jobs/adb9e69b/tmp/'
d=json.load(gzip.open(T+'AA_ESTATE.json.gz','rt'))
tr=d['trades']
allt=[]
for s,rows in tr.items():
    for r in rows:
        r['_sleeve']=s; allt.append(r)

LIVE24=set("AUDJPY AUDUSD BTCUSD CHFJPY ETHUSD EURGBP EURJPY EURUSD GBPJPY GBPUSD GER40 JP225 NAS100 NZDUSD SPX500 UK100 UKOIL_cash US30_cash USDCAD USDCHF USDJPY USOIL_cash XAGUSD XAUUSD".split())
# canonical aliasing seen in estate
ALIAS={'GER40_cash':'GER40','JP225_cash':'JP225','US100_cash':'NAS100','US500_cash':'SPX500','US30_cash':'US30_cash'}
def canon(s): return ALIAS.get(s,s)

def stats(rows,label):
    if not rows: print(label,"EMPTY"); return
    r=[x['r_gross'] for x in rows]
    n=len(r); m=statistics.mean(r); sd=statistics.pstdev(r)
    wins=[x for x in r if x>0]
    print(f"{label:52} n={n:6d} mean_r_gross={m:+.4f} sd={sd:.4f} win%={100*len(wins)/n:5.1f} medR={statistics.median(r):+.3f}")
    return dict(n=n,mean=m,sd=sd,win=len(wins)/n)

recent=[x for x in allt if x['entry_utc'][:4] in ('2024','2025','2026')]
print("=== ALL SLEEVES, all symbols ===")
stats(allt,"whole estate 2000-2026")
stats(recent,"2024-2026")
live=[x for x in recent if canon(x['symbol_canonical']) in LIVE24]
print("2024-26 trades on live-24 surface:",len(live), "of", len(recent), f"= {100*len(live)/len(recent):.1f}%")
stats(live,"2024-2026 on live-24 surface")

# monthly rate
for lab,rows in (("all-symbols",recent),("live24",live)):
    mo=collections.Counter(x['entry_utc'][:7] for x in rows)
    full=[v for k,v in sorted(mo.items()) if k<'2026-07']
    print(f"{lab}: months={len(full)} mean trades/month={statistics.mean(full):.1f} median={statistics.median(full):.1f} max={max(full)} min={min(full)}")

# per-symbol stop distance (live surface, recent)
print()
print("=== per-symbol median sl_distance_price (2024-2026) ===")
bysym=collections.defaultdict(list)
for x in recent: bysym[canon(x['symbol_canonical'])].append(x)
out={}
for s,rows in sorted(bysym.items()):
    sd=[x['sl_distance_price'] for x in rows if x.get('sl_distance_price')]
    if not sd: continue
    out[s]=dict(n=len(rows),med_sl=statistics.median(sd),p10=statistics.quantiles(sd,n=10)[0] if len(sd)>9 else min(sd),
                p90=statistics.quantiles(sd,n=10)[8] if len(sd)>9 else max(sd), med_entry=statistics.median([x['entry_price'] for x in rows]),
                live=s in LIVE24)
    print(f"{s:12} live={out[s]['live']!s:5} n={len(rows):5d} med_sl={out[s]['med_sl']:12.5f} p10={out[s]['p10']:12.5f} p90={out[s]['p90']:12.5f} med_entry={out[s]['med_entry']:11.2f}")
json.dump(out,open(T+'f5/estate_sl_by_symbol.json','w'),indent=1)

# per-sleeve on live24
print()
print("=== per-sleeve (2024-2026, live-24 symbols only) ===")
bysl=collections.defaultdict(list)
for x in live: bysl[x['_sleeve']].append(x)
tot=0
for s,rows in sorted(bysl.items(), key=lambda kv:-len(kv[1])):
    r=[y['r_gross'] for y in rows]
    print(f"{s:40} n={len(rows):5d} mean_gross={statistics.mean(r):+.4f} sd={statistics.pstdev(r):.3f}")
    tot+=len(rows)
print("total",tot)
