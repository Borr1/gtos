"""Generate regime feature catalog (CSV + Markdown).

One-shot. Emits:
  - research/ml_program/feature_catalogs/regime.csv
  - research/ml_program/feature_catalogs/regime.md

Stability scores are read from research/ml_program/data/regime_stability_scores.json
(precomputed by build_regime_dataset.py).
"""
import json
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:/Users/MSI/Documents/ai-trading-agent")
sys.path.insert(0, str(ROOT / "research/ml_program/scripts/features"))

from regime import compute_regime_features, RegimeFeatureContext  # noqa: E402

ctx = RegimeFeatureContext()
ts = datetime(2026, 4, 20, 14, 0, tzinfo=timezone.utc)
sample = compute_regime_features("XAUUSD", ts, "LONG", ctx=ctx)
feat_keys = list(sample.keys())
print(f"Canonical feature count: {len(feat_keys)}")

# Load stability
with (ROOT / "research/ml_program/data/regime_stability_scores.json").open() as f:
    stab_doc = json.load(f)
stab = stab_doc["stability_score"]

META = {
    "regime_v1_is_bullish":       ("current_regime_v1", "backfill.v1_direction", "single", "binary", "v1 H4 detector label one-hot. K54 v1 audit: zero importance globally."),
    "regime_v1_is_bearish":       ("current_regime_v1", "backfill.v1_direction", "single", "binary", "v1 H4 detector label one-hot."),
    "regime_v1_is_transitional":  ("current_regime_v1", "backfill.v1_direction", "single", "binary", "v1 H4 detector label one-hot."),
    "regime_v1_is_untagged":      ("current_regime_v1", "backfill.v1_direction", "single", "binary", "v1 H4 detector label one-hot. UNTAGGED = label missing or sentinel."),
    "regime_v2_is_bullish":       ("current_regime_v2", "backfill.v2_direction", "single", "binary", "v2 H4 detector label one-hot (production label since session 38)."),
    "regime_v2_is_bearish":       ("current_regime_v2", "backfill.v2_direction", "single", "binary", "v2 H4 detector label one-hot."),
    "regime_v2_is_transitional":  ("current_regime_v2", "backfill.v2_direction", "single", "binary", "v2 H4 detector label one-hot."),
    "regime_v2_is_untagged":      ("current_regime_v2", "backfill.v2_direction", "single", "binary", "v2 H4 detector label one-hot."),
    "regime_v2_in_dead_zone":     ("current_regime_v2", "backfill.v2_score, v2_dead_zone", "single", "binary", "abs(v2_score) <= v2_dead_zone. Audit Section 5: v2_dead_zone UNUSED in K54 v1 -> zero-cost win."),
    "regime_v2_score":            ("regime_strength", "backfill.v2_score", "single", "int", "Raw v2 score = (HH+HL) - (LH+LL). Positive = bullish lean. Audit Section 5: UNUSED in K54 v1."),
    "regime_v2_score_abs":        ("regime_strength", "backfill.v2_score", "single", "int", "abs(v2_score). Strength of directional vote regardless of side."),
    "regime_v2_dead_zone_value":  ("regime_strength", "backfill.v2_dead_zone", "single", "int", "Dead-zone divisor (max(2, transitions//8)). Audit Section 5 quick-win."),
    "regime_v2_score_minus_dead_zone": ("regime_strength", "backfill.v2_score, v2_dead_zone", "single", "int", "abs(score) - dead_zone. >=0 means cleared the noise floor."),
    "regime_v2_score_normalized": ("regime_strength", "backfill.v2_score, v2_dead_zone", "single", "float", "score / dead_zone. Period-transferable strength signal."),
    "regime_v2_dz_is_2":           ("regime_strength", "backfill.v2_dead_zone", "single", "binary", "dead_zone == 2 (most common base case)."),
    "regime_v2_dz_is_3":           ("regime_strength", "backfill.v2_dead_zone", "single", "binary", "dead_zone == 3."),
    "regime_v2_dz_is_4_or_more":   ("regime_strength", "backfill.v2_dead_zone", "single", "binary", "dead_zone >= 4 (very-many-swing histories)."),
    "regime_hh_count":             ("regime_microstructure", "backfill.counts.hh", "single", "int", "H4 higher-high count over the v2 swing window."),
    "regime_hl_count":             ("regime_microstructure", "backfill.counts.hl", "single", "int", "H4 higher-low count."),
    "regime_lh_count":             ("regime_microstructure", "backfill.counts.lh", "single", "int", "H4 lower-high count."),
    "regime_ll_count":             ("regime_microstructure", "backfill.counts.ll", "single", "int", "H4 lower-low count."),
    "regime_consecutive_h4_bars":  ("regime_stability", "backfill v2_direction history", "rolling-100", "int", "Run length of current v2 label. Capped at 100."),
    "regime_h4_bars_since_last_flip": ("regime_stability", "backfill v2_direction history", "rolling-100", "int", "H4 bars since most recent v2 label change. -1 if no flip in window."),
    "regime_changed_in_last_1":    ("regime_stability", "backfill v2_direction history", "1 H4 bar", "binary", "v2 label N=1 H4 bar ago != current."),
    "regime_changed_in_last_5":    ("regime_stability", "backfill v2_direction history", "5 H4 bars", "binary", "v2 label N=5 ago != current."),
    "regime_changed_in_last_10":   ("regime_stability", "backfill v2_direction history", "10 H4 bars", "binary", "v2 label N=10 ago != current."),
    "regime_changed_in_last_20":   ("regime_stability", "backfill v2_direction history", "20 H4 bars", "binary", "v2 label N=20 ago != current."),
    "regime_changed_in_last_50":   ("regime_stability", "backfill v2_direction history", "50 H4 bars", "binary", "v2 label N=50 ago != current."),
    "regime_v2_score_change_1":    ("regime_dynamics", "backfill v2_score history", "1 H4 bar", "int", "v2_score[now] - v2_score[1 H4 ago]. Velocity."),
    "regime_v2_score_change_5":    ("regime_dynamics", "backfill v2_score history", "5 H4 bars", "int", "v2_score[now] - v2_score[5 H4 ago]."),
    "regime_v2_score_change_20":   ("regime_dynamics", "backfill v2_score history", "20 H4 bars", "int", "v2_score[now] - v2_score[20 H4 ago]."),
    "regime_v2_score_max_in_20":   ("regime_dynamics", "backfill v2_score history", "20 H4 bars", "int", "max v2_score in last 20 H4 bars."),
    "regime_v2_score_min_in_20":   ("regime_dynamics", "backfill v2_score history", "20 H4 bars", "int", "min v2_score in last 20 H4 bars."),
    "regime_v2_score_range_in_20": ("regime_dynamics", "backfill v2_score history", "20 H4 bars", "int", "max - min v2_score in 20-bar window. Regime turbulence."),
    "regime_v1_v2_disagreement":   ("regime_consistency", "backfill.v1_direction vs v2_direction", "single", "binary", "v1 vs v2 H4 detector emit different labels at same boundary."),
    "regime_counter_to_v2":        ("regime_x_side", "side, backfill.v2_direction", "single", "binary", "Trade direction counter to v2 regime (replicates K54 v1 counter_direction_flag for v2)."),
    "regime_counter_to_v1":        ("regime_x_side", "side, backfill.v1_direction", "single", "binary", "Trade direction counter to v1 regime."),
    "regime_aligned_v2":           ("regime_x_side", "side, backfill.v2_direction", "single", "binary", "Trade direction aligned with v2 regime."),
    "regime_aligned_v1":           ("regime_x_side", "side, backfill.v1_direction", "single", "binary", "Trade direction aligned with v1 regime."),
    "regime_long_in_bullish_v2":   ("regime_x_side", "side, backfill.v2_direction", "single", "binary", "LONG in v2=bullish. F2 cohort: XAU London/trending_bull/LONG -59.8pp WR delta."),
    "regime_short_in_bearish_v2":  ("regime_x_side", "side, backfill.v2_direction", "single", "binary", "SHORT in v2=bearish. Complementary cohort to F2; A6 LONG-side decay finding."),
    "regime_fleet_bullish_count":  ("cross_instrument", "fleet 7 backfill.latest_at(ts)", "point", "int", "Number of fleet symbols (excl self) with v2=bullish at ts."),
    "regime_fleet_bearish_count":  ("cross_instrument", "fleet 7 backfill.latest_at(ts)", "point", "int", "Number with v2=bearish."),
    "regime_fleet_transitional_count": ("cross_instrument", "fleet 7 backfill.latest_at(ts)", "point", "int", "Number transitional or missing-row."),
    "regime_fleet_aligned_with_self": ("cross_instrument", "fleet 7 backfill", "point", "int", "Number of fleet symbols with v2 == self v2."),
    "regime_fleet_score_mean":     ("cross_instrument", "fleet 7 backfill.v2_score", "point", "float", "Mean v2_score across fleet (excl self)."),
    "regime_fleet_score_signed_agreement": ("cross_instrument", "self.v2_score, fleet mean", "point", "binary", "sign(self.v2_score) == sign(mean fleet score)."),
    "regime_xau_v2_is_bullish":    ("cross_instrument", "XAUUSD backfill.latest_at(ts)", "point", "binary", "XAU regime anchor. XAU is risk-correlated with metals + indices per cross_instrument_correlation_gate."),
    "regime_xau_v2_is_bearish":    ("cross_instrument", "XAUUSD backfill.latest_at(ts)", "point", "binary", "XAU regime anchor."),
    "regime_xau_matches_self":     ("cross_instrument", "XAU vs self v2_direction", "point", "binary", "XAU v2 == self v2."),
    "regime_xau_opposite_self":    ("cross_instrument", "XAU vs self v2_direction", "point", "binary", "XAU bullish + self bearish, or vice versa."),
    "regime_xau_score":            ("cross_instrument", "XAUUSD backfill.v2_score", "point", "int", "Raw XAU v2_score (signed)."),
    "regime_xau_score_abs":        ("cross_instrument", "XAUUSD backfill.v2_score", "point", "int", "abs(XAU v2_score)."),
    "regime_xau_to_self_score_diff": ("cross_instrument", "self.v2_score - XAU.v2_score", "point", "int", "Drift of self regime relative to gold anchor."),
    "regime_d1_direction_bullish": ("cross_timeframe", "D1 OHLCV close[-1] vs close[-6]", "5 D1 bars", "binary", "D1 5-bar close-vs-close > +0.5%. Approximation; D1 backfill not available."),
    "regime_d1_direction_bearish": ("cross_timeframe", "D1 OHLCV close[-1] vs close[-6]", "5 D1 bars", "binary", "D1 5-bar close-vs-close < -0.5%."),
    "regime_h4_d1_agreement":      ("cross_timeframe", "v2 H4 vs D1 swing dir", "point", "binary", "H4 v2 label matches D1 5-bar direction (bull-bull or bear-bear)."),
    "regime_atr_h4_14":            ("regime_conditional_vol", "H4 OHLCV ATR(14)", "14 H4 bars", "float", "Raw H4 ATR(14). Instrument-specific magnitude (gold ~10-30, USDJPY ~0.1-0.3). Scaled relatively in ratio features."),
    "regime_atr_h4_ratio_to_20":   ("regime_conditional_vol", "H4 ATR(14) / mean ATR(14, last 20)", "20 H4 bars", "float", "ATR vs 20-bar baseline. >1 = vol expanding within regime."),
    "regime_atr_h4_ratio_to_50":   ("regime_conditional_vol", "H4 ATR(14) / mean ATR(14, last 50)", "50 H4 bars", "float", "ATR vs 50-bar baseline. Slower reference."),
    "regime_atr_h1_to_h4_ratio":   ("regime_conditional_vol", "H1 ATR(14) / H4 ATR(14)", "14 H1 + 14 H4 bars", "float", "Microstructure-vs-macro vol regime."),
    "regime_backfill_available":   ("regime_data_quality", "backfill.latest_at(symbol, ts)", "point", "binary", "CRITICAL: 1 if backfill row found; 0 if missing (e.g. US30_cash, pre-2026-01-21). Distinguishes zero-vs-missing."),
    "regime_backfill_h4_bars_stale": ("regime_data_quality", "ts - backfill_row.ts", "point", "int", "H4 bars between located backfill row and ts. -1 if no row. >=1 means weekend or pre-coverage gap."),
}

