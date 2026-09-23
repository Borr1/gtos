# F3 — Why it comes back

**Commission:** owner swarm 2, 2026-08-12, forensic lane 3. *"When a trade goes our way and then
comes back — why? Not 'it reversed', but what was happening at the point of reversal."*

**Scope discipline.** Measurement only. No broker, no VPS, no config, no decision-contract-bound file
touched, no git write. Every number is recomputed on this machine from the sealed 2026 corpora and the
true-UTC M1 archive. Code and receipts: `f3_reversal/` — 10 scripts, 10 JSON artifacts.

**Population.** All five sealed-read 2026 months (Feb, Apr, May, Jun, Jul): 632,934 candidate
occurrences, **151,743 filled trades with an economic terminal**, 100 trading days, 24 symbols.

---

## 0. The answer, in eight lines

| question | answer |
|---|---|
| **How big is the "went our way then came back" problem?** | **Half the loss, by one measure.** 16,869 trades (11.1 %) reached **+1.0 R** in our favour and still ended negative. They carry **−17,840 R = 50.6 % of the pool's entire loss**. It is not a tail: the worst 1 % of give-back is only 3.2 % of it, the worst 25 % is 50 %. It is broad and systematic. |
| **So why did they come back?** | **Because 90.4 % of "give-back" is arithmetic, not an event.** Marking a trade at the instant it first touches +θ R is a *fair* mark under zero drift, so optional stopping says the terminal must average +θ. Measured: `E[gross \| touched +1 R] = +0.9121 R` against a fair-game benchmark of exactly **+1.0000**. Of the 0.9131 R average give-back, **0.8252 R is what any driftless walk gives back** and only **0.0879 R [−0.106, −0.070] is a real adverse effect**. |
| **Did it turn at a structural level?** | **No. Refuted with a matched control and two placebos.** 151,743 terminal peaks against 425,298 within-trade pauses. Prior-day high, prior-week high/low, prior-session extremes, M15 swings, three moving averages and round numbers at three granularities are **all null or indistinguishable from their own placebo**. `pdh` +0.0003 (p 0.391) while its 5-day-stale placebo reads +0.0004 (p 0.160). Composite "near ANY level" is **−0.028, the wrong sign**. |
| **Did it turn at a clock event?** | **Almost nowhere.** H4 bar edges — the boundaries the sleeves decide on — do **nothing** (lift 0.989, p 0.322). London and NY opens have peaks *less* likely than continuations. The one real lift is the broker rollover ±30 min at **1.75×** — but its damage is at the *fill*, not the peak (§6). |
| **Was there a liquidity signature?** | **Coincident, never leading, and the vacuum theory is backwards.** From −15 to −5 minutes the tape is flat (spread ratio 1.004–1.010). The signature appears at **t−1** and peaks at **t0**, and quote intensity goes **UP** (1.080×), not down. Nothing is actionable at t−1. |
| **Was the system generating an opposing signal?** | **Always, which makes it useless.** An opposing candidate exists within ±15 min at **83.3 %** of peaks — and **82.1 %** of continuations. Separately: **72.2 % of all fills overlap an opposite-side fill on the same instrument.** |
| **Then what is actually killing us?** | **The fill.** F1 relocated the question and the reframe holds: the median stop loser's entire favourable excursion is **0.395 R**, and the median range of the single M1 bar it was filled in is **0.390 R**. It never goes anywhere — its "excursion" is one bar of noise. **A 1 R stop is 3.56 normal M1 bar ranges wide.** |
| **What is knowable at entry?** | **Three things, worth +0.046 R/trade together on TEST** ([+0.033, +0.059], day-block, p 0) — **16 % of the 0.2868 R all-in cost**. Nothing here makes the pool positive. The single largest is not a market fact at all: **fills inside broker hour 00 net −0.722 R against −0.229 elsewhere.** |

**One paragraph for the owner.** The trades did not come back because something stopped them. Nothing
stopped them — there was never anything holding them up. Nine tenths of what looks like "giving it
back" is the difference between a *maximum* and a *mark*, which no exit rule and no entry filter can
ever collect, because a fair game pays you the mark and the maximum was never for sale. The remaining
tenth is real, it is worth about 0.088 R per trade that reaches +1 R, and it is concentrated in trades
whose "excursion" happened in the first five minutes and was really the noise range of the bar they
were filled in. **The reversal is not the disease. The fill is.**

---

## 0.1 Money convention, stated once

R is the trade's own stop distance. Two conventions are in play in this swarm and they differ by 8×,
so both are given and every table below is in R first.

| convention | 1 R = | basis |
|---|---:|---|
| **portfolio-realistic (used here)** | **$250** | $100k FTMO account; the shipped dial is a **2.00 % nominal ceiling** (`config/agent_config.yaml:1320`, profile `clean3_w7_ceiling_nom2p00`, ~1.73 % effective after half-Kelly), spread across the **6–7 distinct firing sleeves per day** the live `RunningConvictionLedger` exports record → ~0.25 %/position |
| F1's convention | $2,000 | 1 R = the full 2 % dial on one trade (`F1_CENSUS.json → mean_net_usd_at_2pct`) |

Multiply any dollar figure below by 8 to read it in F1's units. **Totals over the whole pool are
labelled as such and are not a book**: 151,743 trades over 100 days is 1,517 trades/day, which nothing
trades. Per-trade dollars are the honest unit.

---

## 1. Inventory — what already existed, and where it stops

The owner is right that forensic machinery exists. `git grep -l -iE "mfe|excursion|reversal|structural_level|confluence" -- '*.py'` returns **590 files**. What is
genuinely adjacent, and why none of it answers this question:

