"""Driver: run H1->M15 cascade better-fill transfer on crypto + energy. Forward-only LTF."""
import sys, json, collections, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import TW_mtf_cascade_transfer as C

def agg(vals):
    if not vals: return dict(n=0, ev=0.0, win=0.0)
    n=len(vals); return dict(n=n, ev=round(sum(vals)/n,4), win=round(100*sum(1 for x in vals if x>0)/n,1))

def report_cascade(name, rows):
    fwd=[r for r in rows if r['year']>=2025]
    print(f"\n--- {name} (cascade vs base-H4, same entries) ---")
    print(f"  src mix (all): {dict(collections.Counter(r['src'] for r in rows))}")
    for era,pred in (('TRAIN<=2024',lambda r:r['year']<=2024),('2025',lambda r:r['year']==2025),
                     ('2026',lambda r:r['year']==2026),('FWD',lambda r:r['year']>=2025)):
        sub=[r for r in rows if pred(r)]
        if not sub: continue
        b=agg([r['base_R'] for r in sub]); c=agg([r['casc_R'] for r in sub])
        print(f"  {era:<11} n{b['n']:>3}  base ev{b['ev']:+.3f}/w{b['win']:.0f}  ->  casc ev{c['ev']:+.3f}/w{c['win']:.0f}")
    # paired forward
    diffs=[r['casc_R']-r['base_R'] for r in fwd]
    n=len(diffs); mu=sum(diffs)/n if n else 0; sd=statistics.pstdev(diffs) if n>1 else 0
    t=mu/(sd/(n**0.5)) if sd>0 else 0
    print(f"  paired FWD casc-base: n{n} dR{mu:+.4f} t{t:.2f}")
    # only rows where the LTF actually re-priced the fill
    rep=[r for r in fwd if r['src']!='h4']
    if rep:
        d2=[r['casc_R']-r['base_R'] for r in rep]; m2=sum(d2)/len(d2)
        print(f"  FWD better-filled rows only (n{len(rep)}): dR{m2:+.4f} (base {sum(r['base_R'] for r in rep)/len(rep):+.3f} -> casc {sum(r['casc_R'] for r in rep)/len(rep):+.3f})")
    return dict(name=name, fwd_base=agg([r['base_R'] for r in fwd]), fwd_casc=agg([r['casc_R'] for r in fwd]),
                paired_fwd=dict(n=n,dR=round(mu,4),t=round(t,2)), src=dict(collections.Counter(r['src'] for r in rows)))

OUT={}
print("="*100); print("CRYPTO — H1->M15 cascade better-fill transfer (FORWARD-ONLY LTF 2025-06+)"); print("="*100)
cs_ents=C.crypto_sleeve()
print(f"crypto signals: {len(cs_ents)} (fwd {sum(1 for e in cs_ents if e['year']>=2025)})")
for ex in ['target4','state_d','combo']:
    rows,leaks,aud=C.run_cascade(cs_ents, ex)
    print(f"\n### crypto exit={ex} | leak audit: {leaks} leaks / {aud} LTF entries checked")
    OUT[f'crypto_{ex}']=report_cascade(f"crypto/{ex}", rows)

print("\n"+"="*100); print("ENERGY — H1->M15 cascade better-fill transfer (FORWARD-ONLY LTF 2025-06+)"); print("="*100)
en_ents=C.energy_sleeve()
print(f"energy signals: {len(en_ents)} (fwd {sum(1 for e in en_ents if e['year']>=2025)})")
for ex in ['state_d','combo','lock']:
    rows,leaks,aud=C.run_cascade(en_ents, ex)
    print(f"\n### energy exit={ex} | leak audit: {leaks} leaks / {aud} LTF entries checked")
    OUT[f'energy_{ex}']=report_cascade(f"energy/{ex}", rows)

(HERE/'TW_MTF_CASCADE_RESULT.json').write_text(json.dumps(OUT, indent=1, default=str))
print("\nwrote TW_MTF_CASCADE_RESULT.json")
