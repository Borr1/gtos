"""F5: cost-true net expectancy for the FULL 32-sleeve system on the live-24 surface.
Four-component cost per the repo's own conventions (BROKER_TRUE_COSTS_V1_1.json 'conventions').
"""
import gzip,json,collections,statistics,math
T='/Users/borr/.claude/jobs/adb9e69b/tmp/'
C=json.load(open(T+'COSTS_V11.json'))
p1=json.load(open(T+'P1_SPECS.json'))['profiles']

# canonical -> broker symbol per account
FT_SYM={c:s['mt5_symbol'] for c,s in p1['operator_profile']['symbols'].items()}
FN_SYM={c:s['mt5_symbol'] for c,s in p1['redacted_account']['symbols'].items()}

def cost_r(acct, canon, sl, entry, direction, hold_h):
    m=FT_SYM if acct=='FTMO' else FN_SYM
    bs=m.get(canon)
    inst=C['accounts'][acct]['instruments'].get(bs)
    if inst is None: return None,None
    spec=inst['spec']
    ts=spec['trade_tick_size']; tv=spec['trade_tick_value']
    upppl=tv/ts                                  # USD per 1.0 price unit per lot
    out={}
    sp=inst.get('spread_price') or {}
    p50=(sp.get('percentiles') or {}).get('p50')
    out['spread']= (p50/sl) if p50 else None
    com=inst.get('commission') or {}
    if com.get('kind')=='per_lot':
        out['commission']=com['value']/(upppl*sl)
    elif com.get('kind')=='notional_bp':
        usd=com['value']/1e4*spec['trade_contract_size']*entry
        out['commission']=usd/(upppl*sl)
    elif com.get('kind')=='zero':
        out['commission']=0.0
    else:
        out['commission']=None
    sl_r=(inst.get('slippage') or {}).get('value_r')
    out['slippage']=sl_r
    # swap: mode 1 = points/night. nights = rollover crossings, approximated from hold hours.
    if spec.get('swap_mode')==1:
        pts=spec['swap_long'] if direction>0 else spec['swap_short']
        usd_night=pts*spec['point']*upppl
        nights=math.floor(hold_h/24.0)+(1 if (hold_h%24.0)>12 else 0)
        out['swap']=max(0.0,-(nights*usd_night))/(upppl*sl)   # POSITIVE = a cost; credit floored at 0
        out['_swap_credit']= (nights*usd_night)/(upppl*sl) if usd_night>0 else 0.0
    else:
        out['swap']=None
    tot=sum(v for k,v in out.items() if not k.startswith('_') and v is not None)
    miss=[k for k,v in out.items() if not k.startswith('_') and v is None]
    return tot,dict(parts=out,missing=miss)

d=json.load(gzip.open(T+'AA_ESTATE.json.gz','rt'))
ALIAS={'GER40_cash':'GER40','JP225_cash':'JP225','US100_cash':'NAS100','US500_cash':'SPX500'}
rows=[]
for s,rs in d['trades'].items():
    for r in rs:
        if r['entry_utc'][:4] not in ('2024','2025','2026'): continue
        c=ALIAS.get(r['symbol_canonical'],r['symbol_canonical'])
        if c not in FT_SYM: continue
        rows.append(dict(sleeve=s,sym=c,sl=r['sl_distance_price'],entry=r['entry_price'],
                         dirn=r['direction'],hold=r.get('hold_hours') or 0.0,
                         rg=r['r_gross'],month=r['entry_utc'][:7],day=r['entry_utc'][:10],
                         exit_reason=r.get('exit_reason')))
print("trades:",len(rows))
res={}
for acct in ('FTMO','redacted_account'):
    net=[];miss=collections.Counter();parts=collections.defaultdict(list)
    for r in rows:
        c,det=cost_r(acct,r['sym'],r['sl'],r['entry'],r['dirn'],r['hold'])
        if c is None: miss['no_instrument']+=1; continue
        for k in det['missing']: miss[k]+=1
        for k,v in det['parts'].items():
            if not k.startswith('_') and v is not None: parts[k].append(v)
        r['cost_'+acct]=c
        net.append(r['rg']-c)
    n=len(net); m=statistics.mean(net); sd=statistics.pstdev(net)
    g=statistics.mean([r['rg'] for r in rows])
    print(f"\n### {acct}: n={n} gross={g:+.4f} cost_mean={statistics.mean([r['rg']-x for r,x in zip(rows[:n],net)]) if False else (g-m):+.4f} NET={m:+.4f} R/trade  sd={sd:.4f}")
    for k,v in parts.items():
        print(f"     cost component {k:11} mean={statistics.mean(v):.4f} R  median={statistics.median(v):.4f}  n={len(v)}")
    print("     missing components:",dict(miss))
    res[acct]=dict(n=n,gross=g,net=m,sd=sd,cost=g-m)

# daily aggregation for the MC (FTMO cost basis, the stricter of the two on most symbols)
byday=collections.defaultdict(list)
for r in rows:
    if 'cost_FTMO' in r: byday[r['day']].append(r['rg']-r['cost_FTMO'])
days=sorted(byday)
dayR=[sum(v) for k,v in sorted(byday.items())]
print(f"\nTRADING DAYS with >=1 trade: {len(days)}  span {days[0]}..{days[-1]}")
print(f"mean R/day {statistics.mean(dayR):+.4f}  sd {statistics.pstdev(dayR):.4f}  min {min(dayR):+.2f} max {max(dayR):+.2f}")
print(f"trades/trading-day mean {len(rows)/len(days):.2f}")
mo=collections.Counter(r['month'] for r in rows)
full=[k for k in sorted(mo) if k<'2026-07']
print("months:",len(full),"mean trades/mo",statistics.mean([mo[k] for k in full]))
bymo=collections.defaultdict(float)
for r in rows:
    if 'cost_FTMO' in r: bymo[r['month']]+=r['rg']-r['cost_FTMO']
mr=[bymo[k] for k in full]
print(f"NET R/month: mean {statistics.mean(mr):+.2f}  sd {statistics.pstdev(mr):.2f}  min {min(mr):+.2f} max {max(mr):+.2f}  neg months {sum(1 for x in mr if x<0)}/{len(mr)}")
json.dump(dict(summary=res,
               per_trade_net_FTMO=[r['rg']-r['cost_FTMO'] for r in rows if 'cost_FTMO' in r],
               per_day_net_FTMO=dict(sorted(byday.items())),
               months=len(full), trades_per_month=statistics.mean([mo[k] for k in full]),
               monthly_net_R=dict((k,bymo[k]) for k in full)),
          open(T+'f5/net_expectancy.json','w'))