| existing machinery | what it covers | where it stops for F3 |
|---|---|---|
| `research/operations/final_moonshot_v4_.../hunt_key_level_reaction{,_v2,_v3,_v4}.py` + `HUNT_KEY_LEVEL_REACTION_V{1..4}_RESULT.json` | PDH/PDL/PWH/PWL, round numbers, multi-touch S/R, equal-high/low liquidity pools. **Already runs a matched drift control and a TRAIN≤2024 / FORWARD 2025–26 split.** | Asks *"can I make money entering AT a level"* — verdict no (v4 2026: `sig_long` −0.1044 vs `drift_long` −0.1439). **F3 asks the opposite question: do our existing trades DIE at levels.** Level *construction* reused in spirit; verdicts are consistent and independent. |
| `.../liquidity_map.py`, `confluence.py`, `KB4/KB6/KB7_*` | Resting-liquidity / stop-cluster model, sweep+reclaim, confluence scoring with pairwise-independence checks. Closest thing in the estate to "where do stops get hunted". | H4/M15 on the deep universe 2014–2026, as an **entry generator**. Not the sealed 2026 funnel corpus, not M1, and it never measures give-back on trades already open. |
| `scripts/build_vnext_friday_micro_price_action_anatomy.py`, `..._canonical_event_replay.py` | Tick/M1 path microscope with a clean Friday-close boundary; canonical event + broker-autopsy ledgers. Genuinely "what happened at the turn". | Scoped to **Fridays** in the 2026-06 vNext live-failure route. Wrong population and ~1/5 of the week. |
| `scripts/analyze_raw_ohlc_path_ablation_v1_failure_forensics.py` | Why fixed-R lock ladders failed promotion, J46–J49 baseline vs V1. | Says so itself: *"does not implement structural levels, reentry…"*. Pre-2026 event stream. |
| `scripts/analyze_raw_ohlc_path_scaling_v2_confluence.py`, `..._selector_forensics.py` | Whether V2 structural selectors agree/over-tighten on shared event keys. | Selector-vs-selector agreement on a fixed 2026-05 event log. Not reversal anatomy. |
| `scripts/analyze_historical_opportunity_truth_layer.py` | Cohort diagnostics on the rescued Phase-3 opportunity truth layer. | Different era, different labeller, superseded clock. |
| **`src/components/exit_policy_v4.py`** | **LIVE, armed MFE-conditioned exits**: `partial_trigger_r 1.0`, `be_trigger_r 1.0`, `trailing_trigger_r 1.0`, `stale_min_mfe_r 0.35` (`config/agent_config.yaml:649-656`, `enabled: true`, `apply_to_execution: true`). | **This is a two-stacks boundary, not a gap.** The live moonshot path already reacts to MFE; the replay corpus F3 measures runs a fixed 1 R/2 R contract with no BE move. Every give-back number here describes the *labelling* geometry, not the armed book's. Stated again in §12. |
| `src/components/slippage_shadow_logger.py` | Requested vs actual fill price, per fill, `shadow_logs/slippage.jsonl`. | **The right instrument to confirm §7 on real fills.** F3's fills are modelled M1, not broker fills. This is the follow-up, not a duplicate. |
| `swarm2/lane2_receipts/walk.py` (Lane 2) | Vectorised re-implementation of `resolve_post_submission_m1_lifecycle`, validated at **0.0 max deviation** on 146,736 fills. | **Reused directly.** F3 extends it to capture the path (§2). Superseding nothing. |

**The gap F3 fills:** nothing in the estate had measured the give-back of the sealed 2026 funnel
corpus at M1 resolution **against a matched within-trade control**. That control is the whole
methodological content of this lane.

---

## 2. The instrument, and its fidelity receipt

`f3_walk.py` extends Lane 2's walker, copying the fill logic, the exit-side quote transform
(`quote_side.py:385-412`), the first-complete-successor MARKET fill (`:1281-1289`), the
favourable-open / intrabar-touch LIMIT fill (`:1292-1330`), the invalid-gap guard (`:1344-1356`) and
the barrier scan **verbatim**. What it adds is the excursion path: every new running high in the
favourable coordinate, the retrace that followed it, and which one was terminal.

**Fidelity against Lane 2's sealed-reproducing walker** (`f3_walk.py`, cross-check in §14):

| trades compared | terminal-status agreement | max abs deviation, terminal gross R **and** MFE |
|---:|---:|---:|
| **151,743** | **1.000000** | **0.0** |

Lane 2's walker reproduces the sealed resolver at 0.0; F3's reproduces Lane 2's at 0.0. The 10,523
rows Lane 2 carries that F3 does not are `CENSOR` terminals, which have no economic terminal by
construction and are deliberately dropped.

### 2.1 The matched control, which is the point

For every trade the walker records:

* the **terminal peak** — the running maximum that was never exceeded, i.e. *the reversal point*;
* every **pause** — an advance to a new running high that then retraced by ≥ **0.25 R** and
  afterwards *made a new high anyway*.

A pause is the same event as a peak in every respect except the one that matters: the move resumed.
Same symbol, same day, same hour, same volatility, same trade, same geometry, same retrace magnitude.
**151,743 peaks against 425,298 pauses, compared within trade.** Any structural claim that does not
survive this comparison is an artifact, and §5 shows they all fail it.

Two further placebos run on identical machinery:

* **PLACEBO-LEVEL** — the same level construction lifted from **5 trading days earlier**.
* **PLACEBO-TIME** — the same levels at a random minute inside the trade's life.

---

## 3. The population, and F1's reframe

### 3.1 The give-back census

`F3_CENSUS.json`. Pool: 151,743 trades, total net **−35,290.7 R**, mean −0.2326 R/trade.

| MFE reached | n | share of pool | ended negative | their net R | their share of pool loss |
|---|---:|---:|---:|---:|---:|
| ≥ 0.25 R | 113,854 | 75.0 % | 53.6 % | −62,630 | — |
| ≥ 0.50 R | 90,908 | 59.9 % | 44.8 % | −42,516 | — |
| ≥ 1.00 R | 59,443 | 39.2 % | 28.4 % | **−17,840** | **50.6 %** |
| ≥ 1.50 R | 40,104 | 26.4 % | — | — | — |

**Headline population** — reached **+1.0 R** and ended negative: **16,869 trades**, mean net
**−1.0575 R** (**−$264/trade**), total **−17,840 R** = **50.6 % of the pool's entire loss**.
Terminal mix: 14,225 STOP / 2,548 TIME_STOP / 96 TARGET. Median 8 bars from fill to peak, median
**13 minutes** from peak to death.

