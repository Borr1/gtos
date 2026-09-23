"""F5: account trajectory at fixed-dollar per-trade size, decisions taken at NOMINAL risk.

Design (per the owner's constraint): the decision pipeline runs at nominal 2.0% and is therefore
subject to the SAME throttles production runs -- one unit per (sleeve,symbol,day), one per
(cluster,day), and the 4% gross-open-risk cap. Only the final lot is scaled. So the trade POPULATION
here is the throttled one, and only the DOLLARS per trade change.

Round-up rule (owner requirement 4): actual_$ = max(target_$, floor_$), never skip.
"""
import gzip,json,collections,statistics,random,math
T='/Users/borr/.claude/jobs/adb9e69b/tmp/'
random.seed(20260812)

p1=json.load(open(T+'P1_SPECS.json'))['profiles']
cmpd=json.load(open(T+'BROKER_SPEC.json'))
ftmo={c:dict(ts=s['trade_tick_size'],tv=s['trade_tick_value'],mt5=s['mt5_symbol']) for c,s in p1['operator_profile']['symbols'].items()}
fn={k:dict(v) for k,v in ftmo.items()}
byftmo={v['mt5']:k for k,v in ftmo.items()}
for e in cmpd['comparison']:
    canon=byftmo.get(e.get('ftmo_symbol'))
    if not canon: continue
    df=e.get('differing_fields') or {}
    if 'trade_tick_size' in df: fn[canon]['ts']=df['trade_tick_size']['redacted_account']
    if 'trade_tick_value' in df: fn[canon]['tv']=df['trade_tick_value']['redacted_account']
SPEC={'FTMO':ftmo,'redacted_account':fn}
def floor_usd(acct,sym,sl): s=SPEC[acct][sym]; return 0.01*(sl/s['ts'])*s['tv']

# ---- trades with 4-component net R (from net_expectancy.py, recomputed inline) --------------
C=json.load(open(T+'COSTS_V11.json'))
FT_SYM={c:s['mt5_symbol'] for c,s in p1['operator_profile']['symbols'].items()}
FN_SYM={c:s['mt5_symbol'] for c,s in p1['redacted_account']['symbols'].items()}
def cost_r(acct,canon,sl,entry,direction,hold_h):
    bs=(FT_SYM if acct=='FTMO' else FN_SYM).get(canon)
    inst=C['accounts'][acct]['instruments'].get(bs)
    if inst is None: return None
    spec=inst['spec']; upppl=spec['trade_tick_value']/spec['trade_tick_size']
    tot=0.0
    p50=((inst.get('spread_price') or {}).get('percentiles') or {}).get('p50')
    if p50: tot+=p50/sl
    com=inst.get('commission') or {}
    if com.get('kind')=='per_lot': tot+=com['value']/(upppl*sl)
    elif com.get('kind')=='notional_bp': tot+=(com['value']/1e4*spec['trade_contract_size']*entry)/(upppl*sl)
    tot+=(inst.get('slippage') or {}).get('value_r') or 0.0
    if spec.get('swap_mode')==1:
        pts=spec['swap_long'] if direction>0 else spec['swap_short']
        usd_night=pts*spec['point']*upppl
        nights=math.floor(hold_h/24.0)+(1 if (hold_h%24.0)>12 else 0)
        tot+=max(0.0,-(nights*usd_night))/(upppl*sl)
    return tot

d=json.load(gzip.open(T+'AA_ESTATE.json.gz','rt'))
ALIAS={'GER40_cash':'GER40','JP225_cash':'JP225','US100_cash':'NAS100','US500_cash':'SPX500'}
# asset-class cluster, derived from the canonical symbol (mirrors admission.CLUSTER_OF_SLEEVE's asset_class)
def cluster(sym):
    if sym in ('BTCUSD','ETHUSD'): return 'crypto'
    if sym in ('XAUUSD','XAGUSD'): return 'metals'
    if sym in ('UKOIL_cash','USOIL_cash'): return 'energy'
    if sym in ('GER40','JP225','NAS100','SPX500','UK100','US30_cash'): return 'index'
    if sym.endswith('JPY'): return 'jpy'
    return 'fx'
