"""mtf_refine EXP6 — GRADE-FILTERED H1-native breadth sleeve (track: mtf_refine).

EXP5 learning: H1-native FVG retests under the H4 GO-state add ~52 NEW trades/yr forward,
but raw quality is too low: TRAIN -0.135R / FWD +0.184R = forward-only confound (NOT
promotable). 2016 (-0.98, 4% win) and 2024 (-0.85, 6% win) destroy train.

This experiment adds a GRADE filter to the H1-native FVG and sweeps it. The threshold is
chosen on TRAIN (year<=2024); the SAME fixed rule is reported FORWARD 2025-26 separately,
per-year and per-symbol. Grade dimensions tested:
  G  gap depth      : gap size >= G * ATR_h1  (raw floor was 0.10)
  V  displacement   : the impulse bar that opened the FVG had range >= V * ATR_h1
  C  H4 confluence  : the H1 retest zone overlaps a still-open H4 FVG zone (same dir)
All else identical to EXP5: H4 GO-state gate (trend!=0 + ac60>=0.10 + vol gate), continuation
aligned with H4 trend, protective state-scaled stop (1.5*H4_ATR), STATE_D exit on H1, dedup
vs core H4 grid signals (within 8h same dir), maxbars=320.

NO LOOKAHEAD: H4 state from last fully-closed H4 bar at H1 bar time; H1 FVG uses only closed
bars k<=j; outcomes scored by cs.exit_state_d on the H1 stream (leak-free).
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
H4_STOP_MULT = 1.5

def h4_state(sym):
    T, B = w1.load(sym)
    if len(B) < 200: return [], [], []
    atrs = [atr14(B, k) for k in range(len(B))]
    states = []
    for i in range(len(B)):
        a = atrs[i]; gate = False
        if i >= 100 and a > 0:
            sma = sum(atrs[i-99:i+1])/100
            gate = sma > 0 and a >= g.GATE_K*sma
        tr = w1.htf_trend(B, i, 30) if i >= 60 else 0
        ac = cs.autocorr(B, i, 60)
        states.append(dict(t=T[i], tr=tr, ac=ac if ac is not None else -9,
                           gate=gate, atr=a, vr=cs.vol_ratio(atrs, i)))
    return T, B, states

def last_h4_state(T_h4, states, th):
    lo, hi = 0, len(T_h4)
    while lo < hi:
        mid = (lo+hi)//2
        if T_h4[mid] + datetime.timedelta(hours=4) <= th: lo = mid+1
        else: hi = mid
    return states[lo-1] if lo-1 >= 0 else None

def h4_fvg_zones(B_h4, atrs_h4, ki):
    """Open H4 FVG zones (top,bot,dir) created up to and incl. bar ki (closed). Cheap recent scan."""
    zones = []
    a = atrs_h4[ki] if ki < len(atrs_h4) else 0
    if a <= 0: return zones
    for k in range(max(2, ki-12), ki+1):
        gt = B_h4[k].l; gb = B_h4[k-2].h
        if gt - gb >= 0.10*a: zones.append((gt, gb, +1))   # bullish gap
        gb2 = B_h4[k].h; gt2 = B_h4[k-2].l
        if gt2 - gb2 >= 0.10*a: zones.append((gt2, gb2, -1))  # bearish gap
    return zones

def h1_fvg_native_graded(Bl, j, a, G):
    """H1 FVG-retest trigger with gap-depth grade G and displacement V info.
    Returns list of (dir, struct_extreme, gap_top, gap_bot, disp_range_atr)."""
    b = Bl[j]; out = []
    # long
    for k in range(j-2, max(j-9, 14), -1):
        gap_top = Bl[k].l; gap_bot = Bl[k-2].h
        if gap_top - gap_bot < G*a: continue
        if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
            disp = (Bl[k-1].h - Bl[k-1].l)/a if a > 0 else 0.0  # impulse bar = middle bar k-1
            out.append((+1, min(b.l, gap_bot), gap_top, gap_bot, disp)); break
    for k in range(j-2, max(j-9, 14), -1):
        gap_bot = Bl[k].h; gap_top = Bl[k-2].l
        if gap_top - gap_bot < G*a: continue
        if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
            disp = (Bl[k-1].h - Bl[k-1].l)/a if a > 0 else 0.0
            out.append((-1, max(b.h, gap_top), gap_top, gap_bot, disp)); break
    return out

def run(G=0.10, V=0.0, C=False):
    # core H4 grid signals (for dedup)
    core = collections.defaultdict(list)
    for sym in METALS:
        T, B = w1.load(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is not None and ac >= cs.AC_THR:
                core[sym].append((t, d))
    rows = []
    for sym in METALS:
        T_h4, B_h4, states = h4_state(sym)
        if not states: continue
        atrs_h4 = [st['atr'] for st in states]
        Tl, Bl = m.load_ltf(sym, "H1")
        if len(Bl) < 60: continue
        cost = w1.cost_for(sym); coreset = core.get(sym, [])
        # precompute H4 index lookup pointer
        for j in range(30, len(Bl)-2):
            a = atr14(Bl, j)
            if a <= 0: continue
            # last closed H4 bar index for confluence + state
            lo, hi = 0, len(T_h4)
            while lo < hi:
                mid = (lo+hi)//2
                if T_h4[mid] + datetime.timedelta(hours=4) <= Tl[j]: lo = mid+1
                else: hi = mid
            ki = lo-1
            if ki < 0: continue
            st = states[ki]
            if not st['gate'] or st['tr'] == 0 or st['ac'] < cs.AC_THR: continue
            cands = h1_fvg_native_graded(Bl, j, a, G)
            for (d, struct, gtop, gbot, disp) in cands:
                if d != st['tr']: continue
                if disp < V: continue                        # displacement-velocity grade
                if C:                                          # H4 FVG confluence grade
                    zones = h4_fvg_zones(B_h4, atrs_h4, ki)
                    conf = any(zd == d and not (gtop < zb or gbot > zt)
                               for (zt, zb, zd) in zones)
                    if not conf: continue
                dup = any(dd == d and abs((Tl[j]-tt).total_seconds()) <= 8*3600 for (tt, dd) in coreset)
                if dup: continue
                sd = H4_STOP_MULT * st['atr']
                if sd <= 0: continue
                r = cs.exit_state_d(Bl, j, d, sd, st['vr'], cost, maxbars=H1_MAXBARS)
                rows.append(dict(sym=sym, year=Tl[j].year, vr=st['vr'], R=r['R']))
    return rows

def summ(rows):
    yr = collections.defaultdict(list)
    for r in rows: yr[r['year']].append(r['R'])
    peryr = {y: [len(v), round(sum(v)/len(v), 3),
                 round(100*sum(1 for x in v if x > 0)/len(v), 0)] for y, v in sorted(yr.items())}
    tr = [r['R'] for r in rows if r['year'] <= 2024]
    fw = [r['R'] for r in rows if r['year'] >= 2025]
    return dict(
        per_year=peryr,
        train=[len(tr), round(sum(tr)/len(tr), 4) if tr else None,
               round(100*sum(1 for x in tr if x > 0)/len(tr), 1) if tr else None],
        fwd=[len(fw), round(sum(fw)/len(fw), 4) if fw else None,
             round(100*sum(1 for x in fw if x > 0)/len(fw), 1) if fw else None,
             round(len(fw)/1.5, 0) if fw else 0])

if __name__ == "__main__":
    out = {}
    print("RAW (G=0.10,V=0,C=F):", json.dumps(summ(run(0.10, 0.0, False))['train']),
          json.dumps(summ(run(0.10, 0.0, False))['fwd']))
    # sweep gap depth
    print("\n--- gap-depth grade G ---")
    for G in (0.10, 0.25, 0.40, 0.60, 0.80):
        s = summ(run(G, 0.0, False)); out[f"G{G}"] = s
        print(f"G={G}: train={s['train']} fwd={s['fwd']}")
    # sweep displacement
    print("\n--- displacement grade V (G=0.25) ---")
    for V in (1.0, 1.3, 1.6, 2.0):
        s = summ(run(0.25, V, False)); out[f"G0.25_V{V}"] = s
        print(f"V={V}: train={s['train']} fwd={s['fwd']}")
    # confluence
    print("\n--- H4 confluence C (G=0.25) ---")
    s = summ(run(0.25, 0.0, True)); out["G0.25_C"] = s
    print(f"C=True: train={s['train']} fwd={s['fwd']}")
    # combos
    print("\n--- combos ---")
    for tag, (G, V, C) in {
        "G0.40_V1.3": (0.40, 1.3, False),
        "G0.40_V1.6": (0.40, 1.6, False),
        "G0.60_V1.3": (0.60, 1.3, False),
        "G0.25_V1.3_C": (0.25, 1.3, True),
        "G0.40_V1.6_C": (0.40, 1.6, True),
    }.items():
        s = summ(run(G, V, C)); out[tag] = s
        print(f"{tag}: train={s['train']} fwd={s['fwd']}")
    (HERE/"MTF_REFINE_EXP6.json").write_text(json.dumps(out, indent=1))
    print("\nwrote MTF_REFINE_EXP6.json")
