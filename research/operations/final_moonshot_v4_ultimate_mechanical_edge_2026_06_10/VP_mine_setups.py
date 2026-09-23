"""
VP_mine_setups.py — mine forward odds of VOLUME-PROFILE setups on H4 entries.
Track: VP. Uses the leak-free volume_profile engine (prior-day profile only) + geometry_lib.simulate.

Hypotheses mined (each per-year, per-symbol, per-class, TRAIN<=2024 vs FORWARD>=2025, with n + controls):
  H1 REJECTION-AT-VOID   : price trades INTO a prior-day LVN/void -> reject AWAY from it (fade).
  H2 POC GRAVITATION     : price is FAR (>=th ATR) outside prior-day value -> revert toward POC.
  H3 VA-BREAKOUT CONT.   : H4 closes beyond prior-day VAH/VAL -> continuation in breakout direction.
  H3b VA-BREAKOUT FAIL   : same trigger -> FADE (price returns into value) -> the failure side.

Discipline: M1 only exists 2024+ so TRAIN=2024(one year), FORWARD=2025-26. Reported honestly.
All fills via simulate (pessimistic). Real cost w1.cost_for(sym). Negative control = invert side.
"""
from __future__ import annotations
import sys, os, json
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import volume_profile as vp
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

# Core M1-covered universe (2024+). Crypto BTC/ETH start later (handled by data availability).
UNIV = ["XAUUSD","XAGUSD","BTCUSD","ETHUSD","GER40","JP225","NAS100","SPX500","UK100","US30_cash",
        "UKOIL_cash","USOIL_cash","AUDJPY","CHFJPY","EURJPY","GBPJPY","USDJPY","AUDUSD","EURGBP",
        "EURUSD","GBPUSD","NZDUSD","USDCAD","USDCHF"]

BIN_FRAC = 0.03

def _stats(rs):
    if not rs: return {"n":0,"R":0.0,"win":0.0}
    n=len(rs); s=sum(rs); w=sum(1 for r in rs if r>0)
    return {"n":n,"R":round(s/n,4),"win":round(100*w/n,1)}

def _split(records):
    """records: (sym, year, cls, R)."""
    tr=[r for _,y,_,r in records if y<=2024]
    fw=[r for _,y,_,r in records if y>=2025]
    return _stats(tr),_stats(fw)

def _per_year(records):
    by=defaultdict(list)
    for _,y,_,r in records: by[y].append(r)
    return {y:_stats(by[y]) for y in sorted(by)}

def _per_class_fwd(records):
    by=defaultdict(list)
    for _,y,c,r in records:
        if y>=2025: by[c].append(r)
    return {c:_stats(by[c]) for c in sorted(by)}

def _per_sym_split(records):
    bt=defaultdict(list); bf=defaultdict(list)
    for s,y,_,r in records:
        (bt if y<=2024 else bf)[s].append(r)
    out={}
    for s in sorted(set(list(bt)+list(bf))):
        out[s]={"train":_stats(bt[s]),"fwd":_stats(bf[s])}
    return out


def mine(sym, setup, **kw):
    """Return list of (sym, year, cls, R) for one setup on one symbol's H4 entries."""
    T,B = w1.load(sym)
    if len(B)<200: return []
    cls = ASSET_CLASS_BY_SYMBOL.get(sym)
    cost = w1.cost_for(sym)
    n=len(B)
    atrs=[atr14(B,i) for i in range(n)]
    profs, days = vp.daily_profiles(sym, bin_atr_frac=BIN_FRAC)
    if not days: return []
    # only evaluate H4 bars on/after first day a prior profile exists (2024+)
    first_day = days[0]
    out=[]
    invert = kw.get("invert", False)
    for i in range(60, n-1):
        a=atrs[i]
        if a<=0: continue
        t=T[i]
        if t.date() <= first_day:  # need a PRIOR completed day's profile
            continue
        dp = vp.prior_profile_at(profs, days, t)
        if dp is None: continue
        price = B[i].c
        st = vp.nearest_node_state(dp, price, a)
        if st is None: continue
        sig = setup(B, i, a, dp, st, price, kw)
        if sig is None: continue
        d, stop_dist, target_dist, trail_gap = sig
        if invert: d = -d
        if trail_gap is not None:
            r = simulate(B, i, d, stop_dist=stop_dist, trail_arm=0.5*stop_dist,
                         trail_gap=trail_gap, maxbars=kw.get("maxbars",60), cost=cost)
        else:
            r = simulate(B, i, d, stop_dist=stop_dist, target_dist=target_dist,
                         maxbars=kw.get("maxbars",60), cost=cost)
        out.append((sym, t.year, cls, r))
    return out