raw=[]
for s,rs in d['trades'].items():
    for r in rs:
        if r['entry_utc'][:4] not in ('2024','2025','2026'): continue
        c=ALIAS.get(r['symbol_canonical'],r['symbol_canonical'])
        if c not in ftmo: continue
        raw.append(dict(sleeve=s,sym=c,sl=r['sl_distance_price'],entry=r['entry_price'],
                        dirn=r['direction'],hold=r.get('hold_hours') or 0.0,rg=r['r_gross'],
                        day=r['entry_utc'][:10],ts=r['entry_utc'],cl=cluster(c)))
for r in raw:
    r['netF']=r['rg']-cost_r('FTMO',r['sym'],r['sl'],r['entry'],r['dirn'],r['hold'])
    r['netN']=r['rg']-cost_r('redacted_account',r['sym'],r['sl'],r['entry'],r['dirn'],r['hold'])
raw.sort(key=lambda r:r['ts'])

# ---- THROTTLE simulation: one unit per (sleeve,symbol,day), one per (cluster,day) ----------
seen_ss=set(); seen_cd=set(); thr=[]
for r in raw:
    k1=(r['sleeve'],r['sym'],r['day']); k2=(r['cl'],r['day'])
    if k1 in seen_ss or k2 in seen_cd: continue
    seen_ss.add(k1); seen_cd.add(k2); thr.append(r)
days_all=sorted({r['day'] for r in raw})
span_days=(len(days_all))
mo_raw=collections.Counter(r['day'][:7] for r in raw); mo_thr=collections.Counter(r['day'][:7] for r in thr)
full=[k for k in sorted(mo_raw) if k<'2026-07']
print(f"UNCAPPED : {len(raw):6d} trades  {statistics.mean([mo_raw[k] for k in full]):7.1f}/mo  netR/trade FTMO {statistics.mean([r['netF'] for r in raw]):+.4f}")
print(f"THROTTLED: {len(thr):6d} trades  {statistics.mean([mo_thr[k] for k in full]):7.1f}/mo  netR/trade FTMO {statistics.mean([r['netF'] for r in thr]):+.4f}")
print(f"           [Lane 4 measured throttled cell: 232.5 trades/mo, -0.01097 R spread-only]")

for label,pop in (('UNCAPPED',raw),('THROTTLED',thr)):
    byday=collections.defaultdict(list)
    for r in pop: byday[r['day']].append(r)
    dr=[sum(x['netF'] for x in v) for k,v in sorted(byday.items())]
    print(f"{label:10} days={len(byday):4d} R/day mean {statistics.mean(dr):+.4f} sd {statistics.pstdev(dr):.3f} min {min(dr):+.2f} | R/mo mean {statistics.mean([sum(x['netF'] for x in pop if x['day'][:7]==k) for k in full]):+.2f}")

# ---- effective dollar risk with ROUND-UP ---------------------------------------------------
print("\n=== EFFECTIVE $ RISK PER TRADE WITH ROUND-UP TO MIN LOT (throttled population) ===")
print(f"{'target$':>7} | {'FTMO eff$':>9} {'infl':>6} {'%rounded':>9} | {'FN eff$':>9} {'infl':>6} {'%rounded':>9}")
LEVELS=[1,2,3,5,7.5,10,15,20,25,30,50,100]
eff={}
for L in LEVELS:
    row={}
    for acct,key in (('FTMO','netF'),('redacted_account','netN')):
        act=[max(L,floor_usd(acct,r['sym'],r['sl'])) for r in thr]
        nr=sum(1 for r in thr if floor_usd(acct,r['sym'],r['sl'])>L)
        row[acct]=dict(eff=statistics.mean(act),infl=statistics.mean(act)/L,rounded=100*nr/len(thr))
    eff[L]=row
    print(f"{L:7.1f} | {row['FTMO']['eff']:9.2f} {row['FTMO']['infl']:6.2f}x {row['FTMO']['rounded']:8.1f}% | {row['redacted_account']['eff']:9.2f} {row['redacted_account']['infl']:6.2f}x {row['redacted_account']['rounded']:8.1f}%")

