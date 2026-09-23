"""KB7 — tick-measured execution truth for the highest-EV tick-serviceable sleeves.

Replays each clean covered trade (metals_core XAU/XAG-USD, energy_agri USOIL/UKOIL/NATGAS/HEATOIL)
at TICK resolution and measures the TRUE erosion vs the modeled (cost-map) R and the M1 estimate.

Coverage reality (probed on the live bridge):
  - metals XAUUSD/XAGUSD : ticks serviceable (fast). XAU/XAG-EUR/AUD crosses: NOT on the bridge.
  - energy USOIL/UKOIL/NATGAS/HEATOIL.cash/.c : ticks serviceable (fast).
  - crypto BTCUSD/DASHUSD : copy_ticks_range hangs / returns 0 -> NOT tick-serviceable. The M1
    estimate (-0.030R) remains the best available number for crypto; reported as such.

Method (no lookahead; entries unchanged):
  metals: market entry at the first tick at/after the H4 signal-bar close. Long fills at ASK,
          short at BID. EXEC_COMBO exit (scale 2R + vol-band lock + vol-band runner) replayed on
          the tick quotes (exit closing-side quote: long sells at BID, short buys at ASK).
  energy: cascade limit entry (H1 then M15 leg). The limit fills at the limit price the instant the
          correct tick quote touches it; if not touched in the cascade window -> H4 market fallback
          (entry at first tick after signal close). STATE_D ladder exit replayed on ticks.

Three erosion measurements per trade:
  modeled_R        : the book's bar-model R (cost-map net).            [reference]
  m1_R             : the EXEC_REALISM M1 estimate (next-M1-open + 0.5*cost stop buffer). [reference]
  tick_R_costmap   : tick fills, then subtract the SAME cost map -> apples-to-apples vs modeled_R.
                     (isolates pure FILL realism: entry/stop/limit price vs the bar model.)
  tick_R_realspread: tick fills charging the REAL observed entry+exit spread, with commission-only
                     residual of the cost map added back -> the honest live number.

erosion_tick = tick_R_costmap - modeled_R   (the like-for-like execution erosion)
"""
from __future__ import annotations
import sys, json, collections
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))

from geometry_lib import atr14
import wave1_structure_setups_ict as w1
import multitf_lib as mtf
from EXEC_exit_variants import build_entries, sim_exit, wins
import TW_mtf_cascade_transfer as TW
import KB7_tick_lib as TK

