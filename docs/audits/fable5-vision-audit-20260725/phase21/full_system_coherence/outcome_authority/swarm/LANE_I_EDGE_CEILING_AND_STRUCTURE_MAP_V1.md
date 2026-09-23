# LANE I — The edge ceiling and the structure map

**Owner question this lane serves:** *"Now we have all the systems that we need. How can we find edges?"*
**The question this lane answers first:** how much money is actually available in this market surface,
and what fraction of it has any rule ever captured? Without that, *"we found no edge"* is
uninterpretable — it could mean the surface is empty, or that we searched it badly.

Date 2026-08-11. Lane I of the owner-commissioned swarm. Measurement only: no live path, no config,
no VPS, no trading rule, no backtest of a rule. Receipts under `lane_i_receipts/`, every script that
produced a number under `lane_i_receipts/scripts/`.

---

## 0. The four numbers

Everything below is in **R** — one unit of the trade's own stop distance — the estate's own unit,
so the rows are comparable to each other and to the armed book.

| | R / month | basis |
|---|---:|---|
| **Perfect-foresight ceiling** on the existing generator surface | **+1,566.7** | best resolved candidate in every decision window, one position per symbol |
| **Perfect-foresight floor** (the same protocol run to lose) | **−1,489.1** | worst resolved candidate in every window |
| **Out-of-sample achievable from the 43 recorded predecision features** | **0.0 ± 22.2** | four model classes, five months, indistinguishable from random in both directions |
| **What the frozen MARKET-top-choice rule actually captured** | **+0.19** | committed validation results, 290 trades, Feb+Apr+May+Jun+Jul 2026 |

For comparison, on the same unit: the **armed sleeve book** (FTMO, the four cost-surviving sleeves,
full 2015–2026 window, worst-carry assumption) delivers **+0.48 R/month**
(`research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json` → `SURVIVORS_ONLY / full_nights_max`:
0.26576 R per book-day × 1.81 book-days per calendar month). In the window that *selected* it
(forward 2025+) it delivers +3.09 R/month; that is the in-sample number and should not be planned on.

**So: the surface is not empty — it is enormous. The extraction is what is empty.** The ceiling is
~3,200× what the armed book delivers out of window and ~8,000× what the frozen candidate rule
delivered. The gap is not a modelling near-miss. It is the whole distance.

**And the decisive finding, stated plainly, because the brief asked for it plainly:**

> **The 43 recorded predecision features contain no out-of-sample extractable information that the
> deployed selection protocol can use.** A high-capacity model fitted in-sample reproduces perfect
> foresight (capture ratio 1.00–1.04). Move it *one trading day* forward and the capture ratio is
> **−0.047 to +0.016**. Move it one month forward: **−0.033 to +0.035**. Both straddle zero. This
> holds for a gradient-boosted model, for the frozen ridge, in-sample-day-out and month-out, across
> five months, on 382,181 eligible candidates in 9,237 decision windows.
>
> **Stated exactly** (§3.1 measures this rather than arguing it): out of sample there *is* a small
> **cross-sectional** lift — the top decile of a month's rows beats that month's mean by +0.027 R
> on average. But the protocol never ranks across a month; it ranks **inside one decision window** of
> ~40 candidates and takes the argmax. Measured there, the frozen model's edge is **+0.003 ± 0.005
> R/trade, positive in 2 of 5 months — and it is beaten by "pick the cheapest candidate", which needs
> no model at all (+0.0065 R/trade, 4 of 5 months).** Against a required **+0.09 R/trade** (§7),
> that is 3 % of the way.

That is not a failure of the search. It is a property of the target: §5 shows the strongest, most
stable conditioner in the entire bar archive moves *dispersion, fill probability and outcome mix* by
large amounts and moves *signed expectancy* by less than half of one cost unit. **The estate has been
training models to predict the one quantity its features do not carry.**

---

## 1. What was measured, and against what

**Part 1 population.** The five-month cached candidate population built by the committed
`puzzle_receipts/puzzle_build_cache.py` — February, April, May, June and July 2026, loaded through
the frozen r2→r3b→r4d loader chain against the true-UTC lane manifests. 632,934 candidate
occurrences; **382,181 eligible** (`predecision_geometry_valid` ∧ finite `cost_r` ≤ 0.20);
**84,721 filled**, 251,709 `RESOLVED_NO_FILL`, 45,751 `CENSORED_*`; **9,237 decision windows**.

> **One correctness note that changes every number in this file.** `RESOLVED_NO_FILL` carries a null
> `terminal_net_r`. The frozen scorer reads it as `float(row.get("terminal_net_r") or 0.0)` — a
> resolved, real, **zero-value** outcome, not a missing one. A first pass of this lane treated it as
> missing, which let a null candidate win a window and then block that symbol; it understated the
> oracle by ~35 %. The committed numbers use the frozen convention.

**Part 1 protocol.** The frozen `select()` from `w21_score_feb_market_top_r2.py` — group by
`decision_window_id`, order by earliest `label_span_start_utc`, one open position per symbol, pick
`max(score, −cost_r, occurrence_key)`, abstain below the threshold, `market_top_abstain` also abstains
when the top pick is not a MARKET order. It was **reimplemented and proved byte-equivalent**: identical
selection on all 5 months × 3 policies against a verbatim copy of the frozen function
(`PART1_PROTOCOL_EQUIVALENCE.json`, `all_identical: true`). Every oracle, null and model arm below runs
through that same proved implementation, so no arm gets a different protocol from any other.

**Part 2 sources.** The lane-input hold's bar archives, `time_column_basis: "true_utc"`,
`broker_clock_rule: "new_york_plus_7"` per `SOURCE_CATALOG.json`:

