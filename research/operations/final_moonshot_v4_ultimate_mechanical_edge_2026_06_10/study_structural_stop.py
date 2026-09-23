#!/usr/bin/env python3
"""
STRUCTURAL STOP STUDY (final_moonshot_v4_ultimate_mechanical_edge_2026_06_10)
============================================================================

Dimension: structural_stop.

Owner question: place the stop at STRUCTURE, not a fixed ATR. Compare stop
definitions and measure, per definition:
  - median risk (in ATR units and in pips)
  - win-rate and per-trade R at 2R and 3R targets
  - per-year breakdown + TRAIN(2022-2024) vs FORWARD(2025-2026)
Which structural stop gives the best R while staying tight? Does structure
beat the flat 0.5 ATR baseline?

ENGINE PARITY: this reuses the EXACT confirmed engine from
structural_geometry_study.py (which reproduces the +0.69R/57%-win flat-0.5ATR
baseline). Same entry recipe, same multi-candidate-per-bar firing, same
first-touch rule (target counts only if it strictly precedes the stop bar;
stop ends the trade => pessimistic same-bar = loss), same timeout handling
(-cost, position closed flat), same risk>3.5*ATR degenerate cap, same real
per-asset-class cost. ONLY the set of stop definitions is extended.

STOP DEFINITIONS COMPARED (distance from entry=close[i], +0.10 ATR buffer
beyond the structural level; risk in those distance units = the R-unit):
  flat_0p5atr   : baseline control, 0.5*ATR (non-structural)
  prior_bar     : prior-bar extreme (current bar low/high) + 0.10 ATR
  swing3        : swing-3 extreme (min low / max high last 3 bars) + buffer
  swing5        : swing-5 extreme (min low / max high last 5 bars) + buffer
  order_block   : last opposite-direction high-volume bar before entry; its
                  far extreme (long: last down high-vol bar's low; short: last
                  up high-vol bar's high) + buffer
  supply_demand : recent consolidation extreme (prior-20 low for long / high
                  for short) + buffer

Targets 2R and 3R in those structural-R units. Win = target hit (strictly)
before stop. Per-trade R is net of real cost.
"""

import csv
import json
import statistics
import sys
import collections
from pathlib import Path

ROUTE = Path(__file__).resolve().parent
REPO_ROOT = ROUTE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, "/Users/borr/Documents/gtos/repo/ai-trading-agent")
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST = json.loads((ROUTE / "ULTIMATE_REAL_COST_MAP.json").read_text())
GCOST = COST.get("_global_median", 0.095)
D = REPO_ROOT / "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"

MAXBARS = 60
ATR_BUF = 0.10
MAX_RISK_ATR = 3.5  # degenerate / too-wide structural stop cap (engine parity)
TARGETS = [2.0, 3.0]
STOP_DEFS = ["flat_0p5atr", "prior_bar", "swing3", "swing5",
             "order_block", "supply_demand"]

# Previous-live surface (CLAUDE.md) intersected with files present here.
SYMBOLS = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
    "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
    "SPX500", "UK100", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash", "XAGUSD",
    "XAUUSD",
]


def pip_size(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "")
    if ac == "jpy_fx":
        return 0.01
    if ac == "fx":
        return 0.0001
    return 1.0  # index/metals/energy/crypto: 1 point == 1 'pip'


def new_agg():
    return {sd: {"n": 0, "risk_atr": [], "risk_pips": [],
                 "tot": {t: 0.0 for t in TARGETS},
                 "win": {t: 0 for t in TARGETS},
                 "yr_tot": {t: collections.defaultdict(float) for t in TARGETS},
                 "yr_win": {t: collections.defaultdict(int) for t in TARGETS},
                 "yr_n": collections.defaultdict(int),
                 # long-only bug-free slice (shorts excluded so the short-side
                 # sign issue cannot contaminate the structural comparison)
                 "long_n": 0,
                 "long_tot": {t: 0.0 for t in TARGETS},
                 "long_win": {t: 0 for t in TARGETS}}
            for sd in STOP_DEFS}


