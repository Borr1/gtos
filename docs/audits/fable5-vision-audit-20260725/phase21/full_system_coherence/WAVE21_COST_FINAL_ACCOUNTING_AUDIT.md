# Wave 21 cost and final-accounting audit

Date: 2026-08-09

Lane: E — cost and final accounting

Code baseline: `01446b38390f4e3d1f15dc26da3848a7b3718e6b`

Retained comparator target: `875037f1bc787009c6020be82c3883d9fcf85fa8`

## Decision

The retained three-day comparator does **not** contain final all-in economics. It has 29
exit projections, 25 trade rows (23 numeric gross proxies), and zero validated
`post_lifecycle_component_cost` or accounting packets. Every trade row says
`close_side_all_in_cost_status=not_joined_in_replay_net_proxy_r`. Its numeric
`net_proxy_r` subtracts a pretrade forecast and remains diagnostic; it must not be
promoted to final economics.

Cost is nevertheless materially selection-moving in the retained comparator: 9,712 of
23,309 candidate occurrences (41.67%) have one of the three cost-owned raw Selector
reasons below. The evidence does **not** support relaxing the 0.20R ceiling. Spread and
commission are strongly coupled to stop geometry, the gate blocks more observed stops
than targets, and the retained pretrade model also contains three non-final authority
problems: constant-in-R slippage, maximum-horizon swap labelled as expected, and frozen
profile tick-value FX for non-USD per-lot commission. Current `src/costs` supplies
price-domain slippage, historical FX, and actual-elapsed post-lifecycle swap; it does not
yet supply an as-of expected-hold estimator, and the retained comparator did not consume
the current component authority.

One current-code arithmetic defect was reproduced and repaired: the post-lifecycle
assessor accepted an internally re-summed nonzero spread deduction even when validated
fill-anchored quote geometry declared the physical spread already embedded in gross.
The assessor now requires charged `spread_r == 0` while retaining nonzero observed spread
as attribution.

## Bound inputs

| Day | Stage-ledger SHA-256 | Authenticated compact-manifest SHA-256 |
|---|---|---|
| 2025-10-28 | `89762595a78e7d81003a2595c08e39d9dffb6d0c4bed2c2d0e7970bcbb4a7991` | `3fe9bbf2e556307690ae6d7de6dd3182e9cc9f412259fae47f595c8c66a988e3` |
| 2025-11-03 | `db84b4d7137b6da9d60741abca4ff069152a73dc89fc0e4243f82329e82711d8` | `f0b601bde76d21ba4c69bd654061c76c945bb8624196aacf63af626c96034c5f` |
| 2025-11-07 | `e135d297cee9631eec76d322a9864a3011941987151940d9b4d69dc4a9a9e835` | `97edaa49e3206742a5b656657c1d0825e2e33bf7545c9bfec7bc2d5c4cadefae` |

All three compact missed-row streams were exhausted through the repository's authenticated reader,
which verified the manifest authority root, shard bytes/hashes, frames, ordinals, raw
stream length, and raw stream hash. The run receipt binds effective profile
`operator_profile`, profile path
`config/profiles/operator_profile.yaml`, and the retained target commit above.

No new replay was run. All outcome-aware observations below are descriptive diagnostics
on retained rows, not setup validation and not a threshold-selection exercise.

## Cost-owned raw reasons and components

| Raw reason | Rows | Total R p50 / p90 | Spread p50 / p90 | Slippage p50 / p90 | Swap p50 / p90 | Commission p50 / p90 | Dominant component counts |
|---|---:|---:|---:|---:|---:|---:|---|
| `pretrade_cost_above_selector_v4_ceiling` | 6,773 | 0.2602 / 0.3824 | 0.1441 / 0.2595 | 0.0200 / 0.0200 | 0 / 0.1920 | 0.0547 / 0.1780 | spread 4,024; commission 1,459; swap 1,290 |
| `broker_net_pretrade_cost_packet_refused` | 2,206 | 0.5681 / 0.8187 | 0.1500 / 0.4137 | 0.0200 / 0.0200 | 0.3157 / 0.5832 | 0 / 0.4620 | swap 1,252; spread 557; commission 397 |
| `broker_net_admission_ev_negative_after_cost` | 733 | 1.0729 / 1.7170 | 0.2117 / 1.0452 | 0.0200 / 0.0200 | 0.4954 / 0.9404 | 0.3039 / 0.9518 | swap 401; spread 171; commission 161 |

