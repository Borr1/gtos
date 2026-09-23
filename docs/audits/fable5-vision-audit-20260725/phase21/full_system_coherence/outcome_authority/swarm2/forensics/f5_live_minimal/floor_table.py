"""F5: true minimum placeable position per symbol per broker, and the
fraction of the full 32-sleeve system's trades that survive a fixed-$ risk floor.

Sources (all repo-committed, no broker contacted):
  P1_INERT_PROFILE_SYMBOL_SNAPSHOT.json  (phase20/receipts/science) -> FTMO live spec
  BROKER_SYMBOL_SPEC_COMPARISON.json     (research/operations/vps_broker_truth_2026_07_26) -> FN deltas
  AA_ESTATE_TRADES.json.gz               (phase6/receipts) -> 22,324 trades, per-trade sl_distance_price
  L10_SLIP_RECORDS_V1.json               (phase19/receipts/discovery) -> 140 LIVE fills, cross-check
"""
import gzip,json,collections,statistics,math
T='/Users/borr/.claude/jobs/adb9e69b/tmp/'

p1=json.load(open(T+'P1_SPECS.json'))['profiles']
cmpd=json.load(open(T+'BROKER_SPEC.json'))
ftmo={}
for canon,s in p1['operator_profile']['symbols'].items():
    ftmo[canon]=dict(mt5=s['mt5_symbol'],ts=s['trade_tick_size'],tv=s['trade_tick_value'],
                     cs=s['trade_contract_size'],vmin=s['volume_min'],vstep=s['volume_step'],vmax=s['volume_max'])
# FN starts as a copy of FTMO geometry, then the MEASURED differing fields are applied.
fn={k:dict(v) for k,v in ftmo.items()}
for canon,s in p1['redacted_account']['symbols'].items():
    fn[canon]['mt5']=s['mt5_symbol']; fn[canon]['vmin']=s['volume_min']; fn[canon]['vstep']=s['volume_step']
    if s.get('volume_max') is not None: fn[canon]['vmax']=s['volume_max']
byftmo={v['mt5']:k for k,v in ftmo.items()}
applied=[]
for e in cmpd['comparison']:
    fs=e.get('ftmo_symbol'); canon=byftmo.get(fs)
    if canon is None: continue
    df=e.get('differing_fields') or {}
    for f,key in (('trade_tick_size','ts'),('trade_tick_value','tv'),('trade_contract_size','cs'),('volume_max','vmax'),('volume_min','vmin'),('volume_step','vstep')):
        if f in df:
            fn[canon][key]=df[f]['redacted_account']; applied.append((canon,f,df[f]['ftmo'],df[f]['redacted_account']))
print("FN deltas applied:",len(applied))
for a in applied:
    if a[1] in ('trade_tick_value','trade_tick_size','trade_contract_size'): print("   ",a)

def risk_per_lot(spec,sl):
    return (sl/spec['ts'])*spec['tv']

# ---- estate per-trade -------------------------------------------------------
d=json.load(gzip.open(T+'AA_ESTATE.json.gz','rt'))
ALIAS={'GER40_cash':'GER40','JP225_cash':'JP225','US100_cash':'NAS100','US500_cash':'SPX500'}
rows=[]
for s,rs in d['trades'].items():
    for r in rs:
        if r['entry_utc'][:4] not in ('2024','2025','2026'): continue
        c=ALIAS.get(r['symbol_canonical'],r['symbol_canonical'])
        if c not in ftmo: continue      # off the live 24-symbol surface
        rows.append(dict(sleeve=s,sym=c,sl=r['sl_distance_price'],r=r['r_gross'],
                         month=r['entry_utc'][:7],day=r['entry_utc'][:10]))
print("\nestate trades 2024-2026 on the live-24 surface:",len(rows))

