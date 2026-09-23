# ATR foundation — what the yardstick actually was, and what changes now it is named

**Date** 2026-08-12 · **Receipts** `ops/receipts/ATR_FOUNDATION_V1.json`, `ops/atr_foundation_repair_v1.py`
· **Corpus** `forensics/f1_excursion/F1_TRADE_EXCURSION_CENSUS_V1.parquet` (146,736 filled trades, feb/apr/may/jun/jul 2026)
· **Tests** `tests/research_infra/test_atr_basis_foundation.py` (15, behavioural)

---

## 1. Lead: which timeframe each family's ATR was on

**All ten. M15. Every one of them.** There is no per-family timeframe drift, because there is no
per-family series. The generator builds exactly **one** bar series —
`timeframe="M15"` hardcoded at `src/components/broader_origin_generators.py:448` — and every
candidate of all ten origin families is emitted off the latest closed bar of that one series. The
cross-asset leader series is also M15 (`:1876`), and it correctly emits the **lag** symbol's ATR,
the one its stop is built on (`:1937`).

So the premise that started this — *"four keys, first-present-wins, no timeframe declared… one
volatility yardstick applied to signals whose horizons differ by 20×"* — is **half right for the
wrong reason.** One yardstick, yes. But the horizons do not differ, and the four-key chain is not
where the ambiguity lives.

**The real defect is the estimator, not the clock.** Two materially different ATR-14 definitions are
computed on that same M15 series, and which one a candidate gets is decided by its family:

| basis | definition | families | code |
|---|---|---|---|
| **A** `M15\|high_low_mean_14` | `mean(high − low)` over 14 bars — **gap-blind, not Wilder, not true range** | the 7 single-symbol families | `broader_origin_generators.py:3716-3720`, used at `:1460` |
| **B** `M15\|wilder_true_range_14` | Wilder-smoothed **TRUE** range | `current_fvg_fill`, `current_ob_retest`, `current_breaker_re_entry` | `market_state.py:461`, preferred at `broader_origin_generators.py:2713-2716` |

Basis B is preferred whenever the MSO supplies it and silently falls back to basis A when it does
not — so the basis could switch **within** a family, between candidates, unobservably.

### Proof, from the data rather than the code

`risk_price` (= `abs(entry − stop)`, `f1_walk.py:163`) and `risk_over_atr` (= `risk / atr14`,
`feature_contract.py:229-231`) are computed from the *same* entry/stop pair, so
`atr = risk_price / risk_over_atr` recovers the exact denominator the contract used, per trade.
Comparing families at the **same symbol and same decision minute** — the same closed M15 bar:

- **every same-basis family pair agrees to the bit** (median relative difference exactly `0.0`);
- **no cross-basis pair ever does** (share exactly equal: **0.000 %**, all 18 cross pairs).

A clean bipartite split. Exactly two bases, not ten and not one.

### How far apart they are

| | census-implied (this work) | bar-level (`phase20/receipts/r2/R2_ATR_DEFS_V1.json`) |
|---|---:|---:|
| median B/A | **1.0173** | 1.0234 |
| mean | 1.041 | 1.053 |
| p05 / p95 | 0.838 / 1.327 | 0.833 / 1.364 |
| outside ±10 % | **41.8 %** of decision-cells | 48.3 % of bars |

Two entirely independent routes — backing the denominator out of realised trade geometry, versus
computing both estimators directly on 611,854 bars — land on the same answer. **The divergence was
already measured and is documented in the module itself at `broader_origin_generators.py:2700-2707`.**
What was never done is the consequence: the model row mixes the two, and nothing said which was which.

---

## 2. Which published conclusions change

### The 14.4× spread: **nothing moves, and the reason is structural**

> **Both extremes of that spread are basis-A families sharing one identical ATR value.**

`structural_distance_extreme` (0.358) and `volatility_compression_expansion` (5.146) are both on
basis A. Measured within basis A alone the spread is **14.36×** in risk/ATR and **14.3×** in stop
bp — i.e. the *entire* published spread reproduces inside a single consistent yardstick. Correcting
the basis cannot move it by construction.

