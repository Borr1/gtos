#!/usr/bin/env python3
"""
Phase 3 T3 — Recompute OB retest dataset under PRODUCTION vs RESEARCH semantics.

Research semantics (compute_zone_age_v1.py:269-329):
    - Touch = outside→inside TRANSITION.
    - Window = RETEST_WINDOW = 250 H1 bars after formation.
    - Continuation = entry(close at retest) vs 1.25×ATR target / 0.5×ATR stop, 20 bars.

Production semantics (market_state.py:483-502):
    - touch_count = number of candles whose range overlaps OB [low, high].
    - Applied from formation_index+1 to end of candle list (no 250-bar cap).
    - Counts every stationary-in-zone bar as +1 (no transition aggregation).

Goal:
    Re-derive a touch_count under PRODUCTION semantics per OB and map the
    RESEARCH-semantics dataset (ob_zone_age_events_v1.json) onto the gate
    that actually runs in production. Since the production metric is a
    function of the OB, not the retest event, we compute per-OB prod
    touch count over the full candle history and then answer:

      Q1. For an OB whose RESEARCH touch_number at a given retest event is T
          (T ∈ {1, 2, 3, 4+}), what is the distribution of the PRODUCTION
          touch_count as seen by the gate at that retest event?

      Q2. The gate fires at touches >= 2 (production metric). For the same
          population, what WR remains? Is it still 72.7% touch-1-like, or
          does production touch=1 pull in some research touch-2 events?

    Then the key diagnostic: under production semantics applied to the
    SAME OB population, does Wr-by-touch still show the 72.7%/31.5% cliff?
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]  # ai-trading-agent/
DATA_DIR = ROOT / "exports" / "multi_instrument"
EVENT_FILE = ROOT / "research" / "diagnostics" / "zone_age_analysis" / "ob_zone_age_events_v1.json"

# Re-use the EXACT constants from compute_zone_age_v1.py so OB detection is bit-identical.
SWING_MIN_BARS = 2
WARMUP_CANDLES = 100
MIN_DISPLACEMENT_ATR = 0.4
BODY_RATIO_MIN = 0.40
RETEST_WINDOW = 250
CONTINUATION_WINDOW = 20
ATR_PERIOD = 14
TARGET_ATR_MULT = 1.25
STOP_ATR_MULT = 0.50

INSTRUMENTS = [
    "XAUUSD", "US30_cash", "GBPUSD", "USDJPY", "NZDUSD",
    "GBPJPY", "EURJPY", "EURUSD", "USDCAD", "AUDUSD",
    "XAGUSD", "US500_cash", "USOIL_cash",
]


def load_instrument(symbol: str) -> pd.DataFrame | None:
    candidates = [DATA_DIR / f"{symbol}_H1.csv", DATA_DIR / f"{symbol.replace('.', '_')}_H1.csv"]
    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            for c in ("open", "high", "low", "close"):
                df[c] = df[c].astype(float)
            return df.reset_index(drop=True)
    return None


def compute_atr(highs, lows, closes, period=ATR_PERIOD):
    n = len(highs)
    tr = np.empty(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
    atr = np.full(n, np.nan)
    if n <= period:
        return atr
    atr[period] = float(np.mean(tr[1 : period + 1]))
    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    return atr


def detect_swings_at(highs, lows, i, min_bars=SWING_MIN_BARS):
    n = len(highs)
    is_high = is_low = False
    if i >= min_bars and i < n - min_bars:
        is_high = all(
            highs[i] > highs[i - j] and highs[i] > highs[i + j]
            for j in range(1, min_bars + 1)
        )
        is_low = all(
            lows[i] < lows[i - j] and lows[i] < lows[i + j]
            for j in range(1, min_bars + 1)
        )
    return is_high, is_low


def detect_obs(df, atr):
    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    n = len(df)
    obs = []

    swings = []
    last_high = None
    last_low = None
    current_structure = "neutral"

    for i in range(WARMUP_CANDLES, n - SWING_MIN_BARS):
        if np.isnan(atr[i]) or atr[i] == 0:
            continue
        is_sh, is_sl = detect_swings_at(highs, lows, i)
        if is_sh:
            label = "HH" if (last_high is None or highs[i] > last_high["price"]) else "LH"
            swg = {"index": i, "price": highs[i], "type": "high", "classification": label, "consumed": False}
            swings.append(swg); last_high = swg
        if is_sl:
            label = "HL" if (last_low is None or lows[i] > last_low["price"]) else "LL"
            swg = {"index": i, "price": lows[i], "type": "low", "classification": label, "consumed": False}
            swings.append(swg); last_low = swg
        if len(swings) < 4:
            continue
        highs_l = [s for s in swings if s["type"] == "high" and not s["consumed"]]
        lows_l = [s for s in swings if s["type"] == "low" and not s["consumed"]]
        if not highs_l or not lows_l:
            continue
        lsh = highs_l[-1]
        if closes[i] > lsh["price"] and i > lsh["index"] + 1:
            disp = (closes[i] - lsh["price"]) / atr[i]
            body = abs(closes[i] - opens[i]) / (highs[i] - lows[i] + 1e-10)
            if disp >= MIN_DISPLACEMENT_ATR and body >= BODY_RATIO_MIN:
                et = "CHoCH" if current_structure == "bearish" else "BOS"
                current_structure = "bullish"
                for k in range(i - 1, max(i - 11, WARMUP_CANDLES - 1), -1):
                    if closes[k] < opens[k]:
                        obs.append({"direction": "bullish", "ob_high": highs[k], "ob_low": lows[k],
                                    "formation_index": k, "event_type": et, "break_index": i})
                        lsh["consumed"] = True
                        break
        lsl = lows_l[-1]
        if closes[i] < lsl["price"] and i > lsl["index"] + 1:
            disp = (lsl["price"] - closes[i]) / atr[i]
            body = abs(closes[i] - opens[i]) / (highs[i] - lows[i] + 1e-10)
            if disp >= MIN_DISPLACEMENT_ATR and body >= BODY_RATIO_MIN:
                et = "CHoCH" if current_structure == "bullish" else "BOS"
                current_structure = "bearish"
                for k in range(i - 1, max(i - 11, WARMUP_CANDLES - 1), -1):
                    if closes[k] > opens[k]:
                        obs.append({"direction": "bearish", "ob_high": highs[k], "ob_low": lows[k],
                                    "formation_index": k, "event_type": et, "break_index": i})
                        lsl["consumed"] = True
                        break
    return obs


def count_touches_research_with_events(ob, highs, lows, closes, atr):
    """Research semantics: count outside→inside TRANSITIONS within RETEST_WINDOW.
    Returns a list of events, each event carrying (retest_index, touch_number, continuation).
    """
    n = len(highs)
    start = ob["formation_index"] + 1
    end = min(start + RETEST_WINDOW, n)
    direction = ob["direction"]
    oh = ob["ob_high"]; ol = ob["ob_low"]
    events = []
    in_zone = False
    tc = 0
    for j in range(start, end):
        if direction == "bullish":
            touching = lows[j] <= oh
        else:
            touching = highs[j] >= ol
        if touching and not in_zone:
            in_zone = True
            tc += 1
            cont = measure_cont(j, direction, oh, ol, highs, lows, closes, atr, n)
            events.append({"retest_index": j, "touch_number_research": tc,
                           "formation_age_bars": j - ob["formation_index"],
                           "continuation": cont})
        elif not touching:
            in_zone = False
    return events


def count_touches_production_cumulative(ob, highs, lows):
    """Production semantics: BAR-OVERLAP counting — every candle whose range
    overlaps [ob_low, ob_high] is +1. Starting at formation_index+1, running to
    end of candle list (no window). Returns a list of cumulative counts indexed
    by candle index j, where production_tc[j] = count over candles[formation+1 .. j].
    For efficient lookup per retest_index we return a dict {j: count_at_and_including_j}.
    """
    n = len(highs)
    start = ob["formation_index"] + 1
    oh = ob["ob_high"]; ol = ob["ob_low"]
    counts = {}
    c = 0
    for j in range(start, n):
        if highs[j] >= ol and lows[j] <= oh:
            c += 1
        counts[j] = c
    return counts


def measure_cont(ri, direction, oh, ol, highs, lows, closes, atr, n):
    if ri >= n - 1 or np.isnan(atr[ri]) or atr[ri] == 0:
        return False
    entry = closes[ri]
    td = TARGET_ATR_MULT * atr[ri]; sd = STOP_ATR_MULT * atr[ri]
    if direction == "bullish":
        target = entry + td; stop = entry - sd
    else:
        target = entry - td; stop = entry + sd
    end = min(ri + 1 + CONTINUATION_WINDOW, n)
    for j in range(ri + 1, end):
        if direction == "bullish":
            if highs[j] >= target: return True
            if lows[j] <= stop:    return False
        else:
            if lows[j] <= target:  return True
            if highs[j] >= stop:   return False
    return False


def run_instrument(symbol):
    df = load_instrument(symbol)
    if df is None or len(df) < 500:
        print(f"  SKIP {symbol}"); return []
    highs = df["high"].values; lows = df["low"].values; closes = df["close"].values
    atr = compute_atr(highs, lows, closes)
    obs = detect_obs(df, atr)
    print(f"  {symbol}: {len(df)} candles, {len(obs)} OBs")
    rows = []
    for ob in obs:
        research_events = count_touches_research_with_events(ob, highs, lows, closes, atr)
        if not research_events:
            continue
        production_counts = count_touches_production_cumulative(ob, highs, lows)
        for ev in research_events:
            ri = ev["retest_index"]
            # Production count AT THE MOMENT of retest (cumulative to and including ri).
            prod_tc_at_retest = production_counts.get(ri, 0)
            # Production count at END of history (value the gate would see if the OB
            # is evaluated well after formation — what permissions.py actually gets).
            last_j = max(production_counts) if production_counts else ri
            prod_tc_final = production_counts.get(last_j, 0)
            rows.append({
                "symbol": symbol,
                "formation_index": ob["formation_index"],
                "direction": ob["direction"],
                "event_type": ob["event_type"],
                "retest_index": ri,
                "touch_number_research": ev["touch_number_research"],
                "formation_age_bars": ev["formation_age_bars"],
                "touch_count_prod_at_retest": prod_tc_at_retest,
                "touch_count_prod_final": prod_tc_final,
                "continuation": int(bool(ev["continuation"])),
            })
    return rows


def wilson_ci(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - m), min(1, c + m)


def main():
    all_rows = []
    for sym in INSTRUMENTS:
        all_rows.extend(run_instrument(sym))
    df = pd.DataFrame(all_rows)

    out = Path(__file__).parent / "both_semantics_events.parquet"
    df.to_parquet(out, index=False)
    print(f"\n{len(df):,} rows -> {out}")

    # ── Reproduce the canonical 72.7% / 31.5% table under research semantics ──
    print("\n=== RESEARCH SEMANTICS (touch_number_research) ===")
    df["tcr_clip"] = df["touch_number_research"].clip(upper=4).astype(int)
    tbl = df.groupby("tcr_clip").agg(
        n=("continuation", "size"),
        cont_n=("continuation", "sum"),
    )
    tbl["wr"] = tbl["cont_n"] / tbl["n"] * 100
    print(tbl.to_string())

    # Touch 2+ pooled
    m2plus = df["touch_number_research"] >= 2
    n2 = m2plus.sum(); k2 = df.loc[m2plus, "continuation"].sum()
    print(f"Research Touch-2+ pooled: {k2}/{n2} = {k2/n2*100:.1f}%")

    # ── Production semantics AT RETEST MOMENT ──
    print("\n=== PRODUCTION SEMANTICS at retest moment (touch_count_prod_at_retest) ===")
    df["tcp_clip"] = df["touch_count_prod_at_retest"].clip(upper=10).astype(int)
    tbl = df.groupby("tcp_clip").agg(
        n=("continuation", "size"),
        cont_n=("continuation", "sum"),
    )
    tbl["wr"] = tbl["cont_n"] / tbl["n"] * 100
    print(tbl.to_string())

    # ── Production semantics at FINAL (what the gate actually sees) ──
    print("\n=== PRODUCTION SEMANTICS at final candle (touch_count_prod_final — what gate sees) ===")
    df["tcpf_clip"] = df["touch_count_prod_final"].clip(upper=10).astype(int)
    tbl = df.groupby("tcpf_clip").agg(
        n=("continuation", "size"),
        cont_n=("continuation", "sum"),
    )
    tbl["wr"] = tbl["cont_n"] / tbl["n"] * 100
    print(tbl.to_string())

    # ── Cross-tab: research-touch-1 vs production touch count at retest ──
    print("\n=== Cross-tab: research_touch_number==1 vs prod_touch_count AT RETEST ===")
    first_touch = df[df["touch_number_research"] == 1]
    print(f"n first-touch (research) = {len(first_touch):,}")
    print(first_touch["touch_count_prod_at_retest"].value_counts().sort_index().head(20).to_string())

    # ── The critical gate simulation: gate fires at prod >= 2. For research=touch-1
    #    events, how many would the gate REJECT under prod-at-retest? ──
    rejected_mask = (df["touch_number_research"] == 1) & (df["touch_count_prod_at_retest"] >= 2)
    n_rej = rejected_mask.sum()
    n_ft = (df["touch_number_research"] == 1).sum()
    cont_rej = df.loc[rejected_mask, "continuation"].sum()
    print(f"\nResearch touch-1 events with prod_at_retest >= 2 (would be rejected by gate): {n_rej:,}/{n_ft:,} = {n_rej/n_ft*100:.2f}%")
    if n_rej > 0:
        print(f"  WR of those rejected first-touch events: {cont_rej}/{n_rej} = {cont_rej/n_rej*100:.1f}%")

    passed_mask = (df["touch_number_research"] == 1) & (df["touch_count_prod_at_retest"] < 2)
    n_pass = passed_mask.sum(); cp = df.loc[passed_mask, "continuation"].sum()
    print(f"Research touch-1 events passing gate (prod<2): {n_pass:,}, WR {cp/n_pass*100:.1f}%")

    # ── Simulate the REAL gate situation: gate evaluates a LIVE OB at current
    #    candle. touch_count_prod_final is what the gate sees when the OB is
    #    still unmitigated and being considered for entry right now. So the
    #    correct simulation of the live gate is: prod_final >= 2 → reject. ──
    print("\n=== Live gate simulation: prod_final >= 2 rejects the OB ===")
    rej_live = df["touch_count_prod_final"] >= 2
    n_rej_live = rej_live.sum()
    print(f"OBs that gate WOULD REJECT (prod_final >= 2): {n_rej_live:,}/{len(df):,} = {n_rej_live/len(df)*100:.1f}%")
    pass_live = df[~rej_live]
    rej_live_df = df[rej_live]
    if len(pass_live) > 0:
        print(f"Research-semantics touch# distribution in PASSED OBs: {pass_live['touch_number_research'].value_counts().sort_index().head(5).to_dict()}")
    if len(rej_live_df) > 0:
        print(f"Research-semantics touch# distribution in REJECTED OBs: {rej_live_df['touch_number_research'].value_counts().sort_index().head(5).to_dict()}")

    # Median/quantile divergence
    print("\n=== Median/quantile comparison ===")
    print(f"median(touch_number_research) = {df['touch_number_research'].median()}")
    print(f"median(touch_count_prod_at_retest) = {df['touch_count_prod_at_retest'].median()}")
    print(f"median(touch_count_prod_final) = {df['touch_count_prod_final'].median()}")
    print(f"Ratio of median_prod_final / median_research = {df['touch_count_prod_final'].median() / max(df['touch_number_research'].median(), 1):.2f}x")

    # What research-semantics threshold equals prod>=2?
    print("\n=== Threshold equivalence ===")
    # For each unique value of prod_at_retest, compute the avg research touch#.
    grp = df.groupby("touch_count_prod_at_retest").agg(
        n=("touch_number_research", "size"),
        median_research=("touch_number_research", "median"),
        p25_research=("touch_number_research", lambda s: s.quantile(0.25)),
        p75_research=("touch_number_research", lambda s: s.quantile(0.75)),
    ).head(10)
    print(grp.to_string())


if __name__ == "__main__":
    main()
