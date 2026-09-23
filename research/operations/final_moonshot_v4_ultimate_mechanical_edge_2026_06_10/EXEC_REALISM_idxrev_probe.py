"""EXEC_REALISM — idxrev direct M1 fill check (replaces the JPY-class proxy).

The LOCKED idxrev rule is WIDE stop (1.5*ATR) + TIGHT target (0.75R = 1.125*ATR), H4 entry,
maxbars=60. Wide stop => the exit-side half-spread stop buffer is a small fraction of R, and the
tight target is a LIMIT fill (no slippage). So idxrev should be LOW fill-sensitivity, unlike the
JPY tight-stop sleeves. Measure it directly on the M1-covered indices (2024+).
"""
from __future__ import annotations
import sys, json, collections
from datetime import timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1
import idxrev_sleeve as idx
import EXEC_REALISM_m1_lib as M1

def wins(r): return max(-1.3, min(5.0, r))

# M1-covered indices in the deep pocket (base m1 dir, 2024+):
POCKET_M1 = ['SPX500', 'NAS100', 'GER40', 'UK100', 'JP225', 'US30_cash']
LB = 16; STOP_ATR = 1.5; TGT_R = 0.75; MAXBARS = 60
GAP_TOL = 30   # H4 index bars; allow a slightly wider tolerance (index session opens)

def stop_buffer_px(sym, sd):
    try: return 0.5 * w1.cost_for(sym) * sd
    except Exception: return 0.0

MAXBARS_M1 = MAXBARS * 4 * 60   # 60 H4 bars = 240h wall-clock

def reconcile():
    rows = []
    for sym in POCKET_M1:
        Th4, Bh4 = w1.load(sym)
        if not Bh4: continue
        cost = w1.cost_for(sym)
        Tm, Bm = M1.load_m1(sym)
        if not Bm: continue
        for (t, d, i, B, ac, vr, a, dist_opp, c, rhi, rlo, pdh, pdl) in idx.signals(sym, lb_range=LB):
            sd = STOP_ATR * a
            modeled = wins(simulate(B, i, d, stop_dist=sd, target_dist=TGT_R*sd, cost=cost, maxbars=MAXBARS))
            ts = Th4[i] + timedelta(hours=4)
            if ts < Tm[0] or ts > Tm[-1]: continue
            si = M1.first_m1_after(Tm, ts)
            if si is None or si >= len(Bm) - 5: continue
            gap = (Tm[si] - ts).total_seconds() / 60.0
            if gap > 6 * 60:   # >6h gap => H4 fill bar not covered by M1
                continue
            sbuf = stop_buffer_px(sym, sd)
            entry = Bm[si].o
            stop_px = entry - d * sd
            tgt_px = entry + d * TGT_R * sd
            end = min(si + MAXBARS_M1, len(Bm) - 1)
            R = None
            for j in range(si + 1, end + 1):
                b = Bm[j]
                if (d > 0 and b.l <= stop_px) or (d < 0 and b.h >= stop_px):
                    gf = (b.o if (d > 0 and b.o < stop_px) or (d < 0 and b.o > stop_px) else stop_px)
                    R = d * (gf - d*sbuf - entry) / sd; break
                if (d > 0 and b.h >= tgt_px) or (d < 0 and b.l <= tgt_px):
                    R = d * (tgt_px - entry) / sd; break
            if R is None:
                R = d * (Bm[end].c - entry) / sd
            rows.append(dict(sym=sym, year=t.year, modeled=modeled, m1=wins(R - cost),
                             gapped=gap > GAP_TOL))
    return rows

def block(rs):
    if not rs: return None
    mod = [r['modeled'] for r in rs]; m1 = [r['m1'] for r in rs]
    ero = [r['m1'] - r['modeled'] for r in rs]
    return dict(n=len(rs), modeled_ev=round(sum(mod)/len(mod), 4), m1_ev=round(sum(m1)/len(m1), 4),
                erosion_ev=round(sum(ero)/len(ero), 4),
                m1_win=round(100*sum(1 for x in m1 if x > 0)/len(rs), 1),
                worst_erosion=round(min(ero), 4))

if __name__ == "__main__":
    rows = reconcile()
    out = {"sleeve": "idxrev", "n": len(rows), "all": block(rows)}
    for y in (2024, 2025, 2026):
        out[f"y{y}"] = block([r for r in rows if r['year'] == y])
    bysym = collections.defaultdict(list)
    for r in rows: bysym[r['sym']].append(r)
    out["per_symbol"] = {s: block(v) for s, v in sorted(bysym.items())}
    print("ALL:", json.dumps(out["all"]))
    for y in (2024, 2025, 2026):
        print(f"y{y}:", json.dumps(out.get(f"y{y}")))
    for s, b in out["per_symbol"].items():
        print(f"  {s:12}", json.dumps(b))
    with open(HERE / "EXEC_REALISM_IDXREV_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    print("WROTE EXEC_REALISM_IDXREV_RESULT.json")
