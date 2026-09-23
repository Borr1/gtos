"""Path 2 — AI-chosen-SL buffer reconstruction analysis for GTOS gate decision.

Reconstructs buffer = |SL - OB_edge| and buffer_atr = buffer / M15_ATR for all
historical trades where the AI chose the SL placement, then analyzes outcomes
per buffer band and per gate configuration.

Data sources:
  Batch (AI chose SL in backtest replay):
    - knowledge_base_backtest/analysis/unified_trades_v2_20260331.json  (111 records, 85 XAUUSD joined + 25 XAUUSD inferred)
    - knowledge_base_backtest/analysis/deep_dive_20260406/trade_index_enriched.json  (129 records with symbols, 85 overlap)

  Live (AI chose SL in production from Apr 7, 2026+):
    - knowledge_base/trade_records/*/*.json (92 records, 20 LIMIT_PLACED with full MSO including OB info)
    - knowledge_base/monitoring/edge_monitor_state.json (42 closed live trades, trade_history binary, but no per-trade R)

  Historical OHLC for reconstruction:
    - data/historical/{SYMBOL}_M15.csv
    - data/historical/{SYMBOL}_H1.csv

Methodology:
  OB reconstruction: replay Component 2 on H1 candles up to the entry_time to
  get unmitigated bullish (for LONG) / bearish (for SHORT) OBs. Match by
  proximity: the OB whose zone contains the entry_price (or is nearest).

  M15 ATR: Wilder 14-period ATR on M15 up to the entry_time (matches
  calculate_atr in market_state.py:269-286).

  OB edges: raw candle high/low of origination candle (market_state.py:422-459).

Gate definitions (all bypass sl_too_tight = SL_distance >= 1.5 * M15_ATR):
  Current-live:  framework==ob_retest AND sl_beyond_edge AND buffer >= 0.3*ATR
  Option C/A:    framework==ob_retest AND sl_beyond_edge AND buffer <= 0.5*ATR
  Option D:      framework==ob_retest AND sl_beyond_edge AND buffer <= 0.3*ATR
  Option E:      framework==ob_retest AND sl_beyond_edge AND 0.3*ATR<=buffer<=0.5*ATR
  Baseline:      no bypass (sl_too_tight rejects everything with SL<1.5*ATR)
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

# Make src/ importable for direct reuse of market_state logic
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.components.market_state import (
    detect_swings,
    identify_structure,
    detect_structure_breaks,
    identify_order_blocks,
    calculate_atr,
)

OUT_DIR = ROOT / "research" / "sl_gate_buffer_analysis_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = ["XAUUSD", "GBPUSD", "USDJPY", "GBPJPY", "US30_cash"]

# Cache for loaded CSVs
_ohlc_cache: dict[tuple[str, str], pd.DataFrame] = {}


def load_ohlc(symbol: str, tf: str) -> pd.DataFrame:
    key = (symbol, tf)
    if key not in _ohlc_cache:
        fp = ROOT / "data" / "historical" / f"{symbol}_{tf}.csv"
        df = pd.read_csv(fp)
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time").reset_index(drop=True)
        _ohlc_cache[key] = df
    return _ohlc_cache[key]


def df_to_candles(df: pd.DataFrame) -> list[dict]:
    """Convert OHLC dataframe to market_state candle dicts (time as ISO string)."""
    return [
        {
            "time": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "open": float(o),
            "high": float(h),
            "low": float(l),
            "close": float(c),
        }
        for t, o, h, l, c in zip(
            df["time"], df["open"], df["high"], df["low"], df["close"]
        )
    ]


def find_ob_for_trade(symbol: str, entry_time: pd.Timestamp, direction: str,
                     entry_price: float, lookback_h1: int = 200) -> dict | None:
    """Replay Component 2 on H1 up to entry_time, return best-matching unmitigated OB.

    Returns {'ob_high', 'ob_low', 'ob_edge', 'formation_time', 'type', 'mitigated'} or None.
    """
    df_h1 = load_ohlc(symbol, "H1")
    # Include candle at or before entry time
    df_h1 = df_h1[df_h1["time"] < entry_time].tail(lookback_h1)
    if len(df_h1) < 30:
        return None

    candles = df_to_candles(df_h1)
    swings = detect_swings(candles, min_bars=2)
    structure = identify_structure(swings)
    events = detect_structure_breaks(candles, swings, structure)
    obs = identify_order_blocks(candles, events)

    expected_type = "bullish" if direction == "LONG" else "bearish"
    candidates = [ob for ob in obs if ob.type == expected_type and not ob.mitigated]
    if not candidates:
        # Fall back to mitigated (AI may have traded before mitigation on simulator)
        candidates = [ob for ob in obs if ob.type == expected_type]
    if not candidates:
        return None

    # Match: OB whose zone contains entry_price, else nearest
    tol = 0.02 if symbol in ("GBPUSD", "USDJPY") else (
        1.0 if symbol in ("XAUUSD",) else (0.5 if symbol == "GBPJPY" else 20.0)
    )
    in_zone = [ob for ob in candidates
               if ob.low - tol <= entry_price <= ob.high + tol]
    if in_zone:
        # Most recent OB in zone
        best = max(in_zone, key=lambda o: o.formation_index)
    else:
        # Nearest by zone midpoint
        def dist(ob):
            mid = 0.5 * (ob.high + ob.low)
            return abs(mid - entry_price)
        best = min(candidates, key=dist)

    ob_edge = best.low if direction == "LONG" else best.high
    return {
        "ob_high": best.high,
        "ob_low": best.low,
        "ob_edge": ob_edge,
        "formation_time": best.formation_time,
        "type": best.type,
        "mitigated": best.mitigated,
    }


def compute_m15_atr(symbol: str, entry_time: pd.Timestamp, period: int = 14) -> float:
    """14-period Wilder ATR on M15 up to (but not including) entry_time."""
    df = load_ohlc(symbol, "M15")
    df = df[df["time"] < entry_time].tail(period * 10)  # more than enough
    if len(df) < period + 1:
        return 0.0
    candles = df_to_candles(df)
    return calculate_atr(candles, period=period)


@dataclass
class BatchRecord:
    source: str  # 'batch' or 'live'
    trade_id: str
    symbol: str
    date: str
    direction: str
    entry_price: float
    stop_loss: float
    framework: str
    outcome: str  # 'WIN' / 'LOSS' / 'BREAKEVEN'
    r_multiple: float
    # Reconstructed fields
    ob_high: float | None = None
    ob_low: float | None = None
    ob_edge: float | None = None
    m15_atr: float | None = None
    buffer: float | None = None
    buffer_atr: float | None = None
    sl_distance: float | None = None
    sl_distance_atr: float | None = None
    sl_beyond_edge: bool | None = None
    reconstruction_status: str = "pending"


def parse_entry_time_batch(date_str: str, kill_zone: str, trade_id: str | None = None) -> pd.Timestamp:
    """Batch trade_id: 'bt_YYYY-MM-DD_london_001[_symbol]'. Use kill_zone start as entry proxy.

    London KZ typically 07:00 UTC, NY 13:00 UTC.
    """
    base = pd.Timestamp(date_str)
    if kill_zone == "london":
        return base + pd.Timedelta(hours=7, minutes=15)
    elif kill_zone == "ny":
        return base + pd.Timedelta(hours=13, minutes=15)
    elif kill_zone == "tokyo":
        return base + pd.Timedelta(hours=0, minutes=30)
    else:
        return base + pd.Timedelta(hours=12)


def load_batch_trades() -> list[BatchRecord]:
    """Load unified_trades_v2 + join with enriched index for symbols."""
    v2 = json.load(open(ROOT / "knowledge_base_backtest/analysis/unified_trades_v2_20260331.json",
                        encoding="utf-8"))
    enr = json.load(open(ROOT / "knowledge_base_backtest/analysis/deep_dive_20260406/trade_index_enriched.json",
                         encoding="utf-8"))["trades"]

    def strip_suffix(tid):
        for sfx in ["_xauusd", "_gbpusd", "_us30_cash", "_us30", "_usdjpy", "_gbpjpy"]:
            if tid.endswith(sfx):
                return tid[:-len(sfx)]
        return tid

    enr_by_id = {strip_suffix(t["trade_id"]): t for t in enr}

    def infer_symbol_by_price(ep: float) -> str | None:
        if ep is None:
            return None
        if 1000 <= ep <= 10000:
            return "XAUUSD"
        if 1.0 <= ep <= 1.8:
            return "GBPUSD"
        if 100 <= ep <= 200:
            return "USDJPY"
        if 20000 <= ep <= 50000:
            return "US30_cash"
        return None

    records: list[BatchRecord] = []
    symbol_source = Counter()
    for t in v2:
        tid = t["trade_id"]
        ep = t.get("entry_price")
        inferred = infer_symbol_by_price(ep) if ep is not None else None

        matched = enr_by_id.get(tid)
        if matched and matched.get("symbol"):
            # Sanity: override if enriched symbol disagrees with price-scale
            joined_sym = matched["symbol"]
            if inferred is not None and joined_sym != inferred:
                # ID collision (same date+kz, different underlying). Prefer price-scale.
                symbol = inferred
                symbol_source["joined_overridden"] += 1
            else:
                symbol = joined_sym
                symbol_source["joined"] += 1
        elif inferred is not None:
            symbol = inferred
            symbol_source["inferred"] += 1
        else:
            continue

        records.append(BatchRecord(
            source="batch",
            trade_id=tid,
            symbol=symbol,
            date=t["date"],
            direction=t.get("direction") or "",
            entry_price=t["entry_price"],
            stop_loss=t["stop_loss"],
            framework=t.get("framework", ""),
            outcome=t["outcome"],
            r_multiple=t["r_multiple"],
        ))
    print(f"Batch load: {len(records)} trades; symbol sources = {dict(symbol_source)}")
    return records


def load_live_trades() -> list[BatchRecord]:
    """Load LIMIT_PLACED live records from knowledge_base/trade_records/.

    Live records don't have exit outcomes yet, but they have full MSO with OB info.
    We extract OB edges directly from the stored MSO for methodology fidelity
    (this matches what the live gate actually sees), and cross-validate against
    historical-CSV reconstruction in reconstruct_all.
    """
    records: list[BatchRecord] = []
    for f in sorted((ROOT / "knowledge_base/trade_records").rglob("*.json")):
        try:
            t = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"Skip {f}: {e}")
            continue
        dp = t.get("decision_pipeline", {})
        if dp.get("final_outcome") != "LIMIT_PLACED":
            continue
        tp = t.get("trade_parameters") or {}
        md = t.get("metadata") or {}
        if not tp.get("entry_price") or not tp.get("stop_loss"):
            continue

        # Extract OB + ATR from stored MSO (preferred for live records)
        mso = t.get("mso", {}) or {}
        tfs = mso.get("timeframes") or {}
        h1 = tfs.get("H1") or {}
        m15 = tfs.get("M15") or {}
        stored_obs = h1.get("order_blocks") or []
        stored_m15_atr = m15.get("atr_14")

        direction = tp.get("direction") or dp.get("ai_direction") or ""
        entry = float(tp["entry_price"])
        expected_type = "bullish" if direction == "LONG" else "bearish"

        # Pick OB whose zone matches AI's entry (match by range-containment)
        chosen_ob = None
        candidates = [ob for ob in stored_obs if ob.get("type") == expected_type]
        # Prefer unmitigated in zone
        tol = 0.02 if tp.get("entry_price", 0) < 10 else (
            1.0 if md.get("symbol") == "XAUUSD" else (
                0.5 if md.get("symbol") == "GBPJPY" else 20.0)
        )
        in_zone = [ob for ob in candidates
                   if not ob.get("mitigated")
                   and ob.get("low", 0) - tol <= entry <= ob.get("high", 0) + tol]
        if not in_zone:
            in_zone = [ob for ob in candidates
                       if ob.get("low", 0) - tol <= entry <= ob.get("high", 0) + tol]
        if in_zone:
            # Most recent formation
            chosen_ob = max(in_zone, key=lambda o: o.get("formation_time", ""))
        elif candidates:
            # Nearest by midpoint
            def mid_dist(ob):
                return abs(0.5 * (ob["high"] + ob["low"]) - entry)
            chosen_ob = min(candidates, key=mid_dist)

        rec = BatchRecord(
            source="live",
            trade_id=md.get("trade_id", f.stem),
            symbol=md.get("symbol") or "",
            date=md.get("date") or "",
            direction=direction,
            entry_price=entry,
            stop_loss=float(tp["stop_loss"]),
            framework=dp.get("ai_framework") or "",
            outcome="UNKNOWN",
            r_multiple=float("nan"),
        )
        # Attach stored MSO fields (will be used by reconstruct_all if present)
        if chosen_ob:
            rec.ob_high = chosen_ob["high"]
            rec.ob_low = chosen_ob["low"]
            rec.ob_edge = chosen_ob["low"] if direction == "LONG" else chosen_ob["high"]
        if stored_m15_atr:
            rec.m15_atr = float(stored_m15_atr)
        records.append(rec)
    print(f"Live load: {len(records)} LIMIT_PLACED trades (with stored MSO)")
    return records


def reconstruct_all(records: list[BatchRecord]) -> list[BatchRecord]:
    """Reconstruct OB edges + M15 ATR for each record.

    Live records: prefer stored MSO from trade_record JSON (set by load_live_trades).
    Fall back to CSV-based Component 2 replay if stored fields missing.

    Batch records: always use CSV-based replay (no stored MSO).

    Cross-validation: for live records, if stored MSO is present, we still run
    CSV replay and compare edges to detect drift.
    """
    ok = 0
    failed = Counter()
    cross_mismatches = []
    for r in records:
        if not r.direction or r.direction not in ("LONG", "SHORT"):
            r.reconstruction_status = "missing_direction"
            failed["missing_direction"] += 1
            continue
        if r.symbol not in SYMBOLS:
            r.reconstruction_status = f"unknown_symbol:{r.symbol}"
            failed[f"unknown_symbol"] += 1
            continue

        # Parse entry_time
        if r.source == "live":
            parts = r.trade_id.split("_")
            try:
                date_idx = None
                for i, p in enumerate(parts):
                    if len(p) == 10 and p[4] == "-" and p[7] == "-":
                        date_idx = i
                        break
                if date_idx is None:
                    raise ValueError("no date in trade_id")
                date_str = parts[date_idx]
                kz = parts[date_idx + 1]
                time_str = parts[date_idx + 2] if date_idx + 2 < len(parts) else "0715"
                hh, mm = int(time_str[:2]), int(time_str[2:4])
                entry_time = pd.Timestamp(f"{date_str} {hh:02d}:{mm:02d}:00")
            except Exception as e:
                r.reconstruction_status = f"bad_live_id:{e}"
                failed["bad_live_id"] += 1
                continue
        else:
            kz = "london" if "_london_" in r.trade_id else ("ny" if "_ny_" in r.trade_id else "tokyo")
            entry_time = parse_entry_time_batch(r.date, kz, r.trade_id)

        stored_ob_edge = r.ob_edge
        stored_atr = r.m15_atr
        have_stored_ob = stored_ob_edge is not None
        have_stored_atr = stored_atr is not None and stored_atr > 0

        # CSV-based replay
        ob_csv = find_ob_for_trade(r.symbol, entry_time, r.direction, r.entry_price)
        atr_csv = compute_m15_atr(r.symbol, entry_time)

        # Choose source: stored (live) > CSV (batch fallback)
        if have_stored_ob:
            # Keep stored edges; cross-validate against CSV
            if ob_csv:
                delta_edge = abs(stored_ob_edge - ob_csv["ob_edge"])
                rel = delta_edge / max(abs(stored_ob_edge), 1e-9)
                if rel > 0.005:  # >0.5% drift
                    cross_mismatches.append(
                        (r.trade_id, stored_ob_edge, ob_csv["ob_edge"], rel)
                    )
        else:
            # Use CSV OB
            if ob_csv is None:
                r.reconstruction_status = "no_ob_found"
                failed["no_ob_found"] += 1
                continue
            r.ob_high = ob_csv["ob_high"]
            r.ob_low = ob_csv["ob_low"]
            r.ob_edge = ob_csv["ob_edge"]

        if have_stored_atr:
            pass  # keep stored
        else:
            if atr_csv <= 0:
                r.reconstruction_status = "no_atr"
                failed["no_atr"] += 1
                continue
            r.m15_atr = atr_csv

        r.buffer = abs(r.stop_loss - r.ob_edge)
        r.buffer_atr = r.buffer / r.m15_atr if r.m15_atr > 0 else float("nan")
        r.sl_distance = abs(r.entry_price - r.stop_loss)
        r.sl_distance_atr = r.sl_distance / r.m15_atr
        if r.direction == "LONG":
            r.sl_beyond_edge = r.stop_loss <= r.ob_edge
        else:
            r.sl_beyond_edge = r.stop_loss >= r.ob_edge
        r.reconstruction_status = "ok"
        ok += 1

    print(f"Reconstruction: {ok} ok, failures = {dict(failed)}")
    if cross_mismatches:
        print(f"Cross-validation mismatches (stored vs CSV OB edge): {len(cross_mismatches)}")
        for m in cross_mismatches[:10]:
            print(f"  {m[0]}: stored={m[1]:.5f}, csv={m[2]:.5f}, rel={m[3]:.3%}")
    return records


def filter_degenerate(records: list[BatchRecord]) -> tuple[list[BatchRecord], list[BatchRecord]]:
    """Remove rows where SL is on wrong side of entry (LONG: SL >= entry; SHORT: SL <= entry)
    or |r_multiple| > 5 (outliers), or reconstruction failed."""
    kept = []
    dropped = []
    for r in records:
        if r.reconstruction_status != "ok":
            dropped.append(r)
            continue
        # Direction/SL sanity
        if r.direction == "LONG" and r.stop_loss >= r.entry_price:
            dropped.append(r)
            r.reconstruction_status = "degenerate_sl_above_entry"
            continue
        if r.direction == "SHORT" and r.stop_loss <= r.entry_price:
            dropped.append(r)
            r.reconstruction_status = "degenerate_sl_below_entry"
            continue
        # Outlier R (only check for batch where we have R)
        if r.source == "batch" and r.r_multiple is not None:
            if abs(r.r_multiple) > 5.0:
                dropped.append(r)
                r.reconstruction_status = f"r_outlier:{r.r_multiple}"
                continue
        kept.append(r)
    print(f"After degenerate filter: {len(kept)} kept, {len(dropped)} dropped")
    return kept, dropped


def to_dataframe(records: list[BatchRecord]) -> pd.DataFrame:
    return pd.DataFrame([r.__dict__ for r in records])


def gate_admission(df: pd.DataFrame, config: str) -> pd.Series:
    """Return boolean mask: which trades would the gate ADMIT (bypass sl_too_tight)?

    Semantics: the structural exception bypasses sl_too_tight. A trade is 'admitted'
    by the gate if:
      (a) sl_distance >= 1.5 * M15_ATR (passes floor outright), OR
      (b) framework==ob_retest AND sl_beyond_edge AND buffer condition per config

    For this analysis we focus on trades that WOULD BE BLOCKED by sl_too_tight
    (sl_distance < 1.5*ATR) and analyze which ones each gate would RESCUE.
    """
    # Who needs rescue? (sl_too_tight would block)
    needs_rescue = df["sl_distance_atr"] < 1.5
    passes_floor = ~needs_rescue  # auto-admitted

    is_ob = df["framework"] == "ob_retest"
    safe = df["sl_beyond_edge"] == True

    if config == "Current-live":  # buffer >= 0.3 ATR, no upper
        structural_ok = df["buffer_atr"] >= 0.3
    elif config == "OptionC":  # buffer <= 0.5 ATR, no lower
        structural_ok = df["buffer_atr"] <= 0.5
    elif config == "OptionD":  # buffer <= 0.3 ATR
        structural_ok = df["buffer_atr"] <= 0.3
    elif config == "OptionE":  # 0.3 <= buffer <= 0.5
        structural_ok = (df["buffer_atr"] >= 0.3) & (df["buffer_atr"] <= 0.5)
    elif config == "Baseline":
        structural_ok = pd.Series([False] * len(df), index=df.index)
    else:
        raise ValueError(config)

    rescued = needs_rescue & is_ob & safe & structural_ok
    return passes_floor | rescued


def analyze_gate(df: pd.DataFrame, config: str) -> dict:
    """Analyze admitted trades for a given gate config."""
    # Admission we care about for outcome analysis: only trades with outcomes
    df_out = df[df["outcome"].isin(["WIN", "LOSS", "BREAKEVEN"])].copy()
    admitted = gate_admission(df_out, config)
    adm = df_out[admitted]
    if len(adm) == 0:
        return {"config": config, "n": 0, "wr": None, "expectancy": None,
                "sweep_events": 0, "total_r": 0.0}
    wins = (adm["outcome"] == "WIN").sum()
    losses = (adm["outcome"] == "LOSS").sum()
    wr = wins / (wins + losses) if (wins + losses) > 0 else None
    exp = adm["r_multiple"].mean()
    sweep_events = ((adm["buffer_atr"] < 0.3) & (adm["outcome"] == "LOSS")).sum()
    return {
        "config": config,
        "n": len(adm),
        "wins": wins,
        "losses": losses,
        "wr": wr,
        "expectancy": exp,
        "total_r": adm["r_multiple"].sum(),
        "sweep_events": sweep_events,
    }


def buffer_histogram(df: pd.DataFrame, bins: list[float]) -> pd.DataFrame:
    """Build buffer distribution table."""
    df = df.copy()
    # Bin edges
    labels = [f"[{bins[i]:.1f},{bins[i+1]:.1f})" for i in range(len(bins) - 1)]
    labels.append(f">={bins[-1]:.1f}")

    def bin_idx(x):
        for i in range(len(bins) - 1):
            if bins[i] <= x < bins[i + 1]:
                return labels[i]
        if x >= bins[-1]:
            return labels[-1]
        return "negative"

    df["band"] = df["buffer_atr"].apply(bin_idx)
    has_r = df["r_multiple"].notna()
    g = df[has_r].groupby("band", dropna=False).agg(
        n=("r_multiple", "size"),
        wins=("outcome", lambda x: (x == "WIN").sum()),
        losses=("outcome", lambda x: (x == "LOSS").sum()),
        mean_r=("r_multiple", "mean"),
        median_r=("r_multiple", "median"),
    )
    # Force numeric dtypes for arithmetic
    for c in ("n", "wins", "losses"):
        g[c] = pd.to_numeric(g[c], errors="coerce").fillna(0).astype(int)
    denom = (g["wins"] + g["losses"]).replace(0, np.nan)
    g["wr"] = g["wins"] / denom
    # Ensure all labels represented
    g = g.reindex(labels).fillna({"n": 0, "wins": 0, "losses": 0})
    return g


def sensitivity_scan(df: pd.DataFrame) -> pd.DataFrame:
    """Vary floor {0.2, 0.3, 0.4} and ceiling {0.4, 0.5, 0.6}."""
    rows = []
    df_out = df[df["outcome"].isin(["WIN", "LOSS", "BREAKEVEN"])].copy()
    for floor in [0.2, 0.3, 0.4]:
        for ceil in [0.4, 0.5, 0.6]:
            if floor >= ceil:
                continue
            needs_rescue = df_out["sl_distance_atr"] < 1.5
            passes_floor = ~needs_rescue
            is_ob = df_out["framework"] == "ob_retest"
            safe = df_out["sl_beyond_edge"] == True
            cond = (df_out["buffer_atr"] >= floor) & (df_out["buffer_atr"] <= ceil)
            admitted = passes_floor | (needs_rescue & is_ob & safe & cond)
            adm = df_out[admitted]
            wins = (adm["outcome"] == "WIN").sum()
            losses = (adm["outcome"] == "LOSS").sum()
            wr = wins / (wins + losses) if (wins + losses) > 0 else None
            rows.append({
                "floor_atr": floor,
                "ceiling_atr": ceil,
                "n": len(adm),
                "wr": wr,
                "expectancy": adm["r_multiple"].mean() if len(adm) else None,
            })
    return pd.DataFrame(rows)


def main():
    batch = load_batch_trades()
    live = load_live_trades()
    all_records = batch + live
    all_records = reconstruct_all(all_records)
    kept, dropped = filter_degenerate(all_records)

    df_all = to_dataframe(all_records)
    df = to_dataframe(kept)

    # Save per-trade reconstructed data
    df_all.to_csv(OUT_DIR / "reconstructed_trades.csv", index=False)
    df.to_csv(OUT_DIR / "reconstructed_trades_clean.csv", index=False)

    # Inventory
    print("\n--- Inventory ---")
    print(f"Total records loaded:     {len(all_records)}")
    print(f"  Batch:                  {sum(1 for r in all_records if r.source == 'batch')}")
    print(f"  Live:                   {sum(1 for r in all_records if r.source == 'live')}")
    print(f"After reconstruction:     {len(kept)}")
    print(f"Dropped (degenerate/fail):{len(dropped)}")
    print(f"  Reason breakdown:")
    reasons = Counter(r.reconstruction_status for r in dropped)
    for k, v in reasons.most_common():
        print(f"    {k}: {v}")

    print("\n--- Symbol distribution (kept) ---")
    print(df.groupby("symbol").size())

    print("\n--- Buffer distribution ---")
    # Fine-grained bins for the structural band [0.0, 1.0] and coarser beyond
    bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
    # All pooled
    hist_all = buffer_histogram(df, bins)
    print("All instruments:")
    print(hist_all)
    hist_all.to_csv(OUT_DIR / "buffer_hist_all.csv")

    # Per-symbol
    per_sym = {}
    for sym, grp in df.groupby("symbol"):
        h = buffer_histogram(grp, bins)
        per_sym[sym] = h
        h.to_csv(OUT_DIR / f"buffer_hist_{sym}.csv")

    # Batch vs live
    df_batch = df[df["source"] == "batch"]
    df_live = df[df["source"] == "live"]
    hist_batch = buffer_histogram(df_batch, bins)
    hist_live = buffer_histogram(df_live, bins)
    hist_batch.to_csv(OUT_DIR / "buffer_hist_batch.csv")
    hist_live.to_csv(OUT_DIR / "buffer_hist_live.csv")

    # Summary stats on buffer_atr (AI's choice distribution)
    print("\n--- buffer_atr summary (AI choice distribution) ---")
    print(f"Mean:     {df['buffer_atr'].mean():.3f}")
    print(f"Median:   {df['buffer_atr'].median():.3f}")
    print(f"P25/P75:  {df['buffer_atr'].quantile(0.25):.3f} / {df['buffer_atr'].quantile(0.75):.3f}")
    print(f"Min/Max:  {df['buffer_atr'].min():.3f} / {df['buffer_atr'].max():.3f}")
    print(f"<0.3 count: {(df['buffer_atr'] < 0.3).sum()}")
    print(f"0.3-0.5 count: {((df['buffer_atr'] >= 0.3) & (df['buffer_atr'] <= 0.5)).sum()}")
    print(f">0.5 count: {(df['buffer_atr'] > 0.5).sum()}")

    # Gate analysis (batch only for outcomes)
    print("\n--- Gate configuration results ---")
    gate_configs = ["Baseline", "Current-live", "OptionC", "OptionD", "OptionE"]
    gate_rows = []
    for cfg in gate_configs:
        r = analyze_gate(df, cfg)
        gate_rows.append(r)
        print(r)
    gate_df = pd.DataFrame(gate_rows)
    gate_df.to_csv(OUT_DIR / "gate_results.csv", index=False)

    # Sensitivity
    print("\n--- Sensitivity scan ---")
    sens = sensitivity_scan(df)
    print(sens)
    sens.to_csv(OUT_DIR / "sensitivity.csv", index=False)

    # Tight-buffer cohort
    print("\n--- Tight-buffer cohort (buffer_atr < 0.3) ---")
    tight = df[(df["buffer_atr"] < 0.3) & df["outcome"].isin(["WIN", "LOSS", "BREAKEVEN"])]
    print(f"n = {len(tight)}")
    if len(tight) > 0:
        print(f"WR: {(tight['outcome']=='WIN').sum()} / "
              f"{((tight['outcome']=='WIN') | (tight['outcome']=='LOSS')).sum()} = "
              f"{(tight['outcome']=='WIN').sum()/max(1,((tight['outcome']=='WIN')|(tight['outcome']=='LOSS')).sum()):.3f}")
        print(f"Expectancy: {tight['r_multiple'].mean():.3f}")
        print(f"Per-symbol:")
        print(tight.groupby("symbol").agg(
            n=("r_multiple", "size"),
            wr=("outcome", lambda x: (x == "WIN").sum() / max(1, ((x == "WIN") | (x == "LOSS")).sum())),
            exp=("r_multiple", "mean"),
        ))
    tight.to_csv(OUT_DIR / "tight_buffer_cohort.csv", index=False)

    # Wide-buffer cohort (0.5 < buffer_atr)
    print("\n--- Wide-buffer cohort (buffer_atr > 0.5) ---")
    wide = df[(df["buffer_atr"] > 0.5) & df["outcome"].isin(["WIN", "LOSS", "BREAKEVEN"])]
    print(f"n = {len(wide)}")
    if len(wide) > 0:
        print(f"WR: {(wide['outcome']=='WIN').sum()/max(1,((wide['outcome']=='WIN')|(wide['outcome']=='LOSS')).sum()):.3f}")
        print(f"Expectancy: {wide['r_multiple'].mean():.3f}")
        print(wide.groupby("symbol").agg(
            n=("r_multiple", "size"),
            wr=("outcome", lambda x: (x == "WIN").sum() / max(1, ((x == "WIN") | (x == "LOSS")).sum())),
            exp=("r_multiple", "mean"),
        ))
    wide.to_csv(OUT_DIR / "wide_buffer_cohort.csv", index=False)

    # Medium cohort (Option E target: 0.3 <= buffer_atr <= 0.5)
    print("\n--- Medium cohort (0.3 <= buffer_atr <= 0.5) ---")
    mid = df[(df["buffer_atr"] >= 0.3) & (df["buffer_atr"] <= 0.5) & df["outcome"].isin(["WIN", "LOSS", "BREAKEVEN"])]
    print(f"n = {len(mid)}, wr = {(mid['outcome']=='WIN').sum()/max(1,((mid['outcome']=='WIN')|(mid['outcome']=='LOSS')).sum()):.3f}")
    print(f"Expectancy: {mid['r_multiple'].mean():.3f}")

    # MAE distribution for tight cohort (if we have MAE)
    print("\n--- MAE info (batch only) ---")
    # Load v2 to get mae_r
    v2 = json.load(open(ROOT / "knowledge_base_backtest/analysis/unified_trades_v2_20260331.json", encoding="utf-8"))
    mae_by_id = {t["trade_id"]: t.get("mae_r") for t in v2}
    df_batch_out = df[df["source"] == "batch"].copy()
    df_batch_out["mae_r"] = df_batch_out["trade_id"].map(mae_by_id)
    tight_b = df_batch_out[df_batch_out["buffer_atr"] < 0.3]
    wide_b = df_batch_out[df_batch_out["buffer_atr"] > 0.5]
    print(f"Tight (<0.3) n={len(tight_b)} mean_mae={tight_b['mae_r'].mean():.3f}")
    print(f"Wide (>0.5) n={len(wide_b)} mean_mae={wide_b['mae_r'].mean():.3f}")

    # Save full data
    df.to_csv(OUT_DIR / "final_clean.csv", index=False)

    # ------------------------------------------------------------------
    # Additional analysis: buffer_atr correlation with outcome
    # ------------------------------------------------------------------
    print("\n--- Correlation: buffer_atr vs r_multiple (batch only) ---")
    batch_clean = df[(df["source"] == "batch") & df["outcome"].isin(["WIN", "LOSS", "BREAKEVEN"])]
    if len(batch_clean) > 10:
        corr = batch_clean[["buffer_atr", "r_multiple", "sl_distance_atr"]].corr()
        print(corr)
        # Spearman too
        spearman = batch_clean[["buffer_atr", "r_multiple"]].corr(method="spearman")
        print(f"Spearman(buffer_atr, r_multiple) = {spearman.iloc[0, 1]:.3f}")

    # ------------------------------------------------------------------
    # Live-AI buffer choice analysis (no outcomes yet — just distribution)
    # NOTE: dedup multi-KZ-repeated pending limits by (symbol, entry, SL, ob_edge)
    # ------------------------------------------------------------------
    print("\n--- Live AI buffer choice ---")
    live_df_raw = df[df["source"] == "live"].copy()
    live_df = live_df_raw.drop_duplicates(
        subset=["symbol", "entry_price", "stop_loss", "ob_edge"]
    ).reset_index(drop=True)
    live_df.to_csv(OUT_DIR / "live_deduped.csv", index=False)
    print(f"Total live LIMIT_PLACED rows: {len(live_df_raw)}")
    print(f"Unique pending intents (dedup):{len(live_df)}")
    print(f"  buffer_atr mean: {live_df['buffer_atr'].mean():.3f}")
    print(f"  buffer_atr median: {live_df['buffer_atr'].median():.3f}")
    print(f"  <0.3 ATR (Apr-16-type):  {(live_df['buffer_atr'] < 0.3).sum()} ({(live_df['buffer_atr']<0.3).mean():.1%})")
    print(f"  0.3-0.5 ATR (Option E):  {((live_df['buffer_atr']>=0.3)&(live_df['buffer_atr']<=0.5)).sum()}")
    print(f"  >0.5 ATR (discretionary):{(live_df['buffer_atr']>0.5).sum()}")
    print(f"  sl_distance_atr <1.5 (needs rescue): {(live_df['sl_distance_atr']<1.5).sum()}")

    # Per-symbol live buffer stats
    print("\nLive per-symbol buffer_atr:")
    for sym, grp in live_df.groupby("symbol"):
        print(f"  {sym}: n={len(grp)}, "
              f"mean={grp['buffer_atr'].mean():.3f}, "
              f"median={grp['buffer_atr'].median():.3f}, "
              f"<0.3={(grp['buffer_atr']<0.3).sum()}, "
              f"beyond_edge={grp['sl_beyond_edge'].sum()}")

    # Live gate admission count (all 5 configs)
    print("\nLive gate admission (of 20 LIMIT_PLACED):")
    for cfg in ["Baseline", "Current-live", "OptionC", "OptionD", "OptionE"]:
        admitted = gate_admission(live_df, cfg)
        print(f"  {cfg}: {admitted.sum()} / {len(live_df)}")

    # ------------------------------------------------------------------
    # Export summary stats for report
    # ------------------------------------------------------------------
    summary = {
        "total_records": len(all_records),
        "batch_count": sum(1 for r in all_records if r.source == "batch"),
        "live_count": sum(1 for r in all_records if r.source == "live"),
        "clean_count": len(kept),
        "batch_clean": int((df["source"] == "batch").sum()),
        "live_clean": int((df["source"] == "live").sum()),
        "buffer_atr_mean_all": float(df["buffer_atr"].mean()),
        "buffer_atr_median_all": float(df["buffer_atr"].median()),
        "buffer_atr_mean_batch": float(batch_clean["buffer_atr"].mean()),
        "buffer_atr_median_batch": float(batch_clean["buffer_atr"].median()),
        "buffer_atr_mean_live": float(live_df["buffer_atr"].mean()),
        "buffer_atr_median_live": float(live_df["buffer_atr"].median()),
        "tight_cohort_n": int((df["buffer_atr"] < 0.3).sum()),
        "medium_cohort_n": int(((df["buffer_atr"] >= 0.3) & (df["buffer_atr"] <= 0.5)).sum()),
        "wide_cohort_n": int((df["buffer_atr"] > 0.5).sum()),
        "batch_all_needs_rescue": int(((df["source"] == "batch") & (df["sl_distance_atr"] < 1.5)).sum()),
        "live_needs_rescue": int(((df["source"] == "live") & (df["sl_distance_atr"] < 1.5)).sum()),
    }
    import json as _j
    (OUT_DIR / "summary_stats.json").write_text(_j.dumps(summary, indent=2))
    print(f"\nAll output saved to {OUT_DIR}")
    print(f"Summary: {_j.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