| grid | source | symbols | rows | span |
|---|---|---:|---:|---|
| H4 | `deep_universe_h4d1_2014_2026` | 24 | 376,510 | 2014-01-01 → 2026-06-17 |
| D1 | `deep_universe_h4d1_2014_2026` | 24 | 63,337 | 2013-12-31 → 2026-06-16 |
| M15 | `bridge_ftmo_m15_20250601_20260610` | 24 | 612,190 | 2025-05-31 → 2026-06-09 |

---

## 2. The oracle band — what is theoretically there

`PART1_ORACLE_BAND.json`. All figures are five-month totals with the per-month mean in brackets.

| quantity | 5-month R | per month | what it is |
|---|---:|---:|---|
| sum of \|net R\| over filled rows | 84,369.2 | 16,873.8 | the **dispersion** of the population — not money anyone can take |
| pool net sum | −7,859.2 | −1,571.8 | what taking every filled candidate would earn (−0.0928 R/fill) |
| per-window best, concurrency ignored | 12,751.5 | 2,550.3 | upper bound if you could hold every symbol at once |
| **perfect foresight, protocol-constrained** | **7,833.3** | **1,566.7** | best resolved candidate per window, one position per symbol, abstain when nothing is positive |
| perfect foresight, forced to trade every window | 7,637.8 | 1,527.6 | the instrument used for the ladder in §3 |
| perfect foresight under the frozen MARKET-abstain policy | 3,974.1 | 794.8 | the same oracle restricted to the deployed policy |
| **anti-oracle floor** | **−7,445.5** | **−1,489.1** | the same protocol run to lose |
| random selection (200 draws/month) | −320.4 | −64.1 ± 22.3 | no information at all |

### 2.1 Reconciliation with Session AW's "±38,317 R of separable opportunity"

`JANUARY_BANK.md` §3 and `SESSION_AW_SEPARABILITY_MINE.md` carry **+6,916.95 R of positive rows
against −31,400.82 R of negative rows over 28,519 scoreable rows** in one January arm — the ±38,317 R
figure the estate has quoted since. **That statistic is the sum of |net R| over the row population.
It reproduces here in kind** (84,369.2 R over 84,721 filled rows across five months = 0.996 R of
dispersion per row; January's was 1.344 R/row on a different label contract — the broad-V4 replay,
not this candidate surface, so the levels are not expected to match and the per-row order of magnitude
is the reconciliation).

**But it is not an opportunity figure, and it has been read as one.** A protocol that takes one
position per decision window and one position per symbol cannot harvest row dispersion; it can harvest
at most the best row in each window. Under that constraint the perfect-foresight band is
**±~1,530 R/month — 9.3 % of the dispersion figure.** The ±38,317 R headline overstates the realisable
ceiling by roughly **11×**. Both numbers are correct; only one of them is a ceiling.

This does not weaken AW's underlying point — the owner's challenge that the pool was never tested for
separability by *any* rule was right, and §3 is that test, run properly for the first time. It
right-sizes the prize: the prize is ~1,530 R/month, not ~38,000.

---

## 3. The feature-set information test — the decisive number

`PART1_FEATURE_INFORMATION.json`. The 43 features are the frozen ridge's own contract: 14 categorical
(`symbol, side, origin_family, utc_session, proposed_order_type, utc_hour, weekday, symbol_x_family,
family_x_session, symbol_x_side, poi_mitigation_status, limit_marketable_at_decision, trend_state_m15,
trend_transition_flag`) and 29 numeric (costs, limit distances, risk geometry, POI state, and the ten
`PREDECISION_FEATURE_KEYS` from `broader_origin_generators.py:265`).

**Instrument.** Every arm is forced to trade in *every* window where a resolved candidate is
available — identical window set, identical availability, identical tie-breaks. The **only** thing
that differs between arms is which candidate is picked. That isolates selection skill from abstention.
Capture ratio is `(arm − random) / (perfect foresight − random)`: 0 = no information, 1 = omniscience.

| arm | what it can see | 5-month R | per month | capture ratio, range over months |
|---|---|---:|---:|---:|
| perfect foresight | the outcome | 7,637.8 | 1,527.6 | 1.0000 |
| **`gbm_is`** | 43 features, fitted **on the same month** | **7,803.0** | 1,560.6 | **+0.997 … +1.036** |
| `ridge_is` | 43 features, frozen model class, same month | 584.7 | 116.9 | +0.090 … +0.151 |
| `gbm_is_shuffled` | same capacity, **labels shuffled** | −368.8 | −73.8 | −0.019 … +0.007 |
| **`gbm_cv_day`** | 43 features, **same month, unseen day** | **−482.9** | −96.6 | **−0.047 … +0.016** |
| **`gbm_oos`** | 43 features, **prior months → this month** | **−360.2** | −90.1 | **−0.033 … +0.002** |
| `ridge_oos` | frozen model class, prior months → this month | −181.5 | −45.4 | −0.014 … +0.035 |
| `ridge_oos_frozen` | **the frozen rule's own prediction** | −253.6 | −50.7 | −0.009 … +0.016 |
| random | nothing | −317.3 | −63.5 | 0.0000 (SD 22.3/month) |
| anti-oracle | the outcome, inverted | −7,361.3 | −1,472.3 | −0.901 … −0.867 |

**Read the three rows that matter.**

1. **`gbm_is` captures 100 % of perfect foresight.** The feature set has enough *capacity* to
   reproduce omniscience when it is allowed to see the answers. Spearman against realised net R on
   filled rows: 0.918–0.951. Top-1 % mean +2.13 R. So nothing is wrong with the features as
   identifiers, the model, the pipeline, or the protocol.
