"""KB3 (deepen_val2) — partial-convert the crypto cascade lift toward TRAIN now that BTC/DASH deep
H1+M15 (2024-08+) is exported, covering the 8 TRAIN(<=2024) crypto signals (2024-09..2024-12).
Reuses the exact cascade engine + locked crypto entries + native target4 exit. Leak-audited."""
import sys, json, collections, statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(HERE))
import multitf_lib as m
import TW_mtf_cascade_transfer as tw
DATA=str(ROOT)+"/data/mt5_research_exports"
DEEP=DATA+"/bridge_ftmo_crypto_h1m15_backfill_2024_2026"
m.LTF_PATHS.update({
    ("BTCUSD","H1"):[DEEP+"/BTCUSD_H1.csv"], ("BTCUSD","M15"):[DEEP+"/BTCUSD_M15.csv"],
    ("DASHUSD","H1"):[DEEP+"/DASHUSD_H1.csv"], ("DASHUSD","M15"):[DEEP+"/DASHUSD_M15.csv"],
})
m._LTF_CACHE.clear()
def stat(rs,k):
    if not rs: return (0,0.0,0.0)
    n=len(rs); mm=sum(r[k] for r in rs)/n; w=sum(1 for r in rs if r[k]>0)/n*100
    return n,round(mm,4),round(w,1)
def split(rs,k):
    return dict(TRAIN=stat([r for r in rs if r['year']<=2024],k),
                FWD2025=stat([r for r in rs if r['year']==2025],k),
                FWD2026=stat([r for r in rs if r['year']==2026],k),
                FWD2526=stat([r for r in rs if r['year']>=2025],k))
ents=tw.crypto_sleeve()
rows,leaks,audit=tw.run_cascade(ents,'target4')
srcmix=collections.Counter(r['src'] for r in rows)
tr_mix=collections.Counter(r['src'] for r in rows if r['year']<=2024)
print(f"crypto cascade rows={len(rows)} leaks={leaks} audited={audit}")
print(f"src mix ALL {dict(srcmix)} | TRAIN {dict(tr_mix)}")
out={"n":len(rows),"leaks":leaks,"src_mix_all":dict(srcmix),"src_mix_train":dict(tr_mix)}
for label,k in [("BASE_H4","base_R"),("CASCADE","casc_R")]:
    sp=split(rows,k); print(f"\n[{label}]")
    for kk,v in sp.items(): print(f"   {kk:8s}: n={v[0]} EV={v[1]:+.3f}R win={v[2]:.0f}%")
    out[label]={kk:list(v) for kk,v in sp.items()}
def t(sub):
    d=[r['casc_R']-r['base_R'] for r in sub]
    if len(d)<2: return (len(d), round(sum(d)/len(d),4) if d else 0.0, 0.0)
    mn=sum(d)/len(d); sd=statistics.pstdev(d)
    return (len(d), round(mn,4), round(mn/(sd/len(d)**0.5),2) if sd>0 else 0.0)
out["paired"]={"TRAIN":t([r for r in rows if r['year']<=2024]),"FWD":t([r for r in rows if r['year']>=2025])}
print("\nPAIRED cascade-base:")
for kk,v in out["paired"].items(): print(f"   {kk}: n={v[0]} lift={v[1]:+.4f}R t={v[2]}")
better=[r for r in rows if r['src'] in ('h1','m15')]
out["better_filled_TRAIN_base"]=list(split(better,'base_R')['TRAIN'])
out["better_filled_TRAIN_casc"]=list(split(better,'casc_R')['TRAIN'])
print(f"\nBETTER-FILLED TRAIN: base {split(better,'base_R')['TRAIN']} -> casc {split(better,'casc_R')['TRAIN']}")
(HERE/'KB3_CRYPTO_CASCADE_REVAL_RESULT.json').write_text(json.dumps(out,indent=2))
print("\nwrote KB3_CRYPTO_CASCADE_REVAL_RESULT.json")
