# LANE l6 — the opportunity-cost ledger of the gate stack

**Wave 19 broad forensic. January 2026, true-UTC S0R0 diagnostic pool, n = 27,658.**
Every number below is measured. Scripts and JSON are beside this file; every table here is
reproduced in `l6_RESULT.json`.

---

## 0. Measurement contract (read before quoting any number)

Three different outcome currencies appear. They are not interchangeable.

| symbol | definition |
|---|---|
| `eng_gross` | the pool's own walked `gross_r = opportunity_net_proxy_r + cost_r`. **Contaminated**: 12.72 % of the pool (`born_past_stop`) was never takeable and books a mechanical −0.9948 (w0-capture). |
| `h_gross` | honest no-look-ahead first-touch walk **over the takeable set** — born state from `mkt_r_prev_close` (close of the M1 bar that closes AT the decision; bars are OPEN-stamped), fill = first bar `adv ≤ 0`, target = `policy_target_r`, stop = −1R, else marked at the 2 h horizon clipped to [−1, tgt]. Identical contract to `W0CAP2_NOLOOKAHEAD_FULL_V1`. |
| `h_all` | **the portfolio contract** — same walk, but computed over every non-past-stop row with an **unfilled limit booking 0 R and 0 cost** ("if it does not fill we simply do not trade"). This is the right currency for any gate whose refused set has a low fill rate. |

`h_net_corr73` = `h` minus the frozen cost with the spread limb divided by 7.3 (the measured
over-charge). Frozen cost is quoted where it matters.

Pool references, n = 27,658:

| measure | value |
|---|---|
| `eng_gross` mean | **−0.21750** R/trade |
| takeable n (not past-stop, filled) | **23,884** |
| `h_gross` mean | **−0.12744** R/trade, win 35.66 % |
| portfolio n (`h_all_n`) | **24,125** |
| `h_all` mean | **−0.12617** R/trade |
| `h_net_corr73` mean | **−0.30338** R/trade, total **−7,245.885 R** |
| pool fill rate | **99.0 %** of non-past-stop limits are touched inside the 2 h horizon |

Substrate: `l6_GATEFRAME_V1.jsonl.gz` (27,658 rows, built by `l6_build_gateframe.py`,
17 rows carry no decision anchor and are excluded from born-state splits).

---

## 1. THE HEADLINE — the layered stack is strictly dominated by its own first gate

Eight config-level gate predicates were reconstructed from source and evaluated
**independently on every row** (the pool's single-reason columns cannot do this — co-blockers
are not projected, D2). All 2⁸ = 256 gate subsets were enumerated (`l6_step4_sweep.py`).

| book | n | takeable | `h_gross` | `h_net_corr73` | win % |
|---|---:|---:|---:|---:|---:|
| no gates (whole pool) | 27,658 | 23,884 | −0.12744 | −0.30338 | 35.66 |
| **as-shipped 8-gate stack** | **2,986** | 2,840 | **−0.11062** | **−0.16266** | 38.87 |
| **`total_cost_r ≤ 0.15` ALONE** | **7,584** | 7,292 | **−0.07056** | **−0.12207** | 39.99 |

**Seven of the eight gates, acting together on top of the cost gate, subtract 0.04006 R/trade
of gross and 4,598 trades (60.6 %).** The best book at every subset size k = 1,2,3,4 is the
same 7,584-row book — because the EV gates are strict subsets of the cost gate and change
nothing.

Marginal value of each gate measured at the full stack (Δ `h_net_corr73` from keeping it):

| gate | Δ `h_net` from keeping it | trades it costs | verdict |
|---|---:|---:|---|
| `P2 total_cost_r > 0.15` | **+0.03235** | −971 | **earns its keep — the only one that does** |
| `P3 expected_net_r < 0` | +0.00000 | 0 | dead weight |
| `P4 expected_net_r < 0.10` | +0.00000 | 0 | dead weight |
| `P6 fill_prob < 0.45` | +0.00000 | 0 | dead weight |
| `P8 expected_net_r < 0.20` | +0.00000 | 0 | dead weight |
| `P7 fill_prob < 0.80` | **−0.00346** | −316 | net harmful |
| `P1 spread_r > 0.10` | **−0.00391** | −138 | net harmful |
| `P9 off_configured_session` | **−0.00923** | −2,435 | net harmful, and the largest by count |

Two further config gates **never fire at all**: `selector_v4_calibrated_min_probability = 0.58`
(config:810) and `scheduler_v4_..._dynamic_budget_min_probability = 0.58` (config:1001) block
**0 of 27,658** rows, because `candidate_probability`'s own minimum over the pool is 0.584298
(D7 — the belief layer is structurally incapable of saying no). They are inert by construction.

### 1.1 Co-blocking — the layering is total

Predicate level (8 independent predicates), rows tripping k of them:

| k | n | `h_gross` | `h_net_corr73` |
|---:|---:|---:|---:|
| 0 | 2,986 | −0.11062 | −0.16266 |
| 1 | 3,860 | −0.10543 | −0.17600 |
| 2 | 5,857 | −0.09538 | −0.22363 |
| 3 | 5,263 | −0.11005 | −0.24642 |
| 4 | 1,992 | −0.10458 | −0.25912 |
| 5 | 2,176 | −0.17321 | −0.42636 |
| 6 | 3,665 | −0.20913 | −0.62358 |
| 7 | 1,214 | −0.20213 | −0.58741 |
| 8 | 645 | −0.13692 | −0.50716 |

Unique blocks (rows this predicate alone kills):

| predicate | blocked | unique | unique share | `h_gross` of the unique rows |
|---|---:|---:|---:|---:|
| `P9_off_session` | 16,562 | 2,435 | 14.70 % | −0.08931 |
| `P2_total_cost_0p15` | 20,074 | 971 | 4.84 % | −0.17556 |
| `P7_sched_fill_floor_0p80` | 6,729 | 316 | 4.70 % | −0.08067 |
| `P1_spread_cap_0p10` | 17,259 | 138 | 0.80 % | −0.03275 |
| `P3_ev_negative` | 6,453 | **0** | 0.00 % | — |
| `P4_selector_min_ev_0p10` | 7,268 | **0** | 0.00 % | — |
| `P6_fill_floor_0p45` | 3,407 | **0** | 0.00 % | — |
| `P8_sched_min_ev_0p20` | 8,107 | **0** | 0.00 % | — |
| `P5_prob_floor_0p58` | 0 | 0 | — | — |
| `P10_sched_prob_0p58` | 0 | 0 | — | — |

**Six of ten predicate gates have exactly zero marginal effect.** Four block thousands of rows
that another gate has already killed; two never fire.

