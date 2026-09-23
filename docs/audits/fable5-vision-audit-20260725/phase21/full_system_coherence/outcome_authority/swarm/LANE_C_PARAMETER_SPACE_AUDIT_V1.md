# LANE C — the broad-origin parameter space: what has been searched, and what never has

> ## ⛔ SUPERSEDED IN TWO PLACES 2026-08-12 — `LANE_G_RECONCILIATION_V1.md` §2, §2.3, §3, §4
>
> **This lane's arithmetic was reproduced exactly. Two of its readings are amended; the body
> below is left as written.**
>
> **1. "Eight of ten families are gross-positive" (§3.1, §5) — AMEND to "gross expectancy is
> zero".** `net + cost_r` is not "edge before avoidable cost"; it is the **tape travel** of the
> trade, which is zero under a driftless tape *by construction*. Measured on the seven MARKET
> families it is **+0.0078 ± 0.0042 R/fill** (95 % CI **[−0.0004, +0.0160]**, n = 74,249), and a
> **direction-flipped control on the identical paths** gives **+0.0055 ± 0.0042**, paired
> difference **+0.0012 ± 0.0075** (t = +0.16). The three LIMIT families' +0.049…+0.053 is
> **1.01× / 1.07× / 1.15× half their own mean spread** — the signature of a resting order filling
> at a local extreme of the sampled path, and independently bounded by Lane D's G3 mirror-limit
> control at **≈0.179 R/trade, 3.3× larger than the number it would have to explain**. With the
> spread left where the repaired walker puts it, the funnel population is **0 of 10
> gross-positive**, from −0.0219 (`regime_transition_break`) to −0.2796
> (`structural_distance_extreme`) — Lane D's number, on Lane D's basis, arrived at
> independently. [`lane_g_receipts/martingale.json`, `mirror_result.json`, `final_checks.py`]
>
> **2. The stop-width thesis (§0.3, §4.4, §5) — STRENGTHENED AND BOUNDED.** This lane is
> **right** that `moonshot_broader_origin_stop_width_atr_scale` is the only unsearched axis
> arithmetically connected to the dominant loss term: `cost_r` is cost-in-price divided by the
> stop distance, so doubling the stop halves `spread_r` *and* halves the position at fixed
> fractional risk — nothing else on the parameter surface touches the term that is 100 % of the
> measured loss. **But the ceiling is break-even, not profit.** The gross edge it would collect
> is measured at zero (point estimate +0.0078, upper 95 % bound +0.016). At a median MARKET
> `spread_r` of 0.087, pushing the cost term below the **upper** bound needs a stop ≈**5.4×
> wider**, and the point estimate of net there is still ≈−0.008 R/fill. **Commission the sweep as
> a bound-establishing experiment, not as a repair; no plan should be built on it producing a
> positive.** The one honest caveat in the other direction: an edge of +0.05 R/fill is excluded
> by this population (10 σ), an edge of +0.01 is not — so if a *generator* change moved gross to
> +0.05, a stop wide enough to hold `spread_r` near 0.02 would make it a real strategy. That is a
> statement about a different pool.
>
> **3. This lane and Lane E were never in conflict.** A martingale identity forces
> `p_target = 1/3 − P(ts)·E[cf|ts] / (3·P(bar))`, so a positive time-stop bucket
> **arithmetically requires** a target-hit rate below ⅓. Lane C's positive residual and Lane E's
> below-null hit rate are the same fact seen from two sides, and Lane E's own corridor
> withdrawal removes the interpretation of both. See the header on `LANE_E_GENERATOR_LOGIC_REVIEW_V1.md`.
>
> **Scope.** All of the above is decisive **for these ten broad-origin candidate families only**.
> It says nothing about the armed sleeve estate, AD's exit frontier, or the pooling merges.

**Owner-commissioned swarm, lane C. 2026-08-11.** Analysis only; no live path, config, or VPS
touched. Receipts: `lane_c_receipts/` (8 JSON artifacts + the 8 scripts that wrote them).

Commission: *the estate concluded "these setups have no edge" when what it actually tested was
"these setups at parameters nobody ever designed."* Establish, per family, what parameter space has
ever been searched and what has never been searched at all; measure whatever sensitivity the cached
five-month population can support; price a real design search.

---

## 0. THE ANSWER, IN FOUR SENTENCES

1. **The commission's premise is half right, and the half that is right is not the half it names.**
   Exit geometry — target multiple, stop multiple, horizon, direction — has been searched *hard*
   for these families: 198 cells (CQ), **5,148 population-cell evaluations** (FB), an 11-point stop
   ladder and a 21-cell price grid (g3), a 240-cell exit grid (L4), a 16-point stop sweep (L2), and
   a 5-point generator stop-width scale. What has **never been varied, not once, in any measurement
   in this estate** is the *entry* side: every entry-trigger constant inside
   `broader_origin_generators.py`, the decision timeframe (M15), the stop *rule* (as opposed to the
   stop *width*), and symbol/session/regime as *generation* parameters.

2. **On the axis the estate did search, its own evidence says the axis is not the problem** — L2's
   12× stop sweep moves nothing beyond a CI, g3's 2.83× natural experiment is +0.033 bps
   [−0.346, +0.435], the scale-4 argmax is still mean-negative, and p2's target-deletion effect
   fails a coin-flip side placebo. On the axis it never searched, this lane finds the families are
   **flat in their own trigger variables on gross outcomes**: of 21 own-trigger tests, **zero**
   produce a positive gross gradient that survives the cost and fill-rate controls.