**It is not a tail.** Give-back concentration: worst 1 % of trades = **3.2 %** of total give-back,
worst 5 % = 13.4 %, worst 10 % = 24.3 %, worst 25 % = **50.0 %**. A handful of blow-ups would show
5–10× that concentration. This is a property of the whole pool.

### 3.2 Reconciliation with F1 — the two lanes agree

F1 reports, of 78,207 stop losers, the share that traded through each level pre-exit-bar. F3 measures
running-max MFE at the sealed terminal on its 79,349 STOP terminals:

| threshold | F1 (`reached_*_preexit`) | F3 | agreement |
|---|---:|---:|---|
| ≥ 0.5 R | 42.05 % | 42.31 % | ✓ |
| ≥ 1.0 R | 17.82 % | 17.93 % | ✓ |
| ≥ 1.5 R | 6.15 % | 6.22 % | ✓ |
| ≥ 1.8 R | 1.95 % | 1.98 % | ✓ |
| ≥ 1.9 R | 1.03 % | 1.05 % | ✓ |

The residual is F1's strict pre-exit-bar exclusion against F3's running max through the terminal bar.
**Two independently written walkers on two population definitions agree to within 0.3 pp at every
threshold.**

**Both framings are true and they are not in tension.** At F1's ≥1.8 R bar only ~1,500 losers could
host a "right direction, wrong exit" story — correct, and it kills the near-miss narrative. At the
≥1.0 R bar the same population carries half the pool's loss — also correct, and it is why the question
was worth asking. §4 shows why *neither* is an exit problem.

---

## 4. The null that explains 90 % of it

This is the core of the lane, and it is measured, not asserted.

**The argument.** If the price process carries no drift, then marking a position at the instant it
first touches +θ R is a *fair* mark. Optional stopping then says that whatever rule is applied
afterwards — barrier, clock, anything not using the future — the terminal must average **+θ**. A
driftless walk that has gone +1 R gives back, on average, exactly the +1 R it gained. "It came back"
is then not an event with a cause; **it is the absence of drift**.

So the entire reversal question collapses to one number per threshold:

> **DRIFT_AFTER_TOUCH(θ) = E[terminal gross R | MFE ≥ θ] − θ**

Zero means a fair game and nothing to explain. `F3_NULL.json`, day-block bootstrap (trades on one day
are not independent):

| θ | n | E[gross \| touched θ] | **drift after touch** | CI95 (day-block) | p | total R |
|---:|---:|---:|---:|---|---:|---:|
| 0.25 | 113,854 | 0.1745 | **−0.0755** | [−0.092, −0.060] | 0.000 | −8,594 |
| 0.50 | 90,908 | 0.4036 | **−0.0964** | [−0.113, −0.079] | 0.000 | −8,762 |
| 0.75 | 73,005 | 0.6541 | **−0.0959** | [−0.115, −0.076] | 0.000 | −7,001 |
| **1.00** | **59,443** | **0.9121** | **−0.0879** | **[−0.106, −0.070]** | **0.000** | **−5,225** |
| 1.25 | 48,824 | 1.1688 | −0.0812 | [−0.099, −0.063] | 0.000 | −3,967 |
| 1.50 | 40,104 | 1.4301 | −0.0699 | [−0.088, −0.053] | 0.000 | −2,802 |

**The decomposition of the give-back, at θ = 1.0** (59,443 trades, mean MFE 1.8252 R):

| component | R/trade | share | total R | total $ |
|---|---:|---:|---:|---:|
| average give-back (MFE − terminal gross) | 0.9131 | 100 % | 54,275 | $13.57 M |
| **explained by the null** (MFE − fair mark) | **0.8252** | **90.4 %** | 49,050 | $12.26 M |
| **real adverse drift** (fair mark − terminal) | **0.0879** | **9.6 %** | **5,225** | **$1.31 M** |

**The 90.4 % is not recoverable by anything.** It is the gap between a maximum and a mark. No entry
filter, no exit rule, no stop placement and no sizing change can collect it, because it was never
available: optional stopping is a theorem, not a modelling choice.

**Internal consistency check.** The census computes, independently, that banking every trade at +1 R
the moment it touches would be worth **+5,225.17 R** against realised. The null computes the adverse
drift after touching +1 R as **−0.0879 × 59,443 = −5,225.2 R**. Two computations written for different
purposes agree to four significant figures — as they must, since they are the same quantity.

### 4.1 What breaks the fair game — and it is not a market event

Cutting the θ = 1.0 residual by every candidate cause (`F3_NULL.json → fair_game_broken_by`):

| cut | n | drift inside | drift outside | **gap** | $/trade |
|---|---:|---:|---:|---:|---:|
| **peaked within 5 minutes of fill** | 12,518 | **−0.7741** | +0.0951 | **−0.8692** | **−$217** |
| entered NY session 12–21 UTC | 25,528 | −0.1267 | −0.0587 | −0.0681 | −$17 |
| trade spans the rollover | 563 | −0.0985 | −0.0878 | −0.0107 | −$3 |
| entered Asia 00–07 UTC | 16,217 | −0.0375 | −0.1068 | +0.0694 | +$17 |
| peak within 30 min of rollover | 681 | −0.0129 | −0.0888 | +0.0758 | +$19 |
| order type MARKET | 26,324 | +0.0244 | −0.1772 | +0.2016 | +$50 |
| **peaked after 60 minutes** | 11,560 | **+0.2473** | −0.1688 | +0.4162 | +$104 |
| peak in broker hour 00 | 314 | +0.3684 | −0.0903 | +0.4587 | +$115 |

**One cut dominates every other by 2×, and it is a clock reading, not a market event.** Trades whose
peak arrives within five minutes of the fill under-perform a fair game by **0.77 R**. Trades that peak
after an hour **beat** it by +0.25 R. §7 shows why: a peak in the first five minutes is not a move at
all — it is the noise range of the bar the trade was filled in.

The drift is **stable across all five months** (Feb −0.081, Apr −0.103, May −0.087, Jun −0.084,
Jul −0.084) and splits by family with `current_fvg_fill` worst at −0.192 and `cross_asset_lead_lag`
positive at +0.053.

