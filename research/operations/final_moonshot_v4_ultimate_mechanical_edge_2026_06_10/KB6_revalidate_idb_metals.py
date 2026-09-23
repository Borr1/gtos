"""KB6 (track: deepen_forward) — re-validate the IDB metals FVG-retest sleeve on DEEP H1.

The IDB layer (KB3_intraday_breadth) validated metals_intraday_fvg on a WITHIN-WINDOW split
(TRAIN=2025H2, FWD=2026H1) because H1 only existed 2025-06+. The broker actually serves
XAU/XAG H1 back to 2014-01 (probed) and XAU/XAG EUR/AUD back to 2021. We exported the deep H1
(bridge_ftmo_metals_h1_backfill_2014_2025) and now run the EXACT fvg_retest_signals entry on the
unioned deep stream with a REAL TRAIN(<=2024) -> FORWARD(2025-26) holdout + per-year + n.

Doctrine: geometry_lib.simulate is the only labeler; features from closed bars index<=i; real
w1.cost_for; winsorize netR [-1.3,+5]; per-YEAR never average-as-verdict; distrust forward-only;
delete nothing. The entry function is IMPORTED unchanged from IDB so the harness is identical.
"""
from __future__ import annotations
import sys, os, csv, json, statistics
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import Bar, atr14
import wave1_structure_setups_ict as w1
import IDB_intraday_breadth as idb  # reuse the EXACT validated entry

DATA = str(ROOT) + "/data/mt5_research_exports"
DEEP = DATA + "/bridge_ftmo_metals_h1_backfill_2014_2025"   # new: 2014..2025-05
H1A  = DATA + "/bridge_ftmo_htf_20250601_20260610"          # existing 2025-06+
H1B  = DATA + "/bridge_ftmo_ext_htf_20250601_20260611"

METALS = ['XAUUSD','XAGUSD','XAUEUR','XAGEUR','XAUAUD','XAGAUD']

def wins(r): return max(-1.3, min(5.0, r))

def load_deep_h1(sym):
    """Union deep backfill (2014..2025-05) + existing 2025-06+ H1, deduped, ascending."""
    merged = {}
    for d in (DEEP, H1A, H1B):
        p = os.path.join(d, f"{sym}_H1.csv")
        if not os.path.exists(p): continue
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                    merged[t] = Bar(float(row['open']),float(row['high']),float(row['low']),
                                    float(row['close']),float(row.get('volume',0) or 0))
                except Exception:
                    continue
    items = sorted(merged.items(), key=lambda kv: kv[0])
    return [k for k,_ in items], [v for _,v in items]

def superset_check(sym):
    """Verify the deep export is a strict superset over the overlap with existing 2025-06+ H1."""
    # existing
    ex = {}
    for d in (H1A, H1B):
        p = os.path.join(d, f"{sym}_H1.csv")
        if not os.path.exists(p): continue
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                    ex[t] = (round(float(row['open']),5),round(float(row['high']),5),
                             round(float(row['low']),5),round(float(row['close']),5))
                except Exception: continue
    dp = {}
    p = os.path.join(DEEP, f"{sym}_H1.csv")
    if os.path.exists(p):
        with open(p) as f:
            for row in csv.DictReader(f):
                try:
                    t = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
                    dp[t] = (round(float(row['open']),5),round(float(row['high']),5),
                             round(float(row['low']),5),round(float(row['close']),5))
                except Exception: continue
    # overlap timestamps present in both (deep ends 2025-05, existing starts 2025-06; tiny overlap)
    over = set(ex) & set(dp)
    mism = sum(1 for t in over if ex[t]!=dp[t])
    return dict(deep_first=min(dp).isoformat() if dp else None,
                deep_last=max(dp).isoformat() if dp else None, deep_n=len(dp),
                overlap_bars=len(over), overlap_mismatch=mism)

def st(rows):
    if not rows: return dict(n=0,ev=0.0,win=0.0)
    return dict(n=len(rows), ev=round(sum(r['R'] for r in rows)/len(rows),4),
                win=round(sum(1 for r in rows if r['R']>0)/len(rows)*100,1))