3. **The economically decisive number is neither.** Across all ten emitting families the mean
   **gross** outcome per fill is **−0.023 R to +0.055 R** — a coin flip — while the **cost charged
   is 0.09 R to 0.58 R per fill**, i.e. **2× to 58× the gross edge**. The negative result is not a
   verdict on the setups; it is a verdict on a contract whose R unit (a 0.10–0.25 × ATR14 M15 stop)
   is smaller than its own transaction cost. That geometry was inherited, not chosen — and the one
   knob built to fix it (`moonshot_broader_origin_stop_width_atr_scale`,
   `broader_origin_generators.py:1263`) has **never been set in the five-month outcome-authority
   lane**.

4. **So the better-supported description is "never designed" for the entry side and "adequately
   searched, negative" for the exit side — with the caveat that this lane can only test the
   *tightening* direction of an entry constant, and it finds no family that a tighter threshold
   rescues.** Two cells clear a max-T bar in the tightening direction
   (`displacement_continuation` p 0.0105, `cross_asset_lead_lag` p 0.0238) at 2–5 % retention,
   n = 415–546 over five months; both are in-sample, uncorrected for the estate's prior spend, and
   at that retention the whole family is ~85 trades/month across 24 symbols. **`structural_distance_extreme`
   moves monotonically the WRONG way in its own trigger** — the single cleanest evidence in this
   lane that a family's stated idea is not in its data.

---

## 1. WHAT THE FUNNEL FAMILIES ACTUALLY ARE, AND WHERE EVERY CONSTANT COMES FROM

Thirteen declared families (`broader_origin_generators.py:68-91`): ten `PRODUCTION_ORIGIN_FAMILIES`
plus three `CURRENT_FRAMEWORK_ORIGIN_FAMILY` rows. Ten emit in the outcome-authority lane;
`range_extreme_reversion` and the two microstructure families are behind default-off keys
(`:476-480`) and emit **zero** rows in all five months (`lane_c_receipts/LANEC_FAMILY_BASELINE.json`).

### 1.1 The entry-trigger constants, cited

| family | entry trigger, verbatim | line |
|---|---|---|
| `structural_distance_extreme` | `pos50 >= 0.97` (SHORT) / `<= 0.03` (LONG), lookback 50 | `:1709`, `:1727` |
| `liquidity_sweep_reclaim` | `bar.high > p_high20 and bar.close < p_high20` — lookback 20, **no depth threshold**, both legs in one M15 bar | `:1555` |
| `displacement_continuation` | `bar_range/atr14 >= 1.5` **and** `body/atr14 >= 0.75` | `:1592` |
| `volatility_compression_expansion` | prior `atr14/atr50 <= 0.75` **and** `bar_range/atr14 >= 1.25`, 20-bar channel | `:1620` |
| `session_open_range_break` | fixed session windows; **range length = 30 min, an artefact of `range_start_index + 1`**; no width filter | `:176`, `:1779` |
| `regime_transition_break` | trend-state flip + close beyond the prior-20 extreme | `:1665-1670` |
| `cross_asset_lead_lag` | `leader_impulse >= 1.0` **and** `lag_response <= 0.5`, fixed `LEAD_LAG_PAIRS` | `:237`, `:1900` |
| `range_extreme_reversion` (off) | thrust cap `bar_range < 1.5×atr14`, buckets 0.25 / 0.75 | `:1519`, `:1526` |
| microstructure ×2 (off) | `STOP_ATR_MICROSTRUCTURE = 2.5`, `_VOL_SMA_N = 20`, `_RANGE_POS_N = 48`, absorption `eff <= 0.6×baseline` | `:1367-1369`, `:1407` |
| `current_fvg_fill` / `_ob_retest` / `_breaker_re_entry` | `poi_proximity_tolerance_pct = 0.01`, entry at **zone midpoint** | `:2641-2656`, `:2658-2672` |

### 1.2 The stop rule, cited

Formulaic in every family, and always an ATR fraction off the trigger bar's own extreme:
`0.25 × atr14` (`:1565`, `:1717`, `:1593`), `0.20 × atr14` (`:1629`), `0.10 × atr14` (`:1673`,
`:1798`), `1.0 × atr14` (`:1534`), `2.5 × atr14` (microstructure only, `:1367`), or a config
`sl_buffer_*_atr_multiplier` off the POI zone edge (`:2673-2705`).

### 1.3 The target, and the two different unchosen numbers

`FAMILY_TARGET_RR` (`:3557-3602`) marks **all thirteen rows `UNCHOSEN`**, and the policy that reads
it is behind `broad_origin_target_policy_enabled`, default **False** (`:3607`, `:3697`). So the
target resolves to `risk.min_rr`, whose own config comment reads *"vNext sanity floor only; dynamic
policy sets live targets"* (`config/agent_config.yaml:39`).

**Measured, this lane:** on the five-month outcome-authority population the implied RR is **1.5 on
121,302 / 121,302 February rows exactly** (`target_distance_atr / stop_distance_atr`), i.e. the
`min_rr` floor. On the sealed replay rows it is **2.0**, written by
`dynamic_execution_policy.momentum_exhaustion_policy(final_target_r=2.0)`
(`src/research/dynamic_execution_policy.py:167-171`). **Two different inherited numbers on two
different populations, neither chosen for any family.**

One structural consequence worth knowing: because the current-framework families enter on a **LIMIT
at the zone midpoint**, a fill improves the entry and shrinks the realised risk, so the *realised*
target multiple runs above the declared 1.5 — median `terminal_net_r` on target fills is **1.898**
(February, n=6,117). The declared and the realised geometry are not the same number.

### 1.4 The horizon and the timeframe

`pending_expiry_minutes=120` (`w21_generate_day_r2.py:116`, `r2b.py:110`) — the 2-hour funnel
lifecycle. `timeframe="M15"` is hardcoded at `broader_origin_generators.py:406`, `:418`, `:448`,
`:1876`, `:2127`; **one M15 `BarSeries` drives every family**, while the campaign itself resolves
four decision timeframes (`lane_rematerialization.py:134`). `regime_transition_break`'s own
provenance string admits the mismatch: *"its birth registry required H1/H4/D1 and it shipped on
M15, so its horizon is wrong before its target is"* (`:3591-3593`).

