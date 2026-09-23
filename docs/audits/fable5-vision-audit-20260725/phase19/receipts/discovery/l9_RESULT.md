# Lane l9 — does the allocator pick the right trades?

**Population.** `w0_WORKING_SET.jsonl.gz` (CJ_RECLOCKED_S0R0, January 2026, true UTC, 27,658 rows)
joined on `(candidate_id, decision_time_utc)` to `w0cap2_DECISION_ANCHOR_V1.jsonl.gz`. The anchor's
`mkt_r_prev_close` reproduces wave-0's born-state census **exactly** — at_limit 14,911 / resting 7,949 /
past_stop 3,516 / marketable 1,265 — so `takeable = born_state != past_stop` (n = 24,108) is the clean
population used throughout.

**Outcome measure.** `fill_honest_walk_r` — the first-touch 2R/−1R walk that REQUIRES the entry limit
to be touched before the trade exists (w0's `require_fill=True`). `gross_r` (the pool's own fill-blind
diagnostic score) and `plain_walk_r` (fill-BLIND first touch) are reported alongside because W0-F2
established the fill-blind convention manufactures +0.2776 R/trade of fiction. **A conservative
"zero-neither" variant** is reported for every headline: trades unresolved at the 2-hour wall score
exactly 0.0 instead of their mark. Where the two disagree, both are given.

Scripts: `l9_lib.py`, `l9_01_rank.py` … `l9_14_floorrobust.py` in this directory.
Machine artifact: `l9_RESULT.json` (merges all 16 sub-artifacts).

---

## 0. HEADLINE

**The system carries a hard configured minimum on `execution_fill_probability` — 0.45 in the selector
(`config/agent_config.yaml:811`) and 0.80 in the scheduler's dynamic budget
(`config/agent_config.yaml:1002`) — and the population it refuses is measurably BETTER than the
population it keeps, at every floor level, in the same decision cycles.**

At the 0.45 floor, over the 24,012 takeable candidates carrying a fill probability:

| | n | fill-honest R/trade | zero-neither R/trade |
|---|---:|---:|---:|
| **REFUSED** (fp < 0.45) | 3,400 | **−0.0349** | −0.1291 |
| **KEPT** (fp ≥ 0.45) | 20,612 | **−0.1416** | −0.2160 |
| **delta (refused − kept)** | | **+0.1067**  (t = +5.23) | **+0.0868** |