### 4.2 The wick correction, and a sign flip worth recording

`F3_WICK.json`. MFE is the bar **high**; a high can be one tick. Is the −0.088 R real or a
measurement convention? Two arms:

| θ | wick arm (mark = θ) | close arm (mark = **actual close at crossing**) | close arm benchmarked against θ — **BIASED** |
|---:|---:|---:|---:|
| 0.50 | −0.0968 [−0.114, −0.080] | −0.0056 [−0.021, +0.010] | **+0.1930** |
| 1.00 | −0.0891 [−0.107, −0.071] | **−0.0339 [−0.049, −0.020]** | **+0.1919** |
| 1.50 | −0.0720 [−0.090, −0.056] | −0.0724 [−0.088, −0.056] | +0.1765 |

**The third column is a trap this lane fell into and climbed out of, and it is worth reporting.**
Benchmarking the close arm against θ credits the *overshoot* (the first close beyond θ is 0.19–0.26 R
past it) as drift, and flips the sign from −0.03 to **+0.19**. Corrected against the actual mark, the
effect returns. The wick arm needs no such correction: price is continuous, so the first touch of θ is
*at* θ — which is also exactly what a resting take-profit limit at +θ would fill at.

**Verdict: the adverse drift is real, and about 38 % of it survives on a strictly transactable
close-based mark.** The wick arm is the right model for a resting limit; the close arm bounds it from
below.

---

## 5. Where in price — the structural story is refuted

`F3_STRUCTURE.json`. 151,743 peaks vs 425,298 within-trade pauses, paired, at τ = 0.10 R.

| level | peak rate | pause rate | diff | CI95 | p | reading |
|---|---:|---:|---:|---|---:|---|
| *own 2 R target* | 0.1002 | 0.0258 | +0.0744 | [+0.073, +0.076] | 0.000 | **mechanical** — the target is an absorbing barrier, so a pause cannot exist within touching distance of it |
| *own entry* | 0.0205 | 0.0856 | −0.0650 | [−0.066, −0.064] | 0.000 | **mechanical** — pauses happen early and near entry, peaks are far from it |
| session hi/lo at fill | 0.0202 | 0.0369 | −0.0167 | [−0.018, −0.016] | 0.000 | wrong sign; same mechanical driver as entry |
| day hi/lo at fill | 0.0157 | 0.0254 | −0.0097 | [−0.011, −0.009] | 0.000 | wrong sign |
| M15 swing high | 0.0348 | 0.0328 | +0.0020 | [+0.001, +0.003] | 0.003 | 0.2 pp on a 3.5 % base — same order as the placebos |
| **round number (fine)** | 0.6572 | 0.6592 | −0.0020 | [−0.005, +0.001] | 0.161 | **null**; its own PLACEBO-TIME reads −0.0017 |
| SMA20 / SMA50 / SMA200 (M15) | — | — | −0.0011 / −0.0009 / +0.0003 | all span 0 | 0.088 / 0.093 / 0.445 | **null** |
| **prior-day high** | 0.0098 | 0.0095 | **+0.0003** | [−0.000, +0.001] | **0.391** | **null** — and its 5-day-stale **placebo reads +0.0004** |
| prior-day low | 0.0084 | 0.0088 | −0.0004 | [−0.001, +0.000] | 0.242 | **null** |
| **prior-week high** | 0.0040 | 0.0039 | +0.0001 | [−0.000, +0.001] | **0.641** | **null** — while **PLACEBO_LEVEL_wkh is +0.0005 at p 0.008** |
| prior-session hi/lo | 0.0155 / 0.0166 | 0.0166 / 0.0166 | −0.0011 / −0.0000 | — | 0.010 / 0.919 | **null** |

**Composite — "within τ of ANY structural level":**

| τ | peak rate | pause rate | diff | CI95 | p |
|---:|---:|---:|---:|---|---:|
| 0.05 R | 0.1004 | 0.1244 | **−0.0240** | [−0.026, −0.022] | 0.000 |
| 0.10 R | 0.1920 | 0.2195 | **−0.0275** | [−0.030, −0.025] | 0.000 |
| 0.25 R | 0.3993 | 0.4283 | **−0.0289** | [−0.032, −0.026] | 0.000 |

**Reversals are LESS likely to be near a structural level than continuations are, at every tolerance.**

Three things to take from this table:

1. **Every genuinely structural level is null**, and each one's placebo is the same size or larger.
   `wkh` is the cleanest demonstration in the estate: the real level reads p 0.641 and the
   deliberately-wrong-day placebo reads p 0.008. At n = 151,743 a p-value on an effect this small
   carries no information, which is exactly why the placebo, not the p-value, is the referee.
2. **Levels really are everywhere.** The fine round grid puts **65.7 %** of *all* observations "at a
   round number" at τ = 0.10 R. Any analysis without a matched control would have found a
   spectacular round-number effect and it would have been noise.
3. **The two significant rows are mechanical**, both driven by the absorbing barrier and by where in a
   trade's life pauses can occur. Neither is a market-structure claim.

### 5.1 The one structural finding that looked real — and died on its own lag test

`F3_EXANTE.json`, `F3_EXANTE_lag5.json`, `F3_CONTROL.json`.

Asking the ex-ante version — *is there a level in the path between entry and the 2 R target* — first
produced a strong, monotone, out-of-sample-replicating result with the **opposite sign** to the folk
theory:

| strong obstacles in path (TEST: jun+jul) | n | share | mean net R | give-back R | reversal rate |
|---:|---:|---:|---:|---:|---:|
| 0 | 30,406 | 47.4 % | −0.2933 | 1.136 | 13.7 % |
| 1 | 12,576 | 19.6 % | −0.2723 | 1.086 | 13.4 % |
| 2 | 11,350 | 17.7 % | −0.2058 | 0.901 | 6.8 % |
| 3 | 5,762 | 9.0 % | −0.1695 | 0.792 | 5.1 % |
| 4 | 3,322 | 5.2 % | **−0.1085** | **0.693** | **3.3 %** |