def per_year(rows):
    ys={}
    for r in rows: ys.setdefault(r['year'],[]).append(r)
    return {y: st(rs) for y,rs in sorted(ys.items())}

def revalidate(gate_k=1.2, ac_thr=0.10, tgt_R=2.0, trend_lb=30, label=""):
    allrows=[]; persym={}; coverage={}
    for s in METALS:
        T,B = load_deep_h1(s)
        if len(B) < 300:
            coverage[s]=dict(n_bars=len(B)); continue
        coverage[s]=dict(n_bars=len(B), first=T[0].isoformat(), last=T[-1].isoformat())
        atrs=[atr14(B,k) for k in range(len(B))]
        cost = w1.cost_for(s)
        rows = idb.fvg_retest_signals(T,B,atrs,cost, gate_k=gate_k, trend_lb=trend_lb,
                                      ac_thr=ac_thr, tgt_R=tgt_R, maxbars=320)
        for r in rows: r['sym']=s; r['R']=wins(r['R'])
        allrows += rows; persym[s]=rows
    tr=[r for r in allrows if r['year']<=2024]
    f25=[r for r in allrows if r['year']==2025]
    f26=[r for r in allrows if r['year']==2026]
    fwd=[r for r in allrows if r['year']>=2025]
    ps={}
    for s,r in persym.items():
        if not r: continue
        a=st([x for x in r if x['year']<=2024]); b=st([x for x in r if x['year']>=2025])
        ps[s]=dict(train=a,fwd=b,by_year=per_year(r),
                   both_pos=bool(a['ev']>0 and b['ev']>0 and a['n']>=20))
    # leak audit: every signal year must be within data coverage; no future read (entry uses closed bars)
    return dict(label=label, gate_k=gate_k, ac_thr=ac_thr, tgt_R=tgt_R,
                train=st(tr), fwd25=st(f25), fwd26=st(f26), fwd=st(fwd),
                by_year=per_year(allrows), per_symbol=ps, coverage=coverage,
                n_total=len(allrows))

if __name__ == "__main__":
    out={}
    out['superset_check'] = {s: superset_check(s) for s in METALS}
    # the two LOCKED metals IDB tiers from KB3:
    out['metals_fvg_breadth_acNone'] = revalidate(ac_thr=None, label="metals_intraday_fvg (acNone, breadth)")
    out['metals_fvg_hi_ac0.10']      = revalidate(ac_thr=0.10, label="metals_intraday_fvg_hi (ac>=0.10)")
    # gate monotonicity (anti-overfit): ac sweep
    out['ac_sweep'] = {f"ac{a}": revalidate(ac_thr=a)['fwd'] | {'train':revalidate(ac_thr=a)['train']}
                       for a in (None,0.05,0.10,0.15,0.20)}
    p = HERE / "KB6_IDB_METALS_REVAL_RESULT.json"
    p.write_text(json.dumps(out, indent=2, default=str))
    # console summary
    for key in ('metals_fvg_breadth_acNone','metals_fvg_hi_ac0.10'):
        r=out[key]
        print(f"\n=== {r['label']} ===")
        print(f"  TRAIN<=2024: {r['train']}   FWD25: {r['fwd25']}   FWD26: {r['fwd26']}   FWD: {r['fwd']}")
        print(f"  by_year: " + " ".join(f"{y}:{v['ev']}(n{v['n']})" for y,v in r['by_year'].items()))
        print(f"  n_total={r['n_total']}")
        for s,v in r['per_symbol'].items():
            print(f"    {s}: TRAIN {v['train']['ev']}(n{v['train']['n']}) / FWD {v['fwd']['ev']}(n{v['fwd']['n']}) both_pos={v['both_pos']}")
    print("\ncoverage:", json.dumps(out['metals_fvg_breadth_acNone']['coverage'], default=str))
    print("superset:", json.dumps(out['superset_check'], default=str))
    print(f"\nwrote {p}")
