# Lane l5 — cost re-denominated in money, and the gate rebuilt

**Population.** `CJ_RECLOCKED_S0R0_POOL_V1` January 2026, 27,658 candidates, true UTC, joined to
`w0_WORKING_SET.jsonl.gz` and to the no-look-ahead born-state anchor
`w0cap2_DECISION_ANCHOR_V1.jsonl.gz`. Account basis $100,000 FTMO
(`config/profiles/operator_profile.yaml:82`). Broker truth from
`research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json` (167 FTMO
instruments) and, as a second independent truth source, `src/costs/spread_model.py` evaluated at
**each candidate's own decision instant** (era ratio + intraweek multiplier).

All 27,658 rows mapped to a broker instrument with zero misses
(`l5_MONEY_BUILD_V1.json` → `missing_symbols: {}`).

Everything below is an **offline scorer**. No engine file, config file or contract-bound path was
edited.

---

## 0. The arithmetic that had to be settled first

Two lines of the engine define the denominator:

```
spread_r     = spread_price / sl_distance                                   broker_net_cost_engine.py:300-304
commission_r = usd_per_lot / (sl_distance * usd_per_price_unit_per_lot)     broker_net_cost_engine.py:557-560
```

and sizing is fixed-fractional, `lots = risk_usd / (sl_distance × usd_per_price_unit_per_lot)`.
Therefore

> **cost_usd = cost_r × risk_usd, exactly, with no contract-spec term.**

`risk_distance` was verified to equal `|entry_price − stop_loss|` on all 27,658 rows
(max relative difference **0**).

**This kills the lane's own opening hypothesis in the form it was posed.** "Dividing by the stop
distance means an identical dollar cost looks four times worse on a stop four times tighter" is
false under fixed-fractional sizing: a stop four times tighter buys a position four times larger,
so the dollar cost rises in lockstep. `cost_r` is exactly *cost as a fraction of cash at risk*, and
against an R-denominated payoff that is the economically correct ratio.

**The denominator artifact that DOES exist is a different one**, and it is measured in §4: the
pool's `risk_per_trade_pct` spans **8×** (0.25 / 0.5 / 1.0 / 2.0 %), so a single flat `cost_r ≤ 0.15`
cap is a dollar cap of **$37.50 / $75 / $150 / $300** depending on which bucket the candidate
landed in.

---

## 1. Cost in price units and in dollars (item 1)

### 1.1 Pool-wide distributions, n = 27,658

| quantity | mean | p25 | p50 | p75 | p95 | max |
|---|---:|---:|---:|---:|---:|---:|
| `cost_r` (charged) | 0.6632 | 0.1383 | 0.3031 | 0.7031 | 2.6443 | 18.7758 |
| **cost, USD** | **547.10** | 133.47 | 327.02 | 671.91 | 2,014 | 13,587 |
| spread, USD | 418.13 | 70.15 | 205.46 | 475.78 | 1,746 | 12,216 |
| commission, USD | 93.25 | 0.00 | 13.13 | 141.26 | 381.47 | 2,336 |
| slippage, USD | 23.09 | 10.00 | 20.00 | 40.00 | 40.00 | 40.00 |
| swap, USD | 12.62 | 0.00 | 2.93 | 15.30 | 55.83 | 384.76 |
| **broker-true total cost_r** | **0.2466** | 0.0915 | 0.1626 | 0.2798 | 0.7105 | 7.7098 |
| **broker-true total, USD** | **278.37** | 61.75 | 151.39 | 361.26 | 923.84 | 6,160 |
| cost as bp of notional | 5.594 | 0.716 | 1.847 | 6.980 | 20.166 | 51.730 |
| notional, USD | 104,418,273 | 343,399 | 1,268,922 | 5,892,618 | 724,447,733 | 6,911,022,600 |
| implied lots | 44.24 | 8.95 | 28.03 | 55.36 | 152.54 | 936.45 |
| risk, USD | 1,155 | 500 | 1,000 | 2,000 | 2,000 | 2,000 |

**The average January candidate is charged $547 of cost against $1,155 of risk.** Broker truth
says it costs **$278**. Median charged $327 against a median true $151.

Aggregate over the month: frozen charges **$15,131,706**; broker truth is **$7,699,236**.

### 1.2 The frozen spread is a per-symbol CONSTANT — and it is wrong in both directions

`frozen_spread_price = spread_r × risk_distance` recovers the price-unit spread the engine
actually charged. For **16 of 24 symbols it takes exactly ONE value across every row in the month**
(100.00 % modal share): no session variation, no hour variation, no volatility variation, no era.

