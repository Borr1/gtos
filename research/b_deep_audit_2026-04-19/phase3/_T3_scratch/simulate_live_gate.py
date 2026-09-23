#!/usr/bin/env python3
"""
Simulate the LIVE gate as it actually runs: H1 OB over the last 168 H1 bars.

For each research-derived retest event (from ob_zone_age_events_v1.json):
  - "Eval time" = retest_index (the moment the ob_retest setup fires).
  - The gate sees the 168 H1 bars ending at retest_index.
  - OB was formed at formation_index, which (for events in research) must satisfy
    formation_index >= retest_index - 249 (within the 250-bar retest window).
  - _count_touches(ob, candles_last_168_ending_at_retest_index) returns the
    number of candles in that 168-bar window whose range overlaps the OB.

Q: For the canonical research touch-1 events (n=23,575), what fraction would
   the live gate reject (touches >= 2)?

Q: What does the prod WR-by-touch curve look like under this realistic
   windowing?

CRITICAL: In production, the OB detection is rerun on the 168-bar window
each candle. If formation_index would fall BEFORE the window start (168 bars
before current), the OB can't be detected at all — it simply doesn't exist
in mso. So we also need to check whether the OB would even be present.
Simplifying assumption: we use the dataset as-is (OBs and retests that research
identified) and treat each retest row as "gate was asked to evaluate here".
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "exports" / "multi_instrument"

SWING_MIN_BARS = 2
WARMUP_CANDLES = 100
MIN_DISPLACEMENT_ATR = 0.4
BODY_RATIO_MIN = 0.40
RETEST_WINDOW = 250
CONTINUATION_WINDOW = 20
ATR_PERIOD = 14
TARGET_ATR_MULT = 1.25
STOP_ATR_MULT = 0.50
H1_LOOKBACK = 168  # DEFAULT_LOOKBACKS["H1"] in src/components/data_ingestion.py:38

INSTRUMENTS = [
    "XAUUSD", "US30_cash", "GBPUSD", "USDJPY", "NZDUSD",
    "GBPJPY", "EURJPY", "EURUSD", "USDCAD", "AUDUSD",
    "XAGUSD", "US500_cash", "USOIL_cash",
]


def load_instrument(symbol: str):
    for p in [DATA_DIR / f"{symbol}_H1.csv", DATA_DIR / f"{symbol.replace('.', '_')}_H1.csv"]:
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
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr = np.full(n, np.nan)
    if n <= period: return atr
    atr[period] = float(np.mean(tr[1:period+1]))
    for i in range(period+1, n):
        atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    return atr


def detect_swings_at(highs, lows, i, min_bars=SWING_MIN_BARS):
    n = len(highs)
    is_h = is_l = False
    if min_bars <= i < n - min_bars:
        is_h = all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, min_bars+1))
        is_l = all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, min_bars+1))
    return is_h, is_l


def detect_obs(df, atr):
    opens = df["open"].values; highs = df["high"].values
    lows = df["low"].values; closes = df["close"].values
    n = len(df); obs = []
    swings = []; last_h = None; last_l = None; cs = "neutral"
    for i in range(WARMUP_CANDLES, n - SWING_MIN_BARS):
        if np.isnan(atr[i]) or atr[i] == 0: continue
        isH, isL = detect_swings_at(highs, lows, i)
        if isH:
            lbl = "HH" if (last_h is None or highs[i] > last_h["price"]) else "LH"
            s = {"index": i, "price": highs[i], "type": "high", "classification": lbl, "consumed": False}
            swings.append(s); last_h = s
        if isL:
            lbl = "HL" if (last_l is None or lows[i] > last_l["price"]) else "LL"
            s = {"index": i, "price": lows[i], "type": "low", "classification": lbl, "consumed": False}
            swings.append(s); last_l = s
        if len(swings) < 4: continue
        hl = [s for s in swings if s["type"] == "high" and not s["consumed"]]
        ll = [s for s in swings if s["type"] == "low" and not s["consumed"]]
        if not hl or not ll: continue
        lsh = hl[-1]
        if closes[i] > lsh["price"] and i > lsh["index"] + 1:
            disp = (closes[i] - lsh["price"]) / atr[i]
            body = abs(closes[i] - opens[i]) / (highs[i] - lows[i] + 1e-10)
            if disp >= MIN_DISPLACEMENT_ATR and body >= BODY_RATIO_MIN:
                et = "CHoCH" if cs == "bearish" else "BOS"; cs = "bullish"
                for k in range(i - 1, max(i - 11, WARMUP_CANDLES - 1), -1):
                    if closes[k] < opens[k]:
                        obs.append({"direction": "bullish", "ob_high": highs[k], "ob_low": lows[k],
                                    "formation_index": k, "event_type": et, "break_index": i})
                        lsh["consumed"] = True; break
        lsl = ll[-1]
        if closes[i] < lsl["price"] and i > lsl["index"] + 1:
            disp = (lsl["price"] - closes[i]) / atr[i]
            body = abs(closes[i] - opens[i]) / (highs[i] - lows[i] + 1e-10)
            if disp >= MIN_DISPLACEMENT_ATR and body >= BODY_RATIO_MIN:
                et = "CHoCH" if cs == "bullish" else "BOS"; cs = "bearish"
                for k in range(i - 1, max(i - 11, WARMUP_CANDLES - 1), -1):
                    if closes[k] > opens[k]:
                        obs.append({"direction": "bearish", "ob_high": highs[k], "ob_low": lows[k],
                                    "formation_index": k, "event_type": et, "break_index": i})
                        lsl["consumed"] = True; break
    return obs


def measure_cont(ri, direction, oh, ol, highs, lows, closes, atr, n):
    if ri >= n - 1 or np.isnan(atr[ri]) or atr[ri] == 0:
        return False
    entry = closes[ri]
    td = TARGET_ATR_MULT * atr[ri]; sd = STOP_ATR_MULT * atr[ri]
    if direction == "bullish":
        tgt = entry + td; stp = entry - sd
    else:
        tgt = entry - td; stp = entry + sd
    end = min(ri + 1 + CONTINUATION_WINDOW, n)
    for j in range(ri + 1, end):
        if direction == "bullish":
            if highs[j] >= tgt: return True
            if lows[j] <= stp:  return False
        else:
            if lows[j] <= tgt:  return True
            if highs[j] >= stp: return False
    return False


def research_events(ob, highs, lows, closes, atr):
    n = len(highs)
    start = ob["formation_index"] + 1
    end = min(start + RETEST_WINDOW, n)
    direction = ob["direction"]; oh = ob["ob_high"]; ol = ob["ob_low"]
    evs = []
    in_zone = False; tc = 0
    for j in range(start, end):
        touching = (lows[j] <= oh) if direction == "bullish" else (highs[j] >= ol)
        if touching and not in_zone:
            in_zone = True; tc += 1
            cont = measure_cont(j, direction, oh, ol, highs, lows, closes, atr, n)
            evs.append({"retest_index": j, "touch_number_research": tc,
                        "formation_age_bars": j - ob["formation_index"],
                        "continuation": int(bool(cont))})
        elif not touching:
            in_zone = False
    return evs


def prod_touch_count_in_window(ob, highs, lows, window_start, window_end_inclusive):
    """Count candles in [max(formation+1, window_start) .. window_end_inclusive]
    whose range overlaps [ob_low, ob_high]."""
    start = max(ob["formation_index"] + 1, window_start)
    end = window_end_inclusive  # inclusive
    if start > end: return 0
    oh = ob["ob_high"]; ol = ob["ob_low"]
    count = 0
    for j in range(start, end + 1):
        if highs[j] >= ol and lows[j] <= oh:
            count += 1
    return count


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
        revs = research_events(ob, highs, lows, closes, atr)
        for ev in revs:
            ri = ev["retest_index"]
            # Live gate: candle at ri is the latest candle (just closed). The
            # gate window is [ri - 167 .. ri], i.e. 168 bars ending at ri.
            win_start = max(0, ri - (H1_LOOKBACK - 1))
            win_end = ri  # inclusive
            # Is the OB still detectable? formation_index must be inside window.
            ob_in_window = (ob["formation_index"] >= win_start) and (ob["formation_index"] <= win_end)
            prod_tc_live = prod_touch_count_in_window(ob, highs, lows, win_start, win_end)
            rows.append({
                "symbol": symbol,
                "formation_index": ob["formation_index"],
                "retest_index": ri,
                "touch_number_research": ev["touch_number_research"],
                "formation_age_bars": ev["formation_age_bars"],
                "ob_in_168_bar_window": ob_in_window,
                "touch_count_prod_live_window": prod_tc_live,
                "continuation": ev["continuation"],
            })
    return rows


def main():
    all_rows = []
    for s in INSTRUMENTS:
        all_rows.extend(run_instrument(s))
    df = pd.DataFrame(all_rows)
    out = Path(__file__).parent / "live_gate_sim.parquet"
    df.to_parquet(out, index=False)
    print(f"\n{len(df):,} rows -> {out}")

    # Filter to rows where OB would actually be detectable in live window.
    df_live = df[df["ob_in_168_bar_window"]].copy()
    print(f"\n{len(df_live):,} rows where OB is still in the 168-bar window at eval time")
    print(f"  (rows lost because formation is >168 bars before retest: {len(df) - len(df_live):,})")

    # Research touch-1 retention under realistic live gate
    ft_all = df_live[df_live["touch_number_research"] == 1]
    print(f"\nResearch touch-1 events still detectable in live window: {len(ft_all):,}")

    # Under live gate: prod_live >= 2 rejects.
    would_reject = ft_all["touch_count_prod_live_window"] >= 2
    n_rej = would_reject.sum()
    print(f"  Of these, would the live gate reject (prod_live >= 2): {n_rej:,} ({n_rej/len(ft_all)*100:.1f}%)")
    if n_rej > 0:
        cont_rej = ft_all.loc[would_reject, "continuation"].sum()
        print(f"  WR of those rejected first-touch (under research semantics): {cont_rej}/{n_rej} = {cont_rej/n_rej*100:.1f}%")
    kept = ft_all[~would_reject]
    print(f"  Would pass: {len(kept):,}, WR = {kept['continuation'].sum()/len(kept)*100:.1f}%")

    # Histogram of prod_live touch count at retest
    print("\n=== Distribution of production touch_count at retest moment (live-window) ===")
    print("For RESEARCH TOUCH-1 events:")
    vc = ft_all["touch_count_prod_live_window"].value_counts().sort_index()
    print(vc.head(15).to_string())

    # WR by prod_live for all rows (live-detectable)
    print("\n=== WR by prod_live touch_count (all live-detectable events) ===")
    df_live["tcpl_clip"] = df_live["touch_count_prod_live_window"].clip(upper=10).astype(int)
    g = df_live.groupby("tcpl_clip").agg(
        n=("continuation", "size"), cont_n=("continuation", "sum"),
    )
    g["wr"] = g["cont_n"] / g["n"] * 100
    print(g.to_string())

    # The gate-level simulation: apply prod_live >= 2 to ALL live-detectable OBs.
    print("\n=== Gate simulation: reject all prod_live >= 2 ===")
    gate_pass = df_live["touch_count_prod_live_window"] < 2
    n_pass = gate_pass.sum(); cont_pass = df_live.loc[gate_pass, "continuation"].sum()
    n_rej_all = (~gate_pass).sum(); cont_rej_all = df_live.loc[~gate_pass, "continuation"].sum()
    print(f"  Passed: {n_pass:,} events, WR {cont_pass/n_pass*100:.1f}%")
    print(f"  Rejected: {n_rej_all:,} events, WR of rejected {cont_rej_all/n_rej_all*100:.1f}%")

    # Counterfactual: if gate were instead 'research_touch_number >= 2 → reject'
    print("\n=== Counterfactual: 'research touch_number >= 2 rejects' (the intended semantic) ===")
    gate_r_pass = df_live["touch_number_research"] < 2
    n_pr = gate_r_pass.sum(); cr_pr = df_live.loc[gate_r_pass, "continuation"].sum()
    n_rr = (~gate_r_pass).sum(); cr_rr = df_live.loc[~gate_r_pass, "continuation"].sum()
    print(f"  Passed: {n_pr:,} events, WR {cr_pr/n_pr*100:.1f}%")
    print(f"  Rejected: {n_rr:,} events, WR of rejected {cr_rr/n_rr*100:.1f}%")

    # Find a prod_live threshold T s.t. 'prod_live < T' approximately matches
    # 'research_touch == 1' pass set.
    print("\n=== Calibration: what prod_live threshold recovers research touch==1 pass rate? ===")
    best_diff = 1e9; best_T = None
    target_wr = cr_pr / n_pr * 100  # WR on research touch-1
    target_n = n_pr
    for T in range(1, 15):
        pass_mask = df_live["touch_count_prod_live_window"] < T
        n = pass_mask.sum()
        if n == 0: continue
        wr = df_live.loc[pass_mask, "continuation"].sum() / n * 100
        # Diagnostic: how close to target (WR ~= 72.7%, n ~= 23,575)
        line = f"  T={T:>2}: pass n={n:>6,}, WR={wr:5.1f}%"
        if T == 2:
            line += " <== current gate"
        print(line)

    # Equivalence table
    print("\n=== Research-touch vs prod_live_touch cross-tabulation (first 5 research touches) ===")
    ct = pd.crosstab(df_live["touch_number_research"].clip(upper=5),
                     df_live["touch_count_prod_live_window"].clip(upper=10),
                     margins=True, margins_name="All")
    print(ct.to_string())


if __name__ == "__main__":
    main()
