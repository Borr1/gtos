# f1 — WHAT IS ACTUALLY TRUE, ON THE CORRECT POPULATION

Lane f1, wave 19. Everything below is measured on this machine over the **whole** population of
**eight** open windows — **1,118,694 candidate emissions** (98.0 % of the sealed 1,141,640), **331,548 honest fills**, **552 selected
candidates**, **507 executed trades** — Oct/Nov/Dec 2025 and Jan/Feb/Mar/Apr/May 2026.
**Nothing is sampled anywhere.** The three READ-RESTRICTED windows (june/august/september 2025) were
not opened, not counted, and not referenced.

Machine-readable: `f1_BASELINE_V1.json` (this directory) — the canonical baseline other lanes read.
Code: `f1_*.py` in this directory (dependency order in §8). Per-row evidence: `f1_rows/`.
The roster harness is Session PB's `receipts/pbg/pbg_run.py --min-rr 1.5` with `--minutes` empty
(= close-only), run here for the five windows PB had not built.

**Verdict axis, for the wave's tally.** §4 (the population's gross ≈ 0) is **SIGNAL**. §4.2 (one
family born past its own stop) is **SIGNAL** and repairable. §4.3 (the toll is 21× the deficit and
is set by the generator's own stop width) is **USAGE**. §3 and §5 (the selector/management stack)
are **USAGE**, and they come out **positive** — which is the finding that reframes the question.

---

## 0. THE ANSWER, IN SIX SENTENCES

**The taken set had never been looked at, and it is not what the estate believes.** Across eight
windows the broad V4 system selected **552 of 1,141,640 candidates (0.0484 %)** and executed **507
trades**; on the 464 with a terminal R it books **gross +0.05505 R/trade** and **net −0.01932
R/trade** (t = −0.403, CI95 [−0.11246, +0.07454]) — statistically indistinguishable from zero, on
its own arm's cost model, over eight months.

**On the correct population — the generator's own roster, not the 18 % counterfactual pool — the
signal is not negative, it is ZERO.** 331,548 honest fills book gross **−0.08233 R/trade**; strip
the one structurally defective family and gross is **−0.01327 R/trade** on 298,537 fills, a win rate
of **37.98 %** against its own payoff-implied breakeven of **38.55 %** — short by **0.57 percentage
points**, and the per-window gross runs −0.035 … **+0.019** with April 2026 positive.

**The broker toll on that same population is +0.28118 R/trade — 21× the size of the gross deficit
— and no risk-distance band, no family and no month gets it below the gross.** That is the
mechanism, and it is a USAGE mechanism: the toll in R is `cost_price ÷ risk_distance`, and the
generator's median risk distance is **9.3 bps** against a ~2.5–3 bps round-trip.

---

## 1. THE THREE POPULATIONS — sizes, and how the split is decided

Every sealed S0R0 arm writes exactly three things. The split is **not** a research choice; it is the
engine's own, and it happens at two places:

1. **selected vs missed** — `candidate_rows − missed_opportunity_rows`. A candidate that survives
   selector admission, risk finalisation and order materialisation becomes an order; everything else
   is written to the missed-opportunity ledger.
2. **missed → pool** — the *scoreability gate*,
   `missed_opportunity_scoreability_fields` (`v4_timewarp_simulated_live_research_loop.py:28107-28160`).
   A missed row enters the diagnostic pool only when `not headline_r_scoreable` **and**
   `opportunity_net_proxy_r is not None` **and** it is cost- or diagnostic-scoreable. All 27,658
   January pool rows carry `missed_opportunity_r_scoreability_status =
   "diagnostic_opportunity_r_scoreable"` — **the pool is one branch of a three-way status field.**

| window | candidates (roster) | missed | **selected** | orders | **trades** | pool (scoreable missed) | pool as % of roster | selection rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025-10 | 174,479 | 174,382 | 97 | 194 | 86 | 29,192 | 16.73 % | 0.0556 % |
| 2025-11 | 151,190 | 151,131 | 59 | 118 | 58 | 26,374 | 17.44 % | 0.0390 % |
| 2025-12 | 136,141 | 136,093 | 48 | 96 | 47 | 22,973 | 16.88 % | 0.0353 % |
| 2026-01 | 153,486 | 153,425 | 61 | 122 | 57 | 27,658 | 18.02 % | 0.0397 % |
| 2026-02 | 129,231 | 129,165 | 66 | 132 | 58 | 24,239 | 18.76 % | 0.0511 % |
| 2026-03 | 130,124 | 130,004 | 120 | 240 | 110 | (not built) | — | 0.0922 % |
| 2026-04 | 134,489 | 134,443 | 46 | 92 | 40 | 25,056 | 18.63 % | 0.0342 % |
| 2026-05 | 132,500 | 132,445 | 55 | 110 | 51 | 21,285 | 16.06 % | 0.0415 % |
| **TOTAL** | **1,141,640** | **1,141,088** | **552** | **1,104** | **507** | **176,777** | **~17.5 %** | **0.0484 %** |

Sources: `CJ_RECLOCKED_ARM_S0R0_V7.json`, `CP_FEBRUARY_ARM_S0R0_V1.json`, `FA2_M_R0_RECEIPT.json`,
`CS_APRIL_S0R0_ARM_V1.json`, `CS_MAY_S0R0_ARM_V1.json`, `LP_{OCT,NOV,DEC}_2025_S0R0_RECEIPT.json`
→ `receipt_counts`; trades from each arm's `LANE_TRADE_TABLE.jsonl` / `*_TRADE_LEDGER.jsonl`.

**Three things follow immediately.**

- **The system takes 0.048 % of what it generates.** ~60 trades a month, of which 54 % are XAUUSD
  (274 of 507) and which touch only **11 of 24** instruments.
- **`order_rows ≈ 2 × trade_rows` in every window** (1,104 / 507 = 2.18) — orders are the lifecycle
  rows, not distinct opportunities.
- **The pool everyone analysed is ~17.5 % of the roster and 100 % counterfactual** — confirming
  Session PB. It is neither the population nor the system's footprint.

### 1.1 The join proves the roster reproduction reaches the taken set

All **57** January taken trades match Session PB's regenerated close-only roster on
`(candidate_id, decision_time_utc)` — **57/57 exact**, and **57/57 identical stop price**. Entry
matches on 39/57 and the target on **0/57**: the generator sets the **stop**, the downstream
`momentum_exhaustion` geometry policy re-writes the **target** from `min_rr` 1.5 to 2.0. So
roster / pool / taken are geometry-comparable on the risk denominator by construction.

---

## 2. THE CONTRACT — one walker, three populations, verified against sealed evidence

| contract | rule | verification |
|---|---|---|
| **C0 MARKET** | fill at the close of the last M1 bar strictly before the decision instant | reproduces the sealed sidecar's `plain_walk_r` on January's 27,658 rows: **+0.040332 vs +0.040897**, mean\|diff\| **0.001154**, **99.88 %** within 0.01 R |
| **C1 HONEST LIMIT** *(canonical)* | every candidate rests at its own entry; a LONG fills when an M1 low ≤ entry, a SHORT when an M1 high ≥ entry (gaps through fill); walk starts on the NEXT bar; never touched inside 120 bars → 0.0 R, no cost | reproduces the sealed `fill_honest_walk_r` census: mine **−0.20556** vs sealed **−0.23672**, mean\|diff\| 0.0606, 74.6 % within 0.01 R; exits stop 15,636 / 4,042 target / 85 no-fill vs sealed 15,852 / 3,713 / 241. Residual = M1 OHLC vs the sealed tick-ordered sidecar. |

Both use target = 2.0R (the policy target; 1.5R is also carried in the JSON), the candidate's own
stop, 120 M1 bars, conservative tie (stop wins inside a bar), mark to market at the wall. Cost is
the h1 four-term broker-true, hour-aware basis, charged once in price units and divided by that
row's own risk distance — **charged only on filled rows**.

> **Do not walk the roster at C0.** Walking POI limit candidates as market orders manufactures
> **+1.54 R/trade** of phantom edge (Jan roster, C0, 86.7 % "win rate") because it credits the
> unfilled move to the limit level. The pool hides this — its entries sit near the market, so its
> C0 number is only +0.040. **This is why `plain_walk_r` is safe on the pool and lethal on the
> roster.**

---

## 3. THE TAKEN SET — the first time anyone has seen it

Realised, on the arm's own policy and the arm's own cost model. Rows with `final_r = null`
(`entry_fill_executable_terminal_r_ordered_tick_sequence_required`, 43 of 507) are excluded from
means and counted separately.

| window | trades | scored | gross | cost | **net** | win rate | payoff | breakeven | **gap** | net total R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025-10 | 86 | 82 | +0.0861 | 0.0740 | **+0.0122** | 0.5000 | 1.204 | 0.4537 | **+0.0463** | +1.00 |
| 2025-11 | 58 | 56 | +0.2741 | 0.0709 | **+0.2032** | 0.6071 | 1.160 | 0.4631 | **+0.1441** | +11.38 |
| 2025-12 | 47 | 42 | −0.2109 | 0.0726 | **−0.2835** | 0.3333 | 1.242 | 0.4459 | −0.1126 | −11.91 |
| 2026-01 | 57 | 55 | −0.0222 | 0.0779 | **−0.1001** | 0.4182 | 1.328 | 0.4295 | −0.0113 | −5.51 |
| 2026-02 | 58 | 58 | +0.0035 | 0.0718 | **−0.0683** | 0.4310 | 1.333 | 0.4287 | +0.0023 | −3.96 |
| 2026-03 | 110 | 100 | +0.1523 | 0.0791 | **+0.0732** | 0.4900 | 1.446 | 0.4088 | **+0.0812** | +7.32 |
| 2026-04 | 40 | 36 | +0.1618 | 0.0783 | **+0.0834** | 0.6111 | 1.014 | 0.4966 | **+0.1146** | +3.00 |
| 2026-05 | 51 | 35 | −0.2300 | 0.0641 | **−0.2941** | 0.3143 | 1.275 | 0.4396 | −0.1253 | −10.29 |
| **POOLED** | **507** | **464** | **+0.05505** | **0.07437** | **−0.01932** | **0.4720** | **1.2662** | **0.4413** | **+0.0307** | **−8.96** |

Pooled significance: gross se 0.0478, **t +1.151**, CI95 [−0.03840, +0.14859], p(≤0) 0.1270.
Net se 0.0479, **t −0.403**, CI95 [−0.11246, +0.07454], p(≤0) 0.6558.
Total book: **−8.96 R over eight months = −0.896 % of account** at the arm's 0.1 % risk unit.

**Read the gap column.** On GROSS the taken set **beats** its own payoff-implied breakeven by
**+3.07 pp** (47.20 % actual vs 44.13 % needed). On NET it falls **0.0107** short. **The taken set
is a coin flip that pays a small toll** — it is not the −0.2175 catastrophe the estate publishes.

Close reasons across all 507: `stop_loss` 107, `giveback_close` 97, `path_end_mark_to_market` 82,
`time_stop_close_mark_from_m1` 73, `stop_reached_before_target` 59, unresolved 43,
`target_reached_before_stop` 36, `final_target` 10. **`born past stop`: 0 of 507, in every window.**

---

## 4. THE CORRECT POPULATION — the roster, eight windows, whole

C1, target 2.0R, h1 broker-true cost. "CLEAN" = filled, minus rows born already past their stop,
minus the `current_breaker_re_entry` family (§4.2 shows these are the same defect).

| window | emissions | fill rate | fills | gross | cost | net | CLEAN n | CLEAN gross | CLEAN net | CLEAN wr | breakeven | **gap** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2025-10 | 169,624 | 0.2728 | 46,270 | −0.09158 | 0.30280 | −0.39437 | 41,350 | −0.02282 | −0.33088 | 0.3782 | 0.3879 | −0.0097 |
| 2025-11 | 147,120 | 0.2844 | 41,840 | −0.12427 | 0.27922 | −0.40349 | 36,762 | −0.03549 | −0.31645 | 0.3677 | 0.3825 | −0.0149 |
| 2025-12 | 134,298 | 0.2683 | 36,026 | −0.08858 | 0.33209 | −0.42067 | 32,054 | −0.00707 | −0.33787 | 0.3825 | 0.3855 | −0.0030 |
| 2026-01 | 151,002 | 0.2909 | 43,922 | −0.08763 | 0.30891 | −0.39654 | 38,983 | −0.00467 | −0.31691 | 0.3833 | 0.3853 | −0.0020 |
| 2026-02 | 126,931 | 0.3090 | 39,225 | −0.06099 | 0.24080 | −0.30179 | 36,357 | −0.01373 | −0.25585 | 0.3789 | 0.3848 | −0.0059 |
| 2026-03 | 127,932 | 0.3524 | 45,082 | −0.06263 | 0.19541 | −0.25804 | 42,365 | −0.03133 | −0.22745 | 0.3731 | 0.3867 | −0.0135 |
| 2026-04 | 132,137 | 0.3109 | 41,084 | −0.06206 | 0.28303 | −0.34509 | 36,702 | **+0.01891** | −0.26174 | 0.3896 | 0.3815 | **+0.0082** |
| 2026-05 | 129,650 | 0.2939 | 38,099 | −0.08018 | 0.31353 | −0.39371 | 33,964 | −0.00507 | −0.31979 | 0.3869 | 0.3890 | −0.0022 |
| **POOLED 8** | **1,118,694** | **0.2964** | **331,548** | **−0.08233** | **0.28066** | **−0.36299** | **298,537** | **−0.01327** | **−0.29445** | **0.3798** | **0.3855** | **−0.0057** |

(Each roster is **restricted to that arm's own trading-day set** — taken from the arm's pool for the
seven windows that have one, from the roster's own 22 days for March, whose scorecard is 2,112 = 22 × 96.
That drops the 4 Christmas-week days, 2 Easter days and 3 May holidays the sealed arms skipped;
it moves the pooled clean gross by 0.0003 R. Close-only regeneration then recovers **98.0 %** of the
sealed `candidate_rows` in total; PB's exact-key match against the sealed rosters is **99.82 %** for
both January and February and my walk drops a further ~1.7 % at tape boundaries.)

**Per-emission (including the 70.4 % that never fill): gross −0.02440, cost 0.08318, net −0.10758.**

### 4.1 The signal, stated exactly

On the clean population the family needs a **38.55 %** win rate at its realised 1.5943:1 payoff and
gets **37.98 %**. **It is 0.57 percentage points short.** Per window that deficit runs
−1.49 pp … **+0.82 pp**. That is not a dead signal; it is a **zero** signal, and it is stable
across eight consecutive months and 298,537 honest fills.

### 4.2 The one defect that produced the entire published catastrophe

| family | emissions | fill rate | fills | gross | cost | net | gap | median d (bps) | born past stop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`current_breaker_re_entry`** | 88,323 | 0.370 | **32,668** | **−0.70463** | 0.27724 | −0.98187 | −0.3137 | 6.13 | **0.680** |
| `volatility_compression_expansion` | 4,987 | 0.991 | 4,940 | −0.03992 | 0.08463 | −0.12455 | −0.0479 | 34.33 | 0.000 |
| `current_ob_retest` | 249,376 | 0.071 | 17,809 | −0.02247 | 0.17216 | −0.19463 | −0.0120 | 10.68 | 0.019 |
| `current_fvg_fill` | 645,192 | 0.227 | 146,565 | −0.02200 | 0.26656 | −0.28855 | −0.0088 | 8.68 | 0.000 |
| `cross_asset_lead_lag` | 20,052 | 0.987 | 19,787 | −0.01934 | 0.45053 | −0.46987 | −0.0070 | 6.21 | 0.000 |
| `regime_transition_break` | 2,216 | 0.995 | 2,205 | −0.01142 | 0.05474 | −0.06615 | −0.0128 | 44.30 | 0.000 |
| `session_open_range_break` | 7,855 | 0.992 | 7,795 | −0.00996 | 0.08901 | −0.09896 | −0.0063 | 18.12 | 0.000 |
| `displacement_continuation` | 36,929 | 0.992 | 36,644 | −0.00645 | 0.14843 | −0.15488 | −0.0035 | 16.80 | 0.000 |
| `liquidity_sweep_reclaim` | 41,152 | 0.991 | 40,774 | **+0.00273** | 0.29879 | −0.29606 | +0.0011 | 7.93 | 0.000 |
| `structural_distance_extreme` | 22,612 | 0.989 | 22,361 | **+0.00687** | 0.63022 | −0.62335 | +0.0023 | 3.17 | 0.000 |

**Nine of ten families sit inside −0.040 … +0.007 R/trade gross. One sits at −0.705.** And the two
"defects" the estate tracks separately are one defect:

- **98.48 %** of born-past-stop filled rows are `current_breaker_re_entry`.
- **68.01 %** of `current_breaker_re_entry` fills are born past their stop, booking ≈ **−0.998**.
- Removing **either** takes the roster's gross from −0.0823 to ≈ **−0.018**; removing both gives
  **−0.0133**. They are not additive because they are the same rows.

`current_breaker_re_entry` contributes **−0.0613 of the roster's −0.0823 gross (74 %)** on **9.85 %** of
the fills. This is the family CQ's V27 "inverted-breaker" candidate is built on; L7 already measured
that its +11.9 R/trade is the fill-blind convention and that at market or with an honest fill it is
**zero**. This lane's independent measurement agrees and localises the reason: the candidates are
born dead.

### 4.3 The risk-distance surface — the whole lever, and its ceiling

Clean population, 8 windows, deciles of risk distance in bps of entry price:

| decile | d (bps) | n | gross | cost | net | win rate | payoff | breakeven | gap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.32–2.89 | 29,854 | +0.00745 | **0.72996** | −0.72251 | 0.3421 | 1.9448 | 0.3396 | +0.0026 |
| 2 | 2.89–4.26 | 29,854 | −0.00244 | 0.37061 | −0.37305 | 0.3510 | 1.8421 | 0.3519 | −0.0009 |
| 3 | 4.26–5.66 | 29,853 | +0.00548 | 0.27610 | −0.27062 | 0.3620 | 1.7784 | 0.3599 | +0.0021 |
| 4 | 5.66–7.26 | 29,854 | −0.00915 | 0.24936 | −0.25851 | 0.3675 | 1.6949 | 0.3711 | −0.0036 |
| 5 | 7.26–9.28 | 29,853 | −0.03053 | 0.23004 | −0.26058 | 0.3714 | 1.6048 | 0.3839 | −0.0126 |
| 6 | 9.28–11.95 | 29,854 | −0.01414 | 0.22917 | −0.24331 | 0.3824 | 1.5744 | 0.3884 | −0.0060 |
| 7 | 11.95–15.97 | 29,854 | −0.01982 | 0.23417 | −0.25399 | 0.3879 | 1.5203 | 0.3968 | −0.0089 |
| 8 | 15.97–23.27 | 29,853 | −0.00532 | 0.22217 | −0.22749 | 0.3988 | 1.4924 | 0.4012 | −0.0025 |
| 9 | 23.27–41.56 | 29,854 | −0.02352 | 0.17208 | −0.19560 | 0.4077 | 1.3825 | 0.4197 | −0.0120 |
| 10 | 41.56–1624 | 29,854 | −0.04069 | 0.09818 | **−0.13887** | 0.4272 | 1.2022 | 0.4541 | −0.0269 |

**Three readings, all load-bearing.**

1. **Cost falls 7.4× across the surface (0.730 → 0.098 R) while gross stays inside a ±0.04 band.**
   Cost is a *pure* function of geometry; gross is not a function of geometry at all.
2. **The tightest decile pays 73.0 % of its risk unit to the broker.** A candidate with a 2 bps stop
   cannot be traded by anyone at any skill level.
3. **No decile is net-positive, and the best net (−0.139) is at the widest.** Pushing past the
   deciles, on the same 8-window clean population: d ≥ 50 bps → n 23,569, gross −0.0375, cost 0.0887,
   **net −0.1262**; d ≥ 75 bps → n 13,354, **net −0.1128** (the floor); d ≥ 150 bps → gross **−0.0987**,
   net −0.1398; d ≥ 300 bps → gross **−0.1840**, net −0.2064. **Gross deteriorates faster than cost
   falls past ~75 bps** — widening runs out of road before the toll runs out.

**What would have to be true.** The population's best gross cell is **+0.00745 R/trade** (decile 1,
0.3–2.9 bps) and it pays **0.730 R** of toll; the best net cell pays **0.098 R** for **−0.041** of
gross. To break even at any cell the toll must fall to ≤ the cell's gross — a **20×–98×** reduction —
or, equivalently, an unchanged ~2.5–3 bps round trip needs a risk distance of **≈ 300–500 bps while
gross holds at +0.01**, and the measurement says gross at d ≥ 300 bps is **−0.184** on 1,098 fills.
**There is no cell where this closes.**