Across the 9,712 rows, the occurrence-summed component shares are spread 41.75%, swap
28.94%, commission 24.55%, and slippage 4.76%. These sums measure gate pressure across
candidate occurrences; they are not portfolio costs and must not be added to trade P&L.

Removing one component in isolation, while preserving the 0.20 total ceiling, 0.35 spread
ceiling, and positive model EV, would move 5,553 rows for spread, 3,360 for commission,
2,276 for swap, and 1,282 for slippage out of the cost-owned class. This is a causal
diagnostic only; multiple retained component authorities are not yet cost-truth complete.

## Symbol decomposition

`Reject %` is cost-owned rows divided by all retained candidates for that symbol. Stop
distance is `abs(entry-stop) / entry * 10,000` and is comparable across price scales.

| Symbol | Rows | Reject % | Total R p50 | Stop bp p50 | Main interpretation |
|---|---:|---:|---:|---:|---|
| UK100 | 1,829 | 59.08% | 0.3466 | 3.93 | spread-led (58.0% of summed cost) |
| BTCUSD | 853 | 89.79% | 0.5134 | 14.67 | notional commission-led (74.7%) |
| SPX500 | 787 | 34.72% | 0.3014 | 2.91 | spread-led; tight geometry |
| NAS100 | 706 | 32.25% | 0.2862 | 3.29 | spread-led; source slippage is also material |
| USDCAD | 588 | 79.25% | 0.2820 | 3.80 | commission 48.8%, spread 38.2% |
| GER40 | 577 | 29.05% | 0.2680 | 3.13 | spread-led |
| CHFJPY | 567 | 77.78% | 0.2465 | 7.48 | spread-led; historical-FX per-lot commission applies |
| ETHUSD | 548 | 76.01% | 0.3594 | 27.03 | notional commission-led (62.2%) |
| GBPJPY | 513 | 85.93% | 0.3029 | 6.35 | spread-led; historical-FX per-lot commission applies |
| NZDUSD | 413 | 91.17% | 0.2660 | 10.02 | spread/commission; current slippage sample is measured zero |
| AUDJPY | 350 | 58.92% | 0.2864 | 7.94 | spread-led; historical-FX per-lot commission applies |
| AUDUSD | 337 | 51.22% | 0.2262 | 6.51 | spread/commission plus source slippage |
| US30_cash | 241 | 8.88% | 0.3469 | 6.55 | low reject rate; extreme tight-stop tail |
| EURJPY | 212 | 68.83% | 0.2804 | 5.46 | spread-led; historical-FX per-lot commission applies |
| EURGBP | 201 | 41.88% | 0.2854 | 4.57 | spread/commission; historical-FX per-lot commission applies |
| GBPUSD | 188 | 25.58% | 0.2425 | 4.29 | spread-led |
| XAGUSD | 164 | 67.77% | 0.3182 | 27.27 | spread-led (91.9%); current slippage source missing |
| JP225 | 149 | 13.13% | 0.3342 | 4.81 | spread plus source slippage |
| USDCHF | 144 | 30.13% | 0.2700 | 5.86 | spread/commission; historical-FX per-lot commission applies |
| EURUSD | 105 | 20.67% | 0.2576 | 3.26 | commission-led (49.8%) |
| USDJPY | 95 | 21.54% | 0.3718 | 4.74 | balanced; historical-FX per-lot commission applies |
| XAUUSD | 68 | 6.78% | 0.3368 | 7.89 | low reject rate; spread/commission tail |
| USOIL_cash | 42 | 35.90% | 0.3899 | 8.37 | swap/spread tail; current slippage source missing |
| UKOIL_cash | 35 | 21.08% | 0.2777 | 9.08 | swap/spread tail; current slippage source missing |

## Candidate-family decomposition