Enacted level (the pipeline's own reason strings, 16 gates, `L6_ENACTED_INTERACTION_V1.json`):
rows tripping k enacted gates — **0: 1 · 1: 20,583 · 2: 3,062 · 3: 2,556 · 4: 1,456**.
`cost_authority` uniquely blocks **20,448 of 20,448 (100 %)**; every other enacted gate is
0.0–1.9 % unique, and **nine of them are 0.0 % unique**: `displacement_veto`, `fill_floor_veto`,
`offsession`, `no_shadow_sleeve`, `marketable_guard`, `non_admission_sleeve`,
`signed_authority`, `src_required_fail_closed`, `daily_lockout`. Exactly **one** candidate in
the whole month is refused by no gate at all.

---

## 2. THE OPPORTUNITY-COST LEDGER — every gate, ranked by what it refused

### 2.1 Enacted gates (the pipeline's own reason strings)

Sorted by `h_gross` of the refused set. `vsPool` = how much better than the pool average the
refused candidates were. `1stEm` = the same measured on distinct setups only (`is_first_emission`
— w0-F1: 24.39 % of the pool is the same setup re-emitted every 15 min, 91.9 % of it in
`current_fvg_fill`).

| gate | n | takeable | `h_gross` | vsPool | `h_net_corr73` | total net R | 1stEm n | 1stEm `h_gross` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`signed_authority_invalid`** | 247 | 247 | **+0.23213** | +0.3596 | **+0.18224** | **+45.013** | 37 | **+0.27619** |
| **`numeric_confluence_structured_disagreement`** | 484 | 483 | **+0.15367** | +0.2811 | **+0.09922** | **+47.925** | 120 | +0.07569 |
| **`same_symbol_daily_loss_lockout`** | 55 | 54 | **+0.12887** | +0.2563 | **+0.08566** | **+4.626** | 21 | **+0.31696** |
| **`source_required_fail_closed`** | 168 | 166 | **+0.10325** | +0.2307 | **+0.06069** | **+10.074** | 62 | **+0.16655** |
| `marketable_limit_entry_guard` | 599 | 556 | −0.02856 | +0.0989 | −0.09584 | −53.286 | 599 | −0.02856 |
| `off_configured_session_entry_blocked` | 1,079 | 997 | −0.04160 | +0.0858 | −0.08872 | −88.457 | 736 | −0.05372 |
| `package_executable_authority_required_not_met` | 4,097 | 3,950 | −0.07788 | +0.0496 | −0.12822 | −506.478 | 3,097 | −0.09626 |
| `dynamic_router_refusal` | 739 | 731 | −0.08337 | +0.0441 | −0.13863 | −101.342 | 515 | −0.05938 |
| `fill_floor` veto | 1,445 | 1,410 | −0.08381 | +0.0436 | −0.13996 | −197.340 | 1,207 | −0.08331 |
| `source_required_hold` | 131 | 129 | −0.09025 | +0.0372 | −0.21263 | −27.429 | 131 | −0.09025 |
| `scheduler_vetoed_*` | 3,816 | 3,736 | −0.10595 | +0.0215 | −0.15924 | −594.916 | 3,369 | −0.09619 |
| `source_bound_router_refusal` | 3,743 | 3,576 | −0.10724 | +0.0202 | −0.15948 | −570.317 | 3,327 | −0.08714 |
| `displacement_quality` veto | 2,090 | 2,045 | −0.10810 | +0.0193 | −0.15985 | −326.895 | 1,974 | −0.09691 |
| `no_shadow_sleeve_match` | 786 | 775 | −0.10843 | +0.0190 | −0.15760 | −122.138 | 753 | −0.11881 |
| `cost_authority` | 20,448 | 16,956 | −0.14649 | **−0.0191** | −0.37303 | −6,325.179 | 16,056 | −0.14976 |
| `non_admission_sleeve_only` | 315 | 303 | −0.17131 | −0.0439 | −0.23182 | −70.242 | 315 | −0.17131 |
| `adaptive_replay_memory_guard` | 88 | 86 | −0.23755 | −0.1101 | −0.27528 | −23.674 | 29 | −0.27779 |
| `scheduler_rank_limited` | 15 | 14 | −0.30936 | −0.1819 | −0.36485 | −5.108 | 11 | −0.39266 |

**Only FOUR of the eighteen enacted gates refuse candidates that are worse than the pool
average**: `cost_authority` (−0.0191), `non_admission_sleeve_only` (−0.0439),
`adaptive_replay_memory_guard` (−0.1101) and `scheduler_rank_limited` (−0.1819) — and those
four are 20,866 of the 20,448+ refusals, i.e. the cost gate plus 418 rows. **The other fourteen
gates all refuse candidates that are better than what the system keeps.**

### 2.2 The four gates that refuse systematically POSITIVE candidates

Full-length names, source, and whether intent matches effect.

**(1) `package_positive_reduce_risk_signed_authority_invalid` — n = 247, +0.23213 R gross,
+0.18224 net, +45.013 R forgone. First emissions only: n = 37 at **+0.27619** gross,
62.16 % win, +0.22357 net (+8.272 R) — it survives deduplication.**

Source: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:80454-80480`. The
candidate has already been routed as `package_positive_reduce_risk_predecision_route_authorized`
(`:80444`); the scheduler then calls
`sign_materialized_scheduler_package_new_entry_authority` (`:19095`) and, if
`signed_reduce_row.get("package_new_entry_authority_valid") is not True`, writes
`scheduler_materialization_skip_reason = "package_positive_reduce_risk_signed_authority_invalid"`
and `continue`s (`:80474-80478`).

**Intent vs effect: this is not an economic judgment at all.** It is an attestation/signing
ceremony (the function it calls is 500+ lines of alias refreshing, `:19095-19700`), and it
refuses the best-performing cohort in the January pool. Composition: 245 of 247 are
`current_fvg_fill`, 225 of 247 XAUUSD.

**(2) `numeric_confluence_structured_disagreement` — n = 484, +0.15367 R gross, +0.09922 net,
+47.925 R forgone (the largest single line in the ledger). First emissions: n = 120 at +0.07569
gross, +0.01621 net.**

Source: `src/components/selector_v4.py:4644-4648` — `if confluence["mixed_count"]:` append
`"numeric_confluence_structured_disagreement"` to `reduce_reasons` (the friendlier alternative
label needs `package_numeric_disagreement_reduce_risk_authority_allowed`, `:4625-4642`, which
requires `not live_allowed` **and** `broker_cost_passed_for_package_router` **and**
`positive_predecision_package_edge` **and** a quality gate, plus two config keys).

**Intent vs effect: sign-inverted.** The system demotes a candidate when its own numeric
components DISAGREE. Measured, component disagreement is a **positive** predictor: +0.15367
against a pool of −0.12744, a +0.281 R/trade spread. The floors that would let such a candidate
through are the harshest in the config —
`scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_min_expected_net_r: 1.00`
and `..._min_probability: 0.85` (`config/agent_config.yaml:1009-1010`).

**(3) `same_symbol_daily_loss_lockout_after_closed_trade` — n = 55, +0.12887 R gross, +0.08566
net, +4.626 R forgone, 51.85 % win. First emissions: n = 21 at **+0.31696**.**

Source: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:1638-1647` — fires when a
prior trade on the **same symbol** closed **today** with `prior_net_r <=
same_symbol_daily_loss_lockout_max_prior_net_r` and `|min(0, prior_net_r)| >=
same_symbol_daily_loss_lockout_min_abs_prior_loss_r`.

**Intent vs effect: a revenge-trade guard that fires on mean reversion.** Intent (do not
re-enter a symbol that just lost) is a behavioural guard; the measured effect is that the
post-loss re-entry on the same symbol is the single highest-win-rate cohort in the pool
(54.35 % at the `final_blocker_class` level, n = 47). This is the one gate the swarm brief
already knew about (+0.242 R on 47 rows under the contaminated engine measure); under the
honest contract it is +0.12955 (`final_blocker_class`) / +0.12887 (`risk_finalizer_reason`).

**(4) `source_required_fail_closed_hold_not_executable_without_source` — n = 168, +0.10325 R
gross, +0.06069 net, +10.074 R forgone. First emissions: n = 62 at +0.16655.**

Source: `src/research_infra/v4_timewarp_simulated_live_research_loop.py:79943`. A
provenance/completeness fail-closed hold, not an economic test. Its `miss_reason` variants carry
their own override-failure lists; the largest of those, n = 12, is **+1.16560 R gross / +1.11881
net (75 % win, +13.426 R)** — the highest-value refusal line in the whole ledger:

```
scheduler_materialization_skipped_source_required_fail_closed_package_replay_override_failed:
  package_not_executable_source_bound_admission | expected_net_r_below_floor |
  probability_below_floor | signed_package_new_entry_authority_required_for_source_required_
  fail_closed_override | signed_package_new_entry_authority:signed_package_new_entry_
  authority_surface_missing
```

A second variant (n = 29) is +0.38670 gross / +0.32780 net (51.72 % win, +9.506 R), and a third
(n = 25) is +0.16388 / +0.12577 (+3.144 R).

### 2.3 The cohort is one cohort, not four

Overlap of the positive labels (`L6_POSITIVE_COHORT_V1.json`):

| pair | overlap |
|---|---:|
| numeric_disagreement ∩ signed_authority_invalid | 166 |
| numeric_disagreement ∩ `final_blocker_class = execution_fillability` | 245 |
| signed_authority_invalid ∩ execution_fillability | 242 |
| signed_authority_invalid ∩ reduce-risk action | 247 (total) |
| numeric_disagreement ∩ reduce-risk action | 473 of 484 |

| set | n | takeable | `h_gross` | `h_net_corr73` | total net R |
|---|---:|---:|---:|---:|---:|
| A only (numeric disagreement, not signed-invalid) | 318 | 317 | +0.08264 | +0.02705 | +8.574 |
| B only (signed-invalid, not numeric disagreement) | 81 | 81 | +0.11496 | +0.06990 | +5.662 |
| **A ∩ B** | **166** | 166 | **+0.28931** | **+0.23706** | **+39.351** |
| union of all six positive labels | 981 | 895 | +0.06508 | +0.01608 | +14.392 |
| union, first emissions only | 349 | 263 | +0.03185 | −0.02020 | −5.313 |

**Caveat stated plainly:** the union's edge does not survive deduplication (first emissions
−0.0202 net). What survives is the narrow B cohort (signed-authority-invalid, n = 37 distinct
setups at +0.27619) and the daily-lockout cohort (n = 21 distinct at +0.31696). Both are small.
Day positivity across the labels is 47.6–58.3 % of 12–21 trading days — real but not consistent.

