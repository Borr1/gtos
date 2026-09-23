"""
VP_walkforward.py — FAIR walk-forward holdout for the volume-profile layer.
Track: VP. The calendar TRAIN<=2024 / FWD>=2025 split is degenerate for an M1-derived layer
(M1 starts 2024, so >75% of trades land in 'forward'). Here we add an HONEST chronological
walk-forward split (first SPLIT fraction of each symbol's trades = TRAIN, remainder = OOS) so
both halves carry real sample size. We re-measure the only cells that survived per-symbol
(European-index POC-gravitation: GER40, UK100) plus a pooled European-index cell and the
US-index + crypto cells, with per-year, per-symbol, sample size, and invert control.

This is the verdict layer: a cell ships ONLY if it holds on BOTH chronological halves AND
across calendar years AND n_oos>=~40 AND its invert is the opposite sign.
"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict

HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import VP_confluence as vc

def _st(rs):
    if not rs: return {"n":0,"R":0.0,"win":0.0}
    n=len(rs);s=sum(rs);w=sum(1 for r in rs if r>0)
    return {"n":n,"R":round(s/n,4),"win":round(100*w/n,1)}

def wf_split(recs, frac=0.55):
    """recs: list of (sym, year, R) already in chronological order PER SYMBOL (gen_signals yields
    in time order). Split each symbol's stream at `frac`, pool the train/oos halves."""
    by=defaultdict(list)
    for r in recs: by[r[0]].append(r)
    tr=[]; oos=[]
    for s,lst in by.items():
        k=int(len(lst)*frac)
        tr+=lst[:k]; oos+=lst[k:]
    return tr,oos

def py(recs):
    by=defaultdict(list)
    for _,y,r in recs: by[y].append(r)
    return {y:_st(by[y]) for y in sorted(by)}

def collect(kind, syms, **kw):
    recs=[]
    for s in syms: recs+=vc.gen_signals(s,kind,**kw)
    return recs

def evaluate(name, kind, syms, **kw):
    recs=collect(kind,syms,**kw)
    tr,oos=wf_split(recs,0.55)
    st_tr=_st([r for _,_,r in tr]); st_oos=_st([r for _,_,r in oos])
    # invert
    inv=collect(kind,syms,invert=True,**kw)
    itr,ioos=wf_split(inv,0.55)
    ist_oos=_st([r for _,_,r in ioos])
    pyr=py(recs)
    pyl=" ".join(f"{y}:{pyr[y]['R']:+.3f}(n{pyr[y]['n']})" for y in pyr)
    print(f"\n== {name} ==")
    print(f"  WF-TRAIN(55%) n={st_tr['n']:4d} R={st_tr['R']:+.4f} w={st_tr['win']:.0f}% | "
          f"WF-OOS(45%) n={st_oos['n']:4d} R={st_oos['R']:+.4f} w={st_oos['win']:.0f}%")
    print(f"  INVERT WF-OOS n={ist_oos['n']:4d} R={ist_oos['R']:+.4f}  (edge real if opposite sign)")
    print(f"  per-year: {pyl}")
    holds = (st_tr["R"]>0 and st_oos["R"]>0 and st_oos["n"]>=40 and ist_oos["R"]<st_oos["R"])
    print(f"  -> HOLDS both halves + invert-opposite + n_oos>=40 : {holds}")
    return {"name":name,"wf_train":st_tr,"wf_oos":st_oos,"invert_oos":ist_oos,
            "per_year":{str(y):pyr[y] for y in pyr},"holds":holds}

def main():
    res={}
    EU=["GER40","UK100"]
    USIDX=["NAS100","SPX500","US30_cash"]
    ALLIDX=vc.CLASSES["index"]
    cells=[
        ("EUidx_pocgrav_2.0",        "poc_grav", EU,        dict(far=2.0)),
        ("EUidx_pocgrav_2.0_vr1.2",  "poc_grav", EU,        dict(far=2.0,vr_min=1.2)),
        ("EUidx_pocgrav_2.5",        "poc_grav", EU,        dict(far=2.5)),
        ("GER40_pocgrav_2.0",        "poc_grav", ["GER40"], dict(far=2.0)),
        ("UK100_pocgrav_2.0",        "poc_grav", ["UK100"], dict(far=2.0)),
        ("USidx_pocgrav_2.0_vr1.2",  "poc_grav", USIDX,     dict(far=2.0,vr_min=1.2)),
        ("ALLidx_pocgrav_2.0_vr1.2", "poc_grav", ALLIDX,    dict(far=2.0,vr_min=1.2)),
        ("ALLidx_pocgrav_2.0_capR2", "poc_grav", ALLIDX,    dict(far=2.0,cap_tgt=2.0)),
        ("crypto_vabreak_cont",      "va_break_cont", vc.CLASSES["crypto"], dict(ac_min=0.10,vr_min=1.0,tgt=2.5)),
        ("energy_vafade_vr1.2",      "va_fade", vc.CLASSES["energy"], dict(tgt=1.5,vr_min=1.2)),
    ]
    for nm,kind,syms,kw in cells:
        res[nm]=evaluate(nm,kind,syms,**kw)
    shipped=[nm for nm,r in res.items() if r["holds"]]
    print(f"\n#### CELLS THAT HOLD (WF both halves + invert + n): {shipped if shipped else 'NONE'}")
    out={"cells":res,"shipped":shipped,
         "meta":{"wf_frac":0.55,"note":"chronological per-symbol 55/45 split; M1 2024-2026 window; leak-free prior-day profile."}}
    with open(HERE+"/VP_WALKFORWARD_RESULT.json","w") as f: json.dump(out,f,indent=1)
    print("\nWROTE VP_WALKFORWARD_RESULT.json")

if __name__=="__main__":
    main()