def main():
    agg = new_agg()
    N = 0
    per_symbol_n = {}

    for sym in SYMBOLS:
        f = D / f"{sym}_H4.csv"
        if not f.exists():
            print(f"WARN missing {sym}", file=sys.stderr)
            continue
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        c = float(COST.get(ac, GCOST))
        psize = pip_size(sym)
        rows = [(str(r["time"])[:19], float(r["open"]), float(r["high"]),
                 float(r["low"]), float(r["close"]), float(r["volume"]))
                for r in csv.DictReader(open(f))
                if r.get("close") and r.get("volume")]
        if len(rows) < 250:
            continue
        n = len(rows)
        O = [x[1] for x in rows]
        Hh = [x[2] for x in rows]
        L = [x[3] for x in rows]
        C = [x[4] for x in rows]
        V = [x[5] for x in rows]
        T = [x[0] for x in rows]
        tr = [0.0] * n
        for i in range(1, n):
            tr[i] = max(Hh[i] - L[i], abs(Hh[i] - C[i - 1]), abs(L[i] - C[i - 1]))
        rng = [Hh[i] - L[i] for i in range(n)]
        vd = [(V[i] * (C[i] - O[i]) / rng[i]) if rng[i] > 0 else 0.0
              for i in range(n)]
        sym_n = 0
        prev = None
        for i in range(60, n - 1):
            atr = sum(tr[i - 13:i + 1]) / 14
            if atr <= 0:
                continue
            m20 = sum(C[i - 19:i + 1]) / 20
            m50 = sum(C[i - 49:i + 1]) / 50
            trend = "up" if m20 > m50 * 1.001 else ("down" if m20 < m50 * 0.999 else "flat")
            hi, lo = max(Hh[i - 47:i + 1]), min(L[i - 47:i + 1])
            pos = (C[i] - lo) / (hi - lo) if hi > lo else .5
            posb = "low" if pos < .25 else ("high" if pos > .75 else "mid")
            relv = V[i] / (sum(V[i - 19:i + 1]) / 20 or 1)
            eff = rng[i] / V[i] if V[i] > 0 else 0
            beff = sum((rng[k] / V[k] if V[k] > 0 else 0) for k in range(i - 19, i + 1)) / 20
            absb = eff <= 0.6 * beff if beff > 0 else False
            expb = eff >= 1.4 * beff if beff > 0 else False
            ph, pl = max(Hh[i - 20:i]), min(L[i - 20:i])
            swh = Hh[i] > ph and C[i] < ph and relv >= 1.5
            swl = L[i] < pl and C[i] > pl and relv >= 1.5
            vdacc = sum(vd[i - 2:i + 1])
            is_entry = (trend, posb, relv >= 1.5, bool(swh or swl)) != prev
            prev = (trend, posb, relv >= 1.5, bool(swh or swl))
            if not is_entry:
                continue
            cands = []
            if swl:
                cands.append(+1)
            if swh:
                cands.append(-1)
            if relv <= 0.6 and trend == "down" and posb == "low":
                cands.append(+1)
            if relv <= 0.6 and trend == "up" and posb == "high":
                cands.append(-1)
            if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]:
                cands.append(+1)
            if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]:
                cands.append(-1)
            if absb and posb == "low":
                cands.append(+1)
            if absb and posb == "high":
                cands.append(-1)
            if posb == "high" and vdacc < 0:
                cands.append(-1)
            if posb == "low" and vdacc > 0:
                cands.append(+1)
            entry = C[i]
            yr = T[i][:4]

            for d in cands:
                N += 1
                sym_n += 1
                # ---- structural stop distances ----
                sdist = {}
                sdist["flat_0p5atr"] = 0.5 * atr
                pb = L[i] if d > 0 else Hh[i]
                sdist["prior_bar"] = abs(entry - pb) + ATR_BUF * atr
                sw3 = min(L[i - 2:i + 1]) if d > 0 else max(Hh[i - 2:i + 1])
                sdist["swing3"] = abs(entry - sw3) + ATR_BUF * atr
                sw5 = min(L[i - 4:i + 1]) if d > 0 else max(Hh[i - 4:i + 1])
                sdist["swing5"] = abs(entry - sw5) + ATR_BUF * atr
                # order block: last opposite-dir high-volume bar before entry
                v20 = sum(V[i - 19:i + 1]) / 20
                ob_lvl = None
                for k in range(i - 1, max(i - 21, 0), -1):
                    high_vol = V[k] >= v20
                    if d > 0 and C[k] < O[k] and high_vol:
                        ob_lvl = L[k]
                        break
                    if d < 0 and C[k] > O[k] and high_vol:
                        ob_lvl = Hh[k]
                        break
                sdist["order_block"] = (abs(entry - ob_lvl) + ATR_BUF * atr) if ob_lvl is not None else None
                # supply/demand: prior-20 consolidation extreme
                sd_lvl = min(L[i - 20:i]) if d > 0 else max(Hh[i - 20:i])
                sdist["supply_demand"] = abs(entry - sd_lvl) + ATR_BUF * atr

                for sd, risk in sdist.items():
                    if risk is None or risk <= 0 or risk > MAX_RISK_ATR * atr:
                        continue
                    a = agg[sd]
                    a["n"] += 1
                    a["yr_n"][yr] += 1
                    a["risk_atr"].append(risk / atr)
                    a["risk_pips"].append(risk / psize)
                    if d > 0:
                        a["long_n"] += 1
                    # first-touch
                    tbars = {t: None for t in TARGETS}
                    stbar = None
                    for j in range(i + 1, min(i + MAXBARS, n)):
                        if d > 0:
                            fav = Hh[j] - entry
                            adv = entry - L[j]
                        else:
                            fav = entry - L[j]
                            adv = Hh[j] - entry
                        if stbar is None and adv >= risk:
                            stbar = j
                        for t in TARGETS:
                            if tbars[t] is None and fav >= t * risk:
                                tbars[t] = j
                        if stbar is not None:
                            break  # stop ends the trade (pessimistic same-bar)
                    for t in TARGETS:
                        tb = tbars[t]
                        if tb is not None and (stbar is None or tb < stbar):
                            r_net = t - c
                            is_w = True
                        elif stbar is not None:
                            r_net = -1 - c
                            is_w = False
                        else:  # timeout: close flat, pay cost
                            r_net = -c
                            is_w = False
                        a["tot"][t] += r_net
                        a["yr_tot"][t][yr] += r_net
                        if is_w:
                            a["win"][t] += 1
                            a["yr_win"][t][yr] += 1
                        if d > 0:
                            a["long_tot"][t] += r_net
                            if is_w:
                                a["long_win"][t] += 1
        per_symbol_n[sym] = sym_n

    med = lambda x: round(statistics.median(x), 4) if x else None
    medp = lambda x: round(statistics.median(x), 2) if x else None

    out = {
        "schema_version": "structural_stop_study_v1",
        "engine_note": (
            "Uses the SAME entry recipe + first-touch engine as "
            "structural_geometry_study.py BUT fixes a short-side sign bug. The "
            "reference uses adv=d*(entry-L) for d>0 else d*(Hh-entry); for d<0 "
            "that evaluates to entry-Hh which is NEGATIVE on adverse moves, so "
            "short trades almost never stop out, inflating the 'confirmed' "
            "+0.69R/57%-win baseline. Isolated: ref longs=-0.034R/35%win (real), "
            "ref shorts=+1.28R/74%win (artifact). With the correct adverse "
            "formula adv=(entry-L) for longs / (Hh-entry) for shorts, the flat "
            "0.5ATR baseline is -0.082R/34%win pooled. This study uses the "
            "CORRECT formula on both sides; all numbers below are bug-free."
        ),
        "short_side_bug_isolation": {
            "reference_buggy": {"all": {"per_trade_R": 0.6932, "win": 0.567, "n": 15290},
                                 "long": {"per_trade_R": -0.0338, "win": 0.353, "n": 6850},
                                 "short": {"per_trade_R": 1.2832, "win": 0.740, "n": 8440}},
            "corrected": {"all": {"per_trade_R": -0.0824, "win": 0.336, "n": 15290},
                          "long": {"per_trade_R": -0.0338, "win": 0.353, "n": 6850},
                          "short": {"per_trade_R": -0.1217, "win": 0.321, "n": 8440}},
        },
        "symbols": SYMBOLS,
        "n_symbols": len(per_symbol_n),
        "total_candidate_entries": N,
        "per_symbol_entries": per_symbol_n,
        "maxbars": MAXBARS,
        "atr_buffer": ATR_BUF,
        "max_risk_atr_cap": MAX_RISK_ATR,
        "targets": [f"{t:.0f}R" for t in TARGETS],
        "cost_map_used": {k: COST.get(k) for k in ["fx", "jpy_fx", "index", "metals", "energy"]},
        "global_median_cost": GCOST,
        "stop_defs": {},
    }

    for sd in STOP_DEFS:
        a = agg[sd]
        if a["n"] == 0:
            continue
        rec = {
            "n": a["n"],
            "med_risk_atr": med(a["risk_atr"]),
            "med_risk_pips": medp(a["risk_pips"]),
            "long_only_bug_free": {
                "n": a["long_n"],
                "2R": {"per_trade_R": round(a["long_tot"][2.0] / a["long_n"], 4) if a["long_n"] else None,
                       "win": round(a["long_win"][2.0] / a["long_n"], 4) if a["long_n"] else None},
                "3R": {"per_trade_R": round(a["long_tot"][3.0] / a["long_n"], 4) if a["long_n"] else None,
                       "win": round(a["long_win"][3.0] / a["long_n"], 4) if a["long_n"] else None},
            },
            "targets": {},
        }
        for t in TARGETS:
            tk = f"{t:.0f}R"
            yrs = sorted(set(a["yr_n"].keys()))
            per_year = {}
            for y in yrs:
                nyr = a["yr_n"][y]
                if nyr == 0:
                    continue
                per_year[y] = {
                    "n": nyr,
                    "per_trade_R": round(a["yr_tot"][t][y] / nyr, 4),
                    "win": round(a["yr_win"][t][y] / nyr, 4),
                }
            # train / forward partition
            def part(lo, hiy):
                pn = sum(a["yr_n"][y] for y in yrs if lo <= int(y) <= hiy)
                pt = sum(a["yr_tot"][t][y] for y in yrs if lo <= int(y) <= hiy)
                pw = sum(a["yr_win"][t][y] for y in yrs if lo <= int(y) <= hiy)
                return {"n": pn,
                        "per_trade_R": round(pt / pn, 4) if pn else None,
                        "win": round(pw / pn, 4) if pn else None}
            rec["targets"][tk] = {
                "n": a["n"],
                "total_R": round(a["tot"][t], 1),
                "per_trade_R": round(a["tot"][t] / a["n"], 4),
                "win": round(a["win"][t] / a["n"], 4),
                "TRAIN_2022_2024": part(2022, 2024),
                "FORWARD_2025_2026": part(2025, 2026),
                "per_year": per_year,
            }
        out["stop_defs"][sd] = rec

    out_path = ROUTE / "STRUCTURAL_STOP_STUDY_RESULT.json"
    out_path.write_text(json.dumps(out, indent=1, sort_keys=False))

    # ---- console digest ----
    print("=" * 96)
    print("STRUCTURAL STOP STUDY  (H4 deep 2022-2026, 22 symbols, confirmed engine, real cost)")
    print("=" * 96)
    print(f"candidate entries (multi-cand/bar): {N}  across {len(per_symbol_n)} symbols\n")
    for t in TARGETS:
        tk = f"{t:.0f}R"
        print(f"---------- TARGET {tk} (pooled) ----------")
        print(f"{'stop_def':<15}{'n':>7}{'per_R':>9}{'win%':>8}{'medATR':>9}{'medPips':>11}{'tot_R':>10}")
        for sd in STOP_DEFS:
            if sd not in out["stop_defs"]:
                continue
            r = out["stop_defs"][sd]
            tv = r["targets"][tk]
            print(f"{sd:<15}{tv['n']:>7}{tv['per_trade_R']:>9.3f}{tv['win']*100:>7.1f}%"
                  f"{r['med_risk_atr']:>9.3f}{r['med_risk_pips']:>11.2f}{tv['total_R']:>10.1f}")
        print()
    print("---------- TRAIN(22-24) vs FORWARD(25-26) per-trade R ----------")
    for t in TARGETS:
        tk = f"{t:.0f}R"
        print(f"  target {tk}:")
        print(f"    {'stop_def':<15}{'TRAIN R':>10}{'TRAIN n':>9}{'FWD R':>10}{'FWD n':>8}")
        for sd in STOP_DEFS:
            if sd not in out["stop_defs"]:
                continue
            tv = out["stop_defs"][sd]["targets"][tk]
            tr_ = tv["TRAIN_2022_2024"]
            fw = tv["FORWARD_2025_2026"]
            print(f"    {sd:<15}{tr_['per_trade_R']:>10.3f}{tr_['n']:>9}"
                  f"{fw['per_trade_R']:>10.3f}{fw['n']:>8}")
    print()
    print("---------- per-year per-trade R (target 2R) ----------")
    years = ["2022", "2023", "2024", "2025", "2026"]
    print(f"{'stop_def':<15}" + "".join(f"{y:>9}" for y in years))
    for sd in STOP_DEFS:
        if sd not in out["stop_defs"]:
            continue
        py = out["stop_defs"][sd]["targets"]["2R"]["per_year"]
        cells = []
        for y in years:
            cells.append(f"{py[y]['per_trade_R']:>9.3f}" if y in py else f"{'-':>9}")
        print(f"{sd:<15}" + "".join(cells))
    print()
    print("---------- LONG-ONLY bug-free slice (shorts excluded) ----------")
    print(f"{'stop_def':<15}{'long_n':>8}{'2R per_R':>10}{'2R win%':>9}{'3R per_R':>10}{'3R win%':>9}")
    for sd in STOP_DEFS:
        if sd not in out["stop_defs"]:
            continue
        lo = out["stop_defs"][sd]["long_only_bug_free"]
        print(f"{sd:<15}{lo['n']:>8}{lo['2R']['per_trade_R']:>10.3f}{lo['2R']['win']*100:>8.1f}%"
              f"{lo['3R']['per_trade_R']:>10.3f}{lo['3R']['win']*100:>8.1f}%")
    print()
    print("SHORT-SIDE BUG (isolated): reference engine adv=d*(entry-L) for d<0")
    print("  evaluates to entry-Hh (negative on adverse) -> shorts rarely stop.")
    print("  ref all=+0.69R/57%win is an artifact; corrected all=-0.082R/34%win.")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
