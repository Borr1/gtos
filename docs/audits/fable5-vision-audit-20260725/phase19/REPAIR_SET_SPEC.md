# REPAIR SET SPEC — the composed repair program, ex ante (Phase C governance artifact)

**Session FA continuation (OD-BROAD-FORENSIC-2), Phase C. 2026-08-04. Branch
`phase19/broad-forensic`.** This document is committed **BEFORE any Phase-C repair's first
measured run** — the commission's requirement (`SESSION_FA_CONTINUATION.md` §4 Phase C). It is
the governance artifact every T1 pool screen, T2 lane arm, and T3 leave-one-out will be judged
against: expected effects are stated here first, with direction and magnitude where a
diagnostic receipt measured them, and with an honest "unknown" where none did. The numbers
quoted below are Phase-B pool DIAGNOSTICS (B1 walk, B3 BELIEF-RECAL, B4 open questions, B5
adversarial pass) — attribution previews, not repair runs; no repair code has produced a
measured outcome as of this commit.

**Evidence class, binding on every consumer of this document:** every number any of these
repairs produces on January, February, or the June gap is **DEVELOPMENT-FITTED lane evidence,
billed per the ledger discipline, never confirmatory** — the only confirmatory read in the
program is the pre-registered March one-shot, which Borhen triggers (OD-FA2-1). **Kill, park,
and arm verdicts over the broad family stay Borhen's**; this spec authorizes measurement,
never a decision.

Binding inputs, in authority order:

1. `phase19/receipts/forensic/B5_ADVERSARIAL_VERDICTS.md` + `b5_verdicts.json` — the
   adversarial pass whose "Phase C consequences" section is BINDING and reordered this
   program (C3 REFUTED both lenses).
2. `phase19/SESSION_FA_CONTINUATION.md` §4 Phase C (repair classes + pattern requirements)
   and Phase D (the T1/T2/T3 rules and the arm table).
3. `phase19/FULL_FLOW_SPEC.md` — the link table these repairs exist to turn FLAWLESS.
4. Mechanism receipts: `phase19/receipts/forensic/PHASE1_OPEN_QUESTIONS.md` (B4),
   `BELIEF_RECAL.md` (B3), `walk/WALK_2D_ANNEX.md` (B1), `a2_verify/` (A2, incl.
   `FD_VERIFY.md`/`FE_VERIFY.md`/`FF_VERIFY.md`, `RECONCILE_A_Q.md`,
   `LOSS_CLASS_RULE_RATIFICATION.md`).
5. The implementation pattern of record:
   `src/research_infra/train_engine/repairs.py` (fa2-integration tree) — registry entry +
   **paired INERT CONTROL** + `INCOMPATIBLE_REPAIRS` rows, per its own module contract
   ("a repair with no control cannot be attributed", `repairs.py:1116-1117`).

---

## 0. What B5 changed (before → after, per repair class)

The B5 adversarial pass (14 refuters, 7 claims × 2 lenses; 1 claim REFUTED, 5 QUALIFIED,
1 clean) is the reason this spec does not match the commission's original Phase-C wording
line for line. Its consequences section is in force:

| class | before B5 (commission wording, 2026-08-03) | after B5 (in force here) |
|---|---|---|
| **R-COST-TRUTH** | one repair class among five: replace three placeholder spreads (BTCUSD 0.0001, UKOIL/USOIL constants) + February's `cost_missing` 0.12 defaults | **FIRST and load-bearing.** The placeholder class is **20 of 24 symbols** (17 per-row config constants via the `broker_profile_symbol_spec_spread` fallback, `v4t:58806-58816`, + 3 floor constants, `admission.py:73-84`), ~7× wider than filed; SPX500's constant is 16.7× tick truth, NAS100 28.6×. Adds part (b): **cross-window cost-ruler harmonization** (Feb `cost_r` deviates from its component sum on 73.5% of rows) and part (c): slippage stays flat 0.02, disclosed. |
| **R-BELIEF** | "wire `context[\"cost_r\"]` so thesis EV is net-of-cost" (a one-key fix) | **re-scoped: the naive wire DOUBLE-CHARGES.** The replay funnel already charges cost once downstream (`expected_net_r = ev − cost_r` on 8,448/8,448 at `v4t:67450`; router floors `:16883-16886`; allocator anti-double-charge). The repair is a **single-charge-point decision** (live-style inside the debate XOR replay-style at the consumers) + **simultaneous downstream neutralizations**, with `candidate_direction` in the same parity bundle. Landed naively it re-prices 57.8%/78.1% of the funnel by a double charge. |
| **R-SCHEMA** | Feb emitter drift + join key + softened-reject semantics | unchanged in intent; **gains items from the later receipts**: WALK-F1 (B1), exit-vocabulary two-layer naming (B1/B4-Q3), `close_mark_clamped` (B4-Q3), `expectancy_r` dedup (B4-Q1), the FD memo-key defect (A2/`FD_VERIFY.md`), plus B5's standing documentation corrections (loss-class precedence wording; `CALIBRATION.md` "measured means" → config constants; C5's two retired evidence legs). |
| **R-GEOMETRY** | "this is where the cost gate's winner-kill gets addressed from one side" — sized on the 73.9/82.2% untradeable headline and the −19.95/−13.97 R exit cells | **loses exclusivity; re-sized on the truthed residual.** The flagship winner-kill exhibits are spread-INPUT fiction (C3 REFUTED); the genuine geometry-killed core is ~41.6% Jan / 31.8% Feb at broker-true p50. Exit-side yield is **bounded by the driftless-barrier arithmetic**: loser-MFE survival matches the zero-edge prediction at the 0.25R floor (0.656/0.697 vs 0.700) and TP-at-floor recovers only **+3.41/+2.83 R/month**; the yield case rests on **FB-grid-class CONTRACT changes** (entry/stop/target families), not exit tweaks to the current book. |
| **R-CAPS** | ""the gate was right on average" is where the analysis starts, not where it stops" | **the premise is RETIRED as evidence** (C2-B): 77.3% of the refused set's −22,923.5 R is the gate's own cost estimate fed back as outcome; refused vs kept price-normalized market outcomes are near-identical (−0.0238% vs −0.0182%); an arbitrarily wrong cost model prints the same table. Cap re-derivation is grounded **ONLY in externally validated cost inputs**, is **joint with R-GEOMETRY** (shared denominator), and its reachable February winner pool is the cost-attributed **74.1% (5,554)**, not 84.3%. |

