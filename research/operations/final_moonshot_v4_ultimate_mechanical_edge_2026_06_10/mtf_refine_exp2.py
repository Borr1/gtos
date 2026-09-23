"""mtf_refine EXP2 — better FILL, same protective stop. + M15 fill. + frequency probe.

EXP1 learning: tightening the stop to lower-TF structure FAILS (noise stops you out; the
H4-width stop is protective in the persistence regime). So keep the H4 stop DISTANCE but
improve the ENTRY PRICE by waiting for a lower-TF pullback inside the H4 window.

VAR_C (H1 better-fill, H4-width stop): after H4 signal closes, wait up to W H1 bars for a
  pullback AGAINST the signal dir (long: an H1 bar low below the signal-bar close), enter at
  that improved price, stop = entry -/+ sd_h4 (SAME R-dollar width as baseline). Outcome on H1.
  -> if filled better, the same dollar-move = MORE R, AND fewer trades stop out (entry closer
     to the stop-protected zone is actually farther in price terms = lower stop-out odds? no:
     better long fill = lower entry = stop is the same DISTANCE below a LOWER entry, i.e. lower
     absolute stop -> we are buying the dip with the same risk unit). Pessimistic: if no
     pullback within W bars, FALL BACK to baseline H4 entry (never skip a signal).

VAR_D (M15 better-fill): same idea on M15 (finer pullback granularity).

VAR_E (improved-fill cap): only accept the better fill if it improves entry by >= K*ATR_h1,
  else baseline. Avoids chasing.

FREQ probe: count how often a real lower-TF pullback existed (added-quality fills) vs fallback.
All leak-free: lower-TF bars strictly after H4 signal close; simulate scores forward only.
"""
import sys, json, collections, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m

SYM = "XAUUSD"
H1_MAXBARS = 320
M15_MAXBARS = 1280
W_H1 = 12         # wait window for a better fill (H1 bars ~ half day)
W_M15 = 48        # same wall-clock on M15
def wins(r): return max(-1.3, min(5.0, r))

def state_d_at(B, i, d, sd, vr, cost, maxbars):
    return cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=maxbars)

def h4_signals():
    T, B = w1.load(SYM)
    atrs = [atr14(B, k) for k in range(len(B))]
    cost = w1.cost_for(SYM)
    out = []
    for (t, d, sd, td, i, B2, c2) in g.fvg_signals(SYM):
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < cs.AC_THR: continue
        vr = cs.vol_ratio(atrs, i)
        out.append((t, d, sd, i, B, vr, c2))
    return out

def better_fill(Tl, Bl, si, d, signal_close, sd_h4, window, min_improve):
    """Wait up to `window` lower-TF bars for a fill better than signal_close by >= min_improve.
    Returns (entry_idx, improved) where improved=True if a real better fill was taken.
    Pessimistic: we only get filled if price trades through our limit (long: low<=limit)."""
    end = min(si + window, len(Bl) - 1)
    limit = signal_close - min_improve if d > 0 else signal_close + min_improve
    for j in range(si, end + 1):
        b = Bl[j]
        if d > 0 and b.l <= limit:
            return j, True   # filled on the pullback at this bar
        if d < 0 and b.h >= limit:
            return j, True
    return None, False

def run_tf(tf, maxbars, window, min_improve_atr):
    sigs = h4_signals()
    Tl, Bl = m.load_ltf(SYM, tf)
    rows = []; filled_better = 0; fallback = 0
    for (t, d, sd_h4, i_h4, B_h4, vr, cost) in sigs:
        ts_close = t + datetime.timedelta(hours=4)
        si = m.first_ltf_index_after(Tl, ts_close)
        if si is None or si < 30 or si >= len(Bl)-2:
            # no lower-TF coverage: use baseline H4 outcome
            rb = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)
            rows.append((t.year, rb['R'], False)); fallback += 1; continue
        signal_close = B_h4[i_h4].c
        a1 = atr14(Bl, si)
        min_imp = min_improve_atr * a1 if a1 > 0 else 0.0
        ej, improved = better_fill(Tl, Bl, si, d, signal_close, sd_h4, window, min_imp)
        if ej is None:
            # no pullback -> fall back to immediate lower-TF entry at si, H4-width stop
            r = state_d_at(Bl, si, d, sd_h4, vr, cost, maxbars)
            rows.append((t.year, r['R'], False)); fallback += 1
        else:
            r = state_d_at(Bl, ej, d, sd_h4, vr, cost, maxbars)
            rows.append((t.year, r['R'], improved)); filled_better += 1
    return rows, filled_better, fallback

def baseline_rows():
    rows = []
    for (t, d, sd_h4, i_h4, B_h4, vr, cost) in h4_signals():
        rb = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)
        rows.append((t.year, rb['R']))
    return rows

def report(name, rows):
    yr = collections.defaultdict(list)
    for tup in rows:
        y, r = tup[0], tup[1]; yr[y].append(r)
    print(f"\n=== {name} (n={len(rows)}) ===")
    for y in sorted(yr):
        v = yr[y]; print(f"  {y}: n={len(v):>3} R/t={sum(v)/len(v):+.3f} win={100*sum(1 for x in v if x>0)/len(v):.0f}%")
    fwd = [t[1] for t in rows if t[0] >= 2025]; tr = [t[1] for t in rows if t[0] <= 2024]
    if tr: print(f"  TRAIN<=2024: n={len(tr)} R/t={sum(tr)/len(tr):+.3f}")
    if fwd: print(f"  FWD 2025-26: n={len(fwd)} R/t={sum(fwd)/len(fwd):+.3f} win={100*sum(1 for x in fwd if x>0)/len(fwd):.0f}%")

if __name__ == "__main__":
    report("BASELINE H4-close, H4 STATE_D", baseline_rows())
    for tf, mb, w in (("H1", H1_MAXBARS, W_H1), ("M15", M15_MAXBARS, W_M15)):
        for mi in (0.0, 0.25, 0.5):
            rows, fb, fbk = run_tf(tf, mb, w, mi)
            improved = sum(1 for t in rows if len(t) > 2 and t[2])
            report(f"VAR {tf} better-fill min_improve={mi}*ATR (better-filled {improved}/{len(rows)})", rows)