**The 14.4× spread is designed geometry, correctly measured.** The families anchor their stops at
structural levels — a 20-bar extreme plus a 0.10–0.25 × ATR buffer — and how far that level sits from
price is what differs, not the volatility unit. The expectation that ATR normalisation *should*
flatten risk/ATR across families is itself wrong: normalisation makes the stop comparable in
volatility units; it does not make different geometries identical, and flattening it would destroy
real information.

### The hold-time table: **the 20× spread is largely censoring, not horizon**

`hold_min` maxes at **119 minutes for every single family** — that is the census walk horizon, not a
family property. The three families whose *median* hold equals it are simply mostly unresolved when
the walk ends: time-stop share **0.874** (`regime_transition_break`), **0.871**
(`volatility_compression_expansion`), **0.645** (`session_open_range_break`). "Median hold 119 min"
should be read as "over half still open at the horizon". Any inference that these families are
slower *by design* is not supported by this corpus.

### The stop-distance filter: **two conclusions change, and the second is the important one**

**(a) The measured value of the filter moves materially once the basis is fixed.** Restating the
basis-B families onto basis A, on the subset where a same-cell basis-A ATR exists:

| family | as shipped (basis B) | restated (basis A) | change |
|---|---:|---:|---:|
| `current_breaker_re_entry` | +$282.5/trade | **+$432.6/trade** | **+$150** |
| `current_fvg_fill` | +$162.1/trade | **+$220.0/trade** | **+$58** |

And **5.28 %** of basis-B rows (1,240 of 23,484) **flip side of the 0.75 threshold** purely from the
estimator choice — 813 in, 427 out. On `current_fvg_fill`, which is 41.5 % of the whole corpus and
whose median risk/ATR is 0.503, i.e. sitting right where a 0.75 cut bites.

**(b) The filter is a COST filter, not an edge filter — and in bp it is neutral-to-harmful.** This
is the conclusion that most needs restating. Reported in both domains, as the standing units rule
requires:

| family | Δ dollars/trade | Δ **bp**/trade |
|---|---:|---:|
| `liquidity_sweep_reclaim` | **+$353.3** | **−1.191** |
| `cross_asset_lead_lag` | **+$309.7** | +0.047 |
| `current_fvg_fill` | +$234.0 | **−0.760** |
| `current_ob_retest` | +$211.8 | +2.833 |
| `current_breaker_re_entry` | +$149.1 | **−0.410** |

**In dollars all five improve; in basis points three of five get worse, including the two biggest
dollar winners.** That is the exact signature the project's own units rule warns about: selecting on
stop distance while measuring in R selects on the denominator of the statistic.

The mechanism is measurable and it is cost:

| risk/ATR | median stop (bp) | cost (R) | cost ($) | cost (bp) | net ($) |
|---|---:|---:|---:|---:|---:|
| (0, 0.25] | 1.81 | 0.426 | **$853** | 0.77 | −$1,792 |
| (0.5, 0.75] | 9.05 | 0.150 | $300 | 1.36 | −$518 |
| (1.0, 1.5] | 12.81 | 0.096 | $193 | 1.23 | −$297 |
| (2.0, ∞) | 29.81 | 0.050 | **$101** | 1.50 | −$217 |

**Cost is roughly a constant ~0.8–1.5 bp of price at every stop width.** Divided by a 1.8 bp stop it
is 0.43 R; divided by a 30 bp stop it is 0.05 R — an **8.5× swing in cost-per-trade from geometry
alone.** The filter works in dollars because it removes trades that were cost-destroyed before the
market did anything. That is real money under fixed-fractional sizing and worth having, but it is
**not** evidence of directional edge, and it should never be quoted as one.

**Every bucket is negative.** The widest-stop bucket still loses **$217/trade**. The filter improves
a losing population; it does not create an edge.

### Portability to the armed H4 book: **the filter is not transferable as written**

`risk_over_atr` is M15-denominated for all ten families. Measured on the 50 M15/H4 series in
`vps-bars-20260727`, **median H4-ATR14 / M15-ATR14 = 4.268** (p05 2.33, p95 6.49). So a
**0.75 M15-ATR cut is a 0.176 H4-ATR cut** on an H4-decided sleeve — roughly a quarter of the
intended severity, i.e. almost no filter at all. Carrying the threshold across without rescaling
would silently apply a far weaker cut than the one that was measured. This is precisely what the
basis label now prevents.

