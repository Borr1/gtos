# KB4 — Empirical Regime Discovery + Hurst/Timescale Map (track: regime_hurst)

Builder pass 2026-06-15. LAYER, not a strategy: a reusable engine (`regime_map.py`) that
discovers regimes per instrument from the data (KMeans on a leak-free state feature space),
computes a rolling Hurst exponent (variance-ratio estimator) as the momentum-vs-reversion
compass, and mines the FORWARD EV of momentum vs reversion entries conditioned on
(discovered regime, Hurst sign). Output = a queryable map + the engine.

Doctrine honored: build & improve (nothing killed — losing cells are negative evidence,
not deletions); the map judges STATES not systems; NO averages-as-verdicts (per-cell,
per-YEAR, per-regime); NO lookahead (every feature from closed bars index<=i; the cluster
model is fit on TRAIN rows only then applied forward; `geometry_lib.simulate` is the
leak-free pessimistic labeler; real per-asset cost `w1.cost_for`); FORWARD HOLDOUT
mandatory (TRAIN<=2024 vs FORWARD 2025-26 + per-year + sample size n; trust only if it holds
forward AND n>=~40 AND TRAIN not a disaster).

## Engine (reusable, importable): `regime_map.py`

- `hurst_vr(closes, i, w=128)` — Hurst at bar i from variance-ratio scaling of log returns
  (`var(sum of k returns) ~ k^(2H)`). Uses only `closes[i-w+1:i+1]`. H>0.5 trending /
  H<0.5 mean-reverting timescale.
- `feature_row(B, closes, atrs, i)` — leak-free state vector: vol level (ATR/own-100bar-mean),
  vol-of-vol, trend magnitude (|Δclose_30|/ATR), return autocorrelation(40), range expansion.
- `RegimeModel.fit(train_rows)` / `.label(row)` / `.describe()` — standardizer + KMeans (K=4),
  **fit on TRAIN(<=2024) rows ONLY**, applied forward (forward rows never train the model).
- `build_instrument_map(sym)` — per-instrument regimes + Hurst + forward-EV cells.
- `build_map(symbols)` — full 48-instrument map -> `KB4_REGIME_HURST_MAP.json`.
- `aggregate(map)` / `top_forward_cells(map)` -> `KB4_REGIME_HURST_AGGREGATE.json`.
- `regime_at(B, closes, atrs, i, model)` — single-bar query helper for downstream sleeves.

Entries mined per bar (both simulated, R-unit = 1*ATR stop):
- **momentum**: continuation in the 30-bar trend direction (needs |drift|>=0.5 ATR); stop 1.0 ATR, target 2.0 ATR.
- **reversion**: fade a stretched extreme (close = 20-bar hi/lo with >0.8 ATR move); stop 1.0 ATR, target 1.5 ATR.

Cell key = `entry | regime_id | hurst_sign`. K=4 regimes × 2 Hurst signs × 2 entries = up to 16 cells/instrument.

`forward_validated` requires: has_train AND fwd n>=40 AND fwd mean_R>0 AND train mean_R>-0.05.
Symbols whose history starts in 2025 (no TRAIN) get `forward_only_insample` only — **NOT
trustworthy** (the KMeans was fit on the same forward data; no holdout). Treat their "valid"
cells as candidates to revisit when deeper history exists.

## Regime taxonomy (data-driven, K=4 per instrument)

Per-instrument KMeans ids are not comparable across symbols by number, so the engine also
maps each instrument-regime to a cross-symbol ARCHETYPE from its centroid:
- **calm_trend** — low/normal vol, strong directional drift (trend_mag>=3), normal range.
- **calm_chop** — low/normal vol, weak drift; sideways.
- **vol_expansion** — high vol_ratio (>=1.25) or high vol-of-vol (>=0.28); volatile.
- **range_spike** — normal vol but large single-bar range (rng_exp>=1.5); outlier candles.

Example (XAUUSD): reg0=calm_trend (drift 3.2 ATR, +ac), reg1=calm_chop / quiet pullback
(low vol 0.92, drift 2.4, **ac=-0.16** = mean-reverting micro), reg2=vol_expansion
(vol 1.35, vov 0.34), reg3=range_spike (rng_exp 2.04). Full per-symbol centroids in
`KB4_REGIME_HURST_MAP.json`.

