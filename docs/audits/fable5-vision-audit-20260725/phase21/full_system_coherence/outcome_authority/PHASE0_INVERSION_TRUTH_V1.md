# Phase 0 — inversion truth

**Commission:** `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §4 Phase 0, the decisive experiment.
**Verdict: KILL.** No MARKET family clears the gate. Not one family-month out of 35
reaches +0.03 R/trade; **34 of 35** are outright negative, the best single cell in the
whole study is **+0.0103**, and every family's pooled result is negative at
t = −3.9 … −13.0.

Measurement job on already-read months. No new window read, no live system touched, no
config byte outside scratch. All five months (Feb/Apr/May/Jun/Jul 2026) are post-read.

---

## 0. The answer in six sentences

The inverted contract was re-walked properly — real entries, the committed labeler, the
same M1 paths, broker-true costs — and it is **negative in every family, every month**.
The plan's +0.07…+0.09 R/trade came from two errors that compound: **the sealed rows carry
a 2.0 risk-reward geometry, not the 1.5 the plan assumed** (which alone removes 75–80 % of
the claimed edge and moves the driftless benchmark from 0.400 to 0.333), and **the
arithmetic inversion never charged the inverted contract's own spread at its own
barriers** — it re-used the original walk's touch sequence, which was computed on the
opposite quote side. The plan's predicted failure mode was the wrong one: it feared
inverted-side slippage ≥ 0.15 R, and **measured slippage at realistic latency is +0.0009 R
at 100 ms and ~0 at 1–5 s** (21,449 trigger instants against the broker tick archive), with
broker-reconciled adverse fill cost of **0.0057 R** in inverted units — two orders of
magnitude below the fear. The cost that kills it was never the *new* cost: it is the
spread that was already inside the sealed walk, which on `structural_distance_extreme`
runs at a **median 0.238 R of the risk unit over the full population**, so at the inverted
contract's 2× risk unit it still costs 0.053 R against a 0.5 R payoff. The **anti-signal
itself is real and survives correction** — against a per-row driftless benchmark that
accounts for the true geometry, the actual spread and the actual fill price, the families
run z = −5.6 … −25.0 — so §1 and §2 of the plan stand; only §3's constructive conclusion
falls. **The funnel's Phase-0 kill branch fires: the pool is anti-predictive AND its
inversion is not extractable, so the program closes here.**

---

## 1. What was run

| | |
|---|---|
| candidates | the five sealed compact event sinks (`missed` ledger), 81,968 MARKET-family occurrences |
| M1 paths + spreads | `w21_score_aprmay_r3b.load_m1_sources`, hash-checked, `spread_model_v1` hour-aware, FTMO, band `mid` — the exact loader the sealed April/May and June/July reads used |
| labeler | `resolve_post_submission_m1_lifecycle` (`src/research_infra/walkforward/quote_side.py`), unmodified |
| inverted contract | same symbol, same submission instant, same expiry and horizon, same entry price level, **opposite direction, stop at the old target level, target at the old stop level**, so the approved risk distance becomes the old target distance |
| costs | spread mechanically inside `terminal_gross_r`; slippage + swap + commission carried from the sealed rows and rescaled to the inverted risk unit, exactly as `candidate_funnel_analysis._lifecycle_row` does it |

**Control (`phase0_receipts/P0_CONTROL.json`).** The same harness also re-walks the *original*
contract. Across all five months it reproduces the sealed cache **exactly: 81,968 rows
compared, 81,968 lifecycle statuses identical, 81,968 `terminal_net_r` identical, maximum
absolute difference 0.0, zero rows missing.** The inverted arm is the same function of the
same inputs with one argument triple changed.

**Population identity.** The walk's filled-n matches the plan's `INVERSION_ANSWERS.json`
**exactly, family by family and month by month** — 11,118 / 23,049 / 10,919 / 20,737 /
4,785 / 1,222 / 2,419 pooled, and all 20 per-month cells of the four headline families.
This is the same population, not a similar one.

---

## 2. The geometry error — the single largest correction

**Every sealed candidate carries `risk_reward_ratio = 2.0`, not 1.5.** Measured on all
five months: target distance / stop distance is exactly 2.0 on 81,968 / 81,968 rows
(`P0_FULL_RESULT.json → geometry`). `risk.min_rr` is indeed 1.5
(`config/agent_config.yaml:39`), but it is not what sets the barrier: the replay runs the
`momentum_exhaustion` dynamic execution policy, `final_target_r = 2.0`
(`src/research/dynamic_execution_policy.py:167-186`), and `take_profit_1` — the level the
labeler uses — is written at 2.0 R. Every compact row also carries
`dynamic_geometry_policy: momentum_exhaustion` and `risk_reward_ratio: 2.0`.

Three of the plan's §3 statements move as a result:

| plan | corrected |
|---|---|
| driftless benchmark 0.400 | **0.3333** at RR 2.0 (and 0.334–0.407 per family once the actual spread and fill price are used) |
| "the inverted risk unit is the old 1.5R target distance" | the old **2.0R** distance |
| "the inverted target pays 0.667 R_new" | **0.500 R_new** |

**The anti-signal survives this correction.** Recomputed against a per-row driftless
benchmark — `P(target first) = down_distance / (down + up)` from the *actual modelled fill
price*, which is exact for driftless continuous paths at any volatility and absorbs the
geometry, the spread side and the entry drift (`phase0_receipts/P0_CORRECTED_BENCHMARK.json`):

| family | barrier n | hit | plan bench / z | true bench / z |
|---|---:|---:|---:|---:|
| `structural_distance_extreme` | 11,008 | 0.3128 | 0.400 / −18.68 | **0.4074 / −21.61** |
| `liquidity_sweep_reclaim` | 18,642 | 0.2742 | 0.400 / −35.07 | 0.3598 / −24.99 |
| `cross_asset_lead_lag` | 9,935 | 0.3113 | 0.400 / −18.04 | 0.3746 / −13.55 |
| `displacement_continuation` | 10,904 | 0.2353 | 0.400 / −35.10 | 0.3419 / −23.78 |
| `session_open_range_break` | 1,699 | 0.1984 | 0.400 / −16.97 | 0.3417 / −12.55 |
| `volatility_compression_expansion` | 313 | 0.1022 | 0.400 / −10.75 | 0.3349 / −8.79 |
| `regime_transition_break` † | 154 | 0.1234 | 0.400 / −7.01 | 0.3341 / −5.57 |

† not in the plan's §3 table; its plan-benchmark z is computed here for comparability.

The plan's flat 0.400 **overstated** the anti-signal on five families and **understated**
it on `structural_distance_extreme` (whose large spread pushes its own benchmark above
0.400). Either way the conclusion holds: these families are directionally anti-predictive.
That is not what fails.

---

## 3. T2 — the proper inverted walk

`phase0_receipts/P0_FULL_RESULT.json`, `phase0_receipts/P0_DECOMPOSITION.json`.

### 3.1 From the plan's published number to the walk

Each step changes exactly one thing, on the identical candidate set.

| family | plan §3 | A: plan method, 0 cost, RR 1.5 | A2: same method, true RR 2.0 | B: real walk, gross | B net | B net, cost-eligible | B net, decision-instant fill |
|---|---:|---:|---:|---:|---:|---:|---:|
| `structural_distance_extreme` | +0.0927 | +0.1417 | **+0.0289** | **−0.1399** | −0.2848 | **−0.0560** | −0.0342 |
| `liquidity_sweep_reclaim` | +0.0864 | +0.1304 | +0.0424 | −0.0664 | −0.1372 | **−0.0534** | −0.0539 |
| `cross_asset_lead_lag` | +0.0718 | +0.1174 | +0.0172 | −0.1030 | −0.1907 | **−0.0658** | −0.0649 |
| `displacement_continuation` | +0.0308 | +0.0758 | +0.0259 | −0.0377 | −0.0731 | **−0.0514** | −0.0499 |
| `session_open_range_break` | −0.0061 | +0.0406 | +0.0128 | −0.0388 | −0.0702 | −0.0614 | −0.0617 |
| `regime_transition_break` | −0.0352 | +0.0194 | +0.0107 | −0.0160 | −0.0371 | −0.0368 | −0.0367 |
| `volatility_compression_expansion` | −0.0027 | +0.0542 | +0.0373 | −0.0060 | −0.0254 | −0.0226 | −0.0219 |

Reading the columns:

* **plan → A** is a near-constant **+0.044…+0.057** across all seven families. That
  identifies the plan's cost term exactly: a flat ≈0.047 R charge — the "realized cost on
  selected trades" figure from §1 — applied to the *whole* population and in *original*
  risk units. The plan's own §3 note ("at +0.05 R/side of cost the top three are
  +0.07…+0.09") is consistent. Method reproduced.
* **A → A2** is the geometry correction: **−0.113 / −0.088 / −0.100 / −0.050**. It removes
  **75–80 %** of the three headline families' claimed edge on its own.
* **A2 → B** is everything the arithmetic could not see: **−0.169 / −0.109 / −0.120 /
  −0.064**. Mechanism in §3.2.
* **B → B net** charges the sealed deductible (slippage 0.02 R flat + commission + swap),
  rescaled to the inverted risk unit.
* **cost-eligible** applies the funnel's own gate, `cost_r ≤ 0.20`
  (`candidate_funnel_analysis.py:52`). This is the population the funnel would actually
  trade and it is the honest denominator. It rescues nothing.

### 3.2 Why the real walk differs from the arithmetic

The arithmetic inversion re-used the original walk's touch sequence, which was resolved
against the *original* executable exit side. The inverted contract exits on the **other**
side, so both of its barriers shift by one spread in the adverse direction. The clean
signature is candidates on which **both** arms stop — impossible under "roles swapped"
arithmetic, routine in reality (`phase0_receipts/P0_BOTH_STOP.json`):

| family | n | both arms STOP | share | median `spread_r` |
|---|---:|---:|---:|---:|
| `structural_distance_extreme` | 13,206 | 936 | **7.09 %** | 0.2381 |
| `cross_asset_lead_lag` | 12,072 | 466 | 3.86 % | 0.1352 |
| `liquidity_sweep_reclaim` | 25,021 | 627 | 2.51 % | 0.1038 |
| `displacement_continuation` | 22,630 | 90 | 0.40 % | 0.0503 |
| `session_open_range_break` | 4,790 | 5 | 0.10 % | 0.0434 |
| `regime_transition_break` | 1,290 | 0 | 0.00 % | 0.0192 |
| `volatility_compression_expansion` | 2,959 | 0 | 0.00 % | 0.0240 |

**corr(median `spread_r`, both-stop share) = 0.995.** The path pokes into the spread band
just short of the original target — not enough for the original to win, enough for the
inverted contract's stop to trigger — and then reverses through the original stop. Both
lose. That is not a modelling artifact; it is what one spread costs when the spread is
5–24 % of the risk unit.

The same relation lets the arithmetic estimator's bias be *predicted* rather than assumed:
on the cost-eligible population, `A2 − B = 0.0189 + 0.5053 × median spread_r`, corr 0.96,
range +0.023…+0.072 (`phase0_receipts/P0_A2_BIAS.json`). This is used in T4.

### 3.3 Per family, per month (cost-eligible, inverted net R/trade)

| family | n | feb | apr | may | jun | jul | pooled | se | t |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `structural_distance_extreme` | 2,248 | −0.0287 | −0.0293 | −0.1503 | −0.0219 | −0.0795 | −0.0560 | 0.0143 | −3.92 |
| `liquidity_sweep_reclaim` | 10,640 | −0.0605 | −0.0415 | −0.0690 | −0.0488 | −0.0464 | −0.0534 | 0.0059 | −9.11 |
| `cross_asset_lead_lag` | 3,826 | −0.0566 | −0.0734 | −0.0345 | −0.0516 | −0.1150 | −0.0658 | 0.0107 | −6.16 |
| `displacement_continuation` | 16,640 | −0.0734 | −0.0538 | −0.0199 | −0.0461 | −0.0592 | −0.0514 | 0.0040 | −13.02 |
| `session_open_range_break` | 4,247 | −0.0999 | −0.0529 | −0.0297 | −0.0811 | −0.0339 | −0.0614 | 0.0067 | −9.14 |
| `regime_transition_break` | 1,205 | −0.0601 | −0.0219 | −0.0324 | −0.0517 | −0.0169 | −0.0368 | 0.0085 | −4.33 |
| `volatility_compression_expansion` | 2,319 | −0.0358 | **+0.0103** | −0.0606 | −0.0044 | −0.0286 | −0.0226 | 0.0057 | −3.95 |

**34 of 35 family-months negative; the one positive cell is +0.0103, a third of the gate.**
Hit rates, medians, worst days and drawdowns are in `P0_FULL_RESULT.json →
T2_inverted_walk`; the drawdown series is monotone for every family (max drawdown equals
the whole pooled loss, i.e. there is no recovery phase anywhere).

---

## 4. T1 — the inverted-entry cost, measured

`phase0_receipts/P0_T1_COST.json`. Four terms, each labelled MEASURED or TRANSFERRED, each in
units of the **inverted** risk distance (2× the original stop distance, so a fixed price
cost is worth half as many inverted R as original R).

### Term 1 — spread [MEASURED]

Already inside the walk: the entry transacts on the executable entry side and stop/target
are compared against the executable exit side (`quote_side.py:385-413`, `:1218-1247`), so
one round trip costs exactly one spread.

Validated at the exact trigger instants against the broker tick archive
(`/Users/borr/GTOSActive/vps-ticks-20260726/ftmo`, broker wall → UTC at a constant +3 h
over the whole archive, `new_york_plus_7`; 21,502 candidates inside coverage, 21,449 with
a quote fresher than 60 s at both instants, all 24 surface symbols, 88.7 M ticks scanned):

* quoted `spread/risk` at the decision instant: **tick median 0.0983 vs model 0.0906**;
* **ratio tick/model: median 1.000, p10 0.790, p90 1.561**; the model under-charges on
  **39.9 %** of trigger instants and under-states the *mean* by 14 % (0.2024 vs 0.1772).

**Uncertainty band on the spread term: ×[0.79, 1.56] per trigger, unbiased at the median.**
Coverage caveat: the tick archive spans 2026-06-18…07-26 broker wall, so this validates
June and July directly and is *transferred* to February, April and May. The spread model's
own reference window is the same archive, so its anchor levels are in-sample there;
`era_ratio` is what carries them back, and the model publishes a low/high band for exactly
that reason (see term 1b).

Median spread in inverted risk units, cost-eligible population: `structural_distance_extreme`
0.0533, `cross_asset_lead_lag` 0.0335, `liquidity_sweep_reclaim` 0.0278,
`displacement_continuation` 0.0201, `session_open_range_break` 0.0188,
`volatility_compression_expansion` 0.0110, `regime_transition_break` 0.0093. Over the
**full** population `structural_distance_extreme` runs 0.238 in original units — which is
why only **18.65 %** of its candidates (2,463 of 13,206) pass the funnel's own
`cost_r ≤ 0.20` gate.

### Term 1b — spread-model band [MEASURED]

The whole five-month walk was re-run at the spread model's **low** band, the most
favourable case for the inversion. See §8.

### Term 2 — entry timing [MEASURED]

The labeler refuses the submission bar as causal and fills MARKET at the **open of the
first complete successor M1 bar** (`quote_side.py:1278-1290`), i.e. 60 s after the decision
instant. A live book places at the decision instant. This is the term the plan called
"entering WITH momentum", and it is measurable two ways:

* **from M1, all five months.** Tape drift over that minute, signed against the original
  direction, on the cost-eligible filled population: `structural_distance_extreme` +0.0417,
  `cross_asset_lead_lag` +0.0144, `liquidity_sweep_reclaim` +0.0060, others |·| < 0.005 in
  original risk units — i.e. the walk hands the inverted contract a better entry than a
  live fill would, worth up to **+0.021 R** in inverted units on `structural_distance_extreme`.
  It is not a uniform windfall: on the rows the inverted arm *censors* (gap through a
  barrier) the same drift averages **−1.01 R**, so the filled-row windfall and the censoring
  loss are opposite-signed and must not be counted separately.
* **from ticks, June–July.** The same quantity on the executable entry side: mean −0.00217
  R pooled, per family −0.0166…+0.0174, correlating 0.70–0.98 with the M1 measure row by row.

**Settled by re-walking rather than by adjustment.** Handing the resolver a submission time
one minute earlier makes the *decision* minute the first complete successor, so the fill is
the executable-side open at the decision instant — a genuine live-realistic fill with no
change to the labeler, the barriers, the spreads or any censoring rule. Result, cost-eligible,
in the table in §3.1: **`structural_distance_extreme` improves to −0.0342, every other family
moves by less than 0.002 R.** The 60-second fill convention is **not** a material bias in
either direction, because the windfall on filled rows is offset by the gap rows it censors.

### Term 3 — execution slippage [MEASURED for latency; TRANSFERRED for broker fills]

* **Latency drift**, from ticks, signed against the original direction, original risk units,
  21,449 trigger instants: **+0.00094 R at 100 ms (se 0.00044), +0.00113 at 250 ms,
  +0.00002 at 1 s, −0.00006 at 5 s.** In inverted units that is **≤ 0.0006 R**. The plan's
  falsifier — "inverted-side slippage ≥ 0.15 R would erase the entire repair" — is
  **refuted by a factor of ~250**.
* **Broker-reconciled fills**: `phase21/cost/SLIPPAGE_PRICE_V1.json`, 138 accepted rows,
  `mean(max(0, directional slippage))` over reconciled entries. Candidate-weighted over the
  15 surface symbols it covers: **0.0057 R in inverted units** (range 0.000 for
  GER40/NZDUSD/UK100/US30_cash to 0.0205 for NAS100). **TRANSFERRED, not measured**: these
  are the armed estate's own entries in 2026-06/07, carry no momentum conditioning, and
  cover 15 of 24 symbols at n = 1–11 per symbol.
* For reference the sealed replay charged a **flat 0.02 R on every row of every symbol**
  (`config.selected_cell_default_expected_slippage_r`,
  `broker_net_cost_engine.py:718-728`) — i.e. **3.5× the broker-reconciled figure**, so the
  walk's slippage charge is already conservative.

### Term 4 — commission and swap [carried]

Unchanged from the sealed rows, rescaled to the inverted risk unit.

### The T1 answer

**Measured inverted-entry execution cost: 0.0057 R (broker-reconciled adverse fill) +
≤0.0006 R (latency drift) ≈ 0.006 R in inverted risk units.** The walk already charges
0.010 R in inverted units for slippage (the flat 0.02 R original-unit constant), so **the
incremental cost of entering with momentum, over what is already charged, is zero to
slightly negative** — the sealed cost model is conservative on this term.

**Uncertainty band.** The dominant uncertainty is not slippage, it is the spread. At the
tick-measured per-trigger band of ×[0.79, 1.56] applied to the largest-spread family
(`structural_distance_extreme`, median 0.0533 R inverted) the result moves by
**−0.011 … +0.030 R**; on the other six families the same band is worth −0.002 … +0.019 R.
The independently re-walked low spread band lands inside that (+0.0014 … +0.0041, §8).
The broker-fill term carries its own band from n = 1–11 per symbol over 15 of 24 symbols,
but at 0.006 R its whole plausible range is smaller than the spread band.

**Total honest envelope on the inverted result: −0.075 … −0.025 R/trade.** The gate is
+0.03. Per-family and per-symbol-class detail is in `P0_T1_COST.json` and
`P0_TICK_COST.json`.

---

## 5. T3 — the time-stop question, resolved exactly

`P0_FULL_RESULT.json → T3_time_stops`. The plan flagged its `−gross/1.5` re-pricing as the
weakest approximation. The walk resolves the bucket exactly — `terminal_gross_r =
direction × (last complete pre-horizon executable-exit-side close − fill price) / risk` —
so no approximation is needed.

| family | inverted time-stop share | time-stop mean net R | barrier mean net R | time-stop share of total net | exact vs `−gross/2.0` | exact vs plan's `−gross/1.5` |
|---|---:|---:|---:|---:|---:|---:|
| `volatility_compression_expansion` | 89.3 % | −0.0600 | **+0.2623** | 210 % | −0.033 | −0.030 |
| `regime_transition_break` | 88.3 % | −0.0771 | **+0.2637** | 183 % | −0.025 | −0.014 |
| `session_open_range_break` | 65.9 % | −0.1548 | **+0.0936** | 145 % | −0.048 | −0.020 |
| `displacement_continuation` | 48.8 % | −0.1868 | **+0.0354** | 125 % | −0.058 | −0.024 |
| `liquidity_sweep_reclaim` | 20.2 % | −0.2647 | −0.1050 | 39 % | −0.083 | −0.036 |
| `cross_asset_lead_lag` | 9.7 % | −0.2906 | −0.1800 | 15 % | −0.115 | −0.071 |
| `structural_distance_extreme` | 1.2 % | −0.4098 | −0.2833 | 2 % | −0.168 | −0.115 |

Three things follow.

1. **The time-stop bucket is uniformly negative for the inverted contract** and it is what
   converts a positive barrier expectancy into a negative total on the four high-time-stop
   families. `displacement_continuation` — the plan's named exposed case at 47 % — has a
   **positive** barrier bucket (+0.0354) and a **−0.1868** time-stop bucket; the bucket is
   **125 %** of its net loss. `structural_distance_extreme`, the plan's named safest case at
   1 %, has the study's **largest per-time-stop error (−0.168 R)** but the smallest exposure
   to it — 1.2 % of its trades, so it contributes ~0.002 R to that family's total. **The
   plan's reliability ranking is inverted at the per-trade level and correct only at the
   bucket level**, because the error scales with spread, not with time-stop share.
2. **The plan's approximation was optimistic in every family**, by −0.014 to −0.115 R.
   Mechanism: negating the original's gross implicitly awards the inverted contract a
   spread *credit* where a real walk charges it. Predicted residual ≈ one `spread_r`;
   measured residual vs the RR-correct approximation is −0.033 (`spread_r` 0.024), −0.058
   (0.050), −0.083 (0.104), −0.168 (0.238) — the relation holds across a 10× range.
3. **A wider target does not rescue any of it.** The inverted contract's target is the old
   stop level and cannot be moved without abandoning the inversion premise.

---

## 6. T4 — the LIMIT families

`phase0_receipts/P0_T4_LIMIT.json`.

**Is an inverted LIMIT contract well-defined? YES — but it is a different order type.**
The three LIMIT families rest a pending entry away from the market
(`limit_marketable_at_decision` false on **98.74 %** of 550,966 rows over the five months;
median `distance_to_limit_risk` **4.71** risk units, IQR 2.30–8.87). A LONG resting below the market is a BUY LIMIT; inverting the side while
keeping the level makes it a SELL order below the market, i.e. a **SELL STOP**. The trigger
*event* is nearly identical (price falling to the level) but two things change: the trigger
quote side flips (a BUY LIMIT/STOP triggers on the ASK, a SELL on the BID —
`quote_side.entry_trigger_level_on_tape`, citing `execution.py:6197`), and — the
substantive change — **the fill-price convention inverts**. A LIMIT fills at its level *or
better*; a STOP fills at its level *or worse*. The plan's premise that fill dynamics change
is correct and the direction is adverse to the inversion.

**Is it measurable with the committed machinery? NO.** Demonstrated, not asserted: running
the committed resolver on the inverted LIMIT contract over one full trading day, 4,360
candidates, **4,258 (97.7 %) censor as `CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING`** and
only 21 resolve. The cause is structural — `limit_touched` is hardwired to the direction
(`quote_side.py:1249-1250`), so flipping a BUY LIMIT asks whether the *high* reached a
level *below* the market, which is true at the submission bar.

**Machinery required, exactly:**

1. a `STOP` order type in `resolve_post_submission_m1_lifecycle` with (a) the
   direction-inverted touch predicate, (b) **adverse** gap fill at the executable-side open
   rather than at the level — the existing
   `FAVORABLE_EXECUTABLE_SIDE_M1_OPEN_THROUGH_LIMIT` branch (`:1300-1310`) grants price
   improvement and would systematically flatter the inverted contract (it fired on 10 of
   775 fills in the demo day, so the bias is small but real), (c) an
   already-through-at-submission disposition that fills at market instead of censoring, and
   (d) its own rule for a stop trigger and a terminal touch inside one M1 bar;
2. a matching generator hook so the inverted contract is emitted rather than reconstructed;
3. tests pinning that a STOP fill is never better than its level — the one property the
   LIMIT branch deliberately violates.

Scope: one focused session on `quote_side.py` and its test module.

**Bounded estimate, so the decision is not left open.** The A2 estimator runs straight off
the sealed labels, and this session measured its bias against a real walk on seven MARKET
families: `bias = 0.0189 + 0.5053 × median spread_r`, corr 0.96. Applied to the LIMIT
families on the cost-eligible population:

| family | eligible n | median `spread_r` | A2 | predicted bias | **bounded estimate** |
|---|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 36,786 | 0.0829 | +0.0119 | +0.0608 | **−0.0488** |
| `current_ob_retest` | 4,829 | 0.0480 | −0.0088 | +0.0431 | **−0.0519** |
| `current_breaker_re_entry` | 1,959 | 0.0560 | −0.0275 | +0.0472 | **−0.0747** |

`current_fvg_fill` — the estate's largest family at 305k candidates — carries the only
positive A2 in the study (+0.0119) and is still **−0.049 after the measured bias
correction**, below the gate by 0.08 R. The bias transfer assumes the inverted LIMIT walk
behaves like a MARKET one at the barriers; it does not adjust for the adverse stop-entry
fill, which moves the estimate further **down**. So the bound is conservative in the
direction that matters. **Building the STOP machinery to measure it exactly is not
warranted by this bound.**

---

## 7. T5 — adversarial pass

`P0_FULL_RESULT.json → T5_adversarial`.

**(a) Fill/labeling asymmetry favouring the stop side.** Two candidate mechanisms found and
both measured, neither manufactures the anti-signal. (i) The 60-second-late modelled fill:
settled by re-walking with a decision-instant fill (§4 term 2) — moves six of seven
families by < 0.002 R. (ii) The spread's asymmetric effect at the barriers: this *is* real
and is the both-stop effect of §3.2, but it acts against **both** arms, not toward the stop
side of one. The decisive check is that the anti-signal survives a benchmark computed from
the **actual fill price on the actual executable side**, which absorbs any such asymmetry
by construction: z = −5.6 … −25.0 (§2). Additionally, hit rate by spread quintile shows the
anti-signal in **every one of 35 quintiles**, including the cheapest: at q1 the z-scores are
−2.33 (`cross_asset_lead_lag`, median `spread_r` 0.037), −11.16 (`displacement_continuation`,
0.016), −9.67 (`liquidity_sweep_reclaim`, 0.029), −2.84 (`structural_distance_extreme`,
0.072), −8.26 (`session_open_range_break`, 0.017). It is not a cost artifact concentrated in
expensive rows. The *magnitude* does grow with spread on three families
(`structural_distance_extreme` −2.84 → −21.45 across quintiles), which is the expected
signature of a spread that widens the entry-side barrier gap, not of a fabricated signal.

**(b) Exclude the single worst symbol per family.** Nothing moves:

| family | worst symbol | all | ex-worst | months positive |
|---|---|---:|---:|---:|
| `structural_distance_extreme` | US30_cash | −0.0560 | −0.0511 | 0 |
| `liquidity_sweep_reclaim` | XAUUSD | −0.0534 | −0.0529 | 0 |
| `cross_asset_lead_lag` | NAS100 | −0.0658 | −0.0627 | 0 |
| `displacement_continuation` | UK100 | −0.0514 | −0.0503 | 0 |
| `session_open_range_break` | AUDJPY | −0.0614 | −0.0559 | 0 |
| `regime_transition_break` | EURJPY | −0.0368 | −0.0336 | 0 |
| `volatility_compression_expansion` | EURGBP | −0.0226 | −0.0193 | 1 |

**(c) Within-month stability, first half vs second half.** **7 of 70 half-month cells are
positive.** Five families are 0/10. `structural_distance_extreme` is 4/10 with 4 sign flips
— consistent with noise around a negative mean, not with a real edge.

**(d) Portfolio constraint — one trade per decision window rather than counting every
candidate.** Ranked by lowest cost (no model, so no selection leakage), cost-eligible:

| family | trades | mean R | total R | months positive | worst day | max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| `displacement_continuation` | 4,363 | −0.0512 | −223.4 | 0 | −15.59 | −223.4 |
| `liquidity_sweep_reclaim` | 4,590 | −0.0476 | −218.3 | 0 | −14.26 | −235.6 |
| `cross_asset_lead_lag` | 2,234 | −0.0558 | −124.7 | 0 | −9.20 | −124.8 |
| `structural_distance_extreme` | 1,525 | −0.0703 | −107.3 | 0 | −7.40 | −120.6 |
| `session_open_range_break` | 1,507 | −0.0496 | −74.7 | 0 | −7.85 | −74.7 |
| `volatility_compression_expansion` | 1,195 | −0.0267 | −32.0 | 1 | −5.43 | −32.3 |
| `regime_transition_break` | 791 | −0.0252 | −19.9 | 0 | −2.80 | −21.1 |

Max drawdown equals the total for five of seven — the equity curve never recovers anywhere.

**(e) Direction mapping, checked independently rather than trusting §1's last row.** Two
tests. **Structural:** the labeler refuses any row whose stop/entry/target ordering
contradicts its declared side (`CENSORED_GEOMETRY`, `quote_side.py:1148-1152`), so a
systematic side/geometry mismatch is bounded by that censor count — **695 of 81,968
(0.85 %)**, and those are geometry failures of every kind, not side errors. **Economic:**
over 120 symbol-months with ≥40 filled candidates and both sides present, the correlation
between the symbol's own price move over the month and (mean LONG gross R − mean SHORT
gross R) is **+0.562**, with **78.3 %** sign agreement. Longs earn on symbols that rose.
The mapping is correct.

**What the adversarial pass killed:** nothing of the result — every attack left the
inversion negative. What it did kill is **two of my own intermediate readings**: that the
60-second fill convention was a material conservative bias against the inversion (it is
not, once its censoring is accounted for), and that the entry-timing windfall could be
subtracted as a standalone adjustment (it cannot — the windfall and the censoring are the
same phenomenon with opposite signs, which is why the question had to be settled by a
re-walk rather than by arithmetic).

---

## 8. Spread-band sensitivity

The entire five-month walk was re-run at the spread model's **low** band — the most
favourable spread assumption the model publishes — with the loader otherwise byte-identical
(same manifest, same per-file sha256 checks, same schema, chronology and 24-symbol
denominator; only `spread_for(..., band=)` changes). `phase0_receipts/P0_SPREAD_BAND.json`.

The low band is a real reduction, not a rounding: `spread_for` returns 0.58× (USOIL_cash),
0.83× (EURUSD), 0.90× (US30_cash), 0.91× (XAUUSD) of the mid band.

| family | mid band | low band | Δ | months ≥ +0.03 at low band |
|---|---:|---:|---:|---:|
| `structural_distance_extreme` | −0.0560 | −0.0519 | +0.0041 | 0 / 5 |
| `cross_asset_lead_lag` | −0.0658 | −0.0622 | +0.0036 | 0 / 5 |
| `liquidity_sweep_reclaim` | −0.0534 | −0.0506 | +0.0028 | 0 / 5 |
| `displacement_continuation` | −0.0514 | −0.0489 | +0.0025 | 0 / 5 |
| `session_open_range_break` | −0.0614 | −0.0590 | +0.0024 | 0 / 5 |
| `regime_transition_break` | −0.0368 | −0.0354 | +0.0014 | 0 / 5 |
| `volatility_compression_expansion` | −0.0226 | −0.0212 | +0.0014 | 0 / 5 |

**At the most favourable published spread the answer does not change**: no family clears
+0.03 in any month, best single cell +0.0114. The high band would move every row the other
way and was not run.

---

## 9. The gate

> **Gate (plan §4 Phase 0):** at least one MARKET family clears **+0.03 R/trade after true
> costs in ≥4 of 5 months**, with the cost term measured on inverted entries.

| family | pooled R/trade (cost-eligible) | months ≥ +0.03 | **PASS** |
|---|---:|---:|:--:|
| `structural_distance_extreme` | −0.0560 | 0 / 5 | **NO** |
| `liquidity_sweep_reclaim` | −0.0534 | 0 / 5 | **NO** |
| `cross_asset_lead_lag` | −0.0658 | 0 / 5 | **NO** |
| `displacement_continuation` | −0.0514 | 0 / 5 | **NO** |
| `session_open_range_break` | −0.0614 | 0 / 5 | **NO** |
| `regime_transition_break` | −0.0368 | 0 / 5 | **NO** |
| `volatility_compression_expansion` | −0.0226 | 0 / 5 | **NO** |
| `current_fvg_fill` (LIMIT, bounded) | −0.0488 | — | **NO** |
| `current_ob_retest` (LIMIT, bounded) | −0.0519 | — | **NO** |
| `current_breaker_re_entry` (LIMIT, bounded) | −0.0747 | — | **NO** |

**ANY FAMILY PASSES: NO.** The gate is missed by 0.05–0.10 R per trade, in every family, in
every month, under every robustness cut, at both spread bands, and at both fill conventions.

**The plan's kill branch fires as written:** *"if the whole edge is inside the slippage, the
funnel program closes honestly and effort redirects to the armed estate."* The edge is not
inside the slippage — slippage is 0.006 R — it was inside an arithmetic error. The
conclusion is the same and it is cheaper: the funnel V2 program should close at Phase 0.
Phases 1–3 were conditional on this gate and are not reached.

---

## 10. What is left standing, and what a successor should not redo

**Standing from the plan (unaffected by this work):**

* §1 and §2 — every layer's verdict, including the pool being uniformly negative, cell
  concentration, prequential momentum-chasing, and the selector's genuine relative skill.
* The anti-predictive finding itself, at corrected magnitudes (§2 above).
* The observation that `FAMILY_TARGET_RR` is `"UNCHOSEN"` — and it is now *worse* than the
  plan said, because the effective target is not even the sanity floor it names: it is 2.0,
  set by a dynamic execution policy that no artifact in the funnel lineage cites.

**Falsified:**

* §3's constructive conclusion — the inversion is not worth +0.07…+0.09 R/trade; it is
  worth −0.02…−0.07, and −0.05…−0.07 on the three headline families.
* §6 item 1, the plan's own most-likely failure mode — inverted-side slippage is 0.006 R,
  not ≥0.15 R.
* §6 item 2's ranking of reliability — the time-stop approximation is optimistic in
  **every** family, and `structural_distance_extreme` (named safest, 1 % time stops) has the
  **largest** per-trade approximation error, −0.168 R, because the error scales with spread
  rather than with time-stop share.

**Not falsified, and left open:** §6 item 3's concern that `current_fvg_fill` is unmeasured
under inversion. It is now *bounded* (−0.049), not measured. If a successor wants the exact
number, §6 lists the machinery; the bound says it is not worth building.

**Corroboration that does not transfer.** The plan cites Session CQ's inverted
`current_breaker_re_entry` at +11.9 net R/trade (`CANDIDATE_FAMILY_V27.json`) as
independent support. That is a different object: a specific 5D/0.25D exit contract on a
sleeve-registry generator, not this family's 2.0R candidate geometry, and this session
measures the funnel's `current_breaker_re_entry` inversion at a bounded −0.075. The two are
not in conflict and neither supports the other.

---

## Receipts

All under `phase0_receipts/`, with the scripts that produced them.

| file | what |
|---|---|
| `P0_CONTROL.json` | the original arm vs the sealed cache: 81,968 rows, 0 mismatches |
| `P0_FULL_RESULT.json` | T2, T3, T5 and the gate |
| `P0_DECOMPOSITION.json` | plan → A → A2 → walk → net → eligible → live-fill, per family |
| `P0_RECONCILIATION.json` | estimator comparison, cross-tabs, spread and cost distributions |
| `P0_T1_COST.json` | the four cost terms with their bands |
| `P0_T4_LIMIT.json` | the LIMIT verdict, the measured degeneracy, the bounded estimate |
| `P0_TICK_COST.json` | tick-measured spread and latency drift at the trigger instants |
| `P0_CORRECTED_BENCHMARK.json` | per-row driftless benchmark and corrected z |
| `P0_BOTH_STOP.json` | the spread-band mechanism |
| `P0_A2_BIAS.json` | the arithmetic estimator's measured bias vs spread |
| `P0_SPREAD_BAND.json` | low-band re-walk |
| `p0_walk.py` | the two-arm walk (and the band-parameterized loader) |
| `p0_live_arm.py` | the decision-instant-fill arm |
| `p0_ticks.py` | tick-archive spread and latency measurement |
| `p0_control.py`, `p0_full.py`, `p0_reconcile.py`, `p0_decompose.py`, `p0_t1_cost.py`, `p0_t4_limit.py` | analysis |

Inputs, unmodified: `/private/tmp/w21-market-top-{feb-r2,aprmay-r3,junjul-r4}` (sealed
candidate roots, durable copies in the evidence hold);
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/`
(M1); `/Users/borr/GTOSActive/vps-ticks-20260726/ftmo` (ticks);
`docs/audits/fable5-vision-audit-20260725/phase21/cost/SLIPPAGE_PRICE_V1.json`;
`/private/tmp/w21-puzzle-cache` (the plan's own receipts, read-only).