2. **`gbm_is_shuffled` captures 0 %.** Same capacity, shuffled labels: Spearman −0.0002 … +0.0071,
   decile spread −0.026 … −0.003. This proves row 1 is memorisation of *real* labels rather than an
   artefact of capacity — the control the estate's own doctrine demands, and it passes.
3. **Everything out of sample is inside the random band.** One trading day of separation is enough to
   destroy all of it. `gbm_cv_day` is not merely at random — pooled it is **−165.6 R below** random
   against a pooled SD of 49.8 (z −3.3): the in-sample relation **reverses** out of sample, which is
   the signature of fitting a transient regime rather than a stable one.

### 3.1 The one place a lift does exist — and why the protocol cannot spend it

`PART1_WITHIN_WINDOW_SKILL.json`. Ranking skill has to be measured in the shape the protocol uses it,
and the two shapes give different answers. Across the 18 out-of-sample month × arm cells:

| statistic | value |
|---|---|
| top-decile lift over the month's population mean | **+0.027 R** on average, positive in **12 / 18** cells, range [−0.055, +0.120] |
| top-1 % lift | +0.062 R on average, positive in 14 / 18, range [−0.177, +0.254] |
| **top-decile mean net R in absolute terms** | **negative in 17 of 18 cells** (mean −0.070); only February's frozen ridge is positive |
| Spearman on filled rows | +0.020 mean, range [−0.002, +0.050] |

So a small **cross-sectional** lift is real. It is a quarter of the median cost (0.112 R) and it never
lifts the top decile above zero. And it is *between-window* information — the model can tell which rows
are globally worse — which the must-trade protocol cannot spend, because it must trade in every window
regardless.

**What the protocol actually performs is a ranking inside one decision window** (median 37–43 resolved
candidates). Measured there — argmax net R minus that window's own mean net R, every window with ≥ 2
resolved candidates:

| arm | pooled within-window lift | SE | t | months positive |
|---|---:|---:|---:|---:|
| **`ridge_oos_frozen`** (the deployed model) | **+0.00298 R/trade** | 0.00488 | +0.61 | **2 / 5** |
| **`negative_cost`** — pick the cheapest candidate, no model | **+0.00650 R/trade** | 0.00464 | +1.40 | **4 / 5** |
| `random` | −0.00825 R/trade | 0.00608 | −1.36 | 1 / 5 |

**The deployed model's within-window edge is +0.003 R/trade, and a one-line cost heuristic beats it.**
Against the +0.09 R/trade the surface demands (§7), the model supplies 3 % and the free heuristic
supplies 7 %. The frozen rule's own published diagnostic agrees from the other side
(`ANSWERS.json` → `ranking_health_population`: top-decile mean net −0.1011, −0.0480, −0.0980, −0.1011
for Apr/Jul/Jun/May; only February positive, at +0.0586).

### 3.2 Is there level structure, if there is no row structure?

`PART1_CELL_PERSISTENCE.json`. If rows are unpredictable, cells might still persist — "the
symbol × family that paid last month pays this month" is the estate's working hypothesis whenever it
proposes a sleeve. Tested on filled rows, prior-months mean versus current-month mean, cells with
n ≥ 30 on both sides:

| cell | mean Spearman | months positive | prior-top-tercile lift over population, next month |
|---|---:|---:|---:|
| `symbol` | +0.254 | 3 / 4 | **+0.0035 R/trade** (3/4 months) |
| `symbol_x_family` | +0.105 | 2 / 4 | +0.0039 R/trade (2/4) |
| `symbol_x_family_x_side` | +0.094 | 4 / 4 | +0.0032 R/trade (2/4) |
| `origin_family` | +0.170 | 2 / 4 | −0.0019 R/trade (3/4) |
| `utc_hour` | +0.077 | 3 / 4 | −0.0074 R/trade (1/4) |
| `utc_session` | +0.059 | 3 / 4 | −0.0171 R/trade (2/4) |

**Level structure exists and is worth about +0.003 R/trade.** The population mean is −0.093 R/fill and
the median cost is 0.112 R. The persistence is real and it is **two orders of magnitude too small** to
matter. Selecting cells on last month's performance is not a lever.

---

## 4. Capture ratio — what the frozen rule and the armed book actually took

`PART1_CAPTURE_RATIO.json`. The numerator is the **committed** validation results (daily prequential
refit, `market_top_abstain`), not this lane's replica. The null is matched-count: draw the same number
of trades at random from the same month's eligible / resolved / **filled / MARKET-order** pool — the
exact pool the policy draws from (its published outcome mixes contain only STOP / TARGET / TIME_STOP /
CENSORED, no `NO_FILL`, because MARKET orders always fill).

| month | trades | frozen realised R | matched-count random | z | percentile |
|---|---:|---:|---:|---:|---:|
| Feb | 106 | **+14.168** | −7.86 ± 11.23 | +1.96 | 97.3 |
| Apr | 50 | −7.742 | −5.72 ± 7.34 | −0.28 | 40.2 |
| May | 17 | +5.130 | −2.09 ± 4.27 | +1.69 | 94.8 |
| Jun | 49 | +3.964 | −5.03 ± 7.15 | +1.26 | 89.2 |
| Jul | 68 | −14.566 | −6.70 ± 8.58 | −0.92 | 18.2 |
| **pooled** | **290** | **+0.954** | **−27.39 ± 17.97** | **+1.58** | — |

**Three honest readings of the same table.**

- **Against perfect foresight: 0.024 %.** +0.954 R out of a 3,974.1 R ceiling under its own policy.
- **Against the out-of-sample-achievable ceiling: undefined, because that ceiling is zero.** §3
  measured it at 0.0 ± 22.3 R/month. The frozen rule captured essentially all of an essentially empty
  set. This is the interpretation the lane was commissioned to supply, and it reframes the whole
  programme: the rule did not underperform its opportunity, it *matched* it.
