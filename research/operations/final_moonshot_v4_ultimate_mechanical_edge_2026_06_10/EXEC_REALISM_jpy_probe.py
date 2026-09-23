"""EXEC_REALISM — JPY breadth fill-sensitivity probe (the brief's explicit low-win flag).

The two JPY breadth sleeves (London R1 open-impulse, NY R1 open-impulse) are conf-0.15 breadth:
M15 entries, TIGHT 1.0*ATR stop, 2.5*ATR target, 48 M15-bar horizon, ~36-37% win. Tight-stop
low-win sleeves are where slippage erodes EV hardest, so we re-price them at M1.

Modeled: enter at the M15 first-hour-close bar (B[iw].c), simulate stop/target on M15.
M1-realistic: enter at next M1 OPEN after that M15 bar closes + adverse spread; stop/target on M1
with adverse slippage on the stop and limit (no positive slip) on the target; same-bar pessimistic.

These sleeves are 5% (London) and 1% (NY) of book EV, so even a large % erosion is a small book hit,
but the brief asks us to FLAG fill-sensitive sleeves explicitly -- this quantifies it.
"""
from __future__ import annotations
import sys, json, collections
from datetime import datetime, timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import Bar, atr14, simulate
import wave1_structure_setups_ict as w1
import kb2_new_breadth as nb
import EXEC_REALISM_m1_lib as M1

def wins(r): return max(-1.3, min(5.0, r))

# JPY R1 config (mirrors kb2_new_breadth.session_open_mom; London R1 + NY R1)
JPY = ['GBPJPY', 'USDJPY']
LW = 4; STOP_M = 1.0; TGT_M = 2.5; MAXBARS = 48
LONDON_HOUR = 8     # London open (server hour, per KB_fx_jpy R1)
NY_HOUR = 14        # NY-open analogue locked in kb2_new_breadth

def jpy_signals(session_hour):
    """Yield (entry_ts, sym, year, d, sd_price, entry_close, modeled_R) for the R1 open-impulse."""
    out = []
    for sym in JPY:
        T, B, A = nb.load_m15(sym); cost = w1.cost_for(sym)
        byday = collections.defaultdict(list)
        for i, t in enumerate(T): byday[t.date()].append(i)
        for day, idxs in sorted(byday.items()):
            ses = [i for i in idxs if T[i].hour >= session_hour]
            if len(ses) < LW + 2: continue
            i0 = ses[0]; iw = ses[LW-1]
            if i0 < 20: continue
            a = A[iw]
            if a <= 0: continue
            imp = B[iw].c - B[i0].o
            d = 1 if imp > 0 else -1
            modeled = wins(simulate(B, iw, d, stop_dist=STOP_M*a, target_dist=TGT_M*a,
                                    maxbars=MAXBARS, cost=cost))
            # entry instant = close of the first-hour window bar iw -> T[iw] + 15min
            entry_ts = T[iw] + timedelta(minutes=15)
            out.append(dict(sym=sym, year=day.year, ts=entry_ts, d=d, sd=STOP_M*a,
                            tgt=TGT_M*a, entry_close=B[iw].c, modeled=modeled, cost=cost))
    return out

# Stop-side buffer in PRICE = half the per-symbol round-trip cost (spread already in cost map;
# do NOT re-add spread on the entry -- only model the exit-side market-order stop crossing).
def stop_buffer_px(sym, sd):
    try:
        return 0.5 * w1.cost_for(sym) * sd
    except Exception:
        return 0.0

MAXBARS_M1 = MAXBARS * 15   # 48 M15 bars = 720 minutes
GAP_TOL = 15

def m1_reconcile(sig):
    sym = sig['sym']; d = sig['d']; sd = sig['sd']; tgt = sig['tgt']; cost = sig['cost']
    T, B = M1.load_m1(sym)
    if not B or sig['ts'] < T[0] or sig['ts'] > T[-1]: return None
    si = M1.first_m1_after(T, sig['ts'])
    if si is None or si >= len(B) - 5: return None
    gap = (T[si] - sig['ts']).total_seconds() / 60.0
    sbuf = stop_buffer_px(sym, sd)                 # exit-side half-spread on stops only
    entry_px = B[si].o                             # market fill at next M1 open (cost in R)
    stop_px = entry_px - d * sd
    tgt_px = entry_px + d * tgt
    end = min(si + MAXBARS_M1, len(B) - 1)
    R = None
    for j in range(si + 1, end + 1):
        b = B[j]
        # pessimistic same-bar: stop first
        if (d > 0 and b.l <= stop_px) or (d < 0 and b.h >= stop_px):
            gap_fill = (b.o if (d > 0 and b.o < stop_px) or (d < 0 and b.o > stop_px) else stop_px)
            fill = gap_fill - d * sbuf
            R = d * (fill - entry_px) / sd; break
        if (d > 0 and b.h >= tgt_px) or (d < 0 and b.l <= tgt_px):
            R = d * (tgt_px - entry_px) / sd; break
    if R is None:
        R = d * (B[end].c - entry_px) / sd
    m1R = wins(R - cost)
    return dict(sym=sym, year=sig['year'], modeled=sig['modeled'], m1=m1R,
                gap_min=round(gap, 1), gapped=gap > GAP_TOL)

def block(rs):
    if not rs: return None
    mod = [r['modeled'] for r in rs]; m1 = [r['m1'] for r in rs]
    ero = [r['m1'] - r['modeled'] for r in rs]
    return dict(n=len(rs), modeled_ev=round(sum(mod)/len(mod), 4), m1_ev=round(sum(m1)/len(m1), 4),
                erosion_ev=round(sum(ero)/len(ero), 4),
                m1_win=round(100*sum(1 for x in m1 if x > 0)/len(rs), 1),
                worst_erosion=round(min(ero), 4))

def run(name, session_hour):
    sigs = jpy_signals(session_hour)
    rows = [r for s in sigs if (r := m1_reconcile(s)) is not None]
    clean = [r for r in rows if not r['gapped']]
    res = {"sleeve": name, "n_signals": len(sigs), "n_m1": len(rows),
           "n_clean": len(clean), "n_gapped": len(rows) - len(clean),
           "clean": block(clean), "gapped": block([r for r in rows if r['gapped']])}
    for y in (2025, 2026):
        res[f"y{y}_clean"] = block([r for r in clean if r['year'] == y])
    bysym = collections.defaultdict(list)
    for r in clean: bysym[r['sym']].append(r)
    res["per_symbol_clean"] = {s: block(v) for s, v in sorted(bysym.items())}
    return res

if __name__ == "__main__":
    out = {}
    for name, hr in (("fx_jpy_london", LONDON_HOUR), ("fx_jpy_ny", NY_HOUR)):
        r = run(name, hr); out[name] = r
        print(f"=== {name} (hr={hr}) ===")
        print("CLEAN:", json.dumps(r["clean"]))
        print("y2025:", json.dumps(r.get("y2025_clean")))
        print("y2026:", json.dumps(r.get("y2026_clean")))
    with open(HERE / "EXEC_REALISM_JPY_RESULT.json", "w") as f:
        json.dump(out, f, indent=1)
    print("WROTE EXEC_REALISM_JPY_RESULT.json")