missing_meta = [k for k in feat_keys if k not in META]
extra_meta = [k for k in META if k not in feat_keys]
if missing_meta or extra_meta:
    print(f"WARN: META missing {missing_meta}; extra {extra_meta}")

# Write CSV
out_csv = ROOT / "research/ml_program/feature_catalogs/regime.csv"
out_csv.parent.mkdir(parents=True, exist_ok=True)
with out_csv.open("w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow([
        "feature_name", "family", "group", "source", "lookback", "dtype",
        "stability_spearman_pre_2026_04", "description",
    ])
    for fk in feat_keys:
        m = META.get(fk, ("regime", "unknown", "", "", "TBD", ""))
        group, source, lookback, dtype, desc = m
        rho = stab.get(fk)
        rho_str = f"{rho:+.4f}" if isinstance(rho, (int, float)) else "NA"
        wr.writerow([fk, "regime", group, source, lookback, dtype, rho_str, desc])
print(f"Wrote: {out_csv}")

# Top features by |stability|
ranked = sorted(
    [(k, stab.get(k)) for k in feat_keys],
    key=lambda kv: abs(kv[1]) if isinstance(kv[1], (int, float)) else 0.0,
    reverse=True,
)
top5 = [(k, v) for k, v in ranked[:5]]
print("top5:", top5)
with (ROOT / "research/ml_program/data/regime_top5.json").open("w") as f:
    json.dump({"top5": top5, "n_features": len(feat_keys)}, f, indent=2)
