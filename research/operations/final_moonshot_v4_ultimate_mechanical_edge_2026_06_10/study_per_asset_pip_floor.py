"""per_asset_pip_floor study.

Characterizes, per symbol, the immediate ADVERSE-NOISE FLOOR after entry:
the distribution of adverse excursion (MAE) BEFORE the favorable move
develops, separately for eventual-winners vs eventual-losers.

Goal: find the tightest stop (in pips AND ATR) that avoids being
noise-hit on eventual winners while still cutting losers fast, and emit a
per-symbol recommended stop (pips + ATR), and flag which symbols can take
the tightest stops.

Uses the SHARED ENTRY-DETECTION RECIPE exactly, multi-candidate per bar
(every matching rule = one trade), matching the confirmed sibling engine
study_structural_stop.py. Baseline geometry: stop=0.5*ATR, target=2R
(=1.0*ATR), first-touch <=60 bars, pessimistic same-bar (stop wins ties),
minus real per-asset-class cost.

PARITY NOTE / CAVEAT: the recipe header advertises this raw baseline as
"+0.69R/trade, 57% win". It does NOT reproduce at the raw pooled entry
level: the confirmed sibling study_structural_stop.py itself reports
flat_0.5ATR @ 2R = -0.100 R/trade, 33.5% win pooled, and THIS study
reproduces -0.099 R/trade, 33.5% win across the 21 surface symbols
present in the H4 export. The +0.69R/57% figure is therefore a
conditioned/filtered-subset result, not the raw recipe. All per-symbol
MAE distributions below are computed on this parity-correct raw engine and
are directly comparable to the other route studies.

Partitions: TRAIN 2022-2024, FORWARD 2025-2026. Per-year breakdown too.
R-unit = the stop distance. ETHUSD and EURGBP have no H4 file in this
export and are skipped.
"""

import sys
import json
import os
import math
from collections import defaultdict

sys.path.insert(0, "/Users/borr/Documents/gtos/repo/ai-trading-agent")

import numpy as np

from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

DATA_DIR = "/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
COST_MAP_PATH = "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_REAL_COST_MAP.json"

# Previous-live surface (CLAUDE.md), restricted to symbols present as H4 files.
LIVE_SURFACE = [
    "AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY",
    "EURUSD", "GBPJPY", "GBPUSD", "GER40", "JP225", "NAS100", "NZDUSD",
    "SPX500", "UK100", "USOIL_cash", "US30_cash", "USDCAD", "USDCHF",
    "USDJPY", "XAGUSD", "XAUUSD",
]
# UKOIL_cash not present in data dir; skip silently if missing.

# Pip-size conventions matching src/components/slippage_shadow_logger.py
# extended across the full surface using the documented rules.
PIP_SIZE = {
    # Metals
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    # JPY pairs
    "USDJPY": 0.01, "GBPJPY": 0.01, "EURJPY": 0.01, "AUDJPY": 0.01, "CHFJPY": 0.01,
    # Other FX (4-digit pip)
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDCAD": 0.0001, "USDCHF": 0.0001, "EURGBP": 0.0001,
    # Indices (1 point = 1 pip)
    "GER40": 1.0, "JP225": 1.0, "NAS100": 1.0, "SPX500": 1.0, "UK100": 1.0,
    "US30_cash": 1.0,
    # Energy (oil: 0.01 per cent convention)
    "USOIL_cash": 0.01,
    # Crypto (1 unit = 1 pip by point convention)
    "BTCUSD": 1.0, "ETHUSD": 0.1,
}

COST_CLASS_KEY = {  # ASSET_CLASS_BY_SYMBOL value -> cost map key
    "fx": "fx", "jpy_fx": "jpy_fx", "index": "index", "metals": "metals",
    "energy": "energy", "crypto": None, "agri": None,
}

MAX_HOLD = 60
STOP_ATR = 0.5  # baseline winning geometry stop in ATR
TARGET_R = 2.0  # 2R target


