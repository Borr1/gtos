# LTO030 6B / SI Depth Policy - 2026-05-05

**Status:** `OK_WITH_6B_POLICY_AND_SI_BLOCKER`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Summary

6B is unblocked at the policy level only when future rows declare and apply common-second alignment. Existing unaligned rows remain blocked. SI remains source/depth-definition blocked because common-second masking did not remove material depth deltas for SIM or SIL.

## Policy Rows

| Symbol | Source | Futures | Status | Current depth use | After-policy depth use | Event15 common | Event15 common max delta |
|---|---|---|---|---:|---:|---:|---:|
| GBPUSD | `6BM26-CME` | `6B.v.0` | `COMMON_SECOND_ALIGNMENT_POLICY_REGISTERED` | false | true | 632 | 5 |
| XAGUSD | `SIM26-COMEX` | `SI.v.0` | `SOURCE_DEPTH_DEFINITION_BLOCKED` | false | false | 718 | 25 |
| XAGUSD | `SILM26-COMEX` | `SI.v.0` | `SOURCE_DEPTH_DEFINITION_BLOCKED` | false | false | 679 | 25 |

## 6B Common-Second Policy

- GBPUSD/6B depth features are not interpreted from unaligned Sierra-only seconds.
- A future usable row must declare `sample_alignment_policy=6b_common_second_alignment_v1` and carry the reference-second source, common-second count, coverage Jaccard, all-seconds delta, and common-seconds delta.
- Existing current rows keep source/depth blockers until an aligned feature row exists.

## SI Depth Definition

- SIM and SIL remain blocked for XAGUSD/SI depth interpretation.
- Common-second masking did not remove material depth deltas, so this is not just a sampling-clock issue.
- SI rows remain source-status evidence only until source/contract/depth semantics are registered and re-tested.

## Boundary

This is source-policy infrastructure only. It is not a live filter, signal, risk modifier, or promotion dossier.
