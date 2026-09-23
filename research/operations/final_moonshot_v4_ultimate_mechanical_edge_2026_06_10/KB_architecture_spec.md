# KB ARCHITECTURE SPEC — Conditional, Dynamic, Self-Improving Mechanical Trading System

Route: `final_moonshot_v4_ultimate_mechanical_edge_2026_06_10`
Author: lead architect (KB design pass)
Date: 2026-06-14
Status: design spec, implementable. Grounds every choice in this program's audited evidence and the 6 leaks.

---

## 0. PREAMBLE — design constraints that come from EVIDENCE, not taste

This spec is written against three hard facts already established and audited in this route. They are not negotiable design inputs; they are the boundary conditions.

- **FACT A — entering without setup selectivity has no edge.** The "enter every bar both directions + GBM picks" engine was ~-0.15R *everywhere* (`dead_class_harness.py`, ledger). Conditioning a non-edge does not create an edge. Therefore the architecture's job is NOT "decide direction each bar"; it is "rank and size a small set of *structurally selective* setups per state." State is a **modulator on top of setups**, never a generator of trades on its own.
- **FACT B — the only audited, leak-free, FTMO-safe edge on free MT5 data is the precious-metals vol-gated FVG-retest 2R continuation sleeve** (`gold_sleeve_strategy.py`, `ULTIMATE_GO_LIVE_DOSSIER.md`). It is real but small (+0.22R/trade, 8/12 positive years, ~0.05 unit-R/day) and gold-concentrated. Eight waves + controls (invert null, count-matched random null, leave-one-symbol-out, M1 intrabar delta 0.000R) failed to find any second engine, broadener, or diversifier *in this data class*. Monte-Carlo: ~71% P(pass one FTMO challenge) at 0.5%/unit, 0% daily-breach (`challenge_montecarlo.py`).
- **FACT C — the broad incumbent V4 selector run through the real engine LOSES** (-0.25 to -0.29R/fill, negative every month, native real-engine run). Deploying the edge means running the *narrow rule as a standalone replacement*, not augmenting the broad selector.

**Reconciliation of the owner's "ultimate / broad / high-frequency" goal with the evidence.** The owner's success criteria (absolute return + compounding + breadth + high frequency) cannot all be satisfied *today on free OHLCV* — that is now a proven empirical ceiling, not a research gap. The honest design is therefore a **two-layer system**:

1. **The Conditional Edge Engine (CEE)** — a general, dynamic, self-improving machine that takes a *registry of structurally selective setups*, scores each candidate by **per-state conditional EV**, sizes by confidence, and learns from every closed trade. Today its registry contains exactly ONE proven member (gold sleeve) plus *bench* members held at zero size. The CEE is built to be broad and high-frequency **the instant a new +EV setup or a new data class clears validation** — without re-architecting. This is how "ultimate/broad" is honored: as an *absorptive architecture*, not a fabricated breadth.
2. **The Funding Objective Wrapper (FOW)** — the portfolio/sizing/risk layer that turns whatever the CEE produces into max P(pass FTMO before breach), across N accounts, nothing-killed.

Breadth and frequency are *outcomes the architecture can deliver when real edges exist*, not properties we force onto an empty registry. Forcing breadth onto non-edges is exactly leak #3/#5 territory. The CEE makes breadth cheap to add and safe to reject.

---

## 1. STATE REPRESENTATION

**Goal:** a minimal-but-sufficient vector `S_t` describing "what kind of market/time is this right now," computable from free OHLCV with **zero lookahead** (every feature uses only bars with close-time `<=` the decision bar; the decision bar itself is the just-closed bar, entries fire at its close per `geometry_lib.simulate` which iterates `j>i`).

