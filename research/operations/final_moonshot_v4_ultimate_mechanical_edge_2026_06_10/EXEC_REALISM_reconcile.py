"""EXEC_REALISM driver — reconcile each deployed sleeve's MODELED R against M1-realistic R.

For every entry the book actually takes (same signal logic, unchanged), where M1 covers the
trade window we:
  1. Model the ENTRY exactly as the book does (H4-close, or cascade limit at sc-1*ATR), then
     replace it with the M1-realistic fill:
       - market (H4-close) entry  -> first M1 OPEN at/after signal-close + adverse spread/2
       - cascade LIMIT entry      -> fills at the LIMIT PRICE the instant M1 touches it (this is
         the live limit-order semantics; better than the modeled LTF-bar-close in most cases)
  2. Replace the modeled exit with the M1 intrabar exit (realistic_exit): scale/lock/target are
     limit fills at level; structural/lock stops take adverse slippage + any M1 gap.
  3. Score erosion = M1_R - modeled_R, per trade / per sleeve / per year, winsorized [-1.3,+5].

Sleeves covered (those with M1 coverage on the deciding symbols):
  - metals_core  : EXEC_COMBO exit (scale 2.0R + vol-band lock + vol-band runner target)
  - crypto       : target4 single fixed target + H1->M15 cascade limit fill
  - energy_agri  : STATE_D ladder + H1->M15 cascade limit fill
  - JPY / index  : fill-sensitivity probe (low-win sleeves) -- diagnostic only (conf 0.15 breadth)
"""
from __future__ import annotations
import sys, json, statistics, collections
from datetime import timedelta
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import energy_agri_sleeve as ea
import multitf_lib as mtf
from EXEC_exit_variants import sim_exit, wins, build_entries
import EXEC_REALISM_m1_lib as M1

