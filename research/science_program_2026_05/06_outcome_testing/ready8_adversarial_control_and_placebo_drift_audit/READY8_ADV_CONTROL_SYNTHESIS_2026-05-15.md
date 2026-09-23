# READY8 Adversarial Control And Placebo Drift Audit

Generated: 2026-05-15T08:57:42Z
Evidence class: `READY8_ADVERSARIAL_CONTROL_PLACEBO_DRIFT_AND_DUPLICATE_ARTIFACT_AUDIT_ONLY`

Terminal posture: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Exact Ledger Coverage

- adv001_rows: 4288
- adv003_rows: 12611
- baseline_drift_rows: 3546
- duplicate_artifact_rows: 3270
- comparison_mapping_rows: 10563
- negative_control_residual_rows: 1
- explained_weakened_rows: 2622
- concentration_rows: 79746
- stress_vs_sealed_rows: 45913
- underpower_rows: 79746

## Control Adjustment Result

- Full control explanation rows: 2608
- Materially weakened rows: 14
- Residual preserved rows: 1
- Underpowered retained rows: 4318
- Not numeric / not adjustable rows: 3622
- Control-match missing rows: 0

## Per-Card Summary

- BEH-001: residual_preserved=1, fully_explained=239, weakened=14, underpowered=540, not_numeric=476, branch_rows=8432, concentrated_branch_rows=7783
- HAZ-001: residual_preserved=0, fully_explained=219, weakened=0, underpowered=1807, not_numeric=1380, branch_rows=16231, concentrated_branch_rows=16231
- HAZ-005: residual_preserved=0, fully_explained=966, weakened=0, underpowered=887, not_numeric=300, branch_rows=23187, concentrated_branch_rows=23187
- MAC-001: residual_preserved=0, fully_explained=659, weakened=0, underpowered=303, not_numeric=438, branch_rows=6376, concentrated_branch_rows=6376
- MAC-004: residual_preserved=0, fully_explained=131, weakened=0, underpowered=700, not_numeric=799, branch_rows=5533, concentrated_branch_rows=5533
- UNC-004: residual_preserved=0, fully_explained=394, weakened=0, underpowered=81, not_numeric=229, branch_rows=3088, concentrated_branch_rows=3088

## Interpretation

ADV-001 and ADV-003 explain or weaken a material subset of READY8 movement, but they are not blanket erasers. The route preserves every non-ADV comparison row and assigns a matched control-envelope adjustment. Branches that remain outside the matched control envelope are retained as residual neutral target-movement intelligence only, still subject to duplicate-effective-N, concentration, and stress/sealed checks.

The downstream rule is exact: subtract the matched ADV control envelope first; then kill, weaken, retain-underpowered, or preserve residuals according to the generated adjustment ledger. No output is a promotion, live-readiness, R/PnL, win-rate, expectancy, AI/API, broker, order, or execution claim.

## Safe Boundary

No live, prompt, config, risk, safety, execution, selector, canary, broker/order, paid/API, raw market blob, registry, or remote surface was opened by this route.
