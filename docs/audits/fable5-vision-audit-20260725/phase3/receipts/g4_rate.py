"""G4 half 2, final: real bar closes AND broker-name keyed bar files.

Two driver bugs were caught by one control -- idxrev, the top live placer, firing
zero. (1) synthetic UTC bar closes instead of the archive's broker-aligned ones;
(2) bar files keyed by CANONICAL symbol while book_engine.py:461 fetches under the
BROKER symbol, so every index/oil series silently returned no bars.
"""
import sys, os, yaml, glob, datetime as dt, collections; sys.path.insert(0,'.')
from src.research_infra.replay_policy.generation import GenerationPort, CsvBarSource
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.components.ultimate_book.sleeves.registry import active_specs
from src.components.ultimate_book.admission import resolve_market_expansion_sleeves

TF={'M15':15,'H1':16385,'H4':16388,'D1':16408}
base=yaml.safe_load(open('config/agent_config.yaml')); cfg=dict(base.get('gtos_vnext_runtime') or {})
me,_=resolve_market_expansion_sleeves(policy=cfg.get('ultimate_book_market_expansion_policy'),
        explicit_sleeves=cfg.get('ultimate_book_market_expansion_sleeves') or [])
specs=active_specs(None, include_candidate_book=True,
        candidate_book_sleeves=cfg.get('ultimate_book_candidate_book_sleeves'),
        include_market_expansion_book=True, market_expansion_sleeves=me)
prof=yaml.safe_load(open('config/profiles/operator_profile.yaml')) or {}
res=build_broker_symbol_resolver(prof)

raw={}
for f in glob.glob('data/historical_2026/*.csv'):
    b=os.path.basename(f)[:-4]; sym,_,tfn=b.rpartition('_')
    if tfn in TF: raw[(sym,TF[tfn])]=f
files={(res(s),tf):p for (s,tf),p in raw.items()}          # key by BROKER name
print("canonical->broker remaps that matter:",
      {s:res(s) for s,_ in raw if res(s)!=s})

src=CsvBarSource(files, label='data/historical_2026')
port=GenerationPort(cfg, src, namespace='g4_archive3', broker_symbol=res)
h4_tags=[s.tag for s in specs if s.timeframe==TF['H4']]

closes=set()
for key in [(res('XAUUSD'),TF['H4']),(res('BTCUSD'),TF['H4'])]:
    for r in src._load(key):
        closes.add(dt.datetime.fromisoformat(r['time'])+dt.timedelta(minutes=240))
closes=sorted(t for t in closes if dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)<=t
              <=dt.datetime(2026,4,24,23,59,tzinfo=dt.timezone.utc))
print(f"driving {len(closes)} real H4 closes {closes[0].date()}..{closes[-1].date()}")

fires=collections.Counter(); persym=collections.Counter()
for t in closes:
    r=port.generate(t, tags=h4_tags)
    for c in r.candidates: fires[c.sleeve]+=1; persym[(c.sleeve,c.symbol)]+=1
print("\nPER-SLEEVE FIRES (archive, 2026-01-01..04-24):")
for s in sorted(h4_tags): print(f"   {s:26s} {fires[s]:5d}")
print("\nper (sleeve,symbol):")
for k,v in sorted(persym.items(), key=lambda kv:-kv[1]): print(f"   {k[0]:24s} {k[1]:14s} {v}")