# Extend LTF map for crypto/energy cascade (same as TW_mtf_cascade_transfer)
DATA = str(ROOT) + "/data/mt5_research_exports"
mtf.LTF_PATHS.update({
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

# ---- slippage model (avoids double-counting the spread already in the cost map) ----
# The book's modeled R is ALREADY net of round-trip cost (spread+commission) via w1.cost_for.
# So we do NOT re-add spread on the entry. The INCREMENTAL execution realism we charge is:
#   (1) entry at next-M1-OPEN instead of the (unfillable) signal-bar CLOSE  -> captured by using
#       Bm[fill_idx].o as the entry price (no added spread);
#   (2) STOP fills are market orders that cross beyond the touched level: charge a conservative
#       HALF of the per-symbol round-trip cost (in price) as a stop buffer, ON TOP of any M1 gap
#       (gap_fill already follows the M1 open if price gapped through the stop);
#   (3) take-profit / scale / runner-target are LIMIT fills at the level (no positive slippage).
# stop_buffer_px(sym, sd) = 0.5 * cost_R(sym) * sd  (half the round-trip spread, exit side only).
def stop_buffer_px(sym, sd):
    try:
        return 0.5 * w1.cost_for(sym) * sd
    except Exception:
        return 0.0

WALL_MIN_H4 = 80 * 4 * 60   # H4 maxbars=80 -> minutes of wall-clock = 19200 M1 bars (trading time)

def _wallclock_end_idx(Tm, Bm, Th4, i_h4, fill_idx):
    """M1 index whose time is at/after the H4 horizon end (Th4[i+80] + 4h), so the M1 exit
    horizon ends at the SAME wall-clock instant as the modeled H4 exit horizon. This removes
    the bar-count-vs-wall-clock mismatch (weekend/session gaps) from the erosion measurement."""
    end_h4 = min(i_h4 + 80, len(Th4) - 1)
    horizon_ts = Th4[end_h4] + timedelta(hours=4)
    j = M1.first_m1_after(Tm, horizon_ts)
    if j is None: j = len(Bm) - 1
    return max(fill_idx + 1, min(j, len(Bm) - 1))

GAP_TOL_MIN = 15   # if first M1 bar is >15min after the signal-close instant, the H4 fill bar
                   # spans an M1 data gap (broker daily-rollover) -> fills are unreliable; flag.

def _m1_window(sym, ts):
    """Return (T,B,start_idx,gap_min) where start_idx is first M1 at/after ts; None if no coverage.
    gap_min = minutes between ts and the first available M1 bar (0 == clean)."""
    T, B = M1.load_m1(sym)
    if not B: return None
    if ts < T[0] or ts > T[-1]: return None
    si = M1.first_m1_after(T, ts)
    if si is None or si >= len(B) - 5: return None
    gap_min = (T[si] - ts).total_seconds() / 60.0
    return (T, B, si, gap_min)

# --------------------------------------------------------------------------------------------
# METALS CORE — EXEC_COMBO exit on the fixed FVG+persistence entries, H4-close market entry.
# --------------------------------------------------------------------------------------------
def combo_params(vr):
    if vr < 1.35:   return (2.0, 0.25, 4.0)
    elif vr < 1.6:  return (2.0, 0.50, 3.0)
    else:           return (2.0, 0.75, 2.5)

def reconcile_metals():
    ents = build_entries()
    rows = []
    for e in ents:
        sym = e['sym']; B_h4 = e['B']; i = e['i']; d = e['d']; sd = e['sd']; vr = e['vr']
        cost = e['cost']; year = e['year']; date = e['date']
        # modeled R (EXEC_COMBO)
        scaleR, be, runR = combo_params(vr)
        modeled = sim_exit(dict(B=B_h4, i=i, d=d, sd=sd, vr=vr, cost=cost),
                           ladder=[(scaleR, 0.5)], be_after_first=be, runner_R=runR, maxbars=80)['R']
        # M1 entry: signal bar closes at T[i]+4h
        Th4, _ = w1.load(sym)
        sig_close_ts = Th4[i] + timedelta(hours=4)
        win = _m1_window(sym, sig_close_ts)
        if win is None:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, modeled=modeled,
                             m1=None, covered=False)); continue
        Tm, Bm, si, gap_min = win
        gapped = gap_min > GAP_TOL_MIN
        entry_px = Bm[si].o                            # market entry at next M1 open (cost in R)
        sp = stop_buffer_px(sym, sd)                   # exit-side half-spread on stops only
        eci = _wallclock_end_idx(Tm, Bm, Th4, i, si)
        res = M1.realistic_exit(Bm, si, entry_px, d, sd,
                                ladder=[(scaleR, 0.5)], be_after_first=be, runner_R=runR,
                                maxbars=WALL_MIN_H4, slip_px=sp, end_clock_idx=eci)
        m1R = wins(res['R'] - cost)
        rows.append(dict(sym=sym, year=year, date=date, vr=vr, modeled=modeled,
                         m1=m1R, reason=res['reason'], covered=True,
                         gap_min=round(gap_min, 1), gapped=gapped))
    return rows

# --------------------------------------------------------------------------------------------
# CASCADE sleeves (crypto target4, energy STATE_D) — limit fill + M1 exit.
# Reuses TW builders for the exact entry set, recomputes cascade fill index, then prices on M1.
# --------------------------------------------------------------------------------------------
import TW_mtf_cascade_transfer as TW

def _cascade_fill_ltf(sym, sig_close_ts, d, sc):
    """Replicate TW cascade fill: H1 leg then M15 leg. Return (ltf_tf, fill_ts, limit_px) or None."""
    for tf, window in (("H1", TW.W_H1), ("M15", TW.W_M15)):
        Tl, Bl = mtf.load_ltf(sym, tf)
        if len(Bl) <= 50: continue
        si = mtf.first_ltf_index_after(Tl, sig_close_ts)
        if si is None or not (30 <= si < len(Bl) - 2): continue
        a1 = atr14(Bl, si); imp = TW.MI * a1 if a1 > 0 else 0.0
        limit = sc - imp if d > 0 else sc + imp
        end = min(si + window, len(Bl) - 1)
        for j in range(si, end + 1):
            b = Bl[j]
            if (d > 0 and b.l <= limit) or (d < 0 and b.h >= limit):
                return (tf, Tl[j], limit)
        # H1 found nothing -> try M15 (only if H1 had coverage but no fill)
    return None

