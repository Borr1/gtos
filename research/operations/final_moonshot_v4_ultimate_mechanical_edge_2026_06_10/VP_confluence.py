"""
VP_confluence.py — CONFLUENCE mining for the volume-profile layer.
Track: VP. The raw single-pattern VP averages are negative (see VP_SETUP_MINE_RESULT.json) — exactly
the doctrine's point: averages are not verdicts; edge lives in CELLS + CONFLUENCE. Here we STACK the
profile state with independent, already-validated gates (vol_ratio, autocorr persistence, value-area
location) and per-class routing, then re-measure forward odds per cell with sample size.

Independent conditions stacked:
  (P) profile state    : VA-breakout / far-from-POC / void-touch (from volume_profile, leak-free prior day)
  (V) vol regime       : cs.vol_ratio(atrs,i)  (high-vol vs compressed)
  (A) momentum persist : cs.autocorr(B,i,60)   (trend persistence proxy)
  (S) class route      : energy / index / metals / fx (route the setup to where the auction works)

All entries H4, fills via geometry_lib.simulate (pessimistic), real cost. TRAIN=2024, FWD=2025-26
(M1 depth). Per-year + per-symbol + sample size always; invert control on each shipped cell.
"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict

HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE); sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import volume_profile as vp
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

BIN_FRAC=0.03
CLASSES={
 "energy":["USOIL_cash","UKOIL_cash"],
 "index":["GER40","JP225","NAS100","SPX500","UK100","US30_cash"],
 "metals":["XAUUSD","XAGUSD"],
 "fx":["AUDUSD","EURGBP","EURUSD","GBPUSD","NZDUSD","USDCAD","USDCHF"],
 "jpy":["AUDJPY","CHFJPY","EURJPY","GBPJPY","USDJPY"],
 "crypto":["BTCUSD","ETHUSD"],
}

def _st(rs):
    if not rs: return {"n":0,"R":0.0,"win":0.0}
    n=len(rs);s=sum(rs);w=sum(1 for r in rs if r>0)
    return {"n":n,"R":round(s/n,4),"win":round(100*w/n,1)}
def _split(recs):
    return _st([r for _,y,r in recs if y<=2024]), _st([r for _,y,r in recs if y>=2025])
def _py(recs):
    by=defaultdict(list)
    for _,y,r in recs: by[y].append(r)
    return {y:_st(by[y]) for y in sorted(by)}
def _pys(recs):  # per symbol split
    bt=defaultdict(list);bf=defaultdict(list)
    for s,y,r in recs:(bt if y<=2024 else bf)[s].append(r)
    return {s:{"train":_st(bt[s]),"fwd":_st(bf[s])} for s in sorted(set(list(bt)+list(bf)))}


def gen_signals(sym, kind, **kw):
    """Yield (year, R) plus track symbol. kind selects the confluence setup.
    Leak-free: prior-day profile + closed-bar features only."""
    T,B=w1.load(sym)
    if len(B)<200: return []
    cost=w1.cost_for(sym); n=len(B)
    atrs=[atr14(B,i) for i in range(n)]
    profs,days=vp.daily_profiles(sym,bin_atr_frac=BIN_FRAC)
    if not days: return []
    fday=days[0]
    invert=kw.get("invert",False)
    out=[]
    for i in range(101,n-1):
        a=atrs[i]
        if a<=0: continue
        t=T[i]
        if t.date()<=fday: continue
        dp=vp.prior_profile_at(profs,days,t)
        if dp is None: continue
        price=B[i].c
        st=vp.nearest_node_state(dp,price,a)
        if st is None: continue
        vr=cs.vol_ratio(atrs,i); ac=cs.autocorr(B,i,60)
        sig=None
        if kind=="va_fade":
            # VA breakout FADE, gated. Fade only when breakout is SHALLOW (likely failed auction)
            margin=kw.get("margin",0.10)
            if price>dp.vah+margin*a and price<=dp.vah+kw.get("maxext",1.2)*a:
                d=-1; edge=dp.vah
            elif price<dp.val-margin*a and price>=dp.val-kw.get("maxext",1.2)*a:
                d=1; edge=dp.val
            else: continue
            # vol gate: failed auctions need elevated vol (exhaustion); ac gate: low persistence (reversion)
            if vr<kw.get("vr_min",0.0): continue
            if vr>kw.get("vr_max",99): continue
            if ac is not None and kw.get("ac_max") is not None and ac>kw["ac_max"]: continue
            stop_dist=max(kw.get("stop",1.0)*a, abs(price-edge)+0.2*a)
            target_dist=kw.get("tgt",1.5)*stop_dist
            sig=(d,stop_dist,target_dist)
        elif kind=="poc_grav":
            far=kw.get("far",2.0)
            dpoc=st["d_poc_atr"]
            if abs(dpoc)<far or st["in_va"]: continue
            if vr<kw.get("vr_min",0.0): continue
            if vr>kw.get("vr_max",99): continue
            if ac is not None and kw.get("ac_max") is not None and ac>kw["ac_max"]: continue
            d=-1 if dpoc>0 else 1
            stop_dist=kw.get("stop",1.0)*a
            target_dist=abs(price-dp.poc)
            if target_dist<kw.get("min_rr",0.8)*stop_dist: continue
            if kw.get("cap_tgt"): target_dist=min(target_dist,kw["cap_tgt"]*stop_dist)
            sig=(d,stop_dist,target_dist)
        elif kind=="va_break_cont":
            # VA breakout CONTINUATION gated by high persistence + elevated vol (trend confluence)
            margin=kw.get("margin",0.15)
            if price>dp.vah+margin*a: d=1; edge=dp.vah
            elif price<dp.val-margin*a: d=-1; edge=dp.val
            else: continue
            if ac is None or ac<kw.get("ac_min",0.10): continue
            if vr<kw.get("vr_min",1.0): continue
            stop_dist=max(kw.get("stop",0.6)*a, abs(price-edge)+0.1*a)
            target_dist=kw.get("tgt",2.5)*stop_dist
            sig=(d,stop_dist,target_dist)
        if sig is None: continue
        d,sd,td=sig
        if invert: d=-d
        r=simulate(B,i,d,stop_dist=sd,target_dist=td,maxbars=kw.get("maxbars",60),cost=cost)
        out.append((sym,t.year,r))
    return out


def run(kind, syms, **kw):
    recs=[]
    for s in syms: recs+=gen_signals(s,kind,**kw)
    return recs

def show(name, recs):
    tr,fw=_split([(s,y,r) for s,y,r in recs])
    py=_py([(s,y,r) for s,y,r in recs])
    posf=sum(1 for y in py if y>=2025 and py[y]["R"]>0); nf=sum(1 for y in py if y>=2025)
    pyl=" ".join(f"{y}:{py[y]['R']:+.3f}(n{py[y]['n']})" for y in py)
    print(f"\n== {name} ==")
    print(f"  TRAIN<=24 n={tr['n']:4d} R={tr['R']:+.4f} w={tr['win']:.0f}% | FWD n={fw['n']:4d} R={fw['R']:+.4f} w={fw['win']:.0f}% | pos-fwd {posf}/{nf}")
    print(f"  per-year: {pyl}")
    return {"name":name,"train":tr,"fwd":fw,"per_year":{str(y):py[y] for y in py},
            "pos_fwd_years":posf,"total_fwd_years":nf}

def main():
    res={}
    # ---- direction 1: ENERGY value-area FADE, vol-gated (failed auctions on oil) ----
    print("################ ENERGY VA-FADE (gated) ################")
    grid=[
        ("energy_vafade_base",      dict(kind="va_fade",tgt=1.5)),
        ("energy_vafade_vr1.2",     dict(kind="va_fade",tgt=1.5,vr_min=1.2)),
        ("energy_vafade_vr1.4",     dict(kind="va_fade",tgt=1.5,vr_min=1.4)),
        ("energy_vafade_vr1.4_acmax0.05",dict(kind="va_fade",tgt=1.5,vr_min=1.4,ac_max=0.05)),
        ("energy_vafade_vr1.4_t2",  dict(kind="va_fade",tgt=2.0,vr_min=1.4)),
        ("energy_vafade_shallow",   dict(kind="va_fade",tgt=1.5,vr_min=1.2,maxext=0.7)),
    ]
    for nm,kw in grid:
        recs=run(kw.pop("kind"),CLASSES["energy"],kind="va_fade",**kw) if False else run("va_fade",CLASSES["energy"],**{k:v for k,v in kw.items() if k!="kind"})
        res[nm]=show(nm,recs)
    # ---- direction 2: INDEX POC gravitation, gated ----
    print("\n################ INDEX POC-GRAVITATION (gated) ################")
    grid2=[
        ("index_pocgrav_2.0",       dict(far=2.0)),
        ("index_pocgrav_2.0_capR2", dict(far=2.0,cap_tgt=2.0)),
        ("index_pocgrav_2.5",       dict(far=2.5)),
        ("index_pocgrav_2.0_acmax0",dict(far=2.0,ac_max=0.0)),
        ("index_pocgrav_2.0_vr1.2", dict(far=2.0,vr_min=1.2)),
    ]
    for nm,kw in grid2:
        recs=run("poc_grav",CLASSES["index"],**kw)
        res[nm]=show(nm,recs)
    # ---- direction 3: VA breakout CONTINUATION (trend confluence) per class ----
    print("\n################ VA-BREAKOUT CONTINUATION (ac+vr gated) ################")
    for cls in ["energy","index","metals","crypto","jpy","fx"]:
        recs=run("va_break_cont",CLASSES[cls],ac_min=0.10,vr_min=1.0,tgt=2.5)
        res[f"{cls}_vabreak_cont"]=show(f"{cls}_vabreak_cont",recs)

    # ---- invert controls on the best both-sided cells ----
    print("\n################ INVERT CONTROLS on best both-sided ################")
    best=[]
    for nm,r in res.items():
        if r["fwd"]["n"]>=40 and r["train"]["n"]>=20 and r["fwd"]["R"]>0 and r["train"]["R"]>0:
            best.append((nm,r["fwd"]["R"]))
    best.sort(key=lambda x:-x[1])
    ctrl={}
    persym={}
    for nm,_ in best[:6]:
        # reconstruct args -> rerun inverted + persym (re-derive from name maps)
        pass
    # rerun the named winners explicitly for invert + persym
    winners_args={
        "energy_vafade_vr1.4":      ("va_fade",CLASSES["energy"],dict(tgt=1.5,vr_min=1.4)),
        "energy_vafade_vr1.4_acmax0.05":("va_fade",CLASSES["energy"],dict(tgt=1.5,vr_min=1.4,ac_max=0.05)),
        "energy_vafade_vr1.2":      ("va_fade",CLASSES["energy"],dict(tgt=1.5,vr_min=1.2)),
        "index_pocgrav_2.0":        ("poc_grav",CLASSES["index"],dict(far=2.0)),
        "index_pocgrav_2.0_capR2":  ("poc_grav",CLASSES["index"],dict(far=2.0,cap_tgt=2.0)),
        "index_pocgrav_2.5":        ("poc_grav",CLASSES["index"],dict(far=2.5)),
    }
    for nm,(kind,syms,kw) in winners_args.items():
        if nm not in res: continue
        inv=[]
        for s in syms: inv+=gen_signals(s,kind,invert=True,**kw)
        ci=show("INV_"+nm,inv); ctrl["INV_"+nm]=ci
        # per-symbol
        full=[]
        for s in syms: full+=gen_signals(s,kind,**kw)
        persym[nm]=_pys(full)

    out={"confluence":res,"controls":ctrl,"per_symbol":persym,
         "meta":{"bin_frac":BIN_FRAC,"note":"M1 2024+ -> TRAIN=2024, FWD=2025-26; leak-free prior-day profile + cs gates."}}
    with open(HERE+"/VP_CONFLUENCE_RESULT.json","w") as f: json.dump(out,f,indent=1)
    print("\nWROTE VP_CONFLUENCE_RESULT.json")

if __name__=="__main__":
    main()