DATA = str(ROOT) + "/data/mt5_research_exports"
# extend cascade LTF map (same as reconcile)
mtf.LTF_PATHS.update({
    ("USOIL_cash", "H1"):  [DATA + "/bridge_ftmo_htf_20250601_20260610/USOIL_cash_H1.csv"],
    ("USOIL_cash", "M15"): [DATA + "/bridge_ftmo_m15_20250601_20260610/USOIL_cash_M15.csv"],
    ("NATGAS_cash", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/NATGAS_cash_H1.csv"],
    ("NATGAS_cash", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/NATGAS_cash_M15.csv"],
    ("HEATOIL_c", "H1"):  [DATA + "/bridge_ftmo_ext_htf_20250601_20260611/HEATOIL_c_H1.csv"],
    ("HEATOIL_c", "M15"): [DATA + "/bridge_ftmo_ext_m15_20250601_20260611/HEATOIL_c_M15.csv"],
})

TICK_SYMS_METALS = {"XAUUSD", "XAGUSD"}
TICK_SYMS_ENERGY = {"USOIL_cash", "UKOIL_cash", "NATGAS_cash", "HEATOIL_c"}

# commission-only residual: w1.cost_for embeds round-trip (spread+commission) in R. We estimate the
# commission fraction conservatively at 0 for these instruments (CFD/cash usually spread-only); so
# tick_R_realspread = tick fills with REAL spread and NO extra cost. If a venue charges commission,
# this is optimistic by that amount; reported in the note.
COMMISSION_R = {s: 0.0 for s in (TICK_SYMS_METALS | TICK_SYMS_ENERGY)}

WALL_MIN_H4 = 80 * 4 * 60  # H4 maxbars wall-clock minutes


def combo_params(vr):
    if vr < 1.35:   return (2.0, 0.25, 4.0)
    elif vr < 1.6:  return (2.0, 0.50, 3.0)
    else:           return (2.0, 0.75, 2.5)


def _ts_ms(dt):
    return int(dt.timestamp() * 1000)


def _pull_stream(sym, start_dt, end_dt):
    return TK.load_window_stream(sym, start_dt, end_dt)


def reconcile_metals_tick():
    ents = build_entries()
    rows = []
    for e in ents:
        sym = e['sym']
        if sym not in TICK_SYMS_METALS:
            continue
        B_h4 = e['B']; i = e['i']; d = e['d']; sd = e['sd']; vr = e['vr']
        cost = e['cost']; year = e['year']; date = e['date']
        scaleR, be, runR = combo_params(vr)
        modeled = sim_exit(dict(B=B_h4, i=i, d=d, sd=sd, vr=vr, cost=cost),
                           ladder=[(scaleR, 0.5)], be_after_first=be, runner_R=runR, maxbars=80)['R']
        Th4, _ = w1.load(sym)
        sig_close = Th4[i] + timedelta(hours=4)
        if sig_close.tzinfo is None:
            sig_close = sig_close.replace(tzinfo=timezone.utc)
        # exit horizon end = signal close + maxbars wall-clock (cap the tick pull at +20 days)
        horizon_end = sig_close + timedelta(minutes=WALL_MIN_H4)
        pull_end = min(horizon_end, sig_close + timedelta(days=20))
        import time as _t; _t0 = _t.time()
        ts = _pull_stream(sym, sig_close - timedelta(minutes=5), pull_end)
        print(f"  metals {sym} {date}: nticks={0 if ts is None else len(ts)} "
              f"({_t.time()-_t0:.1f}s)", flush=True)
        if ts is None:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, modeled=modeled,
                             tick=None, covered=False, reason="no_tick"))
            continue
        si = ts.first_at_or_after(_ts_ms(sig_close))
        if si is None or si >= len(ts) - 5:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, modeled=modeled,
                             tick=None, covered=False, reason="no_tick_at_entry"))
            continue
        entry_px, half_sp = TK.entry_fill(ts, si, d)
        end_ms = _ts_ms(horizon_end)
        res = TK.tick_exit(ts, si, entry_px, d, sd,
                           ladder=[(scaleR, 0.5)], be_after_first=be, runner_R=runR, end_ms=end_ms)
        # tick_R_costmap: subtract the model cost map (apples vs modeled). entry already paid real
        #   spread (ASK/BID) -> to compare to the model which DID embed spread in cost, we DON'T
        #   double charge: costmap variant subtracts (cost - real_entry_spread_R) so total spread
        #   charged once. We approximate by: gross tick R, then subtract full cost map (the model's
        #   own convention). This is conservative (charges spread ~twice) -> erosion upper bound.
        gross = res['R']
        tick_costmap = wins(gross - cost)
        # tick_R_realspread: entry spread already in entry_px; exit fills already on real quotes;
        #   so the ONLY extra cost is commission residual (0 here). Honest live number.
        entry_spread_R = (half_sp * 2.0) / sd if sd > 0 else 0.0  # round-trip spread already in fills
        tick_real = wins(gross - COMMISSION_R.get(sym, 0.0))
        rows.append(dict(sym=sym, year=year, date=date, vr=vr, modeled=round(modeled, 4),
                         tick_costmap=round(tick_costmap, 4), tick_real=round(tick_real, 4),
                         entry_spread_R=round(entry_spread_R, 4), reason=res['reason'],
                         n_legs=res['n_legs'], covered=True, n_ticks=len(ts)))
    return rows


