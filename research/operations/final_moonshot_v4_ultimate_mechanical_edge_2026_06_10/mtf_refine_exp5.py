"""mtf_refine EXP5 — FREQUENCY: H1-native FVG retests under the H4 regime gate (added breadth).

Goal: more setups, not just better fills. H4 sets the STATE (HTF trend + persistence ac60>=0.10
+ vol gate) on each H4 bar; within H4 bars whose state is GO, scan H1 for FVG-retest
continuation entries (same geometry as the H4 setup, computed natively on H1). These are NEW
trades the H4 grid never saw (an H1 FVG can form and retest entirely inside one H4 bar window,
or across H4 bars where the H4 close didn't itself trigger).

State is read from the LAST CLOSED H4 bar at the time of each H1 bar (no lookahead): for H1 bar
at time th, use H4 bar k = last H4 whose open+4h <= th. trend/ac60/vol gate from that H4 bar.
Stop = H1 structural? -> EXP1 showed tight stops fail. So use a STATE-scaled stop = H4 ATR-based
width (k's ATR * fixed mult) anchored at the H1 entry. Exit = STATE_D on H1.

Dedup: don't double-count an H1 entry that coincides (same dir, within 4h) with an H4 grid signal
already counted by the core sleeve -> those are the EXP3/4 'better-fill' trades. Here we COUNT
ONLY the genuinely NEW H1 entries and measure their standalone EV + win + per-year/symbol.
This is the breadth sleeve; kept at small size if forward-positive.
Deep H1 only where available (XAUUSD full; others 2025-06+).
"""
import sys, json, collections, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m

METALS = cs.METALS
H1_MAXBARS = 320
STOP_BUF = 0.10; STOP_FLOOR = 0.25
H4_STOP_MULT = 1.5   # state stop width = H4_STOP_MULT * H4_ATR (wide, protective)

def h4_state(sym):
    """Per H4 bar: (open_time, trend, ac60, vol_gate_ok, atr_h4). Leak-free per-bar."""
    T, B = w1.load(sym)
    if len(B) < 200: return [], [], []
    atrs = [atr14(B, k) for k in range(len(B))]
    states = []
    for i in range(len(B)):
        a = atrs[i]
        gate = False
        if i >= 100 and a > 0:
            sma = sum(atrs[i-99:i+1])/100
            gate = sma > 0 and a >= g.GATE_K*sma
        tr = w1.htf_trend(B, i, 30) if i >= 60 else 0
        ac = cs.autocorr(B, i, 60)
        states.append(dict(t=T[i], tr=tr, ac=ac if ac is not None else -9,
                           gate=gate, atr=a, vr=cs.vol_ratio(atrs, i)))
    return T, B, states

def last_h4_state(T_h4, states, th):
    """State from last H4 bar that has fully closed by time th (open+4h <= th)."""
    lo, hi = 0, len(T_h4)
    while lo < hi:
        mid = (lo+hi)//2
        if T_h4[mid] + datetime.timedelta(hours=4) <= th: lo = mid+1
        else: hi = mid
    return states[lo-1] if lo-1 >= 0 else None

def h1_fvg_native(Bl, j, a):
    """H1 FVG-retest continuation trigger at bar j (mirror of g.fvg_signals geometry), dir-agnostic.
    Returns (dir, raw_struct) candidates; caller filters by H4 trend."""
    b = Bl[j]; out = []
    # long FVG
    for k in range(j-2, max(j-9, 14), -1):
        gap_top = Bl[k].l; gap_bot = Bl[k-2].h
        if gap_top - gap_bot < 0.10*a: continue
        if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
            out.append((+1, min(b.l, gap_bot))); break
    for k in range(j-2, max(j-9, 14), -1):
        gap_bot = Bl[k].h; gap_top = Bl[k-2].l
        if gap_top - gap_bot < 0.10*a: continue
        if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
            out.append((-1, max(b.h, gap_top))); break
    return out

def run():
    # collect H4 grid signal times per symbol to dedup
    grid = collections.defaultdict(set)
    for sym in METALS:
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(*w1.load(sym), 60) if False else None
        # recompute grid signals w/ persistence (same as core)
    # simpler: recompute core signal set
    core = collections.defaultdict(list)
    for sym in METALS:
        T, B = w1.load(sym); atrs = [atr14(B, k) for k in range(len(B))]
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is not None and ac >= cs.AC_THR:
                core[sym].append((t, d))
    new_rows = []
    for sym in METALS:
        T_h4, B_h4, states = h4_state(sym)
        if not states: continue
        Tl, Bl = m.load_ltf(sym, "H1")
        if len(Bl) < 60: continue
        cost = w1.cost_for(sym)
        coreset = core.get(sym, [])
        for j in range(30, len(Bl)-2):
            a = atr14(Bl, j)
            if a <= 0: continue
            st = last_h4_state(T_h4, states, Tl[j])
            if st is None or not st['gate'] or st['tr'] == 0 or st['ac'] < cs.AC_THR: continue
            cands = h1_fvg_native(Bl, j, a)
            for (d, struct) in cands:
                if d != st['tr']: continue   # continuation only, aligned with H4 trend
                # dedup: skip if within 8h of a core H4 signal same dir
                dup = any(dd == d and abs((Tl[j]-tt).total_seconds()) <= 8*3600 for (tt, dd) in coreset)
                if dup: continue
                sd = H4_STOP_MULT * st['atr']   # protective state-scaled stop
                if sd <= 0: continue
                r = cs.exit_state_d(Bl, j, d, sd, st['vr'], cost, maxbars=H1_MAXBARS)
                new_rows.append(dict(sym=sym, year=Tl[j].year, vr=st['vr'], R=r['R']))
    return new_rows

def block(rows, pred):
    v = [r for r in rows if pred(r)]
    if not v: return None
    R = [x['R'] for x in v]
    return dict(n=len(v), Rt=round(sum(R)/len(R), 4), win=round(100*sum(1 for x in R if x > 0)/len(R), 1))

if __name__ == "__main__":
    rows = run()
    print(f"NEW H1-native breadth trades: {len(rows)}")
    print("Per-year:")
    for y in sorted(set(r['year'] for r in rows)):
        print(f"  {y}:", block(rows, lambda r, y=y: r['year'] == y))
    print("FWD per-symbol:")
    for s in METALS:
        b = block(rows, lambda r, s=s: r['sym'] == s and r['year'] >= 2025)
        if b: print(f"  {s:>7}:", b)
    tr = [r for r in rows if r['year'] <= 2024]; fw = [r for r in rows if r['year'] >= 2025]
    if tr: print(f"TRAIN n={len(tr)} R/t={sum(x['R'] for x in tr)/len(tr):+.4f}")
    if fw: print(f"FWD   n={len(fw)} R/t={sum(x['R'] for x in fw)/len(fw):+.4f} win={100*sum(1 for x in fw if x['R']>0)/len(fw):.1f}% ~{len(fw)/1.5:.0f}/yr")
    (HERE/"MTF_REFINE_EXP5.json").write_text(json.dumps({"n": len(rows),
        "train": [len(tr), sum(x['R'] for x in tr)/len(tr) if tr else None],
        "fwd": [len(fw), sum(x['R'] for x in fw)/len(fw) if fw else None]}, indent=1))
