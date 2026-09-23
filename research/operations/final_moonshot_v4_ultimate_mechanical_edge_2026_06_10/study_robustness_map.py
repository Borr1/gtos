#!/usr/bin/env python3
"""
ROBUSTNESS MAP / OVERFIT TEST for the V4 ultimate mechanical edge geometry.

Sweep stop in {0.3,0.4,0.5,0.6,0.75,1.0}*ATR  x  target in {1.5,2.0,2.5,3.0}R.

For each (stop_mult, target_R) cell:
  - run the SHARED ENTRY-DETECTION RECIPE on every symbol/year
  - simulate first-touch over <=60 bars, pessimistic same-bar (stop wins ties)
  - subtract real per-asset-class cost (cost is in R-units of the BASELINE 0.5*ATR
    stop; we re-scale cost to the cell's stop distance so an R is an R)
  - report per-trade R (cost-adjusted), win%, n_trades, and per-year sign

Question: is the positive region a BROAD CONTIGUOUS PLATEAU (real edge) or a
knife-edge (overfit)?  Map plateau boundaries + most-robust cell.

R-unit = the stop distance of THAT cell.
"""
import sys
import os
import json
import csv
import math
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
sys.path.insert(0, REPO)

from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa: E402

DATA_DIR = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP_PATH = os.path.join(
    REPO,
    "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_REAL_COST_MAP.json",
)

with open(COST_MAP_PATH) as f:
    COST_MAP = json.load(f)
GLOBAL_COST = COST_MAP.get("_global_median", 0.095)

# Universe = the previous-live surface (CLAUDE.md "Current Truth"), restricted to
# symbols present both as a data file and in ASSET_CLASS_BY_SYMBOL.
LIVE_SURFACE = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY", "EURUSD",
    "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD", "SPX500", "UK100",
    "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash",
    "XAGUSD", "XAUUSD",
]


def cost_for(symbol):
    ac = ASSET_CLASS_BY_SYMBOL.get(symbol)
    if ac is None:
        return GLOBAL_COST
    return COST_MAP.get(ac, GLOBAL_COST)


def load_bars(symbol):
    path = os.path.join(DATA_DIR, f"{symbol}_H4.csv")
    if not os.path.exists(path):
        return None
    t, O, H, L, C, V = [], [], [], [], [], []
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            t.append(row["time"])
            O.append(float(row["open"]))
            H.append(float(row["high"]))
            L.append(float(row["low"]))
            C.append(float(row["close"]))
            V.append(float(row["volume"]))
    return {"time": t, "O": O, "H": H, "L": L, "C": C, "V": V}


def sma(arr, i, n):
    if i + 1 < n:
        return None
    return sum(arr[i - n + 1 : i + 1]) / n


def true_range(H, L, C, i):
    if i == 0:
        return H[i] - L[i]
    return max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))


def year_of(ts):
    return int(ts[:4])