---

## 3. The repair

Scoped to **R2-unbound** files only. The bound allocator
(`moonshot_scheduler_v4_best_trade_allocator.py`) and `config/agent_config.yaml` are **untouched**;
the R2 drift count is **7 before and 7 after** — no new seal break.

| file | change |
|---|---|
| `src/components/poi_execution_lifecycle.py` | `predecision_limit_fillability_from_geometry` gains an optional `atr14_basis` and **echoes it on both return shapes**, including the degraded one. The ATR now travels with its yardstick. Unlabelled stays `None` — never guessed. |
| `src/components/broader_origin_generators.py` | Basis labels that name **timeframe and estimator** (`ATR_BASIS_M15_*`), a `ATR_SOURCE_* → basis` map, and `ATR_COMMON_BASIS`. New `_current_framework_atr_resolution` returns `(atr14, source, common_basis_atr)` — the first two byte-identical to before, so **stop geometry does not move**. All ten families now emit `atr14_basis`, `atr14_common_basis` and `atr14_common_basis_value`. |
| `src/research_infra/wave21_forward_shadow/feature_contract.py` | `resolve_atr_common_basis()` — fail-closed resolution onto one declared denominator. Row gains `risk_over_atr_basis`, **`risk_over_atr_v2`** and `risk_over_atr_v2_basis`. |

**The live feature is not silently re-pointed.** `risk_over_atr` keeps its exact as-shipped value and
meaning; it is a live input to the wave-21 forward-shadow ridge. The repaired quantity ships
**beside** it as `risk_over_atr_v2`, is **absent from `NUMERIC_FEATURES`**, and is therefore
invisible to the current model by construction (pinned by test). What it does add immediately is
`risk_over_atr_basis`, so the frozen feature is no longer *ambiguous* even though its value is
unchanged.

**What would need refitting.** Promoting `risk_over_atr_v2` to a model input requires a full refit of
the ridge (`daily_refit.py`) and a new ridge artifact — `ridge_artifact.py` asserts its feature
tuples match the contract, so it is not a drop-in swap. The shadow's daily prequential refit would
pick it up only after `NUMERIC_FEATURES` is amended, which is a deliberate, separate change.

**Fail-closed, by test.** An unlabelled `atr14` is never accepted as if it were on the common basis:
`risk_over_atr_v2` is `NaN` and the basis reads `unavailable`. That is the property that stops this
regressing silently.

---

## 4. Audit of every ATR-denominated feature

Verdict key: **OK** = single consistent basis, now labelled · **MIXED** = basis varies by family
· **CROSS-TF** = the numerator's timeframe differs from the ATR's · **DEAD** = never resolves.

| feature | producer | denominator basis | verdict |
|---|---|---|---|
| `risk_over_atr` | `feature_contract.py:229` | A for 7 families, **B for 3** | **MIXED** → labelled; `_v2` added |
| `distance_to_limit_atr` | `poi_execution_lifecycle.py:168-170` | whatever the caller passed | **MIXED** → now carries `atr14_basis` |
| `poi_distance_to_zone_atr` | `broader_origin_generators.py:2264` | B (MSO-preferred) | **MIXED** → labelled |
| `poi_distance_to_midpoint_atr` | `:2266` | B (MSO-preferred) | **MIXED** → labelled |
| `unit_risk_atr` | `moonshot_scheduler_v4…:17790` | first-present chain across `fillability`/`metadata`/`source_fields` | **MIXED**, R2-bound — reported, not edited |
| `stop_distance_atr` | `:3833` | A | **OK** |
| `target_distance_atr` | `:3834` | A | **OK** |
| `atr14_over_atr50` / `atr14_atr50_ratio` | `:3832` / `:1494` | A / A | **OK** — a ratio of two same-basis ATRs, self-cancelling |
| `trigger_bar_range_atr`, `trigger_bar_body_atr` | `:3854-3855` | A | **OK** |
| `dist_to_prior_high20_atr`, `dist_to_prior_low20_atr` | `:3848-3852` | A | **OK** |
| `sweep_depth_atr` | `:3868-3870` | A | **OK** |
| `session_open_range_width_atr` | `:3876-3878` | A | **OK** |
| `current_bar_displacement_atr14` | `orchestrator.py:4532` | A | **OK** |
| `leader_move_atr14`, `lag_prior_response_atr14` | `:1940-1941` | A, each on its own symbol's series | **OK** — correct by construction |