| symbol | rows | distinct frozen spread values | modal value |
|---|---:|---:|---|
| GBPJPY, GER40, JP225, NAS100, SPX500, UK100, AUDUSD, ETHUSD, CHFJPY, EURJPY, NZDUSD, GBPUSD, USDCHF, AUDJPY, EURGBP, USDCAD, US30_cash | 1 each | **1** | 0.018 / 5.0 / 50.0 / 50.0 / 10.0 / 5.0 / 5e-05 / 10.0 / 0.05 / 0.05 / 9e-05 / 0.0001 / 5e-05 / 0.011 / 7e-05 / 5e-05 / 8.0 |
| USDJPY | 893 | 25 | 0.005 (52.63 %) |
| EURUSD | 808 | 14 | 1e-05 (40.47 %) |
| XAUUSD | 2,356 | 78 | 0.31 (9.25 %) |
| XAGUSD | 928 | 88 | 0.049 (6.03 %) |
| USOIL_cash | 733 | 699 | — |
| UKOIL_cash | 790 | 750 | — |
| BTCUSD | 1,203 | 1,179 | — |

Against `src/costs/spread_model.py` evaluated at each candidate's own January instant
(`l5_SMTRUTH_V1.json`, coverage MEASURED on 17,853 rows / MODELLED 5,711 / TRANSFERRED 4,094;
decidable on 26,135 of 27,658):

| symbol | frozen (price units) | spread_model Jan-2026 | **charge error** | true cost per $1,000 risk |
|---|---:|---:|---:|---:|
| NAS100 | 50.0 | 1.7639 | **28.35× OVER** | $103.54 |
| SPX500 | 10.0 | 0.5060 | **19.76× OVER** | $147.07 |
| ETHUSD | 10.0 | 0.6000 | **16.67× OVER** | $308.00 |
| JP225 | 50.0 | 4.1376 | **12.08× OVER** | $94.46 |
| UK100 | 5.0 | 0.9150 | 5.46× OVER | $191.03 |
| US30_cash | 8.0 | 2.0732 | 3.86× OVER | $118.32 |
| GER40 | 5.0 | 1.3368 | 3.74× OVER | $102.55 |
| EURJPY | 0.05 | 0.014628 | 3.42× OVER | $313.58 |
| CHFJPY | 0.05 | 0.020191 | 2.48× OVER | $356.68 |
| GBPUSD | 0.0001 | 0.000045 | 2.20× OVER | $262.50 |
| EURGBP | 7e-05 | 0.000037 | 1.90× OVER | $407.05 |
| AUDUSD | 5e-05 | 0.000031 | 1.59× OVER | $256.45 |
| NZDUSD | 9e-05 | 0.000078 | 1.15× OVER | $507.17 |
| EURUSD / USDCHF / USDCAD | — | — | 1.00× | $158.89 / $301.48 / $355.10 |
| USDJPY | 0.005 | 0.005265 | 0.95× | $269.97 |
| AUDJPY | 0.011 | 0.012000 | 0.92× | $378.85 |
| GBPJPY | 0.018 | 0.021230 | 0.85× | $378.19 |
| XAUUSD | 0.30 | 0.445601 | 0.66× (1.5× UNDER) | $109.38 |
| XAGUSD | 0.045 | 0.074281 | 0.58× (1.7× UNDER) | $199.44 |
| USOIL_cash | 0.005427 | 0.039214 | **0.138× (7.2× UNDER)** | $715.34 |
| UKOIL_cash | 0.005093 | 0.037746 | **0.135× (7.4× UNDER)** | $725.01 |
| BTCUSD | 0.024196 | 1.000000 | **0.024× (41.3× UNDER)** | $361.68 |

Oil's `spread_model` estimate is MODELLED and **not decidable** (band [0.0214, 0.0665] on UKOIL) —
the only cohort where the truth source itself declines to decide. Its direction (frozen far too
cheap) is unambiguous at every point in the band.

Aggregated over all 27,658 rows against the `BROKER_TRUE_COSTS` artifact
(`l5_LEVERAGE_V1.json` → `charge_error_usd`):

- **gross over-charge $8,214,216 on 21,604 rows**
- **gross under-charge $781,746 on 6,054 rows**
- net over-charge $7,432,470
- rows charged correctly: **0 of 27,658**

### 1.3 Two more charged terms that are constants

- **Slippage is a flat `0.02 R` on all 27,658 rows** (1 distinct value). FTMO's measured slippage is
  **`0.003 R`** (`BROKER_TRUE_COSTS_V1_1.json` → `instruments.<sym>.slippage.value_r`, coverage
  MEASURED, provenance `GATE_G1B_RECEIPT.md:767-768`). **6.67× over-charge**, $23.09 charged vs
  $3.46 true per candidate, $543 k over the month.
- **Commission is broadly right**: pool mean `commission_r` 0.065224 vs independently recomputed
  broker-true 0.085307; median relative difference **0**; 9,905 rows are genuinely zero-commission;
  **1,523 rows (5.5 %) are charged zero where the broker schedule is non-zero.**

---

## 2. Decomposing the 20,448 cost refusals (item 2)

### 2.1 By limb — and the asymmetry nobody has published

| refusal class | n | gross R | fill-honest R | net at broker truth | mean charged $ | mean true $ |
|---|---:|---:|---:|---:|---:|---:|
| all refusals | 20,448 | −0.25475 | −0.28224 | −0.51949 | 699.78 | 318.09 |
| **spread limb ONLY** (spread_r > 0.10, total ≤ 0.15) | **374** | **+0.16630** | **+0.11888** | **+0.08568** | 104.50 | 70.18 |
| total limb only | 3,189 | −0.23407 | −0.24591 | −0.66054 | 273.40 | 345.39 |
| both limbs | 16,885 | −0.26798 | −0.29799 | −0.50625 | 793.49 | 318.43 |

