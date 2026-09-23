"""mtf_refine EXP4 — lock the TRAIN-selected param, dissect FORWARD for confounds.

Train selection: best TRAIN<=2024 R/t was W=12, mi=1.0 (+0.465). To avoid over-fitting the
fallback rate, also report the most-conservative robust choice W=24, mi=0.25 (max coverage,
best forward). Report BOTH as a fixed rule forward, with:
  - per-YEAR (2025, 2026 separately)
  - per-SYMBOL forward (is it all XAUUSD? single-symbol confound?)
  - per-REGIME (vol tier) forward
  - win-rate, trades, and how much of the lift is from 'better-filled' rows vs fallback.
Also a paired diff: for rows that were better-filled, baseline R vs mtf R (apples-to-apples).
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

def h4_signals(sym):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    atrs = [atr14(B, k) for k in range(len(B))]
    cost = w1.cost_for(sym)
    out = []
    for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < cs.AC_THR: continue
        vr = cs.vol_ratio(atrs, i)
        out.append((t, d, sd, i, B, vr, c2))
    return out

def better_fill(Bl, si, d, signal_close, window, min_imp):
    end = min(si + window, len(Bl) - 1)
    limit = signal_close - min_imp if d > 0 else signal_close + min_imp
    for j in range(si, end + 1):
        b = Bl[j]
        if d > 0 and b.l <= limit: return j
        if d < 0 and b.h >= limit: return j
    return None

def run(window, min_improve_atr):
    rows = []  # dict per trade
    for sym in METALS:
        Tl, Bl = m.load_ltf(sym, "H1"); have = len(Bl) > 50
        for (t, d, sd_h4, i_h4, B_h4, vr, cost) in h4_signals(sym):
            rb = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)['R']
            rec = dict(sym=sym, year=t.year, vr=vr, base=rb, kind='fallback_nocov', R=rb)
            if have:
                ts = t + datetime.timedelta(hours=4); si = m.first_ltf_index_after(Tl, ts)
                if si is not None and 30 <= si < len(Bl)-2:
                    a1 = atr14(Bl, si); mi = min_improve_atr * a1 if a1 > 0 else 0.0
                    ej = better_fill(Bl, si, d, B_h4[i_h4].c, window, mi)
                    if ej is None:
                        rec['kind'] = 'fallback_nofill'
                    else:
                        rec['R'] = cs.exit_state_d(Bl, ej, d, sd_h4, vr, cost, maxbars=H1_MAXBARS)['R']
                        rec['kind'] = 'better'
            rows.append(rec)
    return rows

def block(rows, pred):
    v = [r for r in rows if pred(r)]
    if not v: return None
    R = [x['R'] for x in v]
    return dict(n=len(v), Rt=round(sum(R)/len(R), 4), win=round(100*sum(1 for x in R if x > 0)/len(R), 1))

def dissect(label, window, mi):
    rows = run(window, mi)
    print(f"\n############ {label}: W={window}, min_improve={mi}*ATR ############")
    print("FWD per-year:")
    for y in (2025, 2026):
        print(f"  {y}:", block(rows, lambda r, y=y: r['year'] == y))
    print("FWD per-symbol:")
    for s in METALS:
        b = block(rows, lambda r, s=s: r['sym'] == s and r['year'] >= 2025)
        if b: print(f"  {s:>7}:", b)
    print("FWD per vol-regime:")
    for lab, lo, hi in (('LOW<1.35', 0, 1.35), ('MID1.35-1.6', 1.35, 1.6), ('HI>=1.6', 1.6, 99)):
        b = block(rows, lambda r, lo=lo, hi=hi: r['year'] >= 2025 and lo <= r['vr'] < hi)
        if b: print(f"  {lab:>11}:", b)
    # paired diff on better-filled forward rows only (apples-to-apples)
    bf = [r for r in rows if r['kind'] == 'better' and r['year'] >= 2025]
    if bf:
        db = sum(r['base'] for r in bf)/len(bf); dm = sum(r['R'] for r in bf)/len(bf)
        print(f"PAIRED (better-filled fwd rows n={len(bf)}): base {db:+.3f} -> mtf {dm:+.3f}  (lift {dm-db:+.3f}R)")
    tr = [r for r in rows if r['year'] <= 2024]; fw = [r for r in rows if r['year'] >= 2025]
    print(f"TRAIN n={len(tr)} R/t={sum(x['R'] for x in tr)/len(tr):+.4f}")
    print(f"FWD   n={len(fw)} R/t={sum(x['R'] for x in fw)/len(fw):+.4f} win={100*sum(1 for x in fw if x['R']>0)/len(fw):.1f}%")
    return rows

if __name__ == "__main__":
    # baseline forward per-symbol for confound comparison
    base = run(0, 9999)  # window 0 + huge improve -> never better-filled -> pure baseline
    print("=== PURE BASELINE (no mtf) forward per-symbol ===")
    for s in METALS:
        b = block(base, lambda r, s=s: r['sym'] == s and r['year'] >= 2025)
        if b: print(f"  {s:>7}:", b)
    fw = [r for r in base if r['year'] >= 2025]
    print(f"  BASELINE FWD n={len(fw)} R/t={sum(x['R'] for x in fw)/len(fw):+.4f} win={100*sum(1 for x in fw if x['R']>0)/len(fw):.1f}%")
    dissect("TRAIN-AGGRESSIVE", 12, 1.0)
    dissect("ROBUST-MAXCOV", 24, 0.25)
