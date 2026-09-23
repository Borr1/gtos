"""TW track — transfer the H1->M15 CASCADE better-fill (KB_multitf, multitf_lib) to the crypto
and energy sleeves. After an H4 signal bar CLOSES, wait up to W_h1 H1 bars for a pullback that
improves the fill by >= mi*ATR_h1 vs the signal close (long: H1 low <= sc - mi*ATR_h1; short
mirror). Enter at that price with the SAME H4-width structural stop (same risk unit). If H1 finds
nothing, scan up to W_m15 M15 bars for a pullback >= mi*ATR_m15. Only THEN fall back to H4.
Never skip a signal (frequency preserved). Exit replicated on the LTF stream.

Cascade order: H1 fill -> (if none) M15 fill -> (if none) H4 fallback.
Wall-clock horizon matched to H4 maxbars=80 (=320h): H1=320 bars, M15=1280 bars.

DATA HONESTY: crypto (BTC/DASH) and energy (USOIL/NATGAS/HEATOIL) LTF is FORWARD-ONLY
(2025-06+). Unlike XAUUSD metals (deep H1 2015+), there is NO pre-2025 OOS for the better-fill
mechanic here. So the cascade transfer can be validated FORWARD ONLY for these sleeves; the
metals causal pre-2025 proof (+0.416R lift on genuine OOS) is the cross-class evidence the
mechanic is not a forward-only artifact. We report this confound explicitly.

NO LOOKAHEAD: H4 signal actionable t+4h; LTF entry uses only closed LTF bars >= t+4h
(first_ltf_index_after binary search). Per-bar leak audit included.
"""
import sys, json, datetime, collections, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import atr14
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import energy_agri_sleeve as ea
import multitf_lib as m
from EXEC_exit_variants import sim_exit, wins

DATA = str(ROOT) + "/data/mt5_research_exports"

