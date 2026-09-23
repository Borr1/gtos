# Lane 2 C-7 / C-9 Path Scaling Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Classify the remaining Lane 2 backlog items C-7 and C-9 from committed artifacts, closing only what is answered and converting the rest into precise blockers.

## Classification

| id | status | classification | blocker/trigger |
| --- | --- | --- | --- |
| C-7 | DONE | Path-9 deep-dive completed: Feb-heavy, cross-cohort temporal-window signal; replication scan shows fragility rather than stable all-window lift. |  |
| C-9 | BLOCKED_WITH_REASON | Architecture/path-scaling chain is partially completed, but the full C-9 comparison is blocked by L2 reconstruction, unresolved V2b forward pairs, and missing lifecycle/pre-fill fields for reentry. | Deterministic L2 candidate reconstruction is still required for L2 on/off architecture attribution.; V2b has 0 resolved post-cutoff OB-boundary/J46 pairs, so structural level quality is not forward-validated.; Close-and-reenter path scaling needs pending lifecycle truth and original POI/pre-fill fields before risk accounting is trustworthy.; Historical OHLC cost/slippage remains an R-sensitivity model, not measured broker cost. |

## C-7 Path-9 Deep Dive

- Path-9 date range: `2026-01-22` to `2026-03-10`.
- Test rows: `176`; February 2026 share: `0.625`.
- Top-symbol share: `0.164773`; positive groups: `4/4`; positive symbols: `6/7`.
- Path-level AUC diff: `0.145445`; rank among fixed-HP CPCV paths: `1`.
- Classification: `CROSS_COHORT_TEMPORAL_WINDOW_SIGNAL_NOT_SINGLE_SYMBOL`.

Path 9 worked because the Feb-heavy Q1 2026 window lifted K54 v2 versus v1 across all four effective groups and six of seven symbols. It was not a single-symbol XAU artifact; XAGUSD was the only negative symbol-level diff.

## C-7 Replication Scan

Fold-level reconstruction averages each row's K54 v2/v1 prediction across the CPCV paths that tested that row, then recomputes paired AUC by chronological fold.

| fold | date min | date max | n | K54 v2 AUC | K54 v1 AUC | diff |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 2024-04-01 | 2025-12-18 | 88 | 0.585622 | 0.588252 | -0.00263004 |
| 1 | 2025-12-19 | 2026-01-22 | 88 | 0.575758 | 0.503581 | 0.0721763 |
| 2 | 2026-01-22 | 2026-02-13 | 88 | 0.677604 | 0.501302 | 0.176302 |
| 3 | 2026-02-13 | 2026-03-10 | 88 | 0.619318 | 0.569731 | 0.0495868 |
| 4 | 2026-03-10 | 2026-03-31 | 88 | 0.476562 | 0.5625 | -0.0859375 |
| 5 | 2026-04-01 | 2026-04-24 | 88 | 0.572831 | 0.512655 | 0.0601756 |

Fixed-HP CPCV path diffs:

| path | n | AUC diff |
| --- | --- | --- |
| 0 | 176 | -0.0371392 |
| 1 | 176 | 0.0357578 |
| 2 | 176 | 0.0279957 |
| 3 | 176 | 0.0940841 |
| 4 | 176 | 0.0860487 |
| 5 | 176 | 0.0408964 |
| 6 | 176 | 0.0935983 |
| 7 | 176 | -0.0595288 |
| 8 | 176 | 0.113669 |
| 9 | 176 | 0.145445 |
| 10 | 176 | -0.0619658 |
| 11 | 176 | -0.11633 |
| 12 | 176 | -0.0605263 |
| 13 | 176 | 0.101111 |
| 14 | 176 | 0.0603289 |

The Feb-heavy window is cross-cohort, but it does not replicate as a stable all-window effect: Path 9 is the strongest CPCV path, while 6 of 15 fixed-HP paths are negative and fold 4 is negative after the window.

C-7 is therefore closed as a diagnostic: the composition question is answered and the replication check says the effect is temporal-fragile, not a reusable all-window condition.

## C-9 Path-Scaling Chain

| component | status | artifact | result |
| --- | --- | --- | --- |
| protocol_frozen | DONE | research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md | Raw-OHLC ablation/path-scaling protocol exists; V0 explicitly blocked L2 attribution and reentry. |
| v0_base_j46_lock_only | DONE | research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_PATH_SCALING_V0_REPORT_2026-05-01.md | J46_J49_ONLY led at 0.05R cost with net_mean_r=0.190128; best lock-only minus J46=-0.019758 globally. |
| v2_structural_selector | DONE_DISCOVERY | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_FINAL_DISPOSITION_2026-05-02.md | STRUCT_SWING_PROTECTED_V2 beat J46 globally by +0.024511 net R at 0.05R cost, but concentration blocked promotion. |
| v2_confluence_deep_dive | ACCEPTED_CANDIDATE_DISCOVERY | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json | FVG and OB confluence/disagreement pockets are positive same-dataset discoveries; Composite remains an over-lock warning. |
| v2b_forward_status_tool | BLOCKED_NO_RESOLVED_PROSPECTIVE_PAIRS | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.json | Prospective rows exist, but resolved post-cutoff OB-boundary/J46 pairs are still zero. |
| v3_exploratory_reentry_replay | STRONGER_THAN_BASELINE_DISCOVERY_ONLY | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json | V3_FVG_ONLY_RESCUE_RISK_BANK has mean_delta_vs_j46=+0.270259 on existing replay, but same-dataset discovery cannot validate reentry. |

## C-9 Blockers

- Deterministic L2 candidate reconstruction is still required for L2 on/off architecture attribution.
- V2b has 0 resolved post-cutoff OB-boundary/J46 pairs, so structural level quality is not forward-validated.
- Close-and-reenter path scaling needs pending lifecycle truth and original POI/pre-fill fields before risk accounting is trustworthy.
- Historical OHLC cost/slippage remains an R-sensitivity model, not measured broker cost.

Trigger: Resume C-9 when L2 reconstruction exists, V2b has resolved post-cutoff pairs that meet sample floors, and pending-lifecycle/pre-fill fields are joined for reentry accounting.

Current V2b counters:

| rows after cutoff | wanted variant rows | wanted resolved rows |
| --- | --- | --- |
| 264 | 110 | 0 |

The strongest current V3 branch remains discovery-only:

| variant | eligible | resolved | mean R | mean delta vs J46 | top group share |
| --- | --- | --- | --- | --- | --- |
| V3_FVG_ONLY_RESCUE_RISK_BANK | 625 | 352 | 0.275834 | 0.270259 | 0.268087 |

## Ambiguity Ledger

- C-7 uses existing K54 v2 CPCV artifacts; it does not open or relabel forward data.
- C-9 has meaningful completed subcomponents, but the exact backlog request includes L2 on/off and close-and-reenter variants that are not executable to validation standard yet.
- V3 positive discovery remains same-dataset and reentry-accounting-limited; it is not validation.
- All path-scaling artifacts retain `NO_PROMOTION_VERDICT`.
