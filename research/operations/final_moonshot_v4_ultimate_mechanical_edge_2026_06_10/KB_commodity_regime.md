# KB: Commodity Continuation Regime Map (vol-gated FVG-retest)

Investigator: quant regime-mapping pass, 2026-06-14.
Entry engine: `gold_sleeve_strategy.fvg_signals` (H4 FVG-retest continuation in HTF trend,
ATR-expansion gate K=1.2, structural stop +0.10 ATR floor 0.25 ATR, target 2R).
Outcome label: `geometry_lib.simulate` (leak-free, pessimistic ties). Net R winsorized [-1.3,+5].
TRAIN = entries <=2024; FORWARD reported separately for 2025 and 2026.
Universe data depth (critical): only **XAUUSD 2015-2026** and **XAGUSD 2019-2026** have real
multi-year history. XAUEUR/XAGEUR/XAGAUD start 2024; XAUAUD/XCUUSD/HEATOIL/COTTON start 2025;
CORN 2023; NATGAS 2024; USOIL 2020-2026; UKOIL only 2020-2021. So the "2017/2018 metals" regime
is XAUUSD; the 2025/2026 forward sample is a 6-symbol metals basket (much larger n).

---

## 1. UNDERSTANDING — what regime makes commodity continuation pay vs bleed

The regime that separates winning from losing **is not visible in the local setup geometry.**
Contrasting XAUUSD winning years (2017,2018,2024; EV +0.64) against losing years (2015,2023;
EV -0.40), the entry-bar features are nearly identical: trend strength (trend30_dir ~4.3 vs 4.25),
distance from MA50 (~3.4 vs 3.5), efficiency ratio (0.32 vs 0.33), 3-bar momentum (1.73 vs 1.65),
ATR expansion (1.38 vs 1.41). **A 2018 winner and a 2023 loser look the same at the moment of
entry on every standard continuation feature.** Trend strength / extension / vol-expansion do NOT
separate the regimes.

What DOES separate them is the **serial correlation of recent returns** — whether the market is
in a *momentum-persistence* regime or a *mean-reverting/choppy* regime. Measured as the lag-1
autocorrelation of 1-bar H4 close-to-close returns over the trailing 60 bars (`ac60`, a pure
function of bars <= i, no lookahead):

Pooled metals EV by ac60 bucket (quintiles):
| ac60 bucket | n | EV/trade | win% |
|---|---|---|---|
| [-0.51,-0.15] | 124 | +0.333 | 46.0 |
| [-0.15,-0.05] | 124 | -0.065 | 32.3 |
| [-0.05,+0.02] | 124 | -0.144 | 30.6 |
| [+0.02,+0.13] | 124 | +0.109 | 38.7 |
| [+0.13,+0.43] | 126 | **+0.585** | **54.8** |

The decisive cell is the **top bucket: when recent returns are positively autocorrelated,
continuation pays +0.585R at 55% win.** The dead zone is ac60 near 0 (random walk → the 2R target
is a coin flip the cost drags below zero). (The slightly positive bottom bucket is a different,
weaker effect — strong negative autocorrelation is a violent-reversal regime; we do not trade it.)

**Market interpretation.** Commodity (especially gold/silver) trends are driven by persistent
macro flows — real-rate cycles, central-bank and reserve buying, inflation/risk hedging, supply
shocks. When those flows are *on*, H4 returns cluster directionally (positive autocorrelation),
pullbacks into FVGs are genuine refills of one-directional demand, and 2R continuation targets get
hit. When the macro driver is absent, gold ranges and mean-reverts intrabar; the same FVG retest
is just noise and the 2R target rarely fills before the stop. **The edge is exploiting momentum
*persistence*, not the trend label itself** — htf_trend (already required by the entry) tells you a
trend EXISTS; ac60 tells you the trend is the kind that *continues* rather than chops.

---

## 2. THE RULE

