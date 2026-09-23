"""mtf_refine EXP8 — (a) paired causal proof the H1 lift is NOT forward-only, and
(b) H1->M15 cascade fill: use H1 better-fill; if H1 does not fill within window, try M15;
else fall back to H4. Goal: raise fill RATE (more signals get the better entry) while keeping
the H1 EV. The locked H1 rule already wins; this asks whether the cascade adds without harm.

Locked H1 rule = W=12 H1 bars, mi=1.0*ATR_h1, H4-width stop, STATE_D exit, fallback H4.
Cascade  = same; if H1 window has no qualifying pullback, try M15 (W=48 bars=12h, mi=1.0*ATR_m15)
           before falling back to H4.
Paired causal: per signal, record (base_H4_R, h1_R, filled_flag). Split by era to show the
better-filled lift exists in deep-H1 PRE-2025 (true OOS) as well as forward.

NO LOOKAHEAD throughout (H4 signal actionable t+4h; LTF entry from first bar>=t+4h).
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
H1_MAXBARS = 320; M15_MAXBARS = 1280
DEEP_H1 = {"XAUUSD", "XAGUSD"}   # symbols with pre-2025 H1 coverage (true OOS train)

def h4_signals(sym):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    atrs = [atr14(B, k) for k in range(len(B))]
    out = []
    for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < cs.AC_THR: continue
        vr = cs.vol_ratio(atrs, i)
        out.append((t, d, sd, i, B, vr, c2))
    return out

def find_fill(Bl, si, d, signal_close, window, mi):
    end = min(si + window, len(Bl) - 1)
    a1 = atr14(Bl, si); imp = mi * a1 if a1 > 0 else 0.0
    limit = signal_close - imp if d > 0 else signal_close + imp
    for j in range(si, end + 1):
        b = Bl[j]
        if d > 0 and b.l <= limit: return j
        if d < 0 and b.h >= limit: return j
    return None

def run():
    rows = []  # dict(sym, year, base_R, h1_R, casc_R, h1_filled, casc_src)
    for sym in METALS:
        sigs = h4_signals(sym)
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        for (t, d, sd_h4, i_h4, B_h4, vr, cost) in sigs:
            base_R = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)['R']
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            h1_R = base_R; h1_filled = False; casc_R = base_R; casc_src = "h4"
            # H1 leg
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1)-2:
                    ej = find_fill(B1, si, d, sc, 12, 1.0)
                    if ej is not None:
                        h1_R = cs.exit_state_d(B1, ej, d, sd_h4, vr, cost, maxbars=H1_MAXBARS)['R']
                        h1_filled = True
                        casc_R = h1_R; casc_src = "h1"
            # cascade M15 leg only if H1 didn't fill
            if not h1_filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15)-2:
                    ej = find_fill(B15, si, d, sc, 48, 1.0)
                    if ej is not None:
                        casc_R = cs.exit_state_d(B15, ej, d, sd_h4, vr, cost, maxbars=M15_MAXBARS)['R']
                        casc_src = "m15"
            rows.append(dict(sym=sym, year=t.year, base_R=base_R, h1_R=h1_R,
                             casc_R=casc_R, h1_filled=h1_filled, casc_src=casc_src))
    return rows

def agg(vals):
    if not vals: return [0, None, None]
    return [len(vals), round(sum(vals)/len(vals), 4),
            round(100*sum(1 for x in vals if x > 0)/len(vals), 1)]

if __name__ == "__main__":
    rows = run()
    res = {}
    for era, pred in (("train", lambda r: r['year'] <= 2024), ("fwd", lambda r: r['year'] >= 2025)):
        sub = [r for r in rows if pred(r)]
        res[era] = dict(base=agg([r['base_R'] for r in sub]),
                        h1=agg([r['h1_R'] for r in sub]),
                        cascade=agg([r['casc_R'] for r in sub]),
                        fill_src=dict(collections.Counter(r['casc_src'] for r in sub)))
    # CAUSAL: paired lift on rows where H1 actually filled, split by era (deep-H1 only pre-2025)
    causal = {}
    for era, pred in (("train_deepH1", lambda r: r['year'] <= 2024 and r['sym'] in DEEP_H1),
                      ("fwd_all", lambda r: r['year'] >= 2025)):
        bf = [r for r in rows if pred(r) and r['h1_filled']]
        causal[era] = dict(n=len(bf),
                           base=round(sum(r['base_R'] for r in bf)/len(bf), 4) if bf else None,
                           h1=round(sum(r['h1_R'] for r in bf)/len(bf), 4) if bf else None,
                           lift=round(sum(r['h1_R']-r['base_R'] for r in bf)/len(bf), 4) if bf else None)
    # per-year cascade vs base vs h1
    peryr = {}
    for y in sorted(set(r['year'] for r in rows)):
        sub = [r for r in rows if r['year'] == y]
        peryr[y] = dict(n=len(sub),
                        base=round(sum(r['base_R'] for r in sub)/len(sub), 3),
                        h1=round(sum(r['h1_R'] for r in sub)/len(sub), 3),
                        casc=round(sum(r['casc_R'] for r in sub)/len(sub), 3))
    # per-symbol forward, h1 vs cascade
    persym = {}
    for s in METALS:
        sub = [r for r in rows if r['sym'] == s and r['year'] >= 2025]
        if sub:
            persym[s] = dict(n=len(sub),
                             h1=round(sum(r['h1_R'] for r in sub)/len(sub), 3),
                             casc=round(sum(r['casc_R'] for r in sub)/len(sub), 3),
                             h1_win=round(100*sum(1 for r in sub if r['h1_R'] > 0)/len(sub), 1))
    out = dict(era=res, causal=causal, per_year=peryr, per_symbol_fwd=persym)
    (HERE/"MTF_REFINE_EXP8.json").write_text(json.dumps(out, indent=1))
    print("ERA:", json.dumps(res, indent=1))
    print("CAUSAL paired (H1-filled rows):", json.dumps(causal, indent=1))
    print("PER-YEAR:", json.dumps(peryr))
    print("PER-SYMBOL FWD:", json.dumps(persym))