Ex the `born_past_stop` artifact (w0-capture): spread-limb-only n = **373**, gross **+0.16942 ±
0.05288** (3.20 SE), **win 56.30 %** against a pool 39.72 %, **net at broker truth +0.08886 ±
0.05345**, fill-honest +0.12188.

Composition of those 373: GER40 165, XAGUSD 70, US30_cash 59, XAUUSD 40, JP225 20, UK100 11,
CHFJPY 5, EURJPY 3 — every one an index or metal, i.e. an instrument on which FTMO's measured
commission is zero, which is the only way `spread_r > 0.10` can coexist with `total ≤ 0.15`.
Families: `current_fvg_fill` 125, `displacement_continuation` 75, `liquidity_sweep_reclaim` 60,
`current_ob_retest` 29, `cross_asset_lead_lag` 24, rest ≤ 19. Risk buckets 0.5 % 196 / 1.0 % 169 /
2.0 % 8. Born states: at-limit 216, resting 138, marketable 19.

> **The separate spread cap is the only limb whose exclusive refusals are profitable, and it is
> the limb no prior session named.** Mean charged $104.50, true $70.10, gross +0.169, net-true
> +0.089.

### 2.2 By whether the refusal survives broker truth

2×2 of incumbent verdict × the same 0.10/0.15 thresholds applied to broker-true cost, on the
tradeable population (ex `born_past_stop`, n = 24,142):

| cell | n | share | gross | net at broker truth | mean charged $ | mean true $ |
|---|---:|---:|---:|---:|---:|---:|
| refused by both — **genuinely expensive** | 11,659 | 48.3 % | −0.11121 | −0.47307 | 835.72 | 418.44 |
| **refused by frozen, PASSES broker truth — model error** | **5,499** | 22.8 % | −0.11597 | −0.19763 | 346.67 | **73.37** |
| **admitted by frozen, REFUSED by broker truth — model error** | **1,835** | 7.6 % | −0.07623 | **−0.59301** | 70.73 | **292.08** |
| admitted by both | 5,149 | 21.3 % | −0.08614 | −0.16307 | 127.70 | 117.07 |

**The gate's verdict is inverted on 7,334 of 24,142 rows — 30.4 % of every decision it makes.**
On the full pool the same cells are 14,457 / 5,991 / 1,899 / 5,311 of 27,658.

Where the inversion lands is entirely predictable from §1.2:

| harmful admissions (frozen PASS, truth REFUSE) | n | share | charged $ | true $ |
|---|---:|---:|---:|---:|
| UKOIL_cash | 589 | 32.10 % | 34.16 | 370.16 |
| USOIL_cash | 553 | 30.14 % | 35.46 | 365.03 |
| XAUUSD | 553 | 30.14 % | 121.52 | 156.54 |
| XAGUSD | 92 | 5.01 % | 97.31 | 156.32 |
| all others | 48 | 2.61 % | — | — |

| missed admissions (frozen REFUSE, truth PASS) | n | share | charged $ | true $ |
|---|---:|---:|---:|---:|
| NAS100 | 1,070 | 19.46 % | 664.10 | 31.25 |
| SPX500 | 827 | 15.04 % | 414.54 | 33.04 |
| GER40 | 769 | 13.98 % | 116.37 | 36.81 |
| US30_cash | 686 | 12.47 % | 255.70 | 84.91 |
| UK100 | 546 | 9.93 % | 196.35 | 40.78 |
| JP225 | 491 | 8.93 % | 164.44 | 38.73 |
| EURJPY / ETHUSD / GBPUSD / CHFJPY | 231 / 226 / 189 / 171 | 4.20 / 4.11 / 3.44 / 3.11 % | — | — |

**92.4 % of the harmful admissions are oil and gold; 79.8 % of the missed admissions are equity
indices.** The gate systematically deletes the index book and systematically admits the oil book,
because the frozen spread is 12–28× too high on indices and 7–41× too low on oil and crypto.

### 2.3 The denominator artifact, in the form it actually exists

The incumbent's `cost_r ≤ 0.15` is a **dollar** ceiling of $37.50 at 0.25 % risk, $75 at 0.5 %,
$150 at 1.0 % and $300 at 2.0 %. Refusals whose real dollar cost is at or below the $150 that a
1 %-risk candidate is allowed:

| | n | gross | fill-honest | net at broker truth | mean charged $ |
|---|---:|---:|---:|---:|---:|
| refused **and** cost ≤ $150 (denominator artifact) | 2,437 | **−0.00424** | −0.03251 | −0.32844 | 97.18 |
| refused and cost > $150 (genuinely expensive) | 18,011 | −0.28864 | −0.31603 | −0.54534 | 781.31 |

Ex `born_past_stop`: 2,407 rows at gross **+0.00818** — **the only refused subpopulation in the
whole pool with a positive gross mean.**