# Extend the LTF path map for crypto + energy (forward-only 2025-06+).
m.LTF_PATHS.update({
    ("BTCUSD", "H1"):  [DATA + "/bridge_ftmo_htf_20250601_20260610/BTCUSD_H1.csv"],
    ("BTCUSD", "M15"): [DATA + "/bridge_ftmo_m15_20250601_20260610/BTCUSD_M15.csv"],
    ("DASHUSD", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/DASHUSD_H1.csv"],
    ("DASHUSD", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/DASHUSD_M15.csv"],
    ("USOIL_cash", "H1"):  [DATA + "/bridge_ftmo_htf_20250601_20260610/USOIL_cash_H1.csv"],
    ("USOIL_cash", "M15"): [DATA + "/bridge_ftmo_m15_20250601_20260610/USOIL_cash_M15.csv"],
    ("NATGAS_cash", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/NATGAS_cash_H1.csv"],
    ("NATGAS_cash", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/NATGAS_cash_M15.csv"],
    ("HEATOIL_c", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/HEATOIL_c_H1.csv"],
    ("HEATOIL_c", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/HEATOIL_c_M15.csv"],
})

H1_MAXBARS = 320; M15_MAXBARS = 1280
W_H1 = 12; W_M15 = 48; MI = 1.0


def find_fill(Bl, si, d, signal_close, window, mi):
    """First LTF bar index in [si, si+window] whose extreme improves the fill by >= mi*ATR."""
    end = min(si + window, len(Bl) - 1)
    a1 = atr14(Bl, si); imp = mi * a1 if a1 > 0 else 0.0
    limit = signal_close - imp if d > 0 else signal_close + imp
    for j in range(si, end + 1):
        b = Bl[j]
        if d > 0 and b.l <= limit: return j
        if d < 0 and b.h >= limit: return j
    return None


def _exit_on_stream(B, ej, d, sd, vr, cost, maxbars, exit_name):
    """Apply the chosen exit policy to an entry at index ej on stream B, using sd as risk unit.
    exit policies: state_d, combo, lock, target4."""
    ent = dict(B=B, i=ej, d=d, sd=sd, vr=vr, cost=cost)
    if exit_name == 'state_d':
        if vr < 1.35:   scaleR, runR = 1.5, 4.0
        elif vr < 1.6:  scaleR, runR = 1.5, 3.0
        else:           scaleR, runR = 1.0, 2.5
        return sim_exit(ent, ladder=[(scaleR, 0.5)], be_after_first=0.0, runner_R=runR, maxbars=maxbars)['R']
    if exit_name == 'combo':
        if vr < 1.35:   be, runR = 0.25, 4.0
        elif vr < 1.6:  be, runR = 0.50, 3.0
        else:           be, runR = 0.75, 2.5
        return sim_exit(ent, ladder=[(2.0, 0.5)], be_after_first=be, runner_R=runR, maxbars=maxbars)['R']
    if exit_name == 'lock':
        if vr < 1.35:   scaleR, runR, be = 1.5, 4.0, 0.0
        elif vr < 1.6:  scaleR, runR, be = 1.5, 3.0, 0.5
        else:           scaleR, runR, be = 1.0, 2.5, 0.75
        return sim_exit(ent, ladder=[(scaleR, 0.5)], be_after_first=be, runner_R=runR, maxbars=maxbars)['R']
    if exit_name == 'target4':
        from geometry_lib import simulate
        return wins(simulate(B, ej, d, stop_dist=sd, target_dist=4.0*sd, cost=cost, maxbars=maxbars))
    raise ValueError(exit_name)


def run_cascade(sleeve, exit_name):
    """sleeve = list of dicts(sym, year, date, i, d, sd, vr, cost, B, T). Returns per-signal rows:
    base_R (H4 exit), casc_R (cascade fill + exit on LTF stream), src, leak_flag."""
    rows = []; leaks = 0; ltf_audit = 0
    # group entries by symbol to load LTF once
    bysym = collections.defaultdict(list)
    for e in sleeve: bysym[e['sym']].append(e)
    for sym, ents in bysym.items():
        T1, B1 = m.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = m.load_ltf(sym, "M15"); have15 = len(B15) > 50
        # H4 maxbars for base exit
        for e in ents:
            B_h4 = e['B']; i_h4 = e['i']; d = e['d']; sd = e['sd']; vr = e['vr']; cost = e['cost']
            t = e['T'][i_h4]
            base_R = _exit_on_stream(B_h4, i_h4, d, sd, vr, cost, 80, exit_name)
            ts = t + datetime.timedelta(hours=4); sc = B_h4[i_h4].c
            casc_R = base_R; src = "h4"
            # H1 leg
            filled = False
            if have1:
                si = m.first_ltf_index_after(T1, ts)
                if si is not None and 30 <= si < len(B1)-2:
                    ltf_audit += 1
                    if T1[si] < ts: leaks += 1  # must be >= signal close instant
                    ej = find_fill(B1, si, d, sc, W_H1, MI)
                    if ej is not None:
                        if T1[ej] < ts: leaks += 1
                        casc_R = _exit_on_stream(B1, ej, d, sd, vr, cost, H1_MAXBARS, exit_name)
                        src = "h1"; filled = True
            # M15 leg (only if H1 didn't fill)
            if not filled and have15:
                si = m.first_ltf_index_after(T15, ts)
                if si is not None and 30 <= si < len(B15)-2:
                    if T15[si] < ts: leaks += 1
                    ej = find_fill(B15, si, d, sc, W_M15, MI)
                    if ej is not None:
                        if T15[ej] < ts: leaks += 1
                        casc_R = _exit_on_stream(B15, ej, d, sd, vr, cost, M15_MAXBARS, exit_name)
                        src = "m15"
            rows.append(dict(sym=sym, year=e['year'], date=e['date'], vr=vr,
                             base_R=base_R, casc_R=casc_R, src=src))
    return rows, leaks, ltf_audit


# ---- sleeve entry builders carrying T (timestamps) for the LTF mapping ----
def crypto_sleeve():
    KEEP = ['BTCUSD', 'DASHUSD']; ents = []
    for s in KEEP:
        T, B = w1.load(s)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(s); n = len(B)
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            hh = max(B[k].h for k in range(i-20, i)); ll = min(B[k].l for k in range(i-20, i))
            d = 0
            if B[i].c > hh: d = +1
            elif B[i].c < ll: d = -1
            if d == 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.15: continue
            ents.append(dict(sym=s, year=T[i].year, date=str(T[i])[:10], i=i, d=d, sd=2.0*a,
                             vr=cs.vol_ratio(atrs, i), cost=cost, B=B, T=T))
    return ents


def energy_sleeve():
    ents = []
    for s in ea.ENERGY:
        try: T, B = w1.load(s)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; base_cost = w1.cost_for(s)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
            vr = cs.vol_ratio(atrs, i); slope = ea.trend_slope(B, i, 30)
            if not ((vr >= 2.0) or (abs(slope) < 0.05)): continue
            a = atrs[i] if atrs[i] > 0 else sd
            cost_scaled = base_cost * (0.5*a/sd) if sd > 0 else base_cost
            ents.append(dict(sym=s, year=t.year, date=str(t)[:10], i=i, d=d, sd=sd, vr=vr,
                             cost=cost_scaled, B=B, T=T))
    return ents
