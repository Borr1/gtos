"""csb_commodity_setups.py  (track key: csb = commodity setup breadth)

Goal: add BREADTH OF ENTRY TRIGGERS on the commodity core (metals + energy) beyond the
confirmed FVG-retest. Four new triggers, each:
  - signal computed ONLY from closed bars index<=i (no lookahead),
  - gated by the SAME momentum-persistence regime cs.autocorr(ac60>=0.10),
  - managed by the SAME exit cs.exit_state_d (vol-tiered scale-out),
  - filled by leak-free geometry_lib via cs.exit_state_d.

New triggers:
  OB   order-block retest      : last opposite-color candle before an impulse, retest+hold.
  BRK  breakout-retest         : break a prior swing level, pull back to it, reclaim.
  DISP displacement continuation: large-range impulse bar (range>=k*atr), enter the first
                                  shallow pullback close in trend direction.
  SWP  liquidity-sweep-reclaim : sweep a recent swing extreme (stops run) then close back
                                  through it, continuation in trend direction.

Baseline to beat/extend: FVG metals ac60 gate + exit_state_d = +0.865R fwd 25-26, 78% win.
Reporting: per-YEAR and FORWARD-HOLDOUT (train<=2024, fwd 2025 & 2026) always. Real cost.
Winsorize via cs.wins (exit_state_d already winsorizes). Deep symbols (XAUUSD/XAGUSD/USOIL)
carry the forward-holdout integrity; recent-only symbols add breadth/frequency.
"""
from __future__ import annotations
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs

METALS = cs.METALS
ENERGY = cs.ENERGY
CORE = METALS + ENERGY
AC_THR = 0.10
# symbols with deep (pre-2025) history -> carry forward-holdout proof
DEEP = {"XAUUSD", "XAGUSD", "USOIL_cash"}

def _atrs(B):
    return [atr14(B, i) for i in range(len(B))]

# vol-expansion gate identical to g.fvg_signals (the gate doing heavy lifting in the baseline)
GATE_K = 1.2
def vol_gate_ok(A, i, gate_k=GATE_K):
    if i < 100: return False
    a = A[i]
    if a <= 0: return False
    sma100 = sum(A[i-99:i+1]) / 100
    return sma100 > 0 and a >= gate_k * sma100

# ---------------------------------------------------------------------------
# helpers: swing pivots from CLOSED bars only (no lookahead)
# A pivot-high at index p needs `left` bars before AND `right` bars after, all <= i.
# We only ever query pivots fully formed at index <= i-1.
# ---------------------------------------------------------------------------
def last_pivot_high(B, i, left=2, right=2, lookback=40):
    """Most recent confirmed swing high strictly before bar i (fully closed)."""
    best = None
    for p in range(i-1-right, max(i-1-right-lookback, left), -1):
        seg = B[p-left:p+right+1]
        if not seg: continue
        if B[p].h == max(b.h for b in seg) and all(B[p].h >= b.h for b in seg):
            # strict-ish local max (allow ties on equal but require it to be the peak)
            return B[p].h, p
    return None, None

def last_pivot_low(B, i, left=2, right=2, lookback=40):
    for p in range(i-1-right, max(i-1-right-lookback, left), -1):
        seg = B[p-left:p+right+1]
        if not seg: continue
        if B[p].l == min(b.l for b in seg) and all(B[p].l <= b.l for b in seg):
            return B[p].l, p
    return None, None

# ===========================================================================
# SETUP 1: ORDER-BLOCK RETEST (continuation in HTF trend)
# last opposite-color candle before the impulse; price retests its body and holds.
# ===========================================================================
def sig_ob(sym, trend_lb=30, stop_buf=0.10, atr_stop_floor=0.25, ob_lookback=9,
           use_vol_gate=True):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    A = _atrs(B); cost = w1.cost_for(sym); out = []
    for i in range(60, len(B)-1):
        a = A[i]
        if a <= 0: continue
        if use_vol_gate and not vol_gate_ok(A, i): continue
        tr = w1.htf_trend(B, i, trend_lb); b = B[i]
        if tr == 1:
            for k in range(i-2, max(i-ob_lookback, 60), -1):
                if not (B[k].c < B[k].o): continue          # down (bullish OB) candle
                # impulse up after the OB (next bar closes above OB high)
                if not (B[k+1].c > B[k].h): continue
                ob_top, ob_bot = B[k].h, B[k].l
                # retest: current bar dips into OB zone and closes back up bullishly
                if b.l <= ob_top and b.c > ob_bot and b.c > b.o:
                    sd = max((b.c - min(b.l, ob_bot)) + stop_buf*a, atr_stop_floor*a)
                    out.append((T[i], +1, sd, i, B, cost)); break
        elif tr == -1:
            for k in range(i-2, max(i-ob_lookback, 60), -1):
                if not (B[k].c > B[k].o): continue           # up (bearish OB) candle
                if not (B[k+1].c < B[k].l): continue
                ob_top, ob_bot = B[k].h, B[k].l
                if b.h >= ob_bot and b.c < ob_top and b.c < b.o:
                    sd = max((max(b.h, ob_top) - b.c) + stop_buf*a, atr_stop_floor*a)
                    out.append((T[i], -1, sd, i, B, cost)); break
    return out

