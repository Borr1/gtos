"""mtf_refine EXP7 — M15 BETTER-FILL on the full 6-metals basket (finer than H1).

Confirmed locked edge (EXP3): H1 better-fill, H4-width stop -> FWD 2025-26 +1.129R (vs base
+0.865R), 85.7% win, freq preserved by fallback. Question here: does FINER granularity (M15)
capture pullbacks that H1 misses, lifting EV further AND filling more signals (fewer fallbacks)?

Rule per H4 signal (audited core set, identical to EXP3):
  - after H4 signal bar closes, wait up to W M15 bars for a pullback that improves the fill by
    >= mi*ATR_m15 vs the signal-bar close.
  - if filled: enter there with stop = H4-width sd_h4 (SAME risk unit), STATE_D exit on M15
    (maxbars=1280 = 320h wall-clock, matched to H4 maxbars=80).
  - if not filled within W OR no M15 coverage: FALL BACK to baseline H4 outcome (never skip).
Wall-clock window matched to the H1 locked rule: H1 W=12 bars = 12h. On M15 that is 48 bars.
We sweep W in M15-bar units around that and mi in ATR_m15 units. Threshold chosen on TRAIN
(year<=2024, where only XAUUSD/XAGUSD have deep/early M15); FWD 2025-26 reported separately,
per-year and per-symbol.

NO LOOKAHEAD: H4 signal actionable only from t+4h; M15 entry from first M15 bar >= t+4h;
outcomes via cs.exit_state_d on the M15 stream (leak-free). Leak check emitted.
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
M15_MAXBARS = 1280   # 320h wall-clock, matched to H4 maxbars=80
LEAK = collections.Counter()

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

def better_fill(Bl, si, d, signal_close, window, min_imp):
    end = min(si + window, len(Bl) - 1)
    limit = signal_close - min_imp if d > 0 else signal_close + min_imp
    for j in range(si, end + 1):
        b = Bl[j]
        if d > 0 and b.l <= limit: return j
        if d < 0 and b.h >= limit: return j
    return None

def run(window, min_improve_atr, tf="M15"):
    base = []; mtf = []; cov = collections.Counter()
    for sym in METALS:
        sigs = h4_signals(sym)
        Tl, Bl = m.load_ltf(sym, tf)
        have = len(Bl) > 50
        for (t, d, sd_h4, i_h4, B_h4, vr, cost) in sigs:
            rb = cs.exit_state_d(B_h4, i_h4, d, sd_h4, vr, cost)
            base.append((t.year, rb['R']))
            if not have:
                mtf.append((t.year, rb['R'])); cov['fallback_nocov'] += 1; continue
            ts_close = t + datetime.timedelta(hours=4)
            si = m.first_ltf_index_after(Tl, ts_close)
            if si is None or si < 30 or si >= len(Bl)-2:
                mtf.append((t.year, rb['R'])); cov['fallback_nocov'] += 1; continue
            if Tl[si] < ts_close: LEAK['before_close'] += 1
            a1 = atr14(Bl, si); min_imp = min_improve_atr * a1 if a1 > 0 else 0.0
            ej = better_fill(Bl, si, d, B_h4[i_h4].c, window, min_imp)
            if ej is None:
                mtf.append((t.year, rb['R'])); cov['fallback_nofill'] += 1
            else:
                r = cs.exit_state_d(Bl, ej, d, sd_h4, vr, cost, maxbars=M15_MAXBARS)
                mtf.append((t.year, r['R'])); cov['better'] += 1
    return base, mtf, cov

def summ(rows):
    yr = collections.defaultdict(list)
    for y, r in rows: yr[y].append(r)
    peryr = {y: [len(v), round(sum(v)/len(v), 3)] for y, v in sorted(yr.items())}
    fwd = [r for y, r in rows if y >= 2025]; tr = [r for y, r in rows if y <= 2024]
    return {"per_year": peryr,
            "train": [len(tr), round(sum(tr)/len(tr), 4) if tr else None,
                      round(100*sum(1 for x in tr if x > 0)/len(tr), 1) if tr else None],
            "fwd": [len(fwd), round(sum(fwd)/len(fwd), 4) if fwd else None,
                    round(100*sum(1 for x in fwd if x > 0)/len(fwd), 1) if fwd else None]}

if __name__ == "__main__":
    base, _, _ = run(48, 1.0)
    print("BASELINE 6-metals (H4):", json.dumps(summ(base)))
    out = {"baseline": summ(base), "variants": {}}
    # M15 windows around 48 bars (=12h, matching H1 W=12); mi in ATR_m15 units
    for w in (24, 48, 96, 144):
        for mi in (0.25, 0.5, 1.0):
            b, mtf, cov = run(w, mi, "M15")
            s = summ(mtf); s['cov'] = dict(cov)
            out["variants"][f"W{w}_mi{mi}"] = s
            print(f"M15 W={w:>3} mi={mi}: train={s['train']} fwd={s['fwd']} cov={dict(cov)}")
    out["leak"] = dict(LEAK)
    (HERE/"MTF_REFINE_EXP7.json").write_text(json.dumps(out, indent=1))
    print("LEAK:", dict(LEAK))
    print("wrote MTF_REFINE_EXP7.json")