TRAIN none-vs-2+ **−0.145 R** [−0.192, −0.096]; TEST **−0.115 R** [−0.165, −0.065], p 0. Monotone in
both halves. **16 of the 17 level types with a measurable comparison group point the same way**,
including moving averages and round numbers — having a level in the path is associated with a *better*
outcome in almost every family. **That uniformity was the tell**, and three kills followed:

| test | result |
|---|---|
| **LAG TEST — levels lifted 5 trading days stale** | TEST effect **−0.1149 R** against the real-levels **−0.1150 R**. **Identical.** The effect does not know what day the levels came from. |
| **Stratify on `risk_over_atr`** | raw −0.133 R → **−0.034 R**. **74 % of the effect is stop width.** Correlation of `risk_over_atr` with obstacle count: **+0.599**. |
| Stratify on family × stop-width simultaneously | −0.064 R |

**Verdict: artifact.** A 2 R span that crosses no levels is simply a *narrow* span. Lane 2 already
established that cost in R is a price quantity divided by the stop, and measured the stop-width lever
at +0.159 R/trade. This is that same lever wearing a structural costume. It is reported here in full
because it would have been an attractive and completely wrong entry filter, and because the lag test
is what killed it.

**Also worth recording:** with 18 level families (15 structural + a round grid at three
granularities), **every single one of the 151,743 trades has at least one level between its entry and
its target** — the "clean path" cell is empty, n = 0. The finest round grid is itself in nearly every
path, which is why it has no comparison group. "Is there an obstacle" is not a question that
discriminates anything.

---

## 6. When in time

`F3_TIMING.json`. Peaks against matched pauses, plus an exposure denominator (peaks per 1,000
trade-minutes actually at risk), because a raw histogram of peak times mostly measures when the book
is open.

| clock event | peak rate | pause rate | lift | p |
|---|---:|---:|---:|---:|
| **broker rollover ±30 min** | 0.01426 | 0.00816 | **1.748** | 0.000 |
| broker hour 00 (whole hour) | 0.00573 | 0.00543 | 1.054 | **0.195** |
| M15 bar edge | 0.0700 | 0.0649 | 1.079 | 0.000 |
| H1 bar edge | 0.1231 | 0.1180 | 1.044 | 0.000 |
| NY cash open 13:30–14:00 UTC | 0.0422 | 0.0396 | 1.068 | 0.000 |
| **H4 bar edge** | 0.0634 | 0.0641 | **0.989** | **0.322** |
| London open 07:00–07:30 UTC | 0.0349 | 0.0375 | **0.931** | 0.000 |
| NY open 13:00–13:30 UTC | 0.0271 | 0.0287 | **0.944** | 0.000 |

* **The H4 bar boundary — the timeframe the sleeves decide on — does nothing.** Lift 0.989, p 0.322.
* **The session opens are the wrong way round.** Peaks are *less* frequent at the London and NY opens
  than continuations: moves run through the opens rather than dying at them.
* **The rollover is the only real clock lift, at 1.75×, and it is specifically the ±30-minute window
  and not the hour** (the whole hour reads 1.054, p 0.195). The precision matters: this is a
  boundary effect, not an hour effect.
* **But the rollover's damage is not at the peak.** §4.1 shows peaks *inside* the rollover window
  actually beat the fair game (+0.076 gap). The money is lost at the fill (§7.3).

**Trades whose realised life spans the rollover:** 1,687 (1.1 %), mean net **−0.545 R** vs −0.229 R,
difference **−0.316 R** [−0.399, −0.241], p 0. Note the ex-ante version is a wider set: whether the
*fixed 120-minute horizon* crosses broker midnight is determined at submission and catches **4.7 %**
of the book, because most trades resolve before their horizon. Lever L1 (§11.2) uses the ex-ante
definition, which is the only one an entry filter could act on.

---

## 7. The fill — where the damage actually is

F1 relocated this lane's question and the relocation is correct. `F3_FILL.json`, `F3_FILLBAR.json`.

### 7.1 The artifact check, run first as instructed — and it fires

| quantity | value |
|---|---:|
| median range of the **single M1 bar the fill lands in** | **0.390 R** |
| median MFE of a **STOP loser** | **0.395 R** |
| median bars from fill to peak, STOP losers | **1.0** |
| share of STOP losers whose peak is **inside the fill bar itself** | **47.1 %** |
| share of all trades whose peak is inside the fill bar | 27.3 % |

**These are the same number.** The median stop loser's entire favourable excursion is one M1 bar of
range around its own fill. It does not go and come back. **It never goes anywhere.**

So F1's "+0.42 R at 1 minute" is real as a measurement and must not be read as a micro-extreme that
could have been exited at: at M1 resolution the first observation *is* the fill bar's own high, and
that high is not a price the position could have been closed at except by a resting limit sitting
inside a single minute's range. **This is the bar-resolution caveat the coordinator asked for, and it
is confirmed.**

### 7.2 Is the fill bar abnormal? The control says yes — and reveals the real geometry

| quantity | value |
|---|---:|
| median fill-bar range | 0.390 R |
| median range of the **preceding 60 M1 bars**, same trade's R | **0.281 R** |
| median ratio fill-bar : normal bar | **1.379×** (mean 1.759×) |
| **a 1 R stop, measured in normal M1 bar ranges** | **3.56 bars** |
| a 1 R stop, measured in fill-bar ranges | 2.57 bars |

**This is the geometry finding of the lane.** The stop is 3.56 minutes of ordinary price range wide.
The trades are not being reversed by anything; they are being stopped by noise at M1 scale, and the
"excursion" that precedes it is the same noise pointing the other way first.

By order type the split is stark:

| | fill-bar range | prior-60 range | ratio |
|---|---:|---:|---:|
| **LIMIT** | **0.623 R** | 0.354 R | **1.68×** |
| MARKET | 0.241 R | 0.205 R | 1.15× |

**A LIMIT order is filled by a bar that spans 62 % of the entire stop distance and is 1.68× the
normal bar.** The limit is not being reached; it is being swept through.

### 7.3 Order type, and the rollover as a fill defect