- **Against matched-count random: +1.58 SD over five months, +0.10 R/trade, 3 of 5 months positive.**
  Not significant, not reproducible, and entirely consistent with the estate's own read history
  (February PASS, April+May REJECT, June+July REJECT). Whatever small lift is there sits in the
  **abstention** threshold, not in the ranking: §3.1 measures the same predictor's within-window
  ranking edge at **+0.003 ± 0.005 R/trade**, behind a cost heuristic that uses no model.

**The armed sleeve estate, same unit.** FTMO four cost-surviving sleeves, `SURVIVOR_BOOK_V1.json`:
+0.905 R/month at zero carry, **+0.481 R/month at worst carry**, over the full 2015–2026 window; the
eleven-sleeve book of record is +0.087 R/month at worst carry. In the 2025+ window that selected the
sleeves those two become +3.09 and +2.63 — the in-window figures, which CLAUDE.md §4 already flags
("treat the small number as the expected case"). So the
armed book, out of window, captures **0.031 %** of the perfect-foresight ceiling on this candidate
surface. It out-earns the frozen candidate rule by ~2.5×, which is the honest ranking of the estate's
two extraction attempts. Both are within rounding distance of zero against the ceiling.

*Caveat, stated rather than buried:* the sleeve book runs a different generator surface and a
different contract (320-hour horizons against the candidate surface's 2 hours). The unit — R at one
risk unit per trade — is the same, and the comparison is made on that basis only.

---

## 5. Where the money is — the structure map

`PART2_STRUCTURE_SCAN.json` / `.csv`. 176 cells: 13 conditioning variables + 3 calendar factors, ×
4 horizons, × 3 grids. Quintiles formed **within symbol**. Reported as effect sizes and cross-period
stability, never as p-values, because this is a scan.

Every cell carries: the endpoint effect (top bin − bottom bin), the same for **|forward return|**, the
monotonicity ρ over the ordered bins, per-year sign agreement across 13 years, per-symbol sign
agreement across 24 symbols, a genuine **2014–2021 → 2022–2026 holdout**, and a null from **200
circular shifts** of the forward-return series within symbol (destroys the conditional relation,
preserves each series' own autocorrelation and marginals).

### 5.1 The headline of Part 2

Of the 128 non-M15 cells, passing a fixed bar of |IR| ≥ 0.02 **and** holdout sign match **and** year
sign agreement ≥ 0.75:

| effect measured on | cells passing | cells with \|IR\| ≥ 0.05 |
|---|---:|---:|
| **signed** forward return (direction) | **10 / 128** | **1** |
| **\|forward return\|** (magnitude) | **59 / 128** | **41** |

*(Both counts include the 8 `weekday` cells that §5.2 strikes as artefacts. Removing them:
signed **7 / 120**, magnitude **56 / 120** — the ratio, which is the point, moves from 5.9× to 8.0×
in favour of magnitude.)*

**The bar archive contains large, monotone, cross-year and cross-symbol stable structure in the SIZE
of forward moves, and essentially none in their DIRECTION.** That single sentence explains §3.

### 5.2 The ranked map — magnitude effects, H4 grid, 2014–2026

Effect = mean |forward return| in ATR units, top bin − bottom bin. IR = effect / SD of the forward
return at that horizon.

| rank | variable | horizon | effect (ATR) | IR | monotone ρ | years | symbols | train → test |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | **hour of day** | 4 h | −0.211 | **−0.289** | −0.706 | **13/13** | 23/24 | −0.224 → −0.196 |
| 2 | **ATR14/ATR50** | 5 d | −1.080 | **−0.255** | **−1.000** | **13/13** | **24/24** | −1.168 → −0.970 |
| 3 | **ATR14/ATR50** | 3 d | −0.801 | −0.248 | **−1.000** | **13/13** | **24/24** | −0.858 → −0.731 |
| 4 | **ATR14/ATR50** | 1 d | −0.411 | −0.225 | **−1.000** | **13/13** | **24/24** | −0.433 → −0.383 |
| 5 | bar range / ATR14 | 4 h | +0.148 | +0.203 | **+1.000** | **13/13** | **24/24** | +0.125 → +0.176 |
| 6 | range compression (20) | 4 h | +0.131 | +0.179 | **+1.000** | **13/13** | **24/24** | +0.110 → +0.156 |
| 7 | cross-asset global vol | 4 h | +0.119 | +0.163 | +0.900 | **13/13** | 22/24 | +0.105 → +0.136 |
| 8 | ATR14/ATR50 | 4 h | −0.115 | −0.157 | **−1.000** | **13/13** | **24/24** | −0.115 → −0.114 |
| ~~9~~ | ~~weekday~~ | 4 h | −0.066 | −0.090 | −0.286 | 7/8 | **2/2** | **artefact — see below** |
| 9 | cross-asset risk state | 4 h | −0.049 | −0.066 | −0.900 | 7/8 | 23/24 | −0.070 → −0.042 |
| 10 | trend deviation / ATR | 5 d | +0.263 | +0.062 | **+1.000** | 12/13 | 16/24 | +0.272 → +0.257 |
| 11 | 24-bar momentum / ATR | 5 d | +0.217 | +0.051 | **+1.000** | 11/13 | 15/24 | +0.211 → +0.226 |

Ranks 1–8 are not scan artefacts by any reasonable standard: perfect or near-perfect monotonicity,
13 of 13 years, 22–24 of 24 symbols, and a holdout half that reproduces the training half to within
~20 %. Ranks 10–11 are weaker (two-thirds symbol agreement) and I would not pre-register them.

> **`weekday` is struck from this table by my own adversarial pass, and the mechanism is worth
> recording.** It scored well on every automated criterion and it is a **symbol-composition
> artefact**. Saturday and Sunday exist in this universe only for crypto: 3,480 and 15,408 H4 bars
> against ~74,000 for each weekday, and **exactly two of the 24 symbols (BTCUSD, ETHUSD) have bars on
> all seven levels** — which is why its per-symbol agreement reads a perfect 2/2. The "weekday
> effect" is a comparison of weekend crypto against weekday everything. Any future scan over this
> archive must either drop the weekend levels or restrict the universe before reading a calendar
> factor.
>
> *`hour`, by contrast, survives the same interrogation.* Its 12 levels are the **two US-DST phases**
> of the same six H4 anchors — every one of the 24 symbols carries bars in both phases across a year,
> which is why `symbols_measured` is 24. The pairing in the table below is by session, and the two
> DST members of each pair agree to within 0.02 ATR, which is the check that the pairing is right
> rather than a convenience.

**The two shapes, in full.**

*Hour of day* — mean |4-hour forward move| in ATR, by the window the move occurs in (H4 bar hour + 4):

| window (UTC) | 13–17 | 09–13 | 05–09 | 17–21 | 01–05 | 21–01 |
|---|---:|---:|---:|---:|---:|---:|
| mean \|move\| (ATR) | **0.680** | 0.590 | 0.560 | 0.397 | 0.373 | 0.349 |

The NY cash session carries **1.95×** the travel of the quietest window, stable across 13 years and
23 of 24 symbols. This corroborates AH's FX-D1 hour finding and AM/AQ's hour-01 entry convention from
a completely independent direction — the entry hour matters because the *available travel* differs
by a factor of two, not because of a subtle behavioural effect.

*ATR14/ATR50* — mean |forward move| in ATR, by within-symbol quintile:

| quintile | median ATR14/ATR50 | 4 h | 1 d | 3 d | 5 d |
|---|---:|---:|---:|---:|---:|
| Q0 (compressed) | 0.791 | **0.563** | **1.558** | **2.784** | **3.638** |
| Q2 | 0.984 | 0.494 | 1.330 | 2.419 | 3.149 |
| Q4 (elevated) | 1.229 | 0.448 | 1.147 | 1.983 | 2.557 |
| **Q0 / Q4** | | **1.26×** | **1.36×** | **1.40×** | **1.42×** |

**This is the most actionable structural fact in the report, and it is a geometry defect rather than
an edge.** The estate scales its stop as a multiple of ATR14 (`stop_distance_atr` median 0.986,
`risk_over_atr` median 0.959). ATR14 mean-reverts against ATR50. So a fixed ATR14-multiple stop buys
systematically **42 % more expected forward travel per unit of risk** when short-term vol is
compressed than when it is elevated — perfectly monotone, 13/13 years, 24/24 symbols. Every fixed-R
contract pegged to ATR14 is mis-scaled by ~1.4× across the vol-ratio range, predictably, for free.

### 5.3 The directional map — for completeness, because it is nearly empty

Best signed effects, H4, ranked by |IR|:

| variable | horizon | effect (ATR) | IR | years | symbols | train → test |
|---|---|---:|---:|---:|---:|---|
| ~~weekday~~ | 3 d | +0.153 | +0.047 | 7/8 | **2/2** | **artefact (§5.2)** |
| ATR14/ATR50 | 5 d | −0.182 | −0.043 | 8/13 | 19/24 | −0.046 → **−0.354** |
| ~~weekday~~ | 1 d | +0.077 | +0.042 | 7/8 | **2/2** | **artefact (§5.2)** |
| 6-bar momentum | 1 d | +0.057 | +0.031 | 8/13 | 12/24 | +0.102 → **+0.003** |
| dist to 20-bar high | 1 d | −0.054 | −0.029 | 9/13 | 13/24 | −0.104 → **+0.006** |
| USD strength | 1 d | +0.039 | +0.021 | 9/13 | 20/24 | −0.006 → **+0.089** |

**With `weekday` struck, nothing is left.** The two largest surviving signed effects have IR ≤ 0.043;
`ATR14/ATR50` grows 7.8× between the training and test halves (−0.046 → −0.354), momentum collapses
to +0.003, distance-from-extremes **inverts**, USD strength inverts. Per-symbol agreement for the
momentum and distance families is a coin flip (12/24, 13/24). That is the same reversal §3 measured at
the row level — here at the bar level, on 12 years instead of 5 months, on a completely different
construction, with the estate's labelling machinery nowhere in the pipeline. **Two independent
instruments agreeing is why the directional null is stated as a finding rather than as a limitation.**

---

## 6. The horizon question — the estate runs the worst end of the curve

`PART2_HORIZON_ASYMMETRY.json`. Cost anchor from the population itself:
`cost_atr = cost_r × risk_over_atr`, median **0.0897 ATR**, p90 0.260 (median `cost_r` 0.1124,
median `risk_over_atr` 0.9591). Cost is paid once; dispersion grows ≈ √t.

| grid | horizon | forward SD (ATR) | skew | tail ratio 2σ | **cost drag as % of 1 SD** |
|---|---|---:|---:|---:|---:|
| M15 | 1 h | 1.619 | +0.06 | 0.881 | **5.54 %** |
| M15 | 4 h | 3.404 | −0.06 | 0.928 | 2.64 % |
| M15 | 24 h | 8.901 | −0.14 | 1.010 | **1.01 %** |
| H4 | 4 h | 0.730 | −0.62 | 0.895 | **12.28 %** |
| H4 | 24 h | 1.822 | −0.16 | 0.885 | 4.93 % |
| H4 | 72 h | 3.235 | −0.01 | 0.989 | 2.77 % |
| H4 | 120 h | 4.241 | +0.01 | 1.052 | **2.12 %** |
| D1 | 24 h | 0.694 | −0.15 | 0.900 | **12.93 %** |
| D1 | 240 h | 2.292 | +0.18 | 1.204 | **3.92 %** |

*(The M15 and H4 rows for the same wall-clock horizon differ because each grid's ATR14 is computed on
its own bars — 14 M15 bars versus 14 H4 bars. Compare within a grid, never across.)*

**Two first-principles answers the estate has never asked for:**

1. **Cost drag falls as 1/√t, by construction, and it is the dominant term at the estate's horizon.**
   On the M15 grid — the grid the estate's own ATR14 lives on — cost drag falls **5.5×** from the
   1-hour to the 24-hour horizon. On the D1 grid it falls **3.3×** from 1 day to 10 days. The
   conditional structure in §5 does **not** weaken correspondingly (ATR14/ATR50's IR is 0.157 at 4 h
   and 0.255 at 5 d — it *strengthens*). **The same structure is worth several times more per unit of
   risk at a longer horizon**, and the estate's broad candidate contract runs a **2-hour label span**
   (median and modal 2.00 h over 336,430 resolved rows).
2. **The payoff distribution's asymmetry flips from adverse to favourable as horizon lengthens.**
   Skew runs −0.62 → +0.01 (H4, 4 h → 120 h) and −0.15 → +0.18 (D1, 1 d → 10 d); the 2σ tail ratio
   runs 0.895 → 1.052 and 0.900 → **1.204**. At 10 days the right tail is 20 % fatter than the left;
   at 4 hours it is 10 % thinner. For a fixed-risk, wide-target contract that is the difference
   between fighting the distribution and being carried by it.

**Note where the armed book already sits.** The three live sleeves are H4 with `time_stop_bars` 1280
(= 320 hours). The sleeve estate is *already* at the favourable end of this curve; the broad candidate
surface that keeps failing is at the unfavourable end. That is not a coincidence worth ignoring.

---

## 7. The asymmetry question — payoff geometry at fixed risk

`PART2_HORIZON_ASYMMETRY.json`, `PART2_ESTATE_CONTRACT_LADDER.json`. First-touch triple barrier from
**every bar** of **every symbol** — no entry rule, only geometry. Stop = 1 × ATR14. A bar that spans
both barriers is scored **STOP** (the estate's own labeller *censors* that case; scoring it a loss is
the strictly pessimistic alternative). Net expectancy charges the estate's own median cost.

### 7.1 The estate's own contract, lengthened (M15 grid, 2025-06 → 2026-06, 612k bars)

The estate's broad candidate geometry is **stop 0.986 ATR, target 1.479 ATR (R:R 1.5), 2-hour span**.

| target | horizon | LONG gross | LONG net | SHORT gross | SHORT net |
|---|---|---:|---:|---:|---:|
| **1.5 ATR** | **2 h** ← the estate's contract | −0.0122 | **−0.1019** | +0.0052 | **−0.0846** |
| 2.0 ATR | 24 h | −0.0255 | −0.1153 | **+0.0203** | **−0.0694** ← best of 28 |
| 3.0 ATR | 72 h | −0.0177 | −0.1074 | +0.0053 | −0.0845 |
| 5.0 ATR | 168 h | −0.0013 | −0.0910 | −0.0273 | −0.1170 |

**Not one of the 28 cells is net positive. Not one of the 140 vol-regime-conditioned cells is net
positive** (best: SHORT 2 ATR / 8 h in the lowest ATR14/ATR50 quintile, gross **+0.0783**, net
−0.0114 ± 0.0041). On the 12-year H4 grid the same is true: best unconditional cell LONG 5 ATR /
120 h at net −0.027, best conditioned cell `vol_regime` Q0 at net −0.0056.

**The single most important line in Part 2:** entered blind, this market surface is a **fair game
gross** — every gross expectancy across 28 geometries × 2 grids sits within ±0.03 R of zero — and the
*entire* deficit is cost. Independently confirmed by the candidate population: mean −0.0928 R/fill
plus median cost 0.1124 R = **+0.020 R/fill gross**.

> **Therefore: the edge a rule must generate is +0.09 R/trade of pure selection skill, just to break
> even. The out-of-sample within-window selection skill measurable from the 43 recorded features is
> +0.003 ± 0.005 R/trade** (§3.1). That is the arithmetic of the whole programme in two numbers: the
> requirement and the supply differ by a factor of thirty, and the supply is not distinguishable
> from zero.

### 7.2 One caution on "asymmetry", because it is easy to misread

On the 12-year H4 archive LONG beats SHORT at every geometry (+0.078 R at the widest cell). On the
one-year M15 archive **SHORT beats LONG at every geometry**. The long-side advantage in the long
archive is the universe's secular drift (indices and crypto, 2014–2026), not structure. A directional
tilt fitted to the H4 archive would have been wrong for the most recent year. Report it as beta.

---

## 8. Why §3 and §5 are the same finding — the bridge

`PART3_BRIDGE_VOL_REGIME.json`. `atr14_over_atr50` **is one of the 43 recorded features**. §5 shows it
carries the estate's most stable conditioning effect. So why did §3's models find nothing?

Within-symbol quintiles of `atr14_over_atr50` on the estate's own eligible population, all five months
pooled:

| quintile | median ratio | fill rate | censor rate | mean net R | mean \|net R\| | SD net R | target rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Q0 | 0.628 | **16.8 %** | **20.3 %** | −0.0895 | 0.926 | 1.087 | 15.4 % |
| Q1 | 0.823 | 19.6 % | 14.7 % | −0.1185 | 0.992 | 1.132 | 17.2 % |
| Q2 | 1.003 | 22.7 % | 10.9 % | −0.0942 | 1.034 | 1.168 | 18.9 % |
| Q3 | 1.188 | 25.1 % | 8.1 % | −0.0932 | 1.021 | 1.157 | 18.4 % |
| Q4 | 1.481 | **26.6 %** | **5.8 %** | −0.0743 | 0.986 | 1.133 | 17.5 % |

Endpoint (Q4 − Q0) and its month-to-month stability across the five months:

| quantity | mean endpoint | months agreeing with the pooled sign |
|---|---:|---:|
| fill rate | **+9.9 pp** | 5 / 5 (perfectly monotone in the pooled data) |
| censor rate | **−14.5 pp** | 5 / 5 (perfectly monotone) |
| SD of net R | +0.045 | **5 / 5** |
| mean \|net R\| | +0.059 | **5 / 5** |
| target rate | +2.1 pp | **5 / 5** |
| **mean net R (signed)** | **+0.014** | **3 / 5** — and the two dissenters are large (+0.044 vs −0.042) |

**There it is.** The strongest conditioner in the archive moves fill probability by 10 points, censoring
by 14 points, dispersion by 4.5 %, and outcome mix by 2 points — all five-of-five stable — while moving
**signed expectancy by +0.014 R against a 0.112 R cost, with the sign unstable across months.**

**The 43 features are informative. They are informative about the wrong quantity.** They predict
*whether the trade happens*, *how far it travels*, and *how it terminates*. They do not predict
*which way*. A selection model trained on signed net R is being asked for the one thing they do not
carry, and §3 measures exactly that: capture ratio 1.0 in-sample (where memorising the sign is
possible) and 0.0 out-of-sample (where it is not).

---

## 9. What would survive a pre-registered test, and what would not

Explicit, because this lane scanned 176 cells and the estate's standard demands it.

**Would survive pre-registration** — perfect or near-perfect monotonicity, 13/13 years, 22–24/24
symbols, holdout half reproducing the training half:

- **F1. Intraday travel profile.** Mean |4-hour move| in ATR varies **1.95×** by session; the NY cash
  window is the largest. IR 0.289. *A magnitude claim, not a direction claim.*
- **F2. ATR14/ATR50 → forward travel per unit of ATR14.** Monotone across all five bins at all four
  horizons; Q0/Q4 ratio 1.26× (4 h) to **1.42×** (5 d). IR 0.157–0.255. *A geometry defect in every
  ATR14-pegged fixed-R contract.*
- **F3. Volatility clustering.** Current bar range and 20-bar compression → next-bar travel, IR
  0.203 / 0.179, 13/13 years, 24/24 symbols, monotone ρ = +1.000.
- **F4. Cost drag falls as 1/√t** while conditional IR does not fall. Arithmetic, not a fit.
- **F5. Payoff skew and 2σ tail ratio improve monotonically with horizon** (tail ratio 0.90 → 1.20
  from 1 day to 10 days on D1).
- **F6. `atr14_over_atr50` → fill rate and censor rate** in the estate's own population: +9.9 pp and
  −14.5 pp, 5/5 months, monotone. This is a *data-quality* lever — 45,751 censored rows, concentrated
  in the compressed-vol quintile.
- **F7. The out-of-sample null itself.** Four model classes, two generalisation gaps, five months:
  capture ratio in [−0.047, +0.035]; within-window edge +0.003 ± 0.005 R/trade. Pre-registering
  "no usable OOS row-level information in these 43 features" would pass.
- **F8. `negative_cost` beats the frozen model at within-window ranking** (+0.0065 vs +0.0030
  R/trade, 4 of 5 months vs 2 of 5). Small, and it is a free control every future candidate should
  be measured against — a model that cannot beat "pick the cheapest" has not earned its complexity.

**Would not survive, and is named here so nobody mines it later:**

- **Every signed conditioning effect, without exception.** Momentum, distance-from-extremes, USD
  strength, trend deviation, risk state and ATR14/ATR50-on-direction all invert or collapse between
  2014–2021 and 2022–2026 (§5.3).
- The **weekday** effect, signed *and* magnitude, at every horizon. It passed every automated
  criterion in this lane's own scan and it is a symbol-composition artefact: weekends exist only for
  crypto, and only 2 of 24 symbols carry all seven levels (§5.2). Recorded as a named failure mode
  rather than quietly deleted, because the next scan over this archive will hit it too.
- The frozen rule's **+1.58 SD** over matched-count random (§4). Three of five months positive on 290
  trades; February alone supplies +14.2 R of the +0.95 R total.
- The **LONG > SHORT** asymmetry (§7.2) — it is secular drift and it reverses in the recent year.
- `vol_regime` Q0 as a **barrier cell**: best of 140 and still net −0.011 ± 0.004.

---

## 10. What this lane concludes, for the owner's question

**The surface is not empty.** ±1,530 R/month is realisable by a protocol that already exists, on
generators that already run, on data already on this machine. The frozen rule captured +0.19 R/month
of it and the armed book captures +0.48 R/month out of window. Nothing here says stop.

**The search has been aimed at the one thing the data does not carry.** Every extraction attempt in the
estate's history — the broad V4 policy switches, the ridge, the MARKET-top-choice rule, the sleeve
admission gates — ranks candidates by predicted **signed** outcome. This lane measures, four different
ways, that signed outcome is not predictable from the recorded pre-decision state one day out. It also
measures that the same state predicts travel, fill and termination with 13/13-year and 24/24-symbol
stability. **The next program should search where the structure is.** Three directions follow from the
measurements rather than from a concept, in the order the evidence supports:

1. **Fix the geometry before searching for an edge (F2 + F6).** An ATR14-pegged stop is mis-scaled
   ~1.4× across the vol-ratio range, monotonically and predictably; the same variable moves fill
   probability by 10 points and censoring by 14. Both are deterministic corrections to the contract,
   not bets. They change what every future search measures — including re-reading anything already
   read, because a censored row is a row the estate paid to generate and never got an answer from.
2. **Lengthen the contract (F4 + F5).** Cost drag falls 5.5× from 1 h to 24 h and the tail ratio flips
   from 0.90 to 1.20 by 10 days, while conditional IR does not fall. The candidate surface's 2-hour
   span is the worst point on that curve; the armed sleeves' 320-hour contract is near the best. This
   is the cheapest available change to the *ratio of edge to cost*, and it requires no new edge.
3. **Change the target, not the model.** The features predict dispersion, fill and outcome mix. Those
   are the inputs to *sizing* and *admission*, which is where AO's `vr` work and AR's tilt already
   pointed and where AR's own control correctly refused to over-claim. A model that predicts
   `P(target before stop)` or expected travel is being asked for something the data demonstrably
   carries; a model that predicts signed net R is not.

**And the standard for the next attempt, from this lane's own instruments:** the required edge is
**+0.09 R/trade**. Any candidate that cannot state its expected edge against that number, out of
sample, with **three** controls — a same-month-unseen-day fit, a shuffled-label fit, and a
`negative_cost` heuristic it must beat — has not been measured, it has been fitted. All three are in
`lane_i_receipts/scripts/` (`part1_information.py`, `part1_within_window.py`) and cost about a minute
each to run. And the skill must be reported **within decision window**, not cross-sectionally: §3.1
is the worked example of how far apart those two numbers are for the same model.

---

## 11. What I got wrong, and the limits

- **First pass understated the oracle by ~35 %** by treating `RESOLVED_NO_FILL`'s null
  `terminal_net_r` as missing rather than as the zero the frozen scorer reads it as. Corrected before
  any figure was written; the protocol equivalence receipt was added specifically so this class of
  error is detectable.
- **I first wrote "the out-of-sample top decile is at or below the population mean in 12 of 13
  cells." That was wrong** — it is *above* in 12 of 18, by +0.027 R on average. The claim survived
  only because I had read the sign off the *absolute* top-decile means (negative in 17 of 18) rather
  than the lift. §3.1 exists because of that error, and it is a better section than the sentence it
  replaced: measuring the within-window quantity resolved the apparent tension instead of arguing it
  away. The corrected reading is weaker in wording and stronger in evidence.
- **The oracle is greedy, not globally optimal.** It picks the best candidate in each window in time
  order; under the one-position-per-symbol constraint a locally worse pick can enable a better
  sequence. `gbm_is` beating the oracle by 2 % (§3) is exactly that. So +1,566.7 R/month is a **lower
  bound** on the true constrained optimum, and the ceiling is if anything understated.
- **The `gbm_oos` arm was given one fixed configuration**, not a search. A tuned OOS model might do
  better than −0.033…+0.002 capture. It would have to beat the *in-sample-same-month-different-day*
  arm, which had every advantage and still landed at −0.047…+0.016; I do not think tuning closes a
  gap that a full month of extra information does not.
- **The M15 archive is one year.** The estate-contract ladder (§7.1) therefore has no cross-period
  stability behind it. Its direction is corroborated by the 12-year H4 archive; its levels are not.
- **The 43-feature set is the frozen rule's contract, not the universe of possible features.** "No
  extractable information" is a claim about *these* features on *this* population — precisely the
  claim the estate needed, and not a claim that no feature could work. §5 names features that are not
  in the set and that do carry stable structure.
- **Two grids, two ATR normalisations.** M15-ATR14 and H4-ATR14 are different objects; every table in
  §6 and §7 compares within a grid only.
- **The armed-book comparison crosses surfaces.** Same R unit, different generators and different
  contracts. Stated in §4 rather than smoothed over.
- **Nothing here was billed against a candidate family.** This lane declares no candidate and proposes
  no rule; every number is a population property or a null. Findings F1–F7 are offered as
  pre-registration material for a future look, not as looks already taken.

---

### Receipts

`lane_i_receipts/` — `PART1_ORACLE_BAND.json`, `PART1_PROTOCOL_EQUIVALENCE.json`,
`PART1_FEATURE_INFORMATION.json`, `PART1_WITHIN_WINDOW_SKILL.json`, `PART1_CAPTURE_RATIO.json`,
`PART1_CELL_PERSISTENCE.json`,
`PART2_STRUCTURE_SCAN.json` / `.csv`, `PART2_HORIZON_ASYMMETRY.json`,
`PART2_BARRIER_UNCONDITIONAL.csv`, `PART2_BARRIER_CONDITIONAL.csv`,
`PART2_ESTATE_CONTRACT_LADDER.json` / `.csv`, `PART3_BRIDGE_VOL_REGIME.json`; every producing script
under `lane_i_receipts/scripts/`. Seeds fixed at 20260811 throughout.

**Inputs, none mutated:** `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz` (durable
copy at `/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-puzzle-cache-20260812/`);
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/{deep_universe_h4d1_2014_2026,bridge_ftmo_m15_20250601_20260610}`;
committed frozen validation results for the realised frozen-rule figures;
`research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json` for the armed-book comparison.
No live path, no config, no R2-bound file, no VPS was touched.
