"""Q-2.7 / B8 — Premium/Discount Zone Evidence

Pre-registered analysis:
    For each OB-retest trade, identify the most recent H1 impulse swing
    with BOS before entry. Classify entry location into:
        discount (0-38.2% of impulse range)
        equilibrium (38.2-61.8%)
        premium (61.8-100%)

    For LONG retest trades, "correct-side" = discount.
    For SHORT retest trades, "correct-side" = premium.

    Primary test: 2-prop z-test correct-WR vs wrong-WR, pooled.
    Per-symbol test with Bonferroni alpha/5 = 0.01.
    Effect size threshold: >=5pp WR difference to call actionable.
    Sample threshold: n>=30 per zone stratum.

Data source: research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv
    (726 retests, 5 symbols, 2026-01-01 to 2026-04-17).
    All retests are OHLC-derived (deterministic), mirrors production methodology.
    CONTINUED = win, REVERSED = loss, UNRESOLVED excluded.

Swing definition for impulse:
    Match market_state.calculate_premium_discount and A2_v2 methodology:
    - Use 3-bar strict pivot swings on H1.
    - For a LONG retest (bullish OB): impulse_low = most recent swing low
        with idx <= bos_idx, impulse_high = highest H1 high between that
        swing low and the BOS candle inclusive (the impulse extreme).
    - Mirror for SHORT.
    Fib zones computed from that impulse:
        long:  discount = [impulse_low, impulse_low + 0.382 * range]
               equilibrium = (0.382, 0.618)
               premium = [0.618 to impulse_high]
        short: discount = [impulse_high - 0.382 * range, impulse_high]
               equilibrium = (0.382, 0.618)
               premium = [impulse_low, impulse_high - 0.618 * range]
    Zone assignment by retest_entry_price clip to [impulse_low, impulse_high].

Pre-registration committed 2026-04-18 before examining zone-outcome numbers.

Author: Claude Code research agent (Q-2.7)
"""

from __future__ import annotations

import csv
import math
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
RETEST_CSV = ROOT / "research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv"
HIST_DIR = ROOT / "data/historical"
OUT_DIR = ROOT / "research/q27_premium_discount"
OUT_CSV = OUT_DIR / "q27_zone_classifications.csv"
OUT_REPORT = OUT_DIR / "q27_report_2026-04-18.md"

SYMBOLS = ["XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"]
# Swing window for BOS-anchoring pivot detection. Match A2_v2 (window=1, 3-bar pivot)
# because that is the cadence that generated the retest dataset. The impulse for a
# LONG retest = (most recent swing LOW prior to BOS, BOS candle HIGH). Mirror for SHORT.
SWING_WINDOW = 1

# Fib thresholds (pre-registered)
DISCOUNT_TOP = 0.382
EQUILIBRIUM_TOP = 0.618


# ---------------------------------------------------------------------------
# H1 loading
# ---------------------------------------------------------------------------

def load_h1(symbol: str) -> pd.DataFrame:
    """Load H1 OHLC data. Returns DataFrame with DatetimeIndex (UTC)."""
    path = HIST_DIR / f"{symbol}_H1.csv"
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").reset_index(drop=True)
    df = df.set_index("time")
    return df


# ---------------------------------------------------------------------------
# Pivot / swing detection (3-bar strict) — matches A2_v2 and market_state
# ---------------------------------------------------------------------------

def detect_pivots(h1: pd.DataFrame, window: int = SWING_WINDOW) -> list[tuple[int, float, str]]:
    """Return list of (idx, price, 'high'|'low') for 3-bar strict pivots.
    A pivot high at i requires high[i] > high[i-1] AND high[i] > high[i+1]. Mirror for low.
    """
    highs = h1["high"].to_numpy()
    lows = h1["low"].to_numpy()
    pivots: list[tuple[int, float, str]] = []
    for i in range(window, len(h1) - window):
        is_high = True
        for k in range(1, window + 1):
            if not (highs[i] > highs[i - k] and highs[i] > highs[i + k]):
                is_high = False
                break
        if is_high:
            pivots.append((i, float(highs[i]), "high"))
            continue
        is_low = True
        for k in range(1, window + 1):
            if not (lows[i] < lows[i - k] and lows[i] < lows[i + k]):
                is_low = False
                break
        if is_low:
            pivots.append((i, float(lows[i]), "low"))
    return pivots