---

## 2. SEARCH-HISTORY CENSUS

### 2.1 The sleeve estate's exit corpus is NOT funnel evidence — verified

Sessions **AA, AD, AK, AQ, AU, AV** all run over one population: `AA_ESTATE_TRADES.json.gz`,
22,324 trades over 29 registry sleeves generated by
`active_specs` / `SLEEVE_EXIT_PROFILES` / `GenerationPort`
(`phase6/receipts/aa_estate_generate.py:89`, `:130`, `:143-150`; `phase7/receipts/ad_exit_sweep.py:127`;
`phase8/receipts/ak_supply_gate.py:74-75`; `phase11/receipts/aq_contract_truth.py:90`;
`phase12/receipts/au_exit_contract_wiring.py:78`). **`broader_origin_generators` is imported by no
file under phase6, phase7, phase8, phase11 or phase12.** AD's 1,631 gated exit cells, AK's frontier,
AQ's time-stop repair and AU's contract wiring are **sleeve** work and must not be credited to any
funnel family. `phase20/receipts/r1/R1_FRONTIER_SURFACE_V1.json` (the later bid/ask-corrected
re-run of the whole exit surface) reports `"trades": 22354, "sleeves": 29` — still the sleeve
population.

The one adjacent item worth naming precisely: `phase20/forward/receipts/p3/p3_sweep.py:9`
pre-declares and sweeps a stop-floor `K_GRID = (0.00 … 2.00)` — for **`asia_pdl_fade`, a sleeve**.
It is the estate's only properly pre-declared sweep of a generator-adjacent entry constant, and it
was spent on a sleeve, never on a funnel family.

### 2.2 What HAS been searched on the funnel families

| study | axis varied | scale | class |
|---|---|---|---|
| **FB** (`phase19/SESSION_FB_SOL_FULL_FAMILY_GRID_RESULT.md`) | target ∈ 11 × stop ∈ 9 × orientation ∈ 2, on 26 of 30 strata | **5,148 population-cell evaluations** | outcome |
| **CQ** (`phase18/receipts/cq_path_pool_grid.py`) | same grid, 3 scopes, Jan TRAIN/HOLDOUT | 198 cells | outcome |
| **g3** (`phase20/provenance/G3_REVERSION_AND_EXTREME_DOSSIERS.md`) | stop ladder k ∈ 11 (`a5_sep2.py:30`); stop × target price grid 21 cells over **all 10 families** (`a6_price_grid.py:24`); 7 exit arms × 2 horizons (`a15_final.py:24-29`); naked drift H ∈ 8 (`a10_fwd.py:3`); per-minute drift to 119 min (`a7_drift.py:10`); a 2.83× paired natural experiment | large | outcome |
| **L4 / L2 / B1 / D6 / E2 / X3** (`phase19/receipts/discovery/`) | 240-cell target×stop×maxbars; 16-point stop sweep; 2,640-cell entry-delay × exit × cost × **session window**; horizon ∈ 4; 100-cell family-depth × session; entry-offset k ∈ −15…+60 min | large, pooled | outcome |
| **June program** (`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`) | **generator stop-width scale 1×/2×/3×/4×/5×**; 61-policy exit tournament × 186 segments; pullback entry 0.15/0.25/0.4 R; universe 24 → 46 | large | outcome |
| **p2** (`phase20/forward/p2/`) | target **present vs deleted** (binary, level fixed at the CLI scalar); horizon ladder ∈ 8; quote-side convention ∈ 3; resolution grid ∈ 3; OOS split; **coin-flip side placebo** | 471,269 rows | outcome |
| **pm_geometry** (`postmortem/pm_geometry.py:18-27`) | 7 variants: target {1.0,1.5,3.0}, stop {0.75,1.5}, horizon ×2 | 3 families, **selected set only** (n = 124/29/13), in-sample | outcome |
| **R2** (`phase20/SESSION_R2_GENERATOR_REPAIR.md:191-205`) | POI far-side radius ∈ {None,1.5,3,5,10}, near-side ∈ {off,0.0} | 1.21 M emissions | outcome — both ship OFF, "economically inert" |

### 2.3 What has NEVER been searched — the exhaustive list

1. **Every entry-trigger constant in §1.1. Zero variations, ever.** Every script that touches a
   predicate hard-codes the shipped value in order to *reproduce* it; none parameterises it.
   `phase20/forward/receipts/p3/p3_census.py:257` transcribes
   `close_position(50) >= 0.97 or <= 0.03` verbatim — a census of the constants, not a sweep.
2. **The decision timeframe.** No family has ever been generated or measured on H1/H4/D1. g3 names
   the gap twice and calls it *"the one unpriced thing in this dossier"*
   (`G3_...DOSSIERS.md:334-335`, `:575-577`).
3. **The stop *rule*.** Every sweep rescales the shipped ATR-fraction stop. Structure-based
   placement is listed as unbuilt work in `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md:220-227`, never reached.
4. **Symbol eligibility and session/hour as *generation* parameters.** Applied only as post-hoc
   slicers. No funnel family has an hour or session gate of any kind.
5. **Regime conditioning inside a family.** Every regime test (pm SD1–SD3, the entry-conditioning
   study, `family × session` in the puzzle pool) filters after emission.
6. **The 120-minute lifecycle as a *generation* parameter.** Varied only in re-walks of rows already
   emitted at 120 min; never in generation, never in a frozen prereg.