---

## 5. SIGNAL OR USAGE — the decomposition, on one contract

All rows below are the SAME contract (C1, 2.0R, 120 bars, h1 broker-true cost).

| population | n | gross | cost | net | what it isolates |
|---|---:|---:|---:|---:|---|
| ROSTER, all emissions (8 win) | 1,118,694 | −0.02440 | 0.08318 | −0.10758 | the family as generated |
| ROSTER, honest fills | 331,548 | −0.08233 | 0.28066 | −0.36299 | the family as tradeable |
| ROSTER, fills, CLEAN | 298,537 | **−0.01327** | 0.28118 | −0.29445 | **the SIGNAL** |
| POOL (declined & scoreable, 7 win) | 176,777 | −0.20543 | 0.25980 | −0.46523 | what the system rejected (wr 0.3203, payoff 1.3952, be 0.4175) |
| TAKEN, same plain contract | 507 | +0.03183 | 0.14844 | −0.11661 | **what SELECTION picks** |
| TAKEN, realised (arm policy + arm cost) | 464 | **+0.05505** | 0.07437 | **−0.01932** | **selection + management + arm cost** |

**Decomposition of the clean net (−0.29445 R/trade):**
`signal −0.01327` (**4.5 %**) + `broker toll −0.28118` (**95.5 %**).

