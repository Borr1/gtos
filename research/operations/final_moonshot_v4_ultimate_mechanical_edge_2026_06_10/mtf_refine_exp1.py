"""mtf_refine EXP1 — does H1-timed entry beat H4-close entry on the SAME H4 commodity signals?

H4 produces the audited signal (FVG-retest continuation + ac60>=0.10 persistence gate + vol gate).
Baseline = enter at H4 signal-bar close, STATE_D exit, scored on H4 (the +0.865R forward edge).

Variant A (H1 retest-continuation timing): after the H4 signal bar closes, scan up to W H1 bars
for a continuation trigger in the signal direction:
  long  : an H1 bar that pulls back (low < prior H1 low) then closes up (c>o and c>prior close)
  short : mirror.
Enter at that H1 close. Stop = structural (H1 swing extreme of the trigger +0.10*H1_ATR, floored).
This gives a TIGHTER stop (H1 swing vs H4 swing) -> larger R on the same dollar move, and timing.

Variant B (H1 immediate, tighter stop only): enter at the FIRST H1 bar after the H4 signal,
stop = H1-structural. Isolates the "tighter stop" effect from the "wait for trigger" effect.

All scored on the H1 stream with simulate (leak-free). Wall-clock matched: H1 maxbars=320.
Forward holdout: TRAIN<=2024 (threshold-free here; geometry is fixed), report per-year + fwd.
"""
import sys, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m

SYM = "XAUUSD"
H1_MAXBARS = 320            # 320h == H4 maxbars(80)*4h
H1_TRIGGER_WINDOW = 24      # scan up to 24 H1 bars (~1 day) after H4 signal for trigger
STOP_BUF = 0.10
STOP_FLOOR = 0.25
def wins(r): return max(-1.3, min(5.0, r))

def state_d_h1(B, i, d, sd, vr, cost):
    """STATE_D exit on the H1 stream (same R-tiers as cs.exit_state_d, H1 maxbars)."""
    return cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=H1_MAXBARS)

def h4_signals():
    """Audited H4 commodity signals for XAUUSD: (t, d, sd_h4, i_h4, B_h4, vr, cost)."""
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

def h1_trigger_entry(Tl, Bl, start_idx, d, window):
    """Find first H1 retest-continuation trigger from start_idx within `window` bars.
    Returns (entry_idx, stop_dist) or None. No lookahead: uses closed H1 bars only."""
    end = min(start_idx + window, len(Bl) - 1)
    for j in range(start_idx + 1, end + 1):
        a = atr14(Bl, j)
        if a <= 0: continue
        b = Bl[j]; pb = Bl[j-1]
        if d > 0:
            if b.l < pb.l and b.c > b.o and b.c > pb.c:   # pullback then up-close
                swing_low = min(b.l, pb.l)
                sd = max((b.c - swing_low) + STOP_BUF*a, STOP_FLOOR*a)
                return j, sd
        else:
            if b.h > pb.h and b.c < b.o and b.c < pb.c:
                swing_high = max(b.h, pb.h)
                sd = max((swing_high - b.c) + STOP_BUF*a, STOP_FLOOR*a)
                return j, sd
    return None

def run():
    sigs = h4_signals()
    Tl, Bl = m.load_ltf(SYM, "H1")
    base = []      # H4-close entry, H4 STATE_D  (the audited baseline)
    varA = []      # H1 trigger-timed entry, H1 STATE_D
    varB = []      # H1 immediate entry (tighter stop only), H1 STATE_D
    no_h1 = 0
    for (t, d, sd_h4, i_h4, B_h4, vr, cost) in sigs:
        # baseline outcome on H4
        rb = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)
        base.append((t.year, rb['R']))
        # H1 actionable instant = signal bar close = T_h4[i]+4h
        ts_close = t + __import__('datetime').timedelta(hours=4)
        si = m.first_ltf_index_after(Tl, ts_close)
        if si is None or si < 30 or si >= len(Bl)-2:
            no_h1 += 1; continue
        # Variant B: immediate H1 entry with H1-structural stop
        aB = atr14(Bl, si)
        if aB > 0:
            sdB = max(STOP_FLOOR*aB, 0.5*aB)   # H1-tight stop ~ 0.5 H1 ATR
            rB = state_d_h1(Bl, si, d, sdB, vr, cost)
            varB.append((t.year, rB['R']))
        # Variant A: wait for H1 trigger
        trig = h1_trigger_entry(Tl, Bl, si, d, H1_TRIGGER_WINDOW)
        if trig is not None:
            j, sdA = trig
            rA = state_d_h1(Bl, j, d, sdA, vr, cost)
            varA.append((t.year, rA['R']))
    return base, varA, varB, no_h1

def report(name, rows):
    yr = collections.defaultdict(list)
    for y, r in rows: yr[y].append(r)
    print(f"\n=== {name} (n={len(rows)}) ===")
    for y in sorted(yr):
        v = yr[y]; print(f"  {y}: n={len(v):>3} R/t={sum(v)/len(v):+.3f} win={100*sum(1 for x in v if x>0)/len(v):.0f}%")
    fwd = [r for y, r in rows if y >= 2025]
    tr = [r for y, r in rows if y <= 2024]
    if tr: print(f"  TRAIN<=2024: n={len(tr)} R/t={sum(tr)/len(tr):+.3f}")
    if fwd: print(f"  FWD 2025-26: n={len(fwd)} R/t={sum(fwd)/len(fwd):+.3f} win={100*sum(1 for x in fwd if x>0)/len(fwd):.0f}% ~{len(fwd)/1.5:.0f}/yr")
    return yr

if __name__ == "__main__":
    base, varA, varB, no_h1 = run()
    print(f"H4 signals with no H1 coverage: {no_h1}")
    report("BASELINE H4-close entry, H4 STATE_D", base)
    report("VAR_A  H1 trigger-timed, H1 STATE_D", varA)
    report("VAR_B  H1 immediate (tight stop), H1 STATE_D", varB)