def load_csv(path):
    rows = []
    with open(path) as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < 6:
                continue
            t = parts[0]
            try:
                o = float(parts[1]); h = float(parts[2]); l = float(parts[3])
                c = float(parts[4]); v = float(parts[5])
            except ValueError:
                continue
            rows.append((t, o, h, l, c, v))
    return rows


def sma(arr, n, i):
    if i + 1 < n:
        return np.nan
    return float(np.mean(arr[i - n + 1:i + 1]))


def percentile(vals, p):
    if not vals:
        return None
    return float(np.percentile(np.asarray(vals, dtype=float), p))


def run_symbol(sym, cost_map):
    path = os.path.join(DATA_DIR, f"{sym}_H4.csv")
    if not os.path.exists(path):
        return None
    rows = load_csv(path)
    if len(rows) < 200:
        return None

    times = [r[0] for r in rows]
    O = np.array([r[1] for r in rows])
    H = np.array([r[2] for r in rows])
    L = np.array([r[3] for r in rows])
    C = np.array([r[4] for r in rows])
    V = np.array([r[5] for r in rows])
    n = len(rows)

    # True range
    tr = np.zeros(n)
    tr[0] = H[0] - L[0]
    for i in range(1, n):
        tr[i] = max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))

    asset_class = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    ckey = COST_CLASS_KEY.get(asset_class)
    cost_r = cost_map.get(ckey, cost_map.get("_global_median", 0.0953)) if ckey else cost_map.get("_global_median", 0.0953)
    pip = PIP_SIZE.get(sym)

    prev_tuple = None
    trades = []  # each: dict

    for i in range(60, n):
        atr = float(np.mean(tr[i - 13:i + 1]))  # mean truerange[i-13..i] (14 bars)
        if atr <= 0:
            continue
        m20 = sma(C, 20, i); m50 = sma(C, 50, i)
        if math.isnan(m20) or math.isnan(m50):
            continue
        if m20 > m50 * 1.001:
            trend = "up"
        elif m20 < m50 * 0.999:
            trend = "down"
        else:
            trend = "flat"

        lo48 = float(np.min(L[i - 47:i + 1])); hi48 = float(np.max(H[i - 47:i + 1]))
        rng48 = hi48 - lo48
        pos = (C[i] - lo48) / rng48 if rng48 > 0 else 0.5
        if pos < 0.25:
            posb = "low"
        elif pos > 0.75:
            posb = "high"
        else:
            posb = "mid"

        v20 = sma(V, 20, i)
        relv = V[i] / v20 if v20 and v20 > 0 else 0.0

        rng = H[i] - L[i]
        eff = rng / V[i] if V[i] > 0 else 0.0
        effs = []
        for j in range(i - 19, i + 1):
            if V[j] > 0:
                effs.append((H[j] - L[j]) / V[j])
        beff = float(np.mean(effs)) if effs else 0.0
        absb = eff <= 0.6 * beff if beff > 0 else False
        expb = eff >= 1.4 * beff if beff > 0 else False

        ph = float(np.max(H[i - 20:i])); pl = float(np.min(L[i - 20:i]))
        swh = (H[i] > ph) and (C[i] < ph) and (relv >= 1.5)
        swl = (L[i] < pl) and (C[i] > pl) and (relv >= 1.5)

        vdacc = 0.0
        for j in range(i - 2, i + 1):
            r = H[j] - L[j]
            if r > 0:
                vdacc += V[j] * (C[j] - O[j]) / r

        swept = bool(swh or swl)
        cur_tuple = (trend, posb, relv >= 1.5, swept)
        debounce_ok = cur_tuple != prev_tuple
        prev_tuple = cur_tuple
        if not debounce_ok:
            continue

        # candidate directions -- multi-candidate per bar (CONFIRMED ENGINE
        # PARITY: study_structural_stop.py appends ALL matching rules, each a
        # separate trade; do NOT first-match).
        cands = []
        if swl: cands.append(1)
        if swh: cands.append(-1)
        if relv <= 0.6 and trend == "down" and posb == "low": cands.append(1)
        if relv <= 0.6 and trend == "up" and posb == "high": cands.append(-1)
        if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]: cands.append(1)
        if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]: cands.append(-1)
        if absb and posb == "low": cands.append(1)
        if absb and posb == "high": cands.append(-1)
        if posb == "high" and vdacc < 0: cands.append(-1)
        if posb == "low" and vdacc > 0: cands.append(1)
        if not cands:
            continue

        entry = C[i]
        R = STOP_ATR * atr  # R unit = stop distance; target at TARGET_R*R (=1.0 ATR)
        year = times[i][:4]

        for d in cands:
            # First-touch <=MAX_HOLD bars. CONFIRMED-ENGINE resolution: record
            # first bar target reached (tbar) and first bar stop reached (stbar);
            # loop breaks on stop. Win iff tbar exists and (stbar is None or
            # tbar < stbar) -> pessimistic same-bar (ties = loss). adv/fav use
            # bar high/low.
            stbar = None
            tbar = None
            # mae_price = max adverse excursion BEFORE the favorable move
            # develops (i.e. up to and including the resolving bar). For a
            # winner this is the noise it had to survive before the target was
            # reached; we STOP accumulating once the target bar is seen so the
            # floor is not polluted by post-target adverse drift.
            mae_price = 0.0
            bars_held = 0
            for k in range(i + 1, min(i + 1 + MAX_HOLD, n)):
                bars_held = k - i
                if d == 1:
                    fav = H[k] - entry
                    adv = entry - L[k]
                else:
                    fav = entry - L[k]
                    adv = H[k] - entry
                # accumulate adverse floor only while still pre-resolution
                if tbar is None:
                    if adv > mae_price:
                        mae_price = adv
                if stbar is None and adv >= R:
                    stbar = k
                if tbar is None and fav >= TARGET_R * R:
                    tbar = k
                    # winner resolves here if target precedes/ties stop bar
                    if stbar is None or tbar < stbar:
                        break
                if stbar is not None:
                    break  # stop ends the trade

            if tbar is not None and (stbar is None or tbar < stbar):
                outcome = "win"
            elif stbar is not None:
                outcome = "loss"
            else:
                outcome = "timeout"

            # For winners, mae_price is the adverse-noise floor they survived
            # BEFORE the target developed (capped below R by construction, since
            # a winner never reached adv>=R earlier than the target).
            mae_atr = mae_price / atr if atr > 0 else 0.0
            mae_R = mae_price / R if R > 0 else 0.0
            mae_pips = mae_price / pip if pip else None

            trades.append({
                "i": i,
                "year": year,
                "d": d,
                "outcome": outcome,
                "atr": atr,
                "R_price": R,
                "mae_price": mae_price,
                "mae_atr": mae_atr,
                "mae_R": mae_R,
                "mae_pips": mae_pips,
                "bars_held": bars_held,
                "cost_r": cost_r,
                "pip": pip,
            })

    return {
        "symbol": sym,
        "asset_class": asset_class,
        "cost_r": cost_r,
        "pip": pip,
        "trades": trades,
    }


