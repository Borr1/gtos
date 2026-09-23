"""Generate `feature_catalogs/structure.csv` from the running set of
columns produced by `structure.build_structure_features` joined with
`structure_stability.csv`.

Usage:
    python research/ml_program/scripts/features/_build_structure_catalog.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "research" / "ml_program" / "scripts" / "features"))

from structure import (  # noqa: E402
    LOOKBACKS_BY_TF,
    build_structure_features,
    _df_to_candles,
    _make_synthetic_candles,
)


CATALOG_DIR = PROJECT_ROOT / "research" / "ml_program" / "feature_catalogs"
OUT_CSV = CATALOG_DIR / "structure.csv"
STAB_CSV = CATALOG_DIR / "structure_stability.csv"


# Map (primitive prefix) -> (computation summary, expensive flag, lookback applies?)
PRIMITIVE_DOC = {
    # OB family
    "ob_count": ("Count of order blocks formed in last <lookback> bars per TF.",
                 False, True),
    "ob_bull_count": ("Count of bullish OBs (impulse-up origin) in window.",
                      False, True),
    "ob_bear_count": ("Count of bearish OBs (impulse-down origin) in window.",
                      False, True),
    "ob_unmitigated_count": ("OBs in window where no past candle has "
                             "closed beyond the zone (Component-2 mitigated=False).",
                             False, True),
    "ob_mitigated_count": ("OBs in window where a past candle body has "
                           "closed beyond the zone (mitigated=True).",
                           False, True),
    "ob_breaker_count_in_window": ("Breaker blocks formed in window — "
                                   "i.e. OBs that have flipped post-mitigation.",
                                   False, True),
    "ob_mean_depth_atr": ("Mean (ob.high-ob.low)/ATR across active OBs.",
                          False, True),
    "ob_mean_age_bars": ("Mean (last_idx - ob.formation_index) across "
                        "active OBs.", False, True),
    "ob_max_touch_count": ("Max retest count among active OBs (counts "
                           "candles overlapping each OB after formation).",
                           False, True),
    "nearest_ob_dist_atr": ("|close - ob.midpoint| / ATR for the OB whose "
                            "midpoint is closest to the latest close.",
                            False, True),
    "nearest_ob_signed_atr": ("(close - ob.midpoint) / ATR; positive = "
                              "price above OB mid.", False, True),
    "nearest_ob_depth_atr": ("(ob.high - ob.low) / ATR for nearest OB.",
                             False, True),
    "nearest_ob_age_bars": ("(last_idx - ob.formation_index) for nearest "
                            "OB.", False, True),
    "nearest_ob_touch_count": ("Retest count of nearest OB up to current "
                               "candle.", False, True),
    "nearest_ob_is_bullish": ("1 if nearest OB is bullish (impulse-up "
                              "origin), else 0.", False, True),
    # FVG family
    "fvg_count": ("Count of FVGs formed in window.", False, True),
    "fvg_bull_count": ("Bullish FVG count in window.", False, True),
    "fvg_bear_count": ("Bearish FVG count in window.", False, True),
    "fvg_filled_count": ("FVGs in window where any later candle has "
                         "fully closed the gap.", False, True),
    "fvg_unfilled_count": ("FVGs in window not yet filled.", False, True),
    "fvg_mean_size_atr": ("Mean (top-bottom)/ATR across active FVGs.",
                          False, True),
    "nearest_fvg_dist_atr": ("|close - fvg.midpoint| / ATR for FVG closest "
                             "to current price.", False, True),
    "nearest_fvg_size_atr": ("(top - bottom)/ATR for nearest FVG.",
                             False, True),
    "nearest_fvg_age_bars": ("(last_idx - mid_candle_idx) for nearest FVG.",
                             False, True),
    "nearest_fvg_fill_ratio": ("Fraction of nearest FVG range filled by "
                               "subsequent candles (0=untouched, 1=closed).",
                               False, True),
    "nearest_fvg_retest_count": ("Number of post-formation candles whose "
                                 "range overlaps the nearest FVG zone.",
                                 False, True),
    "nearest_fvg_is_bullish": ("1 if nearest FVG bullish, else 0.",
                               False, True),
    "nearest_fvg_is_filled": ("1 if Component-2 marked the nearest FVG "
                              "filled.", False, True),
    # BB family
    "bb_count": ("Active breaker blocks (post-mitigation flipped OBs) "
                 "in window.", False, True),
    "bb_bull_count": ("Bullish breakers (originated as bearish OBs) "
                      "in window.", False, True),
    "bb_bear_count": ("Bearish breakers (originated as bullish OBs) "
                      "in window.", False, True),
    "bb_retested_count": ("Breakers in window where price has returned "
                          "to retest the zone from the new side.",
                          False, True),
    "nearest_bb_dist_atr": ("|close - bb.midpoint|/ATR for nearest BB.",
                            False, True),
    "nearest_bb_signed_atr": ("(close - bb.midpoint)/ATR for nearest BB.",
                              False, True),
    "nearest_bb_depth_atr": ("(zone_high - zone_low)/ATR for nearest BB.",
                             False, True),
    "nearest_bb_age_bars": ("(last_idx - formation_idx) for nearest BB.",
                            False, True),
    "nearest_bb_is_retested": ("1 if nearest BB has been retested, else 0.",
                               False, True),
    "nearest_bb_orig_was_bullish": ("1 if nearest BB's pre-flip OB was "
                                    "bullish.", False, True),
    "nearest_bb_is_bullish": ("1 if nearest BB is now bullish "
                              "(was-bearish-OB).", False, True),
    # Event family
    "bos_count": ("BOS events in last <lookback> bars per TF.",
                   False, True),
    "choch_count": ("CHoCH events in last <lookback> bars per TF.",
                    False, True),
    "bos_bull_count": ("Bullish-direction BOS events in window.",
                       False, True),
    "bos_bear_count": ("Bearish-direction BOS events in window.",
                       False, True),
    "displacement_present_count": ("Events with displacement_present=True "
                                   "(body/avg_body >= 1.5) in window.",
                                   False, True),
    "mean_displacement_ratio": ("Mean event.displacement_ratio "
                                "(body/avg_body) across active events.",
                                False, True),
    "last_bos_age_bars": ("(last_idx - last_bos_event.candle_index).",
                          False, True),
    "last_choch_age_bars": ("(last_idx - last_choch_event.candle_index).",
                            False, True),
    "last_event_was_bos": ("1 if most recent structure event in window "
                           "was BOS, else 0 (CHoCH).", False, True),
    "last_event_displaced": ("displacement_present flag of most recent "
                             "event.", False, True),
    # Swing family
    "swing_high_count": ("Number of swing highs in window per TF.",
                         False, True),
    "swing_low_count": ("Number of swing lows in window per TF.",
                        False, True),
    "swing_total_count": ("Total swings (highs + lows) in window.",
                          False, True),
    "swing_high_ratio": ("swing_high_count / swing_total_count "
                        "(0..1).", False, True),
    "last_swing_range_atr": ("|last_swing_high.price - last_swing_low.price|"
                             " / ATR.", False, True),
    "last_swing_leg_bars": ("|last_swing_high.index - last_swing_low.index|.",
                             False, True),
    "last_swing_velocity_atr_per_bar": ("(last_swing_range / leg_bars) / ATR.",
                                        False, True),
    "max_up_leg_atr": ("Max consecutive low->low ascent across active "
                       "swings, ATR-units.", False, True),
    "max_down_leg_atr": ("Max consecutive high->high descent, ATR-units.",
                         False, True),
    "last_high_age_bars": ("(last_idx - last_swing_high.index).",
                           False, True),
    "last_low_age_bars": ("(last_idx - last_swing_low.index).",
                          False, True),
    "swing_dispersion_atr": ("(max(swing_prices) - min(swing_prices))"
                             " / ATR.", False, True),
    # Distance-to-swing (TF-level, no lookback)
    "dist_to_nearest_swing_high_atr": ("min(|close - swing_high.price|) "
                                       "across all swings, ATR-units.",
                                       False, False),
    "dist_to_nearest_swing_low_atr": ("min(|close - swing_low.price|) "
                                      "ATR-units.", False, False),
    "dist_to_swing_band_atr": ("|nearest_high - nearest_low|/ATR — "
                               "tightest enclosing swing band.",
                               False, False),
    # Impulse leg (M15+H1 only)
    "impulse_range_atr": ("(leg_high - leg_low)/ATR over candles "
                          "[ob.formation_index .. bos.candle_index].",
                          False, False),
    "impulse_bar_count": ("len(leg) for the leg above.", False, False),
    "impulse_to_ob_depth_ratio": ("impulse_range / ob_depth.",
                                  False, False),
    "impulse_bull_candle_ratio": ("Fraction of leg candles with "
                                  "close>open.", False, False),
    "impulse_max_displacement_ratio": ("max(|c.close-c.open| / avg_body) "
                                       "across the leg.", False, False),
    "impulse_pre_consolidation_bars": ("Walk back from ob.formation_index; "
                                       "count consecutive bars with "
                                       "(high-low)/ATR < 0.7. Cap=50.",
                                       False, False),
    # MTF alignment (top-level)
    "dir_M15": ("identify_structure(M15).direction encoded as "
                "+1/0/-1 (bullish/transitional|insufficient/bearish).",
                False, False),
    "dir_H1": ("Same encoding for H1.", False, False),
    "dir_H4": ("Same encoding for H4.", False, False),
    "dir_D1": ("Same encoding for D1.", False, False),
    "agree_M15_H1": ("1.0 if dir_M15 == dir_H1 and both non-zero, "
                     "else 0.0.", False, False),
    "agree_M15_H4": ("Same for M15/H4.", False, False),
    "agree_M15_D1": ("Same for M15/D1.", False, False),
    "agree_H1_H4": ("Same for H1/H4.", False, False),
    "agree_H1_D1": ("Same for H1/D1.", False, False),
    "agree_H4_D1": ("Same for H4/D1.", False, False),
    "mtf_agreement_count": ("Sum of the 6 pairwise agreement flags. "
                            "Range [0, 6].", False, False),
    "mtf_signed_score": ("dir_M15 + dir_H1 + dir_H4 + dir_D1. Range "
                         "[-4, +4].", False, False),
    "mtf_all_aligned_bull": ("1 if all 4 TF directions == +1.",
                             False, False),
    "mtf_all_aligned_bear": ("1 if all 4 TF directions == -1.",
                             False, False),
}


# Family classification by primitive name prefix
def _family_of(primitive: str) -> str:
    if primitive.startswith("ob_") or primitive.startswith("nearest_ob_"):
        return "structure_ob"
    if primitive.startswith("fvg_") or primitive.startswith("nearest_fvg_"):
        return "structure_fvg"
    if primitive.startswith("bb_") or primitive.startswith("nearest_bb_"):
        return "structure_bb"
    if primitive.startswith("bos_") or primitive.startswith("choch_") \
            or primitive.endswith("_displacement_count") \
            or primitive.startswith("displacement_present") \
            or primitive.startswith("mean_displacement") \
            or primitive.startswith("last_bos_") \
            or primitive.startswith("last_choch_") \
            or primitive.startswith("last_event_"):
        return "structure_event"
    if primitive.startswith("swing_") or primitive.startswith("last_swing_") \
            or primitive.startswith("max_up_") or primitive.startswith("max_down_") \
            or primitive.startswith("last_high_") or primitive.startswith("last_low_"):
        return "structure_swing"
    if primitive.startswith("dist_to_"):
        return "structure_distance_to_swing"
    if primitive.startswith("impulse_"):
        return "structure_impulse"
    if primitive.startswith("dir_") or primitive.startswith("agree_") \
            or primitive.startswith("mtf_"):
        return "structure_mtf_alignment"
    return "structure_other"


def _parse_feature_name(name: str) -> tuple[str, str, str]:
    """Parse 'TF__primitive__lbN' or 'TF__primitive' or 'primitive'.
    Returns (tf, primitive, lookback_str).
    """
    parts = name.split("__")
    if len(parts) == 1:
        return ("", parts[0], "")
    if len(parts) == 2:
        return (parts[0], parts[1], "")
    if len(parts) == 3 and parts[2].startswith("lb"):
        return (parts[0], parts[1], parts[2][2:])
    return (parts[0], "__".join(parts[1:]), "")


def _doc_for(primitive: str, tf: str, lb: str) -> tuple[str, bool]:
    """Look up doc and expensive flag. Falls back to primitive name."""
    if primitive in PRIMITIVE_DOC:
        text, expensive, _has_lb = PRIMITIVE_DOC[primitive]
    else:
        text = primitive
        expensive = False
    return text, expensive


def main() -> None:
    # Drive feature names from the live module by featurizing one
    # synthetic candle — guarantees this catalog stays in lock-step
    # with the implementation.
    candles = _make_synthetic_candles(80)
    df = build_structure_features(
        [candles[-1]["time"]],
        {"M15": candles, "H1": candles, "H4": candles, "D1": candles},
    )
    feature_names = list(df.columns)

    # Stability
    if STAB_CSV.exists():
        stab = pd.read_csv(STAB_CSV).set_index("feature")
    else:
        stab = pd.DataFrame()

    rows = []
    for fn in feature_names:
        tf, primitive, lb = _parse_feature_name(fn)
        family = _family_of(primitive)
        text, expensive = _doc_for(primitive, tf, lb)
        if lb:
            source = f"OHLCV {tf} candles, last {lb} bars"
            lookback = lb
        elif tf:
            source = f"OHLCV {tf} candles"
            lookback = "TF-level"
        else:
            source = "OHLCV M15+H1+H4+D1 (multi-TF)"
            lookback = "TF-level"

        comp = text
        rho = stab.loc[fn]["rho"] if fn in stab.index else float("nan")
        n = stab.loc[fn]["n"] if fn in stab.index else float("nan")
        p = stab.loc[fn]["p"] if fn in stab.index else float("nan")

        rows.append({
            "family": family,
            "feature_name": fn,
            "source": source,
            "lookback": lookback,
            "computation_summary": comp,
            "stability_rho": rho if pd.notna(rho) else "",
            "stability_n": int(n) if pd.notna(n) else "",
            "stability_p": p if pd.notna(p) else "",
            "expensive_flag": "true" if expensive else "false",
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_CSV}: {len(out)} rows")
    print("\nFamily counts:")
    print(out["family"].value_counts())


if __name__ == "__main__":
    main()
