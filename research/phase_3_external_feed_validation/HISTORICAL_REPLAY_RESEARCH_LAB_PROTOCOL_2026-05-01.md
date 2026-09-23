# Phase 3 Historical Replay Research Lab Protocol

**Created:** 2026-05-01  
**Status:** research/tooling protocol  
**Scope:** historical rapid-replay research over existing Phase 3 truth-layer data  
**Promotion allowed:** no  

## Boundary

This protocol exists to make the existing historical data usable as a fast, live-like research lab without pretending that historical replay is the same thing as untouched future evidence.

It authorizes tooling, measurement, strategy-surface exploration, and controlled replay. It does not authorize alpha promotion, live trading changes, prompt changes, risk changes, execution changes, or paid AI/API calls.

The key engineering idea is prequential replay:

1. Sort historical opportunities by replay clock.
2. Project each row into an as-of observation.
3. Let the strategy decide from that observation only.
4. Attach scorer-only outcomes after the decision is locked.
5. Record hashes, trial identity, run mode, and leakage diagnostics.

## Honest Constraint

Code can be prevented from seeing future fields. A human researcher cannot unsee results already inspected. The lab therefore separates two different risks:

- **Mechanical leakage:** engineered away by the replay clock, observation projection, and scorer-only outcome fields.
- **Researcher contamination:** controlled by labels, frozen specs, split manifests, trial budgets, PBO, DSR, effective_N, and prospective confirmation.

This is not bad news. It means historical data remains extremely useful for discovery and engineering, but the evidence class must be named correctly.

## Limitation Register And Controls

| Limitation | Engineered control | Remaining interpretation |
|---|---|---|
| Truth-layer rows contain as-of features and future outcomes in the same JSON object. | Strategy receives an allowlisted observation projection. `truth_*`, `m1_*`, `m5_*`, `m15_*`, and `lower_tf_*` fields are scorer-only unless explicitly aliased as as-of fields. | If a field is needed for strategy, it must be justified as available at candle close and added to the allowlist. |
| Historical file order may not equal live chronological order across symbols. | Replay sorts by `candle_close_utc` and `opportunity_key` before evaluation, and reports input-order regressions. | Sorting creates a multi-symbol replay clock; it does not simulate process scheduling. |
| Duplicate opportunity keys can double-count evidence. | Duplicate keys are counted and block clean interpretation until resolved. | A duplicate-free report is required before using results in controlled research. |
| Strategy code could request outcome fields directly. | Built-in JSON strategy DSL validates every referenced field against the observation schema before replay. | Arbitrary Python strategy plugins should stay disabled until a sandboxed interface is added. |
| Outcome leakage can happen if scoring is mixed with decision logic. | Two-phase loop: decision first, scoring second. The scorer attaches outcome only after `TAKE` or `SKIP` is fixed. | Reports must preserve action counts separately from scored/resolved counts. |
| Post-hoc cohort selection can look strong on the same dataset. | Every replay run carries a run mode and evidence class. Same-dataset historical positives remain diagnostic unless frozen before an untouched slice. | Same data can rank ideas and kill weak ideas, but not prove a discovered edge. |
| Multiple experiments inflate false discovery risk. | Strategy specs are hashed. Locked families consume trial budget. Matrix evaluations keep all registered candidates in scope for PBO/effective_N. | Flexible discovery is allowed, but claims must include family/trial accounting. |
| Parameter optimization can silently become curve fitting. | Parameter grids must be declared before locked replay. Optimizer output is a candidate generator, not final evidence. | Nested or future splits are required before promotion-grade claims. |
| Rolling regime decay can hide behind positive full-sample averages. | Reports must support period/fold summaries and should include recent stress slices before any controlled follow-up. | A high mean with weak fold stability remains a research lead only. |
| Data gaps and lower-timeframe incompleteness can make outcomes unreliable. | Resolution-safe population filters remain scorer-side. Gap diagnostics are not exposed to strategy unless a future as-of data-quality feature is explicitly registered. | Dropping bad outcome rows after seeing results is invalid. |
| External features can be accidentally future-dated. | Replay checks `external_snapshot_as_of_utc <= candle_close_utc` where both fields exist. | Feature bundles still need source-specific publication-time audits. |
| HTF state can leak if the row uses a partially known higher-timeframe close inconsistently. | Replay spec must name HTF close policy. Any new dataset builder must stamp features with their as-of timestamp. | Existing truth-layer replay inherits the current historical opportunity builder policy. |
| Date/time features can be overfit. | Date, session, and calendar fields are allowed because they are live-visible, but locked claims require trial accounting and OOS/prospective confirmation. | Time-of-year discoveries are allowed as hypotheses, not proof by themselves. |
| Single-symbol winners can dominate a family. | Effective_N and dominance checks are required before promotion language. | Primary-child effective_N below threshold remains blocked even if both children are profitable. |
| Same-dataset PBO can be uncomfortable after good-looking cohorts. | PBO is treated as a selection-risk diagnostic, not as a veto on all research. | PBO above threshold means "more overfit risk", not "stop researching". |
| Strategy runs can become unreproducible. | Reports include input SHA256, lab-spec SHA256, strategy-spec SHA256, code commit when available, row counts, and run timestamps. | Unhashed or manually edited results are not evidence. |

## Replay Modes

| Mode | Purpose | Allowed output |
|---|---|---|
| `DISCOVERY_SANDBOX` | Explore ideas, generate hypotheses, inspect failure anatomy. | Research leads only. No alpha proof. |
| `LOCKED_HISTORICAL_REPLAY` | Replay a frozen strategy spec on a historical slice. | Same-dataset or pseudo-OOS diagnostics, depending on split status. |
| `REGISTERED_MATRIX_REPLAY` | Evaluate a frozen family of candidates without cherry-picking one winner. | PBO/effective_N diagnostics when enough periods exist. |
| `PROMOTION_DOSSIER` | Assemble evidence after DSR, PBO, effective_N, and untouched/prospective requirements pass. | Promotion recommendation only if all gates pass and CEO approves. |

## Evidence Ladder

1. **Exploratory:** found after looking at the same data.
2. **Locked historical replay:** strategy spec frozen, replayed one observation at a time.
3. **Pseudo-OOS historical:** split was declared before the run, but the broad dataset has already been studied.
4. **Prospective shadow:** rows arrive after registration cutoff.
5. **Live shadow/live micro:** operational evidence under live system constraints.

Phase 3 is currently between levels 1 and 2 for the historical truth-layer cohorts, with prospective infrastructure prepared for level 4.

## Current Implementation Target

The first implementation layer is a truth-layer replay harness:

- Input: `historical_opportunity_truth_layer_v2` JSONL.
- Clock: `candle_close_utc`.
- Decision surface: allowlisted as-of fields and safe aliases such as `cohort_key`.
- Scorer-only surface: realized outcome, lower-timeframe refinements, gap timing, truth confidence, and failure anatomy.
- Output: run summary JSON and markdown report.

This does not replace future raw M15/M1 replay. It establishes the anti-leak contract that raw candle replay should also use.

## Next Engineering Extensions

1. Add raw OHLC replay adapters that expose rolling candle windows through the same observation interface.
2. Add split manifests with purge/embargo rules for strategy families.
3. Add a trial ledger that records every locked family run and its trial-budget cost.
4. Add nested walk-forward research templates for parameter grids.
5. Add matrix-level replay reports that connect directly to DSR, PBO, and effective_N gates.
6. Add optional event-log output for full audit trails when a strategy family becomes important enough to inspect action by action.