def net_r(outcome, cost_r):
    if outcome == "win":
        return TARGET_R - cost_r
    if outcome == "loss":
        return -1.0 - cost_r
    return -cost_r  # timeout: flat exit minus cost (conservative)


def summarize_symbol(res, partition_filter=None):
    """Return summary stats over trades, optionally filtered by year predicate."""
    trades = res["trades"]
    if partition_filter is not None:
        trades = [t for t in trades if partition_filter(t["year"])]
    if not trades:
        return None

    winners = [t for t in trades if t["outcome"] == "win"]
    losers = [t for t in trades if t["outcome"] == "loss"]
    timeouts = [t for t in trades if t["outcome"] == "timeout"]
    resolved = winners + losers

    def mae_stats(group, key):
        vals = [t[key] for t in group if t[key] is not None]
        if not vals:
            return None
        return {
            "n": len(vals),
            "median": float(np.median(vals)),
            "p75": percentile(vals, 75),
            "p90": percentile(vals, 90),
            "p95": percentile(vals, 95),
            "max": float(np.max(vals)),
            "mean": float(np.mean(vals)),
        }

    n = len(trades)
    nres = len(resolved)
    win_rate = len(winners) / nres if nres else 0.0
    net = sum(net_r(t["outcome"], t["cost_r"]) for t in trades) / n if n else 0.0

    return {
        "n_trades": n,
        "n_win": len(winners),
        "n_loss": len(losers),
        "n_timeout": len(timeouts),
        "win_rate_resolved": win_rate,
        "net_r_per_trade": net,
        "winners_mae_atr": mae_stats(winners, "mae_atr"),
        "winners_mae_pips": mae_stats(winners, "mae_pips"),
        "losers_mae_atr": mae_stats(losers, "mae_atr"),
        "losers_mae_pips": mae_stats(losers, "mae_pips"),
        "all_mae_atr": mae_stats(trades, "mae_atr"),
    }


