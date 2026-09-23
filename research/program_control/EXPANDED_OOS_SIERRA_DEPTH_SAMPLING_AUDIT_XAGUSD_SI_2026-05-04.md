# Sierra Depth Sampling Parity Audit - XAGUSD / SI.v.0

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research-only; cached/local data only.

## Event

| Field | Value |
|---|---|
| Event | `XAGUSD_20260501T0815_candidate_443` |
| Source | `SIM26-COMEX` |
| Futures | `SI.v.0` |
| Canonical close | `2026-05-01T08:15:00+00:00` |

## Window Audit

| Window | Classification | Sierra samples | Databento samples | Common | Jaccard | All max abs delta | Common max abs delta |
|---|---|---:|---:|---:|---:|---:|---:|
| pre60 | `SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS` | 2897 | 2949 | 2880 | 0.971005 | 52 | 26 |
| event15 | `SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS` | 719 | 741 | 718 | 0.967655 | 25 | 25 |

## Boundary

Sampling/source parity audit only; not replay validation, not OOS evidence, and not a live-filter claim.