# ---------------------------------------------------------------------------
# Impulse computation
# ---------------------------------------------------------------------------

def compute_impulse_for_retest(
    h1: pd.DataFrame,
    pivots: list[tuple[int, float, str]],
    bos_idx: int,
    side: str,
) -> tuple[float, float] | None:
    """Return (impulse_low, impulse_high) — the BOS-forming impulse leg.

    For a bullish BOS (LONG retest):
        impulse_low  = price of most recent confirmed swing LOW with p.idx < bos_idx.
        impulse_high = H1 HIGH of the BOS candle at bos_idx, clipped to the max
                       H1 high from impulse_low.idx through bos_idx inclusive
                       (the actual extreme reached during the impulse leg).
    Mirror for SHORT.

    "Confirmed" requires p.idx + SWING_WINDOW <= bos_idx (forward bars observed).
    Returns None if no prior pivot of the required side exists, or range <= 0.

    This is the SMC-standard definition: the impulse leg is the directional move
    that caused the BOS, bracketed by the pullback pivot that preceded it and the
    extreme reached at the break.
    """
    confirmed = [
        p for p in pivots if p[0] + SWING_WINDOW <= bos_idx and p[0] < bos_idx
    ]
    if not confirmed:
        return None

    if side == "long":
        # Most recent pivot LOW before BOS
        prior_lows = [p for p in confirmed if p[2] == "low"]
        if not prior_lows:
            return None
        swing_idx, swing_price, _ = prior_lows[-1]
        # Impulse extreme: highest h1 high from swing_idx through bos_idx inclusive
        highs_slice = h1["high"].iloc[swing_idx : bos_idx + 1]
        impulse_high = float(highs_slice.max())
        impulse_low = float(swing_price)
    elif side == "short":
        prior_highs = [p for p in confirmed if p[2] == "high"]
        if not prior_highs:
            return None
        swing_idx, swing_price, _ = prior_highs[-1]
        lows_slice = h1["low"].iloc[swing_idx : bos_idx + 1]
        impulse_low = float(lows_slice.min())
        impulse_high = float(swing_price)
    else:
        return None

    if impulse_high <= impulse_low:
        return None
    return (impulse_low, impulse_high)


def classify_zone(
    entry_price: float,
    impulse_low: float,
    impulse_high: float,
    side: str,
) -> tuple[str, float] | None:
    """Return (zone_name, fib_pct) where zone is 'discount' | 'equilibrium' | 'premium'.

    fib_pct is the normalised retracement position (0.0 = trend origin, 1.0 = impulse extreme),
    measured from the 0% side. For LONG, 0% = impulse_low, 100% = impulse_high.
    For SHORT, 0% = impulse_high, 100% = impulse_low.

    Returns None if impulse_high <= impulse_low (degenerate).
    """
    if impulse_high <= impulse_low:
        return None
    rng = impulse_high - impulse_low
    if side == "long":
        # Discount = low half of impulse (entry near impulse_low = "discount" buy)
        pct = (entry_price - impulse_low) / rng
    else:  # short
        # Discount/premium inverted: entry near impulse_high = "premium" sell
        # To unify: "fib_pct" measures retrace depth from trend origin
        # For short: 0% = impulse_high (the trend origin), 1.0 = impulse_low (deep into the move)
        # Discount side for SHORT = entry deep into impulse (close to impulse_low)
        # Premium side for SHORT = entry shallow (close to impulse_high).
        pct = (impulse_high - entry_price) / rng

    # Clip clip reporting — flag out-of-range but still compute zone from raw pct
    raw_pct = pct
    if pct < DISCOUNT_TOP:
        zone = "discount"
    elif pct < EQUILIBRIUM_TOP:
        zone = "equilibrium"
    else:
        zone = "premium"
    return (zone, raw_pct)


