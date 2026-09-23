"""K1-b disagreement enumeration, classified. Two levels, because the live record
supports two different comparisons and only one of them can reach zero.

  COUNT level    -- live's own `bridge.n_candidates_in` vs the port's candidate
                    count, per cycle. Live's counter is complete: it is written by
                    the bridge from the intent list itself, so it has no attribution
                    gap. This is the level at which "zero disagreements" is
                    achievable and therefore the level K1-b is judged on.
  IDENTITY level -- the set of (sleeve, symbol, decision_bar_iso). Live only names
                    these on some event types (D15/C6): `unit_admitted` is
                    sleeve-null on 81% of rows, `unit_shadow` on 41%. So a port
                    intent that live also had can still be unmatchable here.
"""
import json, collections, sys, glob, os, yaml
sys.path.insert(0,'.')
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
K='/private/tmp/claude-501/-Users-borr-GTOSActive-worktrees-wave3-generation-port-20260727/30c8b23c-f232-4a6d-b3d8-303f09f5cd4a/scratchpad/k1'
BARS='/Users/borr/GTOSActive/vps-bars-20260727'
raw=json.load(open(f'{K}/{sys.argv[1] if len(sys.argv)>1 else "k1b_raw.json"}'))
prof=yaml.safe_load(open('config/profiles/operator_profile.yaml')) or {}
res=build_broker_symbol_resolver(prof)
HAVE=collections.defaultdict(set)
for p in glob.glob(f'{BARS}/FTMO_*.csv.gz'):
    stem=os.path.basename(p)[:-7]; tf=stem.rsplit('_',1)[1]; sym=stem[len('FTMO_'):-(len(tf)+1)]
    HAVE[tf].add(sym)

rows=[r for r in raw if 'error' not in r]
print(f"cycles replayed: {len(rows)}  (errors {len(raw)-len(rows)})\n")

# ---------------- COUNT LEVEL ----------------
agree=0; dis=[]
for r in rows:
    n=r.get('n_in'); p=len(r['port'])
    if n is None: continue
    if n==p: agree+=1
    else: dis.append((r['cycle'], tuple(r['shape']), n, p,
                      sorted({tuple(x) for x in r.get('live_covered',[])}),
                      sorted({tuple(x) for x in r['port']})))
tot=agree+len(dis)
print(f"COUNT LEVEL: {agree}/{tot} cycles agree exactly ({100*agree/tot:.2f}%)")
print(f"             {len(dis)} cycles disagree\n")
d_over=[x for x in dis if x[3]>x[2]]; d_under=[x for x in dis if x[3]<x[2]]
print(f"  port OVER-generated : {len(d_over)} cycles (sum +{sum(x[3]-x[2] for x in d_over)})")
print(f"  port UNDER-generated: {len(d_under)} cycles (sum -{sum(x[2]-x[3] for x in d_under)})")

# classify the under-generating cycles by whether the missing live intent lacks bars
def tf_of(bar_iso, sleeve): return None
noBars=collections.Counter(); withBars=collections.Counter()
for cyc,shape,n,p,live,port in d_under:
    for sl,sym,bar in live:
        if sym not in HAVE['M15'] and sym not in HAVE['H4'] and sym not in HAVE['D1']:
            noBars[(sl,sym)]+=1
        elif (sl,sym,bar) not in set(port):
            withBars[(sl,sym)]+=1
print(f"\n  of the under-generated, named live intents the port missed:")
print(f"    on symbols with NO delivered bars: {sum(noBars.values())}")
for k,v in noBars.most_common(8): print(f"       {k[0]:24s} {k[1]:12s} {v}")
print(f"    on symbols WITH bars (real misses): {sum(withBars.values())}")
for k,v in withBars.most_common(15): print(f"       {k[0]:24s} {k[1]:12s} {v}")

# ---------------- IDENTITY LEVEL ----------------
LIVE=set(); LIVEC=set(); PORT=set()
for r in rows:
    LIVE|={tuple(x) for x in r['live']}
    LIVEC|={tuple(x) for x in r.get('live_covered',[])}
    PORT|={tuple(x) for x in r['port']}
print(f"\nIDENTITY LEVEL")
print(f"  live named        {len(LIVE)}   (of a counter total {sum(r.get('n_in') or 0 for r in rows)})")
print(f"  live named, bars  {len(LIVEC)}")
print(f"  port              {len(PORT)}")
print(f"  agreed            {len(LIVEC&PORT)}")
print(f"  live-only         {len(LIVEC-PORT)}")
print(f"  port-only         {len(PORT-LIVEC)}")
for label,s in (("live-only",LIVEC-PORT),("port-only",PORT-LIVEC)):
    print(f"\n  {label} by sleeve:")
    for k,v in collections.Counter(x[0] for x in s).most_common(): print(f"     {k:30s} {v}")
json.dump({'count_agree':agree,'count_total':tot,
           'disagreements':[{'cycle':c,'shape':list(sh),'live_n':n,'port_n':p,
                             'live_named':[list(x) for x in lv],'port':[list(x) for x in po]}
                            for c,sh,n,p,lv,po in dis]},
          open(f'{K}/k1b_disagreements.json','w'), indent=1)
print(f"\nwrote k1b_disagreements.json ({len(dis)} enumerated)")