def detect_entries(bars):
    """SHARED ENTRY-DETECTION RECIPE. Returns list of (entry_idx, direction, year)."""
    O, H, L, C, V, T = bars["O"], bars["H"], bars["L"], bars["C"], bars["V"], bars["time"]
    n = len(C)

    tr = [true_range(H, L, C, i) for i in range(n)]

    entries = []
    prev_tuple = None

    # Precompute 20-bar mean efficiency rolling
    eff = [None] * n
    for i in range(n):
        rng = H[i] - L[i]
        if V[i] > 0:
            eff[i] = rng / V[i]
        else:
            eff[i] = 0.0

    for i in range(n):
        if i < 60:
            continue
        atr = sum(tr[i - 13 : i + 1]) / 14.0
        if atr <= 0:
            prev_tuple = None
            continue
        m20 = sma(C, i, 20)
        m50 = sma(C, i, 50)
        if m20 is None or m50 is None:
            continue
        if m20 > m50 * 1.001:
            trend = "up"
        elif m20 < m50 * 0.999:
            trend = "down"
        else:
            trend = "flat"

        # 48-bar range pos
        hi48 = max(H[i - 47 : i + 1])
        lo48 = min(L[i - 47 : i + 1])
        if hi48 > lo48:
            pos = (C[i] - lo48) / (hi48 - lo48)
        else:
            pos = 0.5
        if pos < 0.25:
            posb = "low"
        elif pos > 0.75:
            posb = "high"
        else:
            posb = "mid"

        v20 = sma(V, i, 20)
        relv = (V[i] / v20) if (v20 and v20 > 0) else 0.0

        # efficiency baseline (20-bar mean of eff)
        beff = sum(eff[i - 19 : i + 1]) / 20.0
        cur_eff = eff[i]
        absb = cur_eff <= 0.6 * beff
        expb = cur_eff >= 1.4 * beff

        # prior-20 high/low (bars i-20..i-1)
        ph = max(H[i - 20 : i])
        pl = min(L[i - 20 : i])
        swh = (H[i] > ph) and (C[i] < ph) and (relv >= 1.5)
        swl = (L[i] < pl) and (C[i] > pl) and (relv >= 1.5)

        # vdacc over last 3 bars
        vdacc = 0.0
        for j in range(i - 2, i + 1):
            rngj = H[j] - L[j]
            if rngj > 0:
                vdacc += V[j] * (C[j] - O[j]) / rngj

        low = posb == "low"
        high = posb == "high"
        down = trend == "down"
        up = trend == "up"

        swept = bool(swh or swl)
        cur_tuple = (trend, posb, relv >= 1.5, swept)
        fire = cur_tuple != prev_tuple
        prev_tuple = cur_tuple
        if not fire:
            continue

        # candidate directions
        d = None
        if swl:
            d = +1
        elif swh:
            d = -1
        elif relv <= 0.6 and down and low:
            d = +1
        elif relv <= 0.6 and up and high:
            d = -1
        elif relv >= 1.8 and expb and high and C[i] > O[i]:
            d = +1
        elif relv >= 1.8 and expb and low and C[i] < O[i]:
            d = -1
        elif absb and low:
            d = +1
        elif absb and high:
            d = -1
        elif high and vdacc < 0:
            d = -1
        elif low and vdacc > 0:
            d = +1

        if d is None:
            continue

        entries.append((i, d, atr, year_of(T[i])))

    return entries


def simulate_cell(bars, entries, stop_mult, target_R, raw_cost):
    """
    For a cell: stop = stop_mult*ATR, target = target_R * stop (R = stop dist).
    First-touch over <=60 bars, pessimistic same-bar (stop wins ties).
    Cost is supplied as baseline R (0.5*ATR stop). Re-scale to this cell's stop:
       cost_atr_units = raw_cost * 0.5          (cost in ATR)
       cost_this_R    = cost_atr_units / stop_mult
    Returns list of (R_result_after_cost, year, win_bool).
    """
    H, L, C = bars["H"], bars["L"], bars["C"]
    n = len(C)
    cost_atr = raw_cost * 0.5
    cost_R = cost_atr / stop_mult

    results = []
    for (i, d, atr, yr) in entries:
        entry_px = C[i]
        stop_dist = stop_mult * atr
        tgt_dist = target_R * stop_dist
        if d == +1:
            stop_px = entry_px - stop_dist
            tgt_px = entry_px + tgt_dist
        else:
            stop_px = entry_px + stop_dist
            tgt_px = entry_px - tgt_dist

        outcome = None  # R before cost
        end = min(i + 60, n - 1)
        for j in range(i + 1, end + 1):
            hi, lo = H[j], L[j]
            if d == +1:
                hit_stop = lo <= stop_px
                hit_tgt = hi >= tgt_px
            else:
                hit_stop = hi >= stop_px
                hit_tgt = lo <= tgt_px
            if hit_stop and hit_tgt:
                outcome = -1.0  # pessimistic: stop wins ties / same-bar
                break
            elif hit_stop:
                outcome = -1.0
                break
            elif hit_tgt:
                outcome = float(target_R)
                break
        if outcome is None:
            # no touch within 60 bars: mark-to-market at close of last bar
            last = C[end]
            if d == +1:
                outcome = (last - entry_px) / stop_dist
            else:
                outcome = (entry_px - last) / stop_dist

        results.append((outcome - cost_R, yr, outcome > 0))
    return results