def correct_side_for_direction(side: str) -> str:
    """Per pre-registration: LONG => correct = discount, SHORT => correct = premium.

    NOTE: In this analysis, zone is defined in "retracement depth from impulse origin"
    terms. For a LONG bullish-OB retest, we want a *shallow pullback*, i.e. entry near
    the top of the impulse (premium in retrace terms) ... wait, see below.

    REVISITED: The standard SMC premium/discount framing for a bullish impulse:
        discount zone = below 50% of the impulse (close to the impulse_low)
        premium zone = above 50% of the impulse (close to the impulse_high)
    For LONG setups (buying), "discount" is considered the good zone to buy.
    For SHORT setups (selling), "premium" is considered the good zone to sell.

    Our computation: for LONG, fib_pct = (entry - impulse_low) / range.
        pct < 0.382 => entry near the impulse_low => "discount" => correct for LONG.
        pct > 0.618 => entry near the impulse_high => "premium" => wrong for LONG.
    For SHORT, fib_pct = (impulse_high - entry) / range.
        pct < 0.382 => entry near the impulse_high => "discount" in our naming.
        BUT in SMC framing, entry near impulse_high for a SHORT = "premium" sell (correct).
    This creates an ambiguity in labelling. To avoid confusion:
        use "discount" to mean "good side for LONG, bad for SHORT (= near impulse_low)".
        use "premium" to mean "good side for SHORT, bad for LONG (= near impulse_high)".

    Redefine: zone label is fixed in PRICE terms, not direction terms.
        zone_pricewise = 'discount' if entry is in lower half of impulse
                        'premium' if entry is in upper half of impulse
    That matches SMC convention. Let's use THAT definition and rewrite classify_zone.
    """
    return "discount" if side == "long" else "premium"


# We re-do classify_zone properly below to use PRICE-based zone naming.

def classify_zone_price_based(
    entry_price: float,
    impulse_low: float,
    impulse_high: float,
) -> tuple[str, float] | None:
    """Zone label is fixed to price location in the impulse, NOT trade direction.

    pct = (entry - impulse_low) / (impulse_high - impulse_low).
    Values outside [0,1] are clipped for zone-labelling purposes; the raw pct
    is returned verbatim for diagnostics.

        pct <= 0.382  => 'discount' (lower third)
        0.382 < pct < 0.618 => 'equilibrium'
        pct >= 0.618 => 'premium' (upper third)

    Interpretation:
        LONG retest IN discount = correct-side (deep pullback buy, price near low).
        LONG retest IN premium  = wrong-side (shallow pullback buy, price near high).
        SHORT retest IN premium = correct-side (deep rally sell, price near high).
        SHORT retest IN discount = wrong-side (shallow pullback sell, price near low).
    """
    if impulse_high <= impulse_low:
        return None
    rng = impulse_high - impulse_low
    pct = (entry_price - impulse_low) / rng
    # Clip for zone labelling; raw pct remains
    pct_clipped = max(0.0, min(1.0, pct))
    if pct_clipped <= DISCOUNT_TOP:
        zone = "discount"
    elif pct_clipped < EQUILIBRIUM_TOP:
        zone = "equilibrium"
    else:
        zone = "premium"
    return (zone, pct)


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------

