"""KB6 (track: deepen_forward) — re-validate the VP EUidx POC-gravitation cell with a REAL
calendar TRAIN split, now that pre-2024 M1 (2023-04+) exists for GER40/UK100.

KB4_volume_profile shipped EUidx_pocgrav_2.0_vr1.2 (GER40+UK100) but flagged the honest caveat:
"this whole layer's TRAIN is the single 2024 calendar year (M1 depth). The walk-forward 55/45 is
the fair holdout; ... the bridge could export pre-2024 M1 for the core symbols in a later pass to
lengthen TRAIN." We did exactly that: exported 2023 M1 (GER40 2023-04-18+, UK100 2023-04-11+).

This script re-runs the EXACT VP_confluence.gen_signals cell on the now-deeper M1 and verdicts on:
  (1) the NEW real calendar split TRAIN(<=2024 = 2023-04..2024-12) -> FORWARD(2025-26), per-year, n;
  (2) invert control (edge real only if invert is opposite-signed);
  (3) the still-fair chronological WF 55/45 (for continuity with KB4).
Doctrine: gen_signals is imported UNCHANGED (same leak-free prior-day profile, same simulate
labeler); per-YEAR never average-as-verdict; distrust forward-only; delete nothing.
"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
import VP_confluence as vc

def _st(rs):
    if not rs: return {"n":0,"R":0.0,"win":0.0}
    n=len(rs); s=sum(rs); w=sum(1 for r in rs if r>0)
    return {"n":n,"R":round(s/n,4),"win":round(100*w/n,1)}

def collect(kind, syms, **kw):
    recs=[]
    for s in syms: recs+=vc.gen_signals(s,kind,**kw)   # (sym, year, R)
    return recs

def calendar_split(recs):
    tr=[r for (_,y,r) in recs if y<=2024]
    f25=[r for (_,y,r) in recs if y==2025]
    f26=[r for (_,y,r) in recs if y==2026]
    fwd=[r for (_,y,r) in recs if y>=2025]
    return _st(tr),_st(f25),_st(f26),_st(fwd)

def per_year(recs):
    by=defaultdict(list)
    for _,y,r in recs: by[y].append(r)
    return {y:_st(by[y]) for y in sorted(by)}

def wf_split(recs, frac=0.55):
    by=defaultdict(list)
    for r in recs: by[r[0]].append(r)
    tr=[]; oos=[]
    for s,lst in by.items():
        k=int(len(lst)*frac); tr+=lst[:k]; oos+=lst[k:]
    return _st([r for _,_,r in tr]), _st([r for _,_,r in oos])

def per_symbol(syms, kind, **kw):
    out={}
    for s in syms:
        rc=vc.gen_signals(s,kind,**kw)
        tr,f25,f26,fwd=calendar_split(rc)
        out[s]=dict(train=tr,fwd=fwd,by_year=per_year(rc),
                    both_pos=bool(tr["R"]>0 and fwd["R"]>0 and tr["n"]>=20))
    return out

def evaluate(name, kind, syms, **kw):
    recs=collect(kind,syms,**kw)
    tr,f25,f26,fwd=calendar_split(recs)
    pyr=per_year(recs)
    wftr,wfoos=wf_split(recs)
    inv=collect(kind,syms,invert=True,**kw)
    itr,_,_,ifwd=calendar_split(inv)
    iwftr,iwfoos=wf_split(inv)
    holds_cal = (tr["R"]>0 and fwd["R"]>0 and tr["n"]>=40 and ifwd["R"]<fwd["R"])
    return dict(name=name, train_le2024=tr, fwd25=f25, fwd26=f26, fwd=fwd,
                invert_fwd=ifwd, by_year={str(y):v for y,v in pyr.items()},
                wf_train=wftr, wf_oos=wfoos, invert_wf_oos=iwfoos,
                per_symbol=per_symbol(syms,kind,**kw),
                holds_calendar=holds_cal,
                holds_wf=bool(wftr["R"]>0 and wfoos["R"]>0 and wfoos["n"]>=40 and iwfoos["R"]<wfoos["R"]))

def main():
    EU=["GER40","UK100"]
    cells=[
        ("EUidx_pocgrav_2.0_vr1.2","poc_grav",EU,dict(far=2.0,vr_min=1.2)),  # the SHIPPED cell
        ("EUidx_pocgrav_2.0","poc_grav",EU,dict(far=2.0)),                    # ungated higher-freq
        ("GER40_pocgrav_2.0","poc_grav",["GER40"],dict(far=2.0)),
        ("UK100_pocgrav_2.0","poc_grav",["UK100"],dict(far=2.0)),
        ("EUidx_pocgrav_2.5_vr1.2","poc_grav",EU,dict(far=2.5,vr_min=1.2)),   # robustness
    ]
    res={}
    for nm,kind,syms,kw in cells:
        r=evaluate(nm,kind,syms,**kw); res[nm]=r
        print(f"\n== {nm} ==")
        print(f"  TRAIN<=2024 n={r['train_le2024']['n']:4d} R={r['train_le2024']['R']:+.4f} w={r['train_le2024']['win']}%"
              f" | FWD25 R={r['fwd25']['R']:+.4f}(n{r['fwd25']['n']}) FWD26 R={r['fwd26']['R']:+.4f}(n{r['fwd26']['n']})"
              f" | FWD R={r['fwd']['R']:+.4f}(n{r['fwd']['n']})")
        print(f"  invert FWD R={r['invert_fwd']['R']:+.4f}  | WF-TRAIN R={r['wf_train']['R']:+.4f}(n{r['wf_train']['n']}) WF-OOS R={r['wf_oos']['R']:+.4f}(n{r['wf_oos']['n']}) invWF-OOS {r['invert_wf_oos']['R']:+.4f}")
        print(f"  by_year: " + " ".join(f"{y}:{v['R']:+.3f}(n{v['n']})" for y,v in r['by_year'].items()))
        print(f"  per-sym: " + " | ".join(f"{s}:TR{v['train']['R']:+.3f}(n{v['train']['n']})/FWD{v['fwd']['R']:+.3f}(n{v['fwd']['n']}) bp={v['both_pos']}" for s,v in r['per_symbol'].items()))
        print(f"  HOLDS calendar(TR>0,FWD>0,nTR>=40,invFWD<FWD)={r['holds_calendar']}  HOLDS wf={r['holds_wf']}")
    p=os.path.join(HERE,"KB6_VP_EUIDX_REVAL_RESULT.json")
    json.dump(res, open(p,"w"), indent=1)
    print(f"\nwrote {p}")

if __name__=="__main__":
    main()
