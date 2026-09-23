# Q1.3 CPCV Bias-Variance Bookkeeping

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Hypothesis

The Q1.3 `+0.0309` fixed-HP CPCV lift is dominated by path-to-path variance rather than transferable signal.

## Inputs

- CPCV artifact: `research/ml_program/models/k54_v2/cpcv_paired_results.json`.
- Prior statistical re-evaluation: `research/ml_program/audit/statistical_reevaluation.md`.
- No model retraining and no holdout opening were performed.

## Result

- Classification: `VARIANCE_DOMINATED_NO_SIGNAL_CLAIM`.
- Mean lift: `0.030896` versus Q1.3 gate threshold `0.040000`.
- Path sample std: `0.079431`.
- CPCV-honest weighted SE: `0.064857`.
- 95% weighted normal-approx CI: `[-0.096223, 0.158016]`.
- Signal share of mean-plus-path-variance: `0.131415`.
- Path variance share of mean-plus-path-variance: `0.868585`.
- Positive/negative path count: `10 / 5` out of `15`.
- Most influential path: `11`; dropping it moves the mean to `0.041412` (`34.04%` absolute relative change).
- Largest positive support path: `9` with diff `0.145445`.
- Largest negative drag path: `11` with diff `-0.116330`.

## Per-Path Diffs

| path | auc_v2 | auc_v1 | diff | delong_p |
| --- | --- | --- | --- | --- |
| 0 | 0.506508 | 0.543647 | -0.0371392 | 0.597343 |
| 1 | 0.611134 | 0.575376 | 0.0357578 | 0.539002 |
| 2 | 0.526533 | 0.498537 | 0.0279957 | 0.561233 |
| 3 | 0.520741 | 0.426657 | 0.0940841 | 0.204759 |
| 4 | 0.538502 | 0.452454 | 0.0860487 | 0.183199 |
| 5 | 0.541362 | 0.500465 | 0.0408964 | 0.457705 |
| 6 | 0.630067 | 0.536469 | 0.0935983 | 0.0680713 |
| 7 | 0.475676 | 0.535204 | -0.0595288 | 0.28715 |
| 8 | 0.587564 | 0.473895 | 0.113669 | 0.103937 |
| 9 | 0.64648 | 0.501035 | 0.145445 | 0.00923716 |
| 10 | 0.46274 | 0.524706 | -0.0619658 | 0.248197 |
| 11 | 0.444229 | 0.560559 | -0.11633 | 0.0708546 |
| 12 | 0.510066 | 0.570592 | -0.0605263 | 0.306833 |
| 13 | 0.605049 | 0.503939 | 0.101111 | 0.0846339 |
| 14 | 0.536579 | 0.47625 | 0.0603289 | 0.335166 |

## Interpretation

- The +0.0309 Q1.3 lift is variance-dominated: the squared mean accounts for only 13.1% of mean-plus-path-variance, while path variance accounts for 86.9%.
- The weighted interval crosses zero, so the average lift is not a stable signal estimate.
- The Stouffer p-value is not used; it assumes path independence that this CPCV design does not have.

## Next Steps

- Keep Q1.3 K54 v2 closed; do not cite Stouffer p as evidence.
- Use this decomposition pattern for any future CPCV path report that has per-path diffs.
- Continue Lane 1 with M-10/M-11/M-14/M-15/M-5/M-6 unless another artifact-supported closure is found.

## NO_PROMOTION_VERDICT

This report closes M-16 as methodology bookkeeping only. It does not validate, promote, or modify live trading behavior.