def two_proportion_z(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float, float]:
    """Two-proportion z-test (two-sided). Returns (z, p_two_sided, diff_pp).
    diff_pp = (x1/n1 - x2/n2) * 100. Returns (0, 1, 0) if degenerate.
    """
    if n1 == 0 or n2 == 0:
        return (0.0, 1.0, 0.0)
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    denom = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if denom == 0:
        return (0.0, 1.0, (p1 - p2) * 100)
    z = (p1 - p2) / denom
    # Abramowitz-Stegun erf-based two-sided p-value
    p = 2 * (1 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2))))
    return (z, p, (p1 - p2) * 100)


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"Loading retests: {RETEST_CSV}")
    retests = pd.read_csv(RETEST_CSV)
    print(f"  {len(retests)} retests")

    # Map symbol -> H1 df (pre-compute pivots per symbol once)
    h1_cache: dict[str, pd.DataFrame] = {}
    pivot_cache: dict[str, list[tuple[int, float, str]]] = {}
    for sym in SYMBOLS:
        print(f"Loading H1 {sym}...")
        h1 = load_h1(sym)
        h1_cache[sym] = h1
        pivot_cache[sym] = detect_pivots(h1, window=SWING_WINDOW)
        print(f"  H1 rows: {len(h1)}, pivots: {len(pivot_cache[sym])}")

    rows_out = []
    exclude_reasons: dict[str, int] = {}

    for _, r in retests.iterrows():
        sym = r["symbol"]
        side = r["side"]
        if sym not in h1_cache:
            exclude_reasons["symbol_missing"] = exclude_reasons.get("symbol_missing", 0) + 1
            continue

        h1 = h1_cache[sym]
        pivots = pivot_cache[sym]
        bos_ts_str = r["bos_confirm_ts"]
        bos_ts_open = pd.to_datetime(bos_ts_str, utc=True) - pd.Timedelta(hours=1)
        # bos_confirm_ts in a2_v2 = OPEN + 1h (close time). Bos_idx is the open_time candle.
        try:
            bos_idx = h1.index.get_loc(bos_ts_open)
            if isinstance(bos_idx, slice):  # duplicate timestamp
                bos_idx = bos_idx.start
        except KeyError:
            exclude_reasons["bos_ts_not_found"] = exclude_reasons.get("bos_ts_not_found", 0) + 1
            continue

        entry_price = float(r["retest_entry_price"])
        imp = compute_impulse_for_retest(h1, pivots, bos_idx, side)
        if imp is None:
            exclude_reasons["no_prior_swing"] = exclude_reasons.get("no_prior_swing", 0) + 1
            continue
        impulse_low, impulse_high = imp
        cls = classify_zone_price_based(entry_price, impulse_low, impulse_high)
        if cls is None:
            exclude_reasons["degenerate_impulse"] = exclude_reasons.get("degenerate_impulse", 0) + 1
            continue
        zone, fib_pct = cls

        # Determine correct-side
        correct_zone = correct_side_for_direction(side)
        is_correct_side = (zone == correct_zone)

        outcome = r["outcome_a"]
        if outcome == "UNRESOLVED":
            exclude_reasons["unresolved"] = exclude_reasons.get("unresolved", 0) + 1
            continue
        win = 1 if outcome == "CONTINUED" else 0  # CONTINUED=win, REVERSED=loss

        rows_out.append({
            "symbol": sym,
            "retest_date": r["retest_date"],
            "retest_ts": r["retest_ts"],
            "side": side,
            "entry_price": entry_price,
            "impulse_low": impulse_low,
            "impulse_high": impulse_high,
            "fib_pct": round(fib_pct, 4),
            "zone": zone,
            "correct_zone": correct_zone,
            "is_correct_side": int(is_correct_side),
            "outcome_a": outcome,
            "win": win,
            "continuation_r_a": r["continuation_r_a"],
        })

    print(f"\nProcessed: {len(rows_out)} retests included")
    print(f"Exclude reasons: {exclude_reasons}")

    # Write CSV
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows_out)
    df.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV}")

    # ================================================================
    # Analysis
    # ================================================================

    # Per-symbol per-zone WR
    print("\n=== Zone distribution by symbol ===")
    dist = df.groupby(["symbol", "zone"]).size().unstack(fill_value=0)
    print(dist)

    print("\n=== WR by symbol x zone ===")
    wr_table = (
        df.groupby(["symbol", "zone"])
        .agg(n=("win", "size"), wins=("win", "sum"))
        .reset_index()
    )
    wr_table["wr_pct"] = (wr_table["wins"] / wr_table["n"] * 100).round(2)
    print(wr_table.to_string(index=False))

    # Per-symbol correct vs wrong
    print("\n=== Per-symbol correct-side vs wrong-side ===")
    per_sym_rows = []
    for sym in SYMBOLS:
        sub = df[df["symbol"] == sym]
        correct = sub[sub["is_correct_side"] == 1]
        wrong = sub[sub["is_correct_side"] == 0]
        # "Wrong" excludes equilibrium (it's neither correct nor wrong in binary framing)
        # Actually, per pre-reg: correct = discount for long / premium for short.
        # "Wrong" = premium for long / discount for short. Equilibrium = neutral (not wrong).
        wrong_strict = sub[
            ((sub["side"] == "long") & (sub["zone"] == "premium"))
            | ((sub["side"] == "short") & (sub["zone"] == "discount"))
        ]
        correct_wins = correct["win"].sum()
        correct_n = len(correct)
        wrong_wins = wrong_strict["win"].sum()
        wrong_n = len(wrong_strict)
        eq = sub[sub["zone"] == "equilibrium"]

        correct_wr = (correct_wins / correct_n * 100) if correct_n else float("nan")
        wrong_wr = (wrong_wins / wrong_n * 100) if wrong_n else float("nan")
        gap = (correct_wr - wrong_wr) if (correct_n and wrong_n) else float("nan")

        z, p, _ = two_proportion_z(int(correct_wins), int(correct_n), int(wrong_wins), int(wrong_n))

        underpowered = (correct_n < 30) or (wrong_n < 30)

        per_sym_rows.append({
            "symbol": sym,
            "correct_n": correct_n,
            "correct_wins": int(correct_wins),
            "correct_wr_pct": round(correct_wr, 2) if not math.isnan(correct_wr) else None,
            "wrong_n": wrong_n,
            "wrong_wins": int(wrong_wins),
            "wrong_wr_pct": round(wrong_wr, 2) if not math.isnan(wrong_wr) else None,
            "eq_n": len(eq),
            "eq_wr_pct": round(eq["win"].mean() * 100, 2) if len(eq) else None,
            "gap_pp": round(gap, 2) if not math.isnan(gap) else None,
            "z": round(z, 3),
            "p_value": round(p, 4),
            "underpowered": underpowered,
        })

    per_sym_df = pd.DataFrame(per_sym_rows)
    print(per_sym_df.to_string(index=False))

    # Pooled
    print("\n=== POOLED correct-side vs wrong-side ===")
    correct_all = df[df["is_correct_side"] == 1]
    wrong_all = df[
        ((df["side"] == "long") & (df["zone"] == "premium"))
        | ((df["side"] == "short") & (df["zone"] == "discount"))
    ]
    eq_all = df[df["zone"] == "equilibrium"]
    pooled_correct_n = len(correct_all)
    pooled_correct_wins = int(correct_all["win"].sum())
    pooled_wrong_n = len(wrong_all)
    pooled_wrong_wins = int(wrong_all["win"].sum())
    correct_wr = pooled_correct_wins / pooled_correct_n * 100 if pooled_correct_n else float("nan")
    wrong_wr = pooled_wrong_wins / pooled_wrong_n * 100 if pooled_wrong_n else float("nan")
    gap = correct_wr - wrong_wr

    z_p, p_p, _ = two_proportion_z(pooled_correct_wins, pooled_correct_n, pooled_wrong_wins, pooled_wrong_n)
    print(f"  CORRECT-SIDE: {pooled_correct_wins}/{pooled_correct_n} = {correct_wr:.2f}%")
    print(f"  WRONG-SIDE:   {pooled_wrong_wins}/{pooled_wrong_n} = {wrong_wr:.2f}%")
    print(f"  EQUILIBRIUM:  {eq_all['win'].sum()}/{len(eq_all)} = {eq_all['win'].mean()*100 if len(eq_all) else float('nan'):.2f}%")
    print(f"  Gap: {gap:+.2f} pp")
    print(f"  z = {z_p:.3f}  p (2-sided) = {p_p:.4f}")

    # Also compute direction-stratified (long-only, short-only)
    print("\n=== Pooled by direction ===")
    for d in ["long", "short"]:
        sub = df[df["side"] == d]
        correct = sub[sub["is_correct_side"] == 1]
        wrong = sub[
            ((sub["side"] == "long") & (sub["zone"] == "premium"))
            | ((sub["side"] == "short") & (sub["zone"] == "discount"))
        ]
        c_wr = correct["win"].mean() * 100 if len(correct) else float("nan")
        w_wr = wrong["win"].mean() * 100 if len(wrong) else float("nan")
        print(f"  {d}: correct n={len(correct)} wr={c_wr:.2f}%  wrong n={len(wrong)} wr={w_wr:.2f}%  gap={c_wr - w_wr:+.2f}pp")

    # Save summary
    summary = {
        "pooled": {
            "correct_n": pooled_correct_n,
            "correct_wins": pooled_correct_wins,
            "correct_wr_pct": round(correct_wr, 2),
            "wrong_n": pooled_wrong_n,
            "wrong_wins": pooled_wrong_wins,
            "wrong_wr_pct": round(wrong_wr, 2),
            "gap_pp": round(gap, 2),
            "z": round(z_p, 3),
            "p_value": round(p_p, 4),
            "eq_n": len(eq_all),
            "eq_wins": int(eq_all["win"].sum()),
            "eq_wr_pct": round(eq_all["win"].mean() * 100, 2) if len(eq_all) else None,
        },
        "per_symbol": per_sym_rows,
        "exclude_reasons": exclude_reasons,
        "total_included": len(df),
    }
    import json
    with (OUT_DIR / "q27_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote {OUT_DIR / 'q27_summary.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