### Three findings that are NOT the basis defect and are filed, not fixed

1. **CROSS-TF, real.** `current_ob_retest` (`:2397`) and `current_breaker_re_entry` (`:2475`) declare
   `poi_timeframe: "H1"` — their zones are **H1** — but their stop buffer and every `poi_*_atr`
   distance are scaled by the **M15** ATR. Only the FVG branch (`poi_timeframe: "M15"`) is
   timeframe-consistent. This is a genuine numerator/denominator timeframe mismatch on two live
   families and it is a **geometry** change to fix, so it belongs in front of Borhen, not in this
   commit.
2. **DEAD branches.** At `moonshot_scheduler_v4_best_trade_allocator.py:19364-19371` the four-key
   chain is effectively **one** key: `metadata` is `dict(row)` (`:10599`) and no producer ever writes
   a top-level `atr14`/`atr` — the value lives nested under `source_fields`. So
   `metadata.get("atr14")`, `metadata.get("atr")` and `fillability.get("atr")` are **always `None`**.
   The sibling function at `:17703-17711` consults `source_fields`; **the stop-hazard guard does
   not**, so when the fillability packet is the degraded shape the guard sees `atr14 = None` and
   degrades to `no_block` while the M15 ATR sits in `source_fields` unread. **R2-bound file —
   reported, not edited.**
3. **Genuinely varying timeframe, elsewhere.** `candidate_features_logger.py:580-581, 633-635` uses
   `atr_for_pool = m15_atr or h1_atr` — the timeframe there really does change at runtime depending
   on whether the M15 value is truthy. Logging surface only; no decision authority.

### Confirmed NOT affected

The `ultimate_book` sleeves — including the four armed ones — are **structurally sealed off** from
this. They never write an `atr14`/`atr` dict key, `TradeIntent` (`admission.py:842-872`) has no ATR
field, and the policy adapter (`replay_policy/generation.py:548-549`) whitelists six features that do
not include one. **Nothing in this repair touches armed money**, and no armed sleeve's geometry
moves.

---

## 5. Verification

- **A/B against parent on the affected surface**: 635 passed → 635 passed, **0 regressed**, +4 new
  (`-k "broader_origin or poi or fillability or limit_order or current_framework or origin_generator
  or wave21 or feature_contract"`).
- Wider consumer sweep (`selector`/`orchestrator`/`scheduler_v4`/`allocator`/`candidate`): **1,643
  passed**.
- New behavioural tests: **15 passed** — including the two that matter most, *two families on
  different bases now share one `v2` denominator* and *a threshold that flips as-shipped does not
  flip on the repaired feature*. No test asserts on source text.
- **R2 drift: 7 before, 7 after.** `config/agent_config.yaml` untouched; no activation-token re-mint
  implied.

---

## 6. Standing corrections to the record

1. `risk_over_atr`'s ATR is **M15 for all ten families** — the timeframe was never the defect.
2. There are **two** ATR-14 estimators, not one; they differ by a median 1.7 % and are outside ±10 %
   on ~42–48 % of observations, and **0.000 %** of cross-basis observations are exactly equal.
3. The **14.4× cross-family spread is entirely within one basis** and is designed geometry.
   Correcting the basis moves it by nothing.
4. The hold-time spread is **largely censoring** at the 119-minute walk horizon.
5. The `risk_over_atr ≥ 0.75` filter is a **cost filter**. It improves dollars because cost is a
   near-constant ~1 bp of price and a tight stop cannot pay it; in bp it is neutral-to-negative on
   three of five families. **Every stop-width bucket is still negative.**
6. A 0.75 M15-ATR threshold is a **0.176 H4-ATR** threshold. It is not portable to the armed H4 book
   as written.