def reconcile_cascade(sleeve_name):
    if sleeve_name == "crypto":
        ents = TW.crypto_sleeve(); exit_name = "target4"; runR = 4.0
    elif sleeve_name == "energy":
        ents = TW.energy_sleeve(); exit_name = "state_d"; runR = None
    else:
        raise ValueError(sleeve_name)
    rows = []
    for e in ents:
        sym = e['sym']; B_h4 = e['B']; Th4 = e['T']; i = e['i']; d = e['d']; sd = e['sd']
        vr = e['vr']; cost = e['cost']; year = e['year']; date = e['date']
        sc = B_h4[i].c
        sig_close_ts = Th4[i] + timedelta(hours=4)
        # modeled cascade R (TW engine) — re-run to get the modeled number for THIS entry
        base_R = TW._exit_on_stream(B_h4, i, d, sd, vr, cost, 80, exit_name)
        casc_modeled = base_R; src = "h4"
        T1, B1 = mtf.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = mtf.load_ltf(sym, "M15"); have15 = len(B15) > 50
        filled = False; fill_ts = None; limit_px = None; ltf_tf = None
        if have1:
            si = mtf.first_ltf_index_after(T1, sig_close_ts)
            if si is not None and 30 <= si < len(B1) - 2:
                ej = TW.find_fill(B1, si, d, sc, TW.W_H1, TW.MI)
                if ej is not None:
                    casc_modeled = TW._exit_on_stream(B1, ej, d, sd, vr, cost, TW.H1_MAXBARS, exit_name)
                    src = "h1"; filled = True
                    a1 = atr14(B1, si); limit_px = sc - TW.MI*a1*d if False else (sc - TW.MI*a1 if d>0 else sc + TW.MI*a1)
                    fill_ts = T1[ej]; ltf_tf = "H1"
        if not filled and have15:
            si = mtf.first_ltf_index_after(T15, sig_close_ts)
            if si is not None and 30 <= si < len(B15) - 2:
                ej = TW.find_fill(B15, si, d, sc, TW.W_M15, TW.MI)
                if ej is not None:
                    casc_modeled = TW._exit_on_stream(B15, ej, d, sd, vr, cost, TW.M15_MAXBARS, exit_name)
                    src = "m15"; filled = True
                    a1 = atr14(B15, si); limit_px = (sc - TW.MI*a1 if d>0 else sc + TW.MI*a1)
                    fill_ts = T15[ej]; ltf_tf = "M15"
        # ---- M1 reconciliation ----
        # Cascade limit search window must match the MODEL's wall-clock: H1 leg waits W_H1=12 H1
        # bars (=12h) and M15 leg W_M15=48 M15 bars (=12h). On M1 that is 720 bars. If the limit
        # is not touched within that window on M1, the model would have fallen back to H4 -> we do
        # the same (H4 market entry, never skip the signal).
        CASCADE_WIN_M1 = 12 * 60   # 12h of M1 bars (both H1 and M15 legs use a 12h window)
        no_fill = False
        win = _m1_window(sym, sig_close_ts)
        if win is None:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                             modeled=wins(casc_modeled), m1=None, covered=False)); continue
        Tm, Bm, si0, gap_min = win
        gapped = gap_min > GAP_TOL_MIN
        if filled and fill_ts is not None and limit_px is not None:
            fill_idx = None
            end = min(si0 + CASCADE_WIN_M1, len(Bm) - 1)
            for j in range(si0, end + 1):
                b = Bm[j]
                if (d > 0 and b.l <= limit_px) or (d < 0 and b.h >= limit_px):
                    fill_idx = j; break
            if fill_idx is None:
                # limit not reached on M1 within the cascade window -> model falls back to H4.
                no_fill = True
                fill_idx = si0
                entry_px = Bm[si0].o                       # H4 market entry at signal close
            else:
                entry_px = limit_px      # limit fills AT the limit price (live limit semantics)
        else:
            fill_idx = si0
            entry_px = Bm[fill_idx].o                      # H4 market entry
        sp = stop_buffer_px(sym, sd)                       # exit-side half-spread on stops only
        eci = _wallclock_end_idx(Tm, Bm, Th4, i, fill_idx)
        if exit_name == "target4":
            res = M1.realistic_fixed_target(Bm, fill_idx, entry_px, d, sd,
                                            target_R=4.0, maxbars=WALL_MIN_H4, slip_px=sp,
                                            end_clock_idx=eci)
        else:  # state_d ladder
            if vr < 1.35:   scaleR, rr = 1.5, 4.0
            elif vr < 1.6:  scaleR, rr = 1.5, 3.0
            else:           scaleR, rr = 1.0, 2.5
            res = M1.realistic_exit(Bm, fill_idx, entry_px, d, sd,
                                    ladder=[(scaleR, 0.5)], be_after_first=0.0, runner_R=rr,
                                    maxbars=WALL_MIN_H4, slip_px=sp, end_clock_idx=eci)
        m1R = wins(res['R'] - cost)
        rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                         modeled=wins(casc_modeled), m1=m1R, reason=res['reason'], covered=True,
                         no_fill=(no_fill and src != "h4"),
                         cascade_missed=(no_fill and src != "h4"),
                         gap_min=round(gap_min, 1), gapped=gapped))
    return rows