Refusals by risk bucket (`l5_DECOMPOSE_V1.json` → `refusals_by_risk_pct`) confirm the mechanism is
the risk fraction, not the stop: mean charged cost among refusals is $194 at 0.25 % risk and $730 at
2 %, for the same `cost_r` ceiling.

---

## 3. Does `cost_r` predict a bad trade? (item 3)

### 3.1 It does — weakly, and only because it is a stop-width proxy

Deciles of `cost_r` against realized gross, ex `born_past_stop` (n = 24,142):

| decile | n | cost_r range | mean charged $ | gross R | win % |
|---:|---:|---|---:|---:|---:|
| 1 | 2,414 | 0.0236–0.0685 | 52.8 | −0.05334 | 45.98 |
| 2 | 2,414 | 0.0685–0.1071 | 109.7 | −0.13188 | 43.87 |
| 3 | 2,414 | 0.1071–0.1477 | 169.1 | −0.02406 | 47.39 |
| 4 | 2,414 | 0.1478–0.1993 | 236.9 | −0.10050 | 44.41 |
| 5 | 2,415 | 0.1994–0.2806 | 330.9 | −0.05831 | 42.65 |
| 6 | 2,414 | 0.2806–0.3917 | 420.3 | −0.08077 | 39.73 |
| 7 | 2,414 | 0.3918–0.5364 | 494.2 | −0.08851 | 38.36 |
| 8 | 2,414 | 0.5366–0.8614 | 706.2 | −0.13428 | 33.72 |
| 9 | 2,414 | 0.8617–1.6610 | 884.5 | −0.08749 | 33.93 |
| 10 | 2,415 | 1.6638–18.7758 | 1,746.6 | −0.28371 | 27.20 |

Correlations: Pearson `cost_r` vs `gross_r` **−0.0477**, Spearman **−0.1031** (ex past-stop);
on the raw pool −0.0450 / −0.1400.

**The mechanism.** Since the frozen spread is a per-symbol constant, `cost_r` inside a symbol is a
monotone function of `1 / risk_distance` and carries **no independent cost information at all**.
Measured Spearman(`cost_r`, `1/risk_distance`) per symbol:

`GBPUSD 1.0000 · SPX500 1.0000 · NAS100 1.0000 · JP225 1.0000 · EURJPY 0.9999 · CHFJPY 0.9999 ·
ETHUSD 0.9999 · NZDUSD 0.9997 · AUDUSD 0.9997 · UK100 0.9996 · GER40 0.9993 · EURGBP 0.9989 ·
AUDJPY 0.9989 · BTCUSD 0.9987 · USDCAD 0.9983 · GBPJPY 0.9982 · US30_cash 0.9978 · USDCHF 0.9966 ·
USDJPY 0.9690 · EURUSD 0.9639 · XAUUSD 0.9549 · XAGUSD 0.8775 · UKOIL 0.4033 · USOIL 0.3659`

Eighteen of twenty-four symbols are ≥ 0.9966 and four are exactly 1.0000.

The underlying signal is stop width, and it is real. Within-symbol tertiles of relative stop width
(`risk_distance / entry_price`), ex past-stop:

| tertile | n | gross | win % |
|---|---:|---:|---:|
| tightest | 8,057 | −0.13079 | 35.89 |
| middle | 8,047 | −0.10489 | 40.10 |
| widest | 8,038 | −0.07713 | 43.18 |

Within-symbol tertiles of `cost_r` give **−0.07127 / −0.11670 / −0.12496** — the same ordering,
because they are the same variable. The cross-tab is degenerate: the off-diagonal cells hold 11 to
547 rows against diagonal cells of 7,178 to 7,619 (`l5_RESIDUAL_V1.json` →
`cost_x_stopwidth_grid_within_symbol`), so **`cost_r` has no measurable residual signal once stop
width is held.**

### 3.2 The true cost is a WORSE predictor than the wrong one

Deciles of broker-true total cost, ex past-stop:

| decile | true cost per $1,000 risk | gross | win % |
|---:|---:|---:|---:|
| 1 | $35.1 | −0.03912 | 44.78 |
| 2 | $60.9 | −0.05727 | 43.33 |
| 3 | $85.3 | −0.16712 | 38.24 |
| 4 | $110.9 | −0.17209 | 39.31 |
| 5 | $138.6 | −0.12481 | 40.66 |
| 6 | $170.4 | **−0.02130** | 45.48 |
| 7 | $211.4 | −0.09877 | 40.18 |
| 8 | $280.3 | −0.07283 | 39.52 |
| 9 | $408.7 | −0.16297 | 33.55 |
| 10 | $988.5 | −0.12661 | 32.17 |

Non-monotone in gross (decile 6 is the second-best cell in the table), monotone only in win rate
44.78 % → 32.17 %.

> **The frozen cost model predicts outcome BETTER than the true one, because its numerator is a
> constant — it is a pure geometry proxy. Its predictive power is evidence that it is not measuring
> cost.**

Cost as bp of notional is flat across deciles 1–9 (−0.062 to −0.121) and only the top decile
(19.2–51.7 bp) separates at −0.23744.

