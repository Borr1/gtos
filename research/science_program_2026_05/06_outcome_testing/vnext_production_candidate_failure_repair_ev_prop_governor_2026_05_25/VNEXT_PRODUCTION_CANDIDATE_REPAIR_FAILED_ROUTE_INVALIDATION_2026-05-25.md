# vNext Production Candidate Repair - Failed Route Invalidation

Date: 2026-05-25

Route id: `vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25`

## Verdict

`75a85d244 research: complete vnext production change route` is not activation-safe. The prior completion claim is preserved as evidence and invalidated for broker-facing activation.

## Evidence

- Failed Stage09 summary: `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json`
- Failed Stage10 completion audit: `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json`
- Failed session state: `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json`
- Forensic report: `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md`
- Stage09 replay shards: `11` shards, `253234` rows, shard-manifest hash `2f79b5caa9ee44ffb2cf0dedc9fbb0c5a55b5d0645e878af73bfec1bc6bd6848`
- Input manifest: `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json`
- Invalidation ledger: `research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_LEDGER_2026-05-25.jsonl`

## Recomputed Failure Facts

| Metric | Failed route value |
|---|---:|
| Candidate rows | 253,234 |
| Baseline selected rows | 35,983 |
| Baseline performance rows | 33,845 |
| Baseline total R | 4008.331701256812 |
| Baseline expectancy R | 0.118432019538 |
| Baseline win rate | 44.765844290100% |
| Baseline profit factor | 1.214657122925 |
| New mechanical selected rows | 10 |
| New mechanical performance rows | 10 |
| New mechanical total R | -4.999959196997 |
| New mechanical expectancy R | -0.499995919700 |
| New mechanical win rate | 20.000000000000% |
| New mechanical profit factor | 0.375005100375 |
| AI no-paid-call selected rows | 0 |

The failed route selected only 10 of 253,234 generated candidates, lost about -5R, had negative expectancy, and had profit factor below 1. The baseline/current shadow stream selected 35,983 rows and produced about +4008.3317R.

## Invalidated Completion Claim

The Stage10 audit recorded `complete=true` and `instruction_coverage_ok=true`, but its embedded stage table still had `STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER=in_progress`. More importantly, the completion gate did not reject the negative, near-zero-trade production candidate. Artifact existence and instruction coverage are not viability proof.

## Activation Boundary

Current config still keeps broker-facing vNext execution flags off:

| Flag | Value |
|---|---|
| `gtos_vnext_runtime.apply_to_execution` | `False` |
| `gtos_vnext_runtime.pre_ai_apply_to_ai_call` | `False` |
| `gtos_vnext_runtime.ltf_path_execution_apply_to_execution` | `False` |
| `gtos_vnext_runtime.prop_safe_selector_apply_to_execution` | `False` |

This proves current broker-facing safety only. It does not repair the failed candidate and cannot be used as completion.

## Stage 00 Decision

- Branch decision: `failed_route_completion_claim_invalidated`
- Implementation decision: continue repair route; do not activate the failed route.
- Replay effect preserved: baseline `+4008.331701R` versus new mechanical `-4.999959R`.
- First incomplete invariant: `STAGE_01_FULL_FAILURE_ANATOMY_LEDGER`

## Next Same-Evidence-Class Work

Build the full row-level failure anatomy from `stage09_shards/*/replay_comparison.jsonl.gz`, Stage09/Stage10 source code, and upstream Stage03/Stage04 joins. The next artifact must preserve selected rows, dropped baseline rows, route-semantics bugs, selected-only coverage, AVOID pressure, LTF effect, AI/no-paid-call behavior, and acceptance-gate failures before moving to repair.