# ---------------- setup signal functions ----------------
# Each returns (direction, stop_dist, target_dist, trail_gap) or None.

def setup_void_reject(B,i,a,dp,st,price,kw):
    """H1: entry bar's RANGE penetrates a prior-day LVN/void, and CLOSE is back on the
    value-side of it -> fade back toward value (reject the void). Tight stop beyond the void."""
    if not dp.lvn: return None
    th_touch = kw.get("touch",0.20)   # how close (ATR) the bar must come to the void
    # nearest void
    void = min(dp.lvn, key=lambda p: abs(p-price))
    dist = abs(void-price)/a
    if dist > th_touch: return None
    # require the bar to have actually traded INTO the void (h/l straddles it)
    if not (B[i].l <= void <= B[i].h): return None
    # reject AWAY from the void back toward POC (value magnet)
    d = 1 if dp.poc > void else -1
    # but only if close is already turning that way (close on the POC-side of the void)
    if d>0 and price < void: return None
    if d<0 and price > void: return None
    stop_dist = max(kw.get("stop",0.6)*a, abs(price-void)+0.2*a)
    target_dist = kw.get("tgt",2.0)*stop_dist
    return (d, stop_dist, target_dist, None)

def setup_poc_gravitate(B,i,a,dp,st,price,kw):
    """H2: price is FAR outside value (|d_poc|>=th ATR, and outside [VAL,VAH]) -> fade toward POC.
    Target = the POC (measured), stop = beyond current extreme."""
    th = kw.get("far",1.0)
    dpoc = st["d_poc_atr"]
    if abs(dpoc) < th: return None
    if st["in_va"]: return None
    d = -1 if dpoc>0 else 1   # above POC -> short toward POC; below -> long
    stop_dist = kw.get("stop",1.0)*a
    target_dist = abs(price-dp.poc)
    if target_dist < kw.get("min_rr",0.8)*stop_dist: return None
    if kw.get("cap_tgt"):  # optionally cap target at fixed R
        target_dist = min(target_dist, kw.get("cap_tgt")*stop_dist)
    return (d, stop_dist, target_dist, None)

def setup_va_breakout(B,i,a,dp,st,price,kw):
    """H3: H4 CLOSE beyond prior-day VAH/VAL by >= margin ATR -> continuation in breakout dir.
    Stop back inside value (at the broken edge), target fixed R."""
    margin = kw.get("margin",0.10)
    if price > dp.vah + margin*a:
        d=1; edge=dp.vah
    elif price < dp.val - margin*a:
        d=-1; edge=dp.val
    else:
        return None
    stop_dist = max(kw.get("min_stop",0.5)*a, abs(price-edge)+kw.get("buf",0.1)*a)
    if kw.get("trail"):
        return (d, stop_dist, None, kw.get("trail_gap",0.8)*a)
    target_dist = kw.get("tgt",2.0)*stop_dist
    return (d, stop_dist, target_dist, None)

def setup_va_breakout_fade(B,i,a,dp,st,price,kw):
    """H3b: same VA-break trigger but FADE it (mean-revert back into value) — tests whether
    breakouts FAIL more than they continue (the auction 'failed-auction' edge)."""
    sig = setup_va_breakout(B,i,a,dp,st,price,dict(kw, trail=False))
    if sig is None: return None
    d,sd,td,_ = sig
    return (-d, sd, td, None)