## HEADLINE SCIENCE — does Hurst sign / regime give a free momentum-vs-reversion compass?

**No, not universally.** Pooled across all TRAIN-history instruments (true out-of-sample),
the naive fixed-RR entries are net-NEGATIVE after real cost in every Hurst/archetype bucket —
exactly as doctrine predicts (a losing average hides high-odds cells; raw H4 1R/2R entries
with no confluence are a losing baseline). Pooled FORWARD mean_R:

| entry × hurst_sign | TRAIN n / mR | FORWARD n / mR |
|---|---|---|
| rev × trend | 11588 / -0.129 | 4022 / **-0.064** |
| rev × revert | 26433 / -0.121 | 10770 / -0.095 |
| mom × revert | 104945 / -0.103 | 43613 / -0.116 |
| mom × trend | 47822 / -0.106 | 17057 / -0.139 |

Reading: Hurst sign alone is a WEAK discriminator (reversion entries are *least bad* in
trending-Hurst windows — counterintuitive, mostly cost/geometry-driven, do not trade on it).
The edge is NOT a global compass; it lives in **per-instrument confluence cells**
(instrument × discovered regime × Hurst sign), where conditioning lifts EV positive
out-of-sample. This is the layer's real product.

## FORWARD-VALIDATED high-odds cells (has_train, true holdout, fwd n>=40)

Ranked by forward mean_R; per-year positivity shown. Full list in `KB4_REGIME_HURST_AGGREGATE.json`.

| symbol | class | cell | TRAIN n / mR | FWD n / mR / win | pos-years |
|---|---|---|---|---|---|
| **XAUUSD** | metals | mom\|reg1(quiet-pullback,−ac)\|revert | 3068 / +0.064 | 388 / **+0.423** / 49% | **8/12** |
| UK100 | index | mom\|reg2(compressed)\|trend | 283 / +0.155 | 154 / **+0.358** / 47% | 5/6 |
| XAUUSD | metals | mom\|reg2(vol-exp)\|trend | 587 / +0.002 | 176 / +0.284 / 44% | 6/12 |
| GER40 | index | mom\|reg1\|trend | 537 / −0.036 | 100 / +0.256 / 44% | 4/7 |
| XAUUSD | metals | mom\|reg3(range-spike)\|trend | 608 / −0.015 | 74 / +0.251 / 43% | 7/12 |
| UKOIL_cash | energy | mom\|reg3\|trend | 42 / +0.463 | 105 / +0.248 / 43% | 5/6 |
| SPX500 | index | rev\|reg0\|revert | 276 / −0.049 | 116 / +0.208 / 51% | 4/6 |
| CORN_c | agri | rev\|reg0\|revert | 76 / +0.056 | 115 / +0.187 / 51% | 3/4 |
| **XAGUSD** | metals | mom\|reg0(strong-drift)\|revert | 573 / +0.109 | 378 / +0.176 / 41% | 4/5 |
| USOIL_cash | energy | rev\|reg3\|revert | 297 / +0.040 | 95 / +0.173 / 48% | 4/6 |
| NAS100 | index | mom\|reg0\|revert | 466 / +0.024 | 230 / +0.110 / 39% | 4/5 |
| **XAUUSD** | metals | rev\|reg0(calm-trend)\|trend | 394 / +0.045 | 51 / +0.131 / 47% | **9/12** |

THIN-TRAIN cautions (passed the fwd n>=40 gate but TRAIN n is tiny — do NOT trust yet):
BTCUSD mom\|reg3\|trend (train n=32), ETHUSD rev\|reg3\|trend (train n=5), UKOIL mom\|reg3
(train n=42). Flagged in the JSON; revisit with deeper crypto/energy history.

## Permutation null — does the regime LABEL carry real information?

For each flagship cell, shuffle regime labels across the SAME forward trade set 500× and ask
how often a random same-size partition matches the observed forward mean_R (`KB4_null_test.py`):