print("\n=== TRUE MINIMUM PLACEABLE RISK PER SYMBOL (0.01 lots, at the estate's median stop) ===")
print(f"{'canon':11} {'FTMO sym':12} {'FTMO $ @0.01':>12} {'FN sym':10} {'FN $ @0.01':>11}  {'med_sl':>12}  {'p10_sl':>12} {'FTMO$@p10':>10} {'n':>5}")
bysym=collections.defaultdict(list)
for r in rows: bysym[r['sym']].append(r['sl'])
tbl={}
for c in sorted(ftmo):
    sls=bysym.get(c) or []
    if not sls: 
        print(f"{c:11} {ftmo[c]['mt5']:12} {'-':>12} {fn[c]['mt5']:10} {'-':>11}  {'(no trades)':>12}")
        continue
    med=statistics.median(sls); p10=statistics.quantiles(sls,n=10)[0] if len(sls)>9 else min(sls)
    fa=0.01*risk_per_lot(ftmo[c],med); fb=0.01*risk_per_lot(fn[c],med); fp=0.01*risk_per_lot(ftmo[c],p10)
    tbl[c]=dict(ftmo_min=fa,fn_min=fb,med_sl=med,p10_sl=p10,n=len(sls))
    print(f"{c:11} {ftmo[c]['mt5']:12} {fa:12.2f} {fn[c]['mt5']:10} {fb:11.2f}  {med:12.5f}  {p10:12.5f} {fp:10.2f} {len(sls):5d}")
json.dump(tbl,open(T+'f5/min_lot_floor_by_symbol.json','w'),indent=1)

# ---- placeability at fixed $ risk ------------------------------------------
print("\n=== FRACTION OF THE FULL SYSTEM PLACEABLE AT A FIXED $ RISK (per trade, exact) ===")
print("A trade is placeable iff target_risk$ >= 0.01 lots' cash risk at ITS OWN stop.")
print("execution.py:3474-3479 SHEDS anything below volume_min -- it does NOT round up.")
LEVELS=[5,10,15,20,25,30,40,50,75,100,150,200,300,500]
mo=sorted({r['month'] for r in rows if r['month']<'2026-07'})
nmo=len(mo)
print(f"\n{'target$':>8} {'FTMO placeable':>15} {'%':>6} {'trades/mo':>10} | {'FN placeable':>13} {'%':>6} {'trades/mo':>10}")
place={}
for L in LEVELS:
    fa=[r for r in rows if L >= 0.01*risk_per_lot(ftmo[r['sym']],r['sl'])-1e-12]
    fb=[r for r in rows if L >= 0.01*risk_per_lot(fn[r['sym']],r['sl'])-1e-12]
    fa_m=len([r for r in fa if r['month']<'2026-07'])/nmo
    fb_m=len([r for r in fb if r['month']<'2026-07'])/nmo
    place[L]=dict(ftmo_n=len(fa),ftmo_pct=100*len(fa)/len(rows),ftmo_per_month=fa_m,
                  fn_n=len(fb),fn_pct=100*len(fb)/len(rows),fn_per_month=fb_m,
                  ftmo_mean_r=statistics.mean([r['r'] for r in fa]) if fa else None,
                  fn_mean_r=statistics.mean([r['r'] for r in fb]) if fb else None)
    print(f"{L:8d} {len(fa):15d} {100*len(fa)/len(rows):6.1f} {fa_m:10.1f} | {len(fb):13d} {100*len(fb)/len(rows):6.1f} {fb_m:10.1f}")
json.dump(dict(levels=place,total=len(rows),months=nmo),open(T+'f5/placeability.json','w'),indent=1)

# which symbols are shed at each level (FTMO)
print("\n=== SYMBOLS SHED AT EACH FIXED $ LEVEL (FTMO), by trade count ===")
for L in (10,20,30,50,100):
    shed=collections.Counter(r['sym'] for r in rows if L < 0.01*risk_per_lot(ftmo[r['sym']],r['sl']))
    tot=sum(shed.values())
    print(f"  ${L:>4}: {tot:5d} trades shed ({100*tot/len(rows):4.1f}%) -> {shed.most_common(10)}")
print("\n=== SYMBOLS SHED AT EACH FIXED $ LEVEL (redacted_account) ===")
for L in (10,20,30,50,100):
    shed=collections.Counter(r['sym'] for r in rows if L < 0.01*risk_per_lot(fn[r['sym']],r['sl']))
    tot=sum(shed.values())
    print(f"  ${L:>4}: {tot:5d} trades shed ({100*tot/len(rows):4.1f}%) -> {shed.most_common(10)}")