# ---- MONTE CARLO ---------------------------------------------------------------------------
byday=collections.defaultdict(list); 
for r in thr: byday[r['day']].append(r)
DAYS=[v for k,v in sorted(byday.items())]
BLOCK=5
def sim(acct,key,target,months,n=4000,initial=100000.0,daily_limit=5000.0,floor_equity=90000.0):
    dpm=len(DAYS)/ (len(full)+ (1 if True else 0))     # measured days-with-trades per month
    dpm=len(DAYS)/30.0
    ndays=int(round(dpm*months))
    breach_dd=0; breach_daily=0; ends=[]; worst=[]
    for _ in range(n):
        eq=initial; peakloss=0.0; hit_dd=False; hit_daily=False
        i=0
        while i<ndays:
            start=random.randrange(0,max(1,len(DAYS)-BLOCK))
            for b in range(BLOCK):
                if i>=ndays: break
                day=DAYS[(start+b)%len(DAYS)]
                pnl=0.0
                for r in day:
                    a=max(target,floor_usd(acct,r['sym'],r['sl']))
                    pnl+=r[key]*a
                if pnl<=-daily_limit: hit_daily=True
                eq+=pnl
                if eq<=floor_equity: hit_dd=True
                peakloss=min(peakloss,eq-initial)
                i+=1
        breach_dd+=hit_dd; breach_daily+=hit_daily; ends.append(eq); worst.append(peakloss)
    return dict(p_floor=breach_dd/n,p_daily=breach_daily/n,
                end_mean=statistics.mean(ends),end_p05=sorted(ends)[int(0.05*n)],end_p50=statistics.median(ends),
                worst_mean=statistics.mean(worst),worst_p05=sorted(worst)[int(0.05*n)],ndays=ndays)

print("\n=== MONTE CARLO: FTMO ($100k, static $90,000 floor, $5,000 fixed daily limit) ===")
print("     block-bootstrap of whole trading days (block=5) from the throttled estate, 4,000 paths")
print(f"{'target$':>7} {'mo':>3} {'eff$/trade':>10} {'P(floor)':>9} {'P(daily)':>9} {'E[end $]':>11} {'p05 end':>10} {'E[worst DD $]':>13}")
res={}
for L in [5,10,20,30,50,100,200]:
    for M in (3,6,12):
        s=sim('FTMO','netF',L,M)
        res[f"FTMO_{L}_{M}"]=s
        print(f"{L:7d} {M:3d} {eff[L]['FTMO']['eff'] if L in eff else float('nan'):10.2f} {s['p_floor']:9.3f} {s['p_daily']:9.3f} {s['end_mean']:11,.0f} {s['end_p05']:10,.0f} {s['worst_mean']:13,.0f}")
print("\n=== MONTE CARLO: redacted_account ($100k, 10% overall, $5,000 fixed daily) ===")
for L in [10,20,30,50]:
    for M in (3,6,12):
        s=sim('redacted_account','netN',L,M)
        res[f"FN_{L}_{M}"]=s
        print(f"{L:7d} {M:3d} {eff[L]['redacted_account']['eff']:10.2f} {s['p_floor']:9.3f} {s['p_daily']:9.3f} {s['end_mean']:11,.0f} {s['end_p05']:10,.0f} {s['worst_mean']:13,.0f}")
json.dump(dict(effective_risk=eff,mc=res,
               throttled_trades=len(thr),uncapped_trades=len(raw),
               throttled_per_month=statistics.mean([mo_thr[k] for k in full]),
               uncapped_per_month=statistics.mean([mo_raw[k] for k in full]),
               net_r_throttled_FTMO=statistics.mean([r['netF'] for r in thr]),
               net_r_uncapped_FTMO=statistics.mean([r['netF'] for r in raw]),
               net_r_throttled_FN=statistics.mean([r['netN'] for r in thr])),
          open(T+'f5/mc_trajectory.json','w'),indent=1)