7. **`moonshot_broader_origin_stop_width_atr_scale` in the outcome-authority lane.** The knob exists
   (`:1263-1279`) and was swept once in June 2026 on a different program; `_config_for`
   (`w21_generate_day_r2.py:63-88`) never sets it, so all five months ran at scale 1.0.

### 2.4 Per-family searched / unsearched matrix

`E` = entry trigger constants · `S` = stop multiple · `Sr` = stop rule · `T` = target multiple ·
`H` = horizon · `TF` = decision timeframe · `Sn` = session/hour at generation · `Sy` = symbol
eligibility · `Rg` = regime conditioning at generation · `D` = direction/orientation

| family | E | S | Sr | T | H | TF | Sn | Sy | Rg | D |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `liquidity_sweep_reclaim` | ✗ | ✔ g3,L2,scale | ✗ | ✔ FB,CQ,g3,pm | ✔ g3,pm,D6 | ✗ | ✗ | ✗ | ✗ | ✔ FB,p2 |
| `structural_distance_extreme` | ✗ | ✔ g3,L2,scale | ✗ | ✔ FB,g3,M2 | ✔ g3,M2 | ✗ | ✗ | ✗ | ✗ | ✔ FB,p2 |
| `displacement_continuation` | ✗ | ✔ g3,scale | ✗ | ✔ FB,g3,pm | ✔ g3,pm | ✗ | ✗ | ✗ | ✗ | ✔ FB,p2 |
| `cross_asset_lead_lag` | ✗ | ✔ g3,scale | ✗ | ✔ FB,g3 | ✔ g3 | ✗ | ✗ | ✗ | ✗ | ✔ FB |
| `session_open_range_break` | ✗ | ✔ g3,pm,scale | ✗ | ✔ FB,g3,pm | ✔ g3,pm | ✗ | ✗ | ✗ | ✗ | ✔ FB,p2 |
| `regime_transition_break` | ✗ | ✔ g3,scale | ✗ | ✔ g3 (FB: **n too small**) | ✔ g3 | ✗ | ✗ | ✗ | ✗ | ✔ p2 |
| `volatility_compression_expansion` | ✗ | ✔ g3,scale | ✗ | ✔ FB,g3 | ✔ g3 | ✗ | ✗ | ✗ | ✗ | ✔ FB,p2 |
| `current_fvg_fill` | ✗ | ✔ FB,CQ | ✗ | ✔ FB,CQ | ✗ (120 fixed) | ✗ | ✗ | ✗ | ✗ | ✔ FB,CQ |
| `current_ob_retest` | ✗ | ✔ FB,CQ | ✗ | ✔ FB,CQ | ✗ | ✗ | ✗ | ✗ | ✗ | ✔ FB,CQ |
| `current_breaker_re_entry` | ✗ | ✔ FB,CQ | ✗ | ✔ FB,CQ | ✗ | ✗ | ✗ | ✗ | ✗ | ✔ FB,CQ |
| `range_extreme_reversion` (off) | ✗ | ✔ g3,L2 | ✗ | ✔ g3 | ✔ g3 | ✗ | ✗ | ✗ | ✗ | ✔ p2 |
| microstructure ×2 (off) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

The two default-off microstructure families have **never had any axis varied and have never emitted
a production candidate.** `range_extreme_reversion` is the family whose founding mine
(`ULTIMATE_ORIGIN_DISCOVERY_MINE_V2`) tested **no stop, no target and no direction contract** — it
measured naked close-to-close drift at H ∈ {4,8,16,32} M15 bars — and the shipped family then added
a 1.0×ATR stop and a `min_rr` target that the mine never evaluated.

---

## 3. SENSITIVITY, MEASURED

**Population.** The five cached months at `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`
(durable copy `/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-puzzle-cache-20260812/`;
builder `outcome_authority/puzzle_receipts/puzzle_build_cache.py`). **632,934 emitted candidates,
535,657 usable, 100 trading days, 10 families.**

**Basis.** Per-candidate economic R: `RESOLVED_NO_FILL` = 0.0 R (the honest denominator for a LIMIT
family — declining to trade is an outcome), censored rows excluded (15.4 %). All intervals are
**day-clustered bootstrap**, B = 4,000, seed 20260811.

**Standing caveat.** All five months were read before this lane existed. Every number in §3 is
**in-sample and post-outcome**. Nothing here is an admission, and nothing here is corrected for the
estate's prior spend on these families.

### 3.1 Baseline: the contract, not the setups, is what is negative

`lane_c_receipts/LANEC_FAMILY_BASELINE.json`, `LANEC_HORIZON_COST_HOUR.json`.

| family | emitted | fill % | E[R]/cand | ci95 | **E[R] gross/fill** | **cost R/fill** | cost ÷ \|gross\| |
|---|---:|---:|---:|---|---:|---:|---:|
| `current_fvg_fill` | 368,325 | 20.0 | −0.0395 | [−0.0454,−0.0335] | **+0.0545** | 0.2521 | 4.6× |
| `current_ob_retest` | 145,721 | 6.0 | −0.0081 | [−0.0119,−0.0045] | **+0.0490** | 0.1837 | 3.7× |
| `current_breaker_re_entry` | 36,920 | 12.9 | −0.0246 | [−0.0352,−0.0148] | **+0.0523** | 0.2438 | 4.7× |
| `liquidity_sweep_reclaim` | 25,021 | 100 | −0.2916 | [−0.3237,−0.2587] | **−0.0028** | 0.2888 | 103× |
| `displacement_continuation` | 22,630 | 100 | −0.1366 | [−0.1672,−0.1059] | **+0.0089** | 0.1454 | 16.4× |
| `structural_distance_extreme` | 13,206 | 100 | −0.5688 | [−0.6117,−0.5255] | **+0.0095** | 0.5783 | 60.6× |
| `cross_asset_lead_lag` | 12,072 | 100 | −0.3240 | [−0.3572,−0.2916] | **+0.0322** | 0.3562 | 11.1× |
| `session_open_range_break` | 4,790 | 100 | −0.0977 | [−0.1432,−0.0528] | **+0.0201** | 0.1178 | 5.9× |
| `volatility_compression_expansion` | 2,959 | 100 | −0.1142 | [−0.1520,−0.0761] | **−0.0234** | 0.0909 | 3.9× |
| `regime_transition_break` | 1,290 | 100 | −0.0640 | [−0.1119,−0.0153] | **+0.0085** | 0.0725 | 8.5× |
| **pooled** | 632,934 | — | **−0.0636** | [−0.0676,−0.0594] | — | — | — |