# --------------------------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------------------------
def summarize(rows, name):
    cov = [r for r in rows if r.get('covered')]
    nocov = [r for r in rows if not r.get('covered')]
    out = {"sleeve": name, "n_total": len(rows), "n_m1_covered": len(cov),
           "n_uncovered": len(nocov)}
    def block(rs):
        if not rs: return None
        mod = [r['modeled'] for r in rs]
        m1 = [r['m1'] for r in rs]
        ero = [r['m1'] - r['modeled'] for r in rs]
        return dict(n=len(rs),
                    modeled_ev=round(sum(mod)/len(mod), 4),
                    m1_ev=round(sum(m1)/len(m1), 4),
                    erosion_ev=round(sum(ero)/len(ero), 4),
                    m1_win=round(100*sum(1 for x in m1 if x > 0)/len(rs), 1),
                    worst_erosion=round(min(ero), 4))
    clean = [r for r in cov if not r.get('gapped')]   # trustworthy: no M1 data-gap at the H4 fill bar
    gapped = [r for r in cov if r.get('gapped')]
    out["all_covered"] = block(cov)
    out["clean"] = block(clean)          # << the trustworthy erosion verdict
    out["gapped"] = block(gapped)        # M1 daily-rollover gap spans the H4 fill bar -> unreliable
    out["n_clean"] = len(clean); out["n_gapped"] = len(gapped)
    for y in (2024, 2025, 2026):
        out[f"y{y}_clean"] = block([r for r in clean if r['year'] == y])
    # per-symbol (clean only)
    bysym = collections.defaultdict(list)
    for r in clean: bysym[r['sym']].append(r)
    out["per_symbol_clean"] = {s: block(rs) for s, rs in sorted(bysym.items())}
    # cascade limit not reachable on M1 -> fell back to H4 market (lost the better-fill)
    out["n_cascade_missed"] = sum(1 for r in clean if r.get('cascade_missed'))
    out["n_limit_no_fill"] = out["n_cascade_missed"]
    return out

if __name__ == "__main__":
    import json
    result = {}
    print("=== metals_core (EXEC_COMBO) ===", flush=True)
    rm = reconcile_metals(); result["metals_core"] = summarize(rm, "metals_core")
    print("CLEAN:", json.dumps(result["metals_core"]["clean"]), flush=True)
    print("GAPPED:", json.dumps(result["metals_core"]["gapped"]), flush=True)
    print("=== crypto (target4 + cascade) ===", flush=True)
    rc = reconcile_cascade("crypto"); result["crypto"] = summarize(rc, "crypto")
    print("CLEAN:", json.dumps(result["crypto"]["clean"]), flush=True)
    print("=== energy (STATE_D + cascade) ===", flush=True)
    re = reconcile_cascade("energy"); result["energy_agri"] = summarize(re, "energy_agri")
    print("CLEAN:", json.dumps(result["energy_agri"]["clean"]), flush=True)
    with open(HERE / "EXEC_REALISM_RESULT.json", "w") as f:
        json.dump(result, f, indent=1)
    # per-trade ledger
    with open(HERE / "EXEC_REALISM_TRADE_LEDGER.jsonl", "w") as f:
        for nm, rs in (("metals_core", rm), ("crypto", rc), ("energy_agri", re)):
            for r in rs:
                r2 = dict(r); r2["sleeve"] = nm; f.write(json.dumps(r2) + "\n")
    print("WROTE EXEC_REALISM_RESULT.json + EXEC_REALISM_TRADE_LEDGER.jsonl", flush=True)