def reconcile_energy_tick():
    ents = TW.energy_sleeve()
    rows = []
    for e in ents:
        sym = e['sym']
        if sym not in TICK_SYMS_ENERGY:
            continue
        B_h4 = e['B']; Th4 = e['T']; i = e['i']; d = e['d']; sd = e['sd']
        vr = e['vr']; cost = e['cost']; year = e['year']; date = e['date']
        sc = B_h4[i].c
        sig_close = Th4[i] + timedelta(hours=4)
        if sig_close.tzinfo is None:
            sig_close = sig_close.replace(tzinfo=timezone.utc)
        # modeled cascade R
        casc_modeled = TW._exit_on_stream(B_h4, i, d, sd, vr, cost, 80, "state_d"); src = "h4"
        limit_px = None; filled = False
        T1, B1 = mtf.load_ltf(sym, "H1"); have1 = len(B1) > 50
        T15, B15 = mtf.load_ltf(sym, "M15"); have15 = len(B15) > 50
        if have1:
            sidx = mtf.first_ltf_index_after(T1, sig_close.replace(tzinfo=None))
            if sidx is not None and 30 <= sidx < len(B1) - 2:
                ej = TW.find_fill(B1, sidx, d, sc, TW.W_H1, TW.MI)
                if ej is not None:
                    casc_modeled = TW._exit_on_stream(B1, ej, d, sd, vr, cost, TW.H1_MAXBARS, "state_d")
                    a1 = atr14(B1, sidx); limit_px = (sc - TW.MI*a1 if d > 0 else sc + TW.MI*a1)
                    filled = True; src = "h1"
        if not filled and have15:
            sidx = mtf.first_ltf_index_after(T15, sig_close.replace(tzinfo=None))
            if sidx is not None and 30 <= sidx < len(B15) - 2:
                ej = TW.find_fill(B15, sidx, d, sc, TW.W_M15, TW.MI)
                if ej is not None:
                    casc_modeled = TW._exit_on_stream(B15, ej, d, sd, vr, cost, TW.M15_MAXBARS, "state_d")
                    a1 = atr14(B15, sidx); limit_px = (sc - TW.MI*a1 if d > 0 else sc + TW.MI*a1)
                    filled = True; src = "m15"
        casc_modeled = wins(casc_modeled)
        # tick pull window: from signal close to horizon end (cap 20d)
        horizon_end = sig_close + timedelta(minutes=WALL_MIN_H4)
        pull_end = min(horizon_end, sig_close + timedelta(days=20))
        import time as _t; _t0 = _t.time()
        ts = _pull_stream(sym, sig_close - timedelta(minutes=5), pull_end)
        print(f"  energy {sym} {date}: nticks={0 if ts is None else len(ts)} "
              f"({_t.time()-_t0:.1f}s)", flush=True)
        if ts is None:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                             modeled=casc_modeled, tick=None, covered=False, reason="no_tick"))
            continue
        si0 = ts.first_at_or_after(_ts_ms(sig_close))
        if si0 is None or si0 >= len(ts) - 5:
            rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                             modeled=casc_modeled, tick=None, covered=False, reason="no_tick_at_entry"))
            continue
        no_fill = False
        if filled and limit_px is not None:
            # find first tick where the correct quote touches the limit within cascade window (12h)
            casc_end_ms = _ts_ms(sig_close + timedelta(hours=12))
            fill_i = None
            j = si0
            while j < len(ts) and ts.ms[j] <= casc_end_ms:
                # limit BUY (long) fills when ASK<=limit; limit SELL (short) when BID>=limit
                q = ts.ask[j] if d > 0 else ts.bid[j]
                if (d > 0 and q <= limit_px) or (d < 0 and q >= limit_px):
                    fill_i = j; break
                j += 1
            if fill_i is None:
                no_fill = True
                entry_px, _ = TK.entry_fill(ts, si0, d); fill_i = si0   # H4 market fallback
            else:
                entry_px = limit_px   # limit fills at the limit price (live limit semantics)
        else:
            entry_px, _ = TK.entry_fill(ts, si0, d); fill_i = si0
        # STATE_D ladder params
        if vr < 1.35:   scaleR, rr = 1.5, 4.0
        elif vr < 1.6:  scaleR, rr = 1.5, 3.0
        else:           scaleR, rr = 1.0, 2.5
        end_ms = _ts_ms(horizon_end)
        res = TK.tick_exit(ts, fill_i, entry_px, d, sd,
                           ladder=[(scaleR, 0.5)], be_after_first=0.0, runner_R=rr, end_ms=end_ms)
        gross = res['R']
        tick_costmap = wins(gross - cost)
        tick_real = wins(gross - COMMISSION_R.get(sym, 0.0))
        half_sp = (ts.ask[si0] - ts.bid[si0]) / 2.0
        entry_spread_R = (half_sp * 2.0) / sd if sd > 0 else 0.0
        rows.append(dict(sym=sym, year=year, date=date, vr=vr, src=src,
                         modeled=casc_modeled, tick_costmap=round(tick_costmap, 4),
                         tick_real=round(tick_real, 4), entry_spread_R=round(entry_spread_R, 4),
                         reason=res['reason'], n_legs=res['n_legs'], covered=True,
                         cascade_no_fill=no_fill, n_ticks=len(ts)))
    return rows