State is split into **continuous context features** (fed to the conditional-EV model) and **discrete regime keys** (used for cell bucketing, shrinkage backoff, and per-cell reporting). Both come from the same raw measurements; the discrete keys are quantile bins of the continuous features computed on a **trailing expanding window** (never the full sample — see Trap #4).

### 1.1 Volatility block (per symbol)
- `atr14` (from `geometry_lib.atr14`) — the R-unit scale.
- `vol_ratio = atr14 / SMA100(atr14)` — the ONE proven lever (gold gate is `vol_ratio >= 1.2`). Continuous feature AND the gate.
- `vol_pct = trailing-rank of atr14 in expanding window` (0..1) — regime key `vol_state ∈ {low, mid, high}` via trailing 33/66 pct.
- `vol_accel = atr14 / atr14[-5] - 1` — expansion vs contraction.
- `realized_vol_20 = stdev(log returns, 20)` — second vol view, decorrelates intrabar-range from close-to-close.

### 1.2 Trend / structure block (per symbol)
- `htf_trend` (from `wave1_structure_setups_ict.htf_trend`) — discrete `{up, down, flat}`; the setup direction filter.
- `ema_slope_norm = (EMA50 - EMA50[-10]) / atr14` — trend strength in R-units.
- `dist_from_ema200_atr = (close - EMA200) / atr14` — extension/stretch.
- `structural_distance` — distance from the nearest swing high/low in ATR units (this is the feature behind the one certified segment cell `fx/structural_distance_extreme/h12_13`; keep it). Regime key `struct_state ∈ {at_level, mid, extended}`.
- `swing_age` — bars since the last confirmed swing pivot (confirmation lag included; no lookahead).
- `consolidation_flag` — Donchian(20) width / atr14 below trailing-median (range vs trend regime).

### 1.3 Time block (computed from bar timestamp; **NEVER selected in-sample** — see Trap #4)
- `session ∈ {asia, london, ny, overlap, off}` — used only as a *reported stratum and a model feature*, never as a standalone selector.
- `dow ∈ {mon..fri}`, `is_month_end`, `is_pre_known_high_impact_window` (deterministic from calendar of *recurring* sessions only; no event feed = no event feature).
- Time features enter the model as one-hot context. They may NEVER be the sole reason a trade is taken or sized up. Guardrail: a config flag `time_only_signals_forbidden=True` that the validation harness asserts.

### 1.4 Cross-asset / relative-strength block (computed with strict as-of alignment)
- `corr_cluster_id` — static map (metals, fx-majors, jpy, index, energy, crypto). Used by the FOW for correlated-risk-unit sizing (Trap #3 + FTMO).
- `rel_strength_20 = symbol_return_20 - cluster_mean_return_20` — relative strength vs its cluster (as-of, equal-coverage; see Trap #3).
- `dxy_proxy_state` / `risk_on_proxy` — sign of a basket return (e.g. index basket) as a coarse macro regime key, **only** if every member is aligned to the same as-of bar with equal history.

### 1.5 Setup-intrinsic block (per candidate, not per bar)
Attached to each candidate the setup generator emits:
- `setup_id`, `direction`, `gap_size_atr` (FVG width), `retest_depth_atr`, `displacement_atr` (impulse that created the gap), `n_touches`, `time_since_setup`.

### 1.6 The state key (for cell tables)
```
cell_key = (asset_class, setup_id, vol_state, trend_state, struct_state)
```
5 dims. With trailing-quantile binning this yields O(hundreds) of cells across the registry — small enough that each cell can carry an honest shrunk EV estimate, large enough to be conditional. `session`/`dow` are **deliberately excluded from the cell key** and live only as continuous model features + reporting strata, precisely because in-sample session/dow selection was leak #4.

**Lookahead discipline (applies to every feature above):** all rolling stats use `min_periods` and trailing windows; all quantile bins use an **expanding trailing** distribution (recomputed as-of each decision bar, frozen for that bar); no feature may read any bar at index `> i`. This is asserted by a unit test that recomputes `S_t` on truncated history `bars[:i+1]` and checks byte-equality with the streaming value.

---

## 2. THE CONDITIONAL POLICY

### 2.1 Pipeline (per decision bar, per symbol)
```
generate candidates  ->  compute S_t  ->  conditional-EV score per candidate
   ->  rank  ->  gate (EV floor)  ->  hand survivors to FOW for sizing
```
The setup generators are the *only* source of candidates (Fact A). Direction is set by the setup + `htf_trend`, never by the model alone. The model's job is **EV(cell, context)** and **rank**, not "trade y/n from scratch."

### 2.2 The model — chosen representation and WHY

**Chosen: a two-stage conditional-EV estimator = shrunk per-cell empirical EV (Stage A) + a monotone-constrained gradient-boosted residual ranker (Stage B), gated by a per-cell confidence floor.** Justification follows from the overfit evidence in this program (the learned per-candidate model topped out at AUC 0.53; flat linear models couldn't beat 0.528 even with path features — `ULTIMATE_LEARNED_EDGE_LAYER_V4.json`). That history says: **do not ask a flexible model to manufacture signal that isn't there; ask it only to refine an already-honest base rate.**

- **Stage A — shrinkage conditional-EV table (the backbone).**
  For each `cell_key`, store `n`, `mean_R`, `var_R` from CLOSED trades only. The point estimate is James-Stein / empirical-Bayes shrinkage toward the parent:
  ```
  EV_hat(cell) = (n_cell/(n_cell+k)) * mean_R(cell) + (k/(n_cell+k)) * EV_hat(parent)
  ```
  with backoff hierarchy `cell -> (asset_class,setup_id,vol_state) -> (asset_class,setup_id) -> setup_id -> global`. `k` (shrinkage strength, ~ prior-equivalent sample size) is itself tuned by walk-forward, default `k≈30`. This directly answers "small effective sample per cell": a thin cell is pulled to its parent until it earns its own estimate. **Never judge a rule by its average across heterogeneous regimes** (the cardinal principle) is *literally* the shrinkage table — the global average is only the last-resort prior, never the decision statistic.
  - Confidence per cell = a lower confidence bound, e.g. `LCB = EV_hat(cell) - z * sqrt(var_R/n_eff)` with `n_eff = n_cell + k`. Use a bootstrap p05 of cell EV for the gate (matches the verified microstructure gauntlet's `bootstrap p05>0` criterion).
- **Stage B — monotone GBT residual ranker (HistGradientBoosting).**
  Trains on `target = realized_R - EV_hat(cell)` using the *continuous* context features (vol_ratio, ema_slope_norm, dist_from_ema200_atr, structural_distance, rel_strength_20, gap_size_atr, retest_depth_atr, displacement_atr, session/dow one-hots). Output is a small ranking adjustment, **clamped to ±0.3R** so the base rate dominates. Monotonic constraints where domain sign is known (e.g. EV non-decreasing in `vol_ratio` for the proven gate). This is the part that gives *intra-cell* selectivity (which FVG retest in this regime is better) without re-litigating whether the cell has edge.
  - Trained ONLY on closed trades, ONLY on training folds, with embargo (Trap #2/#4). Refit on a schedule, never per-trade (Trap: in-sample snooping).
- **Final score:** `score = EV_hat(cell) + clamp(GBT_residual, ±0.3) - cost(asset_class)`. Costs are the real per-class R from `ULTIMATE_REAL_COST_MAP.json` (fx .16 / jpy .115 / index .064 / metals .046 / energy .037), subtracted explicitly so a candidate is only positive if it clears its *real* cost.

**Why not pure kNN/instance-based over state?** kNN was considered and rejected as the *primary* because (a) it has no honest shrinkage-to-parent backoff for thin regions (it silently averages whatever neighbors exist, recreating the coverage artifact), and (b) it cannot subtract real cost or enforce monotone priors cleanly. It is retained as a **diagnostic / challenger only** (a 3rd opinion in validation), not as the deployed scorer.

**Why not a single flexible GBT on raw outcomes?** That is exactly what scored AUC 0.53 here. A flexible model on a near-zero-signal target overfits folds and collapses out-of-time. The shrinkage table is the regularizer that history says we need; the GBT is demoted to a clamped residual.

### 2.3 Dynamic geometry (stop / target are state functions — the cardinal principle for exits)
Exit-oracle work showed median +0.49–0.72R left on the table vs fixed-2R; exits must be state-dependent (`ULTIMATE_EXIT_DIAGNOSTIC.json`, `ULTIMATE_EXIT_POLICY_SEGMENT_TABLE_V3_UNIV.json`). BUT vol-state sizing/timing/exits were *killed* as robust additions — the headroom exists in the oracle but no naive vol-exit captured it. Resolution:
- **Stop:** structural (just beyond the gap/retest extreme + 0.10*ATR, floor 0.25*ATR) — proven in the gold sleeve. This IS state-dependent (the R-unit scales with ATR and the structure).
- **Target:** per-cell learned target multiple, **chosen by walk-forward only**, from a SMALL grid `{1.5R, 2R, 3R, trail}` — not a free continuous fit. Default 2R (proven). A cell may only adopt a non-default target if it clears the same gauntlet as a new edge (§5). Until then, 2R. This keeps the exit "conditional" but blocks the over-fit that killed the naive vol-exits: the exit family is a *gated registry member*, not a per-trade knob.
- **All fills go through `geometry_lib.simulate` / `simulate_detail`.** Never hand-roll a fill (Trap #1). `simulate_detail` gives the close index, which is the ONLY legal source of "is this trade closed yet" for any path-dependent state (Trap #2).

### 2.4 What "conditional / non-static" concretely means here
| Decision | Static (forbidden) | Conditional (this design) |
|---|---|---|
| Which setup fires | one rule always | per-cell EV gate; a setup is muted in cells where its shrunk LCB ≤ cost |
| Direction | fixed | setup + `htf_trend` per bar |
| Stop | fixed pips | structural, scales with ATR & gap |
| Target | fixed 2R global | per-cell walk-forward target from a gated grid |
| Size | fixed % | confidence-weighted (§3), correlated-unit |
| Gate | global average | per-cell bootstrap-p05 EV floor |

---

## 3. CONFIDENCE-WEIGHTED SIZING (Funding Objective Wrapper)

**Objective is NOT Sharpe/maxDD — it is `P(reach +8% before -5% daily or -10% max)`** across N=2 FTMO accounts, no time limit. This reframing is already proven decisive here (`challenge_montecarlo.py`: the same edge that looked "too small" for perpetual Sharpe has ~71% pass odds at 0.5%/unit with 0% daily-breach). The sizer optimizes pass-probability, not return.

### 3.1 Confidence -> size map (nothing-killed)
For each surviving candidate, size is a continuous function of its confidence, floored small, never zero-by-deletion:
```
conf = sigmoid( a * (LCB_cell - cost) )                      # 0..1, LCB = bootstrap p05 EV of the cell
base_unit% = size_floor + (size_cap - size_floor) * conf     # e.g. 0.05% .. 0.50% per RISK UNIT
```
- **Low-confidence = tiny size, still taken** (the owner's "nothing killed" rule). This also keeps the learning loop fed with data in marginal cells (§4) — a deleted cell never earns more `n` to graduate.
- `size_cap` defaults to the Monte-Carlo-optimal `0.5%/unit` (71% pass, 0% daily-breach). Owner may set conservative `0.25%`.

### 3.2 Correlated-risk-unit aggregation (mandatory — this is what makes FTMO-safe possible)
- All same-decision-day candidates in the **same correlation cluster** (`corr_cluster_id`) collapse into ONE risk unit, split equally (gold/silver crosses are ~the same trade). This bounded the worst correlated day from -8.37R to -1.05R in the gold sleeve and is the difference between FTMO-safe and not.
- Hard **cluster cap** and **portfolio cap**: total open risk across all units ≤ a fraction of the daily-loss budget such that even a full simultaneous stop-out stays under the 5% daily breach with margin. Concretely: `sum(open_unit_risk%) ≤ 0.5 * 5% = 2.5%` worst-case-stop, leaving 2.5% slack for slippage/gaps.

### 3.3 Daily-breach governor (fail-closed)
- Track realized + open intraday R against the 5% daily and 10% max ceilings using a *soft floor well below the hard limit*: stop opening new units at e.g. **-3% intraday** (soft) so the hard -5% is never approached. This is the `challenge_montecarlo.py` "0% daily-breach" property made into a runtime invariant, not a hope.
- Max-DD governor: as equity approaches the -10% max from the high-water start, shrink `size_cap` multiplicatively (de-risk into the wall), never widen.
- All governors are **fail-closed**: any missing/contradictory state -> size 0 for new entries, existing managed by their structural stops.

### 3.4 Two-account policy
Run the SAME engine on both accounts but with **decorrelated entry phase / size tier** (e.g. account A at 0.5%/unit, account B at 0.35%/unit, or staggered so they don't blow up on the identical bad day). Monte-Carlo already estimates ~92% pass ≥1 / ~50% pass both at 0.5% — the staggering lifts pass-≥1 without raising single-account breach risk.

---

## 4. THE LEARNING LOOP

### 4.1 What is stored (one append-only ledger row per CANDIDATE, including REJECTED)
Reuse the existing counterfactual frame pattern (`build_path_dataset` / `relabel_frame_under_segment_exits.py`): one labeled row per candidate at decision time with **post-asof outcome filled later**, including the ones we did NOT take. Schema:
```
asof_ts, symbol, asset_class, setup_id, direction, S_t (full feature vector),
cell_key, EV_hat_at_decision, GBT_resid_at_decision, score, conf, taken(bool), size%,
realized_R (filled at close via geometry_lib.simulate_detail), exit_index, exit_reason
```
Logging rejected candidates with their counterfactual outcome is what lets the system learn whether its *gates* were right, not just its taken trades — and it is leak-safe because the outcome is computed by `simulate` forward of the asof bar.

### 4.2 How conditions are re-scored
- **Stage A table** updates online: each newly *closed* trade increments its cell's `(n, mean, var)`; `EV_hat` and `LCB` recompute. Shrinkage means a single new trade moves a thin cell only slightly (anti-snooping by construction).
- **Stage B GBT** refits on a **fixed schedule** (e.g. weekly) on the embargoed training window, never per-trade. Per-trade refits are forbidden (config-asserted) because that is online in-sample snooping.
- **Cell graduation:** a *bench* cell (size_floor only) is promoted to full `size_cap` eligibility only when it independently clears the §5 gauntlet on its accumulated closed sample (bootstrap p05 > 0, positive in a held-out forward window, broad across symbols in-class, survives 2× cost). Promotion is logged with the evidence snapshot.
- **Cell demotion:** a live cell whose *rolling forward* LCB drops below cost for a sustained window is demoted to bench (size_floor), NOT deleted. Demotion is reversible if it recovers. This is the "stays non-stale" mechanism — regimes change, and a cell that stops working loses size but keeps logging.

### 4.3 How it avoids snooping itself to death
- **Closed-info-only state** for every path-dependent feature (Trap #2). Any streak/skip/regime-transition counter advances only on bars where `simulate_detail.exit_index <= i`.
- **Embargo** between train and the data used to score live: no trade whose holding window overlaps the training window contributes to a live score. Embargo length = max holding bars (`maxbars`).
- **Decision-time freeze:** the score that sizes a trade uses the model as of the last scheduled refit, never a model that has seen the trade's own outcome.
- **Multiple-testing budget:** every cell-promotion test spends from a tracked Benjamini-Hochberg budget (`build_segment_book.py` already does BH(0.10)). The loop cannot promote unlimited cells; the BH threshold tightens as more cells are tested. This is the structural cure for "snooping itself to death."
- **Random/invert nulls re-run on schedule:** the loop periodically re-checks that the live book still beats an invert-direction null and a count-matched random-entry null under the SAME selection (the controls that caught leaks #1 and #5). If the book stops beating its null, alarm + auto-demote.

---

## 5. VALIDATION PROTOCOL (rigorous AND non-destructive — maps confidence, never binary-kills)

A candidate edge (new setup, new cell, new exit family) earns *size eligibility*, not life/death. Failing the gauntlet sends it to **bench (size_floor, keep logging)**, not deletion. Checklist (a cell must pass ALL to graduate to full size):

1. **Tested fills only.** All R from `geometry_lib.simulate`/`simulate_detail`. No hand-rolled fills anywhere in the path (Trap #1). CI asserts `test_geometry_lib.py` passes.
2. **No-lookahead audit.** Recompute the cell's signals/state on truncated history and confirm identical to the streaming values; confirm all path-state uses `exit_index<=i` (Trap #2). Independent re-implementation cross-check (the gold sleeve was confirmed by a *separate* `gold_sleeve_strategy.py`).
3. **Equal-coverage / per-symbol reporting.** Report per-symbol AND leave-one-symbol-out; a pooled mean alone is invalid (Trap #3). A cell that is one symbol carrying the rest is flagged, not certified as broad.
4. **Walk-forward with embargo.** Train -> embargo (≥ maxbars) -> forward test, rolled across the sample. Report train vs forward separately; a cell whose edge lives only in train fails.
5. **Per-regime AND per-year reporting.** Report EV per `vol_state`/`trend_state` and per calendar year (the gold sleeve is honestly 8/12 positive years). A cell positive only in one bull window fails the confound check (Trap #5: forward-only-positive-but-negative-in-sample = bull confound).
6. **Forward holdout never touched in selection.** Any feature that *selects* a cell (session, dow, threshold) must be chosen on train and confirmed on an untouched forward holdout (Trap #4).
7. **Controls: invert null + count-matched random null** under the SAME selection. Must beat both (caught #1 and #5).
8. **Cost stress.** Survive 2× the real per-class cost. (Caught marginal candidates that only "worked" at the optimistic 0.17 proxy.)
9. **Bootstrap p05 > 0** of cell EV (the verified microstructure gauntlet criterion).
10. **Monte-Carlo funding check.** Run the *book* (not the cell in isolation) through `challenge_montecarlo.py`: report P(pass), fail-by-maxDD, daily-breach %, median days. A cell is only deployed at size if it raises (or holds) book P(pass) without raising daily-breach above 0.

Output of validation is a **confidence map per cell** (LCB, p05, per-year vector, pass-prob delta), feeding §3 sizing. Nothing is deleted; everything is *sized by how much the gauntlet trusts it.*

---

## 6. TRAP MAP — the 6 leaks + foreseeable others, each with its architectural guardrail

| # | Leak (how it produced a FALSE result before) | Guardrail in THIS architecture |
|---|---|---|
| 1 | **Short-side sign bug** — adverse excursion sign wrong, shorts never stopped. | ALL fills via unit-tested `geometry_lib.simulate` (explicit long/short branches, known-answer synthetic tests in `test_geometry_lib.py`). No module may hand-compute a fill; CI fails if `simulate` is bypassed. |
| 2 | **Lookahead gate** — skip-after-loss state advanced using still-open overlapping trades' outcomes. | Every path-dependent state (streaks, skips, regime counters, cell `n`) advances ONLY on bars where `simulate_detail.exit_index <= i`. Closed-info-only invariant, asserted by a replay-parity test. |
| 3 | **Cross-sectional coverage artifact** — long-history symbols dominated a pooled average. | Cell key includes `asset_class`; reporting is per-symbol + leave-one-symbol-out; rel-strength/cross-asset features require equal as-of history per cluster member; pooled mean is NEVER a decision statistic (shrinkage backoff, not pooling). |
| 4 | **Session/DOW selected in-sample, reported as edge.** | `session`/`dow` are EXCLUDED from the cell key and from gates; allowed only as continuous model features + reporting strata. Any threshold/feature selection is train-only, confirmed on untouched forward holdout. `time_only_signals_forbidden=True` asserted. |
| 5 | **Breakout = 2025-26 bull confound** (forward-only positive, negative in-sample). | Mandatory per-year reporting; a cell must be positive across multiple regimes/years, not one window. Invert + random nulls under same selection. Cross-backfill that WEAKENS WF is rejected (logged precedent: 2021 cross-backfill off). |
| 6 | **Microstructure book = sign-bug + OOS-selection.** | Combination of #1 (tested fills) + #4 (no OOS selection) + #9 (bootstrap p05) + #2 (closed-info). Microstructure/tick is bench-only until a *different data class* clears the full gauntlet; not on the live path now. |
| 7 (new) | **Online snooping** — refitting per trade so the model sees its own outcomes. | Stage B refits on a fixed schedule on embargoed data only; per-trade refit forbidden (config-asserted). Decision-time model freeze. |
| 8 (new) | **Multiple-testing inflation** — testing many cells until one looks significant. | BH(0.10) budget tracked across ALL promotion tests (`build_segment_book.py` pattern); threshold tightens with test count. Promotions logged with evidence snapshot. |
| 9 (new) | **Cost optimism** — validating at a proxy cost cheaper than reality. | Real per-class cost from `ULTIMATE_REAL_COST_MAP.json` subtracted in the score; 2× cost stress in the gauntlet. |
| 10 (new) | **Regime drift / staleness** — a dead edge keeps trading at full size. | Rolling-forward LCB demotion to bench (reversible); scheduled null re-checks; cells never frozen as "permanently good." |
| 11 (new) | **Objective mismatch** — optimizing Sharpe/maxDD instead of challenge-pass. | Sizer optimizes `challenge_montecarlo` P(pass); daily-breach governor at soft -3%; this is the proven-decisive reframing. |
| 12 (new) | **Forced breadth** — manufacturing diversification that isn't there (Fact A/B). | Registry starts with only proven members at size; bench members sit at size_floor and must earn graduation. The architecture is absorptive, not fabricating. No cell trades at size on a non-validated average. |

---

## 7. BUILD PLAN

Build order is chosen so the **leak-proof spine exists before any edge logic**, and so the one proven edge is live (small, on a challenge account) while the general engine is built around it. Parallelizable work is marked `‖`; everything depends on the spine.

### Phase 0 — Spine (serial, blocking; ~all other work waits on this)
1. **Lock `geometry_lib`** as the single fill authority; ensure `test_geometry_lib.py` green in CI. (DONE in repo — verify only.)
2. **State builder `state.py`** computing §1 `S_t` from OHLCV with the truncated-history no-lookahead unit test. ‖ unit-testable in isolation.
3. **Counterfactual ledger writer** (extend `build_path_dataset` / `relabel_frame_under_segment_exits.py`): one row per candidate incl. rejected, outcome filled via `simulate_detail`.
4. **Validation harness `gauntlet.py`** implementing the §5 checklist + BH budget + null controls + `challenge_montecarlo` hook. This is the gate everything else passes through.

### Phase 1 — Capture the proven edge LIVE (parallel to Phase 2; this is the funding path)
5. **Wire the gold sleeve as a standalone production rule** (default-off elsewhere): H4 FVG-retest, 6 metals only, `vol_ratio>=1.2` gate (walk-forward threshold), structural stop, 2R, correlated-risk-unit sizer + cluster/daily governors (§3). Unit-test sizer + gate (precedent: `test_gold_sleeve.py`, 3 tests).
6. **Disable the broad incumbent V4 selector on the live surface** (Fact C). Config restricts live to the gold-sleeve rule.
7. **Runtime/broker-authority work** (the actual go-live blocker per CLAUDE.md): hard-halt row-level forensic join, V3-vs-live authority gap audit, dual-broker audit, production-return dossier. ‖ can run as a separate subagent track in parallel with edge research.
8. **Deploy small on 2 challenge accounts** at 0.5%/0.35%/unit (§3.4). This is the live forward test.

### Phase 2 — The Conditional Edge Engine (general machine, built around the live edge)
9. **Stage A shrinkage cell table** (`conditional_engine.py` already exists — refactor to the §2.2 backoff hierarchy + LCB/p05). ‖ from #10.
10. **Stage B clamped monotone GBT residual ranker** (HistGradientBoosting; ±0.3R clamp; scheduled refit; embargo). ‖ from #9.
11. **kNN challenger** (diagnostic only) for validation 3rd-opinion. ‖
12. **FOW sizer** generalizing #5's sizer to the full registry (confidence map -> size, correlated units, governors). 
13. **Learning loop** (§4): online table update, scheduled GBT refit, graduation/demotion, scheduled null re-checks, BH budget tracking.

### Phase 3 — Absorption (how breadth/frequency actually arrive)
14. **Bench-member intake:** register candidate setups/cells (other classes, other timeframes) at size_floor; let them log via the counterfactual ledger; promote ONLY through `gauntlet.py`. This is the standing loop that *can* deliver breadth/frequency if/when real edges appear — without re-architecture.
15. **New-data-class readiness:** the same engine ingests order-flow/fundamentals features as additional `S_t` columns + new setup_ids the day the owner authorizes that data (post-payout). The honest broadener lives here, not in more MT5 search.

### Subagent parallelization map
- **Track A (funding, critical path):** Phase 0 spine -> Phase 1 (gold sleeve live + broker authority). Highest priority; owner is going live now.
- **Track B (engine):** Phase 2 CEE — depends only on Phase 0 spine, runs in parallel with Track A.
- **Track C (absorption/research):** Phase 3 bench intake + new mining — depends on Phase 2; lowest urgency. All candidate mining MUST go through `gauntlet.py` (no side-channel "breakthroughs").
- **Track D (broker/runtime):** Phase 1 #7 — independent of edge work entirely; can be a dedicated subagent.

### Human/agent-in-the-loop (not fire-and-forget)
- **Every promotion/demotion writes a one-line ledger entry + evidence snapshot** to `RESEARCH_LOOP_LEDGER.md` (existing pattern). Owner/lead reviews promotions before they go to full `size_cap` on a live account (bench at size_floor is auto-allowed).
- **Daily live reconciliation:** the live counterfactual ledger is diffed against the backtest expectation (the M1-delta / parity-proof discipline). A divergence beyond tolerance pages the operator and de-risks (governor to size_floor) until reviewed.
- **Weekly null re-check report** + per-year/per-regime book health to the owner. Any failed null auto-demotes AND surfaces for human decision.
- **Kill-switch is a governor, not a code change:** the operator can set `size_cap=0` (flatten new entries, manage existing on structural stops) without touching the engine — fail-closed by design.

---

## 8. ONE-PARAGRAPH HONEST SUMMARY FOR THE OWNER

This design gives you the dynamic, conditional, self-improving engine you asked for — a per-state shrinkage-EV core plus a clamped learned ranker, confidence-weighted correlated-unit sizing tuned to *pass the FTMO challenge* (not to look good on Sharpe), a learning loop that updates on every win and loss without snooping itself to death, and a validation gauntlet that maps confidence instead of binary-killing. It is structurally incapable of reproducing the six leaks (tested fills, closed-info-only state, per-symbol+per-year reporting, no in-sample time selection, null controls, real costs). The one honest caveat — already proven, not a guess — is that on free MT5 OHLCV the engine's registry currently contains exactly ONE validated edge (the small gold sleeve, ~71% single-account pass at 0.5%/unit). The architecture is built to *absorb* breadth and frequency the moment a new edge or a new data class clears the gauntlet; it will not *fabricate* them. Ship the gold sleeve now on both challenge accounts via the spine; build the general engine around it; let real new edges earn their size through the gauntlet.