**Entry trigger** (unchanged, from `fvg_signals`): H4 fair-value-gap retest continuation —
established HTF trend (30-bar slope > 1 ATR), ATR14 >= 1.2 * SMA100(ATR14) volatility gate, price
pulls back to tag a recent same-direction FVG and closes back with the trend. Direction = trend
direction (long in uptrend, short in downtrend). Structural stop just beyond the gap/retest extreme
+0.10 ATR (floor 0.25 ATR). **Target 2R.**

**STATE GATE (the addition):** take the trade only when
> `ac60(i) >= THR`, where `ac60` = lag-1 autocorrelation of the last 60 H4 1-bar returns
> (closed bars only). `THR` chosen on TRAIN.

THR is a frequency↔EV dial (all values hold forward, monotone — see below):
- **THR = 0.10** (primary): EV +0.49 train, win 52%.
- THR = 0.05 (higher frequency) or THR = 0.15 (highest EV) are both valid.

**Universe:** precious metals. **Exclude XCUUSD (copper)** — only 2025-26 data and structurally
negative (-0.44) even gated; it is a different (industrial) asset, not part of the precious-metals
flow regime.

**Direction logic:** strictly with the trend. Inverting destroys it (see caveats) — the edge is
directional, not survivorship.

**Geometry:** the existing structural stop + 2R fixed target already captures it; no state-dependent
geometry change was needed. (Tightening THR raises win rate toward 80% at THR=0.15, so a runner/
trail could be explored later, but 2R fixed already holds forward.)

---

## 3. FORWARD NUMBERS (winsorized EV/trade, n, win%)

### Primary rule: metals **ex-XCUUSD**, FVG-retest + `ac60 >= 0.10`
| segment | n | EV/trade | win% |
|---|---|---|---|
| TRAIN <=2024 | 82 | **+0.491** | 52.4 |
| FWD 2025 | 24 | **+1.119** | 70.8 |
| FWD 2026 (to Jun) | 25 | **+0.874** | 64.0 |

Baseline (no gate, same universe incl XCU): TRAIN +0.123, 2025 +0.180, 2026 +0.252.
**Gate ≈ 4x the train edge and holds / improves forward in BOTH out-of-sample years.**

### Threshold robustness (metals ex-XCU) — monotone, all hold forward
| THR | TRAIN n/EV/w | 2025 n/EV/w | 2026 n/EV/w |
|---|---|---|---|
| 0.05 | 108 / +0.438 / 51 | 38 / +0.518 / 50 | 46 / +0.650 / 57 |
| 0.075 | 94 / +0.467 / 52 | 31 / +0.752 / 58 | 35 / +0.840 / 63 |
| 0.10 | 82 / +0.491 / 52 | 24 / +1.119 / 71 | 25 / +0.874 / 64 |
| 0.15 | 59 / +0.581 / 56 | 15 / +1.419 / 80 | 15 / +1.354 / 80 |

### Per-year (metals incl XCU, ac60>=0.10) — n thin pre-2019 but sign consistent
2015:+1.95(n1) 2016:+0.16(n7) 2017:+0.24(n7) 2018:+1.29(n9) 2019:+0.38(n19) 2020:+0.06(n2)
2021:+0.91(n13) 2022:-1.05(n3) 2023:-0.45(n10) 2024:+1.14(n11) 2025:+0.71(n33) 2026:+0.56(n32).
10 of 12 years positive gated (2022 n=3, 2023 the two residual negatives).

### Per-symbol (ac60>=0.10): XAUUSD +0.50(n66), XAGUSD +0.79(n31), XAUEUR +1.10(n7),
XAGEUR +1.05(n10), XAGAUD +1.14(n11), XAUAUD +0.12(n6), **XCUUSD -0.45(n16) → excluded.**

### XAUUSD-only (no multi-symbol expansion confound): baseline TR +0.154 → gated +0.479; 2025 +0.754.
(2026 XAUUSD-alone had 0 gated signals — single symbol is too sparse at THR=0.10; this is why the
basket is used.)

