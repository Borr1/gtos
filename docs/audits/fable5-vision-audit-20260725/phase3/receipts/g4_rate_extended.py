"""G4 re-measured on the VPS bars: full 6-symbol metals universe, multi-year.

The published rates rested on 1-3 fires over 480 closes x 2 symbols. The delivered
archive carries all six metals_core symbols (incl. the four crosses) and DASHUSD,
so the rate can be re-estimated with a far larger denominator -- and the D0
counterfactual (what the crosses would have contributed) becomes measurable.
"""
import sys, os, glob, json, yaml, datetime as dt, collections, time
sys.path.insert(0,'.')
from dataclasses import replace
from src.components.ultimate_book.sleeves import registry as REG
calls=collections.Counter()
def wrap(tag, fn):
    def g(symbol, bars, day, **kw):
        calls[(tag,symbol)]+=1
        return fn(symbol,bars,day,**kw)
    return g
REG.BUILT={k:replace(v,generator=wrap(k,v.generator)) for k,v in REG.BUILT.items()}
REG.CANDIDATE_BUILT={k:replace(v,generator=wrap(k,v.generator)) for k,v in REG.CANDIDATE_BUILT.items()}

from src.research_infra.replay_policy.generation import GenerationPort, CsvBarSource
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
TFN={'M15':15,'H4':16388,'D1':16408}
base=yaml.safe_load(open('config/agent_config.yaml')); cfg=dict(base.get('gtos_vnext_runtime') or {})
prof=yaml.safe_load(open('config/profiles/operator_profile.yaml')) or {}
res=build_broker_symbol_resolver(prof)
files={}
for p in glob.glob('/Users/borr/GTOSActive/vps-bars-20260727/FTMO_*.csv.gz'):
    stem=os.path.basename(p)[:-7]; tfn=stem.rsplit('_',1)[1]
    sym=stem[len('FTMO_'):-(len(tfn)+1)]
    if tfn in TFN: files[(res(sym),TFN[tfn])]=p
src=CsvBarSource(files, label='vps-bars-FTMO')
port=GenerationPort(cfg, src, namespace='g4x2', broker_symbol=res)

START=dt.datetime(2024,1,1,tzinfo=dt.timezone.utc); END=dt.datetime(2026,7,26,tzinfo=dt.timezone.utc)
closes=sorted({dt.datetime.fromisoformat(r['time'])+dt.timedelta(minutes=240)
               for r in src._load((res('XAUUSD'),TFN['H4']))})
closes=[t for t in closes if START<=t<=END]
TAGS=['metals_core','metals_softband','metals_ob_micro','crypto','energy_agri','idxrev']
print(f"driving {len(closes)} H4 closes {closes[0].date()}..{closes[-1].date()}", flush=True)
fires=collections.Counter(); persym=collections.Counter(); dates=collections.defaultdict(set)
t0=time.time()
for i,t in enumerate(closes):
    for c in port.generate(t, tags=TAGS).candidates:
        fires[c.sleeve]+=1; persym[(c.sleeve,c.symbol)]+=1; dates[c.sleeve].add(t.date().isoformat())
    if (i+1)%2000==0: print(f"  {i+1}/{len(closes)} {time.time()-t0:.0f}s", flush=True)
print(f"\n{'sleeve':20s} {'invoked':>8s} {'fires':>6s} {'rate/inv':>10s} {'fire days':>10s}")
out={}
for s in TAGS:
    inv=sum(v for (tg,_),v in calls.items() if tg==s)
    r=fires[s]/inv if inv else float('nan')
    out[s]=dict(invoked=inv,fires=fires[s],rate=r,fire_days=len(dates[s]))
    print(f"{s:20s} {inv:8d} {fires[s]:6d} {r:10.5f} {len(dates[s]):10d}")
print("\nper (sleeve,symbol):")
for k,v in sorted(persym.items(), key=lambda kv:-kv[1]): print(f"   {k[0]:22s} {k[1]:10s} {v}")
json.dump({'window':[str(closes[0]),str(closes[-1])],'closes':len(closes),
           'sleeves':out,'per_symbol':{f"{a}|{b}":v for (a,b),v in persym.items()}},
          open('/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave3-generation-port-20260727/30c8b23c-f232-4a6d-b3d8-303f09f5cd4a/scratchpad/k1/g4_extended2.json','w'), indent=2)