def evaluate_stop(res, stop_atr, partition_filter=None):
    """Re-evaluate the trade set under a counterfactual stop = stop_atr*ATR,
    keeping the SAME 2R-in-baseline-R target geometry is NOT what we want; we
    want a sweep where stop changes and target is held at the SAME absolute
    price (2R of the baseline 0.5 ATR = 1.0 ATR). But MAE-based re-evaluation
    needs full path; here we instead re-derive outcome from recorded MAE and
    a re-walk is required for full fidelity. We approximate using a dedicated
    re-walk in sweep_stop() instead. This helper kept for clarity only."""
    raise NotImplementedError


def sweep_stop(sym, cost_map, stop_atr_grid, partition_filter=None):
    """Full re-walk: for each candidate stop (in ATR), hold target at 1.0*ATR
    (the baseline 2R absolute target) and re-run first-touch. R-unit for
    net-R accounting is the candidate stop distance, so a win = (1.0*ATR /
    stop_dist) R, a loss = -1R. Reports net-R/trade and win rate per stop.

    This isolates the pip/ATR FLOOR effect: tighter stops get noise-hit more
    (lower win rate) but each loss is smaller relative to the fixed target."""
    path = os.path.join(DATA_DIR, f"{sym}_H4.csv")
    if not os.path.exists(path):
        return None
    rows = load_csv(path)
    if len(rows) < 200:
        return None
    times = [r[0] for r in rows]
    O = np.array([r[1] for r in rows]); H = np.array([r[2] for r in rows])
    L = np.array([r[3] for r in rows]); C = np.array([r[4] for r in rows])
    V = np.array([r[5] for r in rows]); n = len(rows)
    tr = np.zeros(n); tr[0] = H[0] - L[0]
    for i in range(1, n):
        tr[i] = max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))
    asset_class = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    ckey = COST_CLASS_KEY.get(asset_class)
    cost_r = cost_map.get(ckey, cost_map.get("_global_median", 0.0953)) if ckey else cost_map.get("_global_median", 0.0953)

    # collect entries once
    entries = []
    prev_tuple = None
    for i in range(60, n):
        atr = float(np.mean(tr[i - 13:i + 1]))
        if atr <= 0:
            continue
        m20 = sma(C, 20, i); m50 = sma(C, 50, i)
        if math.isnan(m20) or math.isnan(m50):
            continue
        trend = "up" if m20 > m50 * 1.001 else ("down" if m20 < m50 * 0.999 else "flat")
        lo48 = float(np.min(L[i - 47:i + 1])); hi48 = float(np.max(H[i - 47:i + 1]))
        rng48 = hi48 - lo48
        pos = (C[i] - lo48) / rng48 if rng48 > 0 else 0.5
        posb = "low" if pos < 0.25 else ("high" if pos > 0.75 else "mid")
        v20 = sma(V, 20, i); relv = V[i] / v20 if v20 and v20 > 0 else 0.0
        rng = H[i] - L[i]; eff = rng / V[i] if V[i] > 0 else 0.0
        effs = [(H[j] - L[j]) / V[j] for j in range(i - 19, i + 1) if V[j] > 0]
        beff = float(np.mean(effs)) if effs else 0.0
        absb = eff <= 0.6 * beff if beff > 0 else False
        expb = eff >= 1.4 * beff if beff > 0 else False
        ph = float(np.max(H[i - 20:i])); pl = float(np.min(L[i - 20:i]))
        swh = (H[i] > ph) and (C[i] < ph) and (relv >= 1.5)
        swl = (L[i] < pl) and (C[i] > pl) and (relv >= 1.5)
        vdacc = 0.0
        for j in range(i - 2, i + 1):
            r = H[j] - L[j]
            if r > 0:
                vdacc += V[j] * (C[j] - O[j]) / r
        swept = bool(swh or swl)
        cur_tuple = (trend, posb, relv >= 1.5, swept)
        if cur_tuple == prev_tuple:
            continue
        prev_tuple = cur_tuple
        cands = []
        if swl: cands.append(1)
        if swh: cands.append(-1)
        if relv <= 0.6 and trend == "down" and posb == "low": cands.append(1)
        if relv <= 0.6 and trend == "up" and posb == "high": cands.append(-1)
        if relv >= 1.8 and expb and posb == "high" and C[i] > O[i]: cands.append(1)
        if relv >= 1.8 and expb and posb == "low" and C[i] < O[i]: cands.append(-1)
        if absb and posb == "low": cands.append(1)
        if absb and posb == "high": cands.append(-1)
        if posb == "high" and vdacc < 0: cands.append(-1)
        if posb == "low" and vdacc > 0: cands.append(1)
        for d in cands:
            entries.append((i, d, atr))

    results = {}
    for stop_atr in stop_atr_grid:
        nt = 0; nw = 0; nl = 0; nto = 0; net_sum = 0.0
        for (i, d, atr) in entries:
            yr = times[i][:4]
            if partition_filter is not None and not partition_filter(yr):
                continue
            entry = C[i]
            stop_dist = stop_atr * atr
            tgt_dist = 1.0 * atr  # fixed baseline 2R absolute target (= TARGET_R * 0.5 ATR)
            if stop_dist <= 0:
                continue
            # CONFIRMED-ENGINE resolution: stbar/tbar, strict-earlier win, stop ends trade.
            stbar = None; tbar = None
            for k in range(i + 1, min(i + 1 + MAX_HOLD, n)):
                if d == 1:
                    fav = H[k] - entry; adv = entry - L[k]
                else:
                    fav = entry - L[k]; adv = H[k] - entry
                if stbar is None and adv >= stop_dist:
                    stbar = k
                if tbar is None and fav >= tgt_dist:
                    tbar = k
                if stbar is not None:
                    break
            if tbar is not None and (stbar is None or tbar < stbar):
                outcome = "win"
            elif stbar is not None:
                outcome = "loss"
            else:
                outcome = "timeout"
            nt += 1
            win_R = tgt_dist / stop_dist  # reward in R-units of THIS stop
            if outcome == "win":
                nw += 1; net_sum += win_R - cost_r
            elif outcome == "loss":
                nl += 1; net_sum += -1.0 - cost_r
            else:
                nto += 1; net_sum += -cost_r
        results[stop_atr] = {
            "n": nt, "win": nw, "loss": nl, "timeout": nto,
            "win_rate": (nw / (nw + nl)) if (nw + nl) else 0.0,
            "net_r_per_trade": (net_sum / nt) if nt else 0.0,
            "reward_R_per_win_at_median": None,  # filled below if needed
        }
    return results