Two further B5 rulings bind the measurement language downstream of every repair: **C7** — the
120-minute wall is SYMMETRIC censoring (wall-affected population 25/58 Feb; the −1.28 R MTM
figure is 84% sunk cost on a gross-flat cohort and survives any horizon); March MDE language
says "censoring", never "suppressed edge". **C5** — never again cite the −0.076/−0.006
rank↔outcome Spearman (the S0 neutral draw's designed null) or the 67th-percentile figure
(gate-conditioning); the selection conclusion rests on the degenerate hard pools + the
eligible-set orthogonality leg, and it is **conditional on the current funnel**: R-GEOMETRY/
R-CAPS widening re-opens selection instrumentation as a companion item (see §5/§6).

---

## 1. The composition substrate and the pattern contract

**Substrate.** Every repair in this program composes **on top of the CJ recipe** — the exact
cut+repair set of the sealed baseline arms: the six outcome-inert cuts named in the CJ/CP arm
receipts (`ledger_scalar_projection`, `missed_pool_projection`, + 4 memo/gc cuts;
`FULL_FLOW_SPEC.md` L0, receipt-verified) plus the two landed repairs
**`commission_broker_true_gated` + `swap_horizon_true`** (`repairs.py`; commission live on
8,452/8,452 walk rows, mean 0.0736 R). The recipe is pinned by the fence adjudication
(`FENCE_LANE_ADJUDICATION.md`, bounded digest `32e004ee`), not re-typed here. Baselines are
the **sealed 57/58-trade receipts** (CJ re-clocked January S0R0; CP virgin February S0R0) —
never re-run.

**Pattern contract (from `repairs.py`, binding on every implementation agent):**

1. a registry entry with a stable id, registered via `register_repairs()`;
2. a **paired INERT CONTROL** — same wrapper, same symbol, same intermediate computation,
   neutral value applied — added to `REPAIR_PAIRS`; a repair with no control cannot be
   attributed;
3. `INCOMPATIBLE_REPAIRS` rows for every composition that is wrong rather than unusual,
   refused by name with the reason (§9);
4. this ex-ante spec, committed before the repair's first measured run, carrying the defect
   classification {bug | miscalibration | wrong-geometry | overkill | unjustified-gate |
   missing-condition} and the expected effect.

**T2 arm map (Phase D, restated):**

| arm | contents | expected headline |
|---|---|---|
| (i) | CJ recipe + **R-COST-TRUTH** (`spread_input_truth`; + `cost_ruler_harmonize` on February) | the cheaper-path hypothesis: Feb executed book was gross-positive +0.204 R — is the book positive at honest costs alone? |
| (ii) | (i) + **R-BELIEF** bundle + **R-SCHEMA** set | do the defect fixes move the book without any contract change? Expected: **fewer trades** (stand-down), R-SCHEMA exactly 0 |
| (iii) | (ii) + **R-GEOMETRY** cells + **R-CAPS** cells (declared from T1 on truthed costs) | the repair set's headline |
| (iv) | CJ recipe + all paired **INERT CONTROLS** | plumbing is inert; any (iv)−baseline delta is a bug |
| (v) | (iii) + **admitted candidates** (inverted breaker per A1's corrected-null ADMIT; OB-retest per O1 as-written, if graduated) | the system with its edge in. **Candidates enter ONLY here** — openly declared, billed, never smuggled into a repair delta |

Arm discipline: 2-day smoke before every new arm config; strictly serial (H3), 8 GiB
headroom floor; every evidence arm passes `--keep-outputs` (B1 operating rule). T3
leave-one-out (cap ≤ 6 arms) fires only where |ΔT1| > 0.5 R/window, admission-set change
> 5%, or T1/T2 signs disagree; **per-repair deltas do not sum** (path dependence via the
adaptive memory guard, `v4t:34895-34926`) — every table that prints them says so. February
sidecar: built only if exit/geometry repairs survive Jan T1; decision recorded either way.

---

## 2. R-COST-TRUTH (first and load-bearing — B5 ordering)

### 2.1 `spread_input_truth` (+ paired `spread_input_inert_control`)

- **Defect classification: `bug`.** The replay's pretrade spread numerator is a per-row
  CONSTANT for 17/24 symbols in both monthly pools — the quote-synthesis fallback
  `broker_profile_symbol_spec_spread` (`v4t:58806-58816`), a static config value used
  whenever the sealed replay has no tick source — plus 3 floor-table constants
  (`admission.py:73-84`: BTCUSD 0.0001, UKOIL 0.0258, USOIL 0.0270). Only 4 symbols (18% of
  rows: EURUSD, USDJPY, XAUUSD, XAGUSD) carry a measured spread. SPX500's constant (10.0) is
  16.7× the broker-measured anchor (0.6, and 10× the worst tick ever captured); NAS100's
  (50.0) is 28.6× (1.75). **Receipt:** `B5_ADVERSARIAL_VERDICTS.md` §C3 (REFUTED, both
  lenses); `b5_verdicts.json` C3-A/C3-B; breaks named at
  `calibration/CALIBRATION.md:113-119` and `COST_BELIEF.json:121`.
- **Repair.** Intercept the spec-constant and floor branches of the quote synthesis and
  substitute **SPREAD_MODEL_V1 hour-aware broker-true spreads**
  (`research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json`, built from the 263
  M-row tick corpus; broker wall-clock = New York + 7 h with the measured US-DST calendar via
  `src/utils/broker_clock.py`). The real-tick branch is untouched. **Era label disclosed on
  every artifact: "Jun–Jul 2026 anchors applied to Jan/Feb 2026"** — within-era per B5
  (the constants exceed the observed 5.5-week MAXIMUM by 10×/8.5×, so no spread-regime shift
  rescues them). Slippage stays flat 0.02, disclosed, unless measured (part c).
- **Inert control.** `spread_input_inert_control`: same interception, computes the
  SPREAD_MODEL_V1 truth value and the same intermediates, then applies the ORIGINAL constant.
  Outcome identity under the control attributes every live-repair difference to the number,
  not the wrapping.
- **Ex-ante expected effect (direction + magnitude, pool-diagnostic previews):**
  - pool mean `spread_r` **0.564 → ~0.157** (Jan; the published mean was 3.6× inflated);
  - untradeable share **73.9% → ~61% (Jan), 82.2% → ~60% (Feb)** at mean-truth (~72–73% at
    worst-hour truth) — ~4,887 Jan / 5,361 Feb rows un-killed (~25% of the killed pool);
    SPX500 48–54% of its kills un-killed, NAS100 ~74%;
  - a **genuine geometry-killed residual REMAINS**: ~41.6% Jan / 31.8% Feb of the pool still
    spread-killed at broker-true p50 (SPX500 ~52%, NAS100 ~26–28%) — this repair does not
    exhaust the cost story, it truths it;
  - **book-level executed delta: UNKNOWN by construction.** Un-killed rows enter a pool whose
    cheapest band is still negative on average (C1 mean net −0.178 R/row, BELIEF-RECAL §3),
    so MORE trades is expected, sign of the book is the arm-(i) question, not an expectation.
    Both directions are decision-grade; the arm reports which way it lands.
- **Composition.** Active in arms (i)–(iii) and (v); its control in arm (iv). Composes with
  the CJ recipe untouched (commission and swap repairs price different components). Every
  downstream number consuming `cost_r` (the 94.1% refused-loss share, cost-band gradients,
  EV-after-cost kills, COST_BAND_CROSS) inherits the truthed numerators and is re-derived,
  never spliced.
- **T1 preview** (January CQ sidecar, 3.23 M ordered observations): re-price every row's
  `spread_r`/`cost_r` at hour-aware truth; report kill-table and band migrations. **Label:
  "no selection feedback"** — this repair moves admission (the cost gate's refusal set
  changes), so the executed set changes in ways the sidecar cannot see; T2 arm (i) is the
  measurement.

### 2.2 `cost_ruler_harmonize`

- **Defect classification: `bug`** (inter-window measurement-ruler inconsistency). February's
  `cost_r` deviates from its own component sum on **17,819/24,239 rows (73.5%)**, including
  flat **0.12 overrides on GER40 (1,635 rows; Jan measured mean 0.323), UKOIL_cash (1,203),
  USOIL_cash (717)** that are component-blind in both directions and mechanically evict those
  symbols from every February C1 cell. January is component-sum exact on 27,658/27,658.
  **Receipt:** `b5_verdicts.json` C4-A (qualification + evidence);
  `B5_ADVERSARIAL_VERDICTS.md` consequences item 1(b).
- **Repair.** One cost ruler across windows: `cost_r` := component sum
  (spread + slippage + commission + swap) on every row, with the flat-0.12 override class
  removed and its rows re-priced from components (post-`spread_input_truth` components where
  composed). **No cross-month cell comparison is trusted until harmonized.**
- **Inert control / no-op proof.** Paired `cost_ruler_inert_control` recomputes the component
  sum and writes back the original value. Additionally the repair itself must be a proven
  **no-op on January** (already component-sum exact) — a nonzero January delta is a bug.
- **Ex-ante expected effect:** GER40 February costs UP (0.12 → measured-analog ~0.28–0.32);
  UKOIL DOWN (components 0.049 → cost was 0.12); evicted symbols re-enter Feb C1 cells.
  Conclusion-level preview already measured: re-pricing February on January's ruler leaves
  the BELIEF-RECAL transfer negative (**−22.64 R over 299 rows, sign agreement still 1/4**) —
  harmonization restores comparability; it does not conjure a sub-book.
- **Composition.** Arms (i)–(iii), (v) on February windows (and any cross-window table);
  no-op on January by construction. Ordering with 2.1: `spread_input_truth` acts at quote
  synthesis, `cost_ruler_harmonize` at cost composition — they compose with a single charge
  point preserved.
- **T1 preview:** Feb pool re-priced under one ruler; cell-population and eviction-reversal
  census. **Label: "no selection feedback"** where the re-priced `cost_r` crosses a cap.

---

## 3. R-BELIEF (the honesty bundle — re-scoped by B5/C6-B)

**Registry note.** R-BELIEF implementation launches AFTER R-COST-TRUTH commits (repairs.py
ownership; `RESUME_STATE.json` phase_c). The ids below are the spec's proposed names; the
implementation agent binds final ids at freeze — the classifications, expected effects, and
atomicity rules attach to the content regardless of final naming.

**Bundle-level expectation, stated first and honestly (BELIEF-RECAL §8, binding):** honest
beliefs make this family **STAND DOWN — fewer trades, not more R**. Of 160 declared cells,
0/108 BH-marked at α = 0.10; the 4 nominal January positives transfer to February at
**−19.13 R**; what transfers cross-month is the cost gradient and a loss-severity ordering
(within-band partial r 0.513) — nothing positive. The value of R-BELIEF is **truthful refusal
and truthful pricing of any future family**, not recovered edge from this pool. Any claim
that a belief repair alone produced a positive broad-V4 book is a red flag against the
receipts. Expected T2-(ii) direction: trade count DOWN vs arm (i); book delta sign unknown,
expected small and refusal-driven.

### 3.1 `belief_cost_single_charge` (the parity bundle — ATOMIC)

- **Defect classification: `bug`** (replay/live divergence). The replay's debate context
  omits top-level `cost_r` and `candidate_direction` (`v4t:58197-58213`) while the LIVE
  runtime builder passes both (`probability_debate_v4.py:934`, `:1094-1096`) — replay and
  live run different belief systems; the debate's direct cost term is zero on 8,448/8,448
  fence rows (stamped `probability_context_omits_cost_r_so_debate_cost_r_is_zero`).
  **Receipt:** `PHASE1_OPEN_QUESTIONS.md` Q1 + cross-cutting item 1; `b5_verdicts.json`
  C6-A (NOT_REFUTED) and C6-B (the re-scope).
- **Repair (a cost-accounting DECISION plus a multi-site change, landed as ONE id):**
  1. choose the single charge point — live-style inside the debate **XOR** replay-style at
     the consumers;
  2. if `cost_r` enters the debate context, **simultaneously neutralize the downstream
     charges** — `expected_net_r = ev − cost_r` at `v4t:67450`, the router-floor semantics at
     `:16883-16886` (its 0.55/0.85 floors were calibrated against a single-charged quantity),
     and the allocator's `score_cost_total` for `value_source "decision_time_ev_r"`;
  3. pass `candidate_direction` in the same parity change (the +0.08 prior boost);
  4. re-baseline the p-gates (0.58/0.70/0.85) after the p-channel moves (cost_penalty·0.7
     shifts p by ~−0.43 logit at median cost).
  **The context-wire-only form is REFUSED as a registrable id** (§9): B5 measured that landed
  alone it double-charges — `expected_net_r ≤ 0` 42.8% → 57.8%, router-floor exclusion
  61.3% → 78.1%.
- **Inert control.** Wire the key with value 0.0 (and `candidate_direction` absent-semantics
  preserved) + neutralizations installed in pass-through mode: same call graph, same
  intermediates, zero repriced quantity.
- **Ex-ante expected effect:** the debate's own EV veto (`EV_below_trade_threshold`,
  currently unable to fire — EV floor +0.442, 0/8,448 ≤ 0) becomes live and **would fire on
  ~42.8% of rows** at the single charge point; probability becomes cost-informed. Direction:
  fewer admissions; magnitude at book level unknown (no selection feedback at T1).
- **T1 preview:** recompute debate p/EV per pool row under the chosen charge point; census of
  veto-crossings and p-gate migrations. **Label: "no selection feedback."**

### 3.2 `belief_hash_term_removal`

- **Defect classification: `bug`.** Probability includes `family_hash*0.04` —
  `int(sha256(origin_family)[:8],16)/0xFFFFFFFF` — content-free by construction
  (`v4t:53681-53694`), plus its `family_hash_signal` export and the
  `candidate_generation_rank_key` tiebreak (`:56777-56791`). Measured live through the real
  path: family name alone moves thesis p by 0.00446 and EV by 0.0114 R.
  **Receipt:** `PHASE1_OPEN_QUESTIONS.md` Q1 (mechanism + live probe).
- **Repair:** delete the term (and export/tiebreak); replace the tiebreak with a declared
  content-free deterministic key that does not masquerade as signal.
- **Inert control:** compute the hash term, multiply by 0.0.
- **Ex-ante expected effect:** ~0.45 pp probability noise and ~1.1 cR EV noise removed per
  family name; near-zero book delta expected — this is the smallest defect on the path and
  is repaired for truthfulness, not yield.

### 3.3 `belief_confidence_constant_retire`

- **Defect classification: `miscalibration`.** `candidate_confidence` ≡ 0.55 on 100% of rows
  (`REPLAY_MISSING_CONFIDENCE_DEFAULT`, `ultimate_candidate_package.py:72`, mirrored
  `v4t:26625`) yet feeds the scheduler score at weight ×0.20 — a constant wearing a weight.
  **Receipt:** `PHASE1_OPEN_QUESTIONS.md` Q1 step 4; `FULL_FLOW_SPEC.md` L3b/L5.
- **Repair:** remove the constant from the score; if a confidence slot must exist, an n-based
  shrinkage weight (how much the cell's p̂ is data vs prior) per BELIEF-RECAL §8.3.
- **Inert control:** keep the term, weight 0.0 — must be outcome-identical to removal.
- **Ex-ante expected effect:** ZERO on selection (a constant × weight is rank-inert);
  nonzero delta in T2 = bug. Repaired so the score stops lying about what it consumes.

### 3.4 `belief_ev_walked_contract`

- **Defect classification: `miscalibration`.** EV is priced at a 1.5R symmetric contract
  (`rr` defaults 1.5, proven uniform by the zero-cost identity residual d ∈ [0.027, 0.064]
  on 8,448/8,448), then the policy rewrite attaches the 2.0R-capped giveback AFTER belief
  attachment (`v4t:67426-67450` vs `:67680-67712`; raw_target_r = 2.0 on 26,427/27,658
  rows) — the stamped payoff describes almost no cell (measured W̄ 0.27–2.29, |L̄| 0.30–1.00
  across eligible cells). The jury construction (4 of 5 sources FOLLOW the candidate;
  opposition capped at 0.35·w_cost; shrinkage-to-0.50 with weight ≤ 0.98) makes the layer
  structurally unable to express a loser: stamped p̄ 0.766 vs realized 0.347 gross / 0.279
  net; Brier skill −1.147/−0.965. The "[0.58, 0.97] clamp" is REFUTED — the envelope is
  emergent, so **a recalibration map alone cannot fix this; the source construction or the
  calibration map must change** (B4 Q1 verdict). L3d's ordering defect (belief attached
  before contract known) folds in here.
  **Receipt:** `PHASE1_OPEN_QUESTIONS.md` Q1; `BELIEF_RECAL.md` §1.2/§4/§8;
  `FULL_FLOW_SPEC.md` L3b/L3d.
- **Repair:** price EV at the WALKED contract from measured magnitudes —
  EV(cell) = p̂·W̄ − (1−p̂)·|L̄| − c̄ with p̂ a shrunk base rate at the declared
  family × cost-band × session granularity (n ≥ 30, Jeffreys/beta shrinkage); publish
  p\* = (|L̄|+c̄)/(W̄+|L̄|) beside it; **EV must be allowed to go negative** (under these
  formulas essentially every cell of this family prices negative — that is the correct
  output); attach belief AFTER the contract rewrite or price at the rewritten contract.
- **Inert control:** compute honest p̂/EV alongside, stamp them as observability fields, apply
  the original values.
- **Ex-ante expected effect:** stand-down (bundle headline above). Honest p̂ spans ~0.42–0.58
  in the BEST cells; the engine must be able to say 0.2.
- **T1 preview:** BELIEF-RECAL **is** the preview (already committed, declared-before-compute,
  160 cells). **Label: "no selection feedback"** — honest beliefs move router floors, the EV
  veto, and the scheduler score.

### 3.5 `belief_fill_probability_deweight` (P1-blocked)

- **Defect classification: `missing-condition`.** `execution_fill_probability` = 0.92 for
  every marketable limit — one constant for every symbol and session
  (`poi_execution_lifecycle.py:176-178`, `0.92·0.70 + 0.92·0.30`); the function receives no
  symbol, session, spread, or tick input. 3 of 4 executed walk trades ride exactly 0.92 (the
  4th the 0.95 distance-branch ceiling): 100% of executed trades carried a modeled template
  while the gates comparing it to 0.8/0.85/0.5 believed they were measuring something. The
  separate pool heuristic `fill_probability` pins 19.2% of rows at its own 0.95 ceiling.
  **Receipt:** `PHASE1_OPEN_QUESTIONS.md` Q2.
- **Repair:** honest fill probability requires **P1 (fill truth from tick captures)** with
  HP's M1-acceptance rule — SCHEDULED-ON-NEED per the WAVE20 supersession register; it has
  NOT run. Until it lands: **de-weight or drop the term from the score** and treat every
  consumer decision (full-risk tier 0.8, fallback envelope 0.85, stop-hazard 0.5) as
  unmeasured. FD's authority stamps (`decision_semantics.py:1429-1446`) already mark
  exact-0.92 rows non-authoritative — extend that pattern to the MISSED projection
  (R-SCHEMA S6) and never merge the two fill fields under one name.
- **Ex-ante expected effect:** score de-weighting expected near-rank-inert (the term is a
  constant on marketable rows today); honest magnitude UNKNOWN until P1. Stated plainly:
  this item cannot be truthed inside this program's data; it is bounded and labeled instead.

---

## 4. R-SCHEMA (measurement integrity — expected economic effect: ZERO)

**Class-level acceptance rule:** every R-SCHEMA item is observability, naming, projection, or
cache-key work. **Expected outcome delta in any T2 arm: exactly zero.** The set behaves like
its own inert control; any nonzero economic delta attributable to an R-SCHEMA item is a bug
by definition (same standard the cuts live under). Implementation scope of the current agent:
`cuts.py`/`decision_semantics.py` only (S1–S5); S6–S8 are projection/documentation standards
riding the same class.

| id | defect class | defect (receipt) | repair |
|---|---|---|---|
| **S1 `walk_f1_condition_feature_reroute`** | `bug` | WALK-F1: `condition_feature_propagation`'s features land on TRADE (4/4) and ORDER (8/8) rows, **0 of 8,448 MISSED rows** — the missed-row assembly never consumes the wrapped helper's return (`walk/WALK_2D_ANNEX.md` §Instrumentation). Per-candidate market context exists for executed rows only — the pool the instrument NAMES is the one it misses. | route the projector into the missed writer (or stamp at `project_missed_pool_row`); status fields fail-open |
| **S2 `exit_vocabulary_companion_fields`** | `bug` (naming) | two exit vocabulary layers under interchangeable names: contract-walk terminal (`path_final_r`, `v4t:60302-60359`) vs selected-policy replay overwrite (`:62446`) — walk trade 4 closed `giveback_close` while `terminal_outcome = stop_reached_before_target`; both true, different layers (`WALK_2D_ANNEX.md` trade 4; `PHASE1_OPEN_QUESTIONS.md` Q3) | companion fields naming the layer on every row; any analyzer counting "stops" must state which layer it counts |
| **S3 `close_mark_clamped_stamp`** | `missing-condition` | the `:60351` clamp can land a time-stop/expiry mark exactly on −1.0 or target while keeping its time-stop reason — 0 incidence measured on the fence arm, structurally open on every future window (`PHASE1_OPEN_QUESTIONS.md` Q3 verdict + implication 3) | `close_mark_clamped: bool` derived at projection; populations separable by construction |
| **S4 `expectancy_alias_stamp`** | `bug` | `expectancy_r` ≡ `candidate_ev_r` byte-equal on 8,448/8,448 — a duplicate field masquerading as a second measurement (`PHASE1_OPEN_QUESTIONS.md` Q1 table + cross-cutting 2) | stamp as deprecated alias (the `cd_pool.py` triple-block pattern: explicit populations + `deprecated_alias_of`) |
| **S5 `memo_key_set_canonicalization`** | `bug` | FD memo-key instability survives at HEAD: `_exact_content_key`'s set branch returns `frozenset(items)` (`cuts.py:319`, fa2-integration), so equal set-valued payloads can get unequal memo keys (`FD_VERIFY.md` §FD3; `a2_verify/MEMO_KEY_PROBE.json`). Cache-key-only — a miss recomputes through the exact path — so the defect costs determinism-of-reuse, not outcomes | canonicalize (sorted tuple) in the set/frozenset branch |
| **S6 `missed_projection_completeness`** | `bug` | Feb emitter drift: `pretrade_cost_packet_status` present on zero Feb rows; repair-status columns null in pools while repairs demonstrably ran; MISSED rows carry no execution-fill field so pool studies silently study the heuristic (`FULL_FLOW_SPEC.md` L9/L10; `PHASE1_OPEN_QUESTIONS.md` Q2 implication) | projection completeness for repair/cost/fill-authority stamps; extend the `decision_semantics` authority-stamp pattern to the MISSED projection |
| **S7 `four_tuple_join_key`** | `bug` (join hazard) | `candidate_id` is not unique across the pool; joins require the `(candidate_id, decision_time_utc, symbol, side)` 4-tuple (Phase-1 register row P; `FULL_FLOW_SPEC.md` L9) | the 4-tuple is the ONLY sanctioned join key in every new analyzer; float-exactness endpoint reconstruction is banned where a native gross field exists (Q3: the `binary_population` method drops 70–78% of genuine endpoint rows to float noise) |
| **S8 `softened_reject_semantics`** | provisional `unjustified-gate` — **classification pending adjudication** | 3,536 selector-reject rows re-enter as `open-reduced-risk` — non-monotone (`FULL_FLOW_SPEC.md` L3e) | fix or **document as intended semantics** (the commission allows both); the T1 census decides which; if documented-intended, the item exits the repair set with the record kept |

Also carried under R-SCHEMA as **documentation duties** (B5 standing corrections, no code):
the loss-class precedence wording ("≥0.25 floor applied BEFORE recoverability" in
`LOSS_CLASS_RULE_RATIFICATION.md`/register row A), the `CALIBRATION.md` "measured means" →
config-constants correction, and the retirement of C5's two evidence legs from every future
citation.

---

## 5. R-GEOMETRY — a DERIVATION RULE, not hand-picked numbers

- **Defect classification: `wrong-geometry`.** Structure-tight stops genuinely bind on the
  truthed residual (~41.6% Jan / 31.8% Feb of the pool spread-killed at broker-true p50;
  SPX500 ~52%, NAS100 ~26–28%), and the executed book's largest loss class both months is
  exit geometry (Jan −19.95 R / Feb −13.97 R at the ratified rule, dominance understated by
  ~0.25/0.63 R by the floor precedence) — but the flagship kill exhibits were spread-input
  fiction (C3), and the exit-side recoverable mass on the CURRENT book is bounded by the
  driftless-barrier arithmetic (TP-at-the-0.25R-floor recovers only +3.41/+2.83 R/month;
  loser-MFE survival 0.656/0.697 vs 0.700 predicted, THINNER deeper). **Receipts:**
  `B5_ADVERSARIAL_VERDICTS.md` §C3/§C1; `b5_verdicts.json` C1-A/C1-B/C3-A/C3-B;
  `FULL_FLOW_SPEC.md` L2/L8; FC 0/40 (the overlay FAMILY died OOS; the AXIS is alive).
- **Derivation rule (declared method; cells come from T1 on truthed costs):**
  1. every candidate geometry cell is drawn from **FB's 198×10 grid as the declared prior**
     (a SCREENING FAMILY per A4 — internally max-T/BH controlled; non-graduating cells are
     DEAD absent a new declaration; FB's two survivors +11.901/+1.647 R at their cells,
     A2-verified bit-identical);
  2. cells are re-screened at T1 **on truthed costs** (post-2.1/2.2) with the era label
     disclosed; any graduation to a measured arm is a **new declared step** at the ratified
     rule (`CANDIDATE_BOOK_V1`, sealed `B_balanced` α = 0.10) against the A4-adjudicated
     family table;
  3. **entry/stop/target CONTRACT families carry the yield case**; exit tweaks to the current
     book are bounded ex ante by the +3.4/+2.8 R implementable ceiling and are not the
     program's headline;
  4. the **breakeven/trail family is the decisive unknown** and is decided on ordered-path
     data (post-MFE entry-revisit) — undecidable from per-trade tables (C1-B);
  5. the winner-side giveback channel (Feb TP@1.75 +10.62 R vs Jan +0.16 R) is treated as
     **one-month-fragile** and never sized from February alone;
  6. the dominance ordering is never quoted at MFE floors ≥ 0.35 without the inversion
     disclosure; 7. the live no-edge branch is carried: with both months' executed gross ~0,
     exit-side work is not assumed to out-rank direction/entry work merely because its bucket
     is bigger.
- **Cells selected by this rule are DECLARED in the freeze (§10) before T2 arm (iii) runs.**
  L3c's dead router (one exit contract for ten families, `momentum_exhaustion` on
  8,448/8,448) is resolved HERE: family-fit contracts are the repair; whether the router
  mechanism revives or retires is recorded as a design decision in the same cell declaration.