**Is the selection real?** Matched controls, same window, same symbol, risk distance within ±25 %,
≥ 5 controls, bootstrap 8,000:

| comparison | n | taken gross | control gross | **Δ** | CI95 | p(≤0) |
|---|---:|---:|---:|---:|---|---:|
| TAKEN vs **POOL** (the declined set) | 396 | +0.04357 | −0.10604 | **+0.14961** | [+0.03964, +0.26157] | **0.0027** |
| TAKEN vs POOL, + same family | 359 | +0.06368 | −0.09740 | **+0.16107** | [+0.03899, +0.28532] | **0.0050** |
| TAKEN vs **ROSTER** (whole population) | 397 | +0.04498 | −0.04302 | +0.08800 | [−0.02279, +0.20079] | 0.0601 |
| TAKEN vs ROSTER, + same family | 379 | +0.06054 | −0.02968 | +0.09022 | [−0.02669, +0.20810] | 0.0641 |
| TAKEN vs **ROSTER-CLEAN** | 397 | +0.04498 | −0.02169 | **+0.06667** | [−0.04363, +0.17962] | 0.1231 |

**The selector significantly beats what it declined, and does not significantly beat a
geometry-matched draw from the population once the defective family is removed from the control.**
The unmatched raw gap (taken +0.045 vs pool −0.205 = **+0.250**) is: ~40 % geometry (the taken set's
median risk distance is **2.02×** the pool's — 19.47 vs 9.63 bps), and of the remainder, most is the
avoidance of `current_breaker_re_entry` / born-past-stop rows, which the taken set contains **zero**
of in eight windows.

**Verdict on usage.** The downstream stack is not destroying a good signal. Measured end to end it
**adds**: selection +0.045 gross over a matched roster draw, management a further +0.023
(realised +0.05505 vs the same candidates' plain walk +0.03183), and the arm's own cost model
charges 0.074 where the plain contract charges 0.148. **The usage is the only reason the number is
near zero rather than −0.29.** Its cost is that it fires 0.048 % of the time — ~60 trades a month,
54 % of them one instrument — which is too thin to compound and too thin to prove anything: net
t = −0.403 on 464 trades over eight months.

---

## 6. WHAT THIS CORRECTS — old vs new, bluntly

| # | published claim | provenance | what it actually is | status |
|---|---|---|---|---|
| 1 | **gross mean −0.2175 R** | `gross_r` in `w0_WORKING_SET` = `opportunity_net_proxy_r + cost_r` — the **engine's counterfactual proxy**, not a path walk (`w0_DATA_DICTIONARY.md:451,486`) | the same 27,658 rows walked on the tape give **+0.0409** (market) or **−0.2367** (honest fill). Three numbers on one object spanning 0.28 R. | **SURVIVES as a property of the pool** (honest-fill walk −0.2056 agrees); **DIES as a property of "the system"** — the roster is −0.0827, the clean roster −0.0136, the taken set **+0.0551** |
| 2 | **34.68 % win rate** | same field, 2R geometry | pool honest-fill **32.03 %**; **roster fills 35.39 %**; **clean roster 37.98 %**; **taken set 47.20 %** | **SUPERSEDED** — off by 12.5 pp against the system's own trades |
| 3 | **1.1768:1 payoff → 45.94 % breakeven** | `winner_mean_r 1.0448 / loser_mean_r 0.8878` on `gross_r` | recomputed: **clean roster 1.5943 → 38.55 %**; **taken set 1.2662 → 44.13 %** | **SUPERSEDED.** The estate's own breakeven arithmetic was right; the payoff it used belongs to the counterfactual proxy |
| 4 | "needs 45.94 %, gets 34.68 %" → **−11.3 pp gap** | derived from 2 & 3 | clean roster **37.98 % vs 38.55 % = −0.57 pp**; taken set gross **47.20 % vs 44.13 % = +3.07 pp** | **DIES.** The gap is 20× smaller than published, and positive on the taken set |
| 5 | **12.72 % born past stop, −0.9948 R** | w0-capture on the pool | **reproduced** on the pool (12.43 % Jan). On the **roster** it is **2.02 %** of emissions / **6.81 %** of fills at ≈ **−0.996**; on the **taken set 0.00 %** in all 8 windows | **SURVIVES on the pool, MISLEADS as a population fact** — the pool is enriched **6.1×** in these rows |
| 6 | **`risk.min_rr` is 1.5, not 2.0** | PB | confirmed and extended: the **stop is the generator's** (57/57 identical on the January taken join) and the **target is the policy's** (0/57 identical). Both 1.5R and 2.0R walks are carried in `f1_BASELINE_V1.json`; the sign of every conclusion is unchanged | **CONFIRMED, and localised** |
| 7 | "55.65 % first-minute share" | **could not be located** in any committed receipt in `phase19/receipts/discovery` | measured analogues on the January pool: **61.29 %** of rows touch their entry within the first forward M1 bar; **31.24 %** of rows that end in a stop are stopped in the first M1 bar after fill; on the roster the latter is 21.4–29.8 % | **UNVERIFIABLE AS STATED** — use one of the measured definitions |
| 8 | "the broad family is finished / unrepairable" | `JANUARY_BANK.md` §3, CLAUDE.md §4 | true of the **policy layers on the pool**; **false as a statement about the setups**: 9 of 10 families sit within ±0.040 R of zero gross, 2 are positive, and April 2026's whole clean population is **+0.0189** | **SUPERSEDED — see §7** |
| 9 | cost basis | the arms' own `cost_r` | arm mean **0.07437** vs h1 broker-true **0.14938** on the same 507 trades — **2.008× on the mean, 0.899× on the median**. XAUUSD (274 trades) agrees at **1.044×**; the entire gap is `UKOIL_cash` **11.11×** and `USOIL_cash` **4.57×**; `US30_cash`/`GER40`/`JP225` run **0.12–0.18×** (h1 is *cheaper*) | **NEW — unreconciled.** Any claim quoting arm `cost_r` on an oil CFD is quoting a different cost model |

---

## 7. WHY IT IS FINISHED, AND WHAT WOULD HAVE TO BE TRUE

The owner ruled out "the broad family is finished" without a reason. Here is the reason, with the
measurement, on 1,118,694 emissions:

> **It is not finished because the setups are wrong. It is finished because the setups are worth
> zero and the unit of risk they are measured in is too small to survive a round trip.**
>
> The clean population's gross expectancy is **−0.01327 R/trade** — a **0.57 percentage point**
> shortfall against its own payoff-implied breakeven, on 298,537 honest fills across eight
> consecutive months, with one month positive. The broker toll on the identical rows is
> **+0.28118 R/trade**. The toll is **21×** the signal deficit and **95.5 %** of the loss.
>
> The toll is `cost_price ÷ risk_distance`, and the generator's median risk distance is **9.28 bps**
> (8.68 on its largest family) against a ~2.5–3 bps round trip. Across ten deciles of risk distance
> the toll falls 7.4× (0.730 → 0.098 R) **and the gross does not move** — it stays inside a ±0.04
> band with no monotone trend. So the geometry lever moves cost and only cost, and it runs out at
> −0.139 R/trade net.
>
> **What would have to be true for it to work**: a cell with gross ≥ +0.28 R/trade at the current
> geometry, or the current gross (≈ 0) at a risk distance ~20× wider (300–500 bps) without gross
> decaying — and the measurement says gross at d ≥ 150 bps is **−0.10**. Neither exists in this
> population. **The one thing that has never been measured is whether a rule exists that separates
> the ±0.04 gross band into a positive cell large enough to pay 0.22 R** — the family surface says
> the *families* do not do it, and §5 says the shipped selector does not do it either
> (+0.0667 R/trade vs a matched clean control, p 0.123).

**And one repairable thing, worth its own line.** `current_breaker_re_entry` emits 88,323 candidates
of which **68.0 %** are born past their own stop. It costs the family **−0.061 R/trade of gross**
(74 % of the whole deficit) on 9.85 % of the fills, and it is the single largest term in every
negative headline this estate has published about the broad family. **Removing it is free** — no
other family's numbers move — and it takes the published gross from −0.0823 to **−0.0180 (−78 %)**.

---

## 8. RECEIPTS

| artifact | what |
|---|---|
| `f1_BASELINE_V1.json` | **the canonical baseline other lanes read**: census, contracts + their verification, per-window taken economics, roster by window / pooled / clean, family table, decile table, matched controls, cost-model comparison, day-restriction ledger |
| `f1_ARM_TRADING_DAYS_V1.json` | each arm's own trading-day set, used to restrict the regenerated rosters |
| `f1_rows/RR_<window>.json.gz` | **per-row roster walks — 1,167,100 rows over 8 windows, un-day-restricted** (the day filter is applied at read time from `f1_ARM_TRADING_DAYS_V1.json`) (`sym, day, fam, d_bps, g, c, filled, past, reason, touch`). Reuse this instead of re-walking. |
| `f1_rows/M_<window>.json.gz` | per-row pool + taken walks, same schema, for the matched controls |
| `f1_rows/W_<window>.json` | per-window three-population summaries, both contracts, both targets, per family, per cohort |
| `f1_*.py` | every script, in dependency order: `f1_paths` → `f1_census` → `f1_extract_trades` → `f1_slim` → `f1_taken` → `f1_walk` → `f1_roster_rows` → `f1_matched` → `f1_matched_full` → `f1_final_tables` → `f1_build_artifact`; verification in `f1_validate_contract` / `f1_validate2`; cost cross-check in `f1_costcheck` |
| `f1_gen_rosters.sh` | close-only roster regeneration at `--min-rr 1.5` for the five windows PB had not built (`pbg_run.py --month <yyyymm> --min-rr 1.5 --workers 4`, ~5 min/month) |

Scratch outputs were produced under `/tmp/f1/`; everything load-bearing is copied here. The
regenerated close-only rosters themselves (`/tmp/f1/roster_<yyyymm>/`, ~90 MB) are **not** copied —
they rebuild in ~5 minutes a month from `f1_gen_rosters.sh`, and `f1_rows/RR_*.json.gz` already
carries every walked row.

**Not opened:** `LP_{june,august,september}_2025_S0R0_POOL_V1.jsonl.gz` and every artifact derived
from them, per `phase19/receipts/pools/READ_RESTRICTED_INDEX.md`.