**Read the gross column first.** Eight of ten families are gross-positive; every one of them is
gross-*tiny*. The mean gross outcome of the whole funnel is a coin flip, and the cost is 2–103× it.
Spread is 40–57 % of that cost; the rest is slippage, commission and swap.

This is a **geometry** statement, not an **idea** statement: R is denominated in the stop, and the
stop is 0.10–0.25 × ATR14 on M15. A cost of ~2–4 bps against a risk unit of a quarter of a 15-minute
ATR is arithmetically hostile before any setup is evaluated. The generator's own knob docstring said
so in June 2026 — *"the measured 0.25×ATR(M15) stops put routine M1 noise and ~0.17 R costs above the
realizable exit edge"* (`:1268-1271`) — and the knob was never used in this lane.

### 3.2 The 120-minute horizon binds hardest on the families with the thinnest evidence

| family | target % | stop % | **time-stop %** | E[R] \| time-stop | E[R] \| resolved |
|---|---:|---:|---:|---:|---:|
| `regime_transition_break` | 1.6 | 11.1 | **87.4** | +0.024 | — |
| `volatility_compression_expansion` | 1.3 | 11.6 | **87.1** | −0.021 | −0.743 |
| `session_open_range_break` | 7.0 | 28.5 | **64.5** | +0.126 | −0.503 |
| `current_ob_retest` | 11.8 | 39.9 | **48.3** | +0.170 | −0.419 |
| `displacement_continuation` | 12.4 | 40.2 | **47.4** | +0.151 | −0.396 |
| `current_breaker_re_entry` | 16.8 | 47.9 | 35.3 | +0.133 | −0.369 |
| `liquidity_sweep_reclaim` | 22.2 | 58.7 | 19.1 | +0.211 | −0.410 |
| `current_fvg_fill` | 23.9 | 57.8 | 18.3 | +0.188 | −0.284 |
| `cross_asset_lead_lag` | 28.3 | 62.7 | 9.0 | +0.161 | −0.372 |
| `structural_distance_extreme` | 31.0 | **68.0** | **1.0** | — | −0.576 |

For `regime_transition_break` and `volatility_compression_expansion` **87 % of fills are a
mark-to-market at 120 minutes** — those two families' published economics describe a contract that
almost never reaches either of its own barriers. At the other end, `structural_distance_extreme`
resolves 99 % of fills inside two hours, 68 % of them at the stop: its 0.25 × ATR stop sits inside
the noise it is trying to fade.

The two rightmost columns are the same fact from the other side: in every family, the trades that
*survive* two hours average positive and the trades that *resolve* average −0.28 to −0.74 R. That is
the signature of a stop placed too close to entry relative to cost, not of a setup with no
information.

### 3.3 Trigger-strength sensitivity — the core measurement

`lane_c_receipts/LANEC_TRIGGER_SENSITIVITY_V1.json`, `LANEC_GROSS_CONTROL.json`.

Top-quintile-minus-bottom-quintile of each family's **own** trigger variable, in three arms:
**NET** (per-candidate), **GROSS** (net + `cost_r`, which removes cost dilution — a wider stop
mechanically shrinks a fixed cost expressed in R), and **FILLED-GROSS** (gross conditional on a
fill, which removes the fill-rate confound — for a LIMIT family a "stronger" trigger often just
means *fewer fills*, and 0.0 R beats a negative mean without any edge being involved).