- **Ex-ante expected effect:** honest statement — **unknown until T1 on truthed costs**;
  bounded ex ante as above. Direction expected: fewer cost-kills at survivable geometry,
  book delta sign unknown.
- **T2 arm:** (iii) and (v). **T1 label: "no selection feedback"** (geometry changes
  admission and the executed set).
- **Companion obligation (C5 trigger):** R-GEOMETRY/R-CAPS widening re-populates hard pools
  (936/1,969 Jan and 716/1,888 Feb windows already hold ≥2 eligible candidates) whose
  within-set outcomes are ordered by nothing measured in-band — **selection instrumentation
  ships as a companion to the funnel repairs**, and the seed-band expectation inherits the
  same conditionality.

---

## 6. R-CAPS — the derivation rule, stated formally

- **Defect classification: `unjustified-gate`** (values without surviving external
  justification — with `overkill` the plausible alternative reading, and FLAWLESS the
  possible verdict if the frontier vindicates the current values; the classification is of
  the caps' EVIDENCE BASIS, which C2-B emptied, not a presumption of their wrongness).
  The caps: `selected_cell_pretrade_max_spread_r = 0.10`,
  `selected_cell_pretrade_max_total_cost_r = 0.15` (`config/agent_config.yaml:715-716`,
  enforced `broker_net_cost_engine.py:718-728,772-776`, consumed `v4t:86204-86224`).
  **Receipts:** `b5_verdicts.json` C2-A/C2-B; `B5_ADVERSARIAL_VERDICTS.md` consequences 2.
- **What may NOT be cited (binding):** "the gate was right on average" — 77.3% of the
  refused set's −22,923.5 R is the gate's own cost estimate fed back as outcome; refused vs
  kept price-normalized market outcomes are near-identical (−0.0238% vs −0.0182%); an
  information-free size-matched gate captures 73.9% of pool loss vs the 94.1% printed. The
  +3,213.5 R top-decile killed-winner figure may not be booked as expected recovery
  (denominator artifacts at current geometry: decile-9 winners 96.4% blocked, 11 bp stops,
  gross pinned at the 2R cap).
- **Derivation rule (declared method; cells come from T1 on truthed costs):**
  Let P\* be the January pool re-priced under §2 (spread truth + one ruler). The declared
  search axis is **the existing `cost_ceiling_*` dials** — `COST_CEILING_CELLS =
  (0.05, 0.10, 0.25, 0.50, 1.00)` on `total_cost_r` (`repairs.py:781`), with the companion
  `spread_r` cap held at its declared ratio or swept on the same named grid, and **no cell
  outside the declared grid ever measured**. For each cell c:
  - **F(c)** = Σ net-R of pool winners FREED (refused under the current caps, admitted under
    c), priced on **externally validated costs ONLY** (SPREAD_MODEL_V1 hour-aware truth +
    broker-true commission + swap at the 120-min horizon), with a price-normalized companion
    column reported;
  - **A(c)** = Σ net-R of pool losers ADMITTED under c, same pricing;
  - the candidate frontier = argmax over the declared grid of **F(c) − A(c)**, subject to a
    train/holdout split within January and the multiplicity discipline of a declared
    screening family.
  **Constraints:** (1) no quantity fed back from the gate's own cost estimate appears on the
  outcome side (the C2-B identity); outcomes are gross + external cost, never the pool's
  self-debited net; (2) reachable winner mass is quoted at the consistent-rule pairing —
  Feb cost-attributed **74.1% (5,554)** / Jan 78.1% — never 84.3% (the ~780 Feb winners and
  ~1,285 Jan behind non-cost selector gates are outside cap reach and get their own line);
  (3) **joint with R-GEOMETRY**: both F and A move mechanically when the stop denominator
  moves, so cap cells are re-derived after any geometry cell lands, never carried across;
  (4) acceptance in T2 is scored on price-normalized or post-re-geometry outcomes, never on
  this pool's net-R alone, which the caps partly manufacture.
- **Ex-ante expected effect:** honest statement — **unknown until T1**; the direction of any
  loosening is "frees winners at the price of admitting losers", and in a pool whose
  cheapest band is negative on average the null expectation is that the frontier lands NEAR
  the current caps; the analysis is run because the caps' evidence basis is empty, not
  because loosening is presumed profitable.
- **Composition (hard rule, existing `INCOMPATIBLE_REPAIRS` row, `repairs.py:1136-1147`):**
  `cost_ceiling_*` does NOT compose with `commission_broker_true_gated` (two wrappers would
  gate one packet). **Any arm carrying a ceiling cell swaps the CJ recipe's gated commission
  for `commission_broker_true` (accounting-only) so exactly one wrapper owns the gate** — the
  swap is declared in the arm manifest and named in the receipt. At most ONE ceiling cell per
  arm (§9). T2 arm: (iii) and (v). **T1 label: "no selection feedback."**

---

## 7. Sol adoption register (the four wave-20 default-off deliverables, verified by path)

Adopted per `SOL_DISPOSITION.md` (content-via-FG, A2-verified); paths verified by direct read
in the integration tree `/Users/borr/GTOSActive/worktrees/fa2-integration-20260803`
(branch `phase19/fa2-integration`) on 2026-08-04:

| adoption | verified paths (fa2-integration tree) | state |
|---|---|---|
| **FD — decision semantics** | `src/research_infra/train_engine/decision_semantics.py` (fill-authority stamps verified at `:1429-1446`: `marketable_limit_constant_template_non_authoritative` / `modeled_template_not_measured` / `authoritative_execution_fill_probability = None`) | default-on projections are evidence-shape only (`sealed_compatible=False`); economic repairs default-off (`FD_VERIFY.md` §FD3). **The FD memo-key defect survives at HEAD** (`cuts.py:319` frozenset branch) → repaired as R-SCHEMA **S5** |
| **CR — capture infrastructure** | `src/research_infra/walkforward/fidelity.py`; `src/research_infra/walkforward/gate.py`; `tests/research_infra/test_cr_ny_metals_capture.py`; protocol script `docs/audits/fable5-vision-audit-20260725/phase19/receipts/cr_ny_metals_capture.py` (commit `47139bc35`) | adopted **as INFRASTRUCTURE** — stays live regardless of the class verdict (N1 REPRICED: the NY-metals class went gross-negative in February's own funnel); CR's March-decode asterisk is adjudicated INSIDE the March prereg (Phase E) |
| **FF — observability** | `src/research_infra/train_engine/cuts.py:866-868` (`hard_eligibility_observability` patch id + stamp), registered `default_on=False` (`:1612`), absent from `TRAIN_SAFE_SET_PATCHES`/`TRAIN_DEFAULT_PATCHES` (`:1745-1756`); gating `src/research_infra/fast_engine/accel.py:155` | default-off; fails closed unless count/keys/digest reconcile; it is what measured the walk's 92/96-empty hard pools |
| **FE — telemetry (`condition_feature_propagation`)** | `src/research_infra/train_engine/cuts.py:1654` (`make_condition_feature_propagation_patch`), patch id `:1663`, `default_on=False` (`:1721`); 15-field `CONDITION_FEATURE_KEYS`; explicit opt-in set `TRAIN_CONDITION_FEATURE_PATCHES` (`:1762-1765`) | default-off, sealed-incompatible, observation-only fail-open. **Carries the WALK-F1 miswire** (features reach TRADE/ORDER, never MISSED) — being fixed by the R-SCHEMA implementation agent as **S1** |

---

## 8. Composition summary (what runs where)

| repair / entry | (i) | (ii) | (iii) | (iv) | (v) |
|---|---|---|---|---|---|
| CJ recipe (6 cuts + `commission_broker_true_gated` + `swap_horizon_true`) | X | X | X (commission swaps to accounting-only when a ceiling cell is present) | X | as (iii) |
| `spread_input_truth` | X | X | X | control | X |
| `cost_ruler_harmonize` (Feb; proven no-op Jan) | X | X | X | control | X |
| R-BELIEF bundle (3.1–3.5) | | X | X | controls | X |
| R-SCHEMA set (S1–S8) | | X | X | (is its own control; zero-delta standard) | X |
| R-GEOMETRY cells (declared at freeze from T1) | | | X | | X |
| R-CAPS `cost_ceiling_*` cell (≤1; declared at freeze from T1) | | | X | | X |
| admitted candidates (breaker; OB-retest if graduated) | | | | | **X — only here** |

The candidates' door: graduation happens at the ratified rule against the A4-adjudicated
family table (A1's corrected-null re-issue included), then the candidate is MEASURED IN via
arm (v), openly declared and billed — never inside a repair delta.

---

## 9. INCOMPATIBLE_REPAIRS — rows this spec requires (refused by name, with reasons)

Existing rows carried forward (`repairs.py:1136-1160`): `commission_broker_true_gated ×
cost_ceiling_*` (one wrapper owns the gate; compose ceilings with the accounting-only
commission variant); `neutral_seed_replicate_r1 × neutral_seed_replicate_r2` (one seed dial
per arm).

New rows this program adds:

1. **`<any_horizon_extension> × swap_horizon_true`** (declared prospectively — no horizon
   repair exists in this set; C7 ruled the wall symmetric censoring and T1 horizon
   counterfactuals hypothesis-measurement). Reason: `swap_horizon_true` prices swap at
   `TRUE_SWAP_HORIZON_BARS = 120 min / 15 = 8` bars, derived from
   `REPLAY_MAX_HOLD_MINUTES = 120` (`repairs.py:104-118`). Any repair that moves the
   120-minute wall silently invalidates that constant; the composition is refused so the
   swap horizon is RE-DERIVED with the new wall, never inherited.
2. **`belief_cost_single_charge` is ATOMIC**: the context-wire-only form (add `cost_r` to
   the replay debate context without the downstream neutralizations) is refused as a
   registrable id — B5/C6-B measured the double-charge it creates (57.8% / 78.1% funnel
   re-pricing). The charge-point decision and its neutralizations land as one entry or not
   at all.
3. **`cost_ceiling_<a> × cost_ceiling_<b>`**: at most one ceiling cell per arm — two ceilings
   on one packet builder would leave the receipt unable to say which cap decided.
4. **A repair never composes with its own inert control in one arm** (the control replaces
   the repair in arm (iv); pairing is attribution, not composition).
5. **R-GEOMETRY cell × R-CAPS cell carried ACROSS a geometry change**: a cap cell derived on
   pre-geometry denominators is refused for composition with a landed geometry cell until
   re-derived (§6 constraint 3). Same-freeze cells derived jointly are fine.

---

## 10. Freeze protocol stub (executed at Phase E, before any March byte)

Phase E freezes, in one committed receipt (`MARCH_PREREG_V1.json` + companion md):

1. the **exact repair registry entries** — final ids, `REPAIR_PAIRS`, `INCOMPATIBLE_REPAIRS`
   as landed, and the file SHAs of `repairs.py`, `cuts.py`, `decision_semantics.py`, and
   every intercepted engine file;
2. the **declared R-GEOMETRY and R-CAPS cells** (from T1 on truthed costs, per §5/§6
   derivation rules — cells named, grid closed);
3. **config bytes**: `agent_config.yaml` cap values if any R-CAPS cell lands as config, the
   SPREAD_MODEL_V1.json SHA, the broker-clock module SHA;
4. the **T2 arm compositions** exactly as §8, including the commission gated→accounting swap
   wherever a ceiling cell rides;
5. the March arms (S0R0 baseline, the frozen composed arm, and — if an admission stands at
   freeze — the composed+admitted arm), all in ONE decode event; primary endpoint the paired
   daily net-R delta; one-sided α, pass threshold, and MDE (from day-ledger variance + the
   Phase-B seed band) fixed ex ante, with the MDE language saying **"censoring"** per C7;
6. NOT_EVALUABLE terminals; the CR March-decode asterisk adjudicated IN the prereg; the
   S0-style metadata-only March-pack preflight.

Nothing in this spec authorizes reading a March byte; Borhen triggers the confirm
(OD-FA2-1).

---

## 11. Flags — commission Phase-C wording vs B5 reordering (flagged, not resolved)

Recorded so no future reader mistakes the original commission text for the operative spec:

1. **R-COST-TRUTH scope**: the commission enumerates 3 placeholder spreads + Feb 0.12
   defaults; B5/C3 measured the class at 20/24 symbols and added ruler harmonization. The
   commission's enumeration is a proper subset; this spec follows B5 (its consequences
   section is binding).
2. **R-BELIEF instruction**: the commission's "wire `context[\"cost_r\"]` so thesis EV is
   net-of-cost", executed literally, implements the exact double-charge B5/C6-B measured.
   This spec's §3.1 supersedes the sentence.
3. **R-GEOMETRY framing**: the commission's "this is where the cost gate's winner-kill gets
   addressed from one side" reads geometry as the primary winner-kill lever; B5/C3 refuted
   that causal reading (the flagship exhibits are input fiction; geometry is second, on the
   residual).
4. **R-CAPS premise**: the commission's ""the gate was right on average" is where the
   analysis starts" grants the premise evidentiary standing; B5/C2-B retired it entirely
   (accounting identity). Direction of the class is unchanged; the sanctioned evidence basis
   is not.
5. **Arm (i) naming**: "cost-truth-only (R-COST-TRUTH alone)" rides a baseline recipe that
   already carries two cost repairs (`commission_broker_true_gated`, `swap_horizon_true`).
   Since the sealed 57/58-trade baselines carry both, the (i)−baseline delta isolates spread
   truthing + harmonization correctly — but any prose quoting arm (i) must name all three
   cost repairs or readers will misattribute.
6. **R-SCHEMA enumeration**: the commission lists three items; the receipts added five more
   (S1–S5 origins in B1/B4/A2). Accretion, not contradiction — recorded because the
   commission text is the older document.

---

## 12. Ownership and honesty clauses (binding)

- Every number produced under these repairs on January, February, or the June gap is
  **DEVELOPMENT-FITTED lane evidence** until the March confirm; the RESULT doc labels every
  number with its class; nothing upstream of the March one-shot is ever quoted as
  confirmatory, however good it looks.
- **Kill, park, and arm stay Borhen's.** This program delivers understanding + landed
  repairs + measured results + a priced decision sheet. No verdict to abandon the family
  exists in this vocabulary, and nothing arms itself out of this spec.
- Per-repair deltas do not sum (path dependence); every table printing them says so.
- Where this spec says UNKNOWN, the T1/T2 measurement decides it; where a measurement
  contradicts an expectation stated here, the contradiction is reported loudly in the
  RESULT doc's "What I got wrong" — that is what an ex-ante spec is for.
