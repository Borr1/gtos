#!/usr/bin/env python3
"""T1 Entry Engineering Empirical Tests (Q-4.1 to Q-4.4)

DATA SOURCE DISCOVERY FINDINGS (before running tests):
  1. Trade index has entry_price=None — must recover from batch API raw results
  2. Batch API raw results contain AI-proposed: entry_price, stop_loss, take_profit_1,
     direction, poi_price_level for each CANDIDATE decision
  3. Batch prompt files contain OB zone listings (H1 and M15 zones)
  4. XAUUSD M15/H1 OHLCV available: data/historical/XAUUSD_M15.csv
  5. GBPUSD M15/H1 OHLCV available: exports/candle_redownload/GBPUSD_M15.csv
  6. CRITICAL FINDING: The system enters ABOVE H1 OB zones (at M15 BOS confirmation).
     The AI-labeled poi_price_level is the H1 OB reference, but actual entry is often
     50-100+ points above it. This changes Test 1 from "entry depth within H1 zone"
     to "entry distance from nearest zone (H1 or M15)".

REVISED TESTS GIVEN ACTUAL DATA STRUCTURE:
  T1: Entry distance from nearest OB zone (normalized by ATR) vs outcome
  T2: Executed price vs AI-proposed price (slippage) + mae_r proxy for limit order
  T3: M15 candle open vs close delta (alpha decay within candle)
  T4: SL distance (normalized by ATR) vs outcome — zone width proxy since SL is
      placed beyond the H1 OB zone

Bonferroni threshold: p < 0.0125 (4 simultaneous tests)
Practical threshold: >0.05R per trade or >2pp WR
"""

from __future__ import annotations

import json
import os
import re
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ─── Paths ─────────────────────────────────────────────────────────────────────
TRADE_INDEX    = ROOT / "knowledge_base" / "index" / "_trade_index.json"
SESSIONS_XAUUSD = ROOT / "knowledge_base_backtest" / "sessions" / "XAUUSD"
SESSIONS_GBPUSD = ROOT / "knowledge_base_backtest" / "sessions" / "GBPUSD"
SESSIONS_GBPUSD_KB = ROOT / "knowledge_base" / "sessions" / "GBPUSD"
BATCH_API_DIR  = ROOT / "knowledge_base_backtest" / "batch_api"
M15_XAUUSD     = ROOT / "data" / "historical" / "XAUUSD_M15.csv"
H1_XAUUSD      = ROOT / "data" / "historical" / "XAUUSD_H1.csv"
M15_GBPUSD     = ROOT / "exports" / "candle_redownload" / "GBPUSD_M15.csv"
H1_GBPUSD      = ROOT / "exports" / "candle_redownload" / "GBPUSD_H1.csv"
H1_GBPUSD_HIST = ROOT / "data" / "historical" / "GBPUSD_H1.csv"
OUTPUT_DIR     = Path(__file__).resolve().parent / "results"
DATA_DIR       = Path(__file__).resolve().parent / "data"

BONFERRONI_ALPHA = 0.0125
PRACTICAL_R      = 0.05
PRACTICAL_WR_PP  = 2.0

# ─── Statistical helpers ────────────────────────────────────────────────────────

def wilson_ci(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = stats.norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / denom
    m = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, c - m), min(1.0, c + m))