| family | trigger feature | NET TmB | GROSS TmB | verdict |
|---|---|---|---|---|
| `structural_distance_extreme` | `close_position_in_lookback_range` | −0.062 [−0.19,+0.05] | +0.037 [−0.07,+0.14] | **FLAT** |
| | `dist_to_prior_high20_atr` | +0.094 [−0.02,+0.22] | −0.013 [−0.12,+0.10] | FLAT |
| | `risk_over_atr` | +0.335 [+0.24,+0.43] | +0.037 [−0.05,+0.13] | **COST ARTIFACT** |
| `liquidity_sweep_reclaim` | `sweep_depth_atr` | +0.111 [+0.06,+0.17] | −0.035 [−0.09,+0.02] | **COST ARTIFACT** |
| | `dist_to_prior_high20_atr` | +0.113 [+0.03,+0.19] | −0.009 [−0.09,+0.07] | **COST ARTIFACT** |
| | `risk_over_atr` | +0.257 [+0.19,+0.33] | −0.047 [−0.12,+0.02] | **COST ARTIFACT** |
| `displacement_continuation` | `trigger_bar_range_atr` | +0.057 [−0.00,+0.12] | +0.013 [−0.04,+0.07] | FLAT |
| | `trigger_bar_body_atr` | +0.070 [+0.01,+0.13] | +0.004 [−0.06,+0.06] | **COST ARTIFACT** |
| `cross_asset_lead_lag` | `trigger_bar_range_atr` | +0.183 [+0.10,+0.27] | +0.009 [−0.07,+0.10] | **COST ARTIFACT** |
| `volatility_compression_expansion` | `compression_ratio_prior_bar` | +0.016 [−0.07,+0.10] | +0.015 [−0.06,+0.10] | FLAT |
| | `trigger_bar_range_atr` | −0.040 [−0.12,+0.04] | −0.018 [−0.10,+0.06] | FLAT |
| `session_open_range_break` | `session_open_range_width_atr` | −0.040 [−0.12,+0.05] | **−0.107 [−0.19,−0.02]** | gross-only, **NEGATIVE** |
| | `bars_since_session_open` | −0.018 [−0.11,+0.07] | −0.030 [−0.12,+0.06] | FLAT |
| `regime_transition_break` | `close_position_in_lookback_range` | −0.011 [−0.13,+0.11] | −0.013 [−0.13,+0.11] | FLAT |
| `current_fvg_fill` | `poi_distance_to_zone_atr` | +0.118 [+0.10,+0.13] | −0.017 [−0.03,−0.00] | **COST/FILL ARTIFACT** |
| | `poi_age_hours` | +0.100 [+0.08,+0.12] | −0.019 [−0.04,−0.00] | **COST/FILL ARTIFACT** |
| | `poi_max_mitigation_fraction` | −0.012 [−0.03,+0.00] | −0.015 [−0.03,−0.00] | fills-only, **NEGATIVE** |
| | `poi_touch_count` | +0.009 [−0.00,+0.02] | −0.011 [−0.02,−0.00] | fills-only, **NEGATIVE** |
| `current_ob_retest` | `distance_to_limit_atr` | +0.034 [+0.02,+0.05] | −0.013 [−0.03,+0.00] | **COST/FILL ARTIFACT** |
| `current_breaker_re_entry` | `distance_to_limit_atr` | +0.116 [+0.08,+0.15] | −0.001 [−0.04,+0.03] | **COST/FILL ARTIFACT** |

**Result: of 21 own-trigger tests, zero produce a positive gross gradient whose interval excludes
zero. Nine are cost or fill artefacts — significant on net, dead once cost is added back. Nine are
flat in both arms. Three are significantly NEGATIVE in gross** (wider open ranges, more-mitigated
POIs, more-touched POIs all do *worse*).

Two things follow, and they point in opposite directions:

- **Against the commission's thesis:** a family that is flat in its own trigger variable across the
  entire range it emits is a family whose stated ordering principle carries no information *within
  the population it produces*. On the evidence available, tightening these thresholds is not where
  the repair is.
- **For the commission's thesis:** the arm that is monotone and significant almost everywhere is
  `risk_over_atr` — the **stop width**, a parameter nobody chose — and its entire gradient is cost
  dilution. That is not a mirage; it is a real net-R improvement available from a design choice.
  It just says the lever is the R unit, not the trigger.

**Two important limits on the poi columns.** `poi_distance_to_zone_atr`, `poi_age_hours`,
`poi_max_mitigation_fraction` and `poi_touch_count` are recorded **only for `current_fvg_fill`**;
for `current_ob_retest` and `current_breaker_re_entry` they are `not_applicable`. **Those two
families have no recorded trigger-strength feature at all** — the estate cannot condition on their
trigger strength with the features it captured, and `distance_to_limit_atr` is the only available
proxy. Separately, `poi_max_mitigation_fraction` has a mass point: 164,902 rows share one value, so
the retention grid saturates below 50 %.

### 3.4 Threshold tightening — the only direction the cache can test

`lane_c_receipts/LANEC_TIGHTENING_V1.json`, `LANEC_MAXT_V1.json`.

**What this can and cannot answer.** Retaining the top-k % of a family by its own trigger variable
simulates a *tighter* shipped constant exactly. It cannot simulate a *looser* one (those candidates
were never emitted), a different lookback, a different timeframe, or a different stop rule — those
are different detectors that would have to be generated.

Statistic: mean **gross** R of the retained subset. Max-T over a 7-point retention grid, null
permutes the trigger variable **within trading day**, 4,000 permutations.

| family | feature | best retain | n | gross R | **max-T p** | net R at that cell |
|---|---|---:|---:|---:|---:|---:|
| `displacement_continuation` | `trigger_bar_range_atr` | 2 % | 415 | +0.150 | **0.0105** | **+0.057** |
| `displacement_continuation` | `trigger_bar_body_atr` | 2 % | 415 | +0.145 | **0.0105** | **+0.066** |
| `cross_asset_lead_lag` | `trigger_bar_range_atr` | 5 % | 546 | +0.146 | **0.0238** | −0.105 |
| `current_fvg_fill` | `poi_age_hours` | 5 % | 15,300 | +0.018 | 0.1103 | +0.005 |
| `structural_distance_extreme` | `close_position_in_lookback_range` | 20 % | 2,224 | +0.016 | 0.7532 | −0.697 |
| `liquidity_sweep_reclaim` | `sweep_depth_atr` | 75 % | 17,287 | −0.001 | 0.8438 | −0.270 |

Under BH at α = 0.10 over these six looks, three survive. **But `displacement_continuation`'s two
features are the range and the body of the same bar — one look, not two** — so the honest count is
two families, and the bill excludes everything the estate already spent on these families (FB's
5,148 cells alone). Treat these as **hypotheses worth pre-registering**, not results.

**The three curves that matter, in full:**

`structural_distance_extreme` — **monotonically worse in its own trigger.** Net −0.5688 at 100 %
retention → −0.9139 at 2 %; gross +0.0095 → −0.0711. **Both halves of the calendar agree**
(early −0.534 → −0.816; late −0.618 → −1.042). The more extreme the close's position in its own
50-bar range, the worse the fade performs. This is the clearest single result in the lane: the
family's stated idea — *fade the structural extreme* — is not merely unprofitable at its shipped
parameters, it is **anti-correlated with its own strength measure across the whole range it emits**.
A tighter `pos50` is not the repair; the sign is.