### 3.3 REFUTED: the gate is not a leverage cap in disguise

Implied notional/balance leverage, ex past-stop: p50 **11.37×**, p75 59.59×, p90 2,900.64×,
p95 5,912.06×, max **69,110×**; **21.59 % of the tradeable pool implies more than 100× leverage** on
a $100,000 account and is not executable at the declared risk fraction — an unpriced constraint,
but not the gate's mechanism. A count-matched leverage cap (≤ 3.66×, admitting exactly the same
6,984 rows) overlaps the incumbent's admitted set at **Jaccard 0.2527** (2,818 of 6,984 shared), and
the leverage bands show no monotone outcome ordering (0–5× −0.0934, 300–1000× **+0.0306**,
>1000× −0.0875).

---

## 4. The rebuilt gate, measured (item 4)

All variants scored offline over the same population. `netTRUE` = `gross_r − broker_true_total_cost_r`.

### 4.1 Same thresholds, different cost model — ex `born_past_stop`, n = 24,142

| gate | n admitted | gross | fill-honest | **netTRUE** | ±SE | mean true $ |
|---|---:|---:|---:|---:|---:|---:|
| pool | 24,142 | −0.10429 | −0.12653 | −0.35333 | 0.00729 | 266.0 |
| **G0 incumbent** (frozen 0.10 / 0.15) | 6,984 | −0.08354 | −0.08003 | **−0.27604** | 0.01161 | 163.1 |
| G1 frozen, spread limb dropped (0.15 only) | 7,357 | −0.07071 | −0.06980 | −0.25753 | 0.01139 | 158.3 |
| **G2 broker-true, same 0.10 / 0.15** | **10,648** | −0.10154 | −0.11639 | **−0.18092** | 0.00906 | 94.5 |
| G3 broker-true, total only ≤ 0.15 | 11,756 | −0.11081 | −0.12761 | −0.19521 | 0.00878 | 94.3 |
| G4 broker-true, flat $150 ceiling | 12,578 | −0.10067 | −0.11809 | −0.22414 | 0.00916 | 67.2 |
| G5 broker-true ≤ 0.030 ($30 / $1k risk) | 676 | −0.04099 | −0.05142 | −0.06510 | 0.02843 | 19.7 |
| G6 broker-true ≤ 0.050 ($50 / $1k risk) | 2,607 | −0.05071 | −0.05714 | −0.08686 | 0.01610 | 29.2 |
| G7 frozen, flat $150 ceiling | 7,500 | −0.04959 | −0.05395 | −0.30587 | 0.01244 | 142.2 |

> **G0 → G2 is the headline repair: +0.09512 R/trade of net at broker truth AND +3,664 more
> admitted candidates (+52.5 %), from swapping the frozen cost model for the broker-true artifact
> the repository already ships. Nothing new is captured.** On the full pool the same swap is
> −0.30707 → −0.23370 (+0.07337) on 7,210 → 11,302 rows.