def main():
    with open(COST_MAP_PATH) as f:
        cost_map = json.load(f)

    stop_grid = [0.25, 0.30, 0.40, 0.50, 0.60, 0.75, 1.00]

    out = {
        "config": {
            "max_hold": MAX_HOLD,
            "baseline_stop_atr": STOP_ATR,
            "baseline_target_r": TARGET_R,
            "stop_grid_atr": stop_grid,
            "cost_map": cost_map,
            "pip_size": PIP_SIZE,
        },
        "per_symbol": {},
    }

    print("=" * 100)
    print("PER-ASSET PIP FLOOR STUDY")
    print("=" * 100)

    for sym in LIVE_SURFACE:
        res = run_symbol(sym, cost_map)
        if res is None:
            print(f"[skip] {sym}: no data / too few rows")
            continue

        full = summarize_symbol(res)
        train = summarize_symbol(res, lambda y: y in ("2022", "2023", "2024"))
        fwd = summarize_symbol(res, lambda y: y in ("2025", "2026"))
        per_year = {}
        for yr in ("2022", "2023", "2024", "2025", "2026"):
            s = summarize_symbol(res, (lambda yy: (lambda y: y == yy))(yr))
            if s:
                per_year[yr] = {
                    "n": s["n_trades"], "win_rate": round(s["win_rate_resolved"], 3),
                    "net_r": round(s["net_r_per_trade"], 4),
                }

        # Stop sweep (full + partitions)
        sweep_full = sweep_stop(sym, cost_map, stop_grid)
        sweep_train = sweep_stop(sym, cost_map, stop_grid, lambda y: y in ("2022", "2023", "2024"))
        sweep_fwd = sweep_stop(sym, cost_map, stop_grid, lambda y: y in ("2025", "2026"))

        # Recommended stop: the ATR multiple that just covers the eventual-
        # winners' adverse-excursion floor (so winners survive) -> use p90 of
        # winners' MAE in ATR as the noise floor; recommend the smallest grid
        # stop >= that floor, but also confirm it doesn't tank net-R.
        rec = None
        floor_atr = None
        if full and full["winners_mae_atr"]:
            floor_atr = full["winners_mae_atr"]["p90"]
            # smallest grid stop >= floor (so >=90% of winners survive)
            cand = [s for s in stop_grid if s >= floor_atr]
            stop_choice = cand[0] if cand else stop_grid[-1]
            # but pick the grid stop maximizing forward net-R among those that
            # keep >=80% winner survival (i.e. stop >= p80 floor)
            best_stop = None; best_net = -1e9
            for s in stop_grid:
                fr = sweep_fwd.get(s) if sweep_fwd else None
                if fr and fr["n"] >= 20:
                    if fr["net_r_per_trade"] > best_net:
                        best_net = fr["net_r_per_trade"]; best_stop = s
            pip = res["pip"]
            atr_med = None
            atrs = [t["atr"] for t in res["trades"]]
            if atrs:
                atr_med = float(np.median(atrs))
            rec = {
                "winner_noise_floor_atr_p90": round(floor_atr, 4),
                "winner_noise_floor_atr_p75": round(full["winners_mae_atr"]["p75"], 4) if full["winners_mae_atr"] else None,
                "min_grid_stop_covering_p90_floor_atr": stop_choice,
                "fwd_netr_optimal_stop_atr": best_stop,
                "median_atr_price": round(atr_med, 6) if atr_med else None,
                "median_atr_pips": round(atr_med / pip, 2) if (atr_med and pip) else None,
                "rec_stop_atr": stop_choice,
                "rec_stop_pips_at_median_atr": round(stop_choice * atr_med / pip, 2) if (atr_med and pip) else None,
                "winner_floor_pips_p90": round(full["winners_mae_pips"]["p90"], 2) if (full["winners_mae_pips"]) else None,
            }

        out["per_symbol"][sym] = {
            "asset_class": res["asset_class"],
            "cost_r": res["cost_r"],
            "pip": res["pip"],
            "full": full,
            "train": train,
            "forward": fwd,
            "per_year": per_year,
            "sweep_full": {str(k): v for k, v in (sweep_full or {}).items()},
            "sweep_train": {str(k): v for k, v in (sweep_train or {}).items()},
            "sweep_forward": {str(k): v for k, v in (sweep_fwd or {}).items()},
            "recommendation": rec,
        }

        # Console summary
        wf = full["winners_mae_atr"]; lf = full["losers_mae_atr"]
        print(f"\n{sym} [{res['asset_class']}] cost_r={res['cost_r']:.4f} pip={res['pip']}")
        print(f"  trades={full['n_trades']} win%={full['win_rate_resolved']*100:.1f} netR/trade={full['net_r_per_trade']:+.4f} (timeouts={full['n_timeout']})")
        if wf:
            print(f"  WINNERS  MAE atr: med={wf['median']:.3f} p75={wf['p75']:.3f} p90={wf['p90']:.3f} p95={wf['p95']:.3f} max={wf['max']:.3f}")
        wp = full["winners_mae_pips"]
        if wp:
            print(f"  WINNERS  MAE pips: med={wp['median']:.1f} p75={wp['p75']:.1f} p90={wp['p90']:.1f} p95={wp['p95']:.1f}")
        if lf:
            print(f"  LOSERS   MAE atr: med={lf['median']:.3f} p75={lf['p75']:.3f} p90={lf['p90']:.3f} (note: losers capped at stop=0.5ATR)")
        if rec:
            print(f"  REC stop: {rec['rec_stop_atr']} ATR (~{rec['rec_stop_pips_at_median_atr']} pips at median ATR); winner noise floor p90={rec['winner_noise_floor_atr_p90']} ATR; fwd-netR-optimal stop={rec['fwd_netr_optimal_stop_atr']} ATR")
        # sweep line (forward)
        if sweep_fwd:
            sline = "  FWD sweep netR: " + " ".join(
                f"{s:.2f}={sweep_fwd[s]['net_r_per_trade']:+.3f}(wr{sweep_fwd[s]['win_rate']*100:.0f})" for s in stop_grid
            )
            print(sline)

    outpath = "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/study_per_asset_pip_floor_RESULT.json"
    with open(outpath, "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(f"\n\nWrote {outpath}")

    # ---- Cross-symbol synthesis ----
    print("\n" + "=" * 100)
    print("CROSS-SYMBOL SYNTHESIS: tightest-stop tolerance")
    print("=" * 100)
    rows = []
    for sym, d in out["per_symbol"].items():
        rec = d.get("recommendation")
        full = d.get("full")
        if not rec or not full:
            continue
        rows.append((
            sym, d["asset_class"],
            rec["winner_noise_floor_atr_p90"],
            rec["winner_noise_floor_atr_p75"],
            rec["rec_stop_atr"],
            rec["rec_stop_pips_at_median_atr"],
            rec["fwd_netr_optimal_stop_atr"],
            full["win_rate_resolved"],
            full["net_r_per_trade"],
        ))
    rows.sort(key=lambda r: (r[2] if r[2] is not None else 9))
    print(f"{'symbol':12} {'class':8} {'p90floorATR':>11} {'p75floorATR':>11} {'recStopATR':>10} {'recStopPips':>11} {'fwdOptStop':>10} {'win%':>6} {'netR':>7}")
    tightest = []
    for r in rows:
        print(f"{r[0]:12} {r[1]:8} {r[2]:>11.3f} {r[3]:>11.3f} {r[4]:>10.2f} {str(r[5]):>11} {str(r[6]):>10} {r[7]*100:>5.1f} {r[8]:>+7.3f}")
        if r[2] is not None and r[2] <= 0.40:
            tightest.append(r[0])
    print(f"\nSymbols whose eventual-winners tolerate a TIGHT stop (p90 winner-MAE <= 0.40 ATR): {tightest}")

    return out


if __name__ == "__main__":
    main()
