"""KB3 (deepen_val2) — convert the H1->M15 cascade better-fill lift on ENERGY from FORWARD-ONLY
to TRAIN-VALIDATED, now that USOIL/UKOIL deep H1+M15 (2020-12+) is exported.

Reuses the EXACT cascade engine (TW_mtf_cascade_transfer.run_cascade) and the locked energy entry
builder (energy_sleeve()). The ONLY change: repoint USOIL/UKOIL/NATGAS LTF paths to the new deep
export so the better-fill mechanic can be measured on TRAIN-year signals (2021-2024), not just fwd.

Leak-free: cascade engine enforces LTF entry >= H4 signal close instant (first_ltf_index_after +
per-bar leak audit). Winsorized in EXEC sim. Real cost scaled by stop tightness. No re-derivation.
"""
import sys, json, collections
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(HERE))
import multitf_lib as m
import TW_mtf_cascade_transfer as tw

DATA=str(ROOT)+"/data/mt5_research_exports"
DEEP=DATA+"/bridge_ftmo_energy_h1m15_backfill_2020_2026"
FWD_H1=DATA+"/bridge_ftmo_htf_20250601_20260610"
FWD_M15=DATA+"/bridge_ftmo_m15_20250601_20260610"
FWD_EXT_H1=DATA+"/bridge_ftmo_ext_htf_20250601_20260611"
FWD_EXT_M15=DATA+"/bridge_ftmo_ext_m15_20250601_20260611"

# REPOINT energy LTF to DEEP export (union deep first, then any forward dir for the tail overlap).
# Deep export already runs to 2026-06-12 so it is a strict superset; union is safe (dedupe by ts).
m.LTF_PATHS.update({
    ("USOIL_cash","H1"):  [DEEP+"/USOIL_cash_H1.csv"],
    ("USOIL_cash","M15"): [DEEP+"/USOIL_cash_M15.csv"],
    ("UKOIL_cash","H1"):  [DEEP+"/UKOIL_cash_H1.csv"],
    ("UKOIL_cash","M15"): [DEEP+"/UKOIL_cash_M15.csv"],
    ("NATGAS_cash","H1"):  [DEEP+"/NATGAS_cash_H1.csv"],
    ("NATGAS_cash","M15"): [DEEP+"/NATGAS_cash_M15.csv"],
})
m._LTF_CACHE.clear()

def stat(rs,k):
    if not rs: return (0,0.0,0.0)
    n=len(rs); mm=sum(r[k] for r in rs)/n; w=sum(1 for r in rs if r[k]>0)/n*100
    return n,round(mm,4),round(w,1)
def split(rs,k):
    tr=[r for r in rs if r['year']<=2024]; f25=[r for r in rs if r['year']==2025]; f26=[r for r in rs if r['year']==2026]
    fwd=[r for r in rs if r['year']>=2025]
    return dict(TRAIN=stat(tr,k),FWD2025=stat(f25,k),FWD2026=stat(f26,k),FWD2526=stat(fwd,k))
def paired(rs):
    """paired casc-base, TRAIN and FWD, with t-stat."""
    import statistics
    def t(sub):
        d=[r['casc_R']-r['base_R'] for r in sub]
        if len(d)<2: return (len(d), round(sum(d)/len(d),4) if d else 0.0, 0.0)
        mn=sum(d)/len(d); sd=statistics.pstdev(d)
        tt=mn/(sd/ (len(d)**0.5)) if sd>0 else 0.0
        return (len(d), round(mn,4), round(tt,2))
    return dict(TRAIN=t([r for r in rs if r['year']<=2024]), FWD=t([r for r in rs if r['year']>=2025]))

ents=tw.energy_sleeve()
print(f"energy entries (locked A/B gate): n={len(ents)}")
bysym=collections.Counter(e['sym'] for e in ents)
print("  by sym:",dict(bysym))

rows,leaks,audit=tw.run_cascade(ents,'state_d')
print(f"cascade rows={len(rows)} leak_flags={leaks} ltf_audited={audit}")
srcmix=collections.Counter(r['src'] for r in rows)
# src mix split by train/fwd
tr_mix=collections.Counter(r['src'] for r in rows if r['year']<=2024)
print(f"fill src mix ALL: {dict(srcmix)}  |  TRAIN-only: {dict(tr_mix)}")

out={"n":len(rows),"leaks":leaks,"src_mix_all":dict(srcmix),"src_mix_train":dict(tr_mix)}
print("\n=== ENERGY cascade: BASE (H4 STATE_D) vs CASCADE (H1->M15 better-fill) ===")
for label,k in [("BASE_H4","base_R"),("CASCADE","casc_R")]:
    sp=split(rows,k)
    print(f"\n[{label}]")
    for kk,v in sp.items(): print(f"    {kk:8s}: n={v[0]} EV={v[1]:+.3f}R win={v[2]:.0f}%")
    out[label]={kk:list(v) for kk,v in sp.items()}

pr=paired(rows)
print("\n=== PAIRED cascade-base (the conversion proof) ===")
for k,v in pr.items(): print(f"    {k:6s}: n={v[0]} mean_lift={v[1]:+.4f}R t={v[2]}")
out["paired"]=pr

# better-filled rows only (where LTF actually improved the fill) — TRAIN split
better=[r for r in rows if r['src'] in ('h1','m15')]
print(f"\n=== BETTER-FILLED rows only (src=h1/m15): n={len(better)} ===")
for k in ['base_R','casc_R']:
    sp=split(better,k)
    print(f"  [{ 'BASE' if k=='base_R' else 'CASC'}] TRAIN {sp['TRAIN']} | FWD2526 {sp['FWD2526']}")
out["better_filled_n"]=len(better)
out["better_filled_TRAIN_base"]=list(split(better,'base_R')['TRAIN'])
out["better_filled_TRAIN_casc"]=list(split(better,'casc_R')['TRAIN'])

# per-symbol cascade lift (forward-validatable symbols), TRAIN + FWD
print("\n=== PER-SYMBOL cascade (base->casc), TRAIN | FWD2526 ===")
persym={}
bysymrows=collections.defaultdict(list)
for r in rows: bysymrows[r['sym']].append(r)
for s,rr in sorted(bysymrows.items()):
    bt=split(rr,'base_R'); ct=split(rr,'casc_R')
    print(f"  {s:12s} TRAIN base{bt['TRAIN'][1]:+.3f}->casc{ct['TRAIN'][1]:+.3f}(n{bt['TRAIN'][0]}) | "
          f"FWD base{bt['FWD2526'][1]:+.3f}->casc{ct['FWD2526'][1]:+.3f}(n{bt['FWD2526'][0]})")
    persym[s]={"TRAIN_base":bt['TRAIN'][1],"TRAIN_casc":ct['TRAIN'][1],"TRAIN_n":bt['TRAIN'][0],
               "FWD_base":bt['FWD2526'][1],"FWD_casc":ct['FWD2526'][1],"FWD_n":bt['FWD2526'][0]}
out["per_symbol"]=persym

(HERE/'KB3_ENERGY_CASCADE_REVAL_RESULT.json').write_text(json.dumps(out,indent=2))
# write the ledger
with open(HERE/'KB3_ENERGY_CASCADE_LEDGER.jsonl','w') as f:
    for r in rows: f.write(json.dumps(r)+"\n")
print("\nwrote KB3_ENERGY_CASCADE_REVAL_RESULT.json + KB3_ENERGY_CASCADE_LEDGER.jsonl")