# ===========================================================================
# SETUP 2: BREAKOUT-RETEST (pullback to a broken swing level, reclaim)
# Price breaks a confirmed prior swing level, then pulls back to it and reclaims.
# ===========================================================================
def sig_brk(sym, trend_lb=30, stop_buf=0.10, atr_stop_floor=0.25,
            brk_min=0.10, retest_lookback=8, use_vol_gate=True):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    A = _atrs(B); cost = w1.cost_for(sym); out = []
    for i in range(60, len(B)-1):
        a = A[i]
        if a <= 0: continue
        if use_vol_gate and not vol_gate_ok(A, i): continue
        tr = w1.htf_trend(B, i, trend_lb); b = B[i]
        if tr == 1:
            ph, pp = last_pivot_high(B, i)
            if ph is None: continue
            # a break must have happened recently: some bar in (pp, i) closed above ph by brk_min*atr
            broke = any(B[j].c > ph + brk_min*a for j in range(pp+1, i))
            if not broke: continue
            # retest: current bar dips back to/below the level then closes back above it bullishly
            if b.l <= ph and b.c > ph and b.c > b.o:
                sd = max((b.c - b.l) + stop_buf*a, atr_stop_floor*a)
                out.append((T[i], +1, sd, i, B, cost))
        elif tr == -1:
            pl, pp = last_pivot_low(B, i)
            if pl is None: continue
            broke = any(B[j].c < pl - brk_min*a for j in range(pp+1, i))
            if not broke: continue
            if b.h >= pl and b.c < pl and b.c < b.o:
                sd = max((b.h - b.c) + stop_buf*a, atr_stop_floor*a)
                out.append((T[i], -1, sd, i, B, cost))
    return out

# ===========================================================================
# SETUP 3: DISPLACEMENT / RANGE-EXPANSION CONTINUATION
# A large-range impulse bar (range >= disp_k * atr) in trend direction, then the first
# shallow pullback bar that closes back in trend direction -> enter continuation.
# ===========================================================================
def sig_disp(sym, trend_lb=30, stop_buf=0.10, atr_stop_floor=0.25,
             disp_k=1.5, pull_lookback=4, use_vol_gate=True):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    A = _atrs(B); cost = w1.cost_for(sym); out = []
    for i in range(60, len(B)-1):
        a = A[i]
        if a <= 0: continue
        if use_vol_gate and not vol_gate_ok(A, i): continue
        tr = w1.htf_trend(B, i, trend_lb); b = B[i]
        if tr == 1:
            # find a recent displacement up bar in window
            for k in range(i-1, max(i-pull_lookback-1, 60), -1):
                rng = B[k].h - B[k].l
                if rng < disp_k*a: continue
                if not (B[k].c > B[k].o and B[k].c > B[k-1].c): continue   # bullish impulse
                # current bar i is a pullback that holds: low dips below prior close but closes back up
                if b.l < B[k].c and b.c > b.o and b.c >= B[k].o:
                    sd = max((b.c - b.l) + stop_buf*a, atr_stop_floor*a)
                    out.append((T[i], +1, sd, i, B, cost)); break
        elif tr == -1:
            for k in range(i-1, max(i-pull_lookback-1, 60), -1):
                rng = B[k].h - B[k].l
                if rng < disp_k*a: continue
                if not (B[k].c < B[k].o and B[k].c < B[k-1].c): continue
                if b.h > B[k].c and b.c < b.o and b.c <= B[k].o:
                    sd = max((b.h - b.c) + stop_buf*a, atr_stop_floor*a)
                    out.append((T[i], -1, sd, i, B, cost)); break
    return out

