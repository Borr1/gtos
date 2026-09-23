# Phase 3 Status, Numbers, And Plan

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Source State

- Live-state regenerated before this report.
- Current research state is fresh against `fa84eeb research: validate phase3 base before expansion`.
- Backlog count summary corrected in `6c12060 docs: correct ml backlog item counts`.
- Remaining worktree dirt after regeneration is live/runtime or pre-existing local state, not staged research output.

## 2026 Raw-OHLC Path-Scaling Snapshot

This table is computed from existing local event logs for 2026-01-02 through 2026-04-30. It is not live broker PnL and not a promotion result. Cost assumption is `0.05R` per resolved trade.

Source event logs:

- V0: `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_ablation_v0/raw_ohlc_path_ablation_v0_events_20260501T150924Z.jsonl`
- V1: `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_ablation_v1_mtf/raw_ohlc_path_ablation_v1_mtf_events_20260501T192723Z.jsonl`
- V2: `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/raw_ohlc_path_scaling_v2_structural_levels_events_20260501T213225Z.jsonl`

| Phase | Variant | Resolved n | Net sum R | Net mean R/trade | Win rate | Readout |
|---|---|---:|---:|---:|---:|---|
| V0 | BASE_RAW_FIXED_TP | 328 | +6.702780 | +0.020435 | 44.512% | barely positive |
| V0 | J46_J49_ONLY | 413 | -31.133770 | -0.075384 | 45.278% | negative on 2026 slice under M15-only path |
| V0 | PATH_LOCK_HALF_GAIN_V0 | 324 | +9.853653 | +0.030413 | 49.383% | best V0 2026 slice, still weak |
| V1 | BASE_RAW_FIXED_TP | 450 | +81.195901 | +0.180435 | 48.000% | lower-TF path resolution materially changes 2026 scoring |
| V1 | J46_J49_ONLY | 474 | -48.961735 | -0.103295 | 40.506% | negative on 2026 slice under V1/V2 path engine |
| V1 | PATH_LOCK_HALF_GAIN_V0 | 450 | +62.986721 | +0.139970 | 54.444% | positive but not promotion-grade |
| V2 | J46_J49_ONLY | 474 | -48.961735 | -0.103295 | 40.506% | baseline comparator for V2 2026 slice |
| V2 | STRUCT_SWING_PROTECTED_V2 | 474 | +97.308326 | +0.205292 | 72.996% | strongest clean mean except FVG, but full-corpus concentration-blocked |
| V2 | STRUCT_FVG_MID_EDGE_V2 | 474 | +124.510270 | +0.262680 | 70.886% | best 2026 slice, but not yet selected as cleanest due full-corpus truncation/cohort behavior |
| V2 | STRUCT_OB_BOUNDARY_V2 | 474 | +61.878108 | +0.130545 | 66.034% | cleanest V2b validation candidate despite not best 2026 mean |
| V2 | STRUCT_COMPOSITE_ANY_V2 | 474 | +111.878635 | +0.236031 | 76.371% | 2026-positive but full-corpus rejected as over-locking |

Important interpretation:

- The current production-relevant baseline remains J46-J49 as the validated historical/risk baseline, but the 2026 raw-OHLC slice shows J46-J49 path behavior is weak/negative in this research harness.
- V2 structural path management looks materially better on 2026 data, but this is still same-dataset/research evidence.
- V2b has zero post-cutoff rows; therefore it has not validated or failed.
- Percentage improvement versus a negative J46 baseline is not meaningful as a relative percent. The meaningful V2 2026 absolute deltas versus J46 are:
  - Swing: `+0.308587R/trade`, `+146.270061R` sum.
  - FVG: `+0.365975R/trade`, `+173.472005R` sum.
  - OB-boundary: `+0.233840R/trade`, `+110.839843R` sum.
  - Composite: `+0.339326R/trade`, `+160.840370R` sum.

## Full-Corpus Research Baseline

Current full-corpus path findings through 2026-04-30:

| Layer | Status | Full-corpus headline at 0.05R cost |
|---|---|---|
| J46-J49 validated baseline | DSR-surviving program result | +0.742R/trade in prior portfolio policy research; forward-citable as a validated claim in current project doctrine |
| V0 fixed-R path scaling | closed, no promotion | J46 best globally at `+0.190128R`; best lock-only `+0.170370R` |
| V1 MTF path resolution | diagnostic infrastructure accepted | J46 best globally at `+0.163894R`; fixed-R lock-only rejected |
| V2 structural selector | discovery signal alive | Swing `+0.188405R`; OB-boundary `+0.177765R`; J46 `+0.163894R`; composite rejected |
| V2b OB-boundary validation | blocked by no prospective rows | `0` post-cutoff resolved rows |
| V3 reentry | design-only for now | blocked from outcome-mining until V2b answers level-quality question |

## Backlog Status

Mechanical parse of `research/ml_program/MASTER_BACKLOG.md` after count correction:

| Status | Count |
|---|---:|
| PENDING | 145 |
| DEFERRED | 11 |
| DONE / completed / answered / shipped / filed / partial / failed categories | 24 |
| Total | 180 |

Open pending IDs by section:

- A: 18 (`A-1` through `A-18`)
- B: 5 (`B-2`, `B-3`, `B-4`, `B-5`, `B-7`)
- C: 8 (`C-2` through `C-9`, excluding failed `C-1`)
- D: 12 (`D-1` through `D-12`)
- E: 5 (`E-1` through `E-5`)
- K: 14 (`K-5` through `K-18`, excluding deferred/failed early K items)
- L: 6 (`L-1`, `L-2`, `L-3`, `L-4`, `L-5`, `L-8`)
- M: 10 (`M-5`, `M-6`, `M-7`, `M-10` through `M-16`)
- O: 3 (`O-3`, `O-5`, `O-8`)
- P: 9 (`P-1`, `P-2`, `P-3`, `P-5` through `P-10`)
- R: 9 (`R-1` through `R-9`)
- RR: 7 (`RR-1` through `RR-7`)
- S: 5 (`S-1` through `S-5`)
- U: 14 (`U-1`, `U-2`, `U-4`, `U-6`, `U-8` through `U-17`)
- V: 9 (`V-1` through `V-9`)
- X: 7 (`X-1` through `X-7`)
- Z: 4 (`Z-1` through `Z-4`)

Closed/answered/deferred highlights:

- DSR validated: J46-J49 and S79.
- DSR failed: K54 v1, standalone instrument WR claims, +0.200R expectancy, FVG-impulse, +17pp OB relative headline.
- Failed/killed: C-1 second-half session feature, K-4/P-4 Stoikov micro-price on MT5 substrate, Q-1 DLinear baseline gate, B-1 K54 v3 master bundle.
- Deferred: K-1/K-2/K-3 volume/dollar/imbalance bars on MT5 retail substrate; Q-2 through Q-9 sequence models until n >= 5000.
- Shipped/design: entry-side slippage logger shipped; token-usage logger design complete; close-side slippage extension pending integration.

## Progress View

These percentages are engineering/research maturity estimates, not statistical claims.

| Area | Maturity | Reason |
|---|---:|---|
| Validation discipline | 70% | DSR doctrine, claim ledger, V2b protocol, freshness audit exist; effective-N and universal PBO infra still open |
| Baseline J46/S79 | 75% | two DSR-surviving pillars; 2026 path behavior shows drift risk |
| Path scaling V0/V1 | 100% research-closed | V0 and V1 answered their layer questions |
| Path scaling V2 | 70% discovery-closed | structural signal exists; concentration blocks promotion |
| Path scaling V2b | 20% validation-ready | spec exists; zero post-cutoff resolved rows |
| Path scaling V3 | 15% | design intent clear; outcome-mining blocked |
| Orderflow data/tooling | 40% | Databento path works; labels/proxies/depth sample are the blockers |
| Orderflow alpha validation | 5% | no broad rule; actual broker-R only 1/54 candidate rows in expanded coverage |
| ML/K54 family | 30% | K54 v3 failed; NAS_US30 specialist remains a shadow candidate |
| Risk policy | 45% | S79 validated; R-1/R-2/R-5/R-6/R-7 bundle still pending |
| Vol-conditioning | 20% | literature path exists; NA8 key-cohort result was not supportive enough |
| Execution telemetry | 45% | entry slippage shipped; close slippage and pending-limit telemetry still open |

## Current Plan

1. V2b forward validation:
   - Build/enable rolling post-cutoff replay for every qualifying setup.
   - Emit OB-boundary, J46, swing, FVG, fixed-R comparators, lower-TF availability, ambiguity state, and no-leak diagnostics.
   - Stop calling V2b blocked once the first post-cutoff resolved pairs exist; use interim reports until sample floors are met.

2. Existing-data V2 forensics:
   - Decompose why FVG wins the 2026 slice but OB-boundary is cleaner full-corpus.
   - Run leave-one-symbol/session/side/regime stress.
   - Keep results discovery-only.

3. V3 architecture only:
   - Specify reentry state machine, risk budget, cost accounting, and failure conditions.
   - Do not mine V3 outcomes until V2b validates or rejects level quality.

4. Orderflow:
   - Follow NAS100-first forward collection.
   - Collect trades + MBP-1 for new supported NAS100 candidates; MBP-10 only for predeclared windows.
   - Keep synthetic/path, actual broker R, and fill/no-fill labels separate.
   - Add pending-limit telemetry before relying on LIMIT_PLACED labels.

5. Proxy/data:
   - Resolve USDJPY/6J strict transfer or keep it blocked.
   - Keep GBPJPY blocked until a two-book synthetic method is registered.
   - Run D-11 2022-2023 data quality bias check before leaning harder on old backfill.

6. Backlog priorities:
   - Methodology: M-7, M-12, M-13.
   - Risk: R-1, R-2, R-5, R-6, R-7/R-9.
   - Execution observability: O-8, L-7 close-side extension, pending-limit telemetry.
   - Asset/mechanism: A-8, E-1, E-4.
   - AI/tooling: L-6 integration, L-1/L-2 grounding design.
   - Shadow ML: evaluate NAS_US30 specialist through K55 shadow, not production.

## Staleness/Artifact Issues Found

- Forward collection plan had stale pre-proxy defaults and was fixed in `fa84eeb`.
- Forward plan limit-intent count read the wrong JSON location and was fixed in `fa84eeb`.
- Backlog count summary was stale by two rows and was fixed in `6c12060`.
- Mutable shadow logs remain unsuitable as immutable population counts.
- Same-date reports can drift if rerun in place; future research should prefer timestamped or content-addressed outputs.
