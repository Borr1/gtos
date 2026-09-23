"""KB7 (track: reinstate-sleeves) — materialize the dropped IDB intraday-breadth sleeves
and the leadlag/subh4 streams with a CONFIGURABLE winsor cap, cache them for the growth-MC.

IDB sleeves re-tested: crypto H1 FVG-retest (ac>=0.10, t2) and metals H1 FVG-retest.
We materialize them on the DEEP H1 union (2014/2021-2026) where it exists (metals via the
W6 deep backfill) and on the 2025-06+ stream for crypto (no pre-2025 crypto H1 exists).
We carry the RAW (un-winsorized) R so the growth-MC can choose the cap.
"""
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'../../..')
import json, pickle, statistics
from datetime import datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
from geometry_lib import Bar, atr14
import wave1_structure_setups_ict as w1
import IDB_intraday_breadth as idb
import KB6_revalidate_idb_metals as RVM  # deep H1 metals loader

def raw_fvg_rows(grp, syms, loader, *, gate_k=1.2, ac_thr=0.10, tgt_R=2.0, trend_lb=30, sleeve='idb'):
    """Run the EXACT IDB fvg_retest entry but record the RAW (un-winsorized) R + date."""
    rows = []
    for s in syms:
        T, B = loader(s)
        if len(B) < 300: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        cost = w1.cost_for(s)
        # call the IDB entry but pull raw R by re-simulating without wins(): easiest is to
        # re-run fvg_retest_signals (which winsorizes) -> instead reconstruct raw via simulate.
        from geometry_lib import simulate
        import compounding_sleeve as cs
        n = len(B); mb = 320
        for i in range(max(trend_lb+2,101), n-1):
            a = atrs[i]
            if a <= 0: continue
            sma100 = sum(atrs[i-99:i+1])/100
            if sma100 <= 0 or a < gate_k*sma100: continue
            diff = B[i].c - B[i-trend_lb].c
            tr = 1 if diff > 1.0*a else (-1 if diff < -1.0*a else 0)
            if tr == 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac_thr is not None and (ac is None or ac < ac_thr): continue
            b = B[i]; d = 0; sd = None
            if tr == 1:
                for k in range(i-2, max(i-9,60), -1):
                    gap_top=B[k].l; gap_bot=B[k-2].h
                    if gap_top-gap_bot < 0.10*a: continue
                    if b.l<=gap_top and b.c>gap_bot and b.c>b.o:
                        sd=max((b.c-min(b.l,gap_bot))+0.10*a, 0.25*a); d=1; break
            else:
                for k in range(i-2, max(i-9,60), -1):
                    gap_bot=B[k].h; gap_top=B[k-2].l
                    if gap_top-gap_bot < 0.10*a: continue
                    if b.h>=gap_bot and b.c<gap_top and b.c<b.o:
                        sd=max((max(b.h,gap_top)-b.c)+0.10*a, 0.10*a); d=-1; break
            if d==0 or sd is None: continue
            R = simulate(B, i, d, stop_dist=sd, target_dist=tgt_R*sd, cost=cost, maxbars=mb)
            rows.append(dict(sleeve=sleeve, sym=s, date=T[i].date(), year=T[i].year, R_raw=R))
    return rows

def main():
    out = {}
    # crypto H1 FVG (2025-06+ only; no deep crypto H1) -- loader = idb.load_ltf
    cload = lambda s: idb.load_ltf('crypto', s, 'H1')
    out['idb_crypto'] = raw_fvg_rows('crypto', idb.CRYPTO, cload, ac_thr=0.10, tgt_R=2.0, sleeve='idb_crypto')
    # metals H1 FVG on DEEP union (real TRAIN<=2024)
    out['idb_metals'] = raw_fvg_rows('metals', RVM.METALS, RVM.load_deep_h1, ac_thr=0.10, tgt_R=2.0, sleeve='idb_metals')
    out['idb_metals_acNone'] = raw_fvg_rows('metals', RVM.METALS, RVM.load_deep_h1, ac_thr=None, tgt_R=2.0, sleeve='idb_metals_acNone')
    pickle.dump(out, open(HERE/'KB7_idb_streams_cache.pkl','wb'))
    for k,v in out.items():
        R=[r['R_raw'] for r in v]; n=len(R)
        tr=[r['R_raw'] for r in v if r['year']<=2024]; fw=[r['R_raw'] for r in v if r['year']>=2025]
        def m(x): return round(sum(x)/len(x),3) if x else None
        print(f"{k}: n={n} rawEV={m(R)} | TRAIN n={len(tr)} EV={m(tr)} | FWD n={len(fw)} EV={m(fw)} | maxR={round(max(R),2) if R else None}")
if __name__=='__main__':
    main()