`displacement_continuation` — **monotonically better, and it crosses zero.** Net −0.1366 → +0.0569
and gross +0.0089 → +0.1499 as the trigger bar's range tightens from ≥1.5 × ATR14 (shipped) to the
top 2 %. Sign-stable across halves at every retention point. At the crossing cell the family emits
**415 usable candidates in five months across 24 symbols** — ~83/month — and the net figure straddles
zero ([−0.084, +0.197]). This is the single best-supported case in the estate that a funnel family
was **mis-parameterised rather than edgeless**, and it is also small enough that a design search
would be measuring ~80 trades a month.

`cross_asset_lead_lag` — gross rises +0.032 → +0.146 at 5 % retention (interval excludes zero from
20 % down), but **net never crosses zero** (−0.105 at the best cell): its 0.356 R/fill cost is the
largest in the funnel and swallows the improvement. Its repair is a cost/geometry repair before it
is a trigger repair.

`liquidity_sweep_reclaim` — the postmortem's favourite family and the one p2 found the only positive
family-specific residual for — is **flat-to-worse in its own sweep depth** (gross −0.003 → −0.105 at
5 % retention, max-T p 0.84). Consistent with §4.4 of `THREE_MONTH_POSTMORTEM_V1.md` finding its
native contract already near-optimal: there is nothing left on this axis for this family.

### 3.5 Hour of day — an unfiltered axis with a large in-sample spread