| | n | mean net R | mean MFE | fill position in prior 30-bar range* | pre-fill 15 min move* | peak is fill bar |
|---|---:|---:|---:|---:|---:|---:|
| **LIMIT** | 73,943 | **−0.1864** [−0.210, −0.160] | 1.087 | **−0.059** | **−1.418 R** | 35.2 % |
| **MARKET** | 77,800 | **−0.2765** [−0.294, −0.259] | 0.779 | **+0.617** | −0.117 R | 19.8 % |

\* oriented so 1.0 = the fill sits at the extreme **in our favour**; 0.5 = mid-range; negative = the
fill is outside the prior range on the **adverse** side.

* **MARKET fills land at the 62nd percentile of the recent range in our own direction** — mild
  buying-into-strength.
* **LIMIT fills land just *outside* the prior 30-bar range on the adverse side**, after price has
  travelled **1.42 R against the trade in the preceding 15 minutes.** Part of that is mechanical (a
  buy limit only fills if price falls to it); the magnitude is not. This is the classic
  adverse-selection channel, quantified.
* On this raw pool **LIMIT nets 0.090 R better than MARKET**, which is the opposite of the shipped
  MARKET-top-choice rule's direction. That is not a contradiction — the shipped rule selects the
  *top-ranked* candidate and abstains on LIMIT, a selection question this table does not address (see
  `breakthrough/B1_LIMIT_ARM_MEASURED_V1.md`) — but it is worth the owner knowing.

**The rollover, at the fill:**

| cut | n | share | mean net R | fill position in range | elsewhere |
|---|---:|---:|---:|---:|---:|
| fill within 30 min of broker rollover | 1,721 | 1.13 % | **−0.720** [−0.817, −0.610] | 0.526 | −0.227 |
| **fill inside broker hour 00** | 1,119 | 0.74 % | **−0.722** [−0.797, −0.644] | **0.930** | −0.229 |

**Fills inside broker hour 00 land at the 93rd percentile of the recent range in our own direction and
then lose 0.72 R — 3.2× the pool average.** That is B10's 34× spread spike converted into a fill: the
order crosses a blown-out spread, prints at an extreme, and reverts. It is an instrument defect, it is
entirely knowable at entry, and it is the cleanest repair in this lane.

**One sub-question closes degenerately:** every submission in the corpus sits on the M15 grid
(share = 1.000), so "does the damage concentrate at M15 bar boundaries" cannot be asked of this
population — there is no off-grid comparison group.

---

## 8. Calendar and events — the calendar is unusable, and say so

`data/economic_calendar.csv` is **14 lines**: a header and **13 events**, all between **2026-06-01 and
2026-06-05**, all `impact HIGH`, covering 5 calendar days of a 100-trading-day corpus. It carries no
2026-02, 2026-04, 2026-05 or 2026-07 rows at all. **It cannot support any event analysis and none is
attempted here.** Nothing in the tick archive substitutes for it: the archive is quote-only (§9) and
carries no event tags.

What *is* available is the clock-clustering evidence in §6, which is the honest proxy the mandate
allowed: reversal clustering around fixed times of day is itself evidence, and it says the H4/session
boundaries do nothing while the broker rollover does.

---

## 9. The tape — quote-only, coincident, and the vacuum theory is backwards

`F3_TAPE.json`, `F3_TAPE_LEAD.json`. Window 2026-06-18..07-24, the tick archive's coverage.

**Boundary, verified rather than accepted.** Direct scan of 300,000 rows of
`FTMO_EURUSD_ticks_20260618_to_20260726.csv.gz`: `last`, `volume` and `volume_real` are **zero on
every row**; only `flags` is populated. **True order flow — aggressor side, trade size, imbalance — is
not recoverable from this archive at any effort.** What is measurable is the quote process.

Every quantity is normalised by *the same symbol's median for the same broker hour*, because B10
measured a 34× spread spike at broker hour 00 and a DST smear that has already cost two lanes; a raw
spread comparison would mostly measure what hour it was.

| at the stall minute | peak | pause | diff | CI95 | p |
|---|---:|---:|---:|---|---:|
| spread / hour-median | 1.153 | 1.103 | +0.050 | [+0.041, +0.059] | 0.000 |
| **quote intensity / hour-median** | **1.384** | **1.343** | **+0.041** | [+0.030, +0.053] | 0.000 |
| quote range / hour-median | 1.726 | 1.577 | +0.149 | [+0.128, +0.172] | 0.000 |
| max spread / hour-median | 1.812 | 1.657 | +0.155 | [+0.119, +0.194] | 0.000 |

**Quote intensity goes UP at the reversal, not down. There is no liquidity vacuum.** The signature is
a volatility burst: a wider range, a modestly wider spread, and *more* quoting.

**And it does not lead.** Peak-to-pause ratios by offset from the stall:

| minute | −15 | −10 | −5 | −3 | **−1** | **0** | +1 | +5 | +10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| spread ratio | 1.004 | 1.008 | 1.010 | 1.010 | **1.025** | **1.038** | 1.020 | 1.008 | 0.992 |
| intensity ratio | 1.009 | 1.014 | 1.017 | 1.027 | **1.045** | **1.080** | 1.066 | 1.058 | 1.036 |

Flat from −15 to −5. The signature appears at **t−1** and peaks at **t0**. **A 2.5 % relative spread
elevation one minute ahead is not a tradeable warning.** There is no usable liquidity precursor in
this data.

---

## 10. The system's own signals

`F3_OPPOSING.json`. Nobody had checked this; it is cheap and two of the three answers are negative.

| | at peaks | at pauses | diff | CI95 | p |
|---|---:|---:|---:|---|---:|
| an **opposing**-side candidate within ±15 min | 83.30 % | 82.07 % | +1.22 pp | [+1.09, +1.35] | 0.000 |
| a **same**-side candidate within ±15 min | 88.33 % | 94.70 % | **−6.37 pp** | [−6.52, −6.22] | 0.000 |

* **The opposing-candidate theory is dead on arrival.** An opposing candidate is present at 83 % of
  reversals — and at 82 % of continuations. The funnel is nearly always generating both sides, so its
  presence carries essentially no information. The 1.2 pp difference is statistically certain and
  operationally worthless.
