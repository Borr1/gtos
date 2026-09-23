"""K1-b: replay every live FTMO cycle from bars and compare generated intents to live.

FTMO only -- the redacted_account bar pull is 7 of 43 symbols and would silently bias
any cross-broker claim (INGEST_NOTE.md).
"""
import sys, os, glob, json, pickle, yaml, datetime as dt, collections, time
sys.path.insert(0,'.')
from src.research_infra.replay_policy.generation import GenerationPort, CsvBarSource
from src.research_infra.replay_policy import packet_validation as PV
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
from src.components.ultimate_book.sleeves.registry import active_specs
from src.components.ultimate_book.admission import resolve_market_expansion_sleeves

SCRATCH='/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave3-generation-port-20260727/30c8b23c-f232-4a6d-b3d8-303f09f5cd4a/scratchpad/k1'
BARS='/Users/borr/GTOSActive/vps-bars-20260727'
TFN={'M15':15,'H1':16385,'H4':16388,'D1':16408}
LIMIT=int(sys.argv[1]) if len(sys.argv)>1 else 0

base=yaml.safe_load(open('config/agent_config.yaml'))
base_rt=dict(base.get('gtos_vnext_runtime') or {})
prof=yaml.safe_load(open('config/profiles/operator_profile.yaml')) or {}
res=build_broker_symbol_resolver(prof)

files={}
for p in glob.glob(f'{BARS}/FTMO_*.csv.gz'):
    stem=os.path.basename(p)[:-7]           # FTMO_SYM_TF
    _,sym,tfn = stem.split('_',1)[0], stem.split('_')[1], stem.rsplit('_',1)[1]
    sym=stem[len('FTMO_'):-(len(tfn)+1)]
    if tfn in TFN: files[(res(sym),TFN[tfn])]=p     # key by BROKER symbol (book_engine.py:461)
src=CsvBarSource(files, label='vps-bars-20260727/FTMO')
HAVE={s for s,_ in files}
print(f"bar series available: {len(files)}")

# tag sets by telemetry shape (spec_count -> advancing timeframes)
me,_=resolve_market_expansion_sleeves(policy=base_rt.get('ultimate_book_market_expansion_policy'),
        explicit_sleeves=base_rt.get('ultimate_book_market_expansion_sleeves') or [])
specs=active_specs(None, include_candidate_book=True,
        candidate_book_sleeves=base_rt.get('ultimate_book_candidate_book_sleeves'),
        include_market_expansion_book=True, market_expansion_sleeves=me)
tf_tags=collections.defaultdict(list)
for s in specs: tf_tags[s.timeframe].append(s.tag)
SHAPE_TAGS={
 (6,27):  tf_tags[TFN['H4']],
 (10,53): tf_tags[TFN['M15']],
 (13,15): tf_tags[TFN['D1']],
 (16,80): tf_tags[TFN['M15']]+tf_tags[TFN['H4']],
 (19,42): tf_tags[TFN['H4']]+tf_tags[TFN['D1']],
 (23,68): tf_tags[TFN['M15']]+tf_tags[TFN['D1']],
 (29,95): tf_tags[TFN['M15']]+tf_tags[TFN['H4']]+tf_tags[TFN['D1']],
}
cycles=pickle.load(open(f'{SCRATCH}/cycles.pkl','rb'))
ft=[c for c in cycles.values() if c['ns']=='operator_profile']
ft.sort(key=lambda c: c['created'] or '')
if LIMIT: ft=ft[:LIMIT]
print(f"replaying {len(ft)} FTMO cycles")

ports={}
out=[]; t0=time.time()
for i,c in enumerate(ft):
    tags=SHAPE_TAGS.get(c['shape'])
    if tags is None:
        out.append(dict(cycle=c['created'], shape=list(c['shape']), error='unknown_shape')); continue
    cfg=PV.config_from_bridge(c['bridge'], base=base_rt)
    ck=json.dumps({k:cfg.get(k) for k in sorted(cfg)}, sort_keys=True, default=str)
    if ck not in ports:
        ports[ck]=GenerationPort(cfg, src, namespace='k1b', broker_symbol=res)
    now=dt.datetime.fromisoformat(c['created'])
    r=ports[ck].generate(now, tags=tags)
    got={(x.sleeve, x.symbol, x.decision_bar_iso) for x in r.candidates}
    live=set(map(tuple,c['intents']))
    # a live intent on a symbol with no delivered bars can never be reproduced;
    # separate it so it is an enumerated evidence gap, not a false port miss.
    live_cov={t for t in live if res(t[1]) in HAVE}
    out.append(dict(cycle=c['created'], shape=list(c['shape']), n_in=c['n_in'],
                    live=sorted(live), live_covered=sorted(live_cov), port=sorted(got)))
    if (i+1)%100==0:
        el=time.time()-t0
        print(f"  {i+1}/{len(ft)}  {el:.0f}s  ({el/(i+1):.2f}s/cycle)", flush=True)
json.dump(out, open(f'{SCRATCH}/k1b_raw.json','w'))
print(f"done in {time.time()-t0:.0f}s -> k1b_raw.json")