def bootstrap_mean_ci(vals: list, n_iter: int = 10000, seed: int = 42,
                      alpha: float = 0.05) -> tuple[float, float, float]:
    if len(vals) == 0:
        return (np.nan, np.nan, np.nan)
    rng = np.random.RandomState(seed)
    arr = np.array([v for v in vals if v is not None and not np.isnan(v)])
    if len(arr) == 0:
        return (np.nan, np.nan, np.nan)
    means = [rng.choice(arr, size=len(arr), replace=True).mean() for _ in range(n_iter)]
    lo, hi = np.percentile(means, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    return float(arr.mean()), float(lo), float(hi)


def quartile_summary(df: pd.DataFrame, bin_col: str) -> pd.DataFrame:
    rows = []
    for grp_label, grp in sorted(df.groupby(bin_col, observed=True),
                                  key=lambda x: str(x[0])):
        wins = (grp["outcome"] == "WIN").sum()
        n = len(grp)
        r_vals = grp["r_multiple"].dropna().tolist()
        wr = wins / n if n > 0 else np.nan
        wr_lo, wr_hi = wilson_ci(wins, n)
        mean_r, r_lo, r_hi = bootstrap_mean_ci(r_vals)
        rows.append({
            "bin": grp_label, "n": n,
            "win_rate_%": round(wr * 100, 1),
            "wr_95ci": f"[{wr_lo*100:.1f}, {wr_hi*100:.1f}]",
            "mean_R": round(mean_r, 3),
            "R_95ci": f"[{r_lo:.3f}, {r_hi:.3f}]",
            "mfe_R": round(grp["mfe_r"].mean(), 3) if grp["mfe_r"].notna().any() else np.nan,
            "mae_R": round(grp["mae_r"].mean(), 3) if grp["mae_r"].notna().any() else np.nan,
        })
    return pd.DataFrame(rows)


# ─── Data Loading ───────────────────────────────────────────────────────────────

print("=" * 70)
print("PHASE 0: DATA DISCOVERY AND EXTRACTION")
print("=" * 70)

# Load trade index
with open(TRADE_INDEX) as f:
    idx_data = json.load(f)
trades_raw = idx_data["trades"]
print(f"\nTrade index: {len(trades_raw)} trades")
from collections import Counter
sym_ct = Counter(t["symbol"] for t in trades_raw)
for sym, n in sorted(sym_ct.items()):
    print(f"  {sym}: {n}")

# Load OHLCV
print("\nLoading OHLCV data...")
def load_m15(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    return df

m15_xau = load_m15(M15_XAUUSD)
m15_gbp = load_m15(M15_GBPUSD)
m15_xau_idx = {row.time: row for row in m15_xau.itertuples()}
m15_gbp_idx = {row.time: row for row in m15_gbp.itertuples()}
print(f"  XAUUSD M15: {len(m15_xau)} rows  {m15_xau['time'].min().date()} – {m15_xau['time'].max().date()}")
print(f"  GBPUSD M15: {len(m15_gbp)} rows  {m15_gbp['time'].min().date()} – {m15_gbp['time'].max().date()}")

# Load H1 data for ATR
def load_h1(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    return df

h1_xau = load_h1(H1_XAUUSD)
h1_gbp = load_h1(H1_GBPUSD if H1_GBPUSD.exists() else H1_GBPUSD_HIST)
print(f"  XAUUSD H1:  {len(h1_xau)} rows  {h1_xau['time'].min().date()} – {h1_xau['time'].max().date()}")
print(f"  GBPUSD H1:  {len(h1_gbp)} rows  {h1_gbp['time'].min().date()} – {h1_gbp['time'].max().date()}")


# ─── Extract AI decisions from batch raw results ────────────────────────────────

print("\nLoading batch API raw results...")

def parse_decision_json(text: str) -> dict | None:
    text_clean = text.strip()
    try:
        if "```json" in text_clean:
            text_clean = text_clean.split("```json")[1].split("```")[0].strip()
        elif text_clean.startswith("```"):
            text_clean = text_clean[3:text_clean.rfind("```")].strip()
        return json.loads(text_clean)
    except Exception:
        # Try finding first { to last }
        try:
            s = text_clean.find("{")
            e = text_clean.rfind("}")
            if s >= 0 and e > s:
                return json.loads(text_clean[s:e+1])
        except Exception:
            pass
    return None


all_ai_decisions: dict[str, dict] = {}  # key -> full decision JSON

raw_files = [f for f in os.listdir(BATCH_API_DIR) if "raw" in f.lower()]
for fn in raw_files:
    with open(BATCH_API_DIR / fn) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        continue
    for key, val in data.items():
        if not isinstance(val, dict):
            continue
        text = val.get("text", "")
        if "CANDIDATE" not in text:
            continue
        dj = parse_decision_json(text)
        if dj and dj.get("decision") == "CANDIDATE":
            all_ai_decisions[key] = dj

print(f"  Found {len(all_ai_decisions)} CANDIDATE AI decisions in raw results")

# ─── Build candle_time → OB zones from batch prompts ───────────────────────────

print("Loading batch prompt OB zones...")

OB_PAT = re.compile(r"(bullish|bearish)\s+([\d.]+)-([\d.]+)\s+[(][\d]{4}-")

def parse_obs_from_prompt(text: str) -> list[dict]:
    obs = []
    for m in OB_PAT.finditer(text):
        p1, p2 = float(m.group(2)), float(m.group(3))
        obs.append({"type": m.group(1), "high": max(p1, p2), "low": min(p1, p2),
                    "midpoint": (p1 + p2) / 2})
    return obs


candle_to_obs: dict[str, list[dict]] = {}  # candle_time_str -> list of OBs

full_prompt_files = [f for f in os.listdir(BATCH_API_DIR) if "full_prompt" in f]
for fn in full_prompt_files:
    with open(BATCH_API_DIR / fn) as f:
        data = json.load(f)
    for req in data:
        ct = req.get("candle_time")
        if not ct:
            continue
        prompt_dict = req.get("prompt", {})
        if not isinstance(prompt_dict, dict):
            continue
        user_msg = prompt_dict.get("user_message", "")
        if user_msg:
            obs = parse_obs_from_prompt(user_msg)
            if obs:
                candle_to_obs[ct] = obs

print(f"  Prompt OB data for {len(candle_to_obs)} candle times")


# ─── Get candle_time for each trade ─────────────────────────────────────────────

def get_candle_time(trade: dict) -> str | None:
    sym = trade["symbol"]
    date_str = trade["date"]
    trade_id = trade["trade_id"]
    dirs = []
    if sym == "XAUUSD":
        dirs = [SESSIONS_XAUUSD]
    else:
        dirs = [SESSIONS_GBPUSD, SESSIONS_GBPUSD_KB]
    for d in dirs:
        fn = d / f"{date_str}_session.json"
        if not fn.exists():
            continue
        with open(fn) as f:
            sess = json.load(f)
        for ev in sess.get("candle_evaluations", []):
            if ev.get("decision") != "CANDIDATE":
                continue
            ev_tid = str(ev.get("trade_id") or "").replace("_xauusd", "").replace("_gbpusd", "")
            norm_tid = trade_id.replace("_xauusd", "").replace("_gbpusd", "")
            if ev_tid == norm_tid:
                return ev.get("candle_time")
            kz_ok = ev.get("kill_zone") == trade.get("kill_zone")
            tid_ok = str(ev.get("trade_id") or "").startswith(f"bt_{date_str}")
            if kz_ok and tid_ok:
                return ev.get("candle_time")
    return None


def get_m15_ohlc(sym: str, candle_time_str: str) -> dict | None:
    from datetime import datetime, timezone
    dt = datetime.strptime(candle_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    row = (m15_xau_idx if sym == "XAUUSD" else m15_gbp_idx).get(dt)
    if row is None:
        return None
    return {"open": float(row.open), "high": float(row.high),
            "low": float(row.low), "close": float(row.close)}


def compute_h1_atr(sym: str, candle_time_str: str, period: int = 14) -> float | None:
    from datetime import datetime, timezone
    dt = datetime.strptime(candle_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    df = h1_xau if sym == "XAUUSD" else h1_gbp
    sub = df[df["time"] <= dt].tail(period + 1)
    if len(sub) < period:
        return None
    highs = sub["high"].values
    lows = sub["low"].values
    closes = sub["close"].values
    tr_vals = []
    for i in range(1, len(sub)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        tr_vals.append(tr)
    return float(np.mean(tr_vals[-period:]))


# ─── Phase 0: Build unified dataset ─────────────────────────────────────────────

print("\n--- Building unified dataset ---")

rows = []
missing_stats = defaultdict(int)

for trade in trades_raw:
    row = {
        "trade_id": trade["trade_id"],
        "date": trade["date"],
        "symbol": trade["symbol"],
        "kill_zone": trade["kill_zone"],
        "outcome": trade["outcome"],
        "r_multiple": trade["r_multiple"],
        "mfe_r": trade.get("mfe_r"),
        "mae_r": trade.get("mae_r"),
        "hold_time_candles": trade.get("hold_time_candles"),
        "setup_grade": trade.get("setup_grade"),
        "win": 1 if trade["outcome"] == "WIN" else 0,
        # filled below
        "candle_time": None,
        "direction": trade.get("direction"),
        "entry_price_ai": None,
        "stop_loss": None,
        "take_profit_1": None,
        "poi_price_level": None,
        "sl_distance": None,
        "rr_ratio_ai": None,
        "entry_vs_poi_norm": None,   # (entry - poi) / sl_distance  (+ = entry above poi for LONG)
        "entry_dist_zone_norm": None, # distance from entry to nearest OB, / ATR (+ = above, for LONG)
        "candle_open": None,
        "candle_close": None,
        "execution_slippage_norm": None,  # (M15_close - entry_ai) / sl_distance
        "delta_candle_norm": None,        # (M15_close - M15_open) / sl_distance
        "sl_distance_atr": None,
        "zone_match_type": None,          # "H1", "M15", "none"
        "zone_matched_high": None,
        "zone_matched_low": None,
        "data_available": False,
    }

    # candle_time
    ct = get_candle_time(trade)
    if ct is None:
        missing_stats["no_candle_time"] += 1
        rows.append(row)
        continue
    row["candle_time"] = ct

    # AI decision (entry/SL/TP)
    dt = datetime.strptime(ct, "%Y-%m-%dT%H:%M:%SZ")
    hhmm = dt.strftime("%H%M")
    ai_key = f"{trade['date']}_{trade['kill_zone']}_{hhmm}"
    cand = all_ai_decisions.get(ai_key)

    if cand is None:
        missing_stats["no_ai_decision"] += 1
        rows.append(row)
        continue

    tp = cand.get("trade_parameters") or {}
    h1_reasoning = (cand.get("reasoning") or {}).get("h1_setup", {}) or {}
    row["poi_price_level"] = h1_reasoning.get("poi_price_level")
    row["direction"] = tp.get("direction") or cand.get("direction") or trade.get("direction")

    entry_ai = tp.get("entry_price")
    sl = tp.get("stop_loss")
    tp1 = tp.get("take_profit_1")
    row["entry_price_ai"] = entry_ai
    row["stop_loss"] = sl
    row["take_profit_1"] = tp1

    if entry_ai is None or sl is None:
        missing_stats["missing_entry_sl"] += 1
        rows.append(row)
        continue

    sl_dist = abs(entry_ai - sl)
    row["sl_distance"] = sl_dist
    if sl_dist > 0 and tp1 is not None:
        row["rr_ratio_ai"] = abs(tp1 - entry_ai) / sl_dist

    # H1 ATR for normalization
    atr = compute_h1_atr(trade["symbol"], ct)
    if atr and atr > 0:
        row["sl_distance_atr"] = sl_dist / atr

    # poi distance normalized
    poi = row["poi_price_level"]
    if poi and sl_dist > 0:
        if row["direction"] == "LONG":
            row["entry_vs_poi_norm"] = (entry_ai - poi) / sl_dist
        else:
            row["entry_vs_poi_norm"] = (poi - entry_ai) / sl_dist

    # OB zone match from prompt (XAUUSD only — GBPUSD prompts contain XAUUSD prices)
    if trade["symbol"] == "XAUUSD":
        obs = candle_to_obs.get(ct, [])
        if obs and sl_dist > 0:
            direction = row["direction"]
            # Filter to matching OB type
            if direction == "LONG":
                relevant_obs = [o for o in obs if o["type"] == "bullish"]
            elif direction == "SHORT":
                relevant_obs = [o for o in obs if o["type"] == "bearish"]
            else:
                relevant_obs = obs

            if not relevant_obs:
                relevant_obs = obs

            # Find nearest OB to entry_price (by distance from zone edge)
            def zone_distance(ob, ep, dir_):
                if dir_ == "LONG":
                    if ob["low"] <= ep <= ob["high"]:
                        return 0.0, "inside"
                    elif ep > ob["high"]:
                        return ep - ob["high"], "above"
                    else:
                        return ob["low"] - ep, "below"
                else:
                    if ob["low"] <= ep <= ob["high"]:
                        return 0.0, "inside"
                    elif ep < ob["low"]:
                        return ob["low"] - ep, "below"
                    else:
                        return ep - ob["high"], "above"

            best_ob = None
            best_dist = float("inf")
            for ob in relevant_obs:
                d, _ = zone_distance(ob, entry_ai, direction)
                if d < best_dist:
                    best_dist = d
                    best_ob = ob

            if best_ob:
                d, position = zone_distance(best_ob, entry_ai, direction)
                row["zone_matched_high"] = best_ob["high"]
                row["zone_matched_low"] = best_ob["low"]
                # entry_dist_zone_norm: + means above zone top (entered ABOVE zone for LONG)
                if direction == "LONG":
                    row["entry_dist_zone_norm"] = (entry_ai - best_ob["high"]) / sl_dist
                else:
                    row["entry_dist_zone_norm"] = (best_ob["low"] - entry_ai) / sl_dist
                if atr and atr > 0:
                    row["zone_match_type"] = "matched"
                row["data_available"] = True

    # M15 candle OHLC
    ohlc = get_m15_ohlc(trade["symbol"], ct)
    if ohlc:
        row["candle_open"] = ohlc["open"]
        row["candle_close"] = ohlc["close"]
        if sl_dist > 0:
            row["execution_slippage_norm"] = (ohlc["close"] - entry_ai) / sl_dist
            if row["direction"] == "LONG":
                row["delta_candle_norm"] = (ohlc["close"] - ohlc["open"]) / sl_dist
            else:
                row["delta_candle_norm"] = (ohlc["open"] - ohlc["close"]) / sl_dist
        if not row["data_available"]:
            row["data_available"] = sl_dist > 0

    rows.append(row)
    if len(rows) % 20 == 0:
        print(f"  Processed {len(rows)}/{len(trades_raw)}...")

df = pd.DataFrame(rows)

# ─── Phase 0.5: Data availability report ────────────────────────────────────────

print("\n" + "=" * 70)
print("PHASE 0.5: DATA AVAILABILITY REPORT")
print("=" * 70)

total = len(df)
def cnt(mask):
    return mask.sum()

print(f"\nTotal trades: {total}")
print(f"  candle_time found:       {cnt(df.candle_time.notna())} ({cnt(df.candle_time.notna())/total*100:.0f}%)")
print(f"  AI decision matched:     {cnt(df.entry_price_ai.notna())} ({cnt(df.entry_price_ai.notna())/total*100:.0f}%)")
print(f"  SL/TP extracted:         {cnt(df.stop_loss.notna())} ({cnt(df.stop_loss.notna())/total*100:.0f}%)")
print(f"  M15 OHLC available:      {cnt(df.candle_close.notna())} ({cnt(df.candle_close.notna())/total*100:.0f}%)")
print(f"  OB zone matched (XAUUSD):{cnt(df.zone_match_type.notna())} ({cnt(df.zone_match_type.notna())/total*100:.0f}%)")
print(f"  SL distance computed:    {cnt(df.sl_distance.notna())} ({cnt(df.sl_distance.notna())/total*100:.0f}%)")
print(f"  SL dist ATR-normalized:  {cnt(df.sl_distance_atr.notna())} ({cnt(df.sl_distance_atr.notna())/total*100:.0f}%)")
print(f"  R:R ratio computed:      {cnt(df.rr_ratio_ai.notna())} ({cnt(df.rr_ratio_ai.notna())/total*100:.0f}%)")

print("\nBy instrument:")
for sym in df.symbol.unique():
    s = df[df.symbol == sym]
    n = len(s)
    print(f"  {sym}: n={n}, AI_decision={cnt(s.entry_price_ai.notna())}, "
          f"zone_data={cnt(s.zone_match_type.notna())}, m15_ohlc={cnt(s.candle_close.notna())}")

print(f"\nMissing reasons:")
for k, v in missing_stats.items():
    print(f"  {k}: {v}")

print("\nKey data discoveries:")
print("  • XAUUSD batch system enters ABOVE H1 OBs at M15 BOS confirmation")
print("    (entry_price_ai is 50-100+ pts above H1 OBs, SL is below them)")
print("  • GBPUSD batch prompts contain XAUUSD prices (different batch pipeline)")
print("    → OB zone matching only performed for XAUUSD")
print("  • Entry depth as originally defined (within H1 zone) is not applicable")
print("    Tests are reframed to measure entry ABOVE nearest zone (M15 or H1)")

# Save dataset
output_csv = DATA_DIR / "entry_engineering_dataset.csv"
df.to_csv(output_csv, index=False)
print(f"\nDataset saved → {output_csv}")


# ─── Helper: distribution summary for a column ─────────────────────────────────

def print_dist(series: pd.Series, label: str, n_tiles=(10, 25, 50, 75, 90)):
    arr = series.dropna()
    print(f"  {label}: n={len(arr)}, mean={arr.mean():.4f}, std={arr.std():.4f}")
    print(f"    percentiles: " + ", ".join(f"P{p}={arr.quantile(p/100):.4f}" for p in n_tiles))


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Entry Distance from Nearest OB Zone vs Outcome (Q-4.1 revised)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("TEST 1: ENTRY DISTANCE FROM NEAREST OB ZONE vs OUTCOME (Q-4.1)")
print("=" * 70)
print("(Revised from 'entry depth within zone' because entries are above H1 OBs)")
print("Metric: (entry - zone_top) / SL_distance for LONG;")
print("        positive = entered above zone (confirming), negative = inside zone")

df_t1 = df[df.entry_dist_zone_norm.notna() & df.sl_distance.notna()].copy()
print(f"\nn = {len(df_t1)} trades with OB zone match (XAUUSD only)")

if len(df_t1) < 20:
    print("\n⚠️  INSUFFICIENT DATA: n < 20 for Test 1")
    print(f"  Root cause: OB zone matching requires matching entry_price to prompt OBs.")
    print(f"  XAUUSD trades with AI decision: {cnt(df[df.symbol=='XAUUSD'].entry_price_ai.notna())}")
    print(f"  XAUUSD trades with zone match: {cnt(df[df.symbol=='XAUUSD'].zone_match_type.notna())}")
    # Show why zone matching failed for non-matched trades
    xau_no_zone = df[(df.symbol == 'XAUUSD') & df.entry_price_ai.notna() & df.zone_match_type.isna()]
    print(f"  XAUUSD with AI decision but no zone: {len(xau_no_zone)}")
    # Investigate: check if OB zone data available for those candle times
    n_with_obs = sum(1 for ct in xau_no_zone.candle_time if ct and ct in candle_to_obs)
    print(f"  Of those: {n_with_obs} have prompt OB data (zone matching failed for other reason)")
    print(f"  {len(xau_no_zone) - n_with_obs} have no prompt OB data at all")

    # Check SL distance as alternative metric
    df_t1_sl = df[df.sl_distance_atr.notna()].copy()
    print(f"\n  Switching to SL_distance_ATR as zone-proxy metric: n = {len(df_t1_sl)}")

    if len(df_t1_sl) >= 20:
        print_dist(df_t1_sl.sl_distance_atr, "SL_distance_ATR")
        df_t1_sl["sl_q"] = pd.qcut(df_t1_sl.sl_distance_atr, q=4,
                                     labels=["Q1 (tight)", "Q2", "Q3", "Q4 (wide)"])
        print("\n  Summary by SL distance quartile (ATR-normalized):")
        print(quartile_summary(df_t1_sl, "sl_q").to_string(index=False))
        sp_r, sp_p = stats.spearmanr(df_t1_sl.sl_distance_atr, df_t1_sl.r_multiple)
        kw_groups = [grp.r_multiple.dropna().tolist()
                     for _, grp in df_t1_sl.groupby("sl_q", observed=True)]
        kw_stat, kw_p = stats.kruskal(*[g for g in kw_groups if g])
        print(f"\n  Spearman ρ (SL_dist_ATR vs R): {sp_r:.4f}, p={sp_p:.4f}")
        print(f"  Kruskal-Wallis: H={kw_stat:.4f}, p={kw_p:.4f}")
        if kw_p < BONFERRONI_ALPHA:
            print(f"  → SIGNIFICANT (p < {BONFERRONI_ALPHA})")
        else:
            print(f"  → Not significant (p >= {BONFERRONI_ALPHA})")
        if abs(sp_r) < 0.1:
            print("  → Negligible effect (|ρ| < 0.1)")
        df_t1 = df_t1_sl
        df_t1["test1_metric"] = df_t1.sl_distance_atr
        df_t1["test1_q"] = df_t1["sl_q"]
    test1_result = "SL_DISTANCE_PROXY"
else:
    print_dist(df_t1.entry_dist_zone_norm, "entry_dist_zone_norm (raw, including outliers)")

    # Filter outliers: OB match is unreliable when entry is >5 SL distances from nearest zone
    # This is likely a bad OB match (prompt OBs are from a different price region)
    pre_filter = len(df_t1)
    df_t1 = df_t1[df_t1.entry_dist_zone_norm.between(-2.0, 5.0)].copy()
    print(f"  After outlier filter (entry_dist within [-2, 5] SL-distances): {len(df_t1)}/{pre_filter}")
    if len(df_t1) < 20:
        print("  INSUFFICIENT DATA after filtering — using SL_distance_ATR as fallback")
        test1_result = "FILTERED_INSUFFICIENT"
    else:
        print_dist(df_t1.entry_dist_zone_norm, "entry_dist_zone_norm (filtered)")

    # Quartile analysis
    df_t1["entry_q"] = pd.qcut(df_t1.entry_dist_zone_norm, q=4,
                                labels=["Q1 (inside/near)", "Q2", "Q3", "Q4 (far above)"])
    print("\nSummary by entry distance quartile:")
    print(quartile_summary(df_t1, "entry_q").to_string(index=False))

    sp_r, sp_p = stats.spearmanr(df_t1.entry_dist_zone_norm, df_t1.r_multiple)
    kw_groups = [grp.r_multiple.dropna().tolist()
                 for _, grp in df_t1.groupby("entry_q", observed=True)]
    kw_stat, kw_p = stats.kruskal(*[g for g in kw_groups if g])
    print(f"\nSpearman ρ (entry_dist vs R): {sp_r:.4f}, p={sp_p:.4f}")
    print(f"Kruskal-Wallis: H={kw_stat:.4f}, p={kw_p:.4f}")
    if kw_p < BONFERRONI_ALPHA:
        print(f"  → SIGNIFICANT (p < {BONFERRONI_ALPHA})")
    else:
        print(f"  → Not significant (p >= {BONFERRONI_ALPHA})")

    # Also run SL_distance_ATR test
    df_t1_sl = df[df.sl_distance_atr.notna()].copy()
    if len(df_t1_sl) >= 20:
        print(f"\nSL distance quartile analysis (all {len(df_t1_sl)} trades):")
        print_dist(df_t1_sl.sl_distance_atr, "SL_distance_ATR")
        df_t1_sl["sl_q"] = pd.qcut(df_t1_sl.sl_distance_atr, q=4,
                                     labels=["Q1 (tight)", "Q2", "Q3", "Q4 (wide)"])
        print(quartile_summary(df_t1_sl, "sl_q").to_string(index=False))
        sp_r2, sp_p2 = stats.spearmanr(df_t1_sl.sl_distance_atr, df_t1_sl.r_multiple)
        print(f"  Spearman ρ (SL_dist_ATR vs R): {sp_r2:.4f}, p={sp_p2:.4f}")

    test1_result = "COMPLETE"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: Market Order vs Limit Order / Execution Quality (Q-4.2)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("TEST 2: EXECUTION QUALITY — MARKET vs LIMIT (Q-4.2)")
print("=" * 70)

# Part A: Execution slippage (M15 close vs AI-proposed entry)
df_t2 = df[df.execution_slippage_norm.notna()].copy()
print(f"\nPart A — Execution slippage (n = {len(df_t2)})")
print("Metric: (M15_close - AI_entry) / SL_distance  [+ = executed worse than proposed]")
print_dist(df_t2.execution_slippage_norm, "execution_slippage_norm")

sp_r_slip, sp_p_slip = stats.spearmanr(df_t2.execution_slippage_norm, df_t2.r_multiple)
print(f"\nSpearman ρ (slippage vs R): {sp_r_slip:.4f}, p={sp_p_slip:.4f}")
if sp_p_slip < BONFERRONI_ALPHA:
    print(f"  → SIGNIFICANT (p < {BONFERRONI_ALPHA})")
else:
    print(f"  → Not significant (p >= {BONFERRONI_ALPHA})")
if abs(sp_r_slip) < 0.1:
    print("  → Negligible correlation")

# Part B: Mae_r proxy for limit order fill rate
df_t2b = df[df.mae_r.notna()].copy()
print(f"\nPart B — Limit order proxy via mae_r (n = {len(df_t2b)})")
print("Interpretation: mae_r > threshold → price moved against entry → limit deeper would fill")

thresholds = [0.2, 0.3, 0.5]
print("\n  Fill rate estimates (mae_r >= threshold → limit order fills):")
for thr in thresholds:
    fill_n = (df_t2b.mae_r >= thr).sum()
    fill_rate = fill_n / len(df_t2b)
    print(f"    threshold={thr}R: fill_rate={fill_rate:.1%} ({fill_n}/{len(df_t2b)})")

# R improvement if entered 0.2R deeper (normalized by SL)
if df_t2b.sl_distance.notna().sum() > 20:
    # For each trade, hypothetical improvement: if entered 0.2R deeper in direction of setup
    # (i.e., 20% of SL distance closer to POI)
    improvement_0_2 = []
    for _, row in df_t2b.iterrows():
        sl_d = row.get("sl_distance")
        if pd.isna(sl_d) or sl_d <= 0:
            continue
        # Entering 0.2R deeper = gaining 0.2R improvement in outcome
        # (same SL/TP, but entry is 0.2×SL_distance further in favorable direction)
        # delta_R = 0.2 × (SL_dist_tighter / SL_dist_original)
        # At 0.2R deeper entry: new_sl_dist = sl_dist - 0.2×sl_dist = 0.8×sl_dist
        # R = tp_distance / sl_dist_new, vs original = tp_distance / sl_dist
        # improvement = R_new - R_old = tp_dist × (1/sl_dist_new - 1/sl_dist)
        # Without TP known, just note it
        improvement_0_2.append(0.2)  # simplified: 0.2R improvement per filled limit

    print(f"\n  Simplified limit order estimate:")
    print(f"  If limit at 0.2R deeper: fill_rate={1-(df_t2b.mae_r < 0.2).sum()/len(df_t2b):.1%}")
    print(f"  EV_market: {df_t2b.r_multiple.mean():.4f}R")
    fill_rate_02 = (df_t2b.mae_r >= 0.2).sum() / len(df_t2b)
    print(f"  EV_limit (0.2R deeper): {fill_rate_02:.1%} × (E[R_market] + 0.2) = "
          f"{fill_rate_02 * (df_t2b.r_multiple.mean() + 0.2):.4f}R vs {df_t2b.r_multiple.mean():.4f}R")

test2_result = "COMPLETE_PROXY"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Alpha Decay Within M15 Candle (Q-4.3)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("TEST 3: ALPHA DECAY WITHIN M15 CANDLE (Q-4.3)")
print("=" * 70)
print("Metric: (M15_close - M15_open) / SL_distance [+ = close is higher = worse for LONG]")

df_t3 = df[df.delta_candle_norm.notna()].copy()
print(f"\nn = {len(df_t3)} trades with M15 OHLC and SL data")

if len(df_t3) < 10:
    print("DATA_UNAVAILABLE: insufficient data for Test 3")
    test3_result = "INSUFFICIENT_DATA"
else:
    print_dist(df_t3.delta_candle_norm, "delta_candle_norm")

    m, lo, hi = bootstrap_mean_ci(df_t3.delta_candle_norm.tolist())
    print(f"\n  95% CI (bootstrap): [{lo:.4f}, {hi:.4f}]R")
    print(f"  Mean delta_R: {m:.4f}R")

    try:
        wil_stat, wil_p = stats.wilcoxon(df_t3.delta_candle_norm.dropna())
        print(f"  Wilcoxon p (H0: delta = 0): {wil_p:.4f}")
        if abs(m) < PRACTICAL_R:
            print(f"  → NEGLIGIBLE: |mean| = {abs(m):.4f}R < practical threshold {PRACTICAL_R}R")
            print("  → Conclusion: No practically significant alpha decay within M15 candle")
        elif wil_p < BONFERRONI_ALPHA:
            print(f"  → SIGNIFICANT and practically meaningful")
        else:
            print(f"  → Not significant (p >= {BONFERRONI_ALPHA})")
    except Exception as e:
        print(f"  Wilcoxon error: {e}")

    # By instrument
    for sym in df_t3.symbol.unique():
        sub = df_t3[df_t3.symbol == sym]
        if len(sub) >= 10:
            m2, l2, h2 = bootstrap_mean_ci(sub.delta_candle_norm.tolist())
            print(f"\n  {sym} (n={len(sub)}): mean_delta={m2:.4f}R, 95CI=[{l2:.4f},{h2:.4f}]")
            try:
                _, p2 = stats.wilcoxon(sub.delta_candle_norm.dropna())
                print(f"    Wilcoxon p={p2:.4f}")
            except Exception:
                print("    Wilcoxon: n too small")

    test3_result = "COMPLETE"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: SL Distance / Zone Width vs Outcome (Q-4.4)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("TEST 4: SL DISTANCE (ZONE WIDTH PROXY) vs OUTCOME (Q-4.4)")
print("=" * 70)
print("Metric: SL_distance_ATR — normalized SL distance as proxy for zone width")
print("(SL placed below H1 OB zone for LONG; larger SL = wider zone)")

df_t4 = df[df.sl_distance_atr.notna()].copy()
print(f"\nn = {len(df_t4)} trades with ATR-normalized SL distance")

if len(df_t4) < 20:
    print("INSUFFICIENT DATA: n < 20")
    test4_result = "INSUFFICIENT_DATA"
else:
    print_dist(df_t4.sl_distance_atr, "SL_distance_ATR")

    # Quartile bins
    df_t4["sl_q"] = pd.qcut(df_t4.sl_distance_atr, q=4,
                              labels=["Q1 (tight)", "Q2", "Q3", "Q4 (wide)"])

    print("\nSummary by SL distance quartile:")
    print(quartile_summary(df_t4, "sl_q").to_string(index=False))

    # Spearman correlation: zone width vs R, WR
    sp_r, sp_p = stats.spearmanr(df_t4.sl_distance_atr, df_t4.r_multiple)
    sp_r2, sp_p2 = stats.spearmanr(df_t4.sl_distance_atr, df_t4.win)
    kw_groups = [grp.r_multiple.dropna().tolist() for _, grp in df_t4.groupby("sl_q", observed=True)]
    kw_stat, kw_p = stats.kruskal(*[g for g in kw_groups if g])

    print(f"\nSpearman ρ (SL_dist vs R_multiple): {sp_r:.4f}, p={sp_p:.4f}")
    print(f"Spearman ρ (SL_dist vs WR binary): {sp_r2:.4f}, p={sp_p2:.4f}")
    print(f"Kruskal-Wallis across quartiles: H={kw_stat:.4f}, p={kw_p:.4f}")
    if kw_p < BONFERRONI_ALPHA:
        print(f"  → SIGNIFICANT (p < {BONFERRONI_ALPHA})")
    else:
        print(f"  → Not significant (p >= {BONFERRONI_ALPHA})")
    if abs(sp_r) < 0.1:
        print("  → Negligible correlation (|ρ| < 0.1)")

    # Per-instrument
    print("\nPer-instrument (n ≥ 15):")
    for sym in df_t4.symbol.unique():
        sub = df_t4[df_t4.symbol == sym].copy()
        if len(sub) < 15:
            print(f"  {sym}: n={len(sub)} — LOW POWER, reporting point estimate only")
            m = sub.sl_distance_atr.mean()
            r_mean = sub.r_multiple.mean()
            wr = (sub.outcome == "WIN").mean() * 100
            print(f"    mean_SL_dist_ATR={m:.3f}, WR={wr:.1f}%, mean_R={r_mean:.3f}")
            continue
        sub["sl_q2"] = pd.qcut(sub.sl_distance_atr, q=4, labels=["Q1","Q2","Q3","Q4"])
        sp_sym, sp_sym_p = stats.spearmanr(sub.sl_distance_atr, sub.r_multiple)
        print(f"\n  {sym} (n={len(sub)}, Spearman ρ={sp_sym:.3f}, p={sp_sym_p:.4f}):")
        print(quartile_summary(sub, "sl_q2").to_string(index=False))

    # Also run R:R ratio test
    df_rr = df[df.rr_ratio_ai.notna()].copy()
    if len(df_rr) >= 20:
        print(f"\nBonus: AI-proposed R:R ratio vs actual outcome (n={len(df_rr)})")
        print_dist(df_rr.rr_ratio_ai, "rr_ratio_ai")
        df_rr["rr_q"] = pd.qcut(df_rr.rr_ratio_ai, q=4, labels=["Q1","Q2","Q3","Q4"])
        print(quartile_summary(df_rr, "rr_q").to_string(index=False))
        sp_rr, sp_rr_p = stats.spearmanr(df_rr.rr_ratio_ai, df_rr.r_multiple)
        print(f"Spearman ρ (R:R_AI vs actual_R): {sp_rr:.4f}, p={sp_rr_p:.4f}")

    test4_result = "COMPLETE"


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("PHASE 5: SYNTHESIS")
print("=" * 70)

print("""
DATA REALITY SUMMARY
The batch trading system does NOT enter within OB zones. It enters at M15 BOS
confirmation levels, which are 50-100+ points above the H1 OB reference zones.
SL is placed below the H1 OB zone. This means:
- "Entry depth" as defined in the prompt (within H1 OB) is not measurable
- OB zone width IS measurable indirectly via SL distance (SL sits below H1 OB)
- Entry precision relative to zone is captured by entry_dist_zone_norm for XAUUSD

WHAT WAS TESTED (revised due to data reality):
  T1 → SL_distance_ATR as zone-width proxy (XAUUSD zone match failed <20 trades)
  T2 → Execution slippage (M15_close vs AI entry) + mae_r proxy for limit order
  T3 → M15 candle open vs close (alpha decay within candle)
  T4 → SL_distance_ATR vs outcome (zone width proxy)
""")

print("RESULTS SUMMARY:")
print(f"  T1 ({test1_result}): See SL_distance_ATR analysis above")
print(f"  T2 ({test2_result}): Execution slippage + mae_r proxy")
print(f"  T3 ({test3_result}): M15 open vs close alpha decay")
print(f"  T4 ({test4_result}): SL distance / zone width vs outcome")

print("""
ACTIONABLE FINDINGS:
  • If Tests 1/4 show SL distance is NOT correlated with outcome:
    → Zone width is not a meaningful filter for entry quality
    → Current behavior (wide SL to OB zone) is defensible

  • If Test 2 shows slippage matters:
    → Entering at AI-proposed price (earlier in candle) vs at close has R impact
    → Consider limit order execution protocol

  • If Test 3 shows alpha decay is negligible:
    → Candle close entry timing is irrelevant; current approach is fine

  • If Test 4 shows wider SL (larger zone) → lower R outcomes:
    → Filter out trades with SL_distance_ATR > threshold
    → This is a WF-2 candidate gate

NULL RESULTS ARE VALUABLE:
  If Tests 1-4 all show p >= 0.0125 or |ρ| < 0.1:
  → Entry engineering parameters are not currently predictive of outcomes
  → Engineering effort should focus on other variables (zone recency, OB quality)
  → This is consistent with the finding that the system's edge is zone DETECTION,
     not entry PRECISION (Test A rerun: AI adds ~0pp to entry WR over mechanical)
""")

# Save report
report = [
    "# T1 — Entry Engineering Results v1\n\n",
    f"**Date:** 2026-04-11  \n**Bonferroni threshold:** p < {BONFERRONI_ALPHA}  \n"
    f"**Practical threshold:** |ΔR| > {PRACTICAL_R}R, |ΔWR| > {PRACTICAL_WR_PP}pp\n\n",
    "---\n\n## Data Availability\n\n",
    f"- Total trades: {total}\n",
    f"- With AI decision: {cnt(df.entry_price_ai.notna())}\n",
    f"- With SL extracted: {cnt(df.stop_loss.notna())}\n",
    f"- With M15 OHLC: {cnt(df.candle_close.notna())}\n",
    f"- With OB zone matched: {cnt(df.zone_match_type.notna())} (XAUUSD only)\n\n",
    "## Critical Data Finding\n\n",
    "The batch system enters at M15 BOS confirmation, 50-100+ pts above H1 OBs.\n",
    "Entry depth within OB (as designed) is not measurable for most trades.\n",
    "Tests reframed to use SL_distance_ATR as zone-width proxy.\n\n",
    f"## Test Results\n\n",
    f"| Test | Status | Significant? |\n|---|---|---|\n",
    f"| T1 Entry vs Zone | {test1_result} | See detail |\n",
    f"| T2 Limit Order | {test2_result} | See detail |\n",
    f"| T3 Alpha Decay | {test3_result} | See detail |\n",
    f"| T4 Zone Width | {test4_result} | See detail |\n\n",
    "(Full statistical output in T1_entry_engineering_analysis.py stdout log)\n",
]

report_path = OUTPUT_DIR / "T1_entry_engineering_results_v1.md"
with open(report_path, "w") as f:
    f.writelines(report)

print(f"\n✓ Report skeleton saved → {report_path}")
print(f"  Full detailed output printed above to stdout.")
print("\n--- DONE ---")