* **The informative one is the opposite of what was expected**, and it is 5× larger: when a move is
  going to *continue*, the funnel is still generating **same-side** candidates; when it is about to
  top, same-side generation has dried up. **Stated as a caveat that matters: the "pause" label uses
  the future** (a pause is defined by a subsequent new high), so this is a valid *descriptive*
  contrast and **not** a validated predictive signal. Converting it into one requires a forward test
  that this lane did not run — it is filed as the single most promising unexplored item in §13.

**The structural finding the mandate anticipated is real.** Across the funnel population,
**109,501 of 151,743 fills (72.2 %) overlap in time with an opposite-side fill on the same
instrument** — 164,048 overlapping pairs. Whenever that happens, one side's give-back is the other
side's profit and the pair nets to a pure cost payment. (Hedged trades average −0.152 R against
−0.442 R for unhedged, difference +0.290 [+0.276, +0.304]; this is **not** a causal claim — busy,
liquid periods generate both sides — but the self-opposition rate itself is a property of the pool
that any breadth or diversification claim must price.)

---

## 11. What is knowable at entry — the centre of the lane

Per the owner's standing objection: widening a stop protects a thing that was not strong to begin
with, and the same objection retires every exit-side repair. So each cause is classified by whether it
can be seen *before the candidate is filled*.

### 11.1 The classification

| cause | share of the give-back it explains | knowable at entry? | what it is |
|---|---|---|---|
| **No drift (optional stopping)** | **90.4 %** | n/a — **not a cause** | Arithmetic. Unavailable to any rule. |
| **Fill lands in a displacement bar 1.38× normal, with a stop only 3.56 normal bars wide** | the dominant part of the remaining 9.6 % | **YES — fully** | Bar range and stop distance both exist at submission. This is the geometry, and it is `risk_over_atr`. |
| **Fill inside broker hour 00 / rollover ±30 min** | 1.13 % of trades, **−0.49 R each** in excess | **YES — deterministically** | Instrument defect (blown spread → extreme print → revert). |
| **Horizon spans the broker rollover** | 1.11 % of trades, −0.316 R each | **YES — deterministically** | Submission time + the fixed 120-min horizon determine it. |
| **LIMIT adverse selection** (filled by a 1.68× bar sweeping through, after 1.42 R of adverse travel) | concentrated in 48.7 % of the pool | **YES — order type is a property of the candidate** | Classic adverse selection. |
| Entry hour (broker) | −0.021 R vs pool at the worst hours | **YES** | Partly the rollover, partly session cost. |
| Peak arrives < 5 min after fill (−0.869 R gap) | largest single cut in §4.1 | **NO** — it is an outcome | Mostly the §7.1 artifact restated; not a filter. |
| Spread/intensity burst at the turn | +0.050 / +0.041 normalised | **NO** — coincident, t−1 at best | Cost of doing business. |
| Same-side candidate generation drying up | −6.37 pp | **NO at entry** — a live signal | Management signal, unvalidated. |
| Structural level at the reversal | **0 %** — refuted | n/a | Does not exist. |
| Session / H4 / M15 boundaries | ~0 % | n/a | Do nothing. |
| News events | unmeasurable | no data | Calendar is 13 events over 5 days. |

### 11.2 The levers, priced on TEST only

`F3_LEVERS.json`. Every lever selected on TRAIN (Feb, Apr, May) and priced on **TEST (Jun, Jul)**
only, day-block bootstrapped. TEST book: 64,166 trades, mean net **−0.2512 R**.

| lever | knowable at entry | % dropped | Δ mean net R | CI95 (day-block) | p | $/trade | loss avoided |
|---|---|---:|---:|---|---:|---:|---:|
| **L3** drop narrowest stop quintile (`risk_over_atr` < TRAIN p20) | yes | 21.0 % | **+0.0365** | [+0.0247, +0.0480] | 0.000 | +$9.13 | $1,309,891 |
| **L2** drop worst entry broker-hours (TRAIN-selected: **0, 8, 21, 22, 23**) | yes | 14.3 % | +0.0210 | [+0.0110, +0.0302] | 0.000 | +$5.25 | $865,801 |
| **L1** drop horizon-spanning-rollover | yes | 4.7 % | +0.0127 | [+0.0079, +0.0181] | 0.000 | +$3.18 | $383,954 |
| **L1 + L3** | yes | 24.6 % | **+0.0463** | **[+0.0332, +0.0594]** | 0.000 | **+$11.58** | $1,551,329 |
| L4 restrict to MARKET only | yes | 49.1 % | **−0.0519** | [−0.0735, −0.0302] | 0.000 | −$12.98 | — |
| *X1 close at +1 R whenever touched* | **no** — an exit rule | — | +0.0325 | — | — | +$8.13 | $521,714 |

**An unplanned cross-validation.** L2's worst hours were chosen purely on TRAIN net R with no
knowledge of the clock, and came back as broker hours **0, 8, 21, 22, 23** — **four of the five are the
rollover and the three hours leading into it.** An economically-selected filter independently
rediscovered the boundary §6 and §7.3 identified structurally. That is the strongest single piece of
corroboration in this lane.

**Priced against the thing that matters.** F1 measures the pool's all-in cost at **0.2868 R/trade**
against a barrier-free directional edge of **+0.0301 R** (t = 3.18). So:

* **L1 + L3 recovers +0.0463 R = 16.1 % of the all-in cost**, and **1.54× the entire measured
  directional edge**.
* It does **not** make the pool positive: TEST mean net goes −0.2512 → −0.2049 R. **This is damage
  reduction, not an edge.**
* L3 is Lane 2's stop-width lever rediscovered from the reversal side, and §5.1 shows the structural
  dressing on it is an artifact. Credit belongs to Lane 2; the contribution here is the independent
  path and the lag test that removes the false explanation.

### 11.3 The one repair worth doing on its own terms

**Do not fill inside broker hour 00.** n = 1,119 (0.74 % of the pool), mean net **−0.722 R** against
−0.229 R elsewhere, fills landing at the **93rd percentile** of the recent range. Excess loss ≈
**0.49 R/trade ≈ $123/trade**. It is deterministic at submission, it costs 0.74 % of the book, it needs
no model, and it is an instrument defect rather than a market fact — which is precisely the
distinction this lane exists to draw.