---

## 3. THE FILL-PROBABILITY FLOOR IS SIGN-INVERTED — the largest mechanism in this lane

`execution_fill_probability` is computed at `src/components/poi_execution_lifecycle.py:162-190`:

```
limit_marketable = (LONG and entry >= current) or (SHORT and entry <= current)
if limit_marketable:  atr_component = risk_component = 0.92          # flat constant
else:                 atr_component = 1/(1 + d_atr**1.35)            # d = distance to limit
                      risk_component = 1/(1 + d_risk**1.10)
```

It is therefore a **monotone decreasing function of how far the entry sits from the market**,
with a flat 0.92 ceiling awarded to every already-marketable limit. Realized R runs the **other
way**. Measured over the pool, `m` = market-to-entry distance in R at the decision instant,
signed for the trade's own side (`mkt_r_prev_close`, no look-ahead; `m < 0` = the limit is
already through the market, `m ≤ −1` = past the stop and never takeable):

| `m` band | n | `h_all` R/trade | win % | t | mean `execution_fill_probability` |
|---|---:|---:|---:|---:|---:|
| `−1 < m < 0` (marketable) | 1,265 | **−0.31408** | — | **−11.571** | **0.92000** |
| `m = 0` (at market) | 14,911 | −0.12701 | 35.38 | −13.842 | 0.92022 |
| `0 < m ≤ 1` | 3,356 | −0.14019 | — | −7.548 | ~0.75 |
| `1 < m ≤ 2` | 2,422 | −0.09609 | — | −4.267 | ~0.44 |
| `m > 2` | 2,171 | **−0.02277** | — | −0.877 | ~0.28 |

Finer, non-past-stop: `(−1,−0.3] → −0.48946` (win 20.11 %), `(−0.3,−0.05] → −0.21305`,
`(−0.05,0] → −0.11319`, `m=0 → −0.12900`, `(0.3,1.0] → −0.13422`, `(1,3] → −0.08003`,
`(3,∞) → −0.00340` (win 38.57 %).