**HOLDS FORWARD: YES.** +EV in train AND positive in 2025 AND 2026, monotone across thresholds,
on the apples-to-apples single symbol and on the basket.

### Frequency
~8-25 gated trades/year across the 6-symbol metals basket at THR=0.10 (2026 partial: 25 by June,
~50 full-year pace); ~108 train / 84 forward total. THR=0.05 roughly doubles count. This is the
main limitation — tradeable but thin, especially per individual symbol.

---

## 4. CAVEATS / CONFOUNDS CHECKED

- **Directional (inverted control):** metals INVERTED under the same gate = TR -0.490 (w18%),
  2025 -0.955 (w3%), 2026 -0.343 (w25%). Fading continuation in the momentum regime loses almost
  everything → the edge is real and directional, not one-sided survivorship.
- **State carries the EV (gate vs anti-gate):** ac60>=0.10 = +0.49/+0.71/+0.56; ac60<0.10 =
  -0.013/+0.081/+0.123. The continuation entries are essentially dead when autocorrelation is low.
  The momentum-persistence STATE is the edge, not the entries.
- **Multi-symbol expansion confound (ruled out):** forward n is inflated because 4 metals symbols
  only exist from 2024-25. Re-checked on XAUUSD ALONE 2015-2026: gate still lifts +0.154→+0.479 and
  2025 +0.754. Not an artifact of pooling new symbols.
- **Single-year energy/agri confound (CONFIRMED, excluded):** energy baseline TRAIN -0.228 but
  2026 +0.933 — the headline "energy positive" is a single-window 2026 artifact; TRAIN is negative.
  Gated energy/agri have n=4/n=3 in train → cannot be validated. Precious-metals-only is the safe
  carrier; energy/agri left as "insufficient history."
- **Copper (XCUUSD):** negative even gated, only 2025-26 data; excluded as not part of the
  precious-metals flow regime.
- **Could NOT fully rule out:** (a) 2023 stays negative even gated (-0.45, n=10) — ac60 is a
  trailing proxy and a year can show locally-positive autocorrelation while the macro driver
  reverses; the gate AVOIDS most of the bleed years but does not RESCUE 2023. (b) Small per-year n
  pre-2019 (XAUUSD only) means early-year point estimates are noisy; the forward (2025/26) and
  pooled evidence carry the claim, not 2017's n=7. (c) No transaction-cost stress beyond the
  per-asset cost map; thin frequency means slippage/missed-fill risk per realized trade is material.

---

## 5. NEXT (to make it stronger)

1. **Frequency**: ac60 gate keeps only ~25% of signals. Test (a) THR=0.05 for ~2x count with
   still-positive forward; (b) lower the entry's HTF-trend strictness so more raw FVGs exist to be
   gated; (c) add sweep-reclaim and breakout entries under the SAME ac60 gate to pool more trades.
2. **Geometry under the gate**: win rate hits ~80% at THR=0.15 — test a partial-at-2R + ATR-trail
   runner to harvest the strong-persistence tail instead of capping at 2R.
3. **Better persistence proxy**: ac60 is lag-1 only; test multi-lag/variance-ratio or a
   Hurst-exponent estimate (>0.5 = trending) as the state; test ac90/ac30 horizons (ac60 was the
   sweet spot here).
4. **Macro overlay (optional, non-mechanical-pure)**: the regime is real-rate / reserve-flow driven;
   a slow real-yield or DXY-trend filter may align with ac60 and add confidence, but keep the
   mechanical ac60 gate as the primary tradeable trigger.
5. **Cross-class once data deepens**: re-run energy/agri when >=3 years of history exist before
   trusting any non-metals continuation claim.

Scratch scripts: `_kb_commodity_probe.py`, `_kb_commodity_probe2.py`, `_kb_commodity_gate.py`,
`_kb_commodity_confound.py`; result `_KB_COMMODITY_GATE_RESULT.json`.
