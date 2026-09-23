"""mtf_refine EXP9 — robustness + leak audit of the H1->M15 cascade better-fill.

EXP8 showed cascade (H1 better-fill; if no H1 pullback, try M15) beats the locked H1 rule on
BOTH train and forward (fwd +1.164 vs +1.129; train +0.482 vs +0.465) and lifts win 85.7->87.8.
Here: (1) sweep the M15-leg params to show insensitivity, (2) explicit leak audit (count any
LTF entry before the H4 signal-bar close), (3) horizon insensitivity on the M15 leg.
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
LEAK = collections.Counter()

def h4_signals(sym):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    atrs = [atr14(B, k) for k in range(len(B))]
    out = []
    for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < cs.AC_THR: continue
        out.append((t, d, sd, i, B, cs.vol_ratio(atrs, i), c2))
    return out

def find_fill(Bl, Tl, si, d, sc, window, mi, ts):
    end = min(si + window, len(Bl) - 1)
    a1 = atr14(Bl, si); imp = mi * a1 if a1 > 0 else 0.0
    limit = sc - imp if d > 0 else sc + imp
    for j in range(si, end + 1):
        if Tl[j] < ts: LEAK['before_close'] += 1; continue
        b = Bl[j]
        if d > 0 and b.l <= limit: return j
        if d < 0 and b.h >= limit: return j
    return None

def run(m15_w, m15_mi, m15_maxbars=1280):
    rows = []
    for sym in METALS:
        sigs = h4_signals(sym)
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd_h4, i_h4, B_h4, vr, cost) in sigs:
            base_R = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)['R']
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            R = base_R; filled = False
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1)-2:
                    ej = find_fill(B1, T1, si, d, sc, 12, 1.0, ts)
                    if ej is not None:
                        R = cs.exit_state_d(B1, ej, d, sd_h4, vr, cost, maxbars=H1_MAXBARS)['R']; filled = True
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15)-2:
                    ej = find_fill(B15, T15, si, d, sc, m15_w, m15_mi, ts)
                    if ej is not None:
                        R = cs.exit_state_d(B15, ej, d, sd_h4, vr, cost, maxbars=m15_maxbars)['R']
            rows.append((t.year, R))
    return rows

def summ(rows):
    fw = [r for y, r in rows if y >= 2025]; tr = [r for y, r in rows if y <= 2024]
    return dict(train=[len(tr), round(sum(tr)/len(tr), 4),
                       round(100*sum(1 for x in tr if x > 0)/len(tr), 1)],
                fwd=[len(fw), round(sum(fw)/len(fw), 4),
                     round(100*sum(1 for x in fw if x > 0)/len(fw), 1)])

if __name__ == "__main__":
    out = {}
    print("--- M15-leg param robustness (cascade) ---")
    for w in (24, 48, 96):
        for mi in (0.5, 1.0):
            s = summ(run(w, mi)); out[f"m15W{w}_mi{mi}"] = s
            print(f"M15 leg W={w:>3} mi={mi}: train={s['train']} fwd={s['fwd']}")
    print("--- M15-leg horizon robustness (W48,mi1.0) ---")
    for mb in (640, 960, 1280, 1920):
        s = summ(run(48, 1.0, mb)); out[f"m15mb{mb}"] = s
        print(f"M15 maxbars={mb}: train={s['train']} fwd={s['fwd']}")
    out["leak"] = dict(LEAK)
    (HERE/"MTF_REFINE_EXP9.json").write_text(json.dumps(out, indent=1))
    print("LEAK (entries before H4 close):", dict(LEAK))