**Span from the worst band to the best is +0.486 R/trade, and the gate sorts on it backwards.**

Every fill floor in the config is therefore inverted. Measured (`L6_FILLPROB_V1.json`):

| floor | config | below n | below `h_gross` | above n | above `h_gross` | inversion |
|---|---|---:|---:|---:|---:|---:|
| 0.45 | `selector_v4_calibrated_min_fill_probability` (config:811) | 3,407 | −0.03487 | 24,099 | −0.14324 | **+0.10837** |
| 0.80 | `..._dynamic_budget_min_fill_probability` (config:1002) | 6,729 | −0.07854 | 20,777 | −0.14711 | **+0.06857** |
| 0.70 | `..._positive_predecision_off_session_min_fill_probability` (config:794) | 5,939 | −0.06596 | 21,567 | −0.14826 | **+0.08230** |
| 0.25 | `..._soften_selector_fill_floor_min_fill_probability` (config:798) | 1,033 | −0.02706 | 26,473 | −0.13228 | **+0.10522** |

The refused-side cohorts contain **zero** past-stop rows (0 at the 0.45 floor, 1 at the 0.80
floor), so this is not the w0-capture artifact reappearing.

Decile table of `execution_fill_probability` (only four buckets exist — 20,010 rows sit at
exactly 0.92, the marketable constant):

| bucket | n | mean P | fill % | `h_gross` | `h_all` | win % | median \|entry dist\| R | mean `spread_r` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [0.0401, 0.3932) | 2,750 | 0.2716 | 100.0 | **−0.04029** | −0.04029 | 41.12 | 2.54882 | 0.64718 |
| [0.3932, 0.6556) | 2,751 | 0.5191 | 100.0 | −0.06163 | −0.06163 | 38.95 | 1.20738 | 0.79016 |
| [0.6556, 0.92) | 1,995 | 0.7747 | 99.9 | **−0.19320** | −0.19301 | 31.66 | 0.48450 | 0.93465 |
| [0.92, 0.95] | 20,010 | 0.9207 | 98.55 | −0.14560 | −0.14350 | 34.66 | 0.00000 | 0.48099 |

Inverting the gate — blocking `P ≥ 0.92` instead of `P < 0.45` — keeps 7,648 rows at −0.08850
against 20,010 blocked at −0.14560: a **+0.05710** R/trade discrimination, where the shipped
floor's is **−0.10794**.

**Why 100 % of far limits fill inside 2 hours:** the risk distances are tiny. Median
`risk_distance / entry_price` is 0.09–0.33 % across the bands, so "3 R away" is ~0.1–0.3 % of
price. Median time to fill in the `m > 3` cohort is **62 minutes** (quartiles 36 / 89), not
bar 1 — these are genuine retrace fills, not instant ones. Example
`broadorigin_69fa1abd62949b698ed44fe8` (JP225 SHORT, m = 6.2797, risk_distance 20.54 on a
50,694 price, fill bar 94).

### 3.1 The marketable penalty replicates in 8 of 8 symbols and 3 of 3 families

First, a substrate fact nobody has recorded: **only three of the ten families ever emit an
entry that is not at the market.** `liquidity_sweep_reclaim` (4,475), `displacement_continuation`
(4,465), `cross_asset_lead_lag` (2,083), `structural_distance_extreme` (1,993),
`session_open_range_break` (987) and `volatility_compression_expansion` (605) are **100 % at
market** (`m = 0`). The limit-order contract exists only for `current_fvg_fill`,
`current_breaker_re_entry` and `current_ob_retest`.

Within-family portfolio R (n / mean / t), by `m` band (`L6_WITHIN_GROUP_V1.json`):

| family | marketable (`−1<m<0`) | at market | `0<m≤1` | `1<m≤2` | `m>2` |
|---|---|---|---|---|---|
| `current_fvg_fill` | 936 / **−0.274** / −9.2 | 6 / −0.493 | 2,691 / −0.174 / −8.4 | 1,702 / −0.146 / −5.2 | 1,800 / −0.011 / −0.4 |
| `current_breaker_re_entry` | 200 / **−0.463** / −5.8 | — | 241 / −0.148 / −2.0 | 204 / +0.124 / +1.5 | 148 / +0.130 / +1.4 |
| `current_ob_retest` | 129 / **−0.371** / −4.0 | — | 424 / +0.080 / +1.6 | 516 / −0.019 / −0.5 | 223 / −0.217 / −3.8 |

Within-symbol (n / mean), top 8 by count:

| symbol | marketable | at market | `0<m≤1` | `1<m≤2` | `m>2` |
|---|---|---|---|---|---|
| XAUUSD | 78 / **−0.286** | 729 / −0.125 | 395 / −0.144 | 407 / −0.228 | 720 / +0.103 |
| UK100 | 109 / **−0.493** | 645 / −0.234 | 254 / −0.252 | 206 / +0.101 | 186 / −0.231 |
| SPX500 | 225 / **−0.198** | 655 / −0.142 | 435 / −0.171 | 222 / −0.063 | 180 / −0.049 |
| NAS100 | 195 / **−0.439** | 673 / −0.153 | 304 / −0.423 | 161 / −0.460 | 150 / −0.432 |
| US30_cash | 106 / **−0.515** | 684 / −0.130 | 301 / −0.136 | 198 / −0.226 | 189 / −0.195 |
| GBPUSD | 14 / −0.321 | 706 / −0.217 | 29 / −0.662 | 48 / −0.010 | 26 / +0.319 |
| GER40 | 109 / **−0.340** | 615 / −0.120 | 294 / +0.131 | 200 / +0.240 | 181 / −0.088 |
| JP225 | 76 / **−0.250** | 522 / −0.166 | 279 / −0.177 | 210 / +0.045 | 196 / +0.187 |

**The marketable band is the worst or statistically tied-worst band in 8 of 8 symbols and 3 of
3 eligible families.** It is not a composition artifact. The far end (`m > 2`) is **not**
robust — positive on XAUUSD/JP225/GBPUSD, negative on UK100/NAS100/US30/GER40/SPX500 — which is
why §4.3 declines to call it an edge.

Value of the rule *"never send an order whose limit is already through the market"*: it removes
**4,781 rows (17.28 % of the pool)** — 3,516 `born_past_stop` (already priced by w0-capture at
+0.11332 R/trade on the engine measure) plus **1,265 marketable at −0.31408 R/trade,
t = −11.571, −397.31 R over January**. Removing just the marketable 1,265 moves the portfolio
book from −0.12617 (n = 24,125) to **−0.11577** (n = 22,860) = **+0.0104 R/trade**, for free
and with no look-ahead.

---

## 4. THE COUNTERFACTUAL FRONTIER

### 4.1 Removing the shipped gates (8 predicates, exhaustive 2⁸)

Best book at each active-gate count (takeable ≥ 250):

| k active | n | takeable | `h_gross` | `h_net_corr73` | gates |
|---:|---:|---:|---:|---:|---|
| 0 | 27,658 | 23,884 | −0.12744 | −0.30338 | — |
| **1** | **7,584** | 7,292 | **−0.07056** | **−0.12207** | `P2 total_cost` |
| 2 | 7,584 | 7,292 | −0.07056 | −0.12207 | `P2` + `P8` (P8 adds nothing) |
| 3 | 7,584 | 7,292 | −0.07056 | −0.12207 | `P2 + P4 + P8` |
| 4 | 7,584 | 7,292 | −0.07056 | −0.12207 | `P2 + P3 + P4 + P8` |
| 5 | 4,011 | 3,856 | −0.07329 | −0.12497 | + `P9 off_session` |
| 6 | 3,827 | 3,681 | −0.07836 | −0.13057 | + `P1 spread_cap` |
| 7 | 5,421 | 5,139 | −0.10109 | −0.15343 | + both fill floors, − off_session |
| 8 | 2,986 | 2,840 | −0.11062 | −0.16266 | **as shipped** |

Monotone degradation from k = 1 to k = 8. The frontier is: **one gate.**

### 4.2 Rebuilding the stack on the measured sign of each axis

In-sample on January by construction — a mechanism demonstration, not an admission claim.
Portfolio contract (`h_all`, unfilled = 0 R):

| stack | n | `h_all` | `h_all` net@corr73 | win % | days+ | 1stEm n | 1stEm `h_all` |
|---|---:|---:|---:|---:|---:|---:|---:|
| none | 24,125 | −0.12617 | −0.30035 | 35.66 | 4.8 % | 18,390 | −0.12890 |
| **as-shipped 8 gates** | 2,880 | −0.10909 | −0.16040 | 38.87 | **14.3 %** | 2,779 | −0.10474 |
| cost only | 7,353 | −0.06997 | −0.12106 | 39.99 | 23.8 % | 5,858 | −0.08635 |
| cost + block marketable (`m < 0`) | 7,087 | −0.06392 | −0.11541 | 40.23 | 19.0 % | 5,780 | −0.08283 |
| block marketable only | 22,860 | −0.11577 | −0.29152 | 36.11 | 4.8 % | 17,964 | −0.12314 |
| require `m ≥ 0.3` only | 6,980 | −0.08630 | −0.28655 | 37.77 | 19.0 % | 2,861 | −0.09867 |
| require `m ≥ 1.0` only | 4,593 | −0.06143 | −0.25788 | 38.80 | 42.9 % | 1,857 | −0.07366 |
| **cost + require `m ≥ 0.3`** | 1,895 | **+0.00732** | −0.04373 | 42.22 | 47.6 % | 803 | −0.02461 |
| **cost + require `m ≥ 1.0`** | 1,336 | **+0.01354** | −0.03917 | 41.92 | 52.4 % | 562 | **+0.01159** |
| cost + `m ≥ 1.0` + off-session block | 659 | **+0.09705** | **+0.04251** | 43.40 | 52.4 % | 310 | −0.03553 |
| corrected spread cap + block marketable | 18,365 | −0.09268 | −0.21559 | 37.61 | 4.8 % | 15,141 | −0.10666 |
| all 8 candidate gates | 659 | +0.09705 | +0.04251 | 43.40 | 52.4 % | 310 | −0.03553 |