---

## 12. Boundaries — what this lane does NOT cover

1. **This is the funnel candidate corpus, not the armed sleeve estate.** 151,743 fills across 24
   symbols and 10 origin families. It is the pool the MARKET-top-choice rule selects *from*. No number
   here describes `crypto`, `energy_agri`, `sub_mid_dn_revert` or `sub_xvol_pullback`.
2. **The measured contract is fixed 1 R / 2 R with a 120-minute clock and no break-even move.** The
   live moonshot path runs `exit_policy_v4` **armed** (`agent_config.yaml:649-656`,
   `partial_trigger_r 1.0`, `be_trigger_r 1.0`, `trailing_trigger_r 1.0`). **Give-back as measured here
   is a property of the labelling geometry and overstates what the live book would experience** on any
   sleeve running a partial/BE/trailing profile. §4's optional-stopping result is unaffected by this —
   it holds for *any* stopping rule — but the 0.9131 R average give-back is not the live book's.
3. **Fills are modelled M1, not broker fills.** `expected_slippage_r` is the constant 0.02 on all
   rows (Lane 2 §5). The adverse-selection finding in §7 should be confirmed against real
   requested-vs-actual fill prices via `src/components/slippage_shadow_logger.py` before it is priced
   into anything live.
4. **The tape section covers 2026-06-18..07-24 only** and is quote-only.
5. **The "same-side generation dries up" contrast uses the future in its control label.** It is
   descriptive. It is not a validated signal and is not proposed as one.
6. Levels are built from the same true-UTC M1 archive as the walker, so the clock is self-consistent;
   they are **not** cross-checked against the `deep_universe_h4d1` D1/H4 archive, which in any case
   ends 2026-06-16 and could not cover Jun–Jul.

---

## 13. What would reverse each finding

| finding | what would overturn it |
|---|---|
| 90.4 % of give-back is the null | A drift measurement showing `E[gross \| touched θ] − θ` ≈ 0 on a population where it is currently −0.09. The statistic is one line; anyone can re-run it. |
| No structural level explains reversals | A level construction this lane did not build (volume profile POC/VAH/VAL, options strikes, overnight-session VWAP, opposing-signal entry prices as a *density*) that beats its own 5-day-stale placebo in the paired test. The machinery takes a level array and returns the answer. |
| The obstacle effect is stop width | A version that survives the lag test. It did not, at −0.1149 vs −0.1150. |
| The tape has no precursor | Real order flow. The archive cannot answer it — `last`/`volume`/`volume_real` are zero. A depth-of-book or time-and-sales capture would reopen it entirely. |
| Rollover fills are an instrument defect | Broker fill records showing hour-00 fills print at the mid rather than the extreme. `slippage_shadow_logger` output would settle it. |
| LIMIT adverse selection | Showing the 1.68× fill-bar ratio is a property of the *level placement* rather than the fill, e.g. by measuring bars that touched an unfilled limit. |
| The self-opposition rate matters | Showing that the deployable selection rule removes it — this lane measured the raw pool, not the selected book. **This is the highest-value open item**, since a 72.2 % self-opposition rate would make any breadth claim illusory. |

**The most promising unexplored item** is §10's same-side-generation signal, converted into a proper
forward test: at minute *t*, does the absence of same-side candidate generation predict that the
running maximum will not be exceeded? It is a live, causal, cheap signal, it is 5× larger than the
opposing-candidate effect, and it has never been measured predictively.

---

## 14. Receipts

All under `swarm2/forensics/f3_reversal/`. Heavy intermediates in
`/Users/borr/.claude/jobs/adb9e69b/tmp/f3/` (not committed).

| script | artifact | what it establishes |
|---|---|---|
| `f3_walk.py` | *(walk pickles)* | Path-capturing walker. **1.000000 status agreement, 0.0 max deviation on gross R and MFE vs Lane 2 on 151,743 trades.** |
| `f3_census.py` | `F3_CENSUS.json` | The give-back census, the ladder, concentration. |
| `f3_levels.py` | *(level pickles)* | 17 causal structural-level families from true-UTC M1, broker day via `NEW_YORK_PLUS_7`. |
| `f3_structure.py` | `F3_STRUCTURE.json` | Paired peak-vs-pause + both placebos. §5. |
| `f3_timing.py` | `F3_TIMING.json` | Clock events with exposure and matched denominators. §6. |
| `f3_tape.py`, `f3_tape_lead.py` | `F3_TAPE.json`, `F3_TAPE_LEAD.json` | Quote-only tape at and around the turn. §9. |
| `f3_opposing.py` | `F3_OPPOSING.json` | Opposing/same-side generation; self-opposition rate. §10. |
| `f3_exante.py` | `F3_EXANTE.json`, `F3_EXANTE_lag5.json` | The obstacle hypothesis and its lag test. §5.1. |
| `f3_control.py` | `F3_CONTROL.json` | Confound stratification that kills it. §5.1. |
| `f3_null.py` | `F3_NULL.json` | **Optional-stopping drift-after-touch. The core result.** §4. |
| `f3_wick.py` | `F3_WICK.json` | Wick-vs-close arms and the overshoot-bias correction. §4.2. |
| `f3_fill.py`, `f3_fillbar.py` | `F3_FILL.json`, `F3_FILLBAR.json` | Fill-quality anatomy, order-type split, rollover fills, F1 reconciliation. §7. |
| `f3_levers.py` | `F3_LEVERS.json` | TRAIN-selected / TEST-priced ex-ante levers. §11.2. |

**Sources.** Sealed candidate rows `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`;
trade geometry `lane2_receipts/extract_geom.py` output; true-UTC M1
`lane-inputs-true-utc-hold-20260805/.../sources/bars/bridge_ftmo_m1_2026{01..07}`; ticks
`/Users/borr/GTOSActive/vps-ticks-20260726/` (broker wall clock, converted via
`src/utils/broker_clock`); spread model `src.research_infra.walkforward.quote_side.spread_for`.