# ===========================================================================
# SETUP 4: LIQUIDITY-SWEEP-RECLAIM (continuation, trend-aligned)
# Sweep a recent swing extreme intrabar (run stops) then close back through it.
# Trend-aligned: in an uptrend we want a sweep of a recent swing LOW then reclaim (long).
# ===========================================================================
def sig_swp(sym, trend_lb=30, stop_buf=0.10, atr_stop_floor=0.25,
            sweep_min=0.05, reclaim_min=0.10, use_vol_gate=True):
    T, B = w1.load(sym)
    if len(B) < 200: return []
    A = _atrs(B); cost = w1.cost_for(sym); out = []
    for i in range(60, len(B)-1):
        a = A[i]
        if a <= 0: continue
        if use_vol_gate and not vol_gate_ok(A, i): continue
        tr = w1.htf_trend(B, i, trend_lb); b = B[i]
        if tr == 1:
            pl, pp = last_pivot_low(B, i)
            if pl is None: continue
            if (pl - b.l) >= sweep_min*a and b.c > pl and (b.c - pl) >= reclaim_min*a and b.c > b.o:
                sd = max((b.c - b.l) + stop_buf*a, atr_stop_floor*a)
                out.append((T[i], +1, sd, i, B, cost))
        elif tr == -1:
            ph, pp = last_pivot_high(B, i)
            if ph is None: continue
            if (b.h - ph) >= sweep_min*a and b.c < ph and (ph - b.c) >= reclaim_min*a and b.c < b.o:
                sd = max((b.h - b.c) + stop_buf*a, atr_stop_floor*a)
                out.append((T[i], -1, sd, i, B, cost))
    return out

SETUPS = {"OB": sig_ob, "BRK": sig_brk, "DISP": sig_disp, "SWP": sig_swp,
          "FVG": None}  # FVG handled via g.fvg_signals

# ---------------------------------------------------------------------------
def gated_trades(setup_name, syms):
    """Apply ac60>=0.10 gate + exit_state_d. Returns rows of dicts."""
    rows = []
    for s in syms:
        T, B = w1.load(s)
        if len(B) < 200: continue
        A = _atrs(B); cost = w1.cost_for(s)
        if setup_name == "FVG":
            sigs = [(t, d, sd, i, B2, c2) for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s)]
        else:
            sigs = SETUPS[setup_name](s)
        for (t, d, sd, i, B2, c2) in sigs:
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < AC_THR: continue
            vr = cs.vol_ratio(A, i)
            ex = cs.exit_state_d(B, i, d, sd, vr, c2)
            rows.append(dict(sym=s, year=t.year, date=str(t)[:10], dir=d,
                             ac60=round(ac, 4), vr=round(vr, 3),
                             R=round(ex['R'], 4), reason=ex['reason'],
                             mfe=round(ex['mfe'], 3), bars1R=ex['bars1R'],
                             deep=(s in DEEP)))
    return rows

def stat(rs):
    if not rs: return (0, 0.0, 0.0)
    n = len(rs); m = sum(r['R'] for r in rs)/n; w = sum(1 for r in rs if r['R'] > 0)/n*100
    return n, round(m, 4), round(w, 1)

def per_year_str(rows):
    by = collections.defaultdict(list)
    for r in rows: by[r['year']].append(r)
    parts = []
    for y in sorted(by):
        n, m, w = stat(by[y])
        parts.append(f"{y}:{m:+.2f}(n{n})")
    return " ".join(parts)

def summarize(name, rows):
    n, m, w = stat(rows)
    train = [r for r in rows if r['year'] <= 2024]
    fwd = [r for r in rows if r['year'] >= 2025]
    f25 = [r for r in rows if r['year'] == 2025]
    f26 = [r for r in rows if r['year'] == 2026]
    # deep-only forward (clean holdout)
    fwd_deep = [r for r in fwd if r['deep']]
    tr_n, tr_m, tr_w = stat(train)
    fw_n, fw_m, fw_w = stat(fwd)
    d = dict(name=name, n=n, all_EV=m, all_win=w,
             train=dict(n=tr_n, EV=tr_m, win=tr_w),
             fwd_all=dict(n=fw_n, EV=fw_m, win=fw_w),
             fwd_2025=dict(n=stat(f25)[0], EV=stat(f25)[1], win=stat(f25)[2]),
             fwd_2026=dict(n=stat(f26)[0], EV=stat(f26)[1], win=stat(f26)[2]),
             fwd_deep_only=dict(n=stat(fwd_deep)[0], EV=stat(fwd_deep)[1], win=stat(fwd_deep)[2]),
             per_year=per_year_str(rows),
             trades_per_year_fwd=round(fw_n/1.5, 1))
    return d