def main():
    stop_mults = [0.3, 0.4, 0.5, 0.6, 0.75, 1.0]
    target_Rs = [1.5, 2.0, 2.5, 3.0]
    years = [2022, 2023, 2024, 2025, 2026]
    TRAIN = {2022, 2023, 2024}
    FORWARD = {2025, 2026}

    # Load + detect once per symbol (entry detection is geometry-independent)
    per_symbol = {}
    universe = []
    for sym in LIVE_SURFACE:
        bars = load_bars(sym)
        if bars is None:
            print(f"  [skip] {sym}: no data file", file=sys.stderr)
            continue
        ent = detect_entries(bars)
        per_symbol[sym] = (bars, ent, cost_for(sym))
        universe.append(sym)
    total_signals = sum(len(v[1]) for v in per_symbol.values())
    print(f"Universe: {len(universe)} symbols, {total_signals} raw entry signals")

    # cell -> aggregate
    cells = {}
    for sm in stop_mults:
        for tr in target_Rs:
            all_res = []
            for sym in universe:
                bars, ent, raw_cost = per_symbol[sym]
                all_res.extend(simulate_cell(bars, ent, sm, tr, raw_cost))
            n = len(all_res)
            mean_R = sum(r[0] for r in all_res) / n if n else 0.0
            wins = sum(1 for r in all_res if r[2])
            win_pct = wins / n if n else 0.0
            # per-year
            yr_R = {}
            yr_n = {}
            for (R, yr, w) in all_res:
                yr_R.setdefault(yr, 0.0)
                yr_n.setdefault(yr, 0)
                yr_R[yr] += R
                yr_n[yr] += 1
            yr_mean = {y: (yr_R[y] / yr_n[y]) for y in yr_R}
            yr_sign = {y: (1 if yr_mean.get(y, 0) > 0 else (0 if yr_mean.get(y, 0) == 0 else -1)) for y in years}
            train_res = [r[0] for r in all_res if r[1] in TRAIN]
            fwd_res = [r[0] for r in all_res if r[1] in FORWARD]
            train_mean = sum(train_res) / len(train_res) if train_res else 0.0
            fwd_mean = sum(fwd_res) / len(fwd_res) if fwd_res else 0.0
            n_pos_years = sum(1 for y in years if yr_sign[y] == 1)
            cells[(sm, tr)] = {
                "stop_mult": sm,
                "target_R": tr,
                "n_trades": n,
                "mean_R": mean_R,
                "win_pct": win_pct,
                "train_mean_R": train_mean,
                "forward_mean_R": fwd_mean,
                "year_mean_R": {str(y): round(yr_mean.get(y, float("nan")), 4) for y in years},
                "year_sign": {str(y): yr_sign[y] for y in years},
                "n_pos_years": n_pos_years,
            }

    # -------- Render grid --------
    print("\n=== PER-TRADE MEAN R (cost-adjusted), rows=stop*ATR, cols=target R ===")
    hdr = "stop\\tgt |" + "".join(f"{tr:>9.1f}R" for tr in target_Rs)
    print(hdr)
    print("-" * len(hdr))
    for sm in stop_mults:
        row = f"  {sm:>4.2f}  |"
        for tr in target_Rs:
            row += f"{cells[(sm,tr)]['mean_R']:>+10.4f}"
        print(row)

    print("\n=== N POSITIVE YEARS (out of 5: 2022-2026) ===")
    print(hdr)
    print("-" * len(hdr))
    for sm in stop_mults:
        row = f"  {sm:>4.2f}  |"
        for tr in target_Rs:
            row += f"{cells[(sm,tr)]['n_pos_years']:>10d}"
        print(row)

    print("\n=== FORWARD (2025-2026) MEAN R ===")
    print(hdr)
    print("-" * len(hdr))
    for sm in stop_mults:
        row = f"  {sm:>4.2f}  |"
        for tr in target_Rs:
            row += f"{cells[(sm,tr)]['forward_mean_R']:>+10.4f}"
        print(row)

    print("\n=== WIN % ===")
    print(hdr)
    print("-" * len(hdr))
    for sm in stop_mults:
        row = f"  {sm:>4.2f}  |"
        for tr in target_Rs:
            row += f"{cells[(sm,tr)]['win_pct']*100:>9.1f}%"
        print(row)

    # -------- Plateau analysis --------
    # "Positive cell" = mean_R > 0 AND all 5 years positive (the baseline standard)
    def is_plateau(c):
        return c["mean_R"] > 0 and c["n_pos_years"] == 5

    plateau_cells = [(sm, tr) for sm in stop_mults for tr in target_Rs if is_plateau(cells[(sm, tr)])]
    pos_meanR_cells = [(sm, tr) for sm in stop_mults for tr in target_Rs if cells[(sm, tr)]["mean_R"] > 0]

    print(f"\nCells with positive mean R: {len(pos_meanR_cells)} / {len(cells)}")
    print(f"Cells in STRICT plateau (mean R>0 AND all 5 years positive): {len(plateau_cells)} / {len(cells)}")
    print("Strict-plateau cells:", [(round(s, 2), t) for s, t in sorted(plateau_cells)])

    # Most robust cell = among strict-plateau cells, pick the one whose worst neighbor
    # (in the grid) is strongest, with high min-year R as tiebreak. This rewards
    # being in the MIDDLE of a good region rather than on a spike.
    def neighbors(sm, tr):
        si = stop_mults.index(sm)
        ti = target_Rs.index(tr)
        out = []
        for dsi in (-1, 0, 1):
            for dti in (-1, 0, 1):
                if dsi == 0 and dti == 0:
                    continue
                ni, nj = si + dsi, ti + dti
                if 0 <= ni < len(stop_mults) and 0 <= nj < len(target_Rs):
                    out.append((stop_mults[ni], target_Rs[nj]))
        return out

    def min_year_R(c):
        vals = [c["year_mean_R"][str(y)] for y in years if not (isinstance(c["year_mean_R"][str(y)], float) and math.isnan(c["year_mean_R"][str(y)]))]
        return min(vals) if vals else float("-inf")

    robust_scores = []
    for (sm, tr) in plateau_cells:
        nbrs = neighbors(sm, tr)
        nbr_meanRs = [cells[nb]["mean_R"] for nb in nbrs]
        worst_nbr = min(nbr_meanRs) if nbr_meanRs else float("-inf")
        # robustness = self mean_R + worst neighbor mean_R + min-year-R (all must be solid)
        score = cells[(sm, tr)]["mean_R"] + worst_nbr + min_year_R(cells[(sm, tr)])
        robust_scores.append(((sm, tr), score, worst_nbr, min_year_R(cells[(sm, tr)])))
    robust_scores.sort(key=lambda x: -x[1])

    highest_cell = max(cells.items(), key=lambda kv: kv[1]["mean_R"])
    print(f"\nHighest mean-R cell: stop={highest_cell[0][0]} tgt={highest_cell[0][1]} -> {highest_cell[1]['mean_R']:+.4f}R "
          f"({highest_cell[1]['n_pos_years']}/5 yrs pos)")
    if robust_scores:
        (rs, rt), rscore, rworst, rminyr = robust_scores[0]
        print(f"MOST ROBUST cell (center-of-plateau): stop={rs} tgt={rt} -> "
              f"mean {cells[(rs,rt)]['mean_R']:+.4f}R, worst-neighbor {rworst:+.4f}R, worst-year {rminyr:+.4f}R")

    baseline = cells[(0.5, 2.0)]
    print(f"\nBASELINE cell (stop=0.5, tgt=2.0): mean {baseline['mean_R']:+.4f}R, win {baseline['win_pct']*100:.1f}%, "
          f"{baseline['n_pos_years']}/5 yrs pos, n={baseline['n_trades']}")
    print("Baseline per-year R:", baseline["year_mean_R"])

    # Verdict heuristic
    frac_plateau = len(plateau_cells) / len(cells)
    verdict_plateau = frac_plateau >= 0.4  # >=40% of grid is a clean all-years-positive plateau

    out = {
        "universe_symbols": universe,
        "n_symbols": len(universe),
        "total_raw_signals": total_signals,
        "grid_stop_mults": stop_mults,
        "grid_target_Rs": target_Rs,
        "cells": {f"s{sm}_t{tr}": cells[(sm, tr)] for sm in stop_mults for tr in target_Rs},
        "n_cells": len(cells),
        "n_cells_positive_meanR": len(pos_meanR_cells),
        "n_cells_strict_plateau": len(plateau_cells),
        "strict_plateau_cells": [f"s{s}_t{t}" for s, t in sorted(plateau_cells)],
        "frac_strict_plateau": round(frac_plateau, 3),
        "highest_meanR_cell": {"stop": highest_cell[0][0], "target": highest_cell[0][1],
                                "mean_R": highest_cell[1]["mean_R"],
                                "n_pos_years": highest_cell[1]["n_pos_years"]},
        "most_robust_cell": (
            {"stop": robust_scores[0][0][0], "target": robust_scores[0][0][1],
             "mean_R": cells[robust_scores[0][0]]["mean_R"],
             "worst_neighbor_meanR": robust_scores[0][2],
             "worst_year_R": robust_scores[0][3],
             "win_pct": cells[robust_scores[0][0]]["win_pct"]}
            if robust_scores else None
        ),
        "baseline_cell_0.5_2.0": baseline,
        "verdict_is_broad_plateau": bool(verdict_plateau),
    }
    out_path = os.path.join(
        REPO,
        "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/study_robustness_map_RESULT.json",
    )
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")
    return out


if __name__ == "__main__":
    main()