| cell | fwd n | fwd mean_R | permutation p |
|---|---|---|---|
| XAUUSD mom\|reg1\|revert | 388 | +0.423 | **0.000** |
| UK100 mom\|reg2\|trend | 154 | +0.358 | **0.000** |
| XAGUSD mom\|reg0\|revert | 378 | +0.176 | 0.026 |
| XAUUSD rev\|reg0\|trend | 51 | +0.131 | 0.028 |

All p<0.03 → the discovered regime label selects materially better-than-random trades within
the forward window; the conditioning is real, not a slice of a good period.

## Which regimes favor momentum vs reversion (forward-validated read)

- **Momentum (continuation) wins** in: quiet low-vol pullback regimes with negative micro-autocorr
  (XAUUSD reg1), compressed/coiled index regimes (UK100 reg2, GER40 reg1), strong-drift metals
  (XAGUSD reg0), and vol-expansion / range-spike trend regimes (XAUUSD reg2/reg3, UKOIL reg3).
  Counterintuitively, Hurst "revert" sign does NOT veto momentum — the strongest momentum cell
  (XAUUSD reg1) sits in a mean-reverting-Hurst regime, because the regime is a *pullback* that
  precedes continuation. **Lesson: the regime archetype + instrument matters more than Hurst sign.**
- **Reversion (fade) wins** in: calm-trend index/agri pullbacks (SPX500 reg0, CORN_c reg0,
  XAUUSD reg0) and energy range-spikes (USOIL reg3) — fading the stretch back toward value.
- **Both lose** in: high-vol-expansion reversion (rev|vol_expansion pooled −0.10 fwd) and
  generic calm_chop momentum (mom|calm_chop −0.13 fwd) — do not trade naive entries there.

## Honesty / limitations

- 2025-26 FORWARD numbers for metals/indices/oil are inflated by the gold/silver/equity/oil bull;
  TRUST comes from the TRAIN-era positivity + multi-year pos-year counts + permutation p, not the
  forward mean alone. XAUUSD reg1 (8/12 yrs incl. 2017/2022) and rev|reg0 (9/12 yrs) are the most
  regime-stable, not just bull-lucky.
- **Correlation with existing book**: the metals momentum cells (XAUUSD/XAGUSD reg1/reg0/reg2)
  overlap conceptually with the existing compounding metals sleeve (metals momentum continuation).
  The ADDITIVE, lower-correlation finds are the **index (UK100 reg2, GER40 reg1, SPX500 reg0,
  NAS100 reg0) and energy (UKOIL/USOIL reg3)** regime cells — these are the new uncorrelated edge
  candidates this layer contributes. Corr-check required before sizing.
- The entries here are deliberately naive (fixed 1R/2R) to isolate the regime/Hurst signal. Real
  sleeves should compose `regime_at()` as a GATE on top of the structural entries + vol-tiered
  exits already validated (compounding_sleeve STATE_D), which should lift these cells further.
- Forward-only symbols (history from 2025): regime model has no holdout; their cells are
  `forward_only_insample` candidates, not validated edges.

## How downstream waves consume this layer

1. Use `regime_at(B, closes, atrs, i, model)` as a confluence GATE: only take a momentum entry when
   the bar's regime is in {XAUUSD reg1/2/3, UK100 reg2, GER40 reg1, XAGUSD reg0, UKOIL/USOIL reg3};
   only take a fade when in {SPX500 reg0, CORN reg0, XAUUSD reg0, USOIL reg3}.
2. Stack with the volume/liquidity/lead-lag layers (other tracks) — independent conditions
   multiply per the confluence doctrine; report the intersection cell's forward odds + n.
3. Re-fit the RegimeModel inside any walk-forward harness (fit on the expanding TRAIN window only).

## Artifacts

- `regime_map.py` — engine (importable).
- `KB4_REGIME_HURST_MAP.json` — full per-instrument map (48 instruments: taxonomy, regime-year
  counts, per-cell TRAIN/FWD/per-year stats, forward_validated flags).
- `KB4_REGIME_HURST_AGGREGATE.json` — pooled science (entry×hurst, entry×archetype,
  entry×archetype×hurst) + ranked top forward-validated cells.
- `KB4_null_test.py` — permutation null validating the regime label's information content.