SETUPS = {
    "H1_void_reject":      (setup_void_reject,   dict(touch=0.20, stop=0.6, tgt=2.0)),
    "H1_void_reject_t1.5": (setup_void_reject,   dict(touch=0.20, stop=0.6, tgt=1.5)),
    "H1_void_reject_t3":   (setup_void_reject,   dict(touch=0.20, stop=0.6, tgt=3.0)),
    "H2_poc_grav_1.0":     (setup_poc_gravitate, dict(far=1.0, stop=1.0)),
    "H2_poc_grav_1.5":     (setup_poc_gravitate, dict(far=1.5, stop=1.0)),
    "H2_poc_grav_2.0":     (setup_poc_gravitate, dict(far=2.0, stop=1.0)),
    "H2_poc_grav_capR2":   (setup_poc_gravitate, dict(far=1.5, stop=1.0, cap_tgt=2.0)),
    "H3_va_break_2R":      (setup_va_breakout,   dict(margin=0.10, tgt=2.0)),
    "H3_va_break_1R":      (setup_va_breakout,   dict(margin=0.10, tgt=1.0)),
    "H3_va_break_3R":      (setup_va_breakout,   dict(margin=0.10, tgt=3.0)),
    "H3_va_break_trail":   (setup_va_breakout,   dict(margin=0.10, trail=True, trail_gap=0.8)),
    "H3b_va_break_fade":   (setup_va_breakout_fade, dict(margin=0.10, tgt=2.0)),
}

def run_setup(name, syms=UNIV):
    fn, kw = SETUPS[name]
    recs=[]
    for s in syms:
        recs += mine(s, fn, **kw)
    return recs

def summarize(name, recs):
    tr,fw = _split(recs)
    py = _per_year(recs)
    pc = _per_class_fwd(recs)
    pos_yrs = sum(1 for y in py if py[y]["R"]>0)
    pos_fwd = sum(1 for y in py if y>=2025 and py[y]["R"]>0)
    nfwd_yrs = sum(1 for y in py if y>=2025)
    return {
        "name":name, "train":tr, "fwd":fw,
        "per_year":{str(y):py[y] for y in py},
        "per_class_fwd":pc,
        "pos_years":pos_yrs, "total_years":len(py),
        "pos_fwd_years":pos_fwd, "total_fwd_years":nfwd_yrs,
    }

def main():
    results={}
    raw={}
    for name in SETUPS:
        recs = run_setup(name)
        raw[name]=recs
        s = summarize(name, recs)
        results[name]=s
        tr,fw=s["train"],s["fwd"]
        py=s["per_year"]
        pyl=" ".join(f"{y}:{py[y]['R']:+.3f}(n{py[y]['n']})" for y in py)
        print(f"\n== {name} ==")
        print(f"  TRAIN<=24 n={tr['n']:5d} R={tr['R']:+.4f} w={tr['win']:.0f}% | FWD>=25 n={fw['n']:5d} R={fw['R']:+.4f} w={fw['win']:.0f}%")
        print(f"  per-year: {pyl}")
        print(f"  pos-fwd-years {s['pos_fwd_years']}/{s['total_fwd_years']}")

    # invert controls on the strongest forward setups (by FWD R with n_fwd>=40)
    print("\n#### INVERT CONTROLS (strongest fwd, n_fwd>=40) ####")
    cand=[(n,results[n]["fwd"]["R"],results[n]["fwd"]["n"]) for n in results if results[n]["fwd"]["n"]>=40]
    cand.sort(key=lambda x:-x[1])
    ctrl={}
    for n,_,_ in cand[:4]:
        fn,kw=SETUPS[n]
        inv=[]
        for s in UNIV: inv+=mine(s, fn, **dict(kw, invert=True))
        ci=summarize("INV_"+n, inv)
        ctrl["INV_"+n]=ci
        print(f"  INV_{n}: FWD n={ci['fwd']['n']} R={ci['fwd']['R']:+.4f}  (orig FWD R={results[n]['fwd']['R']:+.4f})")

    out={"setups":results,"controls":ctrl,
         "meta":{"bin_frac":BIN_FRAC,"univ":UNIV,
                 "note":"M1 2024+ -> TRAIN=2024 only, FORWARD=2025-26. Prior-day profile, leak-free."}}
    with open(HERE+"/VP_SETUP_MINE_RESULT.json","w") as f:
        json.dump(out,f,indent=1)
    # also persist per-symbol splits for the strongest 4 for the KB writeup
    persym={}
    for n,_,_ in cand[:6]:
        persym[n]=_per_sym_split(raw[n])
    with open(HERE+"/VP_SETUP_PERSYM.json","w") as f:
        json.dump(persym,f,indent=1)
    print("\nWROTE VP_SETUP_MINE_RESULT.json + VP_SETUP_PERSYM.json")

if __name__=="__main__":
    main()