**The only gross-positive book that survives deduplication is `total_cost_r ≤ 0.15` AND
`m ≥ 1.0R`: +0.01354 R/trade on 1,336 candidates, +0.01159 on 562 distinct setups, 52.4 % of
21 days positive.** Its net at corrected cost is still **−0.03917** — the residual cost eats
the gross edge. The 659-row book that is net-positive (+0.04251) does **not** survive
deduplication (−0.03553 on 310 distinct setups) and should not be quoted as an edge.

### 4.3 Significance of the distance axis (portfolio contract, `L6_SIGNIF_V1.json`)

| cohort | n | mean R | sd | t | total R |
|---|---:|---:|---:|---:|---:|
| whole pool | 24,125 | −0.12617 | 1.1152 | −17.572 | −3,043.80 |
| marketable, non-past-stop (`−1 < m < 0`) | 1,265 | **−0.31408** | 0.9654 | **−11.571** | −397.31 |
| at market (`m = 0`) | 14,911 | −0.12701 | 1.1205 | −13.842 | −1,893.88 |
| `0 < m ≤ 1` | 3,356 | −0.14019 | 1.0760 | −7.548 | −470.47 |
| `1 < m ≤ 2` | 2,422 | −0.09609 | 1.1083 | −4.267 | −232.72 |
| `m > 2` | 2,171 | −0.02277 | 1.2099 | −0.877 | −49.43 |
| cost-passed, marketable | 266 | −0.23118 | 0.9295 | −4.056 | −61.49 |
| cost-passed, at market | 4,953 | −0.09205 | 0.9963 | −6.502 | −455.91 |
| cost-passed, `m > 1` | 1,336 | +0.01354 | 1.1740 | +0.422 | +18.09 |
| **cost-passed, `m > 2`** | **680** | **+0.10466** | 1.2568 | **+2.172** | **+71.17** |
| cost-passed, `m > 2`, first emissions | 199 | −0.00562 | 1.0009 | −0.079 | −1.12 |

The negative end is certain (t = −11.6). The positive end is not: the cost-passed `m > 2` book
is +0.105 at t = 2.17 but collapses to −0.006 on 199 distinct setups, and 563 of its 680 rows
are XAUUSD `current_fvg_fill` — the pseudo-replicated family. **Report the marketable end as
the finding; the far end is "no longer negative", not "positive".**

Day means, cost-passed `m > 2` (21 days, 12 positive): 0.343, 0.354, 0.332, 0.473, −0.608,
−0.237, 0.314, 0.155, 0.703, −0.243, −0.016, 1.180, −0.150, −0.389, −0.280, 0.085, 0.053,
0.557, −0.197, −0.188, 0.340.

---

## 5. THE EV GATE IS A COST GATE WEARING A DIFFERENT NAME

`src/components/selector_v4.py:3812-3832`:

```
broker_net_admission_ev = min( expectancy_r,
                               broker_net_expectancy_r,
                               stress_expectancy_r,
                               probability_thesis_ev_after_cost - total_cost )
if broker_net_admission_ev < 0: hard_reject "broker_net_admission_ev_negative_after_cost"
```

It is a **min over up to four estimators**: every additional estimator is another independent
chance to reject, and only the cost-subtracted members can go negative. `candidate_ev_r`
(= `expectancy_r`, an exact duplicate column, D4) has a **minimum of +0.398495 over all 27,658
rows and is never negative** (D7). So all 6,453 EV rejections are produced by the cost limb —
and it blocks **zero** rows the cost gate has not already blocked (§1.1).

`P3_ev_negative` is nonetheless the sharpest *discriminator* of the ten: the rows it flags are
−0.23364 against a kept set of −0.09806, a **+0.13558** spread. That discrimination is
real but redundant — it is `spread_r` in disguise, and `spread_r` is R-denominated, so a high
`spread_r` means a **tight stop relative to the instrument's spread**. The EV gate is
accidentally measuring stop-tightness, which is a genuine loss predictor. That is why the cost
gate earns its keep while its four EV echoes do not.

Discrimination of each predicate (kept `h_gross` − blocked `h_gross`):