def block(rs, key="tick_costmap"):
    rs = [r for r in rs if r.get('covered')]
    if not rs:
        return None
    mod = [r['modeled'] for r in rs]
    tk = [r[key] for r in rs]
    ero = [r[key] - r['modeled'] for r in rs]
    esr = [r.get('entry_spread_R', 0.0) for r in rs]
    return dict(n=len(rs),
                modeled_ev=round(sum(mod)/len(mod), 4),
                tick_ev=round(sum(tk)/len(tk), 4),
                erosion_ev=round(sum(ero)/len(ero), 4),
                tick_win=round(100*sum(1 for x in tk if x > 0)/len(rs), 1),
                worst_erosion=round(min(ero), 4),
                mean_entry_spread_R=round(sum(esr)/len(esr), 4))


def summarize(rows, name):
    cov = [r for r in rows if r.get('covered')]
    out = {"sleeve": name, "n_total": len(rows), "n_covered": len(cov),
           "n_uncovered": len(rows) - len(cov),
           "costmap": block(cov, "tick_costmap"),
           "realspread": block(cov, "tick_real")}
    for y in (2024, 2025, 2026):
        b = block([r for r in cov if r['year'] == y], "tick_costmap")
        if b:
            out[f"y{y}_costmap"] = b
    bysym = collections.defaultdict(list)
    for r in cov:
        bysym[r['sym']].append(r)
    out["per_symbol_costmap"] = {s: block(rs, "tick_costmap") for s, rs in sorted(bysym.items())}
    return out


if __name__ == "__main__":
    result = {}
    print("=== metals_core (tick) ===", flush=True)
    rm = reconcile_metals_tick()
    result["metals_core"] = summarize(rm, "metals_core")
    print(json.dumps(result["metals_core"].get("costmap"), indent=0), flush=True)
    print("=== energy_agri (tick) ===", flush=True)
    re = reconcile_energy_tick()
    result["energy_agri"] = summarize(re, "energy_agri")
    print(json.dumps(result["energy_agri"].get("costmap"), indent=0), flush=True)
    with open(HERE / "KB7_TICK_TRUTH_RESULT.json", "w") as f:
        json.dump(result, f, indent=1)
    with open(HERE / "KB7_TICK_TRUTH_LEDGER.jsonl", "w") as f:
        for nm, rs in (("metals_core", rm), ("energy_agri", re)):
            for r in rs:
                r2 = dict(r); r2["sleeve"] = nm
                f.write(json.dumps(r2) + "\n")
    print("WROTE KB7_TICK_TRUTH_RESULT.json + KB7_TICK_TRUTH_LEDGER.jsonl", flush=True)