Under first-emission dedup (which removes W0-F1's 24.4 % pseudo-replication) the delta is
**+0.0774 R/trade, t = +2.91** (zero-neither +0.0349). At the 0.80 scheduler floor: **+0.0665, t = +4.14**
(dedup +0.0565, t = +2.53).

The mechanism is not subtle: `execution_fill_probability` is 0.92 whenever the entry price is at or
through the decision price (`src/components/poi_execution_lifecycle.py:162-176` — an inclusive
`entry >= current` / `entry <= current`), and a distance-scaled value below that. **A low fill
probability means a genuine passive limit sitting away from the market.** The floors therefore delete
the passive-limit book and keep the market-order book. The allocator's own objective then multiplies by
the same quantity, tilting the ranking the same wrong way (§3).

---

## 1. The structural limit that constrains this whole lane, stated first

**The pool contains ZERO selected-and-kept candidates.** `scheduler_selection_disposition` census over
all 27,658 rows:

| disposition | n |
|---|---:|
| `candidate_materialization_skipped_before_scheduler` | 23,563 |
| `candidate_generated_not_scheduler_selected` | 3,899 |
| `scheduler_preselected_then_rejected_by_finalizer` | 196 |
| *selected and kept* | **0** |

3,899 + 196 = 4,095 = `scheduler_option_materialized` exactly. The diagnostic pool is built by
`v4_timewarp_simulated_live_research_loop.py:28122-28146`, which requires `not headline_r_scoreable`,
and `headline_r_scoreable = execution_bound_headline_eligible and net_proxy_r is not None`
(`:28122-28130`). Anything that reached execution-bound headline scoring is excluded **by construction**.

**A literal "selected vs rejected at the same contention point" comparison is therefore impossible
from this asset.** What IS available, and is used instead, is the allocator's own complete preference
order: `risk_finalizer_rank` is **non-null on 27,658 / 27,658 rows, unique within every one of the 1,969
decision cycles, and 0 cycles have duplicate ranks.**

**How much of the ranked universe we can see.** Summing `max(rank)` per cycle gives a universe of
**142,917** against 27,658 visible rows — **19.35 % visible, 115,259 implied missing**. Visibility by
rank position:

| rank | present | missing | visible % |
|---:|---:|---:|---:|
| 1 | 1,153 | 816 | **58.6** |
| 2 | 915 | 1,054 | 46.5 |
| 3 | 748 | 1,221 | 38.0 |
| 4 | 637 | 1,331 | 32.4 |
| 5 | 506 | 1,462 | 25.7 |
| 10 | 356 | 1,603 | 18.2 |
| 20 | 392 | 1,555 | 20.1 |
| 40 | 263 | 1,661 | 13.7 |

Visibility is **highest at the top of the allocator's order and flat at ~18 % below rank 6**. That is
the opposite of what "the top pick was executed and therefore removed" predicts, so the missing mass is
dominated by rows that failed the `opportunity_net_proxy_r is not None` scoreability leg, not by
executions. 1,969 cycles, median 13 visible candidates, max 61; 99.97 % of rows sit in a cycle with at
least one competitor.

---

## 2. Lane item 2 — `risk_finalizer_rank` vs realized R (full table)

Absolute rank buckets, all rows and takeable-only. `gross` = pool's own score, `honest` =
`fill_honest_walk_r`, `plain` = fill-blind walk (shown to expose the fiction), `past%` = share of the
born-past-stop artifact, `cost` = mean `cost_r`.

**ALL 27,658**

| rank | n | gross | plain | honest | win % | full-stop % | past % | cost_r |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,153 | −0.1460 | −0.0283 | −0.1441 | 41.0 | 46.0 | 5.0 | 0.116 |
| 2 | 915 | −0.1631 | −0.0499 | −0.1952 | 38.8 | 46.7 | 7.5 | 0.114 |
| 3 | 748 | −0.1104 | +0.0503 | −0.1147 | 42.1 | 44.4 | 7.1 | 0.138 |
| 4 | 637 | −0.1241 | +0.1323 | −0.1131 | 41.4 | 43.6 | 4.1 | 0.169 |
| 5 | 506 | −0.0335 | +0.1463 | −0.0373 | 44.3 | 40.5 | 1.6 | 0.228 |
| 6–10 | 1,979 | −0.1506 | +0.0623 | −0.1825 | 38.5 | 49.6 | 5.2 | 0.386 |
| 11–20 | 3,804 | −0.2513 | −0.0861 | −0.2664 | 31.5 | 59.1 | 17.7 | 0.573 |
| 21–40 | 6,121 | −0.2239 | +0.0140 | −0.2615 | 32.1 | 57.1 | 15.5 | 0.857 |
| 41+ | 11,795 | −0.2454 | +0.0960 | −0.2586 | 34.2 | 55.6 | 13.4 | 0.813 |

**TAKEABLE (past-stop removed), n = 24,108**

| rank | n | gross | plain | honest | win % | full-stop % | cost_r |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,095 | −0.1008 | +0.0204 | −0.1015 | 43.2 | 43.1 | 0.117 |
| 2 | 846 | −0.0949 | +0.0276 | −0.1296 | 42.0 | 42.3 | 0.112 |
| 3 | 695 | −0.0426 | +0.1261 | −0.0515 | 45.3 | 40.1 | 0.138 |
| 4 | 611 | −0.0868 | +0.1805 | −0.0754 | 43.2 | 41.2 | 0.170 |
| 5 | 498 | −0.0180 | +0.1647 | −0.0219 | 45.0 | 39.6 | 0.229 |
| 6–10 | 1,877 | −0.1045 | +0.1200 | −0.1381 | 40.5 | 46.9 | 0.380 |
| 11–20 | 3,131 | −0.0903 | +0.1103 | −0.1087 | 38.3 | 50.4 | 0.581 |
| 21–40 | 5,174 | −0.0819 | +0.1995 | −0.1263 | 38.0 | 49.3 | 0.877 |
| 41+ | 10,198 | −0.1297 | +0.2646 | −0.1448 | 39.5 | 48.7 | 0.821 |

**The rank is NOT monotone in outcome.** Rank 2 (−0.1296 honest) is worse than rank 5 (−0.0219). Ranks
1–5 span −0.0219 to −0.1296 with no ordering. The whole informative content is a level shift of about
0.04 R/trade between the top handful and everything below.

**Within-cycle rank quintiles** (controls for group size; cycles with ≥ 4 candidates):

| quintile | n | gross | honest | plain | cost_r | risk-dist % | mean abs rank |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q1 (best rank) | 5,503 | −0.0791 | **−0.0936** | +0.0952 | 0.327 | 0.2882 | 7.0 |
| Q2 | 4,778 | −0.1188 | −0.1423 | +0.1495 | 0.668 | 0.2108 | 20.5 |
| Q3 | 4,776 | −0.1230 | **−0.1536** | +0.1467 | 1.031 | 0.1661 | 37.3 |
| Q4 | 4,778 | −0.0950 | −0.1146 | +0.2182 | 0.930 | 0.1695 | 57.3 |
| Q5 (worst rank) | 4,060 | −0.1064 | −0.1313 | +0.3869 | 0.351 | 0.1992 | 74.9 |

U-shaped, not monotone. Q5 beats Q3 by 0.022 R. `cost_r` is inverted-U across the quintiles (0.33 →
1.03 → 0.35), which kills the tempting "the rank is just a cost sort" story.

**Spearman, within cycle, demeaned by cycle:**

| target | ALL | TAKEABLE |
|---|---:|---:|
| gross_r | −0.0466 | −0.0276 |
| fill_honest_walk_r | −0.0509 | **−0.0320** (z = −5.0) |
| plain_walk_r | +0.0172 | +0.0419 |

Negative rho = correct direction (lower rank number → higher R). So the rank is **weakly correct on the
honest measure and weakly ANTI-correct on the fill-blind one** — which is itself a warning that anyone
who evaluated this ranker against `plain_walk_r`-style scoring would have concluded it was backwards.

---

## 3. Lane item 5 — what the allocator optimises, from source, vs what predicts outcome

### 3.1 The objective, exactly

`src/research_infra/v4_timewarp_simulated_live_research_loop.py:41834-41842` sorts every cycle's options
by

```
key = ( authority_priority_tier          ASC     (:41646-41672)
      , -expected_transfer_score         DESC    (:41673-41741)
      , -score                           DESC
      , -(action_class != "zero_trade")
      , scheduler_preserved_rank         ASC )
```

and stamps position as `risk_finalizer_rank` (`:41846-41849`). The transfer score is (`:41736-41741`):

```
transfer_score = max(0.0, expected_net_r)
               * clamp(probability, 0, 1)
               * clamp(fill_probability, 0, 1)
               * clamp(source_completeness, 0, 1)
```

Four measured properties of that expression on this pool:

1. **`max(0.0, ·)` collapses a quarter of the universe to a tie.** 6,453 rows (23.33 %) have
   `expected_net_r ≤ 0` and 6,533 (23.62 %) have `transfer_score` exactly 0.0. For those the allocator
   expresses **no preference at all** and falls through to `score` and then to generation order.
2. **`expected_net_r` is a contaminated input.** It is gross EV minus the frozen cost, and `spread_r` is
   85.08 % of that cost and is over-charged 7.3–8.5× (w0-dictionary D1/D8). The allocator's primary
   ordering key therefore inherits the single largest known measurement error in the estate.
3. **`source_completeness` is 1.0 on 27,658 / 27,658 rows** — a constant factor, contributing nothing.
4. **`fill_probability` is anti-predictive** (§4). Multiplying by it makes the objective worse than its
   own first factor.

### 3.2 The objective is worse than its own first factor, and worse than a coin flip inside its own domain

Within-cycle Spearman against `fill_honest_walk_r`, TAKEABLE:

| quantity | rho | z |
|---|---:|---:|
| `expected_net_r` (factor 1, unclipped) | **+0.0656** | +10.2 |
| `max(0, expected_net_r)` (factor 1, clipped) | +0.0631 | +9.8 |
| **`transfer_score` (the full objective)** | **+0.0478** | +7.4 |
| `candidate_probability` (factor 2) | +0.0287 | +4.4 |
| `execution_fill_probability` (factor 3) | **−0.0434** | −6.7 |
| `source_completeness` (factor 4) | −0.0098 | −1.5 |
| `risk_finalizer_rank` (the emitted order) | −0.0320 | −5.0 |

Per-cycle argmax selection, TAKEABLE, `fill_honest_walk_r`, 1,949 cycles:

| selection rule | mean R/trade |
|---|---:|
| **argmin `execution_fill_probability`** (most passive) | **+0.0943** |
| argmax `candidate_probability` | −0.0368 |
| argmax `candidate_ev_r` | −0.0371 |
| argmax `expected_net_r` | −0.0449 |
| **allocator rank 1 (what actually runs)** | **−0.0968** |
| random within positive-score set | −0.1049 |
| **argmax `transfer_score` within positive-score set** | **−0.1198** |
| argmax `transfer_score` (whole cycle) | −0.1212 |
| random pick from the cycle | −0.1271 |
| argmax `execution_fill_probability` | −0.1573 |
| random within the zero-score (tied) set | −0.1856 |

Two things fall out. **(a) Inside the domain where the objective is non-degenerate, maximising it is
worse than picking at random: −0.1198 vs −0.1049, a loss of 0.0149 R/trade.** **(b) The clip does carry
real information** — positive-score −0.1049 vs zero-score −0.1856 — the allocator simply throws that
information away by tying the whole zero set together and then ordering the positive set wrongly.

Reconstruction caveat, stated honestly: rebuilding `transfer_score` from the pool's own fields
reproduces only **59.2 % of untied within-cycle pairs** (rho 0.108, 5.5 % of pairs tie on the
reconstructed score). The pool carries the diagnostic recompute of `expected_net_r`, not the exact
scheduler input, and `authority_priority_tier` is not in the pool at all. **The formula above is a
source citation, not a fit** — the empirical claims in §3.2 are about the observed `risk_finalizer_rank`
and about each factor measured directly.

### 3.3 What actually predicts outcome, among decision-time-legal fields only

Within-cycle Spearman vs `fill_honest_walk_r`, TAKEABLE, restricted to fields available before the
decision (no path/outcome fields):

| field | rho | z |
|---|---:|---:|
| `risk_distance` as % of entry price | **+0.0822** | +12.7 |
| `cost_r` / `expected_cost_r` | −0.0739 | −11.5 |
| `expected_net_r` | +0.0656 | +10.2 |
| `spread_r` | −0.0609 | −9.4 |
| `execution_fill_probability` | **−0.0446** | −6.9 |
| `risk_finalizer_rank` | **−0.0320** | −5.0 |
| `candidate_probability` | +0.0287 | +4.4 |
| `matched_sleeve_count` | −0.0130 | −2.0 |
| `effective_admission_count` | +0.0006 | +0.1 |

**The allocator's rank is a weaker predictor of realized outcome than one raw field it already holds at
decision time** (`risk_distance` as a fraction of price: |rho| 0.0822 vs 0.0320, 2.6×). On ALL rows,
`mkt_r_prev_close` — the decision-instant market position relative to the entry, i.e. the born state —
is the strongest decision-time predictor at rho +0.1673 (z +27.8), which is the wave-0 capture finding
reappearing as a ranking signal.

---

## 4. THE FIND — passivity is the axis, and every gate in the stack is pointed at it backwards

### 4.1 The gradient, over genuine resting limits

`execution_fill_probability` bands, RESTING born-state only (n = 7,936 + 13 null). `resMean`/`resWin%`
are computed over trades that actually resolved to target or stop inside the window, so they are
immune to the "less time in market" objection.

| fp band | n | honest | tgt % | stop % | neither % | resolved n | resolved mean | resolved win % | bars to entry | risk-dist % | mean rank |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| < 0.10 | 43 | **+0.3924** | 37.2 | 37.2 | 25.6 | 32 | +0.5000 | 50.0 | 84.8 | 0.1029 | 72.4 |
| 0.10–0.20 | 515 | −0.0601 | 16.5 | 47.4 | 36.1 | 329 | −0.2249 | 25.8 | 73.1 | 0.1375 | 56.4 |
| 0.20–0.30 | 1,044 | −0.0470 | 14.2 | 43.4 | 42.4 | 601 | −0.2612 | 24.6 | 65.8 | 0.1689 | 48.6 |
| 0.30–0.40 | 1,241 | −0.0257 | 15.1 | 42.7 | 42.1 | 718 | −0.2145 | 26.2 | 54.7 | 0.1540 | 43.6 |
| 0.40–0.50 | 1,083 | −0.0470 | 17.1 | 47.4 | 35.5 | 698 | −0.2049 | 26.5 | 43.8 | 0.1816 | 40.8 |
| 0.50–0.60 | 1,027 | −0.0376 | 16.6 | 48.7 | 34.8 | 670 | −0.2388 | 25.4 | 36.1 | 0.1842 | 38.6 |
| 0.60–0.70 | 975 | −0.2119 | 15.0 | 56.6 | 28.4 | 698 | −0.3725 | 20.9 | 24.5 | 0.1920 | 38.5 |
| 0.70–0.80 | 790 | −0.1729 | 17.5 | 58.5 | 23.9 | 600 | −0.3100 | 23.0 | 18.9 | 0.1815 | 38.8 |
| 0.80–0.92 | 767 | −0.1790 | 16.9 | 58.5 | 24.4 | 579 | −0.3264 | 22.5 | 10.5 | 0.1772 | 37.4 |
| ≥ 0.92 | 451 | −0.2044 | 14.4 | 56.3 | 29.0 | 319 | −0.3887 | 20.4 | 7.0 | 0.1857 | 35.4 |

There is a **cliff at 0.60**. Below it: honest −0.026…−0.060, resolved mean −0.205…−0.261, resolved win
24.6–26.5 %. Above it: honest −0.173…−0.212, resolved mean −0.310…−0.389, resolved win 20.4–23.0 %.
**Both channels move**: the passive book resolves less often AND resolves better when it does. And the
allocator's mean rank runs the wrong way across the whole gradient — 72.4 for the best band, 35.4 for
the worst.

### 4.2 The configured floors, and what each one deletes

| config key | file:line | value | excludes (takeable) | excluded R | kept R | delta | zero-neither delta |
|---|---|---:|---:|---:|---:|---:|---:|
| `ultimate_candidate_package_soften_selector_fill_floor_min_fill_probability` (feature OFF at `:795`) | `config/agent_config.yaml:798` | 0.25 | 1,027 (4.3 %) | −0.0271 | −0.1309 | **+0.1038** (t 2.92) | +0.0836 |
| `ultimate_candidate_package_strong_fill_floor_bypass_min_execution_fill_probability` | `:801` | 0.35 | 2,196 (9.1 %) | −0.0292 | −0.1362 | **+0.1071** (t 4.35) | +0.0818 |
| `selector_v4_calibrated_min_fill_probability` | `:811` | **0.45** | 3,400 (14.1 %) | −0.0349 | −0.1416 | **+0.1067** (t 5.23) | +0.0868 |
| `scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability` | `:1030` | 0.45 | (same) | | | | |
| `scheduler_v4_best_trade_allocator_dynamic_budget_min_fill_probability` | **`:1002`** | **0.80** | 6,718 (27.8 %) | −0.0785 | −0.1451 | **+0.0665** (t 4.14) | +0.0517 |
| `scheduler_v4_best_trade_allocator_selector_reduce_risk_new_entry_min_fill_probability` | `:1016` | 0.80 | (same) | | | | |

**The system already ships a mechanism to soften the floor to 0.25 — and it is switched off, and its
release condition is the cost gate.** `ultimate_candidate_package_soften_selector_fill_floor_enabled:
false` (`config/agent_config.yaml:795`); when enabled it requires
`..._requires_broker_cost_pass: true` (`:796`) and `..._requires_positive_predecision_edge: true`
(`:797`). So the one switch that would admit the measured-better population is gated on passing the very
cost limb that refuses that population 2.4× more often than it refuses the allocator's favourite (§4.5).

The default floor when nothing positive is configured is **0.45**
(`src/components/poi_execution_lifecycle.py:265-269`, and a second hardcoded 0.45 fallback at `:311`).
`scheduler_readiness_fill_floor` picks the **minimum** of the three configured positive candidates
(`:258-264`), i.e. 0.45 here — so the 0.80 scheduler value only binds where the 0.45 keys are absent.

**Robustness of the 0.45 delta** (`L9_FLOORROBUST_V1.json`):

| slice | n below | n above | below | above | delta | t | ZN delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| takeable, all | 3,400 | 20,612 | −0.0349 | −0.1416 | +0.1067 | +5.23 | +0.0868 |
| **takeable, first-emission only (dedup)** | 1,457 | 16,928 | −0.0576 | −0.1349 | **+0.0774** | **+2.91** | +0.0349 |
| resting only | 3,400 | 4,536 | −0.0349 | −0.1408 | +0.1059 | +4.18 | +0.0896 |
| resting, first-emission | 1,457 | 1,692 | −0.0576 | −0.1440 | +0.0864 | +2.28 | +0.0516 |
| ALL incl. past-stop | 3,407 | 24,099 | −0.0368 | −0.2648 | +0.2280 | +11.36 | +0.1980 |
| family `current_breaker_re_entry` | 271 | 513 | +0.0866 | −0.1988 | +0.2854 | +3.28 | +0.2394 |
| family `current_fvg_fill` | 2,355 | 4,780 | −0.0336 | −0.1920 | +0.1584 | +5.51 | +0.1393 |
| family `current_ob_retest` | 774 | 510 | −0.0812 | −0.0295 | **−0.0517** | −0.92 | −0.0206 |
| Jan 01–09 | 1,108 | 5,987 | −0.0395 | −0.1546 | +0.1151 | +3.19 | +0.1198 |
| Jan 10–19 | 800 | 5,378 | +0.0750 | −0.1190 | +0.1941 | +4.44 | +0.1624 |
| Jan 20–29 | 1,381 | 8,355 | −0.0995 | −0.1474 | +0.0478 | +1.55 | +0.0195 |
| Jan 30–31 | 111 | 892 | +0.0239 | −0.1352 | +0.1591 | +1.41 | +0.1005 |

Only three families generate any candidate below 0.45 (only they emit genuine resting limits); **two of
three are strongly positive and `current_ob_retest` runs the other way, not significantly.** Three of
four ten-day periods positive.

### 4.3 As a per-cycle selection rule

Cycles with ≥ 5 takeable candidates, n = 1,807. `hZN` = zero-neither convention. `net@spread/7.3` charges
the frozen cost with `spread_r` divided by the measured 7.3× over-charge.

| rule | honest | t | hZN | t | net@spread/7.3 | t | netZN | t |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| most passive AND widest stop | **+0.1294** | 4.82 | +0.0166 | 0.66 | −0.0444 | −1.62 | −0.1572 | −6.09 |
| **most passive (argmin fp)** | **+0.1196** | **4.42** | +0.0066 | 0.26 | −0.0595 | −2.15 | −0.1724 | −6.61 |
| most passive, cost-gated first | +0.0323 | 1.24 | −0.0724 | −2.99 | −0.0415 | −1.59 | −0.1462 | −6.03 |
| widest risk distance | −0.0174 | −0.80 | −0.1217 | −6.44 | −0.1207 | −5.50 | −0.2251 | −11.66 |
| **allocator rank 1** | **−0.1103** | −4.34 | −0.2164 | −9.37 | −0.2482 | −9.60 | −0.3543 | −15.08 |
| random pick (cycle mean) | −0.1260 | −13.34 | −0.2030 | −23.22 | −0.3111 | −31.87 | −0.3881 | −42.97 |

**The allocator's own pick beats a random pick by +0.0157 R/trade on the honest measure and LOSES to it
by 0.0134 under the zero-neither convention.** Reordering the identical candidate set by ascending fill
probability instead is worth **+0.2299 R/trade** against the allocator's pick (+0.2230 zero-neither).

Passivity position ladder (1 = most passive in its cycle), same 1,807 cycles:

| position | n | honest | se | t | mean fp | mean alloc rank | neither % |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,807 | **+0.1196** | 0.0271 | **+4.42** | 0.357 | 44.1 | 41.4 |
| 2 | 1,807 | −0.0745 | 0.0264 | −2.83 | 0.502 | 39.6 | 35.9 |
| 3 | 1,807 | −0.1286 | 0.0258 | −4.98 | 0.631 | 35.2 | 34.9 |
| 4 | 1,807 | −0.1220 | 0.0265 | −4.61 | 0.735 | 30.1 | 32.4 |
| 5 | 1,807 | −0.1383 | 0.0265 | −5.21 | 0.806 | 30.1 | 30.3 |
| 6 | 1,695 | −0.1971 | 0.0269 | −7.34 | 0.854 | 29.4 | 28.0 |
| 7 | 1,579 | −0.1919 | 0.0278 | −6.91 | 0.879 | 30.8 | 29.1 |
| 8+ | 11,350 | −0.1530 | 0.0103 | −14.79 | 0.913 | 40.7 | 32.0 |

Permutation test, 2,000 within-cycle random re-picks: observed +0.11962, null mean −0.12528, null p95
−0.08505, **null max −0.03766, 0/2000 ≥ observed, p ≤ 0.0005.**

Stability of the most-passive pick: **15 of 21 trading days positive, median day +0.1875**; by ISO week
+0.2802 / +0.0386 / +0.1270 / +0.0903 / +0.1912. By contention depth the effect grows monotonically —
min cycle size 2 → +0.1059, 3 → +0.1134, 5 → +0.1196, 8 → +0.1393, 12 → **+0.2116** (t 5.51).

### 4.4 The two honest caveats on §4.3, both material

1. **Under first-emission dedup the per-cycle rule collapses**: pos1 falls to **−0.0450 (t −1.65)** and
   the advantage over the allocator shrinks to **+0.0599**. The most-passive candidate in a cycle is
   frequently a *stale re-emission* of an earlier setup whose limit the market has walked away from
   (W0-F1: 24.4 % of the pool is pseudo-replication). **The population-level floor finding in §4.2
   survives dedup (+0.0774, t 2.91); the extreme per-cycle argmin rule does not.** Use the floor number
   as the durable one.
2. **Roughly all of the pos1 cohort's absolute positivity is the mark at the 2-hour wall.** pos1 honest
   +0.1196 → zero-neither **+0.0066 (t 0.26)**. The *relative* gain survives (+0.2230 vs the allocator,
   +0.2096 vs random) because the comparison cohorts collapse further, but pos1 is **not** a positive-
   expectancy rule on its own: its outcome mix is 357 target (+2.00) / 702 stop (−1.00) / 748 neither
   (+0.2729), and at the frozen cost it nets −0.6513, at spread/7.3 −0.0512.

### 4.5 The cost gate is pointed at the same population, also backwards

The frozen cost gate admits **66.1 %** of the allocator's rank-1 picks but only **27.8 %** of the
most-passive picks — it is 2.4× more likely to refuse the passive candidate. That is arithmetic, not
policy: a far resting limit in this pool carries a narrower `risk_distance` (0.1514 % of price at pos1
vs 0.2426 % at position 8+), and `cost_r` is R-denominated, so the passive book mechanically prices as
expensive. Applying the gate first is what turns the +0.1196 rule into +0.0323.

**`src/components/broker_net_cost_engine.py:299-319` (`_tick_packet(tick, sl_distance)`) computes
`spread_r = spread_price / sl_distance` and takes no order-type argument — and a case-insensitive search
of all 938 lines of that file for `order_type|is_limit|passive|marketable|crossing|maker|taker` returns
ZERO hits.** The cost engine has no notion of order type at all: a passive limit filled *at its own
price* is charged the identical entry spread as a market order that crosses. The passive book is
therefore charged for liquidity it supplies rather than takes, and is then refused for being expensive.
This is a second, independent over-charge stacked on top of the measured 7.3–8.5× spread error, and it
falls **entirely** on the population §4.1 measures as the better one.

---

## 5. Lane item 3 — admission count and disposition

**`effective_admission_count`** (TAKEABLE) is the one allocator-side field that behaves correctly:

| count | n | honest | t | gross | mean rank |
|---|---:|---:|---:|---:|---:|
| 0 | 9,134 | −0.1724 | −15.94 | −0.1361 | 44.0 |
| 1 | 14,963 | −0.0980 | −10.33 | −0.0845 | 33.2 |
| 2 | 28 | −0.0714 | −0.38 | +0.0357 | 26.0 |

**`matched_sleeve_count` does not**, and this is the field whose analogue drives live conviction sizing:

| sleeves matched | n | honest | t | gross |
|---|---:|---:|---:|---:|
| 0 | 2,305 | −0.1762 | −8.24 | −0.1102 |
| 1 | 16,685 | −0.1162 | −13.39 | −0.1069 |
| 2 | 3,142 | −0.1566 | −7.83 | −0.1067 |
| 3 | 1,700 | −0.0947 | −3.37 | −0.0517 |
| 4 | 289 | −0.1473 | −2.19 | −0.1493 |
| 5 | 4 | −0.8483 | −5.59 | −0.8483 |

**Non-monotone: 2 is worse than 1, 4 is worse than 3.** "More sleeves agree" carries no outcome signal
here. The live Kelly-lite conviction multiplier keys on the day's distinct firing-sleeve count
(`admission.py:920-935`, `running_conviction_state.py:33-82`, half-Kelly bins
`((1,1,0.748),(2,3,0.991),(4,99,1.241))` — a 1→2 step is +25.2 % on every unit). The nearest testable
analogue in this pool:

- **day-level breadth vs day-level quality: Spearman −0.1662 over 21 days** (more candidates on a day →
  slightly *worse* mean outcome).
- cycle-level breadth vs cycle quality: +0.0243 over 1,966 cycles ≈ nothing.

n = 21 days is small and this is a proxy, not the live counter — but the sign is negative and there is
no evidence anywhere in this pool that breadth predicts quality. **Size is being scaled by a quantity
with no measured relationship to edge.**

**`scheduler_selection_disposition`** (TAKEABLE):

| disposition | n | honest | t | mean rank |
|---|---:|---:|---:|---:|
| `candidate_generated_not_scheduler_selected` | 3,826 | −0.1031 | −6.08 | 3.8 |
| `candidate_materialization_skipped_before_scheduler` | 20,174 | −0.1308 | −16.48 | 43.8 |
| `scheduler_preselected_then_rejected_by_finalizer` | 125 | −0.0778 | −0.80 | 3.5 |

The 196 late finalizer vetoes (125 takeable) were of slightly-better-than-average candidates, not worse
ones — directionally wrong, not significant.

---

## 6. Lane item 4 — the exposure logic is inert

| field | zero | non-zero | non-zero share |
|---|---:|---:|---:|
| `same_symbol_exposure_risk_pct` | 23,924 | **201** | 0.83 % |
| `same_side_pending_risk_pct` | 24,108 | **17** | 0.07 % |
| `opposite_pending_risk_pct` | 24,107 | **18** | 0.07 % |

**The same-symbol / same-side / opposite-pending exposure machinery never sees anything in this
population.** Where it does fire the sample is unusable (n = 17 and 18, honest −0.5107 and −0.3521
respectively, gross +0.0730 and +0.0119 — the two measures disagree in sign, which at that n means
nothing). `same_symbol_exposure_risk_pct` non-zero (n = 201) reads +0.0105 honest against −0.1273 for
the zero mass. Any hypothesis about correlation control being the leak is **unmeasurable from January
S0R0** and should not be pursued here.

The three explicit exposure guards, by `risk_finalizer_reason` (ALL rows):

| guard | n | honest | t | verdict |
|---|---:|---:|---:|---|
| `same_symbol_daily_loss_lockout_after_closed_trade` | 55 | **+0.1265** | +0.79 | blocked candidates that were POSITIVE on average — wrong side, n.s. |
| `adaptive_replay_memory_guard_blocked:symbol_origin_side` | 79 | −0.2778 | −2.17 | blocked genuinely bad candidates — correct |
| `recent_same_cluster_opposite_side_closed_trade_cooldown` | 10 | — | — | n too small |

This reproduces the brief's "daily_lockout is the only positive blocker class" on the honest measure and
on the finalizer reason rather than the cascade label — but at n = 55 and t = 0.79 it is a direction,
not a result.

---

## 7. Cross-lane: why repairing costs made the system trade more and earn no more

Sweeping the frozen spread over-charge divisor and re-applying **both** cost limbs
(`spread_r ≤ 0.10` at `broker_net_cost_engine.py:859-866` and `total_cost_r ≤ 0.15` at `:923-927`):

| divisor | n admitted | of which past-stop | honest, all admitted | honest, takeable only |
|---:|---:|---:|---:|---:|
| 1.0 (frozen) | 7,210 | 230 (3.1 %) | −0.1076 | −0.0802 |
| 7.3 | 16,444 | 1,618 (9.8 %) | −0.1881 | −0.1015 |
| 8.5 | 17,149 | 1,863 (10.9 %) | −0.1955 | −0.0994 |

Repairing the spread to the measured 7.3× degrades the admitted book by **−0.0805 R/trade**, but only
**−0.0213** of that is real: **73.5 % of the degradation is the born-past-stop artifact being released
into the tradeable set.** 3,290 of the 3,516 past-stop rows (93.6 %) are held out by nothing except the
cost gate, and each books a mechanical −0.9948.

**The engine already contains the correct-shaped guard and it almost never fires:**

| guard | catches past-stop | class size | precision | recall vs 3,516 |
|---|---:|---:|---:|---:|
| `pre_order_materialization_preflight_blocked:marketable_limit_structure_preservation_contract_unmet` | 44 | 52 | **84.6 %** | 1.25 % |
| `final_blocker_class = marketable_guard` | 84 | 156 | 53.8 % | 2.4 % |
| `broker_cost_authority_blocked_non_executable` | 3,290 | 20,448 | 16.1 % | 93.6 % |

So the cost gate has been doing the stop-integrity gate's job by accident, at 16 % precision. **Any cost
repair must land together with a stop-integrity precondition, or it releases ~1,600–1,850 mechanical
−0.99 R rows into the book** — which is exactly the shape of the twelve month-replays' "trades 2.2–2.4×
more, earns no more".

### 7.1 The two repairs composed, at book level

Takeable population, `net` charges the frozen cost with `spread_r ÷ 7.3`. `totR` is the whole-month sum
of honest R across the admitted book (an ordering aid, not a P&L — the pool is counterfactual).

| book | n | honest | t | hZN | net | t | netZN | totR | mean fp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **F** repaired cost, floor 0.45 kept, **no stop guard** | 14,186 | **−0.2158** | −25.2 | −0.2938 | **−0.2919** | −33.9 | −0.3699 | −3,060.9 | 0.879 |
| **A** frozen cost + floor 0.45 (as-shipped analogue) | 5,932 | −0.0993 | −7.6 | −0.1886 | −0.1847 | −14.0 | −0.2740 | −589.0 | 0.878 |
| **B** repaired cost + stop guard + floor 0.45 | 12,584 | −0.1178 | −12.7 | −0.2049 | −0.1895 | −20.5 | −0.2766 | −1,482.4 | 0.874 |
| **C** repaired cost + stop guard, **floor removed** | 14,826 | −0.1015 | −11.8 | −0.1895 | −0.1731 | −20.1 | −0.2611 | −1,505.4 | 0.789 |
| **D** repaired cost + stop guard, **passive slice only** (fp < 0.45) | 2,173 | **−0.0154** | −0.66 | −0.1091 | **−0.0870** | −3.7 | −0.1807 | −33.5 | 0.295 |
| **E** passive slice with no cost gate at all | 3,400 | −0.0349 | −1.9 | −0.1291 | −0.2005 | −10.5 | −0.2947 | −118.5 | 0.301 |

Read F → B: **the stop-integrity guard alone is worth +0.0980 honest / +0.1024 net per trade.**
Read B → C: **removing the fill floor adds 2,242 trades and is worth a further +0.0163 honest /
+0.0164 net per trade.** Read C → D: the passive slice is the only cohort in the estate that comes
within one standard error of zero on gross-honest R (−0.0154, t −0.66) and is 2× better than any other
book on net (−0.0870).

**Stated against the mission, without decoration: nothing here is positive.** The best book is still
−0.087 R/trade net. What the table establishes is *where the value is going* — the naive cost repair
(F) is 0.11 R/trade worse than the frozen gate it replaces, and every one of the three levers that
recovers ground (stop guard, floor removal, passivity selection) is currently pointed the other way.

---

## 8. Everything this lane measured, as a list of numbers

- Cycles 1,969; visible share of the ranked universe 19.35 %; implied missing rows 115,259; rank-1
  present in 1,153 cycles (58.6 %); 0 cycles with duplicate ranks; 0 cycles where `max(rank)` equals the
  visible count.
- Pool `fill_honest_walk_r` outcome mix: neither 7,852 / stop 15,852 / target 3,713 / no_fill 241.
  no_fill scores exactly 0.0 on all 241.
- `fill_realism_class`: `passive_queue_confirmed` 21,052 at −0.2221 honest, mean rank 35.2;
  `source_safe_immediate_marketable` 6,606 at −0.2833, mean rank 44.8.
- Oracle ceiling / floor per cycle (TAKEABLE, honest): best-in-cycle **+1.6493**, worst-in-cycle
  −0.9860, random −0.1271, allocator rank1 −0.0968, allocator rank-LAST −0.1309.
- Selection alpha of the allocator = rank1 − random = **+0.0303** (honest, TAKEABLE, 1,949 cycles);
  = **−0.0134** under zero-neither at cycle size ≥ 5.
- pos1 cohort composition: mean fp 0.357, median 0.3165, 94.8 % resting born-state, mean bars to entry
  touch 56.2, mean allocator rank 44.1, mean `cost_r` 0.771, `plain_walk_r` **+1.3169** (the fill-blind
  fiction, shown for contrast).
- pos1 by symbol (top): USDCHF n29 +0.3424 (t 2.67), JP225 n160 +0.3234 (t 3.26), UKOIL_cash n30
  +0.2816, AUDUSD n33 +0.2729, XAUUSD n409 +0.2464 (t 3.73), SPX500 n149 +0.2366 (t 2.57).
  (bottom): XAGUSD n18 −0.1578, USDCAD n21 −0.1647, NAS100 n116 −0.1953 (t −2.31), CHFJPY n13 −0.2467,
  EURJPY n23 −0.3294 (t −2.33), EURGBP n17 −0.4720 (t −2.46).
- `risk_finalizer_reason` honest means (ALL, n ≥ 40): daily-loss lockout +0.1265 (55) · displacement
  veto −0.0903 (1,601) · marketable-limit entry guard −0.0933 (599) · package authority −0.1000 (4,097)
  · scheduler runtime ineligible −0.1147 (602) · adaptive memory guard −0.2778 (79) · cost authority
  −0.2822 (20,448) · reduce-risk origin preserved −0.3383 (41) · marketable-limit structure preflight
  **−0.9137 (52, 84.6 % past-stop)**.
- Fill-floor veto cohort (`miss_reason` starts `scheduler_vetoed_candidate_package_fill_floor`):
  n = 1,443, **100 % scheduler-materialized, mean allocator rank 3.35**, honest −0.0981 (t −3.51),
  `cost_r` 0.0918, 41.2 % unresolved. The floor is vetoing the allocator's own top-of-book.
- Scheduler-materialized rows (n = 4,095): mean fp 0.839, 81.1 % ≥ 0.80, 92.1 % ≥ 0.45, 7.9 % < 0.45,
  honest −0.1324. Not-materialized (n = 23,563): mean fp 0.7991, 74.1 % ≥ 0.80, 13.1 % < 0.45.
- Within-cycle Spearman of `risk_finalizer_rank` against each pool field, |rho| top 6:
  `commission_r` −0.2237, `spread_r` +0.1706, `matched_sleeve_count` −0.1594,
  `old_proxy_vs_broker_calibrated_delta_r` +0.1516, `effective_admission_count` −0.1226, `cost_r`
  +0.1023. **No single visible field explains the rank** (max |rho| 0.22).
- Two-way passivity quintile × risk-distance quartile (honest, TAKEABLE, 1,807 cycles): P1 row
  −0.0682 / +0.0261 / −0.0402 / −0.0348; P5 row −0.2271 / −0.1973 / −0.1244 / −0.0451. **The two axes
  are independent and additive**; best cell P1_D2 +0.0261 (n 1,472), worst P3_D2 −0.2409 (n 1,241).

---

## 9. What a later wave should test

1. **Take the fill-floor delta to another month.** February (`CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz`, 24,239
   rows, 101 fields including inline first-touch timestamps) is the natural test and does not need a
   path sidecar to answer it. The pre-declared statistic is the §4.2 table at the 0.45 floor,
   first-emission dedup, resting-only: January says **+0.0864, t 2.28**.
2. **Price the counterfactual properly.** Everything here is bounded by the pool's hard 2-hour horizon
   (86.1 % of paths are exactly 120 M1 bars). The passive book fills at bar 43–85 on average, so it is
   the population *most* truncated by that wall. A longer walk on raw M1 would move these numbers, and
   the sign of the move is not knowable from this asset.
3. **Separate "the limit is far" from "the limit is stale".** §4.4 caveat 1 is the open question: build
   a passivity measure that excludes re-emissions of a setup whose level the market has already left
   (w0-capture measured that 51.7–55.7 % of past-stop rows quote a level untraded in 24 h). If the
   passive edge survives that split, it is an entry-price edge; if it does not, it is a staleness
   artifact and the floors are right for the wrong reason.
4. **Rebuild the ranker's objective from `expected_net_r` alone** and re-run: the measured ordering says
   dropping the `× probability × fill_probability × source_completeness` factors improves within-cycle
   rho from +0.0478 to +0.0656 and per-cycle selection from −0.1212 to −0.0449 R/trade.