`lane_c_receipts/LANEC_HOUR_V1.json`. No funnel family gates on hour or session (the only session
logic in the module is `session_open_range_break`'s range construction). Argmax over up to 24 hours,
**in-sample, uncorrected**:

| family | hrs | best h | E[R] net | worst h | E[R] net | **gross best − worst (ci95)** |
|---|---:|---:|---:|---:|---:|---|
| `liquidity_sweep_reclaim` | 23 | 11 | −0.115 | 20 | −1.014 | **+0.544 [+0.34,+0.73]** |
| `current_fvg_fill` | 24 | 23 | −0.021 | 20 | −0.713 | **+0.217 [+0.04,+0.38]** |
| `cross_asset_lead_lag` | 22 | 7 | −0.133 | 22 | −0.572 | **+0.211 [+0.00,+0.42]** |
| `structural_distance_extreme` | 22 | 9 | −0.319 | 20 | −0.927 | +0.212 [−0.06,+0.45] |
| `current_ob_retest` | 23 | 5 | +0.004 | 19 | −0.025 | **+0.035 [+0.01,+0.07]** |
| `displacement_continuation` | 21 | 9 | −0.056 | 18 | −0.241 | +0.168 [−0.03,+0.37] |
| `session_open_range_break` | 7 | 0 | −0.018 | 1 | −0.186 | +0.181 [−0.02,+0.38] |
| `current_breaker_re_entry` | 22 | 6 | +0.014 | 19 | −0.100 | +0.116 [−0.00,+0.23] |

The worst hour is **19–22 UTC for six of eight families** — the rollover band, where spreads widen.
So most of this is the cost surface again, and the gross intervals that exclude zero are consistent
with a residual liquidity effect on top. A 24-way argmax with no correction is not evidence; it is
a **pre-registration target**, and it is the cheapest one in this report because it needs no new
generation — the emitted rows already carry the hour.

---

## 4. WHAT A REAL DESIGN SEARCH WOULD COST

### 4.1 The constraint that dominates everything: there is no unread window left

- **2026:** Jan, Feb, Apr, May, Jun, Jul all read. February is used-once VAL after wave 18; the
  Feb/Apr/May/Jun/Jul rows are exactly the population §3 mined.
- **2025:** `V2_2025_WINDOWS_READINESS_V1.md` §0 establishes that `june_2025`, `august_2025` and
  `september_2025` were spent by wave-19 lane p2 on 2026-08-06, and `december_2025` by `d2`/`f1`.
  They are **funnel-virgin but not estate-virgin**, off the same inputs, same clock, same hold.
- **March 2026** is outcome-unread and is reserved by standing instruction for a broad-family
  treatment.

**Therefore: any honest design search must buy its own validation window.** The cheapest source is
forward capture — the forward-shadow lane already deployed (`origin/main` HEAD) is measuring
live-forward funnel candidates, which is the only genuinely virgin evidence the estate can still
produce.

### 4.2 The search, specified

**Stage A — free, no new generation, no new window.** Re-analysis of rows already emitted:
hour/session gates (§3.5), and the fill-conditional POI conditioning for `current_fvg_fill`.
Cost: hours. Value: pre-registration targets only; **must not be read as results**, all five months
are in-sample.

**Stage B — the entry axis, which requires re-generation.** For each family, the grid that has never
been run:

| axis | proposed range | cells |
|---|---|---:|
| primary threshold | shipped ± , 5 points (e.g. `pos50` ∈ {0.90, 0.94, 0.97, 0.99, 0.995}; `bar_range/atr14` ∈ {1.0, 1.25, 1.5, 2.0, 3.0}) | 5 |
| lookback | {20, 50, 100} where the family has one | 3 |
| stop rule | {ATR-fraction (shipped), structure-based, k×ATR with k ∈ {0.5, 1, 2, 3}} | 6 |
| decision timeframe | {M15 (shipped), H1, H4} | 3 |
| horizon | {120 min (shipped), 240, 480, 1440} | 4 |
| hour/session gate | {none (shipped), 4 declared blocks} | 5 |

That is **5 × 3 × 6 × 3 × 4 × 5 = 5,400 cells per family**, and it must be crossed with the
target/stop grid the estate already runs (99 cells) to avoid the exact error this lane is auditing —
judging a new entry at an inherited exit. The full product is ~535,000 cells per family. **That is
not a search anyone should authorise.**

**The honest version is a staged, pre-registered ladder:**

1. **Freeze one axis at a time**, in the order the evidence ranks them:
   **(i) the R unit** (stop rule + multiple — the axis §3.1 shows is worth 2–103× the gross edge),
   **(ii) the decision timeframe** (never tested, and named as the unpriced gap by g3),
   **(iii) the primary entry threshold**, **(iv) hour/session**.
2. **Scope to the families with a signed hypothesis**: `displacement_continuation` (tighten, p 0.0105),
   `cross_asset_lead_lag` (cost repair first), `structural_distance_extreme` (**invert or retire** —
   §3.4's monotonicity is a directional hypothesis, and `PHASE0_INVERSION_TRUTH_V1.md` already
   priced whole-population inversion as a KILL, so this would be a family-scoped re-test, not a
   repeat).
3. **Pre-register the cell before generating**, into `CANDIDATE_FAMILY_V*` at the ratified
   `CANDIDATE_BOOK_V1` standard, α = 0.10, and declare the family size honestly — a 4-axis ladder
   at 5 points each over 3 families is **60 declared looks**, which at BH α = 0.10 needs a rank-1
   bar of p ≤ 0.0017. Nothing in §3 is within an order of magnitude of that.
4. **Validate on captured-forward data only.** At the observed rate the two candidate cells emit
   ~80–110 usable rows/month, so a 3-month forward capture yields n ≈ 250–330 per cell — enough for
   a sign, not enough for a 0.0017 bar. **The multiplicity bill and the sample rate are
   incompatible at the estate's ratified standard**, and that incompatibility is the finding, not a
   reason to lower the bar.

### 4.3 Compute

Generation is the cost. The five-month cache is 632,934 candidates over 100 days × 24 symbols ×
4 timeframes; the lane materialises per day through `w21_generate_day_r2.py`. One re-generation of
one month at one cell is one full lane pass. **A 5-point sweep of a single entry constant over one
month is 5 lane passes**; the ladder in §4.2 at its most disciplined (4 axes × 5 points × 3 families,
one axis at a time, one month) is **60 lane passes plus 60 label/cost passes**. Re-analysis of
already-emitted rows (Stage A, and everything in §3) is minutes — the whole of §3 ran in under an
hour on one machine from the cached pickles.

### 4.4 The recommendation, stated plainly

**Do not authorise a broad entry-parameter search.** Its multiplicity bill cannot be paid at the
sample rate these families produce, and this lane's own measurement says the entry thresholds are
flat where they can be tested. **Do authorise, if anything, the R-unit work** — it is one axis, it
has a measured 2–103× cost-to-edge ratio behind it, the knob already exists
(`moonshot_broader_origin_stop_width_atr_scale`, `:1263`, default 1.0, never used in this lane), and
it is the only axis in this report where the arithmetic is unambiguous. And record
`structural_distance_extreme`'s monotonicity as a standing finding either way.

---

## 5. VERDICT: "no edge" or "never designed"?

**Neither alone. The evidence supports a third statement, and it is more useful than either.**

- **"Never designed" is true of the entry side and is now measured to be the *wrong place to look*.**
  Every entry-trigger constant is un-searched — that part of the commission is correct and is
  established in §2.3. But §3.3 measures the families' sensitivity to those same constants across
  the range they actually emit, and finds them **flat in gross terms in every case, and monotone the
  wrong way in one**. Un-searched is not the same as promising.

- **"No edge" overstates a real result.** The families are not noise: eight of ten are gross-positive.
  They are **swamped**, by a factor of 2 to 103, by a transaction cost expressed in a risk unit that
  is a fraction of a 15-minute ATR. Calling that "no edge" attributes to the setups a defect that
  belongs to the contract.

- **The best-supported description: the funnel families carry a gross edge of order +0.01 to +0.05 R
  and are run inside a geometry that charges 0.09 to 0.58 R to collect it.** The exit side of that
  geometry has been searched thoroughly and cannot close the gap (FB's 5,148 cells yield two
  survivors, both orientation findings, one month, never re-tested out of month). The entry side has
  never been searched, and where this lane can test it, it is flat. **The one axis that is both
  un-searched and arithmetically live is the R unit itself** — the stop rule and multiple that set
  the denominator — and the estate built the knob for it fourteen months ago and never turned it.

One dissenting data point, kept because it is the strongest thing on the other side:
`displacement_continuation` at its top-2 % trigger cell is **net-positive (+0.057 R/candidate,
gross +0.150, max-T p 0.0105, sign-stable across the calendar halves)**. That is one family, 415
candidates in five months, in-sample, uncorrected for the estate's prior spend. It is the only place
in this report where "mis-parameterised, not edgeless" is the better reading of the data — and it is
also small enough that proving it would take longer than the estate has windows for.

---

## 6. WHAT THIS LANE COULD NOT DO

- **The cache stores one outcome number per row, no price path.** No alternative stop, target or
  horizon can be re-walked from it. Every geometry claim here is about the *shipped* contract; the
  geometry sweeps in §2.2 are cited, not reproduced.
- **Only the tightening direction of an entry constant is measurable.** Loosening, changing a
  lookback, and changing the timeframe all require re-generation.
- **`current_ob_retest` and `current_breaker_re_entry` have no recorded trigger-strength feature**
  (`poi_*` are `not_applicable`); `distance_to_limit_atr` is a proxy for the limit's placement, not
  for the setup's quality.
- **No side placebo.** p2 established that the coin-flip control is the one that matters for this
  population, and outcomes in this cache are bound to the realised side, so it cannot be run here.
  The gross and fill-rate controls in §3.3 are weaker instruments in the same spirit.
- **Everything is in-sample.** All five months were read before this lane was commissioned.