def main():
    results = {}
    print("="*78)
    print("COMMODITY SETUP BREADTH — each gated ac60>=0.10 + exit_state_d, metals+energy")
    print("="*78)
    # baseline FVG for anchor
    for name in ["FVG", "OB", "BRK", "DISP", "SWP"]:
        rows = gated_trades(name, CORE)
        results[name] = dict(summary=summarize(name, rows), rows=rows)
        s = results[name]['summary']
        print(f"\n--- {name} (n={s['n']}) ---")
        print(f"  TRAIN<=24: n={s['train']['n']:3d} EV={s['train']['EV']:+.3f} win={s['train']['win']:.0f}%")
        print(f"  FWD 25-26: n={s['fwd_all']['n']:3d} EV={s['fwd_all']['EV']:+.3f} win={s['fwd_all']['win']:.0f}%  (~{s['trades_per_year_fwd']}/yr)")
        print(f"    2025: n={s['fwd_2025']['n']:3d} EV={s['fwd_2025']['EV']:+.3f}  2026: n={s['fwd_2026']['n']:3d} EV={s['fwd_2026']['EV']:+.3f}")
        print(f"    fwd DEEP-only (clean holdout): n={s['fwd_deep_only']['n']:3d} EV={s['fwd_deep_only']['EV']:+.3f} win={s['fwd_deep_only']['win']:.0f}%")
        print(f"    per-year: {s['per_year']}")

    # combined NEW setups (dedupe identical sym+date+dir keeping best? -> count all, report overlap)
    new_names = ["OB", "BRK", "DISP", "SWP"]
    allnew = []
    seen = set()
    dupes = 0
    for name in new_names:
        for r in results[name]['rows']:
            key = (r['sym'], r['date'], r['dir'])
            if key in seen:
                dupes += 1
                continue
            seen.add(key); rr = dict(r); rr['setup'] = name; allnew.append(rr)
    s = summarize("NEW_COMBINED_dedup", allnew)
    results['NEW_COMBINED'] = dict(summary=s, n_dupes_removed=dupes)
    print(f"\n=== NEW SETUPS COMBINED (dedup sym+date+dir, {dupes} dupes removed) ===")
    print(f"  TRAIN<=24: n={s['train']['n']:3d} EV={s['train']['EV']:+.3f} win={s['train']['win']:.0f}%")
    print(f"  FWD 25-26: n={s['fwd_all']['n']:3d} EV={s['fwd_all']['EV']:+.3f} win={s['fwd_all']['win']:.0f}%  (~{s['trades_per_year_fwd']}/yr)")
    print(f"    fwd DEEP-only: n={s['fwd_deep_only']['n']:3d} EV={s['fwd_deep_only']['EV']:+.3f} win={s['fwd_deep_only']['win']:.0f}%")
    print(f"    per-year: {s['per_year']}")

    # FVG + all new combined (the full breadth portfolio)
    allcombo = list(allnew)
    for r in results['FVG']['rows']:
        key = (r['sym'], r['date'], r['dir'])
        if key in seen: continue
        seen.add(key); rr = dict(r); rr['setup'] = 'FVG'; allcombo.append(rr)
    s = summarize("FVG_PLUS_NEW", allcombo)
    results['FVG_PLUS_NEW'] = dict(summary=s)
    print(f"\n=== FULL BREADTH (FVG + 4 new, dedup) ===")
    print(f"  TRAIN<=24: n={s['train']['n']:3d} EV={s['train']['EV']:+.3f} win={s['train']['win']:.0f}%")
    print(f"  FWD 25-26: n={s['fwd_all']['n']:3d} EV={s['fwd_all']['EV']:+.3f} win={s['fwd_all']['win']:.0f}%  (~{s['trades_per_year_fwd']}/yr)")
    print(f"    2025: n={s['fwd_2025']['n']:3d} EV={s['fwd_2025']['EV']:+.3f}  2026: n={s['fwd_2026']['n']:3d} EV={s['fwd_2026']['EV']:+.3f}")
    print(f"    fwd DEEP-only: n={s['fwd_deep_only']['n']:3d} EV={s['fwd_deep_only']['EV']:+.3f} win={s['fwd_deep_only']['win']:.0f}%")
    print(f"    per-year: {s['per_year']}")

    # strip rows for json compactness
    out = {k: (v['summary'] if 'summary' in v else v) for k, v in results.items()}
    (HERE/'CSB_COMMODITY_SETUPS_RESULT.json').write_text(json.dumps(out, indent=1))
    print("\nwrote CSB_COMMODITY_SETUPS_RESULT.json")

if __name__ == "__main__":
    main()