| predicate | blocked | blocked `h_gross` | kept | kept `h_gross` | discrimination |
|---|---:|---:|---:|---:|---:|
| `P3_ev_negative` | 6,453 | −0.23364 | 21,205 | −0.09806 | **+0.13558** |
| `P4_selector_min_ev_0p10` | 7,268 | −0.20824 | 20,390 | −0.10104 | +0.10720 |
| `P8_sched_min_ev_0p20` | 8,107 | −0.19962 | 19,551 | −0.09957 | +0.10005 |
| `P2_total_cost_0p15` | 20,074 | −0.15244 | 7,584 | −0.07056 | +0.08188 |
| `P1_spread_cap_0p10` | 17,259 | −0.15696 | 10,399 | −0.08295 | +0.07401 |
| `P9_off_session` | 16,562 | −0.12316 | 11,096 | −0.13363 | **−0.01047** |
| `P7_sched_fill_floor_0p80` | 6,729 | −0.07854 | 20,929 | −0.14657 | **−0.06803** |
| `P6_fill_floor_0p45` | 3,407 | −0.03487 | 24,251 | −0.14281 | **−0.10794** |

A corrected-spread cap at the same 0.10 R threshold (`spread_r / 7.3 > 0.10`) blocks 5,854 rows
at −0.21434 and keeps 21,804 at −0.10585 — discrimination **+0.10849**, better per refused row
than the frozen cap's +0.07401, on 2.9× fewer refusals.

---

## 6. OFF-SESSION: 16,562 candidates for 0.01 R of signal

`route_session == "off_configured_session"` covers **16,562 rows (59.88 %)** — the largest
population any gate touches. Its discrimination is **−0.01047**: off-session candidates are
*marginally better* than on-session ones. The pipeline only enacts the block on **1,079** of
them (`admission_quality_off_configured_session_entry_blocked`,
`selector_v4.py:2556/4412`), and those 1,079 are **+0.0858 R/trade better than the pool**
(−0.04160 vs −0.12744). Removing the predicate from the full stack is worth −0.00923 R/trade
and 2,435 trades.

The one exception: within the cost-passed book, adding the off-session block to
`cost + m ≥ 1.0` moves 1,336 rows at +0.01354 to 659 rows at +0.09705. That is a real
interaction and it is also where deduplication kills the result (§4.2), so it is filed as a
question for wave 2, not a recommendation.

---

## 7. WHAT EARNS ITS KEEP — stated for the record

The owner's hypothesis is that layered gates suppress the system. Measured, it is **mostly but
not entirely true**, and the honest exceptions are:

1. **`total_cost_r ≤ 0.15` earns its keep.** +0.03235 R/trade marginal at the full stack, +0.08188
   discrimination, and it is the only gate whose removal makes the book worse. It costs 971
   uniquely-blocked candidates at −0.17556.
2. **`non_admission_sleeve_only` (n = 315, −0.17131), `adaptive_replay_memory_guard` (n = 88,
   −0.23755) and `scheduler_rank_limited` (n = 15, −0.30936)** all refuse candidates worse than
   the pool. They are small but correctly signed.
3. **The `marketable_limit_entry_guard` is correctly signed in direction but far too narrow.**
   It refuses 599 rows at −0.02856 — better than the pool, so on its face harmful — but §3 shows
   the whole marketable population (`m < 0`, 4,781 rows including 3,516 past-stop) is the worst
   cohort in the pool at −0.31408 excluding past-stop. The guard is aimed at the right thing and
   catches 599 of 4,781.

Everything else in the stack is either redundant (six predicate gates with zero marginal effect,
nine enacted gates with zero unique blocks), inert (two probability floors that can never fire),
or inverted (four fill-probability floors, and the two authority/attestation gates in §2.2).

---

## 8. Artifacts

| file | contents |
|---|---|
| `l6_build_gateframe.py` → `l6_GATEFRAME_V1.jsonl.gz` | 27,658 rows: every gate field + honest walk + born state |
| `l6_lib.py` | shared stats (`h_gross`, `h_all`, `h_net_corr73`) |
| `l6_step1_enumerate.py` → `L6_GATE_ENUM_V1.json` | all 35 gate fields × every distinct value × full outcome block |
| `l6_step2_cohort.py` → `L6_POSITIVE_COHORT_V1.json` | positive-refusal cohort, overlaps, per-day, per-family, per-symbol |
| `l6_step3_predicates.py` → `L6_PREDICATE_V1.json` | 10 independent predicates, co-blocking, unique blocks, containment, greedy frontier |
| `l6_step4_sweep.py` → `L6_SWEEP_V1.json` | exhaustive 2⁸ gate-subset books, marginals, enacted-gate ledger |
| `l6_step5_fillprob.py` → `L6_FILLPROB_V1.json` | fill-probability deciles, all four floors, entry-distance table |
| `l6_step6_constructive.py` → `L6_CONSTRUCTIVE_V1.json` | rebuilt-stack sweep, named stacks, day positivity, first-emission |
| `L6_MLADDER_V1.json`, `L6_SIGNIF_V1.json`, `L6_ENACTED_INTERACTION_V1.json` | distance ladder, t-stats, enacted co-blocking |
| `l6_RESULT.json` | every table in this document, machine-readable |