| Origin family | Rows | Reject % | Total R p50 / p90 | Stop bp p50 |
|---|---:|---:|---:|---:|
| `current_fvg_fill` | 5,113 | 38.38% | 0.3653 / 0.8653 | 4.11 |
| `current_ob_retest` | 2,857 | 44.68% | 0.2565 / 0.4103 | 7.03 |
| `current_breaker_re_entry` | 638 | 54.58% | 0.2982 / 0.4419 | 6.00 |
| `liquidity_sweep_reclaim` | 406 | 53.07% | 0.3596 / 0.8490 | 4.76 |
| `structural_distance_extreme` | 331 | 84.44% | 0.5876 / 1.2412 | 2.47 |
| `cross_asset_lead_lag` | 212 | 60.75% | 0.3943 / 0.7582 | 4.00 |
| `displacement_continuation` | 130 | 19.91% | 0.2616 / 0.4279 | 8.77 |
| `session_open_range_break` | 22 | 15.07% | 0.2305 / 0.2897 | 8.91 |
| `volatility_compression_expansion` | 2 | 2.70% | 0.4241 / 0.4532 | 12.08 |
| `regime_transition_break` | 1 | 2.17% | 0.2142 / 0.2142 | 18.32 |

## Same-market geometry examples

These pairs have the same day, symbol, origin family, and nearly identical implied spread
price. The cost change is therefore dominated by stop geometry, not a larger market
spread.

| Symbol/day | Tight stop -> total | Wider stop -> total | Cost ratio |
|---|---|---|---:|
| US30 2025-11-03 | 10.36 price / 2.17 bp -> 1.2530R | 144.21 / 30.46 bp -> 0.0324R | 38.72x |
| SPX500 2025-11-03 | 1.77 / 2.58 bp -> 1.0381R | 22.45 / 32.95 bp -> 0.0374R | 27.76x |
| NAS100 2025-11-03 | 7.54 / 2.91 bp -> 0.9854R | 63.84 / 24.39 bp -> 0.0421R | 23.41x |
| UK100 2025-11-03 | 2.33 / 2.41 bp -> 1.3885R | 5.97 / 6.15 bp -> 0.1631R | 8.51x |
| XAUUSD 2025-11-03 | 2.31 / 5.79 bp -> 0.4509R | 6.73 / 16.91 bp -> 0.0614R | 7.35x |

This is deliberate R arithmetic: price-domain execution cost divided by a smaller stop is
a larger fraction of risk. It is a geometry-quality problem when the stop itself is
malformed; it is not evidence that the cost ceiling should be relaxed.

## Outcome-aware gate diagnostic

| Cost reason | No fill | Ordered-tick NE | Stop | Target | Time stop | Other source gap |
|---|---:|---:|---:|---:|---:|---:|
| 0.20–0.45 ceiling | 5,399 | 544 | 475 | 170 | 185 | 0 |
| Packet refused | 1,534 | 365 | 204 | 74 | 26 | 3 |
| Negative after cost | 377 | 204 | 109 | 36 | 7 | 0 |

Across unambiguous target/stop rows, the gate blocked 280 targets at +2R and 788 stops at
-1R: -228R gross before time-stop and execution cost. Target share among target/stop is
26.36%, 26.62%, and 24.83% for the three groups. Thus the gate is directionally filtering
more observed losers than winners even though its component authority must be upgraded.
No-fill remains a separate lifecycle disposition: 17,830 across all three retained days
(6,563 on 2025-11-03), not an execution-cost component.

## Retained authority defects versus current cost truth

### Slippage

Every one of the 9,712 cost-owned retained rows uses exactly 0.02R from
`config.selected_cell_default_expected_slippage_r`. The retained engine therefore prices
slippage in R before stop geometry instead of using the reconciled price displacement.

Applying the current manifest-bound FTMO slippage authority to the same stop distances is
decidable for 7,409 rows and `NOT_EVALUABLE` for 2,303 rows across nine symbols. Among the
decidable rows, source-bound slippage is below 0.02R on 4,604 and above it on 2,805; median
is 0.00102R, p90 0.08815R, and the occurrence sum is 265.81R versus the retained 148.18R.
NAS100 alone averages 0.2160R. A blanket subtraction of 0.02R would therefore overcharge
many rows and dangerously undercharge others. Missing exact-account/profile symbol
slippage must remain NE.

