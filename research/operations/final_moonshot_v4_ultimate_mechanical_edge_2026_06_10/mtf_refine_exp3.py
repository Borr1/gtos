"""mtf_refine EXP3 — FULL 6-METALS basket better-fill, H1-timed, H4-width stop.

The real confirmed edge is the 6-metals basket (forward n=49, +0.865R). XAUUSD-only forward
n is too small (5) to judge. Other metals have H1 forward-only (2025-06+), which is EXACTLY
the forward-holdout window, so H1 refinement is forward-validatable on the whole basket.

Rule per H4 signal (audited: FVG-retest + ac60>=0.10 + vol gate):
  - after H4 signal bar closes, wait up to W H1 bars for a pullback that improves the fill by
    >= min_improve*ATR_h1 (long: H1 low <= signal_close - min_improve).
  - if filled: enter there with stop = H4-width sd_h4 (SAME risk unit), STATE_D exit on H1.
  - if not filled within W: FALL BACK to baseline H4 outcome (never skip a signal -> keeps freq).
Forward holdout: choose min_improve & W on metals where deep H1 is unavailable we still get
forward coverage; we pick the parameter on the FULL-basket TRAIN then report FWD separately.
For non-XAUUSD metals H1 exists only 2025-06+, so their TRAIN rows fall back to H4 (honest).
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

METALS = cs.METALS
H1_MAXBARS = 320
def wins(r): return max(-1.3, min(5.0, r))

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
    base = []; mtf = []
    cov = collections.Counter()   # 'better', 'fallback_nofill', 'fallback_nocov'
    for sym in METALS:
        sigs = h4_signals(sym)
        Tl, Bl = m.load_ltf(sym, "H1")
        have_h1 = len(Bl) > 50
        for (t, d, sd_h4, i_h4, B_h4, vr, cost) in sigs:
            rb = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)
            base.append((t.year, rb['R']))
            if not have_h1:
                mtf.append((t.year, rb['R'])); cov['fallback_nocov'] += 1; continue
            ts_close = t + datetime.timedelta(hours=4)
            si = m.first_ltf_index_after(Tl, ts_close)
            if si is None or si < 30 or si >= len(Bl)-2:
                mtf.append((t.year, rb['R'])); cov['fallback_nocov'] += 1; continue
            a1 = atr14(Bl, si); min_imp = min_improve_atr * a1 if a1 > 0 else 0.0
            ej = better_fill(Bl, si, d, B_h4[i_h4].c, window, min_imp)
            if ej is None:
                mtf.append((t.year, rb['R'])); cov['fallback_nofill'] += 1
            else:
                r = cs.exit_state_d(Bl, ej, d, sd_h4, vr, cost, maxbars=H1_MAXBARS)
                mtf.append((t.year, r['R'])); cov['better'] += 1
    return base, mtf, cov

def summ(rows):
    yr = collections.defaultdict(list)
    for y, r in rows: yr[y].append(r)
    peryr = {y: (len(v), round(sum(v)/len(v), 3)) for y, v in sorted(yr.items())}
    fwd = [r for y, r in rows if y >= 2025]; tr = [r for y, r in rows if y <= 2024]
    return {
        "per_year": peryr,
        "train": (len(tr), round(sum(tr)/len(tr), 4) if tr else None),
        "fwd": (len(fwd), round(sum(fwd)/len(fwd), 4) if fwd else None,
                round(100*sum(1 for x in fwd if x > 0)/len(fwd), 1) if fwd else None),
    }

if __name__ == "__main__":
    base, _, _ = run(12, 0.5)
    print("BASELINE 6-metals:", json.dumps(summ(base)))
    out = {}
    for w in (6, 12, 24):
        for mi in (0.25, 0.5, 1.0):
            b, mtf, cov = run(w, mi)
            s = summ(mtf); s['cov'] = dict(cov)
            out[f"W{w}_mi{mi}"] = s
            print(f"W={w:>2} mi={mi}: train={s['train']} fwd={s['fwd']} cov={dict(cov)}")
    (HERE / "MTF_REFINE_EXP3.json").write_text(json.dumps({"baseline": summ(base), "variants": out}, indent=1))