At the second truth source (`spread_model` at each candidate's own instant) the incumbent's net is
−0.24897 and the ≤ 0.15 broker-true-equivalent cell is −0.17935 → **+0.06962 R/trade**, so the
repair's sign and order of magnitude are stable across truth sources.

**Where the +0.09512 comes from, decomposed — and two caveats that must travel with it.**
Both cells are scored net of the same broker-true cost, so the gain splits exactly:

| | G0 incumbent | G2 broker-true | delta |
|---|---:|---:|---:|
| gross R/trade | −0.08354 | −0.10154 | **−0.01800** (worse trades) |
| true cost R/trade | 0.19250 | 0.07938 | **+0.11312** (cheaper trades) |
| netTRUE R/trade | −0.27604 | −0.18092 | +0.09512 |

**The entire gain is cost selection, and it is paid for with 0.018 R/trade of gross quality.** The
frozen gate is not picking bad trades — it is picking *expensive* ones: its admitted book carries
2.42× the true cost of the book the same thresholds select at broker truth.

Caveat 1 — this is partly definitional: G2 selects on low true cost and is then scored net of true
cost. It is the right instrument for "which gate delivers a better book", not evidence that any new
edge exists. Caveat 2 — **the per-trade improvement does not carry to the dollar total.** G2 admits
52.5 % more candidates, each still losing, so total net-true worsens from −$1,880,278 to
−$2,167,509. Both numbers are in the stack table in §6 and neither should be quoted without the
other.

### 4.2 Count-matched swap — what the money gate trades away

Holding the admitted count at exactly 6,984 and ranking by different quantities:

| ranking quantity | threshold | gross of admitted | swap-in (n) | swap-in gross | swap-out gross |
|---|---:|---:|---:|---:|---:|
| `cost_r` (frozen, total only) | 0.142908 | −0.07071 | 277 | **+0.22236** | −0.10109 |
| **`cost_usd` (flat dollar)** | **$137.71** | **−0.05050** | 2,114 | **+0.01164** | −0.09751 |
| `true_total_cost_r` | 0.095136 | −0.08314 | 3,601 | −0.08363 | −0.08441 |
| `true_total_cost_usd` | $66.72 | −0.10371 | 5,093 | −0.11490 | −0.08723 |
| widest relative stop | 0.001918 | −0.07918 | 3,190 | −0.08033 | −0.08987 |
| incumbent (reference) | — | −0.08354 | — | — | — |

**A flat dollar ceiling beats the flat R ceiling by +0.03304 R/trade on an identical admitted
count.** The 2,114 rows it swaps in cost $90.71 each and are gross **+0.01164**; the 2,114 it swaps
out cost $219.29 each and are **−0.09751** — a **0.10915 R/trade** difference across 30.3 % of the
admitted book.

### 4.3 The concrete rule

```
# offline scorer, docs/audits/.../phase19/receipts/discovery/l5_finalgate.py
ADMIT iff  broker_true_total_cost_usd <= CEILING_USD * (risk_usd / 1000)
           where broker_true_total_cost_usd =
               spread_price(symbol, account, decision_time_utc, band="mid")   # src/costs/spread_model.py
             + commission_usd_per_lot(symbol, entry_price)                    # src/costs/model.py
             + 0.003 R slippage                                              # BROKER_TRUE_COSTS_V1_1 measured
             + swap                                                          # unchanged
           scaled by lots = risk_usd / (risk_distance * usd_per_price_unit_per_lot)
and the separate spread limb is DELETED.
```

Three changes, each independently measured above: (a) broker-true numerator instead of the frozen
per-symbol constant (+0.09512 R/trade), (b) no separate spread cap — the 373 rows it exclusively
refuses are +0.08886 net-true, and folding them into the incumbent book is exactly the measured G1
row: n 6,984 → 7,357, netTRUE **−0.27604 → −0.25753, +0.01851 R/trade** (independently reproduced
by the closed form `(6984×−0.27604 + 373×0.08886)/7357 = −0.25754`), (c) the ceiling set on the
measured curve rather than at 0.15.

---

## 5. The right ceiling, in dollars, for a $1,000-risk trade (item 5)

Sweep of the broker-true ceiling, ex `born_past_stop`. `netTRUE` and `fhNetTRUE` (fill-honest
outcome minus true cost) are the two honest bottom lines.

| ceiling per $1,000 risk | n | gross | fill-honest | **netTRUE** | ±SE | fhNetTRUE |
|---:|---:|---:|---:|---:|---:|---:|
| $10 | 18 | +0.31835 | +0.22465 | +0.31016 | — | +0.21646 |
| $15 | 66 | +0.06765 | +0.08160 | +0.05643 | — | +0.07039 |
| **$20** | **122** | +0.04930 | +0.06508 | **+0.03507** | 0.0734 | +0.05085 |
| **$25** | **274** | +0.04040 | +0.02600 | **+0.02150** | 0.0481 | +0.00709 |
| **$30** | **676** | −0.04099 | −0.05142 | **−0.06510** | 0.0284 | −0.07552 |
| $35 | 1,025 | −0.07945 | −0.08052 | −0.10645 | — | −0.10752 |
| $40 | 1,578 | −0.06009 | −0.06652 | −0.09081 | 0.0191 | −0.09725 |
| $50 | 2,607 | −0.05071 | −0.05714 | −0.08686 | 0.0161 | −0.09329 |
| $75 | 4,503 | −0.03938 | −0.05443 | −0.08568 | — | −0.10072 |
| $100 | 7,449 | −0.09223 | −0.11259 | −0.15374 | 0.0105 | −0.17410 |
| **$150 (incumbent)** | **11,756** | −0.11081 | −0.12761 | **−0.19521** | 0.0088 | −0.21201 |
| $200 | 15,137 | −0.09432 | −0.10777 | −0.19854 | — | −0.21199 |
| $250 | 17,287 | −0.09286 | −0.10903 | −0.21182 | — | −0.22799 |

Reproduced independently at `spread_model` truth (`l5_SMTRUTH_V1.json` → `stack_sm`): $20 → +0.0402
(n=121), $25 → +0.0247 (n=284), $30 → −0.0540 (n=660), $50 → −0.0950 (n=2,871), $150 → −0.1794
(n=11,927). Band sensitivity at the $50 cell is negligible: mid −0.09495, low-band −0.09352,
high-band −0.08251.

> **Answer: about $25–30 of all-in cost per $1,000 of risk — 2.5–3 % of the money at stake.
> The incumbent gate permits $150 (and $300 on a 2 %-risk candidate). It is 5–6× too loose.**

Two qualifications stated plainly:

1. **The positive cells are not significant.** At $25 the net is +0.0215 with SE 0.0481 (0.45 SE)
   and n = 274 of 24,142 (**1.13 %**). At $20, +0.0351 ± 0.0734. What is robust is the *shape* —
   the curve crosses zero between $25 and $30 on both truth sources and on both outcome columns —
   not the level of the positive tail.
2. **No ceiling makes the pool positive at scale.** The best cell with n > 2,000 is $50 at
   −0.0869 netTRUE. A ceiling that recovers a positive book keeps ~1 % of what the generator emits.

### 5.1 Which instruments are affordable at all

Broker-true cost per $1,000 of risk, ex past-stop (`l5_PERSYMBOL_V1.json`):

| symbol | n | true $/1k | frozen $/1k | charge error | gross | **netTRUE** | ±SE |
|---|---:|---:|---:|---:|---:|---:|---:|
| NAS100 | 1,483 | 100.14 | 2,307.81 | 23.05× | −0.28422 | −0.38436 | 0.0261 |
| GER40 | 1,400 | 100.66 | 322.90 | 3.21× | −0.00300 | **−0.10366** | 0.0328 |
| XAUUSD | 2,329 | 108.77 | 95.77 | 0.88× | −0.07644 | −0.18522 | 0.0184 |
| US30_cash | 1,478 | 118.54 | 367.77 | 3.10× | −0.15670 | −0.27524 | 0.0288 |
| EURUSD | 728 | 151.33 | 175.40 | 1.16× | −0.11533 | −0.26667 | 0.0320 |
| XAGUSD | 925 | 152.26 | 131.54 | 0.86× | −0.11174 | −0.26400 | 0.0290 |
| SPX500 | 1,717 | 167.71 | 2,379.24 | 14.19× | −0.10986 | −0.27756 | 0.0265 |
| GBPUSD | 823 | 190.38 | 290.02 | 1.52× | −0.16031 | −0.35069 | 0.0406 |
| UK100 | 1,412 | 190.98 | 914.78 | 4.79× | −0.18544 | −0.37642 | 0.0305 |
| JP225 | 1,283 | 194.79 | 894.77 | 4.59× | −0.04777 | −0.24257 | 0.0323 |
| USDJPY | 892 | 210.20 | 285.26 | 1.36× | −0.09344 | −0.30363 | 0.0289 |
| AUDUSD | 612 | 234.89 | 255.02 | 1.09× | −0.02785 | −0.26274 | 0.0460 |
| EURJPY | 628 | 242.90 | 660.69 | 2.72× | −0.02326 | −0.26616 | 0.0456 |
| USDCHF | 774 | 250.60 | 254.60 | 1.02× | **+0.01175** | −0.23885 | 0.0427 |
| CHFJPY | 575 | 251.44 | 529.96 | 2.11× | −0.07553 | −0.32697 | 0.0472 |
| USDCAD | 798 | 284.54 | 297.63 | 1.05× | −0.17702 | −0.46156 | 0.0399 |
| GBPJPY | 689 | 287.47 | 281.44 | 0.98× | −0.08031 | −0.36778 | 0.0459 |
| ETHUSD | 916 | 308.00 | 1,301.44 | 4.23× | −0.17422 | −0.48222 | 0.0370 |
| AUDJPY | 640 | 312.11 | 304.32 | 0.98× | −0.08724 | −0.39935 | 0.0448 |
| NZDUSD | 737 | 342.05 | 436.92 | 1.28× | −0.04570 | −0.38774 | 0.0442 |
| EURGBP | 666 | 358.04 | 440.54 | 1.23× | −0.12372 | −0.48176 | 0.0459 |
| BTCUSD | 1,177 | 361.68 | 363.35 | 1.01× | −0.02836 | −0.39004 | 0.0336 |
| **UKOIL_cash** | 735 | **972.69** | 94.86 | 0.098× | −0.05181 | **−1.02450** | 0.0537 |
| **USOIL_cash** | 725 | **991.24** | 107.86 | 0.109× | −0.14143 | **−1.13266** | 0.0526 |

> **The oil book costs 97–99 % of the money it risks.** The generator emits stops on UKOIL/USOIL of
> the same order as the quoted spread, and the frozen model charges them at one tenth of truth — so
> the gate lets almost all of them through. 1,142 of the 1,835 harmful admissions are these two
> symbols. Nothing in the estate has ever priced them at broker truth.

**Not one of 24 symbols is net-positive at broker truth.** The least-bad is GER40 at −0.1037.

---

## 6. The stacked repair, end to end

Ex `born_past_stop` throughout except row A/B (`l5_STACK_V1.json`).

| step | n | gross | fill-honest | netTRUE | ±SE | mean true $ | net-true $ total |
|---|---:|---:|---:|---:|---:|---:|---:|
| A pool as shipped | 27,658 | −0.21750 | −0.23672 | −0.46412 | 0.0066 | 278.4 | −15,428,344 |
| B incumbent gate | 7,210 | −0.11185 | −0.10762 | −0.30707 | 0.0115 | 165.7 | −2,251,607 |
| C + drop `born_past_stop` | 6,984 | −0.08354 | −0.08003 | −0.27604 | 0.0116 | 163.1 | −1,880,278 |
| D + broker-true cost @ 0.10/0.15 | 10,648 | −0.10154 | −0.11639 | −0.18092 | 0.0091 | 94.5 | −2,167,509 |
| E + drop the spread limb | 11,756 | −0.11081 | −0.12761 | −0.19521 | 0.0088 | 94.3 | −2,404,836 |
| F ceiling $50 / $1k risk | 2,607 | −0.05071 | −0.05714 | −0.08686 | 0.0161 | 29.2 | −174,151 |
| F ceiling $30 / $1k risk | 676 | −0.04099 | −0.05142 | −0.06510 | 0.0284 | 19.7 | −37,163 |
| F ceiling $25 / $1k risk | 274 | +0.04040 | +0.02600 | **+0.02150** | 0.0481 | 17.5 | +1,379 |

Family composition at ≤ $50 per $1,000 risk (n = 2,607):

| family | n | gross ± SE | netTRUE | fhNetTRUE | win % |
|---|---:|---:|---:|---:|---:|
| **cross_asset_lead_lag** | **65** | **+0.25622 ± 0.1388** | **+0.21909** | **+0.14053** | **56.92** |
| liquidity_sweep_reclaim | 233 | −0.01570 ± 0.0649 | −0.05259 | −0.08950 | 44.64 |
| session_open_range_break | 143 | −0.01539 ± 0.0691 | −0.04993 | −0.06969 | 45.45 |
| regime_transition_break | 133 | −0.02786 ± 0.0481 | −0.06279 | −0.08066 | 45.86 |
| volatility_compression_expansion | 227 | −0.03840 ± 0.0343 | −0.07291 | −0.07701 | 48.02 |
| displacement_continuation | 651 | −0.04432 ± 0.0362 | −0.08000 | −0.09756 | 41.78 |
| current_fvg_fill | 993 | −0.06020 ± 0.0238 | −0.09682 | −0.07876 | 44.21 |
| current_ob_retest | 91 | −0.22342 ± 0.0769 | −0.26234 | −0.27969 | 41.76 |
| current_breaker_re_entry | 69 | −0.28441 ± 0.1293 | −0.32177 | −0.34862 | 31.88 |

Symbol composition at the same ceiling: XAUUSD 631 (netTRUE −0.0653), NAS100 458 (−0.2065),
GER40 371 (**−0.0242**), SPX500 368 (−0.0911), US30_cash 323 (−0.0522), XAGUSD 127
(**+0.0030**, fhNetTRUE **+0.0712**), EURUSD 83 (−0.0286), UK100 65 (−0.0296), JP225 61 (−0.0748).

---

## 7. Candidate IDs cited

Spread-limb-only refusals (the +0.169 gross / +0.089 net-true cohort), first eight as emitted:
`broadorigin_1c86ff14cca8da89ce29c890`, `broadorigin_438c5b07c0d1ea96334b2aa5`,
`broadorigin_d5bf5f2656b204f1afb709bd`, `broadorigin_531c69fe53bc7cf16fc2776e`,
`broadorigin_3ac2d7a5c7a1257ed52ffe98`, `broadorigin_eef128439a847b2748707241`,
`broadorigin_8fe278eae1a43592b4b9008a`, `broadorigin_aec7c0f92c18759ebe48ef22`
— source `l5_PERSYMBOL_V1.json` →
`spread_limb_only_refusals_EX_PAST_STOP.example_candidate_ids`. The full 373 are reproducible in
one line from `l5_MONEY_TABLE.jsonl.gz` with `spread_r > 0.10 and cost_r <= 0.15` (note
`candidate_id` alone is not a primary key — W0-F1; join on `(candidate_id, decision_time_utc)`).

## 8. Artifacts

| file | what |
|---|---|
| `l5_MONEY_TABLE.jsonl.gz` | 27,658 rows × 52 cols — lots, notional, cost in price units and USD, broker-true cost, per-row |
| `l5_MONEY_TABLE_SM.jsonl.gz` | same + `sm_*` columns from `src/costs/spread_model.py` at each candidate's own instant, with low/mid/high band |
| `l5_money_build.py` / `l5_smtruth.py` | the two builders |
| `l5_MONEY_SUMMARY_V1.json` / `l5_money_summary.py` | distributions, per-symbol overcharge, per-risk-bucket |
| `l5_PREDICT_V1.json` / `l5_predict.py` | spread constancy, cost deciles, correlations |
| `l5_RESIDUAL_V1.json` / `l5_residual.py` | cost-vs-stop-width identity, cross-tab, per-symbol Spearman |
| `l5_GATES_V1.json` / `l5_gates.py` | 2×2 frozen×true, count-matched alternatives, dollar sweeps |
| `l5_DECOMPOSE_V1.json` / `l5_decompose.py` | refusal anatomy by limb, by truth, by dollar, by risk bucket |
| `l5_FINALGATE_V1.json` / `l5_finalgate.py` | G0–G7 gate variants, harmful/missed admission census |
| `l5_PERSYMBOL_V1.json` / `l5_persymbol.py` | affordability table, commission fidelity, slippage, spread-limb cohort |
| `l5_LEVERAGE_V1.json` / `l5_leverage.py` | leverage hypothesis (refuted), dollar charge error |
| `l5_STACK_V1.json` / `l5_stack.py` | the stacked repair, per-family and per-symbol |
| `l5_SMTRUTH_V1.json` | second truth source, band sensitivity |
| `l5_SPREADMODEL_CHECK_V1.json` | 13-symbol spot check of `spread_model` at 2026-01-15 14:00Z |
| `l5_RESULT.json` | all of the above merged |