### Forecast swap versus actual elapsed lifecycle

The retained pretrade engine obtains `holding_bars` from the dynamic time stop or the
configured `selected_cell_swap_cost_time_stop_bars`. The retained effective config has 32
bars at 15 minutes: a fixed eight-hour **maximum time-stop horizon**, passed to broker
rollover counting and emitted inside `expected_cost_r`. It is not an estimated holding
distribution.

Swap is positive on 3,333 cost-owned rows and is the dominant component on 2,943. The
authenticated missed-row streams contain counterfactual fill and close instants for 2,374
cost-owned rows. Of 686 with positive forecast swap and a known lifecycle, 669 crossed no
actual broker rollover. Restricting to 323 rows with numeric gross outcome, 309 crossed no
rollover (181 stops, 71 targets, 57 time stops); their retained forecast swap sums to
99.47R, and 188 would clear the 0.20/positive-net cost conditions if swap alone were zero.
Only 14 of those numeric rows crossed a rollover.

Example: the 2025-11-03 19:15 UTC USOIL cross-asset candidate forecast 2.5860R swap and
2.7757R total, filled at 19:16, stopped at 19:19, and crossed no rollover; cost excluding
forecast swap was 0.1897R. This proves maximum-horizon swap can be excessively conservative
for the observed lifecycle. It does **not** authorize an outcome-derived pretrade rule.
Required repair input is an as-of holding/survival estimator by symbol/family/session, or
an honestly named conservative-horizon field kept separate from expected cost. Final
accounting must use actual fill/exit elapsed time only.

### Commission and historical FX

The retained run binds FTMO Server 3 and broker-true commission schedules, but its legacy
packet converts cash-per-lot commission with profile `trade_tick_value/trade_tick_size`, a
modern snapshot. Current `src/costs` instead uses the last completed historical D1 FX rate
for every non-USD profit-currency `per_lot` row; zero and notional-bp R do not consume FX.

There are 2,082 cost-owned non-USD per-lot occurrences across AUDJPY, CHFJPY, EURGBP,
EURJPY, GBPJPY, USDCHF, and USDJPY. Recomputing only that commission term with current
historical FX changes their occurrence sum from 191.219R to 185.588R (-5.631R), with a
median ratio of 0.9649; 27 rows cross the 0.20/positive-net boundary in isolation. The
current source repair is correct, but the retained comparator must be re-costed before its
cost decisions can be called current truth.

### Spread and exact arithmetic

The retained M1 comparator subtracts its model spread once inside pretrade
`net_proxy_r`; it does not retain typed quote geometry proving whether gross already
contains physical spread. Therefore final spread accounting is NE, not a demonstrated
retained-row double charge. Complete retained missed-row component dictionaries preserve
the declared left-to-right component sum; trade projections round the scalar total and are
not complete cost packets.

Current post-lifecycle construction has the stronger contract: validated fill-anchored
bid/ask geometry attributes observed physical spread, charges zero additional spread, and
sums slippage + actual-elapsed swap + commission exactly once. The repaired assessor now
refuses a packet that puts attributed spread back into the charged slot even when the
caller re-sums `total_cost_r` to hide the mutation.

## Exact closure requirements

Before final economics can be numeric, each selected lifecycle needs a shared-stage-
validated fill/exit predecessor carrying trade/account/symbol/side, entry and exit UTC and
prices, stop distance, gross basis, and adjacency; hash-bound quote rows must prove whether
gross embeds spread. The final packet must then contain four finite source-backed
components in fixed order: charged spread (zero when embedded), source-bound expected
slippage with honest coverage, swap from actual elapsed broker rollovers, and date-correct
commission. Missing quote geometry, historical FX, slippage source, actual exit, or any
component remains `NOT_EVALUABLE`; no pretrade horizon/default may substitute.

No live, broker, VPS, launcher, selector threshold, scheduler, or config surface changed.
