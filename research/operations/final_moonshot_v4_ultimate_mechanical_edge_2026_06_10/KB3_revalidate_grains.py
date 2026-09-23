"""KB3 (deepen_val2) — re-validate AGRI grains now that WHEAT_c/SOYBEAN_c H4 exist
(2023-2024 TRAIN + 2025-26 FORWARD, CORN-style split). Applies the LOCKED agri gates verbatim
(agri_gate_high ac60>=0.10 ; agri_gate_breadth not-Dec-Feb) via the existing energy_agri_sleeve
machinery. No re-derivation. Reports TRAIN<=2024 / FWD2025 / FWD2026 / per-symbol, winsorized,
real cost, leak-free (geometry simulate/exit_state_d look-forward-only on decided labels)."""
import sys, json, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2])); sys.path.insert(0,str(HERE))
import energy_agri_sleeve as ea

# extend AGRI universe with the newly-available grains (delete nothing, additive)
ea.AGRI = ['CORN_c','COTTON_c','WHEAT_c','SOYBEAN_c']
# grains with a real train slice are forward-validatable (2023-24 train); COTTON stays fwd-only
ea.FORWARD_VALIDATABLE = ea.FORWARD_VALIDATABLE | {'WHEAT_c','SOYBEAN_c'}

def stat(rs,k='R'):
    if not rs: return (0,0.0,0.0)
    n=len(rs); m=sum(r[k] for r in rs)/n; w=sum(1 for r in rs if r[k]>0)/n*100
    return n,round(m,4),round(w,1)
def split(rs):
    tr=[r for r in rs if r['year']<=2024]; f25=[r for r in rs if r['year']==2025]; f26=[r for r in rs if r['year']==2026]
    fwd=[r for r in rs if r['year']>=2025]
    return dict(TRAIN=stat(tr),FWD2025=stat(f25),FWD2026=stat(f26),FWD2526=stat(fwd))

rows=ea.build_candidates()
agri=[r for r in rows if r['grp']=='agri']
print(f"AGRI candidates (all 4 syms): n={len(agri)}")
for s in ['CORN_c','COTTON_c','WHEAT_c','SOYBEAN_c']:
    ss=[r for r in agri if r['sym']==s]
    yrs=sorted(set(r['year'] for r in ss))
    print(f"  {s}: n={len(ss)} years={yrs}")

sleeve=ea.final_sleeve(rows)
out={"agri_candidates":len(agri)}
print("\n=== LOCKED AGRI GATES, re-validated with grains (TRAIN<=2024 / FWD) ===")
for tag in ['agri_persistence','agri_seasonal']:
    rs=[r for r in sleeve if r.get('tag')==tag]
    sp=split(rs)
    print(f"\n[{tag}] total n={len(rs)}")
    for k,v in sp.items(): print(f"    {k:8s}: n={v[0]} EV={v[1]:+.3f}R win={v[2]:.0f}%")
    # per-symbol within tag
    bysym=collections.defaultdict(list)
    for r in rs: bysym[r['sym']].append(r)
    for s,rr in sorted(bysym.items()):
        sp2=split(rr)
        print(f"      {s:11s} TRAIN {sp2['TRAIN']} | FWD2526 {sp2['FWD2526']}")
    out[tag]={k:list(v) for k,v in sp.items()}

# grains-only (WHEAT+SOYBEAN) high-conf pocket — the conversion question
gr=[r for r in sleeve if r['sym'] in ('WHEAT_c','SOYBEAN_c') and r['tag']=='agri_persistence']
out['grains_persistence']={k:list(v) for k,v in split(gr).items()}
print("\n=== GRAINS-ONLY (WHEAT+SOYBEAN) persistence pocket (the conversion target) ===")
for k,v in split(gr).items(): print(f"    {k:8s}: n={v[0]} EV={v[1]:+.3f}R win={v[2]:.0f}%")
# grains seasonal breadth too
grb=[r for r in sleeve if r['sym'] in ('WHEAT_c','SOYBEAN_c') and r['tag']=='agri_seasonal']
out['grains_seasonal']={k:list(v) for k,v in split(grb).items()}
print("\n=== GRAINS-ONLY seasonal breadth ===")
for k,v in split(grb).items(): print(f"    {k:8s}: n={v[0]} EV={v[1]:+.3f}R win={v[2]:.0f}%")

(HERE/'KB3_GRAINS_REVAL_RESULT.json').write_text(json.dumps(out,indent=2))
print("\nwrote KB3_GRAINS_REVAL_RESULT.json")
